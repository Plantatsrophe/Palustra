"""Realistic sample plot fixtures and three-parameter jurisdictional determination tests."""

import pytest
from app.wetland.models import RegionEnum, SoilHorizon, SpeciesCover
from app.wetland.synthesis import perform_jurisdictional_wetland_determination


class TestWetlandDeterminationSynthesis:
    """End-to-end evaluation using realistic field plot fixtures."""

    def test_piedmont_bottomland_hardwood_wetland(self):
        """Realistic EMP bottomland hardwood swamp plot (Jurisdictional Wetland)."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=45.0, indicator_status="FACW"),
                SpeciesCover(taxon="Liquidambar styraciflua", percent_cover=35.0, indicator_status="FAC"),
                SpeciesCover(taxon="Acer negundo", percent_cover=20.0, indicator_status="FAC"),
            ],
            "Herb": [
                SpeciesCover(taxon="Carex lurida", percent_cover=60.0, indicator_status="OBL"),
                SpeciesCover(taxon="Saururus cernuus", percent_cover=30.0, indicator_status="OBL"),
                SpeciesCover(taxon="Boehmeria cylindrica", percent_cover=10.0, indicator_status="FACW"),
            ],
        }

        # Soil Profile: NRCS A11 & F3 confirmed
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=12.0,
                matrix_hue="10YR",
                matrix_value=2.5,
                matrix_chroma=1.0,
                texture="silt loam",
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=12.0,
                bottom_depth_cm=35.0,  # Depleted layer 23 cm thick starting at 12 cm
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="silty clay loam",
                redox_percent=5.0,
                redox_distinctness="distinct",
            ),
        ]

        # Hydrology: Primary indicator A2 (High Water Table)
        hydrology = ["A2"]

        result = perform_jurisdictional_wetland_determination(
            plot_id="PLOT-EMP-01",
            region=RegionEnum.EMP,
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )

        assert result.is_jurisdictional_wetland is True
        assert result.hydrophytic_vegetation.hydrophytic_vegetation_present is True
        assert result.hydric_soils.hydric_soil_present is True
        assert "A11" in result.hydric_soils.confirmed_indicators
        assert "F3" in result.hydric_soils.confirmed_indicators
        assert result.wetland_hydrology.wetland_hydrology_present is True
        assert "JURISDICTIONAL WETLAND CRITERIA SATISFIED" in result.summary

    def test_coastal_pine_flatwood_wetland(self):
        """Realistic AGCP sandy pine flatwood depression plot (Jurisdictional Wetland)."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Pinus serotina", percent_cover=70.0, indicator_status="FACW"),
                SpeciesCover(taxon="Pinus taeda", percent_cover=20.0, indicator_status="FAC"),
            ],
            "Sapling/Shrub": [
                SpeciesCover(taxon="Ilex glabra", percent_cover=55.0, indicator_status="FACW"),
                SpeciesCover(taxon="Lyonia lucida", percent_cover=35.0, indicator_status="FACW"),
            ],
            "Herb": [
                SpeciesCover(taxon="Woodwardia virginica", percent_cover=60.0, indicator_status="OBL"),
                SpeciesCover(taxon="Rhynchospora chalarocephala", percent_cover=30.0, indicator_status="OBL"),
            ],
        }

        # Sandy Soil Profile: NRCS S5 confirmed
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=6.0,
                matrix_hue="10YR",
                matrix_value=2.0,
                matrix_chroma=1.0,
                texture="sand",
            ),
            SoilHorizon(
                name="Cg",
                top_depth_cm=6.0,
                bottom_depth_cm=26.0,
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=2.0,
                texture="sand",
                redox_percent=8.0,
                redox_distinctness="prominent",
            ),
        ]

        # Hydrology in AGCP: B6 is a PRIMARY indicator!
        hydrology = ["B6"]

        result = perform_jurisdictional_wetland_determination(
            plot_id="PLOT-AGCP-02",
            region=RegionEnum.AGCP,
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )

        assert result.is_jurisdictional_wetland is True
        assert "S5" in result.hydric_soils.confirmed_indicators
        assert "B6" in result.wetland_hydrology.primary_indicators

    def test_upland_oak_hickory_forest_non_wetland(self):
        """Realistic upland forest plot failing all three parameters (Non-Wetland)."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Quercus alba", percent_cover=55.0, indicator_status="FACU"),
                SpeciesCover(taxon="Carya tomentosa", percent_cover=30.0, indicator_status="UPL"),
                SpeciesCover(taxon="Liriodendron tulipifera", percent_cover=15.0, indicator_status="FACU"),
            ],
            "Herb": [
                SpeciesCover(taxon="Polystichum acrostichoides", percent_cover=40.0, indicator_status="FACU"),
                SpeciesCover(taxon="Chimaphila maculata", percent_cover=20.0, indicator_status="UPL"),
            ],
        }

        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=8.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=3.0,
                texture="sandy loam",
            ),
            SoilHorizon(
                name="Bt",
                top_depth_cm=8.0,
                bottom_depth_cm=45.0,
                matrix_hue="7.5YR",
                matrix_value=5.0,
                matrix_chroma=6.0,
                texture="clay loam",
            ),
        ]

        hydrology = []

        result = perform_jurisdictional_wetland_determination(
            plot_id="PLOT-UPLAND-03",
            region=RegionEnum.EMP,
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )

        assert result.is_jurisdictional_wetland is False
        assert result.hydrophytic_vegetation.hydrophytic_vegetation_present is False
        assert result.hydric_soils.hydric_soil_present is False
        assert result.wetland_hydrology.wetland_hydrology_present is False
        assert "NON-WETLAND / UPLAND DETERMINATION" in result.summary

    def test_prevalence_index_rescue_in_problematic_community(self):
        """Community failing Dominance Test but passing via Prevalence Index (PI <= 3.00)."""
        # Dominants: 1 OBL (35%), 1 UPL (35%) -> Total Dominants = 2, A = 1 (50.0% FAILS dominance test).
        # Subdominant cover: 15% OBL, 15% FACW (both < 20% threshold, so not dominants).
        # Prevalence Index:
        # OBL: 35 + 15 = 50 (50*1 = 50)
        # FACW: 15 (15*2 = 30)
        # UPL: 35 (35*5 = 175)
        # Sum = 255 / 100 = 2.55 <= 3.00 (PASSES).
        strata = {
            "Herb": [
                SpeciesCover(taxon="Taxon OBL Dominant", percent_cover=35.0, indicator_status="OBL"),
                SpeciesCover(taxon="Taxon UPL Dominant", percent_cover=35.0, indicator_status="UPL"),
                SpeciesCover(taxon="Taxon OBL Subdominant", percent_cover=15.0, indicator_status="OBL"),
                SpeciesCover(taxon="Taxon FACW Minor", percent_cover=15.0, indicator_status="FACW"),
            ]
        }

        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=8.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="loam",
            ),
            SoilHorizon(
                name="Bg",
                top_depth_cm=8.0,
                bottom_depth_cm=28.0,
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="clay loam",
            ),
        ]

        # Hydrology: 2 secondary indicators (B10, D2)
        hydrology = ["B10", "D2"]

        result = perform_jurisdictional_wetland_determination(
            plot_id="PLOT-PI-RESCUE-04",
            region=RegionEnum.EMP,
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )

        assert result.hydrophytic_vegetation.dominance_test_passed is False
        assert result.hydrophytic_vegetation.prevalence_index_passed is True
        assert result.hydrophytic_vegetation.prevalence_index == 2.55
        assert result.hydrophytic_vegetation.hydrophytic_vegetation_present is True
        assert result.is_jurisdictional_wetland is True
