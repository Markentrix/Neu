"""Mehrsprachige Texte, Events, Hinweise und „heute geschlossen“ für die Angebotsseite der Kunden-Website."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import publish
from .db import tx
from .routes_zusammenarbeit import nicht_gefunden
from .security import audit, require_admin, require_kunde, require_modul

kunde_router = APIRouter(prefix="/api/kunde")
router = APIRouter(prefix="/api/admin")
MAX_AKTIV = 60


class InhaltIn(BaseModel):
    art: str = Field(pattern="^(angebot|event|hinweis|geschlossen)$")
    titel: dict[str, str] = {}
    text: dict[str, str] = {}
    preis: str | None = Field(default=None, max_length=40)
    gueltig_von: date | None = None
    gueltig_bis: date | None = None


class InhaltAendernIn(BaseModel):
    titel: dict[str, str] | None = None
    text: dict[str, str] | None = None
    preis: str | None = Field(default=None, max_length=40)
    gueltig_von: date | None = None
    gueltig_bis: date | None = None
    datum_loeschen: bool = False
    aktiv: bool | None = None


def _sauber(d: dict[str, str], erlaubt: list[str], feld: str, maxlen: int) -> dict[str, str]:
    out = {}
    for k, v in (d or {}).items():
        v = (v or "").strip()
        if not v:
            continue
        if k not in publish.SPRACHEN:
            raise HTTPException(400, "Unbekannte Sprache.")
        if len(v) > maxlen:
            raise HTTPException(400, f"{feld} ist zu lang (höchstens {maxlen} Zeichen).")
        out[k] = v
    return out


def _web(cur):
    cur.execute("SELECT id, domain, sprachen FROM websites WHERE art='live' ORDER BY erstellt_am LIMIT 1")
    return cur.fetchone()


def _alle(cur):
    cur.execute("""SELECT id, art, titel, text, preis, gueltig_von, gueltig_bis, aktiv, erstellt_am FROM angebots_inhalte
                   ORDER BY aktiv DESC, art, gueltig_von NULLS LAST, erstellt_am DESC LIMIT 300""")
    return cur.fetchall()


def neu_veroeffentlichen(cur):
    """Baut die Seite neu. Gibt (status, hinweis) zurück, ändert nie die Datenbankinhalte."""
    web = _web(cur)
    if not web:
        return "ohne_website", "Noch keine Website verknüpft. Die Einträge sind gespeichert und erscheinen nach der Verknüpfung."
    try:
        publish.inhalte_aktualisieren(web["domain"], web["sprachen"], [i for i in _alle(cur) if i["aktiv"]])
        cur.execute("UPDATE websites SET letzte_veroeffentlichung=now() WHERE id=%s", (web["id"],))
        return "veroeffentlicht", None
    except Exception as e:
        return "fehler", str(e)[:300]


@kunde_router.get("/angebots-inhalte")
def liste(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        require_modul(cur, user, "wochenangebote")
        web = _web(cur)
        return {"sprachen": publish.sprachen_pruefen(web["sprachen"]) if web else ["de"], "sprachnamen": publish.SPRACHEN,
                "website": web["domain"] if web else None, "inhalte": _alle(cur)}


@kunde_router.post("/angebots-inhalte")
def neu(data: InhaltIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        require_modul(cur, user, "wochenangebote")
        web = _web(cur)
        sp = publish.sprachen_pruefen(web["sprachen"]) if web else ["de"]
        titel, text = _sauber(data.titel, sp, "Der Titel", 200), _sauber(data.text, sp, "Der Text", 2000)
        von, bis = data.gueltig_von, data.gueltig_bis
        if data.art == "geschlossen":
            von = von or date.today()
        elif not titel.get("de") and not any(titel.values()):
            raise HTTPException(400, "Bitte gib mindestens einen Titel an.")
        if not titel.get("de") and data.art != "geschlossen":
            raise HTTPException(400, "Bitte fülle den Titel auf Deutsch aus, er dient als Ersatz für fehlende Übersetzungen.")
        if von and bis and bis < von:
            raise HTTPException(400, "Das Enddatum liegt vor dem Startdatum.")
        cur.execute("SELECT count(*) AS n FROM angebots_inhalte WHERE aktiv")
        if cur.fetchone()["n"] >= MAX_AKTIV:
            raise HTTPException(400, f"Es sind höchstens {MAX_AKTIV} aktive Einträge möglich. Bitte lösche alte Einträge.")
        cur.execute("""INSERT INTO angebots_inhalte (kunden_id, art, titel, text, preis, gueltig_von, gueltig_bis, erstellt_von)
                       VALUES (%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s) RETURNING id""",
                    (kid, data.art, _json(titel), _json(text), (data.preis or "").strip() or None, von, bis, user["id"]))
        iid = cur.fetchone()["id"]
        audit(cur, user, "angebots_inhalt_neu", kid, {"art": data.art})
        status, hinweis = neu_veroeffentlichen(cur)
    return {"id": iid, "status": status, "hinweis": hinweis}


def _json(o):
    import json
    return json.dumps(o, ensure_ascii=False)


@kunde_router.patch("/angebots-inhalte/{iid}")
def aendern(iid: str, data: InhaltAendernIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            require_modul(cur, user, "wochenangebote")
            cur.execute("SELECT * FROM angebots_inhalte WHERE id=%s FOR UPDATE", (iid,))
            alt = cur.fetchone()
            if not alt:
                raise nicht_gefunden()
            web = _web(cur)
            sp = publish.sprachen_pruefen(web["sprachen"]) if web else ["de"]
            titel = _sauber(data.titel, sp, "Der Titel", 200) if data.titel is not None else alt["titel"]
            text = _sauber(data.text, sp, "Der Text", 2000) if data.text is not None else alt["text"]
            von = None if data.datum_loeschen else (data.gueltig_von or alt["gueltig_von"])
            bis = None if data.datum_loeschen else (data.gueltig_bis or alt["gueltig_bis"])
            if alt["art"] == "geschlossen" and not von:
                von = date.today()
            if von and bis and bis < von:
                raise HTTPException(400, "Das Enddatum liegt vor dem Startdatum.")
            if alt["art"] != "geschlossen" and not titel.get("de"):
                raise HTTPException(400, "Der Titel auf Deutsch darf nicht leer sein.")
            preis = alt["preis"] if data.preis is None else ((data.preis or "").strip() or None)
            cur.execute("""UPDATE angebots_inhalte SET titel=%s::jsonb, text=%s::jsonb, preis=%s, gueltig_von=%s, gueltig_bis=%s, aktiv=coalesce(%s,aktiv), geaendert_am=now() WHERE id=%s""",
                        (_json(titel), _json(text), preis, von, bis, data.aktiv, iid))
            audit(cur, user, "angebots_inhalt_geaendert", kid, {"id": iid})
            status, hinweis = neu_veroeffentlichen(cur)
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"status": status, "hinweis": hinweis}


@kunde_router.delete("/angebots-inhalte/{iid}")
def loeschen(iid: str, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            require_modul(cur, user, "wochenangebote")
            cur.execute("DELETE FROM angebots_inhalte WHERE id=%s RETURNING id", (iid,))
            if not cur.fetchone():
                raise nicht_gefunden()
            audit(cur, user, "angebots_inhalt_geloescht", kid, {"id": iid})
            status, hinweis = neu_veroeffentlichen(cur)
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"status": status, "hinweis": hinweis}


class SprachenIn(BaseModel):
    sprachen: list[str]


@router.put("/websites/{wid}/sprachen")
def sprachen_setzen(wid: str, data: SprachenIn, user: dict = Depends(require_admin)):
    if any(s not in publish.SPRACHEN for s in data.sprachen):
        raise HTTPException(400, "Erlaubt sind: " + ", ".join(publish.SPRACHEN))
    sp = publish.sprachen_pruefen(data.sprachen)
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE websites SET sprachen=%s WHERE id=%s RETURNING kunden_id", (sp, wid))
            w = cur.fetchone()
            if not w:
                raise nicht_gefunden()
            audit(cur, user, "website_sprachen", w["kunden_id"], {"sprachen": sp})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"sprachen": sp}
