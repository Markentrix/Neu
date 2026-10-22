"""Vertragsvorlagen (ausfüllbare PDF-Formulare) mit Daten vorausfüllen: Referenzvertrag (Kunde) und Handelsvertretervertrag (Vertriebspartner).
Der Wortlaut der Verträge bleibt unverändert, es werden nur die Formularfelder gefüllt. Haken setzt immer der Vertragspartner selbst (Referenz) bzw. der Partner (Anlage 3)."""
import io
from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

DIR = Path(__file__).parent / "vorlagen"
VORLAGEN = {"referenz": "referenzvertrag.pdf", "handelsvertreter": "handelsvertretervertrag.pdf"}
DATEINAME = {"referenz": "Referenzvertrag-Markentrix", "handelsvertreter": "Handelsvertretervertrag-Markentrix"}


def felder(art: str) -> dict:
    return PdfReader(DIR / VORLAGEN[art]).get_fields() or {}


def ausfuellen(art: str, werte: dict, haken: list | tuple = ()) -> bytes:
    """Füllt die Formularfelder. werte: Feldname -> Text; haken: Feldnamen von Kontrollkästchen, die angekreuzt werden. Unbekannte Felder sind ein Fehler."""
    r = PdfReader(DIR / VORLAGEN[art])
    alle = r.get_fields() or {}
    unbekannt = [k for k in list(werte) + list(haken) if k not in alle]
    if unbekannt:
        raise ValueError("Unbekannte Formularfelder: " + ", ".join(unbekannt))
    w = PdfWriter(clone_from=r)
    setzen = {k: (v or "") for k, v in werte.items() if v not in (None, "")}
    for k in haken:
        zustaende = [s for s in (alle[k].get("/_States_") or []) if s != "/Off"]
        setzen[k] = NameObject(zustaende[0] if zustaende else "/Yes")
    for seite in w.pages:
        if "/Annots" not in seite:
            continue
        w.update_page_form_field_values(seite, setzen, auto_regenerate=False)
    w.set_need_appearances_writer(True)
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def datum_de(d: date | None = None) -> str:
    d = d or date.today()
    return d.strftime("%d.%m.%Y")


def feldwerte(art: str, pdf: bytes) -> dict:
    """Gelesene Werte eines ausgefüllten Formulars (für Tests und Kontrolle)."""
    return {k: v.get("/V") for k, v in (PdfReader(io.BytesIO(pdf)).get_fields() or {}).items()}
