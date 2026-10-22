<?php
declare(strict_types=1);

// Regelmäßige Aufgaben – stündlich per Cron aufrufen:
//   docker exec aj-atelier php /var/www/site/app/cron.php
//
// 1. Terminerinnerung ca. 24 Std. vorher (gehört zum Termin, keine Einwilligung nötig)
// 2. Folgetermin-Erinnerung („Zeit für den Ansatz?“) – nur mit Einwilligung, einmalig
// 3. Bitte um Google-Bewertung am Tag nach dem Termin – nur mit Einwilligung, einmalig
// Verschickt wird nur tagsüber. Jede Mail wird genau einmal versucht.

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
require __DIR__ . '/lib.php';

// Lebenszeichen für die Überwachung (/api/health.php)
file_put_contents(dirname(cfg()['local']['databasePath'] ?? __DIR__ . '/data/x') . '/cron-heartbeat', (string)time());

$c = cfg();
$s = $c['salon'];
$hour = (int)date('G');
$anyHour = getenv('AJ_IGNORE_HOURS') === '1'; // nur für die Testsuite
$daytime = fn(int $from, int $to) => $anyHour || ($hour >= $from && $hour < $to);
$log = fn(string $msg) => print(date('c') . " {$msg}\n");
$sig = '<p>' . e("{$s['name']} · {$s['street']} · {$s['zip']} {$s['city']}-{$s['district']} · Tel. {$s['phoneDisplay']}") . '</p>';

function service_list(array $b): string
{
    return implode(', ', array_column(json_decode($b['services'], true) ?: [], 'name'));
}

// ---------- 1. Terminerinnerung ----------
if ($daytime(8, 20)) {
    $st = db()->prepare("SELECT * FROM entries WHERE type = 'booking' AND status = 'confirmed' AND reminder_sent_at IS NULL
        AND date >= ? AND date <= ?");
    $st->execute([today(), add_days(today(), 2)]);
    $mark = db()->prepare('UPDATE entries SET reminder_sent_at = ? WHERE id = ?');
    foreach ($st->fetchAll() as $b) {
        $start = strtotime($b['date'] . ' ' . to_time((int)$b['start_min']));
        $left = $start - time();
        if ($left > ($c['booking']['reminderHours'] + 4) * 3600 || $left < 2 * 3600) continue;
        if (time() - strtotime($b['created_at']) < 6 * 3600) continue; // gerade erst gebucht – Bestätigung reicht
        $time = to_time((int)$b['start_min']);
        $cancel = site_url('/termin-stornieren?id=' . rawurlencode($b['id']) . '&t=' . $b['cancel_token']);
        $ok = send_mail($b['email'], "Erinnerung: Ihr Termin bei {$s['name']} am " . german_date($b['date']) . ", {$time} Uhr",
            '<p>Hallo ' . e($b['name']) . ',</p>'
            . '<p>wir freuen uns auf Sie: <strong>' . e(german_date($b['date'])) . ' um ' . $time . ' Uhr</strong><br>' . e(service_list($b)) . '</p>'
            . '<p>Adresse: ' . e("{$s['street']}, {$s['zip']} {$s['city']}-{$s['district']}") . '</p>'
            . '<p>Sie sind verhindert? Dann sagen Sie bitte kurz Bescheid, damit wir den Termin weitergeben können: telefonisch unter '
            . e($s['phoneDisplay']) . ($left > $c['booking']['freeCancelHours'] * 3600 ? ' oder <a href="' . e($cancel) . '">online stornieren</a>' : '') . '.</p>'
            . $sig);
        $mark->execute([date('c') . ($ok ? '' : ' (fehlgeschlagen)'), $b['id']]);
        $log("Terminerinnerung {$b['id']}: " . ($ok ? 'gesendet' : 'fehlgeschlagen'));
    }
}

// ---------- 2. Folgetermin-Erinnerung ----------
if ($daytime(9, 19)) {
    $st = db()->prepare("SELECT * FROM entries WHERE type = 'booking' AND status = 'confirmed' AND followup_optin = 1
        AND followup_sent_at IS NULL AND date < ? ORDER BY date");
    $st->execute([today()]);
    $mark = db()->prepare('UPDATE entries SET followup_sent_at = ? WHERE id = ?');
    $later = db()->prepare("SELECT COUNT(*) FROM entries WHERE type = 'booking' AND status = 'confirmed' AND lower(email) = lower(?) AND date > ?");
    foreach ($st->fetchAll() as $b) {
        // Leistung mit dem kürzesten Abstand bestimmt den Zeitpunkt
        $best = null;
        foreach (json_decode($b['services'], true) ?: [] as $sv) {
            $weeks = services()[$sv['id']]['rebookWeeks'] ?? null;
            if ($weeks && (!$best || $weeks < $best[1])) $best = [$sv['id'], (int)$weeks];
        }
        if (!$best) {
            $mark->execute(['entfällt (keine passende Leistung)', $b['id']]);
            continue;
        }
        $due = add_days($b['date'], $best[1] * 7);
        if ($due > today()) continue;
        $later->execute([$b['email'], $b['date']]);
        if ((int)$later->fetchColumn() > 0) {
            $mark->execute(['entfällt (neuer Termin vorhanden)', $b['id']]);
            continue;
        }
        if ($due < add_days(today(), -14)) {
            $mark->execute(['entfällt (zu spät)', $b['id']]);
            continue;
        }
        $sv = services()[$best[0]];
        $ok = send_mail($b['email'], "Zeit für Ihren nächsten Termin bei {$s['name']}?",
            '<p>Hallo ' . e($b['name']) . ',</p>'
            . '<p>Ihr letzter Besuch bei uns (' . e($sv['fullName']) . ') ist jetzt ' . $best[1] . ' Wochen her. Wenn Sie mögen, ist jetzt ein guter Zeitpunkt für den nächsten Termin.</p>'
            . '<p><a href="' . e(site_url('/termin?leistung=' . $best[0])) . '" style="display:inline-block;background:#8a6727;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none">Termin online buchen</a></p>'
            . $sig
            . '<p style="font-size:12px;color:#6e6150">Sie erhalten diese einmalige E-Mail, weil Sie bei Ihrer Buchung zugestimmt haben. Weitere Erinnerungen schicken wir nur, wenn Sie bei einer neuen Buchung wieder zustimmen.</p>');
        $mark->execute([date('c') . ($ok ? '' : ' (fehlgeschlagen)'), $b['id']]);
        $log("Folgetermin-Erinnerung {$b['id']}: " . ($ok ? 'gesendet' : 'fehlgeschlagen'));
    }
}

// ---------- 3. Bitte um Google-Bewertung ----------
if (!empty($s['reviewUrl']) && $daytime(10, 19)) {
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
            . '<p><a href="' . e($s['reviewUrl']) . '" style="display:inline-block;background:#8a6727;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none">Jetzt bei Google bewerten</a></p>'
            . '<p>Herzliche Grüße<br>Ihr Team vom ' . e($s['name']) . '</p>'
            . '<p style="font-size:12px;color:#6e6150">Sie erhalten diese einmalige E-Mail, weil Sie bei der Buchung zugestimmt haben. Weitere E-Mails dieser Art schicken wir Ihnen nicht.</p>');
        // Auch bei Fehlschlag markieren, damit niemand später doppelt angeschrieben wird
        $mark->execute([date('c') . ($ok ? '' : ' (fehlgeschlagen)'), $b['id']]);
        $log("Bewertungsanfrage {$b['id']}: " . ($ok ? 'gesendet' : 'fehlgeschlagen'));
    }
}
