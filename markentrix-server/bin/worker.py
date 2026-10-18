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
        subprocess.run(["docker", "compose", "--project-directory", str(BASE), "-f", str(BASE / "docker-compose.yml"),
                        "exec", "-T", "caddy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"], check=False, capture_output=True)


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


def aufraeumen():
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
