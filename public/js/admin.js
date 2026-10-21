// Terminverwaltung für den Salon

const $ = (s, r = document) => r.querySelector(s);
const API = "/api/admin.php";
let csrf = "";

const euro = (n) => new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(n);
const addDays = (iso, n) => { const d = new Date(`${iso}T12:00`); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const todayIso = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

async function api(path = "", opts = {}) {
  const res = await fetch(API + path, { ...opts, headers: { "content-type": "application/json", "x-csrf-token": csrf, ...(opts.headers || {}) } });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) { showLogin(); throw new Error(data.error); }
  if (!res.ok) throw new Error(data.error || "Fehler");
  if (data.csrf) csrf = data.csrf;
  return data;
}

const login = $("[data-login]");
const app = $("[data-app]");
const logoutBtn = $("[data-logout]");
const fromInput = $("[data-from]");
const showCancelled = $("[data-show-cancelled]");

function showLogin() { if (login) { login.hidden = false; app.hidden = true; logoutBtn.hidden = true; } }

login?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("[data-login-error]");
  try {
    await api("?action=login", { method: "POST", body: JSON.stringify({ password: login.password.value }) });
    login.hidden = true; app.hidden = false; logoutBtn.hidden = false; err.hidden = true;
    login.reset();
    load();
  } catch (ex) { err.textContent = ex.message; err.hidden = false; }
});
logoutBtn?.addEventListener("click", async () => { await api("?action=logout"); showLogin(); });

async function load() {
  const from = fromInput.value || todayIso();
  const { entries } = await api(`?from=${from}&days=7`);
  const days = $("[data-days]");
  days.innerHTML = "";
  let count = 0, revenue = 0, paid = 0;
  for (let i = 0; i < 7; i++) {
    const date = addDays(from, i);
    const list = entries.filter((e) => e.date === date && (showCancelled.checked || e.status !== "cancelled"));
    const label = new Date(`${date}T12:00`).toLocaleDateString("de-DE", { weekday: "long", day: "numeric", month: "long" });
    const box = document.createElement("section");
    box.className = "card day";
    const active = list.filter((e) => e.type === "booking" && e.status !== "cancelled");
    count += active.length;
    revenue += active.reduce((n, e) => n + Number(e.price_estimate), 0);
    paid += active.reduce((n, e) => n + (e.refunded ? 0 : Number(e.pay_amount)), 0);
    box.innerHTML = `<h2>${esc(label)} <small>${active.length} Termin${active.length === 1 ? "" : "e"}</small></h2>` +
      (list.length ? list.map(renderEntry).join("") : '<p class="muted">Keine Einträge</p>');
    days.append(box);
  }
  $("[data-stats]").textContent = `${count} Termine · ca. ${euro(revenue)} Umsatz · ${euro(paid)} per PayPal bezahlt`;
}

function renderEntry(e) {
  const [h, m] = e.time.split(":").map(Number);
  const endMin = h * 60 + m + Number(e.duration);
  const end = `${String(Math.floor(endMin / 60)).padStart(2, "0")}:${String(endMin % 60).padStart(2, "0")}`;
  const cls = `entry${e.type === "block" ? " is-block" : ""}${e.status === "cancelled" ? " is-cancelled" : ""}`;
  if (e.type === "block") {
    return `<div class="${cls}"><div class="time">${e.time}<small>bis ${end}</small></div>
      <div><div class="who">Blockiert${e.name ? ` – ${esc(e.name)}` : ""}</div><div class="meta">${esc(e.note)}</div></div>
      <div class="actions"><button class="link-btn" data-del="${e.id}">Freigeben</button></div></div>`;
  }
  const services = e.services.map((s) => esc(s.name)).join(", ");
  const pay = Number(e.pay_amount) > 0
    ? `<span class="tag paid">${e.refunded ? "erstattet" : `PayPal ${euro(Number(e.pay_amount))}`}</span>`
    : '<span class="tag">vor Ort</span>';
  const status = e.status === "cancelled" ? `<span class="tag">storniert (${e.cancelled_by === "customer" ? "Kund:in" : "Salon"})</span>` : "";
  return `<div class="${cls}"><div class="time">${e.time}<small>bis ${end}</small></div>
    <div><div class="who">${esc(e.name)} ${pay}${status}</div>
      <div class="meta">${services}</div>
      <div class="meta"><a href="tel:${esc(e.phone)}">${esc(e.phone)}</a> · <a href="mailto:${esc(e.email)}">${esc(e.email)}</a></div>
      ${e.note ? `<div class="meta">„${esc(e.note)}“</div>` : ""}</div>
    <div class="actions">${e.status !== "cancelled" ? `<button class="link-btn" data-cancel="${e.id}" data-paid="${Number(e.pay_amount) > 0 && !e.refunded ? 1 : 0}">Absagen</button>` : ""}</div></div>`;
}

$("[data-days]")?.addEventListener("click", async (ev) => {
  const del = ev.target.closest("[data-del]");
  const cancel = ev.target.closest("[data-cancel]");
  try {
    if (del && confirm("Blockierung entfernen?")) {
      await api(`?id=${encodeURIComponent(del.dataset.del)}`, { method: "DELETE" });
      load();
    }
    if (cancel && confirm("Termin wirklich absagen?")) {
      const refund = cancel.dataset.paid === "1" && confirm("PayPal-Zahlung erstatten?");
      const notify = confirm("Kund:in per E-Mail informieren?");
      await api(`?id=${encodeURIComponent(cancel.dataset.cancel)}&refund=${refund ? 1 : 0}&notify=${notify ? 1 : 0}`, { method: "DELETE" });
      load();
    }
  } catch (ex) { alert(ex.message); }
});

$("[data-block]")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  try {
    await api("", { method: "POST", body: JSON.stringify({ date: f.date.value, time: f.time.value, duration: Number(f.duration.value), name: f.name.value, note: f.note.value }) });
    f.reset();
    load();
  } catch (ex) { alert(ex.message); }
});

$("[data-prev]")?.addEventListener("click", () => { fromInput.value = addDays(fromInput.value, -7); load(); });
$("[data-next]")?.addEventListener("click", () => { fromInput.value = addDays(fromInput.value, 7); load(); });
$("[data-today]")?.addEventListener("click", () => { fromInput.value = todayIso(); load(); });
fromInput?.addEventListener("change", load);
showCancelled?.addEventListener("change", load);

if (app && !app.hidden) load().catch(() => {});

// ---------- Tabs ----------
document.querySelectorAll("[data-tab]").forEach((tab) => tab.addEventListener("click", () => {
  document.querySelectorAll("[data-tab]").forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
  document.querySelectorAll("[data-panel]").forEach((p) => (p.hidden = p.dataset.panel !== tab.dataset.tab));
  if (tab.dataset.tab === "gutscheine") loadVouchers();
}));

// ---------- Gutscheine ----------
const vSearch = $("[data-voucher-search]");
const vList = $("[data-vouchers]");
const dateDe = (iso) => new Date(iso.length === 10 ? `${iso}T12:00` : iso).toLocaleDateString("de-DE");

async function loadVouchers() {
  const q = vSearch.q.value.trim();
  const { vouchers } = await api(`?action=vouchers&q=${encodeURIComponent(q)}`);
  vList.innerHTML = vouchers.length ? "" : '<p class="card muted">Keine Gutscheine gefunden.</p>';
  for (const v of vouchers) {
    const box = document.createElement("section");
    box.className = "card voucher-admin";
    const state = v.status === "redeemed" ? "eingelöst" : v.expired ? "abgelaufen" : "aktiv";
    box.innerHTML = `<div class="entry">
      <div class="time">${euro(Number(v.balance))}<small>von ${euro(Number(v.amount))}</small></div>
      <div><div class="who">${esc(v.code)} <span class="tag ${state === "aktiv" ? "paid" : ""}">${state}</span></div>
        <div class="meta">Gekauft am ${dateDe(v.created_at)} von ${esc(v.buyer_name)} (<a href="mailto:${esc(v.buyer_email)}">${esc(v.buyer_email)}</a>)${v.recipient ? ` · für ${esc(v.recipient)}` : ""}</div>
        <div class="meta">Gültig bis ${dateDe(v.valid_until)}</div>
        ${v.redemptions.map((r) => `<div class="meta">Eingelöst am ${dateDe(r.created_at)}: ${euro(Number(r.amount))}${r.note ? ` (${esc(r.note)})` : ""}</div>`).join("")}
      </div>
      <div class="actions"><button class="link-btn" data-resend="${esc(v.code)}">PDF erneut senden</button></div>
    </div>
    ${v.status === "active" ? `<form class="redeem-form" data-redeem="${esc(v.code)}">
      <label>Betrag einlösen (€)<input name="amount" type="number" min="0.01" step="0.01" max="${Number(v.balance)}" required></label>
      <label>Notiz<input name="note" maxlength="120" placeholder="z. B. Balayage"></label>
      <button class="btn btn-gold btn-sm" type="submit">Einlösen</button>
      <p class="form-msg" role="status"></p>
    </form>` : ""}`;
    vList.append(box);
  }
}

vSearch?.addEventListener("submit", (e) => { e.preventDefault(); loadVouchers().catch((ex) => alertBox(ex.message)); });

vList?.addEventListener("submit", async (e) => {
  const f = e.target.closest("[data-redeem]");
  if (!f) return;
  e.preventDefault();
  const msg = f.querySelector(".form-msg");
  try {
    const { balance } = await api("?action=redeem", { method: "POST", body: JSON.stringify({ code: f.dataset.redeem, amount: Number(f.amount.value), note: f.note.value }) });
    msg.textContent = `Eingelöst. Restguthaben: ${euro(balance)}`;
    setTimeout(() => loadVouchers(), 1200);
  } catch (ex) { msg.textContent = ex.message; }
});

vList?.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-resend]");
  if (!b) return;
  b.disabled = true;
  try {
    const { ok } = await api("?action=resend", { method: "POST", body: JSON.stringify({ code: b.dataset.resend }) });
    b.textContent = ok ? "Gesendet ✓" : "Versand fehlgeschlagen";
  } catch (ex) { b.textContent = ex.message; }
});

function alertBox(msg) { vList.innerHTML = `<p class="card form-error">${esc(msg)}</p>`; }
