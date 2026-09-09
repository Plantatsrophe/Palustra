# Client State Management & Storage Quota Governance

This document establishes the patterns for reactive client state binding, storage quota preservation, and battery/hardware conservation in zero-connectivity field tablets.

---

## 1. Reactive Client State via Dexie `useLiveQuery`

Rather than maintaining detached Redux/Zustand global stores that can desynchronize from IndexedDB, Palustra couples UI rendering directly to the local database using **Live Queries**:

### Reactive Pattern
```typescript
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../db';

export function PlotVegetationList({ plotId, stratumId }: { plotId: string; stratumId: string }) {
  // Automatically re-evaluates whenever IndexedDB 'vegetation_taxa' table changes locally or via background sync
  const taxa = useLiveQuery(
    () => db.vegetation_taxa
      .where('[plot_id+stratum_id]')
      .equals([plotId, stratumId])
      .and(item => !item.is_deleted)
      .toArray(),
    [plotId, stratumId]
  );

  if (!taxa) return <LoadingSpinner />;

  return (
    <ul>
      {taxa.map(t => (
        <TaxonRow key={t.id} taxon={t} />
      ))}
    </ul>
  );
}
```

### Advantages for Offline Work
* **No Synchronization Mismatch**: The UI is always an exact projection of IndexedDB.
* **Zero Boilerplate**: No actions, reducers, or complex cache invalidation mechanisms.
* **Instant Background Updates**: When background sync merges edits from another team member, the UI updates surgically without page reloads.

---

## 2. Storage Quota & Persistence Architecture

Modern mobile browsers (Safari on iOS, Chrome on Android) reserve the right to silently evict IndexedDB contents during low disk storage conditions unless explicit persistence is granted.

### Mandatory Initialization Protocol
Upon app boot, request persistent storage:

```typescript
export async function initializeStoragePersistence(): Promise<{
  persisted: boolean;
  quotaBytes: number;
  usageBytes: number;
  percentUsed: number;
}> {
  let persisted = false;
  if (navigator.storage && navigator.storage.persist) {
    persisted = await navigator.storage.persist();
  }

  let quotaBytes = 0;
  let usageBytes = 0;
  let percentUsed = 0;

  if (navigator.storage && navigator.storage.estimate) {
    const estimate = await navigator.storage.estimate();
    quotaBytes = estimate.quota || 0;
    usageBytes = estimate.usage || 0;
    percentUsed = quotaBytes > 0 ? (usageBytes / quotaBytes) * 100 : 0;
  }

  return { persisted, quotaBytes, usageBytes, percentUsed };
}
```

### Storage Quota Guardrails
* **Warning Threshold ($\ge 80\%$)**: Display persistent banner in UI advising surveyor to offload high-resolution photos or prune completed projects.
* **Critical Threshold ($\ge 95\%$)**: Temporarily disable automatic high-resolution photo capture, capturing downscaled WebP images only ($1280\times 720$) until storage is cleared.

---

## 3. Field Battery & Hardware Conservation Rules

In backcountry conditions where field tablets operate on battery power for 8–12 hours:
1. **Zero Continuous Polling**: Never execute background `setInterval` timers checking for connectivity. Rely exclusively on the browser `online` and `offline` event handlers.
2. **Client-Side Image Compression**:
   * Compress camera images inside a Web Worker using `OffscreenCanvas` before writing to IndexedDB.
   * Target: Maximum width/height $1920\text{px}$, quality $0.8$ WebP/JPEG, reducing raw $10\text{MB}$ camera files to $\approx 350\text{KB}$.
3. **Screen Sleep Prevention during Data Entry**:
   * Utilize the Screen Wake Lock API (`navigator.wakeLock.request('screen')`) only when an active soil or vegetation plot form is open, releasing it when navigating to view-only screens.
