/* Burnout Celler-Kartbahn – Rückmeldungen und lebendige Elemente
   (Öffnungsstatus, FAQ, Preis-Check). Ein orchestrierter Moment (Hero) läuft rein in CSS.
   Keine Dauerbewegung, keine Zähler, kein Scroll-Reveal. */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Öffnungsstatus live (aus den echten Öffnungszeiten) ----------
     Mo–Fr ab 15:00 (Ferien ab 13:00 – nicht berechenbar, daher „ab 15 Uhr“), Sa ab 13:00, So ab 11:00, Open End.
     Ohne JavaScript steht der statische Text im HTML. */
  var status = document.querySelector("[data-open-status]");
  if (status) {
    var now = new Date(), d = now.getDay(), h = now.getHours() + now.getMinutes() / 60;
    var opens = d === 0 ? 11 : d === 6 ? 13 : 15;
    var txt = status.querySelector("[data-text]");
    if (h >= opens && h < 23) { status.classList.add("is-open"); txt.textContent = "Jetzt geöffnet, Open End"; }
    else if (h < opens) { status.classList.add("is-closed"); txt.textContent = "Heute ab " + opens + " Uhr geöffnet"; }
    else { var n = (d + 1) % 7, no = n === 0 ? 11 : n === 6 ? 13 : 15; status.classList.add("is-closed"); txt.textContent = "Morgen ab " + no + " Uhr geöffnet"; }
  }

  /* ---------- FAQ: weiches Öffnen (gelegentliche Aktion, 250 ms) ---------- */
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

  /* ---------- Preis-Check (echte Preise, Stand Oktober 2026) ---------- */
  var calc = document.getElementById("preis-check-form");
  if (calc) {
    var P = { sa_so: { erw: [15, 30, 43, 52, 60, 9], kids: [13.5, 27, 36, 43, 50, 7] }, fr: { erw: [14, 25, 34, 42, 49, 7], kids: [12, 21, 29, 36, 41, 6] }, mo_do: { erw: { 3: 30, 5: 43 }, kids: { 3: 27, 5: 36 } } };
    var euro = function (n) { return n.toLocaleString("de-DE", { style: "currency", currency: "EUR" }); };
    var total = calc.querySelector(".calc__total"), lines = calc.querySelector(".calc__lines"), note = calc.querySelector(".calc__note"), link = calc.querySelector(".calc__cta");
    function val(n) { var el = calc.querySelector('[name="' + n + '"]:checked') || calc.querySelector('[name="' + n + '"]'); return el ? el.value : ""; }
    function num(n) { return Math.max(0, parseInt(val(n), 10) || 0); }
    function perPerson(tab, kind, f) { var a = P[tab][kind]; if (f <= 5) return a[f - 1]; return a[4] + (f - 5) * a[5]; }
    function personen(n) { return n === 1 ? "1 Person" : n + " Personen"; }
    function update() {
      var tag = val("tag"), e = num("erw"), k = num("kids"), f = Math.min(Math.max(num("fahrten"), 1), 8); var out = [], sum = 0, txt = "";
      if (e + k === 0) { total.textContent = "0,00 €"; lines.innerHTML = ""; note.textContent = "Bitte mindestens eine Person eintragen."; link.textContent = "Fahrten reservieren"; link.href = "buchen.html?angebot=tickets"; return; }
      if (tag === "mo_do") {
        if (f === 3 || f === 5) { if (e) out.push([e + " Erw. × " + f + " Fahrten (" + (f === 3 ? "3 für 2" : "5 für 3") + ")", e * P.mo_do.erw[f]]); if (k) out.push([k + " Kids × " + f + " Fahrten", k * P.mo_do.kids[f]]); txt = "Spartag Mo–Do: ihr nutzt das Angebot " + (f === 3 ? "3 Fahrten zum Preis von 2." : "5 Fahrten zum Preis von 3."); }
        else { if (e) out.push([e + " Erw. × " + f + " Fahrten (Normalpreis)", e * perPerson("sa_so", "erw", f)]); if (k) out.push([k + " Kids × " + f + " Fahrten (Normalpreis)", k * perPerson("sa_so", "kids", f)]); txt = "Tipp: Mo–Do lohnen sich 3 oder 5 Fahrten pro Person am meisten (3 für 2 oder 5 für 3)."; }
      } else {
        if (e) out.push([e + " Erw. × " + f + " × 10 Min", e * perPerson(tag, "erw", f)]); if (k) out.push([k + " Kids × " + f + " × 10 Min", k * perPerson(tag, "kids", f)]);
        txt = tag === "fr" ? "Freitagsspecial: je öfter, desto günstiger." : "Normalpreis am Wochenende, pro Person.";
      }
      sum = out.reduce(function (s, l) { return s + l[1]; }, 0);
      lines.textContent = ""; out.forEach(function (l) { var li = document.createElement("li"), a = document.createElement("span"), b = document.createElement("span"); a.textContent = l[0]; b.textContent = euro(l[1]); li.appendChild(a); li.appendChild(b); lines.appendChild(li); });
      total.textContent = euro(sum); if (!reduce) { total.classList.remove("bump"); void total.offsetWidth; total.classList.add("bump"); }
      note.textContent = txt + " Neukunden zahlen einmalig 2 € Registrierung und 3 € Sturmhaube dazu. Bezahlt wird vor Ort.";
      var n = e + k;
      if (n >= 5) { link.href = "buchen.html?angebot=tickets&teilnehmer=" + n + "&kinder=" + k + "&fahrten=" + Math.min(f, 5); link.textContent = personen(n) + " reservieren"; }
      else { link.href = "tel:+495141908650"; link.textContent = "Unter 5 Personen: anrufen und reservieren"; }
    }
    calc.addEventListener("input", update); calc.addEventListener("change", update);
    calc.querySelectorAll(".stepper-count button").forEach(function (b) {
      b.addEventListener("click", function () { var inp = b.parentNode.querySelector("input"); var v = (parseInt(inp.value, 10) || 0) + (b.dataset.dir === "+" ? 1 : -1); inp.value = Math.min(Math.max(v, parseInt(inp.min, 10) || 0), parseInt(inp.max, 10) || 99); update(); });
    });
    link.addEventListener("click", function () { if (window.mkEvent) window.mkEvent("preischeck_zur_buchung"); });
    update();
  }
})();
