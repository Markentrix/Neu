"""Portal für Vertriebler: nur eigene Kunden, eigene Leads, eigene Provisionen.
Die Abfragen laufen im Systemkontext, deshalb steht JEDE Abfrage ausdrücklich auf die eigene Vertriebler-ID."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

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
        cur.execute("""SELECT pr.id, pr.monat, k.kundennummer, k.firma, pr.vertragsmonat, pr.basis_cent, pr.prozent, pr.betrag_cent, pr.status
                       FROM provisionen pr JOIN kunden k ON k.id=pr.kunden_id
                       WHERE pr.vertriebspartner_id=%s ORDER BY pr.monat DESC, k.kundennummer LIMIT 500""", (user["vertriebspartner_id"],))
        return cur.fetchall()


@router.get("/leads")
def leads(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("""SELECT id, firma, ansprechpartner, ort, branche, status, erstellt_am FROM leads
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


@router.post("/leads")
def lead_neu(data: LeadIn, user: dict = Depends(require_vertrieb)):
    d = data.model_dump()
    d["pid"] = user["vertriebspartner_id"]
    with tx("system") as cur:
        cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, branche, plz, ort, quelle, vertriebspartner_id, notiz)
                       VALUES (%(firma)s,%(ansprechpartner)s,%(email)s,%(telefon)s,%(website)s,%(branche)s,%(plz)s,%(ort)s,'empfehlung',%(pid)s,%(notiz)s) RETURNING id""", d)
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
    for k in ("score", "loeschen_nach", "kunden_id", "vertriebspartner_id"):
        l.pop(k, None)
    return {"lead": l, "aktivitaeten": akt}


class StatusIn(BaseModel):
    status: str


@router.post("/leads/{lid}/status")
def lead_status(lid: str, data: StatusIn, user: dict = Depends(require_vertrieb)):
    if data.status not in LEAD_STATUS_ERLAUBT:
        raise HTTPException(400, "Dieser Status kann nur Markentrix setzen.")
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if l["status"] in ("gewonnen", "gesperrt", "consent_ausstehend"):
            raise HTTPException(400, "Dieser Lead kann nur Markentrix ändern.")
        if l["status"] != data.status:
            cur.execute("UPDATE leads SET status=%s WHERE id=%s", (data.status, lid))
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


class PasswortIn(BaseModel):
    alt: str
    neu: str


@router.post("/passwort")
def passwort(data: PasswortIn, user: dict = Depends(require_vertrieb)):
    check_password_rules(data.neu)
    with tx("system") as cur:
        cur.execute("SELECT passwort_hash FROM benutzer WHERE id=%s", (user["id"],))
        if not verify_password(data.alt, cur.fetchone()["passwort_hash"]):
            raise HTTPException(400, "Das aktuelle Passwort stimmt nicht.")
        cur.execute("UPDATE benutzer SET passwort_hash=%s WHERE id=%s", (hash_password(data.neu), user["id"]))
        audit(cur, user, "passwort_geaendert")
    return {"ok": True}
