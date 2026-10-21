<?php
$o = orte()[$params['slug']];
$path = "/friseur-{$params['slug']}";
$crumbs = [[$o['title'], $path]];
$s = cfg()['salon'];
$fmtKm = fn(float $km) => number_format($km, 1, ',', '') . ' km';

$faq = [];
foreach ($o['routes'] as [$from, $km, $min]) {
    $faq[] = ["Wie weit ist AJ Atelier von {$from} entfernt?", "Von {$from} sind es rund {$fmtKm($km)} bzw. etwa {$min} Minuten mit dem Auto bis zu AJ Atelier in der {$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}."];
}
$faq[] = ["Kann ich als Kundin oder Kunde aus {$o['name']} online buchen?", 'Ja. Termine buchen Sie rund um die Uhr online, mit sofortiger Bestätigung per E-Mail. Bezahlen können Sie per PayPal oder vor Ort.'];

page_start([
    'title' => $o['metaTitle'],
    'description' => $o['description'],
    'path' => $path,
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <?php page_hero("Für {$o['name']} und Umgebung", $o['title'], e($o['intro']), $crumbs); ?>

    <section class="section">
      <div class="container content-grid">
        <article class="prose">
          <h2>Anfahrt aus <?= e($o['name']) ?></h2>
          <div class="table-wrap">
            <table class="route-table">
              <thead><tr><th scope="col">Start</th><th scope="col">Strecke</th><th scope="col">Fahrzeit (Auto)</th></tr></thead>
              <tbody>
                <?php foreach ($o['routes'] as [$from, $km, $min]): ?>
                <tr><th scope="row"><?= e($from) ?></th><td><?= e($fmtKm($km)) ?></td><td>ca. <?= (int)$min ?> Min.</td></tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
          <p class="hint">Richtwerte ohne Verkehr, berechnet mit OpenStreetMap.</p>
          <?php foreach ($o['text'] as $p): ?><p><?= e($p) ?></p><?php endforeach; ?>
          <h2>Unser Angebot für <?= e($o['name']) ?></h2>
          <p>Bei uns finden Sie <a href="/leistungen/balayage">Balayage</a> und <a href="/leistungen/babylights">Babylights</a> für natürlich aufgehelltes Haar, <a href="/leistungen/damenhaarschnitt">Damenhaarschnitte</a> und <a href="/leistungen/herren">Herrenschnitte</a> zum Festpreis sowie <a href="/leistungen/farbe">Farbe und Blondierung</a>. Alle Preise finden Sie in der <a href="/preise">Preisliste</a>.</p>
        </article>
        <aside class="content-aside">
          <div class="aside-card">
            <h2>So finden Sie uns</h2>
            <?php nap_block(); ?>
          </div>
          <div class="aside-card">
            <h2>Öffnungszeiten</h2>
            <?php hours_table(); ?>
          </div>
        </aside>
      </div>
      <div class="container"><?php map_link(); ?></div>
    </section>

    <section class="section marble" aria-labelledby="svc-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Leistungen</p>
          <h2 id="svc-title">Was wir für Sie tun</h2>
        </header>
        <?php service_cards(); ?>
      </div>
    </section>

    <section class="section" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Fragen aus <?= e($o['name']) ?></p>
          <h2 id="faq-title">Häufige Fragen</h2>
        </header>
        <?php faq_list($faq, true); ?>
      </div>
    </section>

    <?php cta_band('Termin für Kundinnen und Kunden aus ' . $o['name']); ?>
  </main>
<?php page_end();
