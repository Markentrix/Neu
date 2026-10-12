/* Vergleichsansicht. Links ein Bild der bisherigen Seite, rechts der neue Entwurf im Rahmen.
   Beide werden auf dieselbe Breite skaliert und laufen auf Wunsch gemeinsam. */
(function () {
  'use strict';
  var root = document.getElementById('cmp');
  if (!root) return;
  var PAGES = JSON.parse(root.getAttribute('data-pages') || '[]');
  var OLD_BASE = root.getAttribute('data-old-base') || '';
  var WIDTH = { d: 1280, m: 390 };
  var $ = function (id) { return document.getElementById(id); };

  var sel = $('cmp-page'), frame = $('new-frame'), img = $('old-img');
  var scrollOld = $('scroll-old'), scrollNew = $('scroll-new');
  var sizeOld = $('size-old'), sizeNew = $('size-new');
  var oldNone = $('old-none'), sync = $('cmp-sync');

  var small = Math.min(window.innerWidth, 9999) < 700;
  var state = { idx: 0, view: small ? 'm' : 'd', zoom: 0, contentH: 900 };

  PAGES.forEach(function (p, i) {
    var o = document.createElement('option');
    o.value = String(i); o.textContent = p.label;
    sel.appendChild(o);
  });

  function paneWidth(el) { return Math.max(120, el.clientWidth); }

  function scale() {
    var w = WIDTH[state.view];
    var fit = Math.min(1, paneWidth(scrollNew) / w);
    return state.zoom || fit;
  }

  function layout() {
    var w = WIDTH[state.view], s = scale();
    // Rechts: Rahmen in voller Breite, verkleinert dargestellt
    frame.style.width = w + 'px';
    frame.style.height = state.contentH + 'px';
    frame.style.transform = 'scale(' + s + ')';
    sizeNew.style.width = Math.round(w * s) + 'px';
    sizeNew.style.height = Math.round(state.contentH * s) + 'px';
    // Links: Bild in derselben Breite
    sizeOld.style.width = Math.round(w * s) + 'px';
  }

  function showOld() {
    var p = PAGES[state.idx];
    var has = p && p.id;
    oldNone.hidden = !!has;
    sizeOld.style.display = has ? '' : 'none';
    if (has) img.src = 'alt/' + p.id + '-' + state.view + '.jpg';
    $('old-link').href = has && p.old ? OLD_BASE + p.old : OLD_BASE;
    layout();
  }

  function measure() {
    try {
      var d = frame.contentDocument;
      if (!d || !d.documentElement) return;
      var h = Math.max(d.documentElement.scrollHeight, d.body ? d.body.scrollHeight : 0);
      if (h && Math.abs(h - state.contentH) > 1) { state.contentH = h; layout(); }
    } catch (e) { /* anderer Ursprung: nichts messen */ }
  }

  function currentIndex() {
    try {
      var path = frame.contentWindow.location.pathname;
      var at = path.indexOf('/neu/');
      var rel = at >= 0 ? path.slice(at + 5) : '';
      for (var i = 0; i < PAGES.length; i++) if (PAGES[i].new === rel) return i;
      return -1;
    } catch (e) { return state.idx; }
  }

  function loadNew() {
    $('new-link').href = 'neu/' + PAGES[state.idx].new;
    state.contentH = 900;
    frame.src = 'neu/' + PAGES[state.idx].new;
  }

  var observer = null;
  frame.addEventListener('load', function () {
    var i = currentIndex();
    if (i !== state.idx) {                       // Besucher hat rechts einen Link angeklickt
      if (i >= 0) { state.idx = i; sel.value = String(i); showOld(); }
      else { oldNone.hidden = false; sizeOld.style.display = 'none'; }
    }
    scrollNew.scrollTop = 0;
    measure();
    var d = frame.contentDocument;
    if (d && d.fonts && d.fonts.ready) d.fonts.ready.then(measure);
    setTimeout(measure, 400); setTimeout(measure, 1200); setTimeout(measure, 3000);
    if (observer) observer.disconnect();
    if (window.ResizeObserver && d && d.documentElement) {
      observer = new ResizeObserver(measure);
      observer.observe(d.documentElement);
    }
  });

  sel.addEventListener('change', function () {
    state.idx = parseInt(sel.value, 10) || 0;
    scrollOld.scrollTop = 0; scrollNew.scrollTop = 0;
    showOld(); loadNew();
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-view]'), function (b) {
    b.addEventListener('click', function () {
      state.view = b.getAttribute('data-view');
      state.zoom = 0;
      Array.prototype.forEach.call(document.querySelectorAll('[data-view]'), function (x) {
        x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
      });
      scrollOld.scrollTop = 0; scrollNew.scrollTop = 0;
      showOld(); layout();
      setTimeout(measure, 150); setTimeout(measure, 700);
    });
  });

  function zoomBy(f) {
    state.zoom = Math.max(0.15, Math.min(2, scale() * f));
    layout();
  }
  $('zoom-in').addEventListener('click', function () { zoomBy(1.25); });
  $('zoom-out').addEventListener('click', function () { zoomBy(0.8); });
  $('zoom-fit').addEventListener('click', function () { state.zoom = 0; layout(); });
  window.addEventListener('resize', function () { layout(); });

  // Gemeinsam scrollen: im gleichen Verhältnis, damit gleiche Abschnitte ungefähr nebeneinander liegen
  var lock = false;
  function link(from, to) {
    from.addEventListener('scroll', function () {
      if (!sync.checked || lock) return;
      lock = true;
      var fy = from.scrollHeight - from.clientHeight, ty = to.scrollHeight - to.clientHeight;
      var fx = from.scrollWidth - from.clientWidth, tx = to.scrollWidth - to.clientWidth;
      to.scrollTop = fy > 0 ? (from.scrollTop / fy) * ty : 0;
      to.scrollLeft = fx > 0 ? (from.scrollLeft / fx) * tx : 0;
      requestAnimationFrame(function () { lock = false; });
    }, { passive: true });
  }
  link(scrollOld, scrollNew);
  link(scrollNew, scrollOld);

  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  document.addEventListener('dragstart', function (e) { e.preventDefault(); });

  showOld();
  loadNew();
})();
