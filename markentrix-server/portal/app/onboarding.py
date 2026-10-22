"""Standard-Checkliste für neue Kunden. 'modul' = nur wenn das Modul aktiv ist, 'auto' = wird aus den Daten erkannt."""

VORLAGE = [
    # code, titel, hilfe, sortierung, modul, auto
    ("vertrag", "Angebot/Vertrag unterschrieben", "Wird automatisch erledigt, sobald ein Angebot als angenommen markiert ist (Kunde hat im Portal zugestimmt). Sonst von Hand abhaken.", 10, None, "angebot_ok"),
    ("avv", "Auftragsverarbeitungsvertrag (AVV) unterschrieben", "Pflicht, sobald Daten von Kundinnen/Kunden des Kunden verarbeitet werden. Wird automatisch erledigt, sobald die unterschriebene Fassung abgelegt ist.", 20, None, "avv"),
    ("zugang", "Portal-Zugang eingerichtet", "Kunde hat sein Passwort gesetzt und sich einmal angemeldet.", 30, None, "zugang"),
    ("briefing", "Briefing ausgefüllt", "Der Kunde hat den Fragebogen zu Unternehmen, Zielen und Wünschen abgeschickt.", 35, None, "briefing"),
    ("stammdaten", "Firmendaten, Öffnungszeiten, Leistungen erfasst", "Wird für Website, Assistent und Berichte gebraucht.", 40, None, None),
    ("branding", "Logo, Farben, Fotos erhalten", "Vom Kunden bekommen oder mit ihm abgestimmt.", 50, None, None),
    ("domain", "Domain erfasst", "Im Kundenblatt unter „Domains“ Inhaber, Registrar und Ablaufdatum eintragen (wird dann automatisch erkannt).", 60, "website", "domain_erfasst"),
    ("dns", "DNS zeigt auf den Server", "Wird automatisch erkannt, sobald @ und www auf den Server zeigen. Unter Websites & Demos steht bei „DNS prüfen“, was der Kunde ändern muss, und dort lässt sich die Anleitung direkt mailen.", 65, "website", "dns_ok"),
    ("website", "Website live", "Seite ist veröffentlicht und geprüft (Handy, Impressum, Datenschutz).", 70, "website", "website_live"),
    ("google_profil", "Google-Unternehmensprofil geprüft", "Eintrag vorhanden, Öffnungszeiten, Adresse und Website-Adresse stimmen; Bewertungslink liegt vor.", 75, "website", None),
    ("wissen", "Wissensbasis für den Assistenten befüllt", "Leistungen, Preise, Öffnungszeiten, FAQ, Tonalität.", 80, "ki_chat", "wissen"),
    ("agent", "KI-Assistent / Agent getestet", "Mit typischen Fragen ausprobiert, Hinweis auf KI sichtbar.", 90, "ki_chat", None),
    ("konten", "Zugänge zu externen Diensten erhalten", "z. B. Google Unternehmensprofil, Social Media, Kalender.", 100, None, None),
    ("einweisung", "Einweisung / Übergabe-Termin durchgeführt", "Kunde weiß, wie er das Portal und die Benachrichtigungen nutzt.", 110, None, None),
    ("rechnung", "Erste Rechnung gestellt", "Einrichtung und erster Monat abgerechnet (wird automatisch erkannt, bei Referenzkunden entfällt das).", 120, None, "rechnung"),
]


# Schritte, bei denen der Kunde selbst etwas tun muss: code -> (Seite im Kundenportal, Beschriftung)
KUNDE_AKTION = {
    "avv": ("avv", "Vertrag bestätigen"),
    "briefing": ("briefing", "Briefing ausfüllen"),
    "branding": ("unterlagen", "Logo und Fotos hochladen"),
    "konten": ("nachrichten", "Zugänge senden"),
    "stammdaten": ("briefing", "Angaben ergänzen"),
}


def anlegen(cur, kid):
    """Legt fehlende Standardpunkte an (idempotent). Gibt die Zahl neuer Punkte zurück."""
    cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (kid,))
    ref = cur.fetchone()["referenzkunde"]
    cur.execute("SELECT modul_code FROM kunden_module WHERE kunden_id=%s AND aktiv", (kid,))
    module = {r["modul_code"] for r in cur.fetchall()}
    neu = 0
    for code, titel, hilfe, sort, modul, _auto in VORLAGE:
        if modul and modul not in module:
            continue
        if ref and code == "rechnung":
            continue
        cur.execute("""INSERT INTO onboarding_punkte (kunden_id, code, titel, hilfe, sortierung) VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (kunden_id, code) DO NOTHING""", (kid, code, titel, hilfe, sort))
        neu += cur.rowcount
    return neu


def auto_erkannt(cur, kid) -> set:
    erkannt = set()
    cur.execute("SELECT 1 FROM benutzer WHERE kunden_id=%s AND passwort_hash IS NOT NULL AND letzter_login IS NOT NULL LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("zugang")
    cur.execute("SELECT 1 FROM websites WHERE kunden_id=%s AND status='live' LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("website_live")
    cur.execute("SELECT 1 FROM domains WHERE kunden_id=%s AND status<>'gekuendigt' AND ablauf_am IS NOT NULL AND (inhaber_name IS NOT NULL OR inhaber='markentrix') LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("domain_erfasst")
    cur.execute("""SELECT 1 FROM websites w JOIN domain_pruefung p ON p.domain = w.domain WHERE w.kunden_id=%s AND w.art='live' AND p.ok LIMIT 1""", (kid,))
    if cur.fetchone():
        erkannt.add("dns_ok")
    cur.execute("SELECT 1 FROM belege WHERE kunden_id=%s AND art='rechnung' AND status IN ('gestellt','versendet','bezahlt') LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("rechnung")
    cur.execute("SELECT 1 FROM belege WHERE kunden_id=%s AND art='angebot' AND status='angenommen' LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("angebot_ok")
    cur.execute("SELECT 1 FROM wissensbasis WHERE kunden_id=%s AND aktiv LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("wissen")
    cur.execute("SELECT 1 FROM avv WHERE kunden_id=%s AND datei IS NOT NULL AND unterschrieben_am IS NOT NULL LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("avv")
    cur.execute("SELECT 1 FROM briefings WHERE kunden_id=%s AND status='abgeschickt'", (kid,))
    if cur.fetchone():
        erkannt.add("briefing")
    return erkannt


def lesen(cur, kid) -> list:
    anlegen(cur, kid)
    erkannt = auto_erkannt(cur, kid)
    auto = {c: a for c, _t, _h, _s, _m, a in VORLAGE if a}
    cur.execute("SELECT code, titel, hilfe, erledigt, erledigt_am, notiz FROM onboarding_punkte WHERE kunden_id=%s ORDER BY sortierung, id", (kid,))
    out = []
    for r in cur.fetchall():
        a = auto.get(r["code"])
        r["automatisch"] = bool(a and a in erkannt)
        r["fertig"] = r["erledigt"] or r["automatisch"]
        out.append(r)
    return out


# Phasen der Kunden-Reise: (Schlüssel, Titel, Codes). Eigene Punkte (x-…) zählen zur Phase „Aufbau“.
PHASEN = [
    ("start", "Start", ("vertrag", "avv", "zugang")),
    ("material", "Briefing & Material", ("briefing", "stammdaten", "branding", "konten")),
    ("aufbau", "Aufbau", ("domain", "dns", "wissen", "agent")),
    ("live", "Live & Übergabe", ("website", "google_profil", "einweisung", "rechnung")),
]


def phase_von(code: str) -> str:
    for schluessel, _t, codes in PHASEN:
        if code in codes:
            return schluessel
    return "aufbau"


def phasenstand(punkte: list) -> dict:
    """Phasen mit Fortschritt; aktuell = erste Phase mit offenem Punkt (None, wenn alles erledigt)."""
    out = []
    for schluessel, titel, _c in PHASEN:
        mine = [p for p in punkte if phase_von(p["code"]) == schluessel]
        fertig = sum(1 for p in mine if p["fertig"])
        out.append({"schluessel": schluessel, "titel": titel, "fertig": fertig, "gesamt": len(mine), "erledigt": bool(mine) and fertig == len(mine), "leer": not mine})
    aktuell = next((p["schluessel"] for p in out if not p["leer"] and not p["erledigt"]), None)
    return {"phasen": out, "aktuell": aktuell}
