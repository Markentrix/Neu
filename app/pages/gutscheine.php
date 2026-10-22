<?php
$c = cfg();
$v = $c['vouchers'];
$crumbs = [['Gutscheine', '/gutscheine']];
$faq = [
    ['Wie lange ist ein Gutschein gültig?', 'Gutscheine sind drei Jahre gültig, gerechnet ab dem Ende des Jahres, in dem sie gekauft wurden. Ein im Mai gekaufter Gutschein gilt also bis zum 31. Dezember drei Jahre später.'],
    ['Wofür kann der Gutschein eingelöst werden?', 'Für alle Leistungen im AJ Atelier, auch in Teilbeträgen. Der Restbetrag bleibt auf dem Gutschein erhalten.'],
    ['Wie läuft die Bestellung ab?', 'Sie wählen Betrag und Widmung und senden die Anfrage ab. Per E-Mail erhalten Sie den Link zur Zahlung mit PayPal. Sobald die Zahlung da ist, bekommen Sie den Gutschein mit persönlichem Code zum Ausdrucken oder Weiterleiten.'],
    ['Kann ich auch im Salon einen Gutschein kaufen?', 'Ja, natürlich. Sprechen Sie uns einfach bei Ihrem nächsten Besuch an, dort zahlen Sie bar oder mit Karte.'],
];
page_start([
    'title' => 'Gutschein verschenken | Friseur AJ Atelier Wettmar',
    'description' => 'Friseur-Gutschein von AJ Atelier in Burgwedel-Wettmar: Betrag wählen, online anfragen, bequem per PayPal bezahlen und per E-Mail erhalten. 3 Jahre gültig.',
    'path' => '/gutscheine',
    'crumbs' => $crumbs,
    'schema' => [faq_schema($faq), [
        '@context' => 'https://schema.org',
        '@type' => 'Product',
        'name' => 'Gutschein AJ Atelier',
        'description' => 'Wertgutschein für alle Leistungen bei AJ Atelier in Burgwedel-Wettmar, per E-Mail.',
        'brand' => ['@type' => 'Brand', 'name' => $c['salon']['name']],
        'offers' => ['@type' => 'AggregateOffer', 'priceCurrency' => 'EUR', 'lowPrice' => $v['min'], 'highPrice' => $v['max'], 'availability' => 'https://schema.org/InStock', 'url' => site_url('/gutscheine')],
    ]],
]);
?>
  <main id="main">
    <?php page_hero('Gutscheine', 'Gutschein verschenken', 'Ein Friseur-Gutschein für Balayage, einen neuen Schnitt oder eine Pflege-Auszeit. Betrag wählen, anfragen und bequem per PayPal bezahlen.', $crumbs, null); ?>

    <section class="section">
      <div class="container content-grid">
        <div class="voucher-shop">
          <?= fallback_contact('Die Anfrage konnte gerade nicht gesendet werden. Gutscheine bekommen Sie auch telefonisch oder direkt im Salon.') ?>
          <form class="form-grid voucher-form" method="post" data-anfrage="gutschein" data-min="<?= (int)$v['min'] ?>" data-max="<?= (int)$v['max'] ?>" novalidate>
            <fieldset class="full amount-field">
              <legend>Betrag wählen</legend>
              <div class="amount-chips">
                <?php foreach ($v['amounts'] as $i => $a): ?>
                <label class="chip"><input type="radio" name="betrag_wahl" value="<?= (int)$a ?>"<?= $i === 1 ? ' checked' : '' ?>><span><?= (int)$a ?> €</span></label>
                <?php endforeach; ?>
                <label class="chip chip-custom"><input type="radio" name="betrag_wahl" value="custom"><span>Eigener Betrag</span></label>
              </div>
              <label class="custom-amount" data-custom-amount hidden>Betrag in Euro (<?= (int)$v['min'] ?>–<?= (int)$v['max'] ?>)
                <input id="v-custom" name="betrag_eigen" type="number" inputmode="numeric" min="<?= (int)$v['min'] ?>" max="<?= (int)$v['max'] ?>" step="1">
                <small class="field-error" data-error-for="betrag_eigen"></small>
              </label>
            </fieldset>
            <label>Für (optional)<input id="v-recipient" name="empfaenger" maxlength="60" placeholder="z. B. Maria"></label>
            <label class="full">Persönliche Widmung (optional, max. 200 Zeichen)<textarea id="v-message" name="widmung" rows="3" maxlength="200" placeholder="Alles Liebe zum Geburtstag!"></textarea></label>
            <label>Ihr Name*<input id="v-buyer" name="name" autocomplete="name" required minlength="2" maxlength="80"><small class="field-error" data-error-for="name"></small></label>
            <label>Ihre E-Mail*<input id="v-email" name="email" type="email" autocomplete="email" required maxlength="254"><small class="field-error" data-error-for="email"></small></label>
            <label class="full">Telefon <small>(optional, für Rückfragen)</small><input id="v-phone" name="telefon" type="tel" autocomplete="tel" maxlength="30"><small class="field-error" data-error-for="telefon"></small></label>
            <?= form_consent('zur Ausstellung und Zusendung des Gutscheins') ?>
            <small class="field-error full" data-error-for="einwilligung"></small>
            <p class="form-error full" data-form-error role="alert" hidden></p>
            <div class="full">
              <button class="btn btn-gold" type="submit">Gutschein anfragen</button>
              <p class="hint">Sie zahlen erst, wenn Sie den PayPal-Link von uns per E-Mail erhalten haben.</p>
            </div>
          </form>
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
            <p><?= icon('calendar') ?> Drei Jahre gültig, bis zum Jahresende</p>
            <p><?= icon('sparkle') ?> Für alle Leistungen, auch in Teilbeträgen</p>
            <p><?= icon('arrow') ?> Bezahlung per PayPal, Gutschein per E-Mail</p>
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
<?php page_end(true, ['formulare.js']);
