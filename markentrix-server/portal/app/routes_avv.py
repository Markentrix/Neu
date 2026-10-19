"""AVV pro Kunde: erzeugen, per Mail senden, unterschriebene Fassung ablegen; Kunde sieht seine abgelegten Verträge."""
import base64
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import avv, einstellungen, mailer, rechtstexte
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin, require_inhaber

router = APIRouter(prefix="/api/admin")
kunde_router = APIRouter(prefix="/api/kunde")

MAX_DATEI = 6 * 1024 * 1024
LISTE = "id, version, erstellt_am, gesendet_am, unterschrieben_am, datei_name, hochgeladen_am, portal_freigabe_am, online_bestaetigt_am, online_bestaetigt_name, (datei IS NOT NULL) AS hat_datei"


def _404():
    return HTTPException(404, "Nicht gefunden.")


def _antwort(daten: bytes, typ: str, name: str):
    return Response(daten, media_type=typ, headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------------------------------------------------------------- Einstellung: Unterauftragsverarbeiter
class AvvEinstIn(BaseModel):
    unterauftragnehmer: str = Field(default="", max_length=3000)


@router.get("/einstellungen/avv")
def einst_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        e = einstellungen.lesen(cur, "avv")
    standard = "\n".join(" | ".join(z) for z in avv.STANDARD_UNTERAUFTRAGNEHMER)
    return {"unterauftragnehmer": e.get("unterauftragnehmer", ""), "standard": standard}


@router.put("/einstellungen/avv")
def einst_speichern(data: AvvEinstIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "avv", {"unterauftragnehmer": data.unterauftragnehmer.strip()})
        audit(cur, user, "einstellungen_avv")
    return {"ok": True}


# ---------------------------------------------------------------- Admin: pro Kunde
def avv_vorhanden(cur, kid) -> bool:
    cur.execute("SELECT 1 FROM avv WHERE kunden_id=%s AND datei IS NOT NULL AND unterschrieben_am IS NOT NULL LIMIT 1", (kid,))
    return cur.fetchone() is not None


@router.get("/kunden/{kid}/avv")
def liste(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise _404()
            cur.execute(f"SELECT {LISTE} FROM avv WHERE kunden_id=%s ORDER BY erstellt_am DESC", (kid,))
            return {"liste": cur.fetchall(), "vorhanden": avv_vorhanden(cur, kid)}
    except errors.InvalidTextRepresentation:
        raise _404()


@router.post("/kunden/{kid}/avv")
def erstellen(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise _404()
            cur.execute("INSERT INTO avv (kunden_id, version) VALUES (%s,%s) RETURNING id", (kid, avv.VERSION))
            r = cur.fetchone()
            audit(cur, user, "avv_erstellt", kid)
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"id": r["id"]}


def _pdf(cur, aid):
    cur.execute("SELECT kunden_id FROM avv WHERE id=%s", (aid,))
    a = cur.fetchone()
    if not a:
        raise _404()
    cur.execute("SELECT firma, rechtsform, strasse, plz, ort, email, ansprechpartner FROM kunden WHERE id=%s", (a["kunden_id"],))
    k = cur.fetchone()
    f = rechtstexte.firma(cur)
    unter = avv.unterauftragnehmer(einstellungen.lesen(cur, "avv").get("unterauftragnehmer"))
    return avv.avv_pdf(k, f, unter), k


@router.get("/avv/{aid}/vorlage.pdf")
def vorlage(aid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            daten, _k = _pdf(cur, aid)
    except errors.InvalidTextRepresentation:
        raise _404()
    return _antwort(daten, "application/pdf", "Auftragsverarbeitungsvertrag.pdf")


@router.post("/avv/{aid}/senden")
def senden(aid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            daten, k = _pdf(cur, aid)
    except errors.InvalidTextRepresentation:
        raise _404()
    an = (k.get("email") or "").strip()
    if not an:
        raise HTTPException(400, "Beim Kunden ist keine E-Mail-Adresse hinterlegt.")
    ok, fehler = mailer.avv(an, k.get("ansprechpartner"), daten)
    if not ok:
        raise HTTPException(400, "Die Mail konnte nicht gesendet werden: " + (fehler or "unbekannt"))
    with tx("admin") as cur:
        cur.execute("UPDATE avv SET gesendet_am=now() WHERE id=%s", (aid,))
        audit(cur, user, "avv_gesendet")
    return {"ok": True}


class UploadIn(BaseModel):
    datei_base64: str = Field(max_length=9_000_000)
    datei_name: str = Field(default="AVV-unterschrieben.pdf", max_length=200)
    unterschrieben_am: date


@router.post("/avv/{aid}/upload")
def upload(aid: str, data: UploadIn, user: dict = Depends(require_admin)):
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
        raise HTTPException(400, "Bitte den unterschriebenen AVV als PDF (oder Foto als PNG/JPG) hochladen.")
    if data.unterschrieben_am > date.today():
        raise HTTPException(400, "Das Unterschriftsdatum liegt in der Zukunft.")
    name = "".join(c for c in data.datei_name if c.isalnum() or c in "._- ")[:120] or "AVV"
    try:
        with tx("admin") as cur:
            cur.execute("""UPDATE avv SET datei=%s, datei_typ=%s, datei_name=%s, unterschrieben_am=%s, hochgeladen_am=now() WHERE id=%s RETURNING kunden_id""",
                        (roh, typ, name, data.unterschrieben_am, aid))
            r = cur.fetchone()
            if not r:
                raise _404()
            audit(cur, user, "avv_hochgeladen", r["kunden_id"], {"datum": str(data.unterschrieben_am)})
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"ok": True}


@router.get("/avv/{aid}/datei")
def datei(aid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT datei, datei_typ, datei_name FROM avv WHERE id=%s", (aid,))
            a = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise _404()
    if not a or not a["datei"]:
        raise _404()
    return _antwort(bytes(a["datei"]), a["datei_typ"], a["datei_name"] or "AVV")


@router.delete("/avv/{aid}")
def loeschen(aid: str, user: dict = Depends(require_admin)):
    """Nur Entwürfe (ohne abgelegte Datei) lassen sich löschen; abgelegte Verträge bleiben erhalten."""
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM avv WHERE id=%s AND datei IS NULL RETURNING kunden_id", (aid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(400, "Nicht gefunden oder schon als unterschriebene Fassung abgelegt.")
            audit(cur, user, "avv_entwurf_geloescht", r["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise _404()
    return {"ok": True}


@router.get("/avv-fehlt")
def fehlt(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return fehlende(cur)


def fehlende(cur) -> list:
    cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.status, k.erstellt_am
                   FROM kunden k
                   WHERE k.status IN ('onboarding','aktiv','pausiert')
                     AND NOT EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL)
                   ORDER BY k.erstellt_am""")
    return cur.fetchall()


# ---------------------------------------------------------------- Kundenseite
@kunde_router.get("/avv")
def kunde_liste(user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute(f"SELECT {LISTE} FROM avv WHERE datei IS NOT NULL ORDER BY unterschrieben_am DESC")
        return cur.fetchall()


@kunde_router.get("/avv/{aid}/datei")
def kunde_datei(aid: str, user: dict = Depends(require_inhaber)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("SELECT datei, datei_typ, datei_name FROM avv WHERE id=%s AND datei IS NOT NULL", (aid,))
            a = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise _404()
    if not a:
        raise _404()
    return _antwort(bytes(a["datei"]), a["datei_typ"], a["datei_name"] or "AVV")


# ---------------------------------------------------------------- Bestätigung per Klick im Portal
@router.post("/avv/{aid}/portal-freigeben")
def portal_freigeben(aid: str, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    """Gibt den AVV im Kundenportal zur Bestätigung frei und benachrichtigt den Kunden per Mail."""
    try:
        with tx("admin") as cur:
            cur.execute("""UPDATE avv SET portal_freigabe_am=now() WHERE id=%s AND datei IS NULL RETURNING kunden_id""", (aid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(400, "Nicht gefunden oder schon abgelegt.")
            cur.execute("SELECT email, ansprechpartner FROM kunden WHERE id=%s", (r["kunden_id"],))
            k = cur.fetchone()
            audit(cur, user, "avv_portal_freigegeben", r["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise _404()
    an = (k.get("email") or "").strip()
    if an:
        bg.add_task(mailer.avv_portal, an, k.get("ansprechpartner"))
    return {"ok": True, "gemailt": bool(an)}


@kunde_router.get("/avv-offen")
def kunde_offen(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        cur.execute("""SELECT id, version, portal_freigabe_am FROM avv
                       WHERE kunden_id=%s AND datei IS NULL AND portal_freigabe_am IS NOT NULL ORDER BY portal_freigabe_am DESC""", (kid,))
        return cur.fetchall()


def _eigener_avv(cur, aid, kid):
    cur.execute("SELECT id, kunden_id FROM avv WHERE id=%s AND kunden_id=%s AND datei IS NULL AND portal_freigabe_am IS NOT NULL", (aid, kid))
    if not cur.fetchone():
        raise _404()


@kunde_router.get("/avv-offen/{aid}/vorlage.pdf")
def kunde_vorlage(aid: str, user: dict = Depends(require_inhaber)):
    try:
        with tx("system") as cur:
            _eigener_avv(cur, aid, user["kunden_id"])
            daten, _k = _pdf(cur, aid)
    except errors.InvalidTextRepresentation:
        raise _404()
    return _antwort(daten, "application/pdf", "Auftragsverarbeitungsvertrag.pdf")


class BestaetigenIn(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    akzeptiert: bool


@kunde_router.post("/avv-offen/{aid}/bestaetigen")
def kunde_bestaetigen(aid: str, data: BestaetigenIn, request: Request, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    if not data.akzeptiert:
        raise HTTPException(400, "Bitte bestätige, dass du den Vertrag gelesen hast und vertretungsberechtigt bist.")
    rate_limit("avvok:" + str(user["kunden_id"]), 5, 600)
    kid = user["kunden_id"]
    name = " ".join(data.name.split())
    try:
        with tx("system") as cur:
            _eigener_avv(cur, aid, kid)
            cur.execute("SELECT firma, rechtsform, strasse, plz, ort, email, ansprechpartner FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            f = rechtstexte.firma(cur)
            unter = avv.unterauftragnehmer(einstellungen.lesen(cur, "avv").get("unterauftragnehmer"))
            jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
            hashwert = avv.text_hash(k, f, unter)
            pdf_bytes = avv.avv_pdf(k, f, unter, {"zeit": jetzt.strftime("%d.%m.%Y, %H:%M Uhr"), "name": name, "email": user["email"], "hash": hashwert})
            cur.execute("""UPDATE avv SET datei=%s, datei_typ='application/pdf', datei_name='AVV-online-bestaetigt.pdf', unterschrieben_am=%s, hochgeladen_am=now(),
                                  online_bestaetigt_am=now(), online_bestaetigt_name=%s, online_bestaetigt_email=%s, online_bestaetigt_ip=%s, online_bestaetigt_hash=%s
                           WHERE id=%s""", (pdf_bytes, jetzt.date(), name, user["email"], client_ip(request), hashwert, aid))
            audit(cur, user, "avv_online_bestaetigt", kid, {"name": name, "hash": hashwert})
            from .routes_zusammenarbeit import admin_empfaenger
            an = admin_empfaenger(cur)
            cur.execute("SELECT kundennummer FROM kunden WHERE id=%s", (kid,))
            nr = cur.fetchone()["kundennummer"]
    except errors.InvalidTextRepresentation:
        raise _404()
    if an:
        bg.add_task(mailer.avv_bestaetigt_team, an, k["firma"], nr, name, str(kid))
    return {"ok": True}
