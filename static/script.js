/* ElbDetail – Website-Skript. Ohne Abhängigkeiten. Formulare, Termine und Statistik laufen über das Markentrix-Portal (relative /api-Adressen). */
(function () {
  "use strict";

  var ELB = window.ELB || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var API = ELB.api || "/api";
  var IS_LIVE = /^https?:$/.test(location.protocol);  // als Datei geöffnet: keine Portal-Schnittstelle, gleich die Ausweichwege zeigen
  /* Englische Fassung (/en/): Texte kommen aus config.js (ELB.t), {name} wird ersetzt. Ohne Eintrag bleibt der deutsche Text. */
  var EN = ELB.lang === "en", I18N = ELB.t || {};
  function t(s, v) { var r = I18N[s] || s; if (v) Object.keys(v).forEach(function (k) { r = r.split("{" + k + "}").join(v[k]); }); return r; }

  function fmt(v) { return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, EN ? "," : "."); }
  function eur(v) { return EN ? "€" + fmt(v) : fmt(v) + "\u00a0€"; }
  function eurCt(v) { var s = Number(v).toFixed(2).replace(".00", ""); return EN ? "€" + s : s.replace(".", ",") + "\u00a0€"; }
  function waLink(text) { return "https://wa.me/" + ELB.whatsapp + (text ? "?text=" + encodeURIComponent(text) : ""); }
  function pkg(key) { return (ELB.packages || []).filter(function (p) { return p.key === key; })[0]; }
  function cls(key) { return (ELB.classes || []).filter(function (c) { return c.key === key; })[0]; }
  function price(pk, ck, scope) {
    var p = pkg(pk); if (!p) return null;
    if (p.scope) { if (scope) return p.scope[scope] != null ? p.scope[scope] : null; var v = Object.keys(p.scope).map(function (k) { return p.scope[k]; }); return v.length ? Math.min.apply(null, v) : null; }  // Scheibenkeramik: Preis je Umfang, nicht je Fahrzeugklasse
    return p.prices ? p.prices[ck] : null;
  }
  function radio(form, name) { var el = form.querySelector('input[name="' + name + '"]:checked'); return el ? el.value : ""; }
  function deDate(iso) { if (!iso) return ""; var p = iso.split("-"), sep = EN ? "/" : "."; return p.length === 3 ? p[2] + sep + p[1] + sep + p[0] : iso; }
  function todayIso() { var n = new Date(); return n.getFullYear() + "-" + String(n.getMonth() + 1).padStart(2, "0") + "-" + String(n.getDate()).padStart(2, "0"); }
  function params() { var o = {}; location.search.replace(/^\?/, "").split("&").forEach(function (kv) { if (!kv) return; var p = kv.split("="); o[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || "").replace(/\+/g, " ")); }); return o; }
  var Q = params();
  var SPECIAL = { beratung: t("Beratung / Einzelleistung"), keramik: t("Keramikversiegelung"), care: "ElbDetail Care" };  // Anfragen ohne Paketpreis

  /* Verfügbarkeit (Sperrtage, Ruhetage, nächster freier Tag) – einmal laden, mehrfach nutzen */
  var availP = null;
  function availability() {
    if (!availP) availP = IS_LIVE ? fetch(API + "/verfuegbarkeit").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }) : Promise.resolve(null);
    return availP;
  }
  /* PayPal.me-Name kommt aus dem Portal (/api/verfuegbarkeit → paypalMe). Leer = kein Zahlungslink. */
  function payMeName(j) {
    var v = String((j && j.paypalMe) || "").trim().replace(/^(https?:\/\/)?(www\.)?paypal\.me\//i, "").replace(/\/+$/, "");
    return /^[A-Za-z0-9]{1,40}$/.test(v) ? v : "";
  }
  function niceDate(iso) {
    var d = new Date(iso + "T12:00:00"), now = new Date(); now.setHours(12, 0, 0, 0);  // nicht „t“ nennen: das ist die Übersetzungsfunktion
    var diff = Math.round((d - now) / 86400000);
    var txt = d.toLocaleDateString(EN ? "en-GB" : "de-DE", { weekday: "short", day: "numeric", month: "short" });
    return diff === 0 ? t("heute, {d}", { d: txt }) : diff === 1 ? t("morgen, {d}", { d: txt }) : txt;
  }

  /* ---------------------------------------------------------------- Statistik über das Portal (/api/e), cookielos */
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
  }

  /* Cookie-Hinweis und Statistik-Einstellungen liefert das Portal (Baustein data-mk="cookies" im Fußbereich). */
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
  function focusTarget(el) {
    var had = el.hasAttribute("tabindex");
    if (!had) el.setAttribute("tabindex", "-1");
    el.focus({ preventScroll: true });
    if (!had) el.addEventListener("blur", function () { el.removeAttribute("tabindex"); }, { once: true });
  }
  if (location.hash && /^#[\w-]+$/.test(location.hash)) {
    var toHash = function () { var el = document.getElementById(location.hash.slice(1)); if (el) el.scrollIntoView({ block: "start" }); };
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
    var el = id ? document.getElementById(id) : null;
    if (el) {
      e.preventDefault();
      var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      el.scrollIntoView({ block: "start", behavior: reduceMotion ? "auto" : "smooth" });
      history.pushState(null, "", "#" + id); focusTarget(el);
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
      menuToggle.setAttribute("aria-label", open ? t("Menü schließen") : t("Menü öffnen"));
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
      var paint = function (n) { qv.innerHTML = "<small>" + t("ab") + "</small>" + eur(n); };
      if (v == null) { qv.innerHTML = "<small>" + t("Preis") + "</small>" + t("auf Anfrage"); return; }
      if (from == null || from === v || qReduce || !window.requestAnimationFrame) { paint(v); return; }
      qBox.setAttribute("aria-busy", "true");
      qBox.classList.remove("bump"); void qBox.offsetWidth; qBox.classList.add("bump");
      var t0 = null, dur = 480;
      var step = function (ts) {
        if (t0 === null) t0 = ts;
        var k = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - k, 3);
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
        ? (c.note || t("Für dieses Fahrzeug erstellen wir nach einer kurzen Begutachtung ein individuelles Angebot."))
        : t("Richtwert für normalen Pflegezustand. Der verbindliche Preis hängt von Fahrzeug und Zustand ab und wird vor dem Termin bestätigt.");
      $("#quoteBook").lastChild.textContent = onReq ? t("Individuelles Angebot anfragen") : t("Dieses Paket anfragen");
      showQuoteValue(v);
      $("#quotePkgName").textContent = p.name;
      $("#quoteBook").href = "termin.html?paket=" + pk + "&klasse=" + ck;
      $("#quoteWa").href = waLink(t("Hallo ElbDetail, ich interessiere mich für das Paket „{paket}“ ({klasse}). Fahrzeug: … Wunschtermin: …",
        { paket: p.name, klasse: c.name + (onReq ? t(", bitte um ein individuelles Angebot") : t(", Richtpreis ab {preis}", { preis: eur(v) })) }));
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
        if (amount) amount.textContent = v != null ? eur(v) : t("auf Anfrage");
        if (from) from.hidden = v == null;
        var book = $("[data-book]", plan); if (book) book.href = "termin.html?paket=" + pk + "&klasse=" + ck;
        var wa = $("[data-wa-plan]", plan); if (wa) wa.href = waLink(t("Hallo ElbDetail, ich möchte das Paket „{paket}“ anfragen ({klasse}). Fahrzeug: … Wunschtermin: …",
          { paket: p.name, klasse: c.name + (v != null ? t(", Richtpreis ab {preis}", { preis: eur(v) }) : t(", bitte um ein individuelles Angebot")) }));
      });
      var lbl = $("#priceClassLabel"); if (lbl && c) lbl.textContent = c.name;
    };
    priceSwitch.addEventListener("change", applyClass); applyClass();
  }

  /* Faktenbox: auf schmalen Bildschirmen eingeklappt starten (im HTML offen für Suchmaschinen und ohne JS) */
  if (window.matchMedia && matchMedia("(max-width: 899.98px)").matches) $$("[data-close-narrow]").forEach(function (d) { d.open = false; });

  /* Nächster freier Tag (aus dem Markentrix-Portal, /api/verfuegbarkeit) */
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
    dlg.innerHTML = '<button type="button" class="lightbox-close" aria-label="' + t("Schließen") + '">×</button><img alt="">';
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
      var step = function (ts) {
        if (touched) { ba.style.setProperty("--pos", r.value + "%"); return; }
        if (t0 === null) t0 = ts;
        var e = ts - t0, i = 1;
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
    f.title = t("Standort ElbDetail, Lachtehäuser Straße 1, 29223 Celle");
    f.src = "https://www.google.com/maps?q=Lachteh%C3%A4user%20Stra%C3%9Fe%201,%2029223%20Celle&output=embed";
    mapPh.replaceWith(f); track("Karte geladen");
  });

  /* ---------------------------------------------------------------- Formulare */
  var LABELS = {
    typ: null, website: null, einwilligung: null, quelle: null, sprache: null, name: t("Name"), telefon: t("Telefon"), email: t("E-Mail"), paket: t("Paket"),
    klasse: t("Fahrzeugklasse"), fahrzeug: t("Fahrzeug"), zustand: t("Zustand"), extras: t("Extras"), abholung: t("Abholung"), datum: t("Wunschtermin"),
    datum2: t("Ausweichtermin"), zeitfenster: t("Zeitfenster"), uhrzeit: t("Uhrzeit"), gutscheincode: t("Gutscheincode"), kanal: t("Antwort per"), nachricht: t("Nachricht"),
    bewertung_ok: null, art: t("Gutschein"), betrag: t("Betrag"), wunschbetrag: t("Wunschbetrag"), fuer: t("Für"), von: t("Von"), widmung: t("Widmung"),
    zustellung: t("Zustellung"), firma: t("Firma"), anzahl: t("Fahrzeuge"), intervall: t("Intervall"), leistungen: t("Leistungen"), scheibenumfang: t("Scheiben"),
    vorgang: t("Vorgang / Gutscheincode"), winterschutz: t("Schutz im Winterangebot")
  };
  var TITLES = { kontakt: t("Anfrage"), termin: t("Terminanfrage"), gutschein: t("Gutscheinbestellung"), firma: t("Firmenanfrage"), widerruf: t("Widerruf") };

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
    if (EN) data.sprache = "en";  // René sieht, dass auf Englisch geantwortet werden sollte
    return data;
  }
  function pretty(k, v) {
    if (k === "paket") { var p = pkg(v); return p ? p.name : (SPECIAL[v] || v); }
    if (k === "klasse") { var c = cls(v); return c ? c.name : v; }
    if (k === "datum" || k === "datum2") return deDate(v);
    if (k === "betrag" || k === "wunschbetrag") return eur(v);
    if (k === "winterschutz") return v === "keramik" ? t("C² CarCeramic statt Wachs (Aufpreis nach Absprache)") : t("Wachsversiegelung (inklusive)");
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
    return waLink(t("Hallo ElbDetail, hier meine {titel}:", { titel: TITLES[typ] || t("Anfrage") }) + "\n" + asText(data));
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
    var mail = "mailto:" + ELB.email + "?subject=" + encodeURIComponent(t("{titel} über die Website", { titel: TITLES[data.typ] || t("Anfrage") }) + " – " + (data.name || "")) +
      "&body=" + encodeURIComponent(asText(data));
    return '<span>' + reason + '</span><span class="fb-actions"><a class="btn btn-wa btn-sm" target="_blank" rel="noopener" href="' + waFromForm(form) +
      '">' + t("Per WhatsApp senden") + '</a><a class="btn btn-line-light btn-sm" href="' + mail + '">' + t("Per E-Mail senden") + '</a></span><span class="hint">' + t("Oder rufen Sie an:") + ' <a href="tel:' + ELB.phone + '">' + ELB.phoneDisplay + '</a></span>';
  }
  function fieldError(form, name, text) {
    var el = form.querySelector('[name="' + name + '"]'); if (!el) return;
    el.setAttribute("aria-invalid", "true");
    var row = el.closest(".form-row, .consent-row") || el.parentNode, m = $("[data-err]", row);
    if (!m) { m = document.createElement("span"); m.className = "field-msg error"; m.setAttribute("data-err", ""); row.appendChild(m); }
    m.textContent = text;
  }
  function clearErrors(form) { $$("[data-err]", form).forEach(function (m) { m.remove(); }); }
  function validate(form, scope) {
    var ok = true, first = null;
    $$("input, select, textarea", scope || form).forEach(function (el) {
      if (!el.willValidate) return;
      var valid = el.checkValidity();
      if (el.type === "radio") valid = !el.required || !!form.querySelector('input[name="' + el.name + '"]:checked');
      el.setAttribute("aria-invalid", valid ? "false" : "true");
      if (!valid) { ok = false; first = first || el; }
    });
    if (first) first.focus();
    return ok;
  }

  /* ---------------------------------------------------------------- Fotos vom Fahrzeug (Markentrix-Portal: /api/foto) */
  var fotoCfgP = null;
  function fotoCfg() {
    if (!fotoCfgP) fotoCfgP = IS_LIVE ? fetch(API + "/foto").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }) : Promise.resolve(null);
    return fotoCfgP;
  }
  /* Im Browser auf höchstens 1600 Pixel verkleinern und als JPEG neu zeichnen: spart Datenvolumen, Standortdaten fallen weg */
  function shrink(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file), img = new Image();
      img.onload = function () {
        var f = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight)), c = document.createElement("canvas");
        c.width = Math.max(1, Math.round(img.naturalWidth * f)); c.height = Math.max(1, Math.round(img.naturalHeight * f));
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        c.toBlob(function (b) { if (b) resolve(b); else reject(new Error("")); }, "image/jpeg", 0.85);
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error(t("Dieses Bildformat lässt sich hier nicht verarbeiten. Bitte ein JPG oder PNG wählen."))); };
      img.src = url;
    });
  }
  $$("[data-foto]").forEach(function (row) {
    var form = row.closest("form"), input = $("[data-foto-input]", row), list = $("[data-foto-list]", row), hint = $("[data-foto-hint]", row);
    var items = [];
    form.__fotos = items;
    var sync = function () {
      var busy = items.some(function (x) { return x.busy; });
      $$('[type="submit"]', form).forEach(function (b) { b.disabled = busy; });
      input.disabled = items.length >= row.__max;
    };
    fotoCfg().then(function (cfg) {
      if (!cfg || !cfg.aktiv) return;
      row.__max = Math.max(1, parseInt(cfg.max, 10) || 5);
      /* Hinweis zur Löschfrist kommt vom Portal auf Deutsch; die englische Seite formuliert ihn aus der Anzahl der Tage selbst */
      var fh = EN ? (cfg.tage ? t("Die Fotos werden nach {n} Tagen automatisch gelöscht.", { n: parseInt(cfg.tage, 10) }) : "") : (cfg.hinweis || "");
      hint.textContent = (fh ? fh + " " : "") + (row.__max === 1 ? t("Höchstens {n} Foto.", { n: 1 }) : t("Höchstens {n} Fotos.", { n: row.__max }));
      row.hidden = false;
      input.addEventListener("change", function () {
        var files = [].slice.call(input.files || []); input.value = "";
        files.forEach(function (file) {
          if (items.length >= row.__max) return;
          var it = { token: "", busy: true }, li = document.createElement("li");
          li.className = "foto-item is-busy";
          li.innerHTML = '<img alt="" width="64" height="64"><span class="foto-state">' + t("Wird hochgeladen …") + '</span><button type="button" class="link-btn">' + t("Entfernen") + '</button>';
          $("img", li).alt = t("Vorschau {name}", { name: file.name });
          items.push(it); list.appendChild(li); sync();
          $("button", li).addEventListener("click", function () { items.splice(items.indexOf(it), 1); li.remove(); sync(); });
          shrink(file).then(function (blob) {
            $("img", li).src = URL.createObjectURL(blob);
            return fetch(API + "/foto", { method: "POST", headers: { "Content-Type": "text/plain" }, body: blob });
          }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || !j.token) throw new Error(j.message || ""); return j; });
          }).then(function (j) {
            it.token = j.token; it.busy = false; li.classList.remove("is-busy"); $(".foto-state", li).textContent = t("Hochgeladen");
            track("Foto hochgeladen");
          }).catch(function (e) {
            it.busy = false; li.classList.remove("is-busy"); li.classList.add("is-error");
            $(".foto-state", li).textContent = (e && e.message && !EN ? e.message : "") || t("Dieses Foto konnte nicht hochgeladen werden.");
          }).then(sync);
        });
      });
    });
  });

  $$("form.js-form").forEach(function (form) {
    var typ = form.getAttribute("data-form");
    $$("[data-wa-from-form]", form).forEach(function (b) {
      b.addEventListener("click", function () { track("WhatsApp-Klick", { ort: "formular-" + typ }); openWa(waFromForm(form)); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.website && form.website.value) return;
      if (!validate(form)) { setStatus(form, t("Bitte die markierten Pflichtfelder ausfüllen."), "error"); return; }
      var btn = form.querySelector('[type="submit"]:not([hidden])');
      if (!IS_LIVE) {
        setStatus(form, "", "info", fallbackHtml(form, t("Das Formular kann hier nicht übertragen werden. Senden Sie die Angaben direkt:")));
        return;
      }
      var fotos = form.__fotos || [];
      if (fotos.some(function (x) { return x.busy; })) { setStatus(form, t("Einen Moment bitte, die Fotos werden noch hochgeladen."), "info"); return; }
      if (btn && btn.disabled) return;  // Doppelklick: nur einmal senden
      clearErrors(form);
      if (btn) { btn.disabled = true; btn.classList.add("is-loading"); }
      setStatus(form, t("Wird gesendet …"), "");
      fetch(API + "/anfrage", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify((function () {
        var d = collect(form), tk = fotos.filter(function (x) { return x.token; }).map(function (x) { return x.token; });
        if (tk.length) d.fotos = tk;
        return d;
      })()) })
        .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (j) { j.status = r.status; return j; }); })
        .then(function (j) {
          if (j.ok) {
            track("Anfrage gesendet", { typ: typ });
            var anz = form.getAttribute("data-anzahlung");
            location.href = "danke.html?typ=" + encodeURIComponent(typ) + (j.ref ? "&ref=" + encodeURIComponent(j.ref) : "") + (anz ? "&anz=" + encodeURIComponent(anz) : "");
          } else if (j.status === 429) {
            setStatus(form, "", "error", fallbackHtml(form, t("Gerade kommen sehr viele Anfragen an. Bitte versuchen Sie es später noch einmal oder melden Sie sich direkt:")));
          } else if (j.errors) {
            /* Fehlertexte des Portals sind deutsch; die englische Seite zeigt eigene */
            Object.keys(j.errors).forEach(function (k) {
              fieldError(form, k, !EN ? j.errors[k] : k === "uhrzeit" ? t("Diese Uhrzeit wurde gerade vergeben. Bitte eine andere wählen.") : t("Bitte diese Angabe prüfen."));
            });
            setStatus(form, (!EN && j.message) || t("Bitte die markierten Angaben prüfen."), "error");
            form.dispatchEvent(new CustomEvent("elb:errors", { detail: j.errors }));
          } else throw new Error("server");
        })
        .catch(function () { setStatus(form, "", "error", fallbackHtml(form, t("Die Anfrage konnte gerade nicht übertragen werden. Bitte senden Sie sie direkt:"))); })
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
    var blocked = [], closedWeekdays = [0], payMe = "";

    if (Q.paket) { var rp = wz.querySelector('input[name="paket"][value="' + Q.paket + '"]'); if (rp) rp.checked = true; }
    if (Q.schutz === "keramik") { var rw = wz.querySelector('input[name="winterschutz"][value="keramik"]'); if (rw) rw.checked = true; }
    if (Q.klasse) { var rk = wz.querySelector('input[name="klasse"][value="' + Q.klasse + '"]'); if (rk) rk.checked = true; }
    if (Q.quelle) wz.quelle.value = Q.quelle;
    if (Q.gutschein) wz.gutscheincode.value = Q.gutschein;
    ["datum", "datum2"].forEach(function (n) { if (wz[n]) wz[n].min = todayIso(); });

    if (Q.datum && /^\d{4}-\d{2}-\d{2}$/.test(Q.datum) && Q.datum >= todayIso() && wz.datum) wz.datum.value = Q.datum;
    availability().then(function (j) {
      if (!j) return;
      blocked = j.blocked || []; if (j.closedWeekdays) closedWeekdays = j.closedWeekdays;
      /* Direkte Buchung nur, wenn das Portal sie freigibt; sonst bleibt es beim Terminwunsch */
      if (j.selfBooking) $$("[data-sb-text]").forEach(function (el) { el.textContent = el.getAttribute("data-sb-text"); });
      payMe = payMeName(j);
      $$("[data-pay]").forEach(function (el) { el.hidden = (el.getAttribute("data-pay") === "on") !== !!payMe; });
      if (wz.datum.value) checkDate(wz.datum);
      summary();
    });

    /* Winterangebot: Wachs inklusive oder C² CarCeramic statt Wachs (dann Keramik-Standzeit und Aufpreis nach Absprache) */
    var winterBox = $(".wz-winter", wz);
    function paketVal() { return (wz.querySelector('input[name="paket"]:checked') || {}).value || ""; }
    function winterKer() { var r = wz.querySelector('input[name="winterschutz"]:checked'); return paketVal() === "winter" && !!r && r.value === "keramik"; }
    var scheibenBox = $(".wz-scheiben", wz);
    function syncWinter() {
      [[winterBox, "winter"], [scheibenBox, "scheiben"]].forEach(function (x) {
        if (x[0]) { x[0].hidden = paketVal() !== x[1]; $$("input", x[0]).forEach(function (r) { r.disabled = x[0].hidden; }); }
      });
    }
    /* Freie Abgabezeiten des gewählten Tages aus dem Portal (/api/slots). Nur freie Zeiten sind wählbar. */
    var slotBox = $("#t-slots"), slotMsg = $("#t-slots-msg"), slotReq = 0;
    function loadSlots(keep) {
      if (!slotBox) return;
      var day = wz.datum.value, chosen = keep || radio(wz, "uhrzeit");
      var say = function (msg, err, html) { if (slotMsg) { if (html) slotMsg.innerHTML = msg; else slotMsg.textContent = msg; slotMsg.className = "field-msg" + (err ? " error" : ""); } };
      var alt = t("Rufen Sie uns an ({tel}) oder schreiben Sie per {wa}.", { tel: '<a href="tel:' + ELB.phone + '">' + ELB.phoneDisplay + '</a>',
        wa: '<a href="' + waLink(t("Hallo ElbDetail, ich möchte einen Termin am {datum} vereinbaren.", { datum: deDate(day) })) + '" target="_blank" rel="noopener">WhatsApp</a>' });
      if (!day || wz.datum.validationMessage) { slotBox.innerHTML = ""; say(day ? "" : t("Bitte zuerst einen Tag wählen.")); return; }
      if (!IS_LIVE) { slotBox.innerHTML = ""; say(t("Freie Uhrzeiten können hier nicht geladen werden.") + " " + alt, true, true); return; }
      var my = ++slotReq;
      say(t("Freie Uhrzeiten werden geladen …"));
      fetch(API + "/slots?tag=" + encodeURIComponent(day)).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
        if (my !== slotReq) return;
        if (!j || !j.slots) { slotBox.innerHTML = ""; say(t("Die freien Uhrzeiten konnten gerade nicht geladen werden.") + " " + alt, true, true); return; }
        var free = j.slots.filter(function (x) { return x.frei; });
        slotBox.innerHTML = j.slots.map(function (x) {
          var z = String(x.zeit).replace(/[^0-9:]/g, "");
          return '<label class="choice-pill"' + (x.frei ? "" : ' title="' + t("Bereits vergeben") + '"') + '><input type="radio" name="uhrzeit" value="' + z + '" required' +
            (x.frei ? "" : " disabled") + (x.frei && z === chosen ? " checked" : "") + '><span><strong>' + t("{zeit} Uhr", { zeit: z }) + '</strong></span></label>';
        }).join("");
        say(free.length ? (free.length === 1 ? t("{n} Uhrzeit frei an diesem Tag.", { n: 1 }) : t("{n} Uhrzeiten frei an diesem Tag.", { n: free.length }))
          : t("An diesem Tag ist leider keine Uhrzeit mehr frei. Bitte einen anderen Tag wählen."), !free.length);
        summary();
      }).catch(function () { if (my === slotReq) { slotBox.innerHTML = ""; say(t("Die freien Uhrzeiten konnten gerade nicht geladen werden.") + " " + alt, true, true); } });
    }
    /* Zwei Buchungen zur selben Zeit: das Portal lässt nur eine gewinnen, die andere bekommt einen Hinweis an der Uhrzeit */
    wz.addEventListener("elb:errors", function (e) {
      var errs = e.detail || {}, k = Object.keys(errs)[0];
      if (errs.uhrzeit) loadSlots("-");
      var el = k && wz.querySelector('[name="' + k + '"]'), st = el && el.closest(".wz-step");
      if (st) show(steps.indexOf(st));
    });
    /* Termin innerhalb von 14 Tagen: vorzeitigen Beginn ausdrücklich verlangen (Widerrufsrecht) */
    var vzRow = $("[data-vorzeitig]", wz);
    function syncVorzeitig() {
      if (!vzRow) return;
      var v = wz.datum.value, lim = new Date(); lim.setDate(lim.getDate() + 14);
      var need = !!v && new Date(v + "T12:00:00") < lim;
      vzRow.hidden = !need; var cb = $("input", vzRow); cb.disabled = !need; cb.required = need;
    }
    function checkDate(el) {
      var msg = $("#" + el.id + "-msg"), v = el.value, txt = "";
      if (v) {
        var d = new Date(v + "T12:00:00");
        if (v < todayIso()) txt = t("Bitte ein Datum ab heute wählen.");
        else if (closedWeekdays.indexOf(d.getDay()) !== -1) txt = t("An Sonntagen sind wir geschlossen. Bitte einen anderen Tag wählen.");
        else if (blocked.indexOf(v) !== -1) txt = t("An diesem Tag sind wir leider ausgebucht oder geschlossen.");
      }
      el.setCustomValidity(txt);
      if (msg) { msg.textContent = txt; msg.className = "field-msg" + (txt ? " error" : ""); }
    }
    ["datum", "datum2"].forEach(function (n) { if (wz[n]) wz[n].addEventListener("change", function () { checkDate(wz[n]); if (n === "datum") { loadSlots(); syncVorzeitig(); } summary(); }); });
    $$('input[name="paket"], input[name="winterschutz"], input[name="scheibenumfang"]', wz).forEach(function (r) { r.addEventListener("change", syncWinter); });

    function show(i) {
      cur = Math.max(0, Math.min(steps.length - 1, i));
      steps.forEach(function (s, k) { s.hidden = k !== cur; });
      inds.forEach(function (li, k) { li.className = k < cur ? "done" : (k === cur ? "current" : ""); if (k === cur) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current"); });
      prev.hidden = cur === 0; next.hidden = cur === steps.length - 1; submit.hidden = cur !== steps.length - 1;
      track("Buchung Schritt", { schritt: cur + 1 });
    }
    function go(d) {
      if (d > 0 && !validate(wz, steps[cur])) { setStatus(wz, t("Bitte die markierten Angaben ergänzen."), "error"); return; }
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
      var d = collect(wz), p = pkg(d.paket), c = cls(d.klasse), wk = winterKer(), sch = !!(p && p.scope);
      var v = sch ? price(d.paket, null, d.scheibenumfang) : (p && c ? price(d.paket, d.klasse) : null);
      var sc = (ELB.booking || {}).surcharge || {}, zs = [].concat(d.zustand || []).filter(function (z) { return (sc.exempt || []).indexOf(z) === -1; });
      var surPct = zs.reduce(function (a, z) { return a + ((sc.overrides || {})[z] != null ? sc.overrides[z] : (sc.percent || 0)); }, 0);
      if (sch) surPct = 0;  // Zustand des Innenraums spielt für die Scheiben keine Rolle
      if (v != null && surPct) v = Math.round(v * (1 + surPct / 100));
      var surEl = $("#t-surcharge"); if (surEl) surEl.textContent = surPct ? t("Richtpreis inkl. {p} % Zuschlag für den Zustand.", { p: surPct }) : "";
      var set = function (k, x) { var el = wz.parentNode.querySelector('[data-sum="' + k + '"]'); if (el) el.textContent = x; };
      var shown = function (name) {  // angezeigter Text der Auswahl (die Werte bleiben deutsch, damit René sie versteht)
        return $$('input[name="' + name + '"]:checked', wz).map(function (el) { var s = $("strong", el.parentNode) || el.nextElementSibling; return s ? s.textContent.trim() : el.value; });
      };
      set("paket", (p ? p.name : (SPECIAL[d.paket] || "–")) + (wk ? " · " + t("C² CarCeramic statt Wachs") : "") + (sch && d.scheibenumfang ? " · " + shown("scheibenumfang").join("") : ""));
      set("klasse", (c ? c.name : "–") + (d.fahrzeug ? " · " + d.fahrzeug : ""));
      set("extras", d.extras && d.extras.length ? shown("extras").join(", ") : t("keine"));
      set("datum", d.datum ? deDate(d.datum) + (d.uhrzeit ? ", " + t("{zeit} Uhr", { zeit: d.uhrzeit }) : "") + (d.datum2 ? " (" + t("alt.") + " " + deDate(d.datum2) + ")" : "") : "–");
      set("preis", v != null ? (sch ? "" : t("ab") + " ") + eur(v) + (wk ? " + " + t("Aufpreis C² CarCeramic") : "") : (SPECIAL[d.paket] ? t("nach Begutachtung") : "–"));
      var bk = ELB.booking || {}, base = wk ? null : (v != null ? v : (d.paket === "keramik" ? bk.keramikMin : null));
      var anz = base && payMe ? (Math.round(base * (bk.depositPercent || 15)) / 100).toFixed(2) : "";
      if (anz) wz.setAttribute("data-anzahlung", anz); else wz.removeAttribute("data-anzahlung");
      set("anzahlung", anz ? t("{betrag} per PayPal nach dem Absenden", { betrag: eurCt(anz) }) : (d.paket ? t("nach Absprache") : "–"));
      $$("[data-price-for]", wz).forEach(function (el) { var x = price(el.getAttribute("data-price-for"), d.klasse || ELB.classes[0].key); el.textContent = x != null ? t("ab") + " " + eur(x) : t("auf Anfrage"); });
    }
    wz.addEventListener("change", summary); wz.addEventListener("input", summary);
    if (wz.datum.value) checkDate(wz.datum);
    loadSlots(); syncVorzeitig(); syncWinter(); summary(); show(0);
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
        setVc("value", p ? p.name : t("Paket")); setVc("desc", t("Fahrzeugaufbereitung für einen Kleinwagen") + (p ? " · " + t("Wert {preis}", { preis: eur(p.prices[ELB.classes[0].key]) }) : ""));
      } else {
        var c = vf.wunschbetrag.value ? parseInt(vf.wunschbetrag.value, 10) : parseInt(radio(vf, "betrag") || "0", 10);
        setVc("value", eur(c || 0)); setVc("desc", t("für eine Fahrzeugaufbereitung nach Wahl"));
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
    var bk = ELB.booking || {}, owner = bk.owner || t("Wir");
    var T = {
      termin: [t("Terminanfrage eingegangen."), t("{owner} meldet sich telefonisch, sieht sich Ihr Fahrzeug vorab an und bestätigt den Termin. Eine Eingangsbestätigung ist unterwegs an Ihre E-Mail-Adresse.", { owner: owner })],
      kontakt: [t("Anfrage eingegangen."), t("Wir melden uns so schnell wie möglich, in der Regel am selben oder nächsten Werktag.")],
      gutschein: [t("Gutscheinbestellung eingegangen."), t("Sie erhalten eine Eingangsbestätigung per E-Mail. Die Zahlungsdaten schicken wir Ihnen in Kürze, nach Zahlungseingang erhalten Sie den Gutschein.")],
      firma: [t("Anfrage eingegangen."), t("Vielen Dank für Ihr Interesse. Wir melden uns mit einem Vorschlag für Umfang, Intervalle und Konditionen.")],
      widerruf: [t("Ihr Widerruf ist eingegangen."), t("Sie erhalten eine Eingangsbestätigung per E-Mail. Bereits geleistete Zahlungen erstatten wir unverzüglich, spätestens binnen 14 Tagen.")]
    }[Q.typ];
    if (T) { thanks.innerHTML = t("Danke!") + " <em>" + T[0] + "</em>"; var tt = $("[data-thanks-text]"); if (tt) tt.textContent = T[1] + (Q.ref ? " " + t("Ihre Vorgangsnummer: {ref}.", { ref: Q.ref }) : ""); }
    /* Anzahlung per PayPal.me: Betrag steht im Link, die Vorgangsnummer als Verwendungszweck */
    var pay = $("[data-thanks-pay]"), amt = parseFloat(Q.anz || "");
    if (pay && Q.typ === "termin" && amt > 0 && amt < 10000) availability().then(function (j) {
      var me = payMeName(j); if (!me) return;
      var amtTxt = eurCt(amt), ref = (Q.ref || t("Ihren Namen")).replace(/[^A-Za-z0-9 -]/g, "");
      pay.innerHTML = '<h2>' + t("Anzahlung leisten") + '</h2><p>' + t("Mit der Anzahlung von {betrag} sichern Sie sich Ihren Termin. Sie wird mit dem Endpreis verrechnet.", { betrag: "<strong>" + amtTxt + "</strong>" }) + " " +
        t("Bitte geben Sie bei PayPal als Verwendungszweck {ref} an und zahlen Sie als „Waren oder Dienstleistungen“.", { ref: "<strong>" + ref + "</strong>" }) + '</p>' +
        '<a class="btn btn-primary btn-lg" href="https://paypal.me/' + encodeURIComponent(me) + '/' + amt.toFixed(2) + 'EUR" target="_blank" rel="noopener">' + t("Anzahlung {betrag} mit PayPal senden", { betrag: amtTxt }) + '</a>' +
        '<p class="hint">' + t("Kommt der Termin nicht zustande oder widerrufen Sie innerhalb der Frist, erstatten wir die Anzahlung vollständig.") + '</p>';
      pay.hidden = false;
    });
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
