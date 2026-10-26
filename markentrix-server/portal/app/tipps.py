"""Hinweise auf passende weitere Pakete im Kundenportal („Ein Tipp für dich“). Ab Werk aus (Admin → Pakete → Hinweise im Kundenportal).
Die Hinweise beruhen auf Zahlen aus dem eigenen Portal des Kunden, nennen keine Preise und versprechen keine Ergebnisse. Der Kunde kann sie ablehnen (90 Tage Ruhe)
oder sich die Pakete ansehen; gebucht wird nur über den bekannten Ablauf mit Bestätigung durch Markentrix."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import einstellungen
from .db import tx
from .routes_pakete import LAUFEND
from .security import audit, require_admin, require_inhaber

kunde = APIRouter(prefix="/api/kunde")
admin = APIRouter(prefix="/api/admin/zusatzverkauf")
RUHE_TAGE = 90
MIN_KUNDE_TAGE = 30


def _einst(cur) -> dict:
    return {"aktiv": False, **(einstellungen.lesen(cur, "zusatzverkauf") or {})}


def kandidaten(cur, kid) -> list[dict]:
    """Passende Hinweise in der Reihenfolge ihrer Wichtigkeit, ohne bereits gebuchte Pakete."""
    cur.execute("SELECT paket_code, status, erstellt_am < now() - make_interval(days => %s) AS lange FROM kunden WHERE id=%s", (MIN_KUNDE_TAGE, kid))
    k = cur.fetchone()
    if not k or k["status"] != "aktiv" or not k["lange"]:
        return []
    cur.execute("SELECT produkt_code FROM buchungen WHERE kunden_id=%s AND status = ANY(%s)", (kid, list(LAUFEND)))
    habe = {r["produkt_code"] for r in cur.fetchall()} | ({k["paket_code"]} if k["paket_code"] else set())
    cur.execute("""SELECT count(*) FILTER (WHERE status='erledigt' AND beginn >= now() - interval '30 days') AS erledigt FROM termine WHERE kunden_id=%s""", (kid,))
    erledigt = cur.fetchone()["erledigt"]
    cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND quelle='telefon' AND erstellt_am >= now() - interval '30 days'", (kid,))
    telefon = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM kontakte WHERE kunden_id=%s", (kid,))
    kontakte = cur.fetchone()["n"]
    out = []
    if telefon >= 5 and k["paket_code"] == "KI_ONE" and not habe & {"KI_BUSINESS", "KI_KOMPLETT", "KI_ENTERPRISE"}:
        out.append({"code": "KI_BUSINESS", "titel": "Anrufe nicht verpassen",
                    "text": f"In den letzten 30 Tagen kamen {telefon} Anfragen per Telefon. Mit einem Paket mit Telefon-Assistent kann ein Teil davon automatisch angenommen und festgehalten werden."})
    if erledigt >= 5 and "BEWERTUNGSANFRAGEN" not in habe:
        out.append({"code": "BEWERTUNGSANFRAGEN", "titel": "Mehr Google-Bewertungen",
                    "text": f"Im letzten Monat wurden {erledigt} Termine erledigt. Automatische Bewertungsanfragen nach dem Termin machen es für zufriedene Kunden leicht, eine Bewertung zu schreiben."})
    if kontakte >= 50 and "NEWSLETTER" not in habe:
        out.append({"code": "NEWSLETTER", "titel": "In Kontakt bleiben",
                    "text": f"Du hast {kontakte} Kontakte gespeichert. Mit einem Newsletter erinnerst du Stammkunden regelmäßig an dich."})
    return out


@kunde.get("/tipp")
def tipp(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        if not _einst(cur)["aktiv"]:
            return {"tipp": None}
        cur.execute("SELECT code, status, geaendert_am > now() - make_interval(days => %s) AS frisch FROM kunden_tipps WHERE kunden_id=%s", (RUHE_TAGE, kid))
        bekannt = {r["code"]: r for r in cur.fetchall()}
        cur.execute("SELECT code, name FROM produkte WHERE einzeln_buchbar")
        namen = {r["code"]: r["name"] for r in cur.fetchall()}
        for c in kandidaten(cur, kid):
            b = bekannt.get(c["code"])
            if c["code"] not in namen or (b and (b["status"] == "interesse" or (b["status"] == "nein" and b["frisch"]))):
                continue
            cur.execute("""INSERT INTO kunden_tipps (kunden_id, code) VALUES (%s,%s) ON CONFLICT (kunden_id, code) DO UPDATE SET status = CASE WHEN kunden_tipps.status='nein' THEN 'gezeigt' ELSE kunden_tipps.status END""",
                        (kid, c["code"]))
            return {"tipp": {**c, "paket": namen[c["code"]]}}
    return {"tipp": None}


class ReaktionIn(BaseModel):
    art: str = Field(pattern="^(interesse|nein)$")


@kunde.post("/tipp/{code}/reaktion")
def reaktion(code: str, d: ReaktionIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        cur.execute("UPDATE kunden_tipps SET status=%s WHERE kunden_id=%s AND code=%s RETURNING code", ("interesse" if d.art == "interesse" else "nein", kid, code))
        if not cur.fetchone():
            raise HTTPException(404, "Hinweis nicht gefunden.")
    return {"ok": True}


class EinstIn(BaseModel):
    aktiv: bool = False


@admin.get("")
def stand(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        e = _einst(cur)
        cur.execute("""SELECT code, count(*)::int AS gezeigt, count(*) FILTER (WHERE status='interesse')::int AS interesse, count(*) FILTER (WHERE status='nein')::int AS nein
                       FROM kunden_tipps GROUP BY code ORDER BY code""")
        return {"aktiv": e["aktiv"], "zahlen": cur.fetchall()}


@admin.put("")
def einstellen(d: EinstIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "zusatzverkauf", {"aktiv": d.aktiv})
        audit(cur, user, "zusatzverkauf_einstellen", None, {"aktiv": d.aktiv})
    return {"ok": True}
