// Kontaktformular
(function () {
"use strict";

// Demo nur auf Vorschau-Adressen oder per Doppelklick (siehe main.js)
const demoAllowed = () => location.protocol === "file:" || /\.vorschau\.markentrix\.de$|\.localhost$/.test(location.hostname);

const form = document.querySelector("[data-contact-form]");
const err = form?.querySelector("[data-contact-error]");
const ok = form?.querySelector("[data-contact-ok]");

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const checks = [
    [form.name, form.name.value.trim().length >= 2, "Bitte geben Sie Ihren Namen an."],
    [form.email, form.email.checkValidity() && form.email.value.includes("."), "Bitte geben Sie eine gültige E-Mail-Adresse an."],
    [form.message, form.message.value.trim().length >= 10, "Bitte schreiben Sie uns eine kurze Nachricht."],
    [form.consent, form.consent.checked, "Bitte stimmen Sie der Datenverarbeitung zu."],
  ];
  checks.forEach(([el, valid]) => el.setAttribute("aria-invalid", String(!valid)));
  const failed = checks.find(([, valid]) => !valid);
  ok.hidden = true;
  err.hidden = !failed;
  if (failed) { err.textContent = failed[2]; failed[0].focus(); return; }

  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Wird gesendet …";
  try {
    const res = await fetch("/api/contact.php", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: form.name.value, email: form.email.value, phone: form.phone.value,
        message: form.message.value, website: form.website.value, consent: form.consent.checked,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Die Nachricht konnte nicht gesendet werden. Bitte rufen Sie uns an.");
    form.reset();
    ok.hidden = false;
  } catch (ex) {
    if (demoAllowed() && !(ex instanceof Error && ex.message.startsWith("Bitte"))) {
      form.reset();
      ok.textContent = "Demo-Vorschau: Das Formular funktioniert, in der Demo wird aber nichts versendet.";
      ok.hidden = false;
      return;
    }
    err.textContent = ex.message;
    err.hidden = false;
  } finally {
    btn.disabled = false;
    btn.textContent = "Nachricht senden";
  }
});
})();
