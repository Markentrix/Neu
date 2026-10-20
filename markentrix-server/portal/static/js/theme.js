/* Erscheinungsbild: hell, dunkel oder automatisch (Geräteeinstellung). Läuft vor dem ersten Zeichnen, damit nichts aufblitzt. */
(function () {
  var wahl = 'auto';
  try { wahl = localStorage.getItem('mk-theme') || 'auto'; } catch (e) { /* ohne Speicher: automatisch */ }
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  function anwenden() {
    var dunkel = wahl === 'dunkel' || (wahl === 'auto' && mq && mq.matches);
    document.documentElement.setAttribute('data-theme', dunkel ? 'dark' : 'light');
  }
  anwenden();
  if (mq && mq.addEventListener) mq.addEventListener('change', anwenden);
  /** @type {any} */ (window).mkTheme = {
    get: function () { return wahl; },
    set: function (w) { wahl = w; try { localStorage.setItem('mk-theme', w); } catch (e) { /* nur bis zum Neuladen */ } anwenden(); }
  };
})();
