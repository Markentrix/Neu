"""Gesprächsleitfaden für Vertriebler: Standardtexte, einfaches Textformat zum Bearbeiten, Branchenhinweise.
Alles ist ein Vorschlag zum Üben. Die Texte versprechen nichts und nennen keine Preise."""
import re

STANDARD = {
    "abschnitte": [
        {"titel": "Vor dem Anruf", "punkte": [
            "Schau dir den Betrieb kurz an: Website, Google-Bewertungen, Öffnungszeiten. Ein konkreter Satz dazu wirkt besser als jede Floskel.",
            "Prüfe im Lead, ob schon jemand Kontakt hatte und was notiert wurde.",
            "Ruf nur an, wenn eine geschäftliche Ansprache zulässig ist. Im Zweifel nicht anrufen und bei Markentrix nachfragen.",
            "Lege dir die Zeit für Notizen bereit: Nach jedem Gespräch sofort Ergebnis und Wiedervorlage festhalten."]},
        {"titel": "Eröffnung (30 Sekunden)", "punkte": [
            "Name, Firma, Grund des Anrufs in einem Satz: „Guten Tag, hier ist … von Markentrix. Ich rufe an, weil wir kleinen Betrieben helfen, dass keine Kundenanfrage mehr verloren geht.“",
            "Frage nach der Zeit: „Haben Sie gerade zwei Minuten?“ Wenn nein: Rückrufzeit vereinbaren und eintragen.",
            "Ein konkreter Bezug zum Betrieb direkt danach, zum Beispiel zur Website oder zu den Bewertungen."]},
        {"titel": "Fragen, die das Gespräch öffnen", "punkte": [
            "Wie kommen heute neue Kunden zu Ihnen?",
            "Was passiert, wenn jemand außerhalb der Öffnungszeiten anruft oder schreibt?",
            "Wie viel Zeit geht bei Ihnen für Anfragen, Termine und Nachfassen drauf?",
            "Was nervt Sie im Alltag am meisten an der Verwaltung?"]},
        {"titel": "Was Markentrix konkret tut", "punkte": [
            "Ein KI-Telefonassistent nimmt Anrufe an, wenn niemand Zeit hat, und leitet Anfragen weiter.",
            "Website und Anfragen-Formular, die Kundenanfragen sauber einsammeln.",
            "Erinnerungen, Berichte und Nachfassen laufen automatisch im Hintergrund.",
            "Der Betrieb behält den Überblick im eigenen Kundenportal.",
            "Nenne nur das, was zum Betrieb passt, und keine Preise, die nicht in der Preisliste stehen."]},
        {"titel": "Abschluss und nächster Schritt", "punkte": [
            "Bei Interesse: ein Termin für ein kurzes Gespräch mit Markentrix, nicht der Verkauf am Telefon.",
            "Datum und Uhrzeit wiederholen und in „Termin vereinbart“ eintragen.",
            "Bei „vielleicht später“: Wiedervorlage setzen und höflich verabschieden.",
            "Bei „kein Interesse“: freundlich bedanken, „Kein Interesse“ eintragen und nie wieder anrufen."]},
        {"titel": "Spielregeln", "punkte": [
            "Nichts versprechen, was nicht sicher ist (keine Garantien für Umsatz oder Kundenzahlen).",
            "Keine Preise nennen, die nicht in der Preisliste stehen.",
            "Wer nicht angerufen werden möchte, wird sofort eingetragen und respektiert.",
            "Niemals bedrängen. Ein höfliches Nein ist ein gutes Ergebnis."]},
    ],
    "einwaende": [
        {"einwand": "Dafür habe ich keine Zeit.", "antwort": "Das verstehe ich, deshalb nur kurz: Wann passt es Ihnen besser, dass ich zurückrufe, heute Nachmittag oder morgen früh?"},
        {"einwand": "Wir haben schon jemanden.", "antwort": "Schön, dann ist das Thema bei Ihnen schon angekommen. Ich will nichts ersetzen. Darf ich fragen, was Ihnen daran gut gefällt und was Sie sich noch anders wünschen würden?"},
        {"einwand": "Das ist bestimmt zu teuer.", "antwort": "Das kann ich verstehen. Genaue Zahlen bespricht mein Kollege im Termin, damit sie zu Ihrem Betrieb passen. Es kostet nichts, sich das einmal anzusehen."},
        {"einwand": "Brauche ich nicht, läuft alles bei uns.", "antwort": "Wunderbar. Eine Frage dazu: Wie läuft es, wenn Sie mal im Urlaub oder krank sind und das Telefon klingelt?"},
        {"einwand": "Schicken Sie mir einfach was per Mail.", "antwort": "Gern. Damit es für Sie passt: Was soll in der Mail unbedingt stehen? Und wann darf ich danach noch einmal kurz anrufen?"},
        {"einwand": "KI, das ist mir zu unsicher.", "antwort": "Verständlich. Deshalb prüfen Sie bei uns alles vorher, nichts geht ohne Ihre Freigabe live. Im Termin zeigen wir Ihnen, wie das konkret aussieht."},
        {"einwand": "Rufen Sie mich nicht mehr an.", "antwort": "Selbstverständlich, vielen Dank für Ihre Zeit. (Sofort als „Kein Interesse“ eintragen und nicht erneut anrufen.)"},
    ],
    "branchen": {
        "werkstatt": {"name": "Kfz-Werkstatt, Reifenservice", "tipps": [
            "Typischer Schmerz: Telefon klingelt in der Werkstatt, aber niemand kann abnehmen, weil alle am Fahrzeug arbeiten.",
            "Frage nach Terminanfragen für Reifenwechsel und Inspektion außerhalb der Öffnungszeiten.",
            "Saisonspitzen (Reifenwechsel, TÜV) machen ein Telefonproblem sichtbar."]},
        "friseur": {"name": "Friseur, Kosmetik, Barber", "tipps": [
            "Typischer Schmerz: Während der Behandlung kann niemand ans Telefon, Termine gehen verloren.",
            "Frage nach Terminausfällen und Nachfassen bei Stammkunden.",
            "Online-Terminbuchung und Erinnerungen reduzieren Ausfälle."]},
        "gastro": {"name": "Restaurant, Imbiss, Café, Bäckerei", "tipps": [
            "Typischer Schmerz: Reservierungsanrufe in der Stoßzeit.",
            "Frage nach Bewertungen und wie auf Rückfragen reagiert wird.",
            "Öffnungszeiten, Speisekarte und Aktionen müssen überall aktuell sein."]},
        "handwerk": {"name": "Handwerk (Elektro, Sanitär, Maler, Bau)", "tipps": [
            "Typischer Schmerz: Auf der Baustelle ist niemand erreichbar, Anfragen bleiben liegen.",
            "Frage nach Angebotsanfragen und wie schnell darauf geantwortet wird.",
            "Wer schnell antwortet, bekommt oft den Auftrag."]},
        "einzelhandel": {"name": "Einzelhandel, Markt, Laden", "tipps": [
            "Typischer Schmerz: Kunden fragen nach Verfügbarkeit und Öffnungszeiten, während der Laden voll ist.",
            "Frage nach Wochenangeboten und wie sie bekannt gemacht werden.",
            "Gute Website und aktuelle Google-Einträge bringen Laufkundschaft."]},
        "fitness": {"name": "Fitness, Sport, Studio", "tipps": [
            "Typischer Schmerz: Probetraining-Anfragen werden zu langsam beantwortet.",
            "Frage nach Kündigungen und wie Mitglieder gehalten werden.",
            "Automatische Erinnerungen und Nachfassen helfen bei Interessenten."]},
    },
    "mail": {"betreff": "Unser Gespräch, {firma}",
             "text": "Guten Tag {name},\n\nvielen Dank für das nette Gespräch heute. Wie besprochen sende ich Ihnen eine kurze Zusammenfassung:\n\n- [Was wir besprochen haben]\n- [Vereinbarter nächster Schritt, z. B. Termin am … um …]\n\nSollten Sie vorher Fragen haben, melden Sie sich gern direkt bei mir.\n\nViele Grüße\n{vertriebler}\nMarkentrix"},
}

_BRANCHEN_STICHWORTE = {
    "werkstatt": ("werkstatt", "kfz", "reifen", "auto", "karosserie", "tüv"),
    "friseur": ("friseur", "barber", "kosmetik", "beauty", "nagel", "salon"),
    "gastro": ("restaurant", "gastro", "imbiss", "café", "cafe", "bäcker", "baecker", "pizz", "döner", "bistro"),
    "handwerk": ("handwerk", "elektro", "sanitär", "sanitaer", "maler", "dach", "bau", "heizung", "tischler", "schreiner"),
    "einzelhandel": ("einzelhandel", "laden", "markt", "shop", "handel", "geschäft"),
    "fitness": ("fitness", "sport", "studio", "yoga", "gym"),
}


def branche_fuer(*texte) -> str | None:
    t = " ".join(x for x in texte if x).lower()
    for code, woerter in _BRANCHEN_STICHWORTE.items():
        if any(w in t for w in woerter):
            return code
    return None


def zusammenfuehren(gespeichert: dict | None) -> dict:
    """Gespeicherte Anpassungen über die Standardtexte legen (fehlende Teile kommen aus dem Standard)."""
    g = gespeichert or {}
    return {k: (g.get(k) if g.get(k) else STANDARD[k]) for k in STANDARD}


# ---------------------------------------------------------------- Textformat zum Bearbeiten
def als_text(cfg: dict) -> str:
    out = []
    for a in cfg["abschnitte"]:
        out.append(f"[Abschnitt] {a['titel']}")
        out += [f"- {p}" for p in a["punkte"]]
        out.append("")
    for e in cfg["einwaende"]:
        out += [f"[Einwand] {e['einwand']}", e["antwort"], ""]
    for code, b in cfg["branchen"].items():
        out.append(f"[Branche] {code} | {b['name']}")
        out += [f"- {t}" for t in b["tipps"]]
        out.append("")
    out += [f"[Mail] {cfg['mail']['betreff']}", cfg["mail"]["text"]]
    return "\n".join(out).strip() + "\n"


def aus_text(text: str) -> dict:
    """Wandelt das Textformat zurück. Wirft ValueError mit verständlicher Meldung bei Fehlern."""
    cfg = {"abschnitte": [], "einwaende": [], "branchen": {}, "mail": None}
    akt = None
    for roh in text.replace("\r", "").split("\n"):
        z = roh.rstrip()
        m = re.match(r"^\[(Abschnitt|Einwand|Branche|Mail)\]\s*(.*)$", z)
        if m:
            art, rest = m.group(1), m.group(2).strip()
            if not rest:
                raise ValueError(f"Hinter [{art}] fehlt der Titel.")
            if art == "Abschnitt":
                akt = ("a", {"titel": rest[:120], "punkte": []}); cfg["abschnitte"].append(akt[1])
            elif art == "Einwand":
                akt = ("e", {"einwand": rest[:300], "antwort": ""}); cfg["einwaende"].append(akt[1])
            elif art == "Branche":
                code, _, name = rest.partition("|")
                code = re.sub(r"[^a-z0-9_]", "", code.strip().lower())
                if not code or not name.strip():
                    raise ValueError("Eine Branche braucht die Form: [Branche] kürzel | Name")
                akt = ("b", {"name": name.strip()[:120], "tipps": []}); cfg["branchen"][code] = akt[1]
            else:
                akt = ("m", {"betreff": rest[:200], "text": "", "_z": []}); cfg["mail"] = akt[1]
            continue
        if akt is None:
            if z.strip():
                raise ValueError("Der Text muss mit einer Überschrift wie [Abschnitt] … beginnen.")
            continue
        art, ziel = akt
        if art in ("a", "b"):
            if z.startswith("- "):
                ziel["punkte" if art == "a" else "tipps"].append(z[2:].strip()[:500])
            elif z.strip():
                lst = ziel["punkte" if art == "a" else "tipps"]
                if lst:
                    lst[-1] = (lst[-1] + " " + z.strip())[:500]
                else:
                    raise ValueError("Punkte beginnen mit „- “.")
        elif art == "e":
            ziel["antwort"] = (ziel["antwort"] + ("\n" if ziel["antwort"] else "") + z.strip()).strip()[:1000] if z.strip() else ziel["antwort"]
        else:
            ziel["_z"].append(z)
    if cfg["mail"]:
        cfg["mail"]["text"] = "\n".join(cfg["mail"].pop("_z")).strip("\n")[:4000]
    if not cfg["abschnitte"]:
        raise ValueError("Mindestens ein [Abschnitt] ist nötig.")
    for e in cfg["einwaende"]:
        if not e["antwort"]:
            raise ValueError(f"Beim Einwand „{e['einwand']}“ fehlt die Antwort.")
    if not cfg["einwaende"]:
        cfg["einwaende"] = STANDARD["einwaende"]
    if not cfg["branchen"]:
        cfg["branchen"] = STANDARD["branchen"]
    if not cfg["mail"] or not cfg["mail"]["text"].strip():
        cfg["mail"] = STANDARD["mail"]
    return cfg
