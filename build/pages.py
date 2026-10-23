# -*- coding: utf-8 -*-
"""Startseite, Leistungsseiten, Rechtsseiten, 404 und Danke-Seite."""
import os
import re

import core
import md
import seo
from core import ESC, I, STARS5, inl


# --------------------------------------------------------------------------- Vorher/Nachher
def _ba_placeholder(n):
    before = f'''<svg class="ba-art" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="b{n}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3d44"/><stop offset="1" stop-color="#23262c"/></linearGradient><filter id="n{n}"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2"/><feColorMatrix values="0 0 0 0 0.5 0 0 0 0 0.45 0 0 0 0 0.4 0 0 0 0.25 0"/></filter></defs><rect width="400" height="300" fill="url(#b{n})"/><rect width="400" height="300" filter="url(#n{n})"/><path d="M40 210c20-70 70-110 160-110s140 40 160 110" fill="none" stroke="#7a7f88" stroke-width="10" stroke-linecap="round"/><circle cx="120" cy="225" r="26" fill="#55595f"/><circle cx="280" cy="225" r="26" fill="#55595f"/><circle cx="90" cy="120" r="30" fill="#6b5d4a" opacity=".45"/><circle cx="300" cy="90" r="22" fill="#6b5d4a" opacity=".4"/></svg>'''
    after = f'''<svg class="ba-art ba-after" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="a{n}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2c3340"/><stop offset=".55" stop-color="#1b2029"/><stop offset="1" stop-color="#101318"/></linearGradient><linearGradient id="s{n}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#5b9be8" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><rect width="400" height="300" fill="url(#a{n})"/><path d="M40 210c20-70 70-110 160-110s140 40 160 110" fill="none" stroke="#dfe7f3" stroke-width="10" stroke-linecap="round"/><path d="M60 196c20-56 62-90 140-90" fill="none" stroke="url(#s{n})" stroke-width="4" stroke-linecap="round"/><circle cx="120" cy="225" r="26" fill="#eef2f7"/><circle cx="280" cy="225" r="26" fill="#eef2f7"/><circle cx="120" cy="225" r="12" fill="#1c4f9c"/><circle cx="280" cy="225" r="12" fill="#1c4f9c"/></svg>'''
    return before, after


def picture(site, name, alt, cls, prefix, sizes="(min-width: 900px) 33vw, 90vw", eager=False):
    m = site.media.get(name)
    if not m:
        return ""
    srcs = ""
    if m.get("avif"):
        srcs += f'<source type="image/avif" srcset="{", ".join(prefix + s for s in m["avif"])}" sizes="{sizes}">'
    if m.get("webp"):
        srcs += f'<source type="image/webp" srcset="{", ".join(prefix + s for s in m["webp"])}" sizes="{sizes}">'
    return (f'<picture class="{cls}">{srcs}<img src="{prefix}{m["src"]}" alt="{ESC(alt)}" width="{m["w"]}" height="{m["h"]}" '
            + ('fetchpriority="low" ' if eager else 'loading="lazy" ') + 'decoding="async"></picture>')


def figure(site, img, prefix, sizes="(min-width: 900px) 600px, 92vw"):
    """Bild mit Bildunterschrift und Quellenangabe, z. B. {"file", "alt", "caption", "credit"}."""
    if not img or img.get("file") not in site.media:
        return ""
    pic = picture(site, img["file"], img.get("alt", ""), "fig-img", prefix, sizes=sizes)
    cap = ESC(img.get("caption", ""))
    if img.get("credit"):
        cap += f' <span class="fig-credit">Bild: {ESC(img["credit"])}</span>'
    return f'<figure class="fig">{pic}' + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>"


def _refs(site):
    return [r if isinstance(r, dict) else {"name": r} for r in site.s.get("references", [])]


def _svg_size(site, fname):
    """Breite und Höhe aus dem SVG (width/height, sonst viewBox), damit nichts beim Laden springt."""
    try:
        with open(os.path.join(getattr(site, "static_dir", ""), fname), encoding="utf-8") as f:
            tag = re.search(r"<svg\b[^>]*>", f.read(4096)).group(0)
    except (OSError, AttributeError):
        return ""
    w, h = re.search(r'\bwidth="([\d.]+)', tag), re.search(r'\bheight="([\d.]+)', tag)
    if w and h:
        return f' width="{round(float(w.group(1)))}" height="{round(float(h.group(1)))}"'
    vb = re.search(r'viewBox="[\d.\s-]+?([\d.]+)\s+([\d.]+)"', tag)
    return f' width="{round(float(vb.group(1)))}" height="{round(float(vb.group(2)))}"' if vb else ""


def _ref_mark(site, r, prefix, cls):
    """Logo, falls vorhanden, sonst der Name als ruhige Wortmarke. Geschützte Bindestriche halten Namen zusammen."""
    name = ESC(r["name"])
    if r.get("logo"):
        return f'<img class="{cls}-logo" src="{prefix}{ESC(r["logo"])}" alt="{ESC(r["name"])}"{_svg_size(site, r["logo"])} loading="lazy" decoding="async">'
    return f'<span class="{cls}-word">{name}</span>'


def ref_wall(site, prefix=""):
    """Logo-Wand für die Firmenkunden-Seite (dunkler Abschnitt)."""
    rl = _refs(site)
    if not rl:
        return ""
    cells = []
    for r in rl:
        inner = f'<span class="ref-cell-mark">{_ref_mark(site, r, prefix, "ref")}</span><span class="ref-cell-type">{ESC(r.get("type") or "Firmenkunde")}</span>'
        if r.get("url", "").startswith("https://"):
            cells.append(f'<li><a class="ref-cell" href="{ESC(r["url"])}" target="_blank" rel="noopener">{inner}'
                         f'<span class="ref-cell-go">Website<span class="visually-hidden"> von {ESC(r["name"])} (öffnet in neuem Tab)</span> {I["arrow"]}</span></a></li>')
        else:
            cells.append(f'<li><div class="ref-cell">{inner}</div></li>')
    return f'''
  <section class="dark on-dark refs-band" aria-labelledby="refs-h">
    <div class="container">
      <div class="refs-head reveal">
        <div><p class="eyebrow">Referenzen</p><h2 id="refs-h" class="display">Unternehmen aus Celle <em>vertrauen uns.</em></h2></div>
        <p>Diese Unternehmen aus Celle lassen ihre Fahrzeuge bei uns aufbereiten. Ein Klick auf das Logo führt zur jeweiligen Website.</p>
      </div>
      <ul class="ref-wall reveal">{"".join(cells)}</ul>
      <div class="refs-cta reveal"><p><strong>Ihr Unternehmen fehlt hier noch?</strong> Wir erstellen Ihnen ein Angebot für Ihren Fuhrpark.</p>
        <a class="btn btn-primary" href="#firmenanfrage">{I["brief"]}Angebot anfordern</a></div>
    </div>
  </section>'''


def ref_strip(site, prefix=""):
    """Kompakte Logo-Leiste für die Startseite."""
    rl = _refs(site)
    if not rl:
        return ""
    items = "".join(
        (f'<li><a href="{ESC(r["url"])}" target="_blank" rel="noopener" title="{ESC(r["name"])} · {ESC(r.get("type") or "")}">{_ref_mark(site, r, prefix, "rs")}'
         f'<span class="visually-hidden"> (öffnet in neuem Tab)</span></a></li>') if r.get("url", "").startswith("https://")
        else f'<li><span>{_ref_mark(site, r, prefix, "rs")}</span></li>' for r in rl)
    return f'''
      <div class="ref-strip reveal">
        <p class="ref-strip-label">Auch Unternehmen aus Celle vertrauen uns</p>
        <ul class="ref-strip-list">{items}</ul>
        <a class="text-link ref-strip-more" href="{prefix}firmenkunden.html">Angebote für Firmen →</a>
      </div>'''


def offer_card(site, o, prefix=""):
    """Angebotskarte für /angebote.html und die Startseite. Enddatum steht im Attribut, damit abgelaufene Karten sofort verschwinden."""
    until = ""
    if o.get("validUntil"):
        y, m, d = o["validUntil"].split("-")
        until = f'<span class="offer-until">gültig bis {d}.{m}.{y}</span>'
    href = o.get("ctaHref") or "termin.html"
    ext = href.startswith("http")
    if not href.startswith(("http", "#", "mailto:", "tel:")):
        href = prefix + href
    icon = I.get(o.get("icon") or "spark", I["spark"])
    img = picture(site, o.get("image", ""), o.get("imageAlt") or o["title"], "offer-img", prefix, sizes="(min-width: 900px) 380px, 88vw")
    price = ESC(o.get("price", "")).replace(" €", "&nbsp;€")
    return f'''
        <article class="offer reveal{" is-highlight" if o.get("highlight") else ""}{" has-img" if img else ""}" data-offer{f' data-until="{ESC(o["validUntil"])}"' if o.get("validUntil") else ""}>
          {img}
          <div class="offer-top"><span class="offer-icon">{icon}</span>{f'<span class="offer-badge">{ESC(o["badge"])}</span>' if o.get("badge") else ""}</div>
          <h3>{ESC(o["title"])}</h3>
          <p>{ESC(o.get("text", ""))}</p>
          <div class="offer-foot">
            <span class="offer-price">{price}</span>{until}
          </div>
          <a class="btn {"btn-primary" if o.get("highlight") else "btn-line-light"}" href="{ESC(href)}"{' target="_blank" rel="noopener"' if ext else ""}>{ESC(o.get("ctaLabel") or "Jetzt anfragen")}</a>
        </article>'''


def offers_home(site):
    """Startseiten-Bereich: hervorgehobene Angebote zuerst, höchstens drei Karten."""
    offers = sorted(site.offers, key=lambda o: not o.get("highlight"))[:3]
    if not offers:
        return ""
    more = len(site.offers) > len(offers)
    return f'''
  <section id="angebote" class="offers-home" aria-labelledby="angebote-h" data-offer-section>
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Aktuelle Angebote</p>
        <h2 id="angebote-h" class="display">Gerade <em>besonders lohnend.</em></h2>
      </div>
      <div class="offer-grid offer-grid--home stagger">{"".join(offer_card(site, o) for o in offers)}
      </div>
      <p class="section-more"><a class="text-link" href="angebote.html">{"Alle " + str(len(site.offers)) + " Angebote ansehen" if more else "Alle Angebote im Überblick"} →</a></p>
    </div>
  </section>'''


def ba_tile(site, item, n, prefix=""):
    has = item.get("before") in site.media and item.get("after") in site.media
    if has:
        before = picture(site, item["before"], "Vorher: " + item.get("alt", item["title"]), "ba-art", prefix)
        after = picture(site, item["after"], "Nachher: " + item.get("alt", item["title"]), "ba-art ba-after", prefix)
    else:
        before, after = _ba_placeholder(n)
    return f'''
        <div class="ba reveal">
          {before}{after}
          <span class="ba-tag l">Vorher</span><span class="ba-tag r">Nachher</span>
          <div class="ba-handle"></div>
          <label><span class="visually-hidden">Vorher-Nachher-Vergleich: {ESC(item["title"])}</span><input type="range" min="0" max="100" value="50"></label>
          <div class="ba-caption">{ESC(item["title"])}<span>{ESC(item.get("sub", ""))}</span></div>
        </div>''', has


def service_ba(site, sv, prefix=""):
    """Vorher-Nachher-Regler auf einer Leistungsseite (Eintrag aus der Galerie per Titel)."""
    it = next((g for g in site.gallery if g.get("title") == sv.get("beforeAfter")), None)
    if not it:
        return ""
    tile, has = ba_tile(site, it, 9, prefix)
    return f'<div class="ba-single" aria-label="Vorher-Nachher-Vergleich">{tile}<p class="hint">Ziehen Sie den Regler, um vorher und nachher zu vergleichen.</p></div>' if has else ""


# --------------------------------------------------------------------------- Startseite
def plan_card(site, p, prefix=""):
    def li(f):
        if f.get("optional"):
            return f'<li class="opt">{I["plus"]}{ESC(f["text"])}</li>'
        return f'<li class="{"" if f.get("included") else "no"}">{I["check"] if f.get("included") else I["x"]}{ESC(f["text"])}</li>'
    lis = "".join(li(f) for f in p["features"])
    cls0 = site.pricing["classes"][0]["key"]
    featured = p.get("featured")
    return f'''
        <article class="plan{" is-featured" if featured else ""} reveal" data-plan="{p["key"]}">
          {'<span class="plan-badge">Unsere Empfehlung</span>' if featured else ""}
          <h3>{ESC(p["name"])}</h3>
          <p class="plan-for">{ESC(p["for"])}</p>
          <div class="plan-price"><span class="from">ab</span><span class="amount">{p["prices"][cls0]} €</span></div>
          <div class="plan-meta"><span title="reine Arbeitszeit">{I["clock"]}{ESC(p["duration"])}</span><span>{I["hand"]}Handarbeit</span></div>
          <ul>{lis}</ul>
          <a class="btn {"btn-primary" if featured else "btn-line-light"}" href="{prefix}termin.html?paket={p["key"]}" data-book="{p["key"]}">{I["cal"]}{ESC(p["name"])} anfragen</a>
          <a class="text-link plan-wa" href="{site.wa()}" data-wa-plan="{p["key"]}" target="_blank" rel="noopener">{I["wa"]}oder per WhatsApp</a>
        </article>'''


def plan_row(site, p, prefix=""):
    featured = p.get("featured")
    return f'''
        <a class="plan-row{" is-featured" if featured else ""} reveal" href="{prefix}termin.html?paket={p["key"]}">
          <span class="plan-row-name"><strong>{ESC(p["name"])}</strong>{'<span class="plan-row-badge">Empfehlung</span>' if featured else ""}<small>{ESC(p["for"])}</small></span>
          <span class="plan-row-price"><small>ab</small>{site.min_price(p["key"])}&nbsp;€<small>{ESC(p["duration"])}</small></span>
          <span class="service-arrow">{I["arrow"]}</span>
        </a>'''


HOME_FAQ = [0, 10, 2, 5, 3]     # Indizes aus faq.json, die auf der Startseite stehen
PRICE_FAQ = [0, 1, 7, 8, 9, 11]    # … und auf der Preisseite


def pick(items, idx):
    return [items[i] for i in idx if i < len(items)] or items[:5]


def _eur(v):
    return f"{v:,}".replace(",", ".") + "&nbsp;€" if v is not None else "auf Anfrage"


def addon_table(site, a):
    """Preistabelle einer Zusatz-Keramik (Felgen oder Scheiben)."""
    promo = site.addon_promo(a["key"])
    cell = lambda p, reg: (f'<s class="price-was" aria-label="statt {_eur(reg)}">{_eur(reg)}</s> <strong class="price-promo">{_eur(p)}</strong>' if reg is not None
                           else ("ab " if a.get("from") and p is not None else "") + _eur(p))
    tag = f'<small>{ESC(promo["title"])} bis {_de(promo["validUntil"])}</small>' if promo else ""
    rows = "".join(f'<tr{" class=is-promo" if reg is not None else ""}><th scope="row">{ESC(n)}{tag if reg is not None else ""}</th><td class="num">{cell(p, reg)}</td></tr>'
                   for n, p, reg in site.addon_items(a["key"]))
    dur = f' · Dauer {ESC(a["duration"])}' if a.get("duration") else ""
    return f'''<div class="price-scroll" tabindex="0" role="region" aria-label="Preise {ESC(a["title"])}">
            <table class="price-table ceramic-table">
              <caption>{ESC(a["name"])} · {ESC(a["title"])}{dur}</caption>
              <thead><tr><th scope="col">{ESC(a["priceLabel"])}</th><th scope="col" class="num">Preis{" " + ESC(a["unit"]) if a.get("unit") else ""}</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>'''


def promo_box(site, a, prefix=""):
    """Hinweis auf eine laufende Aktion der Zusatz-Keramik."""
    pr = site.addon_promo(a["key"])
    if not pr:
        return ""
    items = " · ".join(f"{ESC(n)} {_eur(p)}" for n, p in pr["prices"].items())
    dur = f' Dauer {ESC(a["duration"].rstrip("."))}.' if a.get("duration") else ""
    return f'''<div class="promo-box">{I["snow"]}<div><strong>{ESC(pr["title"])} bis {_de(pr["validUntil"])}: {items}</strong>
          <p>{ESC(pr.get("text", ""))}{dur}</p></div></div>'''


def addon_details(site, a, prefix=""):
    """Vorteile, Standzeit und Preise einer Zusatz-Keramik für die eigene Leistungsseite."""
    pr = site.pricing
    pts = "".join(f'<li>{I["check"]}{ESC(b)}</li>' for b in a["benefits"])
    return f'''
      <div class="ceramic-prices reveal" id="keramik-preise">
        <h2>{ESC(a["name"])}: Preise und Vorteile</h2>
        <div class="ceramic-grid">
          {addon_table(site, a)}
          <div class="addon-facts">
            <p class="addon-durability">{I["shield"]}<span><strong>Standzeit {ESC(a["durability"])}</strong><small>laut Hersteller, unter optimalen Voraussetzungen</small></span></p>
            <ul class="includes">{pts}</ul>
          </div>
        </div>
        {promo_box(site, a, prefix)}
        <p class="price-note">{ESC(pr.get("durabilityNote", ""))}</p>
        <a class="btn btn-primary" href="{prefix}termin.html?paket={"scheiben" if a["key"] == "scheiben" else "keramik"}">{I["cal"]}{ESC(a["title"])} {"buchen" if a["key"] == "scheiben" else "anfragen"}</a>
      </div>'''


def addons_prices(site, prefix=""):
    """Felgen- und Scheibenkeramik auf der Preisseite."""
    ads = site.pricing.get("addons", [])
    if not ads:
        return ""
    links = " · ".join(f'<a class="text-link" href="{prefix}leistungen/{a["slug"]}.html">Mehr zur {ESC(a["title"])}</a>' for a in ads)
    return f'''
      <div class="ceramic-prices reveal" id="felgen-scheiben-preise">
        <h2>Felgen- und Scheibenkeramik</h2>
        <p>Die Keramikbeschichtungen von C²Coating für Felgen und Scheiben buchen Sie einzeln oder zusammen mit der Lackkeramik.</p>
        <div class="ceramic-grid ceramic-grid--even">{"".join(addon_table(site, a) for a in ads)}</div>
        {"".join(promo_box(site, a, prefix) for a in ads)}
        <p class="price-note">Standzeit laut Hersteller: {", ".join(f"{ESC(a['title'])} {ESC(a['durability'])}" for a in ads)}. {ESC(site.pricing.get("durabilityNote", ""))}</p>
        <p>{links}</p>
      </div>'''


def ceramic_cards(site, prefix=""):
    """Startseite: Lack-, Felgen- und Scheibenkeramik als einheitliche Karten unter dem Keramik-Schwerpunkt."""
    pr = site.pricing
    if not pr.get("addons"):
        return ""
    cards = [("spark", "C²Coating CarCeramic", "Lackkeramik", site.min_price("keramik"), "keramikversiegelung-celle",
              ["Tiefer Glanz und starker Abperleffekt", "Langzeitschutz gegen Witterung, Streusalz und UV", "Ab Paket Signature oder beim Neuwagen"], None, "")]
    icons = {"felgen": "car", "scheiben": "shield"}
    for a in pr["addons"]:
        cards.append((icons.get(a["key"], "shield"), a["name"], a["title"], site.min_price(a["key"]), a["slug"], a["benefits"][:3], a["durability"], a.get("unit", "")))
    html = "".join(f'''
        <a class="cer-card reveal" href="{prefix}leistungen/{slug}.html">
          <span class="cer-icon">{I[ic]}</span>
          <span class="cer-brand">{ESC(brand)}</span>
          <h3>{ESC(title)}</h3>
          <span class="cer-price"><small>ab</small> {_eur(price)}{f" <small>{ESC(unit)}</small>" if unit else ""}</span>
          <ul>{"".join(f"<li>{I['check']}{ESC(b)}</li>" for b in pts)}</ul>
          {f'<span class="cer-dur">Standzeit {ESC(dur)}*</span>' if dur else '<span class="cer-dur">Preis je C²Coating-Fahrzeugkategorie</span>'}
          <span class="cer-more">Mehr erfahren {I["arrow"]}</span>
        </a>''' for ic, brand, title, price, slug, pts, dur, unit in cards)
    return f'''
      <div class="cer-cards stagger">{html}
      </div>
      <p class="cer-note">* Herstellerangaben unter optimalen Voraussetzungen. Die tatsächliche Haltbarkeit hängt von der Beanspruchung, der fachgerechten Verarbeitung und der anschließenden Pflege ab.</p>'''


def ceramic_section(site, prefix="", head="h2"):
    """C² CarCeramic-Preisliste (eigene Fahrzeugeinteilung von C²Coating)."""
    cer = site.pricing.get("ceramic")
    if not cer:
        return ""
    eur = _eur
    car = "".join(f'<tr><th scope="row">{ESC(c["name"])}</th><td>{ESC(c["examples"])}</td><td class="num">{eur(c["price"])}</td></tr>' for c in cer["car"])
    camper = "".join(f'<tr><th scope="row">{ESC(c["name"])}</th><td class="num">{eur(c["price"])}</td></tr>' for c in cer.get("camper", []))
    notes = "".join(f"<li>{ESC(n)}</li>" for n in cer.get("notes", []))
    return f'''
      <div class="ceramic-prices reveal" id="keramik-preise">
        <{head}>{ESC(cer["title"])}</{head}>
        <p>{ESC(cer["intro"])}</p>
        <div class="ceramic-grid">
          <div class="price-scroll" tabindex="0" role="region" aria-label="Keramik-Preise für Pkw">
            <table class="price-table ceramic-table">
              <caption>Pkw nach C²Coating-Kategorie</caption>
              <thead><tr><th scope="col">Kategorie</th><th scope="col">Beispiele</th><th scope="col" class="num">Preis</th></tr></thead>
              <tbody>{car}</tbody>
            </table>
          </div>
          {f'''<div class="price-scroll" tabindex="0" role="region" aria-label="Keramik-Preise für Wohnmobile">
            <table class="price-table ceramic-table">
              <caption>Wohnmobile &amp; Wohnwagen nach Länge</caption>
              <thead><tr><th scope="col">Länge</th><th scope="col" class="num">Preis</th></tr></thead>
              <tbody>{camper}</tbody>
            </table>
          </div>''' if camper else ""}
        </div>
        <p class="price-note">{ESC(cer.get("carNote", ""))}</p>
        <ul class="ceramic-notes">{notes}</ul>
        <a class="btn btn-primary" href="{prefix}termin.html?paket=keramik">{I["cal"]}Keramikversiegelung anfragen</a>
      </div>'''


def price_matrix(site):
    """Alle Ab-Preise auf einen Blick: Fahrzeugklassen × Pakete."""
    pr = site.pricing
    ths = "".join(f'<th scope="col" class="num">{ESC(p["name"])}</th>' for p in pr["packages"])
    def td(p, c):
        v = p["prices"].get(c["key"])
        return f'<td class="num">{f"ab {v}&nbsp;€" if v is not None else "auf Anfrage"}</td>'
    trs = "".join(f'<tr><th scope="row">{ESC(c["name"])}<small>{ESC(c["examples"])}</small></th>' + "".join(td(p, c) for p in pr["packages"]) + "</tr>"
                  for c in pr["classes"])
    return f'''
      <div class="price-matrix reveal" id="alle-preise">
        <h2>Alle Preise auf einen Blick</h2>
        <div class="price-scroll" tabindex="0" role="region" aria-label="Preisübersicht nach Fahrzeugklasse, seitlich scrollbar">
          <table class="price-table">
            <caption class="visually-hidden">Ab-Preise je Fahrzeugklasse und Paket</caption>
            <thead><tr><th scope="col">Fahrzeugklasse</th>{ths}</tr></thead>
            <tbody>{trs}</tbody>
          </table>
        </div>
      </div>'''


def price_section(site, prefix=""):
    """Volle Preisübersicht mit Klassen-Umschalter, Paketen, Extras und Vergleichstabelle."""
    pr = site.pricing
    feat = next((p for p in pr["packages"] if p.get("featured")), pr["packages"][0])
    price_cls = "".join(f'<label><input type="radio" name="pclass" value="{c["key"]}"{" checked" if i == 0 else ""}><span title="{ESC(c["name"])}">{ESC(c["short"])}</span></label>' for i, c in enumerate(pr["classes"]))
    plans = "".join(plan_card(site, p, prefix) for p in pr["packages"])
    addon_by_extra = {a["extra"]: a["key"] for a in pr.get("addons", [])}

    def extra_price(e):
        return f"ab {site.min_price(addon_by_extra[e])}&nbsp;€" if e in addon_by_extra else "auf Anfrage"
    extras = "".join(f"<li>{ESC(e)} <small>· {extra_price(e)}</small></li>" for e in pr["extras"])

    def cell(v, f=False):
        if v == "optional":
            c, mark, sr = "opt", "+", "Optional, separat buchbar"
        else:
            c, mark, sr = ("yes" if v else ""), ("✓" if v else "—"), ("Inklusive" if v else "Nicht enthalten")
        c = ("featured-col " if f else "") + c
        return f'<td class="{c.strip()}"><span aria-hidden="true">{mark}</span><span class="visually-hidden">{sr}</span></td>'
    keys = [p["key"] for p in pr["packages"]]
    fkey = feat["key"]
    trs = "".join(f'<tr><th scope="row">{ESC(r["label"])}</th>' + "".join(cell(r.get(k), k == fkey) for k in keys) + "</tr>" for r in pr["compare"])
    fc = ' class="featured-col"'
    ths = "".join(f'<th scope="col"{fc if p["key"] == fkey else ""}>{ESC(p["name"])}</th>' for p in pr["packages"])
    return f'''
      <div class="price-toolbar reveal">
        <fieldset id="priceClass"><legend class="visually-hidden">Fahrzeugklasse wählen</legend><div class="seg{" c6" if len(pr["classes"]) > 4 else ""}">{price_cls}</div></fieldset>
        <p>Richtpreise für <strong id="priceClassLabel">{ESC(pr["classes"][0]["name"])}</strong> in normalem Pflegezustand.</p>
      </div>
      <div class="plans stagger">{plans}
      </div>
      {price_matrix(site)}
      <p class="price-note">{ESC(pr["note"])}</p>
      {f'<p class="price-stand">{I["clock"]}<span>{ESC(pr["standNote"])}</span></p>' if pr.get("standNote") else ""}
      {f'<p class="price-stand">{I["spark"]}<span>{ESC(pr["polishNote"])}</span></p>' if pr.get("polishNote") else ""}
      <div class="pkg-details reveal">
        <h2>Was in den Paketen steckt</h2>
        <dl>{"".join(f'<div><dt>{ESC(p["name"])}</dt><dd>{ESC(p["description"])}</dd></div>' for p in pr["packages"] if p.get("description"))}</dl>
      </div>
      {ceramic_section(site, prefix)}
      {addons_prices(site, prefix)}
      <div class="extras reveal">
        <h2>Einzeln buchbar oder als Ergänzung</h2>
        <ul>{extras}</ul>
      </div>
      <details class="compare reveal" open>
        <summary>Alle Leistungen der Pakete im Vergleich</summary>
        <div class="price-scroll" tabindex="0" role="region" aria-label="Vergleichstabelle, seitlich scrollbar">
          <table class="price-table">
            <caption class="visually-hidden">Vergleich der Aufbereitungspakete nach enthaltenen Leistungen</caption>
            <thead><tr><th scope="col">Leistung</th>{ths}</tr></thead>
            <tbody>{trs}</tbody>
          </table>
        </div>
        <p class="compare-legend">✓ enthalten · + optional, separat buchbar · — nicht enthalten</p>
      </details>'''


def contact_compact(site, prefix=""):
    """Kurzer Kontaktblock: Termin, WhatsApp, Anrufen. Das ausführliche Formular steht auf kontakt.html."""
    s = site.s
    return f'''  <section id="kontakt" class="tight" aria-labelledby="kontakt-h">
    <div class="container">
      <div class="cta-band reveal">
        <p class="eyebrow">Kontakt &amp; Termin</p>
        <h2 id="kontakt-h" class="display">Bereit für ein Auto, das sich <em>wieder neu anfühlt?</em></h2>
        <p>Nennen Sie uns Fahrzeug, Wunschpaket und Zeitraum. Sie erhalten ein verbindliches Angebot, bevor irgendetwas passiert.</p>
        <div class="contact-actions">
          <a class="contact-action is-primary" href="{prefix}termin.html">{I["cal"]}<span><strong>Termin online anfragen</strong><small>In 2 Minuten, mit Richtpreis</small></span></a>
          <a class="contact-action" href="{site.wa("Hallo ElbDetail, ich möchte einen Termin zur Fahrzeugaufbereitung anfragen. Fahrzeug: … Wunsch: …")}" target="_blank" rel="noopener">{I["wa"]}<span><strong>WhatsApp</strong><small>{ESC(s["phoneIntl"])}</small></span></a>
          <a class="contact-action" href="tel:{s["phone"]}">{I["phone"]}<span><strong>Anrufen</strong><small>{ESC(s["phoneDisplay"])}</small></span></a>
        </div>
        <a class="next-free next-free--band" href="{prefix}termin.html" data-next-free hidden><span class="nf-dot" aria-hidden="true"></span>Nächster freier Tag: <strong data-nf-date></strong></a>
        <p class="contact-line"><a href="{site.maps_url()}" target="_blank" rel="noopener">{I["pin"]}{ESC(site.addr_line())}</a><a href="{prefix}kontakt.html">Kontaktformular &amp; Anfahrt</a></p>
      </div>
    </div>
  </section>
'''


def owner_html(site, prefix=""):
    """Inhaber-Karte. Erscheint erst, wenn Name und Text im Portal (Grunddaten → Über uns) gepflegt sind."""
    ab = site.s.get("about") or {}
    if not (ab.get("name") and ab.get("text")):
        return ""
    photo = picture(site, ab.get("photo", ""), f'{ab["name"]}, {ab.get("role") or "Inhaber"} von {site.s["name"]}', "owner-photo", prefix, sizes="96px")
    since = f' · seit {ESC(ab["since"])}' if ab.get("since") else ""
    return f'''
        <figure class="owner-card reveal">
          {photo}
          <blockquote>„{ESC(ab["text"])}“</blockquote>
          <figcaption><strong>{ESC(ab["name"])}</strong>{ESC(ab.get("role") or "Inhaber")}, {ESC(site.s["name"])}{since}</figcaption>
        </figure>'''


def build_home(site, write):
    s = site.s
    pr = site.pricing
    title = f"Fahrzeugaufbereitung in Celle ab {site.min_price('refresh')} € | ElbDetail"
    desc = (f"Fahrzeugaufbereitung in Celle mit Liebe zum Detail: Lackkorrektur, Keramikversiegelung und Innenraum in Handarbeit. "
            f"{s['rating']['value']} ★ bei Google, Festpreis vorab.")
    home_faq = pick(site.faq, HOME_FAQ)
    hi = s.get("heroImage") or {}
    hero_img = picture(site, hi.get("file", ""), "", "hero-photo", "", sizes="100vw", eager=True)
    if hero_img:
        hero_img = hero_img.replace('<picture class="hero-photo">', '<picture class="hero-photo" aria-hidden="true">')
        if hi.get("credit"):
            hero_img += f'<span class="hero-credit">Bild: {ESC(hi["credit"])}</span>'
    sp = s.get("spotlightImage") or {}
    spot_pic = picture(site, sp.get("file", ""), sp.get("alt", ""), "spot-img", "", sizes="(min-width: 900px) 520px, 92vw")
    spotlight = ""
    if spot_pic:
        spotlight = f'''
  <section class="tight" aria-labelledby="ker-h">
    <div class="container">
      <div class="spot reveal">
        <figure class="spot-media">{spot_pic}{f'<figcaption>Bild: {ESC(sp["credit"])}</figcaption>' if sp.get("credit") else ""}</figure>
        <div class="spot-copy">
          <p class="eyebrow">Unser Schwerpunkt</p>
          <h2 id="ker-h" class="display">Keramikversiegelung. <em>Glanz, der bleibt.</em></h2>
          <p>Als offizieller C²Coating Excellence Partner versiegeln wir Lack, Felgen und Scheiben keramisch. Das hält deutlich länger als Wachs oder klassische Versiegelung.</p>
          <ul class="spot-points">
            <li>{I["shield"]}<span>Langzeitschutz gegen Witterung, Streusalz und UV</span></li>
            <li>{I["spark"]}<span>Tiefer Glanz und starker Abperleffekt</span></li>
            <li>{I["hand"]}<span>Lackschichtdicke gemessen, Korrektur in Handarbeit</span></li>
          </ul>
          <div class="hero-actions">
            <a class="btn btn-primary" href="leistungen/keramikversiegelung-celle.html">Mehr zur Keramikversiegelung</a>
            <a class="btn btn-line" href="termin.html?paket=keramik">{I["cal"]}Beratung anfragen</a>
          </div>
        </div>
      </div>{ceramic_cards(site)}
    </div>
  </section>'''
    hero_q = site.reviews.get("heroQuote") or {"text": site.reviews["featuredQuote"], "name": "Google-Bewertung", "source": ""}
    owner_card = owner_html(site)
    ld = [seo.business(site), seo.website(site), seo.faq(home_faq),
          seo.webpage(site, "/", title, {"speakable": {"@type": "SpeakableSpecification", "cssSelector": ["#auf-einen-blick", ".hero-sub"]}})]

    services_rows = "".join(f'''
        <a class="service-row reveal" href="leistungen/{sv["slug"]}.html">
          <span class="service-num">{i + 1:02d}</span>
          <span class="service-title">{ESC(sv["short"])}</span>
          <span class="service-desc">{ESC(sv["teaser"])}</span>
          <span class="service-arrow">{I["arrow"]}</span>
        </a>''' for i, sv in enumerate(site.services))

    cls_radios = "".join(f'<label><input type="radio" name="qclass" value="{c["key"]}"{" checked" if i == 0 else ""}><span>{ESC(c["short"])}<small>{ESC(c["examples"])}</small></span></label>'
                         for i, c in enumerate(pr["classes"]))
    pkg_radios = "".join(f'<label><input type="radio" name="qpkg" value="{p["key"]}"{" checked" if p.get("featured") else ""}><span>{ESC(p["name"])} <small>{ESC(p["short"])}</small></span></label>'
                         for p in pr["packages"])
    feat = next((p for p in pr["packages"] if p.get("featured")), pr["packages"][0])
    cls0 = pr["classes"][0]["key"]
    plan_rows = "".join(plan_row(site, p) for p in reversed(pr["packages"]))  # höchstes Paket zuerst (Preisanker)

    tiles, real = [], 0
    for n, it in enumerate(site.gallery):
        h, has = ba_tile(site, it, n + 1)
        tiles.append((h, has)); real += has
    tiles = [t for t, has in tiles if has] if real else [t for t, _ in tiles]  # sobald echte Fotos da sind, keine Platzhalter mehr
    gallery_note = ("Ziehen Sie den Regler, um den Unterschied zu sehen. Weitere aktuelle Arbeiten zeigen wir laufend auf Instagram und TikTok."
                    if real else "Die Darstellungen sind Platzhalter, bis die ersten Vorher-/Nachher-Fotos online sind. Echte Ergebnisse finden Sie jederzeit auf Instagram und TikTok.")

    articles = site.articles[:3]
    art_cards = "".join(f'''
        <a class="article-card reveal" href="ratgeber/{a["slug"]}.html">
          <span class="article-cat">{ESC(a.get("category", "Ratgeber"))}</span>
          <h3>{ESC(a["title"])}</h3>
          <p>{ESC(a.get("excerpt", ""))}</p>
          <span class="more">{a.get("readingTime", 5)} Min. Lesezeit · Weiterlesen →</span>
        </a>''' for a in articles)
    ratgeber_section = f'''
  <section id="ratgeber" aria-labelledby="ratgeber-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Ratgeber</p>
        <h2 id="ratgeber-h" class="display">Wissen aus der <em>Werkstatt.</em></h2>
        <p>Ehrliche Antworten auf die Fragen, die wir täglich hören. Von Preisen über Leasingrückgabe bis zur richtigen Lackpflege im Winter.</p>
      </div>
      <div class="article-grid home-scroll stagger" tabindex="0" role="region" aria-label="Ratgeber-Artikel, seitlich wischen">{art_cards}</div>
      <p class="section-more"><a class="btn btn-line-light" href="ratgeber/index.html">Alle Ratgeber-Artikel</a></p>
    </div>
  </section>''' if articles else ""

    body = f'''
<main id="main">

  <section class="hero{" has-photo" if hero_img else ""}" aria-labelledby="hero-h">
    {hero_img}
    <div class="hero-bg-grid" aria-hidden="true"></div>
    <div class="container hero-inner">
      <div class="hero-copy">
        <div class="hero-kicker">
          <a class="hero-badge" href="#bewertungen">{STARS5} <span>{ESC(s["rating"]["value"])} · {s["rating"]["count"]} <span class="hide-xs">Google-</span>Bewertungen</span></a>
          <span class="hero-badge hero-badge-addr">{I["pin"]} {ESC(s["address"]["city"])} · {ESC(s["address"]["street"])}</span>
        </div>
        <h1 id="hero-h" class="hero-headline">Fahrzeug&shy;aufbereitung in Celle. <em>Mit Liebe zum Detail.</em></h1>
        <p class="hero-sub">Lackaufbereitung, <strong>Keramikversiegelung</strong> und Innenaufbereitung in Handarbeit. Für den Neuwagen, das Liebhaberstück und den Familienwagen, der wieder glänzen soll. Mit Festpreis, bevor wir anfangen.</p>
        <div class="hero-actions">
          <a class="btn btn-primary btn-lg" href="termin.html">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich möchte einen Termin anfragen. Fahrzeug: … Wunsch: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        </div>
        <a class="next-free" href="termin.html" data-next-free hidden><span class="nf-dot" aria-hidden="true"></span>Nächster freier Tag: <strong data-nf-date></strong></a>
        <figure class="hero-quote">
          <blockquote>„{ESC(hero_q["text"])}“</blockquote>
          <figcaption><span class="hq-stars" aria-hidden="true">★★★★★</span> {ESC(hero_q["name"])} · {ESC(hero_q.get("source", "Google-Bewertung"))}</figcaption>
        </figure>
      </div>

      <form class="quote-card" id="quoteForm" aria-labelledby="quote-h">
        <div class="quote-head"><h2 id="quote-h">Richtpreis in 10 Sekunden</h2><span>Unverbindlich</span></div>
        <fieldset class="quote-field"><legend><span>Fahrzeugklasse</span></legend><div class="seg{" c4" if len(pr["classes"]) == 4 else ""}{" c6" if len(pr["classes"]) == 6 else ""}">{cls_radios}</div></fieldset>
        <fieldset class="quote-field"><legend><span>Paket</span></legend><div class="seg pk">{pkg_radios}</div></fieldset>
        <div class="quote-result" aria-live="polite">
          <span class="lbl">Richtpreis <span id="quotePkgName">{ESC(feat["name"])}</span></span>
          <span class="val" id="quoteValue"><small>ab</small>{feat["prices"][cls0]}&nbsp;€</span>
        </div>
        <a class="btn btn-primary" id="quoteBook" href="termin.html?paket={feat["key"]}&amp;klasse={cls0}">{I["cal"]}Dieses Paket anfragen</a>
        <a class="quote-wa" id="quoteWa" href="{site.wa()}" target="_blank" rel="noopener">{I["wa"]}oder Angebot per WhatsApp</a>
        <p class="quote-note" id="quoteNote">Richtwert für normalen Pflegezustand. Der verbindliche Preis hängt von Fahrzeug und Zustand ab und wird vor dem Termin bestätigt.</p>
      </form>
    </div>
  </section>

  <div class="trust-bar" aria-label="Vertrauen">
    <div class="container">
      <ul>
        <li>{I["star"]}<span>{ESC(s["rating"]["value"])} von 5 Sternen<small>{s["rating"]["count"]} Google-Bewertungen</small></span></li>
        <li>{I["hand"]}<span>Handarbeit statt Waschstraße<small>Lackschonende Arbeit</small></span></li>
        <li>{I["euro"]}<span>Festpreis vorab<small>Keine Überraschung bei Abholung</small></span></li>
        <li><a class="trust-link" href="zertifikate.html">{I["shield"]}<span>C²Coating Excellence Partner<small>Koch-Chemie zertifiziert · Zertifikate ansehen</small></span></a></li>
      </ul>
    </div>
  </div>

{offers_home(site)}
  <section id="leistungen" aria-labelledby="leistungen-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Leistungen</p>
        <h2 id="leistungen-h" class="display">Für jedes Auto die <em>passende Pflege.</em></h2>
        <p>Vom Frischekick für den Alltag bis zur mehrstufigen Politur für den Neuwagen. Alle Leistungen auch einzeln buchbar.</p>
      </div>
      <div class="service-list stagger">{services_rows}
      </div>
      <p class="service-more reveal">Außerdem: Cabrioverdeck reinigen und imprägnieren, Motorraumreinigung, Abhol- und Bringservice nach Vereinbarung. Für regelmäßige Pflege gibt es <a class="text-link" href="elbdetail-care.html">ElbDetail Care</a>, für Unternehmen unsere <a class="text-link" href="firmenkunden.html">Firmenkunden-Angebote</a>.</p>
    </div>
  </section>
{spotlight}

  <section id="vorher-nachher" class="soft" aria-labelledby="vn-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Ergebnisse</p>
        <h2 id="vn-h" class="display">Vorher. Nachher. <em>Selbst schieben.</em></h2>
        <p>Ziehen Sie den Regler, um den Unterschied zu sehen.</p>
      </div>
      <div class="ba-grid stagger{" ba-grid--few" if len(tiles) < 3 else ""}">{"".join(tiles)}
      </div>
      <p class="gallery-note">{ESC(gallery_note)} <a class="text-link" href="{s["social"]["instagram"]}" target="_blank" rel="noopener">Instagram</a> · <a class="text-link" href="{s["social"]["tiktok"]}" target="_blank" rel="noopener">TikTok</a></p>
    </div>
  </section>

  <section id="bewertungen" aria-labelledby="bewertungen-h">
    <div class="container">
      <div class="section-head section-head--tight reveal">
        <p class="eyebrow">Bewertungen</p>
        <h2 id="bewertungen-h" class="display">Was Kund:innen aus Celle <em>sagen.</em></h2>
      </div>
      <div class="review-block reveal">
        <div class="review-score-wrap">
          <span class="review-score-big">{ESC(s["rating"]["value"])}</span>
          {STARS5}
          <p>{s["rating"]["count"]} Bewertungen bei Google</p>
        </div>
        <div>
          <p class="review-quote">„{ESC(site.reviews["featuredQuote"])}“</p>
          <div class="review-cta"><a class="btn btn-line-light btn-sm" href="{s["googleMapsUrl"]}" target="_blank" rel="noopener">Alle Bewertungen auf Google</a></div>
        </div>
      </div>
      <div class="mk-reviews" data-mk="bewertungen"></div>
      <div class="review-grid stagger" tabindex="0" role="region" aria-label="Kundenbewertungen">{core.review_cards(site)}
      </div>{ref_strip(site)}
      <p class="gallery-note">Ausgewählte Google-Rezensionen im Wortlaut, teils gekürzt, ohne Emojis (Stand {ESC(s["rating"]["asOf"])}). <strong>Hinweis zur Echtheit:</strong> Wir prüfen nicht, ob alle Bewertenden unsere Leistung genutzt haben. Google prüft Bewertungen nach eigenen Richtlinien.</p>
    </div>
  </section>

  <section id="preise" class="soft" aria-labelledby="preise-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Pakete &amp; Preise</p>
        <h2 id="preise-h" class="display">Klare Preise. <em>Bevor wir anfangen.</em></h2>
        <p>Ab-Preise für einen Kleinwagen. Den verbindlichen Preis für Ihr Fahrzeug erhalten Sie vor dem Termin, kostenlos und unverbindlich.</p>
      </div>
      <div class="plan-rows stagger">{plan_rows}
      </div>
      <p class="section-more"><a class="btn btn-line-light" href="preise.html">Alle Preise &amp; Leistungen</a></p>
    </div>
  </section>


  <section id="warum" class="dark on-dark" aria-labelledby="warum-h">
    <div class="container why-grid">
      <div class="reveal">
        <div class="section-head section-head--tight">
          <p class="eyebrow">Warum ElbDetail</p>
          <h2 id="warum-h" class="display">Sorgfalt, die man sieht. <em>Ein Preis, der vorher steht.</em></h2>
          <p>Inhabergeführter Fachbetrieb in Celle. Kein Franchise, keine Waschstraße: Jedes Fahrzeug wird persönlich und von Hand aufbereitet.</p>
        </div>
        <details class="facts-wrap" open data-close-narrow>
        <summary>ElbDetail auf einen Blick</summary>
        <dl class="facts" id="auf-einen-blick">
          <div><dt>Betrieb</dt><dd>{ESC(s["name"])} – {ESC(s["tagline"])}</dd></div>
          <div><dt>Standort</dt><dd>{ESC(site.addr_line())}</dd></div>
          <div><dt>Einzugsgebiet</dt><dd>Celle und Landkreis Celle</dd></div>
          <div><dt>Leistungen</dt><dd>Keramikversiegelung, Lackkorrektur, Innen- &amp; Außenaufbereitung, Lederpflege und -reparatur, Geruchsneutralisierung, Cabrioverdeck</dd></div>
          <div><dt>Richtpreise</dt><dd>{" / ".join(f"ab {site.min_price(p['key'])} €" for p in pr["packages"])} (Kleinwagen)</dd></div>
          <div><dt>Inhaber</dt><dd>{ESC((s.get("about") or {}).get("name") or "")} ({ESC((s.get("about") or {}).get("role") or "Inhaber")})</dd></div>
          <div><dt>Partner</dt><dd>Offizieller C²Coating Excellence Partner, Koch-Chemie-Fachschulungen, Colourlock für Leder</dd></div>
          <div><dt>Service</dt><dd>Abhol- und Bringservice nach Vereinbarung, regelmäßige Pflege mit ElbDetail Care</dd></div>
          <div><dt>Bewertung</dt><dd>{ESC(s["rating"]["value"])} ★ bei {s["rating"]["count"]} Google-Rezensionen (Stand {ESC(s["rating"]["asOf"])})</dd></div>
          <div><dt>Termin</dt><dd><a href="termin.html">Online-Terminanfrage</a> oder <a href="{site.wa()}" target="_blank" rel="noopener">WhatsApp {ESC(s["phoneIntl"])}</a></dd></div>
        </dl>
        </details>
      </div>
      <div class="why-list stagger">{owner_card}
        <div class="why-item reveal">{I["hand"]}<div><h3>Lackschonende Arbeit</h3><p>Handwäsche mit der Zwei-Eimer-Methode, weiche Mikrofaser und schonende Trocknung. So behandeln wir Ihren Lack so sanft wie möglich.</p></div></div>
        <div class="why-item reveal">{I["shield"]}<div><h3>Profi-Systeme statt Baumarkt</h3><p>Offizieller C²Coating Excellence Partner für Keramikversiegelungen, Fachschulungen bei Koch-Chemie, Colourlock für Leder. Jedes Material bekommt das passende Mittel.</p></div></div>
        <div class="why-item reveal">{I["euro"]}<div><h3>Preis vor dem Termin</h3><p>Sie erhalten ein verbindliches Angebot, bevor wir anfangen. Zusätzliche Arbeiten gibt es nur nach Rücksprache.</p></div></div>
        <div class="why-item reveal">{I["clock"]}<div><h3>Termin, wann es Ihnen passt</h3><p>Online buchen oder per WhatsApp anfragen, Montag bis Samstag. Auch kurzfristig vor Verkauf oder Rückgabe.</p></div></div>
      </div>
    </div>
  </section>

  <section id="ablauf" aria-labelledby="ablauf-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Ablauf</p>
        <h2 id="ablauf-h" class="display">In drei Schritten zum <em>Auto wie neu.</em></h2>
      </div>
      <div class="process-rail stagger" data-draw>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 01</span><h3>Anfrage in 2 Minuten</h3><p>Online-Terminanfrage oder WhatsApp mit Fahrzeug, Wunschpaket und Wunschtermin. Gern mit Fotos vom Zustand.</p></div>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 02</span><h3>Angebot &amp; Termin</h3><p>Sie erhalten ein verbindliches Angebot und eine Terminbestätigung. Erst wenn beides passt, geht es los.</p></div>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 03</span><h3>Aufbereitung &amp; Abnahme</h3><p>Handarbeit an unserem Standort in Celle. Optimal ist ein Tag Standzeit bei uns, bei Versiegelung und Keramik sind es 3 Tage, damit alles in Ruhe aushärtet. Danach gemeinsame Abnahme bei Tageslicht. Bezahlung bar, mit Karte oder per PayPal.</p></div>
      </div>
    </div>
  </section>


  <section class="tight" aria-labelledby="gift-h">
    <div class="container">
      <div class="promo-band reveal">
        <div class="promo-icon">{I["gift"]}</div>
        <div>
          <h2 id="gift-h">Verschenken Sie ein <em>Auto wie neu.</em></h2>
          <p>Gutscheine für Wunschbetrag oder Paket, mit persönlicher Nachricht. Ideal zu Weihnachten, zum Geburtstag oder als Dankeschön.</p>
        </div>
        <a class="btn btn-primary" href="gutscheine.html">Gutschein gestalten</a>
      </div>
    </div>
  </section>

{ratgeber_section}
  <section id="faq" class="soft" aria-labelledby="faq-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Häufige Fragen</p>
        <h2 id="faq-h" class="display">Gut zu wissen, <em>bevor Sie anfragen.</em></h2>
      </div>
      <div class="faq-list stagger">
        {core.faq_html(home_faq, first_open=False)}
      </div>
      <p class="section-more"><a class="text-link" href="preise.html#fragen">Weitere Fragen zu Preisen, Dauer und Bezahlung →</a></p>
    </div>
  </section>

{contact_compact(site)}
</main>
'''
    write("index.html", core.head(site, title, desc, "/", ld=ld, og_type="business.business") + core.header(site, home=True) + body + core.footer(site, home=True))


# --------------------------------------------------------------------------- Preise & Kontakt
def build_preise(site, write):
    pr = site.pricing
    path = "/preise.html"
    title = f"Preise Fahrzeugaufbereitung Celle ab {site.min_price('refresh')} € | ElbDetail"
    desc = ("Fahrzeugaufbereitung Celle: "
            + ", ".join(f"{p['name']} ab {site.min_price(p['key'])} €" for p in pr["packages"]) + ". Preise je Fahrzeugklasse, Festpreis vorab.")
    faq = pick(site.faq, PRICE_FAQ)
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Preise", path)]), seo.faq(faq)]
    facts = "".join(f'<div class="keyfact"><strong>ab {site.min_price(p["key"])} €</strong><span>{ESC(p["name"])}</span></div>' for p in pr["packages"])
    body = f'''
<main id="main">
  <section class="page-hero" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb("", [("Startseite", "index.html"), ("Pakete & Preise", None)])}
      <h1 id="page-h">Preise für Fahrzeug&shy;aufbereitung in Celle</h1>
      <p class="lead">Vier Pakete, transparente Ab-Preise je Fahrzeugklasse. Den verbindlichen Preis bestätigen wir kostenlos vor dem Termin, Zusatzarbeiten nur nach Rücksprache.</p>
      <div class="keyfacts">{facts}</div>
    </div>
  </section>

  <section id="pakete" class="soft" aria-labelledby="pakete-h">
    <div class="container">
      <h2 id="pakete-h" class="visually-hidden">Pakete und Richtpreise</h2>{price_section(site)}
    </div>
  </section>

  <section id="fragen" aria-labelledby="fragen-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Häufige Fragen</p>
        <h2 id="fragen-h" class="display">Preise, Dauer und Bezahlung.</h2>
      </div>
      <div class="faq-list stagger">
        {core.faq_html(faq)}
      </div>
    </div>
  </section>

{core.cta_band(site)}
</main>
'''
    write("preise.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="preise.html") + body + core.footer(site))


def build_kontakt(site, write):
    s = site.s
    path = "/kontakt.html"
    title = "Kontakt & Anfahrt | ElbDetail Fahrzeugaufbereitung Celle"
    desc = (f"ElbDetail in Celle kontaktieren: {s['address']['street']}, {s['address']['zip']} {s['address']['city']}. "
            f"Per WhatsApp, Telefon, E-Mail oder Kontaktformular. {s['openingHours']['text']}.")
    ld = [seo.webpage(site, path, title, {"@type": "ContactPage"}), seo.crumbs(site, [("Startseite", "/"), ("Kontakt", path)])]
    body = f'''
<main id="main">
  <section class="page-hero" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb("", [("Startseite", "index.html"), ("Kontakt", None)])}
      <h1 id="page-h">Kontakt &amp; Anfahrt</h1>
      <p class="lead">Standort, Erreichbarkeit und Kontaktformular von ElbDetail in Celle. Schreiben Sie uns, rufen Sie an oder kommen Sie vorbei.</p>
    </div>
  </section>
{core.contact_section(site)}
</main>
'''
    write("kontakt.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="kontakt.html") + body + core.footer(site))


def _de(iso):
    return f"{iso[8:10]}.{iso[5:7]}.{iso[:4]}" if iso and len(iso) >= 10 else ""


def cert_card(site, c, prefix="", compact=False):
    """Zertifikat als Karte. Ein Klick auf das Bild öffnet die große Ansicht (Lightbox, ohne JS: neue Seite mit dem Bild)."""
    m = site.media.get(c.get("image", ""))
    alt = f'{c.get("kind") or "Zertifikat"} „{c["title"]}“ für {(site.s.get("about") or {}).get("fullName") or "den Inhaber"}, {c.get("issuer", "")}'
    pic = picture(site, c.get("image", ""), alt, "cert-img", prefix, sizes="(min-width: 900px) 360px, 80vw")
    big = (prefix + (m["webp"][-1].split(" ")[0] if m.get("webp") else m["src"])) if m else ""
    media = (f'<a class="cert-media" href="{big}" data-lightbox aria-label="{ESC(c["title"])} groß ansehen">{pic}'
             f'<span class="cert-zoom">{I["zoom"]}Vergrößern</span></a>') if m else ""
    meta = " · ".join(x for x in [c.get("issuer", ""), c.get("place", ""), _de(c.get("date", ""))] if x)
    if compact:
        return f'''<article class="cert cert--compact reveal">{media}<div class="cert-body"><span class="cert-kind">{ESC(c.get("kind") or "Zertifikat")}</span><h3>{ESC(c["title"])}</h3><p class="cert-meta">{ESC(meta)}</p></div></article>'''
    return f'''
        <article class="cert reveal">
          {media}
          <div class="cert-body">
            <span class="cert-kind">{ESC(c.get("kind") or "Zertifikat")}</span>
            <h2>{ESC(c["title"])}</h2>
            {f'<p class="cert-sub">{ESC(c["subtitle"])}</p>' if c.get("subtitle") else ""}
            <p class="cert-meta">{ESC(meta)}</p>
            <p>{ESC(c.get("text", ""))}</p>
            {f'<p class="cert-benefit">{I["check"]}<span><strong>Ihr Vorteil:</strong> {ESC(c["benefit"])}</span></p>' if c.get("benefit") else ""}
          </div>
        </article>'''


def build_zertifikate(site, write):
    s = site.s
    ab = s.get("about") or {}
    path = "/zertifikate.html"
    title = "Zertifikate & Qualifikationen | ElbDetail Celle"
    desc = "Zertifikate von ElbDetail Celle: Koch-Chemie-Fachseminar für Lack- und Keramikversiegelung, Hochvolt-Qualifikation für E-Autos, C²Coating Partner."
    faq = [
        {"q": "Bereiten Sie auch Elektroautos und Hybridfahrzeuge auf?", "a": "Ja. Inhaber " + (ab.get("name") or "René") + " ist für Arbeiten an Serienfahrzeugen mit Hochvoltsystemen sensibilisiert (Qualifikation Stufe S). Für die Aufbereitung von Lack, Innenraum und Felgen ist das die passende Grundlage. Arbeiten an der Hochvolttechnik selbst gehören in eine Fachwerkstatt."},
        {"q": "Was bedeutet das Koch-Chemie-Fachseminar für mein Auto?", "a": "Lackkorrektur und Versiegelung werden nach den Vorgaben des Herstellers ausgeführt, von der hologrammfreien Politur bis zur Nano- und Keramikversiegelung. Die Fortbildung baut auf den Ausbildungsbausteinen des Bundesverbandes Fahrzeugaufbereitung (BFA) auf."},
        {"q": "Kann ich die Zertifikate im Original sehen?", "a": "Gern. Bei Ihrem Termin zeigen wir Ihnen die Originale. Auf dieser Seite sind sie zum Schutz der Unterzeichnenden mit unkenntlich gemachter Unterschrift abgebildet."},
    ]
    ld = [seo.webpage(site, path, title, {"mainEntity": {"@type": "Person", "name": ab.get("fullName") or ab.get("name") or s["name"],
                                                          "worksFor": {"@id": site.url + "/#business"}, "hasCredential": seo.credentials(site)}}),
          seo.crumbs(site, [("Startseite", "/"), ("Über uns", "/ueber-uns.html"), ("Zertifikate", path)]), seo.faq(faq)]
    cards = "".join(cert_card(site, c) for c in site.certs) or '<p class="empty-offers">Zertifikate folgen in Kürze.</p>'
    partners = "".join(f'<div class="usecase">{I["shield"]}<h3>{ESC(x["name"])}</h3><p><strong>{ESC(x["role"])}.</strong> {ESC(x["text"])}.</p></div>'
                       for x in s.get("partners", []))
    body = f'''
<main id="main">
  <section class="page-hero page-hero--compact" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb("", [("Startseite", "index.html"), ("Über uns", "ueber-uns.html"), ("Zertifikate", None)])}
      <p class="eyebrow">Zertifikate &amp; Qualifikationen</p>
      <h1 id="page-h">Geprüftes Können. <em>Schwarz auf weiß.</em></h1>
      <p class="lead">Gute Aufbereitung ist Handwerk mit Fachwissen. Hier sehen Sie die Nachweise von {ESC(ab.get("fullName") or ab.get("name") or "unserem Inhaber")}, im Original abgebildet.</p>
      <div class="hero-actions"><a class="btn btn-primary btn-lg" href="termin.html">{I["cal"]}Termin anfragen</a><a class="btn btn-line" href="ueber-uns.html">Mehr über {ESC(ab.get("name") or "uns")}</a></div>
    </div>
  </section>
  <section aria-label="Zertifikate">
    <div class="container">
      <div class="cert-list stagger">{cards}
      </div>
      <p class="price-note">Zum Schutz der Unterzeichnenden sind Unterschriften unkenntlich gemacht. Die Originale zeigen wir Ihnen gern beim Termin.</p>
    </div>
  </section>
  <section class="soft" aria-labelledby="partner-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Partnerschaften</p><h2 id="partner-h" class="display">Profi-Systeme, <em>geschult angewendet.</em></h2></div>
      <div class="usecase-grid">{partners}</div>
    </div>
  </section>
  <section aria-labelledby="zfaq-h">
    <div class="container narrow">
      <div class="section-head"><p class="eyebrow">Fragen</p><h2 id="zfaq-h" class="display">Gut zu wissen.</h2></div>
      <div class="faq-list">{core.faq_html(faq, "")}</div>
    </div>
  </section>
{core.cta_band(site, "")}
</main>
'''
    write("zertifikate.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="ueber-uns.html") + body + core.footer(site))


def build_about(site, write):
    """Über uns: René, seine Geschichte, sein Anspruch, Partner und Qualifikationen."""
    s = site.s
    ab = s.get("about") or {}
    name = ab.get("name") or "der Inhaber"
    path = "/ueber-uns.html"
    title = f"Über uns: {name}, Gründer von ElbDetail Celle"
    desc = (f"{name}, Gründer von ElbDetail in Celle: Fahrzeugaufbereitung aus Leidenschaft. "
            "C²Coating Excellence Partner, Koch-Chemie geschult.")
    photo = picture(site, ab.get("photo", ""), f"{name}, {ab.get('role') or 'Inhaber'} von {s['name']}", "about-photo", "", sizes="(min-width: 900px) 40vw, 90vw")
    partners = "".join(f'<div class="usecase">{I["shield"]}<h3>{ESC(x["name"])}</h3><p><strong>{ESC(x["role"])}.</strong> {ESC(x["text"])}.</p></div>'
                       for x in s.get("partners", []))
    ld = [seo.webpage(site, path, title, {"@type": "AboutPage", "mainEntity": {"@type": "Person", "name": ab.get("fullName") or name, "jobTitle": ab.get("role") or "Inhaber",
                                                                                "worksFor": {"@id": site.url + "/#business"}}}),
          seo.crumbs(site, [("Startseite", "/"), ("Über uns", path)])]
    body = f'''
<main id="main">
  <section class="page-hero" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb("", [("Startseite", "index.html"), ("Über uns", None)])}
      <p class="eyebrow">Über ElbDetail</p>
      <h1 id="page-h">Hinter ElbDetail steht <em>{ESC(name)}.</em></h1>
      <p class="lead">Ich bin {ESC(name)}, 30 Jahre alt und Gründer von ElbDetail in Celle. Aus meiner Leidenschaft für Autos und ihre Pflege ist mein Beruf geworden.</p>
    </div>
  </section>

  <section aria-label="Geschichte">
    <div class="container two-up">
      <div class="prose">
        <h2>Aus Leidenschaft zum Beruf</h2>
        <p>Ich begeistere mich schon lange für Fahrzeuge, für ihre Optik und für die Möglichkeiten, ihren Zustand zu erhalten oder wiederherzustellen. Aus dieser Begeisterung ist irgendwann der Wunsch entstanden, meine Leidenschaft zum Beruf zu machen. So habe ich mich mit der professionellen Fahrzeugaufbereitung selbstständig gemacht.</p>
        <p>Für mich ist Fahrzeugaufbereitung deshalb nicht einfach nur eine Dienstleistung. Ich beschäftige mich gern intensiv mit einem Fahrzeug, achte auf die Details und freue mich jedes Mal, wenn ich am Ende sehe, was die richtige Pflege erreichen kann.</p>
        <h2>Jedes Fahrzeug verdient die gleiche Sorgfalt</h2>
        <p>Ob ein alltäglicher Familienwagen, ein Firmenfahrzeug oder ein hochwertiger Sportwagen vor mir steht, spielt für mich keine Rolle. Jedes Fahrzeug bekommt die gleiche Aufmerksamkeit.</p>
        <p>Mein Anspruch ist, hochwertige Arbeit, professionelle Produkte und persönliche Betreuung miteinander zu verbinden. Ich möchte, dass Sie nicht einfach nur ein sauberes Auto zurückbekommen, sondern sich wirklich über das Ergebnis freuen.</p>
        <h2>Mein Schwerpunkt: Lack und Keramik</h2>
        <p>Besonders am Herzen liegt mir die professionelle Lackaufbereitung in Verbindung mit hochwertigen <a href="leistungen/keramikversiegelung-celle.html">Keramikversiegelungen</a>. Dabei geht es nicht nur um eine schöne Optik, sondern auch um langfristigen Lackschutz und eine leichtere Pflege. Als offizieller C²Coating Excellence Partner möchte ich ElbDetail zur festen Anlaufstelle für Keramikversiegelungen in Celle und Umgebung machen.</p>
        {figure(site, ab.get("partnerImage"), "")}
        <p>Genauso wichtig ist mir die Zusammenarbeit mit <a href="firmenkunden.html">Autohäusern, Unternehmen und Flotten</a>, und zwar langfristig und partnerschaftlich. Mein Ziel bleibt dabei immer dasselbe: hochwertige Fahrzeugpflege aus echter Leidenschaft.</p>
      </div>
      <aside class="sticky-aside">
        {('<div class="aside-card">' + photo + '</div>') if photo else ""}
        <div class="aside-card dark">
          <h3>Lernen Sie mich kennen</h3>
          <p>Schreiben Sie mir oder rufen Sie an. Ich berate Sie persönlich und ehrlich.</p>
          <a class="btn btn-primary" href="termin.html">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa" href="{site.wa(f"Hallo {name}, ich habe eine Frage zu meinem Fahrzeug: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp {ESC(s["phoneIntl"])}</a>
          <p>{ESC(site.addr_line())}</p>
        </div>
      </aside>
    </div>
  </section>

  <section class="soft" aria-labelledby="partner-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Partner &amp; Qualifikationen</p><h2 id="partner-h" class="display">Profi-Systeme, <em>geschult angewendet.</em></h2>
        <p>Ich arbeite mit professionellen Produkten und Aufbereitungssystemen, die ich kenne und denen ich vertraue.</p></div>
      <div class="usecase-grid">{partners}</div>
      {('<div class="cert-row stagger">' + "".join(cert_card(site, c, "", compact=True) for c in site.certs) + '</div><p class="section-more"><a class="text-link" href="zertifikate.html">Alle Zertifikate im Detail ansehen →</a></p>') if site.certs else ""}
    </div>
  </section>

{core.cta_band(site, "", "Ihr Auto in den besten Händen.", "Erzählen Sie mir kurz, worum es geht. Sie erhalten ein verbindliches Angebot, bevor irgendetwas passiert.")}
</main>
'''
    write("ueber-uns.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="ueber-uns.html") + body + core.footer(site))


# --------------------------------------------------------------------------- Leistungsseiten
def build_service(site, sv, write):
    prefix = "../"
    path = "/leistungen/" + sv["slug"] + ".html"
    p = site.pkg(sv["package"]) if sv.get("package") else None
    book = p["key"] if p else sv.get("bookAs", "beratung")  # Leistungen ohne Paketpreis: Anfrage nach Begutachtung
    if p:
        price_card = (f'<h3>Passendes Paket</h3><p><strong>{ESC(p["name"])}</strong> enthält diese Leistung, Richtpreis ab {site.min_price(p["key"])} € '
                      f'für einen Kleinwagen.</p><a class="btn btn-line-light" href="{prefix}preise.html">Pakete vergleichen</a>')
    elif sv.get("priceCard"):
        price_card = (f'<h3>{ESC(sv["priceCard"]["title"])}</h3><p>{ESC(sv["priceCard"]["text"])}</p>'
                      f'<a class="btn btn-line-light" href="{prefix}preise.html">Pakete vergleichen</a>')
    elif sv.get("addon") and site.addon(sv["addon"]):
        ad = site.addon(sv["addon"])
        price_card = (f'<h3>{ESC(ad["name"])}</h3><p>{ESC(ad["title"])} ab {site.min_price(ad["key"])} €{" " + ESC(ad["unit"]) if ad.get("unit") else ""}. Standzeit laut Hersteller {ESC(ad["durability"])}, '
                      f'unter optimalen Voraussetzungen.</p><a class="btn btn-line-light" href="#keramik-preise">Zur Preisliste</a>')
    elif book == "keramik" and site.pricing.get("ceramic"):
        price_card = (f'<h3>C² CarCeramic</h3><p>Keramikversiegelung für Pkw ab {site.min_price("keramik")} €, je nach C²Coating-Fahrzeugkategorie. '
                      f'Buchbar ab dem Paket Signature oder beim Neuwagen nach Lackprüfung.</p><a class="btn btn-line-light" href="#keramik-preise">Zur Preisliste</a>')
    else:
        price_card = (f'<h3>Preis nach Begutachtung</h3><p>Den Preis legen wir nach Fahrzeug und Zustand fest. Sie erhalten vorab einen verbindlichen Festpreis. '
                      f'Für eine erste Einschätzung genügen oft ein paar Fotos per WhatsApp.</p><a class="btn btn-line-light" href="{prefix}preise.html">Alle Pakete &amp; Preise</a>')
    toc = []
    intro = md.render(sv["intro"], prefix, toc=toc)
    ld = [seo.service(site, sv), seo.crumbs(site, [("Startseite", "/"), ("Leistungen", "/#leistungen"), (sv["short"] + " Celle", path)]),
          seo.faq(sv["faq"]), seo.webpage(site, path, sv["seoTitle"])]
    facts = "".join(f'<div class="keyfact"><strong>{ESC(f["value"])}</strong><span>{ESC(f["label"])}</span></div>' for f in sv["facts"])
    includes = "".join(f'<li>{I["check"]}{ESC(t)}</li>' for t in sv["includes"])
    steps = "".join(f'<div class="step"><div><h3>{ESC(x["title"])}</h3><p>{ESC(x["text"])}</p></div></div>' for x in sv["steps"])
    related = "".join(f'<a href="{r["slug"]}.html"><strong>{ESC(r["short"])}</strong><span>{ESC(r["teaser"])}</span></a>'
                      for r in (site.service(x) for x in sv.get("related", [])) if r)
    arts = [a for a in site.articles if a.get("service") == sv["slug"]][:3]
    art_links = "".join(f'<li><a href="../ratgeber/{a["slug"]}.html">{ESC(a["title"])}</a></li>' for a in arts)
    art_aside = f'<div class="aside-card"><h3>Passend im Ratgeber</h3><ul>{art_links}</ul></div>' if arts else ""
    wa = site.wa(f"Hallo ElbDetail, ich interessiere mich für {sv['short']} in Celle. Fahrzeug: … Wunschtermin: …")
    others = "".join(f'<li><a href="{x["slug"]}.html">{ESC(x["short"])} Celle</a></li>' for x in site.services if x["slug"] != sv["slug"])
    body = f'''
<main id="main">
  <section class="page-hero" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Leistungen", prefix + "index.html#leistungen"), (sv["short"], None)])}
      <h1 id="page-h">{inl(sv["h1"])}</h1>
      <p class="lead">{inl(sv["lead"])}</p>
      <div class="keyfacts">{facts}</div>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" href="{prefix}termin.html?paket={book}">{I["cal"]}Termin anfragen</a>
        <a class="btn btn-wa btn-lg" href="{wa}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        <a class="btn btn-line" href="{prefix}preise.html">Alle Pakete &amp; Preise</a>
      </div>
    </div>
  </section>

  <section aria-label="Details">
    <div class="container two-up">
      <div class="prose">
        {intro}
        {service_ba(site, sv, prefix)}
        {figure(site, sv.get("image"), prefix)}
        <h2 id="enthalten">Das ist enthalten</h2>
        <ul class="includes">{includes}</ul>
        {addon_details(site, site.addon(sv["addon"]), prefix) if sv.get("addon") and site.addon(sv["addon"]) else (ceramic_section(site, prefix) if book == "keramik" else "")}
        <h2 id="ablauf">So läuft es ab</h2>
        <div class="steps">{steps}</div>
        <h2 id="fragen">Häufige Fragen zu {ESC(sv["short"])}</h2>
        <div class="faq-list stagger">{core.faq_html(sv["faq"], prefix)}</div>
      </div>
      <aside class="sticky-aside">
        <div class="aside-card dark">
          <h3>Termin in Celle anfragen</h3>
          <p>Paket, Fahrzeug und Wunschtermin in 2 Minuten. Sie erhalten ein verbindliches Angebot vor dem Termin.</p>
          <a class="btn btn-primary" href="{prefix}termin.html?paket={book}">{I["cal"]}Online-Terminanfrage</a>
          <a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener">{I["wa"]}WhatsApp {ESC(site.s["phoneIntl"])}</a>
          <p>{ESC(site.addr_line())} · {ESC(site.s["openingHours"]["text"])}</p>
        </div>
        <div class="aside-card">{price_card}</div>
        {art_aside}
        <div class="aside-card"><h3>Weitere Leistungen</h3><ul>{others}</ul></div>
      </aside>
    </div>
  </section>

  <section class="soft" aria-labelledby="rel-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Das passt dazu</p><h2 id="rel-h" class="display">Weitere Leistungen in Celle.</h2></div>
      <div class="related">{related}</div>
    </div>
  </section>

{core.cta_band(site, prefix)}
</main>
'''
    write("leistungen/" + sv["slug"] + ".html",
          core.head(site, sv["seoTitle"], sv["description"], path, prefix=prefix, ld=ld) + core.header(site, prefix) + body + core.footer(site, prefix))


# --------------------------------------------------------------------------- Rechtsseiten
def _ph(v, text):
    return ESC(v) if v else f'<span class="legal-placeholder">[{text}]</span>'


def build_legal(site, write):
    s = site.s
    L = s["legal"]
    vat = ("<p>Kleinunternehmer im Sinne von § 19 UStG. Es wird keine Umsatzsteuer berechnet und daher auch nicht ausgewiesen.</p>" if L.get("smallBusiness")
           else f"<p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: {ESC(L['vatId'])}</p>" if L.get("vatId")
           else '<p><span class="legal-placeholder">[USt-IdNr. gemäß § 27a UStG, falls vorhanden – sonst Hinweis auf Kleinunternehmerregelung gemäß § 19 UStG]</span></p>')
    imp = f'''
    <h2>Diensteanbieter</h2>
    <p>{_ph(L.get("owner"), "Vollständiger Name der Inhaberin / des Inhabers oder Firmenname lt. Gewerbeanmeldung")}<br>
      {ESC(s["name"])} – {ESC(s["tagline"])}<br>{ESC(s["address"]["street"])}<br>{ESC(s["address"]["zip"])} {ESC(s["address"]["city"])}<br>Deutschland</p>
    <h2>Kontakt</h2>
    <p>Telefon / WhatsApp: {ESC(s["phoneIntl"])}<br>E-Mail: <a href="mailto:{s["email"]}">{ESC(s["email"])}</a></p>
    <h2>Umsatzsteuer</h2>
    {vat}
    <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
    <p>{_ph(L.get("responsible"), "Name, Anschrift wie oben")}</p>
    <h2>Verbraucherstreitbeilegung</h2>
    <p>Wir sind nicht verpflichtet und nicht bereit, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
    <h2>Haftung für Inhalte</h2>
    <p>Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG sind wir jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.</p>
    <h2>Haftung für Links</h2>
    <p>Unser Angebot enthält Links zu externen Websites Dritter (z. B. Google Maps, Instagram, Facebook, TikTok, WhatsApp, C²Coating, Koch-Chemie, Colourlock), auf deren Inhalte wir keinen Einfluss haben. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter verantwortlich.</p>
    <h2>Urheberrecht</h2>
    <p>Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Beiträge Dritter sind als solche gekennzeichnet.</p>
    <h2>Hinweis zu Preisangaben</h2>
    <p>Alle auf dieser Website genannten Preise sind unverbindliche Einstiegspreise für Fahrzeuge in normalem Pflegezustand{" und Endpreise; gemäß § 19 UStG wird keine Umsatzsteuer berechnet" if L.get("smallBusiness") else " inklusive gesetzlicher Umsatzsteuer"}. Ein verbindliches Angebot erfolgt individuell nach Fahrzeug und Zustand.</p>
    <div class="design-credit">
      <span>Designed by</span>
      <a href="https://markentrix.de/" target="_blank" rel="noopener" aria-label="Markentrix, Webdesign aus Celle (öffnet in neuem Tab)"><img src="markentrix-logo.svg" alt="Markentrix" width="147" height="36" loading="lazy"></a>
    </div>
'''
    mail = _ph(L.get("mailProvider"), "E-Mail-Anbieter mit Anschrift, z. B. der Anbieter des Postfachs info@elbdetail.de")
    host = ESC(L.get("hosting") or "Markentrix") + (", " + ESC(L["hostingAddress"]) if L.get("hostingAddress") else "")
    ds = f'''
    <h2>1. Verantwortlicher</h2>
    <p>Verantwortlicher im Sinne der Datenschutz-Grundverordnung (DSGVO) ist:<br>
      {_ph(L.get("owner"), "Vollständiger Name der Inhaberin / des Inhabers")}<br>
      {ESC(s["name"])} – {ESC(s["tagline"])}, {ESC(site.addr_line())}<br>
      E-Mail: <a href="mailto:{s["email"]}">{ESC(s["email"])}</a> · Telefon: {ESC(s["phoneIntl"])}</p>
    <h2>2. Grundsätzliches</h2>
    <p>Wir verarbeiten personenbezogene Daten nur, soweit dies zur Bereitstellung dieser Website, zur Bearbeitung von Anfragen und zur Durchführung unserer Leistungen erforderlich ist. Rechtsgrundlagen sind Art. 6 Abs. 1 lit. a DSGVO (Einwilligung), lit. b (Vertrag und Vertragsanbahnung), lit. c (rechtliche Pflichten) und lit. f (berechtigte Interessen).</p>
    <h2>3. Hosting und Website-Portal</h2>
    <p>Diese Website wird von {host} gehostet. Formulare, Terminanfragen, die Besucherstatistik und die Abfrage Ihrer Einwilligung laufen über das Website-Portal von Markentrix. Markentrix verarbeitet die Daten ausschließlich in unserem Auftrag und nach unserer Weisung; mit Markentrix besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO.{f" Website und Portal laufen auf Servern der {ESC(L['hostingServer'])} im Rechenzentrum {ESC(L.get('hostingLocation') or 'in Deutschland')}. Die Daten verbleiben in Deutschland. Hetzner ist als Unterauftragsverarbeiter von Markentrix eingebunden." if L.get("hostingServer") else ""} Schriftarten und Skripte der Website werden vom selben Server geladen, es werden keine Schriften oder Skripte von Drittanbietern nachgeladen.</p>
    <p><strong>Server-Logfiles:</strong> Beim Aufruf der Website werden technisch notwendige Daten verarbeitet (IP-Adresse, Datum und Uhrzeit, aufgerufene Adresse, Herkunftsseite, Browsertyp und Betriebssystem), um die Seite auszuliefern, die Stabilität zu sichern und Missbrauch abzuwehren. Rechtsgrundlage ist unser berechtigtes Interesse an einem sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO). Die Logfiles werden nur so lange gespeichert, wie es dafür erforderlich ist.</p>
    <h2>4. Statistik und Einwilligung</h2>
    <p>Beim ersten Besuch fragt Sie ein Hinweisfenster des Markentrix-Portals, ob Sie der Besucherstatistik zustimmen. Statistik-Dienste, die Cookies setzen oder Daten auf Ihrem Gerät speichern, werden nur mit Ihrer Einwilligung geladen (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG). Welche Dienste das sind, wofür sie eingesetzt werden und wie lange Daten gespeichert werden, sehen Sie im Hinweisfenster. Ihre Einwilligung können Sie jederzeit mit Wirkung für die Zukunft widerrufen oder ändern: über „Statistik-Einstellungen“ unten auf jeder Seite.</p>
    <p>Unabhängig davon zählt das Portal Seitenaufrufe und einzelne Ereignisse (z. B. Klick auf „WhatsApp“, abgeschickte Anfrage) ohne Cookies und ohne Speicherung auf Ihrem Gerät. Übertragen werden die aufgerufene Seite, die Herkunftsseite (nur Domain), Kampagnenparameter (utm) und die Bildschirmbreite. Rechtsgrundlage ist unser berechtigtes Interesse an einer bedarfsgerechten Gestaltung der Website (Art. 6 Abs. 1 lit. f DSGVO). Wenn Ihr Browser „Do Not Track“ oder „Global Privacy Control“ sendet, wird nichts gezählt.</p>
    <h2>5. Anfragen über die Website-Formulare</h2>
    <p>Wenn Sie das Kontakt-, Termin-, Gutschein-, Firmenkunden- oder Widerrufsformular nutzen, werden Ihre Angaben (z. B. Name, Telefonnummer, E-Mail-Adresse, Fahrzeug, Wunschtermin, Nachricht) verschlüsselt an das Markentrix-Portal übertragen, dort gespeichert und zur Bearbeitung Ihrer Anfrage verwendet (Art. 6 Abs. 1 lit. b DSGVO, beim Widerruf lit. c). Der Inhaber wird per E-Mail und Push-Nachricht benachrichtigt. Sie erhalten an die angegebene E-Mail-Adresse eine Eingangsbestätigung mit Vorgangsnummer. Ein unsichtbares Prüffeld schützt die Formulare vor automatisierten Spam-Einträgen.</p>
    <p>Anfragen, aus denen kein Auftrag entsteht, löschen wir spätestens 12 Monate nach dem letzten Kontakt. Daten zu Aufträgen und Gutscheinen bewahren wir entsprechend den gesetzlichen Aufbewahrungsfristen (bis zu 10 Jahre für Buchungsbelege) auf.</p>
    <h2>6. Terminbuchung</h2>
    <p>Bei der Terminbuchung fragt die Website beim Markentrix-Portal ab, an welchen Tagen und zu welchen Uhrzeiten Termine frei sind. Ihre Buchung (gewählte Leistung, Fahrzeug, Tag, Uhrzeit und Kontaktdaten) wird im Portal gespeichert. Wir bestätigen den Termin per E-Mail oder telefonisch und melden uns vorab, um das Fahrzeug anzusehen. Dies dient der Durchführung des Vertrags (Art. 6 Abs. 1 lit. b DSGVO).</p>
    <h2>7. Anzahlung per PayPal</h2>
    <p>Für die Anzahlung können Sie nach der Buchung einen PayPal.me-Link öffnen. Erst mit dem Klick werden Sie zu PayPal weitergeleitet (PayPal (Europe) S.à r.l. et Cie, S.C.A., 22–24 Boulevard Royal, L-2449 Luxemburg). Ihre Zahlungsdaten geben Sie direkt bei PayPal ein, die Website erhält sie nicht. Von PayPal erhalten wir Name, Betrag, Verwendungszweck und Zahlungsstatus. Rechtsgrundlage ist die Vertragsdurchführung (Art. 6 Abs. 1 lit. b DSGVO). Es gilt die <a href="https://www.paypal.com/de/legalhub/privacy-full" target="_blank" rel="noopener">Datenschutzerklärung von PayPal</a>.</p>
    <h2>8. Google-Bewertungen</h2>
    <p>Bewertungen aus unserem Google-Unternehmensprofil werden über das Markentrix-Portal auf dieser Website angezeigt. Außerdem zeigen wir einzelne öffentlich einsehbare Bewertungen auszugsweise (Anzeigename und Bewertungstext). Rechtsgrundlage ist unser berechtigtes Interesse an der Außendarstellung (Art. 6 Abs. 1 lit. f DSGVO). Auf Wunsch entfernen wir ein Zitat umgehend nach Nachricht an <a href="mailto:{s["email"]}">{ESC(s["email"])}</a>.</p>
    <h2>9. Kontakt per WhatsApp, E-Mail oder Telefon</h2>
    <p>WhatsApp-Links führen zum Messenger-Dienst der WhatsApp Ireland Ltd. / Meta Platforms Ireland Limited, 4 Grand Canal Square, Dublin 2, Irland. Erst wenn Sie dort eine Nachricht senden, werden Daten an WhatsApp übertragen; es gilt die Datenschutzerklärung von WhatsApp, eine Übermittlung in die USA ist nicht auszuschließen. Die Nutzung ist freiwillig, alternativ erreichen Sie uns über das Formular, per E-Mail oder Telefon. Bei Kontakt per E-Mail oder Telefon verarbeiten wir Ihre Angaben zur Bearbeitung der Anfrage (Art. 6 Abs. 1 lit. b, f DSGVO). Unser E-Mail-Postfach liegt bei: {mail}.</p>
    <h2>10. Google Maps</h2>
    <p>Die Kartendarstellung wird erst nach Ihrem Klick auf „Karte laden“ eingebunden (Zwei-Klick-Lösung). Erst dann wird eine Verbindung zu Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland hergestellt, wobei IP-Adresse und ggf. Cookies übertragen werden können. Rechtsgrundlage ist Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG). Informationen: <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">policies.google.com/privacy</a>.</p>
    <h2>11. Verweise auf soziale Netzwerke</h2>
    <p>Diese Website enthält reine Verlinkungen (keine eingebetteten Plugins) zu Instagram und Facebook (Meta Platforms Ireland Limited) sowie TikTok (TikTok Technology Limited, Irland). Ohne Klick findet keine Datenübertragung an diese Anbieter statt.</p>
    <h2>12. Gutscheine</h2>
    <p>Für bestellte Gutscheine speichern wir Käufer, Empfängername, Wert, Code und Einlösestatus zur Vertragsabwicklung und zur Erfüllung steuerlicher Pflichten (Art. 6 Abs. 1 lit. b, c DSGVO).</p>
    <h2>13. Ihre Rechte</h2>
    <ul>
      <li>Auskunft (Art. 15 DSGVO)</li><li>Berichtigung (Art. 16 DSGVO)</li><li>Löschung (Art. 17 DSGVO)</li>
      <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li><li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
      <li>Widerspruch gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 21 DSGVO)</li><li>Widerruf erteilter Einwilligungen mit Wirkung für die Zukunft (Art. 7 Abs. 3 DSGVO)</li>
    </ul>
    <p>Zudem besteht ein Beschwerderecht bei einer Datenschutz-Aufsichtsbehörde, z. B. bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
    <h2>14. Keine automatisierte Entscheidungsfindung</h2>
    <p>Wir setzen keine automatisierte Entscheidungsfindung oder Profiling im Sinne des Art. 22 DSGVO ein.</p>
    <h2>15. Verschlüsselung</h2>
    <p>Diese Seite nutzt eine TLS-Verschlüsselung, erkennbar an „https://“ in der Adresszeile.</p>
'''
    for fname, title, desc, h1, sub, content in [
        ("impressum.html", "Impressum | ElbDetail Fahrzeugaufbereitung Celle", "Impressum von ElbDetail, Fahrzeugaufbereitung in Celle, Lachtehäuser Straße 1: Anbieterkennzeichnung, Kontakt und rechtliche Angaben nach DDG.", "Impressum", "Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG)", imp),
        ("datenschutz.html", "Datenschutzerklärung | ElbDetail Fahrzeugaufbereitung Celle", "Datenschutzerklärung von ElbDetail: Hosting bei Markentrix in Nürnberg, Formulare und Termine über das Website-Portal, Statistik nur mit Einwilligung.", "Datenschutzerklärung", f"Stand: {s['stand']}", ds)]:
        body = f'''
<main id="main" class="legal-main">
  <div class="container">
    <a class="back-home" href="index.html">&larr; Zurück zur Startseite</a>
    <h1>{h1}</h1>
    <p class="legal-updated">{sub}</p>
    {content}
  </div>
</main>
'''
        write(fname, core.head(site, title, desc, "/" + fname) + core.header(site) + body + core.footer(site))


# --------------------------------------------------------------------------- 404 und Danke
def build_404(site, write):
    body = f'''
<main id="main" class="notfound">
  <div class="container notfound-inner">
    <span class="code">404</span>
    <h1>Diese Seite gibt es nicht (mehr).</h1>
    <p class="notfound-text">Vielleicht ein Tippfehler im Link. Alles zu Fahrzeugaufbereitung in Celle finden Sie auf der Startseite.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/">Zur Startseite</a>
      <a class="btn btn-line-light" href="/termin.html">Termin anfragen</a>
    </div>
  </div>
</main>
'''
    page = core.head(site, "Seite nicht gefunden | ElbDetail", "Die angeforderte Seite wurde nicht gefunden.", "/404.html", prefix="/", noindex=True) + core.header(site, "/") + body + core.footer(site, "/")
    write("404.html", page)


def build_danke(site, write):
    body = f'''
<main id="main">
  <section class="page-hero" aria-labelledby="page-h">
    <div class="container">
      <p class="eyebrow">Anfrage eingegangen</p>
      <h1 id="page-h" data-thanks-title>Danke! <em>Wir melden uns schnell.</em></h1>
      <p class="lead" data-thanks-text>Ihre Anfrage ist bei uns angekommen. In der Regel antworten wir am selben oder nächsten Werktag mit einem verbindlichen Angebot und einem Terminvorschlag.</p>
      <div class="thanks-pay" data-thanks-pay hidden></div>
      <div class="hero-actions">
        <a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich habe gerade eine Anfrage über die Website geschickt.")}" target="_blank" rel="noopener">{I["wa"]}Rückfrage per WhatsApp</a>
        <a class="btn btn-line" href="index.html">Zur Startseite</a>
      </div>
    </div>
  </section>
  <section aria-labelledby="next-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">So geht es weiter</p><h2 id="next-h" class="display">Die nächsten Schritte.</h2></div>
      <div class="process-rail">
        <div class="process-cell"><span class="process-index">JETZT</span><h3>Eingangsbestätigung</h3><p>Sie erhalten gleich eine E-Mail mit Ihren Angaben und der Vorgangsnummer.</p></div>
        <div class="process-cell"><span class="process-index">BALD</span><h3>Angebot &amp; Termin</h3><p>Wir prüfen Ihre Angaben und melden uns per WhatsApp, Telefon oder E-Mail, ganz nach Ihrem Wunsch.</p></div>
        <div class="process-cell"><span class="process-index">TIPP</span><h3>Fotos helfen</h3><p>Schick uns gern ein paar Fotos vom Zustand per WhatsApp. So wird das Angebot noch genauer.</p></div>
      </div>
    </div>
  </section>
</main>
'''
    write("danke.html", core.head(site, "Danke für Ihre Anfrage | ElbDetail", "Ihre Anfrage bei ElbDetail ist eingegangen. Wir melden uns mit Angebot und Terminvorschlag, meist am selben oder nächsten Werktag.", "/danke.html", noindex=True) + core.header(site) + body + core.footer(site))
