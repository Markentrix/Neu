'use strict';
const path = require('path');
const root = path.resolve(__dirname, '..');
// einfache .env-Unterstützung (ohne Abhängigkeit) für lokalen Betrieb; Docker übergibt die Variablen direkt
try { require('fs').readFileSync(path.join(root, '.env'), 'utf8').split('\n').forEach(l => { const m = l.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*(?:#.*)?$/); if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2].replace(/^["']|["']$/g, ''); }); } catch (e) { }
const env = process.env;
const c = {
  port: +env.PORT || 3000,
  baseUrl: (env.BASE_URL || 'http://localhost:3000').replace(/\/$/, ''),
  dataDir: path.resolve(env.DATA_DIR || path.join(root, 'data')),
  appRoot: root,
  siteDir: path.resolve(env.SITE_DIR || path.join(root, 'site')),
  prod: env.NODE_ENV === 'production',
  sessionSecret: env.SESSION_SECRET || 'dev-secret-change-me',
  admin: { email: env.ADMIN_EMAIL || '', password: env.ADMIN_PASSWORD || '' },
  mail: { host: env.SMTP_HOST || '', port: +env.SMTP_PORT || 587, secure: env.SMTP_SECURE === '1', user: env.SMTP_USER || '', pass: env.SMTP_PASS || '',
          from: env.MAIL_FROM || 'Italia Camper 24 <info@italiacamper24.de>', notify: env.SHOP_NOTIFY_EMAIL || 'info@italiacamper24.de' },
  stripe: { key: env.STRIPE_SECRET_KEY || '', webhookSecret: env.STRIPE_WEBHOOK_SECRET || '', api: env.STRIPE_API_BASE || 'https://api.stripe.com' },
  paypal: { id: env.PAYPAL_CLIENT_ID || '', secret: env.PAYPAL_CLIENT_SECRET || '',
            api: env.PAYPAL_API_BASE || (env.PAYPAL_ENV === 'live' ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com') },
  company: { name: 'Italia Camper 24', owner: env.COMPANY_OWNER || 'Felicia Grieco', street: env.COMPANY_STREET || 'Schillerstr. 12', zip: env.COMPANY_ZIP || '49326', city: env.COMPANY_CITY || 'Wellingholzhausen',
             phone: env.COMPANY_PHONE || '+49 (0) 151 404 790 19', email: env.COMPANY_EMAIL || 'info@italiacamper24.de', vat: env.COMPANY_VAT || 'DE328340321' },
  bank: { holder: env.BANK_HOLDER || 'Felicia Grieco', name: env.BANK_NAME || '', iban: env.BANK_IBAN || '', bic: env.BANK_BIC || '' },
  vatRate: 0.19,
};
module.exports = c;
