"""Vertriebs-Arbeitsliste, KI-Gesprächsleitfaden und Vertriebs-Auswertung."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg import errors

from . import einstellungen, heissleads, ki, leadkontakt
from .db import tx
from .security import audit, rate_limit, require_admin, require_vertrieb

router = APIRouter(prefix="/api")
OFFEN = "('verloren','gewonnen','gesperrt','tot','consent_ausstehend')"


@router.get("/vertrieb/heute")
def vertrieb_heute(user: dict = Depends(require_vertrieb)):
    """Arbeitsliste für heute: fällige Wiedervorlagen, HOT-Leads ohne Kontakt, neu zugewiesene Leads."""
    pid = user["vertriebspartner_id"]
    felder = "l.id, l.firma, l.ansprechpartner, l.telefon, l.ort, l.gruppe, l.branche, l.temperatur, l.status, l.wiedervorlage_am, l.rueckruf_am, l.letzter_kontakt_am"
    with tx("system") as cur:
        cur.execute(f"""SELECT {felder} FROM leads l WHERE l.vertriebspartner_id=%s AND l.wiedervorlage_am <= current_date AND l.status NOT IN {OFFEN}
                        ORDER BY l.wiedervorlage_am, l.rueckruf_am NULLS LAST LIMIT 30""", (pid,))
        wiedervorlagen = cur.fetchall()
        cur.execute(f"""SELECT {felder} FROM leads l WHERE l.vertriebspartner_id=%s AND l.status='neu' AND l.temperatur='heiss' AND l.letzter_kontakt_am IS NULL
                        AND (l.wiedervorlage_am IS NULL OR l.wiedervorlage_am > current_date) ORDER BY l.erstellt_am DESC LIMIT 30""", (pid,))
        heiss = cur.fetchall()
        cur.execute(f"""SELECT {felder} FROM leads l WHERE l.vertriebspartner_id=%s AND l.status='neu' AND l.letzter_kontakt_am IS NULL AND coalesce(l.temperatur,'') <> 'heiss'
                        AND (l.wiedervorlage_am IS NULL OR l.wiedervorlage_am > current_date)
                        ORDER BY (l.temperatur='warm') DESC NULLS LAST, l.geaendert_am DESC LIMIT 15""", (pid,))
        neu = cur.fetchall()
        # Leads mit frischem Signal (Angebot angesehen, Antwort, Terminbuchung) gehören nach oben, auch wenn sie schon einmal kontaktiert wurden
        bekannt = {str(z["id"]) for z in wiedervorlagen + heiss}
        cur.execute(f"""SELECT {felder} FROM leads l WHERE l.vertriebspartner_id=%s AND l.status NOT IN {OFFEN} AND (
                          EXISTS (SELECT 1 FROM belege b WHERE b.lead_id=l.id AND b.art='angebot' AND b.status IN ('gestellt','versendet') AND b.angesehen_am > now() - interval '7 days')
                          OR EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id=l.id AND a.art='antwort' AND a.zeit > now() - interval '7 days'))
                        ORDER BY l.geaendert_am DESC LIMIT 15""", (pid,))
        extra = [z for z in cur.fetchall() if str(z["id"]) not in bekannt]
        heiss += extra
        neu[:] = [z for z in neu if str(z["id"]) not in {str(e["id"]) for e in extra}]
        heissleads.anreichern(cur, wiedervorlagen, heiss, neu)
        cur.execute("""SELECT count(*) AS n FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id
                       WHERE l.vertriebspartner_id=%s AND a.art='anruf' AND a.zeit::date = current_date""", (pid,))
        heute_anrufe = cur.fetchone()["n"]
        cur.execute("""SELECT g.start, g.name, g.telefon, g.lead_id FROM gespraechstermine g JOIN leads l ON l.id=g.lead_id
                       WHERE l.vertriebspartner_id=%s AND g.status='gebucht' AND g.start >= now() AND g.start < now() + interval '3 days' ORDER BY g.start LIMIT 10""", (pid,))
        termine = cur.fetchall()
    return {"wiedervorlagen": wiedervorlagen, "heiss": heiss, "neu": neu, "anrufe_heute": heute_anrufe, "termine": termine, "kontakt_optionen": leadkontakt.optionen_fuer_oberflaeche(),
            "gesamt": len(wiedervorlagen) + len(heiss) + len(neu)}


def _skript(cur, lid: str, pid: str | None):
    cfg = einstellungen.lesen(cur, "ki") or {}
    try:
        if pid:
            cur.execute("SELECT * FROM leads WHERE id=%s AND vertriebspartner_id=%s", (lid, pid))
        else:
            cur.execute("SELECT * FROM leads WHERE id=%s", (lid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    l = cur.fetchone()
    if not l:
        raise HTTPException(404, "Lead nicht gefunden.")
    return l, cfg


def _skript_erzeugen(lid: str, pid: str | None, user: dict):
    rate_limit("skript:" + str(user["id"]), 30, 3600)
    with tx("system") as cur:
        l, cfg = _skript(cur, lid, pid)
        # Kontext für das Skript: bisheriger Verlauf und Ergebnis des Website-Checks
        cur.execute("SELECT inhalt FROM lead_aktivitaeten WHERE lead_id=%s AND art IN ('notiz','anruf','antwort','termin') ORDER BY zeit DESC LIMIT 8", (lid,))
        l["verlauf"] = " | ".join((r["inhalt"] or "")[:160] for r in cur.fetchall())
        cur.execute("SELECT score, ergebnis FROM lead_checks WHERE lead_id=%s ORDER BY erstellt_am DESC LIMIT 1", (lid,))
        c = cur.fetchone()
        if c:
            l["website_check"] = f"Score {c['score']}/100. " + json.dumps(c["ergebnis"], ensure_ascii=False)[:600]
    if not cfg.get("api_key"):
        raise HTTPException(400, "Für den Gesprächsleitfaden fehlt der KI-Schlüssel (Einstellungen → KI). Bitte beim Team melden.")
    try:
        s = ki.skript_entwurf(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, l)
    except Exception as e:
        raise ki.fehler(e, user, "Der KI-Dienst hat nicht geantwortet. Bitte später erneut versuchen.")
    import json
    with tx("system") as cur:
        cur.execute("UPDATE leads SET skript=%s::jsonb, skript_am=now() WHERE id=%s", (json.dumps(s, ensure_ascii=False), lid))
        audit(cur, user, "lead_skript", None, {"id": lid})
    return s


class NotizIn(BaseModel):
    text: str = Field(min_length=5, max_length=4000)


@router.post("/vertrieb/notiz-zusammenfassen")
def notiz_zusammenfassen(data: NotizIn, user: dict = Depends(require_vertrieb)):
    """Fasst eine diktierte oder getippte Gesprächsnotiz zusammen. Es geht nur der Text an die KI, keine Daten des Leads."""
    rate_limit("notiz-ki:" + str(user["id"]), 60, 3600)
    with tx("system") as cur:
        cfg = einstellungen.lesen(cur, "ki") or {}
    if not cfg.get("api_key"):
        raise HTTPException(400, "Die Zusammenfassung ist noch nicht eingerichtet (KI-Schlüssel fehlt). Bitte beim Team melden. Die Notiz kannst du trotzdem speichern.")
    try:
        text = ki.notiz_zusammenfassen(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, data.text)
    except Exception as e:
        raise ki.fehler(e, user, "Der KI-Dienst hat nicht geantwortet. Die Notiz kannst du trotzdem speichern.")
    if not text:
        raise HTTPException(502, "Es kam keine Zusammenfassung zurück. Bitte noch einmal versuchen.")
    return {"zusammenfassung": text}


@router.post("/vertrieb/leads/{lid}/skript")
def skript_vertrieb(lid: str, user: dict = Depends(require_vertrieb)):
    return _skript_erzeugen(lid, user["vertriebspartner_id"], user)


@router.post("/admin/leads/{lid}/skript")
def skript_admin(lid: str, user: dict = Depends(require_admin)):
    return _skript_erzeugen(lid, None, user)


def _trichter(cur, gruppierung: str, join: str = "") -> list:
    cur.execute(f"""SELECT {gruppierung} AS name,
                  count(*) AS leads,
                  count(*) FILTER (WHERE l.letzter_kontakt_am IS NOT NULL) AS bearbeitet,
                  count(*) FILTER (WHERE l.status IN ('antwort','termin','angebot','gewonnen')) AS erreicht,
                  count(*) FILTER (WHERE l.status IN ('termin','angebot','gewonnen')) AS termine,
                  count(*) FILTER (WHERE l.status = 'gewonnen') AS kunden,
                  count(*) FILTER (WHERE l.status IN ('verloren','tot')) AS verloren
                  FROM leads l {join} GROUP BY 1 ORDER BY count(*) DESC LIMIT 60""")
    return cur.fetchall()


@router.get("/admin/vertrieb/auswertung")
def auswertung(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        gesamt = _trichter(cur, "'Alle Leads'")
        je_vertriebler = _trichter(cur, "coalesce(v.name, 'Nicht zugeordnet')", "LEFT JOIN vertriebspartner v ON v.id=l.vertriebspartner_id")
        je_liste = _trichter(cur, "coalesce(l.liste, 'Ohne Liste')")
        je_gruppe = _trichter(cur, "coalesce(l.gruppe, l.branche, 'Ohne Branche')")
        je_quelle = _trichter(cur, "l.quelle")
        cur.execute("""SELECT coalesce(v.name,'Nicht zugeordnet') AS name,
                              count(*) FILTER (WHERE a.zeit >= now() - interval '7 days') AS anrufe_7t,
                              count(*) FILTER (WHERE a.zeit::date = current_date) AS anrufe_heute
                       FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id LEFT JOIN vertriebspartner v ON v.id=l.vertriebspartner_id
                       WHERE a.art='anruf' AND a.zeit >= now() - interval '7 days' GROUP BY 1""")
        anrufe = {r["name"]: r for r in cur.fetchall()}
        cur.execute("SELECT count(*) AS n FROM gespraechstermine WHERE status='gebucht' AND start >= now()")
        gebucht = cur.fetchone()["n"]
        cur.execute("SELECT verlust_grund AS grund, count(*) AS n FROM leads WHERE status='verloren' AND verlust_grund IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
        verlustgruende = cur.fetchall()
        cur.execute("""SELECT count(*) FILTER (WHERE ansprache_grundlage IS NULL AND status IN ('neu','kontaktiert','antwort','termin','angebot') AND quelle <> 'website') AS ohne_grundlage FROM leads""")
        ohne_grundlage = cur.fetchone()["ohne_grundlage"]
    for r in je_vertriebler:
        a = anrufe.get(r["name"]) or {}
        r["anrufe_7t"] = a.get("anrufe_7t", 0)
        r["anrufe_heute"] = a.get("anrufe_heute", 0)
    return {"gesamt": gesamt[0] if gesamt else None, "je_vertriebler": je_vertriebler, "je_liste": je_liste, "je_gruppe": je_gruppe, "je_quelle": je_quelle, "gebuchte_gespraeche": gebucht, "verlustgruende": verlustgruende, "ohne_grundlage": ohne_grundlage}
