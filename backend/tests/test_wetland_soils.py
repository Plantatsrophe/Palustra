"""Unit tests for NRCS Hydric Soil indicators (v8.2) and Munsell matrix criteria."""

import pytest
from app.wetland.models import SoilHorizon
from app.wetland.soils import (
    check_indicator_a11,
    check_indicator_a12,
    check_indicator_f3,
    check_indicator_f6,
    check_indicator_s5,
    evaluate_hydric_soils,
    is_depleted_matrix,
    is_gleyed_matrix,
)


class TestMunsellDepletedAndGleyedMatrix:
    """Tests for Munsell depleted matrix categories and gleyed charts."""

    def test_depleted_category_1(self):
        """Value >= 5, Chroma <= 1: depleted without redox."""
        h = SoilHorizon(
            name="Btg",
            top_depth_cm=10.0,
            bottom_depth_cm=30.0,
            matrix_hue="10YR",
            matrix_value=5.0,
            matrix_chroma=1.0,
            texture="silt loam",
        )
        is_dep, cat = is_depleted_matrix(h)
        assert is_dep is True
        assert "Category 1" in cat

    def test_depleted_category_2(self):
        """Value >= 6, Chroma <= 2: depleted without redox."""
        h = SoilHorizon(
            name="Btg",
            top_depth_cm=15.0,
            bottom_depth_cm=35.0,
            matrix_hue="2.5Y",
            matrix_value=6.0,
            matrix_chroma=2.0,
            texture="clay loam",
        )
        is_dep, cat = is_depleted_matrix(h)
        assert is_dep is True
        assert "Category 2" in cat

    def test_depleted_category_3(self):
        """Value 4 or 5, Chroma 2 with >= 2% distinct or prominent redox."""
        h_valid = SoilHorizon(
            name="Btg1",
            top_depth_cm=10.0,
            bottom_depth_cm=30.0,
            matrix_hue="10YR",
            matrix_value=4.0,
            matrix_chroma=2.0,
            texture="loam",
            redox_percent=3.0,
            redox_distinctness="distinct",
        )
        is_dep, cat = is_depleted_matrix(h_valid)
        assert is_dep is True
        assert "Category 3" in cat

        # Fails if redox < 2%
        h_low_redox = h_valid.model_copy()
        h_low_redox.redox_percent = 1.0
        assert is_depleted_matrix(h_low_redox)[0] is False

        # Fails if redox is faint
        h_faint = h_valid.model_copy()
        h_faint.redox_distinctness = "faint"
        assert is_depleted_matrix(h_faint)[0] is False

    def test_depleted_category_4(self):
        """Value 4, Chroma 1 with >= 2% distinct or prominent redox."""
        h_valid = SoilHorizon(
            name="Btg",
            top_depth_cm=10.0,
            bottom_depth_cm=25.0,
            matrix_hue="10YR",
            matrix_value=4.0,
            matrix_chroma=1.0,
            texture="clay",
            redox_percent=2.5,
            redox_distinctness="prominent",
        )
        is_dep, cat = is_depleted_matrix(h_valid)
        assert is_dep is True
        assert "Category 4" in cat

        # Value 4, Chroma 1 without redox is NOT depleted
        h_no_redox = h_valid.model_copy()
        h_no_redox.redox_percent = 0.0
        assert is_depleted_matrix(h_no_redox)[0] is False

    def test_non_depleted_matrix(self):
        """Matrix colors that are not depleted."""
        h1 = SoilHorizon(
            name="B",
            top_depth_cm=10.0,
            bottom_depth_cm=30.0,
            matrix_hue="10YR",
            matrix_value=4.0,
            matrix_chroma=3.0,
            texture="loam",
        )
        assert is_depleted_matrix(h1)[0] is False

        h2 = SoilHorizon(
            name="B",
            top_depth_cm=10.0,
            bottom_depth_cm=30.0,
            matrix_hue="7.5YR",
            matrix_value=5.0,
            matrix_chroma=4.0,
            texture="loam",
        )
        assert is_depleted_matrix(h2)[0] is False

    def test_gleyed_matrix(self):
        """Gley 1 and Gley 2 charts with Value >= 4.0."""
        h_gley1 = SoilHorizon(
            name="Bg",
            top_depth_cm=10.0,
            bottom_depth_cm=30.0,
            matrix_hue="5GY",
            matrix_value=5.0,
            matrix_chroma=1.0,
            texture="clay",
        )
        assert is_gleyed_matrix(h_gley1) is True

        # Gley with Value < 4 fails
        h_gley_dark = h_gley1.model_copy()
        h_gley_dark.matrix_value = 3.0
        assert is_gleyed_matrix(h_gley_dark) is False


class TestNRCSIndicators:
    """Tests for individual NRCS hydric soil indicators A11, A12, F3, F6, S5."""

    def test_indicator_a11_depleted_below_dark_surface(self):
        """A11: Depleted layer >= 15 cm thick within 30 cm under dark surface."""
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=12.0,
                matrix_hue="10YR",
                matrix_value=2.5,
                matrix_chroma=1.0,
                texture="loam",
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=12.0,
                bottom_depth_cm=32.0,  # thickness = 20 cm >= 15 cm, starts at 12 cm <= 30 cm
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="clay loam",
            ),
        ]
        res = check_indicator_a11(horizons)
        assert res.confirmed is True
        assert "A" in res.qualifying_layers
        assert "Btg" in res.qualifying_layers

    def test_indicator_a12_thick_dark_surface(self):
        """A12: Thick dark surface >= 30 cm underlain by depleted layer within 35 cm."""
        horizons = [
            SoilHorizon(
                name="A1",
                top_depth_cm=0.0,
                bottom_depth_cm=15.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="mucky loam",
            ),
            SoilHorizon(
                name="A2",
                top_depth_cm=15.0,
                bottom_depth_cm=32.0,  # Cumulative dark = 32 cm >= 30 cm
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="loam",
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=32.0,     # Starts within 35 cm
                bottom_depth_cm=50.0,
                matrix_hue="10YR",
                matrix_value=6.0,
                matrix_chroma=1.0,
                texture="sandy clay loam",
            ),
        ]
        res = check_indicator_a12(horizons)
        assert res.confirmed is True

    def test_indicator_f3_depleted_matrix(self):
        """F3: Depleted matrix in loamy/clayey soils."""
        # Condition 1: >= 5 cm thick starting within 10 cm
        h_cond1 = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=5.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=2.0,
                texture="silt loam",
            ),
            SoilHorizon(
                name="Eg",
                top_depth_cm=5.0,
                bottom_depth_cm=13.0,  # Thickness 8 cm >= 5 cm, starts at 5 cm <= 10 cm
                matrix_hue="10YR",
                matrix_value=6.0,
                matrix_chroma=2.0,
                texture="silt loam",
            ),
        ]
        res1 = check_indicator_f3(h_cond1)
        assert res1.confirmed is True

        # Condition 2: >= 15 cm thick starting within 25 cm
        h_cond2 = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=18.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=3.0,
                texture="clay loam",
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=18.0,
                bottom_depth_cm=38.0,  # Thickness 20 cm >= 15 cm, starts at 18 cm <= 25 cm
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="clay",
            ),
        ]
        res2 = check_indicator_f3(h_cond2)
        assert res2.confirmed is True

    def test_indicator_f6_redox_dark_surface(self):
        """F6: Dark mineral layer >= 10 cm thick within 20 cm with >= 2% redox."""
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=14.0,  # Thickness 14 cm >= 10 cm
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="clay loam",
                redox_percent=4.0,
                redox_distinctness="distinct",
            ),
        ]
        res = check_indicator_f6(horizons)
        assert res.confirmed is True

    def test_indicator_s5_sandy_redox(self):
        """S5: Sandy layer starting within 15 cm with Chroma <= 2 and >= 2% redox."""
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=5.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="loamy sand",
            ),
            SoilHorizon(
                name="C",
                top_depth_cm=5.0,     # Starts at 5 cm <= 15 cm
                bottom_depth_cm=25.0,
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=2.0,    # Chroma <= 2
                texture="sand",
                redox_percent=5.0,
                redox_distinctness="prominent",
            ),
        ]
        res = check_indicator_s5(horizons)
        assert res.confirmed is True

    def test_hydric_soil_determination_fails_upland(self):
        """Upland soil with high chroma and no redox fails all hydric indicators."""
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=10.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=3.0,
                texture="sandy loam",
            ),
            SoilHorizon(
                name="Bt",
                top_depth_cm=10.0,
                bottom_depth_cm=45.0,
                matrix_hue="7.5YR",
                matrix_value=5.0,
                matrix_chroma=6.0,
                texture="clay loam",
            ),
        ]
        det = evaluate_hydric_soils(horizons)
        assert det.hydric_soil_present is False
        assert len(det.confirmed_indicators) == 0
