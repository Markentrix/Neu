'use strict';
const crypto = require('crypto');
const cfg = require('./config'); const { round2, vatOf, eur, esc, fdate } = require('./money');
const NAMES = { neu: 'Neu', wartet_auf_zahlung: 'Wartet auf Zahlung', pruefung: 'Rechnungskauf – in Prüfung', bezahlt: 'Bezahlt', in_bearbeitung: 'In Bearbeitung', versendet: 'Versendet', abgeschlossen: 'Abgeschlossen', storniert: 'Storniert', erstattet: 'Erstattet' };
const PAY = { paypal: 'PayPal', card: 'Kreditkarte / Apple Pay / Google Pay', transfer: 'Überweisung (Vorkasse)', invoice: 'Rechnung' };
const str = (v, n = 200) => (v == null ? '' : String(v)).trim().slice(0, n);
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function service(db, catalog, mail) {
  const S = (k, d) => db.setting(k, d);
  const methods = () => ({ paypal: S('pay_paypal', '1') === '1', card: S('pay_card', '1') === '1', transfer: S('pay_transfer', '1') === '1', invoice: S('pay_invoice', '1') === '1' });
  function shippingFor(country, subtotal) { const free = +S('free_shipping_from', '0'); const base = +S('shipping_cost', '0'); return (free && subtotal >= free) || base === 0 ? 0 : base; }
  function price(items, couponCode, country) {
    if (!Array.isArray(items) || !items.length) throw Object.assign(new Error('Der Warenkorb ist leer.'), { status: 400 });
    if (items.length > 60) throw Object.assign(new Error('Zu viele Positionen.'), { status: 400 });
    const lines = []; const merged = new Map();
    for (const it of items) { const sku = str(it.sku, 160); const qty = Math.floor(+it.qty); if (!sku || !(qty >= 1) || qty > 20) throw Object.assign(new Error('Ungültige Position im Warenkorb.'), { status: 400 }); merged.set(sku, Math.min(20, (merged.get(sku) || 0) + qty)); }
    for (const [sku, qty] of merged) {
      const s = catalog.skus.get(sku); if (!s || !s.active) throw Object.assign(new Error(`Artikel nicht mehr verfügbar: ${sku}`), { status: 409, sku });
      lines.push({ sku, name: s.name, price: s.price, qty, product: s.product, kind: s.kind });
    }
    const subtotal = round2(lines.reduce((a, l) => a + l.price * l.qty, 0));
    let discount = 0, coupon = null;
    if (couponCode) {
      const c = db.get('SELECT * FROM coupons WHERE code=? COLLATE NOCASE', str(couponCode, 40));
      if (!c || !c.active || (c.expires && c.expires < Date.now()) || (c.max_uses && c.uses >= c.max_uses) || subtotal < (c.min_total || 0)) throw Object.assign(new Error('Gutscheincode ungültig oder nicht anwendbar.'), { status: 400 });
      discount = c.type === 'percent' ? round2(subtotal * c.value / 100) : Math.min(subtotal, c.value); coupon = c.code;
    }
    const shipping_cost = shippingFor(country, subtotal - discount); const total = round2(subtotal - discount + shipping_cost);
    return { lines, subtotal, discount, coupon, shipping_cost, total, vat: vatOf(total) };
  }
  const addr = (a, label) => {
    a = a || {}; const o = { first: str(a.first, 60), last: str(a.last, 60), company: str(a.company, 80), street: str(a.street, 100), zip: str(a.zip, 12), city: str(a.city, 60), country: a.country === 'AT' ? 'AT' : 'DE' };
    if (!o.first || !o.last || !o.street || !o.city || !/^\d{4,5}$/.test(o.zip)) throw Object.assign(new Error(`Bitte ${label} vollständig ausfüllen.`), { status: 400 });
    return o;
  };
  function number() { for (let i = 0; i < 20; i++) { const d = new Date(); const n = `IC-${String(d.getFullYear()).slice(2)}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}-${crypto.randomInt(1000, 9999)}`; if (!db.get('SELECT 1 FROM orders WHERE number=?', n)) return n; } throw new Error('Bestellnummer'); }
  function event(orderId, type, text) { db.run('INSERT INTO order_events(order_id,at,type,text) VALUES(?,?,?,?)', orderId, Date.now(), type, text); }
  function create(input, user, ip) {
    const method = str(input.payment, 20); const m = methods(); if (!PAY[method] || !m[method]) throw Object.assign(new Error('Diese Zahlart ist nicht verfügbar.'), { status: 400 });
    if (method === 'card' && !require('./payments').stripe.enabled()) throw Object.assign(new Error('Kartenzahlung ist derzeit nicht verfügbar.'), { status: 400 });
    if (method === 'paypal' && !require('./payments').paypal.enabled()) throw Object.assign(new Error('PayPal ist derzeit nicht verfügbar.'), { status: 400 });
    if (!input.accept) throw Object.assign(new Error('Bitte AGB und Widerrufsbelehrung bestätigen.'), { status: 400 });
    const c = input.customer || {}; const email = str(c.email, 120).toLowerCase(); if (!EMAIL.test(email)) throw Object.assign(new Error('Bitte eine gültige E-Mail-Adresse angeben.'), { status: 400 });
    const billing = addr(input.billing, 'die Rechnungsadresse'); const shipping = input.sameShipping === false ? addr(input.shipping, 'die Lieferadresse') : billing;
    const p = price(input.items, input.coupon, shipping.country);
    if (method === 'invoice' && p.total > +S('invoice_max', '5000')) throw Object.assign(new Error('Rechnungskauf ist für diesen Betrag nicht möglich – bitte andere Zahlart wählen.'), { status: 400 });
    const token = crypto.randomBytes(18).toString('base64url'); const num = number(); const now = Date.now();
    const status = method === 'transfer' ? 'wartet_auf_zahlung' : method === 'invoice' ? 'pruefung' : 'neu';
    const pstat = method === 'invoice' ? 'rechnung' : 'offen';
    const customer = { email, first: str(c.first || billing.first, 60), last: str(c.last || billing.last, 60), phone: str(c.phone, 40) };
    const id = db.tx(() => {
      const r = db.run(`INSERT INTO orders(number,token,customer_id,email,status,payment_method,payment_status,items,subtotal,discount,shipping_cost,total,vat,coupon,customer,billing,shipping,vehicle,note,created_at,ip)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`, num, token, user ? user.id : null, email, status, method, pstat, JSON.stringify(p.lines), p.subtotal, p.discount, p.shipping_cost, p.total, p.vat, p.coupon,
        JSON.stringify(customer), JSON.stringify(billing), JSON.stringify(shipping), str(input.vehicle, 160), str(input.note, 1000), now, ip || '');
      if (p.coupon) db.run('UPDATE coupons SET uses=uses+1 WHERE code=? COLLATE NOCASE', p.coupon);
      event(r.lastInsertRowid, 'angelegt', `Bestellung angelegt (${PAY[method]})`); return r.lastInsertRowid;
    });
    return { order: get(num), pricing: p, id };
  }
  const get = (num) => db.get('SELECT * FROM orders WHERE number=?', num);
  const forPay = (o) => ({ number: o.number, token: o.token, email: o.email, total: o.total, subtotal: o.subtotal, discount: o.discount, shipping_cost: o.shipping_cost, lines: JSON.parse(o.items) });
  const view = (o) => ({ number: o.number, status: o.status, statusText: NAMES[o.status] || o.status, payment_method: o.payment_method, payment: PAY[o.payment_method], payment_status: o.payment_status,
    items: JSON.parse(o.items), subtotal: o.subtotal, discount: o.discount, shipping_cost: o.shipping_cost, total: o.total, vat: o.vat, coupon: o.coupon, billing: JSON.parse(o.billing), shipping: JSON.parse(o.shipping),
    created_at: o.created_at, paid_at: o.paid_at, tracking: o.tracking, carrier: o.carrier, invoice_no: o.invoice_no, vehicle: o.vehicle, note: o.note,
    bank: ['transfer', 'invoice'].includes(o.payment_method) ? { holder: cfg.bank.holder, name: cfg.bank.name, iban: cfg.bank.iban, bic: cfg.bank.bic } : null });
  function nextInvoiceNo() { return db.tx(() => { const y = new Date().getFullYear(); const k = `inv_seq_${y}`; const n = +db.setting(k, '0') + 1; db.setSetting(k, n); return `RE-${y}-${String(n).padStart(5, '0')}`; }); }
  function ensureInvoice(o) { if (o.invoice_no) return o; const no = nextInvoiceNo(); db.run('UPDATE orders SET invoice_no=?, invoice_date=? WHERE id=?', no, Date.now(), o.id); return get(o.number); }
  async function markPaid(num, ref, ref2, source) {
    let o = get(num); if (!o) return null; if (o.payment_status === 'bezahlt') return o;
    db.run("UPDATE orders SET payment_status='bezahlt', paid_at=?, status=CASE WHEN status IN ('neu','wartet_auf_zahlung','pruefung') THEN 'bezahlt' ELSE status END, payment_ref=COALESCE(?,payment_ref), payment_ref2=COALESCE(?,payment_ref2) WHERE id=?", Date.now(), ref || null, ref2 || null, o.id);
    event(o.id, 'bezahlt', `Zahlung eingegangen (${source || PAY[o.payment_method]})${ref ? ' – ' + ref : ''}`); o = ensureInvoice(get(num));
    await notify(o, 'paid'); return o;
  }
  async function setStatus(num, status, extra = {}) {
    const o = get(num); if (!o) return null; if (!NAMES[status]) throw Object.assign(new Error('Unbekannter Status'), { status: 400 });
    const sets = ['status=?']; const args = [status];
    if (status === 'versendet') { sets.push('shipped_at=?'); args.push(Date.now()); if (extra.tracking != null) { sets.push('tracking=?', 'carrier=?'); args.push(str(extra.tracking, 80), str(extra.carrier, 40)); } }
    db.run(`UPDATE orders SET ${sets.join(',')} WHERE id=?`, ...args, o.id); event(o.id, 'status', `Status: ${NAMES[status]}${extra.tracking ? ` (Sendungsnr. ${extra.tracking})` : ''}`);
    const n = get(num); if (status === 'versendet') { ensureInvoice(n); await notify(get(num), 'shipped'); } if (status === 'storniert') await notify(n, 'cancelled'); return get(num);
  }
  const itemsHtml = (o) => `<table width="100%" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:14px">${JSON.parse(o.items).map(i => `<tr><td style="border-bottom:1px solid #dce6e0">${i.qty} × ${esc(i.name)}</td><td align="right" style="border-bottom:1px solid #dce6e0;white-space:nowrap">${eur(i.price * i.qty)}</td></tr>`).join('')}
    ${o.discount ? `<tr><td>Rabatt${o.coupon ? ' (' + esc(o.coupon) + ')' : ''}</td><td align="right">−${eur(o.discount)}</td></tr>` : ''}<tr><td>Versand</td><td align="right">${o.shipping_cost ? eur(o.shipping_cost) : 'kostenlos'}</td></tr>
    <tr><td><strong>Gesamt (inkl. ${(cfg.vatRate * 100).toFixed(0)} % MwSt.)</strong></td><td align="right"><strong>${eur(o.total)}</strong></td></tr></table>`;
  const itemsText = (o) => JSON.parse(o.items).map(i => `${i.qty} x ${i.name} – ${eur(i.price * i.qty)}`).join('\n') + `\nGesamt: ${eur(o.total)} (inkl. MwSt.)`;
  async function notify(o, kind) {
    const link = `${cfg.baseUrl}/bestellung.html?n=${o.number}&t=${o.token}`; const c = JSON.parse(o.customer); const bank = cfg.bank.iban ? `<p><strong>Bankverbindung</strong><br>${esc(cfg.bank.holder)}<br>${esc(cfg.bank.name)}<br>IBAN ${esc(cfg.bank.iban)}${cfg.bank.bic ? '<br>BIC ' + esc(cfg.bank.bic) : ''}<br>Verwendungszweck: ${o.number}</p>` : '<p>Unsere Bankverbindung senden wir Ihnen in Kürze separat zu.</p>';
    const greet = `<p>Hallo ${esc(c.first || '')} ${esc(c.last || '')},</p>`;
    if (kind === 'created') {
      const extra = o.payment_method === 'transfer' ? `<p>Bitte überweisen Sie den Betrag innerhalb von 7 Tagen. Wir versenden nach Zahlungseingang.</p>${bank}` : o.payment_method === 'invoice' ? `<p>Ihr Rechnungskauf wird kurz geprüft. Wir melden uns umgehend. Zahlungsziel: 14 Tage nach Rechnungsstellung.</p>${bank}` : '';
      await mail.send({ to: o.email, subject: `Ihre Bestellung ${o.number} bei Italia Camper 24`, html: mail.wrap(`Vielen Dank für Ihre Bestellung ${o.number}`, `${greet}<p>wir haben Ihre Bestellung erhalten.</p>${itemsHtml(o)}${extra}<p><a href="${link}">Bestellstatus ansehen</a></p>`), text: `Vielen Dank für Ihre Bestellung ${o.number}.\n\n${itemsText(o)}\n\nStatus: ${link}` });
      await mail.send({ to: cfg.mail.notify, subject: `Neue Bestellung ${o.number} – ${eur(o.total)} (${PAY[o.payment_method]})`, html: mail.wrap(`Neue Bestellung ${o.number}`, `<p>${esc(c.first)} ${esc(c.last)} · ${esc(o.email)} · ${esc(c.phone || '')}</p>${itemsHtml(o)}<p>Zahlart: ${PAY[o.payment_method]}<br>Fahrzeug: ${esc(o.vehicle || '–')}<br>Anmerkung: ${esc(o.note || '–')}</p><p><a href="${cfg.baseUrl}/admin/#/order/${o.number}">Im Admin öffnen</a></p>`), text: `Neue Bestellung ${o.number}: ${eur(o.total)} – ${cfg.baseUrl}/admin/` });
    } else if (kind === 'paid') {
      await mail.send({ to: o.email, subject: `Zahlung erhalten – Bestellung ${o.number}`, html: mail.wrap('Zahlung eingegangen', `${greet}<p>Ihre Zahlung für Bestellung <strong>${o.number}</strong> ist eingegangen. Wir bereiten den Versand vor.</p><p><a href="${link}">Bestellung &amp; Rechnung ansehen</a></p>`), text: `Zahlung für ${o.number} erhalten. ${link}` });
    } else if (kind === 'shipped') {
      await mail.send({ to: o.email, subject: `Ihre Bestellung ${o.number} wurde versendet`, html: mail.wrap('Ihre Bestellung ist unterwegs', `${greet}<p>Ihre Bestellung <strong>${o.number}</strong> wurde versendet.${o.tracking ? `<br>Sendungsnummer${o.carrier ? ' (' + esc(o.carrier) + ')' : ''}: <strong>${esc(o.tracking)}</strong>` : ''}</p><p>Die Rechnung finden Sie unter <a href="${link}">Bestellstatus</a>.</p>`), text: `Bestellung ${o.number} versendet. ${o.tracking || ''}\n${link}` });
    } else if (kind === 'cancelled') {
      await mail.send({ to: o.email, subject: `Bestellung ${o.number} storniert`, html: mail.wrap('Bestellung storniert', `${greet}<p>Ihre Bestellung <strong>${o.number}</strong> wurde storniert. Bei Fragen erreichen Sie uns unter ${cfg.company.phone}.</p>`), text: `Bestellung ${o.number} storniert.` });
    }
  }
  return { price, create, get, view, forPay, markPaid, setStatus, notify, event, ensureInvoice, methods, NAMES, PAY, str, EMAIL };
}
module.exports = { service, NAMES, PAY };
