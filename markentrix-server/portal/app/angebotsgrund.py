"""Grund festhalten, warum ein Angebot (noch) nicht angenommen wurde: Auswahl plus freier Text. Grundlage der Auswertung „Woran scheitern Angebote?“."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")
GRUENDE = {"zu_teuer": "Zu teuer (Preis oder Laufzeit)", "umfang": "Umfang passt nicht oder unklar", "zeitpunkt": "Zeitpunkt ungünstig", "konkurrenz": "Vergleicht / anderer Anbieter",
           "kein_bedarf": "Kein Bedarf mehr", "intern": "Interne Entscheidung dauert", "keine_antwort": "Keine Antwort", "sonstiges": "Sonstiges"}
# Gründe der Online-Ablehnung (Angebotsseite) auf die gemeinsame Liste abgebildet
ONLINE = {"zu_teuer": "zu_teuer", "spaeter": "zeitpunkt", "anderer_anbieter": "konkurrenz", "nicht_passend": "umfang", "sonstiges": "sonstiges"}


class GrundIn(BaseModel):
    code: str = Field(default="", max_length=30)
    text: str = Field(default="", max_length=500)


@router.get("/angebote-grund")
def liste(user: dict = Depends(require_admin)):
    return {"gruende": [{"code": k, "name": v} for k, v in GRUENDE.items()]}


@router.post("/angebote-grund/{bid}")
def setzen(bid: str, data: GrundIn, user: dict = Depends(require_admin)):
    code = data.code.strip()
    if code and code not in GRUENDE:
        raise HTTPException(400, "Unbekannter Grund.")
    with tx("admin") as cur:
        try:
            cur.execute("SELECT id, nummer, status, kunden_id, lead_id FROM belege WHERE id=%s AND art='angebot'", (bid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Angebot nicht gefunden.")
        b = cur.fetchone()
        if not b:
            raise HTTPException(404, "Angebot nicht gefunden.")
        if b["kunden_id"]:
            r = user.get("admin_rechte")
            if r is not None and "finanzen" not in r:
                raise HTTPException(403, "Dafür fehlt dir das Recht „Angebote, Rechnungen & Preise“.")
        if b["status"] not in ("gestellt", "versendet", "abgelehnt") or not b["nummer"]:
            raise HTTPException(400, "Einen Grund gibt es nur für ein gesendetes oder abgelehntes Angebot.")
        cur.execute("UPDATE belege SET grund_code=%s, grund_text=%s, grund_am=CASE WHEN %s::text IS NULL THEN NULL ELSE now() END, geaendert_am=now() WHERE id=%s",
                    (code or None, data.text.strip() or None, code or None, bid))
        if code and b["lead_id"]:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)",
                        (b["lead_id"], f"Angebot {b['nummer']}: Grund festgehalten: {GRUENDE[code]}" + (f" ({data.text.strip()})" if data.text.strip() else ""), user["email"]))
        audit(cur, user, "angebot_grund", b["kunden_id"], {"nummer": b["nummer"], "grund": code or None})
    return {"ok": True, "code": code or None}
