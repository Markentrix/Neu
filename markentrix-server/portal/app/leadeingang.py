"""Gemeinsame Nachbearbeitung eingehender Leads (Kontaktformular, Website-Check, Terminbuchung):
automatische Zuweisung (wenn eingeschaltet), Wiederbelebung verlorener Leads und Information des Zuständigen."""
from . import push, zuweisung


def bearbeiten(cur, lid, neu: bool, anlass: str) -> list:
    """Gibt die Push-Empfänger (Zuständiger) zurück, die nach dem Commit benachrichtigt werden sollen. `anlass`: kurzer Text für den Verlauf."""
    cur.execute("SELECT status, vertriebspartner_id, kunden_id FROM leads WHERE id=%s", (lid,))
    l = cur.fetchone()
    if not l:
        return []
    cur.execute("UPDATE leads SET ansprache_grundlage = coalesce(ansprache_grundlage, 'anfrage') WHERE id=%s", (lid,))
    pid = l["vertriebspartner_id"]
    if not pid and not l["kunden_id"]:
        pid = zuweisung.naechster(cur)
        if pid:
            cur.execute("UPDATE leads SET vertriebspartner_id=%s WHERE id=%s", (pid, lid))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz','Automatisch einem Vertriebler zugewiesen','automatisch')", (lid,))
    if not neu and l["status"] in ("verloren", "tot", "kontaktiert") and not l["kunden_id"]:
        cur.execute("UPDATE leads SET status='antwort', wiedervorlage_am=current_date, verlust_grund=NULL WHERE id=%s", (lid,))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,'website')", (lid, f"{l['status']} → antwort ({anlass}: hat sich erneut gemeldet)"))
    elif not neu and l["status"] in ("neu", "antwort", "termin", "angebot"):
        cur.execute("UPDATE leads SET wiedervorlage_am=least(coalesce(wiedervorlage_am, current_date), current_date) WHERE id=%s", (lid,))
    return push.partner(cur, pid) if pid else []
