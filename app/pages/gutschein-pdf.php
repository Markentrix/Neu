<?php
// Gutschein-PDF erneut herunterladen (Link aus der Kauf-Mail)
require_once __DIR__ . '/../vouchers.php';
$v = voucher_find((string)($_GET['c'] ?? ''));
if (!$v || !hash_equals($v['dl_token'], (string)($_GET['t'] ?? ''))) {
    $params = [];
    require __DIR__ . '/404.php';
    return;
}
header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="Gutschein-' . $v['code'] . '.pdf"');
header('X-Robots-Tag: noindex');
header('Cache-Control: private, no-store');
echo voucher_pdf($v);
