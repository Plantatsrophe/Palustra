"""Pydantic v2 schemas and models for USACE Wetland Determination export and GIS boundary mapping."""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.wetland.models import (
    HydrologyDetermination,
    RegionEnum,
    SoilDetermination,
    SoilHorizon,
    SpeciesCover,
    VegetationDetermination,
    WetlandDeterminationResult,
)


class BoundaryRoleEnum(str, Enum):
    WETLAND_BOUNDARY = "wetland_boundary"
    PAIRED_UPLAND = "paired_upland"
    INTERIOR_WETLAND = "interior_wetland"
    INTERIOR_UPLAND = "interior_upland"
    TRANSECT_POINT = "transect_point"


class USACEPlotExportData(BaseModel):
    """Unified payload representing a complete USACE sampling plot for PDF & GIS export."""

    model_config = ConfigDict(extra="ignore")

    # Administrative & Location Details (Page 1 Header)
    sampling_point: str = Field("DP-01", description="Plot identifier / sampling point ID.")
    project_name: str = Field("Palustra Wetland Survey", description="Project or site name.")
    project_code: Optional[str] = Field(None, description="Client or internal project code.")
    applicant_owner: Optional[str] = Field(None, description="Applicant or property owner.")
    investigator: Optional[str] = Field(None, description="Investigator(s) name and credentials.")
    city_county: Optional[str] = Field(None, description="City or County.")
    state: Optional[str] = Field(None, description="State (e.g., 'NC', 'VA').")
    section_township_range: Optional[str] = Field(None, description="PLSS Section, Township, Range.")
    local_relief: Optional[str] = Field(None, description="Local relief (e.g. Concave, Convex, None, Depression).")
    slope_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Slope gradient in percent.")
    subregion: Optional[str] = Field(None, description="Subregion (LRR or MLRA, e.g. 'LRR P, MLRA 136').")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees.")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees.")
    datum: str = Field("WGS84", description="Geodetic datum (WGS84 or NAD83).")
    nwi_classification: Optional[str] = Field(None, description="NWI wetland classification code.")
    soil_map_unit_name: Optional[str] = Field(None, description="Soil Survey map unit name.")
    sampling_date: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Date of field sampling (YYYY-MM-DD).",
    )
    region: RegionEnum = Field(RegionEnum.EMP, description="USACE Region: EMP or AGCP.")

    # Environmental Condition Flags
    climatic_conditions_typical: bool = Field(True, description="Typical climatic/hydrologic conditions for season.")
    vegetation_disturbed: bool = Field(False, description="Significantly disturbed vegetation.")
    soil_disturbed: bool = Field(False, description="Significantly disturbed soils.")
    hydrology_disturbed: bool = Field(False, description="Significantly disturbed hydrology.")
    vegetation_problematic: bool = Field(False, description="Naturally problematic vegetation.")
    soil_problematic: bool = Field(False, description="Naturally problematic soils.")
    hydrology_problematic: bool = Field(False, description="Naturally problematic hydrology.")

    # Summary of Findings
    summary_remarks: Optional[str] = Field(None, description="Remarks for Summary of Findings.")

    # Hydrology Observations & Indicators (Page 1)
    hydrology_indicators: List[str] = Field(
        default_factory=list,
        description="USACE hydrology indicator codes observed (e.g. ['A1', 'A2', 'B6', 'D2']).",
    )
    surface_water_present: bool = Field(False, description="Surface water present at plot.")
    surface_water_depth_in: Optional[float] = Field(None, ge=0.0, description="Surface water depth in inches.")
    water_table_present: bool = Field(False, description="Free water table present in pit.")
    water_table_depth_in: Optional[float] = Field(None, ge=0.0, description="Water table depth in inches.")
    saturation_present: bool = Field(False, description="Soil saturation present.")
    saturation_depth_in: Optional[float] = Field(None, ge=0.0, description="Soil saturation depth in inches.")
    recorded_data_description: Optional[str] = Field(
        None, description="Recorded data (monitoring wells, stream gauges, aerial photos)."
    )
    hydrology_remarks: Optional[str] = Field(None, description="Hydrology remarks.")

    # Vegetation Plot Data (Page 2)
    strata_vegetation: Dict[str, List[SpeciesCover]] = Field(
        default_factory=lambda: {"Tree": [], "Sapling/Shrub": [], "Herb": [], "Woody Vine": []},
        description="Vegetation occurrences grouped by stratum.",
    )
    tree_plot_size: Optional[str] = Field("30 ft radius", description="Tree stratum plot size.")
    sapling_shrub_plot_size: Optional[str] = Field("15 ft radius", description="Sapling/Shrub stratum plot size.")
    herb_plot_size: Optional[str] = Field("5 ft radius", description="Herb stratum plot size.")
    woody_vine_plot_size: Optional[str] = Field("30 ft radius", description="Woody Vine stratum plot size.")
    vegetation_remarks: Optional[str] = Field(None, description="Vegetation section remarks.")

    # Soil Profile & Indicators (Page 2)
    soil_horizons: List[SoilHorizon] = Field(
        default_factory=list,
        description="Soil horizons evaluated in profile pit.",
    )
    restrictive_layer_type: Optional[str] = Field(None, description="Type of restrictive layer if present.")
    restrictive_layer_depth_in: Optional[float] = Field(None, description="Depth to restrictive layer in inches.")
    soil_remarks: Optional[str] = Field(None, description="Soil section remarks.")

    # Precomputed Determinations (Optional: auto-computed if omitted)
    determination: Optional[WetlandDeterminationResult] = Field(
        None, description="Precomputed three-parameter determination result."
    )

    # GIS Boundary Mapping Attributes
    boundary_role: Optional[BoundaryRoleEnum] = Field(
        None, description="GIS boundary role (e.g. wetland_boundary, paired_upland)."
    )
    flag_id: Optional[str] = Field(None, description="Survey ribbon/flag identifier (e.g. 'WL-A-01').")
    transect_id: Optional[str] = Field(None, description="Transect identifier (e.g. 'T-01').")
    paired_plot_id: Optional[str] = Field(None, description="Paired wetland/upland sampling point ID.")


class PlotDeterminationInput(USACEPlotExportData):
    """Input payload for automated three-parameter wetland determination evaluation."""

    pass


class GeoJSONExportRequest(BaseModel):
    """Request payload for exporting one or more plots to GeoJSON."""

    plots: List[USACEPlotExportData]
    include_transect_lines: bool = Field(
        True, description="Generate LineString features connecting paired transect points."
    )


class PDFExportRequest(BaseModel):
    """Request payload for exporting a plot to USACE PDF."""

    plot: USACEPlotExportData
    watermark: Optional[str] = Field(None, description="Optional draft/sample watermark text.")
