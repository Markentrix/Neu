'use strict';
const crypto = require('crypto');
const cfg = require('./config');
const cents = (n) => Math.round(n * 100);
const enc = (o) => Object.entries(o).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');

// ---------- Stripe (Checkout-Weiterleitung: Karte, Apple Pay, Google Pay – im Stripe-Dashboard aktivieren) ----------
const stripe = {
  enabled: () => !!cfg.stripe.key,
  async call(path, body, method = 'POST') {
    const r = await fetch(cfg.stripe.api + path, { method, headers: { Authorization: `Bearer ${cfg.stripe.key}`, 'Content-Type': 'application/x-www-form-urlencoded' }, body: body ? enc(body) : undefined });
    const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error('Stripe: ' + ((j.error && j.error.message) || r.status)); return j;
  },
  async createSession(order) {
    const desc = order.lines.map(l => `${l.qty}× ${l.name}`).join(', ').slice(0, 480);
    const s = await this.call('/v1/checkout/sessions', {
      mode: 'payment', client_reference_id: order.number, customer_email: order.email, locale: 'de',
      success_url: `${cfg.baseUrl}/bestellung.html?n=${order.number}&t=${order.token}&paid=1`, cancel_url: `${cfg.baseUrl}/bestellung.html?n=${order.number}&t=${order.token}&cancel=1`,
      'metadata[order]': order.number, 'payment_intent_data[metadata][order]': order.number, 'payment_intent_data[description]': `Bestellung ${order.number} – Italia Camper 24`,
      'line_items[0][quantity]': 1, 'line_items[0][price_data][currency]': 'eur', 'line_items[0][price_data][unit_amount]': cents(order.total),
      'line_items[0][price_data][product_data][name]': `Bestellung ${order.number}`, 'line_items[0][price_data][product_data][description]': desc,
    });
    return { id: s.id, url: s.url };
  },
  getSession(id) { return this.call(`/v1/checkout/sessions/${encodeURIComponent(id)}`, null, 'GET'); },
  refund(paymentIntent, amount) { const b = { payment_intent: paymentIntent }; if (amount) b.amount = cents(amount); return this.call('/v1/refunds', b); },
  verifyWebhook(raw, header) {
    if (!cfg.stripe.webhookSecret) return false;
    const p = {}; (header || '').split(',').forEach(x => { const i = x.indexOf('='); if (i > 0) p[x.slice(0, i)] = x.slice(i + 1); });
    if (!p.t || !p.v1 || Math.abs(Date.now() / 1000 - +p.t) > 600) return false;
    const exp = crypto.createHmac('sha256', cfg.stripe.webhookSecret).update(`${p.t}.${raw}`).digest('hex');
    try { return crypto.timingSafeEqual(Buffer.from(exp), Buffer.from(p.v1)); } catch { return false; }
  },
};

// ---------- PayPal (Orders v2, Weiterleitung + Capture) ----------
let tok = null;
const paypal = {
  enabled: () => !!(cfg.paypal.id && cfg.paypal.secret),
  async token() {
    if (tok && tok.exp > Date.now() + 30000) return tok.t;
    const r = await fetch(cfg.paypal.api + '/v1/oauth2/token', { method: 'POST', headers: { Authorization: 'Basic ' + Buffer.from(`${cfg.paypal.id}:${cfg.paypal.secret}`).toString('base64'), 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'grant_type=client_credentials' });
    const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error('PayPal-Anmeldung fehlgeschlagen'); tok = { t: j.access_token, exp: Date.now() + j.expires_in * 1000 }; return tok.t;
  },
  async call(path, body, method = 'POST') {
    const r = await fetch(cfg.paypal.api + path, { method, headers: { Authorization: 'Bearer ' + await this.token(), 'Content-Type': 'application/json', 'PayPal-Request-Id': crypto.randomUUID() }, body: body ? JSON.stringify(body) : undefined });
    const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error('PayPal: ' + (j.message || (j.details && j.details[0] && j.details[0].description) || r.status)); return j;
  },
  async createOrder(order) {
    const j = await this.call('/v2/checkout/orders', { intent: 'CAPTURE', purchase_units: [{ reference_id: order.number, invoice_id: order.number, description: `Bestellung ${order.number}`, amount: { currency_code: 'EUR', value: order.total.toFixed(2) } }],
      payment_source: { paypal: { experience_context: { brand_name: 'Italia Camper 24', locale: 'de-DE', landing_page: 'LOGIN', shipping_preference: 'NO_SHIPPING', user_action: 'PAY_NOW',
        return_url: `${cfg.baseUrl}/api/paypal/return?n=${order.number}&t=${order.token}`, cancel_url: `${cfg.baseUrl}/bestellung.html?n=${order.number}&t=${order.token}&cancel=1` } } } });
    const link = (j.links || []).find(l => l.rel === 'payer-action' || l.rel === 'approve'); return { id: j.id, url: link && link.href };
  },
  capture(id) { return this.call(`/v2/checkout/orders/${encodeURIComponent(id)}/capture`, null); },
  refund(captureId, amount) { return this.call(`/v2/payments/captures/${encodeURIComponent(captureId)}/refund`, amount ? { amount: { value: amount.toFixed(2), currency_code: 'EUR' } } : {}); },
};
module.exports = { stripe, paypal };
