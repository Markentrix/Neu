"""Team-Zugänge eines Kunden (Rollen) und Branding (Logo, Farbe)."""
import base64
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from psycopg import errors
from pydantic import BaseModel, Field

from . import zugang
from .db import tx
from .security import EMAIL_RE, audit, rate_limit, require_admin, require_inhaber, require_kunde

router = APIRouter(prefix="/api/kunde")
admin_router = APIRouter(prefix="/api/admin")

ROLLEN = ("inhaber", "mitarbeiter", "nur_lesen", "empfang")
MAX_LOGO = 400 * 1024


# ------------------------------------------------------------------ Team (Kundenseite)
@router.get("/team")
def team(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("""SELECT b.id, b.email, b.name, b.kunden_rolle, b.aktiv, b.zugang_bis, b.letzter_login, b.passwort_hash IS NOT NULL AS angemeldet,
                              b.website_mitarbeiter_id, m.name AS person
                       FROM benutzer b LEFT JOIN website_mitarbeiter m ON m.id = b.website_mitarbeiter_id WHERE b.kunden_id=%s ORDER BY b.erstellt_am""", (user["kunden_id"],))
        return cur.fetchall()


def _person_pruefen(cur, kid, wert):
    """Person der Terminbuchung, mit der ein Zugang verknüpft wird (leer = keine Bindung)."""
    if not wert:
        return None
    try:
        cur.execute("SELECT id FROM website_mitarbeiter WHERE id=%s AND kunden_id=%s", (wert, kid))
    except Exception:
        raise HTTPException(400, "Diese Person gibt es nicht.")
    r = cur.fetchone()
    if not r:
        raise HTTPException(400, "Diese Person gibt es nicht.")
    return r["id"]


class EinladenIn(BaseModel):
    email: str = Field(max_length=254)
    name: str | None = Field(default=None, max_length=120)
    kunden_rolle: str = "mitarbeiter"
    zugang_bis: date | None = None             # Vertretung: Zugang endet automatisch nach diesem Tag
    website_mitarbeiter_id: str = ""           # verknüpft den Zugang mit einer Person der Terminbuchung: sieht nur deren Termine


@router.post("/team/einladen")
def einladen(data: EinladenIn, user: dict = Depends(require_inhaber)):
    rate_limit("team:" + str(user["id"]), 20, 3600)
    if data.kunden_rolle not in ROLLEN:
        raise HTTPException(400, "Unbekannte Rolle.")
    if not EMAIL_RE.match(data.email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    with tx("system") as cur:
        link = zugang.link_erzeugen(cur, data.email, data.name, "kunde", kunden_id=user["kunden_id"], kunden_rolle=data.kunden_rolle)
        person = _person_pruefen(cur, user["kunden_id"], data.website_mitarbeiter_id)
        cur.execute("UPDATE benutzer SET kunden_rolle=%s, zugang_bis=%s, website_mitarbeiter_id=%s WHERE lower(email)=lower(%s) AND kunden_id=%s", (data.kunden_rolle, data.zugang_bis, person, data.email.strip(), user["kunden_id"]))
        audit(cur, user, "team_eingeladen", user["kunden_id"], {"rolle": data.kunden_rolle})
    mail = zugang.per_mail(data.email, data.name, link, "kunde")
    return {"ok": True, "gemailt": bool(mail and mail.get("gesendet")), "einladungslink": None if (mail and mail.get("gesendet")) else link}


class MitgliedIn(BaseModel):
    aktiv: bool | None = None
    kunden_rolle: str | None = None
    zugang_bis: date | None = None
    website_mitarbeiter_id: str | None = None


@router.patch("/team/{bid}")
def mitglied(bid: str, data: MitgliedIn, user: dict = Depends(require_inhaber)):
    if data.kunden_rolle is not None and data.kunden_rolle not in ROLLEN:
        raise HTTPException(400, "Unbekannte Rolle.")
    try:
        with tx("system") as cur:
            cur.execute("SELECT id, kunden_rolle, aktiv FROM benutzer WHERE id=%s AND kunden_id=%s", (bid, user["kunden_id"]))
            m = cur.fetchone()
            if not m:
                raise HTTPException(404, "Zugang nicht gefunden.")
            neue_rolle = data.kunden_rolle or m["kunden_rolle"]
            neu_aktiv = m["aktiv"] if data.aktiv is None else data.aktiv
            if str(m["id"]) == str(user["id"]) and (not neu_aktiv or neue_rolle != "inhaber"):
                raise HTTPException(400, "Du kannst dir selbst weder den Zugang sperren noch die Rolle ändern.")
            cur.execute("UPDATE benutzer SET kunden_rolle=%s, aktiv=%s, gesperrt_manuell=%s WHERE id=%s", (neue_rolle, neu_aktiv, not neu_aktiv, bid))
            if "website_mitarbeiter_id" in data.model_fields_set:
                cur.execute("UPDATE benutzer SET website_mitarbeiter_id=%s WHERE id=%s", (_person_pruefen(cur, user["kunden_id"], data.website_mitarbeiter_id), bid))
            if "zugang_bis" in data.model_fields_set:
                cur.execute("UPDATE benutzer SET zugang_bis=%s WHERE id=%s", (data.zugang_bis, bid))
            if not neu_aktiv:
                cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s", (bid,))
            audit(cur, user, "team_geaendert", user["kunden_id"], {"rolle": neue_rolle, "aktiv": neu_aktiv})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Zugang nicht gefunden.")
    return {"ok": True}


# ------------------------------------------------------------------ Branding
def _logo_antwort(row):
    if not row or not row["logo"]:
        raise HTTPException(404, "Kein Logo hinterlegt.")
    return Response(bytes(row["logo"]), media_type=row["logo_typ"], headers={"Cache-Control": "private, max-age=300"})


@router.get("/logo")
def logo(user: dict = Depends(require_kunde)):
    with tx("system") as cur:
        cur.execute("SELECT logo, logo_typ FROM kunden WHERE id=%s", (user["kunden_id"],))
        return _logo_antwort(cur.fetchone())


@admin_router.get("/kunden/{kid}/logo")
def logo_admin(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT logo, logo_typ FROM kunden WHERE id=%s", (kid,))
            return _logo_antwort(cur.fetchone())
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")


class BrandingIn(BaseModel):
    farbe: str | None = Field(default=None, max_length=7)
    logo_base64: str | None = Field(default=None, max_length=700_000)
    logo_entfernen: bool = False


@admin_router.put("/kunden/{kid}/branding")
def branding(kid: str, data: BrandingIn, user: dict = Depends(require_admin)):
    if data.farbe and not re.fullmatch(r"#[0-9a-fA-F]{6}", data.farbe):
        raise HTTPException(400, "Die Farbe muss als #RRGGBB angegeben werden.")
    logo, typ = None, None
    if data.logo_base64:
        try:
            logo = base64.b64decode(data.logo_base64.split(",")[-1], validate=True)
        except Exception:
            raise HTTPException(400, "Das Logo konnte nicht gelesen werden.")
        if len(logo) > MAX_LOGO:
            raise HTTPException(400, "Das Logo ist zu groß (maximal 400 KB).")
        if logo.startswith(b"\x89PNG\r\n\x1a\n"):
            typ = "image/png"
        elif logo.startswith(b"\xff\xd8\xff"):
            typ = "image/jpeg"
        else:
            raise HTTPException(400, "Bitte ein Logo als PNG oder JPG hochladen.")
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE kunden SET branding_farbe=%s WHERE id=%s", (data.farbe or None, kid))
            if cur.rowcount == 0:
                raise HTTPException(404, "Kunde nicht gefunden.")
            if logo:
                cur.execute("UPDATE kunden SET logo=%s, logo_typ=%s WHERE id=%s", (logo, typ, kid))
            elif data.logo_entfernen:
                cur.execute("UPDATE kunden SET logo=NULL, logo_typ=NULL WHERE id=%s", (kid,))
            audit(cur, user, "branding_geaendert", kid)
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    return {"ok": True}
