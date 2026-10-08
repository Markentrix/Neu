// ---- Konfiguration ---------------------------------------------------------
// TODO: E-Mail-Adresse der Fleischerei eintragen, an die Bestellungen gehen.
// Einstellungen stehen in config.js (E-Mail, optionaler Bestell-Endpunkt).
const CFG = window.SITE_CONFIG || {};
const ORDER_EMAIL = CFG.orderEmail || "bestellung@example.de";
const ORDER_ENDPOINT = (CFG.orderEndpoint || "").trim(); // leer = Fallback ohne Server

// Öffnungszeiten: 0 = Sonntag … 6 = Samstag, Zeiten in Minuten ab Mitternacht
const m = (h, min = 0) => h * 60 + min;
const HOURS = {
  0: [],
  1: [],
  2: [[m(8), m(13)], [m(14), m(18)]],
  3: [[m(8), m(13)]],
  4: [[m(8), m(13)], [m(14), m(18)]],
  5: [[m(8), m(13)], [m(14), m(18)]],
  6: [],
};
const DAYS = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
const fmt = (x) => String(Math.floor(x / 60)).padStart(2, "0") + ":" + String(x % 60).padStart(2, "0");
const $ = (s, r = document) => r.querySelector(s);

// ---- Navigation ------------------------------------------------------------
const toggle = $(".nav-toggle");
const nav = $("#nav");
toggle.addEventListener("click", () => {
  const open = nav.classList.toggle("open");
  toggle.setAttribute("aria-expanded", open);
  toggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && nav.classList.contains("open")) {
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Menü öffnen");
    toggle.focus();
  }
});
nav.addEventListener("click", (e) => {
  if (e.target.closest("a")) {
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  }
});
$("#year").textContent = new Date().getFullYear();

// ---- Live-Status "Geöffnet / Geschlossen" ----------------------------------
function updateStatus() {
  const now = new Date();
  const day = now.getDay();
  const t = now.getHours() * 60 + now.getMinutes();
  const slots = HOURS[day];
  const dot = $("#statusDot");
  const text = $("#statusText");

  document.querySelectorAll("#hoursTable tr").forEach((tr) =>
    tr.classList.toggle("today", Number(tr.dataset.day) === day));

  $("#todayHours").textContent = slots.length
    ? slots.map(([a, b]) => `${fmt(a)}–${fmt(b)}`).join(" · ")
    : "Heute geschlossen";

  const current = slots.find(([a, b]) => t >= a && t < b);
  if (current) {
    dot.className = "dot open";
    text.textContent = `Jetzt geöffnet · bis ${fmt(current[1])} Uhr`;
    return;
  }
  dot.className = "dot closed";
  const later = slots.find(([a]) => t < a);
  if (later) {
    text.textContent = `Geschlossen · öffnet heute um ${fmt(later[0])} Uhr`;
    return;
  }
  for (let i = 1; i <= 7; i++) {
    const d = (day + i) % 7;
    if (HOURS[d].length) {
      const when = i === 1 ? "morgen" : DAYS[d];
      text.textContent = `Geschlossen · öffnet ${when} um ${fmt(HOURS[d][0][0])} Uhr`;
      return;
    }
  }
}
updateStatus();
setInterval(updateStatus, 60000);

// ---- Bestellformular -------------------------------------------------------
const form = $("#orderForm");
const itemsEl = $("#items");
const errorEl = $("#formError");

function addItem(values = {}) {
  const row = document.createElement("div");
  row.className = "item";
  row.innerHTML = `
    <input name="item" placeholder="Artikel (z. B. Schnitzel)" aria-label="Artikel" value="${values.name || ""}">
    <input name="qty" type="number" min="0" step="any" placeholder="Menge" aria-label="Menge" value="${values.qty || ""}">
    <select name="unit" aria-label="Einheit">
      <option>kg</option><option>g</option><option>Stück</option><option>Scheiben</option><option>Portionen</option>
    </select>
    <button type="button" class="rm" aria-label="Zeile entfernen">×</button>`;
  itemsEl.appendChild(row);
}
addItem();
addItem();
$("#addItem").addEventListener("click", () => addItem());
itemsEl.addEventListener("click", (e) => {
  if (e.target.classList.contains("rm") && itemsEl.children.length > 1) e.target.closest(".item").remove();
});

function setType(type) {
  const radio = form.querySelector(`input[name="type"][value="${type}"]`);
  if (radio) radio.checked = true;
  syncType();
}
function syncType() {
  const feier = form.elements.type.value === "Feier / Partyservice";
  $("#guestsField").hidden = !feier;
  $("#occasionField").hidden = !feier;
}
form.querySelectorAll('input[name="type"]').forEach((r) => r.addEventListener("change", syncType));
document.querySelectorAll("[data-type]").forEach((a) =>
  a.addEventListener("click", () => setType("Feier / Partyservice")));
syncType();

// frühestes Datum: morgen
const dateEl = form.elements.date;
const tomorrow = new Date(Date.now() + 864e5);
dateEl.min = tomorrow.toISOString().slice(0, 10);

function buildMessage() {
  const f = form.elements;
  const lines = [];
  const feier = f.type.value === "Feier / Partyservice";
  lines.push(`${feier ? "ANFRAGE FEIER / PARTYSERVICE" : "VORBESTELLUNG"}`, "");
  lines.push(`Name: ${f.name.value.trim()}`);
  lines.push(`Telefon: ${f.phone.value.trim()}`);
  if (f.email.value.trim()) lines.push(`E-Mail: ${f.email.value.trim()}`);
  const d = f.date.value ? new Date(f.date.value + "T12:00:00") : null;
  if (d) lines.push(`Wunschtermin: ${DAYS[d.getDay()]}, ${d.toLocaleDateString("de-DE")}${f.time.value ? ", " + f.time.value + " Uhr" : ""}`);
  if (feier) {
    if (f.occasion.value.trim()) lines.push(`Anlass: ${f.occasion.value.trim()}`);
    if (f.guests.value) lines.push(`Personenzahl: ${f.guests.value}`);
  }
  const items = [...itemsEl.children].map((r) => {
    const n = r.querySelector('[name="item"]').value.trim();
    const q = r.querySelector('[name="qty"]').value;
    const u = r.querySelector('[name="unit"]').value;
    return n ? `- ${q ? q + " " + u + " " : ""}${n}` : null;
  }).filter(Boolean);
  if (items.length) lines.push("", "Wunschliste:", ...items);
  if (f.notes.value.trim()) lines.push("", "Anmerkungen:", f.notes.value.trim());
  return { feier, items, text: lines.join("\n") };
}

function validate() {
  const f = form.elements;
  let ok = true;
  [f.name, f.phone, f.date].forEach((el) => {
    const bad = !el.value.trim();
    el.classList.toggle("invalid", bad);
    ok = ok && !bad;
  });
  const { feier, items } = buildMessage();
  let msg = "";
  if (!ok) msg = "Bitte Name, Telefon und Wunschtermin ausfüllen.";
  else if (!items.length && !f.notes.value.trim() && !feier) msg = "Bitte mindestens einen Artikel oder eine Anmerkung angeben.";
  else if (!f.privacy.checked) msg = "Bitte stimmen Sie der Datenschutzerklärung zu.";
  const d = f.date.value ? new Date(f.date.value + "T12:00:00") : null;
  if (!msg && d && HOURS[d.getDay()].length === 0) msg = `Am ${DAYS[d.getDay()]} ist geschlossen – bitte einen anderen Abholtag wählen (Di–Fr).`;
  errorEl.hidden = !msg;
  errorEl.textContent = msg;
  if (msg) errorEl.focus();
  return !msg;
}

// ---- Bestellung senden ------------------------------------------------------
// Ohne ORDER_ENDPOINT: fertiger Text zum Kopieren / per E-Mail (Fallback).
// Mit ORDER_ENDPOINT: JSON-POST an das Backend (siehe docs/bestellung-backend.md).
const formStart = Date.now();
const submitBtn = $("#submitBtn");
const SUBMIT_LABEL = ORDER_ENDPOINT ? "Verbindlich vorbestellen" : "Bestellung zusammenstellen";
submitBtn.textContent = SUBMIT_LABEL;
if (!ORDER_ENDPOINT) {
  const n = $("#formNote");
  if (n) n.innerHTML = "Ihre Bestellung wird als fertiger Text angezeigt. Senden Sie ihn per E-Mail an die Fleischerei oder geben Sie ihn telefonisch unter <strong>05144 2632</strong> durch. Pflichtfelder sind mit * markiert.";
}

function newRef() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  const rnd = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `KW-${String(d.getFullYear()).slice(2)}${p(d.getMonth() + 1)}${p(d.getDate())}-${rnd}`;
}

function buildPayload() {
  const f = form.elements;
  const feier = f.type.value === "Feier / Partyservice";
  return {
    ref: newRef(),
    type: feier ? "feier" : "vorbestellung",
    name: f.name.value.trim(),
    phone: f.phone.value.trim(),
    email: f.email.value.trim() || null,
    date: f.date.value,
    time: f.time.value || null,
    guests: feier && f.guests.value ? Number(f.guests.value) : null,
    occasion: feier ? f.occasion.value.trim() || null : null,
    items: [...itemsEl.children].map((r) => ({
      name: r.querySelector('[name="item"]').value.trim(),
      qty: r.querySelector('[name="qty"]').value ? Number(r.querySelector('[name="qty"]').value) : null,
      unit: r.querySelector('[name="unit"]').value,
    })).filter((i) => i.name),
    notes: f.notes.value.trim() || null,
    consent: true,
    consentAt: new Date().toISOString(),
    // Spam-Schutz: Honeypot (muss leer sein) und Ausfüllzeit in Sekunden
    hp: f.website ? f.website.value : "",
    fillSeconds: Math.round((Date.now() - formStart) / 1000),
  };
}

function showFallback(text, subject) {
  $("#resultText").textContent = text;
  $("#mailShow").textContent = ORDER_EMAIL;
  $("#mailLink").href = `mailto:${ORDER_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`;
  $("#result").hidden = false;
  $("#result").focus();
  $("#result").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showSuccess(ref) {
  $("#refShow").textContent = ref;
  $("#success").hidden = false;
  $("#result").hidden = true;
  form.hidden = true;
  $("#success").focus();
  $("#success").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!validate()) return;
  const { feier, text } = buildMessage();
  const subject = `${feier ? "Feier-Anfrage" : "Vorbestellung"} – ${form.elements.name.value.trim()}`;

  if (!ORDER_ENDPOINT) { showFallback(text, subject); return; }

  const payload = buildPayload();
  if (payload.hp) return; // Bot: stillschweigend verwerfen
  submitBtn.disabled = true;
  submitBtn.textContent = "Wird gesendet …";
  errorEl.hidden = true;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 15000);
    const res = await fetch(ORDER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    clearTimeout(t);
    if (!res.ok) throw new Error("HTTP " + res.status);
    let ref = payload.ref;
    try { ref = (await res.json()).ref || ref; } catch {}
    showSuccess(ref);
  } catch {
    errorEl.textContent = "Die Bestellung konnte nicht gesendet werden. Bitte versuchen Sie es erneut oder nutzen Sie den Text unten bzw. rufen Sie an: 05144 2632.";
    errorEl.hidden = false;
    errorEl.focus();
    showFallback(text, subject);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = SUBMIT_LABEL;
  }
});

$("#newOrder").addEventListener("click", () => {
  form.reset();
  syncType();
  itemsEl.innerHTML = "";
  addItem(); addItem();
  form.hidden = false;
  $("#success").hidden = true;
  form.scrollIntoView({ behavior: "smooth", block: "start" });
});

$("#copyBtn").addEventListener("click", async () => {
  const btn = $("#copyBtn");
  try {
    await navigator.clipboard.writeText($("#resultText").textContent);
    btn.textContent = "Kopiert ✓";
  } catch {
    const r = document.createRange();
    r.selectNodeContents($("#resultText"));
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    btn.textContent = "Text markiert – jetzt kopieren";
  }
  setTimeout(() => (btn.textContent = "Text kopieren"), 2500);
});
