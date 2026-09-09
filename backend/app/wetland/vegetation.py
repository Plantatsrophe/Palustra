"""Hydrophytic vegetation mathematical logic adhering to USACE 1987 Manual & Regional Supplements."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union
from app.wetland.models import (
    SpeciesCover,
    StratumDominanceResult,
    VegetationDetermination,
)
from app.wetland.regions.base import RegionalSupplementPolicy
from app.wetland.regions.factory import RegionalPolicyFactory

INDICATOR_WEIGHTS: Dict[str, int] = {
    "OBL": 1,
    "FACW": 2,
    "FAC": 3,
    "FACU": 4,
    "UPL": 5,
    "NL": 5,
}

HYDROPHYTIC_DOMINANT_INDICATORS: set[str] = {"OBL", "FACW", "FAC"}
RAPID_TEST_INDICATORS: set[str] = {"OBL", "FACW"}


def calculate_stratum_50_20(
    stratum_name: str,
    species_list: Sequence[SpeciesCover],
) -> StratumDominanceResult:
    """Calculate dominant plant species for a single stratum using the exact 50/20 rule with tie-breaking.

    Algorithm:
    1. Total stratum cover T = sum of percent cover for all species in the stratum.
    2. Rank species in descending order of percent cover.
       (Ties in cover are sorted alphabetically by taxon for deterministic reproducibility).
    3. Calculate 50% threshold: T_50 = 0.50 * T.
    4. Calculate 20% threshold: T_20 = 0.20 * T.
    5. 50% Rule: Accumulate cover from highest to lowest until running sum is strictly
       greater than T_50 (> 0.50 * T).
    6. Exact Tie-Breaking Rule at 50% Cutoff: If one or more species are tied in cover
       with the species that crosses the 50% cutoff, ALL tied species must be included.
    7. 20% Rule: Include any additional species with percent cover >= T_20.
    """
    # Filter to species with positive cover
    active_species = [s.model_copy() for s in species_list if s.percent_cover > 0.0]
    total_cover = sum(s.percent_cover for s in active_species)

    if total_cover <= 0.0:
        return StratumDominanceResult(
            stratum=stratum_name,
            total_cover=0.0,
            threshold_50=0.0,
            threshold_20=0.0,
            dominants=[],
            all_species=[],
        )

    # Deterministic descending sort: primary by percent_cover (desc), secondary by taxon (asc)
    ranked = sorted(active_species, key=lambda s: (-s.percent_cover, s.taxon))

    threshold_50 = 0.50 * total_cover
    threshold_20 = 0.20 * total_cover

    # 50% Dominance Set with tie-breaking
    cumulative_cover = 0.0
    cutoff_index = -1
    d50_species: List[SpeciesCover] = []

    for idx, sp in enumerate(ranked):
        cumulative_cover += sp.percent_cover
        d50_species.append(sp)
        # Check strict inequality: running sum strictly greater than 50% of total
        if cumulative_cover > threshold_50:
            cutoff_index = idx
            break

    tied_50: List[SpeciesCover] = []
    if cutoff_index >= 0:
        cutoff_cover = ranked[cutoff_index].percent_cover
        # Check if any subsequent species share the exact same cover as the cutoff species
        for sp in ranked[cutoff_index + 1:]:
            if sp.percent_cover == cutoff_cover:
                tied_50.append(sp)
            else:
                break

    # 20% Dominance Set: any species with cover >= 20% total cover
    d20_species = [sp for sp in ranked if sp.percent_cover >= threshold_20]

    # Combine all dominants preserving unique taxa
    dominant_taxa: set[str] = set()
    combined_dominants: List[SpeciesCover] = []

    for sp in ranked:
        is_dom = (
            sp in d50_species
            or sp in tied_50
            or sp in d20_species
        )
        if is_dom and sp.taxon not in dominant_taxa:
            dominant_taxa.add(sp.taxon)
            dom_copy = sp.model_copy()
            dom_copy.is_dominant = True
            dom_copy.stratum = stratum_name
            combined_dominants.append(dom_copy)

    # Mark is_dominant flag in all_species output
    all_output: List[SpeciesCover] = []
    for sp in ranked:
        sp_copy = sp.model_copy()
        sp_copy.is_dominant = sp.taxon in dominant_taxa
        sp_copy.stratum = stratum_name
        all_output.append(sp_copy)

    return StratumDominanceResult(
        stratum=stratum_name,
        total_cover=round(total_cover, 4),
        threshold_50=round(threshold_50, 4),
        threshold_20=round(threshold_20, 4),
        cumulative_50_species=[s.taxon for s in d50_species],
        tied_50_species=[s.taxon for s in tied_50],
        species_20_set=[s.taxon for s in d20_species],
        dominants=combined_dominants,
        all_species=all_output,
    )


def calculate_prevalence_index(
    all_plot_species: Sequence[SpeciesCover],
) -> Optional[float]:
    """Calculate the Prevalence Index (PI) across all strata using arithmetic half-up rounding.

    Formula:
        PI = sum(w_i * c_i) / sum(c_i)
    where:
        OBL = 1, FACW = 2, FAC = 3, FACU = 4, UPL = 5, NL = 5.
    Returns:
        float rounded to 2 decimal places using ROUND_HALF_UP, or None if total cover == 0.
    """
    total_cover = 0.0
    weighted_sum = 0.0

    for sp in all_plot_species:
        if sp.percent_cover <= 0.0:
            continue
        ind = sp.normalized_indicator
        weight = INDICATOR_WEIGHTS.get(ind, 5)
        total_cover += sp.percent_cover
        weighted_sum += weight * sp.percent_cover

    if total_cover <= 0.0:
        return None

    unrounded_pi = weighted_sum / total_cover
    # Exact arithmetic half-up rounding to 2 decimal places
    d_pi = Decimal(str(unrounded_pi)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d_pi)


def classify_stratum(
    policy: Union[RegionalSupplementPolicy, str],
    dbh_in: Optional[float] = None,
    height_m: Optional[float] = None,
    is_woody: bool = True,
    is_vine: bool = False,
) -> str:
    """Classify a botanical specimen into a regulatory stratum using the regional supplement policy."""
    policy_instance = RegionalPolicyFactory.get_policy(policy)
    definitions = policy_instance.get_stratum_definitions()

    for name, criteria in definitions.items():
        if criteria.matches(dbh_in=dbh_in, height_m=height_m, is_woody=is_woody, is_vine=is_vine):
            return criteria.name
    return "Herb"


def evaluate_hydrophytic_vegetation(
    strata_data: Dict[str, Sequence[SpeciesCover]],
    enable_morphological_adaptations: bool = True,
    policy: Optional[Union[RegionalSupplementPolicy, str]] = None,
) -> VegetationDetermination:
    """Evaluate hydrophytic vegetation across all strata following USACE regulatory hierarchy:

    1. Calculate 50/20 dominance independently per stratum.
    2. Rapid Test: True if 100% of dominant species are OBL and/or FACW.
    3. Dominance Test: True if dominant occurrences with status in {OBL, FACW, FAC} strictly exceed 50.0% (> 50.0%).
    4. Prevalence Index: Calculated across all species in plot; passes if PI <= 3.00.
    5. Morphological Adaptations: If Dominance and PI fail, FACU dominants with >=50% adaptations
       are reassigned to FAC and re-evaluated.
    """
    policy_instance: Optional[RegionalSupplementPolicy] = None
    if policy is not None:
        policy_instance = RegionalPolicyFactory.get_policy(policy)

    # Process strata data: resolve missing or regionally-specific indicator statuses via policy
    processed_strata: Dict[str, List[SpeciesCover]] = {}
    for stratum_name, species_list in strata_data.items():
        processed_list = []
        for sp in species_list:
            sp_copy = sp.model_copy()
            if policy_instance is not None:
                # If indicator is not provided, or taxon has a policy-specific rating
                policy_rating = policy_instance.get_indicator_status(sp.taxon, sp.indicator_status or "NL")
                if policy_rating and policy_rating != "NL":
                    sp_copy.indicator_status = policy_rating
                elif not sp_copy.indicator_status:
                    sp_copy.indicator_status = "NL"
            processed_list.append(sp_copy)
        processed_strata[stratum_name] = processed_list

    # 1. Run 50/20 rule per stratum
    strata_results: Dict[str, StratumDominanceResult] = {}
    all_dominants: List[SpeciesCover] = []
    all_species_flat: List[SpeciesCover] = []

    for stratum_name, species_list in processed_strata.items():
        res = calculate_stratum_50_20(stratum_name, species_list)
        strata_results[stratum_name] = res
        all_dominants.extend(res.dominants)
        all_species_flat.extend(res.all_species)

    # 2. Rapid Test Evaluation
    if all_dominants:
        rapid_test_passed = all(
            d.normalized_indicator in RAPID_TEST_INDICATORS for d in all_dominants
        )
    else:
        rapid_test_passed = False

    # 3. Dominance Test Evaluation
    b_total_dominants = len(all_dominants)
    a_hydrophytic_dominants = sum(
        1 for d in all_dominants if d.normalized_indicator in HYDROPHYTIC_DOMINANT_INDICATORS
    )

    if b_total_dominants > 0:
        dominance_percent = (a_hydrophytic_dominants / b_total_dominants) * 100.0
        # Strict inequality: must be strictly > 50.0% (50.00% FAILS)
        dominance_test_passed = dominance_percent > 50.0
    else:
        dominance_percent = 0.0
        dominance_test_passed = False

    # 4. Prevalence Index Evaluation
    pi_value = calculate_prevalence_index(all_species_flat)
    pi_passed = (pi_value is not None) and (pi_value <= 3.00)

    # Initial hydrophytic determination
    hydrophytic_present = rapid_test_passed or dominance_test_passed or pi_passed
    remarks: List[str] = []

    if rapid_test_passed:
        remarks.append("Rapid Test PASSED: 100% of dominant species are OBL/FACW.")
    elif dominance_test_passed:
        remarks.append(
            f"Dominance Test PASSED: {dominance_percent:.1f}% (>50%) of dominant species are OBL, FACW, or FAC."
        )
    elif pi_passed:
        remarks.append(
            f"Prevalence Index PASSED: PI = {pi_value:.2f} (<= 3.00)."
        )

    # 5. Morphological Adaptations Workflow
    if not hydrophytic_present and enable_morphological_adaptations:
        facu_adapted = [
            d for d in all_dominants
            if d.normalized_indicator == "FACU" and d.has_morphological_adaptations
        ]
        if facu_adapted:
            # Reassign FACU with adaptations to FAC
            remarks.append(
                f"Applying Morphological Adaptations: {len(facu_adapted)} FACU dominant(s) reassigned to FAC."
            )
            adjusted_dominants = []
            for d in all_dominants:
                if d in facu_adapted:
                    adj = d.model_copy()
                    adj.indicator_status = "FAC"
                    adjusted_dominants.append(adj)
                else:
                    adjusted_dominants.append(d)

            a_adj = sum(
                1 for d in adjusted_dominants if d.normalized_indicator in HYDROPHYTIC_DOMINANT_INDICATORS
            )
            dominance_percent_adj = (a_adj / b_total_dominants) * 100.0
            dominance_passed_adj = dominance_percent_adj > 50.0

            # Also adjust all_species for PI recalculation
            adjusted_flat = []
            for sp in all_species_flat:
                if any(sp.taxon == fa.taxon for fa in facu_adapted):
                    adj_sp = sp.model_copy()
                    adj_sp.indicator_status = "FAC"
                    adjusted_flat.append(adj_sp)
                else:
                    adjusted_flat.append(sp)

            pi_adj = calculate_prevalence_index(adjusted_flat)
            pi_passed_adj = (pi_adj is not None) and (pi_adj <= 3.00)

            if dominance_passed_adj or pi_passed_adj:
                hydrophytic_present = True
                dominance_test_passed = dominance_passed_adj
                dominance_percent = dominance_percent_adj
                a_hydrophytic_dominants = a_adj
                pi_value = pi_adj
                pi_passed = pi_passed_adj
                remarks.append("Hydrophytic vegetation satisfied via Morphological Adaptations recalculation.")

    if not hydrophytic_present:
        remarks.append(
            f"Hydrophytic Vegetation FAILED: Dominance = {dominance_percent:.1f}%, PI = "
            + (f"{pi_value:.2f}" if pi_value is not None else "N/A")
        )

    return VegetationDetermination(
        rapid_test_passed=rapid_test_passed,
        dominance_test_a=a_hydrophytic_dominants,
        dominance_test_b=b_total_dominants,
        dominance_test_percent=round(dominance_percent, 2),
        dominance_test_passed=dominance_test_passed,
        prevalence_index=pi_value,
        prevalence_index_passed=pi_passed,
        hydrophytic_vegetation_present=hydrophytic_present,
        strata_results=strata_results,
        all_dominants=all_dominants,
        remarks=remarks,
    )
