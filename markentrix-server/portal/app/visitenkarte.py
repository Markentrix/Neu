"""Digitale Visitenkarte für das Markentrix-Team (Admins und Vertriebler): als .vcf-Datei, die sich mit einem Klick im Adressbuch speichern lässt.
Versand per E-Mail als Anhang (wie die Visitenkarte in Outlook) oder über „Teilen“ (z. B. WhatsApp) auf dem Handy. Gibt es nicht für Kunden."""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import mailer, rechtstexte
from .db import tx
from .routes_leadangebot import BLOCKIERT, EMAIL, _lead
from .routes_vertrieb import eigener_lead
from .security import audit, rate_limit, require_admin, require_vertrieb

router = APIRouter(prefix="/api")


class KarteIn(BaseModel):
    anzeigename: str = Field(default="", max_length=120)
    funktion: str = Field(default="", max_length=120)
    telefon: str = Field(default="", max_length=60)
    mobil: str = Field(default="", max_length=60)
    email: str = Field(default="", max_length=254)
    web: str = Field(default="", max_length=200)


class SendenIn(BaseModel):
    kanal: str = Field(pattern="^(mail|whatsapp|teilen|datei)$")
    an: str | None = Field(default=None, max_length=254)


def _esc(s) -> str:
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _falten(zeile: str) -> str:
    roh = zeile.encode()
    if len(roh) <= 74:
        return zeile
    teile, i = [], 0
    while i < len(roh):
        j = min(i + (74 if i == 0 else 73), len(roh))
        while j < len(roh) and (roh[j] & 0xC0) == 0x80:
            j -= 1
        teile.append(roh[i:j].decode())
        i = j
    return "\r\n ".join(teile)


def vcard(k: dict, f: dict) -> bytes:
    """vCard 3.0 (UTF-8): wird von Outlook, Apple Kontakte, Android und Gmail gelesen."""
    name = (k["anzeigename"] or "").strip() or "Markentrix"
    teile = name.rsplit(" ", 1)
    nachname, vorname = (teile[1], teile[0]) if len(teile) == 2 else (name, "")
    z = ["BEGIN:VCARD", "VERSION:3.0", "PRODID:-//Markentrix//Portal//DE", f"N:{_esc(nachname)};{_esc(vorname)};;;", f"FN:{_esc(name)}",
         f"ORG:{_esc(f.get('name') or 'Markentrix')}"]
    if k["funktion"]:
        z.append(f"TITLE:{_esc(k['funktion'])}")
    if k["telefon"]:
        z.append(f"TEL;TYPE=WORK,VOICE:{_esc(k['telefon'])}")
    if k["mobil"]:
        z.append(f"TEL;TYPE=CELL,VOICE:{_esc(k['mobil'])}")
    if k["email"]:
        z.append(f"EMAIL;TYPE=INTERNET,WORK:{_esc(k['email'])}")
    if k["web"]:
        web = k["web"] if re.match(r"^https?://", k["web"]) else "https://" + k["web"]
        z.append(f"URL:{_esc(web)}")
    if f.get("strasse") or f.get("ort"):
        z.append(f"ADR;TYPE=WORK:;;{_esc(f.get('strasse'))};{_esc(f.get('ort'))};;{_esc(f.get('plz'))};Deutschland")
    z += [f"REV:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}", "END:VCARD"]
    return ("\r\n".join(_falten(x) for x in z) + "\r\n").encode()


def _karte(cur, user: dict, rolle: str) -> tuple[dict, dict]:
    """Gespeicherte Angaben, sonst sinnvolle Vorgaben aus Konto und Firmendaten."""
    f = rechtstexte.firma(cur)
    cur.execute("SELECT anzeigename, funktion, telefon, mobil, email, web FROM visitenkarten WHERE benutzer_id=%s", (user["id"],))
    k = cur.fetchone()
    telefon = f["telefon"]
    if rolle == "vertrieb":
        cur.execute("SELECT name, telefon FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        p = cur.fetchone() or {}
        telefon = p.get("telefon") or ""
    standard = {"anzeigename": user.get("name") or (p.get("name") if rolle == "vertrieb" else "") or "", "funktion": "Vertrieb" if rolle == "vertrieb" else "Inhaber",
                "telefon": telefon or "", "mobil": "", "email": user["email"], "web": f["website"] or ""}
    if k:
        return {x: (k[x] if k[x] is not None else standard[x]) for x in standard}, f
    return standard, f


def _speichern(user, rolle, d: KarteIn):
    if d.email.strip() and not EMAIL.match(d.email.strip()):
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse eintragen.")
    if not d.anzeigename.strip():
        raise HTTPException(400, "Bitte den Namen eintragen, der auf der Karte stehen soll.")
    with tx("system") as cur:
        cur.execute("""INSERT INTO visitenkarten (benutzer_id, anzeigename, funktion, telefon, mobil, email, web) VALUES (%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (benutzer_id) DO UPDATE SET anzeigename=EXCLUDED.anzeigename, funktion=EXCLUDED.funktion, telefon=EXCLUDED.telefon, mobil=EXCLUDED.mobil,
                       email=EXCLUDED.email, web=EXCLUDED.web, geaendert_am=now()""",
                    (user["id"], d.anzeigename.strip(), d.funktion.strip(), d.telefon.strip(), d.mobil.strip(), d.email.strip(), d.web.strip()))
    return {"ok": True}


def _datei(user, rolle) -> Response:
    with tx("system") as cur:
        k, f = _karte(cur, user, rolle)
    dateiname = re.sub(r"[^A-Za-z0-9_-]+", "-", k["anzeigename"]).strip("-") or "Markentrix"
    return Response(vcard(k, f), media_type="text/vcard; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{dateiname}.vcf"'})


def _senden(cur, user, rolle, l: dict, d: SendenIn) -> dict:
    if l["status"] in BLOCKIERT:
        raise HTTPException(400, "An diesen Lead darf nichts gesendet werden (gesperrt, ohne Einwilligung, verloren oder ungültig).")
    k, f = _karte(cur, user, rolle)
    gesendet, grund, an = False, "", None
    if d.kanal == "mail":
        an = (d.an or l.get("email") or "").strip()
        if not EMAIL.match(an):
            raise HTTPException(400, "Für diesen Lead ist keine gültige E-Mail-Adresse hinterlegt.")
        rate_limit("visitenkarte:" + str(user["id"]), 60, 3600)
        gruss = f"Guten Tag {l['ansprechpartner']}," if l.get("ansprechpartner") else "Guten Tag,"
        text = (f"{gruss}\n\nschön, dass wir gesprochen haben. Wie versprochen sende ich Ihnen meine Kontaktdaten als digitale Visitenkarte im Anhang. "
                "Ein Klick auf die Datei genügt, dann können Sie die Daten direkt in Ihren Kontakten speichern.\n\n"
                f"Bei Fragen melden Sie sich jederzeit gern.\n\nViele Grüße\n{k['anzeigename']}" + (f"\n{k['funktion']}" if k["funktion"] else "") + f"\n{f['name'] or 'Markentrix'}"
                + (f"\n{k['telefon']}" if k["telefon"] else "") + (f"\n{k['mobil']}" if k["mobil"] else ""))
        dateiname = re.sub(r"[^A-Za-z0-9_-]+", "-", k["anzeigename"]).strip("-") or "Markentrix"
        gesendet, grund = mailer.senden(an, f"Meine Visitenkarte – {f['name'] or 'Markentrix'}", text, (f"{dateiname}.vcf", vcard(k, f), "text/vcard"),
                                        reply_to=k["email"] or None, von_name=f"{k['anzeigename']} | {f['name'] or 'Markentrix'}", art="visitenkarte")
    wie = {"mail": "per E-Mail gesendet" if gesendet else "per E-Mail nicht gesendet", "whatsapp": "per WhatsApp geschickt", "teilen": "über „Teilen“ geschickt", "datei": "als Datei heruntergeladen"}[d.kanal]
    cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s)",
                (l["id"], "mail_gesendet" if gesendet else "notiz", f"Visitenkarte {wie}" + (f" ({an})" if an and gesendet else ""), user["email"]))
    if gesendet or d.kanal != "mail":
        cur.execute("UPDATE leads SET letzter_kontakt_am=now() WHERE id=%s", (l["id"],))
    audit(cur, user, "visitenkarte_gesendet", None, {"lead": str(l["id"]), "kanal": d.kanal, "ok": gesendet or d.kanal != "mail"})
    return {"gesendet": gesendet, "grund": grund, "an": an, "kanal": d.kanal}


def _antwort(user, rolle):
    with tx("system") as cur:
        k, f = _karte(cur, user, rolle)
    return {"karte": k, "firma": f["name"] or "Markentrix"}


# ---------------------------------------------------------------- Vertriebler
@router.get("/vertrieb/visitenkarte")
def v_lesen(user: dict = Depends(require_vertrieb)):
    return _antwort(user, "vertrieb")


@router.put("/vertrieb/visitenkarte")
def v_speichern(d: KarteIn, user: dict = Depends(require_vertrieb)):
    return _speichern(user, "vertrieb", d)


@router.get("/vertrieb/visitenkarte.vcf")
def v_datei(user: dict = Depends(require_vertrieb)):
    return _datei(user, "vertrieb")


@router.post("/vertrieb/leads/{lid}/visitenkarte")
def v_senden(lid: str, d: SendenIn, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        return _senden(cur, user, "vertrieb", eigener_lead(cur, lid, user["vertriebspartner_id"]), d)


# ---------------------------------------------------------------- Admin
@router.get("/admin/visitenkarte")
def a_lesen(user: dict = Depends(require_admin)):
    return _antwort(user, "admin")


@router.put("/admin/visitenkarte")
def a_speichern(d: KarteIn, user: dict = Depends(require_admin)):
    return _speichern(user, "admin", d)


@router.get("/admin/visitenkarte.vcf")
def a_datei(user: dict = Depends(require_admin)):
    return _datei(user, "admin")


@router.post("/admin/leads/{lid}/visitenkarte")
def a_senden(lid: str, d: SendenIn, user: dict = Depends(require_admin)):
    with tx("system") as cur:
        return _senden(cur, user, "admin", _lead(cur, lid), d)
