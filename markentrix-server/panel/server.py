#!/usr/bin/env python3
"""Markentrix Server-Dashboard (nur lesend).

Zeigt laufende Dienste, Websites und Demos, Speicher und Sicherungen.
Docker wird ausschließlich über den schreibgeschützten Socket-Proxy gelesen.
Nur Python-Standardbibliothek, keine zusätzlichen Pakete.
"""
import hmac
import json
import os
import shutil
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASSWORD = os.environ.get("PANEL_PASSWORD", "")
DOCKER = os.environ.get("DOCKER_HOST", "http://socket-proxy:2375").replace("tcp://", "http://")
SITES = Path(os.environ.get("SITES_ROOT", "/srv/sites"))
BACKUPS = Path(os.environ.get("BACKUP_DIR", "/backups"))
DOMAIN = os.environ.get("DOMAIN", "")
INDEX = Path(__file__).with_name("index.html")
MAX_FILES = 20000


def docker_get(path):
    with urllib.request.urlopen(DOCKER + path, timeout=5) as r:
        return json.loads(r.read().decode())


def containers():
    try:
        raw = docker_get("/containers/json?all=1")
    except Exception as exc:  # Dienst nicht erreichbar
        return {"error": str(exc), "items": []}
    items = []
    for c in raw:
        status = c.get("Status", "")
        items.append({
            "name": (c.get("Names") or ["?"])[0].lstrip("/"),
            "image": c.get("Image", ""),
            "state": c.get("State", ""),
            "status": status,
            "health": "unhealthy" if "(unhealthy)" in status else ("healthy" if "(healthy)" in status else ""),
            "project": (c.get("Labels") or {}).get("com.docker.compose.project", ""),
            "created": c.get("Created", 0),
            "ports": sorted({f"{p['PublicPort']}→{p['PrivatePort']}" for p in c.get("Ports", []) if p.get("PublicPort")}),
        })
    items.sort(key=lambda i: (i["project"], i["name"]))
    return {"error": "", "items": items}


def host_info():
    info = {"load": list(os.getloadavg())}
    try:
        info["uptime_s"] = int(float(Path("/proc/uptime").read_text().split()[0]))
    except Exception:
        info["uptime_s"] = None
    mem = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, val = line.split(":", 1)
            mem[key] = int(val.strip().split()[0]) * 1024
        info["mem_total"] = mem["MemTotal"]
        info["mem_used"] = mem["MemTotal"] - mem["MemAvailable"]
    except Exception:
        info["mem_total"] = info["mem_used"] = None
    try:
        du = shutil.disk_usage(str(SITES if SITES.exists() else Path("/")))
        info["disk_total"], info["disk_used"] = du.total, du.used
    except Exception:
        info["disk_total"] = info["disk_used"] = None
    return info


def dir_stats(path):
    size = files = 0
    newest = 0
    for root, _dirs, names in os.walk(path):
        for n in names:
            files += 1
            if files > MAX_FILES:
                return size, files, newest
            try:
                st = os.stat(os.path.join(root, n))
                size += st.st_size
                newest = max(newest, int(st.st_mtime))
            except OSError:
                pass
    return size, files, newest


def sites():
    out = []
    for kind in ("live", "demos"):
        base = SITES / kind
        if not base.is_dir():
            continue
        for d in sorted(p for p in base.iterdir() if p.is_dir()):
            size, files, newest = dir_stats(d)
            meta = {}
            mp = d / "site.json"
            try:
                if mp.is_file() and mp.stat().st_size < 4096:
                    meta = json.loads(mp.read_text())
            except Exception:
                meta = {}
            url = f"https://{d.name}" if kind == "live" else (f"https://demo.{DOMAIN}/{d.name}/" if DOMAIN else "")
            out.append({
                "name": d.name,
                "kind": "Live" if kind == "live" else "Demo",
                "url": url,
                "kunde": str(meta.get("kunde", "")),
                "angelegt": str(meta.get("angelegt", "")),
                "size": size,
                "files": files,
                "changed": newest,
            })
    return out


def backups():
    items = []
    if BACKUPS.is_dir():
        for d in sorted((p for p in BACKUPS.iterdir() if p.is_dir()), reverse=True)[:14]:
            size, files, newest = dir_stats(d)
            items.append({"name": d.name, "size": size, "files": files})
    last = None
    try:
        last = int((BACKUPS / "last_success").read_text().strip())
    except Exception:
        pass
    return {"last_success": last, "items": items}


def status():
    return {
        "now": int(time.time()),
        "domain": DOMAIN,
        "host": host_info(),
        "containers": containers(),
        "sites": sites(),
        "backups": backups(),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "mk-panel"

    def _authorized(self):
        header = self.headers.get("Authorization", "")
        if not PASSWORD or not header.startswith("Basic "):
            return False
        import base64
        try:
            given = base64.b64decode(header[6:]).decode()
        except Exception:
            return False
        return hmac.compare_digest(given.encode(), f"admin:{PASSWORD}".encode())

    def _send(self, code, body, ctype, extra=None):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            return self._send(200, "ok", "text/plain")
        if not self._authorized():
            time.sleep(1)
            return self._send(401, "Anmeldung erforderlich", "text/plain; charset=utf-8",
                              {"WWW-Authenticate": 'Basic realm="Markentrix Server", charset="UTF-8"'})
        if path in ("/", "/index.html"):
            return self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/status":
            return self._send(200, json.dumps(status()), "application/json")
        return self._send(404, "Nicht gefunden", "text/plain; charset=utf-8")

    do_POST = do_PUT = do_DELETE = lambda self: self._send(405, "Nur lesend", "text/plain; charset=utf-8")


if __name__ == "__main__":
    if not PASSWORD:
        raise SystemExit("PANEL_PASSWORD fehlt")
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
