(function(){
  'use strict';
  var IC = window.IC || {products:[],pages:[]};
  var KEY='ic24_cart_v1';
  var $=function(s,c){return (c||document).querySelector(s)}, $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};
  var eur=function(n){return n.toLocaleString('de-DE',{style:'currency',currency:'EUR'})};
  function load(){try{return JSON.parse(localStorage.getItem(KEY))||[]}catch(e){return []}}
  function save(c){try{localStorage.setItem(KEY,JSON.stringify(c))}catch(e){}badge()}
  function prod(id){return IC.products.filter(function(p){return p.id===id})[0]}
  function count(){return load().reduce(function(a,l){return a+l.q},0)}
  function badge(){$$('[data-cart-badge]').forEach(function(b){var n=count();b.textContent=n||'';b.setAttribute('data-n',n)})}
  function toast(msg,link){var t=$('#toast');if(!t)return;t.innerHTML='<span>'+msg+'</span>'+(link?'<a href="'+link.h+'">'+link.t+'</a>':'');t.classList.add('on');clearTimeout(toast.t);toast.t=setTimeout(function(){t.classList.remove('on')},4200)}
  function add(id,q){var c=load(),l=c.filter(function(x){return x.id===id})[0];if(l)l.q=Math.min(l.q+q,20);else c.push({id:id,q:q});save(c)}

  /* Add to cart */
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-add]');if(!b)return;e.preventDefault();
    var id=b.getAttribute('data-add'),qi=$('#qty'),q=qi&&b.hasAttribute('data-useqty')?Math.max(1,parseInt(qi.value,10)||1):1;
    add(id,q);var p=prod(id);toast((p?p.name:'Artikel')+' im Warenkorb',{h:'warenkorb.html',t:'Zum Warenkorb'});
  });
  /* Qty stepper */
  $$('.qty').forEach(function(w){var i=$('input',w);w.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var v=parseInt(i.value,10)||1;v+=b.getAttribute('data-d')==='+'?1:-1;i.value=Math.min(20,Math.max(1,v))})});

  /* Gallery */
  var gm=$('#gmain');
  $$('.thumbs button').forEach(function(b){b.addEventListener('click',function(){var im=$('img',b),m=$('img',gm);m.srcset='';m.sizes='';m.src=im.getAttribute('data-big');m.alt=im.alt;$$('.thumbs button').forEach(function(x){x.removeAttribute('aria-current')});b.setAttribute('aria-current','true')})});

  /* Mobile menu */
  var mb=$('#menuBtn'),nav=$('#nav');
  if(mb&&nav)mb.addEventListener('click',function(){var o=nav.classList.toggle('open');mb.setAttribute('aria-expanded',o)});

  /* Search */
  var si=$('#q'),sl=$('#suggest');
  if(si&&sl){
    si.addEventListener('input',function(){
      var v=si.value.trim().toLowerCase();if(v.length<2){sl.classList.remove('on');sl.innerHTML='';return}
      var hits=IC.pages.filter(function(p){return (p.t+' '+p.k).toLowerCase().indexOf(v)>-1}).slice(0,7);
      sl.innerHTML=hits.length?hits.map(function(h){return '<li><a href="'+h.u+'"><span>'+h.t+'</span><small>'+h.c+'</small></a></li>'}).join(''):'<li><a href="kontakt.html"><span>Nichts gefunden – wir beraten Sie persönlich</span><small>Kontakt</small></a></li>';
      sl.classList.add('on')});
    document.addEventListener('click',function(e){if(!e.target.closest('.search'))sl.classList.remove('on')});
    si.form&&si.form.addEventListener('submit',function(e){e.preventDefault();var f=$('a',sl);if(f)location.href=f.getAttribute('href')});
  }

  /* Vehicle finder */
  var vf=$('#finder');
  if(vf)vf.addEventListener('submit',function(e){e.preventDefault();var s=$('select',vf);if(!s.value){s.classList.add('invalid');s.focus();return}location.href='fahrzeug-'+s.value+'.html'});

  /* Sort */
  var so=$('#sort'),gr=$('#prodgrid');
  if(so&&gr)so.addEventListener('change',function(){
    var items=$$('.card',gr),k=so.value;
    items.sort(function(a,b){var pa=+a.dataset.price||1e9,pb=+b.dataset.price||1e9;
      if(k==='asc')return pa-pb;if(k==='desc')return (+b.dataset.price||0)-(+a.dataset.price||0);return +a.dataset.i-+b.dataset.i});
    items.forEach(function(i){gr.appendChild(i)})});

  /* Cart page */
  var cl=$('#cartlist');
  function totals(){var c=load(),s=0;c.forEach(function(l){var p=prod(l.id);if(p&&p.price)s+=p.price*l.q});return s}
  function renderCart(){
    if(!cl)return;var c=load().filter(function(l){var p=prod(l.id);return p&&p.price});
    var sum=$('#sum'),co=$('#tocheckout');
    if(!c.length){cl.innerHTML='<div class="empty"><h2>Ihr Warenkorb ist leer</h2><p>Stöbern Sie in unseren Kategorien oder lassen Sie sich beraten.</p><a class="btn btn-cta" href="index.html#kategorien">Zu den Kategorien</a></div>';if(sum)sum.hidden=true;return}
    if(sum)sum.hidden=false;
    cl.innerHTML=c.map(function(l){var p=prod(l.id);return '<div class="cart-row"><div class="thumb">'+(p.img?'<img src="'+p.img+'" alt="" width="80" height="80">':'<svg class="ico" aria-hidden="true"><use href="#i-'+p.icon+'"/></svg>')+'</div><div><h3><a href="'+p.u+'">'+p.name+'</a></h3><small>'+(p.from?'Preis ab · ':'')+eur(p.price)+' / Stück</small><br><button class="rm" data-rm="'+p.id+'">Entfernen</button></div><div class="qty" data-q="'+p.id+'"><button type="button" data-d="-" aria-label="Menge verringern">−</button><input value="'+l.q+'" readonly aria-label="Menge"><button type="button" data-d="+" aria-label="Menge erhöhen">+</button></div><strong>'+eur(p.price*l.q)+'</strong></div>'}).join('');
    var t=totals();$('#t-sub').textContent=eur(t);$('#t-tot').textContent=eur(t);$('#t-vat').textContent=eur(t-t/1.19);
  }
  document.addEventListener('click',function(e){
    var r=e.target.closest('[data-rm]');if(r){save(load().filter(function(l){return l.id!==r.getAttribute('data-rm')}));renderCart();return}
    var q=e.target.closest('.qty[data-q] button');if(q){var id=q.parentNode.getAttribute('data-q'),c=load(),l=c.filter(function(x){return x.id===id})[0];if(l){l.q+=q.getAttribute('data-d')==='+'?1:-1;if(l.q<1)c=c.filter(function(x){return x.id!==id});l.q=Math.min(l.q,20);save(c);renderCart()}}
  });
  renderCart();badge();

  /* Checkout */
  var ck=$('#checkout');
  if(ck){
    var c=load().filter(function(l){var p=prod(l.id);return p&&p.price});
    var ol=$('#orderlines');
    if(!c.length){ck.hidden=true;$('#cohint').hidden=false}else{
      ol.innerHTML=c.map(function(l){var p=prod(l.id);return '<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0"><span>'+l.q+' × '+p.name+'</span><strong>'+eur(p.price*l.q)+'</strong></div>'}).join('');
      $('#o-tot').textContent=eur(totals());
    }
    ck.addEventListener('submit',function(e){
      e.preventDefault();var ok=true;
      $$('[required]',ck).forEach(function(f){var bad=!f.checkValidity();f.classList.toggle('invalid',bad);if(bad&&ok){f.focus();ok=false}});
      if(!ok)return;
      var d={};$$('input,select,textarea',ck).forEach(function(f){if(f.name)d[f.name]=f.type==='checkbox'?(f.checked?'ja':'nein'):f.value});
      var lines=c.map(function(l){var p=prod(l.id);return l.q+' x '+p.name+' = '+eur(p.price*l.q)}).join('\n');
      var body='Bestellanfrage\n\n'+lines+'\nGesamt: '+eur(totals())+'\n\nName: '+d.vorname+' '+d.nachname+'\nAdresse: '+d.strasse+', '+d.plz+' '+d.ort+'\nE-Mail: '+d.email+'\nTelefon: '+d.tel+'\nFahrzeug: '+d.fahrzeug+'\nZahlart: '+d.zahlart+'\nMontage: '+d.montage+'\nAnmerkung: '+d.note;
      var btn=$('button[type=submit]',ck);btn.disabled=true;
      location.href='mailto:'+IC.mail+'?subject='+encodeURIComponent('Bestellanfrage italiacamper24.de')+'&body='+encodeURIComponent(body);
      setTimeout(function(){btn.disabled=false;$('#done').hidden=false;$('#done').scrollIntoView({behavior:'smooth'})},600);
    });
    $$('input,select',ck).forEach(function(f){f.addEventListener('blur',function(){if(f.required)f.classList.toggle('invalid',!f.checkValidity())})});
  }

  /* Contact form prefill + submit */
  var cf=$('#contactform');
  if(cf){
    var u=new URLSearchParams(location.search);if(u.get('produkt')){var m=$('[name=nachricht]',cf);m.value='Ich interessiere mich für: '+u.get('produkt')+'\n\nFahrzeug / Baujahr:\n';}
    cf.addEventListener('submit',function(e){e.preventDefault();var ok=true;
      $$('[required]',cf).forEach(function(f){var bad=!f.checkValidity();f.classList.toggle('invalid',bad);if(bad&&ok){f.focus();ok=false}});if(!ok)return;
      var d={};$$('input,select,textarea',cf).forEach(function(f){if(f.name)d[f.name]=f.value});
      location.href='mailto:'+IC.mail+'?subject='+encodeURIComponent('Anfrage: '+(d.betreff||'Beratung'))+'&body='+encodeURIComponent(d.nachricht+'\n\n'+d.name+'\n'+d.email+'\n'+d.tel);
      $('#sent').hidden=false});
  }
})();
