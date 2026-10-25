"""Lead-Funnel (Kampagnen mit eigener Anmeldeseite /f/<name>) und Empfehlungsprogramm.
Alles ist ab Werk aus: eine Kampagne geht erst live, wenn ihr Rechtstext als geprüft eingetragen ist.
Prämien-Beträge legt nur der Admin je Empfehlung fest, es gibt keine Standardbeträge."""
import re
import secrets
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import config, einstellungen, leadeingang, mailer, push
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin, require_kunde

public = APIRouter(prefix="/api/public")
admin = APIRouter(prefix="/api/admin")
kunde = APIRouter(prefix="/api/kunde")
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[A-Za-z]{2,}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,39}$")
CODE_ZEICHEN = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
FESTE = ("empfehlung",)


def _empfehlung_einst(cur) -> dict:
    return {"aktiv": False, "beschreibung": "", **(einstellungen.lesen(cur, "empfehlung") or {})}


def _oeffentlich_bereit(k: dict | None, cur) -> bool:
    if not k or not k["aktiv"] or not k["rechtlich_geprueft_am"]:
        return False
    return not (k["slug"] == "empfehlung" and not _empfehlung_einst(cur)["aktiv"])


# ------------------------------------------------------------------ öffentlich

@public.get("/funnel/{slug}")
def seite(slug: str, request: Request):
    rate_limit("funnel-seite:" + client_ip(request), 120, 600)
    with tx("system") as cur:
        cur.execute("SELECT * FROM lead_kampagnen WHERE slug=%s", (slug,))
        k = cur.fetchone()
        if not _oeffentlich_bereit(k, cur):
            raise HTTPException(404, "Diese Seite gibt es nicht.")
        cur.execute("""INSERT INTO lead_kampagnen_tage (kampagne_id, tag, aufrufe) VALUES (%s, current_date, 1)
                       ON CONFLICT (kampagne_id, tag) DO UPDATE SET aufrufe = lead_kampagnen_tage.aufrufe + 1""", (k["id"],))
    return {"name": k["name"], "titel": k["titel"], "untertitel": k["untertitel"], "nutzen": k["nutzen"], "button": k["button"],
            "einwilligung_text": k["einwilligung_text"], "danke_titel": k["danke_titel"], "danke_text": k["danke_text"],
            "telefon_pflicht": k["telefon_pflicht"], "website_abfragen": k["website_abfragen"], "termin_anbieten": k["termin_anbieten"]}


class AnmeldungIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    firma: str | None = Field(default=None, max_length=200)
    email: str = Field(max_length=320)
    telefon: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=300)
    einwilligung: bool = False
    ref: str | None = Field(default=None, max_length=20)
    utm: dict[str, str] = {}
    zweitfeld: str | None = Field(default=None, max_length=200)   # Falle für Roboter: Menschen sehen das Feld nicht


@public.post("/funnel/{slug}")
def anmelden(slug: str, data: AnmeldungIn, request: Request, bg: BackgroundTasks):
    ip = client_ip(request)
    rate_limit("funnel-senden:" + ip, 20, 3600)
    if data.zweitfeld:
        return {"ok": True, "termin": False}
    email = data.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not data.einwilligung:
        raise HTTPException(400, "Ohne Ihre Einwilligung können wir Sie nicht kontaktieren.")
    utm = {k[:30]: v[:100] for k, v in list((data.utm or {}).items())[:8] if re.match(r"^(utm_[a-z]+|gclid|fbclid)$", k)}
    with tx("system") as cur:
        cur.execute("SELECT * FROM lead_kampagnen WHERE slug=%s", (slug,))
        k = cur.fetchone()
        if not _oeffentlich_bereit(k, cur):
            raise HTTPException(404, "Diese Seite gibt es nicht.")
        telefon = (data.telefon or "").strip() or None
        if k["telefon_pflicht"] and not telefon:
            raise HTTPException(400, "Bitte geben Sie eine Telefonnummer an, unter der wir Sie erreichen.")
        website = (data.website or "").strip() or None
        firma = (data.firma or "").strip() or data.name.strip()
        geber = None
        if slug == "empfehlung" and data.ref:
            cur.execute("SELECT id FROM kunden WHERE empfehlungscode=%s AND status NOT IN ('beendet')", (data.ref.strip().upper(),))
            g = cur.fetchone()
            geber = g and g["id"]
        quelle = "empfehlung" if geber else "website"
        cur.execute("SELECT id FROM leads WHERE lower(email)=%s ORDER BY erstellt_am LIMIT 1", (email,))
        l = cur.fetchone()
        neu = not l
        if neu:
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, quelle, temperatur, loeschen_nach, notiz, kampagne_id, utm, empfohlen_von)
                           VALUES (%s,%s,%s,%s,%s,%s,'heiss', current_date + interval '12 months', %s, %s, %s::jsonb, %s) RETURNING id""",
                        (firma, data.name.strip(), email, telefon, website, quelle, f"Über die Seite „{k['name']}“", k["id"],
                         __import__("json").dumps(utm), geber))
            lid = cur.fetchone()["id"]
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent',%s,'website')",
                        (lid, f"Einwilligung auf der Seite „{k['name']}“ erteilt (Text: {k['einwilligung_text'][:400]})"))
        else:
            lid = l["id"]
            cur.execute("""UPDATE leads SET temperatur='heiss', telefon=coalesce(telefon,%s), website=coalesce(website,%s), kampagne_id=coalesce(kampagne_id,%s),
                           loeschen_nach=greatest(loeschen_nach, current_date + interval '12 months') WHERE id=%s""", (telefon, website, k["id"], lid))
        if geber and neu:
            cur.execute("INSERT INTO empfehlungs_praemien (lead_id, kunden_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (lid, geber))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'website')",
                    (lid, f"Anmeldung über „{k['name']}“" + (" (Empfehlung eines Kunden)" if geber else "") + (f"; {', '.join(f'{a}={b}' for a, b in utm.items())}" if utm else "")))
        an = admin_empfaenger(cur)
        partner_ids = leadeingang.bearbeiten(cur, lid, neu, "Funnel")
        push_ids = push.admins(cur)
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                      VALUES (NULL, %s, %s, current_date, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                    (f"Neuer Funnel-Lead, bitte innerhalb einer Stunde anrufen: {firma}", an, f"lead-funnel-{lid}-{date.today().isoformat()}"))
        termin = bool(k["termin_anbieten"])
        name = k["name"]
    push.senden(push_ids + partner_ids, "Neuer Lead", f"{firma} über „{name}“: jetzt anrufen.", "/admin#lead/" + str(lid), "check")
    if an:
        bg.add_task(mailer.senden, an, f"Neuer Lead über „{name}“: {firma}",
                    f"{data.name.strip()} ({email}{', ' + telefon if telefon else ''}) hat sich über „{name}“ angemeldet. Bitte innerhalb einer Stunde anrufen.\n\n{config.BASE_URL}/admin#lead/{lid}")
    return {"ok": True, "termin": termin, "neu": neu}


# ------------------------------------------------------------------ Admin: Kampagnen

class KampagneIn(BaseModel):
    slug: str | None = Field(default=None, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    titel: str = Field(default="", max_length=160)
    untertitel: str = Field(default="", max_length=400)
    nutzen: list[str] = Field(default=[], max_length=6)
    button: str = Field(default="Kostenlos anfragen", min_length=2, max_length=60)
    einwilligung_text: str = Field(default="", max_length=800)
    danke_titel: str = Field(default="Vielen Dank!", max_length=120)
    danke_text: str = Field(default="Wir melden uns in Kürze bei Ihnen.", max_length=600)
    telefon_pflicht: bool = True
    website_abfragen: bool = True
    termin_anbieten: bool = True
    kosten_cent: int = Field(default=0, ge=0, le=100_000_000)
    notiz: str | None = Field(default=None, max_length=1000)
    rechtlich_geprueft: bool = False
    aktiv: bool = False


def _link(slug: str) -> str:
    return f"{config.BASE_URL.rstrip('/')}/f/{slug}"


@admin.get("/funnel")
def kampagnen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT k.*, coalesce((SELECT sum(aufrufe) FROM lead_kampagnen_tage t WHERE t.kampagne_id = k.id), 0)::int AS aufrufe,
                         count(l.id)::int AS leads,
                         count(l.id) FILTER (WHERE l.status IN ('termin','angebot','gewonnen'))::int AS termine,
                         count(l.id) FILTER (WHERE l.status = 'gewonnen' OR l.kunden_id IS NOT NULL)::int AS kunden
                       FROM lead_kampagnen k LEFT JOIN leads l ON l.kampagne_id = k.id GROUP BY k.id ORDER BY k.erstellt_am""")
        rows = cur.fetchall()
        einst = _empfehlung_einst(cur)
    for r in rows:
        r["link"] = _link(r["slug"])
        r["kosten_pro_lead_cent"] = round(r["kosten_cent"] / r["leads"]) if r["kosten_cent"] and r["leads"] else None
        r["kosten_pro_kunde_cent"] = round(r["kosten_cent"] / r["kunden"]) if r["kosten_cent"] and r["kunden"] else None
        r["feste"] = r["slug"] in FESTE
        r["rechtlich_geprueft"] = bool(r["rechtlich_geprueft_am"])
    return {"kampagnen": rows, "empfehlung": einst}


def _pruefen(d: KampagneIn):
    if d.aktiv and not d.rechtlich_geprueft:
        raise HTTPException(400, "Die Seite geht erst live, wenn der Rechtstext (Einwilligung, Datenschutz) geprüft ist. Bitte zuerst „Rechtlich geprüft“ eintragen.")
    if d.aktiv and not (d.titel.strip() and d.einwilligung_text.strip()):
        raise HTTPException(400, "Für eine aktive Seite braucht es eine Überschrift und den Einwilligungstext.")


@admin.post("/funnel")
def kampagne_neu(d: KampagneIn, user: dict = Depends(require_admin)):
    slug = (d.slug or "").strip().lower()
    if not SLUG.match(slug):
        raise HTTPException(400, "Der Seitenname darf nur Kleinbuchstaben, Ziffern und Bindestriche enthalten (2 bis 40 Zeichen).")
    _pruefen(d)
    with tx("admin") as cur:
        cur.execute("SELECT 1 FROM lead_kampagnen WHERE slug=%s", (slug,))
        if cur.fetchone():
            raise HTTPException(409, "Diesen Seitennamen gibt es schon.")
        cur.execute("""INSERT INTO lead_kampagnen (slug, name, titel, untertitel, nutzen, button, einwilligung_text, danke_titel, danke_text, telefon_pflicht, website_abfragen,
                         termin_anbieten, kosten_cent, notiz, aktiv, rechtlich_geprueft_am) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (slug, d.name.strip(), d.titel.strip(), d.untertitel.strip(), [n.strip() for n in d.nutzen if n.strip()], d.button.strip(), d.einwilligung_text.strip(),
                     d.danke_titel.strip(), d.danke_text.strip(), d.telefon_pflicht, d.website_abfragen, d.termin_anbieten, d.kosten_cent, d.notiz,
                     d.aktiv, date.today() if d.rechtlich_geprueft else None))
        kid = cur.fetchone()["id"]
        audit(cur, user, "funnel_neu", None, {"slug": slug})
    return {"id": kid, "link": _link(slug)}


@admin.put("/funnel/{kid}")
def kampagne_aendern(kid: str, d: KampagneIn, user: dict = Depends(require_admin)):
    _pruefen(d)
    with tx("admin") as cur:
        cur.execute("SELECT slug, rechtlich_geprueft_am FROM lead_kampagnen WHERE id=%s", (kid,))
        alt = cur.fetchone()
        if not alt:
            raise HTTPException(404, "Seite nicht gefunden.")
        geprueft = (alt["rechtlich_geprueft_am"] or date.today()) if d.rechtlich_geprueft else None
        cur.execute("""UPDATE lead_kampagnen SET name=%s, titel=%s, untertitel=%s, nutzen=%s, button=%s, einwilligung_text=%s, danke_titel=%s, danke_text=%s, telefon_pflicht=%s,
                         website_abfragen=%s, termin_anbieten=%s, kosten_cent=%s, notiz=%s, aktiv=%s, rechtlich_geprueft_am=%s WHERE id=%s""",
                    (d.name.strip(), d.titel.strip(), d.untertitel.strip(), [n.strip() for n in d.nutzen if n.strip()], d.button.strip(), d.einwilligung_text.strip(),
                     d.danke_titel.strip(), d.danke_text.strip(), d.telefon_pflicht, d.website_abfragen, d.termin_anbieten, d.kosten_cent, d.notiz, d.aktiv, geprueft, kid))
        audit(cur, user, "funnel_aendern", None, {"slug": alt["slug"], "aktiv": d.aktiv})
    return {"ok": True}


@admin.delete("/funnel/{kid}")
def kampagne_weg(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT slug FROM lead_kampagnen WHERE id=%s", (kid,))
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Seite nicht gefunden.")
        if k["slug"] in FESTE:
            raise HTTPException(400, "Diese Seite gehört zum Empfehlungsprogramm und lässt sich nicht löschen, nur ausschalten.")
        cur.execute("DELETE FROM lead_kampagnen WHERE id=%s", (kid,))
        audit(cur, user, "funnel_weg", None, {"slug": k["slug"]})
    return {"ok": True}


# ------------------------------------------------------------------ Admin: Empfehlungsprogramm

class EmpfehlungIn(BaseModel):
    aktiv: bool = False
    beschreibung: str = Field(default="", max_length=1000)


@admin.put("/empfehlung")
def empfehlung_einstellen(d: EmpfehlungIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT aktiv, rechtlich_geprueft_am FROM lead_kampagnen WHERE slug='empfehlung'")
        k = cur.fetchone()
        if d.aktiv and not (k and k["aktiv"] and k["rechtlich_geprueft_am"]):
            raise HTTPException(400, "Zuerst die Seite „empfehlung“ im Lead-Funnel rechtlich prüfen lassen und einschalten.")
        einstellungen.schreiben(cur, "empfehlung", {"aktiv": d.aktiv, "beschreibung": d.beschreibung.strip()})
        audit(cur, user, "empfehlung_einstellen", None, {"aktiv": d.aktiv})
    return {"ok": True}


@admin.get("/empfehlung/liste")
def empfehlung_liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT l.id AS lead_id, l.firma AS lead_firma, l.status, l.kunden_id, l.erstellt_am, g.id AS geber_id, g.firma AS geber, g.kundennummer AS geber_nr,
                         p.status AS praemie_status, p.betrag_cent, p.notiz
                       FROM leads l JOIN kunden g ON g.id = l.empfohlen_von LEFT JOIN empfehlungs_praemien p ON p.lead_id = l.id
                       ORDER BY l.erstellt_am DESC LIMIT 300""")
        return {"eintraege": cur.fetchall()}


class PraemieIn(BaseModel):
    status: str = Field(pattern="^(offen|ausgezahlt|verworfen)$")
    betrag_cent: int | None = Field(default=None, ge=0, le=10_000_000)
    notiz: str | None = Field(default=None, max_length=500)


@admin.put("/empfehlung/{lead_id}")
def praemie_setzen(lead_id: str, d: PraemieIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE empfehlungs_praemien SET status=%s, betrag_cent=%s, notiz=%s WHERE lead_id=%s RETURNING kunden_id", (d.status, d.betrag_cent, d.notiz, lead_id))
        if not cur.fetchone():
            raise HTTPException(404, "Empfehlung nicht gefunden.")
        audit(cur, user, "empfehlung_praemie", None, {"lead": lead_id, "status": d.status, "betrag_cent": d.betrag_cent})
    return {"ok": True}


# ------------------------------------------------------------------ Kunde

def _code(cur, kid) -> str:
    cur.execute("SELECT empfehlungscode FROM kunden WHERE id=%s", (kid,))
    c = cur.fetchone()["empfehlungscode"]
    while not c:
        neu = "".join(secrets.choice(CODE_ZEICHEN) for _ in range(8))
        cur.execute("UPDATE kunden SET empfehlungscode=%s WHERE id=%s AND empfehlungscode IS NULL AND NOT EXISTS (SELECT 1 FROM kunden WHERE empfehlungscode=%s)", (neu, kid, neu))
        if cur.rowcount:
            c = neu
        else:
            cur.execute("SELECT empfehlungscode FROM kunden WHERE id=%s", (kid,))
            c = cur.fetchone()["empfehlungscode"]
    return c


@kunde.get("/empfehlung")
def meine_empfehlung(user: dict = Depends(require_kunde)):
    with tx("system") as cur:
        cur.execute("SELECT aktiv, rechtlich_geprueft_am FROM lead_kampagnen WHERE slug='empfehlung'")
        k = cur.fetchone()
        einst = _empfehlung_einst(cur)
        if not (einst["aktiv"] and k and k["aktiv"] and k["rechtlich_geprueft_am"]):
            return {"aktiv": False}
        code = _code(cur, user["kunden_id"])
        cur.execute("""SELECT count(*)::int AS gesamt, count(*) FILTER (WHERE l.status='gewonnen' OR l.kunden_id IS NOT NULL)::int AS kunden
                       FROM leads l WHERE l.empfohlen_von=%s""", (user["kunden_id"],))
        z = cur.fetchone()
    link = f"{_link('empfehlung')}?ref={code}"
    return {"aktiv": True, "code": code, "link": link, "beschreibung": einst["beschreibung"], "gesamt": z["gesamt"], "kunden": z["kunden"],
            "whatsapp": "https://wa.me/?text=" + quote(f"Ich arbeite mit Markentrix und bin zufrieden. Schau dir das mal an: {link}")}
