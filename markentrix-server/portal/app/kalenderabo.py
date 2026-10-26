"""Kalender-Abo für Vertriebler: fällige Wiedervorlagen und gebuchte Erstgespräche als Kalender-Link (iCalendar), z. B. für den Handy-Kalender.
Der Link enthält ein geheimes Zeichen statt einer Anmeldung. Wer ihn kennt, sieht Firmennamen und Telefonnummern der Wiedervorlagen. Mit „Neuen Link erzeugen“ wird der alte ungültig."""
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from . import config
from .db import tx
from .security import client_ip, rate_limit, require_vertrieb

vertrieb = APIRouter(prefix="/api/vertrieb")
public = APIRouter(prefix="/api/public")


def _text(s) -> str:
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _falten(zeile: str) -> str:
    roh = zeile.encode()
    if len(roh) <= 74:
        return zeile
    teile, i = [], 0
    while i < len(roh):
        j = min(i + (74 if i == 0 else 73), len(roh))
        while j < len(roh) and (roh[j] & 0xC0) == 0x80:   # nie mitten in einem Zeichen trennen
            j -= 1
        teile.append(roh[i:j].decode())
        i = j
    return "\r\n ".join(teile)


def kalender_text(name: str, wiedervorlagen: list[dict], gespraeche: list[dict]) -> str:
    jetzt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Markentrix//Portal//DE", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_text('Markentrix Wiedervorlagen')}",
         "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H"]
    for w in wiedervorlagen:
        tag: date = w["wiedervorlage_am"]
        beschr = "\n".join(x for x in (f"Telefon: {w['telefon']}" if w["telefon"] else "", f"Ansprechpartner: {w['ansprechpartner']}" if w["ansprechpartner"] else "", f"{config.BASE_URL.rstrip('/')}/vertrieb#lead/{w['id']}") if x)
        z += ["BEGIN:VEVENT", f"UID:wv-{w['id']}@markentrix", f"DTSTAMP:{jetzt}", f"DTSTART;VALUE=DATE:{tag:%Y%m%d}", f"DTEND;VALUE=DATE:{tag + timedelta(days=1):%Y%m%d}",
              f"SUMMARY:{_text('Anrufen: ' + w['firma'])}", f"DESCRIPTION:{_text(beschr)}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    for g in gespraeche:
        beschr = "\n".join(x for x in (f"Telefon: {g['telefon']}" if g["telefon"] else "", f"E-Mail: {g['email']}" if g["email"] else "") if x)
        z += ["BEGIN:VEVENT", f"UID:gt-{g['id']}@markentrix", f"DTSTAMP:{jetzt}", f"DTSTART:{g['start'].astimezone(timezone.utc):%Y%m%dT%H%M%SZ}", f"DTEND:{g['ende'].astimezone(timezone.utc):%Y%m%dT%H%M%SZ}",
              f"SUMMARY:{_text('Erstgespräch: ' + (g['firma'] or g['name']))}", f"DESCRIPTION:{_text(beschr)}", "END:VEVENT"]
    z.append("END:VCALENDAR")
    return "\r\n".join(_falten(x) for x in z) + "\r\n"


def _link(token: str) -> dict:
    basis = config.BASE_URL.rstrip("/")
    https = f"{basis}/api/public/kalender/{token}.ics"
    return {"https": https, "webcal": "webcal://" + https.split("://", 1)[1]}


@vertrieb.get("/kalender-link")
def link(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("SELECT kalender_token FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        t = cur.fetchone()["kalender_token"]
    return {"link": _link(t) if t else None}


@vertrieb.post("/kalender-link/neu")
def link_neu(user: dict = Depends(require_vertrieb)):
    rate_limit("kalender-neu:" + str(user["id"]), 10, 3600)
    t = secrets.token_urlsafe(32)
    with tx("system") as cur:
        cur.execute("UPDATE vertriebspartner SET kalender_token=%s WHERE id=%s", (t, user["vertriebspartner_id"]))
    return {"link": _link(t)}


@public.get("/kalender/{token}.ics")
def abo(token: str, request: Request):
    rate_limit("kalender:" + client_ip(request), 120, 600)
    if not (20 <= len(token) <= 80):
        raise HTTPException(404, "Nicht gefunden.")
    with tx("system") as cur:
        cur.execute("SELECT id, name FROM vertriebspartner WHERE kalender_token=%s AND status='aktiv'", (token,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Nicht gefunden.")
        cur.execute("""SELECT id, firma, ansprechpartner, telefon, wiedervorlage_am FROM leads
                       WHERE vertriebspartner_id=%s AND wiedervorlage_am IS NOT NULL AND status NOT IN ('gewonnen','verloren','gesperrt','tot')
                       ORDER BY wiedervorlage_am LIMIT 400""", (p["id"],))
        wv = cur.fetchall()
        cur.execute("""SELECT g.id, g.start, g.ende, g.name, g.email, g.telefon, l.firma FROM gespraechstermine g JOIN leads l ON l.id = g.lead_id
                       WHERE l.vertriebspartner_id=%s AND g.status='gebucht' AND g.start > now() - interval '7 days' ORDER BY g.start LIMIT 200""", (p["id"],))
        gt = cur.fetchall()
    return Response(kalender_text(p["name"], wv, gt), media_type="text/calendar; charset=utf-8", headers={"Content-Disposition": 'inline; filename="wiedervorlagen.ics"'})
