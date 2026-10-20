"""Systemstatus im Admin: liest die Ergebnisse der Server-Überwachung (watchdog.sh) und meldet, wenn die Überwachung selbst verstummt."""
import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends

from . import betrieb, einstellungen
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


def _punkt(id, titel, status, detail):
    return {"id": id, "titel": titel, "status": status, "detail": detail}


def _stunden(h):
    return "über 400 Tage" if h >= 9999 else (f"{h} Std." if h < 48 else f"{h // 24} Tage")


def ampel(d: dict | None, smtp: dict, jobs: dict | None, mail: dict | None) -> list[dict]:
    """Übersetzt die Messwerte in eine Ampel: ok (grün), warn (gelb), bad (rot), unbekannt (grau)."""
    out = []
    if d is None:
        out.append(_punkt("ueberwachung", "Server-Überwachung", "unbekannt", "Noch keine Meldung (der Wächter läuft alle 5 Minuten auf dem Server)."))
    elif d["alter_minuten"] > 30:
        out.append(_punkt("ueberwachung", "Server-Überwachung", "bad", f"Seit {d['alter_minuten']} Minuten keine Meldung."))
    else:
        out.append(_punkt("ueberwachung", "Server-Überwachung", "ok", "meldet sich regelmäßig"))
    if d:
        b = d.get("backup_stunden", 9999)
        out.append(_punkt("backup", "Sicherung (lokal)", "ok" if b <= 36 else "bad", "letzte vor " + _stunden(b) if b < 9999 else "noch keine Sicherung vorhanden"))
        if d.get("offsite_aktiv"):
            o = d.get("offsite_stunden", 9999)
            out.append(_punkt("offsite", "Sicherung (extern)", "ok" if o <= 36 else "bad", "letzte vor " + _stunden(o) if o < 9999 else "noch keine externe Sicherung"))
        else:
            out.append(_punkt("offsite", "Sicherung (extern)", "warn", "nicht eingerichtet, bei einem Serverausfall wären auch die Sicherungen weg"))
        c = d.get("zertifikat_tage", -1)
        out.append(_punkt("zertifikat", "Zertifikat (HTTPS)", "unbekannt" if c < 0 else ("ok" if c >= 14 else "bad"), "nicht geprüft" if c < 0 else f"läuft in {c} Tagen ab"))
        p = d.get("platte_prozent", 0)
        out.append(_punkt("platte", "Speicherplatz", "ok" if p < 80 else ("warn" if p < 90 else "bad"), f"{p} % belegt"))
    if os.environ.get("PORTAL_JOBS", "1") == "0":
        out.append(_punkt("jobs", "Hintergrundjobs", "warn", "ausgeschaltet (Erinnerungen, Berichte und Mails laufen nicht)"))
    elif not jobs:
        out.append(_punkt("jobs", "Hintergrundjobs", "unbekannt", "noch kein Lauf festgehalten"))
    else:
        fehler = (jobs["wert"] or {}).get("fehler_job")
        if jobs["sekunden"] > 300:
            out.append(_punkt("jobs", "Hintergrundjobs", "bad", f"seit {jobs['sekunden'] // 60} Minuten kein Lauf"))
        elif fehler:
            out.append(_punkt("jobs", "Hintergrundjobs", "warn", f"laufen, aber der Job „{fehler}“ ist zuletzt fehlgeschlagen"))
        else:
            out.append(_punkt("jobs", "Hintergrundjobs", "ok", "laufen"))
    if not smtp.get("host"):
        out.append(_punkt("mail", "E-Mail-Versand", "warn", "noch nicht eingerichtet (Einstellungen → E-Mail)"))
    else:
        w = (mail or {}).get("wert") or {}
        ok_am, fe_am = w.get("ok_am"), w.get("fehler_am")
        if fe_am and (not ok_am or fe_am > ok_am):
            out.append(_punkt("mail", "E-Mail-Versand", "bad", "letzter Versand fehlgeschlagen: " + str(w.get("fehler", ""))[:120]))
        elif ok_am:
            out.append(_punkt("mail", "E-Mail-Versand", "ok", "letzter Versand hat geklappt"))
        else:
            out.append(_punkt("mail", "E-Mail-Versand", "unbekannt", "eingerichtet, aber noch keine Mail verschickt"))
    return out


@router.get("/admin/systemstatus")
def systemstatus(user: dict = Depends(require_admin)):
    d = lesen_status()
    with tx("admin") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        ki = einstellungen.lesen(cur, "ki") or {}
        jobs, mail = betrieb.lesen(cur, "jobs"), betrieb.lesen(cur, "mail")
    probleme = list(d["probleme"]) if d else []
    if d and d["alter_minuten"] > 30:
        probleme.append(f"Die Server-Überwachung hat sich seit {d['alter_minuten']} Minuten nicht gemeldet")
    if not smtp.get("host"):
        probleme.append("E-Mail-Versand ist noch nicht eingerichtet (Einstellungen → E-Mail)")
    punkte = ampel(d, smtp, jobs, mail)
    for p in punkte:   # Rote Punkte aus der Datenbank erscheinen auch in der Problemliste (Jetzt wichtig)
        if p["status"] == "bad" and p["id"] in ("jobs", "mail"):   # Server-Themen meldet der Wächter schon selbst
            probleme.append(f"{p['titel']}: {p['detail']}")
    rang = {"ok": 0, "unbekannt": 1, "warn": 2, "bad": 3}
    gesamt = max((p["status"] for p in punkte), key=lambda s: rang[s], default="unbekannt")
    return {"ampel": punkte, "gesamt": gesamt, "vorhanden": d is not None, "status": d, "probleme": probleme, "mail_eingerichtet": bool(smtp.get("host")), "ki_eingerichtet": bool(ki.get("api_key"))}
