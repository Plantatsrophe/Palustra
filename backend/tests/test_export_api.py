"""Tests for FastAPI export REST API endpoints."""

import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_payload():
    return {
        "plot": {
            "sampling_point": "DP-API-01",
            "project_name": "API Test Delineation",
            "region": "EMP",
            "investigator": "Test Specialist",
            "latitude": 35.5,
            "longitude": -78.5,
            "hydrology_indicators": ["A1"],
            "strata_vegetation": {
                "Herb": [
                    {"taxon": "Typha latifolia", "percent_cover": 75.0, "indicator_status": "OBL"}
                ]
            },
            "soil_horizons": [
                {
                    "name": "A",
                    "top_depth_cm": 0,
                    "bottom_depth_cm": 30,
                    "matrix_hue": "10YR",
                    "matrix_value": 4,
                    "matrix_chroma": 1,
                    "texture": "loam",
                    "redox_percent": 10,
                }
            ],
        },
        "watermark": "API TEST",
    }


def test_export_pdf_endpoint(client, sample_payload):
    """Test POST /api/v1/export/pdf returns valid 2-page PDF binary."""
    response = client.post("/api/v1/export/pdf", json=sample_payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"USACE_DataForm_DP-API-01.pdf\"" in response.headers["content-disposition"]

    pdf_bytes = response.content
    assert pdf_bytes.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2


def test_export_geojson_endpoint(client, sample_payload):
    """Test POST /api/v1/export/geojson returns valid GeoJSON FeatureCollection."""
    req_body = {
        "plots": [sample_payload["plot"]],
        "include_transect_lines": True,
    }
    response = client.post("/api/v1/export/geojson", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["id"] == "DP-API-01"
    assert feature["geometry"]["coordinates"] == [-78.5, 35.5]
    assert feature["properties"]["determination_result"] == "WETLAND"


def test_export_project_bundle_endpoint(client, sample_payload):
    """Test POST /api/v1/export/project-bundle returns valid ZIP with PDFs and GeoJSON."""
    req_body = {
        "plots": [sample_payload["plot"]],
        "include_transect_lines": True,
    }
    response = client.post(
        "/api/v1/export/project-bundle?project_name=Test_Survey",
        json=req_body,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_bytes = response.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        assert "pdfs/USACE_DataForm_DP-API-01.pdf" in namelist
        assert "gis/Test_Survey_boundary_points.geojson" in namelist
