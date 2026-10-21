<?php
// Inhalte der Leistungsseiten (/leistungen/<slug>).
// "services" verweist auf IDs aus config.php: Preise und Dauer kommen immer von dort.

return [
    'balayage' => [
        'name' => 'Balayage',
        'title' => 'Balayage in Wettmar',
        'metaTitle' => 'Balayage in Wettmar & Burgwedel | AJ Atelier',
        'description' => 'Balayage bei AJ Atelier in Burgwedel-Wettmar: frei gemalte, natürliche Farbverläufe ab 250 €. Individuelle Beratung, Kostenvoranschlag vor Ort, online Termin buchen.',
        'teaser' => 'Frei Hand gemalte Farbverläufe, die natürlich herauswachsen.',
        'icon' => 'sparkle',
        'services' => ['f-balayage'],
        'intro' => 'Bei der Balayage wird die Aufhellung frei Hand auf die Haaroberfläche gemalt, statt in Folien gepackt. So entstehen weiche Übergänge vom Ansatz in die Längen, wie bei Haar, das die Sonne aufgehellt hat. Weil kein harter Ansatz entsteht, wächst eine Balayage sehr natürlich heraus.',
        'sections' => [
            ['Für wen eignet sich Balayage?', [
                'Balayage passt zu mittellangem und langem Haar, glatt wie lockig. Sie ist ideal, wenn Sie mehr Helligkeit und Bewegung möchten, ohne alle paar Wochen zum Nachfärben zu müssen.',
                'Ob karamellige Töne auf dunkelbraunem Haar oder kühles Beige-Blond auf hellem Haar: Welche Nuancen zu Ihrem Hautton und Ihrer Naturfarbe passen, besprechen wir vor jeder Behandlung ausführlich.',
            ]],
            ['Balayage oder Babylights?', [
                'Balayage wirkt weicher und sonniger, mit Fokus auf Längen und Spitzen. <a href="/leistungen/babylights">Babylights</a> sind hauchfeine Strähnen bis an den Ansatz und hellen gleichmäßiger auf. Oft kombinieren wir beides, zum Beispiel feine Babylights am Scheitel und eine Balayage in den Längen.',
            ]],
            ['Was kostet eine Balayage?', [
                'Eine Balayage beginnt bei uns ab 250 €. Der Endpreis hängt von Haarlänge, Haardichte und dem Material ab, das wir tatsächlich verbrauchen. Vor dem Start erhalten Sie einen individuellen Kostenvoranschlag, damit es keine Überraschungen gibt.',
                'Für Balayage planen Sie bitte rund 3,5 Stunden ein. Mit einem Glossing zum Abschluss wird das Ergebnis besonders harmonisch und glänzend.',
            ]],
        ],
        'steps' => [
            ['Beratung', 'Wir schauen uns Ihr Haar, Ihre Wunschfarbe und frühere Färbungen an.'],
            ['Aufhellung', 'Die Farbe wird frei Hand gemalt, Partie für Partie.'],
            ['Glossing', 'Ein Glossing gleicht Töne aus und sorgt für Glanz.'],
            ['Schnitt & Styling', 'Zum Schluss Pflege, auf Wunsch Spitzenschnitt und Föhnen.'],
        ],
        'faq' => [
            ['Wie lange hält eine Balayage?', 'Weil der Übergang zum Ansatz weich ist, sieht eine Balayage auch nach drei bis vier Monaten noch gepflegt aus. Viele Kundinnen frischen sie zwei- bis dreimal im Jahr auf, dazwischen reicht oft ein Glossing.'],
            ['Schadet Balayage meinen Haaren?', 'Jede Aufhellung beansprucht das Haar. Wir arbeiten deshalb mit einem Bond Treatment, das die Haarstruktur während der Behandlung schützt, und empfehlen passende Pflege für zu Hause.'],
            ['Muss ich bei der Online-Buchung schon bezahlen?', 'Sie können vor Ort bezahlen. Wer lieber online bucht und zahlt, leistet über PayPal eine Anzahlung von 50 €, die vollständig verrechnet wird.'],
        ],
        'related' => ['babylights', 'farbe', 'pflege'],
    ],

    'babylights' => [
        'name' => 'Babylights',
        'title' => 'Babylights in Wettmar',
        'metaTitle' => 'Babylights in Wettmar & Burgwedel | AJ Atelier',
        'description' => 'Babylights bei AJ Atelier in Burgwedel-Wettmar: hauchfeine Strähnen für ein natürliches, helles Ergebnis ab 250 €. Beratung inklusive, online Termin buchen.',
        'teaser' => 'Hauchfeine Strähnen für helles, natürliches Haar.',
        'icon' => 'sparkle',
        'services' => ['f-babylights'],
        'intro' => 'Babylights sind sehr feine Strähnen, die bis nah an den Ansatz gesetzt werden. Sie erinnern an die hellen Spitzen, die Kinderhaar im Sommer bekommt, daher der Name. Das Ergebnis wirkt gleichmäßig aufgehellt und trotzdem natürlich, ohne sichtbare Streifen.',
        'sections' => [
            ['Für wen eignen sich Babylights?', [
                'Babylights sind ideal, wenn Sie heller werden möchten, ohne dass man den Unterschied als „gefärbt“ wahrnimmt. Sie eignen sich für jede Haarlänge, auch für kürzere Schnitte, bei denen eine Balayage kaum Platz hätte.',
                'Auch wer graue Haare sanft kaschieren möchte, ist mit Babylights gut beraten: Die feinen hellen Strähnen lassen nachwachsendes Grau weniger auffallen.',
            ]],
            ['Unterschied zu klassischen Strähnchen', [
                'Klassische Strähnen sind breiter und kontrastreicher. Bei Babylights nehmen wir nur sehr wenig Haar pro Strähne auf und arbeiten dafür mit vielen Folien. Das braucht Zeit und Präzision, ergibt aber einen weichen, gleichmäßigen Effekt.',
            ]],
            ['Preis und Dauer', [
                'Babylights beginnen ab 250 €. Der genaue Preis richtet sich nach Haarlänge, Dichte und Materialverbrauch. Sie erhalten vorab einen Kostenvoranschlag. Planen Sie rund 3,5 Stunden ein.',
            ]],
        ],
        'steps' => [
            ['Beratung', 'Wir legen Helligkeit, Ton und Strähnenstärke gemeinsam fest.'],
            ['Feine Strähnen', 'Partie für Partie werden die Babylights in Folien gesetzt.'],
            ['Einwirkzeit & Glossing', 'Danach gleicht ein Glossing den Farbton aus.'],
            ['Styling', 'Pflege, Föhnen und auf Wunsch ein frischer Schnitt.'],
        ],
        'faq' => [
            ['Wie oft muss ich Babylights auffrischen?', 'Weil die Strähnen bis an den Ansatz gehen, ist das Nachwachsen etwas eher sichtbar als bei einer Balayage. Die meisten Kundinnen kommen alle drei bis vier Monate.'],
            ['Kann ich Babylights und Balayage kombinieren?', 'Ja, das ist sogar sehr beliebt: feine Babylights am Oberkopf und eine weiche Balayage in den Längen. Sprechen Sie uns bei der Beratung darauf an.'],
        ],
        'related' => ['balayage', 'farbe', 'pflege'],
    ],

    'damenhaarschnitt' => [
        'name' => 'Damenhaarschnitt',
        'title' => 'Damenhaarschnitt & Styling',
        'metaTitle' => 'Damenhaarschnitt in Wettmar | Friseur AJ Atelier Burgwedel',
        'description' => 'Damenhaarschnitt bei AJ Atelier in Burgwedel-Wettmar: Waschen, Schneiden & Föhnen ab 55 €, Waschen & Föhnen ab 35 €. Feste Preise nach Haarlänge, online buchen.',
        'teaser' => 'Schnitte, die zu Ihnen und Ihrem Alltag passen.',
        'icon' => 'scissors',
        'services' => ['d-wsf-kurz', 'd-wsf-mittel', 'd-wsf-lang', 'd-wf-kurz', 'd-wf-mittel', 'd-wf-lang'],
        'intro' => 'Ein guter Schnitt sieht nicht nur am ersten Tag gut aus, sondern auch dann, wenn Sie Ihr Haar morgens selbst stylen. Deshalb fragen wir vor dem Schneiden, wie viel Zeit Sie sich für Ihre Haare nehmen möchten, wie Ihr Haar fällt und was Sie bisher gestört hat.',
        'sections' => [
            ['Feste Preise nach Haarlänge', [
                'Bei Damenhaarschnitten gelten bei uns feste Preise, gestaffelt nach kurz, mittel und lang. So wissen Sie schon bei der Buchung, was der Termin kostet, und können online direkt mit PayPal bezahlen.',
                'Kurz bedeutet ungefähr bis zum Kinn, mittel bis zur Schulter, lang alles darüber hinaus. Im Zweifel buchen Sie die längere Variante, dann ist ausreichend Zeit eingeplant.',
            ]],
            ['Nur Waschen & Föhnen', [
                'Vor einem Anlass, einem Fototermin oder einfach zum Verwöhnen: Waschen und Föhnen ohne Schnitt bieten wir ab 35 € an. Für aufwendigere Frisuren wie Hochsteckfrisuren gibt es eine <a href="/leistungen/hochsteckfrisuren">eigene Leistung</a>.',
            ]],
        ],
        'steps' => [
            ['Beratung', 'Wunsch, Haarstruktur und Alltag besprechen.'],
            ['Waschen & Pflege', 'Haarwäsche mit passender Pflege.'],
            ['Schnitt', 'Präzise geschnitten, passend zu Gesichtsform und Fall.'],
            ['Föhnen & Styling', 'Mit Tipps, wie Sie das Styling zu Hause hinbekommen.'],
        ],
        'faq' => [
            ['Welche Länge soll ich bei der Buchung wählen?', 'Kurz reicht etwa bis zum Kinn, mittel bis zur Schulter, lang ist alles darüber hinaus. Wenn Sie unsicher sind, wählen Sie die längere Variante.'],
            ['Kann ich Schnitt und Farbe in einem Termin buchen?', 'Ja. Wählen Sie bei der Online-Buchung einfach mehrere Leistungen aus, zum Beispiel Ansatzfarbe und Waschen, Schneiden & Föhnen. Die Dauer wird automatisch zusammengerechnet.'],
        ],
        'related' => ['hochsteckfrisuren', 'farbe', 'pflege'],
    ],

    'hochsteckfrisuren' => [
        'name' => 'Hochsteckfrisuren',
        'title' => 'Hochsteckfrisuren für besondere Anlässe',
        'metaTitle' => 'Hochsteckfrisur Hochzeit & Anlass in Wettmar | AJ Atelier',
        'description' => 'Hochsteckfrisuren für Hochzeit, Abiball und Feiern bei AJ Atelier in Burgwedel-Wettmar. Ab 55 €, individuelle Beratung, Termin online buchen.',
        'teaser' => 'Für Hochzeit, Abiball, Konfirmation und Feiern.',
        'icon' => 'flower',
        'services' => ['d-hochstecken'],
        'intro' => 'Ob Hochzeit, Abiball, Konfirmation oder Geburtstag: Eine Hochsteckfrisur soll den ganzen Tag halten und auf Fotos gut aussehen. Wir stecken Ihr Haar so, dass es zu Kleid, Gesichtsform und Anlass passt, von locker-romantisch bis elegant und streng.',
        'sections' => [
            ['So bereiten Sie sich vor', [
                'Waschen Sie Ihr Haar am Vortag, nicht am Morgen des Termins. Leicht „griffiges“ Haar hält Nadeln und Volumen besser. Bringen Sie gern Fotos von Frisuren mit, die Ihnen gefallen, und ein Bild Ihres Outfits.',
                'Haarschmuck wie Spangen, Blüten oder ein Schleier wird am besten gleich mit eingearbeitet. Bringen Sie ihn deshalb zum Termin mit.',
            ]],
            ['Für Brautfrisuren', [
                'Für Hochzeiten empfehlen wir einen Probetermin einige Wochen vorher. So können wir die Frisur in Ruhe ausprobieren und am großen Tag zügig und entspannt arbeiten. Für Probe und Termin buchen Sie jeweils die Leistung „Hochstecken“.',
            ]],
            ['Preis', [
                'Hochsteckfrisuren beginnen ab 55 €. Der Preis hängt von Haarlänge und Aufwand ab. Bei der Online-Buchung können Sie eine Anzahlung von 20 € per PayPal leisten oder komplett vor Ort bezahlen.',
            ]],
        ],
        'faq' => [
            ['Wie lange hält eine Hochsteckfrisur?', 'Mit der richtigen Vorbereitung und gutem Halt hält eine Hochsteckfrisur problemlos einen ganzen Tag und eine lange Nacht.'],
            ['Kann ich mehrere Personen anmelden, etwa Brautjungfern?', 'Ja. Buchen Sie bitte für jede Person einen eigenen Termin, oder rufen Sie uns an, dann planen wir die Termine gemeinsam.'],
        ],
        'related' => ['damenhaarschnitt', 'augenbrauen-wimpern', 'pflege'],
    ],

    'herren' => [
        'name' => 'Herren & Bart',
        'title' => 'Herrenhaarschnitt & Bart',
        'metaTitle' => 'Herrenfriseur Wettmar & Burgwedel | Haarschnitt & Bart | AJ Atelier',
        'description' => 'Herrenhaarschnitt inkl. Waschen & Styling für 45 €, Maschinenschnitt 30 €, Bart schneiden 20 € bei AJ Atelier in Burgwedel-Wettmar. Termin online buchen.',
        'teaser' => 'Klassischer Herrenschnitt, Maschinenschnitt und Bartpflege.',
        'icon' => 'razor',
        'services' => ['h-schnitt', 'h-maschine', 'h-bart'],
        'intro' => 'Ob klassischer Schnitt mit der Schere, Fade oder kurzer Maschinenschnitt: Im AJ Atelier bekommen Männer einen sauberen Schnitt zu festen Preisen. Den Termin buchen Sie online in wenigen Klicks, auch abends oder am Wochenende.',
        'sections' => [
            ['Herrenschnitt inklusive Waschen & Styling', [
                'Der Herrenschnitt für 45 € enthält Haarwäsche, Schnitt mit Schere und Maschine sowie Styling. Wir besprechen vorher, wie kurz es an den Seiten werden soll und wie Sie Ihre Haare im Alltag tragen.',
            ]],
            ['Maschinenschnitt', [
                'Wenn es schnell gehen soll und Sie Ihre Haare gleichmäßig kurz tragen, ist der Maschinenschnitt für 30 € die richtige Wahl. Dauer: rund 20 Minuten.',
            ]],
            ['Bart schneiden', [
                'Konturen, Länge und Übergänge: Wir bringen Ihren Bart für 20 € in Form. Kombiniert mit dem Haarschnitt wählen Sie bei der Online-Buchung einfach beide Leistungen aus.',
            ]],
        ],
        'faq' => [
            ['Kann ich Haarschnitt und Bart zusammen buchen?', 'Ja. Wählen Sie im Buchungssystem „Herrenschnitt“ und „Bart schneiden“ aus. Die Zeit wird automatisch zusammengerechnet.'],
            ['Wie oft sollte ich zum Nachschneiden kommen?', 'Bei kurzen Schnitten mit Übergängen empfehlen wir alle drei bis vier Wochen, bei längeren Schnitten alle sechs bis acht Wochen.'],
        ],
        'related' => ['damenhaarschnitt', 'pflege', 'augenbrauen-wimpern'],
    ],

    'farbe' => [
        'name' => 'Färben & Blondierung',
        'title' => 'Haare färben & Blondierung',
        'metaTitle' => 'Haare färben & blondieren in Wettmar | AJ Atelier Burgwedel',
        'description' => 'Ansatzfarbe ab 55 €, Färben ab 50 €, Glossing ab 22 €, Blondierung ab 55 € und Color Correction bei AJ Atelier in Burgwedel-Wettmar. Individueller Kostenvoranschlag.',
        'teaser' => 'Ansatz, Komplettfarbe, Glossing, Blond und Farbkorrektur.',
        'icon' => 'drop',
        'services' => ['f-ansatz', 'f-faerben', 'f-glossing', 'f-blondierung', 'f-correction'],
        'intro' => 'Farbe ist Vertrauenssache. Bevor wir färben, schauen wir uns an, was Ihr Haar schon erlebt hat: frühere Färbungen, Aufhellungen, Tönungen. Erst dann entscheiden wir gemeinsam, wie wir Ihre Wunschfarbe am schonendsten erreichen.',
        'sections' => [
            ['Ansatzfarbe und Komplettfärbung', [
                'Bei der Ansatzfarbe färben wir nur das nachgewachsene Haar, damit Längen und Spitzen nicht unnötig belastet werden. Bei einer Komplettfärbung bringen wir Ansatz und Längen in einen einheitlichen Ton, zum Beispiel bei einem Farbwechsel.',
            ]],
            ['Glossing', [
                'Ein Glossing ist eine Tönung, die Farbe auffrischt, Gelbstich neutralisiert und viel Glanz gibt. Es eignet sich als Abschluss nach einer Aufhellung oder als schnelle Auffrischung zwischen zwei Farbterminen.',
            ]],
            ['Blondierung', [
                'Für helles Blond muss das natürliche Pigment aus dem Haar gelöst werden. Wir hellen deshalb schrittweise und mit Bond Treatment auf. Wenn das gewünschte Blond nicht in einem Termin erreichbar ist, ohne das Haar zu überfordern, sagen wir Ihnen das ehrlich und planen mehrere Etappen.',
            ]],
            ['Color Correction', [
                'Grünstich, ungleichmäßige Farbe nach dem Selbstfärben oder ein zu dunkles Ergebnis: Eine Farbkorrektur ist individuell und lässt sich nicht pauschal kalkulieren. Buchen Sie zuerst den Beratungstermin. Danach erhalten Sie einen konkreten Plan und Preis.',
            ]],
            ['Wie berechnen sich die Farbpreise?', [
                'Alle Farbpreise werden nach Aufwand und Verbrauch berechnet. Die genannten Preise sind Startpreise. Vor Ort erstellen wir einen individuellen Kostenvoranschlag, bevor wir beginnen.',
            ]],
        ],
        'faq' => [
            ['Kann ich graue Haare abdecken lassen?', 'Ja. Für eine vollständige Grauabdeckung eignet sich die Ansatzfarbe bzw. Komplettfärbung. Wer das Grau lieber sanft kaschieren möchte, ist mit Babylights oder einem Glossing gut beraten.'],
            ['Ich habe mir die Haare selbst gefärbt. Ist das ein Problem?', 'Nein, sagen Sie es uns nur bei der Beratung. Heimfärbungen beeinflussen, wie neue Farbe angenommen wird. Bei größeren Abweichungen ist eine Color Correction der richtige Weg.'],
        ],
        'related' => ['balayage', 'babylights', 'pflege'],
    ],

    'pflege' => [
        'name' => 'Pflege & Bond Treatment',
        'title' => 'Haarpflege & Bond Treatment',
        'metaTitle' => 'Haarpflege & Bond Treatment in Wettmar | AJ Atelier',
        'description' => 'Haarpflege ab 15 € und Bond Treatment ab 20 € bei AJ Atelier in Burgwedel-Wettmar. Für kräftiges, glänzendes Haar, auch zusätzlich zu Farbe oder Schnitt.',
        'teaser' => 'Für gesundes, kräftiges und glänzendes Haar.',
        'icon' => 'leaf',
        'services' => ['p-haarpflege', 'p-bond'],
        'intro' => 'Gesundes Haar ist die Grundlage für jede schöne Farbe und jeden Schnitt. Mit gezielter Pflege im Salon geben wir trockenem, strapaziertem oder gefärbtem Haar zurück, was ihm fehlt.',
        'sections' => [
            ['Bond Treatment', [
                'Beim Aufhellen und Färben werden Verbindungen in der Haarstruktur gelöst. Ein Bond Treatment hilft, diese inneren Verbindungen zu stärken. Das Haar bricht weniger, fühlt sich wieder kräftiger an und behält seine Elastizität.',
                'Wir setzen das Bond Treatment begleitend bei Blondierung, Balayage und Babylights ein. Sie können es aber auch als eigene Behandlung buchen, wenn Ihr Haar eine Kur braucht.',
            ]],
            ['Haarpflege im Salon', [
                'Je nach Haarzustand wählen wir eine Pflege mit Feuchtigkeit, Glanz oder Repair-Wirkung. Die Haarpflege lässt sich gut mit jedem Schnitt- oder Föhntermin kombinieren.',
            ]],
        ],
        'faq' => [
            ['Kann ich eine Pflege zum Haarschnitt dazubuchen?', 'Ja. Wählen Sie im Buchungssystem einfach Ihren Haarschnitt und zusätzlich Haarpflege oder Bond Treatment.'],
            ['Wie oft ist ein Bond Treatment sinnvoll?', 'Bei regelmäßig aufgehelltem Haar empfehlen wir es bei jeder Aufhellung. Als Kur bei strapaziertem Haar reichen oft einige Anwendungen im Abstand von wenigen Wochen.'],
        ],
        'related' => ['farbe', 'balayage', 'damenhaarschnitt'],
    ],

    'augenbrauen-wimpern' => [
        'name' => 'Augenbrauen & Wimpern',
        'title' => 'Augenbrauen & Wimpern',
        'metaTitle' => 'Augenbrauen zupfen & färben, Wimpern färben in Wettmar | AJ Atelier',
        'description' => 'Augenbrauen zupfen ab 15 €, Augenbrauen färben ab 15 €, Wimpern färben 16 € bei AJ Atelier in Burgwedel-Wettmar. Auch ideal zusammen mit dem Friseurtermin.',
        'teaser' => 'Zupfen und Färben für einen klaren Rahmen.',
        'icon' => 'eye',
        'services' => ['b-zupfen', 'b-faerben', 'b-wimpern'],
        'intro' => 'Augenbrauen rahmen das Gesicht. Schon kleine Korrekturen an Form und Farbe lassen den Blick wacher und das Gesicht harmonischer wirken. Bei AJ Atelier können Sie Brauen und Wimpern ganz einfach mit Ihrem Friseurtermin verbinden.',
        'sections' => [
            ['Augenbrauen zupfen', [
                'Wir formen Ihre Brauen passend zu Gesichtsform und Augenpartie, natürlich und nicht zu dünn. Ab 15 €, Dauer rund 15 Minuten.',
            ]],
            ['Augenbrauen und Wimpern färben', [
                'Helle oder ergraute Brauen und Wimpern wirken nach dem Färben definierter, und Sie sparen sich morgens Zeit beim Schminken. Augenbrauen färben ab 15 €, Wimpern färben 16 €.',
            ]],
        ],
        'faq' => [
            ['Wie lange hält die Farbe bei Brauen und Wimpern?', 'Je nach Haarwachstum und Pflege etwa drei bis sechs Wochen.'],
            ['Kann ich das zum Haarschnitt dazubuchen?', 'Ja, wählen Sie bei der Online-Buchung einfach mehrere Leistungen aus.'],
        ],
        'related' => ['hochsteckfrisuren', 'damenhaarschnitt', 'pflege'],
    ],
];
