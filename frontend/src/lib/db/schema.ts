import { IndicatorStatus, StratumType } from '../wetland/types';

export type SyncStatus = 'clean' | 'pending_insert' | 'pending_update' | 'pending_delete';

export interface ProjectRecord {
  id: string;
  client_project_code: string;
  project_name: string;
  created_at: string;
  updated_at: string;
  sync_status: SyncStatus;
}

export interface PlotRecord {
  id: string;
  project_id: string;
  plot_name: string;
  latitude?: number;
  longitude?: number;
  datum?: 'WGS84' | 'NAD83';
  region: 'EMP' | 'AGCP';
  determination_result?: 'WETLAND' | 'UPLAND' | 'IN_PROGRESS';
  is_deleted: boolean;
  sync_status: SyncStatus;
  created_at: string;
  updated_at: string;
}

export interface VegetationStratumRecord {
  id: string;
  plot_id: string;
  stratum_type: StratumType;
  total_cover?: number;
}

export interface VegetationTaxonRecord {
  id: string;
  plot_id: string;
  stratum_id: StratumType;
  usda_symbol: string;
  taxon: string;
  common_name?: string;
  percent_cover: number;
  indicator_status: IndicatorStatus;
  has_morphological_adaptations?: boolean;
  is_deleted: boolean;
  sync_status: SyncStatus;
  created_at: string;
  updated_at: string;
}

export interface SyncOutboxRecord {
  outbox_id: string;
  entity_type: string;
  entity_id: string;
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  payload: any;
  timestamp: number;
  retry_count: number;
}

export interface SyncMetadataRecord {
  key: string;
  value: any;
  updated_at: string;
}

export interface ReferenceTaxonRecord {
  id: string;
  symbol: string;
  scientific_name: string;
  common_name: string;
  emp_indicator: IndicatorStatus;
  agcp_indicator: IndicatorStatus;
  typical_stratum: StratumType;
}
