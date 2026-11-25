// Formulartest nach Abschnitt 21 des Skills. Nur gegen den Mock-Server. Aufruf: node tools/formtest.mjs /kontakt/
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const BASE = process.env.BASE || 'http://localhost:8787', PFAD = process.argv[2] || '/kontakt/', erg = [];
const E = (ok, text) => erg.push(`${ok ? 'PASS' : 'FAIL'}  ${text}`);
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
const neu = async (antwort) => { const p = await browser.newPage({ viewport: { width: 390, height: 800 } });
  if (antwort) await p.route('**/api/anfrage', r => antwort === 'aus' ? r.abort() : r.fulfill({ status: antwort.status, contentType: 'application/json', body: JSON.stringify(antwort.body) }));
  await p.goto(BASE + PFAD, { waitUntil: 'networkidle' }); return p; };
const fuellen = p => p.evaluate(() => { const f = document.querySelector('form'); if (!f) return false;
  f.querySelectorAll('input,textarea,select').forEach(e => { if (e.name === 'website' || e.type === 'hidden' || e.type === 'submit' || e.type === 'file') return;
    if (e.type === 'checkbox' || e.type === 'radio') { if (e.type === 'checkbox' && (e.required || e.name === 'einwilligung' || e.name === 'agb')) e.checked = true; }
    else if (e.tagName === 'SELECT') { const o = [...e.options].find(o => o.value && !o.disabled); if (o) e.value = o.value; }
    else e.value = e.type === 'email' ? 'test@example.com' : e.type === 'tel' ? '05141 123456' : e.type === 'date' ? new Date(Date.now() + 6048e5).toISOString().slice(0, 10) : e.type === 'number' ? '1' : 'Test Person';
    e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }); return true; });
const senden = async p => { await p.locator('form button[type=submit], form button:not([type])').first().click(); await p.waitForTimeout(1500); };
const text = p => p.evaluate(() => document.body.innerText);
let p = await neu(); if (!(await p.locator('form').count())) { console.log('Kein Formular auf ' + PFAD); await browser.close(); process.exit(2); }
await senden(p); E(!p.url().includes('danke'), 'leeres Formular wird nicht abgeschickt');
p = await neu(); await fuellen(p);
E(await p.evaluate(() => { const w = document.querySelector('[name=website]'); return !!w && w.value === ''; }), 'Lockfeld "website" vorhanden und leer');
await senden(p); E(/danke\.html|thank-you\.html/.test(p.url()) && /MOCK-/.test(await text(p)), 'Erfolg: Weiterleitung auf danke.html mit Vorgangsnummer');
p = await neu({ status: 422, body: { ok: false, errors: { name: 'TESTFEHLER-NAME' } } }); await fuellen(p); await senden(p);
E(/TESTFEHLER-NAME/.test(await text(p)), '422: Fehlertext erscheint'); E(await p.evaluate(() => [...document.querySelectorAll('form input')].some(e => e.value === 'test@example.com')), '422: Eingaben bleiben erhalten');
E(await p.evaluate(() => !document.querySelector('form button[type=submit]')?.disabled), '422: Knopf wieder bedienbar');
p = await neu({ status: 429, body: { ok: false } }); await fuellen(p); await senden(p); E(/später|later/i.test(await text(p)), '429: Hinweis "später noch einmal"');
p = await neu('aus'); await fuellen(p); await senden(p); E(/tel:|\d{4,}[\s\/-]?\d{3,}|@/.test(await p.evaluate(() => document.body.innerText + [...document.querySelectorAll('a[href^="tel:"],a[href^="mailto:"]')].map(a => a.href).join(' '))), 'API aus: Ausweichkontakt sichtbar');
await browser.close(); console.log(erg.join('\n')); process.exit(erg.some(e => e.startsWith('FAIL')) ? 1 : 0);
