"""Three-parameter jurisdictional wetland determination synthesis engine."""

from typing import Dict, List, Optional, Sequence, Union
from app.wetland.hydrology import evaluate_wetland_hydrology
from app.wetland.models import (
    RegionEnum,
    SoilHorizon,
    SpeciesCover,
    WetlandDeterminationResult,
)
from app.wetland.regions.base import RegionalSupplementPolicy
from app.wetland.regions.factory import RegionalPolicyFactory
from app.wetland.soils import evaluate_hydric_soils
from app.wetland.vegetation import evaluate_hydrophytic_vegetation


def perform_jurisdictional_wetland_determination(
    plot_id: str,
    region: Union[RegionalSupplementPolicy, RegionEnum, str],
    strata_vegetation: Dict[str, Sequence[SpeciesCover]],
    soil_horizons: Sequence[SoilHorizon],
    hydrology_indicators: Sequence[str],
    enable_morphological_adaptations: bool = True,
) -> WetlandDeterminationResult:
    """Execute complete three-parameter USACE jurisdictional wetland evaluation using policy injection.

    Parameters:
    1. Hydrophytic Vegetation: Evaluated via 50/20 dominance, Rapid Test, Dominance Test,
       and Prevalence Index, with regional taxa indicator lookup.
    2. Hydric Soils: Evaluated against NRCS Field Indicators (A11, A12, F3, F6, S5, F19, F20)
       filtered by regional supplement approval.
    3. Wetland Hydrology: Evaluated via primary/secondary regional criteria and automated
       FAC-Neutral (D5) secondary indicator.

    Jurisdictional Wetland Status:
        Confirmed iff Hydrophytic Vegetation AND Hydric Soils AND Wetland Hydrology are ALL True.
    """
    policy = RegionalPolicyFactory.get_policy(region)
    region_enum = policy.region_code

    # 1. Vegetation Parameter
    veg_det = evaluate_hydrophytic_vegetation(
        strata_data=strata_vegetation,
        enable_morphological_adaptations=enable_morphological_adaptations,
        policy=policy,
    )

    # 2. Soils Parameter
    soil_det = evaluate_hydric_soils(
        horizons=soil_horizons,
        policy=policy,
    )

    # 3. Hydrology Parameter (passing dominants to automatically run FAC-Neutral D5)
    hydro_det = evaluate_wetland_hydrology(
        region=policy,
        observed_indicators=hydrology_indicators,
        dominants=veg_det.all_dominants,
    )

    # 4. Three-Parameter Synthesis
    is_wetland = (
        veg_det.hydrophytic_vegetation_present
        and soil_det.hydric_soil_present
        and hydro_det.wetland_hydrology_present
    )

    # Executive Summary Text
    params_met: List[str] = []
    params_failed: List[str] = []

    if veg_det.hydrophytic_vegetation_present:
        params_met.append("Hydrophytic Vegetation")
    else:
        params_failed.append("Hydrophytic Vegetation")

    if soil_det.hydric_soil_present:
        params_met.append("Hydric Soils")
    else:
        params_failed.append("Hydric Soils")

    if hydro_det.wetland_hydrology_present:
        params_met.append("Wetland Hydrology")
    else:
        params_failed.append("Wetland Hydrology")

    if is_wetland:
        summary = (
            f"Plot {plot_id} ({region_enum.value}): JURISDICTIONAL WETLAND CRITERIA SATISFIED. "
            f"All three mandatory parameters confirmed: {', '.join(params_met)}."
        )
    else:
        summary = (
            f"Plot {plot_id} ({region_enum.value}): NON-WETLAND / UPLAND DETERMINATION. "
            f"Failed parameter(s): {', '.join(params_failed)}. "
            f"Met parameter(s): {', '.join(params_met) if params_met else 'None'}."
        )

    return WetlandDeterminationResult(
        plot_id=plot_id,
        region=region_enum,
        hydrophytic_vegetation=veg_det,
        hydric_soils=soil_det,
        wetland_hydrology=hydro_det,
        is_jurisdictional_wetland=is_wetland,
        summary=summary,
    )
