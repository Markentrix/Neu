"""Beste Anrufzeit je Branche: aus den eigenen Anrufen (erreicht oder nicht) ermittelt, wann Betriebe tatsächlich abnehmen.
Es werden nur Zähler je Branchengruppe und Stunde ausgewertet, keine Personen. Ohne genug Anrufe gibt es keine Empfehlung."""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")
MIN_GRUPPE = 20      # so viele Anrufe braucht eine Branche, bevor wir etwas empfehlen
MIN_STUNDE = 4       # so viele Anrufe braucht eine Stunde, um zu zählen
GRUPPE_SQL = "coalesce(nullif(l.gruppe,''), nullif(l.branche,''))"


def statistik(cur) -> dict:
    """{Branche: {"stunden": [8, 12], "quote": 62, "anzahl": 41}} nur für Branchen mit genug Anrufen und erkennbar besseren Stunden."""
    cur.execute(f"""SELECT {GRUPPE_SQL} AS g, extract(hour from a.zeit at time zone 'Europe/Berlin')::int AS std, count(*)::int AS n,
                           count(*) FILTER (WHERE a.ergebnis = 'anruf_erreicht')::int AS ok
                    FROM lead_aktivitaeten a JOIN leads l ON l.id = a.lead_id
                    WHERE a.art = 'anruf' AND a.ergebnis IN ('anruf_erreicht','anruf_nicht_erreicht','anruf_mailbox') AND a.zeit > now() - interval '12 months'
                    GROUP BY 1, 2""")
    je: dict = {}
    for z in cur.fetchall():
        if z["g"]:
            je.setdefault(z["g"], []).append(z)
    erg = {}
    for g, zeilen in je.items():
        gesamt = sum(z["n"] for z in zeilen)
        if gesamt < MIN_GRUPPE:
            continue
        schnitt = sum(z["ok"] for z in zeilen) / gesamt
        gut = sorted((z for z in zeilen if z["n"] >= MIN_STUNDE and z["ok"] / z["n"] > schnitt), key=lambda z: (-z["ok"] / z["n"], -z["n"]))[:2]
        if not gut:
            continue
        n = sum(z["n"] for z in gut)
        erg[g] = {"stunden": sorted(z["std"] for z in gut), "quote": round(100 * sum(z["ok"] for z in gut) / n), "anzahl": gesamt}
    return erg


def gruppen_jetzt(cur, jetzt: datetime | None = None) -> list:
    """Branchen, für die die aktuelle Stunde eine der besten Anrufzeiten ist."""
    std = (jetzt or datetime.now(TZ)).astimezone(TZ).hour
    return [g for g, v in statistik(cur).items() if std in v["stunden"]]


def _bereich(stunden: list) -> str:
    return " und ".join(f"{s}–{s + 1} Uhr" for s in stunden)


def hinweis(cur, gruppe: str | None, branche: str | None = None) -> dict | None:
    """Kurzer Hinweis für die Lead-Seite oder None, wenn es (noch) keine belastbare Empfehlung gibt."""
    st = statistik(cur)
    g = next((x for x in (gruppe, branche) if x and x in st), None)
    if not g:
        return None
    v = st[g]
    return {"gruppe": g, "text": f"Beste Anrufzeit für {g}: {_bereich(v['stunden'])} ({v['quote']} % erreicht, nach {v['anzahl']} Anrufen)"}


def naechster_termin(cur, lid) -> dict | None:
    """Nächster vereinbarter Anruf: Rückrufzeit am Lead oder gebuchtes Erstgespräch."""
    cur.execute("""SELECT start, art FROM (SELECT rueckruf_am AS start, 'rueckruf' AS art FROM leads WHERE id=%s AND rueckruf_am > now()
                   UNION ALL SELECT start, 'erstgespraech' FROM gespraechstermine WHERE lead_id=%s AND status='gebucht' AND start > now()) t ORDER BY start LIMIT 1""", (lid, lid))
    z = cur.fetchone()
    return {"start": z["start"].isoformat(), "art": z["art"]} if z else None
