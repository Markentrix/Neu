<?php
declare(strict_types=1);
require __DIR__ . '/../app/lib.php';
require __DIR__ . '/../app/layout.php';

$id = (string)($_GET['id'] ?? '');
$token = (string)($_GET['t'] ?? '');
$st = db()->prepare("SELECT * FROM entries WHERE id = ? AND type = 'booking'");
$st->execute([$id]);
$b = $st->fetch();
$valid = $b && $b['cancel_token'] && hash_equals($b['cancel_token'], $token);

page_start([
    'title' => 'Termin stornieren | AJ Atelier',
    'description' => 'Termin bei AJ Atelier online stornieren.',
    'path' => '/termin-stornieren.php',
    'robots' => 'noindex, nofollow',
]);
?>
  <main id="main" class="page">
    <div class="container narrow card center" data-cancel data-id="<?= e($id) ?>" data-token="<?= e($token) ?>">
      <h1>Termin stornieren</h1>
      <?php if (!$valid): ?>
        <p>Dieser Link ist ungültig. Bitte rufen Sie uns an: <a href="tel:<?= e(cfg()['salon']['phone']) ?>"><?= e(cfg()['salon']['phoneDisplay']) ?></a>.</p>
      <?php elseif ($b['status'] === 'cancelled'): ?>
        <p>Dieser Termin wurde bereits storniert.</p>
      <?php else:
        $services = implode(', ', array_column(json_decode($b['services'], true) ?: [], 'name')); ?>
        <p><strong><?= e(german_date($b['date'])) ?>, <?= to_time((int)$b['start_min']) ?> Uhr</strong><br><?= e($services) ?></p>
        <?php if ((float)$b['pay_amount'] > 0): ?><p>Ihre Zahlung über <?= e(euro((float)$b['pay_amount'], true)) ?> wird automatisch über PayPal erstattet.</p><?php endif; ?>
        <p data-cancel-msg role="status"></p>
        <p><button class="btn btn-gold" type="button" data-cancel-btn>Termin jetzt stornieren</button></p>
        <p><a href="/#termin">Neuen Termin buchen</a></p>
      <?php endif; ?>
    </div>
  </main>
  <script type="module" src="/js/cancel.js"></script>
<?php page_end(false);
