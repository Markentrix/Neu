'use strict';
const express = require('express'); const path = require('path'); const fs = require('fs'); const { spawn } = require('child_process');
const cfg = require('../config'); const A = require('../auth'); const { stripe, paypal } = require('../payments'); const invoice = require('../invoice'); const { esc, eur } = require('../money');
module.exports = (ctx) => {
  const { db, catalog, orders, mail } = ctx; const r = express.Router();
  const wrap = (fn) => (req, res) => Promise.resolve().then(() => fn(req, res)).catch(e => { if (e.status) return res.status(e.status).json({ error: e.message }); console.error(e); res.status(500).json({ error: e.message || 'Serverfehler' }); });
  r.post('/api/admin/login', A.limiter(db, 'adminlogin', 10, 900), wrap((req, res) => {
    const u = db.get('SELECT * FROM customers WHERE email=? AND is_admin=1', orders.str(req.body.email, 120).toLowerCase());
    if (!u || !A.verify(String(req.body.password || ''), u.pw)) return res.status(401).json({ error: 'Zugangsdaten falsch.' }); A.createSession(db, res, u.id, 1); res.json({ ok: true });
  }));
  r.use('/api/admin', A.requireAdmin);
  const parse = (o) => ({ ...o, items: JSON.parse(o.items), customer: JSON.parse(o.customer), billing: JSON.parse(o.billing), shipping: JSON.parse(o.shipping) });
  r.get('/api/admin/stats', (req, res) => {
    const d30 = Date.now() - 30 * 864e5; const one = (s, ...a) => db.get(s, ...a);
    res.json({ neu: one("SELECT COUNT(*) n FROM orders WHERE status IN ('neu','bezahlt','pruefung')").n, offen: one("SELECT COUNT(*) n FROM orders WHERE status='wartet_auf_zahlung'").n, bearbeitung: one("SELECT COUNT(*) n FROM orders WHERE status='in_bearbeitung'").n,
      revenue30: one("SELECT COALESCE(SUM(total),0) s FROM orders WHERE payment_status='bezahlt' AND created_at>?", d30).s, orders30: one("SELECT COUNT(*) n FROM orders WHERE created_at>? AND status!='storniert'", d30).n,
      forms: one("SELECT COUNT(*) n FROM forms WHERE status='neu'").n, customers: one('SELECT COUNT(*) n FROM customers WHERE is_admin=0').n, stripe: stripe.enabled(), paypal: paypal.enabled(), smtp: !!cfg.mail.host, bank: !!cfg.bank.iban,
      latest: db.all('SELECT number,email,total,status,payment_method,created_at FROM orders ORDER BY id DESC LIMIT 8') });
  });
  r.get('/api/admin/orders', (req, res) => {
    const w = []; const a = []; if (req.query.status) { w.push('status=?'); a.push(req.query.status); } if (req.query.q) { w.push('(number LIKE ? OR email LIKE ? OR customer LIKE ? OR billing LIKE ?)'); const q = `%${String(req.query.q).slice(0, 60)}%`; a.push(q, q, q, q); }
    const page = Math.max(1, +req.query.page || 1); const where = w.length ? 'WHERE ' + w.join(' AND ') : '';
    const total = db.get(`SELECT COUNT(*) n FROM orders ${where}`, ...a).n;
    res.json({ total, page, rows: db.all(`SELECT number,email,status,payment_method,payment_status,total,created_at,customer,invoice_no FROM orders ${where} ORDER BY id DESC LIMIT 50 OFFSET ?`, ...a, (page - 1) * 50).map(o => ({ ...o, customer: JSON.parse(o.customer) })) });
  });
  r.get('/api/admin/orders.csv', (req, res) => {
    const rows = db.all('SELECT * FROM orders ORDER BY id DESC'); const q = (v) => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const csv = ['Bestellnr;Datum;Status;Zahlart;Zahlstatus;E-Mail;Name;Gesamt;MwSt;Rechnungsnr', ...rows.map(o => { const c = JSON.parse(o.customer); return [o.number, new Date(o.created_at).toISOString(), o.status, o.payment_method, o.payment_status, o.email, `${c.first} ${c.last}`, o.total.toFixed(2).replace('.', ','), o.vat.toFixed(2).replace('.', ','), o.invoice_no || ''].map(q).join(';'); })].join('\r\n');
    res.setHeader('Content-Type', 'text/csv; charset=utf-8'); res.setHeader('Content-Disposition', 'attachment; filename="bestellungen.csv"'); res.send('﻿' + csv);
  });
  const need = (n) => { const o = orders.get(n); if (!o) throw Object.assign(new Error('Bestellung nicht gefunden'), { status: 404 }); return o; };
  r.get('/api/admin/orders/:n', wrap((req, res) => { const o = need(req.params.n); res.json({ order: parse(o), events: db.all('SELECT at,type,text FROM order_events WHERE order_id=? ORDER BY id', o.id), names: orders.NAMES, pay: orders.PAY }); }));
  r.post('/api/admin/orders/:n/status', wrap(async (req, res) => { need(req.params.n); const o = await orders.setStatus(req.params.n, req.body.status, { tracking: req.body.tracking, carrier: req.body.carrier }); res.json({ order: parse(o) }); }));
  r.post('/api/admin/orders/:n/paid', wrap(async (req, res) => { need(req.params.n); const o = await orders.markPaid(req.params.n, req.body.ref || null, null, 'manuell durch Admin'); res.json({ order: parse(o) }); }));
  r.post('/api/admin/orders/:n/note', wrap((req, res) => { const o = need(req.params.n); orders.event(o.id, 'notiz', orders.str(req.body.text, 1000)); res.json({ ok: true }); }));
  r.post('/api/admin/orders/:n/mail', wrap(async (req, res) => { const o = need(req.params.n); const t = orders.str(req.body.text, 5000); const s = orders.str(req.body.subject, 150) || `Ihre Bestellung ${o.number}`; if (!t) return res.status(400).json({ error: 'Text fehlt' });
    await mail.send({ to: o.email, subject: s, text: t, html: mail.wrap(s, t.split('\n').map(l => `<p>${esc(l)}</p>`).join('')) }); orders.event(o.id, 'mail', `E-Mail gesendet: ${s}`); res.json({ ok: true }); }));
  r.post('/api/admin/orders/:n/refund', wrap(async (req, res) => {
    const o = need(req.params.n); const amount = req.body.amount ? +req.body.amount : null; if (amount && (amount <= 0 || amount > o.total)) return res.status(400).json({ error: 'Ungültiger Betrag' });
    if (o.payment_status !== 'bezahlt') return res.status(400).json({ error: 'Nur bezahlte Bestellungen können erstattet werden.' });
    if (o.payment_method === 'card') { if (!o.payment_ref2) return res.status(400).json({ error: 'Keine Zahlungsreferenz.' }); await stripe.refund(o.payment_ref2, amount); }
    else if (o.payment_method === 'paypal') { if (!o.payment_ref2) return res.status(400).json({ error: 'Keine Capture-ID.' }); await paypal.refund(o.payment_ref2, amount); }
    else orders.event(o.id, 'erstattung', 'Erstattung manuell auszuführen (Überweisung/Rechnung)');
    if (!amount || amount >= o.total) { db.run("UPDATE orders SET payment_status='erstattet', status='erstattet' WHERE id=?", o.id); } orders.event(o.id, 'erstattung', `Erstattung ${amount ? eur(amount) : 'komplett'} ausgelöst`); res.json({ ok: true });
  }));
  r.get('/api/admin/orders/:n/invoice.pdf', wrap(async (req, res) => { let o = need(req.params.n); o = orders.ensureInvoice(o); const pdf = await invoice.build(o, cfg.bank); res.setHeader('Content-Type', 'application/pdf'); res.send(pdf); }));
  // Produkte / Preise
  r.get('/api/admin/products', (req, res) => {
    const q = String(req.query.q || '').toLowerCase().slice(0, 60); const cat = catalog.raw; const out = [];
    for (const p of cat.products) { if (q && !(p.name + ' ' + p.slug).toLowerCase().includes(q)) continue; const skus = [...catalog.skus.values()].filter(s => s.product === p.slug); out.push({ slug: p.slug, name: p.name, cat: p.cat, skus: skus.map(s => ({ sku: s.sku, name: s.name, price: s.price, base: s.base, active: s.active, kind: s.kind })) }); if (out.length >= 80) break; }
    res.json({ products: out, overrides: db.get('SELECT COUNT(*) n FROM sku_overrides').n });
  });
  r.put('/api/admin/sku', wrap((req, res) => {
    const sku = String(req.body.sku || ''); const s = catalog.skus.get(sku); if (!s) return res.status(404).json({ error: 'SKU unbekannt' });
    const price = req.body.price === '' || req.body.price == null ? null : +req.body.price; if (price != null && !(price > 0 && price < 100000)) return res.status(400).json({ error: 'Ungültiger Preis' });
    db.run('INSERT INTO sku_overrides(sku,price,active) VALUES(?,?,?) ON CONFLICT(sku) DO UPDATE SET price=excluded.price, active=excluded.active', sku, price, req.body.active === false || req.body.active === 0 ? 0 : 1); catalog.reload(); res.json({ ok: true, sku: catalog.skus.get(sku) });
  }));
  let regen = { running: false, last: null };
  r.post('/api/admin/regenerate', wrap((req, res) => {
    if (regen.running) return res.status(409).json({ error: 'Läuft bereits' }); const script = path.join(cfg.appRoot, 'src', 'build.py'); if (!fs.existsSync(script)) return res.status(501).json({ error: 'Generator nicht vorhanden' });
    const ov = {}; for (const o of db.all('SELECT * FROM sku_overrides')) ov[o.sku] = { price: o.price, active: !!o.active }; const f = path.join(cfg.dataDir, 'overrides.json'); fs.mkdirSync(cfg.dataDir, { recursive: true }); fs.writeFileSync(f, JSON.stringify(ov));
    regen = { running: true, last: null }; const p = spawn('python3', [script], { env: { ...process.env, IC_OUT: cfg.siteDir, IC_OVERRIDES: f }, cwd: cfg.appRoot }); let out = '';
    p.stdout.on('data', d => out += d); p.stderr.on('data', d => out += d); p.on('close', code => { regen = { running: false, last: { code, out: out.slice(-400), at: Date.now() } }; });
    res.json({ started: true });
  }));
  r.get('/api/admin/regenerate', (req, res) => res.json(regen));
  // Kunden / Formulare / Gutscheine / Einstellungen / Mails
  r.get('/api/admin/customers', (req, res) => res.json({ rows: db.all('SELECT c.id,c.email,c.first,c.last,c.phone,c.created_at,c.last_login,(SELECT COUNT(*) FROM orders o WHERE o.customer_id=c.id) orders FROM customers c WHERE c.is_admin=0 ORDER BY c.id DESC LIMIT 300') }));
  r.get('/api/admin/forms', (req, res) => res.json({ rows: db.all('SELECT * FROM forms ORDER BY id DESC LIMIT 200').map(f => ({ ...f, data: JSON.parse(f.data) })) }));
  r.put('/api/admin/forms/:id', wrap((req, res) => { db.run('UPDATE forms SET status=? WHERE id=?', ['neu', 'in_arbeit', 'erledigt'].includes(req.body.status) ? req.body.status : 'neu', +req.params.id); res.json({ ok: true }); }));
  r.get('/api/admin/coupons', (req, res) => res.json({ rows: db.all('SELECT * FROM coupons ORDER BY code') }));
  r.post('/api/admin/coupons', wrap((req, res) => { const b = req.body || {}; const code = String(b.code || '').trim().toUpperCase().slice(0, 30); if (!/^[A-Z0-9_-]{3,30}$/.test(code) || !(+b.value > 0) || !['percent', 'fixed'].includes(b.type)) return res.status(400).json({ error: 'Code (3–30 Zeichen), Typ und Wert prüfen.' });
    if (b.type === 'percent' && +b.value > 100) return res.status(400).json({ error: 'Max. 100 %' }); db.run('INSERT INTO coupons(code,type,value,min_total,active,max_uses,expires) VALUES(?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET type=excluded.type,value=excluded.value,min_total=excluded.min_total,active=excluded.active,max_uses=excluded.max_uses,expires=excluded.expires',
      code, b.type, +b.value, +b.min_total || 0, b.active === false ? 0 : 1, b.max_uses ? +b.max_uses : null, b.expires ? Date.parse(b.expires) : null); res.json({ ok: true }); }));
  r.delete('/api/admin/coupons/:code', wrap((req, res) => { db.run('DELETE FROM coupons WHERE code=?', req.params.code); res.json({ ok: true }); }));
  const SET = ['pay_paypal', 'pay_card', 'pay_transfer', 'pay_invoice', 'shipping_cost', 'free_shipping_from', 'invoice_max'];
  r.get('/api/admin/settings', (req, res) => { const s = {}; SET.forEach(k => s[k] = db.setting(k, k.startsWith('pay_') ? '1' : (k === 'invoice_max' ? '5000' : '0'))); res.json({ settings: s, env: { stripe: stripe.enabled(), paypal: paypal.enabled(), smtp: !!cfg.mail.host, bank: !!cfg.bank.iban, baseUrl: cfg.baseUrl } }); });
  r.put('/api/admin/settings', wrap((req, res) => { for (const k of SET) if (req.body[k] != null) db.setSetting(k, String(req.body[k]).slice(0, 20)); res.json({ ok: true }); }));
  r.get('/api/admin/mails', (req, res) => res.json({ rows: db.all('SELECT id,at,to_addr,subject,status,error FROM mail_log ORDER BY id DESC LIMIT 100') }));
  r.post('/api/admin/password', wrap((req, res) => { if (!A.verify(String(req.body.old || ''), req.user.pw)) return res.status(400).json({ error: 'Aktuelles Passwort falsch' }); if (String(req.body.password || '').length < 12) return res.status(400).json({ error: 'Mindestens 12 Zeichen' }); db.run('UPDATE customers SET pw=? WHERE id=?', A.hash(req.body.password), req.user.id); res.json({ ok: true }); }));
  return r;
};
