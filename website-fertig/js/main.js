// AJ Atelier – Navigation, Öffnungsstatus und Online-Terminbuchung
(function () {
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const euro = (n) => new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", minimumFractionDigits: n % 1 ? 2 : 0 }).format(n);
const duration = (m) => (m >= 60 ? `${Math.floor(m / 60)} Std.${m % 60 ? ` ${m % 60} Min.` : ""}` : `${m} Min.`);
const longDate = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString("de-DE", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

function berlinNow() {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23", weekday: "short",
  }).formatToParts(new Date()).map((x) => [x.type, x.value]));
  const days = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return { date: `${p.year}-${p.month}-${p.day}`, day: days[p.weekday], minutes: +p.hour * 60 + +p.minute };
}

// ---------- Navigation ----------
const header = $("[data-header]");
const toggle = $("[data-nav-toggle]");
const mobileNav = $("[data-mobile-nav]");
toggle?.addEventListener("click", () => {
  const open = toggle.getAttribute("aria-expanded") !== "true";
  toggle.setAttribute("aria-expanded", String(open));
  mobileNav.hidden = !open;
});
mobileNav?.addEventListener("click", (e) => {
  if (e.target.closest("a")) { toggle.setAttribute("aria-expanded", "false"); mobileNav.hidden = true; }
});
const mobileCta = $(".mobile-cta");
const bookingSection = $("#termin");
const onScroll = () => {
  header?.classList.toggle("is-scrolled", scrollY > 10);
  if (mobileCta) {
    const r = bookingSection?.getBoundingClientRect();
    const inBooking = r && r.top < innerHeight && r.bottom > 0;
    mobileCta.classList.toggle("is-visible", scrollY > 500 && !inBooking);
  }
};
addEventListener("scroll", onScroll, { passive: true });
onScroll();

// ---------- Einblenden beim Scrollen ----------
// Nur Bereiche, die beim Laden noch unterhalb des Bildschirms liegen; ohne JS oder
// mit „Bewegung reduzieren“ bleibt alles sofort sichtbar.
const REVEAL = ".section-head, .svc-card, .price-card, .price-teaser, .faq details, .aside-card, .service-box, .steps-list li, "
  + ".split > *, .prose > *, .cta-inner, .table-wrap, .voucher-card, .info-grid > *, .map-actions, .contact-grid > *, .soon, .contact-form";
if (matchMedia("(prefers-reduced-motion: no-preference)").matches && "IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    for (const { target, isIntersecting } of entries) {
      if (!isIntersecting) continue;
      io.unobserve(target);
      target.classList.add("is-in");
      const done = (e) => {
        if (e.target !== target || e.propertyName !== "transform") return;
        target.removeEventListener("transitionend", done);
        target.classList.remove("reveal", "is-in");
        target.style.removeProperty("--d");
      };
      target.addEventListener("transitionend", done);
    }
  }, { rootMargin: "0px 0px -6% 0px", threshold: 0.08 });
  const groups = new Map();
  for (const el of $$(REVEAL)) {
    if (el.closest("[data-booking]") || el.parentElement.closest(".reveal")) continue;
    if (el.getBoundingClientRect().top < innerHeight) continue;
    const n = groups.get(el.parentElement) ?? 0;
    groups.set(el.parentElement, n + 1);
    el.style.setProperty("--d", Math.min(n, 5));
    el.classList.add("reveal");
    io.observe(el);
  }
}

// ---------- „Jetzt geöffnet“ ----------
const hoursEl = $("#hours-data");
if (hoursEl) {
  const DATA = JSON.parse(hoursEl.textContent);
  const now = berlinNow();
  const toMin = (t) => +t.slice(0, 2) * 60 + +t.slice(3);
  const today = DATA.hours[now.day];
  const holiday = DATA.holidays.includes(now.date);
  $(`.hours tr[data-day="${now.day}"]`)?.classList.add("is-today");
  const el = $("[data-open-now]");
  if (el) {
    if (today && !holiday && now.minutes >= toMin(today[0]) && now.minutes < toMin(today[1])) {
      el.textContent = `Jetzt geöffnet – bis ${today[1]} Uhr`;
      el.classList.add("is-open");
    } else {
      el.textContent = holiday ? "Heute Feiertag – geschlossen" : "Derzeit geschlossen – online buchen jederzeit möglich";
    }
  }
}

// ---------- Anfragen an das Markentrix-Portal (/api/anfrage) ----------
// Antwort: {ok, ref} | 422 {errors:{feld:text}} | 429. Ohne Server (z. B. Doppelklick-Vorschau) → kind "offline".
async function sendAnfrage(payload) {
  let res;
  try {
    res = await fetch("/api/anfrage", {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    return { kind: "offline" };
  }
  const data = await res.json().catch(() => null);
  if (res.ok && data?.ok && data.ref) return { kind: "ok", ref: data.ref };
  if (res.status === 422 && data?.errors) return { kind: "invalid", errors: data.errors };
  if (res.status === 429) return { kind: "busy" };
  return { kind: "offline" };
}

/** Fehlertexte an die Felder schreiben; liefert das erste fehlerhafte Feld. */
function showFieldErrors(form, errors) {
  let first = null;
  $$("[data-error-for]", form).forEach((el) => {
    const msg = errors[el.dataset.errorFor] || "";
    el.textContent = msg;
    const input = form.elements[el.dataset.errorFor];
    if (input && !(input instanceof RadioNodeList)) input.setAttribute("aria-invalid", String(Boolean(msg)));
    if (msg && !first) first = input instanceof RadioNodeList ? input[0] : input;
  });
  return first;
}

/** Prüft die Pflichtfelder eines Formulars im Browser (der Server prüft noch einmal). */
function checkRequired(form, extra = {}) {
  const errors = { ...extra };
  for (const el of form.elements) {
    if (!el.name || el.disabled || el.closest("[hidden]")) continue;
    const v = el.type === "checkbox" ? el.checked : el.value.trim();
    if (el.required && !v) {
      errors[el.name] ??= el.type === "checkbox" ? "Bitte stimmen Sie der Verarbeitung zu." : "Bitte ausfüllen.";
    } else if (v && el.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim())) {
      errors[el.name] ??= "Bitte eine gültige E-Mail-Adresse angeben.";
    } else if (v && el.type === "tel" && !/^[+()\d\s/-]{6,30}$/.test(el.value.trim())) {
      errors[el.name] ??= "Bitte eine gültige Telefonnummer angeben.";
    } else if (v && el.minLength > 0 && el.value.trim().length < el.minLength) {
      errors[el.name] ??= `Bitte mindestens ${el.minLength} Zeichen.`;
    }
  }
  return errors;
}

// Weiterleitung auf die Danke-Seite. Typ und Nummer liegen zusätzlich im Browser, falls eine Umleitung
// des Servers (danke.html → /danke) die Parameter nicht mitnimmt.
const thanks = (typ, ref) => {
  try { sessionStorage.setItem("aj-anfrage", JSON.stringify({ typ, ref })); } catch { /* ohne Speicher nur per Adresse */ }
  return `danke.html?typ=${encodeURIComponent(typ)}&ref=${encodeURIComponent(ref)}`;
};
window.AJ = { sendAnfrage, showFieldErrors, checkRequired, thanks };

// ---------- Online-Terminbuchung ----------
const root = $("[data-booking]");
if (root) initBooking(root);

function initBooking(root) {
  const getJSON = async (url) => {
    const r = await fetch(url, { headers: { accept: "application/json" }, cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  };
  const qs = (o) => new URLSearchParams(Object.entries(o).filter(([, v]) => v)).toString();
  const state = { step: 1, services: [], staff: [], service: null, person: "", avail: null, date: null, time: null, sending: false };
  const fallback = $("[data-fallback]", root);
  const body = $("[data-booking-body]", root);
  const goOffline = () => { fallback.hidden = false; body.hidden = true; };

  // Schritte
  const stepsBar = $(".steps", root);
  function showStep(step) {
    const back = step < state.step;
    state.step = step;
    $$("[data-step]", root).forEach((el) => (el.hidden = el.dataset.step !== String(step)));
    stepsBar.style.setProperty("--progress", `${(step / 3) * 100}%`);
    const entering = $(`[data-step="${step}"]`, root);
    const cls = back ? "is-leaving-back" : "is-entering";
    entering.classList.remove("is-entering", "is-leaving-back");
    void entering.offsetWidth; // Animation neu starten
    entering.classList.add(cls);
    entering.addEventListener("animationend", () => entering.classList.remove(cls), { once: true });
    $$("[data-step-label]", root).forEach((li) => {
      const n = +li.dataset.stepLabel;
      li.classList.toggle("is-active", n === step);
      li.classList.toggle("is-done", n < step);
    });
    const top = root.getBoundingClientRect().top;
    if (top < 0 || top > innerHeight * 0.6) root.scrollIntoView({ behavior: "smooth", block: "start" });
    const h = entering.querySelector("h3");
    h?.setAttribute("tabindex", "-1");
    h?.focus({ preventScroll: true });
    if (step === 2) loadDays();
  }
  $$("[data-back]", root).forEach((b) => b.addEventListener("click", () => showStep(state.step - 1)));

  // Zusammenfassung
  const priceText = (p) => (p === null || p === undefined || p === "" ? "–" : typeof p === "number" ? euro(p) : String(p));
  function renderSummary() {
    const s = state.service;
    $("[data-summary-service]", root).textContent = s ? s.name : (state.services.length ? "–" : "nach Absprache");
    $("[data-summary-duration]", root).textContent = s?.dauer ? `ca. ${duration(+s.dauer)}` : "–";
    $("[data-summary-price]", root).textContent = s ? priceText(s.preis) : "–";
    $("[data-summary-hint]", root).hidden = !(s && /\bab\b/i.test(String(s.preis)));
    $("[data-summary-date]", root).textContent = state.date && state.time
      ? `${new Date(`${state.date}T12:00`).toLocaleDateString("de-DE", { weekday: "short", day: "2-digit", month: "2-digit" })}, ${state.time} Uhr` : "–";
    const person = state.staff.find((m) => m.key === state.person);
    $("[data-summary-staff-row]", root).hidden = !person;
    $("[data-summary-staff]", root).textContent = person?.name || "";
  }

  // Schritt 1: Leistung (und ggf. Wunschperson) – Listen kommen aus dem Portal
  const picker = $("[data-service-picker]", root);
  const next1 = $('[data-step="1"] [data-next]', root);
  const staffWrap = $("[data-staff-wrap]", root);
  const staffSel = $("[data-staff]", root);
  function renderStaff() {
    const offers = (m) => !m.leistungen?.length || !state.service || m.leistungen.includes(state.service.key);
    const list = state.staff.filter(offers);
    staffWrap.hidden = list.length < 2;
    if (!list.some((m) => m.key === state.person)) state.person = "";
    staffSel.innerHTML = '<option value="">Egal – erste freie Person</option>';
    list.forEach((m) => staffSel.add(new Option(m.name, m.key, false, m.key === state.person)));
  }
  staffSel.addEventListener("change", () => { state.person = staffSel.value; state.avail = null; state.date = state.time = null; renderSummary(); });

  picker.addEventListener("change", (e) => {
    state.service = state.services.find((s) => s.key === e.target.value) || null;
    state.avail = null;
    state.date = state.time = null;
    next1.disabled = !state.service;
    renderStaff();
    renderSummary();
  });
  next1.addEventListener("click", () => showStep(2));

  function renderServices() {
    picker.innerHTML = "";
    const box = document.createElement("div");
    box.className = "service-options";
    box.setAttribute("role", "radiogroup");
    box.setAttribute("aria-labelledby", "st1");
    state.services.forEach((s) => {
      const label = document.createElement("label");
      label.className = "service-option";
      label.innerHTML = '<input type="radio" name="leistung"><span><span class="n"></span><small></small></span><span class="price"></span>';
      label.querySelector("input").value = s.key;
      label.querySelector(".n").textContent = s.name;
      label.querySelector("small").textContent = [s.dauer ? `ca. ${duration(+s.dauer)}` : "", s.beschreibung || ""].filter(Boolean).join(" · ");
      label.querySelector(".price").textContent = s.preis === null || s.preis === undefined || s.preis === "" ? "" : priceText(s.preis);
      box.append(label);
    });
    picker.append(box);
  }

  Promise.all([
    getJSON("/api/leistungen").then((d) => d.leistungen || []).catch((e) => (e.message === "404" ? [] : Promise.reject(e))),
    getJSON("/api/mitarbeiter").then((d) => d.mitarbeiter || []).catch(() => []),
  ]).then(([services, staff]) => {
    state.services = services;
    state.staff = staff;
    if (!services.length) {
      // Der Salon bucht ohne Leistungsliste: Wunsch als Freitext, direkt zur Terminwahl
      $("[data-wish-wrap]", root).hidden = false;
      $("[data-wish-wrap] input", root).required = true;
      $('[data-step-label="1"]', root).hidden = true;
      picker.innerHTML = "";
      renderStaff();
      renderSummary();
      if (staffWrap.hidden) { $('[data-step="1"]', root).hidden = true; showStep(2); $('[data-step="2"] [data-back]', root).hidden = true; }
      else next1.disabled = false;
      return;
    }
    renderServices();
    renderStaff();
    // Direktwahl über Links wie termin.html?leistung=f-balayage
    const pre = new URLSearchParams(location.search).get("leistung");
    const input = pre && $$('input[name="leistung"]', picker).find((i) => i.value === pre);
    if (input) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
    renderSummary();
  }).catch(goOffline);

  // Schritt 2: Datum & Uhrzeit
  const strip = $("[data-date-strip]", root);
  const slotsEl = $("[data-slots]", root);
  const slotError = $("[data-slot-error]", root);
  const next2 = $('[data-step="2"] [data-next]', root);
  const filter = () => ({ leistung: state.service?.key || "", mitarbeiter: state.person });
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const HORIZON = 60;

  async function loadDays() {
    if (state.avail) return selectDate(state.date, true);
    strip.innerHTML = "";
    slotsEl.innerHTML = '<div class="loader" role="status" aria-label="Lade freie Tage"></div>';
    next2.disabled = true;
    try {
      state.avail = await getJSON(`/api/verfuegbarkeit?${qs(filter())}`);
    } catch {
      return goOffline();
    }
    const a = state.avail;
    applyBookingMode(a.selfBooking !== false);
    const blocked = new Set(a.blocked || []);
    const closed = new Set(a.closedWeekdays || []);
    const start = new Date();
    for (let i = 0; i <= HORIZON; i++) {
      const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i, 12);
      const id = iso(d);
      const open = !closed.has(d.getDay()) && !blocked.has(id) && (!a.nextFree || id >= a.nextFree);
      const b = document.createElement("button");
      b.type = "button";
      b.className = "date-btn";
      b.dataset.date = id;
      b.disabled = !open;
      b.setAttribute("aria-pressed", "false");
      b.setAttribute("aria-label", longDate(id) + (open ? "" : " – nicht buchbar"));
      b.innerHTML = `<span>${d.toLocaleDateString("de-DE", { weekday: "short" })}</span><strong>${d.getDate()}</strong><span>${d.toLocaleDateString("de-DE", { month: "short" })}</span>`;
      strip.append(b);
    }
    const first = $(".date-btn:not(:disabled)", strip);
    if (!first) {
      slotsEl.innerHTML = '<p class="empty">In den nächsten Wochen ist online leider nichts frei. Rufen Sie uns gerne an, oft finden wir telefonisch noch eine Lösung.</p>';
      return;
    }
    selectDate(state.date && !$(`.date-btn[data-date="${state.date}"]`, strip)?.disabled ? state.date : first.dataset.date, true);
  }

  // Ohne Selbstbuchung im Portal ist es ein Terminwunsch, den der Salon bestätigt
  function applyBookingMode(self) {
    $("#st2", root).textContent = self ? "Wann passt es Ihnen?" : "Wann hätten Sie gern Ihren Termin?";
    $("[data-submit]", root).textContent = self ? "Termin verbindlich buchen" : "Terminwunsch senden";
    root.dataset.mode = self ? "buchung" : "wunsch";
  }

  strip.addEventListener("click", (e) => {
    const b = e.target.closest(".date-btn");
    if (b && !b.disabled) { state.time = null; selectDate(b.dataset.date); }
  });
  $("[data-date-prev]", root).addEventListener("click", () => strip.scrollBy({ left: -strip.clientWidth * 0.8, behavior: "smooth" }));
  $("[data-date-next]", root).addEventListener("click", () => strip.scrollBy({ left: strip.clientWidth * 0.8, behavior: "smooth" }));

  async function selectDate(date, scroll = false) {
    state.date = date;
    $$(".date-btn", strip).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.date === date)));
    if (scroll) $(`.date-btn[data-date="${date}"]`, strip)?.scrollIntoView({ block: "nearest", inline: "center" });
    renderSummary();
    next2.disabled = !state.time;
    slotsEl.innerHTML = '<div class="loader" role="status" aria-label="Lade freie Zeiten"></div>';
    let slots;
    try {
      slots = (await getJSON(`/api/slots?${qs({ tag: date, ...filter() })}`)).slots || [];
    } catch {
      slotsEl.innerHTML = '<p class="empty">Freie Zeiten konnten nicht geladen werden. Bitte versuchen Sie es erneut oder rufen Sie uns an.</p>';
      return;
    }
    if (state.date !== date) return;
    const free = slots.filter((s) => s.frei).map((s) => s.zeit);
    if (state.time && !free.includes(state.time)) state.time = null;
    slotsEl.innerHTML = "";
    if (!free.length) {
      slotsEl.innerHTML = '<p class="empty">An diesem Tag ist leider nichts mehr frei. Bitte wählen Sie einen anderen Tag.</p>';
    }
    free.forEach((t, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "slot-btn";
      b.textContent = t;
      b.setAttribute("aria-pressed", String(t === state.time));
      b.setAttribute("aria-label", `${t} Uhr`);
      b.style.setProperty("--i", i);
      slotsEl.append(b);
    });
    next2.disabled = !state.time;
    renderSummary();
  }
  slotsEl.addEventListener("click", (e) => {
    const b = e.target.closest(".slot-btn");
    if (!b) return;
    state.time = b.textContent;
    slotError.hidden = true;
    $$(".slot-btn", slotsEl).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    next2.disabled = false;
    renderSummary();
  });
  next2.addEventListener("click", () => showStep(3));

  // Schritt 3: Kontaktdaten und Absenden
  const form = $("[data-customer-form]", root);
  const formError = $("[data-form-error]", root);
  const submit = $("[data-submit]", root);
  form.addEventListener("submit", (e) => { e.preventDefault(); send(); });
  submit.addEventListener("click", send);

  async function send() {
    if (state.sending) return; // Doppelklick verhindern
    formError.hidden = true;
    const errors = checkRequired(form);
    const first = showFieldErrors(form, errors);
    if (first) { first.focus(); return; }
    state.sending = true;
    submit.disabled = true;
    const label = submit.textContent;
    submit.textContent = "Wird gesendet …";
    const f = form.elements;
    const s = state.service;
    const person = state.staff.find((m) => m.key === state.person);
    const result = await sendAnfrage({
      typ: "termin",
      name: f.name.value.trim(), telefon: f.telefon.value.trim(), email: f.email.value.trim(),
      nachricht: f.nachricht.value.trim(),
      datum: state.date, uhrzeit: state.time,
      leistung: s?.key || "", leistung_name: s?.name || f.wunsch.value.trim(),
      mitarbeiter: state.person || "", mitarbeiter_name: person?.name || "",
      einwilligung: f.einwilligung.checked ? "ja" : "", website: f.website.value,
    });
    state.sending = false;
    submit.disabled = false;
    submit.textContent = label;
    if (result.kind === "ok") {
      try {
        sessionStorage.setItem("aj-termin", JSON.stringify({ ref: result.ref, datum: state.date, uhrzeit: state.time, leistung: s?.name || f.wunsch.value.trim(), dauer: s?.dauer || 0, wunsch: root.dataset.mode === "wunsch" }));
      } catch { /* ohne Speicher zeigt die Danke-Seite nur die Vorgangsnummer */ }
      location.href = thanks("termin", result.ref);
      return;
    }
    if (result.kind === "invalid") {
      const errs = result.errors;
      if (errs.uhrzeit || errs.datum) {
        // Jemand war schneller (oder der Tag ist inzwischen gesperrt): Zeiten neu laden
        state.time = null;
        state.avail = null;
        showStep(2);
        slotError.textContent = `${errs.uhrzeit || errs.datum} Bitte wählen Sie eine andere Uhrzeit, Ihre Angaben bleiben erhalten.`;
        slotError.hidden = false;
        return;
      }
      if (errs.leistung || errs.mitarbeiter) {
        showStep(1);
        return;
      }
      const field = showFieldErrors(form, errs);
      formError.textContent = Object.values(errs).join(" ");
      formError.hidden = false;
      field?.focus();
      return;
    }
    formError.textContent = result.kind === "busy"
      ? "Gerade kommen sehr viele Anfragen an. Bitte versuchen Sie es in ein paar Minuten noch einmal."
      : "Die Buchung konnte nicht gesendet werden.";
    formError.hidden = false;
    if (result.kind === "offline") fallback.hidden = false;
  }
}
})();
