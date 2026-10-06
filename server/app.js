'use strict';
const express = require('express'); const path = require('path'); const fs = require('fs');
const cfg = require('./config'); const dbm = require('./db'); const A = require('./auth'); const catalogm = require('./catalog'); const mailm = require('./mail'); const ordersm = require('./orders');
function create(opts = {}) {
  const db = dbm.open(opts.dbFile || dbm.defaultFile()); const catalog = catalogm.load(db); const mail = mailm.create(db); const orders = ordersm.service(db, catalog, mail);
  // Admin-Konto aus Umgebungsvariablen anlegen/aktualisieren
  if (cfg.admin.email && cfg.admin.password) {
    const ex = db.get('SELECT * FROM customers WHERE email=?', cfg.admin.email.toLowerCase());
    if (!ex) db.run('INSERT INTO customers(email,pw,first,last,is_admin,created_at) VALUES(?,?,?,?,1,?)', cfg.admin.email.toLowerCase(), A.hash(cfg.admin.password), 'Admin', '', Date.now());
    else if (!A.verify(cfg.admin.password, ex.pw) || !ex.is_admin) db.run('UPDATE customers SET pw=?, is_admin=1 WHERE id=?', A.hash(cfg.admin.password), ex.id);
  }
  const app = express(); app.disable('x-powered-by'); app.set('trust proxy', 1);
  app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff'); res.setHeader('X-Frame-Options', 'DENY'); res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin'); res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    if (cfg.prod) res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    res.setHeader('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'");
    next();
  });
  app.get('/healthz', (req, res) => { try { db.get('SELECT 1'); res.json({ ok: true }); } catch (e) { res.status(500).json({ ok: false }); } });
  // 301-Weiterleitungen alter Jimdo-URLs (SEO-Migration)
  let redirects = {}; try { redirects = JSON.parse(fs.readFileSync(path.join(__dirname, 'redirects.json'), 'utf8')); } catch (e) { }
  app.use((req, res, next) => { if (req.method !== 'GET') return next(); const k = req.path.endsWith('/') || redirects[req.path] ? req.path : req.path; const t = redirects[k] || redirects[k.replace(/\/?$/, '/')]; if (t) return res.redirect(301, t); next(); });
  app.use(A.loader(db));
  const ctx = { db, catalog, orders, mail };
  const json = express.json({ limit: '100kb' });
  app.use('/api', (req, res, next) => req.path === '/webhooks/stripe' ? next() : json(req, res, next)); // Webhook braucht Rohdaten
  app.use(A.csrf);
  app.use(require('./routes/shop')(ctx)); app.use(require('./routes/account')(ctx)); app.use(require('./routes/admin')(ctx));
  app.use('/api', (req, res) => res.status(404).json({ error: 'Nicht gefunden' }));
  app.use('/admin', express.static(path.join(__dirname, 'admin'), { index: 'index.html', maxAge: 0 }));
  const site = opts.siteDir || cfg.siteDir;
  app.use(express.static(site, { extensions: ['html'], setHeaders: (res, p) => { if (/\.(webp|woff2|jpg|png|svg)$/.test(p)) res.setHeader('Cache-Control', 'public, max-age=2592000, immutable'); else if (/\.(css|js)$/.test(p)) res.setHeader('Cache-Control', 'public, max-age=3600'); else res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate'); } }));
  app.use((req, res) => { const f = path.join(site, '404.html'); res.status(404); fs.existsSync(f) ? res.sendFile(f) : res.send('404'); });
  app.use((err, req, res, next) => { if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'Ungültige Anfrage' }); console.error(err); res.status(500).json({ error: 'Serverfehler' }); });
  return { app, db, catalog, orders, mail };
}
module.exports = { create };
