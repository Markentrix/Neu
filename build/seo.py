"""Suchmaschinen- und KI-Auffindbarkeit: Open Graph, strukturierte Daten, llms.txt, Teilen-Bild.

Ohne Domain bleibt alles relativ (Upload auf beliebige Domain). Für den Livegang mit fester Domain:
  python3 build/build.py --live                      (Domain aus build/config.py)
  python3 build/build.py --domain https://schichtatelier.de
setzt zusätzlich kanonische Adressen, absolute Sitemap, og:url und og:image.
"""
import os, sys, json, html
import config as C

E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "website-fertig"))


def site_url():
    if "--live" in sys.argv:
        return getattr(C, "DOMAIN", "").rstrip("/")
    for i, a in enumerate(sys.argv):
        if a == "--domain" and i + 1 < len(sys.argv):
            return sys.argv[i + 1].rstrip("/")
    return os.environ.get("SITE_URL", "").rstrip("/")


SITE = site_url()
if SITE and not SITE.startswith("https://"):
    raise SystemExit("--domain muss mit https:// beginnen")


def absolut(pfad):
    return f"{SITE}/{pfad.lstrip('/')}" if SITE else ""


def seiten_url(name):
    return absolut("" if name == "index.html" else name)


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>\n"


def meta(name, title, desc, extra=""):
    """Zusätzliche <head>-Zeilen: Robots, kanonische Adresse, Open Graph, Twitter."""
    if "noindex" in extra:
        return ""
    t = []
    t.append('<meta name="robots" content="index,follow,max-image-preview:large">')
    if SITE:
        t.append(f'<link rel="canonical" href="{E(seiten_url(name))}">')
    t.append(f'<meta property="og:site_name" content="{E(C.MARKE)}">')
    t.append('<meta property="og:locale" content="de_DE">')
    t.append('<meta property="og:type" content="website">')
    t.append(f'<meta property="og:title" content="{E(title)}">')
    t.append(f'<meta property="og:description" content="{E(desc)}">')
    if SITE:
        t.append(f'<meta property="og:url" content="{E(seiten_url(name))}">')
        t.append(f'<meta property="og:image" content="{E(absolut("assets/img/teilen.jpg"))}">')
        t.append('<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">')
        t.append(f'<meta property="og:image:alt" content="{E(C.MARKE)}: 3D-Druck aus Celle">')
        t.append('<meta name="twitter:card" content="summary_large_image">')
    else:
        t.append('<meta name="twitter:card" content="summary">')
    return "\n".join(t) + "\n"


def organisation():
    o = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": C.MARKE, "legalName": C.FIRMA,
         "description": "3D-Druck-Atelier in Celle: Deko, Geschenke und Teile nach eigener Datei, gedruckt auf Bestellung auf einem Bambu Lab X1 Carbon.",
         "telephone": C.TELEFON, "email": C.EMAIL, "founder": {"@type": "Person", "name": C.INHABER},
         "address": {"@type": "PostalAddress", "streetAddress": C.STRASSE, "postalCode": C.PLZ_ORT.split()[0], "addressLocality": " ".join(C.PLZ_ORT.split()[1:]), "addressCountry": "DE"},
         "areaServed": {"@type": "Country", "name": "Deutschland"},
         "knowsAbout": ["3D-Druck", "PLA", "PETG", "ABS", "TPU", "Ersatzteile", "Geschenke"]}
    if SITE:
        o["url"] = SITE + "/"; o["@id"] = SITE + "/#betrieb"; o["logo"] = absolut("apple-touch-icon.png"); o["image"] = absolut("assets/img/teilen.jpg")
    return o


def website():
    w = {"@context": "https://schema.org", "@type": "WebSite", "name": C.MARKE, "inLanguage": "de-DE"}
    if SITE: w["url"] = SITE + "/"
    return w


def breadcrumb(name, title):
    if name == "index.html" or name.startswith("produkt/"):
        return ""
    teile = [("Start", "index.html")]
    if name.startswith("material/"): teile.append(("Materialien", "materialien.html"))
    teile.append((title.split(" · ")[0], name))
    items = [{"@type": "ListItem", "position": i + 1, "name": n, **({"item": seiten_url(u)} if SITE else {})} for i, (n, u) in enumerate(teile)]
    return ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})


def faq(paare):
    if not paare: return ""
    return ld({"@context": "https://schema.org", "@type": "FAQPage",
               "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in paare]})


def llms_txt(materialien, versand_pauschale, versandfrei_ab):
    z = [f"# {C.MARKE}", "",
         f"> {C.MARKE} ist ein kleines 3D-Druck-Atelier in {C.PLZ_ORT.split(' ', 1)[1]}. {C.INHABER} druckt Deko, Geschenke und Teile nach eigener Datei auf einem Bambu Lab X1 Carbon, jeweils erst nach der Bestellung.", "",
         "## Das Wichtigste", "",
         f"- Ort: {C.STRASSE}, {C.PLZ_ORT}. Abholung nach Terminabsprache.",
         f"- Kontakt: {C.EMAIL}, {C.TELEFON}",
         f"- Produktion: {C.PRODUKTIONSZEIT}, danach Versand ({C.LIEFERZEIT}). Alle Zeiten sind Richtwerte.",
         f"- Versand innerhalb Deutschlands: {('%.2f' % versand_pauschale).replace('.', ',')} Euro, ab {('%.2f' % versandfrei_ab).replace('.', ',')} Euro Bestellwert kostenlos. Abholung in Celle kostenlos.",
         "- Zahlung per PayPal oder bei Abholung. Bestellungen werden per E-Mail bestätigt.",
         "- Druckservice: eigene Dateien (STL, 3MF, STEP, OBJ), Ersatzteile, Einzelstücke und Kleinserien ab 1 Stück, bis 25 cm Kantenlänge, Preis und Lieferzeit vor dem Druck.",
         "", "## Materialien (Wärmegrenze laut Seite)", ""]
    for m in materialien:
        z.append(f"- {m['name']}: {m['einsatz']}, {m['temp']}")
    z += ["", "## Seiten", "",
          "- [Shop](shop.html): Artikel mit Farbwahl, teils mit Wunschtext",
          "- [Druckservice](druckservice.html): eigene Datei drucken lassen",
          "- [Materialien](materialien.html): PLA, PETG, ABS und TPU im Vergleich",
          "- [Fragen und Antworten](faq.html)",
          "- [Versand und Zahlung](versand.html)",
          "- [Über uns](ueber-uns.html)",
          "- [Kontakt und Anfrage](kontakt.html)", ""]
    if SITE:  # Links absolut machen, wenn die Domain bekannt ist
        import re
        z = [re.sub(r"\]\(([^)]+)\)", lambda m: f"]({SITE}/{m.group(1)})", l) for l in z]
    return "\n".join(z)


def teilen_bild():
    """1200 x 630 Vorschaubild für Link-Vorschauen: Hero-Foto, Wortmarke, Zeile."""
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    import tempfile
    fonts = os.path.join(ROOT, "assets", "fonts")
    def ttf(woff, **loc):
        f = TTFont(os.path.join(fonts, woff)); f.flavor = None
        p = tempfile.mktemp(suffix=".ttf"); f.save(p); return p
    abril = ttf("AbrilFatface.woff2"); hanken = ttf("HankenGrotesk.woff2")
    W, H = 1200, 630
    base = Image.new("RGB", (W, H), (31, 77, 58))
    hero = Image.open(os.path.join(ROOT, "assets", "img", "hero.webp")).convert("RGB").resize((630, 630))
    base.paste(hero, (570, 0))
    d = ImageDraw.Draw(base)
    d.text((60, 200), "Schichtatelier", font=ImageFont.truetype(abril, 68), fill=(241, 237, 228))
    d.rectangle((60, 308, 300, 313), fill=(226, 174, 124))
    d.text((60, 340), "3D-Druck aus Celle", font=ImageFont.truetype(hanken, 40), fill=(226, 174, 124))
    d.text((60, 405), "Deko, Geschenke und Teile", font=ImageFont.truetype(hanken, 28)); d.text((60, 442), "nach eigener Datei", font=ImageFont.truetype(hanken, 28), fill=(205, 220, 211))
    base.save(os.path.join(ROOT, "assets", "img", "teilen.jpg"), "JPEG", quality=84, optimize=True)
