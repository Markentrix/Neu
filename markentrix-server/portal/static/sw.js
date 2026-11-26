// Service Worker: macht das Portal als App installierbar und zeigt Push-Nachrichten an.
// Zwischengespeichert werden nur die statischen Programmdateien (/static/…: Skripte, Styles, Symbole), nie /api und nie Seiten mit Daten.
const CACHE = 'mk-shell-v2';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE && k.startsWith('mk-shell')).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
// „Teilen mit Markentrix“ aus anderen Apps: Die geteilten Inhalte landen kurz im Zwischenspeicher, die Seite /teilen zeigt sie zur Auswahl des Ziels
async function teilenAnnehmen(r) {
  try {
    const fd = await r.formData(), c = await caches.open('mk-teilen');
    for (const k of await c.keys()) await c.delete(k);
    const text = [fd.get('title'), fd.get('text'), fd.get('url')].filter((x) => typeof x === 'string' && x.trim()).join('\n');
    await c.put('/teilen-text', new Response(JSON.stringify({ text, zeit: Date.now() }), { headers: { 'Content-Type': 'application/json' } }));
    let i = 0;
    for (const f of fd.getAll('dateien')) if (f && f.size) await c.put('/teilen-datei/' + (i++), new Response(f, { headers: { 'Content-Type': f.type || 'application/octet-stream', 'X-Name': encodeURIComponent(f.name || 'Datei') } }));
  } catch (x) { /* die Seite zeigt dann „nichts angekommen“ */ }
  return Response.redirect('/teilen?neu=1', 303);
}
self.addEventListener('fetch', (e) => {
  const r = e.request, u = new URL(r.url);
  if (r.method === 'POST' && u.origin === self.location.origin && u.pathname === '/teilen') { e.respondWith(teilenAnnehmen(r)); return; }
  if (r.method !== 'GET' || u.origin !== self.location.origin || !u.pathname.startsWith('/static/')) return;
  // Zuerst Netz (immer aktuell), bei Ausfall die letzte gespeicherte Datei
  e.respondWith(fetch(r).then((a) => { if (a.ok) { const k = a.clone(); caches.open(CACHE).then((c) => c.put(r, k)); } return a; }).catch(() => caches.match(r).then((c) => c || Response.error())));
});
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = {}; }
  // Punkt/Zahl am App-Symbol; die genaue Zahl setzt die App beim Öffnen
  try { if (self.navigator && self.navigator.setAppBadge) self.navigator.setAppBadge(); } catch (x) { /* ohne Unterstützung */ }
  e.waitUntil(self.registration.showNotification(d.titel || 'Markentrix', {
    body: d.text || '', icon: '/static/icons/icon-192.png', badge: '/static/icons/icon-192.png', tag: d.tag || undefined,
    // Schnellaktionen in der Meldung (Android): öffnen oder später noch einmal erinnern; iPhone zeigt nur die Meldung selbst
    actions: d.tag === 'test' ? [] : [{ action: 'oeffnen', title: 'Öffnen' }, { action: 'spaeter', title: 'In 1 Std. erinnern' }],
    data: { url: d.url || '/', titel: d.titel || 'Markentrix', text: d.text || '' } }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const dd = e.notification.data || {}, url = dd.url || '/';
  if (e.action === 'spaeter') {   // nicht öffnen, nur später noch einmal melden
    e.waitUntil(fetch('/api/push/spaeter', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-MK': '1' },
      body: JSON.stringify({ titel: dd.titel || 'Markentrix', text: dd.text || '', url, minuten: 60 }) }).catch(() => {}));
    return;
  }
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((liste) => {
    // Läuft die App schon, springt sie ohne Neuladen direkt zur richtigen Seite
    for (const c of liste) { if ('focus' in c) { c.postMessage({ typ: 'mk-oeffnen', url }); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
