import Dexie, { Table } from 'dexie';
import {
  PlotRecord,
  ProjectRecord,
  ReferenceTaxonRecord,
  SyncMetadataRecord,
  SyncOutboxRecord,
  VegetationStratumRecord,
  VegetationTaxonRecord,
} from './schema';
import { REFERENCE_PLANTS, SEED_PLOT, SEED_PROJECT, SEED_TAXA } from './seedData';

export class PalustraDatabase extends Dexie {
  projects!: Table<ProjectRecord, string>;
  plots!: Table<PlotRecord, string>;
  vegetation_strata!: Table<VegetationStratumRecord, string>;
  vegetation_taxa!: Table<VegetationTaxonRecord, string>;
  reference_taxa!: Table<ReferenceTaxonRecord, string>;
  sync_outbox!: Table<SyncOutboxRecord, string>;
  sync_metadata!: Table<SyncMetadataRecord, string>;

  constructor() {
    super('PalustraFieldDB');

    this.version(1).stores({
      projects: 'id, client_project_code, updated_at, sync_status',
      plots: 'id, project_id, plot_name, updated_at, sync_status, [project_id+updated_at]',
      vegetation_strata: 'id, plot_id, stratum_type, [plot_id+stratum_type]',
      vegetation_taxa: 'id, plot_id, stratum_id, usda_symbol, [plot_id+stratum_id], sync_status',
      reference_taxa: 'id, symbol, scientific_name, typical_stratum',
      sync_outbox: 'outbox_id, entity_type, entity_id, timestamp, retry_count',
      sync_metadata: 'key',
    });
  }

  /**
   * Atomic local transaction for adding or modifying a vegetation entry.
   * Updates IndexedDB and logs a pending mutation into sync_outbox.
   */
  async saveVegetationTaxon(record: VegetationTaxonRecord): Promise<void> {
    await this.transaction('rw', [this.vegetation_taxa, this.plots, this.sync_outbox], async () => {
      await this.vegetation_taxa.put(record);

      await this.plots.update(record.plot_id, {
        updated_at: new Date().toISOString(),
        sync_status: 'pending_update',
      });

      await this.sync_outbox.add({
        outbox_id: crypto.randomUUID(),
        entity_type: 'vegetation_taxon',
        entity_id: record.id,
        operation: 'UPDATE',
        payload: record,
        timestamp: Date.now(),
        retry_count: 0,
      });
    });
  }

  /**
   * Soft-delete a vegetation entry with tombstone pattern and outbox logging.
   */
  async softDeleteTaxon(id: string, plotId: string): Promise<void> {
    await this.transaction('rw', [this.vegetation_taxa, this.plots, this.sync_outbox], async () => {
      const existing = await this.vegetation_taxa.get(id);
      if (!existing) return;

      const updated = {
        ...existing,
        is_deleted: true,
        sync_status: 'pending_delete' as const,
        updated_at: new Date().toISOString(),
      };

      await this.vegetation_taxa.put(updated);

      await this.plots.update(plotId, {
        updated_at: new Date().toISOString(),
        sync_status: 'pending_update',
      });

      await this.sync_outbox.add({
        outbox_id: crypto.randomUUID(),
        entity_type: 'vegetation_taxon',
        entity_id: id,
        operation: 'DELETE',
        payload: { id, plot_id: plotId },
        timestamp: Date.now(),
        retry_count: 0,
      });
    });
  }
}

export const db = new PalustraDatabase();

/**
 * Initializes persistent browser storage and audits storage quota.
 */
export async function initializeStoragePersistence(): Promise<{
  persisted: boolean;
  quotaBytes: number;
  usageBytes: number;
  percentUsed: number;
}> {
  let persisted = false;
  if (typeof window !== 'undefined' && 'storage' in navigator && navigator.storage.persist) {
    try {
      persisted = await navigator.storage.persist();
    } catch (e) {
      console.warn('Persistent storage request failed:', e);
    }
  }

  let quotaBytes = 0;
  let usageBytes = 0;
  let percentUsed = 0;

  if (typeof window !== 'undefined' && 'storage' in navigator && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate();
      quotaBytes = estimate.quota || 0;
      usageBytes = estimate.usage || 0;
      percentUsed = quotaBytes > 0 ? (usageBytes / quotaBytes) * 100 : 0;
    } catch (e) {
      console.warn('Storage estimation error:', e);
    }
  }

  return { persisted, quotaBytes, usageBytes, percentUsed };
}

/**
 * Seeds reference plants and the default plot if empty.
 */
export async function seedInitialDatabase(): Promise<void> {
  if (typeof window === 'undefined') return;

  const count = await db.reference_taxa.count();
  if (count === 0) {
    await db.reference_taxa.bulkPut(REFERENCE_PLANTS);
  }

  const plotCount = await db.plots.count();
  if (plotCount === 0) {
    await db.transaction('rw', [db.projects, db.plots, db.vegetation_taxa], async () => {
      await db.projects.put(SEED_PROJECT);
      await db.plots.put(SEED_PLOT);
      await db.vegetation_taxa.bulkPut(SEED_TAXA);
    });
  }
}
