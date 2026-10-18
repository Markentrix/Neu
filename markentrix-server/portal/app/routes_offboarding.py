"""Vertragsende: Datenexport und Löschung (nur Admin)."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel

from . import offboarding, routes_websites
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


@router.get("/kunden/{kid}/export.zip")
def export(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT kundennummer FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if not k:
                raise HTTPException(404, "Kunde nicht gefunden.")
            daten = offboarding.export_zip(cur, kid)
            audit(cur, user, "kunde_export", kid)
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    return Response(daten, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="Datenexport-{k["kundennummer"]}.zip"'})


class LoeschIn(BaseModel):
    bestaetigung: str
    export_uebergeben: bool = False


@router.post("/kunden/{kid}/loeschen")
def loeschen(kid: str, data: LoeschIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT kundennummer, status, geloescht_am FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if not k:
                raise HTTPException(404, "Kunde nicht gefunden.")
            if k["geloescht_am"]:
                raise HTTPException(400, "Die Daten dieses Kunden wurden bereits gelöscht.")
            if k["status"] not in ("gekuendigt", "beendet"):
                raise HTTPException(400, "Gelöscht werden kann erst, wenn der Status des Kunden „gekuendigt“ oder „beendet“ ist.")
            if data.bestaetigung.strip() != k["kundennummer"]:
                raise HTTPException(400, "Zur Bestätigung muss die Kundennummer genau eingetippt werden.")
            if not data.export_uebergeben:
                raise HTTPException(400, "Bitte bestätigen, dass der Datenexport an den Kunden übergeben wurde.")
            ergebnis = offboarding.loeschen(cur, kid, user["email"])
            audit(cur, user, "kunde_inhalte_geloescht", kid, {"zaehler": {t: n for t, n in ergebnis["zaehler"].items() if n}})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    offboarding.dateien_entfernen(kid)
    for s in ergebnis["websites"]:
        if s["art"] == "live" and s["domain"]:
            try:
                routes_websites.auftrag({"aktion": "loeschen", "art": "live", "name": s["domain"]})
            except HTTPException:
                pass  # Ordner kann auch später über „Websites & Demos“ entfernt werden
    return {"ok": True, "geloescht": {t: n for t, n in ergebnis["zaehler"].items() if n},
            "hinweis": "Website-Ordner landen 14 Tage im Papierkorb. Sicherungen enthalten die Daten bis zu 14 Tage (lokal) bzw. entsprechend lange extern."}
