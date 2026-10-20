"""Domainverwaltung pro Kunde: Inhaber, Registrar, Ablauf, Jahrespreis. Auth-Codes werden nicht gespeichert."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from .db import tx
from .publish import DOMAIN_RE
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")

SPALTEN = "id, kunden_id, domain, registrar, inhaber, inhaber_name, inhaber_kontakt, registriert_am, ablauf_am, auto_verlaengern, preis_jahr_cent, status, notiz"


class DomainIn(BaseModel):
    domain: str = Field(min_length=4, max_length=253)
    registrar: str = Field(default="INWX", max_length=60)
    inhaber: str = Field(default="markentrix", pattern="^(kunde|markentrix)$")
    inhaber_name: str = Field(default="", max_length=200)
    inhaber_kontakt: str = Field(default="", max_length=300)
    registriert_am: str = Field(default="", pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    ablauf_am: str = Field(default="", pattern=r"^(\d{4}-\d{2}-\d{2})?$")
    auto_verlaengern: bool = True
    preis_jahr_eur: float | None = Field(default=None, ge=0, le=10000)
    status: str = Field(default="aktiv", pattern="^(aktiv|transfer|gekuendigt)$")
    notiz: str = Field(default="", max_length=500)


def _werte(data: DomainIn) -> tuple:
    d = data.domain.strip().lower()
    if not DOMAIN_RE.match(d):
        raise HTTPException(400, "Die Domain ist ungültig (zum Beispiel firma.de).")
    reg = date.fromisoformat(data.registriert_am) if data.registriert_am else None
    abl = date.fromisoformat(data.ablauf_am) if data.ablauf_am else None
    if reg and abl and abl < reg:
        raise HTTPException(400, "Das Ablaufdatum liegt vor dem Registrierungsdatum.")
    preis = round(data.preis_jahr_eur * 100) if data.preis_jahr_eur is not None else None
    return (d, data.registrar.strip() or "INWX", data.inhaber, data.inhaber_name.strip() or None, data.inhaber_kontakt.strip() or None, reg, abl,
            data.auto_verlaengern, preis, data.status, data.notiz.strip() or None)


def liste_fuer(cur, kid) -> list:
    cur.execute(f"SELECT {SPALTEN} FROM domains WHERE kunden_id=%s ORDER BY domain", (kid,))
    return cur.fetchall()


@router.get("/kunden/{kid}/domains")
def liste(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise HTTPException(404, "Kunde nicht gefunden.")
            return liste_fuer(cur, kid)
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")


@router.post("/kunden/{kid}/domains")
def anlegen(kid: str, data: DomainIn, user: dict = Depends(require_admin)):
    w = _werte(data)
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise HTTPException(404, "Kunde nicht gefunden.")
            try:
                with cur.connection.transaction():
                    cur.execute("""INSERT INTO domains (kunden_id, domain, registrar, inhaber, inhaber_name, inhaber_kontakt, registriert_am, ablauf_am, auto_verlaengern, preis_jahr_cent, status, notiz)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""", (kid, *w))
                    did = cur.fetchone()["id"]
            except errors.UniqueViolation:
                raise HTTPException(400, "Diese Domain ist bei diesem Kunden schon eingetragen.")
            audit(cur, user, "domain_angelegt", kid, {"domain": w[0]})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    return {"id": did}


@router.put("/domains/{did}")
def aendern(did: str, data: DomainIn, user: dict = Depends(require_admin)):
    w = _werte(data)
    try:
        with tx("admin") as cur:
            try:
                with cur.connection.transaction():
                    cur.execute("""UPDATE domains SET domain=%s, registrar=%s, inhaber=%s, inhaber_name=%s, inhaber_kontakt=%s, registriert_am=%s, ablauf_am=%s,
                                          auto_verlaengern=%s, preis_jahr_cent=%s, status=%s, notiz=%s WHERE id=%s RETURNING kunden_id""", (*w, did))
                    r = cur.fetchone()
            except errors.UniqueViolation:
                raise HTTPException(400, "Diese Domain ist bei diesem Kunden schon eingetragen.")
            if not r:
                raise HTTPException(404, "Nicht gefunden.")
            audit(cur, user, "domain_geaendert", r["kunden_id"], {"domain": w[0]})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    return {"ok": True}


@router.delete("/domains/{did}")
def loeschen(did: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM domains WHERE id=%s RETURNING kunden_id, domain", (did,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Nicht gefunden.")
            audit(cur, user, "domain_geloescht", r["kunden_id"], {"domain": r["domain"]})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    return {"ok": True}


@router.get("/domains-ablauf")
def ablaufend(tage: int = 60, user: dict = Depends(require_admin)):
    """Aktive Domains, die in den nächsten Tagen ablaufen (oder schon abgelaufen sind)."""
    tage = max(1, min(tage, 365))
    with tx("admin") as cur:
        cur.execute("""SELECT d.id, d.domain, d.ablauf_am, d.inhaber, d.auto_verlaengern, k.id AS kunden_id, k.firma
                       FROM domains d JOIN kunden k ON k.id=d.kunden_id
                       WHERE d.status='aktiv' AND d.ablauf_am IS NOT NULL AND d.ablauf_am <= current_date + %s ORDER BY d.ablauf_am""", (tage,))
        return cur.fetchall()
