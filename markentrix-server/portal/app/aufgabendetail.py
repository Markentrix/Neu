"""Erklärt zu jeder automatisch angelegten Team-Aufgabe, WAS genau offen ist (für die Sammelmail „neue Aufgaben“)."""
from datetime import date

from . import config
from .onboarding import KUNDE_AKTION


def _tage(zeit) -> int:
    return max(0, (date.today() - zeit.date()).days) if zeit else 0


def _kunde_link(kid) -> str:
    return f"{config.BASE_URL}/admin#kunde/{kid}" if kid else f"{config.BASE_URL}/admin#aufgaben"


def _onboarding(cur, kid) -> list[str]:
    cur.execute("SELECT erstellt_am FROM kunden WHERE id=%s", (kid,))
    k = cur.fetchone()
    cur.execute("SELECT code, titel, erledigt FROM onboarding_punkte WHERE kunden_id=%s ORDER BY sortierung, id", (kid,))
    punkte = cur.fetchall()
    offen = [p for p in punkte if not p["erledigt"]]
    zeilen = [f"Seit {_tage(k['erstellt_am'])} Tagen im Onboarding, {len(punkte) - len(offen)} von {len(punkte)} Schritten erledigt."] if k else []
    if offen:
        zeilen.append("Noch offen:")
        for p in offen[:12]:
            zeilen.append("- " + p["titel"] + (" (Kunde ist am Zug: " + KUNDE_AKTION[p["code"]][1] + ")" if p["code"] in KUNDE_AKTION else ""))
    return zeilen


def beschreibe(cur, a: dict) -> dict:
    """a: Zeile der neuen Aufgabe (id, kunden_id, ticket_id, titel). Gibt {'detail': [Zeilen], 'link': Adresse} zurück. Fehler hier dürfen den Versand nie verhindern."""
    titel, kid = a["titel"], a.get("kunden_id")
    detail: list[str] = []
    link = _kunde_link(kid)
    try:
        if titel.startswith(("Onboarding nachfassen:", "Kunde anrufen (Stillstand")) and kid:
            detail = _onboarding(cur, kid)
        elif titel.startswith("Zugang prüfen") and kid:
            cur.execute("SELECT k.erstellt_am, k.email FROM kunden k WHERE k.id=%s", (kid,))
            k = cur.fetchone()
            if k:
                detail = [f"Der Kunde hat sein Passwort noch nicht gesetzt (angelegt vor {_tage(k['erstellt_am'])} Tagen, Einladung an {k['email']}).",
                          "Im Kundenblatt unter „Zugänge“ die Einladung neu senden oder den Kunden anrufen."]
        elif titel.startswith(("Antworten:", "Nachfassen:")) and a.get("ticket_id"):
            cur.execute("SELECT betreff, status, geaendert_am FROM tickets WHERE id=%s", (a["ticket_id"],))
            t = cur.fetchone()
            cur.execute("SELECT von, text, erstellt_am FROM ticket_nachrichten WHERE ticket_id=%s AND NOT intern ORDER BY id DESC LIMIT 1", (a["ticket_id"],))
            n = cur.fetchone()
            if t:
                detail = [f"Betreff: {t['betreff']}", f"Seit {_tage(t['geaendert_am'])} Tag(en) ohne Bewegung."]
                if n:
                    detail += [("Letzte Nachricht vom Kunden:" if n["von"] == "kunde" else "Unsere letzte Nachricht:"), (n["text"][:300] + ("…" if len(n["text"]) > 300 else ""))]
                link = f"{config.BASE_URL}/admin#postfach"
        elif titel.startswith("Rechnung ") and kid:
            nummer = titel.split(" ")[1]
            cur.execute("SELECT brutto_cent, faellig_am, status FROM belege WHERE kunden_id=%s AND nummer=%s AND art='rechnung'", (kid, nummer))
            b = cur.fetchone()
            if b:
                tage = (date.today() - b["faellig_am"]).days if b["faellig_am"] else 0
                detail = [f"Betrag: {b['brutto_cent'] / 100:.2f} € brutto".replace(".", ","), f"Fällig war: {b['faellig_am'].strftime('%d.%m.%Y') if b['faellig_am'] else '–'} (vor {tage} Tagen)",
                          "Nächster Schritt: Zahlungserinnerung senden oder beim Kunden nachfragen."]
        elif titel.startswith("Keine Buchung, keine Provision") and kid:
            detail = ["Der Kunde wurde von einem Vertriebler gebracht, hat aber noch keine laufende Buchung. Ohne Buchung entsteht keine Provision.", "Nächster Schritt: Angebot/Buchung im Kundenblatt anlegen."]
        elif titel.startswith("Angebot") or titel.startswith("Gespräch-Ergebnis"):
            link = f"{config.BASE_URL}/admin#leads"
    except Exception:  # noqa: BLE001  (Hinweistext ist nur eine Hilfe)
        detail = []
    return {"titel": titel, "detail": detail, "link": link}
