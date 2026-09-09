# Botanical Data Standards & Schema Specifications

This document defines the data structures, export formats, field definitions, and validation rules for botanical datasets processed by the **Botanical Nomenclature Engine**.

---

## 1. Standard Botanical Record Schema

All botanical records resolved from field notes or data forms must conform to the following JSON schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BotanicalTaxonRecord",
  "type": "object",
  "required": [
    "raw_field_name",
    "clean_scientific_name",
    "accepted_scientific_name",
    "usda_plants_symbol",
    "taxonomic_status",
    "identification_confidence",
    "nativity"
  ],
  "properties": {
    "raw_field_name": {
      "type": "string",
      "description": "Exact text entered by field observer."
    },
    "clean_scientific_name": {
      "type": "string",
      "description": "Normalized botanical name with authorities and informal notations stripped."
    },
    "accepted_scientific_name": {
      "type": "string",
      "description": "Current accepted scientific binomial/trinomial per USDA PLANTS."
    },
    "usda_plants_symbol": {
      "type": "string",
      "description": "Standard 4 to 8 character alphanumeric USDA PLANTS symbol (e.g., ACRU, SYDU2)."
    },
    "common_name": {
      "type": "string",
      "description": "Standard accepted English vernacular name."
    },
    "family": {
      "type": "string",
      "description": "Botanical plant family (e.g., Aceraceae/Sapindaceae, Cyperaceae, Poaceae)."
    },
    "taxonomic_status": {
      "type": "string",
      "enum": ["Accepted", "Synonym", "Ambiguous", "Unresolved"]
    },
    "infraspecific_rank": {
      "type": ["string", "null"],
      "enum": ["subsp.", "var.", "f.", null]
    },
    "infraspecific_epithet": {
      "type": ["string", "null"]
    },
    "nwpl_indicator_emp": {
      "type": ["string", "null"],
      "enum": ["OBL", "FACW", "FAC", "FACU", "UPL", "NL", null]
    },
    "nwpl_indicator_agcp": {
      "type": ["string", "null"],
      "enum": ["OBL", "FACW", "FAC", "FACU", "UPL", "NL", null]
    },
    "c_value": {
      "type": ["integer", "null"],
      "minimum": 0,
      "maximum": 10
    },
    "nativity": {
      "type": "string",
      "enum": ["Native", "Introduced", "Cryptogenic", "Unknown"]
    },
    "identification_confidence": {
      "type": "string",
      "enum": ["Definitive", "Provisional", "Affinity", "Indeterminate"]
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Audit warnings such as SYNONYM_RESOLVED, NWPL_SPLIT_STATUS, AMBIGUOUS_GENUS, STERILE."
    }
  }
}
```

---

## 2. Tabular / CSV Export Specification

When exporting tabular vegetation data for USACE reports or FQA summaries, columns must follow this standardized order:

| Column Header | Data Type | Description & Format |
| :--- | :--- | :--- |
| `raw_input` | String | Original raw name from field data form. |
| `accepted_name` | String | Validated USDA PLANTS accepted scientific name. |
| `usda_symbol` | String (Uppercase) | Current USDA PLANTS symbol (e.g., `ACRU`, `QUAL`). |
| `common_name` | String | Official accepted common name. |
| `family` | String | Botanical family name. |
| `stratum` | String | Tree, Sapling/Shrub, Herb, or Woody Vine. |
| `percent_cover` | Float | Absolute percent cover ($0.0 - 100.0\%$). |
| `emp_nwpl` | String | EMP wetland indicator status (OBL, FACW, FAC, FACU, UPL). |
| `agcp_nwpl` | String | AGCP wetland indicator status (OBL, FACW, FAC, FACU, UPL). |
| `c_value` | Integer / Empty | Regional Coefficient of Conservatism (0–10). |
| `nativity` | String | Native or Introduced. |
| `confidence` | String | Definitive, Provisional (`cf.`), Affinity (`aff.`), or Indeterminate. |
| `notes` | String | Taxonomic audit trail and synonym tracking notes. |

---

## 3. Data Integrity & Validation Checklist

Before finalizing any botanical dataset:
1. **Symbol Verification**: Ensure `usda_plants_symbol` exists in `Data/NC_USDA_PlantList.csv` or national PLANTS index.
2. **Indicator Validation**: Verify that `nwpl_indicator_emp` and `nwpl_indicator_agcp` match official ratings in `Data/2022_NWPL_EMP.xlsx` and `Data/2022_NWPL_AGCP.xlsx`.
3. **Nativity vs. C-Value Consistency**:
   * If `nativity == "Introduced"`, then `c_value` **must** be `0`.
   * If `c_value >= 1`, then `nativity` **must** be `Native`.
4. **Ambiguity Flags**:
   * Ensure any record with `identification_confidence != "Definitive"` is explicitly excluded from $N$ in FQA calculations.
