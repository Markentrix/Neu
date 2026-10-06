(function(){
  var f=document.getElementById('resForm');if(!f)return;
  var z=f.zeit,p=f.personen,d=f.datum,msg=document.getElementById('resMsg');
  for(var h=11;h<=19;h++){['00','30'].forEach(function(m){if(h===19&&m==='30')return;var o=document.createElement('option');o.textContent=h+':'+m+' Uhr';z.appendChild(o)})}
  for(var i=1;i<=8;i++){var o=document.createElement('option');o.value=i;o.textContent=i+(i===1?' Person':' Personen');if(i===2)o.selected=true;p.appendChild(o)}
  var t=new Date();d.min=d.value=t.getFullYear()+'-'+String(t.getMonth()+1).padStart(2,'0')+'-'+String(t.getDate()).padStart(2,'0');
  d.addEventListener('change',function(){if(d.value&&new Date(d.value+'T12:00').getDay()===0){msg.className='msg err';msg.textContent='Sonntags ist Ruhetag. Bitte wählen Sie einen anderen Tag.';d.value=''}else{msg.textContent=''}});
  document.getElementById('waLink').addEventListener('click',function(e){
    var txt='Reservierungsanfrage Pizzeria Molise%0A'+['datum','zeit','personen','name'].map(function(k){return k+': '+encodeURIComponent(f[k].value)}).join('%0A');
    e.preventDefault();window.open('https://wa.me/495141214421?text='+txt,'_blank','noopener');
  });
  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!f.checkValidity()){f.reportValidity();return}
    msg.className='msg';msg.textContent='Wird gesendet …';
    fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){if(!r.ok)throw 0;msg.className='msg ok';msg.textContent='Danke! Wir melden uns zur Bestätigung telefonisch.';f.reset()})
      .catch(function(){msg.className='msg err';msg.textContent='Senden nicht möglich. Bitte rufen Sie uns an: 05141 21 44 21'});
  });
})();
(function(){
  var el=document.getElementById('state');if(!el)return;
  try{
    var p=new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',weekday:'short',hour:'numeric',minute:'numeric',hour12:false}).formatToParts(new Date()),o={};
    p.forEach(function(x){o[x.type]=x.value});
    var m=(+o.hour)*60+(+o.minute),sun=/^So/.test(o.weekday);
    if(!sun&&m>=660&&m<1200){el.className='state open';el.textContent='Jetzt geöffnet bis 20 Uhr'}
    else{el.className='state closed';el.textContent=sun?'Heute Ruhetag':(m<660?'Öffnet heute um 11 Uhr':'Heute geschlossen')}
  }catch(e){}
})();
