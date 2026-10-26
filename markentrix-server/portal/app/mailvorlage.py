"""Einheitliches, ordentliches Mail-Layout für alle Mails, die im Namen eines Kunden verschickt werden.
Aus dem einfachen Text der Aufrufer wird eine HTML-Mail (Kopf mit Logo, Absätze, Tabelle für „Angabe: Wert“, Knopf statt langem Link, Signatur).
Der Text bleibt als Alternative erhalten (Mail-Programme ohne HTML) und wird dort sauber abgeschlossen."""
import re
from html import escape

URL = re.compile(r"https?://[^\s<>\"']+")
ZEILE_WERT = re.compile(r"^([^:\n]{1,40}):\s+(\S.*)$")
GRUSS = re.compile(r"^(mit freundlichen gr(ü|ue)ßen|freundliche gr(ü|ue)ße|viele gr(ü|ue)ße|beste gr(ü|ue)ße|herzliche gr(ü|ue)ße)\b", re.I)
HINWEIS_ZEILE = re.compile(r"^(sie können direkt auf diese e-mail antworten|—|--)", re.I)
BILD_TYPEN = {"image/png": "png", "image/jpeg": "jpeg", "image/gif": "gif"}


def _knopf_text(url: str, davor: str) -> str:
    u, d = url.lower(), davor.lower()
    if "/bestaetigen?" in u:
        return "Termin bestätigen"
    if "/ablehnen?" in u:
        return "Termin ablehnen"
    if "/termin/absagen" in u:
        return "Termin absagen"
    if "/termin/verschieben" in u:
        return "Termin verschieben"
    if "/admin#" in u or "/app#" in u or "/vertrieb#" in u:
        return "Im Portal öffnen"
    if "zahl" in d or "paypal" in u or "anzahlung" in d:
        return "Jetzt bezahlen"
    if "bewert" in d or "review" in u:
        return "Bewertung abgeben"
    return "Link öffnen"


def _verlinken(t: str) -> str:
    """Escaped Text mit anklickbaren Adressen (die Adresse selbst bleibt sichtbar, aber kurz gehalten)."""
    def ersetze(m):
        u = m.group(0).rstrip(".,;)")
        rest = m.group(0)[len(u):]
        sicht = u if len(u) <= 45 else u[:42] + "…"
        return f'<a href="{escape(u, quote=True)}" style="color:#1d4ed8">{escape(sicht)}</a>{escape(rest)}'
    out, pos = [], 0
    for m in URL.finditer(t):
        out.append(escape(t[pos:m.start()]))
        out.append(ersetze(m))
        pos = m.end()
    out.append(escape(t[pos:]))
    return "".join(out)


def _koerper_ohne_gruss(text: str) -> tuple[str, bool, str]:
    """Trennt den vom Aufrufer angehängten Schluss („Mit freundlichen Grüßen / Firma“) ab.
    Rückgabe: (Text davor, war ein Gruß da = Mail an einen Gast, Text danach (z. B. Abmeldelink, bleibt erhalten))."""
    zeilen = text.rstrip().split("\n")
    for i in range(len(zeilen) - 1, -1, -1):
        if GRUSS.match(zeilen[i].strip()):
            rest = zeilen[i + 1:]
            k = 0
            while k < len(rest) and rest[k].strip() and k < 3 and not URL.search(rest[k]):   # Zeilen direkt unter dem Gruß = alte Unterschrift
                k += 1
            return "\n".join(zeilen[:i]).rstrip(), True, "\n".join(rest[k:]).strip()
    return text.rstrip(), False, ""


def signatur_text(firma: str, eigene: str | None) -> str:
    return (eigene or "").strip() or f"Mit freundlichen Grüßen\n{firma}"


def text_mit_signatur(text: str, firma: str, eigene: str | None, extras: dict | None = None) -> str:
    koerper, gast, nachsatz = _koerper_ohne_gruss(text)
    if not gast:
        return text
    return koerper + "\n\n" + signatur_text(firma, eigene) + text_extras(extras) + (("\n\n" + nachsatz) if nachsatz else "")


def _absatz(zeilen: list[str], html: list[str], ci: bool = False) -> None:
    """Textzeilen als Absatz, „- Punkt“-Zeilen als Liste, eine Zeile nur mit Adresse als Knopf (Beschriftung nach dem Text davor)."""
    text: list[str] = []
    punkte: list[str] = []
    davor = ""

    def text_aus():
        nonlocal davor
        if text:
            davor = " ".join(text)
            teile = [(f'<b>{_verlinken(z)}</b>' if z.strip().endswith(":") and len(z.strip()) <= 30 else _verlinken(z)) for z in text]
            html.append(f'<p style="margin:0 0 12px;line-height:1.55;color:#111827">{"<br>".join(teile)}</p>')
            text.clear()

    def punkte_aus():
        if punkte:
            html.append('<ul style="margin:0 0 14px;padding-left:20px;line-height:1.55;color:#111827">' + "".join(f'<li style="margin:2px 0">{_verlinken(x)}</li>' for x in punkte) + "</ul>")
            punkte.clear()

    for z in zeilen:
        st = z.strip()
        if st.startswith("- "):
            text_aus()
            punkte.append(st[2:])
            continue
        punkte_aus()
        m = URL.fullmatch(st)
        if m:
            text_aus()
            url = m.group(0)
            if ci:   # Mail von Markentrix an das eigene Team: Knopf im CI (Cyan → Blau, Schrift Navy)
                html.append(f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:6px 0 18px"><tr><td bgcolor="#28C7F7" style="border-radius:12px;background:#28C7F7;'
                            f'background-image:linear-gradient(135deg,#28C7F7,#1E9BFF)"><a href="{escape(url, quote=True)}" style="display:inline-block;padding:13px 22px;color:#0B1020;'
                            f'text-decoration:none;font-weight:700;border-radius:12px">{escape(_knopf_text(url, davor))}<span> &rarr;</span></a></td></tr></table>')
            else:
                html.append(f'<p style="margin:4px 0 18px"><a href="{escape(url, quote=True)}" style="display:inline-block;background:#111827;color:#ffffff;text-decoration:none;'
                            f'padding:11px 20px;border-radius:8px;font-weight:600">{escape(_knopf_text(url, davor))}</a></p>')
        else:
            text.append(z)
    text_aus()
    punkte_aus()


def _bloecke(koerper: str, firma: str, ci: bool = False) -> list[str]:
    html: list[str] = []
    for block in re.split(r"\n\s*\n", koerper.strip()):
        zeilen = [z.rstrip() for z in block.split("\n") if z.strip() != ""]
        if not zeilen:
            continue
        if len(zeilen) == 1 and HINWEIS_ZEILE.match(zeilen[0].strip()) and zeilen[0].strip() in ("—", "--"):
            continue
        karte = re.match(r"^(\d{1,2})\.\s+(\S.{0,200})$", zeilen[0])
        if karte:   # nummerierter Eintrag (z. B. Aufgabenliste): Überschrift, darunter Einzelheiten
            html.append(f'<p style="margin:22px 0 8px;padding-top:14px;border-top:1px solid #e5e7eb;font-weight:700;font-size:17px;color:#111827">{karte.group(1)}. {escape(karte.group(2))}</p>')
            _absatz(zeilen[1:], html, ci)
            continue
        # Abschnitt „Nachricht:“ / „Ihre Angaben:“ mit Überschrift
        kopf = None
        if zeilen[0].endswith(":") and len(zeilen[0]) <= 40 and len(zeilen) > 1 and not URL.search(zeilen[0]):
            kopf, zeilen = zeilen[0][:-1], zeilen[1:]
        paare = [ZEILE_WERT.match(z) for z in zeilen]
        if zeilen and all(paare) and not any(URL.search(z) for z in zeilen):
            zl = "".join(f'<tr><td style="padding:6px 14px 6px 0;color:#6b7280;vertical-align:top;white-space:nowrap">{escape(m.group(1))}</td>'
                         f'<td style="padding:6px 0;color:#111827;vertical-align:top">{_wert(m.group(1), m.group(2))}</td></tr>' for m in paare)
            if kopf:
                html.append(f'<p style="margin:18px 0 6px;font-weight:600;color:#111827">{escape(kopf)}</p>')
            html.append(f'<table role="presentation" cellpadding="0" cellspacing="0" style="border-top:1px solid #e5e7eb;border-bottom:1px solid #e5e7eb;width:100%;margin:0 0 14px">{zl}</table>')
            continue
        if kopf and not any(URL.search(z) for z in zeilen):
            html.append(f'<p style="margin:18px 0 6px;font-weight:600;color:#111827">{escape(kopf)}</p>'
                        f'<div style="background:#f3f4f6;border-radius:8px;padding:12px 14px;margin:0 0 12px;color:#111827">{"<br>".join(_verlinken(z) for z in zeilen)}</div>')
            continue
        if kopf:
            zeilen = [kopf + ":"] + zeilen
        _absatz(zeilen, html, ci)
    return html


def _wert(label: str, wert: str) -> str:
    """Wert in der Tabelle „Angabe: Wert“: Telefonnummern und Mail-Adressen anklickbar."""
    lab = label.strip().lower()
    if lab in ("telefon", "tel.", "mobil", "handy") and re.fullmatch(r"\+?[0-9][0-9 /()\-]{4,}[0-9]", wert.strip()):
        return f'<a href="tel:{escape(re.sub(r"[^0-9+]", "", wert), quote=True)}" style="color:#1d4ed8;text-decoration:none;font-weight:600">{escape(wert.strip())}</a>'
    if re.fullmatch(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", wert.strip()):
        return f'<a href="mailto:{escape(wert.strip(), quote=True)}" style="color:#1d4ed8;text-decoration:none">{escape(wert.strip())}</a>'
    return _verlinken(wert)


KONTAKT = re.compile(r"(?P<mail>[\w.+-]+@[\w-]+(?:\.[\w-]+)+)|(?P<url>https?://[^\s<>\"']+)|(?i:(?P<lab>web|internet|homepage)\s*:\s*)(?P<dom>(?:https?://)?[\w-]+(?:\.[\w-]+)+(?:/\S*)?)|(?i:(?P<tel>tel\.?|telefon|mobil|handy)\s*:?\s*)(?P<nr>\+?[0-9][0-9 /()\-]{5,}[0-9])")


def _kontakt_verlinken(z: str) -> str:
    """Eine Signaturzeile: Mail-Adressen, Web-Adressen und Telefonnummern werden anklickbar."""
    out, pos = [], 0
    for m in KONTAKT.finditer(z):
        out.append(escape(z[pos:m.start()]))
        if m.group("mail"):
            out.append(f'<a href="mailto:{escape(m.group("mail"), quote=True)}" style="color:#1d4ed8;text-decoration:none">{escape(m.group("mail"))}</a>')
        elif m.group("url"):
            u = m.group("url").rstrip(".,;)")
            out.append(f'<a href="{escape(u, quote=True)}" style="color:#1d4ed8;text-decoration:none">{escape(u)}</a>')
        elif m.group("dom"):
            d = m.group("dom").rstrip(".,;)")
            u = d if d.lower().startswith("http") else "https://" + d
            out.append(f'{escape(m.group("lab"))}: <a href="{escape(u, quote=True)}" style="color:#1d4ed8;text-decoration:none">{escape(d)}</a>')
        else:
            nr = m.group("nr")
            out.append(f'{escape(m.group("tel"))} <a href="tel:{escape(re.sub(r"[^0-9+]", "", nr), quote=True)}" style="color:#1d4ed8;text-decoration:none">{escape(nr)}</a>')
        pos = m.end()
    out.append(escape(z[pos:]))
    return "".join(out)


def _sicherer_link(u: str | None) -> str | None:
    u = (u or "").strip()
    return u if re.fullmatch(r"https://[^\s<>\"']{4,300}", u) else None


def signatur_html(firma: str, signatur: str | None, farbe: str, logo_cid: str | None, extras: dict | None) -> str:
    extras = extras or {}
    zeilen = signatur_text(firma, signatur).split("\n")
    gruss = ""
    if zeilen and GRUSS.match(zeilen[0].strip()):
        gruss, zeilen = zeilen[0].strip(), zeilen[1:]
    if not any(z.strip() for z in zeilen):
        zeilen = [firma]
    rechts = []
    for i, z in enumerate(zeilen):
        if not z.strip():
            rechts.append('<div style="height:10px;line-height:10px">&nbsp;</div>')
        elif i == 0:
            rechts.append(f'<div style="font-weight:700;font-size:17px;color:#111827">{escape(z.strip())}</div>')
        else:
            rechts.append(f'<div style="color:#374151;line-height:1.5">{_kontakt_verlinken(z.strip())}</div>')
    if logo_cid:
        zelle = (f'<td valign="middle" style="padding:12px 16px 12px 0;width:34%"><img src="cid:{logo_cid}" alt="{escape(firma, quote=True)}" style="max-width:100%;max-height:120px;display:block;border:0"></td>'
                 f'<td valign="middle" style="padding:8px 0 8px 16px;border-left:1px solid #d1d5db">{"".join(rechts)}</td>')
    else:
        zelle = f'<td valign="middle" style="padding:14px 0">{"".join(rechts)}</td>'
    h = ""
    if gruss:
        h += f'<p style="margin:26px 0 12px;color:#111827">{escape(gruss)}</p>'
    else:
        h += '<div style="height:20px"></div>'
    h += f'<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;border-top:3px solid {farbe}"><tr>{zelle}</tr></table>'
    bew = _sicherer_link(extras.get("bewertung_link"))
    if bew:
        h += (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:14px 0 0"><tr><td style="background:#1f2937;padding:16px 22px;color:#ffffff;line-height:1.5">'
              f'Ihre Meinung hilft uns weiter.<br><a href="{escape(bew, quote=True)}" style="color:#ffffff;font-weight:700;text-decoration:underline">Jetzt Google-Bewertung abgeben</a></td></tr></table>')
    soz = [(n, _sicherer_link(extras.get(k))) for n, k in (("Facebook", "facebook"), ("Instagram", "instagram"))]
    soz = [(n, u) for n, u in soz if u]
    if soz:
        h += '<p style="margin:16px 0 0;color:#111827">Folgen Sie uns: ' + " | ".join(f'<a href="{escape(u, quote=True)}" style="color:#1d4ed8;font-weight:700;text-decoration:none">{n}</a>' for n, u in soz) + "</p>"
    if (extras.get("hinweis") or "").strip():
        h += f'<p style="margin:18px 0 0;font-size:12px;line-height:1.5;color:#6b7280">{escape(extras["hinweis"].strip())}</p>'
    return h


def text_extras(extras: dict | None) -> str:
    extras = extras or {}
    t = ""
    if _sicherer_link(extras.get("bewertung_link")):
        t += "\n\nIhre Meinung hilft uns weiter. Google-Bewertung abgeben: " + extras["bewertung_link"].strip()
    soz = [f"{n}: {extras[k].strip()}" for n, k in (("Facebook", "facebook"), ("Instagram", "instagram")) if _sicherer_link(extras.get(k))]
    if soz:
        t += "\n\nFolgen Sie uns: " + " | ".join(soz)
    if (extras.get("hinweis") or "").strip():
        t += "\n\n" + extras["hinweis"].strip()
    return t


def html_mail(firma: str, text: str, signatur: str | None = None, farbe: str | None = None, logo_cid: str | None = None, extras: dict | None = None, intern: bool = False) -> str:
    koerper, gast, nachsatz = _koerper_ohne_gruss(text)
    if intern:   # Mail von Markentrix selbst: Text bleibt wie er ist (Gruß inklusive), keine Kunden-Signatur
        koerper, gast, nachsatz = text.rstrip(), False, ""
    # Hinweis „Sie können direkt auf diese E-Mail antworten …“ klein ans Ende
    hinweis = ""
    teile = re.split(r"\n\s*—\s*\n", koerper)
    if len(teile) > 1 and HINWEIS_ZEILE.match(teile[-1].strip()):
        hinweis, koerper = teile[-1].strip(), "\n—\n".join(teile[:-1])
    m_auto = re.search(r"\n\s*\n(\(automatische [^\n]*\))\s*$", koerper)
    if m_auto:
        hinweis, koerper = m_auto.group(1), koerper[:m_auto.start()].rstrip()
    farbe = farbe if farbe and re.fullmatch(r"#[0-9a-fA-F]{6}", farbe) else "#111827"
    # Mail an einen Gast: Logo steht in der Signatur, im Kopf nur der Firmenname. Mail ans Team (ohne Signatur): Logo im Kopf.
    if intern:
        return _intern_html(firma, koerper, logo_cid, hinweis)
    if logo_cid and not gast:
        kopf = f'<img src="cid:{logo_cid}" alt="{escape(firma, quote=True)}" style="max-height:56px;max-width:220px;display:block;border:0">'
    else:
        kopf = f'<div style="font-size:20px;font-weight:700;color:#111827">{escape(firma)}</div>'
    sig = signatur_html(firma, signatur, farbe, logo_cid, extras) if gast else ""
    fuss = f'<p style="margin:22px 0 0;font-size:12px;color:#9ca3af">{escape(hinweis)}</p>' if hinweis else ""
    if nachsatz:   # z. B. Abmeldelink: klein unter der Signatur
        fuss = "".join(f'<p style="margin:16px 0 0;font-size:12px;line-height:1.5;color:#6b7280">{"<br>".join(_verlinken(z) for z in b.split(chr(10)))}</p>' for b in re.split(r"\n\s*\n", nachsatz)) + fuss
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
            '<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:16px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6"><tr><td align="center" style="padding:24px 12px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden">'
            f'<tr><td style="padding:22px 28px 16px;border-bottom:3px solid {farbe}">{kopf}</td></tr>'
            f'<tr><td style="padding:24px 28px 28px">{"".join(_bloecke(koerper, firma))}{sig}{fuss}</td></tr></table>'
            '</td></tr></table></body></html>')


def _intern_html(firma: str, koerper: str, logo_cid: str | None, hinweis: str) -> str:
    """Mails von Markentrix an das eigene Team (neuer Lead, Alarme, Aufgaben) im Markentrix-CI."""
    schrift = "Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
    logo = f'<td valign="middle" style="padding-right:10px"><img src="cid:{logo_cid}" alt="" width="40" height="34" style="display:block;border:0;width:40px;height:34px"></td>' if logo_cid else ""
    fuss = f'<p style="margin:16px 0 0;font-size:12px;color:#667085">{escape(hinweis)}</p>' if hinweis else ""
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"></head>'
            f'<body style="margin:0;padding:0;background:#F8FAFC;font-family:{schrift};font-size:16px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC"><tr><td align="center" style="padding:24px 12px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">'
            f'<tr><td style="padding:0 4px 14px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{logo}'
            f'<td valign="middle" style="font-family:{schrift};font-size:20px;font-weight:800;letter-spacing:-.02em;color:#0B1020">{escape(firma)}</td></tr></table></td></tr>'
            '<tr><td style="background:#FFFFFF;border:1px solid #E6E9F3;border-radius:18px;overflow:hidden">'
            '<div style="height:4px;line-height:4px;font-size:0;background:#28C7F7;background-image:linear-gradient(90deg,#28C7F7,#1E9BFF)">&nbsp;</div>'
            f'<div style="padding:24px 22px 22px;font-family:{schrift}">{"".join(_bloecke(koerper, firma, True))}{fuss}</div></td></tr>'
            '</table></td></tr></table></body></html>')


def bild_pruefen(logo: bytes | None, typ: str | None) -> tuple[bytes, str, str] | None:
    """(Daten, Haupttyp, Untertyp) für ein einbettbares Logo, sonst None (SVG und Co. zeigen Mail-Programme nicht)."""
    if not logo or typ not in BILD_TYPEN or len(logo) > 400_000:
        return None
    return bytes(logo), "image", BILD_TYPEN[typ]


def inhalt_setzen(msg, text: str, firma: str, signatur: str | None = None, farbe: str | None = None, logo: tuple[bytes, str, str] | None = None, extras: dict | None = None, intern: bool = False) -> None:
    """Setzt Text und HTML (mit eingebettetem Logo) in eine EmailMessage. Der Aufrufer hängt danach Anhänge an."""
    msg.set_content(text if intern else text_mit_signatur(text, firma, signatur, extras))
    cid = "logo@mail" if logo else None
    msg.add_alternative(html_mail(firma, text, signatur, farbe, cid, extras, intern), subtype="html")
    if logo:
        daten, haupt, unter = logo
        msg.get_payload()[1].add_related(daten, maintype=haupt, subtype=unter, cid=f"<{cid}>", disposition="inline")
