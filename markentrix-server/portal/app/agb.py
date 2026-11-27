"""AGB: aktive Version, Anhang für Mails und Prüfung, ob ein Kunde die aktive Version schon bestätigt hat."""
from .db import tx


def aktiv(cur) -> dict | None:
    cur.execute("SELECT id, version, dateiname, sha256, mitsenden, login_pflicht, erstellt_am FROM agb_versionen WHERE aktiv")
    return cur.fetchone()


def anhang() -> tuple[str, bytes, str] | None:
    """(Dateiname, PDF, MIME) für Angebots- und Rechnungsmails, wenn eine AGB aktiv ist und mitgesendet werden soll."""
    try:
        with tx("system") as cur:
            cur.execute("SELECT dateiname, datei FROM agb_versionen WHERE aktiv AND mitsenden")
            r = cur.fetchone()
        return (r["dateiname"], bytes(r["datei"]), "application/pdf") if r else None
    except Exception:       # Mail darf nie an der AGB scheitern
        return None


def offen(cur, kunden_id) -> dict | None:
    """Die aktive Version, wenn der Kunde sie bestätigen muss (Pflicht beim Anmelden, noch keine Bestätigung zu dieser Version)."""
    a = aktiv(cur)
    if not a or not a["login_pflicht"]:
        return None
    cur.execute("SELECT 1 FROM agb_zustimmungen WHERE kunden_id=%s AND agb_id=%s LIMIT 1", (kunden_id, a["id"]))
    return None if cur.fetchone() else {"id": str(a["id"]), "version": a["version"]}


def vorhanden() -> bool:
    try:
        with tx("system") as cur:
            return aktiv(cur) is not None
    except Exception:
        return False
