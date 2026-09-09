"""Production Command Line Interface for Palustra ETL and Search Service."""

import argparse
import json
import sys
from pathlib import Path
import uvicorn

from palustra.config import settings
from palustra.db.fts import search_taxa
from palustra.db.session import get_db_context, init_db
from palustra.etl.cache import field_cache
from palustra.etl.ingest import run_etl_pipeline
from palustra.etl.parser import classify_field_ambiguity, parse_scientific_name
from palustra.models.db_models import Taxon
from sqlalchemy import select

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
    """Run SQLite FTS5 trigram search."""
    init_db()
    with get_db_context() as session:
        result = search_taxa(
            session,
            query_str=args.query,
            limit=args.limit,
            region=args.region,
        )
        print(f"\nSearch results for '{args.query}' (Total: {result['total']}):")
        if not result["results"]:
            print("  No matching taxa found.")
            return

        for i, hit in enumerate(result["results"], 1):
            emp = hit["nwpl_indicator_emp"] or "NL"
            agcp = hit["nwpl_indicator_agcp"] or "NL"
            comm = f" - '{hit['common_name']}'" if hit["common_name"] else ""
            print(
                f"  [{i}] {hit['symbol']} | {hit['clean_scientific_name']}{comm} | "
                f"EMP: {emp} | AGCP: {agcp} | BM25: {hit['bm25_score']:.3f}"
            )

def cmd_validate(args):
    """Validate a field plant name under USACE ambiguous taxa governance."""
    init_db()
    raw = args.name.strip()
    ambiguity = classify_field_ambiguity(raw)
    print(f"\nTaxon Validation for: '{raw}'")
    print(f"  - Ambiguity Type: {ambiguity['ambiguity_type'] or 'Definitive Identification'}")
    print(f"  - Confidence Level: {ambiguity['confidence_level']}")
    print(f"  - Cleaned Target Name: {ambiguity['cleaned_target_name']}")
    print(f"  - USACE 50/20 Rule: {ambiguity['usace_dominance_rule']}")
    print(f"  - FQA C-value Rule: {ambiguity['fqa_treatment_rule']}")

    with get_db_context() as session:
        parsed = parse_scientific_name(ambiguity["cleaned_target_name"])
        taxon = session.execute(
            select(Taxon).where(
                (Taxon.clean_scientific_name == parsed["clean_name"])
                | (Taxon.species_name == parsed["species_name"])
            ).limit(1)
        ).scalar_one_or_none()

        if taxon:
            print(f"\n  Matched Database Taxon:")
            print(f"    Symbol: {taxon.symbol}")
            print(f"    Scientific Name: {taxon.clean_scientific_name}")
            print(f"    Common Name: {taxon.common_name or 'N/A'}")
            print(f"    EMP Rating: {taxon.nwpl_indicator_emp or 'NL'}")
            print(f"    AGCP Rating: {taxon.nwpl_indicator_agcp or 'NL'}")
        else:
            print("\n  Taxon not found in current database.")

def cmd_cache_export(args):
    """Export local field offline snapshot."""
    init_db()
    output_path = Path(args.output) if args.output else settings.cache_dir / "field_offline_bundle.json"
    with get_db_context() as session:
        taxa = session.execute(select(Taxon).order_by(Taxon.symbol.asc())).scalars().all()
        data = {
            "version": "1.0.0",
            "total_taxa": len(taxa),
            "taxa": [
                {
                    "symbol": t.symbol,
                    "scientific_name": t.clean_scientific_name,
                    "common_name": t.common_name,
                    "nwpl_indicator_emp": t.nwpl_indicator_emp,
                    "nwpl_indicator_agcp": t.nwpl_indicator_agcp,
                }
                for t in taxa
            ],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Exported {len(taxa)} taxa to offline field cache snapshot: {output_path}")

def cmd_serve(args):
    """Launch FastAPI Uvicorn server."""
    print(f"Starting Palustra API server at http://{args.host}:{args.port}")
    uvicorn.run("palustra.api.app:app", host=args.host, port=args.port, reload=args.reload)

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
