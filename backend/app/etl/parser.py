"""Botanical taxonomic parser, authority stripper, and regulatory ambiguity classifier."""

import re
from typing import Any, Dict, Optional, Tuple

# Infraspecific rank markers according to ICN
INFRASPECIFIC_RANKS = {"subsp.", "ssp.", "var.", "f."}

# Ambiguity indicator keywords
AMBIGUITY_PATTERNS = {
    "cf": re.compile(r"\bcf\.?\b", re.IGNORECASE),
    "aff": re.compile(r"\baff\.?\b", re.IGNORECASE),
    "sp": re.compile(r"\b(sp\.|spp\.|sp)\b", re.IGNORECASE),
    "sterile": re.compile(r"\b(sterile|sterilis)\b", re.IGNORECASE),
    "indet": re.compile(r"\b(indet\.|indeterminate)\b", re.IGNORECASE),
}

# Known homogeneous genera in USACE EMP and AGCP regions where all regional taxa share identical status
HOMOGENEOUS_GENERA_INDICATORS: Dict[str, Dict[str, str]] = {
    "Typha": {"EMP": "OBL", "AGCP": "OBL"},
    "Osmundastrum": {"EMP": "FACW", "AGCP": "FACW"},
    "Saururus": {"EMP": "OBL", "AGCP": "OBL"},
    "Peltandra": {"EMP": "OBL", "AGCP": "OBL"},
    "Taxodium": {"EMP": "OBL", "AGCP": "OBL"},
    "Platanus": {"EMP": "FACW", "AGCP": "FACW"},
}

def clean_text(text: str) -> str:
    """Normalize whitespace and strip non-breaking characters."""
    if not text:
        return ""
    # Replace non-breaking space and tabs with standard space
    normalized = text.replace("\xa0", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", normalized).strip()

def parse_hybrid_formula(raw_name: str) -> Tuple[str, Optional[str]]:
    """Extract bracketed hybrid parentage if present (e.g. [chinensis × uniflora])."""
    hybrid_parentage = None
    m = re.search(r"\[(.*?)\]", raw_name)
    if m:
        hybrid_parentage = clean_text(m.group(1))
        cleaned = raw_name[:m.start()] + raw_name[m.end():]
        return clean_text(cleaned), hybrid_parentage
    return clean_text(raw_name), None

def parse_scientific_name(raw_name: str) -> Dict[str, Any]:
    """Parse raw botanical name into scientific components, stripping author citations.
    
    Standardizes:
    - 'Acer negundo L. var. negundo ' -> clean: 'Acer negundo var. negundo', authority: 'L.'
    - 'Acer rubrum L. var. trilobum Torr. & A. Gray' -> clean: 'Acer rubrum var. trilobum'
    - 'Abelia ×grandiflora (Rovelli ex André) Rehder' -> clean: 'Abelia ×grandiflora'
    """
    text_cleaned, hybrid_parentage = parse_hybrid_formula(clean_text(raw_name))
    
    infraspecific_rank: Optional[str] = None
    infraspecific_epithet: Optional[str] = None
    species_author: Optional[str] = None
    infra_author: Optional[str] = None
    
    # Check for infraspecific rank marker: subsp., ssp., var., f.
    infra_match = re.search(r"\b(subsp\.|ssp\.|var\.|f\.)\s+([A-Za-z0-9\-]+)", text_cleaned)
    if infra_match:
        raw_rank = infra_match.group(1)
        infraspecific_rank = "subsp." if raw_rank == "ssp." else raw_rank
        infraspecific_epithet = infra_match.group(2)
        
        pre_infra = text_cleaned[:infra_match.start()].strip()
        post_infra = text_cleaned[infra_match.end():].strip()
        infra_author = post_infra if post_infra else None
        
        tokens = pre_infra.split()
        if len(tokens) >= 2:
            genus = tokens[0]
            if tokens[1] in ("×", "x", "X") and len(tokens) >= 3:
                species_epithet = tokens[1] + tokens[2]
                species_author = " ".join(tokens[3:]) if len(tokens) > 3 else None
            else:
                species_epithet = tokens[1]
                species_author = " ".join(tokens[2:]) if len(tokens) > 2 else None
        else:
            genus = tokens[0] if tokens else ""
            species_epithet = ""
            species_author = None
            
        clean_name = f"{genus} {species_epithet} {infraspecific_rank} {infraspecific_epithet}".strip()
        species_name = f"{genus} {species_epithet}".strip()
        
    else:
        tokens = text_cleaned.split()
        if len(tokens) >= 2:
            genus = tokens[0]
            if tokens[1] in ("×", "x", "X") and len(tokens) >= 3:
                species_epithet = tokens[1] + tokens[2]
                species_author = " ".join(tokens[3:]) if len(tokens) > 3 else None
            else:
                species_epithet = tokens[1]
                species_author = " ".join(tokens[2:]) if len(tokens) > 2 else None
        else:
            genus = tokens[0] if tokens else ""
            species_epithet = ""
            species_author = None
            
        clean_name = f"{genus} {species_epithet}".strip() if species_epithet else genus
        species_name = clean_name
        
    # Combine authorities if both present
    full_authority = None
    if species_author and infra_author:
        full_authority = f"{species_author} / {infra_author}"
    elif species_author:
        full_authority = species_author
    elif infra_author:
        full_authority = infra_author
        
    return {
        "raw_name": raw_name,
        "clean_name": clean_name,
        "species_name": species_name,
        "genus": genus,
        "species_epithet": species_epithet,
        "infraspecific_rank": infraspecific_rank,
        "infraspecific_epithet": infraspecific_epithet,
        "authority": full_authority,
        "hybrid_parentage": hybrid_parentage,
    }

def classify_field_ambiguity(raw_field_name: str) -> Dict[str, Any]:
    """Classify field-recorded plant names under USACE ambiguous taxa governance rules.
    
    Classifications:
    - Definitive: Identified to species or below without ambiguity tokens.
    - Provisional (cf.): Characters match named species, but diagnostic structures absent.
    - Affinity (aff.): Related to, but morphologically distinct from reference species.
    - Indeterminate: Genus-only (sp./spp.), sterile, or completely unidentifiable fragment.
    """
    cleaned = clean_text(raw_field_name)
    
    # 1. Check for sterile notation
    if AMBIGUITY_PATTERNS["sterile"].search(cleaned):
        return {
            "ambiguity_type": "sterile",
            "confidence_level": "Indeterminate",
            "cleaned_target_name": re.sub(AMBIGUITY_PATTERNS["sterile"], "", cleaned).strip(),
            "usace_dominance_rule": (
                "MUST include absolute cover in stratum total cover (T). "
                "Treated as Indeterminate for dominance indicator status; counts toward "
                "denominator (B) only, excluded from hydrophytic dominants numerator (A)."
            ),
            "fqa_treatment_rule": (
                "EXCLUDE entirely from N in Mean C and FQI calculations; do not assign C=0."
            ),
            "warnings": [
                "STERILE_MATERIAL: Vegetative only, excluded from FQA species count."
            ],
        }
        
    # 2. Check for indet notation
    if AMBIGUITY_PATTERNS["indet"].search(cleaned) or cleaned.lower() in ("unknown", "unknown herb", "unknown shrub"):
        return {
            "ambiguity_type": "indet",
            "confidence_level": "Indeterminate",
            "cleaned_target_name": cleaned,
            "usace_dominance_rule": (
                "Include cover in stratum total cover (T). Marked Indeterminate; "
                "counts toward total dominants denominator (B), excluded from numerator (A)."
            ),
            "fqa_treatment_rule": "Exclude from FQA equations.",
            "warnings": ["INDETERMINATE_MATERIAL: Completely unidentifiable."],
        }
        
    # 3. Check for provisional (cf.)
    if re.search(r"\bcf(?:\.|\b)", cleaned, re.IGNORECASE):
        target = re.sub(r"\bcf(?:\.|\b)\s*", "", cleaned, flags=re.IGNORECASE)
        target_parsed = parse_scientific_name(target)
        return {
            "ambiguity_type": "provisional_cf",
            "confidence_level": "Provisional",
            "cleaned_target_name": target_parsed["clean_name"],
            "comparison_species": target_parsed["clean_name"],
            "usace_dominance_rule": (
                "Adopt comparison species' indicator status for provisional calculations. "
                "Flag record as PROVISIONAL in audit remarks."
            ),
            "fqa_treatment_rule": (
                "Adopt comparison species' C-value for provisional scoring, flagged PROVISIONAL."
            ),
            "warnings": ["PROVISIONAL_IDENTIFICATION: Field record qualified with cf."],
        }
        
    # 4. Check for affinity (aff.)
    if re.search(r"\baff(?:\.|\b)", cleaned, re.IGNORECASE):
        target = re.sub(r"\baff(?:\.|\b)\s*", "", cleaned, flags=re.IGNORECASE)
        target_parsed = parse_scientific_name(target)
        return {
            "ambiguity_type": "affinity_aff",
            "confidence_level": "Affinity",
            "cleaned_target_name": target_parsed["clean_name"],
            "reference_species": target_parsed["clean_name"],
            "usace_dominance_rule": (
                "Do NOT assume identical indicator status without verified voucher check. "
                "If unverified, mark Indeterminate."
            ),
            "fqa_treatment_rule": (
                "Do NOT assign comparison C-value without regional botanical authority confirmation."
            ),
            "warnings": ["TAXONOMIC_AFFINITY: Field record qualified with aff."],
        }
        
    # 5. Check for genus-only notation (sp. or spp.)
    if AMBIGUITY_PATTERNS["sp"].search(cleaned):
        genus = cleaned.split()[0]
        # Check if genus is homogeneous
        emp_status = HOMOGENEOUS_GENERA_INDICATORS.get(genus, {}).get("EMP")
        agcp_status = HOMOGENEOUS_GENERA_INDICATORS.get(genus, {}).get("AGCP")
        is_homogeneous = emp_status is not None
        
        return {
            "ambiguity_type": "genus_only",
            "confidence_level": "Indeterminate",
            "cleaned_target_name": f"{genus} sp.",
            "genus": genus,
            "is_homogeneous": is_homogeneous,
            "homogeneous_status": {"EMP": emp_status, "AGCP": agcp_status},
            "usace_dominance_rule": (
                f"Include cover in stratum total cover (T). "
                + (f"Homogeneous genus: assign {emp_status} (EMP) / {agcp_status} (AGCP)."
                   if is_homogeneous else
                   "Heterogeneous genus: do NOT assume hydrophytic status; tally in denominator (B) only.")
            ),
            "fqa_treatment_rule": (
                "EXCLUDE from N in Mean C and FQI calculations to prevent index distortion."
            ),
            "warnings": [
                f"GENUS_ONLY_TAXON: {genus} sp. cannot be assigned species-specific C-value."
            ],
        }
        
    # 6. Definitive species identification
    parsed = parse_scientific_name(cleaned)
    return {
        "ambiguity_type": None,
        "confidence_level": "Definitive",
        "cleaned_target_name": parsed["clean_name"],
        "usace_dominance_rule": "Apply official NWPL regional indicator directly.",
        "fqa_treatment_rule": "Include in N, Mean C, and FQI calculations with species C-value.",
        "warnings": [],
    }
