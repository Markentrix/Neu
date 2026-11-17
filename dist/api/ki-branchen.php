<?php
/**
 * Markentrix · Branchenprofile für das KI-Potenzial im Website-Check.
 *
 * Jede Branche hat: Erkennungs-Stichwörter (stark und schwach), und ein Profil, aus dem die Empfehlungen entstehen:
 *   alltag    Wo Sie sind, wenn das Telefon klingelt
 *   anliegen  Was Kunden typischerweise anfragen (Akkusativ, für „… beantwortet …“)
 *   fragen    Typische Kundenfragen (für Chat, Telefon und Fragen-und-Antworten-Bereich)
 *   rueckruf  Was ein Rückrufwunsch enthalten muss
 *   termin    [Titel, Text] der passenden Terminlogik (Reservierung, Behandlungstermin, Einsatztermin …)
 *   bew       Wann die Bitte um eine Bewertung sinnvoll ist
 *   content   Worüber Profile und Newsletter regelmäßig berichten könnten
 *   extra     Zusätzliche, nur für diese Branche sinnvolle Chancen: [Titel, Text, Wirkung, Paket, Gewicht, Voraussetzung]
 *             Voraussetzung: always | noform | nobooking | nowa | nofaq | noreviews | noshop | nosocial | nonews | hastel
 * Stichwörter: Wortanfang; ab sieben Buchstaben auch mitten im Wort; ein „!“ am Ende verlangt das ganze Wort (zum Beispiel „bar!“).
 * Es werden nur Leistungen genannt, die auf markentrix.de beschrieben sind. Keine Zahlen zu Einsparungen.
 */
declare(strict_types=1);

function ki_profile(): array {
  return [
    'lohn' => ['label' => 'Lohnunternehmen und Landwirtschaft',
      'strong' => 'lohnunternehm|lohnarbeit|landlohn|agrarservice|agrardienst|landwirtschaft|landwirt|ackerbau|landtechnik|erntearbeit|ernte|mähdrusch|mähdrescher|häcksel|gülle|gärrest|ausbringung|pflüg|bodenbearbeitung|aussaat|drillen|silage|rundballen|strohpress|schlepper|traktor|biogas|agrar|forstwirtschaft|forstarbeit|holzernte|erdarbeit|stallbau|futterbau|grünland|maisaussaat|körnermais|maschinenring|pflanzenschutz|düngung|strohballen',
      'weak' => 'maschinenpark|fuhrpark|einsatz|saison|hof|acker|feld|wiese|mähen|pressen|kran|bagger|radlader|kies|schotter',
      'alltag' => 'auf der Maschine oder im Feld', 'anliegen' => 'Anfragen zu Einsätzen, Flächen und Terminen in der Saison', 'fragen' => 'Leistungen, Maschinen, Einsatzgebiet, Preise und freie Termine',
      'rueckruf' => 'Name, Betrieb, gewünschte Arbeit, Fläche und Zeitraum', 'termin' => ['Einsatzplanung mit Wunschzeitraum', 'Auftraggeber nennen Arbeit, Fläche, Ort und Wunschzeitraum. Sie sehen alle Anfragen geordnet nach Datum und können Zusagen mit einem Klick bestätigen.'],
      'bew' => 'nach jedem Einsatz', 'content' => 'Saisonstart, freie Kapazitäten und neue Maschinen',
      'extra' => [['Saison-Erinnerung an Stammkunden', 'Vor Mahd, Aussaat und Ernte geht automatisch eine kurze Nachricht an Stammkunden: „Wir planen die nächste Saison, wann passt es Ihnen?“. Sie bestimmen Zeitpunkt und Empfänger.', 'Frühe Buchungen, bessere Auslastung der Maschinen, weniger Telefonate im Frühjahr.', 'Zusatz: Newsletter-System', 62, 'always']]],

    'bau' => ['label' => 'Bau, Dach und Ausbau',
      'strong' => 'bauunternehm|hochbau|rohbau|dachdeck|zimmerei|zimmerer|dachstuhl|trockenbau|stuckateur|maurer|fliesenleger|malerbetrieb|maler und lackierer|fassade|gerüstbau|sanierung|innenausbau|estrich|abbruch|bauleitung|holzbau|fertigbau|bedachung|dachfenster|spengler|tiefbau|pflasterarbeiten|straßenbau',
      'weak' => 'baustelle|neubau|umbau|anbau|ausbau|renovier',
      'alltag' => 'auf der Baustelle', 'anliegen' => 'Anfragen zu Angeboten, Besichtigungen und Terminen', 'fragen' => 'Leistungen, Einsatzgebiet, Ablauf eines Angebots und freie Kapazitäten',
      'rueckruf' => 'Name, Objekt, Art der Arbeiten und gewünschter Zeitraum', 'termin' => ['Besichtigungstermin vor Ort', 'Interessenten wählen einen freien Besichtigungstermin und laden Fotos hoch. Sie sehen vorab, worum es geht, und fahren nur zu passenden Objekten.'],
      'bew' => 'nach Abnahme der Arbeiten', 'content' => 'abgeschlossene Projekte und freie Kapazitäten',
      'extra' => [['Anfrage mit Fotos und Eckdaten', 'Ein Formular oder der WhatsApp-Assistent fragt Objektart, Ort, Umfang, Wunschzeitraum und Fotos ab. Anfragen kommen vorsortiert bei Ihnen an.', 'Weniger Rückfragen, schnellere Angebote, weniger Anfahrten ohne Auftrag.', 'ab Paket LANDING START', 85, 'noform']]],

    'handwerk' => ['label' => 'Handwerk und Haustechnik',
      'strong' => 'elektro|elektriker|elektroinstallation|sanitär|heizung|klempner|installateur|tischler|schreiner|schlosser|metallbau|photovoltaik|wallbox|haustechnik|fensterbau|haustür|handwerksbetrieb|wärmepumpe|klimaanlage|smart home|notdienst|kundendienst|rollladen|jalousie|glaserei|sonnenschutz|schlüsseldienst|solartechnik|solaranlage|energietechnik',
      'weak' => 'handwerk|installation|montage|reparatur|wartung|meisterbetrieb',
      'alltag' => 'beim Kunden oder auf der Baustelle', 'anliegen' => 'Anfragen zu Reparaturen, Wartung, Notdiensten und Angeboten', 'fragen' => 'Leistungen, Einsatzgebiet, Notdienst, Preise für Anfahrt und Termine',
      'rueckruf' => 'Name, Adresse, Art des Problems und Dringlichkeit', 'termin' => ['Einsatztermin mit Dringlichkeit', 'Kunden schildern das Problem, wählen Dringlichkeit und Wunschzeitraum und erhalten einen Terminvorschlag. Notfälle lassen sich nach vorn sortieren.'],
      'bew' => 'nach dem Einsatz', 'content' => 'Projekte, Tipps zur Wartung und Aktionen',
      'extra' => [['Wartungs-Erinnerung', 'Kunden mit Heizung, Anlage oder Prüfpflicht erhalten vor dem Fälligkeitstermin eine Erinnerung mit Terminvorschlag. Sie geben die Intervalle vor.', 'Planbare Folgeaufträge ohne eigenes Nachfassen.', 'Zusatz: Newsletter-System', 60, 'always'],
                 ['Anfrage mit Fotos und Eckdaten', 'Ein Formular oder WhatsApp-Assistent fragt Ort, Art des Problems und Fotos ab. Sie sehen vor der Anfahrt, was zu tun ist.', 'Weniger Rückfragen, bessere Einsatzplanung.', 'ab Paket LANDING START', 85, 'noform']]],

    'reinigung' => ['label' => 'Reinigung, Hausmeister und Gebäudeservice',
      'strong' => 'gebäudereinigung|glasreinigung|unterhaltsreinigung|reinigungsservice|reinigungsfirma|hausmeisterservice|hausmeister|winterdienst|schädlingsbekämpfung|fensterputz|treppenhausreinigung|büroreinigung|teppichreinigung|haushaltshilfe|haushaltsnahe|gebäudeservice|facility|objektbetreuung|desinfektion',
      'weak' => 'reinigung|sauber|hygiene',
      'alltag' => 'im Objekt oder unterwegs zum nächsten Einsatz', 'anliegen' => 'Anfragen zu Objekten, Reinigungsintervallen und Angeboten', 'fragen' => 'Leistungen, Intervalle, Einsatzgebiet und Ablauf eines Angebots',
      'rueckruf' => 'Name, Objekt, Größe, gewünschte Intervalle', 'termin' => ['Besichtigung und Probereinigung', 'Interessenten buchen eine Objektbesichtigung. Objektart, Fläche und Intervall liegen vorab vor, das Angebot geht schneller raus.'],
      'bew' => 'nach dem ersten Einsatz', 'content' => 'Leistungen, Saisonhinweise und freie Kapazitäten',
      'extra' => [['Angebotsanfrage mit Objektdaten', 'Ein Formular fragt Objektart, Fläche, Intervall und Wunschbeginn ab. Gewerbliche Anfragen kommen vorsortiert bei Ihnen an.', 'Schnellere Angebote, weniger Rückfragen.', 'ab Paket LANDING START', 85, 'noform']]],

    'garten' => ['label' => 'Garten- und Landschaftsbau',
      'strong' => 'garten|landschaftsbau|landschaftspflege|rasenpflege|heckenschnitt|baumpflege|baumfäll|gärtner|gärtnerei|baumschule|zaunbau|teichbau|poolbau|gartengestaltung|grünpflege|grünschnitt|pflaster|baumdienst|erdarbeiten',
      'weak' => 'rasen|hecke|pflanzen|beet',
      'alltag' => 'im Einsatz', 'anliegen' => 'Anfragen zu Gartenpflege, Gestaltung und Terminen', 'fragen' => 'Leistungen, Einsatzgebiet, Preise je Fläche und freie Termine',
      'rueckruf' => 'Name, Adresse, gewünschte Arbeiten und Wunschzeitraum', 'termin' => ['Aufmaß- und Beratungstermin', 'Interessenten wählen einen freien Termin für das Aufmaß und laden Fotos des Gartens hoch. Sie planen Routen sinnvoll.'],
      'bew' => 'nach Abschluss der Arbeiten', 'content' => 'Projekte mit Vorher-nachher und Saisontipps',
      'extra' => [['Saison-Erinnerung an Stammkunden', 'Vor Heckenschnitt, Rasenpflege und Winterdienst geht automatisch eine Erinnerung an Stammkunden. Sie bestimmen Zeitpunkt und Empfänger.', 'Frühe Buchungen und planbare Auslastung.', 'Zusatz: Newsletter-System', 62, 'always']]],

    'transport' => ['label' => 'Transport, Umzug und Entsorgung',
      'strong' => 'spedition|umzug|logistik|fuhrunternehm|transportunternehm|kurier|containerdienst|abschlepp|autokran|krandienst|schwertransport|kippertransport|baustofftransport|entrümpelung|haushaltsauflösung|taxi|fahrdienst|krankenfahrt|möbeltransport|busreise|reisebus|personenbeförderung|entsorgung|schrott',
      'weak' => 'transport|fahrt|lieferung|abholung|lkw',
      'alltag' => 'auf Tour', 'anliegen' => 'Anfragen zu Fahrten, Umzügen, Abholungen und Preisen', 'fragen' => 'Preise, Einsatzgebiet, Kapazitäten und freie Termine',
      'rueckruf' => 'Name, Start- und Zielort, Art und Menge, Wunschtermin', 'termin' => ['Fahrt- und Umzugstermin', 'Kunden nennen Start, Ziel, Umfang und Datum und erhalten einen Terminvorschlag. Sie sehen alle Anfragen geordnet nach Tag.'],
      'bew' => 'nach der Fahrt', 'content' => 'freie Kapazitäten und Leistungen',
      'extra' => [['Anfrage mit Start, Ziel und Umfang', 'Formular oder WhatsApp-Assistent fragt Orte, Etagen, Umfang und Wunschtermin ab. Sie erhalten vollständige Daten für das Angebot.', 'Weniger Rückfragen, schnellere Angebote.', 'ab Paket LANDING START', 85, 'noform']]],

    'kfz' => ['label' => 'Autowerkstatt und Fahrzeugservice',
      'strong' => 'kfz|autowerkstatt|autohaus|autohändler|reifen|reifendienst|tüv|hauptuntersuchung|inspektion|autopflege|aufbereitung|karosserie|autoglas|autoreparatur|autolackier|fahrzeugpflege|fahrzeugaufbereitung|gebrauchtwagen|unfallinstandsetzung|zweirad|motorrad|fahrradwerkstatt|werkstatt|autovermietung|mietwagen',
      'weak' => 'fahrzeug|pkw|bremsen|ölwechsel',
      'alltag' => 'unterm Auto', 'anliegen' => 'Terminwünsche, Preisfragen und Rückfragen zum Fahrzeug', 'fragen' => 'Preise, Leistungen, Dauer, Ersatzwagen und Öffnungszeiten',
      'rueckruf' => 'Name, Kennzeichen oder Modell, Anliegen und Wunschtermin', 'termin' => ['Werkstatttermin online', 'Kunden wählen Leistung (zum Beispiel Inspektion oder Reifenwechsel) und einen freien Termin. Bestätigung und Erinnerung gehen automatisch raus.'],
      'bew' => 'nach der Abholung des Fahrzeugs', 'content' => 'Aktionen, Saisonwechsel und Leistungen',
      'extra' => [['Erinnerung an TÜV, Reifenwechsel und Inspektion', 'Kunden erhalten zur passenden Zeit eine Erinnerung mit Terminvorschlag. Sie geben die Fristen und Texte vor.', 'Planbare Werkstattauslastung, Folgeaufträge ohne Nachtelefonieren.', 'Zusatz: Newsletter-System', 70, 'always']]],

    'beauty' => ['label' => 'Friseur, Kosmetik und Beauty',
      'strong' => 'friseur|frisör|haarstudio|barber|kosmetik|nagelstudio|nageldesign|wimpern|beautysalon|haarschnitt|fußpflege|podolog|tattoo|piercing|waxing|permanent make|sonnenstudio|friseursalon|haarverlängerung|visagist|brauen|lashes|microblading',
      'weak' => 'beauty|styling|haare|nägel',
      'alltag' => 'am Stuhl', 'anliegen' => 'Terminwünsche, Preisfragen und Umbuchungen', 'fragen' => 'Preise, Leistungen, Dauer, Terminwünsche und Öffnungszeiten',
      'rueckruf' => 'Name, gewünschte Leistung und Wunschzeit', 'termin' => ['Online-Terminbuchung nach Leistung', 'Kundinnen und Kunden wählen Leistung, Mitarbeiter und Zeit. Dauer wird automatisch eingeplant, Erinnerungen senken Terminausfälle.'],
      'bew' => 'nach dem Termin', 'content' => 'Neuheiten, Aktionen und Vorher-nachher',
      'extra' => [['Wiederbuchungs-Erinnerung', 'Nach der üblichen Zeit zwischen zwei Terminen geht eine freundliche Erinnerung mit Direktlink zur Buchung raus.', 'Stammkundschaft bleibt im Kalender, ohne dass Sie nachfragen müssen.', 'Zusatz: Newsletter-System', 68, 'always'],
                 ['Gutscheine online', 'Gutscheine lassen sich online kaufen und im Portal einlösen.', 'Zusätzlicher Verkaufsweg, besonders vor Feiertagen.', 'ab Paket BUSINESS WEB', 55, 'noshop']]],

    'praxis' => ['label' => 'Praxis, Therapie und Gesundheit',
      'strong' => 'arztpraxis|zahnarzt|zahnärzt|zahnmedizin|physiotherap|ergotherap|heilpraktik|logopäd|osteopath|orthopäd|hausarzt|kieferorthop|augenarzt|hautarzt|kinderarzt|frauenarzt|psycholog|psychotherap|krankengymnastik|podologie|hörgeräte|optiker|apotheke|sanitätshaus|massage|wellness|therapie|gesundheitszentrum|ernährungsberat',
      'weak' => 'praxis|patient|behandlung|sprechzeiten',
      'alltag' => 'in der Behandlung', 'anliegen' => 'Terminanfragen, Rezeptwünsche und Rückrufe', 'fragen' => 'Sprechzeiten, Leistungen, Kassen, Anfahrt und was zum Termin mitzubringen ist',
      'rueckruf' => 'Name, Geburtsdatum, Anliegen und bevorzugte Rückrufzeit', 'termin' => ['Online-Terminbuchung für die Praxis', 'Patienten wählen Terminart und freie Zeit. Bestätigung und Erinnerung gehen automatisch raus, Ausfälle werden weniger. Medizinische Auskünfte gibt der Assistent nicht.'],
      'bew' => 'nach der Behandlung', 'content' => 'Sprechzeiten-Änderungen, Urlaub und Gesundheitstipps',
      'extra' => [['Terminerinnerung gegen Ausfälle', 'Patienten erhalten vor dem Termin eine Erinnerung per E-Mail oder WhatsApp mit Möglichkeit zur Absage. Frei gewordene Termine lassen sich neu vergeben.', 'Weniger nicht wahrgenommene Termine, weniger Anrufe zur Umbuchung.', 'ab Paket ONE', 72, 'always']]],

    'pflege' => ['label' => 'Pflege und Betreuung',
      'strong' => 'pflegedienst|tagespflege|seniorenbetreu|seniorenheim|altenheim|pflegeheim|betreutes wohnen|häusliche pflege|24-stunden|krankenpflege|betreuung|haushaltsnahe dienst',
      'weak' => 'pflege|senioren|angehörige',
      'alltag' => 'im Einsatz bei Klienten', 'anliegen' => 'Anfragen von Angehörigen und Beratungswünsche', 'fragen' => 'Leistungen, Kosten, Kassen, Einsatzgebiet und Ablauf der Aufnahme',
      'rueckruf' => 'Name, Beziehung zur pflegebedürftigen Person, Anliegen und Dringlichkeit', 'termin' => ['Beratungstermin für Angehörige', 'Angehörige wählen einen Termin für ein Erstgespräch oder einen Hausbesuch. Dringlichkeit und Anliegen liegen vorab vor.'],
      'bew' => 'nach der Aufnahme, wenn Angehörige es wünschen', 'content' => 'Leistungen, Freigaben und Mitarbeitergesuche',
      'extra' => [['Erstkontakt vorsortieren', 'Der Assistent nimmt Anfragen auch außerhalb der Bürozeiten auf, fragt Dringlichkeit und Eckdaten ab und legt sie Ihnen zum Rückruf vor. Entscheidungen bleiben bei Ihnen.', 'Angehörige erreichen jemanden, Sie starten den Rückruf mit allen Angaben.', 'ab Paket BUSINESS', 75, 'always']]],

    'tier' => ['label' => 'Tiere, Reitbetrieb und Tierservice',
      'strong' => 'tierarzt|tierärzt|tierheim|tierpension|hundeschule|hundetraining|hundesalon|hundepension|katzenpension|reitschule|reitunterricht|ponyclub|reitverein|reiterhof|pferdepension|pensionspferde|pferdesport|pferdehof|stall|reitstall|reitanlage|tierbedarf|zoofachhandel|tiertrainer|tierphysio|pferd',
      'weak' => 'hund|katze|pony|reiten|tiere',
      'alltag' => 'im Stall oder mit den Tieren', 'anliegen' => 'Anfragen zu Kursen, Stunden, Pension und Terminen', 'fragen' => 'Preise, Kurse, freie Plätze, Pensionsbedingungen und Öffnungszeiten',
      'rueckruf' => 'Name, Tier, Anliegen und Wunschzeitraum', 'termin' => ['Buchung von Stunden, Kursen und Pensionszeiträumen', 'Kunden wählen Kurs, Stunde oder Pensionszeitraum und erhalten eine Bestätigung. Die Belegung ist für Sie auf einen Blick sichtbar.'],
      'bew' => 'nach dem Kurs oder Aufenthalt', 'content' => 'Kurstermine, freie Plätze und Neuigkeiten aus dem Betrieb',
      'extra' => [['Warteliste und freie Plätze', 'Wenn ein Kurs voll ist, tragen sich Interessenten auf eine Warteliste ein und werden benachrichtigt, sobald ein Platz frei wird.', 'Kurse bleiben ausgelastet, weniger Nachfragen am Telefon.', 'ab Paket LANDING', 66, 'always']]],

    'gastro' => ['label' => 'Gastronomie',
      'strong' => 'restaurant|gasthaus|gasthof|speisekarte|café|cafe|bistro|imbiss|pizzeria|biergarten|bäckerei|konditorei|eisdiele|kantine|hofcafé|landgasthof|gaststätte|tischreservierung|brauerei|weingut|winzer|weinstube|döner|burger|sushi|trattoria|steakhouse|frühstückscafé|mittagstisch',
      'weak' => 'speisen|getränke|küche|menü|frühstück|gerichte',
      'alltag' => 'in Küche und Service', 'anliegen' => 'Reservierungen und Fragen zu Karte, Öffnungszeiten und Allergenen', 'fragen' => 'Öffnungszeiten, Speisekarte, Allergene, freie Tische und Anfahrt',
      'rueckruf' => 'Name, Datum, Uhrzeit, Personenzahl', 'termin' => ['Tischreservierung online', 'Gäste reservieren Datum, Uhrzeit und Personenzahl und erhalten eine Bestätigung und eine Erinnerung. Weniger Ausfälle, volle Tische.'],
      'bew' => 'nach dem Besuch', 'content' => 'Tagesgerichte, Aktionen und Veranstaltungen',
      'extra' => [['Anfragen für Feiern und Gruppen', 'Ein Formular fragt Anlass, Personenzahl, Datum und Wünsche ab. Gruppenanfragen kommen vollständig bei Ihnen an.', 'Mehr planbare Großaufträge, weniger Rückfragen.', 'ab Paket LANDING START', 80, 'noform'],
                 ['Gutscheine online', 'Gäste kaufen Gutscheine online, Sie lösen sie im Portal ein.', 'Zusätzlicher Verkaufsweg, vor allem vor Weihnachten und Muttertag.', 'ab Paket BUSINESS WEB', 55, 'noshop']]],

    'bar' => ['label' => 'Bar, Club und Veranstaltungsort',
      'strong' => 'bar!|cocktailbar|cocktails|kneipe|pub!|lounge|nachtclub|disco|diskothek|club!|clubbing|partynächte|tanzlokal|tanzbar|shisha|weinbar|musikbar|livemusik|live-musik|dj!|karaoke|eventlocation|saalvermietung|partylocation|veranstaltungsraum|bierstube',
      'weak' => 'drinks|party|abend|musik|nacht|events|veranstaltung',
      'alltag' => 'hinter dem Tresen oder in der Vorbereitung', 'anliegen' => 'Reservierungen, Anfragen zu Feiern und Fragen zu Programm und Öffnungszeiten', 'fragen' => 'Öffnungszeiten (auch bei Events), Programm, Eintritt, Dresscode und Reservierung',
      'rueckruf' => 'Name, Anlass, Datum und Personenzahl', 'termin' => ['Tisch- und Gästelistenreservierung', 'Gäste reservieren Tisch oder Platz für ein Event, mit Datum und Personenzahl. Sie sehen die Auslastung je Abend und senden Erinnerungen.'],
      'bew' => 'am Tag nach dem Besuch', 'content' => 'Programm, Mottoabende und Änderungen der Öffnungszeiten',
      'extra' => [['Anfragen für private Feiern und Firmen-Events', 'Ein Formular oder der WhatsApp-Assistent fragt Anlass (Geburtstag, Firmenfeier, Motto-Party), Datum, Personenzahl und Budget ab. Sie sehen vollständige Anfragen und sagen mit einem Klick zu oder ab.', 'Mehr gebuchte Abende ohne langes Hin und Her, bessere Planung von Wochentagen.', 'ab Paket LANDING START', 88, 'noform'],
                 ['Programm und Öffnungszeiten immer aktuell', 'Änderungen bei Events werden einmal gepflegt und erscheinen auf Website, Google-Profil und in den Antworten des Assistenten. Ein Beitrag für Social Media wird vorbereitet.', 'Gäste stehen nicht vor geschlossener Tür, weniger Nachfragen „Habt ihr heute auf?“.', 'ab Paket ONE, Social Media als Zusatz', 78, 'always'],
                 ['Event-Newsletter und Gutscheine', 'Stammgäste erhalten das Programm per Newsletter. Gutscheine lassen sich online kaufen und an der Bar einlösen.', 'Stammpublikum wird erinnert, zusätzlicher Verkaufsweg für Geschenke.', 'Zusatz: Newsletter, ab BUSINESS WEB: Shop', 60, 'nonews']]],

    'event' => ['label' => 'Events, Catering und Feiern',
      'strong' => 'catering|partyservice|hochzeit|eventagentur|eventservice|veranstaltungstechnik|partyverleih|hüpfburg|festzelt|zeltverleih|eventplanung|hochzeitsplan|dj-service|alleinunterhalter|fotobox|candybar|fingerfood|buffet|eventcatering|mietmöbel|geschirrverleih|bühne',
      'weak' => 'feier|fest|veranstaltung|event',
      'alltag' => 'beim Aufbau oder unterwegs', 'anliegen' => 'Anfragen zu Terminen, Personenzahlen und Angeboten', 'fragen' => 'Verfügbarkeit, Preise, Leistungsumfang, Einsatzgebiet und Ablauf',
      'rueckruf' => 'Name, Anlass, Datum, Ort, Personenzahl', 'termin' => ['Terminprüfung und Beratungstermin', 'Interessenten nennen Datum und Anlass, Sie sehen sofort Verfügbarkeiten. Beratungstermine lassen sich online buchen.'],
      'bew' => 'nach dem Event', 'content' => 'Referenzen, Aktionen und freie Termine',
      'extra' => [['Anfrage mit Datum, Ort und Personenzahl', 'Formular oder WhatsApp-Assistent fragt Anlass, Datum, Ort, Personenzahl und Budget ab und prüft grob die Verfügbarkeit. Sie erhalten vollständige Anfragen.', 'Schnellere Angebote, weniger Rückfragen, Termine sind früh reserviert.', 'ab Paket LANDING START', 88, 'noform']]],

    'foto' => ['label' => 'Fotografie und Medien',
      'strong' => 'fotograf|fotostudio|fotografie|videograf|videoproduktion|filmproduktion|drohnenaufnahme|hochzeitsfotograf|portraitfotograf|businessfotograf|bildjournalist|kameramann',
      'weak' => 'shooting|bildbearbeitung|portfolio',
      'alltag' => 'beim Shooting', 'anliegen' => 'Anfragen zu Shootings, Paketen und Terminen', 'fragen' => 'Preise, Pakete, Dauer, Lieferzeit der Bilder und freie Termine',
      'rueckruf' => 'Name, Anlass, Datum, Ort', 'termin' => ['Shooting-Termine online buchen', 'Kunden wählen Paket und freien Termin, bekommen eine Bestätigung und Hinweise zur Vorbereitung.'],
      'bew' => 'nach Lieferung der Bilder', 'content' => 'neue Arbeiten und freie Termine',
      'extra' => [['Anfrage mit Anlass, Datum und Ort', 'Ein Formular fragt Anlass, Datum, Ort, gewünschte Leistung und Budget ab. Sie sehen auf einen Blick, ob der Termin passt.', 'Weniger Rückfragen, planbare Auslastung.', 'ab Paket LANDING START', 80, 'noform']]],

    'hotel' => ['label' => 'Hotel, Pension und Ferienunterkunft',
      'strong' => 'hotel|pension|ferienwohnung|ferienhaus|gästezimmer|übernachtung|unterkunft|bed\s?&\s?breakfast|zimmer buchen|campingplatz|ferienhof|urlaub auf dem bauernhof|gästehaus|herberge|wohnmobilstellplatz|apartment',
      'weak' => 'gäste|zimmer|buchung|anreise|urlaub|ferien',
      'alltag' => 'an der Rezeption oder im Haus', 'anliegen' => 'Zimmeranfragen, Preise und Fragen zu Anreise und Ausstattung', 'fragen' => 'Zimmer, Preise, Frühstück, Haustiere, Parken und An- und Abreisezeiten',
      'rueckruf' => 'Name, Zeitraum, Personenzahl und Zimmerwunsch', 'termin' => ['Direktbuchung mit freien Zeiträumen', 'Gäste sehen freie Zeiträume und fragen direkt an. Bestätigung und Reiseinformationen gehen automatisch raus, weniger Provision für Portale.'],
      'bew' => 'nach der Abreise', 'content' => 'Angebote, Saison und Veranstaltungen in der Umgebung',
      'extra' => [['Reiseinformationen vor der Anreise', 'Vor der Anreise erhalten Gäste automatisch Anreise, Check-in-Zeit und Hinweise. Nach dem Aufenthalt folgt die Bitte um eine Bewertung.', 'Weniger Rückfragen vor der Anreise, mehr Bewertungen.', 'ab Paket ONE', 72, 'always']]],

    'freizeit' => ['label' => 'Freizeit, Kultur und Erlebnis',
      'strong' => 'museum|kino|escape room|escaperoom|freizeitpark|bowling|minigolf|kegelbahn|zoo!|tierpark|erlebnisbad|schwimmbad|therme|theater|kleinkunst|konzert|ausstellung|galerie|outdoor|kanu|stadtführung|erlebnis|ausflugsziel|spielhalle|lasertag|trampolin|paintball|kartbahn',
      'weak' => 'eintritt|führung|besucher|ausflug',
      'alltag' => 'im laufenden Betrieb', 'anliegen' => 'Anfragen zu Tickets, Gruppen, Öffnungszeiten und Veranstaltungen', 'fragen' => 'Öffnungszeiten, Preise, Gruppenangebote, Barrierefreiheit und Anfahrt',
      'rueckruf' => 'Name, Gruppengröße, Wunschtermin', 'termin' => ['Ticket- und Zeitfensterbuchung', 'Besucher buchen Zeitfenster oder Ticket online, bekommen Bestätigung und Erinnerung. Sie sehen die Auslastung je Tag.'],
      'bew' => 'nach dem Besuch', 'content' => 'Programm, Aktionen und Öffnungszeiten',
      'extra' => [['Gruppen- und Geburtstagsanfragen', 'Ein Formular fragt Anlass, Gruppengröße, Datum und Wünsche ab. Anfragen kommen vollständig an.', 'Mehr gebuchte Gruppentermine, weniger Rückfragen.', 'ab Paket LANDING START', 80, 'noform']]],

    'fitness' => ['label' => 'Fitness, Sport und Kurse',
      'strong' => 'fitnessstudio|fitness|sportstudio|yoga|pilates|crossfit|personal trainer|tanzschule|kampfsport|kursplan|probetraining|sportverein|schwimmschule|tennis|golf|kletter|rehasport|gesundheitssport|boxen|judo|karate|zumba',
      'weak' => 'training|kurs|trainer|mitglied',
      'alltag' => 'im Training', 'anliegen' => 'Anfragen zu Probetraining, Kursen und Mitgliedschaft', 'fragen' => 'Kurszeiten, Preise, Mitgliedschaft, Probetraining und freie Plätze',
      'rueckruf' => 'Name, Wunschkurs und Rückrufzeit', 'termin' => ['Probetraining und Kursbuchung', 'Interessenten buchen Probetraining und Kurs online. Plätze, Warteliste und Erinnerungen laufen automatisch.'],
      'bew' => 'nach dem Probetraining', 'content' => 'Kursplan, neue Kurse und Aktionen',
      'extra' => [['Interessenten nachfassen', 'Wer ein Probetraining gebucht oder angefragt hat, erhält nach dem Termin automatisch eine Nachricht mit Angebot.', 'Mehr Probetrainings werden zu Mitgliedschaften, ohne dass Sie nachtelefonieren.', 'ab Paket ONE', 70, 'always']]],

    'bildung' => ['label' => 'Bildung, Schule und Betreuung',
      'strong' => 'fahrschule|nachhilfe|musikschule|sprachschule|volkshochschule|kindergarten|kita|krippe|tagesmutter|schule!|lernstudio|bildungsträger|weiterbildung|seminar|akademie|reitschule|malschule|kunstschule',
      'weak' => 'unterricht|schüler|kurs|lehrer',
      'alltag' => 'im Unterricht', 'anliegen' => 'Anfragen zu Kursen, Anmeldung und Terminen', 'fragen' => 'Kurse, Preise, Anmeldung, Starttermine und freie Plätze',
      'rueckruf' => 'Name, gewünschter Kurs und Rückrufzeit', 'termin' => ['Anmeldung und Schnuppertermin', 'Interessenten melden sich online an oder buchen einen Schnuppertermin. Bestätigung und Unterlagen gehen automatisch raus.'],
      'bew' => 'nach Kursende', 'content' => 'neue Kurse, Starttermine und freie Plätze',
      'extra' => [['Anmeldestrecke mit Unterlagen', 'Nach der Anmeldung erhalten Teilnehmer automatisch Bestätigung, Unterlagen und Erinnerung vor Kursbeginn.', 'Weniger Nachfragen zum Ablauf, weniger Ausfälle am ersten Tag.', 'ab Paket LANDING', 68, 'always']]],

    'handel' => ['label' => 'Handel und Fachgeschäft',
      'strong' => 'supermarkt|einzelhandel|fachgeschäft|boutique|fachhandel|blumenladen|blumengeschäft|floristik|geschenkartikel|onlineshop|online-shop|warenkorb|fleischtheke|feinkost|lebensmittel|wochenmarkt|tabakwaren|schreibwaren|buchhandlung|spielwaren|baumarkt|raumausstatter|möbelhaus|einrichtungshaus|futtermittel|landhandel|bauernladen|direktvermarkt|bioladen|reformhaus|schmuck|juwelier|uhren|metzgerei|fleischerei|hofladen|fahrradladen|elektrofachhandel',
      'weak' => 'sortiment|angebote der woche|verkauf|kaufen',
      'alltag' => 'im Laden', 'anliegen' => 'Fragen zu Sortiment, Preisen, Bestellungen und Öffnungszeiten', 'fragen' => 'Sortiment, Verfügbarkeit, Aktionen, Öffnungszeiten und Bestellung zur Abholung',
      'rueckruf' => 'Name, gewünschter Artikel und Rückrufzeit', 'termin' => ['Vorbestellung und Abholung', 'Kunden bestellen vor und holen zum Wunschzeitpunkt ab. Bestellungen kommen geordnet bei Ihnen an.'],
      'bew' => 'nach dem Einkauf oder der Abholung', 'content' => 'Angebote der Woche, Neuheiten und Saisonartikel',
      'extra' => [['Angebote der Woche automatisch verbreiten', 'Eine Aktion wird einmal gepflegt und erscheint auf Website, Google-Profil, Newsletter und in Social-Media-Beiträgen.', 'Kunden erfahren von Angeboten, ohne dass Sie überall einzeln schreiben.', 'Zusatz: Social Media, Newsletter', 70, 'always'],
                 ['Click and Collect', 'Kunden reservieren oder bestellen online und holen im Laden ab. Zahlung vor Ort oder online.', 'Mehr Umsatz außerhalb der Öffnungszeiten, weniger Anrufe zur Verfügbarkeit.', 'ab Paket BUSINESS WEB', 62, 'noshop']]],

    'industrie' => ['label' => 'Fertigung, Großhandel und B2B',
      'strong' => 'maschinenbau|metallverarbeitung|cnc|zerspanung|blechbearbeitung|schweißtechnik|kunststofftechnik|verpackung|großhandel|zulieferer|werkzeugbau|anlagenbau|fertigung|lohnfertigung|industrieservice|betriebsausstattung|bürobedarf|arbeitsschutz|laser',
      'weak' => 'produktion|b2b|industrie|serie|bauteile',
      'alltag' => 'in der Fertigung oder beim Kunden', 'anliegen' => 'Anfragen nach Angeboten, Mustern und Lieferzeiten', 'fragen' => 'Leistungen, Materialien, Stückzahlen, Lieferzeiten und Ansprechpartner',
      'rueckruf' => 'Firma, Ansprechpartner, Bauteil oder Produkt, Stückzahl und Wunschtermin', 'termin' => ['Beratungs- und Aufmaßtermin', 'Geschäftskunden buchen einen Termin für Beratung, Aufmaß oder Betriebsbesuch.'],
      'bew' => 'nach Abschluss eines Auftrags, mit Zustimmung des Kunden', 'content' => 'Referenzen, Kapazitäten und neue Verfahren',
      'extra' => [['Angebotsanfrage mit Zeichnung und Stückzahl', 'Ein Formular nimmt Zeichnung, Material, Stückzahl und Wunschtermin entgegen. Anfragen sind für ein Angebot sofort verwertbar.', 'Weniger Rückfragen, schnellere Angebote.', 'ab Paket LANDING START', 88, 'noform']]],

    'immobilien' => ['label' => 'Immobilien und Hausverwaltung',
      'strong' => 'immobilienmakler|immobilien|hausverwaltung|makler|wohnungsverwaltung|mietverwaltung|immobilienbewertung|baugenossenschaft|bauträger|wohnungsbau|vermietung|eigentumswohnung|grundstück|hausverkauf',
      'weak' => 'expose|besichtigung|miete|kauf',
      'alltag' => 'bei einer Besichtigung', 'anliegen' => 'Interessentenanfragen, Besichtigungswünsche und Fragen von Mietern', 'fragen' => 'Objektdaten, Besichtigungstermine, Unterlagen und Ablauf',
      'rueckruf' => 'Name, Objekt, Anliegen und Rückrufzeit', 'termin' => ['Besichtigungstermine online', 'Interessenten buchen einen Besichtigungstermin für ein Objekt. Sie sehen Gruppen und Reihenfolge.'],
      'bew' => 'nach Vermittlung oder Verwaltung eines Objekts', 'content' => 'neue Objekte und Marktinformationen',
      'extra' => [['Interessenten vorqualifizieren', 'Der Assistent fragt vor dem Termin Budget, Haushaltsgröße und Zeitrahmen ab. Sie sehen, wer wirklich passt.', 'Weniger Besichtigungen ohne Aussicht, schnellere Auswahl.', 'ab Paket BUSINESS', 80, 'always']]],

    'beratung' => ['label' => 'Beratung, Kanzlei und Finanzen',
      'strong' => 'steuerberat|kanzlei|rechtsanwalt|unternehmensberat|versicherung|coaching|buchhaltung|lohnbuchhaltung|finanzberat|architekt|ingenieurbüro|übersetz|gutachter|sachverständig|energieberat|notar|zahnlabor|anwalt|wirtschaftsprüf|finanzdienst|vermögensberat|steuerkanzlei',
      'weak' => 'beratung|mandant|dienstleist',
      'alltag' => 'im Mandantengespräch', 'anliegen' => 'Erstanfragen, Terminwünsche und Fragen zu Unterlagen', 'fragen' => 'Leistungen, Ablauf des Erstgesprächs, Kosten und benötigte Unterlagen',
      'rueckruf' => 'Name, Thema, Dringlichkeit und Rückrufzeit', 'termin' => ['Online-Terminbuchung für Erstgespräche', 'Interessenten wählen Thema und freien Termin. Unterlagenlisten gehen automatisch vorab raus. Rechtliche oder steuerliche Beratung gibt der Assistent nicht.'],
      'bew' => 'nach Abschluss eines Mandats, soweit berufsrechtlich zulässig', 'content' => 'Fristen, Gesetzesänderungen und Hinweise',
      'extra' => [['Mandatsanfragen vorqualifizieren', 'Der Assistent nimmt Thema und Dringlichkeit auf und legt sie Ihnen zusammen mit dem Terminvorschlag vor. Beratung bleibt bei Ihnen.', 'Weniger Telefonate ohne Mandatsaussicht, schnellerer Start passender Mandate.', 'ab Paket BUSINESS', 75, 'always'],
                 ['Fristen-Erinnerungen an Mandanten', 'Mandanten erhalten vor Stichtagen eine Erinnerung mit Checkliste. Sie geben Termine und Texte vor.', 'Weniger Nachfragen kurz vor Fristende.', 'Zusatz: Newsletter-System', 62, 'always']]],

    'agentur' => ['label' => 'IT, Agentur und Medien',
      'strong' => 'werbeagentur|webdesign|webagentur|it-service|it-dienstleist|systemhaus|computerservice|computerreparatur|softwareentwicklung|webentwicklung|druckerei|grafikdesign|mediengestaltung|marketingagentur|onlinemarketing|app-entwicklung|netzwerktechnik|edv',
      'weak' => 'agentur|software|digital|marketing',
      'alltag' => 'bei Kunden oder im Projekt', 'anliegen' => 'Projektanfragen, Supportfälle und Angebotswünsche', 'fragen' => 'Leistungen, Ablauf, Preise und Reaktionszeiten',
      'rueckruf' => 'Name, Firma, Anliegen und Dringlichkeit', 'termin' => ['Beratungstermin online', 'Interessenten buchen ein Erstgespräch. Projektangaben liegen vorab vor.'],
      'bew' => 'nach Projektabschluss', 'content' => 'Projekte, Know-how und freie Kapazitäten',
      'extra' => [['Supportanfragen sortieren', 'Der Assistent nimmt Supportfälle auf, sortiert nach Dringlichkeit und legt sie zur Bearbeitung vor.', 'Dringendes wird zuerst bearbeitet, Standardfragen beantwortet der Assistent.', 'ab Paket ONE', 70, 'always']]],

    'verein' => ['label' => 'Verein, Gemeinde und Organisation',
      'strong' => 'sportverein|schützenverein|feuerwehr|kirchengemeinde|gemeinde!|verein!|vereinsheim|förderverein|stiftung|kirche|dorfgemeinschaft|bürgerverein|heimatverein|musikverein|chor!|tafel!',
      'weak' => 'mitglied|ehrenamt|vorstand|spenden',
      'alltag' => 'ehrenamtlich unterwegs', 'anliegen' => 'Fragen zu Terminen, Mitgliedschaft und Veranstaltungen', 'fragen' => 'Termine, Mitgliedschaft, Kontakt zum Vorstand und Veranstaltungen',
      'rueckruf' => 'Name, Anliegen und Rückrufzeit', 'termin' => ['Anmeldung zu Veranstaltungen', 'Mitglieder und Gäste melden sich online zu Veranstaltungen an. Teilnehmerlisten entstehen automatisch.'],
      'bew' => 'nach Veranstaltungen', 'content' => 'Termine, Berichte und Aufrufe',
      'extra' => [['Mitgliederinformation per Newsletter', 'Termine und Berichte gehen einmal gepflegt an alle, die es möchten. Anmeldung und Abmeldung laufen automatisch.', 'Weniger Einzelnachrichten für den Vorstand.', 'Zusatz: Newsletter-System', 70, 'always']]],
  ];
}

/** Zuordnung von schema.org-Typen zu Branchen (stärkstes Signal, wenn die Seite sich selbst so beschreibt). */
function ki_ld_map(): array {
  return ['AutoRepair' => 'kfz', 'AutomotiveBusiness' => 'kfz', 'AutoDealer' => 'kfz', 'AutoWash' => 'kfz', 'MotorcycleRepair' => 'kfz', 'AutoRental' => 'kfz', 'Dentist' => 'praxis', 'Physician' => 'praxis', 'MedicalBusiness' => 'praxis', 'MedicalClinic' => 'praxis', 'Pharmacy' => 'praxis', 'Optician' => 'praxis', 'VeterinaryCare' => 'tier',
          'Restaurant' => 'gastro', 'FoodEstablishment' => 'gastro', 'Bakery' => 'gastro', 'CafeOrCoffeeShop' => 'gastro', 'BarOrPub' => 'bar', 'NightClub' => 'bar', 'FastFoodRestaurant' => 'gastro', 'Winery' => 'gastro', 'Brewery' => 'gastro', 'Hotel' => 'hotel', 'LodgingBusiness' => 'hotel', 'BedAndBreakfast' => 'hotel', 'Campground' => 'hotel',
          'HairSalon' => 'beauty', 'BeautySalon' => 'beauty', 'DaySpa' => 'beauty', 'NailSalon' => 'beauty', 'TattooParlor' => 'beauty', 'HealthClub' => 'fitness', 'SportsActivityLocation' => 'fitness', 'ExerciseGym' => 'fitness', 'SportsClub' => 'fitness',
          'Electrician' => 'handwerk', 'Plumber' => 'handwerk', 'HVACBusiness' => 'handwerk', 'Locksmith' => 'handwerk', 'RoofingContractor' => 'bau', 'GeneralContractor' => 'bau', 'HousePainter' => 'bau', 'HomeAndConstructionBusiness' => 'bau',
          'MovingCompany' => 'transport', 'LegalService' => 'beratung', 'AccountingService' => 'beratung', 'FinancialService' => 'beratung', 'InsuranceAgency' => 'beratung', 'Attorney' => 'beratung', 'Notary' => 'beratung', 'RealEstateAgent' => 'immobilien',
          'Store' => 'handel', 'GroceryStore' => 'handel', 'Florist' => 'handel', 'ClothingStore' => 'handel', 'HardwareStore' => 'handel', 'Butcher' => 'handel', 'GardenStore' => 'handel', 'PetStore' => 'tier',
          'AmusementPark' => 'freizeit', 'Museum' => 'freizeit', 'MovieTheater' => 'freizeit', 'EntertainmentBusiness' => 'freizeit', 'Zoo' => 'freizeit', 'School' => 'bildung', 'Preschool' => 'bildung', 'ChildCare' => 'bildung', 'DrivingSchool' => 'bildung', 'EventVenue' => 'bar', 'Photographer' => 'foto', 'ProfessionalService' => 'beratung', 'Organization' => ''];
}
