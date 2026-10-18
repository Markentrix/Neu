// Minimaler Service Worker: macht das Portal als App installierbar.
// Es wird bewusst nichts zwischengespeichert, damit keine Kundendaten auf dem Gerät hängen bleiben.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
