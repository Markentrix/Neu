/* Kurz erklärt: Audio-Einführung auf der Startseite. Ohne JavaScript bleibt der normale Audio-Player sichtbar.
   Es startet nie von selbst, nur auf Tipp oder Klick. Datei und Text liegen auf dem eigenen Server. */
(function () {
  'use strict';
  var root = document.querySelector('[data-intro]');
  if (!root) return;
  var audio = root.querySelector('[data-intro-audio]');
  var btn = root.querySelector('[data-intro-btn]');
  var label = root.querySelector('[data-intro-label]');
  var bar = root.querySelector('[data-intro-bar]');
  if (!audio || !btn || !label || !bar || !audio.play) return;

  audio.controls = false;
  btn.hidden = false;
  root.classList.add('is-ready');

  var TXT_PLAY = 'Kurz erklärt anhören · 35 Sek.';
  var TXT_PAUSE = 'Pause';
  var TXT_RESUME = 'Weiter anhören';
  var TXT_AGAIN = 'Noch einmal anhören';

  // Messung: zählt nur nach Einwilligung zur Statistik (gtag ist ohne Einwilligung inaktiv). Es werden keine Inhalte oder Personendaten übergeben.
  function track(name, params) { try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (e) { } }
  var started = false, half = false;

  function set(playing, text) {
    btn.setAttribute('aria-pressed', playing ? 'true' : 'false');
    root.classList.toggle('is-playing', playing);
    label.textContent = text;
  }

  btn.addEventListener('click', function () {
    if (audio.paused) {
      if (audio.ended) audio.currentTime = 0;
      var p = audio.play();
      if (p && p.catch) p.catch(function () { set(false, TXT_PLAY); });
    } else {
      audio.pause();
    }
  });
  audio.addEventListener('play', function () { set(true, TXT_PAUSE); if (!started) { started = true; track('audio_intro_start', { location: location.pathname }); } });
  audio.addEventListener('pause', function () { if (!audio.ended) set(false, audio.currentTime > 0 ? TXT_RESUME : TXT_PLAY); });
  audio.addEventListener('ended', function () { set(false, TXT_AGAIN); bar.style.width = '0%'; track('audio_intro_complete', { location: location.pathname }); });
  audio.addEventListener('timeupdate', function () {
    if (audio.duration) bar.style.width = (audio.currentTime / audio.duration * 100).toFixed(1) + '%';
    if (!half && audio.duration && audio.currentTime / audio.duration >= 0.5) { half = true; track('audio_intro_50', { location: location.pathname }); }
  });
  document.addEventListener('visibilitychange', function () { if (document.hidden && !audio.paused) audio.pause(); });
  set(false, TXT_PLAY);
})();
