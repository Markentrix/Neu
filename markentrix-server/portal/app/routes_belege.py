import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import angebotsfluss, angebotsgrund, belege, mailer, rechtstexte, zahlungsabgleich
from .db import tx
from .security import audit, require_admin, require_inhaber

router = APIRouter(prefix="/api/admin")
kunde_router = APIRouter(prefix="/api/kunde")

FELDER = "id, art, nummer, kunden_id, lead_id, status, betreff, einleitung, schluss, positionen, leistungen, leistungszeitraum, datum, faellig_am, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer, angebot_id, storno_von, versendet_am, erinnerungen, erinnert_am, grund_code, grund_text, bezahlt_am, bezahlt_cent, mahnstufe, mahn_am, notiz, erstellt_am"
UEBERFAELLIG = "(art='rechnung' AND status IN ('gestellt','versendet') AND faellig_am < current_date)"


def _laden(cur, bid):
    try:
        cur.execute(f"SELECT {FELDER} FROM belege WHERE id=%s", (bid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Beleg nicht gefunden.")
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Beleg nicht gefunden.")
    return b


def _pdf_antwort(daten, name):
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


@router.get("/belege-export.csv")
def csv_export(von: str = "", bis: str = "", user: dict = Depends(require_admin)):
    """Rechnungen als CSV (Semikolon, deutsches Zahlenformat) für Buchhaltung/Steuerberatung, z. B. sevDesk-Import."""
    import csv, io
    try:
        with tx("admin") as cur:
            cur.execute("""SELECT b.nummer, b.datum, k.kundennummer, k.firma, b.netto_cent, b.ust_satz, b.ust_cent, b.brutto_cent, b.status, b.bezahlt_am, b.faellig_am, b.storno_von IS NOT NULL AS storno
                           FROM belege b JOIN kunden k ON k.id=b.kunden_id
                           WHERE b.art='rechnung' AND b.status<>'entwurf' AND (%s::date IS NULL OR b.datum >= %s::date) AND (%s::date IS NULL OR b.datum <= %s::date) ORDER BY b.datum, b.nummer""", (von or None, von or None, bis or None, bis or None))
            zeilen = cur.fetchall()
    except (errors.InvalidDatetimeFormat, errors.DatetimeFieldOverflow):
        raise HTTPException(400, "Datum bitte als JJJJ-MM-TT angeben.")
    eur = lambda c: f"{int(c) / 100:.2f}".replace(".", ",")
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";")
    w.writerow(["Rechnungsnummer", "Datum", "Kundennummer", "Kunde", "Netto", "USt-Satz", "USt", "Brutto", "Status", "Bezahlt am", "Fällig am", "Storno"])
    for z in zeilen:
        w.writerow([z["nummer"], z["datum"], z["kundennummer"], z["firma"], eur(z["netto_cent"]), str(z["ust_satz"]).replace(".", ","), eur(z["ust_cent"]), eur(z["brutto_cent"]),
                    z["status"], z["bezahlt_am"] or "", z["faellig_am"] or "", "ja" if z["storno"] else ""])
    return Response("\ufeff" + puffer.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="rechnungen.csv"'})


# ---------------------------------------------------------------- Liste und Übersicht
@router.get("/belege")
def liste(art: str = "", status: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute(f"""SELECT b.id, b.art, b.nummer, b.status, b.betreff, b.datum, b.faellig_am, b.brutto_cent, b.bezahlt_am, b.mahnstufe, b.storno_von,
                              b.lead_id, b.kunden_id, coalesce(k.kundennummer, 'Lead') AS kundennummer, coalesce(k.firma, l.firma) AS firma, {UEBERFAELLIG.replace('art', 'b.art').replace('status', 'b.status').replace('faellig_am', 'b.faellig_am')} AS ueberfaellig
                       FROM belege b LEFT JOIN kunden k ON k.id=b.kunden_id LEFT JOIN leads l ON l.id=b.lead_id
                       WHERE (%s='' OR b.art=%s) AND (%s='' OR b.status=%s) ORDER BY b.erstellt_am DESC LIMIT 300""", (art, art, status, status))
        zeilen = cur.fetchall()
        cur.execute(f"""SELECT coalesce(sum(brutto_cent) FILTER (WHERE art='rechnung' AND status IN ('gestellt','versendet')),0) AS offen,
                               coalesce(sum(brutto_cent) FILTER (WHERE {UEBERFAELLIG}),0) AS ueberfaellig,
                               count(*) FILTER (WHERE {UEBERFAELLIG}) AS ueberfaellig_n,
                               coalesce(sum(brutto_cent) FILTER (WHERE art='rechnung' AND status='bezahlt' AND date_trunc('month', bezahlt_am) = date_trunc('month', current_date)),0) AS bezahlt_monat
                        FROM belege""")
        summen = cur.fetchone()
    return {"belege": zeilen, "summen": {k: int(v) for k, v in summen.items()}}


@router.get("/kunden/{kid}/belege")
def kunde_belege(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(404, "Kunde nicht gefunden.")
        cur.execute(f"SELECT id, art, nummer, status, betreff, datum, faellig_am, brutto_cent, storno_von, {UEBERFAELLIG} AS ueberfaellig FROM belege WHERE kunden_id=%s ORDER BY erstellt_am DESC LIMIT 100", (kid,))
        return cur.fetchall()


@router.get("/kunden/{kid}/belege-vorlage")
def vorlage(kid: str, user: dict = Depends(require_admin)):
    """Positionsvorschlag aus den Buchungen des Kunden (Referenzkunden zahlen nichts)."""
    with tx("admin") as cur:
        cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if k["referenzkunde"]:
            return {"referenzkunde": True, "positionen": []}
        cur.execute("""SELECT p.name, b.einrichtung_cent, b.monatlich_cent, b.rabatt_cent, b.status FROM buchungen b JOIN produkte p ON p.code=b.produkt_code
                       WHERE b.kunden_id=%s AND b.status IN ('beauftragt','in_einrichtung','aktiv') ORDER BY b.erstellt_am""", (kid,))
        pos = []
        for b in cur.fetchall():
            if b["einrichtung_cent"]:
                pos.append({"text": f"Einrichtung {b['name']}", "menge": 1, "einheit": "", "preis_cent": int(b["einrichtung_cent"])})
            if b["monatlich_cent"]:
                pos.append({"text": f"{b['name']} – monatlich", "menge": 1, "einheit": "Monat", "preis_cent": int(b["monatlich_cent"] - (b["rabatt_cent"] or 0))})
    return {"referenzkunde": False, "positionen": pos}


# ---------------------------------------------------------------- Anlegen und Bearbeiten
class BelegIn(BaseModel):
    art: str = Field(pattern="^(angebot|rechnung)$")
    betreff: str = Field(default="", max_length=200)
    einleitung: str = Field(default="", max_length=3000)
    schluss: str = Field(default="", max_length=3000)
    leistungszeitraum: str = Field(default="", max_length=100)
    positionen: list[dict] = []
    leistungen: list[str] = Field(default=[], max_length=60)
    angebot_id: str | None = None


class BelegPut(BaseModel):
    betreff: str = Field(default="", max_length=200)
    einleitung: str = Field(default="", max_length=3000)
    schluss: str = Field(default="", max_length=3000)
    leistungszeitraum: str = Field(default="", max_length=100)
    positionen: list[dict] = []
    leistungen: list[str] = Field(default=[], max_length=60)
    notiz: str | None = Field(default=None, max_length=2000)


@router.post("/kunden/{kid}/belege")
def anlegen(kid: str, data: BelegIn, user: dict = Depends(require_admin)):
    pos = belege.positionen_pruefen(data.positionen)
    with tx("admin") as cur:
        try:
            cur.execute("SELECT referenzkunde, status FROM kunden WHERE id=%s", (kid,))
        except errors.InvalidTextRepresentation:
            raise HTTPException(404, "Kunde nicht gefunden.")
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        if k["referenzkunde"] and data.art == "rechnung":
            raise HTTPException(400, "Referenzkunden bekommen keine Rechnung.")
        f = rechtstexte.firma(cur)
        s = belege.summen(pos, f["mwst_satz"], f["kleinunternehmer"])
        cur.execute("""INSERT INTO belege (art, kunden_id, betreff, einleitung, schluss, positionen, leistungen, leistungszeitraum, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer, angebot_id)
                       VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (data.art, kid, data.betreff, data.einleitung, data.schluss, json.dumps(pos), json.dumps([x.strip()[:300] for x in data.leistungen if x.strip()]), data.leistungszeitraum, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], data.angebot_id))
        bid = cur.fetchone()["id"]
        audit(cur, user, "beleg_angelegt", kid, {"art": data.art})
    return {"id": bid}


@router.get("/belege/{bid}")
def detail(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        cur.execute("SELECT kundennummer, firma, email, referenzkunde FROM kunden WHERE id=%s", (b["kunden_id"],))
        k = cur.fetchone()
    return {"beleg": b, "kunde": k}


@router.put("/belege/{bid}")
def aendern(bid: str, data: BelegPut, user: dict = Depends(require_admin)):
    pos = belege.positionen_pruefen(data.positionen)
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["status"] != "entwurf":
            raise HTTPException(400, "Ausgestellte Belege werden nicht mehr geändert. Bitte stornieren und neu erstellen.")
        f = rechtstexte.firma(cur)
        s = belege.summen(pos, f["mwst_satz"], f["kleinunternehmer"])
        cur.execute("""UPDATE belege SET betreff=%s, einleitung=%s, schluss=%s, leistungszeitraum=%s, positionen=%s::jsonb, leistungen=%s::jsonb, notiz=coalesce(%s,notiz),
                              netto_cent=%s, ust_satz=%s, ust_cent=%s, brutto_cent=%s, kleinunternehmer=%s, geaendert_am=now() WHERE id=%s""",
                    (data.betreff, data.einleitung, data.schluss, data.leistungszeitraum, json.dumps(pos), json.dumps([x.strip()[:300] for x in data.leistungen if x.strip()]), data.notiz, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], bid))
        audit(cur, user, "beleg_geaendert", b["kunden_id"], {"beleg": bid})
    return {"ok": True}


@router.delete("/belege/{bid}")
def loeschen(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["status"] != "entwurf" or b["nummer"]:
            raise HTTPException(400, "Nur Entwürfe können gelöscht werden. Ausgestellte Rechnungen bitte stornieren.")
        cur.execute("DELETE FROM belege WHERE id=%s", (bid,))
        audit(cur, user, "beleg_geloescht", b["kunden_id"], {"art": b["art"]})
    return {"ok": True}


# ---------------------------------------------------------------- Ausstellen, Senden, Zahlung, Mahnung, Storno
class AusstellenIn(BaseModel):
    gueltig_tage: int = Field(default=30, ge=1, le=365)


@router.post("/belege/{bid}/ausstellen")
def ausstellen(bid: str, data: AusstellenIn | None = None, user: dict = Depends(require_admin)):
    data = data or AusstellenIn()
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if not b["kunden_id"]:
            raise HTTPException(400, "Dieses Angebot gehört zu einem Lead. Bitte im Lead auf „Angebot senden“ gehen.")
        if b["status"] != "entwurf":
            raise HTTPException(400, "Dieser Beleg ist schon ausgestellt.")
        if not b["positionen"]:
            raise HTTPException(400, "Bitte mindestens eine Position eintragen.")
        f = rechtstexte.firma(cur)
        if b["art"] == "rechnung":
            belege.firmendaten_pruefen(f)
            cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (b["kunden_id"],))
            if cur.fetchone()["referenzkunde"]:
                raise HTTPException(400, "Referenzkunden bekommen keine Rechnung.")
            if b["brutto_cent"] <= 0:
                raise HTTPException(400, "Eine Rechnung braucht einen Betrag größer 0.")
        elif not (f["name"] and f["strasse"]):
            raise HTTPException(400, "Bitte zuerst unter Einstellungen → Firmendaten Name und Anschrift eintragen.")
        s = belege.summen(b["positionen"], f["mwst_satz"], f["kleinunternehmer"])
        prefix = f["rechnungsprefix"] if b["art"] == "rechnung" else f["angebotsprefix"]
        nummer = belege.naechste_nummer(cur, b["art"], prefix or ("RE" if b["art"] == "rechnung" else "AN"))
        heute = date.today()
        ziel = heute + timedelta(days=f["zahlungsziel_tage"] if b["art"] == "rechnung" else data.gueltig_tage)
        cur.execute("""UPDATE belege SET nummer=%s, status='gestellt', datum=%s, faellig_am=%s, netto_cent=%s, ust_satz=%s, ust_cent=%s, brutto_cent=%s, kleinunternehmer=%s,
                              empfaenger=%s::jsonb, geaendert_am=now() WHERE id=%s""",
                    (nummer, heute, ziel, s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], json.dumps(belege.empfaenger_von(cur, b["kunden_id"])), bid))
        audit(cur, user, "beleg_ausgestellt", b["kunden_id"], {"nummer": nummer})
    return {"nummer": nummer}


@router.post("/belege/{bid}/senden")
def senden(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if not b["kunden_id"]:
            raise HTTPException(400, "Dieses Angebot gehört zu einem Lead. Bitte im Lead auf „Angebot senden“ gehen.")
        if b["status"] not in ("gestellt", "versendet") or not b["nummer"]:
            raise HTTPException(400, "Bitte den Beleg zuerst ausstellen.")
        cur.execute("SELECT email, ansprechpartner FROM kunden WHERE id=%s", (b["kunden_id"],))
        k = cur.fetchone()
        daten, name = belege.beleg_pdf(cur, bid)
    if not k["email"]:
        raise HTTPException(400, "Beim Kunden ist keine E-Mail-Adresse hinterlegt.")
    ok, fehler = mailer.beleg(k["email"], b["art"], b["nummer"], k["ansprechpartner"], daten, name, b["faellig_am"], angebot_link=b["art"] == "angebot")
    if b["art"] == "angebot":
        from . import angebotserinnerung
        angebotserinnerung.mail_ergebnis(bid, ok, fehler)
    if ok:
        with tx("admin") as cur:
            cur.execute("UPDATE belege SET versendet_am=now(), status='versendet', geaendert_am=now() WHERE id=%s", (bid,))
            audit(cur, user, "beleg_gesendet", b["kunden_id"], {"nummer": b["nummer"]})
    return {"gesendet": ok, "grund": fehler}


class BezahltIn(BaseModel):
    betrag_cent: int | None = Field(default=None, ge=0)
    datum: date | None = None


@router.post("/belege/{bid}/bezahlt")
def bezahlt(bid: str, data: BezahltIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["art"] != "rechnung" or b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Nur offene Rechnungen können als bezahlt markiert werden.")
        betrag = data.betrag_cent if data.betrag_cent is not None else b["brutto_cent"]
        if betrag < b["brutto_cent"]:
            raise HTTPException(400, "Der Betrag ist kleiner als die Rechnung. Teilzahlungen werden nicht geführt – bitte erst bei vollständigem Eingang buchen.")
        cur.execute("UPDATE belege SET status='bezahlt', bezahlt_am=%s, bezahlt_cent=%s, geaendert_am=now() WHERE id=%s", (data.datum or date.today(), betrag, bid))
        audit(cur, user, "rechnung_bezahlt", b["kunden_id"], {"nummer": b["nummer"]})
    return {"ok": True}


class AbgleichIn(BaseModel):
    csv: str = Field(max_length=3_000_000)
    anwenden: bool = False


@router.post("/belege/zahlungsabgleich")
def zahlungsabgleich_route(data: AbgleichIn, user: dict = Depends(require_admin)):
    """Kontoauszug-CSV mit offenen Rechnungen abgleichen. Ohne 'anwenden' nur Vorschau; gebucht werden nur eindeutige Treffer mit passendem Betrag."""
    try:
        zeilen = zahlungsabgleich.zeilen_lesen(data.csv)
    except ValueError as e:
        raise HTTPException(400, str(e))
    with tx("admin") as cur:
        erg = zahlungsabgleich.abgleichen(cur, zeilen)
        gebucht = 0
        if data.anwenden:
            for t in erg["sicher"]:
                cur.execute("UPDATE belege SET status='bezahlt', bezahlt_am=%s, bezahlt_cent=%s, geaendert_am=now() WHERE id=%s AND status IN ('gestellt','versendet') RETURNING kunden_id",
                            (t["datum"] or date.today(), t["eingang_cent"], t["beleg_id"]))
                r = cur.fetchone()
                if r:
                    gebucht += 1
                    audit(cur, user, "rechnung_bezahlt", r["kunden_id"], {"nummer": t["nummer"], "quelle": "kontoauszug"})
    return {"zeilen": len(zeilen), "gebucht": gebucht, "angewendet": data.anwenden, **erg}


class MahnIn(BaseModel):
    stufe: int = Field(ge=1, le=3)
    senden: bool = True
    text: str | None = Field(default=None, max_length=5000)


MAHN_TITEL = {1: "Zahlungserinnerung", 2: "1. Mahnung", 3: "2. Mahnung"}


def mahnung_ausfuehren(user: dict, bid: str, stufe: int, senden: bool = True, text: str | None = None) -> dict:
    """Erzeugt die Mahn-PDF, verschickt sie (wenn gewünscht) und hält die Stufe fest. Wirft HTTPException bei Problemen."""
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["art"] != "rechnung" or b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Mahnen geht nur bei offenen Rechnungen.")
        if not b["faellig_am"] or b["faellig_am"] >= date.today():
            raise HTTPException(400, "Die Rechnung ist noch nicht überfällig.")
        if stufe <= b["mahnstufe"]:
            raise HTTPException(400, "Diese Mahnstufe wurde schon verschickt.")
        cur.execute("SELECT email, ansprechpartner FROM kunden WHERE id=%s", (b["kunden_id"],))
        k = cur.fetchone()
        daten, name = belege.mahn_pdf(cur, bid, stufe)
    titel = MAHN_TITEL[stufe]
    gesendet, grund = False, ""
    if senden:
        if not k["email"]:
            raise HTTPException(400, "Beim Kunden ist keine E-Mail-Adresse hinterlegt.")
        gesendet, grund = mailer.mahnung(k["email"], titel, b["nummer"], daten, name, (text or "").strip() or None, (k["ansprechpartner"] or "").strip() or None)
        if not gesendet:
            return {"gesendet": False, "grund": grund}
    with tx("admin") as cur:
        cur.execute("UPDATE belege SET mahnstufe=%s, mahn_am=current_date, geaendert_am=now() WHERE id=%s", (stufe, bid))
        audit(cur, user, "mahnung", b["kunden_id"], {"nummer": b["nummer"], "stufe": stufe, "gesendet": gesendet, "text_angepasst": bool((text or "").strip())})
    return {"gesendet": gesendet, "grund": grund}


@router.post("/belege/{bid}/mahnung")
def mahnung(bid: str, data: MahnIn, user: dict = Depends(require_admin)):
    return mahnung_ausfuehren(user, bid, data.stufe, data.senden, data.text)


@router.post("/belege/{bid}/stornieren")
def stornieren(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["art"] != "rechnung" or b["storno_von"] or b["status"] not in ("gestellt", "versendet", "bezahlt"):
            raise HTTPException(400, "Diese Rechnung kann nicht storniert werden.")
        f = rechtstexte.firma(cur)
        neg = [{**p, "preis_cent": -p["preis_cent"]} for p in b["positionen"]]
        s = belege.summen(neg, b["ust_satz"], b["kleinunternehmer"])
        nummer = belege.naechste_nummer(cur, "rechnung", f["rechnungsprefix"] or "RE")
        cur.execute("""INSERT INTO belege (art, nummer, kunden_id, status, betreff, positionen, leistungszeitraum, datum, faellig_am, netto_cent, ust_satz, ust_cent, brutto_cent,
                                           kleinunternehmer, empfaenger, storno_von)
                       VALUES ('rechnung',%s,%s,'gestellt',%s,%s::jsonb,%s,current_date,current_date,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id""",
                    (nummer, b["kunden_id"], f"Storno zu {b['nummer']}", json.dumps(neg), b["leistungszeitraum"], s["netto_cent"], b["ust_satz"], s["ust_cent"], s["brutto_cent"],
                     b["kleinunternehmer"], json.dumps(belege.empfaenger_von(cur, b["kunden_id"])), bid))
        sid = cur.fetchone()["id"]
        cur.execute("UPDATE belege SET status='storniert', geaendert_am=now() WHERE id=%s", (bid,))
        audit(cur, user, "rechnung_storniert", b["kunden_id"], {"nummer": b["nummer"], "storno": nummer})
    return {"id": sid, "nummer": nummer}


class AngebotStatus(BaseModel):
    status: str = Field(pattern="^(angenommen|abgelehnt)$")
    grund_code: str = Field(default="", max_length=30)
    grund_text: str = Field(default="", max_length=500)


@router.post("/belege/{bid}/angebot-status")
def angebot_status(bid: str, data: AngebotStatus, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["art"] != "angebot" or b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Nur ausgestellte Angebote können angenommen oder abgelehnt werden.")
        info = None
        if data.status == "angenommen" and b.get("lead_id"):
            # Angebot an einen Lead: gleicher Ablauf wie bei der Online-Annahme (Verlauf, Aufgabe, Hinweise, Bestätigung)
            cur.execute("SELECT firma AS lead_firma FROM leads WHERE id=%s", (b["lead_id"],))
            b = {**b, **(cur.fetchone() or {})}
            info = angebotsfluss.angenommen(cur, b, "telefonisch/schriftlich bestätigt", "team", user["email"], user=user)
        else:
            cur.execute("UPDATE belege SET status=%s, geaendert_am=now() WHERE id=%s", (data.status, bid))
            if data.status == "abgelehnt" and data.grund_code in angebotsgrund.GRUENDE:
                cur.execute("UPDATE belege SET grund_code=%s, grund_text=%s, grund_am=now() WHERE id=%s", (data.grund_code, data.grund_text.strip() or None, bid))
            if data.status == "abgelehnt" and b.get("lead_id"):
                cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)", (b["lead_id"], f"Angebot {b['nummer']} abgelehnt (vom Team erfasst)", user["email"]))
                cur.execute("UPDATE leads SET status=CASE WHEN status='angebot' THEN 'antwort' ELSE status END, wiedervorlage_am=current_date WHERE id=%s AND kunden_id IS NULL", (b["lead_id"],))
        audit(cur, user, "angebot_" + data.status, b["kunden_id"], {"nummer": b["nummer"]})
    if info:
        angebotsfluss.melden(info)
    return {"ok": True}


@router.post("/belege/{bid}/rechnung")
def aus_angebot(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        if b["art"] != "angebot" or b["status"] not in ("angenommen", "versendet", "gestellt"):
            raise HTTPException(400, "Eine Rechnung kann nur aus einem ausgestellten Angebot erstellt werden.")
        if not b["kunden_id"]:
            raise HTTPException(400, "Das Angebot gehört noch zu einem Lead. Bitte erst den Lead in einen Kunden umwandeln.")
        cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (b["kunden_id"],))
        if cur.fetchone()["referenzkunde"]:
            raise HTTPException(400, "Referenzkunden bekommen keine Rechnung.")
        f = rechtstexte.firma(cur)
        s = belege.summen(b["positionen"], f["mwst_satz"], f["kleinunternehmer"])
        cur.execute("""INSERT INTO belege (art, kunden_id, betreff, einleitung, schluss, positionen, netto_cent, ust_satz, ust_cent, brutto_cent, kleinunternehmer, angebot_id)
                       VALUES ('rechnung',%s,%s,'',%s,%s::jsonb,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (b["kunden_id"], b["betreff"], "", json.dumps(b["positionen"]), s["netto_cent"], s["ust_satz"], s["ust_cent"], s["brutto_cent"], f["kleinunternehmer"], bid))
        rid = cur.fetchone()["id"]
        audit(cur, user, "rechnung_aus_angebot", b["kunden_id"], {"angebot": b["nummer"]})
    return {"id": rid}


@router.get("/belege/{bid}/pdf")
def pdf_admin(bid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            daten, name = belege.beleg_pdf(cur, bid)
    except (LookupError, errors.InvalidTextRepresentation):
        raise HTTPException(404, "Beleg nicht gefunden.")
    return _pdf_antwort(daten, name)


# ---------------------------------------------------------------- Kundenportal
@kunde_router.get("/belege")
def kunde_liste(user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute(f"""SELECT id, art, nummer, status, betreff, datum, faellig_am, brutto_cent, storno_von, {UEBERFAELLIG} AS ueberfaellig
                        FROM belege WHERE status <> 'entwurf' ORDER BY datum DESC, erstellt_am DESC LIMIT 200""")
        return cur.fetchall()


@kunde_router.get("/belege/{bid}/pdf")
def kunde_pdf(bid: str, user: dict = Depends(require_inhaber)):
    try:
        f = rechtstexte.firma_system()
        with tx("kunde", user["kunden_id"]) as cur:
            daten, name = belege.beleg_pdf(cur, bid, f)
    except (LookupError, errors.InvalidTextRepresentation):
        raise HTTPException(404, "Beleg nicht gefunden.")
    return _pdf_antwort(daten, name)


@kunde_router.post("/belege/{bid}/annehmen")
def kunde_annehmen(bid: str, user: dict = Depends(require_inhaber)):
    mail_an = None
    with tx("system") as cur:
        cur.execute("SELECT art, nummer, status, kunden_id, faellig_am FROM belege WHERE id=%s AND kunden_id=%s", (bid, user["kunden_id"]))
        b = cur.fetchone()
        if not b or b["art"] != "angebot":
            raise HTTPException(404, "Angebot nicht gefunden.")
        if b["status"] not in ("gestellt", "versendet"):
            raise HTTPException(400, "Dieses Angebot kann nicht mehr angenommen werden.")
        if b["faellig_am"] and b["faellig_am"] < date.today():
            raise HTTPException(400, "Dieses Angebot ist abgelaufen. Bitte melde dich bei uns.")
        cur.execute("UPDATE belege SET status='angenommen', geaendert_am=now() WHERE id=%s", (bid,))
        audit(cur, user, "angebot_angenommen", user["kunden_id"], {"nummer": b["nummer"]})
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        r = cur.fetchone()
        mail_an = r and r["email"]
    if mail_an:
        mailer.senden(mail_an, f"Angebot {b['nummer']} wurde angenommen", f"Der Kunde hat das Angebot {b['nummer']} im Portal angenommen.\n\n{mailer.config.BASE_URL}/admin#belege" + mailer.SIGNATUR)
    return {"ok": True}
