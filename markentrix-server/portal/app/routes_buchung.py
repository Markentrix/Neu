"""Terminbuchung: Interessenten wählen selbst einen freien Termin für ein Erstgespräch."""
import re
import secrets
from datetime import datetime, timedelta, timezone
from html import escape
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import config, einstellungen, leadeingang, mailer, push
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin

router = APIRouter(prefix="/api")
TZ = ZoneInfo("Europe/Berlin")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

STANDARD = {"aktiv": False, "dauer": 30, "tage": 14, "von": "09:00", "bis": "17:00", "wochentage": [1, 2, 3, 4, 5],
            "vorlauf_std": 12, "ort": "Telefon oder Videocall, wir melden uns zum Termin bei Ihnen."}


class BuchungEinst(BaseModel):
    aktiv: bool = False
    dauer: int = Field(default=30, ge=15, le=120)
    tage: int = Field(default=14, ge=1, le=60)
    von: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    bis: str = Field(default="17:00", pattern=r"^\d{2}:\d{2}$")
    wochentage: list[int] = Field(default=[1, 2, 3, 4, 5], max_length=7)
    vorlauf_std: int = Field(default=12, ge=0, le=240)
    ort: str = Field(default=STANDARD["ort"], max_length=300)


def lesen(cur) -> dict:
    return {**STANDARD, **(einstellungen.lesen(cur, "buchung") or {})}


@router.get("/admin/einstellungen/buchung")
def einst_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return lesen(cur)


@router.put("/admin/einstellungen/buchung")
def einst_speichern(data: BuchungEinst, user: dict = Depends(require_admin)):
    if data.von >= data.bis:
        raise HTTPException(400, "Das Ende muss nach dem Beginn liegen.")
    if any(w < 1 or w > 7 for w in data.wochentage):
        raise HTTPException(400, "Ungültiger Wochentag.")
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "buchung", data.model_dump())
        audit(cur, user, "einstellungen_buchung", None, {"aktiv": data.aktiv})
    return {"ok": True}


@router.get("/admin/gespraeche")
def gespraeche(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT g.id, g.start, g.ende, g.name, g.email, g.telefon, g.nachricht, g.status, g.lead_id, l.firma
                       FROM gespraechstermine g LEFT JOIN leads l ON l.id=g.lead_id
                       WHERE g.start > now() - interval '1 day' ORDER BY g.start LIMIT 100""")
        return cur.fetchall()


def _slots(cur, c: dict) -> list[datetime]:
    jetzt = datetime.now(timezone.utc)
    frueh = jetzt + timedelta(hours=c["vorlauf_std"])
    h1, m1 = map(int, c["von"].split(":"))
    h2, m2 = map(int, c["bis"].split(":"))
    ende_ges = jetzt + timedelta(days=c["tage"] + 1)
    cur.execute("SELECT start FROM gespraechstermine WHERE status='gebucht' AND start >= %s AND start < %s", (jetzt, ende_ges))
    belegt = {r["start"] for r in cur.fetchall()}
    heute = datetime.now(TZ).date()
    liste = []
    for i in range(c["tage"] + 1):
        tag = heute + timedelta(days=i)
        if tag.isoweekday() not in c["wochentage"]:
            continue
        t = datetime(tag.year, tag.month, tag.day, h1, m1, tzinfo=TZ)
        schluss = datetime(tag.year, tag.month, tag.day, h2, m2, tzinfo=TZ)
        while t + timedelta(minutes=c["dauer"]) <= schluss:
            u = t.astimezone(timezone.utc)
            if u >= frueh and u not in belegt:
                liste.append(u)
            t += timedelta(minutes=c["dauer"])
    return liste


@router.get("/public/buchung/slots")
def slots(request: Request):
    rate_limit("slots:" + client_ip(request), 60, 300)
    with tx("system") as cur:
        c = lesen(cur)
        if not c["aktiv"]:
            return {"aktiv": False, "tage": []}
        tage: dict = {}
        for s in _slots(cur, c):
            lokal = s.astimezone(TZ)
            tage.setdefault(lokal.strftime("%Y-%m-%d"), []).append({"start": s.isoformat(), "uhr": lokal.strftime("%H:%M")})
    return {"aktiv": True, "dauer": c["dauer"], "ort": c["ort"], "tage": [{"datum": d, "slots": s} for d, s in tage.items()]}


class BuchenIn(BaseModel):
    start: str = Field(max_length=40)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=200)
    telefon: str | None = Field(default=None, max_length=60)
    nachricht: str | None = Field(default=None, max_length=1500)
    einwilligung: bool = False


def ics(g_id: str, start: datetime, ende: datetime, titel: str, ort: str, abgesagt: bool = False) -> bytes:
    f = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Markentrix//Portal//DE", "METHOD:" + ("CANCEL" if abgesagt else "PUBLISH"), "BEGIN:VEVENT",
         f"UID:{g_id}@markentrix.de", f"DTSTAMP:{f(datetime.now(timezone.utc))}", f"DTSTART:{f(start)}", f"DTEND:{f(ende)}",
         f"SUMMARY:{titel}", f"LOCATION:{ort.replace(chr(10), ' ').replace(',', ' ')}", "STATUS:" + ("CANCELLED" if abgesagt else "CONFIRMED"), "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(z) + "\r\n").encode()


def _mails(g: dict, ort: str, an_team: list):
    lokal = g["start"].astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")
    absagen = f"{config.BASE_URL}/api/public/buchung/absagen?t={g['token']}"
    anhang = ("termin.ics", ics(str(g["id"]), g["start"], g["ende"], "Erstgespräch mit Markentrix", ort), "text/calendar")
    mailer.senden(g["email"], "Ihr Gespräch mit Markentrix am " + lokal,
                  f"Guten Tag {g['name']},\n\nIhr Termin ist gebucht: {lokal}.\n{ort}\n\nDie Kalendereinladung hängt an. Falls Sie nicht können, sagen Sie bitte hier ab: {absagen}" + mailer.SIGNATUR, anhang)
    for a in an_team:
        mailer.senden(a, f"Neues Gespräch gebucht: {g['name']} am {lokal}",
                      f"{g['name']} ({g['email']}, {g.get('telefon') or 'keine Nummer'}) hat ein Erstgespräch gebucht: {lokal}.\n\n{g.get('nachricht') or ''}\n\nDer Lead wurde im Portal auf 'Termin' gesetzt: {config.BASE_URL}/admin", anhang)


def _lead_partner(cur, lid):
    cur.execute("SELECT vertriebspartner_id FROM leads WHERE id=%s AND vertriebspartner_id IS NOT NULL", (lid,))
    return cur.fetchone()


@router.post("/public/buchung")
def buchen(data: BuchenIn, bg: BackgroundTasks, request: Request):
    rate_limit("buchen:" + client_ip(request), 10, 3600)
    email = data.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not data.einwilligung:
        raise HTTPException(400, "Bitte stimmen Sie der Verarbeitung Ihrer Angaben zu.")
    try:
        start = datetime.fromisoformat(data.start).astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(400, "Ungültiger Termin.")
    with tx("system") as cur:
        c = lesen(cur)
        if not c["aktiv"] or start not in _slots(cur, c):
            raise HTTPException(409, "Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie einen anderen.")
        ende = start + timedelta(minutes=c["dauer"])
        token = secrets.token_urlsafe(24)
        cur.execute("SELECT id, status FROM leads WHERE lower(email)=%s ORDER BY erstellt_am LIMIT 1", (email,))
        l = cur.fetchone()
        if l:
            lid = l["id"]
            cur.execute("""UPDATE leads SET status = CASE WHEN status IN ('neu','kontaktiert','antwort') THEN 'termin' ELSE status END,
                           temperatur='heiss', wiedervorlage_am=%s, telefon=coalesce(telefon,%s),
                           loeschen_nach=greatest(loeschen_nach, current_date + interval '12 months') WHERE id=%s""",
                        (start.astimezone(TZ).date(), (data.telefon or "").strip() or None, lid))
        else:
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, quelle, status, temperatur, wiedervorlage_am, loeschen_nach, notiz)
                           VALUES (%s,%s,%s,%s,'website','termin','heiss',%s, current_date + interval '12 months', 'Über die Terminbuchung auf markentrix.de') RETURNING id""",
                        (data.name.strip(), data.name.strip(), email, (data.telefon or "").strip() or None, start.astimezone(TZ).date()))
            lid = cur.fetchone()["id"]
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent','Einwilligung bei der Terminbuchung erteilt','website')", (lid,))
        try:
            cur.execute("""INSERT INTO gespraechstermine (start, ende, name, email, telefon, nachricht, lead_id, token)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id, start, ende, name, email, telefon, nachricht, token""",
                        (start, ende, data.name.strip(), email, (data.telefon or "").strip() or None, (data.nachricht or "").strip() or None, lid, token))
        except Exception:
            raise HTTPException(409, "Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie einen anderen.")
        g = cur.fetchone()
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'termin',%s,'website')",
                    (lid, "Gespräch gebucht für " + start.astimezone(TZ).strftime("%d.%m.%Y %H:%M") + " Uhr"))
        an = [x for x in [admin_empfaenger(cur)] if x]
        ort = c["ort"]
        ids = push.admins(cur) + leadeingang.bearbeiten(cur, lid, not l, "Terminbuchung")
    push.senden(ids, "Neues Gespräch gebucht", "Ein Interessent hat ein Erstgespräch gebucht.", "/admin#leads", "buchung")
    bg.add_task(_mails, g, ort, an)
    return {"ok": True, "wann": start.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")}


def _seite(text: str) -> HTMLResponse:
    return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Markentrix</title>'
                        f'<body style="font:16px system-ui;max-width:520px;margin:12vh auto;padding:0 20px;color:#0B1020"><h2>Markentrix</h2><p>{escape(text)}</p></body>')


@router.get("/public/buchung/absagen")
def absagen_frage(t: str):
    """Erst nach Klick auf den Knopf wird abgesagt (Mail-Scanner rufen Links vorab ab)."""
    if len(t) < 10 or len(t) > 100:
        return _seite("Dieser Link ist ungültig.")
    return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Markentrix</title>'
                        '<body style="font:16px system-ui;max-width:520px;margin:12vh auto;padding:0 20px;color:#0B1020"><h2>Markentrix</h2><p>Möchten Sie Ihr Gespräch absagen?</p>'
                        f'<form method="post"><input type="hidden" name="t" value="{escape(t)}"><button style="font:inherit;padding:10px 18px;border-radius:8px;border:0;background:#0B1020;color:#fff;cursor:pointer">Ja, Termin absagen</button></form></body>')


@router.post("/public/buchung/absagen")
def absagen(request: Request, bg: BackgroundTasks, t: str = Form("")):
    rate_limit("absagen:" + client_ip(request), 20, 600)
    if len(t) < 10 or len(t) > 100:
        return _seite("Dieser Link ist ungültig.")
    with tx("system") as cur:
        cur.execute("UPDATE gespraechstermine SET status='abgesagt' WHERE token=%s AND status='gebucht' AND start > now() RETURNING id, start, name, lead_id", (t,))
        g = cur.fetchone()
        if not g:
            return _seite("Dieser Termin ist nicht mehr aktiv.")
        ids = []
        if g["lead_id"]:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'termin','Gespräch vom Interessenten abgesagt','website')", (g["lead_id"],))
            # Lead zurück in die Bearbeitung: nicht mehr „Termin“, Wiedervorlage heute, Zuständiger erfährt es
            cur.execute("UPDATE leads SET status=CASE WHEN status='termin' THEN 'antwort' ELSE status END, wiedervorlage_am=current_date WHERE id=%s AND kunden_id IS NULL AND status NOT IN ('verloren','tot','gesperrt')", (g["lead_id"],))
            lp = _lead_partner(cur, g["lead_id"])
            ids = push.partner(cur, lp["vertriebspartner_id"]) if lp else []
        an = [x for x in [admin_empfaenger(cur)] if x]
    if ids:
        push.senden(ids, "Gespräch abgesagt", f"{g['name']} hat abgesagt. Bitte neu vereinbaren.", "/vertrieb#heute", "buchung")
    wann = g["start"].astimezone(TZ).strftime("%d.%m.%Y %H:%M")
    for a in an:
        bg.add_task(mailer.senden, a, f"Gespräch abgesagt: {g['name']}", f"{g['name']} hat das Gespräch am {wann} Uhr abgesagt.")
    return _seite("Ihr Termin wurde abgesagt. Sie können jederzeit einen neuen buchen.")
