// Mock-Server nach Skill website-mit-portal V4.2, Abschnitt 11 (liegt neben website-fertig/, nie im Export).
// Start: node mock.mjs  → http://localhost:8787   | HART=1 node mock.mjs → Schlimmstfälle (Abschnitt 14)
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = path.resolve(process.env.ROOT || 'website-fertig'), taken = new Set(['10:00']);
const HART = process.env.HART === '1';
const mime = {html:'text/html',css:'text/css',js:'text/javascript',json:'application/json',svg:'image/svg+xml',webp:'image/webp',woff2:'font/woff2',xml:'application/xml',txt:'text/plain',png:'image/png',jpg:'image/jpeg',ico:'image/x-icon',pdf:'application/pdf',webmanifest:'application/manifest+json'};
const json = (res, code, o) => { res.writeHead(code, {'content-type':'application/json'}); res.end(JSON.stringify(o)); };
const times = HART ? ['13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00','21:00','22:00'] : ['13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00'];
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'), p = u.pathname;
  if (u.searchParams.get('fail') === '429') return json(res, 429, {ok:false});
  if (p === '/api/verfuegbarkeit') return json(res, 200, HART
    ? {blocked:[], closedWeekdays:[1,2], nextFree:null, selfBooking:false, slotTimes:times}
    : {blocked:[new Date(Date.now()+2*864e5).toISOString().slice(0,10)], closedWeekdays:[], nextFree:new Date(Date.now()+864e5).toISOString().slice(0,10), selfBooking:true, slotTimes:times});
  if (p === '/api/slots') return json(res, 200, {tag:u.searchParams.get('tag'), slots: HART ? times.map(z => ({zeit:z, frei:false})) : times.map(z => ({zeit:z, frei:!taken.has(z) && z !== '15:00'}))});
  if (p === '/api/leistungen') return json(res, 200, {leistungen:[{key:'a', name:'Testleistung', beschreibung:'', preis:'', dauer:30}]});
  if (p === '/api/mitarbeiter') return json(res, 200, {mitarbeiter:[{key:'m1', name:'Testperson', leistungen:['a']}]});
  if (p === '/api/gutschein/pruefen') return json(res, 200, {ok:true, gueltig:false});
  if (p === '/api/gutschein') return HART ? json(res, 404, {ok:false}) : json(res, 200, {aktiv:true, einloesen:false, betraege:[25,50,100], min:10, max:500, gueltigkeitMonate:36, zustellung:['Per E-Mail als PDF','Abholung vor Ort']});
  if (p.startsWith('/api/produkte')) return json(res, 404, {ok:false});
  if (p === '/api/e') { res.writeHead(204); return res.end(); }
  if (p === '/api/anfrage' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', () => {
      let d = {}; try { d = JSON.parse(b); } catch {}
      const e = {};
      if (!d.name) e.name = 'Bitte Namen angeben.';
      if (d.einwilligung !== 'ja') e.einwilligung = 'Bitte der Datenschutzerklärung zustimmen.';
      if (d.typ === 'termin' && !d.datum) e.datum = 'Bitte einen Tag wählen.';
      if (d.typ === 'termin' && taken.has(d.uhrzeit)) e.uhrzeit = 'Diese Uhrzeit ist gerade vergeben.';
      if ((d.typ === 'termin' || d.typ === 'bestellung') && !d.email) e.email = 'Bitte E-Mail angeben.';
      if (d.website) return json(res, 200, {ok:true, ref:'MOCK-0000'});
      if (Object.keys(e).length) return json(res, 422, {ok:false, errors:e});
      if (d.uhrzeit) taken.add(d.uhrzeit);
      console.log('ANFRAGE', d.typ, JSON.stringify(d).slice(0, 300));
      json(res, 200, {ok:true, ref:'MOCK-2026-0001'});
    }); return;
  }
  const f = path.join(ROOT, p === '/' ? 'index.html' : decodeURIComponent(p));
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404, {'content-type':'text/html'}); return res.end(fs.existsSync(path.join(ROOT,'404.html')) ? fs.readFileSync(path.join(ROOT,'404.html')) : '404'); }
  res.writeHead(200, {'content-type': mime[path.extname(f).slice(1)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
}).listen(process.env.PORT || 8787, () => console.log('Mock: http://localhost:' + (process.env.PORT || 8787) + (HART ? ' (HÄRTETEST)' : '')));
