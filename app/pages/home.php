<?php
$c = cfg();
$s = $c['salon'];
$faq = array_slice(general_faq(), 0, 5);

page_start([
    'title' => 'Friseur Wettmar & Burgwedel | AJ Atelier – Balayage & Schnitt',
    'ogTitle' => 'AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'AJ Atelier, Ihr Friseur in Burgwedel-Wettmar: Balayage, Babylights, Haarschnitt, Färben & Styling für Damen und Herren. Online Termin buchen, auch mit PayPal.',
    'path' => '/',
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <section class="hero marble" aria-labelledby="hero-title">
      <div class="container hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">Friseur in Burgwedel-Wettmar</p>
          <h1 id="hero-title">Dein Look.<br><em>Unsere Leidenschaft.</em></h1>
          <p class="lead">Balayage, Babylights, präzise Schnitte und Styling mit Gefühl. Im AJ Atelier in Wettmar nehmen wir uns Zeit für Ihr Haar.</p>
          <div class="hero-actions">
            <a class="btn btn-gold" href="#termin">Online Termin buchen</a>
            <a class="btn btn-ghost" href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a>
          </div>
          <ul class="hero-facts" aria-label="Auf einen Blick">
            <li><strong>Di–Fr</strong> 10–18 Uhr</li>
            <li><strong>Sa</strong> 10–14 Uhr</li>
            <li><strong>PayPal</strong> oder vor Ort zahlen</li>
          </ul>
        </div>
        <div class="hero-emblem" aria-hidden="true">
          <span class="em-shine"></span>
          <svg viewBox="0 0 400 400" class="emblem">
            <defs>
              <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#ecd7a2"/><stop offset=".45" stop-color="#b8893a"/>
                <stop offset=".7" stop-color="#dcb86c"/><stop offset="1" stop-color="#8f6524"/>
              </linearGradient>
            </defs>
            <circle class="em-disc" cx="200" cy="200" r="190" fill="rgba(255,255,255,.35)"/>
            <circle class="em-draw em-ring" cx="200" cy="200" r="190" fill="none" stroke="url(#gold)" stroke-width="1.2" pathLength="1" transform="rotate(-90 200 200)"/>
            <circle class="em-draw em-ring2" cx="200" cy="200" r="178" fill="none" stroke="url(#gold)" stroke-width=".5" pathLength="1" transform="rotate(90 200 200)"/>
            <path class="em-draw em-swoosh" pathLength="1" d="M48 238 C 120 110, 290 84, 366 166" fill="none" stroke="url(#gold)" stroke-width="2.4" stroke-linecap="round"/>
            <path class="em-draw em-swoosh2" pathLength="1" d="M70 268 C 150 182, 296 166, 350 222" fill="none" stroke="url(#gold)" stroke-width="1" stroke-linecap="round"/>
            <text class="em-aj" x="200" y="246" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="180" font-weight="500" fill="url(#gold)">AJ</text>
            <text class="em-atelier" x="206" y="318" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="30" letter-spacing="13" fill="#2c2620">ATELIER</text>
            <text class="em-hair" x="203" y="346" text-anchor="middle" font-family="Jost, sans-serif" font-size="11" letter-spacing="6" fill="#7a6a55">HAIR · BEAUTY</text>
          </svg>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="leistungen-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Leistungen</p>
          <h2 id="leistungen-title">Handwerk, das man sieht</h2>
          <p>Von der natürlichen Balayage bis zum klassischen Herrenschnitt. Jede Leistung beginnt mit einer ehrlichen Beratung.</p>
        </header>
        <?php service_cards(); ?>
        <p class="soon">Extensions – <strong>bald im AJ Atelier</strong></p>
      </div>
    </section>

    <section class="section marble" aria-labelledby="preise-title">
      <div class="container split">
        <div>
          <p class="eyebrow">Preise</p>
          <h2 id="preise-title">Klare Preise, ehrliche Beratung</h2>
          <p>Schnitte und Styling haben bei uns feste Preise. Bei Farbe und Techniken wie Balayage richtet sich der Preis nach Haarlänge und Verbrauch. Bevor wir beginnen, erhalten Sie einen Kostenvoranschlag.</p>
          <p><a class="btn btn-ghost" href="/preise">Komplette Preisliste</a></p>
        </div>
        <dl class="price-teaser">
          <?php foreach (['d-wsf-kurz', 'h-schnitt', 'f-ansatz', 'f-balayage', 'f-glossing', 'b-wimpern'] as $id): $sv = services()[$id]; ?>
          <div class="price-row"><dt><?= e($sv['fullName']) ?></dt><dd><?= e(price_label($sv)) ?></dd></div>
          <?php endforeach; ?>
        </dl>
      </div>
    </section>

    <section id="termin" class="section booking-section" aria-labelledby="termin-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Online-Terminbuchung</p>
          <h2 id="termin-title">Ihr Wunschtermin in 4 Schritten</h2>
          <p>Rund um die Uhr buchen, sofortige Bestätigung per E-Mail. Bezahlen Sie bequem mit PayPal oder vor Ort.</p>
        </header>
        <?php booking_widget(); ?>
      </div>
    </section>

    <section class="section marble" aria-labelledby="ueber-title">
      <div class="container split">
        <div>
          <p class="eyebrow">Über uns</p>
          <h2 id="ueber-title">Ein Atelier für Haar &amp; Beauty, mitten in Wettmar</h2>
          <p>Im AJ Atelier verbinden wir moderne Farbtechniken mit klassischem Friseurhandwerk. Wir hören zu, beraten ehrlich und arbeiten mit Produkten, die Ihr Haar schonen.</p>
          <ul class="checklist">
            <li>Individuelle Farbberatung &amp; Kostenvoranschlag</li>
            <li>Haarschonende Aufhellung mit Bond Treatment</li>
            <li>Online buchen, mit PayPal oder vor Ort zahlen</li>
          </ul>
          <p><a class="btn btn-ghost" href="/ueber-uns">Mehr über uns</a></p>
        </div>
        <figure class="quote">
          <blockquote><p>„Dein Look.<br>Unsere Leidenschaft.“</p></blockquote>
          <figcaption>Das Team vom AJ Atelier</figcaption>
        </figure>
      </div>
    </section>

    <section class="section" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Häufige Fragen</p>
          <h2 id="faq-title">Gut zu wissen</h2>
        </header>
        <?php faq_list($faq, true); ?>
        <p class="center"><a class="btn btn-ghost" href="/faq">Alle Fragen &amp; Antworten</a></p>
      </div>
    </section>

    <section class="section contact" aria-labelledby="kontakt-title">
      <div class="container contact-grid">
        <div>
          <p class="eyebrow">Kontakt &amp; Anfahrt</p>
          <h2 id="kontakt-title">Besuchen Sie uns in Wettmar</h2>
          <?php nap_block(); ?>
          <p class="areas">Schnell erreichbar aus
            <?php $links = []; foreach (orte() as $slug => $o) $links[] = '<a href="/friseur-' . e($slug) . '">' . e($o['name']) . '</a>'; echo implode(', ', $links); ?>.</p>
        </div>
        <div class="hours-card">
          <h3>Öffnungszeiten</h3>
          <?php hours_table(); ?>
        </div>
      </div>
      <div class="container"><?php map_link(); ?></div>
    </section>
  </main>
<?php page_end();
