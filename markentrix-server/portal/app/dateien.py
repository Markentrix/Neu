"""Dateien in der Datenbank (Anhänge zu Nachrichten, Freigaben, Dokumentenablage). Max. 8 MB je Datei; Auslieferung immer als Download."""
import io
import os
import re
import shutil
import subprocess
import zipfile

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
    inhalt_pruefen(name, daten)
    return name, TYPEN[endung], daten


QUOTA = 500 * 1024 * 1024            # Speicher je Kunde für eigene Uploads
GEFAEHRLICH = (".exe", ".dll", ".bat", ".cmd", ".com", ".scr", ".js", ".jse", ".vbs", ".vbe", ".ps1", ".msi", ".jar", ".lnk", ".sh", ".apk")


def inhalt_pruefen(name: str, daten: bytes) -> None:
    """Einfache Schutzprüfung ohne Virenscanner: Zip-Bomben, ausführbare Dateien in Archiven, Office-Makros, PDF-Startaktionen.
    Ist ein Virenscanner (clamdscan) installiert, wird er zusätzlich benutzt."""
    endung = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if daten[:2] == b"PK":
        try:
            z = zipfile.ZipFile(io.BytesIO(daten))
            infos = z.infolist()
        except zipfile.BadZipFile:
            raise HTTPException(400, "Das Archiv ist beschädigt.")
        if len(infos) > 5000 or sum(i.file_size for i in infos) > 300 * 1024 * 1024:
            raise HTTPException(400, "Das Archiv ist zu groß oder enthält zu viele Dateien.")
        for i in infos:
            n = i.filename.lower()
            if n.startswith("/") or ".." in n.split("/"):
                raise HTTPException(400, "Das Archiv enthält ungültige Pfade.")
            if "vbaproject.bin" in n:
                raise HTTPException(400, "Dateien mit Makros sind nicht erlaubt.")
            if endung == "zip" and n.endswith(GEFAEHRLICH):
                raise HTTPException(400, "Das Archiv enthält ausführbare Dateien und wurde abgelehnt.")
    elif endung == "pdf" and (b"/Launch" in daten):
        raise HTTPException(400, "Dieses PDF enthält eine Startaktion und wurde abgelehnt.")
    scanner = shutil.which("clamdscan")
    if scanner:
        try:
            r = subprocess.run([scanner, "--no-summary", "--stdin"], input=daten, capture_output=True, timeout=30)
            if r.returncode == 1:
                raise HTTPException(400, "Die Datei wurde vom Virenscanner abgelehnt.")
        except (subprocess.SubprocessError, OSError):
            pass


def quota_pruefen(cur, kunden_id, neu: int) -> None:
    """Begrenzt den Speicher je Kunde (nur für Uploads durch den Kunden)."""
    cur.execute("SELECT COALESCE(sum(groesse),0) AS s FROM dateien WHERE kunden_id=%s", (kunden_id,))
    if int(cur.fetchone()["s"]) + neu > QUOTA:
        raise HTTPException(413, "Der Speicher für Ihre Dateien ist voll (500 MB). Bitte löschen Sie alte Dateien oder fragen Sie uns.")


def antwort(name: str, mime: str, daten: bytes) -> Response:
    sicher = re.sub(r'[^A-Za-z0-9._-]', "_", name)
    return Response(bytes(daten), media_type=mime, headers={"Content-Disposition": f'attachment; filename="{sicher}"', "X-Content-Type-Options": "nosniff"})
