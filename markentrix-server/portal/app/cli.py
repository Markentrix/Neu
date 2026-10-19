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


DEMO_PRAEFIX = "DEMO – "


def demo_daten():
    """Legt Beispieldaten an (Kunde als Referenzkunde = ohne Abrechnung, Leads, Anfragen, Aufgabe), damit man gefahrlos klicken und Schulungen machen kann. Alles trägt 'DEMO –' im Namen."""
    with db.tx("system") as cur:
        cur.execute("SELECT count(*) AS n FROM kunden WHERE firma LIKE %s", (DEMO_PRAEFIX + "%",))
        if cur.fetchone()["n"]:
            sys.exit("Die Demo-Daten gibt es schon (mkctl demo-daten-entfernen löscht sie).")
        cur.execute("""INSERT INTO kunden (firma, ansprechpartner, email, telefon, status, referenzkunde)
                       VALUES (%s,'Erika Beispiel','demo-kunde@example.invalid','0511 000000','aktiv',true) RETURNING id""", (DEMO_PRAEFIX + "Autohaus Beispiel GmbH",))
        kid = cur.fetchone()["id"]
        for n, (name, text) in enumerate((("Max Mustermann", "Bitte um Rückruf wegen Reifenwechsel."), ("Sabine Probe", "Wann habt ihr Samstag geöffnet?"), ("Jan Test", "Angebot für Klimaservice gewünscht."))):
            cur.execute("INSERT INTO anfragen (kunden_id, name, kontakt, nachricht) VALUES (%s,%s,%s,%s)", (kid, name, "demo@example.invalid", text))
        for i, (firma, temp) in enumerate((("Bäckerei Beispiel", "heiss"), ("Elektro Muster", "warm"), ("Friseur Probe", "kalt"), ("Kfz Demo Werkstatt", "heiss"), ("Fitness Test Studio", "warm"))):
            cur.execute("""INSERT INTO leads (firma, ansprechpartner, email, telefon, ort, quelle, temperatur, loeschen_nach, notiz)
                           VALUES (%s,'Demo Person','demo@example.invalid','0511 111111','Celle','manuell',%s, current_date + interval '30 days','Demo-Datensatz')""", (DEMO_PRAEFIX + firma, temp))
        cur.execute("INSERT INTO aufgaben (kunden_id, titel, quelle, faellig_am) VALUES (%s,'DEMO – Kunden anrufen','manuell', current_date)", (kid,))
        audit(cur, None, "demo_daten_angelegt", None, {"kunde": str(kid)})
    print("Demo-Daten angelegt: 1 Kunde (Referenzkunde, nie abgerechnet), 3 Anfragen, 5 Leads, 1 Aufgabe.")


def demo_entfernen():
    with db.tx("system") as cur:
        cur.execute("DELETE FROM aufgaben WHERE titel LIKE %s", (DEMO_PRAEFIX + "%",))
        cur.execute("DELETE FROM leads WHERE firma LIKE %s", (DEMO_PRAEFIX + "%",))
        cur.execute("DELETE FROM kunden WHERE firma LIKE %s", (DEMO_PRAEFIX + "%",))
        n = cur.rowcount
        audit(cur, None, "demo_daten_entfernt", None, {"kunden": n})
    print(f"Demo-Daten entfernt ({n} Kunde).")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "admin-add":
        db.open_pool()
        admin_add(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        db.close_pool()
    elif len(sys.argv) >= 2 and sys.argv[1] in ("demo-daten", "demo-daten-entfernen"):
        db.open_pool()
        try:
            demo_daten() if sys.argv[1] == "demo-daten" else demo_entfernen()
        finally:
            db.close_pool()
    elif len(sys.argv) >= 5 and sys.argv[1] == "alarm-mail":
        db.open_pool()
        try:
            alarm_mail(sys.argv[2], sys.argv[3], sys.argv[4])
        finally:
            db.close_pool()
    else:
        sys.exit("Aufruf: python -m app.cli admin-add EMAIL [NAME]")
