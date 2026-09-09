"""Unit tests for wetland hydrology decision logic and automated FAC-Neutral test."""

import pytest
from app.wetland.hydrology import (
    compute_fac_neutral_test,
    evaluate_wetland_hydrology,
    get_indicator_tier,
)
from app.wetland.models import RegionEnum, SpeciesCover


class TestRegionalHydrologyTiers:
    """Tests for indicator tier differences between EMP and AGCP regional supplements."""

    def test_b6_surface_soil_cracks_tier_difference(self):
        """B6 is Primary in AGCP but Secondary in EMP."""
        assert get_indicator_tier("B6", RegionEnum.AGCP) == "Primary"
        assert get_indicator_tier("B6", RegionEnum.EMP) == "Secondary"

        # In AGCP, B6 alone satisfies the hydrology criterion
        agcp_det = evaluate_wetland_hydrology(RegionEnum.AGCP, observed_indicators=["B6"])
        assert agcp_det.wetland_hydrology_present is True
        assert "B6" in agcp_det.primary_indicators

        # In EMP, B6 alone is insufficient
        emp_det = evaluate_wetland_hydrology(RegionEnum.EMP, observed_indicators=["B6"])
        assert emp_det.wetland_hydrology_present is False
        assert "B6" in emp_det.secondary_indicators

    def test_b9_water_stained_leaves_tier_difference(self):
        """B9 is Primary in AGCP but Secondary in EMP."""
        assert get_indicator_tier("B9", RegionEnum.AGCP) == "Primary"
        assert get_indicator_tier("B9", RegionEnum.EMP) == "Secondary"

        # In AGCP, B9 alone satisfies
        agcp_det = evaluate_wetland_hydrology(RegionEnum.AGCP, observed_indicators=["B9"])
        assert agcp_det.wetland_hydrology_present is True
        assert "B9" in agcp_det.primary_indicators

        # In EMP, B9 alone is insufficient
        emp_det = evaluate_wetland_hydrology(RegionEnum.EMP, observed_indicators=["B9"])
        assert emp_det.wetland_hydrology_present is False
        assert "B9" in emp_det.secondary_indicators

    def test_d6_sphagnum_moss_regional_recognition(self):
        """D6 is recognized as Secondary in EMP, but Not Recognized in AGCP."""
        assert get_indicator_tier("D6", RegionEnum.EMP) == "Secondary"
        assert get_indicator_tier("D6", RegionEnum.AGCP) == "Not Recognized"

        emp_det = evaluate_wetland_hydrology(RegionEnum.EMP, observed_indicators=["D6", "D2"])
        assert emp_det.wetland_hydrology_present is True
        assert "D6" in emp_det.secondary_indicators

        agcp_det = evaluate_wetland_hydrology(RegionEnum.AGCP, observed_indicators=["D6", "D2"])
        # In AGCP, D6 is ignored; only D2 remains (1 secondary is not enough)
        assert agcp_det.wetland_hydrology_present is False
        assert "D6" not in agcp_det.secondary_indicators


class TestFACNeutralTest:
    """Tests for automated FAC-Neutral calculation (Indicator D5)."""

    def test_fac_neutral_positive(self):
        """N_wet > N_dry results in positive D5 indicator."""
        dominants = [
            SpeciesCover(taxon="Taxodium distichum", percent_cover=50.0, indicator_status="OBL"),
            SpeciesCover(taxon="Nyssa biflora", percent_cover=30.0, indicator_status="FACW"),
            SpeciesCover(taxon="Acer rubrum", percent_cover=20.0, indicator_status="FAC"),  # Excluded
            SpeciesCover(taxon="Ilex opaca", percent_cover=15.0, indicator_status="FACU"),
        ]
        # Wet (OBL + FACW) = 2. Dry (FACU) = 1. FAC = 1 (excluded).
        # 2 > 1 -> Positive!
        res = compute_fac_neutral_test(dominants)
        assert res.n_wet == 2
        assert res.n_dry == 1
        assert res.n_fac == 1
        assert res.passed is True
        assert res.indicator_d5_positive is True

    def test_fac_neutral_negative_or_tie(self):
        """N_wet <= N_dry results in negative D5 indicator."""
        dominants = [
            SpeciesCover(taxon="Species 1", percent_cover=40.0, indicator_status="FACW"),
            SpeciesCover(taxon="Species 2", percent_cover=30.0, indicator_status="FAC"),
            SpeciesCover(taxon="Species 3", percent_cover=20.0, indicator_status="FACU"),
        ]
        # Wet = 1, Dry = 1 -> 1 is not > 1 -> Fails!
        res = compute_fac_neutral_test(dominants)
        assert res.n_wet == 1
        assert res.n_dry == 1
        assert res.passed is False

    def test_automated_d5_integration_in_hydrology_evaluation(self):
        """Automated D5 satisfies the 2-secondary indicator requirement when combined with D2."""
        dominants = [
            SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=60.0, indicator_status="FACW"),
            SpeciesCover(taxon="Liquidambar styraciflua", percent_cover=40.0, indicator_status="FAC"),
        ]
        # Dominants: 1 FACW (wet), 1 FAC (excluded) -> N_wet=1 > N_dry=0 -> D5 is Positive!
        # Field observer only noted D2 (Geomorphic Position).
        det = evaluate_wetland_hydrology(
            region=RegionEnum.EMP,
            observed_indicators=["D2"],
            dominants=dominants,
        )
        assert det.fac_neutral is not None
        assert det.fac_neutral.passed is True
        assert "D5" in det.secondary_indicators
        assert "D2" in det.secondary_indicators
        assert det.wetland_hydrology_present is True
