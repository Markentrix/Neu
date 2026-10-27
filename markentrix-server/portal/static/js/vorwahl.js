// Ort-Hinweis aus der Telefonvorwahl für das schnelle Anlegen von Leads. Nur ein Vorschlag, der Vertriebler prüft ihn.
const ORTE = {
  '030': 'Berlin', '040': 'Hamburg', '069': 'Frankfurt am Main', '089': 'München', '0221': 'Köln', '0211': 'Düsseldorf', '0231': 'Dortmund', '0201': 'Essen',
  '0711': 'Stuttgart', '0341': 'Leipzig', '0351': 'Dresden', '0421': 'Bremen', '0511': 'Hannover', '0531': 'Braunschweig', '0551': 'Göttingen', '0541': 'Osnabrück',
  '0441': 'Oldenburg', '05141': 'Celle', '05121': 'Hildesheim', '05151': 'Hameln', '05361': 'Wolfsburg', '05371': 'Gifhorn', '05331': 'Wolfenbüttel', '04131': 'Lüneburg',
  '0581': 'Uelzen', '0471': 'Bremerhaven', '0461': 'Flensburg', '0431': 'Kiel', '0451': 'Lübeck', '0381': 'Rostock', '0391': 'Magdeburg', '0361': 'Erfurt',
  '0911': 'Nürnberg', '0821': 'Augsburg', '0761': 'Freiburg', '0621': 'Mannheim', '0611': 'Wiesbaden', '0228': 'Bonn', '0241': 'Aachen', '0251': 'Münster',
  '0521': 'Bielefeld', '0561': 'Kassel',
};

/** Telefonnummer vereinheitlichen: +49… und 0049… werden zu 0…, nur Ziffern. */
export function nummerBereinigen(roh) {
  let z = String(roh || '').trim().replace(/\(0\)/g, '').replace(/[^\d+]/g, '');
  if (z.startsWith('+49')) z = '0' + z.slice(3); else if (z.startsWith('0049')) z = '0' + z.slice(4);
  return z.replace(/\D/g, '');
}

/** Ort zur Vorwahl (längste passende Vorwahl gewinnt) oder ''. */
export function ortZurVorwahl(roh) {
  const z = nummerBereinigen(roh);
  for (let n = 5; n >= 3; n--) { const o = ORTE[z.slice(0, n)]; if (o) return o; }
  return '';
}

/** Aus eingefügtem Text eine Telefonnummer und, falls vorhanden, einen Firmennamen holen.
 * Beispiel: „Autohaus Müller\nTel. 05141 12345“ → { telefon: '05141 12345', firma: 'Autohaus Müller' } */
export function ausText(text) {
  const t = String(text || '');
  const m = t.match(/(?:\+49|0049|0)[\d\s/()-]{6,18}\d/);
  const telefon = m ? m[0].replace(/\s+/g, ' ').trim() : '';
  const rest = t.replace(m ? m[0] : '', '').split(/\n|,|;/).map(x => x.replace(/^(tel\.?|telefon|fon|phone|mobil)\s*[:.]?\s*/i, '').trim()).filter(x => x && !/^[\d\s+()/-]+$/.test(x));
  return { telefon, firma: rest[0] ? rest[0].slice(0, 120) : '' };
}
