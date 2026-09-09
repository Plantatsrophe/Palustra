"""Tests for official USACE Regional Supplement 2-Page Data Form PDF generation."""

import io
import pytest
from pypdf import PdfReader

from palustra.export.models import BoundaryRoleEnum, USACEPlotExportData
from palustra.export.pdf_form import render_usace_pdf, render_usace_project_pdf
from palustra.wetland.models import RegionEnum, SoilHorizon, SpeciesCover


@pytest.fixture
def sample_emp_wetland_plot():
    """Create a realistic wetland plot in Eastern Mountains and Piedmont (EMP) region."""
    return USACEPlotExportData(
        sampling_point="DP-01W",
        project_name="Eno River Wetland Delineation",
        project_code="ENO-2026-01",
        applicant_owner="North Carolina Land Trust",
        investigator="B. Smith, PWS",
        city_county="Orange County",
        state="NC",
        section_township_range="Sec 14, T2N, R3E",
        local_relief="Depression",
        slope_percent=1.0,
        subregion="LRR P, MLRA 136",
        latitude=35.913200,
        longitude=-79.055800,
        datum="WGS84",
        nwi_classification="PFO1A",
        soil_map_unit_name="Wehadkee silt loam, 0 to 2 percent slopes, frequently flooded",
        sampling_date="2026-09-09",
        region=RegionEnum.EMP,
        climatic_conditions_typical=True,
        summary_remarks="All three parameters clearly satisfied in active floodplain depression.",
        hydrology_indicators=["A1", "A2", "A3", "B1", "B10"],
        surface_water_present=True,
        surface_water_depth_in=2.0,
        water_table_present=True,
        water_table_depth_in=4.0,
        saturation_present=True,
        saturation_depth_in=0.0,
        recorded_data_description="USGS Gauge 02085070 Eno River at Hillsborough",
        hydrology_remarks="Water marks visible on tree trunks up to 18 inches above ground surface.",
        strata_vegetation={
            "Tree": [
                SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=35.0, indicator_status="FACW"),
                SpeciesCover(taxon="Acer rubrum", percent_cover=25.0, indicator_status="FAC"),
                SpeciesCover(taxon="Liquidambar styraciflua", percent_cover=15.0, indicator_status="FAC"),
            ],
            "Sapling/Shrub": [
                SpeciesCover(taxon="Alnus serrulata", percent_cover=30.0, indicator_status="OBL"),
                SpeciesCover(taxon="Cephalanthus occidentalis", percent_cover=15.0, indicator_status="OBL"),
            ],
            "Herb": [
                SpeciesCover(taxon="Carex lurida", percent_cover=40.0, indicator_status="OBL"),
                SpeciesCover(taxon="Boehmeria cylindrica", percent_cover=20.0, indicator_status="OBL"),
                SpeciesCover(taxon="Microstegium vimineum", percent_cover=10.0, indicator_status="FAC"),
            ],
            "Woody Vine": [
                SpeciesCover(taxon="Toxicodendron radicans", percent_cover=15.0, indicator_status="FAC"),
            ],
        },
        tree_plot_size="30 ft radius",
        sapling_shrub_plot_size="15 ft radius",
        herb_plot_size="5 ft radius",
        woody_vine_plot_size="30 ft radius",
        vegetation_remarks="Dense hydrophytic canopy and herbaceous stratum with 100% dominance test.",
        soil_horizons=[
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=10.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="silt loam",
                redox_percent=0.0,
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=10.0,
                bottom_depth_cm=45.0,
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="silty clay loam",
                redox_percent=12.0,
                redox_distinctness="prominent",
                redox_hue="7.5YR",
                redox_value=5.0,
                redox_chroma=6.0,
            ),
        ],
        soil_remarks="Depleted matrix below dark surface confirming NRCS indicator F3 and A11.",
        boundary_role=BoundaryRoleEnum.WETLAND_BOUNDARY,
        flag_id="WL-A-01",
        transect_id="T-01",
        paired_plot_id="DP-01U",
    )


@pytest.fixture
def sample_agcp_upland_plot():
    """Create a paired upland plot in Atlantic and Gulf Coastal Plain (AGCP) region."""
    return USACEPlotExportData(
        sampling_point="DP-01U",
        project_name="Eno River Wetland Delineation",
        project_code="ENO-2026-01",
        applicant_owner="North Carolina Land Trust",
        investigator="B. Smith, PWS",
        city_county="Orange County",
        state="NC",
        local_relief="Convex shoulder",
        slope_percent=6.5,
        subregion="LRR T, MLRA 133A",
        latitude=35.913350,
        longitude=-79.055620,
        datum="WGS84",
        sampling_date="2026-09-09",
        region=RegionEnum.AGCP,
        climatic_conditions_typical=True,
        summary_remarks="Upland point; lacks hydrophytic vegetation, hydric soils, and hydrology.",
        hydrology_indicators=[],
        surface_water_present=False,
        water_table_present=False,
        saturation_present=False,
        strata_vegetation={
            "Tree": [
                SpeciesCover(taxon="Quercus alba", percent_cover=45.0, indicator_status="FACU"),
                SpeciesCover(taxon="Pinus taeda", percent_cover=30.0, indicator_status="FAC"),
            ],
            "Sapling/Shrub": [
                SpeciesCover(taxon="Cornus florida", percent_cover=20.0, indicator_status="FACU"),
            ],
            "Herb": [
                SpeciesCover(taxon="Dichanthelium clandestinum", percent_cover=25.0, indicator_status="FACW"),
                SpeciesCover(taxon="Solidago rugosa", percent_cover=15.0, indicator_status="FAC"),
            ],
            "Woody Vine": [],
        },
        soil_horizons=[
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=15.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=4.0,
                texture="sandy loam",
                redox_percent=0.0,
            ),
            SoilHorizon(
                name="Bt",
                top_depth_cm=15.0,
                bottom_depth_cm=50.0,
                matrix_hue="7.5YR",
                matrix_value=5.0,
                matrix_chroma=6.0,
                texture="sandy clay loam",
                redox_percent=0.0,
            ),
        ],
        soil_remarks="Bright upland matrix (Chroma 6); no hydric indicators.",
        boundary_role=BoundaryRoleEnum.PAIRED_UPLAND,
        flag_id="UP-A-01",
        transect_id="T-01",
        paired_plot_id="DP-01W",
    )


def test_render_emp_wetland_pdf(sample_emp_wetland_plot):
    """Verify official EMP wetland determination PDF renders strictly 2 pages with all sections."""
    pdf_bytes = render_usace_pdf(sample_emp_wetland_plot)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    # Must strictly contain exactly 2 pages
    assert len(reader.pages) == 2

    # Check document metadata
    meta = reader.metadata
    assert "USACE" in meta["/Title"]
    assert "DP-01W" in meta["/Title"]
    assert meta["/Author"] == "B. Smith, PWS"
    assert "Palustra" in meta["/Producer"]

    # Verify text on Page 1
    page1_text = reader.pages[0].extract_text()
    assert "WETLAND DETERMINATION DATA FORM" in page1_text
    assert "Eastern Mountains and Piedmont" in page1_text
    assert "DP-01W" in page1_text
    assert "Eno River Wetland Delineation" in page1_text
    assert "SUMMARY OF FINDINGS" in page1_text
    assert "HYDROLOGY" in page1_text
    assert "YES (WETLAND)" in page1_text

    # Verify text on Page 2
    page2_text = reader.pages[1].extract_text()
    assert "SAMPLING POINT: DP-01W" in page2_text
    assert "VEGETATION" in page2_text
    assert "Fraxinus pennsylvanica" in page2_text
    assert "Dominance Test Worksheet" in page2_text
    assert "Prevalence Index Worksheet" in page2_text
    assert "SOIL" in page2_text
    assert "Hydric Soil Indicators" in page2_text
    assert "HYDRIC SOIL: YES" in page2_text


def test_render_agcp_upland_pdf(sample_agcp_upland_plot):
    """Verify official AGCP upland determination PDF renders properly with negative determination."""
    pdf_bytes = render_usace_pdf(sample_agcp_upland_plot, watermark="DRAFT")
    assert len(pdf_bytes) > 2000

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2

    page1_text = reader.pages[0].extract_text()
    assert "Atlantic and Gulf Coastal Plain" in page1_text
    assert "DP-01U" in page1_text
    assert "NO (UPLAND)" in page1_text

    page2_text = reader.pages[1].extract_text()
    assert "Quercus alba" in page2_text
    assert "HYDRIC SOIL: NO" in page2_text


def test_multi_plot_project_pdf(sample_emp_wetland_plot, sample_agcp_upland_plot):
    """Verify multi-plot project PDF concatenates 2 plots into exactly 4 pages."""
    plots = [sample_emp_wetland_plot, sample_agcp_upland_plot]
    project_pdf = render_usace_project_pdf(plots, watermark="PRELIMINARY")
    assert len(project_pdf) > 4000

    reader = PdfReader(io.BytesIO(project_pdf))
    assert len(reader.pages) == 4

    # Pages 1-2 belong to DP-01W
    p1_text = reader.pages[0].extract_text()
    assert "DP-01W" in p1_text

    # Pages 3-4 belong to DP-01U
    p3_text = reader.pages[2].extract_text()
    assert "DP-01U" in p3_text


def test_empty_strata_handling():
    """Verify that plots with empty vegetation strata render without exceptions."""
    minimal_plot = USACEPlotExportData(
        sampling_point="DP-MIN",
        project_name="Minimal Test",
        region=RegionEnum.EMP,
        strata_vegetation={},
        soil_horizons=[],
        hydrology_indicators=[],
    )
    pdf_bytes = render_usace_pdf(minimal_plot)
    assert len(pdf_bytes) > 1000
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2
