<?php
$slug = $params['slug'];
$a = ratgeber()[$slug];
$path = "/ratgeber/{$slug}";
$crumbs = [['Ratgeber', '/ratgeber'], [$a['title'], $path]];
$s = cfg()['salon'];
page_start([
    'title' => $a['metaTitle'],
    'description' => $a['description'],
    'path' => $path,
    'crumbs' => $crumbs,
    'schema' => [[
        '@context' => 'https://schema.org',
        '@type' => 'BlogPosting',
        'headline' => $a['title'],
        'description' => $a['description'],
        'datePublished' => $a['date'],
        'dateModified' => date('Y-m-d', filemtime(__DIR__ . '/../content/ratgeber.php')),
        'inLanguage' => 'de-DE',
        'mainEntityOfPage' => site_url($path),
        'image' => site_url('/img/og-image.png'),
        'author' => ['@type' => 'Organization', 'name' => $s['name'], 'url' => site_url('/')],
        'publisher' => ['@id' => site_url('/#salon')],
    ]],
]);
?>
  <main id="main">
    <?php page_hero('Ratgeber · ' . (int)$a['minutes'] . ' Min. Lesezeit', $a['title'], e($a['intro']), $crumbs, null); ?>
    <section class="section">
      <div class="container content-grid">
        <article class="prose">
          <?php foreach ($a['sections'] as [$h, $paras]): ?>
          <h2><?= e($h) ?></h2>
          <?php foreach ($paras as $p): ?><p><?= $p ?></p><?php endforeach; ?>
          <?php endforeach; ?>
          <p class="hint">Veröffentlicht am <?= e(date('d.m.Y', strtotime($a['date']))) ?> vom Team des <?= e($s['name']) ?>.</p>
        </article>
        <div class="content-aside">
          <div class="aside-card">
            <h2>Persönliche Beratung</h2>
            <p>Jedes Haar ist anders. Wir schauen uns Ihres gern an und beraten Sie ehrlich.</p>
            <p><a class="btn btn-gold" href="/termin">Termin buchen</a></p>
          </div>
          <div class="aside-card">
            <h2>Weitere Artikel</h2>
            <?php foreach (ratgeber() as $other => $o): if ($other === $slug) continue; ?>
            <p><?= icon('arrow') ?> <a href="/ratgeber/<?= e($other) ?>"><?= e($o['title']) ?></a></p>
            <?php endforeach; ?>
          </div>
        </div>
      </div>
    </section>
    <section class="section marble" aria-labelledby="related-title">
      <div class="container">
        <header class="section-head">
          <p class="eyebrow">Passende Leistungen</p>
          <h2 id="related-title">Im AJ Atelier</h2>
        </header>
        <?php service_cards($a['related']); ?>
      </div>
    </section>
  </main>
<?php page_end();
