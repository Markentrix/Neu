"""Fehlerhilfe: erkennt einen Fehler am Text, sagt in einfachen Worten was los ist und was man tun kann.

Zentrale Stelle für alle Fehler im Portal (unerwartete Fehler, Hintergrundjobs, Mailversand, Website-Dienste).
Die Regeln sind bewusst eine einfache Liste: erste passende Regel gewinnt, am Ende steht ein allgemeiner Hinweis.
Gespeichert wird nie mehr als ein kurzer, von Zugangsdaten bereinigter Text.
"""
import json
import logging
import re
import secrets
import time

log = logging.getLogger("markentrix.fehlerhilfe")

# (id, Muster, Titel, Ursache, [Schritte], wer behebt es)
REGELN: list[tuple[str, str, str, str, list[str], str]] = [
    ("smtp_login", r"SMTPAuthenticationError|\b535\b|authentication (failed|unsuccessful)|Username and Password not accepted|BadCredentials",
     "Mail-Anmeldung abgelehnt", "Der Mailserver nimmt Benutzername oder Passwort nicht an.",
     ["Admin → Einstellungen → E-Mail öffnen und Benutzer und Passwort prüfen.", "Bei Gmail: kein normales Passwort, sondern ein App-Passwort verwenden (2-Faktor muss bei Google an sein).", "Danach „Test-Mail senden“ klicken."], "admin"),
    ("smtp_verbindung", r"SMTP.*(ConnectionRefused|ConnectionReset|timed out|gaierror|Name or service)|SMTPServerDisconnected|SMTPConnectError|ConnectionRefusedError.*(25|465|587)|Connection unexpectedly closed|getaddrinfo failed.*smtp|Name or service not known.*smtp",
     "Mailserver nicht erreichbar", "Die Verbindung zum Mailserver kommt nicht zustande (falscher Host, falscher Port oder der Anbieter blockiert).",
     ["Admin → Einstellungen → E-Mail: Server, Port und Verschlüsselung prüfen (587 = STARTTLS, 465 = SSL).", "Bei IONOS/Gmail die Angaben aus der Anbieter-Hilfe vergleichen.", "Sperrt der Hetzner-Server Port 25/465/587? Dann einen anderen Anbieter-Port nutzen."], "admin"),
    ("smtp_empfaenger", r"SMTPRecipientsRefused|SMTPSenderRefused|\b55[0-4]\b.*(recipient|mailbox|user unknown|rejected)|Recipient address rejected|mailbox unavailable",
     "Mail abgelehnt", "Die Adresse des Empfängers (oder der Absender) wurde vom Mailserver nicht angenommen.",
     ["Die E-Mail-Adresse beim Kunden/Besucher auf Tippfehler prüfen.", "Ist die Absenderadresse in Einstellungen → E-Mail beim Anbieter erlaubt? (Gmail: muss zum Konto passen.)"], "admin"),
    ("smtp_limit", r"\b(421|450|451|452|454)\b.*(rate|limit|too many|quota|try again)|Daily user sending (quota|limit)|sending limit",
     "Mail-Limit erreicht", "Der Mailanbieter hat das Tageslimit erreicht oder bremst den Versand.",
     ["Ein paar Stunden warten, danach geht es von selbst weiter.", "Bei Dauerproblemen auf einen Anbieter mit höherem Limit wechseln."], "admin"),
    ("tls", r"SSLError|CERTIFICATE_VERIFY_FAILED|certificate (has expired|verify failed)|SSLCertVerificationError",
     "Zertifikat-Problem", "Ein Sicherheitszertifikat ist ungültig oder abgelaufen (eigene Domain oder Gegenstelle).",
     ["Betrifft es eine Kundendomain: DNS prüfen (Domain muss auf 5.75.146.212 zeigen), dann Admin → Websites & Demos → „Jetzt prüfen“.", "Betrifft es den Mailserver: Server-Name exakt wie beim Anbieter eintragen.", "Auf dem Server: `sudo mkctl selbsttest` zeigt das Zertifikat."], "admin"),
    ("datenbank_verbindung", r"OperationalError.*(connect|connection|could not|server closed)|psycopg.*(connection|timeout)|too many connections|the database system is (starting|shutting)",
     "Datenbank nicht erreichbar", "Das Portal erreicht die Datenbank nicht (läuft gerade neu oder ist überlastet).",
     ["Auf dem Server: `sudo mkctl status` und `docker logs mk-db --tail 50` ansehen.", "Hilft das nicht: `sudo mkctl restart`.", "Bleibt es: `sudo mkctl restore-test` zeigt, ob die Sicherung heil ist, bevor man weiter eingreift."], "server"),
    ("platte_voll", r"No space left on device|disk full|could not extend file|ENOSPC",
     "Festplatte voll", "Auf dem Server ist kein Platz mehr, deshalb schlagen Speichern und Hochladen fehl.",
     ["Auf dem Server: `df -h` und `docker system df` ansehen.", "Alte Docker-Reste löschen: `docker image prune -a` (laufende Container bleiben).", "Alte Sicherungen unter /opt/markentrix/backups prüfen und Platz schaffen, nötigenfalls Server-Speicher in Hetzner vergrößern."], "server"),
    ("eindeutig", r"UniqueViolation|duplicate key|already exists|Dublette",
     "Eintrag gibt es schon", "Dieselben Daten (z. B. Telefonnummer, E-Mail, Domain) sind schon vorhanden.",
     ["Den vorhandenen Eintrag suchen und dort weiterarbeiten statt neu anzulegen.", "Bei Domains: gehört sie schon einem anderen Kunden?"], "admin"),
    ("rechte", r"InsufficientPrivilege|permission denied for|row-level security|new row violates row-level",
     "Keine Berechtigung in der Datenbank", "Eine Abfrage wurde von den Datenbank-Rechten (Row-Level-Security) gestoppt, meist nach einem Update ohne Migration.",
     ["Auf dem Server: `sudo mkctl migrate` ausführen und die Aktion wiederholen.", "Tritt es weiter auf, ist es ein Programmfehler: Meldung samt Fehler-Nr. an den Entwickler geben."], "server"),
    ("migration", r"UndefinedTable|UndefinedColumn|relation \".*\" does not exist|column \".*\" does not exist",
     "Datenbank nicht auf dem neuesten Stand", "Das Portal ist neuer als die Datenbank: eine Migration fehlt.",
     ["Auf dem Server: `sudo mkctl migrate`.", "Danach `sudo mkctl selbsttest`."], "server"),
    ("ki_schluessel", r"(401|403).*(anthropic|openai|api[_ -]?key)|invalid[_ -]?api[_ -]?key|authentication_error|Incorrect API key",
     "KI-Schlüssel ungültig", "Der hinterlegte KI-Schlüssel wird vom Anbieter nicht akzeptiert.",
     ["Admin → Einstellungen → KI: Schlüssel neu eintragen (aus dem Anbieter-Konto kopieren).", "Prüfen, ob das Guthaben/Abo beim Anbieter aktiv ist."], "admin"),
    ("ki_limit", r"\b429\b|rate_limit|overloaded|insufficient_quota|credit balance",
     "KI gerade überlastet oder Guthaben leer", "Der KI-Anbieter bremst (zu viele Anfragen) oder das Guthaben ist aufgebraucht.",
     ["Kurz warten und erneut versuchen.", "Guthaben/Limit im Konto des KI-Anbieters prüfen und bei Bedarf aufladen."], "admin"),
    ("paypal", r"paypal|PAYPAL",
     "Problem mit PayPal", "Die PayPal-Anbindung antwortet mit einem Fehler (Zugangsdaten, Konto oder Betrag).",
     ["Admin → Einstellungen → Zahlung: Client-ID und Secret prüfen (live, nicht Sandbox).", "Beim PayPal.Me-Link: Name exakt wie im Link, ohne Leerzeichen."], "admin"),
    ("caddy", r"caddy|Caddyfile|reload.*(failed|error)|admin API",
     "Webserver-Eintrag fehlerhaft", "Der Webserver (Caddy) konnte die Domain-Einstellung nicht übernehmen.",
     ["Auf dem Server: `docker logs server-caddy-1 --tail 50` ansehen.", "Domain richtig geschrieben? Admin → Websites & Demos: Eintrag prüfen, dann erneut veröffentlichen."], "server"),
    ("dns", r"NXDOMAIN|Temporary failure in name resolution|Name or service not known|getaddrinfo failed|gaierror",
     "Adresse nicht auflösbar (DNS)", "Ein Servername oder eine Domain wird im Internet nicht gefunden.",
     ["Domain beim Anbieter (INWX/IONOS) prüfen: A-Eintrag auf 5.75.146.212, www ebenfalls.", "DNS braucht nach Änderungen bis zu einigen Stunden. Danach „Jetzt prüfen“ im Admin."], "admin"),
    ("jobs_still", r"Hintergrundjobs|\bjob\b.*(fehlgeschlagen|stehen)",
     "Hintergrundjobs laufen nicht", "Die automatischen Aufgaben (Erinnerungen, Mails, Sicherungs-Checks) melden sich nicht oder brechen ab.",
     ["Auf dem Server: `docker logs mk-portal --tail 100` ansehen, dort steht der Grund des Abbruchs.", "Dann `sudo mkctl restart`.", "Danach `sudo mkctl selbsttest`."], "server"),
    ("verbindung_verweigert", r"ConnectionRefusedError|ConnectionResetError|ConnectError|Connection refused|Errno 111",
     "Verbindung verweigert", "Der Dienst, zu dem das Portal sich verbinden will, nimmt keine Verbindung an (er läuft nicht, falscher Port oder gesperrt).",
     ["Handelt es sich um den Mailversand: Admin → Einstellungen → E-Mail, Server und Port prüfen.", "Handelt es sich um n8n oder die Datenbank: auf dem Server `sudo mkctl status` ansehen und mit `sudo mkctl restart` neu starten.", "Danach `sudo mkctl selbsttest`."], "server"),
    ("zeitueberschreitung", r"ReadTimeout|ConnectTimeout|TimeoutError|timed out|Timeout",
     "Zeitüberschreitung", "Eine Gegenstelle hat nicht rechtzeitig geantwortet.",
     ["Meist vorübergehend: nach ein paar Minuten erneut versuchen.", "Tritt es dauernd bei derselben Aktion auf: `docker logs mk-portal --tail 100` und Fehler-Nr. an den Entwickler."], "admin"),
    ("n8n", r"\bn8n\b",
     "Problem im Automations-Workflow", "Ein n8n-Workflow ist fehlgeschlagen oder nicht erreichbar.",
     ["Admin → Datenschutz & Qualität → Workflow-Fehler: Knoten und Text ansehen.", "Auf dem Server: `docker logs mk-n8n --tail 50`.", "Zugangsdaten im betroffenen Workflow erneuern (häufigste Ursache)."], "admin"),
    ("datei_fehlt", r"FileNotFoundError|No such file or directory|IsADirectoryError",
     "Datei oder Ordner fehlt", "Das Portal sucht eine Datei, die nicht (mehr) da ist.",
     ["Bei Website-Uploads: ZIP erneut hochladen.", "Auf dem Server: `sudo mkctl status` und prüfen, ob /srv/sites und /opt/markentrix vollständig sind."], "server"),
    ("dateirechte", r"PermissionError|Permission denied|Errno 13",
     "Keine Schreibrechte", "Das Portal darf in einen Ordner nicht schreiben.",
     ["Auf dem Server: `sudo bash install.sh` im Ordner /root/Neu/markentrix-server stellt die Rechte wieder her."], "server"),
    ("speicher", r"MemoryError|Cannot allocate memory|(?-i:\bOOM\b)|(?-i:\bKilled\b)",
     "Arbeitsspeicher knapp", "Dem Server geht der Arbeitsspeicher aus.",
     ["Auf dem Server: `free -h` und `docker stats --no-stream` ansehen.", "Große Uploads/Importe in kleinere Teile aufteilen; bei Dauerproblem Server-Typ in Hetzner vergrößern."], "server"),
    ("ungueltige_daten", r"ValidationError|JSONDecodeError|ValueError|invalid input syntax|Invalid (date|time|format)",
     "Ungültige Eingabe", "Eine Eingabe oder Datei hatte ein Format, das das Portal nicht verarbeiten kann.",
     ["Eingabe prüfen (Datum, Zahl, E-Mail) und erneut versuchen.", "Bei Importen: die Datei wie in der Vorlage aufbauen (CSV, UTF-8)."], "admin"),
    ("einstellungen_defekt", r"InvalidToken|Fernet|PORTAL_SECRET",
     "Gespeicherte Einstellungen nicht lesbar", "Der Schlüssel PORTAL_SECRET passt nicht zu den verschlüsselten Einstellungen (er wurde geändert oder fehlt).",
     ["In /opt/markentrix/.env den ursprünglichen PORTAL_SECRET wiederherstellen (aus der getrennt aufbewahrten Sicherung der .env).", "Niemals neu erzeugen, sonst sind SMTP-, KI- und Kalenderdaten verloren und müssen neu eingegeben werden."], "server"),
]
ALLGEMEIN = ("allgemein", "Unerwarteter Fehler", "Der Fehler ist nicht bekannt. Er wurde mit einer Fehler-Nr. protokolliert.",
             ["Aktion einmal wiederholen.", "Hilft das nicht: `sudo docker logs mk-portal --tail 100` auf dem Server ansehen und die Fehler-Nr. mit dem Text an den Entwickler geben.", "Mit `sudo mkctl selbsttest` prüfen, ob sonst etwas auffällt."], "server")

_GEHEIM = re.compile(r"(?i)(passwor[dt]|passwd|secret|token|api[_-]?key|authorization|bearer)(\s*[=:]\s*|\s+)([^\s,;'\"]{3,})")
_LANG = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")
_ERKANNT = [(r[0], re.compile(r[1], re.I), r) for r in REGELN]
_letzte: dict = {}


def bereinigen(text) -> str:
    """Entfernt Passwörter, Schlüssel und lange Zeichenketten aus Fehlertexten, bevor sie gespeichert oder angezeigt werden."""
    t = _GEHEIM.sub(lambda m: m.group(1) + m.group(2) + "***", str(text or ""))
    return _LANG.sub("***", t)[:600]


def erklaeren(text) -> dict:
    """Erste passende Regel (oder der allgemeine Hinweis). Immer ein Ergebnis mit id, titel, ursache, schritte, wer."""
    t = str(text or "")
    for rid, muster, r in _ERKANNT:
        if muster.search(t):
            return {"id": rid, "titel": r[2], "ursache": r[3], "schritte": list(r[4]), "wer": r[5], "bekannt": True}
    return {"id": ALLGEMEIN[0], "titel": ALLGEMEIN[1], "ursache": ALLGEMEIN[2], "schritte": list(ALLGEMEIN[3]), "wer": ALLGEMEIN[4], "bekannt": False}


def kurztipp(text) -> str:
    """Ein Satz für Protokollzeilen (z. B. im Kundenportal). Leer, wenn der Fehler nicht erkannt wurde."""
    e = erklaeren(text)
    return f"Tipp: {e['schritte'][0]}" if e["bekannt"] and e["schritte"] else ""


def melden(quelle: str, exc_oder_text, titel: str | None = None, stufe: str = "warnung", sperre_sek: int = 1800, push_senden: bool = True, sperre_von: str = "") -> str:
    """Legt einen Alarm mit Erklärung und Lösungsvorschlag an. Gibt die Fehler-Nr. zurück (auch wenn wegen der Sperre kein neuer Alarm entsteht).
    Je Quelle und Fehlerart höchstens ein Alarm pro sperre_sek. Wirft nie."""
    nr = secrets.token_hex(3).upper()
    try:
        text = f"{type(exc_oder_text).__name__}: {exc_oder_text}" if isinstance(exc_oder_text, BaseException) else str(exc_oder_text or "")
        e = erklaeren(text)
        schluessel = f"{sperre_von or quelle}|{e['id']}"
        jetzt = time.time()
        if jetzt - _letzte.get(schluessel, 0) < sperre_sek:
            return nr
        _letzte[schluessel] = jetzt
        from . import push
        from .db import tx
        with tx("system") as cur:
            details = {"fehler_nr": nr, "text": bereinigen(text), "erklaerung": {k: e[k] for k in ("id", "titel", "ursache", "schritte", "wer")}}
            cur.execute("INSERT INTO alarme (stufe, quelle, titel, details) VALUES (%s,%s,%s,%s::jsonb)",
                        (stufe if stufe in ("info", "warnung", "kritisch") else "warnung", quelle[:60], (titel or e["titel"])[:200], json.dumps(details)))
            if push_senden:
                push.senden(push.admins(cur), e["titel"], e["schritte"][0][:140] + " (Admin → Datenschutz & Qualität → Alarme)", "/admin#compliance", "fehler")
    except Exception:  # noqa: BLE001 - die Fehlerhilfe darf nie selbst einen Fehler auslösen
        log.debug("Fehlerhilfe konnte nicht melden", exc_info=True)
    return nr
