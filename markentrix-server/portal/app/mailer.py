"""E-Mail-Versand über den eigenen SMTP-Zugang (Einstellungen im Admin-Bereich)."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from . import config, einstellungen
from .db import tx


def konfiguriert() -> bool:
    with tx("system") as cur:
        c = einstellungen.lesen(cur, "smtp")
    return bool(c.get("host") and c.get("absender"))


def senden(an: str, betreff: str, text: str, anhang: tuple[str, bytes, str] | None = None) -> tuple[bool, str]:
    """Gibt (ok, Fehlertext) zurück. Wirft nie."""
    try:
        with tx("system") as cur:
            c = einstellungen.lesen(cur, "smtp")
        if not (c.get("host") and c.get("absender")):
            return False, "E-Mail-Versand ist noch nicht eingerichtet."
        msg = EmailMessage()
        msg["From"] = formataddr((c.get("absender_name") or "Markentrix", c["absender"]))
        msg["To"] = an
        msg["Subject"] = betreff
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=c["absender"].split("@")[-1])
        msg.set_content(text)
        if anhang:
            name, daten, mime = anhang
            maintype, subtype = mime.split("/")
            msg.add_attachment(daten, maintype=maintype, subtype=subtype, filename=name)
        host, port, mode = c["host"], int(c.get("port") or 587), c.get("sicherung", "starttls")
        ctx = ssl.create_default_context()
        if mode == "ssl":
            s = smtplib.SMTP_SSL(host, port, timeout=20, context=ctx)
        else:
            s = smtplib.SMTP(host, port, timeout=20)
        with s:
            s.ehlo()
            if mode == "starttls":
                s.starttls(context=ctx)
                s.ehlo()
            if c.get("benutzer"):
                s.login(c["benutzer"], c.get("passwort", ""))
            s.send_message(msg)
        return True, ""
    except Exception as e:  # bewusst breit: der Aufrufer zeigt nur den Text an
        return False, f"{type(e).__name__}: {str(e)[:200]}"


SIGNATUR = "\n\nViele Grüße\nIhr Markentrix-Team"


def einladung(an: str, name: str | None, link: str, rolle: str, tage: int) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    wofuer = "Ihr Zugang zum Markentrix-Kundenportal ist eingerichtet." if rolle == "kunde" else "Ihr Zugang zum Markentrix-Partnerportal ist eingerichtet."
    text = (f"{hallo}\n\n{wofuer}\n\nBitte legen Sie über diesen Link Ihr Passwort fest "
            f"(der Link ist {tage} Tage gültig und nur einmal nutzbar):\n\n{link}\n\n"
            f"Danach melden Sie sich mit dieser E-Mail-Adresse unter {config.BASE_URL} an." + SIGNATUR)
    return senden(an, "Ihr Zugang zum Markentrix-Portal", text)


def passwort_zuruecksetzen(an: str, link: str) -> tuple[bool, str]:
    text = (f"Hallo,\n\nfür Ihr Konto wurde das Zurücksetzen des Passworts angefordert.\n\n"
            f"Über diesen Link legen Sie ein neues Passwort fest (gültig {config.RESET_HOURS} Stunden):\n\n{link}\n\n"
            "Wenn Sie das nicht angefordert haben, können Sie diese E-Mail ignorieren." + SIGNATUR)
    return senden(an, "Passwort zurücksetzen – Markentrix-Portal", text)


def neue_anfragen(an: str, firma: str, anfragen: list) -> tuple[bool, str]:
    zeilen = []
    for a in anfragen:
        zeilen.append(f"- {a.get('name') or 'Unbekannt'} ({a.get('kontakt') or 'ohne Kontaktangabe'}) über {a.get('quelle')}\n  {(a.get('nachricht') or '').strip()[:300]}")
    n = len(anfragen)
    text = (f"Hallo,\n\nüber {firma} " + ("ist eine neue Anfrage eingegangen:" if n == 1 else f"sind {n} neue Anfragen eingegangen:") +
            "\n\n" + "\n\n".join(zeilen) + f"\n\nAlle Anfragen sehen Sie im Portal: {config.BASE_URL}/app#anfragen" + SIGNATUR)
    return senden(an, "Neue Anfrage" if n == 1 else f"{n} neue Anfragen", text)


def termin_erinnerung(an: str, termine: list) -> tuple[bool, str]:
    zeilen = [f"- {t['beginn'].strftime('%d.%m.%Y um %H:%M')} Uhr: {t['titel']}" + (f" ({t['kontakt_name']})" if t.get("kontakt_name") else "") for t in termine]
    text = ("Hallo,\n\nzur Erinnerung, diese Termine stehen bald an:\n\n" + "\n".join(zeilen) + f"\n\nIhre Termine: {config.BASE_URL}/app#termine" + SIGNATUR)
    return senden(an, "Erinnerung: anstehende Termine", text)


def monatsbericht(an: str, firma: str, monat: str, pdf: bytes, dateiname: str) -> tuple[bool, str]:
    text = (f"Hallo,\n\nanbei Ihr Monatsbericht für {monat}: was bei {firma} über Ihre Website, Anfragen und Automatisierungen gelaufen ist.\n\n"
            f"Den Bericht finden Sie auch jederzeit im Portal: {config.BASE_URL}/app#berichte\n\nBei Fragen melden Sie sich gern." + SIGNATUR)
    return senden(an, f"Ihr Monatsbericht {monat}", text, (dateiname, pdf, "application/pdf"))


def beleg(an: str, art: str, nummer: str, name: str | None, pdf_bytes: bytes, dateiname: str, faellig=None, angebot_link: bool = False) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    if art == "angebot":
        text = (f"{hallo}\n\nanbei unser Angebot {nummer}." + (f"\n\nSie können es im Kundenportal ansehen und dort direkt annehmen: {config.BASE_URL}/app#belege" if angebot_link else "") +
                "\n\nBei Fragen melden Sie sich gern." + SIGNATUR)
        return senden(an, f"Angebot {nummer}", text, (dateiname, pdf_bytes, "application/pdf"))
    text = (f"{hallo}\n\nanbei erhalten Sie die Rechnung {nummer}." + (f"\nBitte überweisen Sie den Betrag bis zum {faellig:%d.%m.%Y}." if faellig else "") +
            "\n\nBei Fragen melden Sie sich gern." + SIGNATUR)
    return senden(an, f"Rechnung {nummer}", text, (dateiname, pdf_bytes, "application/pdf"))


def mahnung(an: str, titel: str, nummer: str, pdf_bytes: bytes, dateiname: str) -> tuple[bool, str]:
    text = (f"Guten Tag,\n\nzur Rechnung {nummer} finden Sie im Anhang eine {titel}.\n\nSollte sich die Zahlung mit dieser Nachricht überschnitten haben, betrachten Sie sie bitte als gegenstandslos." + SIGNATUR)
    return senden(an, f"{titel} zu Rechnung {nummer}", text, (dateiname, pdf_bytes, "application/pdf"))
