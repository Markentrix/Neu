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
SPALTEN = ("id, art, kunden_id, partner_id, daten, erstellt_am, gesendet_am, gesendet_an, unterschrieben_am, datei_name, hochgeladen_am, datei IS NOT NULL AS hat_datei, "
           "erinnerungen, erinnert_am, online_am, online_name, widerrufen_am")


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


def _basis(cur, z: dict) -> tuple:
    """Formularwerte, Haken, Standard-Empfänger und Anrede für einen Vertrag, wie der Admin ihn angelegt hat."""
    d = z["daten"]
    if z["art"] == "referenz":
        cur.execute("SELECT firma, ansprechpartner, strasse, plz, ort, email FROM kunden WHERE id=%s", (z["kunden_id"],))
        k = cur.fetchone()
        return referenz_werte(k, d), [], k["email"], k["ansprechpartner"]
    cur.execute("SELECT name, email FROM vertriebspartner WHERE id=%s", (z["partner_id"],))
    p = cur.fetchone()
    werte, haken = handelsvertreter_werte(p, d, rechtstexte.firma(cur))
    return werte, haken, (_kurz(d.get("mail")) or p["email"]), (_kurz(d.get("name")) or p["name"])


def _pdf(cur, z: dict, online: tuple | None = None) -> tuple:
    """online = (werte, haken) aus der Bestätigung im Portal; sie ergänzen die Werte des Admins, die Haken ersetzen dessen Vorbelegung."""
    werte, haken, mail, anrede = _basis(cur, z)
    if online:
        werte = {**werte, **online[0]}
        haken = online[1]
    return vertraege.ausfuellen(z["art"], werte, haken), vertraege.DATEINAME[z["art"]] + ".pdf", mail, anrede


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


# ---------------------------------------------------------------- Übersicht „Was fehlt noch?“, Referenzliste, Einarbeitung (Admin)
def _stand(z: dict | None) -> dict:
    """Kurzstand eines Vertragsdokuments: keins / erstellt / gesendet (offen) / unterschrieben / widerrufen."""
    if not z:
        return {"stand": "keins"}
    if z["widerrufen_am"]:
        return {"stand": "widerrufen", "id": z["id"]}
    if z["unterschrieben_am"] or z["hat_datei"]:
        return {"stand": "unterschrieben", "id": z["id"], "am": z["unterschrieben_am"], "online": bool(z["online_am"])}
    if z["gesendet_am"]:
        return {"stand": "gesendet", "id": z["id"], "am": z["gesendet_am"], "erinnerungen": z["erinnerungen"]}
    return {"stand": "erstellt", "id": z["id"]}


@router.get("/vertragsdokumente/uebersicht")
def uebersicht(user: dict = Depends(require_admin)):
    """Je aktivem Kunden AVV und Referenzvertrag, je Vertriebler der Handelsvertretervertrag und die Einarbeitung."""
    from .routes_vertragportal import einarbeitung
    with tx("admin") as cur:
        cur.execute(f"""SELECT DISTINCT ON (kunden_id) kunden_id, {SPALTEN} FROM vertragsdokumente WHERE art='referenz' ORDER BY kunden_id, erstellt_am DESC""")
        ref = {str(r["kunden_id"]): r for r in cur.fetchall()}
        cur.execute(f"""SELECT DISTINCT ON (partner_id) partner_id, {SPALTEN} FROM vertragsdokumente WHERE art='handelsvertreter' ORDER BY partner_id, erstellt_am DESC""")
        hv = {str(r["partner_id"]): r for r in cur.fetchall()}
        cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.status,
                              EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL) AS avv_ok,
                              EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NULL AND a.portal_freigabe_am IS NOT NULL) AS avv_im_portal
                       FROM kunden k WHERE k.status IN ('onboarding','aktiv','pausiert') ORDER BY k.firma LIMIT 500""")
        kunden = [{**k, "referenz": _stand(ref.get(str(k["id"])))} for k in cur.fetchall()]
        cur.execute("SELECT id, name, status, vereinbarung_am FROM vertriebspartner WHERE status IN ('anfrage','aktiv','pausiert') ORDER BY name LIMIT 500")
        partner = []
        for p in cur.fetchall():
            e = einarbeitung(cur, p["id"])
            partner.append({"id": p["id"], "name": p["name"], "status": p["status"], "vertrag": _stand(hv.get(str(p["id"]))), "vereinbarung_am": p["vereinbarung_am"],
                            "einarbeitung_erledigt": sum(1 for x in e if x["erledigt"]), "einarbeitung_gesamt": len(e), "einarbeitung_offen": [x["text"] for x in e if not x["erledigt"]]})
    offen = {"avv": sum(1 for k in kunden if not k["avv_ok"]), "referenz_gesendet": sum(1 for k in kunden if k["referenz"]["stand"] == "gesendet"),
             "vertrag": sum(1 for p in partner if p["vertrag"]["stand"] != "unterschrieben" and not p["vereinbarung_am"]), "einarbeitung": sum(1 for p in partner if p["einarbeitung_erledigt"] < p["einarbeitung_gesamt"])}
    return {"kunden": kunden, "partner": partner, "offen": offen}


@router.get("/vertragsdokumente/referenzen")
def referenzliste(user: dict = Depends(require_admin)):
    """Alle unterschriebenen Referenzverträge mit dem, was freigegeben wurde. Widerrufene stehen getrennt."""
    with tx("admin") as cur:
        cur.execute("""SELECT d.id, d.kunden_id, k.firma, k.kundennummer, d.unterschrieben_am, d.online_am, d.widerrufen_am, d.antworten, d.daten, d.datei IS NOT NULL AS hat_datei
                       FROM vertragsdokumente d JOIN kunden k ON k.id=d.kunden_id
                       WHERE d.art='referenz' AND (d.unterschrieben_am IS NOT NULL OR d.datei IS NOT NULL) ORDER BY d.widerrufen_am IS NOT NULL, d.unterschrieben_am DESC NULLS LAST LIMIT 500""")
        zeilen = cur.fetchall()
    for z in zeilen:
        a = z.pop("antworten") or {}
        d = z.pop("daten") or {}
        z["projekt"] = d.get("projekt") or ""
        z["elemente"] = [{"code": c, "name": vertraege.REF_ELEMENTE[c], "text": t} for c, t in (a.get("elemente") or {}).items() if c in vertraege.REF_ELEMENTE]
        z["kanaele"] = [vertraege.REF_KANAELE[c] for c in a.get("kanaele") or [] if c in vertraege.REF_KANAELE]
        z["personen"] = bool(a.get("personen_zeigen"))
        z["einschraenkungen"] = a.get("einschraenkungen") or ""
        z["strukturiert"] = bool(a)
    return {"aktiv": [z for z in zeilen if not z["widerrufen_am"]], "widerrufen": [z for z in zeilen if z["widerrufen_am"]]}


class WiderrufAdminIn(BaseModel):
    widerrufen: bool = True


@router.post("/vertragsdokumente/{zid}/widerruf")
def widerruf_setzen(zid: str, data: WiderrufAdminIn, user: dict = Depends(require_admin)):
    """Widerruf, der per Mail oder Telefon kam, im Portal festhalten (oder zurücknehmen, wenn er irrtümlich eingetragen wurde)."""
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE vertragsdokumente SET widerrufen_am = CASE WHEN %s THEN COALESCE(widerrufen_am, now()) END WHERE id=%s AND art='referenz' RETURNING kunden_id", (data.widerrufen, zid))
            r = cur.fetchone()
            if not r:
                raise _404()
            audit(cur, user, "referenz_widerruf_vermerkt" if data.widerrufen else "referenz_widerruf_zurueck", r["kunden_id"], {})
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"ok": True}


@router.get("/vertrieb/partner/{pid}/einarbeitung")
def partner_einarbeitung(pid: str, user: dict = Depends(require_admin)):
    from .routes_vertragportal import einarbeitung
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM vertriebspartner WHERE id=%s", (pid,))
            if not cur.fetchone():
                raise _404()
            return {"punkte": einarbeitung(cur, pid)}
    except errors.InvalidTextRepresentation:
        raise _404()
