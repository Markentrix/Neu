"""Kontaktergebnis zu einem Lead festhalten (Angerufen, Mail, Termin …): Verlaufseintrag, Status und Wiedervorlage in einem Schritt."""
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from . import sperre

VERLUSTGRUENDE = {"kein_bedarf": "Kein Bedarf", "zu_teuer": "Zu teuer", "hat_anbieter": "Hat schon einen Anbieter", "spaeter": "Später / aktuell kein Thema", "falscher_ansprechpartner": "Falscher Ansprechpartner", "sonstiges": "Sonstiges"}

# code, Beschriftung, Art im Verlauf, neuer Status (nur wenn der Lead noch davor steht), Tage bis zur Wiedervorlage (None = keine, 0 = löschen)
OPTIONEN = [
    ("anruf_erreicht", "Angerufen: erreicht", "anruf", "kontaktiert", 3),
    ("anruf_nicht_erreicht", "Angerufen: nicht erreicht", "anruf", None, 2),
    ("anruf_mailbox", "Angerufen: Nachricht hinterlassen", "anruf", "kontaktiert", 3),
    ("mail_gesendet", "E-Mail geschickt", "mail_gesendet", "kontaktiert", 3),
    ("antwort", "Hat geantwortet", "antwort", "antwort", 2),
    ("termin", "Termin vereinbart", "termin", "termin", 3),
    ("angebot", "Angebot geschickt", "notiz", "angebot", 5),
    ("rueckruf", "Bittet um Rückruf", "notiz", "antwort", 1),
    ("kein_interesse", "Kein Interesse", "notiz", "verloren", 0),
    ("widerspruch", "Widerspricht der Ansprache / bittet um Löschung", "notiz", "gesperrt", 0),   # kommt auf die Sperrliste
    ("falsche_nummer", "Nummer falsch / nicht erreichbar", "notiz", "tot", 0),   # wird abgelegt (Status „tot“): taucht in keiner Anrufliste mehr auf
]
_NACH = {o[0]: o for o in OPTIONEN}
# Reihenfolge der Status: ein Ergebnis setzt den Status nur vor, nie zurück
_RANG = {"neu": 0, "kontaktiert": 1, "antwort": 2, "termin": 3, "angebot": 4}
TZ = ZoneInfo("Europe/Berlin")
ZEIT = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
GESPERRT = ("gewonnen", "gesperrt", "consent_ausstehend")


def optionen_fuer_oberflaeche() -> list:
    return [{"code": c, "text": t, "wiedervorlage_tage": w} for c, t, _a, _s, w in OPTIONEN]


def erfassen(cur, lid, ergebnis: str, notiz: str | None, wiedervorlage: date | None, von: str, darf_status: bool = True, verlust_grund: str | None = None, zeit: str | None = None) -> dict:
    o = _NACH.get(ergebnis)
    if not o:
        raise HTTPException(400, "Unbekanntes Ergebnis.")
    _c, text, art, neuer_status, tage = o
    if verlust_grund and verlust_grund not in VERLUSTGRUENDE:
        raise HTTPException(400, "Unbekannter Grund.")
    cur.execute("SELECT status, firma, email, telefon, website, wiedervorlage_am FROM leads WHERE id=%s", (lid,))
    l = cur.fetchone()
    if not l:
        raise HTTPException(404, "Lead nicht gefunden.")
    if wiedervorlage and wiedervorlage < date.today():
        raise HTTPException(400, "Die Wiedervorlage liegt in der Vergangenheit.")
    if zeit and not ZEIT.match(zeit):
        raise HTTPException(400, "Die Uhrzeit ist ungültig (Format 14:30).")
    if zeit and not wiedervorlage:
        raise HTTPException(400, "Für eine Uhrzeit bitte auch das Datum der Wiedervorlage wählen.")
    inhalt = text + (": " + notiz.strip() if notiz and notiz.strip() else "")
    if verlust_grund and neuer_status == "verloren":
        inhalt += f" (Grund: {VERLUSTGRUENDE[verlust_grund]})"
    cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von, ergebnis) VALUES (%s,%s,%s,%s,%s)", (lid, art, inhalt[:2000], von, ergebnis))
    status = l["status"]
    if darf_status and neuer_status and status not in GESPERRT:
        if neuer_status in ("verloren", "tot", "gesperrt") or _RANG.get(neuer_status, 0) > _RANG.get(status, 0):
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)", (lid, f"{status} → {neuer_status}", von))
            status = neuer_status
    if wiedervorlage:
        wv = wiedervorlage
    elif tage:
        wv = date.today() + timedelta(days=tage)
    else:
        wv = l["wiedervorlage_am"]       # eine bestehende Wiedervorlage bleibt erhalten
    if tage == 0 or status in ("verloren", "gewonnen", "gesperrt", "tot"):
        wv = None
    rueckruf = None
    if zeit and wv:
        rueckruf = datetime.combine(wv, time(int(zeit[:2]), int(zeit[3:])), tzinfo=TZ)
        if rueckruf <= datetime.now(TZ):
            raise HTTPException(400, "Die vereinbarte Uhrzeit liegt in der Vergangenheit.")
    neu_gesetzt = bool(zeit or wiedervorlage or tage) or wv is None   # sonst bleibt eine bestehende Rückrufzeit erhalten
    # Aktivität verlängert die Löschfrist (nur wenn der Lead eine hat)
    cur.execute("""UPDATE leads SET status=%s, wiedervorlage_am=%s, letzter_kontakt_am=now(),
                          rueckruf_am = CASE WHEN %s THEN %s ELSE rueckruf_am END, rueckruf_push = CASE WHEN %s THEN 0 ELSE rueckruf_push END,
                          loeschen_nach = CASE WHEN loeschen_nach IS NOT NULL THEN greatest(loeschen_nach, current_date + interval '12 months') END,
                          verlust_grund = CASE WHEN %s = 'verloren' THEN %s ELSE verlust_grund END WHERE id=%s""", (status, wv, neu_gesetzt, rueckruf, neu_gesetzt, status, verlust_grund, lid))
    if ergebnis in ("kein_interesse", "widerspruch") and neuer_status:
        sperre.eintragen(cur, "kein_interesse" if ergebnis == "kein_interesse" else "widerspruch", f"Lead {lid}", l["email"], l["telefon"], l["website"])
    return {"status": status, "wiedervorlage_am": wv, "rueckruf_am": rueckruf}
