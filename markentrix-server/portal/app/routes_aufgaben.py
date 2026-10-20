"""Aufgaben und Kennzahlen für das Team, Kennzahlen für Kunden, Stammdaten ändern, Zusatzmodule anfragen."""
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import mailer
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger, nicht_gefunden, ticket_anlegen
from .security import audit, require_admin, require_inhaber, require_kunde

router = APIRouter(prefix="/api/admin")
kunde_router = APIRouter(prefix="/api/kunde")


# ================================================================= Aufgaben (Admin)
class AufgabeIn(BaseModel):
    titel: str = Field(min_length=1, max_length=200)
    beschreibung: str | None = Field(default=None, max_length=2000)
    zustaendig: str | None = Field(default=None, max_length=200)
    faellig_am: date | None = None
    kunden_id: str | None = None
    ticket_id: str | None = None


class AufgabeAendernIn(BaseModel):
    titel: str | None = Field(default=None, min_length=1, max_length=200)
    beschreibung: str | None = Field(default=None, max_length=2000)
    zustaendig: str | None = Field(default=None, max_length=200)
    faellig_am: date | None = None
    faellig_loeschen: bool = False
    status: str | None = Field(default=None, pattern="^(offen|erledigt)$")


@router.get("/aufgaben")
def aufgaben_liste(status: str = "offen", zustaendig: str = "", user: dict = Depends(require_admin)):
    if status not in ("offen", "erledigt", "alle"):
        raise HTTPException(400, "Status ungültig.")
    with tx("admin") as cur:
        cur.execute("""SELECT a.id, a.titel, a.beschreibung, a.zustaendig, a.faellig_am, a.status, a.quelle, a.ticket_id, a.erstellt_am, a.erledigt_am,
                              k.id AS kunden_id, k.kundennummer, k.firma,
                              (a.status = 'offen' AND a.faellig_am IS NOT NULL AND a.faellig_am < current_date) AS ueberfaellig
                       FROM aufgaben a LEFT JOIN kunden k ON k.id = a.kunden_id
                       WHERE (%s = 'alle' OR a.status = %s) AND (%s = '' OR a.zustaendig = %s)
                       ORDER BY (a.status = 'erledigt'), a.faellig_am NULLS LAST, a.erstellt_am DESC LIMIT 500""", (status, status, zustaendig, zustaendig))
        return cur.fetchall()


@router.post("/aufgaben")
def aufgabe_neu(data: AufgabeIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("INSERT INTO aufgaben (kunden_id, ticket_id, titel, beschreibung, zustaendig, faellig_am) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                        (data.kunden_id or None, data.ticket_id or None, data.titel.strip(), data.beschreibung, (data.zustaendig or user["email"]).strip(), data.faellig_am))
            aid = cur.fetchone()["id"]
            audit(cur, user, "aufgabe_erstellt", data.kunden_id or None, {"titel": data.titel})
    except (errors.InvalidTextRepresentation, errors.ForeignKeyViolation):
        raise HTTPException(400, "Kunde oder Nachricht nicht gefunden.")
    return {"id": aid}


@router.patch("/aufgaben/{aid}")
def aufgabe_aendern(aid: str, data: AufgabeAendernIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("""UPDATE aufgaben SET titel=coalesce(%s,titel), beschreibung=coalesce(%s,beschreibung), zustaendig=coalesce(%s,zustaendig),
                           faellig_am=CASE WHEN %s::boolean THEN NULL ELSE coalesce(%s,faellig_am) END, status=coalesce(%s,status),
                           erledigt_am=CASE WHEN %s='erledigt' THEN now() WHEN %s='offen' THEN NULL ELSE erledigt_am END,
                           erledigt_von=CASE WHEN %s='erledigt' THEN %s WHEN %s='offen' THEN NULL ELSE erledigt_von END
                           WHERE id=%s RETURNING id""",
                        (data.titel, data.beschreibung, data.zustaendig, data.faellig_loeschen, data.faellig_am, data.status,
                         data.status, data.status, data.status, user["email"], data.status, aid))
            if not cur.fetchone():
                raise nicht_gefunden()
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


@router.delete("/aufgaben/{aid}")
def aufgabe_loeschen(aid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM aufgaben WHERE id=%s AND quelle='manuell' RETURNING id", (aid,))
            if not cur.fetchone():
                raise HTTPException(404, "Nicht gefunden. Automatische Aufgaben kannst du nur als erledigt markieren.")
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


# ================================================================= Kennzahlen (Admin)
def kennzahlen_laden(cur) -> dict:
    cur.execute("""SELECT
        (SELECT count(*) FROM tickets WHERE status <> 'erledigt') AS tickets_offen,
        (SELECT count(*) FROM tickets WHERE status <> 'erledigt' AND team_ungelesen) AS tickets_ungelesen,
        (SELECT count(*) FROM tickets WHERE status <> 'erledigt' AND faellig_am < current_date) AS tickets_ueberfaellig,
        (SELECT count(*) FROM kundenfreigaben WHERE status = 'wartet') AS freigaben_wartend,
        (SELECT count(*) FROM aufgaben WHERE status = 'offen') AS aufgaben_offen,
        (SELECT count(*) FROM aufgaben WHERE status = 'offen' AND faellig_am < current_date) AS aufgaben_ueberfaellig,
        (SELECT round((avg(extract(epoch FROM erste_antwort_am - erstellt_am)) / 3600)::numeric, 1) FROM tickets WHERE erstellt_am > now() - interval '90 days' AND erste_antwort_am IS NOT NULL) AS antwortzeit_h,
        (SELECT round((avg(extract(epoch FROM erledigt_am - erstellt_am)) / 3600)::numeric, 1) FROM tickets WHERE erstellt_am > now() - interval '90 days' AND erledigt_am IS NOT NULL) AS erledigungszeit_h,
        (SELECT round((avg(extract(epoch FROM entschieden_am - angefragt_am)) / 3600)::numeric, 1) FROM kundenfreigaben WHERE angefragt_am > now() - interval '90 days' AND entschieden_am IS NOT NULL AND status IN ('freigegeben','abgelehnt')) AS freigabedauer_h
    """)
    z = cur.fetchone()
    cur.execute("""SELECT count(*) AS n, round(avg(punkte)::numeric, 1) AS durchschnitt,
                          count(*) FILTER (WHERE punkte >= 9) AS promoter, count(*) FILTER (WHERE punkte <= 6) AS kritiker
                   FROM zufriedenheit WHERE erstellt_am > now() - interval '90 days'""")
    s = cur.fetchone()
    z["bewertungen"] = s["n"]
    z["bewertung_durchschnitt"] = s["durchschnitt"]
    z["nps"] = round((s["promoter"] - s["kritiker"]) * 100 / s["n"]) if s["n"] else None
    return z


@router.get("/kennzahlen")
def kennzahlen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        z = kennzahlen_laden(cur)
        cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.status,
                              (SELECT count(*) FROM tickets t WHERE t.kunden_id = k.id AND t.status <> 'erledigt') AS tickets_offen,
                              (SELECT count(*) FROM kundenfreigaben f WHERE f.kunden_id = k.id AND f.status = 'wartet') AS freigaben_wartend,
                              (SELECT max(t.geaendert_am) FROM tickets t WHERE t.kunden_id = k.id) AS letzte_aktivitaet,
                              (SELECT round(avg(zf.punkte)::numeric, 1) FROM zufriedenheit zf WHERE zf.kunden_id = k.id AND zf.erstellt_am > now() - interval '180 days') AS bewertung
                       FROM kunden k WHERE k.status IN ('onboarding','aktiv','pausiert') ORDER BY tickets_offen DESC, k.firma LIMIT 300""")
        z["kunden"] = cur.fetchall()
        cur.execute("""SELECT z.punkte, z.kommentar, z.art, z.erstellt_am, k.kundennummer, k.firma FROM zufriedenheit z JOIN kunden k ON k.id = z.kunden_id
                       WHERE z.kommentar IS NOT NULL ORDER BY z.erstellt_am DESC LIMIT 20""")
        z["kommentare"] = cur.fetchall()
    return z


# ================================================================= Kennzahlen, Stammdaten, Module (Kunde)
@kunde_router.get("/kennzahlen")
def k_kennzahlen(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        cur.execute("""SELECT
            (SELECT count(*) FROM tickets WHERE status <> 'erledigt') AS nachrichten_offen,
            (SELECT count(*) FROM tickets WHERE status = 'wartet_auf_kunde' OR kunde_ungelesen) AS wartet_auf_dich,
            (SELECT count(*) FROM kundenfreigaben WHERE status = 'wartet') AS freigaben_wartend,
            (SELECT count(*) FROM anfragen WHERE erstellt_am > now() - interval '30 days' AND status <> 'spam') AS anfragen_30d,
            (SELECT round((avg(extract(epoch FROM erste_antwort_am - erstellt_am)) / 3600)::numeric, 1) FROM tickets WHERE erstellt_am > now() - interval '90 days' AND erste_antwort_am IS NOT NULL) AS antwortzeit_h,
            (SELECT count(*) FROM zufriedenheit WHERE art = 'quartal' AND erstellt_am > now() - interval '90 days') AS quartal_bewertet,
            (SELECT k.erstellt_am < now() - interval '30 days' FROM kunden k WHERE k.id = %s) AS lange_kunde""", (kid,))
        z = cur.fetchone()
    lange, quartal = z.pop("lange_kunde"), z.pop("quartal_bewertet")
    z["bewertung_faellig"] = bool(lange) and quartal == 0
    return z


class StammdatenIn(BaseModel):
    strasse: str | None = Field(default=None, max_length=200)
    plz: str | None = Field(default=None, max_length=12)
    ort: str | None = Field(default=None, max_length=120)


@kunde_router.patch("/stammdaten")
def k_stammdaten(data: StammdatenIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    """Rechnungsanschrift ändern. Läuft im Systemkontext (Tabelle kunden ist für Kunden schreibgeschützt), nur für den eigenen Datensatz; das Team wird informiert."""
    neu = {k: (v or "").strip() for k, v in data.model_dump().items() if v is not None}
    if not neu:
        raise HTTPException(400, "Nichts zu ändern.")
    with tx("system") as cur:
        cur.execute("SELECT firma, kundennummer, strasse, plz, ort FROM kunden WHERE id=%s", (user["kunden_id"],))
        alt = cur.fetchone()
        cur.execute("UPDATE kunden SET strasse=coalesce(%s,strasse), plz=coalesce(%s,plz), ort=coalesce(%s,ort), geaendert_am=now() WHERE id=%s",
                    (neu.get("strasse"), neu.get("plz"), neu.get("ort"), user["kunden_id"]))
        audit(cur, user, "stammdaten_geaendert", user["kunden_id"], {"alt": {k: alt[k] for k in neu}, "neu": neu})
        an = admin_empfaenger(cur)
    text = "\n".join(f"{k}: {alt[k] or '–'} -> {v or '–'}" for k, v in neu.items())
    if an:
        bg.add_task(mailer.stammdaten_geaendert_team, an, alt["firma"], alt["kundennummer"], text)
    return {"ok": True}


class ModulAnfrageIn(BaseModel):
    modul_code: str = Field(min_length=1, max_length=80)
    text: str | None = Field(default=None, max_length=2000)


@kunde_router.post("/modul-anfrage")
def k_modul(data: ModulAnfrageIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        cur.execute("SELECT name FROM module WHERE code=%s", (data.modul_code,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(404, "Dieses Modul gibt es nicht.")
        cur.execute("SELECT 1 FROM kunden_module WHERE kunden_id=%s AND modul_code=%s AND aktiv", (kid, data.modul_code))
        if cur.fetchone():
            raise HTTPException(400, "Dieses Modul ist bei dir schon aktiv.")
        cur.execute("SELECT id FROM tickets WHERE modul_code=%s AND status <> 'erledigt' LIMIT 1", (data.modul_code,))
        if cur.fetchone():
            raise HTTPException(400, "Zu diesem Modul gibt es schon eine offene Anfrage. Wir melden uns bei dir.")
        text = (data.text or "").strip() or f"Ich interessiere mich für das Modul \"{m['name']}\". Bitte meldet euch bei mir mit Details und Preis."
        t = ticket_anlegen(cur, kid, user, f"Zusatzmodul anfragen: {m['name']}", "modul", text, modul=data.modul_code)
        cur.execute("SELECT firma, kundennummer FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        audit(cur, user, "modul_angefragt", kid, {"modul": data.modul_code})
    with tx("system") as cur:
        an = admin_empfaenger(cur)
    if an:
        bg.add_task(mailer.ticket_neu_team, an, t["nr"], k["firma"], k["kundennummer"], f"Zusatzmodul anfragen: {m['name']}", "Zusatzmodul-Anfrage", text)
    return {"id": t["id"], "nr": t["nr"]}


# ================================================================= Heute zu tun (Admin-Übersicht)
@router.get("/heute")
def heute(user: dict = Depends(require_admin)):
    from .routes_avv import fehlende, veraltete
    with tx("admin") as cur:
        cur.execute("""SELECT t.id, t.nummer, t.betreff, k.firma, k.id AS kunden_id FROM tickets t JOIN kunden k ON k.id = t.kunden_id
                       WHERE t.status <> 'erledigt' AND t.team_ungelesen ORDER BY t.geaendert_am LIMIT 6""")
        nachrichten = cur.fetchall()
        cur.execute("""SELECT a.id, a.titel, a.faellig_am, a.kunden_id FROM aufgaben a WHERE a.status = 'offen' AND a.faellig_am <= current_date
                       ORDER BY a.faellig_am, a.erstellt_am LIMIT 8""")
        aufgaben = cur.fetchall()
        cur.execute("""SELECT id, firma, temperatur, quelle, erstellt_am FROM leads WHERE status = 'neu'
                       ORDER BY (temperatur = 'heiss') DESC NULLS LAST, erstellt_am DESC LIMIT 6""")
        leads = cur.fetchall()
        cur.execute("""SELECT l.id, l.firma, l.wiedervorlage_am, v.name AS vertriebler FROM leads l LEFT JOIN vertriebspartner v ON v.id = l.vertriebspartner_id
                       WHERE l.wiedervorlage_am <= current_date AND l.status NOT IN ('verloren','gewonnen','gesperrt','tot') ORDER BY l.wiedervorlage_am LIMIT 8""")
        wiedervorlagen = cur.fetchall()
        cur.execute("SELECT count(*) AS n FROM leads WHERE status = 'neu'")
        leads_n = cur.fetchone()["n"]
        cur.execute("""SELECT f.id, f.titel, k.firma, k.id AS kunden_id FROM kundenfreigaben f JOIN kunden k ON k.id = f.kunden_id
                       WHERE f.status = 'wartet' AND f.angefragt_am < now() - interval '3 days' ORDER BY f.angefragt_am LIMIT 6""")
        freigaben = cur.fetchall()
        cur.execute("""SELECT k.id, k.firma FROM kunden k WHERE k.status = 'onboarding' AND k.erstellt_am < now() - interval '5 days'
                       AND EXISTS (SELECT 1 FROM onboarding_punkte p WHERE p.kunden_id = k.id AND NOT p.erledigt) ORDER BY k.erstellt_am LIMIT 6""")
        onboarding = cur.fetchall()
        cur.execute("""SELECT b.id, b.nummer, k.firma, k.id AS kunden_id FROM belege b JOIN kunden k ON k.id = b.kunden_id
                       WHERE b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date AND b.nummer IS NOT NULL ORDER BY b.faellig_am LIMIT 6""")
        rechnungen = cur.fetchall()
        avv_fehlt = [{"id": r["id"], "firma": r["firma"]} for r in fehlende(cur)][:6]
        avv_veraltet = [{"id": r["id"], "firma": r["firma"]} for r in veraltete(cur)][:6]
        # Angebote im Blick: offene (gesendet, evtl. angesehen) und kürzlich beantwortete, für Leads und Kunden
        cur.execute("""SELECT b.id, b.nummer, b.status, b.brutto_cent, b.lead_id, b.kunden_id, b.datum, b.faellig_am, b.versendet_am, b.angesehen_am, b.angenommen_am, b.abgelehnt_am,
                              coalesce(k.firma, l.firma) AS firma, (l.kunden_id IS NOT NULL) AS lead_ist_kunde
                       FROM belege b LEFT JOIN kunden k ON k.id = b.kunden_id LEFT JOIN leads l ON l.id = b.lead_id
                       WHERE b.art = 'angebot' AND b.nummer IS NOT NULL
                         AND (b.status IN ('gestellt','versendet') OR (b.status IN ('angenommen','abgelehnt') AND coalesce(b.angenommen_am, b.abgelehnt_am, b.geaendert_am) > now() - interval '30 days'))
                       ORDER BY coalesce(b.angesehen_am, b.versendet_am, b.erstellt_am) DESC LIMIT 30""")
        angebote = cur.fetchall()
    gesamt = len(nachrichten) + len(aufgaben) + len(wiedervorlagen) + leads_n + len(freigaben) + len(onboarding) + len(rechnungen) + len(avv_fehlt)
    return {"nachrichten": nachrichten, "aufgaben": aufgaben, "leads": leads, "wiedervorlagen": wiedervorlagen, "leads_gesamt": leads_n, "freigaben": freigaben,
            "onboarding": onboarding, "rechnungen": rechnungen, "avv_fehlt": avv_fehlt, "avv_veraltet": avv_veraltet, "angebote": angebote, "gesamt": gesamt}
