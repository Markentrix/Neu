/* Kontaktformular mit Schadenfotos.
   Fotos werden im Browser verkleinert (das spart Datenvolumen und entfernt den Aufnahmeort),
   der Server prüft und verarbeitet sie noch einmal. Es werden keine Cookies verwendet. */
(function () {
  'use strict';

  var form = document.getElementById('contact-form');
  if (!form) return;

  var $ = function (id) { return document.getElementById(id); };
  var ENDPOINT = form.getAttribute('data-endpoint') || '';
  var DEMO = form.getAttribute('data-demo') === 'true';
  var PHONE = form.getAttribute('data-phone') || '';
  var PHONE_TEL = form.getAttribute('data-phone-tel') || '';
  var MAIL = form.getAttribute('data-email') || '';
  var EN = document.documentElement.lang === 'en';
  var LANG = EN ? 'en' : 'de';
  /* Texte in der Sprache der Seite */
  var M = EN ? {
    alsoReach: ' You can also reach us by phone on ', orMail: ' or by email at ',
    sending: 'Sending …', send: 'Send enquiry', preparing: 'Preparing photos …',
    photo: 'Photo ', countOf: ' of ', photosSelected: ' photos selected', none: 'No photos selected yet',
    badType: ' is not a supported format. Please choose JPG, PNG or WebP.', tooBig: ' is too large.',
    unreadable: ' could not be read. Please choose a JPG or PNG.', limit: 'A maximum of ' , limitEnd: ' photos is possible.',
    name: 'Please enter your name.', email: 'Please enter a valid email address.', subject: 'Please choose your topic.',
    message: 'Please briefly say what it is about.', consent: 'Please agree to the privacy policy.',
    failed: 'The enquiry could not be sent.', conn: 'The connection failed.', mb: ' MB', dec: '.', open: '\u201c', close: '\u201d'
  } : {
    alsoReach: ' Sie erreichen uns auch telefonisch unter ', orMail: ' oder per E-Mail an ',
    sending: 'Wird gesendet …', send: 'Anfrage senden', preparing: 'Fotos werden vorbereitet …',
    photo: 'Foto ', countOf: ' von ', photosSelected: ' Fotos ausgewählt', none: 'Noch keine Fotos ausgewählt',
    badType: ' hat kein unterstütztes Format. Bitte JPG, PNG oder WebP wählen.', tooBig: ' ist zu groß.',
    unreadable: ' konnte nicht gelesen werden. Bitte wählen Sie ein JPG oder PNG.', limit: 'Es sind höchstens ', limitEnd: ' Fotos möglich.',
    name: 'Bitte geben Sie Ihren Namen an.', email: 'Bitte geben Sie eine gültige E-Mail-Adresse an.', subject: 'Bitte wählen Sie Ihr Anliegen.',
    message: 'Bitte schreiben Sie kurz, worum es geht.', consent: 'Bitte stimmen Sie der Datenschutzerklärung zu.',
    failed: 'Die Anfrage konnte nicht gesendet werden.', conn: 'Die Verbindung hat nicht geklappt.', mb: ' MB', dec: ',', open: '\u201e', close: '\u201c'
  };
  var MAX_PHOTOS = 5;
  var MAX_EDGE = 2000;
  var MAX_ORIGINAL_BYTES = 30 * 1024 * 1024;
  var MIN_TOKEN_AGE_MS = 4500;
  var TYPES = ['image/jpeg', 'image/png', 'image/webp'];

  var photos = [];
  var token = '';
  var tokenAt = 0;
  var tokenRequest = null;
  var busy = false;

  var FIELDS = {
    name: 'f-name', email: 'f-email', subject: 'f-subject', message: 'f-message', consent: 'f-consent'
  };

  /* ---------------------------------------------------------------- Hilfen */

  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function kb(n) { return n >= 1048576 ? (n / 1048576).toFixed(1).replace('.', M.dec) + M.mb : Math.max(1, Math.round(n / 1024)) + ' KB'; }

  function setError(field, text) {
    var err = $('err-' + field);
    var input = $(FIELDS[field] || 'photos-field');
    if (err) { err.textContent = text || ''; err.hidden = !text; }
    if (input && FIELDS[field]) {
      if (text) { input.setAttribute('aria-invalid', 'true'); input.setAttribute('aria-describedby', 'err-' + field); }
      else { input.removeAttribute('aria-invalid'); input.removeAttribute('aria-describedby'); }
    }
  }

  function clearErrors() {
    Object.keys(FIELDS).forEach(function (f) { setError(f, ''); });
    setError('photos', '');
    var g = $('form-error');
    g.hidden = true;
    g.textContent = '';
  }

  function showGeneral(text, withFallback) {
    var g = $('form-error');
    g.textContent = text;
    if (withFallback) {
      g.appendChild(document.createTextNode(' Sie erreichen uns auch telefonisch unter '));
      var a = document.createElement('a');
      a.href = 'tel:' + PHONE_TEL; a.textContent = PHONE;
      g.appendChild(a);
      g.appendChild(document.createTextNode(' oder per E-Mail an '));
      var m = document.createElement('a');
      m.href = 'mailto:' + MAIL; m.textContent = MAIL;
      g.appendChild(m);
      g.appendChild(document.createTextNode('.'));
    }
    g.hidden = false;
    g.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  function setBusy(on, label) {
    busy = on;
    form.classList.toggle('is-sending', on);
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = on;
    btn.textContent = on ? (label || M.sending) : M.send;
  }

  /* ---------------------------------------------------------------- Token (Schutz vor automatischen Absendern) */

  function fetchToken() {
    if (DEMO || tokenRequest) return tokenRequest;
    tokenAt = Date.now();
    tokenRequest = fetch(ENDPOINT + '?aktion=token', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) { token = j.token || ''; $('f-token').value = token; })
      .catch(function () { tokenRequest = null; });
    return tokenRequest;
  }
  form.addEventListener('focusin', fetchToken);

  /* ---------------------------------------------------------------- Fotos */

  function drawToBlob(source, w, h) {
    return new Promise(function (resolve, reject) {
      var s = Math.min(1, MAX_EDGE / Math.max(w, h));
      var c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(w * s));
      c.height = Math.max(1, Math.round(h * s));
      var ctx = c.getContext('2d');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(source, 0, 0, c.width, c.height);
      c.toBlob(function (b) { b ? resolve(b) : reject(new Error('toBlob')); }, 'image/jpeg', 0.85);
    });
  }

  function compress(file) {
    var viaImage = function () {
      return new Promise(function (resolve, reject) {
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function () {
          drawToBlob(img, img.naturalWidth, img.naturalHeight).then(function (b) { URL.revokeObjectURL(url); resolve(b); }, reject);
        };
        img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('image')); };
        img.src = url;
      });
    };
    if (window.createImageBitmap) {
      return createImageBitmap(file, { imageOrientation: 'from-image' }).then(function (bmp) {
        return drawToBlob(bmp, bmp.width, bmp.height).then(function (b) { if (bmp.close) bmp.close(); return b; });
      }).catch(viaImage);
    }
    return viaImage();
  }

  function renderPhotos() {
    var list = $('photo-list');
    list.textContent = '';
    photos.forEach(function (p, i) {
      var li = document.createElement('li');
      var img = document.createElement('img');
      img.src = p.url; img.alt = M.photo + (i + 1); img.width = 160; img.height = 120;
      var meta = document.createElement('div');
      meta.className = 'meta';
      var nm = document.createElement('span'); nm.textContent = M.photo + (i + 1);
      var sz = document.createElement('span'); sz.textContent = kb(p.blob.size);
      meta.appendChild(nm); meta.appendChild(sz);
      var rm = document.createElement('button');
      rm.type = 'button'; rm.className = 'rm';
      rm.setAttribute('aria-label', EN ? 'Remove photo ' + (i + 1) : 'Foto ' + (i + 1) + ' entfernen');
      rm.innerHTML = '<span aria-hidden="true">×</span>';
      rm.addEventListener('click', function () {
        URL.revokeObjectURL(p.url);
        photos.splice(i, 1);
        setError('photos', '');
        renderPhotos();
      });
      li.appendChild(img); li.appendChild(meta); li.appendChild(rm);
      list.appendChild(li);
    });
    $('dz-count').textContent = photos.length ? photos.length + M.countOf + MAX_PHOTOS + M.photosSelected : M.none;
  }

  function addFiles(fileList) {
    var files = Array.prototype.slice.call(fileList || []);
    if (!files.length) return Promise.resolve();
    setError('photos', '');
    var problems = [];
    var queue = [];
    files.forEach(function (f) {
      if (photos.length + queue.length >= MAX_PHOTOS) {
        if (problems.indexOf('limit') < 0) problems.push('limit');
        return;
      }
      if (TYPES.indexOf(f.type) < 0) { problems.push(M.open + f.name + M.close + M.badType); return; }
      if (f.size > MAX_ORIGINAL_BYTES) { problems.push(M.open + f.name + M.close + M.tooBig); return; }
      queue.push(f);
    });
    setBusy(true, M.preparing);
    return queue.reduce(function (chain, f) {
      return chain.then(function () {
        return compress(f).then(function (blob) {
          photos.push({ blob: blob, url: URL.createObjectURL(blob) });
        }).catch(function () {
          problems.push(M.open + f.name + M.close + M.unreadable);
        });
      });
    }, Promise.resolve()).then(function () {
      problems = problems.map(function (p) { return p === 'limit' ? M.limit + MAX_PHOTOS + M.limitEnd : p; });
      if (problems.length) setError('photos', problems.join(' '));
      renderPhotos();
    }).then(function () { setBusy(false); });
  }

  var input = $('f-photos');
  input.addEventListener('change', function () {
    addFiles(input.files).then(function () { input.value = ''; });
  });

  var zone = $('dropzone');
  ['dragenter', 'dragover'].forEach(function (t) {
    zone.addEventListener(t, function (e) { e.preventDefault(); zone.classList.add('is-over'); });
  });
  ['dragleave', 'drop'].forEach(function (t) {
    zone.addEventListener(t, function (e) { e.preventDefault(); zone.classList.remove('is-over'); });
  });
  zone.addEventListener('drop', function (e) { addFiles(e.dataTransfer && e.dataTransfer.files); });

  /* ---------------------------------------------------------------- Prüfen und senden */

  function validate() {
    var errs = {};
    if (!$('f-name').value.trim()) errs.name = M.name;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test($('f-email').value.trim())) errs.email = M.email;
    if (!$('f-subject').value) errs.subject = M.subject;
    if ($('f-message').value.trim().length < 5) errs.message = M.message;
    if (!$('f-consent').checked) errs.consent = M.consent;
    return errs;
  }

  function showErrors(errs) {
    var first = null;
    ['name', 'email', 'subject', 'message', 'photos', 'consent'].forEach(function (f) {
      if (errs[f]) {
        setError(f, errs[f]);
        if (!first) first = f;
      }
    });
    if (first) {
      var el = $(FIELDS[first] || 'f-photos');
      if (el) { el.focus({ preventScroll: true }); el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    }
  }

  function success(ref) {
    photos.forEach(function (p) { URL.revokeObjectURL(p.url); });
    photos = [];
    renderPhotos();
    form.reset();
    form.hidden = true;
    $('success-ref').textContent = ref;
    var box = $('form-success');
    box.hidden = false;
    box.focus();
    box.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (busy) return;
    clearErrors();
    var errs = validate();
    if (Object.keys(errs).length) { showErrors(errs); return; }

    setBusy(true);
    var run;
    if (DEMO) {
      run = sleep(800).then(function () { success('DEMO-0000'); });
    } else {
      run = fetchToken().then(function () {
        var wait = MIN_TOKEN_AGE_MS - (Date.now() - tokenAt);
        return wait > 0 ? sleep(wait) : null;
      }).then(function () {
        var fd = new FormData();
        fd.append('name', $('f-name').value.trim());
        fd.append('email', $('f-email').value.trim());
        fd.append('phone', $('f-phone').value.trim());
        fd.append('subject', $('f-subject').value);
        fd.append('message', $('f-message').value.trim());
        fd.append('consent', '1');
        fd.append('lang', LANG);
        fd.append('token', token);
        fd.append('website', $('f-website').value);
        photos.forEach(function (p, i) { fd.append('photos[]', p.blob, 'foto-' + (i + 1) + '.jpg'); });
        var ctrl = new AbortController();
        var timer = setTimeout(function () { ctrl.abort(); }, 90000);
        return fetch(ENDPOINT, { method: 'POST', body: fd, credentials: 'same-origin', signal: ctrl.signal })
          .then(function (r) {
            clearTimeout(timer);
            return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, json: j }; });
          });
      }).then(function (res) {
        var j = res.json || {};
        if (res.status === 200 && j.ok) { success(j.ref || ''); return; }
        if (j.errors && Object.keys(j.errors).some(function (k) { return k !== 'general'; })) {
          showErrors(j.errors);
          return;
        }
        // Token abgelaufen oder zu schnell: neues holen, damit ein erneuter Versuch klappt
        token = ''; tokenRequest = null; fetchToken();
        showGeneral(j.error || M.failed, res.status >= 500 || res.status === 403 || res.status === 429);
      });
    }
    run.catch(function () {
      showGeneral(M.conn, true);
    }).then(function () { setBusy(false); });
  });

  $('form-again').addEventListener('click', function () {
    $('form-success').hidden = true;
    form.hidden = false;
    clearErrors();
    $('f-name').focus();
  });

  renderPhotos();
})();
