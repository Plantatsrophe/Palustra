# Dexie.js Schema Design & Local Storage Architecture

This document specifies the exact IndexedDB database schemas, compound indices, transactional boundaries, and binary blob storage strategies for **Palustra** using **Dexie.js**.

---

## 1. Dexie Database Definition & Versioning

The Palustra offline database is declared with strictly typed stores and migration pipelines.

```typescript
import Dexie, { Table } from 'dexie';

export class PalustraDatabase extends Dexie {
  projects!: Table<ProjectRecord, string>;
  plots!: Table<PlotRecord, string>;
  vegetation_strata!: Table<VegetationStratumRecord, string>;
  vegetation_taxa!: Table<VegetationTaxonRecord, string>;
  soil_profiles!: Table<SoilProfileRecord, string>;
  soil_layers!: Table<SoilLayerRecord, string>;
  hydrology_records!: Table<HydrologyRecord, string>;
  photo_attachments!: Table<PhotoAttachmentRecord, string>;
  sync_outbox!: Table<SyncOutboxRecord, string>;
  sync_metadata!: Table<SyncMetadataRecord, string>;

  constructor() {
    super('PalustraFieldDB');

    this.version(1).stores({
      projects: 'id, client_project_code, updated_at, sync_status',
      plots: 'id, project_id, plot_name, updated_at, sync_status, [project_id+updated_at]',
      vegetation_strata: 'id, plot_id, stratum_type, [plot_id+stratum_type]',
      vegetation_taxa: 'id, plot_id, stratum_id, usda_symbol, [plot_id+stratum_id], sync_status',
      soil_profiles: 'id, plot_id, updated_at, sync_status',
      soil_layers: 'id, profile_id, layer_depth_top, [profile_id+layer_depth_top]',
      hydrology_records: 'id, plot_id, sync_status',
      photo_attachments: 'id, plot_id, entity_type, entity_id, created_at, [plot_id+entity_type]',
      sync_outbox: 'outbox_id, entity_type, entity_id, timestamp, retry_count',
      sync_metadata: 'key'
    });
  }
}

export const db = new PalustraDatabase();
```

---

## 2. Table Schemas & Compound Indices

### A. Plots Table (`plots`)
* **Primary Key**: `id` (UUIDv4).
* **Indices**:
  * `project_id`: Filters plots within an active delineation project.
  * `updated_at`: Range slicing for incremental sync.
  * `[project_id+updated_at]`: Compound index for rapid chronological delta synchronization per project.
* **Fields**:
  * `id`: string (UUID)
  * `project_id`: string (UUID)
  * `plot_name`: string (e.g., "SP-01-WET")
  * `latitude`: number
  * `longitude`: number
  * `datum`: "WGS84" | "NAD83"
  * `region`: "EMP" | "AGCP"
  * `determination_result`: "WETLAND" | "UPLAND" | "IN_PROGRESS"
  * `is_deleted`: boolean
  * `sync_status`: "clean" | "pending_insert" | "pending_update" | "pending_delete"
  * `created_at`: string (ISO8601)
  * `updated_at`: string (ISO8601)

### B. Vegetation Taxa Table (`vegetation_taxa`)
* **Primary Key**: `id` (UUIDv4).
* **Indices**: `plot_id`, `stratum_id`, `usda_symbol`, `[plot_id+stratum_id]`.
* **Compound Index Purpose**: Enables single-cycle index scan to retrieve all plant species within a specific stratum for rapid 50/20 dominance calculations:
  ```typescript
  const herbTaxa = await db.vegetation_taxa
    .where('[plot_id+stratum_id]')
    .equals([activePlotId, herbStratumId])
    .toArray();
  ```

### C. Photo Attachments (`photo_attachments`)
* **Binary Isolation Strategy**: Field photos taken on mobile cameras (5MB to 15MB each) must never be encoded as Base64 strings inside JSON documents. This prevents excessive serialization overhead and IndexedDB memory pressure.
* **Schema**:
  * `id`: string (UUIDv4)
  * `plot_id`: string (UUIDv4)
  * `entity_type`: "plot_overview" | "soil_pit" | "dominant_plant" | "hydrology_indicator"
  * `entity_id`: string (Foreign key to plot, soil, or vegetation record)
  * `photo_blob`: `Blob` (Raw compressed image binary, e.g., JPEG or WebP)
  * `thumbnail_blob`: `Blob` (Downscaled 256x256 thumbnail for instantaneous UI grid rendering)
  * `file_size_bytes`: number
  * `mime_type`: "image/webp" | "image/jpeg"
  * `caption`: string
  * `created_at`: string (ISO8601)

---

## 3. Transactional Boundaries & Data Integrity

To guarantee ACID properties locally:
* **All multi-table writes must occur inside an atomic Dexie transaction**:
  ```typescript
  await db.transaction('rw', [db.plots, db.vegetation_taxa, db.sync_outbox], async () => {
    // 1. Insert or update taxon
    await db.vegetation_taxa.put(taxonRecord);
    
    // 2. Touch plot updated_at
    await db.plots.update(plotId, {
      updated_at: new Date().toISOString(),
      sync_status: 'pending_update'
    });
    
    // 3. Append to sync outbox
    await db.sync_outbox.add({
      outbox_id: crypto.randomUUID(),
      entity_type: 'vegetation_taxon',
      entity_id: taxonRecord.id,
      operation: 'PUT',
      payload: taxonRecord,
      timestamp: Date.now(),
      retry_count: 0
    });
  });
  ```
* **Failure Isolation**: If any step fails (e.g. quota exceeded), the entire transaction aborts, preventing broken or partially synchronized states.
