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
  var CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
  var VOUCHER = null, catalogLoaded = false, catalogHooks = [];

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
  function updateBadge() {
    var n = cartCount();
    $$(".cart-badge").forEach(function (b) { b.textContent = n; b.classList.toggle("show", n > 0); });
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
    return { zwischensumme: sum, versand: versand, gesamt: sum + versand, abholung: abholung };
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
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { $(".nav").classList.remove("open"); mb.setAttribute("aria-expanded", "false"); } });
  }

  /* ---------- Karten (gleiches Markup wie der Generator) ---------- */
  function cardHtml(p, h) {
    h = h || "h3"; var href = hrefOf(p);
    var badge = p.tags.indexOf("bestseller") >= 0 ? '<span class="badge badge-accent">Bestseller</span>' : p.tags.indexOf("neu") >= 0 ? '<span class="badge">Neu</span>' : (p.tags.indexOf("personalisiert") >= 0 || p.text) ? '<span class="badge">Personalisierbar</span>' : "";
    var action = p.text ? '<a class="btn btn-primary" href="' + esc(href) + '">Jetzt gestalten</a>' : '<button class="btn btn-primary" type="button" data-add="' + esc(p.id) + '">In den Warenkorb</button>';
    var tags = p.tags.concat(p.text && p.tags.indexOf("personalisiert") < 0 ? ["personalisiert"] : []).join(" ");
    return '<article class="card" data-kat="' + esc(p.kat) + '" data-tags="' + esc(tags) + '" data-preis="' + p.preis + '" data-name="' + esc(p.name) + '" data-pos="' + (p._pos || 0) + '">' +
      '<a class="card-img" href="' + esc(href) + '" tabindex="-1" aria-hidden="true"><img src="' + esc(imgOf(p)) + '" width="800" height="600" alt="" loading="lazy"></a>' +
      '<div class="card-body"><span class="card-cat">' + esc(KAT[p.kat] || "") + '</span><' + h + '><a href="' + esc(href) + '">' + esc(p.name) + '</a></' + h + '>' +
      '<p class="small muted" style="margin:0">' + esc(p.kurz) + '</p><div class="price">' + EUR(p.preis) + ' ' + badge + '</div>' +
      (p.farben.length > 1 ? '<span class="card-colors">in ' + p.farben.length + ' Farben</span>' : "") + action +
      '<a class="card-more" href="' + esc(href) + '">Details ansehen</a></div></article>';
  }

  /* ---------- Produktseite (Kaufformular) ---------- */
  var buy = null;
  function bindBuy(form) {
    buy = form; if (!form) return;
    var qtyIn = $("#menge", form);
    $$(".qty button", form).forEach(function (b) {
      b.addEventListener("click", function () { var v = parseInt(qtyIn.value, 10) || 1; v += parseInt(b.dataset.d, 10); qtyIn.value = Math.min(20, Math.max(1, v)); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var id = form.dataset.id;
      var farbe = (form.querySelector("input[name=farbe]:checked") || {}).value || "";
      var textEl = $("#wunschtext", form);
      var text = textEl ? textEl.value.trim() : "";
      if (textEl && textEl.required && !text) { textEl.focus(); textEl.closest(".field").classList.add("err"); return; }
      var menge = Math.min(20, Math.max(1, parseInt(qtyIn.value, 10) || 1));
      addToCart(id, farbe, text, menge);
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
    var sp = $(".sticky-price"); if (sp) sp.textContent = EUR(p.preis);
    var ld = $("#ld-json"); var pd = $("#produkt-daten");
    if (pd) { try { var d = JSON.parse(pd.textContent); d.price = p.preis.toFixed(2); renderLd(d); } catch (e) { /* weiter */ } }
  });

  /* ---------- Shop: Raster, Filter, Sortierung ---------- */
  var activeKat = "alle", sortBound = false, hashApplied = false;
  function applyFilter() {
    var grid = $("#shop-grid"); if (!grid) return;
    var cards = $$(".card", grid); var sort = $("#sortierung");
    var vis = cards.filter(function (c) { return activeKat === "alle" || c.dataset.kat === activeKat || (c.dataset.tags || "").split(" ").indexOf(activeKat) >= 0; });
    cards.forEach(function (c) { c.style.display = vis.indexOf(c) >= 0 ? "" : "none"; });
    var mode = sort ? sort.value : "standard";
    vis.sort(function (a, b) {
      if (mode === "preis-auf") return a.dataset.preis - b.dataset.preis;
      if (mode === "preis-ab") return b.dataset.preis - a.dataset.preis;
      if (mode === "name") return a.dataset.name.localeCompare(b.dataset.name, "de");
      return a.dataset.pos - b.dataset.pos;
    }).forEach(function (c) { grid.appendChild(c); });
    var cnt = $("#treffer"); if (cnt) cnt.textContent = vis.length + " Artikel";
  }
  function bindChips() {
    var chips = $$(".chip");
    chips.forEach(function (ch) {
      ch.setAttribute("aria-pressed", ch.dataset.kat === activeKat ? "true" : "false");
      ch.addEventListener("click", function () { activeKat = ch.dataset.kat; chips.forEach(function (x) { x.setAttribute("aria-pressed", x === ch ? "true" : "false"); }); applyFilter(); });
    });
  }
  function setupShop() {
    var grid = $("#shop-grid"); if (!grid) return;
    bindChips();
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
    var n = $("#shop-anzahl"); if (n) n.textContent = P.length;
    applyFilter();
  });
  /* Startseite: erste vier Artikel, Bestseller zuerst */
  catalogHooks.push(function () {
    var fg = $("#featured-grid"); if (!fg) return;
    var best = P.filter(function (p) { return p.tags.indexOf("bestseller") >= 0; }); var rest = P.filter(function (p) { return p.tags.indexOf("bestseller") < 0; });
    fg.innerHTML = best.concat(rest).slice(0, 4).map(function (p) { return cardHtml(p, "h3"); }).join("");
    var n = $("#alle-anzahl"); if (n) n.textContent = P.length;
  });

  /* ---------- Formular-Hilfen (Portal: POST /api/anfrage) ---------- */
  function fallbackHtml() {
    var mail = CFG.email ? '<a href="mailto:' + CFG.email + '">' + CFG.email + "</a>" : "";
    var tel = CFG.telefon ? '<a href="tel:' + CFG.telefon.replace(/[^+\d]/g, "") + '">' + CFG.telefon + "</a>" : "";
    var alt = [mail, tel].filter(Boolean).join(" oder ");
    return "Das Senden hat gerade nicht geklappt. Bitte versuchen Sie es in ein paar Minuten noch einmal" + (alt ? " oder schreiben Sie uns direkt: " + alt : "") + ".";
  }
  function clearErrors(form) {
    $$(".field", form).forEach(function (f) { f.classList.remove("err"); var m = $(".msg", f); if (m) m.textContent = ""; });
    var a = $(".alert", form); if (a) { a.classList.remove("show"); a.innerHTML = ""; }
  }
  function showErrors(form, errors) {
    var first = null; var map = { adresse: "strasse", anschrift: "strasse" };
    Object.keys(errors || {}).forEach(function (name) {
      var el = form.querySelector('[name="' + (map[name] || name) + '"]'); if (!el) return;
      var f = el.closest(".field"); if (!f) return;
      f.classList.add("err"); var m = $(".msg", f); if (m) m.textContent = errors[name]; if (!first) first = el;
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
  function bindForm(form, typ, extra, onDone, fallbackTyp) {
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors(form);
      var errors = validate(form);
      if (Object.keys(errors).length) { showErrors(form, errors); return; }
      var data = { typ: typ };
      $$("input,select,textarea", form).forEach(function (el) {
        if (!el.name) return;
        if (el.type === "checkbox") { if (el.checked) data[el.name] = el.value || "ja"; return; }
        if (el.type === "radio") { if (el.checked) data[el.name] = el.value; return; }
        data[el.name] = el.value.trim();
      });
      if (data.website) return; /* Lockfeld gefüllt: nichts senden */
      data.website = "";
      if (extra) { var ex = extra(); for (var k in ex) data[k] = ex[k]; }
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
            try { if (pu) sessionStorage.setItem("sw_paypal", JSON.stringify({ ref: res.body.ref, url: pu })); else sessionStorage.removeItem("sw_paypal"); } catch (e2) { /* ohne Speicher weiter */ }
            var sm = data.summe; if (typeof sm === "number") sm = EUR(sm);
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

  /* ---------- Gutschein (Betrag, Zustellung); Konfiguration aus GET /api/gutschein ---------- */
  var gf = $("#gutscheinformular");
  function voucherMin() { return (VOUCHER && Number(VOUCHER.min)) || 10; }
  if (gf) {
    var adr = $("#g-adresse", gf); var adrIn = $("#g-adr", gf);
    $$("input[name=zustellung]", gf).forEach(function (r) { r.addEventListener("change", function () { var post = r.value.indexOf("Post") === 0 && r.checked; adr.hidden = !post; adrIn.required = post; adrIn.dataset.err = "Bitte die Postanschrift eintragen."; }); });
    bindForm(gf, "gutschein", function () {
      var frei = parseInt(($("[name=betrag_frei]", gf).value || "").trim(), 10);
      var fix = (gf.querySelector("input[name=betrag]:checked") || {}).value;
      var betrag = frei >= voucherMin() ? frei : parseInt(fix, 10);
      return { betrag: betrag + " €", summe: EUR(betrag), nachricht: "GUTSCHEIN " + betrag + " € · Zustellung: " + ((gf.querySelector("input[name=zustellung]:checked") || {}).value || "") + " · Für: " + ($("[name=empfaenger]", gf).value || "–") + " · Von: " + ($("[name=absender]", gf).value || "–") + " · Text: " + ($("[name=gutscheintext]", gf).value || "–") };
    });
  }
  function applyVoucher() {
    if (!VOUCHER) return;
    var card = $(".card-gutschein"); if (card && VOUCHER.aktiv === false) card.remove();
    if (!gf) return;
    if (VOUCHER.aktiv === false) { gf.hidden = true; if (!$(".offline-note")) { var n = document.createElement("p"); n.className = "offline-note"; n.textContent = "Geschenkgutscheine sind im Moment nicht bestellbar. Schreiben Sie uns gern eine Nachricht."; gf.parentNode.insertBefore(n, gf); } return; }
    var box = $("#g-betraege", gf);
    if (box && Array.isArray(VOUCHER.betraege) && VOUCHER.betraege.length) {
      var def = VOUCHER.betraege.indexOf(20) >= 0 ? 20 : VOUCHER.betraege[0];
      box.innerHTML = VOUCHER.betraege.map(function (a) { return '<label class="swatch"><input type="radio" name="betrag" value="' + esc(a) + '"' + (a === def ? " checked" : "") + '><span>' + esc(a) + ' €</span></label>'; }).join("");
    }
    var fr = $("#g-frei", gf); if (fr) { fr.min = voucherMin(); if (VOUCHER.max) fr.max = VOUCHER.max; }
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
          '<div class="buyrow" style="margin-top:8px"><span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" min="1" max="20" value="' + i.menge + '" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span> <button type="button" class="remove">Entfernen</button></div></div>' +
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
      $("#s-gesamt").textContent = EUR(t.gesamt);
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
        $("#ship-fill").style.width = pct + "%"; prog.classList.toggle("done", t.versand === 0);
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
    var setQty = function (idx, v) { var c = loadCart(); c[idx].menge = Math.min(20, Math.max(1, v)); saveCart(c); render(); };
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
      bindForm(checkout, "bestellung", function () {
        var c = loadCart().filter(function (i) { return findProduct(i.id); }); var t = cartTotals(c);
        var la = lieferart();
        var strasse = $("[name=strasse]", checkout).value, plz = $("[name=plz]", checkout).value, ort = $("[name=ort]", checkout).value;
        var adr = la === "abholung" ? "Abholung in Celle" : [strasse, plz + " " + ort].join(", ");
        var za = (checkout.querySelector("input[name=zahlungsart]:checked") || {}).value || "";
        return {
          art: "bestellung", lieferart: la, zahlungsart: za,
          adresse: la === "abholung" ? null : { strasse: strasse, plz: plz, ort: ort, land: "DE" },
          positionen: c.map(function (i) { var p = findProduct(i.id); return { id: p.id, name: p.name, farbe: i.farbe || "", farbeName: i.farbe ? colorName(i.farbe) : "", text: i.text || "", menge: i.menge, einzelpreis: p.preis }; }),
          zwischensumme: Math.round(t.zwischensumme * 100) / 100, versand: Math.round(t.versand * 100) / 100, summe: Math.round(t.gesamt * 100) / 100,
          bestellung: cartAsText(c), lieferadresse: adr,
          nachricht: "BESTELLUNG über den Online-Shop\n\n" + cartAsText(c) + "\n\nZwischensumme: " + EUR(t.zwischensumme) + "\nLieferung: " + (la === "abholung" ? "Abholung in Celle" : "Versand DHL") + "\nVersand: " + (t.versand === 0 ? "kostenlos" : EUR(t.versand)) + "\nGesamt: " + EUR(t.gesamt) + "\nZahlungsart: " + za + "\nLieferadresse: " + adr + "\n\nAnmerkung des Kunden: " + ($("[name=anmerkung]", checkout).value || "–")
        };
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
    var pp = $("#paypal-link"); var payUrl = "";
    if (pp) {
      var amount = (q.summe || "").replace(/[^\d,]/g, "").replace(",", ".");
      try { var sp = JSON.parse(sessionStorage.getItem("sw_paypal") || "null"); if (sp && sp.ref === q.ref) payUrl = safePaypal(sp.url); } catch (e) { /* ohne Speicher */ }
      if (!payUrl && CFG.paypalMe && amount) payUrl = CFG.paypalMe.replace(/\/$/, "") + "/" + amount + "EUR";
      if (isOrder && q.zahlung === "paypal" && payUrl) { pp.href = payUrl; pp.parentElement.hidden = false; }
      else pp.parentElement.hidden = true;
    }
    var ph = $("#paypal-hinweis"); if (ph) ph.hidden = !(isOrder && q.zahlung === "paypal" && !payUrl);
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
  function renderProductPage() {
    var host = $("#produkt-dyn"); if (!host || dynDone) return; dynDone = true;
    var m = location.search.match(/[?&]id=([^&]+)/); var id = m ? decodeURIComponent(m[1]) : "";
    var p = findProduct(id);
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
      '<div class="product"><div><div class="product-media"><img id="pd-img" src="' + esc(/^(\/|https?:)/.test(mainUrl) ? mainUrl : ROOT + mainUrl) + '" width="1200" height="900" alt="' + esc(mainAlt) + '"></div>' + thumbs + '</div>' +
      '<div class="product-info"><span class="eyebrow">' + esc(KAT[p.kat] || "") + '</span><h1>' + esc(p.name) + '</h1>' +
      '<p class="price">' + EUR(p.preis) + ' <small>' + esc(CFG.preishinweis || "") + ', zzgl. <a href="' + ROOT + 'versand.html">Versand</a></small></p><p>' + esc(p.kurz) + '</p>' +
      '<form id="kaufen" data-id="' + esc(p.id) + '" novalidate>' + (p.farben.length ? '<fieldset style="border:0;padding:0;margin:0 0 14px"><legend style="font-weight:600;margin-bottom:8px">Farbe</legend><div class="swatches">' + sw + '</div></fieldset>' : "") + textField +
      '<div class="buyrow"><span class="qty"><button type="button" data-d="-1" aria-label="Menge verringern">−</button><input type="number" id="menge" name="menge" min="1" max="20" value="1" aria-label="Menge"><button type="button" data-d="1" aria-label="Menge erhöhen">+</button></span><button class="btn btn-primary" type="submit">In den Warenkorb</button></div>' +
      '<p class="added" role="status">Liegt im Warenkorb. <a href="' + ROOT + 'warenkorb.html">Zum Warenkorb</a> oder <a href="' + ROOT + 'shop.html">weiter stöbern</a>.</p></form>' +
      '<p class="delivery" data-delivery>Bestellen Sie heute, Lieferung voraussichtlich <strong data-delivery-range></strong>.</p>' +
      '<div class="trust-list"><span>' + CHECK + ' Versandfrei ab ' + EUR(CFG.versandfreiAb) + ', sonst ' + EUR(CFG.versandPauschale) + '</span><span>' + CHECK + (p.text ? ' Personalisiert für Sie gefertigt, Vorschau vor dem Druck' : ' 14 Tage Rückgaberecht') + '</span><span>' + CHECK + ' PayPal-Käuferschutz' + abh + '</span><span>' + CHECK + ' Nachdruck-Garantie bei Transportschäden</span></div>' +
      '<dl class="specs">' + specs + '</dl><h2 style="font-size:1.15rem">Beschreibung</h2>' + desc +
      '<p class="small muted">Hinweis: 3D-gedruckte Teile zeigen feine Schichtlinien, das ist Teil des Verfahrens. Farben können je nach Filamentcharge leicht abweichen.</p>' +
      (p.text ? '<p class="small muted">Personalisierter Artikel: Nach Ihrer Freigabe des Textes ist der Kauf vom Widerruf ausgenommen (§ 312g Abs. 2 Nr. 1 BGB). <a href="' + ROOT + 'widerruf.html">Mehr dazu</a>.</p>' : "") + '</div></div>' +
      (related.length ? '<h2 style="margin-top:40px">Oft zusammen bestellt</h2><div class="grid">' + related.map(function (q) { return cardHtml(q, "h3"); }).join("") + "</div>" : "");
    var sticky = document.createElement("div"); sticky.className = "sticky-buy"; sticky.setAttribute("aria-hidden", "true");
    sticky.innerHTML = '<span class="sticky-price">' + EUR(p.preis) + '</span><button class="btn btn-primary" type="button" data-sticky-buy>In den Warenkorb</button>'; document.body.appendChild(sticky);
    bindBuy($("#kaufen")); setupSticky(); initDelivery();
    $$(".thumbs button", host).forEach(function (tb) { tb.addEventListener("click", function () { var im = $("#pd-img"); im.src = tb.dataset.img; im.alt = tb.dataset.alt; $$(".thumbs button", host).forEach(function (x) { x.removeAttribute("aria-current"); }); tb.setAttribute("aria-current", "true"); }); });
  }

  /* ---------- Katalog aus dem Portal: GET /api/produkte (Rückfall: eingebaute Liste) ---------- */
  function fetchJson(path, ms) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, ms || 4000) : null;
    return fetch(ROOT + path, { headers: { "Accept": "application/json" }, signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) { if (timer) clearTimeout(timer); if (!r.ok) throw new Error("http " + r.status); return r.json(); }, function (e) { if (timer) clearTimeout(timer); throw e; });
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
    return fetchJson("api/produkte").then(function (j) { if (applyCatalog(j)) { try { sessionStorage.setItem(CKEY, JSON.stringify({ t: Date.now(), d: j })); } catch (e) { /* ohne Speicher */ } } }).catch(function () { /* Rückfall bleibt */ }).then(runHooks);
  }
  (function startCatalog() {
    var cached = null; try { cached = JSON.parse(sessionStorage.getItem(CKEY) || "null"); } catch (e) { cached = null; }
    var fromCache = cached && Date.now() - cached.t < 600000 && applyCatalog(cached.d);
    if (fromCache) runHooks();
    var settled = false;
    function settle() { if (settled) return; settled = true; renderProductPage(); }
    if (fromCache) settle();
    refreshCatalog().then(settle);
    if ($("#shop-grid") || gf) {
      fetchJson("api/gutschein").then(function (j) { VOUCHER = j; applyVoucher(); }).catch(function () { /* Standardwerte der Seite */ });
    }
  })();

  updateBadge();
})();
