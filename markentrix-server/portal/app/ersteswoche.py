"""„Deine erste Woche“: kurze Checkliste für neue Kunden mit Fortschrittsbalken. Erkennt selbst, was erledigt ist. Erscheint 30 Tage nach dem Start, bis alles erledigt ist oder der Kunde sie ausblendet."""
from fastapi import APIRouter, Depends

from .db import tx
from .security import require_kunde

router = APIRouter(prefix="/api/kunde")
TAGE = 30


@router.get("/erste-woche")
def erste_woche(user: dict = Depends(require_kunde)):
    kid, uid = user["kunden_id"], user["id"]
    inhaber = user.get("kunden_rolle") == "inhaber"
    with tx("system") as cur:
        cur.execute("SELECT erstellt_am > now() - make_interval(days => %s) AS neu FROM kunden WHERE id=%s", (TAGE, kid))
        k = cur.fetchone()
        cur.execute("SELECT ansicht FROM benutzer WHERE id=%s", (uid,))
        zu = bool((cur.fetchone()["ansicht"] or {}).get("erste_woche_zu"))
        if not k or not k["neu"] or zu:
            return {"aktiv": False, "schritte": []}
        cur.execute("""SELECT
              (totp_aktiv OR EXISTS (SELECT 1 FROM passkeys p WHERE p.benutzer_id = b.id)) AS sicher,
              EXISTS (SELECT 1 FROM push_abos a WHERE a.benutzer_id = b.id) AS push
            FROM benutzer b WHERE b.id=%s""", (uid,))
        s = cur.fetchone()
        cur.execute("SELECT EXISTS (SELECT 1 FROM tickets t JOIN ticket_nachrichten n ON n.ticket_id = t.id WHERE t.kunden_id=%s AND n.von='kunde') AS nachricht", (kid,))
        nachricht = cur.fetchone()["nachricht"]
        cur.execute("SELECT count(*) FILTER (WHERE status='wartet') AS offen, count(*) FILTER (WHERE status IN ('freigegeben','abgelehnt')) AS erledigt FROM kundenfreigaben WHERE kunden_id=%s", (kid,))
        f = cur.fetchone()
        cur.execute("SELECT count(*) FILTER (WHERE datei IS NULL AND portal_freigabe_am IS NOT NULL) AS offen, count(*) FILTER (WHERE datei IS NOT NULL) AS da FROM avv WHERE kunden_id=%s", (kid,))
        avv = cur.fetchone()
        cur.execute("SELECT mail_aktiv FROM website_dienste WHERE kunden_id=%s", (kid,))
        w = cur.fetchone()
    schritte = [
        {"code": "app", "titel": "Portal als App aufs Handy legen", "fertig": None, "link": "#willkommen", "knopf": "So geht’s"},
        {"code": "push", "titel": "Benachrichtigungen aufs Handy einschalten", "fertig": bool(s["push"]), "link": "#einstellungen", "knopf": "Einschalten"},
        {"code": "sicher", "titel": "Anmeldung mit Fingerabdruck/Face-ID oder Zwei-Faktor einrichten", "fertig": bool(s["sicher"]), "link": "#einstellungen", "knopf": "Einrichten"},
        {"code": "nachricht", "titel": "Uns die erste Nachricht schreiben", "fertig": bool(nachricht), "link": "#nachrichten", "knopf": "Nachricht schreiben"},
    ]
    if f["offen"] or f["erledigt"]:
        schritte.append({"code": "freigabe", "titel": "Die erste Freigabe prüfen", "fertig": not f["offen"], "link": "#freigaben", "knopf": "Ansehen"})
    if inhaber and (avv["offen"] or avv["da"]):
        schritte.append({"code": "avv", "titel": "Datenschutz-Vertrag bestätigen", "fertig": not avv["offen"], "link": "#avv", "knopf": "Öffnen"})
    if inhaber and w is not None:
        schritte.append({"code": "formular", "titel": "Kontaktformular für die Website einschalten", "fertig": bool(w["mail_aktiv"]), "link": "#dienste", "knopf": "Einrichten"})
    return {"aktiv": True, "schritte": schritte}
