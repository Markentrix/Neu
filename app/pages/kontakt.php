<?php
$crumbs = [['Kontakt & Anfahrt', '/kontakt']];
$s = cfg()['salon'];
page_start([
    'title' => 'Kontakt & Anfahrt | Friseur AJ Atelier Burgwedel-Wettmar',
    'description' => 'AJ Atelier, Hauptstraße 64, 30938 Burgwedel-Wettmar, Tel. 05139 9856600. Geöffnet Di–Fr 10–18 Uhr, Sa 10–14 Uhr. Anfahrt und Kontaktformular.',
    'path' => '/kontakt',
    'crumbs' => $crumbs,
    'schema' => [[
        '@context' => 'https://schema.org',
        '@type' => 'ContactPage',
        'url' => site_url('/kontakt'),
        'name' => 'Kontakt AJ Atelier',
        'about' => ['@id' => site_url('/#salon')],
    ]],
]);
?>
  <main id="main">
    <?php page_hero('Kontakt & Anfahrt', 'So erreichen Sie uns', 'Am schnellsten geht ein Termin online. Für Fragen rufen Sie uns an oder schreiben Sie uns über das Formular.', $crumbs); ?>

    <section class="section">
      <div class="container contact-grid">
        <div>
          <h2>AJ Atelier in Wettmar</h2>
          <?php nap_block(); ?>
          <h3>Anfahrt</h3>
          <p>Der Salon liegt an der Hauptstraße in Wettmar, einem Ortsteil von Burgwedel in der Region Hannover. Ins Navi geben Sie „Hauptstraße 64, 30938 Burgwedel“ ein.</p>
          <ul class="route-list">
            <?php foreach (orte() as $slug => $o): [$from, $km, $min] = $o['routes'][0]; ?>
            <li><a href="/friseur-<?= e($slug) ?>"><?= e($from) ?></a><span>ca. <?= (int)$min ?> Min.</span></li>
            <?php endforeach; ?>
          </ul>
        </div>
        <div class="hours-card">
          <h2>Öffnungszeiten</h2>
          <?php hours_table(); ?>
        </div>
      </div>
      <div class="container"><?php map_link(); ?></div>
    </section>

    <section class="section marble" aria-labelledby="form-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Nachricht</p>
          <h2 id="form-title">Schreiben Sie uns</h2>
          <p>Für Fragen zu Leistungen, Brautfrisuren oder Gruppenterminen. Termine selbst buchen Sie am schnellsten <a href="/termin">online</a>.</p>
        </header>
        <form class="form-grid contact-form" data-contact-form novalidate>
          <label>Name*<input id="c-name" name="name" autocomplete="name" required minlength="2" maxlength="80"></label>
          <label>Telefon <small>(optional)</small><input id="c-phone" name="phone" type="tel" autocomplete="tel" maxlength="25"></label>
          <label class="full">E-Mail*<input id="c-email" name="email" type="email" autocomplete="email" required maxlength="254"></label>
          <label class="full">Ihre Nachricht*<textarea id="c-message" name="message" rows="5" required minlength="10" maxlength="2000"></textarea></label>
          <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
          <label class="check full"><input id="c-consent" type="checkbox" name="consent" required> <span>Ich bin einverstanden, dass meine Angaben zur Beantwortung meiner Anfrage verarbeitet werden. Details in der <a href="/datenschutz">Datenschutzerklärung</a>.*</span></label>
          <p class="form-error full" data-contact-error role="alert" hidden></p>
          <p class="form-ok full" data-contact-ok role="status" hidden>Vielen Dank! Ihre Nachricht ist angekommen. Wir melden uns so schnell wie möglich.</p>
          <div class="full"><button class="btn btn-gold" type="submit">Nachricht senden</button></div>
        </form>
      </div>
    </section>
  </main>
  <script type="module" src="/js/contact.js?v=<?= filemtime(__DIR__ . '/../../public/js/contact.js') ?>"></script>
<?php page_end();
