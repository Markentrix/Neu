"""Systemstatus im Admin: liest die Ergebnisse der Server-Überwachung (watchdog.sh) und meldet, wenn die Überwachung selbst verstummt."""
import json
import os
import time
from pathlib import Path

import segno
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import betrieb, config, einstellungen, fehlerhilfe
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


def ampel(d: dict | None, smtp: dict, jobs: dict | None, mail: dict | None, kistatus: dict | None = None) -> list[dict]:
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
        elif fehler and int((jobs["wert"] or {}).get("fehler_serie") or 0) >= 10:
            out.append(_punkt("jobs", "Hintergrundjobs", "bad", f"der Job „{fehler}“ ist {int(jobs['wert']['fehler_serie'])}-mal hintereinander fehlgeschlagen"))
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
    w = (kistatus or {}).get("wert") or {}
    if w.get("fehler_am") and (not w.get("ok_am") or w["fehler_am"] > w["ok_am"]):   # nur Hinweis: KI-Funktionen sind Zusatz, der Betrieb läuft weiter
        out.append(_punkt("ki", "KI-Dienst", "warn", "letzter Aufruf fehlgeschlagen: " + str(w.get("fehler", ""))[:300]))
    if einstellungen.defekt:
        out.append(_punkt("geheimnis", "Gespeicherte Einstellungen", "bad", "nicht lesbar: " + ", ".join(sorted(einstellungen.defekt)) + ". Stimmt PORTAL_SECRET in der .env noch?"))
    return out


@router.get("/admin/systemstatus")
def systemstatus(user: dict = Depends(require_admin)):
    d = lesen_status()
    with tx("admin") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        ki = einstellungen.lesen(cur, "ki") or {}
        jobs, mail, kistatus = betrieb.lesen(cur, "jobs"), betrieb.lesen(cur, "mail"), betrieb.lesen(cur, "ki")
    probleme = list(d["probleme"]) if d else []
    if d and d["alter_minuten"] > 30:
        probleme.append(f"Die Server-Überwachung hat sich seit {d['alter_minuten']} Minuten nicht gemeldet")
    if not smtp.get("host"):
        probleme.append("E-Mail-Versand ist noch nicht eingerichtet (Einstellungen → E-Mail)")
    punkte = ampel(d, smtp, jobs, mail, kistatus)
    for p in punkte:   # Rote Punkte aus der Datenbank erscheinen auch in der Problemliste (Jetzt wichtig)
        if p["status"] == "bad" and p["id"] in ("jobs", "mail"):   # Server-Themen meldet der Wächter schon selbst
            probleme.append(f"{p['titel']}: {p['detail']}")
    rang = {"ok": 0, "unbekannt": 1, "warn": 2, "bad": 3}
    gesamt = max((p["status"] for p in punkte), key=lambda s: rang[s], default="unbekannt")
    return {"ampel": punkte, "gesamt": gesamt, "vorhanden": d is not None, "status": d, "probleme": probleme, "mail_eingerichtet": bool(smtp.get("host")), "ki_eingerichtet": bool(ki.get("api_key"))}


@router.get("/admin/vertragsstand")
def vertragsstand(user: dict = Depends(require_admin)):
    """Nachweis, dass die Zusagen aus dem AVV (Anlage 2) im Betrieb eingehalten werden: ein Blick statt vieler Karten."""
    from . import avv as avv_modul
    from .routes_avv import fehlende, veraltete
    d = lesen_status()
    out = []
    with tx("admin") as cur:
        cur.execute("SELECT count(*) AS n, count(*) FILTER (WHERE totp_aktiv) AS mit FROM benutzer WHERE rolle='admin' AND aktiv")
        a = cur.fetchone()
        out.append(_punkt("zwei_faktor", "Zwei-Faktor-Anmeldung der Admins", "ok" if a["n"] and a["n"] == a["mit"] else "bad", f"{a['mit']} von {a['n']} Admin-Konten mit 2FA"))
        cur.execute("SELECT min(zeit) AS aelteste FROM audit_log")
        r = cur.fetchone()["aelteste"]
        tage = int((time.time() - r.timestamp()) / 86400) if r else 0
        out.append(_punkt("audit", "Audit-Log: Aufbewahrung 12 Monate", "ok" if tage <= 400 else "bad", f"ältester Eintrag {tage} Tage" + ("" if tage <= 400 else ", die Bereinigung läuft nicht")))
        cur.execute("SELECT min(erstellt_am) AS aelteste FROM chat_verlauf")
        r = cur.fetchone()["aelteste"]
        tage = int((time.time() - r.timestamp()) / 86400) if r else 0
        out.append(_punkt("chat", "Chatverläufe: Aufbewahrung 6 Monate", "ok" if tage <= 200 else "bad", f"ältester Eintrag {tage} Tage" + ("" if tage <= 200 else ", die Bereinigung läuft nicht")))
        fe, ve = fehlende(cur), veraltete(cur)
        out.append(_punkt("avv_fehlt", "Kunden ohne AVV", "ok" if not fe else "bad", "alle Kunden haben einen AVV" if not fe else f"{len(fe)} Kunden ohne AVV"))
        out.append(_punkt("avv_alt", f"AVV-Fassung (aktuell: Version {avv_modul.VERSION})", "ok" if not ve else "warn", "alle auf der aktuellen Fassung" if not ve else f"{len(ve)} Kunden noch mit alter Fassung"))
        cur.execute("""SELECT count(*) AS n FROM uav_mitteilungen m JOIN uav_aenderungen a ON a.id=m.aenderung_id WHERE m.widerspruch_am IS NOT NULL AND a.wirksam_ab >= current_date - 30""")
        w = cur.fetchone()["n"]
        out.append(_punkt("widerspruch", "Widersprüche gegen Unterauftragsverarbeiter", "ok" if not w else "warn", "keine offenen" if not w else f"{w} Widerspruch/Widersprüche in den letzten 30 Tagen prüfen"))
        cur.execute("SELECT count(*) AS n FROM domains WHERE status='aktiv' AND ablauf_am IS NOT NULL AND ablauf_am <= current_date + 30")
        dn = cur.fetchone()["n"]
        out.append(_punkt("domains", "Domains laufen ab", "ok" if not dn else "warn", "keine in den nächsten 30 Tagen" if not dn else f"{dn} Domain(s) laufen in den nächsten 30 Tagen ab"))
    if d:
        b = d.get("backup_stunden", 9999)
        out.append(_punkt("backup", "Tägliche Sicherung (Aufbewahrung 30 Tage)", "ok" if b <= 36 else "bad", "letzte vor " + _stunden(b) if b < 9999 else "noch keine Sicherung"))
        rs = d.get("restore_stunden", 9999)
        out.append(_punkt("restore", "Wiederherstellungstest (mindestens vierteljährlich, läuft wöchentlich)", "ok" if rs <= 240 else "bad" if rs < 9999 else "unbekannt", "letzter Test vor " + _stunden(rs) if rs < 9999 else "noch kein Test festgehalten"))
        o = d.get("offsite_stunden", 9999)
        out.append(_punkt("offsite", "Verschlüsselte Kopie getrennt vom Server", "ok" if d.get("offsite_aktiv") and o <= 36 else "bad" if d.get("offsite_aktiv") else "warn",
                          ("letzte vor " + _stunden(o)) if d.get("offsite_aktiv") and o < 9999 else "nicht eingerichtet (mkctl offsite-setup)"))
    else:
        out.append(_punkt("ueberwachung", "Server-Überwachung", "unbekannt", "noch keine Meldung"))
    rang = {"ok": 0, "unbekannt": 1, "warn": 2, "bad": 3}
    return {"punkte": out, "gesamt": max((p["status"] for p in out), key=lambda s: rang[s])}


@router.get("/admin/portal-qr")
def portal_qr(user: dict = Depends(require_admin)):
    """QR-Code der Portal-Adresse (Anmeldeseite), damit Kunden und Vertriebler das Portal direkt am Handy öffnen."""
    return {"url": config.BASE_URL, "svg": segno.make(config.BASE_URL, error="m").svg_data_uri(scale=6, border=2)}


# ---------------------------------------------------------------- Fehlerhilfe
@router.get("/admin/fehlerhilfe")
def fehlerhilfe_liste(user: dict = Depends(require_admin)):
    """Letzte Fehler-Alarme mit Ursache und Lösungsvorschlag (offene zuerst)."""
    with tx("admin") as cur:
        cur.execute("""SELECT id, zeit, stufe, quelle, titel, details, bestaetigt_am IS NOT NULL AS erledigt FROM alarme
                       WHERE details ? 'erklaerung' ORDER BY (bestaetigt_am IS NULL) DESC, zeit DESC LIMIT 40""")
        rows = cur.fetchall()
    return [{"id": r["id"], "zeit": r["zeit"], "stufe": r["stufe"], "quelle": r["quelle"], "titel": r["titel"], "erledigt": r["erledigt"],
             "fehler_nr": r["details"].get("fehler_nr"), "text": r["details"].get("text"), "erklaerung": r["details"].get("erklaerung")} for r in rows]


class ErklaerIn(BaseModel):
    text: str = Field(min_length=3, max_length=4000)


@router.post("/admin/fehlerhilfe/erklaeren")
def fehlerhilfe_erklaeren(data: ErklaerIn, user: dict = Depends(require_admin)):
    """Eine Fehlermeldung einfügen (z. B. aus einer Mail oder vom Bildschirm): bekommt Ursache und Schritte."""
    return fehlerhilfe.erklaeren(data.text)


def _smtp_probe(c: dict) -> str:
    """Prüft Verbindung und Anmeldung beim Mailserver, ohne etwas zu senden. Gibt "" bei Erfolg zurück, sonst den Fehlertext."""
    import smtplib
    import ssl
    try:
        host, port, mode = c["host"], int(c.get("port") or 587), c.get("sicherung", "starttls")
        ctx = ssl.create_default_context()
        sm = smtplib.SMTP_SSL(host, port, timeout=10, context=ctx) if mode == "ssl" else smtplib.SMTP(host, port, timeout=10)
        with sm:
            sm.ehlo()
            if mode == "starttls":
                sm.starttls(context=ctx)
                sm.ehlo()
            if c.get("benutzer"):
                sm.login(c["benutzer"], c.get("passwort", ""))
        return ""
    except Exception as e:  # noqa: BLE001 - jeder Fehler ist hier das Ergebnis
        return f"{type(e).__name__}: {str(e)[:200]}"


@router.post("/admin/fehlerhilfe/pruefen")
def fehlerhilfe_pruefen(user: dict = Depends(require_admin)):
    """Prüft jetzt die wichtigsten Dinge und gibt bei jedem Problem Ursache und Lösungsvorschlag mit. Sendet keine Mails."""
    import shutil
    out = []

    def punkt(id, titel, ok, detail="", fehler_text=""):
        out.append({"id": id, "titel": titel, "ok": ok, "detail": detail, "vorschlag": None if ok else fehlerhilfe.erklaeren(fehler_text or detail)})
    try:
        with tx("system") as cur:
            cur.execute("SELECT 1")
            smtp = einstellungen.lesen(cur, "smtp") or {}
            jobs = betrieb.lesen(cur, "jobs")
        punkt("db", "Datenbank", True, "erreichbar")
    except Exception as e:  # noqa: BLE001
        punkt("db", "Datenbank", False, "nicht erreichbar", f"{type(e).__name__}: {e}")
        return {"punkte": out, "ok": False}
    frei = shutil.disk_usage("/")
    pr = round(100 * (frei.total - frei.free) / frei.total)
    punkt("platte", "Festplatte", pr < 90, f"{pr} % belegt", "No space left on device")
    punkt("geheimnis", "Gespeicherte Einstellungen", not einstellungen.defekt, "lesbar" if not einstellungen.defekt else "nicht lesbar: " + ", ".join(sorted(einstellungen.defekt)), "InvalidToken PORTAL_SECRET")
    if not smtp.get("host"):
        punkt("mail", "E-Mail-Versand", False, "noch nicht eingerichtet", "SMTPConnectError nicht eingerichtet")
    else:
        f = _smtp_probe(smtp)
        punkt("mail", "E-Mail-Versand (Anmeldung beim Mailserver)", not f, "Anmeldung klappt" if not f else f, "SMTP " + f)
    if not jobs or jobs["sekunden"] > 300:
        punkt("jobs", "Hintergrundjobs", False, "melden sich nicht (seit " + (str(jobs["sekunden"] // 60) + " Min." if jobs else "dem Start") + ")", "TimeoutError Hintergrundjobs")
    else:
        punkt("jobs", "Hintergrundjobs", True, "laufen")
    return {"punkte": out, "ok": all(p["ok"] for p in out)}
