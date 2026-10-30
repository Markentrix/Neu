"""Erzeugt alle HTML-Seiten, produkte.js, sitemap.xml, robots.txt und site.webmanifest in website-fertig/.
Aufruf: python3 build/build.py"""
import os, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(__file__))
import config as C
from produkte import PRODUKTE, FARBEN, KATEGORIEN, VERSAND_PAUSCHALE, VERSANDFREI_AB
from materialien import MATERIALIEN, VERGLEICH, FAQ
AKTIV = [p for p in PRODUKTE if not p.get("entwurf")]          # nur freigeschaltete Artikel
KAT_AKTIV = {k: v for k, v in KATEGORIEN.items() if any(p["kat"] == k for p in AKTIV)}

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "website-fertig"))
E = html.escape
EUR = lambda n: ("%.2f" % n).replace(".", ",") + " €"
TEL_HREF = "tel:" + "".join(ch for ch in C.TELEFON if ch.isdigit() or ch == "+")
TODAY = datetime.date.today().isoformat()

SVG_CART = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h2l2.4 12.4a2 2 0 0 0 2 1.6h8.2a2 2 0 0 0 2-1.6L21 8H6"/><circle cx="9" cy="21" r="1.2"/><circle cx="18" cy="21" r="1.2"/></svg>'
SVG_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
from logo import mark as _mark
from logo_lockup import inline_svg as _lockup
LOCKUP_FOOTER = _lockup(False, "lockup")
LOCKUP_HEAD = _lockup(False, "lockup lockup-head")
def SVG_LOGO_ID(uid):
    return '<svg viewBox="0 0 64 64" aria-hidden="true">' + _mark(True, uid=uid, small=True) + '</svg>'


def head(title, desc, rel, canonical_name, extra=""):
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#f3f5f1">
<link rel="icon" href="{rel}favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<link rel="manifest" href="{rel}site.webmanifest">
<link rel="preload" href="{rel}assets/fonts/HankenGrotesk.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{rel}assets/fonts/AbrilFatface.woff2" as="font" type="font/woff2" crossorigin>
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
    <a class="lockup-link" href="{rel}index.html" aria-label="{E(C.MARKE)} Startseite">{LOCKUP_HEAD}</a>
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
    <div class="footer-top">
      <div>
        <a class="lockup-link" href="{rel}index.html" aria-label="{E(C.MARKE)} Startseite">{LOCKUP_FOOTER}</a>
        <div class="footer-kontakt">
          <p>{E(C.STRASSE)}, {E(C.PLZ_ORT)}<br>Abholung nach Terminabsprache</p>
          <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a><br>
          <a href="{TEL_HREF}">{E(C.TELEFON)}</a>
        </div>
      </div>
      <div>
        <h2>Kaufen und anfragen</h2>
        <ul>
          <li><a href="{rel}shop.html">Shop</a></li>
          <li><a href="{rel}gutschein.html">Geschenkgutschein</a></li>
          <li><a href="{rel}druckservice.html">Druckservice</a></li>
          <li><a href="{rel}kontakt.html">Angebot anfordern</a></li>
          <li><a href="{rel}versand.html">Versand und Zahlung</a></li>
        </ul>
      </div>
      <div>
        <h2>Wissen und Recht</h2>
        <ul>
          <li><a href="{rel}materialien.html">Materialien</a></li>
          <li><a href="{rel}faq.html">Fragen und Antworten</a></li>
          <li><a href="{rel}ueber-uns.html">Über uns</a></li>
          <li><a href="{rel}impressum.html">Impressum</a></li>
          <li><a href="{rel}datenschutz.html">Datenschutz</a></li>
          <li><a href="{rel}agb.html">AGB</a></li>
          <li><a href="{rel}widerruf.html">Widerrufsrecht</a></li>
          <li><span data-mk="cookies"></span></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© {datetime.date.today().year} {E(C.FIRMA)}</span>
      <span>Gehostet bei Markentrix</span>
      <span>Keine Tracking-Cookies</span>
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
    href = f"{rel}produkt/{p['id']}.html"
    notes = []
    if p.get("text"): notes.append("Mit Wunschtext")
    if len(p["farben"]) > 1: notes.append(f"in {len(p['farben'])} Farben")
    note = f'<span class="card-note">{E(", ".join(notes))}</span>' if notes else ""
    action = (f'<a class="btn btn-primary" href="{href}">Text und Farbe wählen</a>' if p.get("text")
              else f'<button class="btn btn-primary" type="button" data-add="{p["id"]}">In den Warenkorb</button>')
    return f"""<article class="card" data-kat="{p['kat']}" data-tags="{' '.join(p['tags'])}" data-preis="{p['preis']}" data-name="{E(p['name'])}" data-pos="{pos}">
  <a class="card-img" href="{href}" tabindex="-1" aria-hidden="true"><img src="{rel}assets/img/produkte/{p['id']}.webp" width="800" height="600" alt="" loading="lazy"></a>
  <div class="card-body">
    <{h}><a href="{href}">{E(p['name'])}</a></{h}>
    <p class="small">{E(p['kurz'])}</p>
    <div class="price">{EUR(p['preis'])}</div>
    {note}
    {action}
    <a class="card-more" href="{href}">Details ansehen</a>
  </div>
</article>"""


def datei_band(titel, text, knopf, href):
    return f"""<section class="datei on-deep">
  <div class="wrap in">
    <h2>{E(titel)}</h2>
    <div><p>{E(text)}</p><a class="btn btn-primary" href="{href}">{E(knopf)}</a></div>
  </div>
</section>
"""


# ---------------------------------------------------------------- Startseite
def build_index():
    best = AKTIV[:4]
    cards = "\n".join(card(p, "", i) for i, p in enumerate(best))
    mat_rows = "".join(
        f'<li><a href="material/{m["id"]}.html"><span class="mname">{E(m["name"])}</span><span class="muse">{E(m["einsatz"])}</span><span class="mtemp">{E(m["temp"])}</span></a></li>'
        for m in MATERIALIEN)
    body = f"""<section class="hero-dark on-deep">
  <div class="hero-in">
    <div class="hero-copy">
      <h1>Gedruckt in Celle, Schicht für Schicht.</h1>
      <p>Kleine Dinge aus dem 3D-Drucker von {E(C.INHABER)}: Deko, Geschenke und Teile nach Ihrer Datei. Jedes Stück entsteht erst nach Ihrer Bestellung.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="shop.html">Im Shop ansehen</a>
        <a class="textlink" href="druckservice.html">Eigene Datei drucken lassen</a>
      </div>
    </div>
    <figure class="hero-photo">
      <img src="assets/img/hero.webp" width="1200" height="1200" alt="Kleiner Kürbis aus orangefarbenem Silk-PLA auf dem Druckbett eines Bambu Lab X1 Carbon, im Hintergrund weitere frisch gedruckte Kürbisse" fetchpriority="high">
      <figcaption>Kleiner Kürbis aus Orange Silk, frisch vom Druckbett des Bambu Lab X1 Carbon.</figcaption>
    </figure>
  </div>
</section>
<div class="schichtkante" aria-hidden="true"></div>

<section class="section">
  <div class="wrap shop-block">
    <div class="side">
      <h2>Im Shop</h2>
      <p>Farbe wählen, bei Wunschtext-Artikeln den Text eintragen, in den Warenkorb legen. Gedruckt wird nach der Bestellung.</p>
      <p><a class="textlink" href="shop.html">Alle <span id="alle-anzahl">{len(AKTIV)}</span> Artikel ansehen</a><br><a class="textlink" href="gutschein.html">Geschenkgutschein</a></p>
    </div>
    <div id="featured-grid">{cards}</div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap zeit">
    <div>
      <h2>Wann es bei Ihnen ist</h2>
      <p class="muted">Gedruckt wird nach Ihrer Bestellung. Bei Artikeln mit Wunschtext beginnt der Druck nach Ihrer Freigabe. Die Zeiten sind Richtwerte.</p>
    </div>
    <div>
      <div class="zeit-bar" role="img" aria-label="Druck {E(C.PRODUKTIONSZEIT)}, danach Versand {E(C.LIEFERZEIT)}"><span class="z-order"></span><span class="z-print"></span><span class="z-ship"></span></div>
      <div class="zeit-legend"><span><strong>Tag 0</strong>Bestellung</span><span><strong>{E(C.PRODUKTIONSZEIT)}</strong>Druck</span><span><strong>{E(C.LIEFERZEIT)}</strong>Versand</span></div>
    </div>
  </div>
</section>

{datei_band("Sie haben eine Datei?", "STL, 3MF oder STEP, ein kaputtes Teil als Foto mit Maßen oder nur eine Idee. Schreiben Sie, was Sie brauchen, und Sie bekommen Preis und Lieferzeit.", "Angebot für meine Datei anfordern", "kontakt.html")}

<section class="section">
  <div class="wrap shop-block">
    <div class="side">
      <h2>Welches Material?</h2>
      <p>Vier Kunststoffe, je nach Einsatzort. Die Temperatur ist die Grenze, ab der das Teil weich wird.</p>
      <p><a class="textlink" href="materialien.html">Alle im Vergleich</a></p>
    </div>
    <ul class="materialliste">{mat_rows}</ul>
  </div>
</section>

<section class="section-tight" id="kundenstimmen" hidden>
  <div class="wrap">
    <h2>Das sagen Kunden</h2>
    <div class="reviews-box"><div data-mk="bewertungen"></div></div>
  </div>
</section>
"""
    page("index.html", f"{C.MARKE} · 3D-gedruckte Alltagshelfer kaufen", "3D-Druck-Atelier in Celle: Deko, Geschenke und Teile nach eigener Datei, gedruckt nach Bestellung auf einem Bambu Lab X1 Carbon.", body, "index")


# ---------------------------------------------------------------- Shop
def build_shop():
    chips = '<button class="chip" type="button" data-kat="alle" aria-pressed="true">Alle</button>' + "".join(
        f'<button class="chip" type="button" data-kat="{k}" aria-pressed="false">{E(v)}</button>' for k, v in KAT_AKTIV.items()) + ('<button class="chip" type="button" data-kat="personalisiert" aria-pressed="false">Mit Wunschtext</button>' if any(p.get("text") for p in AKTIV) else "")
    cards = "\n".join(card(p, "", i, "h2") for i, p in enumerate(AKTIV))
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Alle Artikel</h1>
    <p class="lead"><span id="shop-anzahl">{len(AKTIV)}</span> Artikel, jeder wird erst nach Ihrer Bestellung gedruckt. Versand {EUR(VERSAND_PAUSCHALE)}, ab {EUR(VERSANDFREI_AB)} kostenlos, Abholung in Celle ohne Versandkosten.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <div class="filterbar" role="group" aria-label="Nach Kategorie filtern">
      <span id="kat-chips" class="chips-wrap">{chips}</span>
      <label class="sr-only" for="sortierung">Sortierung</label>
      <select id="sortierung"><option value="standard">Reihenfolge im Shop</option><option value="preis-auf">Preis aufsteigend</option><option value="preis-ab">Preis absteigend</option><option value="name">Name A bis Z</option></select>
    </div>
    <p class="small muted" id="treffer" aria-live="polite">{len(AKTIV)} Artikel</p>
    <div class="grid" id="shop-grid">{cards}{gutschein_card("")}</div>
  </div>
</section>
"""
    page("shop.html", f"Shop · Alle 3D-Druck-Artikel · {C.MARKE}", "Alle Artikel von Schichtatelier: auf Bestellung in Celle gedruckt, Farbe wählbar, Versand oder Abholung, Zahlung per PayPal.", body, "shop")


# ---------------------------------------------------------------- Produktseiten
def build_products():
    # Seiten von Entwürfen oder gelöschten Artikeln entfernen
    pdir = os.path.join(ROOT, "produkt")
    if os.path.isdir(pdir):
        keep = {p["id"] + ".html" for p in AKTIV}
        for f in os.listdir(pdir):
            if f not in keep: os.remove(os.path.join(pdir, f))
    for i, p in enumerate(AKTIV):
        rel = "../"
        sw = ""
        for j, f in enumerate(p["farben"]):
            name, hexc = FARBEN[f]
            sw += f'<label class="swatch"><input type="radio" name="farbe" value="{f}"{" checked" if j == 0 else ""}><span><i style="background:{hexc}"></i>{E(name)}</span></label>'
        textfield = ""
        if p.get("text"):
            textfield = f"""<div class="field"><label for="wunschtext">{E(p['textlabel'])}</label><input type="text" id="wunschtext" name="wunschtext" maxlength="80" required autocomplete="off"><p class="msg">Bitte den Wunschtext eintragen.</p></div>"""
        related = [q for q in AKTIV if q["kat"] == p["kat"] and q["id"] != p["id"]][:3]
        if len(related) < 3:
            related += [q for q in AKTIV if q["id"] != p["id"] and q not in related][:3 - len(related)]
        rel_cards = "\n".join(card(q, rel, k) for k, q in enumerate(related))
        widerruf = ('<p class="small muted">Personalisierter Artikel: Nach Ihrer Freigabe des Textes ist der Kauf vom Widerruf ausgenommen (§ 312g Abs. 2 Nr. 1 BGB). <a href="../widerruf.html">Mehr dazu</a>.</p>' if p.get("text") else "")
        body = f"""<section class="section-tight">
  <div class="wrap">
    <nav aria-label="Pfad" class="crumbs"><a href="../index.html">Start</a> › <a href="../shop.html">Shop</a> › <a href="../shop.html#{p['kat']}">{E(KATEGORIEN[p['kat']])}</a></nav>
    <div class="product">
      <div class="product-media"><img src="../assets/img/produkte/{p['id']}.webp" width="800" height="600" alt="{E(p['name'])}{', gedruckt in ' + E(FARBEN[p['farben'][0]][0]) if p.get('foto') else ', Illustration in ' + E(FARBEN[p['farben'][0]][0])}"></div>
      <div class="product-info">
        <h1>{E(p['name'])}</h1>
        <p class="price">{EUR(p['preis'])} <small>{'inkl. MwSt.' if not C.KLEINUNTERNEHMER else 'Endpreis, keine Umsatzsteuer nach § 19 UStG'}, zzgl. <a href="../versand.html">Versand</a></small></p>
        <p>{E(p['kurz'])}</p>
        <form id="kaufen" data-id="{p['id']}" novalidate>
          <fieldset style="border:0;padding:0;margin:0 0 14px"><legend style="font-weight:600;margin-bottom:8px">Farbe</legend><div class="swatches">{sw}</div></fieldset>
          {textfield}
          <div class="buyrow">
            <span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" id="menge" name="menge" min="1" max="99" value="1" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span>
            <button class="btn btn-primary" type="submit">In den Warenkorb</button>
          </div>
          <p class="added" role="status">Liegt im Warenkorb. <a href="../warenkorb.html">Zum Warenkorb</a> oder <a href="../shop.html">weiter stöbern</a>.</p>
        </form>
        <p class="delivery" data-delivery>Bestellen Sie heute, Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>
        <dl class="konditionen"><dt>Versand</dt><dd>{EUR(VERSAND_PAUSCHALE)}, ab {EUR(VERSANDFREI_AB)} kostenlos</dd><dt>Abholung</dt><dd>Celle, kostenlos, nach Terminabsprache</dd><dt>Zahlung</dt><dd>PayPal oder bei Abholung</dd><dt>Rückgabe</dt><dd>{'ausgeschlossen, weil nach Ihrem Text gefertigt' if p.get('text') else '14 Tage'}</dd></dl>
        <dl class="specs">
          <dt>Maße</dt><dd>{E(p['masse'])}</dd>
          <dt>Material</dt><dd>{E(p['material'])}</dd>
          <dt>Gewicht</dt><dd>{E(p['gewicht'])}</dd>
          <dt>Fertigung</dt><dd>Druck in {E(C.PRODUKTIONSZEIT)}, dann Versand</dd>
        </dl>
        <h2 class="sub">Beschreibung</h2>
        <p>{E(p['lang'])}</p>
        <p class="small muted">Hinweis: 3D-gedruckte Teile zeigen feine Schichtlinien, das ist Teil des Verfahrens. Farben können je nach Filamentcharge leicht abweichen.{'' if p.get('foto') else ' Die Abbildung ist eine Illustration des Artikels.'}</p>
        {widerruf}
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Weitere Artikel</h2>
    <p class="muted">Ab {EUR(VERSANDFREI_AB)} Bestellwert entfallen die Versandkosten. Alles aus einer Bestellung wird zusammen gedruckt und verschickt.</p>
    <div class="grid">{rel_cards}</div>
  </div>
</section>
<div class="sticky-buy" aria-hidden="true"><span class="sticky-price">{EUR(p['preis'])}</span><button class="btn btn-primary" type="button" data-sticky-buy>In den Warenkorb</button></div>
"""
        title = f"{p['name']} · {C.MARKE}"
        if len(title) > 60:
            title = p["name"][:57].rstrip() + "…"
        ld = json.dumps({"name": p["name"], "description": p["kurz"], "sku": p["id"], "image": f"assets/img/produkte/{p['id']}.webp",
                         "url": f"produkt/{p['id']}.html", "price": "%.2f" % p["preis"], "material": p["material"], "category": KATEGORIEN[p["kat"]],
                         "brand": C.MARKE, "seller": C.FIRMA, "shipping": "%.2f" % VERSAND_PAUSCHALE, "freeFrom": "%.2f" % VERSANDFREI_AB,
                         "breadcrumbs": [["Start", "index.html"], ["Shop", "shop.html"], [p["name"], f"produkt/{p['id']}.html"]]}, ensure_ascii=False)
        body = body.replace('<div class="sticky-buy"', f'<script type="application/json" id="produkt-daten">{ld}</script>\n<div class="sticky-buy"', 1)
        page(f"produkt/{p['id']}.html", title, p["kurz"][:155], body, "shop", rel)


# ---------------------------------------------------------------- Allgemeine Produktseite (Artikel aus dem Portal)
def build_product_dyn():
    body = """<section class="section-tight">
  <div class="wrap" id="produkt-dyn">
    <h1>Artikel wird geladen …</h1>
    <noscript><p>Für die Artikelansicht wird JavaScript benötigt. Alle Artikel finden Sie im <a href="shop.html">Shop</a>.</p></noscript>
  </div>
</section>
"""
    page("produkt.html", f"Artikel · {C.MARKE}", "Artikel im Online-Shop von Schichtatelier: Farbe wählen, in den Warenkorb legen, auf Bestellung gedruckt.", body, "shop", "", '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- Gutschein
def gutschein_card(rel):
    return f"""<article class="card card-gutschein" data-kat="geschenk" data-preis="10" data-name="Geschenkgutschein" data-pos="999">
  <a class="card-img" href="{rel}gutschein.html" tabindex="-1" aria-hidden="true"><img src="{rel}assets/img/produkte/gutschein.webp" width="800" height="600" alt="" loading="lazy"></a>
  <div class="card-body">
    <h3><a href="{rel}gutschein.html">Geschenkgutschein</a></h3>
    <p class="small muted" style="margin:0">Wunschbetrag ab 10 €, als Karte per Post oder zum Ausdrucken per E-Mail. 3 Jahre gültig.</p>
    <div class="price">ab 10,00 €</div>
    <a class="btn btn-primary" href="{rel}gutschein.html">Gutschein wählen</a>
  </div>
</article>"""


def build_voucher():
    amounts = "".join(f'<label class="swatch"><input type="radio" name="betrag" value="{a}"{" checked" if a == 20 else ""}><span>{a} €</span></label>' for a in (10, 20, 30, 50))
    body = f"""<section class="section-tight">
  <div class="wrap">
    <nav aria-label="Pfad" class="crumbs"><a href="index.html">Start</a> › <a href="shop.html">Shop</a> › Geschenkgutschein</nav>
    <div class="product">
      <div class="product-media"><img src="assets/img/produkte/gutschein.webp" width="800" height="600" alt="Geschenkgutschein von Schichtatelier, Karte mit Logo und Wunschbetrag"></div>
      <div class="product-info">
        <h1>Geschenkgutschein</h1>
        <p class="price">ab 10,00 € <small>Wunschbetrag, kein Aufschlag, 3 Jahre gültig</small></p>
        <p>Für alle, die sich lieber selbst etwas aussuchen: Der Gutschein gilt für alle Artikel im Shop und für den Druckservice. Als gedruckte Karte per Post oder als PDF per E-Mail zum Selbstausdrucken, auf Wunsch mit persönlicher Nachricht.</p>
        <form class="form" id="gutscheinformular">
          <div class="alert" role="alert"></div>
          <fieldset style="border:0;padding:0;margin:0"><legend style="font-weight:600;margin-bottom:8px">Betrag</legend><div class="swatches" id="g-betraege">{amounts}</div></fieldset>
          <div class="field"><label for="g-frei">Anderer Betrag in Euro <span class="opt">(optional, mindestens 10)</span></label><input type="number" id="g-frei" name="betrag_frei" min="10" max="500" step="1" inputmode="numeric"><p class="msg"></p></div>
          <fieldset id="g-zustellung" style="border:0;padding:0;margin:0"><legend style="font-weight:600;margin-bottom:8px">Zustellung</legend>
            <label class="check"><input type="radio" name="zustellung" value="E-Mail (PDF)" checked> Per E-Mail als PDF, meist am selben Werktag</label>
            <label class="check"><input type="radio" name="zustellung" value="Post (Karte)"> Als gedruckte Karte per Post, versandkostenfrei</label>
          </fieldset>
          <div class="row">
            <div class="field"><label for="g-fuer">Für wen? <span class="opt">(Name auf dem Gutschein)</span></label><input type="text" id="g-fuer" name="empfaenger" maxlength="60"><p class="msg"></p></div>
            <div class="field"><label for="g-von">Von <span class="opt">(optional)</span></label><input type="text" id="g-von" name="absender" maxlength="60"><p class="msg"></p></div>
          </div>
          <div class="field"><label for="g-msg">Persönliche Nachricht <span class="opt">(optional, bis 200 Zeichen)</span></label><textarea id="g-msg" name="gutscheintext" rows="3" maxlength="200"></textarea><p class="msg"></p></div>
          <h2 class="sub" style="margin:8px 0 0">Ihre Daten</h2>
          <div class="row">
            <div class="field"><label for="g-name">Ihr Name</label><input type="text" id="g-name" name="name" required autocomplete="name" data-err="Bitte Ihren Namen eintragen."><p class="msg"></p></div>
            <div class="field"><label for="g-email">Ihre E-Mail <span class="opt">(für Bestätigung und Gutschein)</span></label><input type="email" id="g-email" name="email" required autocomplete="email" data-err="Bitte Ihre E-Mail-Adresse eintragen."><p class="msg"></p></div>
          </div>
          <div class="field" id="g-adresse" hidden><label for="g-adr">Postanschrift für die Karte</label><input type="text" id="g-adr" name="anschrift" autocomplete="street-address"><p class="msg"></p></div>
          <div class="field hp" aria-hidden="true"><label for="g-web">Website</label><input type="text" id="g-web" name="website" tabindex="-1" autocomplete="off"></div>
          <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir den Gutschein nicht ausstellen."><span>Ich bin einverstanden, dass meine Angaben zur Ausstellung des Gutscheins gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
          <button class="btn btn-primary" type="submit">Gutschein zahlungspflichtig bestellen</button>
          <dl class="konditionen"><dt>Gültigkeit</dt><dd>3 Jahre</dd><dt>Einlösbar</dt><dd>Shop und Druckservice</dd><dt>Code</dt><dd>nach Zahlungseingang per E-Mail oder Post</dd></dl>
        </form>
      </div>
    </div>
  </div>
</section>
"""
    page("gutschein.html", f"Geschenkgutschein · {C.MARKE}", "Geschenkgutschein für 3D-gedruckte Artikel und Druckservice bei Schichtatelier: Wunschbetrag ab 10 €, per E-Mail oder als Karte per Post, 3 Jahre gültig.", body, "shop")


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
        <div id="cross-sell" hidden><h2 class="sub" style="margin-top:32px">Dazu passt</h2><div class="grid grid-small" id="cross-sell-grid"></div></div>
        <form class="form" id="bestellformular" style="margin-top:32px" hidden>
          <h2>Lieferung und Zahlung</h2>
          <p class="muted small">Sie bestellen verbindlich. Der Vertrag kommt mit unserer Bestätigung per E-Mail zustande. Bei Versand erhalten Sie damit den PayPal-Zahlungslink, gedruckt wird nach Zahlungseingang. Bei Abholung zahlen Sie vor Ort.</p>
          <div class="alert" role="alert"></div>
          <div class="field"><label for="b-name">Vor- und Nachname</label><input type="text" id="b-name" name="name" required autocomplete="name" data-err="Bitte Ihren Namen eintragen."><p class="msg"></p></div>
          <div class="row">
            <div class="field"><label for="b-email">E-Mail <span class="opt">(für die Bestätigung)</span></label><input type="email" id="b-email" name="email" required autocomplete="email" data-err="Bitte Ihre E-Mail-Adresse eintragen."><p class="msg"></p></div>
            <div class="field"><label for="b-tel">Telefon <span class="opt">(optional, für Rückfragen)</span></label><input type="tel" id="b-tel" name="telefon" autocomplete="tel"><p class="msg"></p></div>
          </div>
          <fieldset style="border:0;padding:0;margin:0"><legend style="font-weight:600;margin-bottom:8px">Lieferung</legend>
            <label class="check"><input type="radio" name="lieferart" value="versand" checked> Versand innerhalb Deutschlands ({EUR(VERSAND_PAUSCHALE)}, ab {EUR(VERSANDFREI_AB)} kostenlos)</label>
            <label class="check"><input type="radio" name="lieferart" value="abholung"> Abholung in Celle, kostenlos ({E(C.STRASSE)}, nach Terminabsprache)</label>
          </fieldset>
          <div id="adresse-felder">
          <div class="field"><label for="b-strasse">Straße und Hausnummer</label><input type="text" id="b-strasse" name="strasse" required autocomplete="street-address" data-err="Bitte die Straße eintragen."><p class="msg"></p></div>
          <div class="row">
            <div class="field"><label for="b-plz">PLZ</label><input type="text" id="b-plz" name="plz" required inputmode="numeric" autocomplete="postal-code" data-err="Bitte die Postleitzahl eintragen."><p class="msg"></p></div>
            <div class="field"><label for="b-ort">Ort</label><input type="text" id="b-ort" name="ort" required autocomplete="address-level2" data-err="Bitte den Ort eintragen."><p class="msg"></p></div>
          </div>
          </div>
          <fieldset style="border:0;padding:0;margin:0"><legend style="font-weight:600;margin-bottom:8px">Zahlung</legend>
            <label class="check"><input type="radio" name="zahlungsart" value="paypal" checked> PayPal, mit Käuferschutz {"(Zahlungslink direkt nach dem Absenden)" if C.PAYPAL_ME else "(Zahlungslink kommt mit der Bestätigung per E-Mail)"}</label>
            <label class="check" id="zahlung-abholung" hidden><input type="radio" name="zahlungsart" value="abholung"> Bei Abholung, bar oder per PayPal vor Ort</label>
          </fieldset>
          <div class="field" id="gutscheincode-box" hidden><label for="b-code">Gutscheincode <span class="opt">(optional)</span></label><div class="code-row"><input type="text" id="b-code" autocomplete="off" autocapitalize="characters" maxlength="40"><button class="btn btn-ghost" type="button" id="code-pruefen">Einlösen</button></div><p class="code-msg" id="code-msg" role="status"></p></div>
          <div class="field"><label for="b-anm">Anmerkung <span class="opt">(optional)</span></label><textarea id="b-anm" name="anmerkung" rows="3"></textarea><p class="msg"></p></div>
          <div class="field hp" aria-hidden="true"><label for="b-web">Website</label><input type="text" id="b-web" name="website" tabindex="-1" autocomplete="off"></div>
          <div class="field"><label class="check"><input type="checkbox" name="agb" value="ja" required data-err="Bitte die AGB und die Widerrufsbelehrung bestätigen."><span>Ich habe die <a href="agb.html">AGB</a> und die <a href="widerruf.html">Widerrufsbelehrung</a> gelesen und akzeptiere sie.</span></label><p class="msg"></p></div>
          <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir die Bestellung nicht bearbeiten."><span>Ich bin einverstanden, dass meine Angaben zur Bearbeitung der Bestellung gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
          <button class="btn btn-primary btn-block" type="submit">Zahlungspflichtig bestellen</button>
          <p class="small muted">Klappt das Senden nicht? <a id="cart-mail" href="mailto:{E(C.EMAIL)}">Bestellung per E-Mail schicken</a> oder anrufen: <a href="{TEL_HREF}">{E(C.TELEFON)}</a>.</p>
        </form>
      </div>
      <div class="summary" id="cart-summary" hidden>
        <h2 class="sub" style="margin:0 0 .6em">Zusammenfassung</h2>
        <div class="line"><span>Zwischensumme</span><strong id="s-zwischen">0,00 €</strong></div>
        <div class="line"><span id="s-versand-label">Versand ({E(C.VERSANDLAND)})</span><strong id="s-versand">0,00 €</strong></div>
        <div class="line" id="s-gutschein-row" hidden><span>Gutschein</span><strong id="s-gutschein">−0,00 €</strong></div>
        <div class="line total"><span id="s-gesamt-label">Gesamt</span><span id="s-gesamt">0,00 €</span></div>
        <p class="small muted" id="s-hint"></p>
        <p class="small" data-delivery>Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>
        <p class="small muted">{'Keine Umsatzsteuer nach § 19 UStG.' if C.KLEINUNTERNEHMER else 'Alle Preise inkl. gesetzlicher MwSt.'} Produktion {E(C.PRODUKTIONSZEIT)} plus Versand {E(C.LIEFERZEIT)}.</p>
        <a class="btn btn-ghost btn-block" href="shop.html">Weiter einkaufen</a>
      </div>
    </div>
  </div>
</section>
"""
    page("warenkorb.html", f"Warenkorb · {C.MARKE}", "Warenkorb und Bestellung bei Schichtatelier: Artikel prüfen, Versand oder Abholung in Celle wählen, per PayPal bezahlen.", body, "", "", '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- Kontakt / eigenes Modell
def build_contact():
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Eigene Datei drucken lassen</h1>
    <p class="lead">Beschreiben Sie, was Sie brauchen: eine Datei, ein kaputtes Teil oder nur die Idee. Sie bekommen Preis und Lieferzeit, bevor gedruckt wird.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap kontakt-grid">
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
        <div class="field"><label for="k-mat">Material <span class="opt">(optional)</span></label><select id="k-mat" name="material"><option>Egal, bitte empfehlen</option>{"".join(f'<option>{E(m["name"])} ({E(m["einsatz"])})</option>' for m in MATERIALIEN)}</select><p class="msg"></p></div>
      </div>
      <div class="field"><label for="k-msg">Beschreibung <span class="opt">(Maße, Einsatzzweck, Farbe)</span></label><textarea id="k-msg" name="nachricht" required data-err="Bitte beschreiben Sie kurz Ihr Vorhaben."></textarea><p class="msg"></p></div>
      <div class="field hp" aria-hidden="true"><label for="k-web">Website</label><input type="text" id="k-web" name="website" tabindex="-1" autocomplete="off"></div>
      <div class="field"><label class="check"><input type="checkbox" name="einwilligung" value="ja" required data-err="Ohne Einwilligung können wir die Anfrage nicht bearbeiten."><span>Ich bin einverstanden, dass meine Angaben zur Bearbeitung der Anfrage gespeichert werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>.</span></label><p class="msg"></p></div>
      <button class="btn btn-primary" type="submit">Anfrage senden</button>
    </form>
    <div>
      <div class="kontakt-info">
        <h2>Direkt erreichen</h2>
        <p><a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a><br><a href="{TEL_HREF}">{E(C.TELEFON)}</a></p>
        <p class="small muted" style="margin:0">{E(C.STRASSE)}, {E(C.PLZ_ORT)}. Abholung nach Terminabsprache.</p>
      </div>
      <div class="kontakt-info">
        <h2>Was sich drucken lässt</h2>
        <ul class="small">
          <li>Bis 25 cm Kantenlänge am Stück</li>
          <li><a href="materialien.html">{", ".join(m["name"] for m in MATERIALIEN)}</a></li>
          <li>Schichthöhe 0,12 bis 0,28 mm</li>
          <li>Dateien als STL, 3MF, STEP oder OBJ</li>
        </ul>
      </div>
    </div>
  </div>
</section>
"""
    page("kontakt.html", f"Eigene Datei drucken lassen · {C.MARKE}", "Eigene STL-Datei, Ersatzteil oder Kleinserie anfragen: Preis und Lieferzeit vor dem Druck, gedruckt in Celle.", body, "kontakt")


# ---------------------------------------------------------------- Über uns
def build_about():
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Das Atelier von {E(C.INHABER)} in Celle.</h1>
    <p class="lead">{E(C.MARKE)} druckt kleine Dinge erst dann, wenn jemand sie bestellt. Gedruckt wird auf einem Bambu Lab X1 Carbon.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap prose">
    <h2>Der Drucker</h2>
    <p>Der X1 Carbon hat einen geschlossenen Bauraum. Darin lassen sich neben PLA und PETG auch ABS und TPU drucken, Teile bis 25 cm Kantenlänge am Stück. Die Schichtlinien, die dabei entstehen, gehören zum Verfahren. Sie bleiben am fertigen Teil sichtbar.</p>
    <h2>Was hier entsteht</h2>
    <p>Deko und Geschenke im Shop, dazu Teile nach Ihrer Datei oder Ihrer Beschreibung. Stückzahlen ab eins. Was der Shop zeigt, ist wirklich vorhanden und wird nach der Bestellung gedruckt, nicht aus einem Lager geholt.</p>
    <h2>So erreichen Sie uns</h2>
    <p>{E(C.STRASSE)}, {E(C.PLZ_ORT)}<br><a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a><br><a href="{TEL_HREF}">{E(C.TELEFON)}</a></p>
    <p>Abholung ist nach Terminabsprache möglich. Für eigene Dateien und Ersatzteile nutzen Sie das <a href="kontakt.html">Anfrageformular</a>.</p>
  </div>
</section>
"""
    page("ueber-uns.html", f"Über uns · {C.MARKE}", "Schichtatelier in Celle: 3D-Druck auf einem Bambu Lab X1 Carbon, kleine Stückzahlen nach Bestellung, Deko, Geschenke und Teile nach eigener Datei.", body, "ueber")


# ---------------------------------------------------------------- Versand & Zahlung
def build_shipping():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <h1>Versand und Zahlung</h1>
    <h2>Versandkosten</h2>
    <table>
      <tr><th>Lieferland</th><th>Kosten</th><th>Versandfrei ab</th></tr>
      <tr><td>{E(C.VERSANDLAND)}</td><td>{EUR(VERSAND_PAUSCHALE)} pro Bestellung</td><td>{EUR(VERSANDFREI_AB)} Bestellwert</td></tr>
    </table>
    <p>Wir versenden als Päckchen oder Paket innerhalb Deutschlands. Sobald das Paket unterwegs ist, melden wir uns per E-Mail. Lieferungen in andere Länder sind auf Anfrage möglich, schreiben Sie uns vorher.</p>
    <h2>Abholung in Celle</h2>
    <p>Wer in der Nähe wohnt, spart den Versand: Im Warenkorb „Abholung“ wählen, wir melden uns per E-Mail, sobald Ihr Teil fertig ist, und vereinbaren einen Termin. Abholadresse: {E(C.STRASSE)}, {E(C.PLZ_ORT)}. Bezahlt wird bei Abholung bar oder per PayPal.</p>
    <h2>Lieferzeit</h2>
    <p>Alle Artikel werden nach Bestellung gedruckt. Rechnen Sie mit {E(C.PRODUKTIONSZEIT)} Produktion nach Zahlungseingang plus {E(C.LIEFERZEIT)} Versand. Bei personalisierten Artikeln stimmen wir den Text oder das Motiv vorher mit Ihnen ab, die Produktionszeit beginnt mit Ihrer Freigabe.</p>
    <h2>Zahlungsarten</h2>
    <ul>
      <li><strong>PayPal:</strong> Sie erhalten einen PayPal-Zahlungslink über den Gesamtbetrag, Käuferschutz von PayPal inklusive. Nach Zahlungseingang beginnt der Druck.</li>
      <li><strong>Abholung in Celle:</strong> Sie holen Ihre Bestellung bei uns ab ({E(C.STRASSE)}, {E(C.PLZ_ORT)}, nach Terminabsprache) und zahlen vor Ort bar oder per PayPal. Keine Versandkosten.</li>
    </ul>
    <div class="notice">Wir speichern keine Zahlungsdaten auf dieser Website. Die Zahlung läuft direkt über PayPal oder bei der Abholung.</div>
    <h2>Rückgabe</h2>
    <p>Für Lagerartikel aus dem Shop gilt das gesetzliche <a href="widerruf.html">Widerrufsrecht</a> von 14 Tagen. Personalisierte Artikel mit Wunschtext oder eigenem Foto sind davon ausgenommen. Kommt ein Teil beschädigt an, schicken Sie uns bitte ein Foto an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>. Wir klären dann, ob neu gedruckt oder erstattet wird.</p>
  </div>
</section>
"""
    page("versand.html", f"Versand und Zahlung · {C.MARKE}", f"Versandkosten {EUR(VERSAND_PAUSCHALE)}, versandfrei ab {EUR(VERSANDFREI_AB)}. Zahlung per PayPal oder Abholung in Celle, Lieferzeit und Rückgabe bei Schichtatelier.", body, "versand")


# ---------------------------------------------------------------- AGB
def build_agb():
    ust = ("Alle Preise sind Endpreise. Als Kleinunternehmer im Sinne von § 19 UStG wird keine Umsatzsteuer berechnet und ausgewiesen." if C.KLEINUNTERNEHMER
           else "Alle Preise verstehen sich inklusive der gesetzlichen Umsatzsteuer.")
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <h1>Allgemeine Geschäftsbedingungen</h1>
    <p class="muted">Stand: {datetime.date.today().strftime("%d.%m.%Y")}</p>
    <h2>1. Geltungsbereich</h2>
    <p>Diese AGB gelten für alle Bestellungen von Verbrauchern und Unternehmern über den Online-Shop von {E(C.FIRMA)}, {E(C.INHABER)}, {E(C.STRASSE)}, {E(C.PLZ_ORT)} (nachfolgend „wir“). Verbraucher ist jede natürliche Person, die ein Rechtsgeschäft zu Zwecken abschließt, die überwiegend weder ihrer gewerblichen noch ihrer selbständigen beruflichen Tätigkeit zugerechnet werden können.</p>
    <h2>2. Vertragsschluss</h2>
    <p>Die Darstellung der Artikel im Shop ist kein verbindliches Angebot, sondern eine Aufforderung zur Bestellung. Mit dem Klick auf „Zahlungspflichtig bestellen“ geben Sie ein verbindliches Angebot ab. Sie erhalten umgehend eine automatische Eingangsbestätigung mit Vorgangsnummer, diese ist noch keine Annahme. Der Vertrag kommt zustande, wenn wir Ihre Bestellung innerhalb von zwei Werktagen per E-Mail bestätigen und, bei Zahlung per PayPal, den Zahlungslink übersenden. Vor dem Absenden können Sie Ihre Eingaben im Warenkorb jederzeit prüfen und ändern. Der Vertragstext wird von uns gespeichert und Ihnen mit der Bestätigung zugeschickt. Vertragssprache ist Deutsch.</p>
    <h2>3. Preise und Versandkosten</h2>
    <p>{ust} Zusätzlich fallen Versandkosten in Höhe von {EUR(VERSAND_PAUSCHALE)} pro Bestellung innerhalb von {E(C.VERSANDLAND)} an; ab einem Bestellwert von {EUR(VERSANDFREI_AB)} liefern wir versandkostenfrei. Lieferungen in andere Länder nur nach vorheriger Absprache.</p>
    <h2>4. Zahlung</h2>
    <p>Bei Versand bieten wir Zahlung per PayPal (Zahlungslink) an. Der Gesamtbetrag ist innerhalb von 7 Tagen nach Erhalt der Bestätigung fällig; die Produktion beginnt nach Zahlungseingang. Geht innerhalb von 14 Tagen keine Zahlung ein, können wir vom Vertrag zurücktreten. Bei Abholung erfolgt die Zahlung bei Übergabe in bar oder per PayPal.</p>
    <h2>5. Fertigung und Lieferung</h2>
    <p>Alle Artikel werden nach Bestellung gefertigt. Die Produktionszeit beträgt in der Regel {E(C.PRODUKTIONSZEIT)} nach Zahlungseingang, bei personalisierten Artikeln nach Ihrer Freigabe des Textes oder Motivs. Hinzu kommt die Versandzeit von etwa {E(C.LIEFERZEIT)}. Die Lieferung erfolgt an die von Ihnen angegebene Adresse oder, wenn Sie Abholung gewählt haben, durch Übergabe an unserem Standort in Celle nach Terminabsprache. Bei Verbrauchern geht die Gefahr des zufälligen Untergangs mit Übergabe der Ware an Sie über. Abgeholt werden kann innerhalb von 14 Tagen nach unserer Fertigmeldung.</p>
    <h2>6. Beschaffenheit 3D-gedruckter Teile</h2>
    <p>Unsere Artikel entstehen im Schichtverfahren (FDM). Sichtbare Schichtlinien, leichte Farbabweichungen zwischen Filamentchargen und Maßtoleranzen von etwa ±0,3 mm sind verfahrensbedingt und stellen keinen Mangel dar. Abbildungen können Illustrationen oder Fotos eines Musterstücks sein. Angaben zu Belastbarkeit und Temperaturbeständigkeit sind Richtwerte für den üblichen Gebrauch.</p>
    <h2>7. Personalisierte Artikel</h2>
    <p>Bei Artikeln mit Wunschtext oder eigenem Foto senden wir Ihnen vor dem Druck eine Vorschau zur Freigabe. Für Rechtschreibung und Inhalt Ihres Textes sind Sie verantwortlich. Wir drucken keine Inhalte, die Rechte Dritter verletzen oder strafbar sind. Personalisierte Artikel sind vom Widerrufsrecht ausgenommen (§ 312g Abs. 2 Nr. 1 BGB).</p>
    <h2>8. Widerrufsrecht</h2>
    <p>Verbrauchern steht ein Widerrufsrecht nach den Bestimmungen der <a href="widerruf.html">Widerrufsbelehrung</a> zu.</p>
    <h2>8a. Geschenkgutscheine</h2>
    <p>Gutscheine werden nach Zahlungseingang mit einem Code ausgestellt und sind drei Jahre ab Ausstellung gültig. Sie sind für alle Artikel im Shop und für Leistungen des Druckservice einlösbar, eine Barauszahlung ist ausgeschlossen. Ein Restguthaben bleibt bis zum Ablauf erhalten. Für den Kauf eines Gutscheins gilt das Widerrufsrecht; ein bereits eingelöster Gutschein kann nicht widerrufen werden.</p>
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
    page("agb.html", f"AGB · {C.MARKE}", "Allgemeine Geschäftsbedingungen des Schichtatelier-Online-Shops: Vertragsschluss, Preise, Zahlung, Lieferung, Gewährleistung und Besonderheiten 3D-gedruckter Teile.", body)


# ---------------------------------------------------------------- Widerruf
def build_widerruf():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
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
      <div class="field"><label for="w-ware">Bestellte Waren und Vorgangsnummer</label><textarea id="w-ware" name="nachricht" required data-err="Bitte die Waren und die Vorgangsnummer angeben."></textarea><p class="msg"></p></div>
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
    page("widerruf.html", f"Widerrufsrecht · {C.MARKE}", "Widerrufsbelehrung und Widerrufsformular für Bestellungen im Schichtatelier-Shop. 14 Tage Widerrufsrecht, Ausnahme für personalisierte Artikel.", body)


# ---------------------------------------------------------------- Impressum
def build_imprint():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
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
    <p>Produktillustrationen, Logo und Grafiken: eigene Erstellung. Schriften „Abril Fatface“ (TypeTogether) und „Hanken Grotesk“ (Hanken Design Co.), jeweils SIL Open Font License, lokal eingebunden.</p>
  </div>
</section>
"""
    page("impressum.html", f"Impressum · {C.MARKE}", "Impressum und Anbieterkennzeichnung von Schichtatelier 3D-Druck.", body)


# ---------------------------------------------------------------- Datenschutz
def build_privacy():
    body = f"""<section class="section-tight">
  <div class="wrap prose">
    <h1>Datenschutzerklärung</h1>
    <p class="muted">Stand: {datetime.date.today().strftime("%d.%m.%Y")}</p>
    <h2>1. Verantwortlicher</h2>
    <p>{E(C.FIRMA)}, {E(C.INHABER)}, {E(C.STRASSE)}, {E(C.PLZ_ORT)}<br>Telefon: {E(C.TELEFON)}, E-Mail: <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a></p>
    <h2>2. Hosting und Server-Logs</h2>
    <p>Diese Website wird bei Markentrix gehostet. Beim Aufruf speichert der Server automatisch Zugriffsdaten (aufgerufene Seite, Datum und Uhrzeit, übertragene Datenmenge, Browsertyp, Betriebssystem, verweisende Seite, IP-Adresse) in Protokolldateien. Diese Daten dienen der Sicherheit und dem störungsfreien Betrieb und werden nach spätestens 14 Tagen gelöscht. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse am sicheren Betrieb). Mit Markentrix besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO.</p>
    <h2>3. Bestellungen über den Shop</h2>
    <p>Wenn Sie bestellen, erheben wir Name, E-Mail-Adresse, Lieferadresse, gewählte Zahlungsart, die bestellten Artikel und gegebenenfalls Telefonnummer, Wunschtexte und Anmerkungen. Die Daten werden über das Markentrix-Portal an uns übermittelt und dort gespeichert; Sie erhalten eine Eingangsbestätigung mit Vorgangsnummer an die angegebene E-Mail-Adresse. Wir verwenden die Daten zur Vertragsabwicklung, Rechnungsstellung und Lieferung (Art. 6 Abs. 1 lit. b DSGVO). Die Lieferadresse geben wir an den Versanddienstleister weiter. Rechnungsdaten bewahren wir nach den steuer- und handelsrechtlichen Fristen bis zu zehn Jahre auf.</p>
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
    <p>Markentrix (Hosting und Portal, Auftragsverarbeitung), Versanddienstleister, PayPal (bei gewählter Zahlungsart), Steuerberatung und Finanzbehörden (Rechnungsdaten, soweit gesetzlich erforderlich). Eine Übermittlung in Drittländer findet durch uns nicht statt; PayPal kann Daten nach seiner eigenen Datenschutzerklärung übermitteln.</p>
    <h2>11. Ihre Rechte</h2>
    <p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch (Art. 21). Eine erteilte Einwilligung können Sie jederzeit mit Wirkung für die Zukunft widerrufen. Außerdem haben Sie das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren. Wenden Sie sich dafür an die oben genannte Kontaktadresse.</p>
    <h2>12. Datensicherheit</h2>
    <p>Die Übertragung aller Daten erfolgt verschlüsselt über HTTPS.</p>
  </div>
</section>
"""
    page("datenschutz.html", f"Datenschutz · {C.MARKE}", "Datenschutzerklärung von Schichtatelier: Hosting bei Markentrix, Bestell- und Kontaktformular, Warenkorb, PayPal, Google-Bewertungen und Statistik ohne Cookies.", body)


# ---------------------------------------------------------------- Danke / 404
def build_thanks():
    body = f"""<section class="danke" id="danke">
  <div class="wrap">
    <h1 id="danke-h1">Danke, Ihre Bestellung ist eingegangen.</h1>
    <div data-show="bestellung">
      <p class="lead">Sie erhalten in wenigen Minuten eine Eingangsbestätigung per E-Mail. Innerhalb von zwei Werktagen melden wir uns mit der Bestätigung.</p>
    </div>
    <div data-show="widerruf" data-h1="Danke, Ihr Widerruf ist eingegangen." hidden>
      <p class="lead">Sie erhalten eine Eingangsbestätigung per E-Mail. Wir melden uns innerhalb von zwei Werktagen mit den nächsten Schritten zur Rücksendung und Erstattung.</p>
    </div>
    <div data-show="gutschein" data-h1="Danke, Ihre Gutschein-Bestellung ist eingegangen." hidden>
      <p class="lead">Sie erhalten eine Eingangsbestätigung per E-Mail. Nach Zahlungseingang schicken wir den Gutschein mit Code als PDF oder als Karte per Post.</p>
    </div>
    <div data-show="kontakt" data-h1="Danke, Ihre Anfrage ist eingegangen." hidden>
      <p class="lead">Sie erhalten eine Eingangsbestätigung per E-Mail. Wir melden uns mit Preis und Lieferzeit.</p>
    </div>
    <div class="ref-card"><span class="small">Ihre Vorgangsnummer, bitte bei Rückfragen angeben</span><span class="ref" id="ref"></span></div>
    <p hidden><a class="btn btn-primary" id="paypal-link" href="#" rel="noopener">Jetzt <span id="danke-summe"></span> per PayPal bezahlen</a></p>
    <p class="notice" id="paypal-hinweis" hidden>Den PayPal-Zahlungslink über den Gesamtbetrag erhalten Sie mit der Bestätigung per E-Mail. Nach Zahlungseingang beginnt der Druck.</p>
    <p class="notice" id="gutschein-hinweis" hidden></p>
    <p class="notice" id="abhol-hinweis" hidden>Sie holen in Celle ab: Wir melden uns per E-Mail, sobald Ihr Teil fertig ist, und vereinbaren einen Termin. Abholadresse {E(C.STRASSE)}, {E(C.PLZ_ORT)}. Bezahlt wird bei Abholung bar oder per PayPal.</p>
  </div>
</section>
<section class="section-tight" data-show="bestellung">
  <div class="wrap">
    <h2>Wie es weitergeht</h2>
    <ol class="ablauf">
      <li><h3>Bestätigung</h3><p>Wir prüfen Ihre Bestellung und melden uns per E-Mail, bei PayPal mit dem Zahlungslink.</p></li>
      <li><h3>Druck</h3><p>Nach Zahlungseingang drucken wir Ihr Teil, Richtwert {E(C.PRODUKTIONSZEIT)}.</p></li>
      <li><h3>Versand oder Abholung</h3><p>Sie bekommen eine Nachricht, sobald das Paket unterwegs ist oder zur Abholung bereitsteht.</p></li>
    </ol>
  </div>
</section>
<section class="section-tight">
  <div class="wrap">
    <p class="small muted">Keine E-Mail erhalten? Prüfen Sie den Spam-Ordner oder schreiben Sie an <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>.</p>
    <p><a class="btn btn-ghost" href="shop.html">Zurück zum Shop</a></p>
  </div>
</section>
"""
    page("danke.html", f"Danke · {C.MARKE}", "Bestätigung: Ihre Bestellung oder Anfrage bei Schichtatelier ist eingegangen.", body, "", "", '<meta name="robots" content="noindex">')


def build_404():
    body = f"""<section class="danke">
  <div class="wrap">
    <h1>Diese Schicht fehlt noch.</h1>
    <p class="lead">Die Seite gibt es nicht oder der Artikel ist nicht mehr im Shop. Vielleicht hilft einer dieser Wege.</p>
    <div class="lost-links">
      <a href="shop.html"><strong>Shop</strong><span>Alle Artikel, auf Bestellung gedruckt</span></a>
      <a href="druckservice.html"><strong>Druckservice</strong><span>Eigene Datei oder Ersatzteil anfragen</span></a>
      <a href="faq.html"><strong>Fragen und Antworten</strong><span>Lieferung, Material, Rückgabe</span></a>
      <a href="kontakt.html"><strong>Kontakt</strong><span>Schreiben oder anrufen</span></a>
    </div>
  </div>
</section>
"""
    page("404.html", f"Seite nicht gefunden · {C.MARKE}", "Die aufgerufene Seite existiert nicht.", body, "", "", '<meta name="robots" content="noindex">')


# ---------------------------------------------------------------- Daten, Sitemap, Robots, Manifest
def build_data():
    data = [dict(id=p["id"], name=p["name"], preis=p["preis"], kat=p["kat"], text=bool(p.get("text")), textlabel=p.get("textlabel", ""), farben=p["farben"], kurz=p["kurz"], lang=p["lang"], material=p["material"], masse=p["masse"], gewicht=p["gewicht"], tags=p["tags"]) for p in AKTIV]
    cfg = dict(email=C.EMAIL, telefon=C.TELEFON, paypalMe=C.PAYPAL_ME, versandPauschale=VERSAND_PAUSCHALE, versandfreiAb=VERSANDFREI_AB, produktionMin=2, produktionMax=4, versandMin=2, versandMax=3, marke=C.MARKE, abholung=True, produktion=C.PRODUKTIONSZEIT,
               preishinweis=("Endpreis, keine Umsatzsteuer nach § 19 UStG" if C.KLEINUNTERNEHMER else "inkl. MwSt."))
    farben = {k: [v[0], v[1]] for k, v in FARBEN.items()}
    with open(os.path.join(ROOT, "assets", "js", "produkte.js"), "w", encoding="utf-8") as f:
        f.write("/* generiert von build/build.py */\n")
        f.write("window.SW_CONFIG=" + json.dumps(cfg, ensure_ascii=False) + ";\n")
        f.write("window.SW_FARBEN=" + json.dumps(farben, ensure_ascii=False) + ";\n")
        f.write("window.SW_PRODUKTE=" + json.dumps(data, ensure_ascii=False) + ";\n")
        f.write("window.SW_KATEGORIEN=" + json.dumps(KAT_AKTIV, ensure_ascii=False) + ";\n")
        f.write("window.SW_STATIC=" + json.dumps([p["id"] for p in AKTIV]) + ";\n")
    pages = ["index.html", "shop.html", "druckservice.html", "materialien.html", "faq.html", "kontakt.html", "versand.html", "ueber-uns.html", "agb.html", "widerruf.html", "impressum.html", "datenschutz.html", "gutschein.html"] + [f"material/{m['id']}.html" for m in MATERIALIEN] + [f"produkt/{p['id']}.html" for p in AKTIV]
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in pages:
            f.write(f"  <url><loc>/{u}</loc><lastmod>{TODAY}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /warenkorb.html\nDisallow: /danke.html\n")
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump({"name": f"{C.MARKE} {C.CLAIM}", "short_name": C.MARKE, "start_url": "index.html", "display": "browser",
                   "background_color": "#f6f4ef", "theme_color": "#b8763f",
                   "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]}, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- Materialien
def build_materials():
    rows = "".join(
        f'<li><a href="material/{m["id"]}.html"><span class="mname">{E(m["name"])}</span><span class="muse">{E(m["einsatz"])}</span><span class="mtemp">{E(m["temp"])}</span></a></li>'
        for m in MATERIALIEN)
    head_row = "".join(f'<th scope="col"><a href="material/{m["id"]}.html">{E(m["name"])}</a></th>' for m in MATERIALIEN)
    trs = "".join(f'<tr><th scope="row">{E(k)}</th>' + "".join(f"<td>{E(vals[m['id']])}</td>" for m in MATERIALIEN) + "</tr>" for k, vals in VERGLEICH)
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Welches Material passt zu Ihrem Teil?</h1>
    <p class="lead">Vier Kunststoffe decken fast alles ab, was im Alltag gedruckt wird. Hier steht, wofür welcher taugt und wo seine Grenzen liegen.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap"><ul class="materialliste">{rows}</ul></div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Im Vergleich</h2>
    <div class="table-scroll"><table class="compare"><thead><tr><th scope="col"><span class="sr-only">Eigenschaft</span></th>{head_row}</tr></thead><tbody>{trs}</tbody></table></div>
    <p class="small muted">Richtwerte für Standard-Filamente bei 0,2 mm Schichthöhe. Den Preis für Ihr Teil nennen wir im Angebot.</p>
  </div>
</section>
{datei_band("Unsicher, welches Material?", "Beschreiben Sie Einsatzort und Belastung. Wir schlagen ein Material vor und nennen den Preis.", "Angebot anfordern", "kontakt.html")}
"""
    page("materialien.html", f"Materialien für den 3D-Druck · {C.MARKE}", "PLA, PETG, ABS und TPU im Vergleich: Wärmebeständigkeit, Festigkeit, Außeneinsatz, Detailtreue. Welches Material passt zu Ihrem 3D-Druck-Teil?", body, "material")

    mdir = os.path.join(ROOT, "material")
    if os.path.isdir(mdir):
        keep = {m["id"] + ".html" for m in MATERIALIEN}
        for f in os.listdir(mdir):
            if f not in keep: os.remove(os.path.join(mdir, f))
    for m in MATERIALIEN:
        rel = "../"
        props = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in m["eigenschaften"])
        gut = "".join(f"<li>{E(x)}</li>" for x in m["gut"])
        nicht = "".join(f"<li>{E(x)}</li>" for x in m["nicht"])
        faq = "".join(f'<details class="faq-item"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in m["faq"])
        others = "".join(
            f'<li><a href="{rel}material/{o["id"]}.html"><span class="mname">{E(o["name"])}</span><span class="muse">{E(o["einsatz"])}</span><span class="mtemp">{E(o["temp"])}</span></a></li>'
            for o in MATERIALIEN if o["id"] != m["id"])
        shop_examples = [p for p in AKTIV if m["name"] in p["material"]][:3]
        examples = ""
        if shop_examples:
            examples = f"""<section class="section-tight"><div class="wrap"><h2>Aus {E(m['name'])} im Shop</h2><div class="grid">{"".join(card(p, rel, k) for k, p in enumerate(shop_examples))}</div></div></section>"""
        body = f"""<section class="mat-head">
  <div class="wrap">
    <nav aria-label="Pfad" class="crumbs"><a href="../index.html">Start</a> › <a href="../materialien.html">Materialien</a> › {E(m['name'])}</nav>
    <h1>{E(m['titel'])}</h1>
    <p class="lead">{E(m['claim'])}</p>
    <p class="muted" style="max-width:36em">{E(m['kurz'])}</p>
    <a class="btn btn-primary" href="../kontakt.html">Angebot für {E(m['name'])}-Teile anfordern</a>
  </div>
</section>
<section class="section-tight">
  <div class="wrap mat-cols">
    <div>
      <h2>Eigenschaften</h2>
      <dl class="specs">{props}</dl>
      <h2>Druckparameter</h2>
      <dl class="specs"><dt>Schichthöhe</dt><dd>{E(m['schicht'])}</dd><dt>Düsentemperatur</dt><dd>{E(m['duesen'])}</dd><dt>Druckbett</dt><dd>{E(m['bett'])}</dd><dt>Dichte</dt><dd>{E(m['dichte'])}</dd></dl>
    </div>
    <div>
      <h2>Geeignet für</h2>
      <ul class="liste-ja">{gut}</ul>
      <h2>Nicht geeignet für</h2>
      <ul class="liste-nein">{nicht}</ul>
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
    <ul class="materialliste">{others}</ul>
  </div>
</section>
"""
        page(f"material/{m['id']}.html", f"{m['titel']} · {C.MARKE}", (m["claim"] + " " + m["kurz"])[:155], body, "material", rel)


# ---------------------------------------------------------------- Druckservice
def build_service():
    mats = ", ".join(f'<a href="material/{m["id"]}.html">{E(m["name"])}</a>' for m in MATERIALIEN)
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Ihre Datei, gedruckt in Celle.</h1>
    <p class="lead">Schicken Sie eine STL-, 3MF- oder STEP-Datei, ein Foto vom kaputten Teil oder eine Beschreibung. Sie erfahren Preis und Lieferzeit, bevor gedruckt wird.</p>
    <p><a class="btn btn-primary" href="kontakt.html">Angebot für meine Datei anfordern</a></p>
  </div>
</section>
<section class="section">
  <div class="wrap shop-block">
    <div class="side"><h2>Was sich drucken lässt</h2></div>
    <dl class="spaltenliste">
      <div><dt>Größe</dt><dd>Bis 25 cm Kantenlänge am Stück. Größeres besprechen wir einzeln.</dd></div>
      <div><dt>Material</dt><dd>{mats}. Der <a href="materialien.html">Vergleich</a> zeigt, was wofür taugt.</dd></div>
      <div><dt>Schichthöhe</dt><dd>0,12 bis 0,28 mm. Feinere Schichten dauern länger.</dd></div>
      <div><dt>Dateien</dt><dd>STL, 3MF, STEP oder OBJ in Millimetern, Modell geschlossen.</dd></div>
      <div><dt>Wandstärke</dt><dd>Mindestens 1,2 mm, bei TPU 2 mm.</dd></div>
      <div><dt>Stückzahl</dt><dd>Ab 1 Stück.</dd></div>
    </dl>
  </div>
</section>
<section class="section-tight">
  <div class="wrap shop-block">
    <div class="side"><h2>So läuft es</h2></div>
    <ol class="ablauf">
      <li><h3>Anfrage</h3><p>Formular ausfüllen. Die Datei schicken Sie per E-Mail an die Adresse aus unserer Antwort.</p></li>
      <li><h3>Prüfung und Preis</h3><p>Wir prüfen Wandstärken, Überhänge und Maße und nennen Preis und Liefertermin.</p></li>
      <li><h3>Druck</h3><p>Nach Ihrer Freigabe wird gedruckt.</p></li>
      <li><h3>Übergabe</h3><p>Versand innerhalb Deutschlands oder Abholung in Celle.</p></li>
    </ol>
  </div>
</section>
<section class="section">
  <div class="wrap shop-block">
    <div class="side"><h2>Was wir nicht drucken</h2></div>
    <p class="prose" style="margin:0">Keine Waffen oder Waffenteile, keine markengeschützten Teile zum Weiterverkauf und keine Teile, deren Versagen Menschen gefährden kann, etwa tragende Fahrzeugteile oder Druckbehälter.</p>
  </div>
</section>
"""
    page("druckservice.html", f"3D-Druckservice für eigene Dateien · {C.MARKE}", "Eigene Datei, Ersatzteil oder Kleinserie in PLA, PETG, ABS oder TPU drucken lassen: Preis und Lieferzeit vor dem Druck, ab 1 Stück.", body, "service")


# ---------------------------------------------------------------- FAQ
def build_faq():
    groups = ""
    for title, items in FAQ:
        groups += f'<h2>{E(title)}</h2>' + "".join(f'<details class="faq-item"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in items)
    body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Fragen und Antworten</h1>
    <p class="lead">Zu Bestellung, Material und Druckservice. Nicht dabei? <a href="kontakt.html">Schreiben Sie uns</a>.</p>
  </div>
</section>
<section class="section-tight">
  <div class="wrap prose">
    {groups}
  </div>
</section>
"""
    page("faq.html", f"Fragen und Antworten · {C.MARKE}", "Antworten zu Lieferzeit, Zahlung, Materialwahl, Dateiformaten, Rückgabe und Reklamation im Schichtatelier-Shop.", body, "faq")


if __name__ == "__main__":
    for fn in (build_data, build_index, build_shop, build_products, build_product_dyn, build_voucher, build_cart, build_contact, build_about, build_shipping, build_agb, build_widerruf, build_imprint, build_privacy, build_thanks, build_404, build_materials, build_service, build_faq):
        fn()
    n = sum(len(f) for _, _, f in os.walk(ROOT))
    print("Fertig:", n, "Dateien in", ROOT)
