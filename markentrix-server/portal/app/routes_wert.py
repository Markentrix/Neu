"""„Das hat Markentrix dir gebracht“: nachvollziehbare Zahlen aus dem Portal für die Startseite des Kunden. Nichts davon ist geschätzt, außer der gekennzeichneten Zeitersparnis."""
from datetime import date

from fastapi import APIRouter, Depends

from . import berichte
from .db import tx
from .security import require_kunde

router = APIRouter(prefix="/api/kunde")

MINUTEN_JE_VORGANG = 3     # grobe Annahme für die Zeitersparnis; im Portal als Schätzung gekennzeichnet
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def zahlen(cur, kid, von: date, bis: date) -> dict:
    cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status<>'spam'", (kid, von, bis))
    anfragen = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status='spam'", (kid, von, bis))
    spam = cur.fetchone()["n"]
    cur.execute("""SELECT count(*) FILTER (WHERE richtung='aus' AND agent_lauf_id IS NOT NULL) AS automatisch FROM nachrichten
                   WHERE kunden_id=%s AND zeit >= %s AND zeit < %s""", (kid, von, bis))
    automatisch = cur.fetchone()["automatisch"]
    cur.execute("""SELECT count(*) FILTER (WHERE status IN ('gebucht','reserviert')) AS gebucht,
                          count(*) FILTER (WHERE ergebnis='erschienen') AS erschienen,
                          count(*) FILTER (WHERE ergebnis='nicht_erschienen') AS nicht_erschienen,
                          coalesce(sum(preis_betrag) FILTER (WHERE ergebnis='erschienen'), 0) AS umsatz,
                          coalesce(sum(erinnerung), 0) AS erinnerungen
                   FROM website_termine WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s""", (kid, von, bis))
    wt = cur.fetchone()
    cur.execute("""SELECT coalesce(sum(anzahlung_betrag), 0) AS summe, count(*) AS n FROM website_termine
                   WHERE kunden_id=%s AND anzahlung_erhalten_am >= %s AND anzahlung_erhalten_am < %s""", (kid, von, bis))
    az = cur.fetchone()
    cur.execute("SELECT count(*) AS n FROM website_warteliste WHERE kunden_id=%s AND benachrichtigt_am >= %s AND benachrichtigt_am < %s", (kid, von, bis))
    warte = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM bewertungsanfragen WHERE kunden_id=%s AND gesendet_am >= %s AND gesendet_am < %s", (kid, von, bis))
    bewertungen = cur.fetchone()["n"]
    vorgaenge = automatisch + int(wt["gebucht"]) + int(wt["erinnerungen"]) + warte + bewertungen
    return {"anfragen": anfragen, "spam_abgefangen": spam, "automatisch_beantwortet": automatisch,
            "termine_gebucht": int(wt["gebucht"]), "erschienen": int(wt["erschienen"]), "nicht_erschienen": int(wt["nicht_erschienen"]),
            "umsatz_erschienen": float(wt["umsatz"]), "erinnerungen": int(wt["erinnerungen"]),
            "anzahlungen_summe": float(az["summe"]), "anzahlungen_anzahl": az["n"],
            "warteliste_benachrichtigt": warte, "bewertungsanfragen": bewertungen,
            "stunden_gespart": round(vorgaenge * MINUTEN_JE_VORGANG / 60, 1), "vorgaenge": vorgaenge}


@router.get("/wertbilanz")
def wertbilanz(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    heute = date.today()
    von, bis = berichte.monat_grenzen(heute)
    vvon, vbis = berichte.monat_grenzen(berichte.vormonat(heute))
    with tx("system") as cur:
        dieser, letzter = zahlen(cur, kid, von, bis), zahlen(cur, kid, vvon, vbis)
    return {"monat_name": f"{MONATE[heute.month - 1]} {heute.year}", "vormonat_name": f"{MONATE[vvon.month - 1]} {vvon.year}",
            "dieser": dieser, "letzter": letzter, "minuten_je_vorgang": MINUTEN_JE_VORGANG}
