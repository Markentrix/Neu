"""Wissensbasis eines Kunden pflegen: Einträge von Hand, Upload von TXT/MD/PDF (Text wird gelesen und gespeichert), ein-/ausschalten, löschen.
Die aktiven Einträge nutzt der Assistent (KI) des Kunden. Die Originaldatei wird nicht aufbewahrt, nur der gelesene Text."""
import io
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from . import push
from .db import tx
from .security import audit, rate_limit, require_admin, require_inhaber, require_modul

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


@router.get("/{kid}/wissen-vorschlaege")
def vorschlaege(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _kunde(cur, kid)
        cur.execute("""SELECT v.*, w.schluessel AS alt_titel, w.wert AS alt_wert FROM wissen_vorschlaege v LEFT JOIN wissensbasis w ON w.id=v.wissen_id
                       WHERE v.kunden_id=%s AND (v.status='offen' OR v.bearbeitet_am > now() - interval '14 days') ORDER BY (v.status='offen') DESC, v.erstellt_am DESC LIMIT 60""", (kid,))
        return {"vorschlaege": [_vorschlag(r, True) for r in cur.fetchall()]}


class EntscheidungIn(BaseModel):
    notiz: str = Field(default="", max_length=500)


def _entscheiden(kid: str, vid: str, user: dict, uebernehmen: bool, notiz: str):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM wissen_vorschlaege WHERE id=%s AND kunden_id=%s FOR UPDATE", (vid, kid))
        except Exception:
            raise HTTPException(404, "Vorschlag nicht gefunden.")
        v = cur.fetchone()
        if not v:
            raise HTTPException(404, "Vorschlag nicht gefunden.")
        if v["status"] != "offen":
            raise HTTPException(409, "Dieser Vorschlag ist schon bearbeitet.")
        if uebernehmen:
            if v["aktion"] == "neu":
                _speichern(cur, kid, _bereich(v["bereich"] or "kunde"), v["schluessel"], v["wert"], "kunde", True)
            else:
                if not v["wissen_id"]:
                    raise HTTPException(409, "Der Eintrag, auf den sich der Vorschlag bezieht, existiert nicht mehr. Bitte ablehnen.")
                if v["aktion"] == "aendern":
                    cur.execute("UPDATE wissensbasis SET wert=%s WHERE id=%s AND kunden_id=%s", (v["wert"], v["wissen_id"], kid))
                else:
                    cur.execute("UPDATE wissensbasis SET aktiv=false WHERE id=%s AND kunden_id=%s", (v["wissen_id"], kid))
        cur.execute("UPDATE wissen_vorschlaege SET status=%s, notiz=%s, bearbeitet_am=now() WHERE id=%s",
                    ("uebernommen" if uebernehmen else "abgelehnt", notiz.strip() or None, vid))
        cur.execute("UPDATE aufgaben SET status='erledigt', erledigt_am=now(), erledigt_von=%s WHERE auto_schluessel=%s AND status='offen'", (user.get("email"), f"wissen-{vid}"))
        audit(cur, user, "wissen_vorschlag_" + ("uebernommen" if uebernehmen else "abgelehnt"), kid, {"schluessel": v["schluessel"][:120], "aktion": v["aktion"]})
        ids = push.kunde(cur, kid)
    push.senden(ids, "Dein Wissen für den Assistenten" if uebernehmen else "Änderungswunsch abgelehnt", f"„{v['schluessel'][:60]}“: " + ("übernommen." if uebernehmen else (notiz.strip()[:120] or "abgelehnt.")), "/app#wissen", "wissen")
    return {"ok": True}


@router.post("/{kid}/wissen-vorschlaege/{vid}/uebernehmen")
def uebernehmen(kid: str, vid: str, user: dict = Depends(require_admin)):
    return _entscheiden(kid, vid, user, True, "")


@router.post("/{kid}/wissen-vorschlaege/{vid}/ablehnen")
def ablehnen(kid: str, vid: str, data: EntscheidungIn, user: dict = Depends(require_admin)):
    return _entscheiden(kid, vid, user, False, data.notiz)


def _vorschlag(r: dict, admin: bool = False) -> dict:
    o = {"id": str(r["id"]), "aktion": r["aktion"], "bereich": r["bereich"] or "", "schluessel": r["schluessel"], "wert": r["wert"] or "", "status": r["status"],
         "notiz": r["notiz"] or "", "erstellt_am": r["erstellt_am"], "bearbeitet_am": r["bearbeitet_am"]}
    if admin:
        o["alt_wert"] = r.get("alt_wert") or ""
    return o


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


# ---------------------------------------------------------------- Kunde: Änderungen vorschlagen
kunde = APIRouter(prefix="/api/kunde/wissen")


def _kunden_gate(cur, user):
    require_modul(cur, user, "ki_chat")


@kunde.get("")
def k_liste(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        _kunden_gate(cur, user)
        cur.execute("SELECT * FROM wissensbasis WHERE kunden_id=%s ORDER BY bereich, schluessel", (kid,))
        eintraege = [{**_zeile(r), "wert": r["wert"][:6000], "gekuerzt": len(r["wert"]) > 6000} for r in cur.fetchall()]
        cur.execute("SELECT * FROM wissen_vorschlaege WHERE kunden_id=%s AND (status='offen' OR bearbeitet_am > now() - interval '30 days') ORDER BY (status='offen') DESC, erstellt_am DESC LIMIT 40", (kid,))
        return {"eintraege": eintraege, "vorschlaege": [_vorschlag(r) for r in cur.fetchall()]}


class VorschlagIn(BaseModel):
    aktion: str = Field(pattern=r"^(neu|aendern|ausschalten)$")
    wissen_id: str | None = None
    schluessel: str = Field(default="", max_length=120)
    wert: str = Field(default="", max_length=TEXT_MAX)


def _vorschlag_anlegen(user: dict, aktion: str, wissen_id: str | None, schluessel: str, wert: str):
    kid = user["kunden_id"]
    rate_limit("wissenvorschlag:" + str(kid), 40, 3600)
    schluessel, wert = schluessel.strip(), wert.strip()
    with tx("kunde", kid) as cur:
        _kunden_gate(cur, user)
        bereich = "kunde"
        if aktion in ("aendern", "ausschalten"):
            try:
                cur.execute("SELECT id, bereich, schluessel FROM wissensbasis WHERE id=%s AND kunden_id=%s", (wissen_id, kid))
            except Exception:
                raise HTTPException(404, "Eintrag nicht gefunden.")
            w = cur.fetchone()
            if not w:
                raise HTTPException(404, "Eintrag nicht gefunden.")
            schluessel, bereich = w["schluessel"], w["bereich"]
        if not schluessel:
            raise HTTPException(400, "Bitte einen Titel eintragen.")
        if aktion != "ausschalten" and not wert:
            raise HTTPException(400, "Bitte den Text eintragen.")
        cur.execute("SELECT count(*) AS n FROM wissen_vorschlaege WHERE kunden_id=%s AND status='offen'", (kid,))
        if cur.fetchone()["n"] >= 20:
            raise HTTPException(409, "Es warten schon 20 Vorschläge auf Prüfung. Bitte warte, bis das Team sie bearbeitet hat.")
        cur.execute("""INSERT INTO wissen_vorschlaege (kunden_id, wissen_id, aktion, bereich, schluessel, wert, von) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (kid, w["id"] if aktion != "neu" else None, aktion, bereich, schluessel, wert or None, user["id"]))
        vid = cur.fetchone()["id"]
    with tx("system") as cur:
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = cur.fetchone()["firma"]
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        a = cur.fetchone()
        was = {"neu": "neues Wissen", "aendern": "Änderung", "ausschalten": "Ausschalten"}[aktion]
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel) VALUES (%s,%s,%s,current_date + 2,'auto',%s) ON CONFLICT DO NOTHING""",
                    (kid, f"{firma}: Wissen prüfen ({was}: {schluessel})"[:200], a and a["email"], f"wissen-{vid}"))
        ids = push.admins(cur)
    push.senden(ids, "Wissen: Änderungswunsch", f"{firma}: {was} „{schluessel[:60]}“", "/admin#kunden", "wissen")
    return {"ok": True, "id": str(vid)}


@kunde.post("/vorschlaege")
def k_vorschlag(data: VorschlagIn, user: dict = Depends(require_inhaber)):
    return _vorschlag_anlegen(user, data.aktion, data.wissen_id, data.schluessel, data.wert)


@kunde.post("/vorschlaege/datei")
def k_vorschlag_datei(datei: UploadFile = File(...), user: dict = Depends(require_inhaber)):
    name = (datei.filename or "").replace("\\", "/").split("/")[-1].strip()
    if not name.lower().endswith(ENDUNGEN):
        raise HTTPException(422, "Erlaubt sind TXT-, MD- und PDF-Dateien.")
    roh = datei.file.read(DATEI_MAX + 1)
    if len(roh) > DATEI_MAX:
        raise HTTPException(413, "Die Datei ist größer als 10 MB.")
    text = text_aus_datei(name, roh)
    return _vorschlag_anlegen(user, "neu", None, re.sub(r"\.(txt|md|pdf)$", "", name, flags=re.I)[:120] or "Dokument", text)


@kunde.delete("/vorschlaege/{vid}")
def k_zurueckziehen(vid: str, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        try:
            cur.execute("UPDATE wissen_vorschlaege SET status='zurueckgezogen', bearbeitet_am=now() WHERE id=%s AND kunden_id=%s AND status='offen' RETURNING id", (vid, kid))
        except Exception:
            raise HTTPException(404, "Vorschlag nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(409, "Dieser Vorschlag ist nicht mehr offen.")
    with tx("system") as cur:
        cur.execute("UPDATE aufgaben SET status='erledigt', erledigt_am=now(), erledigt_von='Kunde' WHERE auto_schluessel=%s AND status='offen'", (f"wissen-{vid}",))
    return {"ok": True}
