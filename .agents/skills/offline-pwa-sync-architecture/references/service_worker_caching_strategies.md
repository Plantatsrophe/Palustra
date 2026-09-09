# Service Worker Caching Strategies & Offline Routing

This document defines the Service Worker architecture, Workbox routing rules, offline asset precaching, and background synchronization mechanisms for **Palustra**.

---

## 1. Service Worker Lifecycle & Activation

The Service Worker must install immediately and activate without waiting for existing tabs to close, ensuring immediate offline availability on initial installation:

```javascript
self.addEventListener('install', (event) => {
  // Force immediate activation of waiting service worker
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Claim control over all open client windows immediately
  event.waitUntil(self.clients.claim());
});
```

---

## 2. Workbox Strategy Routing Architecture

Palustra segments network traffic into four deterministic caching routes:

```javascript
import { registerRoute } from 'workbox-routing';
import { CacheFirst, StaleWhileRevalidate, NetworkOnly } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// 1. APP SHELL PRECACHE (Compiled Bundles, CSS, Web Fonts)
// Handled via Workbox Precache Manifest injected during build:
// workbox.precaching.precacheAndRoute(self.__WB_MANIFEST);

// 2. BOTANICAL & REGULATORY REFERENCE DATASETS
// Datasets (USDA PLANTS, NWPL 2022 EMP/AGCP, Regional FQA lookups) are versioned and immutable.
registerRoute(
  ({ url }) => url.pathname.startsWith('/data/reference/'),
  new CacheFirst({
    cacheName: 'palustra-reference-data-v1',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year cache
      })
    ]
  })
);

// 3. OFFLINE MAP TILES (Vector / Raster Survey Grids)
registerRoute(
  ({ url }) => url.pathname.startsWith('/tiles/'),
  new CacheFirst({
    cacheName: 'palustra-offline-tiles',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({
        maxEntries: 5000,
        maxAgeSeconds: 90 * 24 * 60 * 60 // 90 days
      })
    ]
  })
);

// 4. CLUSTER READS / METADATA
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/projects'),
  new StaleWhileRevalidate({
    cacheName: 'palustra-projects-cache',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] })
    ]
  })
);

// 5. MUTATION API CALLS (Bypass network entirely if offline)
registerRoute(
  ({ url, request }) => url.pathname.startsWith('/api/sync') && request.method === 'POST',
  new NetworkOnly()
);
```

---

## 3. Pre-Survey Dataset Download (Bulk Warming)

Before departing into zero-connectivity field zones, the surveyor triggers a "Pre-Survey Download":
* The PWA fetches and streams the entire USDA PLANTS North Carolina index (`NC_USDA_PlantList.csv`) and the regional NWPL sheets into IndexedDB/CacheStorage.
* Verification check: A progress indicator confirms all 10,000+ botanical taxa and required base-map tile bundles are cached before the field team enters airplane mode.

---

## 4. Background Sync API (`SyncManager`)

When device connectivity drops to zero, standard HTTP mutations fail. The Service Worker intercepts sync events when connection recovers:

```javascript
self.addEventListener('sync', (event) => {
  if (event.tag === 'palustra-outbox-sync') {
    event.waitUntil(processOutboxQueue());
  }
});

async function processOutboxQueue() {
  // Inform client windows to drain the Dexie sync_outbox table
  const allClients = await self.clients.matchAll({ includeUncontrolled: true });
  for (const client of allClients) {
    client.postMessage({ type: 'TRIGGER_OUTBOX_SYNC' });
  }
}
```

* **Graceful Fallback for Non-Chromium Browsers**: In Safari/WebKit where `SyncManager` is unsupported, the client application listens to `window.addEventListener('online', triggerSync)` and checks connection status with a lightweight periodic health ping.
