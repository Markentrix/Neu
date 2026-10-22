<?php
declare(strict_types=1);

// Warnung per E-Mail an alertEmail (Fallback: salonEmail) – für die Skripte in deploy/.
//   php app/alert.php "Betreff" "Text"
if (PHP_SAPI !== 'cli') exit(1);
require __DIR__ . '/lib.php';

[$subject, $text] = [$argv[1] ?? 'Hinweis', $argv[2] ?? ''];
$to = cfg()['local']['alertEmail'] ?? '' ?: (cfg()['local']['mail']['salonEmail'] ?? '');
$ok = send_mail($to, '[AJ Atelier] ' . $subject, '<p>' . nl2br(e($text)) . '</p><p style="font-size:12px;color:#6e6150">Automatische Nachricht vom Server ' . e(gethostname() ?: '') . ', ' . date('d.m.Y H:i') . ' Uhr.</p>');
fwrite(STDERR, ($ok ? 'Warnung gesendet an ' : 'Warnung konnte nicht gesendet werden an ') . ($to ?: '(keine Adresse)') . "\n");
exit($ok ? 0 : 1);
