// Service Worker: macht das Portal als App installierbar und zeigt Push-Nachrichten an.
// Es wird bewusst nichts zwischengespeichert, damit keine Kundendaten auf dem Gerät hängen bleiben.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = {}; }
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
