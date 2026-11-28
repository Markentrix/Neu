"""Stammdaten-Check: Sind die Angaben eines Kunden vollständig und brauchbar? Rechnungen, Mails und Erinnerungen hängen daran."""
import re

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def pruefen(k: dict, mail_fehler_30: int = 0) -> dict:
    """k = Zeile aus kunden. mail_fehler_30 = fehlgeschlagene Mails an die hinterlegte Adresse in den letzten 30 Tagen."""
    def leer(f):
        return not (k.get(f) or "").strip()
    ziffern = re.sub(r"\D", "", k.get("telefon") or "")
    punkte = [
        ("ansprechpartner", not leer("ansprechpartner"), "Ansprechpartner fehlt (für die Anrede in Mails und Rechnungen)."),
        ("email", not leer("email") and bool(EMAIL.match((k.get("email") or "").strip())), "E-Mail-Adresse fehlt oder ist ungültig."),
        ("email_funktioniert", mail_fehler_30 == 0, f"Mails an diese Adresse sind {mail_fehler_30}× fehlgeschlagen. Adresse prüfen und mit dem Kunden klären."),
        ("telefon", len(ziffern) >= 6, "Telefonnummer fehlt oder ist zu kurz."),
        ("strasse", not leer("strasse"), "Straße und Hausnummer fehlen (Pflicht auf Rechnungen)."),
        ("plz", bool(re.fullmatch(r"\d{5}", (k.get("plz") or "").strip())), "PLZ fehlt oder hat keine 5 Ziffern."),
        ("ort", not leer("ort"), "Ort fehlt."),
        ("branche", not leer("branche"), "Branche fehlt (hilft bei Texten und Auswertungen)."),
    ]
    if k.get("status") == "aktiv":
        punkte.append(("domain", not leer("domain"), "Keine Domain hinterlegt."))
    liste = [{"feld": f, "ok": ok, "text": t} for f, ok, t in punkte]
    return {"punkte": liste, "ok": sum(1 for p in liste if p["ok"]), "gesamt": len(liste)}
