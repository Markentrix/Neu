import json
"""Admin: Vertriebler, Leads, Preise und Konditionen, Datenschutz und Qualität."""
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors, sql
from pydantic import BaseModel, Field

from . import config, leadkontakt, leadpruefung, onboarding, push, zugang
from .db import tx
from .security import EMAIL_RE, audit, require_admin

router = APIRouter(prefix="/api/admin")

PARTNER_STATUS = ("anfrage", "aktiv", "pausiert", "beendet")
LEAD_STATUS = ("neu", "kontaktiert", "antwort", "termin", "angebot", "gewonnen", "verloren", "gesperrt", "consent_ausstehend", "tot")
PROV_STATUS = ("berechnet", "freigegeben", "ausgezahlt", "storniert")
AKT_ART = ("mail_gesendet", "antwort", "anruf", "termin", "notiz", "statuswechsel", "consent")


def fehler_db(e):
    if isinstance(e, errors.ForeignKeyViolation):
        return HTTPException(400, "Verweis auf einen Eintrag, den es nicht gibt.")
    if isinstance(e, errors.UniqueViolation):
        return HTTPException(409, "Diesen Eintrag gibt es schon.")
    return HTTPException(400, "Ein Feld hat einen ungültigen oder fehlenden Wert.")


DB_FEHLER = (errors.CheckViolation, errors.ForeignKeyViolation, errors.UniqueViolation, errors.NotNullViolation,
             errors.InvalidTextRepresentation, errors.InvalidDatetimeFormat, errors.NumericValueOutOfRange)


def felder_setzen(cur, tabelle, rid, felder, idspalte="id"):
    if not felder:
        return
    teile = sql.SQL(", ").join(sql.SQL("{}=%s").format(sql.Identifier(k)) for k in felder)
    cur.execute(sql.SQL("UPDATE {} SET {} WHERE {}=%s").format(sql.Identifier(tabelle), teile, sql.Identifier(idspalte)), (*felder.values(), rid))
    if cur.rowcount == 0:
        raise HTTPException(404, "Nicht gefunden.")


# ================================================================= Vertriebler
class PartnerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    status: str = "aktiv"
    notiz: str | None = Field(default=None, max_length=2000)
    einladen: bool = False   # Portal-Einladung gleich per E-Mail senden (braucht E-Mail-Adresse)


class PartnerPatch(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    status: str | None = None
    notiz: str | None = Field(default=None, max_length=2000)
    iban_hinterlegt: bool | None = None
    vereinbarung_am: date | None = None


@router.get("/vertrieb/partner")
def partner_liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT v.id, v.name, v.firma, v.email, v.telefon, v.status, v.iban_hinterlegt, v.vereinbarung_am,
                       (SELECT CASE WHEN bool_or(b.passwort_hash IS NOT NULL AND b.aktiv) THEN 'aktiv' WHEN bool_or(b.einladung_token_hash IS NOT NULL AND b.einladung_ablauf > now()) THEN 'eingeladen'
                               WHEN count(*) > 0 THEN 'abgelaufen' ELSE 'keiner' END FROM benutzer b WHERE b.vertriebspartner_id=v.id) AS zugang,
                       (SELECT count(*) FROM kunden k WHERE k.vertriebspartner_id=v.id) AS kunden,
                       (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=v.id AND l.status NOT IN ('gewonnen','verloren','tot','gesperrt')) AS offene_leads,
                       (SELECT coalesce(sum(betrag_cent),0) FROM provisionen p WHERE p.vertriebspartner_id=v.id AND p.status IN ('berechnet','freigegeben')) AS offen_cent
                       FROM vertriebspartner v ORDER BY (v.status='aktiv') DESC, lower(v.name)""")
        return cur.fetchall()


@router.post("/vertrieb/partner")
def partner_neu(data: PartnerIn, user: dict = Depends(require_admin)):
    if data.status not in PARTNER_STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    if data.email and not EMAIL_RE.match(data.email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    with tx("admin") as cur:
        cur.execute("INSERT INTO vertriebspartner (name, firma, email, telefon, status, notiz) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                    (data.name.strip(), data.firma, data.email, data.telefon, data.status, data.notiz))
        r = cur.fetchone()
        audit(cur, user, "partner_angelegt", None, {"name": data.name})
        link = None
        if data.einladen:
            if not data.email:
                raise HTTPException(400, "Für die Einladung wird eine E-Mail-Adresse gebraucht.")
            link = zugang.link_erzeugen(cur, data.email, data.name.strip(), "vertrieb", partner_id=r["id"])
            audit(cur, user, "partner_einladung", None, {"partner": str(r["id"])})
    if link:
        return {**r, "einladungslink": link, "mail": zugang.per_mail(data.email, data.name.strip(), link, "vertrieb")}
    return r


@router.get("/vertrieb/partner/{pid}")
def partner_detail(pid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT * FROM vertriebspartner WHERE id=%s", (pid,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(404, "Vertriebler nicht gefunden.")
            cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.status, pk.name AS paket,
                           (SELECT coalesce(sum(b.monatlich_cent - b.rabatt_cent),0) FROM buchungen b WHERE b.kunden_id=k.id AND b.status IN ('beauftragt','in_einrichtung','aktiv')) AS monatlich_cent
                           FROM kunden k LEFT JOIN produkte pk ON pk.code=k.paket_code WHERE k.vertriebspartner_id=%s ORDER BY k.kundennummer DESC""", (pid,))
            kunden = cur.fetchall()
            cur.execute("""SELECT pr.art, pr.notiz, pr.id, pr.monat, k.kundennummer, k.firma, pr.vertragsmonat, pr.basis_cent, pr.prozent, pr.betrag_cent, pr.status
                           FROM provisionen pr JOIN kunden k ON k.id=pr.kunden_id WHERE pr.vertriebspartner_id=%s ORDER BY pr.monat DESC, k.kundennummer LIMIT 300""", (pid,))
            prov = cur.fetchall()
            cur.execute("SELECT id, firma, status, ort, erstellt_am FROM leads WHERE vertriebspartner_id=%s ORDER BY erstellt_am DESC LIMIT 100", (pid,))
            leads = cur.fetchall()
            cur.execute("SELECT id, email, aktiv, letzter_login, totp_aktiv, passwort_hash IS NOT NULL AS hat_passwort FROM benutzer WHERE vertriebspartner_id=%s ORDER BY erstellt_am", (pid,))
            zugaenge = cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vertriebler nicht gefunden.")
    return {"partner": p, "kunden": kunden, "provisionen": prov, "leads": leads, "zugaenge": zugaenge}


@router.patch("/vertrieb/partner/{pid}")
def partner_aendern(pid: str, data: PartnerPatch, user: dict = Depends(require_admin)):
    felder = {k: v for k, v in data.model_dump().items() if v is not None}
    if "status" in felder and felder["status"] not in PARTNER_STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    if "email" in felder and not EMAIL_RE.match(felder["email"].strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    try:
        with tx("admin") as cur:
            felder_setzen(cur, "vertriebspartner", pid, felder)
            if felder.get("status") == "beendet":
                cur.execute("UPDATE vertriebspartner SET beendet_am=coalesce(beendet_am, current_date) WHERE id=%s", (pid,))
            elif felder.get("status"):
                cur.execute("UPDATE vertriebspartner SET beendet_am=NULL WHERE id=%s", (pid,))
            audit(cur, user, "partner_geaendert", None, {"id": pid, "felder": list(felder)})
    except DB_FEHLER as e:
        raise fehler_db(e)
    return {"ok": True}


class ZuordnungIn(BaseModel):
    partner_id: str | None = None


@router.put("/kunden/{kid}/partner")
def kunde_partner(kid: str, data: ZuordnungIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE kunden SET vertriebspartner_id=%s WHERE id=%s", (data.partner_id or None, kid))
            if cur.rowcount == 0:
                raise HTTPException(404, "Kunde nicht gefunden.")
            audit(cur, user, "kunde_vertriebler_zugeordnet", kid, {"partner_id": data.partner_id})
    except DB_FEHLER as e:
        raise fehler_db(e)
    return {"ok": True}


@router.get("/vertrieb/partnerliste")
def partner_auswahl(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id, name, status FROM vertriebspartner WHERE status IN ('anfrage','aktiv','pausiert') ORDER BY lower(name)")
        return cur.fetchall()


class StatusIn(BaseModel):
    status: str


@router.post("/vertrieb/provisionen/{rid}/status")
def provision_status(rid: str, data: StatusIn, user: dict = Depends(require_admin)):
    if data.status not in PROV_STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    try:
        with tx("admin") as cur:
            felder_setzen(cur, "provisionen", rid, {"status": data.status})
            audit(cur, user, "provision_status", None, {"id": rid, "status": data.status})
    except DB_FEHLER as e:
        raise fehler_db(e)
    return {"ok": True}


@router.get("/vertrieb/provisionsuebersicht")
def provisionsuebersicht(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT v.id, v.name, p.status, count(*) AS anzahl, sum(p.betrag_cent) AS summe_cent
                       FROM provisionen p JOIN vertriebspartner v ON v.id=p.vertriebspartner_id GROUP BY v.id, v.name, p.status ORDER BY v.name, p.status""")
        return cur.fetchall()


# ================================================================= Leads
class LeadIn(BaseModel):
    trotzdem: bool = False
    ansprache_grundlage: str | None = None
    firma: str = Field(min_length=1, max_length=200)
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=253)
    branche: str | None = Field(default=None, max_length=120)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=120)
    quelle: str = "manuell"
    vertriebspartner_id: str | None = None
    notiz: str | None = Field(default=None, max_length=2000)


class LeadPatch(BaseModel):
    status: str | None = None
    temperatur: str | None = None   # kalt | warm | heiss, leer = Einstufung entfernen
    vertriebspartner_id: str | None = None
    zuordnung_loeschen: bool = False
    notiz: str | None = Field(default=None, max_length=2000)
    score: int | None = Field(default=None, ge=0, le=100)
    firma: str | None = Field(default=None, max_length=200)
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=253)
    branche: str | None = Field(default=None, max_length=120)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=120)
    ansprache_grundlage: str | None = None
    ansprache_hinweis: str | None = Field(default=None, max_length=300)


KONTAKTFELDER = ("ansprechpartner", "email", "telefon", "website", "branche", "plz", "ort")


FILTER_WHERE = """(%(s)s='' OR l.status=%(s)s)
                         AND (%(q)s='' OR l.firma ILIKE %(l)s OR coalesce(l.ort,'') ILIKE %(l)s OR coalesce(l.email,'') ILIKE %(l)s OR coalesce(l.telefon,'') ILIKE %(l)s OR coalesce(l.branche,'') ILIKE %(l)s OR coalesce(l.ansprechpartner,'') ILIKE %(l)s OR coalesce(l.notiz,'') ILIKE %(l)s)
                         AND (%(qu)s='' OR l.quelle=%(qu)s)
                         AND (%(t)s='' OR (%(t)s='keine' AND l.temperatur IS NULL) OR l.temperatur=%(t)s)
                         AND (%(v)s='' OR (%(v)s='keiner' AND l.vertriebspartner_id IS NULL) OR l.vertriebspartner_id::text=%(v)s)
                         AND (%(li)s='' OR l.liste=%(li)s)
                         AND (%(g)s='' OR l.gruppe=%(g)s)
                         AND (%(fk)s='' OR (%(fk)s='ueberfaellig' AND l.wiedervorlage_am < current_date AND l.status IN ('neu','kontaktiert','antwort','termin','angebot'))
                              OR (%(fk)s='ohne_kontakt' AND l.status IN ('kontaktiert','antwort','termin','angebot') AND coalesce(l.letzter_kontakt_am, l.erstellt_am) < now() - interval '7 days')
                              OR (%(fk)s='heiss_unzugewiesen' AND l.vertriebspartner_id IS NULL AND l.temperatur='heiss' AND l.status IN ('neu','kontaktiert','antwort')))"""
SEITE = 50


def _filter(status="", q="", quelle="", temperatur="", vertriebler="", liste="", gruppe="", fokus="") -> dict:
    return {"s": status, "q": q, "l": f"%{q}%", "qu": quelle, "t": temperatur, "v": vertriebler, "li": liste, "g": gruppe, "fk": fokus if fokus in ("ueberfaellig", "ohne_kontakt", "heiss_unzugewiesen") else ""}


@router.get("/leads")
def leads_liste(status: str = "", q: str = "", quelle: str = "", temperatur: str = "", vertriebler: str = "", liste: str = "", gruppe: str = "", fokus: str = "", seite: int = 1, user: dict = Depends(require_admin)):
    """Filter: Status, Suche, Quelle, Einstufung, Vertriebler (ID oder 'keiner'), Importliste, Branchengruppe. 50 Leads pro Seite."""
    f = _filter(status, q, quelle, temperatur, vertriebler, liste, gruppe, fokus)
    seite = max(1, seite)
    with tx("admin") as cur:
        cur.execute(f"SELECT count(*) AS n FROM leads l WHERE {FILTER_WHERE}", f)
        gesamt = cur.fetchone()["n"]
        cur.execute(f"""SELECT l.id, l.firma, l.ansprechpartner, l.email, l.telefon, l.ort, l.branche, l.quelle, l.status, l.temperatur, l.liste, l.gruppe, l.wiedervorlage_am, l.letzter_kontakt_am, l.score, l.erstellt_am, l.kunden_id, v.name AS vertriebler
                       FROM leads l LEFT JOIN vertriebspartner v ON v.id=l.vertriebspartner_id
                       WHERE {FILTER_WHERE}
                       ORDER BY {"l.wiedervorlage_am NULLS LAST, coalesce(l.letzter_kontakt_am, l.erstellt_am), l.firma" if f["fk"] else "l.erstellt_am DESC, l.firma"} LIMIT {SEITE} OFFSET {(seite - 1) * SEITE}""", f)
        rows = cur.fetchall()
        cur.execute("SELECT status, count(*) AS n FROM leads GROUP BY status")
        zaehler = {r["status"]: r["n"] for r in cur.fetchall()}
        cur.execute("SELECT liste, count(*) AS n FROM leads WHERE liste IS NOT NULL GROUP BY liste ORDER BY max(erstellt_am) DESC LIMIT 50")
        listen = cur.fetchall()
        cur.execute("SELECT gruppe, count(*) AS n FROM leads WHERE gruppe IS NOT NULL GROUP BY gruppe ORDER BY gruppe")
        gruppen = cur.fetchall()
    return {"leads": rows, "zaehler": zaehler, "listen": listen, "gruppen": gruppen, "gesamt": gesamt, "seite": seite, "pro_seite": SEITE}


class BulkIn(BaseModel):
    aktion: str                              # temperatur | vertriebler | status | loeschen
    wert: str | None = None
    ids: list[str] | None = Field(default=None, max_length=500)
    alle_gefilterten: bool = False
    filter: dict | None = None


@router.post("/leads/bulk")
def leads_bulk(data: BulkIn, user: dict = Depends(require_admin)):
    """Mehrere Leads auf einmal ändern: ausgewählte (ids) oder alle, die zum aktuellen Filter passen."""
    if data.aktion not in ("temperatur", "vertriebler", "status", "loeschen"):
        raise HTTPException(400, "Unbekannte Aktion.")
    if data.aktion == "temperatur" and data.wert not in ("", "kalt", "warm", "heiss", None):
        raise HTTPException(400, "Ungültige Einstufung.")
    if data.aktion == "status" and data.wert not in ("neu", "kontaktiert", "antwort", "termin", "angebot", "verloren", "tot"):
        raise HTTPException(400, "Ungültiger Status.")
    f = _filter(**{k: str(v) for k, v in (data.filter or {}).items() if k in ("status", "q", "quelle", "temperatur", "vertriebler", "liste", "gruppe", "fokus")})
    push_ziel = None
    try:
        with tx("admin") as cur:
            if data.alle_gefilterten:
                cur.execute(f"SELECT l.id FROM leads l WHERE {FILTER_WHERE} AND l.kunden_id IS NULL LIMIT 5000", f)
                ids = [r["id"] for r in cur.fetchall()]
            elif data.ids:
                ids = data.ids
            else:
                raise HTTPException(400, "Keine Leads ausgewählt.")
            if not ids:
                return {"geaendert": 0}
            if data.aktion == "loeschen":
                cur.execute("DELETE FROM leads WHERE id = ANY(%s::uuid[]) AND kunden_id IS NULL", (ids,))
            elif data.aktion == "temperatur":
                cur.execute("UPDATE leads SET temperatur=%s WHERE id = ANY(%s::uuid[])", (data.wert or None, ids))
            elif data.aktion == "vertriebler":
                if data.wert:
                    cur.execute("SELECT 1 FROM vertriebspartner WHERE id=%s", (data.wert,))
                    if not cur.fetchone():
                        raise HTTPException(400, "Vertriebler nicht gefunden.")
                cur.execute("UPDATE leads SET vertriebspartner_id=%s WHERE id = ANY(%s::uuid[])", (data.wert or None, ids))
                zugewiesen = cur.rowcount
                if data.wert and zugewiesen:
                    push_ziel = (push.partner(cur, data.wert), zugewiesen)
            else:
                cur.execute("UPDATE leads SET status=%s WHERE id = ANY(%s::uuid[]) AND status NOT IN ('gewonnen','gesperrt','consent_ausstehend')", (data.wert, ids))
            n = zugewiesen if data.aktion == "vertriebler" else cur.rowcount
            audit(cur, user, "leads_bulk", None, {"aktion": data.aktion, "wert": data.wert, "anzahl": n})
    except (errors.InvalidTextRepresentation, errors.DataError):
        raise HTTPException(400, "Ungültige Auswahl.")
    if push_ziel:
        push.senden(push_ziel[0], "Neue Leads", f"{push_ziel[1]} Lead(s) wurden Ihnen zugewiesen.", "/vertrieb#heute", "zugewiesen")
    return {"geaendert": n}


@router.post("/leads")
def lead_neu(data: LeadIn, user: dict = Depends(require_admin)):
    d = data.model_dump()
    if d["ansprache_grundlage"] not in (None, "", "anfrage", "einwilligung", "b2b_mutmasslich", "empfehlung", "bestandskontakt"):
        raise HTTPException(400, "Ungültige Grundlage der Ansprache.")
    d["ansprache_grundlage"] = d["ansprache_grundlage"] or None
    try:
        with tx("admin") as cur:
            leadpruefung.pruefen(cur, d, trotzdem=d.pop("trotzdem"))
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, branche, plz, ort, quelle, vertriebspartner_id, notiz, ansprache_grundlage)
                           VALUES (%(firma)s,%(ansprechpartner)s,%(email)s,%(telefon)s,%(website)s,%(branche)s,%(plz)s,%(ort)s,%(quelle)s,%(vertriebspartner_id)s,%(notiz)s,%(ansprache_grundlage)s) RETURNING id""", d)
            r = cur.fetchone()
            audit(cur, user, "lead_angelegt", None, {"firma": data.firma})
    except DB_FEHLER as e:
        raise fehler_db(e)
    return r


@router.get("/leads/{lid}")
def lead_detail(lid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT l.*, v.name AS vertriebler FROM leads l LEFT JOIN vertriebspartner v ON v.id=l.vertriebspartner_id WHERE l.id=%s", (lid,))
            l = cur.fetchone()
            if not l:
                raise HTTPException(404, "Lead nicht gefunden.")
            cur.execute("SELECT id, art, inhalt, zeit, von FROM lead_aktivitaeten WHERE lead_id=%s ORDER BY zeit DESC LIMIT 200", (lid,))
            akt = cur.fetchall()
            cur.execute("SELECT id, website, score, ergebnis, erstellt_am, status, ampel FROM lead_checks WHERE lead_id=%s ORDER BY erstellt_am DESC LIMIT 20", (lid,))
            checks = cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    return {"lead": l, "aktivitaeten": akt, "checks": checks, "kontakt_optionen": leadkontakt.optionen_fuer_oberflaeche(), "verlustgruende": leadkontakt.VERLUSTGRUENDE}


@router.patch("/leads/{lid}")
def lead_aendern(lid: str, data: LeadPatch, user: dict = Depends(require_admin)):
    felder = {k: v for k, v in data.model_dump(exclude={"zuordnung_loeschen"}).items() if v is not None}
    if data.zuordnung_loeschen:
        felder["vertriebspartner_id"] = None
    if "status" in felder and felder["status"] not in LEAD_STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    for k in KONTAKTFELDER + ("firma",):
        if k in felder:
            felder[k] = felder[k].strip() or None   # leer = Angabe entfernen
    if "firma" in felder and not felder["firma"]:
        raise HTTPException(400, "Die Firma darf nicht leer sein.")
    if felder.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", felder["email"]):
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse eintragen.")
    if felder.get("ansprache_grundlage") not in (None, "anfrage", "einwilligung", "b2b_mutmasslich", "empfehlung", "bestandskontakt"):
        raise HTTPException(400, "Ungültige Grundlage der Ansprache.")
    if "temperatur" in felder:
        if felder["temperatur"] not in ("kalt", "warm", "heiss", ""):
            raise HTTPException(400, "Unbekannte Einstufung.")
        felder["temperatur"] = felder["temperatur"] or None
    try:
        with tx("admin") as cur:
            if "status" in felder:
                cur.execute("SELECT status FROM leads WHERE id=%s", (lid,))
                alt = cur.fetchone()
                if not alt:
                    raise HTTPException(404, "Lead nicht gefunden.")
                if alt["status"] != felder["status"]:
                    cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)",
                                (lid, f"{alt['status']} → {felder['status']}", user["email"]))
            neu_partner = None
            if felder.get("vertriebspartner_id"):
                cur.execute("SELECT vertriebspartner_id FROM leads WHERE id=%s", (lid,))
                alt_p = cur.fetchone()
                if alt_p and str(alt_p["vertriebspartner_id"] or "") != str(felder["vertriebspartner_id"]):
                    neu_partner = felder["vertriebspartner_id"]
            felder_setzen(cur, "leads", lid, felder)
            audit(cur, user, "lead_geaendert", None, {"id": lid, "felder": list(felder)})
            ids_p = push.partner(cur, neu_partner) if neu_partner else []
    except DB_FEHLER as e:
        raise fehler_db(e)
    if ids_p:
        push.senden(ids_p, "Neuer Lead für dich", "Ein Lead wurde dir zugewiesen.", "/vertrieb#lead/" + lid, "zugewiesen")
    return {"ok": True}


class AktIn(BaseModel):
    art: str = "notiz"
    inhalt: str = Field(min_length=1, max_length=2000)


class KontaktIn(BaseModel):
    ergebnis: str
    notiz: str | None = Field(default=None, max_length=1500)
    wiedervorlage: date | None = None
    verlust_grund: str | None = None


@router.post("/leads/{lid}/kontakt")
def lead_kontakt(lid: str, data: KontaktIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            r = leadkontakt.erfassen(cur, lid, data.ergebnis, data.notiz, data.wiedervorlage, user["email"], verlust_grund=data.verlust_grund)
            audit(cur, user, "lead_kontakt", None, {"id": lid, "ergebnis": data.ergebnis})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    return r


@router.delete("/leads/{lid}")
def lead_loeschen(lid: str, user: dict = Depends(require_admin)):
    """Löscht den Lead samt Verlauf und Website-Check-Ergebnissen. Ein bereits angelegter Kunde bleibt bestehen."""
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM leads WHERE id=%s RETURNING firma", (lid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Lead nicht gefunden.")
            audit(cur, user, "lead_geloescht", None, {"id": lid, "firma": r["firma"]})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    return {"ok": True}


@router.post("/leads/{lid}/aktivitaet")
def lead_aktivitaet(lid: str, data: AktIn, user: dict = Depends(require_admin)):
    if data.art not in AKT_ART:
        raise HTTPException(400, "Unbekannte Art.")
    try:
        with tx("admin") as cur:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s) RETURNING id", (lid, data.art, data.inhalt, user["email"]))
            r = cur.fetchone()
    except DB_FEHLER as e:
        raise fehler_db(e)
    return r


class ZuKundeIn(BaseModel):
    paket_code: str | None = None
    beginn: date | None = None
    einladen: bool = False
    rabatt_cent: int = Field(default=0, ge=0)


@router.get("/leads/{lid}/zu-kunde-vorschlag")
def zu_kunde_vorschlag(lid: str, user: dict = Depends(require_admin)):
    """Vorbelegung für den Assistenten „Kunde und Buchung aus Angebot“: Paket aus dem angenommenen Angebot oder der Angebotsanfrage."""
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, firma, email, ansprechpartner, kunden_id, status FROM leads WHERE id=%s", (lid,))
            l = cur.fetchone()
            if not l:
                raise HTTPException(404, "Lead nicht gefunden.")
            cur.execute("SELECT id, nummer, status, positionen, brutto_cent FROM belege WHERE lead_id=%s AND art='angebot' AND status='angenommen' ORDER BY angenommen_am DESC NULLS LAST LIMIT 1", (lid,))
            ang = cur.fetchone()
            cur.execute("SELECT code, name, kategorie FROM produkte WHERE aktiv ORDER BY kategorie, name")
            pakete = cur.fetchall()
            vorschlag = None
            if ang:
                text = json.dumps(ang["positionen"], ensure_ascii=False).lower()
                for p in sorted(pakete, key=lambda x: -len(x["name"])):
                    if p["name"].lower() in text:
                        vorschlag = p["code"]; break
            if not vorschlag:
                cur.execute("SELECT paket_code FROM angebotsanfragen WHERE lead_id=%s AND paket_code IS NOT NULL ORDER BY erstellt_am DESC LIMIT 1", (lid,))
                r = cur.fetchone()
                vorschlag = r and r["paket_code"]
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    return {"lead": l, "angebot": ang and {"nummer": ang["nummer"], "brutto_cent": int(ang["brutto_cent"])}, "vorschlag": vorschlag, "pakete": pakete}


@router.post("/leads/{lid}/zu-kunde")
def lead_zu_kunde(lid: str, data: ZuKundeIn | None = None, user: dict = Depends(require_admin)):
    """Macht aus dem Lead einen Kunden (Status Onboarding), übernimmt den Vertriebler und legt auf Wunsch Paket, Buchung und Einladung gleich mit an."""
    data = data or ZuKundeIn()
    with tx("admin") as cur:
        cur.execute("SELECT * FROM leads WHERE id=%s", (lid,))
        l = cur.fetchone()
        if not l:
            raise HTTPException(404, "Lead nicht gefunden.")
        if l["kunden_id"]:
            raise HTTPException(409, "Aus diesem Lead ist schon ein Kunde geworden.")
        if l["status"] in ("gesperrt", "consent_ausstehend"):
            raise HTTPException(400, "Dieser Lead ist gesperrt oder wartet auf Einwilligung.")
        if data.einladen and not (l["email"] or "").strip():
            raise HTTPException(400, "Zum Einladen braucht der Lead eine E-Mail-Adresse.")
        if data.paket_code:
            cur.execute("SELECT 1 FROM produkte WHERE code=%s AND aktiv", (data.paket_code,))
            if not cur.fetchone():
                raise HTTPException(400, "Unbekanntes Paket.")
        cur.execute("""INSERT INTO kunden (firma, ansprechpartner, email, telefon, branche, plz, ort, domain, vertriebspartner_id, status, paket_code)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,%s,'onboarding',%s) RETURNING id, kundennummer""",
                    (l["firma"], l["ansprechpartner"], l["email"], l["telefon"], l["branche"], l["plz"], l["ort"], l["vertriebspartner_id"], data.paket_code or None))
        k = cur.fetchone()
        cur.execute("UPDATE leads SET kunden_id=%s, status='gewonnen', wiedervorlage_am=NULL WHERE id=%s", (k["id"], lid))
        cur.execute("UPDATE belege SET kunden_id=%s WHERE lead_id=%s AND kunden_id IS NULL", (k["id"], lid))   # Angebote an den Lead wandern zum Kunden
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)", (lid, "Zum Kunden gemacht: " + k["kundennummer"], user["email"]))
        if data.paket_code:
            cur.execute("""INSERT INTO kunden_module (kunden_id, modul_code, aktiv) SELECT %s, modul_code, true FROM produkt_module WHERE produkt_code=%s
                           ON CONFLICT (kunden_id, modul_code) DO UPDATE SET aktiv=true, geaendert_am=now()""", (k["id"], data.paket_code))
        onboarding.anlegen(cur, k["id"])
        link = zugang.link_erzeugen(cur, l["email"].strip(), l["ansprechpartner"], "kunde", kunden_id=k["id"]) if data.einladen else None
        audit(cur, user, "lead_zu_kunde", k["id"], {"lead": lid, "paket": data.paket_code})
    buchung_id = None
    if data.paket_code:
        from .routes_admin import BuchungIn, buchung_neu
        b = buchung_neu(str(k["id"]), BuchungIn(produkt_code=data.paket_code, beginn=data.beginn, rabatt_cent=data.rabatt_cent, rabatt_grund="Aus Angebot" if data.rabatt_cent else None), user)
        buchung_id = b["id"]
    mail = zugang.per_mail(l["email"].strip(), l["ansprechpartner"], link, "kunde") if link else None
    return {**k, "buchung_id": buchung_id, "einladungslink": link, "mail": mail}


# ================================================================= Preise und Konditionen
class PreisIn(BaseModel):
    produkt_code: str
    gueltig_ab: date
    einrichtung_cent: int | None = Field(default=None, ge=0)
    monatlich_cent: int | None = Field(default=None, ge=0)
    projekt_cent: int | None = Field(default=None, ge=0)
    ab_preis: bool = False


@router.get("/preise")
def preise(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT * FROM v_preise_aktuell ORDER BY kategorie, code")
        aktuell = cur.fetchall()
        cur.execute("SELECT id, produkt_code, gueltig_ab, einrichtung_cent, monatlich_cent, projekt_cent, ab_preis, freigegeben_von FROM produkt_preise ORDER BY gueltig_ab DESC, produkt_code LIMIT 200")
        verlauf = cur.fetchall()
        cur.execute("SELECT schluessel, wert_text, wert_zahl, beschreibung FROM konditionen ORDER BY schluessel")
        konditionen = cur.fetchall()
        cur.execute("SELECT id, name, von_monat, bis_monat, prozent, art, status, gueltig_ab FROM provisionsregeln ORDER BY art, von_monat")
        regeln = cur.fetchall()
    return {"aktuell": aktuell, "verlauf": verlauf, "konditionen": konditionen, "provisionsregeln": regeln}


@router.post("/preise")
def preis_neu(data: PreisIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("""INSERT INTO produkt_preise (produkt_code, gueltig_ab, einrichtung_cent, monatlich_cent, projekt_cent, ab_preis, quelle, freigegeben_von)
                           VALUES (%s,%s,%s,%s,%s,%s,'admin-portal',%s)""",
                        (data.produkt_code, data.gueltig_ab, data.einrichtung_cent, data.monatlich_cent, data.projekt_cent, data.ab_preis, user["email"]))
            audit(cur, user, "preis_neu", None, {"produkt": data.produkt_code, "ab": str(data.gueltig_ab)})
    except errors.UniqueViolation:
        raise HTTPException(409, "Für dieses Produkt gibt es zu diesem Datum schon einen Preis.")
    except DB_FEHLER as e:
        raise fehler_db(e)
    return {"ok": True}


class KondIn(BaseModel):
    wert_text: str | None = Field(default=None, max_length=500)
    wert_zahl: int | None = None


@router.put("/konditionen/{schluessel}")
def kondition(schluessel: str, data: KondIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE konditionen SET wert_text=%s, wert_zahl=%s, geaendert_am=now() WHERE schluessel=%s", (data.wert_text, data.wert_zahl, schluessel))
        if cur.rowcount == 0:
            raise HTTPException(404, "Unbekannte Kondition.")
        audit(cur, user, "kondition_geaendert", None, {"schluessel": schluessel})
    return {"ok": True}


@router.post("/provisionsregeln/{rid}/freigeben")
def regel_freigeben(rid: int, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE provisionsregeln SET status='freigegeben', gueltig_ab=coalesce(gueltig_ab, current_date) WHERE id=%s AND status='entwurf'", (rid,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Regel nicht gefunden oder schon freigegeben.")
        audit(cur, user, "provisionsregel_freigegeben", None, {"id": rid})
    return {"ok": True}


# ================================================================= Datenschutz und Qualität
# Tabelle -> (Statusspalte, erlaubte Werte, Zusatzfelder beim Setzen)
ENTSCHEIDUNG = {
    "auskunftsanfragen": ("status", ("offen", "in_bearbeitung", "erledigt", "abgelehnt")),
    "freigaben": ("status", ("offen", "freigegeben", "abgelehnt")),
    "aenderungsfreigaben": ("status", ("offen", "freigegeben", "abgelehnt", "zurueckgezogen")),
    "befunde": ("status", ("offen", "in_arbeit", "behoben", "verifiziert", "ausnahme")),
    "massnahmen": ("status", ("geplant", "in_arbeit", "umgesetzt", "verifiziert", "verworfen")),
}


@router.get("/compliance")
def compliance(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        def q(s):
            cur.execute(s)
            return cur.fetchall()
        return {
            "auskunft": q("SELECT id, person_ref, art, eingang_am, frist_bis, status, notiz FROM auskunftsanfragen WHERE status IN ('offen','in_bearbeitung') ORDER BY frist_bis NULLS LAST LIMIT 100"),
            "freigaben": q("SELECT f.id, k.kundennummer, f.art, f.vorschau, f.status, f.erstellt_am FROM freigaben f LEFT JOIN kunden k ON k.id=f.kunden_id WHERE f.status='offen' ORDER BY f.erstellt_am LIMIT 100"),
            "aenderungen": q("SELECT id, gegenstand, beschreibung, art, beantragt_von, beantragt_am, status FROM aenderungsfreigaben WHERE status='offen' ORDER BY beantragt_am LIMIT 100"),
            "alarme": q("SELECT id, zeit, stufe, quelle, titel, details->'erklaerung'->>'ursache' AS ursache, details->'erklaerung'->'schritte'->>0 AS tipp, details->>'fehler_nr' AS fehler_nr FROM alarme WHERE bestaetigt_am IS NULL ORDER BY zeit DESC LIMIT 100"),
            "workflow_fehler": q("SELECT id, zeit, workflow_name, knoten, left(fehlertext, 300) AS fehlertext FROM workflow_fehler WHERE NOT behoben ORDER BY zeit DESC LIMIT 100"),
            "befunde": q("SELECT id, titel, schwere, status, regel_code, gefunden_am FROM befunde WHERE status IN ('offen','in_arbeit') ORDER BY (schwere='kritisch') DESC, gefunden_am DESC LIMIT 100"),
            "massnahmen": q("SELECT id, beschreibung, verantwortlich, faellig_am, status FROM massnahmen WHERE status IN ('geplant','in_arbeit') ORDER BY faellig_am NULLS LAST LIMIT 100"),
        }


class EntscheidIn(BaseModel):
    status: str
    begruendung: str | None = Field(default=None, max_length=1000)


@router.post("/compliance/{tabelle}/{rid}")
def entscheiden(tabelle: str, rid: str, data: EntscheidIn, user: dict = Depends(require_admin)):
    if tabelle not in ENTSCHEIDUNG or data.status not in ENTSCHEIDUNG[tabelle][1]:
        raise HTTPException(400, "Unbekannte Aktion.")
    extra = {}
    if tabelle in ("freigaben", "aenderungsfreigaben"):
        extra = {"entschieden_von": user["email"], "entschieden_am": "now"}
        if data.begruendung:
            extra["begruendung"] = data.begruendung
    if tabelle == "auskunftsanfragen" and data.status in ("erledigt", "abgelehnt"):
        extra = {"erledigt_am": "now"}
    try:
        with tx("admin") as cur:
            sets = [sql.SQL("{}=%s").format(sql.Identifier("status"))]
            werte = [data.status]
            for k, v in extra.items():
                if v == "now":
                    sets.append(sql.SQL("{}=now()").format(sql.Identifier(k)))
                else:
                    sets.append(sql.SQL("{}=%s").format(sql.Identifier(k)))
                    werte.append(v)
            cur.execute(sql.SQL("UPDATE {} SET {} WHERE id=%s").format(sql.Identifier(tabelle), sql.SQL(", ").join(sets)), (*werte, rid))
            if cur.rowcount == 0:
                raise HTTPException(404, "Nicht gefunden.")
            audit(cur, user, "compliance_entscheidung", None, {"tabelle": tabelle, "id": rid, "status": data.status})
    except DB_FEHLER as e:
        raise fehler_db(e)
    return {"ok": True}


@router.post("/alarme/{aid}/bestaetigen")
def alarm_bestaetigen(aid: int, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE alarme SET bestaetigt_von=%s, bestaetigt_am=now() WHERE id=%s AND bestaetigt_am IS NULL", (user["email"], aid))
        if cur.rowcount == 0:
            raise HTTPException(404, "Alarm nicht gefunden.")
    return {"ok": True}


@router.post("/workflow-fehler/{fid}/behoben")
def fehler_behoben(fid: int, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE workflow_fehler SET behoben=true WHERE id=%s", (fid,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Eintrag nicht gefunden.")
    return {"ok": True}


# ================================================================= Vertriebler-Zugang und Provisionsberechnung
class PartnerEinladungIn(BaseModel):
    email: str
    per_mail: bool = True


@router.post("/vertrieb/partner/{pid}/einladung")
def partner_einladung(pid: str, data: PartnerEinladungIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT name, status FROM vertriebspartner WHERE id=%s", (pid,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(404, "Vertriebler nicht gefunden.")
            if p["status"] in ("beendet",):
                raise HTTPException(400, "Dieser Vertriebler ist beendet.")
            link = zugang.link_erzeugen(cur, data.email, p["name"], "vertrieb", partner_id=pid)
            audit(cur, user, "partner_einladung", None, {"partner": pid})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Vertriebler nicht gefunden.")
    mail = zugang.per_mail(data.email, p["name"], link, "vertrieb") if data.per_mail else None
    return {"einladungslink": link, "gueltig_tage": config.INVITE_DAYS, "mail": mail}


@router.post("/vertrieb/zugang/{bid}/aktiv")
def partner_zugang_aktiv(bid: str, data: dict, user: dict = Depends(require_admin)):
    aktiv = bool(data.get("aktiv"))
    with tx("admin") as cur:
        cur.execute("UPDATE benutzer SET aktiv=%s, gesperrt_manuell=%s WHERE id=%s AND rolle='vertrieb'", (aktiv, not aktiv, bid))
        if cur.rowcount == 0:
            raise HTTPException(404, "Zugang nicht gefunden.")
        if not aktiv:
            cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s", (bid,))
        audit(cur, user, "partner_zugang_aktiv", None, {"aktiv": aktiv})
    return {"ok": True}


class BerechnenIn(BaseModel):
    monat: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    vorschau: bool = True


BERECHNUNG = """
WITH m AS (SELECT %(m)s::date AS tag),
basis AS (
  SELECT v.id AS pid, v.name AS partner, k.id AS kunden_id, k.kundennummer, k.firma, b.id AS buchung_id,
         ((extract(year FROM m.tag) - extract(year FROM b.beginn)) * 12 + extract(month FROM m.tag) - extract(month FROM b.beginn))::int + 1 AS vm,
         (b.monatlich_cent - b.rabatt_cent) AS basis_cent
  FROM m, buchungen b JOIN kunden k ON k.id = b.kunden_id JOIN vertriebspartner v ON v.id = k.vertriebspartner_id
  WHERE (v.status = 'aktiv' OR (v.status = 'beendet' AND v.beendet_am IS NOT NULL AND m.tag <= v.beendet_am + make_interval(months => %(nachlauf)s))) AND NOT k.referenzkunde AND b.status = 'aktiv' AND b.beginn IS NOT NULL AND b.monatlich_cent > 0
    AND b.beginn < (m.tag + interval '1 month') AND (b.ende IS NULL OR b.ende >= m.tag)
)
SELECT basis.*, r.id AS regel_id, r.prozent, round(basis.basis_cent * r.prozent / 100)::bigint AS betrag_cent
FROM basis JOIN provisionsregeln r ON r.art = 'laufend' AND r.status = 'freigegeben'
     AND basis.vm >= r.von_monat AND (r.bis_monat IS NULL OR basis.vm <= r.bis_monat)
WHERE basis.vm >= 1 AND basis.basis_cent > 0
ORDER BY basis.partner, basis.kundennummer
"""


@router.post("/vertrieb/provisionen/berechnen")
def provisionen_berechnen(data: BerechnenIn, user: dict = Depends(require_admin)):
    monat = data.monat + "-01"
    with tx("admin") as cur:
        cur.execute("SELECT count(*) AS n FROM provisionsregeln WHERE art='laufend' AND status='freigegeben'")
        if cur.fetchone()["n"] == 0:
            raise HTTPException(400, "Es gibt noch keine freigegebene Provisionsregel. Bitte zuerst unter Preise & Konditionen freigeben.")
        cur.execute("SELECT wert FROM konfiguration WHERE schluessel='provision.nachlauf_monate' ORDER BY version DESC LIMIT 1")
        nl = cur.fetchone()
        try:
            nachlauf = int(str(nl["wert"]).strip('"')) if nl else 6
        except ValueError:
            nachlauf = 6
        cur.execute(BERECHNUNG, {"m": monat, "nachlauf": nachlauf})
        zeilen = cur.fetchall()
        if data.vorschau:
            cur.execute("""SELECT count(*) AS n FROM provisionen WHERE monat=%s""", (monat,))
            return {"vorschau": True, "zeilen": zeilen, "schon_vorhanden": cur.fetchone()["n"]}
        neu = 0
        for z in zeilen:
            cur.execute("""INSERT INTO provisionen (vertriebspartner_id, kunden_id, buchung_id, regel_id, monat, vertragsmonat, basis_cent, prozent, betrag_cent)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertriebspartner_id, buchung_id, monat, art) DO NOTHING""",
                        (z["pid"], z["kunden_id"], z["buchung_id"], z["regel_id"], monat, z["vm"], z["basis_cent"], z["prozent"], z["betrag_cent"]))
            neu += cur.rowcount
        audit(cur, user, "provisionen_berechnet", None, {"monat": data.monat, "neu": neu})
    return {"vorschau": False, "angelegt": neu, "uebersprungen": len(zeilen) - neu}
