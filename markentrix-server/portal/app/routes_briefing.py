"""Briefing-Fragebogen (Kunde füllt aus), Auswertung für Kunden, extern gepflegte Monatszahlen (Admin)."""
import json
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import berichte, mailer
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger, nicht_gefunden
from .security import audit, require_admin, require_kunde

kunde_router = APIRouter(prefix="/api/kunde")
router = APIRouter(prefix="/api/admin")

# (Abschnitt, [(Schlüssel, Frage, Art, Pflicht)])   Art: text | lang | wahl:a|b|c
BRIEFING = [
    ("Über dein Unternehmen", [
        ("beschreibung", "Was macht dein Unternehmen? Beschreibe es in 2 bis 3 Sätzen.", "lang", True),
        ("zielgruppe", "Wer sind deine Kunden?", "lang", False),
        ("besonderheit", "Was macht dich besonders, warum kommen Kunden zu dir?", "lang", False),
    ]),
    ("Öffnungszeiten und Kontakt", [
        ("oeffnungszeiten", "Öffnungszeiten (so, wie sie auf der Website stehen sollen)", "lang", True),
        ("telefon_oeffentlich", "Telefonnummer für die Website", "text", False),
        ("adresse_oeffentlich", "Adresse für die Website (falls abweichend von der Rechnungsanschrift)", "text", False),
    ]),
    ("Auftritt", [
        ("sprachen", "In welchen Sprachen soll deine Website erscheinen?", "text", False),
        ("farben", "Farben, Logo und Schrift: Was gibt es schon, was wünschst du dir?", "lang", False),
        ("vorbilder", "Websites, die dir gefallen (Links)", "lang", False),
        ("ton", "Wie sollen deine Texte klingen?", "wahl:förmlich|freundlich|locker", False),
    ]),
    ("Inhalte", [
        ("leistungen", "Deine wichtigsten Leistungen oder Produkte", "lang", True),
        ("aktionen", "Hast du regelmäßig Angebote oder Aktionen (z. B. Wochenangebote)?", "wahl:ja|nein|manchmal", False),
        ("social", "Links zu deinen Social-Media-Seiten", "lang", False),
        ("google_profil", "Link zu deinem Google-Unternehmensprofil (falls vorhanden)", "text", False),
    ]),
    ("Ziele", [
        ("ziele", "Was soll die Zusammenarbeit mit Markentrix für dich bringen?", "lang", False),
        ("wuensche", "Sonstige Wünsche oder Hinweise", "lang", False),
    ]),
]
ALLE = {k: p for _, felder in BRIEFING for k, _, _, p in felder}


def _struktur():
    return [{"abschnitt": a, "felder": [{"key": k, "frage": f, "art": art, "pflicht": p} for k, f, art, p in fs]} for a, fs in BRIEFING]


def _lesen(cur):
    cur.execute("SELECT daten, status, abgeschickt_am, geaendert_am FROM briefings")
    b = cur.fetchone()
    return b or {"daten": {}, "status": "offen", "abgeschickt_am": None, "geaendert_am": None}


class BriefingIn(BaseModel):
    daten: dict[str, str]
    abschicken: bool = False


@kunde_router.get("/briefing")
def briefing_lesen(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        return {"struktur": _struktur(), **_lesen(cur)}


@kunde_router.put("/briefing")
def briefing_speichern(data: BriefingIn, bg: BackgroundTasks, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    daten = {}
    for k, v in data.daten.items():
        if k not in ALLE:
            raise HTTPException(400, "Unbekanntes Feld.")
        v = (v or "").strip()
        if len(v) > 3000:
            raise HTTPException(400, "Ein Text ist zu lang (höchstens 3000 Zeichen).")
        if v:
            daten[k] = v
    if data.abschicken:
        fehlt = [f for k, f, _, p in [x for _, fs in BRIEFING for x in fs] if p and not daten.get(k)]
        if fehlt:
            raise HTTPException(400, "Bitte fülle noch aus: " + "; ".join(f.split(" (")[0].rstrip("?.") for f in fehlt))
    with tx("kunde", kid) as cur:
        cur.execute("""INSERT INTO briefings (kunden_id, daten, status, abgeschickt_am, geaendert_von) VALUES (%s,%s::jsonb,%s,%s,%s)
                       ON CONFLICT (kunden_id) DO UPDATE SET daten=EXCLUDED.daten,
                         status=CASE WHEN %s THEN 'abgeschickt' ELSE briefings.status END,
                         abgeschickt_am=CASE WHEN %s THEN now() ELSE briefings.abgeschickt_am END,
                         geaendert_von=EXCLUDED.geaendert_von, geaendert_am=now()""",
                    (kid, json.dumps(daten, ensure_ascii=False), "abgeschickt" if data.abschicken else "offen", None, user["id"], data.abschicken, data.abschicken))
        if data.abschicken:
            cur.execute("UPDATE briefings SET abgeschickt_am=now() WHERE kunden_id=%s", (kid,))
            cur.execute("SELECT firma, kundennummer FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
        audit(cur, user, "briefing_abgeschickt" if data.abschicken else "briefing_gespeichert", kid, {})
    if data.abschicken:
        with tx("system") as cur:
            an = admin_empfaenger(cur)
            cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                           VALUES (%s, %s, %s, current_date + 2, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                        (kid, f"Briefing prüfen: {k['firma']}", an, f"briefing-{kid}-{date.today().isoformat()}"))
        if an:
            bg.add_task(mailer.briefing_team, an, k["firma"], k["kundennummer"], str(kid))
    return {"ok": True, "status": "abgeschickt" if data.abschicken else "gespeichert"}


@router.get("/kunden/{kid}/briefing")
def briefing_admin(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT daten, status, abgeschickt_am, geaendert_am FROM briefings WHERE kunden_id=%s", (kid,))
            b = cur.fetchone() or {"daten": {}, "status": "offen", "abgeschickt_am": None, "geaendert_am": None}
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"struktur": _struktur(), **b}


# ================================================================= Auswertung
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


@kunde_router.get("/auswertung")
def auswertung(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    heute = date.today()
    von, bis = berichte.monat_grenzen(heute)
    vor = berichte.vormonat(heute)
    vvon, vbis = berichte.monat_grenzen(vor)
    with tx("kunde", kid) as cur:
        dieser = berichte.sammeln(cur, kid, von, bis)
        letzter = berichte.sammeln(cur, kid, vvon, vbis)
        cur.execute("""SELECT w::date AS ab FROM generate_series(date_trunc('week', now()) - interval '11 weeks', date_trunc('week', now()), interval '1 week') w ORDER BY w""")
        starts = [r["ab"] for r in cur.fetchall()]
        cur.execute("""SELECT date_trunc('week', erstellt_am)::date AS ab, count(*) AS n FROM anfragen WHERE kunden_id=%s AND status <> 'spam' AND erstellt_am >= date_trunc('week', now()) - interval '11 weeks' GROUP BY 1""", (kid,))
        a_w = {r["ab"]: r["n"] for r in cur.fetchall()}
        wochen = [{"ab": st, "anfragen": a_w.get(st, 0)} for st in starts]
        cur.execute("""SELECT to_char(m, 'YYYY-MM') AS monat FROM generate_series(date_trunc('month', now()) - interval '5 months', date_trunc('month', now()), interval '1 month') m ORDER BY m""")
        mon = [r["monat"] for r in cur.fetchall()]
        cur.execute("""SELECT to_char(date_trunc('month', erstellt_am), 'YYYY-MM') AS monat, count(*) AS n FROM anfragen WHERE kunden_id=%s AND status <> 'spam' AND erstellt_am >= date_trunc('month', now()) - interval '5 months' GROUP BY 1""", (kid,))
        a_m = {r["monat"]: r["n"] for r in cur.fetchall()}
        cur.execute("""SELECT to_char(date_trunc('month', beginn), 'YYYY-MM') AS monat, count(*) AS n FROM termine WHERE kunden_id=%s AND status NOT IN ('abgesagt') AND beginn >= date_trunc('month', now()) - interval '5 months' AND beginn < date_trunc('month', now()) + interval '1 month' GROUP BY 1""", (kid,))
        t_m = {r["monat"]: r["n"] for r in cur.fetchall()}
        monate = [{"monat": m, "anfragen": a_m.get(m, 0), "termine": t_m.get(m, 0)} for m in mon]
        cur.execute("SELECT to_char(monat, 'YYYY-MM') AS monat, besucher, google_aufrufe, google_bewertungen, google_sterne FROM kennzahlen_extern ORDER BY monat DESC LIMIT 12")
        extern = list(reversed(cur.fetchall()))
    return {"monat_name": f"{MONATE[heute.month - 1]} {heute.year}", "vormonat_name": f"{MONATE[vor.month - 1]} {vor.year}",
            "dieser": dieser, "letzter": letzter, "wochen": wochen, "monate": monate, "extern": extern}


class ExternIn(BaseModel):
    monat: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    besucher: int | None = Field(default=None, ge=0, le=100_000_000)
    google_aufrufe: int | None = Field(default=None, ge=0, le=100_000_000)
    google_bewertungen: int | None = Field(default=None, ge=0, le=1_000_000)
    google_sterne: float | None = Field(default=None, ge=1, le=5)


@router.get("/kunden/{kid}/kennzahlen-extern")
def extern_liste(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT to_char(monat, 'YYYY-MM') AS monat, besucher, google_aufrufe, google_bewertungen, google_sterne FROM kennzahlen_extern WHERE kunden_id=%s ORDER BY monat DESC LIMIT 24", (kid,))
            return cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


@router.put("/kunden/{kid}/kennzahlen-extern")
def extern_setzen(kid: str, data: ExternIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("""INSERT INTO kennzahlen_extern (kunden_id, monat, besucher, google_aufrufe, google_bewertungen, google_sterne) VALUES (%s,%s::date,%s,%s,%s,%s)
                           ON CONFLICT (kunden_id, monat) DO UPDATE SET besucher=EXCLUDED.besucher, google_aufrufe=EXCLUDED.google_aufrufe,
                             google_bewertungen=EXCLUDED.google_bewertungen, google_sterne=EXCLUDED.google_sterne""",
                        (kid, data.monat + "-01", data.besucher, data.google_aufrufe, data.google_bewertungen, data.google_sterne))
            audit(cur, user, "kennzahlen_extern", kid, {"monat": data.monat})
    except (errors.InvalidTextRepresentation, errors.ForeignKeyViolation):
        raise nicht_gefunden()
    return {"ok": True}
