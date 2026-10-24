"""Angebot direkt an einen Lead: Paket wählen, Vorschau, per Mail senden. Der Lead nimmt online über einen geheimen Link an oder ab.
Das Angebot hängt am Lead (ohne Kunde); wird der Lead zum Kunden, wandert es mit."""
import hashlib
import json
import re
import secrets
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import angebotsfluss, angebotsgrund, belege, config, einstellungen, mailer, push, rechtstexte
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin

router = APIRouter()
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BLOCKIERT = ("gesperrt", "consent_ausstehend", "tot", "verloren")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _lead(cur, lid):
    try:
        cur.execute("SELECT * FROM leads WHERE id=%s", (lid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    l = cur.fetchone()
    if not l:
        raise HTTPException(404, "Lead nicht gefunden.")
    return l


def _beleg(cur, lid, bid):
    try:
        cur.execute("SELECT * FROM belege WHERE id=%s AND lead_id=%s AND art='angebot'", (bid, lid))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Angebot nicht gefunden.")
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Angebot nicht gefunden.")
    return b


def _link(token: str) -> str:
    return f"{config.BASE_URL}/angebot?t={token}"


def empfaenger_lead(l: dict) -> dict:
    return {"kundennummer": "", "firma": l["firma"], "ansprechpartner": l.get("ansprechpartner"), "strasse": "", "plz": l.get("plz"), "ort": l.get("ort"), "email": l.get("email")}


def _vorname_gruss(l: dict) -> str:
    n = (l.get("ansprechpartner") or "").strip()
    return f"Guten Tag {n}," if n else "Guten Tag,"


# ---------------------------------------------------------------- Vorlage
@router.get("/api/admin/leads/{lid}/angebot-vorlage")
def vorlage(lid: str, user: dict = Depends(require_admin)):
    """Alles, was der Dialog braucht: Pakete mit aktuellen Preisen, Textvorschlag, Steuerangaben."""
    with tx("admin") as cur:
        l = _lead(cur, lid)
        cur.execute("SELECT v.code, v.kategorie, v.name, v.einrichtung_cent, v.monatlich_cent, v.projekt_cent, v.ab_preis, v.nur_auf_anfrage, p.leistungen FROM v_preise_aktuell v JOIN produkte p ON p.code = v.code ORDER BY v.kategorie, v.name")
        pakete = cur.fetchall()
        cur.execute("SELECT paket_code FROM angebotsanfragen WHERE lead_id=%s ORDER BY erstellt_am DESC LIMIT 1", (lid,))
        a = cur.fetchone()
        f = rechtstexte.firma(cur)
        cur.execute("SELECT id, nummer, status, betreff, einleitung, schluss, positionen, leistungen FROM belege WHERE lead_id=%s AND art='angebot' AND status='entwurf' ORDER BY erstellt_am DESC LIMIT 1", (lid,))
        entwurf = cur.fetchone()
    return {"lead": {"id": l["id"], "firma": l["firma"], "ansprechpartner": l["ansprechpartner"], "email": l["email"], "status": l["status"], "kunden_id": l["kunden_id"]},
            "pakete": pakete, "vorschlag_paket": a and a["paket_code"], "entwurf_id": entwurf and entwurf["id"], "entwurf": entwurf and {k: entwurf[k] for k in ("betreff", "einleitung", "schluss", "positionen", "leistungen")},
            "gruss": _vorname_gruss(l), "mwst_satz": float(f["mwst_satz"]), "kleinunternehmer": bool(f["kleinunternehmer"]),
            "firma_ok": bool(f["name"] and f["strasse"]), "mail_eingerichtet": mailer.konfiguriert()}


# ---------------------------------------------------------------- Entwurf anlegen oder ändern
class AngebotIn(BaseModel):
    beleg_id: str | None = None
    betreff: str = Field(default="", max_length=200)
    einleitung: str = Field(default="", max_length=3000)
    schluss: str = Field(default="", max_length=3000)
    positionen: list[dict] = []
    leistungen: list[str] = Field(default=[], max_length=60)   # „Das bekommen Sie“; Zeilen mit „## “ sind Zwischenüberschriften


@router.post("/api/admin/leads/{lid}/angebote")
def entwurf(lid: str, data: AngebotIn, user: dict = Depends(require_admin)):
    pos = belege.positionen_pruefen(data.positionen)
    if not pos:
        raise HTTPException(400, "Bitte mindestens eine Position eintragen.")
    leist = json.dumps([x.strip()[:300] for x in data.leistungen if x.strip()])
    with tx("admin") as cur:
        l = _lead(cur, lid)
        if l["status"] in BLOCKIERT:
            raise HTTPException(400, "Für diesen Lead darf kein Angebot gesendet werden (gesperrt, ohne Einwilligung, verloren oder tot).")
        f = rechtstexte.firma(cur)
        s = belege.summen(pos, f["mwst_satz"], f["kleinunternehmer"])
        if data.beleg_id:
            b = _beleg(cur, lid, data.beleg_id)
            if b["status"] != "entwurf":
                raise HTTPException(400, "Dieses Angebot ist schon ausgestellt.")
            cur.execute("""UPDATE belege SET betreff=%s, einleitung=%s, schluss=%s, positionen=%s::jsonb, leistungen=%s::jsonb, netto_cent=%s, ust_satz=%s, ust_cent=%s, brutto_cent=%s, kleinunternehmer=%s,
                                  geaendert_am=now() WHERE id=%s""",
                        (data.betreff, data.einleitung, data.schluss, json.dumps(pos), leist, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], b["id"]))
            bid = b["id"]
        else:
            cur.execute("""INSERT INTO belege (art, kunden_id, lead_id, betreff, einleitung, schluss, positionen, leistungen, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer)
                           VALUES ('angebot', %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s) RETURNING id""",
                        (l["kunden_id"], lid, data.betreff, data.einleitung, data.schluss, json.dumps(pos), leist, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"]))
            bid = cur.fetchone()["id"]
        audit(cur, user, "lead_angebot_entwurf", l["kunden_id"], {"lead": lid})
    return {"id": bid, "netto_cent": s["netto_cent"], "brutto_cent": s["brutto_cent"]}


@router.delete("/api/admin/leads/{lid}/angebote/{bid}")
def entwurf_loeschen(lid: str, bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _beleg(cur, lid, bid)
        if b["status"] != "entwurf" or b["nummer"]:
            raise HTTPException(400, "Nur Entwürfe können gelöscht werden.")
        cur.execute("DELETE FROM belege WHERE id=%s", (bid,))
        audit(cur, user, "lead_angebot_entwurf_geloescht", None, {"lead": lid})
    return {"ok": True}


@router.get("/api/admin/leads/{lid}/angebote/{bid}/pdf")
def vorschau(lid: str, bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _beleg(cur, lid, bid)
        l = _lead(cur, lid)
        daten, name = belege.beleg_pdf(cur, bid, rechtstexte.firma(cur), empfaenger_lead(l))
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


@router.get("/api/admin/leads/{lid}/angebote")
def liste(lid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _lead(cur, lid)
        cur.execute("""SELECT id, nummer, status, betreff, datum, faellig_am, netto_cent, brutto_cent, versendet_am, angesehen_am, angenommen_am, angenommen_von, abgelehnt_am, erinnerungen, erinnert_am, grund_code, grund_text,
                              (annahme_hash IS NOT NULL) AS hat_link FROM belege WHERE lead_id=%s AND art='angebot' ORDER BY erstellt_am DESC""", (lid,))
        return cur.fetchall()


# ---------------------------------------------------------------- Ausstellen und senden
class SendenIn(BaseModel):
    gueltig_tage: int = Field(default=30, ge=1, le=365)
    an: str | None = Field(default=None, max_length=200)
    erinnerung: bool = False        # kurze Nachfrage-Mail statt Erstversand
    neuer_link: bool = False        # nur wenn ausdrücklich gewünscht: alter Link wird ungültig
    nur_link: bool = False          # nicht mailen (z. B. Mail nicht eingerichtet): Link zum Weitergeben per WhatsApp o. Ä.


@router.post("/api/admin/leads/{lid}/angebote/{bid}/senden")
def senden(lid: str, bid: str, data: SendenIn, user: dict = Depends(require_admin)):
    rate_limit("leadangebot:" + str(user["id"]), 40, 3600)
    token = secrets.token_urlsafe(24)
    with tx("admin") as cur:
        l = _lead(cur, lid)
        b = _beleg(cur, lid, bid)
        if b["status"] not in ("entwurf", "gestellt", "versendet"):
            raise HTTPException(400, "Dieses Angebot wurde schon angenommen oder abgelehnt.")
        if l["status"] in BLOCKIERT:
            raise HTTPException(400, "Für diesen Lead darf kein Angebot gesendet werden (gesperrt, ohne Einwilligung, verloren oder tot).")
        an = (data.an or l.get("email") or "").strip()
        if not data.nur_link and not EMAIL.match(an):
            raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse eintragen.")
        if not b["positionen"]:
            raise HTTPException(400, "Bitte mindestens eine Position eintragen.")
        f = rechtstexte.firma(cur)
        if not (f["name"] and f["strasse"]):
            raise HTTPException(400, "Bitte zuerst unter Einstellungen → Firmendaten Name und Anschrift eintragen.")
        nummer = b["nummer"]
        if b["status"] == "entwurf":
            s = belege.summen(b["positionen"], f["mwst_satz"], f["kleinunternehmer"])
            nummer = belege.naechste_nummer(cur, "angebot", f["angebotsprefix"] or "AN")
            cur.execute("""UPDATE belege SET nummer=%s, status='gestellt', datum=%s, faellig_am=%s, netto_cent=%s, ust_satz=%s, ust_cent=%s, brutto_cent=%s, kleinunternehmer=%s,
                                  empfaenger=%s::jsonb, geaendert_am=now() WHERE id=%s""",
                        (nummer, date.today(), date.today() + timedelta(days=data.gueltig_tage), s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"],
                         json.dumps(empfaenger_lead(l)), bid))
        nonlocal_token = None
        if b.get("annahme_token_enc") and not data.neuer_link:     # derselbe Link bleibt gültig (auch der aus der ersten Mail)
            alt = einstellungen.entschluesseln(b["annahme_token_enc"])
            if alt and b["annahme_hash"] == _hash(alt):
                nonlocal_token = alt
        token = nonlocal_token or token
        cur.execute("UPDATE belege SET annahme_hash=%s, annahme_token_enc=%s, geaendert_am=now() WHERE id=%s", (_hash(token), einstellungen.verschluesseln(token), bid))
        daten, name = belege.beleg_pdf(cur, bid, f)
        cur.execute("SELECT faellig_am FROM belege WHERE id=%s", (bid,))
        gueltig = cur.fetchone()["faellig_am"]
    link = _link(token)
    gesendet, grund = False, ""
    if not data.nur_link:
        gesendet, grund = mailer.lead_angebot(an, l.get("ansprechpartner"), l["firma"], nummer, daten, name, gueltig, link, f["name"], erinnerung=data.erinnerung and b["status"] != "entwurf")
    with tx("admin") as cur:
        if gesendet:
            cur.execute("UPDATE belege SET versendet_am=now(), status='versendet' WHERE id=%s", (bid,))
        if l["status"] in ("neu", "kontaktiert", "antwort", "termin"):
            cur.execute("UPDATE leads SET status='angebot' WHERE id=%s", (lid,))
        if gesendet or data.nur_link:   # Nachfass-Termin setzen: nach Erstversand 4 Tage, nach Erinnerung 3 Tage
            cur.execute("UPDATE leads SET wiedervorlage_am=current_date + %s, letzter_kontakt_am=now() WHERE id=%s", (3 if data.erinnerung else 4, lid))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s)",
                    (lid, "mail_gesendet" if gesendet else "notiz", f"Angebot {nummer} " + (("Erinnerung per E-Mail gesendet" if data.erinnerung else "per E-Mail gesendet") if gesendet else "erstellt (Link zum Weitergeben)"), user["email"]))
        cur.execute("UPDATE angebotsanfragen SET status='angebot_raus', geaendert_am=now() WHERE lead_id=%s AND status IN ('angefragt','in_pruefung')", (lid,))
        audit(cur, user, "lead_angebot_gesendet", None, {"lead": lid, "nummer": nummer, "per_mail": gesendet})
        if l.get("vertriebspartner_id"):
            ids = push.partner(cur, l["vertriebspartner_id"])
        else:
            ids = []
    if ids and (gesendet or data.nur_link) and not data.erinnerung:
        push.senden(ids, "Angebot ist raus", l["firma"], "/vertrieb#lead/" + lid, "angebotsstatus")
    return {"nummer": nummer, "gesendet": gesendet, "grund": grund, "link": link, "an": an, "betreff": f"Angebot {nummer}"}


# ---------------------------------------------------------------- Öffentliche Seite für den Empfänger
oeffentlich = APIRouter(prefix="/api/angebot")


def _holen(cur, token: str) -> dict:
    cur.execute("""SELECT b.*, l.vertriebspartner_id AS partner_id, l.firma AS lead_firma FROM belege b LEFT JOIN leads l ON l.id=b.lead_id
                   WHERE b.annahme_hash=%s AND b.art='angebot' AND b.status IN ('gestellt','versendet','angenommen','abgelehnt')""", (_hash(token),))
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Dieses Angebot gibt es nicht (mehr). Bitte fragen Sie bei uns nach einem aktuellen Link.")
    return b


def _info(b: dict, firma: dict) -> dict:
    abgelaufen = bool(b["faellig_am"] and b["faellig_am"] < date.today())
    return {"anbieter": firma["name"], "nummer": b["nummer"], "empfaenger": (b["empfaenger"] or {}).get("firma") or b["lead_firma"], "betreff": b["betreff"], "einleitung": b["einleitung"], "schluss": b["schluss"],
            "positionen": b["positionen"], "leistungen": b["leistungen"], "bedingungen": (firma.get("angebotsbedingungen") or "").strip(), "netto_cent": int(b["netto_cent"]), "ust_satz": float(b["ust_satz"]), "ust_cent": int(b["ust_cent"]), "brutto_cent": int(b["brutto_cent"]),
            "kleinunternehmer": b["kleinunternehmer"], "datum": b["datum"], "gueltig_bis": b["faellig_am"], "status": b["status"], "abgelaufen": abgelaufen,
            "angenommen_am": b["angenommen_am"], "kontakt": {"email": firma.get("email"), "telefon": firma.get("telefon")}}


def _empfaenger(cur, b: dict) -> list:
    """Wer über Reaktionen auf das Angebot Bescheid bekommt: alle Admins und der zuständige Vertriebler."""
    return push.admins(cur) + (push.partner(cur, b["partner_id"]) if b.get("partner_id") else [])


@oeffentlich.get("/{token}")
def ansehen(token: str, request: Request):
    rate_limit("angebot:" + client_ip(request), 60, 600)
    ids = []
    with tx("system") as cur:
        b = _holen(cur, token)
        f = rechtstexte.firma(cur)
        if not b["angesehen_am"]:
            cur.execute("UPDATE belege SET angesehen_am=now() WHERE id=%s", (b["id"],))
            ids = _empfaenger(cur, b)
    if ids:
        push.senden(ids, "Angebot angesehen", b["lead_firma"] or "", "/admin#lead/" + str(b["lead_id"]), "angebotsreaktion")
    return _info(b, f)


@oeffentlich.get("/{token}/pdf")
def pdf(token: str, request: Request):
    rate_limit("angebotpdf:" + client_ip(request), 30, 600)
    with tx("system") as cur:
        b = _holen(cur, token)
        daten, name = belege.beleg_pdf(cur, b["id"], rechtstexte.firma(cur))
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


class AnnahmeIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    bestaetigt: bool = False


@oeffentlich.post("/{token}/annehmen")
def annehmen(token: str, data: AnnahmeIn, request: Request):
    rate_limit("angebotjn:" + client_ip(request), 15, 3600)
    if not data.bestaetigt:
        raise HTTPException(400, "Bitte bestätigen Sie, dass Sie das Angebot verbindlich annehmen möchten.")
    with tx("system") as cur:
        b = _holen(cur, token)
        if b["status"] == "angenommen":
            return {"ok": True, "schon": True}
        if b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Dieses Angebot kann nicht mehr angenommen werden.")
        if b["faellig_am"] and b["faellig_am"] < date.today():
            raise HTTPException(400, "Dieses Angebot ist abgelaufen. Bitte melden Sie sich bei uns, wir senden Ihnen gern ein neues.")
        name = data.name.strip()
        info = angebotsfluss.angenommen(cur, b, name, "online", "Angebotsseite", client_ip(request))
    angebotsfluss.melden(info)
    return {"ok": True}


GRUENDE = {"zu_teuer": "Zu teuer", "spaeter": "Später / gerade kein Thema", "anderer_anbieter": "Anderer Anbieter", "nicht_passend": "Passt nicht zu unserem Bedarf", "sonstiges": "Sonstiges"}


class AblehnungIn(BaseModel):
    grund: str = Field(default="", max_length=500)
    grund_code: str = Field(default="", max_length=30)


@oeffentlich.post("/{token}/ablehnen")
def ablehnen(token: str, data: AblehnungIn, request: Request):
    rate_limit("angebotjn:" + client_ip(request), 15, 3600)
    with tx("system") as cur:
        b = _holen(cur, token)
        if b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Dieses Angebot kann nicht mehr abgelehnt werden.")
        cur.execute("UPDATE belege SET status='abgelehnt', abgelehnt_am=now(), geaendert_am=now(), grund_code=%s, grund_text=%s, grund_am=CASE WHEN %s::text IS NULL THEN NULL ELSE now() END WHERE id=%s",
                    (angebotsgrund.ONLINE.get(data.grund_code), data.grund.strip()[:500] or None, angebotsgrund.ONLINE.get(data.grund_code), b["id"]))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,'Angebotsseite')",
                    (b["lead_id"], f"Angebot {b['nummer']} online abgelehnt" + (f" (Grund: {GRUENDE[data.grund_code]})" if data.grund_code in GRUENDE else "") + (f": {data.grund.strip()}" if data.grund.strip() else "")))
        # Der Lead bleibt bearbeitbar: nicht mehr „Angebot“, heute auf die Wiedervorlage
        cur.execute("UPDATE leads SET status=CASE WHEN status='angebot' THEN 'antwort' ELSE status END, wiedervorlage_am=current_date WHERE id=%s AND kunden_id IS NULL", (b["lead_id"],))
        cur.execute("UPDATE angebotsanfragen SET status='abgelehnt', geaendert_am=now() WHERE lead_id=%s AND status IN ('angefragt','in_pruefung','angebot_raus')", (b["lead_id"],))
        audit(cur, None, "lead_angebot_abgelehnt", None, {"lead": str(b["lead_id"]), "nummer": b["nummer"], "ip": client_ip(request)})
        ids = _empfaenger(cur, b)
    push.senden(ids, "Angebot abgelehnt", f"{b['lead_firma']}: {b['nummer']}", "/admin#lead/" + str(b["lead_id"]), "angebotsreaktion")
    return {"ok": True}
