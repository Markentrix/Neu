/* Website-Vorschau: setzt Name und Ort aus dem Fragment der Adresse (#n=...&o=...) in die Beispielseite ein.
   Das Fragment wird nicht an den Server gesendet. Ohne Fragment bleibt die Beispielseite unverändert. */
(function () {
  var d = document, slug = (location.pathname.match(/\/beispiel\/([a-z]+-muster)\//) || [])[1];
  var BASE = { 'elektro-muster': 'Elektro Muster', 'praxis-muster': 'Praxis Muster', 'gasthaus-muster': 'Gasthaus Muster' };
  if (!slug || !BASE[slug]) return;
  var base = BASE[slug], title0 = d.title, items = [], ribbon = d.querySelector('.ribbon'), ribbon0 = ribbon ? ribbon.textContent : '';
  var ATTR = ['placeholder', 'aria-label', 'title', 'alt'];

  (function collect() {
    var wk = d.createTreeWalker(d.body, NodeFilter.SHOW_TEXT, null), n;
    while ((n = wk.nextNode())) {
      var p = n.parentNode && n.parentNode.nodeName;
      if (p === 'SCRIPT' || p === 'STYLE' || (ribbon && ribbon.contains(n)) || !n.nodeValue.trim()) continue;
      items.push({ n: n, o: n.nodeValue });
    }
    Array.prototype.forEach.call(d.body.querySelectorAll('*'), function (e) {
      ATTR.forEach(function (a) { if (e.hasAttribute(a)) items.push({ e: e, a: a, o: e.getAttribute(a) }); });
    });
  })();

  function clean(s, max) { return String(s || '').replace(/[\u0000-\u001f\u007f<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, max); }
  function params() {
    var o = {}; (location.hash || '').replace(/^#/, '').split('&').forEach(function (kv) {
      var i = kv.indexOf('='); if (i < 1) return;
      try { o[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); } catch (e) { }
    });
    return { n: clean(o.n, 48), o: clean(o.o, 40) };
  }
  function initials(n) {
    var w = n.split(' ').filter(function (x) { return /[A-Za-zÄÖÜäöüß]/.test(x); });
    if (!w.length) return '';
    var a = w[0].replace(/[^A-Za-zÄÖÜäöüß]/g, ''), b = w[1] ? w[1].replace(/[^A-Za-zÄÖÜäöüß]/g, '') : '';
    return (a.charAt(0) + (b ? b.charAt(0) : a.charAt(1))).toUpperCase();
  }
  function tx(s, n, o) {
    var r = s;
    if (o) {
      r = r.split('Celle, Bergen, Wietze, Hambühren, Winsen').join(o + ' und Umgebung')
        .replace(/Stadt Celle mit Altstadt[^.]*\.[^.]*\./, o + ' und die umliegenden Orte. Anfahrt im Einzugsgebiet ist im Festpreis enthalten.')
        .split('Einfamilienhaus in Wietze').join('Einfamilienhaus in ' + o)
        .split('im Landkreis Celle').join('in ' + o + ' und Umgebung')
        .split('des Landkreises Celle').join('des Einzugsgebiets')
        .split('Celle und Landkreis').join(o)
        .split('in der Celler Altstadt').join('in ' + o)
        .split('29221 Celle').join(o)
        .replace(/05141[\s\u00a0]00[\s\u00a0]00([\s\u00a0]0\d)?/g, 'Ihre Nummer')
        .replace(/\bCelle\b/g, o);
    }
    if (n) r = r.split(base).join(n);
    return r;
  }
  function apply() {
    var p = params(), on = !!(p.n || p.o);
    items.forEach(function (it) {
      var v = on ? tx(it.o, p.n, p.o) : it.o;
      if (it.n) it.n.nodeValue = v; else it.e.setAttribute(it.a, v);
    });
    Array.prototype.forEach.call(d.querySelectorAll('.mark'), function (m) { if (m.dataset.o === undefined) m.dataset.o = m.textContent; m.textContent = p.n ? initials(p.n) : m.dataset.o; });
    Array.prototype.forEach.call(d.querySelectorAll('.pin'), function (pin, i) { pin.style.display = (on && p.o && i > 0) ? 'none' : ''; });
    if (ribbon) ribbon.textContent = on ? 'Vorschau von Markentrix' + (p.n ? ' für ' + p.n : '') + '. Beispielinhalte: Texte, Bilder, Formular und Nummer sind nicht aktiv.' : ribbon0;
    d.title = on && p.n ? p.n + ' · Vorschau (Beispiel)' : title0;
  }
  apply();
  window.addEventListener('hashchange', apply);
})();
