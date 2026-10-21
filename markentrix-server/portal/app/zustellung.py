"""Mail-Zustellbarkeit: Versandprotokoll (ohne Empfängeradressen) und Prüfung von SPF, DKIM und DMARC der Absender-Domains.
Rückläufer, die erst später vom Zielserver kommen (Bounces), sieht das Portal nicht; hier wird festgehalten, was der Versandserver sofort meldet."""
import json
import logging

from .db import tx

log = logging.getLogger("zustellung")
DKIM_SELEKTOREN = ["default", "mail", "dkim", "selector1", "selector2", "google", "k1", "k2", "s1", "s2", "mxvault", "smtp", "mandrill", "mailo", "everlytickey1"]


def fehlerart(text: str) -> str:
    t = (text or "").lower()
    if "recipientsrefused" in t or "user unknown" in t or "mailbox unavailable" in t or "no such user" in t or "550" in t or "553" in t:
        return "adresse"
    if "authentication" in t or "auth" in t and "535" in t:
        return "anmeldung"
    if "timeout" in t or "connect" in t or "refused" in t or "ssl" in t or "name or service" in t:
        return "verbindung"
    return "sonstiges"


def protokoll(kunden_id, art: str, an: str, ok: bool, fehler: str = ""):
    """Hält einen Versand fest. Wirft nie."""
    try:
        domain = (an or "").rsplit("@", 1)[-1].lower()[:120] or None
        with tx("system") as cur:
            cur.execute("INSERT INTO mail_protokoll (kunden_id, art, an_domain, ok, fehlerart, fehler) VALUES (%s,%s,%s,%s,%s,%s)",
                        (kunden_id, art[:30], domain, ok, None if ok else fehlerart(fehler), None if ok else (fehler or "")[:250]))
    except Exception:  # noqa: BLE001
        log.debug("Mailprotokoll nicht geschrieben", exc_info=True)


# ---------------------------------------------------------------- DNS
def txt(name: str) -> list[str] | None:
    """TXT-Einträge; [] wenn es keine gibt; None, wenn die Abfrage nicht möglich war (Netz, Zeitüberschreitung)."""
    try:
        import dns.exception
        import dns.resolver
    except ImportError:
        return None
    try:
        antwort = dns.resolver.resolve(name, "TXT", lifetime=5)
        return ["".join(p.decode("utf8", "replace") for p in r.strings) for r in antwort]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return []
    except dns.exception.DNSException:
        return None


def pruefen_domain(domain: str) -> dict:
    """Ergebnis je Verfahren: ok | warn | fehlt | unbekannt, dazu ein Satz Klartext."""
    domain = (domain or "").strip().lower().rstrip(".")
    out = {"domain": domain, "spf": "unbekannt", "dkim": "unbekannt", "dmarc": "unbekannt", "details": {}}
    t = txt(domain)
    if t is not None:
        spf = [x for x in t if x.lower().startswith("v=spf1")]
        if not spf:
            out["spf"], out["details"]["spf"] = "fehlt", "Kein SPF-Eintrag: Mailserver können nicht prüfen, ob der Versand von hier erlaubt ist. Viele Empfänger sortieren solche Mails in den Spam."
        elif len(spf) > 1:
            out["spf"], out["details"]["spf"] = "warn", "Mehrere SPF-Einträge: das ist ungültig und wird oft abgelehnt. Es darf nur einen geben."
        elif spf[0].lower().endswith("+all") or spf[0].lower().endswith(" ?all"):
            out["spf"], out["details"]["spf"] = "warn", "SPF erlaubt jeden Absender (+all / ?all). Besser ~all oder -all am Ende."
        else:
            out["spf"], out["details"]["spf"] = "ok", "SPF vorhanden."
    d = txt("_dmarc." + domain)
    if d is not None:
        eintrag = [x for x in d if x.lower().startswith("v=dmarc1")]
        if not eintrag:
            out["dmarc"], out["details"]["dmarc"] = "fehlt", "Kein DMARC-Eintrag. Empfehlung: v=DMARC1; p=none; rua=mailto:… (erst beobachten, später verschärfen)."
        elif "p=none" in eintrag[0].lower().replace(" ", ""):
            out["dmarc"], out["details"]["dmarc"] = "ok", "DMARC vorhanden (nur beobachtend, p=none)."
        else:
            out["dmarc"], out["details"]["dmarc"] = "ok", "DMARC vorhanden."
    gefunden, unklar = None, False
    for sel in DKIM_SELEKTOREN:
        k = txt(f"{sel}._domainkey.{domain}")
        if k is None:
            unklar = True
            break
        if any("v=dkim1" in x.lower() or "p=" in x.lower() for x in k):
            gefunden = sel
            break
    if gefunden:
        out["dkim"], out["details"]["dkim"] = "ok", f"DKIM-Schlüssel gefunden (Selector „{gefunden}“)."
    elif not unklar:
        out["dkim"], out["details"]["dkim"] = "fehlt", ("Kein DKIM-Schlüssel unter den üblichen Selektoren gefunden. Hat der Mailanbieter einen eigenen Selector, "
                                                         "ist das ein Fehlalarm; sonst DKIM beim Anbieter aktivieren und den Eintrag setzen.")
    return out


def speichern(cur, r: dict):
    cur.execute("""INSERT INTO mail_dns (domain, geprueft_am, spf, dkim, dmarc, details) VALUES (%s, now(), %s, %s, %s, %s::jsonb)
                   ON CONFLICT (domain) DO UPDATE SET geprueft_am = now(), spf = EXCLUDED.spf, dkim = EXCLUDED.dkim, dmarc = EXCLUDED.dmarc, details = EXCLUDED.details""",
                (r["domain"], r["spf"], r["dkim"], r["dmarc"], json.dumps(r["details"])))


def schlecht(r: dict) -> bool:
    return r["spf"] in ("fehlt", "warn") or r["dkim"] == "fehlt"


def lesen(cur, domain: str) -> dict | None:
    cur.execute("SELECT domain, geprueft_am, spf, dkim, dmarc, details FROM mail_dns WHERE domain=%s", ((domain or "").lower(),))
    return cur.fetchone()


def kennzahlen(cur, kid=None, tage: int = 7) -> dict:
    cur.execute("""SELECT count(*) AS gesamt, count(*) FILTER (WHERE NOT ok) AS fehler, count(*) FILTER (WHERE fehlerart = 'adresse') AS adresse,
                          count(*) FILTER (WHERE fehlerart IN ('anmeldung','verbindung')) AS technisch
                   FROM mail_protokoll WHERE zeit > now() - make_interval(days => %s) AND (%s::uuid IS NULL OR kunden_id = %s::uuid)""", (tage, kid, kid))
    z = cur.fetchone()
    cur.execute("""SELECT zeit, art, an_domain, fehlerart, fehler FROM mail_protokoll WHERE NOT ok AND zeit > now() - make_interval(days => %s) AND (%s::uuid IS NULL OR kunden_id = %s::uuid)
                   ORDER BY zeit DESC LIMIT 10""", (tage, kid, kid))
    return {"tage": tage, "gesamt": z["gesamt"], "fehler": z["fehler"], "adresse": z["adresse"], "technisch": z["technisch"], "letzte_fehler": cur.fetchall()}
