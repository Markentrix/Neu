"""Öffentliche Statusseite der Plattform (ohne Anmeldung): Portal, Datenbank, Kunden-Websites (nur Zahlen, keine Namen), E-Mail-Versand, Datensicherung
und Meldungen zu Störungen und Wartung. Admin pflegt die Meldungen."""
from datetime import datetime, timedelta, timezone
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from psycopg import errors
from pydantic import BaseModel, Field

from . import webbetrieb
from .db import tx
from .routes_status import _letzte_sicherung
from .security import audit, client_ip, rate_limit, require_admin

public = APIRouter()
admin = APIRouter(prefix="/api/admin/statusmeldungen")
ARTEN = {"stoerung": "Störung", "wartung": "Wartung", "info": "Hinweis"}
STUFE = {"ok": 0, "warn": 1, "bad": 2}


def komponenten(cur) -> list:
    """Zustand der Bausteine. Jeder Eintrag: name, stufe (ok/warn/bad), text."""
    out = [{"name": "Kunden-Portal", "stufe": "ok", "text": "Läuft"}]
    cur.execute("SELECT 1")
    out.append({"name": "Datenbank", "stufe": "ok", "text": "Läuft"})
    cur.execute("""SELECT count(*) AS n, count(*) FILTER (WHERE ok) AS ok FROM website_wacht w JOIN websites s ON s.domain = w.domain AND s.art = 'live'
                   WHERE w.geprueft_am > now() - interval '30 minutes'""")
    r = cur.fetchone()
    if not r["n"]:
        out.append({"name": "Kunden-Websites", "stufe": "ok", "text": "Keine Messung aktiv"})
    elif r["ok"] == r["n"]:
        out.append({"name": "Kunden-Websites", "stufe": "ok", "text": f"Alle {r['n']} erreichbar"})
    else:
        out.append({"name": "Kunden-Websites", "stufe": "bad" if r["ok"] * 2 < r["n"] else "warn", "text": f"{r['ok']} von {r['n']} erreichbar, wir arbeiten daran"})
    cur.execute("SELECT count(*) FILTER (WHERE NOT ok) AS fehl, count(*) AS n FROM mail_protokoll WHERE zeit > now() - interval '24 hours'")
    m = cur.fetchone()
    if m["n"] >= 5 and m["fehl"] * 4 > m["n"]:
        out.append({"name": "E-Mail-Versand", "stufe": "warn", "text": "Einzelne Mails verzögern sich"})
    else:
        out.append({"name": "E-Mail-Versand", "stufe": "ok", "text": "Läuft"})
    sich = _letzte_sicherung()
    frisch = False
    if sich:
        try:
            frisch = datetime.now() - datetime.strptime(sich, "%d.%m.%Y") <= timedelta(days=2)
        except ValueError:
            pass
    out.append({"name": "Datensicherung", "stufe": "ok" if frisch else "warn", "text": f"Letzte Sicherung {sich}" if sich else "Noch keine Angabe"})
    return out


def verfuegbarkeit(cur) -> float | None:
    cur.execute("SELECT sum(ok) AS ok, sum(geprueft) AS n FROM website_wacht_tag WHERE tag >= current_date - 30")
    r = cur.fetchone()
    return round(100.0 * r["ok"] / r["n"], 2) if r and r["n"] else None


def meldungen(cur) -> tuple:
    cur.execute("""SELECT id, art, titel, text, beginn, beendet_am FROM statusmeldungen WHERE beendet_am IS NULL ORDER BY beginn DESC LIMIT 20""")
    offen = cur.fetchall()
    cur.execute("""SELECT id, art, titel, text, beginn, beendet_am FROM statusmeldungen WHERE beendet_am IS NOT NULL AND beendet_am > now() - interval '30 days'
                   ORDER BY beendet_am DESC LIMIT 10""")
    return offen, cur.fetchall()


def gesamt(komp: list, offen: list) -> tuple:
    jetzt = datetime.now(timezone.utc)
    aktiv = [m for m in offen if m["beginn"] <= jetzt]
    stufe = max([STUFE[k["stufe"]] for k in komp] + [2 if any(m["art"] == "stoerung" for m in aktiv) else 1 if any(m["art"] == "wartung" for m in aktiv) else 0])
    return ("ok", "Alle Systeme laufen") if stufe == 0 else ("warn", "Teilweise eingeschränkt") if stufe == 1 else ("bad", "Störung")


def _d(t) -> str:
    return t.astimezone(webbetrieb.TZ).strftime("%d.%m.%Y %H:%M") if isinstance(t, datetime) else ""


def daten() -> dict:
    with tx("system") as cur:
        komp = komponenten(cur)
        offen, erledigt = meldungen(cur)
        v = verfuegbarkeit(cur)
    s, titel = gesamt(komp, offen)
    return {"stufe": s, "titel": titel, "komponenten": komp, "verfuegbarkeit_30_tage": v,
            "meldungen": [{"art": m["art"], "titel": m["titel"], "text": m["text"], "beginn": m["beginn"].isoformat(), "beendet_am": m["beendet_am"].isoformat() if m["beendet_am"] else None} for m in offen + erledigt]}


SEITE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="120"><title>Status – Markentrix</title><style>
:root{{--bg:#f6f7fb;--fg:#0B1020;--card:#fff;--mut:#5b6480;--ok:#14803c;--bad:#b42318;--warn:#a15c07;--line:#e3e6ef}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0B1020;--fg:#eef0f8;--card:#141b33;--mut:#9aa4c7;--ok:#4ade80;--bad:#f87171;--warn:#fbbf24;--line:#26304f}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}}main{{max-width:720px;margin:0 auto;padding:24px 16px 48px}}
h1{{font-size:24px;margin:0 0 4px}}h2{{font-size:17px;margin:0 0 8px}}.mut{{color:var(--mut);font-size:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px;vertical-align:middle}}
.ok{{background:var(--ok)}}.bad{{background:var(--bad)}}.warn{{background:var(--warn)}}
table{{width:100%;border-collapse:collapse;font-size:15px}}td{{padding:8px 0;border-top:1px solid var(--line)}}td:last-child{{text-align:right}}
</style></head><body><main><h1>Markentrix Status</h1><p class="mut">Stand {stand}. Aktualisiert sich automatisch.</p>
<div class="card"><h2><span class="dot {stufe}"></span>{titel}</h2>{verf}</div>{aktuell}
<div class="card"><h2>Bausteine</h2><table>{zeilen}</table></div>{verlauf}
<p class="mut">Fragen? Schreiben Sie uns über Ihr Portal oder an die bekannte Adresse.</p></main></body></html>"""


def _meldung(m) -> str:
    ende = f" bis {_d(m['beendet_am'])}" if m["beendet_am"] else ""
    return f'<p><b>{escape(ARTEN[m["art"]])}: {escape(m["titel"])}</b><br><span class="mut">{_d(m["beginn"])}{ende}</span>' + (f'<br>{escape(m["text"])}' if m["text"] else "") + "</p>"


@public.get("/status", include_in_schema=False)
def seite(request: Request):
    rate_limit("plattformstatus:" + client_ip(request), 120, 300)
    with tx("system") as cur:
        komp = komponenten(cur)
        offen, erledigt = meldungen(cur)
        v = verfuegbarkeit(cur)
    s, titel = gesamt(komp, offen)
    zeilen = "".join(f'<tr><td><span class="dot {k["stufe"]}"></span>{escape(k["name"])}</td><td>{escape(k["text"])}</td></tr>' for k in komp)
    aktuell = '<div class="card"><h2>Aktuelle Meldungen</h2>' + "".join(_meldung(m) for m in offen) + "</div>" if offen else ""
    verlauf = '<div class="card"><h2>Letzte 30 Tage</h2>' + "".join(_meldung(m) for m in erledigt) + "</div>" if erledigt else ""
    verf = f'<p class="mut">Erreichbarkeit der Kunden-Websites in den letzten 30 Tagen: {str(v).replace(".", ",")} %</p>' if v is not None else ""
    html = SEITE.format(stand=datetime.now(webbetrieb.TZ).strftime("%d.%m.%Y %H:%M"), stufe=s, titel=escape(titel), verf=verf, aktuell=aktuell, zeilen=zeilen, verlauf=verlauf)
    return HTMLResponse(html, 200, {"Cache-Control": "no-store"})


@public.get("/api/status", include_in_schema=False)
def api_status(request: Request):
    rate_limit("plattformstatus:" + client_ip(request), 120, 300)
    return JSONResponse(daten(), headers={"Cache-Control": "no-store"})


class MeldungIn(BaseModel):
    art: str = Field(pattern="^(stoerung|wartung|info)$")
    titel: str = Field(min_length=1, max_length=120)
    text: str = Field(default="", max_length=1500)
    beginn: datetime | None = None


@admin.get("")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT id, art, titel, text, beginn, beendet_am FROM statusmeldungen ORDER BY erstellt_am DESC LIMIT 50")
        return cur.fetchall()


@admin.post("")
def neu(data: MeldungIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("INSERT INTO statusmeldungen (art, titel, text, beginn) VALUES (%s,%s,%s,coalesce(%s, now())) RETURNING id", (data.art, data.titel.strip(), data.text.strip(), data.beginn))
        mid = cur.fetchone()["id"]
        audit(cur, user, "statusmeldung_neu", None, {"art": data.art, "titel": data.titel})
    return {"id": mid}


@admin.post("/{mid}/beenden")
def beenden(mid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE statusmeldungen SET beendet_am = now() WHERE id=%s AND beendet_am IS NULL RETURNING id", (mid,))
            if not cur.fetchone():
                raise HTTPException(404, "Meldung nicht gefunden oder schon beendet.")
            audit(cur, user, "statusmeldung_beendet", None, {"id": mid})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Meldung nicht gefunden.")
    return {"ok": True}


@admin.delete("/{mid}")
def loeschen(mid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM statusmeldungen WHERE id=%s RETURNING id", (mid,))
            if not cur.fetchone():
                raise HTTPException(404, "Meldung nicht gefunden.")
            audit(cur, user, "statusmeldung_geloescht", None, {"id": mid})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Meldung nicht gefunden.")
    return {"ok": True}
