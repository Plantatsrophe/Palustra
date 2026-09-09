"""GIS RFC 7946 GeoJSON exporter for USACE wetland determination boundary mapping.

Generates standard GeoJSON FeatureCollections containing:
- Point features for sampling plots (wetland and paired upland determinations).
- Optional LineString features connecting paired transect points across the wetland boundary.
Ensures full compatibility with ESRI ArcGIS Pro, QGIS, Leaflet, and Mapbox.
"""

from typing import Any, Dict, List, Optional, Sequence

from app.export.models import BoundaryRoleEnum, USACEPlotExportData
from app.wetland.models import WetlandDeterminationResult
from app.wetland.synthesis import perform_jurisdictional_wetland_determination


def plot_to_geojson_feature(
    plot: USACEPlotExportData,
    determination: Optional[WetlandDeterminationResult] = None,
) -> Dict[str, Any]:
    """Convert a single USACE plot into an RFC 7946 GeoJSON Point feature."""
    if determination is None:
        if plot.determination is not None:
            determination = plot.determination
        else:
            determination = perform_jurisdictional_wetland_determination(
                plot_id=plot.sampling_point,
                region=plot.region,
                strata_vegetation=plot.strata_vegetation,
                soil_horizons=plot.soil_horizons,
                hydrology_indicators=plot.hydrology_indicators,
                enable_morphological_adaptations=True,
            )

    # Geometry: Point [longitude, latitude] or null if unlocated
    geometry: Optional[Dict[str, Any]] = None
    if plot.longitude is not None and plot.latitude is not None:
        geometry = {
            "type": "Point",
            "coordinates": [round(plot.longitude, 7), round(plot.latitude, 7)],
        }

    # Determine boundary role if not set
    role = plot.boundary_role
    if role is None:
        if determination.is_jurisdictional_wetland:
            role = BoundaryRoleEnum.WETLAND_BOUNDARY
        else:
            role = BoundaryRoleEnum.PAIRED_UPLAND

    veg = determination.hydrophytic_vegetation
    soils = determination.hydric_soils
    hydro = determination.wetland_hydrology

    properties = {
        "plot_id": plot.sampling_point,
        "project_name": plot.project_name,
        "project_code": plot.project_code,
        "sampling_date": plot.sampling_date,
        "investigator": plot.investigator,
        "region": plot.region.value,
        "datum": plot.datum,
        # Determination Results
        "is_jurisdictional_wetland": determination.is_jurisdictional_wetland,
        "determination_result": "WETLAND" if determination.is_jurisdictional_wetland else "UPLAND",
        "boundary_role": role.value if hasattr(role, "value") else str(role),
        "flag_id": plot.flag_id,
        "transect_id": plot.transect_id,
        "paired_plot_id": plot.paired_plot_id,
        # Three Mandatory Parameters
        "hydrophytic_vegetation": veg.hydrophytic_vegetation_present,
        "dominance_percent": round(veg.dominance_test_percent, 2),
        "prevalence_index": round(veg.prevalence_index, 2) if veg.prevalence_index is not None else None,
        "rapid_test_passed": veg.rapid_test_passed,
        "hydric_soils": soils.hydric_soil_present,
        "confirmed_soil_indicators": soils.confirmed_indicators,
        "wetland_hydrology": hydro.wetland_hydrology_present,
        "confirmed_hydrology_indicators": hydro.primary_indicators + hydro.secondary_indicators,
        # Field Observations
        "water_table_depth_in": plot.water_table_depth_in,
        "saturation_depth_in": plot.saturation_depth_in,
        "surface_water_depth_in": plot.surface_water_depth_in,
        # Site Metadata
        "soil_map_unit": plot.soil_map_unit_name,
        "nwi_classification": plot.nwi_classification,
        "local_relief": plot.local_relief,
        "slope_percent": plot.slope_percent,
        "summary": determination.summary,
    }

    return {
        "type": "Feature",
        "id": plot.sampling_point,
        "geometry": geometry,
        "properties": properties,
    }


def plots_to_geojson_collection(
    plots: Sequence[USACEPlotExportData],
    include_transect_lines: bool = True,
    skip_unlocated: bool = False,
) -> Dict[str, Any]:
    """Convert a sequence of USACE plots into an RFC 7946 GeoJSON FeatureCollection."""
    features: List[Dict[str, Any]] = []
    transect_groups: Dict[str, List[USACEPlotExportData]] = {}

    for plot in plots:
        feature = plot_to_geojson_feature(plot)
        if skip_unlocated and feature["geometry"] is None:
            continue
        features.append(feature)

        # Track for transect connection lines
        if include_transect_lines and plot.transect_id and plot.longitude is not None and plot.latitude is not None:
            transect_groups.setdefault(plot.transect_id, []).append(plot)

    # Generate transect LineString features connecting paired boundary plots
    if include_transect_lines:
        for t_id, t_plots in transect_groups.items():
            if len(t_plots) >= 2:
                # Sort: wetland first then upland, or by sampling point name
                sorted_pts = sorted(
                    t_plots,
                    key=lambda p: (
                        0 if p.determination and p.determination.is_jurisdictional_wetland else 1,
                        p.sampling_point,
                    ),
                )
                line_coords = [[p.longitude, p.latitude] for p in sorted_pts if p.longitude and p.latitude]
                if len(line_coords) >= 2:
                    features.append({
                        "type": "Feature",
                        "id": f"transect-{t_id}",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": line_coords,
                        },
                        "properties": {
                            "feature_type": "transect_boundary_line",
                            "transect_id": t_id,
                            "points": [p.sampling_point for p in sorted_pts],
                            "project_name": sorted_pts[0].project_name,
                            "summary": f"Boundary transect {t_id} connecting {len(sorted_pts)} determination plots.",
                        },
                    })

    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
    }
