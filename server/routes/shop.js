'use strict';
const express = require('express');
const cfg = require('../config'); const A = require('../auth'); const { stripe, paypal } = require('../payments'); const invoice = require('../invoice');
module.exports = (ctx) => {
  const { db, catalog, orders, mail } = ctx; const r = express.Router();
  const wrap = (fn) => (req, res) => Promise.resolve().then(() => fn(req, res)).catch(e => { if (e.status) return res.status(e.status).json({ error: e.message, sku: e.sku }); console.error(e); res.status(500).json({ error: 'Serverfehler – bitte versuchen Sie es erneut.' }); });
  // Warenkorb serverseitig neu bewerten (Preise/Namen sind maßgeblich, Client-Preise werden ignoriert)
  r.post('/api/cart/quote', A.limiter(db, 'quote', 120, 60), wrap((req, res) => {
    const p = orders.price(req.body.items, req.body.coupon, req.body.country); res.json({ ...p, methods: { ...orders.methods(), card: orders.methods().card && stripe.enabled(), paypal: orders.methods().paypal && paypal.enabled() } });
  }));
  r.get('/api/config', (req, res) => res.json({ methods: { ...orders.methods(), card: orders.methods().card && stripe.enabled(), paypal: orders.methods().paypal && paypal.enabled() }, freeShipping: true }));
  r.post('/api/checkout', A.limiter(db, 'checkout', 20, 600), wrap(async (req, res) => {
    const b = req.body || {}; const { order, pricing } = orders.create(b, req.user, req.ip);
    // optional Kundenkonto anlegen
    if (b.createAccount && !req.user && b.password) {
      try { if (String(b.password).length < 8) throw new Error('pw'); if (!db.get('SELECT 1 FROM customers WHERE email=?', order.email)) { const c = JSON.parse(order.customer);
        const r2 = db.run('INSERT INTO customers(email,pw,first,last,phone,addr,created_at) VALUES(?,?,?,?,?,?,?)', order.email, A.hash(b.password), c.first, c.last, c.phone, JSON.stringify({ billing: JSON.parse(order.billing), shipping: JSON.parse(order.shipping) }), Date.now());
        db.run('UPDATE orders SET customer_id=? WHERE id=?', r2.lastInsertRowid, order.id); A.createSession(db, res, r2.lastInsertRowid); } } catch (e) { /* Konto optional */ }
    }
    const out = { number: order.number, token: order.token }; const next = `bestellung.html?n=${order.number}&t=${order.token}`;
    const fresh = () => orders.get(order.number);
    try {
      if (order.payment_method === 'card') { const s = await stripe.createSession(orders.forPay(order)); db.run('UPDATE orders SET payment_ref=? WHERE id=?', s.id, order.id); orders.event(order.id, 'zahlung', 'Stripe-Checkout gestartet'); out.redirect = s.url; }
      else if (order.payment_method === 'paypal') { const s = await paypal.createOrder(orders.forPay(order)); if (!s.url) throw new Error('PayPal-Link fehlt'); db.run('UPDATE orders SET payment_ref=? WHERE id=?', s.id, order.id); orders.event(order.id, 'zahlung', 'PayPal-Zahlung gestartet'); out.redirect = s.url; }
      else out.redirect = next;
    } catch (e) {
      db.run("UPDATE orders SET payment_status='fehlgeschlagen', status='storniert' WHERE id=?", order.id); orders.event(order.id, 'fehler', 'Zahlungsstart fehlgeschlagen: ' + e.message);
      return res.status(502).json({ error: 'Die Zahlung konnte nicht gestartet werden. Bitte andere Zahlart wählen oder uns anrufen.' });
    }
    if (!['card', 'paypal'].includes(order.payment_method)) await orders.notify(fresh(), 'created'); else await orders.notify(fresh(), 'created');
    res.json(out);
  }));
  const allowed = (req, o) => o && ((req.query.t && req.query.t === o.token) || (req.user && (req.user.is_admin || req.user.id === o.customer_id)));
  r.get('/api/order/:n', wrap(async (req, res) => {
    let o = orders.get(req.params.n); if (!allowed(req, o)) return res.status(404).json({ error: 'Bestellung nicht gefunden.' });
    // Rückkehr von Stripe: Zahlung aktiv prüfen, falls Webhook noch nicht da ist
    if (o.payment_method === 'card' && o.payment_status === 'offen' && o.payment_ref && stripe.enabled() && req.query.paid) { try { const s = await stripe.getSession(o.payment_ref); if (s.payment_status === 'paid') o = await orders.markPaid(o.number, o.payment_ref, s.payment_intent, 'Stripe'); } catch (e) { } }
    res.json(orders.view(o));
  }));
  r.get('/api/order/:n/invoice.pdf', wrap(async (req, res) => {
    let o = orders.get(req.params.n); if (!allowed(req, o)) return res.status(404).send('Nicht gefunden');
    if (o.payment_status === 'bezahlt' || o.payment_method === 'invoice') o = orders.ensureInvoice(o);
    const pdf = await invoice.build(o, cfg.bank); res.setHeader('Content-Type', 'application/pdf'); res.setHeader('Content-Disposition', `inline; filename="${o.invoice_no || o.number}.pdf"`); res.send(pdf);
  }));
  // PayPal-Rückkehr: Zahlung einziehen
  r.get('/api/paypal/return', wrap(async (req, res) => {
    const o = orders.get(String(req.query.n || '')); if (!o || o.token !== req.query.t) return res.redirect('/bestellung.html?error=1');
    try { if (o.payment_status !== 'bezahlt') { const cap = await paypal.capture(o.payment_ref); const c = cap.purchase_units && cap.purchase_units[0] && cap.purchase_units[0].payments && cap.purchase_units[0].payments.captures && cap.purchase_units[0].payments.captures[0];
      if (cap.status === 'COMPLETED' && c) await orders.markPaid(o.number, o.payment_ref, c.id, 'PayPal'); else orders.event(o.id, 'zahlung', 'PayPal-Status: ' + cap.status); } }
    catch (e) { orders.event(o.id, 'fehler', 'PayPal-Capture fehlgeschlagen: ' + e.message); return res.redirect(`/bestellung.html?n=${o.number}&t=${o.token}&cancel=1`); }
    res.redirect(`/bestellung.html?n=${o.number}&t=${o.token}&paid=1`);
  }));
  // Stripe-Webhook (Rohdaten für Signatur)
  r.post('/api/webhooks/stripe', express.raw({ type: '*/*', limit: '1mb' }), wrap(async (req, res) => {
    const raw = req.body.toString('utf8'); if (!stripe.verifyWebhook(raw, req.headers['stripe-signature'])) return res.status(400).send('bad signature');
    const ev = JSON.parse(raw); const obj = ev.data && ev.data.object || {};
    if (ev.type === 'checkout.session.completed' || ev.type === 'checkout.session.async_payment_succeeded') { const n = obj.client_reference_id || (obj.metadata && obj.metadata.order); if (n && obj.payment_status === 'paid') await orders.markPaid(n, obj.id, obj.payment_intent, 'Stripe'); }
    if (ev.type === 'checkout.session.async_payment_failed' || ev.type === 'checkout.session.expired') { const n = obj.client_reference_id; const o = n && orders.get(n); if (o && o.payment_status === 'offen') { db.run("UPDATE orders SET payment_status='fehlgeschlagen' WHERE id=?", o.id); orders.event(o.id, 'zahlung', 'Zahlung nicht abgeschlossen (' + ev.type + ')'); } }
    res.json({ received: true });
  }));
  // Formulare: Angebot / Kontakt
  r.post('/api/forms/:kind', A.limiter(db, 'forms', 8, 600), wrap(async (req, res) => {
    const kind = req.params.kind === 'kontakt' ? 'kontakt' : 'angebot'; const b = req.body || {}; if (b.website) return res.json({ ok: true });
    const d = { name: orders.str(b.name, 100), email: orders.str(b.email, 120).toLowerCase(), tel: orders.str(b.tel, 40), produkt: orders.str(b.produkt, 120), fzg: orders.str(b.fzg, 120), bj: orders.str(b.bj, 120), betreff: orders.str(b.betreff, 100), nachricht: orders.str(b.nachricht, 3000) };
    if (!d.name || !orders.EMAIL.test(d.email) || !d.nachricht && !d.produkt) return res.status(400).json({ error: 'Bitte Name, gültige E-Mail und eine Nachricht angeben.' }); if (!b.dsgvo) return res.status(400).json({ error: 'Bitte der Datenschutzerklärung zustimmen.' });
    const row = db.run('INSERT INTO forms(kind,data,created_at,ip) VALUES(?,?,?,?)', kind, JSON.stringify(d), Date.now(), req.ip);
    await mail.send({ to: cfg.mail.notify, replyTo: d.email, subject: `${kind === 'angebot' ? 'Angebotsanfrage' : 'Kontaktanfrage'} von ${d.name}`, text: Object.entries(d).map(([k, v]) => `${k}: ${v}`).join('\n') + `\n\n${cfg.baseUrl}/admin/#/forms`,
      html: mail.wrap(kind === 'angebot' ? 'Neue Angebotsanfrage' : 'Neue Kontaktanfrage', Object.entries(d).filter(([, v]) => v).map(([k, v]) => `<p><strong>${k}:</strong> ${require('../money').esc(v)}</p>`).join('')) });
    await mail.send({ to: d.email, subject: 'Wir haben Ihre Anfrage erhalten – Italia Camper 24', text: `Hallo ${d.name},\n\nvielen Dank für Ihre Anfrage. Wir melden uns schnellstmöglich bei Ihnen.\n\nIhr Team von Italia Camper 24\n${cfg.company.phone}`,
      html: mail.wrap('Vielen Dank für Ihre Anfrage', `<p>Hallo ${require('../money').esc(d.name)},</p><p>wir haben Ihre Anfrage erhalten und melden uns schnellstmöglich bei Ihnen – auch am Wochenende.</p>`) });
    res.json({ ok: true, id: row.lastInsertRowid });
  }));
  return r;
};
