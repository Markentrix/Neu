"""Heiße Leads mit Begründung: warum lohnt sich der Anruf jetzt? Die Gründe stammen aus echten Vorgängen (Angebot angesehen, Antwort, Terminbuchung, Website-Check)."""
from datetime import date

FRISCH_TAGE = 7


def gruende(cur, ids: list) -> dict:
    """Gibt {lead_id: [Text, …]} zurück (nur Leads mit mindestens einem Grund). Für Vertriebler gedacht: keine Preise, keine Angaben zu anderen."""
    if not ids:
        return {}
    out: dict = {}

    def add(lid, text):
        out.setdefault(str(lid), []).append(text)
    cur.execute("SELECT id, temperatur, quelle, wiedervorlage_am FROM leads WHERE id = ANY(%s::uuid[])", (ids,))
    for l in cur.fetchall():
        if l["temperatur"] == "heiss":
            add(l["id"], "Als heiß eingestuft")
        if l["quelle"] in ("website", "funnel"):
            add(l["id"], "Hat sich selbst gemeldet")
        if l["wiedervorlage_am"] and l["wiedervorlage_am"] < date.today():
            add(l["id"], f"Rückruf überfällig seit {(date.today() - l['wiedervorlage_am']).days} Tag(en)")
    cur.execute("""SELECT lead_id, nummer, angesehen_am FROM belege WHERE lead_id = ANY(%s::uuid[]) AND art='angebot' AND status IN ('gestellt','versendet')
                   AND angesehen_am > now() - make_interval(days => %s)""", (ids, FRISCH_TAGE))
    for b in cur.fetchall():
        add(b["lead_id"], f"Hat das Angebot {b['nummer']} angesehen (noch keine Antwort)")
    cur.execute("""SELECT DISTINCT lead_id FROM lead_aktivitaeten WHERE lead_id = ANY(%s::uuid[]) AND art='antwort' AND zeit > now() - make_interval(days => %s)""", (ids, FRISCH_TAGE))
    for r in cur.fetchall():
        add(r["lead_id"], "Hat kürzlich geantwortet")
    cur.execute("SELECT DISTINCT lead_id FROM gespraechstermine WHERE lead_id = ANY(%s::uuid[]) AND status='gebucht' AND start >= now()", (ids,))
    for r in cur.fetchall():
        add(r["lead_id"], "Hat ein Erstgespräch gebucht")
    cur.execute("""SELECT DISTINCT ON (lead_id) lead_id, score FROM lead_checks WHERE lead_id = ANY(%s::uuid[]) ORDER BY lead_id, erstellt_am DESC""", (ids,))
    for r in cur.fetchall():
        if r["score"] is not None and r["score"] < 50:
            add(r["lead_id"], f"Website-Check: {r['score']} von 100 Punkten, viel Verbesserungsbedarf")
    return out


def anreichern(cur, *listen) -> None:
    """Hängt an jede Zeile der Listen das Feld „gruende“ (Liste, evtl. leer)."""
    ids = [z["id"] for l in listen for z in l]
    g = gruende(cur, ids)
    for l in listen:
        for z in l:
            z["gruende"] = g.get(str(z["id"]), [])
