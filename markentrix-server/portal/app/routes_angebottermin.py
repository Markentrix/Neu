"""Terminvorschläge im Angebot: bis zu 3 Zeiten für ein Beratungsgespräch. Der Empfänger wählt im Angebots-Link eine aus,
daraus wird ein Gespräch im Admin-Kalender (Tabelle gespraechstermine) samt Kalendereinladung."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from . import config, mailer
from .routes_buchung import TZ, ics, lesen

MAX = 3


def lokal(d: datetime) -> str:
    return d.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")


def _parse(s: str) -> datetime:
    try:
        d = datetime.fromisoformat(str(s))
    except ValueError:
        raise HTTPException(400, "Ein Terminvorschlag ist ungültig.")
    if d.tzinfo is None:
        d = d.replace(tzinfo=TZ)
    return d.astimezone(timezone.utc)


def _belegt(cur, start: datetime, ende: datetime, ausser_beleg=None) -> bool:
    """Überschneidet sich die Zeit mit einem gebuchten Gespräch oder einem Eintrag im Admin-Kalender?"""
    cur.execute("SELECT 1 FROM gespraechstermine WHERE status='gebucht' AND start < %s AND ende > %s AND (beleg_id IS DISTINCT FROM %s) LIMIT 1", (ende, start, ausser_beleg))
    if cur.fetchone():
        return True
    cur.execute("SELECT 1 FROM kalender_eintraege WHERE start < %s AND ende > %s LIMIT 1", (ende, start))
    return bool(cur.fetchone())


def pruefen(cur, liste: list, beleg_id=None) -> list[str]:
    """Prüft die Vorschläge des Editors: höchstens 3, in der Zukunft, ohne Dubletten und ohne Überschneidung mit dem Kalender. Gibt ISO-Zeiten (UTC) zurück."""
    roh = [x for x in (liste or []) if str(x or "").strip()]
    if len(roh) > MAX:
        raise HTTPException(400, f"Bitte höchstens {MAX} Terminvorschläge eintragen.")
    dauer = lesen(cur)["dauer"]
    jetzt = datetime.now(timezone.utc)
    ergebnis: list[datetime] = []
    for x in roh:
        d = _parse(x)
        if d <= jetzt:
            raise HTTPException(400, "Terminvorschläge müssen in der Zukunft liegen.")
        if d in ergebnis:
            raise HTTPException(400, "Zwei Terminvorschläge sind identisch.")
        if _belegt(cur, d, d + timedelta(minutes=dauer), beleg_id):
            raise HTTPException(400, f"Der Vorschlag {lokal(d)} überschneidet sich mit einem Termin im Kalender. Bitte eine andere Zeit wählen.")
        ergebnis.append(d)
    return [d.isoformat() for d in sorted(ergebnis)]


def gebucht(cur, beleg_id) -> dict | None:
    cur.execute("SELECT id, start, ende FROM gespraechstermine WHERE beleg_id=%s AND status='gebucht' ORDER BY start LIMIT 1", (beleg_id,))
    return cur.fetchone()


def zeigen(cur, b: dict) -> dict:
    """Für die Angebotsseite: freie Vorschläge oder der bereits gebuchte Termin."""
    c = lesen(cur)
    g = gebucht(cur, b["id"])
    if g:
        return {"termin": {"start": g["start"].isoformat(), "ende": g["ende"].isoformat()}, "termine": [], "termin_dauer": c["dauer"], "termin_ort": c["ort"]}
    jetzt = datetime.now(timezone.utc)
    frei = []
    for x in (b.get("terminvorschlaege") or []):
        d = _parse(x)
        if d > jetzt + timedelta(hours=1) and not _belegt(cur, d, d + timedelta(minutes=c["dauer"])):
            frei.append(d.isoformat())
    return {"termin": None, "termine": frei, "termin_dauer": c["dauer"], "termin_ort": c["ort"]}


def waehlen(cur, b: dict, start_roh: str) -> dict:
    """Bucht einen der Vorschläge. Gibt die neue Zeile aus gespraechstermine zurück."""
    if b["status"] == "abgelehnt":
        raise HTTPException(400, "Dieses Angebot wurde abgelehnt.")
    if gebucht(cur, b["id"]):
        raise HTTPException(409, "Für dieses Angebot ist schon ein Gespräch gebucht.")
    start = _parse(start_roh)
    if start not in [_parse(x) for x in (b.get("terminvorschlaege") or [])]:
        raise HTTPException(400, "Dieser Termin gehört nicht zu den Vorschlägen.")
    c = lesen(cur)
    ende = start + timedelta(minutes=c["dauer"])
    nicht_frei = HTTPException(409, "Dieser Vorschlag ist leider nicht mehr frei. Bitte wählen Sie einen anderen oder rufen Sie uns kurz an.")
    if start <= datetime.now(timezone.utc) or _belegt(cur, start, ende):
        raise nicht_frei
    emp = b.get("empfaenger") or {}
    name = (emp.get("ansprechpartner") or emp.get("firma") or b.get("lead_firma") or "Interessent").strip()
    email = (emp.get("email") or "").strip().lower()
    try:
        cur.execute("""INSERT INTO gespraechstermine (start, ende, name, email, lead_id, token, gebucht_von, beleg_id, nachricht)
                       VALUES (%s,%s,%s,%s,%s,%s,'angebot',%s,%s) RETURNING id, start, ende, name, email, token""",
                    (start, ende, name, email, b["lead_id"], secrets.token_urlsafe(24), b["id"], f"Beratungsgespräch zu Angebot {b['nummer']}"))
    except Exception:
        raise nicht_frei
    g = cur.fetchone()
    g["ort"] = c["ort"]
    if b["lead_id"]:
        cur.execute("UPDATE leads SET status=CASE WHEN status IN ('neu','kontaktiert','antwort') THEN 'termin' ELSE status END, wiedervorlage_am=%s, letzter_kontakt_am=now() WHERE id=%s",
                    (start.astimezone(TZ).date(), b["lead_id"]))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von, ergebnis) VALUES (%s,'termin',%s,'Angebotsseite','termin')",
                    (b["lead_id"], f"Beratungsgespräch zu Angebot {b['nummer']} gewählt: {lokal(start)}"))
    return g


def mails(g: dict, nummer: str, an_team: list):
    wann = lokal(g["start"])
    absagen = f"{config.BASE_URL}/api/public/buchung/absagen?t={g['token']}"
    anhang = ("termin.ics", ics(str(g["id"]), g["start"], g["ende"], "Beratungsgespräch mit Markentrix", g["ort"]), "text/calendar")
    if g["email"]:
        mailer.senden(g["email"], "Ihr Beratungsgespräch mit Markentrix am " + wann,
                      f"Guten Tag {g['name']},\n\nvielen Dank, Ihr Beratungsgespräch zum Angebot {nummer} ist vereinbart: {wann}.\n{g['ort']}\n\n"
                      f"Die Kalendereinladung hängt an. Falls Sie nicht können, sagen Sie bitte hier ab: {absagen}" + mailer.SIGNATUR, anhang)
    for a in an_team:
        mailer.senden(a, f"Beratungsgespräch gewählt: {g['name']} am {wann}",
                      f"{g['name']} hat im Angebot {nummer} den Termin {wann} gewählt. Er steht im Admin-Kalender: {config.BASE_URL}/admin", anhang)


def mailtext(liste: list, link: str | None) -> str:
    """Absatz für die Angebots-Mail; leer, wenn keine Vorschläge da sind."""
    if not liste:
        return ""
    zeilen = "\n".join("  • " + lokal(_parse(x)) for x in liste)
    return ("Für ein kurzes Beratungsgespräch zum Angebot schlagen wir Ihnen diese Termine vor:\n" + zeilen + "\n"
            + ("Sie können einen davon direkt im Link auswählen, er landet dann sofort in unserem Kalender.\n\n" if link else "Sagen Sie uns einfach kurz, welcher Termin passt.\n\n"))
