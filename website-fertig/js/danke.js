// Danke-Seite: Text je Anfrageart, Vorgangsnummer und (bei Terminen) Kalendereintrag
(function () {
"use strict";

const $ = (s) => document.querySelector(s);
const p = new URLSearchParams(location.search);
let saved = {};
try { saved = JSON.parse(sessionStorage.getItem("aj-anfrage") || "{}") || {}; } catch { /* ohne Speicher */ }
const typ = p.get("typ") || saved.typ || "kontakt";
const ref = (p.get("ref") || saved.ref || "").replace(/[^\w-]/g, "").slice(0, 40);
const longDate = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString("de-DE", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

let termin = null;
try { termin = JSON.parse(sessionStorage.getItem("aj-termin") || "null"); } catch { /* ohne Speicher */ }
if (termin && termin.ref !== ref) termin = null;

const texts = {
  termin: termin?.wunsch
    ? ["Ihr Terminwunsch ist da!", "Wir prüfen den Termin und bestätigen ihn Ihnen so schnell wie möglich per E-Mail."]
    : ["Ihr Termin ist gebucht!", "Die Bestätigung mit allen Details ist unterwegs in Ihr Postfach. Einen Tag vorher erinnern wir Sie noch einmal."],
  gutschein: ["Vielen Dank für Ihre Gutschein-Anfrage!", "Sie erhalten von uns per E-Mail den Link zur Zahlung mit PayPal. Nach Zahlungseingang schicken wir Ihnen den Gutschein mit persönlichem Code."],
  kontakt: ["Vielen Dank für Ihre Nachricht!", "Ihre Nachricht ist bei uns angekommen. Wir melden uns so schnell wie möglich, eine Eingangsbestätigung ist unterwegs in Ihr Postfach."],
};
const [title, text] = texts[typ] || texts.kontakt;
$("[data-thanks-title]").textContent = title;
$("[data-thanks-text]").textContent = termin
  ? `${termin.leistung ? `${termin.leistung} am ` : "Am "}${longDate(termin.datum)} um ${termin.uhrzeit} Uhr. ${text}`
  : text;
if (ref) {
  const el = $("[data-thanks-ref]");
  el.textContent = `Ihre Vorgangsnummer: ${ref}`;
  el.hidden = false;
}

// Kalendereintrag (nur für gebuchte Termine mit bekannter Uhrzeit)
if (termin && !termin.wunsch && /^\d{4}-\d{2}-\d{2}$/.test(termin.datum) && /^\d{2}:\d{2}$/.test(termin.uhrzeit)) {
  const pad = (n) => String(n).padStart(2, "0");
  const startMin = +termin.uhrzeit.slice(0, 2) * 60 + +termin.uhrzeit.slice(3);
  const endMin = startMin + (+termin.dauer || 60);
  const day = termin.datum.replaceAll("-", "");
  const esc = (t) => String(t).replace(/[\\,;]/g, "\\$&").replace(/\n/g, " ");
  const ics = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AJ Atelier//Termin//DE", "BEGIN:VEVENT",
    `UID:${ref || Date.now()}@aj-atelier`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
    `DTSTART;TZID=Europe/Berlin:${day}T${pad(Math.floor(startMin / 60))}${pad(startMin % 60)}00`,
    `DTEND;TZID=Europe/Berlin:${day}T${pad(Math.floor(endMin / 60))}${pad(endMin % 60)}00`,
    `SUMMARY:${esc(`AJ Atelier: ${termin.leistung || "Friseurtermin"}`)}`,
    `LOCATION:${esc("AJ Atelier, Hauptstraße 64, 30938 Burgwedel-Wettmar")}`,
    "END:VEVENT", "END:VCALENDAR",
  ].join("\r\n");
  const a = $("[data-ics]");
  a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
  a.hidden = false;
}
})();
