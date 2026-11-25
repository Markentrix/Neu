"""Alarme anlegen, ohne dieselbe Meldung immer wieder neu aufzulisten: Gleiches wird hochgezählt, Behobenes schließt sich selbst."""
import hashlib
import json


def schluessel(quelle: str, titel: str, text: str = "") -> str:
    return f"{quelle}|{titel}|{hashlib.md5((text or '').encode()).hexdigest()}"


def eintragen(cur, stufe: str, quelle: str, titel: str, details: dict, kanaele: list | None = None, text: str = "") -> bool:
    """Legt einen Alarm an. Gibt True zurück, wenn er neu ist, False, wenn ein offener Alarm nur hochgezählt wurde."""
    s = schluessel(quelle, titel, text)
    cur.execute("UPDATE alarme SET anzahl = anzahl + 1, zuletzt = now(), stufe = %s WHERE id = (SELECT id FROM alarme WHERE schluessel = %s AND bestaetigt_am IS NULL ORDER BY id DESC LIMIT 1)", (stufe, s))
    if cur.rowcount:
        return False
    cur.execute("INSERT INTO alarme (stufe, quelle, titel, details, kanaele_gesendet, schluessel, zuletzt) VALUES (%s,%s,%s,%s::jsonb,%s,%s,now())",
                (stufe, quelle[:60], titel[:200], json.dumps(details), kanaele or [], s))
    return True


def schliessen(cur, quelle: str, von: str = "automatisch (Problem behoben)") -> int:
    """Schließt alle offenen Alarme einer Quelle, weil das Problem nicht mehr besteht."""
    cur.execute("UPDATE alarme SET bestaetigt_von = %s, bestaetigt_am = now() WHERE quelle = %s AND bestaetigt_am IS NULL", (von, quelle))
    return cur.rowcount
