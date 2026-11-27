"""Nächster Schritt je Lead: eine klare Empfehlung (anrufen, nachfassen, Termin vorschlagen …) aus dem, was im Portal schon bekannt ist.
Nur ein Vorschlag zur Orientierung, nichts wird automatisch versendet."""
from datetime import date, datetime, timezone

ENDE = {"gesperrt", "consent_ausstehend", "tot", "verloren", "gewonnen"}


def _tage(d) -> int:
    if d is None:
        return 0
    if isinstance(d, datetime):
        return (datetime.now(timezone.utc) - d).days
    return (date.today() - d).days


def berechnen(cur, l: dict) -> dict | None:
    """Gibt {"text", "grund", "aktion"} zurück oder None, wenn nichts mehr zu tun ist. aktion: anrufen, mail, terminvorschlag, kalender, angebot, daten, warten."""
    if l.get("kunden_id") or l["status"] in ENDE:
        return None
    lid = l["id"]
    cur.execute("SELECT start FROM gespraechstermine WHERE lead_id=%s AND status='gebucht' AND start > now() ORDER BY start LIMIT 1", (lid,))
    g = cur.fetchone()
    if g:
        return {"aktion": "kalender", "text": "Beratungsgespräch vorbereiten", "grund": "Termin am " + g["start"].astimezone().strftime("%d.%m.%Y um %H:%M") + " Uhr steht. Website-Check und Notizen vorher ansehen."}
    cur.execute("""SELECT status, versendet_am, angesehen_am FROM belege WHERE lead_id=%s AND art='angebot' AND status IN ('gestellt','versendet') ORDER BY coalesce(versendet_am, erstellt_am) DESC LIMIT 1""", (lid,))
    b = cur.fetchone()
    if b:
        tage = _tage(b["versendet_am"])
        if b["angesehen_am"]:
            return {"aktion": "anrufen", "text": "Angebot nachfassen: heute anrufen", "grund": "Das Angebot wurde angesehen, aber noch nicht beantwortet."}
        if tage >= 3:
            return {"aktion": "anrufen", "text": "Angebot nicht geöffnet: kurz anrufen", "grund": f"Das Angebot ging vor {tage} Tagen raus und wurde noch nicht angesehen. Vielleicht ist die Mail nicht angekommen."}
        return {"aktion": "warten", "text": "Auf Antwort zum Angebot warten", "grund": "Das Angebot ging gerade erst raus."}
    cur.execute("""SELECT erstellt_am, nachfass_anzahl FROM terminvorschlaege WHERE lead_id=%s AND status='offen' AND gesendet ORDER BY erstellt_am DESC LIMIT 1""", (lid,))
    v = cur.fetchone()
    if v:
        tage = _tage(v["erstellt_am"])
        if tage >= 2:
            return {"aktion": "anrufen", "text": "Terminvorschlag nachfassen", "grund": f"Die Terminvorschläge sind seit {tage} Tagen unbeantwortet. Ein kurzer Anruf klärt es meist schneller als eine Mail."}
        return {"aktion": "warten", "text": "Auf Antwort zu den Terminvorschlägen warten", "grund": "Die Vorschläge gingen gerade erst raus."}
    if l.get("wiedervorlage_am") and l["wiedervorlage_am"] <= date.today():
        return {"aktion": "anrufen", "text": "Wiedervorlage ist fällig: anrufen", "grund": "Für heute oder früher war ein Nachfassen vorgemerkt."}
    if not l.get("telefon") and not l.get("email"):
        return {"aktion": "daten", "text": "Kontaktdaten ergänzen", "grund": "Es ist weder Telefon noch E-Mail hinterlegt."}
    cur.execute("SELECT ergebnis FROM lead_aktivitaeten WHERE lead_id=%s AND ergebnis IS NOT NULL ORDER BY zeit DESC LIMIT 1", (lid,))
    a = cur.fetchone()
    letzt = (a or {}).get("ergebnis") or ""
    if l["status"] == "neu" and not a:
        if l.get("telefon"):
            return {"aktion": "anrufen", "text": "Erster Anruf", "grund": "Der Lead ist neu und wurde noch nicht kontaktiert."}
        return {"aktion": "mail", "text": "Erste Mail schreiben", "grund": "Es gibt keine Telefonnummer, nur eine E-Mail-Adresse."}
    if letzt == "rueckruf":
        return {"aktion": "anrufen", "text": "Zurückrufen", "grund": "Der Lead hat um einen Rückruf gebeten."}
    if letzt in ("anruf_erreicht", "antwort"):
        return {"aktion": "terminvorschlag", "text": "Beratungstermin vorschlagen", "grund": "Der Lead war erreichbar und ist noch ohne Termin. Drei Zeiten per Mail schicken, ein Klick genügt."}
    if letzt == "anruf_nicht_erreicht":
        return {"aktion": "anrufen", "text": "Noch einmal anrufen", "grund": "Beim letzten Mal wurde niemand erreicht. Am besten zu einer anderen Tageszeit."}
    if l.get("telefon"):
        return {"aktion": "anrufen", "text": "Nachfassen", "grund": "Seit dem letzten Kontakt gibt es keinen festen nächsten Schritt. Wiedervorlage setzen oder anrufen."}
    return {"aktion": "mail", "text": "Nachfassen per Mail", "grund": "Kein fester nächster Schritt vorgemerkt."}
