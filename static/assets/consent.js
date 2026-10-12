/* Markentrix · Consent-Banner (TDDDG § 25 / DSGVO) + Google Analytics 4 nur nach Einwilligung.
   GA wird erst nach aktiver Zustimmung geladen. Vorher: keine Verbindung zu Google. */
(function () {
  var GA_ID = 'G-E1VP4SYQ7K';
  var METRICOOL_HASH = 'd4608fdaed9383e42d93839cf230e49f';
  var KEY = 'mx-consent', VERSION = 2, MAX_AGE = 1000 * 60 * 60 * 24 * 180; // 6 Monate
  var DS = '/datenschutz#s5';

  function read() {
    try { var c = JSON.parse(localStorage.getItem(KEY)); if (c && c.v === VERSION && Date.now() - c.ts < MAX_AGE) return c; } catch (e) {}
    return null;
  }
  function save(analytics) {
    var c = { v: VERSION, ts: Date.now(), analytics: !!analytics };
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
    apply(c);
  }

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;
  gtag('consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', wait_for_update: 500 });

  var loaded = false;
  var mcLoaded = false;
  function loadMetricool() {
    if (mcLoaded || !METRICOOL_HASH) return; mcLoaded = true; loaded = loaded || false;
    var s = document.createElement('script'); s.src = 'https://tracker.metricool.com/resources/be.js';
    s.onload = function () { try { window.beTracker.t({ hash: METRICOOL_HASH }); } catch (e) {} };
    document.head.appendChild(s);
  }
  function apply(c) {
    if (c && c.analytics) {
      loadMetricool();
      gtag('consent', 'update', { analytics_storage: 'granted' });
      if (!loaded && /^G-[A-Z0-9]{6,}$/.test(GA_ID) && GA_ID !== 'G-XXXXXXXXXX') {
        loaded = true;
        var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
        document.head.appendChild(s);
        gtag('js', new Date());
        gtag('config', GA_ID, { anonymize_ip: true, allow_google_signals: false, allow_ad_personalization_signals: false });
      }
    } else {
      gtag('consent', 'update', { analytics_storage: 'denied' });
      if (loaded || mcLoaded) { // Widerruf: GA-Cookies entfernen und neu laden, damit das Skript nicht weiterläuft
        document.cookie.split(';').forEach(function (k) {
          var n = k.split('=')[0].trim();
          if (/^_ga/.test(n)) ['', '; domain=' + location.hostname, '; domain=.' + location.hostname.replace(/^www\./, '')].forEach(function (d) {
            document.cookie = n + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
          });
        });
        location.reload();
      }
    }
  }

  var F = "'Inter','Segoe UI',system-ui,sans-serif";
  var BTN = 'flex:1 1 150px;min-height:46px;padding:12px 18px;border-radius:10px;font:600 14.5px ' + F + ';cursor:pointer;';
  var BTN_A = BTN + 'background:#0B1020;color:#FFFFFF;border:2px solid #0B1020;';
  var BTN_B = BTN + 'background:#FFFFFF;color:#0B1020;border:2px solid #0B1020;';
  var el, lastFocus;

  function build() {
    el = document.createElement('div');
    el.id = 'mx-consent';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'false');
    el.setAttribute('aria-labelledby', 'mxc-t');
    el.setAttribute('aria-describedby', 'mxc-d');
    el.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:10000;max-width:560px;margin:0 auto;background:#FFFFFF;color:#0B1020;border:1px solid rgba(11,16,32,.14);border-radius:16px;box-shadow:0 24px 60px rgba(11,16,32,.22);padding:22px 22px 18px;font:14px/1.6 ' + F + ';max-height:calc(100vh - 32px);overflow:auto';
    el.innerHTML =
      '<h2 id="mxc-t" style="margin:0 0 8px;font:800 18px/1.3 \'Space Grotesk\',\'Futura\',sans-serif;color:#0B1020">Datenschutz-Einstellungen</h2>' +
      '<p id="mxc-d" style="margin:0 0 14px;color:#47506A">Wir möchten mit <b style="color:#0B1020">Google Analytics</b> und <b style="color:#0B1020">Metricool</b> messen, welche Inhalte genutzt werden, um die Website zu verbessern. Das geschieht nur mit Ihrer Einwilligung. Dabei werden Cookies gesetzt und Daten an die Anbieter übermittelt (bei Google auch in die USA). Sie können Ihre Wahl jederzeit über „Cookie-Einstellungen“ im Seitenfuß ändern. <a href="' + DS + '" style="color:#0B63C6;text-decoration:underline">Datenschutzerklärung</a> · <a href="/impressum" style="color:#0B63C6;text-decoration:underline">Impressum</a></p>' +
      '<div id="mxc-det" hidden style="border:1px solid rgba(11,16,32,.12);border-radius:12px;margin:0 0 14px;overflow:hidden">' +
        '<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid rgba(11,16,32,.08)"><input type="checkbox" id="mxc-n" checked disabled style="width:20px;height:20px;margin-top:2px;flex-shrink:0;accent-color:#0B1020"><label for="mxc-n" style="flex:1"><b>Notwendig</b> <span style="color:#5B6784">(immer aktiv)</span><br><span style="color:#47506A;font-size:13px">Speichert Ihre Datenschutz-Auswahl, Anzeige- und Barrierefreiheits-Einstellungen lokal im Browser. Keine Übertragung an Dritte.</span></label></div>' +
        '<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 14px"><input type="checkbox" id="mxc-a" style="width:20px;height:20px;margin-top:2px;flex-shrink:0;accent-color:#0B63C6"><label for="mxc-a" style="flex:1;cursor:pointer"><b>Statistik – Google Analytics 4 &amp; Metricool</b><br><span style="color:#47506A;font-size:13px">Anbieter: Google Ireland Ltd., Dublin (Cookies _ga, _ga_*, bis 14 Monate) und Metricool Software S.L., Spanien. Zweck: Reichweitenmessung. Rechtsgrundlage: Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG).</span></label></div>' +
      '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:10px">' +
        '<button type="button" id="mxc-no" style="' + BTN_B + '">Nur notwendige</button>' +
        '<button type="button" id="mxc-yes" style="' + BTN_A + '">Alle akzeptieren</button>' +
        '<button type="button" id="mxc-save" hidden style="' + BTN_A + '">Auswahl speichern</button>' +
      '</div>' +
      '<button type="button" id="mxc-more" aria-expanded="false" aria-controls="mxc-det" style="margin-top:10px;background:none;border:none;padding:6px 0;min-height:36px;color:#0B63C6;font:600 13.5px ' + F + ';text-decoration:underline;cursor:pointer">Einstellungen anpassen</button>';
    document.body.appendChild(el);
    var $ = function (id) { return el.querySelector('#' + id); };
    $('mxc-yes').onclick = function () { save(true); close(); };
    $('mxc-no').onclick = function () { save(false); close(); };
    $('mxc-save').onclick = function () { save($('mxc-a').checked); close(); };
    $('mxc-more').onclick = function () {
      var d = $('mxc-det'), open = d.hidden;
      d.hidden = !open; $('mxc-save').hidden = !open; $('mxc-yes').hidden = open;
      this.setAttribute('aria-expanded', open ? 'true' : 'false');
      this.textContent = open ? 'Weniger anzeigen' : 'Einstellungen anpassen';
    };
  }

  function open(detailed) {
    if (!el) build();
    var c = read();
    el.querySelector('#mxc-a').checked = !!(c && c.analytics);
    el.hidden = false;
    if (detailed && el.querySelector('#mxc-det').hidden) el.querySelector('#mxc-more').click();
    lastFocus = document.activeElement;
    el.querySelector('#mxc-t').setAttribute('tabindex', '-1');
    el.querySelector('#mxc-t').focus({ preventScroll: true });
  }
  function close() { if (el) el.hidden = true; if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true }); }

  window.mxConsent = { open: open, get: read };

  function addFooterLink() {
    var nav = document.querySelector('footer');
    if (!nav || nav.querySelector('[data-consent-open]')) return;
    var ref = nav.querySelector('a[href*="datenschutz"]');
    var a = document.createElement('a');
    a.href = '#cookie-einstellungen'; a.setAttribute('data-consent-open', ''); a.setAttribute('role', 'button');
    a.textContent = 'Cookie-Einstellungen';
    if (ref) { a.style.cssText = ref.getAttribute('style') || ''; a.className = ref.className; }
    if (ref) ref.parentNode.insertBefore(a, ref.nextSibling); else nav.appendChild(a);
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-consent-open],a[href$="#cookie-einstellungen"]');
    if (t) { e.preventDefault(); open(true); }
  });

  function init() {
    addFooterLink();
    var c = read();
    if (c) apply(c); else open(false);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
