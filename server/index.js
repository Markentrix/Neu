'use strict';
const cfg = require('./config'); const { create } = require('./app'); const fs = require('fs'); const path = require('path');
if (cfg.prod && cfg.sessionSecret === 'dev-secret-change-me') console.warn('WARNUNG: SESSION_SECRET nicht gesetzt');
// Persistente Seiten-Kopie (Admin kann Seiten neu generieren): beim ersten Start aus dem Image kopieren
const seed = path.join(cfg.appRoot, 'site');
if (cfg.siteDir !== seed && fs.existsSync(seed) && !fs.existsSync(path.join(cfg.siteDir, 'index.html'))) { fs.mkdirSync(cfg.siteDir, { recursive: true }); fs.cpSync(seed, cfg.siteDir, { recursive: true }); console.log('Seiten nach', cfg.siteDir, 'kopiert'); }
const { app } = create();
const server = app.listen(cfg.port, () => console.log(`Italia Camper 24 Shop läuft auf ${cfg.baseUrl} (Port ${cfg.port})`));
process.on('SIGTERM', () => server.close(() => process.exit(0)));
