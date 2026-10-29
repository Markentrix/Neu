import { h, api, melde, zeit, toast, groesse } from '../common.js';
import { V, zeige } from './kern.js';

const EUR = (z) => Number(z).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
const STATUS = { eingegangen: ['warn', 'Eingegangen'], bestaetigt: ['ok', 'Bestätigt'], bezahlt: ['ok', 'Bezahlt'], im_druck: ['ok', 'In Produktion'], versendet: ['ok', 'Versendet'], abholbereit: ['ok', 'Abholbereit'], abgeholt: ['', 'Abgeholt'], storniert: ['bad', 'Storniert'] };
const feld = (label, el, tipp) => h('div', {}, h('label', {}, label), el, tipp ? h('div', { class: 'small muted' }, tipp) : '');
const haken = (an, text) => { const c = h('input', { type: 'checkbox', checked: !!an, style: 'width:auto' }); return { c, el: h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-weight:400' }, c, text) }; };
const slug = (t) => String(t).toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss').normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
/** @param {HTMLElement} box @param {any} x */
const fehler = (box, x) => melde(box, x && x.message ? x.message : String(x));

/** Bild für den Shop: auf 4:3 zuschneiden (1200 × 900), als WebP speichern, möglichst klein. Transparenz wird weiß. @param {File} datei */
async function alsWebp(datei) {
  const bmp = await createImageBitmap(datei);
  const B = 1200, H = 900, c = document.createElement('canvas');
  c.width = B; c.height = H;
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('Das Bild konnte nicht verarbeitet werden.');
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, B, H);
  const s = Math.max(B / bmp.width, H / bmp.height), w = bmp.width * s, hh = bmp.height * s;
  ctx.drawImage(bmp, (B - w) / 2, (H - hh) / 2, w, hh);
  for (const q of [0.88, 0.78, 0.66, 0.52]) {
    const blob = await new Promise((r) => c.toBlob(r, 'image/webp', q));
    if (blob && blob.type === 'image/webp' && blob.size <= 600 * 1024) return blob;
  }
  throw new Error('Das Bild lässt sich nicht klein genug speichern. Bitte ein einfacheres Bild nehmen.');
}

V.shop = async () => {
  const d = await api('/api/kunde/shop');
  const neu = () => zeige();
  const e = d.einstellungen;
  const offen = d.bestellungen.filter((b) => ['eingegangen', 'bestaetigt', 'bezahlt', 'im_druck'].includes(b.status)).length;
  const KAT = Object.fromEntries(d.kategorien.map((k) => [k.schluessel, k.name]));

  const kopf = h('div', { class: 'card' },
    h('p', {}, 'Hier pflegst du die Artikel deines Shops und bearbeitest die Bestellungen. Deine Website holt Artikel, Preise und Bilder automatisch von hier.'),
    d.domains.length ? h('p', { class: 'small' }, 'Aktiv für: ', d.domains.join(', ')) : h('p', { class: 'msg info' }, 'Für dich ist noch keine Website-Adresse hinterlegt. Wir tragen sie ein, sobald deine Seite online ist.'),
    h('p', { class: 'small' }, h('span', { class: 'pill ' + (e.aktiv ? 'ok' : 'warn') }, e.aktiv ? 'Shop ist eingeschaltet' : 'Shop ist ausgeschaltet'), ' ',
      e.aktiv ? '' : 'Bevor Besucher etwas sehen, Artikel auf „aktiv“ stellen und unten in den Einstellungen den Shop einschalten.'),
    d.paypal_bereit ? '' : h('p', { class: 'msg info' }, 'PayPal ist noch nicht eingetragen (Website-Dienste → PayPal). Ohne PayPal.Me-Link bekommen Kundinnen und Kunden keinen Zahlknopf.'));

  // ------------------------------------------------------------ Bestellungen
  const bestellung = (b) => {
    const st = h('select', {}, Object.entries(STATUS).filter(([k]) => (k !== 'abholbereit' && k !== 'abgeholt') || b.lieferart === 'abholung').filter(([k]) => k !== 'versendet' || b.lieferart === 'versand')
      .map(([k, v]) => h('option', { value: k, selected: k === b.status }, v[1])));
    const sendung = h('input', { value: b.sendungsnummer, maxlength: 80, placeholder: 'Sendungsnummer' });
    const abholung = h('input', { value: b.abholtermin, maxlength: 120, placeholder: 'z. B. Sa, 14.11., 10 bis 12 Uhr' });
    const notiz = h('textarea', { rows: 2, maxlength: 1000, placeholder: 'Interne Notiz (sieht nur ihr)' }, b.notiz);
    const mail = haken(true, 'Kundin bzw. Kunden per Mail über den neuen Status informieren');
    const m = h('div');
    const speichern = async () => {
      try {
        const r = await api('/api/kunde/shop/bestellungen/' + b.id, { method: 'PUT', body: { status: st.value, sendungsnummer: sendung.value, abholtermin: abholung.value, notiz: notiz.value, mail: mail.c.checked } });
        toast(r.mail ? 'Gespeichert, Mail ist raus.' : 'Gespeichert.', 'ok'); neu();
      } catch (x) { fehler(m, x); }
    };
    const a = b.adresse;
    return h('details', { class: 'hilfe', open: b.status === 'eingegangen' },
      h('summary', {}, b.ref + ' · ' + b.name + ' · ' + EUR(b.zu_zahlen) + ' · ', h('span', { class: 'pill ' + STATUS[b.status][0] }, STATUS[b.status][1])),
      h('div', { style: 'margin-top:8px' },
        h('p', { class: 'small muted' }, zeit(b.erstellt_am) + ' · ' + b.email + (b.telefon ? ' · ' + b.telefon : '')),
        h('ul', {}, b.positionen.map((p) => h('li', {}, p.menge + ' × ' + p.name + (p.farbe ? ' (' + p.farbe + ')' : '') + (p.text ? ', Wunschtext: „' + p.text + '“' : '') + ' · ' + EUR(p.einzelpreis * p.menge)))),
        h('p', { class: 'small' }, 'Zwischensumme ' + EUR(b.zwischensumme) + ' · Versand ' + EUR(b.versand) + ' · ', h('b', {}, 'Gesamt ' + EUR(b.summe))),
        b.gutschein > 0 ? h('p', { class: 'small' }, 'Gutschein ' + b.gutschein_code + ': −' + EUR(b.gutschein) + ' · ', h('b', {}, 'zu zahlen ' + EUR(b.zu_zahlen))) : '',
        h('p', { class: 'small' }, b.lieferart === 'abholung' ? 'Abholung' : 'Versand an: ' + (a ? a.strasse + ', ' + a.plz + ' ' + a.ort + (a.land && a.land !== 'DE' ? ', ' + a.land : '') : ''), ' · Zahlung: ' + (b.zahlungsart === 'paypal' ? 'PayPal' : 'bei Abholung')),
        b.anmerkung ? h('p', { class: 'small' }, 'Anmerkung der Kundschaft: ' + b.anmerkung) : '',
        h('div', { class: 'form2' }, feld('Status', st), b.lieferart === 'versand' ? feld('Sendungsnummer', sendung) : feld('Abholtermin', abholung)), notiz, mail.el, m,
        h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: speichern }, 'Speichern'),
          h('a', { class: 'btn sec', href: 'mailto:' + b.email + '?subject=' + encodeURIComponent('Ihre Bestellung ' + b.ref) }, 'Mail schreiben'))));
  };
  const bestellungen = h('div', { class: 'card' }, h('h2', {}, 'Bestellungen' + (offen ? ' (' + offen + ' offen)' : '')),
    d.bestellungen.length ? d.bestellungen.map(bestellung) : h('p', { class: 'muted' }, 'Noch keine Bestellung eingegangen.'),
    h('p', { class: 'small muted' }, 'Bei einer neuen Bestellung bekommst du eine Meldung und eine Mail. Zahlung per PayPal prüfst du selbst in deinem PayPal-Konto und stellst die Bestellung dann auf „Bezahlt“. Ist alles mit einem Gutschein bezahlt, steht sie schon auf „Bezahlt“. Storniert ein Betrieb eine Bestellung, bekommt ein eingelöster Gutschein sein Guthaben zurück.'));

  // ------------------------------------------------------------ Artikel
  const artikel = (p) => {
    const m = h('div');
    const name = h('input', { value: p ? p.name : '', maxlength: 120 });
    const schl = h('input', { value: p ? p.schluessel : '', maxlength: 60, disabled: !!p, placeholder: 'wird aus dem Namen gebildet' });
    const preis = h('input', { type: 'number', min: '0', step: '0.01', value: p ? String(p.preis) : '' });
    const kat = h('select', {}, h('option', { value: '' }, '(keine)'), d.kategorien.map((k) => h('option', { value: k.schluessel, selected: !!p && p.kategorie === k.schluessel }, k.name)));
    const kurz = h('input', { value: p ? p.kurz : '', maxlength: 400 });
    const lang = h('textarea', { rows: 4, maxlength: 4000 }, p ? p.lang : '');
    const material = h('input', { value: p ? p.material : '', maxlength: 120 }), masse = h('input', { value: p ? p.masse : '', maxlength: 120 }), gewicht = h('input', { value: p ? p.gewicht : '', maxlength: 60 });
    const fs = d.farben.map((f) => ({ f, c: h('input', { type: 'checkbox', checked: !!p && p.farben.includes(f.schluessel), style: 'width:auto' }) }));
    const tags = h('input', { value: p ? p.tags.join(', ') : '', placeholder: 'neu, bestseller' });
    const verw = h('input', { value: p ? p.verwandt.join(', ') : '', placeholder: 'Kurznamen anderer Artikel, durch Komma' });
    const pers = haken(p && p.personalisierbar, 'mit Wunschtext (Kundschaft tippt einen Text ein)');
    const tlabel = h('input', { value: p ? p.textlabel : '', maxlength: 80, placeholder: 'Wunschtext' }), tmax = h('input', { type: 'number', min: '0', max: '200', value: p ? String(p.textmax || 20) : '20' });
    const sort = h('input', { type: 'number', min: '0', value: p ? String(p.sort) : '100' });
    const aktiv = haken(p && p.aktiv, 'aktiv (auf der Website sichtbar). Ohne Haken ist der Artikel ein Entwurf.');
    const body = () => ({ name: name.value, schluessel: schl.value, kategorie: kat.value || null, preis: Number(String(preis.value).replace(',', '.')) || 0, kurz: kurz.value, lang: lang.value, material: material.value,
      masse: masse.value, gewicht: gewicht.value, farben: fs.filter((x) => x.c.checked).map((x) => x.f.schluessel), tags: tags.value.split(',').map((x) => x.trim()).filter(Boolean),
      verwandt: verw.value.split(',').map((x) => x.trim()).filter(Boolean), personalisierbar: pers.c.checked, textlabel: tlabel.value, textmax: Number(tmax.value) || 0, sort: Number(sort.value) || 100, aktiv: aktiv.c.checked });
    const speichern = async () => {
      if (!name.value.trim()) { melde(m, 'Bitte einen Namen angeben.'); return; }
      try { await api('/api/kunde/shop/produkte' + (p ? '/' + p.id : ''), { method: p ? 'PUT' : 'POST', body: body() }); toast('Gespeichert.', 'ok'); neu(); } catch (x) { fehler(m, x); }
    };
    const weg = async () => { if (!p || !confirm('„' + p.name + '“ samt Bildern löschen? Bestellungen bleiben erhalten.')) return; try { await api('/api/kunde/shop/produkte/' + p.id, { method: 'DELETE' }); neu(); } catch (x) { fehler(m, x); } };
    // Bilder (nur bei bestehendem Artikel)
    const bm = h('div');
    const hoch = h('input', { type: 'file', accept: 'image/*', multiple: true });
    const hochladen = async () => {
      if (!p || !hoch.files || !hoch.files.length) { melde(bm, 'Bitte zuerst ein Bild wählen.'); return; }
      try {
        for (const datei of Array.from(hoch.files)) {
          const blob = await alsWebp(datei);
          await api('/api/kunde/shop/produkte/' + p.id + '/bilder?alt=' + encodeURIComponent(name.value), { method: 'POST', body: blob });
        }
        toast('Bild gespeichert.', 'ok'); neu();
      } catch (x) { fehler(bm, x); }
    };
    const bilder = p ? h('div', {},
      h('h4', {}, 'Bilder (das erste ist das Hauptbild)'),
      h('div', { class: 'row', style: 'gap:10px;flex-wrap:wrap' }, p.bilder.map((b) => {
        const alt = h('input', { value: b.alt, maxlength: 200, placeholder: 'Bildbeschreibung', style: 'width:160px' });
        return h('div', { style: 'width:170px' }, h('img', { src: '/api/kunde/shop/bilder/' + b.id, alt: b.alt, loading: 'lazy', style: 'width:100%;border-radius:8px;display:block' }), alt,
          h('div', { class: 'row', style: 'gap:6px' },
            h('button', { class: 'btn sec small', onclick: async () => { try { await api('/api/kunde/shop/bilder/' + b.id, { method: 'PUT', body: { alt: alt.value, sort: 100 } }); toast('Gespeichert.', 'ok'); } catch (x) { fehler(bm, x); } } }, 'Text'),
            h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('Bild löschen?')) return; try { await api('/api/kunde/shop/bilder/' + b.id, { method: 'DELETE' }); neu(); } catch (x) { fehler(bm, x); } } }, 'Löschen')));
      })),
      h('div', { class: 'row', style: 'gap:8px;margin-top:8px;flex-wrap:wrap' }, hoch, h('button', { class: 'btn sec', onclick: hochladen }, 'Bild hochladen')),
      h('p', { class: 'small muted' }, 'Das Bild wird automatisch auf 4:3 zugeschnitten und als WebP gespeichert. Höchstens 8 Bilder je Artikel.'), bm) : h('p', { class: 'small muted' }, 'Bilder kannst du hochladen, sobald der Artikel einmal gespeichert ist.');
    return h('details', { class: 'hilfe', open: !p },
      h('summary', {}, p ? p.name + ' · ' + EUR(p.preis) + (p.kategorie && KAT[p.kategorie] ? ' · ' + KAT[p.kategorie] : '') + (p.aktiv ? '' : ' (Entwurf)') : '+ Neuen Artikel anlegen'),
      h('div', { style: 'margin-top:8px' },
        h('div', { class: 'form2' }, feld('Name', name), feld('Preis in Euro (Endpreis)', preis), feld('Kategorie', kat), feld('Kurzname für die Website', schl, p ? 'Lässt sich nicht mehr ändern.' : 'Nur Kleinbuchstaben, Ziffern, Bindestrich.'),
          feld('Material', material), feld('Maße', masse), feld('Gewicht', gewicht), feld('Reihenfolge (kleinere zuerst)', sort)),
        feld('Kurztext (Kachel im Shop)', kurz), feld('Langtext (Artikelseite)', lang),
        d.farben.length ? h('div', {}, h('label', {}, 'Farben (die erste ist die Vorauswahl)'), h('div', { class: 'row', style: 'gap:10px;flex-wrap:wrap' }, fs.map((x) => h('label', { style: 'display:flex;gap:4px;align-items:center;color:inherit;font-weight:400' }, x.c, h('span', { style: 'display:inline-block;width:14px;height:14px;border-radius:50%;border:1px solid #8884;background:' + x.f.hex }), x.f.name)))) : h('p', { class: 'small muted' }, 'Farben legst du weiter unten unter „Farben und Kategorien“ an.'),
        h('div', { class: 'form2' }, feld('Kennzeichen (Tags)', tags, 'z. B. neu, bestseller'), feld('Oft zusammen bestellt mit', verw)),
        pers.el, h('div', { class: 'form2' }, feld('Beschriftung des Textfelds', tlabel), feld('Höchstens … Zeichen', tmax)), aktiv.el, m,
        h('div', { class: 'row', style: 'margin:8px 0' }, h('button', { class: 'btn', onclick: speichern }, p ? 'Speichern' : 'Anlegen'), p ? h('button', { class: 'btn sec', onclick: weg }, 'Löschen') : ''),
        bilder));
  };
  const artikelKarte = h('div', { class: 'card' }, h('h2', {}, 'Artikel (' + d.produkte.length + ')'), d.produkte.map(artikel), artikel(null),
    h('p', { class: 'small muted' }, 'Bilderspeicher: ' + groesse(d.speicher) + ' von ' + groesse(d.speicher_max) + '.'));

  // ------------------------------------------------------------ Farben und Kategorien
  const liste = (titel, art, zeilen, mitFarbe) => {
    const m = h('div');
    const zeile = (z) => {
      const name = h('input', { value: z ? z.name : '', maxlength: 80, placeholder: titel === 'Farben' ? 'z. B. Orange Silk (glänzend)' : 'z. B. Wohnen & Deko' });
      const hex = h('input', { type: 'color', value: z ? z.hex : '#e07a2a', style: 'width:48px;padding:0;height:36px' });
      const sort = h('input', { type: 'number', min: '0', value: z ? String(z.sort) : '100', style: 'width:80px', 'aria-label': 'Reihenfolge' });
      const speichern = async () => {
        if (!name.value.trim()) { melde(m, 'Bitte einen Namen angeben.'); return; }
        try { await api('/api/kunde/shop/' + art + (z ? '/' + z.id : ''), { method: z ? 'PUT' : 'POST', body: { name: name.value, hex: hex.value, sort: Number(sort.value) || 100, schluessel: z ? z.schluessel : slug(name.value) } }); neu(); } catch (x) { fehler(m, x); }
      };
      return h('div', { class: 'row', style: 'gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0' }, name, mitFarbe ? hex : '', sort,
        h('button', { class: 'btn sec small', onclick: speichern }, z ? 'Speichern' : 'Anlegen'),
        z ? h('button', { class: 'btn sec small', onclick: async () => { if (!confirm('„' + z.name + '“ löschen? Sie wird bei allen Artikeln entfernt.')) return; try { await api('/api/kunde/shop/' + art + '/' + z.id, { method: 'DELETE' }); neu(); } catch (x) { fehler(m, x); } } }, 'Löschen') : '');
    };
    return h('div', {}, h('h3', {}, titel), zeilen.map(zeile), zeile(null), m);
  };
  const listen = h('div', { class: 'card' }, h('h2', {}, 'Farben und Kategorien'),
    h('p', { class: 'small muted' }, 'Farben pflegst du hier einmal und wählst sie dann bei den Artikeln aus. Kategorien erscheinen im Shop nur, wenn sie mindestens einen aktiven Artikel haben. Die Zahl rechts bestimmt die Reihenfolge.'),
    liste('Farben', 'farben', d.farben, true), liste('Kategorien', 'kategorien', d.kategorien, false));

  // ------------------------------------------------------------ Einstellungen
  const em = h('div');
  const aktivS = haken(e.aktiv, 'Shop einschalten (Artikel erscheinen auf der Website)');
  const pausch = h('input', { type: 'number', min: '0', step: '0.01', value: String(e.versand_pauschale) });
  const frei = h('input', { type: 'number', min: '0', step: '0.01', value: e.versandfrei_ab === null ? '' : String(e.versandfrei_ab), placeholder: 'leer = nie' });
  const abh = haken(e.abholung, 'Abholung ist möglich (Versand kostet dann nichts)');
  const prod = h('input', { value: e.produktionszeit, maxlength: 200, placeholder: 'z. B. 2 bis 4 Werktage' }), lief = h('input', { value: e.lieferzeit, maxlength: 200, placeholder: 'z. B. 2 bis 3 Werktage nach Versand' });
  const praef = h('input', { value: e.ref_praefix, maxlength: 6, style: 'width:90px' });
  const gAn = haken(e.gutschein_aktiv, 'Geschenkgutscheine anbieten');
  const gBetr = h('input', { value: e.gutschein_betraege.join(', ') }), gMin = h('input', { type: 'number', min: '1', value: String(e.gutschein_min) }), gMax = h('input', { type: 'number', min: '1', value: String(e.gutschein_max) });
  const gMon = h('input', { type: 'number', min: '1', max: '120', value: String(e.gutschein_monate) }), gZu = h('input', { value: e.gutschein_zustellung.join(', ') });
  const speichernE = async () => {
    try {
      await api('/api/kunde/shop/einstellungen', { method: 'PUT', body: { aktiv: aktivS.c.checked, ref_praefix: (praef.value || 'B').toUpperCase(), versand_pauschale: Number(String(pausch.value).replace(',', '.')) || 0,
        versandfrei_ab: frei.value === '' ? null : Number(String(frei.value).replace(',', '.')), abholung: abh.c.checked, produktionszeit: prod.value, lieferzeit: lief.value, gutschein_aktiv: gAn.c.checked,
        gutschein_betraege: gBetr.value.split(',').map((x) => parseInt(x, 10)).filter((x) => x > 0), gutschein_min: Number(gMin.value) || 1, gutschein_max: Number(gMax.value) || 1,
        gutschein_monate: Number(gMon.value) || 36, gutschein_zustellung: gZu.value.split(',').map((x) => x.trim()).filter(Boolean) } });
      toast('Gespeichert.', 'ok'); neu();
    } catch (x) { fehler(em, x); }
  };
  const einstellungen = h('div', { class: 'card' }, h('h2', {}, 'Einstellungen'),
    aktivS.el, h('div', { class: 'form2' }, feld('Versandpauschale (Euro)', pausch), feld('Versandkostenfrei ab (Euro)', frei), feld('Produktionszeit', prod), feld('Lieferzeit', lief), feld('Bestellnummer beginnt mit', praef, 'z. B. SA ergibt SA-2026-0001')), abh.el,
    h('h3', {}, 'Geschenkgutscheine'), gAn.el, h('div', { class: 'form2' }, feld('Betragsauswahl (Euro, durch Komma)', gBetr), feld('Kleinster Betrag', gMin), feld('Größter Betrag', gMax), feld('Gültig (Monate)', gMon), feld('Zustellarten', gZu)),
    h('p', { class: 'small muted' }, 'Gutschein-Bestellungen findest du unter „Website-Dienste“ → Gutscheine, dort sendest du auch den Code. Gesendete Codes können Kundinnen und Kunden an der Kasse des Shops einlösen. Der Rest bleibt stehen, bis der Gutschein abläuft (Gültig-Monate ab dem Versand des Codes).'), em,
    h('div', { class: 'row', style: 'margin-top:8px' }, h('button', { class: 'btn', onclick: speichernE }, 'Speichern')));

  return h('div', { class: 'stack' }, h('div', { class: 'top' }, h('h1', {}, 'Online-Shop')), kopf, bestellungen, artikelKarte, listen, einstellungen);
};
