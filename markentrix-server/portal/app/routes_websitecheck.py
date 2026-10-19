"""Anbindung des Website-Checks auf markentrix.de: legt Leads an und speichert das Prüfergebnis."""
import hmac
import json
import re
import secrets
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, einstellungen, mailer
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


@router.post("/public/website-check")
async def website_check(data: CheckIn, request: Request, bg: BackgroundTasks):
    rate_limit("wcheck", 60, 600)
    with tx("system") as cur:
        soll = (einstellungen.lesen(cur, "website_check") or {}).get("secret") or ""
    gegeben = request.headers.get("x-lead-secret", "")
    if not soll or not hmac.compare_digest(soll.encode(), gegeben.encode()):
        rate_limit("wcheck-falsch:" + client_ip(request), 10, 600)
        raise HTTPException(401, "Nicht berechtigt.")
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
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                      VALUES (NULL, %s, %s, current_date + 1, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                    (f"Lead nachfassen: {firma}", an, f"lead-check-{lid}-{__import__('datetime').date.today().isoformat()}"))
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
