"""Vertragsende: Datenexport (ZIP) und Löschung der Kundeninhalte.
Bewusst NICHT gelöscht werden Stammdaten (Name, Anschrift, Kundennummer), Rechnungen/Angebote/Verträge, Buchungen, Provisionen, AVV und das Audit-Log,
weil dafür gesetzliche Aufbewahrungspflichten gelten können (z. B. Rechnungen). Kontaktdaten der Ansprechperson werden entfernt."""
import io
import json
import shutil
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from . import berichte, belege, config, rechtstexte

EXPORT_TABELLEN = ["anfragen", "termine", "kontakte", "nachrichten", "anrufe", "chat_verlauf", "wissensbasis", "berichte", "bewertungsanfragen",
                   "content_plaene", "content_beitraege", "newsletter_kampagnen", "einwilligungen", "wochenangebote_uploads", "websites",
                   "angebote", "vertraege", "projekte", "buchungen", "belege", "avv", "agent_laeufe",
                   "tickets", "ticket_nachrichten", "kundenfreigaben", "zufriedenheit", "angebots_inhalte", "briefings", "kennzahlen_extern", "kunden_werkzeuge", "antwortvorlagen_kunde", "domains", "website_termine", "website_leistungen", "website_gutscheine"]
# Selbstbedienungs-Export des Kunden: nur, was der Kunde auch im Portal sehen darf (entspricht den Richtlinien der Datenbank).
# Die Abfragen laufen mit Systemrechten, deshalb wird die Sichtbarkeit hier ausdrücklich nachgebaut.
KUNDE_SIEHT = {"ticket_nachrichten": "NOT intern", "belege": "status<>'entwurf'"}
KUNDE_OHNE_FELDER = {"belege": ("notiz",)}
# Inhalte, die bei der Löschung entfernt werden (Reihenfolge ist egal, es gibt keine Abhängigkeiten untereinander außer SET NULL / CASCADE)
LOESCH_TABELLEN = ["anfragen", "termine", "kontakte", "nachrichten", "anrufe", "chat_verlauf", "wissensbasis", "berichte", "bewertungsanfragen",
                   "content_plaene", "content_beitraege", "newsletter_kampagnen", "einwilligungen", "wochenangebote_uploads", "agent_laeufe",
                   "prompts", "freigaben", "projekte", "websites", "tickets", "kundenfreigaben", "zufriedenheit", "aufgaben", "dateien", "angebots_inhalte", "briefings", "kennzahlen_extern", "kunden_werkzeuge", "antwortvorlagen_kunde", "domains"]


def _json(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (bytes, bytearray, memoryview)):
        return None
    return str(o)


def _upload_dir(kid) -> Path:
    return (config.UPLOAD_DIR / str(kid)).resolve()


def export_zip(cur, kid, fuer_kunde: bool = False) -> bytes:
    """Mit fuer_kunde=True (Selbstbedienung im Kundenportal) fehlen interne Team-Notizen."""
    cur.execute("SELECT * FROM kunden WHERE id=%s", (kid,))
    k = cur.fetchone()
    if not k:
        return b""
    k.pop("logo", None)
    if fuer_kunde:
        for feld in ("notizen", "vertriebspartner_id"):
            k.pop(feld, None)
    puffer = io.BytesIO()
    f = rechtstexte.firma(cur)
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LIESMICH.txt", f"Datenexport für {k['firma']} ({k['kundennummer']}), erstellt am {datetime.now():%d.%m.%Y %H:%M}.\n\n"
                   "daten/    alle gespeicherten Daten als JSON-Dateien (eine Datei je Bereich)\n"
                   "belege/   Angebote und Rechnungen als PDF\n"
                   "berichte/ Monatsberichte als PDF\n"
                   "avv/      Auftragsverarbeitungsvertrag (unterschrieben)\n"
                   "uploads/  hochgeladene Dateien (z. B. Wochenangebote)\n"
                   "dateien/  Dokumentenablage und Anhänge aus Nachrichten und Freigaben\n"
                   "websites/ die Dateien Ihrer Website(n)\n")
        z.writestr("daten/kunde.json", json.dumps(k, default=_json, ensure_ascii=False, indent=1))
        cur.execute("SELECT id, email, name, rolle, kunden_rolle, aktiv, letzter_login, erstellt_am FROM benutzer WHERE kunden_id=%s", (kid,))
        z.writestr("daten/zugaenge.json", json.dumps(cur.fetchall(), default=_json, ensure_ascii=False, indent=1))
        for t in EXPORT_TABELLEN:
            cur.execute(f"SELECT * FROM {t} WHERE kunden_id=%s" + (f" AND {KUNDE_SIEHT[t]}" if fuer_kunde and t in KUNDE_SIEHT else ""), (kid,))  # t stammt aus der festen Liste oben
            zeilen = cur.fetchall()
            if fuer_kunde:   # interne Felder gehören dem Team, nicht dem Kunden
                for zeile in zeilen:
                    for feld in KUNDE_OHNE_FELDER.get(t, ()):
                        zeile.pop(feld, None)
            z.writestr(f"daten/{t}.json", json.dumps(zeilen, default=_json, ensure_ascii=False, indent=1))
        cur.execute("SELECT id, nummer, art FROM belege WHERE kunden_id=%s AND status<>'entwurf' AND nummer IS NOT NULL", (kid,))
        for b in cur.fetchall():
            try:
                daten, name = belege.beleg_pdf(cur, b["id"], f)
                z.writestr(f"belege/{name}", daten)
            except Exception:
                z.writestr(f"belege/{b['nummer']}-FEHLER.txt", "Das PDF konnte nicht erzeugt werden. Die Daten stehen in daten/belege.json.")
        cur.execute("SELECT id FROM berichte WHERE kunden_id=%s AND art='monatsbericht'", (kid,))
        for b in cur.fetchall():
            try:
                daten, name = berichte.pdf_erzeugen(cur, b["id"], f)
                z.writestr(f"berichte/{name}", daten)
            except Exception:
                pass
        cur.execute("SELECT id, datei, datei_name, unterschrieben_am FROM avv WHERE kunden_id=%s AND datei IS NOT NULL", (kid,))
        for a in cur.fetchall():
            z.writestr(f"avv/{a['unterschrieben_am']}-{(a['datei_name'] or 'AVV')}", bytes(a["datei"]))
        cur.execute("SELECT id, name, bereich, kategorie, daten FROM dateien WHERE kunden_id=%s" + (" AND sichtbar_kunde" if fuer_kunde else ""), (kid,))
        for d in cur.fetchall():
            z.writestr(f"dateien/{d['bereich']}/{str(d['id'])[:8]}-{d['name']}", bytes(d["daten"]))
        _websites_dazu(z, cur, kid)
        basis = _upload_dir(kid)
        cur.execute("SELECT id, dateiname, dateipfad FROM wochenangebote_uploads WHERE kunden_id=%s", (kid,))
        for u in cur.fetchall():
            p = Path(u["dateipfad"]).resolve()
            if p.is_file() and p.is_relative_to(basis):
                z.write(p, f"uploads/{str(u['id'])[:8]}-{u['dateiname']}")
    return puffer.getvalue()


WEBSITE_MAX = 200 * 1024 * 1024


def _websites_dazu(z, cur, kid):
    """Dateien der Live-Websites des Kunden (ohne Symlinks, höchstens 200 MB insgesamt)."""
    import os
    cur.execute("SELECT domain FROM websites WHERE kunden_id=%s AND art='live' AND domain IS NOT NULL", (kid,))
    gesamt = 0
    for w in cur.fetchall():
        wurzel = (config.SITES_ROOT / "live" / w["domain"])
        if wurzel.is_symlink() or not wurzel.is_dir():
            continue
        for root, dirs, files in os.walk(wurzel):
            dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink() and d not in (".vorversionen",)]
            for f in files:
                p = Path(root) / f
                if p.is_symlink() or not p.is_file() or f == "site.json":
                    continue
                gesamt += p.stat().st_size
                if gesamt > WEBSITE_MAX:
                    z.writestr("websites/ZU-GROSS.txt", "Die Website ist größer als 200 MB und wurde nicht vollständig in den Export gepackt. Wir stellen sie auf Wunsch gesondert bereit.")
                    return
                z.write(p, f"websites/{w['domain']}/{p.relative_to(wurzel).as_posix()}")


def loeschen(cur, kid, durch: str) -> dict:
    """Entfernt die Inhalte. Gibt Zähler und die Domains der Websites zurück (deren Ordner räumt der Worker auf). Dateien löscht der Aufrufer NACH dem Commit."""
    cur.execute("SELECT domain, art FROM websites WHERE kunden_id=%s", (kid,))
    sites = cur.fetchall()
    zaehler = {}
    for t in LOESCH_TABELLEN:
        cur.execute(f"DELETE FROM {t} WHERE kunden_id=%s", (kid,))  # feste Liste, keine Benutzereingabe
        zaehler[t] = cur.rowcount
    cur.execute("DELETE FROM benutzer WHERE kunden_id=%s", (kid,))
    zaehler["benutzer"] = cur.rowcount
    cur.execute("""UPDATE kunden SET ansprechpartner=NULL, email=NULL, telefon=NULL, notizen=NULL, benachr_email=NULL, logo=NULL, logo_typ=NULL, branding_farbe=NULL,
                   status='beendet', geloescht_am=now() WHERE id=%s""", (kid,))
    for t, n in zaehler.items():
        if n:
            cur.execute("INSERT INTO loeschprotokoll (tabelle, geloescht_anzahl, ausgeloest_durch) VALUES (%s,%s,%s)", (f"{t} (Kunde {kid})", n, durch))
    return {"zaehler": zaehler, "websites": sites}


def dateien_entfernen(kid):
    basis = _upload_dir(kid)
    if basis.is_dir() and basis.parent == config.UPLOAD_DIR.resolve():
        shutil.rmtree(basis, ignore_errors=True)
