<?php
$crumbs = [['Termin buchen', '/termin']];
$faq = [
    ['Wann bekomme ich eine Bestätigung?', 'Direkt nach dem Absenden per E-Mail, mit Ihrer Vorgangsnummer und allen Details. Einen Tag vor dem Termin erinnern wir Sie noch einmal per E-Mail.'],
    ['Warum kann ich Balayage nicht sofort fest buchen?', 'Aufwendige Farbtermine dauern drei bis vier Stunden und hängen stark von Ihrem Haar ab. Deshalb senden Sie uns einen Wunschtermin mit ein paar Angaben zu Ihrem Haar. Wir melden uns persönlich, bestätigen den Termin und reservieren ihn gegen eine Anzahlung per PayPal, die vollständig verrechnet wird.'],
    ['Was passiert bei Leistungen mit „ab“-Preis?', 'Den Endpreis besprechen wir vor Beginn mit Ihnen, er richtet sich nach Haarlänge, Dichte und Materialverbrauch. Bezahlt wird nach dem Termin im Salon.'],
    ['Wie sage ich meinen Termin ab?', 'Über den Link in der Bestätigungs- oder Erinnerungs-E-Mail. Bitte sagen Sie spätestens 24 Stunden vorher ab, damit wir den Termin neu vergeben können.'],
    ['Ich finde keinen passenden Termin. Was nun?', 'Rufen Sie uns an. Manchmal werden kurzfristig Zeiten frei, die wir telefonisch vergeben.'],
];

page_start([
    'title' => 'Termin online buchen | Friseur AJ Atelier Wettmar',
    'description' => 'Termin bei AJ Atelier in Burgwedel-Wettmar reservieren: Schnitt und Styling direkt online, Farbtermine wie Balayage mit persönlicher Abstimmung.',
    'path' => '/termin',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <?php page_hero('Online-Terminbuchung', 'Termin buchen', 'Schnitt und Styling reservieren Sie direkt. Farbtermine wie Balayage, Babylights oder Blondierung planen wir persönlich mit Ihnen, damit Zeit, Technik und Preis von Anfang an stimmen.', $crumbs, null); ?>

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
