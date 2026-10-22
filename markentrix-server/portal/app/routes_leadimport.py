"""Leads aus Excel (.xlsx) oder CSV importieren: Spalten werden automatisch erkannt, Dubletten übersprungen."""
import base64
import csv
import io
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from collections import Counter

from . import push, sperre, zuweisung
from .db import tx
from .security import EMAIL_RE, audit, require_admin

router = APIRouter(prefix="/api")
MAX_ZEILEN = 5000

# Zielfeld -> mögliche Spaltenüberschriften (verglichen ohne Groß-/Kleinschreibung und Sonderzeichen)
SPALTEN = {
    "firma": ["firma", "firmenname", "unternehmen", "name", "company", "betrieb", "titel", "title"],
    "ansprechpartner": ["ansprechpartner", "kontakt", "kontaktperson", "inhaber", "geschaeftsfuehrer", "contact", "ansprechperson"],
    "email": ["email", "emailadresse", "mail", "emailaddress"],
    "telefon": ["telefon", "tel", "telefonnummer", "phone", "mobil", "handy", "rufnummer"],
    "website": ["website", "webseite", "homepage", "url", "internet", "web", "domain"],
    "branche": ["branche", "brancheausgoogletyp", "kategorie", "category", "gewerk", "typ", "art"],
    "gruppe": ["branchengruppe", "gruppe"],
    "plz": ["plz", "postleitzahl", "zip", "zipcode"],
    "ort": ["ort", "stadt", "city", "standort"],
    "adresse": ["adresse", "strasse", "anschrift", "address"],
    "prio": ["prio", "prioritaet", "priority"],
    "km": ["km", "entfernung", "entfernungkm"],
    "bewertung": ["bewertung", "rating", "sterne"],
    "anz_bewertungen": ["anzbewertungen", "anzahlbewertungen", "bewertungen", "reviews"],
    "maps": ["googlemaps", "maps", "kartenlink"],
    "hinweis": ["hinweis", "notiz", "notizen", "bemerkung", "kommentar", "note", "beschreibung"],
    "status": ["status"],
    "plattform": ["plattform", "plattformbaukasten", "baukasten"],
}
GRENZEN = {"firma": 200, "ansprechpartner": 200, "email": 254, "telefon": 60, "website": 253, "branche": 120, "gruppe": 120, "plz": 10, "ort": 120, "notiz": 2000}
PRIO_TEMP = {"a": "heiss", "b": "warm", "c": "kalt"}
PLZ_ORT = re.compile(r"\b(\d{5})\s+([^,]+?)\s*$")


def _norm(s) -> str:
    s = str(s or "").strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]", "", s)


def _text(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return s or None


def _blaetter(name: str, roh: bytes) -> list[tuple[str, list[list], list[list]]]:
    """Liefert je Blatt (Name, Zeilen, Links). Links: gleiche Form wie Zeilen, enthält Hyperlink-Ziele (oder None)."""
    n = name.lower()
    if n.endswith((".csv", ".txt")):
        try:
            text = roh.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = roh.decode("cp1252", errors="replace")
        try:
            dialekt = csv.Sniffer().sniff(text[:4000], delimiters=";,\t|")
        except csv.Error:
            dialekt = csv.excel
        z = [list(r) for r in csv.reader(io.StringIO(text), dialekt)]
        return [("Tabelle", z, [[None] * len(r) for r in z])]
    if not n.endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Bitte eine Excel-Datei (.xlsx) oder CSV-Datei hochladen. Ältere .xls-Dateien bitte in Excel als .xlsx speichern.")
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(roh), data_only=True)
        out = []
        for ws in wb.worksheets:
            zeilen, links = [], []
            for row in ws.iter_rows(max_row=MAX_ZEILEN + 12):
                zeilen.append([c.value for c in row])
                links.append([(c.hyperlink.target if getattr(c, "hyperlink", None) else None) for c in row])
            out.append((ws.title, zeilen, links))
        return out
    except Exception:
        raise HTTPException(400, "Die Datei konnte nicht gelesen werden. Ist es eine gültige Excel-Datei?")


def _blatt_lesen(zeilen, links):
    """Findet die Kopfzeile (in den ersten 10 Zeilen mit Firmenspalte) und gibt (Zuordnung, Kopf, Datenzeilen) zurück oder None."""
    for k, z in enumerate(zeilen[:10]):
        zuordnung: dict[str, int] = {}
        for i, c in enumerate(z):
            n = _norm(c)
            if not n:
                continue
            for ziel, namen in SPALTEN.items():
                if ziel not in zuordnung and n in [_norm(x) for x in namen]:
                    zuordnung[ziel] = i
                    break
        if "firma" in zuordnung and len(zuordnung) >= 2:
            daten = [(k + 2 + j, zeilen[k + 1 + j], links[k + 1 + j]) for j in range(len(zeilen) - k - 1) if any(_text(x) for x in zeilen[k + 1 + j])]
            return zuordnung, z, daten
    return None


def _zeile(zuordnung, kopf, z, l, standard_temp):
    d = {}
    for ziel, i in zuordnung.items():
        d[ziel] = _text(z[i]) if i < len(z) else None
    adr = d.get("adresse")
    if adr and not d.get("plz"):
        m = PLZ_ORT.search(adr)
        if m:
            d["plz"] = m.group(1)
            if not d.get("ort"):
                d["ort"] = m.group(2).strip()
    if d.get("maps") and "maps" in zuordnung:
        i = zuordnung["maps"]
        d["maps"] = (l[i] if i < len(l) and l[i] else None) or (d["maps"] if str(d["maps"]).startswith("http") else None)
    prio = (d.get("prio") or "").strip().lower()
    d["temperatur"] = PRIO_TEMP.get(prio) or standard_temp
    teile = []
    if d.get("gruppe"):
        teile.append(d["gruppe"])
    if d.get("prio"):
        teile.append("Prio " + d["prio"])
    if d.get("km"):
        teile.append(f"{d['km']} km von Celle")
    if d.get("bewertung"):
        teile.append("Google-Bewertung " + d["bewertung"] + (f" ({d['anz_bewertungen']} Bewertungen)" if d.get("anz_bewertungen") else ""))
    if d.get("status"):
        teile.append(d["status"])
    if d.get("plattform"):
        teile.append("Plattform: " + d["plattform"])
    if d.get("hinweis"):
        teile.append(d["hinweis"])
    if adr:
        teile.append("Adresse: " + adr)
    if d.get("maps"):
        teile.append("Karte: " + d["maps"])
    d["notiz"] = " · ".join(teile)[:2000] or None
    return d


class ImportIn(BaseModel):
    datei_base64: str = Field(max_length=9_000_000)
    datei_name: str = Field(max_length=200)
    liste: str | None = Field(default=None, max_length=100)
    quelle: str = "lead_finder"
    temperatur: str | None = None          # Standard-Einstufung, wenn die Datei keine Prio-Spalte hat (Prio A/B/C = heiß/warm/kalt)
    vertriebspartner_id: str | None = None
    blaetter: list[str] | None = None      # welche Tabellenblätter importiert werden (leer = alle mit „Firma“-Spalte außer „ungeprüft“)
    grundlage: str | None = None          # Grundlage der Ansprache (b2b_mutmasslich, einwilligung, empfehlung, bestandskontakt)
    verteilen: bool = False                # gleichmäßig auf alle aktiven Vertriebler verteilen (wenn kein Vertriebler gewählt ist)
    nur_pruefen: bool = True


def _standard_blatt(name: str) -> bool:
    return "ungeprüft" not in name.lower() and "ungepruft" not in name.lower()


@router.post("/admin/leads/import")
def importieren(data: ImportIn, user: dict = Depends(require_admin)):
    if data.quelle not in ("manuell", "lead_finder", "empfehlung", "akquise", "messe"):
        raise HTTPException(400, "Ungültige Quelle.")
    if data.grundlage not in (None, "", "b2b_mutmasslich", "einwilligung", "empfehlung", "bestandskontakt"):
        raise HTTPException(400, "Ungültige Grundlage der Ansprache.")
    if data.temperatur not in (None, "", "kalt", "warm", "heiss"):
        raise HTTPException(400, "Ungültige Einstufung.")
    try:
        roh = base64.b64decode(data.datei_base64.split(",")[-1], validate=True)
    except Exception:
        raise HTTPException(400, "Die Datei ist beschädigt.")
    if len(roh) > 8_000_000:
        raise HTTPException(400, "Die Datei ist zu groß (maximal 8 MB).")
    blaetter = []
    for name, zeilen, links in _blaetter(data.datei_name, roh):
        r = _blatt_lesen(zeilen, links)
        if r:
            if len(r[2]) > MAX_ZEILEN:
                raise HTTPException(400, f"Das Blatt „{name}“ hat mehr als {MAX_ZEILEN} Zeilen. Bitte aufteilen.")
            blaetter.append((name, *r))
    if not blaetter:
        raise HTTPException(400, "Es wurde keine Tabelle mit einer Spalte „Firma“ (oder Firmenname, Unternehmen, Name) gefunden. Die Überschriften müssen in der ersten Zeile stehen.")
    gewaehlt = set(data.blaetter) if data.blaetter else {b[0] for b in blaetter if _standard_blatt(b[0])} or {blaetter[0][0]}
    basis = re.sub(r"\.[A-Za-z]+$", "", data.datei_name)[:60]
    with tx("admin") as cur:
        cur.execute("SELECT lower(email) AS e FROM leads WHERE email IS NOT NULL UNION SELECT lower(email) FROM kunden WHERE email IS NOT NULL")
        mails = {r["e"] for r in cur.fetchall()}
        cur.execute("SELECT lower(firma)||'|'||coalesce(plz,'') AS k FROM leads")
        firmen = {r["k"] for r in cur.fetchall()}
        cur.execute("SELECT regexp_replace(telefon,'[^0-9]','','g') AS t FROM leads WHERE telefon IS NOT NULL")
        telefone = {r["t"] for r in cur.fetchall() if r["t"]}
        if data.vertriebspartner_id:
            cur.execute("SELECT 1 FROM vertriebspartner WHERE id=%s", (data.vertriebspartner_id,))
            if not cur.fetchone():
                raise HTTPException(400, "Vertriebler nicht gefunden.")
        cur.execute("SELECT art, wert FROM sperrliste")
        gesperrt_set = {(r["art"], r["wert"]) for r in cur.fetchall()}
        uebersicht, gesamt_neu, verteilt = [], 0, Counter()
        for name, zuordnung, kopf, daten in blaetter:
            neu, doppelt, ungueltig, gesperrt = [], 0, [], 0
            if name in gewaehlt:
                m, f, t = mails, firmen, telefone
            else:  # nur zählen, nichts vormerken
                m, f, t = set(mails), set(firmen), set(telefone)
            for nr, z, l in daten:
                d = _zeile(zuordnung, kopf, z, l, data.temperatur or None)
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
                if any(k in gesperrt_set for k in sperre.schluessel(d.get("email"), d.get("telefon"), d.get("website"))):
                    gesperrt += 1; continue
                tel = re.sub(r"[^0-9]", "", d.get("telefon") or "")
                fk = d["firma"].lower() + "|" + (d.get("plz") or "")
                if (d.get("email") and d["email"] in m) or fk in f or (len(tel) >= 6 and tel in t):
                    doppelt += 1; continue
                if d.get("email"):
                    m.add(d["email"])
                f.add(fk)
                if len(tel) >= 6:
                    t.add(tel)
                d["_liste"] = (data.liste.strip() + " · " if data.liste and data.liste.strip() else basis + " · ") + name
                neu.append(d)
            uebersicht.append({"name": name, "gewaehlt": name in gewaehlt, "zeilen": len(daten), "neu": len(neu), "doppelt": doppelt, "gesperrt": gesperrt, "ungueltig": len(ungueltig),
                               "ungueltig_beispiele": ungueltig[:5], "vorschau": neu[:5], "erkannt": {k: str(kopf[i]).strip() for k, i in zuordnung.items()}})
            if name in gewaehlt:
                gesamt_neu += len(neu)
                if not data.nur_pruefen and neu:
                    if data.vertriebspartner_id:
                        pids = [data.vertriebspartner_id] * len(neu)
                    elif data.verteilen:
                        pids = zuweisung.verteilen(cur, len(neu)) or [None] * len(neu)
                    else:
                        pids = [None] * len(neu)
                    verteilt.update(p for p in pids if p)
                    cur.executemany("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, branche, gruppe, plz, ort, notiz, quelle, temperatur, vertriebspartner_id, liste, loeschen_nach, ansprache_grundlage)
                                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, current_date + interval '12 months', %s)""",
                                    [(d["firma"], d.get("ansprechpartner"), d.get("email"), d.get("telefon"), d.get("website"), d.get("branche"), d.get("gruppe"), d.get("plz"), d.get("ort"),
                                      d.get("notiz"), data.quelle, d["temperatur"], pid, d["_liste"][:120], data.grundlage or None) for d, pid in zip(neu, pids)])
        if not data.nur_pruefen:
            audit(cur, user, "leads_import", None, {"datei": data.datei_name, "neu": gesamt_neu, "blaetter": sorted(gewaehlt)})
    if not data.nur_pruefen and gesamt_neu and verteilt:
        for pid, n in verteilt.items():
            with tx("system") as cur:
                ids = push.partner(cur, pid)
            push.senden(ids, "Neue Leads", f"{n} neue Leads wurden Ihnen zugewiesen.", "/vertrieb#heute", "zugewiesen")
    for u in uebersicht:
        for d in u["vorschau"]:
            d.pop("_liste", None)
    return {"blaetter": uebersicht, "neu": gesamt_neu, "importiert": not data.nur_pruefen}
