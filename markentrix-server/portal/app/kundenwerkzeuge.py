"""Kunden-Werkzeuge: Standard-Antwortvorlagen und Text der Bewertungsbitte (reine Textlogik, ohne Versand)."""
import re

STANDARD_VORLAGEN = [
    ("termin", "Termin bestätigen", "Guten Tag {name}, vielen Dank für Ihre Anfrage bei {firma}. Gerne bestätigen wir Ihnen einen Termin. Passt Ihnen {tag}? Bitte geben Sie uns kurz Bescheid. Freundliche Grüße, {firma}"),
    ("rueckruf", "Rückruf zusagen", "Guten Tag {name}, vielen Dank für Ihre Nachricht. Wir rufen Sie morgen im Laufe des Tages zurück. Freundliche Grüße, {firma}"),
    ("pruefen", "Wir melden uns", "Guten Tag {name}, vielen Dank für Ihre Anfrage bei {firma}. Wir schauen uns das an und melden uns bis spätestens übermorgen bei Ihnen. Freundliche Grüße, {firma}"),
    ("rueckfrage", "Rückfrage stellen", "Guten Tag {name}, danke für Ihre Anfrage bei {firma}. Damit wir Ihnen genau helfen können, brauchen wir noch eine Information: Worum genau geht es, und bis wann soll es erledigt sein? Freundliche Grüße, {firma}"),
    ("absage", "Freundlich absagen", "Guten Tag {name}, vielen Dank für Ihr Interesse an {firma}. Leider können wir Ihr Anliegen derzeit nicht übernehmen. Wir wünschen Ihnen alles Gute. Freundliche Grüße, {firma}"),
]

STANDARD_BEWERTUNG = ("Guten Tag {name}, vielen Dank, dass Sie bei {firma} waren. Wenn Sie zufrieden waren, würden wir uns über eine kurze Bewertung freuen: {link} "
                      "Das ist freiwillig. Freundliche Grüße, {firma}")

_PLATZ = re.compile(r"\{(\w+)\}")


def fuellen(text: str, **werte) -> str:
    """Ersetzt {platzhalter}; unbekannte bleiben stehen, fehlende Werte werden leer."""
    return _PLATZ.sub(lambda m: str(werte.get(m.group(1), m.group(0)) or ""), text or "").strip()


def vorname(name: str | None) -> str:
    n = (name or "").strip()
    return n if n else "Kundin, Kunde"


def kanal_aus_kontakt(kontakt: str | None) -> str:
    k = (kontakt or "").strip()
    if "@" in k:
        return "mail"
    return "telefon" if re.search(r"\d{5,}", re.sub(r"[\s/().-]", "", k)) else "unbekannt"
