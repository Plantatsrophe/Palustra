import assert from 'node:assert';
import test from 'node:test';
import {
  calculateStratum5020,
  calculatePrevalenceIndex,
  evaluateHydrophyticVegetation,
  roundHalfUp,
} from '../lib/wetland/calculations.js';
import { SpeciesEntry, StratumType } from '../lib/wetland/types.js';

test('roundHalfUp correctly performs arithmetic half-up rounding', () => {
  assert.strictEqual(roundHalfUp(3.004, 2), 3.0);
  assert.strictEqual(roundHalfUp(3.005, 2), 3.01);
  assert.strictEqual(roundHalfUp(3.006, 2), 3.01);
  assert.strictEqual(roundHalfUp(2.701, 2), 2.7);
  assert.strictEqual(roundHalfUp(50.004, 2), 50.0);
  assert.strictEqual(roundHalfUp(50.005, 2), 50.01);
});

test('calculateStratum5020: 50/20 rule with 50% tie-breaking', () => {
  // Test case: Total cover = 100
  // Sp1: 40% (running = 40, not > 50)
  // Sp2: 15% (running = 55, > 50 -> cutoff!)
  // Sp3: 15% (tied with Sp2! Must be included as dominant)
  // Sp4: 10% (not in 50%, not >= 20%)
  // Sp5: 20% (>= 20% threshold, dominant via 20% rule!)
  const species: SpeciesEntry[] = [
    {
      id: '1',
      plot_id: 'p1',
      stratum: 'herb',
      taxon: 'Carex lurida',
      usda_symbol: 'CALU4',
      percent_cover: 40,
      indicator_status: 'OBL',
    },
    {
      id: '2',
      plot_id: 'p1',
      stratum: 'herb',
      taxon: 'Typha latifolia',
      usda_symbol: 'TYLA',
      percent_cover: 15,
      indicator_status: 'OBL',
    },
    {
      id: '3',
      plot_id: 'p1',
      stratum: 'herb',
      taxon: 'Boehmeria cylindrica',
      usda_symbol: 'BOCY',
      percent_cover: 15,
      indicator_status: 'OBL',
    },
    {
      id: '4',
      plot_id: 'p1',
      stratum: 'herb',
      taxon: 'Microstegium vimineum',
      usda_symbol: 'MIVI',
      percent_cover: 10,
      indicator_status: 'FAC',
    },
    {
      id: '5',
      plot_id: 'p1',
      stratum: 'herb',
      taxon: 'Osmundastrum cinnamomeum',
      usda_symbol: 'OSCI',
      percent_cover: 20,
      indicator_status: 'FACW',
    },
  ];

  const result = calculateStratum5020('herb', species);

  assert.strictEqual(result.total_cover, 100);
  assert.strictEqual(result.threshold_50, 50);
  assert.strictEqual(result.threshold_20, 20);

  // Sp1 (40) is in 50% set
  // Sp5 is ranked 2nd with 20 cover (cumulative 60 > 50 -> cutoff!)
  // Wait, in descending sort:
  // 40 (Sp1), 20 (Sp5), 15 (Sp2), 15 (Sp3), 10 (Sp4).
  // Cumulative: 40 (no), 40+20=60 (>50 -> cutoff is Sp5).
  // Sp5 cover is 20. Does Sp2 (15) tie with 20? No.
  // Dominants: Sp1 (40), Sp5 (20).
  const domTaxa = result.dominants.map((d) => d.taxon);
  assert.ok(domTaxa.includes('Carex lurida'));
  assert.ok(domTaxa.includes('Osmundastrum cinnamomeum'));
});

test('calculateStratum5020: Exact tie-break at 50% threshold', () => {
  // Total cover = 100
  // Sp1: 45
  // Sp2: 15 (cumulative 60 > 50 -> cutoff!)
  // Sp3: 15 (tied with Sp2 -> MUST BE INCLUDED)
  // Sp4: 15 (tied with Sp2 -> MUST BE INCLUDED)
  // Sp5: 10
  const species: SpeciesEntry[] = [
    {
      id: '1',
      plot_id: 'p1',
      stratum: 'tree',
      taxon: 'Acer rubrum',
      usda_symbol: 'ACRU',
      percent_cover: 45,
      indicator_status: 'FAC',
    },
    {
      id: '2',
      plot_id: 'p1',
      stratum: 'tree',
      taxon: 'Nyssa sylvatica',
      usda_symbol: 'NYSY',
      percent_cover: 15,
      indicator_status: 'FAC',
    },
    {
      id: '3',
      plot_id: 'p1',
      stratum: 'tree',
      taxon: 'Quercus nigra',
      usda_symbol: 'QUNI',
      percent_cover: 15,
      indicator_status: 'FAC',
    },
    {
      id: '4',
      plot_id: 'p1',
      stratum: 'tree',
      taxon: 'Liquidambar styraciflua',
      usda_symbol: 'LIST2',
      percent_cover: 15,
      indicator_status: 'FAC',
    },
    {
      id: '5',
      plot_id: 'p1',
      stratum: 'tree',
      taxon: 'Fagus grandifolia',
      usda_symbol: 'FAGR',
      percent_cover: 10,
      indicator_status: 'FACU',
    },
  ];

  const result = calculateStratum5020('tree', species);

  assert.strictEqual(result.total_cover, 100);
  assert.strictEqual(result.threshold_50, 50);

  // Cutoff is Sp2 (15). Tied species: Sp3 (15) and Sp4 (15).
  // All must be included in dominants!
  assert.strictEqual(result.dominants.length, 4);
  const dominants = result.dominants.map((d) => d.taxon);
  assert.ok(dominants.includes('Acer rubrum'));
  assert.ok(dominants.includes('Liquidambar styraciflua'));
  assert.ok(dominants.includes('Nyssa sylvatica'));
  assert.ok(dominants.includes('Quercus nigra'));
  assert.ok(!dominants.includes('Fagus grandifolia'));
});

test('calculatePrevalenceIndex: Matches USACE arithmetic half-up precision', () => {
  // Example from USACE manual:
  // OBL = 20, FACW = 30, FAC = 20, FACU = 20, UPL = 10. Total cover = 100.
  // Weighted: 20*1 + 30*2 + 20*3 + 20*4 + 10*5 = 20 + 60 + 60 + 80 + 50 = 270.
  // PI = 270 / 100 = 2.70 <= 3.00 -> PASS
  const species: SpeciesEntry[] = [
    { id: '1', plot_id: 'p', stratum: 'herb', taxon: 'A', usda_symbol: 'A', percent_cover: 20, indicator_status: 'OBL' },
    { id: '2', plot_id: 'p', stratum: 'herb', taxon: 'B', usda_symbol: 'B', percent_cover: 30, indicator_status: 'FACW' },
    { id: '3', plot_id: 'p', stratum: 'herb', taxon: 'C', usda_symbol: 'C', percent_cover: 20, indicator_status: 'FAC' },
    { id: '4', plot_id: 'p', stratum: 'herb', taxon: 'D', usda_symbol: 'D', percent_cover: 20, indicator_status: 'FACU' },
    { id: '5', plot_id: 'p', stratum: 'herb', taxon: 'E', usda_symbol: 'E', percent_cover: 10, indicator_status: 'UPL' },
  ];

  const breakdown = calculatePrevalenceIndex(species);
  assert.strictEqual(breakdown.total_cover, 100);
  assert.strictEqual(breakdown.weighted_sum, 270);
  assert.strictEqual(breakdown.rounded_pi, 2.7);
});

test('evaluateHydrophyticVegetation: Strict > 50.0% dominance threshold', () => {
  // Exactly 50.0% FAILS per USACE regulatory standard
  const strataData: Record<StratumType, SpeciesEntry[]> = {
    tree: [
      { id: '1', plot_id: 'p', stratum: 'tree', taxon: 'Hydro', usda_symbol: 'H', percent_cover: 60, indicator_status: 'FAC' },
      { id: '2', plot_id: 'p', stratum: 'tree', taxon: 'Upland', usda_symbol: 'U', percent_cover: 40, indicator_status: 'FACU' },
    ],
    sapling_shrub: [],
    herb: [],
    woody_vine: [],
  };

  // Here: Total = 100. Dominant 50% cutoff is Hydro (60 > 50).
  // But Upland is 40 >= 20% cutoff -> Upland is also dominant!
  // Dominants: Hydro (FAC) and Upland (FACU). Total = 2.
  // Hydro dominants (A) = 1. Total dominants (B) = 2.
  // Dominance % = 1 / 2 = 50.00%.
  // Strict rule: 50.00% FAILS!
  const det = evaluateHydrophyticVegetation(strataData, false);
  assert.strictEqual(det.dominance_test_a, 1);
  assert.strictEqual(det.dominance_test_b, 2);
  assert.strictEqual(det.dominance_test_percent, 50.0);
  assert.strictEqual(det.dominance_test_passed, false);
});
