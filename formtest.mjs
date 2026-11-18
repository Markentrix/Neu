// Formulartest nach Skill website-mit-portal V4.2, Abschnitt 21. NUR gegen den Mock-Server: node mock.mjs, dann node formtest.mjs /kontakt.html
import { chromium } from 'playwright';
const BASE = process.env.BASE || 'http://localhost:8787', PFAD = process.argv[2] || '/', erg = [];
const E = (ok, text) => erg.push(`${ok ? 'PASS' : 'FAIL'}  ${text}`);
const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
const neu = async (antwort) => { const p = await browser.newPage({ viewport: { width: 390, height: 800 } });
  if (antwort) await p.route('**/api/anfrage', r => antwort === 'aus' ? r.abort() : r.fulfill({ status: antwort.status, contentType: 'application/json', body: JSON.stringify(antwort.body) }));
  await p.goto(BASE + PFAD, { waitUntil: 'networkidle' }); return p; };
const fuellen = p => p.evaluate(() => { const f = document.querySelector('form[data-mk-form], form'); if (!f) return false;
  f.querySelectorAll('input,textarea,select').forEach(e => { if (e.name === 'website' || e.type === 'hidden' || e.type === 'submit') return;
    if (e.type === 'checkbox' || e.type === 'radio') { if (e.required || e.name === 'einwilligung' || e.name === 'agb') e.checked = true; }
    else if (e.tagName === 'SELECT') { const o = [...e.options].find(o => o.value && !o.disabled && o.value !== 'frei'); if (o) e.value = o.value; }
    else e.value = e.type === 'email' ? 'test@example.com' : e.type === 'tel' ? '05141 123456' : e.type === 'date' ? new Date(Date.now() + 6048e5).toISOString().slice(0, 10) : e.type === 'number' ? '1' : 'Test Person';
    e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }); return true; });
const senden = async p => { const next = p.locator('form [data-next]'); if (await next.count()) { await next.first().click(); await p.waitForTimeout(300); }
  await p.locator('form button[type=submit], form button:not([type])').first().click(); await p.waitForTimeout(1200); };
const text = p => p.evaluate(() => document.body.innerText);
let p = await neu(); if (!(await p.locator('form[data-mk-form], form').count())) { console.log('Kein Formular auf ' + PFAD); await browser.close(); process.exit(2); }
await senden(p); E(!p.url().includes('danke'), 'leeres Formular wird nicht abgeschickt');
p = await neu(); await fuellen(p); await p.evaluate(() => { const w = document.querySelector('[name=website]'); window.__lock = w ? w.value : null; });
E(await p.evaluate(() => window.__lock === ''), 'Lockfeld "website" vorhanden und leer');
await senden(p); E(p.url().includes('danke.html') && /MOCK-/.test(await text(p)), 'Erfolg: Weiterleitung auf danke.html mit Vorgangsnummer');
p = await neu({ status: 422, body: { ok: false, errors: { name: 'TESTFEHLER-NAME' } } }); await fuellen(p); await senden(p);
E(/TESTFEHLER-NAME/.test(await text(p)), '422: Fehlertext erscheint'); E(await p.evaluate(() => [...document.querySelectorAll('form input')].some(e => e.value === 'test@example.com')), '422: Eingaben bleiben erhalten');
E(await p.evaluate(() => !document.querySelector('form button[type=submit]')?.disabled), '422: Knopf wieder bedienbar');
p = await neu({ status: 429, body: { ok: false } }); await fuellen(p); await senden(p); E(/später/i.test(await text(p)), '429: Hinweis "später noch einmal"');
p = await neu('aus'); await fuellen(p); await senden(p); E(/tel:|\d{4,}[\s\/-]?\d{3,}|@/.test(await p.evaluate(() => document.body.innerText + [...document.querySelectorAll('a[href^="tel:"],a[href^="mailto:"]')].map(a => a.href).join(' '))), 'API aus: Ausweichkontakt sichtbar');
await browser.close(); console.log(erg.join('\n')); process.exit(erg.some(e => e.startsWith('FAIL')) ? 1 : 0);
