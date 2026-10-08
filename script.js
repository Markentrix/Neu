/* ElbDetail – Website-Skript (ohne Abhängigkeiten, ohne Tracking) */
(function () {
  "use strict";

  var WA_NUMBER = "491727613807";
  var MAIL = "info@elbdetail.de";

  /* Richtpreise (Kompaktklasse) und Zuschlagsfaktoren je Fahrzeugklasse.
     Die Faktoren sind Erfahrungswerte und können hier zentral angepasst werden. */
  var PACKAGES = {
    frisch:   { name: "Frisch & Sauber", base: 79 },
    komplett: { name: "Komplettpflege",  base: 179 },
    premium:  { name: "Premium Politur", base: 349 }
  };
  var CLASSES = {
    kompakt: { name: "Kleinwagen / Kompakt", factor: 1.0 },
    mittel:  { name: "Limousine / Kombi",    factor: 1.15 },
    suv:     { name: "SUV / Van / Bus",      factor: 1.3 }
  };

  // Basisklasse zeigt den Listenpreis, Zuschlagsklassen werden auf eine 9er-Endung gerundet (89, 209, 449 …)
  function roundPrice(v, factor) { return factor === 1 ? v : Math.round(v / 10) * 10 - 1; }
  function fmt(v) { return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function priceFor(pkgKey, classKey) {
    var p = PACKAGES[pkgKey], c = CLASSES[classKey];
    if (!p || !c) return null;
    return roundPrice(p.base * c.factor, c.factor);
  }
  function waLink(text) {
    return "https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(text);
  }

  /* -------- Fokus zugänglich mitführen (Skip-Link, Anker) -------- */
  function focusTarget(target) {
    var hadTabindex = target.hasAttribute("tabindex");
    if (!hadTabindex) target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
    if (!hadTabindex) {
      target.addEventListener("blur", function () { target.removeAttribute("tabindex"); }, { once: true });
    }
  }
  if (location.hash) {
    var scrollToHash = function () {
      var t = document.getElementById(location.hash.slice(1));
      if (t) t.scrollIntoView({ block: "start", behavior: "auto" });
    };
    scrollToHash();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(scrollToHash);
    window.addEventListener("load", scrollToHash);
  }
  document.addEventListener("click", function (e) {
    var link = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!link || e.defaultPrevented) return;
    var id = link.getAttribute("href").slice(1);
    var target = id ? document.getElementById(id) : null;
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ block: "start", behavior: "smooth" });
      history.pushState(null, "", "#" + id);
      focusTarget(target);
    }
  });

  /* -------- Header -------- */
  var siteHeader = document.querySelector(".site-header");
  if (siteHeader) {
    var updateHeader = function () { siteHeader.classList.toggle("is-scrolled", window.scrollY > 24); };
    window.addEventListener("scroll", updateHeader, { passive: true });
    updateHeader();
  }
  var menuToggle = document.getElementById("menuToggle");
  var mobileNav = document.getElementById("mobileNav");
  if (menuToggle && mobileNav) {
    var setMenu = function (open) {
      menuToggle.setAttribute("aria-expanded", String(open));
      menuToggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
      mobileNav.hidden = !open;
    };
    menuToggle.addEventListener("click", function () { setMenu(menuToggle.getAttribute("aria-expanded") !== "true"); });
    mobileNav.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") { setMenu(false); menuToggle.focus(); }
    });
    document.addEventListener("click", function (e) {
      if (menuToggle.getAttribute("aria-expanded") === "true" && !e.target.closest(".site-header")) setMenu(false);
    });
    if (window.matchMedia) {
      window.matchMedia("(min-width: 900px)").addEventListener("change", function (e) { if (e.matches) setMenu(false); });
    }
  }

  /* -------- FAQ: sanftes Auf-/Zuklappen -------- */
  document.querySelectorAll(".faq-item").forEach(function (item) {
    var summary = item.querySelector("summary");
    var wrap = item.querySelector(".faq-body-wrap");
    if (!summary || !wrap) return;
    summary.addEventListener("click", function (e) {
      e.preventDefault();
      if (item.hasAttribute("data-animating")) return;
      item.setAttribute("data-animating", "true");
      if (item.open) {
        wrap.style.gridTemplateRows = "1fr"; void wrap.offsetHeight; wrap.style.gridTemplateRows = "0fr";
      } else {
        item.open = true; wrap.style.gridTemplateRows = "0fr"; void wrap.offsetHeight; wrap.style.gridTemplateRows = "1fr";
      }
    });
    wrap.addEventListener("transitionend", function (e) {
      if (e.propertyName !== "grid-template-rows") return;
      if (item.open && wrap.style.gridTemplateRows === "0fr") item.open = false;
      wrap.style.gridTemplateRows = "";
      item.removeAttribute("data-animating");
    });
  });

  /* -------- Richtpreis-Rechner (Hero) -------- */
  var quote = document.getElementById("quoteForm");
  if (quote) {
    var qVal = document.getElementById("quoteValue");
    var qBtn = document.getElementById("quoteWa");
    var qPkgName = document.getElementById("quotePkgName");
    var updateQuote = function () {
      var pkg = (quote.querySelector('input[name="qpkg"]:checked') || {}).value;
      var cls = (quote.querySelector('input[name="qclass"]:checked') || {}).value;
      var price = priceFor(pkg, cls);
      if (price == null) return;
      qVal.innerHTML = "<small>ab</small>" + fmt(price) + " €";
      if (qPkgName) qPkgName.textContent = PACKAGES[pkg].name;
      var text = "Hallo ElbDetail, ich interessiere mich für das Paket „" + PACKAGES[pkg].name + "“ (" + CLASSES[cls].name + ", Richtpreis ab " + fmt(price) + " €). Fahrzeug: … Wunschtermin: … Könnt ihr mir ein Angebot machen?";
      qBtn.href = waLink(text);
    };
    quote.addEventListener("change", updateQuote);
    updateQuote();
  }

  /* -------- Preise: Fahrzeugklasse umschalten -------- */
  var priceSwitch = document.getElementById("priceClass");
  if (priceSwitch) {
    var applyClass = function () {
      var cls = (priceSwitch.querySelector('input[name="pclass"]:checked') || {}).value || "kompakt";
      document.querySelectorAll("[data-plan]").forEach(function (plan) {
        var key = plan.getAttribute("data-plan");
        var price = priceFor(key, cls);
        var amount = plan.querySelector(".amount");
        if (amount && price != null) amount.textContent = fmt(price) + " €";
        var cta = plan.querySelector("a[data-wa]");
        if (cta) {
          cta.href = waLink("Hallo ElbDetail, ich möchte das Paket „" + PACKAGES[key].name + "“ anfragen (" + CLASSES[cls].name + ", Richtpreis ab " + fmt(price) + " €). Fahrzeug: … Wunschtermin: …");
        }
      });
      var lbl = document.getElementById("priceClassLabel");
      if (lbl) lbl.textContent = CLASSES[cls].name;
    };
    priceSwitch.addEventListener("change", applyClass);
    applyClass();
  }

  /* Paket im Formular vorauswählen (Links mit data-package) */
  document.addEventListener("click", function (e) {
    var link = e.target.closest ? e.target.closest("a[data-package]") : null;
    var select = document.getElementById("package");
    if (!link || !select) return;
    var wanted = link.getAttribute("data-package");
    for (var i = 0; i < select.options.length; i++) {
      if (select.options[i].value === wanted) { select.selectedIndex = i; break; }
    }
  });

  /* -------- Vorher/Nachher-Slider -------- */
  document.querySelectorAll(".ba").forEach(function (ba) {
    var range = ba.querySelector('input[type="range"]');
    if (!range) return;
    var set = function () { ba.style.setProperty("--pos", range.value + "%"); };
    range.addEventListener("input", set);
    set();
  });

  /* -------- Tastatur offen: Aktionsleiste ausblenden -------- */
  var kbTimer;
  var isField = function (el) { return el && el.matches && el.matches("input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea, select"); };
  document.addEventListener("focusin", function (e) { if (isField(e.target)) { clearTimeout(kbTimer); document.documentElement.classList.add("kb-open"); } });
  document.addEventListener("focusout", function () {
    clearTimeout(kbTimer);
    kbTimer = setTimeout(function () { if (!isField(document.activeElement)) document.documentElement.classList.remove("kb-open"); }, 120);
  });

  /* -------- Google Maps erst nach Klick (DSGVO) -------- */
  var loadMapBtn = document.getElementById("loadMapBtn");
  var mapPlaceholder = document.getElementById("mapPlaceholder");
  if (loadMapBtn && mapPlaceholder) {
    loadMapBtn.addEventListener("click", function () {
      var iframe = document.createElement("iframe");
      iframe.className = "map-frame";
      iframe.loading = "lazy";
      iframe.referrerPolicy = "no-referrer-when-downgrade";
      iframe.title = "Standort ElbDetail, Lachtehäuser Straße 1, 29223 Celle";
      iframe.src = "https://www.google.com/maps?q=Lachteh%C3%A4user%20Stra%C3%9Fe%201,%2029223%20Celle&output=embed";
      mapPlaceholder.replaceWith(iframe);
    });
  }

  /* -------- Kontaktformular: WhatsApp oder E-Mail, ohne Server -------- */
  var form = document.getElementById("contactForm");
  var statusEl = document.getElementById("formStatus");
  var dateInput = document.getElementById("date");
  if (dateInput) {
    var t = new Date();
    dateInput.min = t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") + "-" + String(t.getDate()).padStart(2, "0");
  }
  function formatDateDE(iso) {
    if (!iso) return "";
    var p = iso.split("-");
    return p.length === 3 ? p[2] + "." + p[1] + "." + p[0] : iso;
  }
  if (form && statusEl) {
    var channel = "whatsapp";
    form.querySelectorAll("button[data-channel]").forEach(function (b) {
      b.addEventListener("click", function () { channel = b.getAttribute("data-channel"); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      statusEl.className = "form-status"; statusEl.textContent = "";
      if (form.website && form.website.value) return; // Honeypot

      var name = form.name.value.trim();
      var phone = form.phone.value.trim();
      var email = form.email.value.trim();
      var pkg = form.package.value;
      var date = form.date.value;
      var vehicle = form.vehicle.value.trim();
      var message = form.message.value.trim();
      var consent = form.consent.checked;

      if (!name || !pkg) {
        statusEl.textContent = "Bitte Name und gewünschtes Paket angeben.";
        statusEl.className = "form-status error"; return;
      }
      if (channel === "email" && !email) {
        statusEl.textContent = "Für die Anfrage per E-Mail brauchen wir deine E-Mail-Adresse.";
        statusEl.className = "form-status error"; return;
      }
      if (!consent) {
        statusEl.textContent = "Bitte bestätige die Datenschutzhinweise, damit wir dich kontaktieren dürfen.";
        statusEl.className = "form-status error"; return;
      }

      var lines = [
        "Name: " + name,
        phone ? "Telefon: " + phone : null,
        email ? "E-Mail: " + email : null,
        "Paket: " + pkg,
        date ? "Wunschtermin: " + formatDateDE(date) : null,
        vehicle ? "Fahrzeug: " + vehicle : null,
        message ? "Nachricht: " + message : null
      ].filter(Boolean);

      if (channel === "email") {
        var subject = "Terminanfrage über die Website – " + name + " (" + pkg + ")";
        window.location.href = "mailto:" + MAIL + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
        statusEl.textContent = "Dein E-Mail-Programm öffnet sich mit der vorausgefüllten Anfrage. Bitte dort absenden.";
      } else {
        var text = "Hallo ElbDetail, ich möchte einen Termin anfragen.\n" + lines.join("\n");
        window.open(waLink(text), "_blank", "noopener");
        statusEl.textContent = "WhatsApp öffnet sich mit deiner vorausgefüllten Anfrage. Bitte dort absenden.";
      }
      statusEl.className = "form-status success";
    });
  }

  /* -------- Scroll-Reveal -------- */
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    document.documentElement.classList.add("js-anim");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
    // Sicherheitsnetz: Falls der Observer nicht feuert (Vorschau, Druck, Screenshot), alles einblenden
    setTimeout(function () { document.querySelectorAll(".reveal:not(.is-visible)").forEach(function (el) { el.classList.add("is-visible"); }); }, 3000);
  }

  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();
