"""Asynchronous Gemini 1.5 Flash service for parsing photos of handwritten botanical field notes."""

import json
import logging
from typing import Any, Dict, List, Optional, Set
import google.generativeai as genai

from app.ai.prompts import (
    BOTANICAL_FIELD_NOTES_SYSTEM_INSTRUCTION,
    PARSE_FIELD_NOTES_USER_PROMPT,
)
from app.ai.schemas import (
    BotanicalEntryExtraction,
    ConfidenceFlagReasonEnum,
    FieldNoteExtractionResponse,
    FieldNoteMetadata,
)
from app.config import settings
from app.etl.parser import classify_field_ambiguity

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/gif",
}


class FieldNotesParserService:
    """Asynchronous parser for handwritten botanical field notes using Gemini 1.5 Flash."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        default_confidence_threshold: Optional[float] = None,
        model: Optional[Any] = None,
    ) -> None:
        """Initialize the field notes parser.
        
        Args:
            api_key: Google Gemini API key. Defaults to settings.gemini_api_key.
            model_name: Gemini model identifier. Defaults to settings.gemini_model ('gemini-1.5-flash').
            default_confidence_threshold: Threshold below which entries are flagged (default: 0.75).
            model: Pre-instantiated or mock model for dependency injection and testing.
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.default_confidence_threshold = (
            default_confidence_threshold
            if default_confidence_threshold is not None
            else settings.field_note_confidence_threshold
        )
        self._model = model

    def _get_or_create_model(self) -> Any:
        """Lazily initialize and configure the GenerativeModel instance."""
        if self._model is not None:
            return self._model

        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set the GEMINI_API_KEY environment variable "
                "or pass api_key to FieldNotesParserService."
            )

        genai.configure(api_key=self.api_key)

        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=FieldNoteExtractionResponse,
            temperature=settings.field_note_temperature,
        )

        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=BOTANICAL_FIELD_NOTES_SYSTEM_INSTRUCTION,
        )
        return self._model

    async def parse_field_notes_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        confidence_threshold: Optional[float] = None,
        custom_prompt: Optional[str] = None,
    ) -> FieldNoteExtractionResponse:
        """Asynchronously parse image bytes of handwritten field notes.

        Args:
            image_bytes: Raw binary bytes of the field note photo.
            mime_type: Image MIME type (e.g., 'image/jpeg', 'image/png').
            confidence_threshold: Custom threshold for low-confidence flag evaluation.
            custom_prompt: Optional override for the extraction user prompt.

        Returns:
            FieldNoteExtractionResponse containing validated botanical entries, confidence scores,
            and diagnostic flags.

        Raises:
            ValueError: If image bytes are empty, MIME type is unsupported, or schema parsing fails.
        """
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("Image bytes payload cannot be empty.")

        normalized_mime = mime_type.lower().strip()
        if normalized_mime == "image/jpg":
            normalized_mime = "image/jpeg"

        if normalized_mime not in SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Unsupported image MIME type: '{mime_type}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_MIME_TYPES))}"
            )

        threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else self.default_confidence_threshold
        )

        model = self._get_or_create_model()

        # Build inline byte part for asynchronous processing
        image_part: Dict[str, Any] = {
            "mime_type": normalized_mime,
            "data": image_bytes,
        }

        user_prompt = custom_prompt or PARSE_FIELD_NOTES_USER_PROMPT

        try:
            # Asynchronous image byte inference via google-generativeai
            response = await model.generate_content_async([image_part, user_prompt])
        except Exception as exc:
            logger.error("Gemini 1.5 Flash extraction error: %s", str(exc), exc_info=True)
            raise RuntimeError(f"Gemini 1.5 Flash field notes parsing failed: {str(exc)}") from exc

        raw_text = getattr(response, "text", None)
        if not raw_text:
            # Fallback inspection of candidates
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    raw_text = candidate.content.parts[0].text

        if not raw_text or not raw_text.strip():
            raise ValueError("Gemini returned an empty response for field notes image.")

        # Parse and enforce strict JSON schema
        try:
            parsed_data = json.loads(raw_text)
        except json.JSONDecodeError as err:
            raise ValueError(f"Failed to parse Gemini output as JSON: {str(err)}. Output: {raw_text[:200]}") from err

        raw_response = FieldNoteExtractionResponse.model_validate(parsed_data)

        # Post-process, audit confidence scores, and apply domain flagging
        return self._enrich_and_audit_extractions(raw_response, threshold=threshold)

    def _enrich_and_audit_extractions(
        self,
        extracted: FieldNoteExtractionResponse,
        threshold: float,
    ) -> FieldNoteExtractionResponse:
        """Audit per-row confidence scores, evaluate botanical ambiguity, and synthesize summary metrics."""
        enriched_entries: List[BotanicalEntryExtraction] = []
        low_confidence_count = 0
        total_confidence = 0.0

        for entry in extracted.entries:
            flag_reasons = list(entry.flag_reasons)
            is_low_conf = entry.is_low_confidence

            # 1. Check numeric extraction confidence threshold
            if entry.extraction_confidence < threshold:
                is_low_conf = True
                if ConfidenceFlagReasonEnum.LOW_CONFIDENCE_SCORE.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.LOW_CONFIDENCE_SCORE.value)

            # 2. Correlate with botanical ambiguity classifier
            ambiguity_info = classify_field_ambiguity(entry.taxon)
            ambiguity_type = ambiguity_info.get("ambiguity_type")

            if ambiguity_type == "provisional_cf":
                is_low_conf = True
                if ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_CF.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_CF.value)
            elif ambiguity_type == "affinity_aff":
                is_low_conf = True
                if ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_AFF.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_AFF.value)
            elif ambiguity_type == "genus_only":
                is_low_conf = True
                if ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_SP.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.AMBIGUOUS_TAXON_SP.value)
            elif ambiguity_type == "sterile":
                is_low_conf = True
                if ConfidenceFlagReasonEnum.STERILE_SPECIMEN.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.STERILE_SPECIMEN.value)

            # 3. Check for unusual percent cover
            if entry.percent_cover <= 0.0 or entry.percent_cover > 100.0:
                is_low_conf = True
                if ConfidenceFlagReasonEnum.UNUSUAL_PERCENT_COVER.value not in flag_reasons:
                    flag_reasons.append(ConfidenceFlagReasonEnum.UNUSUAL_PERCENT_COVER.value)

            if is_low_conf:
                low_confidence_count += 1

            total_confidence += entry.extraction_confidence

            # Create updated immutable Pydantic entry
            updated_entry = entry.model_copy(
                update={
                    "is_low_confidence": is_low_conf,
                    "flag_reasons": flag_reasons,
                }
            )
            enriched_entries.append(updated_entry)

        total_entries = len(enriched_entries)
        overall_conf = round(total_confidence / total_entries, 4) if total_entries > 0 else 1.0

        status_code = (
            "no_entries_detected"
            if total_entries == 0
            else ("flagged_entries_present" if low_confidence_count > 0 else "success")
        )

        return FieldNoteExtractionResponse(
            metadata=extracted.metadata,
            entries=enriched_entries,
            total_entries=total_entries,
            low_confidence_count=low_confidence_count,
            overall_confidence=overall_conf,
            confidence_threshold_applied=threshold,
            status=status_code,
        )
