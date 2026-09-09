import {
  IndicatorStatus,
  PrevalenceBreakdown,
  SpeciesEntry,
  StratumDominanceResult,
  StratumType,
  VegetationDetermination,
} from './types';

export const INDICATOR_WEIGHTS: Record<IndicatorStatus, number> = {
  OBL: 1,
  FACW: 2,
  FAC: 3,
  FACU: 4,
  UPL: 5,
  NL: 5,
};

export const HYDROPHYTIC_DOMINANTS = new Set<IndicatorStatus>(['OBL', 'FACW', 'FAC']);
export const RAPID_TEST_DOMINANTS = new Set<IndicatorStatus>(['OBL', 'FACW']);

/**
 * Exact arithmetic half-up rounding (ROUND_HALF_UP) per USACE standards.
 */
export function roundHalfUp(value: number, decimals: number = 2): number {
  const factor = Math.pow(10, decimals);
  const sign = value < 0 ? -1 : 1;
  return (sign * Math.round(Math.abs(value) * factor + Number.EPSILON)) / factor;
}

/**
 * Calculates the USACE 50/20 dominance rule for a single stratum.
 */
export function calculateStratum5020(
  stratum: StratumType,
  speciesList: SpeciesEntry[]
): StratumDominanceResult {
  const activeSpecies = speciesList.filter((s) => s.percent_cover > 0);
  const totalCover = activeSpecies.reduce((sum, s) => sum + s.percent_cover, 0);

  if (totalCover <= 0) {
    return {
      stratum,
      total_cover: 0,
      threshold_50: 0,
      threshold_20: 0,
      cumulative_50_species: [],
      tied_50_species: [],
      species_20_set: [],
      dominants: [],
      ranked_species: [],
    };
  }

  // Deterministic descending sort: percent_cover DESC, taxon ASC
  const ranked = [...activeSpecies].sort((a, b) => {
    if (b.percent_cover !== a.percent_cover) {
      return b.percent_cover - a.percent_cover;
    }
    return a.taxon.localeCompare(b.taxon);
  });

  const threshold_50 = 0.5 * totalCover;
  const threshold_20 = 0.2 * totalCover;

  // 1. 50% Rule: Accumulate until strictly > 50% of total
  let cumulative = 0;
  let cutoffIdx = -1;
  const d50Species: SpeciesEntry[] = [];

  for (let i = 0; i < ranked.length; i++) {
    const sp = ranked[i];
    cumulative += sp.percent_cover;
    d50Species.push(sp);
    if (cumulative > threshold_50) {
      cutoffIdx = i;
      break;
    }
  }

  // 2. Exact Tie-Breaking Rule at 50% Cutoff:
  // If subsequent species share the exact cover as the cutoff species, they are included.
  const tied50Species: SpeciesEntry[] = [];
  if (cutoffIdx >= 0 && cutoffIdx < ranked.length - 1) {
    const cutoffCover = ranked[cutoffIdx].percent_cover;
    for (let i = cutoffIdx + 1; i < ranked.length; i++) {
      if (Math.abs(ranked[i].percent_cover - cutoffCover) < 1e-9) {
        tied50Species.push(ranked[i]);
      } else {
        break;
      }
    }
  }

  // 3. 20% Rule: Any species with cover >= 20% of total
  const d20Species = ranked.filter((s) => s.percent_cover >= threshold_20);

  // Combine unique dominants
  const dominantIdSet = new Set<string>();
  const dominants: SpeciesEntry[] = [];

  const checkIsDominant = (sp: SpeciesEntry) =>
    d50Species.some((d) => d.id === sp.id) ||
    tied50Species.some((t) => t.id === sp.id) ||
    d20Species.some((d) => d.id === sp.id);

  for (const sp of ranked) {
    if (checkIsDominant(sp) && !dominantIdSet.has(sp.id)) {
      dominantIdSet.add(sp.id);
      dominants.push({ ...sp, is_dominant: true });
    }
  }

  // Build annotated ranked species ledger
  let runningSum = 0;
  const rankedAnnotated = ranked.map((sp, idx) => {
    runningSum += sp.percent_cover;
    const isD50 = d50Species.some((d) => d.id === sp.id);
    const isTied50 = tied50Species.some((t) => t.id === sp.id);
    const isD20 = d20Species.some((d) => d.id === sp.id);

    return {
      ...sp,
      rank: idx + 1,
      cumulative_cover: roundHalfUp(runningSum, 2),
      cumulative_percent: roundHalfUp((runningSum / totalCover) * 100, 1),
      is_dominant: dominantIdSet.has(sp.id),
      is_d50: isD50,
      is_tied50: isTied50,
      is_d20: isD20,
    };
  });

  return {
    stratum,
    total_cover: roundHalfUp(totalCover, 2),
    threshold_50: roundHalfUp(threshold_50, 2),
    threshold_20: roundHalfUp(threshold_20, 2),
    cumulative_50_species: d50Species.map((s) => s.taxon),
    tied_50_species: tied50Species.map((s) => s.taxon),
    species_20_set: d20Species.map((s) => s.taxon),
    dominants,
    ranked_species: rankedAnnotated,
  };
}

/**
 * Calculates the Prevalence Index (PI) across all plot species.
 */
export function calculatePrevalenceIndex(allSpecies: SpeciesEntry[]): PrevalenceBreakdown {
  let oblCover = 0;
  let facwCover = 0;
  let facCover = 0;
  let facuCover = 0;
  let uplCover = 0;

  for (const sp of allSpecies) {
    if (sp.percent_cover <= 0) continue;
    switch (sp.indicator_status) {
      case 'OBL':
        oblCover += sp.percent_cover;
        break;
      case 'FACW':
        facwCover += sp.percent_cover;
        break;
      case 'FAC':
        facCover += sp.percent_cover;
        break;
      case 'FACU':
        facuCover += sp.percent_cover;
        break;
      case 'UPL':
      case 'NL':
      default:
        uplCover += sp.percent_cover;
        break;
    }
  }

  const totalCover = oblCover + facwCover + facCover + facuCover + uplCover;
  if (totalCover <= 0) {
    return {
      obl_cover: 0,
      facw_cover: 0,
      fac_cover: 0,
      facu_cover: 0,
      upl_cover: 0,
      total_cover: 0,
      weighted_sum: 0,
      raw_pi: null,
      rounded_pi: null,
    };
  }

  const weightedSum =
    oblCover * 1 +
    facwCover * 2 +
    facCover * 3 +
    facuCover * 4 +
    uplCover * 5;

  const rawPI = weightedSum / totalCover;
  const roundedPI = roundHalfUp(rawPI, 2);

  return {
    obl_cover: roundHalfUp(oblCover, 2),
    facw_cover: roundHalfUp(facwCover, 2),
    fac_cover: roundHalfUp(facCover, 2),
    facu_cover: roundHalfUp(facuCover, 2),
    upl_cover: roundHalfUp(uplCover, 2),
    total_cover: roundHalfUp(totalCover, 2),
    weighted_sum: roundHalfUp(weightedSum, 2),
    raw_pi: rawPI,
    rounded_pi: roundedPI,
  };
}

/**
 * Comprehensive evaluation of hydrophytic vegetation across all strata.
 */
export function evaluateHydrophyticVegetation(
  strataData: Record<StratumType, SpeciesEntry[]>,
  enableMorphologicalAdaptations: boolean = true
): VegetationDetermination {
  const strataResults: Record<StratumType, StratumDominanceResult> = {
    tree: calculateStratum5020('tree', strataData.tree || []),
    sapling_shrub: calculateStratum5020('sapling_shrub', strataData.sapling_shrub || []),
    herb: calculateStratum5020('herb', strataData.herb || []),
    woody_vine: calculateStratum5020('woody_vine', strataData.woody_vine || []),
  };

  const allDominants: SpeciesEntry[] = [];
  const allSpeciesFlat: SpeciesEntry[] = [];

  (Object.keys(strataResults) as StratumType[]).forEach((strat) => {
    allDominants.push(...strataResults[strat].dominants);
    allSpeciesFlat.push(...(strataData[strat] || []));
  });

  // 1. Rapid Test: 100% of dominants are OBL or FACW
  const rapidTestPassed =
    allDominants.length > 0 &&
    allDominants.every((d) => RAPID_TEST_DOMINANTS.has(d.indicator_status));

  // 2. Dominance Test: (A / B) * 100 > 50.0%
  const bTotalDominants = allDominants.length;
  const aHydrophyticDominants = allDominants.filter((d) =>
    HYDROPHYTIC_DOMINANTS.has(d.indicator_status)
  ).length;

  let dominancePercent = 0;
  let dominanceTestPassed = false;

  if (bTotalDominants > 0) {
    dominancePercent = roundHalfUp((aHydrophyticDominants / bTotalDominants) * 100, 2);
    // Strict inequality: strictly greater than 50.0% (50.00% FAILS)
    dominanceTestPassed = dominancePercent > 50.0;
  }

  // 3. Prevalence Index
  const prevalenceBreakdown = calculatePrevalenceIndex(allSpeciesFlat);
  const piValue = prevalenceBreakdown.rounded_pi;
  const piPassed = piValue !== null && piValue <= 3.0;

  // Initial determination
  let hydrophyticPresent = rapidTestPassed || dominanceTestPassed || piPassed;
  const remarks: string[] = [];

  if (rapidTestPassed) {
    remarks.push('Rapid Test PASSED: 100% of dominant species are OBL/FACW.');
  } else if (dominanceTestPassed) {
    remarks.push(
      `Dominance Test PASSED: ${dominancePercent.toFixed(1)}% (>50.0%) of dominant species are OBL, FACW, or FAC.`
    );
  } else if (piPassed) {
    remarks.push(
      `Prevalence Index PASSED: PI = ${piValue?.toFixed(2)} (≤ 3.00).`
    );
  }

  // 4. Morphological Adaptations (if Dominance and PI failed)
  if (!hydrophyticPresent && enableMorphologicalAdaptations) {
    const facuWithAdaptations = allDominants.filter(
      (d) => d.indicator_status === 'FACU' && d.has_morphological_adaptations
    );

    if (facuWithAdaptations.length > 0) {
      remarks.push(
        `Morphological Adaptations: ${facuWithAdaptations.length} FACU dominant(s) reassigned to FAC.`
      );
      const adjustedDominants = allDominants.map((d) =>
        d.indicator_status === 'FACU' && d.has_morphological_adaptations
          ? { ...d, indicator_status: 'FAC' as IndicatorStatus }
          : d
      );

      const aAdj = adjustedDominants.filter((d) =>
        HYDROPHYTIC_DOMINANTS.has(d.indicator_status)
      ).length;
      const dominancePercentAdj = roundHalfUp((aAdj / bTotalDominants) * 100, 2);
      const dominancePassedAdj = dominancePercentAdj > 50.0;

      const adjustedFlat = allSpeciesFlat.map((sp) =>
        facuWithAdaptations.some((fa) => fa.id === sp.id || fa.taxon === sp.taxon)
          ? { ...sp, indicator_status: 'FAC' as IndicatorStatus }
          : sp
      );
      const piAdjBreakdown = calculatePrevalenceIndex(adjustedFlat);
      const piPassedAdj =
        piAdjBreakdown.rounded_pi !== null && piAdjBreakdown.rounded_pi <= 3.0;

      if (dominancePassedAdj || piPassedAdj) {
        hydrophyticPresent = true;
        remarks.push('Hydrophytic vegetation satisfied via Morphological Adaptations.');
      }
    }
  }

  if (!hydrophyticPresent) {
    remarks.push(
      `Hydrophytic Vegetation FAILED: Dominance = ${dominancePercent.toFixed(1)}%, PI = ${
        piValue !== null ? piValue.toFixed(2) : 'N/A'
      }`
    );
  }

  return {
    rapid_test_passed: rapidTestPassed,
    dominance_test_a: aHydrophyticDominants,
    dominance_test_b: bTotalDominants,
    dominance_test_percent: dominancePercent,
    dominance_test_passed: dominanceTestPassed,
    prevalence_index: piValue,
    prevalence_index_passed: piPassed,
    prevalence_breakdown: prevalenceBreakdown,
    hydrophytic_vegetation_present: hydrophyticPresent,
    strata_results: strataResults,
    all_dominants: allDominants,
    remarks,
  };
}
