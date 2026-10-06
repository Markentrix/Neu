'use strict';
// Baut aus src/catalog.json die kaufbaren SKUs (Preis, Name) – identisch zu den IDs im Frontend (assets/js/app.js).
const fs = require('fs'); const path = require('path');
const cfg = require('./config');
function load(db) {
  const file = [path.join(cfg.appRoot, 'src', 'catalog.json'), path.join(__dirname, 'catalog.json')].find(fs.existsSync);
  const cat = JSON.parse(fs.readFileSync(file, 'utf8'));
  const skus = new Map(); const products = [];
  const add = (sku, name, price, product, kind) => { if (price != null && price > 0) skus.set(sku, { sku, name, price: +price, product, kind, active: 1, base: +price }); };
  for (const p of cat.products) {
    products.push({ slug: p.slug, name: p.name, cat: p.cat, price: p.price });
    add(p.slug, p.name, p.price, p.slug, 'produkt');
    p.variants.forEach((v, k) => add(`${p.slug}~v${k}`, `${p.name} – ${v.t}`, v.p, p.slug, 'variante'));
    p.options.forEach((o, k) => add(`${p.slug}~o${k}`, `${o.name} (${p.name})`, o.price, p.slug, 'zubehoer'));
    (p.montage || []).slice(0, 1).forEach(m => { const vs = m.variants && m.variants.length ? m.variants : [{ t: '', p: m.price }];
      vs.forEach((v, k) => add(`${p.slug}~m${k}`, `Montage: ${p.name}${v.t ? ' – ' + v.t : ''}`, v.p || m.price, p.slug, 'montage')); });
  }
  cat.parts.forEach((q, k) => add(`ersatzteil-${k}`, q.name, q.price, `ersatzteil-${k}`, 'ersatzteil'));
  const apply = () => { if (!db) return; for (const o of db.all('SELECT * FROM sku_overrides')) { const s = skus.get(o.sku); if (s) { if (o.price != null) s.price = o.price; s.active = o.active ? 1 : 0; } } };
  apply();
  return { skus, products, reload() { for (const s of skus.values()) { s.price = s.base; s.active = 1; } apply(); }, raw: cat };
}
module.exports = { load };
