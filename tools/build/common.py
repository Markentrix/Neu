# -*- coding: utf-8 -*-
import os
DEMO = os.environ.get("DEMO") == "1"
CSS_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "css", "style.css")
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.environ.get("OUT", os.path.join(_ROOT, "website-demo") + os.sep if DEMO else os.path.join(_ROOT, "website-fertig") + os.sep)
TEL = "05141 908650"
TEL_LINK = "tel:+495141908650"
WA_LINK = "https://wa.me/4915231394662"
MAIL = "team@celler-kartbahn.com"

ICONS = {
 "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.6a2 2 0 0 1-.5 2.1L8 9.7a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.8.3 1.7.5 2.6.7a2 2 0 0 1 1.7 2z"/></svg>',
 "wa": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.6.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 12 12 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.7 2.7 0 0 0 1.8-1.3 2.2 2.2 0 0 0 .2-1.3c-.1-.1-.2-.2-.5-.3z"/></svg>',
 "ticket": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9a3 3 0 0 1 0 6v3a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-3a3 3 0 0 1 0-6V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z"/><path d="M13 5v2M13 17v2M13 11v2"/></svg>',
 "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
 "flag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5"/></svg>',
 "kids": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><path d="M8 3.5 9.5 6M16 3.5 14.5 6"/></svg>',
 "building": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2M10 21v-3h4v3"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
 "gift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 12v10H4V12M2 7h20v5H2zM12 22V7M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7zM12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>',
 "speed": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 14l4-6"/><path d="M4.9 19a10 10 0 1 1 14.2 0"/></svg>',
 "ruler": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17 17 3l4 4L7 21zM7 13l2 2M10 10l2 2M13 7l2 2"/></svg>',
 "trophy": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 5M17 6h3a3 3 0 0 1-3 5"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 7 10-7"/></svg>',
 "camera": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 7l-7 5 7 5V7zM1 5h15v14H1z"/></svg>',
 "food": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4zM6 1v3M10 1v3M14 1v3"/></svg>',
 "school": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 10 12 5 2 10l10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
}

LOGO = '<svg class="brand__logo" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="9" fill="#e10600"/><path d="M8 29 20 9l12 20H8z" fill="#fff"/><path d="M14 29l6-10 6 10z" fill="#e10600"/><rect x="8" y="30" width="24" height="3" fill="#fff"/></svg>'

NAV = [("index.html","Startseite"),("preise.html","Preise"),("kinder.html","Kinder"),("firmen.html","Firmen &amp; Gruppen"),("kartbahn.html","Die Kartbahn"),("faq.html","FAQ"),("kontakt.html","Kontakt")]

def head(title, desc, jsonld="", img="assets/img/og-image.jpg", noindex=False):
    import re as _re
    title=_re.sub(r"&(?!amp;|#)", "&amp;", title); desc=_re.sub(r"&(?!amp;|#)", "&amp;", desc)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}
<meta name="theme-color" content="#0b0b0d">
<meta name="geo.region" content="DE-NI">
<meta name="geo.placename" content="Celle">
<meta name="geo.position" content="52.6088;10.0614">
<meta name="ICBM" content="52.6088, 10.0614">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="Burnout Celler-Kartbahn">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="/{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Kart-Duell auf der Indoor-Strecke der Burnout Celler-Kartbahn">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Burnout Celler-Kartbahn GmbH">
<meta name="format-detection" content="telephone=yes">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<link rel="stylesheet" href="assets/css/style.css">
{jsonld}
</head>
<body>
<a class="skip" href="#main">Zum Inhalt springen</a>
'''

def header():
    links = "".join(f'<li><a href="{h}">{t}</a></li>' for h,t in NAV)
    mlinks = "".join(f'<li><a href="{h}">{t}</a></li>' for h,t in NAV)
    return f'''<header class="header">
  <div class="wrap">
    <a class="brand" href="index.html" title="Zur Startseite"><img class="brand__img" src="assets/img/logo.webp" width="264" height="84" alt="Burnout Celler-Kartbahn" fetchpriority="low"></a>
    <nav class="nav" aria-label="Hauptnavigation"><ul>{links}<li><a class="btn btn--primary btn--sm" href="buchen.html">Jetzt buchen</a></li><li><a class="btn btn--ghost btn--sm" href="gutscheine.html">Gutscheine</a></li></ul></nav>
    <button class="burger" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="Menü öffnen"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  </div>
</header>
<nav class="mobile-nav" id="mobile-nav" data-open="false" aria-label="Mobile Navigation">
  <ul>{mlinks}<li><a href="gutscheine.html">Gutscheine &amp; Tickets vorab</a></li><li><a href="agb.html">AGB</a></li></ul>
  <a class="btn btn--primary btn--block" href="buchen.html">Jetzt online buchen</a>
</nav>
<main id="main">
'''

def footer():
    return f'''</main>
<footer class="footer">
  <div class="wrap">
    <div class="grid grid-4">
      <div>
        <img class="footer__logo" src="assets/img/logo.webp" width="264" height="84" alt="Burnout Celler-Kartbahn" loading="lazy" decoding="async">
        <h2>Burnout Celler-Kartbahn GmbH</h2>
        <ul>
          <li>Waldweg 100<br>29221 Celle</li>
          <li><a href="{TEL_LINK}">Tel. {TEL}</a></li>
          <li><a href="mailto:{MAIL}">{MAIL}</a></li>
          <li><a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp schreiben</a></li>
        </ul>
      </div>
      <div>
        <h2>Öffnungszeiten</h2>
        <ul>
          <li>Mo–Fr: ab 15:00 Uhr (Ferien ab 13:00)</li>
          <li>Samstag: ab 13:00 Uhr</li>
          <li>Sonntag: ab 11:00 Uhr</li>
          <li class="small">Open End – Ende je nach Auslastung. Vor spontanem Besuch bitte kurz anrufen.</li>
        </ul>
      </div>
      <div>
        <h2>Schnell zu</h2>
        <ul>
          <li><a href="buchen.html">Online buchen</a></li>
          <li><a href="gutscheine.html">Gutscheine &amp; Tickets</a></li>
          <li><a href="preise.html">Preise</a></li>
          <li><a href="kinder.html">Kindergeburtstage</a></li>
          <li><a href="firmen.html">Firmenevents</a></li>
          <li><a href="faq.html">Häufige Fragen</a></li>
        </ul>
      </div>
      <div>
        <h2>Downloads</h2>
        <ul>
          <li><a href="downloads/haftungsausschluss-minderjaehrige.pdf">Einverständniserklärung für Minderjährige (PDF)</a></li>
          <li><a href="downloads/flyer-burnout-celler-kartbahn.pdf">Flyer (PDF, 6&nbsp;MB)</a></li>
          <li><a href="downloads/buffet-2026-2027.jpg">Buffetangebot 2026/2027 (Bild)</a></li>
          <li><a href="https://www.facebook.com/BurnoutCellerKartbahn/" rel="noopener" target="_blank">Facebook</a></li>
          <li><a href="https://www.dartraum-celle.de" rel="noopener" target="_blank">Dartraum Celle</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <div class="footer__legal">
        <a href="impressum.html">Impressum</a>
        <a href="datenschutz.html">Datenschutz</a>
        <a href="agb.html">AGB</a>
        <a href="widerruf.html">Widerruf</a>
        <span data-mk="cookies"></span>
      </div>
      <div>© Burnout Celler-Kartbahn GmbH · Celle</div>
    </div>
  </div>
</footer>
<div class="actionbar" aria-label="Schnellkontakt">
  <a class="btn btn--ghost" href="{TEL_LINK}">{ICONS["phone"]}Anrufen</a>
  <a class="btn btn--wa" href="{WA_LINK}" rel="noopener" target="_blank">{ICONS["wa"]}WhatsApp</a>
  <a class="btn btn--primary" href="buchen.html">{ICONS["cal"]}Jetzt buchen</a>
</div>
<script src="assets/js/main.js" defer></script>
'''

def end(extra_js=""):
    return f'{extra_js}\n</body>\n</html>\n'

def fallback_box(text="Keine Antwort vom Server? Ihr erreicht uns jederzeit direkt:"):
    return f'''<div class="fallback" hidden>
  <strong>{text}</strong>
  <div class="btns">
    <a class="btn btn--ghost btn--sm" href="{TEL_LINK}">{ICONS["phone"]}{TEL}</a>
    <a class="btn btn--wa btn--sm" href="{WA_LINK}" rel="noopener" target="_blank">{ICONS["wa"]}WhatsApp</a>
    <a class="btn btn--ghost btn--sm" href="mailto:{MAIL}">{ICONS["mail"]}E-Mail</a>
  </div>
</div>'''

def contact_strip():
    return f'''<section class="cta-band">
  <div class="wrap grid grid-2" style="align-items:center">
    <div>
      <h2>Fragen? Wir sind da.</h2>
      <p>Telefonisch während der Öffnungszeiten, per WhatsApp oder E-Mail – wir antworten schnell.</p>
    </div>
    <div class="pill-row" style="justify-content:flex-start">
      <a class="btn btn--light" href="{TEL_LINK}">{ICONS["phone"]}{TEL}</a>
      <a class="btn btn--ghost" style="border-color:#fff" href="{WA_LINK}" rel="noopener" target="_blank">{ICONS["wa"]}WhatsApp</a>
      <a class="btn btn--ghost" style="border-color:#fff" href="mailto:{MAIL}">{ICONS["mail"]}E-Mail</a>
    </div>
  </div>
</section>'''

def breadcrumb(name, file):
    return f'''<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Start","item":"/index.html"}},{{"@type":"ListItem","position":2,"name":"{name}","item":"/{file}"}}]}}</script>'''

HERO_MOBILE = {"hero-rennen":"strecke-start","hero-strecke":"strecke-boxengasse","hero-duell":"kart-detail","karts-boxengasse":"karts-boxengasse","strecke-start":"strecke-start","kartflotte":"karts-boxengasse"}
HAS_800 = {"hero-rennen","hero-strecke","hero-duell","kart-sodi-front","anmeldung-theke","bistro-bar","zweite-ebene","kartflotte","karts-boxengasse","kart-detail","kart-motor","strecke-start","strecke-boxengasse","bistro-theke","bistro-lounge","veranstaltungsraum"}
def responsive(html):
    import re as _re
    html = _re.sub(r'<img class="hero__img" src="assets/img/([a-z0-9-]+)\.webp"[^>]*>', lambda m: (lambda name, tag: f'<picture><source media="(max-width: 700px)" srcset="assets/img/{(HERO_MOBILE.get(name,name)+"-800") if HERO_MOBILE.get(name,name) in HAS_800 else HERO_MOBILE.get(name,name)}.webp">{tag}</picture>')(m.group(1), m.group(0)), html)
    def srcset(m):
        tag = m.group(0); name = m.group(1)
        if "hero__img" in tag or name not in HAS_800 or "srcset" in tag: return tag
        w = _re.search(r'width="(\d+)"', tag); w = w.group(1) if w else "1400"
        sizes = "100vw" if "zweite-ebene" in name else "(min-width: 860px) 560px, 100vw"
        return tag[:-1] + f' srcset="assets/img/{name}-800.webp 800w, assets/img/{name}.webp {w}w" sizes="{sizes}">'
    html = _re.sub(r'<img [^>]*src="assets/img/([a-z0-9-]+)\.webp"[^>]*>', srcset, html)
    return html

def minify_css(css):
    import re as _re
    css = _re.sub(r"/\*.*?\*/", "", css, flags=_re.S)
    css = _re.sub(r"\s+", " ", css)
    css = _re.sub(r"\s*([{};])\s*", r"\1", css)
    return css.strip()

def page_jsonld(name, html):
    import re as _re, datetime, json as _json
    t = _re.search(r"<title>(.*?)</title>", html); d = _re.search(r'<meta name="description" content="(.*?)">', html)
    if not t or not d or name in ("danke.html", "404.html"): return ""
    typ = {"kontakt.html": "ContactPage", "faq.html": "FAQPage", "impressum.html": "AboutPage", "kartbahn.html": "AboutPage"}.get(name, "WebPage")
    if name == "faq.html": return ""
    obj = {"@context": "https://schema.org", "@type": typ, "@id": "/" + name + "#webpage", "url": "/" + name,
           "name": t.group(1).replace("&amp;", "&"), "description": d.group(1).replace("&amp;", "&"), "inLanguage": "de-DE",
           "isPartOf": {"@type": "WebSite", "name": "Burnout Celler-Kartbahn", "url": "/"},
           "about": {"@id": "/#kartbahn"}, "publisher": {"@id": "/#kartbahn"},
           "datePublished": "2026-10-28", "dateModified": datetime.date.today().isoformat(),
           "primaryImageOfPage": {"@type": "ImageObject", "url": "/assets/img/og-image.jpg", "width": 1200, "height": 630},
           "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".lead"]}}
    return '<script type="application/ld+json">' + _json.dumps(obj, ensure_ascii=False) + '</script>'

WATERMARK = None
def watermark():
    global WATERMARK
    if WATERMARK is None:
        import urllib.parse
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="420" height="260"><text x="210" y="150" text-anchor="middle" transform="rotate(-28 210 130)" '
               'font-family="Inter,Arial,sans-serif" font-size="30" font-weight="700" fill="#ffffff" fill-opacity="0.16">© Markentrix · Entwurf</text></svg>')
        uri = "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
        WATERMARK = ('<style>.mkwm{position:fixed;inset:0;z-index:9998;pointer-events:none;background:url("' + uri + '") repeat;background-size:420px 260px}'
          '.mkwm-badge{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(5.2rem + env(safe-area-inset-bottom,0px));z-index:9999;pointer-events:none;'
          'background:rgba(225,6,0,.92);color:#fff;font:700 .78rem/1.3 Inter,Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;padding:.45rem .9rem;border-radius:999px;box-shadow:0 6px 20px rgba(0,0,0,.5);white-space:nowrap}'
          '@media(min-width:1000px){.mkwm-badge{bottom:1rem;left:auto;right:1rem;transform:none}}</style>'
          '<div class="mkwm" aria-hidden="true"></div><div class="mkwm-badge" aria-hidden="true">Entwurf © Markentrix 2026 · Vorschau, nicht zur Weitergabe</div>')
    return WATERMARK

def ensure_assets():
    import shutil, os
    src = os.path.join(_ROOT, "website-fertig") + os.sep
    if os.path.abspath(OUT) != os.path.abspath(src):
        for d in ("assets", "downloads"):
            if os.path.isdir(OUT + d): shutil.rmtree(OUT + d)
            shutil.copytree(src + d, OUT + d)
        for f in ("favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            shutil.copy(src + f, OUT + f)
    if os.path.isdir(OUT + "assets/css"): shutil.rmtree(OUT + "assets/css")

def write(name, html):
    if name.endswith(".html"):
        html = responsive(html)
        if DEMO:
            import re as _re
            html = _re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex,nofollow,noarchive">', html)
            html = html.replace("</body>", watermark() + "</body>", 1)
        import os as _os
        if not _os.path.isdir(OUT + "assets"): ensure_assets()
        css = open(CSS_SRC, encoding="utf-8").read()
        html = html.replace('<link rel="stylesheet" href="assets/css/style.css">', "<style>" + minify_css(css).replace('url("/assets/fonts/', 'url("assets/fonts/') + "</style>")
        import re as _re
        m = _re.search(r'<picture><source media="\(max-width: 700px\)" srcset="([^"]+)"><img class="hero__img" src="([^"]+)"', html)
        if m:
            pre = f'<link rel="preload" as="image" href="{m.group(1)}" media="(max-width: 700px)" fetchpriority="high">\n<link rel="preload" as="image" href="{m.group(2)}" media="(min-width: 701px)" fetchpriority="high">\n'
            html = html.replace("</head>", pre + "</head>", 1)
        html = html.replace("</head>", page_jsonld(name, html) + "\n</head>", 1)
        html = "\n".join(l.strip() for l in html.splitlines() if l.strip())
    with open(OUT + name, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", name, len(html))
