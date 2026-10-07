(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const body = document.body;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const EN = document.documentElement.lang === 'en';
  const T = EN ? {
    days: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    open: '● Open now – until 1 am', openShort: 'Open now · Celle',
    today: 'Open tonight from 8 pm', tomorrow: 'Open tomorrow from 8 pm', again: d => `Next opening: ${d} from 8 pm`, next: d => `Next time travel: ${d}`,
    nextToday: 'Next time travel: tonight from 8 pm', nextTomorrow: 'Next time travel: tomorrow from 8 pm', idle: 'Bar · Celle',
    party: 'Party mode', partyOff: 'Party off', map: 'Map: Bar Zeitreise, Hehlentorstraße 16, Celle',
    cdNext: 'Next time travel in', cdOpen: 'Open now – closing in'
  } : {
    days: ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'],
    open: '● Jetzt geöffnet – bis 01:00 Uhr', openShort: 'Jetzt geöffnet · Celle',
    today: 'Heute ab 20:00 Uhr geöffnet', tomorrow: 'Morgen ab 20:00 Uhr geöffnet', again: d => `Wieder geöffnet: ${d} ab 20:00 Uhr`, next: d => `Nächste Zeitreise: ${d}`,
    nextToday: 'Nächste Zeitreise: heute ab 20:00 Uhr', nextTomorrow: 'Nächste Zeitreise: morgen ab 20:00 Uhr', idle: 'Bar · Celle',
    party: 'Party-Modus', partyOff: 'Party aus', map: 'Karte: Bar Zeitreise, Hehlentorstraße 16, Celle',
    cdNext: 'Nächste Zeitreise in', cdOpen: 'Jetzt geöffnet – schließt in'
  };
  const store = {
    get: k => { try { return localStorage.getItem(k); } catch { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch {} }
  };

  /* ---------- Jahrzehnt-Umschalter ---------- */
  function setEra(e) {
    body.dataset.era = e;
    $$('[data-era-panel]').forEach(p => p.hidden = p.dataset.eraPanel !== e);
    $$('.tabs [data-era]').forEach(b => b.setAttribute('aria-pressed', b.dataset.era === e));
    $$('.decades [data-era]').forEach(b => b.classList.toggle('on', b.dataset.era === e));
    store.set('zr-era', e);
  }
  $$('[data-era]').forEach(b => b.matches('button') && b.addEventListener('click', () => setEra(b.dataset.era)));
  const saved = store.get('zr-era');
  setEra(['70', '80', '90'].includes(saved) ? saved : '80');

  /* ---------- Öffnungsstatus (Fr/Sa 20–01 Uhr, Europe/Berlin) ---------- */
  const OPEN = { 5: 1, 6: 1 }; // Tage mit Öffnung; Ende am Folgetag 01:00
  const DAYS = T.days;
  function berlinNow() {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Europe/Berlin', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).formatToParts(new Date()).map(x => [x.type, x.value]));
    const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(p.weekday);
    const min = (+p.hour % 24) * 60 + +p.minute;
    return { day, min, sec: min * 60 + +p.second };
  }
  function updateStatus() {
    const { day, min } = berlinNow();
    const prev = (day + 6) % 7;
    const openNow = (OPEN[day] && min >= 1200) || (OPEN[prev] && min < 60);
    const st = $('#status'), dot = $('#liveDot'), txt = $('#liveText');
    let msg, short;
    if (openNow) {
      msg = T.open; short = T.openShort;
    } else {
      let add = 0;
      for (let i = 0; i < 8; i++) {
        const d = (day + i) % 7;
        if (OPEN[d] && (i > 0 || min < 1200)) { add = i; break; }
      }
      const d = DAYS[(day + add) % 7];
      msg = add === 0 ? T.today : add === 1 ? T.tomorrow : T.again(d);
      short = add === 0 ? T.nextToday : add === 1 ? T.nextTomorrow : T.next(`${d}${EN ? ' from 8 pm' : ' ab 20:00 Uhr'}`);
    }
    st.textContent = msg;
    st.classList.toggle('open', !!openNow);
    dot.classList.toggle('on', !!openNow);
    txt.textContent = short;
    const today = openNow && !(OPEN[day] && min >= 1200) ? prev : day;
    $$('#hours tr').forEach(li => li.classList.toggle('today', +li.dataset.d === today));
  }
  updateStatus();
  setInterval(updateStatus, 60000);

  /* ---------- Countdown bis Öffnung / Schließung ---------- */
  const cd = $('#countdown');
  if (cd) {
    const W = 604800, H = 3600;
    const spans = [[5 * 86400 + 20 * H, 6 * 86400 + H], [6 * 86400 + 20 * H, 7 * 86400 + H]];
    const pad = n => String(n).padStart(2, '0');
    const tick = () => {
      const { day, sec } = berlinNow();
      const now = day * 86400 + sec;
      let open = false, target = Infinity;
      for (const off of [0, W]) for (const [s, e] of spans) {
        if (now + off >= s && now + off < e) { open = true; target = e - (now + off); }
        else if (!open && s > now + off) target = Math.min(target, s - (now + off));
      }
      if (!open) for (const [s] of spans) if (s > now) target = Math.min(target, s - now);
      const d = Math.floor(target / 86400), h = Math.floor(target % 86400 / H), m = Math.floor(target % H / 60), s2 = target % 60;
      $('#cdD').textContent = pad(d); $('#cdH').textContent = pad(h); $('#cdM').textContent = pad(m); $('#cdS').textContent = pad(s2);
      $('#cdLabel').textContent = open ? T.cdOpen : T.cdNext;
      cd.classList.toggle('open', open);
    };
    tick(); setInterval(tick, 1000);
  }

  /* ---------- Zeitmaschine: Jahre laufen beim Scrollen ---------- */
  const tw = $('#zeitreise');
  if (tw && !reduce) {
    const yearEl = $('#twYear'), fill = $('#twFill'), imgs = $$('.tw-imgs img', tw), lis = $$('.tw-eras li', tw);
    let near = false, queued = false, lastYear = 0;
    new IntersectionObserver(es => { near = es[0].isIntersecting; if (near) onScroll(); }, { rootMargin: '20% 0px' }).observe(tw);
    const paint = () => {
      queued = false;
      const r = tw.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
      const year = 1970 + Math.min(29, Math.floor(p * 30));
      fill.style.setProperty('--p', p.toFixed(3));
      if (year === lastYear) return;
      lastYear = year; yearEl.textContent = year;
      const era = year < 1980 ? 0 : year < 1990 ? 1 : 2;
      tw.dataset.tw = ['70', '80', '90'][era];
      imgs.forEach((im, i) => im.classList.toggle('on', i === era));
      lis.forEach((li, i) => li.classList.toggle('on', i === era));
    };
    function onScroll() { if (near && !queued) { queued = true; requestAnimationFrame(paint); } }
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll);
  }

  /* ---------- Reveal + Zähler ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in');
    $$('[data-count]', e.target).forEach(countUp);
    io.unobserve(e.target);
  }), { threshold: .15 });
  $$('.reveal').forEach(el => io.observe(el));
  function countUp(el) {
    const to = +el.dataset.count;
    if (reduce) { el.textContent = to; return; }
    const t0 = performance.now();
    (function f(t) {
      const k = Math.min(1, (t - t0) / 1200);
      el.textContent = Math.round(to * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(f);
    })(t0);
  }

  /* ---------- Events: vergangene Termine ausblenden ---------- */
  (() => {
    const t = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Berlin' }).format(new Date());
    let left = 0;
    $$('#eventList .event[data-date]').forEach(li => { if (li.dataset.date < t) li.hidden = true; else left++; });
    $('#eventsEmpty').hidden = left > 0;
  })();

  /* ---------- Lightbox ---------- */
  const lb = $('#lb');
  $$('.gallery button').forEach(b => b.addEventListener('click', () => {
    const img = $('img', lb); img.src = b.dataset.full; img.alt = $('img', b).alt;
    lb.showModal();
  }));
  lb.addEventListener('click', e => { if (e.target !== $('img', lb)) lb.close(); });

  /* ---------- Karte erst nach Klick laden (DSGVO) ---------- */
  $('#mapBtn').addEventListener('click', () => {
    const f = document.createElement('iframe');
    f.title = T.map;
    f.referrerPolicy = 'no-referrer';
    f.src = 'https://www.openstreetmap.org/export/embed.html?bbox=10.0755%2C52.6235%2C10.0825%2C52.6275&layer=mapnik&marker=52.6255%2C10.079';
    $('#map').append(f); $('#map').classList.add('on');
  });

  /* ---------- PARTY-MODUS ---------- */
  const partyBtn = $('#partyBtn'), soundBtn = $('#soundBtn'), cv = $('#confetti');
  const ctx2d = cv.getContext('2d');
  let soundOn = false, partyOn = false, raf = 0, parts = [], beatT = 0, lastBeat = 0;
  const BPM = 118, STEP = 60 / BPM;

  function resize() { cv.width = innerWidth; cv.height = innerHeight; }
  addEventListener('resize', () => partyOn && resize());

  function burst(n = 120) {
    const cols = ['#ff2fb3', '#2ff3ff', '#ffd23f', '#7cff4f', '#a855ff', '#fff'];
    for (let i = 0; i < n; i++) parts.push({
      x: Math.random() * cv.width, y: -20 - Math.random() * cv.height * .4,
      vx: (Math.random() - .5) * 3, vy: 2 + Math.random() * 4,
      w: 6 + Math.random() * 6, h: 4 + Math.random() * 6, r: Math.random() * 6,
      vr: (Math.random() - .5) * .3, c: cols[i % cols.length]
    });
  }
  function loop(t) {
    if (!partyOn && !parts.length) { ctx2d.clearRect(0, 0, cv.width, cv.height); return; }
    raf = requestAnimationFrame(loop);
    ctx2d.clearRect(0, 0, cv.width, cv.height);
    // Beat-Puls: mit Audio synchron, sonst per Uhr
    const now = soundOn ? audio.currentTime : t / 1000;
    const phase = ((now - beatT) / STEP) % 1;
    const pulse = partyOn ? Math.pow(1 - (phase < 0 ? phase + 1 : phase), 3) : 0;
    body.style.setProperty('--beat', pulse.toFixed(3));
    if (partyOn && parts.length < 90 && Math.floor((now - beatT) / STEP / 8) !== lastBeat) { lastBeat = Math.floor((now - beatT) / STEP / 8); burst(40); }
    parts = parts.filter(p => p.y < cv.height + 20);
    for (const p of parts) {
      p.x += p.vx + Math.sin(p.y / 40); p.y += p.vy; p.r += p.vr;
      ctx2d.save(); ctx2d.translate(p.x, p.y); ctx2d.rotate(p.r);
      ctx2d.fillStyle = p.c; ctx2d.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); ctx2d.restore();
    }
    if (!partyOn && !parts.length) body.style.setProperty('--beat', 0);
  }

  function setParty(on) {
    partyOn = on;
    body.classList.toggle('party', on);
    partyBtn.setAttribute('aria-pressed', on);
    $('.lbl', partyBtn).textContent = on ? T.partyOff : T.party;
    soundBtn.hidden = !on;
    if (on) {
      beatT = performance.now() / 1000;
      resize(); burst(160); cancelAnimationFrame(raf); raf = requestAnimationFrame(loop);
    } else {
      setSound(false);
    }
  }
  const spot = $('#spot');
  let spotQ = false, sx = 0, sy = 0;
  addEventListener('pointermove', e => {
    if (!partyOn || reduce || spotQ) return;
    sx = e.clientX; sy = e.clientY; spotQ = true;
    requestAnimationFrame(() => { spotQ = false; spot.style.setProperty('--mx', sx + 'px'); spot.style.setProperty('--my', sy + 'px'); });
  }, { passive: true });
  partyBtn.addEventListener('click', () => { setParty(!partyOn); if (partyOn && navigator.vibrate) navigator.vibrate([40, 30, 40]); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && partyOn) setParty(false); });
  // Reduzierte Bewegung: Party-Modus nur als Farbwechsel ohne Dauer-Animation (CSS erledigt das)

  /* ---------- Synth-Beat (WebAudio, nur nach Klick) ---------- */
  let audio = null, timer = 0, nextT = 0, step = 0, master = null;
  function kick(t) {
    const o = audio.createOscillator(), g = audio.createGain();
    o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(40, t + .12);
    g.gain.setValueAtTime(.9, t); g.gain.exponentialRampToValueAtTime(.001, t + .3);
    o.connect(g).connect(master); o.start(t); o.stop(t + .32);
  }
  function hat(t, v = .12) {
    const len = audio.sampleRate * .05, buf = audio.createBuffer(1, len, audio.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
    const s = audio.createBufferSource(), f = audio.createBiquadFilter(), g = audio.createGain();
    s.buffer = buf; f.type = 'highpass'; f.frequency.value = 7000; g.gain.value = v;
    s.connect(f).connect(g).connect(master); s.start(t);
  }
  function bass(t, n) {
    const o = audio.createOscillator(), f = audio.createBiquadFilter(), g = audio.createGain();
    o.type = 'sawtooth'; o.frequency.value = n; f.type = 'lowpass'; f.frequency.value = 600;
    g.gain.setValueAtTime(.22, t); g.gain.exponentialRampToValueAtTime(.001, t + STEP / 2 * .9);
    o.connect(f).connect(g).connect(master); o.start(t); o.stop(t + STEP / 2);
  }
  const NOTES = [55, 55, 82.4, 55, 65.4, 65.4, 98, 73.4]; // A-A-E-A-C-C-G-D
  function schedule() {
    while (nextT < audio.currentTime + .2) {
      const s = step % 16;
      if (s % 4 === 0) kick(nextT);
      if (s % 4 === 2) hat(nextT, .16); else hat(nextT, .05);
      if (s % 2 === 0) bass(nextT, NOTES[(s / 2) % 8]);
      nextT += STEP / 4; step++;
    }
  }
  function setSound(on) {
    soundOn = on;
    soundBtn.setAttribute('aria-pressed', on);
    clearInterval(timer);
    if (!on) beatT = performance.now() / 1000;
    if (on) {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      if (!master) { master = audio.createGain(); master.gain.value = .5; master.connect(audio.destination); }
      audio.resume();
      step = 0; nextT = audio.currentTime + .05; beatT = nextT;
      timer = setInterval(schedule, 50);
    } else if (audio) {
      audio.suspend();
    }
  }
  soundBtn.addEventListener('click', () => setSound(soundBtn.getAttribute('aria-pressed') !== 'true'));
})();
