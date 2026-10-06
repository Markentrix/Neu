(function(){
'use strict';
var KEY='ic24_cart_v2', IDX=window.IC_IDX||{p:[],m:[],s:{},h:[],c:[]};
var $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
var eur=function(n){return Number(n).toLocaleString('de-DE',{style:'currency',currency:'EUR'})};
var norm=function(s){return (s||'').toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,' ').trim()};
function load(){try{return JSON.parse(localStorage.getItem(KEY))||[]}catch(e){return []}}
function save(c){try{localStorage.setItem(KEY,JSON.stringify(c))}catch(e){}badge()}
function count(){return load().reduce(function(a,l){return a+l.q},0)}
function badge(){$$('[data-cart-badge]').forEach(function(b){var n=count();b.textContent=n||'';b.setAttribute('data-n',n)})}
function toast(msg,link){var t=$('#toast');if(!t)return;t.innerHTML='<span></span>'+(link?'<a href="'+link.h+'">'+link.t+'</a>':'');t.firstChild.textContent=msg;t.classList.add('on');clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove('on')},4200)}
function add(it,q){var c=load(),l=c.filter(function(x){return x.sku===it.sku})[0];if(l)l.q=Math.min(l.q+q,20);else{it.q=q;c.push(it)}save(c);toast(it.name+' im Warenkorb',{h:'warenkorb.html',t:'Zum Warenkorb'})}
function item(b){return {sku:b.getAttribute('data-sku'),name:b.getAttribute('data-name'),price:parseFloat(b.getAttribute('data-price')),img:b.getAttribute('data-img')||'',url:b.getAttribute('data-url')||''}}

/* Warenkorb: Schnell-Hinzufügen */
document.addEventListener('click',function(e){var b=e.target.closest('[data-add]');if(!b)return;e.preventDefault();add(item(b),1)});
/* Qty */
$$('.qty').forEach(function(w){var i=$('input',w);if(!i||i.readOnly)return;w.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var v=parseInt(i.value,10)||1;v+=b.getAttribute('data-d')==='+'?1:-1;i.value=Math.min(20,Math.max(1,v))})});

/* Produktseite: Variante, Montage, Kauf */
var bb=$('[data-buy]');
if(bb){
  var vs=$('#variant'),pp=$('#pprice'),mon=$('#mont'),mv=$('#mont-v');
  var base=parseFloat(bb.getAttribute('data-base'))||0;
  function cur(){return vs?parseFloat(vs.options[vs.selectedIndex].getAttribute('data-price')):base}
  function upd(){if(pp&&vs){pp.innerHTML=eur(cur())}}
  if(vs){vs.addEventListener('change',upd)}
  if(mon&&mv)mon.addEventListener('change',function(){mv.hidden=!mon.checked});
  function buy(){
    var q=Math.max(1,parseInt(($('#qty')||{value:1}).value,10)||1),sku=bb.getAttribute('data-sku'),nm=bb.getAttribute('data-name');
    if(vs){sku+='~v'+vs.value;nm+=' – '+vs.options[vs.selectedIndex].text.replace(/\s–\s[\d\.]+,\d{2}\s€$/,'')}
    var it={sku:sku,name:nm,price:cur(),img:bb.getAttribute('data-img'),url:bb.getAttribute('data-url')};
    var c=load(),l=c.filter(function(x){return x.sku===sku})[0];if(l)l.q=Math.min(l.q+q,20);else{it.q=q;c.push(it)}
    if(mon&&mon.checked){var ms=bb.getAttribute('data-sku')+'~m'+mv.value,mp=parseFloat(mv.options[mv.selectedIndex].getAttribute('data-price'))||parseFloat(mon.getAttribute('data-mprice')),ml=c.filter(function(x){return x.sku===ms})[0];
      var mname='Montage: '+bb.getAttribute('data-name')+(mv.options[mv.selectedIndex]?' – '+mv.options[mv.selectedIndex].text:'');
      if(ml)ml.q=Math.min(ml.q+q,20);else c.push({sku:ms,name:mname,price:mp,img:'',url:bb.getAttribute('data-url'),q:q})}
    save(c);toast(nm+' im Warenkorb',{h:'warenkorb.html',t:'Zum Warenkorb'})}
  var b1=$('#buy'),b2=$('#buy2');if(b1)b1.addEventListener('click',buy);if(b2)b2.addEventListener('click',buy);
}
/* Galerie */
var gm=$('#gmain');
$$('.thumbs button').forEach(function(b){b.addEventListener('click',function(){var m=$('img',gm);m.removeAttribute('srcset');m.removeAttribute('sizes');m.src=b.getAttribute('data-big');m.alt=$('img',b).alt;$$('.thumbs button').forEach(function(x){x.removeAttribute('aria-current')});b.setAttribute('aria-current','true')})});

/* Menü */
var mb=$('#menuBtn'),nav=$('#nav');
if(mb&&nav)mb.addEventListener('click',function(){var o=nav.classList.toggle('open');mb.setAttribute('aria-expanded',o)});
document.addEventListener('click',function(e){$$('.dd details[open]').forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open')})});

/* Produkt-Suche (Index) */
function findP(q,max){
  var t=norm(q).split(' ').filter(Boolean);if(!t.length)return [];
  var out=[];
  IDX.p.forEach(function(r){var hay=norm(r[1]+' '+(r[8]||'')+' '+r[6].join(' ')+' '+(IDX.c[r[2]]||[])[1]);var ok=t.every(function(w){return hay.indexOf(w)>-1});if(ok)out.push(r)});
  return max?out.slice(0,max):out;
}
function cardJS(r){
  var im=r[5]?'<img class="photo" src="assets/img/p/'+r[5]+'-360.webp" width="360" height="360" alt="" loading="lazy">':'<div class="noimg"></div>';
  var pr=r[3]?'<div class="price">'+(r[4]?'<span class="from">ab</span> ':'')+eur(r[3])+'<small>inkl. MwSt., versandkostenfrei</small></div>':'<div class="price ask">Preis auf Anfrage</div>';
  return '<article class="card"><div class="art">'+im+'</div><div class="body"><h3><a href="produkt-'+r[0]+'.html"></a></h3>'+pr+'<div class="foot"><a class="btn btn-out btn-block" href="produkt-'+r[0]+'.html">Ansehen</a></div></div></article>'}
var si=$('#q'),sl=$('#suggest');
if(si&&sl){
  si.addEventListener('input',function(){
    var v=si.value.trim();if(v.length<2){sl.classList.remove('on');sl.innerHTML='';return}
    var hits=findP(v,6);sl.innerHTML='';
    hits.forEach(function(r){var li=document.createElement('li'),a=document.createElement('a');a.href='produkt-'+r[0]+'.html';var s1=document.createElement('span');s1.textContent=r[1];var s2=document.createElement('small');s2.textContent=r[3]?eur(r[3]):'Anfrage';a.appendChild(s1);a.appendChild(s2);li.appendChild(a);sl.appendChild(li)});
    var li=document.createElement('li'),a=document.createElement('a');a.href='suche.html?q='+encodeURIComponent(v);a.innerHTML='<strong>Alle Treffer anzeigen</strong>';li.appendChild(a);sl.appendChild(li);sl.classList.add('on')});
  document.addEventListener('click',function(e){if(!e.target.closest('.search'))sl.classList.remove('on')});
}
var sres=$('#sres');
if(sres){
  var q=new URLSearchParams(location.search).get('q')||'';var qi=$('#q2');if(qi)qi.value=q;
  var hits=q?findP(q):[];$('#sh').textContent=q?'Suche: „'+q+'“':'Suche';$('#sq').textContent=q?hits.length+' Treffer':'Geben Sie einen Suchbegriff ein.';
  sres.innerHTML=hits.slice(0,60).map(cardJS).join('');$$('.card h3 a',sres).forEach(function(a,i){a.textContent=hits[i][1]});
  if(q&&!hits.length)$('#snone').hidden=false;
}

/* Fahrzeugfinder */
$$('[data-finder]').forEach(function(box){
  var tabs=$$('[data-tab]',box),panes=$$('[data-pane]',box);
  tabs.forEach(function(t){t.addEventListener('click',function(){tabs.forEach(function(x){x.setAttribute('aria-selected',x===t)});panes.forEach(function(p){p.hidden=p.getAttribute('data-pane')!==t.getAttribute('data-tab')})})});
  var mk=$('#f-make',box),sr=$('#f-series',box),br=$('#f-brand',box),md=$('#f-model',box);
  function grp(k){var m=IDX.m.filter(function(x){return x[0]===k})[0];return m&&m[2]}
  mk.addEventListener('change',function(){mk.classList.remove('invalid');var g=grp(mk.value),L=(IDX.s[g]||[]);sr.innerHTML='<option value="">Alle Baureihen</option>'+L.map(function(s){return '<option value="'+s[0]+'">'+s[1]+' · '+s[2]+'</option>'}).join('');sr.disabled=!mk.value});
  $('[data-pane=base]',box).addEventListener('submit',function(e){e.preventDefault();if(!mk.value){mk.classList.add('invalid');mk.focus();return}location.href='fahrzeug-'+mk.value+(sr.value?'-'+sr.value:'')+'.html'});
  br.addEventListener('change',function(){br.classList.remove('invalid');var h=IDX.h.filter(function(x){return x[0]===br.value})[0];md.innerHTML='<option value="">Alle Modelle ansehen</option>'+(h?h[2].map(function(m){return '<option value="'+m[0]+'">'+m[1]+'</option>'}).join(''):'');md.disabled=!h});
  $('[data-pane=coach]',box).addEventListener('submit',function(e){e.preventDefault();if(!br.value){br.classList.add('invalid');br.focus();return}location.href=md.value?'produkt-'+md.value+'.html':'hersteller-'+br.value+'.html'});
});

/* Kategorie: Filter, Sortierung, Mehr laden */
var gr=$('#prodgrid');
if(gr){
  var cards=$$('.card',gr),STEP=24,shown=STEP,fk='all',fm='',fq='',so=$('#sort'),more=$('#more'),cnt=$('#count'),nr=$('#noresult'),fqi=$('#fq'),fmi=$('#fm');
  if(!more)STEP=9999;
  function apply(){
    var vis=cards.filter(function(c){return (fk==='all'||c.getAttribute('data-k')===fk)&&(!fm||(' '+c.getAttribute('data-m')+' ').indexOf(' '+fm+' ')>-1)&&(!fq||norm(c.getAttribute('data-q')).indexOf(fq)>-1)});
    cards.forEach(function(c){c.hidden=true});
    vis.slice(0,shown).forEach(function(c){c.hidden=false});
    if(cnt)cnt.textContent=vis.length+' Artikel';if(nr)nr.hidden=vis.length>0;
    if(more){more.hidden=vis.length<=shown;more.textContent='Mehr Artikel anzeigen ('+Math.max(0,vis.length-shown)+')'}}
  if(so)so.addEventListener('change',function(){var k=so.value;cards.sort(function(a,b){var pa=+a.dataset.price||1e9,pb=+b.dataset.price||1e9;return k==='asc'?pa-pb:k==='desc'?(+b.dataset.price||0)-(+a.dataset.price||0):+a.dataset.i-+b.dataset.i}).forEach(function(c){gr.appendChild(c)});shown=STEP;apply()});
  $$('.filterbar .chip[data-k]').forEach(function(b){b.addEventListener('click',function(){fk=b.getAttribute('data-k');$$('.filterbar .chip[data-k]').forEach(function(x){x.setAttribute('aria-pressed',x===b)});shown=STEP;apply()})});
  if(fmi)fmi.addEventListener('change',function(){fm=fmi.value;shown=STEP;apply()});
  if(fqi)fqi.addEventListener('input',function(){fq=norm(fqi.value);shown=STEP;apply()});
  if(more)more.addEventListener('click',function(){shown+=STEP;apply()});
  apply();
}
var parts=$('#parts'),pf=$('#fq');
if(parts&&pf)pf.addEventListener('input',function(){var v=norm(pf.value);$$('tr',parts).forEach(function(r){r.hidden=v&&norm(r.getAttribute('data-q')).indexOf(v)<0})});

/* Bewertungen */
var rv=$('#reviews'),rm=$('#rmore');
if(rv&&rm){var rs=$$('.review',rv),n=18;function rshow(){rs.forEach(function(r,i){r.hidden=i>=n});rm.hidden=n>=rs.length}rm.addEventListener('click',function(){n+=24;rshow()});rshow()}

/* Warenkorb-Seite */
var cl=$('#cartlist');
function totals(){return load().reduce(function(a,l){return a+l.price*l.q},0)}
function renderCart(){
  if(!cl)return;var c=load(),sum=$('#sum');
  if(!c.length){cl.innerHTML='<div class="empty"><h2>Ihr Warenkorb ist leer</h2><p>Finden Sie das passende Zubehör für Ihr Fahrzeug.</p><a class="btn btn-cta btn-lg" href="fahrzeugfinder.html">Zum Fahrzeugfinder</a></div>';if(sum)sum.hidden=true;return}
  if(sum)sum.hidden=false;cl.innerHTML='';
  c.forEach(function(l){var r=document.createElement('div');r.className='cart-row';
    r.innerHTML='<div class="thumb"></div><div><h3><a></a></h3><small></small><br><button class="rm" type="button">Entfernen</button></div><div class="qty"><button type="button" data-d="-" aria-label="Menge verringern">−</button><input value="" readonly aria-label="Menge"><button type="button" data-d="+" aria-label="Menge erhöhen">+</button></div><strong></strong>';
    if(l.img){var im=document.createElement('img');im.src=l.img;im.alt='';im.width=80;im.height=80;$('.thumb',r).appendChild(im)}
    var a=$('a',r);a.textContent=l.name;a.href=l.url||'#';$('small',r).textContent=eur(l.price)+' / Stück';$('input',r).value=l.q;$('strong',r).textContent=eur(l.price*l.q);
    $('.rm',r).addEventListener('click',function(){save(load().filter(function(x){return x.sku!==l.sku}));renderCart()});
    $('.qty',r).addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var c2=load(),it=c2.filter(function(x){return x.sku===l.sku})[0];if(!it)return;it.q+=b.getAttribute('data-d')==='+'?1:-1;if(it.q<1)c2=c2.filter(function(x){return x.sku!==l.sku});else it.q=Math.min(it.q,20);save(c2);renderCart()});
    cl.appendChild(r)});
  var t=totals();$('#t-sub').textContent=eur(t);$('#t-tot').textContent=eur(t);$('#t-vat').textContent=eur(t-t/1.19)}
renderCart();badge();

/* Anfrage-/Kontaktformulare: per API, Fallback mailto (Vorschau ohne Server) */
['quoteform','contactform'].forEach(function(id){
  var f=document.getElementById(id);if(!f)return;
  var u=new URLSearchParams(location.search),pr=u.get('produkt');if(pr){var m=$('[name=nachricht]',f);m.value='Ich interessiere mich für: '+pr+'\n\nFahrzeug / Baujahr:\n'}
  function data(){var d={};$$('input,select,textarea',f).forEach(function(x){if(x.name)d[x.name]=x.type==='checkbox'?x.checked:x.value});return d}
  function txt(d){return (d.nachricht||'')+'\n\nProdukt: '+(d.produkt||'-')+'\nFahrzeug: '+(d.fzg||'-')+' '+(d.bj||'')+'\n\n'+d.name+'\n'+d.email+'\n'+(d.tel||'')}
  f.addEventListener('submit',function(e){e.preventDefault();var ok=true;$$('[required]',f).forEach(function(x){var bad=!x.checkValidity();x.classList.toggle('invalid',bad);if(bad&&ok){x.focus();ok=false}});if(!ok)return;
    var d=data(),btn=$('button[type=submit]',f),err=$('#ferr');if(err)err.hidden=true;
    if(location.protocol==='file:'){location.href='mailto:'+window.IC_MAIL+'?subject='+encodeURIComponent('Anfrage italiacamper24.de')+'&body='+encodeURIComponent(txt(d));$('#sent').hidden=false;return}
    btn.disabled=true;
    fetch('/api/forms/'+(id==='contactform'?'kontakt':'angebot'),{method:'POST',headers:{'Content-Type':'application/json','X-Requested-With':'ic'},body:JSON.stringify(d)}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j}})}).then(function(r){
      btn.disabled=false;if(r.ok){$('#sent').hidden=false;f.reset();$('#sent').scrollIntoView({behavior:'smooth',block:'center'})}else if(err){err.textContent=r.j.error||'Fehler beim Senden.';err.hidden=false}}).catch(function(){btn.disabled=false;if(err){err.textContent='Verbindungsfehler – bitte rufen Sie uns an oder nutzen Sie WhatsApp.';err.hidden=false}})});
  var wa=$('#wa-send');if(wa)wa.addEventListener('click',function(){wa.href='https://wa.me/'+window.IC_WA+'?text='+encodeURIComponent(txt(data()))});
});
/* Hinweis zu technisch notwendiger Speicherung (kein Tracking, keine Cookies von Drittanbietern) */
try{if(!localStorage.getItem('ic24_notice')&&location.protocol!=='file:'){var n=document.createElement('div');n.className='cookie';n.setAttribute('role','region');n.setAttribute('aria-label','Hinweis zur Datenspeicherung');
  n.innerHTML='<p>Wir verwenden nur technisch notwendige Speicherung (Warenkorb, Anmeldung). Kein Tracking, keine Werbe-Cookies. <a href="datenschutz.html">Datenschutz</a></p><button class="btn btn-pri btn-sm" type="button">Verstanden</button>';
  $('button',n).addEventListener('click',function(){try{localStorage.setItem('ic24_notice','1')}catch(e){}n.remove()});document.body.appendChild(n)}}catch(e){}
badge();
})();
