<?php
$c = cfg();
$v = $c['vouchers'];
$crumbs = [['Gutscheine', '/gutscheine']];
$faq = [
    ['Wie lange ist ein Gutschein gültig?', "Gutscheine sind bis zum Ende des dritten Jahres nach dem Kauf gültig, ein im Jahr " . date('Y') . " gekaufter Gutschein also bis zum 31.12." . ((int)date('Y') + $v['validYears']) . '.'],
    ['Wofür kann der Gutschein eingelöst werden?', 'Für alle Leistungen im AJ Atelier, auch in Teilbeträgen. Der Restbetrag bleibt auf dem Gutschein erhalten.'],
    ['Wie bekomme ich den Gutschein?', 'Direkt nach der Zahlung per E-Mail als PDF zum Ausdrucken oder Weiterleiten. Sie können ihn außerdem sofort auf der Seite herunterladen.'],
    ['Kann ich auch im Salon einen Gutschein kaufen?', 'Ja, natürlich. Sprechen Sie uns einfach bei Ihrem nächsten Besuch an.'],
];
page_start([
    'title' => 'Gutschein online kaufen | Friseur AJ Atelier Wettmar',
    'description' => 'Friseur-Gutschein von AJ Atelier in Burgwedel-Wettmar online kaufen: Betrag wählen, mit PayPal bezahlen, sofort als PDF per E-Mail erhalten. 3 Jahre gültig.',
    'path' => '/gutscheine',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq), [
        '@context' => 'https://schema.org',
        '@type' => 'Product',
        'name' => 'Gutschein AJ Atelier',
        'description' => 'Wertgutschein für alle Leistungen bei AJ Atelier in Burgwedel-Wettmar, als PDF per E-Mail.',
        'brand' => ['@type' => 'Brand', 'name' => $c['salon']['name']],
        'offers' => ['@type' => 'AggregateOffer', 'priceCurrency' => 'EUR', 'lowPrice' => $v['min'], 'highPrice' => $v['max'], 'availability' => 'https://schema.org/InStock', 'url' => site_url('/gutscheine')],
    ]],
]);
?>
  <main id="main">
    <?php page_hero('Gutscheine', 'Gutschein verschenken', 'Ein Friseur-Gutschein für Balayage, einen neuen Schnitt oder eine Pflege-Auszeit. Online bezahlen und sofort als PDF per E-Mail erhalten.', $crumbs, null); ?>

    <section class="section">
      <div class="container content-grid">
        <div class="voucher-shop" data-voucher-shop data-min="<?= (int)$v['min'] ?>" data-max="<?= (int)$v['max'] ?>" data-paypal="<?= e(paypal_enabled() ? $c['local']['paypal']['clientId'] : '') ?>">
          <form class="form-grid voucher-form" data-voucher-form novalidate>
            <fieldset class="full amount-field">
              <legend>Betrag wählen</legend>
              <div class="amount-chips">
                <?php foreach ($v['amounts'] as $i => $a): ?>
                <label class="chip"><input type="radio" name="amount" value="<?= (int)$a ?>"<?= $i === 1 ? ' checked' : '' ?>><span><?= (int)$a ?> €</span></label>
                <?php endforeach; ?>
                <label class="chip chip-custom"><input type="radio" name="amount" value="custom"><span>Eigener Betrag</span></label>
              </div>
              <label class="custom-amount" data-custom-amount hidden>Betrag in Euro (<?= (int)$v['min'] ?>–<?= (int)$v['max'] ?>)
                <input id="v-custom" name="custom" type="number" inputmode="numeric" min="<?= (int)$v['min'] ?>" max="<?= (int)$v['max'] ?>" step="1">
              </label>
            </fieldset>
            <label>Für (optional)<input id="v-recipient" name="recipient" maxlength="60" placeholder="z. B. Maria"></label>
            <label class="full">Persönliche Nachricht (optional, max. 200 Zeichen)<textarea id="v-message" name="message" rows="3" maxlength="200" placeholder="Alles Liebe zum Geburtstag!"></textarea></label>
            <label>Ihr Name*<input id="v-buyer" name="buyerName" autocomplete="name" required maxlength="80"></label>
            <label>Ihre E-Mail*<input id="v-email" name="buyerEmail" type="email" autocomplete="email" required maxlength="254"></label>
            <label class="check full"><input id="v-consent" type="checkbox" name="consent" required> <span>Ich bin einverstanden, dass meine Angaben zur Ausstellung und Zusendung des Gutscheins verarbeitet werden. Details in der <a href="/datenschutz">Datenschutzerklärung</a>.*</span></label>
            <p class="form-error full" data-voucher-error role="alert" hidden></p>
            <div class="full" data-voucher-pay>
              <?php if (paypal_enabled()): ?>
              <button class="btn btn-gold" type="submit">Weiter zur Zahlung</button>
              <?php else: ?>
              <p class="notice">Online-Gutscheine sind gerade nicht verfügbar. Gutscheine erhalten Sie jederzeit im Salon oder telefonisch unter <a href="tel:<?= e($c['salon']['phone']) ?>"><?= e($c['salon']['phoneDisplay']) ?></a>.</p>
              <?php endif; ?>
            </div>
            <div class="full paypal-box" data-voucher-paypal hidden>
              <p class="hint">Gutschein über <strong data-voucher-sum></strong> – bezahlen Sie sicher mit PayPal:</p>
              <div data-voucher-buttons></div>
              <button class="btn btn-ghost btn-sm" type="button" data-voucher-edit>Angaben ändern</button>
            </div>
          </form>
          <div class="voucher-done" data-voucher-done hidden tabindex="-1">
            <div class="check-circle" aria-hidden="true">✓</div>
            <h2>Vielen Dank für Ihren Kauf!</h2>
            <p>Ihr Gutschein über <strong data-done-amount></strong> ist ausgestellt.</p>
            <p class="voucher-code" data-done-code></p>
            <p data-done-mail></p>
            <p><a class="btn btn-gold" data-done-pdf href="#" target="_blank" rel="noopener">Gutschein als PDF öffnen</a></p>
          </div>
        </div>
        <div class="content-aside">
          <div class="voucher-card" aria-hidden="true">
            <span class="brand-mark">AJ</span>
            <span class="vc-title">Gutschein</span>
            <span class="vc-amount" data-preview-amount>50 €</span>
            <span class="vc-for" data-preview-for></span>
          </div>
          <div class="aside-card">
            <h2>Gut zu wissen</h2>
            <p><?= icon('calendar') ?> Gültig bis 31.12.<?= (int)date('Y') + $v['validYears'] ?></p>
            <p><?= icon('sparkle') ?> Für alle Leistungen, auch in Teilbeträgen</p>
            <p><?= icon('arrow') ?> Sofort als PDF per E-Mail</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section marble" aria-labelledby="faq-title">
      <div class="container narrow">
        <header class="section-head">
          <p class="eyebrow">Gutscheine</p>
          <h2 id="faq-title">Häufige Fragen</h2>
        </header>
        <?php faq_list($faq); ?>
      </div>
    </section>
  </main>
  <script type="module" src="/js/voucher.js?v=<?= filemtime(__DIR__ . '/../../public/js/voucher.js') ?>"></script>
<?php page_end();
