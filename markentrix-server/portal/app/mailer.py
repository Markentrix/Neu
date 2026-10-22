"""E-Mail-Versand über den eigenen SMTP-Zugang (Einstellungen im Admin-Bereich)."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from . import betrieb, config, einstellungen, zustellung
from .db import tx


def konfiguriert() -> bool:
    with tx("system") as cur:
        c = einstellungen.lesen(cur, "smtp")
    return bool(c.get("host") and c.get("absender"))


def senden(an: str, betreff: str, text: str, anhang: tuple[str, bytes, str] | None = None, reply_to: str | None = None,
           von_name: str | None = None, kunden_id=None, art: str = "system") -> tuple[bool, str]:
    """Gibt (ok, Fehlertext) zurück. Wirft nie. Das Ergebnis wird für die Betriebs-Ampel und das Zustell-Protokoll festgehalten."""
    ok, grund = _senden(an, betreff, text, anhang, reply_to, von_name)
    if grund != "E-Mail-Versand ist noch nicht eingerichtet.":
        zustellung.protokoll(kunden_id, art, an, ok, grund)
        betrieb.notieren("mail", {"ok_am": betrieb.jetzt()} if ok else {"fehler_am": betrieb.jetzt(), "fehler": grund[:200]})
    return ok, grund


def _senden(an: str, betreff: str, text: str, anhang: tuple[str, bytes, str] | None = None, reply_to: str | None = None,
            von_name: str | None = None) -> tuple[bool, str]:
    try:
        with tx("system") as cur:
            c = einstellungen.lesen(cur, "smtp")
        if not (c.get("host") and c.get("absender")):
            return False, "E-Mail-Versand ist noch nicht eingerichtet."
        msg = EmailMessage()
        msg["From"] = formataddr((von_name or c.get("absender_name") or "Markentrix", c["absender"]))
        if reply_to:
            msg["Reply-To"] = reply_to
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
            f"Danach melden Sie sich mit dieser E-Mail-Adresse unter {config.BASE_URL} an.\n\n"
            "Tipp: Am Handy können Sie das Portal wie eine App nutzen. Öffnen Sie es dazu auf Android in Google Chrome "
            "bzw. auf dem iPhone in Safari. Nach der Anmeldung zeigt Ihnen das Portal in wenigen Schritten mit Bildern, wie die Installation geht "
            "(Android: Menü ⋮ → „App installieren“, iPhone: Teilen → „Zum Home-Bildschirm“)." + SIGNATUR)
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


def lead_angebot(an: str, name: str | None, firma: str, nummer: str, pdf_bytes: bytes, dateiname: str, gueltig, link: str, absender: str, erinnerung: bool = False) -> tuple[bool, str]:
    hallo = f"Guten Tag {name}," if name else "Guten Tag,"
    if erinnerung:
        text = (f"{hallo}\n\nwir wollten kurz nachfragen, ob Sie unser Angebot {nummer} für {firma} schon ansehen konnten. Zur Sicherheit hängen wir es noch einmal an.\n\n"
                f"Hier können Sie es online ansehen und direkt annehmen:\n{link}\n\n"
                + (f"Das Angebot ist gültig bis zum {gueltig:%d.%m.%Y}.\n\n" if gueltig else "")
                + "Falls Sie Fragen haben oder etwas angepasst werden soll, antworten Sie einfach auf diese Mail." + SIGNATUR)
        return senden(an, f"Erinnerung: Ihr Angebot {nummer} von {absender}", text, (dateiname, pdf_bytes, "application/pdf"))
    text = (f"{hallo}\n\nvielen Dank für Ihr Interesse. Anbei erhalten Sie unser Angebot {nummer} für {firma} als PDF.\n\n"
            f"Sie können es auch online ansehen und dort direkt annehmen:\n{link}\n\n"
            + (f"Das Angebot ist gültig bis zum {gueltig:%d.%m.%Y}.\n\n" if gueltig else "")
            + "Bei Fragen melden Sie sich gern, wir sprechen alles in Ruhe durch." + SIGNATUR)
    return senden(an, f"Ihr Angebot {nummer} von {absender}", text, (dateiname, pdf_bytes, "application/pdf"))


def avv(an: str, name: str | None, pdf_bytes: bytes) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nanbei erhalten Sie den Vertrag zur Auftragsverarbeitung (AVV) nach Art. 28 DSGVO. Er regelt, wie wir personenbezogene Daten in Ihrem Auftrag verarbeiten.\n\n"
            "Bitte unterschreiben Sie ihn und senden Sie uns ihn unterschrieben zurück (Scan oder Foto genügt)." + SIGNATUR)
    return senden(an, "Vertrag zur Auftragsverarbeitung (AVV)", text, ("Auftragsverarbeitungsvertrag.pdf", pdf_bytes, "application/pdf"))


def vertrag_dokument(an: str, name: str | None, art: str, pdf_bytes: bytes, dateiname: str) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    if art == "referenz":
        text = (f"{hallo}\n\nanbei erhalten Sie unseren Referenzvertrag. Damit dürfen wir Ihr Projekt in unserer Eigenwerbung zeigen, aber nur, was Sie ausdrücklich freigeben.\n\n"
                "So geht es: Kreuzen Sie in Anlage 1 nur die Punkte an, die für Sie in Ordnung sind (alles andere bleibt tabu), und unterschreiben Sie. Das Formular lässt sich am Bildschirm ausfüllen. "
                "Senden Sie es uns anschließend unterschrieben zurück (Scan oder Foto genügt).\n\n"
                "Das ist freiwillig und völlig unabhängig von Ihrem Auftrag. Sie können es jederzeit ohne Begründung widerrufen, ohne dass Ihnen daraus ein Nachteil entsteht." + SIGNATUR)
        betreff = "Referenzvertrag: Ihre Freigabe für unsere Referenzen"
    else:
        text = (f"{hallo}\n\nanbei erhalten Sie den Handelsvertretervertrag für Ihre Zusammenarbeit mit Markentrix.\n\n"
                "Bitte lesen Sie ihn in Ruhe, ergänzen Sie Ihre Angaben (Anlage 3 mit den Fragen zu Ihrer Selbständigkeit) und unterschreiben Sie ihn. "
                "Das Formular lässt sich am Bildschirm ausfüllen. Senden Sie es uns anschließend unterschrieben zurück (Scan oder Foto genügt). Bei Fragen melden Sie sich jederzeit." + SIGNATUR)
        betreff = "Handelsvertretervertrag Markentrix"
    return senden(an, betreff, text, (dateiname, pdf_bytes, "application/pdf"), art="vertrag")


def avv_portal(an: str, name: str | None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nder Vertrag zur Auftragsverarbeitung (AVV) nach Art. 28 DSGVO liegt in Ihrem Portal zur Bestätigung bereit. "
            f"Sie können ihn dort lesen und mit einem Klick bestätigen, Drucken und Unterschreiben ist nicht nötig.\n\n{config.BASE_URL}/app#avv" + SIGNATUR)
    return senden(an, "Vertrag zur Auftragsverarbeitung: bitte bestätigen", text)


def website_aktualisiert(an: str, name: str | None, domain: str, hinweis: str, kid=None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    was = f"\n\nDas haben wir geändert:\n{hinweis}" if hinweis.strip() else ""
    text = (f"{hallo}\n\ndas Update Ihrer Website {domain} ist online.{was}\n\nBitte schauen Sie kurz drüber: https://{domain}\n\n"
            f"Wenn Ihnen etwas auffällt oder noch etwas fehlt, schreiben Sie uns einfach im Portal unter „Nachrichten“: {config.BASE_URL}/app#nachrichten" + SIGNATUR)
    return senden(an, f"Ihre Website ist aktualisiert: {domain}", text, kunden_id=kid, art="website")


def website_online(an: str, name: str | None, domain: str, hinweis: str, kid=None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    extra = f"\n\n{hinweis.strip()}" if hinweis.strip() else ""
    text = (f"{hallo}\n\nIhre neue Website ist online: https://{domain}{extra}\n\nSie ist ab sofort für alle erreichbar. Bitte schauen Sie sich alles in Ruhe an, auch am Handy. "
            f"Kleine Wünsche und Korrekturen schicken Sie uns bitte im Portal unter „Nachrichten“: {config.BASE_URL}/app#nachrichten\n\n"
            f"Tipp: Tragen Sie die neue Adresse in Ihre E-Mail-Signatur, auf Visitenkarten und in Ihr Google-Unternehmensprofil ein." + SIGNATUR)
    return senden(an, f"Ihre neue Website ist online: {domain}", text, kunden_id=kid, art="website")


def avv_erinnerung_kunde(an: str, name: str | None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    text = (f"{hallo}\n\nkleine Erinnerung: Der Vertrag zur Auftragsverarbeitung (AVV) wartet in Ihrem Portal noch auf Ihre Bestätigung. "
            f"Es dauert nur einen Klick: {config.BASE_URL}/app#avv\n\nOhne diesen Vertrag dürfen wir keine Daten Ihrer Kundinnen und Kunden verarbeiten." + SIGNATUR)
    return senden(an, "Erinnerung: AVV bitte bestätigen", text)


def willkommen_start(an: str, name: str | None, firma: str, punkte: list[str]) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    liste = "\n".join("- " + p for p in punkte)
    text = (f"{hallo}\n\nschön, dass {firma} dabei ist! Damit wir zügig starten können, brauchen wir von Ihnen:\n\n{liste}\n\n"
            f"Das meiste können Sie direkt in Ihrem Portal erledigen: {config.BASE_URL}/app. "
            f"Dort sehen Sie auch jederzeit, wie weit wir sind. Bei Fragen schreiben Sie uns einfach über „Nachrichten“ im Portal." + SIGNATUR)
    return senden(an, f"Willkommen bei Markentrix: so starten wir für {firma}", text)


def avv_bestaetigt_team(an: str, firma: str, kundennummer: str, name: str, kid: str) -> tuple[bool, str]:
    t = (f"{firma} ({kundennummer}) hat den AVV im Portal bestätigt (durch {name}).\n\nAnsehen im Admin-Bereich: {config.BASE_URL}/admin#kunde/{kid}" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"AVV bestätigt: {firma}", t)


def uav_aenderung(an: str, name: str | None, art: str, uav: str, leistung: str, wirksam: str, hinweis: str) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    was = "ein zusätzlicher Unterauftragsverarbeiter" if art == "neu" else "ein Wechsel eines Unterauftragsverarbeiters"
    text = (f"{hallo}\n\nnach Ziffer 5 unseres Vertrags zur Auftragsverarbeitung (AVV) informieren wir Sie vorab über eine geplante Änderung: {was}.\n\n"
            f"Unternehmen: {uav}\nLeistung: {leistung}\nGeplant ab: {wirksam}\n" + (f"\n{hinweis}\n" if hinweis else "") +
            f"\nSie können der Änderung bis zu diesem Datum aus wichtigem datenschutzrechtlichem Grund widersprechen, direkt im Portal unter „Datenschutz-Vertrag“: {config.BASE_URL}/app#avv\n"
            "Ohne Widerspruch gilt die Änderung als genehmigt. Bis zu einer Klärung setzen wir den neuen Anbieter für Sie nicht ein." + SIGNATUR)
    return senden(an, f"Information zur Auftragsverarbeitung: Änderung bei Unterauftragsverarbeitern ({uav})", text)


def uav_widerspruch_team(an: str, firma: str, kundennummer: str, uav: str, name: str, grund: str, kid: str) -> tuple[bool, str]:
    t = (f"{firma} ({kundennummer}) widerspricht der Änderung bei Unterauftragsverarbeitern: {uav}\n\nEingelegt von: {name}\nBegründung: {grund}\n\n"
         f"Der neue Anbieter darf für diesen Kunden nicht eingesetzt werden, bis das geklärt ist.\nAdmin-Bereich: {config.BASE_URL}/admin#kunde/{kid}" + "\n\n(automatische Meldung des Portals)")
    return senden(an, f"Widerspruch gegen Unterauftragsverarbeiter: {firma}", t)


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


def mahn_text(titel: str, nummer: str, name: str | None = None) -> str:
    """Vorgeschlagener Mailtext zur Zahlungserinnerung oder Mahnung (vor dem Versand bearbeitbar)."""
    hallo = f"Guten Tag {name}," if name else "Guten Tag,"
    return (f"{hallo}\n\nzur Rechnung {nummer} finden Sie im Anhang eine {titel}." + "\n\nSollte sich die Zahlung mit dieser Nachricht überschnitten haben, betrachten Sie sie bitte als gegenstandslos." + SIGNATUR)


def mahnung(an: str, titel: str, nummer: str, pdf_bytes: bytes, dateiname: str, text: str | None = None, name: str | None = None) -> tuple[bool, str]:
    return senden(an, f"{titel} zu Rechnung {nummer}", text or mahn_text(titel, nummer, name), (dateiname, pdf_bytes, "application/pdf"))


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


def freigabe_anfrage_kunde(an: str, name: str | None, titel: str, link: str | None = None) -> tuple[bool, str]:
    hallo = f"Hallo {name}," if name else "Hallo,"
    t = (f"{hallo}\n\nwir bitten um Ihre Freigabe: {titel}\n\n")
    if link:
        t += (f"Direkt ansehen und freigeben, ohne Anmeldung (Link 14 Tage gültig):\n{link}\n\n"
              f"Oder im Portal: {config.BASE_URL}/app#freigaben" + SIGNATUR)
    else:
        t += ("Bitte sehen Sie es sich im Portal an und geben Sie es frei oder teilen Sie uns mit, was geändert werden soll: "
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


def mandat_bestaetigt(an: str, name: str | None, referenz: str, iban_ende: str, glaeubiger_id: str, firma: str) -> tuple[bool, str]:
    text = (f"{'Hallo ' + name + ',' if name else 'Guten Tag,'}\n\nSie haben {firma} ein SEPA-Lastschriftmandat erteilt. Zur Bestätigung:\n\n"
            f"Mandatsreferenz: {referenz}\nGläubiger-Identifikationsnummer: {glaeubiger_id}\nKonto: ...{iban_ende}\n\n"
            "Rechnungen werden künftig von diesem Konto eingezogen. Vor jedem Einzug erhalten Sie eine Ankündigung mit Betrag und Datum. "
            "Sie können das Mandat jederzeit im Kundenportal unter Angebote & Rechnungen widerrufen." + SIGNATUR)
    return senden(an, "Bestätigung Ihres SEPA-Lastschriftmandats", text)


def lastschrift_vorab(an: str, name: str | None, positionen: list, datum, referenz: str, glaeubiger_id: str, firma: str) -> tuple[bool, str]:
    summe = sum(p[1] for p in positionen)
    zeilen = "\n".join(f"- Rechnung {n}: {c / 100:.2f} EUR".replace(".", ",") for n, c in positionen)
    text = (f"{'Hallo ' + name + ',' if name else 'Guten Tag,'}\n\nwir ziehen am {datum:%d.%m.%Y} per SEPA-Lastschrift ein:\n\n{zeilen}\n"
            f"Gesamt: {summe / 100:.2f} EUR\n\n".replace(".", ",") +
            f"Mandatsreferenz: {referenz}\nGläubiger-Identifikationsnummer: {glaeubiger_id}\nEinzug durch: {firma}\n\n"
            "Bitte sorgen Sie für ausreichende Deckung auf dem Konto." + SIGNATUR)
    return senden(an, f"Ankündigung Lastschrift am {datum:%d.%m.%Y}", text)
