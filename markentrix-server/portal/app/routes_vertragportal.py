"""Verträge im Portal: Kunden bestätigen den Referenzvertrag, Vertriebler den Handelsvertretervertrag direkt online (einfache elektronische Signatur
mit Protokoll, wie beim AVV). Dazu die Einarbeitungs-Checkliste und der Telefonleitfaden als durchsuchbarer Text für Vertriebler."""
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field
from pypdf import PdfReader

from . import mailer, rechtstexte, vertraege
from .db import tx
from .routes_vertraege import SPALTEN, _basis, _pdf
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_inhaber, require_vertrieb

kunde = APIRouter(prefix="/api/kunde")
vertrieb = APIRouter(prefix="/api/vertrieb")
OFFEN = "gesendet_am IS NOT NULL AND unterschrieben_am IS NULL AND datei IS NULL AND widerrufen_am IS NULL"


def _404():
    return HTTPException(404, "Nicht gefunden.")


class Antworten(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    ort: str = Field(min_length=2, max_length=100)
    akzeptiert: bool
    angaben: dict = Field(default_factory=dict)


def _bestaetigen(zid: str, art: str, eigen: str, eigen_id, data: Antworten, request: Request, user: dict) -> dict:
    """Gemeinsamer Ablauf: Antworten prüfen, Vertrag ausfüllen, Protokollseite anhängen, ablegen, Team informieren."""
    if not data.akzeptiert:
        raise HTTPException(400, "Bitte bestätige, dass du den Vertrag gelesen hast und die Angaben stimmen.")
    rate_limit("vertragok:" + str(eigen_id), 5, 600)
    name, ort = " ".join(data.name.split()), " ".join(data.ort.split())
    a = data.angaben if isinstance(data.angaben, dict) else {}
    if art == "referenz":
        werte, haken, sauber = vertraege.referenz_online(a, ort, name)
        if not sauber["elemente"] and not sauber["kanaele"]:
            raise HTTPException(400, "Bitte wähle mindestens ein Element und einen Kanal, oder lehne die Referenz ab, indem du den Vertrag nicht bestätigst.")
        if sauber["elemente"] and not sauber["kanaele"]:
            raise HTTPException(400, "Bitte wähle mindestens einen Kanal, in dem die Elemente gezeigt werden dürfen.")
    else:
        werte, haken, sauber = vertraege.handelsvertreter_online(a, ort, name)
        if not a.get("beauftragung") in ("haupt", "neben"):
            raise HTTPException(400, "Bitte wähle, ob du im Haupt- oder im Nebenberuf tätig bist.")
        if not sauber["strasse"] or not sauber["ort_anschrift"]:
            raise HTTPException(400, "Bitte trage deine Anschrift (Straße, PLZ und Ort) ein.")
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    zeit = jetzt.strftime("%d.%m.%Y, %H:%M Uhr")
    try:
        with tx("system") as cur:
            cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE id=%s AND {eigen}=%s AND art=%s AND {OFFEN}", (zid, eigen_id, art))
            z = cur.fetchone()
            if not z:
                raise _404()
            pdf_roh, dateiname, _m, _a = _pdf(cur, z, (werte, haken))
            alle_werte = {**_basis(cur, z)[0], **werte}
            hashwert = vertraege.pruefsumme(art, alle_werte, haken)
            firma = rechtstexte.firma(cur)
            gegen = ""
            if z["gesendet_am"]:
                gegen = (f"Markentrix hat den Vertrag am {z['gesendet_am'].astimezone(ZoneInfo('Europe/Berlin')):%d.%m.%Y um %H:%M Uhr} an {z['gesendet_an'] or 'den Empfänger'} versendet und damit seine Vertragserklärung abgegeben "
                         "(Name sowie Ort und Datum von Markentrix sind im Vertrag eingetragen).")
            pdf_fertig = vertraege.mit_protokoll(pdf_roh, art, firma, name, user["email"], zeit, client_ip(request), hashwert, gegen)
            cur.execute("""UPDATE vertragsdokumente SET datei=%s, datei_typ='application/pdf', datei_name=%s, unterschrieben_am=%s, hochgeladen_am=now(), online_am=now(),
                                  online_name=%s, online_email=%s, online_ip=%s, online_hash=%s, antworten=%s::jsonb WHERE id=%s""",
                        (pdf_fertig, dateiname.replace(".pdf", "-online-bestaetigt.pdf"), jetzt.date(), name, user["email"], client_ip(request), hashwert, json.dumps(sauber), zid))
            if art == "handelsvertreter":
                cur.execute("UPDATE vertriebspartner SET vereinbarung_am=%s WHERE id=%s", (jetzt.date(), eigen_id))
                cur.execute("SELECT name FROM vertriebspartner WHERE id=%s", (eigen_id,))
                wer, link = cur.fetchone()["name"], "/admin#partner/" + str(eigen_id)
            else:
                cur.execute("SELECT firma FROM kunden WHERE id=%s", (eigen_id,))
                wer, link = cur.fetchone()["firma"], "/admin#kunde/" + str(eigen_id)
            audit(cur, user, "vertrag_online_bestaetigt", eigen_id if art == "referenz" else None, {"art": art, "name": name, "hash": hashwert})
            an = admin_empfaenger(cur)
    except errors.InvalidTextRepresentation:
        raise _404()
    for ziel, fn in ((user["email"], lambda: mailer.vertrag_kopie(user["email"], name, art, pdf_fertig, dateiname)), (an, lambda: mailer.vertrag_online_team(an, wer, art, name, link))):
        try:
            if ziel:
                fn()
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True}


# ---------------------------------------------------------------- Kunde: Referenzvertrag
@kunde.get("/vertraege")
def kunde_liste(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute(f"""SELECT id, art, gesendet_am, unterschrieben_am, online_am, widerrufen_am, antworten, datei IS NOT NULL AS hat_datei, ({OFFEN}) AS offen
                        FROM vertragsdokumente WHERE kunden_id=%s AND art='referenz' AND (gesendet_am IS NOT NULL OR datei IS NOT NULL) ORDER BY erstellt_am DESC""", (user["kunden_id"],))
        return cur.fetchall()


@kunde.get("/vertraege/{zid}/vorlage.pdf")
def kunde_vorlage(zid: str, user: dict = Depends(require_inhaber)):
    try:
        with tx("system") as cur:
            cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE id=%s AND kunden_id=%s AND art='referenz' AND {OFFEN}", (zid, user["kunden_id"]))
            z = cur.fetchone()
            if not z:
                raise _404()
            pdf, name, _m, _a = _pdf(cur, z)
    except errors.InvalidTextRepresentation:
        raise _404()
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"', "Cache-Control": "private, no-store"})


@kunde.get("/vertraege/{zid}/datei")
def kunde_datei(zid: str, user: dict = Depends(require_inhaber)):
    try:
        with tx("system") as cur:
            cur.execute("SELECT datei, datei_typ, datei_name FROM vertragsdokumente WHERE id=%s AND kunden_id=%s AND art='referenz'", (zid, user["kunden_id"]))
            r = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise _404()
    if not r or r["datei"] is None:
        raise _404()
    return Response(bytes(r["datei"]), media_type=r["datei_typ"], headers={"Content-Disposition": f'inline; filename="{r["datei_name"]}"', "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@kunde.post("/vertraege/{zid}/bestaetigen")
def kunde_bestaetigen(zid: str, data: Antworten, request: Request, user: dict = Depends(require_inhaber)):
    return _bestaetigen(zid, "referenz", "kunden_id", user["kunden_id"], data, request, user)


class WiderrufIn(BaseModel):
    hinweis: str = Field(default="", max_length=1000)


@kunde.post("/vertraege/{zid}/widerrufen")
def kunde_widerrufen(zid: str, data: WiderrufIn, user: dict = Depends(require_inhaber)):
    """Der Kunde nimmt seine Referenz-Freigabe jederzeit zurück (§ 7 Referenzvertrag), ohne Begründung."""
    try:
        with tx("system") as cur:
            cur.execute("""UPDATE vertragsdokumente SET widerrufen_am=now() WHERE id=%s AND kunden_id=%s AND art='referenz' AND unterschrieben_am IS NOT NULL AND widerrufen_am IS NULL RETURNING id""",
                        (zid, user["kunden_id"]))
            if not cur.fetchone():
                raise _404()
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (user["kunden_id"],))
            firma = cur.fetchone()["firma"]
            audit(cur, user, "referenz_widerrufen", user["kunden_id"], {"hinweis": data.hinweis[:300]})
            an = admin_empfaenger(cur)
    except errors.InvalidTextRepresentation:
        raise _404()
    if an:
        try:
            mailer.referenz_widerruf_team(an, firma, " ".join(data.hinweis.split()), "/admin#kunde/" + str(user["kunden_id"]))
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True}


# ---------------------------------------------------------------- Vertriebler: Handelsvertretervertrag
@vertrieb.get("/vertrag")
def partner_vertrag(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute(f"""SELECT id, art, gesendet_am, unterschrieben_am, online_am, datei IS NOT NULL AS hat_datei, ({OFFEN}) AS offen
                        FROM vertragsdokumente WHERE partner_id=%s AND art='handelsvertreter' AND (gesendet_am IS NOT NULL OR datei IS NOT NULL) ORDER BY erstellt_am DESC""", (user["vertriebspartner_id"],))
        zeilen = cur.fetchall()
        cur.execute("SELECT name, email FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        p = cur.fetchone()
    return {"dokumente": zeilen, "name": p["name"], "email": p["email"]}


@vertrieb.get("/vertrag/{zid}/vorlage.pdf")
def partner_vorlage(zid: str, user: dict = Depends(require_vertrieb)):
    try:
        with tx("system") as cur:
            cur.execute(f"SELECT {SPALTEN} FROM vertragsdokumente WHERE id=%s AND partner_id=%s AND art='handelsvertreter' AND {OFFEN}", (zid, user["vertriebspartner_id"]))
            z = cur.fetchone()
            if not z:
                raise _404()
            pdf, name, _m, _a = _pdf(cur, z)
    except errors.InvalidTextRepresentation:
        raise _404()
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"', "Cache-Control": "private, no-store"})


@vertrieb.get("/vertrag/{zid}/datei")
def partner_datei(zid: str, user: dict = Depends(require_vertrieb)):
    try:
        with tx("system") as cur:
            cur.execute("SELECT datei, datei_typ, datei_name FROM vertragsdokumente WHERE id=%s AND partner_id=%s AND art='handelsvertreter'", (zid, user["vertriebspartner_id"]))
            r = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise _404()
    if not r or r["datei"] is None:
        raise _404()
    return Response(bytes(r["datei"]), media_type=r["datei_typ"], headers={"Content-Disposition": f'inline; filename="{r["datei_name"]}"', "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@vertrieb.post("/vertrag/{zid}/bestaetigen")
def partner_bestaetigen(zid: str, data: Antworten, request: Request, user: dict = Depends(require_vertrieb)):
    return _bestaetigen(zid, "handelsvertreter", "partner_id", user["vertriebspartner_id"], data, request, user)


# ---------------------------------------------------------------- Einarbeitung
def einarbeitung(cur, pid) -> list:
    cur.execute("SELECT iban_hinterlegt, vereinbarung_am, leitfaden_gelesen_am FROM vertriebspartner WHERE id=%s", (pid,))
    p = cur.fetchone()
    cur.execute("SELECT bool_or(totp_aktiv) AS zf FROM benutzer WHERE vertriebspartner_id=%s", (pid,))
    zf = bool(cur.fetchone()["zf"])
    cur.execute("SELECT count(*) AS n FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=%s AND a.art='anruf'", (pid,))
    anrufe = cur.fetchone()["n"]
    return [{"code": "vertrag", "text": "Handelsvertretervertrag unterschrieben", "erledigt": bool(p["vereinbarung_am"]), "link": "#vertrag"},
            {"code": "leitfaden", "text": "Telefonleitfaden gelesen", "erledigt": bool(p["leitfaden_gelesen_am"]), "link": "#leitfaden"},
            {"code": "zwei_faktor", "text": "Zwei-Faktor-Anmeldung eingerichtet", "erledigt": zf, "link": "#konto"},
            {"code": "iban", "text": "Bankverbindung für die Provision hinterlegt", "erledigt": bool(p["iban_hinterlegt"]), "link": "#konto"},
            {"code": "anruf", "text": "Ersten Anruf im Portal festgehalten", "erledigt": anrufe > 0, "link": "#heute"}]


@vertrieb.get("/einarbeitung")
def meine_einarbeitung(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        punkte = einarbeitung(cur, user["vertriebspartner_id"])
    return {"punkte": punkte, "fertig": all(x["erledigt"] for x in punkte)}


@vertrieb.post("/einarbeitung/leitfaden-gelesen")
def leitfaden_gelesen(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("UPDATE vertriebspartner SET leitfaden_gelesen_am = COALESCE(leitfaden_gelesen_am, now()) WHERE id=%s", (user["vertriebspartner_id"],))
    return {"ok": True}


# ---------------------------------------------------------------- Telefonleitfaden als Text
_TEXT: list | None = None


@vertrieb.get("/telefonleitfaden-text")
def leitfaden_text(user: dict = Depends(require_vertrieb)):
    """Seitenweiser Text des Leitfadens zum Durchsuchen im Portal (wird einmal gelesen und gemerkt)."""
    global _TEXT
    if _TEXT is None:
        r = PdfReader(io.BytesIO((vertraege.DIR / "telefonleitfaden.pdf").read_bytes()))
        _TEXT = [{"seite": i + 1, "text": (s.extract_text() or "").strip()} for i, s in enumerate(r.pages)]
    return {"seiten": _TEXT}


# ---------------------------------------------------------------- Tägliche Nachfass-Erinnerung (Einstellung des Vertrieblers)
@vertrieb.get("/erinnerung")
def erinnerung_lesen(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("SELECT erinnerung_mail FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        return {"an": cur.fetchone()["erinnerung_mail"]}


class ErinnerungIn(BaseModel):
    an: bool


@vertrieb.put("/erinnerung")
def erinnerung_setzen(data: ErinnerungIn, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("UPDATE vertriebspartner SET erinnerung_mail=%s WHERE id=%s", (data.an, user["vertriebspartner_id"]))
    return {"ok": True}
