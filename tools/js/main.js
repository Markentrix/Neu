/* Burnout Celler-Kartbahn – Basis-Skript: Navigation, Karte (2-Klick), Formulare über das Markentrix-Portal */
(function () {
  "use strict";

  /* ---------- Navigation ---------- */
  var burger = document.querySelector(".burger");
  var mnav = document.querySelector(".mobile-nav");
  if (burger && mnav) {
    burger.addEventListener("click", function () {
      var open = mnav.getAttribute("data-open") === "true";
      mnav.setAttribute("data-open", open ? "false" : "true");
      burger.setAttribute("aria-expanded", open ? "false" : "true");
      burger.setAttribute("aria-label", open ? "Menü öffnen" : "Menü schließen");
      document.body.style.overflow = open ? "" : "hidden";
    });
    mnav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        mnav.setAttribute("data-open", "false");
        burger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });
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
      f.loading = "lazy";
      f.referrerPolicy = "no-referrer";
      box.innerHTML = "";
      box.appendChild(f);
    });
  });

  /* ---------- Besucherzahl (ohne Cookies, Portal) ---------- */
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/e", new Blob([JSON.stringify({ t: "pv", u: location.pathname, n: document.title, w: window.innerWidth })], { type: "application/json" }));
    }
  } catch (e) { /* still */ }

  /* ---------- Formulare: Kontakt, Gutschein, Widerruf ---------- */
  function setError(form, name, msg) {
    var el = form.querySelector('[name="' + name + '"]');
    if (!el) return;
    var field = el.closest(".field");
    if (!field) return;
    var err = field.querySelector(".error");
    if (msg) { field.classList.add("is-invalid"); if (err) err.textContent = msg; }
    else { field.classList.remove("is-invalid"); }
  }
  function clearErrors(form) {
    form.querySelectorAll(".field.is-invalid").forEach(function (f) { f.classList.remove("is-invalid"); });
  }
  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }

  window.mkSubmit = function (form, data, status, btn) {
    status.removeAttribute("data-state"); status.textContent = "";
    btn.disabled = true; var old = btn.textContent; btn.textContent = "Wird gesendet …";
    var typ = data.typ || "kontakt";
    return fetch("/api/anfrage", {
      method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(data)
    }).then(function (r) {
      if (r.status === 429) { throw { soft: "Zu viele Anfragen in kurzer Zeit. Bitte in ein paar Minuten noch einmal versuchen." }; }
      return r.json().then(function (j) { return { status: r.status, body: j }; });
    }).then(function (res) {
      if (res.body && res.body.ok && res.body.ref) {
        location.href = "danke.html?typ=" + encodeURIComponent(typ) + "&ref=" + encodeURIComponent(res.body.ref);
        return true;
      }
      if (res.status === 422 && res.body && res.body.errors) {
        var first = null;
        Object.keys(res.body.errors).forEach(function (k) { setError(form, k, res.body.errors[k]); if (!first) first = k; });
        status.setAttribute("data-state", "error");
        status.textContent = "Bitte prüfe die markierten Felder.";
        var fe = form.querySelector('[name="' + first + '"]'); if (fe) fe.focus();
        return false;
      }
      throw { soft: "Das hat leider nicht geklappt. Bitte versuche es gleich noch einmal oder nutze Telefon, WhatsApp oder E-Mail." };
    }).catch(function (e) {
      status.setAttribute("data-state", "error");
      status.innerHTML = (e && e.soft ? e.soft : "Der Server ist gerade nicht erreichbar. Bitte nutze Telefon, WhatsApp oder E-Mail.") +
        ' <span class="small">Deine Eingaben bleiben erhalten.</span>';
      var fb = form.querySelector(".fallback"); if (fb) fb.hidden = false;
      return false;
    }).finally(function () { btn.disabled = false; btn.textContent = old; });
  };

  document.querySelectorAll("form[data-mk-form]").forEach(function (form) {
    var status = form.querySelector(".form-status");
    var btn = form.querySelector('button[type="submit"]');
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      clearErrors(form);
      var data = {}; var ok = true;
      new FormData(form).forEach(function (v, k) { data[k] = typeof v === "string" ? v.trim() : v; });
      form.querySelectorAll("[required]").forEach(function (el) {
        var v = el.type === "checkbox" ? el.checked : el.value.trim();
        if (!v) { ok = false; setError(form, el.name, el.type === "checkbox" ? "Bitte zustimmen." : "Bitte ausfüllen."); }
      });
      var em = form.querySelector('[name="email"]');
      if (em && em.value && !validEmail(em.value)) { ok = false; setError(form, "email", "Bitte eine gültige E-Mail-Adresse angeben."); }
      if (data.website) { return; } /* Lockfeld gefüllt: nichts senden */
      data.einwilligung = form.querySelector('[name="einwilligung"]') && form.querySelector('[name="einwilligung"]').checked ? "ja" : "";
      data.typ = form.getAttribute("data-mk-form") || "kontakt";
      if (!ok) {
        status.setAttribute("data-state", "error"); status.textContent = "Bitte fülle alle Pflichtfelder aus.";
        var f = form.querySelector(".field.is-invalid [name]"); if (f) f.focus();
        return;
      }
      window.mkSubmit(form, data, status, btn);
    });
  });

  /* ---------- Danke-Seite ---------- */
  var ref = document.getElementById("ref");
  if (ref) {
    var q = new URLSearchParams(location.search);
    var r = q.get("ref"); var t = q.get("typ") || "kontakt";
    ref.textContent = r ? r : "–";
    var titles = { kontakt: "Danke für deine Nachricht!", termin: "Danke für deine Buchungsanfrage!", gutschein: "Danke für deine Gutschein-Bestellung!", firma: "Danke für deine Event-Anfrage!", widerruf: "Dein Widerruf ist eingegangen." };
    var h = document.getElementById("danke-title"); if (h && titles[t]) h.textContent = titles[t];
    var tx = document.getElementById("danke-text");
    var texts = {
      termin: "Wir prüfen deinen Wunschtermin und bestätigen dir die Buchung per E-Mail. Erst mit unserer Buchungsbestätigung ist der Termin verbindlich. Bitte denkt daran: 30 Minuten vor der Startzeit bei uns eintreffen.",
      gutschein: "Du erhältst in Kürze eine E-Mail mit den Zahlungsinformationen. Nach Zahlungseingang senden wir dir den Gutschein mit Gutscheincode per E-Mail zu.",
      widerruf: "Wir bestätigen dir den Eingang deines Widerrufs per E-Mail und melden uns zur Rückabwicklung.",
      firma: "Wir melden uns mit einem individuellen Angebot bei dir, in der Regel innerhalb von zwei Werktagen."
    };
    if (tx && texts[t]) tx.textContent = texts[t];
  }
})();
