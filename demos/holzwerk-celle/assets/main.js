// Progressive Enhancement: Die Seite funktioniert auch ohne dieses Skript.
document.documentElement.classList.add('js');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

// Reveal beim Scrollen
const targets = document.querySelectorAll('[data-reveal]');
if (reduce || !('IntersectionObserver' in window)) {
  targets.forEach(el => el.classList.add('is-in'));
} else {
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  targets.forEach(el => io.observe(el));
}

// Mobiles Menü
const btn = document.querySelector('.menu-btn'), nav = document.getElementById('nav');
if (btn && nav) {
  const set = (open) => { nav.dataset.open = open; btn.setAttribute('aria-expanded', open); btn.textContent = open ? 'Schließen' : 'Menü'; };
  btn.addEventListener('click', () => set(nav.dataset.open !== 'true'));
  nav.addEventListener('click', e => { if (e.target.closest('a')) set(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.dataset.open === 'true') { set(false); btn.focus(); } });
}

// Vorher/Nachher-Regler (nativer Range-Input, per Tastatur bedienbar)
document.querySelectorAll('.ba').forEach(ba => {
  const r = ba.querySelector('input');
  const upd = () => ba.style.setProperty('--pos', r.value + '%');
  r.addEventListener('input', upd); upd();
});

// Demo-Formular: nicht aktiv
const form = document.getElementById('anfrage');
if (form) form.addEventListener('submit', e => {
  e.preventDefault();
  document.getElementById('form-status').textContent = 'Demo: Das Formular ist in dieser Vorschau nicht aktiv. Es wurde nichts gesendet.';
});
