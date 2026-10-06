'use strict';
const nodemailer = require('nodemailer');
const cfg = require('./config'); const { esc } = require('./money');
function create(db) {
  const transport = cfg.mail.host ? nodemailer.createTransport({ host: cfg.mail.host, port: cfg.mail.port, secure: cfg.mail.secure, auth: cfg.mail.user ? { user: cfg.mail.user, pass: cfg.mail.pass } : undefined }) : null;
  async function send({ to, subject, text, html, replyTo, attachments }) {
    const row = db.run('INSERT INTO mail_log(at,to_addr,subject,body,status) VALUES(?,?,?,?,?)', Date.now(), to, subject, text || '', transport ? 'queued' : 'nicht konfiguriert');
    if (!transport) { if (!cfg.prod) console.log(`[mail] ${to}: ${subject}`); return false; }
    try { await transport.sendMail({ from: cfg.mail.from, to, subject, text, html, replyTo, attachments }); db.run("UPDATE mail_log SET status='gesendet' WHERE id=?", row.lastInsertRowid); return true; }
    catch (e) { db.run("UPDATE mail_log SET status='Fehler', error=? WHERE id=?", String(e.message).slice(0, 300), row.lastInsertRowid); console.error('[mail] Fehler', e.message); return false; }
  }
  const wrap = (title, inner) => `<!doctype html><html lang="de"><body style="margin:0;background:#f4f5f0;font-family:Arial,Helvetica,sans-serif;color:#14241b"><table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden"><tr><td style="height:6px;background:linear-gradient(90deg,#008c45 33%,#f4f5f0 33% 66%,#cd212a 66%)"></td></tr>
<tr><td style="padding:24px 28px"><h1 style="font-size:20px;margin:0 0 16px;color:#06301b">${esc(title)}</h1>${inner}<p style="color:#44564c;font-size:13px;margin-top:28px;border-top:1px solid #dce6e0;padding-top:14px">${esc(cfg.company.name)} · ${esc(cfg.company.owner)} · ${esc(cfg.company.street)}, ${esc(cfg.company.zip)} ${esc(cfg.company.city)}<br>Tel. ${esc(cfg.company.phone)} · <a href="mailto:${cfg.company.email}">${cfg.company.email}</a></p></td></tr></table></td></tr></table></body></html>`;
  return { send, wrap };
}
module.exports = { create };
