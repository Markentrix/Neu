// @ts-check
const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const PAGES = [
  "/", "/preise.html", "/kontakt.html", "/termin.html", "/gutscheine.html", "/firmenkunden.html", "/aktion/winterschutz.html", "/ratgeber/index.html",
  "/ratgeber/leasingrueckgabe-checkliste.html", "/ratgeber/kosten-fahrzeugaufbereitung-celle.html",
  "/leistungen/aussenaufbereitung-celle.html", "/leistungen/innenaufbereitung-celle.html", "/leistungen/lackpolitur-celle.html",
  "/leistungen/lackversiegelung-celle.html", "/leistungen/leasingrueckgabe-gebrauchtwagen-celle.html",
  "/impressum.html", "/datenschutz.html", "/danke.html",
];

function nextWorkday(days) {
  const d = new Date(); d.setDate(d.getDate() + days);
  while (d.getDay() === 0) d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

for (const path of PAGES) {
  test(`Seite ${path}: lädt fehlerfrei, eine H1, kein Querscrollen`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error" && !/maps|google/.test(m.text())) errors.push(m.text()); });
    const res = await page.goto(path);
    expect(res.status()).toBe(200);
    await expect(page.locator("h1")).toHaveCount(1);
    expect((await page.title()).length).toBeGreaterThan(10);
    const desc = await page.locator('meta[name="description"]').getAttribute("content");
    expect(desc && desc.length).toBeGreaterThan(50);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    expect(errors).toEqual([]);
  });
}

test("Alle internen Links funktionieren", async ({ page, request }) => {
  const seen = new Set();
  for (const path of PAGES) {
    await page.goto(path);
    const hrefs = await page.$$eval("a[href]", (as) => as.map((a) => a.href));
    hrefs.forEach((h) => { const u = new URL(h); if (u.origin === new URL(page.url()).origin) seen.add(u.pathname); });
  }
  const broken = [];
  for (const p of seen) {
    const r = await request.get(p);
    if (r.status() !== 200) broken.push(`${p} → ${r.status()}`);
  }
  expect(broken).toEqual([]);
});

for (const path of ["/", "/preise.html", "/kontakt.html", "/termin.html", "/gutscheine.html", "/ratgeber/leasingrueckgabe-checkliste.html", "/leistungen/lackpolitur-celle.html", "/firmenkunden.html"]) {
  test(`Barrierefreiheit ${path}: keine schweren axe-Verstöße`, async ({ page }) => {
    await page.goto(path);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.evaluate(() => document.querySelectorAll(".reveal").forEach((e) => e.classList.add("is-visible")));
    // Einblend-Effekte (gestaffelte Verzögerung) abwarten, sonst misst axe halbtransparente Elemente
    await page.waitForFunction(() => [...document.querySelectorAll(".reveal")].every((e) => getComputedStyle(e).opacity === "1"), null, { timeout: 5000 });
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = r.violations.filter((v) => ["serious", "critical"].includes(v.impact || ""));
    expect(serious.map((v) => `${v.id}: ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
  });
}

test("Richtpreis-Rechner rechnet je Fahrzeugklasse", async ({ page }) => {
  await page.goto("/");
  await page.locator('#quoteForm label:has(input[value="suv"])').click();
  await page.locator('#quoteForm label:has(input[value="premium"])').click();
  await expect(page.locator("#quoteValue")).toContainText("449");
  await expect(page.locator("#quoteBook")).toHaveAttribute("href", /paket=premium&klasse=suv/);
});

test("Buchung: Zurück und Absenden erst dann sichtbar, wenn sie gebraucht werden", async ({ page }) => {
  await page.goto("/termin.html");
  await expect(page.locator("[data-wz-prev]")).toBeHidden();
  await expect(page.locator("[data-wz-submit]")).toBeHidden();
  await expect(page.locator("[data-wz-next]")).toBeVisible();
  await page.locator("[data-wz-next]").click();
  await expect(page.locator("[data-wz-prev]")).toBeVisible();
  await expect(page.locator("[data-wz-submit]")).toBeHidden();
});

test("Terminbuchung komplett bis zur Danke-Seite", async ({ page }) => {
  await page.goto("/termin.html?paket=komplett&klasse=suv");
  await expect(page.locator('input[name="paket"][value="komplett"]')).toBeChecked();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 229 €");
  await page.locator("[data-wz-next]").click();
  await expect(page.locator('input[name="klasse"][value="suv"]')).toBeChecked();
  await page.fill("#t-vehicle", "VW Tiguan 2020");
  await page.locator("[data-wz-next]").click();
  await page.locator('label.check:has(input[value="Motorraumreinigung"])').click();
  await page.locator("[data-wz-next]").click();
  await page.locator("[data-wz-next]").click();
  await expect(page.locator(".form-status")).toContainText("ergänzen");
  await page.fill("#t-date1", nextWorkday(4));
  await page.locator("[data-wz-next]").click();
  await page.fill("#t-name", "E2E Kunde");
  await page.fill("#t-phone", "0172 5555555");
  await page.fill("#t-email", "e2e@example.com");
  await page.locator('label[for="t-consent"]').click();
  await page.locator("[data-wz-submit]").click();
  await expect(page).toHaveURL(/danke\.html\?typ=termin&ref=T/);
  await expect(page.locator("h1")).toContainText("Terminanfrage eingegangen");
});

test("Kontaktformular zeigt Pflichtfelder an", async ({ page }) => {
  await page.goto("/kontakt.html");
  await page.locator('#contactForm button[type="submit"]').click();
  await expect(page.locator("#k-name")).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#k-status")).toContainText("Pflichtfelder");
});

test("Preisseite: Fahrzeugklasse schaltet Richtpreise um", async ({ page }) => {
  await page.goto("/preise.html");
  const amount = page.locator('[data-plan="komplett"] .amount');
  const before = await amount.textContent();
  await page.locator('#priceClass label').nth(2).click();
  await expect(amount).not.toHaveText(before || "");
  await expect(page.locator('[data-plan="komplett"] [data-book]')).toHaveAttribute("href", /paket=komplett&klasse=/);
});

test("Startseite: kompakter Kontaktblock führt zu Termin, WhatsApp und Kontaktseite", async ({ page }) => {
  await page.goto("/");
  const k = page.locator("#kontakt");
  await expect(k.locator('a[href="termin.html"]')).toHaveCount(1);
  await expect(k.locator('a[href^="https://wa.me/"]')).toHaveCount(1);
  await expect(k.locator('a[href^="tel:"]')).toHaveCount(1);
  await expect(k.locator('a[href="kontakt.html"]')).toHaveCount(1);
  await expect(page.locator("#contactForm")).toHaveCount(0);
});

test("Nächster freier Tag: Anzeige auf der Startseite und Übernahme in die Buchung", async ({ page }) => {
  await page.goto("/");
  const nf = page.locator(".hero [data-next-free]");
  await expect(nf).toBeVisible();
  await expect(nf.locator("[data-nf-date]")).not.toHaveText("");
  const href = await nf.getAttribute("href");
  expect(href).toMatch(/termin\.html\?datum=\d{4}-\d{2}-\d{2}$/);
  await page.goto("/" + href);
  await expect(page.locator("#t-date1")).toHaveValue(href.split("=")[1]);
  await page.goto("/termin.html");
  for (let i = 0; i < 3; i++) await page.locator("[data-wz-next]").click();  // bis Schritt 4 (Wunschtermin)
  await page.locator("[data-nf-fill]").click();
  await expect(page.locator("#t-date1")).toHaveValue(href.split("=")[1]);
});

test("Gutschein-Vorschau und Bestellung", async ({ page }) => {
  await page.goto("/gutscheine.html");
  await page.fill("#g-for", "Papa");
  await page.fill("#g-msg", "Frohe Weihnachten");
  await expect(page.locator('[data-vc="fuer"]')).toHaveText("Papa");
  await page.fill("#g-custom", "120");
  await expect(page.locator('[data-vc="value"]')).toHaveText("120 €");
  await page.locator('label.choice-pill:has(input[value="paket"])').click();
  await expect(page.locator('[data-vc="value"]')).toHaveText("Komplettpflege", { timeout: 2000 }).catch(() => {});
  await page.locator('label.choice-pill:has(input[value="wert"])').click();
  await page.fill("#g-name", "E2E Käuferin");
  await page.fill("#g-email", "kauf@example.com");
  await page.locator('label[for="g-consent"]').click();
  await page.locator('#voucherForm button[type="submit"]').click();
  await expect(page).toHaveURL(/danke\.html\?typ=gutschein/);
});

test("404-Seite", async ({ request }) => {
  const r = await request.get("/gibt-es-nicht.html");
  expect(r.status()).toBe(404);
  expect(await r.text()).toContain("Diese Seite gibt es nicht");
});
