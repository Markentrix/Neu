"""Mail-Verlauf je Kunde und Lead: jede Mail an einen bekannten Empfänger wird mit Betreff, Art und Ergebnis festgehalten.
Der Empfänger wird über die Adresse gefunden (Kunde, Zugang oder Lead), wenn der Aufrufer keine ID mitgibt. Mails ans Team landen nirgends."""
import logging
import re

from .db import tx

log = logging.getLogger("verlauf")

# Betreff-Stichworte -> Art (nur wenn der Aufrufer keine Art genannt hat)
ARTEN = [("erinnerung", "erinnerung"), ("mahnung", "mahnung"), ("zahlungserinnerung", "mahnung"), ("rechnung", "rechnung"), ("angebot", "angebot"),
         ("terminvorschl", "termin"), ("termin", "termin"), ("gespräch", "termin"), ("willkommen", "zugang"), ("einladung", "zugang"), ("zugang", "zugang"),
         ("passwort", "zugang"), ("monatsbericht", "bericht"), ("bericht", "bericht"), ("datenschutz", "vertrag"), ("vertrag", "vertrag"), ("avv", "vertrag"),
         ("website", "website"), ("freigabe", "freigabe"), ("anfrage", "anfrage"), ("ticket", "ticket")]


def art_aus_betreff(art: str, betreff: str) -> str:
    if art and art != "system":
        return art
    t = (betreff or "").lower()
    for wort, a in ARTEN:
        if wort in t:
            return a
    return "system"


def notieren(an: str, betreff: str, art: str, ok: bool, fehler: str = "", kunden_id=None, lead_id=None) -> None:
    """Hält einen Versand fest. Wirft nie."""
    try:
        adr = (an or "").strip().lower()
        if not adr or "@" not in adr:
            return
        with tx("system") as cur:
            if not kunden_id and not lead_id:
                cur.execute("""SELECT id FROM kunden WHERE lower(email) = %s UNION SELECT kunden_id FROM benutzer WHERE lower(email) = %s AND kunden_id IS NOT NULL LIMIT 1""", (adr, adr))
                r = cur.fetchone()
                if r:
                    kunden_id = r["id"]
                else:
                    cur.execute("SELECT id FROM leads WHERE lower(email) = %s ORDER BY erstellt_am DESC LIMIT 1", (adr,))
                    r = cur.fetchone()
                    lead_id = r["id"] if r else None
            if not kunden_id and not lead_id:
                return
            cur.execute("INSERT INTO mail_verlauf (kunden_id, lead_id, art, betreff, an, ok, fehler) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (kunden_id, lead_id, art_aus_betreff(art, betreff)[:30], re.sub(r"\s+", " ", betreff or "")[:200], adr[:254], ok, None if ok else (fehler or "")[:250]))
    except Exception:  # noqa: BLE001
        log.debug("Mail-Verlauf nicht geschrieben", exc_info=True)


def lesen(cur, kunden_id=None, lead_id=None, limit: int = 100) -> dict:
    """Verlauf und Zähler. Bei einem Kunden zählen auch die Mails aus der Zeit, als er noch Lead war."""
    if kunden_id:
        where, p = "(kunden_id = %s OR lead_id IN (SELECT id FROM leads WHERE kunden_id = %s))", (kunden_id, kunden_id)
    else:
        where, p = "lead_id = %s", (lead_id,)
    cur.execute(f"SELECT id, zeit, art, betreff, an, ok, fehler FROM mail_verlauf WHERE {where} ORDER BY zeit DESC LIMIT %s", (*p, limit))
    liste = cur.fetchall()
    cur.execute(f"SELECT art, count(*) AS n, count(*) FILTER (WHERE NOT ok) AS fehler, max(zeit) AS zuletzt FROM mail_verlauf WHERE {where} GROUP BY art ORDER BY n DESC", p)
    arten = cur.fetchall()
    return {"mails": liste, "arten": arten, "gesamt": sum(a["n"] for a in arten), "fehler": sum(a["fehler"] for a in arten)}
