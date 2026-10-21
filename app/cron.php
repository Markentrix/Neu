<?php
declare(strict_types=1);

// Regelmäßige Aufgaben – stündlich per Cron aufrufen:
//   docker exec aj-atelier php /var/www/site/app/cron.php
// Verschickt die Bitte um eine Google-Bewertung am Tag nach dem Termin
// (nur mit Einwilligung bei der Buchung, nur einmal, nur tagsüber).

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
require __DIR__ . '/lib.php';

$s = cfg()['salon'];
$hour = (int)date('G');
if (empty($s['reviewUrl']) || $hour < 10 || $hour >= 19) exit(0);

$st = db()->prepare("SELECT * FROM entries
    WHERE type = 'booking' AND status = 'confirmed' AND review_optin = 1 AND review_sent_at IS NULL
      AND date < ? AND date >= ? ORDER BY date LIMIT 50");
$st->execute([today(), add_days(today(), -3)]);
$mark = db()->prepare('UPDATE entries SET review_sent_at = ? WHERE id = ?');

foreach ($st->fetchAll() as $b) {
    $ok = send_mail($b['email'], "Wie war Ihr Besuch bei {$s['name']}?",
        '<p>Hallo ' . e($b['name']) . ',</p>'
        . '<p>vielen Dank für Ihren Besuch am ' . e(german_date($b['date'])) . '. Wir hoffen, Sie sind mit Ihrem neuen Look zufrieden!</p>'
        . '<p>Wenn Sie zwei Minuten Zeit haben, würden wir uns sehr über eine Bewertung bei Google freuen. Das hilft anderen bei der Suche nach einem Friseur und uns, noch besser zu werden.</p>'
        . '<p><a href="' . e($s['reviewUrl']) . '" style="display:inline-block;background:#b08a3e;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none">Jetzt bei Google bewerten</a></p>'
        . '<p>Herzliche Grüße<br>Ihr Team vom ' . e($s['name']) . '</p>'
        . '<p style="font-size:12px;color:#8a7b68">Sie erhalten diese einmalige E-Mail, weil Sie bei der Buchung zugestimmt haben. Weitere E-Mails dieser Art schicken wir Ihnen nicht.</p>');
    // Auch bei Fehlschlag markieren, damit niemand später doppelt angeschrieben wird
    $mark->execute([date('c') . ($ok ? '' : ' (fehlgeschlagen)'), $b['id']]);
    echo date('c'), " Bewertungsanfrage an Termin {$b['id']}: ", $ok ? 'gesendet' : 'fehlgeschlagen', "\n";
}
