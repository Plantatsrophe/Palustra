"""Unit tests for Pydantic v2 taxon validation schemas."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    IdentificationConfidenceEnum,
    NativityEnum,
    NWPLIndicatorEnum,
    TaxonRecord,
    TaxonomicStatusEnum,
)

def test_valid_taxon_record():
    record = TaxonRecord(
        raw_field_name="Acer rubrum L.",
        clean_scientific_name="Acer rubrum",
        accepted_scientific_name="Acer rubrum",
        usda_plants_symbol="ACRU",
        common_name="red maple",
        family="Sapindaceae",
        taxonomic_status=TaxonomicStatusEnum.ACCEPTED,
        nwpl_indicator_emp=NWPLIndicatorEnum.FAC,
        nwpl_indicator_agcp=NWPLIndicatorEnum.FAC,
        c_value=3,
        nativity=NativityEnum.NATIVE,
        identification_confidence=IdentificationConfidenceEnum.DEFINITIVE,
        flags=[],
    )
    assert record.usda_plants_symbol == "ACRU"
    assert record.c_value == 3
    assert record.nativity == NativityEnum.NATIVE

def test_introduced_taxon_must_have_c_value_zero():
    # Introduced with c_value=0 is valid
    record = TaxonRecord(
        raw_field_name="Robinia pseudoacacia L.",
        clean_scientific_name="Robinia pseudoacacia",
        accepted_scientific_name="Robinia pseudoacacia",
        usda_plants_symbol="ROPS",
        taxonomic_status=TaxonomicStatusEnum.ACCEPTED,
        c_value=0,
        nativity=NativityEnum.INTRODUCED,
        identification_confidence=IdentificationConfidenceEnum.DEFINITIVE,
    )
    assert record.c_value == 0

    # Introduced with c_value > 0 must fail validation
    with pytest.raises(ValidationError, match="Introduced species must have c_value=0"):
        TaxonRecord(
            raw_field_name="Robinia pseudoacacia L.",
            clean_scientific_name="Robinia pseudoacacia",
            accepted_scientific_name="Robinia pseudoacacia",
            usda_plants_symbol="ROPS",
            taxonomic_status=TaxonomicStatusEnum.ACCEPTED,
            c_value=4,
            nativity=NativityEnum.INTRODUCED,
            identification_confidence=IdentificationConfidenceEnum.DEFINITIVE,
        )

def test_c_value_range_enforcement():
    with pytest.raises(ValidationError):
        TaxonRecord(
            raw_field_name="Test",
            clean_scientific_name="Test",
            accepted_scientific_name="Test",
            usda_plants_symbol="TEST",
            c_value=12,  # exceeds maximum 10
            nativity=NativityEnum.NATIVE,
        )
