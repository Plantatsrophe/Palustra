"""Unit tests for SQLite FTS5 trigram fuzzy search."""

import pytest
from palustra.db.fts import search_taxa

def test_fts5_trigram_exact_and_substring_match(seeded_db_session):
    # Substring 'rub' should match 'Acer rubrum'
    res = search_taxa(seeded_db_session, query_str="rub")
    assert res["total"] >= 1
    symbols = [r["symbol"] for r in res["results"]]
    assert "ACRU" in symbols

def test_fts5_trigram_common_name_match(seeded_db_session):
    # 'maple' should match both red maple and boxelder if described
    res = search_taxa(seeded_db_session, query_str="maple")
    assert res["total"] >= 1
    symbols = [r["symbol"] for r in res["results"]]
    assert "ACRU" in symbols

def test_fts5_trigram_symbol_match(seeded_db_session):
    res = search_taxa(seeded_db_session, query_str="QUNI")
    assert res["total"] == 1
    assert res["results"][0]["symbol"] == "QUNI"
    assert res["results"][0]["clean_scientific_name"] == "Quercus nigra"

def test_fts5_short_query_fallback(seeded_db_session):
    # Query < 3 chars ('Ac') falls back to prefix LIKE
    res = search_taxa(seeded_db_session, query_str="Ac")
    assert res["total"] >= 2
    symbols = [r["symbol"] for r in res["results"]]
    assert "ACRU" in symbols
    assert "ACNE2" in symbols
    assert res["results"][0]["matched_field"] == "prefix_like"

def test_fts5_regional_filter(seeded_db_session):
    # Search 'Quercus' filtered by EMP or AGCP
    res_agcp = search_taxa(seeded_db_session, query_str="Quercus", region="AGCP")
    assert res_agcp["total"] >= 1
    assert res_agcp["results"][0]["nwpl_indicator_agcp"] == "FACW"
