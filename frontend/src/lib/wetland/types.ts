export type StratumType = 'tree' | 'sapling_shrub' | 'herb' | 'woody_vine';

export type IndicatorStatus = 'OBL' | 'FACW' | 'FAC' | 'FACU' | 'UPL' | 'NL';

export interface SpeciesEntry {
  id: string;
  plot_id: string;
  stratum: StratumType;
  taxon: string;
  common_name?: string;
  usda_symbol: string;
  percent_cover: number;
  indicator_status: IndicatorStatus;
  is_dominant?: boolean;
  has_morphological_adaptations?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface StratumDominanceResult {
  stratum: StratumType;
  total_cover: number;
  threshold_50: number;
  threshold_20: number;
  cumulative_50_species: string[];
  tied_50_species: string[];
  species_20_set: string[];
  dominants: SpeciesEntry[];
  ranked_species: (SpeciesEntry & {
    rank: number;
    cumulative_cover: number;
    cumulative_percent: number;
    is_d50: boolean;
    is_tied50: boolean;
    is_d20: boolean;
  })[];
}

export interface PrevalenceBreakdown {
  obl_cover: number;
  facw_cover: number;
  fac_cover: number;
  facu_cover: number;
  upl_cover: number;
  total_cover: number;
  weighted_sum: number;
  raw_pi: number | null;
  rounded_pi: number | null;
}

export interface VegetationDetermination {
  rapid_test_passed: boolean;
  dominance_test_a: number; // Dominants with status OBL, FACW, FAC
  dominance_test_b: number; // Total dominants across all strata
  dominance_test_percent: number; // (A / B) * 100
  dominance_test_passed: boolean; // strictly > 50.0% (50.00% FAILS)
  prevalence_index: number | null; // Rounded to 2 decimal places half-up
  prevalence_index_passed: boolean; // PI <= 3.00
  prevalence_breakdown: PrevalenceBreakdown;
  hydrophytic_vegetation_present: boolean;
  strata_results: Record<StratumType, StratumDominanceResult>;
  all_dominants: SpeciesEntry[];
  remarks: string[];
}

export const STRATA_CONFIG: Record<
  StratumType,
  { label: string; shortKey: string; altKey: string; description: string }
> = {
  tree: {
    label: 'Tree Stratum',
    shortKey: '1',
    altKey: 'Alt+1',
    description: 'Woody plants ≥ 3.0 in. (7.6 cm) DBH (30-ft radius)'
  },
  sapling_shrub: {
    label: 'Sapling/Shrub',
    shortKey: '2',
    altKey: 'Alt+2',
    description: 'Woody plants < 3.0 in. DBH and > 3.28 ft (1.0 m) tall (15-ft radius)'
  },
  herb: {
    label: 'Herb Stratum',
    shortKey: '3',
    altKey: 'Alt+3',
    description: 'All herbaceous plants & woody plants ≤ 3.28 ft (1.0 m) tall (5-ft radius)'
  },
  woody_vine: {
    label: 'Woody Vine',
    shortKey: '4',
    altKey: 'Alt+4',
    description: 'All woody vines > 3.28 ft (1.0 m) tall (30-ft radius)'
  }
};
