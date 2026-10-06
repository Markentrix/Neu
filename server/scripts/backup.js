'use strict';
// Konsistente Sicherung der SQLite-Datenbank (VACUUM INTO) nach /data/backup, behält die letzten 14 Stände.
const fs = require('fs'); const path = require('path'); const { DatabaseSync } = require('node:sqlite');
const dir = process.env.DATA_DIR || path.join(__dirname, '..', '..', 'data'); const out = path.join(dir, 'backup'); fs.mkdirSync(out, { recursive: true });
const db = new DatabaseSync(path.join(dir, 'shop.db')); const f = path.join(out, `shop-${new Date().toISOString().replace(/[:.]/g, '-')}.db`);
db.exec(`VACUUM INTO '${f.replace(/'/g, "''")}'`); db.close();
fs.readdirSync(out).filter(x => x.endsWith('.db')).sort().reverse().slice(14).forEach(x => fs.unlinkSync(path.join(out, x)));
console.log('Backup:', f);
