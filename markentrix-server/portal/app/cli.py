"""Verwaltung auf dem Server:  python -m app.cli admin-add EMAIL [NAME]   (legt Admin an oder setzt Passwort neu)"""
import secrets
import sys

from . import db
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
            cur.execute("UPDATE benutzer SET passwort_hash=%s, aktiv=true, fehlversuche=0, gesperrt_bis=NULL WHERE id=%s", (hash_password(pw), u["id"]))
            aktion = "admin_passwort_neu"
        else:
            cur.execute("INSERT INTO benutzer (email, name, rolle, passwort_hash) VALUES (%s,%s,'admin',%s)", (email, name, hash_password(pw)))
            aktion = "admin_angelegt"
        audit(cur, None, aktion, None, {"email": email})
    print(f"ADMIN_EMAIL={email}")
    print(f"ADMIN_PASSWORT={pw}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "admin-add":
        from . import config
        db.open_pool()
        admin_add(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        db.close_pool()
    else:
        sys.exit("Aufruf: python -m app.cli admin-add EMAIL [NAME]")
