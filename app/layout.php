<?php
declare(strict_types=1);

// Gemeinsamer Seitenrahmen (Kopf, Navigation, Fuß) für alle Seiten.

function security_headers(): void
{
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header('Permissions-Policy: camera=(), microphone=(), geolocation=()');
    header("Content-Security-Policy: default-src 'self'; script-src 'self' https://www.paypal.com https://*.paypal.com; "
        . "style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.paypal.com https://*.paypalobjects.com; "
        . "connect-src 'self' https://*.paypal.com; frame-src https://*.paypal.com; font-src 'self'; "
        . "form-action 'self'; base-uri 'self'; frame-ancestors 'self'");
}

function local_business_schema(): array
{
    $c = cfg();
    $s = $c['salon'];
    $dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    $byHours = [];
    foreach ($c['hours'] as $d => $h) {
        if ($h) $byHours[implode('-', $h)][] = $dayNames[$d];
    }
    $hours = [];
    foreach ($byHours as $span => $days) {
        [$o, $cl] = explode('-', $span);
        $hours[] = ['@type' => 'OpeningHoursSpecification', 'dayOfWeek' => $days, 'opens' => $o, 'closes' => $cl];
    }
    $catalog = [];
    foreach ($c['categories'] as $cat) {
        $offers = [];
        foreach ($cat['services'] as $sv) {
            $name = isset($sv['group']) ? "{$sv['group']} ({$sv['name']})" : $sv['name'];
            $offer = ['@type' => 'Offer', 'itemOffered' => ['@type' => 'Service', 'name' => $name], 'priceCurrency' => 'EUR'];
            if (!empty($sv['consult'])) {
                $offer['description'] = 'Preis nach Beratung';
            } elseif (!empty($sv['from'])) {
                $offer['priceSpecification'] = ['@type' => 'PriceSpecification', 'minPrice' => $sv['price'], 'priceCurrency' => 'EUR'];
            } else {
                $offer['price'] = $sv['price'];
            }
            $offers[] = $offer;
        }
        $catalog[] = ['@type' => 'OfferCatalog', 'name' => $cat['title'], 'itemListElement' => $offers];
    }
    return [
        '@context' => 'https://schema.org',
        '@type' => 'HairSalon',
        '@id' => site_url('/#salon'),
        'name' => $s['name'],
        'alternateName' => [$s['legalName'], 'AJ Atelier Wettmar', 'Friseur AJ Atelier Burgwedel'],
        'description' => 'Friseursalon in Burgwedel-Wettmar für Balayage, Babylights, Färben, Damen- und Herrenschnitte, Styling, Haarpflege sowie Augenbrauen und Wimpern. Online-Terminbuchung mit PayPal.',
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
        'openingHoursSpecification' => $hours,
        'sameAs' => [$s['instagram']],
        'hasOfferCatalog' => ['@type' => 'OfferCatalog', 'name' => 'Preisliste', 'itemListElement' => $catalog],
        'potentialAction' => [
            '@type' => 'ReserveAction',
            'target' => ['@type' => 'EntryPoint', 'urlTemplate' => site_url('/#termin'), 'inLanguage' => 'de-DE', 'actionPlatform' => ['https://schema.org/DesktopWebPlatform', 'https://schema.org/MobileWebPlatform']],
            'result' => ['@type' => 'Reservation', 'name' => 'Friseurtermin'],
        ],
    ];
}

function json_ld(array $data): string
{
    return '<script type="application/ld+json">' . json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG) . '</script>';
}

function page_start(array $o): void
{
    security_headers();
    $s = cfg()['salon'];
    $path = $o['path'] ?? '/';
    $robots = $o['robots'] ?? 'index, follow, max-image-preview:large, max-snippet:-1';
    ?>
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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
  <?= json_ld(local_business_schema()) ?>
  <?php foreach ($o['schema'] ?? [] as $extra) echo json_ld($extra), "\n"; ?>
</head>
<body class="<?= e($o['bodyClass'] ?? '') ?>">
  <a class="skip-link" href="#main">Zum Inhalt springen</a>
  <header class="site-header" data-header>
    <div class="container header-inner">
      <a class="brand" href="/" aria-label="AJ Atelier – Startseite">
        <span class="brand-mark" aria-hidden="true">AJ</span>
        <span class="brand-text">Atelier<small>Hair · Beauty</small></span>
      </a>
      <nav class="main-nav" aria-label="Hauptnavigation">
        <a href="/#leistungen">Leistungen</a>
        <a href="/#preise">Preise</a>
        <a href="/#ueber-uns">Über uns</a>
        <a href="/#kontakt">Kontakt</a>
        <a class="btn btn-gold btn-sm" href="/#termin">Termin buchen</a>
      </nav>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav" data-nav-toggle>
        <span class="sr-only">Menü</span><span></span><span></span>
      </button>
    </div>
    <nav class="mobile-nav" id="mobile-nav" aria-label="Mobile Navigation" hidden data-mobile-nav>
      <a href="/#leistungen">Leistungen</a>
      <a href="/#preise">Preise</a>
      <a href="/#ueber-uns">Über uns</a>
      <a href="/#faq">FAQ</a>
      <a href="/#kontakt">Kontakt</a>
      <a class="btn btn-gold" href="/#termin">Termin buchen</a>
    </nav>
  </header>
<?php
}

function page_end(bool $mobileCta = true): void
{
    $s = cfg()['salon'];
    ?>
  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <span class="brand-mark" aria-hidden="true">AJ</span>
        <p><strong><?= e($s['name']) ?></strong> · Friseur in <?= e("{$s['city']}-{$s['district']}") ?><br>
          <?= e($s['street']) ?> · <?= e("{$s['zip']} {$s['city']}") ?> · <a href="tel:<?= e($s['phone']) ?>"><?= e($s['phoneDisplay']) ?></a></p>
      </div>
      <p class="footer-areas">Für Kund:innen aus <?= e(implode(', ', array_slice($s['areaServed'], 0, -1))) ?> und <?= e(end($s['areaServed'])) ?>.</p>
      <nav aria-label="Rechtliches">
        <a href="/impressum.php">Impressum</a>
        <a href="/datenschutz.php">Datenschutz</a>
        <a href="<?= e($s['instagram']) ?>" rel="noopener" target="_blank">Instagram</a>
      </nav>
    </div>
    <p class="container copyright">© <?= date('Y') ?> <?= e($s['name']) ?></p>
  </footer>
<?php if ($mobileCta): ?>
  <div class="mobile-cta">
    <a class="btn btn-ghost" href="tel:<?= e($s['phone']) ?>">Anrufen</a>
    <a class="btn btn-gold" href="/#termin">Termin buchen</a>
  </div>
<?php endif; ?>
  <script type="module" src="/js/main.js?v=<?= filemtime(__DIR__ . '/../public/js/main.js') ?>"></script>
</body>
</html>
<?php
}
