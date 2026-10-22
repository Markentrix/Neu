"""Verteilung neuer Leads auf aktive Vertriebler (gleichmäßig nach Zahl offener Leads) und die Einstellung dafür."""
from . import einstellungen

OFFEN = ('neu', 'kontaktiert', 'antwort', 'termin', 'angebot')


def einstellung(cur) -> dict:
    e = einstellungen.lesen(cur, "vertrieb") or {}
    return {"auto_zuweisung": bool(e.get("auto_zuweisung")), "reaktionsstunden": int(e.get("reaktionsstunden") or 4), "preise_sichtbar": bool(e.get("preise_sichtbar"))}


def aktive_partner(cur) -> list[dict]:
    """Aktive Vertriebler mit der Zahl ihrer offenen Leads, wenigsten zuerst."""
    cur.execute("""SELECT p.id, p.name, (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=p.id AND l.status = ANY(%s)) AS offen
                   FROM vertriebspartner p WHERE p.status='aktiv'
                     AND EXISTS (SELECT 1 FROM benutzer b WHERE b.vertriebspartner_id=p.id AND b.aktiv AND b.passwort_hash IS NOT NULL)
                   ORDER BY offen, p.name""", (list(OFFEN),))
    return cur.fetchall()


def verteilen(cur, n: int) -> list[str]:
    """Gibt n Partner-IDs zurück (reihum, immer der mit den wenigsten offenen Leads zuerst)."""
    p = [dict(x) for x in aktive_partner(cur)]
    if not p:
        return []
    out = []
    for _ in range(n):
        p.sort(key=lambda x: x["offen"])
        out.append(str(p[0]["id"]))
        p[0]["offen"] += 1
    return out


def naechster(cur) -> str | None:
    """Zuständiger für einen neu eingehenden Lead, wenn die automatische Zuweisung eingeschaltet ist."""
    if not einstellung(cur)["auto_zuweisung"]:
        return None
    v = verteilen(cur, 1)
    return v[0] if v else None
