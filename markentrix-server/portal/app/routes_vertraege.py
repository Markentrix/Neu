"""Verträge aus dem Portal: Referenzvertrag für Kunden, Handelsvertretervertrag für Vertriebspartner (vorausgefüllt als PDF per Mail),
unterschriebene Fassung ablegen. Dazu der Telefonleitfaden (PDF) für Vertriebler."""
import base64
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import mailer, rechtstexte, vertraege
from .db import tx
from .security import audit, require_admin, require_vertrieb

router = APIRouter(prefix="/api/admin")
vertrieb = APIRouter(prefix="/api/vertrieb")
MAX_DATEI = 6 * 1024 * 1024
SPALTEN = "id, art, kunden_id, partner_id, daten, erstellt_am, gesendet_am, gesendet_an, unterschrieben_am, datei_name, hochgeladen_am, datei IS NOT NULL AS hat_datei"


def _404():
    return HTTPException(404, "Nicht gefunden.")


def _kurz(s, n=200):
    return (s or "").strip()[:n]


# ---------------------------------------------------------------- Felder je Vertrag
def referenz_werte(k: dict, d: dict) -> dict:
    firma = _kurz(d.get("firma")) or k["firma"] or ""
    ort = _kurz(d.get("ort")) or f"{k.get('plz') or ''} {k.get('ort') or ''}".strip()
    vertreter = _kurz(d.get("vertreter")) or k.get("ansprechpartner") or ""
    return {"kunde_firma": firma, "kunde_strasse": _kurz(d.get("strasse")) or k.get("strasse") or "", "kunde_ort": ort, "kunde_vertreter": vertreter,
            "a_kunde": firma, "a_projekt": _kurz(d.get("projekt")), "a_datum": _kurz(d.get("hauptvertrag_vom"), 40), "a_zeitraum": _kurz(d.get("zeitraum"), 80),
            "sig_mx_ortdatum": "Celle, " + vertraege.datum_de(), "sig_k_name": f"{vertreter}, {firma}".strip(", ")}


def handelsvertreter_werte(p: dict, d: dict, f: dict) -> tuple:
    name = _kurz(d.get("name")) or p["name"] or ""
    steuer_mx = f.get("steuernummer") or f.get("ustid") or ""
    werte = {"pt_name": name, "pt_rechtsform": _kurz(d.get("rechtsform"), 60), "pt_strasse": _kurz(d.get("strasse")), "pt_ort": _kurz(d.get("ort")),
             "pt_mail": _kurz(d.get("mail")) or p.get("email") or "", "pt_steuer": _kurz(d.get("steuer"), 60), "mx_steuer": steuer_mx,
             "vertrag_mx_ort_datum": "Celle, " + vertraege.datum_de(), "vertrag_pt_name": name}
    for k in ("einmal", "monat", "praemie", "vorschuss"):
        if _kurz(d.get(k), 10):
            werte["rate_" + k] = _kurz(d.get(k), 10)
    haken = {"haupt": ["beauftragung_Hauptberuf"], "neben": ["beauftragung_Nebenberuf"]}.get(d.get("beauftragung") or "", [])
    return werte, haken


def _pdf(cur, z: dict) -> tuple:
    d = z["daten"]
    if z["art"] == "referenz":
        cur.execute("SELECT firma, ansprechpartner, strasse, plz, ort, email FROM kunden WHERE id=%s", (z["kunden_id"],))
        k = cur.fetchone()
        return vertraege.ausfuellen("referenz", referenz_werte(k, d)), vertraege.DATEINAME["referenz"] + ".pdf", k["email"], k["ansprechpartner"]
    cur.execute("SELECT name, email FROM vertriebspartner WHERE id=%s", (z["partner_id"],))
    p = cur.fetchone()
    werte, haken = handelsvertreter_werte(p, d, rechtstexte.firma(cur))
    return vertraege.ausfuellen("handelsvertreter", werte, haken), vertraege.DATEINAME["handelsvertreter"] + ".pdf", (_kurz(d.get("mail")) or p["email"]), (_kurz(d.get("name")) or p["name"])


def _senden(cur, z: dict, an: str | None, user: dict):
    pdf, name, mail_std, anrede = _pdf(cur, z)
    an = (an or mail_std or "").strip()
    if not an:
        raise HTTPException(400, "Keine E-Mail-Adresse hinterlegt. Bitte eine Adresse eintragen.")
    return pdf, name, an, anrede


def _versenden(zid: str, pdf: bytes, name: str, an: str, anrede, art: str, user: dict, kid=None):
    ok, fehler = mailer.vertrag_dokument(an, anrede, art, pdf, name)
    if not ok:
        raise HTTPException(400, "Die Mail konnte nicht gesendet werden: " + (fehler or "unbekannt"))
    with tx("admin") as cur:
        cur.execute("UPDATE vertragsdokumente SET gesendet_am=now(), gesendet_an=%s WHERE id=%s", (an, zid))
        audit(cur, user, "vertrag_gesendet", kid, {"art": art, "an": an})


class ReferenzIn(BaseModel):
    projekt: str = Field(default="", max_length=200)
    hauptvertrag_vom: str = Field(default="", max_length=40)
    zeitraum: str = Field(default="", max_length=80)
    firma: str = Field(default="", max_length=200)
    strasse: str = Field(default="", max_length=200)
    ort: str = Field(default="", max_length=200)
    vertreter: str = Field(default="", max_length=200)
    senden: bool = True
    an: str = Field(default="", max_length=200)


class HandelsIn(BaseModel):
    name: str = Field(default="", max_length=200)
    rechtsform: str = Field(default="", max_length=60)
    strasse: str = Field(default="", max_length=200)
    ort: str = Field(default="", max_length=200)
    mail: str = Field(default="", max_length=200)
    steuer: str = Field(default="", max_length=60)
    beauftragung: str = Field(default="", pattern="^(|haupt|neben)$")
    einmal: str = Field(default="", max_length=10)
    monat: str = Field(default="", max_length=10)
    praemie: str = Field(default="", max_length=10)
    vorschuss: str = Field(default="", max_length=10)
    senden: bool = True
    an: str = Field(default="", max_length=200)


def _anlegen(art: str, kid, pid, daten: dict, senden: bool, an: str, user: dict) -> dict:
    import json
    with tx("admin") as cur:
        if art == "referenz":
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
        else:
            cur.execute("SELECT 1 FROM vertriebspartner WHERE id=%s", (pid,))
        if not cur.fetchone():
            raise _404()
        cur.execute("INSERT INTO vertragsdokumente (art, kunden_id, partner_id, daten) VALUES (%s,%s,%s,%s::jsonb) RETURNING " + SPALTEN, (art, kid, pid, json.dumps(daten)))
        z = cur.fetchone()
        audit(cur, user, "vertrag_erstellt", kid, {"art": art, "id": str(z["id"])})
        pdf, name, an2, anrede = _senden(cur, z, an, user) if senden else (None, None, None, None)
    if senden:
        _versenden(z["id"], pdf, name, an2, anrede, art, user, kid)
    return {"ok": True, "id": z["id"], "gesendet": bool(senden)}


@router.post("/kunden/{kid}/referenzvertrag")
def referenz_neu(kid: str, data: ReferenzIn, user: dict = Depends(require_admin)):
    try:
        return _anlegen("referenz", kid, None, data.model_dump(exclude={"senden", "an"}), data.senden, data.an, user)
    except errors.InvalidTextRepresentation:
        raise _404()


@router.post("/vertrieb/partner/{pid}/handelsvertretervertrag")
def handelsvertreter_neu(pid: str, data: HandelsIn, user: dict = Depends(require_admin)):
    try:
        return _anlegen("handelsvertreter", None, pid, data.model_dump(exclude={"senden", "an"}), data.senden, data.an, user)
    except errors.InvalidTextRepresentation:
        raise _404()


@router.get("/kunden/{kid}/vertragsdokumente")
def liste_kunde(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE kunden_id=%s ORDER BY erstellt_am DESC", (kid,))
            return cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise _404()


@router.get("/vertrieb/partner/{pid}/vertragsdokumente")
def liste_partner(pid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE partner_id=%s ORDER BY erstellt_am DESC", (pid,))
            return cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise _404()


def _holen(cur, zid):
    cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE id=%s", (zid,))
    z = cur.fetchone()
    if not z:
        raise _404()
    return z


@router.get("/vertragsdokumente/{zid}/vorlage.pdf")
def vorlage(zid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            pdf, name, _m, _a = _pdf(cur, _holen(cur, zid))
    except errors.InvalidTextRepresentation:
        raise _404()
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


class SendenIn(BaseModel):
    an: str = Field(default="", max_length=200)


@router.post("/vertragsdokumente/{zid}/senden")
def erneut_senden(zid: str, data: SendenIn | None = None, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            z = _holen(cur, zid)
            pdf, name, an, anrede = _senden(cur, z, data.an if data else "", user)
    except errors.InvalidTextRepresentation:
        raise _404()
    _versenden(zid, pdf, name, an, anrede, z["art"], user, z["kunden_id"])
    return {"ok": True}


class UploadIn(BaseModel):
    datei_base64: str = Field(max_length=9_000_000)
    datei_name: str = Field(default="Vertrag-unterschrieben.pdf", max_length=200)
    unterschrieben_am: date


@router.post("/vertragsdokumente/{zid}/upload")
def upload(zid: str, data: UploadIn, user: dict = Depends(require_admin)):
    try:
        roh = base64.b64decode(data.datei_base64.split(",")[-1], validate=True)
    except Exception:
        raise HTTPException(400, "Die Datei konnte nicht gelesen werden.")
    if len(roh) > MAX_DATEI:
        raise HTTPException(400, "Die Datei ist zu groß (maximal 6 MB).")
    if roh.startswith(b"%PDF"):
        typ = "application/pdf"
    elif roh.startswith(b"\x89PNG\r\n\x1a\n"):
        typ = "image/png"
    elif roh.startswith(b"\xff\xd8\xff"):
        typ = "image/jpeg"
    else:
        raise HTTPException(400, "Bitte den unterschriebenen Vertrag als PDF (oder Foto als PNG/JPG) hochladen.")
    if data.unterschrieben_am > date.today():
        raise HTTPException(400, "Das Unterschriftsdatum liegt in der Zukunft.")
    name = "".join(c for c in data.datei_name if c.isalnum() or c in "._- ")[:120] or "Vertrag"
    try:
        with tx("admin") as cur:
            cur.execute("""UPDATE vertragsdokumente SET datei=%s, datei_typ=%s, datei_name=%s, unterschrieben_am=%s, hochgeladen_am=now() WHERE id=%s
                           RETURNING art, kunden_id, partner_id""", (roh, typ, name, data.unterschrieben_am, zid))
            r = cur.fetchone()
            if not r:
                raise _404()
            if r["art"] == "handelsvertreter":
                cur.execute("UPDATE vertriebspartner SET vereinbarung_am=%s WHERE id=%s", (data.unterschrieben_am, r["partner_id"]))
            audit(cur, user, "vertrag_unterschrieben_abgelegt", r["kunden_id"], {"art": r["art"], "datum": str(data.unterschrieben_am)})
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"ok": True}


@router.get("/vertragsdokumente/{zid}/datei")
def datei(zid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT datei, datei_typ, datei_name FROM vertragsdokumente WHERE id=%s", (zid,))
            r = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise _404()
    if not r or r["datei"] is None:
        raise _404()
    return Response(bytes(r["datei"]), media_type=r["datei_typ"], headers={"Content-Disposition": f'inline; filename="{r["datei_name"]}"', "X-Content-Type-Options": "nosniff"})


@router.delete("/vertragsdokumente/{zid}")
def loeschen(zid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM vertragsdokumente WHERE id=%s RETURNING art, kunden_id", (zid,))
            r = cur.fetchone()
            if not r:
                raise _404()
            audit(cur, user, "vertrag_geloescht", r["kunden_id"], {"art": r["art"]})
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"ok": True}


# ---------------------------------------------------------------- Telefonleitfaden für Vertriebler
@vertrieb.get("/telefonleitfaden.pdf")
def telefonleitfaden(user: dict = Depends(require_vertrieb)):
    return FileResponse(vertraege.DIR / "telefonleitfaden.pdf", media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="Markentrix-Telefonleitfaden-Kaltakquise.pdf"', "Cache-Control": "private, no-store"})
