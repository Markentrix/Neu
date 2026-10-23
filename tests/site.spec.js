// @ts-check
const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

const PAGES = [
  "/", "/preise.html", "/kontakt.html", "/ueber-uns.html", "/elbdetail-care.html", "/leistungen/keramikversiegelung-celle.html",
  "/leistungen/lederaufbereitung-celle.html", "/termin.html", "/gutscheine.html", "/firmenkunden.html", "/aktion/winterschutz.html", "/ratgeber/index.html",
  "/ratgeber/leasingrueckgabe-checkliste.html", "/ratgeber/kosten-fahrzeugaufbereitung-celle.html",
  "/leistungen/aussenaufbereitung-celle.html", "/leistungen/innenaufbereitung-celle.html", "/leistungen/lackpolitur-celle.html",
  "/leistungen/lackversiegelung-celle.html", "/leistungen/leasingrueckgabe-gebrauchtwagen-celle.html",
  "/leistungen/felgenversiegelung-celle.html", "/leistungen/scheibenversiegelung-celle.html",
  "/impressum.html", "/datenschutz.html", "/agb.html", "/widerruf.html", "/danke.html", "/angebote.html", "/ratgeber/winter.html", "/zertifikate.html",
  "/ratgeber/auto-im-winter-waschen-streusalz.html", "/ratgeber/feuchtigkeit-im-auto-winter.html",
];

// Desktop und Mobil laufen gleichzeitig gegen dieselbe Portal-Attrappe: je Projekt andere Tage, damit sich Buchungen nicht in die Quere kommen
const dayShift = (info) => (info.project.name === "mobil" ? 40 : 0);
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

for (const path of ["/", "/angebote.html", "/ratgeber/winter.html", "/zertifikate.html", "/preise.html", "/kontakt.html", "/ueber-uns.html", "/elbdetail-care.html", "/leistungen/keramikversiegelung-celle.html", "/termin.html", "/gutscheine.html", "/ratgeber/leasingrueckgabe-checkliste.html", "/leistungen/lackpolitur-celle.html", "/firmenkunden.html"]) {
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
  await page.locator('#quoteForm label:has(input[value="excellence"])').click();
  await expect(page.locator("#quoteValue")).toContainText("899");
  await expect(page.locator("#quoteBook")).toHaveAttribute("href", /paket=excellence&klasse=suv/);
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

test("Terminbuchung komplett bis zur Danke-Seite", async ({ page }, info) => {
  await page.goto("/termin.html?paket=essential&klasse=suv");
  await expect(page.locator('input[name="paket"][value="essential"]')).toBeChecked();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 449 €");
  await page.locator("[data-wz-next]").click();
  await expect(page.locator('input[name="klasse"][value="suv"]')).toBeChecked();
  await page.fill("#t-vehicle", "VW Tiguan 2020");
  await page.locator("[data-wz-next]").click();
  await page.locator('label.check:has(input[value="Motorraumreinigung"])').click();
  await page.locator("[data-wz-next]").click();
  await page.locator("[data-wz-next]").click();
  await expect(page.locator(".form-status")).toContainText("ergänzen");
  await page.fill("#t-date1", nextWorkday(4 + dayShift(info)));
  await page.locator("#t-date1").dispatchEvent("change");
  await expect(page.locator("#t-slots-msg")).toContainText("frei");
  await page.locator('#t-slots label:has(input[value="10:00"])').click();
  await expect(page.locator('[data-sum="datum"]')).toContainText("10:00 Uhr");
  await page.locator("[data-wz-next]").click();
  await page.fill("#t-name", "E2E Kunde");
  await page.fill("#t-phone", "0172 5555555");
  await page.fill("#t-email", "e2e@example.com");
  await page.locator('label[for="t-consent"]').click();
  await page.locator("[data-wz-submit]").click();
  await expect(page.locator("#t-agb")).toHaveAttribute("aria-invalid", "true");  // AGB sind Pflicht
  await page.check("#t-agb");  // nicht auf das Label klicken, darin steckt der Link zu den AGB
  if (await page.locator("#t-vorzeitig").isEnabled()) await page.check("#t-vorzeitig");
  await page.locator("[data-wz-submit]").click();
  await expect(page).toHaveURL(/danke\.html\?typ=termin&ref=T/);
  await expect(page.locator("h1")).toContainText("Terminanfrage eingegangen");
  await expect(page.locator("[data-thanks-text]")).toContainText("Vorgangsnummer: T");
  const sent = (await (await page.request.get("/__mock/anfragen")).json()).pop();
  expect(sent).toMatchObject({ typ: "termin", paket: "essential", klasse: "suv", uhrzeit: "10:00", email: "e2e@example.com", einwilligung: "ja", agb: "ja", website: "" });
  expect(sent.extras).toContain("Motorraumreinigung");
});

test("Buchung: nur freie Uhrzeiten aus dem Portal, Doppelbuchung lädt die Zeiten neu", async ({ page }, info) => {
  const day = nextWorkday(9 + dayShift(info));
  await page.request.post("/__mock/belegen", { data: { datum: day, uhrzeit: "08:00" } });
  await page.goto("/termin.html?paket=refresh&datum=" + day);
  for (let i = 0; i < 3; i++) await page.locator("[data-wz-next]").click();
  await expect(page.locator('#t-slots input[value="08:00"]')).toBeDisabled();
  await expect(page.locator('#t-slots input[value="09:00"]')).toBeEnabled();
  await expect(page.locator("#page-h")).toContainText("Termin buchen");  // Portal meldet selfBooking: true
  await page.locator('#t-slots label:has(input[value="09:00"])').click();
  await page.locator("[data-wz-next]").click();
  await page.fill("#t-name", "Zweite Kundin");
  await page.fill("#t-phone", "0172 5555556");
  await page.fill("#t-email", "zwei@example.com");
  await page.locator('label[for="t-consent"]').click();
  await page.check("#t-agb");  // nicht auf das Label klicken, darin steckt der Link zu den AGB
  if (await page.locator("#t-vorzeitig").isEnabled()) await page.check("#t-vorzeitig");
  await page.request.post("/__mock/belegen", { data: { datum: day, uhrzeit: "09:00" } });  // jemand war schneller
  await page.locator("[data-wz-submit]").click();
  await expect(page.locator("#t-slots-msg, [data-err]").first()).toBeVisible();
  await expect(page.locator('#t-slots input[value="09:00"]')).toBeDisabled();
  await expect(page.locator("#t-name")).toHaveValue("Zweite Kundin");  // Eingaben bleiben erhalten
});

test("Buchung: Termin in den nächsten 14 Tagen verlangt den vorzeitigen Beginn", async ({ page }) => {
  await page.goto("/termin.html?datum=" + nextWorkday(3));
  await expect(page.locator("[data-vorzeitig]")).not.toHaveAttribute("hidden", "");
  await expect(page.locator("#t-vorzeitig")).toHaveAttribute("required", "");
  await page.goto("/termin.html?datum=" + nextWorkday(30));
  await expect(page.locator("[data-vorzeitig]")).toHaveAttribute("hidden", "");
});

test("Ohne erreichbare Schnittstelle: Formular zeigt WhatsApp, E-Mail und Telefon", async ({ page }) => {
  await page.route("**/api/**", (route) => route.abort());
  await page.goto("/kontakt.html");
  await page.fill("#k-name", "Offline Test");
  await page.fill("#k-email", "offline@example.com");
  await page.selectOption("#k-package", { index: 1 });
  await page.fill("#k-message", "Frage");
  await page.locator('label[for="k-consent"]').click();
  await page.locator('#contactForm button[type="submit"]').click();
  const st = page.locator("#k-status");
  await expect(st.locator('a[href^="https://wa.me/"]')).toBeVisible();
  await expect(st.locator('a[href^="mailto:"]')).toBeVisible();
  await expect(st.locator('a[href^="tel:"]')).toBeVisible();
  await page.goto("/termin.html?datum=" + nextWorkday(9));
  for (let i = 0; i < 3; i++) await page.locator("[data-wz-next]").click();
  await expect(page.locator('#t-slots-msg a[href^="tel:"]')).toBeVisible();
});

test("Danke-Seite: Anzahlung per PayPal.me mit Betrag und Vorgangsnummer", async ({ page }) => {
  await page.route("**/config.js*", async (route) => {
    const r = await route.fetch();
    await route.fulfill({ response: r, body: (await r.text()) + '\nwindow.ELB.booking.paypalMe="elbdetail";' });
  });
  await page.goto("/danke.html?typ=termin&ref=T261023-0001&anz=49.35");
  const a = page.locator('[data-thanks-pay] a[href^="https://paypal.me/"]');
  await expect(a).toHaveAttribute("href", "https://paypal.me/elbdetail/49.35EUR");
  await expect(page.locator("[data-thanks-pay]")).toContainText("T261023-0001");
  await page.goto("/danke.html?typ=kontakt&ref=K1&anz=49.35");
  await expect(page.locator("[data-thanks-pay]")).toBeHidden();
});

test("Widerruf über das Formular geht als typ widerruf an das Portal", async ({ page }) => {
  await page.goto("/widerruf.html");
  await page.fill("#w-name", "Karla Kunde");
  await page.fill("#w-email", "karla@example.com");
  await page.fill("#w-vorgang", "T261023-0001");
  await page.locator('label[for="w-consent"]').click();
  await page.locator('#widerrufForm button[type="submit"]').click();
  await expect(page).toHaveURL(/danke\.html\?typ=widerruf&ref=W/);
  const sent = (await (await page.request.get("/__mock/anfragen")).json()).pop();
  expect(sent).toMatchObject({ typ: "widerruf", vorgang: "T261023-0001", email: "karla@example.com" });
});

test("Kontaktformular zeigt Pflichtfelder an", async ({ page }) => {
  await page.goto("/kontakt.html");
  await page.locator('#contactForm button[type="submit"]').click();
  await expect(page.locator("#k-name")).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#k-status")).toContainText("Pflichtfelder");
});

test("Preisseite: Fahrzeugklasse schaltet Richtpreise um", async ({ page }) => {
  await page.goto("/preise.html");
  const amount = page.locator('[data-plan="essential"] .amount');
  const before = await amount.textContent();
  await page.locator('#priceClass label').nth(2).click();
  await expect(amount).not.toHaveText(before || "");
  await expect(page.locator('[data-plan="essential"] [data-book]')).toHaveAttribute("href", /paket=essential&klasse=/);
});

test("Felgen- und Scheibenkeramik: Karten auf der Startseite, Preise und Herstellerhinweis", async ({ page }) => {
  await page.goto("/");
  const cards = page.locator(".cer-card");
  await expect(cards).toHaveCount(3);
  await expect(cards.nth(1)).toContainText("210");
  await expect(cards.nth(2)).toContainText("79");
  await expect(page.locator(".cer-note")).toContainText("Herstellerangaben");
  await page.goto("/leistungen/felgenversiegelung-celle.html");
  await expect(page.locator("#keramik-preise")).toContainText("350");
  await expect(page.locator("#keramik-preise")).toContainText("laut Hersteller");
  await page.goto("/preise.html");
  await expect(page.locator("#felgen-scheiben-preise")).toContainText("114 €");  // Winter-Aktion statt 179 €
});

test("Buchung: Zustandsangaben erhöhen den Richtpreis (Tierhaare 10 %, sonst 5 %, Ledersitze nicht)", async ({ page }) => {
  await page.goto("/termin.html?paket=essential&klasse=kompakt");
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 329 €");
  await page.locator("[data-wz-next]").click();
  await page.locator('label.check:has(input[value="leder"])').click();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 329 €");
  await page.locator('label.check:has(input[value="tierhaare"])').click();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 362 €");
  await expect(page.locator("#t-surcharge")).toContainText("10 %");
  await page.locator('label.check:has(input[value="flecken"])').click();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 378 €");
});

test("Winterangebot: Preise je Fahrzeugklasse und direkt buchbar", async ({ page }) => {
  await page.goto("/aktion/winterschutz.html");
  const t = page.locator(".winter-prices");
  await expect(t).toContainText("ab 329 €");
  await expect(t).toContainText("ab 549 €");
  await expect(t).toContainText("nach Besichtigung");
  await page.goto("/termin.html?paket=winter&quelle=winter");
  await expect(page.locator('input[name="paket"][value="winter"]')).toBeChecked();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 329 €");
});

test("Winterangebot: Inhalt sichtbar, C² CarCeramic statt Wachs wählbar", async ({ page }) => {
  await page.goto("/aktion/winterschutz.html");
  const inc = page.locator("#winterangebot ~ ul.includes").first();
  for (const t of ["Innenreinigung", "Außenwäsche von Hand", "Glanzpolitur", "Wachsversiegelung"]) await expect(inc).toContainText(t);
  await expect(page.locator("main")).toContainText("Dann entfällt das Wachs");
  await page.locator('a[href*="schutz=keramik"]').first().click();
  await expect(page.locator('input[name="winterschutz"][value="keramik"]')).toBeChecked();
  await expect(page.locator(".wz-winter")).toBeVisible();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 329 € + Aufpreis C² CarCeramic");
  await expect(page.locator('[data-sum="anzahlung"]')).toHaveText("nach Absprache");
  await page.locator('label.choice-pill:has(input[value="wachs"])').click();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("ab 329 €");
  await page.locator('label.choice-card:has(input[value="essential"])').click();
  await expect(page.locator(".wz-winter")).toBeHidden();
});

test("Winter-Aktion Scheibenkeramik: Aktionspreise, Angebot und Buchung je Umfang", async ({ page }) => {
  await page.goto("/leistungen/scheibenversiegelung-celle.html");
  const t = page.locator("#keramik-preise .ceramic-table");
  await expect(t.locator("tr.is-promo")).toHaveCount(2);
  await expect(t).toContainText("99 €");
  await expect(t).toContainText("114 €");
  await expect(page.locator(".promo-box")).toContainText("bis 28.02.2027");
  await page.goto("/angebote.html");
  await expect(page.locator("main")).toContainText("alle Außenscheiben 99 €");
  await page.goto("/termin.html?paket=scheiben");
  await expect(page.locator(".wz-scheiben")).toBeVisible();
  await expect(page.locator('input[name="scheibenumfang"][value="Alle Außenscheiben"]')).toBeChecked();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("99 €");
  await page.locator('label.choice-pill:has(input[value="Alle Außenscheiben inklusive Panoramadach"])').click();
  await expect(page.locator('[data-sum="preis"]')).toHaveText("114 €");
  await expect(page.locator('[data-sum="anzahlung"]')).toHaveText("nach Absprache");  // ohne PayPal.me-Namen klärt René die Anzahlung
});

test("AGB und Widerruf: im Fuß verlinkt, Belehrung, Muster-Formular und Widerrufsformular", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('footer a[href="agb.html"]')).toHaveText("AGB");
  await expect(page.locator('footer a[href="widerruf.html"]')).toHaveText("Vertrag widerrufen");
  await page.goto("/agb.html");
  await expect(page.locator("h1")).toContainText("Allgemeine Geschäfts");
  await expect(page.locator("#widerruf")).toBeVisible();
  await expect(page.locator("#widerrufsformular")).toBeVisible();
  await expect(page.locator("main")).toContainText("Nachweis gestattet");
  await page.goto("/widerruf.html");
  await expect(page.locator('#widerrufForm button[type="submit"]')).toHaveText("Widerruf bestätigen");
  await page.goto("/termin.html");
  await expect(page.locator('#bookingForm label[for="t-agb"] a[href="agb.html"]')).toHaveCount(1);
});

test("Preisseite: C² CarCeramic-Preisliste und optionale Versiegelung", async ({ page }) => {
  await page.goto("/preise.html");
  const cer = page.locator("#keramik-preise");
  await expect(cer).toContainText("550");
  await expect(cer).toContainText("1.190");
  await expect(cer).toContainText("bis 7 m");
  await expect(page.locator('[data-plan="signature"] li.opt').first()).toContainText("separat");
  await page.locator('#priceClass label:has(input[value="camper"])').click();
  await expect(page.locator('[data-plan="essential"] .amount')).toContainText("auf Anfrage");
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
  await expect(page.locator('[data-vc="value"]')).toHaveText("Essential", { timeout: 2000 }).catch(() => {});
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

test("Preisrechner: Sport / Luxus und Wohnmobil zeigen individuelles Angebot statt Preis", async ({ page }) => {
  await page.goto("/");
  await page.locator('label:has(input[name="qclass"][value="sport"])').click();
  await expect(page.locator("#quoteValue")).toContainText("auf Anfrage");
  await expect(page.locator("#quoteBook")).toHaveAttribute("href", /klasse=sport/);
  await expect(page.locator("#quoteBook")).toContainText("Individuelles Angebot");
  await page.locator('label:has(input[name="qclass"][value="camper"])').click();
  await expect(page.locator("#quoteNote")).toContainText("Wohnmobile");
  await page.locator('label:has(input[name="qclass"][value="suv"])').click();
  await expect(page.locator("#quoteValue")).toContainText("449");
});

test("Kein eigenes Cookie-Banner und kein Google-Skript: Baustein des Portals im Fuß, Bewertungs-Baustein auf der Startseite", async ({ page }) => {
  const hosts = [];
  page.on("request", (r) => hosts.push(new URL(r.url()).hostname));
  await page.goto("/");
  await page.waitForTimeout(500);
  await expect(page.locator("#consent")).toHaveCount(0);
  await expect(page.locator('footer [data-mk="cookies"]')).toHaveCount(1);
  await expect(page.locator('#bewertungen [data-mk="bewertungen"]')).toHaveCount(1);
  await expect(page.locator(".review-card").first()).toBeVisible();  // Ausweichinhalt, solange der Baustein leer bleibt
  expect(hosts.filter((h) => /google|markentrix/.test(h))).toEqual([]);
});

test("Zertifikate: Vergrößern öffnet die Lightbox, Esc schließt sie", async ({ page }) => {
  await page.goto("/zertifikate.html");
  await expect(page.locator(".cert")).toHaveCount(3);
  await page.locator("a[data-lightbox]").first().click();
  await expect(page.locator("dialog.lightbox")).toHaveAttribute("open", "");
  await expect(page.locator("dialog.lightbox img")).toHaveAttribute("src", /zertifikat-/);
  await page.keyboard.press("Escape");
  await expect(page.locator("dialog.lightbox")).not.toHaveAttribute("open", "");
});
