<?php
$c = cfg();
$crumbs = [['Termin buchen', '/termin']];
$faq = [
    ['Wann bekomme ich eine Bestätigung?', 'Direkt nach der Buchung per E-Mail. Darin finden Sie alle Details und einen Link zum Stornieren.'],
    ['Was passiert bei Leistungen mit „ab“-Preis?', 'Online zahlen Sie per PayPal nur eine Anzahlung, die vor Ort vollständig verrechnet wird. Den Endpreis besprechen wir vor Beginn mit Ihnen.'],
    ['Wie storniere ich meinen Termin?', "Bis {$c['booking']['freeCancelHours']} Stunden vorher kostenfrei über den Link in der Bestätigungs-E-Mail. Online geleistete Zahlungen werden automatisch erstattet."],
    ['Ich finde keinen passenden Termin. Was nun?', 'Rufen Sie uns an. Manchmal werden kurzfristig Zeiten frei, die wir telefonisch vergeben.'],
];

page_start([
    'title' => 'Termin online buchen | Friseur AJ Atelier Wettmar',
    'description' => 'Friseurtermin bei AJ Atelier in Burgwedel-Wettmar online buchen: freie Zeiten sofort sehen, Bestätigung per E-Mail, mit PayPal oder vor Ort bezahlen.',
    'path' => '/termin',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <?php page_hero('Online-Terminbuchung', 'Termin buchen', 'Wählen Sie Ihre Leistungen und eine freie Uhrzeit. Die Bestätigung kommt sofort per E-Mail. Bezahlen Sie per PayPal oder vor Ort.', $crumbs, null); ?>

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
