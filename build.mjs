// Statischer Seitengenerator – erzeugt alle HTML-Seiten nach ./site
// Aufruf: node build.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { company as C, sectors, services, values, timeline, agrarmonitor, team, job, news, faqs, alts, showcase, facts } from './content/site.mjs';

const ROOT = dirname(fileURLToPath(import.meta.url));
const ART = process.env.ARTIFACT_OUT; // Vorschau-Variante: Links mit index.html, Startseite als Fragment
const OUT = ART || join(ROOT, 'site');
const json = (f) => JSON.parse(readFileSync(join(ROOT, 'content', f), 'utf8'));
const svcData = json('services.json');
const legal = json('legal.json');
const images = json('images.json');
const YEAR = new Date().getFullYear();
const SITE_URL = 'https://lu-linneweh.com/';

const esc = (s = '') => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const slugify = (s) => s.toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const altFor = (name) => alts[name] || alts[name.replace(/-\d+$/, '')] || 'Lohnunternehmen Linneweh im Einsatz';
const svc = (s) => ({ ...s, ...svcData[s.key], title: s.title || svcData[s.key].title, path: `leistungen/${s.sector}/${s.slug}/` });
const allSvc = services.map(svc);
const sectorOf = (id) => sectors.find((s) => s.id === id);
const svcOf = (id) => allSvc.filter((s) => s.sector === id);

// Weiche Trennstellen für lange Komposita in großen Überschriften
const SHY = [
  ['Dienstleistung', 'Dienst|leistung'], ['wirtschaftliche', 'wirtschaft|liche'], ['Forstwirtschaft', 'Forst|wirtschaft'], ['Landwirtschaft', 'Land|wirtschaft'],
  ['Flächenvorbereitung', 'Flächen|vor|bereitung'], ['Pflanzvorbereitung', 'Pflanz|vor|bereitung'], ['Bodenvorbereitung', 'Boden|vor|bereitung'], ['Ganzpflanzensilage', 'Ganz|pflanzen|silage'],
  ['Hackschnitzel', 'Hack|schnitzel'], ['Seitenränder', 'Seiten|ränder'], ['Baufeldräumung', 'Baufeld|räumung'], ['Pflanzenschutz', 'Pflanzen|schutz'], ['Pflanzenwachstum', 'Pflanzen|wachstum'],
  ['Winterdienst', 'Winter|dienst'], ['Kulturpflege', 'Kultur|pflege'], ['Wirtschaftsdünger', 'Wirtschafts|dünger'], ['Wegepflegemaschine', 'Wege|pflege|maschine'], ['Baggerarbeiten', 'Bagger|arbeiten'],
  ['Forstmulchen', 'Forst|mulchen'], ['Rückewagen', 'Rücke|wagen'], ['Technologie', 'Techno|logie'], ['Unternehmen', 'Unter|nehmen'], ['Familiengeführt', 'Familien|geführt'], ['Generationen', 'Genera|tionen'],
  ['Aushilfskraft', 'Aushilfs|kraft'], ['Verstärkung', 'Ver|stärkung'], ['Agrarmonitor', 'Agrar|monitor'], ['Zertifiziert', 'Zerti|fiziert'], ['Kartoffeln', 'Kar|toffeln'], ['Unterstützung', 'Unter|stützung'],
  ['Interessiert', 'Inte|res|siert'], ['Kundennah', 'Kunden|nah'], ['Leistungsübersicht', 'Leistungs|übersicht'], ['Abtransport', 'Ab|transport'], ['Reparaturservice', 'Reparatur|service'], ['Reifenservice', 'Reifen|service'],
  ['Hydraulikschlauchservice', 'Hydraulik|schlauch|service'], ['Ersatzteilservice', 'Ersatzteil|service'], ['Schweißarbeit', 'Schweiß|arbeit'], ['Hauptuntersuchung', 'Haupt|unter|suchung'], ['Baumaschinen', 'Bau|maschinen'],
  ['Geschichte', 'Ge|schichte'], ['Ansprechpartner', 'Ansprech|partner'], ['Forstraupe', 'Forst|raupe'], ['Forstfräsen', 'Forst|fräsen'], ['Datenschutz', 'Daten|schutz'], ['Anregungen', 'An|regungen'], ['Leidenschaft', 'Leiden|schaft'],
].map(([a, b]) => [new RegExp(a, 'g'), b.replaceAll('|', '\u00AD')]);
const shyText = (html) => html.replace(/>([^<]+)</g, (x) => SHY.reduce((t, [r, v]) => t.replace(r, v), x));

const ARROW = '<svg class="ico-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICONS = {
  near: '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="24" cy="26" r="12"/><circle cx="40" cy="38" r="12"/><path d="M6 58c2-8 9-12 18-12M58 58c-2-6-6-9-11-11"/></svg>',
  fast: '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 44a24 24 0 1 1 48 0"/><path d="M32 44l12-18"/><circle cx="32" cy="44" r="3"/><path d="M14 52h36"/></svg>',
  rings: '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="26"/><circle cx="32" cy="32" r="18"/><circle cx="32" cy="32" r="10"/><circle cx="32" cy="32" r="2.5"/></svg>',
  mail: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
  phone: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>',
  pin: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.800 7 11 7 11z"/><circle cx="12" cy="10" r="2.500"/></svg>',
  insta: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.500" y="3.500" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.200" cy="6.800" r=".8"/></svg>',
  fb: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 8.500V7c0-1 .500-1.500 1.500-1.500H17V2.500h-2.500C11.500 2.500 10 4.300 10 7v1.500H7.500V12H10v9.500h4V12h2.600l.4-3.500z"/></svg>',
};

function pic(name, { alt, sizes = '100vw', cls = '', eager = false, attrs = '' } = {}) {
  const m = images[name];
  if (!m) throw new Error('Bild fehlt: ' + name);
  const big = m.sizes.length > 1;
  const src = (w) => `{root}assets/img/${name}-${w}.webp`;
  const w1 = m.sizes[0];
  const srcset = big ? `${src(800)} ${w1}w, ${src(1600)} ${m.sizes[1]}w` : `${src(800)} ${w1}w`;
  return `<img${cls ? ` class="${cls}"` : ''} src="${src(800)}" srcset="${srcset}" sizes="${sizes}" width="${m.w}" height="${m.h}" alt="${esc(alt ?? altFor(name))}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async"${attrs ? ' ' + attrs : ''}>`;
}
const bigSrc = (name) => `{root}assets/img/${name}-${images[name].sizes.length > 1 ? 1600 : 800}.webp`;
const btn = (href, text, variant = 'wheat', extra = '') => `<a class="btn btn--${variant}" href="${href}"${extra}><span>${text}</span>${ARROW}</a>`;
const label = (t, tag = 'p', cls = '') => `<${tag} class="label ${cls}"><span class="label__dot"></span>${t}</${tag}>`;

/* ------------------------------------------------------------------ Layout */
const navLinks = [
  ['leistungen/', 'Leistungen'], ['unternehmen/', 'Unternehmen'], ['karriere/', 'Karriere'], ['news/', 'News'], ['faq/', 'FAQ'],
];

function header(path) {
  const cur = (p) => (path.startsWith(p) ? ' aria-current="page"' : '');
  return `
<header class="hdr" data-hdr>
  <a class="hdr__logo" href="{root}" aria-label="${C.name} – Startseite"><img src="{root}assets/img/logo-weiss.png" width="720" height="174" alt="${C.name}"></a>
  <nav class="hdr__nav" aria-label="Hauptnavigation">
    ${navLinks.map(([p, t]) => `<a href="{root}${p}"${cur(p)}>${t}</a>`).join('')}
  </nav>
  <a class="hdr__tel" href="${C.phoneHref}">${ICONS.phone}<span>${C.phone}</span></a>
  <a class="btn btn--wheat btn--sm hdr__cta" href="{root}kontakt/"><span>Kontakt</span>${ARROW}</a>
  <button class="hdr__burger" type="button" aria-expanded="false" aria-controls="menu" data-menu-toggle><span class="hdr__burger-txt">Menü</span><span class="hdr__burger-ico" aria-hidden="true"><i></i><i></i></span></button>
</header>
<div class="menu" id="menu" aria-hidden="true" inert>
  <div class="menu__bg" aria-hidden="true"></div>
  <div class="menu__inner wrap">
    <nav class="menu__main" aria-label="Menü">
      <a href="{root}" data-img="grasernte"><small>00</small>Start</a>
      <a href="{root}leistungen/" data-img="haeckseln-1"><small>01</small>Leistungen</a>
      <a href="{root}unternehmen/" data-img="gruenland-1"><small>02</small>Unternehmen</a>
      <a href="{root}karriere/" data-img="maehen"><small>03</small>Karriere</a>
      <a href="{root}news/" data-img="forstmulcher-2"><small>04</small>News</a>
      <a href="{root}faq/" data-img="agrarmonitor-tablet"><small>05</small>FAQ</a>
      <a href="{root}kontakt/" data-img="beratung"><small>06</small>Kontakt</a>
    </nav>
    <div class="menu__side">
      <div class="menu__preview" aria-hidden="true">
        ${['grasernte', 'haeckseln-1', 'gruenland-1', 'maehen', 'forstmulcher-2', 'agrarmonitor-tablet', 'beratung'].map((n, i) => `<img data-name="${n}" src="{root}assets/img/${n}-800.webp" alt="" loading="lazy"${i === 0 ? ' class="is-on"' : ''}>`).join('')}
      </div>
      <div class="menu__cols">
        ${sectors.map((s) => `<div><a class="label" href="{root}leistungen/${s.id}/">${s.short}</a><ul>${svcOf(s.id).map((x) => `<li><a href="{root}${x.path}">${x.title}</a></li>`).join('')}</ul></div>`).join('')}
      </div>
      <div class="menu__foot">
        <a href="${C.phoneHref}">${C.phone}</a><a href="mailto:${C.email}">${C.email}</a>
        <a href="${C.instagram}" target="_blank" rel="noopener">Instagram</a><a href="${C.facebook}" target="_blank" rel="noopener">Facebook</a>
      </div>
    </div>
  </div>
</div>`;
}

function contactBlock() {
  return `
<section class="cta" id="kontakt-cta">
  <div class="cta__bg" aria-hidden="true">${pic('gruenland-1', { alt: '', sizes: '100vw', attrs: 'data-parallax="0.12"' })}</div>
  <div class="wrap cta__inner">
    ${label('Kontaktieren Sie uns')}
    <h2 class="display cta__title" data-split>Interessiert? Lassen Sie sich zu Ihrem Projekt beraten.</h2>
    <div class="cta__row" data-reveal>
      <p>Noch Fragen? Schauen Sie in unsere <a class="ulink" href="{root}faq/">FAQs</a> oder wenden Sie sich an uns, um mehr über unser Dienstleistungsangebot und unsere Arbeitsweise zu erfahren.</p>
      ${btn('{root}kontakt/', 'Kontakt aufnehmen')}
    </div>
    <div class="cta__cards" data-stagger>
      <a class="ccard" href="mailto:${C.email}" data-reveal>${ICONS.mail}<span class="label">E-Mail</span><strong>${C.email}</strong><small>Melden Sie sich gerne auch per Mail.</small></a>
      <a class="ccard" href="${C.phoneHref}" data-reveal>${ICONS.phone}<span class="label">Telefon</span><strong>${C.phone}</strong><small>Jederzeit zu erreichen.</small></a>
      <a class="ccard" href="${C.maps}" target="_blank" rel="noopener" data-reveal>${ICONS.pin}<span class="label">Standort</span><strong>${C.street} · ${C.city}</strong><small>Vor Ort für Sie da: ${C.hours}</small></a>
    </div>
  </div>
</section>`;
}

function footer() {
  return `
<footer class="ftr">
  <div class="wrap ftr__top">
    <div class="ftr__brand">
      <img src="{root}assets/img/logo-weiss.png" width="720" height="174" alt="${C.name}" loading="lazy">
      <p>${C.claim}.<br>Familiengeführtes Lohnunternehmen seit 1973.</p>
      <div class="ftr__social">
        <a href="${C.instagram}" target="_blank" rel="noopener" aria-label="Instagram">${ICONS.insta}</a>
        <a href="${C.facebook}" target="_blank" rel="noopener" aria-label="Facebook">${ICONS.fb}</a>
      </div>
    </div>
    <nav class="ftr__col" aria-label="Leistungen"><p class="label">Leistungen</p>
      ${sectors.map((s) => `<a href="{root}leistungen/${s.id}/">${s.short}</a>`).join('')}<a href="{root}leistungen/werkstatt/">Werkstatt</a><a href="{root}leistungen/">Alle Leistungen</a></nav>
    <nav class="ftr__col" aria-label="Unternehmen"><p class="label">Unternehmen</p>
      <a href="{root}unternehmen/">Über uns</a><a href="{root}karriere/">Karriere</a><a href="{root}news/">News</a><a href="{root}faq/">FAQ</a><a href="{root}kontakt/">Kontakt</a></nav>
    <div class="ftr__col"><p class="label">Kontakt</p>
      <a href="${C.phoneHref}">${C.phone}</a><a href="mailto:${C.email}">${C.email}</a>
      <span>${C.street}<br>${C.city}</span><span>${C.hours}</span></div>
  </div>
  <div class="ftr__word" aria-hidden="true"><span>Linneweh</span></div>
  <div class="wrap ftr__bottom">
    <span>© ${YEAR} ${C.name}</span>
    <span><a href="{root}datenschutz/">Datenschutz</a><a href="{root}impressum/">Impressum &amp; AGB</a></span>
    <a class="ftr__up" href="#top">Nach oben ↑</a>
  </div>
</footer>`;
}

function layout({ path, title, desc, body, cls = '', img = 'grasernte', cta = true, loader = false, shy = true }) {
  const depth = path.split('/').filter(Boolean).length;
  const root = depth ? '../'.repeat(depth) : './';
  const full = path ? `${title} – ${C.name}` : title;
  const html = `<!doctype html>
<html lang="de" id="top">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(full)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${SITE_URL}${path}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="${C.name}">
<meta property="og:title" content="${esc(full)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${SITE_URL}assets/img/${img}-1600.webp">
<meta name="theme-color" content="#0f2a1c">
<link rel="icon" href="{root}assets/img/favicon.png" type="image/png">
<link rel="preload" href="{root}assets/fonts/barlow-condensed-800.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/barlow-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/main.css">
<script>document.documentElement.classList.add('js');setTimeout(function(){if(!window.__lul)document.documentElement.classList.add('no-anim')},4000);${loader ? "try{if(!sessionStorage.getItem('lul-intro'))document.documentElement.classList.add('intro')}catch(e){}" : ''}</script>
<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org', '@type': 'LocalBusiness', name: C.legal, url: SITE_URL, telephone: '+495173924940', email: C.email, foundingDate: '1973',
    address: { '@type': 'PostalAddress', streetAddress: C.street, postalCode: '29227', addressLocality: 'Celle', addressCountry: 'DE' },
    openingHours: 'Mo-Fr 07:00-19:00', sameAs: [C.instagram, C.facebook],
  })}</script>
</head>
<body class="${cls}">
<a class="skip" href="#main">Zum Inhalt springen</a>
${loader ? `<div class="loader" aria-hidden="true"><div class="loader__in"><img src="{root}assets/img/logo-weiss.png" width="720" height="174" alt=""><div class="loader__bar"><i></i></div><div class="loader__meta"><span>Seit 1973</span><span class="loader__num">0</span></div></div></div>` : ''}
${header(path)}
<main id="main">
${shy ? shyText(body + (cta ? contactBlock() : '')) : body}
</main>
${footer()}
<div class="mbar" data-mbar><a class="mbar__call" href="${C.phoneHref}">${ICONS.phone}<span>Anrufen</span></a><a class="mbar__ask" href="${path === 'kontakt/' ? '#f-name' : '{root}kontakt/'}"><span>Anfrage stellen</span>${ARROW}</a></div>
<dialog class="lb" aria-label="Bildansicht"><button class="lb__x" type="button" aria-label="Schließen">×</button><button class="lb__nav lb__prev" type="button" aria-label="Vorheriges Bild">‹</button><img alt=""><button class="lb__nav lb__next" type="button" aria-label="Nächstes Bild">›</button><p class="lb__cap"></p></dialog>
<div class="cursor" aria-hidden="true"><span></span></div>
<script src="{root}assets/js/main.js" defer></script>
</body>
</html>`;
  const file = join(OUT, path, 'index.html');
  mkdirSync(dirname(file), { recursive: true });
  let out = html.replaceAll('{root}', root);
  if (ART) {
    out = out.replace(/href="((?:\.\.?\/)(?:[^"#?]*\/)?)"/g, 'href="$1index.html"');
    if (!path) {
      const inner = out.slice(out.indexOf('>', out.indexOf('<body')) + 1, out.indexOf('</body>'));
      out = `<title>Linneweh Redesign</title>\n<link rel="stylesheet" href="./assets/css/main.css">\n<script>document.documentElement.lang='de';document.documentElement.id='top';document.documentElement.classList.add('js');document.body.className='${cls}';setTimeout(function(){if(!window.__lul)document.documentElement.classList.add('no-anim')},4000);${loader ? "try{if(!sessionStorage.getItem('lul-intro'))document.documentElement.classList.add('intro')}catch(e){}" : ''}</script>\n${inner}`;
    }
  }
  writeFileSync(file, out);
  pages.push(path);
}
const pages = [];

function pageHero({ kicker, title, sub, img, crumbs = [], tall = false }) {
  return `
<section class="phero${img ? '' : ' phero--plain'}${tall ? ' phero--tall' : ''}">
  ${img ? `<div class="phero__media" aria-hidden="true">${pic(img, { alt: '', eager: true, sizes: '100vw', attrs: 'data-parallax="0.18"' })}</div>` : '<div class="phero__pattern" aria-hidden="true"></div>'}
  <div class="wrap phero__inner">
    <nav class="crumbs" aria-label="Brotkrumen"><a href="{root}">Start</a>${crumbs.map(([p, t]) => `<span>/</span><a href="{root}${p}">${t}</a>`).join('')}</nav>
    ${label(kicker)}
    <h1 class="display phero__title${title.replace(/<[^>]+>/g, ' ').split(' ').some((w) => w.length > 14) ? ' phero__title--long' : ''}" data-split data-split-now>${title}</h1>
    ${sub ? `<p class="phero__sub" data-reveal data-reveal-now>${sub}</p>` : ''}
  </div>
</section>`;
}

const gallery = (names, title = 'Einblicke') => names.length ? `
<section class="gal-sec">
  <div class="wrap gal-sec__head">${label(title)}<p class="gal-sec__hint">Ziehen oder wischen · Klick für Großansicht</p></div>
  <div class="gal" data-drag>
    ${names.map((n) => `<a class="gal__item" href="${bigSrc(n)}" data-lightbox data-cap="${esc(altFor(n))}" data-cursor="Ansehen">${pic(n, { sizes: '(max-width:700px) 80vw, 40vw' })}</a>`).join('')}
  </div>
</section>` : '';

/* ------------------------------------------------------------------ Startseite */
function home() {
  const heroSlides = sectors.map((s, i) => `<div class="hero__slide${i === 0 ? ' is-active' : ''}">${pic(s.heroImg, { alt: i === 0 ? altFor(s.heroImg) : '', eager: i === 0, sizes: '100vw' })}</div>`).join('');
  const marquee = ['Mähen', 'Schwaden', 'Häckseln', 'Düngung', 'Aussaat', 'Forstmulchen', 'Holz rücken', 'Bäume kneifen', 'Wegebau', 'Winterdienst', 'Transport', 'Werkstatt'];
  const mq = marquee.map((t) => `<span>${t}</span><i aria-hidden="true">✳</i>`).join('');
  const panels = [
    ...sectors.map((s) => ({ nr: s.nr, short: s.short, title: s.title, text: s.teaser, img: s.cardImg, href: `leistungen/${s.id}/`, items: svcOf(s.id) })),
    { nr: '04', short: 'Werkstatt', title: 'Werkstatt', text: 'Wir bieten jetzt auch einen Werkstattservice in unserem Hause an – für Land- und Baumaschinen, Kraft- und Nutzfahrzeuge, Industrieanlagen sowie Kleingeräte.', img: 'transport-3', href: 'leistungen/werkstatt/', items: [] },
  ];
  const body = `
<section class="hero" data-hero>
  <div class="hero__media" aria-hidden="true">${heroSlides}</div>
  <div class="hero__shade" aria-hidden="true"></div>
  <div class="wrap hero__inner">
    ${label('Land- und forstwirtschaftliche Dienstleistungen · seit 1973', 'h1', 'hero__kicker')}
    <p class="display hero__title" aria-label="Im Einsatz für Ihr Feld, Ihren Forst und Ihre Kommune">
      <span class="hero__line" aria-hidden="true"><span>Im Einsatz für</span></span>
      <span class="hero__line" aria-hidden="true"><span class="hero__swap">${sectors.map((s, i) => `<b${i === 0 ? ' class="is-active"' : ''}>${s.swap}</b>`).join('')}</span></span>
    </p>
    <div class="hero__foot">
      <p class="hero__lead">Das Lohnunternehmen Linneweh bietet Ihnen Dienstleistungen im land- und forstwirtschaftlichen, sowie im kommunalen Sektor an. Gemeinsam mit Ihnen arbeiten wir für eine grünere Zukunft.</p>
      <div class="hero__cta">${btn('{root}kontakt/', 'Kontakt aufnehmen')}${btn('{root}leistungen/', 'Unsere Dienstleistungen', 'ghost')}</div>
    </div>
  </div>
  <div class="hero__tabs" role="tablist" aria-label="Bereiche">
    ${sectors.map((s, i) => `<button type="button" role="tab" aria-selected="${i === 0}" class="hero__tab${i === 0 ? ' is-active' : ''}"><small>${s.nr}</small><span>${s.short}</span><i aria-hidden="true"></i></button>`).join('')}
  </div>
  <a class="hero__badge" href="{root}unternehmen/" aria-label="Familienunternehmen seit 1973 – mehr über uns">
    <svg viewBox="0 0 120 120" aria-hidden="true"><defs><path id="circ" d="M60 60m-46 0a46 46 0 1 1 92 0a46 46 0 1 1-92 0"/></defs><text><textPath href="#circ">Familienunternehmen · seit 1973 · zwei Generationen · </textPath></text></svg>
    <strong>50+</strong>
  </a>
</section>

<div class="marquee" aria-hidden="true"><div class="marquee__track">${mq}${mq}</div></div>

<section class="sec values">
  <div class="wrap">
    <div class="sec__head">
      ${label('Was uns ausmacht')}
      <h2 class="display" data-split>Kundennah. Effizient. Erfahren.</h2>
    </div>
    <div class="values__grid" data-stagger>
      ${values.map((v, i) => `<article class="value" data-reveal><div class="value__ico">${ICONS[v.icon]}</div><span class="value__nr">0${i + 1}</span><h3>${v.title}</h3><p>${v.text}</p></article>`).join('')}
    </div>
  </div>
</section>

<section class="sec about">
  <div class="wrap about__grid">
    <div class="about__media">
      <figure class="frame frame--tall" data-reveal="clip">${pic('gruenland-1', { sizes: '(max-width:900px) 100vw, 45vw', attrs: 'data-parallax="0.12"' })}</figure>
      <figure class="frame about__small" data-reveal="clip">${pic('beratung', { sizes: '(max-width:900px) 50vw, 20vw' })}</figure>
    </div>
    <div class="about__text">
      ${label('Unser Unternehmen')}
      <h2 class="display" data-split>Familiengeführt. Seit zwei Generationen.</h2>
      <p class="lead" data-reveal>Die Lohnunternehmen Linneweh GmbH &amp; Co. KG steht Ihnen bei Ihrem Projekt im landwirtschaftlichen, forstwirtschaftlichen und kommunalen Sektor zur Seite. Seit über 50 Jahren agieren wir schon als Lohnunternehmen und haben Erfahrungen gesammelt, um Sie optimal zu unterstützen und zu beraten. Mit modernster Technologie sind wir ein zuverlässiger Partner an Ihrer Seite.</p>
      <p data-reveal>Als familiengeführtes Lohnunternehmen liegt uns die Zukunft am Herzen, darum unterstützen wir Sie dabei, die Ernährung und Energieversorgung zu sichern und für eine grünere Zukunft zu sorgen.</p>
      <p class="sign" data-reveal>${C.claim}<br><span>Ihr Lohnunternehmen Linneweh</span></p>
      <div data-reveal>${btn('{root}unternehmen/', 'Mehr erfahren', 'dark')}</div>
    </div>
  </div>
  <div class="wrap stats" data-stagger>
    <div class="stat" data-reveal><strong data-count="1973" data-plain>1973</strong><span>Gründung durch Günther Linneweh</span></div>
    <div class="stat" data-reveal><strong><b data-count="50">50</b>+</strong><span>Jahre Erfahrung als Lohnunternehmen</span></div>
    <div class="stat" data-reveal><strong data-count="2">2</strong><span>Generationen Familienbetrieb</span></div>
    <div class="stat" data-reveal><strong data-count="${allSvc.length}">${allSvc.length}</strong><span>Leistungen in Feld, Forst &amp; Kommune</span></div>
  </div>
</section>

<section class="sec show">
  <div class="wrap">
    <div class="sec__head sec__head--row">
      <div>${label('Im Einsatz')}<h2 class="display" data-split>Starke Technik. Echte Arbeit.</h2></div>
      <p class="show__note" data-reveal>Aufnahmen aus unserem Arbeitsalltag auf dem Feld, im Forst und auf der Straße.</p>
    </div>
    <div class="show__grid">
      ${showcase.map((x, i) => `<a class="show__item show__item--${'abcdef'[i]}" href="{root}${x.href}" data-reveal="clip" data-cursor="Öffnen">${pic(x.img, { sizes: '(max-width:800px) 100vw, 60vw' })}<span class="show__cap"><small>${x.sub}</small><strong class="display">${x.title}</strong></span></a>`).join('')}
    </div>
  </div>
</section>

<section class="hs" data-hscroll>
  <div class="hs__sticky">
    <div class="wrap hs__head">
      <div>${label('Unsere Dienstleistungen', 'p', 'label--light')}<h2 class="display" data-split>Ein Partner. Drei Bereiche.</h2></div>
      <div class="hs__meta"><span class="hs__count"><b>01</b> / 0${panels.length}</span><div class="hs__bar"><i></i></div></div>
    </div>
    <div class="wrap quad">
      ${panels.map((p) => `<a class="quad__item" href="{root}${p.href}"><span class="quad__img">${pic(p.img, { alt: '', sizes: '25vw' })}<i>${p.nr}</i></span><strong>${p.short}</strong></a>`).join('')}
    </div>
    <div class="hs__track">
      ${panels.map((p) => `
      <article class="panel">
        <div class="panel__media">${pic(p.img, { sizes: '(max-width:900px) 90vw, 60vw' })}</div>
        <div class="panel__body">
          <span class="panel__nr">${p.nr}</span>
          <h3 class="display">${p.title.replace(' Dienstleistungen', '<br>Dienstleistungen')}</h3>
          <p>${p.text}</p>
          ${p.items.length ? `<ul class="chips">${p.items.map((x) => `<li><a href="{root}${x.path}">${x.title}</a></li>`).join('')}</ul>` : ''}
          ${btn('{root}' + p.href, 'Zur Leistungsübersicht')}
        </div>
      </article>`).join('')}
    </div>
  </div>
</section>

<section class="facts">
  <div class="facts__bg" aria-hidden="true">${pic('ernte-staub', { alt: '', sizes: '100vw', attrs: 'data-parallax="0.12"' })}</div>
  <div class="wrap facts__inner">
    <div class="sec__head">${label('Technik in Zahlen', 'p', 'label--light')}<h2 class="display" data-split>Modernste Technik für höchste Präzision.</h2></div>
    <div class="facts__grid" data-stagger>
      ${facts.map((f) => `<a class="fact" href="{root}${f.href}" data-reveal><strong class="display">${f.n}<i>${f.unit}</i></strong><span>${f.label}</span>${ARROW}</a>`).join('')}
    </div>
  </div>
</section>

<section class="sec tech">
  <div class="wrap tech__grid">
    <div class="tech__text">
      ${label('Digital organisiert')}
      <h2 class="display" data-split>Wir arbeiten mit Agrarmonitor.</h2>
      <p class="lead" data-reveal>AGRARMONITOR ist die führende Software für Lohnunternehmen, Ackerbaubetriebe und Forstbetriebe. Dokumentation in Echtzeit statt nachträglichem Zettelschreiben durch synchronen Datenaustausch zwischen Fahrer und Büro.</p>
      <ol class="tech__list" data-stagger>
        ${agrarmonitor.map((a, i) => `<li data-reveal><span>0${i + 1}</span><div><h3>${a.title}</h3><p>${a.text}</p></div></li>`).join('')}
      </ol>
      <div data-reveal>${btn('{root}faq/', 'Mehr erfahren', 'dark')}</div>
    </div>
    <div class="tech__media">
      <figure class="frame frame--tall" data-reveal="clip">${pic('agrarmonitor-tablet', { sizes: '(max-width:900px) 100vw, 40vw', attrs: 'data-parallax="0.1"' })}</figure>
      <img class="tech__logo" src="{root}assets/img/agrarmonitor-logo.png" width="700" height="128" alt="AGRARMONITOR" loading="lazy" data-reveal>
    </div>
  </div>
</section>

<section class="sec newsx">
  <div class="wrap sec__head sec__head--row">
    <div>${label('Unsere Neuigkeiten')}<h2 class="display" data-split>Frisch vom Feld.</h2></div>
    <div class="newsx__ctrl"><button type="button" class="rbtn" data-prev aria-label="Zurück">${ARROW}</button><button type="button" class="rbtn" data-next aria-label="Weiter">${ARROW}</button>${btn('{root}news/', 'Alle News', 'dark')}</div>
  </div>
  <div class="newsx__track" data-drag data-carousel>
    ${news.map((n) => newsCard(n)).join('')}
  </div>
</section>

<section class="jobs">
  <div class="jobs__media" aria-hidden="true">${pic('maehen', { alt: '', sizes: '100vw', attrs: 'data-parallax="0.15"' })}</div>
  <div class="wrap jobs__inner">
    ${label('Karriere', 'p', 'label--light')}
    <h2 class="display" data-split>Wir suchen Verstärkung.</h2>
    <p data-reveal>Wenn du dich für die Land- und Forstwirtschaft interessierst, melde dich bei uns.</p>
    <div data-reveal>${btn('{root}karriere/', 'Zu den Stellenangeboten')}</div>
  </div>
</section>`;
  layout({ path: '', title: `${C.name} – Land- und Forstwirtschaftliche Dienstleistungen`, desc: 'Das Lohnunternehmen Linneweh bietet Dienstleistungen im land- und forstwirtschaftlichen sowie im kommunalen Sektor – familiengeführt seit 1973 in Celle.', body, cls: 'p-home', loader: true });
}

function newsCard(n) {
  return `<a class="ncard" href="{root}news/${n.slug}/" data-cursor="Lesen">
    <figure class="ncard__img">${pic(n.img, { sizes: '(max-width:700px) 80vw, 30vw' })}</figure>
    <span class="tag">${n.tag}</span>
    <h3>${n.title}</h3>
    <p>${n.lead}</p>
    <span class="more">Mehr lesen ${ARROW}</span>
  </a>`;
}

/* ------------------------------------------------------------------ Leistungen */
function leistungen() {
  const rows = [
    ...sectors.map((s) => ({ nr: s.nr, title: s.title, text: s.overview, img: s.cardImg, href: `leistungen/${s.id}/`, items: svcOf(s.id) })),
    { nr: '04', title: 'Werkstatt', text: 'Wir bieten jetzt auch einen Werkstattservice in unserem Hause an.', img: 'transport-3', href: 'leistungen/werkstatt/', items: [] },
  ];
  const body = `${pageHero({ kicker: 'Leistungsübersicht', title: 'Dienstleistungen', sub: 'Feld, Forst und Kommune – wir stimmen unsere Leistungen speziell auf Ihre Bedürfnisse ab.', img: 'haeckseln-2', crumbs: [['leistungen/', 'Leistungen']] })}
<section class="sec">
  <div class="wrap rows">
    ${rows.map((r) => `
    <article class="row" data-reveal>
      <a class="row__media frame" href="{root}${r.href}" data-cursor="Öffnen" tabindex="-1" aria-hidden="true">${pic(r.img, { alt: '', sizes: '(max-width:900px) 100vw, 40vw' })}</a>
      <div class="row__body">
        <span class="row__nr">${r.nr}</span>
        <h2 class="display"><a href="{root}${r.href}">${r.title}</a></h2>
        <p class="lead">${r.text}</p>
        ${r.items.length ? `<ul class="chips chips--dark">${r.items.map((x) => `<li><a href="{root}${x.path}">${x.title}</a></li>`).join('')}</ul>` : ''}
        ${btn('{root}' + r.href, 'Zur Leistungsübersicht', 'dark')}
      </div>
    </article>`).join('')}
  </div>
</section>`;
  layout({ path: 'leistungen/', title: 'Dienstleistungen', desc: 'Forstwirtschaftliche, landwirtschaftliche und kommunale Dienstleistungen sowie Werkstattservice vom Lohnunternehmen Linneweh.', body, img: 'haeckseln-2' });
}

function sectorPage(s) {
  const list = svcOf(s.id);
  const others = sectors.filter((x) => x.id !== s.id);
  const body = `${pageHero({ kicker: `${s.nr} — ${s.short}`, title: s.title.replace(' Dienstleistungen', '<br>Dienstleistungen'), sub: s.sub, img: s.pageImg, crumbs: [['leistungen/', 'Leistungen'], [`leistungen/${s.id}/`, s.short]], tall: true })}
<section class="sec intro">
  <div class="wrap intro__grid">
    <h2 class="display" data-split>${s.introTitle}</h2>
    <div>
      <p class="lead" data-reveal>${s.intro}</p>
      ${s.ral ? `<div class="ral" data-reveal><img src="{root}assets/img/ral-guetezeichen.png" width="200" height="400" alt="RAL Gütezeichen Wald- und Landschaftspflege" loading="lazy"><p><strong>Zertifiziert nach</strong><br>GZ 224/1 Holzernte<br>GZ 224/3 Waldverjüngung</p></div>` : ''}
    </div>
  </div>
</section>
<section class="sec sec--flush">
  <div class="wrap">
    <div class="scards" data-stagger>
      ${list.map((x, i) => `
      <a class="scard" href="{root}${x.path}" data-reveal data-cursor="Öffnen">
        <figure class="scard__img">${pic(x.hero, { sizes: '(max-width:700px) 100vw, (max-width:1100px) 50vw, 33vw' })}</figure>
        <div class="scard__body"><span class="scard__nr">${String(i + 1).padStart(2, '0')}</span><h3>${x.title}</h3><p>${x.teaser}</p><span class="more">Mehr erfahren ${ARROW}</span></div>
      </a>`).join('')}
    </div>
  </div>
</section>
<figure class="pband">
  ${pic(s.bandImg, { sizes: '100vw', attrs: 'data-parallax="0.14"' })}
  <figcaption class="wrap"><span class="label label--light"><span class="label__dot"></span>${s.short}</span><strong class="display" data-split>${s.sub}</strong></figcaption>
</figure>
<section class="sec cross">
  <div class="wrap">
    ${label('Weitere Bereiche')}
    <div class="cross__grid">
      ${others.map((o) => `<a class="cross__item" href="{root}leistungen/${o.id}/" data-reveal><span>${o.nr}</span><strong class="display">${o.short}</strong><p>${o.overview}</p>${ARROW}</a>`).join('')}
    </div>
  </div>
</section>`;
  layout({ path: `leistungen/${s.id}/`, title: s.title, desc: s.overview, body, img: s.pageImg });
}

function mcard(c) {
  const lists = c.lists.map((l) => {
    const spec = /Technische Daten|Spezifikationen/.test(l.label);
    return `<div class="mcard__list">${l.label ? `<h4 class="label">${l.label}</h4>` : ''}<ul class="${spec ? 'specs' : 'checks'}">${l.items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul></div>`;
  }).join('');
  return `<article class="mcard${c.lists.length > 1 ? ' mcard--wide' : ''}" data-reveal>
    ${c.kicker ? `<p class="mcard__kicker">${esc(c.kicker)}</p>` : ''}
    ${c.title ? `<h3>${esc(c.title)}</h3>` : ''}
    ${c.paras.map((p) => `<p>${esc(p)}</p>`).join('')}
    ${lists ? `<div class="mcard__lists">${lists}</div>` : ''}
  </article>`;
}
const paras = (list, leadFirst) => list.map((p, i) => (p.startsWith('- ') ? `<p class="cite">Quelle: ${esc(p.slice(2))}</p>` : `<p${leadFirst && i === 0 ? ' class="lead"' : ''} data-reveal>${esc(p)}</p>`)).join('');

function servicePage(x, i, list) {
  const s = sectorOf(x.sector);
  const secs = x.sections.map((sec, n) => ({ ...sec, id: sec.title ? slugify(sec.title) : 'ueberblick', label: sec.title || 'Überblick', n }));
  const prev = list[(i - 1 + list.length) % list.length];
  const next = list[(i + 1) % list.length];
  const body = `${pageHero({ kicker: `${s.short} · Leistung ${String(i + 1).padStart(2, '0')}`, title: x.title, sub: x.sub === x.title ? '' : x.sub, img: x.hero, crumbs: [['leistungen/', 'Leistungen'], [`leistungen/${s.id}/`, s.short], [x.path, x.title]], tall: true })}
<section class="sec svc">
  <div class="wrap svc__grid">
    <aside class="svc__aside">
      ${secs.length > 1 ? `<nav class="toc" aria-label="Auf dieser Seite"><p class="label">Auf dieser Seite</p>${secs.map((q) => `<a href="#${q.id}">${q.label}</a>`).join('')}</nav>` : ''}
      <div class="quick"><p class="label">Direkt anfragen</p><p>Wir beraten Sie gerne zu Ihrem Projekt.</p><a class="quick__tel" href="${C.phoneHref}">${C.phone}</a><a class="ulink" href="mailto:${C.email}?subject=${encodeURIComponent('Anfrage: ' + x.title)}">${C.email}</a></div>
    </aside>
    <div class="svc__body">
      ${secs.map((q) => `
      <section class="svc__sec" id="${q.id}">
        ${q.title ? `<h2 class="display" data-split>${esc(q.title)}</h2>` : ''}
        ${paras(q.paras, true)}
        ${q.cards.length ? `<div class="mcards">${q.cards.map(mcard).join('')}</div>` : ''}
        ${q.links.length ? `<ul class="xlinks">${q.links.map((l) => `<li><a href="${esc(l.href)}" target="_blank" rel="noopener">${esc(l.text)} <span aria-hidden="true">↗</span></a></li>`).join('')}</ul>` : ''}
      </section>`).join('')}
      <div data-reveal>${btn('{root}kontakt/', 'Kontakt aufnehmen', 'dark')}</div>
    </div>
  </div>
</section>
${gallery(x.gallery, 'Im Einsatz')}
<nav class="pn" aria-label="Weitere Leistungen">
  <a class="pn__item" href="{root}${prev.path}"><span class="label label--light">Vorherige Leistung</span><strong class="display">${prev.title}</strong></a>
  <a class="pn__item pn__item--next" href="{root}${next.path}"><span class="label label--light">Nächste Leistung</span><strong class="display">${next.title}</strong></a>
</nav>`;
  layout({ path: x.path, title: `${x.title} – ${s.short}`, desc: x.teaser, body, img: x.hero });
}

function werkstatt() {
  const w = svcData.werkstatt;
  const items = w.sections[0].cards[0].lists[0].items;
  const body = `${pageHero({ kicker: '04 — Werkstatt', title: 'Werkstatt', sub: 'Wir haben jetzt auch einen Werkstattservice im Hause.', crumbs: [['leistungen/', 'Leistungen'], ['leistungen/werkstatt/', 'Werkstatt']] })}
<section class="sec intro">
  <div class="wrap intro__grid">
    <h2 class="display" data-split>Service für Maschinen aller Art</h2>
    <p class="lead" data-reveal>Land- und Baumaschinen, Kraft- und Nutzfahrzeuge, Industrieanlagen sowie Kleingeräte.</p>
  </div>
</section>
<section class="sec sec--flush">
  <div class="wrap">
    ${label('Wir bieten')}
    <ul class="tiles" data-stagger>
      ${items.map((t, i) => `<li class="tile" data-reveal><span>${String(i + 1).padStart(2, '0')}</span><strong class="display">${t}</strong></li>`).join('')}
    </ul>
    <p class="lead tiles__note" data-reveal>Und vieles mehr – bei Interesse kontaktieren Sie uns gerne.</p>
    <div data-reveal>${btn('{root}kontakt/', 'Kontakt aufnehmen', 'dark')}</div>
  </div>
</section>`;
  layout({ path: 'leistungen/werkstatt/', title: 'Werkstatt', desc: 'Werkstattservice für Land- und Baumaschinen, Kraft- und Nutzfahrzeuge, Industrieanlagen sowie Kleingeräte.', body });
}

/* ------------------------------------------------------------------ Unternehmen, Karriere, FAQ */
function unternehmen() {
  const body = `${pageHero({ kicker: 'Über das Lohnunternehmen Linneweh', title: 'Unser Unternehmen', sub: C.claim, img: 'gruenland-1', crumbs: [['unternehmen/', 'Unternehmen']], tall: true })}
<section class="sec about">
  <div class="wrap about__grid">
    <div class="about__media">
      <figure class="frame frame--tall" data-reveal="clip">${pic('haeckseln-1', { sizes: '(max-width:900px) 100vw, 45vw', attrs: 'data-parallax="0.12"' })}</figure>
      <figure class="frame about__small" data-reveal="clip">${pic('transport-1', { sizes: '(max-width:900px) 50vw, 20vw' })}</figure>
    </div>
    <div class="about__text">
      ${label('Seit 1973')}
      <h2 class="display" data-split>${C.claim}</h2>
      <p class="lead" data-reveal>Unser 1973 gegründetes Familienunternehmen arbeitet nun schon seit zwei Generationen als Lohnunternehmen im land- und forstwirtschaftlichen, sowie kommunalen Sektor. Dabei war uns schon immer die Nähe zum Kunden wichtig, denn wir arbeiten für Sie, um Sie bestmöglich bei Ihrer Arbeit zu unterstützen.</p>
      <p data-reveal>Mit modernster Technologie bringen wir dafür nicht nur die nötige Erfahrung, sondern auch das passende Equipment mit, um auf Ihren Flächen das bestmögliche Ergebnis zu erzielen und die größtmöglichen Erträge zu erwirtschaften.</p>
      <p class="sign" data-reveal>${C.claim}<br><span>Ihr Lohnunternehmen Linneweh</span></p>
    </div>
  </div>
</section>
<section class="sec tl-sec">
  <div class="wrap">
    <div class="sec__head">${label('Unsere Geschichte', 'p', 'label--light')}<h2 class="display" data-split>Von 1973 bis heute.</h2></div>
    <ol class="tl" data-progress>
      ${timeline.map((t) => `<li class="tl__item" data-reveal><span class="tl__year display">${t.year}</span><div class="tl__text">${t.text ? `<p>${t.text}</p>` : `<ul>${t.list.map((l) => `<li>${l}</li>`).join('')}</ul>`}</div></li>`).join('')}
    </ol>
  </div>
</section>
<section class="sec certs">
  <div class="wrap certs__grid">
    <div>${label('Geprüfte Qualität')}<h2 class="display" data-split>Zertifiziert &amp; organisiert.</h2></div>
    <div class="certs__items" data-stagger>
      <div class="cert" data-reveal><img src="{root}assets/img/ral-guetezeichen.png" width="200" height="400" alt="RAL Gütezeichen" loading="lazy"><div><h3>RAL Gütezeichen</h3><p>Seit 2021 RAL-zertifiziert durch die Gütegemeinschaft Wald- und Landschaftspflege e.V. – GZ 224/1 Holzernte und GZ 224/3 Waldverjüngung.</p></div></div>
      <div class="cert" data-reveal><img src="{root}assets/img/blu-logo.png" width="258" height="300" alt="Bundesverband Lohnunternehmen e.V." loading="lazy"><div><h3>Mitglied im BLU</h3><p>Als Lohnunternehmen sind wir Mitglied beim Bundesverband Lohnunternehmen e.V., dem Berufsverband und Ansprechpartner für Lohnunternehmen in ganz Deutschland.</p></div></div>
      <div class="cert" data-reveal><img class="cert__wide" src="{root}assets/img/agrarmonitor-logo.png" width="700" height="128" alt="AGRARMONITOR" loading="lazy"><div><h3>Digital mit AGRARMONITOR</h3><p>Seit 2020 dokumentieren wir Aufträge in Echtzeit – durch synchronen Datenaustausch zwischen Fahrer und Büro.</p></div></div>
    </div>
  </div>
</section>
<section class="sec band">
  <div class="wrap band__in">
    <div>${label('Unsere Leistungen')}<h2 class="display" data-split>Vielfältig. Und auf Sie abgestimmt.</h2></div>
    <div><p class="lead" data-reveal>Wir bieten Ihnen ein vielfältiges Angebot an land- und forstwirtschaftlichen Dienstleistungen. Wir stimmen unsere Leistungen speziell auf Ihre Bedürfnisse ab.</p><div data-reveal>${btn('{root}leistungen/', 'Zur Leistungsübersicht', 'dark')}</div></div>
  </div>
</section>`;
  layout({ path: 'unternehmen/', title: 'Unser Unternehmen', desc: 'Familienunternehmen seit 1973: Das Lohnunternehmen Linneweh arbeitet seit zwei Generationen im land- und forstwirtschaftlichen sowie kommunalen Sektor.', body, img: 'gruenland-1' });
}

function karriere() {
  const subject = encodeURIComponent('Bewerbung: ' + job.title);
  const body = `${pageHero({ kicker: C.claim, title: 'Karriere bei uns', sub: 'Du möchtest Teil unseres Teams werden?', img: 'maehen', crumbs: [['karriere/', 'Karriere']], tall: true })}
<section class="sec intro">
  <div class="wrap intro__grid">
    <h2 class="display" data-split>Wir suchen Verstärkung</h2>
    <div>
      <p class="lead" data-reveal>Du möchtest Teil unseres Teams werden? Wir freuen uns über deine Initiativbewerbung. Bewirb dich ganz einfach per Post oder E-Mail.</p>
      <ul class="plain" data-reveal>
        <li>${ICONS.pin}<span>${C.name} · ${C.street} · ${C.city}</span></li>
        <li>${ICONS.mail}<a class="ulink" href="mailto:${C.email}">${C.email}</a></li>
        <li>${ICONS.phone}<a class="ulink" href="${C.phoneHref}">${C.phone}</a></li>
      </ul>
    </div>
  </div>
</section>
<section class="sec sec--flush">
  <div class="wrap">
    ${label('Offene Stelle')}
    <article class="job" data-reveal>
      <header class="job__head"><h2 class="display">${job.title}</h2><span class="tag tag--wheat">Teilzeit</span></header>
      <div class="job__cols">
        <div><h3 class="label">Was du mitbringen solltest</h3><ul class="checks">${job.need.map((t) => `<li>${t}</li>`).join('')}</ul></div>
        <div><h3 class="label">Was wir dir bieten</h3><ul class="checks">${job.offer.map((t) => `<li>${t}</li>`).join('')}</ul></div>
      </div>
      <div class="job__foot">${btn(`mailto:${C.email}?subject=${subject}`, 'Jetzt per E-Mail bewerben')}${btn('{root}kontakt/', 'Kontakt aufnehmen', 'dark')}</div>
    </article>
  </div>
</section>`;
  layout({ path: 'karriere/', title: 'Karriere', desc: 'Wir suchen Verstärkung: Landwirtschaftliche Aushilfskraft (m/w/d) in Teilzeit – oder bewirb dich initiativ beim Lohnunternehmen Linneweh.', body, img: 'maehen' });
}

function faq() {
  const body = `${pageHero({ kicker: 'Antworten & Ansprechpartner', title: 'Häufig gestellte Fragen', sub: 'Sie haben eine Frage zu unserem Unternehmen oder unseren Dienstleistungen? Hier finden Sie Antworten und Ansprechpartner.', crumbs: [['faq/', 'FAQ']] })}
<section class="sec intro">
  <div class="wrap intro__grid">
    <h2 class="display" data-split>Wir helfen gerne!</h2>
    <div>
      <p class="lead" data-reveal>Als Dienstleistungsunternehmen wissen wir, wie wichtig eine gute Beziehung zum Kunden ist, daher helfen wir Ihnen gerne weiter.</p>
      <p data-reveal>Hier finden Sie häufig gestellte Fragen, um Ihnen die Orientierung bei unserem Dienstleistungsangebot zu erleichtern.</p>
    </div>
  </div>
</section>
<section class="sec sec--flush">
  <div class="wrap acc" data-stagger>
    ${faqs.map((f, i) => `
    <details class="acc__item" data-reveal${i === 0 ? ' open' : ''}>
      <summary><span class="acc__nr">0${i + 1}</span><span class="acc__q display">${f.q}</span><span class="acc__ico" aria-hidden="true"></span></summary>
      <div class="acc__a">
        ${f.logo ? `<img class="acc__logo" src="{root}assets/img/${f.logo}" width="258" height="300" alt="Bundesverband Lohnunternehmen e.V." loading="lazy">` : ''}
        <div>${f.a.map((p) => `<p>${p}</p>`).join('')}
        ${f.am ? `<ol class="tech__list">${agrarmonitor.map((a, n) => `<li><span>0${n + 1}</span><div><h3>${a.title}</h3><p>${a.text}</p></div></li>`).join('')}</ol>` : ''}</div>
      </div>
    </details>`).join('')}
  </div>
</section>
<section class="sec band">
  <div class="wrap band__in">
    <div>${label('Sie haben Fragen?')}<h2 class="display" data-split>Fragen Sie uns einfach direkt.</h2></div>
    <div><p class="lead" data-reveal>Bei weiteren offenen Fragen wenden Sie sich gerne an uns.</p>
      <ul class="plain" data-reveal><li>${ICONS.mail}<a class="ulink" href="mailto:${C.email}">${C.email}</a></li><li>${ICONS.phone}<a class="ulink" href="${C.phoneHref}">${C.phone}</a></li></ul></div>
  </div>
</section>`;
  layout({ path: 'faq/', title: 'Häufig gestellte Fragen', desc: 'Was ist ein Lohnunternehmen? Was können wir für Sie tun? Antworten auf häufige Fragen zum Lohnunternehmen Linneweh.', body, img: 'agrarmonitor-tablet', cta: false });
}

/* ------------------------------------------------------------------ News */
function newsIndex() {
  const body = `${pageHero({ kicker: 'Unsere Neuigkeiten', title: 'News', sub: 'Maschinen, Einsätze und Angebote – frisch vom Feld, aus dem Forst und von der Straße.', crumbs: [['news/', 'News']] })}
<section class="sec">
  <div class="wrap ngrid" data-stagger>
    ${news.map((n) => newsCard(n).replace('class="ncard"', 'class="ncard" data-reveal')).join('')}
  </div>
</section>`;
  layout({ path: 'news/', title: 'News', desc: 'Neuigkeiten vom Lohnunternehmen Linneweh: Maschinen, Einsätze und Angebote aus Land- und Forstwirtschaft sowie dem kommunalen Bereich.', body, img: 'forstmulcher-2' });
}

function newsPost(n, i) {
  const next = news[(i + 1) % news.length];
  const bodyHtml = (n.body || []).map((b) => (b.p ? `<p data-reveal>${b.p}</p>` : b.h ? `<h2 class="post__h">${b.h}</h2>` : `<ul class="checks" data-reveal>${b.ul.map((t) => `<li>${t}</li>`).join('')}</ul>`)).join('');
  const body = `${pageHero({ kicker: `News · ${n.tag}`, title: n.title, img: n.img, crumbs: [['news/', 'News'], [`news/${n.slug}/`, n.title]], tall: true })}
<article class="sec post">
  <div class="wrap post__grid">
    <div class="post__body">
      <p class="lead post__lead" data-reveal>${n.lead}</p>
      ${bodyHtml}
      <p class="post__cta" data-reveal><strong>Interessiert?</strong> Dann melden Sie sich bei uns.</p>
      <div class="post__btns" data-reveal>${btn('{root}kontakt/', 'Kontakt aufnehmen')}${n.more ? btn('{root}' + n.more.href, n.more.text, 'dark') : ''}</div>
    </div>
    <aside class="post__aside"><div class="quick"><p class="label">Direkt anfragen</p><a class="quick__tel" href="${C.phoneHref}">${C.phone}</a><a class="ulink" href="mailto:${C.email}?subject=${encodeURIComponent('Anfrage: ' + n.title)}">${C.email}</a></div></aside>
  </div>
</article>
${gallery(n.gallery || [], 'Bilder')}
<nav class="pn pn--single" aria-label="Weitere News">
  <a class="pn__item pn__item--next" href="{root}news/${next.slug}/"><span class="label label--light">Nächste Neuigkeit</span><strong class="display">${next.title}</strong></a>
</nav>`;
  layout({ path: `news/${n.slug}/`, title: n.title, desc: n.lead, body, img: n.img });
}

/* ------------------------------------------------------------------ Kontakt & Rechtliches */
function kontakt() {
  const body = `${pageHero({ kicker: 'Wir sind für Sie da', title: 'Kontakt aufnehmen', sub: 'Das Team der Lohnunternehmen Linneweh GmbH &amp; Co. KG steht Ihnen gerne zur Seite.', img: 'beratung', crumbs: [['kontakt/', 'Kontakt']] })}
<section class="sec">
  <div class="wrap kgrid">
    <div class="kinfo">
      ${label('Kontaktieren Sie uns')}
      <h2 class="display" data-split>Fragen, Anregungen oder Unterstützung?</h2>
      <p class="lead" data-reveal>Sei es telefonisch oder per E-Mail. Wir sind immer gerne für Sie da.</p>
      <ul class="klist" data-stagger>
        <li data-reveal>${ICONS.phone}<div><span class="label">Telefon</span><a href="${C.phoneHref}">${C.phone}</a></div></li>
        <li data-reveal>${ICONS.mail}<div><span class="label">E-Mail</span><a href="mailto:${C.email}">${C.email}</a></div></li>
        <li data-reveal>${ICONS.pin}<div><span class="label">Standort</span><span>${C.name}<br>${C.street} · ${C.city}</span><small>Vor Ort für Sie da: ${C.hours}</small><a class="ulink" href="${C.maps}" target="_blank" rel="noopener">Route planen ↗</a></div></li>
      </ul>
    </div>
    <form class="kform" data-mailto="${C.email}" data-reveal novalidate>
      <p class="label">Projektanfrage</p>
      <div class="f f--half"><label for="f-name">Name *</label><input id="f-name" name="name" autocomplete="name" required></div>
      <div class="f f--half"><label for="f-tel">Telefon</label><input id="f-tel" name="telefon" type="tel" autocomplete="tel"></div>
      <div class="f"><label for="f-bereich">Bereich</label><select id="f-bereich" name="bereich"><option>Landwirtschaft</option><option>Forstwirtschaft</option><option>Kommunal</option><option>Werkstatt</option><option>Karriere</option><option>Sonstiges</option></select></div>
      <div class="f"><label for="f-msg">Ihre Nachricht *</label><textarea id="f-msg" name="nachricht" rows="5" required></textarea></div>
      <button class="btn btn--wheat" type="submit"><span>Anfrage per E-Mail senden</span>${ARROW}</button>
      <p class="kform__note" role="status">Die Anfrage wird in Ihrem E-Mail-Programm geöffnet – es werden keine Daten auf dieser Website gespeichert.</p>
    </form>
  </div>
</section>
<section class="sec sec--flush">
  <div class="wrap">
    ${label('Ansprechpartner')}
    <div class="people" data-stagger>
      ${team.map((t) => `
      <article class="person" data-reveal>
        <div class="person__img">${t.img ? `<img src="{root}assets/img/${t.img}" width="640" height="640" alt="${t.name}" loading="lazy">` : `<span aria-hidden="true">${t.name.split(' ').map((x) => x[0]).join('')}</span>`}</div>
        <div><h3 class="display">${t.name}</h3><p class="label">${t.role}</p><a class="ulink" href="mailto:${t.email}">${t.email}</a><a class="ulink" href="${C.phoneHref}">${C.phone}</a></div>
      </article>`).join('')}
    </div>
  </div>
</section>
<section class="sec band">
  <div class="wrap band__in">
    <div>${label('Unsere Leistungen')}<h2 class="display" data-split>Vielfältig. Und auf Sie abgestimmt.</h2></div>
    <div><p class="lead" data-reveal>Wir bieten Ihnen ein vielfältiges Angebot an land- und forstwirtschaftlichen Dienstleistungen. Wir stimmen unsere Leistungen speziell auf Ihre Bedürfnisse ab.</p><div data-reveal>${btn('{root}leistungen/', 'Zur Leistungsübersicht', 'dark')}</div></div>
  </div>
</section>`;
  layout({ path: 'kontakt/', title: 'Kontakt', desc: `Kontakt zum Lohnunternehmen Linneweh: ${C.phone}, ${C.email}, ${C.street}, ${C.city}.`, body, img: 'beratung', cta: false });
}

function legalPage(key, path, title) {
  const map = { h2: 'h2', h3: 'h3', h4: 'h3', h5: 'h4', h6: 'h4' };
  let html = ''; let inList = false;
  for (const [k, t] of legal[key]) {
    if (k === 'li') { if (!inList) { html += '<ul>'; inList = true; } html += `<li>${esc(t)}</li>`; continue; }
    if (inList) { html += '</ul>'; inList = false; }
    html += k === 'p' ? `<p>${esc(t)}</p>` : `<${map[k]}>${esc(t)}</${map[k]}>`;
  }
  if (inList) html += '</ul>';
  html = html.replace('Website: https://web.agrarhelden.de/linneweh/', 'Website: https://lu-linneweh.com/');
  const body = `${pageHero({ kicker: 'Rechtliches', title, crumbs: [[path, title]] })}
<section class="sec"><div class="wrap"><div class="prose">${html}</div></div></section>`;
  layout({ path, title, desc: `${title} der ${C.legal}.`, body, cta: false, shy: false });
}

function notFound() {
  const body = `${pageHero({ kicker: 'Fehler 404', title: 'Hier ist das Feld leer.', sub: 'Die gesuchte Seite gibt es nicht (mehr).' })}
<section class="sec"><div class="wrap">${btn('/', 'Zur Startseite', 'dark')}</div></section>`;
  layout({ path: '', title: 'Seite nicht gefunden', desc: 'Seite nicht gefunden', body, cta: false });
  const f = join(OUT, 'index.html');
  writeFileSync(join(OUT, '404.html'), readFileSync(f, 'utf8').replaceAll('"./', '"/').replace(/<link rel="canonical"[^>]*>/, '<meta name="robots" content="noindex">'));
  pages.pop();
}

/* ------------------------------------------------------------------ Build */
notFound();
home();
leistungen();
sectors.forEach(sectorPage);
sectors.forEach((s) => { const list = svcOf(s.id); list.forEach((x, i) => servicePage(x, i, list)); });
werkstatt();
unternehmen();
karriere();
faq();
newsIndex();
news.forEach(newsPost);
kontakt();
legalPage('impressum', 'impressum/', 'Impressum & AGB');
legalPage('datenschutz', 'datenschutz/', 'Datenschutz');

writeFileSync(join(OUT, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${pages.map((p) => `  <url><loc>${SITE_URL}${p}</loc></url>`).join('\n')}\n</urlset>\n`);
writeFileSync(join(OUT, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${SITE_URL}sitemap.xml\n`);
console.log(`✔ ${pages.length} Seiten erzeugt in ./site`);
