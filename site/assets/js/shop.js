(function(){
'use strict';
var $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
var eur=function(n){return Number(n).toLocaleString('de-DE',{style:'currency',currency:'EUR'})};
var KEY='ic24_cart_v2', q=new URLSearchParams(location.search);
function cart(){try{return JSON.parse(localStorage.getItem(KEY))||[]}catch(e){return []}}
function saveCart(c){try{localStorage.setItem(KEY,JSON.stringify(c))}catch(e){}$$('[data-cart-badge]').forEach(function(b){var n=c.reduce(function(a,l){return a+l.q},0);b.textContent=n||'';b.setAttribute('data-n',n)})}
function api(path,opt){opt=opt||{};var h={'X-Requested-With':'ic'};if(opt.body)h['Content-Type']='application/json';
  return fetch(path,{method:opt.method||'GET',headers:h,body:opt.body?JSON.stringify(opt.body):undefined,credentials:'same-origin'}).then(function(r){return r.json().catch(function(){return {}}).then(function(j){if(!r.ok){var e=new Error(j.error||'Fehler');e.status=r.status;e.data=j;throw e}return j})})}
function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
function fv(id){var e=document.getElementById(id);return e?(e.type==='checkbox'?e.checked:e.value.trim()):''}
function fset(id,v){var e=document.getElementById(id);if(e&&v!=null)e.value=v}
function valid(f){var ok=true;$$('[required]',f).forEach(function(x){if(x.closest('[hidden]'))return;var bad=!x.checkValidity();x.classList.toggle('invalid',bad);if(bad&&ok){x.focus();ok=false}});return ok}

/* ============ KASSE ============ */
var ck=$('#checkout');
if(ck){
  var state={quote:null,coupon:'',user:null};
  if(location.protocol==='file:'){$('#offline').hidden=false}
  var items=cart();
  if(!items.length){ck.hidden=true;$('#cohint').hidden=false;$('.summary').hidden=true}
  else{
    var PAYINFO={paypal:['PayPal','Zahlen Sie sicher mit Ihrem PayPal-Konto (inkl. Kreditkarte, Lastschrift).'],card:['Kreditkarte, Apple Pay, Google Pay','Sicher bezahlen über Stripe – Visa, Mastercard, American Express, Apple Pay, Google Pay.'],transfer:['Überweisung (Vorkasse)','Versand nach Zahlungseingang. Bankdaten erhalten Sie nach der Bestellung.'],invoice:['Rechnung','Zahlbar innerhalb von 14 Tagen nach Rechnungsstellung – nach kurzer Prüfung Ihrer Bestellung.']};
    function country(){return fv('diffship')?fv('s-country'):fv('b-country')}
    function quote(){
      return api('/api/cart/quote',{method:'POST',body:{items:cart().map(function(l){return {sku:l.sku,qty:l.q}}),coupon:state.coupon,country:country()}}).then(function(q){state.quote=q;render(q)}).catch(function(e){
        if(e.status===409&&e.data&&e.data.sku){saveCart(cart().filter(function(l){return l.sku!==e.data.sku}));alert('Ein Artikel ist nicht mehr verfügbar und wurde aus dem Warenkorb entfernt.');if(!cart().length)location.href='warenkorb.html';else quote()}
        else if(state.coupon&&e.status===400){state.coupon='';$('#cpmsg').textContent=e.message;$('#cpmsg').hidden=false;quote()}else{$('#cerr').textContent=e.message;$('#cerr').hidden=false}})}
    function render(q){
      var ol=$('#orderlines');ol.innerHTML='';
      q.lines.forEach(function(l){var d=el('div','ol');var s=el('span',null,l.qty+' × '+l.name);var b=el('strong',null,eur(l.price*l.qty));d.appendChild(s);d.appendChild(b);ol.appendChild(d)});
      $('#o-sub').textContent=eur(q.subtotal);$('#o-disc-row').hidden=!q.discount;$('#o-disc').textContent='−'+eur(q.discount);$('#o-ship').textContent=q.shipping_cost?eur(q.shipping_cost):'kostenlos';$('#o-vat').textContent=eur(q.vat);$('#o-tot').textContent=eur(q.total);
      var pm=$('#paymethods'),cur=($('input[name=pay]:checked')||{}).value;pm.innerHTML='';
      ['paypal','card','transfer','invoice'].forEach(function(k){if(!q.methods[k])return;var lab=el('label','pay'),inp=document.createElement('input');inp.type='radio';inp.name='pay';inp.value=k;inp.required=true;if(cur===k)inp.checked=true;
        var box=el('span','pb');box.appendChild(el('strong',null,PAYINFO[k][0]));box.appendChild(el('small',null,PAYINFO[k][1]));lab.appendChild(inp);lab.appendChild(box);pm.appendChild(lab)});
      if(!pm.children.length)pm.appendChild(el('p','notice','Derzeit ist keine Zahlart verfügbar – bitte rufen Sie uns an.'));
      var first=$('input[name=pay]',pm);if(first&&!$('input[name=pay]:checked'))first.checked=true;
      var btn=$('#placeorder');btn.lastChild.textContent=' Zahlungspflichtig bestellen · '+eur(q.total)}
    api('/api/me').then(function(r){state.user=r.user;if(r.user){var u=r.user,a=(u.addr||{}).billing||{};fset('c-email',u.email);fset('c-phone',u.phone);fset('b-first',a.first||u.first);fset('b-last',a.last||u.last);['company','street','zip','city'].forEach(function(k){fset('b-'+k,a[k])});if(a.country)fset('b-country',a.country);$('#accbox').hidden=true}else{$('#loginhint').hidden=false}}).catch(function(){}).then(quote);
    $('#diffship').addEventListener('change',function(){$('#shipbox').hidden=!this.checked;$$('#shipbox [data-r]').forEach(function(x){x.required=this.checked},this)});
    var sreq=['first','last','street','zip','city'].map(function(k){return document.getElementById('s-'+k)});$('#diffship').addEventListener('change',function(){var on=this.checked;sreq.forEach(function(x){x.required=on})});
    $('#mkacc').addEventListener('change',function(){$('#pwbox').hidden=!this.checked;$('#pw').required=this.checked});
    ['b-country','s-country'].forEach(function(id){document.getElementById(id).addEventListener('change',quote)});$('#diffship').addEventListener('change',quote);
    $('#applycoupon').addEventListener('click',function(){state.coupon=fv('coupon');$('#cpmsg').hidden=true;quote().then(function(){if(state.coupon&&state.quote&&state.quote.discount){$('#cpmsg').textContent='Gutschein angewendet.';$('#cpmsg').hidden=false}})});
    $$('#checkout input,#checkout select').forEach(function(f){f.addEventListener('blur',function(){if(f.required&&!f.closest('[hidden]'))f.classList.toggle('invalid',!f.checkValidity())})});
    function addr(p){return {first:fv(p+'first'),last:fv(p+'last'),company:fv(p+'company'),street:fv(p+'street'),zip:fv(p+'zip'),city:fv(p+'city'),country:fv(p+'country')}}
    ck.addEventListener('submit',function(e){e.preventDefault();$('#cerr').hidden=true;if(location.protocol==='file:'){$('#offline').hidden=false;return}
      if(!valid(ck))return;var pay=($('input[name=pay]:checked')||{}).value;if(!pay){$('#cerr').textContent='Bitte eine Zahlart wählen.';$('#cerr').hidden=false;return}
      var btn=$('#placeorder');btn.disabled=true;
      var body={items:cart().map(function(l){return {sku:l.sku,qty:l.q}}),coupon:state.coupon,payment:pay,accept:fv('accept'),customer:{email:fv('c-email'),phone:fv('c-phone'),first:fv('b-first'),last:fv('b-last')},billing:addr('b-'),sameShipping:!fv('diffship'),shipping:fv('diffship')?addr('s-'):null,vehicle:fv('vehicle'),note:fv('note'),createAccount:fv('mkacc'),password:fv('pw')};
      api('/api/checkout',{method:'POST',body:body}).then(function(r){if(pay==='transfer'||pay==='invoice')saveCart([]);else try{sessionStorage.setItem('ic24_pending',r.number)}catch(e){}location.href=r.redirect}).catch(function(err){btn.disabled=false;$('#cerr').textContent=err.message;$('#cerr').hidden=false;$('#cerr').scrollIntoView({behavior:'smooth',block:'center'})})});
  }
}

/* ============ BESTELLSTATUS ============ */
var ov=$('#oview');
if(ov){
  var n=q.get('n'),t=q.get('t'),tries=0;
  var STEPS=['neu','bezahlt','in_bearbeitung','versendet'];
  function addrTxt(a){return [a.first+' '+a.last,a.company,a.street,a.zip+' '+a.city,a.country==='AT'?'Österreich':'Deutschland'].filter(Boolean).join('\n')}
  function show(o){
    ov.innerHTML='';var paid=o.payment_status==='bezahlt',head=$('#ohead'),sub=$('#osub');
    if(q.get('cancel')&&!paid&&['card','paypal'].indexOf(o.payment_method)>-1){head.textContent='Zahlung abgebrochen';sub.textContent='Ihre Bestellung '+o.number+' wurde noch nicht bezahlt.';
      var box=el('div','notice');box.appendChild(el('p',null,'Sie haben die Zahlung abgebrochen. Ihre Artikel liegen weiterhin im Warenkorb – Sie können die Bestellung mit einer anderen Zahlart erneut aufgeben.'));var a=el('a','btn btn-cta btn-lg','Zurück zur Kasse');a.href='kasse.html';box.appendChild(a);ov.appendChild(box);
      if(t)api('/api/order/'+encodeURIComponent(n)+'/cancel?t='+encodeURIComponent(t),{method:'POST',body:{}}).catch(function(){});return}
    head.textContent=paid?'Vielen Dank – Zahlung erhalten!':'Vielen Dank für Ihre Bestellung!';sub.textContent='Bestellnummer '+o.number+' · '+o.statusText;
    if(paid||o.payment_method==='transfer'||o.payment_method==='invoice'){saveCart([]);try{sessionStorage.removeItem('ic24_pending')}catch(e){}}
    var g=el('div','ogrid');var main=el('div');var side=el('aside','summary');
    if(!paid&&['card','paypal'].indexOf(o.payment_method)>-1){main.appendChild(el('p','notice','Wir warten noch auf die Bestätigung Ihrer Zahlung. Diese Seite aktualisiert sich automatisch.'))}
    if(o.bank&&!paid){var b=el('div','notice-box');b.appendChild(el('h3',null,o.payment_method==='invoice'?'Zahlung nach Rechnungserhalt':'Bitte überweisen Sie '+eur(o.total)));
      var pp=el('p',null,o.bank.iban?'Empfänger: '+o.bank.holder+'\nBank: '+o.bank.name+'\nIBAN: '+o.bank.iban+(o.bank.bic?'\nBIC: '+o.bank.bic:'')+'\nVerwendungszweck: '+o.number:'Unsere Bankverbindung senden wir Ihnen per E-Mail zu.');pp.style.whiteSpace='pre-line';b.appendChild(pp);main.appendChild(b)}
    var tl=el('ol','tl');[['Bestellt','neu'],['Bezahlt','bezahlt'],['In Bearbeitung','in_bearbeitung'],['Versendet','versendet']].forEach(function(s,i){var li=el('li',null,s[0]);var idx=STEPS.indexOf(o.status);if(o.status==='wartet_auf_zahlung'||o.status==='pruefung')idx=0;if(paid&&idx<1)idx=1;if(i<=idx)li.className='on';tl.appendChild(li)});main.appendChild(tl);
    if(o.tracking){main.appendChild(el('p',null,'Sendungsnummer'+(o.carrier?' ('+o.carrier+')':'')+': '+o.tracking))}
    var h=el('h2',null,'Bestellte Artikel');main.appendChild(h);o.items.forEach(function(i){var d=el('div','ol');d.appendChild(el('span',null,i.qty+' × '+i.name));d.appendChild(el('strong',null,eur(i.price*i.qty)));main.appendChild(d)});
    side.appendChild(el('h2',null,'Zusammenfassung'));[['Zwischensumme',eur(o.subtotal)],o.discount?['Rabatt','−'+eur(o.discount)]:null,['Versand',o.shipping_cost?eur(o.shipping_cost):'kostenlos'],['darin MwSt. 19 %',eur(o.vat)]].forEach(function(r){if(!r)return;var d=el('div','ol');d.appendChild(el('span',null,r[0]));d.appendChild(el('strong',null,r[1]));side.appendChild(d)});
    var tot=el('div','ol total');tot.appendChild(el('span',null,'Gesamt'));tot.appendChild(el('strong',null,eur(o.total)));side.appendChild(tot);
    side.appendChild(el('p','small','Zahlart: '+o.payment+' · '+(paid?'bezahlt':o.payment_status)));
    var pre=el('pre','addr');pre.textContent='Rechnungsadresse\n'+addrTxt(o.billing)+'\n\nLieferadresse\n'+addrTxt(o.shipping);side.appendChild(pre);
    if(paid||o.payment_method==='invoice'){var a=el('a','btn btn-out btn-block','Rechnung als PDF');a.href='/api/order/'+encodeURIComponent(o.number)+'/invoice.pdf'+(t?'?t='+encodeURIComponent(t):'');a.target='_blank';a.rel='noopener';side.appendChild(a)}
    g.appendChild(main);g.appendChild(side);ov.appendChild(g)}
  function load(){api('/api/order/'+encodeURIComponent(n)+'?'+(t?'t='+encodeURIComponent(t):'')+(q.get('paid')?'&paid=1':'')).then(function(o){show(o);if(q.get('paid')&&o.payment_status!=='bezahlt'&&++tries<8)setTimeout(load,2500)}).catch(function(e){ov.innerHTML='';var p=el('p','notice',e.message||'Bestellung nicht gefunden.');ov.appendChild(p);var a=el('a','btn btn-cta','Zum Kundenkonto');a.href='konto.html';ov.appendChild(a)})}
  if(!n){ov.innerHTML='<p class="notice">Keine Bestellung angegeben.</p>'}else load();
}

/* ============ KONTO ============ */
var acc=$('#acc');
if(acc){
  function loginView(){
    acc.innerHTML='';var g=el('div','split');
    var f1=el('form');f1.noValidate=true;f1.innerHTML='<h2>Anmelden</h2><label for="li-e">E-Mail</label><input id="li-e" type="email" required autocomplete="email"><div class="err">Bitte E-Mail angeben.</div><label for="li-p">Passwort</label><input id="li-p" type="password" required autocomplete="current-password"><div class="err">Bitte Passwort angeben.</div><p class="small"><a href="passwort-vergessen.html">Passwort vergessen?</a></p><p class="notice" hidden role="alert"></p><button class="btn btn-cta btn-lg btn-block">Anmelden</button>';
    var f2=el('form');f2.noValidate=true;f2.innerHTML='<h2>Neues Konto</h2><div class="form-grid"><div><label for="rg-f">Vorname</label><input id="rg-f" autocomplete="given-name"></div><div><label for="rg-l">Nachname</label><input id="rg-l" autocomplete="family-name"></div></div><label for="rg-e">E-Mail</label><input id="rg-e" type="email" required autocomplete="email"><div class="err">Bitte E-Mail angeben.</div><label for="rg-p">Passwort (mind. 8 Zeichen)</label><input id="rg-p" type="password" required minlength="8" autocomplete="new-password"><div class="err">Mindestens 8 Zeichen.</div><p class="small">Mit der Registrierung stimmen Sie der <a href="datenschutz.html">Datenschutzerklärung</a> zu.</p><p class="notice" hidden role="alert"></p><button class="btn btn-pri btn-lg btn-block">Konto erstellen</button>';
    function done(){var nx=q.get('next');if(nx==='kasse')location.href='kasse.html';else start()}
    f1.addEventListener('submit',function(e){e.preventDefault();if(!valid(f1))return;var m=$('.notice',f1);m.hidden=true;api('/api/login',{method:'POST',body:{email:fv('li-e'),password:document.getElementById('li-p').value}}).then(done).catch(function(er){m.textContent=er.message;m.hidden=false})});
    f2.addEventListener('submit',function(e){e.preventDefault();if(!valid(f2))return;var m=$('.notice',f2);m.hidden=true;api('/api/register',{method:'POST',body:{first:fv('rg-f'),last:fv('rg-l'),email:fv('rg-e'),password:document.getElementById('rg-p').value}}).then(done).catch(function(er){m.textContent=er.message;m.hidden=false})});
    g.appendChild(f1);g.appendChild(f2);acc.appendChild(g)}
  function dash(u){
    acc.innerHTML='';var top=el('div','sec-head');top.appendChild(el('h2',null,'Hallo '+(u.first||u.email)+'!'));var lo=el('button','btn btn-out','Abmelden');lo.addEventListener('click',function(){api('/api/logout',{method:'POST',body:{}}).then(function(){loginView()})});top.appendChild(lo);acc.appendChild(top);
    if(u.is_admin){var ad=el('p','notice-box');var a=el('a',null,'Zum Admin-Bereich');a.href='admin/';ad.appendChild(a);acc.appendChild(ad)}
    acc.appendChild(el('h3',null,'Meine Bestellungen'));var ol=el('div','tscroll');acc.appendChild(ol);
    api('/api/me/orders').then(function(r){if(!r.orders.length){ol.appendChild(el('p','small','Noch keine Bestellungen.'));return}
      var tb=document.createElement('table');tb.className='spec';r.orders.forEach(function(o){var tr=document.createElement('tr');var td=function(x){var c=document.createElement('td');c.textContent=x;tr.appendChild(c);return c};td(o.number);td(new Date(o.created_at).toLocaleDateString('de-DE'));td(o.statusText);td(eur(o.total)).className='r';var c=document.createElement('td');c.className='r';var a=el('a',null,'Ansehen');a.href='bestellung.html?n='+encodeURIComponent(o.number);c.appendChild(a);tr.appendChild(c);tb.appendChild(tr)});ol.appendChild(tb)});
    var f=el('form');f.noValidate=true;var A=(u.addr||{}).billing||{};
    f.innerHTML='<h3 style="margin-top:32px">Meine Daten</h3><div class="form-grid"><div><label for="p-f">Vorname</label><input id="p-f"></div><div><label for="p-l">Nachname</label><input id="p-l"></div><div><label for="p-t">Telefon</label><input id="p-t" type="tel"></div><div><label>E-Mail</label><input value="" id="p-e" disabled></div><div class="full"><label for="p-s">Straße &amp; Nr.</label><input id="p-s"></div><div><label for="p-z">PLZ</label><input id="p-z"></div><div><label for="p-c">Ort</label><input id="p-c"></div></div><p class="notice ok" hidden>Gespeichert.</p><button class="btn btn-pri">Speichern</button>';
    acc.appendChild(f);fset('p-f',u.first);fset('p-l',u.last);fset('p-t',u.phone);fset('p-e',u.email);fset('p-s',A.street);fset('p-z',A.zip);fset('p-c',A.city);
    f.addEventListener('submit',function(e){e.preventDefault();var b={first:fv('p-f'),last:fv('p-l'),company:'',street:fv('p-s'),zip:fv('p-z'),city:fv('p-c'),country:'DE'};api('/api/me',{method:'PUT',body:{first:fv('p-f'),last:fv('p-l'),phone:fv('p-t'),billing:b,shipping:b}}).then(function(){$('.ok',f).hidden=false})});
    var pw=el('form');pw.noValidate=true;pw.innerHTML='<h3 style="margin-top:32px">Passwort ändern</h3><div class="form-grid"><div><label for="o-p">Aktuelles Passwort</label><input id="o-p" type="password" autocomplete="current-password" required></div><div><label for="n-p">Neues Passwort</label><input id="n-p" type="password" autocomplete="new-password" minlength="8" required></div></div><p class="notice" hidden role="alert"></p><button class="btn btn-out">Passwort ändern</button>';
    acc.appendChild(pw);pw.addEventListener('submit',function(e){e.preventDefault();if(!valid(pw))return;var m=$('.notice',pw);api('/api/me/password',{method:'POST',body:{old:document.getElementById('o-p').value,password:document.getElementById('n-p').value}}).then(function(){m.className='notice ok';m.textContent='Passwort geändert.';m.hidden=false;pw.reset()}).catch(function(er){m.className='notice';m.textContent=er.message;m.hidden=false})})}
  function start(){if(location.protocol==='file:'){acc.innerHTML='<p class="notice">Das Kundenkonto ist nur über den Shop-Server verfügbar.</p>';return}api('/api/me').then(function(r){r.user?dash(r.user):loginView()}).catch(function(){acc.innerHTML='<p class="notice">Der Shop-Server ist nicht erreichbar.</p>'})}
  start();
}
/* ============ PASSWORT ============ */
var fg=$('#forgot');if(fg)fg.addEventListener('submit',function(e){e.preventDefault();if(!valid(fg))return;api('/api/password/forgot',{method:'POST',body:{email:fv('fe')}}).then(function(){$('#fmsg').hidden=false})});
var rs=$('#reset');if(rs)rs.addEventListener('submit',function(e){e.preventDefault();if(!valid(rs))return;var m=$('#rmsg');api('/api/password/reset',{method:'POST',body:{token:q.get('t'),password:document.getElementById('rp').value}}).then(function(){m.className='notice ok';m.innerHTML='Passwort geändert. <a href="konto.html">Jetzt anmelden</a>';m.hidden=false}).catch(function(er){m.className='notice';m.textContent=er.message;m.hidden=false})});
})();
