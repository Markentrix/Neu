<?php
/**
 * Markentrix · KI-Potenzial (Teil des Website-Checks).
 *
 * Wird von check.php eingebunden. Liest nur, was auf der bereits abgerufenen Startseite von außen sichtbar ist
 * (Titel, Überschriften, Text, Kontaktwege, Terminbuchung, Fragen und Antworten, Bewertungen, Sprachen).
 * Es gibt keinen Aufruf einer KI und keinen weiteren Abruf. Alles ist regelbasiert und nachvollziehbar:
 * Jede Empfehlung nennt den Anlass („Das sehen wir bei Ihnen“). Es werden keine Einsparungen in Stunden oder Euro versprochen.
 * Die genannten Bausteine entsprechen den Leistungen auf markentrix.de (KI-Kundenkommunikation, Terminbuchung, Fragen und Antworten,
 * Bewertungsanfragen, Social Media, Newsletter, Online-Shop und Gutscheine).
 */
declare(strict_types=1);

require_once __DIR__ . '/ki-branchen.php';

/** Wandelt eine Stichwortliste in eine Regex: Wortanfang, ab sieben Buchstaben auch mitten im Wort. Liefert das ganze gefundene Wort. */
function ki_re(string $list): string {
  $parts = [];
  foreach (explode('|', $list) as $w) {
    $w = trim($w); if ($w === '') continue;
    if (substr($w, -1) === '!') { $parts[] = '(?<![\p{L}])' . substr($w, 0, -1) . '(?![\p{L}])'; continue; }
    $parts[] = (mb_strlen($w) >= 7 ? '' : '(?<![\p{L}])') . $w;
  }
  return '/\p{L}*(?:' . implode('|', $parts) . ')\p{L}*/iu';
}

/** Zählt die verschiedenen Treffer einer Branche in einem Text; liefert [Punkte, Wörter]. */
function ki_hits(string $text, string $re): array {
  if ($text === '') return [0, []];
  if (!preg_match_all($re, mb_substr($text, 0, 12000), $m)) return [0, []];
  $w = []; foreach ($m[0] as $x) { $k = mb_strtolower($x); if (mb_strlen($k) >= 2) $w[$k] = true; }
  return [count($w), array_keys($w)];
}

/**
 * Erkennt die Branche aus allen Hinweisen, die der Check gesammelt hat: Titel, Überschriften, Beschreibung, Domain, Menü,
 * Adressen der Unterseiten, schema.org-Angaben, Bildbeschreibungen, Text der Startseite und der abgerufenen Unterseiten.
 * Liefert ['key', 'punkte', 'sicher', 'belege'] oder key = null.
 */
function ki_branche(array $d): array {
  $S = (array) ($d['sig'] ?? []);
  $src = [ // [Gewicht, Text]
    [4, (string) $d['title']], [4, implode(' ', (array) $d['h1'])], [3, (string) $d['desc']], [2, implode(' ', array_slice((array) $d['h2'], 0, 12))],
    [4, (string) ($S['host'] ?? '')], [3, (string) ($S['nav'] ?? '')], [2, (string) ($S['slugs'] ?? '')], [2, (string) ($S['og'] ?? '')], [4, (string) ($S['ld_text'] ?? '')],
    [1, (string) ($S['alts'] ?? '')], [1, (string) $d['text']],
  ];
  foreach ((array) ($S['sample'] ?? []) as $sp) {
    $src[] = [3, (string) ($sp['title'] ?? '') . ' ' . (string) ($sp['h1'] ?? '')]; $src[] = [2, implode(' ', (array) ($sp['h2'] ?? [])) . ' ' . (string) ($sp['desc'] ?? '')]; $src[] = [1, (string) ($sp['text'] ?? '')];
  }
  $score = []; $belege = [];
  foreach (ki_profile() as $key => $b) {
    $strong = ki_re($b['strong']); $weak = ki_re($b['weak']); $s = 0.0;
    foreach ($src as [$wt, $tx]) {
      if ($tx === '') continue;
      [$n, $words] = ki_hits($tx, $strong);
      if ($n) { $s += $wt * min($n, 4); foreach (array_slice($words, 0, 3) as $w) $belege[$key][$w] = ($belege[$key][$w] ?? 0) + $wt; }
      [$n2] = ki_hits($tx, $weak); if ($n2) $s += 0.25 * $wt * min($n2, 4);
    }
    $score[$key] = $s;
  }
  // schema.org-Typen: die Seite nennt ihre Art selbst
  foreach ((array) ($S['ld_types'] ?? []) as $t) { $m = ki_ld_map(); if (!empty($m[$t])) { $score[$m[$t]] = ($score[$m[$t]] ?? 0) + 10; $belege[$m[$t]]['schema.org: ' . $t] = 99; } }
  arsort($score); $keys = array_keys($score); $top = $keys[0]; $s1 = $score[$top]; $s2 = $score[$keys[1]] ?? 0;
  $sicher = $s1 >= 7 && $s1 >= 1.4 * $s2;
  $vermutet = !$sicher && $s1 >= 4 && $s1 >= 1.6 * $s2;
  if (!$sicher && !$vermutet) return ['key' => null, 'punkte' => $s1, 'sicher' => false, 'belege' => []];
  $bel = $belege[$top] ?? []; arsort($bel);
  $words = array_values(array_filter(array_keys($bel), fn($w) => mb_strlen((string) $w) <= 22));
  $words = array_map(fn($w) => (strpos((string) $w, ':') !== false) ? (string) $w : mb_strtoupper(mb_substr((string) $w, 0, 1)) . mb_substr((string) $w, 1), $words);
  return ['key' => $top, 'punkte' => $s1, 'sicher' => $sicher, 'belege' => array_slice($words, 0, 4)];
}

/** Hauptfunktion. Erwartet die Merkmale der Startseite, liefert Branche, Reife und bis zu vier Chancen. */
function ki_potenzial(array $d): array {
  $lower = (string) $d['lower'];
  $text = lc((string) $d['text']);
  $all = $lower . ' ' . $text;
  $br = ki_branche($d); $bk = $br['key'];
  $PR = ki_profile(); $pf = $bk ? $PR[$bk] : null;
  $label = $pf['label'] ?? null;
  $alltag = $pf['alltag'] ?? 'bei der Arbeit';
  $anliegen = $pf['anliegen'] ?? 'Anfragen von Kunden';
  $fragen = $pf['fragen'] ?? 'Leistungen, Preise, Öffnungszeiten und Ansprechpartner';
  $rueckruf = $pf['rueckruf'] ?? 'Name, Anliegen und Rückrufzeit';
  $termin = $pf['termin'] ?? ['Online-Terminbuchung mit Erinnerung', 'Kunden wählen freie Termine selbst, bekommen eine Bestätigung und eine Erinnerung. Die Termine landen in Ihrem Kalender.'];
  $bew = $pf['bew'] ?? 'nach Auftrag oder Besuch';
  $content = $pf['content'] ?? 'Neuigkeiten, Angebote und Aktionen';
  $extra = $pf['extra'] ?? [];
  $skip = $pf['skip'] ?? [];
  // Ohne sichere Branche nennen wir, womit sich die Seite selbst vorstellt
  $thema = '';
  if (!$bk) { $thema = trim((string) ($d['h1'][0] ?? '')); if ($thema === '') $thema = trim((string) preg_replace('/\s*[|–—-]\s*[^|–—-]*$/u', '', (string) $d['title'])); $thema = mb_substr($thema, 0, 70); }

  // Merkmale der Startseite
  $chat = (bool) preg_match('/tawk\.to|crisp\.chat|tidio|intercom|drift\.com|zendesk|userlike|livechat|hs-scripts|botpress|manychat|jivochat|smartsupp|olark|freshchat|leadconnector|chatbot|chat-widget|whatsapp-chat/u', $lower);
  $wa = !empty($d['hasWa']);
  $tel = !empty($d['hasTel']);
  $form = !empty($d['hasForm']);
  $mail = !empty($d['hasMail']);
  $booking = (bool) preg_match('/calendly|simplybook|timify|doctolib|jameda|resmio|opentable|booksy|treatwell|setmore|acuity|appointlet|bookingkit|termin\s*(online\s*)?(buchen|vereinbaren)|online-?terminbuchung|online-?termin|tisch\s*reservieren|online\s*reservier|jetzt\s*buchen|zimmer\s*buchen/u', $all);
  $faq = !empty($d['hasFaq']);
  $reviews = (bool) preg_match('/aggregaterating|bewertungen|rezension|kundenstimmen|sterne|trustpilot|provenexpert|google\s*bewertung/u', $all);
  $hours = (bool) preg_match('/öffnungszeiten|openinghours|sprechzeiten|geöffnet|mo\.?\s*[-–]\s*fr/u', $all);
  $multi = ((int) preg_match_all('/hreflang=/', $lower)) >= 2;
  $newsletter = (bool) preg_match('/newsletter/u', $all);
  $shop = (bool) preg_match('/warenkorb|woocommerce|shopify|in den warenkorb|gutschein/u', $all);
  $social = !empty($d['socialCount']);
  $ldLocal = !empty($d['hasEntity']);
  $mobile = !empty($d['viewport']);
  $https = !empty($d['https']);

  // Reife: Wie viele Voraussetzungen für automatisierte Anfragen sind von außen schon sichtbar (0 bis 100)
  $pts = ['Kontaktformular' => [$form, 12], 'Telefonnummer zum Antippen' => [$tel, 8], 'WhatsApp oder Chat' => [$wa || $chat, 15], 'Online-Terminbuchung' => [$booking, 15],
          'Fragen und Antworten' => [$faq, 12], 'Strukturierte Unternehmensdaten' => [$ldLocal, 12], 'Öffnungszeiten' => [$hours, 8], 'Bewertungen sichtbar' => [$reviews, 8],
          'HTTPS' => [$https, 5], 'Mobil darstellbar' => [$mobile, 5]];
  $reife = 0; $da = []; $fehlt = [];
  foreach ($pts as $name => [$ok, $w]) { if ($ok) { $reife += $w; $da[] = $name; } else { $fehlt[] = $name; } }

  // Kandidaten mit Gewicht. Gruppen verschieben die Reihenfolge: Einsatzbetriebe (E), Terminbetriebe (T), Gäste- und Ladenbetriebe (G).
  $grp = ['E' => ['lohn', 'bau', 'handwerk', 'reinigung', 'garten', 'transport', 'pflege'], 'T' => ['kfz', 'beauty', 'praxis', 'tier', 'fitness', 'bildung', 'foto', 'beratung', 'immobilien', 'agentur'], 'G' => ['gastro', 'bar', 'event', 'hotel', 'freizeit', 'handel', 'verein']];
  $in = fn(string $g): bool => $bk !== null && in_array($bk, $grp[$g], true);
  $c = []; $gl0 = 'Das sehen wir bei Ihnen';
  $cap = fn(string $s): string => mb_strtoupper(mb_substr($s, 0, 1)) . mb_substr($s, 1);
  if (!$wa && !$chat) $c[] = [80 + ($bk ? 8 : 0), 'WhatsApp-Assistent für Anfragen und Rückfragen',
    'Der Assistent beantwortet Fragen zu ' . $fragen . ' direkt im Chat und nimmt ' . $anliegen . ' entgegen. Unklares übergibt er an Sie. Antworten kommen aus Texten, die Sie freigegeben haben.',
    'Auf Ihrer Startseite ist weder ein WhatsApp-Kontakt noch ein Chat zu erkennen.', 'Entlastet Telefon und Postfach. Kunden bekommen eine erste Antwort, auch wenn Sie ' . $alltag . ' nicht am Handy sind.', 'ab Paket ONE', $gl0];
  if ($tel) $c[] = [70 + ($in('E') ? 14 : ($in('T') ? 10 : ($in('G') ? 4 : 0))), 'Telefonassistent für verpasste Anrufe',
    'Wenn Sie ' . $alltag . ' nicht rangehen können, nimmt der Assistent den Anruf an, gibt Auskunft zu ' . $fragen . ', erfasst ' . $rueckruf . ' und schlägt einen Termin vor.',
    'Ihre Telefonnummer ist auf der Startseite als Kontaktweg hinterlegt. Jeder verpasste Anruf ist eine offene Anfrage.', 'Weniger verpasste Anfragen im laufenden Betrieb, Rückrufwünsche liegen geordnet und vollständig bei Ihnen.', 'ab Paket BUSINESS', $gl0];
  if (($form || $mail) && !$chat) $c[] = [60 + ($in('T') ? 6 : 0), 'E-Mail-Assistent für das Postfach',
    'Der Assistent sortiert eingehende Nachrichten (' . $anliegen . '), bereitet Antworten vor und legt Wichtiges zur Freigabe vor. Nichts geht ohne Ihr Ok hinaus.',
    'Anfragen kommen über ' . ($form && $mail ? 'Formular und E-Mail-Adresse' : ($form ? 'das Formular' : 'die E-Mail-Adresse')) . ' und müssen heute jeweils von Hand gelesen und beantwortet werden.', 'Weniger Sortieren und Tippen, schnellere erste Antwort.', 'ab Paket ONE', $gl0];
  if (!$booking) $c[] = [74 + ($in('T') ? 14 : ($in('G') ? 12 : 4)), $termin[0], $termin[1],
    'Auf der Startseite ist keine Online-Buchung zu erkennen. Buchungen und Termine laufen heute über Telefon oder Nachricht.', 'Weniger Hin und Her bei der Terminfindung, weniger vergessene Termine.', 'ab Paket LANDING', $gl0];
  if (!$faq) $c[] = [64 + ($in('G') || in_array($bk, ['praxis', 'beratung'], true) ? 8 : 0), 'Fragen und Antworten: ' . $fragen,
    'Ein eigener Bereich beantwortet diese Fragen, bevor jemand anruft. Er wird für Google und KI-Antworten ausgezeichnet und ist später die Grundlage für den Chat-Assistenten.',
    'Auf der Startseite ist kein Bereich mit häufigen Fragen zu finden.', 'Weniger Standardfragen am Telefon, bessere Chance, in KI-Antworten genannt zu werden.', 'in jeder Website möglich', $gl0];
  if (!$reviews && !in_array('noreviews', $skip, true)) $c[] = [55 + ($bk ? 8 : 0), 'Bewertungen ' . $bew . ' anfragen',
    'Eine freundliche Bitte um eine Google-Bewertung geht automatisch ' . $bew . ' an den Kunden, mit direktem Link. Sie bestimmen, wer sie bekommt.',
    'Auf der Startseite sind keine Kundenbewertungen oder Stimmen sichtbar.', 'Mehr sichtbare Bewertungen, ohne dass Sie daran denken müssen.', 'Zusatz, einzeln buchbar', $gl0];
  if ($multi) $c[] = [50 + ($in('G') ? 10 : 0), 'Mehrsprachige Inhalte aktuell halten',
    'Neue Aktionen, Preise und Öffnungszeiten werden über einen Übersetzungsablauf in alle Sprachen übernommen. Fachliche Freigabe bleibt bei Ihnen.',
    'Ihre Seite gibt es in mehreren Sprachen. Jede Änderung muss dort mehrfach gepflegt werden.', 'Weniger doppelte Pflege, einheitliche Angaben in allen Sprachen.', 'im Angebot festgelegt', $gl0];
  if (!$social && !in_array('nosocial', $skip, true)) $c[] = [45 + ($in('G') ? 14 : 4), 'Beiträge zu ' . $content,
    'Ein Redaktionsplan, vorbereitete Beiträge und eine feste Freigabe durch Sie halten Google-Profil und Social Media aktuell, ohne dass es am Feierabend hängen bleibt.',
    'Auf der Startseite sind keine Social-Media-Profile verlinkt.', 'Regelmäßige Sichtbarkeit bei Google und in sozialen Netzwerken, planbarer Aufwand.', 'Zusatz, einzeln buchbar', $gl0];
  if (!$newsletter && !in_array('nonews', $skip, true)) $c[] = [35 + ($in('G') ? 10 : 0), 'Newsletter: ' . $content,
    'Eine Anmeldung auf der Website, Vorlagen und ein fester Rhythmus. Versand und Auswertung laufen mit.',
    'Auf der Startseite ist keine Newsletter-Anmeldung zu finden.', 'Stammkunden erfahren Neues, ohne dass Sie jedes Mal selbst schreiben.', 'Zusatz, einzeln buchbar', $gl0];
  // Chancen, die nur für diese Branche gelten
  $need = [
    'noform' => !$form, 'nobooking' => !$booking, 'nowa' => !$wa && !$chat, 'nofaq' => !$faq, 'noreviews' => !$reviews, 'noshop' => !$shop, 'nosocial' => !$social, 'nonews' => !$newsletter, 'hastel' => $tel, 'always' => true];
  $reason = [
    'noform' => 'Auf der Startseite ist kein Anfrageformular zu erkennen, das die wichtigsten Angaben gleich abfragt.', 'nobooking' => 'Auf der Startseite ist keine Online-Buchung zu erkennen.',
    'nowa' => 'Es ist kein WhatsApp-Kontakt zu erkennen.', 'nofaq' => 'Es ist kein Bereich mit häufigen Fragen zu erkennen.', 'noreviews' => 'Es sind keine Kundenbewertungen sichtbar.',
    'noshop' => 'Auf der Startseite ist kein Shop und kein Gutscheinverkauf zu erkennen.', 'nosocial' => 'Es sind keine Social-Media-Profile verlinkt.', 'nonews' => 'Es ist keine Newsletter-Anmeldung zu erkennen.', 'hastel' => 'Ihre Telefonnummer ist als Kontaktweg hinterlegt.',
    'always' => 'Für ' . ($label ?? 'Ihren Betrieb') . ' ein üblicher Hebel. Ob und wie Sie das heute schon nutzen, sehen wir von außen nicht und klären es im Gespräch.'];
  foreach ($extra as [$xt, $xx, $xw, $xp, $xg, $xn]) {
    if (!($need[$xn] ?? false)) continue;
    $c[] = [$xg, $xt, $xx, $reason[$xn], $xw, $xp, $xn === 'always' ? 'Warum das zu Ihnen passt' : $gl0];
  }
  if (count($c) < 3) $c[] = [20, 'Tägliches Briefing statt Postfach durchsuchen',
    'Jeden Morgen eine kurze Zusammenfassung: neue Anfragen, offene Rückrufe, anstehende Termine.',
    'Mehrere Kontaktwege laufen nebeneinander und sammeln sich an verschiedenen Orten.', 'Ein Blick am Morgen statt mehrerer Postfächer.', 'Teil der KI-Pakete', $gl0];

  usort($c, fn($a, $b) => $b[0] <=> $a[0]);
  $out = [];
  foreach (array_slice($c, 0, 4) as $x) $out[] = ['titel' => $x[1], 'text' => $x[2], 'grund' => $x[3], 'wirkung' => $x[4], 'paket' => $x[5], 'gl' => $x[6]];

  $rt = $reife >= 75 ? 'Viele Voraussetzungen sind schon sichtbar. Automatisierung setzt hier an Feinheiten an.'
      : ($reife >= 45 ? 'Ein Teil der Voraussetzungen ist da. Mit wenigen Bausteinen lassen sich Anfragen spürbar leichter verwalten.'
      : 'Von außen sind erst wenige Voraussetzungen für automatisierte Anfragen zu erkennen. Hier steckt am meisten Spielraum.');
  return [
    'branche' => $label, 'branche_key' => $bk, 'branche_sicher' => (bool) $br['sicher'], 'belege' => array_values($br['belege']), 'thema' => $thema,
    'reife' => $reife, 'reife_text' => $rt,
    'vorhanden' => $da, 'fehlt' => $fehlt,
    'chancen' => $out,
    'hinweis' => 'Einschätzung aus dem, was auf Ihrer Startseite von außen sichtbar ist. Es gibt keine Zusagen zu Einsparungen. Was sich bei Ihnen lohnt, klären wir im Gespräch.',
  ];
}
