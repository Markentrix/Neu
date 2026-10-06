'use strict';
const cfg = require('./config');
const round2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;
const eur = (n) => Number(n).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
const vatOf = (gross) => round2(gross - gross / (1 + cfg.vatRate));
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fdate = (ms) => new Date(ms).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Europe/Berlin' });
module.exports = { round2, eur, vatOf, esc, fdate };
