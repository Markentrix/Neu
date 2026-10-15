# -*- coding: utf-8 -*-
"""Startseite, Leistungsseiten, Rechtsseiten, 404 und Danke-Seite."""
import core
import md
import seo
from core import ESC, I, STARS5, inl


# --------------------------------------------------------------------------- Vorher/Nachher
def _ba_placeholder(n):
    before = f'''<svg class="ba-art" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="b{n}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a3d44"/><stop offset="1" stop-color="#23262c"/></linearGradient><filter id="n{n}"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2"/><feColorMatrix values="0 0 0 0 0.5 0 0 0 0 0.45 0 0 0 0 0.4 0 0 0 0.25 0"/></filter></defs><rect width="400" height="300" fill="url(#b{n})"/><rect width="400" height="300" filter="url(#n{n})"/><path d="M40 210c20-70 70-110 160-110s140 40 160 110" fill="none" stroke="#7a7f88" stroke-width="10" stroke-linecap="round"/><circle cx="120" cy="225" r="26" fill="#55595f"/><circle cx="280" cy="225" r="26" fill="#55595f"/><circle cx="90" cy="120" r="30" fill="#6b5d4a" opacity=".45"/><circle cx="300" cy="90" r="22" fill="#6b5d4a" opacity=".4"/></svg>'''
    after = f'''<svg class="ba-art ba-after" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="a{n}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2c3340"/><stop offset=".55" stop-color="#1b2029"/><stop offset="1" stop-color="#101318"/></linearGradient><linearGradient id="s{n}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#5b9be8" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><rect width="400" height="300" fill="url(#a{n})"/><path d="M40 210c20-70 70-110 160-110s140 40 160 110" fill="none" stroke="#dfe7f3" stroke-width="10" stroke-linecap="round"/><path d="M60 196c20-56 62-90 140-90" fill="none" stroke="url(#s{n})" stroke-width="4" stroke-linecap="round"/><circle cx="120" cy="225" r="26" fill="#eef2f7"/><circle cx="280" cy="225" r="26" fill="#eef2f7"/><circle cx="120" cy="225" r="12" fill="#1c4f9c"/><circle cx="280" cy="225" r="12" fill="#1c4f9c"/></svg>'''
    return before, after


def picture(site, name, alt, cls, prefix, sizes="(min-width: 900px) 33vw, 90vw"):
    m = site.media.get(name)
    if not m:
        return ""
    srcs = ""
    if m.get("avif"):
        srcs += f'<source type="image/avif" srcset="{", ".join(prefix + s for s in m["avif"])}" sizes="{sizes}">'
    if m.get("webp"):
        srcs += f'<source type="image/webp" srcset="{", ".join(prefix + s for s in m["webp"])}" sizes="{sizes}">'
    return (f'<picture class="{cls}">{srcs}<img src="{prefix}{m["src"]}" alt="{ESC(alt)}" width="{m["w"]}" height="{m["h"]}" '
            f'loading="lazy" decoding="async"></picture>')


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


# --------------------------------------------------------------------------- Startseite
def plan_card(site, p, prefix=""):
    lis = "".join(f'<li class="{"" if f["included"] else "no"}">{I["check"] if f["included"] else I["x"]}{ESC(f["text"])}</li>' for f in p["features"])
    cls0 = site.pricing["classes"][0]["key"]
    featured = p.get("featured")
    return f'''
        <article class="plan{" is-featured" if featured else ""} reveal" data-plan="{p["key"]}">
          {'<span class="plan-badge">Am häufigsten gebucht</span>' if featured else ""}
          <h3>{ESC(p["name"])}</h3>
          <p class="plan-for">{ESC(p["for"])}</p>
          <div class="plan-price"><span class="from">ab</span><span class="amount">{p["prices"][cls0]} €</span></div>
          <div class="plan-meta"><span>{I["clock"]}{ESC(p["duration"])}</span><span>{I["hand"]}Handarbeit</span></div>
          <ul>{lis}</ul>
          <a class="btn {"btn-primary" if featured else "btn-line-light"}" href="{prefix}termin.html?paket={p["key"]}" data-book="{p["key"]}">{I["cal"]}{ESC(p["name"])} anfragen</a>
          <a class="text-link plan-wa" href="{site.wa()}" data-wa-plan="{p["key"]}" target="_blank" rel="noopener">{I["wa"]}oder per WhatsApp</a>
        </article>'''


def build_home(site, write):
    s = site.s
    pr = site.pricing
    title = "Fahrzeugaufbereitung Celle | ElbDetail – Innenreinigung, Lackpolitur & Versiegelung"
    desc = (f"ElbDetail: professionelle Fahrzeugaufbereitung in Celle. Innen- & Außenaufbereitung, Lackpolitur, Lackversiegelung – "
            f"{s['rating']['value']} ★ bei Google, Koch-Chemie geschult. Richtpreise ab {site.min_price('frisch')} €. Termin online anfragen.")
    ld = [seo.business(site), seo.website(site), seo.faq(site.faq),
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
    price_cls = "".join(f'<label><input type="radio" name="pclass" value="{c["key"]}"{" checked" if i == 0 else ""}><span>{ESC(c["name"])}</span></label>' for i, c in enumerate(pr["classes"]))
    plans = "".join(plan_card(site, p) for p in pr["packages"])
    extras = "".join(f"<li>{ESC(e)} <small>· auf Anfrage</small></li>" for e in pr["extras"])

    def cell(v, f=False):
        c = ("featured-col " if f else "") + ("yes" if v else "")
        return f'<td class="{c.strip()}"><span aria-hidden="true">{"✓" if v else "—"}</span><span class="visually-hidden">{"Inklusive" if v else "Nicht enthalten"}</span></td>'
    keys = [p["key"] for p in pr["packages"]]
    fkey = feat["key"]
    trs = "".join(f'<tr><th scope="row">{ESC(r["label"])}</th>' + "".join(cell(r.get(k), k == fkey) for k in keys) + "</tr>" for r in pr["compare"])
    fc = ' class="featured-col"'
    ths = "".join(f'<th scope="col"{fc if p["key"] == fkey else ""}>{ESC(p["name"])}</th>' for p in pr["packages"])

    tiles, real = [], 0
    for n, it in enumerate(site.gallery):
        h, has = ba_tile(site, it, n + 1)
        tiles.append(h); real += has
    gallery_note = ("Ziehe den Regler, um den Unterschied zu sehen. Weitere aktuelle Arbeiten zeigen wir laufend auf Instagram und TikTok."
                    if real else "Die Darstellungen sind Platzhalter, bis die ersten Vorher-/Nachher-Fotos online sind. Echte Ergebnisse findest du jederzeit auf Instagram und TikTok.")

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
        <h2 id="ratgeber-h" class="display">Wissen aus der Werkstatt.</h2>
        <p>Ehrliche Antworten auf die Fragen, die wir täglich hören. Von Preisen über Leasingrückgabe bis zur richtigen Lackpflege im Winter.</p>
      </div>
      <div class="article-grid stagger">{art_cards}</div>
      <p class="section-more"><a class="btn btn-line-light" href="ratgeber/index.html">Alle Ratgeber-Artikel</a></p>
    </div>
  </section>''' if articles else ""

    body = f'''
<main id="main">

  <section class="hero" aria-labelledby="hero-h">
    <div class="hero-bg-grid" aria-hidden="true"></div>
    <div class="container hero-inner">
      <div class="hero-copy">
        <div class="hero-kicker">
          <a class="hero-badge" href="#bewertungen">{STARS5} {ESC(s["rating"]["value"])} · {s["rating"]["count"]} Google-Bewertungen</a>
          <span class="hero-badge">{I["pin"]} {ESC(s["address"]["city"])} · {ESC(s["address"]["street"])}</span>
        </div>
        <h1 id="hero-h" class="hero-headline">Fahrzeug&shy;aufbereitung in Celle. <em>Dein Auto, wie neu.</em></h1>
        <p class="hero-sub">Innen- &amp; Außenaufbereitung, Lackpolitur und Lackversiegelung <strong>in Handarbeit</strong> mit Koch-Chemie-Produkten. Transparente Richtpreise ab {site.min_price("frisch")}&nbsp;€, verbindliches Angebot vor dem Termin.</p>
        <div class="hero-actions">
          <a class="btn btn-primary btn-lg" href="termin.html">{I["cal"]}Termin online anfragen</a>
          <a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich möchte einen Termin anfragen. Fahrzeug: … Wunsch: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        </div>
        <ul class="hero-proof">
          <li>{I["shield"]}Koch-Chemie geschult</li>
          <li>{I["hand"]}100 % Handarbeit, keine Waschstraße</li>
          <li>{I["euro"]}Festpreis vor dem Termin</li>
        </ul>
      </div>

      <form class="quote-card" id="quoteForm" aria-labelledby="quote-h">
        <div class="quote-head"><h2 id="quote-h">Richtpreis in 10 Sekunden</h2><span>Unverbindlich</span></div>
        <fieldset class="quote-field"><legend><span>Fahrzeugklasse</span></legend><div class="seg">{cls_radios}</div></fieldset>
        <fieldset class="quote-field"><legend><span>Paket</span></legend><div class="seg pk">{pkg_radios}</div></fieldset>
        <div class="quote-result" aria-live="polite">
          <span class="lbl">Richtpreis <span id="quotePkgName">{ESC(feat["name"])}</span></span>
          <span class="val" id="quoteValue"><small>ab</small>{feat["prices"][cls0]}&nbsp;€</span>
        </div>
        <a class="btn btn-primary" id="quoteBook" href="termin.html?paket={feat["key"]}&amp;klasse={cls0}">{I["cal"]}Mit diesem Paket Termin anfragen</a>
        <a class="quote-wa" id="quoteWa" href="{site.wa()}" target="_blank" rel="noopener">{I["wa"]}oder Angebot per WhatsApp</a>
        <p class="quote-note">Richtwert für normalen Pflegezustand. Der verbindliche Preis hängt von Fahrzeug und Zustand ab und wird vor dem Termin bestätigt.</p>
      </form>
    </div>
  </section>

  <div class="trust-bar" aria-label="Vertrauen">
    <div class="container">
      <ul>
        <li>{I["star"]}<span>{ESC(s["rating"]["value"])} von 5 Sternen<small>{s["rating"]["count"]} Google-Bewertungen</small></span></li>
        <li>{I["shield"]}<span>Koch-Chemie geschult<small>Profi-Produkte, keine Baumarktware</small></span></li>
        <li>{I["hand"]}<span>100 % Handarbeit<small>Keine Waschstraße, keine Kratzer</small></span></li>
        <li>{I["euro"]}<span>Preis vorab bestätigt<small>Keine Überraschungen bei Abholung</small></span></li>
      </ul>
    </div>
  </div>

  <section id="anlaesse" class="soft" aria-labelledby="anlaesse-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Wofür Kund:innen zu uns kommen</p>
        <h2 id="anlaesse-h" class="display">Der richtige Moment für eine Aufbereitung.</h2>
        <p>Ob Alltag, Verkauf oder Rückgabe: Eine professionelle Aufbereitung zahlt sich fast immer aus. In Geld, in Zeit oder einfach im Gefühl beim Einsteigen.</p>
      </div>
      <div class="usecase-grid stagger">
        <a class="usecase reveal" href="leistungen/leasingrueckgabe-gebrauchtwagen-celle.html">{I["key"]}<h3>Leasingrückgabe</h3><p>Verschmutzung, Gerüche und Gebrauchsspuren kosten bei der Rückgabe bares Geld. Wir bereiten das Fahrzeug so auf, dass möglichst wenig beanstandet wird.</p><span class="more">Mehr erfahren →</span></a>
        <a class="usecase reveal" href="leistungen/leasingrueckgabe-gebrauchtwagen-celle.html">{I["tag"]}<h3>Gebrauchtwagenverkauf</h3><p>Ein sauberes, glänzendes Auto verkauft sich schneller und zu einem besseren Preis. Die Aufbereitung holt sich in der Regel mehrfach wieder rein.</p><span class="more">Mehr erfahren →</span></a>
        <a class="usecase reveal" href="leistungen/innenaufbereitung-celle.html">{I["paw"]}<h3>Familie, Hund &amp; Alltag</h3><p>Krümel, Tierhaare, Flecken und Gerüche: Die Innenaufbereitung bringt den Innenraum zurück in den Zustand, in dem man gern einsteigt.</p><span class="more">Innenaufbereitung →</span></a>
        <a class="usecase reveal" href="aktion/winterschutz.html">{I["snow"]}<h3>Lack winterfest machen</h3><p>Vor dem ersten Streusalz versiegeln: Schmutz und Salz haften weniger, Waschen wird leichter und der Lack bleibt länger wie am ersten Tag.</p><span class="more">Winter-Lackschutz →</span></a>
        <a class="usecase reveal" href="leistungen/lackpolitur-celle.html">{I["spark"]}<h3>Matter, verkratzter Lack</h3><p>Waschstraßenkratzer, Hologramme und Oxidation nehmen jedem Auto den Glanz. Eine mehrstufige Politur holt die Tiefe zurück.</p><span class="more">Lackpolitur →</span></a>
        <a class="usecase reveal" href="firmenkunden.html">{I["brief"]}<h3>Firmenwagen &amp; Flotten</h3><p>Planbare Pflege für Firmenfahrzeuge, Autohäuser und Leasingrückläufer in Celle und Umgebung. Ein Ansprechpartner, feste Abläufe.</p><span class="more">Für Firmenkunden →</span></a>
      </div>
    </div>
  </section>

  <section id="leistungen" aria-labelledby="leistungen-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Leistungen</p>
        <h2 id="leistungen-h" class="display">Aufbereitung, die man sieht. Und fühlt.</h2>
        <p>Vom schnellen Frischekick bis zur vollständigen Neuaufbereitung: Jedes Fahrzeug bekommt die Behandlung, die zu seinem Zustand passt. Alle Leistungen auch einzeln buchbar.</p>
      </div>
      <div class="service-list stagger">{services_rows}
      </div>
      <div class="brand-strip reveal">
        {I["shield"]}
        <p>Geschult in den Lehrgängen von Koch-Chemie setzen wir für alle Arbeiten ausschließlich professionelle Koch-Chemie-Pflegeprodukte ein, abgestimmt auf Lack, Leder, Kunststoff und Textil.</p>
        <a href="https://www.koch-chemie.com/de/produkte/automotive" target="_blank" rel="noopener">Produkte ansehen ↗</a>
      </div>
    </div>
  </section>

  <section id="preise" class="soft" aria-labelledby="preise-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Pakete &amp; Preise</p>
        <h2 id="preise-h" class="display">Transparente Richtpreise. Keine Überraschungen.</h2>
        <p>Wähle deine Fahrzeugklasse und sieh sofort, womit du rechnen kannst. Den verbindlichen Preis bestätigen wir kostenlos vor dem Termin.</p>
      </div>
      <div class="price-toolbar reveal">
        <fieldset id="priceClass"><legend class="visually-hidden">Fahrzeugklasse wählen</legend><div class="seg">{price_cls}</div></fieldset>
        <p>Richtpreise für <strong id="priceClassLabel">{ESC(pr["classes"][0]["name"])}</strong> in normalem Pflegezustand.</p>
      </div>
      <div class="plans stagger">{plans}
      </div>
      <p class="price-note">{ESC(pr["note"])}</p>
      <div class="extras reveal">
        <h3>Einzeln buchbar oder als Ergänzung</h3>
        <ul>{extras}</ul>
      </div>
      <details class="compare reveal">
        <summary>Alle Leistungen der Pakete im Vergleich</summary>
        <div class="price-scroll" tabindex="0" role="region" aria-label="Vergleichstabelle, seitlich scrollbar">
          <table class="price-table">
            <caption class="visually-hidden">Vergleich der Aufbereitungspakete nach enthaltenen Leistungen</caption>
            <thead><tr><th scope="col">Leistung</th>{ths}</tr></thead>
            <tbody>{trs}</tbody>
          </table>
        </div>
      </details>
    </div>
  </section>

  <section id="vorher-nachher" aria-labelledby="vn-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Ergebnisse</p>
        <h2 id="vn-h" class="display">Vorher. Nachher. Selbst schieben.</h2>
        <p>Ziehe den Regler, um den Unterschied zu sehen.</p>
      </div>
      <div class="ba-grid stagger">{"".join(tiles)}
      </div>
      <p class="gallery-note">{ESC(gallery_note)} <a class="text-link" href="{s["social"]["instagram"]}" target="_blank" rel="noopener">Instagram</a> · <a class="text-link" href="{s["social"]["tiktok"]}" target="_blank" rel="noopener">TikTok</a></p>
    </div>
  </section>

  <section id="warum" class="dark on-dark" aria-labelledby="warum-h">
    <div class="container why-grid">
      <div class="reveal">
        <div class="section-head" style="margin-bottom:28px">
          <p class="eyebrow">Warum ElbDetail</p>
          <h2 id="warum-h" class="display">Handarbeit, Fachwissen und ein Preis, der vorher feststeht.</h2>
          <p>ElbDetail ist ein inhabergeführter Fachbetrieb für Fahrzeugaufbereitung in Celle. Kein Franchise, keine Waschstraße: Jedes Fahrzeug wird persönlich und von Hand aufbereitet.</p>
        </div>
        <dl class="facts" id="auf-einen-blick">
          <div><dt>Betrieb</dt><dd>{ESC(s["name"])} – {ESC(s["tagline"])}</dd></div>
          <div><dt>Standort</dt><dd>{ESC(site.addr_line())}</dd></div>
          <div><dt>Einzugsgebiet</dt><dd>Celle und Landkreis Celle</dd></div>
          <div><dt>Leistungen</dt><dd>Innen- &amp; Außenaufbereitung, Lackpolitur, Lackversiegelung, Lederpflege, Geruchsentfernung</dd></div>
          <div><dt>Richtpreise</dt><dd>{" / ".join(f"ab {site.min_price(p['key'])} €" for p in pr["packages"])} (Kompaktklasse)</dd></div>
          <div><dt>Produkte</dt><dd>Koch-Chemie (Lehrgänge absolviert)</dd></div>
          <div><dt>Bewertung</dt><dd>{ESC(s["rating"]["value"])} ★ bei {s["rating"]["count"]} Google-Rezensionen (Stand {ESC(s["rating"]["asOf"])})</dd></div>
          <div><dt>Termin</dt><dd><a href="termin.html">Online-Terminanfrage</a> oder <a href="{site.wa()}" target="_blank" rel="noopener">WhatsApp {ESC(s["phoneIntl"])}</a></dd></div>
        </dl>
      </div>
      <div class="why-list stagger">
        <div class="why-item reveal">{I["hand"]}<div><h3>Handarbeit statt Waschstraße</h3><p>Zwei-Eimer-Handwäsche, weiche Mikrofaser, kratzfreie Trocknung. So entstehen keine neuen Swirls, während alte verschwinden.</p></div></div>
        <div class="why-item reveal">{I["shield"]}<div><h3>Koch-Chemie geschult</h3><p>Produkte und Verfahren aus dem Profibereich, abgestimmt auf Lack, Leder, Alcantara, Kunststoff und Textil. Kein Experimentieren an deinem Auto.</p></div></div>
        <div class="why-item reveal">{I["euro"]}<div><h3>Preis vor dem Termin</h3><p>Du bekommst ein verbindliches Angebot, bevor wir anfangen. Zusätzliche Arbeiten gibt es nur nach Rücksprache.</p></div></div>
        <div class="why-item reveal">{I["clock"]}<div><h3>Schnelle Antwort, flexible Termine</h3><p>Online-Anfrage oder WhatsApp, Termin nach Vereinbarung, samstags nach Absprache. Ideal auch kurzfristig vor Verkauf oder Rückgabe.</p></div></div>
        <div class="why-item reveal">{I["pin"]}<div><h3>Lokal in Celle</h3><p>Fester Standort in der Lachtehäuser Straße, gut erreichbar aus der Innenstadt, Westercelle, Altencelle, Garßen und dem gesamten Landkreis.</p></div></div>
      </div>
    </div>
  </section>

  <section id="ablauf" aria-labelledby="ablauf-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Ablauf</p>
        <h2 id="ablauf-h" class="display">In vier Schritten zum Auto wie neu.</h2>
      </div>
      <div class="process-rail stagger">
        <div class="process-cell reveal"><span class="process-index">SCHRITT 01</span><h3>Anfrage in 2 Minuten</h3><p>Online-Terminanfrage oder WhatsApp mit Fahrzeug, Wunschpaket und Wunschtermin. Gern mit Fotos vom Zustand.</p></div>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 02</span><h3>Angebot &amp; Termin</h3><p>Du bekommst ein verbindliches Angebot und eine Terminbestätigung. Erst wenn beides passt, geht es los.</p></div>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 03</span><h3>Aufbereitung in Handarbeit</h3><p>Sorgfältige Aufbereitung an unserem Standort in Celle mit professionellen Koch-Chemie-Produkten.</p></div>
        <div class="process-cell reveal"><span class="process-index">SCHRITT 04</span><h3>Gemeinsame Abnahme</h3><p>Abschlusskontrolle mit dir bei Tageslicht, Pflegetipps für danach, Bezahlung bar oder per Überweisung.</p></div>
      </div>
    </div>
  </section>

  <section id="bewertungen" class="soft" aria-labelledby="bewertungen-h">
    <div class="container">
      <div class="section-head reveal" style="margin-bottom:28px;">
        <p class="eyebrow">Bewertungen</p>
        <h2 id="bewertungen-h" class="display">Was Kund:innen aus Celle sagen.</h2>
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
      <div class="review-grid stagger" tabindex="0" role="region" aria-label="Kundenbewertungen">{core.review_cards(site)}
      </div>
      <p class="gallery-note">Echte Rezensionen aus unserem Google-Unternehmensprofil (Stand {ESC(s["rating"]["asOf"])}), gekürzt um Emojis. <strong>Hinweis zur Echtheit:</strong> Die Bewertungen werden auf Google von Nutzer:innen veröffentlicht. Wir selbst prüfen nicht, ob jede Bewertung von einer Person stammt, die unsere Leistung genutzt hat; Google prüft Bewertungen nach eigenen Richtlinien. Wir übernehmen ausgewählte Bewertungen unverändert im Wortlaut.</p>
    </div>
  </section>

  <section class="tight" aria-labelledby="gift-h">
    <div class="container">
      <div class="promo-band reveal">
        <div class="promo-icon">{I["gift"]}</div>
        <div>
          <h2 id="gift-h">Verschenke ein Auto wie neu.</h2>
          <p>Gutscheine für Wunschbetrag oder Paket, mit persönlicher Nachricht. Ideal zu Weihnachten, zum Geburtstag oder als Dankeschön.</p>
        </div>
        <a class="btn btn-primary" href="gutscheine.html">Gutschein gestalten</a>
      </div>
    </div>
  </section>

  <section id="einzugsgebiet" aria-labelledby="gebiet-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Einzugsgebiet</p>
        <h2 id="gebiet-h" class="display">Fahrzeugaufbereitung für Celle und den Landkreis.</h2>
        <p>Unser Standort liegt in der {ESC(s["address"]["street"])} im Osten von Celle, wenige Minuten von der Altstadt. Kund:innen kommen aus der ganzen Stadt und dem Umland.</p>
      </div>
      <div class="area-grid reveal">
        <div><h3>Stadt Celle</h3><ul class="chips">{"".join(f"<li>{ESC(x)}</li>" for x in s["areas"]["city"])}</ul></div>
        <div>
          <h3>Umland &amp; Landkreis Celle</h3>
          <ul class="chips">{"".join(f"<li>{ESC(x)}</li>" for x in s["areas"]["region"])}</ul>
          <p class="area-note">Du kommst von weiter her, zum Beispiel aus Hannover, Gifhorn oder Uelzen? Kein Problem, die meisten Pakete lassen sich an einem Tag erledigen.</p>
        </div>
      </div>
    </div>
  </section>
{ratgeber_section}
  <section id="faq" class="soft" aria-labelledby="faq-h">
    <div class="container">
      <div class="section-head reveal">
        <p class="eyebrow">Häufige Fragen</p>
        <h2 id="faq-h" class="display">Gut zu wissen, bevor du anfragst.</h2>
      </div>
      <div class="faq-list stagger">
        {core.faq_html(site.faq)}
      </div>
    </div>
  </section>

{core.contact_section(site)}
{core.cta_band(site)}
</main>
'''
    write("index.html", core.head(site, title, desc, "/", ld=ld, og_type="business.business") + core.header(site, home=True) + body + core.footer(site, home=True))


# --------------------------------------------------------------------------- Leistungsseiten
def build_service(site, sv, write):
    prefix = "../"
    path = "/leistungen/" + sv["slug"] + ".html"
    p = site.pkg(sv["package"])
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
        <a class="btn btn-primary btn-lg" href="{prefix}termin.html?paket={p["key"]}">{I["cal"]}Termin anfragen</a>
        <a class="btn btn-wa btn-lg" href="{wa}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        <a class="btn btn-line" href="{prefix}index.html#preise">Alle Pakete &amp; Preise</a>
      </div>
    </div>
  </section>

  <section aria-label="Details">
    <div class="container two-up">
      <div class="prose">
        {intro}
        <h2 id="enthalten">Das ist enthalten</h2>
        <ul class="includes">{includes}</ul>
        <h2 id="ablauf">So läuft es ab</h2>
        <div class="steps">{steps}</div>
        <h2 id="fragen">Häufige Fragen zu {ESC(sv["short"])}</h2>
        <div class="faq-list stagger">{core.faq_html(sv["faq"], prefix)}</div>
      </div>
      <aside class="sticky-aside">
        <div class="aside-card dark">
          <h3>Termin in Celle anfragen</h3>
          <p>Paket, Fahrzeug und Wunschtermin in 2 Minuten. Du bekommst ein verbindliches Angebot vor dem Termin.</p>
          <a class="btn btn-primary" href="{prefix}termin.html?paket={p["key"]}">{I["cal"]}Online-Terminanfrage</a>
          <a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener">{I["wa"]}WhatsApp {ESC(site.s["phoneIntl"])}</a>
          <p>{ESC(site.addr_line())} · {ESC(site.s["openingHours"]["text"])}</p>
        </div>
        <div class="aside-card">
          <h3>Passendes Paket</h3>
          <p><strong>{ESC(p["name"])}</strong> enthält diese Leistung, Richtpreis ab {site.min_price(p["key"])} € für eine Kompaktklasse.</p>
          <a class="btn btn-line-light" href="{prefix}index.html#preise">Pakete vergleichen</a>
        </div>
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
    vat = (f"<p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: {ESC(L['vatId'])}</p>" if L.get("vatId")
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
    <p>Unser Angebot enthält Links zu externen Websites Dritter (z. B. Google Maps, Instagram, Facebook, TikTok, WhatsApp, Koch-Chemie), auf deren Inhalte wir keinen Einfluss haben. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter verantwortlich.</p>
    <h2>Urheberrecht</h2>
    <p>Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Beiträge Dritter sind als solche gekennzeichnet.</p>
    <h2>Hinweis zu Preisangaben</h2>
    <p>Alle auf dieser Website genannten Preise sind unverbindliche Richtwerte inklusive gesetzlicher Umsatzsteuer für Fahrzeuge in normalem Pflegezustand. Ein verbindliches Angebot erfolgt individuell nach Fahrzeug und Zustand.</p>
'''
    mail = _ph(L.get("mailProvider"), "E-Mail-Anbieter mit Anschrift, z. B. der Anbieter des Postfachs info@elbdetail.de")
    ds = f'''
    <h2>1. Verantwortlicher</h2>
    <p>Verantwortlicher im Sinne der Datenschutz-Grundverordnung (DSGVO) ist:<br>
      {_ph(L.get("owner"), "Vollständiger Name der Inhaberin / des Inhabers")}<br>
      {ESC(s["name"])} – {ESC(s["tagline"])}, {ESC(site.addr_line())}<br>
      E-Mail: <a href="mailto:{s["email"]}">{ESC(s["email"])}</a> · Telefon: {ESC(s["phoneIntl"])}</p>
    <h2>2. Grundsätzliches</h2>
    <p>Wir verarbeiten personenbezogene Daten nur, soweit dies zur Bereitstellung dieser Website, zur Bearbeitung von Anfragen und zur Durchführung unserer Leistungen erforderlich ist. Rechtsgrundlagen sind Art. 6 Abs. 1 lit. a DSGVO (Einwilligung), lit. b (Vertrag und Vertragsanbahnung), lit. c (rechtliche Pflichten) und lit. f (berechtigte Interessen).</p>
    <h2>3. Hosting auf eigenem Server</h2>
    <p>Diese Website, alle Formulare und die Besucherstatistik laufen auf einem von uns betriebenen Server im Rechenzentrum der {ESC(L.get("hosting") or "Hetzner Online GmbH")}. Die Daten verbleiben in Deutschland. Mit dem Rechenzentrumsbetreiber besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Es werden keine Inhalte, Schriftarten oder Skripte von fremden Servern nachgeladen.</p>
    <p>Beim Aufruf werden technisch notwendige Daten (u. a. IP-Adresse, Zeitpunkt, aufgerufene Adresse, Browsertyp) verarbeitet, um die Seite auszuliefern und vor Missbrauch zu schützen (Art. 6 Abs. 1 lit. f DSGVO). Zugriffsprotokolle mit IP-Adressen speichern wir nicht dauerhaft.</p>
    <h2>4. Keine Cookies, keine Tracking-Dienste</h2>
    <p>Diese Website setzt keine Cookies und bindet keine Analyse- oder Werbedienste Dritter ein (kein Google Analytics, kein Meta-Pixel). Ausnahme ist die freiwillig nachladbare Google-Karte (Ziffer 8).</p>
    <h2>5. Eigene, cookielose Besucherstatistik</h2>
    <p>Um die Website zu verbessern, zählen wir Seitenaufrufe und einzelne Ereignisse (z. B. Klick auf „WhatsApp“, abgeschickte Terminanfrage) mit einer selbst betriebenen Statistik auf unserem Server. Dabei werden keine Cookies gesetzt und nichts auf deinem Gerät gespeichert. Die IP-Adresse wird nicht gespeichert; zur Zählung eindeutiger Besuche wird aus IP-Adresse, Browserkennung und einem täglich wechselnden, nach 24 Stunden gelöschten Zufallswert ein nicht rückrechenbarer Kurzwert gebildet. Gespeichert werden: aufgerufene Seite, Herkunftsseite (nur Domain), Kampagnenparameter (utm), Gerätekategorie und Zeitpunkt. Eine Zuordnung zu einer Person ist nicht möglich. Rechtsgrundlage ist unser berechtigtes Interesse an einer bedarfsgerechten Gestaltung der Website (Art. 6 Abs. 1 lit. f DSGVO). Wenn dein Browser „Do Not Track“ oder „Global Privacy Control“ sendet, wird nichts gezählt.</p>
    <h2>6. Anfragen über die Website-Formulare</h2>
    <p>Wenn du das Kontakt-, Termin-, Gutschein- oder Firmenkundenformular nutzt, werden deine Angaben (z. B. Name, Telefonnummer, E-Mail-Adresse, Fahrzeug, Wunschtermin, Nachricht) verschlüsselt an unseren Server übertragen, dort in einer Datenbank gespeichert und zur Bearbeitung deiner Anfrage verwendet (Art. 6 Abs. 1 lit. b DSGVO). Zur Benachrichtigung senden wir uns eine E-Mail mit den Angaben; wenn du eine E-Mail-Adresse angibst, erhältst du eine Eingangsbestätigung. Für den E-Mail-Versand nutzen wir: {mail}.</p>
    <p>Anfragen, aus denen kein Auftrag entsteht, löschen wir spätestens 12 Monate nach dem letzten Kontakt. Daten zu Aufträgen und Gutscheinen bewahren wir entsprechend den gesetzlichen Aufbewahrungsfristen (bis zu 10 Jahre für Buchungsbelege) auf.</p>
    <h2>7. Kontakt per WhatsApp, E-Mail oder Telefon</h2>
    <p>WhatsApp-Links führen zum Messenger-Dienst der WhatsApp Ireland Ltd. / Meta Platforms Ireland Limited, 4 Grand Canal Square, Dublin 2, Irland. Erst wenn du dort eine Nachricht sendest, werden Daten an WhatsApp übertragen; es gilt die Datenschutzerklärung von WhatsApp, eine Übermittlung in die USA ist nicht auszuschließen. Die Nutzung ist freiwillig, alternativ erreichst du uns über das Formular, per E-Mail oder Telefon. Bei Kontakt per E-Mail oder Telefon verarbeiten wir deine Angaben zur Bearbeitung der Anfrage (Art. 6 Abs. 1 lit. b, f DSGVO).</p>
    <h2>8. Google Maps</h2>
    <p>Die Kartendarstellung wird erst nach deinem Klick auf „Karte laden“ eingebunden. Erst dann wird eine Verbindung zu Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland hergestellt, wobei IP-Adresse und ggf. Cookies übertragen werden können. Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG). Informationen: <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">policies.google.com/privacy</a>.</p>
    <h2>9. Verweise auf soziale Netzwerke</h2>
    <p>Diese Website enthält reine Verlinkungen (keine eingebetteten Plugins) zu Instagram und Facebook (Meta Platforms Ireland Limited) sowie TikTok (TikTok Technology Limited, Irland). Ohne Klick findet keine Datenübertragung an diese Anbieter statt.</p>
    <h2>10. Kundenstimmen</h2>
    <p>Wir zeigen auszugsweise öffentlich einsehbare Bewertungen aus unserem Google-Unternehmensprofil (Anzeigename und Bewertungstext). Rechtsgrundlage ist unser berechtigtes Interesse an der Außendarstellung (Art. 6 Abs. 1 lit. f DSGVO). Auf Wunsch entfernen wir ein Zitat umgehend nach Nachricht an <a href="mailto:{s["email"]}">{ESC(s["email"])}</a>.</p>
    <h2>11. Gutscheine</h2>
    <p>Für bestellte Gutscheine speichern wir Käufer, Empfängername, Wert, Code und Einlösestatus zur Vertragsabwicklung und zur Erfüllung steuerlicher Pflichten (Art. 6 Abs. 1 lit. b, c DSGVO). Der Gutschein ist über einen nicht erratbaren Link abrufbar.</p>
    <h2>12. Deine Rechte</h2>
    <ul>
      <li>Auskunft (Art. 15 DSGVO)</li><li>Berichtigung (Art. 16 DSGVO)</li><li>Löschung (Art. 17 DSGVO)</li>
      <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li><li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
      <li>Widerspruch gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 21 DSGVO)</li><li>Widerruf erteilter Einwilligungen mit Wirkung für die Zukunft (Art. 7 Abs. 3 DSGVO)</li>
    </ul>
    <p>Zudem besteht ein Beschwerderecht bei einer Datenschutz-Aufsichtsbehörde, z. B. bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
    <h2>13. Keine automatisierte Entscheidungsfindung</h2>
    <p>Wir setzen keine automatisierte Entscheidungsfindung oder Profiling im Sinne des Art. 22 DSGVO ein.</p>
    <h2>14. Verschlüsselung</h2>
    <p>Diese Seite nutzt eine TLS-Verschlüsselung, erkennbar an „https://“ in der Adresszeile.</p>
    <p class="legal-updated" style="margin-top:30px;">Hinweis für den Seitenbetreiber: Diese Datenschutzerklärung ist eine sorgfältig erstellte Vorlage für den Betrieb auf eigenem Server. Bitte Platzhalter im Verwaltungsportal unter „Inhalte → Grunddaten → Rechtliches“ ausfüllen und vor Veröffentlichung rechtlich prüfen lassen.</p>
'''
    for fname, title, desc, h1, sub, content in [
        ("impressum.html", "Impressum | ElbDetail Fahrzeugaufbereitung Celle", "Impressum von ElbDetail, Fahrzeugaufbereitung in Celle, Lachtehäuser Straße 1.", "Impressum", "Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG)", imp),
        ("datenschutz.html", "Datenschutzerklärung | ElbDetail Fahrzeugaufbereitung Celle", "Datenschutzerklärung von ElbDetail: eigener Server in Deutschland, keine Cookies, keine Tracking-Dienste.", "Datenschutzerklärung", f"Stand: {s['stand']}", ds)]:
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
  <div class="container" style="display:grid;gap:18px;justify-items:center">
    <span class="code">404</span>
    <h1>Diese Seite gibt es nicht (mehr).</h1>
    <p style="color:var(--muted);max-width:50ch">Vielleicht ein Tippfehler im Link. Alles zu Fahrzeugaufbereitung in Celle findest du auf der Startseite.</p>
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
      <p class="lead" data-thanks-text>Deine Anfrage ist bei uns angekommen. In der Regel antworten wir am selben oder nächsten Werktag mit einem verbindlichen Angebot und einem Terminvorschlag.</p>
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
        <div class="process-cell"><span class="process-index">JETZT</span><h3>Eingangsbestätigung</h3><p>Hast du eine E-Mail-Adresse angegeben, bekommst du gleich eine Bestätigung mit deinen Angaben.</p></div>
        <div class="process-cell"><span class="process-index">BALD</span><h3>Angebot &amp; Termin</h3><p>Wir prüfen deine Angaben und melden uns per WhatsApp, Telefon oder E-Mail, je nach deinem Wunsch.</p></div>
        <div class="process-cell"><span class="process-index">TIPP</span><h3>Fotos helfen</h3><p>Schick uns gern ein paar Fotos vom Zustand per WhatsApp. So wird das Angebot noch genauer.</p></div>
      </div>
    </div>
  </section>
</main>
'''
    write("danke.html", core.head(site, "Danke für deine Anfrage | ElbDetail", "Deine Anfrage bei ElbDetail ist eingegangen. Wir melden uns mit Angebot und Terminvorschlag, meist am selben oder nächsten Werktag.", "/danke.html", noindex=True) + core.header(site) + body + core.footer(site))
