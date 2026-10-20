/* Vorschau-Entwurf: setzt die Angaben aus dem Fragment der Adresse (#d=<JSON>) ein. Das Fragment verlässt den Browser nicht. */
(function () {
  var d = document, root = d.documentElement;
  function clean(s, max) { return String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f<>]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max); }
  function read() {
    var m = /[#&]d=([^&]*)/.exec(location.hash || ''), o = {};
    if (m) { try { o = JSON.parse(decodeURIComponent(m[1])) || {}; } catch (e) { o = {}; } }
    var l = Array.isArray(o.l) ? o.l.map(function (x) { return clean(x, 45); }).filter(Boolean).slice(0, 6) : [];
    return { n: clean(o.n, 60), h: clean(o.h, 110), b: clean(o.b, 220), l: l, t: clean(o.t, 24).replace(/[^0-9+()\/\-. ]/g, ''), o: clean(o.o, 40), a: clean(o.a, 90), s: /^(handwerk|praxis|gastro)$/.test(o.s) ? o.s : 'handwerk' };
  }
  function initials(n) {
    var w = n.split(' ').filter(function (x) { return /[A-Za-zÄÖÜäöüß]/.test(x); });
    if (!w.length) return 'VS';
    var a = w[0].replace(/[^A-Za-zÄÖÜäöüß]/g, ''), b = w[1] ? w[1].replace(/[^A-Za-zÄÖÜäöüß]/g, '') : '';
    return (a.charAt(0) + (b ? b.charAt(0) : a.charAt(1))).toUpperCase();
  }
  function q(s) { return d.querySelector(s); }
  function set(s, v) { var e = q(s); if (e) e.textContent = v; }
  function show(s, on) { var e = q(s); if (e) e.hidden = !on; }
  function li(ul, t) { var e = d.createElement('li'); e.textContent = t; ul.appendChild(e); }
  function render() {
    var p = read(), name = p.n || 'Ihr Betrieb', ini = initials(name);
    root.setAttribute('data-t', p.s);
    d.title = name + ' · Vorschau (Entwurf)';
    set('[data-name]', name); set('[data-mark]', ini); set('[data-badge]', ini); set('[data-card-name]', name); set('[data-foot-name]', name);
    set('[data-headline]', p.h || name);
    set('[data-lead]', p.b); show('[data-lead]', !!p.b);
    set('[data-eyebrow]', p.o ? 'In ' + p.o : ''); show('[data-eyebrow]', !!p.o);
    set('[data-card-meta]', [p.o, p.t].filter(Boolean).join(' · ') || 'Anfragen jederzeit per Formular');
    set('[data-foot-addr]', p.a ? ' · ' + p.a : '');
    var call = q('[data-call]');
    if (call) { if (p.t) { call.textContent = p.t; call.setAttribute('href', 'tel:' + p.t.replace(/[^0-9+]/g, '')); } else { call.textContent = 'Anfrage senden'; call.setAttribute('href', '#kontakt'); } }
    var proof = q('[data-proof]'); proof.textContent = '';
    if (p.o) li(proof, 'Ihr Ansprechpartner in ' + p.o);
    if (p.t) li(proof, 'Direkt erreichbar: ' + p.t);
    li(proof, 'Anfrage per Formular, ohne Anmeldung');
    var cards = q('[data-cards]'); cards.textContent = '';
    p.l.forEach(function (t, i) {
      var a = d.createElement('a'); a.className = 'card'; a.href = '#kontakt';
      var n = d.createElement('span'); n.className = 'num'; n.textContent = (i < 9 ? '0' : '') + (i + 1);
      var h = d.createElement('h3'); h.textContent = t;
      var s = d.createElement('span'); s.className = 'go'; s.textContent = 'Anfrage dazu stellen';
      a.appendChild(n); a.appendChild(h); a.appendChild(s); cards.appendChild(a);
    });
    show('[data-sec-leistungen]', p.l.length > 0); show('[data-more]', p.l.length > 0); show('[data-nav-leistungen]', p.l.length > 0);
    var sel = q('[data-select]'); sel.textContent = '';
    p.l.concat(p.l.length ? ['Etwas anderes'] : []).forEach(function (t) { var o = d.createElement('option'); o.textContent = t; sel.appendChild(o); });
    show('[data-select-wrap]', p.l.length > 0);
    var facts = q('[data-facts]'); facts.textContent = '';
    if (p.t) li(facts, 'Telefon: ' + p.t);
    if (p.a) li(facts, 'Adresse: ' + p.a); else if (p.o) li(facts, 'Ort: ' + p.o);
    set('[data-ribbon]', 'Vorschau von Markentrix für ' + name + ', aus den öffentlichen Angaben Ihrer Seite zusammengestellt. Formular und Texte sind ein Entwurf, nichts davon ist live.');
  }
  render(); window.addEventListener('hashchange', render);
  var f = q('[data-demo-form]');
  if (f) f.addEventListener('submit', function (e) { e.preventDefault(); var m = f.querySelector('.form-msg'); if (m) m.textContent = 'Vorschau: Das Formular ist nicht aktiv. Auf Ihrer echten Seite landet die Anfrage direkt im Postfach und im Kalender.'; });
})();
