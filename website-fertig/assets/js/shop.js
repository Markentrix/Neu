/* Schichtatelier Shop – Warenkorb, Formulare, Katalog aus dem Portal (Website-API, relative Pfade) */
(function () {
  "use strict";
  var CFG = window.SW_CONFIG || {};
  var FARBEN = window.SW_FARBEN || {};
  var KAT = window.SW_KATEGORIEN || {};
  var STATIC = window.SW_STATIC || [];
  var KEY = "sw_warenkorb", CKEY = "sw_katalog";
  var EUR = function (n) { return Number(n).toFixed(2).replace(".", ",") + " €"; };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var ROOT = (document.body.getAttribute("data-root") || "");
  var VOUCHER = null, coupon = null, catalogLoaded = false, catalogHooks = [];

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (ch) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]; }); }
  function safeColor(h) { return /^#[0-9a-f]{3,8}$/i.test(h || "") ? h : "#cccccc"; }

  /* ---------- Artikel normalisieren (eingebaute Liste und Portal haben dasselbe Zielformat) ---------- */
  function norm(p) {
    return {
      id: String(p.id), name: String(p.name || ""), preis: Number(p.preis) || 0,
      kat: p.kategorie || p.kat || "", text: !!(p.personalisierbar || p.text), textlabel: p.textlabel || "Wunschtext", textmax: parseInt(p.textmax, 10) || 80,
      farben: Array.isArray(p.farben) ? p.farben.map(String) : [], kurz: p.kurz || "", lang: p.lang || "", material: p.material || "", masse: p.masse || "", gewicht: p.gewicht || "",
      tags: Array.isArray(p.tags) ? p.tags.map(String) : [], bilder: Array.isArray(p.bilder) ? p.bilder : [], sort: p.sort == null ? 0 : Number(p.sort), verwandt: Array.isArray(p.verwandt) ? p.verwandt : []
    };
  }
  var P = (window.SW_PRODUKTE || []).map(norm);
  function findProduct(id) { for (var i = 0; i < P.length; i++) if (P[i].id === id) return P[i]; return null; }
  function colorName(k) { return FARBEN[k] ? FARBEN[k][0] : k; }
  function imgDim(p) { var b = p.bilder && p.bilder[0]; return { w: (b && b.w) || 800, h: (b && b.h) || 600 }; }
  function imgOf(p) {
    var b = p.bilder && p.bilder[0]; var u = b && (b.url || b);
    if (typeof u === "string" && u) return /^(\/|https?:)/.test(u) ? u : ROOT + u;
    return ROOT + "assets/img/produkte/" + p.id + ".webp";
  }
  function hrefOf(p) { return STATIC.indexOf(p.id) >= 0 ? ROOT + "produkt/" + p.id + ".html" : ROOT + "produkt.html?id=" + encodeURIComponent(p.id); }

  /* ---------- Warenkorb (nur im Browser des Besuchers, localStorage) ---------- */
  function loadCart() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } }
  function saveCart(c) { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) { /* privater Modus */ } updateBadge(); }
  function cartCount() { return loadCart().reduce(function (s, i) { return s + i.menge; }, 0); }
  var lastCount = null;
  function updateBadge() {
    var n = cartCount(); var more = lastCount !== null && n > lastCount; lastCount = n;
    $$(".cart-link").forEach(function (a) { a.setAttribute("aria-label", n > 0 ? "Warenkorb, " + n + " Stück" : "Warenkorb"); });
    $$(".cart-badge").forEach(function (b) {
      b.textContent = n; b.classList.toggle("show", n > 0);
      if (more) { b.classList.remove("bump"); void b.offsetWidth; b.classList.add("bump"); }
    });
  }
  // Das Artikelbild fliegt in Stufen zum Warenkorb-Symbol, danach pulsiert der Zähler
  function flyToCart(img) {
    var target = $(".cart-link");
    if (!img || !target || !img.animate || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    var a = img.getBoundingClientRect(), b = target.getBoundingClientRect();
    if (!a.width || !b.width) return;
    var f = document.createElement("img"); f.src = img.currentSrc || img.src; f.alt = ""; f.className = "fly";
    f.style.cssText = "left:" + a.left + "px;top:" + a.top + "px;width:" + a.width + "px;height:" + a.height + "px";
    document.body.appendChild(f);
    var dx = b.left + b.width / 2 - (a.left + a.width / 2), dy = b.top + b.height / 2 - (a.top + a.height / 2), sc = Math.max(0.08, 40 / a.width);
    var an = f.animate([{ transform: "translate(0,0) scale(1)", opacity: 1 }, { transform: "translate(" + dx + "px," + dy + "px) scale(" + sc + ")", opacity: 0.6 }], { duration: 650, easing: "steps(9,end)" });
    an.onfinish = function () {
      f.remove();
      $$(".cart-badge").forEach(function (bd) { bd.classList.remove("bump"); void bd.offsetWidth; bd.classList.add("bump"); });
    };
  }
  function addToCart(id, farbe, text, menge) {
    var c = loadCart();
    for (var i = 0; i < c.length; i++) {
      if (c[i].id === id && c[i].farbe === farbe && (c[i].text || "") === (text || "")) { c[i].menge += menge; saveCart(c); return; }
    }
    c.push({ id: id, farbe: farbe, text: text || "", menge: menge });
    saveCart(c);
  }
  function lieferart() { var r = document.querySelector("input[name=lieferart]:checked"); return r ? r.value : "versand"; }
  function cartTotals(c) {
    var sum = 0;
    c.forEach(function (i) { var p = findProduct(i.id); if (p) sum += p.preis * i.menge; });
    var abholung = lieferart() === "abholung";
    var versand = (sum === 0 || abholung) ? 0 : (sum >= CFG.versandfreiAb ? 0 : CFG.versandPauschale);
    var r2 = function (x) { return Math.round(x * 100) / 100; };
    var gesamt = r2(sum + versand); var abz = coupon ? r2(Math.min(coupon.rest, gesamt)) : 0;
    return { zwischensumme: r2(sum), versand: versand, gesamt: gesamt, abholung: abholung, gutschein: abz, zuZahlen: r2(gesamt - abz) };
  }
  function cartAsText(c) {
    return c.map(function (i) {
      var p = findProduct(i.id); if (!p) return "";
      var det = [i.farbe ? colorName(i.farbe) : "", i.text ? "Text: " + i.text : ""].filter(Boolean).join(", ");
      return i.menge + "× " + p.name + (det ? " (" + det + ")" : "") + " à " + EUR(p.preis) + " = " + EUR(p.preis * i.menge);
    }).filter(Boolean).join("\n");
  }
  function toast(msg) {
    var t = $(".toast"); if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }

  /* ---------- Menü ---------- */
  var mb = $(".menu-btn");
  if (mb) {
    mb.addEventListener("click", function (e) {
      e.stopPropagation(); var nav = $(".nav"); var open = nav.classList.toggle("open"); mb.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      var nav = $(".nav"); if (nav.classList.contains("open") && !nav.contains(e.target)) { nav.classList.remove("open"); mb.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { var nv = $(".nav"); var war = nv.classList.contains("open"); nv.classList.remove("open"); mb.setAttribute("aria-expanded", "false"); if (war && nv.contains(document.activeElement)) mb.focus(); } });
  }

  /* ---------- Karten (gleiches Markup wie der Generator) ---------- */
  function cardHtml(p, h) {
    h = h || "h3"; var href = hrefOf(p);
    var notes = []; if (p.text) notes.push("Mit Wunschtext"); if (p.farben.length > 1) notes.push("in " + p.farben.length + " Farben");
    var action = p.text ? '<a class="btn btn-card" href="' + esc(href) + '">Text und Farbe wählen</a>' : '<button class="btn btn-card" type="button" data-add="' + esc(p.id) + '">In den Warenkorb</button>';
    var tags = p.tags.concat(p.text && p.tags.indexOf("personalisiert") < 0 ? ["personalisiert"] : []).join(" ");
    return '<article class="card" data-kat="' + esc(p.kat) + '" data-tags="' + esc(tags) + '" data-preis="' + p.preis + '" data-name="' + esc(p.name) + '" data-pos="' + (p._pos || 0) + '" data-id="' + esc(p.id) + '" data-suche="' + esc([p.name, p.kurz, p.material].join(" ").toLowerCase()) + '">' +
      '<a class="card-img" href="' + esc(href) + '" tabindex="-1" aria-hidden="true"><img src="' + esc(imgOf(p)) + '" width="' + imgDim(p).w + '" height="' + imgDim(p).h + '" alt="" loading="lazy"></a>' +
      '<div class="card-body"><' + h + '><a href="' + esc(href) + '">' + esc(p.name) + '</a></' + h + '>' +
      '<p class="small">' + esc(p.kurz) + '</p>' +
      (notes.length ? '<span class="card-note">' + esc(notes.join(", ")) + '</span>' : "") +
      '<div class="card-foot"><span class="price">' + EUR(p.preis) + '</span>' + action + '</div></div></article>';
  }

  /* ---------- Produktseite (Kaufformular) ---------- */
  var buy = null;
  function bindBuy(form) {
    buy = form; if (!form) return;
    var qtyIn = $("#menge", form);
    $$(".qty button", form).forEach(function (b) {
      b.addEventListener("click", function () { var v = parseInt(qtyIn.value, 10) || 1; v += parseInt(b.dataset.d, 10); qtyIn.value = Math.min(99, Math.max(1, v)); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var id = form.dataset.id;
      var farbe = (form.querySelector("input[name=farbe]:checked") || {}).value || "";
      var textEl = $("#wunschtext", form);
      var text = textEl ? textEl.value.trim() : "";
      if (textEl && textEl.required && !text) { textEl.focus(); var tf = textEl.closest(".field"); tf.classList.add("err"); markInvalid(textEl, $(".msg", tf)); return; }
      var menge = Math.min(99, Math.max(1, parseInt(qtyIn.value, 10) || 1));
      addToCart(id, farbe, text, menge);
      flyToCart($(".product-media img") || $(".product-media-main img"));
      var ok = $(".added"); if (ok) { ok.classList.add("show"); }
      toast("In den Warenkorb gelegt");
    });
  }
  bindBuy($("#kaufen"));

  /* Statische Produktseite: Preis und Verfügbarkeit aus dem Portal übernehmen */
  catalogHooks.push(function () {
    if (!buy || $("#produkt-dyn")) return;
    var p = findProduct(buy.dataset.id); var btn = buy.querySelector("button[type=submit]");
    var pr = $(".product-info .price"); var note = $(".offline-note");
    if (!p) {
      if (btn) btn.disabled = true; var st = $("[data-sticky-buy]"); if (st) st.disabled = true;
      if (!note) { note = document.createElement("p"); note.className = "offline-note"; note.textContent = "Dieser Artikel ist derzeit nicht bestellbar. Schauen Sie gern in den Shop oder fragen Sie uns per Anfrage."; buy.parentNode.insertBefore(note, buy.nextSibling); }
      return;
    }
    if (note) note.remove(); if (btn) btn.disabled = false;
    if (pr && pr.firstChild && pr.firstChild.nodeType === 3) pr.firstChild.nodeValue = EUR(p.preis) + " ";
    var spr = $(".sticky-price"); if (spr) spr.textContent = EUR(p.preis);
    if (p.bilder.length) { var mi = $(".product-media img"); var b0 = p.bilder[0]; if (mi && b0 && b0.url) { mi.src = imgOf(p); if (b0.w) mi.width = b0.w; if (b0.h) mi.height = b0.h; if (b0.alt) mi.alt = b0.alt; } }
    var ld = $("#ld-json"); var pd = $("#produkt-daten");
    if (pd) { try { var d = JSON.parse(pd.textContent); d.price = p.preis.toFixed(2); renderLd(d); } catch (e) { /* weiter */ } }
  });

  /* ---------- Shop: Raster, Filter, Sortierung ---------- */
  var activeKat = "alle", sortBound = false, hashApplied = false;
  function applyFilter() {
    var grid = $("#shop-grid"); if (!grid) return;
    var cards = $$(".card", grid); var sort = $("#sortierung");
    var merk = merkIds(); var words = plain(suchterm).split(/\s+/).filter(Boolean);
    var vis = cards.filter(function (c) {
      var katOk = activeKat === "alle" || c.dataset.kat === activeKat || (c.dataset.tags || "").split(" ").indexOf(activeKat) >= 0 || (activeKat === "merk" && merk.indexOf(c.dataset.id) >= 0);
      if (!katOk) return false;
      var hay = plain(c.dataset.suche || c.dataset.name);
      return words.every(function (w) { return hay.indexOf(w) >= 0; });
    });
    cards.forEach(function (c) { c.style.display = vis.indexOf(c) >= 0 ? "" : "none"; });
    var mode = sort ? sort.value : "standard";
    vis.sort(function (a, b) {
      if (mode === "preis-auf") return a.dataset.preis - b.dataset.preis;
      if (mode === "preis-ab") return b.dataset.preis - a.dataset.preis;
      if (mode === "name") return a.dataset.name.localeCompare(b.dataset.name, "de");
      return a.dataset.pos - b.dataset.pos;
    }).forEach(function (c) { grid.appendChild(c); });
    var cnt = $("#treffer"); if (cnt) cnt.textContent = vis.filter(function (c) { return !c.classList.contains("card-gutschein"); }).length + " Artikel";
    var kt = $("#keine-treffer"); if (kt) kt.hidden = vis.length > 0 || !P.length;
  }
  function setChips() { $$(".chip").forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.kat === activeKat ? "true" : "false"); }); }
  function bindChips() {
    var wrap = $("#kat-chips"); if (!wrap) return;
    setChips(); ensureMerkChip();
    if (wrap.dataset.bound) return; wrap.dataset.bound = "1";
    wrap.addEventListener("click", function (e) { var ch = e.target.closest(".chip"); if (!ch) return; activeKat = ch.dataset.kat; setChips(); applyFilter(); });
  }
  function setupShop() {
    var grid = $("#shop-grid"); if (!grid) return;
    bindChips(); setupSearch(); renderZuletzt($("#zuletzt-host"), "");
    var sort = $("#sortierung"); if (sort && !sortBound) { sort.addEventListener("change", applyFilter); sortBound = true; }
    var hk = location.hash.replace("#", "");
    if (hk && !hashApplied) { hashApplied = true; var hc = $$(".chip").filter(function (c) { return c.dataset.kat === hk; })[0]; if (hc) hc.click(); }
  }
  setupShop();
  catalogHooks.push(function () {
    var grid = $("#shop-grid"); if (!grid) return;
    var vc = $(".card-gutschein", grid);
    P.forEach(function (p, i) { p._pos = i; });
    grid.innerHTML = P.map(function (p) { return cardHtml(p, "h2"); }).join("");
    if (vc && !(VOUCHER && VOUCHER.aktiv === false)) grid.appendChild(vc);
    var bar = $("#kat-chips");
    if (bar) {
      var keys = Object.keys(KAT).filter(function (k) { return P.some(function (p) { return p.kat === k; }); });
      P.forEach(function (p) { if (p.kat && keys.indexOf(p.kat) < 0) keys.push(p.kat); });
      if (keys.indexOf(activeKat) < 0 && activeKat !== "alle" && activeKat !== "personalisiert") activeKat = "alle";
      bar.innerHTML = '<button class="chip" type="button" data-kat="alle" aria-pressed="true">Alle</button>' +
        keys.map(function (k) { return '<button class="chip" type="button" data-kat="' + esc(k) + '" aria-pressed="false">' + esc(KAT[k] || k) + '</button>'; }).join("") +
        (P.some(function (p) { return p.text; }) ? '<button class="chip" type="button" data-kat="personalisiert" aria-pressed="false">Mit Wunschtext</button>' : "");
      bindChips();
    }
    setupSearch(); renderZuletzt($("#zuletzt-host"), "");
    if (!P.length) grid.insertAdjacentHTML("afterbegin", '<div class="empty" style="grid-column:1/-1"><p>Zurzeit ist kein Artikel bestellbar. Schreiben Sie uns gern: ' + contactLinks() + '.</p></div>');
    
    applyFilter();
  });
  /* Startseite: erste vier Artikel, Bestseller zuerst */
  catalogHooks.push(function () {
    var fg = $("#featured-grid"); if (!fg) return;
    var fsec = fg.closest("section"); if (fsec) fsec.hidden = !P.length;
    var best = P.filter(function (p) { return p.tags.indexOf("bestseller") >= 0; }); var rest = P.filter(function (p) { return p.tags.indexOf("bestseller") < 0; });
    fg.innerHTML = best.concat(rest).slice(0, P.length >= 5 ? 5 : P.length >= 3 ? 3 : P.length).map(function (p) { return cardHtml(p, "h3"); }).join("");
    var n = $("#alle-link"); if (n && P.length) n.textContent = P.length > 1 ? "Alle " + P.length + " Artikel ansehen" : "Zum Shop";
  });

  /* ---------- Formular-Hilfen (Portal: POST /api/anfrage) ---------- */
  function contactLinks() {
    var mail = CFG.email ? '<a href="mailto:' + CFG.email + '">' + CFG.email + "</a>" : "";
    var tel = CFG.telefon ? '<a href="tel:' + CFG.telefon.replace(/[^+\d]/g, "") + '">' + CFG.telefon + "</a>" : "";
    return [mail, tel].filter(Boolean).join(" oder ");
  }
  function fallbackHtml() {
    var alt = contactLinks();
    return "Das Senden hat gerade nicht geklappt. Bitte versuchen Sie es in ein paar Minuten noch einmal" + (alt ? " oder schreiben Sie uns direkt: " + alt : "") + ".";
  }
  var msgSeq = 0;
  function markInvalid(el, m) {
    el.setAttribute("aria-invalid", "true");
    if (m) { if (!m.id) m.id = "fehler-" + (++msgSeq); el.setAttribute("aria-describedby", m.id); }
  }
  function clearErrors(form) {
    $$(".field", form).forEach(function (f) { f.classList.remove("err"); var m = $(".msg", f); if (m) m.textContent = ""; $$("input,select,textarea", f).forEach(function (el) { el.removeAttribute("aria-invalid"); el.removeAttribute("aria-describedby"); }); });
    var a = $(".alert", form); if (a) { a.classList.remove("show"); a.innerHTML = ""; }
  }
  function showErrors(form, errors) {
    var first = null; var map = { adresse: "strasse", anschrift: "strasse" };
    Object.keys(errors || {}).forEach(function (name) {
      var el = form.querySelector('[name="' + (map[name] || name) + '"]'); if (!el) return;
      var f = el.closest(".field"); if (!f) return;
      f.classList.add("err"); var m = $(".msg", f); if (m) m.textContent = errors[name]; if (!first) first = el;
      markInvalid(el, m);
    });
    if (first) first.focus();
  }
  function showAlert(form, html, ok) {
    var a = $(".alert", form); if (!a) return;
    a.className = "alert show " + (ok ? "alert-ok" : "alert-err"); a.innerHTML = html; a.scrollIntoView({ block: "nearest" });
  }
  function validate(form) {
    var errors = {}; var isMail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    $$("[required]", form).forEach(function (el) {
      if (el.type === "checkbox") { if (!el.checked) errors[el.name] = el.dataset.err || "Bitte bestätigen."; return; }
      if (!el.value.trim()) errors[el.name] = el.dataset.err || "Bitte ausfüllen.";
      else if (el.type === "email" && !isMail.test(el.value.trim())) errors[el.name] = "Bitte eine gültige E-Mail-Adresse eingeben.";
    });
    return errors;
  }
  function send(data) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 15000) : null;
    return fetch(ROOT + "api/anfrage", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data), signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }, function () { return { status: r.status, body: null }; }); })
      .then(function (res) { if (timer) clearTimeout(timer); return res; }, function (e) { if (timer) clearTimeout(timer); throw e; });
  }
  function safePaypal(u) { return typeof u === "string" && /^https:\/\/(www\.)?paypal\.(com|me)\//i.test(u) ? u : ""; }
  /* fallbackTyp: kennt das Portal den Typ nicht, geht die Anfrage einmal als Kontakt-Anfrage mit Freitext raus */
  function bindForm(form, typ, extra, onDone, fallbackTyp, check) {
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors(form);
      var errors = validate(form);
      if (check) { var ce = check(); for (var ck in ce) errors[ck] = ce[ck]; }
      if (Object.keys(errors).length) { showErrors(form, errors); return; }
      var data = { typ: typ }; var priv = {};
      $$("input,select,textarea", form).forEach(function (el) {
        if (!el.name) return;
        if (el.type === "checkbox") { if (el.checked) data[el.name] = el.value || "ja"; return; }
        if (el.type === "radio") { if (el.checked) data[el.name] = el.value; return; }
        data[el.name] = el.value.trim();
      });
      if (data.website) return; /* Lockfeld gefüllt: nichts senden */
      data.website = "";
      if (extra) { var ex = extra(); for (var k in ex) data[k] = ex[k]; }
      Object.keys(data).forEach(function (k) { if (k.charAt(0) === "_") { priv[k] = data[k]; delete data[k]; } });
      var btn = form.querySelector('button[type=submit]'); var label = btn.textContent;
      btn.disabled = true; btn.textContent = "Wird gesendet …";
      send(data)
        .then(function (res) {
          var unbekannt = res.status === 400 || res.status === 404 || res.status === 501 || (res.status === 422 && res.body && res.body.errors && res.body.errors.typ);
          if (fallbackTyp && data.typ !== fallbackTyp && unbekannt) { data.typ = fallbackTyp; return send(data); }
          return res;
        })
        .then(function (res) {
          if (res.status === 429) { showAlert(form, "Zu viele Anfragen in kurzer Zeit. Bitte versuchen Sie es in einigen Minuten noch einmal.", false); return; }
          if (res.status === 422 && res.body && res.body.errors) {
            if (res.body.errors.summe || res.body.errors.positionen) {
              showAlert(form, "Die Preise im Shop haben sich geändert. Wir haben Ihren Warenkorb aktualisiert, bitte prüfen Sie die Summe und senden Sie die Bestellung erneut.", false);
              refreshCatalog(); return;
            }
            showErrors(form, res.body.errors); showAlert(form, "Bitte prüfen Sie die markierten Felder.", false); return;
          }
          if (res.body && res.body.ok && res.body.ref) {
            if (onDone) onDone();
            var pu = safePaypal(res.body.paypalUrl);
            try { sessionStorage.setItem("sw_paypal", JSON.stringify({ ref: res.body.ref, url: pu, gutschein: res.body.gutschein || null })); } catch (e2) { /* ohne Speicher weiter */ }
            var sm = priv._zuzahlen != null ? priv._zuzahlen : data.summe; if (typeof sm === "number") sm = EUR(sm);
            var q = "danke.html?typ=" + encodeURIComponent(data.typ) + "&ref=" + encodeURIComponent(res.body.ref);
            if (data.art) q += "&art=" + encodeURIComponent(data.art);
            if (sm) q += "&summe=" + encodeURIComponent(sm);
            if (data.zahlungsart) q += "&zahlung=" + encodeURIComponent(data.zahlungsart);
            if (data.lieferart) q += "&liefer=" + encodeURIComponent(data.lieferart);
            location.href = ROOT + q; return;
          }
          showAlert(form, fallbackHtml(), false);
        })
        .catch(function () { showAlert(form, fallbackHtml(), false); })
        .then(function () { btn.disabled = false; btn.textContent = label; });
    });
  }

  /* ---------- Kontakt / Widerruf ---------- */
  var kf = $("#kontaktformular"); if (kf) bindForm(kf, "kontakt");
  var wf = $("#widerrufsformular"); if (wf) bindForm(wf, "widerruf");

  /* ---------- Gutschein verkaufen (Formular) und einlösen (Kasse); Konfiguration aus GET /api/gutschein ---------- */
  var gf = $("#gutscheinformular");
  function voucherMin() { return (VOUCHER && Number(VOUCHER.min)) || 10; }
  function voucherMax() { return (VOUCHER && Number(VOUCHER.max)) || 500; }
  var updateAdr = function () {};
  if (gf) {
    var adr = $("#g-adresse", gf); var adrIn = $("#g-adr", gf);
    updateAdr = function () { var r = gf.querySelector("input[name=zustellung]:checked"); var post = !!r && /post/i.test(r.value); adr.hidden = !post; adrIn.required = post; adrIn.dataset.err = "Bitte die Postanschrift eintragen."; };
    gf.addEventListener("change", function (e) { if (e.target.name === "zustellung") updateAdr(); });
    bindForm(gf, "gutschein", function () {
      var frei = parseInt(($("[name=betrag_frei]", gf).value || "").trim(), 10);
      var fix = (gf.querySelector("input[name=betrag]:checked") || {}).value;
      var betrag = frei > 0 ? frei : parseInt(fix, 10);
      return { betrag: betrag, nachricht: "GUTSCHEIN " + betrag + " € · Zustellung: " + ((gf.querySelector("input[name=zustellung]:checked") || {}).value || "") + " · Für: " + ($("[name=empfaenger]", gf).value || "–") + " · Von: " + ($("[name=absender]", gf).value || "–") + " · Text: " + ($("[name=gutscheintext]", gf).value || "–") };
    }, null, null, function () {
      var errs = {}; var raw = ($("[name=betrag_frei]", gf).value || "").trim();
      if (raw) { var v = Number(raw); if (!(v >= voucherMin() && v <= voucherMax()) || Math.floor(v) !== v) errs.betrag_frei = "Bitte einen ganzen Betrag zwischen " + voucherMin() + " und " + voucherMax() + " Euro eingeben."; }
      return errs;
    });
  }
  function applyVoucher() {
    if (!VOUCHER) return;
    var active = VOUCHER.aktiv !== false;
    var card = $(".card-gutschein"); if (card && !active) card.remove();
    var codeBox = $("#gutscheincode-box"); if (codeBox) codeBox.hidden = !(active && VOUCHER.einloesen);
    if (!active && coupon) { coupon = null; if (renderCart) renderCart(); }
    if (!gf) return;
    var note = $(".offline-note", gf.parentNode);
    if (!active) {
      gf.hidden = true;
      if (!note) { note = document.createElement("p"); note.className = "offline-note"; note.innerHTML = "Geschenkgutscheine sind im Moment nicht bestellbar. Schreiben Sie uns gern: " + contactLinks() + "."; gf.parentNode.insertBefore(note, gf); }
      return;
    }
    gf.hidden = false; if (note) note.remove();
    var box = $("#g-betraege", gf);
    if (box && Array.isArray(VOUCHER.betraege) && VOUCHER.betraege.length) {
      var def = VOUCHER.betraege.indexOf(20) >= 0 ? 20 : VOUCHER.betraege[0];
      box.innerHTML = VOUCHER.betraege.map(function (a) { return '<label class="swatch"><input type="radio" name="betrag" value="' + esc(a) + '"' + (a === def ? " checked" : "") + '><span>' + esc(a) + ' €</span></label>'; }).join("");
    }
    var zs = $("#g-zustellung", gf);
    if (zs && Array.isArray(VOUCHER.zustellung) && VOUCHER.zustellung.length) {
      zs.innerHTML = '<legend style="font-weight:600;margin-bottom:8px">Zustellung</legend>' + VOUCHER.zustellung.map(function (z, i) { return '<label class="check"><input type="radio" name="zustellung" value="' + esc(z) + '"' + (i === 0 ? " checked" : "") + '> ' + esc(z) + '</label>'; }).join("");
      updateAdr();
    }
    var fr = $("#g-frei", gf); if (fr) { fr.min = voucherMin(); fr.max = voucherMax(); }
  }

  /* ---------- Strukturierte Daten für Suchmaschinen (Produktseite) ---------- */
  function renderLd(d) {
    var base = location.origin + location.pathname.replace(/produkt\/[^/]*$/, "");
    var ld = [{ "@context": "https://schema.org", "@type": "Product", "name": d.name, "description": d.description, "sku": d.sku, "image": [base + d.image], "material": d.material, "category": d.category,
      "brand": { "@type": "Brand", "name": d.brand },
      "offers": { "@type": "Offer", "url": base + d.url, "priceCurrency": "EUR", "price": d.price, "availability": "https://schema.org/MadeToOrder", "itemCondition": "https://schema.org/NewCondition", "seller": { "@type": "Organization", "name": d.seller },
        "shippingDetails": { "@type": "OfferShippingDetails", "shippingRate": { "@type": "MonetaryAmount", "value": d.shipping, "currency": "EUR" }, "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "DE" } },
        "hasMerchantReturnPolicy": { "@type": "MerchantReturnPolicy", "applicableCountry": "DE", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail", "returnFees": "https://schema.org/ReturnShippingFees" } } },
      { "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": d.breadcrumbs.map(function (b, i) { return { "@type": "ListItem", "position": i + 1, "name": b[0], "item": base + b[1] }; }) }];
    var sc = $("#ld-json"); if (!sc) { sc = document.createElement("script"); sc.type = "application/ld+json"; sc.id = "ld-json"; document.head.appendChild(sc); }
    sc.textContent = JSON.stringify(ld);
  }
  var pd0 = $("#produkt-daten");
  if (pd0) { try { renderLd(JSON.parse(pd0.textContent)); } catch (e) { /* ohne strukturierte Daten weiter */ } }

  /* ---------- Warenkorb-Seite ---------- */
  var renderCart = null;
  var cartPage = $("#warenkorb");
  if (cartPage) {
    var list = $("#cart-list"); var sumBox = $("#cart-summary"); var empty = $("#cart-empty"); var checkout = $("#bestellformular");
    var render = function () {
      var c = loadCart().filter(function (i) { return findProduct(i.id); });
      list.innerHTML = "";
      renderExtras(c);
      if (!c.length) { empty.hidden = false; sumBox.hidden = true; if (checkout) checkout.hidden = true; return; }
      empty.hidden = true; sumBox.hidden = false; if (checkout) checkout.hidden = false;
      c.forEach(function (i, idx) {
        var p = findProduct(i.id); var f = i.farbe ? colorName(i.farbe) : "";
        var el = document.createElement("div"); el.className = "cart-item";
        el.innerHTML = '<img src="' + esc(imgOf(p)) + '" width="84" height="63" alt="">' +
          '<div><h3><a href="' + esc(hrefOf(p)) + '">' + esc(p.name) + '</a></h3><div class="meta">' + (f ? "Farbe: " + esc(f) + " · " : "") + (i.text ? "Text: „" + esc(i.text) + "“ · " : "") + EUR(p.preis) + ' / Stück</div>' +
          '<div class="buyrow" style="margin-top:8px"><span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" min="1" max="99" value="' + i.menge + '" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span> <button type="button" class="remove">Entfernen</button></div></div>' +
          '<div class="line-price">' + EUR(p.preis * i.menge) + "</div>";
        var inp = $("input", el);
        $$(".qty button", el).forEach(function (b) { b.addEventListener("click", function () { setQty(idx, (parseInt(inp.value, 10) || 1) + parseInt(b.dataset.d, 10)); }); });
        inp.addEventListener("change", function () { setQty(idx, parseInt(inp.value, 10) || 1); });
        $(".remove", el).addEventListener("click", function () { var cc = loadCart(); cc.splice(idx, 1); saveCart(cc); render(); });
        list.appendChild(el);
      });
      var t = cartTotals(c);
      $("#s-zwischen").textContent = EUR(t.zwischensumme);
      $("#s-versand").textContent = t.versand === 0 ? "kostenlos" : EUR(t.versand);
      var vl = $("#s-versand-label"); if (vl) vl.textContent = t.abholung ? "Abholung in Celle" : "Versand (Deutschland)";
      var gr = $("#s-gutschein-row"); if (gr) { gr.hidden = !(coupon && t.gutschein > 0); $("#s-gutschein").textContent = "−" + EUR(t.gutschein); }
      var gl = $("#s-gesamt-label"); if (gl) gl.textContent = coupon ? "Zu zahlen" : "Gesamt";
      $("#s-gesamt").textContent = EUR(t.zuZahlen);
      var hint = $("#s-hint"); if (hint) hint.textContent = t.abholung ? "Abholung nach Terminabsprache, keine Versandkosten." : t.versand > 0 ? "Noch " + EUR(CFG.versandfreiAb - t.zwischensumme) + " bis zum kostenlosen Versand." : "Versandkostenfrei innerhalb Deutschlands.";
      var mailBtn = $("#cart-mail");
      if (mailBtn && CFG.email) {
        mailBtn.href = "mailto:" + CFG.email + "?subject=" + encodeURIComponent("Bestellung " + (CFG.marke || "")) + "&body=" + encodeURIComponent("Hallo " + (CFG.marke || "") + ",\n\nich möchte folgende Artikel bestellen:\n\n" + cartAsText(c) + "\n\nGesamt inkl. Versand: " + EUR(t.gesamt) + "\n\nLieferadresse:\n\n");
      }
    };
    var renderExtras = function (c) {
      var t = cartTotals(c); var prog = $("#ship-progress"); var cs = $("#cross-sell");
      if (!c.length) { if (prog) prog.hidden = true; if (cs) cs.hidden = true; return; }
      if (prog) {
        prog.hidden = t.abholung; var pct = Math.min(100, Math.round(t.zwischensumme / CFG.versandfreiAb * 100));
        $("#ship-fill").style.setProperty("--p", pct / 100); prog.classList.toggle("done", t.versand === 0);
        $("#ship-text").innerHTML = t.versand === 0 ? "<strong>Versandkostenfrei.</strong> Sie sparen " + EUR(CFG.versandPauschale) + "." : "Noch <strong>" + EUR(CFG.versandfreiAb - t.zwischensumme) + "</strong> bis zum kostenlosen Versand.";
      }
      if (cs) {
        var inCart = c.map(function (i) { return i.id; }); var rest = CFG.versandfreiAb - t.zwischensumme;
        var cands = P.filter(function (p) { return inCart.indexOf(p.id) < 0 && !p.text; });
        cands.sort(function (a, b) { var da = rest > 0 ? Math.abs(a.preis - rest) : a.preis; var db = rest > 0 ? Math.abs(b.preis - rest) : b.preis; return da - db; });
        var pick = cands.slice(0, 3); var g = $("#cross-sell-grid"); g.innerHTML = "";
        pick.forEach(function (p) {
          var el = document.createElement("article"); el.className = "card";
          el.innerHTML = '<a class="card-img" href="' + esc(hrefOf(p)) + '" tabindex="-1" aria-hidden="true"><img src="' + esc(imgOf(p)) + '" width="800" height="600" alt="" loading="lazy"></a><div class="card-body"><h3><a href="' + esc(hrefOf(p)) + '">' + esc(p.name) + '</a></h3><div class="price">' + EUR(p.preis) + '</div><button class="btn btn-primary" type="button" data-add="' + esc(p.id) + '">In den Warenkorb</button></div>';
          g.appendChild(el);
        });
        cs.hidden = pick.length === 0;
      }
    };
    var setQty = function (idx, v) { var c = loadCart(); c[idx].menge = Math.min(99, Math.max(1, v)); saveCart(c); render(); };
    render();
    renderCart = render;
    if (checkout) {
      var adrBox = $("#adresse-felder", checkout); var zaAbh = $("#zahlung-abholung", checkout);
      var applyLieferart = function () {
        var abh = lieferart() === "abholung";
        adrBox.hidden = abh; $$("input", adrBox).forEach(function (i) { i.required = !abh; });
        zaAbh.hidden = !abh;
        var pay = checkout.querySelector("input[name=zahlungsart][value=paypal]");
        if (!abh) pay.checked = true;
        render();
      };
      $$("input[name=lieferart]", checkout).forEach(function (r) { r.addEventListener("change", applyLieferart); });
      applyLieferart();
      catalogHooks.push(function () {
        var opt = checkout.querySelector("input[name=lieferart][value=abholung]");
        if (opt && CFG.abholung === false) { opt.closest("label").hidden = true; if (opt.checked) { checkout.querySelector("input[name=lieferart][value=versand]").checked = true; applyLieferart(); } }
        render();
      });
      var codeIn = $("#b-code", checkout), codeBtn = $("#code-pruefen", checkout), codeMsg = $("#code-msg", checkout), codeBusy = false;
      var setCodeMsg = function (txt, ok) { codeMsg.textContent = txt; codeMsg.className = "code-msg " + (txt ? (ok ? "ok" : "bad") : ""); };
      var fmtDate = function (iso) { var d = new Date(iso); return isNaN(d) ? iso : d.toLocaleDateString("de-DE"); };
      if (codeBtn) {
        codeBtn.addEventListener("click", function () {
          if (coupon) { coupon = null; codeIn.value = ""; codeIn.readOnly = false; codeBtn.textContent = "Einlösen"; setCodeMsg("", true); render(); return; }
          var code = codeIn.value.trim();
          if (!code) { setCodeMsg("Bitte den Gutscheincode eingeben.", false); return; }
          if (codeBusy) return; codeBusy = true; codeBtn.disabled = true; setCodeMsg("Wird geprüft …", true);
          fetch(ROOT + "api/gutschein/pruefen", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify({ code: code }) })
            .then(function (r) { if (r.status === 429) return { limit: true }; return r.json().then(function (j) { return { body: j }; }, function () { return { body: null }; }); })
            .then(function (res) {
              if (res.limit) { setCodeMsg("Bitte später noch einmal.", false); return; }
              var bd = res.body;
              if (bd && bd.ok && bd.gueltig && Number(bd.rest) > 0) {
                coupon = { code: code, rest: Number(bd.rest), ablauf: bd.ablauf || "" }; codeIn.readOnly = true; codeBtn.textContent = "Entfernen";
                setCodeMsg("Gutschein gilt: Guthaben " + EUR(coupon.rest) + (coupon.ablauf ? ", gültig bis " + fmtDate(coupon.ablauf) : "") + ".", true); render();
              } else setCodeMsg("Dieser Gutscheincode konnte nicht eingelöst werden.", false);
            })
            .catch(function () { setCodeMsg("Der Gutschein konnte gerade nicht geprüft werden. Bitte versuchen Sie es später noch einmal.", false); })
            .then(function () { codeBusy = false; codeBtn.disabled = false; });
        });
        codeIn.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); codeBtn.click(); } });
      }
      bindForm(checkout, "bestellung", function () {
        var c = loadCart().filter(function (i) { return findProduct(i.id); }); var t = cartTotals(c);
        var la = lieferart();
        var strasse = $("[name=strasse]", checkout).value, plz = $("[name=plz]", checkout).value, ort = $("[name=ort]", checkout).value;
        var adr = la === "abholung" ? "Abholung in Celle" : [strasse, plz + " " + ort].join(", ");
        var za = (checkout.querySelector("input[name=zahlungsart]:checked") || {}).value || "";
        var o = {
          art: "bestellung", lieferart: la, zahlungsart: za,
          adresse: la === "abholung" ? null : { strasse: strasse, plz: plz, ort: ort, land: "DE" },
          positionen: c.map(function (i) { var p = findProduct(i.id); return { id: p.id, name: p.name, farbe: i.farbe || "", farbeName: i.farbe ? colorName(i.farbe) : "", text: i.text || "", menge: i.menge, einzelpreis: p.preis }; }),
          zwischensumme: t.zwischensumme, versand: t.versand, summe: t.gesamt,
          bestellung: cartAsText(c), lieferadresse: adr, _zuzahlen: t.zuZahlen,
          nachricht: "BESTELLUNG über den Online-Shop\n\n" + cartAsText(c) + "\n\nZwischensumme: " + EUR(t.zwischensumme) + "\nLieferung: " + (la === "abholung" ? "Abholung in Celle" : "Versand") + "\nVersand: " + (t.versand === 0 ? "kostenlos" : EUR(t.versand)) + "\nGesamt: " + EUR(t.gesamt) + (coupon ? "\nGutschein " + coupon.code + ": −" + EUR(t.gutschein) + "\nZu zahlen: " + EUR(t.zuZahlen) : "") + "\nZahlungsart: " + za + "\nLieferadresse: " + adr + "\n\nAnmerkung des Kunden: " + ($("[name=anmerkung]", checkout).value || "–")
        };
        if (coupon) o.gutscheincode = coupon.code;
        return o;
      }, function () { saveCart([]); }, "kontakt");
    }
  }

  /* ---------- Danke-Seite ---------- */
  var danke = $("#danke");
  if (danke) {
    var q = {}; location.search.replace(/^\?/, "").split("&").forEach(function (kv) { var p = kv.split("="); if (p[0]) q[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || "").replace(/\+/g, " ")); });
    var refEl = $("#ref"); if (refEl) { if (q.ref) refEl.textContent = q.ref; else refEl.parentElement.hidden = true; }
    var isOrder = q.art === "bestellung" || q.typ === "bestellung";
    var isWiderruf = q.typ === "widerruf";
    var mode = isOrder ? "bestellung" : isWiderruf ? "widerruf" : q.typ === "gutschein" ? "gutschein" : "kontakt";
    $$("[data-show]").forEach(function (el) { el.hidden = el.dataset.show !== mode; if (el.dataset.show === mode && el.dataset.h1) $("#danke-h1").textContent = el.dataset.h1; });
    var pp = $("#paypal-link"); var payUrl = ""; var gInfo = null; var sp = null;
    try { sp = JSON.parse(sessionStorage.getItem("sw_paypal") || "null"); if (sp && sp.ref === q.ref) { payUrl = safePaypal(sp.url); gInfo = sp.gutschein || null; } else sp = null; } catch (e) { sp = null; }
    var paidByVoucher = !!(gInfo && Number(gInfo.zuZahlen) === 0);
    var amount = (q.summe || "").replace(/[^\d,]/g, "").replace(",", ".");
    if (!payUrl && !sp && CFG.paypalMe && amount) payUrl = CFG.paypalMe.replace(/\/$/, "") + "/" + amount + "EUR";
    if (pp) {
      if (isOrder && q.zahlung === "paypal" && payUrl && !paidByVoucher) { pp.href = payUrl; pp.parentElement.hidden = false; }
      else pp.parentElement.hidden = true;
    }
    var ph = $("#paypal-hinweis"); if (ph) ph.hidden = !(isOrder && q.zahlung === "paypal" && !payUrl && !paidByVoucher);
    var gh = $("#gutschein-hinweis");
    if (gh && isOrder && gInfo) { gh.textContent = paidByVoucher ? "Ihre Bestellung ist vollständig mit Gutschein bezahlt." : "Gutschein abgezogen: " + EUR(gInfo.abgezogen) + ". Noch zu zahlen: " + EUR(gInfo.zuZahlen) + "."; gh.hidden = false; }
    var ah = $("#abhol-hinweis"); if (ah) ah.hidden = !(isOrder && q.liefer === "abholung");
    var sumEl = $("#danke-summe"); if (sumEl && q.summe) sumEl.textContent = q.summe;
  }

  /* ---------- Kundenstimmen nur zeigen, wenn der Portal-Baustein Bewertungen liefert ---------- */
  var ks = $("#kundenstimmen");
  if (ks) {
    var slot = $('[data-mk="bewertungen"]', ks);
    var checkReviews = function () { if (slot && slot.children.length > 0 && slot.textContent.trim().length > 20) { ks.hidden = false; return true; } return false; };
    if (!checkReviews() && "MutationObserver" in window) {
      var mo = new MutationObserver(function () { if (checkReviews()) mo.disconnect(); });
      mo.observe(slot, { childList: true, subtree: true, characterData: true });
      setTimeout(function () { mo.disconnect(); checkReviews(); }, 20000);
    }
  }

  /* ---------- Besucherzahl (Portal, ohne Cookies) ---------- */
  try {
    if (navigator.sendBeacon) {
      var payload = JSON.stringify({ t: "pv", u: location.pathname, n: document.title, w: window.innerWidth });
      navigator.sendBeacon(ROOT + "api/e", new Blob([payload], { type: "application/json" }));
    }
  } catch (e) { /* still */ }

  /* ---------- Direktkauf von Produktkarten ---------- */
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-add]"); if (!b) return;
    var p = findProduct(b.dataset.add); if (!p) return;
    addToCart(p.id, p.farben[0] || "", "", 1);
    var card = b.closest(".card"); flyToCart(card && card.querySelector("img"));
    var label = b.textContent; b.textContent = "✓ Im Warenkorb"; b.disabled = true;
    setTimeout(function () { b.textContent = label; b.disabled = false; }, 1800);
    toast(p.name + " liegt im Warenkorb");
    if (cartPage) renderCart();
  });

  /* ---------- Sticky-Kaufleiste (Handy, Produktseite) ---------- */
  var stickyIO = null;
  function setupSticky() {
    var sticky = $(".sticky-buy"); if (!sticky || !buy) return;
    var submitBtn = buy.querySelector("button[type=submit]"); var form = buy;
    var sb = $("[data-sticky-buy]", sticky);
    sb.addEventListener("click", function () { submitBtn.scrollIntoView({ block: "center" }); if (form.requestSubmit) form.requestSubmit(); else submitBtn.click(); });
    if ("IntersectionObserver" in window) {
      if (stickyIO) stickyIO.disconnect();
      stickyIO = new IntersectionObserver(function (en) { sticky.classList.toggle("show", !en[0].isIntersecting && en[0].boundingClientRect.top < 0); }, { threshold: 0 });
      stickyIO.observe(submitBtn);
    }
  }
  setupSticky();

  /* ---------- Voraussichtliches Lieferdatum (Werktage) ---------- */
  function addWorkdays(d, n) { var x = new Date(d); while (n > 0) { x.setDate(x.getDate() + 1); if (x.getDay() !== 0 && x.getDay() !== 6) n--; } return x; }
  function fmt(d) { return d.toLocaleDateString("de-DE", { weekday: "short", day: "numeric", month: "long" }); }
  function initDelivery() {
    $$("[data-delivery]").forEach(function (el) {
      var now = new Date(); if (now.getHours() >= 14) now = addWorkdays(now, 1);
      var a = addWorkdays(now, (CFG.produktionMin || 2) + (CFG.versandMin || 2)); var b = addWorkdays(now, (CFG.produktionMax || 4) + (CFG.versandMax || 3));
      var r = $("[data-delivery-range]", el); if (r) r.textContent = "zwischen " + fmt(a) + " und " + fmt(b);
    });
  }
  initDelivery();

  /* ---------- Allgemeine Produktseite (Artikel, die nicht als eigene Datei existieren) ---------- */
  var dynDone = false;
  function renderProductPage(p, id) {
    var host = $("#produkt-dyn"); if (!host || dynDone) return; dynDone = true;
    if (!p) {
      host.innerHTML = '<h1>Artikel nicht gefunden</h1><p class="muted">Diesen Artikel gibt es nicht oder nicht mehr. Im Shop finden Sie alle aktuellen Artikel.</p><p><a class="btn btn-primary" href="' + ROOT + 'shop.html">Zum Shop</a></p>';
      document.title = "Artikel nicht gefunden · " + (CFG.marke || ""); return;
    }
    document.title = p.name + " · " + (CFG.marke || "");
    var sw = p.farben.map(function (k, j) { return '<label class="swatch"><input type="radio" name="farbe" value="' + esc(k) + '"' + (j === 0 ? " checked" : "") + '><span><i style="background:' + safeColor((FARBEN[k] || [])[1]) + '"></i>' + esc(colorName(k)) + '</span></label>'; }).join("");
    var textField = p.text ? '<div class="field"><label for="wunschtext">' + esc(p.textlabel) + '</label><input type="text" id="wunschtext" name="wunschtext" maxlength="' + p.textmax + '" required autocomplete="off"><p class="msg">Bitte den Wunschtext eintragen.</p></div>' : "";
    var specs = [["Maße", p.masse], ["Material", p.material], ["Gewicht", p.gewicht]].filter(function (r) { return r[1]; }).map(function (r) { return "<dt>" + r[0] + "</dt><dd>" + esc(r[1]) + "</dd>"; }).join("") +
      "<dt>Fertigung</dt><dd>Druck in " + esc(CFG.produktion || "2 bis 4 Werktagen") + ", dann Versand</dd>";
    var desc = esc(p.lang || p.kurz).split(/\n\s*\n/).map(function (s) { return "<p>" + s + "</p>"; }).join("");
    var imgs = p.bilder.length ? p.bilder : [{ url: imgOf(p) }];
    var main = imgs[0]; var mainUrl = typeof main === "string" ? main : main.url; var mainAlt = (main && main.alt) || p.name;
    var thumbs = imgs.length > 1 ? '<div class="thumbs">' + imgs.map(function (b, j) { var u = typeof b === "string" ? b : b.url; u = /^(\/|https?:)/.test(u) ? u : ROOT + u; return '<button type="button" data-img="' + esc(u) + '" data-alt="' + esc((b && b.alt) || p.name) + '"' + (j === 0 ? ' aria-current="true"' : "") + ' aria-label="Bild ' + (j + 1) + '"><img src="' + esc(u) + '" alt="" width="144" height="108"></button>'; }).join("") + "</div>" : "";
    var related = (p.verwandt.map(findProduct).filter(Boolean)).concat(P.filter(function (q) { return q.id !== p.id && q.kat === p.kat; })).concat(P.filter(function (q) { return q.id !== p.id; }));
    var seen = {}; related = related.filter(function (q) { if (seen[q.id] || q.id === p.id) return false; seen[q.id] = 1; return true; }).slice(0, 3);
    related.forEach(function (q, j) { q._pos = j; });
    var abh = CFG.abholung === false ? "" : ", oder Abholung in Celle";
    host.innerHTML = '<nav aria-label="Pfad" class="crumbs"><a href="' + ROOT + 'index.html">Start</a> › <a href="' + ROOT + 'shop.html">Shop</a> › ' + esc(KAT[p.kat] || "Artikel") + '</nav>' +
      '<div class="product"><div><div class="product-media"><img id="pd-img" src="' + esc(/^(\/|https?:)/.test(mainUrl) ? mainUrl : ROOT + mainUrl) + '" width="' + ((main && main.w) || 1200) + '" height="' + ((main && main.h) || 900) + '" alt="' + esc(mainAlt) + '"></div>' + thumbs + '</div>' +
      '<div class="product-info"><h1>' + esc(p.name) + '</h1><div class="kaufbox">' +
      '<p class="price">' + EUR(p.preis) + ' <small>' + esc(CFG.preishinweis || "") + ', zzgl. <a href="' + ROOT + 'versand.html">Versand</a></small></p><p>' + esc(p.kurz) + '</p>' +
      '<form id="kaufen" data-id="' + esc(p.id) + '" novalidate>' + (p.farben.length ? '<fieldset style="border:0;padding:0;margin:0 0 14px"><legend style="font-weight:600;margin-bottom:8px">Farbe</legend><div class="swatches">' + sw + '</div></fieldset>' : "") + textField +
      '<div class="buyrow"><span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" id="menge" name="menge" min="1" max="99" value="1" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span><button class="btn btn-primary" type="submit">In den Warenkorb</button></div>' +
      '<p class="added" role="status">Liegt im Warenkorb. <a href="' + ROOT + 'warenkorb.html">Zum Warenkorb</a> oder <a href="' + ROOT + 'shop.html">weiter stöbern</a>.</p></form>' +
      '<p class="delivery" data-delivery>Bestellen Sie heute, Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>' +
      '</div><details class="faq-item" open><summary>Maße und Material</summary><dl class="specs">' + specs + '</dl></details>' +
      '<details class="faq-item"><summary>Versand, Zahlung und Rückgabe</summary><dl class="konditionen"><dt>Versand</dt><dd>' + EUR(CFG.versandPauschale) + ', ab ' + EUR(CFG.versandfreiAb) + ' kostenlos</dd>' + (CFG.abholung === false ? "" : '<dt>Abholung</dt><dd>Celle, kostenlos, nach Terminabsprache</dd>') + '<dt>Zahlung</dt><dd>PayPal' + (CFG.abholung === false ? "" : " oder bei Abholung") + '</dd><dt>Rückgabe</dt><dd>' + (p.text ? "ausgeschlossen, weil nach Ihrem Text gefertigt" : "14 Tage") + '</dd></dl></details>' +
      '<h2 class="sub">Beschreibung</h2>' + desc +
      '<p class="small muted">Hinweis: 3D-gedruckte Teile zeigen feine Schichtlinien, das ist Teil des Verfahrens. Farben können je nach Filamentcharge leicht abweichen.</p>' +
      (p.text ? '<p class="small muted">Personalisierter Artikel: Nach Ihrer Freigabe des Textes ist der Kauf vom Widerruf ausgenommen (§ 312g Abs. 2 Nr. 1 BGB). <a href="' + ROOT + 'widerruf.html">Mehr dazu</a>.</p>' : "") + '</div></div>' +
      (related.length ? '<h2 style="margin-top:56px">Weitere Artikel</h2><div class="grid">' + related.map(function (q) { return cardHtml(q, "h3"); }).join("") + "</div>" : "");
    var sticky = document.createElement("div"); sticky.className = "sticky-buy"; sticky.setAttribute("aria-hidden", "true");
    sticky.innerHTML = '<span class="sticky-price">' + EUR(p.preis) + '</span><button class="btn btn-primary" type="button" data-sticky-buy>In den Warenkorb</button>'; document.body.appendChild(sticky);
    bindBuy($("#kaufen")); setupSticky(); initDelivery(); initPreview(); initGallery(); addMerkLink($("#kaufen")); trackSeen(p.id); renderZuletzt(host, p.id);
    $$(".thumbs button", host).forEach(function (tb) { tb.addEventListener("click", function () { var im = $("#pd-img"); im.src = tb.dataset.img; im.alt = tb.dataset.alt; $$(".thumbs button", host).forEach(function (x) { x.removeAttribute("aria-current"); }); tb.setAttribute("aria-current", "true"); }); });
  }

  /* ---------- Katalog aus dem Portal: GET /api/produkte (Rückfall: eingebaute Liste) ---------- */
  function fetchJson(path, ms) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, ms || 4000) : null;
    return fetch(ROOT + path, { headers: { "Accept": "application/json" }, signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { if (timer) clearTimeout(timer); if (!r.ok) throw new Error("http " + r.status); return r.json(); }, function (e) { if (timer) clearTimeout(timer); throw e; });
  }
  function fetchRaw(path, ms) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, ms || 4000) : null;
    return fetch(ROOT + path, { headers: { "Accept": "application/json" }, signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { if (timer) clearTimeout(timer); return r.json().then(function (j) { return { status: r.status, body: j }; }, function () { return { status: r.status, body: null }; }); }, function (e) { if (timer) clearTimeout(timer); throw e; });
  }
  /* GET /api/produkte/{id}: Artikel (normalisiert), null = Portal sagt "unbekannt oder inaktiv", undefined = nicht erreichbar */
  function fetchProduct(id) {
    return fetchRaw("api/produkte/" + encodeURIComponent(id)).then(function (res) {
      var a = res.body && (res.body.produkt || res.body);
      if (res.status === 200 && a && a.id) return norm(a);
      if (res.status === 404 && res.body && res.body.ok === false) return null;
      return undefined;
    }).catch(function () { return undefined; });
  }
  function applyCatalog(j) {
    if (!j || !Array.isArray(j.produkte)) return false;
    var list = j.produkte.filter(function (p) { return p && p.id && p.name && p.aktiv !== false; }).map(norm);
    list.sort(function (a, b) { return a.sort - b.sort; });
    P.length = 0; list.forEach(function (p) { P.push(p); });
    if (Array.isArray(j.farben)) { FARBEN = {}; j.farben.forEach(function (f) { if (f && f.key) FARBEN[f.key] = [f.name || f.key, f.hex || "#cccccc"]; }); }
    if (Array.isArray(j.kategorien)) { KAT = {}; j.kategorien.slice().sort(function (a, b) { return (a.sort || 0) - (b.sort || 0); }).forEach(function (k) { if (k && k.key) KAT[k.key] = k.name || k.key; }); }
    if (j.versand) {
      if (j.versand.pauschale != null) CFG.versandPauschale = Number(j.versand.pauschale);
      if (j.versand.versandfreiAb != null) CFG.versandfreiAb = Number(j.versand.versandfreiAb);
      if (j.versand.abholung != null) CFG.abholung = !!j.versand.abholung;
    }
    catalogLoaded = true; return true;
  }
  function runHooks() { if (catalogLoaded) catalogHooks.forEach(function (h) { try { h(); } catch (e) { /* ein Fehler stoppt nicht die anderen */ } }); }
  function refreshCatalog() {
    return fetchJson("api/produkte").then(function (j) { if (applyCatalog(j)) { try { sessionStorage.setItem(CKEY, JSON.stringify({ t: Date.now(), d: j })); } catch (e) { /* ohne Speicher */ } } }).catch(function () { /* Rückfall bleibt */ }).then(function () { if (!P.length) catalogLoaded = true; runHooks(); });
  }
  (function startCatalog() {
    var cached = null; try { cached = JSON.parse(sessionStorage.getItem(CKEY) || "null"); } catch (e) { cached = null; }
    var fromCache = cached && Date.now() - cached.t < 600000 && applyCatalog(cached.d);
    if (fromCache) runHooks();
    var settled = false;
    function settle() {
      if (settled) return; settled = true;
      if (!$("#produkt-dyn")) return;
      var m = location.search.match(/[?&]id=([^&]+)/); var id = m ? decodeURIComponent(m[1]) : "";
      fetchProduct(id).then(function (a) { renderProductPage(a === undefined ? findProduct(id) : a, id); });
    }
    if (fromCache) settle();
    refreshCatalog().then(settle);
    if ($("#shop-grid") || gf || $("#bestellformular")) {
      fetchRaw("api/gutschein").then(function (res) {
        if (res.status === 404) VOUCHER = { aktiv: false };
        else if (res.status === 200 && res.body) VOUCHER = res.body;
        else return;
        applyVoucher();
      }).catch(function () { /* Portal nicht erreichbar: Standardwerte der Seite */ });
    }
  })();


  /* ---------- Zusatzfunktionen: Suche, Merkliste, Zuletzt angesehen ---------- */
  var suchterm = "";
  function plain(t) { t = String(t || "").toLowerCase().replace(/ß/g, "ss"); try { t = t.normalize("NFD").replace(/[̀-ͯ]/g, ""); } catch (e) { /* ältere Browser */ } return t; }
  function lsList(k) { try { var l = JSON.parse(localStorage.getItem(k) || "[]"); return Array.isArray(l) ? l : []; } catch (e) { return []; } }
  function lsSave(k, l) { try { localStorage.setItem(k, JSON.stringify(l)); } catch (e) { /* privater Modus */ } }
  function merkIds() { return lsList("sw_merk"); }
  function setupSearch() {
    var si = $("#suche"); if (!si) return;
    si.hidden = P.length < 8;                                   // erst ab 8 Artikeln sinnvoll
    if (si.dataset.bound) return; si.dataset.bound = "1";
    si.addEventListener("input", function () { suchterm = si.value; applyFilter(); });
    var rs = $("#suche-zurueck"); if (rs) rs.addEventListener("click", function () { si.value = ""; suchterm = ""; activeKat = "alle"; setChips(); applyFilter(); si.focus(); });
  }
  var HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z"/></svg>';
  function decorateCards() {
    $$(".card[data-id]:not(.card-gutschein)").forEach(function (c) {
      if (c.querySelector(".merk")) return;
      var b = document.createElement("button"); b.type = "button"; b.className = "merk"; b.dataset.merk = c.dataset.id; b.dataset.name = c.dataset.name || ""; b.innerHTML = HEART; c.appendChild(b);
    });
    refreshMerk();
  }
  function ensureMerkChip() {
    var wrap = $("#kat-chips"); if (!wrap || $(".chip[data-kat=merk]", wrap)) return;
    var c = document.createElement("button"); c.className = "chip"; c.type = "button"; c.dataset.kat = "merk"; c.setAttribute("aria-pressed", activeKat === "merk" ? "true" : "false"); c.hidden = true; wrap.appendChild(c);
    refreshMerk();
  }
  function refreshMerk() {
    var l = merkIds();
    $$(".merk").forEach(function (b) {
      var on = l.indexOf(b.dataset.merk) >= 0; b.setAttribute("aria-pressed", on ? "true" : "false");
      b.setAttribute("aria-label", (on ? "Von der Merkliste entfernen: " : "Auf die Merkliste: ") + (b.dataset.name || ""));
    });
    $$(".merk-link").forEach(function (b) { var on = l.indexOf(b.dataset.merk) >= 0; b.setAttribute("aria-pressed", on ? "true" : "false"); b.textContent = on ? "Auf der Merkliste, entfernen" : "Auf die Merkliste"; });
    var chip = $(".chip[data-kat=merk]");
    if (chip) {
      chip.hidden = !l.length; chip.textContent = "Merkliste (" + l.length + ")";
      if (!l.length && activeKat === "merk") { activeKat = "alle"; setChips(); applyFilter(); } else if (activeKat === "merk") applyFilter();
    }
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-merk]"); if (!b) return;
    var id = b.dataset.merk, l = merkIds(), i = l.indexOf(id);
    if (i >= 0) l.splice(i, 1); else l.unshift(id);
    lsSave("sw_merk", l.slice(0, 50)); refreshMerk();
  });
  var decoQueued = false;
  if ("MutationObserver" in window) new MutationObserver(function () { if (decoQueued) return; decoQueued = true; requestAnimationFrame(function () { decoQueued = false; decorateCards(); }); }).observe(document.body, { childList: true, subtree: true });
  function trackSeen(id) { var l = lsList("sw_zuletzt").filter(function (x) { return x !== id; }); l.unshift(id); lsSave("sw_zuletzt", l.slice(0, 8)); }
  function renderZuletzt(host, excludeId) {
    if (!host) return;
    var old = $(".zuletzt", host.parentNode || host); if (old) old.remove();
    var ps = lsList("sw_zuletzt").filter(function (x) { return x !== excludeId; }).map(findProduct).filter(Boolean).slice(0, 4);
    if (!ps.length) return;
    ps.forEach(function (p, j) { p._pos = j; });
    var sec = document.createElement("section"); sec.className = "zuletzt";
    sec.innerHTML = '<h2 class="sub">Zuletzt angesehen</h2><div class="grid grid-small">' + ps.map(function (p) { return cardHtml(p, "h3"); }).join("") + "</div>";
    host.appendChild(sec);
  }
  function addMerkLink(form) {
    if (!form || $(".merk-link")) return;
    var p = document.createElement("p"); p.style.margin = "10px 0 0";
    p.innerHTML = '<button type="button" class="textlink merk-link" data-merk="' + esc(form.dataset.id) + '" aria-pressed="false">Auf die Merkliste</button>';
    form.parentNode.insertBefore(p, form.nextSibling); refreshMerk();
  }

  /* ---------- Wunschtext-Vorschau ---------- */
  function initPreview() {
    var inp = $("#wunschtext"); if (!inp || $(".vorschau")) return;
    var field = inp.closest(".field"); if (!field) return;
    var box = document.createElement("div"); box.className = "vorschau";
    box.innerHTML = '<div class="vorschau-tile" aria-hidden="true"><span class="vorschau-text"></span></div><p class="small muted">Vorschau zur Orientierung. Schrift und Größe stimmen wir vor dem Druck mit Ihnen ab.</p>';
    field.parentNode.insertBefore(box, field.nextSibling);
    var tile = $(".vorschau-tile", box), t = $(".vorschau-text", box);
    function update() {
      var v = inp.value.trim(), sw = $("input[name=farbe]:checked"), dot = sw && sw.nextElementSibling && sw.nextElementSibling.querySelector("i");
      var c = dot ? getComputedStyle(dot).backgroundColor : "rgb(201,210,204)";
      var m = c.match(/\d+/g) || [201, 210, 204]; var lum = (0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2]) / 255;
      tile.style.backgroundColor = c; tile.style.color = lum > 0.55 ? "#15231c" : "#f3f5f1";
      var txt = v || "Ihr Text"; t.textContent = txt; t.classList.toggle("leer", !v);
      t.style.fontSize = Math.max(18, Math.min(54, 600 / Math.max(txt.length, 8))) + "px";
    }
    inp.addEventListener("input", update);
    $$("input[name=farbe]").forEach(function (r) { r.addEventListener("change", update); });
    update();
  }

  /* ---------- Bildergalerie: Pfeile, Tastatur, Wischen ---------- */
  function initGallery() {
    var media = $(".product-media"), thumbs = $$(".thumbs button");
    if (!media || thumbs.length < 2 || media.dataset.gal) return; media.dataset.gal = "1";
    var img = $("img", media), idx = 0, cnt = document.createElement("span");
    media.tabIndex = 0; media.setAttribute("role", "group"); media.setAttribute("aria-label", "Bildergalerie, Pfeiltasten wechseln das Bild");
    cnt.className = "gal-count"; cnt.setAttribute("aria-hidden", "true");
    function mk(cls, label, ch) { var b = document.createElement("button"); b.type = "button"; b.className = "gal-btn " + cls; b.setAttribute("aria-label", label); b.textContent = ch; media.appendChild(b); return b; }
    var prev = mk("prev", "Vorheriges Bild", "‹"), next = mk("next", "Nächstes Bild", "›"); media.appendChild(cnt);
    function show(i, silent) {
      idx = (i + thumbs.length) % thumbs.length; var tb = thumbs[idx];
      img.src = tb.dataset.img; img.alt = tb.dataset.alt;
      thumbs.forEach(function (x) { x.removeAttribute("aria-current"); }); tb.setAttribute("aria-current", "true");
      cnt.textContent = (idx + 1) + " / " + thumbs.length;
      if (!silent) { media.classList.remove("wechsel"); void media.offsetWidth; media.classList.add("wechsel"); }
    }
    thumbs.forEach(function (tb, k) { tb.addEventListener("click", function () { show(k); }); var im = new Image(); im.src = tb.dataset.img; });
    prev.addEventListener("click", function () { show(idx - 1); }); next.addEventListener("click", function () { show(idx + 1); });
    media.addEventListener("keydown", function (e) { if (e.key === "ArrowLeft") { show(idx - 1); e.preventDefault(); } else if (e.key === "ArrowRight") { show(idx + 1); e.preventDefault(); } });
    var x0 = null;
    media.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    media.addEventListener("touchend", function (e) { if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null; if (Math.abs(dx) > 40) show(idx + (dx < 0 ? 1 : -1)); });
    show(0, true);
  }

  /* ---------- Aktionsband vor Weihnachten: letzter Bestelltag aus den Richtwerten ---------- */
  (function () {
    var seite = location.pathname.split("/").pop() || "index.html";
    if (/^(warenkorb|danke|404)/.test(seite)) return;
    try { if (sessionStorage.getItem("sw_aktion_zu")) return; } catch (e) { /* ohne Speicher: Band bleibt */ }
    var heute = new Date(); heute.setHours(0, 0, 0, 0);
    var liefer = new Date(heute.getFullYear(), 11, 23);              // Heiligabend ist der 24., Lieferung bis zum 23.
    if (heute > liefer || heute.getMonth() < 10) return;             // nur November und Dezember
    var tage = (CFG.produktionMax || 4) + (CFG.versandMax || 3) + 2;  // Druck + Versand + Bestätigung und Zahlung
    var d = new Date(liefer), n = 0;
    while (n < tage) { d.setDate(d.getDate() - 1); var w = d.getDay(); if (w !== 0 && w !== 6) n++; }
    if (heute > d) return;
    var el = document.createElement("aside"); el.className = "aktion"; el.setAttribute("aria-label", "Hinweis zu Weihnachten");
    var tag = d.toLocaleDateString("de-DE", { weekday: "long", day: "numeric", month: "long" });
    el.innerHTML = '<p>Als Geschenk zu Weihnachten: Bestellen Sie bis <strong>' + esc(tag) + '</strong>, dann kommt es nach unseren Richtwerten rechtzeitig an.' + (/^shop/.test(seite) ? "" : ' <a href="' + ROOT + 'shop.html">Zum Shop</a>') + '</p><button type="button" aria-label="Hinweis schließen">×</button>';
    $("button", el).addEventListener("click", function () { el.remove(); try { sessionStorage.setItem("sw_aktion_zu", "1"); } catch (e) { /* egal */ } });
    document.body.insertBefore(el, $(".site-header") || document.body.firstChild);
  })();

  // Start: Zusatzfunktionen auf statischen Produktseiten und der Shopseite
  if ($("#kaufen") && !$("#produkt-dyn")) {
    initPreview(); initGallery(); addMerkLink($("#kaufen")); trackSeen($("#kaufen").dataset.id);
    var mainEl = $("main") || document.body, zs = document.createElement("section"); zs.className = "section-tight"; zs.innerHTML = '<div class="wrap" id="zuletzt-host"></div>'; mainEl.appendChild(zs);
    renderZuletzt($("#zuletzt-host"), $("#kaufen").dataset.id);
  }
  decorateCards();

  updateBadge();
  try { sessionStorage.setItem("sw_logo", "1"); } catch (e) { /* ohne Speicher: Logo animiert jedes Mal */ }

  // Aufbau beim Scrollen: markierte Elemente bauen sich einmal in Stufen auf, wenn sie ins Bild kommen
  (function () {
    if (!("IntersectionObserver" in window) || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    var SEL = "main h2:not(.card h2), main .datei, .materialliste li, .ablauf li, .spaltenliste > div, .card";
    // Kein IntersectionObserver: Chrome zählt ein weggeschnittenes Ziel (clip-path) als unsichtbar und löst nie aus
    var pending = [], queued = false;
    function check() {
      queued = false; var n = 0, lim = window.innerHeight * 0.94;
      pending = pending.filter(function (el) {
        var r = el.getBoundingClientRect();
        if (r.bottom < 0) { el.classList.remove("pre"); return false; }  // übersprungen (Sprungmarke): sofort zeigen
        if (r.top > lim) return true;                                     // noch unterhalb: warten
        el.style.setProperty("--d", Math.min(n++, 4) * 0.06 + "s");
        el.classList.remove("pre"); el.classList.add("run"); return false;
      });
      if (!pending.length) { window.removeEventListener("scroll", ask); window.removeEventListener("resize", ask); }
    }
    function ask() { if (!queued) { queued = true; requestAnimationFrame(check); } }
    function scan(root) {
      $$(SEL, root || document).forEach(function (el) {
        if (el.classList.contains("rv") || el.closest(".hero-dark") || el.closest("[hidden]")) return;
        el.classList.add("rv", "pre"); pending.push(el);
      });
      if (pending.length) { window.addEventListener("scroll", ask, { passive: true }); window.addEventListener("resize", ask); ask(); }
    }
    scan();
    ["#featured-grid", "#shop-grid", ".grid-small"].forEach(function (g) {
      var node = $(g); if (!node) return;
      new MutationObserver(function () { scan(node); }).observe(node, { childList: true });
    });
  })();

  // Lieferzeit-Balken bauen sich einmal auf, sobald sie im Bild sind
  (function () {
    $$(".zeit, .danke-zeit").forEach(function (z) {
    if (!z || !("IntersectionObserver" in window) || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    z.classList.add("pre");
    new IntersectionObserver(function (en, io) {
      if (!en[0].isIntersecting) return;
      z.classList.remove("pre"); z.classList.add("run"); io.disconnect();
    }, { threshold: 0.4 }).observe(z);
    });
  })();
})();
