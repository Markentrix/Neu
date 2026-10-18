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


def senden(an: str, betreff: str, text: str) -> tuple[bool, str]:
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
