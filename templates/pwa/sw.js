// Minimal service worker for PWA installability.
// We intentionally avoid caching authenticated HTML routes to prevent serving stale sessions.

const STATIC_CACHE = 'fieldops-static-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Cache only same-origin static assets (best-effort).
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (!url.pathname.startsWith('/static/')) return;

  event.respondWith((async () => {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(req);
    const fetchPromise = fetch(req).then((res) => {
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    }).catch(() => cached);

    return cached || fetchPromise;
  })());
});


