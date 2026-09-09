# Conflict Resolution & Outbox Synchronization Protocol

This document establishes the synchronization architecture, conflict resolution mechanics, and data reconciliation logic for **Palustra** multi-user offline field workflows.

---

## 1. The Outbox Event Sourcing Pattern

Every local mutation generates an immutable outbox record in IndexedDB:

```typescript
export interface SyncOutboxRecord {
  outbox_id: string;        // UUIDv4
  entity_type: string;      // "plots" | "vegetation_taxa" | "soil_layers" | ...
  entity_id: string;        // UUIDv4 of modified entity
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  payload: Record<string, any>;
  lamport_clock: number;    // Monotonically increasing logical clock
  client_id: string;        // Unique device/client UUID
  timestamp: number;        // Epoch millis
  retry_count: number;
}
```

### Outbox Processing Lifecycle
1. **Queue Mutation**: Written synchronously inside the local business transaction.
2. **Network Detection**: Triggered on `online` event or `SyncManager.register('palustra-outbox-sync')`.
3. **Batch Transmission**: Batches up to 50 outbox events per HTTP POST request to `/api/sync/push`.
4. **Idempotent Acknowledgment**:
   * Server validates and commits mutations.
   * Server responds with array of acknowledged `outbox_id`s.
   * Client atomically deletes acknowledged items from `sync_outbox` and marks local entities as `sync_status = "clean"`.
5. **Exponential Backoff**: If the network connection drops mid-batch, retry count increments, and replay pauses:
   $$\text{Backoff Interval} = \min(60000, 1000 \times 2^{\text{retry\_count}})$$

---

## 2. Field-Level Three-Way Merge Algorithm

When syncing with a central cloud backend, multiple ecologists may have modified the same sampling plot offline. Palustra performs **field-level granular merging** rather than record-level overwriting:

### Three-Way Merge Decision Matrix

Given:
* **Base ($B$)**: State of the record when the client originally went offline.
* **Local ($L$)**: Current state of the record modified on this device.
* **Remote ($R$)**: Current state of the record received from the server.

For each attribute $k$ in the entity:

| Condition | Merge Action | Resulting Value | Conflict State |
| :--- | :--- | :---: | :---: |
| $L[k] == B[k]$ and $R[k] != B[k]$ | Accept Remote Change (Local did not touch it) | $R[k]$ | None |
| $L[k] != B[k]$ and $R[k] == B[k]$ | Preserve Local Change (Remote did not touch it)| $L[k]$ | None |
| $L[k] == R[k]$ | Identical Edit | $L[k]$ | None |
| $L[k] != B[k]$ and $R[k] != B[k]$ and $L[k] != R[k]$ | **Disputed Field Overlap** | $\text{Resolve via LWW}$ | **Resolved via Lamport Clock** |

### Disputed Overlap Resolution (Last-Write-Wins with Lamport Clocks)
For fields modified concurrently by both local and remote:
$$\text{Winning Value} = \begin{cases} L[k], & \text{if } \text{Clock}_L > \text{Clock}_R \\ R[k], & \text{if } \text{Clock}_R > \text{Clock}_L \\ \max(\text{ClientID}_L, \text{ClientID}_R), & \text{if } \text{Clock}_L == \text{Clock}_R \end{cases}$$

---

## 3. Tombstone Deletion Governance

In distributed offline databases, hard deletions cause "phantom resurrection" (a deleted entity is reintroduced because an older update arrives from another device).

### Deletion Rules
1. **Soft Delete**: When an ecologist deletes a plot or plant record, execute:
   ```typescript
   await db.plots.update(plotId, {
     is_deleted: true,
     deleted_at: new Date().toISOString(),
     updated_at: new Date().toISOString(),
     sync_status: 'pending_delete'
   });
   ```
2. **Reconciliation against Incoming Updates**:
   * If an incoming remote update has `updated_at <= deleted_at`, the update is discarded; the deletion holds.
   * If an incoming remote update has `updated_at > deleted_at`, the record is resurrected with the newer remote data.
3. **Tombstone Pruning (Garbage Collection)**:
   * Tombstones are retained in local IndexedDB for a minimum of 30 days.
   * Once the server confirms all registered project devices have acknowledged the deletion, the tombstone is purged from local IndexedDB.
