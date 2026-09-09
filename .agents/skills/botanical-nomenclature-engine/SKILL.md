---
name: botanical-nomenclature-engine
description: >-
  Governs botanical taxonomy, USDA PLANTS symbol mapping, synonym resolution, and regional Floristic Quality Assessment (FQA) C-value lookups for USACE NWPL and state flora datasets. Use when resolving raw field plant names, standardizing botanical nomenclature, handling ambiguous taxa designations (sp., cf., aff., sterile), or computing standardized regional FQA Mean C-value and FQI metrics.
---

# Botanical Nomenclature & Taxonomy Governance Engine

This skill establishes domain standards, taxonomic protocols, and data harmonization logic for botanical records in regulatory wetland determinations and ecological site evaluations. It governs the cross-referencing of the **USDA PLANTS Database**, the **USACE National Wetland Plant List (NWPL 2022 AGCP & EMP)**, and **Regional Floristic Quality Assessment (FQA)** datasets.

---

## Role & Mandate

* **Role**: Botanical Data Scientist & Taxonomic Curator.
* **Scope**:
  1. Standardizing scientific binomials, infraspecific taxa, and authority citations.
  2. Resolving botanical synonyms to current USDA PLANTS symbols and accepted nomenclature.
  3. Governing ambiguous and sterile field taxa (`sp.`, `cf.`, `aff.`, `sterile`).
  4. Executing regulatory FQA metrics (Native Mean $C$, Total Mean $C$, $FQI$, Cover-Weighted $C$).
* **Output Standard**: Regulatory-grade, audit-ready botanical data schemas.

---

## 1. Taxonomic Normalization & Disambiguation Workflow

Botanical names entered from field logs often contain typographical variances, obsolete synonyms, authority citations, or informal notations. All plant records must undergo standardized normalization:

```
[Raw Field Record] 
       │
       ▼
1. Authority & Formatting Stripping (Separate taxon from author citation)
       │
       ▼
2. Infraspecific Parsing (Normalize ssp., subsp., var., f., × hybrids)
       │
       ▼
3. USDA PLANTS Synonym Lookup (Resolve obsolete synonyms to Accepted Symbol)
       │
       ▼
4. NWPL Status Join (Cross-reference EMP / AGCP wetland ratings)
       │
       ▼
5. Regional FQA Join (Assign Coefficient of Conservatism [C-value] & Nativity)
       │
       ▼
[Standardized Botanical Record]
```

### Normalization Rules
1. **Author Citation Stripping**: Botanical authorities (e.g., `L.`, `Michx.`, `(L.) Moench`) must be parsed and separated from the scientific name. Lookups against NWPL and FQA match on binomial / trinomial text:
   * Example: `"Acer negundo L. var. negundo "` $\to$ Scientific Name: `Acer negundo var. negundo`, Authority: `L.`, Symbol: `ACNEN`.
2. **Infraspecific Notation Standardization**:
   * Normalize `ssp.` to standard `subsp.` for subspecies.
   * Preserve `var.` (variety) and `f.` (forma) in accordance with the International Code of Nomenclature for algae, fungi, and plants (ICN).
   * Normalize hybrid signs: `×` (Unicode `U+00D7`) or `x` (ASCII) must be formatted cleanly with proper spacing (e.g., `Abelia ×grandiflora`, `Acer ×freemanii`).
3. **Punctuation and Whitespace**:
   * Strip trailing/leading spaces, non-breaking spaces (`\xa0`), double spaces, and quotation marks.

---

## 2. USDA PLANTS Symbol & Synonym Resolution

The **USDA PLANTS Database** provides the regulatory anchor for plant symbols and taxonomic acceptance.

### Resolution Protocol
1. **Symbol Search**:
   * Accepted Symbol (e.g., `ACRU` for *Acer rubrum*).
   * Synonym Symbol (e.g., historical symbols mapping to current accepted taxon).
2. **Synonym Chaining & Resolution**:
   * If a field surveyor records an older name or synonym (e.g., *Aster dumosus*, *Eupatorium dubium*, *Dichanthelium* vs. *Panicum*):
     * Identify the matching row in `Data/NC_USDA_PlantList.csv` or national PLANTS index where `Synonym` matches the query.
     * Extract the corresponding `Accepted Symbol` and `Scientific Name`.
     * Store the original raw name in `raw_field_name` and the current name in `accepted_scientific_name`.
3. **Regional NWPL Cross-Reference**:
   * Join against `Data/2022_NWPL_EMP.xlsx` or `Data/2022_NWPL_AGCP.xlsx` based on site location.
   * If an accepted taxon is not listed directly in the NWPL under its current name, check its basionym/synonyms on the NWPL synonym list.

For in-depth synonym matching algorithms, see [taxonomic_resolution_rules.md](./references/taxonomic_resolution_rules.md).

---

## 3. Governance of Ambiguous Field Taxa

Field botanists frequently encounter non-flowering, damaged, or indistinct specimens. This skill enforces strict regulatory handling rules for four ambiguous taxonomic classes:

### A. Genus-Only Records (`sp.` / `spp.`)
* **Notation**: e.g., `Carex sp.`, `Juncus sp.`, `Quercus sp.`, `Solidago sp.`
* **Dominance Test (50/20 Rule) Treatment**:
  * Include in stratum total cover calculations ($T$).
  * If the genus taxon satisfies 50/20 dominance criteria, determine whether **all** regionally co-occurring members of that genus in that habitat share the same indicator status (e.g., all local *Typha* or *Sagittaria* are OBL).
  * If indicator status varies across local species of that genus:
    * **Conservative Default**: If unresolvable, do **not** assume hydrophytic status unless supported by verified site associates or regional supplement guidance.
* **FQA Treatment**:
  * Genus-level taxa **cannot be assigned a species-specific C-value**.
  * **Rule**: Exclude from $N$ in Mean $C$ and $FQI$ calculations to avoid artificially skewing conservatism, but document in taxon inventory.

### B. Provisional Identifications (`cf.` — *confer / compare*)
* **Notation**: e.g., `Carex cf. lurida`, `Dichanthelium cf. clandestinum`.
* **Definition**: Morphological characters match the comparison species, but diagnostic features (such as mature perigynia or ripe achenes) are incomplete.
* **Rule**:
  * Adopt the comparison species' indicator status and $C$-value for provisional calculations.
  * Tag record with `confidence_level = "PROVISIONAL"`.

### C. Morphological Affinity (`aff.` — *affinis*)
* **Notation**: e.g., `Quercus aff. nigra`.
* **Definition**: Specimen exhibits distinct characteristics related to, but morphologically distinct from, the reference species (often an undescribed variant or hybrid).
* **Rule**:
  * Do not automatically assume identical $C$-value or indicator status without botanical documentation.
  * Tag record with `confidence_level = "AFFINITY"`.

### D. Sterile / Vegetative Unidentifiable Records (`sterile`)
* **Notation**: e.g., `sterile Poaceae`, `sterile Cyperaceae`, `unknown Asteraceae`.
* **Rule**:
  * Absolute cover **must** be accounted for in total stratum vegetative cover ($T$) so other species' relative dominance is not artificially inflated.
  * Treated as **Indeterminate** for dominance indicator status ($A$).
  * Excluded entirely from Prevalence Index and FQA $C$-value equations.

For full rules and decision trees, see [ambiguous_taxa_governance.md](./references/ambiguous_taxa_governance.md).

---

## 4. Regional Floristic Quality Assessment (FQA) Standards

Floristic Quality Assessment evaluates the ecological integrity and conservatism of plant communities based on expert-assigned **Coefficients of Conservatism ($C$-values)** ranging from 0 to 10:

| $C$-Value Range | Ecological Fidelity & Conservatism | Typical Habitat |
| :---: | :--- | :--- |
| **0** | Non-native (adventive/exotic) species, or ubiquitous native weeds. | Disturbed roadsides, agricultural fields, waste ground. |
| **1 – 3** | Opportunistic, disturbance-tolerant native generalists. | Early successional old fields, forest edges, ruderal openings. |
| **4 – 6** | Matrix species characteristic of stable natural communities. | Mature upland and wetland forests, typical riparian buffers. |
| **7 – 8** | High-fidelity species associated with advanced successional stages. | Intact bogs, mature bottomland hardwoods, undisturbed seeps. |
| **9 – 10** | Extreme ecological specialists restricted to pristine natural remnants. | Pocosins, calcareous fens, granite outcrops, virgin savannas. |

### Standard FQA Mathematical Formulas

1. **Native Mean $C$ ($\bar{C}_{\text{native}}$)**:
   $$\bar{C}_{\text{native}} = \frac{\sum_{i=1}^{N_{\text{native}}} C_i}{N_{\text{native}}}$$
   where $N_{\text{native}}$ is the total number of native species with assigned $C$-values.

2. **Total Mean $C$ ($\bar{C}_{\text{total}}$)**:
   $$\bar{C}_{\text{total}} = \frac{\sum_{i=1}^{N_{\text{total}}} C_i}{N_{\text{total}}}$$
   where $N_{\text{total}}$ includes both native and non-native species (with non-native species assigned $C = 0$).

3. **Native Floristic Quality Index ($FQI_{\text{native}}$)**:
   $$FQI_{\text{native}} = \bar{C}_{\text{native}} \times \sqrt{N_{\text{native}}}$$

4. **Total Floristic Quality Index ($FQI_{\text{total}}$)**:
   $$FQI_{\text{total}} = \bar{C}_{\text{total}} \times \sqrt{N_{\text{total}}}$$

5. **Cover-Weighted Mean $C$ ($\bar{C}_{\text{weighted}}$)**:
   $$\bar{C}_{\text{weighted}} = \frac{\sum_{i=1}^{n} (C_i \times \text{Cover}_i)}{\sum_{i=1}^{n} \text{Cover}_i}$$
   Calculates the community's structural floristic quality weighted by physical stratum dominance.

For regional calibration and mathematical boundary cases, see [regional_fqa_c_value_logic.md](./references/regional_fqa_c_value_logic.md).

---

## 5. Standardized Botanical Record Schema

When resolving botanical names, output data according to the following strict schema:

```json
{
  "raw_field_name": "Acer negundo L. var. negundo",
  "clean_scientific_name": "Acer negundo var. negundo",
  "accepted_scientific_name": "Acer negundo",
  "usda_plants_symbol": "ACNE2",
  "common_name": "boxelder",
  "family": "Sapindaceae",
  "taxonomic_status": "Accepted",
  "infraspecific_rank": "var.",
  "infraspecific_epithet": "negundo",
  "nwpl_indicator_emp": "FAC",
  "nwpl_indicator_agcp": "FAC",
  "c_value": 3,
  "nativity": "Native",
  "identification_confidence": "Definitive",
  "flags": []
}
```

For schema validation rules and export formats, see [botanical_data_standards.md](./references/botanical_data_standards.md).
