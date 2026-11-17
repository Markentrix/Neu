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

/**
 * Branchen: Schlüssel => [Bezeichnung, Anfragen im Alltag, Alltag am Telefon, starke Stichwörter, schwache Stichwörter]
 * Stichwörter sind Wortanfänge (Gartenbau, Gartenpflege), ab sieben Buchstaben auch mitten im Wort (Rundballenpressen).
 */
function ki_branchen(): array {
  return [
    'lohn'     => ['Lohnunternehmen und Landwirtschaft', 'Anfragen zu Einsätzen und Terminen in der Saison', 'auf der Maschine oder im Feld',
                   'lohnunternehm|lohnarbeit|landlohn|agrarservice|agrardienst|landwirtschaft|landwirt|ackerbau|landtechnik|erntearbeit|ernte|mähdrusch|mähdrescher|häcksel|gülle|gärrest|ausbringung|pflüg|bodenbearbeitung|aussaat|drillen|silage|rundballen|strohpress|schlepper|traktor|biogas|agrar|forstwirtschaft|forstarbeit|holzernte|erdarbeit|tiefbau|stallbau|futterbau|grünland|maisaussaat|körnermais|dienstleistungen für die landwirtschaft|maschinenring|pflanzenschutz|düngung|strohballen|schlepperfahrer|fahrer gesucht',
                   'maschinenpark|fuhrpark|einsatz|saison|hof|acker|feld|wiese|mähen|pressen|transport|kran|bagger|radlader|container|kies|sand|schotter'],
    'bau'      => ['Bau, Dach und Ausbau', 'Anfragen für Angebote und Termine vor Ort', 'auf der Baustelle',
                   'bauunternehm|hochbau|rohbau|dachdeck|zimmerei|zimmerer|dachstuhl|trockenbau|stuckateur|maurer|fliesenleger|malerbetrieb|maler und lackierer|fassade|gerüstbau|sanierung|innenausbau|estrich|abbruch|bauleitung|holzbau|fertigbau|bedachung|dachfenster|spengler',
                   'baustelle|neubau|umbau|anbau|ausbau|renovier'],
    'handwerk' => ['Handwerk und Haustechnik', 'Anfragen und Rückrufwünsche', 'auf der Baustelle',
                   'elektro|elektriker|elektroinstallation|sanitär|heizung|klempner|installateur|tischler|schreiner|schlosser|metallbau|photovoltaik|wallbox|haustechnik|fensterbau|haustür|handwerksbetrieb|wärmepumpe|klimaanlage|smart home|notdienst|kundendienst|rollladen|jalousie|glaserei|sonnenschutz',
                   'handwerk|installation|montage|reparatur|wartung|meisterbetrieb'],
    'kfz'      => ['Autowerkstatt und Fahrzeugpflege', 'Terminwünsche und Rückfragen', 'unterm Auto',
                   'kfz|autowerkstatt|autohaus|autohändler|reifen|reifendienst|tüv|hauptuntersuchung|inspektion|autopflege|aufbereitung|karosserie|autoglas|autoreparatur|autolackier|fahrzeugpflege|fahrzeugaufbereitung|gebrauchtwagen|unfallinstandsetzung|zweirad|motorrad|fahrradwerkstatt|werkstatt',
                   'fahrzeug|auto |pkw|inspektion|bremsen|ölwechsel'],
    'transport'=> ['Transport, Umzug und Logistik', 'Anfragen zu Fahrten, Terminen und Preisen', 'auf Tour',
                   'spedition|umzug|logistik|fuhrunternehm|transportunternehm|kurier|containerdienst|abschlepp|autokran|krandienst|schwertransport|kippertransport|baustofftransport|entrümpelung|haushaltsauflösung|taxi|fahrdienst|krankenfahrt|möbeltransport|busreise|reisebus|personenbeförderung|lkw',
                   'transport|fahrt|lieferung|abholung'],
    'beauty'   => ['Friseur und Beauty', 'Terminwünsche', 'am Stuhl',
                   'friseur|frisör|haarstudio|barber|kosmetik|nagelstudio|nageldesign|wimpern|beautysalon|haarschnitt|fußpflege|podolog|tattoo|piercing|waxing|permanent make|massage|wellness|sonnenstudio|friseursalon|haarverlängerung|visagist',
                   'beauty|styling|haare|farbe|schnitt|pflege'],
    'praxis'   => ['Praxis und Gesundheit', 'Terminanfragen und Rückrufe', 'in der Behandlung',
                   'arztpraxis|zahnarzt|zahnärzt|zahnmedizin|physiotherap|ergotherap|heilpraktik|logopäd|osteopath|tierarzt|tierärzt|orthopäd|hausarzt|kieferorthop|augenarzt|hautarzt|kinderarzt|frauenarzt|psycholog|psychotherap|krankengymnastik|podologie|hörgeräte|optiker|apotheke|sanitätshaus|labor|pflegedienst|tagespflege|seniorenbetreu',
                   'praxis|patient|behandlung|therapie|sprechzeiten|termin'],
    'gastro'   => ['Gastronomie', 'Reservierungen und Fragen zu Karte und Zeiten', 'im Service',
                   'restaurant|gasthaus|gasthof|speisekarte|café|cafe|bistro|imbiss|pizzeria|catering|partyservice|biergarten|bäckerei|konditorei|metzgerei|fleischerei|tischreservierung|gaststätte|eisdiele|kantine|hofcafé|landgasthof|eventlocation|saalvermietung|schlachterei|hofladen',
                   'speisen|getränke|küche|menü|mittagstisch|frühstück|feier'],
    'hotel'    => ['Hotel und Pension', 'Zimmeranfragen und Gästefragen', 'an der Rezeption',
                   'hotel|pension|ferienwohnung|ferienhaus|gästezimmer|übernachtung|unterkunft|bed\s?&\s?breakfast|zimmer buchen|campingplatz|ferienhof|urlaub auf dem bauernhof|gästehaus|herberge|reiterhof|wohnmobilstellplatz',
                   'gäste|zimmer|buchung|anreise|urlaub|ferien'],
    'fitness'  => ['Fitness, Sport und Kurse', 'Anfragen zu Probetraining und Kursen', 'im Training',
                   'fitnessstudio|fitness|sportstudio|yoga|pilates|crossfit|personal trainer|tanzschule|kampfsport|kursplan|probetraining|sportverein|schwimmschule|reitschule|reitunterricht|ponyclub|reitverein|pferdesport|tennis|golf|kletter|musikschule|fahrschule|nachhilfe|sprachschule|volkshochschule|hundeschule|hundetraining|tierpension|tierheim|pferdepension|pensionspferde',
                   'training|kurs|unterricht|trainer|mitglied|verein'],
    'garten'   => ['Garten und Hausservice', 'Anfragen zu Einsätzen und Terminen', 'im Einsatz',
                   'garten|landschaftsbau|landschaftspflege|rasenpflege|heckenschnitt|baumpflege|baumfäll|gärtner|gärtnerei|baumschule|hausmeisterservice|hausmeister|gebäudereinigung|glasreinigung|unterhaltsreinigung|winterdienst|schädlingsbekämpfung|pflasterarbeiten|zaunbau|teichbau|poolbau|gartengestaltung|grünpflege|grünschnitt|reinigungsservice|reinigungsfirma|haushaltshilfe|haushaltsnahe',
                   'rasen|hecke|pflege|reinigung|service'],
    'handel'   => ['Einzelhandel und Fachgeschäft', 'Fragen zu Sortiment, Preisen und Öffnungszeiten', 'im Laden',
                   'supermarkt|einzelhandel|fachgeschäft|boutique|fachhandel|blumenladen|blumengeschäft|floristik|geschenkartikel|onlineshop|online-shop|warenkorb|fleischtheke|feinkost|lebensmittel|wochenmarkt|tabakwaren|schreibwaren|buchhandlung|spielwaren|baumarkt|raumausstatter|möbelhaus|einrichtungshaus|zoofachhandel|futtermittel|landhandel|landmarkt|bauernladen|direktvermarkt|bioladen|reformhaus|schmuck|juwelier|uhren',
                   'sortiment|angebote der woche|preise|öffnungszeiten|verkauf|kaufen'],
    'beratung' => ['Beratung und Dienstleistung', 'Erstanfragen', 'im Mandantengespräch',
                   'steuerberat|kanzlei|rechtsanwalt|unternehmensberat|versicherung|immobilienmakler|immobilien|hausverwaltung|makler|werbeagentur|webdesign|marketing|coaching|buchhaltung|lohnbuchhaltung|finanzberat|architekt|ingenieurbüro|fotograf|fotostudio|übersetz|gutachter|sachverständig|energieberat|bestatter|notar|zahnlabor|druckerei',
                   'beratung|dienstleist|agentur|büro|mandant|kunden'],
  ];
}

/** Zuordnung von schema.org-Typen zu Branchen (stärkstes Signal, wenn die Seite sich selbst so beschreibt). */
function ki_ld_map(): array {
  return ['AutoRepair' => 'kfz', 'AutomotiveBusiness' => 'kfz', 'AutoDealer' => 'kfz', 'AutoWash' => 'kfz', 'MotorcycleRepair' => 'kfz', 'Dentist' => 'praxis', 'Physician' => 'praxis', 'MedicalBusiness' => 'praxis', 'MedicalClinic' => 'praxis', 'Pharmacy' => 'praxis', 'Optician' => 'praxis', 'VeterinaryCare' => 'praxis',
          'Restaurant' => 'gastro', 'FoodEstablishment' => 'gastro', 'Bakery' => 'gastro', 'CafeOrCoffeeShop' => 'gastro', 'BarOrPub' => 'gastro', 'FastFoodRestaurant' => 'gastro', 'Hotel' => 'hotel', 'LodgingBusiness' => 'hotel', 'BedAndBreakfast' => 'hotel', 'Campground' => 'hotel',
          'HairSalon' => 'beauty', 'BeautySalon' => 'beauty', 'DaySpa' => 'beauty', 'NailSalon' => 'beauty', 'HealthClub' => 'fitness', 'SportsActivityLocation' => 'fitness', 'ExerciseGym' => 'fitness', 'SportsClub' => 'fitness',
          'Electrician' => 'handwerk', 'Plumber' => 'handwerk', 'HVACBusiness' => 'handwerk', 'Locksmith' => 'handwerk', 'RoofingContractor' => 'bau', 'GeneralContractor' => 'bau', 'HousePainter' => 'bau', 'HomeAndConstructionBusiness' => 'bau',
          'MovingCompany' => 'transport', 'LegalService' => 'beratung', 'AccountingService' => 'beratung', 'FinancialService' => 'beratung', 'RealEstateAgent' => 'beratung', 'InsuranceAgency' => 'beratung', 'Attorney' => 'beratung', 'Notary' => 'beratung',
          'Store' => 'handel', 'GroceryStore' => 'handel', 'Florist' => 'handel', 'ClothingStore' => 'handel', 'HardwareStore' => 'handel', 'Butcher' => 'gastro', 'GardenStore' => 'handel'];
}

/** Wandelt eine Stichwortliste in eine Regex: Wortanfang, ab sieben Buchstaben auch mitten im Wort. Liefert das ganze gefundene Wort. */
function ki_re(string $list): string {
  $parts = [];
  foreach (explode('|', $list) as $w) {
    $w = trim($w); if ($w === '') continue;
    $parts[] = (mb_strlen($w) >= 7 ? '' : '(?<![\p{L}])') . $w;
  }
  return '/\p{L}*(?:' . implode('|', $parts) . ')\p{L}*/iu';
}

/** Zählt die verschiedenen Treffer einer Branche in einem Text; liefert [Punkte, Wörter]. */
function ki_hits(string $text, string $re): array {
  if ($text === '') return [0, []];
  if (!preg_match_all($re, mb_substr($text, 0, 12000), $m)) return [0, []];
  $w = []; foreach ($m[0] as $x) { $k = mb_strtolower($x); if (mb_strlen($k) >= 4) $w[$k] = true; }
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
  foreach (ki_branchen() as $key => $b) {
    $strong = ki_re($b[3]); $weak = ki_re($b[4]); $s = 0.0;
    foreach ($src as [$wt, $tx]) {
      if ($tx === '') continue;
      [$n, $words] = ki_hits($tx, $strong);
      if ($n) { $s += $wt * min($n, 4); foreach (array_slice($words, 0, 3) as $w) $belege[$key][$w] = ($belege[$key][$w] ?? 0) + $wt; }
      [$n2] = ki_hits($tx, $weak); if ($n2) $s += 0.25 * $wt * min($n2, 4);
    }
    $score[$key] = $s;
  }
  // schema.org-Typen: die Seite nennt ihre Art selbst
  foreach ((array) ($S['ld_types'] ?? []) as $t) { $m = ki_ld_map(); if (isset($m[$t])) { $score[$m[$t]] = ($score[$m[$t]] ?? 0) + 10; $belege[$m[$t]]['schema.org: ' . $t] = 99; } }
  arsort($score); $keys = array_keys($score); $top = $keys[0]; $s1 = $score[$top]; $s2 = $score[$keys[1]] ?? 0;
  $sicher = $s1 >= 8 && $s1 >= 1.4 * $s2;
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
  $B = ki_branchen();
  $label = $bk ? $B[$bk][0] : null;
  $anfragen = $bk ? $B[$bk][1] : 'Anfragen';
  $alltag = $bk ? $B[$bk][2] : 'bei der Arbeit';
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

  // Kandidaten mit Gewicht; Branchen-Zuschläge je Kandidat
  $c = [];
  $bon = function (array $keys, int $v) use ($bk): int { return $bk && in_array($bk, $keys, true) ? $v : 0; };
  if (!$wa && !$chat) $c[] = [80 + $bon(['beauty', 'gastro', 'hotel', 'handel', 'fitness', 'kfz', 'lohn', 'bau', 'garten', 'transport'], 10), 'WhatsApp-Assistent für ' . $anfragen,
    'Ein Assistent beantwortet ' . $anfragen . ' im Chat, schlägt Termine vor und übergibt Unklares an Sie. Antworten kommen aus Texten, die Sie freigegeben haben.',
    'Auf Ihrer Startseite ist weder ein WhatsApp-Kontakt noch ein Chat zu erkennen.', 'Entlastet Telefon und Postfach. Kunden bekommen eine erste Antwort, auch wenn Sie gerade nicht am Handy sind.', 'ab Paket ONE'];
  if ($tel) $c[] = [70 + $bon(['handwerk', 'kfz', 'praxis', 'gastro', 'beauty', 'garten', 'lohn', 'bau', 'transport'], 12), 'Telefonassistent für verpasste Anrufe',
    'Wenn Sie ' . $alltag . ' nicht rangehen können, nimmt der Assistent den Anruf an, gibt Auskunft zu Leistungen und Zeiten und erfasst den Rückrufwunsch samt Terminvorschlag.',
    'Ihre Telefonnummer ist auf der Startseite als Kontaktweg hinterlegt. Jeder verpasste Anruf ist eine offene Anfrage.', 'Weniger verpasste Anfragen im laufenden Betrieb, Rückrufwünsche liegen geordnet bei Ihnen.', 'ab Paket BUSINESS'];
  if (($form || $mail) && !$chat) $c[] = [60 + $bon(['beratung', 'handwerk', 'praxis', 'handel', 'lohn', 'bau', 'transport'], 8), 'E-Mail-Assistent für das Postfach',
    'Der Assistent sortiert eingehende Nachrichten, bereitet Antworten vor und legt Wichtiges zur Freigabe vor. Nichts geht ohne Ihr Ok hinaus.',
    'Anfragen kommen über ' . ($form && $mail ? 'Formular und E-Mail-Adresse' : ($form ? 'das Formular' : 'die E-Mail-Adresse')) . ' und müssen heute jeweils von Hand gelesen und beantwortet werden.', 'Weniger Sortieren und Tippen, schnellere erste Antwort.', 'ab Paket ONE'];
  if (!$form && in_array($bk, ['lohn', 'bau', 'garten', 'transport', 'handwerk'], true)) $c[] = [85, 'Einsatzanfrage mit Ort, Umfang und Wunschzeitraum',
    'Ein Anfrageformular oder ein WhatsApp-Assistent fragt gleich ab, welcher Einsatz gewünscht ist, wo er stattfindet, wie groß er ist und wann. Anfragen kommen vorsortiert bei Ihnen an, Rückfragen entfallen.',
    'Auf der Startseite ist kein Anfrageformular zu erkennen. Anfragen laufen über Telefon oder E-Mail und beginnen mit Rückfragen.', 'Weniger Rückfragen, schnellere Zu- oder Absage, bessere Einsatzplanung.', 'ab Paket LANDING START'];
  if (!$booking) $c[] = [75 + $bon(['beauty', 'praxis', 'kfz', 'fitness', 'handwerk', 'gastro', 'hotel'], 12), 'Online-Terminbuchung mit Erinnerung',
    'Kunden wählen freie Termine selbst, bekommen eine Bestätigung und eine Erinnerung. Die Termine landen in Ihrem Kalender.',
    'Auf der Startseite ist keine Online-Terminbuchung zu erkennen. Terminwünsche laufen heute über Telefon oder Formular.', 'Weniger Hin und Her bei der Terminfindung, weniger vergessene Termine.', 'ab Paket LANDING'];
  if (!$faq) $c[] = [65 + $bon(['praxis', 'hotel', 'gastro', 'handel', 'beratung'], 8), 'Fragen und Antworten für Besucher, Google und KI',
    'Ein Bereich mit den häufigsten Kundenfragen beantwortet vieles, bevor jemand anruft. Er wird für Google und KI-Antworten ausgezeichnet und ist später die Grundlage für einen Chat-Assistenten.',
    'Auf der Startseite ist kein Bereich mit häufigen Fragen zu finden.', 'Weniger Standardfragen am Telefon, bessere Chance, in KI-Antworten genannt zu werden.', 'in jeder Website möglich'];
  if (!$reviews) $c[] = [55 + $bon(['handwerk', 'kfz', 'beauty', 'praxis', 'gastro', 'hotel', 'garten', 'bau', 'lohn', 'transport'], 10), 'Bewertungen nach Auftrag oder Besuch anfragen',
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
    'branche' => $label, 'branche_key' => $bk, 'branche_sicher' => (bool) $br['sicher'], 'belege' => array_values($br['belege']), 'thema' => $thema,
    'reife' => $reife, 'reife_text' => $rt,
    'vorhanden' => $da, 'fehlt' => $fehlt,
    'chancen' => $out,
    'hinweis' => 'Einschätzung aus dem, was auf Ihrer Startseite von außen sichtbar ist. Es gibt keine Zusagen zu Einsparungen. Was sich bei Ihnen lohnt, klären wir im Gespräch.',
  ];
}
