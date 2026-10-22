"""Referenzseite: zeigt NUR, was Kunden im Referenzvertrag ausdrücklich freigegeben haben (Elemente mit Wortlaut, Kanal „Website von Markentrix“, nicht widerrufen).
Die Seite ist erst öffentlich, wenn der Admin sie einschaltet. Logos und Abbildungen gehören nicht dazu, die fügt das Team von Hand ein."""
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import einstellungen
from .db import tx
from .security import audit, require_admin

public = APIRouter()
admin = APIRouter(prefix="/api/admin/referenzseite")
STANDARD = {"aktiv": False, "titel": "Das sagen unsere Kunden", "intro": "Diese Betriebe haben uns erlaubt, ihr Projekt zu zeigen."}


def einstellung(cur) -> dict:
    return {**STANDARD, **(einstellungen.lesen(cur, "referenzseite") or {})}


def eintraege(cur) -> list:
    """Nur Freigegebenes: Inhalte brauchen den vom Kunden angegebenen Wortlaut; ohne Namensfreigabe erscheint der Eintrag anonym."""
    cur.execute("""SELECT k.firma, d.antworten, d.unterschrieben_am FROM vertragsdokumente d JOIN kunden k ON k.id=d.kunden_id
                   WHERE d.art='referenz' AND d.unterschrieben_am IS NOT NULL AND d.widerrufen_am IS NULL AND d.antworten IS NOT NULL
                     AND k.status IN ('onboarding','aktiv','pausiert') ORDER BY d.unterschrieben_am DESC LIMIT 100""")
    out = []
    for r in cur.fetchall():
        a, el = r["antworten"] or {}, (r["antworten"] or {}).get("elemente") or {}
        if "web" not in (a.get("kanaele") or []):
            continue
        e = {"name": (el.get("name") or r["firma"]) if "name" in el else "", "kurz": el.get("kurz") or "", "kenn": el.get("kenn") or "", "zitat": el.get("zitat") or "", "link": ""}
        link = (el.get("link") or "").strip()
        if "link" in el and link.startswith(("https://", "http://")) and " " not in link:
            e["link"] = link
        if not (e["kurz"] or e["kenn"] or e["zitat"]):
            continue
        out.append(e)
    return out


SEITE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{titel}</title>
<style>body{{margin:0;font:16px/1.6 system-ui,sans-serif;background:#f6f7fc;color:#0b1020}}main{{max-width:820px;margin:0 auto;padding:32px 16px}}h1{{font-size:28px;margin:0 0 6px}}
.k{{background:#fff;border-radius:14px;padding:18px 20px;margin:14px 0;box-shadow:0 1px 3px #0001}}blockquote{{margin:8px 0;padding-left:12px;border-left:3px solid #6d3fe0;font-style:italic}}
.n{{font-weight:700}}.m{{color:#6b7390}}a{{color:#6d3fe0}}</style></head><body><main><h1>{titel}</h1><p class="m">{intro}</p>{karten}</main></body></html>"""


def _karte(e: dict) -> str:
    kopf = f'<div class="n">{escape(e["name"]) if e["name"] else "Ein Kunde (ohne Namensnennung)"}</div>'
    if e["link"]:
        kopf = f'<div class="n"><a href="{escape(e["link"], quote=True)}" rel="noopener nofollow" target="_blank">{escape(e["name"] or e["link"])}</a></div>'
    return ('<div class="k">' + kopf + (f'<p>{escape(e["kurz"])}</p>' if e["kurz"] else "") + (f'<p><b>{escape(e["kenn"])}</b></p>' if e["kenn"] else "")
            + (f'<blockquote>{escape(e["zitat"])}</blockquote>' if e["zitat"] else "") + "</div>")


@public.get("/referenzen", include_in_schema=False)
def seite():
    with tx("system") as cur:
        s = einstellung(cur)
        liste = eintraege(cur) if s["aktiv"] else []
    if not s["aktiv"] or not liste:
        raise HTTPException(404, "Nicht gefunden.")
    return HTMLResponse(SEITE.format(titel=escape(s["titel"]), intro=escape(s["intro"]), karten="".join(_karte(e) for e in liste)), 200, {"Cache-Control": "public, max-age=300"})


@public.get("/api/referenzen", include_in_schema=False)
def daten():
    with tx("system") as cur:
        s = einstellung(cur)
        liste = eintraege(cur) if s["aktiv"] else []
    return JSONResponse({"titel": s["titel"], "intro": s["intro"], "eintraege": liste}, headers={"Cache-Control": "public, max-age=300"})


class SeiteIn(BaseModel):
    aktiv: bool = False
    titel: str = Field(default=STANDARD["titel"], min_length=3, max_length=120)
    intro: str = Field(default=STANDARD["intro"], max_length=400)


@admin.get("")
def lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return {**einstellung(cur), "eintraege": eintraege(cur)}


@admin.put("")
def speichern(data: SeiteIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "referenzseite", data.model_dump())
        audit(cur, user, "einstellungen_referenzseite", None, {"aktiv": data.aktiv})
    return {"ok": True}
