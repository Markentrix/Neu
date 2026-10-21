# -*- coding: utf-8 -*-
"""Conversion-Seiten: Terminbuchung, Gutscheine, Firmenkunden, Winter-Aktion, Entwurf Pflege-Abo."""
import datetime

import core
import seo
from pages import offer_card, ref_wall
from core import ESC, I, STARS5


def _page_hero(prefix, crumbs, eyebrow, h1, lead, actions=""):
    return f'''  <section class="page-hero page-hero--compact" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, crumbs)}
      <p class="eyebrow">{eyebrow}</p>
      <h1 id="page-h">{h1}</h1>
      <p class="lead">{lead}</p>
      {actions}
    </div>
  </section>
'''


def _trust_list(site):
    s = site.s
    return f'''<ul class="mini-trust">
          <li>{I["star"]}{ESC(s["rating"]["value"])} ★ bei {s["rating"]["count"]} Google-Bewertungen</li>
          <li>{I["euro"]}Verbindlicher Preis vor dem Termin</li>
          <li>{I["hand"]}100 % Handarbeit, C²Coating Excellence Partner</li>
          <li>{I["shield"]}Daten bleiben auf unserem Server in Deutschland</li>
        </ul>'''


# --------------------------------------------------------------------------- Termin
def build_termin(site, write):
    pr = site.pricing
    s = site.s
    path = "/termin.html"
    title = "Termin anfragen: Fahrzeugaufbereitung Celle | ElbDetail"
    desc = "Fahrzeugaufbereitung in Celle online buchen: Paket wählen, Fahrzeug angeben, Tag und Uhrzeit aussuchen und per E-Mail-Link verbindlich bestätigen."
    ld = [seo.webpage(site, path, title, {"potentialAction": {"@type": "ReserveAction", "target": site.url + path}}),
          seo.crumbs(site, [("Startseite", "/"), ("Termin anfragen", path)])]
    cls0 = pr["classes"][0]["key"]

    slots = "".join(f'<label class="choice-pill"><input type="radio" name="uhrzeit" value="{t}" required><span><strong>{t} Uhr</strong></span></label>'
                    for t in (s.get("booking") or {}).get("slotTimes", ["08:00", "10:00", "13:00", "15:00"]))
    pk = ""
    for p in pr["packages"]:
        inc = "".join(f"<li>{ESC(f['text'])}</li>" for f in p["features"] if f.get("included"))[:]
        pk += f'''<label class="choice-card{" is-featured" if p.get("featured") else ""}">
            <input type="radio" name="paket" value="{p["key"]}" required{" checked" if p.get("featured") else ""}>
            <span class="choice-body">
              <span class="choice-head"><strong>{ESC(p["name"])}</strong><span class="choice-price" data-price-for="{p["key"]}">ab {p["prices"][cls0]} €</span></span>
              <span class="choice-sub">{ESC(p["for"])} · {ESC(p["duration"])}</span>
              <ul class="choice-feats">{inc}</ul>
            </span>
          </label>'''
    pk += f'''<label class="choice-card">
            <input type="radio" name="paket" value="keramik">
            <span class="choice-body">
              <span class="choice-head"><strong>Keramikversiegelung</strong><span class="choice-price">ab {site.min_price("keramik")} €</span></span>
              <span class="choice-sub">C² CarCeramic für den Lack ab Paket Signature oder beim Neuwagen, dazu Felgenkeramik ab {site.min_price("felgen")} € und Scheibenkeramik ab {site.min_price("scheiben")} €.</span>
            </span>
          </label>
          <label class="choice-card">
            <input type="radio" name="paket" value="care">
            <span class="choice-body">
              <span class="choice-head"><strong>ElbDetail Care</strong><span class="choice-price">auf Anfrage</span></span>
              <span class="choice-sub">Regelmäßige Pflege im festen Rhythmus, individuell abgestimmt. Für Privat, Firmen und Flotten.</span>
            </span>
          </label>
          <label class="choice-card">
            <input type="radio" name="paket" value="beratung">
            <span class="choice-body">
              <span class="choice-head"><strong>Unsicher oder Einzelleistung</strong><span class="choice-price">Beratung</span></span>
              <span class="choice-sub">Lederreparatur, Cabrioverdeck, nur Politur oder etwas anderes: Wir beraten Sie und machen ein Angebot.</span>
            </span>
          </label>'''
    cls = "".join(f'''<label class="choice-pill"><input type="radio" name="klasse" value="{c["key"]}" required{" checked" if i == 0 else ""}><span><strong>{ESC(c["short"])}</strong><small>{ESC(c["examples"])}</small></span></label>'''
                  for i, c in enumerate(pr["classes"]))
    zustand = "".join(f'<label class="check"><input type="checkbox" name="zustand" value="{v}"><span>{t}</span></label>' for v, t in [
        ("tierhaare", "Viele Tierhaare"), ("stark", "Stark verschmutzt"), ("geruch", "Geruch (Rauch, Hund, Feuchtigkeit)"),
        ("leder", "Ledersitze"), ("flecken", "Flecken auf Polstern"), ("kratzer", "Sichtbare Kratzer im Lack")])
    extras = "".join(f'<label class="check"><input type="checkbox" name="extras" value="{ESC(e)}"><span>{ESC(e)}</span></label>' for e in pr["extras"])

    owner = ESC((s.get("about") or {}).get("name") or "René")
    dep = (s.get("booking") or {}).get("depositPercent", 15)
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Termin anfragen", None)], "Online-Terminbuchung",
            "Termin buchen in <em>2 Minuten.</em>",
            "Paket wählen, Fahrzeug angeben, Tag und Uhrzeit aussuchen. Mit einer Anzahlung von " + str(dep) + " % per PayPal ist Ihr Termin gebucht, danach meldet sich " + owner + " telefonisch und sieht sich Ihr Fahrzeug vorab an.")}
  <section class="tight-top" aria-label="Terminanfrage">
    <div class="container booking">
      <form class="wizard js-form" id="bookingForm" data-form="termin" action="/api/anfrage" method="post" novalidate>
        <input type="hidden" name="typ" value="termin">
        <input type="hidden" name="quelle" value="">
        <ol class="wz-progress" aria-label="Fortschritt">
          <li data-step-ind="1">Paket</li><li data-step-ind="2">Fahrzeug</li><li data-step-ind="3">Extras</li><li data-step-ind="4">Termin</li><li data-step-ind="5">Kontakt</li>
        </ol>

        <fieldset class="wz-step" data-step="1">
          <legend><span class="wz-num">1</span>Welches Paket passt?</legend>
          <div class="choice-grid">{pk}</div>
        </fieldset>

        <fieldset class="wz-step" data-step="2">
          <legend><span class="wz-num">2</span>Ihr Fahrzeug</legend>
          <p class="wz-hint">Die Fahrzeugklasse bestimmt den Richtpreis.</p>
          <div class="choice-pills">{cls}</div>
          <div class="form-row"><label for="t-vehicle">Marke, Modell, Baujahr <span class="hint">(optional)</span></label><input type="text" id="t-vehicle" name="fahrzeug" maxlength="120" placeholder="z. B. VW Golf 7, 2018"></div>
          <div class="form-row"><span class="label">Zustand <span class="hint">(hilft uns bei der Planung)</span></span><div class="check-grid">{zustand}</div></div>
        </fieldset>

        <fieldset class="wz-step" data-step="3">
          <legend><span class="wz-num">3</span>Extras &amp; Service</legend>
          <p class="wz-hint">Zusätzliche Leistungen werden nach Aufwand berechnet und vorab mit Ihnen abgestimmt.</p>
          <div class="check-grid">{extras}</div>
          <div class="form-row"><span class="label">Hol- und Bringservice</span>
            <div class="choice-pills">
              <label class="choice-pill"><input type="radio" name="abholung" value="nein" checked><span><strong>Ich bringe das Auto</strong><small>{ESC(site.addr_line())}</small></span></label>
              <label class="choice-pill"><input type="radio" name="abholung" value="anfrage"><span><strong>Abholung anfragen</strong><small>nach Absprache in Celle</small></span></label>
            </div>
          </div>
        </fieldset>

        <fieldset class="wz-step" data-step="4">
          <legend><span class="wz-num">4</span>Termin wählen</legend>
          <p class="wz-hint">Wählen Sie Tag und Uhrzeit für die Abgabe Ihres Autos. Sie bekommen danach eine E-Mail mit einem Link: Mit der Anzahlung von {dep} % per PayPal ist Ihr Termin verbindlich gebucht. Die Anzahlung wird mit dem Endpreis verrechnet.</p>
          <p class="wz-hint">Bei Versiegelung und Keramik bleibt Ihr Auto 3 Tage bei uns. Bei allen anderen Leistungen ist es optimal, wenn es einen Tag bleiben kann.</p>
          <div class="form-row"><label for="t-date1">Tag*</label><input type="date" id="t-date1" name="datum" required aria-describedby="t-date1-msg"><span class="field-msg" id="t-date1-msg"></span><button class="next-free next-free--fill" type="button" data-next-free data-nf-fill hidden><span class="nf-dot" aria-hidden="true"></span>Nächster freier Tag: <strong data-nf-date></strong> · übernehmen</button></div>
          <div class="form-row"><span class="label" id="t-slots-l">Uhrzeit der Abgabe*</span>
            <div class="slot-grid" id="t-slots" role="radiogroup" aria-labelledby="t-slots-l" aria-describedby="t-slots-msg">{slots}</div>
            <span class="field-msg" id="t-slots-msg">Bitte zuerst einen Tag wählen.</span>
          </div>
          <div class="form-row"><label for="t-gutschein">Gutscheincode <span class="hint">(falls vorhanden)</span></label><input type="text" id="t-gutschein" name="gutscheincode" maxlength="20" placeholder="ELB-XXXX-XXXX" autocomplete="off"></div>
        </fieldset>

        <fieldset class="wz-step" data-step="5">
          <legend><span class="wz-num">5</span>Wie erreichen wir Sie?</legend>
          <div class="two-col">
            <div class="form-row"><label for="t-name">Name*</label><input type="text" id="t-name" name="name" autocomplete="name" required maxlength="120"></div>
            <div class="form-row"><label for="t-phone">Telefon / WhatsApp*</label><input type="tel" id="t-phone" name="telefon" autocomplete="tel" required maxlength="40"></div>
          </div>
          <div class="form-row"><label for="t-email">E-Mail* <span class="hint">(für den Bestätigungslink und die Erinnerungen)</span></label><input type="email" id="t-email" name="email" autocomplete="email" required maxlength="160"></div>
          <div class="form-row"><span class="label">Antwort bevorzugt per</span>
            <div class="choice-pills choice-pills--3">
              <label class="choice-pill"><input type="radio" name="kanal" value="whatsapp" checked><span><strong>WhatsApp</strong></span></label>
              <label class="choice-pill"><input type="radio" name="kanal" value="anruf"><span><strong>Anruf</strong></span></label>
              <label class="choice-pill"><input type="radio" name="kanal" value="email"><span><strong>E-Mail</strong></span></label>
            </div>
          </div>
          <div class="form-row"><label for="t-msg">Nachricht <span class="hint">(optional)</span></label><textarea id="t-msg" name="nachricht" rows="3" maxlength="2000" placeholder="Besonderheiten, Leasingrückgabe-Datum, Fragen …"></textarea></div>
          {core.honeypot("t-website")}
          <div class="consent-row consent-row--optional">
            <input type="checkbox" id="t-review" name="bewertung_ok" value="ja">
            <label for="t-review">Sie dürfen mich nach dem Termin einmalig fragen, ob ich eine Google-Bewertung schreiben möchte. <span class="hint">(optional, jederzeit widerrufbar)</span></label>
          </div>
          {core.consent_row("", "t-consent")}
        </fieldset>

        <div class="wz-nav">
          <button class="btn btn-line-light" type="button" data-wz-prev hidden>Zurück</button>
          <button class="btn btn-primary" type="button" data-wz-next hidden>Weiter {I["arrow"]}</button>
          <button class="btn btn-primary" type="submit" data-wz-submit>{I["cal"]}Termin buchen</button>
        </div>
        <button class="wz-wa" type="button" data-wa-from-form>{I["wa"]}Stattdessen alles per WhatsApp senden</button>
        {core.form_status("t-status")}
      </form>

      <aside class="wz-summary" aria-label="Zusammenfassung">
        <div class="summary-card">
          <h2>Ihre Anfrage</h2>
          <dl>
            <div><dt>Paket</dt><dd data-sum="paket">–</dd></div>
            <div><dt>Fahrzeug</dt><dd data-sum="klasse">–</dd></div>
            <div><dt>Extras</dt><dd data-sum="extras">keine</dd></div>
            <div><dt>Termin</dt><dd data-sum="datum">–</dd></div>
            <div><dt>Anzahlung ({dep} %)</dt><dd data-sum="anzahlung">–</dd></div>
          </dl>
          <div class="summary-price"><span>Richtpreis</span><strong data-sum="preis">–</strong></div>
          <p class="hint">Einstiegspreis für normalen Pflegezustand. Gemäß § 19 UStG ohne Umsatzsteuer. Den verbindlichen Preis bestätigen wir vor dem Termin.</p>
        </div>
        {_trust_list(site)}
        <p class="summary-alt">Lieber direkt sprechen? <a href="tel:{s["phone"]}">{ESC(s["phoneDisplay"])}</a> oder <a href="{site.wa()}" target="_blank" rel="noopener">WhatsApp</a></p>
      </aside>
    </div>
  </section>
</main>
'''
    write("termin.html", core.head(site, title, desc, path, ld=ld) + core.header(site) + body + core.footer(site))


# --------------------------------------------------------------------------- Gutscheine
def build_gutscheine(site, write):
    s = site.s
    v = s["vouchers"]
    path = "/gutscheine.html"
    title = "Gutschein Fahrzeugaufbereitung Celle | ElbDetail"
    desc = "Gutschein für Fahrzeugaufbereitung in Celle verschenken: Wunschbetrag oder Paket, persönliche Nachricht, als PDF per E-Mail. Ideal zu Weihnachten."
    year = int(s["standIso"][:4])
    faq = [
        {"q": "Wie lange ist ein Gutschein gültig?", "a": f"Gutscheine sind drei Jahre gültig, gerechnet ab dem Ende des Kaufjahres. Ein 2026 gekaufter Gutschein gilt also bis 31.12.{year + 3}."},
        {"q": "Wie löse ich einen Gutschein ein?", "a": "Bei der Online-Terminanfrage den Gutscheincode eingeben oder ihn bei der WhatsApp-Anfrage nennen. Wir verrechnen den Wert mit dem Auftrag."},
        {"q": "Was passiert bei einem größeren Fahrzeug?", "a": "Paketgutscheine gelten für einen Kleinwagen. Bei größeren Fahrzeugen wird nur die Differenz zum Richtpreis der jeweiligen Fahrzeugklasse fällig."},
        {"q": "Wie bezahle ich den Gutschein?", "a": "Nach Ihrer Bestellung erhalten Sie die Zahlungsdaten per E-Mail. Sie zahlen per Überweisung, per PayPal oder bei Abholung bar oder mit Karte. Nach Zahlungseingang erhalten Sie den Gutschein als Link zum Ausdrucken oder holen ihn gedruckt ab."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Gutscheine", path)]), seo.faq(faq),
          {"@context": "https://schema.org", "@type": "Product", "name": "ElbDetail Gutschein Fahrzeugaufbereitung", "brand": {"@type": "Brand", "name": s["name"]},
           "description": "Wert- oder Paketgutschein für eine Fahrzeugaufbereitung bei ElbDetail in Celle.", "image": site.url + "/og-image.png",
           "offers": {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": str(v["minAmount"]), "highPrice": str(v["maxAmount"]),
                      "availability": "https://schema.org/InStock", "seller": {"@id": site.url + "/#business"}}}]
    amounts = "".join(f'<label class="choice-pill"><input type="radio" name="betrag" value="{a}"{" checked" if i == 1 else ""}><span><strong>{a} €</strong></span></label>' for i, a in enumerate(v["amounts"]))
    pkgs = "".join(f'<option value="{p["key"]}">{ESC(p["name"])} (Kompakt, Wert {p["prices"][site.pricing["classes"][0]["key"]]} €)</option>' for p in site.pricing["packages"])
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Gutscheine", None)], "Geschenkidee",
            "Verschenken Sie ein <em>Auto wie neu.</em>",
            "Wunschbetrag oder komplettes Paket, mit persönlicher Nachricht. Als PDF per E-Mail zum Ausdrucken oder gedruckt zum Abholen in Celle.")}
  <section class="tight-top" aria-label="Gutschein gestalten">
    <div class="container voucher-layout">
      <form class="voucher-form js-form" id="voucherForm" data-form="gutschein" action="/api/anfrage" method="post" novalidate>
        <input type="hidden" name="typ" value="gutschein">
        <fieldset class="form-block">
          <legend>1. Art des Gutscheins</legend>
          <div class="choice-pills">
            <label class="choice-pill"><input type="radio" name="art" value="wert" checked><span><strong>Wertgutschein</strong><small>Betrag frei wählbar</small></span></label>
            <label class="choice-pill"><input type="radio" name="art" value="paket"><span><strong>Paketgutschein</strong><small>Leistung verschenken</small></span></label>
          </div>
          <div class="vf-wert">
            <span class="label">Betrag</span>
            <div class="choice-pills choice-pills--4">{amounts}</div>
            <div class="form-row"><label for="g-custom">Oder Wunschbetrag in € <span class="hint">({v["minAmount"]} bis {v["maxAmount"]} €)</span></label><input type="number" id="g-custom" name="wunschbetrag" min="{v["minAmount"]}" max="{v["maxAmount"]}" step="5" inputmode="numeric"></div>
          </div>
          <div class="vf-paket" hidden>
            <div class="form-row"><label for="g-paket">Paket</label><select id="g-paket" name="paket">{pkgs}</select></div>
          </div>
        </fieldset>
        <fieldset class="form-block">
          <legend>2. Persönliche Note</legend>
          <div class="two-col">
            <div class="form-row"><label for="g-for">Für <span class="hint">(Name auf dem Gutschein)</span></label><input type="text" id="g-for" name="fuer" maxlength="60" placeholder="z. B. Papa"></div>
            <div class="form-row"><label for="g-from">Von</label><input type="text" id="g-from" name="von" maxlength="60" placeholder="z. B. Lisa &amp; Tom"></div>
          </div>
          <div class="form-row"><label for="g-msg">Nachricht <span class="hint">(max. 160 Zeichen)</span></label><textarea id="g-msg" name="widmung" rows="2" maxlength="160" placeholder="Frohe Weihnachten! Damit Ihr Auto endlich wieder glänzt."></textarea></div>
        </fieldset>
        <fieldset class="form-block">
          <legend>3. Zustellung &amp; Kontakt</legend>
          <div class="choice-pills">
            <label class="choice-pill"><input type="radio" name="zustellung" value="pdf" checked><span><strong>PDF per E-Mail</strong><small>zum Selbstausdrucken</small></span></label>
            <label class="choice-pill"><input type="radio" name="zustellung" value="abholung"><span><strong>Gedruckt abholen</strong><small>in Celle</small></span></label>
          </div>
          <div class="two-col">
            <div class="form-row"><label for="g-name">Ihr Name*</label><input type="text" id="g-name" name="name" autocomplete="name" required maxlength="120"></div>
            <div class="form-row"><label for="g-email">E-Mail*</label><input type="email" id="g-email" name="email" autocomplete="email" required maxlength="160"></div>
          </div>
          <div class="form-row"><label for="g-phone">Telefon <span class="hint">(optional)</span></label><input type="tel" id="g-phone" name="telefon" autocomplete="tel" maxlength="40"></div>
          {core.honeypot("g-website")}
          {core.consent_row("", "g-consent")}
        </fieldset>
        <button class="btn btn-primary btn-lg btn-block" type="submit">{I["gift"]}Gutschein verbindlich bestellen</button>
        <p class="hint">Sie erhalten die Zahlungsdaten per E-Mail (Überweisung, PayPal oder bei Abholung bar bzw. mit Karte). Nach Zahlungseingang erhalten Sie den Gutschein.</p>
        {core.form_status("g-status")}
      </form>

      <div class="voucher-preview-wrap">
        <p class="eyebrow">Vorschau</p>
        <div class="voucher-card" id="voucherPreview" aria-live="polite">
          <div class="vc-top"><img src="logo.svg" alt="" width="173" height="60"><span>Gutschein</span></div>
          <div class="vc-value" data-vc="value">100 €</div>
          <div class="vc-desc" data-vc="desc">für eine Fahrzeugaufbereitung nach Wahl</div>
          <div class="vc-names"><span>Für <strong data-vc="fuer">…</strong></span><span>Von <strong data-vc="von">…</strong></span></div>
          <p class="vc-msg" data-vc="msg"></p>
          <div class="vc-foot"><span>Code: ELB-••••-••••</span><span>Gültig bis 31.12.{year + 3}</span></div>
        </div>
        {_trust_list(site)}
      </div>
    </div>
  </section>
  <section class="soft" aria-labelledby="gfaq-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Gut zu wissen</p><h2 id="gfaq-h" class="display">Fragen zum Gutschein.</h2></div>
      <div class="faq-list">{core.faq_html(faq)}</div>
    </div>
  </section>
</main>
'''
    write("gutscheine.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="gutscheine.html") + body + core.footer(site))


# --------------------------------------------------------------------------- Firmenkunden
def build_firmen(site, write):
    s = site.s
    path = "/firmenkunden.html"
    title = "Fahrzeugaufbereitung für Firmen & Flotten | ElbDetail Celle"
    desc = "Aufbereitung für Firmenwagen, Flotten, Autohäuser und Leasingrückläufer in Celle: planbare Intervalle, ein Ansprechpartner, Abrechnung nach Absprache."
    faq = [
        {"q": "Ab wie vielen Fahrzeugen lohnt sich eine Rahmenvereinbarung?", "a": "Schon ab wenigen Fahrzeugen mit regelmäßigem Pflegebedarf. Wir besprechen Umfang und Intervalle individuell und machen ein Angebot, das zu Ihrem Fuhrpark passt."},
        {"q": "Bereiten Sie auch Fahrzeuge für Autohäuser und Händler auf?", "a": "Ja. Aufbereitung vor Verkauf, Übergabe oder Fotoshooting gehört zu unseren Kernleistungen. Abläufe und Fristen stimmen wir direkt mit Ihnen ab."},
        {"q": "Wie wird abgerechnet?", "a": "Nach Absprache, zum Beispiel pro Fahrzeug oder gesammelt pro Zeitraum. Die Details halten wir im Angebot fest."},
        {"q": "Gibt es eine Preisliste für Gewerbekunden?", "a": "Nein, bewusst nicht. Die Konditionen richten sich nach Fahrzeuganzahl, Zustand, Leistungsumfang und Auftragsvolumen. Für Gewerbekunden gibt es Sonderkonditionen, die wir individuell vereinbaren."},
        {"q": "Holen Sie Fahrzeuge auch ab?", "a": "Ja, ein Abhol- und Bringservice ist nach Vereinbarung möglich. Für regelmäßige Pflege bietet sich ElbDetail Care an, mit festen Intervallen und einem Ansprechpartner."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Firmenkunden", path)]), seo.faq(faq),
          {"@context": "https://schema.org", "@type": "Service", "name": "Fahrzeugaufbereitung für Firmen und Flotten", "serviceType": "Flottenpflege",
           "provider": {"@id": site.url + "/#business"}, "areaServed": {"@type": "City", "name": s["address"]["city"]}, "audience": {"@type": "BusinessAudience"}}]
    services = "".join(f'<label class="check"><input type="checkbox" name="leistungen" value="{ESC(x)}"><span>{ESC(x)}</span></label>' for x in
                       ["Regelmäßige Pflege (ElbDetail Care)", "Regelmäßige Außenwäsche", "Innenreinigung", "Komplettaufbereitung", "Aufbereitung vor Verkauf/Rückgabe", "Lackpolitur & Versiegelung", "Keramikversiegelung", "Geruchsentfernung", "Abhol- und Bringservice"])
    refs = ref_wall(site)
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Firmenkunden", None)], "Für Unternehmen",
            "Gepflegte Firmenwagen. <em>Planbar und ohne Aufwand.</em>",
            "Individuelle Aufbereitungslösungen und Sonderkonditionen für Autohäuser, Fahrschulen, Pflegedienste, Handwerksbetriebe, Dienstwagen und Fuhrparks in Celle und Umgebung. Einzeln oder als langfristige Vereinbarung.",
            f'<div class="hero-actions"><a class="btn btn-primary btn-lg" href="#firmenanfrage">{I["brief"]}Angebot anfordern</a><a class="btn btn-line" href="tel:{s["phone"]}">{I["phone"]}{ESC(s["phoneDisplay"])}</a></div>')}
  <section class="tight" aria-labelledby="b2b-groups-h">
    <div class="container">
      <h2 id="b2b-groups-h" class="eyebrow">Wir arbeiten für</h2>
      <ul class="chips b2b-groups">
        <li>Autohäuser &amp; Fahrzeughändler</li><li>Fahrschulen</li><li>Pflegedienste</li><li>Handwerksbetriebe</li>
        <li>Unternehmen mit Dienstwagen</li><li>Leasing- &amp; Fuhrparkunternehmen</li>
      </ul>
    </div>
  </section>{refs}
  <section aria-labelledby="b2b-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Warum ElbDetail</p><h2 id="b2b-h" class="display">Was Firmenkunden von uns bekommen.</h2></div>
      <div class="usecase-grid">
        <div class="usecase">{I["cal"]}<h3>Planbare Intervalle</h3><p>Feste Pflegetermine im passenden Rhythmus, abgestimmt auf Ihre Einsatzzeiten. So stehen Fahrzeuge nicht unnötig still.</p></div>
        <div class="usecase">{I["phone"]}<h3>Ein Ansprechpartner</h3><p>Direkter Draht per Telefon oder WhatsApp, kurze Wege und schnelle Rückmeldung auch bei kurzfristigem Bedarf.</p></div>
        <div class="usecase">{I["euro"]}<h3>Klare Konditionen</h3><p>Leistungsumfang und Preise pro Fahrzeugklasse werden im Angebot festgehalten. Abrechnung nach Absprache.</p></div>
        <div class="usecase">{I["key"]}<h3>Leasingrückläufer</h3><p>Aufbereitung vor der Rückgabe reduziert Beanstandungen wegen Verschmutzung, Gerüchen und oberflächlicher Gebrauchsspuren.</p></div>
        <div class="usecase">{I["tag"]}<h3>Autohäuser &amp; Händler</h3><p>Verkaufsfertige Aufbereitung für Inserat, Übergabe oder Showroom, in Handarbeit und mit Profi-Produkten.</p></div>
        <div class="usecase">{I["spark"]}<h3>Repräsentative Fahrzeuge</h3><p>Firmenwagen sind Visitenkarte. Lackpflege und Keramikversiegelung halten sie dauerhaft in gutem Zustand.</p></div>
      </div>
    </div>
  </section>
  <section id="firmenanfrage" class="soft" aria-labelledby="ff-h">
    <div class="container two-up">
      <div>
        <div class="section-head"><p class="eyebrow">Angebot anfordern</p><h2 id="ff-h" class="display">Erzählen Sie uns von Ihrem Fuhrpark.</h2>
          <p>Ein paar Eckdaten genügen. Wir melden uns mit einem Vorschlag für Umfang, Intervalle und Konditionen.</p></div>
        <div class="faq-list">{core.faq_html(faq, first_open=False)}</div>
      </div>
      <form class="contact-form card-form js-form" id="firmForm" data-form="firma" action="/api/anfrage" method="post" novalidate>
        <input type="hidden" name="typ" value="firma">
        <div class="two-col">
          <div class="form-row"><label for="f-firma">Unternehmen*</label><input type="text" id="f-firma" name="firma" autocomplete="organization" required maxlength="160"></div>
          <div class="form-row"><label for="f-name">Ansprechpartner*</label><input type="text" id="f-name" name="name" autocomplete="name" required maxlength="120"></div>
        </div>
        <div class="two-col">
          <div class="form-row"><label for="f-email">E-Mail*</label><input type="email" id="f-email" name="email" autocomplete="email" required maxlength="160"></div>
          <div class="form-row"><label for="f-phone">Telefon</label><input type="tel" id="f-phone" name="telefon" autocomplete="tel" maxlength="40"></div>
        </div>
        <div class="two-col">
          <div class="form-row"><label for="f-count">Anzahl Fahrzeuge</label><select id="f-count" name="anzahl"><option>1–3</option><option>4–10</option><option>11–25</option><option>mehr als 25</option></select></div>
          <div class="form-row"><label for="f-int">Gewünschtes Intervall</label><select id="f-int" name="intervall"><option>einmalig / nach Bedarf</option><option>monatlich</option><option>alle 2–3 Monate</option><option>halbjährlich</option></select></div>
        </div>
        <div class="form-row"><span class="label">Leistungen</span><div class="check-grid">{services}</div></div>
        <div class="form-row"><label for="f-msg">Nachricht</label><textarea id="f-msg" name="nachricht" rows="3" maxlength="2000" placeholder="Fahrzeugtypen, Standort, Besonderheiten …"></textarea></div>
        {core.honeypot("f-website")}
        {core.consent_row("", "f-consent")}
        <button class="btn btn-primary btn-block" type="submit">{I["brief"]}Angebot anfordern</button>
        {core.form_status("f-status")}
      </form>
    </div>
  </section>
{core.cta_band(site, "", "Lieber direkt sprechen?", "Rufen Sie an oder schreiben Sie per WhatsApp. Wir klären Umfang und Ablauf in wenigen Minuten.")}
</main>
'''
    write("firmenkunden.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="firmenkunden.html") + body + core.footer(site))


# --------------------------------------------------------------------------- Winter-Aktion
def build_winter(site, write):
    s = site.s
    prefix = "../"
    path = "/aktion/winterschutz.html"
    title = "Auto winterfest machen in Celle: Lackschutz | ElbDetail"
    ws = s.get("winterSpecial") or {}
    ws_on = bool(ws.get("price")) and (not ws.get("validUntil") or ws["validUntil"] >= datetime.date.today().isoformat())
    ws_until = ".".join(reversed(ws["validUntil"].split("-"))) if ws_on and ws.get("validUntil") else ""
    desc = (f"Lack vor Streusalz schützen: Glanzpolitur und Versiegelung in Celle vor dem ersten Frost. "
            + (f"Winter-Special ab {ws['price']} €. Termin sichern." if ws_on else f"Signature mit Glanzpolitur ab {site.min_price('signature')} €. Termin sichern."))
    prem = site.pkg("signature")
    exc = site.pkg("excellence")
    faq = [
        {"q": "Wann sollte ich mein Auto versiegeln lassen?", "a": "Am besten vor dem ersten Frost und dem ersten Streusalz, in Celle also meist im Oktober oder November. Die Versiegelung braucht trockene Bedingungen und Zeit zum Aushärten."},
        {"q": "Reicht eine Versiegelung ohne Politur?", "a": "Bei gutem Lack ja. Sind Kratzer oder Hologramme sichtbar, empfehlen wir vorher eine Politur, weil die Versiegelung den Zustand darunter konserviert."},
        {"q": "Wie wasche ich das Auto im Winter richtig?", "a": "Regelmäßig Salz abspülen, möglichst per Handwäsche mit pH-neutralem Shampoo. Aggressive Reiniger aus der Waschstraße verkürzen die Haltbarkeit der Versiegelung."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Winter-Lackschutz", path)]), seo.faq(faq)]
    wart = [a for a in site.articles if "winter" in a.get("category", "").lower()]
    art_link = ("<p>Mehr Tipps im <a class=\"text-link\" href=\"" + prefix + "ratgeber/winter.html\">Winter-Ratgeber</a>: "
                + ", ".join(f'<a class="text-link" href="{prefix}ratgeber/{a["slug"]}.html">{ESC(a["title"])}</a>' for a in wart) + ".</p>") if wart else ""
    body = f'''
<main id="main">
  <section class="page-hero page-hero--winter" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Winter-Lackschutz", None)])}
      <p class="eyebrow">Saison-Empfehlung Herbst &amp; Winter</p>
      <h1 id="page-h">Lack winterfest machen. <em>Bevor das Streusalz kommt.</em></h1>
      <p class="lead">Streusalz, Matsch und Frost setzen Lack, Felgen und Dichtungen stärker zu als jede andere Jahreszeit. Eine Versiegelung vor dem Winter sorgt dafür, dass Schmutz schlechter haftet und das Auto im Frühjahr nicht erst gerettet werden muss.</p>
      <div class="keyfacts">{f'<div class="keyfact"><strong>ab {ws["price"]} €</strong><span>{ESC(ws.get("label", "Winter-Special"))}{" bis " + ws_until if ws_until else ""}</span></div>' if ws_on else f'<div class="keyfact"><strong>ab {site.min_price("signature")} €</strong><span>{ESC(prem["name"])} mit Glanzpolitur</span></div>'}<div class="keyfact"><strong>3 Tage</strong><span>Standzeit mit Versiegelung</span></div><div class="keyfact"><strong>+ Versiegelung</strong><span>separat zubuchbar</span></div></div>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" href="{prefix}termin.html?paket=signature&amp;quelle=winter">{I["cal"]}Wintertermin anfragen</a>
        <a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich möchte mein Auto vor dem Winter versiegeln lassen. Fahrzeug: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
      </div>
    </div>
  </section>
  <section aria-labelledby="w1-h">
    <div class="container two-up">
      <div class="prose">
        <h2 id="w1-h">Warum der Winter dem Lack so zusetzt</h2>
        <p>Streusalz löst sich im Spritzwasser und setzt sich als feiner Film auf Lack, Felgen und Unterboden. Zusammen mit Feuchtigkeit greift es ungeschützte Stellen an, besonders Steinschläge, Kanten und Felgen. Hinzu kommen Matsch, Rollsplitt und häufige Temperaturwechsel.</p>
        <p>Eine Versiegelung bildet eine glatte, wasserabweisende Schutzschicht auf dem Klarlack. Salzwasser perlt schneller ab, Schmutz lässt sich leichter abwaschen, und der Lack muss im Frühjahr deutlich weniger aushalten.</p>
        <h2>Unser Winter-Lackschutz</h2>
        <ul class="includes">
          <li>{I["check"]}Gründliche Handwäsche und chemische Dekontamination</li>
          <li>{I["check"]}Lackreinigungsknete gegen eingebrannte Partikel</li>
          <li>{I["check"]}Glanzpolitur (Signature) oder mehrstufige Lackkorrektur (Excellence)</li>
          <li>{I["check"]}Komplette Innenaufbereitung, Leder mit Colourlock gepflegt</li>
          <li>{I["check"]}Lackversiegelung oder C² CarCeramic, separat zubuchbar</li>
          <li>{I["check"]}Felgenkeramik ab {site.min_price("felgen")} € und Scheibenkeramik ab {site.min_price("scheiben")} €</li>
          <li>{I["check"]}Pflege von Gummidichtungen gegen Festfrieren</li>
          <li>{I["check"]}Pflegetipps für die Wäsche im Winter</li>
        </ul>
        <h2>Welche Variante passt?</h2>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Tabelle, seitlich scrollbar"><table class="md-table"><thead><tr><th scope="col">Zustand des Lacks</th><th scope="col">Empfehlung</th><th scope="col">Richtpreis</th></tr></thead><tbody>
          <tr><th scope="row">Neuwagen oder sehr guter Lack</th><td>Versiegelung ohne Politur</td><td>auf Anfrage</td></tr>
          {f'<tr class="is-special"><th scope="row">{ESC(ws.get("label", "Winter-Special"))}{" bis " + ws_until if ws_until else ""}</th><td>{ESC(ws.get("text", ""))}</td><td>ab {ws["price"]} €</td></tr>' if ws_on else ""}
          <tr><th scope="row">Matter Glanz, leichte Gebrauchsspuren</th><td>{ESC(prem["name"])}: Glanzpolitur + Versiegelung</td><td>ab {site.min_price("signature")} € + Versiegelung</td></tr>
          <tr><th scope="row">Viele Waschspuren, Hologramme</th><td>{ESC(exc["name"])}: mehrstufige Lackkorrektur + Versiegelung</td><td>ab {site.min_price("excellence")} € + Versiegelung</td></tr>
          <tr><th scope="row">Langzeitschutz über viele Winter</th><td>C² CarCeramic Keramikversiegelung</td><td>ab {site.min_price("keramik")} €</td></tr>
        </tbody></table></div>
        <p class="hint">Ab-Preise für einen Kleinwagen, jeweils mit kompletter Innen- und Außenaufbereitung. {ESC(prem["name"])} für Kompaktwagen ab {prem["prices"].get("kompakt", "")} €, Limousine/Kombi/SUV ab {prem["prices"].get("mittel", "")} €, großer SUV/Van ab {prem["prices"].get("suv", "")} €. Der Korrekturgrad hängt vom Lackzustand ab.</p>
        {art_link}
        <h2>Häufige Fragen</h2>
        <div class="faq-list">{core.faq_html(faq, prefix)}</div>
      </div>
      <aside class="sticky-aside">
        <div class="aside-card dark">
          <h3>Wintertermin sichern</h3>
          <p>Die Wochen vor dem ersten Frost sind gefragt. Fragen Sie frühzeitig an, wir bestätigen den Termin persönlich.</p>
          <a class="btn btn-primary" href="{prefix}termin.html?paket=signature&amp;quelle=winter">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa" href="{site.wa("Hallo ElbDetail, ich möchte mein Auto vor dem Winter versiegeln lassen.")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        </div>
        <div class="aside-card"><h3>Auch interessant</h3><ul>
          <li><a href="{prefix}leistungen/lackversiegelung-celle.html">Lackversiegelung Celle</a></li>
          <li><a href="{prefix}leistungen/lackpolitur-celle.html">Lackpolitur Celle</a></li>
          <li><a href="{prefix}gutscheine.html">Gutscheine zu Weihnachten</a></li></ul></div>
      </aside>
    </div>
  </section>
{core.cta_band(site, prefix, "Jetzt vor dem ersten Frost versiegeln.", "Nennen Sie uns kurz Fahrzeug und Wunschtermin. Sie erhalten ein verbindliches Angebot, bevor irgendetwas passiert.")}
</main>
'''
    write("aktion/winterschutz.html", core.head(site, title, desc, path, prefix=prefix, ld=ld) + core.header(site, prefix) + body + core.footer(site, prefix))


# --------------------------------------------------------------------------- Entwurf Pflege-Abo
def build_care(site, write):
    """ElbDetail Care: individuelles Pflegekonzept, nur auf Anfrage, ohne Paketpreise."""
    s = site.s
    path = "/elbdetail-care.html"
    title = "ElbDetail Care: Regelmäßige Fahrzeugpflege Celle | ElbDetail"
    desc = ("ElbDetail Care: regelmäßige Fahrzeugpflege in Celle für Privat, Firmen und Flotten. "
            "Leistungen und Intervalle nach Maß, nur auf Anfrage.")
    faq = [
        {"q": "Was kostet ElbDetail Care?", "a": "Es gibt keine festen Paketpreise. Die Konditionen richten sich nach Fahrzeug, gewünschtem Leistungsumfang und Häufigkeit der Pflege. Nach einem kurzen Gespräch erhalten Sie ein individuelles Angebot."},
        {"q": "Für wen eignet sich ElbDetail Care?", "a": "Für alle, die ihr Fahrzeug dauerhaft gepflegt halten möchten: Privatkunden, Unternehmen mit Dienstwagen und Fuhrparks. Besonders sinnvoll ist Care auch für keramisch versiegelte Fahrzeuge, deren Beschichtung regelmäßig gewartet werden sollte."},
        {"q": "Wie oft kommt mein Fahrzeug zur Pflege?", "a": "Das legen wir gemeinsam fest, zum Beispiel monatlich, alle zwei bis drei Monate oder saisonal im Frühjahr und vor dem Winter. Die Intervalle lassen sich jederzeit anpassen."},
        {"q": "Kann das Fahrzeug abgeholt werden?", "a": "Ja, ein Abhol- und Bringservice ist nach Vereinbarung möglich. Die Details klären wir im Gespräch."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("ElbDetail Care", path)]), seo.faq(faq),
          {"@context": "https://schema.org", "@type": "Service", "name": "ElbDetail Care", "serviceType": "Regelmäßige Fahrzeugpflege",
           "description": desc, "provider": {"@id": site.url + "/#business"}, "areaServed": {"@type": "City", "name": s["address"]["city"]}}]
    wa = site.wa("Hallo ElbDetail, ich interessiere mich für ElbDetail Care. Fahrzeug(e): … Gewünschter Rhythmus: …")
    items = [("cal", "Regelmäßige Innen- und Außenpflege", "Feste Termine im passenden Rhythmus, damit Ihr Fahrzeug immer gepflegt ist."),
             ("snow", "Saisonale Pflege", "Lack- und Felgenschutz vor dem Winter, gründliche Frühjahrspflege nach der Streusalz-Saison."),
             ("shield", "Wartung von Keramikversiegelungen", "Pflege und Auffrischung bereits keramisch versiegelter Fahrzeuge, damit der Schutz lange hält."),
             ("car", "Abhol- und Bringservice", "Nach Vereinbarung holen wir das Fahrzeug ab und bringen es gepflegt zurück.")]
    cards = "".join(f'<div class="usecase">{I[i]}<h3>{h}</h3><p>{p}</p></div>' for i, h, p in items)
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("ElbDetail Care", None)], "ElbDetail Care",
            "Dauerhaft gepflegt. <em>Ganz ohne daran zu denken.</em>",
            "Ein individuelles Pflegekonzept für Privatkunden, Unternehmen und Fahrzeugflotten. Leistungen und Intervalle stimmen wir genau auf Sie und Ihr Fahrzeug ab.",
            f'<div class="hero-actions"><a class="btn btn-primary btn-lg" href="termin.html?paket=care">{I["cal"]}Care anfragen</a><a class="btn btn-wa btn-lg" href="{wa}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a></div>')}
  <section aria-labelledby="care-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Was enthalten sein kann</p><h2 id="care-h" class="display">Pflege nach Maß, <em>nicht von der Stange.</em></h2>
        <p>Sie wählen, was Ihr Fahrzeug braucht. Wir kümmern uns darum, dass es regelmäßig passiert.</p></div>
      <div class="usecase-grid">{cards}</div>
    </div>
  </section>
  <section class="soft" aria-labelledby="care2-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">So funktioniert es</p><h2 id="care2-h" class="display">In vier Schritten <em>zu Ihrem Pflegeplan.</em></h2></div>
      <div class="process-rail">
        <div class="process-cell"><span class="process-index">SCHRITT 01</span><h3>Gespräch</h3><p>Wir sprechen über Ihr Fahrzeug, die Nutzung und Ihre Wünsche.</p></div>
        <div class="process-cell"><span class="process-index">SCHRITT 02</span><h3>Individuelles Angebot</h3><p>Sie erhalten einen Pflegeplan mit Leistungen, Intervallen und Konditionen.</p></div>
        <div class="process-cell"><span class="process-index">SCHRITT 03</span><h3>Feste Termine</h3><p>Die Pflegetermine planen wir im Voraus, auf Wunsch mit Abholung.</p></div>
        <div class="process-cell"><span class="process-index">SCHRITT 04</span><h3>Laufende Betreuung</h3><p>Ein fester Ansprechpartner, Anpassungen jederzeit nach Absprache.</p></div>
      </div>
      <p class="hint">ElbDetail Care gibt es nur auf Anfrage. Feste Paketpreise gibt es nicht, weil sich die Konditionen nach Fahrzeug, Umfang und Häufigkeit richten. Für Unternehmen und Fuhrparks siehe auch <a class="text-link" href="firmenkunden.html">Firmenkunden</a>.</p>
    </div>
  </section>
  <section aria-labelledby="care3-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Häufige Fragen</p><h2 id="care3-h" class="display">Gut zu wissen <em>über Care.</em></h2></div>
      <div class="faq-list">{core.faq_html(faq)}</div>
    </div>
  </section>
{core.cta_band(site, "", "Ihr Pflegeplan beginnt mit einem Gespräch.", "Schreiben Sie uns kurz, um welches Fahrzeug es geht und wie oft Sie sich Pflege wünschen. Wir melden uns mit einem individuellen Vorschlag.")}
</main>
'''
    write("elbdetail-care.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="elbdetail-care.html") + body + core.footer(site))



def build_angebote(site, write):
    s = site.s
    path = "/angebote.html"
    title = "Aktuelle Angebote: Fahrzeugaufbereitung Celle | ElbDetail"
    desc = ("Aktuelle Angebote von ElbDetail in Celle: Winter-Lackschutz, Gutscheine, Keramikversiegelung und Sonderkonditionen für Firmen. "
            "Jetzt Termin anfragen.")
    offers = site.offers
    items = []
    for o in offers:
        off = {"@type": "Offer", "name": o["title"], "description": o.get("text", ""), "url": site.url + "/" + (o.get("ctaHref") or "angebote.html").lstrip("/"),
               "seller": {"@id": site.url + "/#business"}, "availability": "https://schema.org/InStock"}
        if o.get("validUntil"):
            off["validThrough"] = o["validUntil"]
        items.append(off)
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Angebote", path)])]
    if items:
        ld.append({"@context": "https://schema.org", "@type": "OfferCatalog", "name": "Aktuelle Angebote von " + s["name"], "itemListElement": items})
    cards = "".join(offer_card(site, o) for o in offers) or \
        '<p class="empty-offers">Gerade läuft keine Aktion. Fragen Sie uns trotzdem gern: Für Stammkunden und Firmen gibt es immer passende Konditionen.</p>'
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Angebote", None)], "Aktuell",
            "Aktuelle Angebote. <em>Für Ihr Auto.</em>",
            "Saisonale Aktionen, Geschenkideen und Sonderkonditionen. Alle Preise sind Endpreise, den verbindlichen Preis bestätigen wir vor dem Termin.",
            f'<div class="hero-actions"><a class="btn btn-primary btn-lg" href="termin.html">{I["cal"]}Termin anfragen</a><a class="btn btn-wa btn-lg" href="{site.wa("Hallo ElbDetail, ich interessiere mich für Ihre aktuellen Angebote. Fahrzeug: …")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a></div>')}
  <section aria-labelledby="offers-h">
    <div class="container">
      <h2 id="offers-h" class="visually-hidden">Alle aktuellen Angebote</h2>
      <div class="offer-grid stagger">{cards}
      </div>
      <p class="price-note">Aktionen gelten, solange freie Termine verfügbar sind. Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.</p>
    </div>
  </section>
</main>
'''
    write("angebote.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="angebote.html") + body + core.footer(site))
