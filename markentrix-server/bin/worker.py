#!/usr/bin/env python3
"""Führt Aufträge aus dem Portal aus (Website/Demo in den Papierkorb, Wiederherstellen).
Läuft jede Minute als root per cron. Prüft jeden Auftrag streng, das Portal bleibt ohne Root-Rechte."""
import json, os, re, shlex, shutil, subprocess, time
from pathlib import Path

BASE = Path(os.environ.get("MK_BASE", "/opt/markentrix"))
SITES = Path(os.environ.get("MK_SITES", "/srv/sites"))
QUEUE = BASE / "queue"
BACKUPS = Path(os.environ.get("MK_BACKUPS", str(BASE / "backups")))
PSQL = shlex.split(os.environ.get("MK_PSQL", "docker exec -i mk-db psql -U markentrix"))
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
# Diese Tabellen kommen nie in einen Kundenauszug (Zugangsdaten, Protokolle, Massendaten)
AUSZUG_NICHT = {"benutzer", "audit_log", "mail_protokoll", "website_stat", "website_wacht", "website_ereignisse", "login_versuche", "sitzungen", "push_abos", "loeschprotokoll"}
TAG = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")
TRASH = SITES / ".papierkorb"
KEEP_DAYS = 14
NAME = {"live": re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$"), "demo": re.compile(r"^[a-z0-9]([a-z0-9-]{0,40}[a-z0-9])?$")}
TRASH_ID = re.compile(r"^\d{8}-\d{6}__(live|demo)__[A-Za-z0-9.-]{1,253}$")
REQ = re.compile(r"^auftrag-[0-9a-f]{12,32}\.json$")


def log(m):
    print(time.strftime("%F %T"), m, flush=True)


CONTAINER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,100}$")


def caddy_sites():
    """Ordner, aus dem der Caddy die Domain-Dateien liest. Bei einem vorhandenen Caddy ist das dessen Ordner (bei der Installation erkannt),
    sonst der eigene unter /opt/markentrix/caddy/sites."""
    try:
        p = Path((BASE / "caddy-sites-dir").read_text().strip())
        if p.is_absolute() and p.is_dir() and not p.is_symlink():
            return p
    except OSError:
        pass
    return BASE / "caddy" / "sites"


def reload_caddy() -> bool:
    """Lädt die Konfiguration des Webservers neu (ändert nichts an ihr). True bei Erfolg."""
    mode = (BASE / "mode").read_text().strip() if (BASE / "mode").exists() else "own"
    try:
        if mode == "own":
            cmd = ["docker", "compose", "--project-directory", str(BASE), "-f", str(BASE / "docker-compose.yml"),
                   "exec", "-T", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"]
        elif mode == "docker":
            c = (BASE / "caddy-container").read_text().strip() if (BASE / "caddy-container").exists() else ""
            if not CONTAINER.match(c):
                log("Caddy-Container nicht bekannt (Datei caddy-container fehlt): bitte install.sh erneut ausführen")
                return False
            cmd = ["docker", "exec", c, "caddy", "reload", "--config", "/etc/caddy/Caddyfile"]
        elif mode == "host":
            cmd = ["systemctl", "reload", "caddy"]
        else:
            return False
        r = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log(f"Caddy konnte nicht neu geladen werden: {(r.stderr or r.stdout)[-200:]}")
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"Caddy konnte nicht neu geladen werden: {e}")
        return False


def loeschen(art, name):
    quelle = SITES / ("live" if art == "live" else "demos") / name
    if quelle.is_symlink() or not quelle.is_dir():
        raise RuntimeError("Ordner nicht vorhanden")
    TRASH.mkdir(mode=0o755, exist_ok=True)
    ziel = TRASH / f"{time.strftime('%Y%m%d-%H%M%S')}__{art}__{name}"
    shutil.move(str(quelle), str(ziel))
    cf = caddy_sites() / f"{name}.caddy"
    if art == "live" and cf.is_file():
        cf.rename(ziel / "_caddy-datei.bak")
        reload_caddy()
    log(f"in Papierkorb: {art} {name}")


def wiederherstellen(tid):
    if not TRASH_ID.match(tid):
        raise RuntimeError("ungültige Papierkorb-ID")
    quelle = TRASH / tid
    if quelle.is_symlink() or not quelle.is_dir():
        raise RuntimeError("Eintrag nicht vorhanden")
    art, name = tid.split("__")[1:3]
    ziel = SITES / ("live" if art == "live" else "demos") / name
    if ziel.exists():
        raise RuntimeError("Es gibt schon eine Seite mit diesem Namen")
    shutil.move(str(quelle), str(ziel))
    bak = ziel / "_caddy-datei.bak"
    if bak.is_file():
        shutil.move(str(bak), str(caddy_sites() / f"{name}.caddy"))
        reload_caddy()
    if art == "live":
        subprocess.run(["chown", "-R", "10001:10001", str(ziel / "angebote")], check=False, capture_output=True)
    log(f"wiederhergestellt: {art} {name}")


def papierkorb_loeschen(a):
    """Löscht einen oder alle Papierkorb-Einträge endgültig (nur Ordner mit gültiger ID, keine Symlinks)."""
    ids = [p.name for p in TRASH.iterdir()] if a.get("alle") and TRASH.is_dir() else [str(a.get("id", ""))]
    for tid in ids:
        if not TRASH_ID.match(tid):
            continue
        q = TRASH / tid
        if q.is_symlink() or not q.is_dir():
            continue
        shutil.rmtree(q, ignore_errors=True)
        log(f"Papierkorb endgültig gelöscht: {tid}")


UPLOAD = re.compile(r"^[0-9a-f]{16}$")
VORVERSION = SITES / ".vorversionen"
VOR_BEHALTEN = 3
VOR_TAGE = 30


def ergebnis(uid, a, ok, text, **extra):
    """Rückmeldung für das Portal (Admin → Verwaltung → Website hochladen). Lesbar für den Portal-Benutzer 10001."""
    try:
        p = QUEUE / f"ergebnis-{uid}.json"
        p.write_text(json.dumps({"id": uid, "aktion": a.get("aktion"), "art": a.get("art"), "name": a.get("name"), "ok": ok, "text": text,
                                 "zeit": time.strftime("%Y-%m-%dT%H:%M:%S"), **extra}))
        os.chown(p, 10001, 10001)
        p.chmod(0o640)
    except OSError as e:
        log(f"Ergebnis nicht schreibbar: {e}")


def baum_pruefen(wurzel):
    """Nur normale Dateien und Ordner: ein Symlink oder Sonderfile im Upload bricht ab (das Portal ist nicht vertrauenswürdig genug für Root-Aktionen)."""
    for root, dirs, files in os.walk(wurzel):
        for n in dirs + files:
            pf = Path(root) / n
            if pf.is_symlink() or not (pf.is_dir() or pf.is_file()):
                raise RuntimeError("Unzulässige Datei im Upload")


def ziel_ordner(art, name):
    return SITES / ("live" if art == "live" else "demos") / name


def uebernehmen(alt, neu):
    """Daten, die das Portal selbst pflegt, wandern in die neue Version: Wochenangebote und die Kennung der Seite."""
    if (alt / "angebote").is_dir() and not (neu / "angebote").exists():
        shutil.move(str(alt / "angebote"), str(neu / "angebote"))
    if (alt / "site.json").is_file():
        (neu / "site.json").unlink(missing_ok=True)
        shutil.move(str(alt / "site.json"), str(neu / "site.json"))


def vorname(art, name):
    """Eindeutiger Sicherungsname, auch wenn mehrere Wechsel in derselben Sekunde passieren."""
    return VORVERSION / f"{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1000000:06d}__{art}__{name}"


def portal_upstream():
    mode = (BASE / "mode").read_text().strip() if (BASE / "mode").exists() else "own"
    return "127.0.0.1:8090" if mode == "host" else "mk-portal:8000"


def caddy_inhalt(domain):
    """Statische Website plus die Website-API: /api/* der Kundendomain geht an das Portal (Pfad wird zu /siteapi/api/…, die Domain im Host bleibt erhalten).
    Nur diese Pfade werden weitergeleitet, die übrige Portal-Schnittstelle ist über die Kundendomain nicht erreichbar."""
    return (f"{domain}, www.{domain} {{\n\tencode zstd gzip\n"
            f"\thandle /api/* {{\n\t\trewrite * /siteapi{{uri}}\n\t\treverse_proxy {portal_upstream()}\n\t}}\n"
            f"\thandle {{\n\t\troot * /srv/sites/live/{domain}\n\t\tfile_server\n\t}}\n}}\n")


def alt_inhalt(domain):
    return f"{domain}, www.{domain} {{\n\tencode zstd gzip\n\troot * /srv/sites/live/{domain}\n\tfile_server\n}}\n"


def caddy_datei(domain):
    cf = caddy_sites() / f"{domain}.caddy"
    if cf.exists():
        return False
    cf.parent.mkdir(parents=True, exist_ok=True)
    cf.write_text(caddy_inhalt(domain))
    return True


def caddy_nachruesten():
    """Ältere, unveränderte Standard-Einträge bekommen die Website-API-Weiterleitung. Von Hand geänderte Dateien bleiben unangetastet."""
    ordner = caddy_sites()
    geaendert = False
    if not ordner.is_dir():
        return
    for cf in ordner.glob("*.caddy"):
        domain = cf.name[:-6]
        if not NAME["live"].match(domain) or cf.is_symlink():
            continue
        try:
            if cf.read_text() == alt_inhalt(domain):
                cf.write_text(caddy_inhalt(domain))
                geaendert = True
        except OSError:
            continue
    if geaendert:
        reload_caddy()
        log("Website-API-Weiterleitung in bestehende Caddy-Einträge eingefügt")


def vorversionen_aufraeumen(art, name):
    if not VORVERSION.is_dir():
        return
    alle = sorted([d for d in VORVERSION.iterdir() if d.is_dir() and not d.is_symlink() and d.name.endswith(f"__{art}__{name}")], reverse=True)
    for i, d in enumerate(alle):
        if i >= VOR_BEHALTEN or d.stat().st_mtime < time.time() - VOR_TAGE * 86400:
            shutil.rmtree(d, ignore_errors=True)


def veroeffentlichen(a):
    art, name, uid = a.get("art"), str(a.get("name", "")), str(a.get("upload", ""))
    if art not in NAME or not NAME[art].match(name) or not UPLOAD.match(uid):
        raise RuntimeError("ungültiger Auftrag")
    stage = SITES / "live" / f".upload-{uid}"
    try:
        if stage.is_symlink() or not stage.is_dir():
            raise RuntimeError("Der Upload ist nicht mehr vorhanden")
        baum_pruefen(stage)
        if not (stage / "index.html").is_file():
            raise RuntimeError("index.html fehlt")
        subprocess.run(["chown", "-R", "-h", "root:root", str(stage)], check=True, capture_output=True)
        subprocess.run(["chmod", "-R", "u-s,g-s,go-w,a+rX", str(stage)], check=True, capture_output=True)
        ziel = ziel_ordner(art, name)
        neu = not ziel.exists()
        if ziel.is_symlink() or (ziel.exists() and not ziel.is_dir()):
            raise RuntimeError("Zielordner ist ungültig")
        if neu:
            (stage / "site.json").write_text(json.dumps({"typ": art, "name": name, "kunde": str(a.get("kunde", "")), "angelegt": time.strftime("%F")}, indent=2))
            if art == "live":
                (stage / "angebote" / "archiv").mkdir(parents=True, exist_ok=True)
        else:
            uebernehmen(ziel, stage)
            VORVERSION.mkdir(mode=0o755, exist_ok=True)
            os.rename(ziel, vorname(art, name))
        if art == "live":
            subprocess.run(["chown", "-R", "-h", "10001:10001", str(stage / "angebote")], check=False, capture_output=True)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        os.rename(stage, ziel)
        angelegt, reload_ok = False, True
        if art == "live":
            angelegt = caddy_datei(name)
            if angelegt:
                reload_ok = reload_caddy()
        vorversionen_aufraeumen(art, name)
        url = f"https://{name}/" if art == "live" else f"https://demo.{os.environ.get('MK_DOMAIN', 'markentrix.de')}/{name}/"
        text = ("Website neu angelegt und veröffentlicht. Damit sie erreichbar ist, muss die Domain per A-Eintrag (auch www) auf diesen Server zeigen, das HTTPS-Zertifikat kommt dann automatisch."
                if neu and art == "live" else "Veröffentlicht. Die vorige Version ist gesichert und lässt sich zurückholen.")
        if not reload_ok:
            text += " ACHTUNG: Der Webserver (Caddy) konnte nicht neu geladen werden. Auf dem Server „mkctl caddy-neu“ ausführen."
        ergebnis(uid, a, True, text, url=url, neu=neu)
        log(f"veröffentlicht: {art} {name}")
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(stage, ignore_errors=True)
        ergebnis(uid if UPLOAD.match(uid) else "0" * 16, a, False, f"Fehlgeschlagen: {e}")
        raise


def sicherung_tage():
    if not BACKUPS.is_dir():
        return []
    return sorted([d.name for d in BACKUPS.iterdir() if TAG.match(d.name) and d.is_dir() and not d.is_symlink() and (d / "sites.tar.gz").is_file()], reverse=True)[:30]


def db_tage():
    if not BACKUPS.is_dir():
        return []
    return sorted([d.name for d in BACKUPS.iterdir() if TAG.match(d.name) and d.is_dir() and not d.is_symlink() and (d / "markentrix-db.sql.gz").is_file()], reverse=True)[:30]


def aus_sicherung(a):
    """Holt eine Website aus der Tagessicherung. Die jetzige Version bleibt wie bei jeder Veröffentlichung als Vorversion erhalten."""
    art, name, tag, uid = a.get("art"), str(a.get("name", "")), str(a.get("tag", "")), str(a.get("upload", ""))
    if art not in NAME or not NAME[art].match(name) or not TAG.match(tag) or not UPLOAD.match(uid):
        raise RuntimeError("ungültiger Auftrag")
    archiv = BACKUPS / tag / "sites.tar.gz"
    tmp = SITES / "live" / f".sicherung-{uid}"
    stage = SITES / "live" / f".upload-{uid}"
    try:
        if archiv.is_symlink() or not archiv.is_file():
            raise RuntimeError("Diese Sicherung gibt es nicht (mehr)")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(mode=0o700, parents=True)
        sub = "live" if art == "live" else "demos"
        r = subprocess.run(["tar", "-xzf", str(archiv), "-C", str(tmp), "--no-same-owner", "--no-same-permissions", f"sites/{sub}/{name}"], capture_output=True, text=True)
        quelle = tmp / "sites" / sub / name
        if r.returncode != 0 or quelle.is_symlink() or not quelle.is_dir():
            raise RuntimeError(f"{name} ist in der Sicherung vom {tag[:10]} nicht enthalten")
        baum_pruefen(quelle)
        if (ziel_ordner(art, name)).is_dir():
            shutil.rmtree(quelle / "angebote", ignore_errors=True)   # aktuelle Wochenangebote bleiben erhalten (uebernehmen)
        os.rename(quelle, stage)
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(stage, ignore_errors=True)
        ergebnis(uid if UPLOAD.match(uid) else "0" * 16, a, False, f"Wiederherstellung fehlgeschlagen: {e}")
        raise
    shutil.rmtree(tmp, ignore_errors=True)
    veroeffentlichen({**a, "aktion": "veroeffentlichen"})
    log(f"aus Sicherung {tag}: {art} {name}")


def _psql(db, sql=None, stdin=None):
    return subprocess.run([*PSQL, "-d", db, "-X", "-A", "-t", "-q", *(["-c", sql] if sql else [])], stdin=stdin, capture_output=True, text=True)


def kundenauszug(a):
    """Lädt die Datenbanksicherung in eine Wegwerf-Datenbank und liest alle Zeilen EINES Kunden heraus (JSON für das Portal).
    Die laufende Datenbank wird dabei nicht angefasst."""
    kid, tag, uid = str(a.get("kunden_id", "")), str(a.get("tag", "")), str(a.get("upload", ""))
    if not UUID.match(kid) or not TAG.match(tag) or not UPLOAD.match(uid):
        raise RuntimeError("ungültiger Auftrag")
    dump = BACKUPS / tag / "markentrix-db.sql.gz"
    db = f"mkrestore_{uid}"
    try:
        if dump.is_symlink() or not dump.is_file():
            raise RuntimeError("Diese Datenbanksicherung gibt es nicht (mehr)")
        r = _psql("postgres", f"CREATE DATABASE {db}")
        if r.returncode != 0:
            raise RuntimeError("Wegwerf-Datenbank konnte nicht angelegt werden: " + r.stderr[:150])
        gz = subprocess.Popen(["gunzip", "-c", str(dump)], stdout=subprocess.PIPE)
        ladung = _psql(db, stdin=gz.stdout)
        gz.stdout.close()
        if gz.wait() != 0:
            raise RuntimeError("Die Sicherung ist beschädigt (gunzip)")
        _ = ladung   # einzelne Fehler beim Einspielen (Rollen, Erweiterungen) sind in der Wegwerf-Datenbank unkritisch
        r = _psql(db, "SELECT c.table_name FROM information_schema.columns c JOIN information_schema.tables t ON t.table_schema=c.table_schema AND t.table_name=c.table_name "
                      "AND t.table_type='BASE TABLE' WHERE c.table_schema='public' AND c.column_name='kunden_id' ORDER BY 1")
        tabellen = [x for x in r.stdout.split() if re.match(r"^[a-z0-9_]+$", x) and x not in AUSZUG_NICHT]
        r = _psql(db, "SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='public' AND data_type='bytea'")
        mit_dateien = set(r.stdout.split())
        r = _psql(db, f"SELECT count(*) FROM kunden WHERE id='{kid}'")
        if r.stdout.strip() != "1":
            raise RuntimeError("Dieser Kunde ist in der Sicherung vom " + tag[:10] + " noch nicht vorhanden")
        aus, uebersprungen = {}, sorted(mit_dateien & set(tabellen))
        for t in tabellen:
            if t in mit_dateien:
                continue
            r = _psql(db, f"SELECT coalesce(json_agg(x), '[]'::json) FROM (SELECT * FROM {t} WHERE kunden_id='{kid}' LIMIT 5000) x")
            zeilen = json.loads(r.stdout.strip() or "[]") if r.returncode == 0 else []
            if zeilen:
                aus[t] = zeilen
        p = QUEUE / f"kundenauszug-{uid}.json"
        p.write_text(json.dumps({"id": uid, "kunden_id": kid, "tag": tag, "tabellen": aus, "ohne_dateiinhalt": uebersprungen, "zeit": time.strftime("%Y-%m-%dT%H:%M:%S")}))
        os.chown(p, 10001, 10001)
        p.chmod(0o640)
        ergebnis(uid, a, True, f"Auszug aus der Sicherung vom {tag[:10]} ist bereit.")
        log(f"Kundenauszug {kid} aus {tag}")
    except Exception as e:  # noqa: BLE001
        ergebnis(uid if UPLOAD.match(uid) else "0" * 16, a, False, f"Auszug fehlgeschlagen: {e}")
        raise
    finally:
        if UPLOAD.match(uid):
            _psql("postgres", f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")


def zurueck(a):
    art, name, uid = a.get("art"), str(a.get("name", "")), str(a.get("upload", ""))
    if art not in NAME or not NAME[art].match(name) or not UPLOAD.match(uid):
        raise RuntimeError("ungültiger Auftrag")
    try:
        ziel = ziel_ordner(art, name)
        alle = sorted([d for d in VORVERSION.iterdir() if d.is_dir() and not d.is_symlink() and d.name.endswith(f"__{art}__{name}")], reverse=True) if VORVERSION.is_dir() else []
        if not alle or ziel.is_symlink() or not ziel.is_dir():
            raise RuntimeError("Es gibt keine frühere Version")
        alt = alle[0]
        uebernehmen(ziel, alt)
        os.rename(ziel, vorname(art, name))
        os.rename(alt, ziel)
        ergebnis(uid, a, True, "Die vorige Version ist wieder online. Die jetzt ersetzte Version ist gesichert, ein weiterer Klick holt sie zurück.", neu=False)
        log(f"zurückgesetzt: {art} {name}")
    except Exception as e:  # noqa: BLE001
        ergebnis(uid if UPLOAD.match(uid) else "0" * 16, a, False, f"Fehlgeschlagen: {e}")
        raise


def server_ip_ermitteln():
    """Öffentliche Adresse des Servers (stündlich) für den DNS-Assistenten im Portal."""
    p = QUEUE / "serverip.json"
    if p.exists() and p.stat().st_mtime > time.time() - 3500:
        return
    import urllib.request
    d = {}
    for key, url in (("v4", os.environ.get("MK_IP_URL", "https://api.ipify.org")), ("v6", os.environ.get("MK_IP6_URL", "https://api64.ipify.org"))):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                d[key] = r.read(100).decode().strip()
        except Exception:  # noqa: BLE001
            pass
    if d.get("v6") == d.get("v4") or (d.get("v6") and ":" not in d["v6"]):
        d.pop("v6", None)
    if d.get("v4"):
        p.write_text(json.dumps(d))
        os.chown(p, 10001, 10001)
        p.chmod(0o640)


def aufraeumen():
    try:
        server_ip_ermitteln()
    except Exception as e:  # noqa: BLE001
        log(f"Server-IP nicht ermittelbar: {e}")
    try:   # Liste der vorhandenen Tagessicherungen für das Portal (Admin → Verwaltung → Aus Sicherung holen)
        p = QUEUE / "sicherungen.json"
        p.write_text(json.dumps({"tage": sicherung_tage(), "db_tage": db_tage(), "stand": time.strftime("%Y-%m-%dT%H:%M:%S")}))
        os.chown(p, 10001, 10001)
        p.chmod(0o640)
    except OSError as e:
        log(f"Sicherungsliste nicht schreibbar: {e}")
    for f in QUEUE.glob("kundenauszug-*.json"):    # enthalten personenbezogene Daten: nach einem Tag weg
        if f.stat().st_mtime < time.time() - 86400:
            f.unlink(missing_ok=True)
    for d in (SITES / "live").glob(".sicherung-*"):
        if d.is_dir() and not d.is_symlink() and d.stat().st_mtime < time.time() - 86400:
            shutil.rmtree(d, ignore_errors=True)
    for d in (SITES / "live").glob(".upload-*"):
        if d.is_dir() and not d.is_symlink() and d.stat().st_mtime < time.time() - 86400:
            shutil.rmtree(d, ignore_errors=True)
    for f in QUEUE.glob("ergebnis-*.json"):
        if f.stat().st_mtime < time.time() - 7 * 86400:
            f.unlink(missing_ok=True)
    if not TRASH.is_dir():
        return
    grenze = time.time() - KEEP_DAYS * 86400
    for d in TRASH.iterdir():
        if TRASH_ID.match(d.name) and d.is_dir() and not d.is_symlink() and d.stat().st_mtime < grenze:
            shutil.rmtree(d)
            log(f"endgültig gelöscht (älter als {KEEP_DAYS} Tage): {d.name}")


def main():
    QUEUE.mkdir(mode=0o770, exist_ok=True)
    for f in sorted(QUEUE.iterdir()):
        if not REQ.match(f.name) or f.is_symlink() or not f.is_file() or f.stat().st_size > 2048:
            continue
        try:
            a = json.loads(f.read_text())
            if a.get("aktion") == "loeschen" and a.get("art") in NAME and NAME[a["art"]].match(str(a.get("name", ""))):
                loeschen(a["art"], a["name"])
            elif a.get("aktion") == "veroeffentlichen":
                veroeffentlichen(a)
            elif a.get("aktion") == "sicherung":
                aus_sicherung(a)
            elif a.get("aktion") == "kundenauszug":
                kundenauszug(a)
            elif a.get("aktion") == "zurueck":
                zurueck(a)
            elif a.get("aktion") == "caddy_neu_laden":
                reload_caddy()
            elif a.get("aktion") == "papierkorb_loeschen":
                papierkorb_loeschen(a)
            elif a.get("aktion") == "wiederherstellen":
                wiederherstellen(str(a.get("id", "")))
            else:
                log(f"Auftrag verworfen: {f.name}")
        except Exception as e:
            log(f"Fehler bei {f.name}: {e}")
        f.unlink(missing_ok=True)
    aufraeumen()
    try:
        caddy_nachruesten()
    except Exception as e:  # noqa: BLE001
        log(f"Caddy-Nachrüstung: {e}")


if __name__ == "__main__":
    main()
