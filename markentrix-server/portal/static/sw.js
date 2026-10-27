// Service Worker: macht das Portal als App installierbar und zeigt Push-Nachrichten an.
// Zwischengespeichert werden nur die statischen Programmdateien (/static/…: Skripte, Styles, Symbole), nie /api und nie Seiten mit Daten.
const CACHE = 'mk-shell-v1';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE && k.startsWith('mk-shell')).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', (e) => {
  const r = e.request, u = new URL(r.url);
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
    body: d.text || '', icon: '/static/icons/icon-192.png', badge: '/static/icons/icon-192.png', tag: d.tag || undefined, data: { url: d.url || '/' } }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((liste) => {
    for (const c of liste) { if ('focus' in c) { if (c.navigate) c.navigate(url); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
