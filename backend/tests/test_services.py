"""Unit tests for the Palustra Service Layer (TaxonService, DeterminationService, ReportService) and Core Exceptions."""

import io
import pytest
from pypdf import PdfReader
import zipfile

from app.core.exceptions import (
    AmbiguousTaxonWarning,
    InconsistentRegionalSupplementError,
    InvalidCoverPercentageError,
    PalustraDomainError,
    ReportGenerationError,
    TaxonNotFoundError,
)
from app.export.models import USACEPlotExportData
from app.models.schemas import (
    FuzzySearchQuery,
    RegionEnum,
    TaxonValidationRequest,
)
from app.services.determination_service import (
    DeterminationService,
    DeterminationSynthesis,
)
from app.services.report_service import ReportService
from app.services.taxon_service import TaxonService, resolve_scientific_name
from app.wetland.models import SoilHorizon, SpeciesCover


@pytest.fixture
def sample_plot_fixture():
    """Realistic EMP bottomland wetland plot for testing services."""
    return USACEPlotExportData(
        sampling_point="DP-SRV-01",
        project_name="Service Test Delineation",
        region=RegionEnum.EMP,
        latitude=35.75,
        longitude=-78.63,
        hydrology_indicators=["A1", "A2"],
        strata_vegetation={
            "Tree": [
                SpeciesCover(taxon="Acer rubrum", percent_cover=60.0, indicator_status="FAC"),
                SpeciesCover(taxon="Fraxinus pennsylvanica", percent_cover=30.0, indicator_status="FACW"),
            ],
            "Herb": [
                SpeciesCover(taxon="Carex lurida", percent_cover=80.0, indicator_status="OBL"),
            ],
        },
        soil_horizons=[
            SoilHorizon(
                name="A",
                top_depth_cm=0.0,
                bottom_depth_cm=25.0,
                matrix_hue="10YR",
                matrix_value=4.0,
                matrix_chroma=1.0,
                texture="silt loam",
                redox_percent=5.0,
                redox_distinctness="distinct",
            )
        ],
    )


class TestTaxonService:
    """Unit tests for TaxonService FTS5 search, symbol lookup, and USACE ambiguity governance."""

    def test_search_taxa_with_seeded_db(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        response = service.search_taxa(query="Acer", limit=10)
        assert response.total_results >= 2
        symbols = [hit.symbol for hit in response.results]
        assert "ACRU" in symbols

    def test_search_taxa_by_query_model(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        query = FuzzySearchQuery(query="Typha", region=RegionEnum.EMP, limit=5)
        response = service.search_taxa_by_query(query)
        assert response.total_results >= 1
        assert response.results[0].symbol == "TYLA"

    def test_get_by_symbol_success(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        record = service.get_by_symbol("ACRU")
        assert record.usda_plants_symbol == "ACRU"
        assert record.clean_scientific_name == "Acer rubrum"
        assert record.c_value == 3

    def test_get_by_symbol_not_found(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        with pytest.raises(TaxonNotFoundError) as exc_info:
            service.get_by_symbol("NONEXISTENT_XYZ")
        assert "NONEXISTENT_XYZ" in exc_info.value.identifier
        assert isinstance(exc_info.value, PalustraDomainError)

    def test_validate_definitive_taxon(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        req = TaxonValidationRequest(raw_name="Carex lurida Wahlenb.", region=RegionEnum.EMP)
        result = service.validate_field_taxon(req)
        assert result.is_valid is True
        assert result.confidence_level.value == "Definitive"
        assert result.recommended_indicator == "OBL"
        assert result.resolved_taxon is not None
        assert result.resolved_taxon.usda_plants_symbol == "CALU5"

    def test_validate_provisional_cf_issues_warning(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        req = TaxonValidationRequest(raw_name="Carex cf. lurida", region=RegionEnum.EMP)
        with pytest.warns(AmbiguousTaxonWarning) as record:
            result = service.validate_field_taxon(req)
        assert len(record) == 1
        assert record[0].message.ambiguity_type == "provisional_cf"
        assert result.is_valid is True
        assert result.confidence_level.value == "Provisional"

    def test_synonym_normalization(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        normalized = service.normalize_synonym("Aster dumosus")
        assert normalized == "Symphyotrichum dumosum"

    def test_state_heritage_rarity_lookup(self, seeded_db_session):
        service = TaxonService(session=seeded_db_session)
        # Known tracked rare species
        rarity = service.lookup_state_heritage_rarity("Helonias bullata")
        assert rarity["is_rare"] is True
        assert rarity["state_rank"] == "S2"
        assert rarity["state_status"] == "Threatened"

        # Common species
        rarity_common = service.lookup_state_heritage_rarity("Acer rubrum", c_value=3, nativity="Native")
        assert rarity_common["is_rare"] is False
        assert rarity_common["state_rank"] == "S5"

    def test_scientific_name_lru_cache(self):
        resolve_scientific_name.cache_clear()
        initial_info = resolve_scientific_name.cache_info()
        assert initial_info.hits == 0

        # First call: miss
        res1 = resolve_scientific_name("Acer rubrum L. var. trilobum Torr. & A. Gray")
        assert res1["genus"] == "Acer"
        assert res1["species_epithet"] == "rubrum"
        assert res1["infraspecific_rank"] == "var."

        # Second call: hit
        res2 = resolve_scientific_name("Acer rubrum L. var. trilobum Torr. & A. Gray")
        assert res2 == res1
        assert resolve_scientific_name.cache_info().hits >= 1


class TestDeterminationService:
    """Unit tests for DeterminationService business logic and validation constraints."""

    def test_synthesize_determination_valid(self, sample_plot_fixture):
        service = DeterminationService()
        determination = service.synthesize_determination(sample_plot_fixture)
        assert isinstance(determination, DeterminationSynthesis)
        assert determination.plot_id == "DP-SRV-01"
        assert determination.is_wetland is True
        assert determination.hydrophytic_vegetation.hydrophytic_vegetation_present is True
        assert determination.hydric_soils.hydric_soil_present is True
        assert determination.wetland_hydrology.wetland_hydrology_present is True
        assert "JURISDICTIONAL WETLAND CRITERIA SATISFIED" in determination.summary

    def test_invalid_cover_percentage_raises_error(self, sample_plot_fixture):
        service = DeterminationService()
        # Set invalid cover percentage > 100%
        sample_plot_fixture.strata_vegetation["Tree"][0].percent_cover = 120.0
        with pytest.raises(InvalidCoverPercentageError) as exc_info:
            service.synthesize_determination(sample_plot_fixture)
        assert exc_info.value.percent_cover == 120.0
        assert isinstance(exc_info.value, ValueError)

    def test_invalid_regional_supplement_raises_error(self, sample_plot_fixture):
        service = DeterminationService()
        with pytest.raises(InconsistentRegionalSupplementError) as exc_info:
            service.validate_regional_supplement("PACIFIC_NORTHWEST_INVALID")
        assert "PACIFIC_NORTHWEST_INVALID" in exc_info.value.region
        assert isinstance(exc_info.value, ValueError)


class TestReportService:
    """Unit tests for ReportService PDF and GeoJSON orchestrations."""

    def test_generate_plot_pdf(self, sample_plot_fixture):
        service = ReportService()
        pdf_bytes = service.generate_plot_pdf(sample_plot_fixture, watermark="TEST DRAFT")
        assert pdf_bytes.startswith(b"%PDF-")
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 2

    def test_generate_boundary_geojson(self, sample_plot_fixture):
        service = ReportService()
        geojson_data = service.generate_boundary_geojson([sample_plot_fixture], include_transect_lines=True)
        assert geojson_data["type"] == "FeatureCollection"
        assert len(geojson_data["features"]) >= 1
        feat = geojson_data["features"][0]
        assert feat["properties"]["determination_result"] == "WETLAND"

    def test_generate_project_bundle_zip(self, sample_plot_fixture):
        service = ReportService()
        zip_bytes = service.generate_project_bundle_zip([sample_plot_fixture], project_name="Service_Survey")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            namelist = zf.namelist()
            assert "pdfs/USACE_DataForm_DP-SRV-01.pdf" in namelist
            assert "gis/Service_Survey_boundary_points.geojson" in namelist

    def test_report_generation_error_wrapping(self, sample_plot_fixture):
        service = ReportService()
        # Pass broken plot data to induce error
        sample_plot_fixture.sampling_point = ""  # Corrupt or induce issue
        # Create an object that fails PDF rendering
        class CorruptedPlot:
            pass

        with pytest.raises(ReportGenerationError) as exc_info:
            service.generate_plot_pdf(CorruptedPlot())  # type: ignore
        assert "USACE Data Form PDF" in exc_info.value.report_type
