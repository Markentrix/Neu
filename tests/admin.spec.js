// @ts-check
const { test, expect } = require("@playwright/test");

test.describe.configure({ mode: "serial" });

async function login(page) {
  await page.goto("/admin/");
  await page.fill('input[name="user"]', "admin");
  await page.fill('input[name="password"]', "E2E-Test-Passwort");
  await page.click('button[type="submit"]');
  await expect(page.locator("h1")).toHaveText("Übersicht");
}

test("Verwaltung: falsches Passwort wird abgewiesen", async ({ page }) => {
  await page.goto("/admin/");
  await page.fill('input[name="user"]', "admin");
  await page.fill('input[name="password"]', "falsch");
  await page.click('button[type="submit"]');
  await expect(page.locator("#lerr")).toContainText("falsch");
});

test("Verwaltung: Anfrage bearbeiten, Kalender, Inhalte, Veröffentlichen", async ({ page, request }) => {
  const d = new Date(); d.setDate(d.getDate() + 6); while (d.getDay() === 0) d.setDate(d.getDate() + 1);
  const r = await request.post("/api/anfrage", { data: { typ: "termin", paket: "premium", klasse: "mittel", datum: d.toISOString().slice(0, 10), name: "Admin Test", telefon: "0172 4444444", einwilligung: "ja" } });
  const { ref } = await r.json();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  await expect(page.locator(".kpi").first()).toBeVisible();
  await page.click('a.nav[href="#/anfragen"]');
  await page.click(`text=${ref}`);
  await expect(page.locator(".drawer h2")).toHaveText("Admin Test");
  await expect(page.locator(".drawer")).toContainText("ab 399 €");
  await page.selectOption("#rst", "termin_bestaetigt");
  await page.click(".drawer >> text=Speichern");
  await expect(page.locator("#toast")).toHaveText("Gespeichert");
  await page.keyboard.press("Escape");
  await page.click('a.nav[href="#/kalender"]');
  await expect(page.locator(".cal")).toBeVisible();
  await page.click('a.nav[href="#/inhalte"]');
  await page.click("text=Pakete & Preise");
  await expect(page.locator(".je")).toBeVisible();
  await page.click('a.nav[href="#/veroeffentlichen"]');
  await page.click("#pub");
  await expect(page.locator("#pres .note").first()).toContainText("Live seit", { timeout: 15000 });
  expect(errors).toEqual([]);
});
