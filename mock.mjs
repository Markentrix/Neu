import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = path.resolve('website-fertig'), taken = new Set(['10:00']);
const mime = {html:'text/html',css:'text/css',js:'text/javascript',json:'application/json',svg:'image/svg+xml',webp:'image/webp',woff2:'font/woff2',xml:'application/xml',txt:'text/plain'};
const json = (res, code, o) => { res.writeHead(code, {'content-type':'application/json'}); res.end(JSON.stringify(o)); };
http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x'), p = u.pathname;
  if (u.searchParams.get('fail') === '429') return json(res, 429, {ok:false});
  if (p === '/api/verfuegbarkeit') return json(res, 200, {blocked:[], closedWeekdays:[0], nextFree:null, selfBooking:true, slotTimes:['08:00','10:00','14:00']});
  if (p === '/api/slots') return json(res, 200, {tag:u.searchParams.get('tag'), slots:['08:00','10:00','14:00'].map(z => ({zeit:z, frei:!taken.has(z)}))});
  if (p === '/api/leistungen') return json(res, 200, {leistungen:[{key:'a', name:'Testleistung', beschreibung:'', preis:'', dauer:30}]});
  if (p === '/api/mitarbeiter') return json(res, 200, {mitarbeiter:[{key:'m1', name:'Testperson', leistungen:['a']}]});
  if (p === '/api/gutschein/pruefen') return json(res, 200, {ok:true, gueltig:false});
  if (p.startsWith('/api/produkte') || p === '/api/gutschein') return json(res, 404, {ok:false});
  if (p === '/api/e') { res.writeHead(204); return res.end(); }
  if (p === '/api/anfrage' && req.method === 'POST') {
    let b = ''; req.on('data', c => b += c); req.on('end', () => {
      let d = {}; try { d = JSON.parse(b); } catch {}
      const e = {};
      if (!d.name) e.name = 'Bitte Namen angeben.';
      if (d.einwilligung !== 'ja') e.einwilligung = 'Bitte der Datenschutzerklärung zustimmen.';
      if (d.typ === 'termin' && !d.datum) e.datum = 'Bitte einen Tag wählen.';
      if (d.typ === 'termin' && taken.has(d.uhrzeit)) e.uhrzeit = 'Diese Uhrzeit ist gerade vergeben.';
      if (d.website) return json(res, 200, {ok:true, ref:'MOCK-0000'});
      if (Object.keys(e).length) return json(res, 422, {ok:false, errors:e});
      if (d.uhrzeit) taken.add(d.uhrzeit);
      json(res, 200, {ok:true, ref:'MOCK-2026-0001'});
    }); return;
  }
  const f = path.join(ROOT, p === '/' ? 'index.html' : p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404, {'content-type':'text/html'}); return res.end(fs.existsSync(path.join(ROOT,'404.html')) ? fs.readFileSync(path.join(ROOT,'404.html')) : '404'); }
  res.writeHead(200, {'content-type': mime[path.extname(f).slice(1)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
}).listen(8787, () => console.log('Mock: http://localhost:8787'));
