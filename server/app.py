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
import urllib.parse
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
STATUS = ["neu", "in_bearbeitung", "angebot_gesendet", "termin_bestaetigt", "erledigt", "abgelehnt"]
V_STATUS = ["offen", "bezahlt", "eingeloest", "storniert"]
TYPES = ["kontakt", "termin", "gutschein", "firma"]
LOCK = threading.Lock()
BUILD_LOCK = threading.Lock()


def now():
    return dt.datetime.now().replace(microsecond=0)


def today():
    return dt.date.today()


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


def send_mail(to, subject, text, reply_to=None):
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
          "zeitfenster": "Zeitfenster", "gutscheincode": "Gutscheincode", "kanal": "Antwort per", "nachricht": "Nachricht",
          "bewertung_ok": "Bewertungsanfrage erlaubt", "art": "Gutscheinart", "wert": "Wert", "fuer": "Für", "von": "Von", "widmung": "Widmung",
          "zustellung": "Zustellung", "firma": "Firma", "anzahl": "Fahrzeuge", "intervall": "Intervall", "leistungen": "Leistungen", "quelle": "Quelle"}


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
    out["email"] = _s(d, "email", 160, typ in ("gutschein", "firma"), errors)
    if out["email"] and not EMAIL_RE.match(out["email"]):
        errors["email"] = "Bitte eine gültige E-Mail-Adresse angeben."
    if out["telefon"] and not re.match(r"^[0-9+()/ \-.]{5,40}$", out["telefon"]):
        errors["telefon"] = "Bitte eine gültige Telefonnummer angeben."
    out["nachricht"] = _s(d, "nachricht", 2000, False, errors)
    if d.get("einwilligung") not in ("ja", "on", True, "true"):
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
        if out["paket"] and out["paket"] not in pkeys + ["beratung"]:
            errors["paket"] = "Bitte ein Paket wählen."
        out["klasse"] = _s(d, "klasse", 20, True, errors)
        if out["klasse"] and out["klasse"] not in ckeys:
            errors["klasse"] = "Bitte eine Fahrzeugklasse wählen."
        out["fahrzeug"] = _s(d, "fahrzeug", 120, False, errors)
        out["zustand"] = _list(d, "zustand", ["tierhaare", "stark", "geruch", "leder", "flecken", "kratzer"])
        out["extras"] = _list(d, "extras", pr.get("extras"))
        out["abholung"] = d.get("abholung") if d.get("abholung") in ("nein", "anfrage") else "nein"
        out["zeitfenster"] = d.get("zeitfenster") if d.get("zeitfenster") in ("morgens", "vormittag", "nachmittag", "flexibel") else "flexibel"
        out["kanal"] = d.get("kanal") if d.get("kanal") in ("whatsapp", "anruf", "email") else "whatsapp"
        out["gutscheincode"] = _s(d, "gutscheincode", 20, False, errors).upper()
        out["bewertung_ok"] = "ja" if d.get("bewertung_ok") in ("ja", "on", True) else "nein"
        out["quelle"] = _s(d, "quelle", 40, False, errors)
        closed = setting("closedWeekdays", [0])
        blocked = blocked_days()
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
    names["beratung"] = "Beratung / Einzelleistung"
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
        if isinstance(v, list):
            v = ", ".join(v)
        lines.append(f"{LABELS.get(k, k)}: {v}")
    return "\n".join(lines)


def richtpreis(data):
    try:
        p = next(x for x in pricing()["packages"] if x["key"] == data.get("paket"))
        return p["prices"].get(data.get("klasse"))
    except StopIteration:
        return None


# --------------------------------------------------------------------------- Anfragen speichern
TITLES = {"kontakt": "Anfrage", "termin": "Terminanfrage", "gutschein": "Gutscheinbestellung", "firma": "Firmenanfrage"}


def new_ref(typ):
    return {"kontakt": "K", "termin": "T", "gutschein": "G", "firma": "F"}[typ] + now().strftime("%y%m%d") + "-" + secrets.token_hex(2).upper()


def store_request(data):
    ref = new_ref(data["typ"])
    ts = now().isoformat()
    with LOCK, db() as c:
        cur = c.execute("INSERT INTO anfragen(ref, typ, status, created, updated, name, telefon, email, datum, data) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (ref, data["typ"], "neu", ts, ts, data.get("name"), data.get("telefon"), data.get("email"), data.get("datum", ""),
                         json.dumps(data, ensure_ascii=False)))
        aid = cur.lastrowid
        if data["typ"] == "gutschein":
            create_voucher(c, data, aid)
    notify(ref, data)
    return ref


def notify(ref, data):
    s = site_info()
    title = TITLES[data["typ"]]
    rp = richtpreis(data)
    body = f"Neue {title} über die Website ({ref})\n\n{summary_text(data)}\n"
    if rp:
        body += f"\nRichtpreis laut Website: ab {rp} €\n"
    body += f"\nIm Verwaltungsportal öffnen: {Cfg.public_url}/admin/#/anfragen/{ref}\n"
    mail_async(Cfg.notify_to or s.get("email"), f"{title}: {data.get('name')} ({ref})", body, reply_to=data.get("email") or None)
    if Cfg.autoreply and data.get("email"):
        greet = f"Hallo {data.get('name', '').split(' ')[0]},".strip()
        extra = ""
        if data["typ"] == "termin":
            extra = "Wir prüfen deinen Wunschtermin und melden uns mit einer Bestätigung und einem verbindlichen Angebot.\n"
        elif data["typ"] == "gutschein":
            pay = setting("zahlungshinweis", "") or "Die Zahlungsdaten senden wir dir in Kürze."
            extra = f"Vielen Dank für deine Gutscheinbestellung über {data.get('wert')} €.\n\n{pay}\n\nNach Zahlungseingang erhältst du den Gutschein als Link zum Ausdrucken.\n"
        else:
            extra = "Wir melden uns so schnell wie möglich bei dir.\n"
        text = (f"{greet}\n\ndanke für deine {title} bei {s.get('name', 'ElbDetail')}. {extra}\nDeine Angaben ({ref}):\n{summary_text(data)}\n\n"
                f"Fragen? Antworte einfach auf diese E-Mail oder schreib per WhatsApp: {s.get('phoneIntl', '')}\n\n"
                f"Viele Grüße\n{s.get('name', 'ElbDetail')}\n{s.get('address', {}).get('street', '')}, {s.get('address', {}).get('zip', '')} {s.get('address', {}).get('city', '')}\n{Cfg.public_url}\n")
        mail_async(data["email"], f"Deine {title} bei {s.get('name', 'ElbDetail')} ({ref})", text, reply_to=s.get("email") or None)


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
    desc = "Fahrzeugaufbereitung für die Kompaktklasse" if v["art"] == "paket" else "für eine Fahrzeugaufbereitung nach Wahl"
    valid = dt.date.fromisoformat(v["valid_until"]).strftime("%d.%m.%Y")
    state = {"offen": "Noch nicht bezahlt – wird nach Zahlungseingang gültig.", "storniert": "Dieser Gutschein wurde storniert.",
             "eingeloest": "Dieser Gutschein wurde bereits eingelöst."}.get(v["status"], "")
    E = html.escape
    a = s.get("address", {})
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Gutschein {E(v['code'])} | {E(s.get('name', 'ElbDetail'))}</title>
<style>
@font-face{{font-family:Oswald;font-weight:700;src:url(/fonts/oswald-700.woff2) format("woff2")}}
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;padding:24px 16px;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#eef3fb;color:#171c24}}
.wrap{{max-width:820px;margin:0 auto;display:grid;gap:16px}}
.card{{position:relative;overflow:hidden;border-radius:20px;padding:32px;color:#f4f6f9;background:radial-gradient(circle at 85% 15%,rgba(91,155,232,.45),transparent 45%),linear-gradient(140deg,#262c36,#15181d);display:grid;gap:10px;min-height:420px}}
.top{{display:flex;justify-content:space-between;align-items:center}}.top img{{height:46px}}.top span{{font-family:Oswald,Arial Narrow,sans-serif;letter-spacing:.3em;text-transform:uppercase;color:#5b9be8}}
.val{{font-family:Oswald,Arial Narrow,sans-serif;font-size:64px;line-height:1;margin-top:28px}}.desc{{color:#9ea6b3}}
.names{{display:flex;gap:28px;flex-wrap:wrap;color:#9ea6b3}}.names b{{color:#fff}}.msg{{font-style:italic;font-size:17px;min-height:1.4em}}
.foot{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.15);padding-top:12px;font-size:13px;color:#c7cdd6}}
.code{{font:700 18px/1 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.08em;color:#fff}}
.state{{background:#fff3cd;border:1px solid #f1d9a0;color:#4d3a0f;padding:12px 16px;border-radius:12px;font-weight:600}}
.how{{background:#fff;border-radius:16px;padding:20px 22px;border:1px solid #d3ddee}}.how h2{{margin:0 0 8px;font-family:Oswald,Arial Narrow,sans-serif}}
.btn{{display:inline-block;background:#1c4f9c;color:#fff;border:0;border-radius:999px;padding:12px 22px;font:inherit;font-weight:800;cursor:pointer;text-decoration:none}}
@media print{{body{{background:#fff;padding:0}}.noprint{{display:none!important}}.card{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body><div class="wrap">
{f'<p class="state">{E(state)}</p>' if state else ''}
<div class="card"><div class="top"><img src="/logo.png" alt="{E(s.get('name', 'ElbDetail'))}"><span>Gutschein</span></div>
<div class="val">{value}</div><div class="desc">{desc}</div>
<div class="names">{f'<span>Für <b>{E(v["fuer"])}</b></span>' if v['fuer'] else ''}{f'<span>Von <b>{E(v["von"])}</b></span>' if v['von'] else ''}</div>
<p class="msg">{E(v['widmung'] or '')}</p>
<div class="foot"><span>Code <span class="code">{E(v['code'])}</span></span><span>Gültig bis {valid}</span><span>{E(s.get('name', ''))} · {E(a.get('street', ''))}, {E(a.get('zip', ''))} {E(a.get('city', ''))}</span></div></div>
<div class="how"><h2>So wird der Gutschein eingelöst</h2><p>Termin über <b>{E(Cfg.public_url.split('//')[-1])}/termin.html</b> anfragen und den Code im Feld „Gutscheincode“ eintragen, oder per WhatsApp an {E(s.get('phoneIntl', ''))} mit dem Code schreiben. Paketgutscheine gelten für die Kompaktklasse; bei größeren Fahrzeugen wird nur die Differenz fällig.</p></div>
<p class="noprint"><button class="btn" id="printBtn" type="button">Drucken oder als PDF speichern</button></p>
</div><script src="/gutschein-druck.js"></script></body></html>"""


# --------------------------------------------------------------------------- Kalender
def blocked_days():
    with db() as c:
        return [r["day"] for r in c.execute("SELECT day FROM blocked WHERE day >= ? ORDER BY day", (today().isoformat(),))]


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
        out["upcoming"] = q("SELECT ref, name, datum, data FROM anfragen WHERE typ='termin' AND datum >= ? AND status NOT IN ('abgelehnt') ORDER BY datum LIMIT 8", e0)
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
                n1 = c.execute("DELETE FROM anfragen WHERE updated < ? AND status IN ('neu','in_bearbeitung','angebot_gesendet','abgelehnt') "
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


EDITABLE = re.compile(r"^(site|pricing|reviews|faq|gallery)\.json$|^services/[a-z0-9-]{2,80}\.json$|^ratgeber/[a-z0-9-]{2,80}\.md$")
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

    def send(self, code, body=b"", ctype="application/json; charset=utf-8", headers=None):
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
            return self.send(200, {"blocked": blocked_days(), "closedWeekdays": setting("closedWeekdays", [0])})
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
            ref = store_request(data)
            if is_form:
                return self.send(303, b"", "text/plain", {"Location": f"/danke.html?typ={data['typ']}&ref={ref}"})
            return self.send(200, {"ok": True, "ref": ref})
        self.send(404, {"ok": False})

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
        user = self.user()
        if not user:
            return self.send(401, {"ok": False, "message": "Bitte anmelden."})
        return AdminAPI(self, method, path, qs).run()


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
                                "lastPublish": setting("lastPublish"), "open": self._open()})
        if p == "stats":
            return h.send(200, stats(self.q("days", "30")))
        if p == "anfragen" and m == "GET":
            return h.send(200, self.list_requests())
        if p == "anfragen.csv":
            return self.csv_export()
        mm = re.match(r"^anfragen/([A-Z]\d{6}-[0-9A-F]{4}|\d+)$", p)
        if mm:
            return self.request_item(mm.group(1))
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
        if p == "medien" and m == "GET":
            return h.send(200, self.media_list())
        if p == "medien" and m == "POST":
            return self.media_upload()
        mm = re.match(r"^medien/(.+)$", p)
        if mm:
            return self.media_item(mm.group(1))
        if p == "veroeffentlichen" and m == "POST":
            return h.send(200, publish())
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
                c.execute("UPDATE anfragen SET status=?, notizen=?, updated=? WHERE id=?", (st, notes, now().isoformat(), r["id"]))
                audit("anfrage_status", f"{r['ref']} → {st}", c)
                return h.send(200, {"ok": True})
            if m == "DELETE":
                c.execute("UPDATE gutscheine SET anfrage_id=NULL WHERE anfrage_id=?", (r["id"],))
                c.execute("DELETE FROM anfragen WHERE id=?", (r["id"],))
                audit("anfrage_geloescht", r["ref"], c)
                return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def template(self, ref, art):
        s = site_info()
        with db() as c:
            r = c.execute("SELECT * FROM anfragen WHERE ref=?", (ref,)).fetchone()
            if not r:
                return self.h.send(404, {"ok": False})
            d = json.loads(r["data"] or "{}")
            parts = (r["name"] or "").split()
            first = parts[0] if parts and r["typ"] != "firma" and not parts[0].endswith(".") else (r["name"] or "")
            if art == "bewertung":
                link = s.get("googleReviewUrl") or "[GOOGLE-BEWERTUNGSLINK]"
                text = (f"Hallo {first}, danke, dass wir dein Auto aufbereiten durften! Wenn du zufrieden warst, würden wir uns sehr über eine kurze "
                        f"Google-Bewertung freuen. Das dauert nur eine Minute: {link}\nViele Grüße, {s.get('name', 'ElbDetail')}")
                c.execute("UPDATE anfragen SET bewertung_angefragt=? WHERE id=?", (now().isoformat(), r["id"]))
                warn = "" if d.get("bewertung_ok") == "ja" else "Achtung: Für diese Anfrage liegt keine Einwilligung zur Bewertungsanfrage vor. Bitte nur nach persönlicher Zustimmung senden."
            else:
                pr = pricing()
                pname = next((p["name"] for p in pr.get("packages", []) if p["key"] == d.get("paket")), d.get("paket", ""))
                date = _date(d.get("datum", ""))
                rp = richtpreis(d)
                text = f"Hallo {first}, danke für deine Anfrage bei {s.get('name', 'ElbDetail')}!"
                if date:
                    text += f" Dein Wunschtermin am {date.strftime('%d.%m.%Y')} passt [ODER: Wir können dir den … anbieten]."
                if pname:
                    text += f" Für {pname}" + (f" liegt der Richtpreis bei ab {rp} €" if rp else "") + ". Der verbindliche Preis für dein Fahrzeug: [PREIS] €."
                text += " Passt das für dich? Viele Grüße"
                warn = ""
            tel = wa_number(r["telefon"])
            return self.h.send(200, {"text": text, "whatsapp": f"https://wa.me/{tel}?text={urllib.parse.quote(text)}" if tel else "", "warning": warn,
                                     "mailto": f"mailto:{r['email']}?subject={urllib.parse.quote('Deine Anfrage bei ' + s.get('name', 'ElbDetail'))}&body={urllib.parse.quote(text)}" if r["email"] else ""})

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
                    text = (f"Hallo {(v['kaeufer'] or '').split(' ')[0]},\n\nvielen Dank, deine Zahlung ist eingegangen. Hier ist dein Gutschein zum Ausdrucken oder Weiterleiten:\n\n"
                            f"{voucher_link(vv)}\n\nCode: {v['code']}\nGültig bis {dt.date.fromisoformat(v['valid_until']).strftime('%d.%m.%Y')}\n\n"
                            f"Viel Freude beim Verschenken!\n{s.get('name', 'ElbDetail')}\n")
                    mail_async(v["email"], f"Dein Gutschein von {s.get('name', 'ElbDetail')}", text, reply_to=s.get("email"))
                    sent = mail_ready()
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
            return h.send(200, {"blocked": bl, "requests": req, "closedWeekdays": setting("closedWeekdays", [0])})
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
            wd = [int(x) for x in d.get("closedWeekdays", []) if str(x).isdigit() and 0 <= int(x) <= 6]
            set_setting("closedWeekdays", wd)
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    def settings(self):
        h = self.h
        if self.m == "GET":
            return h.send(200, {"zahlungshinweis": setting("zahlungshinweis", ""), "mail": mail_ready(), "notify": Cfg.notify_to or site_info().get("email"),
                                "smtpHost": Cfg.smtp_host, "autoreply": Cfg.autoreply, "retentionDays": Cfg.retention_days})
        if self.m == "PUT":
            d = h.parse()
            set_setting("zahlungshinweis", str(d.get("zahlungshinweis", ""))[:1500])
            return h.send(200, {"ok": True})
        h.send(405, {"ok": False})

    # Inhalte
    def content_list(self):
        items = []
        labels = {"site.json": "Grunddaten & Kontakt", "pricing.json": "Pakete & Preise", "reviews.json": "Bewertungen",
                  "faq.json": "Häufige Fragen (Startseite)", "gallery.json": "Vorher/Nachher-Galerie"}
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
        body = "Einleitung …\n\n## Erster Abschnitt\n\nText …\n\n## Aufbereitung in Celle anfragen\n\nHier kannst du direkt einen [Termin anfragen](/termin.html).\n"
        with open(p, "w", encoding="utf-8") as f:
            f.write(mdlib.write_frontmatter(meta, body))
        audit("artikel_neu", slug)
        self.h.send(200, {"ok": True, "path": f"ratgeber/{slug}.md"})

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
