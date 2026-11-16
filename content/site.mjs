// Zentrale Inhalte der Website – alle Texte stammen von lu-linneweh.com
export const company = {
  name: 'Lohnunternehmen Linneweh',
  legal: 'Lohnunternehmen Linneweh GmbH & Co. KG',
  claim: 'Mit Leidenschaft in der Landwirtschaft',
  phone: '05173 / 924940',
  phoneHref: 'tel:+495173924940',
  email: 'info@lu-linneweh.de',
  street: 'Bleckenweg 92',
  city: '29227 Celle',
  hours: 'Mo–Fr von 07:00–19:00 Uhr',
  maps: 'https://www.google.com/maps/dir/?api=1&destination=Bleckenweg+92%2C+29227+Celle',
  instagram: 'https://www.instagram.com/lu_linneweh/',
  facebook: 'https://www.facebook.com/profile.php?id=100070231125766',
};

export const sectors = [
  {
    id: 'landwirtschaft', nr: '01', short: 'Landwirtschaft', swap: 'Ihr Feld',
    title: 'Landwirtschaftliche Dienstleistungen', sub: 'Auf dem Feld für Sie unterwegs.',
    heroImg: 'grasernte', pageImg: 'ernte-staub', cardImg: 'haeckseln-1',
    teaser: 'Ob Mähen, Schwaden, Wenden, der Transport und das Ausbringen von Gärresten, sowie das Pflanzen von Kartoffeln und der mechanische Pflanzenschutz, wir bewirtschaften Ihre Felder für Sie.',
    overview: 'Vom Säen und Pflanzen über das Düngen und den Pflanzenschutz, bis hin zum Roden und Häckseln, wir sind auf Ihren Feldern für Sie unterwegs. Für die Energie und Ernährung von morgen.',
    introTitle: 'Für die Energie und Ernährung von morgen',
    intro: 'Wir unterstützen Sie dabei, auf Ihren Feldern Nahrungsmittel und Energieträger anzubauen, um die Ernährung und Verstromung zu sichern.',
  },
  {
    id: 'forstwirtschaft', nr: '02', short: 'Forstwirtschaft', swap: 'Ihren Forst',
    title: 'Forstwirtschaftliche Dienstleistungen', sub: 'In Forst und Wald für Sie unterwegs.',
    heroImg: 'bagger-forst', pageImg: 'bagger-forst', cardImg: 'flaechenvorbereitung-2',
    teaser: 'Neben Flächenvorbereitungen mit Forstmulchern und -Fräsen bieten wir auch Baggerräumungen und Rückearbeiten an.',
    overview: 'Ob Holzrücken, -Hacken, -Roden, Bäume Kneifen, Flächenvorbereitung oder Kulturpflege, wir kümmern uns um Ihre Forstflächen. Zusammen für eine grünere Zukunft.',
    introTitle: 'Für eine grünere Zukunft',
    intro: 'Wir unterstützen Sie dabei, Ihre Forst- und Waldgebiete zu pflegen, um gemeinsam für eine grünere Zukunft zu sorgen.',
    ral: true,
  },
  {
    id: 'kommunal', nr: '03', short: 'Kommunal', swap: 'Ihre Kommune',
    title: 'Kommunale Dienstleistungen', sub: 'Wir machen den Weg frei.',
    heroImg: 'winterdienst-1', pageImg: 'wegebau-4', cardImg: 'wegebau-4',
    teaser: 'Auch für die Kommunen sind wir da. Mit Wegebau und -pflege, sowie Winterdienst sorgen wir dafür, dass alle sicher an ihr Ziel kommen.',
    overview: 'Mit Wegebau und -Pflege, Winterdienst und Baufeldräumung machen wir für Sie den Weg frei.',
    introTitle: 'Wir machen den Weg frei',
    intro: 'Wir bieten Wegebau und -Pflege, sowie Winterdienst und Baufeldräumung an. Melden Sie sich bei uns, damit Sie immer sicher ans Ziel kommen.',
  },
];

// key = Schlüssel in services.json
export const services = [
  { key: 'duengung', slug: 'duengung', sector: 'landwirtschaft', teaser: 'Ausbringen von Gülle und Gärresten zur Förderung des Pflanzenwachstums.', hero: 'duengung-1', gallery: ['duengung-2', 'transport-5'] },
  { key: 'aussaat', slug: 'aussaat', sector: 'landwirtschaft', teaser: 'Aussaat von Kartoffeln, Rüben und Mais.', hero: 'aussaat-3', gallery: ['aussaat-1', 'aussaat-2', 'aussaat-4'] },
  { key: 'pflanzenschutz', slug: 'pflanzenschutz', sector: 'landwirtschaft', teaser: 'Hacken und Ausbringen von Herbiziden zum Schutz der Kulturpflanze vor Beikräutern.', hero: 'hacke-1', gallery: ['hacke-2', 'hacke-3', 'hacke-4'] },
  { key: 'haeckseln', slug: 'haeckseln', sector: 'landwirtschaft', teaser: 'Häckseln von Mais, Gras und Ganzpflanzensilage (GPS).', hero: 'haeckseln-1', gallery: ['haeckseln-2', 'haeckseln-3', 'maisernte', 'grasernte', 'silo'] },
  { key: 'gruenland', slug: 'gruenland', sector: 'landwirtschaft', teaser: 'Mähen, Wenden, Schwaden und Pressen von Gras in Rund- und Quaderballen.', hero: 'gruenland-1', gallery: ['maehen', 'schwaden', 'grasernte'] },
  { key: 'transport', slug: 'transport', sector: 'landwirtschaft', teaser: 'Transport von Stück- und Schüttgut, sowie Paletten- und Flüssigware.', hero: 'transport-1', gallery: ['transport-2', 'transport-3', 'transport-5', 'rueben', 'ernte-staub'] },
  { key: 'flaechen-vorbereitung', slug: 'flaechenvorbereitung', sector: 'forstwirtschaft', title: 'Flächenvorbereitung', teaser: 'Flächenvorbereitung für Neuanpflanzungen, Neueinsaaten und Aufforstungsmaßnahmen oder die Entfernung von Busch- und Strauchwerk.', hero: 'flaechenvorbereitung-2', gallery: ['flaechenvorbereitung-3', 'flaechenvorbereitung-4', 'flaechenvorbereitung-5', 'forstmulcher-1', 'forstmulcher-2'] },
  { key: 'kulturpflege', slug: 'kulturpflege', sector: 'forstwirtschaft', teaser: 'Entfernung von Begleitwuchs und Busch- und Strauchwerk zur Förderung des Pflanzenwachstums.', hero: 'kulturpflege-2', gallery: ['kulturpflege-1', 'kulturpflege-4', 'kulturpflege-5', 'moritz-4', 'moritz-2'] },
  { key: 'holz-ruecken', slug: 'holz-ruecken', sector: 'forstwirtschaft', title: 'Holz rücken', teaser: 'Holzbergung, Rücken und Transport.', hero: 'holz-ruecken-3', gallery: ['holz-ruecken-1', 'holz-ruecken-2', 'holz-ruecken-4', 'holz-ruecken-5'] },
  { key: 'baeume-kneifen', slug: 'baeume-kneifen', sector: 'forstwirtschaft', title: 'Bäume kneifen', teaser: 'Nachhaltiger Waldumbau und Rückegassen-Erstellung mit minimalem Schaden.', hero: 'baeume-kneifen-1', gallery: ['baeume-kneifen-2', 'baeume-kneifen-3', 'bagger-forst'] },
  { key: 'holz-hacken', slug: 'holz-hacken', sector: 'forstwirtschaft', title: 'Holz hacken', teaser: 'Holz hacken und Hackschnitzelherstellung.', hero: 'holz-hacken-3', gallery: ['holz-hacken-2', 'holz-hacken-4', 'holz-hacken-5'] },
  { key: 'forstfraesen', slug: 'forstfraesen', sector: 'forstwirtschaft', teaser: 'Fräsen von Pflanzflächen und Schneisen.', hero: 'forstfraese-1', gallery: ['forstmulcher-2', 'flaechenvorbereitung-5', 'forst-raupe'] },
  { key: 'pflanzvorbereitungen', slug: 'pflanzvorbereitungen', sector: 'forstwirtschaft', teaser: 'Streifenfräse, TTS Gerät und Waldstreifenpflug.', hero: 'pflanzvorbereitung-1', gallery: ['pflanzvorbereitung-2', 'forst-raupe'] },
  { key: 'wegebau', slug: 'wegebau', sector: 'kommunal', teaser: 'Schotter- und Sandwegebau, sowie Pflege- und Erneuerungsarbeiten.', hero: 'wegebau-4', gallery: ['wegebau-1', 'wegebau-2', 'wegebau-5', 'wegepflege-2', 'wegepflege-1'] },
  { key: 'seitenraender-schlegeln', slug: 'seitenraender-schlegeln', sector: 'kommunal', teaser: 'Beseitigung von Unkraut zur Pflege und Sicherung von Wegen.', hero: 'seitenraender-1', gallery: ['seitenraender-2', 'seitenraender-3', 'seitenraender-4'] },
  { key: 'winterdienst', slug: 'winterdienst', sector: 'kommunal', teaser: 'Streu- und Räumarbeiten auf Wegen und Grundstücken.', hero: 'winterdienst-1', gallery: ['winterdienst-2', 'winterdienst-3'] },
  { key: 'baufeldraeumung', slug: 'baufeldraeumung', sector: 'kommunal', teaser: 'Befreiung von Grundstücken von Störfaktoren mit der Fräse.', hero: 'baufeld-1', gallery: ['baufeld-2', 'forstfraese-1'] },
];

export const values = [
  { title: 'kundennah', icon: 'near', text: 'Bei unserer Arbeit ist die Nähe zum Kunden von entscheidender Bedeutung. Wir betreuen Ihre Projekte, beraten Sie gerne bei möglichen Fragen und sind immer für Sie erreichbar.' },
  { title: 'effizient', icon: 'fast', text: 'Mit modernster land- und forstwirtschaftlicher Technologie arbeiten wir nicht nur schnell, sondern auch mit höchster Präzision.' },
  { title: 'erfahren', icon: 'rings', text: 'Wir sind seit über 50 Jahren im land- und forstwirtschaftlichen Dienstleistungssektor für Sie da und haben Erfahrung in allen Bereichen gesammelt, um Sie optimal zu unterstützen.' },
];

export const timeline = [
  { year: '1973', text: 'Gründung des Lohnunternehmens Linneweh durch Günther Linneweh' },
  { year: '2010', text: 'Aufnahme von Kai Linneweh in die G. u. M. Linneweh GbR, Wiedenrode und Umwidmung dieser in K. & M. Linneweh GbR, sowie Gründung der Lohnunternehmen Linneweh GmbH & Co. KG durch Günther, Maik und Kai Linneweh' },
  { year: '2020', list: ['Anfang der Beteiligung im forstwirtschaftlichen Sektor', 'Einführung von AGRARMONITOR und Digitalisierung des Betriebs', 'Kauf des ersten selbstfahrenden Häckslers'] },
  { year: 'seit 2021', text: 'RAL Zertifizierung durch die Gütegemeinschaft Wald- und Landschaftspflege e.V.' },
  { year: '2022', text: 'Umzug nach Altencelle in den Bleckenweg 92' },
  { year: '2023', text: '50-jähriges Bestehen des Lohnunternehmens Linneweh' },
];

export const agrarmonitor = [
  { title: 'Navigation', text: 'In der Landkarte können sich die Fahrer direkt zum Schlag navigieren lassen und werden zusätzlich über den Bearbeitungsfortschritt der Kollegen informiert.' },
  { title: 'Aufträge', text: 'Mit nur wenigen Klicks alle relevanten Informationen digital und in Echtzeit erfassen. Dabei können Wiegungen und Artikelverbräuche schlagspezifisch dokumentiert werden.' },
  { title: 'GPS-Tracking', text: 'Den Standort der Maschine immer im Blick – bei der mobilen Auftragserfassung werden automatisch auch die Standortverläufe der Maschinen aufgezeichnet.' },
];

export const team = [
  { name: 'Kai Linneweh', role: 'Geschäftsführung', email: 'kai.linneweh@lu-linneweh.com' },
  { name: 'Nico Pietruska', role: 'Buchhaltung', email: 'nico.pietruska@lu-linneweh.com', img: 'team-nico-pietruska.webp' },
];

export const job = {
  title: 'Landwirtschaftliche Aushilfskraft (m/w/d) Teilzeit',
  need: ['Interesse und Engagement im land- und forstwirtschaftlichen Sektor', 'Einen Führerschein der Klasse T', 'Erfahrungen als landwirtschaftliche Aushilfskraft'],
  offer: ['Flexible Arbeitsumgebung mit Gleitzeiten', 'Freundliches Arbeitsklima', 'Leistungsgerechte Bezahlung', 'Aufstiegsmöglichkeiten'],
};

export const news = [
  {
    slug: 'ausbringung-von-wirtschaftsduenger', tag: 'Landwirtschaft', title: 'Ausbringung von Wirtschaftsdünger', img: 'duengung-2', gallery: ['duengung-1'],
    lead: 'Egal ob fest oder flüssig – wir haben die passende Maschine.',
    more: { text: 'Zur Leistung Düngung', href: 'leistungen/landwirtschaft/duengung/' },
  },
  {
    slug: 'wegepflegemaschine-hen-technologie', tag: 'Kommunal', title: 'Wegepflegemaschine HEN Technologie', img: 'wegepflege-1', gallery: ['wegepflege-2', 'wegepflege-3'],
    lead: 'Wir bringen Ihre Wege wieder in Bestform.',
    body: [
      { p: 'Ob land- oder forstwirtschaftliche Wege, Rad- und Wanderstrecken oder kommunale Zufahrten.' },
      { ul: ['Gründliche Aufarbeitung Ihrer Wege', 'Optimale Wegestruktur: Unebenheiten, Schlaglöcher und Auswaschungen werden zuverlässig beseitigt', 'Langlebige Ergebnisse: Perfekte Verdichtung sorgt für stabile und wetterfeste Wege'] },
    ],
    more: { text: 'Zur Leistung Wegebau', href: 'leistungen/kommunal/wegebau/' },
  },
  {
    slug: 'baggerarbeiten', tag: 'Forstwirtschaft', title: 'Baggerarbeiten', img: 'bagger-forst', gallery: ['bagger-2', 'bagger-3'],
    lead: 'Doosan Bagger – flexibel und vielseitig einsetzbar.',
    body: [
      { p: 'Dank seiner robusten Bauweise und der modernen Hydraulik eignet er sich optimal für Arbeiten im Forst-, Garten- und Landschaftsbau sowie im Erd- und Rückbau.' },
      { h: 'Ausstattung und Einsatzmöglichkeiten' },
      { ul: ['Bäume-Kneifer (Woodcracker) – Ideal zum sicheren Greifen, Fällen und Bewegen von Bäumen oder Sträuchern. Perfekt für Forstarbeiten und Landschaftspflege.', 'Mulchkopf für Gestrüpp – Effizientes Zerkleinern von Buschwerk, Gestrüpp und Unterholz, sorgt für eine saubere Fläche und reduziert Nacharbeiten.', 'Roderechen – Zum Entfernen von Wurzelwerk, Steinen und grobem Material, optimal für Flächenrodung und Bodenvorbereitung.', 'Schaufel – Für klassische Erdarbeiten wie Aushub, Planierarbeiten und Materialbewegung.'] },
    ],
    more: { text: 'Zur Leistung Bäume kneifen', href: 'leistungen/forstwirtschaft/baeume-kneifen/' },
  },
  {
    slug: 'forstmulchen', tag: 'Forstwirtschaft', title: 'Forstmulchen', img: 'forstmulcher-2', gallery: ['forstmulcher-4', 'forstmulcher-3'],
    lead: 'Der erste Schritt für nachhaltiges Wachstum.',
    body: [
      { p: 'Mit modernster Technik bereiten wir Ihre Flächen optimal für Aufforstung, Neuanpflanzung und Neueinsaat vor.' },
      { p: 'Unser Forstmulchen sorgt für eine gründliche Zerkleinerung von Wurzelstöcken, Sträuchern und Pflanzenresten – damit neuer Wald effizient und gleichmäßig wachsen kann.' },
      { p: 'Vertrauen Sie auf Erfahrung, Präzision und modernste Maschinen – für gesunde Böden und einen starken Wald von morgen!' },
    ],
    more: { text: 'Zur Leistung Flächenvorbereitung', href: 'leistungen/forstwirtschaft/flaechenvorbereitung/' },
  },
  {
    slug: 'winterdienst-fuer-kommunen-und-unternehmen', tag: 'Kommunal', title: 'Winterdienst für Kommunen & Unternehmen', img: 'winterdienst-1', gallery: ['winterdienst-2', 'winterdienst-3'],
    lead: 'Zuverlässiger Winterdienst – wir halten Ihre Wege frei!',
    body: [
      { p: 'Wenn der Winter kommt, sind wir schon unterwegs! Unser Winterdienst sorgt dafür, dass Straßen, Gehwege und Gewerbeflächen sicher befahrbar und begehbar bleiben.' },
      { p: 'Mit moderner Technik und erfahrenem Personal übernehmen wir für Kommunen und Unternehmen das Streuen und Schneeräumen – pünktlich, gründlich und zuverlässig.' },
      { h: 'Unsere Leistungen im Überblick' },
      { ul: ['Schneeräumen und Streuen von Straßen, Parkplätzen & Gehwegen', 'Betreuung von Gewerbeflächen und Industriearealen'] },
    ],
    more: { text: 'Zur Leistung Winterdienst', href: 'leistungen/kommunal/winterdienst/' },
  },
  {
    slug: 'vermietung-rueckewagen-mit-forstkran', tag: 'Forstwirtschaft', title: 'Vermietung eines Rückewagens mit Forstkran', img: 'rueckewagen-1', gallery: ['rueckewagen-2', 'rueckewagen-3'],
    lead: 'Vermietung inklusive Zugmaschine und Fahrer ebenfalls möglich.',
    body: [
      { h: 'Technische Daten' },
      { ul: ['11,5 t zulässiges Gesamtgewicht', 'Druckluftbremse auf beiden Achsen', 'Eigenölversorgung', 'Kranreichweite max. 7,5 m'] },
    ],
    more: { text: 'Zur Leistung Holz rücken', href: 'leistungen/forstwirtschaft/holz-ruecken/' },
  },
  {
    slug: 'forstraupe-moritz', tag: 'Forstwirtschaft', title: 'Forstraupe „Moritz“', img: 'moritz-1', gallery: ['moritz-4', 'moritz-3'],
    lead: 'Klein in der Größe – groß in der Leistung.',
    body: [
      { p: 'Ob im dichten Bestand, auf engem Raum oder in unwegsamem Gelände – Moritz kommt durch, wo andere passen müssen.' },
      { ul: ['geringes Eigengewicht von nur 1400 kg', 'schmale Abmessungen von 1,15 m Breite und 2,3 m Länge', 'arbeitet sicher und zuverlässig am Hang', 'das bodenschonende Raupenfahrwerk verteilt das Gewicht optimal und verhindert unnötige Verdichtung', 'ideal für empfindliche Waldböden, Wiesen und Naturflächen'] },
    ],
    more: { text: 'Zur Leistung Kulturpflege', href: 'leistungen/forstwirtschaft/kulturpflege/' },
  },
  {
    slug: 'gras-und-gps-ernte', tag: 'Landwirtschaft', title: 'Gras- und GPS-Ernte: Wir übernehmen das!', img: 'silo', gallery: ['gps-ernte', 'maehen'],
    lead: 'Vom Mähen bis zum festgewalzten Silo, wir bieten dir die komplette Kette aus einer Hand.',
    body: [
      { ul: ['Mähen', 'Wenden', 'Schwaden', 'Häckseln oder Pressen & Wickeln (rund oder eckig)', 'Transport', 'Silobau', 'Walzen'] },
    ],
    more: { text: 'Zur Leistung Grünland', href: 'leistungen/landwirtschaft/gruenland/' },
  },
  {
    slug: 'einboeck-chopstar-hacke', tag: 'Landwirtschaft', title: 'Einböck Chopstar Hacke', img: 'hacke-1', gallery: ['hacke-2'],
    lead: 'Du willst deinen Rüben den besten Start ermöglichen? Wir unterstützen dich mit unserem Service im Rübenhacken!',
    body: [
      { ul: ['12-reihig', 'kameragesteuerter Verschieberahmen der Hacke', '50er oder 45er Reihenabstand', 'Section control', 'Bandspritze für Pflanzenschutz oder Flüssigdünger'] },
      { h: 'Vorteile des Hackens' },
      { ul: ['Aufbrechen von Bodenverkrustungen sorgt für eine Verbesserung des Gas- und Wasserhaushalts', 'Regulierung von Beikräutern garantiert einen Wachstumsvorsprung der Kulturpflanzen', 'Nährstoffmobilisierung, Düngereinarbeitung', 'Verringerung/Vermeidung des Herbizidaufwands'] },
    ],
    more: { text: 'Zur Leistung Pflanzenschutz', href: 'leistungen/landwirtschaft/pflanzenschutz/' },
  },
];

export const faqs = [
  {
    q: 'Was ist ein Lohnunternehmen?', logo: 'blu-logo.png',
    a: ['Als Lohnunternehmen sind wir Mitglied beim Bundesverband Lohnunternehmen e.V. (kurz BLU), dem Berufsverband und Ansprechpartner für Lohnunternehmen in ganz Deutschland.', 'Hauptaufgabe eines Lohnunternehmens sind Dienstleistungen im ländlichen Raum. Einerseits gehören dazu die klassischen landwirtschaftlichen Agrardienstleistungen, zunehmend aber auch Aufgaben im Forstbereich oder Aufträge von Kommunen. Ob Winterdienst, Getreide ernten oder Tätigkeiten im Baubereich, moderne Dienstleister sind hier mittlerweile in vielen Bereichen zu finden.'],
  },
  {
    q: 'Was können wir für Sie tun?',
    a: ['Mit modernster Technologie sind wir im land- und forstwirtschaftlichen, sowie im kommunalen Sektor tätig. Dort bieten wir zahlreiche Dienstleistungen für Sie an.', 'Mehr zu den einzelnen Dienstleistungen finden Sie auf dieser Website unter <a href="{root}leistungen/">Dienstleistungen</a>.'],
  },
  {
    q: 'Wie arbeiten wir mit AGRARMONITOR?',
    a: ['AGRARMONITOR ist die führende Software für Lohnunternehmen, Ackerbaubetriebe und Forstbetriebe. Dokumentation in Echtzeit statt nachträglichem Zettelschreiben durch synchronen Datenaustausch zwischen Fahrer und Büro.'],
    am: true,
  },
];

// Bildbeschreibungen (Alt-Texte) nach Namenspräfix
export const alts = {
  'agrarmonitor-tablet': 'Tablet mit der AGRARMONITOR-Kartenansicht', 'aussaat': 'Traktor mit Sätechnik bei der Aussaat auf dem Feld', 'baeume-kneifen': 'Bagger mit Woodcracker beim Bäumekneifen im Wald',
  'bagger': 'Doosan Bagger im Forsteinsatz', 'baufeld': 'Bagger und Traktor mit Mulde bei der Baufeldräumung', 'beratung': 'Beratungsgespräch auf dem Feld', 'duengung': 'Traktor mit Güllefass bei der Düngung',
  'ernte-staub': 'Traktor mit Häckselwagen bei der Ernte', 'flaechenvorbereitung': 'Traktor mit Forstmulcher bei der Flächenvorbereitung', 'forst-raupe': 'Raupenfahrzeug mit Mulcher im Forst', 'forstfraese': 'Traktor mit Forstfräse',
  'forstmulcher': 'Traktor mit Forstmulcher im Einsatz', 'gps-ernte': 'Feldhäcksler bei der GPS-Ernte', 'grasernte': 'Feldhäcksler und Ladewagen bei der Grasernte', 'gruenland': 'Quaderballenpresse im Abendlicht auf dem Grünland',
  'hacke': 'Traktor mit Einböck Chopstar Hacke im Rübenfeld', 'haeckseln': 'Fendt Katana Feldhäcksler beim Häckseln', 'holz-hacken': 'Holzhacker und Hackschnitzel', 'holz-ruecken': 'Rückewagen mit Forstkran beim Holzrücken',
  'kulturpflege': 'Traktor mit Forstmulcher bei der Kulturpflege', 'maehen': 'Traktor mit Schmetterlingsmähwerk beim Mähen', 'maisernte': 'Feldhäcksler und Traktor mit Häckselwagen bei der Maisernte', 'moritz': 'Forstraupe Pfanzelt Moritz im Einsatz',
  'pflanzvorbereitung': 'Maschine bei der Pflanzvorbereitung auf einer Forstfläche', 'rueben': 'Traktor mit Mulde bei der Rübenabfuhr', 'rueckewagen': 'Rückewagen mit Forstkran und Holzstämmen', 'schwaden': 'Traktor mit Vierkreiselschwader beim Schwaden',
  'seitenraender': 'Traktor mit Seitenmulcher beim Schlegeln von Seitenrändern', 'silo': 'Traktor beim Festwalzen des Silos', 'transport': 'LKW und Traktor beim Transport', 'wegebau': 'Traktor mit Wegepflegemaschine beim Wegebau',
  'wegepflege': 'Wegepflegemaschine HEN WPF 200 und aufbereiteter Weg', 'winterdienst': 'Traktor mit Schneeräumschild im Winterdienst',
};
