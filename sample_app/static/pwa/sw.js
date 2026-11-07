// The Tally sample's service worker (recipe pwa-offline): cache-first for its own files, scoped to /pwa/.
// A new version gets a new cache name; activate deletes this app's older caches and takes control of open pages.
const CACHE = 'tally-v1';
const FILES = ['index.html', 'app.js', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys()
    .then((names) => Promise.all(names.filter((name) => name.startsWith('tally-') && name !== CACHE).map((name) => caches.delete(name))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET' || !request.url.startsWith(self.registration.scope)) return;
  const fallback = request.mode === 'navigate' ? 'index.html' : request;
  event.respondWith(caches.match(request, { ignoreSearch: true })
    .then((hit) => hit || fetch(request).catch(() => caches.match(fallback)))
    .then((response) => response || Response.error()));
});
