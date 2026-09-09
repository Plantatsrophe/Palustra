---
name: offline-pwa-sync-architecture
description: >-
  Defines offline-first Progressive Web App (PWA) architecture for remote field operations in zero-connectivity environments. Governs Dexie.js IndexedDB storage schemas, Service Worker caching strategies, the Outbox sync engine, deterministic conflict resolution, and persistent client state management.
---

# Offline-First PWA Architecture & Sync Engine

This skill governs the system architecture, local data persistence, service worker caching, and synchronization mechanics for **Palustra**—an offline-first Progressive Web App (PWA) designed for professional wetland delineations and ecological field surveys in remote backcountry areas with **zero cellular connectivity**.

---

## Architectural Principles

1. **Local-First Ground Truth**: The client's local database (IndexedDB via Dexie.js) is the immediate source of truth. All user actions (plot creation, plant cover entries, soil profile logs, photo captures) execute synchronously against local storage with zero network dependency.
2. **Zero-Connectivity Tolerance**: The application must function flawlessly with 100% feature availability indefinitely in airplane mode or deep wilderness. No UI action may block on a network request.
3. **Optimistic UI with Outbox Queue**: Mutations write immediately to local transactional stores and append an immutable change event to an Outbox sync queue.
4. **Persistent Storage Guarantee**: Storage must be declared persistent via the browser Storage API (`navigator.storage.persist()`) to prevent automated eviction under OS memory pressure.
5. **Deterministic Conflict Resolution**: Multi-user synchronizations reconcile using field-level three-way merging, monotonic Lamport timestamps, and soft-delete tombstones.

---

## 1. Storage Architecture (Dexie.js / IndexedDB)

Palustra uses **Dexie.js** as a typed, reactive abstraction layer over browser IndexedDB.

### Architectural Tiers of Local Storage
```
┌───────────────────────────────────────────────────────────────┐
│                      PALUSTRA LOCAL STORAGE                    │
├──────────────────────────────┬────────────────────────────────┤
│      IndexedDB (Dexie.js)    │         CacheStorage           │
├──────────────────────────────┼────────────────────────────────┤
│ • Field Projects & Plots     │ • App Shell (HTML/CSS/JS)      │
│ • Soil Profiles & Hydrology  │ • NWPL 2022 Reference Datasets │
│ • Outbox Mutation Queue      │ • USDA PLANTS Master Index     │
│ • Photo Blobs / Attachments  │ • Static Map Tiles (MBTiles)   │
└──────────────────────────────┴────────────────────────────────┘
```

### Core Schema Design Rules
* **Synthetic Primary Keys**: All entity IDs must be universally unique client-side identifiers (UUIDv4) to eliminate ID collisions during asynchronous multi-client synchronization.
* **Compound Indexing for Spatial & Project Queries**:
  * Compound index `[project_id+stratum]` for rapid plot stratum queries.
  * Index `[project_id+updated_at]` for chronological delta slicing.
* **Binary Media Isolation**: Store high-resolution field photos in a dedicated `photo_attachments` object store as raw `Blob` objects, referencing metadata foreign keys. Never store binary base64 strings in JSON documents.
* **Sync State Tracking**: Every mutable entity must include:
  * `id`: UUIDv4
  * `created_at`: ISO8601 UTC timestamp
  * `updated_at`: ISO8601 UTC timestamp
  * `client_version`: Monotonic integer counter
  * `sync_status`: `"clean"` | `"pending_insert"` | `"pending_update"` | `"pending_delete"`
  * `is_deleted`: Boolean (Tombstone pattern)

For full Dexie schema definitions and indexing rules, see [dexie_schema_and_storage.md](./references/dexie_schema_and_storage.md).

---

## 2. Service Worker Caching Architecture

The Service Worker operates as a transparent network proxy enforcing distinct caching strategies across five critical asset classes:

```
                  ┌───────────────────────┐
                  │   Incoming Request    │
                  └───────────┬───────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   [ App Shell ]     [ Reference Data ]    [ API Mutation ]
   (HTML/JS/CSS)      (USDA/NWPL/Tiles)     (Sync Endpoints)
         │                    │                    │
         ▼                    ▼                    ▼
   Cache-First /        Cache-First /       Outbox Pattern /
   Precached via        Stale-While-        Queue Mutation in
   Service Worker       Revalidate          IndexedDB Queue
```

### Asset Class Routing Matrix

| Asset Category | Target Resources | Caching Strategy | Offline Behavior |
| :--- | :--- | :--- | :--- |
| **App Shell** | `index.html`, compiled JS/CSS bundles, UI icons, web fonts. | **Cache-First (Precaching)** | Instant boot from CacheStorage; updates download in background for next reload. |
| **Botanical Datasets** | USDA PLANTS list, NWPL 2022 lists (EMP/AGCP), FQA tables. | **Cache-First (Immutable Versioning)** | Stored in dedicated Cache bucket; completely available offline indefinitely. |
| **Spatial Basemaps** | Offline vector/raster map tiles (PBF, MBTiles, WebP). | **Cache-First with LRU Eviction** | Pre-downloaded survey boundaries served directly from local tile cache. |
| **Dynamic Reads** | Cloud project listings, cloud collaborator profiles. | **Network-First with IndexedDB Fallback** | Displays cached local projects immediately if network unreachable. |
| **Mutations / Writes**| Project creation, plot updates, vegetation cover logs. | **Outbox Queue Bypass** | Network request bypassed; written directly to local Dexie Outbox. |

For detailed Service Worker lifecycle events and Workbox configurations, see [service_worker_caching_strategies.md](./references/service_worker_caching_strategies.md).

---

## 3. The Outbox Pattern & Sync Protocol

In zero-connectivity environments, mutations cannot wait for network acknowledgments. Palustra implements an **Asynchronous Outbox Event Pipeline**:

### Mutation Flow
1. **User Action**: Surveyor inputs a vegetation stratum cover change in the UI.
2. **Atomic Local Transaction**: Within a single Dexie transaction:
   * The entity in the local table (e.g., `vegetation_entries`) is updated with new values and `sync_status = "pending_update"`.
   * A change record is appended to `sync_outbox`:
     ```typescript
     {
       outbox_id: "uuid-...",
       entity_type: "vegetation_entry",
       entity_id: "entry-uuid",
       operation: "UPDATE",
       payload: { species: "Carex lurida", cover: 35.0 },
       timestamp: 1725912345678,
       retry_count: 0
     }
     ```
3. **UI Confirmation**: The UI updates instantaneously with optimistic state.
4. **Network Detection & Replay**:
   * The Service Worker listens to `online` events and the `SyncManager` API (`sync` event).
   * When network returns, the sync manager reads the `sync_outbox` chronologically and pushes batches to the backend sync endpoint.
   * On successful server acknowledgment, local records transition to `sync_status = "clean"` and outbox entries are pruned.

---

## 4. Conflict Resolution Engine

When multiple ecologists log data on the same wetland determination across offline devices, merge conflicts will occur when devices re-establish connection.

### Conflict Resolution Hierarchy
1. **Field-Level Granular Merging**:
   * Conflicts are resolved at the **attribute level**, not the entity level.
   * If Surveyor A edits `soil_matrix_value` and Surveyor B edits `soil_matrix_chroma`, both non-overlapping edits merge cleanly.
2. **Last-Write-Wins (LWW) with Lamport Clocks**:
   * For overlapping attribute edits, deterministic resolution uses a monotonic **Lamport logical clock** + device ID tie-breaker:
     $$\text{Winner} = \max(\text{Clock}_{\text{local}}, \text{Clock}_{\text{remote}})$$
3. **Soft-Delete Tombstones**:
   * Deletions never execute a hard SQL/IndexedDB `DELETE` during offline periods.
   * The record is marked `is_deleted = true` with a deletion timestamp.
   * If an update arrives with a timestamp newer than the deletion tombstone, the update resurrects the record; otherwise, the deletion prevails.

For full three-way merge algorithms and conflict schemas, see [conflict_resolution_and_sync.md](./references/conflict_resolution_and_sync.md).

---

## 5. Client State Management & Storage Quota

Field tablets and mobile devices in prolonged backcountry use face storage quota limits and aggressive OS background killing.

### Storage Persistence
Browser storage defaults to "best-effort", which means the browser can silently evict IndexedDB databases when disk space runs low.
* **Mandatory Init Protocol**: At application launch, execute:
  ```javascript
  if (navigator.storage && navigator.storage.persist) {
    const isPersisted = await navigator.storage.persist();
    console.log(`Persistent storage granted: ${isPersisted}`);
  }
  ```
* **Quota Auditing**: Regularly inspect `navigator.storage.estimate()` to alert the surveyor when local database consumption exceeds 80% of available storage.

### Reactive UI Binding
* Palustra couples Dexie directly to client UI components using live reactive queries (e.g., Dexie `useLiveQuery` or lightweight signal subscriptions).
* UI components observe database tables directly; any background sync merge automatically triggers surgical re-renders without manual state dispatcher boilerplate.

For storage quota APIs and battery-conscious synchronization rules, see [client_state_and_storage_quota.md](./references/client_state_and_storage_quota.md).
