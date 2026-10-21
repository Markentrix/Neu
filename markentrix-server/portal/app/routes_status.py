"""Öffentliche Statusseite je Kunde: Erreichbarkeit der Website, Zertifikat, letzte Änderungen, letzte Sicherung. Ohne Anmeldung, über einen geheimen Link."""
import json
import re
import secrets
from datetime import datetime
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import config, webbetrieb
from .db import tx
from .security import audit, client_ip, rate_limit, require_inhaber

kunde = APIRouter(prefix="/api/kunde/statusseite")
public = APIRouter()
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24,64}$")


def _url(token: str) -> str:
    return f"{config.BASE_URL}/status/{token}"


@kunde.get("")
def lesen(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("SELECT token, aktiv FROM statusseiten WHERE kunden_id=%s", (user["kunden_id"],))
        r = cur.fetchone()
    return {"aktiv": bool(r and r["aktiv"]), "url": _url(r["token"]) if r else None}


class AktivIn(BaseModel):
    aktiv: bool


@kunde.put("")
def schalten(data: AktivIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("statusseite:" + str(kid), 30, 600)
    with tx("system") as cur:
        cur.execute("""INSERT INTO statusseiten (kunden_id, token, aktiv) VALUES (%s,%s,%s)
                       ON CONFLICT (kunden_id) DO UPDATE SET aktiv=EXCLUDED.aktiv RETURNING token, aktiv""", (kid, secrets.token_urlsafe(24), data.aktiv))
        r = cur.fetchone()
        audit(cur, user, "statusseite_geschaltet", kid, {"aktiv": data.aktiv})
    return {"aktiv": r["aktiv"], "url": _url(r["token"])}


@kunde.post("/neu")
def neuer_link(user: dict = Depends(require_inhaber)):
    """Neuen geheimen Link erzeugen; der alte Link funktioniert danach nicht mehr."""
    kid = user["kunden_id"]
    rate_limit("statusseite-neu:" + str(kid), 10, 3600)
    with tx("system") as cur:
        cur.execute("UPDATE statusseiten SET token=%s WHERE kunden_id=%s RETURNING token, aktiv", (secrets.token_urlsafe(24), kid))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Die Statusseite ist noch nicht eingeschaltet.")
        audit(cur, user, "statusseite_neuer_link", kid, {})
    return {"aktiv": r["aktiv"], "url": _url(r["token"])}


def _letzte_sicherung() -> str | None:
    try:
        tage = json.loads((config.QUEUE_DIR / "sicherungen.json").read_text()).get("tage") or []
        t = str(tage[0])[:10]
        return f"{t[8:10]}.{t[5:7]}.{t[:4]}" if re.match(r"^\d{4}-\d\d-\d\d$", t) else None
    except (OSError, ValueError, IndexError):
        return None


def _d(t) -> str:
    return t.astimezone(webbetrieb.TZ).strftime("%d.%m.%Y %H:%M") if isinstance(t, datetime) else ""


SEITE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Status – {firma}</title><style>
:root{{--bg:#f6f7fb;--fg:#0B1020;--card:#fff;--mut:#5b6480;--ok:#14803c;--bad:#b42318;--warn:#a15c07;--line:#e3e6ef}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0B1020;--fg:#eef0f8;--card:#141b33;--mut:#9aa4c7;--ok:#4ade80;--bad:#f87171;--warn:#fbbf24;--line:#26304f}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}}main{{max-width:720px;margin:0 auto;padding:24px 16px 48px}}
h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:17px;margin:0 0 8px}}.mut{{color:var(--mut);font-size:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px;vertical-align:middle}}
.ok{{background:var(--ok)}}.bad{{background:var(--bad)}}.warn{{background:var(--warn)}}
table{{width:100%;border-collapse:collapse;font-size:15px}}td{{padding:6px 0;border-top:1px solid var(--line)}}td:last-child{{text-align:right}}
</style></head><body><main><h1>{firma}</h1><p class="mut">Zustand Ihrer Website – Stand {stand}</p>{inhalt}
<p class="mut">Diese Seite wird automatisch aktualisiert (Prüfung alle 5 Minuten) und ist nur über diesen persönlichen Link erreichbar.</p></main></body></html>"""


@public.get("/status/{token}", include_in_schema=False)
def oeffentlich(token: str, request: Request):
    rate_limit("statusseite-pub:" + client_ip(request), 60, 300)
    kopf = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer"}
    if not TOKEN_RE.match(token):
        return HTMLResponse("<!doctype html><meta charset=utf-8><title>Status</title><p style='font:16px system-ui;margin:20vh auto;max-width:480px'>Dieser Link ist nicht (mehr) gültig.</p>", 404, kopf)
    with tx("system") as cur:
        cur.execute("""SELECT s.kunden_id, k.firma FROM statusseiten s JOIN kunden k ON k.id = s.kunden_id WHERE s.token=%s AND s.aktiv AND k.status IN ('onboarding','aktiv')""", (token,))
        s = cur.fetchone()
        if not s:
            return HTMLResponse("<!doctype html><meta charset=utf-8><title>Status</title><p style='font:16px system-ui;margin:20vh auto;max-width:480px'>Dieser Link ist nicht (mehr) gültig.</p>", 404, kopf)
        kid = s["kunden_id"]
        seiten = webbetrieb.status(cur, kid)
        cur.execute("SELECT domain, letzte_veroeffentlichung FROM websites WHERE kunden_id=%s AND art='live' ORDER BY domain", (kid,))
        sites = cur.fetchall()
        cur.execute("""SELECT zeit, aktion FROM audit_log WHERE kunden_id=%s AND aktion IN ('website_hochgeladen','website_zurueck','website_aus_sicherung') ORDER BY zeit DESC LIMIT 8""", (kid,))
        aend = cur.fetchall()
    teile = []
    nach = {x["domain"]: x for x in seiten}
    for w in sites:
        x = nach.get(w["domain"])
        if not x:
            teile.append(f'<div class="card"><h2>{escape(w["domain"])}</h2><p><span class="dot warn"></span>Wird eingerichtet</p></div>')
            continue
        zeilen = [f"<tr><td>Erreichbarkeit (30 Tage)</td><td>{str(x['prozent']).replace('.', ',')} %</td></tr>" if x["prozent"] is not None else "",
                  f"<tr><td>Zertifikat (HTTPS)</td><td>noch {x['cert_tage']} Tage gültig</td></tr>" if x["cert_tage"] is not None else "",
                  f"<tr><td>Typische Ladezeit</td><td>{x['qualitaet']['median_ms']} ms</td></tr>" if x.get("qualitaet") and x["qualitaet"]["median_ms"] is not None else "",
                  f"<tr><td>Defekte Verweise</td><td>{len(x['qualitaet']['tote']) or 'keine'}</td></tr>" if x.get("qualitaet") else "",
                  f"<tr><td>Zuletzt veröffentlicht</td><td>{_d(w['letzte_veroeffentlichung'])}</td></tr>" if w["letzte_veroeffentlichung"] else ""]
        teile.append(f'<div class="card"><h2>{escape(w["domain"])}</h2><p><span class="dot {"ok" if x["ok"] else "bad"}"></span>{"Erreichbar" if x["ok"] else "Aktuell gestört – wir kümmern uns darum"}</p>'
                     f'<table>{"".join(z for z in zeilen if z)}</table></div>')
    sich = _letzte_sicherung()
    teile.append(f'<div class="card"><h2>Datensicherung</h2><p><span class="dot {"ok" if sich else "warn"}"></span>{("Letzte tägliche Sicherung: " + sich) if sich else "Noch keine Angabe"}</p></div>')
    if aend:
        txt = {"website_hochgeladen": "Website aktualisiert", "website_zurueck": "Vorige Version wiederhergestellt", "website_aus_sicherung": "Aus Sicherung wiederhergestellt"}
        teile.append('<div class="card"><h2>Letzte Änderungen</h2><table>' + "".join(f"<tr><td>{txt[a['aktion']]}</td><td>{_d(a['zeit'])}</td></tr>" for a in aend) + "</table></div>")
    html = SEITE.format(firma=escape(s["firma"]), stand=datetime.now(webbetrieb.TZ).strftime("%d.%m.%Y %H:%M"), inhalt="".join(teile))
    return HTMLResponse(html, 200, kopf)
