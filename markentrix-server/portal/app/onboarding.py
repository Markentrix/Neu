"""Standard-Checkliste für neue Kunden. 'modul' = nur wenn das Modul aktiv ist, 'auto' = wird aus den Daten erkannt."""

VORLAGE = [
    # code, titel, hilfe, sortierung, modul, auto
    ("vertrag", "Angebot/Vertrag unterschrieben", "Unterschriebenes Angebot oder Vertrag liegt vor und ist abgelegt.", 10, None, None),
    ("avv", "Auftragsverarbeitungsvertrag (AVV) unterschrieben", "Pflicht, sobald Daten von Kundinnen/Kunden des Kunden verarbeitet werden. Wird automatisch erledigt, sobald die unterschriebene Fassung abgelegt ist.", 20, None, "avv"),
    ("zugang", "Portal-Zugang eingerichtet", "Kunde hat sein Passwort gesetzt und sich einmal angemeldet.", 30, None, "zugang"),
    ("stammdaten", "Firmendaten, Öffnungszeiten, Leistungen erfasst", "Wird für Website, Assistent und Berichte gebraucht.", 40, None, None),
    ("branding", "Logo, Farben, Fotos erhalten", "Vom Kunden bekommen oder mit ihm abgestimmt.", 50, None, None),
    ("domain", "Domain und DNS bereit", "Domain gehört dem Kunden oder wurde registriert, DNS zeigt auf den Server.", 60, "website", None),
    ("website", "Website live", "Seite ist veröffentlicht und geprüft (Handy, Impressum, Datenschutz).", 70, "website", "website_live"),
    ("wissen", "Wissensbasis für den Assistenten befüllt", "Leistungen, Preise, Öffnungszeiten, FAQ, Tonalität.", 80, "ki_chat", "wissen"),
    ("agent", "KI-Assistent / Agent getestet", "Mit typischen Fragen ausprobiert, Hinweis auf KI sichtbar.", 90, "ki_chat", None),
    ("konten", "Zugänge zu externen Diensten erhalten", "z. B. Google Unternehmensprofil, Social Media, Kalender.", 100, None, None),
    ("einweisung", "Einweisung / Übergabe-Termin durchgeführt", "Kunde weiß, wie er das Portal und die Benachrichtigungen nutzt.", 110, None, None),
    ("rechnung", "Erste Rechnung gestellt", "Einrichtung und erster Monat abgerechnet (bei Referenzkunden entfällt das).", 120, None, None),
]


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
    cur.execute("SELECT 1 FROM wissensbasis WHERE kunden_id=%s AND aktiv LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("wissen")
    cur.execute("SELECT 1 FROM avv WHERE kunden_id=%s AND datei IS NOT NULL AND unterschrieben_am IS NOT NULL LIMIT 1", (kid,))
    if cur.fetchone():
        erkannt.add("avv")
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
