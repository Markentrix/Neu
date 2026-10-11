/* Entwurfsmodus von Markentrix: einfache Hürden gegen Gelegenheitskopieren.
   Ein technischer Vollschutz ist bei Webseiten nicht möglich. */
(function () {
  'use strict';
  var NOTICE = '© Markentrix. Entwurf zur Ansicht. Kopieren und Weitergabe nicht gestattet.';
  var isField = function (t) {
    var el = t && t.nodeType === 3 ? t.parentElement : t;
    return !!(el && el.closest && el.closest('input, textarea, select'));
  };
  document.addEventListener('contextmenu', function (e) { if (!isField(e.target)) e.preventDefault(); });
  document.addEventListener('selectstart', function (e) { if (!isField(e.target)) e.preventDefault(); });
  document.addEventListener('dragstart', function (e) { e.preventDefault(); });
  ['copy', 'cut'].forEach(function (type) {
    document.addEventListener(type, function (e) {
      if (isField(e.target)) return;
      e.preventDefault();
      if (e.clipboardData) e.clipboardData.setData('text/plain', NOTICE);
    });
  });
})();
