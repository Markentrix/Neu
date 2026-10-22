<?php
$crumbs = [['Preise', '/preise']];
page_start([
    'title' => 'Preise | Friseur AJ Atelier Wettmar – Balayage ab 250 €',
    'description' => 'Preisliste von AJ Atelier in Burgwedel-Wettmar: Waschen, Schneiden & Föhnen ab 55 €, Herrenschnitt 45 €, Balayage ab 250 €, Glossing ab 22 €. Inkl. MwSt.',
    'path' => '/preise',
    'crumbs' => $crumbs,
]);
?>
  <main id="main">
    <?php page_hero('Preisliste', 'Unsere Preise', 'Alle Preise in Euro inklusive MwSt. Schnitte und Styling haben feste Preise, Farbbehandlungen werden nach Aufwand und Verbrauch berechnet.', $crumbs); ?>

    <section class="section">
      <div class="container">
        <?php price_list('h2'); ?>
      </div>
    </section>

    <section class="section marble" aria-labelledby="zahlung-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Bezahlen</p>
          <h2 id="zahlung-title">So bezahlen Sie bei uns</h2>
        </header>
        <div class="info-grid">
          <div class="aside-card">
            <h3>Festpreise</h3>
            <p>Haarschnitte, Waschen &amp; Föhnen und Wimpern färben haben feste Preise. Was Sie online sehen, zahlen Sie auch im Salon.</p>
          </div>
          <div class="aside-card">
            <h3>„ab“-Preise</h3>
            <p>Bei Farbe, Balayage und Pflege hängt der Preis von Haarlänge, Dichte und Materialverbrauch ab. Vor dem Start bekommen Sie einen Kostenvoranschlag, damit es keine Überraschungen gibt.</p>
          </div>
          <div class="aside-card">
            <h3>Im Salon &amp; Gutscheine</h3>
            <p>Bezahlt wird nach dem Termin im Salon, bar oder mit Karte. Gutscheine können Sie <a href="/gutscheine">online anfragen</a> und bequem per PayPal bezahlen.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="details-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Details</p>
          <h2 id="details-title">Mehr zu jeder Leistung</h2>
          <p>Ablauf, Dauer und Antworten auf häufige Fragen finden Sie auf den Seiten der einzelnen Leistungen.</p>
        </header>
        <?php service_cards(); ?>
      </div>
    </section>

    <?php cta_band(); ?>
  </main>
<?php page_end();
