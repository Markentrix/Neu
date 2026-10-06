'use strict';
const crypto = require('crypto');
const cfg = require('./config');
const hash = (pw) => { const salt = crypto.randomBytes(16); const h = crypto.scryptSync(pw, salt, 64, { N: 16384, r: 8, p: 1 }); return `s1$${salt.toString('hex')}$${h.toString('hex')}`; };
const verify = (pw, stored) => { try { const [v, s, h] = stored.split('$'); if (v !== 's1') return false; const t = crypto.scryptSync(pw, Buffer.from(s, 'hex'), 64, { N: 16384, r: 8, p: 1 }); return crypto.timingSafeEqual(t, Buffer.from(h, 'hex')); } catch { return false; } };
const rnd = (n = 32) => crypto.randomBytes(n).toString('base64url');
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');
function parseCookies(req) { const o = {}; (req.headers.cookie || '').split(';').forEach(p => { const i = p.indexOf('='); if (i > 0) o[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim()); }); return o; }
function setCookie(res, name, val, { maxAge, path = '/' } = {}) {
  const parts = [`${name}=${encodeURIComponent(val)}`, `Path=${path}`, 'HttpOnly', 'SameSite=Lax']; if (maxAge != null) parts.push(`Max-Age=${maxAge}`); if (cfg.prod || cfg.baseUrl.startsWith('https')) parts.push('Secure');
  const prev = res.getHeader('Set-Cookie') || []; res.setHeader('Set-Cookie', [].concat(prev, parts.join('; ')));
}
function createSession(db, res, customerId, days = 30) {
  const token = rnd(32), exp = Date.now() + days * 864e5; db.run('INSERT INTO sessions(token,customer_id,exp) VALUES(?,?,?)', sha(token), customerId, exp);
  setCookie(res, 'ic_sess', token, { maxAge: days * 86400 }); db.run('UPDATE customers SET last_login=? WHERE id=?', Date.now(), customerId);
}
function destroySession(db, req, res) { const t = parseCookies(req).ic_sess; if (t) db.run('DELETE FROM sessions WHERE token=?', sha(t)); setCookie(res, 'ic_sess', '', { maxAge: 0 }); }
function loader(db) {
  return (req, res, next) => {
    req.user = null; const t = parseCookies(req).ic_sess;
    if (t) { const r = db.get('SELECT c.*, s.exp FROM sessions s JOIN customers c ON c.id=s.customer_id WHERE s.token=?', sha(t)); if (r && r.exp > Date.now()) req.user = r; else if (r) db.run('DELETE FROM sessions WHERE token=?', sha(t)); }
    next();
  };
}
// CSRF: Zustandsändernde Requests brauchen den Custom-Header (löst Preflight aus, Cross-Site nicht möglich) + gleiche Origin
function csrf(req, res, next) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) return next();
  if (req.path.startsWith('/api/webhooks/')) return next();
  const o = req.headers.origin; if (o && o.replace(/\/$/, '') !== cfg.baseUrl && !/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(o)) return res.status(403).json({ error: 'Origin nicht erlaubt' });
  if (req.headers['x-requested-with'] !== 'ic') return res.status(403).json({ error: 'CSRF-Schutz: Header fehlt' });
  next();
}
function rateLimit(db, key, max, windowSec) {
  const now = Date.now(); const r = db.get('SELECT * FROM rate WHERE k=?', key);
  if (!r || r.exp < now) { db.run('INSERT INTO rate(k,n,exp) VALUES(?,1,?) ON CONFLICT(k) DO UPDATE SET n=1,exp=excluded.exp', key, now + windowSec * 1000); return true; }
  if (r.n >= max) return false; db.run('UPDATE rate SET n=n+1 WHERE k=?', key); return true;
}
const limiter = (db, name, max, windowSec) => (req, res, next) => { const ip = (req.ip || 'x'); if (!rateLimit(db, `${name}:${ip}`, max, windowSec)) return res.status(429).json({ error: 'Zu viele Anfragen – bitte später erneut versuchen.' }); next(); };
const requireUser = (req, res, next) => req.user ? next() : res.status(401).json({ error: 'Bitte anmelden.' });
const requireAdmin = (req, res, next) => (req.user && req.user.is_admin) ? next() : res.status(401).json({ error: 'Kein Zugriff.' });
module.exports = { hash, verify, rnd, sha, parseCookies, setCookie, createSession, destroySession, loader, csrf, limiter, rateLimit, requireUser, requireAdmin };
