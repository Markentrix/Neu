<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

// Kontaktformular: Nachricht per E-Mail an den Salon
require_method('POST');
$in = json_in();
if (!empty($in['website'])) json_out(['ok' => true]); // Honeypot
if (rate_limited('contact', 5, 3600)) json_fail('Zu viele Nachrichten. Bitte rufen Sie uns an.', 429);

$name = clean_text($in['name'] ?? '', 80);
$email = mb_strtolower(clean_text($in['email'] ?? '', 254));
$phone = clean_text($in['phone'] ?? '', 25);
$message = mb_substr(trim(preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', (string)($in['message'] ?? '')) ?? ''), 0, 2000);

if (mb_strlen($name) < 2) json_fail('Bitte geben Sie Ihren Namen an.');
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) json_fail('Bitte geben Sie eine gültige E-Mail-Adresse an.');
if ($phone !== '' && !preg_match('/^[+()\d\s\/-]{6,25}$/', $phone)) json_fail('Bitte prüfen Sie die Telefonnummer.');
if (mb_strlen($message) < 10) json_fail('Bitte schreiben Sie uns eine kurze Nachricht.');
if (($in['consent'] ?? false) !== true) json_fail('Bitte stimmen Sie der Datenverarbeitung zu.');

$to = cfg()['local']['mail']['salonEmail'] ?? '';
if (!$to) json_fail('Das Formular ist gerade nicht verfügbar. Bitte rufen Sie uns an: ' . cfg()['salon']['phoneDisplay'], 503);

$sent = send_mail($to, "Kontaktanfrage von {$name}",
    '<p><strong>' . e($name) . '</strong> · ' . e($email) . ($phone ? ' · ' . e($phone) : '') . '</p>'
    . '<p>' . nl2br(e($message)) . '</p>', $email);

if (!$sent) json_fail('Die Nachricht konnte nicht gesendet werden. Bitte rufen Sie uns an: ' . cfg()['salon']['phoneDisplay'], 502);
json_out(['ok' => true]);
