"""Taxonomic service encapsulating SQLite FTS5 search, synonym normalization, and rarity governance."""

import json
import logging
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AmbiguousTaxonWarning, TaxonNotFoundError
from app.db.fts import search_taxa as fts_search_taxa
from app.db.session import get_db_context
from app.etl.cache import field_cache
from app.etl.parser import classify_field_ambiguity, parse_scientific_name
from app.models.db_models import Taxon
from app.models.schemas import (
    FuzzySearchQuery,
    FuzzySearchResponse,
    FuzzySearchResult,
    IdentificationConfidenceEnum,
    NativityEnum,
    NWPLIndicatorEnum,
    OfflineCacheManifest,
    RegionEnum,
    TaxonomicStatusEnum,
    TaxonRecord,
    TaxonValidationRequest,
    TaxonValidationResult,
)

logger = logging.getLogger("app.services.taxon")

# Common North Carolina & Southeastern botanical synonyms mapped to accepted USDA scientific names
BOTANICAL_SYNONYMS: Dict[str, str] = {
    "Aster dumosus": "Symphyotrichum dumosum",
    "Aster lateriflorus": "Symphyotrichum lateriflorum",
    "Aster pilosus": "Symphyotrichum pilosum",
    "Eupatorium dubium": "Eutrochium dubium",
    "Eupatorium fistulosum": "Eutrochium fistulosum",
    "Eupatorium purpureum": "Eutrochium purpureum",
    "Panicum scoparium": "Dichanthelium scoparium",
    "Panicum clandestinum": "Dichanthelium clandestinum",
    "Panicum dichotomum": "Dichanthelium dichotomum",
    "Scirpus cyperinus": "Scirpus cyperinus",
    "Scirpus validus": "Schoenoplectus tabernaemontani",
    "Alnus rugosa": "Alnus incana subsp. rugosa",
}

# State Heritage Rarity Ranks for exemplary rare wetland taxa in North Carolina (EMP/AGCP)
STATE_HERITAGE_REGISTRY: Dict[str, Dict[str, str]] = {
    "Helonias bullata": {"rank": "S2", "status": "Threatened", "tier": "High Conservation Concern"},
    "Sagittaria fasciculata": {"rank": "S1", "status": "Endangered", "tier": "High Conservation Concern"},
    "Carex impressa": {"rank": "S1", "status": "Endangered", "tier": "High Conservation Concern"},
    "Carex barrattii": {"rank": "S2", "status": "Significantly Rare", "tier": "High Conservation Concern"},
    "Parnassia grandifolia": {"rank": "S2", "status": "Significantly Rare", "tier": "High Conservation Concern"},
    "Rhynchospora knieskernii": {"rank": "S1", "status": "Endangered", "tier": "High Conservation Concern"},
    "Oxypolis canbyi": {"rank": "S1", "status": "Endangered", "tier": "High Conservation Concern"},
    "Lindera subcoriacea": {"rank": "S2", "status": "Threatened", "tier": "High Conservation Concern"},
}


@lru_cache(maxsize=4096)
def normalize_botanical_query(raw_query: str) -> str:
    """Normalize raw botanical query string for consistent cache key resolution."""
    return " ".join(raw_query.strip().lower().split())


@lru_cache(maxsize=1024)
def resolve_scientific_name(raw_name: str) -> Dict[str, Any]:
    """Parse and standardize raw botanical text with an in-memory LRU cache.

    Strips author citations, standardizes infraspecific designations (subsp., var., f.),
    and extracts genus and species epithets.
    """
    return parse_scientific_name(raw_name)


@lru_cache(maxsize=4096)
def _cached_db_taxon_lookup(name_key: str) -> Optional[Dict[str, Any]]:
    """Cached database lookup by normalized clean or species name."""
    with get_db_context() as session:
        taxon = session.execute(
            select(Taxon).where(
                (Taxon.clean_scientific_name == name_key)
                | (Taxon.species_name == name_key)
            ).limit(1)
        ).scalar_one_or_none()

        if not taxon:
            return None

        return {
            "id": taxon.id,
            "symbol": taxon.symbol,
            "raw_scientific_name": taxon.raw_scientific_name,
            "clean_scientific_name": taxon.clean_scientific_name,
            "species_name": taxon.species_name,
            "genus": taxon.genus,
            "species_epithet": taxon.species_epithet,
            "infraspecific_rank": taxon.infraspecific_rank,
            "infraspecific_epithet": taxon.infraspecific_epithet,
            "authority": taxon.authority,
            "common_name": taxon.common_name,
            "family": taxon.family,
            "taxonomic_status": taxon.taxonomic_status,
            "nativity": taxon.nativity,
            "c_value": taxon.c_value,
            "nwpl_indicator_emp": taxon.nwpl_indicator_emp,
            "nwpl_indicator_agcp": taxon.nwpl_indicator_agcp,
        }


@lru_cache(maxsize=2048)
def _cached_db_symbol_lookup(symbol: str) -> Optional[Dict[str, Any]]:
    """Cached database lookup by normalized USDA PLANTS symbol."""
    with get_db_context() as session:
        taxon = session.execute(
            select(Taxon).where(Taxon.symbol == symbol)
        ).scalar_one_or_none()

        if not taxon:
            return None

        return {
            "id": taxon.id,
            "symbol": taxon.symbol,
            "raw_scientific_name": taxon.raw_scientific_name,
            "clean_scientific_name": taxon.clean_scientific_name,
            "species_name": taxon.species_name,
            "genus": taxon.genus,
            "species_epithet": taxon.species_epithet,
            "infraspecific_rank": taxon.infraspecific_rank,
            "infraspecific_epithet": taxon.infraspecific_epithet,
            "authority": taxon.authority,
            "common_name": taxon.common_name,
            "family": taxon.family,
            "taxonomic_status": taxon.taxonomic_status,
            "nativity": taxon.nativity,
            "c_value": taxon.c_value,
            "nwpl_indicator_emp": taxon.nwpl_indicator_emp,
            "nwpl_indicator_agcp": taxon.nwpl_indicator_agcp,
        }


@lru_cache(maxsize=4096)
def _cached_fts_search(
    norm_query: str,
    region: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Execute SQLite FTS5 trigram fuzzy search with in-memory LRU memoization."""
    with get_db_context() as session:
        return fts_search_taxa(
            session=session,
            query_str=norm_query,
            limit=limit,
            offset=offset,
            region=region,
        )


class TaxonService:
    """Decoupled service handling botanical taxonomy, full-text search, and validation."""

    def __init__(self, session: Optional[Session] = None) -> None:
        """Initialize the taxon service with an optional database session.

        Args:
            session: Optional active SQLAlchemy session. If omitted, methods
                     will utilize the transactional get_db_context() context manager.
        """
        self._session = session

    @contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """Provide an active session, yielding the injected session or a new context session."""
        if self._session is not None:
            yield self._session
        else:
            with get_db_context() as session:
                yield session

    def search_taxa(
        self,
        query: str,
        region: Optional[RegionEnum] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> FuzzySearchResponse:
        """Execute SQLite FTS5 trigram fuzzy search for plant scientific and common names.

        Employs normalized LRU memoization and field_cache to minimize FTS5 database hits.
        """
        norm_query = normalize_botanical_query(query)
        if not norm_query:
            return FuzzySearchResponse(query=query, total_results=0, results=[])

        reg_val = region.value if isinstance(region, RegionEnum) else (str(region).upper() if region else None)
        cache_key = field_cache._generate_key("search", q=norm_query, region=reg_val, limit=limit, offset=offset)
        cached_data = field_cache.get(cache_key)
        if cached_data:
            return FuzzySearchResponse(**cached_data)

        # Check in-memory LRU cache on normalized query
        search_data = None
        if self._session is None:
            search_data = _cached_fts_search(
                norm_query=norm_query,
                region=reg_val,
                limit=limit,
                offset=offset,
            )
        else:
            search_data = fts_search_taxa(
                session=self._session,
                query_str=norm_query,
                limit=limit,
                offset=offset,
                region=reg_val,
            )

        response_payload = {
            "query": query,
            "total_results": search_data["total"],
            "results": [FuzzySearchResult(**r) for r in search_data["results"]],
        }
        field_cache.set(cache_key, response_payload)
        return FuzzySearchResponse(**response_payload)

    def search_taxa_by_query(self, query_obj: FuzzySearchQuery) -> FuzzySearchResponse:
        """Execute FTS5 search using a FuzzySearchQuery Pydantic model."""
        return self.search_taxa(
            query=query_obj.query,
            region=query_obj.region,
            limit=query_obj.limit,
            offset=query_obj.offset,
        )

    def get_by_symbol(self, symbol: str) -> TaxonRecord:
        """Retrieve full botanical taxon details by official USDA PLANTS symbol.

        Raises:
            TaxonNotFoundError: If the symbol does not exist in the database.
        """
        norm_symbol = symbol.strip().upper()
        cache_key = f"taxon:symbol:{norm_symbol}"
        cached = field_cache.get(cache_key)
        if cached:
            return TaxonRecord(**cached)

        taxon_dict = None
        if self._session is not None:
            taxon = self._session.execute(
                select(Taxon).where(Taxon.symbol == norm_symbol)
            ).scalar_one_or_none()
            if taxon:
                taxon_dict = {
                    "raw_scientific_name": taxon.raw_scientific_name,
                    "clean_scientific_name": taxon.clean_scientific_name,
                    "species_name": taxon.species_name,
                    "symbol": taxon.symbol,
                    "common_name": taxon.common_name,
                    "family": taxon.family,
                    "taxonomic_status": taxon.taxonomic_status,
                    "infraspecific_rank": taxon.infraspecific_rank,
                    "infraspecific_epithet": taxon.infraspecific_epithet,
                    "authority": taxon.authority,
                    "nwpl_indicator_emp": taxon.nwpl_indicator_emp,
                    "nwpl_indicator_agcp": taxon.nwpl_indicator_agcp,
                    "c_value": taxon.c_value,
                    "nativity": taxon.nativity,
                }
        else:
            taxon_dict = _cached_db_symbol_lookup(norm_symbol)

        if not taxon_dict:
            raise TaxonNotFoundError(
                identifier=norm_symbol,
                message=f"Taxon with USDA symbol '{norm_symbol}' not found in database.",
            )

        record = TaxonRecord(
            raw_field_name=taxon_dict["raw_scientific_name"],
            clean_scientific_name=taxon_dict["clean_scientific_name"],
            accepted_scientific_name=taxon_dict["species_name"],
            usda_plants_symbol=taxon_dict["symbol"],
            common_name=taxon_dict["common_name"],
            family=taxon_dict["family"],
            taxonomic_status=taxon_dict["taxonomic_status"],
            infraspecific_rank=taxon_dict["infraspecific_rank"],
            infraspecific_epithet=taxon_dict["infraspecific_epithet"],
            authority=taxon_dict["authority"],
            nwpl_indicator_emp=taxon_dict["nwpl_indicator_emp"],
            nwpl_indicator_agcp=taxon_dict["nwpl_indicator_agcp"],
            c_value=taxon_dict["c_value"],
            nativity=taxon_dict["nativity"],
            identification_confidence=IdentificationConfidenceEnum.DEFINITIVE,
            flags=[],
        )

        field_cache.set(cache_key, record.model_dump())
        return record

    def normalize_synonym(self, scientific_name: str) -> str:
        """Normalize obsolete or historical botanical synonyms to accepted USDA names."""
        clean_name = scientific_name.strip()
        return BOTANICAL_SYNONYMS.get(clean_name, clean_name)

    def lookup_state_heritage_rarity(
        self,
        name_or_symbol: str,
        state: str = "NC",
        c_value: Optional[int] = None,
        nativity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Look up or evaluate State Natural Heritage rarity ranking and conservation tier."""
        clean_name = name_or_symbol.strip()
        if clean_name in STATE_HERITAGE_REGISTRY:
            reg = STATE_HERITAGE_REGISTRY[clean_name]
            return {
                "state": state,
                "state_rank": reg["rank"],
                "state_status": reg["status"],
                "conservation_tier": reg["tier"],
                "is_rare": True,
                "remarks": f"Tracked by {state} Natural Heritage Program as {reg['status']} ({reg['rank']}).",
            }

        # Conservatism-based ecological rarity inference
        if nativity == "Introduced" or c_value == 0:
            return {
                "state": state,
                "state_rank": "SNA",
                "state_status": "Not Listed",
                "conservation_tier": "Exotic / Introduced",
                "is_rare": False,
                "remarks": "Non-native adventive/introduced species.",
            }
        elif c_value is not None and c_value >= 9:
            return {
                "state": state,
                "state_rank": "S1/S2",
                "state_status": "High Conservation Concern",
                "conservation_tier": "Extreme Ecological Specialist",
                "is_rare": True,
                "remarks": f"C-value {c_value} denotes pristine natural remnant specialist.",
            }
        elif c_value is not None and c_value >= 7:
            return {
                "state": state,
                "state_rank": "S3",
                "state_status": "Watch List / Sensitive",
                "conservation_tier": "High Ecological Fidelity",
                "is_rare": False,
                "remarks": f"C-value {c_value} denotes high fidelity to mature wetland communities.",
            }
        else:
            return {
                "state": state,
                "state_rank": "S5",
                "state_status": "Secure",
                "conservation_tier": "Common / Matrix Species",
                "is_rare": False,
                "remarks": "Common, secure native or ruderal taxon.",
            }

    def validate_field_taxon(self, request: TaxonValidationRequest) -> TaxonValidationResult:
        """Validate a field-recorded botanical name against USACE governance rules and USDA PLANTS."""
        raw_name = request.raw_name.strip()
        ambiguity = classify_field_ambiguity(raw_name)

        ambiguity_type = ambiguity["ambiguity_type"]
        target_clean = ambiguity["cleaned_target_name"]
        confidence = IdentificationConfidenceEnum(ambiguity["confidence_level"])
        warnings_list: List[str] = list(ambiguity["warnings"])

        if ambiguity_type is not None:
            warnings.warn(
                AmbiguousTaxonWarning(raw_name=raw_name, ambiguity_type=ambiguity_type),
                stacklevel=2,
            )

        # Check botanical synonym mapping
        normalized_name = self.normalize_synonym(target_clean)
        if normalized_name != target_clean:
            warnings_list.append(f"SYNONYM_RESOLVED: '{target_clean}' resolved to accepted '{normalized_name}'.")
            target_clean = normalized_name

        resolved_taxon_record: Optional[TaxonRecord] = None
        recommended_indicator: Optional[str] = None

        if ambiguity_type in ("provisional_cf", "affinity_aff", None):
            parsed = resolve_scientific_name(target_clean)
            target_clean_name = parsed["clean_name"]
            species_name = parsed["species_name"]

            # Query database for taxon record
            cached_data = _cached_db_taxon_lookup(target_clean_name) or _cached_db_taxon_lookup(species_name)

            taxon = None
            if not cached_data and self._session is not None:
                taxon = self._session.execute(
                    select(Taxon).where(
                        (Taxon.clean_scientific_name == target_clean_name)
                        | (Taxon.species_name == species_name)
                    ).limit(1)
                ).scalar_one_or_none()

            if cached_data or taxon:
                t_raw = cached_data["raw_scientific_name"] if cached_data else taxon.raw_scientific_name
                t_clean = cached_data["clean_scientific_name"] if cached_data else taxon.clean_scientific_name
                t_species = cached_data["species_name"] if cached_data else taxon.species_name
                t_symbol = cached_data["symbol"] if cached_data else taxon.symbol
                t_comm = cached_data["common_name"] if cached_data else taxon.common_name
                t_fam = cached_data["family"] if cached_data else taxon.family
                t_status = cached_data["taxonomic_status"] if cached_data else taxon.taxonomic_status
                t_rank = cached_data["infraspecific_rank"] if cached_data else taxon.infraspecific_rank
                t_epith = cached_data["infraspecific_epithet"] if cached_data else taxon.infraspecific_epithet
                t_auth = cached_data["authority"] if cached_data else taxon.authority
                t_emp = cached_data["nwpl_indicator_emp"] if cached_data else taxon.nwpl_indicator_emp
                t_agcp = cached_data["nwpl_indicator_agcp"] if cached_data else taxon.nwpl_indicator_agcp
                t_cval = cached_data["c_value"] if cached_data else taxon.c_value
                t_nat = cached_data["nativity"] if cached_data else taxon.nativity

                # Heritage rarity lookup
                rarity = self.lookup_state_heritage_rarity(
                    name_or_symbol=t_clean,
                    c_value=t_cval,
                    nativity=t_nat,
                )
                if rarity["is_rare"]:
                    warnings_list.append(f"STATE_HERITAGE_ALERT: {rarity['remarks']}")

                resolved_taxon_record = TaxonRecord(
                    raw_field_name=t_raw,
                    clean_scientific_name=t_clean,
                    accepted_scientific_name=t_species,
                    usda_plants_symbol=t_symbol,
                    common_name=t_comm,
                    family=t_fam,
                    taxonomic_status=t_status,
                    infraspecific_rank=t_rank,
                    infraspecific_epithet=t_epith,
                    authority=t_auth,
                    nwpl_indicator_emp=t_emp,
                    nwpl_indicator_agcp=t_agcp,
                    c_value=t_cval,
                    nativity=t_nat,
                    identification_confidence=confidence,
                    flags=warnings_list,
                )

                if request.region == RegionEnum.EMP:
                    recommended_indicator = t_emp
                elif request.region == RegionEnum.AGCP:
                    recommended_indicator = t_agcp
            else:
                warnings_list.append(f"NAME_NOT_FOUND: '{target_clean}' does not match any accepted USDA taxon.")

        elif ambiguity_type == "genus_only":
            if ambiguity.get("is_homogeneous"):
                homo_status = ambiguity.get("homogeneous_status", {})
                if request.region == RegionEnum.EMP:
                    recommended_indicator = homo_status.get("EMP")
                elif request.region == RegionEnum.AGCP:
                    recommended_indicator = homo_status.get("AGCP")
            else:
                recommended_indicator = None

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
            warnings=warnings_list,
        )

    def get_offline_bundle(self) -> OfflineCacheManifest:
        """Fetch or generate complete offline botanical cache bundle for field PWA sync."""
        cached_bundle = field_cache.load_offline_snapshot("field_offline_bundle.json")
        if not cached_bundle:
            with self._get_session() as session:
                taxa = session.execute(select(Taxon).order_by(Taxon.symbol.asc())).scalars().all()
                records: List[Dict[str, Any]] = []
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

        return OfflineCacheManifest(**cached_bundle)

    @classmethod
    def clear_caches(cls) -> None:
        """Clear all in-memory LRU caches."""
        normalize_botanical_query.cache_clear()
        resolve_scientific_name.cache_clear()
        _cached_db_taxon_lookup.cache_clear()
        _cached_db_symbol_lookup.cache_clear()
        _cached_fts_search.cache_clear()
        field_cache.invalidate()
