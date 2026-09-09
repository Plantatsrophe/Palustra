"""Integration tests for ETL pipeline and dataset loading."""

import pytest
from pathlib import Path
from sqlalchemy import select, func

from palustra.config import settings
from palustra.etl.ingest import (
    load_nwpl_excel,
    load_usda_csv,
    resolve_regional_indicator,
    run_etl_pipeline,
)
from palustra.models.db_models import Taxon, RegionalIndicator

def test_load_nwpl_agcp():
    agcp_data = load_nwpl_excel(settings.nwpl_agcp_path, "AGCP")
    assert len(agcp_data) > 4000
    assert agcp_data["Acer negundo"] == "FAC"
    assert agcp_data["Typha latifolia"] == "OBL"

def test_load_nwpl_emp():
    emp_data = load_nwpl_excel(settings.nwpl_emp_path, "EMP")
    assert len(emp_data) > 3000
    assert emp_data["Acer negundo"] == "FAC"
    assert emp_data["Carex lurida"] == "OBL"

def test_load_usda_csv():
    taxa = load_usda_csv(settings.usda_plants_path)
    assert len(taxa) >= 4800
    symbols = {t["symbol"] for t in taxa}
    assert "ACRU" in symbols
    assert "ACNE2" in symbols
    assert "ACNEN" in symbols

def test_resolve_regional_indicator_direct_and_fallback():
    mock_nwpl = {"Acer negundo": "FAC", "Acer rubrum var. drummondii": "OBL"}
    # Direct variety match
    status, source, level = resolve_regional_indicator(
        "Acer rubrum var. drummondii", "Acer rubrum", mock_nwpl
    )
    assert status == "OBL"
    assert level == "direct"

    # Infraspecific fallback to species
    status, source, level = resolve_regional_indicator(
        "Acer negundo var. texanum", "Acer negundo", mock_nwpl
    )
    assert status == "FAC"
    assert level == "species_fallback"

    # Unmatched
    status, source, level = resolve_regional_indicator(
        "Unknown sp.", "Unknown", mock_nwpl
    )
    assert status is None
    assert level == "unmatched"

def test_run_etl_pipeline_integration(db_session, in_memory_engine):
    summary = run_etl_pipeline(
        db_session=db_session,
        usda_path=settings.usda_plants_path,
        agcp_path=settings.nwpl_agcp_path,
        emp_path=settings.nwpl_emp_path,
        rebuild_fts=True,
    )
    assert summary.status == "SUCCESS"
    assert summary.total_taxa_persisted >= 4800
    assert summary.total_indicators_persisted >= 5000

    # Verify query
    acru = db_session.execute(select(Taxon).where(Taxon.symbol == "ACRU")).scalar_one()
    assert acru.clean_scientific_name == "Acer rubrum"
    assert acru.nwpl_indicator_emp == "FAC"
    assert acru.nwpl_indicator_agcp == "FAC"
