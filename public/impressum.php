<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';
$s = cfg()['salon'];

page_start([
    'title' => 'Impressum | AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'Impressum von AJ Atelier, Friseur in der Hauptstraße 64, 30938 Burgwedel-Wettmar.',
    'path' => '/impressum.php',
    'robots' => 'noindex, follow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card">
      <h1>Impressum</h1>
      <h2>Angaben gemäß § 5 DDG</h2>
      <p><span class="placeholder">[Vor- und Nachname der Inhaberin / des Inhabers]</span><br>
        <?= e($s['legalName']) ?><br><?= e($s['street']) ?><br><?= e("{$s['zip']} {$s['city']}-{$s['district']}") ?></p>
      <h2>Kontakt</h2>
      <p>Telefon: <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a><br>
        E-Mail: <span class="placeholder">[E-Mail-Adresse]</span></p>
      <h2>Umsatzsteuer-ID</h2>
      <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: <span class="placeholder">[USt-IdNr. oder Steuernummer]</span></p>
      <h2>Berufsrechtliche Angaben</h2>
      <p>Eintragung in die Handwerksrolle der <span class="placeholder">[Handwerkskammer Hannover]</span>, Betriebsnummer <span class="placeholder">[…]</span>.<br>
        Berufsbezeichnung: Friseurin/Friseur (verliehen in der Bundesrepublik Deutschland). Es gilt die Handwerksordnung (HwO), abrufbar unter <a href="https://www.gesetze-im-internet.de/hwo/" rel="noopener" target="_blank">gesetze-im-internet.de</a>.</p>
      <h2>Verbraucherstreitbeilegung</h2>
      <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
      <h2>Haftung für Inhalte und Links</h2>
      <p>Die Inhalte dieser Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität können wir jedoch keine Gewähr übernehmen. Für Inhalte verlinkter externer Seiten sind ausschließlich deren Betreiber verantwortlich.</p>
    </div>
  </main>
<?php page_end();
