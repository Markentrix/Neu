'use strict';
const test = require('node:test'); const assert = require('node:assert/strict'); const http = require('http'); const fs = require('fs'); const os = require('os'); const path = require('path'); const crypto = require('crypto');
// ---- Fake Stripe & PayPal ----
const calls = []; let sessSeq = 0;
const fake = http.createServer((req, res) => {
  let b = ''; req.on('data', d => b += d); req.on('end', () => {
    calls.push(`${req.method} ${req.url}`); const send = (o, c = 200) => { res.writeHead(c, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(o)); };
    if (req.url === '/v1/oauth2/token') return send({ access_token: 'AT', expires_in: 3000 });
    if (req.url === '/v1/checkout/sessions' && req.method === 'POST') { const id = 'cs_test_' + (++sessSeq); return send({ id, url: `https://checkout.stripe.test/${id}`, _body: b }); }
    if (req.url.startsWith('/v1/checkout/sessions/')) return send({ id: req.url.split('/').pop(), payment_status: 'paid', payment_intent: 'pi_test_9' });
    if (req.url === '/v1/refunds') return send({ id: 're_1' });
    if (req.url === '/v2/checkout/orders') return send({ id: 'PPORDER1', links: [{ rel: 'payer-action', href: 'https://paypal.test/approve/PPORDER1' }] });
    if (/\/capture$/.test(req.url)) return send({ status: 'COMPLETED', purchase_units: [{ payments: { captures: [{ id: 'CAP1' }] } }] });
    if (/\/refund$/.test(req.url)) return send({ id: 'RF1' });
    send({ error: 'nf' }, 404);
  });
});
let base, srv, ctx; const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ic24-'));
test.before(async () => {
  await new Promise(r => fake.listen(0, r)); const fp = fake.address().port;
  Object.assign(process.env, { STRIPE_SECRET_KEY: 'sk_test_x', STRIPE_API_BASE: `http://127.0.0.1:${fp}`, STRIPE_WEBHOOK_SECRET: 'whsec_test', PAYPAL_CLIENT_ID: 'id', PAYPAL_CLIENT_SECRET: 'sec', PAYPAL_API_BASE: `http://127.0.0.1:${fp}`,
    ADMIN_EMAIL: 'admin@test.de', ADMIN_PASSWORD: 'AdminPasswort-123', BASE_URL: 'http://localhost:3999', BANK_IBAN: 'DE02120300000000202051', BANK_NAME: 'Testbank', DATA_DIR: tmp });
  ctx = require('../app').create({ dbFile: path.join(tmp, 't.db'), siteDir: path.join(__dirname, '..', '..', 'site') });
  await new Promise(r => { srv = ctx.app.listen(0, r); }); base = `http://127.0.0.1:${srv.address().port}`;
});
test.after(() => { srv.close(); fake.close(); ctx.db.close(); });
let cookie = '';
async function api(p, { method = 'GET', body, headers = {}, raw, c = true } = {}) {
  const h = { ...headers }; if (body !== undefined && !raw) h['Content-Type'] = 'application/json'; if (method !== 'GET') h['X-Requested-With'] = 'ic'; if (c && cookie) h.Cookie = cookie;
  const r = await fetch(base + p, { method, headers: h, body: raw ? body : body !== undefined ? JSON.stringify(body) : undefined, redirect: 'manual' });
  const sc = r.headers.get('set-cookie'); if (sc && c) { const m = sc.match(/ic_sess=[^;]*/); if (m) cookie = m[0]; }
  const t = await r.text(); let j = null; try { j = JSON.parse(t); } catch { } return { status: r.status, json: j, text: t, headers: r.headers };
}
const addr = { first: 'Max', last: 'Muster', street: 'Hauptstr. 1', zip: '49163', city: 'Bohmte', country: 'DE' };
const base_order = (payment, extra = {}) => ({ items: [{ sku: 'alu-matic-stuetzen', qty: 2 }], customer: { email: 'max@example.de', phone: '0151' }, billing: addr, sameShipping: true, payment, accept: true, ...extra });
const sku = () => [...ctx.catalog.skus.values()].find(s => s.sku === 'alu-matic-stuetzen');

test('Health + statische Seiten + Sicherheitsheader', async () => {
  assert.equal((await api('/healthz')).json.ok, true);
  const r = await api('/index.html'); assert.equal(r.status, 200); assert.match(r.headers.get('content-security-policy'), /default-src 'self'/);
  assert.equal((await api('/gibtsnicht.html')).status, 404);
});
test('Preise kommen vom Server, nicht vom Client', async () => {
  assert.ok(sku(), 'Test-SKU vorhanden'); const price = sku().price;
  const q = await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 2, price: 1 }] } });
  assert.equal(q.status, 200); assert.equal(q.json.subtotal, price * 2); assert.equal(q.json.shipping_cost, 0);
  assert.equal((await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'nope', qty: 1 }] } })).status, 409);
  assert.equal((await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 999 }] } })).status, 400);
});
test('CSRF-Header ist Pflicht', async () => {
  const r = await fetch(base + '/api/cart/quote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); assert.equal(r.status, 403);
});
test('Vorkasse: Bestellung, Status, Mails', async () => {
  const r = await api('/api/checkout', { method: 'POST', body: base_order('transfer'), c: false }); assert.equal(r.status, 200, r.text); assert.match(r.json.redirect, /^bestellung\.html\?n=IC-/);
  const o = await api(`/api/order/${r.json.number}?t=${r.json.token}`); assert.equal(o.json.status, 'wartet_auf_zahlung'); assert.equal(o.json.total, sku().price * 2); assert.ok(o.json.bank.iban);
  assert.equal((await api(`/api/order/${r.json.number}?t=falsch`)).status, 404);
  const mails = ctx.db.all('SELECT to_addr FROM mail_log').map(m => m.to_addr); assert.ok(mails.includes('max@example.de')); assert.ok(mails.includes('info@italiacamper24.de'));
});
test('Rechnungskauf landet in Prüfung', async () => {
  const r = await api('/api/checkout', { method: 'POST', body: base_order('invoice'), c: false }); assert.equal(r.status, 200);
  assert.equal(ctx.orders.get(r.json.number).status, 'pruefung');
  const pdf = await api(`/api/order/${r.json.number}/invoice.pdf?t=${r.json.token}`); assert.equal(pdf.status, 200); assert.equal(pdf.headers.get('content-type'), 'application/pdf'); assert.match(pdf.text.slice(0, 5), /%PDF/);
});
test('Karte (Stripe): Session, Webhook-Signatur, bezahlt + Rechnungsnummer', async () => {
  const r = await api('/api/checkout', { method: 'POST', body: base_order('card'), c: false }); assert.equal(r.status, 200, r.text); assert.match(r.json.redirect, /^https:\/\/checkout\.stripe\.test\//);
  const ev = JSON.stringify({ type: 'checkout.session.completed', data: { object: { id: 'cs_test_1', client_reference_id: r.json.number, payment_status: 'paid', payment_intent: 'pi_test_9' } } });
  const t = Math.floor(Date.now() / 1000); const sig = crypto.createHmac('sha256', 'whsec_test').update(`${t}.${ev}`).digest('hex');
  const bad = await api('/api/webhooks/stripe', { method: 'POST', raw: true, body: ev, headers: { 'stripe-signature': `t=${t},v1=deadbeef`, 'Content-Type': 'application/json' }, c: false }); assert.equal(bad.status, 400);
  const ok = await api('/api/webhooks/stripe', { method: 'POST', raw: true, body: ev, headers: { 'stripe-signature': `t=${t},v1=${sig}`, 'Content-Type': 'application/json' }, c: false }); assert.equal(ok.status, 200);
  const o = ctx.orders.get(r.json.number); assert.equal(o.payment_status, 'bezahlt'); assert.equal(o.status, 'bezahlt'); assert.match(o.invoice_no, /^RE-\d{4}-\d{5}$/); assert.equal(o.payment_ref2, 'pi_test_9');
  await api('/api/webhooks/stripe', { method: 'POST', raw: true, body: ev, headers: { 'stripe-signature': `t=${t},v1=${sig}` }, c: false }); // idempotent
  assert.equal(ctx.db.all("SELECT 1 FROM order_events WHERE order_id=? AND type='bezahlt'", o.id).length, 1);
});
test('PayPal: Weiterleitung und Capture bei Rückkehr', async () => {
  const r = await api('/api/checkout', { method: 'POST', body: base_order('paypal'), c: false }); assert.equal(r.status, 200); assert.match(r.json.redirect, /paypal\.test\/approve/);
  const ret = await api(`/api/paypal/return?n=${r.json.number}&t=${r.json.token}`, { c: false }); assert.equal(ret.status, 302);
  const o = ctx.orders.get(r.json.number); assert.equal(o.payment_status, 'bezahlt'); assert.equal(o.payment_ref2, 'CAP1');
  const bad = await api(`/api/paypal/return?n=${r.json.number}&t=x`, { c: false }); assert.match(bad.headers.get('location'), /error/);
});
test('Validierung: AGB, E-Mail, Adresse', async () => {
  assert.equal((await api('/api/checkout', { method: 'POST', body: base_order('transfer', { accept: false }), c: false })).status, 400);
  assert.equal((await api('/api/checkout', { method: 'POST', body: base_order('transfer', { customer: { email: 'kaputt' } }), c: false })).status, 400);
  assert.equal((await api('/api/checkout', { method: 'POST', body: base_order('transfer', { billing: { ...addr, zip: 'abc' } }), c: false })).status, 400);
});
test('Konto: Registrierung, Login, Bestellungen, Passwort-Reset', async () => {
  cookie = ''; const reg = await api('/api/register', { method: 'POST', body: { email: 'kunde@example.de', password: 'passwort123', first: 'Kai', last: 'Kunde' } }); assert.equal(reg.status, 200);
  assert.equal((await api('/api/me')).json.user.email, 'kunde@example.de');
  const o = await api('/api/checkout', { method: 'POST', body: base_order('transfer', { customer: { email: 'kunde@example.de' } }) }); assert.equal(o.status, 200);
  const list = await api('/api/me/orders'); assert.equal(list.json.orders.length, 1); assert.equal((await api(`/api/order/${o.json.number}`)).status, 200, 'Eingeloggt ohne Token');
  await api('/api/logout', { method: 'POST' }); cookie = ''; assert.equal((await api('/api/me/orders')).status, 401);
  assert.equal((await api('/api/login', { method: 'POST', body: { email: 'kunde@example.de', password: 'falsch' } })).status, 401);
  await api('/api/password/forgot', { method: 'POST', body: { email: 'kunde@example.de' } }); const m = ctx.db.get("SELECT body FROM mail_log WHERE subject LIKE 'Passwort%' ORDER BY id DESC"); const token = m.body.match(/t=([\w-]+)/)[1];
  assert.equal((await api('/api/password/reset', { method: 'POST', body: { token, password: 'neuesPasswort1' } })).status, 200);
  assert.equal((await api('/api/login', { method: 'POST', body: { email: 'kunde@example.de', password: 'neuesPasswort1' } })).status, 200);
});
test('Gutschein, Preis-Override und Admin-Funktionen', async () => {
  cookie = ''; assert.equal((await api('/api/admin/stats')).status, 401); assert.equal((await api('/api/admin/login', { method: 'POST', body: { email: 'admin@test.de', password: 'falsch' } })).status, 401);
  assert.equal((await api('/api/admin/login', { method: 'POST', body: { email: 'admin@test.de', password: 'AdminPasswort-123' } })).status, 200);
  const st = await api('/api/admin/stats'); assert.equal(st.status, 200); assert.ok(st.json.latest.length >= 4);
  assert.equal((await api('/api/admin/coupons', { method: 'POST', body: { code: 'test10', type: 'percent', value: 10 } })).status, 200);
  const old = sku().price; const q = await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 1 }], coupon: 'TEST10' } }); assert.equal(q.json.discount, Math.round(old * 10) / 100);
  assert.equal((await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 1 }], coupon: 'NOPE' } })).status, 400);
  assert.equal((await api('/api/admin/sku', { method: 'PUT', body: { sku: 'alu-matic-stuetzen', price: 299 } })).status, 200);
  assert.equal((await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 1 }] } })).json.subtotal, 299);
  await api('/api/admin/sku', { method: 'PUT', body: { sku: 'alu-matic-stuetzen', active: false } }); assert.equal((await api('/api/cart/quote', { method: 'POST', body: { items: [{ sku: 'alu-matic-stuetzen', qty: 1 }] } })).status, 409);
  await api('/api/admin/sku', { method: 'PUT', body: { sku: 'alu-matic-stuetzen', price: '', active: true } }); assert.equal(sku().price, old);
  const list = await api('/api/admin/orders?status=bezahlt'); assert.ok(list.json.rows.length >= 2); const num = list.json.rows.find(r => r.payment_method === 'card').number;
  const det = await api(`/api/admin/orders/${num}`); assert.ok(det.json.events.length >= 2);
  const sh = await api(`/api/admin/orders/${num}/status`, { method: 'POST', body: { status: 'versendet', tracking: '12345', carrier: 'DHL' } }); assert.equal(sh.json.order.status, 'versendet'); assert.equal(sh.json.order.tracking, '12345');
  assert.ok(ctx.db.get("SELECT 1 FROM mail_log WHERE subject LIKE '%versendet%'"));
  const ref = await api(`/api/admin/orders/${num}/refund`, { method: 'POST', body: {} }); assert.equal(ref.status, 200, ref.text); assert.equal(ctx.orders.get(num).payment_status, 'erstattet');
  const tr = list.json.rows.find(r => r.payment_method === 'paypal'); assert.ok(tr);
  const wait = ctx.db.get("SELECT number FROM orders WHERE status='wartet_auf_zahlung' LIMIT 1").number; const paid = await api(`/api/admin/orders/${wait}/paid`, { method: 'POST', body: {} }); assert.equal(paid.json.order.payment_status, 'bezahlt'); assert.ok(paid.json.order.invoice_no);
  const csv = await api('/api/admin/orders.csv'); assert.match(csv.text, /Bestellnr;Datum/); assert.equal((await api(`/api/admin/orders/${num}/invoice.pdf`)).status, 200);
  assert.equal((await api('/api/admin/products?q=alu-matic')).json.products.length >= 1, true);
  assert.equal((await api('/api/admin/settings')).status, 200); assert.equal((await api('/api/admin/mails')).json.rows.length > 5, true);
});
test('Formulare: Anfrage speichern, Honeypot, Pflichtfelder', async () => {
  cookie = ''; const ok = await api('/api/forms/angebot', { method: 'POST', body: { name: 'Anna', email: 'anna@example.de', produkt: 'Anhängerkupplung', nachricht: 'Ducato 250', dsgvo: true } }); assert.equal(ok.status, 200);
  assert.equal((await api('/api/forms/angebot', { method: 'POST', body: { name: 'Anna', email: 'bad', nachricht: 'x', dsgvo: true } })).status, 400);
  assert.equal((await api('/api/forms/kontakt', { method: 'POST', body: { name: 'Bot', email: 'b@b.de', nachricht: 'x', dsgvo: true, website: 'spam' } })).json.ok, true);
  assert.equal(ctx.db.all('SELECT 1 FROM forms').length, 1);
});
