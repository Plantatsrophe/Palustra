"""Unit tests for botanical parser and USACE ambiguous taxa governance."""

import pytest
from palustra.etl.parser import (
    clean_text,
    parse_scientific_name,
    classify_field_ambiguity,
)

def test_clean_text():
    raw = " \xa0Acer \t rubrum \xa0 \n"
    assert clean_text(raw) == "Acer rubrum"

def test_parse_simple_binomial():
    raw = "Acer rubrum L."
    parsed = parse_scientific_name(raw)
    assert parsed["clean_name"] == "Acer rubrum"
    assert parsed["species_name"] == "Acer rubrum"
    assert parsed["genus"] == "Acer"
    assert parsed["species_epithet"] == "rubrum"
    assert parsed["authority"] == "L."
    assert parsed["infraspecific_rank"] is None

def test_parse_variety_with_dual_authorities():
    raw = "Acer rubrum L. var. trilobum Torr. & A. Gray ex K. Koch"
    parsed = parse_scientific_name(raw)
    assert parsed["clean_name"] == "Acer rubrum var. trilobum"
    assert parsed["species_name"] == "Acer rubrum"
    assert parsed["genus"] == "Acer"
    assert parsed["species_epithet"] == "rubrum"
    assert parsed["infraspecific_rank"] == "var."
    assert parsed["infraspecific_epithet"] == "trilobum"
    assert "Torr. & A. Gray" in parsed["authority"]

def test_parse_subspecies_normalization():
    raw = "Carex stricta Lam. ssp. stricta"
    parsed = parse_scientific_name(raw)
    assert parsed["clean_name"] == "Carex stricta subsp. stricta"
    assert parsed["infraspecific_rank"] == "subsp."
    assert parsed["infraspecific_epithet"] == "stricta"

def test_parse_hybrid_with_parentage():
    raw = "Abelia ×grandiflora (Rovelli ex André) Rehder [chinensis × uniflora]"
    parsed = parse_scientific_name(raw)
    assert parsed["clean_name"] == "Abelia ×grandiflora"
    assert parsed["genus"] == "Abelia"
    assert parsed["species_epithet"] == "×grandiflora"
    assert parsed["hybrid_parentage"] == "chinensis × uniflora"

def test_ambiguity_definitive():
    res = classify_field_ambiguity("Acer rubrum L.")
    assert res["ambiguity_type"] is None
    assert res["confidence_level"] == "Definitive"
    assert res["cleaned_target_name"] == "Acer rubrum"
    assert not res["warnings"]

def test_ambiguity_provisional_cf():
    res = classify_field_ambiguity("Carex cf. lurida")
    assert res["ambiguity_type"] == "provisional_cf"
    assert res["confidence_level"] == "Provisional"
    assert res["comparison_species"] == "Carex lurida"
    assert "PROVISIONAL" in res["warnings"][0]

def test_ambiguity_affinity_aff():
    res = classify_field_ambiguity("Quercus aff. nigra")
    assert res["ambiguity_type"] == "affinity_aff"
    assert res["confidence_level"] == "Affinity"
    assert res["reference_species"] == "Quercus nigra"
    assert "AFFINITY" in res["warnings"][0]

def test_ambiguity_heterogeneous_genus():
    res = classify_field_ambiguity("Carex sp.")
    assert res["ambiguity_type"] == "genus_only"
    assert res["confidence_level"] == "Indeterminate"
    assert res["is_homogeneous"] is False
    assert "EXCLUDE" in res["fqa_treatment_rule"]

def test_ambiguity_homogeneous_genus():
    res = classify_field_ambiguity("Typha sp.")
    assert res["ambiguity_type"] == "genus_only"
    assert res["is_homogeneous"] is True
    assert res["homogeneous_status"]["EMP"] == "OBL"
    assert res["homogeneous_status"]["AGCP"] == "OBL"

def test_ambiguity_sterile():
    res = classify_field_ambiguity("sterile Poaceae")
    assert res["ambiguity_type"] == "sterile"
    assert res["confidence_level"] == "Indeterminate"
    assert "EXCLUDE entirely from N" in res["fqa_treatment_rule"]
