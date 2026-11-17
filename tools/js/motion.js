/* Burnout Celler-Kartbahn – Motion & Interaktion (ohne Fremdbibliotheken)
   Reveal beim Scrollen, Zähler, Header-Zustand, Lesefortschritt, Laufband,
   Karten-Licht, FAQ-Animation, Preis-Check. Respektiert prefers-reduced-motion. */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Reveal beim Scrollen ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    /* Stagger: Position unter den Geschwistern als --i */
    revealEls.forEach(function (el) {
      var i = 0, s = el.previousElementSibling;
      while (s && i < 8) { if (s.classList.contains("reveal")) i++; s = s.previousElementSibling; }
      el.style.setProperty("--i", i);
    });
    /* Was beim Laden schon im Bild ist, erscheint sofort – nur Nachfolgendes animiert */
    var vh = window.innerHeight || doc.clientHeight;
    revealEls.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.95 && r.bottom > 0) { el.classList.add("no-anim", "in"); }
    });
    if ("IntersectionObserver" in window && !reduce) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      revealEls.forEach(function (el) { if (!el.classList.contains("in")) io.observe(el); });
      /* Sicherheitsnetz: nach 2,5 s alles zeigen (z. B. bei Druckansicht) */
      setTimeout(function () { revealEls.forEach(function (el) { el.classList.add("in"); }); }, 2500);
    } else {
      revealEls.forEach(function (el) { el.classList.add("in"); });
    }
  }

  /* ---------- Zahlen hochzählen ---------- */
  var nums = document.querySelectorAll(".stat strong, [data-count]");
  if (nums.length && !reduce && "IntersectionObserver" in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return; cio.unobserve(e.target);
        var el = e.target, txt = el.textContent.trim();
        var m = txt.match(/^([^\d]*)(\d+(?:[.,]\d+)?)(.*)$/); if (!m) return;
        var dec = (m[2].split(/[.,]/)[1] || "").length, sep = m[2].indexOf(",") > -1 ? "," : ".";
        var target = parseFloat(m[2].replace(",", ".")), t0 = null, dur = 1100;
        function step(ts) {
          if (!t0) t0 = ts; var p = Math.min((ts - t0) / dur, 1); p = 1 - Math.pow(1 - p, 3);
          var v = (target * p).toFixed(dec).replace(".", sep);
          el.textContent = m[1] + v + m[3];
          if (p < 1) requestAnimationFrame(step); else el.textContent = txt;
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- Header-Zustand & Lesefortschritt ---------- */
  var header = document.querySelector(".header");
  var bar = document.querySelector(".progress");
  var ticking = false;
  function onScroll() {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY || doc.scrollTop;
      if (header) header.classList.toggle("is-scrolled", y > 24);
      if (bar) { var h = doc.scrollHeight - doc.clientHeight; bar.style.transform = "scaleX(" + (h > 0 ? Math.min(y / h, 1) : 0) + ")"; }
      ticking = false;
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* ---------- Laufband: Inhalt verdoppeln für nahtlose Schleife ---------- */
  document.querySelectorAll(".ticker__track").forEach(function (t) { t.innerHTML += t.innerHTML; t.setAttribute("aria-hidden", "true"); });

  /* ---------- Karten: Lichtpunkt folgt der Maus ---------- */
  if (window.matchMedia("(hover: hover)").matches) {
    document.querySelectorAll(".card--link").forEach(function (c) {
      c.addEventListener("pointermove", function (ev) {
        var r = c.getBoundingClientRect();
        c.style.setProperty("--mx", (ev.clientX - r.left) + "px"); c.style.setProperty("--my", (ev.clientY - r.top) + "px");
      });
    });
  }

  /* ---------- FAQ: weiches Auf- und Zuklappen ---------- */
  document.querySelectorAll(".faq details").forEach(function (d) {
    var sum = d.querySelector("summary"), body = d.querySelector(".faq__body");
    if (!sum || !body || reduce) return;
    sum.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (d.classList.contains("animating")) return;
      d.classList.add("animating");
      if (d.open) {
        body.style.height = body.offsetHeight + "px"; body.offsetHeight; body.style.height = "0px";
        body.addEventListener("transitionend", function h() { body.removeEventListener("transitionend", h); d.open = false; body.style.height = ""; d.classList.remove("animating"); });
      } else {
        d.open = true; var target = body.offsetHeight; body.style.height = "0px"; body.offsetHeight; body.style.height = target + "px";
        body.addEventListener("transitionend", function h() { body.removeEventListener("transitionend", h); body.style.height = ""; d.classList.remove("animating"); });
      }
    });
  });

  /* ---------- Preis-Check (Preise-Seite) ---------- */
  var calc = document.getElementById("preis-check");
  if (calc) {
    var P = { sa_so: { erw: [15, 30, 43, 52, 60, 9], kids: [13.5, 27, 36, 43, 50, 7] }, fr: { erw: [14, 25, 34, 42, 49, 7], kids: [12, 21, 29, 36, 41, 6] }, mo_do: { erw: { 3: 30, 5: 43 }, kids: { 3: 27, 5: 36 } } };
    var euro = function (n) { return n.toLocaleString("de-DE", { style: "currency", currency: "EUR" }); };
    var total = calc.querySelector(".calc__total"), lines = calc.querySelector(".calc__lines"), note = calc.querySelector(".calc__note"), link = calc.querySelector(".calc__cta");
    function val(n) { var el = calc.querySelector('[name="' + n + '"]:checked') || calc.querySelector('[name="' + n + '"]'); return el ? el.value : ""; }
    function num(n) { return Math.max(0, parseInt(val(n), 10) || 0); }
    function perPerson(tab, kind, f) { var a = P[tab][kind]; if (f <= 5) return a[f - 1]; return a[4] + (f - 5) * a[5]; }
    function update() {
      var tag = val("tag"), e = num("erw"), k = num("kids"), f = Math.min(Math.max(num("fahrten"), 1), 8); var out = [], sum = 0, txt = "";
      if (e + k === 0) { total.textContent = "0 €"; lines.innerHTML = ""; note.textContent = "Bitte Personen angeben."; return; }
      if (tag === "mo_do") {
        if (f === 3 || f === 5) { if (e) { out.push([e + " Erw. × " + f + " Fahrten (" + (f === 3 ? "3 für 2" : "5 für 3") + ")", e * P.mo_do.erw[f]]); } if (k) { out.push([k + " Kids × " + f + " Fahrten", k * P.mo_do.kids[f]]); } txt = "Spartag Mo–Do – ihr nutzt das Angebot " + (f === 3 ? "3 Fahrten zum Preis von 2." : "5 Fahrten zum Preis von 3."); }
        else { var base = tag; if (e) out.push([e + " Erw. × " + f + " Fahrten (Normalpreis)", e * perPerson("sa_so", "erw", f)]); if (k) out.push([k + " Kids × " + f + " Fahrten (Normalpreis)", k * perPerson("sa_so", "kids", f)]); txt = "Tipp: Mo–Do lohnen sich 3 oder 5 Fahrten pro Person am meisten (3 für 2 / 5 für 3)."; }
      } else {
        if (e) out.push([e + " Erw. × " + f + " × 10 Min", e * perPerson(tag, "erw", f)]); if (k) out.push([k + " Kids × " + f + " × 10 Min", k * perPerson(tag, "kids", f)]);
        txt = tag === "fr" ? "Freitagsspecial: je öfter, desto günstiger." : "Wochenend-Normalpreis pro Person.";
      }
      sum = out.reduce(function (s, l) { return s + l[1]; }, 0);
      lines.innerHTML = out.map(function (l) { return "<li><span>" + l[0] + "</span><span>" + euro(l[1]) + "</span></li>"; }).join("");
      total.textContent = euro(sum); total.classList.remove("bump"); void total.offsetWidth; total.classList.add("bump");
      note.textContent = txt + " Neukunden zahlen zusätzlich einmalig 2 € Registrierung und 3 € Sturmhaube. Bezahlung vor Ort.";
      var n = e + k; link.href = "buchen.html?angebot=tickets&teilnehmer=" + n + "&kinder=" + k + "&fahrten=" + Math.min(f, 5);
      link.textContent = n >= 5 ? "Diese Auswahl online reservieren" : "Unter 5 Personen: telefonisch reservieren";
      if (n < 5) link.href = "tel:+495141908650";
    }
    calc.addEventListener("input", update); calc.addEventListener("change", update);
    calc.querySelectorAll(".stepper-count button").forEach(function (b) {
      b.addEventListener("click", function () { var inp = b.parentNode.querySelector("input"); var v = (parseInt(inp.value, 10) || 0) + (b.dataset.dir === "+" ? 1 : -1); inp.value = Math.min(Math.max(v, parseInt(inp.min, 10) || 0), parseInt(inp.max, 10) || 99); update(); });
    });
    update();
  }
})();
