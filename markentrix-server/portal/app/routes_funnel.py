"""Lead-Funnel (Kampagnen mit eigener Anmeldeseite /f/<name>) und Empfehlungsprogramm.
Alles ist ab Werk aus: eine Kampagne geht erst live, wenn ihr Rechtstext als geprüft eingetragen ist.
Prämien-Beträge legt nur der Admin je Empfehlung fest, es gibt keine Standardbeträge."""
import re
import secrets
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import config, einstellungen, funnelcheck, leadeingang, mailer, push
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import COOKIE, audit, client_ip, rate_limit, require_admin, require_kunde

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

ROBOTER = re.compile(r"bot|crawl|spider|slurp|facebookexternalhit|preview|headless|curl|wget|python|httpx", re.I)


@public.get("/funnel/{slug}")
def seite(slug: str, request: Request):
    rate_limit("funnel-seite:" + client_ip(request), 120, 600)
    with tx("system") as cur:
        cur.execute("SELECT * FROM lead_kampagnen WHERE slug=%s", (slug,))
        k = cur.fetchone()
        if not _oeffentlich_bereit(k, cur):
            raise HTTPException(404, "Diese Seite gibt es nicht.")
        # Eigene Besuche (angemeldet) und Roboter zählen nicht mit
        if not request.cookies.get(COOKIE) and not ROBOTER.search(request.headers.get("user-agent", "robot")):
            cur.execute("""INSERT INTO lead_kampagnen_tage (kampagne_id, tag, aufrufe) VALUES (%s, current_date, 1)
                           ON CONFLICT (kampagne_id, tag) DO UPDATE SET aufrufe = lead_kampagnen_tage.aufrufe + 1""", (k["id"],))
        firma = einstellungen.lesen(cur, "firma") or {}
    return {"name": k["name"], "titel": k["titel"], "untertitel": k["untertitel"], "nutzen": k["nutzen"], "button": k["button"],
            "einwilligung_text": k["einwilligung_text"], "danke_titel": k["danke_titel"], "danke_text": k["danke_text"],
            "telefon_pflicht": k["telefon_pflicht"], "website_abfragen": k["website_abfragen"] or k["vorlage"] == "website_check", "termin_anbieten": k["termin_anbieten"],
            "vorlage": k["vorlage"], "kicker": k["kicker"], "check_mail": k["vorlage"] == "website_check" and k["check_mail"],
            "firma": firma.get("name") or "Markentrix", "kontakt": {"telefon": firma.get("telefon") or "", "email": firma.get("email") or ""},
            "referenz": {"text": k["referenz_text"], "name": k["referenz_name"], "link": k["referenz_link"], "sterne": k["referenz_sterne"]} if k["referenz_text"] else None,
            "angebot": _angebot(k),
            "foto": "/static/funnel/inhaber.webp" if (config.STATIC_DIR / "funnel" / "inhaber.webp").is_file() else None}


def _angebot(k: dict) -> dict | None:
    """Preis-Abschnitt nur mit Preis; sind alle Plätze vergeben, wird er nicht mehr gezeigt."""
    if not k["angebot_preis"] or (k["plaetze_frei"] is not None and k["plaetze_frei"] <= 0):
        return None
    zaehler = k["plaetze_frei"] is not None and k["plaetze_gesamt"]
    zeitraum = k["plaetze_zeitraum"]
    if zaehler and k["plaetze_monatlich"]:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        zeitraum = "im " + MONATE[datetime.now(ZoneInfo("Europe/Berlin")).month - 1]
    return {"preis": k["angebot_preis"], "zusatz": k["angebot_zusatz"], "text": k["angebot_text"],
            "frei": k["plaetze_frei"] if zaehler else None, "gesamt": k["plaetze_gesamt"] if zaehler else None, "zeitraum": zeitraum if zaehler else ""}


MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def seite_datei(slug: str) -> str:
    """Welche HTML-Datei /f/<slug> ausliefert (die Inhalte lädt die Seite selbst über die öffentliche Schnittstelle)."""
    if not SLUG.match(slug or ""):
        return "funnel.html"
    with tx("system") as cur:
        cur.execute("SELECT vorlage FROM lead_kampagnen WHERE slug=%s", (slug,))
        k = cur.fetchone()
    return "funnel-check.html" if k and k["vorlage"] == "website_check" else "funnel.html"


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
        check = k["vorlage"] == "website_check"
        if check:
            website = funnelcheck.normalisieren(website)
            if not website:
                raise HTTPException(400, "Bitte geben Sie die Adresse Ihrer Website an, z. B. www.ihr-betrieb.de.")
        firma = (data.firma or "").strip() or (funnelcheck.host(website) if check else "") or data.name.strip()
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
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, website, quelle, temperatur, loeschen_nach, notiz, kampagne_id, utm, empfohlen_von, kampagne_seit)
                           VALUES (%s,%s,%s,%s,%s,%s,'heiss', current_date + interval '12 months', %s, %s, %s::jsonb, %s, now()) RETURNING id""",
                        (firma, data.name.strip(), email, telefon, website, quelle, f"Über die Seite „{k['name']}“", k["id"],
                         __import__("json").dumps(utm), geber))
            lid = cur.fetchone()["id"]
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent',%s,'website')",
                        (lid, f"Einwilligung auf der Seite „{k['name']}“ erteilt (Text: {k['einwilligung_text'][:400]})"))
        else:
            lid = l["id"]
            cur.execute("""UPDATE leads SET temperatur='heiss', telefon=coalesce(telefon,%s), website=coalesce(website,%s), kampagne_id=coalesce(kampagne_id,%s),
                           kampagne_seit=CASE WHEN kampagne_id IS NULL THEN now() ELSE kampagne_seit END,
                           loeschen_nach=greatest(loeschen_nach, current_date + interval '12 months') WHERE id=%s""", (telefon, website, k["id"], lid))
            # Neue Einwilligung auch bei bekannten Leads festhalten (z. B. importiert oder früher ohne Einwilligung)
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'consent',%s,'website')",
                        (lid, f"Einwilligung auf der Seite „{k['name']}“ erteilt (Text: {k['einwilligung_text'][:400]})"))
        if geber and neu:
            cur.execute("INSERT INTO empfehlungs_praemien (lead_id, kunden_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (lid, geber))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,'website')",
                    (lid, f"Anmeldung über „{k['name']}“" + (" (Empfehlung eines Kunden)" if geber else "") + (f"; {', '.join(f'{a}={b}' for a, b in utm.items())}" if utm else "")))
        an = admin_empfaenger(cur)
        partner_ids = leadeingang.bearbeiten(cur, lid, neu, "Funnel")
        push_ids = push.admins(cur)
        cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                      VALUES (NULL, %s, %s, current_date, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                    (f"Neuer Funnel-Lead, bitte sofort anrufen (am besten in 5 Minuten): {firma}", an, f"lead-funnel-{lid}-{date.today().isoformat()}"))
        termin = bool(k["termin_anbieten"])
        name = k["name"]
        check_token = check_id = None
        if check:
            check_token = secrets.token_urlsafe(18)
            cur.execute("INSERT INTO lead_checks (lead_id, website, status, token, kampagne_id) VALUES (%s,%s,'laeuft',%s,%s) RETURNING id", (lid, website[:300], check_token, k["id"]))
            check_id = cur.fetchone()["id"]
    push.senden(push_ids + partner_ids, "Neuer Lead", f"{firma} über „{name}“: jetzt anrufen.", "/admin#lead/" + str(lid), "check")
    if an:
        angaben = [("Name", data.name.strip()), ("Firma", firma if firma not in (data.name.strip(), funnelcheck.host(website) if website else "") else ""), ("Telefon", telefon or ""), ("E-Mail", email),
                   ("Website", funnelcheck.host(website) if website else ""), ("Seite", name)]
        bg.add_task(mailer.senden, an, f"Neuer Lead: {firma}, bitte jetzt anrufen",
                    f"Neuer Lead über „{name}“. Bitte sofort anrufen, am besten in den nächsten 5 Minuten.\n\n"
                    + "\n".join(f"{k}: {v}" for k, v in angaben if v) + f"\n\n{config.BASE_URL}/admin#lead/{lid}")
    if check_id:
        bg.add_task(funnelcheck.ausfuehren, check_id)
    return {"ok": True, "termin": termin, "neu": neu, "check": check_token}


@public.get("/funnel/{slug}/check/{token}")
def check_stand(slug: str, token: str, request: Request):
    """Stand des Website-Checks für die Danke-Ansicht (nur über das geheime Kennzeichen aus der Anmeldung)."""
    rate_limit("funnel-check:" + client_ip(request), 200, 600)
    if len(token) < 20 or len(token) > 40:
        raise HTTPException(404, "Nicht gefunden.")
    with tx("system") as cur:
        cur.execute("""SELECT c.status, c.ergebnis, c.lead_id, k.check_mail FROM lead_checks c JOIN lead_kampagnen k ON k.id = c.kampagne_id
                       WHERE c.token=%s AND k.slug=%s""", (token, slug))
        c = cur.fetchone()
        if c:
            c["check_mail"] = bool(c["check_mail"]) and funnelcheck.mail_wird_verschickt(cur, c["lead_id"])
    if not c:
        raise HTTPException(404, "Nicht gefunden.")
    if c["status"] != "fertig":
        return {"status": c["status"], "mail": c["check_mail"]}
    e = c["ergebnis"] or {}
    return {"status": "fertig", "mail": c["check_mail"], "ampel": e.get("ampel"), "score": e.get("score"), "zusammenfassung": e.get("zusammenfassung"),
            "website": funnelcheck.host(e.get("website")), "punkte": [{"titel": x["titel"], "status": x["status"], "text": x["text"]} for x in e.get("punkte", [])]}


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
    # Vorlage „Website-Check“ und Nachfass-Mails (None = unverändert lassen bzw. Standard der Datenbank)
    vorlage: str | None = Field(default=None, pattern="^(standard|website_check)$")
    kicker: str | None = Field(default=None, max_length=120)
    check_mail: bool | None = None
    check_betreff: str | None = Field(default=None, max_length=200)
    check_text: str | None = Field(default=None, max_length=4000)
    folge_aktiv: bool | None = None
    folge_tage: list[int] | None = Field(default=None, max_length=5)
    folge_betreffe: list[str] | None = Field(default=None, max_length=5)
    folge_texte: list[str] | None = Field(default=None, max_length=5)
    referenz_text: str | None = Field(default=None, max_length=600)
    referenz_name: str | None = Field(default=None, max_length=120)
    referenz_link: str | None = Field(default=None, max_length=400, pattern=r"^(|https://\S+)$")
    referenz_sterne: int | None = Field(default=None, ge=0, le=5)   # 0 = ohne Sterne
    angebot_preis: str | None = Field(default=None, max_length=40)
    angebot_zusatz: str | None = Field(default=None, max_length=40)
    angebot_text: str | None = Field(default=None, max_length=400)
    plaetze_frei: int | None = Field(default=None, ge=-1, le=999)     # -1 = ohne Zähler
    plaetze_gesamt: int | None = Field(default=None, ge=0, le=999)    # 0 = ohne Zähler
    plaetze_zeitraum: str | None = Field(default=None, max_length=40)
    plaetze_monatlich: bool | None = None


ZUSATZ = ("vorlage", "kicker", "check_mail", "check_betreff", "check_text", "folge_aktiv", "folge_tage", "folge_betreffe", "folge_texte",
          "referenz_text", "referenz_name", "referenz_link", "referenz_sterne",
          "angebot_preis", "angebot_zusatz", "angebot_text", "plaetze_frei", "plaetze_gesamt", "plaetze_zeitraum", "plaetze_monatlich")


def _zusatz_speichern(cur, kid, d: KampagneIn):
    werte = {f: getattr(d, f) for f in ZUSATZ if getattr(d, f) is not None}
    for f in ("kicker", "check_betreff", "check_text", "referenz_text", "referenz_name", "referenz_link", "angebot_preis", "angebot_zusatz", "angebot_text", "plaetze_zeitraum"):
        if f in werte:
            werte[f] = werte[f].strip()
    for f in ("folge_betreffe", "folge_texte"):
        if f in werte:
            werte[f] = [x.strip()[:4000] for x in werte[f]]
    if werte.get("plaetze_frei") == -1:
        werte["plaetze_frei"] = None
    if werte.get("plaetze_gesamt") == 0:
        werte["plaetze_gesamt"] = None
    if werte.get("referenz_sterne") == 0:
        werte["referenz_sterne"] = None
    if "referenz_sterne" in werte or d.referenz_sterne == 0:
        werte["referenz_sterne"] = werte.get("referenz_sterne")
    if werte:
        cur.execute("UPDATE lead_kampagnen SET " + ", ".join(f"{f}=%s" for f in werte) + " WHERE id=%s", (*werte.values(), kid))
    cur.execute("SELECT vorlage, check_mail, check_betreff, check_text, folge_aktiv, folge_tage, folge_betreffe, folge_texte FROM lead_kampagnen WHERE id=%s", (kid,))
    k = cur.fetchone()
    if k["check_mail"] and k["vorlage"] != "website_check":
        raise HTTPException(400, "Die Ergebnis-Mail gibt es nur bei der Vorlage „Website-Check“.")
    if k["check_mail"] and (len(k["check_betreff"]) < 3 or len(k["check_text"]) < 10):
        raise HTTPException(400, "Für die Ergebnis-Mail braucht es einen Betreff und einen Text.")
    tage = k["folge_tage"] or []
    if not (len(tage) == len(k["folge_betreffe"]) == len(k["folge_texte"])):
        raise HTTPException(400, "Je Nachfass-Mail braucht es einen Tag, einen Betreff und einen Text.")
    if any(t < 1 or t > 60 for t in tage) or any(b >= a for b, a in zip(tage, tage[1:])):
        raise HTTPException(400, "Die Tage der Nachfass-Mails müssen zwischen 1 und 60 liegen und aufsteigen (z. B. 1, 3, 7).")
    # Monatszähler: der laufende Monat gilt als begonnen, damit der Hintergrunddienst den eingetragenen Stand nicht sofort überschreibt
    cur.execute("""UPDATE lead_kampagnen SET plaetze_monat = date_trunc('month', (now() AT TIME ZONE 'Europe/Berlin'))::date
                   WHERE id=%s AND plaetze_monatlich AND plaetze_monat IS NULL""", (kid,))
    cur.execute("SELECT plaetze_frei, plaetze_gesamt FROM lead_kampagnen WHERE id=%s", (kid,))
    pl = cur.fetchone()
    if pl["plaetze_frei"] is not None and pl["plaetze_gesamt"] and pl["plaetze_frei"] > pl["plaetze_gesamt"]:
        raise HTTPException(400, "Es können nicht mehr Plätze frei sein, als es insgesamt gibt.")
    if k["folge_aktiv"] and (not tage or any(len(b) < 3 for b in k["folge_betreffe"]) or any(len(x) < 10 for x in k["folge_texte"])):
        raise HTTPException(400, "Für die Nachfass-Mails braucht jede Stufe einen Betreff und einen Text.")


def _link(slug: str) -> str:
    return f"{config.BASE_URL.rstrip('/')}/f/{slug}"


@admin.get("/funnel")
def kampagnen(tage: int = 0, user: dict = Depends(require_admin)):
    """`tage` = 0: alles seit Start; sonst die letzten 7/30/90 Tage mit Vergleich zur Zeit davor."""
    if tage not in (0, 7, 30, 90):
        raise HTTPException(400, "Zeitraum: 0, 7, 30 oder 90 Tage.")
    with tx("admin") as cur:
        cur.execute("""SELECT k.*,
                         coalesce((SELECT sum(aufrufe) FROM lead_kampagnen_tage t WHERE t.kampagne_id = k.id AND (%(t)s = 0 OR t.tag > current_date - %(t)s)), 0)::int AS aufrufe,
                         coalesce((SELECT sum(aufrufe) FROM lead_kampagnen_tage t WHERE t.kampagne_id = k.id AND %(t)s > 0 AND t.tag <= current_date - %(t)s AND t.tag > current_date - 2 * %(t)s), 0)::int AS aufrufe_vorher,
                         count(l.id) FILTER (WHERE %(t)s = 0 OR l.erstellt_am > now() - make_interval(days => %(t)s))::int AS leads,
                         count(l.id) FILTER (WHERE %(t)s > 0 AND l.erstellt_am <= now() - make_interval(days => %(t)s) AND l.erstellt_am > now() - make_interval(days => 2 * %(t)s))::int AS leads_vorher,
                         count(l.id) FILTER (WHERE l.status IN ('termin','angebot','gewonnen') AND (%(t)s = 0 OR l.erstellt_am > now() - make_interval(days => %(t)s)))::int AS termine,
                         count(l.id) FILTER (WHERE (l.status = 'gewonnen' OR l.kunden_id IS NOT NULL) AND (%(t)s = 0 OR l.erstellt_am > now() - make_interval(days => %(t)s)))::int AS kunden
                       FROM lead_kampagnen k LEFT JOIN leads l ON l.kampagne_id = k.id GROUP BY k.id ORDER BY k.erstellt_am""", {"t": tage})
        rows = cur.fetchall()
        einst = _empfehlung_einst(cur)
        # Standardtexte für neue Seiten direkt aus den Vorgaben der Datenbank (Probezeile, wird sofort verworfen)
        cur.execute("SAVEPOINT vorgabe")
        cur.execute("""INSERT INTO lead_kampagnen (slug, name) VALUES (%s, 'Vorgabe')
                       RETURNING check_betreff, check_text, folge_tage, folge_betreffe, folge_texte, angebot_text""", ("zz-" + secrets.token_hex(12),))
        vorgabe = cur.fetchone()
        cur.execute("ROLLBACK TO SAVEPOINT vorgabe")
    for r in rows:
        r["link"] = _link(r["slug"])
        r["kosten_pro_lead_cent"] = round(r["kosten_cent"] / r["leads"]) if tage == 0 and r["kosten_cent"] and r["leads"] else None
        r["kosten_pro_kunde_cent"] = round(r["kosten_cent"] / r["kunden"]) if tage == 0 and r["kosten_cent"] and r["kunden"] else None
        r["feste"] = r["slug"] in FESTE
        r["rechtlich_geprueft"] = bool(r["rechtlich_geprueft_am"])
    return {"kampagnen": rows, "empfehlung": einst, "vorgabe": vorgabe, "tage": tage}


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
        _zusatz_speichern(cur, kid, d)
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
        _zusatz_speichern(cur, kid, d)
        audit(cur, user, "funnel_aendern", None, {"slug": alt["slug"], "aktiv": d.aktiv, "check_mail": d.check_mail, "folge_aktiv": d.folge_aktiv})
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


# ------------------------------------------------------------------ Admin: neue Funnel-Leads sofort anzeigen

@admin.get("/funnel/neu")
def neue_leads(user: dict = Depends(require_admin)):
    """Funnel-Leads der letzten 30 Minuten, die noch niemand angerufen hat (für das Hinweisfenster im Portal)."""
    with tx("admin") as cur:
        cur.execute("""SELECT l.id, l.firma, l.ansprechpartner, l.telefon, l.website, l.score, k.name AS kampagne,
                              coalesce(l.kampagne_seit, l.erstellt_am) AS seit
                       FROM leads l JOIN lead_kampagnen k ON k.id = l.kampagne_id
                       WHERE coalesce(l.kampagne_seit, l.erstellt_am) > now() - interval '30 minutes'
                         AND NOT EXISTS (SELECT 1 FROM lead_aktivitaeten a WHERE a.lead_id = l.id AND a.art IN ('anruf','termin') AND a.zeit > coalesce(l.kampagne_seit, l.erstellt_am))
                       ORDER BY seit DESC LIMIT 5""")
        return {"leads": cur.fetchall()}


# ------------------------------------------------------------------ Admin: Website-Check (Einstellungen, Probe, PDF)

class CheckEinstIn(BaseModel):
    pagespeed: bool = False
    pagespeed_key: str | None = Field(default=None, max_length=200)


@admin.get("/funnel-check/einstellungen")
def check_einst(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        c = einstellungen.lesen(cur, "funnel_check") or {}
    return {"pagespeed": bool(c.get("pagespeed")), "pagespeed_key_gesetzt": bool(c.get("pagespeed_key"))}


@admin.put("/funnel-check/einstellungen")
def check_einst_speichern(d: CheckEinstIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "funnel_check") or {}
        key = (d.pagespeed_key or "").strip() or alt.get("pagespeed_key")
        if d.pagespeed_key is not None and d.pagespeed_key.strip() == "-":
            key = None
        einstellungen.schreiben(cur, "funnel_check", {"pagespeed": d.pagespeed, "pagespeed_key": key})
        audit(cur, user, "funnel_check_einstellungen", None, {"pagespeed": d.pagespeed})
    return {"ok": True}


def _pdf_antwort(e: dict) -> Response:
    with tx("system") as cur:
        firma = einstellungen.lesen(cur, "firma") or {}
    return Response(funnelcheck.pdf_bauen(e, firma), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{funnelcheck.dateiname(e)}"'})


@admin.get("/funnel-check/probe")
def check_probe(website: str, user: dict = Depends(require_admin)):
    """Probe-Check einer beliebigen Website als PDF (z. B. vor dem Start einer Kampagne). Legt keinen Lead an."""
    rate_limit("funnel-probe:" + str(user["id"]), 20, 600)
    url = funnelcheck.normalisieren(website)
    if not url:
        raise HTTPException(400, "Bitte eine gültige Website-Adresse eingeben, z. B. www.beispiel.de.")
    with tx("admin") as cur:
        cfg = einstellungen.lesen(cur, "funnel_check") or {}
    return _pdf_antwort(funnelcheck.pruefen(url, cfg))


@admin.get("/leads/{lid}/checks/{cid}/pdf")
def check_pdf(lid: str, cid: int, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        try:
            cur.execute("SELECT ergebnis FROM lead_checks WHERE id=%s AND lead_id=%s AND status='fertig'", (cid, lid))
        except Exception:
            raise HTTPException(404, "Nicht gefunden.")
        c = cur.fetchone()
    if not c or not (c["ergebnis"] or {}).get("punkte"):
        raise HTTPException(404, "Für diesen Check gibt es kein PDF.")
    return _pdf_antwort(c["ergebnis"])


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
