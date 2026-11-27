"""Terminvorschläge ohne Angebot: bis zu 3 Zeiten für ein Beratungsgespräch an einen Kunden oder Lead.
Der Empfänger öffnet den Link aus der Mail und bestätigt mit einem Klick. Dann steht das Gespräch im Admin-Kalender (gespraechstermine),
die Kalendereinladung geht an beide Seiten, und die bestehenden Erinnerungen (24 h, 2 h, Push 60/5 Minuten) greifen."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, mailer, push
from .db import tx
from .routes_angebottermin import MAX, _belegt, _parse, lokal, pruefen
from .routes_buchung import TZ, EMAIL, ics, lesen
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin

router = APIRouter(prefix="/api")


class VorschlagIn(BaseModel):
    kunden_id: str | None = None
    lead_id: str | None = None
    zeiten: list[str] = Field(min_length=1, max_length=MAX)
    nachricht: str = Field(default="", max_length=1500)
    an_email: str | None = Field(default=None, max_length=200)    # abweichende Adresse, sonst die des Kunden bzw. Leads


def _empfaenger(cur, data: VorschlagIn) -> dict:
    if bool(data.kunden_id) == bool(data.lead_id):
        raise HTTPException(400, "Bitte entweder einen Kunden oder einen Lead angeben.")
    if data.kunden_id:
        cur.execute("SELECT id, firma, ansprechpartner, email FROM kunden WHERE id=%s", (data.kunden_id,))
    else:
        cur.execute("SELECT id, firma, ansprechpartner, email FROM leads WHERE id=%s", (data.lead_id,))
    r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Empfänger nicht gefunden.")
    email = (data.an_email or r["email"] or "").strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(400, "Es ist keine gültige E-Mail-Adresse hinterlegt. Bitte tragen Sie eine ein.")
    return {"name": (r["ansprechpartner"] or r["firma"] or "").strip() or "Interessent", "firma": r["firma"], "email": email}


def link(token: str, start: str | None = None) -> str:
    return f"{config.BASE_URL}/termin?t={token}" + (f"&s={start}" if start else "")


def mail_text(name: str, zeiten: list[str], token: str, nachricht: str, dauer: int, ort: str) -> str:
    zeilen = "\n".join(f"  • {lokal(_parse(x))}: {link(token, _parse(x).isoformat().replace('+00:00', 'Z'))}" for x in zeiten)
    return (f"Guten Tag {name},\n\n" + (nachricht.strip() + "\n\n" if nachricht.strip() else "")
            + f"für ein Beratungsgespräch (ca. {dauer} Minuten) schlagen wir Ihnen diese Termine vor. Ein Klick auf den passenden Termin genügt, danach bestätigen Sie ihn mit einem Knopf:\n\n"
            + zeilen + f"\n\nAlle Vorschläge auf einen Blick: {link(token)}\n\n{ort}\n\nPasst keiner? Antworten Sie einfach auf diese E-Mail." + mailer.SIGNATUR)


@router.post("/admin/terminvorschlaege")
def anlegen(data: VorschlagIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        e = _empfaenger(cur, data)
        zeiten = pruefen(cur, data.zeiten)
        c = lesen(cur)
        token = secrets.token_urlsafe(24)
        cur.execute("UPDATE terminvorschlaege SET status='zurueckgezogen' WHERE status='offen' AND coalesce(kunden_id::text, '') = coalesce(%s, '') AND coalesce(lead_id::text, '') = coalesce(%s, '')", (data.kunden_id, data.lead_id))
        cur.execute("""INSERT INTO terminvorschlaege (token, kunden_id, lead_id, name, email, zeiten, nachricht, erstellt_von) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING id""",
                    (token, data.kunden_id, data.lead_id, e["name"], e["email"], __import__("json").dumps(zeiten), data.nachricht.strip() or None, user["email"]))
        vid = cur.fetchone()["id"]
        if data.lead_id:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'termin',%s,%s)",
                        (data.lead_id, "Terminvorschläge gesendet: " + ", ".join(lokal(_parse(x)) for x in zeiten), user["email"]))
        audit(cur, user, "terminvorschlag_gesendet", data.kunden_id, {"zeiten": zeiten})
    ok, grund = mailer.senden(e["email"], "Terminvorschläge für Ihr Beratungsgespräch mit Markentrix", mail_text(e["name"], zeiten, token, data.nachricht, c["dauer"], c["ort"]),
                              kunden_id=data.kunden_id, art="terminvorschlag")
    with tx("admin") as cur:
        cur.execute("UPDATE terminvorschlaege SET gesendet=%s WHERE id=%s", (bool(ok), vid))
    return {"ok": True, "id": str(vid), "gesendet": bool(ok), "grund": None if ok else grund}


@router.get("/admin/terminvorschlaege")
def liste(kunden_id: str | None = None, lead_id: str | None = None, user: dict = Depends(require_admin)):
    if bool(kunden_id) == bool(lead_id):
        raise HTTPException(400, "Bitte entweder kunden_id oder lead_id angeben.")
    with tx("admin") as cur:
        cur.execute("""SELECT v.id, v.name, v.email, v.zeiten, v.status, v.gesendet, v.erstellt_am, g.start AS gewaehlt, g.status AS gespraech_status FROM terminvorschlaege v
                       LEFT JOIN gespraechstermine g ON g.id = v.gespraech_id
                       WHERE (v.kunden_id = %s OR v.lead_id = %s) ORDER BY v.erstellt_am DESC LIMIT 20""", (kunden_id, lead_id))
        return cur.fetchall()


@router.delete("/admin/terminvorschlaege/{vid}")
def zurueckziehen(vid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE terminvorschlaege SET status='zurueckgezogen' WHERE id=%s AND status='offen' RETURNING kunden_id", (vid,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Kein offener Vorschlag gefunden.")
        audit(cur, user, "terminvorschlag_zurueckgezogen", r["kunden_id"], {"id": vid})
    return {"ok": True}


def _frei(cur, v: dict, c: dict) -> list[str]:
    jetzt = datetime.now(timezone.utc)
    out = []
    for x in v["zeiten"]:
        d = _parse(x)
        if d > jetzt + timedelta(hours=1) and not _belegt(cur, d, d + timedelta(minutes=c["dauer"])):
            out.append(d.isoformat())
    return out


def _laden(cur, token: str) -> dict:
    cur.execute("SELECT * FROM terminvorschlaege WHERE token=%s", (token,))
    v = cur.fetchone()
    if not v:
        raise HTTPException(404, "Dieser Link ist nicht gültig.")
    return v


@router.get("/public/terminvorschlag")
def zeigen(t: str, request: Request):
    rate_limit("tv:" + client_ip(request), 60, 300)
    with tx("system") as cur:
        v = _laden(cur, t)
        c = lesen(cur)
        if v["status"] == "gewaehlt" and v["gespraech_id"]:
            cur.execute("SELECT start, ende, status FROM gespraechstermine WHERE id=%s", (v["gespraech_id"],))
            g = cur.fetchone()
            if g and g["status"] == "gebucht":
                return {"status": "gewaehlt", "name": v["name"], "termin": {"start": g["start"].isoformat(), "ende": g["ende"].isoformat()}, "termine": [], "dauer": c["dauer"], "ort": c["ort"]}
        if v["status"] != "offen":
            return {"status": "geschlossen", "name": v["name"], "termine": [], "dauer": c["dauer"], "ort": c["ort"]}
        return {"status": "offen", "name": v["name"], "termine": _frei(cur, v, c), "dauer": c["dauer"], "ort": c["ort"], "nachricht": v["nachricht"]}


class WahlIn(BaseModel):
    t: str
    start: str


@router.post("/public/terminvorschlag")
def waehlen(data: WahlIn, bg: BackgroundTasks, request: Request):
    rate_limit("tvw:" + client_ip(request), 10, 3600)
    nicht_frei = HTTPException(409, "Dieser Vorschlag ist leider nicht mehr frei. Bitte wählen Sie einen anderen oder antworten Sie auf unsere E-Mail.")
    with tx("system") as cur:
        v = _laden(cur, data.t)
        if v["status"] != "offen":
            raise HTTPException(409, "Dieser Terminvorschlag ist bereits beantwortet oder zurückgezogen.")
        start = _parse(data.start)
        if start not in [_parse(x) for x in v["zeiten"]]:
            raise HTTPException(400, "Dieser Termin gehört nicht zu den Vorschlägen.")
        c = lesen(cur)
        ende = start + timedelta(minutes=c["dauer"])
        if start <= datetime.now(timezone.utc) or _belegt(cur, start, ende):
            raise nicht_frei
        try:
            cur.execute("""INSERT INTO gespraechstermine (start, ende, name, email, lead_id, kunden_id, vorschlag_id, token, gebucht_von, nachricht)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'terminvorschlag',%s) RETURNING id, start, ende, name, email, token""",
                        (start, ende, v["name"], v["email"], v["lead_id"], v["kunden_id"], v["id"], secrets.token_urlsafe(24), v["nachricht"] or "Beratungsgespräch"))
        except Exception:
            raise nicht_frei
        g = cur.fetchone()
        g["ort"] = c["ort"]
        cur.execute("UPDATE terminvorschlaege SET status='gewaehlt', gespraech_id=%s WHERE id=%s", (g["id"], v["id"]))
        if v["lead_id"]:
            cur.execute("UPDATE leads SET status=CASE WHEN status IN ('neu','kontaktiert','antwort') THEN 'termin' ELSE status END, wiedervorlage_am=%s, letzter_kontakt_am=now() WHERE id=%s",
                        (start.astimezone(TZ).date(), v["lead_id"]))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von, ergebnis) VALUES (%s,'termin',%s,'Terminvorschlag','termin')", (v["lead_id"], f"Beratungsgespräch gewählt: {lokal(start)}"))
        an = [x for x in [admin_empfaenger(cur)] if x]
        ids = push.admins(cur)
        firma = v["name"]
    push.senden(ids, "Beratungstermin bestätigt", f"{firma}: {lokal(start)}", "/admin#kalender", "buchung")
    bg.add_task(_mails, g, an)
    return {"ok": True, "wann": lokal(start)}


def _mails(g: dict, an_team: list):
    wann = lokal(g["start"])
    absagen = f"{config.BASE_URL}/api/public/buchung/absagen?t={g['token']}"
    anhang = ("termin.ics", ics(str(g["id"]), g["start"], g["ende"], "Beratungsgespräch mit Markentrix", g["ort"]), "text/calendar")
    mailer.senden(g["email"], "Ihr Beratungsgespräch mit Markentrix am " + wann,
                  f"Guten Tag {g['name']},\n\nvielen Dank, Ihr Beratungsgespräch ist vereinbart: {wann}.\n{g['ort']}\n\nDie Kalendereinladung hängt an. Falls Sie nicht können, sagen Sie bitte hier ab: {absagen}" + mailer.SIGNATUR, anhang)
    for a in an_team:
        mailer.senden(a, f"Beratungsgespräch bestätigt: {g['name']} am {wann}", f"{g['name']} hat den Termin {wann} bestätigt. Er steht im Admin-Kalender: {config.BASE_URL}/admin#kalender", anhang)
