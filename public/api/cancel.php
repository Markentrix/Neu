<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

// Kund:innen-Storno über den Link aus der Bestätigungs-Mail
require_method('POST');
if (rate_limited('cancel', 20, 3600)) json_fail('Zu viele Versuche.', 429);
$in = json_in();
$id = (string)($in['id'] ?? '');
$token = (string)($in['t'] ?? '');

$st = db()->prepare("SELECT * FROM entries WHERE id = ? AND type = 'booking'");
$st->execute([$id]);
$b = $st->fetch();
if (!$b || !$b['cancel_token'] || !hash_equals($b['cancel_token'], $token)) json_fail('Termin nicht gefunden.', 404);
if ($b['status'] === 'cancelled') json_out(['ok' => true, 'alreadyCancelled' => true]);

$start = new DateTimeImmutable($b['date'] . ' ' . to_time((int)$b['start_min']));
$hours = cfg()['booking']['freeCancelHours'];
if ($start->getTimestamp() - time() < $hours * 3600) {
    json_fail("Eine Online-Stornierung ist nur bis {$hours} Stunden vor dem Termin möglich. Bitte rufen Sie uns an: " . cfg()['salon']['phoneDisplay'], 409);
}

$refunded = 0.0;
if ($b['paypal_capture'] && !$b['refunded']) {
    try {
        paypal_refund($b['paypal_capture']);
        $refunded = (float)$b['pay_amount'];
    } catch (Throwable $e) {
        error_log((string)$e);
        json_fail('Die Erstattung konnte nicht ausgelöst werden. Bitte kontaktieren Sie uns telefonisch.', 502);
    }
}
db()->prepare("UPDATE entries SET status = 'cancelled', cancelled_at = ?, cancelled_by = 'customer', refunded = ? WHERE id = ?")
    ->execute([date('c'), $refunded > 0 || $b['refunded'] ? 1 : 0, $id]);

send_mail(cfg()['local']['mail']['salonEmail'] ?? null, "Storniert: {$b['date']} " . to_time((int)$b['start_min']) . " – {$b['name']}",
    '<p>' . e($b['name']) . ' hat den Termin am ' . e(german_date($b['date'])) . ' um ' . to_time((int)$b['start_min']) . ' Uhr storniert.'
    . ($refunded ? ' Erstattet: ' . euro($refunded, true) . '.' : '') . '</p>');

json_out(['ok' => true, 'refunded' => $refunded]);
