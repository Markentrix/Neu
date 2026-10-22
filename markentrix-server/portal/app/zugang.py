"""Einladungen und Zurücksetzen: erzeugt einmalige Links (nur der Hash wird gespeichert)."""
from fastapi import HTTPException

from . import config, mailer
from .security import EMAIL_RE, new_token, token_hash


def link_erzeugen(cur, email: str, name: str | None, rolle: str, kunden_id=None, partner_id=None, kunden_rolle: str = "inhaber") -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    tok = new_token()
    cur.execute("SELECT id, rolle, kunden_id, vertriebspartner_id FROM benutzer WHERE lower(email)=%s", (email,))
    u = cur.fetchone()
    if u and (u["rolle"] != rolle or str(u["kunden_id"] or "") != str(kunden_id or "") or str(u["vertriebspartner_id"] or "") != str(partner_id or "")):
        raise HTTPException(409, "Diese E-Mail-Adresse gehört schon zu einem anderen Konto.")
    if u:
        cur.execute("UPDATE benutzer SET einladung_token_hash=%s, einladung_ablauf=now()+make_interval(days=>%s) WHERE id=%s", (token_hash(tok), config.INVITE_DAYS, u["id"]))
    else:
        cur.execute("""INSERT INTO benutzer (email, name, rolle, kunden_id, vertriebspartner_id, einladung_token_hash, einladung_ablauf, kunden_rolle)
                       VALUES (%s,%s,%s,%s,%s,%s,now()+make_interval(days=>%s),%s)""", (email, name, rolle, kunden_id, partner_id, token_hash(tok), config.INVITE_DAYS, kunden_rolle))
    return f"{config.BASE_URL}/einladung?token={tok}"


def per_mail(email: str, name: str | None, link: str, rolle: str) -> dict:
    """Versendet die Einladung, wenn E-Mail-Versand eingerichtet ist. Nach dem Commit aufrufen."""
    if not mailer.konfiguriert():
        return {"gesendet": False, "grund": "E-Mail-Versand ist noch nicht eingerichtet (Einstellungen). Bitte den Link selbst senden."}
    anhang = None
    try:
        from . import anleitung_pdf, einstellungen
        from .db import tx
        r = "vertrieb" if rolle == "vertrieb" else "kunde" if rolle == "kunde" else None
        if r:
            with tx("system") as cur:
                firma = einstellungen.lesen(cur, "firma")
            anhang = (f"Markentrix-Anleitung-{r}.pdf", anleitung_pdf.bauen(r, firma), "application/pdf")
    except Exception:  # Anleitung ist nur ein Zusatz, die Einladung muss immer rausgehen
        anhang = None
    ok, fehler = mailer.einladung(email.strip().lower(), name, link, rolle, config.INVITE_DAYS, anhang)
    return {"gesendet": ok, "grund": fehler}
