"""Pakete frei anlegen (Admin → Preise): eigene Katalog-Pakete mit Preis, Modulen und Leistungstexten.
Sie erscheinen wie die festen Pakete im Kundenportal und im Angebot. Preisänderungen laufen weiter über /api/admin/preise (versioniert)."""
import json
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import staffel
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin/pakete")

KATEGORIEN = ("kombi", "ki", "website", "ci", "sichtbarkeit", "personal_branding", "lead")
ABRECHNUNG = ("monatlich", "projekt", "projekt_pflege")
LAUFZEITEN = (1, 3, 6, 12, 24)      # Mindestlaufzeit in Monaten; leer = keine feste Laufzeit


def _code(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")[:40]
    return "EIGEN_" + (s or "PAKET")


class PaketIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    kategorie: str = "kombi"
    beschreibung: str = Field(default="", max_length=500)
    abrechnung: str = "monatlich"
    laufzeit_monate: int | None = Field(default=None, ge=0, le=60)
    einzeln_buchbar: bool = True
    nur_auf_anfrage: bool = False
    module: list[str] = Field(default=[], max_length=40)
    leistungen: list[str] = Field(default=[], max_length=40)
    einrichtung_cent: int | None = Field(default=None, ge=0)
    monatlich_cent: int | None = Field(default=None, ge=0)
    projekt_cent: int | None = Field(default=None, ge=0)
    ab_preis: bool = False
    gueltig_ab: date | None = None
    staffel: list[dict] | None = Field(default=None, max_length=12)


class PaketAendern(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    beschreibung: str | None = Field(default=None, max_length=500)
    laufzeit_monate: int | None = Field(default=None, ge=0, le=60)
    einzeln_buchbar: bool | None = None
    nur_auf_anfrage: bool | None = None
    aktiv: bool | None = None
    module: list[str] | None = Field(default=None, max_length=40)
    leistungen: list[str] | None = Field(default=None, max_length=40)


def _laufzeit(v):
    if v in (None, 0):
        return None
    if v not in LAUFZEITEN:
        raise HTTPException(400, "Die Laufzeit muss 1, 3, 6, 12 oder 24 Monate sein (oder leer).")
    return v


def _pruefen(data: PaketIn):
    data.laufzeit_monate = _laufzeit(data.laufzeit_monate)
    stufen = staffel.pruefen(data.staffel)
    if stufen:
        data.monatlich_cent = staffel.regelpreis(stufen)
    if data.kategorie not in KATEGORIEN:
        raise HTTPException(400, "Unbekannte Kategorie.")
    if data.abrechnung not in ABRECHNUNG:
        raise HTTPException(400, "Unbekannte Abrechnungsart.")
    if not data.nur_auf_anfrage and not any(x is not None for x in (data.einrichtung_cent, data.monatlich_cent, data.projekt_cent)):
        raise HTTPException(400, "Bitte mindestens einen Preis angeben oder „nur auf Anfrage“ wählen.")
    if data.abrechnung != "projekt" and not data.nur_auf_anfrage and data.monatlich_cent is None:
        raise HTTPException(400, "Bei monatlicher Abrechnung bitte den Monatspreis angeben.")


def _module_pruefen(cur, module: list[str]) -> list[str]:
    m = sorted({x.strip() for x in module if x.strip()})
    if m:
        cur.execute("SELECT code FROM module WHERE code = ANY(%s)", (m,))
        ok = {r["code"] for r in cur.fetchall()}
        if set(m) - ok:
            raise HTTPException(400, "Unbekanntes Modul: " + ", ".join(sorted(set(m) - ok)))
    return m


def _punkte(liste: list[str]) -> str:
    return json.dumps([x.strip()[:300] for x in liste if x.strip()])


@router.get("")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT p.code, p.kategorie, p.name, p.beschreibung, p.abrechnung, p.laufzeit_monate, p.einzeln_buchbar, p.nur_auf_anfrage, p.aktiv, p.eigen, p.leistungen,
                              pp.einrichtung_cent, pp.monatlich_cent, pp.projekt_cent, pp.ab_preis, pp.gueltig_ab, pp.staffel,
                              COALESCE((SELECT array_agg(modul_code ORDER BY modul_code) FROM produkt_module m WHERE m.produkt_code=p.code), '{}') AS module,
                              (SELECT count(*) FROM buchungen b WHERE b.produkt_code=p.code) AS buchungen,
                              (SELECT count(*) FROM kunden k WHERE k.paket_code=p.code) AS kunden
                       FROM produkte p
                       LEFT JOIN LATERAL (SELECT * FROM produkt_preise x WHERE x.produkt_code=p.code AND x.gueltig_ab<=current_date ORDER BY gueltig_ab DESC LIMIT 1) pp ON true
                       ORDER BY p.eigen DESC, p.sortierung, p.name""")
        pakete = cur.fetchall()
        cur.execute("SELECT code, name, beschreibung, art FROM module ORDER BY sortierung, name")
        module = cur.fetchall()
    return {"pakete": pakete, "module": module, "kategorien": list(KATEGORIEN)}


@router.post("")
def anlegen(data: PaketIn, user: dict = Depends(require_admin)):
    _pruefen(data)
    basis = _code(data.name)
    with tx("admin") as cur:
        m = _module_pruefen(cur, data.module)
        code, n = basis, 1
        while True:
            cur.execute("SELECT 1 FROM produkte WHERE code=%s", (code,))
            if not cur.fetchone():
                break
            n += 1
            code = f"{basis}_{n}"
        cur.execute("SELECT COALESCE(max(sortierung),0)+1 AS s FROM produkte WHERE kategorie=%s", (data.kategorie,))
        sort = int(cur.fetchone()["s"]) + 100
        cur.execute("""INSERT INTO produkte (code, kategorie, name, beschreibung, abrechnung, laufzeit_monate, nur_auf_anfrage, einzeln_buchbar, aktiv, sortierung, leistungen, eigen)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,true,%s,%s::jsonb,true)""",
                    (code, data.kategorie, data.name.strip(), data.beschreibung.strip(), data.abrechnung, data.laufzeit_monate, data.nur_auf_anfrage,
                     data.einzeln_buchbar, sort, _punkte(data.leistungen)))
        for mc in m:
            cur.execute("INSERT INTO produkt_module (produkt_code, modul_code) VALUES (%s,%s)", (code, mc))
        if not data.nur_auf_anfrage:
            cur.execute("""INSERT INTO produkt_preise (produkt_code, gueltig_ab, einrichtung_cent, monatlich_cent, projekt_cent, ab_preis, quelle, freigegeben_von, staffel)
                           VALUES (%s,%s,%s,%s,%s,%s,'admin-portal',%s,%s::jsonb)""",
                        (code, data.gueltig_ab or date.today(), data.einrichtung_cent, data.monatlich_cent, data.projekt_cent, data.ab_preis, user["email"],
                         json.dumps(staffel.pruefen(data.staffel)) if staffel.pruefen(data.staffel) else None))
        audit(cur, user, "paket_angelegt", None, {"code": code, "name": data.name})
    return {"ok": True, "code": code}


@router.put("/{code}")
def aendern(code: str, data: PaketAendern, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT eigen FROM produkte WHERE code=%s", (code,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Paket nicht gefunden.")
        if not p["eigen"] and (data.name is not None or data.beschreibung is not None or data.module is not None or data.laufzeit_monate is not None
                               or data.einzeln_buchbar is not None or data.nur_auf_anfrage is not None):
            raise HTTPException(400, "Feste Pakete lassen sich nur ausblenden, Leistungstexte und Preise ändern.")
        felder = {"name": data.name and data.name.strip(), "beschreibung": data.beschreibung and data.beschreibung.strip(),
                  "einzeln_buchbar": data.einzeln_buchbar, "nur_auf_anfrage": data.nur_auf_anfrage, "aktiv": data.aktiv}
        for k, v in felder.items():
            if v is not None or (k == "beschreibung" and data.beschreibung == ""):
                cur.execute(f"UPDATE produkte SET {k}=%s WHERE code=%s", (v, code))
        if data.laufzeit_monate is not None:
            cur.execute("UPDATE produkte SET laufzeit_monate=%s WHERE code=%s", (_laufzeit(data.laufzeit_monate), code))
        if data.leistungen is not None:
            cur.execute("UPDATE produkte SET leistungen=%s::jsonb WHERE code=%s", (_punkte(data.leistungen), code))
        if data.module is not None:
            m = _module_pruefen(cur, data.module)
            cur.execute("DELETE FROM produkt_module WHERE produkt_code=%s", (code,))
            for mc in m:
                cur.execute("INSERT INTO produkt_module (produkt_code, modul_code) VALUES (%s,%s)", (code, mc))
        audit(cur, user, "paket_geaendert", None, {"code": code})
    return {"ok": True}


@router.delete("/{code}")
def loeschen(code: str, user: dict = Depends(require_admin)):
    """Löscht nur eigene Pakete ohne Buchungen, Kunden und Belege. Sonst: ausblenden (aktiv=false)."""
    with tx("admin") as cur:
        cur.execute("SELECT eigen FROM produkte WHERE code=%s", (code,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Paket nicht gefunden.")
        if not p["eigen"]:
            raise HTTPException(400, "Feste Pakete lassen sich nicht löschen, nur ausblenden.")
        cur.execute("SELECT (SELECT count(*) FROM buchungen WHERE produkt_code=%s) + (SELECT count(*) FROM kunden WHERE paket_code=%s) AS n", (code, code))
        if cur.fetchone()["n"]:
            raise HTTPException(409, "Das Paket wurde schon gebucht. Blenden Sie es stattdessen aus.")
        try:
            cur.execute("DELETE FROM produkt_preise WHERE produkt_code=%s", (code,))
            cur.execute("DELETE FROM produkte WHERE code=%s", (code,))
        except errors.ForeignKeyViolation:
            raise HTTPException(409, "Das Paket wird noch verwendet. Blenden Sie es stattdessen aus.")
        audit(cur, user, "paket_geloescht", None, {"code": code})
    return {"ok": True}
