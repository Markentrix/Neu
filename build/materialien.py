# Materialseiten für den Druckservice. Werte sind übliche Richtwerte für FDM-Druck.

MATERIALIEN = [
    dict(
        id="pla", name="PLA", titel="3D-Druck mit PLA", farbe="#9e6230",
        claim="Das Standardmaterial: präzise, pflanzenbasiert, in den meisten Farben.",
        kurz="Polylactid aus Maisstärke und Zuckerrohr. Druckt sehr maßhaltig, riecht nicht und ergibt die saubersten Oberflächen. Für alles, was drinnen steht und nicht heiß wird.",
        eigenschaften=[("Wärmebeständig bis", "ca. 55 °C"), ("Festigkeit", "hoch, aber spröde bei Schlag"), ("Oberfläche", "sehr sauber, matt oder seidenglänzend"), ("Maßhaltigkeit", "±0,2 mm"), ("Außeneinsatz", "nicht geeignet"), ("Lebensmittelkontakt", "nur trocken, nicht spülmaschinenfest")],
        gut=["Dekoration, Figuren, Vasen", "Halter und Organizer am Schreibtisch", "Prototypen zum Anfassen und Maßprüfen", "Teile mit feinen Details und Schrift"],
        nicht=["Im Auto oder auf der Fensterbank in praller Sonne (verformt sich ab ca. 55 °C)", "Teile, die dauerhaft unter Last stehen (PLA kriecht)", "Draußen über Monate (UV und Feuchte)"],
        schicht="0,12 bis 0,28 mm", duesen="190 bis 220 °C", bett="55 bis 60 °C", dichte="1,24 g/cm³",
        farben="Schwarz, Weiß, Orange, Mint, Steingrau, Nachtblau, Holzton; weitere auf Anfrage",
        faq=[("Ist PLA biologisch abbaubar?", "Nur in industriellen Kompostieranlagen bei über 60 °C. Im Gartenkompost oder in der Natur baut es sich praktisch nicht ab. Wir sammeln Reste und Fehldrucke und geben sie zum Recycling."),
             ("Kann ich PLA lackieren?", "Ja. Nach leichtem Anschleifen hält Acryllack und Sprühlack gut. Füller gleicht die Schichtlinien aus."),
             ("Wie stabil ist PLA?", "Zugfest etwa wie ABS, aber weniger schlagzäh. Für einen Haken oder einen Halter reicht es locker, für ein Zahnrad unter Dauerlast nehmen wir PETG oder ASA.")],
    ),
    dict(
        id="petg", name="PETG", titel="3D-Druck mit PETG", farbe="#1f4d3a",
        claim="Zäh, wasserfest, lebensmittelecht: das Material für Küche, Bad und Technik.",
        kurz="Glykol-modifiziertes PET, derselbe Grundstoff wie Getränkeflaschen. Etwas flexibler als PLA, nimmt Schläge weg, verträgt Feuchtigkeit und Wärme bis etwa 75 °C.",
        eigenschaften=[("Wärmebeständig bis", "ca. 75 °C"), ("Festigkeit", "hoch und schlagzäh"), ("Oberfläche", "leicht glänzend, etwas weniger Detail als PLA"), ("Maßhaltigkeit", "±0,3 mm"), ("Außeneinsatz", "bedingt (Schatten, Regen ok)"), ("Lebensmittelkontakt", "Filament lebensmittelecht, Druckteil spülbar von Hand")],
        gut=["Halter in Bad und Küche", "Pflanztöpfe mit Wasserreservoir", "Klemmen, Clips und Haken unter Last", "Gehäuse für Elektronik"],
        nicht=["Feinste Details und scharfe Kanten (PETG zieht Fäden)", "Pralle Sonne über Jahre (vergilbt leicht)", "Spülmaschine (zu heiß)"],
        schicht="0,16 bis 0,28 mm", duesen="230 bis 250 °C", bett="70 bis 85 °C", dichte="1,27 g/cm³",
        farben="Schwarz, Weiß, Mint, Steingrau, Transparent; weitere auf Anfrage",
        faq=[("Ist PETG lebensmittelecht?", "Das Filament ist es. Ein gedrucktes Teil hat aber feine Rillen zwischen den Schichten, in denen sich Rückstände halten können. Für trockene Lebensmittel und kurzen Kontakt unproblematisch, für dauerhafte Lagerung empfehlen wir einen Innenbehälter."),
             ("PETG oder PLA?", "Draußen, nass, warm oder unter Last: PETG. Detailreich, dekorativ, maßgenau: PLA. Im Zweifel beraten wir bei der Anfrage.")],
    ),
    dict(
        id="abs", name="ABS", titel="3D-Druck mit ABS", farbe="#2f4d8a",
        claim="Der Klassiker für technische Teile: hitzefest, schleifbar, nachbearbeitbar.",
        kurz="Acrylnitril-Butadien-Styrol, das Material von Klemmbausteinen und Gerätegehäusen. Verträgt bis etwa 95 °C, lässt sich schleifen, bohren, kleben und mit Aceton glätten.",
        eigenschaften=[("Wärmebeständig bis", "ca. 95 °C"), ("Festigkeit", "hoch, gut schlagzäh"), ("Oberfläche", "matt, mit Aceton glättbar"), ("Maßhaltigkeit", "±0,3 mm, Schrumpf beim Abkühlen"), ("Außeneinsatz", "nur lackiert (UV-empfindlich)"), ("Lebensmittelkontakt", "nicht empfohlen")],
        gut=["Ersatzteile für Geräte und Fahrzeuginnenraum", "Gehäuse, Abdeckungen, Halterungen im Motorraum-Umfeld", "Teile, die nachträglich geschliffen oder lackiert werden", "Funktionsmuster, die warm werden"],
        nicht=["Sehr große flache Teile (Verzug beim Abkühlen)", "Draußen ohne Lack (wird spröde durch UV)", "Dekoration mit feinen Details (PLA ist schärfer)"],
        schicht="0,16 bis 0,28 mm", duesen="240 bis 260 °C", bett="95 bis 110 °C, geschlossener Bauraum", dichte="1,04 g/cm³",
        farben="Schwarz, Weiß, Grau; weitere auf Anfrage",
        faq=[("Warum ist ABS teurer als PLA?", "ABS braucht einen beheizten, geschlossenen Bauraum und druckt langsamer. Dafür bekommen Sie ein Teil, das 95 °C aushält und sich wie Spritzguss nachbearbeiten lässt."),
             ("Was ist Aceton-Glätten?", "ABS löst sich in Acetondampf oberflächlich an. Die Schichtlinien verschwinden, das Teil wird glänzend und dichter. Wir bieten das als Option an, Details werden dabei etwas weicher."),
             ("ABS oder ASA?", "Gleiche Mechanik, aber ASA ist UV-stabil. Alles, was draußen bleibt, drucken wir in ASA.")],
    ),
    dict(
        id="asa", name="ASA", titel="3D-Druck mit ASA", farbe="#5a6b7a",
        claim="Für draußen: UV-beständig, wetterfest, so robust wie ABS.",
        kurz="Acrylnitril-Styrol-Acrylat, der Outdoor-Bruder von ABS. Vergilbt nicht, wird in der Sonne nicht spröde und hält Regen, Frost und Hitze über Jahre aus.",
        eigenschaften=[("Wärmebeständig bis", "ca. 95 °C"), ("Festigkeit", "hoch, schlagzäh"), ("Oberfläche", "matt, seidig"), ("Maßhaltigkeit", "±0,3 mm"), ("Außeneinsatz", "uneingeschränkt"), ("Lebensmittelkontakt", "nicht empfohlen")],
        gut=["Gartenteile: Halter, Schilder, Abdeckungen, Vogelhaus-Teile", "Ersatzteile an Auto, Fahrrad, Wohnmobil", "Kamera- und Antennenhalterungen", "Hausnummern und Namensschilder für draußen"],
        nicht=["Teile mit sehr feinen Details", "Große flache Platten (Verzug wie bei ABS)", "Innenräume ohne Belüftung beim Druck (daher drucken wir ASA nur im geschlossenen Drucker)"],
        schicht="0,16 bis 0,28 mm", duesen="240 bis 260 °C", bett="95 bis 110 °C, geschlossener Bauraum", dichte="1,07 g/cm³",
        farben="Schwarz, Weiß, Grau, Anthrazit; weitere auf Anfrage",
        faq=[("Wie lange hält ASA draußen?", "Herstellerangaben und unsere eigenen Teile im Garten sagen: mehrere Jahre ohne sichtbare Veränderung. Farben bleiben, das Material wird nicht spröde."),
             ("Kann ich ASA lackieren?", "Ja, aber meist unnötig, weil ASA selbst UV-stabil ist. Anschleifen und Kunststoffhaftgrund, dann hält jeder Lack.")],
    ),
    dict(
        id="tpu", name="TPU", titel="3D-Druck mit TPU", farbe="#6b3f8c",
        claim="Flexibel wie Gummi: Dichtungen, Puffer, Hüllen, Griffe.",
        kurz="Thermoplastisches Polyurethan, ein gummiartiger Kunststoff mit Shore-Härte 95A. Biegsam, reißfest, abriebfest und gegen Öl und Fett unempfindlich.",
        eigenschaften=[("Härte", "Shore 95A (wie ein Skateboard-Rad)"), ("Wärmebeständig bis", "ca. 80 °C"), ("Festigkeit", "sehr reißfest, dehnbar bis 450 %"), ("Oberfläche", "matt, leicht gummiartig"), ("Maßhaltigkeit", "±0,4 mm"), ("Außeneinsatz", "gut")],
        gut=["Dichtungen, Füße, Puffer, Stoßschutz", "Handyhüllen, Kabelschutz, Griffe", "Flexible Scharniere und Bänder", "Rollen und Räder für Modelle"],
        nicht=["Dünne hohe Teile (knicken)", "Scharfe Kanten und feine Details", "Teile, die steif sein müssen"],
        schicht="0,16 bis 0,24 mm", duesen="220 bis 235 °C", bett="40 bis 60 °C, langsamer Druck", dichte="1,21 g/cm³",
        farben="Schwarz, Weiß, Orange, Transparent; weitere auf Anfrage",
        faq=[("Wie weich ist Shore 95A?", "Etwa wie die Sohle eines Turnschuhs oder ein Skateboard-Rad. Ein 2 mm dünnes Teil lässt sich leicht biegen, ein 10 mm dicker Block kaum."),
             ("Gibt es weicheres TPU?", "Ja, Shore 85A und weicher. Das drucken wir auf Anfrage, es ist langsamer und etwas teurer.")],
    ),
]

# Vergleichstabelle (Reihenfolge wie MATERIALIEN)
VERGLEICH = [
    ("Wärme bis", ["55 °C", "75 °C", "95 °C", "95 °C", "80 °C"]),
    ("Schlagzäh", ["gering", "hoch", "hoch", "hoch", "sehr hoch"]),
    ("Detailtreue", ["sehr gut", "gut", "gut", "gut", "mittel"]),
    ("Draußen", ["nein", "bedingt", "nur lackiert", "ja", "ja"]),
    ("Wasser", ["kurz ok", "ja", "ja", "ja", "ja"]),
]

FAQ = [
    ("Bestellung und Lieferung", [
        ("Wie lange dauert meine Bestellung?", "Shop-Artikel drucken wir innerhalb von 2 bis 4 Werktagen nach Zahlungseingang, dann 2 bis 3 Werktage Versand mit DHL. Bei personalisierten Artikeln beginnt die Frist mit Ihrer Freigabe der Vorschau."),
        ("Kann ich mehrere Artikel in einer Bestellung kombinieren?", "Ja, alles im Warenkorb wird zusammen gedruckt und in einem Paket verschickt. Ab 49 € Bestellwert entfallen die Versandkosten."),
        ("Liefert ihr auch nach Österreich oder in die Schweiz?", "Auf Anfrage. Schreiben Sie uns vor der Bestellung, wir nennen Ihnen die Versandkosten."),
        ("Wie bezahle ich?", "Per PayPal über einen Zahlungslink, den Sie mit der Bestellbestätigung erhalten, oder per Überweisung mit den Bankdaten auf der Rechnung. Auf der Website selbst werden keine Zahlungsdaten eingegeben."),
    ]),
    ("Material und Qualität", [
        ("Sieht man die Schichten?", "Ja, feine Linien von 0,12 bis 0,28 mm gehören zum Verfahren. Bei Sichtteilen drucken wir feiner, auf Wunsch schleifen und lackieren wir."),
        ("Welches Material soll ich nehmen?", "Drinnen und dekorativ: PLA. Nass, warm oder unter Last: PETG. Hitze und Nachbearbeitung: ABS. Draußen: ASA. Flexibel: TPU. Die Übersicht auf der Seite Materialien vergleicht alle fünf."),
        ("Sind die Teile spülmaschinenfest?", "Nein. PLA verformt sich ab 55 °C, PETG ab 75 °C. Von Hand mit warmem Wasser spülen."),
        ("Weichen Farben ab?", "Zwischen Filamentchargen kann der Ton leicht variieren. Bei Nachbestellungen zu einem bestehenden Satz sagen Sie uns Bescheid, dann drucken wir aus derselben Rolle."),
    ]),
    ("Eigene Dateien und Ersatzteile", [
        ("Welche Dateiformate nehmt ihr?", "STL, 3MF, STEP und OBJ. Am liebsten 3MF oder STEP, weil Maße und Einheiten darin eindeutig sind."),
        ("Ich habe keine Datei, nur das kaputte Teil.", "Schicken Sie uns Fotos mit Maßband und eine kurze Beschreibung. Einfache Teile konstruieren wir nach, komplexe Formen können wir vermessen. Die Konstruktion rechnen wir nach Aufwand ab und nennen vorher einen Festpreis."),
        ("Wie groß darf ein Teil sein?", "Bis 25 × 25 × 25 cm am Stück. Größeres teilen wir in Segmente mit Steckverbindung oder verkleben es."),
        ("Druckt ihr alles?", "Nein. Keine Waffen und Waffenteile, keine geschützten Markenprodukte zum Weiterverkauf, keine Teile, deren Versagen Personen gefährden kann (tragende Fahrzeugteile, Druckbehälter)."),
    ]),
    ("Widerruf und Reklamation", [
        ("Kann ich zurückschicken?", "Shop-Artikel ohne Personalisierung: ja, 14 Tage ab Erhalt. Artikel mit Wunschtext oder eigenem Foto sowie Drucke eigener Dateien: nein, weil sie nur für Sie gefertigt wurden."),
        ("Das Teil kam beschädigt an.", "Foto an uns, wir drucken kostenlos nach. Nichts zurückschicken, bevor wir uns gemeldet haben."),
    ]),
]
