import json
import urllib.request
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from psycopg import errors
from pydantic import BaseModel, Field

from . import berichte as bericht_modul, config, rechtstexte, einstellungen, ki, publish
from .db import tx
from .security import EMAIL_RE, audit, check_password_rules, hash_password, require_kunde, require_modul, verify_password

router = APIRouter(prefix="/api/kunde")


def gate(cur, user, code):
    require_modul(cur, user, code)


@router.get("/start")
def start(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        cur.execute("""SELECT k.kundennummer, k.firma, k.ansprechpartner, k.status, p.name AS paket, k.branding_farbe, (k.logo IS NOT NULL) AS logo_vorhanden
                       FROM kunden k LEFT JOIN produkte p ON p.code = k.paket_code WHERE k.id=%s""", (kid,))
        kunde = cur.fetchone()
        cur.execute("""SELECT m.code, m.name, m.art FROM kunden_module km JOIN module m ON m.code = km.modul_code
                       WHERE km.kunden_id=%s AND km.aktiv ORDER BY m.sortierung""", (kid,))
        module = cur.fetchall()
        cur.execute("""SELECT d::date AS tag, (SELECT count(*) FROM anfragen a WHERE a.kunden_id=%s AND a.erstellt_am::date = d::date) AS n
                       FROM generate_series(current_date - 13, current_date, interval '1 day') d ORDER BY d""", (kid,))
        reihe_anfragen = [r["n"] for r in cur.fetchall()]
        cur.execute("""SELECT d::date AS tag, (SELECT count(*) FROM termine t WHERE t.kunden_id=%s AND t.beginn::date = d::date) AS n
                       FROM generate_series(current_date, current_date + 13, interval '1 day') d ORDER BY d""", (kid,))
        reihe_termine = [r["n"] for r in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM anfragen WHERE status='neu'")
        neue = cur.fetchone()["n"]
        cur.execute("SELECT count(*) AS n FROM termine WHERE beginn >= now() AND status IN ('geplant','bestaetigt')")
        kommende = cur.fetchone()["n"]
        cur.execute("SELECT domain, status FROM websites ORDER BY erstellt_am LIMIT 1")
        web = cur.fetchone()
        cur.execute("""SELECT (SELECT count(*) FROM tickets WHERE kunde_ungelesen) AS nachrichten, (SELECT count(*) FROM kundenfreigaben WHERE status='wartet') AS freigaben,
                              (SELECT CASE WHEN EXISTS (SELECT 1 FROM briefings WHERE status='abgeschickt') THEN 0 ELSE 1 END) AS briefing""")
        badges = cur.fetchone()
    return {"badges": badges, "kunde": kunde, "module": module, "anfragen_14d": reihe_anfragen, "termine_14d": reihe_termine,
            "neue_anfragen": neue, "kommende_termine": kommende, "website": web, "kunden_rolle": user["kunden_rolle"]}


# ---------------------------------------------------------------- Chat
class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.get("/chat")
def chat_laden(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "ki_chat")
        cur.execute("SELECT id, absender, text, erstellt_am FROM chat_verlauf ORDER BY id DESC LIMIT 100")
        return list(reversed(cur.fetchall()))


def agent_antwort(kunde: dict, text: str, verlauf: list) -> str:
    if not config.CHAT_WEBHOOK_URL:
        return ("Der Agent ist für dein Konto noch nicht verbunden. Deine Nachricht ist gespeichert, "
                "das Markentrix-Team sieht sie und meldet sich bei dir.")
    body = json.dumps({"kundennummer": kunde["kundennummer"], "kunden_id": str(kunde["id"]), "text": text, "verlauf": verlauf}).encode()
    req = urllib.request.Request(config.CHAT_WEBHOOK_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "X-Webhook-Secret": config.CHAT_WEBHOOK_SECRET})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            antwort = json.loads(r.read().decode()).get("antwort", "")
        return antwort[:4000] or "Dazu habe ich gerade keine Antwort. Das Team schaut sich deine Nachricht an."
    except Exception:
        return "Der Agent ist gerade nicht erreichbar. Deine Nachricht ist gespeichert, das Team meldet sich bei dir."


def ki_antwort(kunde: dict, text: str, verlauf: list, cfg: dict, ctx: dict) -> tuple[str, int, int]:
    system = ki.system_prompt(kunde, ctx["module"], ctx["anfragen"], ctx["termine"])
    return ki.fragen(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, system, ki.nachrichten(verlauf, text))


@router.post("/chat")
def chat_senden(data: ChatIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    text = data.text.strip()
    with tx("kunde", kid) as cur:
        gate(cur, user, "ki_chat")
        cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.ansprechpartner, p.name AS paket FROM kunden k LEFT JOIN produkte p ON p.code=k.paket_code WHERE k.id=%s""", (kid,))
        kunde = cur.fetchone()
        cur.execute("SELECT absender, text FROM chat_verlauf ORDER BY id DESC LIMIT 10")
        verlauf = list(reversed(cur.fetchall()))
        cur.execute("SELECT count(*) AS n FROM chat_verlauf WHERE absender='kunde' AND erstellt_am >= date_trunc('day', now())")
        heute = cur.fetchone()["n"]
        cur.execute("SELECT m.name FROM kunden_module km JOIN module m ON m.code=km.modul_code WHERE km.aktiv AND m.art='portal' ORDER BY m.sortierung")
        module = [r["name"] for r in cur.fetchall()]
        cur.execute("SELECT erstellt_am, name, nachricht FROM anfragen WHERE status='neu' ORDER BY erstellt_am DESC LIMIT 5")
        anfragen = cur.fetchall()
        cur.execute("SELECT beginn, titel, status FROM termine WHERE beginn >= now() AND status IN ('geplant','bestaetigt') ORDER BY beginn LIMIT 5")
        termine = cur.fetchall()
    with tx("system") as cur:
        cfg = einstellungen.lesen(cur, "ki")
    limit = int(cfg.get("tageslimit", 50)) if cfg.get("api_key") else 0
    if cfg.get("api_key") and heute >= limit:
        antwort = f"Für heute ist das Nachrichtenlimit ({limit}) erreicht. Morgen geht es weiter. Dringende Fragen beantwortet das Markentrix-Team direkt."
        ein = aus = 0
    elif cfg.get("api_key"):
        try:
            antwort, ein, aus = ki_antwort(kunde, text, verlauf, cfg, {"module": module, "anfragen": anfragen, "termine": termine})
            antwort = antwort or "Dazu habe ich gerade keine Antwort. Das Markentrix-Team schaut sich deine Nachricht an."
        except Exception:
            antwort, ein, aus = "Der Assistent ist gerade nicht erreichbar. Deine Nachricht ist gespeichert, das Team meldet sich bei dir.", 0, 0
    else:
        antwort, ein, aus = agent_antwort(kunde, text, verlauf), 0, 0     # Webhook oder Platzhalter
    with tx("kunde", kid) as cur:
        cur.execute("INSERT INTO chat_verlauf (kunden_id, benutzer_id, absender, text) VALUES (%s,%s,'kunde',%s)", (kid, user["id"], text))
        cur.execute("INSERT INTO chat_verlauf (kunden_id, absender, text) VALUES (%s,'agent',%s) RETURNING id, absender, text, erstellt_am", (kid, antwort))
        r = cur.fetchone()
    if ein or aus:
        with tx("system") as cur:
            kosten = (ein * float(cfg.get("preis_ein_eur", 3.0)) + aus * float(cfg.get("preis_aus_eur", 15.0))) / 1_000_000 * 100
            cur.execute("INSERT INTO kosten_log (kunden_id, dienst, einheit, menge, kosten_cent) VALUES (%s,'anthropic','tokens',%s,%s)", (kid, ein + aus, round(kosten, 4)))
    return r


# ---------------------------------------------------------------- Anfragen und Termine
class StatusIn(BaseModel):
    status: str


@router.get("/anfragen")
def anfragen(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "anfragen_termine")
        cur.execute("SELECT id, name, kontakt, nachricht, quelle, status, erstellt_am FROM anfragen ORDER BY erstellt_am DESC LIMIT 200")
        return cur.fetchall()


@router.patch("/anfragen/{aid}")
def anfrage_status(aid: str, data: StatusIn, user: dict = Depends(require_kunde)):
    if data.status not in ("neu", "in_bearbeitung", "beantwortet", "erledigt", "spam"):
        raise HTTPException(400, "Unbekannter Status.")
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "anfragen_termine")
        cur.execute("UPDATE anfragen SET status=%s WHERE id=%s RETURNING id, status", (data.status, aid))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Nicht gefunden.")
    return r


@router.get("/termine")
def termine(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "anfragen_termine")
        cur.execute("""SELECT id, titel, beginn, ende, kontakt_name, kontakt_info, status, notiz FROM termine
                       WHERE beginn >= now() - interval '30 days' ORDER BY beginn LIMIT 200""")
        return cur.fetchall()


class TerminIn(BaseModel):
    titel: str = Field(min_length=1, max_length=200)
    beginn: str
    ende: str | None = None
    kontakt_name: str | None = Field(default=None, max_length=200)
    notiz: str | None = Field(default=None, max_length=2000)


@router.post("/termine")
def termin_neu(data: TerminIn, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "anfragen_termine")
        try:
            cur.execute("""INSERT INTO termine (kunden_id, titel, beginn, ende, kontakt_name, notiz) VALUES (%s,%s,%s::timestamptz,%s::timestamptz,%s,%s)
                           RETURNING id""", (user["kunden_id"], data.titel, data.beginn, data.ende, data.kontakt_name, data.notiz))
        except Exception:
            raise HTTPException(400, "Datum oder Uhrzeit sind ungültig.")
        return cur.fetchone()


@router.patch("/termine/{tid}")
def termin_status(tid: str, data: StatusIn, user: dict = Depends(require_kunde)):
    if data.status not in ("geplant", "bestaetigt", "abgesagt", "erledigt", "nicht_erschienen"):
        raise HTTPException(400, "Unbekannter Status.")
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "anfragen_termine")
        cur.execute("UPDATE termine SET status=%s WHERE id=%s RETURNING id, status", (data.status, tid))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Nicht gefunden.")
    return r


# ---------------------------------------------------------------- Kontakte, Angebote, Verträge
class KontaktIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    notiz: str | None = Field(default=None, max_length=2000)


@router.get("/kontakte")
def kontakte(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "kontakte_angebote_vertraege")
        cur.execute("SELECT id, name, firma, email, telefon, notiz FROM kontakte ORDER BY lower(name) LIMIT 500")
        return cur.fetchall()


@router.post("/kontakte")
def kontakt_neu(data: KontaktIn, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "kontakte_angebote_vertraege")
        cur.execute("INSERT INTO kontakte (kunden_id,name,firma,email,telefon,notiz) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                    (user["kunden_id"], data.name, data.firma, data.email, data.telefon, data.notiz))
        return cur.fetchone()


@router.put("/kontakte/{kid}")
def kontakt_aendern(kid: str, data: KontaktIn, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "kontakte_angebote_vertraege")
        cur.execute("UPDATE kontakte SET name=%s, firma=%s, email=%s, telefon=%s, notiz=%s WHERE id=%s RETURNING id",
                    (data.name, data.firma, data.email, data.telefon, data.notiz, kid))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Nicht gefunden.")
    return r


@router.delete("/kontakte/{kid}")
def kontakt_loeschen(kid: str, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "kontakte_angebote_vertraege")
        cur.execute("DELETE FROM kontakte WHERE id=%s", (kid,))
    return {"ok": True}


@router.get("/dokumente")
def dokumente(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "kontakte_angebote_vertraege")
        cur.execute("SELECT id, nummer, titel, betrag_cent, status, gueltig_bis, erstellt_am FROM angebote ORDER BY erstellt_am DESC LIMIT 100")
        angebote = cur.fetchall()
        cur.execute("SELECT id, titel, beginn, ende, status FROM vertraege ORDER BY erstellt_am DESC LIMIT 100")
        vertraege = cur.fetchall()
    return {"angebote": angebote, "vertraege": vertraege}


# ---------------------------------------------------------------- Website, Wochenangebote, Berichte, Automationen
@router.get("/website")
def website(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "website")
        cur.execute("SELECT domain, art, status, letzte_veroeffentlichung FROM websites ORDER BY erstellt_am")
        webs = cur.fetchall()
        cur.execute("SELECT id, titel, art, status, url FROM projekte ORDER BY erstellt_am DESC LIMIT 50")
        projekte = cur.fetchall()
    return {"websites": webs, "projekte": projekte}


@router.get("/wochenangebote")
def wochenangebote(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "wochenangebote")
        cur.execute("""SELECT id, dateiname, mime, groesse, status, gueltig_von, gueltig_bis, fehlertext, erstellt_am, veroeffentlicht_am
                       FROM wochenangebote_uploads ORDER BY erstellt_am DESC LIMIT 50""")
        uploads = cur.fetchall()
        cur.execute("SELECT domain FROM websites WHERE art='live' ORDER BY erstellt_am LIMIT 1")
        web = cur.fetchone()
    return {"uploads": uploads, "website": web["domain"] if web else None}


def _datum(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, "Datum ungültig (Format JJJJ-MM-TT).")


@router.post("/wochenangebote")
def wochenangebot_hochladen(datei: UploadFile = File(...), gueltig_von: str | None = Form(None), gueltig_bis: str | None = Form(None),
                            user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    von, bis = _datum(gueltig_von), _datum(gueltig_bis)
    if von and bis and bis < von:
        raise HTTPException(400, "Das Enddatum liegt vor dem Startdatum.")
    with tx("kunde", kid) as cur:
        gate(cur, user, "wochenangebote")
    typ, mime, groesse, pfad = publish.datei_speichern(datei, kid)
    name = publish.sicherer_name(datei.filename)
    with tx("kunde", kid) as cur:
        cur.execute("SELECT id, domain, sprachen FROM websites WHERE art='live' ORDER BY erstellt_am LIMIT 1")
        web = cur.fetchone()
        cur.execute("SELECT art, titel, text, preis, gueltig_von, gueltig_bis, aktiv FROM angebots_inhalte WHERE aktiv")
        inhalte = cur.fetchall()
        cur.execute("""INSERT INTO wochenangebote_uploads (kunden_id, website_id, dateiname, mime, groesse, dateipfad, gueltig_von, gueltig_bis, hochgeladen_von)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (kid, web["id"] if web else None, name, mime, groesse, str(pfad), von, bis, user["id"]))
        uid = cur.fetchone()["id"]
        status, fehler = "hochgeladen", None
        if not web:
            fehler = "Noch keine Website mit deinem Konto verknüpft. Das Team hat deine Datei und veröffentlicht sie nach der Verknüpfung."
        else:
            try:
                publish.veroeffentlichen(web["domain"], pfad, typ, von, bis, web["sprachen"], inhalte)
                status = "veroeffentlicht"
            except Exception as e:
                status, fehler = "fehler", str(e)[:300]
        if status == "veroeffentlicht":
            cur.execute("UPDATE wochenangebote_uploads SET status='ersetzt' WHERE status='veroeffentlicht' AND website_id=%s AND id<>%s", (web["id"], uid))
            cur.execute("UPDATE wochenangebote_uploads SET status='veroeffentlicht', veroeffentlicht_am=now() WHERE id=%s", (uid,))
            cur.execute("UPDATE websites SET letzte_veroeffentlichung=now() WHERE id=%s", (web["id"],))
        elif fehler:
            cur.execute("UPDATE wochenangebote_uploads SET status=%s, fehlertext=%s WHERE id=%s", (status, fehler, uid))
        audit(cur, user, "wochenangebot_hochgeladen", kid, {"datei": name, "status": status})
    return {"id": uid, "status": status, "hinweis": fehler, "adresse": f"https://{web['domain']}/angebote/" if web and status == "veroeffentlicht" else None}


@router.get("/berichte")
def berichte(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "werbung_berichte")
        cur.execute("SELECT id, titel, art, zeitraum_von, zeitraum_bis, daten, erstellt_am FROM berichte ORDER BY erstellt_am DESC LIMIT 100")
        return cur.fetchall()


@router.get("/automationen")
def automationen(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        gate(cur, user, "automationen")
        cur.execute("""SELECT m.code, m.name, m.beschreibung, coalesce(km.aktiv,false) AS aktiv
                       FROM module m LEFT JOIN kunden_module km ON km.modul_code=m.code AND km.kunden_id=%s
                       WHERE m.art='agent' ORDER BY m.sortierung""", (user["kunden_id"],))
        return cur.fetchall()


# ---------------------------------------------------------------- Einstellungen
class ProfilIn(BaseModel):
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    benachr_email: str | None = Field(default=None, max_length=254)
    benachr_anfragen: bool | None = None
    benachr_termine: bool | None = None
    benachr_bericht: bool | None = None
    benachr_nachrichten: bool | None = None


class PasswortIn(BaseModel):
    alt: str
    neu: str


@router.get("/profil")
def profil(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("""SELECT k.kundennummer, k.firma, k.ansprechpartner, k.email, k.telefon, k.domain, p.name AS paket,
                              k.benachr_email, k.benachr_anfragen, k.benachr_termine, k.benachr_bericht, k.benachr_nachrichten,
                              k.strasse, k.plz, k.ort,
                              k.branding_farbe, (k.logo IS NOT NULL) AS logo_vorhanden
                       FROM kunden k LEFT JOIN produkte p ON p.code=k.paket_code WHERE k.id=%s""", (user["kunden_id"],))
        kunde = cur.fetchone()
        cur.execute("""SELECT b.produkt_code, p.name, b.status, b.beginn, b.mindestlaufzeit_ende FROM buchungen b JOIN produkte p ON p.code=b.produkt_code
                       WHERE b.status IN ('beauftragt','in_einrichtung','aktiv','pausiert') ORDER BY b.beginn NULLS LAST""")
        buchungen = cur.fetchall()
    return {"kunde": kunde, "buchungen": buchungen, "login": user["email"], "kunden_rolle": user["kunden_rolle"]}


@router.patch("/profil")
def profil_aendern(data: ProfilIn, user: dict = Depends(require_kunde)):
    # Kunden dürfen nur Kontaktdaten ändern. Die Tabelle kunden ist für Kunden schreibgeschützt,
    # deshalb läuft die Änderung bewusst im Systemkontext und nur für den eigenen Datensatz.
    if data.benachr_email and not EMAIL_RE.match(data.benachr_email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse für Benachrichtigungen ist ungültig.")
    with tx("system") as cur:
        cur.execute("""UPDATE kunden SET ansprechpartner=coalesce(%s,ansprechpartner), email=coalesce(%s,email), telefon=coalesce(%s,telefon),
                       benachr_email=CASE WHEN %s::boolean THEN nullif(%s,'') ELSE benachr_email END,
                       benachr_anfragen=coalesce(%s,benachr_anfragen), benachr_termine=coalesce(%s,benachr_termine), benachr_bericht=coalesce(%s,benachr_bericht), benachr_nachrichten=coalesce(%s,benachr_nachrichten)
                       WHERE id=%s""",
                    (data.ansprechpartner, data.email, data.telefon, data.benachr_email is not None, data.benachr_email,
                     data.benachr_anfragen, data.benachr_termine, data.benachr_bericht, data.benachr_nachrichten, user["kunden_id"]))
        audit(cur, user, "profil_geaendert", user["kunden_id"])
    return {"ok": True}


@router.post("/passwort")
def passwort_aendern(data: PasswortIn, user: dict = Depends(require_kunde)):
    check_password_rules(data.neu)
    with tx("system") as cur:
        cur.execute("SELECT passwort_hash FROM benutzer WHERE id=%s", (user["id"],))
        if not verify_password(data.alt, cur.fetchone()["passwort_hash"]):
            raise HTTPException(400, "Das aktuelle Passwort stimmt nicht.")
        cur.execute("UPDATE benutzer SET passwort_hash=%s WHERE id=%s", (hash_password(data.neu), user["id"]))
        audit(cur, user, "passwort_geaendert", user["kunden_id"])
    return {"ok": True}


# ---------------------------------------------------------------- Monatsberichte (für alle Kunden)
@router.get("/monatsberichte")
def monatsberichte(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("SELECT id, titel, zeitraum_von, zeitraum_bis, daten, erstellt_am FROM berichte WHERE art='monatsbericht' ORDER BY zeitraum_von DESC LIMIT 36")
        return cur.fetchall()


@router.get("/monatsberichte/{bid}/pdf")
def monatsbericht_pdf(bid: str, user: dict = Depends(require_kunde)):
    try:
        f = rechtstexte.firma_system()
        with tx("kunde", user["kunden_id"]) as cur:
            daten, name = bericht_modul.pdf_erzeugen(cur, bid, f)
    except (LookupError, errors.InvalidTextRepresentation):
        raise HTTPException(404, "Bericht nicht gefunden.")
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
