#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ElbDetail-Server: Formulare, Anfragen-Postfach, Gutscheine, Kalender, Statistik, Inhaltspflege.

Nur Python-Standardbibliothek. Läuft hinter Caddy (TLS, statische Dateien) auf dem eigenen Server.

    python3 server/app.py                  # Server starten (Konfiguration über Umgebungsvariablen)
    python3 server/app.py passwort         # Passwort-Hash für ADMIN_PASSWORD_HASH erzeugen
    python3 server/app.py build            # Website einmal bauen und veröffentlichen
"""
import base64
import collections
import csv
import datetime as dt
import getpass
import hashlib
import hmac
import html
import io
import json
import mimetypes
import os
import re
import secrets
import shutil
import smtplib
import sqlite3
import ssl
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "build"))
import md as mdlib  # noqa: E402


# --------------------------------------------------------------------------- Konfiguration
def env(name, default=""):
    return os.environ.get(name, default)


class Cfg:
    data = env("ELB_DATA", os.path.join(ROOT, "data"))
    content = env("ELB_CONTENT", os.path.join(ROOT, "content"))
    content_seed = env("ELB_CONTENT_SEED", os.path.join(ROOT, "content"))
    site_root = env("ELB_SITE_ROOT", os.path.join(ROOT, "site"))
    static = env("ELB_STATIC", os.path.join(ROOT, "static"))
    builder = env("ELB_BUILDER", os.path.join(ROOT, "build", "build.py"))
    serve_static = env("ELB_SERVE_STATIC", "0") == "1"
    host = env("HOST", "0.0.0.0")
    port = int(env("PORT", "8080"))
    public_url = env("PUBLIC_URL", "http://localhost:8080").rstrip("/")
    admin_user = env("ADMIN_USER", "admin")
    admin_hash = env("ADMIN_PASSWORD_HASH", "")
    admin_plain = env("ADMIN_PASSWORD", "")
    trust_proxy = env("TRUST_PROXY", "1") == "1"
    cookie_secure = env("COOKIE_SECURE", "1") == "1"
    smtp_host = env("SMTP_HOST")
    smtp_port = int(env("SMTP_PORT", "587") or 587)
    smtp_user = env("SMTP_USER")
    smtp_pass = env("SMTP_PASSWORD")
    smtp_from = env("SMTP_FROM")
    smtp_tls = env("SMTP_TLS", "starttls")  # starttls | ssl | none
    notify_to = env("NOTIFY_TO")
    autoreply = env("AUTOREPLY", "1") == "1"
    retention_days = int(env("RETENTION_DAYS", "365"))
    rate_requests = int(env("RATE_LIMIT_ANFRAGEN", "6"))
    stats_days = int(env("STATS_RETENTION_DAYS", "760"))
    secret = env("SECRET_KEY", "")


ADMIN_DIR = os.path.join(HERE, "admin")
STATUS = ["neu", "reserviert", "in_bearbeitung", "angebot_gesendet", "termin_bestaetigt", "erledigt", "abgelehnt", "storniert", "verfallen"]
V_STATUS = ["offen", "bezahlt", "eingeloest", "storniert"]
TYPES = ["kontakt", "termin", "gutschein", "firma", "widerruf"]
LOCK = threading.Lock()
BUILD_LOCK = threading.Lock()


try:  # Termine, Erinnerungen und Tagesgrenzen immer in deutscher Ortszeit, auch wenn der Container in UTC läuft
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(os.environ.get("ELB_TZ", "Europe/Berlin"))
except Exception:  # ohne Zeitzonendaten: Systemzeit
    TZ = None


def now():
    return (dt.datetime.now(TZ).replace(tzinfo=None) if TZ else dt.datetime.now()).replace(microsecond=0)


def today():
    return now().date()


def log(*a):
    print(now().isoformat(), *a, flush=True)


# --------------------------------------------------------------------------- Datenbank
SCHEMA = """
CREATE TABLE IF NOT EXISTS anfragen (
  id INTEGER PRIMARY KEY, ref TEXT UNIQUE, typ TEXT, status TEXT DEFAULT 'neu', created TEXT, updated TEXT,
  name TEXT, telefon TEXT, email TEXT, datum TEXT, data TEXT, notizen TEXT DEFAULT '', bewertung_angefragt TEXT
);
CREATE INDEX IF NOT EXISTS ix_anfragen_created ON anfragen(created);
CREATE TABLE IF NOT EXISTS gutscheine (
  id INTEGER PRIMARY KEY, code TEXT UNIQUE, token TEXT, art TEXT, wert INTEGER, paket TEXT, fuer TEXT, von TEXT, widmung TEXT,
  kaeufer TEXT, email TEXT, telefon TEXT, zustellung TEXT, status TEXT DEFAULT 'offen', created TEXT, paid_at TEXT, redeemed_at TEXT,
  valid_until TEXT, anfrage_id INTEGER, notiz TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, ts TEXT, day TEXT, type TEXT, name TEXT, path TEXT, ref TEXT, utm_s TEXT, utm_m TEXT, utm_c TEXT,
  device TEXT, visitor TEXT, props TEXT
);
CREATE INDEX IF NOT EXISTS ix_events_day ON events(day);
CREATE TABLE IF NOT EXISTS salts (day TEXT PRIMARY KEY, salt TEXT);
CREATE TABLE IF NOT EXISTS blocked (day TEXT PRIMARY KEY, reason TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, ts TEXT, action TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS outbox (
  id INTEGER PRIMARY KEY, ref TEXT, kind TEXT, to_addr TEXT, subject TEXT, body TEXT, attach TEXT, status TEXT,
  created TEXT, send_after TEXT DEFAULT '', sent_at TEXT, note TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_outbox_status ON outbox(status);
"""


class _DB:
    """Kontextmanager: öffnet eine Verbindung, committet bei Erfolg, schließt immer."""
    def __enter__(self):
        self.c = sqlite3.connect(os.path.join(Cfg.data, "elbdetail.db"), timeout=15)
        self.c.row_factory = sqlite3.Row
        self.c.execute("PRAGMA journal_mode=WAL")
        self.c.execute("PRAGMA busy_timeout=15000")
        return self.c

    def __exit__(self, et, ev, tb):
        try:
            if et is None:
                self.c.commit()
            else:
                self.c.rollback()
        finally:
            self.c.close()


def db():
    return _DB()


def init_db():
    os.makedirs(Cfg.data, exist_ok=True)
    with db() as c:
        c.executescript(SCHEMA)
        if not c.execute("SELECT 1 FROM settings WHERE key='closedWeekdays'").fetchone():
            c.execute("INSERT INTO settings VALUES ('closedWeekdays', '[0]')")


def setting(key, default=None):
    with db() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return json.loads(r["value"]) if r else default


def set_setting(key, value):
    with db() as c:
        c.execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))


def audit(action, detail="", conn=None):
    sql = "INSERT INTO audit(ts, action, detail) VALUES (?,?,?)"
    args = (now().isoformat(), action, str(detail)[:500])
    if conn is not None:
        conn.execute(sql, args)
        return
    with db() as c:
        c.execute(sql, args)


def secret_key():
    if Cfg.secret:
        return Cfg.secret.encode()
    p = os.path.join(Cfg.data, "secret.key")
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(secrets.token_hex(32))
        os.chmod(p, 0o600)
    return open(p).read().strip().encode()


# --------------------------------------------------------------------------- Inhalte
def content_json(name):
    with open(os.path.join(Cfg.content, name), encoding="utf-8") as f:
        return json.load(f)


def site_info():
    try:
        return content_json("site.json")
    except Exception:
        return {"name": "ElbDetail", "email": "", "whatsapp": "", "phoneDisplay": ""}


def pricing():
    try:
        return content_json("pricing.json")
    except Exception:
        return {"packages": [], "classes": [], "extras": []}


def seed_content():
    if not os.path.isdir(Cfg.content) or not os.listdir(Cfg.content):
        if os.path.realpath(Cfg.content) != os.path.realpath(Cfg.content_seed) and os.path.isdir(Cfg.content_seed):
            shutil.copytree(Cfg.content_seed, Cfg.content, dirs_exist_ok=True)
            log("Inhalte aus Vorlage übernommen:", Cfg.content_seed)


def merge_seed():
    """Übernimmt neue Dateien aus der mitgelieferten Vorlage (z. B. neue Ratgeber-Artikel), ohne Bestehendes zu überschreiben."""
    added = []
    for base, _, files in os.walk(Cfg.content_seed):
        for f in files:
            src = os.path.join(base, f)
            rel = os.path.relpath(src, Cfg.content_seed)
            if rel.startswith(".") or "/." in rel:
                continue
            dst = os.path.join(Cfg.content, rel)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                added.append(rel)
    return added


def make_backup():
    """Sichert Datenbank (konsistent über die SQLite-Backup-API) und Inhalte als .tar.gz unter <data>/backups."""
    import tarfile
    bdir = os.path.join(Cfg.data, "backups")
    os.makedirs(bdir, exist_ok=True)
    stamp = now().strftime("%Y%m%d-%H%M%S")
    dbcopy = os.path.join(bdir, f"db-{stamp}.sqlite")
    src = sqlite3.connect(os.path.join(Cfg.data, "elbdetail.db"))
    dst = sqlite3.connect(dbcopy)
    src.backup(dst)
    dst.close(); src.close()
    out = os.path.join(bdir, f"elbdetail-{stamp}.tar.gz")
    with tarfile.open(out, "w:gz") as t:
        t.add(dbcopy, arcname="elbdetail.db")
        t.add(Cfg.content, arcname="content", filter=lambda ti: None if "/.media-cache" in ti.name else ti)
    os.remove(dbcopy)
    for old in sorted(f for f in os.listdir(bdir) if f.startswith("elbdetail-"))[:-14]:
        os.remove(os.path.join(bdir, old))
    return out


# --------------------------------------------------------------------------- Veröffentlichen
def publish():
    """Baut die Website in ein neues Release-Verzeichnis und schaltet atomar um."""
    with BUILD_LOCK:
        rel_dir = os.path.join(Cfg.site_root, "releases")
        os.makedirs(rel_dir, exist_ok=True)
        name = now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
        out = os.path.join(rel_dir, name)
        t0 = time.time()
        p = subprocess.run([sys.executable, Cfg.builder, "--content", Cfg.content, "--static", Cfg.static, "--out", out],
                           capture_output=True, text=True, timeout=300)
        logtxt = (p.stdout + p.stderr).strip()
        if p.returncode != 0 or not os.path.exists(os.path.join(out, "index.html")):
            shutil.rmtree(out, ignore_errors=True)
            audit("veroeffentlichen_fehler", logtxt[-400:])
            return {"ok": False, "log": logtxt}
        cur = os.path.join(Cfg.site_root, "current")
        tmp = cur + ".tmp"
        if os.path.lexists(tmp):
            os.remove(tmp)
        os.symlink(os.path.join("releases", name), tmp)
        os.replace(tmp, cur)
        for old in sorted(os.listdir(rel_dir))[:-5]:
            shutil.rmtree(os.path.join(rel_dir, old), ignore_errors=True)
        warnings = [ln[len("Hinweis: "):] for ln in logtxt.splitlines() if ln.startswith("Hinweis: ")]
        info = {"ok": True, "release": name, "seconds": round(time.time() - t0, 1), "log": logtxt, "warnings": warnings, "at": now().isoformat()}
        set_setting("lastPublish", info)
        audit("veroeffentlicht", name)
        return info


def site_dir():
    return os.path.join(Cfg.site_root, "current")


# --------------------------------------------------------------------------- E-Mail
def mail_ready():
    return bool(Cfg.smtp_host and Cfg.smtp_from)


def send_mail(to, subject, text, reply_to=None, attachments=None):
    if not mail_ready() or not to:
        log("E-Mail übersprungen (SMTP nicht konfiguriert):", subject)
        return False
    msg = EmailMessage()
    s = site_info()
    msg["From"] = formataddr((s.get("name", "ElbDetail"), Cfg.smtp_from))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=Cfg.smtp_from.split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    for name, mime, data in attachments or []:  # z. B. ("termin.ics", "text/calendar", b"...")
        main, sub = mime.split("/", 1)
        msg.add_attachment(data, maintype=main, subtype=sub, filename=name)
    ctx = ssl.create_default_context()
    try:
        if Cfg.smtp_tls == "ssl":
            srv = smtplib.SMTP_SSL(Cfg.smtp_host, Cfg.smtp_port, timeout=20, context=ctx)
        else:
            srv = smtplib.SMTP(Cfg.smtp_host, Cfg.smtp_port, timeout=20)
            if Cfg.smtp_tls == "starttls":
                srv.starttls(context=ctx)
        if Cfg.smtp_user:
            srv.login(Cfg.smtp_user, Cfg.smtp_pass)
        srv.send_message(msg)
        srv.quit()
        return True
    except Exception as e:
        log("E-Mail-Fehler:", e)
        audit("mail_fehler", f"{subject}: {e}")
        return False


def mail_async(*a, **k):
    threading.Thread(target=send_mail, args=a, kwargs=k, daemon=True).start()


# --------------------------------------------------------------------------- Validierung
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[a-zA-Z]{2,}$")
LABELS = {"name": "Name", "telefon": "Telefon", "email": "E-Mail", "paket": "Paket", "klasse": "Fahrzeugklasse", "fahrzeug": "Fahrzeug",
          "zustand": "Zustand", "extras": "Extras", "abholung": "Abholung", "datum": "Wunschtermin", "datum2": "Ausweichtermin",
          "zeitfenster": "Zeitfenster", "uhrzeit": "Uhrzeit", "anzahlung": "Anzahlung", "winterschutz": "Schutz im Winterangebot", "scheibenumfang": "Scheiben", "gutscheincode": "Gutscheincode", "kanal": "Antwort per", "nachricht": "Nachricht",
          "bewertung_ok": "Bewertungsanfrage erlaubt", "art": "Gutscheinart", "wert": "Wert", "fuer": "Für", "von": "Von", "widmung": "Widmung",
          "zustellung": "Zustellung", "firma": "Firma", "anzahl": "Fahrzeuge", "intervall": "Intervall", "leistungen": "Leistungen", "quelle": "Quelle", "vorgang": "Vorgang / Gutscheincode"}


class Invalid(Exception):
    def __init__(self, errors):
        self.errors = errors


def _s(d, k, maxlen, req=False, errors=None, label=None):
    v = d.get(k, "")
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v)).strip()
    if len(v) > maxlen:
        errors[k] = f"{label or LABELS.get(k, k)} ist zu lang."
    if req and not v:
        errors[k] = f"{label or LABELS.get(k, k)} fehlt."
    return v[:maxlen]


def _list(d, k, allowed=None, maxitems=12, maxlen=80):
    v = d.get(k, [])
    if isinstance(v, str):
        v = [v] if v else []
    out = []
    for x in v[:maxitems]:
        x = str(x).strip()[:maxlen]
        if x and (allowed is None or x in allowed):
            out.append(x)
    return out


def _date(v):
    try:
        return dt.date.fromisoformat(v)
    except Exception:
        return None


def validate(d):
    errors = {}
    typ = d.get("typ")
    if typ not in TYPES:
        raise Invalid({"typ": "Unbekannte Anfrage."})
    out = {"typ": typ}
    out["name"] = _s(d, "name", 120, True, errors)
    out["telefon"] = _s(d, "telefon", 40, typ == "termin", errors)
    out["email"] = _s(d, "email", 160, typ in ("gutschein", "firma", "widerruf"), errors)
    if out["email"] and not EMAIL_RE.match(out["email"]):
        errors["email"] = "Bitte eine gültige E-Mail-Adresse angeben."
    if out["telefon"] and not re.match(r"^[0-9+()/ \-.]{5,40}$", out["telefon"]):
        errors["telefon"] = "Bitte eine gültige Telefonnummer angeben."
    out["nachricht"] = _s(d, "nachricht", 2000, False, errors)
    if typ != "widerruf" and d.get("einwilligung") not in ("ja", "on", True, "true"):  # Widerruf: Verarbeitung zur Erfüllung einer Rechtspflicht
        errors["einwilligung"] = "Bitte die Datenschutzhinweise bestätigen."
    pr = pricing()
    pkeys = [p["key"] for p in pr.get("packages", [])]
    ckeys = [c["key"] for c in pr.get("classes", [])]
    if typ == "kontakt":
        out["paket"] = _s(d, "paket", 120, True, errors)
        out["fahrzeug"] = _s(d, "fahrzeug", 120, False, errors)
        if not out["telefon"] and not out["email"]:
            errors["telefon"] = "Bitte Telefon oder E-Mail angeben."
    elif typ == "termin":
        out["paket"] = _s(d, "paket", 20, True, errors)
        if out["paket"] and out["paket"] not in pkeys + ["beratung", "keramik", "care"] + (["winter"] if winter_offer() else []) + (["scheiben"] if scheiben_items() else []):
            errors["paket"] = "Bitte ein Paket wählen."
        out["klasse"] = _s(d, "klasse", 20, True, errors)
        if out["klasse"] and out["klasse"] not in ckeys:
            errors["klasse"] = "Bitte eine Fahrzeugklasse wählen."
        out["fahrzeug"] = _s(d, "fahrzeug", 120, False, errors)
        out["zustand"] = _list(d, "zustand", ["tierhaare", "stark", "geruch", "leder", "flecken", "kratzer"])
        out["extras"] = _list(d, "extras", pr.get("extras"))
        if out["paket"] == "scheiben":
            sc = scheiben_items()
            out["scheibenumfang"] = d.get("scheibenumfang") if d.get("scheibenumfang") in sc else next(iter(sc), "")
        if out["paket"] == "winter":
            out["winterschutz"] = WINTERSCHUTZ["keramik" if d.get("winterschutz") in ("keramik", WINTERSCHUTZ["keramik"]) else "wachs"]
        out["abholung"] = d.get("abholung") if d.get("abholung") in ("nein", "anfrage") else "nein"
        out["zeitfenster"] = d.get("zeitfenster") if d.get("zeitfenster") in ("morgens", "vormittag", "nachmittag", "flexibel") else "flexibel"
        out["kanal"] = d.get("kanal") if d.get("kanal") in ("whatsapp", "anruf", "email") else "whatsapp"
        out["gutscheincode"] = _s(d, "gutscheincode", 20, False, errors).upper()
        out["bewertung_ok"] = "ja" if d.get("bewertung_ok") in ("ja", "on", True) else "nein"
        out["quelle"] = _s(d, "quelle", 40, False, errors)
        closed = setting("closedWeekdays", [0])
        blocked = blocked_days(keramik=ker_booking(out))
        for k in ("datum", "datum2"):
            raw = _s(d, k, 10, k == "datum", errors)
            if not raw:
                out[k] = ""
                continue
            day = _date(raw)
            if not day:
                errors[k] = "Ungültiges Datum."
            elif day < today():
                errors[k] = "Bitte ein Datum ab heute wählen."
            elif day > today() + dt.timedelta(days=400):
                errors[k] = "Bitte ein Datum innerhalb der nächsten 12 Monate wählen."
            elif ((day.weekday() + 1) % 7) in closed or raw in blocked:
                errors[k] = "An diesem Tag ist leider kein Termin möglich."
            out[k] = raw
        bc = booking_cfg()
        out["uhrzeit"] = d.get("uhrzeit") if d.get("uhrzeit") in bc["slotTimes"] else ""
        if self_booking():
            if not out["email"]:
                errors["email"] = "Bitte eine E-Mail-Adresse angeben. Dorthin schicken wir den Link zur Terminbestätigung."
            if not out["uhrzeit"]:
                errors["uhrzeit"] = "Bitte eine Uhrzeit wählen."
            elif out["datum"] and "datum" not in errors and not slot_free(out["datum"], out["uhrzeit"], keramik=ker_booking(out)):
                errors["uhrzeit"] = "Diese Uhrzeit ist leider gerade vergeben. Bitte eine andere wählen."
    elif typ == "gutschein":
        art = d.get("art") if d.get("art") in ("wert", "paket") else "wert"
        out["art"] = art
        vcfg = site_info().get("vouchers", {"minAmount": 25, "maxAmount": 1000})
        if art == "wert":
            raw = d.get("wunschbetrag") or d.get("betrag") or ""
            try:
                val = int(float(str(raw).replace(",", ".")))
            except ValueError:
                val = 0
            if not (vcfg.get("minAmount", 25) <= val <= vcfg.get("maxAmount", 1000)):
                errors["wunschbetrag"] = f"Bitte einen Betrag zwischen {vcfg.get('minAmount', 25)} und {vcfg.get('maxAmount', 1000)} € wählen."
            out["wert"] = val
            out["paket"] = ""
        else:
            pk = d.get("paket")
            if pk not in pkeys:
                errors["paket"] = "Bitte ein Paket wählen."
                out["wert"] = 0
            else:
                p = next(x for x in pr["packages"] if x["key"] == pk)
                out["wert"] = int(p["prices"].get(ckeys[0], 0)) if ckeys else 0
            out["paket"] = pk or ""
        out["fuer"] = _s(d, "fuer", 60, False, errors)
        out["von"] = _s(d, "von", 60, False, errors)
        out["widmung"] = _s(d, "widmung", 160, False, errors)
        out["zustellung"] = d.get("zustellung") if d.get("zustellung") in ("pdf", "abholung") else "pdf"
    elif typ == "widerruf":
        out["vorgang"] = _s(d, "vorgang", 40, True, errors).upper()
    elif typ == "firma":
        out["firma"] = _s(d, "firma", 160, True, errors)
        out["anzahl"] = _s(d, "anzahl", 30, False, errors)
        out["intervall"] = _s(d, "intervall", 40, False, errors)
        out["leistungen"] = _list(d, "leistungen")
    if errors:
        raise Invalid(errors)
    return out


def summary_text(data):
    pr = pricing()
    names = {p["key"]: p["name"] for p in pr.get("packages", [])}
    names.update({"beratung": "Beratung / Einzelleistung", "keramik": "Keramikversiegelung", "care": "ElbDetail Care", "scheiben": "Scheibenkeramik (C² Glass Ceramic)",
                  "winter": (pricing().get("winter") or {}).get("name", "Winterangebot")})
    cnames = {c["key"]: c["name"] for c in pr.get("classes", [])}
    lines = []
    for k, v in data.items():
        if k in ("typ",) or v in ("", [], None):
            continue
        if k == "paket":
            v = names.get(v, v)
        if k == "klasse":
            v = cnames.get(v, v)
        if k in ("datum", "datum2") and _date(v):
            v = _date(v).strftime("%d.%m.%Y")
        if k == "wert":
            v = f"{v} €"
        if k == "anzahlung":
            v = eur(float(v)) + f" ({data.get('depositPercent', 15)} %)"
        if isinstance(v, list):
            v = ", ".join(v)
        lines.append(f"{LABELS.get(k, k)}: {v}")
    return "\n".join(lines)


def winter_offer():
    w = pricing().get("winter")
    return w if w and (not w.get("validUntil") or w["validUntil"] >= today().isoformat()) else None


def scheiben_items():
    """Scheibenkeramik je Umfang mit gültigem Preis (laufende Aktion, z. B. Winter-Aktion, ersetzt den regulären Preis)."""
    a = next((x for x in pricing().get("addons", []) if x.get("key") == "scheiben"), None)
    if not a:
        return {}
    pr, t = a.get("promo") or {}, today().isoformat()
    promo = pr.get("prices", {}) if (not pr.get("validFrom") or pr["validFrom"] <= t) and (not pr.get("validUntil") or pr["validUntil"] >= t) else {}
    return {i["name"]: promo.get(i["name"], i["price"]) for i in a.get("items", []) if i.get("price") is not None}


def condition_surcharge(data):
    """Zuschlag in Prozent für angeklickte Zustandsangaben (5 % je Angabe, Tierhaare 10 %, Ledersitze ausgenommen)."""
    if data.get("paket") == "scheiben":
        return 0  # Zustand von Innenraum und Lack spielt für die Scheiben keine Rolle
    cfg = (site_info().get("booking") or {}).get("conditionSurcharge") or {}
    pct, over = float(cfg.get("percent", 0) or 0), cfg.get("overrides") or {}
    return sum(float(over.get(z, pct)) for z in data.get("zustand") or [] if z not in cfg.get("exempt", []))


def richtpreis(data):
    """Richtpreis laut Website inklusive Zustandszuschlag, auf volle Euro gerundet."""
    base = base_price(data)
    if base is None:
        return None
    return int(base * (1 + condition_surcharge(data) / 100) + 0.5)


WINTERSCHUTZ = {"wachs": "Wachsversiegelung (inklusive)", "keramik": "C² CarCeramic statt Wachs (Aufpreis nach Absprache)"}


def ker_booking(d):
    """Buchung mit Keramikversiegelung: eigenes Paket oder Winterangebot mit C² CarCeramic statt Wachs."""
    return d.get("paket") == "keramik" or (d.get("paket") == "winter" and d.get("winterschutz") == WINTERSCHUTZ["keramik"])


def base_price(data):
    if data.get("paket") == "scheiben":
        return scheiben_items().get(data.get("scheibenumfang"))
    if data.get("paket") == "winter":
        if ker_booking(data):
            return None  # Aufpreis für C² CarCeramic legt René fest, auch die Anzahlung
        return ((winter_offer() or {}).get("prices") or {}).get(data.get("klasse"))
    try:
        p = next(x for x in pricing()["packages"] if x["key"] == data.get("paket"))
        return p["prices"].get(data.get("klasse"))
    except StopIteration:
        return None


# --------------------------------------------------------------------------- Anfragen speichern
TITLES = {"kontakt": "Anfrage", "termin": "Terminanfrage", "gutschein": "Gutscheinbestellung", "firma": "Firmenanfrage", "widerruf": "Widerruf"}


def new_ref(typ):
    return {"kontakt": "K", "termin": "T", "gutschein": "G", "firma": "F", "widerruf": "W"}[typ] + now().strftime("%y%m%d") + "-" + secrets.token_hex(2).upper()


def store_request(data):
    ref = new_ref(data["typ"])
    ts = now().isoformat()
    status = "neu"
    if data["typ"] == "termin" and data.get("uhrzeit") and data.get("email") and self_booking():
        status = "reserviert"  # Online-Buchung: Uhrzeit ist reserviert, bis der Kunde per Link bestätigt
        data["token"] = secrets.token_urlsafe(24)
        # Frist läuft ab Versand des Links; bis René die E-Mail freigibt, bleibt die Uhrzeit höchstens 3 Tage vorgemerkt
        hold = max(72, booking_cfg()["holdHours"]) if approval_needed("reservierung") else booking_cfg()["holdHours"]
        data["hold_until"] = (now() + dt.timedelta(hours=hold)).isoformat()
        dep = deposit_amount(data)
        if dep:
            data["anzahlung"] = dep
            data["depositPercent"] = (site_info().get("booking") or {}).get("depositPercent", 15)
    with LOCK, db() as c:
        if status == "reserviert" and not slot_free(data["datum"], data["uhrzeit"], keramik=ker_booking(data)):
            raise Invalid({"uhrzeit": "Diese Uhrzeit wurde gerade vergeben. Bitte eine andere wählen."})
        cur = c.execute("INSERT INTO anfragen(ref, typ, status, created, updated, name, telefon, email, datum, data) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (ref, data["typ"], status, ts, ts, data.get("name"), data.get("telefon"), data.get("email"), data.get("datum", ""),
                         json.dumps(data, ensure_ascii=False)))
        aid = cur.lastrowid
        if data["typ"] == "gutschein":
            create_voucher(c, data, aid)
    notify(ref, data, status)
    return ref, status


def handle_widerruf(ref, data):
    """Widerruf über das Formular: Eingang sofort bestätigen (ohne Freigabe), passenden Online-Termin innerhalb der Frist direkt stornieren und erstatten."""
    s = site_info()
    at = now()
    done = ""
    if re.match(r"^T\d{6}-[0-9A-F]{4}$", data.get("vorgang", "")):
        r, d = load_termin(data["vorgang"])
        if r and (d.get("email") or "").lower() == data["email"].lower() and r["status"] == "termin_bestaetigt" and in_widerruf(d):
            d["widerruf_am"] = at.isoformat()
            save_termin(r["id"], d)
            cancel_termin(r, d, "widerruf", confirm=False)
            r, d = load_termin(data["vorgang"])
            done = widerruf_refund_line(d)
    mail_async(Cfg.notify_to or s.get("email"), f"Widerruf eingegangen: {data.get('name')} ({ref})",
               f"Über das Widerrufsformular der Website ist am {at.strftime('%d.%m.%Y um %H:%M')} Uhr ein Widerruf eingegangen.\n"
               + (f"Der Online-Termin {data['vorgang']} wurde automatisch storniert. {done}\n" if done else
                  "Bitte den Vorgang prüfen und Zahlungen innerhalb von 14 Tagen erstatten.\n")
               + f"\n{summary_text(data)}\n\nIm Verwaltungsportal: {Cfg.public_url}/admin/#/anfragen/{ref}\n", reply_to=data.get("email") or None)
    customer_mail("widerruf", ref, data["email"], f"Eingangsbestätigung Ihres Widerrufs ({ref})",
                  f"Guten Tag {data.get('name', '').strip()},\n\nhiermit bestätigen wir den Eingang Ihres Widerrufs am {at.strftime('%d.%m.%Y um %H:%M')} Uhr.\n\n"
                  f"Inhalt Ihres Widerrufs:\n{summary_text(data)}\n\n"
                  + (f"Der Termin {data['vorgang']} ist abgesagt. {done}\n\n" if done else
                     "Bereits geleistete Zahlungen erstatten wir unverzüglich, spätestens binnen 14 Tagen, über dasselbe Zahlungsmittel.\n\n")
                  + mail_footer())


def notify(ref, data, status="neu"):
    s = site_info()
    if data["typ"] == "widerruf":
        return handle_widerruf(ref, data)
    title = TITLES[data["typ"]]
    rp = richtpreis(data)
    body = f"Neue {title} über die Website ({ref})\n\n{summary_text(public_data(data))}\n"
    if status == "reserviert":
        title = "Online-Buchung"
        dep = f"Vorgeschlagene Anzahlung: {eur(data['anzahlung'])}" if data.get("anzahlung") else "Kein Festpreis hinterlegt: Bitte die Anzahlung festlegen."
        todo = ("Bitte im Portal unter Postausgang die E-Mail an den Kunden prüfen, die Anzahlung bei Bedarf ändern und freigeben."
                if approval_needed("reservierung") else "Der Kunde hat den Link zur Bestätigung bereits erhalten.")
        body = (f"Neue Online-Buchung ({ref}): {de_when(data)}\n{dep}\n{todo}\n\n{summary_text(public_data(data))}\n\n"
                f"Postausgang: {Cfg.public_url}/admin/#/postausgang\n")
    if rp:
        sur = condition_surcharge(data)
        body += f"\nRichtpreis laut Website: ab {rp} €" + (f" (inkl. {sur:g} % Zuschlag für den Zustand)" if sur else "") + "\n"
    body += f"\nIm Verwaltungsportal öffnen: {Cfg.public_url}/admin/#/anfragen/{ref}\n"
    mail_async(Cfg.notify_to or s.get("email"), f"{title}: {data.get('name')} ({ref})", body, reply_to=data.get("email") or None)
    if status == "reserviert":
        mail_reservation(ref, data)
    elif Cfg.autoreply and data.get("email"):
        greet = f"Guten Tag {data.get('name', '').strip()},".replace("Tag ,", "Tag,")
        extra = ""
        if data["typ"] == "termin":
            extra = "Wir prüfen Ihren Wunschtermin und melden uns mit einer Bestätigung und einem verbindlichen Angebot.\n"
        elif data["typ"] == "gutschein":
            pay = setting("zahlungshinweis", "") or "Die Zahlungsdaten senden wir Ihnen in Kürze."
            extra = f"Vielen Dank für Ihre Gutscheinbestellung über {data.get('wert')} €.\n\n{pay}\n\nNach Zahlungseingang erhalten Sie den Gutschein als Link zum Ausdrucken.\n"
        else:
            extra = "Wir melden uns so schnell wie möglich bei Ihnen.\n"
        text = (f"{greet}\n\nvielen Dank für Ihre {title} bei {s.get('name', 'ElbDetail')}. {extra}\nIhre Angaben ({ref}):\n{summary_text(data)}\n\n"
                f"Fragen? Antworten Sie einfach auf diese E-Mail oder schreiben Sie uns per WhatsApp: {s.get('phoneIntl', '')}\n\n"
                f"Viele Grüße\n{s.get('name', 'ElbDetail')}\n{s.get('address', {}).get('street', '')}, {s.get('address', {}).get('zip', '')} {s.get('address', {}).get('city', '')}\n{Cfg.public_url}\n")
        customer_mail("eingang", ref, data["email"], f"Ihre {title} bei {s.get('name', 'ElbDetail')} ({ref})", text)


# --------------------------------------------------------------------------- Gutscheine
CODE_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_code(c):
    while True:
        code = "ELB-" + "".join(secrets.choice(CODE_ALPHA) for _ in range(4)) + "-" + "".join(secrets.choice(CODE_ALPHA) for _ in range(4))
        if not c.execute("SELECT 1 FROM gutscheine WHERE code=?", (code,)).fetchone():
            return code


def create_voucher(c, data, anfrage_id=None):
    code = new_code(c)
    valid = dt.date(today().year + 3, 12, 31).isoformat()
    c.execute("""INSERT INTO gutscheine(code, token, art, wert, paket, fuer, von, widmung, kaeufer, email, telefon, zustellung, status, created, valid_until, anfrage_id)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (code, secrets.token_urlsafe(18), data.get("art", "wert"), int(data.get("wert") or 0), data.get("paket", ""), data.get("fuer", ""),
               data.get("von", ""), data.get("widmung", ""), data.get("name", ""), data.get("email", ""), data.get("telefon", ""),
               data.get("zustellung", "pdf"), "offen", now().isoformat(), valid, anfrage_id))
    return code


def voucher_link(v):
    return f"{Cfg.public_url}/gutschein/{v['code']}?t={v['token']}"


def voucher_html(v):
    s = site_info()
    pr = pricing()
    pname = next((p["name"] for p in pr.get("packages", []) if p["key"] == v["paket"]), "")
    value = html.escape(pname) if v["art"] == "paket" and pname else f"{v['wert']} €"
    desc = "Fahrzeugaufbereitung für einen Kleinwagen" if v["art"] == "paket" else "für eine Fahrzeugaufbereitung nach Wahl"
    valid = dt.date.fromisoformat(v["valid_until"]).strftime("%d.%m.%Y")
    state = {"offen": "Noch nicht bezahlt – wird nach Zahlungseingang gültig.", "storniert": "Dieser Gutschein wurde storniert.",
             "eingeloest": "Dieser Gutschein wurde bereits eingelöst."}.get(v["status"], "")
    E = html.escape
    a = s.get("address", {})
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Gutschein {E(v['code'])} | {E(s.get('name', 'ElbDetail'))}</title>
<style>
@font-face{{font-family:Inter;font-weight:100 900;src:url(/fonts/inter-var.woff2) format("woff2")}}@font-face{{font-family:"Instrument Serif";font-style:italic;src:url(/fonts/instrument-serif-italic.woff2) format("woff2")}}
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;padding:24px 16px;font:15px/1.5 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#f4f5f7;color:#161a21}}
.wrap{{max-width:820px;margin:0 auto;display:grid;gap:16px}}
.card{{position:relative;overflow:hidden;border-radius:20px;padding:32px;color:#f4f6f9;background:radial-gradient(circle at 85% 15%,rgba(91,155,232,.45),transparent 45%),linear-gradient(140deg,#262c36,#15181d);display:grid;gap:10px;min-height:420px}}
.top{{display:flex;justify-content:space-between;align-items:center}}.top img{{height:46px}}.top span{{font-weight:600;font-size:13px;letter-spacing:.3em;text-transform:uppercase;color:#5b9be8}}
.val{{font-weight:300;font-size:64px;letter-spacing:-.03em;line-height:1;margin-top:28px}}.desc{{color:#9ea6b3}}
.names{{display:flex;gap:28px;flex-wrap:wrap;color:#9ea6b3}}.names b{{color:#fff}}.msg{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;font-size:24px;line-height:1.3;min-height:1.4em}}
.foot{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.15);padding-top:12px;font-size:13px;color:#c7cdd6}}
.code{{font:700 18px/1 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.08em;color:#fff}}
.state{{background:#fff3cd;border:1px solid #f1d9a0;color:#4d3a0f;padding:12px 16px;border-radius:12px;font-weight:600}}
.how{{background:#fff;border-radius:16px;padding:20px 22px;border:1px solid #dfe3e9}}.how h2{{margin:0 0 8px;font-weight:650;letter-spacing:-.02em}}
.btn{{display:inline-block;background:#1c4f9c;color:#fff;border:0;border-radius:999px;padding:12px 22px;font:inherit;font-weight:650;cursor:pointer;text-decoration:none}}
@media print{{body{{background:#fff;padding:0}}.noprint{{display:none!important}}.card{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body><div class="wrap">
{f'<p class="state">{E(state)}</p>' if state else ''}
<div class="card"><div class="top"><img src="/logo.svg" alt="{E(s.get('name', 'ElbDetail'))}"><span>Gutschein</span></div>
<div class="val">{value}</div><div class="desc">{desc}</div>
<div class="names">{f'<span>Für <b>{E(v["fuer"])}</b></span>' if v['fuer'] else ''}{f'<span>Von <b>{E(v["von"])}</b></span>' if v['von'] else ''}</div>
<p class="msg">{E(v['widmung'] or '')}</p>
<div class="foot"><span>Code <span class="code">{E(v['code'])}</span></span><span>Gültig bis {valid}</span><span>{E(s.get('name', ''))} · {E(a.get('street', ''))}, {E(a.get('zip', ''))} {E(a.get('city', ''))}</span></div></div>
<div class="how"><h2>So wird der Gutschein eingelöst</h2><p>Termin über <b>{E(Cfg.public_url.split('//')[-1])}/termin.html</b> anfragen und den Code im Feld „Gutscheincode“ eintragen, oder per WhatsApp an {E(s.get('phoneIntl', ''))} mit dem Code schreiben. Paketgutscheine gelten für einen Kleinwagen; bei größeren Fahrzeugen wird nur die Differenz fällig.</p></div>
<p class="noprint"><button class="btn" id="printBtn" type="button">Drucken oder als PDF speichern</button></p>
</div><script src="/gutschein-druck.js"></script></body></html>"""


def booking_policy():
    return (site_info().get("booking") or {}).get("policy", "")


def termin_html(r, d, notice="", mode="", tag=""):
    """Seite hinter dem E-Mail-Link: Termin bestätigen, verschieben oder absagen."""
    s = site_info()
    E = html.escape
    st = r["status"]
    tok = E(d.get("token", ""))
    base = f"/termin/{E(r['ref'])}?t={tok}"
    act = lambda a, label, cls="btn", extra="": (f'<form method="post" action="/termin/{E(r["ref"])}/{a}"><input type="hidden" name="t" value="{tok}">{extra}'
                                                 f'<button class="{cls}" type="submit">{label}</button></form>')
    owner = E((s.get("about") or {}).get("name") or "Wir")
    paid = is_paid(d)
    future = bool(termin_start(d) and termin_start(d) > now())
    policy = f'<p class="small"><strong>Verschieben und Absagen:</strong> {E(booking_policy())}</p>' if d.get("anzahlung") and booking_policy() else ""
    extra_html = ""
    checks = ('<label class="chk"><input type="checkbox" name="agb" value="1" required> <span>Ich habe die <a href="/agb.html" target="_blank" rel="noopener">AGB</a> '
              'und die <a href="/agb.html#widerruf" target="_blank" rel="noopener">Widerrufsbelehrung</a> gelesen.</span></label>'
              + ('<label class="chk"><input type="checkbox" name="vorzeitig" value="1" required> <span>Mein Termin liegt innerhalb der 14-tägigen Widerrufsfrist. '
                 'Ich verlange ausdrücklich, dass ElbDetail vor Ablauf der Widerrufsfrist mit der Leistung beginnt. Mir ist bekannt, dass ich bei einem Widerruf einen '
                 'anteiligen Betrag für bereits erbrachte Leistungen zahle und mein Widerrufsrecht erlischt, sobald die Leistung vollständig erbracht ist.</span></label>'
                 if early_start(d) else ""))
    wbis = widerruf_bis(d)
    can_withdraw = st == "termin_bestaetigt" and future and in_widerruf(d)
    if st == "reserviert" and d.get("hold_until", "") >= now().isoformat():
        if deposit_me(d) and d.get("paypalme_am"):
            head = "Wir prüfen Ihre Anzahlung"
            text = (f"Danke! Sobald Ihre Anzahlung von {eur(d['anzahlung'])} bei uns eingegangen ist, bestätigen wir den Termin per E-Mail. "
                    "Haben Sie die Zahlung noch nicht abgeschlossen, geht es hier weiter.")
            btns = (f'<a class="btn" href="{E(paypal_me_link(d))}" rel="noopener">Zur PayPal-Zahlung ({eur(d["anzahlung"])})</a>'
                    + act("absagen", "Doch nicht, Reservierung freigeben", "btn ghost"))
        elif deposit_me(d):
            head = "Anzahlung leisten und Termin bestätigen"
            text = (f"Mit der Anzahlung von {eur(d['anzahlung'])} per PayPal ist Ihr Termin gebucht. Sie werden zu PayPal weitergeleitet, der Betrag ist schon eingetragen. "
                    f"Bitte als Verwendungszweck „{E(r['ref'])}“ angeben. Die Anzahlung wird mit dem Endpreis verrechnet.")
            btns = act("bestaetigen", f"Anzahlung {eur(d['anzahlung'])} mit PayPal senden", extra=checks) + act("absagen", "Doch nicht, Reservierung freigeben", "btn ghost")
        elif deposit_online(d):
            head = "Anzahlung leisten und Termin bestätigen"
            text = (f"Mit der Anzahlung von {eur(d['anzahlung'])} per PayPal ist Ihr Termin verbindlich gebucht. "
                    "Die Anzahlung wird mit dem Endpreis verrechnet.")
            btns = act("bestaetigen", f"Anzahlung {eur(d['anzahlung'])} mit PayPal leisten", extra=checks) + act("absagen", "Doch nicht, Reservierung freigeben", "btn ghost")
        else:
            head, text = "Bitte bestätigen Sie Ihren Termin", "Ein Klick genügt, dann ist der Termin verbindlich gebucht."
            btns = act("bestaetigen", "Termin verbindlich bestätigen", extra=checks) + act("absagen", "Doch nicht, Reservierung freigeben", "btn ghost")
    elif st == "termin_bestaetigt" and future and mode == "verschieben":
        head = "Termin verschieben"
        text = "Wählen Sie einen neuen Tag und eine Abgabezeit." + (" Ihre Anzahlung bleibt erhalten." if paid or d.get("anzahlung") else "")
        lead = max(0, int(setting("leadDays", 1) or 0))
        mind = (today() + dt.timedelta(days=lead)).isoformat()
        extra_html = (f'<form method="get" action="/termin/{E(r["ref"])}" class="pick"><input type="hidden" name="t" value="{tok}"><input type="hidden" name="aktion" value="verschieben">'
                      f'<label>Neuer Tag<input type="date" name="tag" min="{mind}" value="{E(tag)}" required></label><button class="btn ghost" type="submit">Freie Uhrzeiten zeigen</button></form>')
        btns = f'<a class="btn ghost" href="{base}">Zurück</a>'
        if tag and _date(tag):
            free = [x["zeit"] for x in free_slots(tag, exclude_ref=r["ref"], keramik=ker_booking(d))
                    if x["frei"] and not (tag == d.get("datum") and x["zeit"] == d.get("uhrzeit"))]  # bisherige Uhrzeit nicht anbieten
            if free:
                radios = "".join(f'<label class="slot"><input type="radio" name="uhrzeit" value="{t}" required{" checked" if i == 0 else ""}> {t} Uhr</label>' for i, t in enumerate(free))
                btns = act("verschieben", "Auf diesen Termin verschieben", extra=f'<input type="hidden" name="datum" value="{E(tag)}"><div class="slots">{radios}</div>') + btns
            else:
                extra_html += '<p class="note">An diesem Tag ist leider keine Uhrzeit mehr frei. Bitte wählen Sie einen anderen Tag.</p>'
    elif can_withdraw and mode == "widerrufen":
        head = "Vertrag widerrufen"
        text = (f"Sie können den Vertrag bis zum {wbis.strftime('%d.%m.%Y')} ohne Angabe von Gründen widerrufen. Der Termin wird dann abgesagt"
                + (f" und Ihre Anzahlung von {eur(d['zahlung']['value'])} über PayPal erstattet." if paid else ".")
                + " Die Eingangsbestätigung erhalten Sie sofort per E-Mail.")
        extra_html = (f'<dl><div><dt>Name</dt><dd>{E(d.get("name", ""))}</dd></div><div><dt>Vertrag</dt><dd>Termin {E(r["ref"])}</dd></div>'
                      f'<div><dt>Bestätigung an</dt><dd>{E(d.get("email", ""))}</dd></div></dl>')
        btns = act("widerrufen", "Widerruf bestätigen", extra='<input type="hidden" name="ok" value="1">') + f'<a class="btn ghost" href="{base}">Zurück</a>'
    elif st == "termin_bestaetigt" and future and mode == "absagen" and in_widerruf(d):
        head = "Termin wirklich absagen?"
        text = (f"Sie sind noch innerhalb der Widerrufsfrist (bis {wbis.strftime('%d.%m.%Y')}). Wenn Sie den Termin jetzt absagen, gilt das als Widerruf"
                + (f" und wir erstatten Ihre Anzahlung von {eur(d['zahlung']['value'])} vollständig." if paid else ".")
                + " Sie können den Termin stattdessen auch kostenlos verschieben.")
        btns = (f'<a class="btn" href="{base}&aktion=verschieben">Lieber verschieben</a>'
                + act("absagen", "Ja, Termin absagen", "btn ghost", '<input type="hidden" name="ok" value="1">'))
    elif st == "termin_bestaetigt" and future and mode == "absagen":
        head = "Termin wirklich absagen?"
        text = (f"Wenn Sie den Termin ganz absagen, wird Ihre Anzahlung von {eur(d['zahlung']['value'])} als Ausfallpauschale einbehalten, weil wir den Termin für Sie freigehalten haben. "
                "Ist uns kein oder ein geringerer Schaden entstanden, können Sie uns das nachweisen. Verschieben ist dagegen kostenlos, die Anzahlung bleibt dann erhalten.") if paid else "Möchten Sie den Termin wirklich absagen? Sie können ihn stattdessen auch kostenlos verschieben."
        btns = (f'<a class="btn" href="{base}&aktion=verschieben">Lieber verschieben</a>'
                + act("absagen", "Ja, Termin endgültig absagen" + (" (Anzahlung verfällt)" if paid else ""), "btn ghost", '<input type="hidden" name="ok" value="1">'))
    elif st == "termin_bestaetigt":
        head = "Ihr Termin ist bestätigt"
        text = f"{owner} meldet sich vorab telefonisch bei Ihnen und sieht sich Ihr Fahrzeug vor der Aufbereitung genau an. So erhalten Sie den verbindlichen Preis, bevor wir anfangen."
        if paid:
            text += f" Ihre Anzahlung von {eur(d['zahlung']['value'])} ist eingegangen."
        btns = (f'<a class="btn" href="{base}&aktion=verschieben">Termin verschieben</a><a class="btn ghost" href="{base}&aktion=absagen">Termin absagen</a>') if future else ""
        if can_withdraw:
            btns += f'<a class="btn ghost" href="{base}&aktion=widerrufen">Vertrag widerrufen</a>'
            text += f" Widerrufsrecht: Sie können den Vertrag bis zum {wbis.strftime('%d.%m.%Y')} widerrufen."
    elif st == "storniert":
        head, text, btns = "Termin abgesagt", "Der Termin ist abgesagt. Sie können jederzeit einen neuen Termin buchen.", f'<a class="btn" href="/termin.html">Neuen Termin buchen</a>'
    elif st in ("verfallen", "reserviert"):
        head, text, btns = "Reservierung abgelaufen", "Die Reservierung wurde nicht rechtzeitig bestätigt und ist wieder frei. Buchen Sie einfach einen neuen Termin.", f'<a class="btn" href="/termin.html">Neuen Termin buchen</a>'
    else:
        head, text, btns = "Ihr Termin", "Bei Fragen melden Sie sich gern telefonisch oder per WhatsApp.", ""
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer"><title>{E(head)} | {E(s.get('name', 'ElbDetail'))}</title>
<style>
@font-face{{font-family:Inter;font-weight:100 900;src:url(/fonts/inter-var.woff2) format("woff2")}}
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;padding:24px 16px;font:16px/1.55 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#f4f5f7;color:#161a21}}
.wrap{{max-width:640px;margin:0 auto;display:grid;gap:16px}}.top{{background:#1e2229;border-radius:18px;padding:18px 22px}}.top img{{height:40px;display:block}}
.card{{background:#fff;border:1px solid #dfe3e9;border-radius:18px;padding:26px 24px;display:grid;gap:14px}}h1{{margin:0;font-size:26px;letter-spacing:-.02em;line-height:1.2}}
.when{{font-size:20px;font-weight:650;color:#1c4f9c}}dl{{margin:0;display:grid;gap:6px}}dl div{{display:flex;gap:10px;flex-wrap:wrap}}dt{{color:#5b6472;min-width:110px}}dd{{margin:0;font-weight:600}}
.note{{background:#eef3fb;border-radius:12px;padding:12px 14px;font-size:15px}}.notice{{background:#e7f6ec;border:1px solid #b9e2c6;border-radius:12px;padding:12px 14px;font-weight:600}}
.btns{{display:flex;gap:10px;flex-wrap:wrap}}form{{margin:0}}.chk{{display:flex;gap:10px;align-items:flex-start;font-size:14px;margin:0 0 12px}}.chk input{{width:20px;height:20px;margin-top:2px;flex:none}}.btn{{display:inline-block;background:#1c4f9c;color:#fff;border:1px solid #1c4f9c;border-radius:999px;padding:12px 22px;font:inherit;font-weight:650;cursor:pointer;text-decoration:none;min-height:46px}}
.btn.ghost{{background:#fff;color:#1e2229;border-color:#c9cfd8}}.pick{{display:grid;gap:10px}}.pick label{{display:grid;gap:4px;font-weight:600}}.pick input{{font:inherit;padding:10px 12px;border:1px solid #c9cfd8;border-radius:12px;min-height:46px}}
.slots{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}}.slot{{display:flex;gap:6px;align-items:center;border:1px solid #c9cfd8;border-radius:12px;padding:10px 14px;font-weight:600;cursor:pointer}}.btn:focus-visible{{outline:3px solid #f2b705;outline-offset:2px}}.small{{font-size:14px;color:#5b6472}}a{{color:#1c4f9c}}
</style></head><body><div class="wrap">
<div class="top"><a href="/"><img src="/logo-head.svg" alt="{E(s.get('name', 'ElbDetail'))}"></a></div>
<main class="card">
{f'<p class="notice" role="status">{E(notice)}</p>' if notice else ''}
<h1>{E(head)}</h1><p class="when">{E(de_when(d))}</p><p>{E(text)}</p>
<dl><div><dt>Vorgang</dt><dd>{E(r['ref'])}</dd></div><div><dt>Name</dt><dd>{E(d.get('name', ''))}</dd></div>
<div><dt>Adresse</dt><dd>{E(s.get('address', {}).get('street', ''))}, {E(s.get('address', {}).get('zip', ''))} {E(s.get('address', {}).get('city', ''))}</dd></div></dl>
<p class="note">{E(stand_text(d))}</p>
{extra_html}
<div class="btns">{btns}</div>
{policy}
<p class="small">Fragen? Telefon oder WhatsApp: <a href="tel:{E(s.get('phone', ''))}">{E(s.get('phoneDisplay', ''))}</a></p>
</main></div></body></html>"""


# --------------------------------------------------------------------------- Kalender
def occupying(c, t0):
    """Termine, die Platz belegen: bestätigte Termine und noch gültige, unbestätigte Online-Reservierungen."""
    out, ts = [], now().isoformat()
    for r in c.execute("SELECT ref, status, datum, data FROM anfragen WHERE typ='termin' AND status IN ('termin_bestaetigt','reserviert') AND datum >= ?", (t0,)):
        try:
            d = json.loads(r["data"] or "{}")
        except ValueError:
            d = {}
        if r["status"] == "reserviert" and d.get("hold_until", "") < ts:
            continue
        out.append({"ref": r["ref"], "status": r["status"], "datum": r["datum"], "uhrzeit": d.get("uhrzeit", ""), "paket": d.get("paket", ""), "keramik": ker_booking(d)})
    return out


def blocked_days(keramik=False):
    """Gesperrte Tage plus ausgebuchte Tage (bestätigte Termine ≥ Tageskapazität).

    Keramikversiegelung belegt den Platz exklusiv, und zwar für die ganze Standzeit (Einstellung keramikDays,
    Standard 3 Tage): Diese Tage sind für alles andere ausgebucht, und eine Keramik kann nur beginnen, wenn in
    ihrer Standzeit kein anderer Termin bestätigt ist (Einstellung keramikExclusive).
    """
    cap = int(setting("dailyCapacity", 2) or 0)
    excl = bool(setting("keramikExclusive", True))
    span = max(1, int(setting("keramikDays", 3) or 1))
    t0 = today().isoformat()
    with db() as c:
        days = {r["day"] for r in c.execute("SELECT day FROM blocked WHERE day >= ?", (t0,))}
        count, ker = {}, set()
        for r in occupying(c, t0):
            count[r["datum"]] = count.get(r["datum"], 0) + 1
            if r["keramik"]:
                ker.add(r["datum"])
    if cap > 0:
        days |= {d for d, n in count.items() if n >= cap}
    if excl:
        shift = lambda d, k: (dt.date.fromisoformat(d) + dt.timedelta(days=k)).isoformat()
        days |= {shift(d, k) for d in ker for k in range(span)}
        if keramik:  # Start nur, wenn die ganze Standzeit frei ist
            days |= {shift(d, -k) for d in set(count) for k in range(span)}
            days |= {shift(d, -k) for d in ker for k in range(1, span)}
    return sorted(days)


def next_free_day(blocked=None, closed=None):
    """Nächster buchbarer Tag ab Vorlauf (Standard: morgen), ohne Ruhetage und gesperrte/ausgebuchte Tage."""
    blocked = set(blocked_days() if blocked is None else blocked)
    closed = setting("closedWeekdays", [0]) if closed is None else closed
    d = today() + dt.timedelta(days=max(0, int(setting("leadDays", 1) or 0)))
    for _ in range(120):
        if (d.weekday() + 1) % 7 not in closed and d.isoformat() not in blocked:
            return d.isoformat()
        d += dt.timedelta(days=1)
    return None


# --------------------------------------------------------------------------- Online-Buchung: Uhrzeiten, Reservierung, Bestätigung
def booking_cfg():
    b = site_info().get("booking") or {}
    times = [t for t in b.get("slotTimes", ["08:00", "10:00", "13:00", "15:00"]) if re.match(r"^([01]\d|2[0-3]):[0-5]\d$", str(t))]
    rem = [int(x) for x in b.get("reminderHours", [24, 6]) if str(x).isdigit() and 0 < int(x) <= 168]
    return {"selfBooking": bool(b.get("selfBooking", True)), "slotTimes": sorted(times) or ["08:00"],
            "slotMinutes": max(15, min(240, int(b.get("slotMinutes", 30) or 30))),
            "holdHours": max(1, min(168, int(b.get("holdHours", 24) or 24))), "reminderHours": sorted(rem, reverse=True)}


def self_booking():
    """Kunden buchen Uhrzeit selbst und bestätigen per E-Mail-Link. Ohne E-Mail-Versand: klassische Anfrage."""
    return booking_cfg()["selfBooking"] and mail_ready()


def termin_start(d):
    day = _date(d.get("datum", ""))
    if not day:
        return None
    hh, mm = (d.get("uhrzeit") or "08:00").split(":")
    return dt.datetime.combine(day, dt.time(int(hh), int(mm)))


def free_slots(day, paket="", exclude_ref="", keramik=None):
    """Freie Abgabezeiten an einem Tag: Ruhetage, Sperren, Auslastung, belegte Uhrzeiten und Google-Kalender."""
    cfg = booking_cfg()
    d = _date(day)
    if not d:
        return []
    lead = max(0, int(setting("leadDays", 1) or 0))
    closed = setting("closedWeekdays", [0])
    if d < today() + dt.timedelta(days=lead) or ((d.weekday() + 1) % 7) in closed or day in blocked_days(keramik=paket == "keramik" if keramik is None else keramik):
        return [{"zeit": t, "frei": False} for t in cfg["slotTimes"]]
    with db() as c:
        taken = {o["uhrzeit"] for o in occupying(c, day) if o["datum"] == day and o["ref"] != exclude_ref}
    busy = google_busy(d)
    out = []
    for t in cfg["slotTimes"]:
        start = dt.datetime.combine(d, dt.time(*map(int, t.split(":"))))
        end = start + dt.timedelta(minutes=cfg["slotMinutes"])
        clash = any(b0 < end and b1 > start for b0, b1 in busy)
        hrs = open_hours(d)
        inside = hrs is None or hrs[0] <= t < hrs[1]  # z. B. mittwochs erst ab 9 Uhr
        out.append({"zeit": t, "frei": t not in taken and not clash and start > now() and inside})
    return out


def open_hours(d):
    """Öffnungszeit am Wochentag laut Grunddaten (openingHours.schedule) als (öffnet, schließt) oder None."""
    name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][d.weekday()]
    for o in ((site_info().get("openingHours") or {}).get("schedule") or []):
        if name in (o.get("days") or []):
            return o.get("opens", "00:00"), o.get("closes", "23:59")
    return None


def slot_free(day, zeit, paket="", keramik=None):
    return any(x["zeit"] == zeit and x["frei"] for x in free_slots(day, paket, keramik=keramik))


def booking_link(ref, token, action=""):
    return f"{Cfg.public_url}/termin/{ref}{'/' + action if action else ''}?t={token}"


def de_when(d):
    st = termin_start(d)
    days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return f"{days[st.weekday()]}, {st.strftime('%d.%m.%Y')} um {st.strftime('%H:%M')} Uhr" if st else ""


def stand_text(d):
    if d.get("paket") == "scheiben":
        return "Die Scheibenkeramik dauert etwa 1 Stunde."
    return ("Bei Versiegelung und Keramik bleibt Ihr Auto 3 Tage bei uns, damit die Beschichtung in Ruhe aushärten kann."
            if ker_booking(d) else "Optimal ist es, wenn Ihr Auto einen Tag bei uns bleiben kann. Bei Versiegelung und Keramik sind es 3 Tage.")


def mail_footer():
    s = site_info()
    a = s.get("address", {})
    return (f"Viele Grüße\n{(s.get('about') or {}).get('name') or ''} · {s.get('name', 'ElbDetail')}\n"
            f"{a.get('street', '')}, {a.get('zip', '')} {a.get('city', '')}\nTelefon/WhatsApp: {s.get('phoneIntl', '')}\n{Cfg.public_url}\n")


def ics_event(ref, d, method="PUBLISH", cancel=False):
    s = site_info()
    st = termin_start(d)
    if not st:
        return b""
    end = st + dt.timedelta(minutes=booking_cfg()["slotMinutes"])
    a = s.get("address", {})
    f = lambda x: x.strftime("%Y%m%dT%H%M%S")
    esc = lambda x: str(x).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ElbDetail//Termine//DE", f"METHOD:{method}", "BEGIN:VEVENT",
             f"UID:{ref}@{Cfg.public_url.split('//')[-1]}", f"DTSTAMP:{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
             f"DTSTART;TZID=Europe/Berlin:{f(st)}", f"DTEND;TZID=Europe/Berlin:{f(end)}",
             f"SUMMARY:{esc('Fahrzeugabgabe bei ' + s.get('name', 'ElbDetail'))}",
             f"LOCATION:{esc(a.get('street', '') + ', ' + a.get('zip', '') + ' ' + a.get('city', '') + (' (' + a['hint'] + ')' if a.get('hint') else ''))}",
             f"DESCRIPTION:{esc('Vorgang ' + ref + '. ' + stand_text(d))}", f"STATUS:{'CANCELLED' if cancel else 'CONFIRMED'}",
             "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(lines) + "\r\n").encode()


def reservation_text(ref, d):
    s = site_info()
    cfg = booking_cfg()
    pct = d.get("depositPercent", 15)
    if deposit_me(d):
        ask = (f"Bitte bestätigen Sie den Termin und leisten Sie die Anzahlung von {eur(d['anzahlung'])} per PayPal:\n{booking_link(ref, d['token'])}\n\n"
               f"Sobald die Anzahlung bei uns eingegangen ist, erhalten Sie die Terminbestätigung. Die Anzahlung wird mit dem Endpreis verrechnet.\n\n")
    elif deposit_online(d):
        ask = (f"Bitte bestätigen Sie den Termin, indem Sie die Anzahlung von {eur(d['anzahlung'])} per PayPal leisten:\n{booking_link(ref, d['token'])}\n\n"
               f"Die Anzahlung wird mit dem Endpreis verrechnet.\n\n")
    else:
        ask = f"Bitte bestätigen Sie den Termin mit einem Klick auf diesen Link:\n{booking_link(ref, d['token'])}\n\n"
        if d.get("anzahlung"):
            ask += f"Die Anzahlung von {eur(d['anzahlung'])} besprechen wir mit Ihnen am Telefon.\n\n"
    text = (f"Guten Tag {d.get('name', '').strip()},\n\nvielen Dank für Ihre Buchung bei {s.get('name', 'ElbDetail')}.\n\n"
            f"Wir haben diesen Termin für Sie reserviert:\n{de_when(d)}\n\n{ask}"
            f"Die Reservierung gilt {cfg['holdHours']} Stunden. Ohne Bestätigung geben wir die Uhrzeit danach wieder frei.\n\n"
            + (f"Verschieben und Absagen: {booking_policy()}\n\n" if d.get("anzahlung") and booking_policy() else "") +
            f"Ihre Angaben ({ref}):\n{summary_text(public_data(d))}\n\n{mail_footer()}")
    return f"Bitte bestätigen: Ihr Termin am {termin_start(d).strftime('%d.%m.%Y')} ({ref})", text


def mail_reservation(ref, d):
    subj, text = reservation_text(ref, d)
    customer_mail("reservierung", ref, d["email"], subj, text)


def confirmed_text(ref, d):
    s = site_info()
    owner = (s.get("about") or {}).get("name") or "Wir"
    text = (f"Guten Tag {d.get('name', '').strip()},\n\nIhr Termin bei {s.get('name', 'ElbDetail')} ist bestätigt:\n{de_when(d)}\n\n"
            f"So geht es weiter: {owner} meldet sich vorab telefonisch bei Ihnen und sieht sich Ihr Fahrzeug vor der Aufbereitung genau an. "
            f"So erhalten Sie den verbindlichen Preis, bevor wir anfangen.\n\n{deposit_text(d)}{stand_text(d)}\n\n"
            f"Bitte räumen Sie Wertsachen und persönliche Gegenstände vorher aus dem Auto.\n\n"
            f"Vor dem Termin erinnern wir Sie noch einmal per E-Mail. Den Termin finden Sie auch im Anhang für Ihren Kalender.\n\n"
            f"Termin verschieben, absagen oder Vertrag widerrufen: {booking_link(ref, d['token'])}\n"
            + (f"{booking_policy()}\n" if d.get("anzahlung") and booking_policy() else "")
            + (f"\nWiderrufsrecht: Sie können diesen Vertrag bis zum {widerruf_bis(d).strftime('%d.%m.%Y')} ohne Angabe von Gründen widerrufen. "
               f"Ohne etwas auszufüllen geht das hier: {booking_link(ref, d['token'])}&aktion=widerrufen\n"
               "Die vollständige Widerrufsbelehrung steht am Ende dieser E-Mail.\n" if widerruf_bis(d) else "")
            + ("Sie haben ausdrücklich verlangt, dass wir vor Ablauf der Widerrufsfrist mit der Leistung beginnen. Ihnen ist bekannt, dass Sie bei einem Widerruf "
               "einen anteiligen Betrag für bereits erbrachte Leistungen zahlen und Ihr Widerrufsrecht erlischt, sobald wir die Leistung vollständig erbracht haben.\n"
               if d.get("vorzeitig_am") else "")
            + f"\nIhre Angaben ({ref}):\n{summary_text(public_data(d))}\n\n{mail_footer()}\n\n---\n{widerruf_text()}")
    return f"Termin bestätigt: {termin_start(d).strftime('%d.%m.%Y, %H:%M')} Uhr ({ref})", text


def mail_confirmed(ref, d):
    subj, text = confirmed_text(ref, d)
    discard_mails(ref, ["bestaetigung"], "ersetzt")
    customer_mail("bestaetigung", ref, d["email"], subj, text, attachments=[("termin.ics", "text/calendar", ics_event(ref, d))])


def deposit_text(d):
    z = d.get("zahlung") or {}
    if is_paid(d):
        return f"Ihre Anzahlung von {eur(z['value'])} per PayPal ist eingegangen und wird mit dem Endpreis verrechnet.\n\n"
    if d.get("anzahlung"):
        return f"Die Anzahlung von {eur(d['anzahlung'])} besprechen wir beim Telefonat.\n\n"
    return ""


def reminder_text(ref, d, at):
    """Erinnerungstext aus Sicht des Versandzeitpunkts (morgen / heute)."""
    s = site_info()
    st = termin_start(d)
    when = "morgen" if st.date() == at.date() + dt.timedelta(days=1) else ("heute" if st.date() == at.date() else st.strftime("am %d.%m.%Y"))
    a = s.get("address", {})
    text = (f"Guten Tag {d.get('name', '').strip()},\n\nwir freuen uns auf Sie: Ihr Termin bei {s.get('name', 'ElbDetail')} ist {when} um {st.strftime('%H:%M')} Uhr.\n\n"
            f"Adresse: {a.get('street', '')}, {a.get('zip', '')} {a.get('city', '')}" + (f" ({a['hint']})" if a.get("hint") else "") + "\n"
            f"Route: {'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(a.get('street', '') + ' ' + a.get('city', ''))}\n\n"
            f"{stand_text(d)} Bitte räumen Sie Wertsachen vorher aus dem Auto.\n\n"
            f"Etwas dazwischengekommen? Hier können Sie den Termin kostenlos verschieben: {booking_link(ref, d['token'])}\n\n{mail_footer()}")
    return f"Erinnerung: Ihr Termin {when} um {st.strftime('%H:%M')} Uhr ({ref})", text


WIDERRUF_TAGE = 14


def widerruf_bis(d):
    """Ende der Widerrufsfrist: 14 Tage ab Vertragsschluss (Bestätigung der Buchung durch den Kunden)."""
    try:
        return dt.datetime.fromisoformat(d["bestaetigt_am"]) + dt.timedelta(days=WIDERRUF_TAGE)
    except (KeyError, TypeError, ValueError):
        return None


def in_widerruf(d):
    b = widerruf_bis(d)
    return bool(b and now() < b)


def early_start(d):
    """Termin liegt innerhalb der Widerrufsfrist: Der Kunde muss den vorzeitigen Beginn ausdrücklich verlangen."""
    st = termin_start(d)
    return bool(st and st < now() + dt.timedelta(days=WIDERRUF_TAGE))


def widerruf_refund_line(d):
    z = d.get("zahlung") or {}
    if not is_paid(d):
        return ""
    if z.get("erstattet"):
        return f"Die Anzahlung von {eur(float(z['value']))} wurde über PayPal erstattet."
    return f"Die Anzahlung von {eur(float(z['value']))} erstatten wir unverzüglich, spätestens binnen 14 Tagen, über PayPal."


def widerruf_text():
    """Widerrufsbelehrung als Text für die Bestätigungs-E-Mail (dauerhafter Datenträger)."""
    s = site_info()
    a = s.get("address", {})
    L = s.get("legal", {})
    return (f"Widerrufsbelehrung\n\nWiderrufsrecht\nSie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen. "
            f"Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.\n"
            f"Um Ihr Widerrufsrecht auszuüben, müssen Sie uns ({s.get('name', 'ElbDetail')}, {L.get('owner', '')}, {a.get('street', '')}, {a.get('zip', '')} {a.get('city', '')}, "
            f"Telefon {s.get('phoneIntl', '')}, E-Mail {s.get('email', '')}) mittels einer eindeutigen Erklärung (z. B. ein mit der Post versandter Brief oder eine E-Mail) "
            f"über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür auch die Funktion „Vertrag widerrufen“ auf unserer Website "
            f"({Cfg.public_url}/widerruf.html) oder den Link in dieser E-Mail nutzen. Sie können das Muster-Widerrufsformular unter {Cfg.public_url}/agb.html#widerrufsformular "
            f"verwenden, das jedoch nicht vorgeschrieben ist.\n"
            f"Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.\n\n"
            f"Folgen des Widerrufs\nWenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, unverzüglich und spätestens "
            f"binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung "
            f"verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes "
            f"vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet.\n"
            f"Haben Sie verlangt, dass die Dienstleistungen während der Widerrufsfrist beginnen sollen, so haben Sie uns einen angemessenen Betrag zu zahlen, der dem Anteil "
            f"der bis zu dem Zeitpunkt, zu dem Sie uns von der Ausübung des Widerrufsrechts hinsichtlich dieses Vertrags unterrichten, bereits erbrachten Dienstleistungen "
            f"im Vergleich zum Gesamtumfang der im Vertrag vorgesehenen Dienstleistungen entspricht.\n\n"
            f"Unsere AGB: {Cfg.public_url}/agb.html")


def public_data(d):
    """Kundendaten ohne interne Felder (Token, Kalender-ID, Versandprotokoll)."""
    return {k: v for k, v in d.items() if k not in ("token", "hold_until", "gcal_id", "mails", "bestaetigt_am", "storniert_am", "paypal_order", "zahlung", "depositPercent", "verschoben",
                                             "agb_am", "vorzeitig_am", "widerruf_am")}


def load_termin(ref):
    with db() as c:
        r = c.execute("SELECT * FROM anfragen WHERE ref=? AND typ='termin'", (ref,)).fetchone()
    if not r:
        return None, None
    return dict(r), json.loads(r["data"] or "{}")


def save_termin(rid, d, status=None):
    with db() as c:
        if status:
            c.execute("UPDATE anfragen SET status=?, data=?, updated=? WHERE id=?", (status, json.dumps(d, ensure_ascii=False), now().isoformat(), rid))
        else:
            c.execute("UPDATE anfragen SET data=?, updated=? WHERE id=?", (json.dumps(d, ensure_ascii=False), now().isoformat(), rid))


def confirm_termin(r, d, by="kunde"):
    """Termin verbindlich machen: Status, Google-Kalender, Bestätigungs-E-Mail, Hinweis an den Betrieb (jeweils nur einmal)."""
    d.setdefault("token", secrets.token_urlsafe(24))
    first = not d.get("bestaetigt_am")
    d["bestaetigt_am"] = d.get("bestaetigt_am") or now().isoformat()
    save_termin(r["id"], d, "termin_bestaetigt")
    if not first:
        return
    audit("termin_bestaetigt", f"{r['ref']} durch {by}")
    threading.Thread(target=google_upsert, args=(r["ref"],), daemon=True).start()
    if d.get("email") and termin_start(d):
        mail_confirmed(r["ref"], d)
        schedule_reminders(r["ref"], d)
    discard_mails(r["ref"], ["reservierung"], "Termin bereits bestätigt")
    if by == "kunde":
        s = site_info()
        mail_async(Cfg.notify_to or s.get("email"), f"Termin vom Kunden bestätigt: {d.get('name')} · {de_when(d)} ({r['ref']})",
                   f"Der Kunde hat den Termin online bestätigt. Bitte vorab anrufen und das Fahrzeug ansehen.\n\n{de_when(d)}\n"
                   + (f"Anzahlung per PayPal erhalten: {eur(d['zahlung']['value'])} (Transaktion {d['zahlung']['capture_id']})\n" if (d.get("zahlung") or {}).get("capture_id") else "") +
                   f"Telefon: {d.get('telefon', '')}\n\n{summary_text(public_data(d))}\n\nIm Verwaltungsportal: {Cfg.public_url}/admin/#/anfragen/{r['ref']}\n")


def cancel_termin(r, d, by="kunde", confirm=True):
    """Termin absagen. Durch den Kunden innerhalb der Widerrufsfrist gilt die Absage als Widerruf: Anzahlung wird erstattet.
    Danach wird die Anzahlung als Ausfallpauschale einbehalten. by="widerruf": ausdrücklicher Widerruf (Button oder Formular)."""
    if r["status"] in ("storniert", "verfallen", "abgelehnt"):
        return
    at = now()
    d["storniert_am"] = at.isoformat()
    customer = by in ("kunde", "widerruf")
    paid = is_paid(d)
    widerruf = customer and r["status"] == "termin_bestaetigt" and (by == "widerruf" or in_widerruf(d))
    if widerruf:
        d.setdefault("widerruf_am", at.isoformat())
    elif by == "kunde" and paid and r["status"] == "termin_bestaetigt":
        d["zahlung"]["einbehalten"] = at.isoformat()  # Ausfallpauschale: Termin war für den Kunden geblockt
    save_termin(r["id"], d, "storniert" if customer else r["status"])
    audit("termin_widerrufen" if widerruf else "termin_storniert", f"{r['ref']} durch {by}")
    discard_mails(r["ref"], ["reservierung", "bestaetigung", "erinnerung"], "Termin abgesagt")
    threading.Thread(target=google_delete, args=(r["ref"],), daemon=True).start()
    if widerruf and paid:
        refund_deposit(r["ref"], mail=False)
        r, d = load_termin(r["ref"])
    if customer:
        s = site_info()
        refund = widerruf_refund_line(d) if widerruf else ""
        failed = widerruf and paid and not (d.get("zahlung") or {}).get("erstattet")
        manual = failed and (d.get("zahlung") or {}).get("manuell")
        mail_async(Cfg.notify_to or s.get("email"), f"Termin {'widerrufen' if widerruf else 'abgesagt'}: {d.get('name')} · {de_when(d)} ({r['ref']})",
                   (f"Der Kunde hat den Vertrag innerhalb der Widerrufsfrist widerrufen bzw. abgesagt.\n{refund}\n"
                    + (f"BITTE ERSTATTEN: Die Anzahlung kam über PayPal.me. Bitte {eur(float(d['zahlung']['value']))} über PayPal an den Kunden zurücksenden, "
                       "spätestens binnen 14 Tagen, und danach im Verwaltungsportal auf „Anzahlung erstattet“ klicken.\n" if manual else
                       "ACHTUNG: Die automatische PayPal-Erstattung hat nicht geklappt. Bitte im Verwaltungsportal erstatten, spätestens binnen 14 Tagen.\n" if failed else "")
                    if widerruf else "Der Kunde hat den Termin online abgesagt.\n"
                    + (f"Die Anzahlung von {eur(d['zahlung']['value'])} wird als Ausfallpauschale einbehalten. Eine Erstattung aus Kulanz ist im Verwaltungsportal möglich.\n" if paid else ""))
                   + f"\n{summary_text(public_data(d))}\n")
        if d.get("email") and widerruf and confirm:
            customer_mail("widerruf", r["ref"], d["email"], f"Eingangsbestätigung Ihres Widerrufs ({r['ref']})",
                          f"Guten Tag {d.get('name', '').strip()},\n\nhiermit bestätigen wir den Eingang Ihres Widerrufs am {at.strftime('%d.%m.%Y um %H:%M')} Uhr. "
                          f"Ihr Vertrag über den Termin am {de_when(d)} ({r['ref']}) ist widerrufen, der Termin ist abgesagt. {refund}\n\n"
                          f"Einen neuen Termin buchen Sie jederzeit unter {Cfg.public_url}/termin.html\n\n{mail_footer()}",
                          attachments=[("absage.ics", "text/calendar", ics_event(r["ref"], d, "CANCEL", cancel=True))])
        elif d.get("email") and not widerruf:
            customer_mail("absage", r["ref"], d["email"], f"Ihr Termin wurde abgesagt ({r['ref']})",
                          f"Guten Tag {d.get('name', '').strip()},\n\nIhr Termin am {de_when(d)} ist abgesagt. "
                          + (f"Ihre Anzahlung von {eur(d['zahlung']['value'])} behalten wir als Ausfallpauschale ein, weil wir den Termin für Sie freigehalten haben. "
                             "Ist uns kein oder ein geringerer Schaden entstanden, können Sie uns das gern nachweisen. " if paid and r["status"] == "termin_bestaetigt" else "")
                          + f"Einen neuen Termin buchen Sie jederzeit unter {Cfg.public_url}/termin.html\n\n{mail_footer()}",
                          attachments=[("absage.ics", "text/calendar", ics_event(r["ref"], d, "CANCEL", cancel=True))])


def reschedule_termin(r, d, datum, uhrzeit, by="kunde"):
    """Bestätigten Termin auf einen freien Tag/Uhrzeit legen; Anzahlung, Kalender und Erinnerungen ziehen mit. Gibt eine Fehlermeldung zurück."""
    if not _date(datum) or not uhrzeit:
        return "Bitte Tag und Uhrzeit wählen."
    with LOCK:
        if not any(x["zeit"] == uhrzeit and x["frei"] for x in free_slots(datum, exclude_ref=r["ref"], keramik=ker_booking(d))):
            return "Diese Uhrzeit ist leider nicht mehr frei. Bitte eine andere wählen."
        old = de_when(d)
        d.update(datum=datum, uhrzeit=uhrzeit)
        d.setdefault("verschoben", []).append({"von": old, "am": now().isoformat(), "durch": by})
        with db() as c:
            c.execute("UPDATE anfragen SET datum=?, data=?, updated=? WHERE id=?", (datum, json.dumps(d, ensure_ascii=False), now().isoformat(), r["id"]))
    audit("termin_verschoben", f"{r['ref']} von {old} auf {de_when(d)} durch {by}")
    threading.Thread(target=google_upsert, args=(r["ref"],), daemon=True).start()
    if d.get("email") and d.get("token"):
        mail_confirmed(r["ref"], d)
        schedule_reminders(r["ref"], d)
    if by == "kunde":
        s = site_info()
        mail_async(Cfg.notify_to or s.get("email"), f"Termin verschoben: {d.get('name')} · {de_when(d)} ({r['ref']})",
                   f"Der Kunde hat seinen Termin online verschoben.\nAlt: {old}\nNeu: {de_when(d)}\n"
                   + (f"Die Anzahlung von {eur(d['zahlung']['value'])} bleibt bestehen.\n" if is_paid(d) else "")
                   + f"\n{summary_text(public_data(d))}\n")
    return ""


def booking_watcher():
    """Alle 5 Minuten: abgelaufene Reservierungen freigeben, Erinnerungen 24 h und 6 h vorher verschicken."""
    while True:
        try:
            booking_tick()
        except Exception as e:
            log("Terminprüfung fehlgeschlagen:", e)
        time.sleep(300)


def booking_tick():
    """Ein Durchlauf: Reservierungen ohne Bestätigung verfallen lassen, freigegebene und fällige E-Mails (z. B. Erinnerungen) senden."""
    ts = now()
    with db() as c:
        rows = [dict(r) for r in c.execute("SELECT id, ref, status, data FROM anfragen WHERE typ='termin' AND status='reserviert' AND datum >= ?",
                                           ((today() - dt.timedelta(days=1)).isoformat(),))]
    for r in rows:
        d = json.loads(r["data"] or "{}")
        if d.get("hold_until") and d["hold_until"] < ts.isoformat():
            save_termin(r["id"], d, "verfallen")
            discard_mails(r["ref"], ["reservierung"], "Reservierung verfallen")
            audit("termin_verfallen", r["ref"])
    outbox_tick()


# --------------------------------------------------------------------------- Postausgang: E-Mails an Kunden erst nach Freigabe durch den Betrieb
MAIL_KINDS = {"reservierung": "Buchung: Link zur Anzahlung bzw. Bestätigung", "bestaetigung": "Terminbestätigung", "erinnerung": "Erinnerung vor dem Termin",
              "absage": "Absage", "erstattung": "Erstattung der Anzahlung", "eingang": "Eingangsbestätigung (Kontakt, Gutschein, Firmen)"}


def approval_needed(kind):
    if kind == "widerruf":
        return False  # Eingang eines Widerrufs muss unverzüglich bestätigt werden
    return bool((setting("mailApproval", {}) or {}).get(kind, True))


def customer_mail(kind, ref, to, subject, body, attachments=None, send_after=None):
    """Kunden-E-Mail in den Postausgang legen. Mit Freigabepflicht als Entwurf, sonst sofort bzw. zum geplanten Zeitpunkt senden."""
    if not to:
        return None
    status = "entwurf" if approval_needed(kind) else "freigegeben"
    att = json.dumps([[n, m, base64.b64encode(b).decode()] for n, m, b in (attachments or [])])
    with db() as c:
        oid = c.execute("INSERT INTO outbox(ref, kind, to_addr, subject, body, attach, status, created, send_after) VALUES (?,?,?,?,?,?,?,?,?)",
                        (ref, kind, to, subject, body, att, status, now().isoformat(), send_after or "")).lastrowid
    if status == "freigegeben" and (not send_after or send_after <= now().isoformat()):
        threading.Thread(target=deliver, args=(oid,), daemon=True).start()
    return oid


def deliver(oid):
    with db() as c:
        m = c.execute("SELECT * FROM outbox WHERE id=?", (oid,)).fetchone()
        if not m or m["status"] != "freigegeben":
            return False
        c.execute("UPDATE outbox SET status='wird_gesendet' WHERE id=?", (oid,))
    s = site_info()
    att = [(n, mt, base64.b64decode(b)) for n, mt, b in json.loads(m["attach"] or "[]")]
    ok = send_mail(m["to_addr"], m["subject"], m["body"], reply_to=s.get("email") or None, attachments=att)
    with db() as c:
        c.execute("UPDATE outbox SET status=?, sent_at=? WHERE id=?", ("gesendet" if ok else "fehler", now().isoformat(), oid))
    if ok and m["kind"] == "reservierung" and m["ref"]:  # Reservierungsfrist läuft ab Versand des Links
        r, d = load_termin(m["ref"])
        if r and r["status"] == "reserviert":
            d["hold_until"] = (now() + dt.timedelta(hours=booking_cfg()["holdHours"])).isoformat()
            save_termin(r["id"], d)
    return ok


def discard_mails(ref, kinds, reason="verworfen"):
    with db() as c:
        c.execute(f"UPDATE outbox SET status=?, note=? WHERE ref=? AND kind IN ({','.join('?' * len(kinds))}) AND status IN ('entwurf','freigegeben')",
                  ["verworfen", reason, ref] + list(kinds))


def outbox_tick():
    """Freigegebene, fällige E-Mails senden; nicht rechtzeitig freigegebene Erinnerungen verwerfen."""
    ts = now().isoformat()
    with db() as c:
        due = [r["id"] for r in c.execute("SELECT id FROM outbox WHERE status='freigegeben' AND (send_after='' OR send_after<=?)", (ts,))]
        late = c.execute("SELECT o.id, o.ref FROM outbox o JOIN anfragen a ON a.ref=o.ref WHERE o.kind='erinnerung' AND o.status='entwurf' AND o.send_after<=?", (ts,)).fetchall()
        for r in late:
            r2 = c.execute("SELECT datum, data FROM anfragen WHERE ref=?", (r["ref"],)).fetchone()
            st = termin_start(json.loads(r2["data"] or "{}")) if r2 else None
            if not st or st.isoformat() <= ts:
                c.execute("UPDATE outbox SET status='verworfen', note='nicht rechtzeitig freigegeben' WHERE id=?", (r["id"],))
    for oid in due:
        deliver(oid)


def schedule_reminders(ref, d):
    """Erinnerungen 24 h und 6 h vorher als (freizugebende) geplante E-Mails anlegen."""
    discard_mails(ref, ["erinnerung"], "neu geplant")
    st = termin_start(d)
    if not st or not d.get("email") or not d.get("token"):
        return
    for hrs in booking_cfg()["reminderHours"]:
        at = st - dt.timedelta(hours=hrs)
        if at <= now():
            continue
        subj, text = reminder_text(ref, d, at)
        customer_mail("erinnerung", ref, d["email"], subj, text, send_after=at.isoformat())


def outbox_open():
    with db() as c:
        return c.execute("SELECT COUNT(*) n FROM outbox WHERE status='entwurf'").fetchone()["n"]


# --------------------------------------------------------------------------- Anzahlung per PayPal (Orders API v2, Weiterleitung ohne Fremdskripte)
_PTOKEN = {"token": "", "exp": 0}


def paypal_configured():
    return bool(env("PAYPAL_CLIENT_ID") and env("PAYPAL_SECRET"))


def paypal_base():
    return "https://api-m.sandbox.paypal.com" if env("PAYPAL_MODE", "live") == "sandbox" else "https://api-m.paypal.com"


def paypal_token():
    if _PTOKEN["token"] and _PTOKEN["exp"] > time.time() + 60:
        return _PTOKEN["token"]
    auth = base64.b64encode(f"{env('PAYPAL_CLIENT_ID')}:{env('PAYPAL_SECRET')}".encode()).decode()
    req = urllib.request.Request(paypal_base() + "/v1/oauth2/token", data=b"grant_type=client_credentials", method="POST",
                                 headers={"Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.loads(r.read())
    _PTOKEN.update(token=j["access_token"], exp=time.time() + int(j.get("expires_in", 3000)))
    return _PTOKEN["token"]


def paypal_api(method, path, body=None, idem=""):
    h = {"Authorization": "Bearer " + paypal_token(), "Content-Type": "application/json"}
    if idem:
        h["PayPal-Request-Id"] = idem  # verhindert doppelte Aufträge/Erstattungen bei Wiederholung
    req = urllib.request.Request(paypal_base() + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
        log("PayPal-Fehler:", e.code, raw[:300])
        if e.code != 422:
            raise
    return json.loads(raw) if raw else {}


def deposit_amount(d):
    """Anzahlung in Euro (zwei Nachkommastellen) aus dem Richtpreis; None, wenn es keinen festen Preis gibt (Anfrage, Care, Beratung)."""
    pct = float((site_info().get("booking") or {}).get("depositPercent", 15) or 0)
    if pct <= 0:
        return None
    base = richtpreis(d)
    if base is None and d.get("paket") == "winter" and d.get("klasse") == "sport" and not ker_booking(d):
        base = (winter_offer() or {}).get("sportFrom")  # Sportwagen: Vorschlag vom Ab-Preis, René prüft im Postausgang
    if base is None and d.get("paket") == "keramik":
        try:
            base = min(c["price"] for c in pricing()["ceramic"]["car"] if c.get("price") is not None)
        except (KeyError, ValueError):
            base = None
    if not base:
        return None
    return round(base * pct / 100 + 1e-9, 2)


def eur(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").replace(",00", "") + " €"


def refund_deposit(ref, mail=True, auto=True):
    """PayPal-Anzahlung erstatten. Gibt (HTTP-Code, Meldung) zurück.
    PayPal.me-Zahlungen lassen sich nicht automatisch erstatten: René sendet das Geld selbst zurück und hält es im Portal fest (auto=False)."""
    r, d = load_termin(ref)
    z = (d or {}).get("zahlung") or {}
    if not r or not is_paid(d):
        return 404, "Keine Anzahlung zu diesem Termin."
    if z.get("erstattet"):
        return 200, "Bereits erstattet."
    if z.get("manuell"):
        if auto:
            return 409, "PayPal.me-Zahlung: bitte selbst über PayPal zurücksenden und im Portal als erstattet markieren."
        st = "COMPLETED"
    else:
        st = None
    try:
        if st is None:
            st = paypal_refund(z["capture_id"], float(z["value"]), ref)
    except Exception as e:
        log("PayPal-Erstattung fehlgeschlagen:", ref, e)
        return 502, f"PayPal-Erstattung fehlgeschlagen: {e}"
    if st not in ("COMPLETED", "PENDING"):
        return 502, f"PayPal meldet: {st or 'unbekannt'}"
    z["erstattet"] = now().isoformat()
    d["zahlung"] = z
    save_termin(r["id"], d)
    audit("anzahlung_erstattet", f"{ref}: {z['value']} €")
    if mail and d.get("email"):
        customer_mail("erstattung", ref, d["email"], f"Ihre Anzahlung wurde erstattet ({ref})",
                      f"Guten Tag {d.get('name', '').strip()},\n\nwir haben Ihre Anzahlung von {eur(float(z['value']))} über PayPal erstattet. "
                      f"Je nach Bank dauert die Gutschrift wenige Tage.\n\n{mail_footer()}")
    return 200, "Anzahlung erstattet."


def deposit_online(d):
    return bool(d.get("anzahlung")) and paypal_configured()


def paypal_me_name():
    """PayPal.me-Name aus den Grunddaten (booking.paypalMe), z. B. „elbdetail“ für paypal.me/elbdetail."""
    v = str((site_info().get("booking") or {}).get("paypalMe") or "").strip()
    v = re.sub(r"^(https?://)?(www\.)?paypal\.me/", "", v, flags=re.I).strip("/")
    return v if re.match(r"^[A-Za-z0-9]{1,40}$", v) else ""


def deposit_me(d):
    """Anzahlung über den PayPal.me-Link (René prüft den Eingang und bestätigt im Portal), nur ohne PayPal-Schnittstelle."""
    return bool(d.get("anzahlung")) and not paypal_configured() and bool(paypal_me_name())


def paypal_me_link(d):
    return f"https://paypal.me/{paypal_me_name()}/{float(d['anzahlung']):.2f}EUR"


def is_paid(d):
    z = d.get("zahlung") or {}
    return bool(z.get("capture_id") or z.get("manuell"))


def paypal_create(ref, d):
    s = site_info()
    j = paypal_api("POST", "/v2/checkout/orders", {
        "intent": "CAPTURE",
        "purchase_units": [{"reference_id": ref, "custom_id": ref, "invoice_id": ref + "-A",
                            "description": f"Anzahlung {d.get('depositPercent', 15)} % Termin {ref}"[:127],
                            "amount": {"currency_code": "EUR", "value": f"{d['anzahlung']:.2f}"}}],
        "payment_source": {"paypal": {"experience_context": {
            "brand_name": s.get("name", "ElbDetail")[:127], "locale": "de-DE", "shipping_preference": "NO_SHIPPING", "user_action": "PAY_NOW",
            "return_url": booking_link(ref, d["token"], "bezahlt"), "cancel_url": booking_link(ref, d["token"]) + "&abbruch=1"}}}}, idem="order-" + ref + "-" + d["token"][:8])
    link = next((x["href"] for x in j.get("links", []) if x.get("rel") in ("payer-action", "approve")), "")
    return j.get("id", ""), link


def paypal_capture(order_id):
    j = paypal_api("POST", f"/v2/checkout/orders/{urllib.parse.quote(order_id)}/capture", {}, idem="cap-" + order_id)
    if j.get("status") != "COMPLETED":  # schon erfasst? Dann den aktuellen Stand holen
        j = paypal_api("GET", f"/v2/checkout/orders/{urllib.parse.quote(order_id)}")
    cap = {}
    for pu in j.get("purchase_units", []):
        for c in (pu.get("payments") or {}).get("captures", []):
            cap = c
    return {"status": j.get("status", ""), "capture_id": cap.get("id", ""), "value": float((cap.get("amount") or {}).get("value", 0) or 0),
            "currency": (cap.get("amount") or {}).get("currency_code", ""), "capture_status": cap.get("status", ""),
            "ref": next((pu.get("reference_id") for pu in j.get("purchase_units", [])), "")}


def paypal_refund(capture_id, value, ref):
    j = paypal_api("POST", f"/v2/payments/captures/{urllib.parse.quote(capture_id)}/refund",
                   {"amount": {"currency_code": "EUR", "value": f"{value:.2f}"}, "note_to_payer": f"Erstattung Anzahlung {ref}"[:255]}, idem="ref-" + capture_id)
    return j.get("status", "")


# --------------------------------------------------------------------------- Google Kalender (OAuth, ohne Fremdbibliotheken)
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.freebusy"
_GTOKEN = {"token": "", "exp": 0}
_GBUSY = {}


def google_configured():
    return bool(env("GOOGLE_CLIENT_ID") and env("GOOGLE_CLIENT_SECRET"))


def google_redirect():
    return f"{Cfg.public_url}/admin/api/google/callback"


def google_connected():
    return google_configured() and bool(setting("googleRefreshToken", ""))


def _gpost(url, fields):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def google_token():
    if _GTOKEN["token"] and _GTOKEN["exp"] > time.time() + 60:
        return _GTOKEN["token"]
    j = _gpost("https://oauth2.googleapis.com/token", {"client_id": env("GOOGLE_CLIENT_ID"), "client_secret": env("GOOGLE_CLIENT_SECRET"),
                                                        "refresh_token": setting("googleRefreshToken", ""), "grant_type": "refresh_token"})
    _GTOKEN.update(token=j["access_token"], exp=time.time() + int(j.get("expires_in", 3600)))
    return _GTOKEN["token"]


def google_api(method, path, body=None):
    url = "https://www.googleapis.com/calendar/v3" + path
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Authorization": "Bearer " + google_token(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def google_cal():
    return urllib.parse.quote(setting("googleCalendarId", "primary") or "primary", safe="")


def google_busy(day):
    """Belegte Zeiten aus Renés Google Kalender an einem Tag (2 Minuten zwischengespeichert, Fehler = keine Einschränkung)."""
    if not google_connected():
        return []
    key = day.isoformat()
    hit = _GBUSY.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    busy = []
    try:
        off = (dt.datetime.now(TZ).strftime("%z") if TZ else "+0100")
        off = off[:3] + ":" + off[3:]
        j = google_api("POST", "/freeBusy", {"timeMin": f"{key}T00:00:00{off}", "timeMax": f"{key}T23:59:59{off}", "timeZone": "Europe/Berlin",
                                              "items": [{"id": setting("googleCalendarId", "primary") or "primary"}]})
        for cal in (j.get("calendars") or {}).values():
            for b in cal.get("busy", []):
                b0 = dt.datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
                b1 = dt.datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
                if TZ:
                    b0, b1 = b0.astimezone(TZ), b1.astimezone(TZ)
                busy.append((b0.replace(tzinfo=None), b1.replace(tzinfo=None)))
    except Exception as e:
        log("Google freeBusy fehlgeschlagen:", e)
    _GBUSY[key] = (time.time() + 120, busy)
    return busy


def google_event_body(ref, d):
    s = site_info()
    pr = pricing()
    st = termin_start(d)
    end = st + dt.timedelta(minutes=booking_cfg()["slotMinutes"])
    names = {p["key"]: p["name"] for p in pr.get("packages", [])}
    names.update({"beratung": "Beratung", "keramik": "Keramikversiegelung", "care": "ElbDetail Care", "scheiben": "Scheibenkeramik (C² Glass Ceramic)",
                  "winter": (pr.get("winter") or {}).get("name", "Winterangebot")})
    a = s.get("address", {})
    return {"summary": f"Abgabe: {d.get('name', '')} · {names.get(d.get('paket'), d.get('paket', ''))}",
            "location": f"{a.get('street', '')}, {a.get('zip', '')} {a.get('city', '')}",
            "description": f"Vorgang {ref}\nTelefon: {d.get('telefon', '')}\n\n{summary_text(public_data(d))}\n\n{stand_text(d)}\n\n{Cfg.public_url}/admin/#/anfragen/{ref}",
            "start": {"dateTime": st.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Berlin"},
            "end": {"dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Berlin"},
            "reminders": {"useDefault": True}}


def google_upsert(ref):
    if not google_connected():
        return
    r, d = load_termin(ref)
    if not r or not termin_start(d):
        return
    try:
        if d.get("gcal_id"):
            google_api("PATCH", f"/calendars/{google_cal()}/events/{urllib.parse.quote(d['gcal_id'])}", google_event_body(ref, d))
        else:
            ev = google_api("POST", f"/calendars/{google_cal()}/events", google_event_body(ref, d))
            r, d = load_termin(ref)
            d["gcal_id"] = ev.get("id", "")
            save_termin(r["id"], d)
        _GBUSY.clear()
    except Exception as e:
        log("Google-Termin fehlgeschlagen:", e)
        audit("google_fehler", f"{ref}: {e}")


def google_delete(ref):
    if not google_connected():
        return
    r, d = load_termin(ref)
    if not r or not d.get("gcal_id"):
        return
    try:
        google_api("DELETE", f"/calendars/{google_cal()}/events/{urllib.parse.quote(d['gcal_id'])}")
    except Exception as e:
        log("Google-Termin löschen fehlgeschlagen:", e)
    d.pop("gcal_id", None)
    save_termin(r["id"], d)
    _GBUSY.clear()


def ics_key():
    k = setting("icsKey", "")
    if not k:
        k = secrets.token_urlsafe(24)
        set_setting("icsKey", k)
    return k


def ics_feed():
    """Abo-Kalender (iCal) aller bestätigten Termine, falls Google nicht per Konto verbunden wird."""
    s = site_info()
    with db() as c:
        rows = [dict(r) for r in c.execute("SELECT ref, data FROM anfragen WHERE typ='termin' AND status='termin_bestaetigt' AND datum >= ?",
                                           ((today() - dt.timedelta(days=30)).isoformat(),))]
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ElbDetail//Termine//DE", f"X-WR-CALNAME:{s.get('name', 'ElbDetail')} Termine", "X-WR-TIMEZONE:Europe/Berlin"]
    for r in rows:
        d = json.loads(r["data"] or "{}")
        ev = ics_event(r["ref"], d).decode().split("\r\n")
        body = ev[ev.index("BEGIN:VEVENT"):ev.index("END:VEVENT") + 1]
        body = [("SUMMARY:" + google_event_body(r["ref"], d)["summary"].replace(",", "\\,")) if x.startswith("SUMMARY:") else x for x in body]
        out += body
    out.append("END:VCALENDAR")
    return ("\r\n".join(out) + "\r\n").encode()


# --------------------------------------------------------------------------- Statistik
BOT_RE = re.compile(r"bot|crawl|spider|slurp|headless|lighthouse|pingdom|monitor|curl|wget|python|httpx|preview|facebookexternalhit", re.I)


def daily_salt(c, day):
    r = c.execute("SELECT salt FROM salts WHERE day=?", (day,)).fetchone()
    if r:
        return r["salt"]
    s = secrets.token_hex(16)
    c.execute("INSERT OR IGNORE INTO salts(day, salt) VALUES (?,?)", (day, s))
    c.execute("DELETE FROM salts WHERE day < ?", (day,))
    return c.execute("SELECT salt FROM salts WHERE day=?", (day,)).fetchone()["salt"]


def clean_path(p):
    p = str(p or "/")[:200]
    p = p.split("?")[0].split("#")[0]
    return p if p.startswith("/") else "/"


def record_event(payload, ip, ua):
    if BOT_RE.search(ua or "") or not ua:
        return
    t = payload.get("t")
    if t not in ("pv", "ev"):
        return
    day = today().isoformat()
    w = payload.get("w")
    try:
        w = int(w)
        device = "Mobil" if w < 640 else ("Tablet" if w < 1024 else "Desktop")
    except (TypeError, ValueError):
        device = ""
    utm = payload.get("utm") or {}
    ref = re.sub(r"[^a-z0-9.\-]", "", str(payload.get("r") or "").lower())[:100]
    props = payload.get("p") or {}
    props = json.dumps({str(k)[:30]: str(v)[:80] for k, v in list(props.items())[:6]}, ensure_ascii=False) if isinstance(props, dict) else "{}"
    with db() as c:
        salt = daily_salt(c, day)
        visitor = hashlib.sha256(f"{salt}|{ip}|{ua}".encode()).hexdigest()[:16]
        c.execute("INSERT INTO events(ts, day, type, name, path, ref, utm_s, utm_m, utm_c, device, visitor, props) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (now().isoformat(), day, t, str(payload.get("n") or "")[:60], clean_path(payload.get("u")), ref,
                   str(utm.get("s") or "")[:60], str(utm.get("m") or "")[:60], str(utm.get("c") or "")[:60], device, visitor, props))


def stats(days):
    days = max(1, min(int(days), 400))
    end = today()
    start = end - dt.timedelta(days=days - 1)
    pstart = start - dt.timedelta(days=days)
    s0, e0, p0 = start.isoformat(), end.isoformat(), pstart.isoformat()
    out = {"from": s0, "to": e0, "days": days}
    with db() as c:
        q = lambda sql, *a: [dict(r) for r in c.execute(sql, a)]
        series = {r["day"]: r for r in q("SELECT day, COUNT(DISTINCT visitor) v, COUNT(*) pv FROM events WHERE type='pv' AND day BETWEEN ? AND ? GROUP BY day", s0, e0)}
        leads = {r["day"]: r["n"] for r in q("SELECT substr(created,1,10) day, COUNT(*) n FROM anfragen WHERE substr(created,1,10) BETWEEN ? AND ? GROUP BY day", s0, e0)}
        out["series"] = []
        for i in range(days):
            d = (start + dt.timedelta(days=i)).isoformat()
            out["series"].append({"day": d, "visitors": series.get(d, {}).get("v", 0), "pageviews": series.get(d, {}).get("pv", 0), "leads": leads.get(d, 0)})

        def totals(a, b):
            v = c.execute("SELECT COUNT(DISTINCT day || visitor) v, COUNT(*) pv FROM events WHERE type='pv' AND day BETWEEN ? AND ?", (a, b)).fetchone()
            l = c.execute("SELECT COUNT(*) n FROM anfragen WHERE substr(created,1,10) BETWEEN ? AND ?", (a, b)).fetchone()["n"]
            wa = c.execute("SELECT COUNT(*) n FROM events WHERE type='ev' AND name='WhatsApp-Klick' AND day BETWEEN ? AND ?", (a, b)).fetchone()["n"]
            tel = c.execute("SELECT COUNT(*) n FROM events WHERE type='ev' AND name='Anruf-Klick' AND day BETWEEN ? AND ?", (a, b)).fetchone()["n"]
            return {"visitors": v["v"], "pageviews": v["pv"], "leads": l, "whatsapp": wa, "calls": tel,
                    "conversion": round(100 * (l + wa + tel) / v["v"], 1) if v["v"] else 0}
        out["totals"] = totals(s0, e0)
        out["previous"] = totals(p0, (start - dt.timedelta(days=1)).isoformat())
        out["pages"] = q("SELECT path, COUNT(*) pv, COUNT(DISTINCT day || visitor) v FROM events WHERE type='pv' AND day BETWEEN ? AND ? GROUP BY path ORDER BY pv DESC LIMIT 12", s0, e0)
        out["sources"] = q("""SELECT CASE WHEN utm_s != '' THEN utm_s WHEN ref != '' THEN ref ELSE 'Direkt / unbekannt' END src, COUNT(DISTINCT day || visitor) v
                              FROM events WHERE type='pv' AND day BETWEEN ? AND ? GROUP BY src ORDER BY v DESC LIMIT 10""", s0, e0)
        out["campaigns"] = q("SELECT utm_c c, utm_s s, COUNT(DISTINCT day || visitor) v FROM events WHERE type='pv' AND utm_c != '' AND day BETWEEN ? AND ? GROUP BY utm_c, utm_s ORDER BY v DESC LIMIT 10", s0, e0)
        out["events"] = q("SELECT name, COUNT(*) n FROM events WHERE type='ev' AND name != 'Buchung Schritt' AND day BETWEEN ? AND ? GROUP BY name ORDER BY n DESC LIMIT 15", s0, e0)
        out["devices"] = q("SELECT device, COUNT(DISTINCT day || visitor) v FROM events WHERE type='pv' AND day BETWEEN ? AND ? AND device != '' GROUP BY device ORDER BY v DESC", s0, e0)
        out["leadTypes"] = q("SELECT typ, COUNT(*) n FROM anfragen WHERE substr(created,1,10) BETWEEN ? AND ? GROUP BY typ ORDER BY n DESC", s0, e0)
        funnel = []
        for i in range(1, 6):
            n = c.execute("SELECT COUNT(DISTINCT day || visitor) n FROM events WHERE type='ev' AND name='Buchung Schritt' AND props LIKE ? AND day BETWEEN ? AND ?",
                          (f'%"schritt": "{i}"%', s0, e0)).fetchone()["n"]
            funnel.append({"step": i, "n": n})
        sent = c.execute("SELECT COUNT(*) n FROM anfragen WHERE typ='termin' AND substr(created,1,10) BETWEEN ? AND ?", (s0, e0)).fetchone()["n"]
        funnel.append({"step": "gesendet", "n": sent})
        out["funnel"] = funnel
        out["open"] = c.execute("SELECT COUNT(*) n FROM anfragen WHERE status='neu'").fetchone()["n"]
        out["upcoming"] = q("SELECT ref, name, datum, data FROM anfragen WHERE typ='termin' AND datum >= ? AND status NOT IN ('abgelehnt','storniert','verfallen') ORDER BY datum LIMIT 8", e0)
        for u in out["upcoming"]:
            d = json.loads(u.pop("data") or "{}")
            u["paket"] = d.get("paket")
            u["status"] = c.execute("SELECT status FROM anfragen WHERE ref=?", (u["ref"],)).fetchone()["status"]
    return out


# --------------------------------------------------------------------------- Aufräumen (DSGVO)
def housekeeping():
    while True:
        try:
            cut = (now() - dt.timedelta(days=Cfg.retention_days)).isoformat()
            cut_orders = (now() - dt.timedelta(days=3650)).isoformat()
            with db() as c:
                n1 = c.execute("DELETE FROM anfragen WHERE updated < ? AND status IN ('neu','in_bearbeitung','angebot_gesendet','abgelehnt','storniert','verfallen') "
                               "AND id NOT IN (SELECT anfrage_id FROM gutscheine WHERE anfrage_id IS NOT NULL)", (cut,)).rowcount
                n2 = c.execute("DELETE FROM anfragen WHERE updated < ?", (cut_orders,)).rowcount
                n3 = c.execute("DELETE FROM events WHERE day < ?", ((today() - dt.timedelta(days=Cfg.stats_days)).isoformat(),)).rowcount
                c.execute("DELETE FROM salts WHERE day < ?", (today().isoformat(),))
                c.execute("DELETE FROM blocked WHERE day < ?", ((today() - dt.timedelta(days=30)).isoformat(),))
            if n1 or n2 or n3:
                log(f"Aufräumen: {n1 + n2} Anfragen, {n3} Statistik-Einträge gelöscht")
        except Exception as e:
            log("Aufräumen fehlgeschlagen:", e)
        time.sleep(6 * 3600)


# --------------------------------------------------------------------------- Angebote
OFFER_ICONS = ("spark", "snow", "gift", "tag", "brief", "key", "shield", "star")
OFFER_HREF_RE = re.compile(r"^(?:[a-z0-9][a-z0-9/_.\-]*(?:\?[a-z0-9=&_.\-]*)?(?:#[a-z0-9_\-]+)?|https://[^\s\"'<>]{4,300})$", re.I)


def offers_file():
    return os.path.join(Cfg.content, "angebote.json")


def load_offers():
    try:
        with open(offers_file(), encoding="utf-8") as f:
            d = json.load(f)
    except (FileNotFoundError, ValueError):
        d = {}
    if not isinstance(d, dict):
        d = {}
    d.setdefault("items", [])
    missing = [o for o in d["items"] if not re.fullmatch(r"[a-f0-9]{8}", str(o.get("id", "")))]
    for o in missing:
        o["id"] = secrets.token_hex(4)
    if missing and os.path.exists(offers_file()):
        save_offers(d)  # feste IDs, damit Bearbeiten und Löschen zuverlässig funktionieren
    return d


def save_offers(d):
    p = offers_file()
    backup(p)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, p)


def offer_state(o, day=None):
    day = (day or today()).isoformat()
    if not o.get("active", True):
        return "aus"
    if o.get("validFrom") and o["validFrom"] > day:
        return "geplant"
    if o.get("validUntil") and o["validUntil"] < day:
        return "abgelaufen"
    return "aktiv"


def offers_live_signature():
    """Welche Angebote heute sichtbar sein müssen. Ändert sich das (Start- oder Enddatum erreicht), wird neu veröffentlicht."""
    sig = ",".join(o["id"] for o in load_offers()["items"] if offer_state(o) == "aktiv")
    # Aktionspreise in pricing.json (Winterangebot, Scheiben-Aktion) laufen ebenfalls automatisch an und aus
    return sig + f"|winter:{bool(winter_offer())}|scheiben:{sorted(scheiben_items().items())}"


def clean_offer(d, media_dir):
    errors, out = {}, {}
    out["title"] = _s(d, "title", 80, True, errors, label="Titel")
    out["badge"] = _s(d, "badge", 30, False, errors, label="Etikett")
    out["text"] = _s(d, "text", 400, False, errors, label="Beschreibung")
    out["price"] = _s(d, "price", 60, False, errors, label="Preisangabe")
    out["ctaLabel"] = _s(d, "ctaLabel", 40, False, errors, label="Button-Text") or "Jetzt anfragen"
    href = _s(d, "ctaHref", 300, False, errors, label="Button-Ziel") or "termin.html"
    if not OFFER_HREF_RE.match(href) or href.lower().startswith(("javascript", "data")):
        errors["ctaHref"] = "Bitte eine Seite der Website (z. B. termin.html) oder eine https-Adresse angeben."
    out["ctaHref"] = href
    out["icon"] = d.get("icon") if d.get("icon") in OFFER_ICONS else "spark"
    for k in ("validFrom", "validUntil"):
        v = str(d.get(k) or "").strip()
        if v and not _date(v):
            errors[k] = "Ungültiges Datum."
        out[k] = v if _date(v) else ""
    if out["validFrom"] and out["validUntil"] and out["validUntil"] < out["validFrom"]:
        errors["validUntil"] = "Das Enddatum liegt vor dem Startdatum."
    img = str(d.get("image") or "").strip()
    if img and (not MEDIA_RE.match(img) or not os.path.exists(os.path.join(media_dir, img))):
        errors["image"] = "Bild nicht gefunden. Bitte erneut hochladen."
    out["image"] = img
    out["imageAlt"] = _s(d, "imageAlt", 140, False, errors, label="Bildbeschreibung")
    out["active"] = bool(d.get("active", True))
    out["highlight"] = bool(d.get("highlight", False))
    if errors:
        raise Invalid(errors)
    return out


def offers_watcher():
    """Stündlich prüfen, ob ein Angebot heute startet oder abgelaufen ist, und die Website dann automatisch neu veröffentlichen."""
    if setting("offersSig") is None:
        set_setting("offersSig", offers_live_signature())
    while True:
        time.sleep(3600)
        try:
            sig = offers_live_signature()
            if sig != setting("offersSig"):
                r = publish()
                if r.get("ok"):
                    set_setting("offersSig", sig)
                    log("Angebote: Laufzeit geändert, Website neu veröffentlicht")
        except Exception as e:
            log("Angebote-Prüfung fehlgeschlagen:", e)


# --------------------------------------------------------------------------- Google-Bewertungen automatisch aktuell halten
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def reviews_fetch():
    """Bewertung und Anzahl aus der Google Places API (New). Braucht GOOGLE_PLACES_API_KEY und googlePlaceId in den Grunddaten."""
    key, pid = env("GOOGLE_PLACES_API_KEY"), (site_info().get("googlePlaceId") or "").strip()
    if not key or not pid:
        return None
    req = urllib.request.Request("https://places.googleapis.com/v1/places/" + urllib.parse.quote(pid, safe=""),
                                 headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "rating,userRatingCount"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.loads(r.read())
    if "userRatingCount" not in j:
        return None
    return {"value": f"{float(j.get('rating', 0)):.1f}".replace(".", ","), "count": int(j["userRatingCount"])}


def reviews_sync():
    """Neue Werte in die Grunddaten schreiben und die Website neu veröffentlichen, wenn sich etwas geändert hat."""
    got = reviews_fetch()
    if not got:
        return {"ok": False, "message": "Google-Bewertungen nicht abrufbar (API-Schlüssel oder Place-ID fehlt)."}
    path = os.path.join(Cfg.content, "site.json")
    with BUILD_LOCK:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        cur = d.get("rating") or {}
        set_setting("reviewsChecked", now().isoformat())
        if cur.get("value") == got["value"] and int(cur.get("count", 0)) == got["count"]:
            return {"ok": True, "changed": False, "message": f"Aktuell: {got['value']} ★ bei {got['count']} Bewertungen."}
        backup(path)
        cur.update(got, asOf=f"{MONTHS[today().month - 1]} {today().year}")
        d["rating"] = cur
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")
    audit("bewertungen_aktualisiert", f"{got['value']} ★ / {got['count']}")
    r = publish()
    return {"ok": r.get("ok", False), "changed": True, "message": f"Aktualisiert: {got['value']} ★ bei {got['count']} Bewertungen. Website neu veröffentlicht."}


def reviews_watcher():
    while True:
        time.sleep(60)
        try:
            if env("GOOGLE_PLACES_API_KEY"):
                reviews_sync()
        except Exception as e:
            log("Bewertungsabgleich fehlgeschlagen:", e)
        time.sleep(6 * 3600)


# --------------------------------------------------------------------------- Sicherheit
class RateLimit:
    def __init__(self):
        self.hits = collections.defaultdict(collections.deque)
        self.lock = threading.Lock()

    def ok(self, key, limit, window):
        t = time.time()
        with self.lock:
            q = self.hits[key]
            while q and q[0] < t - window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(t)
            if len(self.hits) > 20000:
                self.hits.clear()
            return True


RL = RateLimit()


def hash_password(pw, iterations=600000):
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, iterations)
    return f"pbkdf2_sha256:{iterations}:{base64.b64encode(salt).decode()}:{base64.b64encode(h).decode()}"


def check_password(pw):
    if Cfg.admin_hash:
        try:
            algo, it, salt, h = re.split(r"[:$]", Cfg.admin_hash.strip())
            calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), base64.b64decode(salt), int(it))
            return hmac.compare_digest(calc, base64.b64decode(h))
        except Exception:
            return False
    if Cfg.admin_plain:
        return hmac.compare_digest(pw.encode(), Cfg.admin_plain.encode())
    return False


def make_session(user):
    payload = base64.urlsafe_b64encode(json.dumps({"u": user, "exp": int(time.time()) + 12 * 3600}).encode()).decode().rstrip("=")
    sig = hmac.new(secret_key(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def read_session(cookie):
    try:
        payload, sig = cookie.split(".")
        if not hmac.compare_digest(sig, hmac.new(secret_key(), payload.encode(), hashlib.sha256).hexdigest()):
            return None
        d = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return d["u"] if d["exp"] > time.time() else None
    except Exception:
        return None


EDITABLE = re.compile(r"^(site|pricing|reviews|faq|gallery|angebote|zertifikate)\.json$|^services/[a-z0-9-]{2,80}\.json$|^ratgeber/[a-z0-9-]{2,80}\.md$")
MEDIA_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}\.(jpg|jpeg|png|webp)$")


def safe_content_path(rel):
    if not EDITABLE.match(rel or ""):
        return None
    p = os.path.realpath(os.path.join(Cfg.content, rel))
    return p if p.startswith(os.path.realpath(Cfg.content) + os.sep) else None


def backup(path):
    if not os.path.exists(path):
        return
    hist = os.path.join(Cfg.data, "history", os.path.relpath(path, Cfg.content).replace(os.sep, "__"))
    os.makedirs(hist, exist_ok=True)
    shutil.copy2(path, os.path.join(hist, now().strftime("%Y%m%d-%H%M%S") + os.path.splitext(path)[1]))
    for old in sorted(os.listdir(hist))[:-30]:
        os.remove(os.path.join(hist, old))


# --------------------------------------------------------------------------- HTTP
def wa_number(tel):
    d = re.sub(r"\D", "", tel or "")
    if d.startswith("00"):
        d = d[2:]
    elif d.startswith("0"):
        d = "49" + d[1:]
    return d


class Handler(BaseHTTPRequestHandler):
    server_version = "ElbDetail"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    # ---- Helfer
    def log_message(self, fmt, *args):  # keine IP-Protokolle
        pass

    def ip(self):
        if Cfg.trust_proxy:
            xff = self.headers.get("X-Forwarded-For", "")
            if xff:
                return xff.split(",")[0].strip()
        return self.client_address[0]

    def drain(self):
        """Ungelesenen Anfrage-Inhalt verwerfen. Sonst stünde er bei wiederverwendeten Verbindungen
        (Keep-Alive, z. B. hinter Caddy) vor der nächsten Anfrage und würde diese zerstören."""
        if getattr(self, "_body_done", True):
            return
        self._body_done = True
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > 2_000_000 or "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            self.close_connection = True
        elif n:
            self.rfile.read(n)

    def send(self, code, body=b"", ctype="application/json; charset=utf-8", headers=None):
        self.drain()
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        if self.path.startswith(("/admin", "/api", "/gutschein")):
            self.send_header("Cache-Control", "no-store")
        if self.path.startswith("/admin") or self.path.startswith("/gutschein/"):
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
                                                        "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def body(self, limit):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit:
            raise ValueError("zu groß")
        self._body_done = True
        return self.rfile.read(n) if n else b""

    def parse(self, limit=65536):
        raw = self.body(limit)
        ct = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ct == "application/x-www-form-urlencoded":
            q = urllib.parse.parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
            return {k: (v if len(v) > 1 or k in ("zustand", "extras", "leistungen") else v[0]) for k, v in q.items()}
        return json.loads(raw.decode("utf-8") or "{}")

    def user(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "elb_s":
                return read_session(v)
        return None

    def same_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or ""
        return urllib.parse.urlparse(origin).netloc == host

    # ---- Routing
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_PUT(self):
        self.route("PUT")

    def do_PATCH(self):
        self.route("PATCH")

    def do_DELETE(self):
        self.route("DELETE")

    def route(self, method):
        self._body_done = False
        try:
            u = urllib.parse.urlparse(self.path)
            path, qs = u.path, urllib.parse.parse_qs(u.query)
            if path.startswith("/api/"):
                return self.api(method, path, qs)
            if path == "/admin" and method == "GET":
                return self.send(301, b"", "text/plain", {"Location": "/admin/"})
            if path.startswith("/admin/api/"):
                return self.admin_api(method, path[len("/admin/api/"):], qs)
            if path.startswith("/admin/") and method in ("GET", "HEAD"):
                return self.admin_static(path[len("/admin/"):])
            if path == "/gutschein-druck.js":
                return self.send(200, "document.getElementById('printBtn')&&document.getElementById('printBtn').addEventListener('click',function(){window.print()});",
                                 "text/javascript; charset=utf-8")
            m = re.match(r"^/termin/(T\d{6}-[0-9A-F]{4})(?:/(bestaetigen|absagen|verschieben|widerrufen|bezahlt))?$", path)
            if m and method in ("GET", "HEAD", "POST"):
                act = m.group(2) or ""
                if act and (method == "POST") != (act != "bezahlt"):
                    act = ""  # bestätigen/absagen nur per POST, die Rückkehr von PayPal (bezahlt) nur per GET
                return self.termin_page(m.group(1), act, qs)
            m = re.match(r"^/gutschein/(ELB-[A-Z0-9]{4}-[A-Z0-9]{4})$", path)
            if m and method in ("GET", "HEAD"):
                return self.voucher_page(m.group(1), (qs.get("t") or [""])[0])
            if Cfg.serve_static and method in ("GET", "HEAD"):
                return self.static(path)
            self.send(404, {"ok": False, "message": "Nicht gefunden"})
        except Invalid as e:
            self.send(422, {"ok": False, "errors": e.errors, "message": next(iter(e.errors.values()))})
        except (ValueError, json.JSONDecodeError) as e:
            self.send(400, {"ok": False, "message": f"Ungültige Anfrage: {e}"})
        except Exception:
            traceback.print_exc()
            self.send(500, {"ok": False, "message": "Interner Fehler"})

    # ---- Öffentliche API
    def api(self, method, path, qs):
        ip = self.ip()
        if path == "/api/health":
            return self.send(200, {"ok": True})
        if path == "/api/verfuegbarkeit" and method == "GET":
            bl, closed = blocked_days(), setting("closedWeekdays", [0])
            return self.send(200, {"blocked": bl, "blockedKeramik": blocked_days(keramik=True), "closedWeekdays": closed,
                                   "nextFree": next_free_day(bl, closed), "selfBooking": self_booking(), "slotTimes": booking_cfg()["slotTimes"]})
        if path == "/api/slots" and method == "GET":
            if not RL.ok("s:" + ip, 120, 60):
                return self.send(429, {"ok": False})
            day = (qs.get("tag") or [""])[0]
            if not _date(day):
                return self.send(400, {"ok": False, "message": "Ungültiges Datum"})
            return self.send(200, {"tag": day, "slots": free_slots(day, keramik=ker_booking({"paket": (qs.get("paket") or [""])[0], "winterschutz": WINTERSCHUTZ.get((qs.get("winterschutz") or [""])[0])})), "selfBooking": self_booking()})
        if path == "/api/kalender.ics" and method == "GET":
            key = setting("icsKey", "")
            if not key or not hmac.compare_digest(key, (qs.get("key") or [""])[0]):
                return self.send(404, {"ok": False})
            return self.send(200, ics_feed(), "text/calendar; charset=utf-8", {"Cache-Control": "no-store"})
        if path == "/api/e" and method == "POST":
            if RL.ok("e:" + ip, 120, 60):
                try:
                    record_event(json.loads(self.body(4096) or b"{}"), ip, self.headers.get("User-Agent", ""))
                except Exception:
                    pass
            return self.send(204, b"")
        if path == "/api/anfrage" and method == "POST":
            if not self.same_origin():
                return self.send(403, {"ok": False, "message": "Herkunft nicht erlaubt"})
            if not RL.ok("a:" + ip, Cfg.rate_requests, 600):
                return self.send(429, {"ok": False, "message": "Zu viele Anfragen in kurzer Zeit. Bitte später erneut versuchen oder per WhatsApp schreiben."})
            is_form = (self.headers.get("Content-Type") or "").startswith("application/x-www-form-urlencoded")
            d = self.parse()
            if d.get("website"):  # Honeypot: so tun, als wäre alles gut
                return self.send(200, {"ok": True, "ref": "OK"}) if not is_form else self.send(303, b"", "text/plain", {"Location": "/danke.html"})
            try:
                data = validate(d)
            except Invalid as e:
                if is_form:
                    msg = "<br>".join(html.escape(x) for x in e.errors.values())
                    return self.send(422, f'<!DOCTYPE html><meta charset="utf-8"><title>Bitte prüfen</title><p>{msg}</p><p><a href="javascript:history.back()">Zurück</a></p>', "text/html; charset=utf-8")
                raise
            ref, status = store_request(data)
            if is_form:
                return self.send(303, b"", "text/plain", {"Location": f"/danke.html?typ={data['typ']}&ref={ref}" + ("&s=reserviert" if status == "reserviert" else "")})
            return self.send(200, {"ok": True, "ref": ref, "status": status})
        self.send(404, {"ok": False})

    def termin_page(self, ref, action, qs):
        r, d = load_termin(ref)
        token = (qs.get("t") or [""])[0]
        if action:
            if not RL.ok("tp:" + self.ip(), 30, 600):
                return self.send(429, "Zu viele Versuche. Bitte später erneut.", "text/plain; charset=utf-8")
            form = {}
            if action != "bezahlt":
                form = self.parse(4096)
                token = str(form.get("t", ""))
        if not r or not token or not d.get("token") or not hmac.compare_digest(d["token"], token):
            return self.send(404, '<!DOCTYPE html><meta charset="utf-8"><title>Nicht gefunden</title><p>Termin nicht gefunden. Bitte nutzen Sie den Link aus Ihrer E-Mail.</p>', "text/html; charset=utf-8")
        notice, err = "", ""
        valid = r["status"] == "reserviert" and d.get("hold_until", "") >= now().isoformat()
        if action == "bestaetigen" and valid:
            if form.get("agb") != "1" or (early_start(d) and form.get("vorzeitig") != "1"):
                action, err = "", "Bitte bestätigen Sie die AGB" + (" und den Beginn vor Ablauf der Widerrufsfrist." if early_start(d) else ".")
                notice = err
            else:
                d["agb_am"] = now().isoformat()
                if early_start(d):
                    d["vorzeitig_am"] = now().isoformat()
                save_termin(r["id"], d)
        if (qs.get("abbruch") or [""])[0] and valid:
            notice = "Die Zahlung wurde abgebrochen. Ihr Termin bleibt reserviert, Sie können die Anzahlung hier jederzeit nachholen."
        if action == "bestaetigen" and valid and deposit_me(d):
            first = not d.get("paypalme_am")
            d["paypalme_am"] = d.get("paypalme_am") or now().isoformat()
            hold = (now() + dt.timedelta(hours=72)).isoformat()  # Zeit für René, den Zahlungseingang zu prüfen
            d["hold_until"] = max(d.get("hold_until", ""), hold)
            save_termin(r["id"], d)
            if first:
                audit("paypalme_weitergeleitet", ref)
                mail_async(Cfg.notify_to or site_info().get("email"), f"Anzahlung per PayPal.me unterwegs: {d.get('name')} · {de_when(d)} ({ref})",
                           f"Der Kunde hat die AGB bestätigt und wurde zu PayPal.me weitergeleitet ({eur(d['anzahlung'])}, Verwendungszweck {ref}).\n"
                           f"Bitte den Zahlungseingang in PayPal prüfen und im Verwaltungsportal auf „Anzahlung eingegangen“ klicken. "
                           f"Erst dann bekommt der Kunde die Terminbestätigung. Die Uhrzeit bleibt bis {dt.datetime.fromisoformat(hold).strftime('%d.%m. %H:%M')} Uhr reserviert.\n\n"
                           f"{summary_text(public_data(d))}\n\nIm Verwaltungsportal: {Cfg.public_url}/admin/#/anfragen/{ref}\n")
            return self.send(303, b"", "text/plain", {"Location": paypal_me_link(d), "Cache-Control": "no-store"})
        if action == "bestaetigen" and valid and deposit_online(d):
            try:  # Anzahlung: weiter zu PayPal, bestätigt wird erst nach erfolgreicher Zahlung
                oid, link = paypal_create(ref, d)
            except Exception as e:
                log("PayPal-Auftrag fehlgeschlagen:", e)
                oid, link = "", ""
            if oid and link:
                d["paypal_order"] = oid
                save_termin(r["id"], d)
                return self.send(303, b"", "text/plain", {"Location": link, "Cache-Control": "no-store"})
            notice = "PayPal ist gerade nicht erreichbar. Bitte versuchen Sie es in ein paar Minuten erneut oder melden Sie sich telefonisch."
        elif action == "bezahlt":
            oid = (qs.get("token") or [""])[0]
            if r["status"] == "termin_bestaetigt":
                notice = "Vielen Dank, Ihr Termin ist verbindlich gebucht."
            elif valid and oid and oid == d.get("paypal_order"):
                try:
                    pay = paypal_capture(oid)
                except Exception as e:
                    log("PayPal-Zahlung nicht erfasst:", e)
                    pay = {}
                if pay.get("capture_id") and pay.get("capture_status") == "COMPLETED" and pay.get("currency") == "EUR" and pay.get("value", 0) + 0.005 >= d["anzahlung"]:
                    d["zahlung"] = {"anbieter": "paypal", "order_id": oid, "capture_id": pay["capture_id"], "value": pay["value"], "am": now().isoformat()}
                    save_termin(r["id"], d)
                    r, d = load_termin(ref)
                    confirm_termin(r, d, "kunde")
                    notice = "Vielen Dank, Ihre Anzahlung ist eingegangen und Ihr Termin verbindlich gebucht. Die Bestätigung kommt per E-Mail."
                else:
                    notice = "Die Zahlung konnte nicht abgeschlossen werden. Bitte versuchen Sie es erneut."
            else:
                notice = "Diese Zahlung gehört nicht zu Ihrem Termin oder die Reservierung ist abgelaufen."
        elif action == "bestaetigen" and valid:
            confirm_termin(r, d, "kunde")
            notice = "Vielen Dank, Ihr Termin ist verbindlich gebucht. Die Bestätigung kommt per E-Mail."
        elif action == "absagen" and (r["status"] == "reserviert" or (r["status"] == "termin_bestaetigt" and form.get("ok") == "1")):
            cancel_termin(r, d, "kunde")
            notice = "Ihr Termin ist abgesagt. Schade, vielleicht ein andermal."
        elif action == "widerrufen" and r["status"] == "termin_bestaetigt" and in_widerruf(d) and form.get("ok") == "1":
            cancel_termin(r, d, "widerruf")
            notice = "Ihr Widerruf ist eingegangen und der Termin abgesagt. Die Eingangsbestätigung kommt per E-Mail."
        elif action == "verschieben" and r["status"] == "termin_bestaetigt":
            err = reschedule_termin(r, d, str(form.get("datum", "")), str(form.get("uhrzeit", "")), "kunde")
            notice = err or "Ihr Termin ist verschoben. Die neue Bestätigung kommt per E-Mail."
        if action:  # aktuellen Stand zeigen; ein erneutes Absenden löst nichts doppelt aus
            r, d = load_termin(ref)
        mode = ("verschieben" if action == "verschieben" else "") if err else ("" if action else (qs.get("aktion") or [""])[0])
        tag = str(form.get("datum", ""))[:10] if err else (qs.get("tag") or [""])[0][:10]
        self.send(200, termin_html(r, d, notice, mode if mode in ("verschieben", "absagen", "widerrufen") else "", tag),
                  "text/html; charset=utf-8", {"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})

    def voucher_page(self, code, token):
        with db() as c:
            v = c.execute("SELECT * FROM gutscheine WHERE code=?", (code,)).fetchone()
        if not v or not token or not hmac.compare_digest(v["token"], token):
            return self.send(404, '<!DOCTYPE html><meta charset="utf-8"><title>Nicht gefunden</title><p>Gutschein nicht gefunden.</p>', "text/html; charset=utf-8")
        self.send(200, voucher_html(dict(v)), "text/html; charset=utf-8")

    # ---- Statische Dateien (nur Entwicklung; produktiv liefert Caddy aus)
    def static(self, path):
        base = os.path.realpath(site_dir())
        rel = urllib.parse.unquote(path).lstrip("/") or "index.html"
        p = os.path.realpath(os.path.join(base, rel))
        if os.path.isdir(p):
            p = os.path.join(p, "index.html")
        if not p.startswith(base) or not os.path.isfile(p):
            nf = os.path.join(base, "404.html")
            return self.send(404, open(nf, "rb").read() if os.path.exists(nf) else b"404", "text/html; charset=utf-8")
        ctype = mimetypes.guess_type(p)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self.send(200, open(p, "rb").read(), ctype)

    def admin_static(self, rel):
        rel = rel or "index.html"
        p = os.path.realpath(os.path.join(ADMIN_DIR, rel))
        if not p.startswith(os.path.realpath(ADMIN_DIR) + os.sep) or not os.path.isfile(p):
            p = os.path.join(ADMIN_DIR, "index.html")
        ctype = mimetypes.guess_type(p)[0] or "text/plain"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self.send(200, open(p, "rb").read(), ctype)

    # ---- Verwaltungs-API
    def admin_api(self, method, path, qs):
        if method != "GET" and (self.headers.get("X-ELB-Admin") != "1" or not self.same_origin()):
            return self.send(403, {"ok": False, "message": "Ungültige Anfrage"})
        if path == "login" and method == "POST":
            if not RL.ok("login:" + self.ip(), 8, 900):
                return self.send(429, {"ok": False, "message": "Zu viele Versuche. Bitte 15 Minuten warten."})
            d = self.parse()
            if hmac.compare_digest(str(d.get("user", "")).encode(), Cfg.admin_user.encode()) and check_password(str(d.get("password", ""))):
                audit("login")
                flags = "; Secure" if Cfg.cookie_secure else ""
                return self.send(200, {"ok": True}, headers={"Set-Cookie": f"elb_s={make_session(Cfg.admin_user)}; Path=/admin; HttpOnly; SameSite=Strict; Max-Age=43200{flags}"})
            time.sleep(0.8)
            return self.send(401, {"ok": False, "message": "Benutzername oder Passwort falsch."})
        if path == "logout":
            return self.send(200, {"ok": True}, headers={"Set-Cookie": "elb_s=; Path=/admin; HttpOnly; SameSite=Strict; Max-Age=0"})
        if path == "google/callback" and method == "GET":  # Rückkehr von Google: Sitzungs-Cookie (SameSite=Strict) fehlt hier, daher signierter state
            return self.google_callback(qs)
        user = self.user()
        if not user:
            return self.send(401, {"ok": False, "message": "Bitte anmelden."})
        return AdminAPI(self, method, path, qs).run()

    def google_callback(self, qs):
        state = (qs.get("state") or [""])[0]
        try:
            ts, sig = state.split(".", 1)
            good = hmac.compare_digest(sig, hmac.new(secret_key(), ("google:" + ts).encode(), hashlib.sha256).hexdigest()) and time.time() - int(ts) < 900
        except ValueError:
            good = False
        code = (qs.get("code") or [""])[0]
        if not good or not code or not google_configured():
            return self.send(302, b"", "text/plain", {"Location": "/admin/#/kalender?google=fehler"})
        try:
            j = _gpost("https://oauth2.googleapis.com/token", {"code": code, "client_id": env("GOOGLE_CLIENT_ID"), "client_secret": env("GOOGLE_CLIENT_SECRET"),
                                                                "redirect_uri": google_redirect(), "grant_type": "authorization_code"})
            if j.get("refresh_token"):
                set_setting("googleRefreshToken", j["refresh_token"])
                _GTOKEN.update(token=j.get("access_token", ""), exp=time.time() + int(j.get("expires_in", 3600)))
                audit("google_verbunden")
                return self.send(302, b"", "text/plain", {"Location": "/admin/#/kalender?google=ok"})
        except Exception as e:
            log("Google-Verbindung fehlgeschlagen:", e)
        return self.send(302, b"", "text/plain", {"Location": "/admin/#/kalender?google=fehler"})


class AdminAPI:
    def __init__(self, h, method, path, qs):
        self.h, self.m, self.p, self.qs = h, method, path, qs

    def q(self, k, d=""):
        return (self.qs.get(k) or [d])[0]

    def run(self):
        h, m, p = self.h, self.m, self.p
        if p == "me":
            s = site_info()
            return h.send(200, {"user": Cfg.admin_user, "site": s.get("name"), "url": Cfg.public_url, "mail": mail_ready(),
                                "lastPublish": setting("lastPublish"), "open": self._open(), "outbox": outbox_open()})
        if p == "stats":
            return h.send(200, stats(self.q("days", "30")))
        if p == "anfragen" and m == "GET":
            return h.send(200, self.list_requests())
        if p == "anfragen.csv":
            return self.csv_export()
        mm = re.match(r"^anfragen/([A-Z]\d{6}-[0-9A-F]{4}|\d+)$", p)
        if mm:
            return self.request_item(mm.group(1))
        mm = re.match(r"^anfragen/(T\d{6}-[0-9A-F]{4})/erstatten$", p)
        if mm and m == "POST":
            return self.refund(mm.group(1))
        mm = re.match(r"^anfragen/(T\d{6}-[0-9A-F]{4})/anzahlung$", p)
        if mm and m == "POST":
            return self.deposit_received(mm.group(1))
        mm = re.match(r"^anfragen/([A-Z]\d{6}-[0-9A-F]{4})/vorlage$", p)
        if mm:
            return self.template(mm.group(1), self.q("art", "antwort"))
        if p == "gutscheine":
            return self.vouchers()
        mm = re.match(r"^gutscheine/(\d+)$", p)
        if mm:
            return self.voucher_item(int(mm.group(1)))
        if p == "gutscheine/pruefen":
            return self.voucher_check(self.q("code").upper().strip())
        if p == "kalender":
            return self.calendar()
        if p == "google":
            return self.google()
        if p == "postausgang":
            return self.outbox()
        mm = re.match(r"^postausgang/(\d+)(?:/(freigeben|verwerfen))?$", p)
        if mm:
            return self.outbox_item(int(mm.group(1)), mm.group(2) or "")
        if p == "einstellungen":
            return self.settings()
        if p == "inhalte" and m == "GET":
            return h.send(200, self.content_list())
        if p == "inhalte/neuer-artikel" and m == "POST":
            return self.new_article()
        if p == "vorschau" and m == "POST":
            d = h.parse(262144)
            return h.send(200, {"html": mdlib.render(str(d.get("md", "")), "/")})
        if p.startswith("inhalte/"):
            return self.content_item(p[len("inhalte/"):])
        if p == "angebote":
            return self.offers()
        if p == "angebote/reihenfolge" and m == "PUT":
            return self.offers_order()
        mm = re.match(r"^angebote/([a-f0-9]{8})$", p)
        if mm:
            return self.offer_item(mm.group(1))
        if p == "medien" and m == "GET":
            return h.send(200, self.media_list())
        if p == "medien" and m == "POST":
            return self.media_upload()
        mm = re.match(r"^medien/(.+)$", p)
        if mm:
            return self.media_item(mm.group(1))
        if p == "veroeffentlichen" and m == "POST":
            return h.send(200, publish())
        if p == "bewertungen" and m == "POST":
            try:
                return h.send(200, reviews_sync())
            except Exception as e:
                return h.send(502, {"ok": False, "message": f"Abruf bei Google fehlgeschlagen: {e}"})
        if p == "testmail" and m == "POST":
            ok = send_mail(Cfg.notify_to or site_info().get("email"), "Test-E-Mail vom ElbDetail-Server", "Wenn du das liest, funktioniert der E-Mail-Versand.")
            return h.send(200, {"ok": ok, "message": "Test-E-Mail versendet." if ok else "Versand fehlgeschlagen oder SMTP nicht eingerichtet."})
        if p == "audit":
            with db() as c:
                return h.send(200, [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")])
        h.send(404, {"ok": False, "message": "Unbekannt"})

    def _open(self):
        with db() as c:
            return c.execute("SELECT COUNT(*) n FROM anfragen WHERE status='neu'").fetchone()["n"]

    # Anfragen
    def list_requests(self):
        where, args = ["1=1"], []
        if self.q("typ") in TYPES:
            where.append("typ=?"); args.append(self.q("typ"))
        if self.q("status") in STATUS:
            where.append("status=?"); args.append(self.q("status"))
        if self.q("q"):
            where.append("(name LIKE ? OR telefon LIKE ? OR email LIKE ? OR ref LIKE ? OR data LIKE ?)")
            args += [f"%{self.q('q')}%"] * 5
        limit = min(int(self.q("limit", "100") or 100), 500)
        with db() as c:
            rows = [dict(r) for r in c.execute(f"SELECT id, ref, typ, status, created, updated, name, telefon, email, datum, data FROM anfragen WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT ?", args + [limit])]
            counts = {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM anfragen GROUP BY status")}
        for r in rows:
            d = json.loads(r.pop("data") or "{}")
            r["paket"] = d.get("paket", "")
            r["klasse"] = d.get("klasse", "")
            r["preis"] = richtpreis(d)
            r["wert"] = d.get("wert")
            r["firma"] = d.get("firma", "")
        return {"items": rows, "counts": counts}

    def request_item(self, key):
        h, m = self.h, self.m
        col = "ref" if not key.isdigit() else "id"
        with db() as c:
            r = c.execute(f"SELECT * FROM anfragen WHERE {col}=?", (key,)).fetchone()
            if not r:
                return h.send(404, {"ok": False, "message": "Nicht gefunden"})
            if m == "GET":
                d = dict(r)
                d["data"] = json.loads(d["data"] or "{}")
                d["summary"] = summary_text(d["data"])
                d["preis"] = richtpreis(d["data"])
                code = d["data"].get("gutscheincode")
                if code:
                    v = c.execute("SELECT code, status, wert, art, paket, valid_until FROM gutscheine WHERE code=?", (code,)).fetchone()
                    d["gutschein"] = dict(v) if v else {"code": code, "status": "unbekannt"}
                v = c.execute("SELECT id, code, status FROM gutscheine WHERE anfrage_id=?", (r["id"],)).fetchone()
                d["voucher"] = dict(v) if v else None
                return h.send(200, d)
            if m == "PATCH":
                body = h.parse()
                st = body.get("status", r["status"])
                if st not in STATUS:
                    return h.send(422, {"ok": False, "message": "Ungültiger Status"})
                notes = str(body.get("notizen", r["notizen"] or ""))[:5000]
                moved = False
                if r["typ"] == "termin" and ("datum" in body or "uhrzeit" in body):  # Termin verschieben (Datum/Uhrzeit)
                    dd = json.loads(r["data"] or "{}")
                    nd, nt = str(body.get("datum", dd.get("datum", ""))), str(body.get("uhrzeit", dd.get("uhrzeit", "")))
                    if not _date(nd) or (nt and not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", nt)):
                        return h.send(422, {"ok": False, "message": "Ungültiges Datum oder Uhrzeit"})
                    moved = (nd, nt) != (dd.get("datum"), dd.get("uhrzeit", ""))
                    if moved:
                        dd.update(datum=nd, uhrzeit=nt)
                        c.execute("UPDATE anfragen SET datum=?, data=? WHERE id=?", (nd, json.dumps(dd, ensure_ascii=False), r["id"]))
                c.execute("UPDATE anfragen SET status=?, notizen=?, updated=? WHERE id=?", (st, notes, now().isoformat(), r["id"]))
                audit("anfrage_status", f"{r['ref']} → {st}", c)
                c.commit()  # erst speichern, dann antworten (sonst sieht ein sofortiges Neuladen den alten Stand)
                if r["typ"] == "termin" and st != r["status"]:
                    rr, dd = load_termin(r["ref"])
                    if st == "termin_bestaetigt":  # Bestätigung durch den Betrieb: Kalender und E-Mail wie bei Kundenbestätigung
                        confirm_termin(rr, dd, "betrieb")
                    elif st in ("abgelehnt", "storniert") and dd.get("gcal_id"):
                        threading.Thread(target=google_delete, args=(r["ref"],), daemon=True).start()
                elif moved and st == "termin_bestaetigt":  # verschobener, bestätigter Termin: Kalender und Kunde informieren
                    rr, dd = load_termin(r["ref"])
                    threading.Thread(target=google_upsert, args=(r["ref"],), daemon=True).start()
                    if dd.get("email") and dd.get("token"):
                        mail_confirmed(r["ref"], dd)
                        schedule_reminders(r["ref"], dd)
                return h.send(200, {"ok": True})
            if m == "DELETE":
                c.execute("UPDATE gutscheine SET anfrage_id=NULL WHERE anfrage_id=?", (r["id"],))
                c.execute("DELETE FROM anfragen WHERE id=?", (r["id"],))
                audit("anfrage_geloescht", r["ref"], c)
                c.commit()
                return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def deposit_received(self, ref):
        """René hat die PayPal.me-Zahlung gesehen: Anzahlung festhalten und Termin bestätigen."""
        r, d = load_termin(ref)
        if not r or not d.get("anzahlung"):
            return self.h.send(404, {"ok": False, "message": "Zu diesem Termin ist keine Anzahlung hinterlegt."})
        if is_paid(d):
            return self.h.send(200, {"ok": True, "message": "Anzahlung ist bereits erfasst."})
        if r["status"] not in ("reserviert", "termin_bestaetigt"):
            return self.h.send(409, {"ok": False, "message": "Der Termin ist nicht mehr reserviert. Bitte mit dem Kunden einen neuen Termin vereinbaren und die Zahlung zurücksenden oder anrechnen."})
        d["zahlung"] = {"anbieter": "paypal.me", "manuell": True, "value": float(d["anzahlung"]), "am": now().isoformat()}
        save_termin(r["id"], d)
        audit("anzahlung_erfasst", f"{ref}: {d['anzahlung']} € per PayPal.me")
        r, d = load_termin(ref)
        if r["status"] != "termin_bestaetigt":
            confirm_termin(r, d, "betrieb")
        return self.h.send(200, {"ok": True, "message": "Anzahlung erfasst, Termin bestätigt."})

    def refund(self, ref):
        code, msg = refund_deposit(ref, auto=False)
        return self.h.send(code, {"ok": code == 200, "message": msg})

    def template(self, ref, art):
        s = site_info()
        with db() as c:
            r = c.execute("SELECT * FROM anfragen WHERE ref=?", (ref,)).fetchone()
            if not r:
                return self.h.send(404, {"ok": False})
            d = json.loads(r["data"] or "{}")
            parts = (r["name"] or "").split()
            first = " ".join(parts) or ""  # Sie-Form: vollständiger Name statt Vorname
            if art == "bewertung":
                link = s.get("googleReviewUrl") or "[GOOGLE-BEWERTUNGSLINK]"
                text = (f"Guten Tag {first}, vielen Dank, dass wir Ihr Auto aufbereiten durften! Über eine kurze, ehrliche "
                        f"Google-Bewertung würden wir uns sehr freuen. Das dauert nur eine Minute: {link}\nViele Grüße, {s.get('name', 'ElbDetail')}")
                c.execute("UPDATE anfragen SET bewertung_angefragt=? WHERE id=?", (now().isoformat(), r["id"]))
                warn = "" if d.get("bewertung_ok") == "ja" else "Achtung: Für diese Anfrage liegt keine Einwilligung zur Bewertungsanfrage vor. Bitte nur nach persönlicher Zustimmung senden."
            else:
                pr = pricing()
                pname = next((p["name"] for p in pr.get("packages", []) if p["key"] == d.get("paket")), d.get("paket", ""))
                date = _date(d.get("datum", ""))
                rp = richtpreis(d)
                text = f"Guten Tag {first}, vielen Dank für Ihre Anfrage bei {s.get('name', 'ElbDetail')}!"
                if date:
                    text += f" Ihr Wunschtermin am {date.strftime('%d.%m.%Y')} passt [ODER: Wir können Ihnen den … anbieten]."
                if pname:
                    text += f" Für {pname}" + (f" liegt der Richtpreis bei ab {rp} €" if rp else "") + ". Der verbindliche Preis für Ihr Fahrzeug: [PREIS] €."
                text += " Passt das für Sie? Viele Grüße"
                warn = ""
            tel = wa_number(r["telefon"])
            c.commit()
            return self.h.send(200, {"text": text, "whatsapp": f"https://wa.me/{tel}?text={urllib.parse.quote(text)}" if tel else "", "warning": warn,
                                     "mailto": f"mailto:{r['email']}?subject={urllib.parse.quote('Ihre Anfrage bei ' + s.get('name', 'ElbDetail'))}&body={urllib.parse.quote(text)}" if r["email"] else ""})

    def csv_export(self):
        with db() as c:
            rows = c.execute("SELECT ref, typ, status, created, name, telefon, email, datum, data, notizen FROM anfragen ORDER BY id DESC").fetchall()
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(["Vorgang", "Typ", "Status", "Eingang", "Name", "Telefon", "E-Mail", "Wunschtermin", "Details", "Notizen"])
        for r in rows:
            w.writerow([r["ref"], r["typ"], r["status"], r["created"], r["name"], r["telefon"], r["email"], r["datum"],
                        summary_text(json.loads(r["data"] or "{}")).replace("\n", " | "), r["notizen"]])
        audit("export_csv")
        self.h.send(200, "﻿" + buf.getvalue(), "text/csv; charset=utf-8",
                    {"Content-Disposition": f'attachment; filename="anfragen-{today().isoformat()}.csv"'})

    # Gutscheine
    def vouchers(self):
        h = self.h
        if self.m == "GET":
            with db() as c:
                rows = [dict(r) for r in c.execute("SELECT * FROM gutscheine ORDER BY id DESC LIMIT 500")]
            for r in rows:
                r["link"] = voucher_link(r)
            return h.send(200, rows)
        if self.m == "POST":
            d = h.parse()
            if d.get("fromRequest"):
                with db() as c:
                    r = c.execute("SELECT * FROM anfragen WHERE ref=?", (d["fromRequest"],)).fetchone()
                    if not r:
                        return h.send(404, {"ok": False})
                    if c.execute("SELECT 1 FROM gutscheine WHERE anfrage_id=?", (r["id"],)).fetchone():
                        return h.send(409, {"ok": False, "message": "Für diese Anfrage gibt es schon einen Gutschein."})
                    code = create_voucher(c, json.loads(r["data"]), r["id"])
            else:
                try:
                    wert = int(d.get("wert") or 0)
                except ValueError:
                    wert = 0
                if wert <= 0 and not d.get("paket"):
                    return h.send(422, {"ok": False, "message": "Bitte Wert oder Paket angeben."})
                data = {"art": "paket" if d.get("paket") else "wert", "wert": wert, "paket": str(d.get("paket", ""))[:20],
                        "fuer": str(d.get("fuer", ""))[:60], "von": str(d.get("von", ""))[:60], "widmung": str(d.get("widmung", ""))[:160],
                        "name": str(d.get("kaeufer", ""))[:120], "email": str(d.get("email", ""))[:160], "zustellung": "abholung"}
                with db() as c:
                    code = create_voucher(c, data)
            audit("gutschein_erstellt", code)
            return h.send(200, {"ok": True, "code": code})
        h.send(405, {"ok": False})

    def voucher_item(self, vid):
        h = self.h
        with db() as c:
            v = c.execute("SELECT * FROM gutscheine WHERE id=?", (vid,)).fetchone()
            if not v:
                return h.send(404, {"ok": False})
            if self.m == "PATCH":
                d = h.parse()
                st = d.get("status", v["status"])
                if st not in V_STATUS:
                    return h.send(422, {"ok": False, "message": "Ungültiger Status"})
                paid = v["paid_at"] or (now().isoformat() if st == "bezahlt" else None)
                red = now().isoformat() if st == "eingeloest" and not v["redeemed_at"] else v["redeemed_at"]
                c.execute("UPDATE gutscheine SET status=?, paid_at=?, redeemed_at=?, notiz=? WHERE id=?",
                          (st, paid, red, str(d.get("notiz", v["notiz"] or ""))[:1000], vid))
                audit("gutschein_status", f"{v['code']} → {st}", c)
                sent = False
                if st == "bezahlt" and d.get("sendMail") and v["email"]:
                    s = site_info()
                    vv = dict(v); vv["status"] = st
                    text = (f"Guten Tag {(v['kaeufer'] or '').strip()},\n\nvielen Dank, Ihre Zahlung ist eingegangen. Hier ist Ihr Gutschein zum Ausdrucken oder Weiterleiten:\n\n"
                            f"{voucher_link(vv)}\n\nCode: {v['code']}\nGültig bis {dt.date.fromisoformat(v['valid_until']).strftime('%d.%m.%Y')}\n\n"
                            f"Viel Freude beim Verschenken!\n{s.get('name', 'ElbDetail')}\n")
                    mail_async(v["email"], f"Ihr Gutschein von {s.get('name', 'ElbDetail')}", text, reply_to=s.get("email"))
                    sent = mail_ready()
                c.commit()
                return h.send(200, {"ok": True, "mailSent": sent})
            if self.m == "GET":
                d = dict(v); d["link"] = voucher_link(d)
                return h.send(200, d)
        h.send(405, {"ok": False})

    def voucher_check(self, code):
        with db() as c:
            v = c.execute("SELECT id, code, status, wert, art, paket, valid_until, fuer FROM gutscheine WHERE code=?", (code,)).fetchone()
        if not v:
            return self.h.send(404, {"ok": False, "message": "Code nicht gefunden"})
        d = dict(v)
        d["expired"] = d["valid_until"] < today().isoformat()
        self.h.send(200, d)

    # Kalender
    def calendar(self):
        h = self.h
        if self.m == "GET":
            with db() as c:
                bl = [dict(r) for r in c.execute("SELECT day, reason FROM blocked WHERE day >= ? ORDER BY day", ((today() - dt.timedelta(days=31)).isoformat(),))]
                req = [dict(r) for r in c.execute("SELECT datum day, COUNT(*) n, SUM(status='termin_bestaetigt') ok FROM anfragen WHERE typ='termin' AND datum != '' GROUP BY datum")]
            return h.send(200, {"blocked": bl, "requests": req, "closedWeekdays": setting("closedWeekdays", [0]),
                                "dailyCapacity": setting("dailyCapacity", 2), "leadDays": setting("leadDays", 1),
                                "keramikExclusive": bool(setting("keramikExclusive", True)), "keramikDays": setting("keramikDays", 3),
                                "nextFree": next_free_day(), "booking": booking_cfg(), "selfBooking": self_booking(), "mail": mail_ready(),
                                "google": {"configured": google_configured(), "connected": google_connected(), "redirect": google_redirect(),
                                           "calendarId": setting("googleCalendarId", "primary")},
                                "icsUrl": f"{Cfg.public_url}/api/kalender.ics?key={ics_key()}",
                                "paypal": {"configured": paypal_configured(), "mode": env("PAYPAL_MODE", "live"), "me": paypal_me_name(),
                                           "percent": (site_info().get("booking") or {}).get("depositPercent", 15)}})
        d = h.parse()
        if self.m == "POST":
            days = d.get("days") or [d.get("day")]
            with db() as c:
                for day in days:
                    if _date(str(day)):
                        c.execute("INSERT OR REPLACE INTO blocked(day, reason) VALUES (?,?)", (str(day), str(d.get("reason", ""))[:120]))
            return h.send(200, {"ok": True})
        if self.m == "DELETE":
            with db() as c:
                c.execute("DELETE FROM blocked WHERE day=?", (str(d.get("day")),))
            return h.send(200, {"ok": True})
        if self.m == "PUT":
            if "closedWeekdays" in d:
                set_setting("closedWeekdays", [int(x) for x in d.get("closedWeekdays", []) if str(x).isdigit() and 0 <= int(x) <= 6])
            if "keramikExclusive" in d:
                set_setting("keramikExclusive", bool(d["keramikExclusive"]))
            for k, lo, hi in (("dailyCapacity", 0, 20), ("leadDays", 0, 30), ("keramikDays", 1, 7)):
                if k in d:
                    v = int(d[k]) if str(d[k]).isdigit() else None
                    if v is None or not lo <= v <= hi:
                        raise Invalid({k: f"Bitte eine Zahl von {lo} bis {hi} angeben."})
                    set_setting(k, v)
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def outbox(self):
        h, m = self.h, self.m
        if m == "PUT":  # Freigabepflicht je E-Mail-Art
            d = h.parse()
            cur = setting("mailApproval", {}) or {}
            cur.update({k: bool(v) for k, v in (d.get("approval") or {}).items() if k in MAIL_KINDS})
            set_setting("mailApproval", cur)
            return h.send(200, {"ok": True})
        st = self.q("status", "offen")
        where = {"offen": "status IN ('entwurf','freigegeben','fehler')", "gesendet": "status='gesendet'", "alle": "1=1"}.get(st, "status IN ('entwurf','freigegeben','fehler')")
        args = []
        if self.q("ref"):
            where = "ref=?"; args = [self.q("ref")]
        with db() as c:
            rows = [dict(r) for r in c.execute(f"SELECT id, ref, kind, to_addr, subject, body, status, created, send_after, sent_at, note FROM outbox WHERE {where} ORDER BY CASE status WHEN 'entwurf' THEN 0 WHEN 'fehler' THEN 1 ELSE 2 END, COALESCE(NULLIF(send_after,''), created) LIMIT 200", args)]
        for o in rows:
            if o["kind"] == "reservierung" and o["ref"]:
                r, d = load_termin(o["ref"])
                o["anzahlung"] = (d or {}).get("anzahlung")
                o["richtpreis"] = richtpreis(d or {})
                o["paypal"] = paypal_configured()
        return h.send(200, {"items": rows, "kinds": MAIL_KINDS, "approval": {k: approval_needed(k) for k in MAIL_KINDS}, "open": outbox_open()})

    def outbox_item(self, oid, action):
        h, m = self.h, self.m
        with db() as c:
            o = c.execute("SELECT * FROM outbox WHERE id=?", (oid,)).fetchone()
        if not o:
            return h.send(404, {"ok": False, "message": "Nicht gefunden"})
        if o["status"] not in ("entwurf", "freigegeben", "fehler"):
            return h.send(409, {"ok": False, "message": "Diese E-Mail ist bereits erledigt."})
        if m == "PUT" or (m == "POST" and action == "freigeben"):
            d = h.parse()
            subj, body = str(d.get("subject", o["subject"]))[:300], str(d.get("body", o["body"]))[:20000]
            if o["kind"] == "reservierung" and "anzahlung" in d and o["ref"]:  # Anzahlung festlegen oder ändern, Text neu erzeugen
                r, td = load_termin(o["ref"])
                try:
                    amt = round(float(str(d["anzahlung"]).replace(",", ".") or 0), 2)
                except ValueError:
                    return h.send(422, {"ok": False, "message": "Bitte einen Betrag in Euro angeben."})
                if amt < 0 or amt > 10000:
                    return h.send(422, {"ok": False, "message": "Bitte einen Betrag zwischen 0 und 10.000 € angeben."})
                if amt != (td.get("anzahlung") or 0):
                    if amt:
                        td["anzahlung"] = amt
                    else:
                        td.pop("anzahlung", None)
                    save_termin(r["id"], td)
                    audit("anzahlung_geaendert", f"{o['ref']}: {amt} €")
                    subj, body = reservation_text(o["ref"], td)
            with db() as c:
                c.execute("UPDATE outbox SET subject=?, body=?, status=? WHERE id=?",
                          (subj, body, "freigegeben" if action == "freigeben" else o["status"], oid))
            if action == "freigeben":
                audit("mail_freigegeben", f"{o['ref']} {o['kind']}")
                if not o["send_after"] or o["send_after"] <= now().isoformat():
                    ok = deliver(oid)
                    return h.send(200 if ok else 502, {"ok": ok, "message": "E-Mail gesendet." if ok else "Versand fehlgeschlagen, bitte SMTP prüfen.",
                                                         "subject": subj, "body": body})
                return h.send(200, {"ok": True, "message": "Freigegeben, wird zum geplanten Zeitpunkt gesendet.", "subject": subj, "body": body})
            return h.send(200, {"ok": True, "message": "Gespeichert.", "subject": subj, "body": body})
        if m == "POST" and action == "verwerfen":
            with db() as c:
                c.execute("UPDATE outbox SET status='verworfen', note='vom Betrieb verworfen' WHERE id=?", (oid,))
            audit("mail_verworfen", f"{o['ref']} {o['kind']}")
            return h.send(200, {"ok": True, "message": "Verworfen."})
        h.send(405, {"ok": False})

    def google(self):
        h, m = self.h, self.m
        if m == "GET":  # Anmelde-Link zu Google erzeugen
            if not google_configured():
                return h.send(422, {"ok": False, "message": "GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET fehlen in der Server-Konfiguration."})
            ts = str(int(time.time()))
            state = ts + "." + hmac.new(secret_key(), ("google:" + ts).encode(), hashlib.sha256).hexdigest()
            url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
                "client_id": env("GOOGLE_CLIENT_ID"), "redirect_uri": google_redirect(), "response_type": "code", "scope": GOOGLE_SCOPES,
                "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true", "state": state})
            return h.send(200, {"url": url})
        if m == "PUT":
            d = h.parse()
            cal = str(d.get("calendarId", "primary")).strip()[:200] or "primary"
            set_setting("googleCalendarId", cal)
            _GBUSY.clear()
            return h.send(200, {"ok": True})
        if m == "DELETE":
            set_setting("googleRefreshToken", "")
            _GTOKEN.update(token="", exp=0)
            _GBUSY.clear()
            audit("google_getrennt")
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def settings(self):
        h = self.h
        if self.m == "GET":
            return h.send(200, {"zahlungshinweis": setting("zahlungshinweis", ""), "mail": mail_ready(), "notify": Cfg.notify_to or site_info().get("email"),
                                "smtpHost": Cfg.smtp_host, "autoreply": Cfg.autoreply, "retentionDays": Cfg.retention_days,
                                "reviews": {"apiKey": bool(env("GOOGLE_PLACES_API_KEY")), "placeId": site_info().get("googlePlaceId", ""),
                                            "rating": site_info().get("rating", {}), "checked": setting("reviewsChecked", "")}})
        if self.m == "PUT":
            d = h.parse()
            set_setting("zahlungshinweis", str(d.get("zahlungshinweis", ""))[:1500])
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    # Inhalte
    def content_list(self):
        items = []
        labels = {"site.json": "Grunddaten & Kontakt", "pricing.json": "Pakete & Preise", "reviews.json": "Bewertungen",
                  "faq.json": "Häufige Fragen (Startseite)", "gallery.json": "Vorher/Nachher-Galerie",
                  "zertifikate.json": "Zertifikate"}
        for f, l in labels.items():
            items.append({"path": f, "label": l, "group": "Allgemein"})
        for f in sorted(os.listdir(os.path.join(Cfg.content, "services"))):
            if f.endswith(".json"):
                try:
                    l = json.load(open(os.path.join(Cfg.content, "services", f), encoding="utf-8")).get("short", f)
                except Exception:
                    l = f
                items.append({"path": "services/" + f, "label": l, "group": "Leistungsseiten"})
        for f in sorted(os.listdir(os.path.join(Cfg.content, "ratgeber"))):
            if f.endswith(".md"):
                try:
                    meta, _ = mdlib.parse_frontmatter(open(os.path.join(Cfg.content, "ratgeber", f), encoding="utf-8").read())
                    l = meta.get("title", f) + (" (Entwurf)" if meta.get("draft") else "")
                except Exception:
                    l = f
                items.append({"path": "ratgeber/" + f, "label": l, "group": "Ratgeber"})
        return items

    def content_item(self, rel):
        h = self.h
        p = safe_content_path(rel)
        if not p:
            return h.send(400, {"ok": False, "message": "Datei nicht erlaubt"})
        if self.m == "GET":
            if not os.path.exists(p):
                return h.send(404, {"ok": False})
            txt = open(p, encoding="utf-8").read()
            if p.endswith(".md"):
                meta, body = mdlib.parse_frontmatter(txt)
                return h.send(200, {"kind": "md", "meta": meta, "body": body})
            return h.send(200, {"kind": "json", "data": json.loads(txt)})
        if self.m == "PUT":
            d = h.parse(1048576)
            if p.endswith(".md"):
                meta = d.get("meta")
                if not isinstance(meta, dict) or not meta.get("title"):
                    return h.send(422, {"ok": False, "message": "Titel fehlt."})
                txt = mdlib.write_frontmatter(meta, str(d.get("body", "")))
            else:
                data = d.get("data")
                if not isinstance(data, (dict, list)):
                    return h.send(422, {"ok": False, "message": "Ungültige Daten."})
                if os.path.exists(p):
                    old = json.load(open(p, encoding="utf-8"))
                    if type(old) is not type(data):
                        return h.send(422, {"ok": False, "message": "Struktur passt nicht."})
                txt = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            backup(p)
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(txt)
            os.replace(tmp, p)
            audit("inhalt_gespeichert", rel)
            return h.send(200, {"ok": True})
        if self.m == "DELETE" and rel.startswith("ratgeber/"):
            backup(p)
            os.remove(p)
            audit("artikel_geloescht", rel)
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def new_article(self):
        d = self.h.parse()
        title = str(d.get("title", "")).strip()[:90]
        slug = mdlib._slug(d.get("slug") or title)
        p = safe_content_path(f"ratgeber/{slug}.md")
        if not title or not p:
            return self.h.send(422, {"ok": False, "message": "Bitte einen Titel angeben."})
        if os.path.exists(p):
            return self.h.send(409, {"ok": False, "message": "Ein Artikel mit dieser Adresse existiert bereits."})
        meta = {"title": title, "seoTitle": title[:50] + " | ElbDetail", "description": "", "date": today().isoformat(), "updated": today().isoformat(),
                "category": "Ratgeber", "readingTime": 5, "excerpt": "", "service": "", "summary": [], "faq": [], "draft": True}
        body = "Einleitung …\n\n## Erster Abschnitt\n\nText …\n\n## Aufbereitung in Celle anfragen\n\nHier können Sie direkt einen [Termin anfragen](/termin.html).\n"
        with open(p, "w", encoding="utf-8") as f:
            f.write(mdlib.write_frontmatter(meta, body))
        audit("artikel_neu", slug)
        self.h.send(200, {"ok": True, "path": f"ratgeber/{slug}.md"})

    # Angebote (eigener Bereich im Portal; jede Änderung geht sofort live)
    def _offers_out(self, d):
        mins = {p["key"]: min(p.get("prices", {}).values() or [0]) for p in pricing().get("packages", [])}
        fill = lambda t: re.sub(r"\{ab:([a-z]+)\}", lambda m: str(mins.get(m.group(1), m.group(0))), t or "")
        items = [dict(o, state=offer_state(o), priceShown=fill(o.get("price"))) for o in d["items"]]
        return {"items": items, "today": today().isoformat(), "icons": list(OFFER_ICONS)}

    def _offers_publish(self, d, action, detail):
        save_offers(d)
        audit(action, detail)
        r = publish()
        if r.get("ok"):
            set_setting("offersSig", offers_live_signature())
        out = self._offers_out(load_offers())
        out.update(ok=True, published=bool(r.get("ok")), publishLog="" if r.get("ok") else (r.get("log") or "")[-600:])
        return self.h.send(200, out)

    def offers(self):
        d = load_offers()
        if self.m == "GET":
            return self.h.send(200, self._offers_out(d))
        if self.m == "POST":
            o = clean_offer(self.h.parse(65536), self.media_dir())
            o["id"] = secrets.token_hex(4)
            d["items"].insert(0, o)
            return self._offers_publish(d, "angebot_neu", o["title"])
        self.h.send(405, {"ok": False})

    def offer_item(self, oid):
        d = load_offers()
        idx = next((i for i, o in enumerate(d["items"]) if o.get("id") == oid), None)
        if idx is None:
            return self.h.send(404, {"ok": False, "message": "Angebot nicht gefunden."})
        if self.m == "PUT":
            o = clean_offer(self.h.parse(65536), self.media_dir())
            o["id"] = oid
            d["items"][idx] = o
            return self._offers_publish(d, "angebot_geaendert", o["title"])
        if self.m == "DELETE":
            old = d["items"].pop(idx)
            return self._offers_publish(d, "angebot_geloescht", old.get("title", ""))
        self.h.send(405, {"ok": False})

    def offers_order(self):
        d = load_offers()
        ids = [str(x) for x in (self.h.parse(8192).get("ids") or [])]
        pos = {x: i for i, x in enumerate(ids)}
        d["items"].sort(key=lambda o: pos.get(o["id"], len(pos)))
        return self._offers_publish(d, "angebote_sortiert", ", ".join(ids)[:200])

    # Medien
    def media_dir(self):
        p = os.path.join(Cfg.content, "media")
        os.makedirs(p, exist_ok=True)
        return p

    def media_list(self):
        out = []
        for f in sorted(os.listdir(self.media_dir())):
            if MEDIA_RE.match(f):
                st = os.stat(os.path.join(self.media_dir(), f))
                out.append({"name": f, "size": st.st_size, "modified": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
        return out

    def media_upload(self):
        d = self.h.parse(22 * 1024 * 1024)
        name = re.sub(r"[^a-z0-9.\-]+", "-", str(d.get("name", "")).lower()).strip("-")
        name = re.sub(r"\.jpeg$", ".jpg", name)
        if not MEDIA_RE.match(name):
            return self.h.send(422, {"ok": False, "message": "Erlaubt sind JPG, PNG oder WebP mit einfachem Dateinamen."})
        m = re.match(r"^data:image/(jpeg|png|webp);base64,(.+)$", str(d.get("data", "")), re.S)
        if not m:
            return self.h.send(422, {"ok": False, "message": "Ungültige Bilddatei."})
        raw = base64.b64decode(m.group(2))
        if len(raw) > 15 * 1024 * 1024:
            return self.h.send(413, {"ok": False, "message": "Datei größer als 15 MB."})
        if not (raw[:3] == b"\xff\xd8\xff" or raw[:8] == b"\x89PNG\r\n\x1a\n" or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")):
            return self.h.send(422, {"ok": False, "message": "Datei ist kein gültiges Bild."})
        with open(os.path.join(self.media_dir(), name), "wb") as f:
            f.write(raw)
        audit("bild_hochgeladen", name)
        self.h.send(200, {"ok": True, "name": name})

    def media_item(self, name):
        if not MEDIA_RE.match(name):
            return self.h.send(400, {"ok": False})
        p = os.path.join(self.media_dir(), name)
        if not os.path.exists(p):
            return self.h.send(404, {"ok": False})
        if self.m == "GET":
            return self.h.send(200, open(p, "rb").read(), mimetypes.guess_type(p)[0] or "application/octet-stream")
        if self.m == "DELETE":
            os.remove(p)
            audit("bild_geloescht", name)
            return self.h.send(200, {"ok": True})
        self.h.send(405, {"ok": False})


# --------------------------------------------------------------------------- Start
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "health":  # für den Docker-Healthcheck, ohne Datenbankzugriff
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{Cfg.port}/api/health", timeout=4) as r:
                sys.exit(0 if r.status == 200 else 1)
        except Exception:
            sys.exit(1)
    if len(sys.argv) > 1 and sys.argv[1] == "alarm":  # vom Wächter-Skript: Warnung per E-Mail an NOTIFY_TO
        text = " ".join(sys.argv[2:]) or "Unbekannte Störung"
        to = Cfg.notify_to or site_info().get("email")
        ok = send_mail(to, "ElbDetail-Server: " + text[:80], text + "\n\nGesendet vom Wächter auf dem Server (deploy/watchdog.sh).")
        print("gesendet" if ok else "nicht gesendet (SMTP prüfen)")
        sys.exit(0 if ok else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "passwort":
        pw = getpass.getpass("Neues Passwort: ")
        if len(pw) < 12:
            print("Bitte mindestens 12 Zeichen verwenden.")
            sys.exit(1)
        if pw != getpass.getpass("Wiederholen: "):
            print("Passwörter stimmen nicht überein.")
            sys.exit(1)
        print("\nIn die Datei deploy/.env eintragen:\nADMIN_PASSWORD_HASH=" + hash_password(pw))
        return
    os.makedirs(Cfg.site_root, exist_ok=True)
    seed_content()
    init_db()
    if len(sys.argv) > 1 and sys.argv[1] == "backup":
        print(make_backup())
        return
    if len(sys.argv) > 1 and sys.argv[1] == "inhalte-ergaenzen":
        added = merge_seed()
        print("Neu übernommen:", ", ".join(added) if added else "nichts")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        r = publish()
        print(r.get("log", ""))
        sys.exit(0 if r.get("ok") else 1)
    if not os.path.exists(os.path.join(site_dir(), "index.html")):
        log("Erster Start: Website wird gebaut …")
        r = publish()
        log("Build", "ok" if r.get("ok") else "FEHLER\n" + r.get("log", ""))
    if not (Cfg.admin_hash or Cfg.admin_plain):
        log("WARNUNG: Kein Admin-Passwort gesetzt (ADMIN_PASSWORD_HASH). Das Verwaltungsportal ist gesperrt.")
    if not mail_ready():
        log("Hinweis: SMTP nicht eingerichtet, E-Mail-Benachrichtigungen sind aus.")
    threading.Thread(target=housekeeping, daemon=True).start()
    threading.Thread(target=offers_watcher, daemon=True).start()
    threading.Thread(target=booking_watcher, daemon=True).start()
    threading.Thread(target=reviews_watcher, daemon=True).start()
    class Server(ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            et = sys.exc_info()[0]
            if et and issubclass(et, (BrokenPipeError, ConnectionResetError, TimeoutError)):
                return
            log("Verbindungsfehler:", sys.exc_info()[1])
    srv = Server((Cfg.host, Cfg.port), Handler)
    srv.daemon_threads = True
    log(f"ElbDetail-Server läuft auf http://{Cfg.host}:{Cfg.port} (statische Dateien: {'ja' if Cfg.serve_static else 'nein, über Caddy'})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
