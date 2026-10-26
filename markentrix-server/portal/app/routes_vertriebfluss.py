"""Schneller arbeiten im Vertrieb: Lead-Suche mit Filtern, Anruf-Modus (nächster heißer Lead) und Lead aus einem Foto."""
import base64
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import einstellungen, ki
from .db import tx
from .security import rate_limit, require_admin, require_vertrieb

router = APIRouter(prefix="/api/vertrieb")
admin = APIRouter(prefix="/api/admin")
OFFEN = "('verloren','gewonnen','gesperrt','tot','consent_ausstehend')"
SEITE = 50
STATUS = ("neu", "kontaktiert", "antwort", "termin", "angebot", "gewonnen", "verloren", "tot")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


@router.get("/leadsuche")
def leadsuche(q: str = "", status: str = "", faellig: int = 0, temperatur: str = "", seite: int = 1, user: dict = Depends(require_vertrieb)):
    """Eigene Leads mit Suche, Status, „nur fällige Wiedervorlagen“ und Einstufung, in Seiten zu je 50."""
    if status and status not in STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    if temperatur not in ("", "heiss", "warm", "kalt"):
        raise HTTPException(400, "Unbekannte Einstufung.")
    pid = user["vertriebspartner_id"]
    wo, par = ["l.vertriebspartner_id = %s"], [pid]
    q = q.strip()[:80]
    if q:
        wo.append("(l.firma ILIKE %s OR l.ort ILIKE %s OR l.ansprechpartner ILIKE %s OR l.telefon ILIKE %s OR l.email ILIKE %s OR l.branche ILIKE %s)")
        par += [_like(q)] * 6
    if status:
        wo.append("l.status = %s")
        par.append(status)
    if temperatur:
        wo.append("l.temperatur = %s")
        par.append(temperatur)
    if faellig:
        wo.append(f"l.wiedervorlage_am <= current_date AND l.status NOT IN {OFFEN}")
    seite = max(1, min(seite, 1000))
    with tx("system") as cur:
        cur.execute("SELECT count(*)::int AS n FROM leads l WHERE " + " AND ".join(wo), par)
        gesamt = cur.fetchone()["n"]
        cur.execute("""SELECT l.id, l.firma, l.ansprechpartner, l.telefon, l.ort, l.branche, l.status, l.wiedervorlage_am, l.letzter_kontakt_am, l.temperatur, l.erstellt_am
                       FROM leads l WHERE """ + " AND ".join(wo) + """ ORDER BY (l.wiedervorlage_am <= current_date AND l.status NOT IN """ + OFFEN + """) DESC NULLS LAST,
                       l.erstellt_am DESC LIMIT %s OFFSET %s""", [*par, SEITE, (seite - 1) * SEITE])
        leads = cur.fetchall()
        cur.execute("SELECT status, count(*)::int AS n FROM leads WHERE vertriebspartner_id=%s GROUP BY status", (pid,))
        zaehler = {r["status"]: r["n"] for r in cur.fetchall()}
        cur.execute(f"SELECT count(*)::int AS n FROM leads WHERE vertriebspartner_id=%s AND wiedervorlage_am <= current_date AND status NOT IN {OFFEN}", (pid,))
        faellig_n = cur.fetchone()["n"]
    return {"leads": leads, "gesamt": gesamt, "seite": seite, "seiten": max(1, -(-gesamt // SEITE)), "zaehler": zaehler, "faellig": faellig_n}


def _naechster_lead(modus: str, ausser: str, wo: str, par: list) -> dict:
    """Wählt den nächsten Lead für den Anruf-Modus. `wo` ist die Einschränkung auf Vertriebler (SQL mit %s), `par` ihre Werte."""
    if modus not in ("heiss", "zufall"):
        raise HTTPException(400, "Unbekannter Modus.")
    ids = [x for x in ausser.split(",") if UUID.match(x)][:300]
    ordnung = "random()" if modus == "zufall" else "(l.wiedervorlage_am <= current_date) DESC NULLS LAST, (l.letzter_kontakt_am IS NULL) DESC, l.letzter_kontakt_am, l.erstellt_am"
    basis = f"FROM leads l WHERE {wo} AND l.status NOT IN {OFFEN} AND l.id <> ALL(%s::uuid[]) AND (l.wiedervorlage_am IS NULL OR l.wiedervorlage_am <= current_date)"
    with tx("system") as cur:
        for quelle, extra, order in (("heiss", " AND l.temperatur='heiss'", ordnung),
                                     ("wiedervorlage", " AND coalesce(l.temperatur,'') <> 'heiss' AND l.wiedervorlage_am <= current_date", "l.wiedervorlage_am"),
                                     ("neu", " AND coalesce(l.temperatur,'') <> 'heiss' AND l.status='neu' AND l.letzter_kontakt_am IS NULL", "(l.temperatur='warm') DESC NULLS LAST, l.erstellt_am DESC")):
            cur.execute(f"SELECT l.id, l.firma, (SELECT count(*)::int {basis}{extra}) AS uebrig {basis}{extra} ORDER BY {order} LIMIT 1", [*par, ids, *par, ids])
            z = cur.fetchone()
            if z:
                return {"id": str(z["id"]), "firma": z["firma"], "quelle": quelle, "uebrig": z["uebrig"]}
    return {"id": None, "firma": None, "quelle": None, "uebrig": 0}


@router.get("/naechster")
def naechster(modus: str = "heiss", ausser: str = "", user: dict = Depends(require_vertrieb)):
    """Anruf-Modus: der nächste Lead. Zuerst heiße Leads (fällige Wiedervorlage, dann ohne Kontakt, dann am längsten nicht angerufen) oder zufällig aus den heißen;
    gibt es keinen heißen mehr, folgen fällige Wiedervorlagen und neue Leads. Bereits abgearbeitete Leads (`ausser`) kommen nicht noch einmal."""
    return _naechster_lead(modus, ausser, "l.vertriebspartner_id=%s", [user["vertriebspartner_id"]])


@admin.get("/anrufmodus/naechster")
def admin_naechster(modus: str = "heiss", ausser: str = "", vertriebler: str = "", user: dict = Depends(require_admin)):
    """Anruf-Modus für den Admin: wie beim Vertrieb, aber über alle Leads oder nur die eines Vertrieblers (`vertriebler` = ID, „keiner“ = nicht zugeordnet)."""
    if vertriebler == "keiner":
        return _naechster_lead(modus, ausser, "l.vertriebspartner_id IS NULL", [])
    if vertriebler:
        if not UUID.match(vertriebler):
            raise HTTPException(400, "Unbekannter Vertriebler.")
        return _naechster_lead(modus, ausser, "l.vertriebspartner_id=%s", [vertriebler])
    return _naechster_lead(modus, ausser, "true", [])


class FotoIn(BaseModel):
    typ: str = Field(pattern="^image/(jpeg|png|webp)$")
    daten: str = Field(min_length=100, max_length=7_500_000)   # Base64, ca. 5 MB


MAGIE = {"image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG", "image/webp": b"RIFF"}


@router.post("/leads/foto")
def lead_aus_foto(d: FotoIn, user: dict = Depends(require_vertrieb)):
    """Liest Firma, Ansprechpartner, Telefon, E-Mail, Website, Branche und Ort aus einem Foto. Es wird nichts gespeichert: Der Vertriebler prüft die Felder und legt den Lead selbst an."""
    rate_limit("leadfoto:" + str(user["id"]), 40, 86400)
    try:
        roh = base64.b64decode(d.daten, validate=True)
    except ValueError:
        raise HTTPException(400, "Das Bild konnte nicht gelesen werden.")
    if not roh.startswith(MAGIE[d.typ]):
        raise HTTPException(400, "Das ist kein gültiges Bild (JPEG, PNG oder WebP).")
    with tx("system") as cur:
        cfg = einstellungen.lesen(cur, "ki")
    if not cfg.get("api_key"):
        raise HTTPException(400, "Das Lesen von Fotos ist noch nicht eingerichtet. Bitte den Lead von Hand anlegen.")
    try:
        felder, ein, aus = ki.lead_aus_foto(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, d.typ, d.daten)
    except Exception as e:
        raise ki.fehler(e, user, "Das Foto konnte gerade nicht gelesen werden. Bitte noch einmal versuchen oder von Hand eintragen.")
    with tx("system") as cur:
        kosten = (ein * float(cfg.get("preis_ein_eur", 3.0)) + aus * float(cfg.get("preis_aus_eur", 15.0))) / 1_000_000 * 100
        cur.execute("INSERT INTO kosten_log (kunden_id, dienst, einheit, menge, kosten_cent) VALUES (NULL,'anthropic','tokens',%s,%s)", (ein + aus, round(kosten, 4)))
    if not any(felder.values()):
        raise HTTPException(422, "Auf dem Foto war nichts Lesbares zu erkennen. Bitte ein schärferes Foto machen oder von Hand eintragen.")
    return {"felder": felder, "hinweis": "Bitte alle Felder prüfen. Das Foto wurde nicht gespeichert."}
