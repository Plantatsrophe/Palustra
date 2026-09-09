"""Tests for GIS RFC 7946 GeoJSON boundary mapping export."""

import pytest

from app.export.geojson import plot_to_geojson_feature, plots_to_geojson_collection
from app.export.models import BoundaryRoleEnum, USACEPlotExportData
from app.wetland.models import RegionEnum, SoilHorizon, SpeciesCover


@pytest.fixture
def boundary_pair():
    """Create a paired wetland and upland plot representing a delineated boundary segment."""
    wetland = USACEPlotExportData(
        sampling_point="DP-01W",
        project_name="Solar Site Boundary",
        project_code="SOL-2026",
        investigator="J. Doe, PWS",
        region=RegionEnum.EMP,
        latitude=36.123456,
        longitude=-78.987654,
        boundary_role=BoundaryRoleEnum.WETLAND_BOUNDARY,
        flag_id="WL-01",
        transect_id="T-01",
        paired_plot_id="DP-01U",
        hydrology_indicators=["A1", "B1"],
        strata_vegetation={
            "Herb": [SpeciesCover(taxon="Typha latifolia", percent_cover=80.0, indicator_status="OBL")]
        },
        soil_horizons=[
            SoilHorizon(
                top_depth_cm=0,
                bottom_depth_cm=30,
                matrix_hue="10YR",
                matrix_value=4,
                matrix_chroma=1,
                redox_percent=10,
            )
        ],
    )

    upland = USACEPlotExportData(
        sampling_point="DP-01U",
        project_name="Solar Site Boundary",
        project_code="SOL-2026",
        investigator="J. Doe, PWS",
        region=RegionEnum.EMP,
        latitude=36.123510,
        longitude=-78.987590,
        boundary_role=BoundaryRoleEnum.PAIRED_UPLAND,
        flag_id="UP-01",
        transect_id="T-01",
        paired_plot_id="DP-01W",
        hydrology_indicators=[],
        strata_vegetation={
            "Herb": [SpeciesCover(taxon="Festuca arundinacea", percent_cover=90.0, indicator_status="FACU")]
        },
        soil_horizons=[
            SoilHorizon(
                top_depth_cm=0,
                bottom_depth_cm=30,
                matrix_hue="7.5YR",
                matrix_value=5,
                matrix_chroma=6,
                redox_percent=0,
            )
        ],
    )
    return wetland, upland


def test_single_plot_to_geojson_feature(boundary_pair):
    """Verify single plot converts to a valid RFC 7946 GeoJSON Point feature."""
    wetland, _ = boundary_pair
    feat = plot_to_geojson_feature(wetland)

    assert feat["type"] == "Feature"
    assert feat["id"] == "DP-01W"
    assert feat["geometry"]["type"] == "Point"
    # RFC 7946 coordinates: [lon, lat]
    assert feat["geometry"]["coordinates"] == [-78.987654, 36.123456]

    props = feat["properties"]
    assert props["plot_id"] == "DP-01W"
    assert props["is_jurisdictional_wetland"] is True
    assert props["determination_result"] == "WETLAND"
    assert props["boundary_role"] == "wetland_boundary"
    assert props["flag_id"] == "WL-01"
    assert props["transect_id"] == "T-01"
    assert props["paired_plot_id"] == "DP-01U"
    assert props["hydrophytic_vegetation"] is True
    assert props["hydric_soils"] is True
    assert props["wetland_hydrology"] is True
    assert "A1" in props["confirmed_hydrology_indicators"]


def test_plots_to_geojson_collection_with_transects(boundary_pair):
    """Verify FeatureCollection contains Point features and generated transect LineString."""
    wetland, upland = boundary_pair
    collection = plots_to_geojson_collection([wetland, upland], include_transect_lines=True)

    assert collection["type"] == "FeatureCollection"
    assert "features" in collection
    # Expect 2 points + 1 transect line = 3 features
    assert len(collection["features"]) == 3

    points = [f for f in collection["features"] if f["geometry"]["type"] == "Point"]
    lines = [f for f in collection["features"] if f["geometry"]["type"] == "LineString"]

    assert len(points) == 2
    assert len(lines) == 1

    # Check line properties
    t_line = lines[0]
    assert t_line["properties"]["feature_type"] == "transect_boundary_line"
    assert t_line["properties"]["transect_id"] == "T-01"
    assert "DP-01W" in t_line["properties"]["points"]
    assert "DP-01U" in t_line["properties"]["points"]
    assert len(t_line["geometry"]["coordinates"]) == 2


def test_unlocated_plot_handling():
    """Verify plots lacking GPS coordinates produce geometry: null or get filtered."""
    unlocated = USACEPlotExportData(
        sampling_point="DP-NOLOC",
        project_name="No GPS Test",
        region=RegionEnum.EMP,
        latitude=None,
        longitude=None,
    )
    feat = plot_to_geojson_feature(unlocated)
    assert feat["geometry"] is None

    # When skip_unlocated is True
    col = plots_to_geojson_collection([unlocated], skip_unlocated=True)
    assert len(col["features"]) == 0

    # When skip_unlocated is False (default)
    col2 = plots_to_geojson_collection([unlocated], skip_unlocated=False)
    assert len(col2["features"]) == 1
    assert col2["features"][0]["geometry"] is None
