<?php
declare(strict_types=1);

// Wiederverwendbare Seitenbausteine.

function icon(string $name): string
{
    $paths = [
        'sparkle' => '<path d="M12 3c.6 4.2 2.8 6.4 7 7-4.2.6-6.4 2.8-7 7-.6-4.2-2.8-6.4-7-7 4.2-.6 6.4-2.8 7-7Z"/><path d="M19 16.5c.2 1.3.9 2 2.2 2.2-1.3.2-2 .9-2.2 2.2-.2-1.3-.9-2-2.2-2.2 1.3-.2 2-.9 2.2-2.2Z"/>',
        'scissors' => '<circle cx="6" cy="6.5" r="2.6"/><circle cx="6" cy="17.5" r="2.6"/><path d="M8.2 8 20 18M8.2 16 20 6"/>',
        'drop' => '<path d="M12 3.5s-6 6.6-6 10.6a6 6 0 0 0 12 0c0-4-6-10.6-6-10.6Z"/><path d="M9 14.5a3 3 0 0 0 3 3"/>',
        'leaf' => '<path d="M5 19c0-8 5-13 14-14-.5 9-5.5 14-14 14Z"/><path d="M5 19 13 11"/>',
        'flower' => '<circle cx="12" cy="12" r="2.2"/><path d="M12 9.8C10.5 6.5 11 4 12 3c1 1 1.5 3.5 0 6.8ZM12 14.2c1.5 3.3 1 5.8 0 6.8-1-1-1.5-3.5 0-6.8ZM9.8 12C6.5 13.5 4 13 3 12c1-1 3.5-1.5 6.8 0ZM14.2 12c3.3-1.5 5.8-1 6.8 0-1 1-3.5 1.5-6.8 0Z"/>',
        'razor' => '<path d="M4 15h9l3-3V9H4z"/><path d="M16 11h3.5a1.5 1.5 0 0 1 0 3H16"/><path d="M7 15v4M10 15v4"/>',
        'eye' => '<path d="M2.5 12S6 6 12 6s9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.6"/>',
        'pin' => '<path d="M12 21s-7-7.8-7-13a7 7 0 0 1 14 0c0 5.2-7 13-7 13Z"/><circle cx="12" cy="8" r="2.4"/>',
        'clock' => '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
        'phone' => '<path d="M6.5 3.5h3l1.5 4-2 1.5a11 11 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2 2A16 16 0 0 1 4.5 5.5a2 2 0 0 1 2-2Z"/>',
        'calendar' => '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
        'arrow' => '<path d="M5 12h14M13 6l6 6-6 6"/>',
    ];
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . ($paths[$name] ?? '') . '</svg>';
}

function price_label(array $sv): string
{
    if (!empty($sv['consult'])) return 'nach Beratung';
    return (!empty($sv['from']) ? 'ab ' : '') . euro((float)$sv['price']);
}

function duration_label(int $m): string
{
    if ($m < 60) return "{$m} Min.";
    $h = intdiv($m, 60);
    $r = $m % 60;
    return $r ? "{$h} Std. {$r} Min." : "{$h} Std.";
}

/** Niedrigster Preis einer Leistungsseite, z. B. "ab 35 €" */
function leistung_from_price(array $l): string
{
    $items = array_map(fn($id) => services()[$id], $l['services']);
    $priced = array_filter($items, fn($s) => !$s['consult']);
    $min = min(array_column($priced, 'price'));
    $fixed = count($priced) === 1 && !reset($priced)['from'];
    return ($fixed ? '' : 'ab ') . euro((float)$min);
}

function crumbs_html(array $crumbs): string
{
    $html = '<nav class="crumbs" aria-label="Brotkrumen"><ol><li><a href="/">Startseite</a></li>';
    foreach ($crumbs as $i => [$name, $href]) {
        $last = $i === array_key_last($crumbs);
        $html .= '<li>' . ($last ? '<span aria-current="page">' . e($name) . '</span>' : '<a href="' . e($href) . '">' . e($name) . '</a>') . '</li>';
    }
    return $html . '</ol></nav>';
}

function page_hero(string $eyebrow, string $title, string $lead, array $crumbs, ?string $cta = '/termin', string $ctaLabel = 'Termin buchen'): void
{
    $s = cfg()['salon']; ?>
    <section class="page-hero marble">
      <div class="container">
        <?= crumbs_html($crumbs) ?>
        <p class="eyebrow"><?= e($eyebrow) ?></p>
        <h1><?= e($title) ?></h1>
        <p class="lead"><?= $lead ?></p>
        <?php if ($cta): ?>
        <div class="hero-actions">
          <a class="btn btn-gold" href="<?= e($cta) ?>"><?= e($ctaLabel) ?></a>
          <a class="btn btn-ghost" href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a>
        </div>
        <?php endif; ?>
      </div>
    </section>
<?php
}

/** Vollständige Preisliste (alle Kategorien aus config.php) */
function price_list(string $tag = 'h3'): void
{ ?>
        <div class="price-card">
          <?php foreach (cfg()['categories'] as $cat): ?>
          <section class="price-group" aria-labelledby="pg-<?= e($cat['id']) ?>">
            <<?= $tag ?> id="pg-<?= e($cat['id']) ?>"><?= e($cat['title']) ?></<?= $tag ?>>
            <p class="price-sub"><?= e($cat['subtitle']) ?></p>
            <dl class="price-list">
              <?php $lastGroup = null; foreach ($cat['services'] as $sv):
                if (isset($sv['group']) && $sv['group'] !== $lastGroup): $lastGroup = $sv['group']; ?>
              <div class="price-row price-row-group"><dt><?= e($sv['group']) ?></dt><dd></dd></div>
              <?php endif; ?>
              <div class="price-row<?= isset($sv['group']) ? ' is-sub' : '' ?>">
                <dt><?= e($sv['name']) ?></dt>
                <dd><?= e(price_label($sv)) ?></dd>
              </div>
              <?php endforeach; ?>
            </dl>
            <?php if (!empty($cat['note'])): ?><p class="price-note"><?= e($cat['note']) ?></p><?php endif; ?>
          </section>
          <?php endforeach; ?>
        </div>
<?php
}

/** Preis-/Dauer-Tabelle einer Leistungsseite mit Direkt-Buchungslinks */
function service_price_box(array $ids): void
{ ?>
        <div class="service-box">
          <h2>Preise &amp; Dauer</h2>
          <ul class="service-rows">
            <?php foreach ($ids as $id): $sv = services()[$id]; ?>
            <li>
              <span class="sr-name"><?= e($sv['fullName']) ?><small>ca. <?= e(duration_label((int)$sv['duration'])) ?></small></span>
              <span class="sr-price"><?= e(price_label($sv)) ?></span>
              <a class="sr-book" href="/termin?leistung=<?= e($id) ?>">Buchen <?= icon('arrow') ?></a>
            </li>
            <?php endforeach; ?>
          </ul>
          <p class="hint">Alle Preise in Euro inkl. MwSt.<?= array_filter($ids, fn($id) => services()[$id]['from'] || services()[$id]['consult']) ? ' „ab“-Preise richten sich nach Aufwand und Verbrauch, Sie erhalten vorab einen Kostenvoranschlag.' : '' ?></p>
        </div>
<?php
}

function booking_data(): array
{
    $c = cfg();
    $s = $c['salon'];
    return [
        'categories' => array_map(fn($cat) => [
            'id' => $cat['id'], 'title' => $cat['title'],
            'services' => array_map(function ($sv) {
                $full = services()[$sv['id']];
                return ['id' => $sv['id'], 'name' => $full['fullName'], 'price' => $sv['price'], 'from' => $full['from'], 'consult' => $full['consult'], 'duration' => $sv['duration'], 'payNow' => online_amount($full)];
            }, $cat['services']),
        ], $c['categories']),
        'days' => bookable_days(),
        'maxServices' => $c['booking']['maxServices'],
        'paypalClientId' => paypal_enabled() ? $c['local']['paypal']['clientId'] : null,
        'hours' => $c['hours'],
        'holidays' => array_keys(holidays((int)date('Y')) + holidays((int)date('Y') + 1)),
        'salon' => ['name' => $s['name'], 'address' => "{$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}"],
    ];
}

/** Daten für Buchung und „Jetzt geöffnet“ – nur einmal pro Seite ausgeben */
function booking_data_script(): string
{
    static $done = false;
    if ($done) return '';
    $done = true;
    return '<script type="application/json" id="booking-data">' . json_encode(booking_data(), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP) . '</script>';
}

function booking_widget(): void
{
    $c = cfg();
    $s = $c['salon'];
    $tel = e($s['phone']);
    include __DIR__ . '/partials/booking-widget.php';
    echo booking_data_script();
}

function hours_table(): void
{
    $c = cfg();
    $names = [2 => 'Dienstag', 3 => 'Mittwoch', 4 => 'Donnerstag', 5 => 'Freitag', 6 => 'Samstag', 0 => 'Sonntag', 1 => 'Montag']; ?>
          <table class="hours">
            <caption class="sr-only">Öffnungszeiten</caption>
            <?php foreach ($names as $d => $n): $h = $c['hours'][$d]; ?>
            <tr data-day="<?= $d ?>"><th scope="row"><?= $n ?></th><td><?= $h ? '<time>' . e($h[0]) . '</time> – <time>' . e($h[1]) . '</time> Uhr' : 'geschlossen' ?></td></tr>
            <?php endforeach; ?>
          </table>
          <p class="open-now" data-open-now aria-live="polite"></p>
          <p class="hint">An gesetzlichen Feiertagen in Niedersachsen geschlossen.</p>
<?php
    echo booking_data_script();
}

function faq_schema(array $faq): array
{
    return [
        '@context' => 'https://schema.org',
        '@type' => 'FAQPage',
        'mainEntity' => array_map(fn($q) => ['@type' => 'Question', 'name' => $q[0], 'acceptedAnswer' => ['@type' => 'Answer', 'text' => strip_tags($q[1])]], $faq),
    ];
}

function faq_list(array $faq, bool $openFirst = false): void
{ ?>
        <div class="faq">
          <?php foreach ($faq as $i => [$q, $a]): ?>
          <details<?= $openFirst && $i === 0 ? ' open' : '' ?>><summary><?= e($q) ?></summary><p><?= e($a) ?></p></details>
          <?php endforeach; ?>
        </div>
<?php
}

/** Karten aller Leistungsseiten; $only begrenzt auf bestimmte Slugs */
function service_cards(?array $only = null, string $headingTag = 'h3'): void
{
    $all = leistungen();
    $slugs = $only ?? array_keys($all); ?>
        <div class="card-grid">
          <?php foreach ($slugs as $slug): $l = $all[$slug]; ?>
          <a class="svc-card" href="/leistungen/<?= e($slug) ?>">
            <span class="feature-icon"><?= icon($l['icon']) ?></span>
            <<?= $headingTag ?>><?= e($l['name']) ?></<?= $headingTag ?>>
            <p><?= e($l['teaser']) ?></p>
            <span class="svc-meta"><?= e(leistung_from_price($l)) ?> <span class="svc-more">Mehr erfahren <?= icon('arrow') ?></span></span>
          </a>
          <?php endforeach; ?>
        </div>
<?php
}

function cta_band(string $title = 'Lust auf einen neuen Look?', string $text = 'Freie Termine sehen Sie sofort online. Bezahlen Sie bequem per PayPal oder vor Ort.'): void
{
    $s = cfg()['salon']; ?>
    <section class="cta-band">
      <div class="container cta-inner">
        <div>
          <h2><?= e($title) ?></h2>
          <p><?= e($text) ?></p>
        </div>
        <div class="hero-actions">
          <a class="btn btn-gold" href="/termin">Termin buchen</a>
          <a class="btn btn-light" href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a>
        </div>
      </div>
    </section>
<?php
}

function nap_block(): void
{
    $s = cfg()['salon']; ?>
          <address class="nap">
            <strong><?= e($s['legalName']) ?></strong><br>
            <?= e($s['street']) ?><br>
            <?= e("{$s['zip']} {$s['city']}-{$s['district']}") ?><br>
            Telefon: <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a><br>
            Instagram: <a href="<?= e($s['instagram']) ?>" rel="noopener" target="_blank">@ajat.elier</a>
          </address>
<?php
}

function map_link(): void
{
    $s = cfg()['salon']; ?>
        <div class="map-actions">
          <a class="map-link" href="https://www.openstreetmap.org/?mlat=<?= $s['lat'] ?>&amp;mlon=<?= $s['lng'] ?>#map=17/<?= $s['lat'] ?>/<?= $s['lng'] ?>" target="_blank" rel="noopener">
            <?= icon('pin') ?>
            <span><strong>Karte öffnen</strong><small><?= e("{$s['street']} · {$s['zip']} {$s['city']}-{$s['district']}") ?></small></span>
          </a>
          <a class="btn btn-gold" href="https://www.google.com/maps/dir/?api=1&amp;destination=<?= rawurlencode("{$s['name']}, {$s['street']}, {$s['zip']} {$s['city']}") ?>" target="_blank" rel="noopener">Route planen</a>
        </div>
<?php
}
