(function(){
  var hd=document.querySelector('.top');function hh(){if(hd)document.documentElement.style.setProperty('--hh',hd.offsetHeight+'px')}hh();addEventListener('resize',hh);addEventListener('load',hh);
  var C=window.RES_CFG,DEMO=false;
  var f=document.getElementById('rf');if(!f)return;
  var E=f.elements,fd=document.getElementById('fd'),fz=document.getElementById('fz'),fp=document.getElementById('fp'),rw=document.getElementById('rw'),next=document.getElementById('next'),send=document.getElementById('send'),msg=document.getElementById('msg'),wa=document.getElementById('wa');
  var WD=['So','Mo','Di','Mi','Do','Fr','Sa'];
  function berlin(){var p=new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),o={};p.forEach(function(x){o[x.type]=x.value});return{iso:o.year+'-'+o.month+'-'+o.day,min:(+o.hour)*60+(+o.minute)}}
  function addDays(iso,n){var d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
  function dow(iso){return new Date(iso+'T12:00:00Z').getUTCDay()}
  function fmt(iso){var d=new Date(iso+'T12:00:00Z');return WD[d.getUTCDay()]+', '+d.getUTCDate()+'.'+(d.getUTCMonth()+1)+'.'}
  function hm(m){return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}
  function mins(s){var p=s.split(':');return +p[0]*60+ +p[1]}
  function opt(sel,v,t,dis){var o=document.createElement('option');o.value=v;o.textContent=t;if(dis)o.disabled=true;sel.appendChild(o)}
  function ok(t){msg.className='msg ok';msg.textContent='';var s=document.createElement('span');s.className='okc';s.setAttribute('aria-hidden','true');msg.appendChild(s);var x=document.createElement('span');x.textContent=t;msg.appendChild(x)}
  var now=berlin(),closed=[C.closedDow],blocked={},slotTimes=null,self=null;
  function getJson(u){var c=typeof AbortController!=='undefined'?new AbortController():null,t=setTimeout(function(){if(c)c.abort()},6000);return fetch(u,{signal:c?c.signal:undefined,headers:{Accept:'application/json'}}).then(function(r){clearTimeout(t);if(!r.ok)throw r;return r.json()})}
  function isClosed(iso){return closed.indexOf(dow(iso))>-1||blocked[iso]}
  function baseTimes(){if(slotTimes&&slotTimes.length)return slotTimes;var a=[];for(var m=C.from;m<=C.to;m+=C.step)a.push(hm(m));return a}
  function lastMin(){var l=baseTimes();return mins(l[l.length-1])}
  function renderTimes(list){var iso=fd.value,keep=fz.value;fz.textContent='';opt(fz,'','Wählen');
    list.forEach(function(s){if(iso===now.iso&&mins(s.zeit)<now.min+30)return;opt(fz,s.zeit,s.frei===false?s.zeit+' belegt':s.zeit,s.frei===false)});
    if(keep&&fz.querySelector('option[value="'+keep+'"]:not(:disabled)'))fz.value=keep}
  function loadTimes(){var iso=fd.value;renderTimes(baseTimes().map(function(z){return{zeit:z,frei:true}}));if(!iso||DEMO)return;
    getJson('/api/slots?tag='+iso).then(function(d){if(fd.value===iso&&d&&d.slots)renderTimes(d.slots)}).catch(function(){})}
  function buildDates(){var keep=fd.value;fd.textContent='';opt(fd,'','Wählen');
    for(var n=0,added=0;n<45&&added<10;n++){var iso=addDays(now.iso,n);if(isClosed(iso))continue;if(n===0&&now.min+30>lastMin())continue;opt(fd,iso,n===0?'Heute':n===1?'Morgen':fmt(iso));added++}
    if(keep&&fd.querySelector('option[value="'+keep+'"]'))fd.value=keep}
  function labels(){send.textContent=self===true?'Tisch buchen':self===false?'Tischwunsch senden':'Tisch anfragen'}
  function note(){return self===true?'Die Bestätigung kommt per E-Mail.':self===false?'Wir melden uns zur Bestätigung.':'Wir bestätigen Ihre Anfrage.'}
  function summary(){return fd.value&&fz.value?fmt(fd.value)+' um '+fz.value+' Uhr, '+fp.value+(fp.value==='1'?' Gast':' Gäste')+'. '+note():''}
  buildDates();loadTimes();
  for(var p=1;p<=C.maxPersons;p++)opt(fp,p,String(p));fp.value='2';
  if(!DEMO)getJson('/api/verfuegbarkeit').then(function(d){if(!d)return;
    if(Array.isArray(d.closedWeekdays))closed=d.closedWeekdays;
    if(Array.isArray(d.blocked))d.blocked.forEach(function(x){blocked[x]=true});
    if(Array.isArray(d.slotTimes)&&d.slotTimes.length)slotTimes=d.slotTimes;
    if(typeof d.selfBooking==='boolean')self=d.selfBooking;
    buildDates();loadTimes();labels()}).catch(function(){});
  fd.addEventListener('change',loadTimes);
  next.addEventListener('click',function(){
    if(!fd.value||!fz.value){msg.className='msg err';msg.textContent='Bitte Tag und Uhrzeit wählen.';(fd.value?fz:fd).focus();return}
    msg.className='msg';msg.textContent=summary();
    rw.classList.add('open');next.classList.add('gone');setTimeout(function(){E.name.focus({preventScroll:true})},120)});
  [fd,fz,fp].forEach(function(s){s.addEventListener('change',function(){if(rw.classList.contains('open')){msg.className='msg';msg.textContent=summary()}})});
  if(wa)wa.addEventListener('click',function(e){e.preventDefault();var t='Reservierungsanfrage '+C.name+'\n'+(fd.value?fmt(fd.value)+' ':'')+(fz.value?fz.value+' Uhr, ':'')+fp.value+' Gäste\nName: '+E.name.value;window.open('https://wa.me/'+C.wa+'?text='+encodeURIComponent(t),'_blank','noopener')});
  function clearErr(){f.querySelectorAll('.ferr').forEach(function(x){x.remove()});f.querySelectorAll('[aria-invalid]').forEach(function(x){x.removeAttribute('aria-invalid')})}
  function showErrors(errs){clearErr();var other=[];Object.keys(errs||{}).forEach(function(k){var el=E[k==='uhrzeit'?'uhrzeit':k];if(el&&el.closest){var l=el.closest('label'),s=document.createElement('span');s.className='ferr';s.setAttribute('role','alert');s.textContent=errs[k];el.setAttribute('aria-invalid','true');(l||el.parentNode).appendChild(s)}else other.push(errs[k])});
    msg.className='msg err';msg.textContent=other.length?other.join(' '):'Bitte prüfen Sie die markierten Felder.'}
  function fallback(){msg.className='msg err';msg.textContent='Die Online-Reservierung ist gerade nicht erreichbar. Bitte rufen Sie uns an: ';var a=document.createElement('a');a.href='tel:'+C.phoneHref;a.textContent=C.phone;msg.appendChild(a);msg.appendChild(document.createTextNode(' oder schreiben Sie uns per WhatsApp (Link unter dem Formular).'))}
  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!rw.classList.contains('open')){next.click();return}
    clearErr();
    if(!f.checkValidity()){var bad=f.querySelector(':invalid');if(bad){var l=bad.closest('label'),s=document.createElement('span');s.className='ferr';s.setAttribute('role','alert');s.textContent=bad.validationMessage||'Bitte ausfüllen.';bad.setAttribute('aria-invalid','true');(l||bad.parentNode).appendChild(s);bad.focus()}msg.className='msg err';msg.textContent='Bitte prüfen Sie die markierten Felder.';return}
    if(DEMO){ok('Vorschau: In der Live-Version geht die Anfrage ans Portal.');return}
    var data={typ:'termin',name:E.name.value.trim(),telefon:E.telefon.value.trim(),email:E.email.value.trim(),nachricht:E.nachricht.value.trim(),einwilligung:E.einwilligung.checked?'ja':'',datum:fd.value,uhrzeit:fz.value,personen:fp.value,website:E.website.value};
    send.disabled=true;msg.className='msg';msg.textContent='Wird gesendet …';
    fetch('/api/anfrage',{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(data)})
      .then(function(r){return r.json().catch(function(){return {}}).then(function(d){return{s:r.status,d:d}})})
      .then(function(x){
        if(x.s===200&&x.d&&x.d.ok){location.href='danke.html?typ=termin&ref='+encodeURIComponent(x.d.ref||'');return}
        send.disabled=false;
        if(x.s===422){showErrors(x.d&&x.d.errors);if(x.d&&x.d.errors&&x.d.errors.uhrzeit)loadTimes();return}
        if(x.s===429){msg.className='msg err';msg.textContent='Bitte versuchen Sie es später noch einmal.';return}
        fallback()})
      .catch(function(){send.disabled=false;fallback()});
  });
  var st=document.getElementById('status');if(st){var m=now.min,open=closed.indexOf(dow(now.iso))===-1&&m>=C.open&&m<C.close;st.className='status '+(open?'open':'closed');st.textContent=open?'Jetzt geöffnet bis '+C.closeLabel:(closed.indexOf(dow(now.iso))>-1?'Heute Ruhetag':(m<C.open?'Öffnet heute um '+C.openLabel:'Heute geschlossen'))}
})();

(function(){
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;if(reduce||matchMedia('(max-width:600px)').matches)return;
  var de=document.documentElement,cats=document.querySelectorAll('.cat');
  if('IntersectionObserver' in window&&cats.length){
    de.classList.add('js-rv');
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -10% 0px',threshold:.08});
    cats.forEach(function(c){io.observe(c)});
  }
  var ph=document.querySelector('.photo'),tick=false;
  if(ph){addEventListener('scroll',function(){if(tick)return;tick=true;requestAnimationFrame(function(){var y=Math.min(scrollY,700);ph.style.setProperty('--py',(y*.05).toFixed(1)+'px');tick=false})},{passive:true})}
})();

(function(){
  var nav=document.querySelector('.nav2');if(!nav||!('IntersectionObserver' in window))return;
  var links={};nav.querySelectorAll('a').forEach(function(l){links[l.getAttribute('href').slice(1)]=l});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;
    Object.keys(links).forEach(function(k){links[k].removeAttribute('aria-current')});
    var l=links[e.target.id];if(l){l.setAttribute('aria-current','true');nav.scrollTo({left:l.offsetLeft-nav.clientWidth/2+l.offsetWidth/2,behavior:'smooth'})}})},{rootMargin:'-35% 0px -60% 0px'});
  document.querySelectorAll('.cat').forEach(function(c){io.observe(c)});
})();
