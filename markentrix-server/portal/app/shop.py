"""Online-Shop: reine Logik ohne Datenbank (Schlüssel, Preise, Bildmaße, Mail-Texte). Die Routen stehen in routes_shop.py."""
import re
import struct
import unicodedata

STATI = ("eingegangen", "bestaetigt", "bezahlt", "im_druck", "versendet", "abholbereit", "abgeholt", "storniert")
STATUS_TEXT = {"eingegangen": "Eingegangen", "bestaetigt": "Bestätigt", "bezahlt": "Bezahlt", "im_druck": "In Produktion", "versendet": "Versendet",
               "abholbereit": "Abholbereit", "abgeholt": "Abgeholt", "storniert": "Storniert"}
SCHLUESSEL = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
PLZ = re.compile(r"^[0-9A-Za-z \-]{3,10}$")
BILD_MAX_BYTES = 600 * 1024
BILD_MAX_JE_ARTIKEL = 8
BILD_SPEICHER_JE_KUNDE = 100 * 1024 * 1024


def schluessel(text: str) -> str:
    """Aus einem Namen wird ein Schlüssel für die Website: „Kleiner Kürbis“ → „kleiner-kuerbis“."""
    t = (text or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def cent(euro) -> int | None:
    """Euro (Zahl oder Text wie „2,79“) → Cent. None bei Unsinn."""
    try:
        s = str(euro).strip().replace("€", "").replace(" ", "")
        s = s.replace(".", "").replace(",", ".") if "," in s else s
        v = round(float(s) * 100)
    except (TypeError, ValueError):
        return None
    return v if 0 <= v <= 10_000_000 else None


def euro(c: int) -> float:
    return round(c / 100, 2)


def eur(c: int) -> str:
    return f"{c / 100:.2f}".replace(".", ",") + " €"


def webp_masse(b: bytes) -> tuple[int, int] | None:
    """Breite und Höhe eines (bereits geprüften) WebP-Bildes aus dem Kopf gelesen."""
    if len(b) < 30 or b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return None
    art = b[12:16]
    try:
        if art == b"VP8 ":
            if b[23:26] != b"\x9d\x01\x2a":
                return None
            return struct.unpack("<H", b[26:28])[0] & 0x3FFF, struct.unpack("<H", b[28:30])[0] & 0x3FFF
        if art == b"VP8L":
            if b[20] != 0x2F:
                return None
            bits = int.from_bytes(b[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if art == b"VP8X":
            return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    except (struct.error, IndexError):
        return None
    return None


def versandkosten(e: dict, zwischensumme_cent: int, lieferart: str) -> int:
    if lieferart == "abholung":
        return 0
    frei = e.get("versandfrei_ab_cent")
    if frei is not None and zwischensumme_cent >= frei:
        return 0
    return int(e["versand_pauschale_cent"])


def positionen_text(positionen: list[dict]) -> str:
    zeilen = []
    for p in positionen:
        z = f"{p['menge']} × {p['name']}"
        if p.get("farbe_name"):
            z += f" ({p['farbe_name']})"
        if p.get("wunschtext"):
            z += f", Wunschtext: „{p['wunschtext']}“"
        zeilen.append(z + f", {eur(p['einzelpreis_cent'] * p['menge'])}")
    return "\n".join(zeilen)


def adresse_text(a: dict | None) -> str:
    if not a:
        return ""
    return f"{a.get('strasse', '')}\n{a.get('plz', '')} {a.get('ort', '')}" + (f"\n{a['land']}" if a.get("land") and a["land"] != "DE" else "")


def bestell_uebersicht(b: dict, positionen: list[dict]) -> str:
    t = positionen_text(positionen) + f"\n\nZwischensumme: {eur(b['zwischensumme_cent'])}\nVersand: {eur(b['versand_cent'])}\nGesamt: {eur(b['summe_cent'])}"
    if b.get("gutschein_cent"):
        t += f"\nGutschein {b.get('gutschein_code') or ''}: −{eur(b['gutschein_cent'])}\nZu zahlen: {eur(b['summe_cent'] - b['gutschein_cent'])}"
    t += "\n\n" + ("Abholung" if b["lieferart"] == "abholung" else "Lieferadresse:\n" + adresse_text(b.get("adresse")))
    if b.get("anmerkung"):
        t += f"\n\nAnmerkung: {b['anmerkung']}"
    return t


def zahlhinweis(b: dict, paypal_url: str) -> str:
    if b["summe_cent"] - b.get("gutschein_cent", 0) <= 0:
        return "Ihre Bestellung ist vollständig mit dem Gutschein bezahlt."
    if b["zahlungsart"] == "abholung":
        return "Die Zahlung erfolgt bei der Abholung."
    if paypal_url:
        return f"Bitte zahlen Sie bequem per PayPal: {paypal_url}\nBitte geben Sie als Verwendungszweck {b['ref']} an."
    return f"Wir melden uns mit den Zahlungsdaten. Ihre Bestellnummer: {b['ref']}."


STATUS_MAIL = {
    "bestaetigt": ("Bestellung bestätigt", "wir haben Ihre Bestellung {ref} bestätigt und kümmern uns darum."),
    "bezahlt": ("Zahlung erhalten", "vielen Dank, die Zahlung zu Ihrer Bestellung {ref} ist bei uns eingegangen."),
    "im_druck": ("Ihre Bestellung ist in Arbeit", "Ihre Bestellung {ref} ist jetzt in Arbeit."),
    "versendet": ("Ihre Bestellung ist unterwegs", "Ihre Bestellung {ref} wurde versendet."),
    "abholbereit": ("Ihre Bestellung ist abholbereit", "Ihre Bestellung {ref} liegt zur Abholung bereit."),
    "storniert": ("Bestellung storniert", "Ihre Bestellung {ref} wurde storniert."),
}


def status_mail(status: str, b: dict, firma: str) -> tuple[str, str] | None:
    """(Betreff, Text) für den Kunden oder None, wenn zu diesem Status keine Mail passt."""
    if status not in STATUS_MAIL:
        return None
    betreff, satz = STATUS_MAIL[status]
    text = f"Guten Tag {b['name']},\n\n{satz.format(ref=b['ref'])}"
    if status == "versendet" and b.get("sendungsnummer"):
        text += f"\nSendungsnummer: {b['sendungsnummer']}"
    if status == "abholbereit" and b.get("abholtermin"):
        text += f"\nAbholung: {b['abholtermin']}"
    return f"{betreff} ({b['ref']})", text + f"\n\nBei Fragen antworten Sie einfach auf diese E-Mail.\n\nMit freundlichen Grüßen\n{firma}"
