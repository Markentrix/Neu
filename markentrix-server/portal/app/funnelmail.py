"""HTML-Layout der Funnel-Mails (Ergebnis des Website-Checks und Nachfass-Mails) im Markentrix-CI.
Aus dem Text, den der Admin pflegt, wird eine gestaltete Mail: Kopf mit Logo, Absätze, Ergebnis-Karte mit Punktzahl
und Prüfpunkten (an der Stelle von {ergebnis} bzw. {punkte}), Termin-Knopf statt langer Adresse, Gruß, Firmenangaben, Abmeldelink.
Nur Tabellen und Inline-Styles, damit Gmail, Outlook und Apple Mail es gleich zeigen."""
import re
from html import escape

MARKE = "⁣ERGEBNIS⁣"   # unsichtbarer Platzhalter: an dieser Stelle steht in der HTML-Mail die Ergebnis-Karte
NAVY, TEXT, MUT, LINIE, HELL, CYAN, BLAU = "#0B1020", "#1F2937", "#667085", "#E6E9F3", "#F8FAFC", "#28C7F7", "#1E9BFF"
SCHRIFT = "Inter,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
AMPEL = {"gruen": ("#16A34A", "#DCFCE7", "Gut aufgestellt"), "gelb": ("#B45309", "#FEF3C7", "Ausbaufähig"), "rot": ("#DC2626", "#FEE2E2", "Handlungsbedarf")}
CHIP = {"gut": ("gut", "#166534", "#DCFCE7"), "mittel": ("teilweise", "#92400E", "#FEF3C7"), "schlecht": ("fehlt", "#991B1B", "#FEE2E2")}
URL = re.compile(r"https?://[^\s<>\"']+")


def _links(t: str) -> str:
    out, pos = [], 0
    for m in URL.finditer(t):
        u = m.group(0).rstrip(".,;)")
        out.append(escape(t[pos:m.start()]))
        out.append(f'<a href="{escape(u, quote=True)}" style="color:{BLAU};text-decoration:underline">{escape(u if len(u) <= 50 else u[:47] + "…")}</a>')
        pos = m.start() + len(u)
    out.append(escape(t[pos:]))
    return "".join(out)


def _knopf(url: str) -> str:
    beschriftung = "15-Minuten-Termin wählen" if url.rstrip("/").endswith("/buchen") else "Link öffnen"
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:6px 0 22px"><tr>'
            f'<td bgcolor="{CYAN}" style="border-radius:12px;background:{CYAN};background-image:linear-gradient(135deg,{CYAN},{BLAU})">'
            f'<a href="{escape(url, quote=True)}" style="display:inline-block;padding:15px 26px;font-family:{SCHRIFT};font-size:16px;font-weight:700;'
            f'color:{NAVY};text-decoration:none;border-radius:12px">{escape(beschriftung)} &rarr;</a></td></tr></table>')


def _p(inhalt: str) -> str:
    return f'<p style="margin:0 0 16px;font-family:{SCHRIFT};font-size:16px;line-height:1.6;color:{TEXT}">{inhalt}</p>'


def _ergebnis_karte(e: dict) -> str:
    farbe, grund, wort = AMPEL.get(e.get("ampel"), (BLAU, "#E0F2FE", "Ergebnis"))
    score = e.get("score", 0)
    pkt = e.get("punkte") or []
    gut = [x for x in pkt if x.get("status") == "gut"][:2]
    from .funnelcheck import WICHTIG   # gleiche Reihenfolge wie im Text der Mail
    rang = {k: i for i, k in enumerate(WICHTIG)}
    offen = sorted([x for x in pkt if x.get("status") == "schlecht"], key=lambda x: rang.get(x.get("id"), 99)) + \
        sorted([x for x in pkt if x.get("status") == "mittel"], key=lambda x: rang.get(x.get("id"), 99))
    zeilen = []
    for x in offen[:3] + gut:
        wort_c, fg, bg = CHIP.get(x.get("status"), ("", MUT, HELL))
        zeilen.append(
            f'<tr><td valign="top" style="padding:10px 10px 10px 0;width:68px"><span style="display:inline-block;padding:3px 9px;border-radius:99px;background:{bg};'
            f'color:{fg};font-family:{SCHRIFT};font-size:12px;font-weight:700;white-space:nowrap">{wort_c}</span></td>'
            f'<td valign="top" style="padding:9px 0;border-bottom:1px solid {LINIE}"><div style="font-family:{SCHRIFT};font-size:15px;font-weight:700;color:{NAVY}">{escape(x.get("titel", ""))}</div>'
            f'<div style="font-family:{SCHRIFT};font-size:14px;line-height:1.5;color:{MUT}">{escape(x.get("text", ""))}</div></td></tr>')
    rest = max(0, len(pkt) - len(offen[:3]) - len(gut))
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:4px 0 22px;border:1px solid {LINIE};border-radius:16px;background:#FFFFFF">'
        f'<tr><td style="padding:18px 16px 6px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td valign="middle" style="width:92px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        f'<td align="center" valign="middle" style="width:80px;height:80px;border-radius:50%;border:6px solid {farbe};background:#FFFFFF">'
        f'<div style="font-family:{SCHRIFT};font-size:28px;font-weight:800;line-height:1;color:{NAVY}">{escape(str(score))}</div>'
        f'<div style="font-family:{SCHRIFT};font-size:11px;color:{MUT};padding-top:3px">von 100</div></td></tr></table></td>'
        f'<td valign="middle" style="padding-left:14px"><span style="display:inline-block;padding:3px 10px;border-radius:99px;background:{grund};color:{farbe};'
        f'font-family:{SCHRIFT};font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase">{wort}</span>'
        f'<div style="font-family:{SCHRIFT};font-size:17px;font-weight:700;line-height:1.35;color:{NAVY};padding-top:6px">{escape(e.get("zusammenfassung", ""))}</div>'
        f'<div style="font-family:{SCHRIFT};font-size:13px;color:{MUT};padding-top:4px">Geprüft: {escape(_host(e.get("website", "")))}</div></td>'
        f'</tr></table></td></tr>'
        f'<tr><td style="padding:6px 16px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(zeilen)}</table></td></tr>'
        f'<tr><td style="padding:10px 16px 16px;font-family:{SCHRIFT};font-size:13px;color:{MUT}">'
        f'{"Dazu " + str(rest) + " weitere Punkte und konkrete Tipps im PDF im Anhang." if rest else "Alle Punkte mit konkreten Tipps finden Sie im PDF im Anhang."}</td></tr></table>')


def _host(u: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", u or "").rstrip("/")


def _koerper(text: str, e: dict | None) -> str:
    html, karte_da = [], False
    for block in re.split(r"\n\s*\n", text.strip()):
        zeilen = [z.strip() for z in block.split("\n") if z.strip()]
        if not zeilen:
            continue
        absatz, punkte = [], []

        def absatz_aus():
            if absatz:
                html.append(_p("<br>".join(_links(z) for z in absatz)))
                absatz.clear()

        def punkte_aus():
            if punkte:
                html.append(f'<ul style="margin:0 0 16px;padding-left:20px;font-family:{SCHRIFT};font-size:16px;line-height:1.6;color:{TEXT}">'
                            + "".join(f'<li style="margin:2px 0">{_links(x)}</li>' for x in punkte) + "</ul>")
                punkte.clear()
        for z in zeilen:
            if MARKE in z:
                absatz_aus(); punkte_aus()
                if e and not karte_da:
                    html.append(_ergebnis_karte(e)); karte_da = True
                vorher, _, nachher = z.partition(MARKE)
                if vorher.strip():
                    absatz.append(vorher.strip())
                if nachher.strip():
                    absatz.append(nachher.strip())
            elif z.startswith("- "):
                absatz_aus(); punkte.append(z[2:])
            elif URL.fullmatch(z):
                absatz_aus(); punkte_aus(); html.append(_knopf(z))
            elif (m := URL.search(z)) and z.endswith(m.group(0)) and m.group(0).rstrip("/").endswith("/buchen"):
                punkte_aus()   # Termin-Adresse am Zeilenende: Text als Absatz, Adresse als Knopf darunter
                vorne = z[:m.start()].rstrip()
                if vorne:
                    absatz.append(vorne)
                absatz_aus(); html.append(_knopf(m.group(0)))
            else:
                punkte_aus(); absatz.append(z)
        absatz_aus(); punkte_aus()
    if e and not karte_da:   # Text ohne Platzhalter: Karte nach der Anrede
        html.insert(min(1, len(html)), _ergebnis_karte(e))
    return "".join(html)


def html_mail(text: str, firma: dict, abmelden: str, impressum: str, ergebnis: dict | None = None, logo_cid: str | None = None) -> str:
    """text = fertiger Mailtext ohne Gruß (Platzhalter schon gefüllt, {ergebnis}/{punkte} als MARKE)."""
    name = firma.get("name") or "Markentrix"
    kontakt = []
    if firma.get("telefon"):
        kontakt.append(f'<a href="tel:{escape(re.sub(r"[^0-9+]", "", firma["telefon"]), quote=True)}" style="color:{NAVY};text-decoration:none">{escape(firma["telefon"])}</a>')
    if firma.get("email"):
        kontakt.append(f'<a href="mailto:{escape(firma["email"], quote=True)}" style="color:{NAVY};text-decoration:none">{escape(firma["email"])}</a>')
    if firma.get("website"):
        w = firma["website"] if firma["website"].startswith("http") else "https://" + firma["website"]
        kontakt.append(f'<a href="{escape(w, quote=True)}" style="color:{NAVY};text-decoration:none">{escape(_host(w))}</a>')
    anschrift = " · ".join(x for x in [name + (", Inhaber " + firma["inhaber"] if firma.get("inhaber") else ""), firma.get("strasse"),
                                       " ".join(x for x in [firma.get("plz"), firma.get("ort")] if x)] if x)
    logo = (f'<img src="cid:{logo_cid}" alt="" width="40" height="34" style="display:block;border:0;width:40px;height:34px">' if logo_cid else "")
    return (
        '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"></head>'
        f'<body style="margin:0;padding:0;background:{HELL}">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{HELL}"><tr><td align="center" style="padding:24px 12px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">'
        # Kopf
        f'<tr><td style="padding:0 4px 14px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        f'<td valign="middle">{logo}</td><td valign="middle" style="padding-left:{10 if logo else 0}px;font-family:{SCHRIFT};font-size:20px;font-weight:800;letter-spacing:-.02em;color:{NAVY}">{escape(name)}</td>'
        f'</tr></table></td></tr>'
        # Karte
        f'<tr><td style="background:#FFFFFF;border:1px solid {LINIE};border-radius:18px;overflow:hidden">'
        f'<div style="height:4px;line-height:4px;font-size:0;background:{CYAN};background-image:linear-gradient(90deg,{CYAN},{BLAU})">&nbsp;</div>'
        f'<div style="padding:26px 22px 24px">{_koerper(text, ergebnis)}'
        f'<p style="margin:8px 0 2px;font-family:{SCHRIFT};font-size:16px;color:{TEXT}">Viele Grüße</p>'
        f'<p style="margin:0;font-family:{SCHRIFT};font-size:16px;font-weight:700;color:{NAVY}">Ihr {escape(name)}-Team</p>'
        + (f'<p style="margin:6px 0 0;font-family:{SCHRIFT};font-size:14px;line-height:1.6;color:{MUT}">{" &nbsp;·&nbsp; ".join(kontakt)}</p>' if kontakt else "")
        + '</div></td></tr>'
        # Fuß
        f'<tr><td style="padding:18px 8px 0;font-family:{SCHRIFT};font-size:12px;line-height:1.6;color:{MUT};text-align:center">'
        f'{escape(anschrift)}<br><a href="{escape(impressum, quote=True)}" style="color:{MUT}">Impressum</a> &nbsp;·&nbsp; '
        f'<a href="{escape(abmelden, quote=True)}" style="color:{MUT}">Keine weiteren Mails zum Website-Check</a></td></tr>'
        '</table></td></tr></table></body></html>')
