# -*- coding: utf-8 -*-
"""Conversion-Seiten: Terminbuchung, Gutscheine, Firmenkunden, Winter-Aktion, Entwurf Pflege-Abo."""
import datetime

import core
import seo
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
          <li>{I["hand"]}100 % Handarbeit, Koch-Chemie geschult</li>
          <li>{I["shield"]}Daten bleiben auf unserem Server in Deutschland</li>
        </ul>'''


# --------------------------------------------------------------------------- Termin
def build_termin(site, write):
    pr = site.pricing
    s = site.s
    path = "/termin.html"
    title = "Termin anfragen: Fahrzeugaufbereitung Celle | ElbDetail"
    desc = "Fahrzeugaufbereitung in Celle online anfragen: Paket wählen, Fahrzeug angeben, Wunschtermin aussuchen. Du bekommst vorab ein verbindliches Angebot."
    ld = [seo.webpage(site, path, title, {"potentialAction": {"@type": "ReserveAction", "target": site.url + path}}),
          seo.crumbs(site, [("Startseite", "/"), ("Termin anfragen", path)])]
    cls0 = pr["classes"][0]["key"]

    pk = ""
    for p in pr["packages"]:
        inc = "".join(f"<li>{ESC(f['text'])}</li>" for f in p["features"] if f["included"])[:]
        pk += f'''<label class="choice-card{" is-featured" if p.get("featured") else ""}">
            <input type="radio" name="paket" value="{p["key"]}" required{" checked" if p.get("featured") else ""}>
            <span class="choice-body">
              <span class="choice-head"><strong>{ESC(p["name"])}</strong><span class="choice-price" data-price-for="{p["key"]}">ab {p["prices"][cls0]} €</span></span>
              <span class="choice-sub">{ESC(p["for"])} · {ESC(p["duration"])}</span>
              <ul class="choice-feats">{inc}</ul>
            </span>
          </label>'''
    pk += '''<label class="choice-card">
            <input type="radio" name="paket" value="beratung">
            <span class="choice-body">
              <span class="choice-head"><strong>Unsicher oder Einzelleistung</strong><span class="choice-price">Beratung</span></span>
              <span class="choice-sub">Leasingrückgabe, nur Politur, nur Versiegelung oder etwas anderes: Wir beraten dich und machen ein Angebot.</span>
            </span>
          </label>'''
    cls = "".join(f'''<label class="choice-pill"><input type="radio" name="klasse" value="{c["key"]}" required{" checked" if i == 0 else ""}><span><strong>{ESC(c["short"])}</strong><small>{ESC(c["examples"])}</small></span></label>'''
                  for i, c in enumerate(pr["classes"]))
    zustand = "".join(f'<label class="check"><input type="checkbox" name="zustand" value="{v}"><span>{t}</span></label>' for v, t in [
        ("tierhaare", "Viele Tierhaare"), ("stark", "Stark verschmutzt"), ("geruch", "Geruch (Rauch, Hund, Feuchtigkeit)"),
        ("leder", "Ledersitze"), ("flecken", "Flecken auf Polstern"), ("kratzer", "Sichtbare Kratzer im Lack")])
    extras = "".join(f'<label class="check"><input type="checkbox" name="extras" value="{ESC(e)}"><span>{ESC(e)}</span></label>' for e in pr["extras"])

    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Termin anfragen", None)], "Online-Terminanfrage",
            "Termin anfragen in <em>2 Minuten.</em>",
            "Paket wählen, Fahrzeug angeben, Wunschtermin aussuchen. Du bekommst ein verbindliches Angebot und eine Terminbestätigung, bevor wir loslegen.")}
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
          <legend><span class="wz-num">2</span>Dein Fahrzeug</legend>
          <p class="wz-hint">Die Fahrzeugklasse bestimmt den Richtpreis.</p>
          <div class="choice-pills">{cls}</div>
          <div class="form-row"><label for="t-vehicle">Marke, Modell, Baujahr <span class="hint">(optional)</span></label><input type="text" id="t-vehicle" name="fahrzeug" maxlength="120" placeholder="z. B. VW Golf 7, 2018"></div>
          <div class="form-row"><span class="label">Zustand <span class="hint">(hilft uns bei der Planung)</span></span><div class="check-grid">{zustand}</div></div>
        </fieldset>

        <fieldset class="wz-step" data-step="3">
          <legend><span class="wz-num">3</span>Extras &amp; Service</legend>
          <p class="wz-hint">Zusätzliche Leistungen werden nach Aufwand berechnet und vorab mit dir abgestimmt.</p>
          <div class="check-grid">{extras}</div>
          <div class="form-row"><span class="label">Hol- und Bringservice</span>
            <div class="choice-pills">
              <label class="choice-pill"><input type="radio" name="abholung" value="nein" checked><span><strong>Ich bringe das Auto</strong><small>{ESC(site.addr_line())}</small></span></label>
              <label class="choice-pill"><input type="radio" name="abholung" value="anfrage"><span><strong>Abholung anfragen</strong><small>nach Absprache in Celle</small></span></label>
            </div>
          </div>
        </fieldset>

        <fieldset class="wz-step" data-step="4">
          <legend><span class="wz-num">4</span>Wunschtermin</legend>
          <p class="wz-hint">{ESC(s["openingHours"]["text"])}, {ESC(s["openingHours"]["detail"])}. Wir bestätigen den Termin persönlich.</p>
          <div class="two-col">
            <div class="form-row"><label for="t-date1">Wunschtermin*</label><input type="date" id="t-date1" name="datum" required aria-describedby="t-date1-msg"><span class="field-msg" id="t-date1-msg"></span><button class="next-free next-free--fill" type="button" data-next-free data-nf-fill hidden><span class="nf-dot" aria-hidden="true"></span>Nächster freier Tag: <strong data-nf-date></strong> · übernehmen</button></div>
            <div class="form-row"><label for="t-date2">Ausweichtermin <span class="hint">(optional)</span></label><input type="date" id="t-date2" name="datum2" aria-describedby="t-date2-msg"><span class="field-msg" id="t-date2-msg"></span></div>
          </div>
          <div class="form-row"><label for="t-slot">Zeitfenster</label>
            <select id="t-slot" name="zeitfenster"><option value="morgens">Morgens bringen, abends abholen</option><option value="vormittag">Vormittags</option><option value="nachmittag">Nachmittags</option><option value="flexibel" selected>Ich bin flexibel</option></select>
          </div>
          <div class="form-row"><label for="t-gutschein">Gutscheincode <span class="hint">(falls vorhanden)</span></label><input type="text" id="t-gutschein" name="gutscheincode" maxlength="20" placeholder="ELB-XXXX-XXXX" autocomplete="off"></div>
        </fieldset>

        <fieldset class="wz-step" data-step="5">
          <legend><span class="wz-num">5</span>Wie erreichen wir dich?</legend>
          <div class="two-col">
            <div class="form-row"><label for="t-name">Name*</label><input type="text" id="t-name" name="name" autocomplete="name" required maxlength="120"></div>
            <div class="form-row"><label for="t-phone">Telefon / WhatsApp*</label><input type="tel" id="t-phone" name="telefon" autocomplete="tel" required maxlength="40"></div>
          </div>
          <div class="form-row"><label for="t-email">E-Mail <span class="hint">(für die Bestätigung)</span></label><input type="email" id="t-email" name="email" autocomplete="email" maxlength="160"></div>
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
            <label for="t-review">Ihr dürft mich nach dem Termin einmalig fragen, ob ich eine Google-Bewertung schreiben möchte. <span class="hint">(optional, jederzeit widerrufbar)</span></label>
          </div>
          {core.consent_row("", "t-consent")}
        </fieldset>

        <div class="wz-nav">
          <button class="btn btn-line-light" type="button" data-wz-prev hidden>Zurück</button>
          <button class="btn btn-primary" type="button" data-wz-next hidden>Weiter {I["arrow"]}</button>
          <button class="btn btn-primary" type="submit" data-wz-submit>{I["cal"]}Terminanfrage senden</button>
        </div>
        <button class="wz-wa" type="button" data-wa-from-form>{I["wa"]}Stattdessen alles per WhatsApp senden</button>
        {core.form_status("t-status")}
      </form>

      <aside class="wz-summary" aria-label="Zusammenfassung">
        <div class="summary-card">
          <h2>Deine Anfrage</h2>
          <dl>
            <div><dt>Paket</dt><dd data-sum="paket">–</dd></div>
            <div><dt>Fahrzeug</dt><dd data-sum="klasse">–</dd></div>
            <div><dt>Extras</dt><dd data-sum="extras">keine</dd></div>
            <div><dt>Wunschtermin</dt><dd data-sum="datum">–</dd></div>
          </dl>
          <div class="summary-price"><span>Richtpreis</span><strong data-sum="preis">–</strong></div>
          <p class="hint">Richtwert für normalen Pflegezustand inkl. MwSt. Den verbindlichen Preis bestätigen wir vor dem Termin.</p>
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
        {"q": "Was passiert bei einem größeren Fahrzeug?", "a": "Paketgutscheine gelten für die Kompaktklasse. Bei Limousine, Kombi, SUV oder Van wird nur die Differenz zum Richtpreis der jeweiligen Fahrzeugklasse fällig."},
        {"q": "Wie bezahle ich den Gutschein?", "a": "Nach deiner Bestellung bekommst du die Zahlungsdaten per E-Mail. Du zahlst per Überweisung oder bar bei Abholung. Nach Zahlungseingang erhältst du den Gutschein als Link zum Ausdrucken oder holst ihn gedruckt ab."},
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
            "Verschenke ein <em>Auto wie neu.</em>",
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
          <div class="form-row"><label for="g-msg">Nachricht <span class="hint">(max. 160 Zeichen)</span></label><textarea id="g-msg" name="widmung" rows="2" maxlength="160" placeholder="Frohe Weihnachten! Damit dein Auto endlich wieder glänzt."></textarea></div>
        </fieldset>
        <fieldset class="form-block">
          <legend>3. Zustellung &amp; Kontakt</legend>
          <div class="choice-pills">
            <label class="choice-pill"><input type="radio" name="zustellung" value="pdf" checked><span><strong>PDF per E-Mail</strong><small>zum Selbstausdrucken</small></span></label>
            <label class="choice-pill"><input type="radio" name="zustellung" value="abholung"><span><strong>Gedruckt abholen</strong><small>in Celle</small></span></label>
          </div>
          <div class="two-col">
            <div class="form-row"><label for="g-name">Dein Name*</label><input type="text" id="g-name" name="name" autocomplete="name" required maxlength="120"></div>
            <div class="form-row"><label for="g-email">E-Mail*</label><input type="email" id="g-email" name="email" autocomplete="email" required maxlength="160"></div>
          </div>
          <div class="form-row"><label for="g-phone">Telefon <span class="hint">(optional)</span></label><input type="tel" id="g-phone" name="telefon" autocomplete="tel" maxlength="40"></div>
          {core.honeypot("g-website")}
          {core.consent_row("", "g-consent")}
        </fieldset>
        <button class="btn btn-primary btn-lg btn-block" type="submit">{I["gift"]}Gutschein verbindlich bestellen</button>
        <p class="hint">Du bekommst die Zahlungsdaten per E-Mail (Überweisung oder bar bei Abholung). Nach Zahlungseingang erhältst du den Gutschein.</p>
        {core.form_status("g-status")}
      </form>

      <div class="voucher-preview-wrap">
        <p class="eyebrow">Vorschau</p>
        <div class="voucher-card" id="voucherPreview" aria-live="polite">
          <div class="vc-top"><img src="logo.svg" alt="" width="150" height="60"><span>Gutschein</span></div>
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
        {"q": "Ab wie vielen Fahrzeugen lohnt sich eine Rahmenvereinbarung?", "a": "Schon ab wenigen Fahrzeugen mit regelmäßigem Pflegebedarf. Wir besprechen Umfang und Intervalle individuell und machen ein Angebot, das zu deinem Fuhrpark passt."},
        {"q": "Bereitet ihr auch Fahrzeuge für Autohäuser und Händler auf?", "a": "Ja. Aufbereitung vor Verkauf, Übergabe oder Fotoshooting gehört zu unseren Kernleistungen. Abläufe und Fristen stimmen wir direkt mit dir ab."},
        {"q": "Wie wird abgerechnet?", "a": "Nach Absprache, zum Beispiel pro Fahrzeug oder gesammelt pro Zeitraum. Die Details halten wir im Angebot fest."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Firmenkunden", path)]), seo.faq(faq),
          {"@context": "https://schema.org", "@type": "Service", "name": "Fahrzeugaufbereitung für Firmen und Flotten", "serviceType": "Flottenpflege",
           "provider": {"@id": site.url + "/#business"}, "areaServed": {"@type": "City", "name": s["address"]["city"]}, "audience": {"@type": "BusinessAudience"}}]
    services = "".join(f'<label class="check"><input type="checkbox" name="leistungen" value="{ESC(x)}"><span>{ESC(x)}</span></label>' for x in
                       ["Regelmäßige Außenwäsche", "Innenreinigung", "Komplettaufbereitung", "Aufbereitung vor Verkauf/Rückgabe", "Lackpolitur & Versiegelung", "Geruchsentfernung"])
    body = f'''
<main id="main">
{_page_hero("", [("Startseite", "index.html"), ("Firmenkunden", None)], "Für Unternehmen",
            "Gepflegte Firmenwagen. <em>Planbar und ohne Aufwand.</em>",
            "Fahrzeugaufbereitung für Fuhrparks, Handwerksbetriebe, Autohäuser und Leasingrückläufer in Celle und Umgebung. Ein Ansprechpartner, feste Abläufe, Abrechnung nach Absprache.",
            f'<div class="hero-actions"><a class="btn btn-primary btn-lg" href="#firmenanfrage">{I["brief"]}Angebot anfordern</a><a class="btn btn-line" href="tel:{s["phone"]}">{I["phone"]}{ESC(s["phoneDisplay"])}</a></div>')}
  <section aria-labelledby="b2b-h">
    <div class="container">
      <div class="section-head"><p class="eyebrow">Warum ElbDetail</p><h2 id="b2b-h" class="display">Was Firmenkunden von uns bekommen.</h2></div>
      <div class="usecase-grid">
        <div class="usecase">{I["cal"]}<h3>Planbare Intervalle</h3><p>Feste Pflegetermine im passenden Rhythmus, abgestimmt auf eure Einsatzzeiten. So stehen Fahrzeuge nicht unnötig still.</p></div>
        <div class="usecase">{I["phone"]}<h3>Ein Ansprechpartner</h3><p>Direkter Draht per Telefon oder WhatsApp, kurze Wege und schnelle Rückmeldung auch bei kurzfristigem Bedarf.</p></div>
        <div class="usecase">{I["euro"]}<h3>Klare Konditionen</h3><p>Leistungsumfang und Preise pro Fahrzeugklasse werden im Angebot festgehalten. Abrechnung nach Absprache.</p></div>
        <div class="usecase">{I["key"]}<h3>Leasingrückläufer</h3><p>Aufbereitung vor der Rückgabe reduziert Beanstandungen wegen Verschmutzung, Gerüchen und oberflächlicher Gebrauchsspuren.</p></div>
        <div class="usecase">{I["tag"]}<h3>Autohäuser &amp; Händler</h3><p>Verkaufsfertige Aufbereitung für Inserat, Übergabe oder Showroom, in Handarbeit und mit Profi-Produkten.</p></div>
        <div class="usecase">{I["spark"]}<h3>Repräsentative Fahrzeuge</h3><p>Firmenwagen sind Visitenkarte. Lackpflege und Versiegelung halten sie dauerhaft in gutem Zustand.</p></div>
      </div>
    </div>
  </section>
  <section id="firmenanfrage" class="soft" aria-labelledby="ff-h">
    <div class="container two-up">
      <div>
        <div class="section-head"><p class="eyebrow">Angebot anfordern</p><h2 id="ff-h" class="display">Erzähl uns von deinem Fuhrpark.</h2>
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
{core.cta_band(site, "", "Lieber direkt sprechen?", "Ruf an oder schreib per WhatsApp. Wir klären Umfang und Ablauf in wenigen Minuten.")}
</main>
'''
    write("firmenkunden.html", core.head(site, title, desc, path, ld=ld) + core.header(site, current="firmenkunden.html") + body + core.footer(site))


# --------------------------------------------------------------------------- Winter-Aktion
def build_winter(site, write):
    s = site.s
    prefix = "../"
    path = "/aktion/winterschutz.html"
    title = "Auto winterfest machen in Celle: Lackschutz | ElbDetail"
    desc = (f"Lack, Felgen und Scheiben vor Streusalz schützen: Versiegelung in Celle vor dem ersten Frost. "
            f"Politur inkl. Versiegelung ab {site.min_price('premium')} €. Termin sichern.")
    prem = site.pkg("premium")
    faq = [
        {"q": "Wann sollte ich mein Auto versiegeln lassen?", "a": "Am besten vor dem ersten Frost und dem ersten Streusalz, in Celle also meist im Oktober oder November. Die Versiegelung braucht trockene Bedingungen und Zeit zum Aushärten."},
        {"q": "Reicht eine Versiegelung ohne Politur?", "a": "Bei gutem Lack ja. Sind Kratzer oder Hologramme sichtbar, empfehlen wir vorher eine Politur, weil die Versiegelung den Zustand darunter konserviert."},
        {"q": "Wie wasche ich das Auto im Winter richtig?", "a": "Regelmäßig Salz abspülen, möglichst per Handwäsche mit pH-neutralem Shampoo. Aggressive Reiniger aus der Waschstraße verkürzen die Haltbarkeit der Versiegelung."},
    ]
    ld = [seo.webpage(site, path, title), seo.crumbs(site, [("Startseite", "/"), ("Winter-Lackschutz", path)]), seo.faq(faq)]
    art = next((a for a in site.articles if a["slug"] == "auto-winterfest-lackschutz"), None)
    art_link = f'<p>Mehr Tipps im Ratgeber: <a class="text-link" href="{prefix}ratgeber/{art["slug"]}.html">{ESC(art["title"])}</a></p>' if art else ""
    body = f'''
<main id="main">
  <section class="page-hero page-hero--winter" aria-labelledby="page-h">
    <div class="container">
      {core.breadcrumb(prefix, [("Startseite", prefix + "index.html"), ("Winter-Lackschutz", None)])}
      <p class="eyebrow">Saison-Empfehlung Herbst &amp; Winter</p>
      <h1 id="page-h">Lack winterfest machen. <em>Bevor das Streusalz kommt.</em></h1>
      <p class="lead">Streusalz, Matsch und Frost setzen Lack, Felgen und Dichtungen stärker zu als jede andere Jahreszeit. Eine Versiegelung vor dem Winter sorgt dafür, dass Schmutz schlechter haftet und das Auto im Frühjahr nicht erst gerettet werden muss.</p>
      <div class="keyfacts"><div class="keyfact"><strong>ab {site.min_price("premium")} €</strong><span>{ESC(prem["name"])} inkl. Versiegelung</span></div><div class="keyfact"><strong>ca. 1 Tag</strong><span>Dauer</span></div><div class="keyfact"><strong>Monate</strong><span>Schutzdauer</span></div></div>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" href="{prefix}termin.html?paket=premium&amp;quelle=winter">{I["cal"]}Wintertermin anfragen</a>
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
          <li>{I["check"]}Bei Bedarf Politur gegen Kratzer und Hologramme</li>
          <li>{I["check"]}Lackversiegelung für Monate Schutz</li>
          <li>{I["check"]}Felgenversiegelung gegen Bremsstaub und Salz</li>
          <li>{I["check"]}Scheibenversiegelung für bessere Sicht bei Regen</li>
          <li>{I["check"]}Pflege von Gummidichtungen gegen Festfrieren</li>
          <li>{I["check"]}Pflegetipps für die Wäsche im Winter</li>
        </ul>
        <h2>Welche Variante passt?</h2>
        <div class="table-scroll" tabindex="0" role="region" aria-label="Tabelle, seitlich scrollbar"><table class="md-table"><thead><tr><th scope="col">Zustand des Lacks</th><th scope="col">Empfehlung</th><th scope="col">Richtpreis</th></tr></thead><tbody>
          <tr><th scope="row">Neuwagen oder sehr guter Lack</th><td>Versiegelung ohne Politur</td><td>auf Anfrage</td></tr>
          <tr><th scope="row">Leichte Kratzer, matter Glanz</th><td>{ESC(prem["name"])}: Politur + Versiegelung</td><td>ab {site.min_price("premium")} €</td></tr>
          <tr><th scope="row">Auch der Innenraum braucht Pflege</th><td>{ESC(prem["name"])} enthält die Komplettpflege innen</td><td>ab {site.min_price("premium")} €</td></tr>
        </tbody></table></div>
        <p class="hint">Richtpreise für eine Kompaktklasse. Limousine/Kombi ab {prem["prices"].get("mittel", "")} €, SUV/Van ab {prem["prices"].get("suv", "")} €.</p>
        {art_link}
        <h2>Häufige Fragen</h2>
        <div class="faq-list">{core.faq_html(faq, prefix)}</div>
      </div>
      <aside class="sticky-aside">
        <div class="aside-card dark">
          <h3>Wintertermin sichern</h3>
          <p>Die Wochen vor dem ersten Frost sind gefragt. Frag frühzeitig an, wir bestätigen den Termin persönlich.</p>
          <a class="btn btn-primary" href="{prefix}termin.html?paket=premium&amp;quelle=winter">{I["cal"]}Termin anfragen</a>
          <a class="btn btn-wa" href="{site.wa("Hallo ElbDetail, ich möchte mein Auto vor dem Winter versiegeln lassen.")}" target="_blank" rel="noopener">{I["wa"]}WhatsApp</a>
        </div>
        <div class="aside-card"><h3>Auch interessant</h3><ul>
          <li><a href="{prefix}leistungen/lackversiegelung-celle.html">Lackversiegelung Celle</a></li>
          <li><a href="{prefix}leistungen/lackpolitur-celle.html">Lackpolitur Celle</a></li>
          <li><a href="{prefix}gutscheine.html">Gutscheine zu Weihnachten</a></li></ul></div>
      </aside>
    </div>
  </section>
{core.cta_band(site, prefix, "Jetzt vor dem ersten Frost versiegeln.", "Kurz Fahrzeug und Wunschtermin nennen. Du bekommst ein verbindliches Angebot, bevor irgendetwas passiert.")}
</main>
'''
    write("aktion/winterschutz.html", core.head(site, title, desc, path, prefix=prefix, ld=ld) + core.header(site, prefix) + body + core.footer(site, prefix))


# --------------------------------------------------------------------------- Entwurf Pflege-Abo
def build_abo_draft(site, write):
    prefix = "../"
    ph = lambda t: f'<span class="legal-placeholder">[{t}]</span>'
    body = f'''
<main id="main">
  <section class="page-hero page-hero--compact" aria-labelledby="page-h">
    <div class="container">
      <p class="eyebrow">Entwurf · nicht öffentlich verlinkt</p>
      <h1 id="page-h">ElbDetail Pflege-Abo: <em>Immer gepflegt, ohne daran zu denken.</em></h1>
      <p class="lead">Regelmäßige Aufbereitung im festen Rhythmus mit Vorzugsterminen. Diese Seite ist ein Entwurf. Preise und Konditionen müssen vom Betrieb festgelegt werden, bevor sie live geht.</p>
    </div>
  </section>
  <section aria-label="Abo-Modelle">
    <div class="container">
      <div class="plans">
        <article class="plan"><h3>Basis</h3><p class="plan-for">Frisch &amp; Sauber alle {ph("6")} Wochen</p><div class="plan-price"><span class="amount">{ph("Preis / Monat")}</span></div><ul><li>{I["check"]}Feste Wunschtermine</li><li>{I["check"]}Erinnerung per WhatsApp</li><li>{I["check"]}{ph("Preisvorteil gegenüber Einzelbuchung")}</li></ul></article>
        <article class="plan is-featured"><span class="plan-badge">Empfehlung</span><h3>Plus</h3><p class="plan-for">Wechsel aus Frisch &amp; Sauber und Komplettpflege</p><div class="plan-price"><span class="amount">{ph("Preis / Monat")}</span></div><ul><li>{I["check"]}Alles aus Basis</li><li>{I["check"]}{ph("Anzahl")} × Komplettpflege pro Jahr</li><li>{I["check"]}Vorzugstermine</li></ul></article>
        <article class="plan"><h3>Premium</h3><p class="plan-for">Plus jährliche Politur und Versiegelung</p><div class="plan-price"><span class="amount">{ph("Preis / Monat")}</span></div><ul><li>{I["check"]}Alles aus Plus</li><li>{I["check"]}1 × Premium Politur pro Jahr</li><li>{I["check"]}{ph("Laufzeit / Kündigung")}</li></ul></article>
      </div>
      <p class="price-note">Zu klären: Laufzeit, Kündigungsfrist, Zahlungsweise, Umgang mit ausgefallenen Terminen, Fahrzeugwechsel. Danach kann die Seite in den Inhalten freigeschaltet und verlinkt werden.</p>
    </div>
  </section>
</main>
'''
    write("entwurf/pflege-abo.html", core.head(site, "Entwurf Pflege-Abo | ElbDetail", "Entwurf, nicht öffentlich.", "/entwurf/pflege-abo.html", prefix=prefix, noindex=True)
          + core.header(site, prefix) + body + core.footer(site, prefix))
