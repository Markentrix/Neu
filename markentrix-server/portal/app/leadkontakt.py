"""Kontaktergebnis zu einem Lead festhalten (Angerufen, Mail, Termin …): Verlaufseintrag, Status und Wiedervorlage in einem Schritt."""
from datetime import date, timedelta

from fastapi import HTTPException

# code, Beschriftung, Art im Verlauf, neuer Status (nur wenn der Lead noch davor steht), Tage bis zur Wiedervorlage (None = keine, 0 = löschen)
OPTIONEN = [
    ("anruf_erreicht", "Angerufen: erreicht", "anruf", "kontaktiert", None),
    ("anruf_nicht_erreicht", "Angerufen: nicht erreicht", "anruf", None, 2),
    ("anruf_mailbox", "Angerufen: Nachricht hinterlassen", "anruf", "kontaktiert", 3),
    ("mail_gesendet", "E-Mail geschickt", "mail_gesendet", "kontaktiert", 3),
    ("antwort", "Hat geantwortet", "antwort", "antwort", None),
    ("termin", "Termin vereinbart", "termin", "termin", None),
    ("angebot", "Angebot geschickt", "notiz", "angebot", 5),
    ("rueckruf", "Bittet um Rückruf", "notiz", "antwort", 1),
    ("kein_interesse", "Kein Interesse", "notiz", "verloren", 0),
    ("falsche_nummer", "Nummer falsch / nicht erreichbar", "notiz", None, 0),
]
_NACH = {o[0]: o for o in OPTIONEN}
# Reihenfolge der Status: ein Ergebnis setzt den Status nur vor, nie zurück
_RANG = {"neu": 0, "kontaktiert": 1, "antwort": 2, "termin": 3, "angebot": 4}
GESPERRT = ("gewonnen", "gesperrt", "consent_ausstehend")


def optionen_fuer_oberflaeche() -> list:
    return [{"code": c, "text": t, "wiedervorlage_tage": w} for c, t, _a, _s, w in OPTIONEN]


def erfassen(cur, lid, ergebnis: str, notiz: str | None, wiedervorlage: date | None, von: str, darf_status: bool = True) -> dict:
    o = _NACH.get(ergebnis)
    if not o:
        raise HTTPException(400, "Unbekanntes Ergebnis.")
    _c, text, art, neuer_status, tage = o
    cur.execute("SELECT status, firma FROM leads WHERE id=%s", (lid,))
    l = cur.fetchone()
    if not l:
        raise HTTPException(404, "Lead nicht gefunden.")
    if wiedervorlage and wiedervorlage < date.today():
        raise HTTPException(400, "Die Wiedervorlage liegt in der Vergangenheit.")
    inhalt = text + (": " + notiz.strip() if notiz and notiz.strip() else "")
    cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s)", (lid, art, inhalt[:2000], von))
    status = l["status"]
    if darf_status and neuer_status and status not in GESPERRT:
        if neuer_status == "verloren" or _RANG.get(neuer_status, 0) > _RANG.get(status, 0):
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)", (lid, f"{status} → {neuer_status}", von))
            status = neuer_status
    if wiedervorlage:
        wv = wiedervorlage
    elif tage:
        wv = date.today() + timedelta(days=tage)
    else:
        wv = None
    if tage == 0 or status in ("verloren", "gewonnen"):
        wv = None
    cur.execute("UPDATE leads SET status=%s, wiedervorlage_am=%s, letzter_kontakt_am=now() WHERE id=%s", (status, wv, lid))
    return {"status": status, "wiedervorlage_am": wv}
