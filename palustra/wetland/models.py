"""Data models and regulatory schemas for USACE wetland determinations."""

from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field, field_validator


from palustra.wetland.regions.base import RegionalSupplementEnum, StratumCriteria

# Preserve backward compatibility while adopting extensible RegionalSupplementEnum
RegionEnum = RegionalSupplementEnum


class IndicatorStatus(str, Enum):
    OBL = "OBL"
    FACW = "FACW"
    FAC = "FAC"
    FACU = "FACU"
    UPL = "UPL"
    NL = "NL"


class StratumEnum(str, Enum):
    TREE = "Tree"
    SAPLING_SHRUB = "Sapling/Shrub"
    HERB = "Herb"
    WOODY_VINE = "Woody Vine"


class SpeciesCover(BaseModel):
    """Vegetation occurrence in a specific stratum."""

    model_config = ConfigDict(extra="ignore")

    taxon: str = Field(..., description="Scientific or vernacular plant taxon identifier.")
    percent_cover: float = Field(..., ge=0.0, le=100.0, description="Absolute percent cover in the stratum.")
    indicator_status: Optional[str] = Field(None, description="Regional NWPL indicator status (e.g., OBL, FACW, FAC, FACU, UPL).")
    stratum: Optional[str] = Field(None, description="Vegetation stratum.")
    has_morphological_adaptations: bool = Field(False, description="True if >= 50% of individuals exhibit adaptations.")
    is_dominant: bool = Field(False, description="Flag assigned by 50/20 dominance algorithm.")

    @property
    def normalized_indicator(self) -> str:
        """Normalize indicator status (stripping +/- modifiers to base NWPL indicator)."""
        if not self.indicator_status:
            return "NL"
        raw = self.indicator_status.strip().upper()
        # Handle modifiers like FACW+, FAC-, etc.
        for base in ("FACW", "FACU", "FAC", "OBL", "UPL"):
            if raw.startswith(base):
                return base
        return "NL"


class StratumDominanceResult(BaseModel):
    """Detailed 50/20 dominance evaluation for a single vegetation stratum."""

    stratum: str
    total_cover: float
    threshold_50: float
    threshold_20: float
    cumulative_50_species: List[str] = Field(default_factory=list, description="Species in the descending sequence meeting >50% cover.")
    tied_50_species: List[str] = Field(default_factory=list, description="Species tied at the 50% boundary cutoff.")
    species_20_set: List[str] = Field(default_factory=list, description="Species with individual cover >= 20% total cover.")
    dominants: List[SpeciesCover] = Field(default_factory=list, description="Final combined list of dominant species.")
    all_species: List[SpeciesCover] = Field(default_factory=list, description="All species ranked in descending cover order.")


class VegetationDetermination(BaseModel):
    """Summary of hydrophytic vegetation evaluation across all strata."""

    rapid_test_passed: bool = Field(..., description="True if 100% of dominant species are OBL and/or FACW.")
    dominance_test_a: int = Field(..., description="Number of dominant occurrences that are OBL, FACW, or FAC.")
    dominance_test_b: int = Field(..., description="Total number of dominant occurrences across all strata.")
    dominance_test_percent: float = Field(..., description="(A / B) * 100.")
    dominance_test_passed: bool = Field(..., description="True if dominance percentage is strictly > 50.0%.")
    prevalence_index: Optional[float] = Field(None, description="Calculated Prevalence Index rounded to 2 decimals.")
    prevalence_index_passed: Optional[bool] = Field(None, description="True if Prevalence Index <= 3.00.")
    hydrophytic_vegetation_present: bool = Field(..., description="Final determination for hydrophytic vegetation parameter.")
    strata_results: Dict[str, StratumDominanceResult] = Field(default_factory=dict)
    all_dominants: List[SpeciesCover] = Field(default_factory=list)
    remarks: List[str] = Field(default_factory=list)


class SoilHorizon(BaseModel):
    """Field description of a soil layer/horizon in a soil pit."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field("A", description="Horizon designation (e.g. A, Btg, C).")
    top_depth_cm: float = Field(..., ge=0.0, description="Upper boundary depth in cm.")
    bottom_depth_cm: float = Field(..., gt=0.0, description="Lower boundary depth in cm.")
    matrix_hue: str = Field(..., description="Munsell Hue (e.g., '10YR', '2.5Y', '5Y', 'GLEY1', 'N').")
    matrix_value: float = Field(..., ge=0.0, le=10.0, description="Munsell Value.")
    matrix_chroma: float = Field(..., ge=0.0, le=20.0, description="Munsell Chroma.")
    texture: str = Field("loam", description="Soil texture: sand, loamy sand, sandy loam, loam, clay loam, clay, etc.")
    redox_percent: float = Field(0.0, ge=0.0, le=100.0, description="Abundance of redox concentrations in percent.")
    redox_distinctness: str = Field("distinct", description="'faint', 'distinct', or 'prominent'.")
    redox_hue: Optional[str] = Field(None, description="Munsell hue of redox concentrations.")
    redox_value: Optional[float] = Field(None, description="Munsell value of redox concentrations.")
    redox_chroma: Optional[float] = Field(None, description="Munsell chroma of redox concentrations.")
    is_organic: bool = Field(False, description="True if organic soil material (peat/muck).")

    @property
    def thickness_cm(self) -> float:
        return max(0.0, self.bottom_depth_cm - self.top_depth_cm)

    @property
    def is_sandy(self) -> bool:
        """Evaluate if texture falls under sandy USDA classification."""
        sandy_textures = {"sand", "coarse sand", "fine sand", "very fine sand", "loamy sand", "loamy fine sand", "loamy coarse sand"}
        return any(s in self.texture.lower() for s in sandy_textures)

    @property
    def is_loamy_clayey(self) -> bool:
        """Evaluate if texture is loamy or clayey."""
        return not self.is_sandy and not self.is_organic


class HydricSoilIndicatorResult(BaseModel):
    """Result of evaluating a specific NRCS hydric soil indicator."""

    code: str = Field(..., description="NRCS indicator code (e.g., A11, A12, F3, F6, S5).")
    name: str = Field(..., description="Indicator name.")
    confirmed: bool = Field(..., description="True if horizon sequence satisfies criteria.")
    qualifying_layers: List[str] = Field(default_factory=list, description="Horizons meeting the criteria.")
    rationale: str = Field("", description="Audit explanation.")


class SoilDetermination(BaseModel):
    """Evaluation of the hydric soils parameter."""

    hydric_soil_present: bool = Field(..., description="True if at least one hydric soil indicator is confirmed.")
    indicators_evaluated: List[HydricSoilIndicatorResult] = Field(default_factory=list)
    confirmed_indicators: List[str] = Field(default_factory=list)
    depleted_layers: List[str] = Field(default_factory=list)
    gleyed_layers: List[str] = Field(default_factory=list)
    remarks: List[str] = Field(default_factory=list)


class HydrologyObservation(BaseModel):
    """Observation of a primary or secondary hydrology indicator."""

    code: str = Field(..., description="USACE indicator code (e.g., A1, B6, B9, D2, D5).")
    present: bool = Field(True, description="Observation status.")
    remarks: Optional[str] = Field(None, description="Field notes or supporting details.")


class FACNeutralResult(BaseModel):
    """Detailed calculation of the FAC-Neutral test (Indicator D5)."""

    n_wet: int = Field(..., description="Count of dominant taxa that are OBL or FACW.")
    n_dry: int = Field(..., description="Count of dominant taxa that are FACU, UPL, or NL.")
    n_fac: int = Field(..., description="Count of dominant taxa that are FAC (excluded).")
    passed: bool = Field(..., description="True if N_wet > N_dry.")
    indicator_d5_positive: bool = Field(..., description="True if qualifies as secondary indicator D5.")


class HydrologyDetermination(BaseModel):
    """Summary of wetland hydrology parameter."""

    region: RegionEnum = Field(..., description="Regulatory region (EMP or AGCP).")
    primary_indicators: List[str] = Field(default_factory=list, description="List of confirmed primary indicator codes.")
    secondary_indicators: List[str] = Field(default_factory=list, description="List of confirmed secondary indicator codes.")
    fac_neutral: Optional[FACNeutralResult] = Field(None, description="Automated FAC-neutral test result.")
    wetland_hydrology_present: bool = Field(..., description="True if >= 1 primary OR >= 2 secondary indicators.")
    remarks: List[str] = Field(default_factory=list)


class WetlandDeterminationResult(BaseModel):
    """Comprehensive Three-Parameter Jurisdictional Wetland Determination."""

    plot_id: str = Field(..., description="Sample plot identifier.")
    region: RegionEnum = Field(..., description="Regulatory region (EMP or AGCP).")
    hydrophytic_vegetation: VegetationDetermination
    hydric_soils: SoilDetermination
    wetland_hydrology: HydrologyDetermination
    is_jurisdictional_wetland: bool = Field(..., description="True iff all three mandatory parameters are present.")
    summary: str = Field(..., description="Executive determination statement.")
