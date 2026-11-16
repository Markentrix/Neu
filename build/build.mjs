// Generator für website-fertig/ (liegt NEBEN dem Export, wird nicht hochgeladen).
// Aufruf: node build.mjs   (aus dem Ordner build/)
import fs from 'node:fs'; import path from 'node:path';
const HIER = path.dirname(new URL(import.meta.url).pathname), ZIEL = path.resolve(HIER, '../website-fertig');
const seiten = JSON.parse(fs.readFileSync(path.join(HIER, 'data/seiten.json'), 'utf8'));
const bilder = JSON.parse(fs.readFileSync(path.join(HIER, 'data/bilder.json'), 'utf8'));
const SITE = '{{SITE_URL}}';
const F = { name: 'Verein aktiver Tierfreunde e.V.', heim: 'Waldtierheim Celle', str: 'Im Sande 3', plz: '29227', ort: 'Celle', tel: '05141 32900', telLink: '+49514132900', mail: 'info@tierfreunde-celle.de',
  fb: 'https://de-de.facebook.com/TierschutzCelle', verband: 'https://www.tierschutz-niedersachsen.de/', spende: 'https://www.betterplace.org/de/projects/27946-aktiver-tierschutz-in-celle-braucht-deine-unterstutzung/donations/new',
  route: 'https://www.google.com/maps/dir/?api=1&destination=Im+Sande+3%2C+29227+Celle', iban: 'DE78 2695 1311 0000 1792 00', bic: 'NOLADE21GFW', bank: 'Sparkasse Celle-Gifhorn-Wolfsburg' };
const WOCHE = [['Montag', 1, '8 bis 11 Uhr', '15 bis 17 Uhr'], ['Dienstag', 2, '8 bis 11 Uhr', ''], ['Mittwoch', 3, '8 bis 11 Uhr', '15 bis 17 Uhr'], ['Donnerstag', 4, '8 bis 11 Uhr', ''], ['Freitag', 5, '8 bis 11 Uhr', '15 bis 17 Uhr'], ['Samstag', 6, '10 bis 11 Uhr', ''], ['Sonntag', 0, '10 bis 11 Uhr', '15 bis 17 Uhr']];

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const asc = p => p.replace(/ü/g, 'ue').replace(/ö/g, 'oe').replace(/ä/g, 'ae').replace(/ß/g, 'ss').replace(/Ü/g, 'Ue').replace(/Ö/g, 'Oe').replace(/Ä/g, 'Ae');
const datum = d => d ? d.slice(8, 10) + '.' + d.slice(5, 7) + '.' + d.slice(0, 4) : '';
const nurText = h => h.replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#\d+;|&[a-z]+;/g, ' ').replace(/\s+/g, ' ').trim();
const kurz = (t, n) => { t = nurText(t); if (t.length <= n) return t; t = t.slice(0, n); return t.slice(0, t.lastIndexOf(' ')).replace(/[,;:.\s]+$/, '') + ' …'; };
const titel = t => t.length <= 59 ? t : t.slice(0, 58).replace(/\s+\S*$/, '') + '…';
const mehrzahl = (n, eins, viele) => n === 1 ? `1 ${eins}` : `${n} ${viele}`;

const weiter = []; // alt -> neu
const alle = new Map();
for (const s of seiten) { s.neu = asc(s.path); if (s.kind === 'detail' && !s.name) { const t = (s.title || '').split(/ [-|] /)[0].trim(), sl = s.path.split('/').pop().replace('.html', '').replace(/^id-\d+-/, '').replace(/-\d+$/, '').replace(/-/g, ' '); s.name = t || sl.charAt(0).toUpperCase() + sl.slice(1); } if (s.neu !== s.path) weiter.push([s.path, s.neu]); alle.set(s.neu, s); }
const P = p => alle.get(p);
const benutzt = new Set();

function bild(k, { alt = '', sizes = '100vw', lazy = true, klein = false, cls = '', extra = '', xl = false } = {}) {
  const b = bilder[k]; if (!b) return '';
  if (xl && b.xw) { benutzt.add(k + '-s'); benutzt.add(k + '-l'); benutzt.add(k + '-xl'); return `<img src="/bilder/${k}-l.webp" srcset="/bilder/${k}-s.webp ${b.sw}w, /bilder/${k}-l.webp ${b.w}w, /bilder/${k}-xl.webp ${b.xw}w" sizes="${sizes}" width="${b.xw}" height="${b.xh}" alt="${esc(alt)}"${lazy ? ' loading="lazy" decoding="async"' : ' fetchpriority="high"'}${cls ? ` class="${cls}"` : ''}${extra}>`; }
  benutzt.add(k + '-s'); if (!klein) benutzt.add(k + '-l');
  const zwei = !klein && b.w > b.sw;
  return `<img src="/bilder/${k}-${zwei ? 'l' : 's'}.webp"${zwei ? ` srcset="/bilder/${k}-s.webp ${b.sw}w, /bilder/${k}-l.webp ${b.w}w" sizes="${sizes}"` : ''} width="${zwei ? b.w : b.sw}" height="${zwei ? b.h : b.sh}" alt="${esc(alt)}"${lazy ? ' loading="lazy" decoding="async"' : ' fetchpriority="high"'}${cls ? ` class="${cls}"` : ''}${extra}>`;
}

/* ---------- Inhalte aufbereiten ---------- */
function text(s) {
  let h = s.html || '';
  h = h.replace(/<a data-pdf="[^"]*">(.*?)<\/a>/g, (m, t) => /paten/i.test(m) ? `<a href="/dokumente/patenschaftsvertrag.pdf">${t}</a>` : t);
  h = h.replace(/<a href="(\/[^"]*)">(.*?)<\/a>/g, (m, href, t) => {
    const ziel = asc(decodeURIComponent(href.replace(/&amp;/g, '&'))).split(/[?#]/)[0];
    return alle.has(ziel) ? `<a href="${ziel}">${t}</a>` : t;
  });
  h = h.replace(/<a href="(https:[^"]*)">/g, '<a href="$1" rel="noopener">');
  h = h.replace(/http:\/\//g, '');
  h = h.replace(/\[Alle anzeigen\]/g, '').replace(/<p>\s*Seite \d+ von \d+\s*<\/p>/g, '').replace(/<p>\s*(Zurück|zurück zur Übersicht)\s*<\/p>/g, '');
  const erste = h.match(/^\s*<h3>(.*?)<\/h3>/);
  if (erste && s.name && nurText(erste[1]).toLowerCase() === s.name.toLowerCase()) h = h.slice(erste[0].length);
  h = h.replace(/<p>\s*(<br>\s*)+/g, '<p>').replace(/(<br>\s*)+<\/p>/g, '</p>').replace(/(<br>\s*){3,}/g, '<br><br>').replace(/<p>\s*<\/p>/g, '');
  return h.trim();
}
const ART = { hunde: ['Hund', 'Hunde'], katzen: ['Katze', 'Katzen'], 'vermittlungshilfe-privat': ['Privatvermittlung', 'Vermittlungshilfe privat'] };
const tiere = { hunde: [], katzen: [], 'vermittlungshilfe-privat': [] };
for (const kat of Object.keys(tiere)) {
  const liste = P(`/im-waldtierheim-celle/${kat}.html`), ordnung = (liste.items || []).map(i => '/' + asc(decodeURIComponent(i[0])));
  const d = seiten.filter(s => s.kind === 'detail' && s.neu.startsWith(`/im-waldtierheim-celle/${kat}/`));
  d.sort((a, b) => { const i = ordnung.indexOf(a.neu), j = ordnung.indexOf(b.neu); return (i < 0 ? 999 : i) - (j < 0 ? 999 : j) || (b.date || '').localeCompare(a.date || ''); });
  d.forEach(s => { s.kat = kat; s.id = (kat[0] + '-' + s.neu.split('/').pop().replace('.html', '')).toLowerCase().replace(/[^a-z0-9-]/g, ''); });
  const VORN = { 'bruce.html': 3, 'hans-peter.html': 3 };
  d.forEach(s => { const n = VORN[s.neu.split('/').pop()]; if (n && s.images[n]) s.images.unshift(...s.images.splice(n, 1)); });
  tiere[kat] = d;
}
const heimtiere = [...tiere.hunde, ...tiere.katzen];
const archiv = k => seiten.filter(s => s.kind === 'detail' && s.neu.startsWith(`/happy-end/${k}/`)).sort((a, b) => (b.date || '').localeCompare(a.date || ''));
const vermHunde = archiv('hunde-vermittelt'), vermKatzen = archiv('katzen-vermittelt'), vermKlein = archiv('kleintiere-vermittelt');
const gruesse = archiv('gruesse-vom-neuen-zuhause').filter(s => !s.neu.endsWith('dein-glueckliches-fuerimmer-zuhause.html'));
const news = seiten.filter(s => s.kind === 'detail' && s.neu.startsWith('/aktuelles/')).sort((a, b) => (b.date || '').localeCompare(a.date || ''));
const feste = seiten.filter(s => s.kind === 'detail' && s.neu.startsWith('/verein/aktionen-und-feste/')).sort((a, b) => (b.date || '').localeCompare(a.date || ''));
const happyZahl = vermHunde.length + vermKatzen.length + vermKlein.length;

/* ---------- Bausteine ---------- */
const orgLd = () => ({ '@type': ['AnimalShelter', 'NGO'], '@id': SITE + '/#tierheim', name: 'Waldtierheim Celle', legalName: F.name, alternateName: ['Verein aktiver Tierfreunde e.V.', 'Tierfreunde Celle'], url: SITE, telephone: F.telLink, email: F.mail,
  image: SITE + '/bilder/' + HERO_BILD + '-l.webp', foundingDate: '1992-01-23', description: 'Privater Tierschutzverein in Celle. Betreibt seit 2003 das Waldtierheim in Altencelle und vermittelt Hunde, Katzen und Kleintiere.',
  address: { '@type': 'PostalAddress', streetAddress: F.str, postalCode: F.plz, addressLocality: F.ort, addressRegion: 'Niedersachsen', addressCountry: 'DE' },
  openingHoursSpecification: [
    { '@type': 'OpeningHoursSpecification', dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], opens: '08:00', closes: '11:00' },
    { '@type': 'OpeningHoursSpecification', dayOfWeek: ['Saturday', 'Sunday'], opens: '10:00', closes: '11:00' },
    { '@type': 'OpeningHoursSpecification', dayOfWeek: ['Monday', 'Wednesday', 'Friday', 'Sunday'], opens: '15:00', closes: '17:00' }],
  sameAs: [F.fb], memberOf: { '@type': 'Organization', name: 'Verband Niedersächsischer Tierschutzvereine e.V.', url: F.verband } });
const pfadLd = kr => ({ '@type': 'BreadcrumbList', itemListElement: kr.map(([n, u], i) => ({ '@type': 'ListItem', position: i + 1, name: n, item: SITE + (u === '/' ? '/' : u) })) });
const pfad = kr => kr.length > 1 ? `<nav aria-label="Du bist hier"><ol class="pfad">${kr.map(([n, u], i) => i === kr.length - 1 ? `<li aria-current="page">${esc(n)}</li>` : `<li><a href="${u}">${esc(n)}</a></li>`).join('')}</ol></nav>` : '';
const NAV = [['Tiere', '/im-waldtierheim-celle.html'], ['Happy End', '/happy-end.html'], ['Verein', '/verein.html'], ['Aktuelles', '/aktuelles.html'], ['Kontakt', '/kontakt.html']];
const wochenTabelle = (kopf = true) => `<table class="woche"><caption class="nur-sr">Öffnungszeiten des Waldtierheims Celle</caption>${kopf ? '<thead><tr><th scope="col">Tag</th><th scope="col">Vormittag</th><th scope="col">Nachmittag</th></tr></thead>' : ''}<tbody>${WOCHE.map(([t, n, v, na]) => `<tr data-tag="${n}"><th scope="row">${t}</th><td>${v}</td><td${na ? '' : ' data-zu'}>${na || 'geschlossen'}</td></tr>`).join('')}</tbody></table>`;

function geruest({ pfad: p, title, desc, body, ld = [], hero, heroXl = false, noindex, aktiv, leiste, htmlKlasse = '' }) {
  const canon = SITE + (p === '/index.html' ? '/' : p);
  const graph = { '@context': 'https://schema.org', '@graph': ld };
  const bar = leiste || [`<a href="/deine-hilfe.html#spenden">Spenden</a>`, `<a href="/im-waldtierheim-celle.html">Tiere ansehen</a>`];
  return `<!doctype html>
<html lang="de"${htmlKlasse ? ` class="${htmlKlasse}"` : ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
${noindex ? '<meta name="robots" content="noindex">' : `<link rel="canonical" href="${canon}">`}
<meta name="theme-color" content="#EADFC8">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="Waldtierheim Celle">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
${noindex ? '' : `<meta property="og:url" content="${canon}">`}
<link rel="preload" href="/schrift/bricolage-800.woff2" as="font" type="font/woff2" crossorigin>
${hero ? `<link rel="preload" as="image" href="/bilder/${hero}-l.webp" imagesrcset="/bilder/${hero}-s.webp ${bilder[hero].sw}w, /bilder/${hero}-l.webp ${bilder[hero].w}w${heroXl && bilder[hero].xw ? `, /bilder/${hero}-xl.webp ${bilder[hero].xw}w` : ''}" imagesizes="${heroXl ? '100vw' : '(max-width: 60rem) 92vw, 46vw'}" fetchpriority="high">` : ''}
<link rel="stylesheet" href="/css/stil.css">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="manifest" href="/site.webmanifest">
${ld.length ? `<script type="application/ld+json">${JSON.stringify(graph).replace(/</g, '\\u003c')}</script>` : ''}
<script src="/js/app.js" defer></script>
</head>
<body>
<a class="sprung" href="#inhalt">Zum Inhalt springen</a>
<header class="kopf"><div class="huelle kopf-innen">
<a class="marke" href="/" aria-label="Waldtierheim Celle, Startseite">Waldtierheim Celle<small>Verein <b>aktiver</b> Tierfreunde e.V.</small></a>
<button class="menue-knopf" type="button" aria-expanded="false" aria-controls="nav">Menü</button>
<nav class="nav" id="nav" aria-label="Hauptnavigation">
<button class="menue-knopf nav-zu" type="button">Schließen</button>
${NAV.map(([n, u]) => `<a href="${u}"${aktiv === u ? ' aria-current="page"' : ''}>${n}</a>`).join('\n')}
<a class="knopf" href="/deine-hilfe.html"${aktiv === '/deine-hilfe.html' ? ' aria-current="page"' : ''}>Spenden und helfen</a>
</nav>
</div></header>
<main id="inhalt">
${body}
</main>
<footer class="fuss"><div class="huelle">
<p class="fuss-name">Waldtierheim Celle${SITTICH_FUSS}</p>
<div class="fuss-raster">
<div><h2>Besuch</h2><address>${F.name}<br>${F.str}, ${F.plz} ${F.ort}<br>Zufahrt Richtung Osterloh<br><a href="tel:${F.telLink}">Telefon ${F.tel}</a><br><a href="mailto:${F.mail}">${F.mail}</a></address></div>
<div><h2>Öffnungszeiten</h2><dl><dt>Mo bis Fr</dt><dd>8 bis 11 Uhr</dd><dt>Sa und So</dt><dd>10 bis 11 Uhr</dd><dt>Mo, Mi, Fr, So</dt><dd>auch 15 bis 17 Uhr</dd></dl></div>
<div><h2>Mehr</h2><ul><li><a href="/im-waldtierheim-celle/vermittlungshilfe-privat.html">Vermittlungshilfe privat</a></li><li><a href="/verein/vorstand.html">Vorstand</a></li><li><a href="/verein/satzung.html">Satzung</a></li><li><a href="/deine-hilfe/danke-an-die-helfer.html">Danke an die Helfer</a></li><li><a href="${F.fb}" rel="noopener">Waldtierheim auf Facebook</a></li><li><a href="${F.verband}" rel="noopener">Mitglied im Verband Niedersächsischer Tierschutzvereine e.V.</a></li></ul></div>
</div>
<div class="fuss-recht"><a href="/impressum.html">Impressum</a><a href="/datenschutz.html">Datenschutz</a><span data-mk="cookies"></span><span style="padding-block:.6rem">Fotos: Verein aktiver Tierfreunde e.V. und Einsendungen</span></div>
</div></footer>
<div class="aktionsleiste">${bar.join('')}</div>
</body>
</html>
`;
}
const SITTICH_FUSS = '<svg class="sittich" viewBox="0 0 80 124" aria-hidden="true" focusable="false"><use href="/zeichen.svg#sittich"/></svg>';
const raus = []; // {pfad, index}
function schreibe(p, html, index = true) { const f = path.join(ZIEL, p); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, html); raus.push({ p, index }); }

function tierDaten(s) {
  const f = s.fields || {}, z = [];
  const r = [f.Rasse, f.Geboren ? 'geboren ' + f.Geboren : ''].filter(Boolean).join(', ');
  if (r) z.push(r);
  if (s.date && s.kat !== 'vermittlungshilfe-privat') z.push('Steckbrief seit ' + datum(s.date));
  return z;
}
function schild(s, nr, { gross = false, sizes = '(max-width: 30rem) 46vw, (max-width: 60rem) 30vw, 22vw', vt = true, lazy = true } = {}) {
  const k = s.images[0], art = ART[s.kat][0];
  return `<a class="schild${gross ? ' schild-gross' : ''}" href="${s.neu}" data-nr="${nr}">
<div class="schild-bild"${vt ? ` style="view-transition-name:${s.id}"` : ''}>${k ? bild(k, { alt: `${s.name}, ${art} im Waldtierheim Celle`, sizes, lazy }) : ''}</div>
<div class="schild-text"><span class="schild-name">${esc(s.name)}</span>
<p class="schild-daten">${tierDaten(s).map(esc).join('<br>')}</p>
${s.date && s.kat !== 'vermittlungshilfe-privat' ? `<p class="tage" data-seit="${s.date}"><span class="tage-zahl"></span><small></small></p>` : ''}</div></a>`;
}
function formular({ typ = 'kontakt', tier = '', knopf, nachricht = 'Deine Nachricht' }) {
  return `<form class="formular" data-anfrage="${typ}" action="/kontakt.html" method="get">
${tier ? `<input type="hidden" name="tier" value="${esc(tier)}">` : ''}
<div class="zwei-felder">
<div class="feld"><label for="f-name">Vorname und Name</label><input id="f-name" name="name" type="text" autocomplete="name" required aria-describedby="e-name"><p class="fehler" id="e-name" data-fehler="name"></p></div>
<div class="feld"><label for="f-email">E-Mail (für unsere Antwort)</label><input id="f-email" name="email" type="email" autocomplete="email" inputmode="email" required aria-describedby="e-email"><p class="fehler" id="e-email" data-fehler="email"></p></div>
</div>
<div class="feld"><label for="f-telefon">Telefon (freiwillig)</label><input id="f-telefon" name="telefon" type="tel" autocomplete="tel" aria-describedby="e-telefon"><p class="fehler" id="e-telefon" data-fehler="telefon"></p></div>
<div class="feld"><label for="f-nachricht">${nachricht}</label><textarea id="f-nachricht" name="nachricht" required enterkeyhint="send" aria-describedby="e-nachricht"></textarea><p class="fehler" id="e-nachricht" data-fehler="nachricht"></p></div>
<div class="honig" aria-hidden="true"><label for="f-website">Bitte leer lassen</label><input id="f-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
<div><div class="haken"><input id="f-einwilligung" name="einwilligung" type="checkbox" value="ja" required aria-describedby="e-einwilligung"><label for="f-einwilligung">Ich habe die <a href="/datenschutz.html">Datenschutzerklärung</a> gelesen und bin einverstanden, dass meine Angaben zur Beantwortung meiner Anfrage gespeichert werden. Die Einwilligung kann ich jederzeit per E-Mail widerrufen.</label></div><p class="fehler" id="e-einwilligung" data-fehler="einwilligung"></p></div>
<div class="meldung" role="status" aria-live="polite"></div>
<div><button class="knopf" type="submit">${knopf}</button></div>
<p class="klein neben">Lieber direkt? <a href="tel:${F.telLink}">Telefon ${F.tel}</a> oder <a href="mailto:${F.mail}">${F.mail}</a></p>
</form>`;
}
const zeichen = (id, cls = 'zeichen') => `<svg class="${cls}" aria-hidden="true" focusable="false"><use href="/zeichen.svg#${id}"/></svg>`;
const spur = (id, n) => `<p class="spur" aria-hidden="true">${Array.from({ length: n }, () => `<svg viewBox="0 0 64 64"><use href="/zeichen.svg#${id}"/></svg>`).join('')}</p>`;
const sittich = `<svg class="sittich" viewBox="0 0 80 124" aria-hidden="true" focusable="false"><use href="/zeichen.svg#sittich"/></svg>`;
const lichtDialog = `<dialog class="licht" aria-label="Foto in groß"><form method="dialog"><button>Schließen</button></form><img src="" alt="" width="1200" height="900"></dialog>`;
const kontoBlock = `<dl class="konto"><dt>Kontoinhaber</dt><dd>${F.name} – Tierschutz</dd><dt>IBAN</dt><dd>${F.iban}</dd><dt>BIC</dt><dd>${F.bic}</dd><dt>Bank</dt><dd>${F.bank}</dd></dl>
<p><button class="kopier" type="button" data-kopiere="${F.iban.replace(/ /g, '')}">IBAN kopieren</button></p>`;

/* ---------- Startseite ---------- */
const heroTier = tiere.hunde.find(s => s.neu.endsWith('/cora.html')) || tiere.hunde[0];
const HERO_BILD = heroTier.images.find(k => bilder[k] && bilder[k].xw) || heroTier.images[0];
const festBild = '71a960304db5', helferBild = '01f19cc3905e';
const laengste = heimtiere.filter(s => s !== heroTier && s.date && s.images.length && !/verwilderte/.test(s.neu)).sort((a, b) => a.date.localeCompare(b.date)).slice(0, 5);
const kachel = (s, i) => `<a class="kachel enthuellt" href="${s.neu}">${bild(s.images[0], { alt: `${s.name}, ${ART[s.kat][0]} im Waldtierheim Celle`, sizes: i === 0 ? '(max-width: 48rem) 92vw, 46vw' : '(max-width: 48rem) 46vw, 24vw' })}<span class="kachel-text"><span><span class="schild-name">${esc(s.name)}</span><span class="schild-daten">${esc(tierDaten(s)[0] || '')}</span></span><span class="tage" data-seit="${s.date}"><span class="tage-zahl"></span><small></small></span></span></a>`;
const lauf = heimtiere.filter(s => !/verwilderte|Junghunde|Jungkatzen|Katzenkinder/.test(s.name + s.neu)).map(s => s.name);
const streifen = [...vermHunde.slice(0, 7), ...vermKatzen.slice(0, 7)].filter(s => s.images[0]);
const brief = gruesse.find(s => s.neu.endsWith('/quickie.html')) || gruesse[0];
const FAQ = [
  ['Wann hat das Waldtierheim Celle geöffnet?', 'Vormittags Montag bis Freitag von 8 bis 11 Uhr, Samstag und Sonntag von 10 bis 11 Uhr. Nachmittags zusätzlich Montag, Mittwoch, Freitag und Sonntag von 15 bis 17 Uhr.'],
  ['Wo liegt das Waldtierheim?', 'Im Sande 3, 29227 Celle, auf einem Waldgrundstück am Rand von Altencelle. Die Zufahrt führt Richtung Osterloh.'],
  ['Wie lerne ich ein Tier kennen?', 'Sieh dir den Steckbrief an und komm in den Öffnungszeiten ins Waldtierheim. Unser Team vor Ort beantwortet deine Fragen zum Tier. Du kannst auch über das Formular am Steckbrief oder unter 05141 32900 anfragen.'],
  ['Werden Katzenkinder einzeln vermittelt?', 'Katzenkinder vermitteln wir mindestens zu zweit oder zu einer bereits vorhandenen, etwa gleichaltrigen Katze. Spielen, Kuscheln und gegenseitiges Putzen mit einem Katzenfreund sind für eine gesunde Entwicklung wichtig.'],
  ['Wie werde ich Gassi-Geher?', 'Melde dich während der Öffnungszeiten direkt im Waldtierheim. Dort besprechen wir alles Weitere mit dir.'],
  ['Was kostet die Mitgliedschaft im Verein?', 'Den Beitrag bestimmst du selbst, mindestens 20 € im Jahr. Den Aufnahmeantrag bekommst du im Tierheim. Einmal im Jahr, im Frühjahr, laden wir zur Mitgliederversammlung ein.'],
  ['Wofür wird meine Spende verwendet?', 'Für Tierarztkosten wie die medizinische Versorgung bei Krankheit und Kastrationen, für Futter und für die Instandhaltung von Hundezwingern und Katzenhaus. Die Spende kommt direkt den Tieren im Waldtierheim zugute.'],
  ['Bekomme ich eine Spendenbescheinigung?', 'Für Spenden über unseren Partner betterplace.org stellt betterplace die Spendenbescheinigung zu Beginn des folgenden Jahres zu.'],
  ['Ich muss mein Tier privat abgeben. Könnt ihr helfen?', 'Ja, mit der Vermittlungshilfe privat. Wir veröffentlichen eine Anzeige für dein Tier, sie bleibt etwa sechs Wochen aktiv. Das Tier bleibt bei dir, Interessierte melden sich direkt bei dir.'],
  ['Sucht ihr Plätze für scheue Katzen?', 'Ja. Für unsere scheuen und verwilderten Katzen suchen wir Bauernhöfe, Reiterhöfe und ähnliche Orte, an denen sie einen geschützten Platz zum Leben finden.']];

function start() {
  const body = `<section class="hero buehne">
${bild(HERO_BILD, { alt: `Hündin ${heroTier.name} liegt lachend im Sand des Waldtierheims Celle`, sizes: '100vw', lazy: false, xl: true, cls: 'buehne-bild' })}
<div class="huelle buehne-innen">
<div class="hero-text">
<h1><span>Waldtierheim Celle</span><span>Zuhause gesucht</span></h1>
<p class="statement">Cora hat vier Jahre in einem Tierheim in Rumänien gelebt. Jetzt wartet sie bei uns im Wald am Rand von Altencelle auf ihre Menschen, so wie viele andere Hunde und Katzen.</p>
<div class="hero-aktion"><a class="knopf" href="/im-waldtierheim-celle.html">Tiere kennenlernen</a><a href="#spenden">Für die Tiere spenden</a></div>
<p class="status" data-status>Geöffnet jeden Vormittag, Mo, Mi, Fr und So auch 15 bis 17 Uhr</p>
</div>
<div class="hero-schild">${sittich}<a class="schild" href="${heroTier.neu}"><div class="schild-text"><span class="schild-name">Das ist ${esc(heroTier.name)}</span><p class="schild-daten">${tierDaten(heroTier).map(esc).join('<br>')}</p><p class="tage" data-seit="${heroTier.date}"><span class="tage-zahl"></span><small></small></p></div></a></div>
</div></section>
<div class="lauf" aria-hidden="true"><div class="lauf-band">${[0, 1].map(() => lauf.map(n => `<span>${esc(n)}${zeichen('hundepfote')}</span>`).join('')).join('')}</div></div>

<section class="abschnitt" aria-labelledby="h-warten"><div class="huelle">
<div class="kopfzeile"><h2 id="h-warten">Diese Tiere warten am längsten</h2><p>Die Zahl zählt die Tage, seit denen der Steckbrief online ist.</p></div>
<div class="mosaik">${laengste.map(kachel).join('\n')}</div>
<p style="margin-top:2rem;display:flex;flex-wrap:wrap;align-items:center;gap:1.5rem"><a class="knopf knopf-still" href="/im-waldtierheim-celle.html">Alle ${heimtiere.length} Steckbriefe ansehen</a>${spur('hundepfote', 4)}</p>
</div></section>

${(() => { const g = tiere.hunde.find(t => t.neu.endsWith('ernie-und-bert.html')); if (!g) return ''; return `<section class="abschnitt geschichte" aria-labelledby="h-geschichte"><div class="huelle geschichte-raster">
<div class="geschichte-bilder"><figure class="enthuellt">${bild(g.images[0], { alt: 'Die Doggen-Brüder Ernie und Bert sitzen nebeneinander im Sand', sizes: '(max-width: 60rem) 52vw, 28vw' })}</figure><figure class="enthuellt">${bild(g.images[1], { alt: 'Eine der beiden Doggen trägt ein Stofftier im Maul', sizes: '(max-width: 60rem) 40vw, 22vw' })}</figure></div>
<div><h2 id="h-geschichte" style="hyphens:manual">Ernie und Bert hatten nur einander</h2>
<blockquote class="statement">„Als sie zu uns kamen, waren sie nahezu verhungert und körperlich in einem erschreckend schlechten Zustand. Doch sie hatten einander.“</blockquote>
<p>Die beiden Deutschen Doggen sind Brüder und vier Jahre alt. Gemeinsam haben sie gekämpft, zugenommen und Schritt für Schritt wieder gelernt, Vertrauen zu fassen. Heute suchen die zwei sanften Riesen gemeinsam ein Zuhause.</p>
<p class="tage" data-seit="${g.date}" style="text-align:left;margin:1.5rem 0"><span class="tage-zahl"></span><small></small></p>
<p><a class="knopf" href="${g.neu}">Ernie und Bert kennenlernen</a></p></div>
</div></section>`; })()}

<section class="abschnitt dunkel" aria-labelledby="h-besuch"><div class="huelle besuch">
<div><h2 id="h-besuch">Komm im Wald vorbei</h2>
<p class="status" data-status style="margin:0 0 1.5rem">Zwei Öffnungsfenster am Tag</p>
${wochenTabelle()}
<p class="klein neben" style="margin-top:1rem">In diesen Zeiten ist unser Team vor Ort und beantwortet deine Fragen zu den Tieren.</p></div>
<div class="anfahrt">
<figure>${bild(P('/kontakt.html').images[0], { alt: 'Einfahrt mit Tor zum Waldtierheim Celle zwischen Kiefern', sizes: '(max-width: 60rem) 92vw, 30vw' })}</figure>
<address>${F.str}<br>${F.plz} ${F.ort}<br><span class="klein neben">Zufahrt Richtung Osterloh</span></address>
<a class="tel" href="tel:${F.telLink}">${F.tel}</a>
<p><a class="knopf" href="${F.route}" rel="noopener">Route in Google Maps öffnen</a></p>
</div>
</div></section>

<section class="abschnitt" aria-labelledby="h-happy"><div class="huelle happy">
<div><p class="grosszahl" aria-hidden="true">${happyZahl}</p>
<h2 id="h-happy">Koffer gepackt und ausgezogen</h2>
<p style="margin-top:1.25rem;max-width:40ch">${happyZahl} Vermittlungen sind in unserem Archiv mit Steckbrief dokumentiert. Danke an alle frisch gebackenen Dosenöffnerinnen und Dosenöffner.</p>
<p><a class="knopf knopf-still" href="/happy-end.html">Happy Ends ansehen</a></p>${spur('katzenpfote', 5)}</div>
<blockquote class="brief">
<p>„Ich kann nur sagen, dass sie wirklich eine Traumkatze ist und ich wirklich erstaunt bin, wie toll sie das macht. Sie ist total verschmust und genießt ihre Streicheleinheiten, sie kommt mit aufs Sofa und legt sich zu uns.“</p>
<p>„Für uns war es auf jeden Fall die richtige Entscheidung.“</p>
<footer>${bild(brief.images[0], { alt: 'Katze Quickie in ihrem neuen Zuhause', klein: true })}<p class="klein" style="margin:0">L. R. über Katze Quickie, ${datum(brief.date)}<br><a href="${brief.neu}">Den ganzen Gruß lesen</a> oder <a href="/happy-end/gruesse-vom-neuen-zuhause.html">alle ${gruesse.length} Grüße</a></p></footer>
</blockquote>
</div>
<ul class="streifen" aria-label="Vermittelte Tiere">${streifen.map(t => `<li><a href="${t.neu}">${bild(t.images[0], { alt: `${t.name}, vermittelt`, klein: true })}<span>${esc(t.name)}</span></a></li>`).join('')}</ul></section>

<section class="hilfe" id="spenden" aria-labelledby="h-hilfe"><div class="band buehne">${bild(helferBild, { alt: 'Freiwillige schaufeln Erde für Sandsäcke auf dem Gelände des Waldtierheims', sizes: '100vw', xl: true, cls: 'buehne-bild' })}<div class="huelle buehne-innen"><div><h2 id="h-hilfe">Deine Spende macht das möglich</h2><p class="statement" style="margin-top:1rem">Wir sind ein privater Tierschutzverein. Tierarzt, Futter und Unterkünfte bezahlen wir aus Mitgliedsbeiträgen und Spenden.</p><p class="klein" style="margin:1rem 0 0">Foto: Freiwillige sichern das Waldtierheim gegen Hochwasser, Dezember 2023.</p></div></div></div>
<div class="huelle spenden-raster">
<div><h3>Dafür brauchen wir deine Hilfe</h3>
<ul class="jahre wofuer"><li><b>Tierarzt</b><span>Medizinische Versorgung bei Krankheit und Kastrationen.</span></li><li><b>Futter</b><span>Die tägliche Versorgung unserer Hunde, Katzen und Kleintiere.</span></li><li><b>Unterkunft</b><span>Instandhaltung von Hundezwingern und Katzenhaus.</span></li></ul>
<p class="klein neben">Für Spenden über betterplace.org bekommst du zu Beginn des folgenden Jahres eine Spendenbescheinigung von betterplace.</p></div>
<div class="spendenbox"><h3>Jetzt spenden</h3>${kontoBlock}<p style="margin:0"><a class="knopf" href="${F.spende}" rel="noopener">Online spenden über betterplace.org</a></p></div>
</div>
<div class="huelle" style="padding-bottom:var(--abschnitt)">
<h3 style="margin-bottom:1.5rem">Du kannst auch anders helfen</h3>
<ul class="wege" style="margin-top:0">
<li><h3>Patenschaft</h3><div><p>Du kannst kein Tier aufnehmen, aber eines liegt dir am Herzen? Unterstütze genau dieses Tier mit Futter, Sachspenden oder einem monatlichen Betrag und besuche es in den Öffnungszeiten.</p><p><a href="/dokumente/patenschaftsvertrag.pdf">Patenschaftsvertrag als PDF (155 KB)</a></p></div></li>
<li><h3>Mitglied werden</h3><div><p>Den Beitrag bestimmst du selbst, mindestens 20 € im Jahr. Den Aufnahmeantrag bekommst du bei uns im Tierheim.</p></div></li>
<li><h3>Gassi gehen</h3><div><p>Unsere Hunde freuen sich über Spaziergänge. Melde dich dafür während der Öffnungszeiten direkt im Waldtierheim.</p></div></li>
</ul>
<p style="margin-top:2.5rem"><a class="knopf knopf-still" href="/deine-hilfe.html">Alles zur Unterstützung lesen</a></p>
</div></section>

<section class="abschnitt" aria-labelledby="h-verein"><div class="huelle verein">
<div><h2 id="h-verein">Tierschutz in Celle seit 1992</h2>
<ul class="jahre">
<li><b>1992</b><span>Gründung am 23. Januar in Celle. Am Anfang steht die Kastration frei lebender Katzen.</span></li>
<li><b>Bis 2002</b><span>Zehn Jahre ohne feste Bleibe. Die Tiere leben bei Mitgliedern oder in gemieteten Zwingern.</span></li>
<li><b>2003</b><span>Bezug und Eröffnung des Waldtierheims auf 9 Hektar Wald am Rand von Altencelle.</span></li>
<li><b>Heute</b><span>Eingetragen beim Amtsgericht Celle, Mitglied im Verband Niedersächsischer Tierschutzvereine, finanziert vor allem über Mitgliedsbeiträge und Spenden.</span></li>
</ul>
<p><a class="knopf knopf-still" href="/verein.html">Den Verein kennenlernen</a></p></div>
<figure class="enthuellt">${bild(festBild, { alt: 'Besucherinnen und Besucher zwischen Kiefern beim Tag der offenen Tür im Waldtierheim Celle', sizes: '(max-width: 60rem) 92vw, 46vw', xl: true })}<figcaption>Tag der offenen Tür im Waldtierheim, September 2024</figcaption></figure>
</div></section>

<section class="abschnitt" style="padding-top:0" aria-labelledby="h-neu"><div class="huelle zwei">
<div><h2 id="h-neu">Neues aus dem Tierheim</h2><p style="margin-top:1.5rem"><a href="/aktuelles.html">Alle Meldungen</a></p></div>
<ul class="zeilen">${news.slice(0, 3).map(n => `<li><a class="zeile" href="${n.neu}"><time datetime="${n.date}">${datum(n.date)}</time><h3>${esc(n.name)}</h3></a></li>`).join('')}</ul>
</div></section>

<section class="abschnitt" style="padding-top:0" aria-labelledby="h-faq"><div class="huelle zwei">
<div><h2 id="h-faq">Kurz gefragt</h2><div class="paar" aria-hidden="true">${sittich.replace(' class="sittich"', '')}${sittich.replace(' class="sittich"', '')}</div><div class="ast" aria-hidden="true"></div></div>
<div class="fragen">${FAQ.map(([q, a]) => `<details><summary>${esc(q)}</summary><div><p>${esc(a)}</p></div></details>`).join('\n')}</div>
</div></section>`;
  schreibe('/index.html', geruest({ pfad: '/index.html', title: 'Tierheim in Celle | Waldtierheim Celle', desc: 'Waldtierheim Celle: Hunde und Katzen suchen ein Zuhause. Steckbriefe, Öffnungszeiten, Anfahrt nach Altencelle, Spenden und Patenschaft. Telefon 05141 32900.', body, hero: HERO_BILD, heroXl: true, htmlKlasse: 'auf',
    ld: [orgLd(), { '@type': 'WebSite', '@id': SITE + '/#website', url: SITE, name: 'Waldtierheim Celle', inLanguage: 'de', publisher: { '@id': SITE + '/#tierheim' } },
      { '@type': 'FAQPage', mainEntity: FAQ.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })) }] }));
}

/* ---------- Tierlisten ---------- */
const reiter = aktiv => `<ul class="reiter">${[['Alle', '/im-waldtierheim-celle.html', heimtiere.length], ['Hunde', '/im-waldtierheim-celle/hunde.html', tiere.hunde.length], ['Katzen', '/im-waldtierheim-celle/katzen.html', tiere.katzen.length], ['Kleintiere', '/im-waldtierheim-celle/kleintiere.html', 0], ['Privat', '/im-waldtierheim-celle/vermittlungshilfe-privat.html', tiere['vermittlungshilfe-privat'].length]]
  .map(([n, u, z]) => `<li><a href="${u}"${aktiv === u ? ' aria-current="page"' : ''}>${n === 'Hunde' ? zeichen('hundepfote') : n === 'Katzen' ? zeichen('katzenpfote') : ''}${n} (${z})</a></li>`).join('')}</ul>`;
const wilde = `<div class="hinweis"><p><strong>Wir suchen Plätze für unsere „Wilden“.</strong> Für scheue und verwilderte Katzen suchen wir Bauernhöfe, Reiterhöfe und ähnliche Orte, an denen sie geschützt leben können. <a href="/im-waldtierheim-celle/katzen/verwilderte-hauskatzen.html">Zum Steckbrief der verwilderten Hauskatzen</a></p></div>`;
function tierliste(p, { h1, title, desc, intro, liste, extra = '', leer = '', sort = true, kr }) {
  const body = `<div class="huelle seitenkopf">${pfad(kr)}<h1>${h1}</h1><p class="statement">${intro}</p></div>
<div class="huelle" style="padding-bottom:var(--abschnitt)">
<div class="werkzeug">${reiter(p)}${sort && liste.length > 1 ? `<ul class="reiter"><li><button type="button" data-sortiere aria-pressed="false" aria-controls="liste">Längste Suche zuerst</button></li></ul>` : ''}</div>
${extra}
${liste.length ? `<div class="schilder" id="liste">${liste.map((s, i) => schild(s, i, { lazy: i > 3 })).join('\n')}</div>` : `<div class="hinweis">${leer}</div>`}
</div>`;
  schreibe(p, geruest({ pfad: p, title, desc, body, aktiv: '/im-waldtierheim-celle.html', ld: [pfadLd(kr), { '@type': 'ItemList', name: nurText(h1), itemListElement: liste.map((s, i) => ({ '@type': 'ListItem', position: i + 1, name: s.name, url: SITE + s.neu })) }] }));
}

/* ---------- Steckbrief ---------- */
function steckbrief(s) {
  const art = ART[s.kat], privat = s.kat === 'vermittlungshilfe-privat', f = s.fields || {};
  const kr = [['Start', '/'], ['Tiere', '/im-waldtierheim-celle.html'], [art[1], `/im-waldtierheim-celle/${s.kat}.html`], [s.name, s.neu]];
  const imgs = s.images, h = text(s);
  const daten = [['Rasse', f.Rasse], ['Geboren', f.Geboren], ['Größe', f['Größe']], ['Steckbrief seit', datum(s.date)]].filter(x => x[1]);
  const body = `<div class="huelle" style="padding-top:clamp(1rem,3vw,2.5rem)">${pfad(kr)}
<article class="steck">
<div class="steck-bilder">
${imgs.length ? `<button type="button" class="steck-haupt" data-licht aria-label="Foto von ${esc(s.name)} vergrößern" style="view-transition-name:${s.id}">${bild(imgs[0], { alt: `${s.name}, ${art[0]}${privat ? '' : ' im Waldtierheim Celle'}`, sizes: '(max-width: 60rem) 92vw, 46vw', lazy: false })}</button>` : ''}
${imgs.length > 1 ? `<ul class="leiste" aria-label="Weitere Fotos von ${esc(s.name)}">${imgs.map((k, i) => `<li><button type="button" aria-current="${i === 0}" aria-label="Foto ${i + 1} zeigen">${bild(k, { alt: `${s.name}, Foto ${i + 1}`, klein: true, lazy: i > 4, extra: ` data-gross="/bilder/${k}-l.webp" data-w="${bilder[k].w}" data-h="${bilder[k].h}"` })}</button></li>`).join('')}</ul>` : ''}
</div>
<div>
<div class="steck-kopf"><h1>${esc(s.name)}</h1>${s.date && !privat ? `<p class="tage" data-seit="${s.date}"><span class="tage-zahl"></span><small></small></p>` : ''}</div>
${daten.length ? `<dl class="daten">${daten.map(([a, b]) => `<dt>${a}</dt><dd>${esc(b)}</dd>`).join('')}</dl>` : ''}
${privat ? `<div class="hinweis"><p><strong>Vermittlung von privat.</strong> ${esc(s.name)} lebt nicht im Waldtierheim. Bitte wende dich bei Fragen direkt an die Halterin oder den Halter unter den Kontaktdaten im Text.</p></div>` : ''}
<div class="lesen">${h}</div>
${privat ? '' : `<p style="margin-top:2rem"><a class="knopf" href="#anfrage">${esc(s.name)} kennenlernen</a></p>`}
</div>
</article></div>
${privat ? '' : `<section class="abschnitt anfrage" id="anfrage" aria-labelledby="h-anfrage"><div class="huelle anfrage-raster">
<div><h2 id="h-anfrage">Frag nach ${esc(s.name)}</h2><p style="margin-top:1.5rem">Schreib uns, wer du bist und wie ${esc(s.name)} bei dir leben würde. Wir melden uns per E-Mail oder Telefon.</p><p class="status" data-status>Oder komm in den Öffnungszeiten vorbei</p><p style="margin-top:1.5rem">Du kannst ${esc(s.name)} nicht aufnehmen? Mit einer <a href="/deine-hilfe.html#patenschaft">Patenschaft</a> oder einer <a href="/deine-hilfe.html#spenden">Spende</a> hilfst du trotzdem.</p></div>
${formular({ typ: 'kontakt', tier: `${s.name} (${art[0]})`, knopf: 'Anfrage zu ' + esc(s.name) + ' senden', nachricht: 'Deine Nachricht an das Tierheim-Team' })}
</div></section>`}
${lichtDialog}`;
  schreibe(s.neu, geruest({ pfad: s.neu, title: titel(`${s.name}: ${privat ? 'Vermittlung von privat' : art[0] + ' sucht Zuhause'} | Waldtierheim Celle`), desc: kurz(`${s.name}${f.Rasse ? ', ' + f.Rasse : ''}${f.Geboren ? ', geboren ' + f.Geboren : ''}. ${nurText(h)}`, 155), body, hero: imgs[0], aktiv: '/im-waldtierheim-celle.html',
    leiste: privat ? null : [`<a href="tel:${F.telLink}">Anrufen ${F.tel}</a>`, `<a href="#anfrage">Kennenlernen anfragen</a>`], ld: [pfadLd(kr)] }));
}

/* ---------- Happy End ---------- */
const HAPPY_INTRO = 'Koffer gepackt und ausgezogen: Hier siehst du unsere Schützlinge, die ihre Familien und Körbchen gefunden haben.';
function archivListe(p, { h1, title, desc, liste, kr, art }) {
  const jahre = [...new Set(liste.map(s => (s.date || '').slice(0, 4) || 'Ohne Datum'))];
  const body = `<div class="huelle seitenkopf">${pfad(kr)}<h1>${h1}</h1><p class="statement">${HAPPY_INTRO} Danke an alle, die einem Tier ein Zuhause gegeben haben.</p></div>
<div class="huelle" style="padding-bottom:var(--abschnitt)">
${jahre.map(j => { const l = liste.filter(s => ((s.date || '').slice(0, 4) || 'Ohne Datum') === j); return `<h2 class="jahr">${j} <span class="klein neben" style="font-family:var(--text);letter-spacing:0">${mehrzahl(l.length, 'Steckbrief', 'Steckbriefe')}</span></h2>
<ul class="archiv">${l.map(s => `<li><a href="${s.neu}">${s.images[0] ? bild(s.images[0], { alt: `${s.name}, vermittelt`, klein: true }) : ''}<span>${esc(s.name)}</span></a></li>`).join('')}</ul>`; }).join('\n')}
</div>`;
  schreibe(p, geruest({ pfad: p, title, desc, body, aktiv: '/happy-end.html', ld: [pfadLd(kr)] }));
}
function archivSeite(s, gruppe, gruppenPfad, art) {
  const kr = [['Start', '/'], ['Happy End', '/happy-end.html'], [gruppe, gruppenPfad], [s.name, s.neu]], f = s.fields || {}, h = text(s), gruss = art === 'Gruß';
  const daten = [['Rasse', f.Rasse], ['Geboren', f.Geboren], ['Größe', f['Größe']], [gruss ? 'Gruß vom' : 'Steckbrief vom', datum(s.date)]].filter(x => x[1]);
  const body = `<div class="huelle" style="padding-top:clamp(1rem,3vw,2.5rem)">${pfad(kr)}
<article class="steck">
<div class="steck-bilder">${s.images[0] ? `<div class="steck-haupt">${bild(s.images[0], { alt: gruss ? `${s.name} im neuen Zuhause` : `${s.name}, ${art}, vermittelt durch das Waldtierheim Celle`, sizes: '(max-width: 60rem) 92vw, 46vw', lazy: false })}</div>` : ''}
${s.images.length > 1 ? `<div class="galerie" style="grid-template-columns:repeat(2,minmax(0,1fr))">${s.images.slice(1).map((k, i) => bild(k, { alt: `${s.name}, Foto ${i + 2}`, sizes: '(max-width: 60rem) 46vw, 23vw' })).join('')}</div>` : ''}</div>
<div><p class="vermittelt">${gruss ? 'Gruß vom neuen Zuhause' : 'Hat ein Zuhause gefunden'}</p>
<div class="steck-kopf"><h1>${esc(s.name)}</h1></div>
${daten.length ? `<dl class="daten">${daten.map(([a, b]) => `<dt>${a}</dt><dd>${esc(b)}</dd>`).join('')}</dl>` : ''}
${gruss ? '' : '<p class="klein neben">Der folgende Text ist der ursprüngliche Vermittlungs-Steckbrief. Kontaktangaben darin sind nicht mehr aktuell.</p>'}
<div class="lesen">${h}</div>
<p style="margin-top:2rem"><a class="knopf" href="/im-waldtierheim-celle.html">Tiere ansehen, die noch warten</a></p></div>
</article></div>`;
  schreibe(s.neu, geruest({ pfad: s.neu, title: titel(`${s.name}: ${gruss ? 'Gruß vom neuen Zuhause' : art + ' vermittelt'}${s.date ? ' ' + datum(s.date).slice(0, 6) + s.date.slice(2, 4) : ''} | Waldtierheim Celle`), desc: kurz(`${s.name}${gruss ? ' grüßt aus dem neuen Zuhause' : ' hat über das Waldtierheim Celle ein Zuhause gefunden'}. ${nurText(h)}`, 155), body, hero: s.images[0], aktiv: '/happy-end.html', ld: [pfadLd(kr)] }));
}

/* ---------- Artikel (Aktuelles, Feste) ---------- */
function artikel(s, gruppe, gruppenPfad, aktiv) {
  const kr = [['Start', '/'], ...(aktiv === '/verein.html' ? [['Verein', '/verein.html']] : []), [gruppe, gruppenPfad], [s.name, s.neu]], h = text(s);
  const body = `<div class="huelle seitenkopf">${pfad(kr)}<h1 style="font-size:clamp(1.9rem,5vw,4.25rem)">${esc(s.name)}</h1>${s.date ? `<p class="klein neben" style="margin-top:1rem">Veröffentlicht am <time datetime="${s.date}">${datum(s.date)}</time></p>` : ''}</div>
<div class="huelle" style="padding-bottom:var(--abschnitt)"><div class="lesen">${h}</div>
${s.images.length ? `<div class="galerie">${s.images.map((k, i) => `<button type="button" data-licht style="padding:0;border:0;background:none;cursor:zoom-in" aria-label="Foto ${i + 1} vergrößern">${bild(k, { alt: `${s.name}, Foto ${i + 1}`, sizes: '(max-width: 40rem) 92vw, 30vw', lazy: i > 1, extra: ` data-gross="/bilder/${k}-l.webp"` })}</button>`).join('')}</div>` : ''}
<p><a class="knopf knopf-still" href="${gruppenPfad}">Zurück zu ${esc(gruppe)}</a></p></div>${lichtDialog}`;
  schreibe(s.neu, geruest({ pfad: s.neu, title: titel(`${s.name} | Waldtierheim Celle`), desc: kurz(nurText(h) || s.name, 155), body, aktiv,
    ld: [pfadLd(kr), { '@type': 'Article', headline: s.name, ...(s.date ? { datePublished: s.date } : {}), author: { '@id': SITE + '/#tierheim' }, publisher: { '@id': SITE + '/#tierheim' }, mainEntityOfPage: SITE + s.neu }] }));
}
function einfach(p, { h1, title, desc, intro = '', inhalt, kr, aktiv, noindex = false, index = true, leiste }) {
  const body = `<div class="huelle seitenkopf">${pfad(kr || [])}<h1>${h1}</h1>${intro ? `<p class="statement">${intro}</p>` : ''}</div>
<div class="huelle" style="padding-bottom:var(--abschnitt)">${inhalt}</div>`;
  schreibe(p, geruest({ pfad: p, title, desc, body, aktiv, noindex, leiste, ld: kr && !noindex ? [pfadLd(kr)] : [] }), index);
}

/* ---------- Bauen ---------- */
start();
const T = '/im-waldtierheim-celle';
tierliste(T + '.html', { h1: 'Tiere im Waldtierheim Celle', title: 'Tiere suchen ein Zuhause | Waldtierheim Celle', desc: `Alle ${heimtiere.length} Steckbriefe aus dem Waldtierheim Celle: Hunde und Katzen, die ein Zuhause suchen. Mit Fotos, Alter und Beschreibung.`, intro: `${tiere.hunde.length} Hunde-Steckbriefe und ${tiere.katzen.length} Katzen-Steckbriefe. Manche Schilder stehen für Geschwister oder eine kleine Gruppe.`, liste: heimtiere, kr: [['Start', '/'], ['Tiere', T + '.html']] });
tierliste(T + '/hunde.html', { h1: 'Hunde im Waldtierheim Celle', title: 'Hunde aus dem Tierheim Celle | Waldtierheim', desc: 'Hunde aus dem Waldtierheim Celle suchen ein Körbchen: Steckbriefe mit Fotos, Rasse, Alter und ehrlicher Beschreibung. Kennenlernen in den Öffnungszeiten.', intro: 'Körbchen gesucht: Diese Hunde warten im Waldtierheim auf Menschen, die zu ihnen passen.', liste: tiere.hunde, kr: [['Start', '/'], ['Tiere', T + '.html'], ['Hunde', T + '/hunde.html']] });
tierliste(T + '/katzen.html', { h1: 'Katzen im Waldtierheim Celle', title: 'Katzen aus dem Tierheim Celle | Waldtierheim', desc: 'Katzen und Katzenkinder aus dem Waldtierheim Celle suchen ein Zuhause. Steckbriefe mit Fotos und Beschreibung. Auch Hofplätze für scheue Katzen gesucht.', intro: 'Zuhause gesucht: Katzen, Kater und Katzenkinder aus unserem Katzenhaus und aus Pflegestellen.', liste: tiere.katzen, extra: wilde, kr: [['Start', '/'], ['Tiere', T + '.html'], ['Katzen', T + '/katzen.html']] });
tierliste(T + '/kleintiere.html', { h1: 'Kleintiere im Waldtierheim Celle', title: 'Kleintiere aus dem Tierheim Celle | Waldtierheim', desc: 'Kleintiere im Waldtierheim Celle: Zurzeit warten keine Kleintiere auf Vermittlung. Frag gern telefonisch nach unter 05141 32900.', intro: 'Kaninchen, Meerschweinchen und andere Kleintiere finden über uns ebenfalls ein Zuhause.', liste: [], sort: false, leer: `<p><strong>Zurzeit warten keine Kleintiere bei uns.</strong> Das kann sich schnell ändern. Frag gern nach: <a href="tel:${F.telLink}">Telefon ${F.tel}</a>.</p><p>Bis dahin: <a href="/happy-end/kleintiere-vermittelt.html">Kleintiere, die schon vermittelt sind</a>.</p>`, kr: [['Start', '/'], ['Tiere', T + '.html'], ['Kleintiere', T + '/kleintiere.html']] });
tierliste(T + '/vermittlungshilfe-privat.html', { h1: 'Vermittlungshilfe von privat', title: 'Vermittlungshilfe privat | Waldtierheim Celle', desc: 'Tiervermittlung von privat zu privat in Celle und Umgebung. Die Tiere leben nicht im Waldtierheim, Kontakt direkt über die Halter. Anzeigen etwa sechs Wochen aktiv.', intro: 'Diese Tiere leben nicht im Waldtierheim. Die Anzeigen bleiben etwa sechs Wochen aktiv. Bei Fragen wende dich bitte direkt an die Halter.', liste: tiere['vermittlungshilfe-privat'], sort: false, extra: `<div class="hinweis"><p><strong>Du suchst selbst ein neues Zuhause für dein Tier?</strong> Schreib uns über das <a href="/kontakt.html">Kontaktformular</a> oder ruf an: <a href="tel:${F.telLink}">${F.tel}</a>.</p></div>`, kr: [['Start', '/'], ['Tiere', T + '.html'], ['Vermittlungshilfe privat', T + '/vermittlungshilfe-privat.html']] });
[...heimtiere, ...tiere['vermittlungshilfe-privat']].forEach(steckbrief);

// Happy End
const H = '/happy-end';
{
  const kr = [['Start', '/'], ['Happy End', H + '.html']];
  const teil = (t, u, l, n) => `<section style="margin-bottom:clamp(3rem,6vw,5rem)"><div class="kopfzeile"><h2>${t}</h2><p><a class="knopf knopf-still" href="${u}">Alle ${n} ansehen</a></p></div><ul class="archiv">${l.slice(0, 8).map(s => `<li><a href="${s.neu}">${s.images[0] ? bild(s.images[0], { alt: `${s.name}`, klein: true }) : ''}<span>${esc(s.name)}</span></a></li>`).join('')}</ul></section>`;
  einfach(H + '.html', { h1: 'Happy End', title: 'Happy End: vermittelte Tiere | Waldtierheim Celle', desc: `${happyZahl} dokumentierte Vermittlungen und ${gruesse.length} Grüße vom neuen Zuhause: Hunde, Katzen und Kleintiere aus dem Waldtierheim Celle, die ihre Familie gefunden haben.`, intro: HAPPY_INTRO + ' Wir sind dankbar, dass diese Tiere wieder ein Heim haben und als Familienmitglied geliebt werden.', kr, aktiv: H + '.html',
    inhalt: teil('Grüße vom neuen Zuhause', H + '/gruesse-vom-neuen-zuhause.html', gruesse, gruesse.length) + teil('Hunde vermittelt', H + '/hunde-vermittelt.html', vermHunde, vermHunde.length) + teil('Katzen vermittelt', H + '/katzen-vermittelt.html', vermKatzen, vermKatzen.length) + teil('Kleintiere vermittelt', H + '/kleintiere-vermittelt.html', vermKlein, vermKlein.length) });
  archivListe(H + '/hunde-vermittelt.html', { h1: 'Vermittelte Hunde', title: 'Vermittelte Hunde | Waldtierheim Celle', desc: `${vermHunde.length} Hunde aus dem Waldtierheim Celle, die ein Zuhause gefunden haben. Archiv der Vermittlungs-Steckbriefe nach Jahren.`, liste: vermHunde, kr: [...kr, ['Hunde vermittelt', H + '/hunde-vermittelt.html']] });
  archivListe(H + '/katzen-vermittelt.html', { h1: 'Vermittelte Katzen', title: 'Vermittelte Katzen | Waldtierheim Celle', desc: `${vermKatzen.length} Katzen aus dem Waldtierheim Celle, die ein Zuhause gefunden haben. Archiv der Vermittlungs-Steckbriefe nach Jahren.`, liste: vermKatzen, kr: [...kr, ['Katzen vermittelt', H + '/katzen-vermittelt.html']] });
  archivListe(H + '/kleintiere-vermittelt.html', { h1: 'Vermittelte Kleintiere', title: 'Vermittelte Kleintiere | Waldtierheim Celle', desc: `${vermKlein.length} Kleintiere aus dem Waldtierheim Celle, die ein Zuhause gefunden haben. Archiv der Vermittlungs-Steckbriefe.`, liste: vermKlein, kr: [...kr, ['Kleintiere vermittelt', H + '/kleintiere-vermittelt.html']] });
  vermHunde.forEach(s => archivSeite(s, 'Hunde vermittelt', H + '/hunde-vermittelt.html', 'Hund'));
  vermKatzen.forEach(s => archivSeite(s, 'Katzen vermittelt', H + '/katzen-vermittelt.html', 'Katze'));
  vermKlein.forEach(s => archivSeite(s, 'Kleintiere vermittelt', H + '/kleintiere-vermittelt.html', 'Kleintier'));
  const G = H + '/gruesse-vom-neuen-zuhause';
  einfach(G + '.html', { h1: 'Grüße vom neuen Zuhause', title: 'Grüße vom neuen Zuhause | Waldtierheim Celle', desc: `${gruesse.length} Briefe von Menschen, die ein Tier aus dem Waldtierheim Celle aufgenommen haben. So leben unsere ehemaligen Schützlinge heute.`, intro: 'Halterinnen und Halter erzählen, wie sich unsere ehemaligen Bewohner eingelebt haben. Ohne diese Für-immer-Zuhause wäre unsere Arbeit nicht möglich.', kr: [...kr, ['Grüße', G + '.html']], aktiv: H + '.html',
    inhalt: `<div class="hinweis"><p><strong>Dein Tier ist von uns?</strong> Zeig, wie es heute lebt. <a href="${G}/dein-glueckliches-fuerimmer-zuhause.html">So schickst du uns deinen Gruß</a></p></div>
<ul class="zeilen">${gruesse.map(s => `<li><a class="zeile" href="${s.neu}"><time datetime="${s.date}">${datum(s.date)}</time><h3>${esc(s.name)}</h3><p>${esc(kurz(text(s), 150))}</p></a></li>`).join('')}</ul>` });
  gruesse.forEach(s => archivSeite(s, 'Grüße', G + '.html', 'Gruß'));
  einfach(G + '/dein-glueckliches-fuerimmer-zuhause.html', { h1: 'Schick uns deinen Gruß', title: 'Gruß vom neuen Zuhause einsenden | Waldtierheim Celle', desc: 'Du hast ein Tier aus dem Waldtierheim Celle aufgenommen? Schick uns ein paar Zeilen und Fotos per E-Mail. Wir veröffentlichen sie kostenfrei.', intro: 'Du hast ein Tier von uns aufgenommen? Wir freuen uns über ein paar Zeilen und Fotos aus eurem Alltag.', kr: [...kr, ['Grüße', G + '.html'], ['Gruß einsenden', G + '/dein-glueckliches-fuerimmer-zuhause.html']], aktiv: H + '.html',
    inhalt: `<div class="lesen"><p>Schreib uns per E-Mail, wie sich dein Schützling eingelebt hat, und hänge zwei oder drei Fotos an. Die Veröffentlichung in der Rubrik „Grüße vom neuen Zuhause“ ist kostenfrei.</p>
<p><a class="knopf" href="mailto:${F.mail}?subject=Gru%C3%9F%20vom%20neuen%20Zuhause">Gruß per E-Mail an ${F.mail} senden</a></p>
<h2>Gut zu wissen</h2>
<p>Mit dem Einsenden erlaubst du uns, deinen Text und deine Bilder hier auf der Website, auf unserer Facebook-Seite und auf Werbemitteln des Vereins zu verwenden. Du versicherst, dass du die Fotos selbst aufgenommen hast und keine Rechte anderer verletzt werden. Wir sind ein privater Tierschutzverein und brauchen jeden Cent für die Tiere.</p>
<p>Wenn du deinen Gruß später wieder entfernen lassen möchtest, genügt eine E-Mail an uns.</p></div>` });
}

// Aktuelles
einfach('/aktuelles.html', { h1: 'Aktuelles aus dem Waldtierheim', title: 'Aktuelles | Waldtierheim Celle', desc: 'Meldungen aus dem Waldtierheim Celle: Tag der offenen Tür, Spendenaufrufe, Mitgliederversammlungen und Berichte aus dem Tierschutz in Celle.', kr: [['Start', '/'], ['Aktuelles', '/aktuelles.html']], aktiv: '/aktuelles.html',
  inhalt: `<ul class="zeilen">${news.map(n => `<li><a class="zeile" href="${n.neu}"><time datetime="${n.date}">${datum(n.date)}</time><h3>${esc(n.name)}</h3><p>${esc(kurz(text(n), 170))}</p></a></li>`).join('')}</ul>` });
news.forEach(n => artikel(n, 'Aktuelles', '/aktuelles.html', '/aktuelles.html'));

// Verein
{
  const V = P('/verein.html'), kr = [['Start', '/'], ['Verein', '/verein.html']];
  einfach('/verein.html', { h1: 'Verein aktiver Tierfreunde e.V.', title: 'Tierschutzverein in Celle | Verein aktiver Tierfreunde', desc: 'Der Verein aktiver Tierfreunde e.V. wurde 1992 in Celle gegründet und betreibt seit 2003 das Waldtierheim in Altencelle. Geschichte, Vorstand, Satzung.', intro: 'Die Verwirklichung des Tierschutzgedankens durch die aktive Hilfe für Tiere: Mit diesem Grundgedanken wurde der Verein am 23. Januar 1992 in Celle gegründet.', kr, aktiv: '/verein.html',
    inhalt: `<div class="verein"><div class="lesen">
<p>Ging es zu Beginn vor allem um die Kastration von frei lebenden Katzen, kam sehr schnell auch die Pflege und Vermittlung von Hunden, Katzen und Kleintieren hinzu.</p>
<p>Da es zum Zeitpunkt der Vereinsgründung noch keine feste Bleibe gab, stellte sich ein wahres Nomadenleben ein. Die überlassenen Tiere wurden ursprünglich von aktiven Vereinsmitgliedern privat aufgenommen oder in angemieteten Hundezwingern in Pensionen untergebracht. Eine schwierige Zeit, wie sich einige Mitglieder der ersten Stunde noch erinnern.</p>
<h2>Nach zehn Jahren das eigene Heim</h2>
<p>Zehn Jahre später war es endlich so weit. Mit dem Angebot eines 9 Hektar großen Waldgrundstücks mit Baumbestand und einem kleinen Wohnhaus am Rande von Altencelle stand dem eigenen Domizil für Hund und Katz nichts mehr im Wege. Dank der fleißigen Unterstützung von Mitgliedern, freiwilligen Helfern und Spendern konnten das Katzenhaus und die Hundezwinger errichtet und bald eingeweiht werden.</p>
<p>Seit Bezug und Eröffnung des Waldtierheims 2003 setzt sich der Verein rund um die Uhr für tierische Notfälle ein, in Celle, in der Umgebung und auch weit darüber hinaus. Zahlreiche Hunde, Katzen, Heim- und Wildtiere konnten medizinisch versorgt, betreut und artgerecht vermittelt werden.</p>
<h2>Wie wir uns finanzieren</h2>
<p>Der Verein aktiver Tierfreunde e.V. ist beim Amtsgericht Celle eingetragen und als besonders förderungswürdig anerkannt sowie Mitglied im Verband Niedersächsischer Tierschutzvereine. Unser Engagement für den Tierschutz finanziert sich über Mitgliedsbeiträge und <a href="/deine-hilfe.html">Spenden</a>.</p>
<p><a class="knopf" href="/deine-hilfe.html">So kannst du helfen</a></p>
</div>
<div><figure>${bild(V.images[0], { alt: 'Hundezwinger aus Holz unter Bäumen im Waldtierheim Celle', sizes: '(max-width: 60rem) 92vw, 42vw', lazy: false })}<figcaption>Hundezwinger im Waldtierheim Celle</figcaption></figure>
<ul class="zeilen" style="margin-top:2rem"><li><a class="zeile" href="/verein/vorstand.html"><span class="neben">Wer</span><h3>Vorstand</h3></a></li><li><a class="zeile" href="/verein/satzung.html"><span class="neben">Regeln</span><h3>Satzung</h3></a></li><li><a class="zeile" href="/verein/aktionen-und-feste.html"><span class="neben">Rückblick</span><h3>Aktionen und Feste</h3></a></li></ul></div></div>` });
  const vs = P('/verein/vorstand.html').images;
  const leute = [['Gabriele Schwarz', 'Vorsitzende', 'vorstand@tierfreunde-celle.de', vs[0]], ['Dirk Kamann', 'stellvertretender Vorsitzender', 'info@tierfreunde-celle.de', vs[1]], ['Gundula Meißner', 'stellvertretende Vorsitzende', 'info@tierfreunde-celle.de', null], ['Anja Zerbe', 'Kassenwartin', '', vs[2]], ['Mirja Hardy', 'Schriftführerin', 'presse@tierfreunde-celle.de', null], ['Silke Reck-Kuchemüller', 'Beisitzerin', '', null], ['Prof. Dr. Stefan Schwarz', 'Beisitzer', '', null]];
  einfach('/verein/vorstand.html', { h1: 'Vorstand', title: 'Vorstand | Verein aktiver Tierfreunde e.V. Celle', desc: 'Der Vorstand des Vereins aktiver Tierfreunde e.V. in Celle: Vorsitzende Gabriele Schwarz, Stellvertretung, Kassenwartin, Schriftführerin und Beisitzer.', intro: 'Diese Menschen führen den Verein ehrenamtlich.', kr: [...kr, ['Vorstand', '/verein/vorstand.html']], aktiv: '/verein.html',
    inhalt: `<ul class="personen">${leute.map(([n, r, m, k]) => `<li>${k ? bild(k, { alt: `${n}, ${r}`, klein: true }) : ''}<div><h2>${n}</h2><p>${r}</p>${m ? `<p><a href="mailto:${m}">${m}</a></p>` : ''}</div></li>`).join('')}</ul>` });
  einfach('/verein/satzung.html', { h1: 'Satzung', title: 'Satzung | Verein aktiver Tierfreunde e.V. Celle', desc: 'Satzung des Vereins aktiver Tierfreunde e.V. – Tierschutz – mit Sitz in Celle: Zweck, Mitgliedschaft, Organe und Gemeinnützigkeit.', kr: [...kr, ['Satzung', '/verein/satzung.html']], aktiv: '/verein.html',
    inhalt: `<div class="lesen">${text(P('/verein/satzung.html')).replace(/^\s*<h3>\s*Satzung\s*<\/h3>/, '').replace(/<h3>/g, '<h2>').replace(/<\/h3>/g, '</h2>')}</div>` });
  einfach('/verein/aktionen-und-feste.html', { h1: 'Aktionen und Feste', title: 'Aktionen und Feste | Waldtierheim Celle', desc: 'Rückblick auf Tage der offenen Tür, Vereinsfeste und Arbeitseinsätze im Waldtierheim Celle, mit Fotos.', kr: [...kr, ['Aktionen und Feste', '/verein/aktionen-und-feste.html']], aktiv: '/verein.html',
    inhalt: `<ul class="zeilen">${feste.map(n => `<li><a class="zeile" href="${n.neu}"><time datetime="${n.date}">${datum(n.date)}</time><h3>${esc(n.name)}</h3><p>${esc(kurz(text(n), 170))}</p></a></li>`).join('')}</ul>` });
  feste.forEach(n => artikel(n, 'Aktionen und Feste', '/verein/aktionen-und-feste.html', '/verein.html'));
}

// Hilfe
{
  const kr = [['Start', '/'], ['Helfen', '/deine-hilfe.html']], linka = P('/deine-hilfe.html').images[0];
  einfach('/deine-hilfe.html', { h1: 'Deine Hilfe zählt', title: 'Spenden und helfen | Waldtierheim Celle', desc: 'So unterstützt du das Waldtierheim Celle: Spende, Patenschaft, Mitgliedschaft ab 20 € im Jahr oder als Gassi-Geher. Bankverbindung und Patenschaftsvertrag.', intro: 'Unser Verein ist ein privater Tierschutzverein, der sich an 365 Tagen im Jahr um Hunde, Katzen und Kleintiere kümmert. Manchmal kreuzt sogar ein Wildtier unsere Wege.', kr, aktiv: '/deine-hilfe.html',
    inhalt: `<div class="verein"><div class="lesen">
<p>Um diese Arbeit leisten zu können, sind wir auf deine Unterstützung angewiesen. Danke an alle Mitglieder, Spender, helfenden Hände und aktiven Tierfreunde.</p>
<h2 id="gassi">Gassi gehen</h2>
<p>Melde dich als Gassi-Geher für unsere Hunde und erlebe tolle Spaziergänge. Interessierte melden sich bitte während der Öffnungszeiten direkt im Waldtierheim.</p>
<h2 id="mitgliedschaft">Werde Mitglied</h2>
<p>Mit einer Mitgliedschaft wirst du Teil unserer Familie und kannst aktiv an der Gestaltung des Vereins mitwirken. Den Aufnahmeantrag bekommst du bei uns im Tierheim. Die Höhe des Mitgliedsbeitrages bestimmst du selbst (mindestens 20 € im Jahr).</p>
<p>Dein Mitgliedsbeitrag wird für die Versorgung der Tiere eingesetzt, zum Beispiel für Arztkosten und Futter, und hilft uns beim Unterhalt des Waldtierheims. Außerdem erhältst du die Einladung zu unserer Mitgliederversammlung, die einmal jährlich im Frühjahr stattfindet.</p>
<h2 id="patenschaft">Übernimm eine Patenschaft</h2>
<p>Du hast keine Möglichkeit, ein Tier bei dir aufzunehmen, und dennoch ist da diese eine kleine Seele, die dein Herz berührt? Übernimm eine Patenschaft und unterstütze speziell dieses eine Tier: mit Sachspenden, Futter oder finanziell mit einer monatlichen tierbezogenen Spende. Bis zur Vermittlung kannst du dein Patentier während unserer Öffnungszeiten jederzeit besuchen.</p>
<p><a class="knopf knopf-still" href="/dokumente/patenschaftsvertrag.pdf">Patenschaftsvertrag als PDF laden (155 KB)</a></p>
<h2 id="spenden">Spende</h2>
<p>Deine Spende kommt direkt den Schützlingen unseres Waldtierheims zugute. Du unterstützt uns bei Arztkosten (medizinische Versorgung bei Krankheit, Kastration), bei der Versorgung der Tiere (zum Beispiel Futterkosten) und bei der Instandhaltung der Unterbringungen (Hundezwinger, Katzenhaus).</p>
<h3>Per Überweisung</h3>
${kontoBlock}
<h3>Online über betterplace.org</h3>
<p>Du wählst den Betrag und ob deine Spende einmalig, monatlich, viertel-, halb- oder jährlich erfolgen soll. Die Spendenbescheinigung stellt dir unser Partner betterplace.org zu Beginn des folgenden Jahres zu.</p>
<p><a class="knopf" href="${F.spende}" rel="noopener">Bei betterplace.org spenden</a></p>
<p class="klein neben">Der Link öffnet die Website von betterplace.org. Dort gelten deren Datenschutzbestimmungen.</p>
<p><a href="/deine-hilfe/danke-an-die-helfer.html">Danke an die Helfer: Menschen und Firmen, die uns unterstützt haben</a></p>
</div>
<figure>${bild(linka, { alt: 'Dackelmischling Linka auf dem Arm, ehemalige Bewohnerin des Waldtierheims', sizes: '(max-width: 60rem) 92vw, 42vw', lazy: false })}<figcaption>Unsere ehemalige Bewohnerin Linka konnte schnell ein tolles Zuhause finden.</figcaption></figure></div>` });
  const D = P('/deine-hilfe/danke-an-die-helfer.html');
  einfach('/deine-hilfe/danke-an-die-helfer.html', { h1: 'Danke an die Helfer', title: 'Danke an die Helfer | Waldtierheim Celle', desc: 'Menschen, Schulen und Firmen aus Celle und Umgebung, die das Waldtierheim mit Spendenaktionen unterstützt haben. Danke.', intro: 'Helfende Menschen und Organisationen, die sich für unsere Schützlinge starkgemacht haben.', kr: [...kr, ['Danke an die Helfer', '/deine-hilfe/danke-an-die-helfer.html']], aktiv: '/deine-hilfe.html',
    inhalt: `<div class="lesen">${text(D).replace(/^\s*<h3>.*?<\/h3>/, '').replace(/<h3>/g, '<h2>').replace(/<\/h3>/g, '</h2>')}</div>
<div class="galerie">${(D.items || []).filter(i => i[1]).map(i => `<figure>${bild(i[1], { alt: i[2] || 'Spendenübergabe für das Waldtierheim Celle', sizes: '(max-width: 40rem) 92vw, 30vw' })}<figcaption>${esc(i[2])}</figcaption></figure>`).join('')}</div>` });
}

// Kontakt
einfach('/kontakt.html', { h1: 'Kontakt und Besuch', title: 'Kontakt und Öffnungszeiten | Waldtierheim Celle', desc: 'Waldtierheim Celle, Im Sande 3, 29227 Celle (Zufahrt Richtung Osterloh). Telefon 05141 32900. Öffnungszeiten, Anfahrt und Kontaktformular.', intro: 'Im Sande 3, 29227 Celle. Die Zufahrt führt Richtung Osterloh.', kr: [['Start', '/'], ['Kontakt', '/kontakt.html']], aktiv: '/kontakt.html',
  inhalt: `<div class="verein" style="margin-bottom:var(--abschnitt)">
<div><p class="status" data-status style="margin:0 0 1.5rem">Öffnungszeiten</p>
<div class="dunkel" style="padding:1.5rem 1.5rem 1rem">${wochenTabelle()}</div></div>
<div class="anfahrt"><figure>${bild(P('/kontakt.html').images[0], { alt: 'Einfahrt mit Tor zum Waldtierheim Celle zwischen Kiefern', sizes: '(max-width: 60rem) 92vw, 40vw', lazy: false })}<figcaption>Hier geht es zu uns: der Eingang des Waldtierheims.</figcaption></figure>
<address>${F.name}<br>${F.str}, ${F.plz} ${F.ort}</address>
<a class="tel" href="tel:${F.telLink}">${F.tel}</a>
<p><a href="mailto:${F.mail}">${F.mail}</a></p>
<p><a class="knopf knopf-still" href="${F.route}" rel="noopener">Route in Google Maps öffnen</a></p></div></div>
<section class="anfrage" id="anfrage" style="padding:clamp(1.5rem,5vw,4rem)" aria-labelledby="h-anfrage"><div class="anfrage-raster">
<div><h2 id="h-anfrage">Schreib uns</h2><p style="margin-top:1.5rem">Fragen zu einem Tier, zur Patenschaft oder zur Vermittlungshilfe? Wir antworten per E-Mail oder rufen zurück.</p></div>
${formular({ typ: 'kontakt', knopf: 'Nachricht an das Tierheim senden' })}</div></section>` });

// Rechtliches
einfach('/impressum.html', { h1: 'Impressum', title: 'Impressum | Waldtierheim Celle', desc: 'Impressum des Vereins aktiver Tierfreunde e.V., Im Sande 3, 29227 Celle. Angaben nach § 5 DDG.', kr: [['Start', '/'], ['Impressum', '/impressum.html']],
  inhalt: `<div class="lesen">
<h2>Angaben gemäß § 5 DDG</h2>
<p>${F.name}<br>${F.str}<br>${F.plz} ${F.ort}</p>
<h2>Vertreten durch den Vorstand</h2>
<p>Gabriele Schwarz (Vorsitzende)<br>Dirk Kamann (stellvertretender Vorsitzender)<br>Gundula Meißner (stellvertretende Vorsitzende)<br>Anja Zerbe (Kassenwartin)</p>
<h2>Kontakt</h2>
<p>Telefon: <a href="tel:${F.telLink}">${F.tel}</a><br>E-Mail: <a href="mailto:${F.mail}">${F.mail}</a></p>
<h2>Registereintrag</h2>
<p>Eingetragen im Vereinsregister.<br>Registergericht: Amtsgericht Celle<br>Registernummer: VR 100559</p>
<h2>Redaktionell verantwortlich</h2>
<p>${F.name}<br>${F.str}<br>${F.plz} ${F.ort}</p>
<h2>Verbraucherstreitbeilegung</h2>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
<h2>Bildnachweis</h2>
<p>Fotos: Verein aktiver Tierfreunde e.V., Mitglieder des Vereins und Einsendungen von Halterinnen und Haltern. Bei einzelnen Beiträgen ist die Quelle im Text genannt.</p>
<h2>Haftung für Inhalte</h2>
<p>Als Diensteanbieter sind wir für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Wir sind jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Bei Bekanntwerden von Rechtsverletzungen entfernen wir diese Inhalte umgehend.</p>
<h2>Haftung für Links</h2>
<p>Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter verantwortlich. Bei Bekanntwerden von Rechtsverletzungen entfernen wir derartige Links umgehend.</p>
<h2>Urheberrecht</h2>
<p>Die durch uns erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechts bedürfen der schriftlichen Zustimmung des jeweiligen Autors oder Erstellers.</p>
</div>` });
einfach('/datenschutz.html', { h1: 'Datenschutz', title: 'Datenschutzerklärung | Waldtierheim Celle', desc: 'Datenschutzerklärung des Vereins aktiver Tierfreunde e.V.: Kontaktformular, Server-Logs, Hosting, Statistik und deine Rechte.', kr: [['Start', '/'], ['Datenschutz', '/datenschutz.html']],
  inhalt: `<div class="lesen">
<h2>Verantwortlicher</h2>
<p>${F.name}<br>${F.str}, ${F.plz} ${F.ort}<br>Telefon: <a href="tel:${F.telLink}">${F.tel}</a><br>E-Mail: <a href="mailto:${F.mail}">${F.mail}</a></p>
<h2>Hosting</h2>
<p>Diese Website wird bei Markentrix gehostet. Beim Aufruf verarbeitet der Server technisch notwendige Daten, damit die Seite ausgeliefert werden kann. Mit dem Hosting-Dienstleister besteht ein Vertrag über Auftragsverarbeitung. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an einem sicheren und zuverlässigen Betrieb).</p>
<h2>Server-Logs</h2>
<p>Bei jedem Aufruf werden automatisch Informationen gespeichert, die dein Browser übermittelt: IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browsertyp und Betriebssystem, zuvor besuchte Seite. Diese Daten dienen der Sicherheit und Fehlersuche und werden nicht mit anderen Daten zusammengeführt. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO.</p>
<h2>Kontaktformular und Anfragen zu Tieren</h2>
<p>Wenn du uns über ein Formular schreibst, verarbeiten wir deinen Namen, deine E-Mail-Adresse, optional deine Telefonnummer, deine Nachricht und gegebenenfalls das Tier, zu dem du anfragst. Wir nutzen diese Angaben nur, um deine Anfrage zu beantworten. Du erhältst eine automatische Eingangsbestätigung per E-Mail. Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO) sowie Art. 6 Abs. 1 lit. b DSGVO, wenn deine Anfrage auf eine Vermittlung zielt. Du kannst deine Einwilligung jederzeit per E-Mail an ${F.mail} widerrufen. Wir löschen die Daten, sobald sie für die Bearbeitung nicht mehr erforderlich sind und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>Kontakt per E-Mail oder Telefon</h2>
<p>Wenn du uns anrufst oder eine E-Mail schreibst, verarbeiten wir deine Angaben zur Bearbeitung deines Anliegens (Art. 6 Abs. 1 lit. b oder lit. f DSGVO).</p>
<h2>Statistik</h2>
<p>Wir zählen Seitenaufrufe und wenige Ereignisse (zum Beispiel eine gesendete Anfrage) ohne Cookies und ohne dass einzelne Besucher wiedererkannt werden. Soweit für weitere Auswertungen eine Einwilligung nötig ist, fragen wir sie über die Statistik-Einstellung ab, die du im Fuß der Seite jederzeit ändern kannst.</p>
<h2>Schriften und Medien</h2>
<p>Schriften, Bilder und Skripte liegen auf unserem eigenen Server. Beim Laden der Seite werden keine Inhalte von Drittanbietern abgerufen.</p>
<h2>Links zu anderen Websites</h2>
<p>Wir verlinken auf betterplace.org (Online-Spenden), Facebook, Google Maps (Routenplanung) und den Verband Niedersächsischer Tierschutzvereine. Erst wenn du einen dieser Links anklickst, werden Daten an den jeweiligen Anbieter übertragen. Dort gelten dessen Datenschutzbestimmungen.</p>
<h2>Fotos und Grüße vom neuen Zuhause</h2>
<p>Texte und Fotos, die uns Halterinnen und Halter für die Rubrik „Grüße vom neuen Zuhause“ senden, veröffentlichen wir auf Grundlage ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO). Die Einwilligung kann jederzeit per E-Mail widerrufen werden, wir entfernen den Beitrag dann.</p>
<h2>Deine Rechte</h2>
<p>Du hast das Recht auf Auskunft über deine gespeicherten Daten (Art. 15 DSGVO), auf Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch gegen die Verarbeitung (Art. 21). Eine erteilte Einwilligung kannst du jederzeit mit Wirkung für die Zukunft widerrufen. Außerdem kannst du dich bei einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
</div>` });
einfach('/danke.html', { h1: 'Danke, deine Nachricht ist da', title: 'Nachricht erhalten | Waldtierheim Celle', desc: 'Deine Nachricht ist beim Waldtierheim Celle angekommen.', noindex: true, index: false,
  inhalt: `<div class="lesen"><p class="statement" style="margin-bottom:1.5rem">Wir haben deine Anfrage erhalten und melden uns per E-Mail oder Telefon. Eine Eingangsbestätigung ist auf dem Weg in dein Postfach.</p>
<p data-ref-zeile hidden>Deine Vorgangsnummer: <strong data-ref></strong></p>
<p>Wenn es eilt, erreichst du uns in den Öffnungszeiten unter <a href="tel:${F.telLink}">${F.tel}</a>.</p>
<p><a class="knopf" href="/im-waldtierheim-celle.html">Weitere Tiere ansehen</a></p></div>` });
einfach('/404.html', { h1: 'Diese Seite ist ausgezogen', title: 'Seite nicht gefunden | Waldtierheim Celle', desc: 'Diese Seite gibt es nicht mehr.', noindex: true, index: false,
  inhalt: `<div class="lesen"><p class="statement" style="margin-bottom:1.5rem">Vielleicht hat das Tier, das du suchst, schon ein Zuhause gefunden. Dann findest du es im Happy End.</p>
<p><a class="knopf" href="/im-waldtierheim-celle.html">Tiere ansehen, die noch warten</a></p>
<p><a href="/happy-end.html">Zum Happy End</a> oder <a href="/">zur Startseite</a>. Fragen beantworten wir unter <a href="tel:${F.telLink}">${F.tel}</a>.</p></div>` });

/* ---------- Sitemap, robots, llms, Manifest, Favicon ---------- */
const heute = new Date().toISOString().slice(0, 10);
fs.writeFileSync(path.join(ZIEL, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${raus.filter(r => r.index).map(r => `<url><loc>${SITE}${r.p === '/index.html' ? '/' : r.p}</loc><lastmod>${heute}</lastmod></url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(path.join(ZIEL, 'robots.txt'), `User-agent: *\nAllow: /\nDisallow: /danke.html\n\nSitemap: ${SITE}/sitemap.xml\n`);
fs.writeFileSync(path.join(ZIEL, 'llms.txt'), `# Waldtierheim Celle (Verein aktiver Tierfreunde e.V.)

> Privater Tierschutzverein in Celle, Niedersachsen. Gegründet am 23. Januar 1992. Betreibt seit 2003 das Waldtierheim auf einem 9 Hektar großen Waldgrundstück am Rand von Altencelle und vermittelt Hunde, Katzen und Kleintiere.

## Fakten
- Adresse: ${F.str}, ${F.plz} ${F.ort} (Zufahrt Richtung Osterloh)
- Telefon: ${F.tel}
- E-Mail: ${F.mail}
- Öffnungszeiten vormittags: Montag bis Freitag 8 bis 11 Uhr, Samstag und Sonntag 10 bis 11 Uhr
- Öffnungszeiten nachmittags: Montag, Mittwoch, Freitag und Sonntag 15 bis 17 Uhr
- Mitgliedschaft: Beitrag frei wählbar, mindestens 20 Euro im Jahr
- Spendenkonto: ${F.name} – Tierschutz, IBAN ${F.iban}, BIC ${F.bic}, ${F.bank}
- Mitglied im Verband Niedersächsischer Tierschutzvereine e.V.
- Aktuell ${tiere.hunde.length} Hunde-Steckbriefe und ${tiere.katzen.length} Katzen-Steckbriefe (Stand ${datum(heute)})

## Wichtige Seiten
- /im-waldtierheim-celle.html : alle Tiere, die ein Zuhause suchen
- /im-waldtierheim-celle/hunde.html : Hunde
- /im-waldtierheim-celle/katzen.html : Katzen
- /im-waldtierheim-celle/vermittlungshilfe-privat.html : Vermittlung von privat zu privat
- /deine-hilfe.html : Spenden, Patenschaft, Mitgliedschaft, Gassi gehen
- /kontakt.html : Öffnungszeiten, Anfahrt, Kontaktformular
- /verein.html : Geschichte und Finanzierung des Vereins
- /happy-end.html : ${happyZahl} dokumentierte Vermittlungen und ${gruesse.length} Grüße vom neuen Zuhause
- /aktuelles.html : Meldungen

## Häufige Fragen
${FAQ.map(([q, a]) => `- ${q} ${a}`).join('\n')}
`);
fs.writeFileSync(path.join(ZIEL, 'site.webmanifest'), JSON.stringify({ name: 'Waldtierheim Celle', short_name: 'Waldtierheim', lang: 'de', start_url: '/', display: 'browser', background_color: '#EADFC8', theme_color: '#EADFC8', icons: [{ src: '/favicon.svg', sizes: 'any', type: 'image/svg+xml' }] }));
fs.writeFileSync(path.join(ZIEL, 'favicon.svg'), `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#14104F"/><path fill="#9BD43A" d="M16 4l7 10h-4l6 9h-7v5h-4v-5H7l6-9H9z"/></svg>\n`);

/* ---------- Aufräumen, Weiterleitungen ---------- */
let weg = 0;
for (const f of fs.readdirSync(path.join(ZIEL, 'bilder'))) if (!benutzt.has(f.replace('.webp', ''))) { fs.unlinkSync(path.join(ZIEL, 'bilder', f)); weg++; }
weiter.push(['/kontakt/nachricht-erhalten.html', '/danke.html']);
fs.writeFileSync(path.resolve(HIER, '../WEITERLEITUNGEN.md'), `# Weiterleitungen (Relaunch tierfreunde-celle.de)

Alle übrigen ${seiten.length - weiter.length} Adressen der alten Website behalten ihren Pfad und brauchen keine Weiterleitung.
Die folgenden Adressen enthalten Umlaute oder entfallen. Bitte als 301 im Portal/Server einrichten.

| alt | neu |
|---|---|
${weiter.map(([a, n]) => `| ${a} | ${n} |`).join('\n')}

Hinweis: Listen-Seiten der alten Website mit Blätter-Parametern (z. B. \`?page_n37=2\`) zeigen jetzt alle Einträge auf einer Seite. Der Parameter wird ignoriert, eine Weiterleitung ist nicht nötig.
`);
console.log(`${raus.length} Seiten, ${benutzt.size} Bilddateien benutzt, ${weg} unbenutzte entfernt.`);
