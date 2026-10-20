"""Admin-Werkzeuge: Zahlungserinnerungen mit Entwurf, Sammelaktionen für Kunden, Textvorlagen, gespeicherte Filter."""
import json
import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import mailer
from .db import tx
from .routes_belege import MAHN_TITEL, mahnung_ausfuehren
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")


# ================================================================= 1. Zahlungserinnerungen: Vorschlag prüfen, dann senden
@router.get("/mahnvorschlaege")
def mahnvorschlaege(user: dict = Depends(require_admin)):
    """Alle überfälligen Rechnungen mit der nächsten Mahnstufe und fertigem Mailtext (Entwurf, wird nichts versendet)."""
    with tx("admin") as cur:
        cur.execute("""SELECT b.id, b.nummer, b.faellig_am, b.brutto_cent, b.mahnstufe, b.mahn_am, (current_date - b.faellig_am) AS tage,
                              k.id AS kunden_id, k.firma, k.kundennummer, k.email, k.ansprechpartner
                       FROM belege b JOIN kunden k ON k.id = b.kunden_id
                       WHERE b.art = 'rechnung' AND b.status IN ('gestellt','versendet') AND b.faellig_am < current_date AND b.nummer IS NOT NULL
                       ORDER BY b.faellig_am LIMIT 100""")
        rows = cur.fetchall()
    out = []
    for r in rows:
        stufe = r["mahnstufe"] + 1
        e = {"id": r["id"], "nummer": r["nummer"], "firma": r["firma"], "kundennummer": r["kundennummer"], "kunden_id": r["kunden_id"], "email": r["email"],
             "brutto_cent": r["brutto_cent"], "faellig_am": r["faellig_am"], "tage": r["tage"], "mahnstufe": r["mahnstufe"], "stufe": None, "titel": None,
             "betreff": None, "text": None, "moeglich": False, "grund": "", "warnung": ""}
        if stufe > 3:
            e["grund"] = "Alle drei Stufen wurden schon verschickt. Bitte persönlich klären."
        elif not r["email"]:
            e["grund"] = "Beim Kunden ist keine E-Mail-Adresse hinterlegt."
        else:
            titel = MAHN_TITEL[stufe]
            e.update(stufe=stufe, titel=titel, betreff=f"{titel} zu Rechnung {r['nummer']}", moeglich=True,
                     text=mailer.mahn_text(titel, r["nummer"], (r["ansprechpartner"] or "").strip() or None))
            if r["mahn_am"] and (date.today() - r["mahn_am"]).days < 7:
                e["warnung"] = f"Die letzte Mahnung ging erst vor {(date.today() - r['mahn_am']).days} Tagen raus."
        out.append(e)
    return out


class MahnEintrag(BaseModel):
    id: str
    stufe: int = Field(ge=1, le=3)
    text: str | None = Field(default=None, max_length=5000)


class MahnSendenIn(BaseModel):
    eintraege: list[MahnEintrag] = Field(min_length=1, max_length=30)


@router.post("/mahnungen/senden")
def mahnungen_senden(data: MahnSendenIn, user: dict = Depends(require_admin)):
    """Verschickt die ausgewählten Erinnerungen/Mahnungen. Jede wird einzeln geprüft, ein Fehler stoppt die anderen nicht."""
    ergebnis = []
    for e in data.eintraege:
        try:
            r = mahnung_ausfuehren(user, e.id, e.stufe, True, e.text)
            ergebnis.append({"id": e.id, "gesendet": r["gesendet"], "grund": r["grund"]})
        except HTTPException as x:
            ergebnis.append({"id": e.id, "gesendet": False, "grund": str(x.detail)})
    return {"ergebnis": ergebnis, "gesendet": sum(1 for r in ergebnis if r["gesendet"])}


# ================================================================= 4. Textvorlagen (Mails, Aufgabenpakete)
class VorlageIn(BaseModel):
    art: str = Field(pattern="^(mail|aufgaben)$")
    name: str = Field(min_length=2, max_length=80)
    betreff: str | None = Field(default=None, max_length=200)
    text: str | None = Field(default=None, max_length=8000)
    aufgaben: list[dict] = Field(default_factory=list, max_length=30)


def _aufgaben_pruefen(liste: list[dict]) -> list[dict]:
    out = []
    for a in liste:
        titel = str(a.get("titel") or "").strip()[:200]
        if not titel:
            continue
        try:
            tage = max(0, min(365, int(a.get("tage") or 0)))
        except (TypeError, ValueError):
            tage = 0
        out.append({"titel": titel, "tage": tage})
    return out


def fuellen(text: str | None, k: dict) -> str:
    """Platzhalter ersetzen: {firma}, {name}, {kundennummer}, {ort}."""
    name = (k.get("ansprechpartner") or "").strip() or (k.get("firma") or "")
    return (text or "").replace("{firma}", k.get("firma") or "").replace("{name}", name).replace("{kundennummer}", k.get("kundennummer") or "").replace("{ort}", k.get("ort") or "")


@router.get("/textvorlagen")
def vorlagen_liste(art: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id, art, name, betreff, text, aufgaben FROM textvorlagen WHERE %s = '' OR art = %s ORDER BY art, name", (art, art))
        return cur.fetchall()


@router.post("/textvorlagen")
def vorlage_neu(data: VorlageIn, user: dict = Depends(require_admin)):
    aufg = _aufgaben_pruefen(data.aufgaben)
    if data.art == "aufgaben" and not aufg:
        raise HTTPException(400, "Ein Aufgabenpaket braucht mindestens eine Aufgabe.")
    if data.art == "mail" and not (data.text or "").strip():
        raise HTTPException(400, "Bitte einen Text eintragen.")
    try:
        with tx("admin") as cur:
            cur.execute("INSERT INTO textvorlagen (art, name, betreff, text, aufgaben) VALUES (%s,%s,%s,%s,%s::jsonb) RETURNING id",
                        (data.art, data.name.strip(), data.betreff, data.text, json.dumps(aufg)))
            vid = cur.fetchone()["id"]
            audit(cur, user, "textvorlage_angelegt", None, {"name": data.name, "art": data.art})
    except errors.UniqueViolation:
        raise HTTPException(409, "Eine Vorlage mit diesem Namen gibt es schon.")
    return {"id": vid}


@router.put("/textvorlagen/{vid}")
def vorlage_aendern(vid: str, data: VorlageIn, user: dict = Depends(require_admin)):
    aufg = _aufgaben_pruefen(data.aufgaben)
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE textvorlagen SET name=%s, betreff=%s, text=%s, aufgaben=%s::jsonb, geaendert_am=now() WHERE id=%s AND art=%s",
                        (data.name.strip(), data.betreff, data.text, json.dumps(aufg), vid, data.art))
            if not cur.rowcount:
                raise HTTPException(404, "Vorlage nicht gefunden.")
            audit(cur, user, "textvorlage_geaendert", None, {"name": data.name})
    except errors.UniqueViolation:
        raise HTTPException(409, "Eine Vorlage mit diesem Namen gibt es schon.")
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vorlage nicht gefunden.")
    return {"ok": True}


@router.delete("/textvorlagen/{vid}")
def vorlage_loeschen(vid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM textvorlagen WHERE id=%s RETURNING name", (vid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Vorlage nicht gefunden.")
            audit(cur, user, "textvorlage_geloescht", None, {"name": r["name"]})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vorlage nicht gefunden.")
    return {"ok": True}


@router.get("/textvorlagen/{vid}/fuer/{kid}")
def vorlage_gefuellt(vid: str, kid: str, user: dict = Depends(require_admin)):
    """Mailvorlage mit den Angaben eines Kunden ausgefüllt (für Antworten und Sammelmails)."""
    try:
        with tx("admin") as cur:
            cur.execute("SELECT betreff, text FROM textvorlagen WHERE id=%s AND art='mail'", (vid,))
            v = cur.fetchone()
            cur.execute("SELECT firma, ansprechpartner, kundennummer, ort FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vorlage oder Kunde nicht gefunden.")
    if not v or not k:
        raise HTTPException(404, "Vorlage oder Kunde nicht gefunden.")
    return {"betreff": fuellen(v["betreff"], k), "text": fuellen(v["text"], k)}


def paket_anwenden(cur, user: dict, k: dict, v: dict) -> int:
    """Legt die Aufgaben eines Pakets für einen Kunden an. Doppelt anwenden legt nichts doppelt an."""
    n = 0
    for i, a in enumerate(v["aufgaben"] or []):
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel) VALUES (%s,%s,%s,%s,'auto',%s) ON CONFLICT DO NOTHING""",
                    (k["id"], f"{k['firma']}: {a['titel']}"[:200], user["email"], date.today() + timedelta(days=int(a.get("tage") or 0)), f"paket-{v['id']}-{i}-{k['id']}"))
        n += cur.rowcount
    return n


class PaketIn(BaseModel):
    vorlage_id: str


@router.post("/kunden/{kid}/aufgabenpaket")
def aufgabenpaket(kid: str, data: PaketIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, name, aufgaben FROM textvorlagen WHERE id=%s AND art='aufgaben'", (data.vorlage_id,))
            v = cur.fetchone()
            cur.execute("SELECT id, firma FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if not v or not k:
                raise HTTPException(404, "Vorlage oder Kunde nicht gefunden.")
            n = paket_anwenden(cur, user, k, v)
            audit(cur, user, "aufgabenpaket", kid, {"paket": v["name"], "angelegt": n})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vorlage oder Kunde nicht gefunden.")
    return {"angelegt": n, "name": v["name"]}


# ================================================================= 2. Sammelaktionen für Kunden
class KundenBulkIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=200)
    aktion: str = Field(pattern="^(aufgabe|mail|aufgabenpaket)$")
    titel: str | None = Field(default=None, max_length=200)
    faellig_am: date | None = None
    vorlage_id: str | None = None
    betreff: str | None = Field(default=None, max_length=200)
    text: str | None = Field(default=None, max_length=8000)


MAX_MAILS = 40


@router.post("/kunden/bulk")
def kunden_bulk(data: KundenBulkIn, user: dict = Depends(require_admin)):
    ids = list(dict.fromkeys(data.ids))
    if data.aktion == "aufgabe" and not (data.titel or "").strip():
        raise HTTPException(400, "Bitte einen Titel für die Aufgabe eintragen.")
    if data.aktion == "mail" and (not (data.betreff or "").strip() or not (data.text or "").strip()):
        raise HTTPException(400, "Bitte Betreff und Text eintragen.")
    if data.aktion == "mail" and len(ids) > MAX_MAILS:
        raise HTTPException(400, f"Pro Sammelmail höchstens {MAX_MAILS} Kunden, damit nichts hängen bleibt.")
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, firma, ansprechpartner, kundennummer, ort, email FROM kunden WHERE id = ANY(%s::uuid[])", (ids,))
            kunden = cur.fetchall()
            paket = None
            if data.aktion == "aufgabenpaket":
                cur.execute("SELECT id, name, aufgaben FROM textvorlagen WHERE id=%s AND art='aufgaben'", (data.vorlage_id,))
                paket = cur.fetchone()
                if not paket:
                    raise HTTPException(404, "Aufgabenpaket nicht gefunden.")
            n = 0
            if data.aktion == "aufgabe":
                for k in kunden:
                    cur.execute("INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am) VALUES (%s,%s,%s,%s)", (k["id"], data.titel.strip(), user["email"], data.faellig_am))
                    n += 1
            elif paket:
                for k in kunden:
                    n += paket_anwenden(cur, user, k, paket)
            if data.aktion != "mail":
                audit(cur, user, "kunden_bulk", None, {"aktion": data.aktion, "kunden": len(kunden), "angelegt": n})
                return {"angelegt": n, "kunden": len(kunden)}
    except errors.InvalidTextRepresentation:
        raise HTTPException(400, "Ungültige Auswahl.")
    gesendet, fehler, ohne = 0, [], 0
    for k in kunden:
        if not k["email"]:
            ohne += 1
            continue
        ok, grund = mailer.senden(k["email"], fuellen(data.betreff, k), fuellen(data.text, k))
        if ok:
            gesendet += 1
        else:
            fehler.append({"firma": k["firma"], "grund": grund})
    with tx("admin") as cur:
        audit(cur, user, "kunden_bulk_mail", None, {"kunden": len(kunden), "gesendet": gesendet, "fehler": len(fehler), "ohne_mail": ohne, "betreff": data.betreff})
    return {"gesendet": gesendet, "fehler": fehler, "ohne_mail": ohne, "kunden": len(kunden)}


# ================================================================= 3. Gespeicherte Filter
class FilterIn(BaseModel):
    bereich: str = Field(pattern="^(leads|kunden|belege)$")
    name: str = Field(min_length=1, max_length=60)
    abfrage: str = Field(default="", max_length=500)


@router.get("/meine-filter")
def filter_liste(bereich: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id, bereich, name, abfrage FROM gespeicherte_filter WHERE benutzer_id=%s AND (%s = '' OR bereich = %s) ORDER BY bereich, name", (user["id"], bereich, bereich))
        return cur.fetchall()


@router.post("/meine-filter")
def filter_speichern(data: FilterIn, user: dict = Depends(require_admin)):
    abfrage = data.abfrage.lstrip("?#").strip()
    if not re.fullmatch(r"[\w%+.,:=&\-äöüÄÖÜß ]*", abfrage):
        raise HTTPException(400, "Der Filter enthält ungültige Zeichen.")
    with tx("admin") as cur:
        cur.execute("""INSERT INTO gespeicherte_filter (benutzer_id, bereich, name, abfrage) VALUES (%s,%s,%s,%s)
                       ON CONFLICT (benutzer_id, bereich, name) DO UPDATE SET abfrage = EXCLUDED.abfrage RETURNING id""", (user["id"], data.bereich, data.name.strip(), abfrage))
        fid = cur.fetchone()["id"]
    return {"id": fid}


@router.delete("/meine-filter/{fid}")
def filter_loeschen(fid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM gespeicherte_filter WHERE id=%s AND benutzer_id=%s", (fid, user["id"]))
            if not cur.rowcount:
                raise HTTPException(404, "Filter nicht gefunden.")
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Filter nicht gefunden.")
    return {"ok": True}
