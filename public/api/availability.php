<?php
declare(strict_types=1);
require __DIR__ . '/../../app/lib.php';

require_method('GET');
$date = (string)($_GET['date'] ?? '');
$summary = summarize(array_filter(explode(',', (string)($_GET['services'] ?? ''))));
if (!valid_date($date)) json_fail('Ungültiges Datum.');
if (!$summary) json_fail('Ungültige Leistungen.');

json_out(['date' => $date, 'duration' => $summary['duration'], 'slots' => free_slots($date, $summary['duration'], busy_ranges($date))]);
