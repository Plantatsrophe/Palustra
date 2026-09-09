"""High-throughput batch plot determination and SQLite connection tuning verification.

Validates:
1. Exact mathematical equivalence between batch evaluation and single-plot evaluation across 50 synthetic plots.
2. Latency benchmark: 50 plots must execute in <150ms.
3. FastAPI REST API endpoint `POST /api/v1/determinations/batch` integration.
4. SQLite connection PRAGMA configuration and in-memory botanical LRU memoization.
"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from palustra.db.session import create_db_engine
from palustra.models.schemas import PlotDeterminationInput, RegionEnum
from palustra.services.determination_service import (
    DeterminationService,
    DeterminationSynthesis,
)
from palustra.services.taxon_service import (
    TaxonService,
    normalize_botanical_query,
    resolve_scientific_name,
)
from palustra.wetland.models import SoilHorizon, SpeciesCover


def create_synthetic_plots(count: int = 50) -> list[PlotDeterminationInput]:
    """Generate diverse synthetic USACE sampling plots for bulk evaluation testing."""
    plots: list[PlotDeterminationInput] = []

    for i in range(1, count + 1):
        is_wetland_candidate = (i % 2 == 1)  # Alternating wetland and upland candidates

        if is_wetland_candidate:
            # Hydrophytic vegetation: OBL/FACW dominants
            strata_veg = {
                "Tree": [
                    SpeciesCover(taxon="Acer rubrum", percent_cover=50.0 + (i % 20), indicator_status="FAC"),
                    SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=25.0, indicator_status="FACW"),
                ],
                "Herb": [
                    SpeciesCover(taxon="Carex lurida", percent_cover=60.0 + (i % 15), indicator_status="OBL"),
                    SpeciesCover(taxon="Typha latifolia", percent_cover=20.0, indicator_status="OBL"),
                ],
            }
            # Confirmed primary hydrology indicators
            hydro_indicators = ["A1", "A2"] if (i % 4 != 0) else ["B1", "B2"]
            # Hydric soil: Depleted matrix (10YR 4/1 with redox concentrations)
            soil_horizons = [
                SoilHorizon(
                    name="A",
                    top_depth_cm=0.0,
                    bottom_depth_cm=20.0 + (i % 10),
                    matrix_hue="10YR",
                    matrix_value=4.0,
                    matrix_chroma=1.0,
                    texture="silt loam",
                    redox_percent=5.0 + (i % 10),
                    redox_distinctness="distinct",
                )
            ]
        else:
            # Upland vegetation: UPL / FACU dominants
            strata_veg = {
                "Tree": [
                    SpeciesCover(taxon="Robinia pseudoacacia", percent_cover=65.0, indicator_status="FACU"),
                    SpeciesCover(taxon="Pinus taeda", percent_cover=20.0, indicator_status="FAC"),
                ],
                "Herb": [
                    SpeciesCover(taxon="Sorghum halepense", percent_cover=55.0, indicator_status="FACU"),
                ],
            }
            # No hydrology indicators
            hydro_indicators = []
            # Upland soil: High chroma matrix (10YR 5/4 without redox)
            soil_horizons = [
                SoilHorizon(
                    name="A",
                    top_depth_cm=0.0,
                    bottom_depth_cm=30.0,
                    matrix_hue="10YR",
                    matrix_value=5.0,
                    matrix_chroma=4.0,
                    texture="sandy loam",
                    redox_percent=0.0,
                )
            ]

        plot = PlotDeterminationInput(
            sampling_point=f"DP-BATCH-{i:03d}",
            project_name="High-Throughput Validation Survey",
            region=RegionEnum.EMP,
            latitude=35.50 + (i * 0.01),
            longitude=-78.50 - (i * 0.01),
            hydrology_indicators=hydro_indicators,
            strata_vegetation=strata_veg,
            soil_horizons=soil_horizons,
        )
        plots.append(plot)

    return plots


class TestBatchProcessing:
    """Benchmark and equivalence test suite for batch plot determination."""

    def test_batch_vs_single_mathematical_equivalence(self):
        """Assert all 50 mathematical determinations in batch are identical to individual evaluations."""
        service = DeterminationService()
        plots = create_synthetic_plots(50)
        assert len(plots) == 50

        # Run batch evaluation
        batch_results = service.evaluate_batch(plots=plots, region="EMP")
        assert len(batch_results) == 50

        # Compare each plot against isolated single-plot evaluation
        for idx, plot in enumerate(plots):
            single_result = service.synthesize_determination(plot)
            batch_result = batch_results[idx]

            assert isinstance(batch_result, DeterminationSynthesis)
            assert batch_result.plot_id == plot.sampling_point
            assert batch_result.is_wetland == single_result.is_wetland
            assert (
                batch_result.hydrophytic_vegetation.hydrophytic_vegetation_present
                == single_result.hydrophytic_vegetation.hydrophytic_vegetation_present
            )
            assert (
                batch_result.hydric_soils.hydric_soil_present
                == single_result.hydric_soils.hydric_soil_present
            )
            assert (
                batch_result.wetland_hydrology.wetland_hydrology_present
                == single_result.wetland_hydrology.wetland_hydrology_present
            )
            assert (
                batch_result.hydrophytic_vegetation.dominance_test_percent
                == single_result.hydrophytic_vegetation.dominance_test_percent
            )
            assert batch_result.summary == single_result.summary
            assert batch_result.model_dump() == single_result.model_dump()

    def test_batch_throughput_benchmark(self):
        """Benchmark throughput: 50 plots must execute in <150ms."""
        service = DeterminationService()
        plots = create_synthetic_plots(50)

        # Warmup execution
        _ = service.evaluate_batch(plots=plots[:5], region="EMP")

        # Timed execution over 50 plots
        start_time = time.perf_counter()
        results = service.evaluate_batch(plots=plots, region="EMP")
        elapsed_sec = time.perf_counter() - start_time
        elapsed_ms = elapsed_sec * 1000.0

        throughput_plots_per_sec = len(plots) / elapsed_sec if elapsed_sec > 0 else float("inf")

        # Telemetry print for documentation and observability
        print(f"\n[BENCHMARK] 50 Plots Batch Evaluation: {elapsed_ms:.2f} ms ({throughput_plots_per_sec:.1f} plots/sec)")

        assert len(results) == 50
        assert elapsed_ms < 150.0, (
            f"Latency benchmark failed: 50 plots completed in {elapsed_ms:.2f}ms, "
            f"exceeding the 150ms constraint."
        )

    def test_batch_determination_api_endpoint(self, client: TestClient):
        """Test POST /api/v1/determinations/batch endpoint with 50 synthetic plots."""
        plots = create_synthetic_plots(50)
        payload = {
            "plots": [p.model_dump() for p in plots],
            "region": "EMP",
        }

        # Timed API round-trip
        start_time = time.perf_counter()
        response = client.post("/api/v1/determinations/batch", json=payload)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        print(f"\n[API BENCHMARK] POST /determinations/batch (50 plots): {elapsed_ms:.2f} ms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 50

        # Verify structure and determinations
        for idx, item in enumerate(data):
            assert item["plot_id"] == plots[idx].sampling_point
            assert "is_jurisdictional_wetland" in item
            assert "hydrophytic_vegetation" in item
            assert "hydric_soils" in item
            assert "wetland_hydrology" in item

    def test_batch_determination_api_list_payload(self, client: TestClient):
        """Test POST /api/v1/determinations/batch with bare list payload format."""
        plots = create_synthetic_plots(5)
        payload = [p.model_dump() for p in plots]

        response = client.post("/api/v1/determinations/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_sqlite_connection_pragma_tuning(self, tmp_path):
        """Verify that SQLite connection tuning runs WAL, synchronous NORMAL, cache_size, and mmap_size."""
        db_file = tmp_path / "pragma_test.db"
        test_engine = create_db_engine(db_url=f"sqlite:///{db_file}")

        with test_engine.connect() as conn:
            journal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
            synchronous = conn.execute(text("PRAGMA synchronous;")).scalar()
            cache_size = conn.execute(text("PRAGMA cache_size;")).scalar()
            mmap_size = conn.execute(text("PRAGMA mmap_size;")).scalar()
            foreign_keys = conn.execute(text("PRAGMA foreign_keys;")).scalar()

            # SQLite PRAGMA return values:
            # journal_mode -> 'wal'
            # synchronous -> 1 (NORMAL)
            # cache_size -> -64000
            # mmap_size -> 268435456
            # foreign_keys -> 1 (ON)
            assert str(journal_mode).lower() == "wal"
            assert synchronous == 1  # 1 corresponds to NORMAL
            assert cache_size == -64000
            assert mmap_size == 268435456
            assert foreign_keys == 1

    def test_botanical_query_memoization(self, seeded_db_session):
        """Verify that normalized botanical queries are memoized and minimize redundant hits."""
        TaxonService.clear_caches()

        raw_query = "   Acer   rubrum   "
        norm1 = normalize_botanical_query(raw_query)
        # Calling with exact same string hits normalization cache
        norm2 = normalize_botanical_query(raw_query)
        assert norm1 == "acer rubrum"
        assert norm2 == norm1
        assert normalize_botanical_query.cache_info().hits >= 1

        # Test search_taxa with whitespace-varying queries on seeded DB session
        service = TaxonService(session=seeded_db_session)
        res1 = service.search_taxa(query="   Acer   ", limit=10)
        res2 = service.search_taxa(query="acer", limit=10)
        assert res1.total_results == res2.total_results
        assert len(res1.results) == len(res2.results)

        # Verify scientific name LRU cache
        res_name1 = resolve_scientific_name("Acer rubrum L.")
        res_name2 = resolve_scientific_name("Acer rubrum L.")
        assert res_name1 == res_name2
        assert resolve_scientific_name.cache_info().hits >= 1

