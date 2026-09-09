"""FastAPI REST API routes for botanical taxonomic search, validation, and ETL."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from palustra.ai import FieldNoteExtractionResponse, FieldNotesParserService

from palustra.config import settings
from palustra.db.fts import search_taxa
from palustra.db.session import get_db
from palustra.etl.cache import field_cache
from palustra.etl.ingest import run_etl_pipeline
from palustra.etl.parser import classify_field_ambiguity, parse_scientific_name
from palustra.models.db_models import IngestionLog, Taxon
from palustra.models.schemas import (
    FuzzySearchResponse,
    FuzzySearchResult,
    IdentificationConfidenceEnum,
    IngestionSummary,
    OfflineCacheManifest,
    RegionEnum,
    TaxonRecord,
    TaxonValidationRequest,
    TaxonValidationResult,
)

router = APIRouter(prefix="/api/v1")

@router.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing DB connectivity, record counts, and cache telemetry."""
    try:
        total_taxa = db.execute(select(func.count(Taxon.id))).scalar() or 0
        cache_stats = field_cache.get_stats()
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "database": {
                "connected": True,
                "total_taxa": total_taxa,
            },
            "field_cache": cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity failure: {str(e)}",
        )

@router.get("/taxa/search", response_model=FuzzySearchResponse, tags=["Taxa Search"])
def search_taxa_endpoint(
    q: str = Query(..., min_length=1, max_length=100, description="Plant name, symbol, or partial string"),
    region: Optional[RegionEnum] = Query(None, description="Optional region filter: EMP or AGCP"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Execute SQLite FTS5 trigram fuzzy search for plant scientific and common names."""
    cache_key = field_cache._generate_key("search", q=q, region=region.value if region else None, limit=limit, offset=offset)
    cached_data = field_cache.get(cache_key)
    if cached_data:
        return FuzzySearchResponse(**cached_data)

    reg_val = region.value if region else None
    search_data = search_taxa(db, query_str=q, limit=limit, offset=offset, region=reg_val)

    response_payload = {
        "query": q,
        "total_results": search_data["total"],
        "results": [FuzzySearchResult(**r) for r in search_data["results"]],
    }
    field_cache.set(cache_key, response_payload)
    return FuzzySearchResponse(**response_payload)

@router.get("/taxa/{symbol}", response_model=TaxonRecord, tags=["Taxa Search"])
def get_taxon_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Retrieve full botanical taxon details by official USDA PLANTS symbol."""
    norm_symbol = symbol.strip().upper()
    cache_key = f"taxon:symbol:{norm_symbol}"
    cached = field_cache.get(cache_key)
    if cached:
        return TaxonRecord(**cached)

    taxon = db.execute(select(Taxon).where(Taxon.symbol == norm_symbol)).scalar_one_or_none()
    if not taxon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Taxon with USDA symbol '{norm_symbol}' not found in database.",
        )

    record = TaxonRecord(
        raw_field_name=taxon.raw_scientific_name,
        clean_scientific_name=taxon.clean_scientific_name,
        accepted_scientific_name=taxon.species_name,
        usda_plants_symbol=taxon.symbol,
        common_name=taxon.common_name,
        family=taxon.family,
        taxonomic_status=taxon.taxonomic_status,
        infraspecific_rank=taxon.infraspecific_rank,
        infraspecific_epithet=taxon.infraspecific_epithet,
        authority=taxon.authority,
        nwpl_indicator_emp=taxon.nwpl_indicator_emp,
        nwpl_indicator_agcp=taxon.nwpl_indicator_agcp,
        c_value=taxon.c_value,
        nativity=taxon.nativity,
        identification_confidence=IdentificationConfidenceEnum.DEFINITIVE,
        flags=[],
    )
    field_cache.set(cache_key, record.model_dump())
    return record

@router.post("/taxa/validate", response_model=TaxonValidationResult, tags=["Taxonomic Governance"])
def validate_field_taxon(
    request: TaxonValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate a field-recorded botanical name against USACE governance rules and USDA PLANTS."""
    raw_name = request.raw_name.strip()
    ambiguity = classify_field_ambiguity(raw_name)

    ambiguity_type = ambiguity["ambiguity_type"]
    target_clean = ambiguity["cleaned_target_name"]
    confidence = IdentificationConfidenceEnum(ambiguity["confidence_level"])
    warnings = list(ambiguity["warnings"])

    # Attempt to resolve against SQLite database
    resolved_taxon_record: Optional[TaxonRecord] = None
    recommended_indicator: Optional[str] = None

    if ambiguity_type in ("provisional_cf", "affinity_aff", None):
        # Look up by clean scientific name
        parsed = parse_scientific_name(target_clean)
        taxon = db.execute(
            select(Taxon).where(
                (Taxon.clean_scientific_name == parsed["clean_name"])
                | (Taxon.species_name == parsed["species_name"])
            ).limit(1)
        ).scalar_one_or_none()

        if taxon:
            resolved_taxon_record = TaxonRecord(
                raw_field_name=taxon.raw_scientific_name,
                clean_scientific_name=taxon.clean_scientific_name,
                accepted_scientific_name=taxon.species_name,
                usda_plants_symbol=taxon.symbol,
                common_name=taxon.common_name,
                family=taxon.family,
                taxonomic_status=taxon.taxonomic_status,
                infraspecific_rank=taxon.infraspecific_rank,
                infraspecific_epithet=taxon.infraspecific_epithet,
                authority=taxon.authority,
                nwpl_indicator_emp=taxon.nwpl_indicator_emp,
                nwpl_indicator_agcp=taxon.nwpl_indicator_agcp,
                c_value=taxon.c_value,
                nativity=taxon.nativity,
                identification_confidence=confidence,
                flags=warnings,
            )
            # Pick regional indicator if region provided
            if request.region == RegionEnum.EMP:
                recommended_indicator = taxon.nwpl_indicator_emp
            elif request.region == RegionEnum.AGCP:
                recommended_indicator = taxon.nwpl_indicator_agcp
        else:
            warnings.append(f"NAME_NOT_FOUND: '{target_clean}' does not match any accepted USDA taxon.")

    elif ambiguity_type == "genus_only":
        # Check homogeneous genus status
        if ambiguity.get("is_homogeneous"):
            homo_status = ambiguity.get("homogeneous_status", {})
            if request.region == RegionEnum.EMP:
                recommended_indicator = homo_status.get("EMP")
            elif request.region == RegionEnum.AGCP:
                recommended_indicator = homo_status.get("AGCP")
        else:
            recommended_indicator = None  # Heterogeneous genus: Indeterminate

    is_valid = (
        resolved_taxon_record is not None
        or ambiguity_type in ("genus_only", "sterile", "indet")
    )

    return TaxonValidationResult(
        is_valid=is_valid,
        input_name=raw_name,
        parsed_clean_name=target_clean,
        confidence_level=confidence,
        ambiguity_type=ambiguity_type,
        resolved_taxon=resolved_taxon_record,
        recommended_indicator=recommended_indicator,
        usace_dominance_rule=ambiguity["usace_dominance_rule"],
        fqa_treatment_rule=ambiguity["fqa_treatment_rule"],
        warnings=warnings,
    )

@router.post("/etl/ingest", response_model=IngestionSummary, tags=["ETL Ingestion"])
def trigger_etl_ingestion(
    rebuild_fts: bool = Query(True, description="Whether to rebuild SQLite FTS5 trigram virtual table after ingest"),
    db: Session = Depends(get_db),
):
    """Trigger the ETL pipeline to ingest USDA PLANTS and USACE NWPL datasets."""
    try:
        summary = run_etl_pipeline(db_session=db, rebuild_fts=rebuild_fts)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL ingestion failed: {str(e)}",
        )

@router.get("/cache/offline-bundle", response_model=OfflineCacheManifest, tags=["Local Field Caching"])
def export_offline_field_bundle(
    response: Response,
    db: Session = Depends(get_db),
):
    """Export complete offline botanical bundle with ETag and Cache-Control headers for PWA sync."""
    cached_bundle = field_cache.load_offline_snapshot("field_offline_bundle.json")
    if not cached_bundle:
        # Generate from database
        taxa = db.execute(select(Taxon).order_by(Taxon.symbol.asc())).scalars().all()
        records: list[dict] = []
        for t in taxa:
            records.append({
                "raw_field_name": t.raw_scientific_name,
                "clean_scientific_name": t.clean_scientific_name,
                "accepted_scientific_name": t.species_name,
                "usda_plants_symbol": t.symbol,
                "common_name": t.common_name,
                "family": t.family,
                "taxonomic_status": t.taxonomic_status,
                "infraspecific_rank": t.infraspecific_rank,
                "infraspecific_epithet": t.infraspecific_epithet,
                "authority": t.authority,
                "nwpl_indicator_emp": t.nwpl_indicator_emp,
                "nwpl_indicator_agcp": t.nwpl_indicator_agcp,
                "c_value": t.c_value,
                "nativity": t.nativity,
                "identification_confidence": "Definitive",
                "flags": [],
            })

        cached_bundle = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_taxa": len(records),
            "taxa": records,
        }
        field_cache.save_offline_snapshot("field_offline_bundle.json", cached_bundle)

    # Compute ETag
    content_str = json.dumps(cached_bundle["taxa"][:5], sort_keys=True) + str(cached_bundle["total_taxa"])
    etag = f'W/"{hashlib.sha256(content_str.encode("utf-8")).hexdigest()[:16]}"'

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"

    return OfflineCacheManifest(**cached_bundle)

@router.get("/cache/stats", tags=["Local Field Caching"])
def get_cache_telemetry():
    """Retrieve operational telemetry from the in-memory local field cache."""
    return field_cache.get_stats()


@router.post(
    "/field-notes/parse-image",
    response_model=FieldNoteExtractionResponse,
    tags=["AI Field Note Transcription"],
    summary="Parse photo of handwritten botanical field notes with Gemini 1.5 Flash",
)
async def parse_field_notes_image_endpoint(
    file: UploadFile = File(..., description="Image file of handwritten field notes"),
    confidence_threshold: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Override confidence threshold for flagging low-confidence entries",
    ),
):
    """Asynchronously parse an uploaded photo of handwritten botanical field notes.

    Enforces strict JSON schemas, calculates per-row extraction confidence scores,
    and flags low-confidence or ambiguous botanical entries.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    mime_type = file.content_type or "image/jpeg"
    parser_service = FieldNotesParserService()
    try:
        result = await parser_service.parse_field_notes_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            confidence_threshold=confidence_threshold,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Field note transcription error: {str(exc)}",
        )
