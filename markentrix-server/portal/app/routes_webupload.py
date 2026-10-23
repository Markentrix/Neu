"""Website-Upload für Admins: ZIP hochladen, prüfen, bereitstellen. Das Portal hat keine Root-Rechte: Es entpackt nur geprüft in einen
Zwischenordner und legt einen Auftrag ab, den der Server-Dienst (bin/worker.py, jede Minute) ausführt (Caddy einrichten, Ordner tauschen)."""
import json
import re
from urllib.parse import urlparse
import secrets
import shutil
import stat
import zipfile
from pathlib import Path

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from . import config, livecheck
from . import sitedienste as sd
from .db import tx
from .routes_websites import NAME, auftrag
from .security import audit, rate_limit, require_admin

router = APIRouter(prefix="/api/admin/websites")

MAX_ZIP = 120 * 1024 * 1024
MAX_GESAMT = 400 * 1024 * 1024
MAX_DATEI = 120 * 1024 * 1024
MAX_DATEIEN = 6000
ERLAUBT = {"html", "htm", "css", "js", "mjs", "json", "xml", "txt", "ico", "png", "jpg", "jpeg", "gif", "webp", "avif", "svg", "woff", "woff2", "ttf", "otf",
           "map", "webmanifest", "pdf", "mp4", "webm", "mp3", "ogg", "vtt", "csv", "md", "wasm"}
SKRIPT_MARKE = "static/js/site.js"
EGAL = {".ds_store", "thumbs.db", "desktop.ini"}


def _ordner_name(art: str, name: str) -> str:
    if art not in NAME or not NAME[art].match(name):
        raise HTTPException(400, "Der Name ist ungültig. Bei einer Live-Website die Domain ohne www (z. B. firma.de), bei einer Demo nur Kleinbuchstaben, Zahlen und Bindestriche.")
    if art == "live":
        portal = (urlparse(config.BASE_URL).hostname or "").lower()
        eigene = portal.split(".", 1)[1] if portal.count(".") >= 2 else portal
        if name.startswith("www.") or name == portal or (eigene and (name == eigene or name.endswith("." + eigene))):
            raise HTTPException(400, "Diese Adresse gehört zum Portal oder ist mit www angegeben. Bitte die Kundendomain ohne www eintragen (z. B. firma.de).")
    return name


BEVORZUGT = ("website-fertig", "website", "dist", "public", "www", "site", "out", "_site", "html")


def webroot_waehlen(teile_liste: list) -> tuple:
    """Findet den Ordner, der die fertige Website enthält. Liegt die index.html direkt oben, ist es die ZIP-Wurzel.
    Sonst: bevorzugte Namen (website-fertig, dist, public …), sonst der höchste Ordner mit index.html (bei Gleichstand der mit den meisten Dateien)."""
    if any(t == ["index.html"] for t in teile_liste):
        return ()
    kandidaten = {}
    for t in teile_liste:
        if len(t) >= 2 and t[-1] == "index.html" and len(t) <= 4:
            kandidaten[tuple(t[:-1])] = 0
    if not kandidaten:
        return None
    for k in kandidaten:
        kandidaten[k] = sum(1 for t in teile_liste if tuple(t[:len(k)]) == k)
    def rang(k):
        bev = BEVORZUGT.index(k[-1].lower()) if k[-1].lower() in BEVORZUGT else 99
        return (bev, len(k), -kandidaten[k])
    return sorted(kandidaten, key=rang)[0]


def entpacken(zip_pfad: Path, ziel: Path, index_noetig: bool = True) -> tuple:
    """Prüft die ZIP streng und entpackt die Website nach ziel. Gibt (Anzahl Dateien, verwendeter Ordner in der ZIP) zurück.
    Ganze Projektordner sind erlaubt: Es wird nur der Ordner mit der fertigen Website übernommen, alles andere (Server-Code, Build-Skripte, Doku) bleibt draußen."""
    try:
        zf = zipfile.ZipFile(zip_pfad)
    except zipfile.BadZipFile:
        raise HTTPException(400, "Das ist keine gültige ZIP-Datei.")
    with zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > MAX_DATEIEN:
            raise HTTPException(400, f"Die ZIP enthält zu viele Dateien (mehr als {MAX_DATEIEN}).")
        alle = []
        for i in infos:
            roh = i.filename.replace("\\", "/")
            if "\x00" in roh or any(ord(c) < 32 for c in roh):
                raise HTTPException(400, "Die ZIP enthält ungültige Dateinamen.")
            teile = [t for t in roh.split("/") if t not in ("", ".")]
            if not teile:
                continue
            if roh.startswith("/") or ".." in teile or re.match(r"^[A-Za-z]:", teile[0]):
                raise HTTPException(400, "Die ZIP enthält unsichere Pfade und wurde abgelehnt.")
            if (i.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise HTTPException(400, "Die ZIP enthält Verknüpfungen (Symlinks) und wurde abgelehnt.")
            if i.flag_bits & 1:
                raise HTTPException(400, "Die ZIP ist passwortgeschützt. Bitte ohne Passwort packen.")
            if teile[0] == "__MACOSX" or teile[-1].lower() in EGAL:
                continue
            if any(t.startswith(".") and t != ".well-known" for t in teile):
                continue           # versteckte Dateien (.git, .htaccess …) gehören nicht auf die Website
            alle.append((i, teile))
        if not alle:
            raise HTTPException(400, "Die ZIP enthält keine Website-Dateien.")
        # Eine einzelne Hülle (z. B. „firma/“) abstreifen, damit die Suche nach dem Website-Ordner einfach bleibt
        wurzel_ordner = ""
        if len({t[0] for _, t in alle}) == 1 and all(len(t) > 1 for _, t in alle):
            wurzel_ordner = alle[0][1][0]
            alle = [(i, t[1:]) for i, t in alle]
        wr = webroot_waehlen([t for _, t in alle])
        if wr is None and not index_noetig:
            wr = ()            # weitere ZIPs einer mehrteiligen Website (nur Bilder, CSS …) brauchen keine eigene index.html
        if wr is None:
            raise HTTPException(400, "In der ZIP wurde keine index.html gefunden. Bitte die fertige Website (mit index.html) packen.")
        eintraege = [(i, t[len(wr):]) for i, t in alle if tuple(t[:len(wr)]) == wr and len(t) > len(wr)]
        verwendet = "/".join(([wurzel_ordner] if wurzel_ordner else []) + list(wr)) or "(oberste Ebene)"
        verboten = []
        brauchbar = []
        for i, t in eintraege:
            ext = t[-1].rsplit(".", 1)[-1].lower() if "." in t[-1] else ""
            if ext not in ERLAUBT:
                verboten.append("/".join(t))
                continue
            if i.file_size > MAX_DATEI:
                raise HTTPException(400, f"Die Datei {'/'.join(t)} ist zu groß.")
            brauchbar.append((i, t))
        if verboten:
            raise HTTPException(400, "Im Website-Ordner (" + verwendet + ") liegen Dateitypen, die auf einer Website nicht erlaubt sind: " + ", ".join(verboten[:6]) + (" …" if len(verboten) > 6 else "") + ". Bitte aus der ZIP entfernen.")
        eintraege = brauchbar
        if sum(i.file_size for i, _ in eintraege) > MAX_GESAMT:
            raise HTTPException(400, "Die Website ist entpackt zu groß (über 400 MB).")
        ziel.mkdir(parents=True, exist_ok=True)
        wurzel = ziel.resolve()
        gesamt = 0
        for i, t in eintraege:
            dest = (ziel / "/".join(t)).resolve()
            if wurzel not in dest.parents:
                raise HTTPException(400, "Die ZIP enthält unsichere Pfade und wurde abgelehnt.")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(i) as q, open(dest, "wb") as z:
                while True:
                    block = q.read(1 << 20)
                    if not block:
                        break
                    gesamt += len(block)
                    if gesamt > MAX_GESAMT:
                        raise HTTPException(400, "Die Website ist entpackt zu groß (über 400 MB).")
                    z.write(block)
            dest.chmod(0o644)
        return len(eintraege), verwendet


DATENSCHUTZ_SEITEN = ("datenschutz.html", "datenschutz.htm", "datenschutzerklaerung.html", "datenschutz/index.html", "datenschutz/index.htm")


def datenschutz_pfad(ordner: Path) -> str:
    """Adresse der Datenschutzseite dieser Website, falls es eine gibt (z. B. /datenschutz.html). Das Skript verlinkt sonst /datenschutz, das bei Seiten mit .html-Endung 404 liefert."""
    for name in DATENSCHUTZ_SEITEN:
        f = ordner / name
        if f.is_file() and not f.is_symlink():
            return "/" + (name[:-len("index.html")] if name.endswith("/index.html") else name[:-len("index.htm")] if name.endswith("/index.htm") else name)
    return ""


SKRIPT_TAG = re.compile(r'<script\b[^>]*' + re.escape(SKRIPT_MARKE) + r'[^>]*>', re.I)
KENNUNG = re.compile(r'(\sdata-site=)(["\']?)([^"\'\s>]*)\2', re.I)   # mit doppelten, einfachen oder ohne Anführungszeichen


def _seiten(ordner: Path):
    for p in list(ordner.rglob("*.html")) + list(ordner.rglob("*.htm")):
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 3_000_000:
            continue
        try:
            yield p, p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def skript_ersetzen(ordner: Path, site_id: str) -> int:
    """Setzt in Seiten, die das Dienste-Skript schon enthalten, die Kennung der Website auf die des Kunden (z. B. wenn die Demo einem anderen Kunden gehörte).
    Die Reihenfolge der Attribute im Skript-Tag spielt keine Rolle."""
    n = 0
    ds = datenschutz_pfad(ordner)
    for p, t in _seiten(ordner):
        def tag(m):
            x = KENNUNG.sub(lambda k: k.group(1) + '"' + site_id + '"', m.group(0))
            if ds and "data-datenschutz=" not in x:
                x = x[:-1].rstrip() + f' data-datenschutz="{ds}">'
            return x
        neu = SKRIPT_TAG.sub(tag, t)
        if neu != t:
            p.write_text(neu, encoding="utf-8")
            n += 1
    return n


def fremde_kennung_entfernen(ordner: Path, erlaubt: str | None) -> int:
    """Entfernt aus dem Dienste-Skript jede Kennung (data-site), die nicht zu diesem Kunden gehört. Ohne Kennung tut das Skript nichts,
    so kann eine mitgebrachte Seite (Demo, Kopie einer anderen Kundenseite) nie Anfragen an das Postfach eines fremden Kunden schicken."""
    n = 0
    for p, t in _seiten(ordner):
        def tag(m):
            return KENNUNG.sub(lambda k: k.group(0) if erlaubt and k.group(3) == erlaubt else "", m.group(0))
        neu = SKRIPT_TAG.sub(tag, t)
        if neu != t:
            p.write_text(neu, encoding="utf-8")
            n += 1
    return n


def skript_einfuegen(ordner: Path, site_id: str, basis: str) -> int:
    """Fügt das Skript der Website-Dienste vor </body> jeder HTML-Seite ein (einmal, ohne Doppelung)."""
    ds = datenschutz_pfad(ordner)
    tag = f'<script src="{basis}/static/js/site.js" data-site="{site_id}"' + (f' data-datenschutz="{ds}"' if ds else '') + ' defer></script>\n'
    n = 0
    for p in list(ordner.rglob("*.html")) + list(ordner.rglob("*.htm")):
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 3_000_000:
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if SKRIPT_MARKE in t:
            continue
        stellen = [m.start() for m in re.finditer(r"</body\s*>", t, re.I)]
        if not stellen:
            continue
        p.write_text(t[:stellen[-1]] + tag + t[stellen[-1]:], encoding="utf-8")
        n += 1
    return n


def _kunde_aufloesen(art: str, name: str, kunden_id: str) -> tuple:
    """Kunde zur Website bestimmen (Auswahl, Kundennummer oder bestehende Domain). Gibt (Kunden-ID, Firma, Kundennummer) zurück."""
    kid, firma, nr = None, "", ""
    with tx("admin") as cur:
        if re.match(r"^MK-?\d+$", kunden_id.strip(), re.I):         # auch die Kundennummer (MK-1001) wird als Auswahl akzeptiert
            cur.execute("SELECT id FROM kunden WHERE upper(kundennummer)=upper(%s)", (kunden_id.strip(),))
            g = cur.fetchone()
            if not g:
                raise HTTPException(400, "Diese Kundennummer gibt es nicht.")
            kunden_id = str(g["id"])
        if art == "live":
            cur.execute("SELECT kunden_id FROM websites WHERE domain=%s", (name,))
            w = cur.fetchone()
            if w:
                kid = w["kunden_id"]
                if kunden_id and str(kunden_id) != str(kid):
                    raise HTTPException(400, "Diese Domain gehört schon zu einem anderen Kunden.")
            elif not kunden_id:
                raise HTTPException(400, "Bitte den Kunden wählen, zu dem diese Website gehört.")
            else:
                kid = kunden_id
        if kid:
            try:
                cur.execute("SELECT firma, kundennummer, domain FROM kunden WHERE id=%s", (kid,))
            except Exception:
                raise HTTPException(400, "Kunde nicht gefunden.")
            k = cur.fetchone()
            if not k:
                raise HTTPException(400, "Kunde nicht gefunden.")
            firma, nr = k["firma"], k["kundennummer"]
            if art == "live" and not k.get("domain"):
                cur.execute("UPDATE kunden SET domain=%s WHERE id=%s", (name, kid))
    return kid, firma, nr


def _abschliessen(user: dict, art: str, name: str, kid, firma: str, nr: str, stage: Path, inhalt: Path, n: int, verwendet: str, skript: bool,
                  zusatz: dict | None = None, melden: bool = False, hinweis: str = "") -> tuple:
    """Gemeinsamer Schluss von Upload und „Demo live schalten“: Website-Dienste einbauen, Website eintragen, prüfen, Auftrag für den Server-Dienst ablegen."""
    eingefuegt = 0
    with tx("admin") as cur:
        site_id = None
        if kid and skript:
            site_id = sd.zeile(cur, kid)["site_id"]
            eingefuegt = skript_ersetzen(inhalt, site_id) + skript_einfuegen(inhalt, site_id, config.BASE_URL)
        elif kid:
            cur.execute("SELECT site_id FROM website_dienste WHERE kunden_id=%s", (kid,))
            r = cur.fetchone()
            site_id = r["site_id"] if r else None
        entfernt = fremde_kennung_entfernen(inhalt, site_id)   # nie die Kennung eines anderen Kunden mitveröffentlichen
        if art == "live":
            cur.execute("""INSERT INTO websites (kunden_id, domain, art, status, letzte_veroeffentlichung) VALUES (%s,%s,'live','live',now())
                           ON CONFLICT (domain) DO UPDATE SET status='live', letzte_veroeffentlichung=now()""", (kid, name))
        audit(cur, user, "website_hochgeladen", kid, {"art": art, "name": name, "dateien": n, "ordner": verwendet, "kunde_informiert": bool(melden and art == "live" and kid), "fremde_kennung_entfernt": entfernt, **(zusatz or {})})
        if melden and art == "live" and kid:
            cur.execute("INSERT INTO website_meldungen (kunden_id, domain, upload_id, hinweis) VALUES (%s,%s,%s,%s)", (kid, name, stage.name.removeprefix(".upload-"), hinweis.strip()[:1000]))
    try:
        check = livecheck.pruefen(inhalt)
    except Exception:  # noqa: BLE001
        check = None
    # Der Server-Dienst erwartet den Inhalt direkt im Zwischenordner
    for p in list(inhalt.iterdir()):
        shutil.move(str(p), str(stage / p.name))
    inhalt.rmdir()
    auftrag({"aktion": "veroeffentlichen", "art": art, "name": name, "upload": stage.name.removeprefix(".upload-"), "kunde": (nr + " " + firma)[:60].strip()})
    return eingefuegt, check


@router.post("/upload")
def hochladen(datei: list[UploadFile] = File(...), art: str = Form("live"), name: str = Form(...), kunden_id: str = Form(""), dienste_skript: str = Form("0"), kunde_informieren: str = Form("0"), aenderung: str = Form(""),
              user: dict = Depends(require_admin)):
    rate_limit("webupload:" + str(user["id"]), 60, 600)
    name = _ordner_name(art, name.strip().lower())
    if not datei or len(datei) > 10:
        raise HTTPException(400, "Bitte 1 bis 10 ZIP-Dateien wählen.")
    if any(not (d.filename or "").lower().endswith(".zip") for d in datei):
        raise HTTPException(400, "Bitte eine ZIP-Datei wählen.")
    if not config.SITES_LIVE.is_dir():
        raise HTTPException(500, "Der Website-Ordner ist im Portal nicht verfügbar.")
    kid, firma, nr = _kunde_aufloesen(art, name, kunden_id)
    uid = secrets.token_hex(8)
    stage = config.SITES_LIVE / f".upload-{uid}"
    try:
        stage.mkdir(mode=0o755)
        inhalt = stage / "inhalt"
        n, teile, gross = 0, [], 0
        for nr_zip, d in enumerate(datei, 1):
            zip_pfad = stage / f"_upload{nr_zip}.zip"
            with open(zip_pfad, "wb") as z:
                while True:
                    block = d.file.read(1 << 20)
                    if not block:
                        break
                    gross += len(block)
                    if gross > MAX_ZIP:
                        raise HTTPException(400, "Die ZIP-Dateien sind zusammen zu groß (über 120 MB). Bitte Bilder und Videos verkleinern.")
                    z.write(block)
            try:
                n1, v1 = entpacken(zip_pfad, inhalt, index_noetig=len(datei) == 1)
            except HTTPException as e:
                if len(datei) > 1:
                    raise HTTPException(400, f"ZIP {nr_zip} ({d.filename}): {e.detail}")
                raise
            zip_pfad.unlink()
            n += n1
            teile.append(v1)
        if not (inhalt / "index.html").is_file():
            raise HTTPException(400, "Nach dem Zusammenführen fehlt die index.html. Mindestens eine ZIP muss sie enthalten.")
        verwendet = " + ".join(teile)
        eingefuegt, check = _abschliessen(user, art, name, kid, firma, nr, stage, inhalt, n, verwendet, dienste_skript == "1",
                                          melden=kunde_informieren == "1", hinweis=aenderung)
    except HTTPException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    except OSError:
        shutil.rmtree(stage, ignore_errors=True)
        raise HTTPException(500, "Die Dateien konnten nicht abgelegt werden (Speicherplatz oder Rechte).")
    return {"ok": True, "id": uid, "dateien": n, "ordner": verwendet, "skript_in_seiten": eingefuegt, "check": check,
            "hinweis": "Hochgeladen und geprüft. Die Website wird innerhalb einer Minute veröffentlicht, unten erscheint das Ergebnis."}


def demo_kopieren(quelle: Path, ziel: Path) -> tuple:
    """Kopiert den Inhalt einer Demo (ohne Verknüpfungen, versteckte Dateien, Wochenangebote und site.json) in einen Zwischenordner. Gibt (Anzahl, Größe) zurück."""
    n, gesamt = 0, 0
    wurzel = quelle.resolve()
    ziel.mkdir(parents=True, exist_ok=True)
    for pf in sorted(quelle.rglob("*")):
        rel = pf.relative_to(quelle)
        teile = rel.parts
        if pf.is_symlink():
            raise HTTPException(400, "Die Demo enthält Verknüpfungen (Symlinks) und kann nicht übernommen werden.")
        if teile[0] in ("angebote", "site.json") or any(t.startswith(".") and t != ".well-known" for t in teile) or teile[-1].lower() in EGAL:
            continue
        if wurzel not in pf.resolve().parents:
            raise HTTPException(400, "Die Demo enthält unsichere Pfade.")
        if pf.is_dir():
            (ziel / rel).mkdir(parents=True, exist_ok=True)
            continue
        if not pf.is_file():
            raise HTTPException(400, "Die Demo enthält unerlaubte Dateien.")
        ext = pf.suffix[1:].lower()
        if ext not in ERLAUBT:
            raise HTTPException(400, f"In der Demo liegt ein nicht erlaubter Dateityp: {rel}")
        n += 1
        gesamt += pf.stat().st_size
        if n > MAX_DATEIEN or gesamt > MAX_GESAMT:
            raise HTTPException(400, "Die Demo ist zu groß.")
        (ziel / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pf, ziel / rel)
        (ziel / rel).chmod(0o644)
    if not (ziel / "index.html").is_file():
        raise HTTPException(400, "In der Demo fehlt die index.html.")
    return n, gesamt


class DemoLiveIn(BaseModel):
    demo: str
    domain: str
    kunden_id: str = ""
    trotzdem: bool = False
    kunde_informieren: bool = True
    aenderung: str = Field(default="", max_length=1000)


@router.post("/demo-zu-live")
def demo_zu_live(data: DemoLiveIn, user: dict = Depends(require_admin)):
    """Eine geprüfte Demo mit einem Klick als Live-Website auf die Kundendomain legen (gleicher Weg wie der Upload: Check, Sicherung, Caddy, Zertifikat)."""
    rate_limit("demolive:" + str(user["id"]), 20, 600)
    demo = _ordner_name("demo", data.demo.strip().lower())
    name = _ordner_name("live", data.domain.strip().lower())
    quelle = config.SITES_ROOT / "demos" / demo
    if quelle.is_symlink() or not quelle.is_dir():
        raise HTTPException(404, "Diese Demo gibt es nicht.")
    if not config.SITES_LIVE.is_dir():
        raise HTTPException(500, "Der Website-Ordner ist im Portal nicht verfügbar.")
    with tx("admin") as cur:
        cur.execute("SELECT status FROM kundenfreigaben WHERE demo_name=%s ORDER BY angefragt_am DESC LIMIT 1", (demo,))
        f = cur.fetchone()
    freigabe = f["status"] if f else None
    if freigabe and freigabe != "freigegeben" and not data.trotzdem:
        raise HTTPException(409, {"wartet": "Der Kunde hat diese Vorschau noch nicht freigegeben", "abgelehnt": "Der Kunde hat diese Vorschau abgelehnt",
                                  "zurueckgezogen": "Die Freigabe-Anfrage wurde zurückgezogen"}.get(freigabe, "Die Vorschau ist nicht freigegeben")
                            + ". Wirklich trotzdem live schalten?")
    kid, firma, nr = _kunde_aufloesen("live", name, data.kunden_id)
    uid = secrets.token_hex(8)
    stage = config.SITES_LIVE / f".upload-{uid}"
    try:
        stage.mkdir(mode=0o755)
        inhalt = stage / "inhalt"
        n, _ = demo_kopieren(quelle, inhalt)
        eingefuegt, check = _abschliessen(user, "live", name, kid, firma, nr, stage, inhalt, n, "Demo " + demo, True,
                                          {"aus_demo": demo, "freigabe": freigabe or "keine Anfrage"}, melden=data.kunde_informieren, hinweis=data.aenderung)
    except HTTPException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    except OSError:
        shutil.rmtree(stage, ignore_errors=True)
        raise HTTPException(500, "Die Dateien konnten nicht abgelegt werden (Speicherplatz oder Rechte).")
    return {"ok": True, "id": uid, "dateien": n, "skript_in_seiten": eingefuegt, "check": check, "freigabe": freigabe,
            "hinweis": f"Die Demo „{demo}“ wird innerhalb einer Minute als {name} veröffentlicht. Damit sie dort erreichbar ist, muss die Domain auf den Server zeigen; unter „DNS prüfen“ steht, was zu tun ist."}


@router.post("/zurueck")
def zurueck(daten: dict, user: dict = Depends(require_admin)):
    art, name = str(daten.get("art", "")), str(daten.get("name", ""))
    _ordner_name(art, name)
    uid = secrets.token_hex(8)
    auftrag({"aktion": "zurueck", "art": art, "name": name, "upload": uid})
    with tx("admin") as cur:
        audit(cur, user, "website_zurueck", None, {"art": art, "name": name})
    return {"ok": True, "hinweis": "Die vorige Version wird innerhalb einer Minute wiederhergestellt."}


TAG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")


@router.get("/livecheck")
def livecheck_live(art: str = "live", name: str = "", user: dict = Depends(require_admin)):
    """Livegang-Check für eine bereits veröffentlichte Seite."""
    rate_limit("livecheck", 60, 3600)
    _ordner_name(art, name)
    ordner = (config.SITES_LIVE if art == "live" else config.SITES_ROOT / "demos") / name
    if ordner.is_symlink() or not ordner.is_dir():
        raise HTTPException(404, "Diese Seite gibt es nicht.")
    return livecheck.pruefen(ordner)


@router.get("/sicherungen")
def sicherungen(user: dict = Depends(require_admin)):
    """Vorhandene Tagessicherungen (vom Server-Auftragsdienst jede Minute aktualisiert)."""
    try:
        d = json.loads((config.QUEUE_DIR / "sicherungen.json").read_text())
        return {"tage": [t for t in d.get("tage", []) if TAG_RE.match(str(t))], "stand": d.get("stand")}
    except (OSError, ValueError):
        return {"tage": [], "stand": None}


@router.post("/aus-sicherung")
def aus_sicherung(daten: dict, user: dict = Depends(require_admin)):
    art, name, tag = str(daten.get("art", "")), str(daten.get("name", "")), str(daten.get("tag", ""))
    _ordner_name(art, name)
    if not TAG_RE.match(tag):
        raise HTTPException(400, "Ungültiges Sicherungsdatum.")
    rate_limit("sicherung-admin", 10, 600)
    uid = secrets.token_hex(8)
    auftrag({"aktion": "sicherung", "art": art, "name": name, "tag": tag, "upload": uid, "kunde": str(daten.get("kunde", ""))[:60]})
    with tx("admin") as cur:
        audit(cur, user, "website_aus_sicherung", None, {"art": art, "name": name, "tag": tag})
    return {"ok": True, "hinweis": "Die Website wird innerhalb einer Minute aus der Sicherung vom " + tag[:10] + " geholt. Die jetzige Version bleibt als Vorversion erhalten. Termine und Anfragen in der Datenbank bleiben unverändert."}


@router.get("/veroeffentlichungen")
def verlauf(user: dict = Depends(require_admin)):
    q = config.QUEUE_DIR
    offen, fertig = [], []
    if q.is_dir():
        for f in q.glob("auftrag-*.json"):
            try:
                a = json.loads(f.read_text())
            except Exception:  # noqa: BLE001
                continue
            if a.get("aktion") in ("veroeffentlichen", "zurueck", "sicherung"):
                offen.append({"aktion": a["aktion"], "art": a.get("art"), "name": a.get("name")})
        for f in sorted(q.glob("ergebnis-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]:
            try:
                e = json.loads(f.read_text())
                if e.get("aktion") == "kundenauszug":
                    continue
                fertig.append(e)
            except Exception:  # noqa: BLE001
                continue
    return {"offen": offen, "ergebnisse": fertig}
