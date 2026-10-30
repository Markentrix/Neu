/* Markentrix · Chat-Assistent (regelbasiert, ohne KI).
 * Zwei Modi: (1) KI-Modus, wenn /api/chat.php aktiv ist (Schlüssel auf dem Server) und der Besucher zugestimmt hat: Die KI antwortet
 * ausschließlich anhand der Wissensbasis. (2) Vorgefertigte Antworten ohne KI aus /assets/chat-data.json (FAQ-Seite plus Handtexte),
 * auch als Rückfall bei Fehlern, Limits oder ohne Zustimmung. Im Modus ohne KI bleiben Eingaben im Browser.
 * Nur wenn Besucher das Formular im Chat absenden, gehen Name, E-Mail und Frage an /api/anfrage.php.
 * Für Besucher klar gekennzeichnet (KI oder automatischer Assistent ohne KI). */
(function (w, d) {
  'use strict';
  if (!d.querySelector || !w.fetch) return;
  var script = d.currentScript, VER = (script && /[?&]v=([\w-]+)/.exec(script.src) || [])[1] || '';
  var DATA = null, loading = null, built = false, lastText = '';
  var root, launcher, panel, log, input, form, subEl, footEl, footLink;
  var mode = 'rule', hist = [], aiCount = 0, noticed = false;

  function el(tag, cls, text) { var e = d.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function track(name, p) { try { if (typeof w.gtag === 'function') w.gtag('event', name, p || {}); } catch (e) { } }

  /* ── Textvergleich ──────────────────────────────────────────────────── */
  var STOP = ' der die das den dem des ein eine einen einem einer und oder ist sind war wird werden hat haben habe ich sie wir ihr ihre ihren ihrer mein meine meinen mir mich dir sich zu zum zur von vom mit bei fuer auf in im an am um als wie was wo wer wann wieso warum welche welcher welches kann koennen koennt moechte moechten gibt es nicht auch noch dann dass bitte mal ob so nur aus nach ueber unter bis ab muss soll man mehr sehr gerne ';
  function norm(s) {
    s = String(s).toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss');
    if (s.normalize) s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    return s.replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function stem(t) { return t.length > 5 ? t.replace(/(ten|en|er|es|em|st|te|e|n|s|t)$/, '') : t; }
  function tokens(s) { return norm(s).split(' ').filter(function (t) { return t && STOP.indexOf(' ' + t + ' ') < 0; }); }
  function same(a, b) { return a === b || (a.length >= 5 && b.length >= 5 && (a.indexOf(b) >= 0 || b.indexOf(a) >= 0)); }

  function score(entry, text, toks) {
    var full = ' ' + norm(text) + ' ', s = 0, hit = {};
    (entry.kw || []).forEach(function (k) {
      var nk = norm(k); if (!nk) return;
      if (nk.indexOf(' ') > 0) { if (full.indexOf(' ' + nk + ' ') >= 0) s += 3; return; }
      var sk = stem(nk);
      for (var i = 0; i < toks.length; i++) { if (same(stem(toks[i]), sk)) { s += 2; hit[toks[i]] = 1; break; } }
    });
    tokens(entry.q).forEach(function (qt) {
      var sq = stem(qt);
      for (var i = 0; i < toks.length; i++) { if (same(stem(toks[i]), sq)) { s += 1.5; break; } }
    });
    return s;
  }
  function search(text) {
    var toks = tokens(text), out = [];
    if (!toks.length) return out;
    DATA.entries.forEach(function (e) { var s = score(e, text, toks); if (s > 0) out.push({ e: e, s: s }); });
    out.sort(function (a, b) { return b.s - a.s; });
    return out;
  }

  /* ── Darstellung ────────────────────────────────────────────────────── */
  function scroll() { log.scrollTop = log.scrollHeight; }
  function bubble(who, node) {
    var row = el('div', 'chat-msg chat-msg--' + who);
    row.appendChild(el('span', 'sr-only', who === 'me' ? 'Sie: ' : 'Assistent: '));
    row.appendChild(node); log.appendChild(row); scroll(); return row;
  }
  function say(text) { return bubble('bot', el('p', null, text)); }
  function linkBtn(l) {
    var a = el('a', 'chat-link', l.label); a.href = l.href;
    if (l.ext) { a.target = '_blank'; a.rel = 'noopener'; a.setAttribute('aria-label', l.label + ' (öffnet in neuem Tab)'); }
    return a;
  }
  function links(arr) { if (!arr || !arr.length) return; var box = el('div', 'chat-links'); arr.forEach(function (l) { box.appendChild(linkBtn(l)); }); bubble('bot', box).classList.add('chat-msg--plain'); }
  function chips(arr) {
    var box = el('div', 'chat-chips'); box.setAttribute('role', 'group'); box.setAttribute('aria-label', 'Vorschläge');
    arr.forEach(function (c) { var b = el('button', 'chat-chip', c.label); b.type = 'button'; b.addEventListener('click', function () { c.run(); }); box.appendChild(b); });
    bubble('bot', box).classList.add('chat-msg--plain');
  }
  function answer(e) { say(e.a); links(e.links); }
  function entryById(id) { for (var i = 0; i < DATA.entries.length; i++) if (DATA.entries[i].id === id) return DATA.entries[i]; return null; }
  var START = ['faq-1', 'ablauf', 'faq-2', 'kontakt', 'erstberatung'];
  function startChips() {
    chips(START.map(function (id) { var e = entryById(id); return e ? { label: e.q, run: function () { ask(e.q, e); } } : null; }).filter(Boolean));
  }

  function fallback() {
    say('Dazu habe ich keine sichere Antwort. Am besten klären wir das persönlich. Sie können Ihre Frage an uns senden, dann antwortet Christian Wien werktags innerhalb von 24 Stunden, oder Sie erreichen uns direkt.');
    chips([{ label: 'Frage an uns senden', run: openForm }]);
    links([{ label: 'Anrufen: 0176 20370429', href: 'tel:+4917620370429' }, { label: 'WhatsApp', href: 'https://wa.me/4917620370429?text=Hallo%20Markentrix%2C%20ich%20habe%20eine%20Frage%20zu%20meiner%20Website.', ext: true }]);
  }

  function ask(text, forced) {
    text = String(text).replace(/\s+/g, ' ').trim().slice(0, 200); if (!text) return;
    lastText = text;
    bubble('me', el('p', null, text));
    var n = norm(text);
    if (!forced) {
      if (/^(hallo|hi|hey|moin|servus|guten (tag|morgen|abend))( |$)/.test(n) && n.split(' ').length <= 4) { say('Guten Tag! Wobei kann ich helfen? Wählen Sie eine Frage oder schreiben Sie Ihre eigene.'); startChips(); return; }
      if (/^(danke|vielen dank|dankeschoen|super|prima|perfekt|alles klar|ok|okay)( |$)/.test(n) && n.split(' ').length <= 4) { say('Gern geschehen! Wenn noch etwas offen ist, fragen Sie einfach weiter.'); return; }
      if (/^(tschuess|tschues|auf wiedersehen|ciao|bye)( |$)/.test(n)) { say('Auf Wiedersehen, und melden Sie sich gern, wenn Sie Fragen haben.'); return; }
    }
    if (!forced && mode === 'ai') { askAI(text); return; }
    ruleAnswer(text, forced);
  }
  function ruleAnswer(text, forced) {
    var res = forced ? [{ e: forced, s: 99 }] : search(text), best = res[0];
    track('chat_question', { treffer: best && best.s >= 2 ? best.e.id : 'keiner' });
    if (best && best.s >= 3.5) { answer(best.e); return; }
    if (best && best.s >= 2) {
      say('Meinen Sie eine dieser Fragen?');
      var cands = res.filter(function (r) { return r.s >= Math.max(2, best.s - 1.5); }).slice(0, 3);
      chips(cands.map(function (r) { return { label: r.e.q, run: function () { ask(r.e.q, r.e); } }; }).concat([{ label: 'Keine davon', run: fallback }]));
      return;
    }
    fallback();
  }

  /* ── KI-Modus ───────────────────────────────────────────────────────── */
  var PHONE = [{ label: 'Anrufen: 0176 20370429', href: 'tel:+4917620370429' }];
  function typing() { var row = bubble('bot', el('p', 'chat-typing', 'Der Assistent schreibt …')); return row; }
  function toRule(why) {
    mode = 'rule'; setSub();
    if (why && !noticed) { noticed = true; say(why); }
  }
  function askAI(text) {
    if (aiCount >= 20) { toRule('Sie haben viele Fragen gestellt, ich antworte ab jetzt mit vorgefertigten Antworten ohne KI.'); ruleAnswer(text); return; }
    aiCount++; hist.push({ role: 'user', content: text });
    var wait = typing(), done = false;
    var timer = setTimeout(function () { if (!done) { wait.remove(); } }, 24000);
    fetch('/api/chat.php', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: hist.slice(-6) }) })
      .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'server' }; }); })
      .then(function (j) {
        done = true; clearTimeout(timer); wait.remove();
        if (j && j.ok && j.answer) {
          hist.push({ role: 'assistant', content: j.answer });
          track('chat_question', { treffer: j.handoff ? 'weiterleitung' : 'ki' });
          say(j.answer); links(j.links);
          if (j.handoff) { chips([{ label: 'Frage an uns senden', run: openForm }]); links(PHONE); }
          return;
        }
        var err = j && j.error;
        hist.pop();
        if (err === 'rate') { say('Sie haben in kurzer Zeit viele Fragen gestellt. Bitte versuchen Sie es später noch einmal oder erreichen Sie uns direkt.'); links(PHONE); toRule(); return; }
        if (err === 'disabled' || err === 'busy') toRule('Der KI-Assistent ist gerade nicht verfügbar. Ich antworte mit vorgefertigten Antworten ohne KI.');
        ruleAnswer(text);
      })
      .catch(function () { done = true; clearTimeout(timer); wait.remove(); hist.pop(); ruleAnswer(text); });
  }
  function aiGreeting() {
    say('Guten Tag! Ich bin der KI-Assistent von Markentrix und beantworte Fragen zu Websites, Preisen, Ablauf und Datenschutz. Ich antworte nur anhand der Informationen dieser Website. Wählen Sie eine Frage oder schreiben Sie Ihre eigene.');
    startChips();
  }
  function ruleGreeting() {
    say('Guten Tag! Ich beantworte Fragen zu Websites, Preisen, Ablauf und Datenschutz. Wählen Sie eine Frage oder schreiben Sie Ihre eigene.');
    startChips();
  }
  function consentGate() {
    var box = el('div', 'chat-gate');
    box.appendChild(el('p', null, 'Dieser Chat kann von einer KI beantwortet werden. Sie schreiben dann mit einer KI, nicht mit einem Menschen. Ihre Nachrichten werden dazu an unseren KI-Dienstleister in den USA übermittelt (Auftragsverarbeitung, Details in der Datenschutzerklärung). Bitte geben Sie keine sensiblen Daten ein.'));
    var a = el('a', null, 'Datenschutzerklärung lesen'); a.href = '/datenschutz#chat-assistent'; var pp = el('p'); pp.appendChild(a); box.appendChild(pp);
    var row = bubble('bot', box); row.classList.add('chat-msg--plain', 'chat-msg--wide');
    chips([
      { label: 'Einverstanden, mit KI chatten', run: function () { try { sessionStorage.setItem('mx-chat-ai', '1'); } catch (e) { } mode = 'ai'; setSub(); track('chat_ki_start'); aiGreeting(); } },
      { label: 'Ohne KI: vorgefertigte Antworten', run: function () { mode = 'rule'; setSub(); ruleGreeting(); } }
    ]);
  }
  function aiAvailable() {
    var ctrl = ('AbortController' in w) ? new AbortController() : null, timer = ctrl && setTimeout(function () { ctrl.abort(); }, 3500);
    return fetch('/api/chat.php?status=1', { signal: ctrl ? ctrl.signal : undefined }).then(function (r) { return r.json(); }).then(function (j) { clearTimeout(timer); return !!(j && j.ok && j.enabled); }).catch(function () { return false; });
  }

  /* ── Frage an uns senden (Formular im Chat) ─────────────────────────── */
  function openForm() {
    var box = el('form', 'chat-form'); box.noValidate = true;
    var id = 'chat-f' + Date.now();
    function field(label, name, type, auto, req) {
      var wrap = el('div', 'chat-field'), l = el('label', null, label); l.setAttribute('for', id + name);
      var i = type === 'textarea' ? el('textarea') : el('input'); if (type !== 'textarea') i.type = type;
      i.id = id + name; i.name = name; if (auto) i.autocomplete = auto; if (req) i.required = true; if (type === 'textarea') i.rows = 3; i.maxLength = type === 'textarea' ? 1000 : 120;
      wrap.appendChild(l); wrap.appendChild(i); box.appendChild(wrap); return i;
    }
    var fn = field('Name', 'name', 'text', 'name', true), fe = field('E-Mail', 'email', 'email', 'email', true), ft = field('Ihre Frage', 'frage', 'textarea', '', true);
    ft.value = lastText;
    var hp = el('div', 'hp'); hp.setAttribute('aria-hidden', 'true'); var hl = el('label', null, 'Website (bitte leer lassen)'); hl.setAttribute('for', id + 'web'); var hi = el('input'); hi.id = id + 'web'; hi.name = 'website'; hi.tabIndex = -1; hi.autocomplete = 'off'; hp.appendChild(hl); hp.appendChild(hi); box.appendChild(hp);
    var cl = el('label', 'chat-check'), cb = el('input'); cb.type = 'checkbox'; cb.name = 'einwilligung'; cb.required = true;
    var ct = el('span'); ct.appendChild(d.createTextNode('Ich willige ein, dass meine Angaben zur Beantwortung meiner Frage verarbeitet werden. Details in der '));
    var dl = el('a', null, 'Datenschutzerklärung'); dl.href = '/datenschutz#chat-assistent'; ct.appendChild(dl); ct.appendChild(d.createTextNode('. Die Einwilligung ist jederzeit widerrufbar.'));
    cl.appendChild(cb); cl.appendChild(ct); box.appendChild(cl);
    var msg = el('div', 'chat-formmsg'); msg.setAttribute('role', 'alert'); box.appendChild(msg);
    var send = el('button', 'btn btn--primary btn--sm', 'Frage senden'); send.type = 'submit'; box.appendChild(send);
    var row = bubble('bot', box); row.classList.add('chat-msg--plain', 'chat-msg--wide'); fn.focus();
    box.addEventListener('submit', function (ev) {
      ev.preventDefault(); msg.textContent = '';
      if (!fn.value.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(fe.value.trim()) || !ft.value.trim()) { msg.textContent = 'Bitte Name, eine gültige E-Mail-Adresse und Ihre Frage angeben.'; return; }
      if (!cb.checked) { msg.textContent = 'Bitte stimmen Sie der Verarbeitung Ihrer Angaben zu.'; return; }
      send.disabled = true; send.textContent = 'Wird gesendet …';
      var payload = { quelle: 'Chat', name: fn.value.trim(), email: fe.value.trim(), thema: 'Frage über den Chat-Assistenten', nachricht_text: ft.value.trim(), einwilligung: 'ja', seite: location.pathname, website: hi.value };
      fetch('/api/anfrage.php', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
        .then(function (j) {
          if (j && j.ok) { track('generate_lead', { channel: 'Chat' }); row.remove(); say('Danke, Ihre Frage ist bei uns eingegangen. Wir melden uns werktags innerhalb von 24 Stunden. Eine Bestätigung geht an Ihre E-Mail-Adresse.'); }
          else { send.disabled = false; send.textContent = 'Frage senden'; msg.textContent = 'Das hat leider nicht geklappt. Bitte versuchen Sie es noch einmal oder rufen Sie an: 0176 20370429.'; }
        })
        .catch(function () { send.disabled = false; send.textContent = 'Frage senden'; msg.textContent = 'Die Verbindung ist abgebrochen. Bitte versuchen Sie es noch einmal oder rufen Sie an: 0176 20370429.'; });
    });
  }

  /* ── Aufbau, Öffnen, Schließen ──────────────────────────────────────── */
  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (!loading) loading = fetch('/assets/chat-data.json' + (VER ? '?v=' + VER : '')).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) { DATA = j; return j; });
    return loading;
  }
  function setSub() {
    if (!subEl) return;
    if (footEl) footEl.firstChild.nodeValue = mode === 'ai' ? 'Im KI-Modus gehen Ihre Nachrichten zur Beantwortung an unseren KI-Dienstleister, wir speichern sie nicht. Das Frageformular sendet Ihre Angaben an uns. ' : 'Ihre Eingaben bleiben in Ihrem Browser. Nur wenn Sie das Formular absenden, erhalten wir Ihre Angaben. ';
    subEl.textContent = mode === 'ai' ? 'KI-Assistent. Sie schreiben mit einer KI, nicht mit einem Menschen. Antworten können Fehler enthalten.' : 'Automatischer Assistent, keine KI. Die Antworten stammen aus den Seiten dieser Website.';
  }
  function build() {
    built = true;
    panel = el('section', 'chat-panel'); panel.id = 'mx-chat'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'false'); panel.setAttribute('aria-labelledby', 'mx-chat-title'); panel.hidden = true;
    var head = el('div', 'chat-head'), ht = el('div'); var h = el('h2', null, 'Fragen an Markentrix'); h.id = 'mx-chat-title';
    subEl = el('p', null, ''); setSub(); ht.appendChild(h); ht.appendChild(subEl);
    var close = el('button', 'chat-close'); close.type = 'button'; close.setAttribute('aria-label', 'Chat schließen'); close.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    close.addEventListener('click', closePanel); head.appendChild(ht); head.appendChild(close);
    log = el('div', 'chat-log'); log.setAttribute('role', 'log'); log.setAttribute('aria-live', 'polite'); log.tabIndex = 0; log.setAttribute('aria-label', 'Gespräch');
    form = el('form', 'chat-input'); form.noValidate = true;
    var lab = el('label', 'sr-only', 'Ihre Frage'); lab.setAttribute('for', 'mx-chat-q');
    input = el('input'); input.id = 'mx-chat-q'; input.type = 'text'; input.maxLength = 200; input.autocomplete = 'off'; input.placeholder = 'Ihre Frage';
    var go = el('button', 'chat-send', 'Senden'); go.type = 'submit';
    form.appendChild(lab); form.appendChild(input); form.appendChild(go);
    form.addEventListener('submit', function (ev) { ev.preventDefault(); var v = input.value; input.value = ''; ask(v); input.focus(); });
    var foot = el('p', 'chat-foot'); footEl = foot; foot.appendChild(d.createTextNode('Ihre Eingaben bleiben in Ihrem Browser. Nur wenn Sie das Formular absenden, erhalten wir Ihre Angaben. '));
    var fl = el('a', null, 'Datenschutz'); fl.href = '/datenschutz#chat-assistent'; foot.appendChild(fl);
    panel.appendChild(head); panel.appendChild(log); panel.appendChild(form); panel.appendChild(foot);
    d.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && panel && !panel.hidden) { closePanel(); } });
    d.body.appendChild(panel);
  }
  function openPanel() {
    if (!built) build();
    launcher.setAttribute('aria-expanded', 'true'); launcher.hidden = true; panel.hidden = false;
    track('chat_open');
    load().then(function () { return log.firstChild ? false : aiAvailable(); }).then(function (ai) {
      if (!log.firstChild) {
        var ok = false; try { ok = sessionStorage.getItem('mx-chat-ai') === '1'; } catch (e) { }
        if (ai && ok) { mode = 'ai'; setSub(); aiGreeting(); }
        else if (ai) consentGate();
        else ruleGreeting();
      }
      input.focus();
    }).catch(function () {
      if (!log.firstChild) { say('Der Assistent ist gerade nicht erreichbar. Sie erreichen uns telefonisch unter 0176 20370429 oder über das Kontaktformular.'); links([{ label: 'Zum Kontaktformular', href: '/kontakt' }]); }
    });
  }
  function closePanel() { panel.hidden = true; launcher.hidden = false; launcher.setAttribute('aria-expanded', 'false'); launcher.focus(); }

  function init() {
    if (d.querySelector('.mx-chat-launcher')) return;
    launcher = el('button', 'mx-chat-launcher'); launcher.type = 'button'; launcher.setAttribute('aria-expanded', 'false'); launcher.setAttribute('aria-controls', 'mx-chat'); launcher.setAttribute('aria-haspopup', 'dialog');
    launcher.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.4A8 8 0 1 1 21 12z"/></svg><span>Fragen?</span>';
    launcher.addEventListener('click', openPanel); d.body.appendChild(launcher);
    root = launcher;
    // Seitenlinks "Chat öffnen" (data-open-chat) funktionieren ebenfalls
    d.addEventListener('click', function (ev) { var t = ev.target.closest && ev.target.closest('[data-open-chat]'); if (t) { ev.preventDefault(); if (!panel || panel.hidden) openPanel(); } });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', init); else init();
})(window, document);
