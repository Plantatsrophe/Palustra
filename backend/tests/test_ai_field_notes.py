"""Unit and integration tests for Gemini 1.5 Flash handwritten field notes parser."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from palustra.ai.field_notes_parser import FieldNotesParserService
from palustra.ai.schemas import (
    BotanicalEntryExtraction,
    ConfidenceFlagReasonEnum,
    FieldNoteExtractionResponse,
    FieldNoteMetadata,
)
from palustra.api.app import app


# ---------------------------------------------------------------------------
# Fixtures & Sample Payloads
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_field_note_json():
    """Realistic JSON output representing Gemini 1.5 Flash transcribing handwritten notes."""
    return {
        "metadata": {
            "plot_id": "DP-04",
            "sampling_date": "2026-05-18",
            "investigators": ["B. Miller", "T. Jackson"],
            "project_name": "Neuse River Basin Wetland Mitigation",
            "strata_recorded": ["Tree", "Sapling/Shrub", "Herb"],
            "general_notes": "Forested floodplain flat adjacent to intermittent channel; hummocky microtopography.",
        },
        "entries": [
            {
                "raw_text": "Acer rubrum 35%",
                "taxon": "Acer rubrum",
                "stratum": "Tree",
                "percent_cover": 35.0,
                "extraction_confidence": 0.95,
                "is_low_confidence": False,
                "flag_reasons": [],
                "morphological_adaptations": True,
                "notes": "Buttressed bases observed on >50% of canopy trees",
            },
            {
                "raw_text": "Frax penn 15%",
                "taxon": "Fraxinus pennsylvanica",
                "stratum": "Tree",
                "percent_cover": 15.0,
                "extraction_confidence": 0.88,
                "is_low_confidence": False,
                "flag_reasons": [],
                "morphological_adaptations": False,
                "notes": None,
            },
            {
                "raw_text": "Carex cf. lurida 8%",
                "taxon": "Carex cf. lurida",
                "stratum": "Herb",
                "percent_cover": 8.0,
                "extraction_confidence": 0.65,
                "is_low_confidence": True,
                "flag_reasons": ["LOW_CONFIDENCE_SCORE", "AMBIGUOUS_TAXON_CF"],
                "morphological_adaptations": False,
                "notes": "Immature perigynia",
            },
            {
                "raw_text": "Salix sp. <1%",
                "taxon": "Salix sp.",
                "stratum": "Sapling/Shrub",
                "percent_cover": 0.5,
                "extraction_confidence": 0.70,
                "is_low_confidence": True,
                "flag_reasons": ["LOW_CONFIDENCE_SCORE", "AMBIGUOUS_TAXON_SP"],
                "morphological_adaptations": False,
                "notes": "Seedling without diagnostic aments",
            },
        ],
        "total_entries": 4,
        "low_confidence_count": 2,
        "overall_confidence": 0.795,
        "confidence_threshold_applied": 0.75,
        "status": "flagged_entries_present",
    }


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------

def test_botanical_entry_schema_normalization():
    """Verify string cover representations normalize to floats correctly."""
    # Percentage strings
    e1 = BotanicalEntryExtraction(
        raw_text="Typha latifolia 45%",
        taxon="Typha latifolia",
        percent_cover="45%",  # type: ignore
        extraction_confidence=0.92,
    )
    assert e1.percent_cover == 45.0

    # Trace strings
    e2 = BotanicalEntryExtraction(
        raw_text="Osmundastrum cinnamomeum trace",
        taxon="Osmundastrum cinnamomeum",
        percent_cover="trace",  # type: ignore
        extraction_confidence=0.85,
    )
    assert e2.percent_cover == 0.5

    # '<1%'
    e3 = BotanicalEntryExtraction(
        raw_text="Alnus serrulata <1%",
        taxon="Alnus serrulata",
        percent_cover="<1%",  # type: ignore
        extraction_confidence=0.80,
    )
    assert e3.percent_cover == 0.5


def test_botanical_entry_validation_errors():
    """Verify bounds enforcement on cover and confidence values."""
    with pytest.raises(ValidationError):
        BotanicalEntryExtraction(
            raw_text="Bad Cover",
            taxon="Acer rubrum",
            percent_cover=120.0,  # Invalid: > 100
            extraction_confidence=0.8,
        )

    with pytest.raises(ValidationError):
        BotanicalEntryExtraction(
            raw_text="Bad Cover",
            taxon="Acer rubrum",
            percent_cover=-5.0,  # Invalid: < 0
            extraction_confidence=0.8,
        )


def test_field_note_response_schema_roundtrip(sample_field_note_json):
    """Verify complete response schema serialization and validation."""
    response = FieldNoteExtractionResponse.model_validate(sample_field_note_json)
    assert response.metadata.plot_id == "DP-04"
    assert len(response.entries) == 4
    assert response.low_confidence_count == 2
    assert response.status == "flagged_entries_present"

    # Export to JSON
    json_data = response.model_dump_json()
    assert "DP-04" in json_data
    assert "Acer rubrum" in json_data


# ---------------------------------------------------------------------------
# Asynchronous Service Tests with Mocked Gemini
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_async_parse_field_notes_image_success(sample_field_note_json):
    """Test async image processing with a mocked Gemini 1.5 Flash model."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(sample_field_note_json)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    service = FieldNotesParserService(api_key="test-api-key", model=mock_model)
    fake_image_bytes = b"\xff\xd8\xff\xe0" + b"fake_jpeg_content"

    result = await service.parse_field_notes_image(
        image_bytes=fake_image_bytes,
        mime_type="image/jpeg",
        confidence_threshold=0.75,
    )

    # Verify model was called with inline byte part and prompt
    assert mock_model.generate_content_async.called
    call_args = mock_model.generate_content_async.call_args[0][0]
    image_part = call_args[0]
    assert image_part["mime_type"] == "image/jpeg"
    assert image_part["data"] == fake_image_bytes

    # Verify returned structured data
    assert result.metadata.plot_id == "DP-04"
    assert result.total_entries == 4
    assert result.entries[0].taxon == "Acer rubrum"
    assert result.entries[0].is_low_confidence is False
    assert result.entries[2].taxon == "Carex cf. lurida"
    assert result.entries[2].is_low_confidence is True
    assert "AMBIGUOUS_TAXON_CF" in result.entries[2].flag_reasons


@pytest.mark.anyio
async def test_per_row_confidence_threshold_and_reasons():
    """Verify that entries below threshold receive LOW_CONFIDENCE_SCORE flag."""
    raw_payload = {
        "metadata": {"plot_id": "T-1"},
        "entries": [
            {
                "raw_text": "Juncus effusus 20%",
                "taxon": "Juncus effusus",
                "percent_cover": 20.0,
                "extraction_confidence": 0.60,  # Below 0.75 threshold
                "is_low_confidence": False,
                "flag_reasons": [],
            },
            {
                "raw_text": "Scirpus cyperinus 10%",
                "taxon": "Scirpus cyperinus",
                "percent_cover": 10.0,
                "extraction_confidence": 0.90,  # Above threshold
                "is_low_confidence": False,
                "flag_reasons": [],
            },
        ],
        "total_entries": 2,
        "low_confidence_count": 0,
        "overall_confidence": 0.75,
        "status": "success",
    }

    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(raw_payload)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    service = FieldNotesParserService(api_key="test-key", model=mock_model)
    result = await service.parse_field_notes_image(
        image_bytes=b"sample_bytes",
        mime_type="image/png",
        confidence_threshold=0.75,
    )

    # First entry should be audited and flagged
    entry0 = result.entries[0]
    assert entry0.is_low_confidence is True
    assert ConfidenceFlagReasonEnum.LOW_CONFIDENCE_SCORE.value in entry0.flag_reasons

    # Second entry should remain clean
    entry1 = result.entries[1]
    assert entry1.is_low_confidence is False
    assert len(entry1.flag_reasons) == 0

    assert result.low_confidence_count == 1
    assert result.status == "flagged_entries_present"


@pytest.mark.anyio
async def test_botanical_ambiguity_enrichment():
    """Verify that sp., cf., aff., and sterile taxons are automatically flagged."""
    raw_payload = {
        "metadata": {"plot_id": "AMB-1"},
        "entries": [
            {
                "raw_text": "Carex cf. lurida 10%",
                "taxon": "Carex cf. lurida",
                "percent_cover": 10.0,
                "extraction_confidence": 0.85,  # High extraction confidence but ambiguous botanical status
                "is_low_confidence": False,
                "flag_reasons": [],
            },
            {
                "raw_text": "Quercus aff. nigra 25%",
                "taxon": "Quercus aff. nigra",
                "percent_cover": 25.0,
                "extraction_confidence": 0.85,
                "is_low_confidence": False,
                "flag_reasons": [],
            },
            {
                "raw_text": "Cyperus sp. 5%",
                "taxon": "Cyperus sp.",
                "percent_cover": 5.0,
                "extraction_confidence": 0.90,
                "is_low_confidence": False,
                "flag_reasons": [],
            },
            {
                "raw_text": "Panicum sterile 2%",
                "taxon": "Panicum sterile",
                "percent_cover": 2.0,
                "extraction_confidence": 0.95,
                "is_low_confidence": False,
                "flag_reasons": [],
            },
        ],
        "total_entries": 4,
        "low_confidence_count": 0,
        "overall_confidence": 0.8875,
        "status": "success",
    }

    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(raw_payload)
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    service = FieldNotesParserService(api_key="test-key", model=mock_model)
    result = await service.parse_field_notes_image(
        image_bytes=b"bytes",
        mime_type="image/webp",
        confidence_threshold=0.75,
    )

    assert result.entries[0].is_low_confidence is True
    assert ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_CF.value in result.entries[0].flag_reasons

    assert result.entries[1].is_low_confidence is True
    assert ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_AFF.value in result.entries[1].flag_reasons

    assert result.entries[2].is_low_confidence is True
    assert ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_SP.value in result.entries[2].flag_reasons

    assert result.entries[3].is_low_confidence is True
    assert ConfidenceFlagReasonEnum.STERILE_SPECIMEN.value in result.entries[3].flag_reasons

    assert result.low_confidence_count == 4
    assert result.status == "flagged_entries_present"


@pytest.mark.anyio
async def test_invalid_image_inputs():
    """Verify validation errors for empty bytes and unsupported MIME types."""
    service = FieldNotesParserService(api_key="test-key")

    with pytest.raises(ValueError, match="Image bytes payload cannot be empty"):
        await service.parse_field_notes_image(b"")

    with pytest.raises(ValueError, match="Unsupported image MIME type"):
        await service.parse_field_notes_image(b"data", mime_type="application/pdf")


@pytest.mark.anyio
async def test_empty_or_malformed_gemini_output():
    """Verify error handling when Gemini returns empty or non-JSON output."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is plain text, not JSON"
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    service = FieldNotesParserService(api_key="test-key", model=mock_model)

    with pytest.raises(ValueError, match="Failed to parse Gemini output as JSON"):
        await service.parse_field_notes_image(b"valid_bytes", mime_type="image/jpeg")


# ---------------------------------------------------------------------------
# FastAPI Route Tests
# ---------------------------------------------------------------------------

def test_api_parse_field_notes_image_endpoint(sample_field_note_json):
    """Test POST /api/v1/field-notes/parse-image route using TestClient."""
    client = TestClient(app)

    with patch.object(FieldNotesParserService, "parse_field_notes_image") as mock_parse:
        mock_parse.return_value = FieldNoteExtractionResponse.model_validate(sample_field_note_json)

        files = {"file": ("field_sheet.jpg", b"mock_jpeg_bytes", "image/jpeg")}
        resp = client.post("/api/v1/field-notes/parse-image?confidence_threshold=0.80", files=files)

        assert resp.status_code == 200
        data = resp.json()
        assert data["metadata"]["plot_id"] == "DP-04"
        assert len(data["entries"]) == 4
        assert data["status"] == "flagged_entries_present"
        assert data["confidence_threshold_applied"] == 0.75


def test_api_parse_field_notes_empty_file():
    """Test POST /api/v1/field-notes/parse-image with empty file raises 400."""
    client = TestClient(app)
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    resp = client.post("/api/v1/field-notes/parse-image", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()
