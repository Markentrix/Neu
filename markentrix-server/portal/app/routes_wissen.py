"""Wissensbasis eines Kunden pflegen: Einträge von Hand, Upload von TXT/MD/PDF (Text wird gelesen und gespeichert), ein-/ausschalten, löschen.
Die aktiven Einträge nutzt der Assistent (KI) des Kunden. Die Originaldatei wird nicht aufbewahrt, nur der gelesene Text."""
import io
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from .db import tx
from .security import audit, rate_limit, require_admin

router = APIRouter(prefix="/api/admin/kunden")

DATEI_MAX = 10 * 1024 * 1024
TEXT_MAX = 200_000
ENDUNGEN = (".txt", ".md", ".pdf")


def _bereich(b: str) -> str:
    b = re.sub(r"[^a-z0-9_]+", "_", (b or "dokumente").strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")).strip("_")
    return b[:40] or "dokumente"


def _kunde(cur, kid: str):
    try:
        cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
    except Exception:
        raise HTTPException(404, "Kunde nicht gefunden.")
    if not cur.fetchone():
        raise HTTPException(404, "Kunde nicht gefunden.")


def text_aus_datei(name: str, roh: bytes) -> str:
    low = name.lower()
    if low.endswith(".pdf"):
        if not roh.startswith(b"%PDF"):
            raise HTTPException(422, "Das ist keine gültige PDF-Datei.")
        try:
            r = PdfReader(io.BytesIO(roh))
            if r.is_encrypted:
                raise HTTPException(422, "Die PDF ist passwortgeschützt. Bitte ohne Schutz speichern und neu hochladen.")
            if len(r.pages) > 300:
                raise HTTPException(422, "Die PDF hat mehr als 300 Seiten. Bitte aufteilen.")
            text = "\n\n".join((p.extract_text() or "").strip() for p in r.pages)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422, "Die PDF konnte nicht gelesen werden.")
    else:
        if b"\x00" in roh[:4096]:
            raise HTTPException(422, "Das ist keine Textdatei.")
        for kod in ("utf-8-sig", "cp1252"):
            try:
                text = roh.decode(kod)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = roh.decode("latin-1", "replace")
    text = re.sub(r"[ \t]+\n", "\n", text.replace("\r\n", "\n").replace("\x00", ""))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise HTTPException(422, "In der Datei steht kein lesbarer Text. Bei gescannten PDFs fehlt die Texterkennung: bitte als Text abtippen oder mit Texterkennung speichern.")
    if len(text) > TEXT_MAX:
        raise HTTPException(422, f"Der Text ist zu lang ({len(text):,} Zeichen, erlaubt {TEXT_MAX:,}). Bitte in mehrere Dateien aufteilen.".replace(",", "."))
    return text


def _zeile(r: dict, voll: bool = False) -> dict:
    return {"id": str(r["id"]), "bereich": r["bereich"], "schluessel": r["schluessel"], "quelle": r["quelle"], "aktiv": r["aktiv"], "geaendert_am": r["geaendert_am"],
            "laenge": len(r["wert"]), "vorschau": r["wert"][:240], **({"wert": r["wert"]} if voll else {})}


@router.get("/{kid}/wissen")
def liste(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _kunde(cur, kid)
        cur.execute("SELECT * FROM wissensbasis WHERE kunden_id=%s ORDER BY bereich, schluessel", (kid,))
        return {"eintraege": [_zeile(r) for r in cur.fetchall()]}


@router.get("/{kid}/wissen/{wid}")
def lesen(kid: str, wid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM wissensbasis WHERE id=%s AND kunden_id=%s", (wid, kid))
        except Exception:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        return _zeile(r, True)


def _speichern(cur, kid: str, bereich: str, schluessel: str, wert: str, quelle: str, aktiv: bool) -> tuple[str, bool]:
    cur.execute("""INSERT INTO wissensbasis (kunden_id, bereich, schluessel, wert, quelle, aktiv) VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (kunden_id, bereich, schluessel) DO UPDATE SET wert=EXCLUDED.wert, quelle=EXCLUDED.quelle, aktiv=EXCLUDED.aktiv
                   RETURNING id, (xmax <> 0) AS ersetzt""", (kid, bereich, schluessel, wert, quelle, aktiv))
    r = cur.fetchone()
    return str(r["id"]), bool(r["ersetzt"])


@router.post("/{kid}/wissen/upload")
def hochladen(kid: str, datei: UploadFile = File(...), bereich: str = Form("dokumente"), aktiv: str = Form("1"), user: dict = Depends(require_admin)):
    rate_limit("wissenup:" + str(user["id"]), 60, 600)
    name = (datei.filename or "").replace("\\", "/").split("/")[-1].strip()
    if not name.lower().endswith(ENDUNGEN):
        raise HTTPException(422, "Erlaubt sind TXT-, MD- und PDF-Dateien.")
    roh = datei.file.read(DATEI_MAX + 1)
    if len(roh) > DATEI_MAX:
        raise HTTPException(413, "Die Datei ist größer als 10 MB.")
    text = text_aus_datei(name, roh)
    schluessel = re.sub(r"\.(txt|md|pdf)$", "", name, flags=re.I).strip()[:120] or "Dokument"
    b = _bereich(bereich)
    with tx("admin") as cur:
        _kunde(cur, kid)
        wid, ersetzt = _speichern(cur, kid, b, schluessel, text, "upload", aktiv != "0")
        audit(cur, user, "wissen_upload", kid, {"datei": name[:120], "zeichen": len(text), "ersetzt": ersetzt})
    return {"ok": True, "id": wid, "schluessel": schluessel, "zeichen": len(text), "ersetzt": ersetzt}


class EintragIn(BaseModel):
    bereich: str = Field(default="allgemein", max_length=40)
    schluessel: str = Field(min_length=1, max_length=120)
    wert: str = Field(min_length=1, max_length=TEXT_MAX)
    aktiv: bool = True


@router.post("/{kid}/wissen")
def anlegen(kid: str, data: EintragIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _kunde(cur, kid)
        wid, ersetzt = _speichern(cur, kid, _bereich(data.bereich), data.schluessel.strip(), data.wert.strip(), "manuell", data.aktiv)
        audit(cur, user, "wissen_eintrag", kid, {"schluessel": data.schluessel[:120], "ersetzt": ersetzt})
    return {"ok": True, "id": wid, "ersetzt": ersetzt}


class AendernIn(BaseModel):
    aktiv: bool | None = None
    wert: str | None = Field(default=None, min_length=1, max_length=TEXT_MAX)


@router.patch("/{kid}/wissen/{wid}")
def aendern(kid: str, wid: str, data: AendernIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("""UPDATE wissensbasis SET aktiv=COALESCE(%s, aktiv), wert=COALESCE(%s, wert) WHERE id=%s AND kunden_id=%s RETURNING schluessel""",
                        (data.aktiv, data.wert.strip() if data.wert else None, wid, kid))
        except Exception:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        audit(cur, user, "wissen_geaendert", kid, {"schluessel": r["schluessel"][:120], "aktiv": data.aktiv})
    return {"ok": True}


@router.delete("/{kid}/wissen/{wid}")
def loeschen(kid: str, wid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("DELETE FROM wissensbasis WHERE id=%s AND kunden_id=%s RETURNING schluessel", (wid, kid))
        except Exception:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Eintrag nicht gefunden.")
        audit(cur, user, "wissen_geloescht", kid, {"schluessel": r["schluessel"][:120]})
    return {"ok": True}
