<?php
$l = leistungen()[$params['slug']];
$slug = $params['slug'];
$path = "/leistungen/{$slug}";
$crumbs = [['Leistungen', '/leistungen'], [$l['name'], $path]];
$s = cfg()['salon'];

$serviceSchema = [
    '@context' => 'https://schema.org',
    '@type' => 'Service',
    'name' => $l['title'],
    'serviceType' => $l['name'],
    'description' => $l['description'],
    'url' => site_url($path),
    'provider' => ['@id' => site_url('/#salon')],
    'areaServed' => array_map(fn($a) => ['@type' => 'Place', 'name' => $a], $s['areaServed']),
    'offers' => array_map(fn($id) => offer_schema(services()[$id]) + ['url' => site_url('/termin?leistung=' . $id)], $l['services']),
];
$schema = [$serviceSchema];
if (!empty($l['faq'])) $schema[] = faq_schema($l['faq']);

page_start([
    'title' => $l['metaTitle'],
    'description' => $l['description'],
    'path' => $path,
    'crumbs' => $crumbs,
    'schema' => $schema,
]);
?>
  <main id="main">
    <?php page_hero('Leistung', $l['title'], e($l['intro']), $crumbs, '/termin?leistung=' . $l['services'][0], $l['name'] . ' buchen'); ?>

    <section class="section">
      <div class="container content-grid">
        <article class="prose">
          <?php foreach ($l['sections'] as [$h, $paras]): ?>
          <h2><?= e($h) ?></h2>
          <?php foreach ($paras as $p): ?><p><?= $p ?></p><?php endforeach; ?>
          <?php endforeach; ?>

          <?php if (!empty($l['steps'])): ?>
          <h2>So läuft Ihr Termin ab</h2>
          <ol class="steps-list">
            <?php foreach ($l['steps'] as [$t, $d]): ?>
            <li><strong><?= e($t) ?></strong><span><?= e($d) ?></span></li>
            <?php endforeach; ?>
          </ol>
          <?php endif; ?>
        </article>
        <aside class="content-aside">
          <?php service_price_box($l['services']); ?>
          <div class="aside-card">
            <h2>AJ Atelier</h2>
            <p><?= icon('pin') ?> <?= e("{$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}") ?></p>
            <p><?= icon('clock') ?> Di–Fr 10–18 Uhr · Sa 10–14 Uhr</p>
            <p><?= icon('phone') ?> <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a></p>
          </div>
        </aside>
      </div>
    </section>

    <?php if (!empty($l['faq'])): ?>
    <section class="section marble" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Fragen zu <?= e($l['name']) ?></p>
          <h2 id="faq-title">Häufige Fragen</h2>
        </header>
        <?php faq_list($l['faq'], true); ?>
      </div>
    </section>
    <?php endif; ?>

    <section class="section" aria-labelledby="related-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Passt gut dazu</p>
          <h2 id="related-title">Weitere Leistungen</h2>
        </header>
        <?php service_cards($l['related']); ?>
      </div>
    </section>

    <?php cta_band($l['name'] . ' bei AJ Atelier buchen'); ?>
  </main>
<?php page_end();
