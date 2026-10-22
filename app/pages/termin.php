<?php
$crumbs = [['Termin buchen', '/termin']];
$faq = [
    ['Wann bekomme ich eine Bestätigung?', 'Direkt nach dem Absenden per E-Mail, mit Ihrer Vorgangsnummer und allen Details. Einen Tag vor dem Termin erinnern wir Sie noch einmal per E-Mail.'],
    ['Was passiert bei Leistungen mit „ab“-Preis?', 'Den Endpreis besprechen wir vor Beginn mit Ihnen, er richtet sich nach Haarlänge, Dichte und Materialverbrauch. Bezahlt wird nach dem Termin im Salon.'],
    ['Wie sage ich meinen Termin ab?', 'Über den Link in der Bestätigungs- oder Erinnerungs-E-Mail. Bitte sagen Sie spätestens 24 Stunden vorher ab, damit wir den Termin neu vergeben können.'],
    ['Ich finde keinen passenden Termin. Was nun?', 'Rufen Sie uns an. Manchmal werden kurzfristig Zeiten frei, die wir telefonisch vergeben.'],
];

page_start([
    'title' => 'Termin online buchen | Friseur AJ Atelier Wettmar',
    'description' => 'Friseurtermin bei AJ Atelier in Burgwedel-Wettmar online buchen: freie Zeiten sofort sehen, rund um die Uhr buchen, Bestätigung per E-Mail.',
    'path' => '/termin',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <?php page_hero('Online-Terminbuchung', 'Termin buchen', 'Wählen Sie Ihre Leistung und eine freie Uhrzeit. Die Bestätigung mit Vorgangsnummer kommt per E-Mail, bezahlt wird im Salon.', $crumbs, null); ?>

    <section id="termin" class="section booking-section" aria-labelledby="buchen-title">
      <div class="container">
        <h2 id="buchen-title" class="sr-only">Leistung und Termin wählen</h2>
        <?php booking_widget(); ?>
      </div>
    </section>

    <section class="section marble" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Zur Buchung</p>
          <h2 id="faq-title">Häufige Fragen</h2>
        </header>
        <?php faq_list($faq); ?>
      </div>
    </section>
  </main>
<?php page_end(false);
