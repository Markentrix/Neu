// Baut die statische Seite: node build.js  ->  site/
const fs=require('fs'),path=require('path');
const OUT='site',BASE='https://www.pizzeria-molise-celle.de';
const css=fs.readFileSync('src/style.css','utf8').replace(/url\(fonts\//g,'url(assets/fonts/').replace(/\n/g,'');
const TEL='05141 21 44 21',TELH='+495141214421';
const it=(n,d,p,tag)=>`<div class="it"><h3>${n}${tag?`<span class="tag">${tag}</span>`:''}</h3><span class="pr">${p}</span>${d?`<p>${d}</p>`:''}</div>`;
const menu={
 'Pizza':[['Margherita','Tomaten, Mozzarella','5,50 €'],['Funghi','Champignons','6,50 €','vegetarisch'],['Prosciutto','Schinken','7,50 €'],['Hawaii','Schinken, Ananas','8,00 €'],['Calzone','Salami, Schinken, Champignons','8,50 €'],['Spezialpizzen','Hausspezialitäten','bis 10,50 €'],['Pizza vom Blech','Handpizza zum Mitnehmen','ab 4,00 €']],
 'Pasta &amp; Überbackenes':[['Spaghetti Carbonara','Ei, Speck, Parmesan','7,50 €'],['Pasta mit Meeresfrüchten','Frutti di Mare','bis 9,50 €'],['Lasagne','Überbacken','ab 8,00 €'],['Tortellini','Überbacken','bis 8,50 €']],
 'Flammkuchen':[['Flammkuchen klassisch','Crème fraîche, Zwiebeln, Speck','ab 5,00 €'],['Flammkuchen Spezial','Wechselnde Beläge, auch vegetarisch','bis 11,00 €']],
 'Salate &amp; Antipasti':[['Bruschetta al Pomodoro','','3,00 €','vegan'],['Insalata Mista','Eisberg, Tomaten, Gurken','4,50 €'],['Insalata Molise','Oliven, Zwiebeln, Mozzarella, Mais','7,00 €'],['Insalata Pollo','Hähnchenbrust, Feta, Rucola, Mais','7,50 €'],['Antipasti misti','Gemischte Platte mit Pizzabrot','12,00 €']]
};
const menuHtml=Object.entries(menu).map(([h,l])=>`<p class="cat">${h}</p>${l.map(x=>it(...x)).join('')}`).join('');
const NAV=[['speisekarte.html','Speisekarte'],['pizza-zum-mitnehmen.html','Zum Mitnehmen'],['vegetarisch-vegan.html','Vegetarisch &amp; vegan'],['italiener-celle-altstadt.html','Anfahrt']];
const faqs=[['Wo finde ich die Pizzeria Molise in Celle?','Die Pizzeria Molise liegt in der Piltzergasse in der Altstadt von Celle (29221), wenige Schritte vom Großen Plan entfernt.'],['Wie kann ich einen Tisch reservieren?',`Über das Formular auf der Startseite oder telefonisch unter ${TEL}.`],['Gibt es Pizza zum Mitnehmen?','Ja. Handpizza und viele Gerichte gibt es am Straßenfenster zum Mitnehmen. Pizza vom Blech gibt es ab 4 Euro.'],['Gibt es vegetarische und vegane Gerichte?','Ja. Vegetarische und vegane Gerichte sind auf der Speisekarte gekennzeichnet.'],['Welche Öffnungszeiten hat die Pizzeria Molise?','Montag bis Samstag von 11:00 bis 20:00 Uhr. Sonntag ist Ruhetag.']];
const faqHtml=faqs.map(([q,a])=>`<details><summary>${q}</summary><p>${a}</p></details>`).join('');
const J=o=>`<script type="application/ld+json">${JSON.stringify(o)}</script>`;
const rest={"@type":["Restaurant","Pizzeria"],"@id":BASE+"/#restaurant","name":"Pizzeria Molise","url":BASE+"/","image":BASE+"/assets/og.png","description":"Italienische Pizzeria in der Altstadt von Celle mit Pizza, Pasta, Flammkuchen und Handpizza zum Mitnehmen.","servesCuisine":["Italienisch","Pizza","Pasta"],"priceRange":"€€","telephone":TELH,"acceptsReservations":"True","hasMenu":BASE+"/speisekarte.html","address":{"@type":"PostalAddress","streetAddress":"Piltzergasse 1","postalCode":"29221","addressLocality":"Celle","addressRegion":"Niedersachsen","addressCountry":"DE"},"geo":{"@type":"GeoCoordinates","latitude":52.6256,"longitude":10.0804},"areaServed":{"@type":"City","name":"Celle"},"openingHoursSpecification":[{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],"opens":"11:00","closes":"20:00"}],"potentialAction":{"@type":"ReserveAction","target":{"@type":"EntryPoint","urlTemplate":BASE+"/#reservieren"},"result":{"@type":"Reservation","name":"Tischreservierung"}}};
const faqLd={"@type":"FAQPage","mainEntity":faqs.map(([q,a])=>({"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}))};

function page({file,title,desc,h1,eyebrow,lead,body,home,ld,noindex,hero}){
  const url=BASE+'/'+(file==='index.html'?'':file);
  const crumbs=home?'':`<p class="crumb"><a href="./">Startseite</a> / ${h1.replace(/<[^>]+>/g,'')}</p>`;
  const graph=home?[rest,faqLd,{"@type":"WebSite","@id":BASE+"/#website","url":BASE+"/","name":"Pizzeria Molise Celle","inLanguage":"de-DE"}]
    :[{"@type":"WebPage","@id":url,"url":url,"name":title,"isPartOf":{"@id":BASE+"/#website"},"about":{"@id":BASE+"/#restaurant"},"inLanguage":"de-DE"},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Startseite","item":BASE+"/"},{"@type":"ListItem","position":2,"name":h1.replace(/<[^>]+>/g,''),"item":url}]},...(ld||[])];
  return `<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title><meta name="description" content="${desc}">
<meta name="robots" content="${noindex?'noindex,follow':'index,follow,max-image-preview:large,max-snippet:-1'}">
<link rel="canonical" href="${url}">
<meta name="theme-color" content="#008C45"><meta name="color-scheme" content="light">
<meta name="geo.region" content="DE-NI"><meta name="geo.placename" content="Celle"><meta name="geo.position" content="52.6256;10.0804"><meta name="ICBM" content="52.6256, 10.0804">
<meta property="og:type" content="website"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="Pizzeria Molise Celle"><meta property="og:title" content="${title}"><meta property="og:description" content="${desc}"><meta property="og:url" content="${url}"><meta property="og:image" content="${BASE}/assets/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/bricolage.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="assets/fonts/instrument.woff2" as="font" type="font/woff2" crossorigin>
<style>${css}</style>
${J({"@context":"https://schema.org","@graph":graph})}
</head><body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="top"><div class="w bar"><a class="logo" href="./"><i aria-hidden="true"></i>Pizzeria Molise</a>
<nav aria-label="Hauptnavigation">${NAV.map(([h,t])=>`<a href="${h}">${t}</a>`).join('')}<a class="btn" href="${home?'':'./'}#reservieren">Tisch reservieren</a></nav></div></header>
<main id="main">
${hero||`<div class="w"><div class="page-hero">${crumbs}<h1>${h1}</h1><p class="lead">${lead}</p></div></div>`}
${body}</main>
<footer><div class="tri" aria-hidden="true" style="margin-bottom:28px"></div><div class="w"><div>Pizzeria Molise · Piltzergasse · 29221 Celle · <a href="tel:${TELH}">${TEL}</a></div><nav aria-label="Fußzeile"><a href="speisekarte.html">Speisekarte</a><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></nav></div></footer>
<a class="sticky" href="${home?'':'./'}#reservieren">Tisch reservieren</a>
${home?'<script src="assets/app.js" defer></script>':''}
</body></html>`;
}
const cta=`<section class="sec"><div class="w split"><div class="side"><p class="lbl">Reservierung</p><h2>Tisch sichern</h2></div><div><p class="prose" style="margin:0 0 1.4rem;color:var(--mute)">Online reservieren oder anrufen. Ab 8 Personen bitte telefonisch.</p><div class="row"><a class="btn acc" href="./#reservieren">Online reservieren</a><a class="btn out" href="tel:${TELH}">${TEL}</a></div></div></div></section>`;
const cards=`<section class="sec"><div class="w"><p class="lbl">Mehr entdecken</p><div class="three"><a href="speisekarte.html"><b>Speisekarte</b><span>Pizza, Pasta, Flammkuchen, Salate</span></a><a href="pizza-zum-mitnehmen.html"><b>Zum Mitnehmen</b><span>Handpizza am Straßenfenster</span></a><a href="vegetarisch-vegan.html"><b>Vegetarisch &amp; vegan</b><span>Fleischlos essen in Celle</span></a></div></div></section>`;

const pages=[];
// ---------- Startseite
const img=(n,alt,lz)=>`<img class="ph" src="assets/img/${n}.svg" width="600" height="400" alt="${alt}" loading="${lz===false?'eager':'lazy'}" decoding="async">`;
const hoursTbl=`<table class="hrs"><caption class="lbl">Öffnungszeiten</caption><tr><th scope="row">Montag bis Samstag</th><td>11:00 – 20:00</td></tr><tr><th scope="row">Sonntag</th><td>Ruhetag</td></tr></table>`;
const route=`<a class="route" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&amp;query=Pizzeria+Molise+Piltzergasse+Celle">Route in Google Maps planen<span>Piltzergasse, 29221 Celle</span></a>`;
const listOf=n=>Object.entries(menu).slice(0,n).map(([h,l])=>`<p class="cat">${h}</p>${l.map(x=>it(...x)).join('')}`).join('');
pages.push({file:'index.html',home:true,
 title:'Pizzeria Molise Celle | Pizza & Pasta in der Altstadt, Tisch reservieren',
 desc:`Pizzeria Molise in der Celler Altstadt: Pizza, Pasta, Flammkuchen und Handpizza zum Mitnehmen. Jetzt online Tisch reservieren oder anrufen: ${TEL}.`,
 hero:`<div class="w hero"><div><p class="lbl">Italienisch · Piltzergasse · Celle</p><h1>Pizza, Pasta und Flammkuchen in der Celler Altstadt.</h1><p class="lead">Am Tisch genießen oder als Handpizza am Fenster mitnehmen.</p><div class="row"><a class="btn acc" href="#reservieren">Tisch reservieren</a><a class="btn out" href="speisekarte.html">Speisekarte</a></div></div>
<aside class="tafel" aria-label="Öffnungszeiten und Kontakt"><p class="state" id="state">Mo–Sa 11–20 Uhr</p><dl><dt>Mo–Sa</dt><dd>11:00 – 20:00</dd><dt>So</dt><dd>Ruhetag</dd></dl><address>Piltzergasse<br>29221 Celle<br><a href="tel:${TELH}">${TEL}</a></address></aside></div>`,
 body:`<div class="w"><div class="three"><a href="pizza-zum-mitnehmen.html"><b>Handpizza am Fenster</b><span>Ab 4 € zum Mitnehmen</span></a><a href="vegetarisch-vegan.html"><b>Vegetarisch &amp; vegan</b><span>Auf der Karte gekennzeichnet</span></a><a href="italiener-celle-altstadt.html"><b>Mitten in der Altstadt</b><span>Am Großen Plan in Celle</span></a></div></div>
<div class="w" style="margin-top:8px"><div class="gal"><figure>${img('pizza','Illustration: Pizza Margherita mit Mozzarella und Basilikum')}</figure><figure>${img('pasta','Illustration: Teller Spaghetti')}</figure><figure>${img('calzone','Illustration: Calzone mit Rotwein')}</figure></div></div>
<section class="sec" id="speisekarte"><div class="w split"><div class="side"><p class="lbl">Speisekarte</p><h2>Auf den Tisch kommt</h2><p>Auszug. Preise nach Stand März 2024.</p></div><div>${listOf(2)}<p class="note">Vegetarische und vegane Gerichte sind gekennzeichnet. <a href="speisekarte.html">Komplette Speisekarte</a></p></div></div></section>
<section class="sec"><div class="w split"><div class="side"><p class="lbl">Über uns</p><h2>Familiär geführt, mitten im Fachwerk</h2>${img('raum','Illustration: gemütlicher Gastraum mit Pizzaofen und karierten Tischdecken')}</div><div class="prose"><p>Zwischen den Fachwerkhäusern von Celle gibt es bei uns Pizza, Pasta und Flammkuchen ohne Schnickschnack. Ob Mittagspause beim Stadtbummel oder Familienessen: Setzen Sie sich zu uns oder nehmen Sie Ihre Handpizza direkt am Straßenfenster mit.</p><ul class="facts"><li><b>Pizza ab 5,50 €</b><span>vom Blech ab 4 €</span></li><li><b>Vegetarisch und vegan</b><span>gekennzeichnet</span></li><li><b>Zentral</b><span>nahe Großer Plan</span></li></ul></div></div></section>
<section class="sec"><div class="w split"><div class="side"><p class="lbl">Gästestimmen</p><h2>Auf Google bewertet</h2></div><div><blockquote style="margin:0"><p class="q">„Das Essen ist ausgezeichnet, die Calzone ist ein Brocken und richtig lecker. Das Personal ist extrem schnell und freundlich.“</p><cite>Google-Rezension</cite></blockquote><div class="qs"><blockquote style="margin:0"><p>„Gute Pizzen mit frischen Zutaten und ausgewogenem Geschmack. Gemütlich und einladend.“</p><cite>Google-Rezension</cite></blockquote><blockquote style="margin:0"><p>„Die Preise sind okay, etwa 11 bis 13 Euro pro Mahlzeit.“</p><cite>Google-Rezension</cite></blockquote></div></div></div></section>
<section class="band" id="reservieren"><div class="w split"><div class="side"><p class="lbl">Reservierung</p><h2>Ihr Tisch in der Altstadt</h2><p>Wir bestätigen Ihre Anfrage per Telefon. Ab 8 Personen bitte kurz anrufen.</p><a class="tel" href="tel:${TELH}">${TEL}</a></div>
<form id="resForm" name="reservierung" method="POST" action="/danke.html" data-netlify="true" netlify-honeypot="bot-field"><input type="hidden" name="form-name" value="reservierung"><p class="hp" aria-hidden="true"><label>Nicht ausfüllen<input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
<div class="g"><label>Datum<input id="datum" type="date" name="datum" required></label><label>Uhrzeit<select id="zeit" name="zeit" required></select></label><label>Personen<select id="personen" name="personen" required></select></label><label>Name<input type="text" name="name" autocomplete="name" required></label></div>
<label>Telefon<input type="tel" name="telefon" autocomplete="tel" required></label><label>Wünsche oder Allergien (optional)<input type="text" name="nachricht"></label>
<label class="check"><input type="checkbox" name="datenschutz" required><span>Ich stimme der Verarbeitung meiner Angaben zur Bearbeitung der Reservierung zu (<a href="datenschutz.html">Datenschutz</a>).</span></label>
<button class="btn" type="submit">Reservierung anfragen</button><p class="msg" id="resMsg" role="status" aria-live="polite"></p><p class="hint">Lieber per WhatsApp? <a id="waLink" href="https://wa.me/495141214421" rel="noopener">Anfrage senden</a></p></form></div></section>
<section class="sec"><div class="w split"><div class="side"><p class="lbl">FAQ</p><h2>Häufige Fragen</h2></div><div>${faqHtml}</div></div></section>
<section class="sec" id="kontakt"><div class="w split"><div class="side"><p class="lbl">Anfahrt</p><h2>So finden Sie uns</h2></div><div><address><b>Pizzeria Molise</b><br>Piltzergasse<br>29221 Celle<br><a href="tel:${TELH}">${TEL}</a></address><br>${hoursTbl}${route}</div></div></section>`});
// ---------- Speisekarte
pages.push({file:'speisekarte.html',title:'Speisekarte Pizzeria Molise Celle | Pizza, Pasta, Flammkuchen',desc:'Die Speisekarte der Pizzeria Molise in Celle: Pizza ab 5,50 €, Pasta, Flammkuchen, Salate und Antipasti. Vegetarische und vegane Gerichte gekennzeichnet.',h1:'Speisekarte',lead:'Pizza, Pasta, Flammkuchen, Salate und Antipasti. Preise nach Stand März 2024.',
 body:`<section class="sec"><div class="w split"><div class="side"><p class="lbl">Pizzeria Molise</p><h2>Alles auf einen Blick</h2>${img('calzone','Illustration: Calzone mit Rotwein',false)}</div><div>${menuHtml}<p class="note">Vegetarische und vegane Gerichte sind gekennzeichnet. Bei Allergien fragen Sie bitte das Team. Änderungen vorbehalten.</p></div></div></section>${cta}${cards}`,
 ld:[{"@type":"Menu","name":"Speisekarte Pizzeria Molise","inLanguage":"de-DE","hasMenuSection":Object.entries(menu).map(([h,l])=>({"@type":"MenuSection","name":h.replace(/&amp;/g,'&'),"hasMenuItem":l.map(([n,d,p])=>({"@type":"MenuItem","name":n,"description":d||undefined,"offers":{"@type":"Offer","priceCurrency":"EUR","price":(p.match(/\d+,\d+/)||['0'])[0].replace(',','.')}}))}))}]});
// ---------- Mitnehmen
pages.push({file:'pizza-zum-mitnehmen.html',title:'Pizza zum Mitnehmen in Celle | Handpizza am Fenster – Pizzeria Molise',desc:'Handpizza und Pizza vom Blech zum Mitnehmen in der Celler Altstadt. Schnell am Straßenfenster der Pizzeria Molise, Pizza ab 4 Euro.',h1:'Pizza zum Mitnehmen in der Altstadt',lead:'Schnell, warm und fair im Preis: Holen Sie Ihre Pizza direkt am Straßenfenster in der Piltzergasse.',
 body:`<section class="sec"><div class="w split"><div class="side"><p class="lbl">Handpizza am Fenster</p><h2>Für die Pause zwischendurch</h2>${img('fenster','Illustration: Straßenfenster mit grün-weiß-roter Markise und Pizzastück',false)}</div><div class="prose"><p>Neben dem Restaurantbereich gibt es bei uns ein <strong>Straßenfenster</strong>. Dort bekommen Sie Handpizza und Pizza vom Blech, ohne sich hinzusetzen. Das passt zum Stadtbummel, zur Mittagspause oder für den kleinen Hunger zwischendurch.</p><p>Sie möchten lieber sitzen? Dann <a href="./#reservieren">reservieren Sie einen Tisch</a>.</p><ul class="facts"><li><b>Pizza vom Blech</b><span>ab 4,00 €</span></li><li><b>Margherita</b><span>5,50 €</span></li><li><b>Calzone</b><span>8,50 €</span></li><li><b>Geöffnet</b><span>Mo–Sa 11–20 Uhr</span></li></ul></div></div></section>${cta}${cards}`});
// ---------- Vegan
pages.push({file:'vegetarisch-vegan.html',title:'Vegetarisch & vegan essen in Celle | Pizzeria Molise',desc:'Vegetarische und vegane Pizza, Pasta, Bruschetta und Salate in der Celler Altstadt. Auf der Speisekarte der Pizzeria Molise gekennzeichnet.',h1:'Vegetarisch und vegan essen in Celle',lead:'Auf unserer Karte finden Sie vegetarische und vegane Gerichte. Sie sind gekennzeichnet, damit Sie schnell wählen können.',
 body:`<section class="sec"><div class="w split"><div class="side"><p class="lbl">Fleischlos genießen</p><h2>Das passt für fleischlose Gäste</h2>${img('pizza','Illustration: Pizza Margherita',false)}</div><div><div class="prose"><p>Zu den vegetarischen Klassikern zählen <strong>Pizza Margherita</strong> und <strong>Pizza Funghi</strong>. Die <strong>Bruschetta al Pomodoro</strong> ist vegan. Beim Flammkuchen gibt es Varianten ohne Fleisch.</p></div>${it('Margherita','Tomaten, Mozzarella','5,50 €','vegetarisch')}${it('Funghi','Champignons','6,50 €','vegetarisch')}${it('Bruschetta al Pomodoro','','3,00 €','vegan')}${it('Insalata Mista','Eisberg, Tomaten, Gurken','4,50 €')}<p class="note">Bei Allergien fragen Sie bitte das Team oder tragen Sie Hinweise bei der <a href="./#reservieren">Reservierung</a> ein. Die genaue Kennzeichnung finden Sie auf der <a href="speisekarte.html">Speisekarte</a>.</p></div></div></section>${cta}${cards}`});
// ---------- Anfahrt / lokal
pages.push({file:'italiener-celle-altstadt.html',title:'Italiener in der Celler Altstadt | Anfahrt & Öffnungszeiten – Pizzeria Molise',desc:'So finden Sie die Pizzeria Molise in der Piltzergasse, Celle: Anfahrt, Öffnungszeiten, Telefon und Route zum Italiener in der Altstadt.',h1:'Italiener in der Celler Altstadt',lead:'Die Pizzeria Molise liegt in der Piltzergasse, mitten in der Altstadt von Celle.',
 body:`<section class="sec"><div class="w split"><div class="side"><p class="lbl">Anfahrt</p><h2>So finden Sie uns</h2>${img('raum','Illustration: Gastraum',false)}</div><div><address><b>Pizzeria Molise</b><br>Piltzergasse<br>29221 Celle<br>Niedersachsen<br><a href="tel:${TELH}">${TEL}</a></address><br>${hoursTbl}<div class="prose"><p>Sie finden uns zu Fuß wenige Schritte vom <strong>Großen Plan</strong> entfernt, im Herzen der Altstadt mit ihren Fachwerkhäusern.</p></div>${route}</div></div></section><section class="sec"><div class="w split"><div class="side"><p class="lbl">FAQ</p><h2>Häufige Fragen</h2></div><div>${faqHtml}</div></div></section>${cta}${cards}`,ld:[faqLd]});
// ---------- rechtliches + danke
const legal=(f,t)=>pages.push({file:f,noindex:true,title:`${t} | Pizzeria Molise Celle`,desc:`${t} der Pizzeria Molise in Celle.`,h1:t,lead:'',body:`<section class="sec"><div class="w prose"><p>Platzhalter: Bitte den rechtlich korrekten Text des Betreibers einfügen (${f==='impressum.html'?'Name, Anschrift, Kontakt, ggf. USt-ID':'Verantwortlicher, Zwecke und Rechtsgrundlagen, Reservierungsformular, Google-Maps-Link, Hosting'}).</p></div></section>`});
legal('impressum.html','Impressum');legal('datenschutz.html','Datenschutz');
pages.push({file:'danke.html',noindex:true,title:'Danke für Ihre Anfrage | Pizzeria Molise Celle',desc:'Ihre Reservierungsanfrage wurde übermittelt.',h1:'Danke für Ihre Anfrage',lead:'Wir melden uns zur Bestätigung telefonisch bei Ihnen.',body:`<section class="sec"><div class="w"><a class="btn acc" href="./">Zur Startseite</a></div></section>`});

for(const p of pages)fs.writeFileSync(path.join(OUT,p.file),page(p));
const idx=pages.filter(p=>!p.noindex);
fs.writeFileSync(OUT+'/sitemap.xml',`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${idx.map(p=>`<url><loc>${BASE}/${p.file==='index.html'?'':p.file}</loc><lastmod>2026-10-06</lastmod></url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(OUT+'/llms.txt',`# Pizzeria Molise Celle

> Italienische Pizzeria in der Altstadt von Celle (Piltzergasse, 29221 Celle). Pizza, Pasta, Flammkuchen, Handpizza zum Mitnehmen. Vegetarische und vegane Gerichte. Telefon ${TEL}. Mo–Sa 11:00–20:00, Sonntag Ruhetag.

## Seiten
- [Startseite und Reservierung](${BASE}/): Überblick, Tisch reservieren, FAQ
- [Speisekarte](${BASE}/speisekarte.html): Pizza ab 5,50 €, Pasta, Flammkuchen, Salate
- [Pizza zum Mitnehmen](${BASE}/pizza-zum-mitnehmen.html): Handpizza am Straßenfenster, ab 4 €
- [Vegetarisch und vegan](${BASE}/vegetarisch-vegan.html): fleischlose Gerichte
- [Anfahrt und Öffnungszeiten](${BASE}/italiener-celle-altstadt.html): Lage, Route, Zeiten
`);
console.log('gebaut:',pages.length,'Seiten');
