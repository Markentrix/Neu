"""Systemstatus im Admin: liest die Ergebnisse der Server-Überwachung (watchdog.sh) und meldet, wenn die Überwachung selbst verstummt."""
import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends

from . import einstellungen
from .db import tx
from .security import require_admin

router = APIRouter(prefix="/api")
DATEI = Path(os.environ.get("BACKUP_DIR", "/backups")) / "system.json"


def lesen_status() -> dict | None:
    try:
        d = json.loads(DATEI.read_text())
        d["alter_minuten"] = int((time.time() - float(d.get("zeit", 0))) / 60)
        return d
    except (OSError, ValueError):
        return None


@router.get("/admin/systemstatus")
def systemstatus(user: dict = Depends(require_admin)):
    d = lesen_status()
    with tx("admin") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        ki = einstellungen.lesen(cur, "ki") or {}
        cur.execute("SELECT max(letzter_login) AS l FROM benutzer WHERE rolle='admin'")
    probleme = list(d["probleme"]) if d else []
    if d and d["alter_minuten"] > 30:
        probleme.append(f"Die Server-Überwachung hat sich seit {d['alter_minuten']} Minuten nicht gemeldet")
    if not smtp.get("host"):
        probleme.append("E-Mail-Versand ist noch nicht eingerichtet (Einstellungen → E-Mail)")
    return {"vorhanden": d is not None, "status": d, "probleme": probleme, "mail_eingerichtet": bool(smtp.get("host")), "ki_eingerichtet": bool(ki.get("api_key"))}
