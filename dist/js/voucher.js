// Gutschein online kaufen (PayPal)
(function () {
"use strict";

// Demo nur auf Vorschau-Adressen oder per Doppelklick (siehe main.js)
const demoAllowed = () => location.protocol === "file:" || /\.vorschau\.markentrix\.de$|\.localhost$/.test(location.hostname);

const $ = (s, r = document) => r.querySelector(s);
const shop = $("[data-voucher-shop]");
const form = $("[data-voucher-form]", shop);
const err = $("[data-voucher-error]", shop);
const payBox = $("[data-voucher-paypal]", shop);
const payStart = $("[data-voucher-pay]", shop);
const customWrap = $("[data-custom-amount]", shop);
const MIN = +shop.dataset.min, MAX = +shop.dataset.max;

// Statisch gebaute Seite: PayPal-Status live vom Server holen
let demo = false;
const enableDemo = () => {
  if (!demoAllowed()) return;
  demo = true;
  $("[data-voucher-submit]", shop).hidden = false;
  $("[data-voucher-submit]", shop).textContent = "Demo: Gutschein ausstellen";
  $("[data-voucher-unavailable]", shop).hidden = true;
};
fetch("/api/booking-config.php", { cache: "no-store" })
  .then((r) => (r.ok ? r.json() : null))
  .then((d) => {
    if (!d) return enableDemo();
    shop.dataset.paypal = d.paypalClientId || "";
    $("[data-voucher-submit]", shop).hidden = !d.paypalClientId;
    $("[data-voucher-unavailable]", shop).hidden = Boolean(d.paypalClientId);
  })
  .catch(enableDemo);
const euro = (n) => new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", minimumFractionDigits: 0 }).format(n);

function amount() {
  const choice = form.querySelector('input[name="amount"]:checked')?.value;
  const n = choice === "custom" ? Number(form.custom.value) : Number(choice);
  return Number.isInteger(n) && n >= MIN && n <= MAX ? n : null;
}

function updatePreview() {
  customWrap.hidden = form.querySelector('input[name="amount"]:checked')?.value !== "custom";
  const a = amount();
  $("[data-preview-amount]").textContent = a ? euro(a) : "– €";
  const r = form.recipient.value.trim();
  $("[data-preview-for]").textContent = r ? `für ${r}` : "";
}
form.addEventListener("input", updatePreview);
form.addEventListener("change", updatePreview);
updatePreview();

function showError(msg, el) {
  err.textContent = msg;
  err.hidden = !msg;
  if (el) el.focus();
}

function validate() {
  const checks = [
    [form.custom, amount() !== null, `Bitte einen ganzen Betrag zwischen ${MIN} und ${MAX} € wählen.`],
    [form.buyerName, form.buyerName.value.trim().length >= 2, "Bitte geben Sie Ihren Namen an."],
    [form.buyerEmail, form.buyerEmail.checkValidity() && form.buyerEmail.value.includes("."), "Bitte geben Sie eine gültige E-Mail-Adresse an."],
    [form.consent, form.consent.checked, "Bitte stimmen Sie der Datenverarbeitung zu."],
  ];
  checks.forEach(([el, ok]) => el.setAttribute("aria-invalid", String(!ok)));
  const failed = checks.find(([, ok]) => !ok);
  showError(failed ? failed[2] : "", failed?.[0]);
  return !failed;
}

function lock(locked) {
  form.querySelectorAll("input, textarea").forEach((el) => (el.disabled = locked));
  payBox.hidden = !locked;
  payStart.hidden = locked;
}

let sdk, rendered = false, orderAmount = null;
function loadPayPal() {
  sdk ??= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(shop.dataset.paypal)}&currency=EUR&intent=capture&locale=de_DE&components=buttons&disable-funding=credit,card`;
    s.onload = () => resolve(window.paypal);
    s.onerror = () => { sdk = null; reject(new Error("PayPal konnte nicht geladen werden.")); };
    document.head.append(s);
  });
  return sdk;
}

const post = async (url, body) => {
  const res = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.");
  return data;
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (demo) {
    if (validate()) done({ amount: amount(), code: "AJ-DEMO-2026", mailed: false, demo: true });
    return;
  }
  if (!shop.dataset.paypal || !validate()) return;
  $("[data-voucher-sum]").textContent = euro(amount());
  lock(true);
  if (rendered) return;
  const box = $("[data-voucher-buttons]");
  try {
    const paypal = await loadPayPal();
    await paypal.Buttons({
      style: { layout: "vertical", color: "gold", shape: "pill", label: "pay", height: 48 },
      createOrder: async () => {
        showError("");
        orderAmount = amount();
        return (await post("/api/voucher-order.php", { amount: orderAmount })).id;
      },
      onApprove: async ({ orderID }) => {
        box.style.opacity = ".4";
        try {
          const { voucher } = await post("/api/voucher.php", {
            orderId: orderID, amount: orderAmount,
            buyerName: form.buyerName.value, buyerEmail: form.buyerEmail.value,
            recipient: form.recipient.value, message: form.message.value, consent: form.consent.checked,
          });
          done(voucher);
        } catch (ex) {
          showError(ex.message);
        } finally {
          box.style.opacity = "";
        }
      },
      onCancel: () => showError("Zahlung abgebrochen – es wurde nichts abgebucht."),
      onError: (ex) => showError(ex?.message || "Bei PayPal ist ein Fehler aufgetreten. Bitte erneut versuchen."),
    }).render(box);
    rendered = true;
  } catch (ex) {
    showError(ex.message);
    lock(false);
  }
});

$("[data-voucher-edit]").addEventListener("click", () => lock(false));

function done(v) {
  form.hidden = true;
  const box = $("[data-voucher-done]");
  $("[data-done-amount]", box).textContent = euro(v.amount);
  $("[data-done-code]", box).textContent = v.code;
  $("[data-done-mail]", box).textContent = v.mailed
    ? `Der Gutschein ist als PDF an ${form.buyerEmail.value} unterwegs.`
    : "Die E-Mail konnte gerade nicht verschickt werden. Bitte speichern Sie den Gutschein jetzt als PDF.";
  $("[data-done-pdf]", box).href = v.pdf || "#";
  $("[data-done-pdf]", box).hidden = Boolean(v.demo);
  if (v.demo) $("[data-done-mail]", box).textContent = "Demo-Vorschau: In der echten Version kommt der Gutschein jetzt als PDF per E-Mail.";
  box.hidden = false;
  box.focus();
}
})();
