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

/** Branchenmerkmale: Schlüssel => [Bezeichnung, Anfragen im Alltag, Stichwörter (Regex, ohne Begrenzer)] */
function ki_branchen(): array {
  return [
    'handwerk' => ['Handwerk und Haustechnik', 'Anfragen und Rückrufwünsche', 'elektr|sanitär|heizung|klempner|installateur|dachdeck|maler|lackier|tischler|schreiner|zimmerer|fliesen|bauunternehmen|handwerk|photovoltaik|wallbox|haustechnik|fensterbau|trockenbau|metallbau'],
    'kfz'      => ['Autowerkstatt und Fahrzeugpflege', 'Terminwünsche und Rückfragen', 'werkstatt|kfz|autohaus|reifen|tüv|inspektion|fahrzeug|autopflege|aufbereitung|lackier|karosserie|autoglas|auto\s?reparatur'],
    'beauty'   => ['Friseur und Beauty', 'Terminwünsche', 'friseur|frisör|haarstudio|barber|kosmetik|nagelstudio|nails|wimpern|beauty|massage|friseursalon|haarschnitt|fußpflege|tattoo'],
    'praxis'   => ['Praxis und Gesundheit', 'Terminanfragen und Rückrufe', 'arztpraxis|zahnarzt|zahnärzt|praxis|physiotherap|ergotherap|heilpraktik|logopäd|osteopath|tierarzt|orthopäd|hausarzt|kieferorthop|therapie'],
    'gastro'   => ['Gastronomie', 'Reservierungen und Fragen zu Karte und Zeiten', 'restaurant|gasthaus|gasthof|speisekarte|café|cafe|bistro|imbiss|pizzeria|catering|biergarten|bäckerei|metzgerei|tischreservierung|gaststätte'],
    'hotel'    => ['Hotel und Pension', 'Zimmeranfragen und Gästefragen', 'hotel|pension|ferienwohnung|ferienhaus|gästezimmer|übernachtung|unterkunft|bed\s?&\s?breakfast|zimmer buchen'],
    'fitness'  => ['Fitness und Sport', 'Anfragen zu Probetraining und Kursen', 'fitness|sportstudio|yoga|pilates|crossfit|training|kurse|personal trainer|tanzschule|kampfsport|fitnessstudio'],
    'garten'   => ['Garten und Hausservice', 'Anfragen zu Einsätzen und Terminen', 'garten|landschaftsbau|rasen|hecke|baumpflege|gartenpflege|hausmeister|gebäudereinigung|reinigung|winterdienst|umzug|entrümpelung|schädlings'],
    'handel'   => ['Einzelhandel', 'Fragen zu Sortiment, Preisen und Öffnungszeiten', 'supermarkt|einzelhandel|geschäft|boutique|laden|markt|fachhandel|blumen|geschenk|sortiment|online-shop|onlineshop|warenkorb|fleischtheke|feinkost'],
    'beratung' => ['Beratung und Dienstleistung', 'Erstanfragen', 'steuerberat|kanzlei|rechtsanwalt|beratung|unternehmensberat|versicherung|immobilien|makler|agentur|coaching|buchhaltung|finanz|architekt|ingenieur|dienstleister'],
  ];
}

/** Erkennt die Branche aus Titel, Überschriften, Beschreibung und Text. Gibt [Schlüssel, Punkte] oder [null, 0] zurück. */
function ki_branche(array $d): array {
  $best = [null, 0];
  foreach (ki_branchen() as $key => $b) {
    $re = '/(' . $b[2] . ')/iu';
    $s = 0;
    $s += 4 * (int) preg_match_all($re, (string) $d['title']);
    $s += 4 * (int) preg_match_all($re, implode(' ', (array) $d['h1']));
    $s += 2 * (int) preg_match_all($re, implode(' ', array_slice((array) $d['h2'], 0, 8)));
    $s += 2 * (int) preg_match_all($re, (string) $d['desc']);
    $s += min(6, (int) preg_match_all($re, mb_substr((string) $d['text'], 0, 4000)));
    if ($s > $best[1]) $best = [$key, $s];
  }
  return $best[1] >= 6 ? $best : [null, $best[1]];
}

/** Hauptfunktion. Erwartet die Merkmale der Startseite, liefert Branche, Reife und bis zu vier Chancen. */
function ki_potenzial(array $d): array {
  $lower = (string) $d['lower'];
  $text = lc((string) $d['text']);
  $all = $lower . ' ' . $text;
  [$bk, $bscore] = ki_branche($d);
  $B = ki_branchen();
  $label = $bk ? $B[$bk][0] : null;
  $anfragen = $bk ? $B[$bk][1] : 'Anfragen';

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

  // Kandidaten mit Gewicht; Branchen-Zuschläge je Kandidat
  $c = [];
  $bon = function (array $keys, int $v) use ($bk): int { return $bk && in_array($bk, $keys, true) ? $v : 0; };
  if (!$wa && !$chat) $c[] = [80 + $bon(['beauty', 'gastro', 'hotel', 'handel', 'fitness', 'kfz'], 10), 'WhatsApp-Assistent für ' . $anfragen,
    'Ein Assistent beantwortet ' . $anfragen . ' im Chat, schlägt Termine vor und übergibt Unklares an Sie. Antworten kommen aus Texten, die Sie freigegeben haben.',
    'Auf Ihrer Startseite ist weder ein WhatsApp-Kontakt noch ein Chat zu erkennen.', 'Entlastet Telefon und Postfach. Kunden bekommen eine erste Antwort, auch wenn Sie gerade nicht am Handy sind.', 'ab Paket ONE'];
  if ($tel) $c[] = [70 + $bon(['handwerk', 'kfz', 'praxis', 'gastro', 'beauty', 'garten'], 12), 'Telefonassistent für verpasste Anrufe',
    'Wenn Sie bei der Arbeit nicht rangehen können, nimmt der Assistent den Anruf an, gibt Auskunft zu Leistungen und Zeiten und erfasst den Rückrufwunsch samt Terminvorschlag.',
    'Ihre Telefonnummer ist auf der Startseite als Kontaktweg hinterlegt. Jeder verpasste Anruf ist eine offene Anfrage.', 'Weniger verpasste Anfragen im laufenden Betrieb, Rückrufwünsche liegen geordnet bei Ihnen.', 'ab Paket BUSINESS'];
  if (($form || $mail) && !$chat) $c[] = [60 + $bon(['beratung', 'handwerk', 'praxis', 'handel'], 8), 'E-Mail-Assistent für das Postfach',
    'Der Assistent sortiert eingehende Nachrichten, bereitet Antworten vor und legt Wichtiges zur Freigabe vor. Nichts geht ohne Ihr Ok hinaus.',
    'Anfragen kommen über ' . ($form && $mail ? 'Formular und E-Mail-Adresse' : ($form ? 'das Formular' : 'die E-Mail-Adresse')) . ' und müssen heute jeweils von Hand gelesen und beantwortet werden.', 'Weniger Sortieren und Tippen, schnellere erste Antwort.', 'ab Paket ONE'];
  if (!$booking) $c[] = [75 + $bon(['beauty', 'praxis', 'kfz', 'fitness', 'handwerk', 'gastro', 'hotel'], 12), 'Online-Terminbuchung mit Erinnerung',
    'Kunden wählen freie Termine selbst, bekommen eine Bestätigung und eine Erinnerung. Die Termine landen in Ihrem Kalender.',
    'Auf der Startseite ist keine Online-Terminbuchung zu erkennen. Terminwünsche laufen heute über Telefon oder Formular.', 'Weniger Hin und Her bei der Terminfindung, weniger vergessene Termine.', 'ab Paket LANDING'];
  if (!$faq) $c[] = [65 + $bon(['praxis', 'hotel', 'gastro', 'handel', 'beratung'], 8), 'Fragen und Antworten für Besucher, Google und KI',
    'Ein Bereich mit den häufigsten Kundenfragen beantwortet vieles, bevor jemand anruft. Er wird für Google und KI-Antworten ausgezeichnet und ist später die Grundlage für einen Chat-Assistenten.',
    'Auf der Startseite ist kein Bereich mit häufigen Fragen zu finden.', 'Weniger Standardfragen am Telefon, bessere Chance, in KI-Antworten genannt zu werden.', 'in jeder Website möglich'];
  if (!$reviews) $c[] = [55 + $bon(['handwerk', 'kfz', 'beauty', 'praxis', 'gastro', 'hotel', 'garten'], 10), 'Bewertungen nach Auftrag oder Besuch anfragen',
    'Nach Auftrag oder Besuch geht automatisch eine freundliche Bitte um eine Google-Bewertung an den Kunden, mit direktem Link. Sie bestimmen, wer sie bekommt.',
    'Auf der Startseite sind keine Kundenbewertungen oder Stimmen sichtbar.', 'Mehr sichtbare Bewertungen, ohne dass Sie daran denken müssen.', 'Zusatz, einzeln buchbar'];
  if ($multi) $c[] = [50 + $bon(['hotel', 'gastro', 'handel'], 10), 'Mehrsprachige Inhalte aktuell halten',
    'Neue Aktionen, Preise und Öffnungszeiten werden über einen Übersetzungsablauf in alle Sprachen übernommen. Fachliche Freigabe bleibt bei Ihnen.',
    'Ihre Seite gibt es in mehreren Sprachen. Jede Änderung muss dort mehrfach gepflegt werden.', 'Weniger doppelte Pflege, einheitliche Angaben in allen Sprachen.', 'im Angebot festgelegt'];
  if (!$social) $c[] = [45 + $bon(['beauty', 'gastro', 'hotel', 'fitness', 'handel', 'kfz'], 10), 'Beiträge für Google-Profil und Social Media',
    'Ein Redaktionsplan, vorbereitete Beiträge und eine feste Freigabe durch Sie halten Profile aktuell, ohne dass es am Feierabend hängen bleibt.',
    'Auf der Startseite sind keine Social-Media-Profile verlinkt.', 'Regelmäßige Sichtbarkeit bei Google und in sozialen Netzwerken, planbarer Aufwand.', 'Zusatz, einzeln buchbar'];
  if (!$newsletter) $c[] = [35 + $bon(['handel', 'gastro', 'beauty', 'fitness', 'hotel'], 10), 'Newsletter für Stammkunden',
    'Eine Anmeldung auf der Website, Vorlagen und ein fester Rhythmus für Aktionen und Neuigkeiten. Versand und Auswertung laufen mit.',
    'Auf der Startseite ist keine Newsletter-Anmeldung zu finden.', 'Stammkunden erfahren von Aktionen, ohne dass Sie jedes Mal selbst schreiben.', 'Zusatz, einzeln buchbar'];
  if (!$shop) $c[] = [33 + $bon(['handel', 'gastro', 'beauty', 'fitness'], 12), 'Gutscheine oder Online-Shop',
    'Gutscheine und Produkte lassen sich online verkaufen und im Portal pflegen. Bestellungen kommen bei Ihnen an.',
    'Auf der Startseite ist kein Shop und kein Gutscheinverkauf zu erkennen.', 'Zusätzlicher Verkaufsweg ohne Zusatzaufwand an der Theke.', 'ab Paket BUSINESS WEB'];
  if (count($c) < 3) $c[] = [20, 'Tägliches Briefing statt Postfach durchsuchen',
    'Jeden Morgen eine kurze Zusammenfassung: neue Anfragen, offene Rückrufe, anstehende Termine.',
    'Mehrere Kontaktwege laufen nebeneinander und sammeln sich an verschiedenen Orten.', 'Ein Blick am Morgen statt mehrerer Postfächer.', 'Teil der KI-Pakete'];

  usort($c, fn($a, $b) => $b[0] <=> $a[0]);
  $out = [];
  foreach (array_slice($c, 0, 4) as $x) $out[] = ['titel' => $x[1], 'text' => $x[2], 'grund' => $x[3], 'wirkung' => $x[4], 'paket' => $x[5]];

  $rt = $reife >= 75 ? 'Viele Voraussetzungen sind schon sichtbar. Automatisierung setzt hier an Feinheiten an.'
      : ($reife >= 45 ? 'Ein Teil der Voraussetzungen ist da. Mit wenigen Bausteinen lassen sich Anfragen spürbar leichter verwalten.'
      : 'Von außen sind erst wenige Voraussetzungen für automatisierte Anfragen zu erkennen. Hier steckt am meisten Spielraum.');
  return [
    'branche' => $label, 'branche_key' => $bk,
    'reife' => $reife, 'reife_text' => $rt,
    'vorhanden' => $da, 'fehlt' => $fehlt,
    'chancen' => $out,
    'hinweis' => 'Einschätzung aus dem, was auf Ihrer Startseite von außen sichtbar ist. Es gibt keine Zusagen zu Einsparungen. Was sich bei Ihnen lohnt, klären wir im Gespräch.',
  ];
}
