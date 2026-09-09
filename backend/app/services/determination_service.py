"""Three-parameter USACE wetland determination service."""

from typing import Any, Dict, List, Optional, Sequence, Union

from app.core.exceptions import (
    InconsistentRegionalSupplementError,
    InvalidCoverPercentageError,
)
from app.export.models import PlotDeterminationInput, USACEPlotExportData
from app.wetland.hydrology import evaluate_wetland_hydrology
from app.wetland.models import (
    HydrologyDetermination,
    RegionEnum,
    SoilDetermination,
    SoilHorizon,
    SpeciesCover,
    VegetationDetermination,
    WetlandDeterminationResult,
)
from app.wetland.regions.base import RegionalSupplementPolicy
from app.wetland.soils import evaluate_hydric_soils
from app.wetland.vegetation import evaluate_hydrophytic_vegetation


class DeterminationSynthesis(WetlandDeterminationResult):
    """Domain entity representing a validated three-parameter jurisdictional determination synthesis."""

    @property
    def is_wetland(self) -> bool:
        """Convenience alias for is_jurisdictional_wetland."""
        return self.is_jurisdictional_wetland


class DeterminationService:
    """Decoupled domain service orchestrating USACE three-parameter wetland determinations."""

    @staticmethod
    def validate_vegetation_cover(strata_vegetation: Dict[str, Sequence[SpeciesCover]]) -> None:
        """Audit percent cover values across all strata to enforce regulatory domain limits [0.0, 100.0].

        Raises:
            InvalidCoverPercentageError: If any species has cover < 0.0 or > 100.0.
        """
        for stratum, species_list in strata_vegetation.items():
            for sp in species_list:
                if sp.percent_cover < 0.0 or sp.percent_cover > 100.0:
                    raise InvalidCoverPercentageError(
                        percent_cover=sp.percent_cover,
                        taxon=sp.taxon,
                        stratum=stratum,
                    )

    @staticmethod
    def validate_regional_supplement(region: Union[RegionEnum, str]) -> RegionEnum:
        """Validate that the specified region corresponds to an approved USACE Regional Supplement.

        Raises:
            InconsistentRegionalSupplementError: If region is not EMP or AGCP.
        """
        if isinstance(region, RegionEnum):
            return region

        try:
            return RegionEnum(str(region).strip().upper())
        except (ValueError, KeyError):
            raise InconsistentRegionalSupplementError(region=str(region))

    def evaluate_vegetation(
        self,
        strata_vegetation: Dict[str, Sequence[SpeciesCover]],
        enable_morphological_adaptations: bool = True,
        policy: Optional[Union[RegionalSupplementPolicy, RegionEnum, str]] = None,
    ) -> VegetationDetermination:
        """Execute 50/20 dominance, Rapid Test, Dominance Test, and Prevalence Index evaluations."""
        self.validate_vegetation_cover(strata_vegetation)
        return evaluate_hydrophytic_vegetation(
            strata_data=strata_vegetation,
            enable_morphological_adaptations=enable_morphological_adaptations,
            policy=policy,
        )

    def evaluate_soils(
        self,
        soil_horizons: Sequence[SoilHorizon],
        policy: Optional[Union[RegionalSupplementPolicy, RegionEnum, str]] = None,
    ) -> SoilDetermination:
        """Evaluate soil horizons against NRCS Field Indicators of Hydric Soils v8.2."""
        return evaluate_hydric_soils(soil_horizons, policy=policy)

    def evaluate_hydrology(
        self,
        region: Union[RegionalSupplementPolicy, RegionEnum, str],
        hydrology_indicators: Sequence[str],
        dominants: Optional[Sequence[SpeciesCover]] = None,
    ) -> HydrologyDetermination:
        """Evaluate observed hydrology indicators and compute automated FAC-Neutral test (D5)."""
        valid_region = self.validate_regional_supplement(region)
        return evaluate_wetland_hydrology(
            region=valid_region,
            observed_indicators=hydrology_indicators,
            dominants=dominants,
        )

    def synthesize_determination(
        self,
        plot: Union[USACEPlotExportData, Dict[str, Any]],
        enable_morphological_adaptations: bool = True,
    ) -> DeterminationSynthesis:
        """Synthesize a complete three-parameter USACE jurisdictional wetland determination.

        Accepts a USACEPlotExportData Pydantic model or raw dict, executes the
        evaluations across Vegetation, Soils, and Hydrology, and returns a validated
        DeterminationSynthesis object.

        Raises:
            InvalidCoverPercentageError: If any species percent cover is out of bounds.
            InconsistentRegionalSupplementError: If region is unrecognized.
        """
        if isinstance(plot, dict):
            plot_data = USACEPlotExportData(**plot)
        else:
            plot_data = plot

        region = self.validate_regional_supplement(plot_data.region)

        # 1. Vegetation Parameter (50/20 Dominance & Prevalence Index with policy)
        veg_det = self.evaluate_vegetation(
            strata_vegetation=plot_data.strata_vegetation,
            enable_morphological_adaptations=enable_morphological_adaptations,
            policy=region,
        )

        # 2. Soils Parameter (NRCS Field Indicators v8.2 with policy)
        soil_det = self.evaluate_soils(plot_data.soil_horizons, policy=region)

        # 3. Hydrology Parameter (Passing vegetation dominants for FAC-Neutral D5 with policy)
        hydro_det = self.evaluate_hydrology(
            region=region,
            hydrology_indicators=plot_data.hydrology_indicators,
            dominants=veg_det.all_dominants,
        )

        # 4. Three-Parameter Jurisdictional Synthesis
        is_wetland = (
            veg_det.hydrophytic_vegetation_present
            and soil_det.hydric_soil_present
            and hydro_det.wetland_hydrology_present
        )

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
                f"Plot {plot_data.sampling_point} ({region.value}): JURISDICTIONAL WETLAND CRITERIA SATISFIED. "
                f"All three mandatory parameters confirmed: {', '.join(params_met)}."
            )
        else:
            summary = (
                f"Plot {plot_data.sampling_point} ({region.value}): NON-WETLAND / UPLAND DETERMINATION. "
                f"Failed parameter(s): {', '.join(params_failed)}. "
                f"Met parameter(s): {', '.join(params_met) if params_met else 'None'}."
            )

        return DeterminationSynthesis(
            plot_id=plot_data.sampling_point,
            region=region,
            hydrophytic_vegetation=veg_det,
            hydric_soils=soil_det,
            wetland_hydrology=hydro_det,
            is_jurisdictional_wetland=is_wetland,
            summary=summary,
        )

    def evaluate_batch(
        self,
        plots: List[PlotDeterminationInput],
        region: str = "EMP",
    ) -> List[DeterminationSynthesis]:
        """Evaluate a batch of USACE sampling plots with high-throughput in-memory execution.

        Args:
            plots: List of PlotDeterminationInput records to evaluate.
            region: Approved USACE Regional Supplement ('EMP' or 'AGCP').

        Returns:
            List of synthesized DeterminationSynthesis three-parameter jurisdictional determinations.

        Raises:
            InconsistentRegionalSupplementError: If region is not recognized.
            InvalidCoverPercentageError: If any plot has species cover outside [0.0, 100.0].
        """
        valid_region = self.validate_regional_supplement(region)
        results: List[DeterminationSynthesis] = []

        for plot in plots:
            if isinstance(plot, dict):
                p_copy = dict(plot)
                p_copy["region"] = valid_region
                plot_input = PlotDeterminationInput(**p_copy)
            elif isinstance(plot, (PlotDeterminationInput, USACEPlotExportData)):
                plot_input = plot.model_copy()
                plot_input.region = valid_region
            else:
                plot_input = PlotDeterminationInput.model_validate(plot)
                plot_input.region = valid_region

            results.append(self.synthesize_determination(plot_input))

        return results

