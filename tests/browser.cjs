// Browser-Test der fertigen Website gegen den Portal-Nachbau (tests/mock-portal.php).
//   php tools/build.php && NODE_PATH=<Ordner mit playwright> node tests/browser.cjs
// Prüft Buchung, Doppelbuchung, Kontakt, Gutschein, Ausfall des Portals, Terminwunsch-Modus,
// Doppelklick-Vorschau (file://) und 390 px Breite ohne seitliches Scrollen.
"use strict";

const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const root = path.resolve(__dirname, "..");
const out = path.join(root, "website-fertig");
const lastFile = path.join(os.tmpdir(), "aj-mock-last.json");
const stateFile = path.join(os.tmpdir(), "aj-mock-portal.json");
let passed = 0;
const failed = [];
const check = (name, ok, detail = "") => {
  if (ok) { passed++; console.log(`  ✓ ${name}`); } else { failed.push(name); console.log(`  ✗ ${name}${detail ? ` – ${detail}` : ""}`); }
};
const last = () => { try { return JSON.parse(fs.readFileSync(lastFile, "utf8")); } catch { return {}; } };

function server(port, mode) {
  const p = spawn("php", ["-S", `127.0.0.1:${port}`, path.join(root, "tests/mock-portal.php")], { env: { ...process.env, MOCK_MODE: mode }, stdio: "ignore" });
  return new Promise((r) => setTimeout(() => r(p), 600));
}

(async () => {
  for (const f of [lastFile, stateFile]) fs.rmSync(f, { force: true });
  const servers = [await server(8711, ""), await server(8712, "aus"), await server(8713, "wunsch"), await server(8714, "ohne-leistungen"), await server(8715, "freigabe")];
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  ctx.on("page", (pg) => pg.on("pageerror", (e) => errors.push(`${pg.url()}: ${e.message}`)));
  const page = await ctx.newPage();
  const B = "http://127.0.0.1:8711";

  try {
    console.log("\nTerminbuchung");
    await page.goto(`${B}/termin.html`);
    await page.waitForSelector('input[name="leistung"]');
    check("Leistungen kommen aus /api/leistungen", (await page.locator('input[name="leistung"]').count()) === 3);
    await page.locator("label.service-option", { hasText: "Föhnen" }).click();
    check("Wunschperson-Auswahl erscheint (2 Personen bieten die Leistung an)", await page.locator("[data-staff-wrap]").isVisible());
    await page.selectOption("[data-staff]", "jo");
    await page.click('[data-step="1"] [data-next]');
    await page.waitForSelector(".slot-btn");
    const blocked = await page.locator(".date-btn:disabled").count();
    check("Ruhetage und Sperrtage sind gesperrt", blocked >= 15, `${blocked} gesperrt`);
    const slotTexts = await page.locator(".slot-btn").allTextContents();
    check("Nur freie Uhrzeiten werden angeboten (11:00 belegt)", slotTexts.length === 7 && !slotTexts.includes("11:00"), slotTexts.join(","));
    await page.locator(".slot-btn").first().click();
    await page.click('[data-step="2"] [data-next]');
    await page.click("[data-submit]");
    check("Leeres Formular: Fehlertexte an den Feldern", (await page.locator('[data-error-for="name"]').textContent()).length > 0 && (await page.locator('[data-error-for="einwilligung"]').textContent()).length > 0);
    check("Leeres Formular wird nicht gesendet", !fs.existsSync(lastFile));
    await page.fill('[data-customer-form] [name="name"]', "Konflikt Test");
    await page.fill('[data-customer-form] [name="telefon"]', "0511 123456");
    await page.fill('[data-customer-form] [name="email"]', "test@example.org");
    await page.check('[data-customer-form] [name="einwilligung"]');
    await page.click("[data-submit]");
    await page.waitForSelector('[data-step="2"]:not([hidden]) [data-slot-error]:not([hidden])');
    check("Doppelbuchung (422 uhrzeit): zurück zur Zeitwahl mit Hinweis", (await page.textContent("[data-slot-error]")).includes("vergeben"));
    await page.locator(".slot-btn").nth(1).click();
    await page.click('[data-step="2"] [data-next]');
    check("Eingaben bleiben nach Fehler erhalten", (await page.inputValue('[data-customer-form] [name="email"]')) === "test@example.org");
    await page.fill('[data-customer-form] [name="name"]', "Maria Muster");
    await Promise.all([page.waitForURL(/danke/), page.click("[data-submit]")]);
    const sent = last();
    check("Anfrage typ=termin mit Leistung, Person, Datum, Uhrzeit, Einwilligung", sent.typ === "termin" && sent.leistung === "d-wsf-mittel" && sent.mitarbeiter === "jo" && /^\d{4}-\d{2}-\d{2}$/.test(sent.datum) && sent.uhrzeit === "10:30" && sent.einwilligung === "ja" && sent.website === "", JSON.stringify(sent));
    check("Weiterleitung auf danke.html?typ=termin&ref=…", /danke\.html\?typ=termin&ref=T\d{6}-AB12/.test(page.url()), page.url());
    const thanks = await page.textContent("main");
    check("Danke-Seite zeigt Vorgangsnummer, Leistung und Termin", thanks.includes("Vorgangsnummer: T") && thanks.includes("mittel am") && thanks.includes("10:30 Uhr"));
    check("Kalendereintrag wird angeboten", await page.locator("[data-ics]").isVisible());

    await page.goto(`${B}/termin.html?leistung=h-schnitt`);
    await page.waitForSelector('input[name="leistung"]');
    check("Direktwahl über ?leistung= (Link von der Leistungsseite)", await page.isChecked('input[value="h-schnitt"]'));
    check("Nur eine Person bietet Herrenschnitt an → keine Auswahl", !(await page.locator("[data-staff-wrap]").isVisible()));

    console.log("\nFarbtermin (persönliche Bestätigung)");
    await page.goto(`${B}/termin.html?leistung=f-balayage`);
    await page.waitForSelector('input[value="f-balayage"]:checked');
    await page.click('[data-step="1"] [data-next]');
    await page.waitForSelector(".slot-btn");
    check("Hinweis auf persönliche Planung und Anzahlung", await page.locator("[data-personal-note]").isVisible());
    await page.locator(".slot-btn").first().click();
    await page.click('[data-step="2"] [data-next]');
    check("Fragebogen zum Haar erscheint", await page.locator("[data-color-questions]").isVisible());
    check("Knopf heißt „Terminwunsch senden“", (await page.textContent("[data-submit]")) === "Terminwunsch senden");
    await page.fill('[data-customer-form] [name="name"]', "Lena Blond");
    await page.fill('[data-customer-form] [name="telefon"]', "0511 654321");
    await page.fill('[data-customer-form] [name="email"]', "lena@example.org");
    await page.check('[data-customer-form] [name="einwilligung"]');
    fs.rmSync(lastFile, { force: true });
    await page.click("[data-submit]");
    check("Haarlänge und Vorbehandlung sind Pflicht", (await page.textContent('[data-error-for="haarlaenge"]')).length > 0 && !fs.existsSync(lastFile));
    await page.selectOption('[name="haarlaenge"]', { index: 2 });
    await page.selectOption('[name="vorbehandlung"]', { index: 3 });
    await Promise.all([page.waitForURL(/danke/), page.click("[data-submit]")]);
    const wish = last();
    check("Ohne Portal-Freigabe: Wunschzeit statt fester Uhrzeit, Fragebogen dabei", wish.wunschzeit === "10:00" && !("uhrzeit" in wish) && wish.haarlaenge === "Schulterlang" && wish.vorbehandlung.startsWith("Blondiert") && wish.terminart.includes("persönlich"), JSON.stringify(wish));
    check("Danke-Seite: Terminwunsch mit Anzahlungs-Hinweis, ohne Kalendereintrag", (await page.textContent("main")).includes("Anzahlung") && !(await page.locator("[data-ics]").isVisible()));
    await page.goto("http://127.0.0.1:8715/termin.html?leistung=f-balayage");
    await page.waitForSelector('input[value="f-balayage"]:checked');
    await page.click('[data-step="1"] [data-next]');
    await page.waitForSelector(".slot-btn");
    check("Mit Portal-Freigabe: Anzahlungsbetrag aus dem Portal", /50\s€/.test(await page.textContent("[data-deposit-text]")));
    await page.locator(".slot-btn").first().click();
    await page.click('[data-step="2"] [data-next]');
    await page.fill('[data-customer-form] [name="name"]', "Lena Blond");
    await page.fill('[data-customer-form] [name="telefon"]', "0511 654321");
    await page.fill('[data-customer-form] [name="email"]', "lena@example.org");
    await page.selectOption('[name="haarlaenge"]', { index: 1 });
    await page.selectOption('[name="vorbehandlung"]', { index: 1 });
    await page.check('[data-customer-form] [name="einwilligung"]');
    await Promise.all([page.waitForURL(/danke/), page.click("[data-submit]")]);
    check("Mit Portal-Freigabe: Uhrzeit wird vorgemerkt (uhrzeit gesendet)", last().uhrzeit && !("wunschzeit" in last()));
    check("Danke-Seite nennt den Anzahlungsbetrag", (await page.textContent("main")).includes("50 €"));

    console.log("\nKontakt und Gutschein");
    await page.goto(`${B}/kontakt.html`);
    await page.fill("#c-name", "Max Muster");
    await page.fill("#c-email", "max@example.org");
    await page.fill("#c-message", "Habt ihr Termine für eine Brautfrisur im Juni?");
    await page.check('[data-anfrage="kontakt"] [name="einwilligung"]');
    await Promise.all([page.waitForURL(/danke/), page.click('[data-anfrage="kontakt"] button[type=submit]')]);
    check("Kontakt: typ=kontakt mit Nachricht → danke.html", last().typ === "kontakt" && last().nachricht.includes("Brautfrisur") && page.url().includes("typ=kontakt"));

    await page.goto(`${B}/gutscheine.html`);
    await page.check('input[name="betrag_wahl"][value="custom"]', { force: true });
    await page.fill("#v-custom", "5");
    await page.fill("#v-buyer", "Erika Muster");
    await page.fill("#v-email", "erika@example.org");
    await page.check('[data-anfrage="gutschein"] [name="einwilligung"]');
    await page.click('[data-anfrage="gutschein"] button[type=submit]');
    check("Gutschein: Betrag unter Minimum wird am Feld gemeldet", (await page.textContent('[data-error-for="betrag_eigen"]')).includes("zwischen"));
    await page.fill("#v-custom", "80");
    await page.fill("#v-recipient", "Oma");
    await Promise.all([page.waitForURL(/danke/), page.click('[data-anfrage="gutschein"] button[type=submit]')]);
    check("Gutschein: typ=gutschein, betrag „80 €“, Empfänger", last().typ === "gutschein" && last().betrag === "80 €" && last().empfaenger === "Oma" && !("betrag_wahl" in last()), JSON.stringify(last()));
    check("Danke-Seite erklärt die PayPal-Zahlung", (await page.textContent("main")).includes("PayPal"));

    console.log("\nPortal nicht erreichbar");
    await page.goto("http://127.0.0.1:8712/termin.html");
    await page.waitForSelector("[data-fallback]:not([hidden])");
    check("Buchung zeigt Telefon als Ausweg", await page.locator('[data-fallback] a[href^="tel:"]').first().isVisible());
    await page.goto("http://127.0.0.1:8712/kontakt.html");
    await page.fill("#c-name", "Max Muster");
    await page.fill("#c-email", "max@example.org");
    await page.fill("#c-message", "Test bei ausgefallenem Portal.");
    await page.check('[data-anfrage="kontakt"] [name="einwilligung"]');
    await page.click('[data-anfrage="kontakt"] button[type=submit]');
    await page.waitForSelector("[data-fallback]:not([hidden])");
    check("Kontakt zeigt Ausweg und behält die Eingaben", (await page.inputValue("#c-message")).includes("ausgefallenem"));

    console.log("\nTerminwunsch (Salon bestätigt selbst)");
    await page.goto("http://127.0.0.1:8713/termin.html");
    await page.waitForSelector('input[name="leistung"]');
    await page.locator("label.service-option").first().click();
    await page.click('[data-step="1"] [data-next]');
    await page.waitForSelector(".slot-btn");
    check("Knopf heißt „Terminwunsch senden“", (await page.textContent("[data-submit]")) === "Terminwunsch senden");

    console.log("\nOhne Leistungsliste im Portal");
    await page.goto("http://127.0.0.1:8714/termin.html");
    await page.waitForSelector("[data-staff-wrap]:not([hidden])");
    await page.click('[data-step="1"] [data-next]');
    await page.waitForSelector(".slot-btn");
    await page.locator(".slot-btn").first().click();
    await page.click('[data-step="2"] [data-next]');
    check("Freitextfeld „Gewünschte Leistung“ erscheint als Pflichtfeld", await page.locator("[data-wish-wrap]").isVisible());

    console.log("\nDoppelklick-Vorschau (file://)");
    await page.goto(`file://${out}/index.html`);
    await page.click('.main-nav a[href="preise.html"]');
    check("Links funktionieren ohne Server", page.url().endsWith("/preise.html") && (await page.textContent("h1")).length > 0);
    await page.goto(`file://${out}/termin.html`);
    await page.waitForSelector("[data-fallback]:not([hidden])");
    check("Ohne Portal: Ausweichmöglichkeit statt kaputtem Formular", true);
    const fontOk = await page.evaluate(async () => { await document.fonts.ready; return document.fonts.check('16px "Jost"'); });
    check("Schriften laden lokal", fontOk);

    console.log("\nMobil (390 px)");
    const m = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
    const mp = await m.newPage();
    const wide = [];
    for (const f of fs.readdirSync(out).filter((f) => f.endsWith(".html"))) {
      await mp.goto(`${B}/${f}`);
      const w = await mp.evaluate(() => document.documentElement.scrollWidth);
      if (w > 390) wide.push(`${f} (${w}px)`);
    }
    check("Keine Seite scrollt seitlich", !wide.length, wide.join(", "));
    await m.close();

    check("Keine JavaScript-Fehler", !errors.length, errors.slice(0, 3).join(" | "));
  } finally {
    await browser.close();
    servers.forEach((s) => s.kill());
  }
  console.log(failed.length ? `\n✗ ${failed.length} fehlgeschlagen, ${passed} bestanden` : `\n✓ Alle ${passed} Browser-Tests bestanden`);
  process.exit(failed.length ? 1 : 0);
})();
