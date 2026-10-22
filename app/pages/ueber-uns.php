<?php
$crumbs = [['Über uns', '/ueber-uns']];
$s = cfg()['salon'];
page_start([
    'title' => 'Über uns | AJ Atelier – Friseur in Burgwedel-Wettmar',
    'description' => 'AJ Atelier ist ein Friseursalon in der Hauptstraße 64 in Burgwedel-Wettmar. Unser Anspruch: ehrliche Beratung, moderne Farbtechniken und klassisches Handwerk.',
    'path' => '/ueber-uns',
    'crumbs' => $crumbs,
    'schema' => [[
        '@context' => 'https://schema.org',
        '@type' => 'AboutPage',
        'url' => site_url('/ueber-uns'),
        'name' => 'Über AJ Atelier',
        'about' => ['@id' => site_url('/#salon')],
    ]],
]);
?>
  <main id="main">
    <?php page_hero('Über uns', 'Dein Look. Unsere Leidenschaft.', 'Das AJ Atelier ist ein Salon für Haar und Beauty in Burgwedel-Wettmar. Hier verbinden wir moderne Farbtechniken mit klassischem Friseurhandwerk.', $crumbs); ?>

    <section class="section">
      <div class="container content-grid">
        <article class="prose">
          <h2>Wofür wir stehen</h2>
          <p>Ein guter Friseurbesuch beginnt nicht mit der Schere, sondern mit Zuhören. Bevor wir schneiden oder färben, sprechen wir über Ihre Wünsche, Ihren Alltag und darüber, was Ihr Haar schon erlebt hat. Erst dann schlagen wir vor, was wirklich zu Ihnen passt.</p>
          <p>Unsere Leidenschaft gilt besonders der Farbe. Mit Techniken wie <a href="/leistungen/balayage">Balayage</a> und <a href="/leistungen/babylights">Babylights</a> entstehen natürliche, weiche Ergebnisse, die schön herauswachsen. Für Aufhellungen setzen wir ein <a href="/leistungen/pflege">Bond Treatment</a> ein, damit Ihr Haar dabei so gut wie möglich geschützt wird.</p>
          <h2>Ehrlich bei Preisen</h2>
          <p>Schnitte und Styling haben bei uns feste Preise. Bei Farbe hängt der Aufwand stark vom Haar ab. Deshalb erhalten Sie vor jeder Farbbehandlung einen individuellen Kostenvoranschlag. So wissen Sie vorher, woran Sie sind.</p>
          <h2>Einfach buchen</h2>
          <p>Termine buchen Sie bei uns rund um die Uhr online. Sie sehen sofort, welche Zeiten frei sind, und bezahlen ganz entspannt nach dem Termin im Salon. Für Kurzfristiges sind wir telefonisch unter <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a> erreichbar.</p>
          <h2>Bald neu: Extensions</h2>
          <p>Mehr Länge und Fülle: Extensions kommen in Kürze ins Angebot. Auf <a href="<?= e($s['instagram']) ?>" rel="noopener" target="_blank">Instagram</a> erfahren Sie zuerst, wann es losgeht.</p>
        </article>
        <div class="content-aside">
          <figure class="quote">
            <blockquote><p>„Dein Look.<br>Unsere Leidenschaft.“</p></blockquote>
            <figcaption>Das Team vom AJ Atelier</figcaption>
          </figure>
          <div class="aside-card">
            <h2>Besuchen Sie uns</h2>
            <?php nap_block(); ?>
          </div>
        </div>
      </div>
    </section>

    <?php cta_band(); ?>
  </main>
<?php page_end();
