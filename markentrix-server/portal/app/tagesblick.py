"""Tageszahlen je Rolle: für die Zahl am App-Symbol und den Morgen-Push „Dein Tag“.
Die Push-Texte enthalten bewusst keine Namen, weil sie auf dem Sperrbildschirm erscheinen."""

_OFFEN = "l.status NOT IN ('verloren','gewonnen','gesperrt','tot','consent_ausstehend')"


def vertrieb(cur, pid) -> dict:
    """Fällige Leads (Wiedervorlage oder heißer neuer Lead) und heutige Erstgespräche eines Vertriebspartners."""
    cur.execute(f"""SELECT count(*) AS n FROM leads l WHERE l.vertriebspartner_id=%s AND {_OFFEN}
                    AND (l.wiedervorlage_am <= current_date OR (l.status='neu' AND l.temperatur='heiss' AND l.letzter_kontakt_am IS NULL))""", (pid,))
    faellig = cur.fetchone()["n"]
    cur.execute("""SELECT count(*) AS n FROM gespraechstermine g JOIN leads l ON l.id=g.lead_id
                   WHERE g.status='gebucht' AND l.vertriebspartner_id=%s AND (g.start AT TIME ZONE 'Europe/Berlin')::date = (now() AT TIME ZONE 'Europe/Berlin')::date""", (pid,))
    return {"faellig": faellig, "termine": cur.fetchone()["n"]}


def kunde(cur) -> dict:
    """Muss mit einem Cursor der Kundenrolle (Row-Level-Security) laufen."""
    cur.execute("""SELECT (SELECT count(*) FROM anfragen WHERE status='neu') AS anfragen,
                          (SELECT count(*) FROM kundenfreigaben WHERE status='wartet') AS freigaben,
                          (SELECT count(*) FROM tickets WHERE kunde_ungelesen) AS nachrichten,
                          (SELECT count(*) FROM termine WHERE status IN ('geplant','bestaetigt')
                             AND (beginn AT TIME ZONE 'Europe/Berlin')::date = (now() AT TIME ZONE 'Europe/Berlin')::date) AS termine""")
    return dict(cur.fetchone())


def admin(cur) -> dict:
    cur.execute("""SELECT (SELECT count(*) FROM tickets WHERE status <> 'erledigt' AND team_ungelesen) AS nachrichten,
                          (SELECT count(*) FROM kundenfreigaben WHERE status = 'wartet') AS freigaben,
                          (SELECT count(*) FROM aufgaben WHERE status = 'offen' AND faellig_am < current_date) AS aufgaben""")
    return dict(cur.fetchone())


def zahl(rolle: str, d: dict) -> int:
    """Zahl am App-Symbol: das, was Aufmerksamkeit braucht."""
    if rolle == "vertrieb":
        return int(d["faellig"])
    if rolle == "admin":
        return int(d["nachrichten"] + d["freigaben"] + d["aufgaben"])
    return int(d["anfragen"] + d["freigaben"] + d["nachrichten"])


def _stueck(n: int, eins: str, viele: str) -> str:
    return f"{n} {eins if n == 1 else viele}"


def push_text(rolle: str, d: dict) -> tuple[str, str] | None:
    """Titel und Text für den Morgen-Push, None wenn nichts ansteht."""
    teile = []
    if rolle == "vertrieb":
        if d["faellig"]:
            teile.append(_stueck(d["faellig"], "Lead wartet", "Leads warten") + " auf Ihren Anruf")
        if d["termine"]:
            teile.append(_stueck(d["termine"], "Erstgespräch", "Erstgespräche") + " heute")
        return ("Dein Tag", " · ".join(teile)) if teile else None
    if rolle == "kunde":
        if d["anfragen"]:
            teile.append(_stueck(d["anfragen"], "neue Anfrage", "neue Anfragen"))
        if d["termine"]:
            teile.append(_stueck(d["termine"], "Termin", "Termine") + " heute")
        if d["freigaben"]:
            teile.append(_stueck(d["freigaben"], "Freigabe wartet", "Freigaben warten"))
        if d["nachrichten"]:
            teile.append(_stueck(d["nachrichten"], "ungelesene Nachricht", "ungelesene Nachrichten"))
        return ("Dein Tag", " · ".join(teile)) if teile else None
    return None
