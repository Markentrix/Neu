"""Website-Upload für Admins: ZIP hochladen, prüfen, bereitstellen. Das Portal hat keine Root-Rechte: Es entpackt nur geprüft in einen
Zwischenordner und legt einen Auftrag ab, den der Server-Dienst (bin/worker.py, jede Minute) ausführt (Caddy einrichten, Ordner tauschen)."""
import json
import re
import secrets
import shutil
import stat
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from . import config
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


def entpacken(zip_pfad: Path, ziel: Path) -> tuple:
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


def skript_einfuegen(ordner: Path, site_id: str, basis: str) -> int:
    """Fügt das Skript der Website-Dienste vor </body> jeder HTML-Seite ein (einmal, ohne Doppelung)."""
    tag = f'<script src="{basis}/static/js/site.js" data-site="{site_id}" defer></script>\n'
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


@router.post("/upload")
def hochladen(datei: UploadFile = File(...), art: str = Form("live"), name: str = Form(...), kunden_id: str = Form(""), dienste_skript: str = Form("0"),
              user: dict = Depends(require_admin)):
    rate_limit("webupload:" + str(user["id"]), 60, 600)
    name = _ordner_name(art, name.strip().lower())
    if not (datei.filename or "").lower().endswith(".zip"):
        raise HTTPException(400, "Bitte eine ZIP-Datei wählen.")
    if not config.SITES_LIVE.is_dir():
        raise HTTPException(500, "Der Website-Ordner ist im Portal nicht verfügbar.")
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
    uid = secrets.token_hex(8)
    stage = config.SITES_LIVE / f".upload-{uid}"
    try:
        stage.mkdir(mode=0o755)
        zip_pfad = stage / "_upload.zip"
        gross = 0
        with open(zip_pfad, "wb") as z:
            while True:
                block = datei.file.read(1 << 20)
                if not block:
                    break
                gross += len(block)
                if gross > MAX_ZIP:
                    raise HTTPException(400, "Die ZIP ist zu groß (über 120 MB). Bitte Bilder und Videos verkleinern.")
                z.write(block)
        inhalt = stage / "inhalt"
        n, verwendet = entpacken(zip_pfad, inhalt)
        zip_pfad.unlink()
        eingefuegt = 0
        with tx("admin") as cur:
            if kid and dienste_skript == "1":
                eingefuegt = skript_einfuegen(inhalt, sd.zeile(cur, kid)["site_id"], config.BASE_URL)
            if art == "live":
                cur.execute("""INSERT INTO websites (kunden_id, domain, art, status, letzte_veroeffentlichung) VALUES (%s,%s,'live','live',now())
                               ON CONFLICT (domain) DO UPDATE SET status='live', letzte_veroeffentlichung=now()""", (kid, name))
            audit(cur, user, "website_hochgeladen", kid, {"art": art, "name": name, "dateien": n, "ordner": verwendet})
        # Der Server-Dienst erwartet den Inhalt direkt im Zwischenordner
        for p in list(inhalt.iterdir()):
            shutil.move(str(p), str(stage / p.name))
        inhalt.rmdir()
        auftrag({"aktion": "veroeffentlichen", "art": art, "name": name, "upload": uid, "kunde": (nr + " " + firma)[:60].strip()})
    except HTTPException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    except OSError:
        shutil.rmtree(stage, ignore_errors=True)
        raise HTTPException(500, "Die Dateien konnten nicht abgelegt werden (Speicherplatz oder Rechte).")
    return {"ok": True, "id": uid, "dateien": n, "ordner": verwendet, "skript_in_seiten": eingefuegt,
            "hinweis": "Hochgeladen und geprüft. Die Website wird innerhalb einer Minute veröffentlicht, unten erscheint das Ergebnis."}


@router.post("/zurueck")
def zurueck(daten: dict, user: dict = Depends(require_admin)):
    art, name = str(daten.get("art", "")), str(daten.get("name", ""))
    _ordner_name(art, name)
    uid = secrets.token_hex(8)
    auftrag({"aktion": "zurueck", "art": art, "name": name, "upload": uid})
    with tx("admin") as cur:
        audit(cur, user, "website_zurueck", None, {"art": art, "name": name})
    return {"ok": True, "hinweis": "Die vorige Version wird innerhalb einer Minute wiederhergestellt."}


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
            if a.get("aktion") in ("veroeffentlichen", "zurueck"):
                offen.append({"aktion": a["aktion"], "art": a.get("art"), "name": a.get("name")})
        for f in sorted(q.glob("ergebnis-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]:
            try:
                fertig.append(json.loads(f.read_text()))
            except Exception:  # noqa: BLE001
                continue
    return {"offen": offen, "ergebnisse": fertig}
