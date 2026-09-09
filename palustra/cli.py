"""Production Command Line Interface for Palustra Service Layer."""

import argparse
import json
import sys
from pathlib import Path

import uvicorn

from palustra.config import settings
from palustra.core.exceptions import ReportGenerationError, TaxonNotFoundError
from palustra.db.session import init_db
from palustra.etl.ingest import run_etl_pipeline
from palustra.export.models import USACEPlotExportData
from palustra.models.schemas import RegionEnum, TaxonValidationRequest
from palustra.services.report_service import ReportService
from palustra.services.taxon_service import TaxonService


def cmd_ingest(args):
    """Run ETL pipeline."""
    print("Initiating Palustra ETL ingestion...")
    usda_path = Path(args.usda) if args.usda else None
    agcp_path = Path(args.agcp) if args.agcp else None
    emp_path = Path(args.emp) if args.emp else None

    summary = run_etl_pipeline(
        usda_path=usda_path,
        agcp_path=agcp_path,
        emp_path=emp_path,
        rebuild_fts=not args.skip_fts,
    )
    print(f"\nETL Ingestion Complete [{summary.status}]:")
    print(f"  - USDA records read: {summary.usda_records_read}")
    print(f"  - AGCP ratings loaded: {summary.agcp_records_read}")
    print(f"  - EMP ratings loaded: {summary.emp_records_read}")
    print(f"  - Total Taxa persisted: {summary.total_taxa_persisted}")
    print(f"  - Regional Indicators: {summary.total_indicators_persisted}")
    print(f"  - Duration: {summary.duration_seconds}s")


def cmd_search(args):
    """Run SQLite FTS5 trigram search via TaxonService."""
    init_db()
    service = TaxonService()
    reg = RegionEnum(args.region) if args.region else None
    response = service.search_taxa(
        query=args.query,
        region=reg,
        limit=args.limit,
    )
    print(f"\nSearch results for '{args.query}' (Total: {response.total_results}):")
    if not response.results:
        print("  No matching taxa found.")
        return

    for i, hit in enumerate(response.results, 1):
        emp = hit.nwpl_indicator_emp or "NL"
        agcp = hit.nwpl_indicator_agcp or "NL"
        comm = f" - '{hit.common_name}'" if hit.common_name else ""
        print(
            f"  [{i}] {hit.symbol} | {hit.clean_scientific_name}{comm} | "
            f"EMP: {emp} | AGCP: {agcp} | BM25: {hit.bm25_score:.3f}"
        )


def cmd_validate(args):
    """Validate a field plant name under USACE ambiguous taxa governance via TaxonService."""
    init_db()
    service = TaxonService()
    raw = args.name.strip()
    request = TaxonValidationRequest(raw_name=raw)
    result = service.validate_field_taxon(request)

    print(f"\nTaxon Validation for: '{raw}'")
    print(f"  - Ambiguity Type: {result.ambiguity_type or 'Definitive Identification'}")
    print(f"  - Confidence Level: {result.confidence_level.value}")
    print(f"  - Cleaned Target Name: {result.parsed_clean_name}")
    print(f"  - USACE 50/20 Rule: {result.usace_dominance_rule}")
    print(f"  - FQA C-value Rule: {result.fqa_treatment_rule}")

    if result.resolved_taxon:
        t = result.resolved_taxon
        print("\n  Matched Database Taxon:")
        print(f"    Symbol: {t.usda_plants_symbol}")
        print(f"    Scientific Name: {t.clean_scientific_name}")
        print(f"    Common Name: {t.common_name or 'N/A'}")
        print(f"    EMP Rating: {t.nwpl_indicator_emp.value if t.nwpl_indicator_emp else 'NL'}")
        print(f"    AGCP Rating: {t.nwpl_indicator_agcp.value if t.nwpl_indicator_agcp else 'NL'}")
    else:
        print("\n  Taxon not found in current database.")


def cmd_cache_export(args):
    """Export local field offline snapshot via TaxonService."""
    init_db()
    service = TaxonService()
    output_path = Path(args.output) if args.output else settings.cache_dir / "field_offline_bundle.json"
    manifest = service.get_offline_bundle()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2, default=str)
    print(f"Exported {manifest.total_taxa} taxa to offline field cache snapshot: {output_path}")


def cmd_serve(args):
    """Launch FastAPI Uvicorn server."""
    print(f"Starting Palustra API server at http://{args.host}:{args.port}")
    uvicorn.run("palustra.api.app:app", host=args.host, port=args.port, reload=args.reload)


def cmd_export_pdf(args):
    """Export USACE two-page form PDF via ReportService."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plot = USACEPlotExportData(**data)
    service = ReportService()
    try:
        pdf_bytes = service.generate_plot_pdf(plot, watermark=args.watermark)
    except ReportGenerationError as err:
        print(f"Error: {err.message}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else Path(f"USACE_DataForm_{plot.sampling_point}.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Exported USACE 2-page Data Form PDF to: {out_path} ({len(pdf_bytes)} bytes)")


def cmd_export_geojson(args):
    """Export GIS GeoJSON FeatureCollection via ReportService."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        plots = [USACEPlotExportData(**p) for p in data]
    else:
        plots = [USACEPlotExportData(**data)]

    service = ReportService()
    try:
        geojson_data = service.generate_boundary_geojson(
            plots=plots,
            include_transect_lines=not args.no_transects,
        )
    except ReportGenerationError as err:
        print(f"Error: {err.message}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else Path("boundary_points.geojson")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)
    print(f"Exported {len(geojson_data['features'])} features to GeoJSON: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Palustra Botanical Data Engineering Service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest command
    p_ingest = subparsers.add_parser("ingest", help="Run ETL pipeline for USDA PLANTS and NWPL")
    p_ingest.add_argument("--usda", help="Path to USDA PLANTS CSV")
    p_ingest.add_argument("--agcp", help="Path to NWPL AGCP XLSX")
    p_ingest.add_argument("--emp", help="Path to NWPL EMP XLSX")
    p_ingest.add_argument("--skip-fts", action="store_true", help="Skip rebuilding FTS5 trigram index")
    p_ingest.set_defaults(func=cmd_ingest)

    # Search command
    p_search = subparsers.add_parser("search", help="FTS5 trigram search for plant name or symbol")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--region", choices=["EMP", "AGCP"], help="Filter by wetland region")
    p_search.add_argument("--limit", type=int, default=10, help="Max results")
    p_search.set_defaults(func=cmd_search)

    # Validate command
    p_validate = subparsers.add_parser("validate", help="Validate plant name under USACE ambiguous rules")
    p_validate.add_argument("name", help="Raw plant name (e.g. 'Carex cf. lurida', 'Typha sp.')")
    p_validate.set_defaults(func=cmd_validate)

    # Cache export command
    p_cache = subparsers.add_parser("cache-export", help="Export offline field cache snapshot")
    p_cache.add_argument("--output", help="Output path for JSON bundle")
    p_cache.set_defaults(func=cmd_cache_export)

    # Export PDF command
    p_pdf = subparsers.add_parser("export-pdf", help="Export official submission-ready 2-page USACE PDF")
    p_pdf.add_argument("--input", required=True, help="Path to JSON file containing plot data")
    p_pdf.add_argument("--output", help="Output path for generated PDF")
    p_pdf.add_argument("--watermark", help="Optional watermark text")
    p_pdf.set_defaults(func=cmd_export_pdf)

    # Export GeoJSON command
    p_geojson = subparsers.add_parser("export-geojson", help="Export RFC 7946 GIS GeoJSON for boundary mapping")
    p_geojson.add_argument("--input", required=True, help="Path to JSON file containing plot or list of plots")
    p_geojson.add_argument("--output", help="Output path for GeoJSON")
    p_geojson.add_argument("--no-transects", action="store_true", help="Disable generating transect boundary lines")
    p_geojson.set_defaults(func=cmd_export_geojson)

    # Serve command
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI web service")
    p_serve.add_argument("--host", default=settings.api_host, help="Host address")
    p_serve.add_argument("--port", type=int, default=settings.api_port, help="Port number")
    p_serve.add_argument("--reload", action="store_true", help="Auto-reload on code change")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
