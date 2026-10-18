"""Wochenangebote: Datei prüfen, ablegen und auf der Kunden-Website veröffentlichen.
Die Website bekommt unter /angebote/ immer das aktuelle Angebot (aktuell.pdf|jpg|png, aktuell.json, index.html)."""
import html
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from . import config

DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$")
TYPEN = {"pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png"}


def erkenne_typ(kopf: bytes, dateiname: str) -> str:
    """Typ nach Dateiinhalt (nicht nach Endung oder Angabe des Browsers)."""
    if kopf.startswith(b"%PDF-"):
        return "pdf"
    if kopf.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if kopf.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    raise HTTPException(400, "Nur PDF, JPG oder PNG sind erlaubt.")


def datei_speichern(upload: UploadFile, kunden_id) -> tuple[str, str, int, Path]:
    kopf = upload.file.read(16)
    typ = erkenne_typ(kopf, upload.filename or "")
    ziel_dir = config.UPLOAD_DIR / str(kunden_id)
    ziel_dir.mkdir(parents=True, exist_ok=True)
    ziel = ziel_dir / f"{uuid.uuid4().hex}.{typ}"
    groesse = len(kopf)
    with open(ziel, "wb") as f:
        f.write(kopf)
        while True:
            block = upload.file.read(1024 * 1024)
            if not block:
                break
            groesse += len(block)
            if groesse > config.MAX_UPLOAD_BYTES:
                f.close()
                ziel.unlink(missing_ok=True)
                raise HTTPException(413, "Die Datei ist größer als 10 MB.")
            f.write(block)
    return typ, TYPEN[typ], groesse, ziel


def sicherer_name(name: str) -> str:
    name = os.path.basename(name or "datei")
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:120] or "datei"


def seite_html(typ: str, von, bis, stand: str) -> str:
    gueltig = ""
    if von or bis:
        gueltig = f"<p class=\"s\">Gültig {html.escape(str(von) if von else '')}{' bis ' + html.escape(str(bis)) if bis else ''}</p>"
    if typ == "pdf":
        inhalt = '<iframe src="aktuell.pdf" title="Aktuelle Angebote"></iframe><p><a href="aktuell.pdf">PDF öffnen</a></p>'
    else:
        inhalt = f'<img src="aktuell.{typ}" alt="Aktuelle Angebote">'
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aktuelle Angebote</title><style>body{{margin:0;font-family:system-ui,sans-serif;background:#f6f7fb;color:#111;text-align:center}}
main{{max-width:900px;margin:0 auto;padding:16px}}img{{max-width:100%;height:auto;border-radius:8px}}iframe{{width:100%;height:80vh;border:0;border-radius:8px;background:#fff}}.s{{color:#555}}</style></head>
<body><main><h1>Aktuelle Angebote</h1>{gueltig}{inhalt}<p class="s">Stand: {html.escape(stand)}</p></main></body></html>"""


def veroeffentlichen(domain: str, quelle: Path, typ: str, von, bis) -> None:
    """Legt das Angebot im Website-Ordner ab. Wirft eine Ausnahme mit lesbarem Text bei Problemen."""
    if not DOMAIN_RE.match(domain or ""):
        raise RuntimeError("Ungültige Domain der Website.")
    root = (config.SITES_LIVE / domain).resolve()
    if config.SITES_LIVE.resolve() not in root.parents:
        raise RuntimeError("Ungültiger Website-Ordner.")
    if not root.is_dir():
        raise RuntimeError(f"Website-Ordner fehlt. Bitte auf dem Server 'mkctl site-add {domain}' ausführen.")
    ziel = root / "angebote"
    try:
        ziel.mkdir(exist_ok=True)
        (ziel / "archiv").mkdir(exist_ok=True)
    except PermissionError:
        raise RuntimeError(f"Keine Schreibrechte im Website-Ordner. Bitte auf dem Server 'mkctl site-add {domain}' ausführen.")
    jetzt = datetime.now(timezone.utc)
    for alt in ziel.glob("aktuell.*"):
        if alt.suffix == ".json":
            continue
        shutil.move(str(alt), str(ziel / "archiv" / f"{jetzt:%Y%m%d-%H%M%S}{alt.suffix}"))
    tmp = tempfile.NamedTemporaryFile(dir=ziel, delete=False)
    tmp.close()
    shutil.copyfile(quelle, tmp.name)
    os.chmod(tmp.name, 0o644)
    os.replace(tmp.name, ziel / f"aktuell.{typ}")
    stand = f"{jetzt:%d.%m.%Y %H:%M} UTC"
    meta = {"datei": f"aktuell.{typ}", "typ": TYPEN[typ], "gueltig_von": str(von) if von else None,
            "gueltig_bis": str(bis) if bis else None, "aktualisiert": jetzt.isoformat()}
    for name, inhalt in (("aktuell.json", json.dumps(meta)), ("index.html", seite_html(typ, von, bis, stand))):
        t = ziel / (name + ".tmp")
        t.write_text(inhalt, encoding="utf-8")
        os.chmod(t, 0o644)
        os.replace(t, ziel / name)
