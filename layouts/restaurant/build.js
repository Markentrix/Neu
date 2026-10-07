// Restaurant-Layout: node layouts/restaurant/build.js  ->  site/gastro.html
// Alle Inhalte stehen in config.json. Bilder: site/assets/img/<name>.svg (oder .jpg/.webp tauschen).
const fs=require('fs'),path=require('path');
const here=__dirname,C=JSON.parse(fs.readFileSync(path.join(here,'config.json'),'utf8'));
const css=fs.readFileSync(path.join(here,'style.css'),'utf8').replace(/url\(fonts\//g,'url(assets/fonts/').replace(/\n/g,'');
const js=fs.readFileSync(path.join(here,'app.js'),'utf8');
const mins=s=>{const[a,b]=s.split(':');return +a*60+ +b};
const cfg={name:C.name,phone:C.phone,wa:C.whatsapp,maxPersons:C.maxPersons,closedDow:['So','Mo','Di','Mi','Do','Fr','Sa'].indexOf(C.hours.closedDay),
 from:mins(C.slots.from),to:mins(C.slots.to),step:C.slots.stepMin,open:mins(C.hours.open),close:mins(C.hours.close),openLabel:C.hours.open.replace(':00',''),closeLabel:C.hours.close.replace(':00','')+' Uhr'};
cfg.openLabel=C.hours.open.replace(':00','')+' Uhr';
const img=(n,alt,eager)=>`<img src="assets/img/${n}.svg" width="600" height="400" alt="${alt}" loading="${eager?'eager':'lazy'}" decoding="async"${eager?' fetchpriority="high"':''}>`;
const tag=t=>t?`<span class="tag">${t}</span>`:'';
const item=([n,d,p,t])=>`<div class="it"><h3>${n}${tag(t)}</h3><span class="pr">${p}</span>${d?`<p>${d}</p>`:''}</div>`;
const place=`${C.street}, ${C.zip} ${C.city}`;
const ld={"@context":"https://schema.org","@type":["Restaurant","Pizzeria"],"name":C.name,"url":C.base+"/","telephone":"+"+C.whatsapp.replace(/^\+/,''),"acceptsReservations":"True","servesCuisine":"Italienisch","address":{"@type":"PostalAddress","streetAddress":C.street,"postalCode":C.zip,"addressLocality":C.city,"addressCountry":"DE"}};
const html=`<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${C.name} ${C.city} | Tisch reservieren und Speisekarte</title>
<meta name="description" content="${C.name} in der ${C.city}er ${C.district}: Pizza, Pasta und Flammkuchen. Tisch in wenigen Sekunden reservieren, Speisekarte ansehen, Handpizza mitnehmen.">
<meta name="robots" content="${C.indexable?'index,follow,max-image-preview:large':'noindex,follow'}"><link rel="canonical" href="${C.base}/"><meta name="theme-color" content="#CD212A"><meta name="color-scheme" content="light">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/anton.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="assets/fonts/instrument.woff2" as="font" type="font/woff2" crossorigin>
<style>${css}</style><script type="application/ld+json">${JSON.stringify(ld)}</script></head><body>
<a class="skip" href="#main">Zum Inhalt springen</a>
<header class="top"><div class="tape"></div><div class="w bar"><a class="logo" href="#">${C.name}</a><nav aria-label="Hauptnavigation"><a href="#karte">Speisekarte</a><a href="#mitnehmen">Mitnehmen</a><a href="#kontakt">Anfahrt</a><a class="tel" href="tel:${C.phoneHref}">${C.phone}</a><a class="btn sm" href="#reservieren">Tisch reservieren</a></nav></div></header>
<main id="main">
<section class="w hero"><div><p class="status" id="status">${C.hours.text}</p>
<h1>${C.headline.map((l,i)=>`<span${i===C.highlight?' class="hl"':''}>${l}</span>`).join('')}</h1>
<p class="lead">${C.lead}</p></div>
<div class="photo">${img(C.hero.img,C.hero.alt,true)}<div class="sticker" aria-hidden="true"><div><b>${C.hero.stickerPrice}</b>${C.hero.stickerName}</div></div></div></section>

<section class="w resw" id="reservieren" aria-label="Tisch reservieren"><form id="rf" name="reservierung" method="POST" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="reservierung"><p class="hp" aria-hidden="true"><label>Nicht ausfüllen<input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
<div class="rrow"><strong class="rt">Tisch reservieren</strong>
<label class="f">Tag<select name="datum" id="fd" required></select></label>
<label class="f">Uhrzeit<select name="zeit" id="fz" required></select></label>
<label class="f">Personen<select name="personen" id="fp" required></select></label>
<button class="btn sm" type="button" id="next">Weiter</button></div>
<div class="rmore" id="more" hidden><label class="f">Name<input class="t" type="text" name="name" autocomplete="name" required></label><label class="f">Telefon<input class="t" type="tel" name="telefon" autocomplete="tel" required></label>
<button class="btn sm" type="submit">Anfrage senden</button>
<label class="chk"><input type="checkbox" name="datenschutz" required><span>Ich stimme der Verarbeitung meiner Angaben zur Reservierung zu (<a href="datenschutz.html">Datenschutz</a>).</span></label>
<a class="wa" id="wa" href="https://wa.me/${C.whatsapp}" rel="noopener">Lieber per WhatsApp</a></div>
<p class="msg" id="msg" role="status" aria-live="polite"></p></form></section>

<section class="menuwrap" id="karte"><nav class="nav2" aria-label="Kategorien"><span class="nt">Speisekarte</span>${C.menu.map(m=>`<a href="#${m.id}">${m.title}</a>`).join('')}</nav>
<div class="w">${C.menu.map((m,i)=>`<section class="cat" id="${m.id}"><div class="cimg"><h2>${m.title}</h2>${img(m.img,m.alt)}<p>${m.note}</p></div><div class="list">${m.items.map(item).join('')}</div></section>`).join('')}<p class="foot-note">Preise nach Stand März 2024, Änderungen vorbehalten. Bei Allergien fragen Sie bitte das Team.</p></div></section>

<section class="take" id="mitnehmen"><div class="w grid"><div><h2>Pizza<br>zum Mitnehmen</h2><p>Handpizza und Pizza vom Blech direkt am Straßenfenster. Ab 4 Euro, schnell und warm.</p><a class="btn" href="tel:${C.phoneHref}">${C.phone}</a></div><div>${img('fenster','Illustration: Straßenfenster mit grün-weiß-roter Markise')}</div></div></section>

<section class="w info" id="kontakt"><div><h3>Anfahrt</h3><address>${C.name}<br>${C.street}<br>${C.zip} ${C.city}<br><a href="tel:${C.phoneHref}">${C.phone}</a></address><p><a href="https://www.google.com/maps/search/?api=1&amp;query=${encodeURIComponent(C.name+' '+place)}" target="_blank" rel="noopener">Route in Google Maps</a></p></div>
<div><h3>Öffnungszeiten</h3><table><caption class="sr" style="position:absolute;left:-999px">Öffnungszeiten</caption><tr><th scope="row">Mo–Sa</th><td>${C.hours.open} – ${C.hours.close}</td></tr><tr><th scope="row">${C.hours.closedDay}</th><td>Ruhetag</td></tr></table></div>
<div><h3>Gut zu wissen</h3>${C.faq.map(([q,a])=>`<details><summary>${q}</summary><p>${a}</p></details>`).join('')}</div></section>
</main>
<footer><div class="tape"></div><div class="w" style="padding-top:22px"><span>${C.name} · ${place}</span><span><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></span></div></footer>
<div class="dock"><a class="btn" href="#reservieren">Reservieren</a><a class="btn alt" href="tel:${C.phoneHref}">Anrufen</a></div>
<script>window.RES_CFG=${JSON.stringify(cfg)};${js}</script>
</body></html>`;
fs.writeFileSync(path.join(here,'../../site/gastro.html'),html);
console.log('gebaut: site/gastro.html',html.length,'Bytes');
