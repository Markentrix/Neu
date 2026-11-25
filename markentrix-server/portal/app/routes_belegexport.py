"""Rechnungen nach Jahr: Übersicht mit Umsatz und Export für die Steuerberatung (ZIP mit PDFs und Rechnungsliste)."""
import csv
import io
import re
import unicodedata
import zipfile
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from . import belege
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin")

MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
SELECT = """SELECT b.id, b.nummer, b.datum, b.status, b.netto_cent, b.ust_satz, b.ust_cent, b.brutto_cent, b.bezahlt_am, b.bezahlt_cent, b.faellig_am,
                   b.leistungszeitraum, b.kleinunternehmer, b.storno_von, b.kaeufer_referenz, k.kundennummer, coalesce(k.firma, b.empfaenger->>'firma', '') AS firma,
                   (SELECT o.nummer FROM belege o WHERE o.id = b.storno_von) AS storno_zu
            FROM belege b LEFT JOIN kunden k ON k.id = b.kunden_id
            WHERE b.art = 'rechnung' AND b.nummer IS NOT NULL AND b.status <> 'entwurf' AND extract(year FROM b.datum) = %s"""


def _jahr(jahr: int | None) -> int:
    j = jahr or date.today().year
    if not 2000 <= j <= 2100:
        raise HTTPException(400, "Bitte ein Jahr zwischen 2000 und 2100 angeben.")
    return j


def _monat(monat: int | None) -> int | None:
    if monat in (None, 0):
        return None
    if not 1 <= monat <= 12:
        raise HTTPException(400, "Der Monat muss zwischen 1 und 12 liegen.")
    return monat


def dateiname(z: dict) -> str:
    """z. B. RE-2026-0001_Rechnung_Muster-GmbH.pdf, Stornos als Stornorechnung."""
    kunde = unicodedata.normalize("NFKD", (z["firma"] or "Kunde").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss"))
    kunde = re.sub(r"[^A-Za-z0-9]+", "-", kunde.encode("ascii", "ignore").decode()).strip("-")[:40] or "Kunde"
    return f"{z['nummer']}_{'Stornorechnung' if z['storno_von'] else 'Rechnung'}_{kunde}.pdf"


@router.get("/rechnungen-jahr")
def rechnungen_jahr(jahr: int | None = None, user: dict = Depends(require_admin)):
    """Alle ausgestellten Rechnungen eines Jahres mit Summen je Monat (Stornorechnungen mindern den Umsatz)."""
    j = _jahr(jahr)
    with tx("admin") as cur:
        cur.execute("SELECT DISTINCT extract(year FROM datum)::int AS j FROM belege WHERE art='rechnung' AND nummer IS NOT NULL ORDER BY j DESC")
        jahre = [r["j"] for r in cur.fetchall()] or [j]
        cur.execute(SELECT + " ORDER BY b.datum, b.nummer", (j,))
        zeilen = cur.fetchall()
    monate = [{"monat": m, "name": MONATE[m - 1], "anzahl": 0, "netto_cent": 0, "ust_cent": 0, "brutto_cent": 0} for m in range(1, 13)]
    offen = bezahlt = 0
    for z in zeilen:
        m = monate[z["datum"].month - 1]
        m["anzahl"] += 1
        m["netto_cent"] += z["netto_cent"]; m["ust_cent"] += z["ust_cent"]; m["brutto_cent"] += z["brutto_cent"]
        if z["status"] in ("gestellt", "versendet"):
            offen += z["brutto_cent"]
        elif z["status"] == "bezahlt":
            bezahlt += z["bezahlt_cent"] or z["brutto_cent"]
    summe = {k: sum(m[k] for m in monate) for k in ("anzahl", "netto_cent", "ust_cent", "brutto_cent")}
    summe.update({"offen_cent": offen, "bezahlt_cent": bezahlt})
    rechnungen = [{"id": z["id"], "nummer": z["nummer"], "datum": z["datum"], "kunde": ((z["kundennummer"] or "") + " " + z["firma"]).strip(), "status": z["status"], "brutto_cent": z["brutto_cent"],
                   "storno": z["storno_von"] is not None, "datei": dateiname(z)} for z in zeilen]
    return {"jahr": j, "jahre": jahre if j in jahre else sorted(jahre + [j], reverse=True), "summe": summe, "monate": monate, "rechnungen": rechnungen}


def _csv(zeilen: list, dateinamen: dict) -> str:
    eur = lambda c: f"{int(c or 0) / 100:.2f}".replace(".", ",")
    d = lambda x: x.strftime("%d.%m.%Y") if x else ""
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";")
    w.writerow(["Rechnungsnummer", "Rechnungsdatum", "Leistungszeitraum", "Kundennummer", "Kunde", "Netto", "USt-Satz %", "USt", "Brutto", "Status", "Bezahlt am", "Bezahlter Betrag",
                "Fällig am", "Storno zu Rechnung", "Hinweis", "Datei"])
    for z in zeilen:
        w.writerow([z["nummer"], d(z["datum"]), z["leistungszeitraum"] or "", z["kundennummer"] or "", z["firma"], eur(z["netto_cent"]), str(z["ust_satz"]).replace(".", ","), eur(z["ust_cent"]), eur(z["brutto_cent"]),
                    z["status"], d(z["bezahlt_am"]), eur(z["bezahlt_cent"]) if z["bezahlt_am"] else "", d(z["faellig_am"]), z["storno_zu"] or "",
                    "Kleinunternehmer § 19 UStG" if z["kleinunternehmer"] else "", dateinamen[z["id"]]])
    return "﻿" + puffer.getvalue()


@router.get("/belege-export.zip")
def export_zip(jahr: int | None = None, monat: int | None = None, user: dict = Depends(require_admin)):
    """ZIP für die Steuerberatung: Ordner „Rechnungen <Jahr>“ mit allen Rechnungs-PDFs (E-Rechnung/ZUGFeRD) und die Rechnungsliste als CSV."""
    j, m = _jahr(jahr), _monat(monat)
    with tx("admin") as cur:
        cur.execute(SELECT + (" AND extract(month FROM b.datum) = %s" if m else "") + " ORDER BY b.datum, b.nummer", (j, m) if m else (j,))
        zeilen = cur.fetchall()
        if len(zeilen) > 1500:
            raise HTTPException(400, "Zu viele Rechnungen für einen Export. Bitte einen einzelnen Monat wählen.")
        namen = {z["id"]: dateiname(z) for z in zeilen}
        ordner = f"Rechnungen {j}" + (f"/{m:02d} {MONATE[m - 1]}" if m else "")
        puffer = io.BytesIO()
        with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for z in zeilen:
                daten, _ = belege.beleg_pdf(cur, z["id"])
                zf.writestr(f"{ordner}/{namen[z['id']]}", daten)
            zf.writestr(f"{ordner}/Rechnungsliste {j}{f'-{m:02d}' if m else ''}.csv", _csv(zeilen, namen).encode("utf-8"))
            zf.writestr(f"{ordner}/LIES-MICH.txt", (
                f"Rechnungen {j}{f' ({MONATE[m - 1]})' if m else ''}, Export vom {date.today():%d.%m.%Y}\r\n\r\n"
                "Die PDF-Dateien sind die ausgestellten Rechnungen und Stornorechnungen. Sie enthalten die Rechnungsdaten zusätzlich maschinenlesbar (E-Rechnung im Format ZUGFeRD, Profil EN 16931).\r\n"
                "Die Rechnungsliste (CSV, Semikolon, Zahlen im deutschen Format, UTF-8) fasst alle Rechnungen mit Netto, Umsatzsteuer, Brutto, Zahlungsstatus und Dateiname zusammen.\r\n"
                "Stornorechnungen stehen mit negativen Beträgen in der Liste und mindern den Umsatz.\r\n").encode("utf-8"))
        audit(cur, user, "rechnungen_export", None, {"jahr": j, "monat": m, "anzahl": len(zeilen)})
    return Response(puffer.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="Rechnungen-{j}{f"-{m:02d}" if m else ""}.zip"'})
