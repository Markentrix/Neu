"""Wochenangebote: Datei prüfen, ablegen und auf der Kunden-Website veröffentlichen.
Die Website bekommt unter /angebote/ immer das aktuelle Angebot (aktuell.pdf|jpg|png, aktuell.json, index.html)."""
import html
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
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


SPRACHEN = {"de": "Deutsch", "tr": "Türkçe", "en": "English", "ar": "العربية"}
UI = {
    "de": {"titel": "Aktuelle Angebote", "geschlossen": "Heute geschlossen", "events": "Veranstaltungen", "hinweise": "Hinweise", "gueltig": "Gültig", "stand": "Stand", "pdf": "PDF öffnen"},
    "tr": {"titel": "Güncel Teklifler", "geschlossen": "Bugün kapalıyız", "events": "Etkinlikler", "hinweise": "Duyurular", "gueltig": "Geçerlilik", "stand": "Güncelleme", "pdf": "PDF dosyasını aç"},
    "en": {"titel": "Current offers", "geschlossen": "Closed today", "events": "Events", "hinweise": "Notices", "gueltig": "Valid", "stand": "Updated", "pdf": "Open PDF"},
    "ar": {"titel": "العروض الحالية", "geschlossen": "مغلق اليوم", "events": "الفعاليات", "hinweise": "إعلانات", "gueltig": "صالح", "stand": "آخر تحديث", "pdf": "فتح ملف PDF"},
}


def sprachen_pruefen(sprachen) -> list[str]:
    liste = [s for s in (sprachen or []) if s in SPRACHEN]
    return list(dict.fromkeys(["de"] + liste)) if liste else ["de"]


def _l(daten: dict, sprache: str) -> str:
    """Text in der Sprache, sonst Deutsch, sonst irgendein Eintrag."""
    daten = daten or {}
    return (daten.get(sprache) or daten.get("de") or next((v for v in daten.values() if v), "") or "").strip()


def _datum_de(d) -> str:
    try:
        return datetime.fromisoformat(str(d)).strftime("%d.%m.%Y")
    except ValueError:
        return str(d)


def _mehrsprachig(sprachen, fn) -> str:
    out = []
    for sp in sprachen:
        t = fn(sp)
        if t:
            out.append(f'<span class="l" lang="{sp}"{" dir=\"rtl\"" if sp == "ar" else ""}>{t}</span>')
    return "".join(out)


def seite_html(typ, von, bis, stand: str, sprachen=("de",), inhalte=()) -> str:
    sprachen = sprachen_pruefen(sprachen)
    e = html.escape
    heute = datetime.now(timezone.utc).date()
    sichtbar = [i for i in inhalte if i.get("aktiv", True) and not (i.get("gueltig_bis") and str(i["gueltig_bis"]) < str(heute - timedelta(days=1)))]

    def zeitraum(v, b, sp):
        if not (v or b):
            return ""
        return f"{e(UI[sp]['gueltig'])}: {e(_datum_de(v)) if v else ''}{' – ' + e(_datum_de(b)) if b else ''}"

    def eintrag(i):
        attr = ""
        v, b = i.get("gueltig_von"), i.get("gueltig_bis")
        if i["art"] == "geschlossen":
            b = b or v
        if v:
            attr += f' data-von="{e(str(v))}"'
        if b:
            attr += f' data-bis="{e(str(b))}"'
        titel = _mehrsprachig(sprachen, lambda sp: f"<h3>{e(_l(i.get('titel'), sp))}</h3>" if _l(i.get("titel"), sp) else "")
        text = _mehrsprachig(sprachen, lambda sp: f"<p>{e(_l(i.get('text'), sp))}</p>" if _l(i.get("text"), sp) else "")
        preis = f'<p class="preis">{e(i["preis"])}</p>' if i.get("preis") else ""
        zr = _mehrsprachig(sprachen, lambda sp: f'<p class="s">{zeitraum(v, b, sp)}</p>') if (v or b) and i["art"] != "geschlossen" else ""
        return f'<article class="k {i["art"]}"{attr}>{titel}{text}{preis}{zr}</article>'

    def block(art, schluessel):
        eintraege = [eintrag(i) for i in sichtbar if i["art"] == art]
        if not eintraege:
            return ""
        kopf = _mehrsprachig(sprachen, lambda sp: f"<h2>{e(UI[sp][schluessel])}</h2>")
        return f'<section class="{art}">{kopf}{"".join(eintraege)}</section>'

    banner = ""
    for i in [x for x in sichtbar if x["art"] == "geschlossen"]:
        v = i.get("gueltig_von"); b = i.get("gueltig_bis") or v
        attr = (f' data-von="{e(str(v))}"' if v else "") + (f' data-bis="{e(str(b))}"' if b else "")
        t = _mehrsprachig(sprachen, lambda sp: e(_l(i.get("titel"), sp) or UI[sp]["geschlossen"]))
        x = _mehrsprachig(sprachen, lambda sp: f'<small>{e(_l(i.get("text"), sp))}</small>' if _l(i.get("text"), sp) else "")
        banner += f'<div class="zu"{attr}><strong>{t}</strong> {x}</div>'
    if typ == "pdf":
        datei = '<iframe src="aktuell.pdf" title="PDF"></iframe><p><a href="aktuell.pdf">' + _mehrsprachig(sprachen, lambda sp: e(UI[sp]["pdf"])) + "</a></p>"
    elif typ:
        datei = f'<img src="aktuell.{typ}" alt="">'
    else:
        datei = ""
    gv = _mehrsprachig(sprachen, lambda sp: f'<p class="s">{zeitraum(von, bis, sp)}</p>') if (von or bis) else ""
    css_l = "".join(f'html[data-l="{sp}"] .l[lang="{sp}"]{{display:revert}}' for sp in sprachen)
    knoepfe = "".join(f'<button type="button" data-sp="{sp}">{e(SPRACHEN[sp])}</button>' for sp in sprachen) if len(sprachen) > 1 else ""
    titel = _mehrsprachig(sprachen, lambda sp: f"<h1>{e(UI[sp]['titel'])}</h1>")
    stand_html = _mehrsprachig(sprachen, lambda sp: f'<p class="s">{e(UI[sp]["stand"])}: {e(stand)}</p>')
    return f"""<!doctype html><html lang="{sprachen[0]}" data-l="{sprachen[0]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(UI[sprachen[0]]['titel'])}</title><style>body{{margin:0;font-family:system-ui,sans-serif;background:#f6f7fb;color:#111;text-align:center}}
main{{max-width:900px;margin:0 auto;padding:16px}}img{{max-width:100%;height:auto;border-radius:8px}}iframe{{width:100%;height:80vh;border:0;border-radius:8px;background:#fff}}.s{{color:#555}}
.l{{display:none}}{css_l}.lang{{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin:8px 0}}.lang button{{border:1px solid #ccd;background:#fff;border-radius:99px;padding:6px 14px;cursor:pointer;font-size:15px}}
.zu{{background:#fee2e2;color:#7f1d1d;border:1px solid #fecaca;border-radius:10px;padding:12px;margin:12px 0;font-size:18px}}
.k{{background:#fff;border:1px solid #e3e6f0;border-radius:12px;padding:12px 16px;margin:10px 0;text-align:start}}.k h3{{margin:0 0 6px}}.k p{{margin:4px 0;white-space:pre-line}}.preis{{font-weight:700;font-size:20px;color:#166534}}
section h2{{text-align:start;margin:22px 0 4px}}</style></head>
<body><main><div class="lang">{knoepfe}</div>{titel}{banner}{gv}{datei}{block("angebot", "titel")}{block("event", "events")}{block("hinweis", "hinweise")}{stand_html}</main>
<script>(function(){{var d=document.documentElement,s={json.dumps(sprachen)},n=(navigator.language||"de").slice(0,2),l=s.indexOf(n)>=0?n:s[0];
function set(x){{d.setAttribute("data-l",x);d.lang=x;d.dir=x==="ar"?"rtl":"ltr"}}set(l);
document.querySelectorAll(".lang button").forEach(function(b){{b.onclick=function(){{set(b.getAttribute("data-sp"))}}}});
var t=new Date(),h=t.getFullYear()+"-"+("0"+(t.getMonth()+1)).slice(-2)+"-"+("0"+t.getDate()).slice(-2);
document.querySelectorAll("[data-von],[data-bis]").forEach(function(e){{var v=e.getAttribute("data-von"),b=e.getAttribute("data-bis");if((v&&h<v)||(b&&h>b))e.style.display="none"}})}})();</script></body></html>"""


def _meta_lesen(ziel: Path) -> dict:
    try:
        return json.loads((ziel / "aktuell.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _ordner(domain: str) -> Path:
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
    return ziel


def _seite_schreiben(ziel: Path, typ, von, bis, sprachen, inhalte) -> None:
    jetzt = datetime.now(timezone.utc)
    stand = f"{jetzt:%d.%m.%Y %H:%M} UTC"
    meta = {"datei": f"aktuell.{typ}" if typ else None, "typ": TYPEN.get(typ) if typ else None, "gueltig_von": str(von) if von else None,
            "gueltig_bis": str(bis) if bis else None, "aktualisiert": jetzt.isoformat(), "sprachen": sprachen_pruefen(sprachen),
            "inhalte": [{k: (str(v) if k.startswith("gueltig") and v else v) for k, v in i.items() if k in ("art", "titel", "text", "preis", "gueltig_von", "gueltig_bis")} for i in inhalte if i.get("aktiv", True)]}
    for name, inhalt in (("aktuell.json", json.dumps(meta, ensure_ascii=False)), ("index.html", seite_html(typ, von, bis, stand, sprachen, inhalte))):
        t = ziel / (name + ".tmp")
        t.write_text(inhalt, encoding="utf-8")
        os.chmod(t, 0o644)
        os.replace(t, ziel / name)


def veroeffentlichen(domain: str, quelle: Path, typ: str, von, bis, sprachen=("de",), inhalte=()) -> None:
    """Legt das Angebot im Website-Ordner ab. Wirft eine Ausnahme mit lesbarem Text bei Problemen."""
    ziel = _ordner(domain)
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
    _seite_schreiben(ziel, typ, von, bis, sprachen, inhalte)


def inhalte_aktualisieren(domain: str, sprachen, inhalte) -> None:
    """Baut die Angebotsseite neu (Texte, Events, Hinweise), die hochgeladene Datei bleibt wie sie ist."""
    ziel = _ordner(domain)
    m = _meta_lesen(ziel)
    typ = (m.get("datei") or "").rsplit(".", 1)[-1] if m.get("datei") else None
    if typ not in TYPEN or not (ziel / f"aktuell.{typ}").exists():
        typ = None
    _seite_schreiben(ziel, typ, m.get("gueltig_von"), m.get("gueltig_bis"), sprachen, inhalte)
