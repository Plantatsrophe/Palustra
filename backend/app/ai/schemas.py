"""Pydantic v2 schemas for Gemini 1.5 Flash handwritten botanical field note extraction."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfidenceFlagReasonEnum(str, Enum):
    """Standard diagnostic codes for low-confidence or ambiguous botanical extractions."""

    LOW_CONFIDENCE_SCORE = "LOW_CONFIDENCE_SCORE"
    AMBIGUOUS_TAXON_SP = "AMBIGUOUS_TAXON_SP"
    AMBIGUOUS_TAXON_CF = "AMBIGUOUS_TAXON_CF"
    AMBIGUOUS_TAXON_AFF = "AMBIGUOUS_TAXON_AFF"
    STERILE_SPECIMEN = "STERILE_SPECIMEN"
    UNCLEAR_HANDWRITING = "UNCLEAR_HANDWRITING"
    APPROXIMATE_COVER = "APPROXIMATE_COVER"
    UNUSUAL_PERCENT_COVER = "UNUSUAL_PERCENT_COVER"
    MISSING_PERCENT_COVER = "MISSING_PERCENT_COVER"
    STRATUM_UNCERTAIN = "STRATUM_UNCERTAIN"


class BotanicalEntryExtraction(BaseModel):
    """Single extracted botanical occurrence from a handwritten field data sheet."""

    model_config = ConfigDict(extra="ignore")

    raw_text: str = Field(
        ...,
        description="Literal handwritten snippet extracted from the field sheet.",
    )
    taxon: str = Field(
        ...,
        description="Transcribed botanical name, binomial, or vernacular designation.",
    )
    stratum: Optional[str] = Field(
        None,
        description="Vegetation stratum, e.g. Tree, Sapling/Shrub, Herb, Woody Vine.",
    )
    percent_cover: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Absolute percent cover value (0.0 to 100.0).",
    )
    extraction_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this row's transcription (0.0 to 1.0).",
    )
    is_low_confidence: bool = Field(
        False,
        description="Flag indicating entry has low confidence or ambiguity requiring field verification.",
    )
    flag_reasons: List[str] = Field(
        default_factory=list,
        description="Diagnostic reasons why entry is flagged.",
    )
    morphological_adaptations: bool = Field(
        False,
        description="Whether morphological wetland adaptations are noted (e.g., adventitious roots, hypertrophied lenticels).",
    )
    notes: Optional[str] = Field(
        None,
        description="Supplemental field notes or observations for this entry.",
    )

    @field_validator("percent_cover", mode="before")
    @classmethod
    def parse_cover_value(cls, v: object) -> float:
        """Handle string inputs like '<1%', '25%', 'trace' before standard validation."""
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            clean = v.strip().rstrip("%").strip()
            if clean.lower() in ("trace", "t", "<1", "< 1", "+"):
                return 0.5
            try:
                return float(clean)
            except ValueError:
                raise ValueError(f"Unable to parse percent cover: {v}")
        raise ValueError(f"Invalid type for percent cover: {type(v)}")

    @field_validator("extraction_confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: object) -> float:
        """Clamp confidence float between 0.0 and 1.0."""
        try:
            val = float(v)  # type: ignore
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0


class FieldNoteMetadata(BaseModel):
    """Metadata extracted from the field notebook or data sheet header."""

    model_config = ConfigDict(extra="ignore")

    plot_id: Optional[str] = Field(None, description="Field plot or sampling station ID.")
    sampling_date: Optional[str] = Field(None, description="Date of field observation (YYYY-MM-DD or as recorded).")
    investigators: List[str] = Field(default_factory=list, description="Field delineators/botanists recorded.")
    project_name: Optional[str] = Field(None, description="Project or site name.")
    strata_recorded: List[str] = Field(default_factory=list, description="All vegetation strata documented on sheet.")
    general_notes: Optional[str] = Field(None, description="General field notes, weather, or site condition comments.")


class FieldNoteExtractionResponse(BaseModel):
    """Complete structured JSON response for a parsed field notes image."""

    model_config = ConfigDict(extra="ignore")

    metadata: FieldNoteMetadata = Field(default_factory=FieldNoteMetadata)
    entries: List[BotanicalEntryExtraction] = Field(default_factory=list)
    total_entries: int = Field(0, ge=0)
    low_confidence_count: int = Field(0, ge=0)
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_threshold_applied: float = Field(0.75, ge=0.0, le=1.0)
    status: str = Field(
        "success",
        description="Status code ('success', 'flagged_entries_present', 'no_entries_detected').",
    )
