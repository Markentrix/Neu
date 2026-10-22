"""Der Vertriebler bucht für seinen Lead direkt ein Erstgespräch (gleicher Terminpool wie die öffentliche Buchung)."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, push
from .db import tx
from .routes_buchung import EMAIL, TZ, _mails, _slots, lesen
from .routes_vertrieb import eigener_lead
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, require_vertrieb

router = APIRouter(prefix="/api/vertrieb")


@router.get("/buchungslink")
def buchungslink(user: dict = Depends(require_vertrieb)):
    return {"link": config.BASE_URL.rstrip("/") + "/buchen"}


@router.get("/leads/{lid}/slots")
def slots(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        eigener_lead(cur, lid, user["vertriebspartner_id"])
        c = lesen(cur)
        if not c["aktiv"]:
            return {"aktiv": False, "tage": []}
        tage: dict = {}
        for s in _slots(cur, c):
            lokal = s.astimezone(TZ)
            tage.setdefault(lokal.strftime("%Y-%m-%d"), []).append({"start": s.isoformat(), "uhr": lokal.strftime("%H:%M")})
    return {"aktiv": True, "dauer": c["dauer"], "ort": c["ort"], "tage": [{"datum": d, "slots": s} for d, s in tage.items()]}


class TerminIn(BaseModel):
    start: str = Field(max_length=40)
    zugestimmt: bool = False          # der Interessent hat dem Termin und der Bestätigungsmail im Gespräch zugestimmt


@router.post("/leads/{lid}/termin")
def termin_buchen(lid: str, data: TerminIn, bg: BackgroundTasks, user: dict = Depends(require_vertrieb)):
    if not data.zugestimmt:
        raise HTTPException(400, "Bitte bestätigen, dass der Interessent dem Termin zugestimmt hat.")
    try:
        start = datetime.fromisoformat(data.start)
        if start.tzinfo is None:
            raise ValueError
    except ValueError:
        raise HTTPException(400, "Ungültiger Termin.")
    start = start.astimezone(timezone.utc)
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if l["status"] in ("gewonnen", "gesperrt", "consent_ausstehend", "tot", "verloren"):
            raise HTTPException(400, "Für diesen Lead kann kein Termin gebucht werden.")
        email = (l["email"] or "").strip().lower()
        if not EMAIL.match(email):
            raise HTTPException(400, "Bitte zuerst die E-Mail-Adresse des Leads ergänzen (Bestätigung und Kalendereinladung gehen dorthin).")
        c = lesen(cur)
        if not c["aktiv"] or start not in _slots(cur, c):
            raise HTTPException(409, "Dieser Termin ist leider nicht mehr frei. Bitte einen anderen wählen.")
        ende = start + timedelta(minutes=c["dauer"])
        name = (l["ansprechpartner"] or l["firma"]).strip()
        try:
            cur.execute("""INSERT INTO gespraechstermine (start, ende, name, email, telefon, lead_id, token, gebucht_von) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                           RETURNING id, start, ende, name, email, telefon, nachricht, token""", (start, ende, name, email, l["telefon"], lid, secrets.token_urlsafe(24), user["email"]))
        except Exception:
            raise HTTPException(409, "Dieser Termin ist leider nicht mehr frei. Bitte einen anderen wählen.")
        g = cur.fetchone()
        lokal = start.astimezone(TZ)
        cur.execute("UPDATE leads SET status=CASE WHEN status IN ('neu','kontaktiert','antwort') THEN 'termin' ELSE status END, wiedervorlage_am=%s, letzter_kontakt_am=now() WHERE id=%s", (lokal.date(), lid))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von, ergebnis) VALUES (%s,'termin',%s,%s,'termin')",
                    (lid, "Gespräch gebucht für " + lokal.strftime("%d.%m.%Y %H:%M") + " Uhr (Interessent hat im Gespräch zugestimmt)", user["email"]))
        audit(cur, user, "lead_termin_vertrieb", None, {"lead": lid, "start": start.isoformat()})
        an = [x for x in [admin_empfaenger(cur)] if x]
        ids = push.admins(cur)
        ort = c["ort"]
    push.senden(ids, "Neues Gespräch gebucht", f"{user.get('name') or 'Ein Vertriebler'} hat ein Erstgespräch für {l['firma']} gebucht.", "/admin#leads", "buchung")
    bg.add_task(_mails, g, ort, an)
    return {"ok": True, "wann": lokal.strftime("%d.%m.%Y um %H:%M Uhr")}
