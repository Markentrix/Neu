<?php
$crumbs = [['Leistungen', '/leistungen']];
$items = [];
foreach (leistungen() as $slug => $l) $items[] = ['@type' => 'ListItem', 'position' => count($items) + 1, 'name' => $l['name'], 'url' => site_url("/leistungen/{$slug}")];

page_start([
    'title' => 'Leistungen | Friseur AJ Atelier in Burgwedel-Wettmar',
    'description' => 'Alle Leistungen von AJ Atelier in Burgwedel-Wettmar: Balayage, Babylights, Damen- & Herrenschnitt, Hochsteckfrisuren, Farbe, Pflege, Brauen & Wimpern.',
    'path' => '/leistungen',
    'crumbs' => $crumbs,
    'schema' => [['@context' => 'https://schema.org', '@type' => 'ItemList', 'name' => 'Leistungen von AJ Atelier', 'itemListElement' => $items]],
]);
?>
  <main id="main">
    <?php page_hero('Leistungen', 'Unsere Leistungen', 'Farbe, Schnitt, Styling und Pflege für Damen und Herren. Wählen Sie eine Leistung für Details, Preise und Dauer, oder buchen Sie direkt online.', $crumbs); ?>

    <section class="section">
      <div class="container">
        <?php service_cards(null, 'h2'); ?>
        <p class="soon">Extensions – <strong>bald im AJ Atelier</strong></p>
      </div>
    </section>

    <section class="section marble" aria-labelledby="beratung-title">
      <div class="container split">
        <div>
          <p class="eyebrow">Beratung</p>
          <h2 id="beratung-title">Nicht sicher, was Sie buchen sollen?</h2>
          <p>Bei Farbwünschen ist die richtige Technik nicht immer offensichtlich. Buchen Sie die Leistung, die Ihrem Wunsch am nächsten kommt, und beschreiben Sie ihn im Feld „Anmerkung“. Vor dem Start besprechen wir alles gemeinsam und erstellen einen Kostenvoranschlag.</p>
          <p>Bei größeren Farbkorrekturen buchen Sie zuerst den Beratungstermin unter <a href="/leistungen/farbe">Färben &amp; Blondierung</a>.</p>
        </div>
        <div class="aside-card">
          <h3>Kombinieren erwünscht</h3>
          <p>Wählen Sie online die Hauptleistung, zum Beispiel Ansatzfarbe, und schreiben Sie weitere Wünsche wie Haarschnitt oder Augenbrauen ins Feld „Anmerkung“. Wir planen die Zeit passend ein und melden uns, falls etwas nicht passt.</p>
          <p><a class="btn btn-gold" href="/termin">Zur Terminbuchung</a></p>
        </div>
      </div>
    </section>

    <?php cta_band(); ?>
  </main>
<?php page_end();
