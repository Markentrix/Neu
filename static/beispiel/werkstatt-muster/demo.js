(function () {
  var f = document.querySelector('[data-demo-form]'); if (!f) return;
  f.addEventListener('submit', function (e) { e.preventDefault(); var m = f.querySelector('.form-msg'); if (m) m.textContent = 'Beispielseite: Das Formular ist nicht aktiv. Auf einer echten Seite landet die Anfrage jetzt im Postfach und im Kalender.'; });
})();
