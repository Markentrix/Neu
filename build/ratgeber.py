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
    body = f'''
<main id="main">
  <section class="page-hero page-hero--compact" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Ratgeber", None)])}
      <p class="eyebrow">Ratgeber</p>
      <h1 id="page-h">Wissen aus der Werkstatt. <em>Ehrlich erklärt.</em></h1>
      <p class="lead">Antworten auf die Fragen, die wir in Celle jeden Tag hören: Was kostet eine Aufbereitung, was hilft vor der Leasingrückgabe, wie pflegst du Lack, Leder und Innenraum richtig?</p>
    </div>
  </section>
  <section class="tight-top" aria-label="Artikel">
    <div class="container">
      <div class="chip-row" role="group" aria-label="Nach Thema filtern">{chips}</div>
      <div class="article-grid" id="articleGrid">{cards}</div>
    </div>
  </section>
{core.cta_band(site, prefix)}
</main>
'''
    write("ratgeber/index.html", core.head(site, title, desc, path, prefix=prefix, ld=ld) + core.header(site, prefix, current="ratgeber/index.html") + body + core.footer(site, prefix))


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
    pkg = sv["package"] if sv else ""
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
        <div class="author-box">{I["shield"]}<div><strong>Über {ESC(site.s["name"])}</strong><p>Fachbetrieb für Fahrzeugaufbereitung in Celle. Koch-Chemie geschult, 100 % Handarbeit, {ESC(site.s["rating"]["value"])} ★ bei {site.s["rating"]["count"]} Google-Bewertungen. Dieser Artikel gibt unsere Erfahrung aus der täglichen Arbeit wieder.</p></div></div>
      </div>
      <aside class="sticky-aside">
        <nav class="aside-card toc" aria-label="Inhalt"><h3>Inhalt</h3><ol>{toc_html}</ol></nav>
        <div class="aside-card dark">
          <h3>Lieber vom Profi?</h3>
          <p>Wir bereiten dein Auto in Celle in Handarbeit auf. Verbindlicher Preis vor dem Termin.</p>
          <a class="btn btn-primary" href="{prefix}termin.html{("?paket=" + pkg) if pkg else ""}">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa" href="{site.wa("Hallo ElbDetail, ich habe euren Ratgeber gelesen und habe eine Frage: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
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
