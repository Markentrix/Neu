<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';

$c = cfg();
$s = $c['salon'];
$tel = e($s['phone']);

$faq = [
    ['Wie kann ich einen Termin bei AJ Atelier buchen?', "Sie buchen rund um die Uhr online auf dieser Website: Leistung wählen, freien Termin aussuchen, Kontaktdaten eingeben – fertig. Sie erhalten sofort eine Bestätigung per E-Mail. Alternativ erreichen Sie uns telefonisch unter {$s['phoneDisplay']}."],
    ['Kann ich mit PayPal bezahlen?', 'Ja. Festpreis-Leistungen wie Haarschnitte können Sie bei der Online-Buchung direkt mit PayPal bezahlen. Bei Leistungen mit „ab“-Preis, etwa Balayage, zahlen Sie online nur eine Anzahlung, die vor Ort vollständig verrechnet wird. Selbstverständlich können Sie auch bar oder mit Karte im Salon bezahlen.'],
    ['Was kostet eine Balayage in Wettmar?', 'Balayage und Babylights beginnen im AJ Atelier ab 250 €. Der genaue Preis richtet sich nach Haarlänge, Haardichte und Materialverbrauch – vor Ort erhalten Sie einen individuellen Kostenvoranschlag, bevor wir beginnen.'],
    ['Was kostet ein Haarschnitt bei AJ Atelier?', 'Waschen, Schneiden und Föhnen für Damen kostet 55 € (kurz), 60 € (mittel) oder 70 € (lang). Der Herrenschnitt inklusive Waschen und Styling kostet 45 €, ein Maschinenschnitt 30 €.'],
    ['Wann hat AJ Atelier geöffnet?', 'Dienstag bis Freitag von 10 bis 18 Uhr und Samstag von 10 bis 14 Uhr. Sonntag, Montag und an Feiertagen ist der Salon geschlossen.'],
    ['Wo finde ich AJ Atelier?', "In der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']} (Region Hannover) – wenige Minuten aus Großburgwedel, Isernhagen, Fuhrberg, Thönse und Engensen, rund 20 Minuten von Hannover."],
    ['Kann ich meinen Termin stornieren?', "Ja, bis {$c['booking']['freeCancelHours']} Stunden vor dem Termin kostenfrei über den Link in Ihrer Bestätigungs-E-Mail. Eine online geleistete Zahlung wird dabei automatisch erstattet."],
    ['Bietet AJ Atelier Extensions an?', 'Extensions kommen in Kürze ins Angebot. Folgen Sie uns auf Instagram (@ajat.elier), um den Start nicht zu verpassen.'],
];

$faqSchema = [
    '@context' => 'https://schema.org',
    '@type' => 'FAQPage',
    'mainEntity' => array_map(fn($q) => ['@type' => 'Question', 'name' => $q[0], 'acceptedAnswer' => ['@type' => 'Answer', 'text' => $q[1]]], $faq),
];

// Daten für das Buchungs-Widget (keine Geheimnisse!)
$bookingData = [
    'categories' => array_map(fn($cat) => [
        'id' => $cat['id'], 'title' => $cat['title'],
        'services' => array_map(function ($sv) {
            $full = services()[$sv['id']];
            return ['id' => $sv['id'], 'name' => $full['fullName'], 'price' => $sv['price'], 'from' => $full['from'], 'consult' => $full['consult'], 'duration' => $sv['duration'], 'payNow' => online_amount($full)];
        }, $cat['services']),
    ], $c['categories']),
    'days' => bookable_days(),
    'maxServices' => $c['booking']['maxServices'],
    'paypalClientId' => paypal_enabled() ? $c['local']['paypal']['clientId'] : null,
    'hours' => $c['hours'],
    'holidays' => array_keys(holidays((int)date('Y')) + holidays((int)date('Y') + 1)),
    'salon' => ['name' => $s['name'], 'address' => "{$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}"],
];

function price_label(array $sv): string
{
    if (!empty($sv['consult'])) return 'nach Beratung';
    return (!empty($sv['from']) ? 'ab ' : '') . euro((float)$sv['price']);
}

page_start([
    'title' => 'Friseur Wettmar | AJ Atelier – Balayage, Babylights & Haarschnitt in Burgwedel',
    'ogTitle' => 'AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'AJ Atelier – Ihr Friseur in Burgwedel-Wettmar. Balayage, Babylights, Haarschnitt, Färben & Styling für Damen und Herren. Jetzt online Termin buchen – auch mit PayPal.',
    'schema' => [$faqSchema],
]);
?>
  <main id="main">
    <section class="hero marble" aria-labelledby="hero-title">
      <div class="container hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">Friseur in Burgwedel-Wettmar</p>
          <h1 id="hero-title">Dein Look.<br><em>Unsere Leidenschaft.</em></h1>
          <p class="lead">Balayage, Babylights, präzise Schnitte und Styling mit Gefühl – im AJ Atelier in Wettmar nehmen wir uns Zeit für Ihr Haar.</p>
          <div class="hero-actions">
            <a class="btn btn-gold" href="#termin">Online Termin buchen</a>
            <a class="btn btn-ghost" href="tel:<?= $tel ?>"><?= e($s['phoneDisplay']) ?></a>
          </div>
          <ul class="hero-facts" aria-label="Auf einen Blick">
            <li><strong>Di–Fr</strong> 10–18 Uhr</li>
            <li><strong>Sa</strong> 10–14 Uhr</li>
            <li><strong>PayPal</strong> oder vor Ort zahlen</li>
          </ul>
        </div>
        <div class="hero-emblem" aria-hidden="true">
          <svg viewBox="0 0 400 400" class="emblem">
            <defs>
              <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#ecd7a2"/><stop offset=".45" stop-color="#b8893a"/>
                <stop offset=".7" stop-color="#dcb86c"/><stop offset="1" stop-color="#8f6524"/>
              </linearGradient>
            </defs>
            <circle cx="200" cy="200" r="190" fill="rgba(255,255,255,.35)" stroke="url(#gold)" stroke-width="1.2"/>
            <circle cx="200" cy="200" r="178" fill="none" stroke="url(#gold)" stroke-width=".5"/>
            <path d="M48 238 C 120 110, 290 84, 366 166" fill="none" stroke="url(#gold)" stroke-width="2.4" stroke-linecap="round"/>
            <path d="M70 268 C 150 182, 296 166, 350 222" fill="none" stroke="url(#gold)" stroke-width="1" stroke-linecap="round"/>
            <text x="200" y="246" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="180" font-weight="500" fill="url(#gold)">AJ</text>
            <text x="206" y="318" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="30" letter-spacing="13" fill="#2c2620">ATELIER</text>
            <text x="203" y="346" text-anchor="middle" font-family="Jost, sans-serif" font-size="11" letter-spacing="6" fill="#7a6a55">HAIR · BEAUTY</text>
          </svg>
        </div>
      </div>
    </section>

    <section id="leistungen" class="section" aria-labelledby="leistungen-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Leistungen</p>
          <h2 id="leistungen-title">Handwerk, das man sieht</h2>
          <p>Von der natürlichen Balayage bis zum klassischen Herrenschnitt – jede Leistung beginnt mit einer ehrlichen Beratung.</p>
        </header>
        <div class="feature-grid">
          <article class="feature">
            <span class="feature-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c.6 4.2 2.8 6.4 7 7-4.2.6-6.4 2.8-7 7-.6-4.2-2.8-6.4-7-7 4.2-.6 6.4-2.8 7-7Z"/><path d="M19 16.5c.2 1.3.9 2 2.2 2.2-1.3.2-2 .9-2.2 2.2-.2-1.3-.9-2-2.2-2.2 1.3-.2 2-.9 2.2-2.2Z"/></svg></span>
            <h3>Balayage &amp; Babylights</h3>
            <p>Freihand gemalte, weiche Farbverläufe und feinste Strähnen für natürlich wirkendes, sonnengeküsstes Haar.</p>
          </article>
          <article class="feature">
            <span class="feature-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6.5" r="2.6"/><circle cx="6" cy="17.5" r="2.6"/><path d="M8.2 8 20 18M8.2 16 20 6"/></svg></span>
            <h3>Schnitt &amp; Styling</h3>
            <p>Damen- und Herrenschnitte, Föhnfrisuren und Hochsteckfrisuren – abgestimmt auf Gesichtsform und Alltag.</p>
          </article>
          <article class="feature">
            <span class="feature-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5s-6 6.6-6 10.6a6 6 0 0 0 12 0c0-4-6-10.6-6-10.6Z"/><path d="M9 14.5a3 3 0 0 0 3 3"/></svg></span>
            <h3>Farbe &amp; Blondierung</h3>
            <p>Ansatzfarbe, Komplettfärbung, Glossing und Color Correction – individuell kalkuliert nach Aufwand.</p>
          </article>
          <article class="feature">
            <span class="feature-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19c0-8 5-13 14-14-.5 9-5.5 14-14 14Z"/><path d="M5 19 13 11"/></svg></span>
            <h3>Pflege &amp; Brows</h3>
            <p>Bond Treatment und Haarpflege für gesunden Glanz, dazu Augenbrauen- und Wimpernservice.</p>
          </article>
        </div>
        <p class="soon">Extensions – <strong>bald im AJ Atelier</strong></p>
      </div>
    </section>

    <section id="preise" class="section marble" aria-labelledby="preise-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Preisliste</p>
          <h2 id="preise-title">Unsere Preise</h2>
          <p>Alle Preise in Euro inkl. MwSt.</p>
        </header>
        <div class="price-card">
          <?php foreach ($c['categories'] as $cat): ?>
          <section class="price-group" aria-labelledby="pg-<?= e($cat['id']) ?>">
            <h3 id="pg-<?= e($cat['id']) ?>"><?= e($cat['title']) ?></h3>
            <p class="price-sub"><?= e($cat['subtitle']) ?></p>
            <dl class="price-list">
              <?php $lastGroup = null; foreach ($cat['services'] as $sv):
                if (isset($sv['group']) && $sv['group'] !== $lastGroup): $lastGroup = $sv['group']; ?>
              <div class="price-row price-row-group"><dt><?= e($sv['group']) ?></dt><dd></dd></div>
              <?php endif; ?>
              <div class="price-row<?= isset($sv['group']) ? ' is-sub' : '' ?>">
                <dt><?= e($sv['name']) ?></dt>
                <dd><?= e(price_label($sv)) ?></dd>
              </div>
              <?php endforeach; ?>
            </dl>
            <?php if (!empty($cat['note'])): ?><p class="price-note"><?= e($cat['note']) ?></p><?php endif; ?>
          </section>
          <?php endforeach; ?>
        </div>
        <p class="center"><a class="btn btn-gold" href="#termin">Jetzt Termin buchen</a></p>
      </div>
    </section>

    <section id="termin" class="section booking-section" aria-labelledby="termin-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Online-Terminbuchung</p>
          <h2 id="termin-title">Ihr Wunschtermin in 4 Schritten</h2>
          <p>Rund um die Uhr buchen, sofortige Bestätigung per E-Mail. Bezahlen Sie bequem mit PayPal oder vor Ort.</p>
        </header>

        <div class="booking" data-booking>
          <ol class="steps" aria-label="Buchungsschritte">
            <li class="is-active" data-step-label="1"><span>1</span> Leistung</li>
            <li data-step-label="2"><span>2</span> Termin</li>
            <li data-step-label="3"><span>3</span> Daten</li>
            <li data-step-label="4"><span>4</span> Zahlung</li>
          </ol>

          <div class="booking-body">
            <div class="booking-main">
              <section class="step" data-step="1" aria-labelledby="st1">
                <h3 id="st1" class="step-title">Welche Leistungen wünschen Sie?</h3>
                <p class="hint">Mehrfachauswahl möglich, z. B. Färben + Schnitt (max. <?= (int)$c['booking']['maxServices'] ?>).</p>
                <div class="service-picker" data-service-picker></div>
                <div class="step-actions">
                  <button class="btn btn-gold" type="button" data-next disabled>Weiter zur Terminwahl</button>
                </div>
              </section>

              <section class="step" data-step="2" hidden aria-labelledby="st2">
                <h3 id="st2" class="step-title">Wann passt es Ihnen?</h3>
                <div class="date-strip-wrap">
                  <button class="icon-btn" type="button" data-date-prev aria-label="Frühere Tage">‹</button>
                  <div class="date-strip" data-date-strip></div>
                  <button class="icon-btn" type="button" data-date-next aria-label="Spätere Tage">›</button>
                </div>
                <div class="slots" data-slots aria-live="polite"></div>
                <div class="step-actions">
                  <button class="btn btn-ghost" type="button" data-back>Zurück</button>
                  <button class="btn btn-gold" type="button" data-next disabled>Weiter</button>
                </div>
              </section>

              <section class="step" data-step="3" hidden aria-labelledby="st3">
                <h3 id="st3" class="step-title">Ihre Kontaktdaten</h3>
                <form class="form-grid" data-customer-form novalidate>
                  <label>Vor- und Nachname*<input name="name" autocomplete="name" required minlength="2" maxlength="80"></label>
                  <label>Telefon*<input name="phone" type="tel" autocomplete="tel" required maxlength="25"></label>
                  <label class="full">E-Mail* <small>(für die Bestätigung)</small><input name="email" type="email" autocomplete="email" required maxlength="254"></label>
                  <label class="full">Anmerkung <small>(optional, z. B. Haarlänge, Wunschfarbe)</small><textarea name="note" rows="3" maxlength="500"></textarea></label>
                  <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
                  <label class="check full"><input type="checkbox" name="consent" required> <span>Ich bin einverstanden, dass meine Angaben zur Terminvereinbarung verarbeitet werden. Details in der <a href="/datenschutz.php" target="_blank" rel="noopener">Datenschutzerklärung</a>.*</span></label>
                  <p class="form-error full" data-form-error role="alert" hidden></p>
                </form>
                <div class="step-actions">
                  <button class="btn btn-ghost" type="button" data-back>Zurück</button>
                  <button class="btn btn-gold" type="button" data-next>Weiter zur Zahlung</button>
                </div>
              </section>

              <section class="step" data-step="4" hidden aria-labelledby="st4">
                <h3 id="st4" class="step-title">Wie möchten Sie bezahlen?</h3>
                <div class="pay-options">
                  <label class="pay-option" data-paypal-option hidden>
                    <input type="radio" name="payment" value="paypal">
                    <span><strong>Jetzt mit PayPal bezahlen</strong><small data-paypal-label></small></span>
                  </label>
                  <label class="pay-option">
                    <input type="radio" name="payment" value="onsite" checked>
                    <span><strong>Vor Ort bezahlen</strong><small>Bar oder Karte im Salon</small></span>
                  </label>
                </div>
                <div class="paypal-box" data-paypal-box hidden>
                  <div data-paypal-buttons></div>
                  <p class="hint">Ihr Termin ist erst nach erfolgreicher Zahlung gebucht. Mit dem Laden von PayPal werden Daten an PayPal (Europe) übermittelt.</p>
                </div>
                <p class="form-error" data-pay-error role="alert" hidden></p>
                <div class="step-actions">
                  <button class="btn btn-ghost" type="button" data-back>Zurück</button>
                  <button class="btn btn-gold" type="button" data-submit-onsite>Verbindlich buchen</button>
                </div>
              </section>

              <section class="step confirmation" data-step="done" hidden tabindex="-1" aria-labelledby="st5">
                <div class="check-circle" aria-hidden="true">✓</div>
                <h3 id="st5" class="step-title">Vielen Dank – Ihr Termin ist gebucht!</h3>
                <p data-confirmation-text></p>
                <p class="hint">Eine Bestätigung ist unterwegs in Ihr Postfach. Bis <?= (int)$c['booking']['freeCancelHours'] ?> Stunden vorher können Sie dort kostenfrei stornieren.</p>
                <div class="step-actions center">
                  <a class="btn btn-ghost" href="#" data-ics download="aj-atelier-termin.ics">In Kalender eintragen</a>
                  <button class="btn btn-gold" type="button" data-restart>Weiteren Termin buchen</button>
                </div>
              </section>
            </div>

            <aside class="booking-summary" aria-label="Ihre Auswahl">
              <h3>Ihre Auswahl</h3>
              <ul data-summary-list><li class="muted">Noch keine Leistung gewählt</li></ul>
              <dl>
                <div><dt>Dauer</dt><dd data-summary-duration>–</dd></div>
                <div><dt>Termin</dt><dd data-summary-date>–</dd></div>
                <div><dt>Preis</dt><dd data-summary-price>–</dd></div>
              </dl>
              <p class="hint" data-summary-hint hidden>Finaler Preis nach Aufwand – Kostenvoranschlag vor Ort.</p>
            </aside>
          </div>
          <noscript><p class="form-error">Für die Online-Buchung wird JavaScript benötigt. Rufen Sie uns gerne an: <a href="tel:<?= $tel ?>"><?= e($s['phoneDisplay']) ?></a>.</p></noscript>
        </div>
      </div>
      <script type="application/json" id="booking-data"><?= json_encode($bookingData, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP) ?></script>
    </section>

    <section id="ueber-uns" class="section marble" aria-labelledby="ueber-title">
      <div class="container split">
        <div>
          <p class="eyebrow">Über uns</p>
          <h2 id="ueber-title">Ein Atelier für Haar &amp; Beauty – mitten in Wettmar</h2>
          <p>Im AJ Atelier verbinden wir moderne Farbtechniken mit klassischem Friseurhandwerk. Ob sanfte Balayage, kühles Blond oder der perfekte Alltags-Schnitt: Wir hören zu, beraten ehrlich und arbeiten mit hochwertigen Produkten, die Ihr Haar schonen.</p>
          <p>Unser Salon liegt in der Hauptstraße in Burgwedel-Wettmar – nur wenige Minuten von Großburgwedel, Isernhagen, Fuhrberg und Thönse entfernt.</p>
          <ul class="checklist">
            <li>Individuelle Farbberatung &amp; Kostenvoranschlag</li>
            <li>Haarschonende Techniken mit Bond-Pflege</li>
            <li>Online buchen, mit PayPal oder vor Ort zahlen</li>
          </ul>
        </div>
        <figure class="quote">
          <blockquote><p>„Dein Look.<br>Unsere Leidenschaft.“</p></blockquote>
          <figcaption>— Das Team vom AJ Atelier</figcaption>
        </figure>
      </div>
    </section>

    <section id="faq" class="section" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">FAQ</p>
          <h2 id="faq-title">Häufige Fragen</h2>
        </header>
        <div class="faq">
          <?php foreach ($faq as $i => [$q, $a]): ?>
          <details<?= $i === 0 ? ' open' : '' ?>><summary><?= e($q) ?></summary><p><?= e($a) ?></p></details>
          <?php endforeach; ?>
        </div>
      </div>
    </section>

    <section id="kontakt" class="section contact" aria-labelledby="kontakt-title">
      <div class="container contact-grid">
        <div>
          <p class="eyebrow">Kontakt &amp; Anfahrt</p>
          <h2 id="kontakt-title">Besuchen Sie uns in Wettmar</h2>
          <address class="nap">
            <strong><?= e($s['legalName']) ?></strong><br>
            <?= e($s['street']) ?><br>
            <?= e("{$s['zip']} {$s['city']}-{$s['district']}") ?><br>
            <a href="tel:<?= $tel ?>"><?= e($s['phoneDisplay']) ?></a><br>
            <a href="<?= e($s['instagram']) ?>" rel="noopener" target="_blank">Instagram: @ajat.elier</a>
          </address>
          <div class="hero-actions">
            <a class="btn btn-gold" href="https://www.google.com/maps/dir/?api=1&amp;destination=<?= rawurlencode("{$s['name']}, {$s['street']}, {$s['zip']} {$s['city']}") ?>" target="_blank" rel="noopener">Route planen</a>
            <a class="btn btn-ghost" href="tel:<?= $tel ?>">Anrufen</a>
          </div>
        </div>
        <div class="hours-card">
          <h3>Öffnungszeiten</h3>
          <table class="hours">
            <?php
            $names = [2 => 'Dienstag', 3 => 'Mittwoch', 4 => 'Donnerstag', 5 => 'Freitag', 6 => 'Samstag', 0 => 'Sonntag', 1 => 'Montag'];
            foreach ($names as $d => $n): $h = $c['hours'][$d]; ?>
            <tr data-day="<?= $d ?>"><th scope="row"><?= $n ?></th><td><?= $h ? '<time>' . e($h[0]) . '</time> – <time>' . e($h[1]) . '</time>' : 'geschlossen' ?></td></tr>
            <?php endforeach; ?>
          </table>
          <p class="open-now" data-open-now aria-live="polite"></p>
        </div>
      </div>
      <div class="container">
        <a class="map-link" href="https://www.openstreetmap.org/?mlat=<?= $s['lat'] ?>&amp;mlon=<?= $s['lng'] ?>#map=17/<?= $s['lat'] ?>/<?= $s['lng'] ?>" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z"/></svg>
          <span><strong>Karte öffnen</strong><small><?= e("{$s['street']} · {$s['zip']} {$s['city']}-{$s['district']}") ?></small></span>
        </a>
      </div>
    </section>
  </main>
<?php page_end();
