"""Doppelte Leads erkennen und zusammenführen: Verlauf, Angebote, Termine und Checks wandern zum Lead, den man behält; leere Felder werden ergänzt."""
import re

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors, sql
from pydantic import BaseModel

from . import leadschritt, sperre
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")

FELDER = ("ansprechpartner", "email", "telefon", "website", "branche", "plz", "ort", "gruppe", "notiz")


def _ziffern(t) -> str:
    return re.sub(r"\D", "", str(t or ""))


@router.get("/leads/{lid}/dubletten")
def dubletten(lid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT id, firma, email, telefon, plz, kunden_id FROM leads WHERE id=%s", (lid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Lead nicht gefunden.")
        l = cur.fetchone()
        if not l:
            raise HTTPException(404, "Lead nicht gefunden.")
        m, t, f = sperre.mail(l["email"]), sperre.telefon(l["telefon"]), (l["firma"] or "").strip().lower()
        cur.execute("""SELECT x.id, x.firma, x.ansprechpartner, x.email, x.telefon, x.ort, x.status, x.erstellt_am, x.kunden_id,
                              (SELECT count(*) FROM lead_aktivitaeten a WHERE a.lead_id = x.id) AS eintraege,
                              (%(m)s::text IS NOT NULL AND lower(x.email) = %(m)s) AS gleiche_mail,
                              (%(t)s::text IS NOT NULL AND regexp_replace(coalesce(x.telefon,''),'[^0-9]','','g') <> '' AND
                               CASE WHEN regexp_replace(x.telefon,'[^0-9]','','g') LIKE '00%%' THEN substr(regexp_replace(x.telefon,'[^0-9]','','g'),3)
                                    WHEN regexp_replace(x.telefon,'[^0-9]','','g') LIKE '0%%' THEN '49' || substr(regexp_replace(x.telefon,'[^0-9]','','g'),2)
                                    ELSE regexp_replace(x.telefon,'[^0-9]','','g') END = %(t)s) AS gleiche_nummer,
                              (%(f)s <> '' AND lower(x.firma) = %(f)s AND coalesce(x.plz,'') = coalesce(%(plz)s,'')) AS gleiche_firma
                       FROM leads x WHERE x.id <> %(id)s AND x.kunden_id IS NULL
                         AND ((%(m)s::text IS NOT NULL AND lower(x.email) = %(m)s)
                           OR (%(t)s::text IS NOT NULL AND regexp_replace(coalesce(x.telefon,''),'[^0-9]','','g') <> '' AND
                               CASE WHEN regexp_replace(x.telefon,'[^0-9]','','g') LIKE '00%%' THEN substr(regexp_replace(x.telefon,'[^0-9]','','g'),3)
                                    WHEN regexp_replace(x.telefon,'[^0-9]','','g') LIKE '0%%' THEN '49' || substr(regexp_replace(x.telefon,'[^0-9]','','g'),2)
                                    ELSE regexp_replace(x.telefon,'[^0-9]','','g') END = %(t)s)
                           OR (%(f)s <> '' AND lower(x.firma) = %(f)s AND coalesce(x.plz,'') = coalesce(%(plz)s,'')))
                       ORDER BY x.erstellt_am LIMIT 10""", {"m": m, "t": t, "f": f, "plz": l["plz"], "id": lid})
        return cur.fetchall()


class MergeIn(BaseModel):
    mit: str


@router.post("/leads/{lid}/zusammenfuehren")
def zusammenfuehren(lid: str, d: MergeIn, user: dict = Depends(require_admin)):
    """Der Lead in der Adresse bleibt, der Lead `mit` wird eingearbeitet und gelöscht."""
    if lid == d.mit:
        raise HTTPException(400, "Ein Lead lässt sich nicht mit sich selbst zusammenführen.")
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM leads WHERE id = ANY(%s::uuid[]) FOR UPDATE", ([lid, d.mit],))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Lead nicht gefunden.")
        zeilen = {str(r["id"]): r for r in cur.fetchall()}
        if lid not in zeilen or d.mit not in zeilen:
            raise HTTPException(404, "Lead nicht gefunden.")
        a, b = zeilen[lid], zeilen[d.mit]
        if a["kunden_id"] or b["kunden_id"]:
            raise HTTPException(409, "Ein Lead, der schon Kunde ist, lässt sich nicht zusammenführen.")
        if b["status"] in ("gesperrt",) and a["status"] not in ("gesperrt",):
            raise HTTPException(409, "Der zweite Lead steht auf der Sperrliste. Bitte den gesperrten Lead behalten.")
        # Alle Tabellen mit Verweis auf leads(id) umhängen (aus dem Datenbankkatalog; Tabellen mit Eins-zu-eins-Bezug bleiben beim gelöschten Lead und verschwinden mit ihm).
        cur.execute("""SELECT c.conrelid::regclass::text AS tabelle, a.attname AS spalte FROM pg_constraint c
                       JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
                       WHERE c.contype = 'f' AND c.confrelid = 'leads'::regclass AND array_length(c.conkey, 1) = 1""")
        umgehaengt = {}
        for r in cur.fetchall():
            tabelle, spalte = r["tabelle"].split(".")[-1].strip('"'), r["spalte"]
            try:
                with cur.connection.transaction():
                    cur.execute(sql.SQL("UPDATE {} SET {} = %s WHERE {} = %s").format(sql.Identifier(tabelle), sql.Identifier(spalte), sql.Identifier(spalte)), (lid, d.mit))
                    umgehaengt[tabelle] = cur.rowcount
            except (errors.UniqueViolation, errors.NotNullViolation):
                umgehaengt[tabelle] = 0
        # Leere Felder ergänzen
        neu = {k: b[k] for k in FELDER if not (a.get(k) or "").strip() and (b.get(k) or "").strip()}
        if neu:
            cur.execute(sql.SQL("UPDATE leads SET {} WHERE id = %s").format(sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(k)) for k in neu)), (*neu.values(), lid))
        if not a["vertriebspartner_id"] and b["vertriebspartner_id"]:
            cur.execute("UPDATE leads SET vertriebspartner_id=%s WHERE id=%s", (b["vertriebspartner_id"], lid))
        cur.execute("""UPDATE leads SET wiedervorlage_am = (SELECT min(w) FROM (VALUES (%s::date), (%s::date)) t(w) WHERE w IS NOT NULL),
                              letzter_kontakt_am = greatest(letzter_kontakt_am, %s) WHERE id = %s""", (a["wiedervorlage_am"], b["wiedervorlage_am"], b["letzter_kontakt_am"], lid))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)",
                    (lid, f"Zusammengeführt mit doppeltem Lead „{b['firma']}“ (Verlauf und Angebote übernommen).", user["email"]))
        cur.execute("DELETE FROM leads WHERE id = %s", (d.mit,))
        audit(cur, user, "lead_zusammengefuehrt", None, {"behalten": lid, "geloescht": d.mit, "firma": b["firma"], "umgehaengt": umgehaengt})
    return {"ok": True, "ergaenzt": sorted(neu), "umgehaengt": {k: v for k, v in umgehaengt.items() if v}}


@router.get("/leads/{lid}/naechster-schritt")
def naechster_schritt(lid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM leads WHERE id=%s", (lid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Lead nicht gefunden.")
        l = cur.fetchone()
        if not l:
            raise HTTPException(404, "Lead nicht gefunden.")
        return {"schritt": leadschritt.berechnen(cur, l)}
