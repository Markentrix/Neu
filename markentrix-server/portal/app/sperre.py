"""Sperrliste: Wer widersprochen hat, abgesagt hat oder sich abgemeldet hat, wird nicht erneut angesprochen (auch nicht über spätere Importe).
Vergleich über normalisierte E-Mail, Telefonnummer und Domain."""
import re
from urllib.parse import urlparse

FREEMAIL = {"gmail.com", "googlemail.com", "gmx.de", "gmx.net", "web.de", "t-online.de", "outlook.com", "outlook.de", "hotmail.com", "hotmail.de", "yahoo.de", "yahoo.com",
            "icloud.com", "me.com", "freenet.de", "posteo.de", "protonmail.com", "proton.me", "live.de", "online.de", "1und1.de", "arcor.de", "aol.com", "mail.de", "gmx.at", "gmx.ch"}


def telefon(t: str | None) -> str | None:
    z = re.sub(r"\D", "", t or "")
    if len(z) < 6:
        return None
    if z.startswith("00"):
        z = z[2:]
    elif z.startswith("0"):
        z = "49" + z[1:]
    return z


def mail(m: str | None) -> str | None:
    m = (m or "").strip().lower()
    return m if "@" in m else None


def domain(website: str | None = None, email: str | None = None) -> str | None:
    h = None
    w = (website or "").strip().lower()
    if w:
        h = urlparse(w if "//" in w else "//" + w).hostname
    if not h:
        return None
    h = h[4:] if h.startswith("www.") else h
    return None if h in FREEMAIL or "." not in h else h


def schluessel(email=None, tel=None, website=None) -> list[tuple[str, str]]:
    out = []
    if mail(email):
        out.append(("email", mail(email)))
    if telefon(tel):
        out.append(("telefon", telefon(tel)))
    d = domain(website, email)
    if d:
        out.append(("domain", d))
    return out


def eintragen(cur, grund: str, quelle: str = "", email=None, tel=None, website=None) -> int:
    n = 0
    for art, wert in schluessel(email, tel, website):
        cur.execute("INSERT INTO sperrliste (art, wert, grund, quelle) VALUES (%s,%s,%s,%s) ON CONFLICT (art, wert) DO NOTHING", (art, wert, grund, quelle[:200]))
        n += cur.rowcount
    return n


def treffer(cur, email=None, tel=None, website=None) -> dict | None:
    """Gibt den ersten Treffer (art, wert, grund) zurück oder None."""
    for art, wert in schluessel(email, tel, website):
        cur.execute("SELECT art, wert, grund FROM sperrliste WHERE art=%s AND wert=%s", (art, wert))
        r = cur.fetchone()
        if r:
            return r
    return None
