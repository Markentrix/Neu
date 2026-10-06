(function(){
  // ---- Konfiguration ----
  var PHONE_WA = '495141214421';   // WhatsApp-Nummer (ohne +)
  var tabs = document.querySelectorAll('.tabs button');
  tabs.forEach(function(b){b.addEventListener('click',function(){
    tabs.forEach(function(x){x.setAttribute('aria-selected',x===b)});
    document.querySelectorAll('.menu').forEach(function(m){m.hidden=m.id!=='tab-'+b.dataset.tab});
  })});

  var f=document.getElementById('resForm'); if(!f) return;
  var sel=f.zeit, d=f.datum, msg=document.getElementById('resMsg');
  for(var h=11;h<=19;h++){['00','30'].forEach(function(m){
    if(h===19&&m==='30')return; var o=document.createElement('option'); o.textContent=h+':'+m+' Uhr'; sel.appendChild(o);});}
  var t=new Date(); var iso=function(x){return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0')};
  d.min=iso(t); d.value=iso(t);
  d.addEventListener('change',function(){ if(new Date(d.value+'T12:00').getDay()===0){msg.className='msg err';msg.textContent='Sonntags ist Ruhetag – bitte anderen Tag wählen.';d.value=''} else msg.textContent='';});

  function summary(){return 'Reservierungsanfrage Pizzeria Molise%0A'+['datum','zeit','personen','name','telefon'].map(function(k){return k+': '+encodeURIComponent(f[k].value)}).join('%0A')}
  document.getElementById('waLink').addEventListener('click',function(e){e.preventDefault();window.open('https://wa.me/'+PHONE_WA+'?text='+summary(),'_blank','noopener')});

  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!f.checkValidity()){f.reportValidity();return}
    msg.className='msg';msg.textContent='Wird gesendet …';
    fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){if(!r.ok)throw 0;msg.className='msg ok';msg.textContent='Danke! Wir haben Ihre Anfrage erhalten und melden uns zur Bestätigung.';f.reset()})
      .catch(function(){msg.className='msg err';msg.innerHTML='Senden nicht möglich – bitte rufen Sie uns an: <a href="tel:+495141214421">05141 21 44 21</a>'});
  });
})();
