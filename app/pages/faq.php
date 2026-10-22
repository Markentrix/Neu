<?php
$crumbs = [['Häufige Fragen', '/faq']];
$faq = general_faq();
foreach (leistungen() as $l) {
    foreach ($l['faq'] ?? [] as $q) $faq[] = $q;
}
// Doppelte Fragen entfernen
$seen = [];
$faq = array_values(array_filter($faq, function ($q) use (&$seen) {
    if (isset($seen[$q[0]])) return false;
    return $seen[$q[0]] = true;
}));

page_start([
    'title' => 'Häufige Fragen | Friseur AJ Atelier Wettmar',
    'description' => 'Antworten zu Terminbuchung, Bezahlung, Preisen, Balayage, Öffnungszeiten und Anfahrt bei AJ Atelier, Ihrem Friseur in Burgwedel-Wettmar.',
    'path' => '/faq',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq)],
]);
?>
  <main id="main">
    <?php page_hero('FAQ', 'Häufige Fragen', 'Alles zu Buchung, Bezahlung, Preisen und unseren Leistungen. Ihre Frage ist nicht dabei? Rufen Sie uns an oder schreiben Sie uns über das Kontaktformular.', $crumbs); ?>

    <section class="section">
      <div class="container narrow">
        <?php faq_list($faq); ?>
        <p class="center"><a class="btn btn-ghost" href="/kontakt">Frage stellen</a></p>
      </div>
    </section>

    <?php cta_band(); ?>
  </main>
<?php page_end();
