"""Telefon-Assistent: Anrufprotokoll. Der Anbieter (z. B. Famulor) schickt nach jedem Gespräch eine Nachricht (Webhook);
das Portal legt den Anruf an und macht bei Eingang eine Anfrage daraus, damit nichts im Postfach untergeht."""
import base64
import hmac
import secrets
from datetime import datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request

from . import config, einstellungen, push
from .db import tx
from .security import audit, client_ip, rate_limit, require_admin, require_kunde

router = APIRouter()

ALIAS = {
    "nummer": ("from_number", "caller_number", "caller", "phone_number", "phone", "telefonnummer", "nummer", "telefon", "customer_number", "from"),
    "name": ("caller_name", "contact_name", "customer_name", "name", "anrufer"),
    "dauer": ("duration_seconds", "duration_sec", "call_duration", "dauer_sek", "duration", "dauer"),
    "zusammenfassung": ("summary", "call_summary", "zusammenfassung", "analysis_summary"),
    "ergebnis": ("outcome", "disposition", "result", "ergebnis", "call_status", "status"),
    "richtung": ("direction", "call_direction", "richtung", "type"),
    "ref": ("call_id", "callid", "uuid", "extern_ref", "id"),
    "beginn": ("started_at", "start_time", "start", "beginn", "created_at", "timestamp"),
    "ki_hinweis": ("ai_disclosure", "ki_hinweis", "ai_disclosed"),
}


def _flach(d, tiefe=0) -> dict:
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and tiefe < 3:
                for k2, v2 in _flach(v, tiefe + 1).items():
                    out.setdefault(k2, v2)
            out.setdefault(str(k).lower(), v)
    return out


def lesen_daten(body: dict) -> dict:
    f = _flach(body)
    def w(name):
        for a in ALIAS[name]:
            v = f.get(a)
            if v not in (None, "", [], {}) and not isinstance(v, (dict, list)):
                return v
        return None
    richtung = str(w("richtung") or "ein").lower()
    richtung = "aus" if richtung in ("aus", "out", "outbound", "outgoing", "ausgehend") else "ein"
    try:
        dauer = int(float(w("dauer"))) if w("dauer") is not None else None
    except (TypeError, ValueError):
        dauer = None
    beginn = None
    b = w("beginn")
    if b:
        try:
            beginn = datetime.fromisoformat(str(b).replace("Z", "+00:00"))
            if beginn.tzinfo is None:
                beginn = beginn.replace(tzinfo=timezone.utc)
        except ValueError:
            beginn = None
    hinweis = w("ki_hinweis")
    return {"nummer": str(w("nummer") or "")[:40] or None, "name": str(w("name") or "")[:100] or None, "dauer": dauer,
            "zusammenfassung": str(w("zusammenfassung") or "")[:3000] or None, "ergebnis": str(w("ergebnis") or "")[:100] or None, "richtung": richtung,
            "ref": str(w("ref") or "")[:100] or None, "beginn": beginn, "ki_hinweis": str(hinweis).lower() in ("true", "1", "ja", "yes") if hinweis is not None else False}


def _pfade(d, vor="", tiefe=0) -> list:
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            pfad = f"{vor}{k}"
            if isinstance(v, dict) and tiefe < 3:
                out += _pfade(v, pfad + ".", tiefe + 1)
            else:
                out.append(f"{pfad} ({type(v).__name__})")
    return out


def probe(body: dict, kundennummer: str) -> dict:
    """Merkt sich nur die STRUKTUR der letzten Nachricht (Feldnamen und Typen, keine Inhalte), damit man nach einem Testanruf sieht, welche Felder der Anbieter schickt und was erkannt wurde."""
    f = _flach(body)
    erkannt, fehlt = {}, []
    for name, namen in ALIAS.items():
        treffer = next((a for a in namen if f.get(a) not in (None, "", [], {}) and not isinstance(f.get(a), (dict, list))), None)
        if treffer:
            erkannt[name] = treffer
        else:
            fehlt.append(name)
    return {"zeit": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kunde": kundennummer[:30], "felder": _pfade(body)[:60], "erkannt": erkannt, "nicht_erkannt": fehlt}


def kunden_geheimnis(g: str, kundennummer: str) -> str:
    """Eigenes Geheimnis je Kunde, abgeleitet aus dem Hauptgeheimnis. Wird eine Webhook-Adresse bekannt, gilt sie nur für diesen einen Kunden."""
    mac = hmac.new(g.encode(), b"telefon:" + kundennummer.encode(), "sha256").digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")[:32]


# ---------------------------------------------------------------- Einrichtung (Admin)
@router.get("/api/admin/einstellungen/telefon")
def einstellung(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        c = einstellungen.lesen(cur, "telefon")
        p = einstellungen.lesen(cur, "telefon_probe") or None
    return {"geheimnis_gesetzt": bool(c.get("geheimnis")), "url": config.BASE_URL + "/api/webhook/telefon/KUNDENNUMMER", "letzte_nachricht": p,
            "nur_pro_kunde": bool(c.get("nur_pro_kunde"))}


class NurProKundeIn(BaseModel):
    aktiv: bool


@router.post("/api/admin/einstellungen/telefon/nur-pro-kunde")
def nur_pro_kunde(data: NurProKundeIn, user: dict = Depends(require_admin)):
    """Schaltet das gemeinsame Geheimnis ab: danach gelten nur noch die Adressen je Kunde (vorher alle Anbieter umstellen!)."""
    with tx("admin") as cur:
        c = einstellungen.lesen(cur, "telefon")
        if not c.get("geheimnis"):
            raise HTTPException(409, "Es ist noch kein Geheimnis erzeugt.")
        einstellungen.schreiben(cur, "telefon", {**c, "nur_pro_kunde": data.aktiv})
        audit(cur, user, "einstellungen_telefon", None, {"nur_pro_kunde": data.aktiv})
    return {"ok": True, "nur_pro_kunde": data.aktiv}


@router.get("/api/admin/kunden/{kundennummer}/telefon-adresse")
def kunden_adresse(kundennummer: str, user: dict = Depends(require_admin)):
    """Die Webhook-Adresse für genau diesen Kunden (mit seinem eigenen Geheimnis)."""
    with tx("admin") as cur:
        g = einstellungen.lesen(cur, "telefon").get("geheimnis")
        if not g:
            raise HTTPException(409, "Zuerst unter Einstellungen → Telefon-Assistent ein Geheimnis erzeugen.")
        cur.execute("SELECT kundennummer FROM kunden WHERE kundennummer=%s", (kundennummer,))
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        audit(cur, user, "telefon_adresse_gezeigt", None, {"kundennummer": kundennummer})
    return {"url": f"{config.BASE_URL}/api/webhook/telefon/{kundennummer}?s={kunden_geheimnis(g, kundennummer)}"}


@router.post("/api/admin/einstellungen/telefon/neues-geheimnis")
def neues_geheimnis(user: dict = Depends(require_admin)):
    g = secrets.token_urlsafe(24)
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "telefon", {**einstellungen.lesen(cur, "telefon"), "geheimnis": g})
        audit(cur, user, "einstellungen_telefon", None, {"neues_geheimnis": True})
    return {"geheimnis": g}                      # wird nur dieses eine Mal angezeigt


# ---------------------------------------------------------------- Webhook
@router.post("/api/webhook/telefon/{kundennummer}")
async def webhook(kundennummer: str, request: Request):
    rate_limit("telhook:" + client_ip(request), 300, 3600)
    with tx("system") as cur:
        c = einstellungen.lesen(cur, "telefon")
    g = c.get("geheimnis")
    gegeben = request.headers.get("x-webhook-secret") or request.query_params.get("s") or ""
    eigenes = bool(g) and hmac.compare_digest(kunden_geheimnis(g, kundennummer).encode(), gegeben.encode())
    gemeinsames = bool(g) and not c.get("nur_pro_kunde") and hmac.compare_digest(g.encode(), gegeben.encode())
    if not (eigenes or gemeinsames):
        raise HTTPException(401, "Nicht berechtigt.")
    roh = await request.body()
    if len(roh) > 300_000:
        raise HTTPException(413, "Zu groß.")
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(400, "Ungültiges JSON.")
    if not isinstance(body, dict):
        raise HTTPException(400, "Ungültiges JSON.")
    d = lesen_daten(body)
    with tx("system") as cur:
        einstellungen.schreiben(cur, "telefon_probe", probe(body, kundennummer))
        cur.execute("SELECT id, status FROM kunden WHERE kundennummer=%s", (kundennummer,))
        k = cur.fetchone()
        if not k or k["status"] not in ("onboarding", "aktiv"):
            raise HTTPException(404, "Kunde nicht gefunden.")
        kid = k["id"]
        if d["ref"]:
            cur.execute("SELECT 1 FROM anrufe WHERE kunden_id=%s AND extern_ref=%s", (kid, d["ref"]))
            if cur.fetchone():
                return {"ok": True, "doppelt": True}
        anfrage_id = None
        if d["richtung"] == "ein" and (d["zusammenfassung"] or d["nummer"]):
            text = d["zusammenfassung"] or "Anruf ohne Zusammenfassung."
            if d["dauer"]:
                text += f"\n\n(Anruf, {d['dauer'] // 60}:{d['dauer'] % 60:02d} min – vom Telefon-Assistenten angenommen)"
            cur.execute("INSERT INTO anfragen (kunden_id, name, kontakt, nachricht, quelle) VALUES (%s,%s,%s,%s,'telefon') RETURNING id",
                        (kid, d["name"], d["nummer"], text))
            anfrage_id = cur.fetchone()["id"]
        cur.execute("""INSERT INTO anrufe (kunden_id, richtung, nummer, name, beginn, dauer_sek, ergebnis, zusammenfassung, ki_hinweis_gegeben, extern_ref, anfrage_id)
                       VALUES (%s,%s,%s,%s,coalesce(%s, now()),%s,%s,%s,%s,%s,%s)""",
                    (kid, d["richtung"], d["nummer"], d["name"], d["beginn"], d["dauer"], d["ergebnis"], d["zusammenfassung"], d["ki_hinweis"], d["ref"], anfrage_id))
        ids = push.kunde(cur, kid) if anfrage_id else []
    if ids:
        push.senden(ids, "Neuer Anruf", "Ihr Telefon-Assistent hat einen Anruf angenommen.", "/app#anrufe", "anruf")
    return {"ok": True, "anfrage": bool(anfrage_id)}


# ---------------------------------------------------------------- Kundenportal
@router.get("/api/kunde/anrufe")
def kunde_anrufe(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("""SELECT id, richtung, nummer, name, beginn, dauer_sek, ergebnis, zusammenfassung, anfrage_id FROM anrufe ORDER BY beginn DESC LIMIT 200""")
        zeilen = cur.fetchall()
        cur.execute("""SELECT count(*) FILTER (WHERE beginn > now() - interval '7 days') AS woche, count(*) FILTER (WHERE beginn > now() - interval '30 days') AS monat,
                              coalesce(round(avg(dauer_sek)), 0)::int AS dauer FROM anrufe WHERE richtung='ein'""")
        s = cur.fetchone()
    return {"anrufe": zeilen, "woche": s["woche"], "monat": s["monat"], "dauer_sek": s["dauer"]}
