import json
import os
import re
import secrets
from pathlib import Path

from urllib.parse import urlparse

from psycopg import errors
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, mailer, webbetrieb
from .db import tx
from .security import audit, rate_limit, require_admin

router = APIRouter(prefix="/api/admin/websites")

SITES = config.SITES_ROOT
QUEUE = config.QUEUE_DIR
NAME = {"live": re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$"), "demo": re.compile(r"^[a-z0-9]([a-z0-9-]{0,40}[a-z0-9])?$")}
TRASH_ID = re.compile(r"^\d{8}-\d{6}__(live|demo)__[A-Za-z0-9.-]{1,253}$")


def groesse(d: Path):
    s = n = 0
    newest = 0
    for root, _dirs, files in os.walk(d):
        for f in files:
            try:
                st = os.lstat(os.path.join(root, f))
            except OSError:
                continue
            s += st.st_size
            n += 1
            newest = max(newest, st.st_mtime)
    return s, n, newest


def ausstehend():
    out = []
    if QUEUE.is_dir():
        for f in QUEUE.glob("auftrag-*.json"):
            try:
                out.append(json.loads(f.read_text()))
            except Exception:
                pass
    return out


@router.get("")
def liste(user: dict = Depends(require_admin)):
    offen = {(a.get("art"), a.get("name")) for a in ausstehend() if a.get("aktion") == "loeschen"}
    aktiv = []
    freigaben = {}
    with tx("admin") as cur:
        cur.execute("""SELECT DISTINCT ON (f.demo_name) f.demo_name, f.status, f.angefragt_am, f.entschieden_am, f.entschieden_name, f.kommentar, k.firma
                       FROM kundenfreigaben f JOIN kunden k ON k.id = f.kunden_id WHERE f.demo_name IS NOT NULL ORDER BY f.demo_name, f.angefragt_am DESC""")
        freigaben = {r["demo_name"]: {k: r[k] for k in ("status", "angefragt_am", "entschieden_am", "entschieden_name", "kommentar", "firma")} for r in cur.fetchall()}
        cur.execute("SELECT w.domain, w.kunden_id, k.firma FROM websites w JOIN kunden k ON k.id = w.kunden_id WHERE w.art = 'live'")
        eigner = {r["domain"]: {"kunden_id": str(r["kunden_id"]), "firma": r["firma"]} for r in cur.fetchall()}
        wacht = {w["domain"]: w for w in webbetrieb.status(cur)}
        cur.execute("SELECT domain, ok, geprueft_am FROM domain_pruefung")
        dnsst = {r["domain"]: {"ok": r["ok"], "geprueft_am": r["geprueft_am"]} for r in cur.fetchall()}
    for art, sub in (("live", "live"), ("demo", "demos")):
        basis = SITES / sub
        if not basis.is_dir():
            continue
        for d in sorted(basis.iterdir()):
            if d.is_symlink() or not d.is_dir() or not NAME[art].match(d.name):
                continue
            s, n, new = groesse(d)
            kunde = ""
            try:
                kunde = str(json.loads((d / "site.json").read_text()).get("kunde", ""))
            except Exception:
                pass
            aktiv.append({"art": art, "name": d.name, "freigabe": freigaben.get(d.name) if art == "demo" else None, "groesse": s, "dateien": n, "geaendert": new, "kunde": kunde,
                          "loeschung_laeuft": (art, d.name) in offen, "wacht": wacht.get(d.name) if art == "live" else None, "eigner": eigner.get(d.name) if art == "live" else None, "dns": dnsst.get(d.name) if art == "live" else None})
    korb = []
    t = SITES / ".papierkorb"
    if t.is_dir():
        for d in sorted(t.iterdir(), reverse=True):
            if TRASH_ID.match(d.name) and d.is_dir() and not d.is_symlink():
                art, name = d.name.split("__")[1:3]
                korb.append({"id": d.name, "art": art, "name": name, "geloescht": d.stat().st_mtime, "groesse": groesse(d)[0]})
    return {"aktiv": aktiv, "papierkorb": korb, "aufbewahrung_tage": 14}


@router.get("/domain/{domain}")
def domain_pruefen(domain: str, user: dict = Depends(require_admin)):
    """DNS-Assistent: wohin zeigt die Domain, was ist zu ändern, Text für den Kunden. Speichert das Ergebnis."""
    rate_limit("domainpruefung", 60, 3600)
    domain = domain.strip().lower()
    if not NAME["live"].match(domain):
        raise HTTPException(400, "Ungültige Domain")
    from . import domaincheck
    with tx("admin") as cur:
        cur.execute("SELECT kunden_id FROM websites WHERE domain=%s AND art='live'", (domain,))
        w = cur.fetchone()
        v4, v6 = domaincheck.server_adressen(cur)
    r = domaincheck.pruefen(domain, v4, v6)
    if w:
        with tx("system") as cur:
            cur.execute("""INSERT INTO domain_pruefung (domain, kunden_id, geprueft_am, ok, ergebnis, live_gemeldet) VALUES (%s,%s,now(),%s,%s,false)
                           ON CONFLICT (domain) DO UPDATE SET geprueft_am=now(), ok=EXCLUDED.ok, ergebnis=EXCLUDED.ergebnis""", (domain, w["kunden_id"], r["ok"], json.dumps(r)))
    with tx("system") as cur:
        cur.execute("SELECT kundenmail_am, erinnerungen FROM domain_pruefung WHERE domain=%s", (domain,))
        m = cur.fetchone()
    r["kundenmail_am"] = m["kundenmail_am"] if m else None
    r["erinnerungen"] = m["erinnerungen"] if m else 0
    return r


class DomainIn(BaseModel):
    domain: str


@router.post("/jetzt-pruefen")
def jetzt_pruefen(data: DomainIn, user: dict = Depends(require_admin)):
    """Sofort neu prüfen: DNS, Startseite, Website-API und Zertifikat. Der Wachdienst-Status wird dabei aktualisiert."""
    rate_limit("jetztpruefen", 30, 600)
    domain = data.domain.strip().lower()
    if not NAME["live"].match(domain):
        raise HTTPException(400, "Ungültige Domain")
    from . import domaincheck
    r = domaincheck.einzeln(domain)
    if not r:
        raise HTTPException(404, "Diese Live-Website gibt es nicht.")
    w = r["wacht"]
    if r["dns"]["ok"] and w["ok"]:
        zustand, text = "ok", "Alles in Ordnung: Domain zeigt auf den Server, Seite und Website-API antworten."
    elif not r["dns"]["ok"]:
        zustand, text = "dns", "Die Domain zeigt noch nicht (richtig) auf den Server. Die Anleitung steht unten."
    else:
        zustand, text = "seite", "DNS stimmt, aber die Seite ist noch nicht erreichbar: " + (w["fehler"] or "keine Antwort") + ". Beim ersten Aufruf holt Caddy das Zertifikat, das dauert bis zu einer Minute."
    return {"zustand": zustand, "text": text, "dns": r["dns"], "wacht": w}


@router.post("/domain/{domain}/kundenmail")
def kundenmail(domain: str, user: dict = Depends(require_admin)):
    """Schickt dem Kunden die DNS-Anleitung per Mail. Nach 3 Tagen erinnert der Server automatisch (höchstens zweimal), solange die Domain nicht stimmt."""
    rate_limit("domainkundenmail", 20, 3600)
    domain = domain.strip().lower()
    if not NAME["live"].match(domain):
        raise HTTPException(400, "Ungültige Domain")
    from . import domaincheck
    ok, grund = domaincheck.kundenmail(domain)
    if not ok:
        raise HTTPException(400, grund)
    with tx("admin") as cur:
        audit(cur, user, "dns_anleitung_gesendet", None, {"domain": domain})
    return {"ok": True, "hinweis": "Die Anleitung wurde an " + grund + " geschickt. In 3 Tagen kommt automatisch eine Erinnerung, falls die Domain dann noch nicht stimmt."}


def auftrag(daten: dict):
    try:
        QUEUE.mkdir(exist_ok=True, mode=0o770)
        p = QUEUE / f"auftrag-{secrets.token_hex(8)}.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(daten))
        os.replace(tmp, p)
    except OSError:
        raise HTTPException(500, "Der Auftrag konnte nicht abgelegt werden (Ordner queue fehlt oder ist nicht beschreibbar).")


class LoeschIn(BaseModel):
    art: str
    name: str
    bestaetigung: str


@router.post("/loeschen")
def loeschen(data: LoeschIn, user: dict = Depends(require_admin)):
    if data.art not in NAME or not NAME[data.art].match(data.name):
        raise HTTPException(400, "Ungültiger Name.")
    if data.bestaetigung.strip() != data.name:
        raise HTTPException(400, "Zur Bestätigung muss der Name genau eingetippt werden.")
    basis = SITES / ("live" if data.art == "live" else "demos") / data.name
    if basis.is_symlink() or not basis.is_dir():
        raise HTTPException(404, "Diese Seite gibt es nicht.")
    auftrag({"aktion": "loeschen", "art": data.art, "name": data.name})
    with tx("admin") as cur:
        if data.art == "live":
            cur.execute("UPDATE websites SET status='offline' WHERE domain=%s", (data.name,))
        audit(cur, user, "website_geloescht", None, {"art": data.art, "name": data.name})
    return {"ok": True, "hinweis": "Wird innerhalb einer Minute in den Papierkorb verschoben."}


class WiederIn(BaseModel):
    id: str


@router.post("/wiederherstellen")
def wiederherstellen(data: WiederIn, user: dict = Depends(require_admin)):
    if not TRASH_ID.match(data.id) or not (SITES / ".papierkorb" / data.id).is_dir():
        raise HTTPException(404, "Eintrag nicht gefunden.")
    auftrag({"aktion": "wiederherstellen", "id": data.id})
    with tx("admin") as cur:
        audit(cur, user, "website_wiederhergestellt", None, {"id": data.id})
    return {"ok": True, "hinweis": "Wird innerhalb einer Minute wiederhergestellt."}


class KorbLoeschIn(BaseModel):
    id: str = ""
    alle: bool = False


@router.post("/papierkorb-loeschen")
def papierkorb_loeschen(data: KorbLoeschIn, user: dict = Depends(require_admin)):
    """Löscht Papierkorb-Einträge endgültig (einen oder alle). Der Server-Dienst führt es aus, eine Sicherung bleibt wie üblich in den Backups."""
    if not data.alle and (not TRASH_ID.match(data.id) or not (SITES / ".papierkorb" / data.id).is_dir()):
        raise HTTPException(404, "Eintrag nicht gefunden.")
    auftrag({"aktion": "papierkorb_loeschen", "id": "" if data.alle else data.id, "alle": bool(data.alle)})
    with tx("admin") as cur:
        audit(cur, user, "papierkorb_geloescht", None, {"id": data.id, "alle": data.alle})
    return {"ok": True, "hinweis": "Wird innerhalb einer Minute endgültig gelöscht."}


class VorschauIn(BaseModel):
    kunden_id: str
    demo_name: str
    hinweis: str = Field(default="", max_length=1000)


@router.post("/vorschau-freigabe")
def vorschau_freigabe(data: VorschauIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    """Schickt dem Kunden die Demo-Vorschau seiner neuen Website zur Freigabe (Link ohne Anmeldung). Name, Zeit und Version der Freigabe werden festgehalten."""
    from .routes_zusammenarbeit import _link_erzeugen, _mails, kunden_empfaenger, nicht_gefunden, team_name
    if not NAME["demo"].match(data.demo_name) or not (SITES / "demos" / data.demo_name).is_dir():
        raise HTTPException(404, "Diese Demo gibt es nicht.")
    root = urlparse(config.BASE_URL).hostname or ""
    root = root[7:] if root.startswith("portal.") else root
    url = f"https://demo.{root}/{data.demo_name}/"
    inhalt = (data.hinweis.strip() + "\n\n" if data.hinweis.strip() else "") + "Bitte sehen Sie sich die Vorschau Ihrer neuen Website an:\n" + url + \
        "\n\nWenn alles passt, klicken Sie unten auf „Freigeben“. Wenn etwas geändert werden soll, wählen Sie „Änderung wünschen“ und schreiben uns, was."
    try:
        with tx("admin") as cur:
            cur.execute("SELECT ansprechpartner FROM kunden WHERE id=%s", (data.kunden_id,))
            k = cur.fetchone()
            if not k:
                raise nicht_gefunden()
            cur.execute("""INSERT INTO kundenfreigaben (kunden_id, titel, art, inhalt, angefragt_von, demo_name) VALUES (%s,%s,'website',%s,%s,%s) RETURNING id""",
                        (data.kunden_id, "Vorschau Ihrer neuen Website", inhalt, team_name(user), data.demo_name))
            fid = cur.fetchone()["id"]
            link = _link_erzeugen(cur, fid)
            ziele = kunden_empfaenger(cur, data.kunden_id)
            audit(cur, user, "vorschau_freigabe_angefragt", data.kunden_id, {"demo": data.demo_name})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    _mails(bg, ziele, mailer.freigabe_anfrage_kunde, k["ansprechpartner"], "Vorschau Ihrer neuen Website", link)
    return {"id": fid, "empfaenger": len(ziele or [])}
