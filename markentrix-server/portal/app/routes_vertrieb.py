"""Portal für Vertriebler: nur eigene Kunden, eigene Leads, eigene Provisionen.
Die Abfragen laufen im Systemkontext, deshalb steht JEDE Abfrage ausdrücklich auf die eigene Vertriebler-ID."""
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg import errors
from pydantic import BaseModel, Field

from datetime import date

from . import leadkontakt, leadpruefung
from .db import tx
from .security import audit, check_password_rules, hash_password, require_vertrieb, verify_password

router = APIRouter(prefix="/api/vertrieb")

LEAD_STATUS_ERLAUBT = ("neu", "kontaktiert", "antwort", "termin", "angebot", "verloren")
AKT_ART = ("notiz", "anruf", "mail_gesendet", "antwort", "termin")


@router.get("/start")
def start(user: dict = Depends(require_vertrieb)):
    pid = user["vertriebspartner_id"]
    with tx("system") as cur:
        cur.execute("SELECT name, firma, status FROM vertriebspartner WHERE id=%s", (pid,))
        partner = cur.fetchone()
        cur.execute("""SELECT k.kundennummer, k.firma, k.status, p.name AS paket, k.erstellt_am
                       FROM kunden k LEFT JOIN produkte p ON p.code=k.paket_code WHERE k.vertriebspartner_id=%s ORDER BY k.kundennummer DESC""", (pid,))
        kunden = cur.fetchall()
        cur.execute("""SELECT
              coalesce(sum(betrag_cent) FILTER (WHERE status IN ('berechnet','freigegeben')),0) AS offen_cent,
              coalesce(sum(betrag_cent) FILTER (WHERE status='ausgezahlt' AND monat >= date_trunc('year', current_date)),0) AS ausgezahlt_jahr_cent,
              coalesce(sum(betrag_cent) FILTER (WHERE monat = date_trunc('month', current_date) AND status<>'storniert'),0) AS dieser_monat_cent
              FROM provisionen WHERE vertriebspartner_id=%s""", (pid,))
        summen = cur.fetchone()
        cur.execute("SELECT status, count(*) AS n FROM leads WHERE vertriebspartner_id=%s GROUP BY status", (pid,))
        leads = {r["status"]: r["n"] for r in cur.fetchall()}
    return {"partner": partner, "kunden": kunden, "summen": summen, "leads": leads}


@router.get("/provisionen")
def provisionen(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("""SELECT pr.id, pr.art, pr.monat, k.kundennummer, k.firma, pr.vertragsmonat, pr.basis_cent, pr.prozent, pr.betrag_cent, pr.status
                       FROM provisionen pr JOIN kunden k ON k.id=pr.kunden_id
                       WHERE pr.vertriebspartner_id=%s ORDER BY pr.monat DESC, k.kundennummer LIMIT 500""", (user["vertriebspartner_id"],))
        return cur.fetchall()


@router.get("/leads")
def leads(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("""SELECT id, firma, ansprechpartner, ort, branche, status, wiedervorlage_am, letzter_kontakt_am, temperatur, erstellt_am FROM leads
                       WHERE vertriebspartner_id=%s ORDER BY erstellt_am DESC LIMIT 300""", (user["vertriebspartner_id"],))
        return cur.fetchall()


class LeadIn(BaseModel):
    firma: str = Field(min_length=1, max_length=200)
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=253)
    branche: str | None = Field(default=None, max_length=120)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=120)
    notiz: str | None = Field(default=None, max_length=2000)
    ansprache_grundlage: str | None = None
    ansprache_hinweis: str | None = Field(default=None, max_length=300)


GRUNDLAGEN = ("einwilligung", "b2b_mutmasslich", "empfehlung", "bestandskontakt")


@router.post("/leads")
def lead_neu(data: LeadIn, user: dict = Depends(require_vertrieb)):
    d = data.model_dump()
    if d["ansprache_grundlage"] not in (None, "") + GRUNDLAGEN:
        raise HTTPException(400, "Ungültige Grundlage der Ansprache.")
    d["ansprache_grundlage"] = d["ansprache_grundlage"] or None
    d["pid"] = user["vertriebspartner_id"]
    with tx("system") as cur:
        leadpruefung.pruefen(cur, d, eigener_partner=user["vertriebspartner_id"])
        cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, branche, plz, ort, quelle, vertriebspartner_id, notiz, ansprache_grundlage, ansprache_hinweis)
                       VALUES (%(firma)s,%(ansprechpartner)s,%(email)s,%(telefon)s,%(website)s,%(branche)s,%(plz)s,%(ort)s,'empfehlung',%(pid)s,%(notiz)s,%(ansprache_grundlage)s,%(ansprache_hinweis)s) RETURNING id""", d)
        r = cur.fetchone()
        audit(cur, user, "lead_angelegt_vertrieb", None, {"firma": data.firma})
    return r


def eigener_lead(cur, lid, pid):
    try:
        cur.execute("SELECT * FROM leads WHERE id=%s AND vertriebspartner_id=%s", (lid, pid))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")
    l = cur.fetchone()
    if not l:
        raise HTTPException(404, "Lead nicht gefunden.")
    return l


@router.get("/leads/{lid}")
def lead_detail(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        cur.execute("SELECT art, inhalt, zeit, von FROM lead_aktivitaeten WHERE lead_id=%s ORDER BY zeit DESC LIMIT 200", (lid,))
        akt = cur.fetchall()
        cur.execute("SELECT website, ergebnis, erstellt_am FROM lead_checks WHERE lead_id=%s ORDER BY erstellt_am DESC LIMIT 1", (lid,))
        check = cur.fetchone()
    for k in ("score", "loeschen_nach", "kunden_id", "vertriebspartner_id"):
        l.pop(k, None)
    return {"lead": l, "aktivitaeten": akt, "check": check, "kontakt_optionen": leadkontakt.optionen_fuer_oberflaeche(), "verlustgruende": leadkontakt.VERLUSTGRUENDE}


class LeadPatchIn(BaseModel):
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=253)
    ort: str | None = Field(default=None, max_length=120)
    ansprache_grundlage: str | None = None
    ansprache_hinweis: str | None = Field(default=None, max_length=300)


@router.patch("/leads/{lid}")
def lead_aendern(lid: str, data: LeadPatchIn, user: dict = Depends(require_vertrieb)):
    """Kontaktdaten ergänzen oder korrigieren (z. B. richtige Mail oder Ansprechpartner aus dem Gespräch). Wird im Verlauf festgehalten."""
    felder = {k: (v.strip() or None) for k, v in data.model_dump().items() if v is not None}
    if not felder:
        raise HTTPException(400, "Nichts zu ändern.")
    if felder.get("ansprache_grundlage") not in (None,) + GRUNDLAGEN:
        raise HTTPException(400, "Ungültige Grundlage der Ansprache.")
    if felder.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", felder["email"]):
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse eintragen.")
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if l["status"] in ("gewonnen", "gesperrt", "consent_ausstehend"):
            raise HTTPException(400, "Dieser Lead kann nur Markentrix ändern.")
        neu = {**l, **felder}
        if any(k in felder for k in ("email", "telefon", "website")):
            leadpruefung.pruefen(cur, neu, eigener_partner=user["vertriebspartner_id"], trotzdem=True)
            x = leadpruefung.dublette(cur, felder.get("email"), felder.get("telefon"), None, None, ausser=lid) if (felder.get("email") or felder.get("telefon")) else None
            if x and x["art"] == "kunde":
                raise HTTPException(409, f"„{x['firma']}“ ist bereits Kunde bei Markentrix.")
        sets = ", ".join(f"{k}=%({k})s" for k in felder)
        cur.execute(f"UPDATE leads SET {sets} WHERE id=%(id)s AND vertriebspartner_id=%(pid)s", {**felder, "id": lid, "pid": user["vertriebspartner_id"]})
        geaendert = ", ".join(k for k in felder if k not in ("ansprache_hinweis",))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)", (lid, f"Angaben ergänzt: {geaendert}", user["email"]))
    return {"ok": True}


class StatusIn(BaseModel):
    status: str
    verlust_grund: str | None = None


@router.post("/leads/{lid}/status")
def lead_status(lid: str, data: StatusIn, user: dict = Depends(require_vertrieb)):
    if data.status not in LEAD_STATUS_ERLAUBT:
        raise HTTPException(400, "Dieser Status kann nur Markentrix setzen.")
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if l["status"] in ("gewonnen", "gesperrt", "consent_ausstehend"):
            raise HTTPException(400, "Dieser Lead kann nur Markentrix ändern.")
        if l["status"] != data.status:
            if data.verlust_grund and data.verlust_grund not in leadkontakt.VERLUSTGRUENDE:
                raise HTTPException(400, "Unbekannter Grund.")
            cur.execute("UPDATE leads SET status=%s, verlust_grund=CASE WHEN %s='verloren' THEN %s ELSE verlust_grund END WHERE id=%s", (data.status, data.status, data.verlust_grund, lid))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)", (lid, f"{l['status']} → {data.status}", user["email"]))
    return {"ok": True}


class AktIn(BaseModel):
    art: str = "notiz"
    inhalt: str = Field(min_length=1, max_length=2000)


@router.post("/leads/{lid}/aktivitaet")
def lead_aktivitaet(lid: str, data: AktIn, user: dict = Depends(require_vertrieb)):
    if data.art not in AKT_ART:
        raise HTTPException(400, "Unbekannte Art.")
    with tx("system") as cur:
        eigener_lead(cur, lid, user["vertriebspartner_id"])
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s)", (lid, data.art, data.inhalt, user["email"]))
    return {"ok": True}


class KontaktIn(BaseModel):
    ergebnis: str
    notiz: str | None = Field(default=None, max_length=1500)
    wiedervorlage: date | None = None
    verlust_grund: str | None = None


@router.post("/leads/{lid}/kontakt")
def lead_kontakt(lid: str, data: KontaktIn, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        r = leadkontakt.erfassen(cur, lid, data.ergebnis, data.notiz, data.wiedervorlage, user["email"], darf_status=l["status"] not in leadkontakt.GESPERRT, verlust_grund=data.verlust_grund)
        audit(cur, user, "lead_kontakt_vertrieb", None, {"id": lid, "ergebnis": data.ergebnis})
    return r


class PasswortIn(BaseModel):
    alt: str
    neu: str


@router.post("/passwort")
def passwort(data: PasswortIn, request: Request, user: dict = Depends(require_vertrieb)):
    check_password_rules(data.neu)
    with tx("system") as cur:
        cur.execute("SELECT passwort_hash FROM benutzer WHERE id=%s", (user["id"],))
        if not verify_password(data.alt, cur.fetchone()["passwort_hash"]):
            raise HTTPException(400, "Das aktuelle Passwort stimmt nicht.")
        cur.execute("UPDATE benutzer SET passwort_hash=%s WHERE id=%s", (hash_password(data.neu), user["id"]))
        # andere Sitzungen beenden, die aktuelle bleibt
        from .security import COOKIE as _C, token_hash as _th
        _t = request.cookies.get(_C)
        cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s AND token_hash IS DISTINCT FROM %s", (user["id"], _th(_t) if _t else None))
        audit(cur, user, "passwort_geaendert")
    return {"ok": True}
