"""Vertriebler im Blick: Aktivität, Rückstand und Warnzeichen je Vertriebler, damit früh gegengesteuert werden kann."""
from fastapi import APIRouter, Depends, HTTPException

from .db import tx
from .security import require_admin

router = APIRouter(prefix="/api/admin")

OFFEN = "('neu','kontaktiert','antwort','termin','angebot')"

SQL = f"""
SELECT v.id, v.name,
  (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='anruf' AND a.zeit >= now() - interval '7 days') AS anrufe_7t,
  (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='anruf' AND a.zeit >= now() - interval '14 days' AND a.zeit < now() - interval '7 days') AS anrufe_vorwoche,
  (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='anruf' AND a.zeit >= now() - interval '30 days') AS anrufe_30t,
  (SELECT count(*) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art='termin' AND a.zeit >= now() - interval '30 days') AS termine_30t,
  (SELECT count(*) FROM kunden k WHERE k.vertriebspartner_id=v.id AND k.erstellt_am >= now() - interval '90 days') AS kunden_90t,
  (SELECT max(a.zeit) FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=v.id AND a.art IN ('anruf','termin','notiz')) AS letzte_aktivitaet,
  (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=v.id AND l.status IN {OFFEN}) AS offene_leads,
  (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=v.id AND l.status IN {OFFEN} AND l.letzter_kontakt_am IS NULL AND l.erstellt_am < now() - interval '7 days') AS unberuehrt_7t,
  (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=v.id AND l.status IN {OFFEN} AND l.wiedervorlage_am < current_date) AS ueberfaellig,
  (SELECT count(*) FROM leads l WHERE l.vertriebspartner_id=v.id AND l.status IN {OFFEN} AND l.letzter_kontakt_am < now() - interval '14 days') AS eingeschlafen
FROM vertriebspartner v WHERE v.status='aktiv' ORDER BY v.name LIMIT 100"""


def bewerten(r: dict) -> dict:
    hinweise = []
    if r["offene_leads"] and not r["anrufe_7t"]:
        hinweise.append("Seit 7 Tagen keine Anrufe festgehalten")
    elif r["anrufe_vorwoche"] >= 10 and r["anrufe_7t"] < r["anrufe_vorwoche"] / 2:
        hinweise.append(f"Anrufe halbiert ({r['anrufe_7t']} statt {r['anrufe_vorwoche']} in der Vorwoche)")
    if r["unberuehrt_7t"]:
        hinweise.append(f"{r['unberuehrt_7t']} Leads seit über 7 Tagen unberührt")
    if r["ueberfaellig"]:
        hinweise.append(f"{r['ueberfaellig']} überfällige Wiedervorlagen")
    if r["eingeschlafen"]:
        hinweise.append(f"{r['eingeschlafen']} Leads seit über 14 Tagen ohne Kontakt")
    if r["anrufe_30t"] >= 40 and not r["termine_30t"]:
        hinweise.append("Viele Anrufe, aber keine Termine in 30 Tagen: Gesprächsführung besprechen")
    quote = round(100 * r["termine_30t"] / r["anrufe_30t"], 1) if r["anrufe_30t"] else None
    return {**r, "id": str(r["id"]), "termin_quote": quote, "hinweise": hinweise, "ampel": "rot" if len(hinweise) >= 3 else "gelb" if hinweise else "gruen"}


@router.get("/vertrieb/qualitaet")
def qualitaet(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute(SQL)
        liste = [bewerten(r) for r in cur.fetchall()]
    liste.sort(key=lambda r: (-len(r["hinweise"]), r["name"]))
    return {"vertriebler": liste, "summe": {a: sum(1 for r in liste if r["ampel"] == a) for a in ("rot", "gelb", "gruen")}}


@router.get("/vertrieb/partner/{pid}/aktivitaet")
def aktivitaet(pid: str, tage: int = 30, user: dict = Depends(require_admin)):
    """Was hat dieser Vertriebler im Zeitraum abgearbeitet? Je Tag und in Summe, plus die letzten Einträge."""
    tage = tage if tage in (7, 30, 90) else 30
    with tx("admin") as cur:
        cur.execute("SELECT id, name FROM vertriebspartner WHERE id=%s", (pid,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Vertriebler nicht gefunden.")
        cur.execute("""SELECT d::date AS tag,
                              count(a.id) FILTER (WHERE a.art='anruf') AS anrufe,
                              count(a.id) FILTER (WHERE a.art='termin') AS termine,
                              count(a.id) FILTER (WHERE a.art='notiz') AS notizen,
                              count(a.id) FILTER (WHERE a.art IN ('mail_gesendet','antwort')) AS mails
                       FROM generate_series(current_date - (%s - 1), current_date, interval '1 day') d
                       LEFT JOIN (SELECT a.* FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=%s) a
                              ON a.zeit::date = d::date
                       GROUP BY d ORDER BY d""", (tage, pid))
        verlauf = cur.fetchall()
        cur.execute("""SELECT count(DISTINCT a.lead_id) AS leads_bearbeitet,
                              count(*) FILTER (WHERE a.art='anruf') AS anrufe,
                              count(*) FILTER (WHERE a.art='anruf' AND a.ergebnis='anruf_erreicht') AS erreicht,
                              count(*) FILTER (WHERE a.art='termin') AS termine,
                              count(*) FILTER (WHERE a.art='notiz') AS notizen,
                              count(*) FILTER (WHERE a.art IN ('mail_gesendet','antwort')) AS mails,
                              count(DISTINCT a.zeit::date) FILTER (WHERE a.art IN ('anruf','termin','notiz','mail_gesendet')) AS aktive_tage
                       FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id
                       WHERE l.vertriebspartner_id=%s AND a.zeit >= current_date - (%s - 1)""", (pid, tage))
        summe = cur.fetchone()
        cur.execute("""SELECT (SELECT count(*) FROM leads WHERE vertriebspartner_id=%s AND erstellt_am >= current_date - (%s - 1)) AS neue_leads,
                              (SELECT count(*) FROM kunden WHERE vertriebspartner_id=%s AND erstellt_am >= current_date - (%s - 1)) AS neue_kunden,
                              (SELECT count(*) FROM leads WHERE vertriebspartner_id=%s AND status IN ('neu','kontaktiert','antwort','termin','angebot')) AS offene_leads""", (pid, tage, pid, tage, pid))
        sonst = cur.fetchone()
        cur.execute("""SELECT a.zeit, a.art, a.ergebnis, a.inhalt, l.id AS lead_id, l.firma
                       FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id
                       WHERE l.vertriebspartner_id=%s AND a.art IN ('anruf','termin','notiz','mail_gesendet','antwort')
                       ORDER BY a.zeit DESC LIMIT 25""", (pid,))
        letzte = cur.fetchall()
    for z in letzte:
        z["inhalt"] = (z["inhalt"] or "")[:160]
    return {"partner": p, "tage": tage, "verlauf": verlauf, "summe": {**summe, **sonst}, "letzte": letzte}
