"""Pydantic v2 schemas for botanical taxon validation and regulatory reporting."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class TaxonomicStatusEnum(str, Enum):
    ACCEPTED = "Accepted"
    SYNONYM = "Synonym"
    AMBIGUOUS = "Ambiguous"
    UNRESOLVED = "Unresolved"

class NativityEnum(str, Enum):
    NATIVE = "Native"
    INTRODUCED = "Introduced"
    CRYPTOGENIC = "Cryptogenic"
    UNKNOWN = "Unknown"

class IdentificationConfidenceEnum(str, Enum):
    DEFINITIVE = "Definitive"
    PROVISIONAL = "Provisional"  # cf.
    AFFINITY = "Affinity"        # aff.
    INDETERMINATE = "Indeterminate"  # sp. or sterile

class NWPLIndicatorEnum(str, Enum):
    OBL = "OBL"
    FACW = "FACW"
    FAC = "FAC"
    FACU = "FACU"
    UPL = "UPL"
    NL = "NL"

class RegionEnum(str, Enum):
    EMP = "EMP"
    AGCP = "AGCP"

class TaxonRecord(BaseModel):
    """Production-grade botanical taxon record conforming to regulatory standards."""

    model_config = ConfigDict(from_attributes=True)

    raw_field_name: str = Field(..., description="Exact text entered by field observer or source.")
    clean_scientific_name: str = Field(..., description="Normalized botanical name with authorities stripped.")
    accepted_scientific_name: str = Field(..., description="Current accepted scientific name per USDA PLANTS.")
    usda_plants_symbol: str = Field(..., min_length=1, max_length=20, description="Standard USDA PLANTS alphanumeric symbol.")
    common_name: Optional[str] = Field(None, description="Accepted English vernacular name.")
    family: Optional[str] = Field(None, description="Botanical plant family.")
    taxonomic_status: TaxonomicStatusEnum = Field(TaxonomicStatusEnum.ACCEPTED, description="Taxonomic acceptance state.")
    infraspecific_rank: Optional[str] = Field(None, description="subsp., var., or f.")
    infraspecific_epithet: Optional[str] = Field(None, description="Infraspecific epithet if applicable.")
    authority: Optional[str] = Field(None, description="Botanical authority citation.")
    nwpl_indicator_emp: Optional[NWPLIndicatorEnum] = Field(None, description="Eastern Mountains and Piedmont wetland rating.")
    nwpl_indicator_agcp: Optional[NWPLIndicatorEnum] = Field(None, description="Atlantic and Gulf Coastal Plain wetland rating.")
    c_value: Optional[int] = Field(None, ge=0, le=10, description="Coefficient of Conservatism (0-10).")
    nativity: NativityEnum = Field(NativityEnum.NATIVE, description="Nativity status.")
    identification_confidence: IdentificationConfidenceEnum = Field(
        IdentificationConfidenceEnum.DEFINITIVE,
        description="Identification confidence per regulatory guidelines."
    )
    flags: List[str] = Field(default_factory=list, description="Audit warnings and notes.")

    @model_validator(mode="after")
    def validate_nativity_c_value_consistency(self) -> "TaxonRecord":
        """Enforce: Introduced taxa must have c_value = 0; c_value >= 1 must be Native."""
        if self.nativity == NativityEnum.INTRODUCED and self.c_value is not None and self.c_value != 0:
            raise ValueError(f"Introduced species must have c_value=0, got {self.c_value}")
        if self.c_value is not None and self.c_value >= 1 and self.nativity == NativityEnum.INTRODUCED:
            raise ValueError(f"Species with c_value={self.c_value} cannot be classified as Introduced.")
        return self

class TaxonValidationRequest(BaseModel):
    """Request schema for validating field-collected plant names."""

    raw_name: str = Field(..., min_length=1, description="Raw plant name from field sheet or log.")
    region: Optional[RegionEnum] = Field(None, description="Target wetland region (EMP or AGCP) for indicator lookup.")
    stratum: Optional[str] = Field(None, description="Vegetation stratum: Tree, Sapling/Shrub, Herb, Woody Vine.")
    percent_cover: Optional[float] = Field(None, ge=0.0, le=100.0, description="Absolute percent cover in stratum.")

class TaxonValidationResult(BaseModel):
    """Detailed validation output including ambiguity governance and regulatory actions."""

    is_valid: bool = Field(..., description="Whether the record resolves to a recognized taxon or valid ambiguous taxon.")
    input_name: str = Field(..., description="Original input string.")
    parsed_clean_name: str = Field(..., description="Parsed binomial/trinomial.")
    confidence_level: IdentificationConfidenceEnum = Field(..., description="Definitive, Provisional, Affinity, or Indeterminate.")
    ambiguity_type: Optional[str] = Field(None, description="'genus_only', 'provisional_cf', 'affinity_aff', 'sterile', or None.")
    resolved_taxon: Optional[TaxonRecord] = Field(None, description="Matched database taxon if found.")
    recommended_indicator: Optional[str] = Field(None, description="Recommended NWPL indicator for dominance calculations.")
    usace_dominance_rule: str = Field(..., description="Explicit rule governing 50/20 dominance inclusion.")
    fqa_treatment_rule: str = Field(..., description="Explicit rule governing FQA Mean C & FQI inclusion.")
    warnings: List[str] = Field(default_factory=list, description="Taxonomic and regulatory warnings.")

class FuzzySearchQuery(BaseModel):
    """Parameters for SQLite FTS5 trigram fuzzy search."""

    query: str = Field(..., min_length=1, max_length=100, description="Search term (scientific name, common name, or symbol).")
    region: Optional[RegionEnum] = Field(None, description="Optional region filter for NWPL rating.")
    limit: int = Field(20, ge=1, le=100, description="Max results to return.")
    offset: int = Field(0, ge=0, description="Offset for pagination.")

class FuzzySearchResult(BaseModel):
    """Single fuzzy search hit ranked by BM25."""

    symbol: str
    clean_scientific_name: str
    common_name: Optional[str] = None
    family: Optional[str] = None
    nwpl_indicator_emp: Optional[str] = None
    nwpl_indicator_agcp: Optional[str] = None
    bm25_score: float = Field(..., description="SQLite FTS5 BM25 rank (lower is better in SQLite FTS5).")
    matched_field: str = Field("scientific_name", description="Field that triggered the match.")

class FuzzySearchResponse(BaseModel):
    """Paginated search response."""

    query: str
    total_results: int
    results: List[FuzzySearchResult]

class IngestionSummary(BaseModel):
    """Summary of ETL ingestion execution."""

    status: str
    usda_records_read: int
    agcp_records_read: int
    emp_records_read: int
    total_taxa_persisted: int
    total_indicators_persisted: int
    duration_seconds: float
    message: str

class OfflineCacheManifest(BaseModel):
    """Manifest for field cache synchronization."""

    version: str
    generated_at: str
    total_taxa: int
    taxa: List[TaxonRecord]
