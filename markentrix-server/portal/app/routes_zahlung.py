"""Zahlung per SEPA-Lastschrift (Mandat im Kundenportal, Einzugsdatei für das Online-Banking) oder Überweisung,
plus automatische Zahlungserinnerungen. Der Zahlungseingang wird weiter über den Kontoauszug-Abgleich gebucht."""
import logging
import re
import secrets
import unicodedata
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import belege, einstellungen, mailer, rechtstexte
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin, require_inhaber

log = logging.getLogger("zahlung")
router = APIRouter()
MAHN_STANDARD = {"aktiv": False, "tage_1": 7, "tage_2": 21, "tage_3": 35, "verzug_tage": 0, "verzug_dienste": False}
ZAHLUNG_STANDARD = {"glaeubiger_id": "", "vorab_tage": 3}
TITEL = {1: "Zahlungserinnerung", 2: "1. Mahnung", 3: "2. Mahnung"}
GID_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{3}[A-Z0-9]{1,28}$")


def zahlung_cfg(cur) -> dict:
    return {**ZAHLUNG_STANDARD, **einstellungen.lesen(cur, "zahlung")}


def mahn_cfg(cur) -> dict:
    return {**MAHN_STANDARD, **einstellungen.lesen(cur, "mahnwesen")}


def iban_ok(iban: str) -> bool:
    i = "".join(iban.split()).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", i):
        return False
    if i.startswith("DE") and len(i) != 22:
        return False
    z = "".join(str(int(c, 36)) for c in i[4:] + i[:4])
    return int(z) % 97 == 1


def sepa_text(s: str, n: int) -> str:
    """Nur Zeichen, die SEPA-Dateien erlauben (Umlaute werden umgeschrieben)."""
    s = (s or "").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9/\-?:().,'+ ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:n] or "-"


# ---------------------------------------------------------------- Einstellungen
@router.get("/api/admin/einstellungen/zahlung")
def lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        z = zahlung_cfg(cur)
        m = mahn_cfg(cur)
        f = rechtstexte.firma(cur)
    return {"lastschrift": {"glaeubiger_id": z["glaeubiger_id"], "vorab_tage": z["vorab_tage"], "iban_da": bool((f.get("iban") or "").strip())}, "mahnwesen": m}


class ZahlungIn(BaseModel):
    glaeubiger_id: str = Field(default="", max_length=40)
    vorab_tage: int = Field(default=3, ge=2, le=14)
    mahn_aktiv: bool = False
    tage_1: int = Field(default=7, ge=1, le=90)
    tage_2: int = Field(default=21, ge=2, le=120)
    tage_3: int = Field(default=35, ge=3, le=180)
    verzug_tage: int = Field(default=0, ge=0, le=180)       # 0 = aus; sonst: so viele Tage nach der 2. Mahnung wird der Wartungsplan pausiert
    verzug_dienste: bool = False                              # zusätzlich Formular und Terminbuchung der Kunden-Website pausieren


@router.put("/api/admin/einstellungen/zahlung")
def speichern(data: ZahlungIn, user: dict = Depends(require_admin)):
    if not (data.tage_1 < data.tage_2 < data.tage_3):
        raise HTTPException(400, "Die Fristen müssen aufsteigend sein (Erinnerung, 1. Mahnung, 2. Mahnung).")
    gid = "".join(data.glaeubiger_id.split()).upper()
    if gid and not GID_RE.match(gid):
        raise HTTPException(400, "Die Gläubiger-Identifikationsnummer sieht anders aus (Beispiel: DE98ZZZ09999999999). Sie kommt von der Bundesbank.")
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "zahlung", {"glaeubiger_id": gid, "vorab_tage": data.vorab_tage})
        einstellungen.schreiben(cur, "mahnwesen", {"aktiv": data.mahn_aktiv, "tage_1": data.tage_1, "tage_2": data.tage_2, "tage_3": data.tage_3, "verzug_tage": data.verzug_tage, "verzug_dienste": data.verzug_dienste})
        audit(cur, user, "einstellungen_zahlung", None, {"lastschrift": bool(gid), "mahnwesen": data.mahn_aktiv})
    return {"ok": True}


# ---------------------------------------------------------------- Mandat im Kundenportal
def mandatstext(firma: str, vorab: int) -> str:
    return (f"Ich ermächtige {firma}, Zahlungen von meinem Konto mittels SEPA-Basislastschrift einzuziehen. Zugleich weise ich mein Kreditinstitut an, "
            f"die von {firma} auf mein Konto gezogenen Lastschriften einzulösen. Hinweis: Ich kann innerhalb von acht Wochen, beginnend mit dem Belastungsdatum, "
            f"die Erstattung des belasteten Betrages verlangen. Es gelten dabei die mit meinem Kreditinstitut vereinbarten Bedingungen. "
            f"Die Ankündigung (Betrag und Datum) erfolgt per E-Mail mindestens {vorab} Tage vor dem Einzug.")


@router.get("/api/kunde/lastschrift")
def mandat_lesen(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        z = zahlung_cfg(cur)
        f = rechtstexte.firma(cur)
        cur.execute("SELECT referenz, kontoinhaber, iban_ende, erteilt_am FROM sepa_mandate WHERE kunden_id=%s AND widerrufen_am IS NULL", (user["kunden_id"],))
        m = cur.fetchone()
    return {"verfuegbar": bool(z["glaeubiger_id"] and (f.get("iban") or "").strip()), "mandat": m, "text": mandatstext(f.get("name") or "Markentrix", z["vorab_tage"]),
            "glaeubiger_id": z["glaeubiger_id"]}


class MandatIn(BaseModel):
    kontoinhaber: str = Field(min_length=2, max_length=70)
    iban: str = Field(min_length=15, max_length=40)
    bic: str = Field(default="", max_length=11)
    zustimmung: bool = False


def _mandat_mails(an, name, ref, ende, gid, firma, team):
    if an:
        mailer.mandat_bestaetigt(an, name, ref, ende, gid, firma)
    if team:
        mailer.senden(team, "Neues SEPA-Lastschriftmandat", f"{firma}-Kunde hat ein Lastschriftmandat erteilt (Referenz {ref}). Einzug unter Angebote & Rechnungen → Lastschrift.")


@router.post("/api/kunde/lastschrift")
def mandat_erteilen(data: MandatIn, request: Request, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    rate_limit("mandat:" + str(user["id"]), 10, 3600)
    if not data.zustimmung:
        raise HTTPException(400, "Bitte bestätigen Sie die Einzugsermächtigung.")
    iban = "".join(data.iban.split()).upper()
    if not iban_ok(iban):
        raise HTTPException(400, "Die IBAN ist ungültig. Bitte prüfen Sie die Eingabe.")
    from .routes_zusammenarbeit import admin_empfaenger
    with tx("system") as cur:
        z = zahlung_cfg(cur)
        f = rechtstexte.firma(cur)
        if not z["glaeubiger_id"] or not (f.get("iban") or "").strip():
            raise HTTPException(400, "Die Lastschrift ist noch nicht eingerichtet. Bitte überweisen Sie den Betrag.")
        cur.execute("SELECT kundennummer, email, ansprechpartner FROM kunden WHERE id=%s", (user["kunden_id"],))
        k = cur.fetchone()
        cur.execute("UPDATE sepa_mandate SET widerrufen_am=now() WHERE kunden_id=%s AND widerrufen_am IS NULL", (user["kunden_id"],))
        ref = f"MK-{k['kundennummer']}-{datetime.now(timezone.utc):%Y%m%d%H%M}-{secrets.token_hex(2).upper()}"
        cur.execute("""INSERT INTO sepa_mandate (kunden_id, referenz, kontoinhaber, iban_verschluesselt, iban_ende, bic, erteilt_ip) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (user["kunden_id"], ref, data.kontoinhaber.strip(), einstellungen.verschluesseln(iban), iban[-4:], data.bic.strip().upper() or None, client_ip(request)))
        audit(cur, user, "sepa_mandat_erteilt", user["kunden_id"], {"referenz": ref})
        team = admin_empfaenger(cur)
    bg.add_task(_mandat_mails, k["email"], k["ansprechpartner"], ref, iban[-4:], z["glaeubiger_id"], f.get("name") or "Markentrix", team)
    return {"ok": True, "referenz": ref}


@router.delete("/api/kunde/lastschrift")
def mandat_widerrufen(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("UPDATE sepa_mandate SET widerrufen_am=now() WHERE kunden_id=%s AND widerrufen_am IS NULL RETURNING referenz", (user["kunden_id"],))
        m = cur.fetchone()
        if not m:
            raise HTTPException(404, "Es gibt kein aktives Mandat.")
        cur.execute("UPDATE belege SET einzug_am=NULL, zahlart=NULL WHERE kunden_id=%s AND zahlart='lastschrift' AND status IN ('gestellt','versendet') AND einzug_am > current_date", (user["kunden_id"],))
        audit(cur, user, "sepa_mandat_widerrufen", user["kunden_id"], {"referenz": m["referenz"]})
    return {"ok": True}


# ---------------------------------------------------------------- Einzug (Admin)
@router.get("/api/admin/lastschrift")
def einzug_liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        z = zahlung_cfg(cur)
        f = rechtstexte.firma(cur)
        cur.execute("""SELECT b.id, b.nummer, b.faellig_am, b.brutto_cent - coalesce(b.bezahlt_cent,0) AS offen_cent, b.einzug_am, k.firma, k.kundennummer, m.iban_ende, m.referenz
                       FROM belege b JOIN kunden k ON k.id=b.kunden_id JOIN sepa_mandate m ON m.kunden_id=b.kunden_id AND m.widerrufen_am IS NULL
                       WHERE b.art='rechnung' AND b.status IN ('gestellt','versendet') AND b.storno_von IS NULL AND b.brutto_cent > 0
                       ORDER BY b.faellig_am NULLS LAST, b.nummer""")
        zeilen = cur.fetchall()
    return {"konfiguriert": bool(z["glaeubiger_id"] and (f.get("iban") or "").strip()), "vorab_tage": z["vorab_tage"],
            "bereit": [r for r in zeilen if not r["einzug_am"]], "angekuendigt": [r for r in zeilen if r["einzug_am"]]}


class ExportIn(BaseModel):
    beleg_ids: list[str] = Field(min_length=1, max_length=200)
    einzug_am: date


def pain008(firma: dict, gid: str, einzug: date, posten: list, jetzt: datetime) -> str:
    """SEPA-Basislastschrift im Format pain.008.001.02, getrennt nach Erst- (FRST) und Folgelastschriften (RCUR)."""
    iban = "".join(firma["iban"].split()).upper()
    bic = (firma.get("bic") or "").strip().upper()
    name = sepa_text(firma.get("name") or "Markentrix", 70)
    msg = "MK" + jetzt.strftime("%Y%m%d%H%M%S")
    gesamt = sum(p["cent"] for p in posten)
    eur = lambda c: f"{c / 100:.2f}"
    teile = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.008.001.02" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
             f'<CstmrDrctDbtInitn><GrpHdr><MsgId>{msg}</MsgId><CreDtTm>{jetzt.strftime("%Y-%m-%dT%H:%M:%S")}</CreDtTm><NbOfTxs>{len(posten)}</NbOfTxs><CtrlSum>{eur(gesamt)}</CtrlSum><InitgPty><Nm>{escape(name)}</Nm></InitgPty></GrpHdr>']
    for folge in ("FRST", "RCUR"):
        gruppe = [p for p in posten if p["folge"] == folge]
        if not gruppe:
            continue
        agent = f"<BIC>{escape(bic)}</BIC>" if bic else "<Othr><Id>NOTPROVIDED</Id></Othr>"
        teile.append(f'<PmtInf><PmtInfId>{msg}-{folge}</PmtInfId><PmtMtd>DD</PmtMtd><BtchBookg>true</BtchBookg><NbOfTxs>{len(gruppe)}</NbOfTxs><CtrlSum>{eur(sum(p["cent"] for p in gruppe))}</CtrlSum>'
                     f'<PmtTpInf><SvcLvl><Cd>SEPA</Cd></SvcLvl><LclInstrm><Cd>CORE</Cd></LclInstrm><SeqTp>{folge}</SeqTp></PmtTpInf><ReqdColltnDt>{einzug.isoformat()}</ReqdColltnDt>'
                     f'<Cdtr><Nm>{escape(name)}</Nm></Cdtr><CdtrAcct><Id><IBAN>{iban}</IBAN></Id></CdtrAcct><CdtrAgt><FinInstnId>{agent}</FinInstnId></CdtrAgt><ChrgBr>SLEV</ChrgBr>'
                     f'<CdtrSchmeId><Id><PrvtId><Othr><Id>{escape(gid)}</Id><SchmeNm><Prtry>SEPA</Prtry></SchmeNm></Othr></PrvtId></Id></CdtrSchmeId>')
        for p in gruppe:
            dbtr_agent = f"<BIC>{escape(p['bic'])}</BIC>" if p["bic"] else "<Othr><Id>NOTPROVIDED</Id></Othr>"
            teile.append(f'<DrctDbtTxInf><PmtId><EndToEndId>{escape(sepa_text(p["nummer"], 35))}</EndToEndId></PmtId><InstdAmt Ccy="EUR">{eur(p["cent"])}</InstdAmt>'
                         f'<DrctDbtTx><MndtRltdInf><MndtId>{escape(sepa_text(p["referenz"], 35))}</MndtId><DtOfSgntr>{p["mandat_datum"]}</DtOfSgntr></MndtRltdInf></DrctDbtTx>'
                         f'<DbtrAgt><FinInstnId>{dbtr_agent}</FinInstnId></DbtrAgt><Dbtr><Nm>{escape(sepa_text(p["inhaber"], 70))}</Nm></Dbtr><DbtrAcct><Id><IBAN>{p["iban"]}</IBAN></Id></DbtrAcct>'
                         f'<RmtInf><Ustrd>{escape(sepa_text("Rechnung " + p["nummer"], 140))}</Ustrd></RmtInf></DrctDbtTxInf>')
        teile.append("</PmtInf>")
    teile.append("</CstmrDrctDbtInitn></Document>")
    return "".join(teile)


def _vorab_mails(auftraege: list, einzug: date, gid: str, firma: str):
    for an, name, posten, ref in auftraege:
        if an:
            mailer.lastschrift_vorab(an, name, posten, einzug, ref, gid, firma)


@router.post("/api/admin/lastschrift/export")
def einzug_export(data: ExportIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        z = zahlung_cfg(cur)
        f = rechtstexte.firma(cur)
        if not z["glaeubiger_id"] or not (f.get("iban") or "").strip():
            raise HTTPException(400, "Bitte zuerst Gläubiger-ID (Einstellungen → Zahlung) und IBAN (Firmendaten) eintragen.")
        if data.einzug_am < date.today() + timedelta(days=z["vorab_tage"]):
            raise HTTPException(400, f"Das Einzugsdatum muss mindestens {z['vorab_tage']} Tage in der Zukunft liegen, damit die Ankündigung rechtzeitig beim Kunden ist.")
        if data.einzug_am.weekday() >= 5:
            raise HTTPException(400, "Bitte einen Werktag als Einzugsdatum wählen.")
        cur.execute("""SELECT b.id, b.nummer, b.kunden_id, b.brutto_cent - coalesce(b.bezahlt_cent,0) AS cent, k.email, k.ansprechpartner,
                              m.id AS mandat_id, m.referenz, m.kontoinhaber, m.iban_verschluesselt, m.bic, m.erteilt_am, m.erstmals_genutzt
                       FROM belege b JOIN kunden k ON k.id=b.kunden_id JOIN sepa_mandate m ON m.kunden_id=b.kunden_id AND m.widerrufen_am IS NULL
                       WHERE b.id = ANY(%s::uuid[]) AND b.art='rechnung' AND b.status IN ('gestellt','versendet') AND b.einzug_am IS NULL AND b.storno_von IS NULL AND b.brutto_cent > 0""",
                    (data.beleg_ids,))
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(400, "Keine passenden Rechnungen (Mandat aktiv, Rechnung offen, noch nicht angekündigt).")
        posten, je_kunde = [], {}
        for r in rows:
            iban = einstellungen.entschluesseln(r["iban_verschluesselt"])
            posten.append({"nummer": r["nummer"], "cent": int(r["cent"]), "referenz": r["referenz"], "inhaber": r["kontoinhaber"], "iban": iban, "bic": r["bic"],
                           "mandat_datum": r["erteilt_am"].date().isoformat(), "folge": "RCUR" if r["erstmals_genutzt"] else "FRST"})
            je_kunde.setdefault(r["kunden_id"], [r["email"], r["ansprechpartner"], [], r["referenz"]])[2].append((r["nummer"], int(r["cent"])))
        # Mehrere Rechnungen eines Kunden mit gleichem Mandat: FRST nur für die erste Gruppe, sonst lehnt die Bank doppelte FRST ab
        gesehen = set()
        for p in posten:
            if p["folge"] == "FRST":
                if p["referenz"] in gesehen:
                    p["folge"] = "RCUR"
                gesehen.add(p["referenz"])
        xml = pain008(f, z["glaeubiger_id"], data.einzug_am, posten, datetime.now(timezone.utc))
        cur.execute("UPDATE belege SET einzug_am=%s, zahlart='lastschrift', geaendert_am=now() WHERE id = ANY(%s::uuid[])", (data.einzug_am, [str(r["id"]) for r in rows]))
        cur.execute("UPDATE sepa_mandate SET erstmals_genutzt=true WHERE id = ANY(%s::uuid[])", ([str(r["mandat_id"]) for r in rows],))
        audit(cur, user, "lastschrift_export", None, {"anzahl": len(rows), "einzug_am": data.einzug_am.isoformat(), "summe_cent": sum(p["cent"] for p in posten)})
    bg.add_task(_vorab_mails, [tuple(v) for v in je_kunde.values()], data.einzug_am, z["glaeubiger_id"], f.get("name") or "Markentrix")
    return Response(xml, media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="lastschrift-{data.einzug_am.isoformat()}.xml"',
                                                                    "X-Anzahl": str(len(rows))})


class ZurueckIn(BaseModel):
    beleg_id: str


@router.post("/api/admin/lastschrift/zuruecksetzen")
def einzug_zurueck(data: ZurueckIn, user: dict = Depends(require_admin)):
    """Z. B. bei Rücklastschrift oder wenn die Datei nicht eingereicht wurde: Rechnung wieder normal offen."""
    with tx("admin") as cur:
        try:
            cur.execute("UPDATE belege SET einzug_am=NULL, zahlart=NULL, geaendert_am=now() WHERE id=%s AND zahlart='lastschrift' AND status IN ('gestellt','versendet') RETURNING kunden_id, nummer", (data.beleg_id,))
        except Exception:
            raise HTTPException(404, "Rechnung nicht gefunden.")
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Für diese Rechnung ist kein Einzug angekündigt.")
        audit(cur, user, "lastschrift_zurueck", r["kunden_id"], {"nummer": r["nummer"]})
    return {"ok": True}


# ---------------------------------------------------------------- Automatische Zahlungserinnerungen
def mahnlauf(cfg=None) -> list:
    """Verschickt fällige Erinnerungen/Mahnungen (nur wenn eingeschaltet). Rechnungen mit angekündigtem Einzug werden übersprungen."""
    with tx("system") as cur:
        m = mahn_cfg(cur)
        if not m["aktiv"]:
            return []
        t1, t2, t3 = int(m["tage_1"]), int(m["tage_2"]), int(m["tage_3"])
        cur.execute("""SELECT b.id, b.nummer, b.kunden_id, b.mahnstufe, k.email, k.firma FROM belege b JOIN kunden k ON k.id = b.kunden_id
                       WHERE b.art='rechnung' AND b.status IN ('gestellt','versendet') AND b.storno_von IS NULL AND NOT k.referenzkunde AND b.faellig_am IS NOT NULL
                         AND b.mahnstufe < 3 AND (b.mahn_am IS NULL OR b.mahn_am <= current_date - 7)
                         AND (b.einzug_am IS NULL OR b.einzug_am < current_date - 7)
                         AND CASE b.mahnstufe WHEN 0 THEN b.faellig_am <= current_date - %s WHEN 1 THEN b.faellig_am <= current_date - %s ELSE b.faellig_am <= current_date - %s END
                       ORDER BY b.faellig_am LIMIT 20""", (t1, t2, t3))
        faellig = cur.fetchall()
    getan = []
    for b in faellig:
        stufe = b["mahnstufe"] + 1
        if not b["email"]:
            continue
        with tx("system") as cur:
            daten, name = belege.mahn_pdf(cur, b["id"], stufe)
        ok, grund = mailer.mahnung(b["email"], TITEL[stufe], b["nummer"], daten, name)
        if not ok:
            log.warning("Auto-Mahnung %s fehlgeschlagen: %s", b["nummer"], grund)
            continue
        with tx("system") as cur:
            cur.execute("UPDATE belege SET mahnstufe=%s, mahn_am=current_date, auto_gemahnt_am=current_date, geaendert_am=now() WHERE id=%s", (stufe, b["id"]))
            audit(cur, None, "mahnung", b["kunden_id"], {"nummer": b["nummer"], "stufe": stufe, "gesendet": True, "automatisch": True})
        getan.append((b["firma"], b["nummer"], TITEL[stufe]))
    if getan:
        with tx("system") as cur:
            from .routes_zusammenarbeit import admin_empfaenger
            an = admin_empfaenger(cur)
        if an:
            mailer.senden(an, f"{len(getan)} Zahlungserinnerung(en) automatisch verschickt",
                          "Diese Schreiben hat das Portal heute automatisch verschickt:\n\n" + "\n".join(f"- {f}: {n} ({t})" for f, n, t in getan) + mailer.SIGNATUR)
    return getan
