"""Provisionen: Verlängerungsbonus, Rückbuchung, Abrechnung (PDF) und Kosten pro Kunde."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import pdf, rechtstexte
from .db import tx
from .security import audit, require_admin, require_vertrieb

router = APIRouter(prefix="/api/admin")
vertrieb_router = APIRouter(prefix="/api/vertrieb")


class VerlaengerungIn(BaseModel):
    buchung_id: str
    monat: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    notiz: str | None = Field(default=None, max_length=300)


@router.post("/vertrieb/provisionen/verlaengerung")
def verlaengerung_erfassen(data: VerlaengerungIn, user: dict = Depends(require_admin)):
    """Verlängerungsbonus einmalig: Prozent der Regel x monatliche Basis x Mindestlaufzeit (Monate) der Buchung."""
    monat = data.monat + "-01"
    try:
        with tx("admin") as cur:
            cur.execute("""SELECT b.id, b.kunden_id, b.monatlich_cent - b.rabatt_cent AS basis, 12 AS laufzeit,
                                  k.vertriebspartner_id, k.referenzkunde
                           FROM buchungen b JOIN kunden k ON k.id=b.kunden_id WHERE b.id=%s""", (data.buchung_id,))
            b = cur.fetchone()
            if not b:
                raise HTTPException(404, "Buchung nicht gefunden.")
            if not b["vertriebspartner_id"] or b["referenzkunde"]:
                raise HTTPException(400, "Dieser Kunde hat keinen Vertriebler oder ist ein Referenzkunde.")
            cur.execute("SELECT id, prozent FROM provisionsregeln WHERE art='verlaengerung' AND status='freigegeben' ORDER BY id DESC LIMIT 1")
            r = cur.fetchone()
            if not r:
                raise HTTPException(400, "Es gibt noch keine freigegebene Verlängerungsregel. Bitte unter Preise & Konditionen freigeben.")
            monate = int(b["laufzeit"] or 12)
            betrag = round(int(b["basis"]) * float(r["prozent"]) / 100 * monate)
            cur.execute("""INSERT INTO provisionen (vertriebspartner_id, kunden_id, buchung_id, regel_id, monat, vertragsmonat, basis_cent, prozent, betrag_cent, art, notiz)
                           VALUES (%s,%s,%s,%s,%s,0,%s,%s,%s,'verlaengerung',%s) ON CONFLICT DO NOTHING RETURNING id""",
                        (b["vertriebspartner_id"], b["kunden_id"], b["id"], r["id"], monat, int(b["basis"]) * monate, r["prozent"], betrag, data.notiz))
            neu = cur.fetchone()
            if not neu:
                raise HTTPException(409, "Für diesen Monat ist die Verlängerung bereits erfasst.")
            audit(cur, user, "provision_verlaengerung", b["kunden_id"], {"betrag_cent": betrag})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Buchung nicht gefunden.")
    return {"ok": True, "betrag_cent": betrag}


class RueckIn(BaseModel):
    monat: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    notiz: str | None = Field(default=None, max_length=300)


@router.post("/vertrieb/provisionen/{rid}/rueckbuchung")
def rueckbuchung(rid: str, data: RueckIn, user: dict = Depends(require_admin)):
    """Bereits ausgezahlte Provision (z. B. nach Zahlungsausfall) als negative Zeile im angegebenen Monat verrechnen."""
    monat = data.monat + "-01"
    try:
        with tx("admin") as cur:
            cur.execute("SELECT * FROM provisionen WHERE id=%s", (rid,))
            o = cur.fetchone()
            if not o:
                raise HTTPException(404, "Provision nicht gefunden.")
            if o["status"] != "ausgezahlt" or o["art"] == "rueckbuchung":
                raise HTTPException(400, "Zurückgebucht werden kann nur eine bereits ausgezahlte Provision. Andere bitte einfach stornieren.")
            cur.execute("""INSERT INTO provisionen (vertriebspartner_id, kunden_id, buchung_id, regel_id, monat, vertragsmonat, basis_cent, prozent, betrag_cent, art, ursprung_id, notiz)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'rueckbuchung',%s,%s) ON CONFLICT DO NOTHING RETURNING id""",
                        (o["vertriebspartner_id"], o["kunden_id"], o["buchung_id"], o["regel_id"], monat, o["vertragsmonat"], o["basis_cent"], o["prozent"],
                         -abs(o["betrag_cent"]), o["id"], data.notiz))
            if not cur.fetchone():
                raise HTTPException(409, "Zu dieser Buchung gibt es in diesem Monat schon eine Rückbuchung.")
            audit(cur, user, "provision_rueckbuchung", o["kunden_id"], {"id": rid})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Provision nicht gefunden.")
    return {"ok": True}


def _monat(text: str) -> date:
    try:
        return date.fromisoformat(text + "-01")
    except ValueError:
        raise HTTPException(400, "Monat bitte als JJJJ-MM angeben.")


def _abrechnung(cur, pid: str, monat: date) -> bytes:
    cur.execute("SELECT name, firma, email FROM vertriebspartner WHERE id=%s", (pid,))
    v = cur.fetchone()
    if not v:
        raise HTTPException(404, "Vertriebler nicht gefunden.")
    cur.execute("""SELECT pr.art, pr.vertragsmonat, pr.basis_cent, pr.prozent, pr.betrag_cent, pr.status, k.kundennummer, k.firma
                   FROM provisionen pr JOIN kunden k ON k.id=pr.kunden_id
                   WHERE pr.vertriebspartner_id=%s AND pr.monat=%s AND pr.status<>'storniert' ORDER BY k.kundennummer, pr.art""", (pid, monat))
    zeilen = cur.fetchall()
    art_text = {"laufend": "Laufende Provision", "verlaengerung": "Verlängerungsbonus", "rueckbuchung": "Rückbuchung"}
    summe = sum(int(z["betrag_cent"]) for z in zeilen)
    f = rechtstexte.firma_system()
    kopf = ["Kunde", "Art", "Basis", "%", "Betrag"]
    daten = [[f"{z['kundennummer']} {z['firma']}", art_text.get(z["art"], z["art"]) + (f" (Monat {z['vertragsmonat']})" if z["art"] == "laufend" else ""),
              pdf.euro(z["basis_cent"]), f"{float(z['prozent']):g}", pdf.euro(z["betrag_cent"])] for z in zeilen]
    inhalt = [pdf.p(f"Provisionsabrechnung {pdf.monat_name(monat)}", pdf.H1), pdf.Spacer(1, 6),
              pdf.p(f"Für: {v['name']}" + (f", {v['firma']}" if v.get("firma") else "")), pdf.Spacer(1, 10)]
    if zeilen:
        inhalt.append(pdf.tabelle(kopf, daten, rechts_ab=2, summe=["Summe", "", "", "", pdf.euro(summe)]))
    else:
        inhalt.append(pdf.p("Für diesen Monat gibt es keine Provisionen."))
    inhalt += [pdf.Spacer(1, 12), pdf.p("Dies ist eine Provisionsabrechnung, keine Rechnung im steuerlichen Sinn. "
               "Bitte stellen Sie, falls Sie umsatzsteuerpflichtig sind, selbst eine Rechnung oder Gutschrift nach den gesetzlichen Vorgaben aus. "
               "Rückbuchungen werden mit dem Betrag des Monats verrechnet.", pdf.KLEIN)]
    return pdf.dokument(f"Provisionsabrechnung {monat:%Y-%m}", f"Provisionsabrechnung {monat:%Y-%m}", inhalt, f)


def _pdf(daten, name):
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/vertrieb/{pid}/abrechnung/{monat}")
def abrechnung_admin(pid: str, monat: str, user: dict = Depends(require_admin)):
    m = _monat(monat)
    try:
        with tx("admin") as cur:
            return _pdf(_abrechnung(cur, pid, m), f"Provisionsabrechnung-{monat}.pdf")
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")


@vertrieb_router.get("/abrechnung/{monat}")
def abrechnung_vertrieb(monat: str, user: dict = Depends(require_vertrieb)):
    m = _monat(monat)
    with tx("system") as cur:
        return _pdf(_abrechnung(cur, user["vertriebspartner_id"], m), f"Provisionsabrechnung-{monat}.pdf")


# ---------------------------------------------------------------- Kosten pro Kunde
@router.get("/kunden/{kid}/kosten")
def kosten(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("""SELECT date_trunc('month', zeit)::date AS monat, round(coalesce(sum(kosten_cent),0))::bigint AS kosten_cent,
                                  coalesce(sum(menge),0)::bigint AS tokens
                           FROM kosten_log WHERE kunden_id=%s GROUP BY 1 ORDER BY 1 DESC LIMIT 12""", (kid,))
            monate = cur.fetchall()
            cur.execute("""SELECT date_trunc('month', zeit)::date AS monat, dienst, round(coalesce(sum(kosten_cent),0))::bigint AS kosten_cent
                           FROM kosten_log WHERE kunden_id=%s GROUP BY 1,2 ORDER BY 1 DESC, 2 LIMIT 60""", (kid,))
            dienste = cur.fetchall()
            cur.execute("SELECT coalesce(sum(monatlich_cent - rabatt_cent),0) AS umsatz FROM buchungen WHERE kunden_id=%s AND status='aktiv'", (kid,))
            umsatz = int(cur.fetchone()["umsatz"])
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    return {"monate": monate, "dienste": dienste, "umsatz_monat_cent": umsatz}


class KostenIn(BaseModel):
    dienst: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_ äöüÄÖÜß.-]+$")
    betrag_eur: float = Field(gt=0, le=100000)
    notiz: str = Field(default="", max_length=200)
    datum: date | None = None


@router.post("/kunden/{kid}/kosten")
def kosten_erfassen(kid: str, data: KostenIn, user: dict = Depends(require_admin)):
    """Kosten von Hand eintragen (z. B. Telefonie, Domain, Werbebudget), damit die Marge pro Kunde stimmt."""
    dienst = data.dienst.strip().lower().replace(" ", "_")
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise HTTPException(404, "Kunde nicht gefunden.")
            cur.execute("INSERT INTO kosten_log (zeit, kunden_id, dienst, einheit, menge, kosten_cent) VALUES (COALESCE(%s::date, now()::date)::timestamptz + interval '12 hours', %s, %s, 'manuell', 0, %s)",
                        (data.datum, kid, dienst, round(data.betrag_eur * 100, 2)))
            audit(cur, user, "kosten_erfasst", kid, {"dienst": dienst, "betrag_eur": data.betrag_eur, "notiz": data.notiz})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    return {"ok": True}
