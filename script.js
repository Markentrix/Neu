// ---- Konfiguration ---------------------------------------------------------
// TODO: E-Mail-Adresse der Fleischerei eintragen, an die Bestellungen gehen.
const ORDER_EMAIL = "bestellung@example.de";

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
  return !msg;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  if (!validate()) return;
  const { feier, text } = buildMessage();
  const subject = `${feier ? "Feier-Anfrage" : "Vorbestellung"} – ${form.elements.name.value.trim()}`;
  location.href = `mailto:${ORDER_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`;
});

$("#copyBtn").addEventListener("click", async () => {
  if (!validate()) return;
  const btn = $("#copyBtn");
  try {
    await navigator.clipboard.writeText(buildMessage().text);
    btn.textContent = "Kopiert ✓";
  } catch {
    btn.textContent = "Kopieren nicht möglich";
  }
  setTimeout(() => (btn.textContent = "Text kopieren"), 2500);
});
