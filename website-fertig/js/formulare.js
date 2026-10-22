// Kontakt- und Gutscheinanfrage: senden an das Markentrix-Portal (/api/anfrage), danach danke.html
(function () {
"use strict";

const { sendAnfrage, showFieldErrors, checkRequired, thanks } = window.AJ;
const $ = (s, r = document) => r.querySelector(s);

for (const form of document.querySelectorAll("form[data-anfrage]")) {
  const typ = form.dataset.anfrage;
  const err = $("[data-form-error]", form);
  const btn = $("button[type=submit]", form);
  const fallback = form.parentElement.querySelector("[data-fallback]");
  let sending = false;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (sending) return; // Doppelklick verhindern
    err.hidden = true;
    const extra = typeof form.ajCheck === "function" ? form.ajCheck() : {};
    const first = showFieldErrors(form, checkRequired(form, extra));
    if (first) { first.focus(); return; }

    const data = { typ };
    for (const el of form.elements) {
      if (!el.name || el.disabled || el.closest("[hidden]")) continue;
      if (el.type === "checkbox") data[el.name] = el.checked ? el.value || "ja" : "";
      else if (el.type === "radio") { if (el.checked) data[el.name] = el.value; }
      else data[el.name] = el.value.trim();
    }
    if (typeof form.ajData === "function") Object.assign(data, form.ajData());

    sending = true;
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = "Wird gesendet …";
    const result = await sendAnfrage(data);
    sending = false;
    btn.disabled = false;
    btn.textContent = label;

    if (result.kind === "ok") { location.href = thanks(typ, result.ref); return; }
    if (result.kind === "invalid") {
      const field = showFieldErrors(form, result.errors);
      err.textContent = Object.values(result.errors).join(" ");
      err.hidden = false;
      field?.focus();
      return;
    }
    err.textContent = result.kind === "busy"
      ? "Gerade kommen sehr viele Anfragen an. Bitte versuchen Sie es in ein paar Minuten noch einmal."
      : "Die Nachricht konnte nicht gesendet werden. Ihre Eingaben bleiben erhalten.";
    err.hidden = false;
    if (result.kind === "offline" && fallback) fallback.hidden = false;
  });
}

// ---------- Gutschein: Betrag und Vorschaukarte ----------
const vform = $("form[data-anfrage=gutschein]");
if (vform) {
  const MIN = +vform.dataset.min, MAX = +vform.dataset.max;
  const euro = (n) => new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", minimumFractionDigits: 0 }).format(n);
  const customWrap = $("[data-custom-amount]", vform);
  const choice = () => vform.querySelector('input[name="betrag_wahl"]:checked')?.value;
  const amount = () => {
    const n = choice() === "custom" ? Number(vform.elements.betrag_eigen.value) : Number(choice());
    return Number.isInteger(n) && n >= MIN && n <= MAX ? n : null;
  };
  const update = () => {
    customWrap.hidden = choice() !== "custom";
    const a = amount();
    $("[data-preview-amount]").textContent = a ? euro(a) : "– €";
    const r = vform.elements.empfaenger.value.trim();
    $("[data-preview-for]").textContent = r ? `für ${r}` : "";
  };
  vform.addEventListener("input", update);
  vform.addEventListener("change", update);
  update();
  // Eigener Betrag außerhalb der Grenzen → Fehler am Feld
  vform.ajCheck = () => (amount() === null ? { betrag_eigen: `Bitte einen ganzen Betrag zwischen ${MIN} und ${MAX} € wählen.` } : {});
  // Das Portal bekommt nur den fertigen Betrag als Text
  vform.ajData = () => ({ betrag: `${amount()} €`, betrag_wahl: undefined, betrag_eigen: undefined });
}
})();
