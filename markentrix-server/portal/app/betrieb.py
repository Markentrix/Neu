"""Betriebsstatus: kleine Messpunkte (Herzschlag der Hintergrundjobs, letzter Mailversand) für die Ampel im Admin."""
import json
import logging
from datetime import datetime, timezone

from .db import tx

log = logging.getLogger("markentrix.betrieb")


def notieren(schluessel: str, wert: dict | None = None) -> None:
    """Setzt den Zeitpunkt auf jetzt und führt wert in die gespeicherten Angaben ein. Wirft nie."""
    try:
        with tx("system") as cur:
            cur.execute("""INSERT INTO betrieb_status (schluessel, wert, am) VALUES (%s, %s::jsonb, now())
                           ON CONFLICT (schluessel) DO UPDATE SET wert = betrieb_status.wert || EXCLUDED.wert, am = now()""",
                        (schluessel, json.dumps(wert or {})))
    except Exception:  # Messpunkte dürfen nie den eigentlichen Vorgang stören
        log.debug("Betriebsstatus %s konnte nicht gespeichert werden", schluessel, exc_info=True)


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def lesen(cur, schluessel: str) -> dict | None:
    cur.execute("SELECT wert, am, EXTRACT(EPOCH FROM (now() - am)) AS sekunden FROM betrieb_status WHERE schluessel=%s", (schluessel,))
    r = cur.fetchone()
    return {"wert": r["wert"], "am": r["am"], "sekunden": int(r["sekunden"])} if r else None
