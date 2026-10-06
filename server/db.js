'use strict';
const fs = require('fs'); const path = require('path');
const { DatabaseSync } = require('node:sqlite');
const cfg = require('./config');
function open(file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;');
  db.exec(`
  CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT NOT NULL, first TEXT DEFAULT '', last TEXT DEFAULT '', phone TEXT DEFAULT '',
    addr TEXT DEFAULT '{}', is_admin INTEGER DEFAULT 0, reset_token TEXT, reset_exp INTEGER, created_at INTEGER NOT NULL, last_login INTEGER);
  CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE, exp INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, number TEXT UNIQUE NOT NULL, token TEXT NOT NULL, customer_id INTEGER REFERENCES customers(id), email TEXT NOT NULL,
    status TEXT NOT NULL, payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'offen', payment_ref TEXT, payment_ref2 TEXT,
    items TEXT NOT NULL, subtotal REAL NOT NULL, discount REAL NOT NULL DEFAULT 0, shipping_cost REAL NOT NULL DEFAULT 0, total REAL NOT NULL, vat REAL NOT NULL,
    coupon TEXT, customer TEXT NOT NULL, billing TEXT NOT NULL, shipping TEXT NOT NULL, vehicle TEXT DEFAULT '', note TEXT DEFAULT '',
    tracking TEXT DEFAULT '', carrier TEXT DEFAULT '', invoice_no TEXT, invoice_date INTEGER, created_at INTEGER NOT NULL, paid_at INTEGER, shipped_at INTEGER, ip TEXT);
  CREATE INDEX IF NOT EXISTS orders_email ON orders(email); CREATE INDEX IF NOT EXISTS orders_cust ON orders(customer_id); CREATE INDEX IF NOT EXISTS orders_status ON orders(status);
  CREATE TABLE IF NOT EXISTS order_events(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE, at INTEGER NOT NULL, type TEXT, text TEXT);
  CREATE TABLE IF NOT EXISTS forms(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL, status TEXT DEFAULT 'neu', created_at INTEGER NOT NULL, ip TEXT);
  CREATE TABLE IF NOT EXISTS coupons(code TEXT PRIMARY KEY, type TEXT NOT NULL, value REAL NOT NULL, min_total REAL DEFAULT 0, active INTEGER DEFAULT 1, uses INTEGER DEFAULT 0, max_uses INTEGER, expires INTEGER);
  CREATE TABLE IF NOT EXISTS sku_overrides(sku TEXT PRIMARY KEY, price REAL, active INTEGER DEFAULT 1);
  CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
  CREATE TABLE IF NOT EXISTS mail_log(id INTEGER PRIMARY KEY, at INTEGER NOT NULL, to_addr TEXT, subject TEXT, body TEXT, status TEXT, error TEXT);
  CREATE TABLE IF NOT EXISTS rate(k TEXT PRIMARY KEY, n INTEGER, exp INTEGER);
  `);
  const q = (sql) => db.prepare(sql);
  return {
    raw: db,
    get: (sql, ...a) => q(sql).get(...a), all: (sql, ...a) => q(sql).all(...a), run: (sql, ...a) => q(sql).run(...a),
    tx(fn) { db.exec('BEGIN IMMEDIATE'); try { const r = fn(); db.exec('COMMIT'); return r; } catch (e) { db.exec('ROLLBACK'); throw e; } },
    setting(k, d = '') { const r = q('SELECT v FROM settings WHERE k=?').get(k); return r ? r.v : d; },
    setSetting(k, v) { q('INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v').run(k, String(v)); },
    close() { db.close(); },
  };
}
module.exports = { open, defaultFile: () => path.join(cfg.dataDir, 'shop.db') };
