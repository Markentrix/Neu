"""Folgemails an Leads: Einstellungen und Abmeldelink. Der Versand läuft im Hintergrunddienst (jobs.py)."""
import secrets
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import einstellungen
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin

router = APIRouter(prefix="/api")

STANDARD = {
    "aktiv": False, "kunden_feedback": False, "tage_1": 2, "tage_2": 7,
    "betreff_1": "Ihre Anfrage bei Markentrix",
    "text_1": ("Guten Tag {name},\n\nvor ein paar Tagen haben Sie sich bei uns gemeldet ({firma}). Haben Sie noch Fragen, oder können wir Ihnen bei den nächsten Schritten helfen?\n\n"
               "Wenn Sie möchten, vereinbaren wir ein kurzes Gespräch, Sie wählen den Termin selbst: {buchen}\n\nSie können natürlich auch einfach auf diese Mail antworten."),
    "betreff_2": "Kurze Nachfrage zu Ihrer Anfrage",
    "text_2": ("Guten Tag {name},\n\nwir möchten uns noch einmal kurz melden. Falls das Thema für Sie noch aktuell ist, buchen Sie gern einen Termin: {buchen}\n\n"
               "Falls nicht, ist das völlig in Ordnung, dann hören Sie von uns nichts weiter."),
}


class FolgeIn(BaseModel):
    aktiv: bool = False
    kunden_feedback: bool = False
    tage_1: int = Field(default=2, ge=1, le=30)
    tage_2: int = Field(default=7, ge=2, le=60)
    betreff_1: str = Field(default=STANDARD["betreff_1"], min_length=3, max_length=200)
    text_1: str = Field(default=STANDARD["text_1"], min_length=10, max_length=3000)
    betreff_2: str = Field(default=STANDARD["betreff_2"], min_length=3, max_length=200)
    text_2: str = Field(default=STANDARD["text_2"], min_length=10, max_length=3000)


def lesen(cur) -> dict:
    return {**STANDARD, **(einstellungen.lesen(cur, "folgemails") or {})}


@router.get("/admin/einstellungen/folgemails")
def einst_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return {**lesen(cur), "standard": STANDARD}


@router.put("/admin/einstellungen/folgemails")
def einst_speichern(data: FolgeIn, user: dict = Depends(require_admin)):
    if data.tage_2 <= data.tage_1:
        raise HTTPException(400, "Die zweite Mail muss später kommen als die erste.")
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "folgemails", data.model_dump())
        audit(cur, user, "einstellungen_folgemails", None, {"aktiv": data.aktiv})
    return {"ok": True}


def token_fuer(cur, lid) -> str:
    cur.execute("SELECT abmelde_token FROM leads WHERE id=%s", (lid,))
    t = cur.fetchone()["abmelde_token"]
    if not t:
        t = secrets.token_urlsafe(24)
        cur.execute("UPDATE leads SET abmelde_token=%s WHERE id=%s", (t, lid))
    return t


def _seite(text: str) -> HTMLResponse:
    return HTMLResponse(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Markentrix</title>'
                        f'<body style="font:16px system-ui;max-width:520px;margin:12vh auto;padding:0 20px;color:#0B1020"><h2>Markentrix</h2><p>{escape(text)}</p></body>')


@router.get("/public/abmelden")
def abmelden(t: str, request: Request):
    """Abmeldung von weiteren Nachrichten per Link aus der Mail."""
    rate_limit("abmelden:" + client_ip(request), 20, 600)
    if len(t) < 10 or len(t) > 100:
        return _seite("Dieser Link ist ungültig.")
    with tx("system") as cur:
        cur.execute("UPDATE leads SET abgemeldet=true, wiedervorlage_am=NULL WHERE abmelde_token=%s RETURNING id", (t,))
        r = cur.fetchone()
        if r:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz','Hat sich von weiteren Nachrichten abgemeldet','website')", (r["id"],))
    return _seite("Sie erhalten von uns keine weiteren Nachrichten zu Ihrer Anfrage." if r else "Dieser Link ist ungültig.")
