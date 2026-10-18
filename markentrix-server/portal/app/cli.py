"""Verwaltung auf dem Server:  python -m app.cli admin-add EMAIL [NAME]   (legt Admin an oder setzt Passwort neu)"""
import secrets
import sys

import json

from . import db, einstellungen, mailer
from .security import EMAIL_RE, audit, hash_password


def passwort() -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(16))


def admin_add(email: str, name: str | None):
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        sys.exit("Ungültige E-Mail-Adresse.")
    pw = passwort()
    with db.tx("system") as cur:
        cur.execute("SELECT id, rolle FROM benutzer WHERE lower(email)=%s", (email,))
        u = cur.fetchone()
        if u and u["rolle"] != "admin":
            sys.exit("Diese E-Mail gehört zu einem Kundenkonto.")
        if u:
            cur.execute("UPDATE benutzer SET passwort_hash=%s, aktiv=true, fehlversuche=0, gesperrt_bis=NULL, totp_aktiv=false, totp_secret=NULL, totp_recovery='[]'::jsonb WHERE id=%s", (hash_password(pw), u["id"]))
            aktion = "admin_passwort_neu"
        else:
            cur.execute("INSERT INTO benutzer (email, name, rolle, passwort_hash) VALUES (%s,%s,'admin',%s)", (email, name, hash_password(pw)))
            aktion = "admin_angelegt"
        audit(cur, None, aktion, None, {"email": email})
    print(f"ADMIN_EMAIL={email}")
    print(f"ADMIN_PASSWORT={pw}")


def alarm_mail(stufe: str, titel: str, text: str):
    """Wird vom Wachdienst auf dem Server aufgerufen (auch wenn der Portal-Dienst selbst ausgefallen ist)."""
    if stufe not in ("info", "warnung", "kritisch"):
        stufe = "warnung"
    with db.tx("system") as cur:
        an = (einstellungen.lesen(cur, "benachrichtigung") or {}).get("alarm_email")
        if not an:
            cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
            r = cur.fetchone()
            an = r and r["email"]
        cur.execute("INSERT INTO alarme (stufe, quelle, titel, details, kanaele_gesendet) VALUES (%s,'wachdienst',%s,%s::jsonb,%s)",
                    (stufe, titel[:200], json.dumps({"text": text[:2000]}), ["mail"] if an else []))
    if not an:
        sys.exit("Kein Empfänger für Alarme gefunden.")
    ok, fehler = mailer.senden(an, titel, text + "\n\n(automatische Meldung der Serverüberwachung)")
    if not ok:
        sys.exit("Mail nicht gesendet: " + fehler)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "admin-add":
        db.open_pool()
        admin_add(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        db.close_pool()
    elif len(sys.argv) >= 5 and sys.argv[1] == "alarm-mail":
        db.open_pool()
        try:
            alarm_mail(sys.argv[2], sys.argv[3], sys.argv[4])
        finally:
            db.close_pool()
    else:
        sys.exit("Aufruf: python -m app.cli admin-add EMAIL [NAME]")
