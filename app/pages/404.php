<?php
page_start([
    'title' => 'Seite nicht gefunden | AJ Atelier',
    'description' => 'Diese Seite existiert nicht.',
    'path' => '/404',
    'canonical' => false,
    'robots' => 'noindex, follow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card center">
      <h1>Seite nicht gefunden</h1>
      <p>Die gesuchte Seite gibt es leider nicht (mehr).</p>
      <p><a class="btn btn-gold" href="/">Zur Startseite</a> <a class="btn btn-ghost" href="/termin">Termin buchen</a></p>
    </div>
    <div class="container" style="margin-top:3rem">
      <h2 class="center">Unsere Leistungen</h2>
      <?php service_cards(); ?>
    </div>
  </main>
<?php page_end();
