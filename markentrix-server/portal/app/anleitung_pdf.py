"""PDF-Anleitungen für Vertrieb, Kunden und Admin. Inhalt kommt aus app/hilfe/<rolle>.json (dieselbe Quelle wie die Hilfe-Suche),
neue Artikel erscheinen also automatisch auch in der PDF."""
import json
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image

from . import pdf
from .pdf import H1, H2, KLEIN, p

DIR = Path(__file__).parent / "hilfe"
ROLLEN = ("vertrieb", "kunde", "admin")


BILDER = Path(__file__).parent.parent / "static" / "hilfe"


def laden(rolle: str) -> dict:
    """Artikel einer Rolle. Gibt es zum Menüziel eines Artikels (Feld „l“, z. B. „#leads“) ein Bild in static/hilfe/<rolle>/, steht es als „bild“ dabei."""
    d = json.loads((DIR / f"{rolle}.json").read_text(encoding="utf8"))
    for a in d["artikel"]:
        seite = (a.get("l") or "").lstrip("#")
        if seite and "/" not in seite and (BILDER / rolle / f"{seite}.png").is_file():
            a["bild"] = f"/static/hilfe/{rolle}/{seite}.png"
    return d


def _pdf_text(x):
    """Die PDF-Schrift hat keine Pfeile und Emojis: Pfeil wird „>“, Emojis entfallen."""
    if isinstance(x, str):
        return "".join(c for c in x.replace("→", ">").replace("✔", "").replace("✕", "x") if ord(c) < 0x2600 or c in "„“”–—•…€").replace("  ", " ")
    if isinstance(x, list):
        return [_pdf_text(i) for i in x]
    if isinstance(x, dict):
        return {k: _pdf_text(v) if k != "bild" else v for k, v in x.items()}
    return x


def bauen(rolle: str, firma: dict) -> bytes:
    d = _pdf_text(laden(rolle))
    gezeigt: set = set()
    inhalt = [p(d["titel"], H1), p(d["untertitel"], KLEIN), pdf.Spacer(1, 8)]
    for t in d["intro"]:
        inhalt += [p(t), pdf.Spacer(1, 4)]
    inhalt.append(p("So fängst du an", H2))
    inhalt += [p(f"{i}. {s}") for i, s in enumerate(d["start"], 1)]
    inhalt.append(p("Inhalt", H2))
    inhalt += [p(f"{i}. {a['t']}") for i, a in enumerate(d["artikel"], 1)]
    inhalt.append(pdf.PageBreak())
    for i, a in enumerate(d["artikel"], 1):
        block = [p(f"{i}. {a['t']}", H2), p("Wo: " + a["wo"], KLEIN), pdf.Spacer(1, 3)]
        if a.get("bild") and a["bild"] not in gezeigt:      # jedes Bild nur einmal, beim ersten passenden Artikel
            gezeigt.add(a["bild"])
            datei = BILDER / rolle / Path(a["bild"]).name
            breit = 150 if rolle == "admin" else 62
            bw, bh = ImageReader(str(datei)).getSize()
            block += [Image(str(datei), width=breit * pdf.mm, height=breit * pdf.mm * bh / bw), p("So sieht die Seite aus (Beispieldaten).", KLEIN), pdf.Spacer(1, 4)]
        block += [p(f"{n}) {s}") for n, s in enumerate(a["s"], 1)]
        if a.get("n"):
            block += [pdf.Spacer(1, 3), p("Gut zu wissen:", KLEIN)] + [p("• " + x, KLEIN) for x in a["n"]]
        inhalt.append(pdf.KeepTogether(block[:4]))
        inhalt += block[4:]
    if d.get("faq"):
        inhalt.append(p("Häufige Fragen", H2))
        for frage, antwort in d["faq"]:
            inhalt += [pdf.KeepTogether([p("Frage: " + frage), p("Antwort: " + antwort, KLEIN)]), pdf.Spacer(1, 4)]
    inhalt.append(p("Einstellungsmöglichkeiten", H2))
    inhalt += [p(f"{t}: {x}") for t, x in d["einstellungen"]]
    inhalt += [p("Hilfe, wenn etwas nicht klappt", H2), p(d["hilfe"]), pdf.Spacer(1, 8),
               p("Diese Anleitung wird mit dem Portal erweitert. Die aktuelle Fassung gibt es im Portal zum Herunterladen. Dieser Text wurde mit KI-Unterstützung vorbereitet.", KLEIN)]
    return pdf.dokument(d["titel"], "Anleitung", inhalt, firma)
