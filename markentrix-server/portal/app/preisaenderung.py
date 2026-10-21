"""Preiserhöhung per Knopfdruck: Vorschau, Ankündigung per Mail mit Frist, Kenntnisnahme oder Widerspruch des Kunden, Anwendung zum Stichtag."""
import json
import secrets
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import mailer, push, config
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin

admin = APIRouter(prefix="/api/admin/preisaenderungen")
public = APIRouter()
MIN_TAGE = 30             # Mindestfrist zwischen Ankündigung und Wirksamkeit


def neu_preis(alt: int, prozent) -> int:
    return int((Decimal(alt) * (Decimal(100) + Decimal(str(prozent))) / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def euro(c: int) -> str:
    return f"{c / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def betroffene(cur, prozent) -> list:
    """Aktive Kunden mit monatlichen Preisen (ohne Referenzkunden und ohne offene Kündigung): Summe alt und neu."""
    cur.execute("""SELECT k.id, k.firma, k.kundennummer, k.email, k.ansprechpartner,
                          sum(b.monatlich_cent - b.rabatt_cent) AS alt
                   FROM kunden k JOIN buchungen b ON b.kunden_id = k.id AND b.status = 'aktiv' AND b.monatlich_cent > 0
                   WHERE k.status = 'aktiv' AND NOT k.referenzkunde
                     AND NOT EXISTS (SELECT 1 FROM kuendigungswuensche q WHERE q.kunden_id = k.id AND q.status IN ('offen','bearbeitet') AND q.vollzogen_am IS NULL)
                   GROUP BY k.id ORDER BY k.firma""")
    out = []
    for r in cur.fetchall():
        alt = int(r["alt"])
        out.append({**r, "alt": alt, "neu": neu_preis(alt, prozent)})
    return out


class NeuIn(BaseModel):
    titel: str = Field(min_length=3, max_length=200)
    prozent: float = Field(gt=0, le=25)
    wirksam_ab: date
    text: str = Field(default="", max_length=3000)


def _frist_pruefen(d: date):
    if d < date.today() + timedelta(days=MIN_TAGE):
        raise HTTPException(400, f"Zwischen Ankündigung und Wirksamkeit müssen mindestens {MIN_TAGE} Tage liegen (frühestens {date.today() + timedelta(days=MIN_TAGE):%d.%m.%Y}).")


@admin.post("/vorschau")
def vorschau(data: NeuIn, user: dict = Depends(require_admin)):
    _frist_pruefen(data.wirksam_ab)
    with tx("admin") as cur:
        k = betroffene(cur, data.prozent)
    return {"kunden": [{"id": str(x["id"]), "firma": x["firma"], "alt_cent": x["alt"], "neu_cent": x["neu"]} for x in k],
            "summe_alt_cent": sum(x["alt"] for x in k), "summe_neu_cent": sum(x["neu"] for x in k)}


@admin.post("")
def anlegen(data: NeuIn, user: dict = Depends(require_admin)):
    _frist_pruefen(data.wirksam_ab)
    with tx("admin") as cur:
        k = betroffene(cur, data.prozent)
        if not k:
            raise HTTPException(400, "Es gibt keine betroffenen Kunden.")
        cur.execute("INSERT INTO preisaenderungen (titel, prozent, wirksam_ab, text) VALUES (%s,%s,%s,%s) RETURNING id", (data.titel.strip(), data.prozent, data.wirksam_ab, data.text.strip()))
        pid = cur.fetchone()["id"]
        for x in k:
            cur.execute("INSERT INTO preisaenderung_kunden (preisaenderung_id, kunden_id, token, alt_cent, neu_cent) VALUES (%s,%s,%s,%s,%s)", (pid, x["id"], secrets.token_urlsafe(24), x["alt"], x["neu"]))
        audit(cur, user, "preisaenderung_angelegt", None, {"prozent": data.prozent, "kunden": len(k)})
    return {"id": str(pid), "kunden": len(k)}


@admin.get("")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT p.id, p.titel, p.prozent, p.wirksam_ab, p.status, p.angekuendigt_am, p.angewendet_am,
                              (SELECT count(*) FROM preisaenderung_kunden k WHERE k.preisaenderung_id = p.id) AS kunden,
                              (SELECT count(*) FROM preisaenderung_kunden k WHERE k.preisaenderung_id = p.id AND k.widerspruch_am IS NOT NULL) AS widersprueche,
                              (SELECT count(*) FROM preisaenderung_kunden k WHERE k.preisaenderung_id = p.id AND k.gelesen_am IS NOT NULL) AS gelesen
                       FROM preisaenderungen p ORDER BY p.erstellt_am DESC LIMIT 50""")
        return {"liste": [{**r, "id": str(r["id"]), "prozent": float(r["prozent"])} for r in cur.fetchall()]}


@admin.get("/{pid}")
def detail(pid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT id, titel, prozent, wirksam_ab, text, status FROM preisaenderungen WHERE id=%s", (pid,))
        except Exception:
            raise HTTPException(404, "Nicht gefunden.")
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Nicht gefunden.")
        cur.execute("""SELECT k.kunden_id, f.firma, k.alt_cent, k.neu_cent, k.benachrichtigt_am, k.gelesen_am, k.widerspruch_am, k.widerspruch_text, k.angewendet_am
                       FROM preisaenderung_kunden k JOIN kunden f ON f.id = k.kunden_id WHERE k.preisaenderung_id=%s ORDER BY f.firma""", (pid,))
        return {"aenderung": {**p, "id": str(p["id"]), "prozent": float(p["prozent"])}, "kunden": [{**r, "kunden_id": str(r["kunden_id"])} for r in cur.fetchall()]}


def _mailtext(p: dict, k: dict, link: str) -> str:
    return (f"Guten Tag {k['ansprechpartner'] or ''},\n\n".replace("Guten Tag ,", "Guten Tag,") +
            f"wir informieren Sie über eine Anpassung unserer Preise zum {p['wirksam_ab']:%d.%m.%Y}.\n\n"
            f"Ihr monatlicher Betrag ändert sich von {euro(k['alt_cent'])} auf {euro(k['neu_cent'])} (Anpassung um {str(p['prozent']).replace('.', ',')} %; Beträge wie auf Ihren Rechnungen).\n\n"
            + (p["text"].strip() + "\n\n" if p["text"].strip() else "") +
            f"Sie können die Ankündigung hier einsehen, bestätigen oder Ihre Einwände mitteilen:\n{link}\n\n"
            f"Wenn Sie mit der Anpassung nicht einverstanden sind, können Sie dem Vertrag nach den vereinbarten Bedingungen widersprechen oder kündigen. Melden Sie sich dazu bitte vor dem {p['wirksam_ab']:%d.%m.%Y}." + mailer.SIGNATUR)


@admin.post("/{pid}/ankuendigen")
def ankuendigen(pid: str, user: dict = Depends(require_admin)):
    rate_limit("preis-ankuendigen", 10, 3600)
    with tx("admin") as cur:
        try:
            cur.execute("SELECT * FROM preisaenderungen WHERE id=%s FOR UPDATE", (pid,))
        except Exception:
            raise HTTPException(404, "Nicht gefunden.")
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Nicht gefunden.")
        if p["status"] not in ("entwurf", "angekuendigt"):
            raise HTTPException(400, "Diese Preisänderung ist schon angewendet oder abgebrochen.")
        _frist_pruefen(p["wirksam_ab"])
        cur.execute("""SELECT k.kunden_id, k.token, k.alt_cent, k.neu_cent, f.email, f.ansprechpartner FROM preisaenderung_kunden k JOIN kunden f ON f.id = k.kunden_id
                       WHERE k.preisaenderung_id=%s AND k.benachrichtigt_am IS NULL""", (pid,))
        rows = cur.fetchall()
    ok_n, fehl = 0, []
    for r in rows:
        if not r["email"]:
            fehl.append(str(r["kunden_id"]))
            continue
        ok, _ = mailer.senden(r["email"], f"Preisanpassung zum {p['wirksam_ab']:%d.%m.%Y}", _mailtext(p, r, f"{config.BASE_URL}/preis/{r['token']}"))
        if ok:
            with tx("admin") as cur:
                cur.execute("UPDATE preisaenderung_kunden SET benachrichtigt_am=now() WHERE preisaenderung_id=%s AND kunden_id=%s", (pid, r["kunden_id"]))
            ok_n += 1
        else:
            fehl.append(str(r["kunden_id"]))
    with tx("admin") as cur:
        if ok_n:
            cur.execute("UPDATE preisaenderungen SET status='angekuendigt', angekuendigt_am=coalesce(angekuendigt_am, now()) WHERE id=%s", (pid,))
        audit(cur, user, "preisaenderung_angekuendigt", None, {"gesendet": ok_n, "fehlgeschlagen": len(fehl)})
    return {"gesendet": ok_n, "fehlgeschlagen": len(fehl), "kunden_ohne_zustellung": fehl}


@admin.post("/{pid}/abbrechen")
def abbrechen(pid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("UPDATE preisaenderungen SET status='abgebrochen' WHERE id=%s AND status IN ('entwurf','angekuendigt') RETURNING id", (pid,))
        except Exception:
            raise HTTPException(404, "Nicht gefunden.")
        if not cur.fetchone():
            raise HTTPException(400, "Diese Preisänderung lässt sich nicht mehr abbrechen.")
        audit(cur, user, "preisaenderung_abgebrochen", None, {})
    return {"ok": True}


# ---------------------------------------------------------------- Öffentliche Seite für den Kunden
SEITE = ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Preisanpassung</title>'
         '<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:560px;margin:8vh auto;padding:0 18px;color:#0B1020}}textarea{{width:100%;min-height:90px;font:inherit}}'
         'button{{font:inherit;padding:10px 16px;border-radius:10px;border:1px solid #0B1020;background:#0B1020;color:#fff;cursor:pointer;margin-right:8px}}button.s{{background:#fff;color:#0B1020}}</style></head><body>{inhalt}</body></html>')
KOPF = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer"}


def _lade(cur, token: str):
    cur.execute("""SELECT k.*, p.prozent, p.wirksam_ab, p.text, p.status, f.firma FROM preisaenderung_kunden k JOIN preisaenderungen p ON p.id = k.preisaenderung_id
                   JOIN kunden f ON f.id = k.kunden_id WHERE k.token=%s""", (token,))
    return cur.fetchone()


def _ansicht(r: dict, meldung: str = "") -> HTMLResponse:
    s = r["status"]
    if s in ("entwurf", "abgebrochen"):
        return HTMLResponse(SEITE.format(inhalt="<p>Diese Preisanpassung ist nicht (mehr) aktiv.</p>"), 404, KOPF)
    teil = (f"<h1>Preisanpassung zum {r['wirksam_ab']:%d.%m.%Y}</h1><p>{escape(r['firma'])}</p>"
            f"<p>Ihr monatlicher Betrag ändert sich von <b>{euro(r['alt_cent'])}</b> auf <b>{euro(r['neu_cent'])}</b> ({str(float(r['prozent'])).replace('.', ',')} %).</p>"
            + (f"<p>{escape(r['text'])}</p>" if r["text"].strip() else "") + (f"<p><b>{escape(meldung)}</b></p>" if meldung else ""))
    if r["widerspruch_am"]:
        teil += "<p>Ihr Einwand wurde an uns übermittelt. Wir melden uns bei Ihnen. Bis dahin wird der Preis nicht geändert.</p>"
    elif s == "angekuendigt":
        teil += ('<form method="post"><p><button name="aktion" value="ok">Zur Kenntnis genommen</button></p>'
                 '<p>Einverstanden sind Sie nicht? Schreiben Sie uns kurz, warum:</p><textarea name="text" maxlength="1500"></textarea>'
                 '<p><button class="s" name="aktion" value="widerspruch">Einwand senden</button></p></form>')
    return HTMLResponse(SEITE.format(inhalt=teil), 200, KOPF)


@public.get("/preis/{token}", include_in_schema=False)
def preis_ansicht(token: str, request: Request):
    rate_limit("preisseite:" + client_ip(request), 60, 300)
    if not (24 <= len(token) <= 64):
        return HTMLResponse(SEITE.format(inhalt="<p>Dieser Link ist ungültig.</p>"), 404, KOPF)
    with tx("system") as cur:
        r = _lade(cur, token)
        if not r:
            return HTMLResponse(SEITE.format(inhalt="<p>Dieser Link ist ungültig.</p>"), 404, KOPF)
        cur.execute("UPDATE preisaenderung_kunden SET gelesen_am=coalesce(gelesen_am, now()) WHERE token=%s", (token,))
    return _ansicht(r)


@public.post("/preis/{token}", include_in_schema=False)
def preis_antwort(token: str, request: Request, aktion: str = Form(""), text: str = Form("")):
    rate_limit("preisseite-post:" + client_ip(request), 20, 600)
    if not (24 <= len(token) <= 64):
        return HTMLResponse(SEITE.format(inhalt="<p>Dieser Link ist ungültig.</p>"), 404, KOPF)
    with tx("system") as cur:
        r = _lade(cur, token)
        if not r or r["status"] != "angekuendigt":
            return HTMLResponse(SEITE.format(inhalt="<p>Dieser Link ist nicht mehr aktiv.</p>"), 404, KOPF)
        if aktion == "widerspruch" and not r["widerspruch_am"] and not r["angewendet_am"]:
            cur.execute("UPDATE preisaenderung_kunden SET widerspruch_am=now(), widerspruch_text=%s, gelesen_am=coalesce(gelesen_am, now()) WHERE token=%s", (text.strip()[:1500], token))
            ids = push.admins(cur)
            r = _lade(cur, token)
            push.senden(ids, "Einwand zur Preisanpassung", f"{r['firma']} widerspricht der Preisanpassung zum {r['wirksam_ab']:%d.%m.%Y}.", "/admin#preise", "preis")
            return _ansicht(r, "Danke, Ihr Einwand ist bei uns eingegangen.")
        if aktion == "ok":
            cur.execute("UPDATE preisaenderung_kunden SET gelesen_am=coalesce(gelesen_am, now()) WHERE token=%s", (token,))
            return _ansicht(r, "Danke, wir haben Ihre Bestätigung vermerkt.")
    return _ansicht(r)


# ---------------------------------------------------------------- Job
def anwenden(cfg=None) -> int:
    """Täglich: Preisänderungen, deren Stichtag erreicht ist, für alle Kunden ohne Einwand anwenden (Buchungen und feste Positionen in Wartungsplänen)."""
    n = 0
    with tx("system") as cur:
        cur.execute("SELECT id, prozent FROM preisaenderungen WHERE status='angekuendigt' AND wirksam_ab <= current_date")
        faellig = cur.fetchall()
    for p in faellig:
        with tx("system") as cur:
            cur.execute("""SELECT k.kunden_id FROM preisaenderung_kunden k JOIN kunden f ON f.id = k.kunden_id
                           WHERE k.preisaenderung_id=%s AND k.angewendet_am IS NULL AND k.widerspruch_am IS NULL AND k.benachrichtigt_am IS NOT NULL AND f.status = 'aktiv'""", (p["id"],))
            for r in cur.fetchall():
                kid = r["kunden_id"]
                cur.execute("SELECT id, monatlich_cent FROM buchungen WHERE kunden_id=%s AND status='aktiv' AND monatlich_cent > 0", (kid,))
                for b in cur.fetchall():
                    cur.execute("UPDATE buchungen SET monatlich_cent=%s WHERE id=%s", (neu_preis(int(b["monatlich_cent"]), p["prozent"]), b["id"]))
                cur.execute("SELECT id, positionen FROM abrechnungsplaene WHERE kunden_id=%s AND NOT aus_buchungen", (kid,))
                for pl in cur.fetchall():
                    pos = [{**x, "preis_cent": neu_preis(int(x["preis_cent"]), p["prozent"])} for x in pl["positionen"]]
                    cur.execute("UPDATE abrechnungsplaene SET positionen=%s::jsonb WHERE id=%s", (json.dumps(pos), pl["id"]))
                cur.execute("UPDATE preisaenderung_kunden SET angewendet_am=now() WHERE preisaenderung_id=%s AND kunden_id=%s", (p["id"], kid))
                cur.execute("INSERT INTO audit_log (kunden_id, aktion, details) VALUES (%s,'preisaenderung_angewendet',%s::jsonb)", (kid, json.dumps({"prozent": float(p["prozent"])})))
                n += 1
            cur.execute("""SELECT count(*) AS offen FROM preisaenderung_kunden WHERE preisaenderung_id=%s AND angewendet_am IS NULL AND widerspruch_am IS NULL AND benachrichtigt_am IS NOT NULL""", (p["id"],))
            if cur.fetchone()["offen"] == 0:
                cur.execute("UPDATE preisaenderungen SET status='angewendet', angewendet_am=now() WHERE id=%s", (p["id"],))
                cur.execute("SELECT count(*) AS n FROM preisaenderung_kunden WHERE preisaenderung_id=%s AND widerspruch_am IS NOT NULL AND angewendet_am IS NULL", (p["id"],))
                w = cur.fetchone()["n"]
                ids = push.admins(cur)
                push.senden(ids, "Preisanpassung angewendet", "Die Preise wurden angepasst" + (f"; {w} Kunde(n) mit Einwand blieben unverändert." if w else "."), "/admin#preise", "preis")
    return n
