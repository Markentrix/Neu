"""Diagramme für Kunden, Onboarding-Board (Admin) und Lead-Pipeline mit Prognose (Admin und Vertriebler)."""
from fastapi import APIRouter, Depends, HTTPException

from . import diagramme, onboarding
from .db import tx
from .security import modul_aktiv, require_admin, require_kunde, require_vertrieb

router = APIRouter(prefix="/api")

_TZ = "Europe/Berlin"


@router.get("/kunde/diagramme")
def kunde_diagramme(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        cur.execute(f"""SELECT to_char(date_trunc('week', now() AT TIME ZONE '{_TZ}') - make_interval(weeks => n), 'YYYY-MM-DD') AS start FROM generate_series(0, 26) n ORDER BY 1""")
        starts = [r["start"] for r in cur.fetchall()]       # 27 Montage: 26 volle Wochen plus die laufende
        cur.execute(f"""SELECT to_char(date_trunc('week', erstellt_am AT TIME ZONE '{_TZ}'), 'YYYY-MM-DD') AS start, count(*) AS n FROM anfragen
                        WHERE kunden_id=%s AND status<>'spam' AND erstellt_am >= now() - interval '28 weeks' GROUP BY 1""", (kid,))
        a_w = {r["start"]: r["n"] for r in cur.fetchall()}
        cur.execute(f"""SELECT to_char(date_trunc('week', beginn AT TIME ZONE '{_TZ}'), 'YYYY-MM-DD') AS start, count(*) AS n FROM termine
                        WHERE kunden_id=%s AND status<>'abgesagt' AND beginn >= now() - interval '28 weeks' AND beginn < now() + interval '2 weeks' GROUP BY 1""", (kid,))
        t_w = {r["start"]: r["n"] for r in cur.fetchall()}
        wochen = [{"start": st, "anfragen": a_w.get(st, 0), "termine": t_w.get(st, 0)} for st in starts[:-1]]
        laufend = {"anfragen": a_w.get(starts[-1], 0), "termine": t_w.get(starts[-1], 0)}
        cur.execute("SELECT quelle, count(*) AS n FROM anfragen WHERE kunden_id=%s AND status<>'spam' AND erstellt_am > now() - interval '90 days' GROUP BY quelle", (kid,))
        quellen = {r["quelle"]: r["n"] for r in cur.fetchall()}
        cur.execute(f"""SELECT extract(isodow FROM erstellt_am AT TIME ZONE '{_TZ}')::int AS tag, count(*) AS n FROM anfragen
                        WHERE kunden_id=%s AND status<>'spam' AND erstellt_am > now() - interval '90 days' GROUP BY 1""", (kid,))
        wt = [0] * 7
        for r in cur.fetchall():
            wt[r["tag"] - 1] = r["n"]
        cur.execute("""SELECT count(*) AS anfragen, count(*) FILTER (WHERE status IN ('beantwortet','erledigt')) AS beantwortet FROM anfragen
                       WHERE kunden_id=%s AND status<>'spam' AND erstellt_am > now() - interval '90 days'""", (kid,))
        t = cur.fetchone()
        cur.execute("""SELECT count(*) FILTER (WHERE status<>'abgesagt') AS termine, count(*) FILTER (WHERE status='erledigt') AS erledigt FROM termine
                      WHERE kunden_id=%s AND beginn > now() - interval '90 days' AND beginn < now() + interval '1 day'""", (kid,))
        tt = cur.fetchone()
        cur.execute(f"""SELECT to_char(date_trunc('month', erstellt_am AT TIME ZONE '{_TZ}'), 'YYYY-MM') AS monat,
                              round((avg(extract(epoch FROM antwort_am - erstellt_am)) / 3600)::numeric, 1) AS stunden, count(*) AS n
                       FROM anfragen WHERE kunden_id=%s AND antwort_am IS NOT NULL AND erstellt_am > now() - interval '6 months' GROUP BY 1 ORDER BY 1""", (kid,))
        antwort = [{"monat": r["monat"], "stunden": float(r["stunden"]), "n": r["n"]} for r in cur.fetchall()]
        modul = modul_aktiv(cur, kid, "anfragen_termine")
    trichter = {"anfragen": t["anfragen"], "beantwortet": t["beantwortet"], "termine": tt["termine"], "erledigt": tt["erledigt"]}
    return {"modul": modul, "laufende_woche": laufend, "wochen": [{"start": w["start"], "anfragen": w["anfragen"], "termine": w["termine"]} for w in wochen], "quellen": quellen, "wochentage": wt,
            "trichter": trichter, "antwortzeit": antwort, "klartext": diagramme.klartext([{"anfragen": w["anfragen"]} for w in wochen], quellen, wt, trichter)}


# ---------------------------------------------------------------- Onboarding-Board
@router.get("/admin/onboarding/board")
def onboarding_board(user: dict = Depends(require_admin)):
    """Kunden im Onboarding nach Phase. Die Phase ergibt sich aus der Checkliste, Karten werden nicht von Hand verschoben."""
    with tx("admin") as cur:
        cur.execute("SELECT id, kundennummer, firma, erstellt_am, (now()::date - erstellt_am::date) AS tage FROM kunden WHERE status='onboarding' ORDER BY erstellt_am LIMIT 100")
        kunden = cur.fetchall()
        spalten = {s: [] for s, _t, _c in onboarding.PHASEN}
        spalten["fertig"] = []
        for k in kunden:
            punkte = onboarding.lesen(cur, k["id"])
            st = onboarding.phasenstand(punkte)
            offen = next((p for p in punkte if not p["fertig"]), None)
            karte = {"id": k["id"], "kundennummer": k["kundennummer"], "firma": k["firma"], "tage": k["tage"], "fertig": sum(1 for p in punkte if p["fertig"]), "gesamt": len(punkte),
                     "naechster": offen["titel"] if offen else None, "haengt": k["tage"] >= 5 and st["aktuell"] == "start"}
            spalten[st["aktuell"] or "fertig"].append(karte)
    titel = {s: t for s, t, _c in onboarding.PHASEN}
    return {"spalten": [{"schluessel": s, "titel": titel.get(s, "Alles erledigt, noch nicht aktiv"), "kunden": v} for s, v in spalten.items()]}


# ---------------------------------------------------------------- Pipeline
STUFEN = ["neu", "kontaktiert", "antwort", "termin", "angebot", "gewonnen"]
STUFEN_TXT = {"neu": "Neu", "kontaktiert": "Kontaktiert", "antwort": "Antwort", "termin": "Termin", "angebot": "Angebot", "gewonnen": "Gewonnen"}
PRO_SPALTE = 25
MIN_ABSCHLUSS = 8   # so viele entschiedene Leads (gewonnen + verloren) braucht eine Quote


def _pipeline(cur, partner_id=None, mit_prognose=False):
    filt, par = ("AND vertriebspartner_id=%s", [partner_id]) if partner_id else ("", [])
    cur.execute(f"SELECT status, count(*) AS n FROM leads WHERE status = ANY(%s) {filt} GROUP BY status", [STUFEN + ["verloren"], *par])
    zaehl = {r["status"]: r["n"] for r in cur.fetchall()}
    spalten = []
    for st in STUFEN:
        extra = "AND geaendert_am > now() - interval '30 days'" if st == "gewonnen" else ""
        cur.execute(f"""SELECT l.id, l.firma, l.ort, l.temperatur, l.wiedervorlage_am, l.letzter_kontakt_am, l.telefon, v.name AS vertriebler
                        FROM leads l LEFT JOIN vertriebspartner v ON v.id = l.vertriebspartner_id
                        WHERE l.status=%s {filt.replace('vertriebspartner_id', 'l.vertriebspartner_id')} {extra.replace('geaendert_am', 'l.geaendert_am')}
                        ORDER BY (l.temperatur='heiss') DESC, (l.temperatur='warm') DESC, l.wiedervorlage_am NULLS LAST, l.erstellt_am DESC LIMIT {PRO_SPALTE}""", [st, *par])
        spalten.append({"status": st, "titel": STUFEN_TXT[st], "anzahl": zaehl.get(st, 0), "leads": cur.fetchall()})
    cur.execute(f"""SELECT count(*) FILTER (WHERE status='gewonnen') AS g, count(*) FILTER (WHERE status='verloren') AS v FROM leads
                    WHERE geaendert_am > now() - interval '180 days' {filt}""", par)
    q = cur.fetchone()
    entschieden = q["g"] + q["v"]
    quote = round(100 * q["g"] / entschieden, 1) if entschieden >= MIN_ABSCHLUSS else None
    # Trichter: wie viele Leads sind mindestens in Stufe X (kumulativ), Basis alle aktuellen Leads außer verloren
    stufen_n = [zaehl.get(s, 0) for s in STUFEN]
    kumulativ = [sum(stufen_n[i:]) for i in range(len(STUFEN))]
    trichter = [{"status": s, "titel": STUFEN_TXT[s], "anzahl": kumulativ[i]} for i, s in enumerate(STUFEN)]
    out = {"spalten": spalten, "trichter": trichter, "verloren": zaehl.get("verloren", 0), "quote": quote, "entschieden": entschieden, "pro_spalte": PRO_SPALTE}
    if mit_prognose:
        cur.execute("SELECT coalesce(sum(b.monatlich_cent - b.rabatt_cent),0) AS cent FROM buchungen b JOIN kunden k ON k.id=b.kunden_id WHERE b.status IN ('aktiv','in_einrichtung','beauftragt') AND b.monatlich_cent IS NOT NULL AND NOT k.referenzkunde")
        mrr = int(cur.fetchone()["cent"])
        cur.execute("SELECT count(*) AS n FROM kunden WHERE status='aktiv' AND NOT referenzkunde")
        aktiv = cur.fetchone()["n"]
        angebote = zaehl.get("angebot", 0)
        schnitt = int(mrr / aktiv) if aktiv else 0
        ok = quote is not None and schnitt > 0
        out["prognose"] = {"angebote": angebote, "quote": quote, "schnitt_cent": schnitt, "erwartet_cent": int(angebote * quote / 100 * schnitt) if ok else None,
                           "hinweis": None if ok else ("Zu wenige abgeschlossene Leads für eine Quote (mindestens %d in 180 Tagen)." % MIN_ABSCHLUSS if quote is None else "Noch kein durchschnittlicher Monatswert je Kunde vorhanden.")}
    return out


@router.get("/admin/pipeline")
def admin_pipeline(vertriebler: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        if vertriebler:
            try:
                cur.execute("SELECT id FROM vertriebspartner WHERE id=%s", (vertriebler,))
            except Exception:
                raise HTTPException(400, "Ungültiger Vertriebler.")
            if not cur.fetchone():
                raise HTTPException(404, "Vertriebler nicht gefunden.")
        d = _pipeline(cur, vertriebler or None, mit_prognose=True)
        cur.execute("SELECT id, name FROM vertriebspartner WHERE status='aktiv' ORDER BY name")
        d["vertriebler"] = cur.fetchall()
    return d


@router.get("/vertrieb/pipeline")
def vertrieb_pipeline(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        return _pipeline(cur, user["vertriebspartner_id"])
