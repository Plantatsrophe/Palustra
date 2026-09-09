"""Wetland hydrology decision logic with regional tier switching and automated FAC-Neutral test."""

from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union
from palustra.wetland.models import (
    FACNeutralResult,
    HydrologyDetermination,
    HydrologyObservation,
    RegionEnum,
    SpeciesCover,
)
from palustra.wetland.regions.base import RegionalSupplementPolicy
from palustra.wetland.regions.factory import RegionalPolicyFactory

# Regional indicator tier lookup: Indicator Code -> (AGCP Tier, EMP Tier)
# Tier values: "Primary", "Secondary", "Not Recognized"
REGIONAL_HYDROLOGY_TIERS: Dict[str, Tuple[str, str]] = {
    # Group A: Surface Water / Saturated Soils
    "A1": ("Primary", "Primary"),
    "A2": ("Primary", "Primary"),
    "A3": ("Primary", "Primary"),
    # Group B: Evidence of Inundation
    "B1": ("Primary", "Primary"),
    "B2": ("Primary", "Primary"),
    "B3": ("Primary", "Primary"),
    "B4": ("Primary", "Primary"),
    "B5": ("Primary", "Primary"),
    "B6": ("Primary", "Secondary"),   # Surface Soil Cracks: Primary in AGCP, Secondary in EMP
    "B7": ("Primary", "Primary"),
    "B8": ("Primary", "Primary"),
    "B9": ("Primary", "Secondary"),   # Water-Stained Leaves: Primary in AGCP, Secondary in EMP
    "B10": ("Secondary", "Secondary"),
    "B11": ("Primary", "Primary"),
    "B12": ("Secondary", "Secondary"),
    "B13": ("Primary", "Primary"),
    "B14": ("Primary", "Primary"),
    "B15": ("Primary", "Primary"),
    "B16": ("Secondary", "Secondary"),
    # Group C: Evidence of Soil Saturation
    "C1": ("Primary", "Primary"),
    "C2": ("Secondary", "Secondary"),
    "C3": ("Primary", "Primary"),
    "C4": ("Primary", "Primary"),
    "C5": ("Primary", "Primary"),
    "C6": ("Primary", "Primary"),
    "C7": ("Primary", "Primary"),
    "C8": ("Secondary", "Secondary"),
    "C9": ("Secondary", "Secondary"),
    # Group D: Other Site Conditions
    "D1": ("Secondary", "Secondary"),
    "D2": ("Secondary", "Secondary"),
    "D3": ("Secondary", "Secondary"),
    "D4": ("Secondary", "Secondary"),
    "D5": ("Secondary", "Secondary"),   # FAC-Neutral Test
    "D6": ("Not Recognized", "Secondary"),  # Sphagnum Moss: EMP only
    "D7": ("Not Recognized", "Secondary"),  # Frost-Heave Hummocks: EMP only
}

INDICATOR_NAMES: Dict[str, str] = {
    "A1": "Surface Water",
    "A2": "High Water Table",
    "A3": "Saturation",
    "B1": "Water Marks",
    "B2": "Sediment Deposits",
    "B3": "Drift Deposits",
    "B4": "Algal Mat or Crust",
    "B5": "Iron Deposits",
    "B6": "Surface Soil Cracks",
    "B7": "Inundation Visible on Aerial Imagery",
    "B8": "Sparsely Vegetated Concave Surface",
    "B9": "Water-Stained Leaves",
    "B10": "Drainage Patterns",
    "B11": "Salt Crust",
    "B12": "Biogenic Tool Marks",
    "B13": "Aquatic Invertebrates",
    "B14": "True Aquatic Plants",
    "B15": "Marl Deposits",
    "B16": "Moss Trim Lines",
    "C1": "Hydrogen Sulfide Odor",
    "C2": "Dry-Season Water Table",
    "C3": "Oxidized Rhizospheres on Living Roots",
    "C4": "Presence of Reduced Iron",
    "C5": "Salt Glands",
    "C6": "Recent Iron Reduction in Tilled Soils",
    "C7": "Thin Muck Surface",
    "C8": "Crayfish Burrows",
    "C9": "Saturation Visible on Aerial Imagery",
    "D1": "Stunted or Stressed Plants",
    "D2": "Geomorphic Position",
    "D3": "Shallow Aquitard",
    "D4": "Microtopographic Relief",
    "D5": "FAC-Neutral Test",
    "D6": "Sphagnum Moss",
    "D7": "Frost-Heave Hummocks",
}


def compute_fac_neutral_test(
    dominants: Sequence[SpeciesCover],
) -> FACNeutralResult:
    """Calculate the USACE FAC-Neutral Test (Indicator D5) from dominant species across all strata.

    Algorithm:
    1. Exclude all species with indicator status 'FAC'.
    2. Count N_wet: dominant occurrences that are OBL or FACW.
    3. Count N_dry: dominant occurrences that are FACU, UPL, or NL.
    4. Pass iff N_wet > N_dry.
    """
    n_wet = 0
    n_dry = 0
    n_fac = 0

    for dom in dominants:
        ind = dom.normalized_indicator
        if ind in ("OBL", "FACW"):
            n_wet += 1
        elif ind in ("FACU", "UPL", "NL"):
            n_dry += 1
        elif ind == "FAC":
            n_fac += 1

    passed = n_wet > n_dry
    return FACNeutralResult(
        n_wet=n_wet,
        n_dry=n_dry,
        n_fac=n_fac,
        passed=passed,
        indicator_d5_positive=passed,
    )


def get_indicator_tier(
    indicator_code: str,
    region: Union[RegionalSupplementPolicy, RegionEnum, str],
) -> str:
    """Return the regulatory tier ('Primary', 'Secondary', or 'Not Recognized') for an indicator in a region."""
    policy = RegionalPolicyFactory.get_policy(region)
    return policy.get_hydrology_tier(indicator_code)


def evaluate_wetland_hydrology(
    region: Union[RegionalSupplementPolicy, RegionEnum, str],
    observed_indicators: Sequence[str],
    dominants: Optional[Sequence[SpeciesCover]] = None,
) -> HydrologyDetermination:
    """Evaluate wetland hydrology compliance under the specified USACE Regional Supplement policy.

    Core Rule:
        Wetland Hydrology is PRESENT if:
        - At least ONE (1) Primary Indicator is confirmed; OR
        - At least TWO (2) Secondary Indicators are confirmed.

    Automated FAC-Neutral Integration:
        If `dominants` is provided, Indicator D5 is computed automatically.
        If D5 passes (N_wet > N_dry), D5 is automatically added to confirmed secondary indicators.
    """
    policy = RegionalPolicyFactory.get_policy(region)
    region_enum = policy.region_code

    confirmed_primary: List[str] = []
    confirmed_secondary: List[str] = []
    remarks: List[str] = []

    # Clean and deduplicate observed indicator codes
    active_codes: Set[str] = {c.strip().upper() for c in observed_indicators if c.strip()}

    # Automated D5 Calculation
    fac_result: Optional[FACNeutralResult] = None
    if dominants is not None and len(dominants) > 0:
        fac_result = compute_fac_neutral_test(dominants)
        if fac_result.passed:
            active_codes.add("D5")
            remarks.append(
                f"FAC-Neutral Test (D5) is POSITIVE: N_wet ({fac_result.n_wet}) > N_dry ({fac_result.n_dry}) "
                f"[{fac_result.n_fac} FAC excluded]. Added as Secondary Indicator."
            )
        else:
            remarks.append(
                f"FAC-Neutral Test (D5) is NEGATIVE: N_wet ({fac_result.n_wet}) <= N_dry ({fac_result.n_dry}) "
                f"[{fac_result.n_fac} FAC excluded]."
            )

    # Classify each indicator according to the polymorphic policy
    for code in sorted(active_codes):
        tier = policy.get_hydrology_tier(code)
        name = INDICATOR_NAMES.get(code, code)

        if tier == "Primary":
            confirmed_primary.append(code)
            remarks.append(f"Confirmed Primary Indicator: {code} - {name} ({region_enum.value}).")
        elif tier == "Secondary":
            confirmed_secondary.append(code)
            remarks.append(f"Confirmed Secondary Indicator: {code} - {name} ({region_enum.value}).")
        else:
            remarks.append(
                f"Indicator {code} ({name}) is NOT RECOGNIZED in the {region_enum.value} regional supplement."
            )

    # Decision logic delegated to policy strategy
    hydrology_present = policy.validate_hydrology_indicators(confirmed_primary, confirmed_secondary)

    if hydrology_present:
        if len(confirmed_primary) >= 1:
            decision_basis = f"{len(confirmed_primary)} Primary Indicator(s)"
        else:
            decision_basis = f"{len(confirmed_secondary)} Secondary Indicators"
        remarks.append(f"Wetland Hydrology Criterion SATISFIED via {decision_basis}.")
    else:
        remarks.append(
            f"Wetland Hydrology Criterion NOT MET: Found {len(confirmed_primary)} Primary and "
            f"{len(confirmed_secondary)} Secondary (requires >= 1 Primary or >= 2 Secondary)."
        )

    return HydrologyDetermination(
        region=region_enum,
        primary_indicators=confirmed_primary,
        secondary_indicators=confirmed_secondary,
        fac_neutral=fac_result,
        wetland_hydrology_present=hydrology_present,
        remarks=remarks,
    )
