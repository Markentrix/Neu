"""Erzeugt alle HTML-Seiten, produkte.js, sitemap.xml, robots.txt und site.webmanifest in website-fertig/.
Aufruf: python3 build/build.py"""
import os, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(__file__))
import config as C
from produkte import PRODUKTE, FARBEN, KATEGORIEN, VERSAND_PAUSCHALE, VERSANDFREI_AB
from materialien import MATERIALIEN, VERGLEICH, FAQ

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "website-fertig"))
E = html.escape
EUR = lambda n: ("%.2f" % n).replace(".", ",") + " €"
TEL_HREF = "tel:" + "".join(ch for ch in C.TELEFON if ch.isdigit() or ch == "+")
TODAY = datetime.date.today().isoformat()

SVG_CART = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h2l2.4 12.4a2 2 0 0 0 2 1.6h8.2a2 2 0 0 0 2-1.6L21 8H6"/><circle cx="9" cy="21" r="1.2"/><circle cx="18" cy="21" r="1.2"/></svg>'
SVG_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
SVG_LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#171a1f"/><rect x="14" y="40" width="36" height="8" rx="3" fill="#e8561f"/><rect x="18" y="29" width="28" height="8" rx="3" fill="#ff8a55"/><rect x="22" y="18" width="20" height="8" rx="3" fill="#ffb08c"/><path d="M32 8v8" stroke="#f1efe9" stroke-width="3" stroke-linecap="round"/></svg>'
SVG_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
ICONS = {
    "layer": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="m2 13 10 5 10-5"/><path d="m2 18 10 5 10-5"/></svg>',
    "leaf": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 20c0-9 5-14 15-15-1 10-6 15-15 15z"/><path d="M5 20c3-5 6-8 10-11"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
    "pen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4 20 4-1 11-11-3-3L5 16l-1 4z"/><path d="m14 7 3 3"/></svg>',
}


def head(title, desc, rel, canonical_name, extra=""):
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#f6f4ef">
<link rel="icon" href="{rel}favicon.ico" sizes="any">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<link rel="manifest" href="{rel}site.webmanifest">
<link rel="preload" href="{rel}assets/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{rel}assets/fonts/Inter-Bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{rel}assets/css/style.css">
{extra}</head>
<body data-root="{rel}">
<a class="skip" href="#main">Zum Inhalt springen</a>
"""


def header(rel, current=""):
    def nav(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{rel}{href}"{cur}>{label}</a>'
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="logo" href="{rel}index.html" aria-label="{E(C.MARKE)} Startseite">{SVG_LOGO}<span>{E(C.MARKE)}</span></a>
    <button class="menu-btn" type="button" aria-label="Menü öffnen" aria-expanded="false" aria-controls="hauptmenu">{SVG_MENU}</button>
    <nav class="nav" id="hauptmenu" aria-label="Hauptmenü">
      {nav("shop.html", "Shop", "shop")}
      {nav("druckservice.html", "Druckservice", "service")}
      {nav("materialien.html", "Materialien", "material")}
      {nav("faq.html", "FAQ", "faq")}
      {nav("ueber-uns.html", "Über uns", "ueber")}
    </nav>
    <a class="cart-link" href="{rel}warenkorb.html" aria-label="Warenkorb">{SVG_CART}<span class="cart-badge" aria-live="polite"></span></a>
  </div>
</header>
<main id="main">
"""


def footer(rel):
    return f"""</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="trust-strip footer-trust"><span>{SVG_CHECK} Versandfrei ab {EUR(VERSANDFREI_AB)}</span><span>{SVG_CHECK} 14 Tage Rückgaberecht</span><span>{SVG_CHECK} PayPal-Käuferschutz</span><span>{SVG_CHECK} Nachdruck-Garantie</span><span>{SVG_CHECK} Gefertigt in Deutschland</span></div>
    <div class="cols">
      <div>
        <a class="logo" href="{rel}index.html">{SVG_LOGO}<span>{E(C.MARKE)}</span></a>
        <p style="margin-top:12px">{E(C.CLAIM)}. Jedes Teil wird nach Ihrer Bestellung in unserer Werkstatt gedruckt, geprüft und verpackt.</p>
        <p><a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a><br><a href="{TEL_HREF}">{E(C.TELEFON)}</a></p>
      </div>
      <div>
        <h2>Shop</h2>
        <ul>
          <li><a href="{rel}shop.html">Alle Artikel</a></li>
          <li><a href="{rel}druckservice.html">Druckservice</a></li>
          <li><a href="{rel}kontakt.html">Anfrage stellen</a></li>
          <li><a href="{rel}versand.html">Versand &amp; Zahlung</a></li>
          <li><a href="{rel}faq.html">Fragen &amp; Antworten</a></li>
          <li><a href="{rel}ueber-uns.html">Über uns</a></li>
        </ul>
      </div>
      <div>
        <h2>Materialien</h2>
        <ul>
          <li><a href="{rel}materialien.html">Übersicht &amp; Vergleich</a></li>
          {"".join(f'<li><a href="{rel}material/{m["id"]}.html">{E(m["titel"])}</a></li>' for m in MATERIALIEN)}
        </ul>
      </div>
      <div>
        <h2>Rechtliches</h2>
        <ul>
          <li><a href="{rel}impressum.html">Impressum</a></li>
          <li><a href="{rel}datenschutz.html">Datenschutz</a></li>
          <li><a href="{rel}agb.html">AGB</a></li>
          <li><a href="{rel}widerruf.html">Widerrufsrecht</a></li>
          <li><span data-mk="cookies"></span></li>
        </ul>
      </div>
    </div>
    <div class="bottom">
      <span>© {datetime.date.today().year} {E(C.FIRMA)}</span>
      <span>Gehostet bei Markentrix · Keine Tracking-Cookies</span>
    </div>
  </div>
</footer>
<script src="{rel}assets/js/produkte.js"></script>
<script src="{rel}assets/js/shop.js"></script>
</body>
</html>
"""


def page(name, title, desc, body, current="", rel="", extra=""):
    out = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(head(title, desc, rel, name, extra) + header(rel, current) + body + footer(rel))


def card(p, rel, pos, h="h3"):
    tags = ""
    if "bestseller" in p["tags"]: tags = '<span class="badge badge-accent">Bestseller</span>'
    elif "neu" in p["tags"]: tags = '<span class="badge">Neu</span>'
    elif "personalisiert" in p["tags"]: tags = '<span class="badge">Personalisierbar</span>'
    return f"""<article class="card" data-kat="{p['kat']}" data-tags="{' '.join(p['tags'])}" data-preis="{p['preis']}" data-name="{E(p['name'])}" data-pos="{pos}">
  <a class="card-img" href="{rel}produkt/{p['id']}.html" tabindex="-1" aria-hidden="true"><img src="{rel}assets/img/produkte/{p['id']}.webp" width="800" height="600" alt="" loading="lazy"></a>
  <div class="card-body">
    <span class="card-cat">{E(KATEGORIEN[p['kat']])}</span>
    <{h}><a href="{rel}produkt/{p['id']}.html">{E(p['name'])}</a></{h}>
    <p class="small muted" style="margin:0">{E(p['kurz'])}</p>
    <div class="price">{EUR(p['preis'])} {tags}</div>
    {'<a class="btn btn-primary" href="' + rel + 'produkt/' + p['id'] + '.html">Jetzt gestalten</a>' if p.get('text') else '<button class="btn btn-primary" type="button" data-add="' + p['id'] + '">In den Warenkorb</button>'}
    <a class="card-more" href="{rel}produkt/{p['id']}.html">Details ansehen</a>
  </div>
</article>"""


# ---------------------------------------------------------------- Startseite
def build_index():
    featured = [p for p in PRODUKTE if "bestseller" in p["tags"]][:4]
    cards = "\n".join(card(p, "", i) for i, p in enumerate(featured))
    cats = "\n".join(f'<a class="chip" href="shop.html#{k}">{E(v)}</a>' for k, v in KATEGORIEN.items())
    hero_art = """<svg viewBox="0 0 400 400" role="img" aria-label="Stilisierter 3D-Drucker, der schichtweise ein orangefarbenes Objekt aufbaut">
      <rect x="40" y="340" width="320" height="22" rx="8" fill="#171a1f"/>
      <rect x="60" y="60" width="14" height="290" rx="4" fill="#2b2e34"/><rect x="326" y="60" width="14" height="290" rx="4" fill="#2b2e34"/>
      <rect x="60" y="48" width="280" height="16" rx="6" fill="#2b2e34"/>
      <rect x="60" y="150" width="280" height="10" rx="4" fill="#4a505b"/>
      <rect x="175" y="130" width="50" height="44" rx="6" fill="#4a505b"/><path d="M190 174 l10 18 l10 -18z" fill="#e8561f"/>
      <rect x="80" y="318" width="240" height="22" rx="6" fill="#8a8f99"/>
      <g fill="#e8561f">
        <rect x="150" y="300" width="100" height="18" rx="4"/><rect x="155" y="282" width="90" height="18" rx="4" opacity=".92"/>
        <rect x="160" y="264" width="80" height="18" rx="4" opacity=".84"/><rect x="165" y="246" width="70" height="18" rx="4" opacity=".76"/>
        <rect x="170" y="228" width="60" height="18" rx="4" opacity=".68"/><rect x="175" y="210" width="50" height="14" rx="4" opacity=".55"/>
      </g>
      <path d="M200 192 v18" stroke="#ff8a55" stroke-width="3" stroke-linecap="round"/>
      <circle cx="200" cy="192" r="4" fill="#ffb08c"/>
    </svg>"""
    body = f"""<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">{E(C.CLAIM)}</span>
      <h1>Dinge, die es so nur für Sie gibt.</h1>
      <p class="lead">Pflanztöpfe, Halter, Organizer und persönliche Geschenke aus dem 3D-Drucker. Jedes Stück wird erst nach Ihrer Bestellung gedruckt, in Ihrer Farbe, auf Wunsch mit Ihrem Namen. In wenigen Tagen bei Ihnen.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="shop.html">Zum Shop</a>
        <a class="btn btn-ghost" href="druckservice.html">Druckservice für eigene Dateien</a>
      </div>
      <div class="hero-facts">
        <span>{SVG_CHECK} Versandfrei ab {EUR(VERSANDFREI_AB)}</span>
        <span>{SVG_CHECK} 14 Tage Rückgaberecht</span>
        <span>{SVG_CHECK} Nachdruck-Garantie</span>
        <span>{SVG_CHECK} 7 Farben zur Wahl</span>
      </div>
    </div>
    <div class="hero-art">{hero_art}</div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <div class="filterbar" aria-label="Kategorien">{cats}</div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Beliebt</span>
    <h2>Das bestellen unsere Kunden am häufigsten</h2>
    <div class="grid">{cards}</div>
    <p style="margin-top:24px"><a class="btn btn-ghost" href="shop.html">Alle {len(PRODUKTE)} Artikel ansehen</a> <a class="btn btn-ghost" href="shop.html#personalisiert">Geschenke mit Namen</a></p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <span class="eyebrow">Warum Schichtwerk</span>
    <h2>Gedruckt, wenn Sie bestellen. Nicht vorher.</h2>
    <div class="feature-grid">
      <div class="feature">{ICONS['layer']}<h3>Auf Bestellung gefertigt</h3><p class="muted">Kein Lager, keine Überproduktion. Jedes Teil entsteht erst, wenn Sie es bestellen, in der Farbe, die Sie wählen.</p></div>
      <div class="feature">{ICONS['leaf']}<h3>Pflanzenbasiertes Material</h3><p class="muted">Wir drucken mit PLA aus Maisstärke und Zuckerrohr. Für Bad, Küche und draußen nehmen wir wasserfestes PETG.</p></div>
      <div class="feature">{ICONS['pen']}<h3>Mit Wunschtext</h3><p class="muted">Schlüsselanhänger, Namensschilder und Lampen mit Ihrem Text oder Foto. Die Vorschau stimmen wir vor dem Druck mit Ihnen ab.</p></div>
      <div class="feature">{ICONS['truck']}<h3>Schnell bei Ihnen</h3><p class="muted">Druck in {E(C.PRODUKTIONSZEIT)}, Versand mit DHL in {E(C.LIEFERZEIT)}. Ab {EUR(VERSANDFREI_AB)} Bestellwert versandkostenfrei.</p></div>
    </div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">So läuft es</span>
    <h2>In drei Schritten zum fertigen Teil</h2>
    <div class="steps">
      <div class="step"><h3>Aussuchen</h3><p class="muted">Artikel, Farbe und Menge wählen, bei personalisierten Teilen den Wunschtext eintragen, in den Warenkorb legen.</p></div>
      <div class="step"><h3>Bestellen</h3><p class="muted">Adresse und Zahlungsart angeben. Sie bekommen sofort eine Eingangsbestätigung mit Vorgangsnummer, dann die Rechnung mit Zahlungsdaten.</p></div>
      <div class="step"><h3>Drucken &amp; liefern</h3><p class="muted">Nach Zahlungseingang drucken wir Ihr Teil, prüfen es und schicken es los. Sie erhalten die Sendungsnummer per Mail.</p></div>
    </div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <div class="guarantee">
      <div class="guarantee-badge">{SVG_CHECK}</div>
      <div>
        <h2>Unsere Nachdruck-Garantie</h2>
        <p class="muted" style="margin:0">Kommt ein Teil beschädigt an oder passt nicht wie beschrieben, schicken Sie uns ein Foto. Wir drucken kostenlos nach, ohne Rücksendung, ohne Diskussion. Dazu das gesetzliche Rückgaberecht von 14 Tagen für alle Artikel ohne Personalisierung.</p>
      </div>
    </div>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Kundenstimmen</span>
    <h2>Das sagen unsere Kunden</h2>
    <div class="reviews-box">
      <div data-mk="bewertungen"></div>
      <p class="reviews-fallback">Bewertungen werden über Google geladen. Sie haben bei uns bestellt? Wir freuen uns über Ihre Rückmeldung per <a href="mailto:{E(C.EMAIL)}">E-Mail</a>.</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cta-band">
      <div><h2>Sie haben eine eigene Datei?</h2><p style="margin:6px 0 0;opacity:.85">Wir drucken auch Ihre STL- oder 3MF-Datei: Ersatzteile, Prototypen, Vereinslogos. Anfrage mit Maßen und Stückzahl genügt.</p></div>
      <div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-primary" href="kontakt.html">Anfrage stellen</a><a class="btn btn-ghost" style="border-color:currentColor;color:inherit" href="materialien.html">Materialien vergleichen</a></div>
    </div>
  </div>
</section>
"""
    page("index.html", f"{C.MARKE} · 3D-gedruckte Alltagshelfer kaufen", "Online-Shop für 3D-gedruckte Pflanztöpfe, Halter, Organizer und personalisierte Geschenke. Auf Bestellung gedruckt, pflanzenbasiertes Material, versandfrei ab 49 €.", body, "index")


# ---------------------------------------------------------------- Shop
def build_shop():
    chips = '<button class="chip" type="button" data-kat="alle" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" type="button" data-kat="{k}" aria-pressed="false">{E(v)}</button>' for k, v in KATEGORIEN.items()) + '<button class="chip" type="button" data-kat="personalisiert" aria-pressed="false">Mit Wunschtext</button>'
    ordered = sorted(PRODUKTE, key=lambda p: (0 if "bestseller" in p["tags"] else 1 if "neu" in p["tags"] else 2))
    cards = "\n".join(card(p, "", i, "h2") for i, p in enumerate(ordered))
    body = f"""<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Shop</span>
    <h1>Alle Artikel</h1>
    <p class="muted" style="max-width:60ch">{len(PRODUKTE)} Artikel, jeder wird erst nach Ihrer Bestellung gedruckt. Endpreise, Versand {EUR(VERSAND_PAUSCHALE)}, ab {EUR(VERSANDFREI_AB)} kostenlos. 14 Tage Rückgabe.</p>
    <div class="trust-strip"><span>{SVG_CHECK} Versandfrei ab {EUR(VERSANDFREI_AB)}</span><span>{SVG_CHECK} 14 Tage Rückgaberecht</span><span>{SVG_CHECK} PayPal-Käuferschutz</span><span>{SVG_CHECK} Nachdruck-Garantie</span></div>
    <div class="filterbar" role="group" aria-label="Nach Kategorie filtern">
      {chips}
      <label class="sr-only" for="sortierung">Sortierung</label>
      <select id="sortierung"><option value="standard">Empfohlen</option><option value="preis-auf">Preis aufsteigend</option><option value="preis-ab">Preis absteigend</option><option value="name">Name A–Z</option></select>
    </div>
    <p class="small muted" id="treffer" aria-live="polite">{len(PRODUKTE)} Artikel</p>
    <div class="grid" id="shop-grid">{cards}</div>
  </div>
</section>
"""
    page("shop.html", f"Shop · Alle 3D-Druck-Artikel · {C.MARKE}", "Alle 3D-gedruckten Artikel von Schichtwerk: Wohnen, Schreibtisch, Küche, Gadgets, Spiel und Garten. Farbe wählen, bestellen, in wenigen Tagen geliefert.", body, "shop")


# ---------------------------------------------------------------- Produktseiten
def build_products():
    for i, p in enumerate(PRODUKTE):
        rel = "../"
        sw = ""
        for j, f in enumerate(p["farben"]):
            name, hexc = FARBEN[f]
            sw += f'<label class="swatch"><input type="radio" name="farbe" value="{f}"{" checked" if j == 0 else ""}><span><i style="background:{hexc}"></i>{E(name)}</span></label>'
        textfield = ""
        if p.get("text"):
            textfield = f"""<div class="field"><label for="wunschtext">{E(p['textlabel'])}</label><input type="text" id="wunschtext" name="wunschtext" maxlength="80" required autocomplete="off"><p class="msg">Bitte den Wunschtext eintragen.</p></div>"""
        related = [q for q in PRODUKTE if q["kat"] == p["kat"] and q["id"] != p["id"]][:3]
        if len(related) < 3:
            related += [q for q in PRODUKTE if q["id"] != p["id"] and q not in related][:3 - len(related)]
        rel_cards = "\n".join(card(q, rel, k) for k, q in enumerate(related))
        widerruf = ('<p class="small muted">Personalisierter Artikel: Nach Ihrer Freigabe des Textes ist der Kauf vom Widerruf ausgenommen (§ 312g Abs. 2 Nr. 1 BGB). <a href="../widerruf.html">Mehr dazu</a>.</p>' if p.get("text") else "")
        body = f"""<section class="section-tight">
  <div class="wrap">
    <nav aria-label="Pfad" class="small muted" style="margin-bottom:16px"><a href="../index.html">Start</a> › <a href="../shop.html">Shop</a> › <a href="../shop.html#{p['kat']}">{E(KATEGORIEN[p['kat']])}</a></nav>
    <div class="product">
      <div class="product-media"><img src="../assets/img/produkte/{p['id']}.webp" width="800" height="600" alt="{E(p['name'])}, Illustration in {E(FARBEN[p['farben'][0]][0])}"></div>
      <div class="product-info">
        <span class="eyebrow">{E(KATEGORIEN[p['kat']])}</span>
        <h1>{E(p['name'])}</h1>
        <p class="price">{EUR(p['preis'])} <small>{'inkl. MwSt.' if not C.KLEINUNTERNEHMER else 'Endpreis, keine Umsatzsteuer nach § 19 UStG'}, zzgl. <a href="../versand.html">Versand</a></small></p>
        <p>{E(p['kurz'])}</p>
        <form id="kaufen" data-id="{p['id']}" novalidate>
          <fieldset style="border:0;padding:0;margin:0 0 14px"><legend style="font-weight:600;margin-bottom:8px">Farbe</legend><div class="swatches">{sw}</div></fieldset>
          {textfield}
          <div class="buyrow">
            <span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" id="menge" name="menge" min="1" max="20" value="1" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span>
            <button class="btn btn-primary" type="submit">In den Warenkorb</button>
          </div>
          <p class="added" role="status">Liegt im Warenkorb. <a href="../warenkorb.html">Zum Warenkorb</a> oder <a href="../shop.html">weiter stöbern</a>.</p>
        </form>
        <p class="delivery" data-delivery>Bestellen Sie heute, Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>
        <div class="trust-list"><span>{SVG_CHECK} Versandfrei ab {EUR(VERSANDFREI_AB)}, sonst {EUR(VERSAND_PAUSCHALE)}</span><span>{SVG_CHECK} {'Personalisiert für Sie gefertigt, Vorschau vor dem Druck' if p.get('text') else '14 Tage Rückgaberecht'}</span><span>{SVG_CHECK} PayPal-Käuferschutz oder Überweisung</span><span>{SVG_CHECK} Nachdruck-Garantie bei Transportschäden</span></div>
        <dl class="specs">
          <dt>Maße</dt><dd>{E(p['masse'])}</dd>
          <dt>Material</dt><dd>{E(p['material'])}</dd>
          <dt>Gewicht</dt><dd>{E(p['gewicht'])}</dd>
          <dt>Fertigung</dt><dd>Druck in {E(C.PRODUKTIONSZEIT)}, dann Versand</dd>
        </dl>
        <h2 style="font-size:1.15rem">Beschreibung</h2>
        <p>{E(p['lang'])}</p>
        <p class="small muted">Hinweis: 3D-gedruckte Teile zeigen feine Schichtlinien, das ist Teil des Verfahrens. Farben können je nach Filamentcharge leicht abweichen. Die Abbildung ist eine Illustration des Artikels.</p>
        {widerruf}
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Oft zusammen bestellt</h2>
    <p class="muted">Ab {EUR(VERSANDFREI_AB)} liefern wir versandkostenfrei. Alles aus einer Bestellung wird zusammen gedruckt und verschickt.</p>
    <div class="grid">{rel_cards}</div>
  </div>
</section>
<div class="sticky-buy" aria-hidden="true"><span class="sticky-price">{EUR(p['preis'])}</span><button class="btn btn-primary" type="button" data-sticky-buy>In den Warenkorb</button></div>
"""
        title = f"{p['name']} · {C.MARKE}"
        if len(title) > 60:
            title = p["name"][:57].rstrip() + "…"
        page(f"produkt/{p['id']}.html", title, p["kurz"][:155], body, "shop", rel)


# ---------------------------------------------------------------- Warenkorb
def build_cart():
    body = f"""<section class="section-tight" id="warenkorb">
  <div class="wrap">
    <ol class="checkout-steps" aria-label="Bestellschritte"><li aria-current="step">Warenkorb</li><li>Adresse &amp; Zahlung</li><li>Bestätigung per E-Mail</li></ol>
    <h1>Ihre Bestellung</h1>
    <div class="empty" id="cart-empty"><p>Ihr Warenkorb ist leer.</p><a class="btn btn-primary" href="shop.html">Zum Shop</a></div>
    <div class="cart-layout">
      <div>
        <div class="ship-progress" id="ship-progress" hidden><div class="ship-bar"><span id="ship-fill"></span></div><p class="small" id="ship-text"></p></div>
        <div class="cart-list" id="cart-list" aria-live="polite"></div>
        <div id="cross-sell" hidden><h2 style="font-size:1.1rem;margin-top:28px">Dazu passt</h2><div class="grid grid-small" id="cross-sell-grid"></div></div>
        <form class="form" id="bestellformular" style="margin-top:32px" hidden>
          <h2>Lieferadresse</h2>
          <p class="muted small">Sie bestellen verbindlich. Der Vertrag kommt mit unserer Bestätigung per E-Mail zustande, danach erhalten Sie die Rechnung mit Zahlungsdaten. Gedruckt wird nach Zahlungseingang.</p>
          <div class="alert" role="alert"></div>
          <div class="field"><label for="b-name">Vor- und Nachname</label><input type="text" id="b-name" name="name" required autocomplete="name" data-err="Bitte Ihren Namen eintragen."><p class="msg"></p></div>
          <div class="row">
            <div class="field"><label for="b-email">E-Mail <span class="opt">(für Bestätigung und Rechnung)</span></label><input type="email" id="b-email" name="email" required autocomplete="email" data-err="Bitte Ihre E-Mail-Adresse eintragen."><p class="msg"></p></div>
            <div class="field"><label for="b-tel">Telefon <span class="opt">(optional, für Rückfragen)</span></label><input type="tel" id="b-tel" name="telefon" autocomplete="tel"><p class="msg"></p></div>
          </div>
          <div class="field"><label for="b-strasse">Straße und Hausnummer</label><input type="text" id="b-strasse" name="strasse" required autocomplete="street-address" data-err="Bitte die Straße eintragen."><p class="msg"></p></div>
          <div class="row">
            <div class="field"><label for="b-plz">PLZ</label><input type="text" id="b-plz" name="plz" required inputmode="numeric" autocomplete="postal-code" data-err="Bitte die Postleitzahl eintragen."><p class="msg"></p></div>
            <div class="field"><label for="b-ort">Ort</label><input type="text" id="b-ort" name="ort" required autocomplete="address-level2" data-err="Bitte den Ort eintragen."><p class="msg"></p></div>
          </div>
          <fieldset style="border:0;padding:0;margin:0"><legend style="font-weight:600;margin-bottom:8px">Zahlungsart</legend>
            <label class="check"><input type="radio" name="zahlungsart" value="paypal" checked> PayPal (Zahlungslink kommt mit der Bestätigung)</label>
            <label class="check"><input type="radio" name="zahlungsart" value="ueberweisung"> Vorkasse per Überweisung (Bankdaten kommen mit der Rechnung)</label>
          </fieldset>
          <div class="field"><label for="b-anm">Anmerkung <span class="opt">(optional)</span></label><textarea id="b-anm" name="anmerkung" rows="3"></textarea><p class="msg"></p></div>
          <div class="field hp" aria-hidden="true"><label for="b-web">Website</label><input type="text" id="b-web" name="website" tabindex="-1" autocomplete="off"></div>
          <div class="field"><label class="check"><input type="checkbox" name="agb" value="ja" required data-err="Bitte die AGB und die Widerrufsbelehrung bestätigen."><span>Ich habe die <a href="agb.html">AGB</a> und die <a href="widerruf.html">Widerrufsbelehrung</a> gelesen und akzeptiere sie.</span></label><p class="msg"></p></div>
          <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir die Bestellung nicht bearbeiten."><span>Ich bin einverstanden, dass meine Angaben zur Bearbeitung der Bestellung gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
          <button class="btn btn-primary btn-block" type="submit">Zahlungspflichtig bestellen</button>
          <div class="trust-list"><span>{SVG_CHECK} Sie zahlen erst nach unserer Bestätigung</span><span>{SVG_CHECK} PayPal-Käuferschutz oder Überweisung</span><span>{SVG_CHECK} 14 Tage Rückgaberecht, Nachdruck-Garantie</span></div>
          <p class="small muted">Klappt das Senden nicht? <a id="cart-mail" href="mailto:{E(C.EMAIL)}">Bestellung per E-Mail schicken</a> oder anrufen: <a href="{TEL_HREF}">{E(C.TELEFON)}</a>.</p>
        </form>
      </div>
      <div class="summary" id="cart-summary" hidden>
        <h2 style="font-size:1.1rem">Zusammenfassung</h2>
        <div class="line"><span>Zwischensumme</span><strong id="s-zwischen">0,00 €</strong></div>
        <div class="line"><span>Versand ({E(C.VERSANDLAND)})</span><strong id="s-versand">0,00 €</strong></div>
        <div class="line total"><span>Gesamt</span><span id="s-gesamt">0,00 €</span></div>
        <p class="small muted" id="s-hint"></p>
        <p class="small" data-delivery>Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>
        <p class="small muted">{'Keine Umsatzsteuer nach § 19 UStG.' if C.KLEINUNTERNEHMER else 'Alle Preise inkl. gesetzlicher MwSt.'} Produktion {E(C.PRODUKTIONSZEIT)} plus Versand {E(C.LIEFERZEIT)}.</p>
        <a class="btn btn-ghost btn-block" href="shop.html">Weiter einkaufen</a>
      </div>
    </div>
  </div>
</section>
"""
    page("warenkorb.html", f"Warenkorb · {C.MARKE}", "Warenkorb und Bestellung bei Schichtwerk: Artikel prüfen, Lieferadresse angeben, per PayPal oder Überweisung bezahlen.", body, "", "", '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- Kontakt / eigenes Modell
def build_contact():
    body = f"""<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Anfrage</span>
    <h1>Eigenes Modell drucken lassen</h1>
    <div class="contact-grid">
      <div>
        <p class="muted" style="max-width:60ch">Sie haben eine STL-, 3MF- oder STEP-Datei, ein kaputtes Ersatzteil oder nur eine Idee? Beschreiben Sie kurz, was Sie brauchen. Wir melden uns innerhalb eines Werktags mit Preis und Lieferzeit. Die Datei schicken Sie uns dann per E-Mail, die Adresse steht in unserer Antwort.</p>
        <form class="form" id="kontaktformular">
          <div class="alert" role="alert"></div>
          <div class="row">
            <div class="field"><label for="k-name">Name</label><input type="text" id="k-name" name="name" required autocomplete="name" data-err="Bitte Ihren Namen eintragen."><p class="msg"></p></div>
            <div class="field"><label for="k-email">E-Mail</label><input type="email" id="k-email" name="email" required autocomplete="email" data-err="Bitte Ihre E-Mail-Adresse eintragen."><p class="msg"></p></div>
          </div>
          <div class="row">
            <div class="field"><label for="k-tel">Telefon <span class="opt">(optional)</span></label><input type="tel" id="k-tel" name="telefon" autocomplete="tel"><p class="msg"></p></div>
            <div class="field"><label for="k-art">Worum geht es?</label><select id="k-art" name="projekt"><option>Eigene Datei drucken</option><option>Ersatzteil nachbauen</option><option>Größere Stückzahl eines Shop-Artikels</option><option>Frage zu einer Bestellung</option><option>Etwas anderes</option></select><p class="msg"></p></div>
          </div>
          <div class="row">
            <div class="field"><label for="k-stueck">Stückzahl <span class="opt">(optional)</span></label><input type="number" id="k-stueck" name="stueckzahl" min="1" max="999"><p class="msg"></p></div>
            <div class="field"><label for="k-mat">Material-Wunsch <span class="opt">(optional)</span></label><select id="k-mat" name="material"><option>Egal, bitte empfehlen</option><option>PLA (Standard, biobasiert)</option><option>PETG (wasserfest, belastbar)</option><option>ABS (hitzefest, schleifbar)</option><option>ASA (wetterfest, für draußen)</option><option>TPU (flexibel)</option></select><p class="msg"></p></div>
          </div>
          <div class="field"><label for="k-msg">Beschreibung <span class="opt">(Maße, Einsatzzweck, Farbe)</span></label><textarea id="k-msg" name="nachricht" required data-err="Bitte beschreiben Sie kurz Ihr Vorhaben."></textarea><p class="msg"></p></div>
          <div class="field hp" aria-hidden="true"><label for="k-web">Website</label><input type="text" id="k-web" name="website" tabindex="-1" autocomplete="off"></div>
          <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir die Anfrage nicht bearbeiten."><span>Ich bin einverstanden, dass meine Angaben zur Bearbeitung der Anfrage gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
          <button class="btn btn-primary" type="submit">Anfrage senden</button>
        </form>
      </div>
      <div>
        <div class="contact-card">
          <h2 style="font-size:1.1rem">Direkt erreichen</h2>
          <p><strong>E-Mail</strong><br><a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a></p>
          <p><strong>Telefon</strong><br><a href="{TEL_HREF}">{E(C.TELEFON)}</a></p>
          <p class="small muted">Antwort meist innerhalb eines Werktags.</p>
        </div>
        <div class="contact-card" style="margin-top:16px">
          <h2 style="font-size:1.1rem">Was wir drucken können</h2>
          <ul class="small" style="padding-left:1.2em;margin:0">
            <li>Bauraum bis 25 × 25 × 25 cm, größere Teile in Segmenten</li>
            <li><a href="materialien.html">PLA, PETG, ABS, ASA, TPU</a>; Schichthöhe 0,12 bis 0,28 mm</li>
            <li>Zwei Farben in einem Teil (Schrift, Logos)</li>
            <li>Dateiformate STL, 3MF, STEP, OBJ</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>
"""
    page("kontakt.html", f"Eigenes Modell drucken lassen · {C.MARKE}", "3D-Druck-Service: eigene STL-Datei, Ersatzteil oder Kleinserie anfragen. Antwort mit Preis und Lieferzeit innerhalb eines Werktags.", body, "kontakt")


# ---------------------------------------------------------------- Über uns
def build_about():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Über uns</span>
    <h1>Eine kleine Werkstatt, ein paar Drucker, viel Geduld.</h1>
    <p class="lead">{E(C.MARKE)} ist eine Ein-Personen-Manufaktur für 3D-gedruckte Alltagsgegenstände. Was Sie hier kaufen, wird nicht aus einem Lager geholt, sondern nach Ihrer Bestellung auf unseren Druckern gefertigt.</p>
    <h2>Wie wir arbeiten</h2>
    <p>Jedes Modell im Shop haben wir selbst entworfen oder sorgfältig angepasst, viele Male probegedruckt und im Alltag getestet. Erst wenn ein Teil stabil ist, sauber vom Druckbett kommt und sich gut anfühlt, landet es im Shop. Wir drucken mit 0,2 mm Schichthöhe, bei Sichtteilen feiner, und prüfen jedes Stück von Hand, bevor es in den Karton geht.</p>
    <h2>Material</h2>
    <p>Standardmaterial ist PLA, ein Kunststoff aus Maisstärke und Zuckerrohr. Er ist formstabil, geruchsneutral und fühlt sich hochwertig an. Für Bad, Küche und draußen verwenden wir PETG, das Feuchtigkeit und Wärme besser verträgt. Unsere Filamente beziehen wir von europäischen Herstellern, Reste und Fehldrucke sammeln wir zum Recycling.</p>
    <h2>Verpackung und Versand</h2>
    <p>Wir verschicken in Kartons aus Altpapier, gepolstert mit Papier statt Plastik. Der Versand läuft über DHL, in der Regel {E(C.LIEFERZEIT)} nach dem Druck.</p>
    <h2>Fragen, Wünsche, Sonderanfertigungen</h2>
    <p>Schreiben Sie uns an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>, rufen Sie an unter <a href="{TEL_HREF}">{E(C.TELEFON)}</a> oder nutzen Sie das <a href="kontakt.html">Anfrageformular</a>. Für eigene Dateien und Ersatzteile machen wir Ihnen gern ein Angebot.</p>
  </div>
</section>
"""
    page("ueber-uns.html", f"Über uns · {C.MARKE}", "Schichtwerk ist eine kleine 3D-Druck-Manufaktur: eigene Entwürfe, pflanzenbasiertes Material, Fertigung auf Bestellung und plastikfreie Verpackung.", body, "ueber")


# ---------------------------------------------------------------- Versand & Zahlung
def build_shipping():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Service</span>
    <h1>Versand und Zahlung</h1>
    <h2>Versandkosten</h2>
    <table>
      <tr><th>Lieferland</th><th>Kosten</th><th>Versandfrei ab</th></tr>
      <tr><td>{E(C.VERSANDLAND)}</td><td>{EUR(VERSAND_PAUSCHALE)} pro Bestellung</td><td>{EUR(VERSANDFREI_AB)} Bestellwert</td></tr>
    </table>
    <p>Wir versenden mit DHL als Päckchen oder Paket. Die Sendungsnummer bekommen Sie per E-Mail, sobald das Paket abgegeben ist. Lieferungen in andere Länder sind auf Anfrage möglich, schreiben Sie uns vorher.</p>
    <h2>Lieferzeit</h2>
    <p>Alle Artikel werden nach Bestellung gedruckt. Rechnen Sie mit {E(C.PRODUKTIONSZEIT)} Produktion nach Zahlungseingang plus {E(C.LIEFERZEIT)} Versand. Bei personalisierten Artikeln stimmen wir den Text oder das Motiv vorher mit Ihnen ab, die Produktionszeit beginnt mit Ihrer Freigabe.</p>
    <h2>Zahlungsarten</h2>
    <ul>
      <li><strong>PayPal:</strong> Mit der Bestellbestätigung erhalten Sie einen PayPal-Zahlungslink über den Gesamtbetrag. Käuferschutz von PayPal inklusive.</li>
      <li><strong>Vorkasse per Überweisung:</strong> Die Bankverbindung steht auf der Rechnung, die Sie mit der Bestätigung bekommen. Nach Zahlungseingang beginnt der Druck.</li>
    </ul>
    <div class="notice">Wir speichern keine Zahlungsdaten auf dieser Website. Die Zahlung läuft direkt über PayPal oder Ihre Bank.</div>
    <h2>Rückgabe</h2>
    <p>Für Lagerartikel aus dem Shop gilt das gesetzliche <a href="widerruf.html">Widerrufsrecht</a> von 14 Tagen. Personalisierte Artikel mit Wunschtext oder eigenem Foto sind davon ausgenommen. Kommt ein Teil beschädigt an, schicken Sie uns bitte ein Foto an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>, wir drucken kostenlos nach.</p>
  </div>
</section>
"""
    page("versand.html", f"Versand und Zahlung · {C.MARKE}", f"Versandkosten {EUR(VERSAND_PAUSCHALE)}, versandfrei ab {EUR(VERSANDFREI_AB)}. Zahlung per PayPal oder Überweisung, Lieferzeit und Rückgabe bei Schichtwerk.", body, "versand")


# ---------------------------------------------------------------- AGB
def build_agb():
    ust = ("Alle Preise sind Endpreise. Als Kleinunternehmer im Sinne von § 19 UStG wird keine Umsatzsteuer berechnet und ausgewiesen." if C.KLEINUNTERNEHMER
           else "Alle Preise verstehen sich inklusive der gesetzlichen Umsatzsteuer.")
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Rechtliches</span>
    <h1>Allgemeine Geschäftsbedingungen</h1>
    <p class="muted">Stand: {datetime.date.today().strftime("%d.%m.%Y")}</p>
    <h2>1. Geltungsbereich</h2>
    <p>Diese AGB gelten für alle Bestellungen von Verbrauchern und Unternehmern über den Online-Shop von {E(C.FIRMA)}, {E(C.INHABER)}, {E(C.STRASSE)}, {E(C.PLZ_ORT)} (nachfolgend „wir“). Verbraucher ist jede natürliche Person, die ein Rechtsgeschäft zu Zwecken abschließt, die überwiegend weder ihrer gewerblichen noch ihrer selbständigen beruflichen Tätigkeit zugerechnet werden können.</p>
    <h2>2. Vertragsschluss</h2>
    <p>Die Darstellung der Artikel im Shop ist kein verbindliches Angebot, sondern eine Aufforderung zur Bestellung. Mit dem Klick auf „Zahlungspflichtig bestellen“ geben Sie ein verbindliches Angebot ab. Sie erhalten umgehend eine automatische Eingangsbestätigung mit Vorgangsnummer, diese ist noch keine Annahme. Der Vertrag kommt zustande, wenn wir Ihre Bestellung innerhalb von zwei Werktagen per E-Mail bestätigen und die Rechnung mit Zahlungsdaten übersenden. Vor dem Absenden können Sie Ihre Eingaben im Warenkorb jederzeit prüfen und ändern. Der Vertragstext wird von uns gespeichert und Ihnen mit der Bestätigung zugeschickt. Vertragssprache ist Deutsch.</p>
    <h2>3. Preise und Versandkosten</h2>
    <p>{ust} Zusätzlich fallen Versandkosten in Höhe von {EUR(VERSAND_PAUSCHALE)} pro Bestellung innerhalb von {E(C.VERSANDLAND)} an; ab einem Bestellwert von {EUR(VERSANDFREI_AB)} liefern wir versandkostenfrei. Lieferungen in andere Länder nur nach vorheriger Absprache.</p>
    <h2>4. Zahlung</h2>
    <p>Wir bieten Zahlung per PayPal (Zahlungslink) oder Vorkasse per Überweisung an. Der Rechnungsbetrag ist innerhalb von 7 Tagen nach Erhalt der Bestätigung fällig. Die Produktion beginnt nach Zahlungseingang. Geht innerhalb von 14 Tagen keine Zahlung ein, können wir vom Vertrag zurücktreten.</p>
    <h2>5. Fertigung und Lieferung</h2>
    <p>Alle Artikel werden nach Bestellung gefertigt. Die Produktionszeit beträgt in der Regel {E(C.PRODUKTIONSZEIT)} nach Zahlungseingang, bei personalisierten Artikeln nach Ihrer Freigabe des Textes oder Motivs. Hinzu kommt die Versandzeit von etwa {E(C.LIEFERZEIT)}. Die Lieferung erfolgt an die von Ihnen angegebene Adresse. Bei Verbrauchern geht die Gefahr des zufälligen Untergangs mit Übergabe der Ware an Sie über.</p>
    <h2>6. Beschaffenheit 3D-gedruckter Teile</h2>
    <p>Unsere Artikel entstehen im Schichtverfahren (FDM). Sichtbare Schichtlinien, leichte Farbabweichungen zwischen Filamentchargen und Maßtoleranzen von etwa ±0,3 mm sind verfahrensbedingt und stellen keinen Mangel dar. Die Produktbilder im Shop sind Illustrationen. Angaben zu Belastbarkeit und Temperaturbeständigkeit sind Richtwerte für den üblichen Gebrauch.</p>
    <h2>7. Personalisierte Artikel</h2>
    <p>Bei Artikeln mit Wunschtext oder eigenem Foto senden wir Ihnen vor dem Druck eine Vorschau zur Freigabe. Für Rechtschreibung und Inhalt Ihres Textes sind Sie verantwortlich. Wir drucken keine Inhalte, die Rechte Dritter verletzen oder strafbar sind. Personalisierte Artikel sind vom Widerrufsrecht ausgenommen (§ 312g Abs. 2 Nr. 1 BGB).</p>
    <h2>8. Widerrufsrecht</h2>
    <p>Verbrauchern steht ein Widerrufsrecht nach den Bestimmungen der <a href="widerruf.html">Widerrufsbelehrung</a> zu.</p>
    <h2>9. Eigentumsvorbehalt</h2>
    <p>Die Ware bleibt bis zur vollständigen Bezahlung unser Eigentum.</p>
    <h2>10. Gewährleistung</h2>
    <p>Es gelten die gesetzlichen Mängelhaftungsrechte. Kommt ein Artikel beschädigt an oder weist er einen Mangel auf, melden Sie sich bitte mit einem Foto bei uns, wir liefern kostenlos nach oder erstatten den Kaufpreis.</p>
    <h2>11. Haftung</h2>
    <p>Wir haften unbeschränkt für Vorsatz, grobe Fahrlässigkeit und bei Verletzung von Leben, Körper oder Gesundheit. Bei leicht fahrlässiger Verletzung wesentlicher Vertragspflichten ist die Haftung auf den vorhersehbaren, vertragstypischen Schaden begrenzt. Im Übrigen ist die Haftung ausgeschlossen. Die Haftung nach dem Produkthaftungsgesetz bleibt unberührt.</p>
    <h2>12. Streitbeilegung</h2>
    <p>Die EU-Kommission stellt eine Plattform zur Online-Streitbeilegung bereit (ec.europa.eu/consumers/odr). Wir sind nicht verpflichtet und nicht bereit, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
    <h2>13. Schlussbestimmungen</h2>
    <p>Es gilt deutsches Recht unter Ausschluss des UN-Kaufrechts. Gegenüber Verbrauchern gilt diese Rechtswahl nur, soweit der Schutz zwingender Vorschriften des Staates, in dem der Verbraucher seinen gewöhnlichen Aufenthalt hat, nicht entzogen wird.</p>
  </div>
</section>
"""
    page("agb.html", f"AGB · {C.MARKE}", "Allgemeine Geschäftsbedingungen des Schichtwerk-Online-Shops: Vertragsschluss, Preise, Zahlung, Lieferung, Gewährleistung und Besonderheiten 3D-gedruckter Teile.", body)


# ---------------------------------------------------------------- Widerruf
def build_widerruf():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Rechtliches</span>
    <h1>Widerrufsbelehrung</h1>
    <h2>Widerrufsrecht</h2>
    <p>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag, an dem Sie oder ein von Ihnen benannter Dritter, der nicht der Beförderer ist, die Waren in Besitz genommen haben bzw. hat.</p>
    <p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns ({E(C.FIRMA)}, {E(C.INHABER)}, {E(C.STRASSE)}, {E(C.PLZ_ORT)}, Telefon {E(C.TELEFON)}, E-Mail {E(C.EMAIL)}) mittels einer eindeutigen Erklärung (z. B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das unten stehende Formular verwenden, das ist jedoch nicht vorgeschrieben. Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.</p>
    <h2>Folgen des Widerrufs</h2>
    <p>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, einschließlich der Lieferkosten (mit Ausnahme der zusätzlichen Kosten, die sich daraus ergeben, dass Sie eine andere Art der Lieferung als die von uns angebotene, günstigste Standardlieferung gewählt haben), unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet. Wir können die Rückzahlung verweigern, bis wir die Waren wieder zurückerhalten haben oder bis Sie den Nachweis erbracht haben, dass Sie die Waren zurückgesandt haben, je nachdem, welches der frühere Zeitpunkt ist.</p>
    <p>Sie haben die Waren unverzüglich und in jedem Fall spätestens binnen vierzehn Tagen ab dem Tag, an dem Sie uns über den Widerruf dieses Vertrags unterrichten, an uns zurückzusenden oder zu übergeben. Die Frist ist gewahrt, wenn Sie die Waren vor Ablauf der Frist von vierzehn Tagen absenden. Sie tragen die unmittelbaren Kosten der Rücksendung der Waren. Sie müssen für einen etwaigen Wertverlust der Waren nur aufkommen, wenn dieser Wertverlust auf einen zur Prüfung der Beschaffenheit, Eigenschaften und Funktionsweise der Waren nicht notwendigen Umgang mit ihnen zurückzuführen ist.</p>
    <h2>Ausschluss des Widerrufsrechts</h2>
    <p>Das Widerrufsrecht besteht nicht bei Verträgen zur Lieferung von Waren, die nicht vorgefertigt sind und für deren Herstellung eine individuelle Auswahl oder Bestimmung durch den Verbraucher maßgeblich ist oder die eindeutig auf die persönlichen Bedürfnisse des Verbrauchers zugeschnitten sind (§ 312g Abs. 2 Nr. 1 BGB). Das betrifft in unserem Shop die Artikel mit Wunschtext oder eigenem Foto.</p>

    <h2 id="formular">Widerrufsformular</h2>
    <p>Wenn Sie den Vertrag widerrufen wollen, füllen Sie dieses Formular aus. Sie erhalten eine Eingangsbestätigung mit Vorgangsnummer.</p>
    <form class="form" id="widerrufsformular">
      <div class="alert" role="alert"></div>
      <p>Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über den Kauf der folgenden Waren:</p>
      <div class="field"><label for="w-ware">Bestellte Waren und Vorgangs- oder Rechnungsnummer</label><textarea id="w-ware" name="nachricht" required data-err="Bitte die Waren und die Vorgangsnummer angeben."></textarea><p class="msg"></p></div>
      <div class="row">
        <div class="field"><label for="w-bestellt">Bestellt am</label><input type="date" id="w-bestellt" name="bestellt_am" required data-err="Bitte das Bestelldatum angeben."><p class="msg"></p></div>
        <div class="field"><label for="w-erhalten">Erhalten am</label><input type="date" id="w-erhalten" name="erhalten_am"><p class="msg"></p></div>
      </div>
      <div class="row">
        <div class="field"><label for="w-name">Name des Verbrauchers</label><input type="text" id="w-name" name="name" required autocomplete="name" data-err="Bitte Ihren Namen eintragen."><p class="msg"></p></div>
        <div class="field"><label for="w-email">E-Mail</label><input type="email" id="w-email" name="email" required autocomplete="email" data-err="Bitte Ihre E-Mail-Adresse eintragen."><p class="msg"></p></div>
      </div>
      <div class="field"><label for="w-adr">Anschrift des Verbrauchers</label><input type="text" id="w-adr" name="anschrift" required autocomplete="street-address" data-err="Bitte Ihre Anschrift eintragen."><p class="msg"></p></div>
      <div class="field hp" aria-hidden="true"><label for="w-web">Website</label><input type="text" id="w-web" name="website" tabindex="-1" autocomplete="off"></div>
      <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir den Widerruf nicht bearbeiten."><span>Ich bin einverstanden, dass meine Angaben zur Bearbeitung des Widerrufs gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
      <button class="btn btn-primary" type="submit">Widerruf senden</button>
      <p class="small muted">Alternativ per E-Mail an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a> oder per Post an die oben genannte Anschrift.</p>
    </form>
  </div>
</section>
"""
    page("widerruf.html", f"Widerrufsrecht · {C.MARKE}", "Widerrufsbelehrung und Widerrufsformular für Bestellungen im Schichtwerk-Shop. 14 Tage Widerrufsrecht, Ausnahme für personalisierte Artikel.", body)


# ---------------------------------------------------------------- Impressum
def build_imprint():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Rechtliches</span>
    <h1>Impressum</h1>
    <h2>Angaben gemäß § 5 DDG</h2>
    <p>{E(C.FIRMA)}<br>Inhaber: {E(C.INHABER)} (Einzelunternehmen)<br>{E(C.STRASSE)}<br>{E(C.PLZ_ORT)}</p>
    <p class="small muted">„{E(C.MARKE)}“ ist eine Geschäftsbezeichnung des Einzelunternehmens von {E(C.INHABER)}, Celle, zu dem auch die Marketingagentur Markentrix gehört.</p>
    <h2>Kontakt</h2>
    <p>Telefon: <a href="{TEL_HREF}">{E(C.TELEFON)}</a><br>E-Mail: <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a></p>
    <h2>Umsatzsteuer</h2>
    <p>{'Kleinunternehmer gemäß § 19 UStG, es wird keine Umsatzsteuer ausgewiesen.<br>Steuernummer: ' + E(C.UST_ID) if C.KLEINUNTERNEHMER else 'Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: ' + E(C.UST_ID)}</p>
    <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
    <p>{E(C.INHABER)}, Anschrift wie oben.</p>
    <h2>Streitbeilegung</h2>
    <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" rel="noopener">https://ec.europa.eu/consumers/odr/</a>. Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
    <h2>Haftung für Inhalte und Links</h2>
    <p>Die Inhalte dieser Seiten wurden mit Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität übernehmen wir keine Gewähr. Für Inhalte verlinkter externer Seiten sind deren Betreiber verantwortlich.</p>
    <h2>Bildnachweis</h2>
    <p>Produktillustrationen, Logo und Grafiken: eigene Erstellung. Schrift „Inter“ von Rasmus Andersson, SIL Open Font License, lokal eingebunden.</p>
  </div>
</section>
"""
    page("impressum.html", f"Impressum · {C.MARKE}", "Impressum und Anbieterkennzeichnung von Schichtwerk 3D-Druck.", body)


# ---------------------------------------------------------------- Datenschutz
def build_privacy():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Rechtliches</span>
    <h1>Datenschutzerklärung</h1>
    <p class="muted">Stand: {datetime.date.today().strftime("%d.%m.%Y")}</p>
    <h2>1. Verantwortlicher</h2>
    <p>{E(C.FIRMA)}, {E(C.INHABER)}, {E(C.STRASSE)}, {E(C.PLZ_ORT)}<br>Telefon: {E(C.TELEFON)}, E-Mail: <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a></p>
    <h2>2. Hosting und Server-Logs</h2>
    <p>Diese Website wird bei Markentrix gehostet. Beim Aufruf speichert der Server automatisch Zugriffsdaten (aufgerufene Seite, Datum und Uhrzeit, übertragene Datenmenge, Browsertyp, Betriebssystem, verweisende Seite, IP-Adresse) in Protokolldateien. Diese Daten dienen der Sicherheit und dem störungsfreien Betrieb und werden nach spätestens 14 Tagen gelöscht. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse am sicheren Betrieb). Mit Markentrix besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO.</p>
    <h2>3. Bestellungen über den Shop</h2>
    <p>Wenn Sie bestellen, erheben wir Name, E-Mail-Adresse, Lieferadresse, gewählte Zahlungsart, die bestellten Artikel und gegebenenfalls Telefonnummer, Wunschtexte und Anmerkungen. Die Daten werden über das Markentrix-Portal an uns übermittelt und dort gespeichert; Sie erhalten eine Eingangsbestätigung mit Vorgangsnummer an die angegebene E-Mail-Adresse. Wir verwenden die Daten zur Vertragsabwicklung, Rechnungsstellung und Lieferung (Art. 6 Abs. 1 lit. b DSGVO). Die Lieferadresse geben wir an das Versandunternehmen (DHL) weiter. Rechnungsdaten bewahren wir nach den steuer- und handelsrechtlichen Fristen bis zu zehn Jahre auf.</p>
    <h2>4. Kontakt- und Anfrageformular, Widerrufsformular</h2>
    <p>Angaben aus den Formularen (Name, E-Mail, optional Telefon, Ihre Nachricht) werden über das Markentrix-Portal an uns übermittelt, dort gespeichert und zur Bearbeitung Ihrer Anfrage genutzt (Art. 6 Abs. 1 lit. b DSGVO, bei allgemeinen Anfragen Art. 6 Abs. 1 lit. a DSGVO auf Grundlage Ihrer Einwilligung). Sie erhalten eine automatische Eingangsbestätigung mit Vorgangsnummer. Anfragen ohne Vertragsschluss löschen wir nach spätestens zwölf Monaten. Ein unsichtbares Formularfeld dient ausschließlich der Spam-Abwehr.</p>
    <h2>5. Warenkorb (lokale Speicherung)</h2>
    <p>Der Inhalt Ihres Warenkorbs wird ausschließlich in Ihrem Browser gespeichert (localStorage) und nicht an uns übertragen, bis Sie die Bestellung absenden. Dies ist technisch notwendig, damit der Warenkorb zwischen den Seiten erhalten bleibt (§ 25 Abs. 2 Nr. 2 TDDDG). Sie können den Speicher jederzeit über die Browser-Einstellungen löschen.</p>
    <h2>6. Zahlung über PayPal</h2>
    <p>Wählen Sie PayPal, erhalten Sie von uns einen Zahlungslink. Die Zahlung findet auf der Website von PayPal (Europe) S.à r.l. et Cie, S.C.A., 22-24 Boulevard Royal, 2449 Luxemburg statt; dabei verarbeitet PayPal die von Ihnen dort eingegebenen Daten nach seiner eigenen Datenschutzerklärung. Wir erhalten von PayPal nur die Information über den Zahlungseingang, Ihren Namen und Ihre E-Mail-Adresse (Art. 6 Abs. 1 lit. b DSGVO). Auf dieser Website werden keine Zahlungsdaten erhoben.</p>
    <h2>7. Google-Bewertungen</h2>
    <p>Auf der Startseite zeigen wir Bewertungen unseres Google-Unternehmensprofils. Die Bewertungstexte werden über das Markentrix-Portal bereitgestellt; dabei wird keine direkte Verbindung von Ihrem Browser zu Google aufgebaut und es werden keine Daten an Google übertragen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (Interesse an der Darstellung von Kundenmeinungen).</p>
    <h2>8. Reichweitenmessung ohne Cookies</h2>
    <p>Zur Messung der Besucherzahlen übermittelt die Website an das Markentrix-Portal die aufgerufene Seite, den Seitentitel und die Fensterbreite. Es werden keine Cookies gesetzt, keine IP-Adressen gespeichert und keine Nutzerprofile gebildet; eine Zuordnung zu Ihrer Person ist nicht möglich (Art. 6 Abs. 1 lit. f DSGVO). Über den Link „Statistik-Einstellung“ im Seitenfuß können Sie die Messung abschalten.</p>
    <h2>9. Schriften und externe Dienste</h2>
    <p>Die verwendete Schrift ist lokal auf dem Server gespeichert. Es werden keine Schriften, Skripte oder Inhalte von Fremdservern (Google Fonts, Content Delivery Networks, soziale Netzwerke) nachgeladen.</p>
    <h2>10. Empfänger der Daten</h2>
    <p>Markentrix (Hosting und Portal, Auftragsverarbeitung), DHL (Versand), PayPal (bei gewählter Zahlungsart), Steuerberatung und Finanzbehörden (Rechnungsdaten, soweit gesetzlich erforderlich). Eine Übermittlung in Drittländer findet durch uns nicht statt; PayPal kann Daten nach seiner eigenen Datenschutzerklärung übermitteln.</p>
    <h2>11. Ihre Rechte</h2>
    <p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch (Art. 21). Eine erteilte Einwilligung können Sie jederzeit mit Wirkung für die Zukunft widerrufen. Außerdem haben Sie das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren. Wenden Sie sich dafür an die oben genannte Kontaktadresse.</p>
    <h2>12. Datensicherheit</h2>
    <p>Die Übertragung aller Daten erfolgt verschlüsselt über HTTPS.</p>
  </div>
</section>
"""
    page("datenschutz.html", f"Datenschutz · {C.MARKE}", "Datenschutzerklärung von Schichtwerk: Hosting bei Markentrix, Bestell- und Kontaktformular, Warenkorb, PayPal, Google-Bewertungen und Statistik ohne Cookies.", body)


# ---------------------------------------------------------------- Danke / 404
def build_thanks():
    body = f"""<section class="hero-mini" id="danke">
  <div class="wrap" style="max-width:640px">
    <span class="eyebrow">Vielen Dank</span>
    <h1 id="danke-h1">Ihre Bestellung ist eingegangen.</h1>
    <div data-show="bestellung">
      <p class="muted">Sie erhalten in wenigen Minuten eine Eingangsbestätigung per E-Mail. Innerhalb von zwei Werktagen folgt unsere Bestellbestätigung mit Rechnung und Zahlungsdaten. Nach Zahlungseingang beginnt der Druck.</p>
    </div>
    <div data-show="widerruf" data-h1="Ihr Widerruf ist eingegangen." hidden>
      <p class="muted">Sie erhalten eine Eingangsbestätigung per E-Mail. Wir melden uns innerhalb von zwei Werktagen mit den nächsten Schritten zur Rücksendung und Erstattung.</p>
    </div>
    <div data-show="kontakt" data-h1="Ihre Anfrage ist eingegangen." hidden>
      <p class="muted">Sie erhalten eine Eingangsbestätigung per E-Mail. Wir melden uns innerhalb eines Werktags mit Preis und Lieferzeit.</p>
    </div>
    <p>Ihre Vorgangsnummer:<br><span class="ref" id="ref"></span></p>
    <p hidden><a class="btn btn-primary" id="paypal-link" href="#" rel="noopener">Jetzt <span id="danke-summe"></span> per PayPal bezahlen</a></p>
    <p class="notice" id="bank-hinweis" hidden style="text-align:left">Sie haben Vorkasse gewählt: Die Bankverbindung steht auf der Rechnung, die Sie mit der Bestellbestätigung per E-Mail erhalten. Bitte geben Sie die Vorgangsnummer als Verwendungszweck an.</p>
    <p class="small muted">Keine E-Mail erhalten? Prüfen Sie den Spam-Ordner oder schreiben Sie an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>.</p>
    <p><a class="btn btn-ghost" href="shop.html">Zurück zum Shop</a></p>
  </div>
</section>
"""
    page("danke.html", f"Danke · {C.MARKE}", "Bestätigung: Ihre Bestellung oder Anfrage bei Schichtwerk ist eingegangen.", body, "", "", '<meta name="robots" content="noindex">')


def build_404():
    body = f"""<section class="hero-mini">
  <div class="wrap" style="max-width:600px">
    <span class="eyebrow">Fehler 404</span>
    <h1>Diese Seite gibt es nicht.</h1>
    <p class="muted">Vielleicht ist der Link veraltet oder der Artikel nicht mehr im Sortiment. Im Shop finden Sie alle aktuellen Artikel.</p>
    <p><a class="btn btn-primary" href="shop.html">Zum Shop</a> <a class="btn btn-ghost" href="index.html">Zur Startseite</a></p>
  </div>
</section>
"""
    page("404.html", f"Seite nicht gefunden · {C.MARKE}", "Die aufgerufene Seite existiert nicht.", body, "", "", '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- Daten, Sitemap, Robots, Manifest
def build_data():
    data = [dict(id=p["id"], name=p["name"], preis=p["preis"], kat=p["kat"], text=bool(p.get("text")), farben=p["farben"], kurz=p["kurz"]) for p in PRODUKTE]
    cfg = dict(email=C.EMAIL, telefon=C.TELEFON, paypalMe=C.PAYPAL_ME, versandPauschale=VERSAND_PAUSCHALE, versandfreiAb=VERSANDFREI_AB, produktionMin=2, produktionMax=4, versandMin=2, versandMax=3)
    farben = {k: [v[0], v[1]] for k, v in FARBEN.items()}
    with open(os.path.join(ROOT, "assets", "js", "produkte.js"), "w", encoding="utf-8") as f:
        f.write("/* generiert von build/build.py */\n")
        f.write("window.SW_CONFIG=" + json.dumps(cfg, ensure_ascii=False) + ";\n")
        f.write("window.SW_FARBEN=" + json.dumps(farben, ensure_ascii=False) + ";\n")
        f.write("window.SW_PRODUKTE=" + json.dumps(data, ensure_ascii=False) + ";\n")
    pages = ["index.html", "shop.html", "druckservice.html", "materialien.html", "faq.html", "kontakt.html", "versand.html", "ueber-uns.html", "agb.html", "widerruf.html", "impressum.html", "datenschutz.html"] + [f"material/{m['id']}.html" for m in MATERIALIEN] + [f"produkt/{p['id']}.html" for p in PRODUKTE]
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in pages:
            f.write(f"  <url><loc>/{u}</loc><lastmod>{TODAY}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /warenkorb.html\nDisallow: /danke.html\n")
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump({"name": f"{C.MARKE} {C.CLAIM}", "short_name": C.MARKE, "start_url": "index.html", "display": "browser",
                   "background_color": "#f6f4ef", "theme_color": "#e8561f",
                   "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]}, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- Materialien
def spool(color, size=72):
    return f"""<svg class="spool" viewBox="0 0 72 72" width="{size}" height="{size}" aria-hidden="true"><circle cx="36" cy="36" r="33" fill="{color}"/><circle cx="36" cy="36" r="24" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="2" stroke-dasharray="3 3"/><circle cx="36" cy="36" r="18" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="2" stroke-dasharray="3 3"/><circle cx="36" cy="36" r="9" fill="var(--bg)"/><circle cx="36" cy="36" r="4" fill="{color}"/></svg>"""


def mat_card(m, rel, h="h3"):
    return f"""<a class="mat-card" href="{rel}material/{m['id']}.html" style="--mat:{m['farbe']}">
  {spool(m['farbe'], 56)}
  <div><span class="mat-name">{E(m['name'])}</span><{h}>{E(m['titel'])}</{h}><p class="small muted">{E(m['claim'])}</p></div>
</a>"""


def build_materials():
    cards = "\n".join(mat_card(m, "", "h2") for m in MATERIALIEN)
    head_row = "".join(f'<th scope="col"><a href="material/{m["id"]}.html">{E(m["name"])}</a></th>' for m in MATERIALIEN)
    rows = "".join(f'<tr><th scope="row">{E(k)}</th>' + "".join(f"<td>{E(v)}</td>" for v in vals) + "</tr>" for k, vals in VERGLEICH)
    body = f"""<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Materialien</span>
    <h1>Welches Material passt zu Ihrem Teil?</h1>
    <p class="lead muted" style="max-width:62ch">Fünf Kunststoffe decken fast alles ab, was im Alltag gedruckt wird. Hier steht, was jedes Material kann, wo seine Grenzen liegen und was der Druck kostet. Im Zweifel beraten wir bei der <a href="kontakt.html">Anfrage</a>.</p>
    <div class="mat-grid">{cards}</div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Vergleich auf einen Blick</h2>
    <div class="table-scroll"><table class="compare"><thead><tr><th scope="col">Eigenschaft</th>{head_row}</tr></thead><tbody>{rows}</tbody></table></div>
    <p class="small muted">Richtwerte für Standard-Filamente bei 0,2 mm Schichthöhe. Den Festpreis für Ihr Teil nennen wir im kostenlosen Angebot.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <div class="feature-grid">
      <div class="feature"><h3>Drinnen, dekorativ, maßgenau</h3><p class="muted">PLA. Die sauberste Oberfläche, die meisten Farben, am schnellsten geliefert.</p></div>
      <div class="feature"><h3>Nass, warm oder unter Last</h3><p class="muted">PETG. Zäh und wasserfest, für Küche, Bad, Clips und Gehäuse.</p></div>
      <div class="feature"><h3>Heiß oder nachbearbeitet</h3><p class="muted">ABS. Bis 95 °C, schleifbar, mit Aceton glättbar, für Ersatzteile.</p></div>
      <div class="feature"><h3>Draußen über Jahre</h3><p class="muted">ASA. UV-stabil und wetterfest, für Garten, Auto und Fassade.</p></div>
      <div class="feature"><h3>Weich und flexibel</h3><p class="muted">TPU. Gummiartig, reißfest, für Dichtungen, Puffer und Hüllen.</p></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="cta-band">
      <div><h2>Unsicher, welches Material?</h2><p style="margin:6px 0 0;opacity:.85">Beschreiben Sie Einsatzort und Belastung, wir schlagen das passende Material vor und schicken innerhalb eines Werktags ein kostenloses Angebot.</p></div>
      <a class="btn btn-primary" href="kontakt.html">Anfrage stellen</a>
    </div>
  </div>
</section>
"""
    page("materialien.html", f"Materialien für den 3D-Druck · {C.MARKE}", "PLA, PETG, ABS, ASA und TPU im Vergleich: Wärmebeständigkeit, Festigkeit, Außeneinsatz, Detailtreue. Welches Material passt zu Ihrem 3D-Druck-Teil?", body, "material")

    for i, m in enumerate(MATERIALIEN):
        rel = "../"
        props = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in m["eigenschaften"])
        gut = "".join(f"<li>{E(x)}</li>" for x in m["gut"])
        nicht = "".join(f"<li>{E(x)}</li>" for x in m["nicht"])
        faq = "".join(f'<details class="faq-item"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in m["faq"])
        others = "\n".join(mat_card(o, rel) for o in MATERIALIEN if o["id"] != m["id"])
        shop_examples = [p for p in PRODUKTE if m["name"] in p["material"]][:3]
        examples = ""
        if shop_examples:
            examples = f"""<section class="section-tight"><div class="wrap"><h2>Aus {E(m['name'])} im Shop</h2><div class="grid">{"".join(card(p, rel, k) for k, p in enumerate(shop_examples))}</div></div></section>"""
        body = f"""<section class="section-tight">
  <div class="wrap">
    <nav aria-label="Pfad" class="small muted" style="margin-bottom:16px"><a href="../index.html">Start</a> › <a href="../materialien.html">Materialien</a> › {E(m['name'])}</nav>
    <div class="mat-hero" style="--mat:{m['farbe']}">
      <div>
        <span class="eyebrow">Material</span>
        <h1>{E(m['titel'])}</h1>
        <p class="lead">{E(m['claim'])}</p>
        <p class="muted" style="max-width:60ch">{E(m['kurz'])}</p>
        <div class="hero-actions"><a class="btn btn-primary" href="../kontakt.html">Kostenloses Angebot für {E(m['name'])}</a><a class="btn btn-ghost" href="../materialien.html">Alle Materialien</a></div>
      </div>
      <div class="mat-art">{spool(m['farbe'], 220)}</div>
    </div>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <div class="mat-cols">
      <div>
        <h2>Eigenschaften</h2>
        <dl class="specs">{props}</dl>
        <h2>Druckparameter</h2>
        <dl class="specs"><dt>Schichthöhe</dt><dd>{E(m['schicht'])}</dd><dt>Düsentemperatur</dt><dd>{E(m['duesen'])}</dd><dt>Druckbett</dt><dd>{E(m['bett'])}</dd><dt>Dichte</dt><dd>{E(m['dichte'])}</dd></dl>
      </div>
      <div>
        <h2>Geeignet für</h2>
        <ul class="list-check">{gut}</ul>
        <h2>Nicht geeignet für</h2>
        <ul class="list-cross">{nicht}</ul>
        <div class="notice"><strong>Farben:</strong> {E(m['farben'])}</div>
        <div class="trust-list"><span>{SVG_CHECK} Kostenloses Angebot innerhalb eines Werktags</span><span>{SVG_CHECK} Festpreis vor dem Druck, keine Überraschungen</span><span>{SVG_CHECK} Nachdruck-Garantie bei Transportschäden</span></div>
      </div>
    </div>
  </div>
</section>
<section class="section-tight">
  <div class="wrap prose">
    <h2>Häufige Fragen zu {E(m['name'])}</h2>
    {faq}
  </div>
</section>
{examples}
<section class="section">
  <div class="wrap">
    <h2>Andere Materialien</h2>
    <div class="mat-grid">{others}</div>
  </div>
</section>
"""
        page(f"material/{m['id']}.html", f"{m['titel']} · {C.MARKE}", (m["claim"] + " " + m["kurz"])[:155], body, "material", rel)


# ---------------------------------------------------------------- Druckservice
def build_service():
    mats = "\n".join(mat_card(m, "") for m in MATERIALIEN)
    body = f"""<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">Druckservice</span>
      <h1>Ihre Datei, unser Drucker.</h1>
      <p class="lead">Ersatzteile, Prototypen, Kleinserien, Vereinslogos: Schicken Sie uns Ihre STL-, 3MF- oder STEP-Datei oder beschreiben Sie das Teil. Sie bekommen innerhalb eines Werktags einen Festpreis.</p>
      <div class="hero-actions"><a class="btn btn-primary" href="kontakt.html">Kostenloses Angebot anfordern</a><a class="btn btn-ghost" href="materialien.html">Materialien vergleichen</a></div>
      <div class="hero-facts">
        <span>{SVG_CHECK} Kostenloses Angebot in 24 h</span>
        <span>{SVG_CHECK} Festpreis vor dem Druck</span>
        <span>{SVG_CHECK} Ab 1 Stück</span>
      </div>
    </div>
    <div class="hero-art">
      <svg viewBox="0 0 400 400" role="img" aria-label="Von der Datei zum gedruckten Teil">
        <rect x="40" y="70" width="150" height="190" rx="12" fill="#2b2e34"/>
        <rect x="56" y="88" width="118" height="12" rx="4" fill="#8a8f99"/><rect x="56" y="110" width="90" height="12" rx="4" fill="#8a8f99"/><rect x="56" y="132" width="104" height="12" rx="4" fill="#8a8f99"/>
        <text x="115" y="230" text-anchor="middle" font-family="Inter,sans-serif" font-weight="700" font-size="26" fill="#ffb08c">.STL</text>
        <path d="M200 165 h60" stroke="#bf3e0b" stroke-width="8" stroke-linecap="round"/><path d="M250 148 l24 17 l-24 17z" fill="#bf3e0b"/>
        <g fill="#bf3e0b"><rect x="280" y="236" width="90" height="16" rx="4"/><rect x="284" y="220" width="82" height="16" rx="4" opacity=".92"/><rect x="288" y="204" width="74" height="16" rx="4" opacity=".84"/><rect x="292" y="188" width="66" height="16" rx="4" opacity=".76"/><rect x="296" y="172" width="58" height="16" rx="4" opacity=".68"/><rect x="300" y="156" width="50" height="12" rx="4" opacity=".55"/></g>
        <rect x="260" y="256" width="130" height="18" rx="6" fill="#8a8f99"/>
        <ellipse cx="325" cy="300" rx="80" ry="12" fill="#000" opacity=".12"/>
      </svg>
    </div>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <span class="eyebrow">Leistungen</span>
    <h2>Was wir für Sie drucken</h2>
    <div class="feature-grid">
      <div class="feature">{ICONS['pen']}<h3>Ersatzteile</h3><p class="muted">Abgebrochene Halter, Zahnräder, Knöpfe, Abdeckungen, Clips. Mit Datei oder nach Foto und Maßen nachkonstruiert.</p></div>
      <div class="feature">{ICONS['layer']}<h3>Prototypen</h3><p class="muted">Formstudien, Passungsmuster und Funktionsmuster für Entwickler, Handwerker und Studierende. Schnell, auch über Nacht.</p></div>
      <div class="feature">{ICONS['truck']}<h3>Kleinserien</h3><p class="muted">10 bis 500 Stück, zum Beispiel Vereinsanhänger, Messe-Giveaways, Halterungen für Betriebe. Mengenrabatt ab 10 Stück.</p></div>
      <div class="feature">{ICONS['leaf']}<h3>Nachbearbeitung</h3><p class="muted">Schleifen, Füllern, Lackieren, Aceton-Glätten bei ABS, Gewindeeinsätze einpressen, Magnete einkleben.</p></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <span class="eyebrow">Ablauf</span>
    <h2>Vom Upload zum Paket</h2>
    <div class="steps">
      <div class="step"><h3>Anfrage</h3><p class="muted">Formular ausfüllen: Stückzahl, Material, Einsatzzweck. Die Datei schicken Sie per Mail an die Adresse aus unserer Antwort.</p></div>
      <div class="step"><h3>Prüfung und Festpreis</h3><p class="muted">Wir prüfen Wandstärken, Überhänge und Maße, schlagen bei Bedarf Material oder Ausrichtung vor und nennen einen Festpreis mit Liefertermin.</p></div>
      <div class="step"><h3>Druck und Kontrolle</h3><p class="muted">Nach Ihrer Freigabe und Zahlung wird gedruckt. Jedes Teil wird vermessen und von Stützmaterial befreit.</p></div>
      <div class="step"><h3>Versand</h3><p class="muted">Verpackt in Papier und Karton, mit DHL und Sendungsnummer. Abholung nach Absprache möglich.</p></div>
    </div>
  </div>
</section>
<section class="section-tight">
  <div class="wrap prose">
    <h2>Festpreis statt Überraschung</h2>
    <p>Sie bekommen vor dem Druck einen Festpreis mit Liefertermin, kostenlos und unverbindlich. Erst wenn Sie freigeben, läuft der Drucker. Nachbearbeitung und Konstruktion stehen getrennt im Angebot, es kommt nichts dazu, was nicht vorher besprochen wurde. Ab zehn gleichen Teilen gibt es Mengenpreise.</p>
    <div class="trust-list"><span>{SVG_CHECK} Angebot innerhalb eines Werktags</span><span>{SVG_CHECK} Unverbindlich, keine Vorkasse für das Angebot</span><span>{SVG_CHECK} Ab 1 Stück, Mengenpreise ab 10 Stück</span><span>{SVG_CHECK} Nachdruck kostenlos, wenn ein Teil nicht passt wie besprochen</span></div>
    <h2>Voraussetzungen für die Datei</h2>
    <ul>
      <li>Format STL, 3MF, STEP oder OBJ, Einheit Millimeter, Modell geschlossen („wasserdicht“)</li>
      <li>Wandstärke mindestens 1,2 mm, bei TPU 2 mm</li>
      <li>Maximal 25 × 25 × 25 cm am Stück, größere Teile segmentieren wir</li>
      <li>Keine Waffen, keine Markenprodukte zum Weiterverkauf, keine sicherheitsrelevanten Teile</li>
    </ul>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <h2>Materialien zur Auswahl</h2>
    <div class="mat-grid">{mats}</div>
  </div>
</section>
"""
    page("druckservice.html", f"3D-Druckservice für eigene Dateien · {C.MARKE}", "3D-Druck auf Bestellung: Ersatzteile, Prototypen und Kleinserien aus PLA, PETG, ABS, ASA oder TPU. Festpreis innerhalb eines Werktags, ab 1 Stück.", body, "service")


# ---------------------------------------------------------------- FAQ
def build_faq():
    groups = ""
    for title, items in FAQ:
        groups += f'<h2>{E(title)}</h2>' + "".join(f'<details class="faq-item"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in items)
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <span class="eyebrow">Hilfe</span>
    <h1>Fragen und Antworten</h1>
    <p class="muted">Die häufigsten Fragen zu Bestellung, Material und Druckservice. Nicht dabei? <a href="kontakt.html">Schreiben Sie uns</a>.</p>
    {groups}
  </div>
</section>
"""
    page("faq.html", f"Fragen und Antworten · {C.MARKE}", "Antworten zu Lieferzeit, Zahlung, Materialwahl, Dateiformaten, Rückgabe und Reklamation im Schichtwerk-Shop.", body, "faq")


if __name__ == "__main__":
    for fn in (build_data, build_index, build_shop, build_products, build_cart, build_contact, build_about, build_shipping, build_agb, build_widerruf, build_imprint, build_privacy, build_thanks, build_404, build_materials, build_service, build_faq):
        fn()
    n = sum(len(f) for _, _, f in os.walk(ROOT))
    print("Fertig:", n, "Dateien in", ROOT)
