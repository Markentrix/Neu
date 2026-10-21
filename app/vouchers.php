<?php
declare(strict_types=1);

// Online-Gutscheine: Code, Gültigkeit, PDF und Versand.

function voucher_code(): string
{
    $alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // ohne 0/O, 1/I – gut abzulesen
    $part = fn() => implode('', array_map(fn() => $alphabet[random_int(0, strlen($alphabet) - 1)], range(1, 4)));
    return 'AJ-' . $part() . '-' . $part();
}

/** Gültig bis Jahresende + 3 Jahre (regelmäßige Verjährung nach §§ 195, 199 BGB) */
function voucher_valid_until(): string
{
    return ((int)date('Y') + (int)cfg()['vouchers']['validYears']) . '-12-31';
}

function voucher_amount_ok($amount): ?int
{
    $v = cfg()['vouchers'];
    if (!is_numeric($amount) || (int)$amount != $amount) return null;
    $a = (int)$amount;
    return $a >= $v['min'] && $a <= $v['max'] ? $a : null;
}

function voucher_find(string $code): ?array
{
    $st = db()->prepare('SELECT * FROM vouchers WHERE code = ?');
    $st->execute([strtoupper(trim($code))]);
    return $st->fetch() ?: null;
}

// ---------- PDF (A5 quer, Standardschriften, ohne Bibliothek) ----------

function pdf_text(string $s): string
{
    $s = mb_convert_encoding($s, 'Windows-1252', 'UTF-8');
    return '(' . strtr($s, ['\\' => '\\\\', '(' => '\\(', ')' => '\\)', "\r" => '', "\n" => ' ']) . ')';
}

function pdf_wrap(string $text, int $maxChars): array
{
    $lines = [];
    $line = '';
    foreach (preg_split('/\s+/u', trim($text)) as $word) {
        if ($line !== '' && mb_strlen($line . ' ' . $word) > $maxChars) {
            $lines[] = $line;
            $line = $word;
        } else {
            $line = $line === '' ? $word : "{$line} {$word}";
        }
    }
    if ($line !== '') $lines[] = $line;
    return $lines;
}

function voucher_pdf(array $v): string
{
    $s = cfg()['salon'];
    $gold = '0.690 0.541 0.243';
    $ink = '0.173 0.149 0.125';
    $muted = '0.478 0.416 0.333';
    $t = function (string $font, float $size, float $x, float $y, string $text, string $color, float $spacing = 0) {
        return "BT /{$font} {$size} Tf {$color} rg {$spacing} Tc {$x} {$y} Td " . pdf_text($text) . " Tj ET\n";
    };

    $c = "0.965 0.945 0.914 rg 0 0 595.28 419.53 re f\n";
    $c .= "{$gold} RG 1.2 w 18 18 559.28 383.53 re S 0.4 w 24 24 547.28 371.53 re S\n";
    $c .= "{$gold} RG 0.6 w 360 70 m 360 350 l S\n";
    $c .= $t('F1', 58, 46, 318, 'AJ', $gold);
    $c .= $t('F1', 15, 49, 296, 'ATELIER', $ink, 5);
    $c .= $t('F3', 6.5, 50, 283, 'HAIR · BEAUTY', $muted, 2.2);
    $c .= $t('F1', 30, 46, 226, 'GUTSCHEIN', $ink, 4);
    $c .= $t('F1', 48, 46, 168, number_format((float)$v['amount'], 0, ',', '.') . ' €', $gold);
    $y = 140;
    if (!empty($v['recipient'])) {
        $c .= $t('F2', 16, 48, $y, 'für ' . $v['recipient'], $ink);
        $y -= 24;
    }
    foreach (array_slice(pdf_wrap((string)($v['message'] ?? ''), 52), 0, 4) as $line) {
        $c .= $t('F2', 11, 48, $y, $line, $muted);
        $y -= 15;
    }
    $c .= $t('F3', 7.5, 384, 300, 'GUTSCHEINCODE', $muted, 1.5);
    $c .= $t('F4', 17, 384, 278, $v['code'], $ink, 0.5);
    $c .= $t('F3', 9, 384, 250, 'Gültig bis ' . date('d.m.Y', strtotime($v['valid_until'])), $ink);
    $c .= $t('F3', 9, 384, 236, 'Einlösbar für alle Leistungen', $ink);
    $c .= $t('F3', 9, 384, 222, 'im AJ Atelier, auch in Teilbeträgen.', $ink);
    $c .= $t('F3', 8, 384, 190, 'Termin buchen:', $muted);
    $c .= $t('F3', 9, 384, 177, preg_replace('#^https?://#', '', site_url('/termin')), $ink);
    $c .= $t('F3', 8, 384, 160, 'oder telefonisch ' . $s['phoneDisplay'], $muted);
    $c .= $t('F3', 7.5, 48, 40, "{$s['legalName']} · {$s['street']} · {$s['zip']} {$s['city']}-{$s['district']}", $muted);
    $c .= $t('F3', 7, 48, 30, 'Keine Barauszahlung. Bei Verlust kein Ersatz ohne Nachweis des Codes.', $muted);

    $objs = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 419.53] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R /F4 8 0 R >> >> >>',
        '<< /Length ' . strlen($c) . " >>\nstream\n{$c}endstream",
    ];
    foreach (['Times-Roman', 'Times-Italic', 'Helvetica', 'Helvetica-Bold'] as $font) {
        $objs[] = "<< /Type /Font /Subtype /Type1 /BaseFont /{$font} /Encoding /WinAnsiEncoding >>";
    }
    $objs[] = '<< /Title ' . pdf_text('Gutschein ' . $v['code']) . ' /Author ' . pdf_text($s['name']) . ' >>';

    $pdf = "%PDF-1.4\n%\xE2\xE3\xCF\xD3\n";
    $offsets = [];
    foreach ($objs as $i => $o) {
        $offsets[] = strlen($pdf);
        $pdf .= ($i + 1) . " 0 obj\n{$o}\nendobj\n";
    }
    $xref = strlen($pdf);
    $pdf .= "xref\n0 " . (count($objs) + 1) . "\n0000000000 65535 f \n";
    foreach ($offsets as $o) $pdf .= sprintf("%010d 00000 n \n", $o);
    $pdf .= 'trailer << /Size ' . (count($objs) + 1) . ' /Root 1 0 R /Info ' . count($objs) . " 0 R >>\nstartxref\n{$xref}\n%%EOF\n";
    return $pdf;
}

function voucher_send(array $v, bool $toSalon = true): bool
{
    $s = cfg()['salon'];
    $pdf = voucher_pdf($v);
    $dl = site_url('/gutschein-pdf?c=' . rawurlencode($v['code']) . '&t=' . $v['dl_token']);
    $amount = euro((float)$v['amount']);
    $ok = send_mail($v['buyer_email'], "Ihr Gutschein über {$amount} – {$s['name']}",
        '<p>Hallo ' . e($v['buyer_name']) . ',</p><p>vielen Dank für Ihren Gutscheinkauf! Im Anhang finden Sie den Gutschein über <strong>' . e($amount) . '</strong> als PDF zum Ausdrucken oder Weiterleiten.</p>'
        . '<p>Gutscheincode: <strong>' . e($v['code']) . '</strong><br>Gültig bis ' . e(date('d.m.Y', strtotime($v['valid_until']))) . '</p>'
        . '<p>Den Gutschein können Sie jederzeit erneut herunterladen: <a href="' . e($dl) . '">Gutschein als PDF</a></p>'
        . '<p>' . e("{$s['name']} · {$s['street']} · {$s['zip']} {$s['city']}-{$s['district']} · Tel. {$s['phoneDisplay']}") . '</p>',
        null, [["Gutschein-{$v['code']}.pdf", 'application/pdf', $pdf]]);
    if ($toSalon) {
        send_mail(cfg()['local']['mail']['salonEmail'] ?? null, "Gutschein verkauft: {$amount} ({$v['code']})",
            '<p>' . e($v['buyer_name']) . ' (' . e($v['buyer_email']) . ') hat einen Gutschein über <strong>' . e($amount) . '</strong> gekauft.</p>'
            . '<p>Code: ' . e($v['code']) . ($v['recipient'] ? '<br>Für: ' . e($v['recipient']) : '') . '</p>', $v['buyer_email']);
    }
    return $ok;
}
