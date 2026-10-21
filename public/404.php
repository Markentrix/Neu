<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';
http_response_code(404);
page_start([
    'title' => 'Seite nicht gefunden | AJ Atelier',
    'description' => 'Diese Seite existiert nicht.',
    'path' => '/',
    'robots' => 'noindex, follow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card center">
      <h1>Seite nicht gefunden</h1>
      <p>Die gesuchte Seite gibt es leider nicht (mehr).</p>
      <p><a class="btn btn-gold" href="/">Zur Startseite</a> <a class="btn btn-ghost" href="/#termin">Termin buchen</a></p>
    </div>
  </main>
<?php page_end();
