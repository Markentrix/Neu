const $ = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];

const nav = $('#nav'), burger = $('#burger'), sticky = $('.sticky-cta');

addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', scrollY > 40);
  sticky.classList.toggle('show', scrollY > innerHeight * 0.8);
}, { passive: true });

burger.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  burger.setAttribute('aria-expanded', open);
});
$$('#menu a').forEach(a => a.addEventListener('click', () => {
  nav.classList.remove('open');
  burger.setAttribute('aria-expanded', false);
}));

$$('.tab').forEach(tab => tab.addEventListener('click', () => {
  $$('.tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', false); });
  $$('.panel').forEach(p => p.classList.remove('active'));
  tab.classList.add('active');
  tab.setAttribute('aria-selected', true);
  $('#' + tab.dataset.tab).classList.add('active');
}));

const io = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
}), { threshold: 0.15 });
$$('.reveal').forEach((el, i) => { el.style.transitionDelay = (i % 4) * 80 + 'ms'; io.observe(el); });

const dateInput = $('input[type=date]');
dateInput.min = new Date().toISOString().slice(0, 10);

$('#resform').addEventListener('submit', e => {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target));
  const body = `Name: ${f.name}\nPersonen: ${f.personen}\nDatum: ${f.datum}\nUhrzeit: ${f.zeit}\n\n${f.msg || ''}`;
  location.href = `mailto:contact@helium-ffm.de?subject=${encodeURIComponent('Reservierung ' + f.datum)}&body=${encodeURIComponent(body)}`;
});

$('#yr').textContent = new Date().getFullYear();
