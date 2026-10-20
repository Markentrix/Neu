"""Klartext zu den Kunden-Diagrammen: kurze, vorsichtige Sätze aus echten Zahlen. Bei zu wenig Daten sagen wir das ehrlich."""

QUELLE = {"website": "über die Website", "email": "per E-Mail", "telefon": "per Telefon", "chat": "über den Chat", "whatsapp": "über WhatsApp", "sonstiges": "auf anderem Weg"}
WOCHENTAG = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MIN_ANFRAGEN = 10


def prozent(teil: int, gesamt: int):
    return round(100 * teil / gesamt) if gesamt else None


def klartext(wochen: list, quellen: dict, wochentage: list, trichter: dict) -> list:
    """Liefert Sätze für Verlauf, Quelle, Wochentag und Trichter. Jede Aussage nennt ihre Grundlage (Zeitraum, Anzahl)."""
    s = []
    gesamt = sum(quellen.values())
    if gesamt < MIN_ANFRAGEN:
        return [f"Für Aussagen zu Trends reichen {gesamt} Anfragen in 90 Tagen noch nicht aus. Sobald mehr zusammenkommen, erscheinen hier Hinweise."]
    letzte = sum(w["anfragen"] for w in wochen[-4:]); davor = sum(w["anfragen"] for w in wochen[-8:-4])
    if davor >= 5:
        d = round(100 * (letzte - davor) / davor)
        s.append(f"In den letzten 4 Wochen gab es {letzte} Anfragen, in den 4 Wochen davor {davor} ({'+' if d >= 0 else ''}{d} %).")
    elif letzte:
        s.append(f"In den letzten 4 Wochen gab es {letzte} Anfragen.")
    q, n = max(quellen.items(), key=lambda x: x[1])
    s.append(f"Die meisten Anfragen kamen {QUELLE.get(q, q)} ({n} von {gesamt} in 90 Tagen, {prozent(n, gesamt)} %).")
    if sum(wochentage) >= MIN_ANFRAGEN:
        i = max(range(7), key=lambda k: wochentage[k])
        s.append(f"Am häufigsten melden sich Kundinnen und Kunden am {WOCHENTAG[i]} ({wochentage[i]} von {sum(wochentage)}).")
    if trichter["anfragen"]:
        b = prozent(trichter["beantwortet"], trichter["anfragen"])
        s.append(f"{b} % der Anfragen sind beantwortet oder erledigt." + (" Offene Anfragen findest du unter „Heute“." if b is not None and b < 90 else ""))
    return s
