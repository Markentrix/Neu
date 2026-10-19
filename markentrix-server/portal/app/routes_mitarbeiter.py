"""Mitarbeiter im Admin-Bereich mit abgestuften Rechten, und die Änderungshistorie pro Kunde."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import zugang
from .db import tx
from .security import RECHTE, audit, require_admin, require_voll

router = APIRouter(prefix="/api")


class MitarbeiterIn(BaseModel):
    email: str = Field(max_length=200)
    name: str | None = Field(default=None, max_length=120)
    rechte: list[str] = Field(default=[], max_length=10)


class MitarbeiterPatch(BaseModel):
    rechte: list[str] | None = Field(default=None, max_length=10)
    aktiv: bool | None = None


def _pruefen(rechte: list[str]):
    if any(r not in RECHTE for r in rechte):
        raise HTTPException(400, "Unbekannter Bereich.")


@router.get("/admin/mitarbeiter")
def liste(user: dict = Depends(require_voll)):
    with tx("admin") as cur:
        cur.execute("SELECT id, email, name, aktiv, admin_rechte, (passwort_hash IS NOT NULL) AS hat_passwort FROM benutzer WHERE rolle='admin' ORDER BY erstellt_am")
        return {"bereiche": RECHTE, "liste": cur.fetchall()}


@router.post("/admin/mitarbeiter")
def anlegen(data: MitarbeiterIn, bg: BackgroundTasks, user: dict = Depends(require_voll)):
    _pruefen(data.rechte)
    with tx("admin") as cur:
        link = zugang.link_erzeugen(cur, data.email, data.name, "admin")
        cur.execute("UPDATE benutzer SET admin_rechte=%s WHERE lower(email)=%s", (data.rechte, data.email.strip().lower()))
        audit(cur, user, "mitarbeiter_angelegt", None, {"email": data.email.strip().lower(), "rechte": data.rechte})
    bg.add_task(zugang.per_mail, data.email, data.name, link, "admin")
    return {"ok": True, "link": link}


@router.patch("/admin/mitarbeiter/{bid}")
def aendern(bid: str, data: MitarbeiterPatch, user: dict = Depends(require_voll)):
    if bid == str(user["id"]):
        raise HTTPException(400, "Das eigene Konto kann hier nicht geändert werden.")
    with tx("admin") as cur:
        cur.execute("SELECT id, admin_rechte FROM benutzer WHERE id=%s AND rolle='admin'", (bid,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(404, "Nicht gefunden.")
        if data.rechte is not None:
            _pruefen(data.rechte)
            cur.execute("UPDATE benutzer SET admin_rechte=%s WHERE id=%s", (data.rechte, bid))
        if data.aktiv is not None:
            cur.execute("UPDATE benutzer SET aktiv=%s WHERE id=%s", (data.aktiv, bid))
            if not data.aktiv:
                cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s", (bid,))
        audit(cur, user, "mitarbeiter_geaendert", None, {"id": bid, "rechte": data.rechte, "aktiv": data.aktiv})
    return {"ok": True}


@router.get("/admin/kunden/{kid}/historie")
def historie(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT a.zeit, a.aktion, a.details, b.name, b.email FROM audit_log a LEFT JOIN benutzer b ON b.id=a.benutzer_id
                       WHERE a.kunden_id=%s ORDER BY a.id DESC LIMIT 150""", (kid,))
        return cur.fetchall()
