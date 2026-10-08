// Restaurant-Layout: node layouts/restaurant/build.js   (aus dem Repo-Root)
// Baut die komplette Website nach site/. Alle Inhalte stehen in config.json,
// Bilder in site/assets/img/<name>.webp (oder .svg als Platzhalter).
const fs=require('fs'),path=require('path');
const here=__dirname,OUT=path.join(here,'../../site'),C=JSON.parse(fs.readFileSync(path.join(here,'config.json'),'utf8'));
const css=fs.readFileSync(path.join(here,'style.css'),'utf8').replace(/url\(fonts\//g,'url(assets/fonts/').replace(/\n/g,'');
const js=fs.readFileSync(path.join(here,'app.js'),'utf8');
const mins=s=>{const[a,b]=s.split(':');return +a*60+ +b};
const DAYS=['So','Mo','Di','Mi','Do','Fr','Sa'];
const cfg={name:C.name,phone:C.phone,wa:C.whatsapp,maxPersons:C.maxPersons,closedDow:DAYS.indexOf(C.hours.closedDay),from:mins(C.slots.from),to:mins(C.slots.to),step:C.slots.stepMin,open:mins(C.hours.open),close:mins(C.hours.close),openLabel:C.hours.open.replace(':00','')+' Uhr',closeLabel:C.hours.close.replace(':00','')+' Uhr'};
const ext=n=>fs.existsSync(path.join(OUT,'assets/img/'+n+'.webp'))?'webp':'svg';
const imgSrc=n=>`assets/img/${n}.${ext(n)}`;
const srcset=n=>`assets/img/${n}-480.webp 480w, assets/img/${n}-720.webp 720w, assets/img/${n}.webp 960w`;
const img=(n,alt,eager,cls,sizes)=>{const w=ext(n)==='webp';return `<img${cls?` class="${cls}"`:''} src="${imgSrc(n)}"${w?` srcset="${srcset(n)}" sizes="${sizes||'(max-width:600px) 92vw, 460px'}"`:''} width="${w?960:600}" height="${w?640:400}" alt="${alt}" loading="${eager?'eager':'lazy'}" decoding="async"${eager?' fetchpriority="high"':''}>`};
const tag=t=>t?`<span class="tag">${t}</span>`:'';
const item=([n,d,p,t])=>`<div class="it"><h3>${n}${tag(t)}</h3><span class="pr">${p}</span>${d?`<p>${d}</p>`:''}</div>`;
const place=`${C.street}, ${C.zip} ${C.city}`,BASE=C.base,TEL=C.phone,TELH=C.phoneHref;
const mapsUrl=`https://www.google.com/maps/search/?api=1&amp;query=${encodeURIComponent(C.name+' '+place)}`;
const J=o=>`<script type="application/ld+json">${JSON.stringify(o)}</script>`;
const faqHtml=C.faq.map(([q,a])=>`<details><summary>${q}</summary><p>${a}</p></details>`).join('');
const faqLd={"@type":"FAQPage","mainEntity":C.faq.map(([q,a])=>({"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}))};
const price=p=>{const m=/^(\d+),(\d+) €$/.exec(p);return m?{"@type":"Offer","priceCurrency":"EUR","price":m[1]+'.'+m[2]}:undefined};
const menuLd={"@type":"Menu","name":"Speisekarte "+C.name,"inLanguage":"de-DE","hasMenuSection":C.menu.map(m=>({"@type":"MenuSection","name":m.title,"hasMenuItem":m.items.map(([n,d,p])=>({"@type":"MenuItem","name":n,...(d?{"description":d}:{}),...(price(p)?{"offers":price(p)}:{})}))}))};
const restLd={"@type":["Restaurant","Pizzeria"],"@id":BASE+"/#restaurant","name":C.name,"url":BASE+"/","image":[BASE+"/assets/og.jpg",...C.menu.map(m=>BASE+"/"+imgSrc(m.img))],"hasMap":"https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(C.name+" "+place),"menu":BASE+"/#karte","description":"Italienische Pizzeria in der Altstadt von Celle mit Pizza, Pasta, Flammkuchen und Handpizza zum Mitnehmen.","servesCuisine":["Italienisch","Pizza","Pasta"],"priceRange":"€€","telephone":"+"+C.whatsapp,"acceptsReservations":"True","hasMenu":menuLd,
 "address":{"@type":"PostalAddress","streetAddress":C.street,"postalCode":C.zip,"addressLocality":C.city,"addressRegion":"Niedersachsen","addressCountry":"DE"},"geo":{"@type":"GeoCoordinates","latitude":52.6256,"longitude":10.0804},"areaServed":{"@type":"City","name":C.city},
 "openingHoursSpecification":[{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],"opens":C.hours.open,"closes":C.hours.close}],
 "potentialAction":{"@type":"ReserveAction","target":{"@type":"EntryPoint","urlTemplate":BASE+"/#reservieren"},"result":{"@type":"Reservation","name":"Tischreservierung"}}};

const NAVL=[['@karte','Speisekarte'],['pizza-zum-mitnehmen.html','Zum Mitnehmen'],['vegetarisch-vegan.html','Vegetarisch &amp; vegan'],['@kontakt','Anfahrt']];
const E=s=>String(s).replace(/&(?!amp;|[a-z]+;|#\d+;)/g,'&amp;');
function shell(p){
  const home=p.home,b=home?'':'./',url=BASE+'/'+(home?'':p.file);
  const href=h=>h[0]==='@'?b+'#'+h.slice(1):h;
  const crumbLd=home?[]:[{"@type":"WebPage","@id":url,"url":url,"name":p.title,"isPartOf":{"@id":BASE+"/#website"},"about":{"@id":BASE+"/#restaurant"},"inLanguage":"de-DE"},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Startseite","item":BASE+"/"},{"@type":"ListItem","position":2,"name":p.h1.replace(/<[^>]+>/g,''),"item":url}]}];
  const graph=home?[restLd,faqLd,{"@type":"WebSite","@id":BASE+"/#website","url":BASE+"/","name":C.name+" "+C.city,"inLanguage":"de-DE"}]:[...crumbLd,...(p.ld||[])];
  const robots=p.noindex||!C.indexable?'noindex,follow':'index,follow,max-image-preview:large,max-snippet:-1';
  return `<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${E(p.title)}</title><meta name="description" content="${E(p.desc)}">
<meta name="robots" content="${robots}"><link rel="canonical" href="${url}"><meta name="theme-color" content="#CD212A"><meta name="color-scheme" content="light">
<meta name="geo.region" content="DE-NI"><meta name="geo.placename" content="${C.city}"><meta name="geo.position" content="52.6256;10.0804"><meta name="ICBM" content="52.6256, 10.0804">
<meta property="og:type" content="website"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="${C.name} ${C.city}"><meta property="og:title" content="${E(p.title)}"><meta property="og:description" content="${E(p.desc)}"><meta property="og:url" content="${url}"><meta property="og:image" content="${BASE}/assets/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="${C.name} ${C.city}: Pizza Margherita"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="assets/apple-touch-icon.png"><link rel="manifest" href="assets/manifest.webmanifest">
<link rel="preload" href="assets/fonts/anton.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="assets/fonts/instrument.woff2" as="font" type="font/woff2" crossorigin>${home?`<link rel="preload" as="image" href="${imgSrc(C.hero.img)}" imagesrcset="${srcset(C.hero.img)}" imagesizes="(max-width:860px) 92vw, 500px" fetchpriority="high">`:''}
<style>${css}</style>${J({"@context":"https://schema.org","@graph":graph})}</head><body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="top"><div class="tape"></div><div class="w bar"><a class="logo" href="${b||'./'}">${C.name}</a><nav aria-label="Hauptnavigation">${NAVL.map(([h,t])=>`<a href="${href(h)}">${t}</a>`).join('')}<a class="tel" href="tel:${TELH}">${TEL}</a><a class="btn sm" href="${b}#reservieren">Tisch reservieren</a></nav></div></header>
<main id="main">${p.body}</main>
<footer><div class="tape"></div><div class="w" style="padding-top:22px"><span>${C.name} · ${place}</span><nav aria-label="Fußzeile"><a href="${b}#karte">Speisekarte</a><a href="pizza-zum-mitnehmen.html">Zum Mitnehmen</a><a href="vegetarisch-vegan.html">Vegetarisch &amp; vegan</a><a href="italiener-celle-altstadt.html">Anfahrt</a><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a></nav></div></footer>
<div class="dock"><a class="btn" href="${b}#reservieren">Reservieren</a><a class="btn alt" href="tel:${TELH}">Anrufen</a></div>
${home?`<script>window.RES_CFG=${JSON.stringify(cfg)};${js}</script>`:`<script>(function(){var h=document.querySelector('.top');function f(){document.documentElement.style.setProperty('--hh',h.offsetHeight+'px')}f();addEventListener('resize',f)})()</script>`}
</body></html>`;
}

const cta=`<section class="ctab"><div class="w"><strong>Tisch reservieren</strong><div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn" href="./#reservieren">Online anfragen</a><a class="btn alt" href="tel:${TELH}">${TEL}</a></div></div></section>`;
const more=`<section class="w"><div class="linkrow" style="padding-top:44px"><a href="./#karte"><b>Speisekarte</b><span>Pizza, Pasta, Flammkuchen, Salate, Antipasti</span></a><a href="pizza-zum-mitnehmen.html"><b>Zum Mitnehmen</b><span>Handpizza am Straßenfenster</span></a><a href="vegetarisch-vegan.html"><b>Vegetarisch &amp; vegan</b><span>Fleischlos essen in Celle</span></a></div></section>`;
const hoursTbl=`<table class="hrs"><caption style="position:absolute;left:-999px">Öffnungszeiten</caption><tbody><tr><th scope="row">Mo–Sa</th><td>${C.hours.open} – ${C.hours.close}</td></tr><tr><th scope="row">${C.hours.closedDay}</th><td>Ruhetag</td></tr></tbody></table>`;
const subpage=(o)=>({noindex:false,...o,body:`<div class="w"><div class="phero"><p class="crumb"><a href="./">Startseite</a> / ${o.h1.replace(/<[^>]+>/g,'')}</p><h1>${o.h1}</h1><p class="lead">${o.lead}</p></div></div><div class="w"><div class="pgrid"><div>${o.left}</div><div class="prose">${o.right}</div></div></div>${cta}${more}`});

const pages=[];
// ---------- Startseite
pages.push({file:'index.html',home:true,title:C.seo.title,desc:C.seo.description,h1:C.name,body:`
<section class="w hero"><div><p class="status" id="status">${C.hours.text}</p>
<h1>${C.headline.map((l,i)=>`<span${i===C.highlight?' class="hl"':''}>${l}</span>`).join('')}</h1>
<p class="lead">${C.lead}</p></div>
<div class="photo">${img(C.hero.img,C.hero.alt,true,'','(max-width:860px) 92vw, 500px')}<div class="sticker" aria-hidden="true"><div><b>${C.hero.stickerPrice}</b>${C.hero.stickerName}</div></div></div></section>
<section class="w resw" id="reservieren" aria-label="Tisch reservieren"><form id="rf" name="reservierung" method="POST" action="/danke.html" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="reservierung"><p class="hp" aria-hidden="true"><label>Nicht ausfüllen<input type="text" name="bot-field" tabindex="-1" autocomplete="off"></label></p>
<div class="rrow"><strong class="rt">Tisch reservieren</strong>
<label class="f">Tag<select name="datum" id="fd" required></select></label><label class="f">Uhrzeit<select name="zeit" id="fz" required></select></label><label class="f">Personen<select name="personen" id="fp" required></select></label>
<button class="btn sm" type="button" id="next">Weiter</button></div>
<div class="rwrap" id="rw"><div class="rclip"><div class="rmore" id="more"><label class="f">Name<input class="t" type="text" name="name" autocomplete="name" required></label><label class="f">Telefon<input class="t" type="tel" name="telefon" autocomplete="tel" required></label>
<button class="btn sm" type="submit">Anfrage senden</button>
<label class="chk"><input type="checkbox" name="datenschutz" required><span>Ich stimme der Verarbeitung meiner Angaben zur Reservierung zu (<a href="datenschutz.html">Datenschutz</a>).</span></label>
<a class="wa" id="wa" href="https://wa.me/${C.whatsapp}" rel="noopener">Lieber per WhatsApp</a></div></div></div>
<p class="msg" id="msg" role="status" aria-live="polite"></p></form></section>
<section class="menuwrap" id="karte"><nav class="nav2" aria-label="Kategorien"><span class="nt">Speisekarte</span>${C.menu.map(m=>`<a href="#${m.id}">${m.title}</a>`).join('')}</nav>
<div class="w">${C.menu.map(m=>`<section class="cat" id="${m.id}"><div class="cimg"><h2>${m.title}</h2>${img(m.img,m.alt)}<p>${m.note}</p></div><div class="list">${m.items.map(item).join('')}</div></section>`).join('')}<p class="foot-note">Preise nach Stand März 2024, Änderungen vorbehalten. Bei Allergien fragen Sie bitte das Team.</p></div></section>
<section class="take" id="mitnehmen"><div class="w grid"><div><h2>Pizza<br>zum Mitnehmen</h2><p>Handpizza und Pizza vom Blech direkt am Straßenfenster. Ab 4 Euro, schnell und warm.</p><a class="btn" href="pizza-zum-mitnehmen.html">Mehr erfahren</a></div><div>${img('fenster','Illustration: Straßenfenster mit grün-weiß-roter Markise')}</div></div></section>
<section class="w info" id="kontakt"><div><h2>Anfahrt</h2><address>${C.name}<br>${C.street}<br>${C.zip} ${C.city}<br><a href="tel:${TELH}">${TEL}</a></address><p><a href="${mapsUrl}" target="_blank" rel="noopener">Route in Google Maps</a> · <a href="italiener-celle-altstadt.html">Mehr zur Lage</a></p></div>
<div><h2>Öffnungszeiten</h2>${hoursTbl}</div><div class="faqs"><h2>Gut zu wissen</h2>${faqHtml}</div></section>`});
// ---------- Zum Mitnehmen
pages.push(subpage({file:'pizza-zum-mitnehmen.html',title:'Pizza zum Mitnehmen in Celle | Handpizza am Fenster – Pizzeria Molise',desc:'Handpizza und Pizza vom Blech zum Mitnehmen in der Celler Altstadt. Schnell am Straßenfenster der Pizzeria Molise, Pizza ab 4 Euro.',h1:'Pizza zum Mitnehmen',lead:'Schnell, warm und fair im Preis: Holen Sie Ihre Pizza direkt am Straßenfenster in der Piltzergasse.',
 left:`<h2>Für die Pause zwischendurch</h2>${img('fenster','Illustration: Straßenfenster mit grün-weiß-roter Markise und Pizzastück',true,'pimg')}`,
 right:`<p>Neben dem Restaurantbereich gibt es bei uns ein <strong>Straßenfenster</strong>. Dort bekommen Sie Handpizza und Pizza vom Blech, ohne sich hinzusetzen. Das passt zum Stadtbummel, zur Mittagspause oder für den kleinen Hunger zwischendurch.</p><p>Die Pizza vom Blech gibt es <strong>ab 4 Euro</strong>, Margherita kostet 5,50 Euro. Sie möchten lieber sitzen? Dann <a href="./#reservieren">reservieren Sie einen Tisch</a>.</p>${[['Pizza vom Blech','Handpizza zum Mitnehmen','ab 4,00 €'],['Margherita','Tomaten, Mozzarella','5,50 €'],['Calzone','Salami, Schinken, Champignons','8,50 €']].map(item).join('')}<p style="margin-top:18px">Geöffnet Montag bis Samstag von ${C.hours.open} bis ${C.hours.close} Uhr.</p>`}));
// ---------- Vegetarisch & vegan
pages.push(subpage({file:'vegetarisch-vegan.html',title:'Vegetarisch & vegan essen in Celle | Pizzeria Molise',desc:'Vegetarische und vegane Pizza, Bruschetta und Salate in der Celler Altstadt. Auf der Speisekarte der Pizzeria Molise gekennzeichnet.',h1:'Vegetarisch &amp; vegan in Celle',lead:'Vegetarische und vegane Gerichte sind auf unserer Karte gekennzeichnet, damit Sie schnell wählen können.',
 left:`<h2>Fleischlos genießen</h2>${img('salat','Gemischter Salat mit Tomaten, Gurken, Oliven und Mozzarella',true,'pimg')}`,
 right:`<p>Zu den vegetarischen Klassikern zählen <strong>Pizza Margherita</strong> und <strong>Pizza Funghi</strong>. Die <strong>Bruschetta al Pomodoro</strong> ist vegan. Beim Flammkuchen gibt es Varianten ohne Fleisch.</p>${[['Margherita','Tomaten, Mozzarella','5,50 €','vegetarisch'],['Funghi','Champignons','6,50 €','vegetarisch'],['Bruschetta al Pomodoro','','3,00 €','vegan'],['Insalata Mista','Eisberg, Tomaten, Gurken','4,50 €']].map(item).join('')}<p style="margin-top:18px">Bei Allergien fragen Sie bitte das Team oder tragen Sie Hinweise bei der Reservierung ein. Die genaue Kennzeichnung finden Sie auf der <a href="./#karte">Speisekarte</a>.</p>`}));
// ---------- Anfahrt
pages.push(subpage({file:'italiener-celle-altstadt.html',title:'Italiener in der Celler Altstadt | Anfahrt & Öffnungszeiten – Pizzeria Molise',desc:'So finden Sie die Pizzeria Molise in der Piltzergasse, Celle: Anfahrt, Öffnungszeiten, Telefon und Route zum Italiener in der Altstadt.',h1:'Italiener in der Celler Altstadt',lead:'Die Pizzeria Molise liegt in der Piltzergasse, mitten in der Altstadt von Celle.',ld:[faqLd],
 left:`<h2>So finden Sie uns</h2>${img('raum','Illustration: gemütlicher Gastraum mit Pizzaofen und karierten Tischdecken',true,'pimg')}<address style="font-style:normal;font-size:1.15rem;margin:22px 0 18px">${C.name}<br>${C.street}<br>${C.zip} ${C.city}<br><a href="tel:${TELH}">${TEL}</a></address>${hoursTbl}<p><a class="btn" href="${mapsUrl}" target="_blank" rel="noopener">Route in Google Maps</a></p>`,
 right:`<p>Sie finden uns zu Fuß wenige Schritte vom <strong>Großen Plan</strong> entfernt, im Herzen der Altstadt mit ihren Fachwerkhäusern.</p><div class="faqs">${faqHtml}</div>`}));
// ---------- Rechtliches
const draft=`<p class="draftnote"><strong>Entwurf.</strong> Platzhalter in eckigen Klammern durch die echten Angaben ersetzen und den Text rechtlich prüfen lassen.</p>`;
const legalPage=(f,t,html)=>pages.push({file:f,noindex:true,title:`${t} | ${C.name} ${C.city}`,desc:`${t} der ${C.name} in ${C.city}.`,h1:t,body:`<div class="w"><div class="phero"><p class="crumb"><a href="./">Startseite</a> / ${t}</p><h1>${t}</h1></div><div class="prose legal">${draft}${html}</div></div>`});
legalPage('impressum.html','Impressum',`<h2>Angaben gemäß § 5 DDG</h2><p>[Name des Betreibers bzw. Firma und Rechtsform]<br>[Straße und Hausnummer]<br>${C.zip} ${C.city}</p>
<h2>Kontakt</h2><p>Telefon: <a href="tel:${TELH}">${TEL}</a><br>E-Mail: [E-Mail-Adresse]</p>
<h2>Vertretungsberechtigt</h2><p>[Name der vertretungsberechtigten Person]</p>
<h2>Umsatzsteuer-Identifikationsnummer</h2><p>[USt-IdNr. gemäß § 27a UStG, falls vorhanden]</p>
<h2>Verbraucherstreitbeilegung</h2><p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen. [Bitte prüfen]</p>
<h2>Haftung für Inhalte und Links</h2><p>Wir erstellen die Inhalte dieser Seite mit Sorgfalt. Für die Richtigkeit, Vollständigkeit und Aktualität können wir keine Gewähr übernehmen. Für Inhalte externer Seiten, auf die wir verlinken, sind ausschließlich deren Betreiber verantwortlich.</p>`);
legalPage('datenschutz.html','Datenschutz',`<h2>1. Verantwortlicher</h2><p>[Name des Betreibers bzw. Firma], [Anschrift], ${C.zip} ${C.city}<br>Telefon: <a href="tel:${TELH}">${TEL}</a>, E-Mail: [E-Mail-Adresse]</p>
<h2>2. Hosting und Server-Logfiles</h2><p>Diese Website wird bei [Hosting-Anbieter, z. B. Netlify] gehostet. Beim Aufruf werden technisch notwendige Daten (IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browser und Betriebssystem) in Server-Logfiles verarbeitet. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (Betrieb und Sicherheit der Website). Mit dem Hosting-Anbieter besteht [ein Vertrag zur Auftragsverarbeitung].</p>
<h2>3. Cookies, Analyse und Werbung</h2><p>Diese Website setzt keine Cookies, nutzt keine Analyse- oder Werbedienste und lädt Schriften von ihrem eigenen Server.</p>
<h2>4. Tischreservierung</h2><p>Wenn Sie eine Reservierung anfragen, verarbeiten wir Datum, Uhrzeit, Personenzahl, Ihren Namen und Ihre Telefonnummer sowie freiwillige Angaben, um Ihre Anfrage zu bearbeiten und zu bestätigen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Anbahnung und Durchführung eines Vertrags). Die Angaben werden über die Formularfunktion des Hosting-Anbieters an uns übermittelt und nach [z. B. 30 Tagen nach dem Termin] gelöscht.</p>
<h2>5. WhatsApp</h2><p>Auf der Seite gibt es einen Link, mit dem Sie uns eine Nachricht über WhatsApp senden können. Erst wenn Sie den Link anklicken, öffnet sich WhatsApp (Meta Platforms Ireland Ltd.) und es gelten deren Datenschutzbestimmungen. [Nur behalten, wenn der Link genutzt wird]</p>
<h2>6. Google Maps</h2><p>Wir verlinken auf Google Maps für die Routenplanung. Die Karte ist nicht in die Seite eingebunden. Erst beim Anklicken des Links werden Daten an Google übertragen.</p>
<h2>7. Ihre Rechte</h2><p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Eine erteilte Einwilligung können Sie jederzeit widerrufen. Sie können sich außerdem bei einer Aufsichtsbehörde beschweren, zum Beispiel bei der Landesbeauftragten für den Datenschutz Niedersachsen.</p>
<p>Stand: ${new Date().toISOString().slice(0,10)}</p>`);
pages.push({file:'danke.html',noindex:true,title:`Danke für Ihre Anfrage | ${C.name} ${C.city}`,desc:'Ihre Reservierungsanfrage wurde übermittelt.',h1:'Danke',body:`<div class="w"><div class="phero"><h1>Danke für Ihre Anfrage</h1><p class="lead">Wir melden uns zur Bestätigung telefonisch bei Ihnen.</p><p style="margin-top:24px"><a class="btn" href="./">Zur Startseite</a></p></div></div>`});

pages.push({file:'404.html',noindex:true,title:`Seite nicht gefunden | ${C.name} ${C.city}`,desc:'Diese Seite gibt es nicht.',h1:'Seite nicht gefunden',body:`<div class="w"><div class="phero"><h1>Diese Seite gibt es nicht</h1><p class="lead">Vielleicht finden Sie hier, was Sie suchen.</p><p style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap"><a class="btn" href="./">Zur Startseite</a><a class="btn alt" href="./#karte">Speisekarte</a></p></div></div>`});
for(const p of pages)fs.writeFileSync(path.join(OUT,p.file),shell(p));
const idx=pages.filter(p=>!p.noindex);
const today=new Date().toISOString().slice(0,10);
const imgXml=C.menu.map(m=>`<image:image><image:loc>${BASE}/${imgSrc(m.img)}</image:loc><image:title>${m.title} bei ${C.name} ${C.city}</image:title></image:image>`).join('');
fs.writeFileSync(path.join(OUT,'sitemap.xml'),`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n${idx.map(p=>`<url><loc>${BASE}/${p.file==='index.html'?'':p.file}</loc><lastmod>${today}</lastmod>${p.file==='index.html'?imgXml:''}</url>`).join('\n')}\n</urlset>\n`);
fs.writeFileSync(path.join(OUT,'llms-full.txt'),`# ${C.name} ${C.city}: vollständige Angaben

Italienische Pizzeria in der Altstadt von Celle (${place}). Telefon ${TEL}. Öffnungszeiten: ${C.hours.text}, ${C.hours.closedDay} Ruhetag. Reservierung online unter ${BASE}/#reservieren oder telefonisch. Handpizza zum Mitnehmen am Straßenfenster.

## Speisekarte (Preise Stand März 2024, Änderungen vorbehalten)
${C.menu.map(m=>`### ${m.title}\n${m.items.map(([n,d,p,t])=>`- ${n}${d?' ('+d+')':''}: ${p}${t?' ['+t+']':''}`).join('\n')}`).join('\n\n')}

## Häufige Fragen
${C.faq.map(([q,a])=>`**${q}** ${a}`).join('\n\n')}
`);
fs.writeFileSync(path.join(OUT,'llms.txt'),`# ${C.name} ${C.city}

> Italienische Pizzeria in der Altstadt von Celle (${place}). Pizza, Pasta, Flammkuchen, Salate, Antipasti, Handpizza zum Mitnehmen. Vegetarische und vegane Gerichte. Telefon ${TEL}. ${C.hours.text}, ${C.hours.closedDay} Ruhetag.

## Seiten
- [Startseite, Speisekarte und Reservierung](${BASE}/): Tisch reservieren, komplette Karte, FAQ
- [Pizza zum Mitnehmen](${BASE}/pizza-zum-mitnehmen.html): Handpizza am Straßenfenster, ab 4 €
- [Vegetarisch und vegan](${BASE}/vegetarisch-vegan.html): fleischlose Gerichte
- [Anfahrt und Öffnungszeiten](${BASE}/italiener-celle-altstadt.html): Lage, Route, Zeiten

## Optional
- [Vollständige Angaben mit Speisekarte als Text](${BASE}/llms-full.txt)
`);
fs.writeFileSync(path.join(OUT,'_headers'),`/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()\n  Strict-Transport-Security: max-age=31536000; includeSubDomains\n  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n`);
fs.writeFileSync(path.join(OUT,'_redirects'),`/speisekarte.html  /#karte  301\n/gastro.html  /  301\n`);
console.log('gebaut:',pages.length,'Seiten');
