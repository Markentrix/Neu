"""Monatsbericht pro Kunde: Zahlen sammeln, in der Datenbank speichern, als PDF ausgeben."""
import json
from datetime import date, timedelta

from . import pdf, rechtstexte


def monat_grenzen(monat: date) -> tuple[date, date]:
    von = monat.replace(day=1)
    bis = (von.replace(day=28) + timedelta(days=4)).replace(day=1)
    return von, bis


def vormonat(heute: date | None = None) -> date:
    heute = heute or date.today()
    return (heute.replace(day=1) - timedelta(days=1)).replace(day=1)


def sammeln(cur, kid, von: date, bis: date) -> dict:
    vor_von, _ = monat_grenzen(vormonat(von))
    cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status<>'spam'", (kid, von, bis))
    a_ges = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status<>'spam'", (kid, vor_von, von))
    a_vor = cur.fetchone()["n"]
    cur.execute("SELECT quelle, count(*) AS n FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status<>'spam' GROUP BY quelle ORDER BY n DESC", (kid, von, bis))
    a_quelle = {r["quelle"]: r["n"] for r in cur.fetchall()}
    cur.execute("SELECT count(*) FILTER (WHERE status IN ('beantwortet','erledigt')) AS bearbeitet, count(*) FILTER (WHERE status='spam') AS spam FROM anfragen WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s", (kid, von, bis))
    ar = cur.fetchone()
    cur.execute("SELECT status, count(*) AS n FROM termine WHERE kunden_id=%s AND beginn >= %s AND beginn < %s GROUP BY status", (kid, von, bis))
    t = {r["status"]: r["n"] for r in cur.fetchall()}
    cur.execute("SELECT richtung, count(*) AS n, coalesce(round(avg(dauer_sek)),0) AS dauer FROM anrufe WHERE kunden_id=%s AND beginn >= %s AND beginn < %s GROUP BY richtung", (kid, von, bis))
    anrufe = {r["richtung"]: {"anzahl": r["n"], "dauer_sek": int(r["dauer"])} for r in cur.fetchall()}
    cur.execute("""SELECT count(*) FILTER (WHERE richtung='ein') AS ein, count(*) FILTER (WHERE richtung='aus') AS aus,
                          count(*) FILTER (WHERE agent_lauf_id IS NOT NULL AND richtung='aus') AS automatisch
                   FROM nachrichten WHERE kunden_id=%s AND zeit >= %s AND zeit < %s""", (kid, von, bis))
    nach = cur.fetchone()
    cur.execute("SELECT count(*) FILTER (WHERE absender='kunde') AS fragen FROM chat_verlauf WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s", (kid, von, bis))
    chat = cur.fetchone()["fragen"]
    cur.execute("SELECT count(*) AS n FROM agent_laeufe WHERE kunden_id=%s AND zeit >= %s AND zeit < %s AND ergebnis='ok'", (kid, von, bis))
    laeufe = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM wochenangebote_uploads WHERE kunden_id=%s AND erstellt_am >= %s AND erstellt_am < %s AND status='veroeffentlicht'", (kid, von, bis))
    wa = cur.fetchone()["n"]
    cur.execute("SELECT count(*) AS n FROM bewertungsanfragen WHERE kunden_id=%s AND gesendet_am >= %s AND gesendet_am < %s", (kid, von, bis))
    bew = cur.fetchone()["n"]
    return {"anfragen": {"gesamt": a_ges, "vormonat": a_vor, "nach_quelle": a_quelle, "bearbeitet": ar["bearbeitet"], "spam": ar["spam"]},
            "termine": {"gesamt": sum(t.values()), "nach_status": t},
            "anrufe": anrufe, "nachrichten": {"ein": nach["ein"], "aus": nach["aus"], "automatisch": nach["automatisch"]},
            "chat_fragen": chat, "automatische_ablaeufe": laeufe, "wochenangebote": wa, "bewertungsanfragen": bew}


def erstellen(cur, kid, monat: date) -> str:
    """Legt den Bericht an (oder aktualisiert die Zahlen) und gibt die Bericht-ID zurück."""
    von, bis = monat_grenzen(monat)
    daten = sammeln(cur, kid, von, bis)
    titel = "Monatsbericht " + pdf.monat_name(von)
    cur.execute("""INSERT INTO berichte (kunden_id, titel, art, zeitraum_von, zeitraum_bis, daten) VALUES (%s,%s,'monatsbericht',%s,%s,%s::jsonb)
                   ON CONFLICT (kunden_id, zeitraum_von) WHERE art='monatsbericht' DO UPDATE SET daten=EXCLUDED.daten, titel=EXCLUDED.titel
                   RETURNING id""", (kid, titel, von, bis - timedelta(days=1), json.dumps(daten)))
    return cur.fetchone()["id"]


def _n(n, einzahl, mehrzahl) -> str:
    return f"{n} {einzahl if n == 1 else mehrzahl}"


def _delta(neu, alt) -> str:
    if alt == 0:
        return "" if neu == 0 else " (Vormonat: keine)"
    d = round((neu - alt) / alt * 100)
    return f" ({'+' if d >= 0 else ''}{d} % zum Vormonat)"


def pdf_erzeugen(cur, bericht_id, f: dict | None = None) -> tuple[bytes, str]:
    cur.execute("""SELECT b.id, b.titel, b.zeitraum_von, b.zeitraum_bis, b.daten, k.firma, k.kundennummer
                   FROM berichte b JOIN kunden k ON k.id=b.kunden_id WHERE b.id=%s AND b.art='monatsbericht'""", (bericht_id,))
    b = cur.fetchone()
    if not b:
        raise LookupError("Bericht nicht gefunden")
    f = f or rechtstexte.firma(cur)
    d = b["daten"]
    a, t = d["anfragen"], d["termine"]
    monat = pdf.monat_name(b["zeitraum_von"])
    inhalt = [pdf.p("Monatsbericht " + monat, pdf.H1), pdf.p(f"{b['firma']} · Kundennr. {b['kundennummer']}", pdf.KLEIN), pdf.Spacer(1, 10)]
    k = [("Anfragen", a["gesamt"]), ("Termine", t["gesamt"]), ("Automatische Abläufe", d["automatische_ablaeufe"]), ("Nachrichten beantwortet (automatisch)", d["nachrichten"]["automatisch"])]
    inhalt += [pdf.kacheln(k)]
    inhalt += [pdf.p("Das Wichtigste", pdf.H2)]
    zeilen = [f"{_n(a['gesamt'], 'Anfrage', 'Anfragen')}{_delta(a['gesamt'], a['vormonat'])}, davon {a['bearbeitet']} bearbeitet." + (f" {a['spam']} als Spam aussortiert." if a["spam"] else "")]
    if t["gesamt"]:
        zeilen.append(f"{_n(t['gesamt'], 'Termin', 'Termine')}, davon {t['nach_status'].get('erledigt', 0)} erledigt" + (f" und {t['nach_status'].get('nicht_erschienen', 0)} nicht wahrgenommen." if t["nach_status"].get("nicht_erschienen") else "."))
    if d["automatische_ablaeufe"]:
        zeilen.append(f"Ihre Automatisierungen haben {d['automatische_ablaeufe']} Abläufe erfolgreich erledigt – ohne dass jemand von Hand eingreifen musste.")
    if d["nachrichten"]["automatisch"]:
        zeilen.append(f"{_n(d['nachrichten']['automatisch'], 'Nachricht wurde', 'Nachrichten wurden')} automatisch beantwortet.")
    if d["wochenangebote"]:
        zeilen.append(f"{_n(d['wochenangebote'], 'Wochenangebot wurde', 'Wochenangebote wurden')} veröffentlicht.")
    if d["bewertungsanfragen"]:
        zeilen.append(f"{d['bewertungsanfragen']} Bewertungsanfragen wurden an Kundinnen und Kunden verschickt.")
    inhalt += [pdf.p("• " + z) for z in zeilen]
    if a["nach_quelle"]:
        inhalt += [pdf.p("Woher die Anfragen kamen", pdf.H2), pdf.tabelle(["Quelle", "Anzahl"], [[q.capitalize(), str(n)] for q, n in a["nach_quelle"].items()], breiten=[120 * pdf.mm, 50 * pdf.mm], rechts_ab=1)]
    if d["anrufe"]:
        z = [[("Eingehend" if r == "ein" else "Ausgehend"), str(v["anzahl"]), f"{v['dauer_sek'] // 60}:{v['dauer_sek'] % 60:02d} min"] for r, v in d["anrufe"].items()]
        inhalt += [pdf.p("Telefonate", pdf.H2), pdf.tabelle(["Richtung", "Anzahl", "Ø Dauer"], z, breiten=[80 * pdf.mm, 45 * pdf.mm, 45 * pdf.mm], rechts_ab=1)]
    if d["chat_fragen"]:
        inhalt += [pdf.p(f"Der KI-Assistent im Portal wurde {d['chat_fragen']}-mal gefragt.", pdf.KLEIN)]
    inhalt += [pdf.Spacer(1, 16), pdf.p("Fragen zum Bericht oder Ideen, was als Nächstes helfen könnte? Wir sprechen gern darüber.", pdf.KLEIN)]
    return pdf.dokument(b["titel"], b["firma"], inhalt, f, "Dieser Bericht wurde automatisch erstellt."), f"Monatsbericht-{b['zeitraum_von']:%Y-%m}-{b['kundennummer']}.pdf"
