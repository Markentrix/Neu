/* Burnout Celler-Kartbahn – Basis-Skript
   Navigation, Karte (Zwei-Klick), Formulare über das Markentrix-Portal (Variante B),
   Gutscheinbestellung nach Shop-Vertrag, zweistufiger Widerruf, Conversion-Ereignisse. */
(function () {
  "use strict";

  /* ---------- Ereignisse (Besucherzahlen ohne Cookies, je Ereignis einmal) ---------- */
  var sent = {};
  function beacon(t, n) {
    try {
      if (navigator.sendBeacon) navigator.sendBeacon("/api/e", new Blob([JSON.stringify({ t: t, u: location.pathname, n: n, w: window.innerWidth })], { type: "application/json" }));
    } catch (e) { /* still */ }
  }
  window.mkEvent = function (name) { if (sent[name]) return; sent[name] = true; beacon("ev", name); };
  beacon("pv", document.title);
  document.querySelectorAll('a[href^="tel:"]').forEach(function (a) { a.addEventListener("click", function () { window.mkEvent("anruf_klick"); }); });
  document.querySelectorAll('a[href*="wa.me"]').forEach(function (a) { a.addEventListener("click", function () { window.mkEvent("whatsapp_klick"); }); });

  /* ---------- Navigation ---------- */
  var burger = document.querySelector(".burger");
  var mnav = document.querySelector(".mobile-nav");
  function closeNav() { if (!mnav) return; mnav.setAttribute("data-open", "false"); burger.setAttribute("aria-expanded", "false"); burger.setAttribute("aria-label", "Menü öffnen"); document.body.style.overflow = ""; }
  if (burger && mnav) {
    burger.addEventListener("click", function () {
      var open = mnav.getAttribute("data-open") === "true";
      if (open) { closeNav(); return; }
      mnav.setAttribute("data-open", "true"); burger.setAttribute("aria-expanded", "true"); burger.setAttribute("aria-label", "Menü schließen"); document.body.style.overflow = "hidden";
      var first = mnav.querySelector("a"); if (first) first.focus();
    });
    mnav.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeNav); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && mnav.getAttribute("data-open") === "true") { closeNav(); burger.focus(); } });
  }
  var here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a, .mobile-nav a").forEach(function (a) {
    var href = (a.getAttribute("href") || "").split("#")[0];
    if (href && href === here) a.setAttribute("aria-current", "page");
  });

  /* ---------- Karte: erst nach Klick laden (Datenschutz) ---------- */
  document.querySelectorAll("[data-map]").forEach(function (box) {
    var btn = box.querySelector("button");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = box.getAttribute("data-map");
      f.title = "Karte: Anfahrt zur Burnout Celler-Kartbahn, Waldweg 100, 29221 Celle";
      f.loading = "lazy"; f.referrerPolicy = "no-referrer";
      box.textContent = ""; box.appendChild(f);
    });
  });

  /* ---------- Formular-Hilfen ---------- */
  function setError(form, name, msg) {
    var el = form.querySelector('[name="' + name + '"]'); if (!el) return;
    var field = el.closest(".field"); if (!field) return;
    var err = field.querySelector(".error");
    if (msg) { field.classList.add("is-invalid"); if (err) err.textContent = msg; }
    else field.classList.remove("is-invalid");
  }
  function clearErrors(form) { form.querySelectorAll(".field.is-invalid").forEach(function (f) { f.classList.remove("is-invalid"); }); }
  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }
  function showStatus(status, state, text) { status.setAttribute("data-state", state); status.textContent = text; }

  window.mkSubmit = function (form, data, status, btn, onOk) {
    status.removeAttribute("data-state"); status.textContent = "";
    btn.disabled = true; var old = btn.textContent; btn.textContent = "Wird gesendet …";
    var typ = data.typ || "kontakt";
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 10000) : null;
    return fetch("/api/anfrage", { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data), signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) {
        if (r.status === 429) throw { soft: "Zu viele Anfragen in kurzer Zeit. Bitte später noch einmal versuchen." };
        return r.json().then(function (j) { return { status: r.status, body: j }; });
      })
      .then(function (res) {
        if (res.body && res.body.ok && res.body.ref) {
          if (onOk) onOk(res.body);
          window.mkEvent(typ + "_gesendet");
          location.href = "danke.html?typ=" + encodeURIComponent(typ) + "&ref=" + encodeURIComponent(res.body.ref);
          return true;
        }
        if (res.status === 422 && res.body && res.body.errors) {
          var first = null;
          Object.keys(res.body.errors).forEach(function (k) { setError(form, k, res.body.errors[k]); if (!first) first = k; });
          showStatus(status, "error", "Bitte prüfe die markierten Felder.");
          var fe = form.querySelector('[name="' + first + '"]'); if (fe) fe.focus();
          return false;
        }
        throw { soft: "Das hat leider nicht geklappt. Bitte versuche es gleich noch einmal oder nutze Telefon, WhatsApp oder E-Mail." };
      })
      .catch(function (e) {
        showStatus(status, "error", (e && e.soft ? e.soft : "Der Server antwortet gerade nicht. Deine Eingaben bleiben erhalten. Bitte noch einmal senden oder Telefon, WhatsApp oder E-Mail nutzen."));
        var fb = form.querySelector(".fallback"); if (fb) fb.hidden = false;
        return false;
      })
      .finally(function () { if (timer) clearTimeout(timer); btn.disabled = false; btn.textContent = old; });
  };

  function collect(form) {
    var data = {}; new FormData(form).forEach(function (v, k) { data[k] = typeof v === "string" ? v.trim() : v; }); return data;
  }
  function validate(form, data) {
    var ok = true;
    form.querySelectorAll("[required]").forEach(function (el) {
      if (el.disabled || el.closest("[hidden]")) return;
      var v = el.type === "checkbox" ? el.checked : el.value.trim();
      if (!v) { ok = false; setError(form, el.name, el.type === "checkbox" ? "Bitte zustimmen." : "Bitte ausfüllen."); }
    });
    var em = form.querySelector('[name="email"]');
    if (em && em.value && !validEmail(em.value)) { ok = false; setError(form, "email", "Bitte eine gültige E-Mail-Adresse angeben, dorthin geht die Bestätigung."); }
    return ok;
  }

  /* ---------- Kontakt / Firma (einstufig) ---------- */
  document.querySelectorAll("form[data-mk-form]").forEach(function (form) {
    var typ = form.getAttribute("data-mk-form");
    if (typ === "gutschein" || typ === "widerruf") return;
    var status = form.querySelector(".form-status");
    var btn = form.querySelector('button[type="submit"]');
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault(); clearErrors(form);
      var data = collect(form); if (data.website) return; /* Lockfeld gefüllt: nichts senden */
      var ok = validate(form, data);
      data.einwilligung = form.querySelector('[name="einwilligung"]').checked ? "ja" : ""; data.typ = typ;
      if (!ok) { showStatus(status, "error", "Bitte fülle alle Pflichtfelder aus."); var f = form.querySelector(".field.is-invalid [name]"); if (f) f.focus(); return; }
      window.mkSubmit(form, data, status, btn);
    });
  });

  /* ---------- Gutscheinbestellung (Shop-Vertrag: nur wenn /api/gutschein aktiv) ---------- */
  var gForm = document.querySelector('form[data-mk-form="gutschein"]');
  if (gForm) {
    var gBox = gForm.closest("[data-gutschein]") || gForm.parentNode;
    var gStatus = gForm.querySelector(".form-status"), gBtn = gForm.querySelector('button[type="submit"]');
    var gOff = document.querySelector("[data-gutschein-aus]");
    var euro = function (n) { return Number(n).toLocaleString("de-DE", { style: "currency", currency: "EUR" }); };
    function gutscheinAus() { gBox.hidden = true; if (gOff) gOff.hidden = false; }
    fetch("/api/gutschein", { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (g) {
        if (!g || !g.aktiv) return gutscheinAus();
        var sel = gForm.querySelector('[name="betrag"]'), frei = gForm.querySelector('[name="betrag_frei"]');
        if (sel && g.betraege && g.betraege.length) {
          sel.textContent = "";
          g.betraege.forEach(function (b) { var o = document.createElement("option"); o.value = String(b); o.textContent = euro(b); sel.appendChild(o); });
          var o = document.createElement("option"); o.value = "frei"; o.textContent = "Anderer Betrag"; sel.appendChild(o);
        }
        if (frei) { if (g.min) frei.min = g.min; if (g.max) frei.max = g.max; var h = frei.closest(".field").querySelector(".hint"); if (h && g.min && g.max) h.textContent = "Zwischen " + euro(g.min) + " und " + euro(g.max) + "."; }
        var zu = gForm.querySelector('[name="zustellung"]');
        if (zu && g.zustellung && g.zustellung.length) { zu.textContent = ""; g.zustellung.forEach(function (z) { var o = document.createElement("option"); o.value = z; o.textContent = z; zu.appendChild(o); }); }
        var g1 = document.querySelector("[data-gueltigkeit]"); if (g1 && g.gueltigkeitMonate) g1.textContent = "Gültig " + g.gueltigkeitMonate + " Monate ab Ausstellung.";
        gBox.hidden = false; updateSummary();
      })
      .catch(gutscheinAus);
    function betrag() { var sel = gForm.querySelector('[name="betrag"]'), frei = gForm.querySelector('[name="betrag_frei"]'); if (!sel) return 0; if (sel.value === "frei") return parseFloat((frei && frei.value || "0").replace(",", ".")) || 0; return parseFloat(sel.value) || 0; }
    function updateSummary() {
      var s = gForm.querySelector("[data-summary]"); if (!s) return;
      var b = betrag(), zu = gForm.querySelector('[name="zustellung"]'), emp = gForm.querySelector('[name="empfaenger"]');
      s.querySelectorAll("[data-s-betrag]").forEach(function (el) { el.textContent = b ? euro(b) : "–"; });
      s.querySelector("[data-s-zustellung]").textContent = zu && zu.value ? zu.value : "–";
      s.querySelector("[data-s-empfaenger]").textContent = emp && emp.value.trim() ? emp.value.trim() : "–";
      var freiField = gForm.querySelector('[name="betrag_frei"]'); if (freiField) { var sel = gForm.querySelector('[name="betrag"]'); freiField.closest(".field").hidden = !(sel && sel.value === "frei"); }
    }
    gForm.addEventListener("input", updateSummary); gForm.addEventListener("change", updateSummary);
    gForm.setAttribute("novalidate", "");
    gForm.addEventListener("submit", function (ev) {
      ev.preventDefault(); clearErrors(gForm);
      var data = collect(gForm); if (data.website) return;
      var ok = validate(gForm, data); var b = betrag();
      var frei = gForm.querySelector('[name="betrag_frei"]');
      if (!b || (frei && !frei.closest(".field").hidden && (b < parseFloat(frei.min || 0) || b > parseFloat(frei.max || 99999)))) { ok = false; setError(gForm, frei && !frei.closest(".field").hidden ? "betrag_frei" : "betrag", "Bitte einen gültigen Betrag wählen."); }
      if (!ok) { showStatus(gStatus, "error", "Bitte prüfe die markierten Felder."); var f = gForm.querySelector(".field.is-invalid [name]"); if (f) f.focus(); return; }
      var payload = { typ: "gutschein", betrag: b.toFixed(2), zustellung: data.zustellung, empfaenger: data.empfaenger || "", absender: data.absender || "", gutscheintext: data.gutscheintext || "", anschrift: data.anschrift || "", name: data.name, email: data.email, telefon: data.telefon || "", einwilligung: "ja", agb: "ja", website: "" };
      window.mkSubmit(gForm, payload, gStatus, gBtn);
    });
  }

  /* ---------- Widerruf (zweistufig, § 356a BGB) ---------- */
  var wForm = document.querySelector('form[data-mk-form="widerruf"]');
  if (wForm) {
    var wStatus = wForm.querySelector(".form-status"), step1 = wForm.querySelector("[data-step1]"), step2 = wForm.querySelector("[data-step2]");
    var wNext = wForm.querySelector("[data-next]"), wBack = wForm.querySelector("[data-back]"), wBtn = wForm.querySelector('button[type="submit"]');
    wForm.setAttribute("novalidate", "");
    wNext.addEventListener("click", function () {
      clearErrors(wForm); var data = collect(wForm);
      if (!validate(wForm, data)) { showStatus(wStatus, "error", "Bitte fülle alle Pflichtfelder aus."); var f = wForm.querySelector(".field.is-invalid [name]"); if (f) f.focus(); return; }
      wStatus.removeAttribute("data-state");
      ["name", "email", "vorgang", "nachricht"].forEach(function (k) { var t = step2.querySelector("[data-w-" + k + "]"); if (t) t.textContent = data[k] || "–"; });
      step1.hidden = true; step2.hidden = false; step2.querySelector("h3").focus();
    });
    wBack.addEventListener("click", function () { step2.hidden = true; step1.hidden = false; });
    wForm.addEventListener("submit", function (ev) {
      ev.preventDefault(); var data = collect(wForm); if (data.website) return;
      var payload = { typ: "widerruf", name: data.name, email: data.email, telefon: data.telefon || "", vorgang: data.vorgang || "", nachricht: data.nachricht || "", einwilligung: "ja", website: "" };
      window.mkSubmit(wForm, payload, wStatus, wBtn);
    });
  }

  /* ---------- Danke-Seite (Werte aus der URL nur per textContent) ---------- */
  var ref = document.getElementById("ref");
  if (ref) {
    var q = new URLSearchParams(location.search);
    var r = q.get("ref"); var t = q.get("typ") || "kontakt";
    ref.textContent = r ? r : "–";
    var titles = { kontakt: "Danke, Nachricht ist da", termin: "Danke, Reservierung ist da", gutschein: "Danke für die Bestellung", firma: "Danke für die Anfrage", widerruf: "Widerruf eingegangen" };
    var h = document.getElementById("danke-title"); if (h && titles[t]) h.textContent = titles[t];
    var tx = document.getElementById("danke-text");
    var texts = {
      termin: "Wir prüfen deinen Wunschtermin und bestätigen die Reservierung per E-Mail. Erst mit unserer Buchungsbestätigung ist der Termin verbindlich. Bitte 30 Minuten vor der Startzeit bei uns eintreffen.",
      gutschein: "Du bekommst in Kürze eine E-Mail mit den Zahlungsinformationen. Nach Zahlungseingang senden wir dir den Gutschein mit Gutscheincode zu.",
      widerruf: "Wir bestätigen dir den Eingang deines Widerrufs per E-Mail und melden uns zur Rückabwicklung.",
      firma: "Wir melden uns mit einem individuellen Angebot bei dir, in der Regel innerhalb von zwei Werktagen."
    };
    if (tx && texts[t]) tx.textContent = texts[t];
  }
})();
