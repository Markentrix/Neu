// Mock-Server für Tests, liegt NEBEN website-fertig/, nie im Export. Start: node tools/mock.mjs  ->  http://localhost:8787
// Beantwortet die Portal-API nach Vertrag (Abschnitt 9 des Skills). Umgebungsvariable MOCK_FOTOS=ablehnen: Anfragen mit Fotos geben 413.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'website-fertig'), taken = new Set(['10:00']);
const PORT = Number(process.env.PORT || 8787); let last = null;
const mime = {html:'text/html; charset=utf-8',css:'text/css',js:'text/javascript',json:'application/json',svg:'image/svg+xml',webp:'image/webp',avif:'image/avif',jpg:'image/jpeg',png:'image/png',ico:'image/x-icon',woff2:'font/woff2',xml:'application/xml',txt:'text/plain'};
const json = (res, code, o) => { res.writeHead(code, {'content-type':'application/json'}); res.end(JSON.stringify(o)); };
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'), p = decodeURIComponent(u.pathname);
  if (u.searchParams.get('fail') === '429') return json(res, 429, {ok:false});
  if (p === '/__last') return json(res, 200, last || {});
  if (p === '/api/verfuegbarkeit') return json(res, 200, {blocked:[], closedWeekdays:[0], nextFree:null, selfBooking:true, slotTimes:['08:00','10:00','14:00']});
  if (p === '/api/slots') return json(res, 200, {tag:u.searchParams.get('tag'), slots:['08:00','10:00','14:00'].map(z => ({zeit:z, frei:!taken.has(z)}))});
  if (p.startsWith('/api/produkte') || p === '/api/gutschein' || p === '/api/leistungen' || p === '/api/mitarbeiter') return json(res, 404, {ok:false});
  if (p === '/api/e') { res.writeHead(204); return res.end(); }
  if (p === '/api/anfrage' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', () => {
      let d = {}; try { d = JSON.parse(b); } catch {}
      last = { ...d, fotos: d.fotos ? d.fotos.map(x => x.length) : undefined, groesse: b.length };
      if (d.fotos && process.env.MOCK_FOTOS === 'ablehnen') return json(res, 413, {ok:false});
      const e = {};
      if (!d.name) e.name = 'Bitte Namen angeben.';
      if (!d.email) e.email = 'Bitte E-Mail angeben.';
      if (d.einwilligung !== 'ja') e.einwilligung = 'Bitte der Datenschutzerklärung zustimmen.';
      if (d.website) return json(res, 200, {ok:true, ref:'MOCK-0000'});
      if (Object.keys(e).length) return json(res, 422, {ok:false, errors:e});
      json(res, 200, {ok:true, ref:'MOCK-2026-0001'});
    }); return;
  }
  let f = path.join(ROOT, p);
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { res.writeHead(404, {'content-type':'text/html; charset=utf-8'}); return res.end(fs.existsSync(path.join(ROOT,'404.html')) ? fs.readFileSync(path.join(ROOT,'404.html')) : '404'); }
  res.writeHead(200, {'content-type': mime[path.extname(f).slice(1)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
}).listen(PORT, () => console.log('Mock: http://localhost:' + PORT));
