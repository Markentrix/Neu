# -*- coding: utf-8 -*-
"""Ratgeber: Übersicht und Artikelseiten."""
import core
import md
import seo
from core import ESC, I


def de_date(iso):
    try:
        y, m, d = iso.split("-")
        return f"{d}.{m}.{y}"
    except Exception:
        return iso or ""


def build_index(site, write):
    prefix = "../"
    path = "/ratgeber/index.html"
    title = "Ratgeber Autopflege & Aufbereitung | ElbDetail Celle"
    desc = "Ratgeber aus Celle: Kosten der Fahrzeugaufbereitung, Leasingrückgabe, Lackpflege, Innenraum und Tipps für den Winter. Ehrlich und praxisnah erklärt."
    cats = []
    for a in site.articles:
        c = a.get("category", "Ratgeber")
        if c not in cats:
            cats.append(c)
    ld = [seo.webpage(site, path, title, {"@type": "CollectionPage"}),
          seo.crumbs(site, [("Startseite", "/"), ("Ratgeber", path)]),
          {"@context": "https://schema.org", "@type": "ItemList",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{site.url}/ratgeber/{a['slug']}.html", "name": a["title"]}
                               for i, a in enumerate(site.articles)]}]
    chips = '<button type="button" class="chip is-active" data-filter="">Alle</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{ESC(c)}">{ESC(c)}</button>' for c in cats)
    cards = "".join(f'''
        <a class="article-card" href="{a["slug"]}.html" data-cat="{ESC(a.get("category", ""))}">
          <span class="article-cat">{ESC(a.get("category", "Ratgeber"))}</span>
          <h2>{ESC(a["title"])}</h2>
          <p>{ESC(a.get("excerpt", ""))}</p>
          <span class="more">{a.get("readingTime", 5)} Min. · aktualisiert {de_date(a.get("updated") or a.get("date"))}</span>
        </a>''' for a in site.articles)
    winter = [a for a in site.articles if "winter" in a.get("category", "").lower()]
    winter_band = ""
    if winter:
        wl = "".join(f'<li><a href="{a["slug"]}.html">{ESC(a["title"])}</a></li>' for a in winter)
        winter_band = f'''
      <div class="winter-band">
        <div class="winter-band-copy">
          <p class="eyebrow">{I["snow"]}Winter-Spezial</p>
          <h2>Gut durch die kalte Jahreszeit.</h2>
          <p>Streusalz, Nässe und Frost: Unsere Tipps für Lack, Felgen und Innenraum im Winter.</p>
          <a class="btn btn-primary" href="winter.html">Zum Winter-Ratgeber</a>
        </div>
        <ul class="winter-band-list">{wl}<li><a href="{prefix}aktion/winterschutz.html">Aktion: Winter-Lackschutz</a></li></ul>
      </div>'''
    body = f'''
<main id="main">
  <section class="page-hero page-hero--compact" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Ratgeber", None)])}
      <p class="eyebrow">Ratgeber</p>
      <h1 id="page-h">Wissen aus der Werkstatt. <em>Ehrlich erklärt.</em></h1>
      <p class="lead">Antworten auf die Fragen, die wir in Celle jeden Tag hören: Was kostet eine Aufbereitung, was hilft vor der Leasingrückgabe, wie pflegen Sie Lack, Leder und Innenraum richtig?</p>
    </div>
  </section>
  <section class="tight-top" aria-label="Artikel">
    <div class="container">
{winter_band}
      <div class="chip-row" role="group" aria-label="Nach Thema filtern">{chips}</div>
      <div class="article-grid" id="articleGrid">{cards}</div>
    </div>
  </section>
{core.cta_band(site, prefix)}
</main>
'''
    write("ratgeber/index.html", core.head(site, title, desc, path, prefix=prefix, ld=ld) + core.header(site, prefix, current="ratgeber/index.html") + body + core.footer(site, prefix))

    if winter:
        build_winter_hub(site, write, winter)


def build_winter_hub(site, write, winter):
    """Winter-Ratgeber: Übersicht aller Winterartikel plus Winteraktion."""
    prefix = "../"
    path = "/ratgeber/winter.html"
    title = "Auto im Winter: Ratgeber für Lack & Innenraum | ElbDetail"
    desc = ("Winter-Ratgeber aus Celle: Auto winterfest machen, Streusalz richtig abwaschen und Feuchtigkeit im Innenraum vermeiden. "
            "Praxistipps von ElbDetail.")
    ld = [seo.webpage(site, path, title, {"@type": "CollectionPage"}),
          seo.crumbs(site, [("Startseite", "/"), ("Ratgeber", "/ratgeber/index.html"), ("Winter", path)]),
          {"@context": "https://schema.org", "@type": "ItemList",
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{site.url}/ratgeber/{a['slug']}.html", "name": a["title"]}
                               for i, a in enumerate(winter)]}]
    cards = "".join(f'''
        <a class="article-card" href="{a["slug"]}.html">
          <span class="article-cat">{ESC(a.get("category", "Winter"))}</span>
          <h2>{ESC(a["title"])}</h2>
          <p>{ESC(a.get("excerpt", ""))}</p>
          <span class="more">{a.get("readingTime", 5)} Min. · aktualisiert {de_date(a.get("updated") or a.get("date"))}</span>
        </a>''' for a in winter)
    tips = "".join(f"<li>{t}</li>" for t in [
        "<strong>Im Herbst versiegeln</strong>, bevor der erste Frost kommt. Dann haften Salz und Schmutz schlechter.",
        "<strong>Salz regelmäßig abspülen</strong>, auch Radkästen, Schweller und Unterboden.",
        "<strong>Bei Plusgraden waschen</strong> und Türdichtungen danach trocknen, damit nichts festfriert.",
        "<strong>Gummimatten nutzen</strong> und Textilmatten bei Nässe herausnehmen und trocknen lassen.",
        "<strong>Innenscheiben sauber halten</strong>, dann beschlagen sie deutlich weniger."])
    body = f'''
<main id="main">
  <section class="page-hero page-hero--compact page-hero--winter" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Ratgeber", "index.html"), ("Winter", None)])}
      <p class="eyebrow">Winter-Spezial</p>
      <h1 id="page-h">Ihr Auto im Winter. <em>Gut geschützt.</em></h1>
      <p class="lead">Streusalz, Matsch und Frost setzen Lack, Felgen und Innenraum stärker zu als jede andere Jahreszeit. Hier finden Sie alles, was Sie für die kalte Jahreszeit wissen müssen.</p>
      <div class="hero-actions"><a class="btn btn-primary btn-lg" href="{prefix}aktion/winterschutz.html">{I["snow"]}Winter-Lackschutz ansehen</a><a class="btn btn-line" href="{prefix}termin.html?quelle=winter-ratgeber">{I["cal"]}Termin anfragen</a></div>
    </div>
  </section>
  <section aria-labelledby="wtips-h">
    <div class="container two-up">
      <div class="prose">
        <h2 id="wtips-h">Die fünf wichtigsten Wintertipps</h2>
        <ul class="includes">{tips}</ul>
      </div>
      <aside class="sticky-aside">
        <div class="aside-card dark">
          <h3>Winter-Lackschutz in Celle</h3>
          <p>Glanzpolitur im Paket Signature ab {site.min_price("signature")} €, dazu eine Versiegelung vor dem ersten Streusalz. Ab dem Paket Essential bleibt Ihr Auto rund 24 Stunden bei uns und trocknet über Nacht in der Halle.</p>
          <a class="btn btn-primary" href="{prefix}aktion/winterschutz.html">Zur Winteraktion</a>
        </div>
      </aside>
    </div>
  </section>
  <section class="soft" aria-labelledby="wart-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Winter-Ratgeber</p><h2 id="wart-h" class="display">Alle Artikel für den Winter.</h2></div>
      <div class="article-grid">{cards}</div>
    </div>
  </section>
{core.cta_band(site, prefix)}
</main>
'''
    write("ratgeber/winter.html", core.head(site, title, desc, path, prefix=prefix, ld=ld) + core.header(site, prefix, current="ratgeber/index.html") + body + core.footer(site, prefix))


def build_article(site, a, write):
    prefix = "../"
    path = f"/ratgeber/{a['slug']}.html"
    toc = []
    html_body = md.render(a["body"], prefix, toc=toc)
    sv = site.service(a.get("service", "")) if a.get("service") else None
    ld = [seo.article(site, a), seo.crumbs(site, [("Startseite", "/"), ("Ratgeber", "/ratgeber/index.html"), (a["title"], path)])]
    if a.get("faq"):
        ld.append(seo.faq(a["faq"]))
    summary = "".join(f"<li>{md.inline(x, prefix)}</li>" for x in a.get("summary", []))
    toc_html = "".join(f'<li><a href="#{hid}">{ESC(t)}</a></li>' for hid, t in toc)
    faq = ""
    if a.get("faq"):
        faq = f'<h2 id="haeufige-fragen">Häufige Fragen</h2><div class="faq-list">{core.faq_html(a["faq"], prefix)}</div>'
    related = [x for x in site.articles if x["slug"] != a["slug"] and x.get("category") == a.get("category")]
    related += [x for x in site.articles if x["slug"] != a["slug"] and x not in related]
    rel = "".join(f'<a href="{x["slug"]}.html"><strong>{ESC(x["title"])}</strong><span>{ESC(x.get("excerpt", ""))}</span></a>' for x in related[:3])
    sv_card = ""
    if sv:
        sv_card = f'''<div class="aside-card"><h3>Passende Leistung</h3><p><strong>{ESC(sv["short"])}</strong>: {ESC(sv["teaser"])}</p>
          <a class="btn btn-line-light" href="{prefix}leistungen/{sv["slug"]}.html">{ESC(sv["short"])} ansehen</a></div>'''
    pkg = (sv.get("package") or sv.get("bookAs", "")) if sv else ""
    body = f'''
<main id="main">
  <article class="article" aria-labelledby="page-h">
    <header class="page-hero page-hero--compact">
      <div class="container">
        {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Ratgeber", "index.html"), (a.get("category", "Artikel"), None)])}
        <p class="eyebrow">{ESC(a.get("category", "Ratgeber"))}</p>
        <h1 id="page-h">{ESC(a["title"])}</h1>
        <p class="lead">{ESC(a.get("excerpt", ""))}</p>
        <p class="article-meta">{I["clock"]}{a.get("readingTime", 5)} Min. Lesezeit · Aktualisiert am <time datetime="{ESC(a.get("updated") or a.get("date"))}">{de_date(a.get("updated") or a.get("date"))}</time> · von {ESC(site.s["name"])}, Fachbetrieb für Fahrzeugaufbereitung in Celle</p>
      </div>
    </header>
    <div class="container two-up article-layout">
      <div class="prose">
        <div class="article-summary"><h2 class="as-h">Das Wichtigste in Kürze</h2><ul>{summary}</ul></div>
        {html_body}
        {faq}
        <div class="author-box">{I["shield"]}<div><strong>Über {ESC(site.s["name"])}</strong><p>Fachbetrieb für Fahrzeugaufbereitung in Celle, gegründet von {ESC((site.s.get("about") or {}).get("name") or "dem Inhaber")}. C²Coating Excellence Partner, Koch-Chemie geschult, 100 % Handarbeit, {ESC(site.s["rating"]["value"])} ★ bei {site.s["rating"]["count"]} Google-Bewertungen. Dieser Artikel gibt unsere Erfahrung aus der täglichen Arbeit wieder.</p></div></div>
      </div>
      <aside class="sticky-aside">
        <nav class="aside-card toc" aria-label="Inhalt"><h3>Inhalt</h3><ol>{toc_html}</ol></nav>
        <div class="aside-card dark">
          <h3>Lieber vom Profi?</h3>
          <p>Wir bereiten Ihr Auto in Celle in Handarbeit auf. Verbindlicher Preis vor dem Termin.</p>
          <a class="btn btn-primary" href="{prefix}termin.html{("?paket=" + pkg) if pkg else ""}">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa" href="{site.wa("Hallo ElbDetail, ich habe Ihren Ratgeber gelesen und habe eine Frage: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        </div>
        {sv_card}
      </aside>
    </div>
  </article>
  <section class="soft" aria-labelledby="rel-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Weiterlesen</p><h2 id="rel-h" class="display">Mehr aus dem Ratgeber.</h2></div>
      <div class="related">{rel}</div>
    </div>
  </section>
{core.cta_band(site, prefix)}
</main>
'''
    title = a.get("seoTitle") or (a["title"] + " | ElbDetail")
    write(f"ratgeber/{a['slug']}.html", core.head(site, title, a["description"], path, prefix=prefix, ld=ld, og_type="article",
                                                   extra=f'<meta property="article:published_time" content="{ESC(a.get("date", ""))}">\n<meta property="article:modified_time" content="{ESC(a.get("updated") or a.get("date", ""))}">\n')
          + core.header(site, prefix, current="ratgeber/index.html") + body + core.footer(site, prefix))
