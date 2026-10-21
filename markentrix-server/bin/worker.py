#!/usr/bin/env python3
"""Führt Aufträge aus dem Portal aus (Website/Demo in den Papierkorb, Wiederherstellen).
Läuft jede Minute als root per cron. Prüft jeden Auftrag streng, das Portal bleibt ohne Root-Rechte."""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path(os.environ.get("MK_BASE", "/opt/markentrix"))
SITES = Path(os.environ.get("MK_SITES", "/srv/sites"))
QUEUE = BASE / "queue"
TRASH = SITES / ".papierkorb"
KEEP_DAYS = 14
NAME = {"live": re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$"), "demo": re.compile(r"^[a-z0-9]([a-z0-9-]{0,40}[a-z0-9])?$")}
TRASH_ID = re.compile(r"^\d{8}-\d{6}__(live|demo)__[A-Za-z0-9.-]{1,253}$")
REQ = re.compile(r"^auftrag-[0-9a-f]{12,32}\.json$")


def log(m):
    print(time.strftime("%F %T"), m, flush=True)


def reload_caddy():
    mode = (BASE / "mode").read_text().strip() if (BASE / "mode").exists() else "own"
    if mode == "own":
        try:
            subprocess.run(["docker", "compose", "--project-directory", str(BASE), "-f", str(BASE / "docker-compose.yml"),
                            "exec", "-T", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"], check=False, capture_output=True)
        except OSError as e:
            log(f"Caddy konnte nicht neu geladen werden: {e}")


def loeschen(art, name):
    quelle = SITES / ("live" if art == "live" else "demos") / name
    if quelle.is_symlink() or not quelle.is_dir():
        raise RuntimeError("Ordner nicht vorhanden")
    TRASH.mkdir(mode=0o755, exist_ok=True)
    ziel = TRASH / f"{time.strftime('%Y%m%d-%H%M%S')}__{art}__{name}"
    shutil.move(str(quelle), str(ziel))
    cf = BASE / "caddy" / "sites" / f"{name}.caddy"
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
        shutil.move(str(bak), str(BASE / "caddy" / "sites" / f"{name}.caddy"))
        reload_caddy()
    if art == "live":
        subprocess.run(["chown", "-R", "10001:10001", str(ziel / "angebote")], check=False, capture_output=True)
    log(f"wiederhergestellt: {art} {name}")


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


def caddy_datei(domain):
    cf = BASE / "caddy" / "sites" / f"{domain}.caddy"
    if cf.exists():
        return False
    cf.parent.mkdir(parents=True, exist_ok=True)
    cf.write_text(f"{domain}, www.{domain} {{\n\tencode zstd gzip\n\troot * /srv/sites/live/{domain}\n\tfile_server\n}}\n")
    return True


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
        angelegt = False
        if art == "live":
            angelegt = caddy_datei(name)
            if angelegt:
                reload_caddy()
        vorversionen_aufraeumen(art, name)
        url = f"https://{name}/" if art == "live" else f"https://demo.{os.environ.get('MK_DOMAIN', 'markentrix.de')}/{name}/"
        text = ("Website neu angelegt und veröffentlicht. Damit sie erreichbar ist, muss die Domain per A-Eintrag (auch www) auf diesen Server zeigen, das HTTPS-Zertifikat kommt dann automatisch."
                if neu and art == "live" else "Veröffentlicht. Die vorige Version ist gesichert und lässt sich zurückholen.")
        ergebnis(uid, a, True, text, url=url, neu=neu)
        log(f"veröffentlicht: {art} {name}")
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(stage, ignore_errors=True)
        ergebnis(uid if UPLOAD.match(uid) else "0" * 16, a, False, f"Fehlgeschlagen: {e}")
        raise


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


def aufraeumen():
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
            elif a.get("aktion") == "zurueck":
                zurueck(a)
            elif a.get("aktion") == "wiederherstellen":
                wiederherstellen(str(a.get("id", "")))
            else:
                log(f"Auftrag verworfen: {f.name}")
        except Exception as e:
            log(f"Fehler bei {f.name}: {e}")
        f.unlink(missing_ok=True)
    aufraeumen()


if __name__ == "__main__":
    main()
