"""Comprehensive unit tests for hydrophytic vegetation mathematical algorithms."""

import pytest
from app.wetland.models import SpeciesCover
from app.wetland.vegetation import (
    calculate_prevalence_index,
    calculate_stratum_50_20,
    evaluate_hydrophytic_vegetation,
)


class TestStratumDominance5020:
    """Tests for per-stratum 50/20 dominance rule and tie-breaking."""

    def test_basic_50_20_dominance(self):
        """Standard scenario with one >50% dominant and one >=20% dominant."""
        species = [
            SpeciesCover(taxon="Acer rubrum", percent_cover=60.0, indicator_status="FAC"),
            SpeciesCover(taxon="Betula nigra", percent_cover=20.0, indicator_status="FACW"),
            SpeciesCover(taxon="Carpinus caroliniana", percent_cover=10.0, indicator_status="FAC"),
            SpeciesCover(taxon="Ilex opaca", percent_cover=10.0, indicator_status="FACU"),
        ]
        result = calculate_stratum_50_20("Tree", species)
        assert result.total_cover == 100.0
        assert result.threshold_50 == 50.0
        assert result.threshold_20 == 20.0

        dom_names = [d.taxon for d in result.dominants]
        assert "Acer rubrum" in dom_names       # selected by 50% rule
        assert "Betula nigra" in dom_names      # selected by 20% rule
        assert "Carpinus caroliniana" not in dom_names
        assert "Ilex opaca" not in dom_names
        assert len(result.dominants) == 2

    def test_exact_50_percent_cutoff_tie_breaking(self):
        """Regulatory tie-breaking: all species tied with the cutoff species must be dominants.

        Plot setup:
        Species A: 40% (running sum = 40 <= 50)
        Species B: 15% (running sum = 55 > 50) -> Cutoff species at 15%
        Species C: 15% -> Tied with cutoff species at 15%
        Species D: 15% -> Tied with cutoff species at 15%
        Species E: 15% -> Tied with cutoff species at 15%
        All 5 species must be included in the dominant list!
        """
        species = [
            SpeciesCover(taxon="Species A", percent_cover=40.0, indicator_status="OBL"),
            SpeciesCover(taxon="Species B", percent_cover=15.0, indicator_status="FACW"),
            SpeciesCover(taxon="Species C", percent_cover=15.0, indicator_status="FAC"),
            SpeciesCover(taxon="Species D", percent_cover=15.0, indicator_status="FACU"),
            SpeciesCover(taxon="Species E", percent_cover=15.0, indicator_status="UPL"),
        ]
        result = calculate_stratum_50_20("Herb", species)
        assert result.total_cover == 100.0
        assert result.threshold_50 == 50.0

        dom_names = [d.taxon for d in result.dominants]
        assert len(dom_names) == 5
        assert set(dom_names) == {"Species A", "Species B", "Species C", "Species D", "Species E"}
        assert len(result.tied_50_species) == 3

    def test_20_percent_rule_with_exact_tie(self):
        """Species exactly at the 20% mark must be included."""
        species = [
            SpeciesCover(taxon="Carex lurida", percent_cover=50.0, indicator_status="OBL"),
            SpeciesCover(taxon="Juncus effusus", percent_cover=20.0, indicator_status="FACW"),
            SpeciesCover(taxon="Scirpus cyperinus", percent_cover=20.0, indicator_status="OBL"),
            SpeciesCover(taxon="Microstegium vimineum", percent_cover=10.0, indicator_status="FAC"),
        ]
        result = calculate_stratum_50_20("Herb", species)
        dom_names = [d.taxon for d in result.dominants]
        # Total = 100, T50 = 50.0. Carex lurida alone is 50.0, not > 50.0.
        # Running sum with Juncus = 70.0 > 50.0.
        # Juncus and Scirpus are also >= 20%.
        assert set(dom_names) == {"Carex lurida", "Juncus effusus", "Scirpus cyperinus"}

    def test_single_dominant_overwhelming_cover(self):
        """One species with >90% cover."""
        species = [
            SpeciesCover(taxon="Typha latifolia", percent_cover=95.0, indicator_status="OBL"),
            SpeciesCover(taxon="Lemna minor", percent_cover=5.0, indicator_status="OBL"),
        ]
        result = calculate_stratum_50_20("Herb", species)
        assert [d.taxon for d in result.dominants] == ["Typha latifolia"]

    def test_empty_stratum(self):
        """Stratum with no species or 0% cover."""
        result = calculate_stratum_50_20("Woody Vine", [])
        assert result.total_cover == 0.0
        assert result.dominants == []


class TestPrevalenceIndex:
    """Tests for Prevalence Index arithmetic precision and regulatory boundaries."""

    def test_pi_pass_boundary(self):
        """PI of 3.004 rounds to 3.00 using ROUND_HALF_UP (PASSED)."""
        # Weighted sum = (99.6 * 3) + (0.4 * 4) = 298.8 + 1.6 = 300.4
        # Total cover = 100.0
        # PI = 3.004 -> rounded = 3.00 <= 3.00
        species = [
            SpeciesCover(taxon="FAC Taxon", percent_cover=99.6, indicator_status="FAC"),
            SpeciesCover(taxon="FACU Taxon", percent_cover=0.4, indicator_status="FACU"),
        ]
        pi = calculate_prevalence_index(species)
        assert pi == 3.00
        assert pi <= 3.00

    def test_pi_fail_boundary(self):
        """PI of 3.006 rounds to 3.01 using ROUND_HALF_UP (FAILED)."""
        # Weighted sum = (99.4 * 3) + (0.6 * 4) = 298.2 + 2.4 = 300.6
        # Total cover = 100.0
        # PI = 3.006 -> rounded = 3.01 > 3.00
        species = [
            SpeciesCover(taxon="FAC Taxon", percent_cover=99.4, indicator_status="FAC"),
            SpeciesCover(taxon="FACU Taxon", percent_cover=0.6, indicator_status="FACU"),
        ]
        pi = calculate_prevalence_index(species)
        assert pi == 3.01
        assert pi > 3.00

    def test_pi_with_unlisted_and_all_indicators(self):
        """Verify weights: OBL=1, FACW=2, FAC=3, FACU=4, UPL=5, NL=5."""
        species = [
            SpeciesCover(taxon="Sp1", percent_cover=20.0, indicator_status="OBL"),   # 20 * 1 = 20
            SpeciesCover(taxon="Sp2", percent_cover=30.0, indicator_status="FACW"),  # 30 * 2 = 60
            SpeciesCover(taxon="Sp3", percent_cover=20.0, indicator_status="FAC"),   # 20 * 3 = 60
            SpeciesCover(taxon="Sp4", percent_cover=20.0, indicator_status="FACU"),  # 20 * 4 = 80
            SpeciesCover(taxon="Sp5", percent_cover=10.0, indicator_status="NL"),    # 10 * 5 = 50
        ]
        # Total cover = 100. Weighted sum = 20 + 60 + 60 + 80 + 50 = 270.
        # PI = 2.70
        pi = calculate_prevalence_index(species)
        assert pi == 2.70


class TestHydrophyticVegetationEvaluation:
    """Tests for complete hydrophytic vegetation determination workflow."""

    def test_rapid_test_success(self):
        """100% of dominant species are OBL and FACW."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Taxodium distichum", percent_cover=70.0, indicator_status="OBL"),
                SpeciesCover(taxon="Nyssa aquatica", percent_cover=30.0, indicator_status="OBL"),
            ],
            "Herb": [
                SpeciesCover(taxon="Saururus cernuus", percent_cover=80.0, indicator_status="OBL"),
            ],
        }
        res = evaluate_hydrophytic_vegetation(strata)
        assert res.rapid_test_passed is True
        assert res.hydrophytic_vegetation_present is True

    def test_dominance_test_strict_50_percent_boundary_fail(self):
        """Exactly 50.0% dominance fails the Dominance Test (>50.0% required)."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Quercus phellos", percent_cover=50.0, indicator_status="FACW"),
                SpeciesCover(taxon="Fagus grandifolia", percent_cover=50.0, indicator_status="FACU"),
            ],
        }
        res = evaluate_hydrophytic_vegetation(strata)
        # Dominants: Quercus phellos (FACW), Fagus grandifolia (FACU). Total = 2, A = 1.
        # 1 / 2 = 50.0%
        assert res.dominance_test_a == 1
        assert res.dominance_test_b == 2
        assert res.dominance_test_percent == 50.0
        assert res.dominance_test_passed is False  # Must strictly exceed 50.0%

    def test_dominance_test_passing_over_50_percent(self):
        """3 out of 4 dominants (75.0%) passes the Dominance Test."""
        strata = {
            "Tree": [
                SpeciesCover(taxon="Liquidambar styraciflua", percent_cover=40.0, indicator_status="FAC"),
                SpeciesCover(taxon="Acer rubrum", percent_cover=35.0, indicator_status="FAC"),
                SpeciesCover(taxon="Pinus taeda", percent_cover=25.0, indicator_status="FAC"),
            ],
            "Herb": [
                SpeciesCover(taxon="Chasmanthium latifolium", percent_cover=70.0, indicator_status="FAC"),
                SpeciesCover(taxon="Lonicera japonica", percent_cover=30.0, indicator_status="FACU"),
            ],
        }
        res = evaluate_hydrophytic_vegetation(strata)
        assert res.dominance_test_passed is True
        assert res.hydrophytic_vegetation_present is True

    def test_morphological_adaptations_rescue(self):
        """FACU dominant with morphological adaptations reassigned to FAC to satisfy criteria."""
        strata = {
            "Tree": [
                SpeciesCover(
                    taxon="Carya ovata",
                    percent_cover=50.0,
                    indicator_status="FACU",
                    has_morphological_adaptations=True,  # Buttressed trunk / hypertrophied lenticels on >=50%
                ),
                SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=30.0, indicator_status="FACW"),
                SpeciesCover(taxon="Juniperus virginiana", percent_cover=20.0, indicator_status="UPL"),
            ],
        }
        # Initially: Dominants: Carya (FACU), Fraxinus (FACW), Juniperus (UPL). Total B = 3.
        # A = 1 (FACW). Dominance = 1/3 = 33.3% (fails).
        # PI = (30*2 + 50*4 + 20*5)/100 = (60+200+100)/100 = 3.60 > 3.00 (fails).
        # With adaptations: Carya ovata becomes FAC.
        # Now: Dominants = Carya (FAC), Fraxinus (FACW), Juniperus (UPL).
        # A = 2 / 3 = 66.7% > 50.0% (passes!).
        res = evaluate_hydrophytic_vegetation(strata, enable_morphological_adaptations=True)
        assert res.hydrophytic_vegetation_present is True
        assert res.dominance_test_passed is True
        assert res.dominance_test_percent == 66.67
        assert any("Morphological Adaptations" in rem for rem in res.remarks)
