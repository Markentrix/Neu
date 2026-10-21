<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';
require __DIR__ . '/../../app/layout.php';

security_headers();
header('X-Robots-Tag: noindex, nofollow');
$configured = !empty(cfg()['local']['adminPasswordHash']);
$loggedIn = is_admin(); // vor jeder Ausgabe, da Session-Cookie
?>
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>Terminverwaltung · AJ Atelier</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/css/styles.css?v=<?= filemtime(__DIR__ . '/../css/styles.css') ?>">
  <link rel="stylesheet" href="/css/admin.css?v=<?= filemtime(__DIR__ . '/../css/admin.css') ?>">
</head>
<body class="admin">
  <header class="admin-bar">
    <a class="brand" href="/"><span class="brand-mark">AJ</span><span class="brand-text">Termine<small>Verwaltung</small></span></a>
    <button class="btn btn-ghost btn-sm" type="button" data-logout <?= $loggedIn ? '' : 'hidden' ?>>Abmelden</button>
  </header>

  <main class="admin-main">
    <?php if (!$configured): ?>
      <div class="card">
        <h1>Einrichtung nötig</h1>
        <p>Bitte in <code>app/config.local.php</code> einen <code>adminPasswordHash</code> eintragen (siehe README).</p>
      </div>
    <?php else: ?>
    <form class="card login" data-login <?= $loggedIn ? 'hidden' : '' ?>>
      <h1>Anmelden</h1>
      <label>Passwort<input type="password" name="password" autocomplete="current-password" required></label>
      <p class="form-error" data-login-error hidden></p>
      <button class="btn btn-gold" type="submit">Anmelden</button>
    </form>

    <div data-app <?= $loggedIn ? '' : 'hidden' ?>>
      <div class="tabs" role="tablist">
        <button type="button" role="tab" aria-selected="true" data-tab="termine">Termine</button>
        <button type="button" role="tab" aria-selected="false" data-tab="gutscheine">Gutscheine</button>
      </div>

      <div data-panel="termine">
      <div class="toolbar">
        <button class="icon-btn" type="button" data-prev aria-label="Vorherige Woche">‹</button>
        <input type="date" data-from value="<?= e(today()) ?>" aria-label="Ab Datum">
        <button class="icon-btn" type="button" data-next aria-label="Nächste Woche">›</button>
        <button class="btn btn-ghost btn-sm" type="button" data-today>Heute</button>
        <label class="inline"><input type="checkbox" data-show-cancelled> Stornierte zeigen</label>
        <span class="stats" data-stats></span>
      </div>

      <div class="days" data-days></div>

      <details class="card block-form">
        <summary><strong>Zeit blockieren</strong> (Pause, Telefon-Termin, Urlaub)</summary>
        <form data-block class="form-grid">
          <label>Datum<input type="date" name="date" required></label>
          <label>Beginn<input type="time" name="time" step="900" required></label>
          <label>Dauer (Minuten)<input type="number" name="duration" min="5" max="720" step="5" value="60" required></label>
          <label>Name (optional)<input name="name" maxlength="80" placeholder="z. B. Telefon-Kundin"></label>
          <label class="full">Notiz<input name="note" maxlength="200"></label>
          <button class="btn btn-gold" type="submit">Blockieren</button>
        </form>
      </details>
      </div>

      <div data-panel="gutscheine" hidden>
        <form class="toolbar" data-voucher-search>
          <input type="search" name="q" placeholder="Code, Käufer:in oder Empfänger:in" aria-label="Gutschein suchen" style="flex:1;min-width:220px">
          <button class="btn btn-gold btn-sm" type="submit">Suchen</button>
        </form>
        <div class="days" data-vouchers></div>
      </div>
    </div>
    <?php endif; ?>
  </main>
  <script type="module" src="/js/admin.js?v=<?= filemtime(__DIR__ . '/../js/admin.js') ?>"></script>
</body>
</html>
