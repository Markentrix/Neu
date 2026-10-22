<?php
// Ziel nach jeder Anfrage an das Portal: danke.html?typ=<typ>&ref=<Vorgangsnummer>
page_start([
    'title' => 'Vielen Dank | AJ Atelier',
    'description' => 'Ihre Anfrage bei AJ Atelier in Burgwedel-Wettmar ist angekommen.',
    'path' => '/danke',
    'canonical' => false,
    'robots' => 'noindex, follow',
]);
$s = cfg()['salon'];
?>
  <main id="main" class="page">
    <div class="container narrow card center thanks" data-thanks>
      <div class="check-circle" aria-hidden="true"><svg viewBox="0 0 52 52"><path class="check-path" pathLength="1" d="M15 27l7.5 7.5L38 19" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="spark s1"></span><span class="spark s2"></span><span class="spark s3"></span><span class="spark s4"></span><span class="spark s5"></span><span class="spark s6"></span></div>
      <h1 data-thanks-title>Vielen Dank!</h1>
      <p data-thanks-text>Ihre Anfrage ist bei uns angekommen. Eine Eingangsbestätigung ist unterwegs in Ihr Postfach.</p>
      <p class="voucher-code" data-thanks-ref hidden></p>
      <p class="hint" data-thanks-hint>Keine E-Mail bekommen? Schauen Sie bitte auch im Spam-Ordner nach oder rufen Sie uns an: <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a>.</p>
      <p class="hero-actions center">
        <a class="btn btn-ghost" href="#" data-ics download="aj-atelier-termin.ics" hidden>In Kalender eintragen</a>
        <a class="btn btn-gold" href="/">Zur Startseite</a>
      </p>
    </div>
  </main>
<?php page_end(false, ['danke.js']);
