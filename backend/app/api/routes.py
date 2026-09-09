"""FastAPI presentation controllers for botanical taxonomy, determination, and regulatory export."""

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import FieldNoteExtractionResponse, FieldNotesParserService
from app.config import settings
from app.core.exceptions import (
    PalustraDomainError,
    ReportGenerationError,
    TaxonNotFoundError,
)
from app.db.session import get_db
from app.etl.cache import field_cache
from app.etl.ingest import run_etl_pipeline
from app.export.models import GeoJSONExportRequest, PDFExportRequest
from app.models.db_models import Taxon
from app.models.schemas import (
    BatchPlotDeterminationRequest,
    FuzzySearchResponse,
    IngestionSummary,
    OfflineCacheManifest,
    PlotDeterminationInput,
    RegionEnum,
    TaxonRecord,
    TaxonValidationRequest,
    TaxonValidationResult,
)
from app.services.determination_service import (
    DeterminationService,
    DeterminationSynthesis,
)
from app.services.report_service import ReportService
from app.services.taxon_service import TaxonService

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
    taxon_service = TaxonService(session=db)
    return taxon_service.search_taxa(query=q, region=region, limit=limit, offset=offset)


@router.get("/taxa/{symbol}", response_model=TaxonRecord, tags=["Taxa Search"])
def get_taxon_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Retrieve full botanical taxon details by official USDA PLANTS symbol."""
    taxon_service = TaxonService(session=db)
    try:
        return taxon_service.get_by_symbol(symbol=symbol)
    except TaxonNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )


@router.post("/taxa/validate", response_model=TaxonValidationResult, tags=["Taxonomic Governance"])
def validate_field_taxon(
    request: TaxonValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate a field-recorded botanical name against USACE governance rules and USDA PLANTS."""
    taxon_service = TaxonService(session=db)
    try:
        return taxon_service.validate_field_taxon(request)
    except PalustraDomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )


@router.post(
    "/determinations/batch",
    response_model=List[DeterminationSynthesis],
    tags=["USACE Wetland Determinations"],
    summary="Batch evaluate USACE three-parameter jurisdictional wetland determinations",
)
def evaluate_batch_determinations(
    payload: Union[BatchPlotDeterminationRequest, List[PlotDeterminationInput]],
    region: Optional[str] = Query(None, description="Optional regional supplement override: EMP or AGCP"),
):
    """Evaluate multiple field plots in a high-throughput batch operation."""
    determination_service = DeterminationService()
    if isinstance(payload, BatchPlotDeterminationRequest):
        plots = payload.plots
        target_region = region or payload.region or "EMP"
    else:
        plots = payload
        target_region = region or (plots[0].region.value if plots and hasattr(plots[0], "region") and plots[0].region else "EMP")

    try:
        return determination_service.evaluate_batch(plots=plots, region=target_region)
    except PalustraDomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
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
    taxon_service = TaxonService(session=db)
    manifest = taxon_service.get_offline_bundle()
    bundle_dict = manifest.model_dump()

    # Compute deterministic ETag
    sample_taxa = bundle_dict.get("taxa", [])[:5]
    content_str = json.dumps(sample_taxa, sort_keys=True) + str(bundle_dict.get("total_taxa", 0))
    etag = f'W/"{hashlib.sha256(content_str.encode("utf-8")).hexdigest()[:16]}"'

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"

    return manifest


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
    """Asynchronously parse an uploaded photo of handwritten botanical field notes."""
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


@router.post(
    "/export/pdf",
    tags=["USACE Regulatory Export"],
    summary="Export official submission-ready 2-page USACE Data Form PDF",
)
def export_usace_pdf_endpoint(request: PDFExportRequest):
    """Generate official submission-ready two-page USACE Regional Supplement Data Form PDF."""
    report_service = ReportService()
    try:
        pdf_bytes = report_service.generate_plot_pdf(plot=request.plot, watermark=request.watermark)
        clean_id = request.plot.sampling_point.replace("/", "_").replace("\\", "_")
        filename = f"USACE_DataForm_{clean_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ReportGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"USACE PDF generation failed: {exc.message}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"USACE PDF generation failed: {str(exc)}",
        )


@router.post(
    "/export/geojson",
    tags=["USACE Regulatory Export"],
    summary="Export GIS RFC 7946 GeoJSON FeatureCollection for boundary mapping",
)
def export_boundary_geojson_endpoint(request: GeoJSONExportRequest):
    """Generate GIS GeoJSON point feature collections for wetland boundary mapping."""
    report_service = ReportService()
    try:
        return report_service.generate_boundary_geojson(
            plots=request.plots,
            include_transect_lines=request.include_transect_lines,
        )
    except ReportGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GeoJSON export failed: {exc.message}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GeoJSON export failed: {str(exc)}",
        )


@router.post(
    "/export/project-bundle",
    tags=["USACE Regulatory Export"],
    summary="Export project ZIP bundle with individual PDFs, consolidated report, and GIS GeoJSON",
)
def export_project_bundle_endpoint(
    request: GeoJSONExportRequest,
    project_name: Optional[str] = Query("Wetland_Project", description="Project name for filenames"),
    watermark: Optional[str] = Query(None, description="Optional watermark for PDFs"),
):
    """Generate a complete submission package ZIP containing PDFs and GIS boundary datasets."""
    report_service = ReportService()
    try:
        zip_bytes = report_service.generate_project_bundle_zip(
            plots=request.plots,
            project_name=project_name or "Wetland_Project",
            watermark=watermark,
            include_transect_lines=request.include_transect_lines,
        )
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{project_name}_package.zip"'},
        )
    except ReportGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project bundle export failed: {exc.message}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project bundle export failed: {str(exc)}",
        )
