<?php
$crumbs = [['Ratgeber', '/ratgeber']];
page_start([
    'title' => 'Haar-Ratgeber | Tipps vom Friseur AJ Atelier Wettmar',
    'description' => 'Tipps vom Friseur aus Burgwedel-Wettmar: Balayage pflegen, wie oft den Ansatz färben, von dunkel zu blond. Ehrlich erklärt vom Team des AJ Atelier.',
    'path' => '/ratgeber',
    'crumbs' => $crumbs,
]);
?>
  <main id="main">
    <?php page_hero('Ratgeber', 'Tipps rund ums Haar', 'Pflege, Farbe und Styling: Antworten auf Fragen, die uns im Salon oft gestellt werden.', $crumbs); ?>
    <section class="section">
      <div class="container">
        <div class="card-grid">
          <?php foreach (ratgeber() as $slug => $a): ?>
          <a class="svc-card" href="/ratgeber/<?= e($slug) ?>">
            <h2><?= e($a['title']) ?></h2>
            <p><?= e($a['teaser']) ?></p>
            <span class="svc-meta"><?= (int)$a['minutes'] ?> Min. Lesezeit <span class="svc-more">Lesen <?= icon('arrow') ?></span></span>
          </a>
          <?php endforeach; ?>
        </div>
      </div>
    </section>
    <?php cta_band(); ?>
  </main>
<?php page_end();
