"""Website-Dienste: Kunden-Websites (von Markentrix gebaut und gehostet) nutzen Kontaktformular, Terminbuchung, PayPal und Bewertungen.

Drei Teile:
 - /site/<site-id>/…           öffentlich, wird vom Skript der Website aufgerufen (Herkunftsprüfung, Begrenzung, Lockfeld)
 - /api/kunde/website-dienste  der Inhaber trägt seine Daten ein (Zugangsdaten nur schreibbar, nie lesbar)
 - /api/admin/…                Status ohne Geheimnisse"""
import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from html import escape
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field, ValidationError

from . import config, einstellungen, push
from . import sitedienste as sd
from .db import tx
from .security import EMAIL_RE, audit, client_ip, rate_limit, require_admin, require_inhaber

router = APIRouter()
TZ = sd.TZ
ROOT = urlparse(config.BASE_URL).hostname or ""
ROOT = ROOT[7:] if ROOT.startswith("portal.") else ROOT


# =============================================================== öffentlich (vom Skript der Website)
def _site(site_id: str) -> dict:
    if not re.match(r"^mk_[A-Za-z0-9]{6,40}$", site_id):
        raise HTTPException(404, "Unbekannte Website.")
    with tx("system") as cur:
        cur.execute("SELECT * FROM website_dienste WHERE site_id=%s", (site_id,))
        z = cur.fetchone()
        if not z:
            raise HTTPException(404, "Unbekannte Website.")
        z["_hosts"] = sd.erlaubte_hosts(cur, z["kunden_id"], ROOT)
    return z


def _cors(request: Request, z: dict) -> dict:
    """Nur Seiten der Domains dieses Kunden dürfen die Schnittstelle aufrufen."""
    origin = request.headers.get("origin", "")
    host = (urlparse(origin).hostname or "").lower() if origin else ""
    if not host or host not in z["_hosts"]:
        raise HTTPException(403, "Diese Seite darf den Dienst nicht nutzen.")
    return {"Access-Control-Allow-Origin": origin, "Vary": "Origin", "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "600", "Cache-Control": "no-store"}


def _antwort(daten, kopf: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(daten, status_code=status, headers=kopf)


async def _korper(request: Request) -> dict:
    roh = await request.body()
    if len(roh) > 20_000:
        raise HTTPException(413, "Die Eingabe ist zu lang.")
    try:
        d = json.loads(roh or b"{}")
    except ValueError:
        raise HTTPException(400, "Ungültige Anfrage.")
    if not isinstance(d, dict):
        raise HTTPException(400, "Ungültige Anfrage.")
    return d


def _pruefen(modell, daten: dict):
    try:
        return modell(**daten)
    except ValidationError:
        raise HTTPException(400, "Bitte füllen Sie alle Felder korrekt aus.")


@router.options("/site/{site_id}/{pfad:path}", include_in_schema=False)
def vorabfrage(site_id: str, pfad: str, request: Request):
    z = _site(site_id)
    return Response(status_code=204, headers=_cors(request, z))


@router.get("/site/{site_id}/config", include_in_schema=False)
def oeff_config(site_id: str, request: Request):
    z = _site(site_id)
    kopf = _cors(request, z)
    rate_limit("siteconf:" + client_ip(request), 120, 300)
    return _antwort({
        "kontakt": bool(z["mail_aktiv"]),
        "termin": {"aktiv": bool(z["kal_aktiv"]), "dauer": z["kal_dauer"], "ort": z["kal_ort"] or ""},
        "paypal": {"aktiv": bool(z["pp_aktiv"] and (z["pp_client_id"] or z["pp_me_link"])), "client_id": z["pp_client_id"] or "", "waehrung": z["pp_waehrung"],
                   "me_link": z["pp_me_link"] or ""},
        "bewertungen": bool(z["bew_aktiv"]),
        "analytics": {"aktiv": bool(z["ga_aktiv"] and z["ga_id"]), "id": z["ga_id"] or ""},
    }, kopf)


class KontaktIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=200)
    telefon: str = Field(default="", max_length=60)
    nachricht: str = Field(min_length=3, max_length=3000)
    einwilligung: bool = False
    hp: str = Field(default="", max_length=200)          # Lockfeld: Menschen sehen es nicht, Bots füllen es aus
    seite: str = Field(default="", max_length=300)


def _empfaenger(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;\s]+", text or "") if x.strip()]


@router.post("/site/{site_id}/kontakt", include_in_schema=False)
def oeff_kontakt(site_id: str, request: Request, daten: dict = Depends(_korper)):
    z = _site(site_id)
    kopf = _cors(request, z)
    rate_limit("kontakt:" + client_ip(request), 6, 600)
    rate_limit("kontaktsite:" + site_id, 150, 86400)
    if not z["mail_aktiv"]:
        raise HTTPException(409, "Das Kontaktformular ist nicht aktiv.")
    d = _pruefen(KontaktIn, daten)
    if d.hp:
        return _antwort({"ok": True}, kopf)               # Bot: so tun als ob, nichts senden
    email = d.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not d.einwilligung:
        raise HTTPException(400, "Bitte stimmen Sie der Verarbeitung Ihrer Angaben zu.")
    kid = z["kunden_id"]
    an = [a for a in _empfaenger(z["mail_empfaenger"]) if EMAIL_RE.match(a)][:5]
    kontakt = email + (", " + d.telefon.strip() if d.telefon.strip() else "")
    with tx("system") as cur:
        cur.execute("INSERT INTO anfragen (kunden_id, name, kontakt, nachricht, quelle) VALUES (%s,%s,%s,%s,'website')",
                    (kid, d.name.strip(), kontakt, d.nachricht.strip()))
        ids = push.kunde(cur, kid)
    push.senden(ids, "Neue Anfrage über die Website", f"{d.name.strip()} hat das Kontaktformular genutzt.", "/app#anfragen", "anfrage")
    betreff = z["mail_betreff"] or "Neue Anfrage über Ihre Website"
    text = (f"Neue Anfrage über das Kontaktformular Ihrer Website.\n\nName: {d.name.strip()}\nE-Mail: {email}\nTelefon: {d.telefon.strip() or '–'}\n\n"
            f"Nachricht:\n{d.nachricht.strip()}\n\n—\nSie können direkt auf diese E-Mail antworten, die Antwort geht an {email}.")
    if not an:
        sd.ereignis(kid, "kontakt", False, "Kein Empfänger eingetragen, die Anfrage liegt nur im Portal unter „Anfragen“.")
        return _antwort({"ok": True}, kopf)
    fehler = ""
    for a in an:
        ok, via = sd.kundenmail(kid, a, betreff, text, reply_to=email, art="kontakt")
        if not ok:
            fehler = via
    if fehler:
        sd.ereignis(kid, "kontakt", False, "Versand fehlgeschlagen, Anfrage liegt im Portal. " + fehler[:150])
    else:
        sd.ereignis(kid, "kontakt", True, "gesendet")
    return _antwort({"ok": True}, kopf)


@router.get("/site/{site_id}/termine", include_in_schema=False)
def oeff_termine(site_id: str, request: Request):
    z = _site(site_id)
    kopf = _cors(request, z)
    rate_limit("sitetermine:" + client_ip(request), 60, 300)
    if not z["kal_aktiv"]:
        return _antwort({"aktiv": False, "tage": []}, kopf)
    with tx("system") as cur:
        tage: dict = {}
        for s in sd.freie_slots(cur, z):
            lokal = s.astimezone(TZ)
            tage.setdefault(lokal.strftime("%Y-%m-%d"), []).append({"start": s.isoformat(), "uhr": lokal.strftime("%H:%M")})
    return _antwort({"aktiv": True, "dauer": z["kal_dauer"], "ort": z["kal_ort"] or "", "tage": [{"datum": d, "slots": s} for d, s in tage.items()]}, kopf)


class TerminIn(BaseModel):
    start: str = Field(max_length=40)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=200)
    telefon: str = Field(default="", max_length=60)
    nachricht: str = Field(default="", max_length=1500)
    einwilligung: bool = False
    hp: str = Field(default="", max_length=200)


def _termin_mails(kid, g: dict, z: dict, firma: str, an: list):
    lokal = g["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
    ort = z["kal_ort"] or ""
    absagen = f"{config.BASE_URL}/site/{z['site_id']}/termin/absagen?t={g['token']}"
    anhang = ("termin.ics", sd.ics(str(g["id"]), g["start"], g["ende"], "Termin bei " + firma, ort), "text/calendar")
    sd.kundenmail(kid, g["email"], f"Ihr Termin bei {firma} am {lokal}",
                  f"Guten Tag {g['name']},\n\nIhr Termin ist gebucht: {lokal}.\n{ort}\n\nDie Kalendereinladung hängt an. Falls Sie nicht können, sagen Sie bitte hier ab:\n{absagen}\n\nBis bald!\n{firma}",
                  anhang=anhang, art="termin")
    for a in an:
        sd.kundenmail(kid, a, f"Neuer Termin: {g['name']} am {lokal}",
                      f"{g['name']} ({g['email']}, {g.get('telefon') or 'keine Nummer'}) hat über Ihre Website einen Termin gebucht: {lokal}.\n\n{g.get('nachricht') or ''}\n\n"
                      f"Der Termin steht im Portal unter „Heute“ und in der Einladung im Anhang.", reply_to=g["email"],
                      anhang=("termin.ics", sd.ics(str(g["id"]), g["start"], g["ende"], "Termin: " + g["name"], ort), "text/calendar"), art="termin")


@router.post("/site/{site_id}/termin", include_in_schema=False)
def oeff_termin(site_id: str, request: Request, bg: BackgroundTasks, daten: dict = Depends(_korper)):
    z = _site(site_id)
    kopf = _cors(request, z)
    rate_limit("sitebuchen:" + client_ip(request), 8, 3600)
    rate_limit("sitebuchensite:" + site_id, 100, 86400)
    if not z["kal_aktiv"]:
        raise HTTPException(409, "Die Terminbuchung ist nicht aktiv.")
    d = _pruefen(TerminIn, daten)
    if d.hp:
        return _antwort({"ok": True, "wann": ""}, kopf)
    email = d.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not d.einwilligung:
        raise HTTPException(400, "Bitte stimmen Sie der Verarbeitung Ihrer Angaben zu.")
    try:
        start = datetime.fromisoformat(d.start).astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(400, "Ungültiger Termin.")
    kid = z["kunden_id"]
    voll = "Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie einen anderen."
    with tx("system") as cur:
        if start not in sd.freie_slots(cur, z):
            raise HTTPException(409, voll)
        ende = start + timedelta(minutes=z["kal_dauer"])
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = cur.fetchone()["firma"]
        kontakt = email + (", " + d.telefon.strip() if d.telefon.strip() else "")
        cur.execute("""INSERT INTO termine (kunden_id, titel, beginn, ende, kontakt_name, kontakt_info, status, notiz)
                       VALUES (%s,%s,%s,%s,%s,%s,'bestaetigt',%s) RETURNING id""",
                    (kid, "Termin über die Website", start, ende, d.name.strip(), kontakt, d.nachricht.strip() or None))
        tid = cur.fetchone()["id"]
        token = secrets.token_urlsafe(24)
        try:
            cur.execute("""INSERT INTO website_termine (kunden_id, termin_id, start, ende, name, email, telefon, nachricht, token)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id, start, ende, name, email, telefon, nachricht, token""",
                        (kid, tid, start, ende, d.name.strip(), email, d.telefon.strip() or None, d.nachricht.strip() or None, token))
        except Exception:
            raise HTTPException(409, voll)         # gleichzeitig gebucht: der Rest der Transaktion wird verworfen
        g = cur.fetchone()
        an = [a for a in _empfaenger(z["kal_empfaenger"] or z["mail_empfaenger"]) if EMAIL_RE.match(a)][:5]
        ids = push.kunde(cur, kid)
    wann = start.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
    push.senden(ids, "Neuer Termin über die Website", f"{d.name.strip()}: {wann}", "/app#heute", "termin")
    sd.ereignis(kid, "termin", True, "gebucht")
    bg.add_task(_termin_mails, kid, g, z, firma, an)
    return _antwort({"ok": True, "wann": wann}, kopf)


def _seite(text: str) -> HTMLResponse:
    return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Termin</title>'
                        f'<body style="font:16px system-ui;max-width:520px;margin:12vh auto;padding:0 20px;color:#0B1020"><p>{escape(text)}</p></body>')


@router.get("/site/{site_id}/termin/absagen", include_in_schema=False)
def oeff_absagen(site_id: str, t: str, request: Request, bg: BackgroundTasks):
    rate_limit("siteabsagen:" + client_ip(request), 20, 600)
    if not re.match(r"^mk_[A-Za-z0-9]{6,40}$", site_id) or not 10 <= len(t) <= 100:
        return _seite("Dieser Link ist ungültig.")
    with tx("system") as cur:
        cur.execute("""UPDATE website_termine w SET status='abgesagt' FROM website_dienste d
                       WHERE w.token=%s AND d.site_id=%s AND d.kunden_id=w.kunden_id AND w.status='gebucht' AND w.start > now()
                       RETURNING w.kunden_id, w.start, w.name, w.termin_id, d.mail_empfaenger, d.kal_empfaenger""", (t, site_id))
        g = cur.fetchone()
        if not g:
            return _seite("Dieser Termin ist nicht mehr aktiv.")
        if g["termin_id"]:
            cur.execute("UPDATE termine SET status='abgesagt' WHERE id=%s", (g["termin_id"],))
        ids = push.kunde(cur, g["kunden_id"])
    wann = g["start"].astimezone(TZ).strftime("%d.%m.%Y %H:%M")
    push.senden(ids, "Termin abgesagt", f"{g['name']} hat den Termin am {wann} Uhr abgesagt.", "/app#heute", "termin")
    for a in [x for x in _empfaenger(g["kal_empfaenger"] or g["mail_empfaenger"]) if EMAIL_RE.match(x)][:5]:
        bg.add_task(sd.kundenmail, g["kunden_id"], a, f"Termin abgesagt: {g['name']}", f"{g['name']} hat den Termin am {wann} Uhr abgesagt.", None, None, "termin")
    return _seite("Ihr Termin wurde abgesagt. Sie können jederzeit einen neuen buchen.")


@router.get("/site/{site_id}/bewertungen", include_in_schema=False)
def oeff_bewertungen(site_id: str, request: Request):
    z = _site(site_id)
    kopf = _cors(request, z)
    rate_limit("sitebew:" + client_ip(request), 60, 300)
    if not z["bew_aktiv"]:
        return _antwort({"aktiv": False}, kopf)
    return _antwort({"aktiv": True, **sd.bewertungen_fuer(z)}, kopf)


# =============================================================== Kunde (nur Inhaber)
kunde = APIRouter(prefix="/api/kunde/website-dienste")


def _status(cur, kid) -> dict:
    cur.execute("""SELECT art, count(*) FILTER (WHERE ok) AS ok, count(*) FILTER (WHERE NOT ok) AS fehler, max(zeit) AS zuletzt
                   FROM website_ereignisse WHERE kunden_id=%s AND zeit > now() - interval '30 days' GROUP BY art""", (kid,))
    out = {r["art"]: {"ok": r["ok"], "fehler": r["fehler"], "zuletzt": r["zuletzt"]} for r in cur.fetchall()}
    cur.execute("SELECT DISTINCT ON (art) art, ok, hinweis, zeit FROM website_ereignisse WHERE kunden_id=%s ORDER BY art, zeit DESC", (kid,))
    for r in cur.fetchall():
        out.setdefault(r["art"], {})["letzte"] = {"ok": r["ok"], "hinweis": r["hinweis"], "zeit": r["zeit"]}
    return out


def _zustand(cur, kid) -> dict:
    z = sd.zeile(cur, kid)
    cur.execute("SELECT count(*) AS n FROM website_termine WHERE kunden_id=%s AND status IN ('gebucht','reserviert') AND start > now()", (kid,))
    offen = cur.fetchone()["n"]
    places = bool(einstellungen.lesen(cur, "places").get("api_key"))
    hosts = sorted(h for h in sd.erlaubte_hosts(cur, kid, ROOT) if not h.startswith("demo.") and not h.startswith("www."))
    smtp = {}
    if z["smtp_enc"]:
        c = json.loads(einstellungen.entschluesseln(z["smtp_enc"]) or "{}")
        smtp = {"gesetzt": True, "absender": z["smtp_absender"], "host": c.get("host", ""), "port": c.get("port", 587), "sicherung": c.get("sicherung", "starttls"),
                "benutzer": c.get("benutzer", ""), "geprueft_am": z["smtp_geprueft_am"]}
    return {
        "site_id": z["site_id"], "domains": hosts, "basis": config.BASE_URL, "places_verfuegbar": places,
        "mail": {"aktiv": z["mail_aktiv"], "empfaenger": z["mail_empfaenger"] or "", "betreff": z["mail_betreff"] or "", "name": z["mail_name"] or "", "smtp": smtp},
        "kalender": {"aktiv": z["kal_aktiv"], "ical_gesetzt": bool(z["kal_ical_enc"]), "ical_geprueft_am": z["kal_ical_geprueft_am"], "dauer": z["kal_dauer"],
                     "tage": z["kal_tage"], "von": z["kal_von"], "bis": z["kal_bis"], "wochentage": z["kal_wochentage"], "vorlauf_std": z["kal_vorlauf_std"],
                     "ort": z["kal_ort"] or "", "empfaenger": z["kal_empfaenger"] or "", "offene_termine": offen,
                     "zeiten": z["kal_zeiten"] or "", "kapazitaet": z["kal_kapazitaet"], "freigabe": z["kal_freigabe"], "halte_std": z["kal_halte_std"]},
        "paypal": {"aktiv": z["pp_aktiv"], "client_id": z["pp_client_id"] or "", "waehrung": z["pp_waehrung"], "me_link": z["pp_me_link"] or ""},
        "analytics": {"aktiv": z["ga_aktiv"], "id": z["ga_id"] or "", "statistik": z["stat_aktiv"]},
        "bewertungen": {"aktiv": z["bew_aktiv"], "place_id": z["bew_place_id"] or "", "sterne": float(z["bew_sterne"]) if z["bew_sterne"] is not None else None,
                        "anzahl": z["bew_anzahl"], "link": z["bew_link"] or "", "stand": z["bew_stand"]},
        "status": _status(cur, kid),
    }


@kunde.get("")
def k_lesen(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        return _zustand(cur, user["kunden_id"])


@kunde.get("/anbieter")
def k_anbieter(email: str, user: dict = Depends(require_inhaber)):
    return sd.vorschlag(email)


def _empf_pruefen(text: str, pflicht: bool) -> str:
    liste = _empfaenger(text)
    if pflicht and not liste:
        raise HTTPException(400, "Bitte trage mindestens eine E-Mail-Adresse für den Empfang ein.")
    if len(liste) > 5 or any(not EMAIL_RE.match(a) for a in liste):
        raise HTTPException(400, "Eine der Empfänger-Adressen ist ungültig (höchstens 5, mit Komma getrennt).")
    return ", ".join(liste)


class MailIn(BaseModel):
    aktiv: bool = False
    empfaenger: str = Field(default="", max_length=400)
    betreff: str = Field(default="", max_length=120)
    name: str = Field(default="", max_length=80)


@kunde.put("/mail")
def k_mail(data: MailIn, user: dict = Depends(require_inhaber)):
    emp = _empf_pruefen(data.empfaenger, data.aktiv)
    with tx("system") as cur:
        sd.zeile(cur, user["kunden_id"])
        cur.execute("UPDATE website_dienste SET mail_aktiv=%s, mail_empfaenger=%s, mail_betreff=%s, mail_name=%s, geaendert_am=now() WHERE kunden_id=%s",
                    (data.aktiv, emp or None, data.betreff.strip() or None, data.name.strip() or None, user["kunden_id"]))
        audit(cur, user, "website_dienste_mail", user["kunden_id"], {"aktiv": data.aktiv})
    return {"ok": True}


class SmtpIn(BaseModel):
    absender: str = Field(max_length=200)
    host: str = Field(min_length=3, max_length=253)
    port: int = Field(ge=1, le=65535)
    sicherung: str = Field(default="starttls", pattern="^(starttls|ssl|keine)$")
    benutzer: str = Field(default="", max_length=200)
    passwort: str = Field(default="", max_length=300)


@kunde.put("/smtp")
def k_smtp(data: SmtpIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("smtppruef:" + str(kid), 12, 600)
    if not EMAIL_RE.match(data.absender.strip()):
        raise HTTPException(400, "Die Absender-Adresse ist ungültig.")
    if data.sicherung == "keine" and not config.SITE_LOKAL_ERLAUBT:
        raise HTTPException(400, "Bitte wähle STARTTLS oder SSL, unverschlüsselt wird nicht versendet.")
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        alt = json.loads(einstellungen.entschluesseln(z["smtp_enc"]) or "{}")
    c = {"host": data.host.strip().lower(), "port": data.port, "sicherung": data.sicherung, "benutzer": data.benutzer.strip() if data.sicherung == "keine" else (data.benutzer.strip() or data.absender.strip()),
         "passwort": data.passwort or alt.get("passwort", ""), "absender": data.absender.strip()}
    if not c["passwort"]:
        raise HTTPException(400, "Bitte trage das Passwort ein.")
    fehler = sd.smtp_pruefen(c)
    if fehler:
        raise HTTPException(400, fehler)
    with tx("system") as cur:
        cur.execute("UPDATE website_dienste SET smtp_enc=%s, smtp_absender=%s, smtp_geprueft_am=now(), geaendert_am=now() WHERE kunden_id=%s",
                    (einstellungen.verschluesseln(json.dumps(c)), c["absender"], kid))
        audit(cur, user, "website_dienste_smtp", kid, {"host": c["host"]})
    return {"ok": True}


@kunde.delete("/smtp")
def k_smtp_weg(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("UPDATE website_dienste SET smtp_enc=NULL, smtp_absender=NULL, smtp_geprueft_am=NULL, geaendert_am=now() WHERE kunden_id=%s", (user["kunden_id"],))
        audit(cur, user, "website_dienste_smtp_entfernt", user["kunden_id"], {})
    return {"ok": True}


class TestIn(BaseModel):
    an: str = Field(max_length=200)


@kunde.post("/mail/test")
def k_mail_test(data: TestIn, user: dict = Depends(require_inhaber)):
    """Schickt eine Testmail auf dem Weg, den auch die Website nutzt (eigenes Postfach, sonst Markentrix)."""
    kid = user["kunden_id"]
    rate_limit("mailtest:" + str(kid), 8, 600)
    if not EMAIL_RE.match(data.an.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    ok, via = sd.kundenmail(kid, data.an.strip(), "Testnachricht von Ihrer Website", "Das ist eine Testnachricht. Das Kontaktformular Ihrer Website kann E-Mails versenden.", art="test")
    if not ok:
        raise HTTPException(400, "Der Versand ist fehlgeschlagen: " + via)
    return {"ok": True, "ueber": via}


class KalenderIn(BaseModel):
    aktiv: bool = False
    ical_url: str = Field(default="", max_length=1500)          # leer = unverändert
    dauer: int = Field(default=30, ge=10, le=240)
    tage: int = Field(default=14, ge=1, le=90)
    von: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    bis: str = Field(default="17:00", pattern=r"^\d{2}:\d{2}$")
    wochentage: list[int] = Field(default=[1, 2, 3, 4, 5], max_length=7)
    vorlauf_std: int = Field(default=12, ge=0, le=240)
    ort: str = Field(default="", max_length=300)
    empfaenger: str = Field(default="", max_length=400)
    zeiten: str = Field(default="", max_length=300)             # feste Uhrzeiten "08:00, 10:00"; leer = Raster
    kapazitaet: int = Field(default=0, ge=0, le=200)
    freigabe: bool = False
    halte_std: int = Field(default=72, ge=1, le=336)


@kunde.put("/kalender")
def k_kalender(data: KalenderIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("kalpruef:" + str(kid), 12, 600)
    if data.von >= data.bis:
        raise HTTPException(400, "Das Ende muss nach dem Beginn liegen.")
    if not data.wochentage or any(w < 1 or w > 7 for w in data.wochentage):
        raise HTTPException(400, "Bitte wähle mindestens einen Wochentag.")
    emp = _empf_pruefen(data.empfaenger, False)
    zeiten = [x.strip() for x in re.split(r"[,;\s]+", data.zeiten) if x.strip()]
    if any(not sd.ZEIT_RE.match(x) for x in zeiten) or len(zeiten) > 24:
        raise HTTPException(400, "Die Uhrzeiten bitte so eintragen: 08:00, 10:00, 13:30.")
    enc, geprueft = None, None
    if data.ical_url.strip():
        try:
            u = sd.ical_url_pruefen(data.ical_url)
            sd.ical_belegt(sd.ical_laden(u), datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=30))
        except ValueError as e:
            raise HTTPException(400, str(e))
        enc, geprueft = einstellungen.verschluesseln(u), datetime.now(timezone.utc)
    with tx("system") as cur:
        sd.zeile(cur, kid)
        cur.execute("""UPDATE website_dienste SET kal_aktiv=%s, kal_dauer=%s, kal_tage=%s, kal_von=%s, kal_bis=%s, kal_wochentage=%s, kal_vorlauf_std=%s,
                       kal_ort=%s, kal_empfaenger=%s, kal_ical_enc=coalesce(%s, kal_ical_enc), kal_ical_geprueft_am=coalesce(%s, kal_ical_geprueft_am),
                       kal_zeiten=%s, kal_kapazitaet=%s, kal_freigabe=%s, kal_halte_std=%s, geaendert_am=now()
                       WHERE kunden_id=%s""",
                    (data.aktiv, data.dauer, data.tage, data.von, data.bis, sorted(set(data.wochentage)), data.vorlauf_std, data.ort.strip() or None, emp or None, enc, geprueft,
                     ", ".join(sorted(set(zeiten))) or None, data.kapazitaet, data.freigabe, data.halte_std, kid))
        audit(cur, user, "website_dienste_kalender", kid, {"aktiv": data.aktiv})
    sd._ical_cache.pop(str(kid), None)
    return {"ok": True}


@kunde.delete("/kalender-adresse")
def k_kal_weg(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("UPDATE website_dienste SET kal_ical_enc=NULL, kal_ical_geprueft_am=NULL, geaendert_am=now() WHERE kunden_id=%s", (user["kunden_id"],))
        audit(cur, user, "website_dienste_kalender_entfernt", user["kunden_id"], {})
    sd._ical_cache.pop(str(user["kunden_id"]), None)
    return {"ok": True}


@kunde.post("/kalender/test")
def k_kal_test(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("kaltest:" + str(kid), 12, 600)
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        if z["kal_ical_enc"]:
            try:
                n = len(sd.kalender_belegt(z, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=z["kal_tage"])))
            except ValueError as e:
                raise HTTPException(400, str(e))
        else:
            n = None
        slots = sd.freie_slots(cur, z)
    erste = [s.astimezone(TZ).strftime("%d.%m. %H:%M") for s in slots[:4]]
    return {"ok": True, "belegt": n, "freie": len(slots), "beispiele": erste}


class PayPalIn(BaseModel):
    aktiv: bool = False
    client_id: str = Field(default="", max_length=140)
    waehrung: str = Field(default="EUR", pattern="^(EUR|CHF|USD|GBP|PLN|CZK|DKK|SEK|NOK)$")
    me_link: str = Field(default="", max_length=200)


@kunde.put("/paypal")
def k_paypal(data: PayPalIn, user: dict = Depends(require_inhaber)):
    cid, link = data.client_id.strip(), data.me_link.strip()
    if cid and not re.match(r"^[A-Za-z0-9_-]{20,140}$", cid):
        raise HTTPException(400, "Die Client-ID sieht ungültig aus. Sie ist eine lange Zeichenfolge, die oft mit „A“ beginnt.")
    if link and not re.match(r"^https://(www\.)?(paypal\.me|paypal\.com/paypalme)/[A-Za-z0-9._/-]{2,80}$", link):
        raise HTTPException(400, "Der PayPal.Me-Link muss so aussehen: https://paypal.me/deinname")
    if data.aktiv and not (cid or link):
        raise HTTPException(400, "Bitte trage die Client-ID oder deinen PayPal.Me-Link ein.")
    with tx("system") as cur:
        sd.zeile(cur, user["kunden_id"])
        cur.execute("UPDATE website_dienste SET pp_aktiv=%s, pp_client_id=%s, pp_waehrung=%s, pp_me_link=%s, geaendert_am=now() WHERE kunden_id=%s",
                    (data.aktiv, cid or None, data.waehrung, link or None, user["kunden_id"]))
        audit(cur, user, "website_dienste_paypal", user["kunden_id"], {"aktiv": data.aktiv})
    return {"ok": True}


class AnalyticsIn(BaseModel):
    aktiv: bool = False
    id: str = Field(default="", max_length=20)


@kunde.put("/analytics")
def k_analytics(data: AnalyticsIn, user: dict = Depends(require_inhaber)):
    gid = data.id.strip().upper()
    if gid and not re.match(r"^G-[A-Z0-9]{6,14}$", gid):
        raise HTTPException(400, "Die Mess-ID sieht ungültig aus. Sie beginnt mit „G-“, zum Beispiel G-AB12CD34EF.")
    if data.aktiv and not gid:
        raise HTTPException(400, "Bitte trage die Mess-ID ein.")
    with tx("system") as cur:
        sd.zeile(cur, user["kunden_id"])
        cur.execute("UPDATE website_dienste SET ga_aktiv=%s, ga_id=%s, geaendert_am=now() WHERE kunden_id=%s", (data.aktiv, gid or None, user["kunden_id"]))
        audit(cur, user, "website_dienste_analytics", user["kunden_id"], {"aktiv": data.aktiv})
    return {"ok": True}


class BewertungIn(BaseModel):
    aktiv: bool = False
    place_id: str = Field(default="", max_length=200)
    sterne: float | None = Field(default=None, ge=1, le=5)
    anzahl: int | None = Field(default=None, ge=0, le=1000000)
    link: str = Field(default="", max_length=400)


@kunde.put("/bewertungen")
def k_bewertungen(data: BewertungIn, user: dict = Depends(require_inhaber)):
    pid, link = data.place_id.strip(), data.link.strip()
    if pid and not sd.PLACE_ID.match(pid):
        raise HTTPException(400, "Die Place-ID sieht ungültig aus. Sie beginnt meist mit „ChIJ“.")
    if link and not re.match(r"^https://[^\s]{4,380}$", link):
        raise HTTPException(400, "Der Bewertungs-Link muss mit https:// beginnen.")
    if data.aktiv and not (pid or data.sterne):
        raise HTTPException(400, "Bitte trage die Place-ID oder Sterne und Anzahl ein.")
    with tx("system") as cur:
        sd.zeile(cur, user["kunden_id"])
        cur.execute("""UPDATE website_dienste SET bew_aktiv=%s, bew_place_id=%s, bew_sterne=%s, bew_anzahl=%s, bew_link=%s, bew_cache=NULL, bew_stand=NULL, geaendert_am=now()
                       WHERE kunden_id=%s""", (data.aktiv, pid or None, data.sterne, data.anzahl, link or None, user["kunden_id"]))
        audit(cur, user, "website_dienste_bewertungen", user["kunden_id"], {"aktiv": data.aktiv})
    return {"ok": True}


@kunde.post("/bewertungen/test")
def k_bew_test(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("bewtest:" + str(kid), 10, 600)
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        key = einstellungen.lesen(cur, "places").get("api_key", "")
    if not z["bew_place_id"]:
        raise HTTPException(400, "Bitte speichere zuerst die Place-ID.")
    if not key:
        raise HTTPException(400, "Die automatische Anzeige ist bei Markentrix noch nicht freigeschaltet. Trage solange Sterne und Anzahl von Hand ein.")
    try:
        r = sd.places_holen(key, z["bew_place_id"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    with tx("system") as cur:
        cur.execute("UPDATE website_dienste SET bew_cache=%s::jsonb, bew_stand=now() WHERE kunden_id=%s", (json.dumps(r), kid))
    return {"ok": True, "sterne": r["sterne"], "anzahl": r["anzahl"]}


# =============================================================== Admin: Status ohne Geheimnisse, Google-Schlüssel
admin = APIRouter(prefix="/api/admin")


# =============================================================== Buchungen, Sperrtage, Statistik (Inhaber)
@kunde.get("/buchungen")
def k_buchungen(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        sd.reservierungen_verfallen(cur, kid, z["kal_halte_std"])
        cur.execute("""SELECT id, ref, status, start, name, email, telefon, nachricht, daten, anzahlung, erstellt_am FROM website_termine
                       WHERE kunden_id=%s AND status IN ('reserviert','gebucht') AND start > now() - interval '1 day'
                       ORDER BY (status='reserviert') DESC, start LIMIT 100""", (kid,))
        zeilen = cur.fetchall()
    out = []
    for r in zeilen:
        d = r["daten"] or {}
        details = {k: v for k, v in d.items() if k not in ("typ", "name", "telefon", "email", "nachricht", "datum", "datum2", "uhrzeit") and v}
        out.append({"id": str(r["id"]), "ref": r["ref"] or "", "status": r["status"], "start": r["start"], "name": r["name"], "email": r["email"], "telefon": r["telefon"] or "",
                    "nachricht": r["nachricht"] or "", "details": details, "anzahlung": r["anzahlung"] or ""})
    return {"buchungen": out, "freigabe": z["kal_freigabe"]}


class BestaetigenIn(BaseModel):
    anzahlung: str = Field(default="", max_length=20)
    hinweis: str = Field(default="", max_length=600)


def _betrag(text: str) -> str:
    t = text.strip().replace("€", "").replace(",", ".").strip()
    if not t:
        return ""
    try:
        v = float(t)
    except ValueError:
        raise HTTPException(400, "Bitte die Anzahlung als Zahl eintragen, z. B. 30 oder 29,90.")
    if not 0 < v <= 100000:
        raise HTTPException(400, "Bitte die Anzahlung als Zahl eintragen, z. B. 30 oder 29,90.")
    return f"{v:.2f}"


@kunde.post("/buchungen/{bid}/bestaetigen")
def k_bestaetigen(bid: str, data: BestaetigenIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("buchbest:" + str(kid), 60, 600)
    betrag = _betrag(data.anzahlung)
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        try:
            cur.execute("""UPDATE website_termine SET status='gebucht', anzahlung=%s WHERE id=%s AND kunden_id=%s AND status='reserviert' AND start > now()
                           RETURNING id, termin_id, start, ende, name, email, telefon, nachricht, token, ref""", (betrag or None, bid, kid))
        except Exception:
            raise HTTPException(400, "Ungültige Buchung.")
        g = cur.fetchone()
        if not g:
            raise HTTPException(409, "Diese Buchung ist nicht mehr offen (bestätigt, abgelehnt oder abgelaufen).")
        if g["termin_id"]:
            cur.execute("UPDATE termine SET status='bestaetigt' WHERE id=%s", (g["termin_id"],))
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = cur.fetchone()["firma"]
        audit(cur, user, "website_buchung_bestaetigt", kid, {"ref": g["ref"]})
    bg.add_task(_bestaetigung_mail, kid, g, z, firma, betrag, data.hinweis.strip())
    return {"ok": True}


def _bestaetigung_mail(kid, g: dict, z: dict, firma: str, betrag: str, hinweis: str):
    lokal = g["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
    absagen = f"{config.BASE_URL}/site/{z['site_id']}/termin/absagen?t={g['token']}"
    zahlung = ""
    if betrag:
        me = (z["pp_me_link"] or "").strip().rstrip("/")
        zahlung = f"\nZur Sicherung des Termins bitten wir um eine Anzahlung von {betrag.replace('.', ',')} €."
        if z["pp_aktiv"] and me.startswith("https://"):
            zahlung += f"\nSie können bequem per PayPal zahlen: {me}/{betrag}{z['pp_waehrung']}"
    text = (f"Guten Tag {g['name']},\n\nIhr Termin ist bestätigt: {lokal}.{(chr(10) + z['kal_ort']) if z['kal_ort'] else ''}\n{zahlung}\n"
            f"{(chr(10) + hinweis + chr(10)) if hinweis else ''}\nDie Kalendereinladung hängt an. Falls Sie nicht können, sagen Sie bitte hier ab:\n{absagen}\n\nBis bald!\n{firma}")
    sd.kundenmail(kid, g["email"], f"Ihr Termin bei {firma} am {lokal} ist bestätigt", text,
                  anhang=("termin.ics", sd.ics(str(g["id"]), g["start"], g["ende"], "Termin bei " + firma, z["kal_ort"] or ""), "text/calendar"), art="termin")


class AblehnenIn(BaseModel):
    grund: str = Field(default="", max_length=600)


@kunde.post("/buchungen/{bid}/ablehnen")
def k_ablehnen(bid: str, data: AblehnenIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("buchabl:" + str(kid), 60, 600)
    with tx("system") as cur:
        try:
            cur.execute("""UPDATE website_termine SET status='abgesagt' WHERE id=%s AND kunden_id=%s AND status IN ('reserviert','gebucht') AND start > now()
                           RETURNING termin_id, start, name, email, ref""", (bid, kid))
        except Exception:
            raise HTTPException(400, "Ungültige Buchung.")
        g = cur.fetchone()
        if not g:
            raise HTTPException(409, "Diese Buchung ist nicht mehr offen.")
        if g["termin_id"]:
            cur.execute("UPDATE termine SET status='abgesagt' WHERE id=%s", (g["termin_id"],))
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = cur.fetchone()["firma"]
        audit(cur, user, "website_buchung_abgelehnt", kid, {"ref": g["ref"]})
    lokal = g["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
    bg.add_task(sd.kundenmail, kid, g["email"], f"Zu Ihrem Termin am {lokal}",
                f"Guten Tag {g['name']},\n\nleider können wir den gewünschten Termin am {lokal} nicht anbieten.\n{(data.grund.strip() + chr(10)) if data.grund.strip() else ''}"
                f"Auf unserer Website können Sie jederzeit einen anderen Termin wählen.\n\nViele Grüße\n{firma}", None, None, "termin")
    return {"ok": True}


@kunde.get("/sperrtage")
def k_sperrtage(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("SELECT tag, grund FROM website_sperrtage WHERE kunden_id=%s AND tag >= current_date ORDER BY tag LIMIT 400", (user["kunden_id"],))
        return {"tage": [{"tag": r["tag"].isoformat(), "grund": r["grund"] or ""} for r in cur.fetchall()]}


class SperrIn(BaseModel):
    von: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    bis: str = Field(default="", pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    grund: str = Field(default="", max_length=80)


@kunde.post("/sperrtage")
def k_sperre(data: SperrIn, user: dict = Depends(require_inhaber)):
    try:
        a = date.fromisoformat(data.von)
        b = date.fromisoformat(data.bis) if data.bis else a
    except ValueError:
        raise HTTPException(400, "Das Datum ist ungültig.")
    if b < a or (b - a).days > 120:
        raise HTTPException(400, "Der Zeitraum ist ungültig (höchstens 120 Tage am Stück).")
    with tx("system") as cur:
        for i in range((b - a).days + 1):
            cur.execute("INSERT INTO website_sperrtage (kunden_id, tag, grund) VALUES (%s,%s,%s) ON CONFLICT (kunden_id, tag) DO UPDATE SET grund=excluded.grund",
                        (user["kunden_id"], a + timedelta(days=i), data.grund.strip() or None))
    return {"ok": True}


@kunde.delete("/sperrtage/{tag}")
def k_sperre_weg(tag: str, user: dict = Depends(require_inhaber)):
    try:
        t = date.fromisoformat(tag)
    except ValueError:
        raise HTTPException(400, "Das Datum ist ungültig.")
    with tx("system") as cur:
        cur.execute("DELETE FROM website_sperrtage WHERE kunden_id=%s AND tag=%s", (user["kunden_id"], t))
    return {"ok": True}


class StatIn(BaseModel):
    aktiv: bool


@kunde.put("/statistik-schalter")
def k_stat_schalter(data: StatIn, user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        sd.zeile(cur, user["kunden_id"])
        cur.execute("UPDATE website_dienste SET stat_aktiv=%s, geaendert_am=now() WHERE kunden_id=%s", (data.aktiv, user["kunden_id"]))
    return {"ok": True}


@kunde.get("/statistik")
def k_statistik(tage: int = 30, user: dict = Depends(require_inhaber)):
    tage = max(1, min(tage, 365))
    kid = user["kunden_id"]
    with tx("system") as cur:
        q = lambda sql, *a: (cur.execute(sql, a), cur.fetchall())[1]  # noqa: E731
        ges = q("""SELECT count(*) FILTER (WHERE art='pv') AS aufrufe, count(DISTINCT tag::text || besucher) FILTER (WHERE art='pv') AS besucher,
                          count(*) FILTER (WHERE art='ev' AND name ILIKE 'WhatsApp%%') AS whatsapp, count(*) FILTER (WHERE art='ev' AND name ILIKE 'Anruf%%') AS anrufe
                   FROM website_stat WHERE kunden_id=%s AND tag > current_date - %s""", kid, tage)[0]
        cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND quelle='website' AND erstellt_am > now() - make_interval(days => %s)", (kid, tage))
        anfragen = cur.fetchone()["n"]
        seiten = q("SELECT pfad, count(*) AS aufrufe FROM website_stat WHERE kunden_id=%s AND art='pv' AND tag > current_date - %s GROUP BY pfad ORDER BY 2 DESC LIMIT 10", kid, tage)
        quellen = q("""SELECT coalesce(quelle, 'Direkt / unbekannt') AS quelle, count(DISTINCT tag::text || besucher) AS besucher FROM website_stat
                       WHERE kunden_id=%s AND art='pv' AND tag > current_date - %s GROUP BY 1 ORDER BY 2 DESC LIMIT 8""", kid, tage)
        verlauf = q("SELECT tag, count(*) AS aufrufe FROM website_stat WHERE kunden_id=%s AND art='pv' AND tag > current_date - %s GROUP BY tag ORDER BY tag", kid, tage)
    return {"tage": tage, "besucher": ges["besucher"], "aufrufe": ges["aufrufe"], "whatsapp": ges["whatsapp"], "anrufe": ges["anrufe"], "anfragen": anfragen,
            "seiten": seiten, "quellen": quellen, "verlauf": [{"tag": r["tag"].isoformat(), "aufrufe": r["aufrufe"]} for r in verlauf]}


@admin.get("/kunden/{kid}/website-dienste")
def a_status(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise HTTPException(404, "Kunde nicht gefunden.")
            d = _zustand(cur, kid)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Kunde nicht gefunden.")
    d["mail"]["smtp"].pop("benutzer", None)
    return d


class PlacesIn(BaseModel):
    api_key: str = Field(default="", max_length=300)


@admin.put("/einstellungen/places")
def a_places(data: PlacesIn, user: dict = Depends(require_admin)):
    if not config.PORTAL_SECRET:
        raise HTTPException(500, "PORTAL_SECRET fehlt in der .env. Bitte install.sh erneut ausführen.")
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "places")
        key = data.api_key.strip() or alt.get("api_key", "")
        einstellungen.schreiben(cur, "places", {"api_key": key})
        audit(cur, user, "einstellungen_places", None, {"gesetzt": bool(key)})
    return {"ok": True}


@admin.get("/einstellungen/places")
def a_places_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return {"key_gesetzt": bool(einstellungen.lesen(cur, "places").get("api_key"))}
