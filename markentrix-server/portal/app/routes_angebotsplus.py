"""Rund ums Angebot: Leistungstexte der Pakete pflegen, Angebot kopieren, Auswertung (Annahmequote, Pakete)."""
import json

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from .db import tx
from .routes_leadangebot import BLOCKIERT
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


# ---------------------------------------------------------------- Leistungstexte je Paket
@router.get("/katalog/leistungstexte")
def leistungstexte(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT code, kategorie, name, beschreibung, leistungen FROM produkte WHERE aktiv ORDER BY sortierung, name")
        return cur.fetchall()


class LeistungenIn(BaseModel):
    leistungen: list[str] = Field(default=[], max_length=40)


@router.put("/katalog/leistungstexte/{code}")
def leistungstext_setzen(code: str, data: LeistungenIn, user: dict = Depends(require_admin)):
    punkte = [x.strip()[:300] for x in data.leistungen if x.strip()]
    with tx("admin") as cur:
        cur.execute("UPDATE produkte SET leistungen=%s::jsonb WHERE code=%s", (json.dumps(punkte), code))
        if cur.rowcount == 0:
            raise HTTPException(404, "Paket nicht gefunden.")
        audit(cur, user, "leistungstext_geaendert", None, {"code": code})
    return {"ok": True, "anzahl": len(punkte)}


# ---------------------------------------------------------------- Angebot kopieren
class KopieIn(BaseModel):
    lead_id: str | None = None      # neuer Empfänger: Lead …
    kunden_id: str | None = None    # … oder Kunde; ohne Angabe bleibt der Empfänger gleich


@router.post("/belege/{bid}/kopie")
def kopieren(bid: str, data: KopieIn, user: dict = Depends(require_admin)):
    """Neuer Entwurf mit denselben Positionen und Texten. Der Firmenname im Text wird auf den neuen Empfänger umgestellt."""
    with tx("admin") as cur:
        try:
            cur.execute("""SELECT b.*, coalesce(k.firma, l.firma) AS firma FROM belege b LEFT JOIN kunden k ON k.id=b.kunden_id LEFT JOIN leads l ON l.id=b.lead_id
                           WHERE b.id=%s AND b.art='angebot'""", (bid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Angebot nicht gefunden.")
        b = cur.fetchone()
        if not b:
            raise HTTPException(404, "Angebot nicht gefunden.")
        lead_id, kunden_id, neu_firma = b["lead_id"], b["kunden_id"], b["firma"]
        if data.lead_id:
            cur.execute("SELECT id, firma, status, kunden_id FROM leads WHERE id=%s", (data.lead_id,))
            l = cur.fetchone()
            if not l:
                raise HTTPException(404, "Lead nicht gefunden.")
            if l["status"] in BLOCKIERT:
                raise HTTPException(400, "Für diesen Lead darf kein Angebot erstellt werden (gesperrt, ohne Einwilligung, verloren oder tot).")
            lead_id, kunden_id, neu_firma = l["id"], l["kunden_id"], l["firma"]
        elif data.kunden_id:
            cur.execute("SELECT id, firma FROM kunden WHERE id=%s", (data.kunden_id,))
            k = cur.fetchone()
            if not k:
                raise HTTPException(404, "Kunde nicht gefunden.")
            lead_id, kunden_id, neu_firma = None, k["id"], k["firma"]
        ersetzen = (lambda t: (t or "").replace(b["firma"], neu_firma)) if b["firma"] and neu_firma and b["firma"] != neu_firma else (lambda t: t or "")
        cur.execute("""INSERT INTO belege (art, kunden_id, lead_id, betreff, einleitung, schluss, positionen, leistungen, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer)
                       VALUES ('angebot', %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s) RETURNING id""",
                    (kunden_id, lead_id, ersetzen(b["betreff"]), ersetzen(b["einleitung"]), ersetzen(b["schluss"]), json.dumps(b["positionen"]), json.dumps(b["leistungen"]),
                     b["netto_cent"], b["ust_satz"], b["ust_cent"], b["brutto_cent"], b["kleinunternehmer"]))
        neu = cur.fetchone()["id"]
        audit(cur, user, "angebot_kopiert", kunden_id, {"von": str(bid), "neu": str(neu)})
    return {"id": neu, "lead_id": lead_id, "kunden_id": kunden_id}


# ---------------------------------------------------------------- Auswertung
@router.get("/belege-auswertung")
def auswertung(tage: int = 180, user: dict = Depends(require_admin)):
    tage = max(30, min(tage, 730))
    with tx("admin") as cur:
        cur.execute("""SELECT b.id, b.status, b.brutto_cent, b.positionen, b.datum, b.faellig_am, b.versendet_am, b.angesehen_am, b.angenommen_am, b.abgelehnt_am, b.grund_code
                       FROM belege b WHERE b.art='angebot' AND b.nummer IS NOT NULL AND b.datum > current_date - %s""", (tage,))
        rows = cur.fetchall()
        cur.execute("SELECT name FROM produkte WHERE aktiv ORDER BY length(name) DESC")
        namen = [r["name"] for r in cur.fetchall()]
    from datetime import date
    heute = date.today()
    gesamt = len(rows)
    angenommen = [r for r in rows if r["status"] == "angenommen"]
    abgelehnt = [r for r in rows if r["status"] == "abgelehnt"]
    angesehen = [r for r in rows if r["angesehen_am"] or r["status"] in ("angenommen", "abgelehnt")]
    abgelaufen = [r for r in rows if r["status"] in ("gestellt", "versendet") and r["faellig_am"] and r["faellig_am"] < heute]
    dauern = [(r["angenommen_am"].date() - r["datum"]).days for r in angenommen if r["angenommen_am"] and r["datum"]]
    pakete: dict = {}
    for r in rows:
        genannt = set()
        for p in r["positionen"] or []:
            for n in namen:
                if n.lower() in str(p.get("text", "")).lower():
                    genannt.add(n)
                    break
        for n in genannt:
            e = pakete.setdefault(n, {"name": n, "angebote": 0, "angenommen": 0})
            e["angebote"] += 1
            e["angenommen"] += r["status"] == "angenommen"
    from .angebotsgrund import GRUENDE
    gz: dict = {}
    for r in rows:
        if r["grund_code"] in GRUENDE and r["status"] != "angenommen":
            gz[r["grund_code"]] = gz.get(r["grund_code"], 0) + 1
    gruende = sorted(({"code": k, "name": GRUENDE[k], "anzahl": n} for k, n in gz.items()), key=lambda e: (-e["anzahl"], e["name"]))
    return {"tage": tage, "gruende": gruende, "gesendet": gesamt, "angesehen": len(angesehen), "angenommen": len(angenommen), "abgelehnt": len(abgelehnt), "abgelaufen": len(abgelaufen),
            "offen": gesamt - len(angenommen) - len(abgelehnt) - len(abgelaufen),
            "quote": round(100 * len(angenommen) / gesamt) if gesamt else None,
            "tage_bis_annahme": round(sum(dauern) / len(dauern), 1) if dauern else None,
            "summe_angenommen_cent": int(sum(r["brutto_cent"] for r in angenommen)),
            "pakete": sorted(pakete.values(), key=lambda e: (-e["angebote"], e["name"]))}
