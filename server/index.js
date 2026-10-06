'use strict';
const cfg = require('./config'); const { create } = require('./app'); const fs = require('fs'); const path = require('path');
if (cfg.prod && cfg.sessionSecret === 'dev-secret-change-me') console.warn('WARNUNG: SESSION_SECRET nicht gesetzt');
// Persistente Seiten-Kopie (Admin kann Seiten neu generieren): beim ersten Start aus dem Image kopieren
const seed = path.join(cfg.appRoot, 'site'); const ver = (d) => { try { return fs.readFileSync(path.join(d, '.version'), 'utf8'); } catch (e) { return ''; } };
if (cfg.siteDir !== seed && fs.existsSync(seed) && ver(seed) !== ver(cfg.siteDir)) {
  fs.mkdirSync(cfg.siteDir, { recursive: true }); fs.cpSync(seed, cfg.siteDir, { recursive: true }); console.log('Seiten nach', cfg.siteDir, 'kopiert (neue Version)');
  const ov = path.join(cfg.dataDir, 'overrides.json'); // Admin-Preisänderungen nach einem Update erneut einarbeiten
  if (fs.existsSync(ov)) require('child_process').spawn('python3', [path.join(cfg.appRoot, 'src', 'build.py')], { env: { ...process.env, IC_OUT: cfg.siteDir, IC_OVERRIDES: ov }, cwd: cfg.appRoot, stdio: 'inherit' });
}
const { app } = create();
const server = app.listen(cfg.port, () => console.log(`Italia Camper 24 Shop läuft auf ${cfg.baseUrl} (Port ${cfg.port})`));
process.on('SIGTERM', () => server.close(() => process.exit(0)));
