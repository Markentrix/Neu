/* Schichtwerk Shop – Warenkorb, Formulare, Portal-Anbindung (Variante B: Website-API) */
(function () {
  "use strict";
  var CFG = window.SW_CONFIG || {};
  var P = window.SW_PRODUKTE || [];
  var FARBEN = window.SW_FARBEN || {};
  var KEY = "sw_warenkorb";
  var EUR = function (n) { return n.toFixed(2).replace(".", ",") + " €"; };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var ROOT = (document.body.getAttribute("data-root") || "");

  /* ---------- Warenkorb (nur im Browser des Besuchers, localStorage) ---------- */
  function loadCart() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } }
  function saveCart(c) { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) { /* privater Modus */ } updateBadge(); }
  function findProduct(id) { for (var i = 0; i < P.length; i++) if (P[i].id === id) return P[i]; return null; }
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
      var f = FARBEN[i.farbe] ? FARBEN[i.farbe][0] : i.farbe;
      return i.menge + "× " + p.name + " (" + f + (i.text ? ", Text: " + i.text : "") + ") à " + EUR(p.preis) + " = " + EUR(p.preis * i.menge);
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

  /* ---------- Produktseite ---------- */
  var buy = $("#kaufen");
  if (buy) {
    var qtyIn = $("#menge", buy);
    $$(".qty button", buy).forEach(function (b) {
      b.addEventListener("click", function () { var v = parseInt(qtyIn.value, 10) || 1; v += parseInt(b.dataset.d, 10); qtyIn.value = Math.min(20, Math.max(1, v)); });
    });
    buy.addEventListener("submit", function (e) {
      e.preventDefault();
      var id = buy.dataset.id;
      var farbe = (buy.querySelector("input[name=farbe]:checked") || {}).value;
      var textEl = $("#wunschtext", buy);
      var text = textEl ? textEl.value.trim() : "";
      if (textEl && textEl.required && !text) { textEl.focus(); textEl.closest(".field").classList.add("err"); return; }
      var menge = Math.min(20, Math.max(1, parseInt(qtyIn.value, 10) || 1));
      addToCart(id, farbe, text, menge);
      var ok = $(".added"); if (ok) { ok.classList.add("show"); }
      toast("In den Warenkorb gelegt");
    });
  }

  /* ---------- Shop-Filter ---------- */
  var grid = $("#shop-grid");
  if (grid) {
    var chips = $$(".chip"); var sort = $("#sortierung"); var cards = $$(".card", grid); var active = "alle";
    function apply() {
      var vis = cards.filter(function (c) { return active === "alle" || c.dataset.kat === active || (c.dataset.tags || "").split(" ").indexOf(active) >= 0; });
      cards.forEach(function (c) { c.style.display = vis.indexOf(c) >= 0 ? "" : "none"; });
      var mode = sort ? sort.value : "standard";
      vis.sort(function (a, b) {
        if (mode === "preis-auf") return a.dataset.preis - b.dataset.preis;
        if (mode === "preis-ab") return b.dataset.preis - a.dataset.preis;
        if (mode === "name") return a.dataset.name.localeCompare(b.dataset.name, "de");
        return a.dataset.pos - b.dataset.pos;
      }).forEach(function (c) { grid.appendChild(c); });
      var cnt = $("#treffer"); if (cnt) cnt.textContent = vis.length + (vis.length === 1 ? " Artikel" : " Artikel");
    }
    chips.forEach(function (ch) { ch.addEventListener("click", function () {
      chips.forEach(function (x) { x.setAttribute("aria-pressed", "false"); }); ch.setAttribute("aria-pressed", "true"); active = ch.dataset.kat; apply();
    }); });
    if (sort) sort.addEventListener("change", apply);
    var hashKat = location.hash.replace("#", "");
    if (hashKat) { var hc = chips.filter(function (c) { return c.dataset.kat === hashKat; })[0]; if (hc) hc.click(); }
  }

  /* ---------- Formular-Hilfen (Portal: POST /api/anfrage) ---------- */
  function fallbackHtml(form) {
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
    var first = null;
    Object.keys(errors || {}).forEach(function (name) {
      var el = form.querySelector('[name="' + name + '"]'); if (!el) return;
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
  function bindForm(form, typ, extra, onDone) {
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
      var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
      var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 15000) : null;
      fetch(ROOT + "api/anfrage", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data), signal: ctrl ? ctrl.signal : undefined })
        .then(function (r) {
          if (r.status === 429) { showAlert(form, "Zu viele Anfragen in kurzer Zeit. Bitte versuchen Sie es in einigen Minuten noch einmal.", false); return null; }
          return r.json().then(function (j) { return { status: r.status, body: j }; }, function () { return { status: r.status, body: null }; });
        })
        .then(function (res) {
          if (!res) return;
          if (res.status === 422 && res.body && res.body.errors) { showErrors(form, res.body.errors); showAlert(form, "Bitte prüfen Sie die markierten Felder.", false); return; }
          if (res.body && res.body.ok && res.body.ref) {
            if (onDone) onDone();
            var q = "danke.html?typ=" + encodeURIComponent(typ) + "&ref=" + encodeURIComponent(res.body.ref);
            if (data.art) q += "&art=" + encodeURIComponent(data.art);
            if (data.summe) q += "&summe=" + encodeURIComponent(data.summe);
            if (data.zahlungsart) q += "&zahlung=" + encodeURIComponent(data.zahlungsart);
            if (data.lieferart) q += "&liefer=" + encodeURIComponent(data.lieferart);
            location.href = ROOT + q; return;
          }
          showAlert(form, fallbackHtml(form), false);
        })
        .catch(function () { showAlert(form, fallbackHtml(form), false); })
        .then(function () { if (timer) clearTimeout(timer); btn.disabled = false; btn.textContent = label; });
    });
  }

  /* ---------- Kontakt / Widerruf ---------- */
  var kf = $("#kontaktformular"); if (kf) bindForm(kf, "kontakt");
  var wf = $("#widerrufsformular"); if (wf) bindForm(wf, "widerruf");
  var gf = $("#gutscheinformular");
  if (gf) {
    var adr = $("#g-adresse", gf); var adrIn = $("#g-adr", gf);
    $$("input[name=zustellung]", gf).forEach(function (r) { r.addEventListener("change", function () { var post = r.value.indexOf("Post") === 0 && r.checked; adr.hidden = !post; adrIn.required = post; adrIn.dataset.err = "Bitte die Postanschrift eintragen."; }); });
    bindForm(gf, "gutschein", function () {
      var frei = parseInt(($("[name=betrag_frei]", gf).value || "").trim(), 10);
      var fix = (gf.querySelector("input[name=betrag]:checked") || {}).value;
      var betrag = frei >= 10 ? frei : parseInt(fix, 10);
      return { betrag: betrag + " €", summe: EUR(betrag), nachricht: "GUTSCHEIN " + betrag + " € · Zustellung: " + ((gf.querySelector("input[name=zustellung]:checked") || {}).value || "") + " · Für: " + ($("[name=empfaenger]", gf).value || "–") + " · Von: " + ($("[name=absender]", gf).value || "–") + " · Text: " + ($("[name=gutscheintext]", gf).value || "–") };
    });
  }

  /* ---------- Strukturierte Daten für Suchmaschinen (Produktseite) ---------- */
  var pd = $("#produkt-daten");
  if (pd) {
    try {
      var d = JSON.parse(pd.textContent); var base = location.origin + location.pathname.replace(/produkt\/[^/]*$/, "");
      var ld = [{ "@context": "https://schema.org", "@type": "Product", "name": d.name, "description": d.description, "sku": d.sku, "image": [base + d.image], "material": d.material, "category": d.category,
        "brand": { "@type": "Brand", "name": d.brand },
        "offers": { "@type": "Offer", "url": base + d.url, "priceCurrency": "EUR", "price": d.price, "availability": "https://schema.org/MadeToOrder", "itemCondition": "https://schema.org/NewCondition", "seller": { "@type": "Organization", "name": d.seller },
          "shippingDetails": { "@type": "OfferShippingDetails", "shippingRate": { "@type": "MonetaryAmount", "value": d.shipping, "currency": "EUR" }, "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "DE" } },
          "hasMerchantReturnPolicy": { "@type": "MerchantReturnPolicy", "applicableCountry": "DE", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail", "returnFees": "https://schema.org/ReturnShippingFees" } } },
        { "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": d.breadcrumbs.map(function (b, i) { return { "@type": "ListItem", "position": i + 1, "name": b[0], "item": base + b[1] }; }) }];
      var sc = document.createElement("script"); sc.type = "application/ld+json"; sc.textContent = JSON.stringify(ld); document.head.appendChild(sc);
    } catch (e) { /* ohne strukturierte Daten weiter */ }
  }

  /* ---------- Warenkorb-Seite ---------- */
  var renderCart = null;
  var cartPage = $("#warenkorb");
  if (cartPage) {
    var list = $("#cart-list"); var sumBox = $("#cart-summary"); var empty = $("#cart-empty"); var checkout = $("#bestellformular");
    function render() {
      var c = loadCart().filter(function (i) { return findProduct(i.id); });
      list.innerHTML = "";
      renderExtras(c);
      if (!c.length) { empty.hidden = false; sumBox.hidden = true; if (checkout) checkout.hidden = true; return; }
      empty.hidden = true; sumBox.hidden = false; if (checkout) checkout.hidden = false;
      c.forEach(function (i, idx) {
        var p = findProduct(i.id); var f = FARBEN[i.farbe] ? FARBEN[i.farbe][0] : i.farbe;
        var el = document.createElement("div"); el.className = "cart-item";
        el.innerHTML = '<img src="' + ROOT + 'assets/img/produkte/' + p.id + '.webp" width="84" height="63" alt="">' +
          '<div><h3><a href="' + ROOT + 'produkt/' + p.id + '.html">' + p.name + '</a></h3><div class="meta">Farbe: ' + f + (i.text ? ' · Text: „' + escapeHtml(i.text) + '“' : "") + ' · ' + EUR(p.preis) + ' / Stück</div>' +
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
        mailBtn.href = "mailto:" + CFG.email + "?subject=" + encodeURIComponent("Bestellung Schichtwerk") + "&body=" + encodeURIComponent("Hallo Schichtwerk,\n\nich möchte folgende Artikel bestellen:\n\n" + cartAsText(c) + "\n\nGesamt inkl. Versand: " + EUR(t.gesamt) + "\n\nLieferadresse:\n\n");
      }
    }
    function renderExtras(c) {
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
          el.innerHTML = '<a class="card-img" href="' + ROOT + 'produkt/' + p.id + '.html" tabindex="-1" aria-hidden="true"><img src="' + ROOT + 'assets/img/produkte/' + p.id + '.webp" width="800" height="600" alt="" loading="lazy"></a><div class="card-body"><h3><a href="' + ROOT + 'produkt/' + p.id + '.html">' + p.name + '</a></h3><div class="price">' + EUR(p.preis) + '</div><button class="btn btn-primary" type="button" data-add="' + p.id + '">In den Warenkorb</button></div>';
          g.appendChild(el);
        });
        cs.hidden = pick.length === 0;
      }
    }
    function setQty(idx, v) { var c = loadCart(); c[idx].menge = Math.min(20, Math.max(1, v)); saveCart(c); render(); }
    function escapeHtml(s) { return s.replace(/[&<>"']/g, function (ch) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]; }); }
    render();
    renderCart = render;
    if (checkout) {
      var adrBox = $("#adresse-felder", checkout); var zaAbh = $("#zahlung-abholung", checkout);
      function applyLieferart() {
        var abh = lieferart() === "abholung";
        adrBox.hidden = abh; $$("input", adrBox).forEach(function (i) { i.required = !abh; });
        zaAbh.hidden = !abh;
        var pay = checkout.querySelector("input[name=zahlungsart][value=paypal]");
        if (!abh) pay.checked = true;
        render();
      }
      $$("input[name=lieferart]", checkout).forEach(function (r) { r.addEventListener("change", applyLieferart); });
      applyLieferart();
    }
    if (checkout) bindForm(checkout, "kontakt", function () {
      var c = loadCart().filter(function (i) { return findProduct(i.id); }); var t = cartTotals(c);
      var la = lieferart();
      var adr = la === "abholung" ? "Abholung in Celle" : [$("[name=strasse]", checkout).value, $("[name=plz]", checkout).value + " " + $("[name=ort]", checkout).value].join(", ");
      var za = (checkout.querySelector("input[name=zahlungsart]:checked") || {}).value || "";
      return {
        art: "bestellung",
        bestellung: cartAsText(c),
        zwischensumme: EUR(t.zwischensumme), versand: t.versand === 0 ? "kostenlos" : EUR(t.versand), summe: EUR(t.gesamt),
        lieferadresse: adr, zahlungsart: za, lieferart: la,
        nachricht: "BESTELLUNG über den Online-Shop\n\n" + cartAsText(c) + "\n\nZwischensumme: " + EUR(t.zwischensumme) + "\nLieferung: " + (la === "abholung" ? "Abholung in Celle" : "Versand DHL") + "\nVersand: " + (t.versand === 0 ? "kostenlos" : EUR(t.versand)) + "\nGesamt: " + EUR(t.gesamt) + "\nZahlungsart: " + za + "\nLieferadresse: " + adr + "\n\nAnmerkung des Kunden: " + ($("[name=anmerkung]", checkout).value || "–")
      };
    }, function () { saveCart([]); });
  }

  /* ---------- Danke-Seite ---------- */
  var danke = $("#danke");
  if (danke) {
    var q = {}; location.search.replace(/^\?/, "").split("&").forEach(function (kv) { var p = kv.split("="); if (p[0]) q[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || "").replace(/\+/g, " ")); });
    var refEl = $("#ref"); if (refEl) { if (q.ref) refEl.textContent = q.ref; else refEl.parentElement.hidden = true; }
    var isOrder = q.art === "bestellung";
    var isWiderruf = q.typ === "widerruf";
    var mode = isOrder ? "bestellung" : isWiderruf ? "widerruf" : q.typ === "gutschein" ? "gutschein" : "kontakt";
    $$("[data-show]").forEach(function (el) { el.hidden = el.dataset.show !== mode; if (el.dataset.show === mode && el.dataset.h1) $("#danke-h1").textContent = el.dataset.h1; });
    var pp = $("#paypal-link");
    if (pp) {
      var amount = (q.summe || "").replace(/[^\d,]/g, "").replace(",", ".");
      if (isOrder && q.zahlung === "paypal" && CFG.paypalMe && amount) { pp.href = CFG.paypalMe.replace(/\/$/, "") + "/" + amount + "EUR"; pp.parentElement.hidden = false; }
      else pp.parentElement.hidden = true;
    }
    var ph = $("#paypal-hinweis"); if (ph) ph.hidden = !(isOrder && q.zahlung === "paypal" && !(CFG.paypalMe && q.summe));
    var ah = $("#abhol-hinweis"); if (ah) ah.hidden = !(isOrder && q.liefer === "abholung");
    var sumEl = $("#danke-summe"); if (sumEl && q.summe) sumEl.textContent = q.summe;
  }

  /* ---------- Kundenstimmen nur zeigen, wenn der Portal-Baustein Bewertungen liefert ---------- */
  var ks = $("#kundenstimmen");
  if (ks) {
    var slot = $('[data-mk="bewertungen"]', ks);
    function checkReviews() { if (slot && slot.children.length > 0 && slot.textContent.trim().length > 20) { ks.hidden = false; return true; } return false; }
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
    addToCart(p.id, p.farben[0], "", 1);
    var label = b.textContent; b.textContent = "✓ Im Warenkorb"; b.disabled = true;
    setTimeout(function () { b.textContent = label; b.disabled = false; }, 1800);
    toast(p.name + " liegt im Warenkorb");
    if (cartPage) renderCart();
  });

  /* ---------- Sticky-Kaufleiste (Handy, Produktseite) ---------- */
  var sticky = $(".sticky-buy");
  if (sticky && buy) {
    var submitBtn = buy.querySelector("button[type=submit]");
    $("[data-sticky-buy]", sticky).addEventListener("click", function () { submitBtn.scrollIntoView({ block: "center" }); if (buy.requestSubmit) buy.requestSubmit(); else submitBtn.click(); });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (en) { var hidden = en[0].isIntersecting || en[0].boundingClientRect.top < 0 && false; sticky.classList.toggle("show", !en[0].isIntersecting && en[0].boundingClientRect.top < 0); }, { threshold: 0 }).observe(submitBtn);
    }
  }

  /* ---------- Voraussichtliches Lieferdatum (Werktage) ---------- */
  function addWorkdays(d, n) { var x = new Date(d); while (n > 0) { x.setDate(x.getDate() + 1); if (x.getDay() !== 0 && x.getDay() !== 6) n--; } return x; }
  function fmt(d) { return d.toLocaleDateString("de-DE", { weekday: "short", day: "numeric", month: "long" }); }
  $$("[data-delivery]").forEach(function (el) {
    var now = new Date(); if (now.getHours() >= 14) now = addWorkdays(now, 1);
    var a = addWorkdays(now, (CFG.produktionMin || 2) + (CFG.versandMin || 2)); var b = addWorkdays(now, (CFG.produktionMax || 4) + (CFG.versandMax || 3));
    var r = $("[data-delivery-range]", el); if (r) r.textContent = "zwischen " + fmt(a) + " und " + fmt(b);
  });

  updateBadge();
})();
