// AJ Atelier – Navigation, Öffnungsstatus und Online-Terminbuchung

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

// ---------- Daten ----------
const dataEl = $("#booking-data");
const DATA = dataEl ? JSON.parse(dataEl.textContent) : null;

// ---------- „Jetzt geöffnet“ ----------
if (DATA) {
  const now = berlinNow();
  const toMin = (t) => +t.slice(0, 2) * 60 + +t.slice(3);
  const today = DATA.hours[now.day];
  const holiday = DATA.holidays.includes(now.date);
  const row = $(`.hours tr[data-day="${now.day}"]`);
  row?.classList.add("is-today");
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

// ---------- Buchung ----------
const root = $("[data-booking]");
if (root && DATA) initBooking(root, DATA);

function initBooking(root, DATA) {
  const services = Object.fromEntries(DATA.categories.flatMap((c) => c.services.map((s) => [s.id, s])));
  // Die Seite ist statisch gebaut: buchbare Tage und PayPal-Status live nachladen
  const fresh = fetch("/api/booking-config.php", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => { if (d?.days) Object.assign(DATA, d); })
    .catch(() => {});
  const state = { selected: [], date: null, time: null, step: 1, slotCache: new Map(), paypalRendered: false };

  const summary = () => {
    const items = state.selected.map((id) => services[id]);
    return {
      items,
      duration: items.reduce((n, s) => n + s.duration, 0),
      price: items.reduce((n, s) => n + s.price, 0),
      hasFrom: items.some((s) => s.from || s.consult),
      payNow: items.reduce((n, s) => n + s.payNow, 0),
    };
  };
  const key = () => `${state.selected.slice().sort().join(",")}|${state.date}`;

  // Schritte
  const stepsBar = $(".steps", root);
  function showStep(step) {
    const back = typeof step === "number" && typeof state.step === "number" && step < state.step;
    state.step = step;
    $$("[data-step]", root).forEach((el) => (el.hidden = el.dataset.step !== String(step)));
    stepsBar.style.setProperty("--progress", step === "done" ? "100%" : `${step * 25}%`);
    const entering = $(`[data-step="${step}"]`, root);
    const cls = back ? "is-leaving-back" : "is-entering";
    entering.classList.remove("is-entering", "is-leaving-back");
    void entering.offsetWidth; // Animation neu starten
    entering.classList.add(cls);
    entering.addEventListener("animationend", () => entering.classList.remove(cls), { once: true });
    $$("[data-step-label]", root).forEach((li) => {
      const n = +li.dataset.stepLabel;
      li.classList.toggle("is-active", n === step);
      li.classList.toggle("is-done", step === "done" || n < step);
    });
    const target = $(`[data-step="${step}"]`, root);
    const top = root.getBoundingClientRect().top;
    if (top < 0 || top > innerHeight * 0.6) root.scrollIntoView({ behavior: "smooth", block: "start" });
    target.querySelector("h3")?.setAttribute("tabindex", "-1");
    target.querySelector("h3")?.focus({ preventScroll: true });
    if (step === 2) renderDates();
    if (step === 4) fresh.then(preparePayment);
  }
  $$("[data-back]", root).forEach((b) => b.addEventListener("click", () => showStep(state.step - 1)));

  // Zusammenfassung
  function renderSummary() {
    const s = summary();
    const list = $("[data-summary-list]", root);
    list.innerHTML = "";
    if (!s.items.length) list.innerHTML = '<li class="muted">Noch keine Leistung gewählt</li>';
    s.items.forEach((it) => {
      const li = document.createElement("li");
      li.innerHTML = `<span></span><strong></strong>`;
      li.firstChild.textContent = it.name;
      li.lastChild.textContent = it.consult ? "Beratung" : `${it.from ? "ab " : ""}${euro(it.price)}`;
      list.append(li);
    });
    $("[data-summary-duration]", root).textContent = s.items.length ? `ca. ${duration(s.duration)}` : "–";
    $("[data-summary-price]", root).textContent = s.items.length ? `${s.hasFrom ? "ab " : ""}${euro(s.price)}` : "–";
    $("[data-summary-date]", root).textContent = state.date && state.time ? `${new Date(`${state.date}T12:00`).toLocaleDateString("de-DE", { weekday: "short", day: "2-digit", month: "2-digit" })}, ${state.time} Uhr` : "–";
    $("[data-summary-hint]", root).hidden = !s.hasFrom;
  }

  // Schritt 1: Leistungen
  const picker = $("[data-service-picker]", root);
  const pickerHint = document.createElement("p");
  pickerHint.className = "form-error";
  pickerHint.setAttribute("role", "alert");
  pickerHint.hidden = true;
  picker.after(pickerHint);
  // Die Liste kommt fertig vom Server; nur falls sie fehlt, hier aufbauen
  if (!picker.children.length) DATA.categories.forEach((cat, i) => {
    const det = document.createElement("details");
    det.className = "service-cat";
    det.open = i === 0;
    det.innerHTML = `<summary><span></span><span class="count" hidden></span></summary><div class="service-options"></div>`;
    det.querySelector("summary span").textContent = cat.title;
    const box = det.querySelector(".service-options");
    cat.services.forEach((s) => {
      const label = document.createElement("label");
      label.className = "service-option";
      label.innerHTML = `<input type="checkbox" value="${s.id}"><span><span class="n"></span><small></small></span><span class="price"></span>`;
      label.querySelector(".n").textContent = s.name;
      label.querySelector("small").textContent = `ca. ${duration(s.duration)}`;
      label.querySelector(".price").textContent = s.consult ? "nach Beratung" : `${s.from ? "ab " : ""}${euro(s.price)}`;
      box.append(label);
    });
    picker.append(det);
  });
  picker.addEventListener("change", (e) => {
    const cb = e.target;
    if (cb.checked && state.selected.length >= DATA.maxServices) {
      cb.checked = false;
      pickerHint.textContent = `Bitte maximal ${DATA.maxServices} Leistungen pro Termin wählen.`;
      pickerHint.hidden = false;
      return;
    }
    pickerHint.hidden = true;
    state.selected = $$("input:checked", picker).map((i) => i.value);
    state.time = null;
    $$(".service-cat", picker).forEach((det) => {
      const n = $$("input:checked", det).length;
      const badge = det.querySelector(".count");
      badge.hidden = !n;
      badge.textContent = n;
    });
    $('[data-step="1"] [data-next]', root).disabled = !state.selected.length;
    renderSummary();
  });
  $('[data-step="1"] [data-next]', root).addEventListener("click", () => showStep(2));

  // Schritt 2: Datum & Uhrzeit
  const strip = $("[data-date-strip]", root);
  const slotsEl = $("[data-slots]", root);
  const slotNotice = document.createElement("p");
  slotNotice.className = "form-error";
  slotNotice.setAttribute("role", "alert");
  slotNotice.hidden = true;
  slotsEl.before(slotNotice);
  const next2 = $('[data-step="2"] [data-next]', root);
  async function renderDates() {
    await fresh;
    if (!strip.children.length) {
      DATA.days.forEach((d) => {
        const dt = new Date(`${d.date}T12:00`);
        const b = document.createElement("button");
        b.type = "button";
        b.className = "date-btn";
        b.dataset.date = d.date;
        b.disabled = !d.open;
        b.setAttribute("aria-pressed", "false");
        b.setAttribute("aria-label", longDate(d.date) + (d.open ? "" : " – geschlossen"));
        b.innerHTML = `<span>${dt.toLocaleDateString("de-DE", { weekday: "short" })}</span><strong>${dt.getDate()}</strong><span>${dt.toLocaleDateString("de-DE", { month: "short" })}</span>`;
        strip.append(b);
      });
    }
    if (!state.date) state.date = DATA.days.find((d) => d.open)?.date;
    selectDate(state.date, true);
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
    const k = key();
    try {
      let slots = state.slotCache.get(k);
      if (!slots) {
        const res = await fetch(`/api/availability.php?date=${date}&services=${encodeURIComponent(state.selected.join(","))}`);
        if (!res.ok) throw new Error();
        slots = (await res.json()).slots;
        state.slotCache.set(k, slots);
      }
      if (key() !== k) return;
      renderSlots(slots);
    } catch {
      slotsEl.innerHTML = '<p class="empty">Freie Zeiten konnten nicht geladen werden. Bitte versuchen Sie es erneut oder rufen Sie uns an.</p>';
    }
  }

  function renderSlots(slots) {
    slotsEl.innerHTML = "";
    if (!slots.length) {
      slotsEl.innerHTML = `<p class="empty">An diesem Tag ist für ${duration(summary().duration)} leider nichts mehr frei. Bitte wählen Sie einen anderen Tag.</p>`;
      return;
    }
    slots.forEach((t) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "slot-btn";
      b.textContent = t;
      b.setAttribute("aria-pressed", String(t === state.time));
      b.setAttribute("aria-label", `${t} Uhr`);
      b.style.setProperty("--i", slotsEl.children.length);
      slotsEl.append(b);
    });
  }
  slotsEl.addEventListener("click", (e) => {
    const b = e.target.closest(".slot-btn");
    if (!b) return;
    state.time = b.textContent;
    slotNotice.hidden = true;
    $$(".slot-btn", slotsEl).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    next2.disabled = false;
    renderSummary();
  });
  next2.addEventListener("click", () => showStep(3));

  // Schritt 3: Kontaktdaten
  const form = $("[data-customer-form]", root);
  const formError = $("[data-form-error]", root);
  function validateForm() {
    const checks = [
      [form.name, form.name.value.trim().length >= 2, "Bitte geben Sie Ihren Namen an."],
      [form.phone, /^[+()\d\s/-]{6,25}$/.test(form.phone.value.trim()), "Bitte geben Sie eine gültige Telefonnummer an."],
      [form.email, form.email.checkValidity() && form.email.value.includes("."), "Bitte geben Sie eine gültige E-Mail-Adresse an."],
      [form.consent, form.consent.checked, "Bitte stimmen Sie der Datenverarbeitung zu."],
    ];
    checks.forEach(([el, ok]) => el.setAttribute("aria-invalid", String(!ok)));
    const failed = checks.find(([, ok]) => !ok);
    formError.hidden = !failed;
    if (failed) { formError.textContent = failed[2]; failed[0].focus(); }
    return !failed;
  }
  $('[data-step="3"] [data-next]', root).addEventListener("click", () => validateForm() && showStep(4));
  form.addEventListener("submit", (e) => { e.preventDefault(); validateForm() && showStep(4); });

  // Schritt 4: Zahlung
  const payError = $("[data-pay-error]", root);
  const ppOption = $("[data-paypal-option]", root);
  const ppBox = $("[data-paypal-box]", root);
  const onsiteBtn = $("[data-submit-onsite]", root);

  function preparePayment() {
    const s = summary();
    payError.hidden = true;
    const canPayPal = Boolean(DATA.paypalClientId) && s.payNow > 0;
    ppOption.hidden = !canPayPal;
    if (canPayPal) {
      $("[data-paypal-label]", root).textContent = s.hasFrom
        ? `Anzahlung ${euro(s.payNow)} – wird vor Ort vollständig verrechnet`
        : `Gesamtbetrag ${euro(s.payNow)} – sicher & sofort`;
    } else {
      $('input[value="onsite"]', root).checked = true;
    }
    onPaymentChange();
  }
  function onPaymentChange() {
    const paypal = $('input[name="payment"]:checked', root)?.value === "paypal";
    ppBox.hidden = !paypal;
    onsiteBtn.hidden = paypal;
    if (paypal) renderPayPal();
  }
  $$('input[name="payment"]', root).forEach((r) => r.addEventListener("change", onPaymentChange));

  const payload = (extra = {}) => ({
    services: state.selected, date: state.date, time: state.time,
    name: form.name.value, phone: form.phone.value, email: form.email.value, note: form.note.value,
    website: form.website.value, consent: form.consent.checked,
    reviewOptin: Boolean(form.reviewOptin?.checked), ...extra,
  });

  function showPayError(msg) {
    payError.textContent = msg;
    payError.hidden = false;
  }

  async function submitBooking(extra) {
    const res = await fetch("/api/booking.php", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload(extra)) });
    const data = await res.json().catch(() => ({}));
    if (res.ok) return done(data.booking);
    if (res.status === 409) {
      state.slotCache.clear();
      state.time = null;
      showStep(2);
      slotNotice.textContent = data.error || "Der Termin ist leider nicht mehr frei.";
      slotNotice.hidden = false;
      return;
    }
    showPayError(data.error || "Die Buchung konnte nicht abgeschlossen werden. Bitte rufen Sie uns an.");
  }

  onsiteBtn.addEventListener("click", async () => {
    onsiteBtn.disabled = true;
    onsiteBtn.textContent = "Wird gebucht …";
    payError.hidden = true;
    try { await submitBooking({ payment: "onsite" }); }
    catch { showPayError("Verbindungsfehler. Bitte erneut versuchen."); }
    finally { onsiteBtn.disabled = false; onsiteBtn.textContent = "Verbindlich buchen"; }
  });

  let sdkPromise;
  function loadPayPal() {
    sdkPromise ??= new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(DATA.paypalClientId)}&currency=EUR&intent=capture&locale=de_DE&components=buttons&disable-funding=credit,card`;
      s.onload = () => resolve(window.paypal);
      s.onerror = () => { sdkPromise = null; reject(new Error("PayPal konnte nicht geladen werden.")); };
      document.head.append(s);
    });
    return sdkPromise;
  }
  async function renderPayPal() {
    if (state.paypalRendered) return;
    const container = $("[data-paypal-buttons]", root);
    container.innerHTML = '<div class="loader"></div>';
    try {
      const paypal = await loadPayPal();
      container.innerHTML = "";
      await paypal.Buttons({
        style: { layout: "vertical", color: "gold", shape: "pill", label: "pay", height: 48 },
        createOrder: async () => {
          payError.hidden = true;
          const res = await fetch("/api/paypal-order.php", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ services: state.selected, date: state.date, time: state.time }) });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) { showPayError(data.error || "PayPal konnte nicht gestartet werden."); throw new Error(data.error); }
          return data.id;
        },
        onApprove: async ({ orderID }) => {
          container.style.opacity = ".4";
          try { await submitBooking({ payment: "paypal", orderId: orderID }); }
          finally { container.style.opacity = ""; }
        },
        onCancel: () => showPayError("Zahlung abgebrochen – es wurde nichts gebucht."),
        onError: () => showPayError("Bei PayPal ist ein Fehler aufgetreten. Bitte erneut versuchen oder vor Ort bezahlen."),
      }).render(container);
      state.paypalRendered = true;
    } catch (err) {
      container.innerHTML = "";
      showPayError(err.message || "PayPal ist derzeit nicht erreichbar. Bitte wählen Sie „Vor Ort bezahlen“.");
    }
  }

  // Bestätigung
  function done(b) {
    const names = b.services.map((s) => s.name).join(", ");
    $("[data-confirmation-text]", root).textContent =
      `${longDate(b.date)} um ${b.time} Uhr – ${names}.` + (b.paid ? ` Online bezahlt: ${euro(b.paid)}.` : " Zahlung vor Ort.");
    const start = `${b.date.replaceAll("-", "")}T${b.time.replace(":", "")}00`;
    const endMin = +b.time.slice(0, 2) * 60 + +b.time.slice(3) + b.duration;
    const end = `${b.date.replaceAll("-", "")}T${String(Math.floor(endMin / 60)).padStart(2, "0")}${String(endMin % 60).padStart(2, "0")}00`;
    const ics = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AJ Atelier//Termin//DE", "BEGIN:VEVENT",
      `UID:${Date.now()}@aj-atelier`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
      `DTSTART;TZID=Europe/Berlin:${start}`, `DTEND;TZID=Europe/Berlin:${end}`,
      `SUMMARY:${DATA.salon.name}: ${names.replace(/[,;]/g, "\\$&")}`, `LOCATION:${DATA.salon.address.replace(/[,;]/g, "\\$&")}`,
      "END:VEVENT", "END:VCALENDAR",
    ].join("\r\n");
    $("[data-ics]", root).href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
    showStep("done");
  }

  $("[data-restart]", root).addEventListener("click", () => {
    $$("input:checked", picker).forEach((i) => (i.checked = false));
    Object.assign(state, { selected: [], date: null, time: null, paypalRendered: false });
    state.slotCache.clear();
    $("[data-paypal-buttons]", root).innerHTML = "";
    $('[data-step="1"] [data-next]', root).disabled = true;
    $$(".service-cat .count", picker).forEach((b) => (b.hidden = true));
    renderSummary();
    showStep(1);
  });

  // Direktwahl über Links wie /termin?leistung=f-balayage
  const pre = new URLSearchParams(location.search).get("leistung")
    || new URLSearchParams(location.hash.split("?")[1] || "").get("leistung");
  if (pre && services[pre]) {
    const cb = $(`input[value="${CSS.escape(pre)}"]`, picker);
    cb.checked = true;
    cb.closest("details").open = true;
    cb.dispatchEvent(new Event("change", { bubbles: true }));
  }
}
