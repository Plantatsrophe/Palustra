"""Unit tests for polymorphic USACE Regional Supplement Strategy Pattern and Factory."""

from typing import Dict, List, Optional, Set
import pytest

from app.wetland.models import RegionEnum, SoilHorizon, SpeciesCover
from app.wetland.regions import (
    AGCPPolicy,
    EMPPolicy,
    RegionalPolicyFactory,
    RegionalSupplementEnum,
    RegionalSupplementPolicy,
    StratumCriteria,
)
from app.wetland.soils import (
    check_indicator_f19,
    check_indicator_f20,
    evaluate_hydric_soils,
)
from app.wetland.hydrology import (
    evaluate_wetland_hydrology,
    get_indicator_tier,
)
from app.wetland.vegetation import (
    classify_stratum,
    evaluate_hydrophytic_vegetation,
)
from app.wetland.synthesis import perform_jurisdictional_wetland_determination


class TestRegionalPolicyFactory:
    """Tests for RegionalPolicyFactory resolution, caching, and extensibility."""

    def setup_method(self):
        RegionalPolicyFactory.clear_cache()

    def test_get_policy_via_enum(self):
        emp_policy = RegionalPolicyFactory.get_policy(RegionalSupplementEnum.EMP)
        assert isinstance(emp_policy, EMPPolicy)
        assert emp_policy.region_code == RegionalSupplementEnum.EMP

        agcp_policy = RegionalPolicyFactory.get_policy(RegionalSupplementEnum.AGCP)
        assert isinstance(agcp_policy, AGCPPolicy)
        assert agcp_policy.region_code == RegionalSupplementEnum.AGCP

    def test_get_policy_via_string_case_insensitive(self):
        emp1 = RegionalPolicyFactory.get_policy("emp")
        emp2 = RegionalPolicyFactory.get_policy("EMP")
        assert isinstance(emp1, EMPPolicy)
        assert emp1 is emp2  # Cached singleton

        agcp = RegionalPolicyFactory.get_policy("AgCp")
        assert isinstance(agcp, AGCPPolicy)

    def test_get_policy_idempotency_with_instance(self):
        emp = EMPPolicy()
        resolved = RegionalPolicyFactory.get_policy(emp)
        assert resolved is emp

    def test_get_policy_unsupported_region_raises(self):
        with pytest.raises(ValueError, match="Unsupported USACE regional supplement"):
            RegionalPolicyFactory.get_policy("UNKNOWN_REGION")

    def test_dynamic_extensibility_register_new_region(self):
        """Verify adding a 3rd USACE region (Midwest - MW) simply by registering a new policy."""
        class MockMidwestPolicy(RegionalSupplementPolicy):
            @property
            def region_code(self) -> RegionalSupplementEnum:
                return RegionalSupplementEnum.MW

            @property
            def region_name(self) -> str:
                return "Midwest Regional Supplement"

            def get_indicator_status(self, taxon_id: str, default_status: str = "NL") -> str:
                return "FAC" if taxon_id.upper() == "CORNUS SERICEA" else default_status

            def get_stratum_definitions(self) -> Dict[str, StratumCriteria]:
                return {
                    "Tree": StratumCriteria(name="Tree", min_dbh_in=3.0),
                    "Sapling": StratumCriteria(name="Sapling", min_dbh_in=1.0, max_dbh_in=3.0),
                    "Shrub": StratumCriteria(name="Shrub", max_dbh_in=1.0, min_height_m=1.0),
                    "Herb": StratumCriteria(name="Herb", max_height_m=1.0),
                    "Woody Vine": StratumCriteria(name="Woody Vine", min_height_m=1.0, growth_form="vine"),
                }

            def validate_hydrology_indicators(self, primary: List[str], secondary: List[str]) -> bool:
                return len(primary) >= 1 or len(secondary) >= 2

            def validate_hydric_soil_indicators(self, indicators: List[str]) -> bool:
                return "A11" in indicators

            def get_hydrology_tier(self, indicator_code: str) -> str:
                return "Primary" if indicator_code == "A1" else "Secondary"

            @property
            def approved_soil_indicators(self) -> Set[str]:
                return {"A11", "F3"}

        RegionalPolicyFactory.register_policy("MW", MockMidwestPolicy)
        try:
            mw = RegionalPolicyFactory.get_policy("MW")
            assert isinstance(mw, MockMidwestPolicy)
            assert mw.region_name == "Midwest Regional Supplement"
            assert mw.get_indicator_status("Cornus sericea") == "FAC"
            assert "Sapling" in mw.get_stratum_definitions()
        finally:
            # Clean up factory registry
            RegionalPolicyFactory._REGISTRY.pop("MW", None)
            RegionalPolicyFactory.clear_cache()


class TestSpeciesIndicatorRegionalDifferences:
    """Tests proving regional botanical indicator status differences."""

    def test_quercus_nigra_regional_status_shift(self):
        """Quercus nigra (Water Oak) is FAC in EMP but FACW in AGCP."""
        emp = EMPPolicy()
        agcp = AGCPPolicy()

        assert emp.get_indicator_status("Quercus nigra") == "FAC"
        assert emp.get_indicator_status("QUNI") == "FAC"

        assert agcp.get_indicator_status("Quercus nigra") == "FACW"
        assert agcp.get_indicator_status("QUNI") == "FACW"

    def test_robinia_pseudoacacia_regional_status_shift(self):
        """Robinia pseudoacacia (Black Locust) is FACU in EMP but UPL in AGCP."""
        emp = EMPPolicy()
        agcp = AGCPPolicy()

        assert emp.get_indicator_status("Robinia pseudoacacia") == "FACU"
        assert emp.get_indicator_status("ROPS") == "FACU"

        assert agcp.get_indicator_status("Robinia pseudoacacia") == "UPL"
        assert agcp.get_indicator_status("ROPS") == "UPL"

    def test_rapid_test_differential_outcome_from_species_shift(self):
        """A stand dominated 100% by Quercus nigra passes the Rapid Test in AGCP (FACW) but fails in EMP (FAC)."""
        plot_strata = {
            "Tree": [
                SpeciesCover(taxon="Quercus nigra", percent_cover=80.0),
            ]
        }

        # Under EMP: Quercus nigra resolves to FAC -> Rapid Test requires 100% OBL/FACW -> Fails Rapid Test
        emp_det = evaluate_hydrophytic_vegetation(plot_strata, policy=RegionalSupplementEnum.EMP)
        assert emp_det.rapid_test_passed is False
        assert emp_det.dominance_test_passed is True  # Dominance test still passes (100% FAC)
        assert emp_det.prevalence_index == 3.00

        # Under AGCP: Quercus nigra resolves to FACW -> Passes Rapid Test!
        agcp_det = evaluate_hydrophytic_vegetation(plot_strata, policy=RegionalSupplementEnum.AGCP)
        assert agcp_det.rapid_test_passed is True
        assert agcp_det.prevalence_index == 2.00


class TestStratumDefinitions:
    """Tests for stratum size thresholds and criteria matching across regions."""

    def test_emp_strata_definitions(self):
        emp = EMPPolicy()
        definitions = emp.get_stratum_definitions()

        assert "Tree" in definitions
        assert "Sapling/Shrub" in definitions
        assert "Herb" in definitions
        assert "Woody Vine" in definitions

        tree = definitions["Tree"]
        assert tree.min_dbh_in == 3.0
        assert tree.matches(dbh_in=5.0, is_woody=True) is True
        assert tree.matches(dbh_in=2.0, is_woody=True) is False

        sapling_shrub = definitions["Sapling/Shrub"]
        assert sapling_shrub.max_dbh_in == 3.0
        assert sapling_shrub.min_height_m == 1.0
        assert sapling_shrub.matches(dbh_in=1.5, height_m=2.0, is_woody=True) is True
        assert sapling_shrub.matches(dbh_in=4.0, height_m=2.0, is_woody=True) is False

    def test_classify_stratum_utility(self):
        assert classify_stratum("EMP", dbh_in=4.5, is_woody=True) == "Tree"
        assert classify_stratum("EMP", dbh_in=1.5, height_m=2.0, is_woody=True) == "Sapling/Shrub"
        assert classify_stratum("EMP", height_m=0.5, is_woody=True) == "Herb"
        assert classify_stratum("EMP", height_m=2.0, is_vine=True) == "Woody Vine"


class TestHydrologyRegionalTiers:
    """Tests for regional hydrology indicator tier differences and validation."""

    def test_b6_surface_soil_cracks_tier_difference(self):
        """B6 is Primary in AGCP but Secondary in EMP."""
        emp = EMPPolicy()
        agcp = AGCPPolicy()

        assert emp.get_hydrology_tier("B6") == "Secondary"
        assert agcp.get_hydrology_tier("B6") == "Primary"

        # B6 alone satisfies AGCP
        assert agcp.validate_hydrology_indicators(primary=["B6"], secondary=[]) is True
        # B6 alone in primary does not satisfy EMP (since B6 is secondary in EMP)
        assert emp.validate_hydrology_indicators(primary=["B6"], secondary=[]) is False

        # In EMP, B6 requires a second secondary indicator
        assert emp.validate_hydrology_indicators(primary=[], secondary=["B6", "B10"]) is True

    def test_b9_water_stained_leaves_tier_difference(self):
        """B9 is Primary in AGCP but Secondary in EMP."""
        emp = EMPPolicy()
        agcp = AGCPPolicy()

        assert emp.get_hydrology_tier("B9") == "Secondary"
        assert agcp.get_hydrology_tier("B9") == "Primary"

        agcp_det = evaluate_wetland_hydrology(agcp, observed_indicators=["B9"])
        assert agcp_det.wetland_hydrology_present is True
        assert "B9" in agcp_det.primary_indicators

        emp_det = evaluate_wetland_hydrology(emp, observed_indicators=["B9"])
        assert emp_det.wetland_hydrology_present is False
        assert "B9" in emp_det.secondary_indicators

    def test_d6_sphagnum_moss_regional_recognition(self):
        """D6 is recognized as Secondary in EMP, but Not Recognized in AGCP."""
        emp = EMPPolicy()
        agcp = AGCPPolicy()

        assert emp.get_hydrology_tier("D6") == "Secondary"
        assert agcp.get_hydrology_tier("D6") == "Not Recognized"

        # Paired with D2 (Geomorphic Position):
        # Passes in EMP (2 secondary)
        emp_det = evaluate_wetland_hydrology(emp, observed_indicators=["D6", "D2"])
        assert emp_det.wetland_hydrology_present is True

        # Fails in AGCP (D6 ignored -> only 1 secondary)
        agcp_det = evaluate_wetland_hydrology(agcp, observed_indicators=["D6", "D2"])
        assert agcp_det.wetland_hydrology_present is False


class TestHydricSoilRegionalDifferences:
    """Tests for regional hydric soil indicators (F19 Piedmont Floodplain vs F20 Anomalous Bright Loamy)."""

    def test_indicator_f19_piedmont_floodplain_soils(self):
        """F19 is confirmed on floodplains with Value <= 4, Chroma <= 2, >= 2% redox starting within 25 cm."""
        f19_profile = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=5.0,
                matrix_hue="10YR",
                matrix_value=4.0,     # Value=4, Chroma=3 (not a dark surface, so A11/A12 fail)
                matrix_chroma=3.0,
                texture="silt loam",
            ),
            SoilHorizon(
                name="Bw",
                top_depth_cm=5.0,
                bottom_depth_cm=25.0,  # 20 cm thick starting at 5 cm <= 25 cm
                matrix_hue="10YR",
                matrix_value=3.0,      # Value=3 <= 4 (not a depleted matrix, so F3 fails; Chroma=2 so F6 fails)
                matrix_chroma=2.0,     # Chroma=2 <= 2
                texture="loam",        # Loam (not sandy, so S5 fails)
                redox_percent=3.0,     # >= 2% distinct redox
                redox_distinctness="distinct",
            ),
        ]
        res = check_indicator_f19(f19_profile)
        assert res.confirmed is True
        assert res.code == "F19"

        # F19 is approved in EMP
        emp = EMPPolicy()
        assert emp.validate_hydric_soil_indicators(["F19"]) is True
        emp_det = evaluate_hydric_soils(f19_profile, policy=emp)
        assert emp_det.hydric_soil_present is True
        assert "F19" in emp_det.confirmed_indicators

        # F19 is NOT approved in AGCP
        agcp = AGCPPolicy()
        assert agcp.validate_hydric_soil_indicators(["F19"]) is False
        agcp_det = evaluate_hydric_soils(f19_profile, policy=agcp)
        assert agcp_det.hydric_soil_present is False
        assert "F19" not in agcp_det.confirmed_indicators
        assert any("NOT APPROVED in AGCP" in rem for rem in agcp_det.remarks)

    def test_indicator_f20_anomalous_bright_loamy_soils(self):
        """F20 is confirmed in AGCP with Value >= 5, Chroma 3 or 4, >= 10% redox starting within 30 cm."""
        f20_profile = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=8.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=2.0,
                texture="sandy loam",
            ),
            SoilHorizon(
                name="Bv",
                top_depth_cm=8.0,
                bottom_depth_cm=22.0,  # 14 cm thick starting at 8 cm <= 30 cm
                matrix_hue="7.5YR",
                matrix_value=5.0,      # Value >= 5
                matrix_chroma=4.0,     # Chroma 3 or 4
                texture="loam",
                redox_percent=12.0,    # >= 10%
                redox_distinctness="prominent",
            ),
        ]
        res = check_indicator_f20(f20_profile)
        assert res.confirmed is True
        assert res.code == "F20"

        # F20 is approved in AGCP
        agcp = AGCPPolicy()
        assert agcp.validate_hydric_soil_indicators(["F20"]) is True
        agcp_det = evaluate_hydric_soils(f20_profile, policy=agcp)
        assert agcp_det.hydric_soil_present is True
        assert "F20" in agcp_det.confirmed_indicators

        # F20 is NOT approved in EMP
        emp = EMPPolicy()
        assert emp.validate_hydric_soil_indicators(["F20"]) is False
        emp_det = evaluate_hydric_soils(f20_profile, policy=emp)
        assert emp_det.hydric_soil_present is False
        assert "F20" not in emp_det.confirmed_indicators


class TestJurisdictionalSynthesisWithInjectedPolicy:
    """End-to-end tests for perform_jurisdictional_wetland_determination using policy injection."""

    def test_synthesis_divergence_based_on_region(self):
        """Same plot with B6 alone: satisfies AGCP (B6 Primary) but fails EMP (B6 Secondary)."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Acer rubrum", percent_cover=60.0, indicator_status="FAC"),
                SpeciesCover(taxon="Liquidambar styraciflua", percent_cover=40.0, indicator_status="FAC"),
            ]
        }
        horizons = [
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=10.0,
                matrix_hue="10YR",
                matrix_value=3.0,
                matrix_chroma=1.0,
                texture="silt loam",
            ),
            SoilHorizon(
                name="Btg",
                top_depth_cm=10.0,
                bottom_depth_cm=30.0,
                matrix_hue="10YR",
                matrix_value=5.0,
                matrix_chroma=1.0,
                texture="clay loam",
            ),
        ]
        # Only B6 observed
        hydrology = ["B6"]

        # 1. Under AGCP policy -> B6 is Primary -> Wetland
        agcp_res = perform_jurisdictional_wetland_determination(
            plot_id="TEST-PLOT-DIFF",
            region=RegionalPolicyFactory.get_policy(RegionalSupplementEnum.AGCP),
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )
        assert agcp_res.is_jurisdictional_wetland is True
        assert agcp_res.wetland_hydrology.wetland_hydrology_present is True

        # 2. Under EMP policy -> B6 is Secondary (1 secondary is insufficient) -> Non-Wetland
        emp_res = perform_jurisdictional_wetland_determination(
            plot_id="TEST-PLOT-DIFF",
            region=RegionalPolicyFactory.get_policy(RegionalSupplementEnum.EMP),
            strata_vegetation=strata,
            soil_horizons=horizons,
            hydrology_indicators=hydrology,
        )
        assert emp_res.is_jurisdictional_wetland is False
        assert emp_res.wetland_hydrology.wetland_hydrology_present is False
