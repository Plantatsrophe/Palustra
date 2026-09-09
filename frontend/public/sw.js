// Palustra Service Worker: Offline-First Field Cache & Outbox Sync
const CACHE_NAME = 'palustra-app-shell-v1';
const REFERENCE_DATA_CACHE = 'palustra-reference-data-v1';

const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icons/icon-192.svg',
  '/icons/icon-512.svg'
];

self.addEventListener('install', (event) => {
  // Force immediate activation of waiting service worker
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('Pre-caching non-fatal warning:', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  // Claim control over all open client windows immediately
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      caches.keys().then((keys) => {
        return Promise.all(
          keys
            .filter((k) => k !== CACHE_NAME && k !== REFERENCE_DATA_CACHE)
            .map((k) => caches.delete(k))
        );
      })
    ])
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip chrome-extension, non-GET or external schemes
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) {
    return;
  }

  // Botanical reference datasets: Cache-First
  if (url.pathname.startsWith('/data/reference/') || url.pathname.includes('plant_reference')) {
    event.respondWith(
      caches.open(REFERENCE_DATA_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;
        try {
          const response = await fetch(request);
          if (response.status === 200) {
            cache.put(request, response.clone());
          }
          return response;
        } catch (err) {
          return new Response(JSON.stringify({ error: 'Offline reference not cached' }), {
            headers: { 'Content-Type': 'application/json' }
          });
        }
      })
    );
    return;
  }

  // App Shell & Static Pages: Stale-While-Revalidate with Cache-First Fallback
  event.respondWith(
    caches.match(request).then(async (cachedResponse) => {
      const fetchPromise = fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const resClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, resClone);
            });
          }
          return networkResponse;
        })
        .catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});

// Background Sync API Handler
self.addEventListener('sync', (event) => {
  if (event.tag === 'palustra-outbox-sync') {
    event.waitUntil(notifyClientsToSync());
  }
});

async function notifyClientsToSync() {
  const clients = await self.clients.matchAll({ includeUncontrolled: true });
  for (const client of clients) {
    client.postMessage({ type: 'TRIGGER_OUTBOX_SYNC', timestamp: Date.now() });
  }
}
