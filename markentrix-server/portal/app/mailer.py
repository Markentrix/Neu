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
    if rolle == "kunde":
        wofuer = "Ihr Zugang zum Markentrix-Kundenportal ist eingerichtet."
    elif rolle == "vertrieb":
        wofuer = ("Ihr Zugang zum Markentrix-Vertriebsportal ist eingerichtet. Dort sehen Sie Ihre Leads, halten fest, wer angerufen wurde oder einen Termin hat, "
                  "und behalten Ihre Kunden und Provisionen im Blick.")
    else:
        wofuer = "Ihr Zugang zum Markentrix-Portal ist eingerichtet."
    text = (f"{hallo}\n\n{wofuer}\n\nBitte legen Sie über diesen Link Ihr Passwort fest "
            f"(der Link ist {tage} Tage gültig und nur einmal nutzbar):\n\n{link}\n\n"
            f"Danach melden Sie sich mit dieser E-Mail-Adresse unter {config.BASE_URL} an." + SIGNATUR)
    return senden(an, "Ihr Zugang zum Markentrix-Vertriebsportal" if rolle == "vertrieb" else "Ihr Zugang zum Markentrix-Portal", text)


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


def avv(an: str, name: str | None, pdf_bytes: bytes) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nanbei erhalten Sie den Vertrag zur Auftragsverarbeitung (AVV) nach Art. 28 DSGVO. Er regelt, wie wir personenbezogene Daten in Ihrem Auftrag verarbeiten.\n\n"
            "Bitte unterschreiben Sie ihn und senden Sie uns ihn unterschrieben zurück (Scan oder Foto genügt)." + SIGNATUR)
    return senden(an, "Vertrag zur Auftragsverarbeitung (AVV)", text, ("Auftragsverarbeitungsvertrag.pdf", pdf_bytes, "application/pdf"))


def avv_portal(an: str, name: str | None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nder Vertrag zur Auftragsverarbeitung (AVV) nach Art. 28 DSGVO liegt in Ihrem Portal zur Bestätigung bereit. "
            f"Sie können ihn dort lesen und mit einem Klick bestätigen, Drucken und Unterschreiben ist nicht nötig.\n\n{config.BASE_URL}/app#avv" + SIGNATUR)
    return senden(an, "Vertrag zur Auftragsverarbeitung: bitte bestätigen", text)


def avv_bestaetigt_team(an: str, firma: str, kundennummer: str, name: str, kid: str) -> tuple[bool, str]:
    t = (f"{firma} ({kundennummer}) hat den AVV im Portal bestätigt (durch {name}).\n\nAnsehen im Admin-Bereich: {config.BASE_URL}/admin#kunde/{kid}" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"AVV bestätigt: {firma}", t)


def onboarding_erinnerung_kunde(an: str, name: str | None, offen: list[str]) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nfür einen guten Start fehlt uns von Ihnen noch Folgendes: bitte " + " und ".join(offen) + f".\n\nDas geht direkt im Portal: {config.BASE_URL}/app\n\nWenn Sie Hilfe brauchen, schreiben Sie uns einfach dort eine Nachricht." + SIGNATUR)
    return senden(an, "Für Ihren Start fehlt noch etwas", text)


def lead_folge(an: str, name: str | None, firma: str, betreff: str, text: str, token: str) -> tuple[bool, str]:
    kopf = {"name": name or "Sie", "firma": firma, "buchen": config.BASE_URL.rstrip("/") + "/buchen"}
    try:
        body = text.format(**kopf)
    except (KeyError, IndexError, ValueError):
        body = text
    abmelden = config.BASE_URL.rstrip("/") + "/api/public/abmelden?t=" + token
    return senden(an, betreff, body + SIGNATUR + f"\n\n--\nSie möchten dazu nichts mehr von uns erhalten? Hier abmelden: {abmelden}")


def kunden_feedback(an: str, name: str | None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nSie sind jetzt seit gut einem Monat bei uns. Wie läuft es aus Ihrer Sicht? Im Portal können Sie uns in zehn Sekunden eine Bewertung geben, "
            f"und jederzeit eine Nachricht schreiben, wenn etwas fehlt: {config.BASE_URL}/app" + SIGNATUR)
    return senden(an, "Wie läuft es bei Ihnen?", text)


def mahnung(an: str, titel: str, nummer: str, pdf_bytes: bytes, dateiname: str) -> tuple[bool, str]:
    text = (f"Guten Tag,\n\nzur Rechnung {nummer} finden Sie im Anhang eine {titel}.\n\nSollte sich die Zahlung mit dieser Nachricht überschnitten haben, betrachten Sie sie bitte als gegenstandslos." + SIGNATUR)
    return senden(an, f"{titel} zu Rechnung {nummer}", text, (dateiname, pdf_bytes, "application/pdf"))


# ---------------------------------------------------------------- Zusammenarbeit (Nachrichten, Freigaben, Aufgaben)
def _kurz(text: str, n: int = 400) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n].rstrip() + " …"


def ticket_neu_team(an: str, nr: str, firma: str, kundennummer: str, betreff: str, art: str, text: str) -> tuple[bool, str]:
    t = (f"Neue Nachricht von {firma} ({kundennummer}), {art}:\n\n{nr}: {betreff}\n\n{_kurz(text)}\n\n"
         f"Antworten im Admin-Bereich: {config.BASE_URL}/admin#postfach" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"Neu: {nr} {betreff} ({firma})", t)


def ticket_antwort_team(an: str, nr: str, firma: str, betreff: str, text: str) -> tuple[bool, str]:
    t = (f"{firma} hat auf {nr} ({betreff}) geantwortet:\n\n{_kurz(text)}\n\nAdmin-Bereich: {config.BASE_URL}/admin#postfach" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"Antwort: {nr} {betreff} ({firma})", t)


def ticket_antwort_kunde(an: str, name: str | None, nr: str, betreff: str, text: str, erledigt: bool = False) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    t = (f"{hallo}\n\nzu Ihrer Nachricht {nr} ({betreff}) gibt es eine Antwort von uns:\n\n{_kurz(text)}\n\n" +
         ("Wir haben die Anfrage damit als erledigt markiert. Wenn noch etwas offen ist, antworten Sie einfach im Portal.\n\n" if erledigt else "") +
         f"Sie können direkt im Portal antworten: {config.BASE_URL}/app#nachrichten" + SIGNATUR)
    return senden(an, f"Antwort zu {nr}: {betreff}", t)


def ticket_erledigt_kunde(an: str, name: str | None, nr: str, betreff: str) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    t = (f"{hallo}\n\nIhre Anfrage {nr} ({betreff}) ist erledigt.\n\nWenn noch etwas offen ist, antworten Sie einfach im Portal, dann öffnen wir sie wieder. "
         f"Über eine kurze Bewertung freuen wir uns: {config.BASE_URL}/app#nachrichten" + SIGNATUR)
    return senden(an, f"Erledigt: {nr} {betreff}", t)


def freigabe_anfrage_kunde(an: str, name: str | None, titel: str) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    t = (f"{hallo}\n\nwir bitten um Ihre Freigabe: {titel}\n\nBitte sehen Sie es sich im Portal an und geben Sie es frei oder teilen Sie uns mit, was geändert werden soll: "
         f"{config.BASE_URL}/app#freigaben" + SIGNATUR)
    return senden(an, f"Bitte um Freigabe: {titel}", t)


def freigabe_erinnerung_kunde(an: str, name: str | None, titel: str) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    t = (f"{hallo}\n\nzur Erinnerung: Wir warten noch auf Ihre Freigabe für \"{titel}\".\n\nIm Portal geht es mit zwei Klicks: {config.BASE_URL}/app#freigaben" + SIGNATUR)
    return senden(an, f"Erinnerung: Freigabe {titel}", t)


def freigabe_entschieden_team(an: str, firma: str, titel: str, status: str, kommentar: str | None, wer: str) -> tuple[bool, str]:
    ergebnis = "freigegeben" if status == "freigegeben" else "abgelehnt (Änderungswunsch)"
    t = (f"{firma} hat \"{titel}\" {ergebnis} (durch {wer}).\n" + (f"\nKommentar: {kommentar}\n" if kommentar else "") +
         f"\nAdmin-Bereich: {config.BASE_URL}/admin#freigaben" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"Freigabe {ergebnis}: {titel} ({firma})", t)


def aufgaben_digest_team(an: str, zeilen: list[str]) -> tuple[bool, str]:
    t = ("Neue Aufgaben im Portal:\n\n" + "\n".join(f"- {z}" for z in zeilen) + f"\n\nAlle Aufgaben: {config.BASE_URL}/admin#aufgaben" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"{len(zeilen)} neue Aufgabe" + ("n" if len(zeilen) != 1 else ""), t)


def stammdaten_geaendert_team(an: str, firma: str, kundennummer: str, aenderung: str) -> tuple[bool, str]:
    t = f"{firma} ({kundennummer}) hat Stammdaten im Portal geändert:\n\n{aenderung}\n\nBitte bei Rechnungen und Verträgen beachten.\n\n(automatische Meldung des Portals)"
    return senden(an, f"Stammdaten geändert: {firma}", t)


def briefing_team(an: str, firma: str, kundennummer: str, kid: str) -> tuple[bool, str]:
    t = (f"{firma} ({kundennummer}) hat das Briefing abgeschickt.\n\nAnsehen im Admin-Bereich: {config.BASE_URL}/admin#kunde/{kid}" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"Briefing abgeschickt: {firma}", t)


def website_check_team(an: str, name: str, firma: str, email: str, website: str, score, neu: bool, lead_id: str) -> tuple[bool, str]:
    t = (f"{'Neuer Lead' if neu else 'Wiederholter Website-Check'} über markentrix.de:\n\nName: {name or '-'}\nFirma: {firma}\nE-Mail: {email}\nGeprüfte Website: {website or '-'}\nErgebnis: {score if score is not None else '-'} von 100\n\n"
         f"Ansehen im Admin-Bereich: {config.BASE_URL}/admin#lead/{lead_id}" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"{'Neuer Lead' if neu else 'Website-Check'}: {firma} ({website or 'ohne Website'})", t)
