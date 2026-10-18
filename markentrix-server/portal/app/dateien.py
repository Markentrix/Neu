"""Dateien in der Datenbank (Anhänge zu Nachrichten, Freigaben, Dokumentenablage). Max. 8 MB je Datei; Auslieferung immer als Download."""
import os
import re

from fastapi import HTTPException, UploadFile
from fastapi.responses import Response

MAX = 8 * 1024 * 1024
TYPEN = {
    "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "txt": "text/plain", "csv": "text/csv", "zip": "application/zip",
}
KATEGORIEN = ("vertrag", "briefing", "logo_material", "rechnung_beleg", "sonstiges")
KATEGORIE_NAMEN = {"vertrag": "Vertrag", "briefing": "Briefing", "logo_material": "Logo und Material", "rechnung_beleg": "Beleg", "sonstiges": "Sonstiges"}


def sicherer_name(name: str) -> str:
    name = os.path.basename(name or "datei").replace("\\", "/").split("/")[-1]
    return re.sub(r"[^A-Za-z0-9._ äöüÄÖÜß-]", "_", name)[:120] or "datei"


def lesen(upload: UploadFile) -> tuple[str, str, bytes]:
    """Gibt (Name, MIME-Typ, Inhalt) zurück oder wirft 400/413. Der Typ wird aus Endung UND Dateianfang bestimmt."""
    name = sicherer_name(upload.filename or "")
    endung = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if endung not in TYPEN:
        raise HTTPException(400, "Dieser Dateityp ist nicht erlaubt. Erlaubt: PDF, Bilder (PNG, JPG, WEBP), Word, Excel, PowerPoint, TXT, CSV, ZIP.")
    daten = upload.file.read(MAX + 1)
    if len(daten) > MAX:
        raise HTTPException(413, "Die Datei ist größer als 8 MB.")
    if not daten:
        raise HTTPException(400, "Die Datei ist leer.")
    kopf = daten[:12]
    pruef = {"pdf": kopf.startswith(b"%PDF"), "png": kopf.startswith(b"\x89PNG"), "jpg": kopf.startswith(b"\xff\xd8"), "jpeg": kopf.startswith(b"\xff\xd8"),
             "webp": kopf[:4] == b"RIFF" and kopf[8:12] == b"WEBP", "docx": kopf.startswith(b"PK"), "xlsx": kopf.startswith(b"PK"), "pptx": kopf.startswith(b"PK"), "zip": kopf.startswith(b"PK")}
    if endung in pruef and not pruef[endung]:
        raise HTTPException(400, "Der Inhalt passt nicht zur Dateiendung.")
    return name, TYPEN[endung], daten


def antwort(name: str, mime: str, daten: bytes) -> Response:
    sicher = re.sub(r'[^A-Za-z0-9._-]', "_", name)
    return Response(bytes(daten), media_type=mime, headers={"Content-Disposition": f'attachment; filename="{sicher}"', "X-Content-Type-Options": "nosniff"})
