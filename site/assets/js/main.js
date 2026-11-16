/* Lohnunternehmen Linneweh – Interaktion & Motion (ohne Abhängigkeiten) */
(() => {
  'use strict';
  window.__lul = true;
  const doc = document.documentElement;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- Text in Wörter zerlegen ---------- */
  function split(el) {
    let wi = 0;
    const walk = (node) => {
      [...node.childNodes].forEach((n) => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.append(' '); return; }
            const w = document.createElement('span');
            w.className = 'w';
            const inner = document.createElement('span');
            inner.textContent = part;
            inner.style.setProperty('--wi', wi++);
            w.append(inner);
            frag.append(w);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && n.tagName !== 'BR') walk(n);
      });
    };
    el.setAttribute('aria-label', el.textContent.trim());
    walk(el);
    el.classList.add('is-split');
  }
  $$('[data-split]').forEach(split);

  /* ---------- Reveal beim Scrollen ---------- */
  $$('[data-stagger]').forEach((g) => $$('[data-reveal]', g).forEach((el, i) => el.style.setProperty('--i', i % 6)));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });
  const lazyReveal = $$('[data-reveal], [data-split]').filter((el) => !el.hasAttribute('data-split-now') && !el.hasAttribute('data-reveal-now'));
  lazyReveal.forEach((el) => io.observe(el));

  /* ---------- Start / Intro ---------- */
  function ready() {
    document.body.classList.add('is-ready');
    $$('[data-split-now], [data-reveal-now]').forEach((el) => el.classList.add('is-in'));
  }
  if (doc.classList.contains('intro') && !reduced) {
    const num = $('.loader__num');
    const from = 1973; const to = new Date().getFullYear(); const t0 = performance.now(); const dur = 1400;
    const tick = (t) => {
      const p = clamp((t - t0) / dur);
      if (num) num.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
      if (p < 1) return requestAnimationFrame(tick);
      doc.classList.add('intro-out');
      setTimeout(ready, 250);
      setTimeout(() => doc.classList.remove('intro', 'intro-out'), 1300);
      try { sessionStorage.setItem('lul-intro', '1'); } catch (e) { /* egal */ }
    };
    requestAnimationFrame(tick);
  } else {
    doc.classList.remove('intro');
    requestAnimationFrame(() => requestAnimationFrame(ready));
  }

  /* ---------- Header ---------- */
  const hdr = $('[data-hdr]');
  let lastY = scrollY;
  function onHeader() {
    const y = scrollY;
    hdr.classList.toggle('is-solid', y > 40);
    if (Math.abs(y - lastY) > 6) {
      hdr.classList.toggle('is-hidden', y > lastY && y > 500 && !document.body.classList.contains('menu-open'));
      lastY = y;
    }
  }

  /* ---------- Menü ---------- */
  const menu = $('#menu');
  const toggle = $('[data-menu-toggle]');
  $$('.menu__main a').forEach((a, i) => a.style.setProperty('--i', i));
  function setMenu(open) {
    menu.classList.toggle('is-open', open);
    menu.toggleAttribute('inert', !open);
    menu.setAttribute('aria-hidden', String(!open));
    toggle.setAttribute('aria-expanded', String(open));
    const txt = $('.hdr__burger-txt', toggle);
    if (txt) txt.textContent = open ? 'Schließen' : 'Menü';
    document.body.classList.toggle('menu-open', open);
    doc.style.overflow = open ? 'hidden' : '';
    if (open) hdr.classList.remove('is-hidden');
  }
  toggle.addEventListener('click', () => setMenu(!menu.classList.contains('is-open')));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && menu.classList.contains('is-open')) { setMenu(false); toggle.focus(); } });
  $$('.menu__main a').forEach((a) => a.addEventListener('pointerenter', () => {
    $$('.menu__preview img').forEach((im) => im.classList.toggle('is-on', im.dataset.name === a.dataset.img));
  }));

  /* ---------- Hero-Slider ---------- */
  const hero = $('[data-hero]');
  if (hero) {
    const slides = $$('.hero__slide', hero); const tabs = $$('.hero__tab', hero); const words = $$('.hero__swap b', hero);
    const DUR = 6500; let cur = 0; let timer;
    hero.style.setProperty('--dur', DUR + 'ms');
    const go = (i) => {
      if (i === cur) return;
      const prev = cur; cur = i;
      slides.forEach((s, n) => {
        const img = $('img', s);
        if (n === prev) { img.style.transform = getComputedStyle(img).transform; s.classList.add('is-prev'); s.classList.remove('is-active'); } else { s.classList.remove('is-prev'); }
        if (n === i) { img.style.transform = ''; s.classList.add('is-active'); }
      });
      words.forEach((w, n) => {
        if (n === prev) { w.classList.add('is-out'); w.classList.remove('is-active'); } else if (n === i) {
          w.style.transition = 'none'; w.classList.remove('is-out'); void w.offsetWidth; w.style.transition = ''; w.classList.add('is-active');
        }
      });
      tabs.forEach((t, n) => { t.classList.toggle('is-active', n === i); t.setAttribute('aria-selected', String(n === i)); });
      schedule();
    };
    const schedule = () => { clearTimeout(timer); if (!reduced) timer = setTimeout(() => go((cur + 1) % slides.length), DUR); };
    tabs.forEach((t, n) => t.addEventListener('click', () => go(n)));
    document.addEventListener('visibilitychange', () => { hero.classList.toggle('is-paused', document.hidden); document.hidden ? clearTimeout(timer) : schedule(); });
    schedule();
  }

  /* ---------- Zähler ---------- */
  const cio = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      cio.unobserve(e.target);
      const el = e.target; const to = +el.dataset.count; const from = el.hasAttribute('data-plain') ? to - 60 : 0; const t0 = performance.now(); const dur = 1800;
      const tick = (t) => {
        const p = clamp((t - t0) / dur);
        el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 4)));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.6 });
  if (!reduced) $$('[data-count]').forEach((el) => cio.observe(el));

  /* ---------- Scroll-gebundene Effekte ---------- */
  const par = reduced ? [] : $$('[data-parallax]').map((el) => ({ el, f: +el.dataset.parallax, box: el.closest('.frame, .phero, .cta, .jobs') || el.parentElement }));
  const tl = $('[data-progress]');
  const word = $('.ftr__word span');
  const hs = $('[data-hscroll]');
  let hsDist = 0;
  const hsTrack = hs && $('.hs__track', hs); const hsCount = hs && $('.hs__count b', hs); const hsBar = hs && $('.hs__bar', hs);
  function measure() {
    if (!hs) return;
    const pin = innerWidth >= 900 && !reduced && innerHeight >= 620;
    hs.classList.toggle('hs--pin', pin);
    if (pin) {
      hsTrack.style.transform = 'none';
      hsDist = Math.max(0, hsTrack.scrollWidth - innerWidth);
      hs.style.height = innerHeight + hsDist + 'px';
    } else { hs.style.height = ''; hsTrack.style.transform = ''; hsDist = 0; }
  }
  function frame() {
    ticking = false;
    const vh = innerHeight;
    onHeader();
    par.forEach(({ el, f, box }) => {
      const r = box.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      const p = clamp((r.top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2), -1, 1);
      el.style.translate = `0 ${(p * r.height * f * 0.45).toFixed(1)}px`;
    });
    if (hs && hsDist) {
      const r = hs.getBoundingClientRect();
      const p = clamp(-r.top / hsDist);
      hsTrack.style.transform = `translate3d(${(-p * hsDist).toFixed(1)}px,0,0)`;
      const n = hsTrack.children.length;
      hsCount.textContent = String(Math.min(n, Math.floor(p * n) + 1)).padStart(2, '0');
      hsBar.style.setProperty('--p', p.toFixed(3));
    }
    if (tl) {
      const r = tl.getBoundingClientRect();
      tl.style.setProperty('--p', clamp((vh * 0.62 - r.top) / r.height).toFixed(3));
    }
    if (word) {
      const r = word.getBoundingClientRect();
      if (r.top < vh) word.style.setProperty('--fill', (clamp((vh - r.top) / (r.height * 1.1)) * 100).toFixed(1) + '%');
    }
  }
  let ticking = false;
  const req = () => { if (!ticking) { ticking = true; requestAnimationFrame(frame); } };
  addEventListener('scroll', req, { passive: true });
  addEventListener('resize', () => { measure(); req(); });
  addEventListener('load', () => { measure(); req(); });
  measure(); frame();

  /* ---------- Ziehen zum Scrollen & Karussell ---------- */
  $$('[data-drag]').forEach((el) => {
    let down = false; let sx = 0; let sl = 0; let moved = false;
    el.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse' || e.button !== 0) return; down = true; moved = false; sx = e.clientX; sl = el.scrollLeft; });
    addEventListener('pointermove', (e) => {
      if (!down) return;
      const dx = e.clientX - sx;
      if (Math.abs(dx) > 5 && !moved) { moved = true; el.classList.add('is-dragging'); }
      if (moved) el.scrollLeft = sl - dx;
    });
    addEventListener('pointerup', () => { if (!down) return; down = false; setTimeout(() => el.classList.remove('is-dragging'), 0); });
    el.addEventListener('click', (e) => { if (moved) { e.preventDefault(); e.stopPropagation(); } }, true);
    el.addEventListener('dragstart', (e) => e.preventDefault());
  });
  $$('[data-carousel]').forEach((track) => {
    const sec = track.closest('section'); const prev = $('[data-prev]', sec); const next = $('[data-next]', sec);
    if (!prev || !next) return;
    const step = () => (track.firstElementChild.getBoundingClientRect().width + 24) * (innerWidth > 900 ? 2 : 1);
    const upd = () => { prev.disabled = track.scrollLeft < 8; next.disabled = track.scrollLeft > track.scrollWidth - track.clientWidth - 8; };
    prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    next.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
    track.addEventListener('scroll', upd, { passive: true }); upd();
  });

  /* ---------- Inhaltsverzeichnis ---------- */
  const tocLinks = $$('.toc a');
  if (tocLinks.length) {
    const map = new Map(tocLinks.map((a) => [a.getAttribute('href').slice(1), a]));
    const tio = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) tocLinks.forEach((a) => a.classList.toggle('is-active', a === map.get(e.target.id))); });
    }, { rootMargin: '-30% 0px -60% 0px' });
    map.forEach((_, id) => { const s = document.getElementById(id); if (s) tio.observe(s); });
  }

  /* ---------- Lightbox ---------- */
  const lb = $('.lb');
  const items = $$('[data-lightbox]');
  if (lb && items.length) {
    const img = $('img', lb); const cap = $('.lb__cap', lb); let group = []; let idx = 0;
    const show = (i) => { idx = (i + group.length) % group.length; img.src = group[idx].href; img.alt = group[idx].dataset.cap || ''; cap.textContent = `${group[idx].dataset.cap || ''} · ${idx + 1} / ${group.length}`; };
    items.forEach((a) => a.addEventListener('click', (e) => {
      e.preventDefault();
      group = $$('[data-lightbox]', a.parentElement);
      show(group.indexOf(a));
      lb.showModal();
    }));
    $('.lb__x', lb).addEventListener('click', () => lb.close());
    $('.lb__prev', lb).addEventListener('click', () => show(idx - 1));
    $('.lb__next', lb).addEventListener('click', () => show(idx + 1));
    lb.addEventListener('click', (e) => { if (e.target === lb) lb.close(); });
    lb.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') show(idx - 1); if (e.key === 'ArrowRight') show(idx + 1); });
  }

  /* ---------- Cursor & magnetische Buttons ---------- */
  if (fine && !reduced) {
    const cur = $('.cursor'); const lab = $('span', cur);
    let x = -100; let y = -100; let tx = x; let ty = y; let run = false;
    const loop = () => {
      x += (tx - x) * 0.2; y += (ty - y) * 0.2;
      cur.style.setProperty('--x', x.toFixed(1) + 'px'); cur.style.setProperty('--y', y.toFixed(1) + 'px');
      if (Math.abs(tx - x) + Math.abs(ty - y) > 0.3) requestAnimationFrame(loop); else run = false;
    };
    addEventListener('pointermove', (e) => {
      tx = e.clientX; ty = e.clientY;
      const t = e.target.closest && e.target.closest('[data-cursor]');
      cur.classList.toggle('is-on', !!t && !document.querySelector('.is-dragging'));
      if (t) lab.textContent = t.dataset.cursor;
      if (!run) { run = true; requestAnimationFrame(loop); }
    }, { passive: true });
    $$('.btn, .rbtn, .hdr__burger-ico').forEach((b) => {
      b.addEventListener('pointermove', (e) => {
        const r = b.getBoundingClientRect();
        b.style.translate = `${((e.clientX - r.left - r.width / 2) * 0.18).toFixed(1)}px ${((e.clientY - r.top - r.height / 2) * 0.28).toFixed(1)}px`;
      });
      b.addEventListener('pointerleave', () => { b.style.transition = 'translate .6s cubic-bezier(.19,1,.22,1), color .4s, background .3s'; b.style.translate = ''; setTimeout(() => { b.style.transition = ''; }, 600); });
    });
  }

  /* ---------- Kontaktformular (öffnet E-Mail-Programm) ---------- */
  const form = $('[data-mailto]');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      let ok = true;
      $$('[required]', form).forEach((f) => { const bad = !f.value.trim(); f.classList.toggle('is-invalid', bad); if (bad && ok) { f.focus(); ok = false; } });
      const note = $('.kform__note', form);
      if (!ok) { note.textContent = 'Bitte füllen Sie die mit * markierten Felder aus.'; return; }
      const d = new FormData(form);
      const subject = `Anfrage ${d.get('bereich')} – ${d.get('name')}`;
      const body = `${d.get('nachricht')}\n\n—\nName: ${d.get('name')}\nTelefon: ${d.get('telefon') || '–'}\nBereich: ${d.get('bereich')}`;
      location.href = `mailto:${form.dataset.mailto}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      note.textContent = 'Ihr E-Mail-Programm wurde geöffnet. Bitte senden Sie die vorbereitete Nachricht dort ab.';
    });
  }
})();
