// Progressive Enhancement: Die Seite funktioniert auch ohne dieses Skript.
document.documentElement.classList.add('js');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

// Reveal beim Scrollen (Sicherheitsnetz nach 2,5 s)
const targets = document.querySelectorAll('[data-reveal]');
if (reduce || !('IntersectionObserver' in window)) { targets.forEach(el => el.classList.add('is-in')); }
else {
  const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
  targets.forEach(el => io.observe(el));
  setTimeout(() => targets.forEach(el => el.classList.add('is-in')), 2500);
}

// Mobiles Menü
const btn = document.querySelector('.menu-btn'), nav = document.getElementById('nav');
if (btn && nav) {
  const set = o => { nav.dataset.open = o; btn.setAttribute('aria-expanded', o); btn.textContent = o ? 'Schließen' : 'Menü'; };
  btn.addEventListener('click', () => set(nav.dataset.open !== 'true'));
  nav.addEventListener('click', e => { if (e.target.closest('a')) set(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.dataset.open === 'true') { set(false); btn.focus(); } });
}

// Bestand filtern und sortieren (die Karten stehen bereits im HTML, JS blendet nur aus/ein)
const list = document.getElementById('bikes');
if (list) {
  const cards = [...list.querySelectorAll('.bike')];
  const f = { marke: document.getElementById('f-marke'), typ: document.getElementById('f-typ'), preis: document.getElementById('f-preis'), sort: document.getElementById('f-sort') };
  const out = document.getElementById('count-out'), empty = document.getElementById('empty');
  const q = new URLSearchParams(location.search);
  for (const k of ['marke', 'typ', 'preis', 'sort']) if (q.get(k) && f[k]) f[k].value = q.get(k);
  const apply = () => {
    const maxp = +f.preis.value || Infinity; let n = 0;
    cards.forEach(c => {
      const ok = (!f.marke.value || c.dataset.marke === f.marke.value) && (!f.typ.value || c.dataset.typ === f.typ.value) && (+c.dataset.preis <= maxp);
      c.hidden = !ok; if (ok) n++;
    });
    const s = f.sort.value, key = { 'preis-auf': c => +c.dataset.preis, 'preis-ab': c => -c.dataset.preis, 'neu': c => -c.dataset.jahr, 'km': c => +c.dataset.km, 'empf': c => +c.dataset.pos }[s] || (c => +c.dataset.pos);
    cards.slice().sort((a, b) => key(a) - key(b)).forEach(c => list.appendChild(c));
    out.textContent = n + (n === 1 ? ' Motorrad' : ' Motorräder');
    empty.classList.toggle('on', n === 0);
    const u = new URLSearchParams(); for (const k in f) if (f[k].value) u.set(k, f[k].value);
    history.replaceState(null, '', u.toString() ? '?' + u : location.pathname);
  };
  Object.values(f).forEach(el => el && el.addEventListener('change', apply));
  document.getElementById('f-reset')?.addEventListener('click', () => { Object.values(f).forEach(el => el.value = ''); apply(); });
  apply();
}

// Galerie auf der Detailseite
document.querySelectorAll('.gal').forEach(g => {
  const main = g.querySelector('.main img'); const bs = g.querySelectorAll('.thumbs button');
  bs.forEach(b => b.addEventListener('click', () => { main.src = b.dataset.src; main.alt = b.dataset.alt; bs.forEach(x => x.removeAttribute('aria-current')); b.setAttribute('aria-current', 'true'); }));
});

// Demo-Formulare: kein Versand, weiter zur Danke-Seite
document.querySelectorAll('form[data-demo-form]').forEach(f => f.addEventListener('submit', e => {
  e.preventDefault();
  const s = f.querySelector('.status'); if (s) s.textContent = 'Demo: Es wurde nichts gesendet. In der echten Seite folgt jetzt die Danke-Seite.';
  setTimeout(() => { location.href = f.dataset.next || 'danke.html'; }, 900);
}));

// Merkliste (nur lokal im Browser, keine Daten gehen an einen Server)
(() => {
  let favs = []; try { favs = JSON.parse(localStorage.getItem('mh-favs') || '[]'); } catch (e) {}
  const save = () => { try { localStorage.setItem('mh-favs', JSON.stringify(favs)); } catch (e) {} };
  const paint = () => {
    document.querySelectorAll('[data-fav]').forEach(b => {
      const on = favs.includes(b.dataset.fav); b.hidden = false; b.setAttribute('aria-pressed', on);
      if (b.classList.contains('fav-btn')) b.textContent = on ? 'Gemerkt' : 'Merken';
    });
    document.querySelectorAll('.fav-link').forEach(a => { a.hidden = false; a.querySelector('[data-fav-count]').textContent = favs.length || ''; a.setAttribute('aria-label', 'Merkliste, ' + favs.length + ' Fahrzeuge'); });
    const ml = document.getElementById('ml-list');
    if (ml) { let n = 0; ml.querySelectorAll('.bike').forEach(c => { const on = favs.includes(c.querySelector('[data-fav]').dataset.fav); c.hidden = !on; n += on; }); document.getElementById('ml-empty').hidden = n > 0; }
  };
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-fav]'); if (!b) return;
    const s = b.dataset.fav; favs = favs.includes(s) ? favs.filter(x => x !== s) : [...favs, s]; save(); paint();
  });
  paint();
})();

// Ratenrechner (Beispielrechnung)
document.querySelectorAll('.calc').forEach(c => {
  c.hidden = false;
  const g = k => c.querySelector('[data-c=' + k + ']'), out = c.querySelector('[data-c-out]'), price = +out.dataset.price;
  const run = () => {
    const down = Math.min(Math.max(+g('down').value || 0, 0), price), n = +g('term').value, r = (+g('rate').value || 0) / 1200, P = price - down;
    const m = P <= 0 ? 0 : (r ? P * r / (1 - Math.pow(1 + r, -n)) : P / n);
    out.textContent = m.toLocaleString('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }) + ' / Monat';
  };
  c.addEventListener('input', run); run();
});
