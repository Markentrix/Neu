"""Mail-Verlauf im Portal sichtbar: beim Kunden und beim Lead (Admin) und beim eigenen Lead (Vertrieb)."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors

from . import stammdatencheck, verlauf
from .db import tx
from .security import require_admin, require_vertrieb

router = APIRouter(prefix="/api")


@router.get("/admin/kunden/{kid}/mails")
def kunde_mails(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(404, "Kunde nicht gefunden.")
        return verlauf.lesen(cur, kunden_id=kid)


@router.get("/admin/kunden/{kid}/stammdaten-check")
def kunde_stammdaten(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM kunden WHERE id=%s", (kid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Kunde nicht gefunden.")
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        cur.execute("SELECT count(*) AS n FROM mail_verlauf WHERE kunden_id=%s AND NOT ok AND zeit > now() - interval '30 days' AND lower(an) = lower(%s)", (kid, k["email"] or ""))
        return stammdatencheck.pruefen(k, cur.fetchone()["n"])


@router.get("/admin/leads/{lid}/mails")
def lead_mails(lid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT 1 FROM leads WHERE id=%s", (lid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Lead nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(404, "Lead nicht gefunden.")
        return verlauf.lesen(cur, lead_id=lid)


@router.get("/vertrieb/leads/{lid}/mails")
def vertrieb_lead_mails(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT 1 FROM leads WHERE id=%s AND vertriebspartner_id=%s", (lid, user["vertriebspartner_id"]))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Lead nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(404, "Lead nicht gefunden.")
        return verlauf.lesen(cur, lead_id=lid)
