"""Kundenportal: Beratungsgespräch mit Markentrix selbst buchen und alle Unterlagen von Markentrix an einem Ort (mit Suche)."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, push
from .db import tx
from .routes_buchung import TZ, _mails, _slots, lesen
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, rate_limit, require_inhaber

router = APIRouter(prefix="/api/kunde")


@router.get("/beratung")
def beratung(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        c = lesen(cur)
        cur.execute("SELECT id, start, ende, token FROM gespraechstermine WHERE kunden_id=%s AND status='gebucht' AND start > now() ORDER BY start", (kid,))
        meine = [{"id": r["id"], "start": r["start"], "ende": r["ende"], "absagen": f"{config.BASE_URL}/api/public/buchung/absagen?t={r['token']}"} for r in cur.fetchall()]
        tage: dict = {}
        if c["aktiv"] and not meine:
            for s in _slots(cur, c):
                tage.setdefault(s.astimezone(TZ).strftime("%Y-%m-%d"), []).append({"start": s.isoformat(), "uhr": s.astimezone(TZ).strftime("%H:%M")})
    return {"aktiv": bool(c["aktiv"]), "dauer": c["dauer"], "ort": c["ort"], "meine": meine, "tage": [{"datum": d, "slots": s} for d, s in tage.items()]}


class BeratungIn(BaseModel):
    start: str = Field(max_length=40)
    nachricht: str | None = Field(default=None, max_length=1500)


@router.post("/beratung")
def buchen(data: BeratungIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("kberatung:" + str(user["id"]), 10, 3600)
    try:
        start = datetime.fromisoformat(data.start).astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(400, "Ungültiger Termin.")
    nicht_frei = HTTPException(409, "Dieser Termin ist leider nicht mehr frei. Bitte wählen Sie einen anderen.")
    with tx("system") as cur:
        c = lesen(cur)
        if not c["aktiv"]:
            raise HTTPException(409, "Die Terminbuchung ist gerade nicht verfügbar. Bitte schreiben Sie uns eine Nachricht.")
        cur.execute("SELECT 1 FROM gespraechstermine WHERE kunden_id=%s AND status='gebucht' AND start > now()", (kid,))
        if cur.fetchone():
            raise HTTPException(409, "Sie haben schon ein Beratungsgespräch gebucht. Bitte sagen Sie es zuerst ab, wenn Sie einen anderen Termin möchten.")
        if start not in _slots(cur, c):
            raise nicht_frei
        cur.execute("SELECT firma, ansprechpartner, telefon FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        name = (k["ansprechpartner"] or k["firma"] or "Kunde").strip()
        try:
            cur.execute("""INSERT INTO gespraechstermine (start, ende, name, email, telefon, nachricht, kunden_id, token, gebucht_von)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'kundenportal') RETURNING id, start, ende, name, email, telefon, nachricht, token""",
                        (start, start + timedelta(minutes=c["dauer"]), name, user["email"], k["telefon"], (data.nachricht or "").strip() or f"Beratungsgespräch ({k['firma']})", kid, secrets.token_urlsafe(24)))
        except Exception:
            raise nicht_frei
        g = cur.fetchone()
        an = [x for x in [admin_empfaenger(cur)] if x]
        ids = push.admins(cur)
        ort = c["ort"]
        audit(cur, user, "beratung_gebucht", kid, {"start": start.isoformat()})
    push.senden(ids, "Beratungsgespräch gebucht", f"{k['firma']}: {start.astimezone(TZ).strftime('%d.%m. %H:%M')} Uhr", "/admin#kalender", "buchung")
    bg.add_task(_mails, g, ort, an)
    return {"ok": True, "wann": start.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")}


@router.get("/ablage")
def ablage(user: dict = Depends(require_inhaber)):
    """Alles, was Markentrix dem Kunden schickt oder von ihm hat: Rechnungen, Angebote, Datenschutz-Vertrag, Monatsberichte, AGB. Durchsucht wird im Browser."""
    kid = user["kunden_id"]
    out = []
    with tx("kunde", kid) as cur:
        cur.execute("SELECT id, art, nummer, betreff, datum, status, storno_von FROM belege WHERE status <> 'entwurf' ORDER BY datum DESC LIMIT 300")
        for r in cur.fetchall():
            art = "Storno" if r["storno_von"] else "Rechnung" if r["art"] == "rechnung" else "Angebot"
            out.append({"art": art, "titel": f"{art} {r['nummer'] or ''}".strip() + (f" · {r['betreff']}" if r["betreff"] else ""), "datum": r["datum"], "link": f"/api/kunde/belege/{r['id']}/pdf"})
        cur.execute("SELECT id, unterschrieben_am, datei_name FROM avv WHERE datei IS NOT NULL ORDER BY unterschrieben_am DESC")
        for r in cur.fetchall():
            out.append({"art": "Datenschutz-Vertrag", "titel": "Auftragsverarbeitungsvertrag (AVV)" + (f" · {r['datei_name']}" if r["datei_name"] else ""), "datum": r["unterschrieben_am"], "link": f"/api/kunde/avv/{r['id']}/datei"})
        cur.execute("SELECT id, titel, zeitraum_von FROM berichte WHERE art='monatsbericht' ORDER BY zeitraum_von DESC LIMIT 36")
        for r in cur.fetchall():
            out.append({"art": "Monatsbericht", "titel": r["titel"], "datum": r["zeitraum_von"], "link": f"/api/kunde/monatsberichte/{r['id']}/pdf"})
    with tx("system") as cur:
        cur.execute("""SELECT v.version, v.erstellt_am, (SELECT max(z.zeit) FROM agb_zustimmungen z WHERE z.agb_id = v.id AND z.kunden_id = %s) AS bestaetigt
                       FROM agb_versionen v WHERE v.aktiv LIMIT 1""", (kid,))
        a = cur.fetchone()
    if a:
        out.append({"art": "AGB", "titel": f"Allgemeine Geschäftsbedingungen ({a['version']})" + (" · von Ihnen bestätigt" if a["bestaetigt"] else ""), "datum": a["bestaetigt"] or a["erstellt_am"], "link": "/api/agb.pdf"})
    out.sort(key=lambda x: str(x["datum"] or ""), reverse=True)
    return out
