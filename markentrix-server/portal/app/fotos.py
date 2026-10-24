"""Fotos zu Anfragen und Terminen: prüfen, von Metadaten (Standort, Kamera, Zeit) befreien, speichern, verknüpfen, nach Frist löschen.

Der Besucher lädt ein Foto zuerst einzeln hoch (bekommt eine Kennung) und schickt die Kennungen mit der Anfrage mit.
Nicht verknüpfte Fotos werden nach 24 Stunden gelöscht, verknüpfte nach der Frist des Betriebs (Standard 90 Tage)."""
import secrets
import struct

from fastapi import HTTPException

MAX_BYTES = 6 * 1024 * 1024         # je Foto (die Website verkleinert vorher auf ca. 0,3 bis 1 MB)
MAX_ANZAHL = 5                       # je Anfrage
MAX_PIXEL = 60_000_000
SPEICHER_JE_KUNDE = 200 * 1024 * 1024
MAIL_MAX = 8 * 1024 * 1024           # bis zu dieser Gesamtgröße hängen die Fotos an der Mail an
STANDARD_TAGE = 90
ENDUNG = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class FotoFehler(ValueError):
    pass


def _jpeg(b: bytes) -> bytes:
    if b[:3] != b"\xff\xd8\xff":
        raise FotoFehler("kein JPEG")
    aus, i, n, sof = [b"\xff\xd8"], 2, len(b), False
    while i + 4 <= n:
        if b[i] != 0xFF:
            raise FotoFehler("JPEG beschädigt")
        m = b[i + 1]
        if m == 0xFF:
            i += 1
            continue
        if m == 0xD9:
            break
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        ln = struct.unpack(">H", b[i + 2:i + 4])[0]
        if ln < 2 or i + 2 + ln > n:
            raise FotoFehler("JPEG beschädigt")
        seg = b[i:i + 2 + ln]
        if m in (0xC0, 0xC1, 0xC2):
            if ln < 8:
                raise FotoFehler("JPEG beschädigt")
            h, w = struct.unpack(">HH", seg[5:9])
            if not w or not h or w * h > MAX_PIXEL:
                raise FotoFehler("Bild zu groß")
            sof = True
        if m == 0xDA:                       # Bilddaten: ab hier unverändert bis zum Ende
            if not sof:
                raise FotoFehler("JPEG beschädigt")
            aus.append(b[i:])
            return b"".join(aus)
        if m == 0xE0 or m == 0xEE or not (0xE1 <= m <= 0xEF or m == 0xFE):   # E1..EF und Kommentare (Exif, XMP, GPS, Software) entfallen
            aus.append(seg)
        i += 2 + ln
    raise FotoFehler("JPEG unvollständig")


_PNG_BEHALTEN = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"sBIT"}


def _png(b: bytes) -> bytes:
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise FotoFehler("kein PNG")
    aus, i, n, erste, idat, ende = [b[:8]], 8, len(b), True, False, False
    while i + 12 <= n:
        ln = struct.unpack(">I", b[i:i + 4])[0]
        art = b[i + 4:i + 8]
        if i + 12 + ln > n:
            raise FotoFehler("PNG beschädigt")
        if erste:
            if art != b"IHDR" or ln != 13:
                raise FotoFehler("PNG beschädigt")
            w, h = struct.unpack(">II", b[i + 8:i + 16])
            if not w or not h or w * h > MAX_PIXEL:
                raise FotoFehler("Bild zu groß")
            erste = False
        if art in _PNG_BEHALTEN:
            aus.append(b[i:i + 12 + ln])
        idat = idat or art == b"IDAT"
        i += 12 + ln
        if art == b"IEND":
            ende = True
            break
    if erste or not idat or not ende:
        raise FotoFehler("PNG unvollständig")
    return b"".join(aus)


def _webp(b: bytes) -> bytes:
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP" or len(b) < 20:
        raise FotoFehler("kein WebP")
    if struct.unpack("<I", b[4:8])[0] + 8 > len(b):
        raise FotoFehler("WebP beschädigt")
    aus, i, n, bild = [], 12, min(len(b), struct.unpack("<I", b[4:8])[0] + 8), False
    while i + 8 <= n:
        art = b[i:i + 4]
        ln = struct.unpack("<I", b[i + 4:i + 8])[0]
        ende = i + 8 + ln + (ln & 1)
        if i + 8 + ln > n:
            raise FotoFehler("WebP beschädigt")
        if art in (b"ANIM", b"ANMF"):
            raise FotoFehler("Animierte Bilder sind nicht erlaubt")
        if art in (b"EXIF", b"XMP "):
            i = ende
            continue
        block = b[i:min(ende, n)]
        if art == b"VP8X":
            if ln < 10:
                raise FotoFehler("WebP beschädigt")
            w, h = (int.from_bytes(b[i + 12:i + 15], "little") + 1), (int.from_bytes(b[i + 15:i + 18], "little") + 1)
            if w * h > MAX_PIXEL:
                raise FotoFehler("Bild zu groß")
            block = block[:8] + bytes([block[8] & ~0x0E & 0xFF]) + block[9:]       # Kennzeichen für Animation, XMP, EXIF löschen
        bild = bild or art in (b"VP8 ", b"VP8L")
        aus.append(block + (b"\x00" if len(block) & 1 else b""))
        i = ende
    if not bild:
        raise FotoFehler("WebP unvollständig")
    inhalt = b"WEBP" + b"".join(aus)
    return b"RIFF" + struct.pack("<I", len(inhalt)) + inhalt


def pruefen(daten: bytes) -> tuple[str, bytes]:
    """Erkennt den Typ am Inhalt (nicht am Dateinamen oder Header des Besuchers) und entfernt Metadaten. Wirft FotoFehler."""
    if not daten or len(daten) > MAX_BYTES:
        raise FotoFehler("Das Foto ist zu groß (höchstens 6 MB).")
    if daten[:3] == b"\xff\xd8\xff":
        return "image/jpeg", _jpeg(daten)
    if daten[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", _png(daten)
    if daten[:4] == b"RIFF" and daten[8:12] == b"WEBP":
        return "image/webp", _webp(daten)
    raise FotoFehler("Bitte ein Foto als JPG, PNG oder WebP hochladen.")


def speichern(cur, kid, daten: bytes) -> str:
    """Prüft und speichert ein Foto, noch ohne Anfrage. Gibt die Kennung zurück. Wirft HTTPException."""
    try:
        typ, sauber = pruefen(daten)
    except FotoFehler as e:
        raise HTTPException(400, str(e))
    cur.execute("SELECT COALESCE(sum(groesse),0) AS s, count(*) FILTER (WHERE loeschen_am IS NULL) AS offen FROM website_fotos WHERE kunden_id=%s", (kid,))
    r = cur.fetchone()
    if int(r["s"]) + len(sauber) > SPEICHER_JE_KUNDE:
        raise HTTPException(413, "Fotos können gerade nicht hochgeladen werden. Bitte schreiben Sie uns ohne Foto.")
    if int(r["offen"]) >= 300:
        raise HTTPException(429, "Zu viele Uploads. Bitte versuchen Sie es später noch einmal.")
    token = secrets.token_urlsafe(18)
    cur.execute("INSERT INTO website_fotos (kunden_id, token, typ, groesse, daten) VALUES (%s,%s,%s,%s,%s)", (kid, token, typ, len(sauber), sauber))
    return token


def kennungen(wert) -> list[str]:
    """Kennungen aus dem Anfrage-Feld „fotos“ (Liste, kommagetrennter Text oder einzelner Wert)."""
    if isinstance(wert, str):
        wert = [x for x in wert.replace(";", ",").split(",")]
    if not isinstance(wert, list):
        return []
    aus = []
    for x in wert:
        x = str(x).strip()
        if 10 <= len(x) <= 64 and all(c.isalnum() or c in "-_" for c in x) and x not in aus:
            aus.append(x)
    return aus[:MAX_ANZAHL]


def verknuepfen(cur, kid, tokens: list[str], tage: int, anfrage_id=None, buchung_id=None) -> list[str]:
    """Hängt hochgeladene Fotos an eine Anfrage bzw. Buchung und setzt das Löschdatum. Gibt die Foto-IDs zurück (nur die, die zu diesem Betrieb gehören und frei sind)."""
    if not tokens:
        return []
    cur.execute("""UPDATE website_fotos SET anfrage_id=%s, buchung_id=%s, token=NULL, loeschen_am=now() + make_interval(days => %s)
                   WHERE kunden_id=%s AND token = ANY(%s) AND loeschen_am IS NULL RETURNING id""", (anfrage_id, buchung_id, tage, kid, tokens))
    return [str(r["id"]) for r in cur.fetchall()]


def fuer_mail(cur, kid, ids: list[str]) -> list[tuple[str, bytes, str]]:
    """Anhänge für die Mail an den Betrieb; leer, wenn alles zusammen größer als MAIL_MAX ist."""
    if not ids:
        return []
    cur.execute("SELECT id, typ, groesse, daten FROM website_fotos WHERE kunden_id=%s AND id = ANY(%s::uuid[]) ORDER BY erstellt_am", (kid, ids))
    zeilen = cur.fetchall()
    if sum(r["groesse"] for r in zeilen) > MAIL_MAX:
        return []
    return [(f"foto-{i}.{ENDUNG[r['typ']]}", bytes(r["daten"]), r["typ"]) for i, r in enumerate(zeilen, 1)]


def liste(cur, kid, anfrage_ids=(), buchung_ids=()) -> dict:
    """Fotos je Anfrage/Buchung für die Portalanzeige: {anfrage:{id:[{id,loeschen_am}]}, buchung:{…}}. Läuft mit Kundenrechten oder systemweit; Betrieb wird immer geprüft."""
    aus: dict = {"anfrage": {}, "buchung": {}}
    if not anfrage_ids and not buchung_ids:
        return aus
    cur.execute("""SELECT id, anfrage_id, buchung_id, loeschen_am FROM website_fotos
                   WHERE kunden_id=%s AND (anfrage_id = ANY(%s::uuid[]) OR buchung_id = ANY(%s::uuid[])) ORDER BY erstellt_am""",
                (kid, [str(x) for x in anfrage_ids], [str(x) for x in buchung_ids]))
    for r in cur.fetchall():
        e = {"id": str(r["id"]), "loeschen_am": r["loeschen_am"]}
        if r["anfrage_id"]:
            aus["anfrage"].setdefault(str(r["anfrage_id"]), []).append(e)
        if r["buchung_id"]:
            aus["buchung"].setdefault(str(r["buchung_id"]), []).append(e)
    return aus


def aufraeumen(cur) -> tuple[int, int]:
    """Löscht abgelaufene Fotos und nie verknüpfte Uploads (älter als 24 Stunden). Gibt (abgelaufen, verwaist) zurück."""
    cur.execute("DELETE FROM website_fotos WHERE loeschen_am IS NOT NULL AND loeschen_am < now()")
    a = cur.rowcount
    cur.execute("DELETE FROM website_fotos WHERE loeschen_am IS NULL AND erstellt_am < now() - interval '24 hours'")
    return a, cur.rowcount
