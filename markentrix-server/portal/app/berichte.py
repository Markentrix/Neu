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


def einordnung_auto(d: dict) -> tuple[str, list[str]]:
    """Regelbasierte Einordnung und nächste Schritte aus den Zahlen. Nur Aussagen, die die Zahlen tragen."""
    a, t = d["anfragen"], d["termine"]
    teile, schritte = [], []
    if a["gesamt"] == 0 and a["vormonat"] == 0:
        teile.append("In diesem Monat sind über die angebundenen Kanäle keine Anfragen eingegangen.")
        schritte.append("Wir prüfen, ob Kontaktformular, Telefonnummer und Google-Profil gut sichtbar und erreichbar sind.")
    else:
        if a["vormonat"] > 0:
            pct = round((a["gesamt"] - a["vormonat"]) / a["vormonat"] * 100)
            if pct >= 5:
                teile.append(f"Die Anfragen sind gegenüber dem Vormonat um {pct} % gestiegen ({a['vormonat']} auf {a['gesamt']}).")
            elif pct <= -5:
                teile.append(f"Die Anfragen sind gegenüber dem Vormonat um {abs(pct)} % zurückgegangen ({a['vormonat']} auf {a['gesamt']}).")
                schritte.append("Wir prüfen, woran der Rückgang liegt (Sichtbarkeit, Saison, Angebote) und schlagen Gegenmaßnahmen vor.")
            else:
                teile.append(f"Die Anfragen liegen mit {a['gesamt']} auf dem Niveau des Vormonats ({a['vormonat']}).")
        else:
            teile.append(f"Im Vormonat gab es keine Anfragen, in diesem Monat waren es {a['gesamt']}.")
        if a["nach_quelle"]:
            q, n = next(iter(a["nach_quelle"].items()))
            teile.append(f"Die meisten Anfragen kamen über „{q}“ ({n} von {a['gesamt']}).")
        if a["gesamt"] >= 3 and a["bearbeitet"] < a["gesamt"] * 0.7:
            schritte.append(f"Offene Anfragen zeitnah beantworten: bisher sind {a['bearbeitet']} von {a['gesamt']} bearbeitet. Schnelle Antworten erhöhen die Chance auf einen Auftrag.")
    if a["spam"] >= 5:
        schritte.append(f"{a['spam']} Spam-Anfragen wurden aussortiert. Wir verschärfen bei Bedarf den Spam-Schutz am Formular.")
    nicht = t["nach_status"].get("nicht_erschienen", 0)
    if t["gesamt"] and nicht:
        teile.append(f"Von {t['gesamt']} Terminen wurden {nicht} nicht wahrgenommen.")
        schritte.append("Terminerinnerungen für Kundinnen und Kunden aktivieren, um Ausfälle zu verringern.")
    elif t["gesamt"]:
        teile.append(f"Es gab {t['gesamt']} Termine.")
    if d["automatische_ablaeufe"]:
        teile.append(f"Die Automatisierungen haben {d['automatische_ablaeufe']} Abläufe erledigt.")
    if not schritte:
        schritte.append("Wir beobachten die Entwicklung weiter und melden uns, sobald sich etwas Auffälliges zeigt.")
    return " ".join(teile), schritte[:5]


def texte(b: dict) -> tuple[str, list[str]]:
    """Gespeicherte (bearbeitete) Texte, sonst die automatische Einordnung."""
    auto_t, auto_s = einordnung_auto(b["daten"])
    text = (b.get("einordnung") or "").strip() or auto_t
    sch = [z.strip() for z in (b.get("naechste_schritte") or "").splitlines() if z.strip()] or auto_s
    return text, sch


def pdf_erzeugen(cur, bericht_id, f: dict | None = None) -> tuple[bytes, str]:
    cur.execute("""SELECT b.id, b.titel, b.zeitraum_von, b.zeitraum_bis, b.daten, b.einordnung, b.naechste_schritte, k.firma, k.kundennummer
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
    ein, schritte = texte(b)
    inhalt += [pdf.p("Einordnung", pdf.H2), pdf.p(ein), pdf.p("Unsere nächsten Schritte", pdf.H2)] + [pdf.p("• " + z) for z in schritte]
    if a["nach_quelle"]:
        inhalt += [pdf.p("Woher die Anfragen kamen", pdf.H2), pdf.tabelle(["Quelle", "Anzahl"], [[q.capitalize(), str(n)] for q, n in a["nach_quelle"].items()], breiten=[120 * pdf.mm, 50 * pdf.mm], rechts_ab=1)]
    if d["anrufe"]:
        z = [[("Eingehend" if r == "ein" else "Ausgehend"), str(v["anzahl"]), f"{v['dauer_sek'] // 60}:{v['dauer_sek'] % 60:02d} min"] for r, v in d["anrufe"].items()]
        inhalt += [pdf.p("Telefonate", pdf.H2), pdf.tabelle(["Richtung", "Anzahl", "Ø Dauer"], z, breiten=[80 * pdf.mm, 45 * pdf.mm, 45 * pdf.mm], rechts_ab=1)]
    if d["chat_fragen"]:
        inhalt += [pdf.p(f"Der KI-Assistent im Portal wurde {d['chat_fragen']}-mal gefragt.", pdf.KLEIN)]
    inhalt += [pdf.Spacer(1, 16), pdf.p("Fragen zum Bericht oder Ideen, was als Nächstes helfen könnte? Wir sprechen gern darüber.", pdf.KLEIN)]
    return pdf.dokument(b["titel"], b["firma"], inhalt, f, "Dieser Bericht wurde automatisch erstellt."), f"Monatsbericht-{b['zeitraum_von']:%Y-%m}-{b['kundennummer']}.pdf"
