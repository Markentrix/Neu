"""Leads aus Excel (.xlsx) oder CSV importieren: Spalten werden automatisch erkannt, Dubletten übersprungen."""
import base64
import csv
import io
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .db import tx
from .security import EMAIL_RE, audit, require_admin

router = APIRouter(prefix="/api")
MAX_ZEILEN = 5000

# Zielfeld -> mögliche Spaltenüberschriften (kleingeschrieben, ohne Sonderzeichen verglichen)
SPALTEN = {
    "firma": ["firma", "firmenname", "unternehmen", "name", "company", "betrieb", "titel", "title"],
    "ansprechpartner": ["ansprechpartner", "kontakt", "kontaktperson", "inhaber", "geschaeftsfuehrer", "contact", "ansprechperson"],
    "email": ["email", "emailadresse", "mail", "emailaddress"],
    "telefon": ["telefon", "tel", "telefonnummer", "phone", "mobil", "handy", "rufnummer"],
    "website": ["website", "webseite", "homepage", "url", "internet", "web", "domain"],
    "branche": ["branche", "kategorie", "category", "gewerk", "typ", "art"],
    "plz": ["plz", "postleitzahl", "zip", "zipcode"],
    "ort": ["ort", "stadt", "city", "standort"],
    "notiz": ["notiz", "notizen", "bemerkung", "kommentar", "hinweis", "note", "beschreibung", "adresse", "strasse", "straße", "anschrift"],
}
GRENZEN = {"firma": 200, "ansprechpartner": 200, "email": 254, "telefon": 60, "website": 253, "branche": 120, "plz": 10, "ort": 120, "notiz": 2000}


def _norm(s) -> str:
    s = str(s or "").strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]", "", s)


def _zeilen(name: str, roh: bytes) -> list[list]:
    if name.lower().endswith(".csv") or name.lower().endswith(".txt"):
        try:
            text = roh.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = roh.decode("cp1252", errors="replace")
        try:
            dialekt = csv.Sniffer().sniff(text[:4000], delimiters=";,\t|")
        except csv.Error:
            dialekt = csv.excel
        return [list(z) for z in csv.reader(io.StringIO(text), dialekt)]
    if not name.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Bitte eine Excel-Datei (.xlsx) oder CSV-Datei hochladen. Ältere .xls-Dateien bitte in Excel als .xlsx speichern.")
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(roh), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        out = []
        for z in ws.iter_rows(values_only=True):
            out.append(list(z))
            if len(out) > MAX_ZEILEN + 5:
                break
        return out
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Die Datei konnte nicht gelesen werden. Ist es eine gültige Excel-Datei?")


def _text(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return s or None


def _lesen(name: str, roh: bytes):
    zeilen = [z for z in _zeilen(name, roh) if any(_text(x) for x in z)]
    if len(zeilen) < 2:
        raise HTTPException(400, "Die Datei enthält keine Datenzeilen. In der ersten Zeile müssen die Spaltenüberschriften stehen.")
    kopf = zeilen[0]
    zuordnung: dict[str, int] = {}
    for i, k in enumerate(kopf):
        n = _norm(k)
        for ziel, namen in SPALTEN.items():
            if ziel not in zuordnung and n in [_norm(x) for x in namen]:
                zuordnung[ziel] = i
                break
    if "firma" not in zuordnung:
        raise HTTPException(400, "Es wurde keine Spalte „Firma“ gefunden. Bitte die Überschrift in der ersten Zeile anpassen (z. B. Firma, Unternehmen, Name).")
    daten = zeilen[1:]
    if len(daten) > MAX_ZEILEN:
        raise HTTPException(400, f"Zu viele Zeilen (mehr als {MAX_ZEILEN}). Bitte die Datei aufteilen.")
    erkannt = {ziel: str(kopf[i]).strip() for ziel, i in zuordnung.items()}
    leads = []
    for z in daten:
        d = {}
        for ziel, i in zuordnung.items():
            d[ziel] = _text(z[i]) if i < len(z) else None
        leads.append(d)
    return leads, erkannt


class ImportIn(BaseModel):
    datei_base64: str = Field(max_length=9_000_000)
    datei_name: str = Field(max_length=200)
    liste: str | None = Field(default=None, max_length=120)
    quelle: str = "akquise"
    temperatur: str | None = None
    vertriebspartner_id: str | None = None
    nur_pruefen: bool = True


@router.post("/admin/leads/import")
def importieren(data: ImportIn, user: dict = Depends(require_admin)):
    if data.quelle not in ("manuell", "lead_finder", "empfehlung", "akquise", "messe"):
        raise HTTPException(400, "Ungültige Quelle.")
    if data.temperatur not in (None, "", "kalt", "warm", "heiss"):
        raise HTTPException(400, "Ungültige Einstufung.")
    try:
        roh = base64.b64decode(data.datei_base64.split(",")[-1], validate=True)
    except Exception:
        raise HTTPException(400, "Die Datei ist beschädigt.")
    if len(roh) > 6_000_000:
        raise HTTPException(400, "Die Datei ist zu groß (maximal 6 MB).")
    leads, erkannt = _lesen(data.datei_name, roh)
    liste = (data.liste or "").strip() or re.sub(r"\.[A-Za-z]+$", "", data.datei_name)[:120] + " " + date.today().strftime("%d.%m.%Y")
    with tx("admin") as cur:
        cur.execute("SELECT lower(email) AS e FROM leads WHERE email IS NOT NULL UNION SELECT lower(email) FROM kunden WHERE email IS NOT NULL")
        vorhanden_mail = {r["e"] for r in cur.fetchall()}
        cur.execute("SELECT lower(firma)||'|'||coalesce(plz,'') AS k FROM leads")
        vorhanden_firma = {r["k"] for r in cur.fetchall()}
        if data.vertriebspartner_id:
            cur.execute("SELECT 1 FROM vertriebspartner WHERE id=%s", (data.vertriebspartner_id,))
            if not cur.fetchone():
                raise HTTPException(400, "Vertriebler nicht gefunden.")
        neu, doppelt, ungueltig = [], 0, []
        for nr, d in enumerate(leads, start=2):
            if not d.get("firma"):
                ungueltig.append({"zeile": nr, "grund": "Firma fehlt"}); continue
            if d.get("email"):
                d["email"] = d["email"].lower().replace("mailto:", "").strip()
                if not EMAIL_RE.match(d["email"]):
                    ungueltig.append({"zeile": nr, "grund": "E-Mail ungültig: " + d["email"][:60]}); continue
            for k, g in GRENZEN.items():
                if d.get(k) and len(d[k]) > g:
                    d[k] = d[k][:g]
            if d.get("website"):
                d["website"] = re.sub(r"^https?://", "", d["website"], flags=re.I).rstrip("/")[:253]
            mail_k = d.get("email")
            fk = d["firma"].lower() + "|" + (d.get("plz") or "")
            if (mail_k and mail_k in vorhanden_mail) or fk in vorhanden_firma:
                doppelt += 1; continue
            if mail_k:
                vorhanden_mail.add(mail_k)
            vorhanden_firma.add(fk)
            neu.append(d)
        if not data.nur_pruefen:
            for d in neu:
                cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, branche, plz, ort, notiz, quelle, temperatur, vertriebspartner_id, liste, loeschen_nach)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, current_date + interval '12 months')""",
                            (d["firma"], d.get("ansprechpartner"), d.get("email"), d.get("telefon"), d.get("website"), d.get("branche"), d.get("plz"), d.get("ort"),
                             d.get("notiz"), data.quelle, data.temperatur or None, data.vertriebspartner_id, liste))
            audit(cur, user, "leads_import", None, {"datei": data.datei_name, "neu": len(neu), "doppelt": doppelt, "ungueltig": len(ungueltig), "liste": liste})
    return {"erkannt": erkannt, "gesamt": len(leads), "neu": len(neu), "doppelt": doppelt, "ungueltig": ungueltig[:30], "ungueltig_anzahl": len(ungueltig),
            "vorschau": neu[:8], "liste": liste, "importiert": not data.nur_pruefen}
