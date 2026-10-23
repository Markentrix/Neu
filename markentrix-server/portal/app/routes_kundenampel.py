"""Kunden-Ampel: pro aktivem Kunde auf einen Blick, ob Website, Mail und Terminbuchung laufen und was beim Team oder Kunden offen ist."""
from fastapi import APIRouter, Depends

from .db import tx
from .security import require_admin

router = APIRouter(prefix="/api/admin")

SQL = """
SELECT k.id, k.firma, k.kundennummer, k.status,
  (SELECT count(*) FROM websites w WHERE w.kunden_id=k.id AND w.art='live' AND w.status='live') AS web_live,
  (SELECT count(*) FROM website_wacht x WHERE x.kunden_id=k.id AND NOT x.ok AND x.seit < now() - interval '1 hour') AS web_gestoert,
  (SELECT string_agg(x.domain || ': ' || coalesce(x.fehler, 'unbekannt'), ' | ') FROM website_wacht x WHERE x.kunden_id=k.id AND NOT x.ok AND x.seit < now() - interval '1 hour') AS web_grund,
  (SELECT count(*) FROM mail_protokoll m WHERE m.kunden_id=k.id AND NOT m.ok AND m.zeit > now() - interval '7 days') AS mail_fehler,
  coalesce(d.mail_aktiv, false) AS mail_aktiv, coalesce(d.kal_aktiv, false) AS kal_aktiv, (d.kunden_id IS NOT NULL) AS hat_dienste,
  (SELECT count(*) FROM website_leistungen l WHERE l.kunden_id=k.id AND l.aktiv) AS leistungen_aktiv,
  (SELECT count(*) FROM website_leistungen l WHERE l.kunden_id=k.id AND NOT l.aktiv) AS leistungen_inaktiv,
  (SELECT count(*) FROM website_termine t WHERE t.kunden_id=k.id AND t.status='reserviert' AND t.erstellt_am < now() - interval '1 day') AS reserviert_alt,
  (SELECT max(t.erstellt_am) FROM website_termine t WHERE t.kunden_id=k.id) AS letzte_buchung,
  (SELECT count(*) FROM website_leistung_aenderungen a WHERE a.kunden_id=k.id AND a.status='offen') AS leistungsaenderungen,
  (SELECT count(*) FROM website_gutscheine g WHERE g.kunden_id=k.id AND g.status IN ('angefragt','zahlungslink_gesendet')) AS gutscheine_offen,
  (SELECT count(*) FROM wissen_vorschlaege v WHERE v.kunden_id=k.id AND v.status='offen') AS wissen_offen,
  (SELECT count(*) FROM website_termine t WHERE t.kunden_id=k.id AND t.status='abgesagt' AND t.storno_kostenlos AND t.anzahlung_erhalten_am IS NOT NULL AND t.erstattet_am IS NULL AND t.abgesagt_am < now() - interval '2 days') AS erstattung_offen,
  (SELECT count(*) FROM anfragen a WHERE a.kunden_id=k.id AND a.status='neu' AND a.erstellt_am < now() - interval '2 days') AS anfragen_alt
FROM kunden k LEFT JOIN website_dienste d ON d.kunden_id=k.id
WHERE k.status IN ('aktiv','onboarding') ORDER BY k.firma LIMIT 500"""


def bewerten(r: dict) -> dict:
    rot, gelb = [], []
    if r["web_gestoert"]:
        rot.append("Website antwortet nicht richtig (seit über einer Stunde)." + (f" Grund: {r['web_grund']}" if r.get("web_grund") else ""))
    if r["mail_fehler"]:
        rot.append(f"{r['mail_fehler']} Mail(s) in den letzten 7 Tagen fehlgeschlagen.")
    if r["status"] == "aktiv" and not r["web_live"]:
        gelb.append("Keine Website ist live geschaltet.")
    if r["hat_dienste"] and r["kal_aktiv"] and not r["leistungen_aktiv"] and r["leistungen_inaktiv"]:
        gelb.append("Terminbuchung ist an, aber alle Leistungen sind noch inaktiv (Preise und Freigabe fehlen).")
    if r["hat_dienste"] and not r["mail_aktiv"] and r["status"] == "aktiv":
        gelb.append("Benachrichtigungen per Mail sind nicht eingerichtet.")
    for schluessel, text in (("reserviert_alt", "unbestätigte Buchung(en) warten über 1 Tag"), ("leistungsaenderungen", "Leistungsänderung(en) warten auf Freigabe"),
                             ("gutscheine_offen", "Gutschein-Anfrage(n) offen"), ("wissen_offen", "Wissensvorschlag/-vorschläge zu prüfen"),
                             ("erstattung_offen", "Anzahlung(en) seit über 2 Tagen nicht erstattet"), ("anfragen_alt", "neue Anfrage(n) seit über 2 Tagen unbeantwortet")):
        if r[schluessel]:
            gelb.append(f"{r[schluessel]} {text}.")
    return {"farbe": "rot" if rot else ("gelb" if gelb else "gruen"), "rot": rot, "gelb": gelb}


@router.get("/kunden-ampel")
def kunden_ampel(user: dict = Depends(require_admin)):
    with tx("system") as cur:
        cur.execute(SQL)
        zeilen = cur.fetchall()
    out = []
    for r in zeilen:
        b = bewerten(r)
        out.append({"id": str(r["id"]), "firma": r["firma"], "kundennummer": r["kundennummer"], "status": r["status"], "letzte_buchung": r["letzte_buchung"],
                    "buchung_aktiv": bool(r["kal_aktiv"]), **b})
    rang = {"rot": 0, "gelb": 1, "gruen": 2}
    out.sort(key=lambda x: (rang[x["farbe"]], x["firma"].lower()))
    return {"kunden": out, "summe": {f: sum(1 for x in out if x["farbe"] == f) for f in rang}}
