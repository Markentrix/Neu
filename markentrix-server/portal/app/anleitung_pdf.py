"""PDF-Anleitungen für Vertrieb, Kunden und Admin. Inhalt kommt aus app/hilfe/<rolle>.json (dieselbe Quelle wie die Hilfe-Suche),
neue Artikel erscheinen also automatisch auch in der PDF."""
import json
from pathlib import Path

from . import pdf
from .pdf import H1, H2, KLEIN, p

DIR = Path(__file__).parent / "hilfe"
ROLLEN = ("vertrieb", "kunde", "admin")


def laden(rolle: str) -> dict:
    return json.loads((DIR / f"{rolle}.json").read_text(encoding="utf8"))


def bauen(rolle: str, firma: dict) -> bytes:
    d = laden(rolle)
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
        block += [p(f"{n}) {s}") for n, s in enumerate(a["s"], 1)]
        if a.get("n"):
            block += [pdf.Spacer(1, 3), p("Gut zu wissen:", KLEIN)] + [p("• " + x, KLEIN) for x in a["n"]]
        inhalt.append(pdf.KeepTogether(block[:4]))
        inhalt += block[4:]
    inhalt.append(p("Einstellungsmöglichkeiten", H2))
    inhalt += [p(f"{t}: {x}") for t, x in d["einstellungen"]]
    inhalt += [p("Hilfe, wenn etwas nicht klappt", H2), p(d["hilfe"]), pdf.Spacer(1, 8),
               p("Diese Anleitung wird mit dem Portal erweitert. Die aktuelle Fassung gibt es im Portal zum Herunterladen. Dieser Text wurde mit KI-Unterstützung vorbereitet.", KLEIN)]
    return pdf.dokument(d["titel"], "Anleitung", inhalt, firma)
