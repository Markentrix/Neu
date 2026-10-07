(function(){
  var C=window.RES_CFG,DEMO=false;
  var f=document.getElementById('rf');if(!f)return;
  var dEl=document.getElementById('dates'),tEl=document.getElementById('times'),pv=document.getElementById('pv'),sum=document.getElementById('sum'),msg=document.getElementById('msg');
  var other=f.querySelector('[name=anderes]'),fd=f.datum,fz=f.zeit,fp=f.personen,persons=2;
  var WD=['So','Mo','Di','Mi','Do','Fr','Sa'];
  function berlin(){var p=new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),o={};p.forEach(function(x){o[x.type]=x.value});return{iso:o.year+'-'+o.month+'-'+o.day,min:(+o.hour)*60+(+o.minute)}}
  function addDays(iso,n){var d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
  function dow(iso){return new Date(iso+'T12:00:00Z').getUTCDay()}
  function fmt(iso){var d=new Date(iso+'T12:00:00Z');return WD[d.getUTCDay()]+', '+d.getUTCDate()+'.'+(d.getUTCMonth()+1)+'.'}
  var now=berlin(),closedIdx=C.closedDow;
  function mk(name,val,label,dis){var l=document.createElement('label');l.className='opt';var i=document.createElement('input');i.type='radio';i.name=name;i.value=val;i.disabled=!!dis;var s=document.createElement('span');s.textContent=label;l.appendChild(i);l.appendChild(s);return l}
  function slots(){var a=[],s=C.from,e=C.to;for(var m=s;m<=e;m+=C.step)a.push(m);return a}
  function hm(m){return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}
  function renderTimes(){
    tEl.textContent='';var iso=fd.value;if(!iso)return;var today=iso===now.iso,any=false,keep=fz.value;fz.value='';
    slots().forEach(function(m){var dis=today&&m<now.min+30;var el=mk('zeit_radio',hm(m),hm(m),dis);if(!dis)any=true;tEl.appendChild(el)});
    if(!any){var p=document.createElement('p');p.className='sum';p.textContent='Für heute sind keine Zeiten mehr frei. Bitte anderen Tag wählen.';tEl.appendChild(p)}
    var r=tEl.querySelector('input[value="'+keep+'"]:not(:disabled)');if(r){r.checked=true;fz.value=keep}
    update();
  }
  function setDate(iso){
    if(dow(iso)===closedIdx){msg.className='msg err';msg.textContent='An diesem Tag ist Ruhetag.';return}
    msg.textContent='';fd.value=iso;renderTimes()}
  var lastSlot=C.to;[0,1,2].forEach(function(n){var iso=addDays(now.iso,n),closed=dow(iso)===closedIdx||(n===0&&now.min+30>lastSlot);var el=mk('tag',iso,(n===0?'Heute':n===1?'Morgen':fmt(iso)),closed);dEl.appendChild(el)});
  var first=dEl.querySelector('input:not(:disabled)');if(first){first.checked=true;setDate(first.value)}
  dEl.addEventListener('change',function(e){if(e.target.name==='tag'){other.value='';setDate(e.target.value)}});
  other.min=now.iso;other.addEventListener('change',function(){if(!other.value)return;dEl.querySelectorAll('input').forEach(function(i){i.checked=false});if(dow(other.value)===closedIdx){other.value='';msg.className='msg err';msg.textContent='An diesem Tag ist Ruhetag.';return}setDate(other.value)});
  tEl.addEventListener('change',function(e){if(e.target.name==='zeit_radio'){fz.value=e.target.value;update()}});
  function setP(n){persons=Math.max(1,Math.min(C.maxPersons,n));pv.textContent=persons+(persons===1?' Person':' Personen');fp.value=persons;update()}
  document.getElementById('pm').addEventListener('click',function(){setP(persons-1)});document.getElementById('pp').addEventListener('click',function(){setP(persons+1)});setP(2);
  function update(){sum.textContent=(fd.value&&fz.value)?fmt(fd.value)+' um '+fz.value+' Uhr für '+persons+(persons===1?' Person':' Personen'):'Bitte Tag und Uhrzeit wählen.'}
  var wa=document.getElementById('wa');if(wa)wa.addEventListener('click',function(e){e.preventDefault();var t='Reservierungsanfrage '+C.name+'%0A'+encodeURIComponent(sum.textContent)+'%0AName: '+encodeURIComponent(f.name.value);window.open('https://wa.me/'+C.wa+'?text='+t,'_blank','noopener')});
  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!fd.value||!fz.value){msg.className='msg err';msg.textContent='Bitte Tag und Uhrzeit wählen.';return}
    if(!f.checkValidity()){f.reportValidity();return}
    if(DEMO){msg.className='msg ok';msg.textContent='Vorschau: In der Live-Version wird die Anfrage übermittelt.';return}
    msg.className='msg';msg.textContent='Wird gesendet …';
    fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){if(!r.ok)throw 0;msg.className='msg ok';msg.textContent='Danke! Wir bestätigen Ihre Anfrage telefonisch.'})
      .catch(function(){msg.className='msg err';msg.textContent='Senden nicht möglich. Bitte rufen Sie uns an: '+C.phone});
  });
  var st=document.getElementById('status');if(st){var m=now.min,open=dow(now.iso)!==closedIdx&&m>=C.open&&m<C.close;st.className='status '+(open?'open':'closed');st.textContent=open?'Jetzt geöffnet bis '+C.closeLabel:(dow(now.iso)===closedIdx?'Heute Ruhetag':(m<C.open?'Öffnet heute um '+C.openLabel:'Heute geschlossen'))}
})();
