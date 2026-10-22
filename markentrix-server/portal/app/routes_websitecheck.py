"""Anbindung des Website-Checks auf markentrix.de: legt Leads an und speichert das Prüfergebnis."""
import hmac
import json
import re
import secrets
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, einstellungen, leadeingang, mailer, push
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin

router = APIRouter(prefix="/api")
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[A-Za-z]{2,}$")


class CheckIn(BaseModel):
    email: str = Field(max_length=320)
    name: str | None = Field(default=None, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=300)
    score: int | None = Field(default=None, ge=0, le=100)
    ergebnis: dict = {}
    einwilligung: bool = False
    einwilligung_text: str | None = Field(default=None, max_length=500)


def _host(url: str | None) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    try:
        return (urlparse(u if "//" in u else "//" + u).hostname or "")[:200]
    except ValueError:
        return ""


def _schluessel_pruefen(request: Request):
    rate_limit("wcheck", 60, 600)
    with tx("system") as cur:
        soll = (einstellungen.lesen(cur, "website_check") or {}).get("secret") or ""
    gegeben = request.headers.get("x-lead-secret", "")
    if not soll or not hmac.compare_digest(soll.encode(), gegeben.encode()):
        rate_limit("wcheck-falsch:" + client_ip(request), 10, 600)
        raise HTTPException(401, "Nicht berechtigt.")


class KontaktIn(BaseModel):
    email: str = Field(max_length=320)
    name: str | None = Field(default=None, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    telefon: str | None = Field(default=None, max_length=60)
    thema: str | None = Field(default=None, max_length=200)
    budget: str | None = Field(default=None, max_length=100)
    nachricht: str | None = Field(default=None, max_length=4000)
    wunschtermin: str | None = Field(default=None, max_length=200)
    einwilligung: bool = False
    einwilligung_text: str | None = Field(default=None, max_length=500)


@router.post("/public/kontakt-lead")
async def kontakt_lead(data: KontaktIn, request: Request, bg: BackgroundTasks):
    """Anfrage über das Kontaktformular der Website: legt einen Lead (heiß) an oder ergänzt den vorhandenen."""
    _schluessel_pruefen(request)
    email = data.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not data.einwilligung:
        raise HTTPException(400, "Ohne Einwilligung wird kein Kontakt angelegt.")
    firma = (data.firma or "").strip() or (data.name or "").strip() or email.split("@")[1]
    zeilen = [f"Thema: {data.thema}" if data.thema else "", f"Budget: {data.budget}" if data.budget else "", f"Wunschtermin: {data.wunschtermin}" if data.wunschtermin else "",
              (data.nachricht or "").strip()]
    inhalt = "Anfrage über das Kontaktformular:\n" + "\n".join(z for z in zeilen if z)
    with tx("system") as cur:
        cur.execute("SELECT id FROM leads WHERE lower(email)=%s ORDER BY erstellt_am LIMIT 1", (email,))
        l = cur.fetchone()
        neu = not l
        if neu:
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, quelle, temperatur, loeschen_nach, notiz)
                           VALUES (%s,%s,%s,%s,'website','heiss', current_date + interval '12 months', 'Über das Kontaktformular auf markentrix.de') RETURNING id""",
                        (firma, (data.name or "").strip() or None, email, (data.telefon or "").strip() or None))
            lid = cur.fetchone()["id"]
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent',%s,'website')",
                        (lid, "Einwilligung im Kontaktformular erteilt" + (f" (Text: {data.einwilligung_text})" if data.einwilligung_text else "")))
        else:
            lid = l["id"]
            cur.execute("""UPDATE leads SET temperatur='heiss', telefon=coalesce(telefon,%s), loeschen_nach=greatest(loeschen_nach, current_date + interval '12 months') WHERE id=%s""",
                        ((data.telefon or "").strip() or None, lid))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'website')", (lid, inhalt[:3900]))
        an = admin_empfaenger(cur)
        partner_ids = leadeingang.bearbeiten(cur, lid, neu, "Kontaktformular")
        push_ids = push.admins(cur)
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                      VALUES (NULL, %s, %s, current_date, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                    (f"Anfrage beantworten: {firma}", an, f"lead-kontakt-{lid}-{__import__('datetime').datetime.now().strftime('%Y%m%d%H%M')}"))
    push.senden(push_ids + partner_ids, "Neue Anfrage über die Website" if neu else "Erneute Anfrage über die Website", f"{firma}: bitte zeitnah antworten.", "/admin#lead/" + str(lid), "check")
    if an:
        bg.add_task(mailer.senden, an, f"Neue Anfrage: {firma}", f"{(data.name or '').strip() or firma} ({email}) hat über das Kontaktformular geschrieben.\n\n{inhalt[:1500]}\n\n{config.BASE_URL}/admin#lead/{lid}" + mailer.SIGNATUR)
    return {"ok": True, "neu": neu}


@router.post("/public/website-check")
async def website_check(data: CheckIn, request: Request, bg: BackgroundTasks):
    _schluessel_pruefen(request)
    email = data.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not data.einwilligung:
        raise HTTPException(400, "Ohne Einwilligung wird kein Kontakt angelegt.")
    ergebnis = json.dumps(data.ergebnis, ensure_ascii=False)
    if len(ergebnis) > 20000:
        raise HTTPException(400, "Das Ergebnis ist zu groß.")
    website = (data.website or "").strip() or None
    firma = (data.firma or "").strip() or _host(website) or (data.name or "").strip() or email.split("@")[1]
    with tx("system") as cur:
        cur.execute("SELECT id FROM leads WHERE lower(email)=%s ORDER BY erstellt_am LIMIT 1", (email,))
        l = cur.fetchone()
        neu = not l
        if neu:
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, quelle, score, temperatur, loeschen_nach, notiz)
                           VALUES (%s,%s,%s,%s,%s,'website',%s,'warm', current_date + interval '12 months', 'Über den Website-Check auf markentrix.de') RETURNING id""",
                        (firma, (data.name or "").strip() or None, email, (data.telefon or "").strip() or None, website, data.score))
            lid = cur.fetchone()["id"]
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent',%s,'website')",
                        (lid, "Einwilligung im Website-Check erteilt" + (f" (Text: {data.einwilligung_text})" if data.einwilligung_text else "")))
        else:
            lid = l["id"]
            cur.execute("UPDATE leads SET website=coalesce(website,%s), score=coalesce(%s,score), loeschen_nach=greatest(loeschen_nach, current_date + interval '12 months') WHERE id=%s", (website, data.score, lid))
        cur.execute("INSERT INTO lead_checks (lead_id, website, score, ergebnis) VALUES (%s,%s,%s,%s::jsonb)", (lid, website, data.score, ergebnis))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'website')",
                    (lid, f"Website-Check für {website or 'ohne Website'}: {data.score if data.score is not None else '-'} von 100"))
        an = admin_empfaenger(cur)
        push_ids = push.admins(cur) + leadeingang.bearbeiten(cur, lid, neu, "Website-Check")
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                      VALUES (NULL, %s, %s, current_date + 1, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                    (f"Lead nachfassen: {firma}", an, f"lead-check-{lid}-{__import__('datetime').date.today().isoformat()}"))
    push.senden(push_ids, "Neuer Website-Check", "Ein Interessent hat den Website-Check genutzt." if neu else "Ein bekannter Lead hat den Website-Check erneut genutzt.", "/admin#leads", "check")
    if an:
        bg.add_task(mailer.website_check_team, an, (data.name or "").strip(), firma, email, website or "", data.score, neu, str(lid))
    return {"ok": True, "neu": neu}


@router.get("/admin/website-check")
def stand(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        aktiv = bool((einstellungen.lesen(cur, "website_check") or {}).get("secret"))
    return {"aktiv": aktiv, "adresse": config.BASE_URL.rstrip("/") + "/api/public/website-check"}


@router.post("/admin/website-check/schluessel")
def schluessel(user: dict = Depends(require_admin)):
    s = secrets.token_urlsafe(32)
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "website_check", {"secret": s})
        audit(cur, user, "website_check_schluessel", None, {})
    return {"schluessel": s, "adresse": config.BASE_URL.rstrip("/") + "/api/public/website-check"}
