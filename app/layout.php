<?php
declare(strict_types=1);

// Gemeinsamer Seitenrahmen (Kopf, Navigation, Fuß) und strukturierte Daten für alle Seiten.

/** CSP ohne frame-ancestors (gilt auch als <meta> in den statischen Seiten) */
function csp_policy(): string
{
    return "default-src 'self'; script-src 'self' https://www.paypal.com https://*.paypal.com; "
        . "style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.paypal.com https://*.paypalobjects.com; "
        . "connect-src 'self' https://*.paypal.com; frame-src https://*.paypal.com; font-src 'self'; "
        . "form-action 'self'; base-uri 'self'";
}

function security_headers(): void
{
    if (headers_sent()) return;
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header('Permissions-Policy: camera=(), microphone=(), geolocation=()');
    header('Content-Security-Policy: ' . csp_policy() . "; frame-ancestors 'self'");
}

function opening_hours_schema(): array
{
    $dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    $byHours = [];
    foreach (cfg()['hours'] as $d => $h) {
        if ($h) $byHours[implode('-', $h)][] = $dayNames[$d];
    }
    $out = [];
    foreach ($byHours as $span => $days) {
        [$o, $cl] = explode('-', $span);
        $out[] = ['@type' => 'OpeningHoursSpecification', 'dayOfWeek' => $days, 'opens' => $o, 'closes' => $cl];
    }
    return $out;
}

function offer_schema(array $sv): array
{
    $offer = ['@type' => 'Offer', 'itemOffered' => ['@type' => 'Service', 'name' => $sv['fullName'] ?? $sv['name']], 'priceCurrency' => 'EUR'];
    if (!empty($sv['consult'])) {
        $offer['description'] = 'Preis nach Beratung';
    } elseif (!empty($sv['from'])) {
        $offer['priceSpecification'] = ['@type' => 'PriceSpecification', 'minPrice' => $sv['price'], 'priceCurrency' => 'EUR'];
    } else {
        $offer['price'] = $sv['price'];
    }
    return $offer;
}

function local_business_schema(): array
{
    $c = cfg();
    $s = $c['salon'];
    $catalog = [];
    foreach ($c['categories'] as $cat) {
        $offers = array_map(fn($sv) => offer_schema(services()[$sv['id']]), $cat['services']);
        $catalog[] = ['@type' => 'OfferCatalog', 'name' => $cat['title'], 'itemListElement' => $offers];
    }
    return [
        '@context' => 'https://schema.org',
        '@type' => 'HairSalon',
        '@id' => site_url('/#salon'),
        'name' => $s['name'],
        'alternateName' => [$s['legalName'], 'AJ Atelier Wettmar', 'Friseur AJ Atelier Burgwedel'],
        'description' => 'Friseursalon in Burgwedel-Wettmar für Balayage, Babylights, Färben, Damen- und Herrenschnitte, Hochsteckfrisuren, Haarpflege sowie Augenbrauen und Wimpern. Online-Terminbuchung mit PayPal.',
        'url' => site_url('/'),
        'logo' => site_url('/img/logo.png'),
        'image' => site_url('/img/og-image.png'),
        'telephone' => $s['phone'],
        'priceRange' => $s['priceRange'],
        'currenciesAccepted' => 'EUR',
        'paymentAccepted' => 'Bargeld, EC-Karte, PayPal',
        'address' => [
            '@type' => 'PostalAddress',
            'streetAddress' => $s['street'],
            'postalCode' => $s['zip'],
            'addressLocality' => "{$s['city']}-{$s['district']}",
            'addressRegion' => $s['region'],
            'addressCountry' => 'DE',
        ],
        'geo' => ['@type' => 'GeoCoordinates', 'latitude' => $s['lat'], 'longitude' => $s['lng']],
        'hasMap' => "https://www.google.com/maps/search/?api=1&query={$s['lat']},{$s['lng']}",
        'areaServed' => array_map(fn($a) => ['@type' => 'Place', 'name' => $a], $s['areaServed']),
        'openingHoursSpecification' => opening_hours_schema(),
        'sameAs' => [$s['instagram']],
        'hasOfferCatalog' => ['@type' => 'OfferCatalog', 'name' => 'Preisliste', 'itemListElement' => $catalog],
        'potentialAction' => [
            '@type' => 'ReserveAction',
            'target' => ['@type' => 'EntryPoint', 'urlTemplate' => site_url('/termin'), 'inLanguage' => 'de-DE', 'actionPlatform' => ['https://schema.org/DesktopWebPlatform', 'https://schema.org/MobileWebPlatform']],
            'result' => ['@type' => 'Reservation', 'name' => 'Friseurtermin'],
        ],
    ];
}

function website_schema(): array
{
    return [
        '@context' => 'https://schema.org',
        '@type' => 'WebSite',
        '@id' => site_url('/#website'),
        'url' => site_url('/'),
        'name' => cfg()['salon']['name'],
        'inLanguage' => 'de-DE',
        'publisher' => ['@id' => site_url('/#salon')],
    ];
}

/** $crumbs = [['Leistungen', '/leistungen'], ['Balayage', '/leistungen/balayage']] – Startseite wird ergänzt. */
function breadcrumb_schema(array $crumbs): array
{
    $items = array_merge([['Startseite', '/']], $crumbs);
    return [
        '@context' => 'https://schema.org',
        '@type' => 'BreadcrumbList',
        'itemListElement' => array_map(fn($c, $i) => ['@type' => 'ListItem', 'position' => $i + 1, 'name' => $c[0], 'item' => site_url($c[1])], $items, array_keys($items)),
    ];
}

function json_ld(array $data): string
{
    return '<script type="application/ld+json">' . json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG) . '</script>';
}

function nav_link(string $href, string $label, string $current, string $class = ''): string
{
    $active = $href === $current || ($href !== '/' && str_starts_with($current, $href . '/'));
    return '<a href="' . e($href) . '"' . ($class ? ' class="' . e($class) . '"' : '') . ($active ? ' aria-current="page"' : '') . '>' . e($label) . '</a>';
}

function page_start(array $o): void
{
    security_headers();
    $s = cfg()['salon'];
    $path = $o['path'] ?? '/';
    $robots = $o['robots'] ?? 'index, follow, max-image-preview:large, max-snippet:-1';
    $schema = [local_business_schema()];
    if ($path === '/') $schema[] = website_schema();
    if (!empty($o['crumbs'])) $schema[] = breadcrumb_schema($o['crumbs']);
    $schema = array_merge($schema, $o['schema'] ?? []);
    ?>
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta http-equiv="Content-Security-Policy" content="<?= e(csp_policy()) ?>">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <title><?= e($o['title']) ?></title>
  <meta name="description" content="<?= e($o['description']) ?>">
  <link rel="canonical" href="<?= e(site_url($path)) ?>">
  <meta name="robots" content="<?= e($robots) ?>">
  <meta name="theme-color" content="#f6f1e9">
  <meta name="geo.region" content="DE-NI">
  <meta name="geo.placename" content="<?= e("{$s['city']}-{$s['district']}") ?>">
  <meta name="geo.position" content="<?= $s['lat'] ?>;<?= $s['lng'] ?>">
  <meta name="ICBM" content="<?= $s['lat'] ?>, <?= $s['lng'] ?>">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="de_DE">
  <meta property="og:site_name" content="<?= e($s['name']) ?>">
  <meta property="og:title" content="<?= e($o['ogTitle'] ?? $o['title']) ?>">
  <meta property="og:description" content="<?= e($o['description']) ?>">
  <meta property="og:url" content="<?= e(site_url($path)) ?>">
  <meta property="og:image" content="<?= e(site_url('/img/og-image.png')) ?>">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="preload" href="/fonts/cormorant-garamond-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/fonts/jost-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/css/styles.css?v=<?= filemtime(__DIR__ . '/../public/css/styles.css') ?>">
  <?php foreach ($schema as $sc) echo json_ld($sc), "\n  "; ?>

</head>
<body class="<?= e($o['bodyClass'] ?? '') ?>">
  <a class="skip-link" href="#main">Zum Inhalt springen</a>
  <header class="site-header" data-header>
    <div class="container header-inner">
      <a class="brand" href="/">
        <span class="brand-mark">AJ</span>
        <span class="brand-text">Atelier<small>Hair · Beauty</small></span>
      </a>
      <nav class="main-nav" aria-label="Hauptnavigation">
        <div class="nav-drop">
          <?= nav_link('/leistungen', 'Leistungen', $path) ?>
          <div class="nav-drop-menu">
            <?php foreach (leistungen() as $slug => $l): ?>
            <?= nav_link("/leistungen/{$slug}", $l['name'], $path) ?>
            <?php endforeach; ?>
          </div>
        </div>
        <?= nav_link('/preise', 'Preise', $path) ?>
        <?= nav_link('/gutscheine', 'Gutscheine', $path) ?>
        <?= nav_link('/ueber-uns', 'Über uns', $path) ?>
        <?= nav_link('/kontakt', 'Kontakt', $path) ?>
        <?= nav_link('/termin', 'Termin buchen', $path, 'btn btn-gold btn-sm') ?>
      </nav>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav" data-nav-toggle>
        <span class="sr-only">Menü</span><span></span><span></span>
      </button>
    </div>
    <nav class="mobile-nav" id="mobile-nav" aria-label="Mobile Navigation" hidden data-mobile-nav>
      <?= nav_link('/leistungen', 'Leistungen', $path) ?>
      <div class="mobile-sub">
        <?php foreach (leistungen() as $slug => $l): ?>
        <?= nav_link("/leistungen/{$slug}", $l['name'], $path) ?>
        <?php endforeach; ?>
      </div>
      <?= nav_link('/preise', 'Preise', $path) ?>
      <?= nav_link('/gutscheine', 'Gutscheine', $path) ?>
      <?= nav_link('/ueber-uns', 'Über uns', $path) ?>
      <?= nav_link('/ratgeber', 'Ratgeber', $path) ?>
      <?= nav_link('/faq', 'Häufige Fragen', $path) ?>
      <?= nav_link('/kontakt', 'Kontakt & Anfahrt', $path) ?>
      <a class="btn btn-gold" href="/termin">Termin buchen</a>
    </nav>
  </header>
<?php
}

function page_end(bool $mobileCta = true): void
{
    $s = cfg()['salon'];
    $c = cfg();
    $dayShort = [2 => 'Di', 3 => 'Mi', 4 => 'Do', 5 => 'Fr', 6 => 'Sa'];
    ?>
  <footer class="site-footer">
    <div class="container footer-grid">
      <div class="footer-brand">
        <a class="brand" href="/">
          <span class="brand-mark">AJ</span>
          <span class="brand-text">Atelier<small>Hair · Beauty</small></span>
        </a>
        <address>
          <?= e($s['street']) ?><br><?= e("{$s['zip']} {$s['city']}-{$s['district']}") ?><br>
          <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a>
        </address>
        <p class="footer-hours">Di–Fr <?= e($c['hours'][2][0]) ?>–<?= e($c['hours'][2][1]) ?> Uhr · Sa <?= e($c['hours'][6][0]) ?>–<?= e($c['hours'][6][1]) ?> Uhr</p>
      </div>
      <nav aria-label="Leistungen">
        <h2>Leistungen</h2>
        <?php foreach (leistungen() as $slug => $l): ?>
        <a href="/leistungen/<?= e($slug) ?>"><?= e($l['name']) ?></a>
        <?php endforeach; ?>
      </nav>
      <nav aria-label="Salon">
        <h2>Salon</h2>
        <a href="/termin">Termin buchen</a>
        <a href="/preise">Preise</a>
        <a href="/gutscheine">Gutscheine</a>
        <a href="/ueber-uns">Über uns</a>
        <a href="/ratgeber">Ratgeber</a>
        <a href="/faq">Häufige Fragen</a>
        <a href="/kontakt">Kontakt &amp; Anfahrt</a>
        <a href="<?= e($s['instagram']) ?>" rel="noopener" target="_blank">Instagram</a>
      </nav>
      <nav aria-label="Einzugsgebiet">
        <h2>Friseur für</h2>
        <?php foreach (orte() as $slug => $o): ?>
        <a href="/friseur-<?= e($slug) ?>"><?= e($o['name']) ?></a>
        <?php endforeach; ?>
      </nav>
    </div>
    <div class="container footer-bottom">
      <p>© <?= date('Y') ?> <?= e($s['legalName']) ?> · Friseur in <?= e("{$s['city']}-{$s['district']}") ?></p>
      <nav aria-label="Rechtliches">
        <a href="/impressum">Impressum</a>
        <a href="/datenschutz">Datenschutz</a>
      </nav>
    </div>
  </footer>
<?php if ($mobileCta): ?>
  <div class="mobile-cta">
    <a class="btn btn-ghost" href="tel:<?= e($s['phone']) ?>">Anrufen</a>
    <a class="btn btn-gold" href="/termin">Termin buchen</a>
  </div>
<?php endif; ?>
  <script defer src="/js/main.js?v=<?= filemtime(__DIR__ . '/../public/js/main.js') ?>"></script>
</body>
</html>
<?php
}
