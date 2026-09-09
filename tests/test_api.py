"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

def test_api_health(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"]["total_taxa"] >= 6

def test_api_search_taxa(client: TestClient):
    resp = client.get("/api/v1/taxa/search", params={"q": "Acer"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Acer"
    assert data["total_results"] >= 2
    symbols = [r["symbol"] for r in data["results"]]
    assert "ACRU" in symbols

def test_api_get_taxon_by_symbol(client: TestClient):
    resp = client.get("/api/v1/taxa/ACRU")
    assert resp.status_code == 200
    data = resp.json()
    assert data["usda_plants_symbol"] == "ACRU"
    assert data["clean_scientific_name"] == "Acer rubrum"
    assert data["nwpl_indicator_emp"] == "FAC"

def test_api_get_taxon_not_found(client: TestClient):
    resp = client.get("/api/v1/taxa/NONEXISTENT999")
    assert resp.status_code == 404

def test_api_validate_definitive_taxon(client: TestClient):
    payload = {
        "raw_name": "Acer rubrum L.",
        "region": "EMP",
    }
    resp = client.post("/api/v1/taxa/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["confidence_level"] == "Definitive"
    assert data["recommended_indicator"] == "FAC"
    assert data["resolved_taxon"]["usda_plants_symbol"] == "ACRU"

def test_api_validate_provisional_cf(client: TestClient):
    payload = {
        "raw_name": "Carex cf. lurida",
        "region": "EMP",
    }
    resp = client.post("/api/v1/taxa/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["confidence_level"] == "Provisional"
    assert data["ambiguity_type"] == "provisional_cf"
    assert data["recommended_indicator"] == "OBL"
    assert "PROVISIONAL" in data["warnings"][0]

def test_api_validate_sterile(client: TestClient):
    payload = {
        "raw_name": "sterile Poaceae",
        "region": "AGCP",
    }
    resp = client.post("/api/v1/taxa/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["confidence_level"] == "Indeterminate"
    assert data["ambiguity_type"] == "sterile"
    assert data["recommended_indicator"] is None
    assert "EXCLUDE entirely from N" in data["fqa_treatment_rule"]

def test_api_cache_offline_bundle(client: TestClient):
    resp = client.get("/api/v1/cache/offline-bundle")
    assert resp.status_code == 200
    assert "ETag" in resp.headers
    assert "Cache-Control" in resp.headers
    data = resp.json()
    assert data["total_taxa"] >= 6
    assert len(data["taxa"]) >= 6

def test_api_cache_stats(client: TestClient):
    resp = client.get("/api/v1/cache/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "hits" in data
    assert "misses" in data
