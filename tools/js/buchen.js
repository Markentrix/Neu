/* Online-Buchung: eigene Oberfläche über die Website-API des Markentrix-Portals (Variante B) */
(function () {
  "use strict";
  var form = document.getElementById("buchung");
  if (!form) return;

  var $ = function (s, c) { return (c || form).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || form).querySelectorAll(s)); };
  var status = $(".form-status");
  var btn = $('button[type="submit"]');
  var slotsBox = $("#slots");
  var slotHint = $("#slot-hint");
  var dateIn = $('[name="datum"]');
  var timeIn = $('[name="uhrzeit"]');
  var avail = null;           /* Antwort von /api/verfuegbarkeit */
  var apiDown = false;
  var selectedSlot = null;

  /* ---------- Angebote (Preise kennt nur die Website) ---------- */
  var ANGEBOTE = {
    tickets: { name: "Ticketfahrten (ab 5 Personen)", min: 5, max: 60, kids: true, fahrten: true },
    kidsparty: { name: "Kidsparty / Kindergeburtstag", min: 6, max: 30, paket: "kids" },
    supercup: { name: "Supercup / Rennen (6–17 Personen)", min: 6, max: 17, paket: "supercup" },
    bahnmiete: { name: "Bahnmiete / Firmenevent (ab 10 Karts)", min: 1, max: 120, paket: "bahnmiete" },
    schulklasse: { name: "Schulklasse (ab 20 Personen)", min: 20, max: 120, paket: "schule" },
    fuehrerschein: { name: "Kinderkartführerschein", min: 1, max: 12, paket: "fs" },
    event: { name: "Event / Flatratefahren", min: 1, max: 60, paket: "event" }
  };
  var PREISE = {
    sa_so: { erw: [15, 30, 43, 52, 60], kids: [13.5, 27, 36, 43, 50] },
    fr: { erw: [14, 25, 34, 42, 49], kids: [12, 21, 29, 36, 41] },
    mo_do: { erw: { 3: 30, 5: 43 }, kids: { 3: 27, 5: 36 } },
    kids: { F1: 40, F2: 48, pizza: 10.5, erw1620: 5, erw21: 7.5 },
    supercup: { standard: 39, professional: 49, premium: 59, double_premium: 59, double_ultra: 75, gp: 49, gp_premium: 59 },
    bahnmiete: { stunde: 650, halbe: 325, kartStunde: 65, kartHalbe: 32.5 },
    schule: { a1: 20, a2: 25 },
    fs: 45
  };
  function euro(n) { return n.toLocaleString("de-DE", { style: "currency", currency: "EUR" }); }

  /* ---------- Hilfen ---------- */
  function setError(name, msg) {
    var el = $('[name="' + name + '"]'); if (!el) return;
    var field = el.closest(".field"); if (!field) return;
    var err = field.querySelector(".error");
    if (msg) { field.classList.add("is-invalid"); if (err) err.textContent = msg; }
    else field.classList.remove("is-invalid");
  }
  function clearErrors() { $$(".field.is-invalid").forEach(function (f) { f.classList.remove("is-invalid"); }); }
  function showStatus(state, html) { status.setAttribute("data-state", state); status.innerHTML = html; }
  function fallback(show) { var fb = $(".fallback"); if (fb) fb.hidden = !show; }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function iso(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function weekday(s) { return new Date(s + "T12:00:00").getDay(); } /* 0 = So */
  function angebot() { var r = $('[name="angebot"]:checked'); return r ? r.value : ""; }

  /* ---------- Schritt 1: Angebot -> passende Felder ---------- */
  function updateAngebot() {
    var a = angebot(); var def = ANGEBOTE[a];
    $$("[data-for]").forEach(function (el) {
      var list = el.getAttribute("data-for").split(" ");
      var on = a && list.indexOf(a) > -1;
      el.hidden = !on;
      $$("input,select,textarea", el).forEach(function (i) { i.disabled = !on; });
    });
    var teil = $('[name="teilnehmer"]');
    if (def) { teil.min = def.min; teil.max = def.max; $("#teil-hint").textContent = "Mindestens " + def.min + (def.max < 100 ? ", maximal " + def.max : "") + " Personen."; }
    $("#step2").hidden = !a; $("#step3").hidden = !a; $("#step4").hidden = !a;
    if (a === "fuehrerschein") { $("#fs-note").hidden = false; } else { $("#fs-note").hidden = true; }
    updateSummary();
  }
  $$('[name="angebot"]').forEach(function (r) { r.addEventListener("change", updateAngebot); });

  /* ---------- Schritt 2: Datum & Uhrzeit aus dem Portal ---------- */
  var today = new Date(); dateIn.min = iso(today);
  var maxD = new Date(); maxD.setFullYear(maxD.getFullYear() + 1); dateIn.max = iso(maxD);

  function loadAvail() {
    return fetch("/api/verfuegbarkeit", { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (j) { avail = j; apiDown = false;
        if (j && j.selfBooking === false) { document.getElementById("form-title").textContent = "Terminwunsch senden"; document.getElementById("self-note").hidden = false; }
        if (j && j.nextFree) { document.getElementById("next-free").textContent = "Nächster freier Tag: " + new Date(j.nextFree + "T12:00:00").toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" }); }
      })
      .catch(function () { apiDown = true; avail = null;
        showStatus("info", "Die Online-Buchung ist gerade nicht erreichbar. Du kannst das Formular trotzdem ausfüllen und es später erneut senden – oder du reservierst direkt per Telefon, WhatsApp oder E-Mail.");
        fallback(true);
      });
  }

  function dateBlocked(s) {
    if (!avail) return "";
    if (avail.closedWeekdays && avail.closedWeekdays.indexOf(weekday(s)) > -1) return "An diesem Wochentag ist keine Buchung möglich.";
    if (avail.blocked && avail.blocked.indexOf(s) > -1) return "Dieser Tag ist bereits ausgebucht oder gesperrt. Bitte einen anderen Tag wählen.";
    return "";
  }

  function renderSlots(list) {
    slotsBox.innerHTML = ""; selectedSlot = null; timeIn.value = "";
    if (!list || !list.length) { slotHint.textContent = "Für diesen Tag sind keine Startzeiten hinterlegt. Bitte ruft uns an oder schreibt uns."; return; }
    var free = 0;
    list.forEach(function (s) {
      var b = document.createElement("button"); b.type = "button"; b.className = "slot"; b.textContent = s.zeit;
      b.setAttribute("aria-pressed", "false");
      if (!s.frei) { b.disabled = true; b.title = "bereits vergeben"; } else { free++; }
      b.addEventListener("click", function () {
        $$(".slot", slotsBox).forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true"); selectedSlot = s.zeit; timeIn.value = s.zeit; setError("uhrzeit", ""); updateSummary();
      });
      slotsBox.appendChild(b);
    });
    slotHint.textContent = free ? "Bitte eine Startzeit wählen. Alle Teilnehmer treffen 30 Minuten vorher bei uns ein." : "Dieser Tag ist leider ausgebucht. Bitte einen anderen Tag wählen.";
  }

  function loadSlots() {
    var d = dateIn.value; setError("datum", ""); setError("uhrzeit", "");
    slotsBox.innerHTML = ""; timeIn.value = ""; selectedSlot = null;
    if (!d) { slotHint.textContent = "Bitte zuerst ein Datum wählen."; updateSummary(); return; }
    var fs = angebot() === "fuehrerschein";
    if (fs) {
      var dt = new Date(d + "T12:00:00");
      if (!(dt.getDay() === 6 && dt.getDate() <= 7)) { setError("datum", "Der Kinderkartführerschein findet jeden 1. Samstag im Monat um 10:00 Uhr statt. Bitte diesen Tag wählen."); updateSummary(); return; }
    }
    var b = dateBlocked(d); if (b) { setError("datum", b); updateSummary(); return; }
    if (apiDown) { slotHint.textContent = "Startzeiten können gerade nicht geladen werden. Bitte Wunschuhrzeit in die Nachricht schreiben oder anrufen."; updateSummary(); return; }
    slotHint.textContent = "Startzeiten werden geladen …";
    fetch("/api/slots?tag=" + encodeURIComponent(d), { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (j) { var list = j.slots || []; if (fs) list = list.filter(function (s) { return s.zeit === "10:00"; }); renderSlots(list); updateSummary(); })
      .catch(function () { slotHint.textContent = "Startzeiten konnten nicht geladen werden. Bitte Seite neu laden oder telefonisch reservieren."; fallback(true); });
  }
  dateIn.addEventListener("change", loadSlots);

  /* ---------- Schritt 3: Details & Preis-Schätzung ---------- */
  function num(name) { var el = $('[name="' + name + '"]'); return el && !el.disabled ? (parseInt(el.value, 10) || 0) : 0; }
  function val(name) { var el = $('[name="' + name + '"]'); return el && !el.disabled ? el.value : ""; }

  function estimate() {
    var a = angebot(); var n = num("teilnehmer"); var d = dateIn.value; var out = { lines: [], total: null, note: "" };
    if (!a || !n) return out;
    if (a === "tickets") {
      var k = Math.min(num("kinder"), n); var e = n - k; var f = num("fahrten") || 1; var wd = d ? weekday(d) : -1;
      var tab = null, label = "";
      if (wd === 0 || wd === 6) { tab = PREISE.sa_so; label = "Wochenendpreis"; }
      else if (wd === 5) { tab = PREISE.fr; label = "Freitagspreis"; }
      else if (wd > 0) {
        label = "Spartag Mo–Do";
        if (f === 3 || f === 5) { var pe = PREISE.mo_do.erw[f], pk = PREISE.mo_do.kids[f];
          if (e) out.lines.push([e + " Erw. × " + f + " Fahrten (" + (f === 3 ? "3 für 2" : "5 für 3") + ")", e * pe]);
          if (k) out.lines.push([k + " Kinder × " + f + " Fahrten (" + (f === 3 ? "3 für 2" : "5 für 3") + ")", k * pk]);
          out.total = e * pe + k * pk; out.note = label + ". Tipp: Mo–Do gibt es 3 Fahrten zum Preis von 2 oder 5 zum Preis von 3.";
        } else { out.note = "Spartag Mo–Do: Mit 3 oder 5 Fahrten pro Person spart ihr am meisten (3 für 2 / 5 für 3). Preis für " + f + " Fahrt(en) nach Preisliste."; }
        return out;
      }
      if (tab) {
        var idx = Math.min(f, 5) - 1; var pe2 = tab.erw[idx], pk2 = tab.kids[idx];
        if (e) out.lines.push([e + " Erw. × " + f + " × 10 Min", e * pe2]);
        if (k) out.lines.push([k + " Kinder × " + f + " × 10 Min", k * pk2]);
        out.total = e * pe2 + k * pk2; out.note = label + " pro Person laut Preisliste.";
      } else { out.note = "Der Preis richtet sich nach dem Wochentag (siehe Preisliste)."; }
    } else if (a === "kidsparty") {
      var p = val("kidspaket") || "F1"; var pizza = Math.min(num("pizza"), 60); var e1 = num("erw1620"), e2 = num("erw21");
      out.lines.push([n + " Kinder × Paket " + p, n * PREISE.kids[p]]);
      if (pizza) out.lines.push([pizza + " × Pizzapaket", pizza * PREISE.kids.pizza]);
      if (e1) out.lines.push([e1 + " × Aufschlag 16–20 J.", e1 * PREISE.kids.erw1620]);
      if (e2) out.lines.push([e2 + " × Aufschlag ab 21 J.", e2 * PREISE.kids.erw21]);
      out.total = out.lines.reduce(function (s, l) { return s + l[1]; }, 0); out.note = "Bezahlung vor Ort in bar oder per EC-Karte.";
    } else if (a === "supercup") {
      var v = val("supercup") || "standard"; var billed = Math.max(n, 6);
      out.lines.push([billed + " × Supercup " + $('[name="supercup"] option:checked').textContent.split(" –")[0], billed * PREISE.supercup[v]]);
      out.total = billed * PREISE.supercup[v]; out.note = n < 6 ? "Es werden mindestens 6 Teilnehmer berechnet." : "Exklusiv: eure Gruppe ist allein auf der Strecke.";
    } else if (a === "bahnmiete") {
      var h = Math.max(parseFloat(val("stunden") || "1"), 1); var karts = Math.max(num("karts") || 10, 10);
      var halbe = Math.max(0, Math.round((h - 1) * 2));
      var base = PREISE.bahnmiete.stunde + halbe * PREISE.bahnmiete.halbe;
      var extra = Math.max(karts - 10, 0); var extraCost = extra * (PREISE.bahnmiete.kartStunde + halbe * PREISE.bahnmiete.kartHalbe);
      out.lines.push([h.toLocaleString("de-DE") + " Std. Bahnmiete inkl. 10 Karts", base]);
      if (extra) out.lines.push([extra + " weitere Karts", extraCost]);
      out.total = base + extraCost; out.note = "Bruttopreise. Max. 16 Karts gleichzeitig auf der Strecke.";
    } else if (a === "schulklasse") {
      var s = val("schulangebot") || "a1";
      out.lines.push([n + " × Angebot " + (s === "a1" ? "1 (20 Min)" : "2 (30 Min + Getränk)"), n * PREISE.schule[s]]);
      out.total = n * PREISE.schule[s]; out.note = "Gültig ab 20 Personen, Mo–Fr, auch vormittags.";
    } else if (a === "fuehrerschein") {
      out.lines.push([n + " × Kinderkartführerschein", n * PREISE.fs]); out.total = n * PREISE.fs; out.note = "Jeden 1. Samstag im Monat, 10:00 Uhr. Bitte um 09:30 Uhr eintreffen.";
    } else if (a === "event") {
      out.note = "Preis je nach Veranstaltung – wir bestätigen den Preis mit der Buchung.";
    }
    return out;
  }

  function updateSummary() {
    var a = angebot(); var box = $("#summary"); if (!a) { box.hidden = true; return; }
    box.hidden = false;
    var est = estimate(); var d = dateIn.value;
    $("#sum-angebot").textContent = ANGEBOTE[a].name;
    $("#sum-datum").textContent = d ? new Date(d + "T12:00:00").toLocaleDateString("de-DE", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" }) + (timeIn.value ? ", " + timeIn.value + " Uhr" : "") : "–";
    $("#sum-teil").textContent = num("teilnehmer") ? num("teilnehmer") + " Personen" : "–";
    var lines = $("#sum-lines"); lines.innerHTML = "";
    est.lines.forEach(function (l) { var li = document.createElement("li"); li.innerHTML = "<span>" + l[0] + "</span><span>" + euro(l[1]) + "</span>"; lines.appendChild(li); });
    $("#sum-total").textContent = est.total !== null ? euro(est.total) : "nach Preisliste";
    $("#sum-note").textContent = est.note;
    form.dataset.preis = est.total !== null ? euro(est.total) : "";
  }
  $$("input,select", $("#step3")).forEach(function (el) { el.addEventListener("input", updateSummary); el.addEventListener("change", updateSummary); });
  $('[name="teilnehmer"]').addEventListener("input", updateSummary);

  /* ---------- Senden ---------- */
  form.setAttribute("novalidate", "");
  form.addEventListener("submit", function (ev) {
    ev.preventDefault(); clearErrors(); status.removeAttribute("data-state");
    var a = angebot(); var ok = true;
    if (!a) { ok = false; showStatus("error", "Bitte wähle zuerst, was ihr buchen möchtet."); }
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = typeof v === "string" ? v.trim() : v; });
    if (data.website) return; /* Lockfeld */
    var def = ANGEBOTE[a] || { min: 1, max: 999 };
    var n = num("teilnehmer");
    if (!n || n < def.min || n > def.max) { ok = false; setError("teilnehmer", "Bitte eine Teilnehmerzahl zwischen " + def.min + " und " + def.max + " angeben." + (a === "tickets" && n && n < 5 ? " Unter 5 Personen bitte telefonisch reservieren (ab 2 Tage vorher)." : "")); }
    if (!data.datum) { ok = false; setError("datum", "Bitte ein Datum wählen."); }
    else { var b = dateBlocked(data.datum); if (b) { ok = false; setError("datum", b); } }
    if (!apiDown && !data.uhrzeit) { ok = false; setError("uhrzeit", "Bitte eine Startzeit auswählen."); }
    ["vorname", "nachname", "telefon", "email"].forEach(function (k) { if (!data[k]) { ok = false; setError(k, "Bitte ausfüllen."); } });
    if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(data.email)) { ok = false; setError("email", "Bitte eine gültige E-Mail-Adresse angeben."); }
    if (!$('[name="einwilligung"]').checked) { ok = false; setError("einwilligung", "Bitte der Datenverarbeitung zustimmen."); }
    if (!$('[name="agb"]').checked) { ok = false; setError("agb", "Bitte die AGB bestätigen."); }
    if (!ok) { if (!status.getAttribute("data-state")) showStatus("error", "Bitte prüfe die markierten Felder."); var f = $(".field.is-invalid [name]"); if (f) f.focus(); return; }

    /* Felder für das Portal zusammenstellen */
    var payload = {
      typ: "termin", datum: data.datum, uhrzeit: data.uhrzeit || "", name: data.vorname + " " + data.nachname,
      telefon: data.telefon, email: data.email, einwilligung: "ja", agb: "ja", website: "",
      leistung: a, paket: ANGEBOTE[a].name, teilnehmer: String(n), firma: data.firma || "",
      nachricht: data.nachricht || ""
    };
    ["kinder", "kinderalter", "karterfahrung", "fahrten", "kidspaket", "pizza", "erw1620", "erw21", "supercup", "pause", "stunden", "karts", "schulangebot", "eventname"].forEach(function (k) { if (data[k] !== undefined && data[k] !== "") payload[k] = data[k]; });
    if (form.dataset.preis) payload.preis_schaetzung = form.dataset.preis;
    if (apiDown && data.wunschzeit) payload.uhrzeit_wunsch = data.wunschzeit;

    btn.disabled = true; var old = btn.textContent; btn.textContent = "Wird gesendet …";
    fetch("/api/anfrage", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) {
        if (r.status === 429) throw { soft: "Zu viele Anfragen in kurzer Zeit. Bitte in ein paar Minuten noch einmal versuchen." };
        return r.json().then(function (j) { return { status: r.status, body: j }; });
      })
      .then(function (res) {
        if (res.body && res.body.ok && res.body.ref) { location.href = "danke.html?typ=termin&ref=" + encodeURIComponent(res.body.ref); return; }
        if (res.status === 422 && res.body && res.body.errors) {
          var errs = res.body.errors; var first = null;
          Object.keys(errs).forEach(function (k) { var key = k === "name" ? "vorname" : k; setError(key, errs[k]); if (!first) first = key; });
          if (errs.uhrzeit) { showStatus("error", "Diese Startzeit wurde gerade vergeben. Wir haben die freien Zeiten neu geladen – bitte wähle eine andere."); loadSlots(); }
          else showStatus("error", "Bitte prüfe die markierten Felder.");
          var fe = $('[name="' + first + '"]'); if (fe) fe.focus();
          return;
        }
        throw { soft: "Das hat leider nicht geklappt. Bitte versuche es gleich noch einmal oder reserviere per Telefon, WhatsApp oder E-Mail." };
      })
      .catch(function (e) {
        showStatus("error", (e && e.soft) ? e.soft : "Der Server ist gerade nicht erreichbar. Deine Eingaben bleiben erhalten – bitte reserviere per Telefon, WhatsApp oder E-Mail.");
        fallback(true);
      })
      .finally(function () { btn.disabled = false; btn.textContent = old; });
  });

  /* ---------- Start ---------- */
  var pre = new URLSearchParams(location.search).get("angebot");
  if (pre && ANGEBOTE[pre]) { var r = $('[name="angebot"][value="' + pre + '"]'); if (r) r.checked = true; }
  updateAngebot();
  loadAvail().then(function () { if (dateIn.value) loadSlots(); });
})();
