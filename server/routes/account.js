'use strict';
const express = require('express');
const cfg = require('../config'); const A = require('../auth'); const { esc } = require('../money');
module.exports = (ctx) => {
  const { db, orders, mail } = ctx; const r = express.Router();
  const wrap = (fn) => (req, res) => Promise.resolve().then(() => fn(req, res)).catch(e => { if (e.status) return res.status(e.status).json({ error: e.message }); console.error(e); res.status(500).json({ error: 'Serverfehler' }); });
  const pub = (u) => ({ id: u.id, email: u.email, first: u.first, last: u.last, phone: u.phone, addr: JSON.parse(u.addr || '{}'), is_admin: !!u.is_admin });
  r.get('/api/me', (req, res) => res.json({ user: req.user ? pub(req.user) : null }));
  r.post('/api/register', A.limiter(db, 'reg', 10, 3600), wrap(async (req, res) => {
    const b = req.body || {}; const email = orders.str(b.email, 120).toLowerCase(); if (!orders.EMAIL.test(email)) return res.status(400).json({ error: 'Bitte gültige E-Mail angeben.' });
    if (String(b.password || '').length < 8) return res.status(400).json({ error: 'Das Passwort muss mindestens 8 Zeichen haben.' });
    if (db.get('SELECT 1 FROM customers WHERE email=?', email)) return res.status(409).json({ error: 'Für diese E-Mail gibt es bereits ein Konto. Bitte anmelden.' });
    const r2 = db.run('INSERT INTO customers(email,pw,first,last,phone,created_at) VALUES(?,?,?,?,?,?)', email, A.hash(b.password), orders.str(b.first, 60), orders.str(b.last, 60), orders.str(b.phone, 40), Date.now());
    db.run('UPDATE orders SET customer_id=? WHERE email=? AND customer_id IS NULL', r2.lastInsertRowid, email);
    A.createSession(db, res, r2.lastInsertRowid); const u = db.get('SELECT * FROM customers WHERE id=?', r2.lastInsertRowid);
    await mail.send({ to: email, subject: 'Willkommen bei Italia Camper 24', text: 'Ihr Kundenkonto wurde angelegt.', html: mail.wrap('Willkommen bei Italia Camper 24', `<p>Ihr Kundenkonto wurde angelegt. Hier sehen Sie Ihre Bestellungen und Rechnungen: <a href="${cfg.baseUrl}/konto.html">Zum Konto</a></p>`) });
    res.json({ user: pub(u) });
  }));
  r.post('/api/login', A.limiter(db, 'login', 15, 900), wrap((req, res) => {
    const email = orders.str(req.body.email, 120).toLowerCase(); const u = db.get('SELECT * FROM customers WHERE email=?', email);
    if (!u || !A.verify(String(req.body.password || ''), u.pw)) return res.status(401).json({ error: 'E-Mail oder Passwort falsch.' });
    A.createSession(db, res, u.id); res.json({ user: pub(u) });
  }));
  r.post('/api/logout', (req, res) => { A.destroySession(db, req, res); res.json({ ok: true }); });
  r.put('/api/me', A.requireUser, wrap((req, res) => {
    const b = req.body || {}; const addr = { billing: b.billing || {}, shipping: b.shipping || {} };
    db.run('UPDATE customers SET first=?,last=?,phone=?,addr=? WHERE id=?', orders.str(b.first, 60), orders.str(b.last, 60), orders.str(b.phone, 40), JSON.stringify(addr).slice(0, 4000), req.user.id);
    res.json({ user: pub(db.get('SELECT * FROM customers WHERE id=?', req.user.id)) });
  }));
  r.post('/api/me/password', A.requireUser, A.limiter(db, 'pwchg', 10, 900), wrap((req, res) => {
    if (!A.verify(String(req.body.old || ''), req.user.pw)) return res.status(400).json({ error: 'Aktuelles Passwort falsch.' }); if (String(req.body.password || '').length < 8) return res.status(400).json({ error: 'Mindestens 8 Zeichen.' });
    db.run('UPDATE customers SET pw=? WHERE id=?', A.hash(req.body.password), req.user.id); res.json({ ok: true });
  }));
  r.get('/api/me/orders', A.requireUser, (req, res) => res.json({ orders: db.all('SELECT number,token,status,total,payment_method,payment_status,created_at,invoice_no FROM orders WHERE customer_id=? OR email=? ORDER BY id DESC LIMIT 200', req.user.id, req.user.email).map(o => ({ ...o, statusText: orders.NAMES[o.status], payment: orders.PAY[o.payment_method] })) }));
  r.post('/api/password/forgot', A.limiter(db, 'forgot', 5, 3600), wrap(async (req, res) => {
    const email = orders.str(req.body.email, 120).toLowerCase(); const u = db.get('SELECT * FROM customers WHERE email=?', email);
    if (u) { const t = A.rnd(32); db.run('UPDATE customers SET reset_token=?, reset_exp=? WHERE id=?', A.sha(t), Date.now() + 3600e3, u.id);
      const link = `${cfg.baseUrl}/passwort-zuruecksetzen.html?t=${t}`; await mail.send({ to: email, subject: 'Passwort zurücksetzen – Italia Camper 24', text: `Passwort zurücksetzen (1 Stunde gültig): ${link}`, html: mail.wrap('Passwort zurücksetzen', `<p>Über diesen Link können Sie ein neues Passwort vergeben (1 Stunde gültig):</p><p><a href="${link}">${esc(link)}</a></p><p>Wenn Sie das nicht angefordert haben, ignorieren Sie diese Nachricht.</p>`) }); }
    res.json({ ok: true });
  }));
  r.post('/api/password/reset', A.limiter(db, 'reset', 10, 3600), wrap((req, res) => {
    const u = db.get('SELECT * FROM customers WHERE reset_token=? AND reset_exp>?', A.sha(String(req.body.token || '')), Date.now()); if (!u) return res.status(400).json({ error: 'Der Link ist ungültig oder abgelaufen.' });
    if (String(req.body.password || '').length < 8) return res.status(400).json({ error: 'Mindestens 8 Zeichen.' });
    db.run('UPDATE customers SET pw=?, reset_token=NULL, reset_exp=NULL WHERE id=?', A.hash(req.body.password), u.id); db.run('DELETE FROM sessions WHERE customer_id=?', u.id); res.json({ ok: true });
  }));
  return r;
};
