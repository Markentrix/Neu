"""Neuer Kunde aus einem Screenshot: Die KI liest die Stammdaten ab, das Bild wird nicht gespeichert. Das Büro prüft die Felder und legt den Kunden selbst an."""
import base64

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import einstellungen, ki
from .db import tx
from .security import rate_limit, require_admin

router = APIRouter(prefix="/api/admin")
MAGIE = {"image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG", "image/webp": b"RIFF"}


class BildIn(BaseModel):
    typ: str = Field(pattern="^image/(jpeg|png|webp)$")
    daten: str = Field(min_length=100, max_length=7_500_000)   # Base64, ca. 5 MB


@router.post("/kunden/aus-bild")
def kunde_aus_bild(d: BildIn, user: dict = Depends(require_admin)):
    rate_limit("kundenbild:" + str(user["id"]), 60, 86400)
    try:
        roh = base64.b64decode(d.daten, validate=True)
    except ValueError:
        raise HTTPException(400, "Das Bild konnte nicht gelesen werden.")
    if not roh.startswith(MAGIE[d.typ]):
        raise HTTPException(400, "Das ist kein gültiges Bild (JPEG, PNG oder WebP).")
    with tx("admin") as cur:
        cfg = einstellungen.lesen(cur, "ki")
    if not cfg.get("api_key"):
        raise HTTPException(400, "Das Lesen von Bildern ist noch nicht eingerichtet (Einstellungen → KI). Bitte den Kunden von Hand anlegen.")
    try:
        felder, ein, aus = ki.kunde_aus_bild(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, d.typ, d.daten)
    except Exception as e:
        raise ki.fehler(e, user, "Das Bild konnte gerade nicht gelesen werden. Bitte noch einmal versuchen oder von Hand eintragen.")
    with tx("admin") as cur:
        kosten = (ein * float(cfg.get("preis_ein_eur", 3.0)) + aus * float(cfg.get("preis_aus_eur", 15.0))) / 1_000_000 * 100
        cur.execute("INSERT INTO kosten_log (kunden_id, dienst, einheit, menge, kosten_cent) VALUES (NULL,'anthropic','tokens',%s,%s)", (ein + aus, round(kosten, 4)))
    hinweis = felder.pop("hinweis", "")
    if not any(felder.values()):
        raise HTTPException(422, "Auf dem Bild war nichts Lesbares zu erkennen. Bitte einen schärferen Ausschnitt nehmen oder von Hand eintragen.")
    return {"felder": felder, "hinweis": hinweis, "info": "Bitte alle Felder prüfen. Das Bild wurde nicht gespeichert."}
