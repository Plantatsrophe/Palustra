"""Production-grade ETL pipeline ingesting USDA PLANTS and USACE NWPL datasets."""

import csv
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import openpyxl
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from palustra.config import settings
from palustra.db.fts import rebuild_fts5
from palustra.db.session import get_db_context, init_db
from palustra.etl.cache import field_cache
from palustra.etl.parser import clean_text, parse_scientific_name
from palustra.models.db_models import IngestionLog, RegionalIndicator, Taxon
from palustra.models.schemas import IngestionSummary

logger = logging.getLogger("palustra.etl")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def load_nwpl_excel(file_path: Path, region_column_name: str) -> Dict[str, str]:
    """Read USACE NWPL Excel workbook and return scientific_name -> indicator_status dict."""
    if not file_path.exists():
        raise FileNotFoundError(f"NWPL file not found at: {file_path}")

    logger.info(f"Loading NWPL data from {file_path.name}...")
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb.active
    rows = iter(sheet.iter_rows(values_only=True))
    
    header = next(rows, None)
    if not header:
        raise ValueError(f"NWPL file {file_path.name} is empty.")

    # Clean headers and locate columns
    cleaned_headers = [clean_text(str(col)) if col is not None else "" for col in header]
    
    sci_name_idx = -1
    status_idx = -1
    
    for i, col in enumerate(cleaned_headers):
        if "scientific name" in col.lower():
            sci_name_idx = i
        elif region_column_name.lower() in col.lower():
            status_idx = i

    if sci_name_idx == -1 or status_idx == -1:
        raise ValueError(
            f"Could not locate required columns in {file_path.name}. Found headers: {cleaned_headers}"
        )

    nwpl_data: Dict[str, str] = {}
    valid_statuses = {"OBL", "FACW", "FAC", "FACU", "UPL", "NL"}

    for row in rows:
        if not row or len(row) <= max(sci_name_idx, status_idx):
            continue
        raw_sci = row[sci_name_idx]
        raw_status = row[status_idx]
        if not raw_sci or not raw_status:
            continue
        sci_name = clean_text(str(raw_sci))
        status = clean_text(str(raw_status)).upper()
        if status in valid_statuses:
            nwpl_data[sci_name] = status

    logger.info(f"Loaded {len(nwpl_data)} valid ratings from {file_path.name}")
    return nwpl_data

def load_usda_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Read USDA PLANTS CSV, parsing botanical names and authority citations."""
    if not file_path.exists():
        raise FileNotFoundError(f"USDA PLANTS CSV not found at: {file_path}")

    logger.info(f"Loading USDA PLANTS data from {file_path.name}...")
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        first_row = next(reader, None)
        # Check if first row is metadata header
        if first_row and len(first_row) == 1 and "Search type:" in first_row[0]:
            header_row = next(reader, None)
        else:
            header_row = first_row

        if not header_row:
            raise ValueError(f"USDA file {file_path.name} is empty.")

        cleaned_headers = [clean_text(col).lower() for col in header_row]
        symbol_idx = cleaned_headers.index("accepted symbol") if "accepted symbol" in cleaned_headers else 0
        sci_name_idx = cleaned_headers.index("scientific name") if "scientific name" in cleaned_headers else 2
        common_name_idx = cleaned_headers.index("common name") if "common name" in cleaned_headers else 3

        taxa_list: List[Dict[str, Any]] = []
        seen_symbols = set()

        for row in reader:
            if not row or len(row) <= max(symbol_idx, sci_name_idx):
                continue
            raw_symbol = clean_text(row[symbol_idx]).upper()
            raw_sci = clean_text(row[sci_name_idx])
            if not raw_symbol or not raw_sci:
                continue

            if raw_symbol in seen_symbols:
                continue
            seen_symbols.add(raw_symbol)

            common_name = None
            if len(row) > common_name_idx and row[common_name_idx]:
                cleaned_comm = clean_text(row[common_name_idx])
                if cleaned_comm:
                    common_name = cleaned_comm

            parsed = parse_scientific_name(raw_sci)
            taxa_list.append({
                "symbol": raw_symbol,
                "raw_scientific_name": raw_sci,
                "clean_scientific_name": parsed["clean_name"],
                "species_name": parsed["species_name"],
                "genus": parsed["genus"],
                "species_epithet": parsed["species_epithet"],
                "infraspecific_rank": parsed["infraspecific_rank"],
                "infraspecific_epithet": parsed["infraspecific_epithet"],
                "authority": parsed["authority"],
                "common_name": common_name,
                "hybrid_parentage": parsed["hybrid_parentage"],
            })

    logger.info(f"Loaded {len(taxa_list)} parsed taxa from {file_path.name}")
    return taxa_list

def resolve_regional_indicator(
    clean_scientific_name: str,
    species_name: str,
    nwpl_lookup: Dict[str, str],
) -> Tuple[Optional[str], Optional[str], str]:
    """Resolve indicator status with direct match or species-level fallback.
    
    Returns: (status, source_scientific_name, matched_level)
    """
    # 1. Direct match on clean scientific name
    if clean_scientific_name in nwpl_lookup:
        return nwpl_lookup[clean_scientific_name], clean_scientific_name, "direct"

    # 2. Species-level fallback for infraspecific varieties/subspecies
    if species_name in nwpl_lookup:
        return nwpl_lookup[species_name], species_name, "species_fallback"

    return None, None, "unmatched"

def run_etl_pipeline(
    db_session: Optional[Session] = None,
    usda_path: Optional[Path] = None,
    agcp_path: Optional[Path] = None,
    emp_path: Optional[Path] = None,
    rebuild_fts: bool = True,
) -> IngestionSummary:
    """Execute complete end-to-end ingestion and database synchronization."""
    start_time = time.time()
    usda_file = usda_path or settings.usda_plants_path
    agcp_file = agcp_path or settings.nwpl_agcp_path
    emp_file = emp_path or settings.nwpl_emp_path

    logger.info("Starting Palustra USACE NWPL & USDA PLANTS ETL Pipeline...")

    # Load source datasets
    usda_records = load_usda_csv(usda_file)
    agcp_lookup = load_nwpl_excel(agcp_file, "AGCP")
    emp_lookup = load_nwpl_excel(emp_file, "EMP")

    # Ensure tables exist
    init_db()

    def _execute_ingestion(session: Session) -> IngestionSummary:
        log_entry = IngestionLog(
            source="USDA_PLANTS_NWPL_2022",
            records_read=len(usda_records),
            status="IN_PROGRESS",
        )
        session.add(log_entry)
        session.flush()

        # Clear existing records for clean idempotent reload
        session.execute(delete(RegionalIndicator))
        session.execute(delete(Taxon))
        session.flush()

        taxa_to_insert: List[Taxon] = []
        indicators_to_insert: List[RegionalIndicator] = []

        for record in usda_records:
            clean_name = record["clean_scientific_name"]
            species_name = record["species_name"]

            # Resolve EMP status
            emp_status, emp_source, emp_level = resolve_regional_indicator(
                clean_name, species_name, emp_lookup
            )
            # Resolve AGCP status
            agcp_status, agcp_source, agcp_level = resolve_regional_indicator(
                clean_name, species_name, agcp_lookup
            )

            taxon = Taxon(
                symbol=record["symbol"],
                raw_scientific_name=record["raw_scientific_name"],
                clean_scientific_name=clean_name,
                species_name=species_name,
                genus=record["genus"],
                species_epithet=record["species_epithet"],
                infraspecific_rank=record["infraspecific_rank"],
                infraspecific_epithet=record["infraspecific_epithet"],
                authority=record["authority"],
                common_name=record["common_name"],
                family=None,
                taxonomic_status="Accepted",
                nativity="Native",
                c_value=None,
                hybrid_parentage=record["hybrid_parentage"],
                nwpl_indicator_emp=emp_status,
                nwpl_indicator_agcp=agcp_status,
            )
            taxa_to_insert.append(taxon)

        session.add_all(taxa_to_insert)
        session.flush()

        # Build detailed regional indicators linked to persisted taxon ids
        for taxon in taxa_to_insert:
            clean_name = taxon.clean_scientific_name
            species_name = taxon.species_name

            if taxon.nwpl_indicator_emp:
                _, emp_source, emp_level = resolve_regional_indicator(clean_name, species_name, emp_lookup)
                indicators_to_insert.append(
                    RegionalIndicator(
                        taxon_id=taxon.id,
                        region="EMP",
                        indicator_status=taxon.nwpl_indicator_emp,
                        source_scientific_name=emp_source,
                        matched_level=emp_level,
                    )
                )
            if taxon.nwpl_indicator_agcp:
                _, agcp_source, agcp_level = resolve_regional_indicator(clean_name, species_name, agcp_lookup)
                indicators_to_insert.append(
                    RegionalIndicator(
                        taxon_id=taxon.id,
                        region="AGCP",
                        indicator_status=taxon.nwpl_indicator_agcp,
                        source_scientific_name=agcp_source,
                        matched_level=agcp_level,
                    )
                )

        session.add_all(indicators_to_insert)
        session.flush()

        # Rebuild FTS5 trigram index
        if rebuild_fts:
            logger.info("Rebuilding SQLite FTS5 trigram virtual table...")
            rebuild_fts5(session.connection())

        elapsed = round(time.time() - start_time, 2)
        log_entry.records_inserted = len(taxa_to_insert)
        log_entry.status = "SUCCESS"
        log_entry.completed_at = datetime.now(timezone.utc)
        log_entry.message = (
            f"Successfully ingested {len(taxa_to_insert)} taxa and "
            f"{len(indicators_to_insert)} regional indicators in {elapsed}s"
        )
        session.commit()

        # Invalidate field cache after fresh ingestion
        field_cache.invalidate()

        logger.info(log_entry.message)
        return IngestionSummary(
            status="SUCCESS",
            usda_records_read=len(usda_records),
            agcp_records_read=len(agcp_lookup),
            emp_records_read=len(emp_lookup),
            total_taxa_persisted=len(taxa_to_insert),
            total_indicators_persisted=len(indicators_to_insert),
            duration_seconds=elapsed,
            message=log_entry.message,
        )

    if db_session:
        return _execute_ingestion(db_session)
    else:
        with get_db_context() as session:
            return _execute_ingestion(session)
