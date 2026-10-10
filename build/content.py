# -*- coding: utf-8 -*-
"""Inhalte der Website. Texte hier ändern, dann `python3 build/build.py` ausführen.

Verlinken im Text: [[leistungen/wertgutachten|Wertgutachten]] (Adresse ohne Slashes am Rand).
Absätze sind Strings, Listen sind ("ul", [...]) oder ("ol", [...]).
"""

BIZ = {
    "domain": "https://psschneider.de",
    "name": "PS Schneider",
    "legal_name": "PS Schneider – Sachverständiger für Fahrzeugtechnik",
    "person": "Patric Schneider",
    "role": "Sachverständiger für Fahrzeugtechnik",
    "craft": "Kraftfahrzeugtechniker-Meister",
    "phone_display": "0172 517 81 50",
    "phone_tel": "+491725178150",
    "phone_copy": "0172 5178150",
    "email": "info@psschneider.de",
    "street": "Im Röthel 43",
    "zip": "29225",
    "city": "Celle",
}

# Reihenfolge = Reihenfolge in Navigation, Karten und Sitemap
SERVICES = [
    {
        "slug": "leistungen/haftpflichtschaden-gutachten",
        "short": "Haftpflichtschaden-Gutachten",
        "tag": "Unfallschaden",
        "icon": "car",
        "title": "Haftpflichtschaden-Gutachten Celle | PS Schneider",
        "desc": "Haftpflichtschaden-Gutachten nach unverschuldetem Unfall in Celle: unabhängiger Kfz-Sachverständiger, Kosten in der Regel durch die gegnerische Versicherung.",
        "h1": "Haftpflichtschaden-Gutachten in Celle",
        "lede": "Nach einem unverschuldeten Unfall dokumentiere ich alle Schäden, beziffere Ihre Ansprüche und liefere das Gutachten, das Sie gegenüber der gegnerischen Versicherung brauchen.",
        "card": "Nach einem unverschuldeten Unfall: alle Schäden dokumentiert, inklusive Reparaturdauer und Wertminderung. Bei Totalschaden mit Restwert und Wiederbeschaffungswert. Die Kosten trägt in der Regel die gegnerische Versicherung.",
        "sections": [
            {"h2": "Wann ein Haftpflichtschaden-Gutachten sinnvoll ist", "body": [
                "Wurde Ihr Fahrzeug bei einem Unfall beschädigt, für den ein anderer verantwortlich ist, richten sich Ihre Ansprüche gegen die Haftpflichtversicherung des Unfallverursachers. Damit diese Ansprüche vollständig und nachvollziehbar beziffert sind, brauchen Sie mehr als einen Kostenvoranschlag.",
                "Ein unabhängiges Gutachten ist besonders wichtig, wenn der Schaden über eine Bagatelle hinausgeht, wenn ein Totalschaden droht, wenn die Haftung strittig ist oder wenn die gegnerische Versicherung Ihre Forderung kürzen will.",
            ]},
            {"h2": "Was das Gutachten enthält", "body": [
                ("ul", [
                    "Alle Schäden, schriftlich und mit Fotos dokumentiert",
                    "Die voraussichtlichen Reparaturkosten",
                    "Die geschätzte Reparaturdauer und damit die Ausfallzeit",
                    "Die zu erwartende Wertminderung",
                    "Bei Totalschaden: Restwert und Wiederbeschaffungswert",
                    "Hinweise auf Vor- und Altschäden",
                ]),
                "Damit haben Sie eine verlässliche Grundlage für Ihre Entscheidung: reparieren lassen, fiktiv abrechnen oder das Fahrzeug verkaufen. Zugleich bietet das Gutachten rechtliche Absicherung.",
            ]},
            {"h2": "So läuft es ab", "body": [
                ("ol", [
                    "Sie rufen an oder schreiben mir. Wir klären kurz, was passiert ist.",
                    "Ich besichtige Ihr Fahrzeug nach Terminabsprache und erfasse alle Schäden.",
                    "Ich erstelle das Gutachten zügig, damit die Wartezeit bis zur Reparatur oder zum Ersatzfahrzeug kurz bleibt.",
                    "Sie legen das Gutachten der gegnerischen Versicherung vor oder geben es an Ihren Rechtsanwalt weiter.",
                ]),
            ]},
            {"h2": "Wer zahlt das Gutachten?", "body": [
                "Im Haftpflichtfall werden die Gutachtenkosten dem Schaden zugerechnet. In der Regel trägt sie die Versicherung des Unfallverursachers. Sie haben das Recht, den Sachverständigen selbst zu wählen. Versicherungen verweisen gern auf einen Kostenvoranschlag und darauf, dass Sie den Sachverständigen selbst bezahlen müssten. Im Haftpflichtfall ist das in der Regel nicht so.",
                ("callout", "Bei reinen Bagatellschäden, in der Rechtsprechung meist bis etwa 750 bis 1.000 Euro, lohnt sich ein Gutachten oft nicht. Das sage ich Ihnen ehrlich, bevor Sie einen Auftrag erteilen."),
            ]},
        ],
        "faq": [
            ("Muss ich den Gutachter der gegnerischen Versicherung akzeptieren?",
             "Nein. Als Geschädigter dürfen Sie einen unabhängigen Sachverständigen Ihrer Wahl beauftragen. Ein von der Versicherung beauftragter Gutachter arbeitet in deren Auftrag."),
            ("Kann ich mir den Schaden auszahlen lassen, ohne zu reparieren?",
             "Ja. Diese fiktive Abrechnung ist bei Bagatellschäden, älteren Fahrzeugen oder Eigenreparatur üblich. Das Gutachten beziffert dabei auch die Wertminderung, die beim späteren Verkauf relevant sein kann."),
            ("Was passiert bei einem Totalschaden?",
             "Dann ermittle ich Restwert und Wiederbeschaffungswert. Auf dieser Grundlage entscheiden Sie, ob sich eine Reparatur lohnt oder ein Verkauf sinnvoller ist."),
            ("Wie schnell erhalte ich das Gutachten?",
             "Den Besichtigungstermin vereinbare ich kurzfristig und erstelle das Gutachten zügig, damit die Wartezeit bis zur Reparatur oder zum Ersatzfahrzeug möglichst kurz bleibt."),
        ],
        "related": ["leistungen/restwertermittlung", "gruende-fuer-ein-gutachten", "unfall-checkliste"],
    },
    {
        "slug": "leistungen/beweissicherungsgutachten",
        "short": "Beweissicherungsgutachten",
        "tag": "Gebrauchtwagen und Werkstatt",
        "icon": "search",
        "title": "Beweissicherungsgutachten Kfz Celle | PS Schneider",
        "desc": "Beweissicherungsgutachten in Celle: verschwiegene Vorschäden, mangelhafte Reparatur oder Streit mit Werkstatt und Verkäufer neutral dokumentieren lassen.",
        "h1": "Beweissicherungsgutachten für Kfz in Celle",
        "lede": "Nach dem Gebrauchtwagenkauf oder einer Reparatur stimmt etwas nicht? Ich halte den Zustand Ihres Fahrzeugs neutral fest, damit Sie gegenüber Verkäufer oder Werkstatt abgesichert sind.",
        "card": "Zieht das Auto nach links oder stimmen die Spaltmaße nicht? Verschwiegene Vorschäden und mangelhafte Reparaturen werden neutral festgehalten, damit Sie gegenüber Verkäufer oder Werkstatt abgesichert sind.",
        "sections": [
            {"h2": "Typische Anlässe", "body": [
                "Nach dem Erwerb eines Gebrauchtwagens oder nach einer Reparatur stellt sich oft heraus, dass etwas nicht in Ordnung ist. Dann kommt schnell der Verdacht auf, dass Vor- oder Altschäden verschwiegen oder nur unzureichend behoben wurden.",
                ("ul", [
                    "Das Fahrzeug zieht beim Fahren leicht nach links",
                    "Die Spaltmaße der Türen oder Klappen sind ungleichmäßig",
                    "Verdacht auf verschwiegene Vor- oder Altschäden nach dem Kauf",
                    "Eine Reparatur wurde nicht oder nur mangelhaft ausgeführt",
                    "Streit mit der Werkstatt über Umfang oder Qualität der Arbeiten",
                ]),
            ]},
            {"h2": "Warum Sie nicht warten sollten", "body": [
                "Ein Mangel ist nicht nur ärgerlich. Er kann Folgeschäden verursachen und im schlimmsten Fall zu Motorschäden oder sogar zu Unfällen führen. Je früher der Zustand neutral dokumentiert ist, desto besser lässt sich später nachweisen, was vorlag.",
                ("callout", "Lassen Sie am Fahrzeug möglichst nichts verändern, bevor es begutachtet wurde. Heben Sie Kaufvertrag, Rechnungen und Schriftverkehr auf."),
            ]},
            {"h2": "Was ich für Sie festhalte", "body": [
                ("ul", [
                    "Den aktuellen Zustand des Fahrzeugs, schriftlich und mit Fotos",
                    "Auffälligkeiten, die auf Vor- oder Altschäden hindeuten",
                    "Mängel an durchgeführten Reparaturen",
                    "Mögliche Folgen und Risiken, etwa für Fahrsicherheit oder Folgeschäden",
                ]),
                "Das Gutachten ist neutral und kann im Streitfall als Beweismittel vorgelegt werden. Sie haben damit eine belastbare Grundlage für das Gespräch mit Verkäufer oder Werkstatt und für Ihren Rechtsanwalt.",
            ]},
        ],
        "faq": [
            ("Wer trägt die Kosten eines Beweissicherungsgutachtens?",
             "Anders als bei einem unverschuldeten Unfall gibt es hier in der Regel keine gegnerische Versicherung, die zahlt. Sie beauftragen mich direkt und erhalten vorab ein Angebot. Ob und in welchem Umfang sich die Kosten später vom Verkäufer oder der Werkstatt zurückholen lassen, klärt im Streitfall Ihr Rechtsanwalt."),
            ("Kann ich das Gutachten vor Gericht verwenden?",
             "Ein neutrales Gutachten eines unabhängigen Sachverständigen kann im Streitfall als Beweismittel vorgelegt werden. Es wird im Gegensatz zu einem Kostenvoranschlag vor Gericht anerkannt."),
            ("Soll ich das Fahrzeug vorher reparieren lassen?",
             "Nein. Lassen Sie den Zustand zuerst dokumentieren. Eine Reparatur davor kann Spuren beseitigen, die Sie später als Beweis brauchen."),
        ],
        "related": ["leistungen/wertgutachten", "leistungen/unfallanalytisches-gutachten", "gruende-fuer-ein-gutachten"],
    },
    {
        "slug": "leistungen/leasingruecknahme-gutachten",
        "short": "Leasingrücknahme-Gutachten",
        "tag": "Leasingende",
        "icon": "key",
        "title": "Leasingrücknahme-Gutachten Celle | PS Schneider",
        "desc": "Leasingrücknahme-Gutachten in Celle: unabhängige Bewertung bei Streit um Wertminderung und Verschleiß, damit Sie keine überzogenen Nachforderungen zahlen.",
        "h1": "Leasingrücknahme-Gutachten in Celle",
        "lede": "Bei der Rückgabe eines Leasingfahrzeugs streiten Leasinggeber und Fahrer oft über die Wertminderung. Ein unabhängiges Gutachten trennt normalen Verschleiß von echtem Schaden.",
        "card": "Normale Gebrauchsspuren sind keine Schäden. Ein unabhängiges Gutachten schützt Sie vor überzogenen Nachforderungen bei der Leasingrückgabe.",
        "sections": [
            {"h2": "Verschleiß ist kein Schaden", "body": [
                "Bei der Rückgabe von Leasingfahrzeugen entstehen häufig Meinungsverschiedenheiten über die Wertminderung. Bedauerlicherweise gibt es keine objektiven Kriterien, die genau festlegen, wann eine übermäßige Abnutzung vorliegt. Deshalb werden oft schon normale Verschleißspuren in die Bewertung einbezogen.",
                "Verschleißspuren sind keine Schäden. Sie müssen je nach Alter und Laufleistung des Fahrzeugs akzeptiert werden.",
            ]},
            {"h2": "Was bei einem Gebrauchtwagen normal ist", "body": [
                ("ul", [
                    "Dellen ohne Lackabsplitterungen",
                    "Steinschläge",
                    "Geringfügige Kratzer am Lack oder an den Felgen",
                    "Leichte Schrammen im Innenraum",
                ]),
                "Das sind in der Regel keine übermäßigen Beschädigungen, die eine Wertminderung rechtfertigen würden.",
            ]},
            {"h2": "Wann ein Gutachten hilft", "body": [
                ("ul", [
                    "Der Leasinggeber fordert nach der Rückgabe eine Nachzahlung für angebliche Schäden",
                    "Sie sind mit dem Rückgabeprotokoll nicht einverstanden",
                    "Sie wollen vor der Rückgabe wissen, was der Leasinggeber beanstanden könnte",
                ]),
                "Bringen Sie zum Termin den Leasingvertrag mit den Rückgabebedingungen und, falls vorhanden, das Rückgabeprotokoll mit. Ich bewerte den Zustand neutral und halte fest, was Verschleiß ist und was ein Schaden.",
            ]},
        ],
        "faq": [
            ("Wann soll ich das Gutachten machen lassen?",
             "Am besten vor der Rückgabe. Dann wissen Sie, was beanstandet werden könnte, und können entscheiden, ob sich eine Reparatur lohnt. Ist die Forderung schon da, hilft das Gutachten auch danach."),
            ("Muss ich Kratzer vor der Rückgabe reparieren lassen?",
             "Das hängt vom Leasingvertrag und vom Zustand ab. Lassen Sie vorher bewerten, was normaler Verschleiß ist. Dann vermeiden Sie Reparaturen, die gar nicht nötig sind."),
            ("Was zählt als normaler Verschleiß?",
             "Gebrauchsspuren, die zu Alter und Laufleistung passen, etwa kleine Kratzer, Steinschläge, Dellen ohne Lackabsplitterungen oder leichte Schrammen im Innenraum."),
        ],
        "related": ["leistungen/wertgutachten", "leistungen/beweissicherungsgutachten", "gruende-fuer-ein-gutachten"],
    },
    {
        "slug": "leistungen/wertgutachten",
        "short": "Wertgutachten",
        "tag": "An- und Verkauf, Oldtimer",
        "icon": "tag",
        "title": "Wertgutachten Kfz und Oldtimer Celle | PS Schneider",
        "desc": "Wertgutachten für Pkw, Lkw, Motorrad, Oldtimer und E-Bike in Celle: der reale Marktwert Ihres Fahrzeugs, objektiv und nachvollziehbar belegt.",
        "h1": "Wertgutachten für Fahrzeuge in Celle",
        "lede": "Ein Wertgutachten belegt den realen Wert Ihres Fahrzeugs. Es schafft Transparenz bei Kauf und Verkauf und dokumentiert Ausstattung sowie Vor- und Altschäden.",
        "card": "Der reale Marktwert Ihres Fahrzeugs, objektiv belegt. Sonderausstattung sowie Vor- und Altschäden werden dokumentiert. Ideal beim Kauf, Verkauf oder für Ihren Oldtimer.",
        "sections": [
            {"h2": "Für welche Fahrzeuge", "body": [
                "Ein Wertgutachten ermittelt den realen Wert eines Fahrzeugs. Das kann ein Auto sein, ein Lastkraftwagen, ein Nutzfahrzeug, ein Motorrad, ein Oldtimer oder sogar ein Elektrofahrrad.",
            ]},
            {"h2": "Wann ein Wertgutachten sinnvoll ist", "body": [
                ("ul", [
                    "Beim Kauf, um den Preis eines Fahrzeugs objektiv einzuordnen",
                    "Beim Verkauf, um den Marktwert belegen zu können",
                    "Für Ihren Oldtimer, wenn der Wert nachvollziehbar dokumentiert sein soll",
                    "Immer dann, wenn Sie eine neutrale Bewertung statt einer Schätzung brauchen",
                ]),
                "Eine gründliche Wertermittlung ist beim An- und Verkauf besonders nützlich, weil sie den aktuellen Marktwert des Fahrzeugs objektiv belegt.",
            ]},
            {"h2": "Was im Wertgutachten steht", "body": [
                ("ul", [
                    "Der ermittelte Wert des Fahrzeugs",
                    "Sonderausstattungen, die den Wert beeinflussen",
                    "Potenzielle Vor- und Altschäden",
                    "Der Gesamtzustand, nachvollziehbar mit Fotos belegt",
                ]),
                "Das Wertgutachten ist ein Ausdruck von Transparenz. Es zeigt, dass keine versteckten oder verschwiegenen Mängel existieren und dass das Fahrzeug tatsächlich dem angegebenen Preis entspricht.",
                "Vereinbaren Sie gern einen Termin.",
            ]},
        ],
        "faq": [
            ("Was ist der Unterschied zwischen Wertgutachten und Schadengutachten?",
             "Ein Schadengutachten beziffert, was ein Unfallschaden kostet und welche Ansprüche daraus folgen. Ein Wertgutachten ermittelt unabhängig von einem Schaden, was das Fahrzeug im aktuellen Zustand wert ist."),
            ("Erstellen Sie auch Wertgutachten für Oldtimer?",
             "Ja. Ein Wertgutachten für den Oldtimer gehört zu meinen Leistungen. Sprechen Sie mich gern auf Ihr Fahrzeug an."),
            ("Für welche Fahrzeugarten erstellen Sie Wertgutachten?",
             "Für Pkw, Lkw, Nutzfahrzeuge, Motorräder, Oldtimer und Elektrofahrräder."),
        ],
        "related": ["leistungen/beweissicherungsgutachten", "leistungen/leasingruecknahme-gutachten", "leistungen/restwertermittlung"],
    },
    {
        "slug": "leistungen/restwertermittlung",
        "short": "Restwertermittlung",
        "tag": "Totalschaden",
        "icon": "euro",
        "title": "Restwertermittlung Kfz Celle | PS Schneider",
        "desc": "Restwertermittlung nach Unfall in Celle: regional oder europaweit, mit Angeboten, damit Sie risikofrei entscheiden, ob Sie reparieren oder verkaufen.",
        "h1": "Restwertermittlung für Unfallfahrzeuge in Celle",
        "lede": "Was ist Ihr unrepariertes Fahrzeug nach dem Unfall noch wert? Ich ermittle den Restwert, hole Angebote ein und Sie entscheiden, ob Sie reparieren oder verkaufen.",
        "card": "Was ist das unreparierte Fahrzeug noch wert? Wir ermitteln den Restwert regional oder europaweit, holen Angebote ein und Sie entscheiden risikofrei: reparieren oder verkaufen.",
        "sections": [
            {"h2": "Was der Restwert aussagt", "body": [
                "Die Feststellung des Restwerts gibt Auskunft darüber, welchen Wert das unreparierte Fahrzeug nach einem Unfall noch auf dem allgemeinen, regionalen Markt besitzt. Als Sachverständiger für Fahrzeugtechnik dokumentiere ich diesen Restwert detailliert in einem Gutachten und kann unterschiedliche Angebote einholen.",
            ]},
            {"h2": "Risikofrei entscheiden", "body": [
                "Bei einer europaweiten Restwertermittlung entscheiden Sie nach dem Einholen der Angebote risikofrei, ob Sie eines davon annehmen. Nachdem der Restwert ermittelt wurde, haben Sie eine Grundlage für die Entscheidung, ob sich eine Reparatur lohnt oder ob es sinnvoller ist, das Fahrzeug zu verkaufen.",
                ("ol", [
                    "Ich besichtige und begutachte das beschädigte Fahrzeug.",
                    "Ich dokumentiere den Restwert und hole Angebote ein.",
                    "Sie entscheiden: Angebot annehmen, reparieren oder anders vorgehen.",
                ]),
            ]},
            {"h2": "Selbstverschuldeter Unfall und nur Haftpflicht?", "body": [
                "Hatten Sie einen selbstverschuldeten Unfall und sind nur haftpflichtversichert? Dann unterstütze ich Sie gern beim Verkauf des stark beschädigten Fahrzeugs.",
                "Im Haftpflichtfall nach einem unverschuldeten Unfall gehört der Restwert zum [[leistungen/haftpflichtschaden-gutachten|Haftpflichtschaden-Gutachten]].",
            ]},
        ],
        "faq": [
            ("Was ist der Unterschied zwischen Restwert und Wiederbeschaffungswert?",
             "Der Wiederbeschaffungswert ist der Betrag, den Sie für ein gleichwertiges gebrauchtes Fahrzeug am regionalen Markt zahlen müssten. Der Restwert ist der Wert, den das beschädigte Fahrzeug im unreparierten Zustand noch hat."),
            ("Muss ich ein Restwertangebot annehmen?",
             "Nein. Sie entscheiden nach dem Einholen der Angebote, ob Sie eines davon annehmen möchten."),
            ("Wann liegt ein Totalschaden vor?",
             "Von einem Totalschaden spricht man, wenn eine Reparatur technisch nicht möglich oder wirtschaftlich nicht sinnvoll ist, in der Regel weil die Reparaturkosten den Wiederbeschaffungswert übersteigen."),
        ],
        "related": ["leistungen/haftpflichtschaden-gutachten", "leistungen/wertgutachten", "unfall-checkliste"],
    },
    {
        "slug": "leistungen/unfallanalytisches-gutachten",
        "short": "Unfallanalytisches Gutachten",
        "tag": "Rechtsstreit",
        "icon": "chart",
        "title": "Unfallanalytisches Gutachten Celle | PS Schneider",
        "desc": "Unfallanalytisches Gutachten bei Rechtsstreitigkeiten in Celle: technische Rekonstruktion des Unfallhergangs als Grundlage für Anwalt, Versicherung und Gericht.",
        "h1": "Unfallanalytisches Gutachten in Celle",
        "lede": "Ist der Unfallhergang strittig, hilft eine technische Analyse. Ich werte Schadenbild und Spuren aus und liefere eine belastbare Grundlage für Anwalt, Versicherung und Gericht.",
        "card": "Wenn der Hergang strittig ist: technische Rekonstruktion des Unfalls als belastbare Grundlage für Anwalt, Versicherung und Gericht.",
        "sections": [
            {"h2": "Wann eine Unfallanalyse hilft", "body": [
                "Nach Verkehrsunfällen treten häufig Unstimmigkeiten auf. Oft versucht auch die gegnerische Versicherung, ihre Verantwortung zumindest teilweise abzulehnen, um Kosten zu minimieren. Steht Aussage gegen Aussage, kann eine unfallanalytische Untersuchung den Sachverhalt klären.",
                ("ul", [
                    "Die Schuldfrage ist zwischen den Beteiligten oder den Versicherungen strittig",
                    "Es gibt einen Rechtsstreit, in dem der Unfallhergang bewiesen werden muss",
                    "Das Schadenbild passt nach Ansicht einer Partei nicht zur Schilderung des Unfalls",
                ]),
            ]},
            {"h2": "Was dabei untersucht wird", "body": [
                "Grundlage sind die technischen Fakten: das Schadenbild an den beteiligten Fahrzeugen, die dokumentierten Spuren und die Angaben zum Unfallablauf. Daraus leite ich nachvollziehbar ab, wie sich der Unfall technisch abgespielt haben kann.",
                "Das Ergebnis halte ich in einem Gutachten fest. Es ist neutral und eignet sich als Grundlage für Ihren Rechtsanwalt, die Versicherung oder ein Gerichtsverfahren.",
            ]},
            {"h2": "Erstgespräch", "body": [
                "Ob und in welchem Umfang eine Unfallanalyse sinnvoll ist, hängt vom Einzelfall ab. Rufen Sie mich an und schildern Sie kurz die Lage. Dann klären wir gemeinsam, was nötig ist, und ich erstelle Ihnen ein individuelles Angebot.",
            ]},
        ],
        "faq": [
            ("Brauche ich bei einem Rechtsstreit zusätzlich einen Anwalt?",
             "In der Regel ja. Das unfallanalytische Gutachten liefert die technische Grundlage. Die rechtliche Vertretung übernimmt Ihr Rechtsanwalt, mit dem ich bei Bedarf zusammenarbeite."),
            ("Ist ein Gutachten bei jedem Unfall nötig?",
             "Nein. Bei klarer Haftung genügt meist ein [[leistungen/haftpflichtschaden-gutachten|Haftpflichtschaden-Gutachten]]. Die Unfallanalyse kommt ins Spiel, wenn der Hergang streitig ist."),
        ],
        "related": ["leistungen/haftpflichtschaden-gutachten", "leistungen/beweissicherungsgutachten", "unfall-checkliste"],
    },
]

# Warum-Seite: Gründe (aus der alten Seite, in Sie-Form)
REASONS = [
    ("Kostenfreiheit",
     ["Die Kosten für ein Kfz-Gutachten werden in der Regel von der Haftpflichtversicherung des Unfallverursachers getragen. Oft akzeptieren Versicherungen einen Kostenvoranschlag mit Fotos und verweisen darauf, dass Sie als Geschädigter die Kosten für einen Sachverständigen selbst übernehmen müssten.",
      "Gesetzlich ist das eindeutig geregelt: Im Haftpflichtfall haben Sie als Unfallgeschädigter das Recht, einen unabhängigen Sachverständigen Ihrer Wahl zu beauftragen. Die Kosten werden dem entstandenen Schaden zugerechnet und von der Haftpflichtversicherung des Unfallverursachers übernommen."]),
    ("Detailliertere Kostenerfassung und höhere Sicherheit",
     ["Ein Gutachten erfasst neben den Reparaturkosten auch die mögliche Wertminderung, die voraussichtliche Reparaturdauer und die Ausfallzeiten. Das dient Ihrer persönlichen finanziellen Sicherheit.",
      "Ein neutrales Gutachten wird außerdem im Gegensatz zu einem Kostenvoranschlag auch vor Gericht rechtlich anerkannt."]),
    ("Objektive Bewertung",
     ["Bei der Abwicklung eines Schadens sind in der Regel mehrere Parteien beteiligt, von denen jede eigene Interessen verfolgt. Als unabhängiger Sachverständiger für Fahrzeugtechnik bewerte ich die Situation objektiv und neutral.",
      "Um Ihre Ansprüche gegenüber der Versicherung des Unfallgegners durchzusetzen, können Sie ein umfassendes Gutachten eines unabhängigen Sachverständigen Ihrer Wahl vorlegen. Dadurch wird die Sachlage objektiv bewertet und dokumentiert."]),
    ("Beweissicherung",
     ["Nach Verkehrsunfällen treten häufig Unstimmigkeiten und Konflikte auf. Oft versucht auch die gegnerische Versicherung, ihre Verantwortung zumindest teilweise abzulehnen, um die Kosten zu minimieren.",
      "Mit einem Gutachten sind Sie dann auf der sicheren Seite. Im Gegensatz zu einem Kostenvoranschlag wird es im Streitfall vor Gericht anerkannt. Es erfasst sämtliche Schäden, die voraussichtlichen Reparaturkosten, die zu erwartende Wertminderung und die durch die Reparatur bedingten Ausfallzeiten."]),
    ("Fiktive Abrechnung",
     ["Auch wenn Sie Ihr Fahrzeug nach einem Unfall nicht reparieren lassen, können Sie Schadensersatzansprüche auszahlen lassen. Die fiktive Abrechnung ist bei Bagatellschäden, älteren Fahrzeugen oder wenn Sie den Schaden günstiger selbst beheben eine übliche Methode der Schadenregulierung.",
      "Um Ihre vollen Ansprüche geltend zu machen, empfiehlt sich ein Gutachten. Es berücksichtigt nicht nur die voraussichtlichen Reparaturkosten, sondern auch die Wertminderung, die bei einem späteren Verkauf relevant sein kann."]),
    ("Umfassende Expertise",
     ["Ich habe 17 Jahre bei Europas größter Sachverständigenorganisation gearbeitet. Dieses Fachwissen hilft mir, die Auswirkungen eines Unfalls detailliert zu erfassen und in einem aussagekräftigen Gutachten festzuhalten. Die Erstellung erfolgt stets kompetent und zügig, um Wartezeiten zu minimieren.",
      "Durch viele verschiedene Fälle und kontinuierliche Weiterbildung kann ich Ihnen nützliche Ratschläge geben, die auch im Umgang mit Anwälten und Versicherungen wertvoll sind."]),
]

COMPARE_ROWS = [
    ("Reparaturkosten", True, True),
    ("Wertminderung des Fahrzeugs", False, True),
    ("Reparaturdauer und Ausfallzeit", False, True),
    ("Restwert und Wiederbeschaffungswert", False, True),
    ("Vor- und Altschäden dokumentiert", False, True),
    ("Vor Gericht anerkannt", False, True),
    ("Neutral, unabhängig von Werkstatt und Versicherung", False, True),
]

HOME_FAQ = [
    ("Wer bezahlt das Gutachten?",
     "Bei einem unverschuldeten Unfall werden die Gutachtenkosten dem Schaden zugerechnet. Die Haftpflichtversicherung des Unfallverursachers übernimmt sie in der Regel. Bei einem selbstverschuldeten Unfall, einem Wert- oder Beweissicherungsgutachten beauftragen Sie mich direkt und erhalten vorab ein individuelles Angebot."),
    ("Muss ich den Gutachter nehmen, den die Versicherung vorschlägt?",
     "Nein. Als Geschädigter haben Sie das Recht, einen unabhängigen Sachverständigen Ihrer Wahl zu beauftragen. Ein von der Versicherung gestellter Gutachter arbeitet im Auftrag der Versicherung."),
    ("Wie schnell bekomme ich mein Gutachten?",
     "Die Besichtigung vereinbare ich kurzfristig. Das Gutachten wird zügig erstellt, damit die Wartezeit bis zur Reparatur oder zum Ersatzfahrzeug so kurz wie möglich bleibt."),
    ("Kann ich mir den Schaden auszahlen lassen, ohne zu reparieren?",
     "Ja, das nennt sich fiktive Abrechnung. Sie ist bei Bagatellschäden, älteren Fahrzeugen oder bei Eigenreparatur üblich. Das Gutachten beziffert dabei nicht nur die Reparaturkosten, sondern auch die Wertminderung, die beim späteren Verkauf relevant ist."),
    ("Was passiert bei einem Totalschaden?",
     "Dann ermittle ich Restwert und Wiederbeschaffungswert und hole auf Wunsch Angebote für das beschädigte Fahrzeug ein. Auf dieser Grundlage entscheiden Sie, ob sich eine Reparatur lohnt oder der Verkauf sinnvoller ist."),
    ("Für welche Fahrzeuge erstellen Sie Gutachten?",
     "Für Pkw, Lkw und Nutzfahrzeuge, Motorräder, Oldtimer und Elektrofahrräder."),
]

CHECKLIST = [
    ("Unfallstelle sichern", "Warnblinkanlage einschalten, Warnweste anziehen, Warndreieck aufstellen."),
    ("Verletzte versorgen", "Erste Hilfe leisten."),
    ("Polizei oder Rettungsdienst verständigen", "110 oder 112. Beantworten Sie die W-Fragen und warten Sie auf Rückfragen."),
    ("Daten mit dem Unfallgegner austauschen", "Name, Anschrift, Kennzeichen, Versicherung."),
    ("Fotos und Notizen zum Unfallhergang", "Fahrzeugpositionen, Schäden, Umgebung. Kontaktdaten von Zeugen notieren."),
    ("Sachverständigen kontaktieren", "Rufen Sie uns so früh wie möglich an. Wir stehen Ihnen bei der Schadenabwicklung zur Seite."),
]
