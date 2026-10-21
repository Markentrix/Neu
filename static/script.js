/* ElbDetail – Website-Skript. Ohne Abhängigkeiten. Drittanbieter (Google Analytics) nur nach Einwilligung. */
(function () {
  "use strict";

  var ELB = window.ELB || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var API = ELB.api || "/api";
  var IS_LIVE = (ELB.hosts || []).indexOf(location.hostname) !== -1;

  function fmt(v) { return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function waLink(text) { return "https://wa.me/" + ELB.whatsapp + (text ? "?text=" + encodeURIComponent(text) : ""); }
  function pkg(key) { return (ELB.packages || []).filter(function (p) { return p.key === key; })[0]; }
  function cls(key) { return (ELB.classes || []).filter(function (c) { return c.key === key; })[0]; }
  function price(pk, ck) { var p = pkg(pk); return p && p.prices ? p.prices[ck] : null; }
  function radio(form, name) { var el = form.querySelector('input[name="' + name + '"]:checked'); return el ? el.value : ""; }
  function deDate(iso) { if (!iso) return ""; var p = iso.split("-"); return p.length === 3 ? p[2] + "." + p[1] + "." + p[0] : iso; }
  function todayIso() { var t = new Date(); return t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") + "-" + String(t.getDate()).padStart(2, "0"); }
  function params() { var o = {}; location.search.replace(/^\?/, "").split("&").forEach(function (kv) { if (!kv) return; var p = kv.split("="); o[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || "").replace(/\+/g, " ")); }); return o; }
  var Q = params();
  var SPECIAL = { beratung: "Beratung / Einzelleistung", keramik: "Keramikversiegelung", care: "ElbDetail Care" };  // Anfragen ohne Paketpreis

  /* Verfügbarkeit (Sperrtage, Ruhetage, nächster freier Tag) – einmal laden, mehrfach nutzen */
  var availP = null;
  function availability() {
    if (!availP) availP = IS_LIVE ? fetch(API + "/verfuegbarkeit").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }) : Promise.resolve(null);
    return availP;
  }
  function niceDate(iso) {
    var d = new Date(iso + "T12:00:00"), t = new Date(); t.setHours(12, 0, 0, 0);
    var diff = Math.round((d - t) / 86400000);
    var txt = d.toLocaleDateString("de-DE", { weekday: "short", day: "numeric", month: "short" });
    return diff === 0 ? "heute, " + txt : diff === 1 ? "morgen, " + txt : txt;
  }

  /* ---------------------------------------------------------------- Statistik (eigener Server, cookielos) */
  var noTrack = navigator.doNotTrack === "1" || window.doNotTrack === "1" || navigator.globalPrivacyControl === true;
  function send(payload) {
    if (noTrack || !IS_LIVE) return;
    try {
      var body = JSON.stringify(payload);
      if (navigator.sendBeacon) navigator.sendBeacon(API + "/e", new Blob([body], { type: "application/json" }));
      else fetch(API + "/e", { method: "POST", body: body, headers: { "Content-Type": "application/json" }, keepalive: true });
    } catch (e) { /* Statistik ist optional */ }
  }
  function track(name, props) {
    send({ t: "ev", n: name, u: location.pathname, p: props || {} });
    if (window.gtag && gaOn) window.gtag("event", name.toLowerCase().replace(/[^a-z0-9äöüß]+/g, "_"), props || {});
  }

  /* ---------------------------------------------------------------- Google Analytics 4: nur nach Einwilligung */
  var GA = (window.ELB && ELB.ga4) || "", gaOn = false, CKEY = "elb-consent";
  var store = { get: function () { try { return localStorage.getItem(CKEY); } catch (e) { return null; } },
                set: function (v) { try { localStorage.setItem(CKEY, v); } catch (e) {} } };
  function loadGa() {
    if (!GA || gaOn || !/^G-[A-Z0-9]{4,}$/.test(GA)) return;
    gaOn = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", GA);
    var sc = document.createElement("script"); sc.async = true; sc.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA);
    document.head.appendChild(sc);
  }
  function dropGaCookies() {
    var host = location.hostname.replace(/^www\./, "");
    document.cookie.split(";").forEach(function (c) {
      var n = c.split("=")[0].trim();
      if (/^_ga/.test(n)) ["", "." + host, host].forEach(function (d) { document.cookie = n + "=; Max-Age=0; path=/" + (d ? "; domain=" + d : ""); });
    });
  }
  function consentBar() {
    if (document.getElementById("consent")) return;
    var bar = document.createElement("div");
    bar.id = "consent"; bar.className = "consent"; bar.setAttribute("role", "dialog"); bar.setAttribute("aria-live", "polite"); bar.setAttribute("aria-label", "Einwilligung Statistik");
    var dl = document.querySelector('a[href$="datenschutz.html"]'), dsHref = dl ? dl.getAttribute("href") : "datenschutz.html";
    bar.innerHTML = '<p><strong>Dürfen wir messen, was Ihnen gefällt?</strong> Mit Ihrer Einwilligung nutzen wir Google Analytics, um die Website zu verbessern. Dabei werden Cookies gesetzt und Daten an Google übermittelt. <a href="' + dsHref + '">Mehr in der Datenschutzerklärung</a></p>' +
      '<div class="consent-actions"><button type="button" class="btn btn-line-light" data-c="denied">Ablehnen</button><button type="button" class="btn btn-line-light" data-c="granted">Akzeptieren</button></div>';
    document.body.appendChild(bar);
    bar.addEventListener("click", function (e) {
      var b = e.target.closest("[data-c]"); if (!b) return;
      var v = b.getAttribute("data-c"); store.set(v);
      if (v === "granted") loadGa(); else { dropGaCookies(); if (gaOn) location.reload(); }
      bar.remove();
    });
  }
  if (GA) {
    if (store.get() === "granted") loadGa();
    else if (store.get() !== "denied") consentBar();
    document.addEventListener("click", function (e) { if (e.target.closest && e.target.closest("[data-consent-open]")) consentBar(); });
  }
  window.elbTrack = track;
  (function pageview() {
    var ref = "";
    try { if (document.referrer && new URL(document.referrer).hostname !== location.hostname) ref = new URL(document.referrer).hostname; } catch (e) {}
    send({ t: "pv", u: location.pathname, r: ref, w: window.innerWidth,
      utm: { s: Q.utm_source || "", m: Q.utm_medium || "", c: Q.utm_campaign || "" } });
  })();
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var h = a.getAttribute("href");
    if (h.indexOf("wa.me/") !== -1) track("WhatsApp-Klick", { ort: a.closest("[id]") ? a.closest("[id]").id : "" });
    else if (h.indexOf("tel:") === 0) track("Anruf-Klick");
    else if (h.indexOf("mailto:") === 0) track("E-Mail-Klick");
    else if (/termin\.html/.test(h)) track("Termin-Button", { ziel: h.split("?")[1] || "" });
  });

  /* ---------------------------------------------------------------- Navigation & Basis */
  function focusTarget(t) {
    var had = t.hasAttribute("tabindex");
    if (!had) t.setAttribute("tabindex", "-1");
    t.focus({ preventScroll: true });
    if (!had) t.addEventListener("blur", function () { t.removeAttribute("tabindex"); }, { once: true });
  }
  if (location.hash && /^#[\w-]+$/.test(location.hash)) {
    var toHash = function () { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView({ block: "start" }); };
    toHash();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(toHash);
    window.addEventListener("load", toHash);
  } else if (window.self !== window.top) {
    /* Eingebettet (z. B. Vorschau im Rahmen): Der äußere Rahmen behält beim Seitenwechsel seine Scrollposition.
       Neue Seiten daher oben beginnen lassen, außer bei Zurück/Vor oder wenn schon gescrollt wurde. */
    var nav = window.performance && performance.getEntriesByType ? performance.getEntriesByType("navigation")[0] : null;
    if (!nav || nav.type === "navigate") {
      var touched = false;
      ["wheel", "touchstart", "keydown", "pointerdown"].forEach(function (ev) { window.addEventListener(ev, function () { touched = true; }, { once: true, passive: true }); });
      var toTop = function () { if (touched) return; try { document.documentElement.scrollIntoView({ block: "start" }); } catch (e) { window.scrollTo(0, 0); } };
      toTop();
      window.addEventListener("load", toTop);
    }
  }
  document.addEventListener("click", function (e) {
    var link = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!link || e.defaultPrevented) return;
    var id = link.getAttribute("href").slice(1);
    var t = id ? document.getElementById(id) : null;
    if (t) {
      e.preventDefault();
      var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      t.scrollIntoView({ block: "start", behavior: reduceMotion ? "auto" : "smooth" });
      history.pushState(null, "", "#" + id); focusTarget(t);
    }
  });

  var header = $(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 24); };
    window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
  }
  var menuToggle = $("#menuToggle"), mobileNav = $("#mobileNav");
  if (menuToggle && mobileNav) {
    var setMenu = function (open) {
      menuToggle.setAttribute("aria-expanded", String(open));
      menuToggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
      mobileNav.hidden = !open;
    };
    menuToggle.addEventListener("click", function () { setMenu(menuToggle.getAttribute("aria-expanded") !== "true"); });
    $$("a", mobileNav).forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") { setMenu(false); menuToggle.focus(); } });
    document.addEventListener("click", function (e) { if (menuToggle.getAttribute("aria-expanded") === "true" && !e.target.closest(".site-header")) setMenu(false); });
    if (window.matchMedia) window.matchMedia("(min-width: 1100px)").addEventListener("change", function (e) { if (e.matches) setMenu(false); });
  }

  /* FAQ: sanftes Auf-/Zuklappen */
  $$(".faq-item").forEach(function (item) {
    var summary = $("summary", item), wrap = $(".faq-body-wrap", item);
    if (!summary || !wrap) return;
    summary.addEventListener("click", function (e) {
      e.preventDefault();
      if (item.hasAttribute("data-animating")) return;
      item.setAttribute("data-animating", "true");
      if (item.open) { wrap.style.gridTemplateRows = "1fr"; void wrap.offsetHeight; wrap.style.gridTemplateRows = "0fr"; }
      else { item.open = true; wrap.style.gridTemplateRows = "0fr"; void wrap.offsetHeight; wrap.style.gridTemplateRows = "1fr"; }
      setTimeout(function () { if (item.hasAttribute("data-animating")) { finish(); } }, 450);
    });
    function finish() {
      if (item.open && wrap.style.gridTemplateRows === "0fr") item.open = false;
      wrap.style.gridTemplateRows = ""; item.removeAttribute("data-animating");
    }
    wrap.addEventListener("transitionend", function (e) { if (e.propertyName === "grid-template-rows") finish(); });
  });

  /* ---------------------------------------------------------------- Richtpreis-Rechner (Startseite) */
  var quote = $("#quoteForm");
  if (quote) {
    quote.addEventListener("submit", function (e) { e.preventDefault(); });
    /* Preis zählt beim Umschalten kurz hoch oder runter, Screenreader hören nur den Endwert */
    var qv = $("#quoteValue"), qBox = qv && qv.parentNode, lastV = null;
    var qReduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    var showQuoteValue = function (v) {
      var from = lastV; lastV = v;
      var paint = function (n) { qv.innerHTML = "<small>ab</small>" + fmt(n) + " €"; };
      if (v == null) { qv.innerHTML = '<small>Preis</small>auf Anfrage'; return; }
      if (from == null || from === v || qReduce || !window.requestAnimationFrame) { paint(v); return; }
      qBox.setAttribute("aria-busy", "true");
      qBox.classList.remove("bump"); void qBox.offsetWidth; qBox.classList.add("bump");
      var t0 = null, dur = 480;
      var step = function (t) {
        if (t0 === null) t0 = t;
        var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        paint(Math.round(from + (v - from) * e));
        if (k < 1) requestAnimationFrame(step); else qBox.setAttribute("aria-busy", "false");
      };
      requestAnimationFrame(step);
    };
    var updateQuote = function (user) {
      var pk = radio(quote, "qpkg"), ck = radio(quote, "qclass"), p = pkg(pk), c = cls(ck), v = price(pk, ck);
      if (!p || !c) return;
      var onReq = v == null;  // z. B. Sportwagen / Premium-Segment: immer individuelles Angebot
      var note = $("#quoteNote");
      if (note) note.textContent = onReq
        ? (c.note || "Für dieses Fahrzeug erstellen wir nach einer kurzen Begutachtung ein individuelles Angebot.")
        : "Richtwert für normalen Pflegezustand. Der verbindliche Preis hängt von Fahrzeug und Zustand ab und wird vor dem Termin bestätigt.";
      $("#quoteBook").lastChild.textContent = onReq ? "Individuelles Angebot anfragen" : "Dieses Paket anfragen";
      showQuoteValue(v);
      $("#quotePkgName").textContent = p.name;
      $("#quoteBook").href = "termin.html?paket=" + pk + "&klasse=" + ck;
      $("#quoteWa").href = waLink("Hallo ElbDetail, ich interessiere mich für das Paket „" + p.name + "“ (" + c.name + (onReq ? ", bitte um ein individuelles Angebot" : ", Richtpreis ab " + fmt(v) + " €") + "). Fahrzeug: … Wunschtermin: …");
      if (user) track("Rechner genutzt", { paket: p.name, klasse: c.short });
    };
    quote.addEventListener("change", function () { updateQuote(true); });
    updateQuote(false);
  }

  /* Pakete: Fahrzeugklasse umschalten */
  var priceSwitch = $("#priceClass");
  if (priceSwitch) {
    var applyClass = function () {
      var ck = radio(priceSwitch, "pclass") || (ELB.classes[0] || {}).key, c = cls(ck);
      $$("[data-plan]").forEach(function (plan) {
        var pk = plan.getAttribute("data-plan"), v = price(pk, ck), p = pkg(pk);
        var amount = $(".amount", plan), from = $(".from", plan);
        if (amount) amount.textContent = v != null ? fmt(v) + " €" : "auf Anfrage";
        if (from) from.hidden = v == null;
        var book = $("[data-book]", plan); if (book) book.href = "termin.html?paket=" + pk + "&klasse=" + ck;
        var wa = $("[data-wa-plan]", plan); if (wa) wa.href = waLink("Hallo ElbDetail, ich möchte das Paket „" + p.name + "“ anfragen (" + c.name + (v != null ? ", Richtpreis ab " + fmt(v) + " €" : ", bitte um ein individuelles Angebot") + "). Fahrzeug: … Wunschtermin: …");
      });
      var lbl = $("#priceClassLabel"); if (lbl && c) lbl.textContent = c.name;
    };
    priceSwitch.addEventListener("change", applyClass); applyClass();
  }

  /* Faktenbox: auf schmalen Bildschirmen eingeklappt starten (im HTML offen für Suchmaschinen und ohne JS) */
  if (window.matchMedia && matchMedia("(max-width: 899.98px)").matches) $$("[data-close-narrow]").forEach(function (d) { d.open = false; });

  /* Nächster freier Tag (nur live, aus dem Kalender im Verwaltungsportal) */
  var nfEls = $$("[data-next-free]");
  if (nfEls.length) availability().then(function (j) {
    if (!j || !j.nextFree) return;
    nfEls.forEach(function (el) {
      var d = $("[data-nf-date]", el); if (d) d.textContent = niceDate(j.nextFree);
      if (el.tagName === "A") { var h = el.getAttribute("href") || "termin.html"; el.setAttribute("href", h + (h.indexOf("?") === -1 ? "?" : "&") + "datum=" + j.nextFree); }
      if (el.hasAttribute("data-nf-fill")) el.addEventListener("click", function () {
        var inp = document.getElementById("t-date1"); if (!inp) return;
        inp.value = j.nextFree; inp.dispatchEvent(new Event("change", { bubbles: true })); inp.focus();
      });
      el.hidden = false;
    });
  });

  /* Angebote: abgelaufene Karten sofort ausblenden (der Server veröffentlicht stündlich neu, das hier überbrückt die Zwischenzeit) */
  (function () {
    var td = todayIso();
    $$("[data-offer][data-until]").forEach(function (el) { if (el.getAttribute("data-until") < td) el.hidden = true; });
    $$("[data-offer-section]").forEach(function (sec) { if (!$("[data-offer]:not([hidden])", sec)) sec.hidden = true; });
  })();

  /* Lightbox für Zertifikate: native <dialog>, Esc und Klick daneben schließen; ohne JS öffnet der Link das Bild */
  var lbLinks = $$("a[data-lightbox]");
  if (lbLinks.length && window.HTMLDialogElement) {
    var dlg = document.createElement("dialog");
    dlg.className = "lightbox";
    dlg.innerHTML = '<button type="button" class="lightbox-close" aria-label="Schließen">×</button><img alt="">';
    document.body.appendChild(dlg);
    var lbImg = dlg.querySelector("img");
    dlg.addEventListener("click", function (e) { if (e.target === dlg || e.target.closest(".lightbox-close")) dlg.close(); });
    lbLinks.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var img = a.querySelector("img");
        lbImg.src = a.getAttribute("href"); lbImg.alt = img ? img.alt : "";
        dlg.showModal();
      });
    });
  }

  /* Vorher/Nachher-Slider */
  $$(".ba").forEach(function (ba) {
    var r = $('input[type="range"]', ba); if (!r) return;
    var set = function () { ba.style.setProperty("--pos", r.value + "%"); };
    r.addEventListener("input", set); set();
  });
  /* Kurzer Hinweis beim ersten Sichtkontakt: Der Regler wandert einmal hin und her, damit klar ist, dass man ihn ziehen kann */
  var baReduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!baReduce && "IntersectionObserver" in window && window.requestAnimationFrame) {
    var baHint = function (ba) {
      var r = $('input[type="range"]', ba); if (!r) return;
      var touched = false, stop = function () { touched = true; };
      ["pointerdown", "keydown", "touchstart"].forEach(function (ev) { r.addEventListener(ev, stop, { once: true, passive: true }); });
      var keys = [[0, 50], [550, 66], [1250, 36], [1800, 50]], t0 = null;
      var ease = function (k) { return k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; };
      var step = function (t) {
        if (touched) { ba.style.setProperty("--pos", r.value + "%"); return; }
        if (t0 === null) t0 = t;
        var e = t - t0, i = 1;
        while (i < keys.length - 1 && e > keys[i][0]) i++;
        var a = keys[i - 1], b = keys[i], k = Math.max(0, Math.min(1, (e - a[0]) / (b[0] - a[0])));
        ba.style.setProperty("--pos", (a[1] + (b[1] - a[1]) * ease(k)) + "%");
        if (e < keys[keys.length - 1][0]) requestAnimationFrame(step); else ba.style.setProperty("--pos", r.value + "%");
      };
      setTimeout(function () { requestAnimationFrame(step); }, 350);
    };
    var baIo = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { baIo.unobserve(en.target); baHint(en.target); } });
    }, { threshold: 0.6 });
    $$(".ba").forEach(function (ba) { baIo.observe(ba); });
  }

  /* Tastatur offen: Aktionsleiste ausblenden */
  var kbT;
  var isField = function (el) { return el && el.matches && el.matches("input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, select"); };
  document.addEventListener("focusin", function (e) { if (isField(e.target)) { clearTimeout(kbT); document.documentElement.classList.add("kb-open"); } });
  document.addEventListener("focusout", function () { clearTimeout(kbT); kbT = setTimeout(function () { if (!isField(document.activeElement)) document.documentElement.classList.remove("kb-open"); }, 120); });

  /* Google Maps erst nach Klick */
  var mapBtn = $("#loadMapBtn"), mapPh = $("#mapPlaceholder");
  if (mapBtn && mapPh) mapBtn.addEventListener("click", function () {
    var f = document.createElement("iframe");
    f.className = "map-frame"; f.loading = "lazy"; f.referrerPolicy = "no-referrer-when-downgrade";
    f.title = "Standort ElbDetail, Lachtehäuser Straße 1, 29223 Celle";
    f.src = "https://www.google.com/maps?q=Lachteh%C3%A4user%20Stra%C3%9Fe%201,%2029223%20Celle&output=embed";
    mapPh.replaceWith(f); track("Karte geladen");
  });

  /* ---------------------------------------------------------------- Formulare */
  var LABELS = {
    typ: null, website: null, einwilligung: null, quelle: null, name: "Name", telefon: "Telefon", email: "E-Mail", paket: "Paket",
    klasse: "Fahrzeugklasse", fahrzeug: "Fahrzeug", zustand: "Zustand", extras: "Extras", abholung: "Abholung", datum: "Wunschtermin",
    datum2: "Ausweichtermin", zeitfenster: "Zeitfenster", uhrzeit: "Uhrzeit", gutscheincode: "Gutscheincode", kanal: "Antwort per", nachricht: "Nachricht",
    bewertung_ok: null, art: "Gutschein", betrag: "Betrag", wunschbetrag: "Wunschbetrag", fuer: "Für", von: "Von", widmung: "Widmung",
    zustellung: "Zustellung", firma: "Firma", anzahl: "Fahrzeuge", intervall: "Intervall", leistungen: "Leistungen"
  };
  var TITLES = { kontakt: "Anfrage", termin: "Terminanfrage", gutschein: "Gutscheinbestellung", firma: "Firmenanfrage" };

  function collect(form) {
    var data = {};
    $$("input, select, textarea", form).forEach(function (el) {
      if (!el.name || el.disabled) return;
      if ((el.type === "checkbox" || el.type === "radio") && !el.checked) return;
      var v = el.value.trim();
      if (el.type === "checkbox" && form.querySelectorAll('input[type=checkbox][name="' + el.name + '"]').length > 1) {
        (data[el.name] = data[el.name] || []).push(v);
      } else data[el.name] = v;
    });
    return data;
  }
  function pretty(k, v) {
    if (k === "paket") { var p = pkg(v); return p ? p.name : (SPECIAL[v] || v); }
    if (k === "klasse") { var c = cls(v); return c ? c.name : v; }
    if (k === "datum" || k === "datum2") return deDate(v);
    if (k === "betrag" || k === "wunschbetrag") return v + " €";
    return Array.isArray(v) ? v.join(", ") : v;
  }
  function asText(data) {
    var lines = [];
    Object.keys(data).forEach(function (k) {
      if (LABELS[k] === null || !data[k] || (Array.isArray(data[k]) && !data[k].length)) return;
      lines.push((LABELS[k] || k) + ": " + pretty(k, data[k]));
    });
    return lines.join("\n");
  }
  function waFromForm(form) {
    var data = collect(form), typ = data.typ || "kontakt";
    return waLink("Hallo ElbDetail, hier meine " + (TITLES[typ] || "Anfrage") + ":\n" + asText(data));
  }
  function openWa(href) {
    var a = document.createElement("a"); a.href = href; a.target = "_blank"; a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
  }
  function setStatus(form, msg, kind, html) {
    var st = $(".form-status", form); if (!st) return;
    st.className = "form-status" + (kind ? " " + kind : "");
    if (html) st.innerHTML = html; else st.textContent = msg;
  }
  function fallbackHtml(form, reason) {
    var data = collect(form);
    var mail = "mailto:" + ELB.email + "?subject=" + encodeURIComponent((TITLES[data.typ] || "Anfrage") + " über die Website – " + (data.name || "")) +
      "&body=" + encodeURIComponent(asText(data));
    return '<span>' + reason + '</span><span class="fb-actions"><a class="btn btn-wa btn-sm" target="_blank" rel="noopener" href="' + waFromForm(form) +
      '">Per WhatsApp senden</a><a class="btn btn-line-light btn-sm" href="' + mail + '">Per E-Mail senden</a></span><span class="hint">Oder ruf an: ' + ELB.phoneDisplay + '</span>';
  }
  function validate(form, scope) {
    var ok = true, first = null;
    $$("input, select, textarea", scope || form).forEach(function (el) {
      if (!el.willValidate) return;
      var valid = el.checkValidity();
      if (el.type === "radio") valid = !el.required || !!form.querySelector('input[name="' + el.name + '"]:checked');
      el.setAttribute("aria-invalid", valid ? "false" : "true");
      if (!valid) { ok = false; first = first || el; }
    });
    if (form.getAttribute("data-form") === "kontakt" && (!scope || scope === form)) {
      var t = form.querySelector('[name="telefon"]'), m = form.querySelector('[name="email"]');
      if (t && m && !t.value.trim() && !m.value.trim()) { ok = false; first = first || t; t.setAttribute("aria-invalid", "true"); }
    }
    if (first) first.focus();
    return ok;
  }

  $$("form.js-form").forEach(function (form) {
    var typ = form.getAttribute("data-form");
    $$("[data-wa-from-form]", form).forEach(function (b) {
      b.addEventListener("click", function () { track("WhatsApp-Klick", { ort: "formular-" + typ }); openWa(waFromForm(form)); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.website && form.website.value) return;
      if (!validate(form)) { setStatus(form, "Bitte die markierten Pflichtfelder ausfüllen.", "error"); return; }
      var btn = form.querySelector('[type="submit"]:not([hidden])');
      if (!IS_LIVE) {
        setStatus(form, "", "info", fallbackHtml(form, "Vorschau-Modus: Auf dieser Vorschau wird das Formular nicht übertragen. Senden Sie die Angaben direkt:"));
        return;
      }
      if (btn) { btn.disabled = true; btn.classList.add("is-loading"); }
      setStatus(form, "Wird gesendet …", "");
      fetch(API + "/anfrage", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(collect(form)) })
        .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (j) { j.status = r.status; return j; }); })
        .then(function (j) {
          if (j.ok) {
            track("Anfrage gesendet", { typ: typ });
            location.href = "danke.html?typ=" + encodeURIComponent(typ) + (j.ref ? "&ref=" + encodeURIComponent(j.ref) : "") + (j.status === "reserviert" ? "&s=reserviert" : "");
          } else if (j.errors) {
            Object.keys(j.errors).forEach(function (k) { var el = form.querySelector('[name="' + k + '"]'); if (el) el.setAttribute("aria-invalid", "true"); });
            setStatus(form, j.message || "Bitte die markierten Angaben prüfen.", "error");
          } else throw new Error("server");
        })
        .catch(function () { setStatus(form, "", "error", fallbackHtml(form, "Die Anfrage konnte gerade nicht übertragen werden. Bitte senden Sie sie direkt:")); })
        .then(function () { if (btn) { btn.disabled = false; btn.classList.remove("is-loading"); } });
    });
    $$("input, select, textarea", form).forEach(function (el) {
      el.addEventListener("input", function () { if (el.getAttribute("aria-invalid") === "true" && el.checkValidity()) el.setAttribute("aria-invalid", "false"); });
    });
  });

  /* ---------------------------------------------------------------- Terminbuchung (Assistent) */
  var wz = $("#bookingForm");
  if (wz) {
    document.documentElement.classList.add("wz-ready");
    var steps = $$(".wz-step", wz), inds = $$("[data-step-ind]", wz), cur = 0;
    var prev = $("[data-wz-prev]", wz), next = $("[data-wz-next]", wz), submit = $("[data-wz-submit]", wz);
    var blocked = [], blockedKer = [], closedWeekdays = [0];

    if (Q.paket) { var rp = wz.querySelector('input[name="paket"][value="' + Q.paket + '"]'); if (rp) rp.checked = true; }
    if (Q.klasse) { var rk = wz.querySelector('input[name="klasse"][value="' + Q.klasse + '"]'); if (rk) rk.checked = true; }
    if (Q.quelle) wz.quelle.value = Q.quelle;
    if (Q.gutschein) wz.gutscheincode.value = Q.gutschein;
    ["datum", "datum2"].forEach(function (n) { if (wz[n]) wz[n].min = todayIso(); });

    if (Q.datum && /^\d{4}-\d{2}-\d{2}$/.test(Q.datum) && Q.datum >= todayIso() && wz.datum) wz.datum.value = Q.datum;
    availability().then(function (j) {
      if (!j) return;
      blocked = j.blocked || []; blockedKer = j.blockedKeramik || blocked; if (j.closedWeekdays) closedWeekdays = j.closedWeekdays;
    });

    function isKer() { var r = wz.querySelector('input[name="paket"]:checked'); return !!r && r.value === "keramik"; }
    /* Freie Abgabezeiten des gewählten Tages vom Server holen (Auslastung, Keramik-Standzeit, Google Kalender) */
    var slotBox = $("#t-slots"), slotMsg = $("#t-slots-msg"), slotReq = 0;
    function loadSlots() {
      if (!slotBox) return;
      var day = wz.datum.value, radios = $$('input[name="uhrzeit"]', wz);
      var say = function (t, err) { if (slotMsg) { slotMsg.textContent = t; slotMsg.className = "field-msg" + (err ? " error" : ""); } };
      if (!day || wz.datum.validationMessage) { radios.forEach(function (r) { r.disabled = !day; }); say(day ? "" : "Bitte zuerst einen Tag wählen."); return; }
      radios.forEach(function (r) { r.disabled = false; });
      if (!IS_LIVE) { say(""); return; }
      var my = ++slotReq, pk = (wz.querySelector('input[name="paket"]:checked') || {}).value || "";
      say("Freie Uhrzeiten werden geladen …");
      fetch(API + "/slots?tag=" + encodeURIComponent(day) + "&paket=" + encodeURIComponent(pk)).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
        if (my !== slotReq || !j || !j.slots) { say(""); return; }
        var free = 0;
        j.slots.forEach(function (x) {
          var r = wz.querySelector('input[name="uhrzeit"][value="' + x.zeit + '"]'); if (!r) return;
          r.disabled = !x.frei; if (!x.frei && r.checked) r.checked = false; if (x.frei) free++;
          r.parentNode.title = x.frei ? "" : "Bereits vergeben";
        });
        say(free ? free + (free === 1 ? " Uhrzeit" : " Uhrzeiten") + " frei an diesem Tag." : "An diesem Tag ist leider keine Uhrzeit mehr frei. Bitte einen anderen Tag wählen.", !free);
        summary();
      }).catch(function () { say(""); });
    }
    function checkDate(el) {
      var msg = $("#" + el.id + "-msg"), v = el.value, txt = "";
      if (v) {
        var d = new Date(v + "T12:00:00");
        if (v < todayIso()) txt = "Bitte ein Datum ab heute wählen.";
        else if (closedWeekdays.indexOf(d.getDay()) !== -1) txt = "An Sonntagen sind wir geschlossen. Bitte einen anderen Tag wählen.";
        else if (blocked.indexOf(v) !== -1) txt = "An diesem Tag sind wir leider ausgebucht oder geschlossen.";
        else if (isKer() && blockedKer.indexOf(v) !== -1) txt = "Für eine Keramikversiegelung brauchen wir die Halle einen ganzen Tag. An diesem Tag ist dafür leider kein Platz frei.";
      }
      el.setCustomValidity(txt);
      if (msg) { msg.textContent = txt; msg.className = "field-msg" + (txt ? " error" : ""); }
    }
    ["datum", "datum2"].forEach(function (n) { if (wz[n]) wz[n].addEventListener("change", function () { checkDate(wz[n]); if (n === "datum") loadSlots(); summary(); }); });
    $$('input[name="paket"]', wz).forEach(function (r) { r.addEventListener("change", function () { ["datum", "datum2"].forEach(function (n) { if (wz[n] && wz[n].value) checkDate(wz[n]); }); loadSlots(); }); });

    function show(i) {
      cur = Math.max(0, Math.min(steps.length - 1, i));
      steps.forEach(function (s, k) { s.hidden = k !== cur; });
      inds.forEach(function (li, k) { li.className = k < cur ? "done" : (k === cur ? "current" : ""); if (k === cur) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current"); });
      prev.hidden = cur === 0; next.hidden = cur === steps.length - 1; submit.hidden = cur !== steps.length - 1;
      track("Buchung Schritt", { schritt: cur + 1 });
    }
    function go(d) {
      if (d > 0 && !validate(wz, steps[cur])) { setStatus(wz, "Bitte die markierten Angaben ergänzen.", "error"); return; }
      setStatus(wz, "", "");
      show(cur + d);
      var lg = $("legend", steps[cur]); if (lg) { lg.setAttribute("tabindex", "-1"); lg.focus(); }
      var top = wz.getBoundingClientRect().top + window.scrollY - 110; if (window.scrollY > top) window.scrollTo({ top: top, behavior: "smooth" });
    }
    next.addEventListener("click", function () { go(1); });
    prev.addEventListener("click", function () { go(-1); });
    inds.forEach(function (li, k) { li.addEventListener("click", function () { if (k < cur) { cur = k; show(k); } }); });
    steps.forEach(function (s) { s.addEventListener("keydown", function (e) { if (e.key === "Enter" && e.target.tagName === "INPUT" && e.target.type !== "checkbox" && cur < steps.length - 1) { e.preventDefault(); go(1); } }); });

    function summary() {
      var d = collect(wz), p = pkg(d.paket), c = cls(d.klasse), v = p && c ? price(d.paket, d.klasse) : null;
      var set = function (k, t) { var el = wz.parentNode.querySelector('[data-sum="' + k + '"]'); if (el) el.textContent = t; };
      set("paket", p ? p.name : (SPECIAL[d.paket] || "–"));
      set("klasse", (c ? c.name : "–") + (d.fahrzeug ? " · " + d.fahrzeug : ""));
      set("extras", d.extras && d.extras.length ? d.extras.join(", ") : "keine");
      set("datum", d.datum ? deDate(d.datum) + (d.uhrzeit ? ", " + d.uhrzeit + " Uhr" : "") + (d.datum2 ? " (alt. " + deDate(d.datum2) + ")" : "") : "–");
      set("preis", v != null ? "ab " + fmt(v) + " €" : (SPECIAL[d.paket] ? "nach Begutachtung" : "–"));
      var bk = ELB.booking || {}, base = v != null ? v : (d.paket === "keramik" ? bk.keramikMin : null);
      set("anzahlung", base ? (Math.round(base * (bk.depositPercent || 15)) / 100).toFixed(2).replace(".", ",").replace(",00", "") + " € per PayPal" : (d.paket ? "nach Absprache" : "–"));
      $$("[data-price-for]", wz).forEach(function (el) { var x = price(el.getAttribute("data-price-for"), d.klasse || ELB.classes[0].key); el.textContent = x != null ? "ab " + fmt(x) + " €" : "auf Anfrage"; });
    }
    wz.addEventListener("change", summary); wz.addEventListener("input", summary);
    if (wz.datum.value) { checkDate(wz.datum); loadSlots(); } else loadSlots();
    summary(); show(0);
  }

  /* ---------------------------------------------------------------- Gutschein-Konfigurator */
  var vf = $("#voucherForm");
  if (vf) {
    var vp = $("#voucherPreview");
    var setVc = function (k, t) { var el = $('[data-vc="' + k + '"]', vp); if (el) el.textContent = t; };
    var updateV = function () {
      var art = radio(vf, "art");
      $(".vf-wert", vf).hidden = art !== "wert"; $(".vf-paket", vf).hidden = art !== "paket";
      if (art === "paket") {
        var p = pkg(vf.paket.value);
        setVc("value", p ? p.name : "Paket"); setVc("desc", "Fahrzeugaufbereitung für einen Kleinwagen" + (p ? " · Wert " + p.prices[ELB.classes[0].key] + " €" : ""));
      } else {
        var c = vf.wunschbetrag.value ? parseInt(vf.wunschbetrag.value, 10) : parseInt(radio(vf, "betrag") || "0", 10);
        setVc("value", (c || 0) + " €"); setVc("desc", "für eine Fahrzeugaufbereitung nach Wahl");
      }
      setVc("fuer", vf.fuer.value.trim() || "…"); setVc("von", vf.von.value.trim() || "…"); setVc("msg", vf.widmung.value.trim());
    };
    vf.addEventListener("input", updateV); vf.addEventListener("change", function (e) {
      if (e.target.name === "betrag") vf.wunschbetrag.value = "";
      updateV();
    });
    vf.wunschbetrag.addEventListener("input", function () { if (vf.wunschbetrag.value) $$('input[name="betrag"]', vf).forEach(function (r) { r.checked = false; }); });
    updateV();
  }

  /* Ratgeber-Filter */
  var grid = $("#articleGrid");
  if (grid) $$(".chip[data-filter]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var f = chip.getAttribute("data-filter");
      $$(".chip[data-filter]").forEach(function (c) { c.classList.toggle("is-active", c === chip); c.setAttribute("aria-pressed", String(c === chip)); });
      $$(".article-card", grid).forEach(function (card) { card.hidden = !!f && card.getAttribute("data-cat") !== f; });
    });
  });

  /* Danke-Seite */
  var thanks = $("[data-thanks-title]");
  if (thanks && Q.typ) {
    var T = {
      termin: Q.s === "reserviert"
        ? ["Bitte bestätigen Sie Ihren Termin.", "Wir haben Ihnen eine E-Mail mit einem Link geschickt. Mit der Anzahlung von " + ((ELB.booking || {}).depositPercent || 15) + " % per PayPal ist der Termin verbindlich gebucht. Die Reservierung gilt " + ((ELB.booking || {}).holdHours || 24) + " Stunden. Danach meldet sich " + ((ELB.booking || {}).owner || "unser Team") + " telefonisch und sieht sich Ihr Fahrzeug vorab an."]
        : ["Terminanfrage eingegangen.", "Wir prüfen Ihren Wunschtermin und melden uns mit Bestätigung und verbindlichem Angebot, in der Regel am selben oder nächsten Werktag."],
      gutschein: ["Gutscheinbestellung eingegangen.", "Sie erhalten gleich eine E-Mail mit den Zahlungsdaten. Nach Zahlungseingang senden wir Ihnen den Gutschein."],
      firma: ["Anfrage eingegangen.", "Vielen Dank für Ihr Interesse. Wir melden uns mit einem Vorschlag für Umfang, Intervalle und Konditionen."]
    }[Q.typ];
    if (T) { thanks.innerHTML = "Danke! <em>" + T[0] + "</em>"; var tt = $("[data-thanks-text]"); if (tt) tt.textContent = T[1] + (Q.ref ? " Ihre Vorgangsnummer: " + Q.ref + "." : ""); }
  }

  /* ---------------------------------------------------------------- Einblenden beim Scrollen */
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    document.documentElement.classList.add("js-anim");
    var ioSeen = false;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { ioSeen = true; en.target.classList.add("is-visible"); io.unobserve(en.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    $$(".reveal, [data-draw]").forEach(function (el) { io.observe(el); });
    /* Sicherheitsnetz nur, falls der Beobachter in dieser Umgebung gar nicht meldet: dann alles sofort zeigen */
    setTimeout(function () { if (!ioSeen) $$(".reveal:not(.is-visible), [data-draw]").forEach(function (el) { el.classList.add("is-visible"); }); }, 2500);
  }
  var y = $("#year"); if (y) y.textContent = String(new Date().getFullYear());
})();
