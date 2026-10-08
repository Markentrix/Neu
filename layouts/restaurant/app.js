(function(){
  var hd=document.querySelector('.top');function hh(){if(hd)document.documentElement.style.setProperty('--hh',hd.offsetHeight+'px')}hh();addEventListener('resize',hh);addEventListener('load',hh);
  var C=window.RES_CFG,DEMO=false;
  var f=document.getElementById('rf');if(!f)return;
  var fd=document.getElementById('fd'),fz=document.getElementById('fz'),fp=document.getElementById('fp'),rw=document.getElementById('rw'),next=document.getElementById('next'),msg=document.getElementById('msg');
  var WD=['So','Mo','Di','Mi','Do','Fr','Sa'];
  function berlin(){var p=new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),o={};p.forEach(function(x){o[x.type]=x.value});return{iso:o.year+'-'+o.month+'-'+o.day,min:(+o.hour)*60+(+o.minute)}}
  function addDays(iso,n){var d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
  function dow(iso){return new Date(iso+'T12:00:00Z').getUTCDay()}
  function fmt(iso){var d=new Date(iso+'T12:00:00Z');return WD[d.getUTCDay()]+', '+d.getUTCDate()+'.'+(d.getUTCMonth()+1)+'.'}
  function hm(m){return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}
  function opt(sel,v,t){var o=document.createElement('option');o.value=v;o.textContent=t;sel.appendChild(o)}
  function ok(t){msg.className='msg ok';msg.innerHTML='<svg class="okc" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M7 12.5l3.2 3.2L17 8.8"/></svg>';var s=document.createElement('span');s.textContent=t;msg.appendChild(s)}
  var now=berlin();
  function times(){var iso=fd.value,keep=fz.value;fz.textContent='';opt(fz,'','Wählen');for(var m=C.from;m<=C.to;m+=C.step){if(iso===now.iso&&m<now.min+30)continue;opt(fz,hm(m),hm(m)+' Uhr')}if(keep)fz.value=keep}
  opt(fd,'','Wählen');
  for(var n=0,added=0;n<14&&added<10;n++){var iso=addDays(now.iso,n);if(dow(iso)===C.closedDow)continue;if(n===0&&now.min+30>C.to)continue;opt(fd,iso,n===0?'Heute':n===1?'Morgen':fmt(iso));added++}
  fd.addEventListener('change',times);times();
  for(var p=1;p<=C.maxPersons;p++)opt(fp,p,String(p));fp.value='2';
  next.addEventListener('click',function(){
    if(!fd.value||!fz.value){msg.className='msg err';msg.textContent='Bitte Tag und Uhrzeit wählen.';(fd.value?fz:fd).focus();return}
    msg.className='msg';msg.textContent=fmt(fd.value)+' um '+fz.value+' Uhr für '+fp.value+(fp.value==='1'?' Person':' Personen');
    rw.classList.add('open');next.classList.add('gone');setTimeout(function(){f.name.focus({preventScroll:true})},120)});
  [fd,fz,fp].forEach(function(s){s.addEventListener('change',function(){if(rw.classList.contains('open')){msg.className='msg';msg.textContent=fd.value&&fz.value?fmt(fd.value)+' um '+fz.value+' Uhr für '+fp.value+(fp.value==='1'?' Person':' Personen'):''}})});
  var wa=document.getElementById('wa');if(wa)wa.addEventListener('click',function(e){e.preventDefault();var t='Reservierungsanfrage '+C.name+'%0A'+encodeURIComponent((fd.value?fmt(fd.value):'')+' '+fz.value+' Uhr, '+fp.value+' Pers.')+'%0AName: '+encodeURIComponent(f.name.value);window.open('https://wa.me/'+C.wa+'?text='+t,'_blank','noopener')});
  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!rw.classList.contains('open')){next.click();return}
    if(!f.checkValidity()){f.reportValidity();return}
    if(DEMO){ok('Vorschau: In der Live-Version wird die Anfrage übermittelt.');return}
    msg.className='msg';msg.textContent='Wird gesendet …';
    fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){if(!r.ok)throw 0;ok('Danke! Wir bestätigen Ihre Anfrage telefonisch.')})
      .catch(function(){msg.className='msg err';msg.textContent='Senden nicht möglich. Bitte rufen Sie uns an: '+C.phone});
  });
  var st=document.getElementById('status');if(st){var m=now.min,open=dow(now.iso)!==C.closedDow&&m>=C.open&&m<C.close;st.className='status '+(open?'open':'closed');st.textContent=open?'Jetzt geöffnet bis '+C.closeLabel:(dow(now.iso)===C.closedDow?'Heute Ruhetag':(m<C.open?'Öffnet heute um '+C.openLabel:'Heute geschlossen'))}
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
  var nav=document.querySelector('.nav2');if(!nav||!('IntersectionObserver' in window)||matchMedia('(max-width:600px)').matches)return;
  var links={};nav.querySelectorAll('a').forEach(function(l){links[l.getAttribute('href').slice(1)]=l});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;
    Object.keys(links).forEach(function(k){links[k].removeAttribute('aria-current')});
    var l=links[e.target.id];if(l){l.setAttribute('aria-current','true');nav.scrollTo({left:l.offsetLeft-nav.clientWidth/2+l.offsetWidth/2,behavior:'smooth'})}})},{rootMargin:'-35% 0px -60% 0px'});
  document.querySelectorAll('.cat').forEach(function(c){io.observe(c)});
})();

(function(){
  var nav=document.querySelector('.nav2');if(!nav)return;
  var mq=matchMedia('(max-width:600px)'),cats=[].slice.call(document.querySelectorAll('.cat')),de=document.documentElement,links={};
  nav.querySelectorAll('a').forEach(function(l){links[l.getAttribute('href').slice(1)]=l});
  function show(id,scroll){
    cats.forEach(function(c){c.classList.toggle('on',c.id===id)});
    Object.keys(links).forEach(function(k){if(k===id)links[k].setAttribute('aria-current','true');else links[k].removeAttribute('aria-current')});
    var l=links[id];if(l)nav.scrollTo({left:l.offsetLeft-nav.clientWidth/2+l.offsetWidth/2,behavior:'smooth'});
    if(scroll){var hh=parseInt(getComputedStyle(de).getPropertyValue('--hh'))||62,top=nav.getBoundingClientRect().top+scrollY-hh;if(Math.abs(scrollY-top)>2&&nav.getBoundingClientRect().top<=hh+2)scrollTo(0,top);else if(nav.getBoundingClientRect().top>hh+2&&scroll===2)scrollTo(0,top)}
  }
  function apply(){
    if(!mq.matches){de.classList.remove('js-tabs');return}
    de.classList.add('js-tabs');
    var h=location.hash.slice(1),cur=document.querySelector('.cat.on');
    show(cats.some(function(c){return c.id===h})?h:(cur?cur.id:cats[0].id),false);
  }
  nav.addEventListener('click',function(e){var a=e.target.closest('a');if(!a||!mq.matches)return;e.preventDefault();show(a.getAttribute('href').slice(1),true)});
  mq.addEventListener('change',apply);apply();
})();
