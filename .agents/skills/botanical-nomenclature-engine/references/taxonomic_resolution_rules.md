# Taxonomic Resolution & Synonym Matching Rules

This document details the exact protocols for resolving scientific plant names, synonym chains, and authority citations using the **USDA PLANTS Database** and the **USACE National Wetland Plant List (NWPL)**.

---

## 1. Scientific Name Structure & Authority Parsing

Botanical nomenclature follows the rules of the International Code of Nomenclature (ICN). A complete botanical name contains:
1. **Genus**: Capitalized noun (e.g., *Acer*).
2. **Specific Epithet**: Lowercase adjective or noun (e.g., *rubrum*).
3. **Infraspecific Rank Marker**: Subspecies (`subsp.` or `ssp.`), variety (`var.`), or form (`f.`).
4. **Infraspecific Epithet**: Lowercase epithet (e.g., *trilobum*).
5. **Author Citation**: The person(s) who published the name (e.g., `L.`, `Michx.`, `(L.) Torr. & A. Gray`).

### Parsing Rules
* **Separate Name from Authority**: Author citations must not be included when querying the NWPL or FQA database.
  * Input: `"Acer rubrum L. var. trilobum Torr. & A. Gray ex Eaton"`
  * Clean Binomial / Trinomial: `Acer rubrum var. trilobum`
  * Authors: `L.` and `Torr. & A. Gray ex Eaton`
* **Handling Hybrid Notations**:
  * Interspecific hybrids use the multiplication sign `×` (or lowercase `x`):
    * Formulaic notation: `Abelia ×grandiflora (Rovelli ex André) Rehder [chinensis × uniflora]`
    * Clean Name: `Abelia ×grandiflora`
  * Hybrid parentage enclosed in square brackets must be separated into a `hybrid_parentage` metadata field.

---

## 2. Synonym Resolution Protocol

Field surveyors frequently record outdated names from older manuals (e.g., Radford et al. 1968, Gleason & Cronquist 1991). These must be resolved to current USDA PLANTS accepted names.

### Resolution Steps
1. **Direct Match**: Search for the exact name in `Accepted Symbol` and `Scientific Name`. If found, retrieve the accepted symbol.
2. **Synonym Match**: If not matched directly, search the `Synonym` column in `NC_USDA_PlantList.csv` or national PLANTS index.
3. **Extract Accepted Identity**:
   * Retrieve the `Accepted Symbol` on that synonym row.
   * Look up the accepted name associated with that symbol.
   * Example:
     * Field Input: `Aster dumosus`
     * Synonym Match: `Aster dumosus L.` has Accepted Symbol `SYDU2`
     * Accepted Name: `Symphyotrichum dumosum (L.) G.L. Nesom var. dumosum`
     * NWPL Status: Cross-referenced under `Symphyotrichum dumosum` (FAC in EMP/AGCP).

### Common High-Frequency Synonyms in Wetland Delineations:

| Field Synonyms (Historic) | Current Accepted Name (USDA PLANTS) | Accepted Symbol | Typical NWPL Status |
| :--- | :--- | :---: | :---: |
| *Acer rubrum* var. *drummondii* | *Acer drummondii* Hook. & Arn. ex Nutt. | `ACDR` | **OBL** |
| *Ampelopsis arborea* | *Nekemias arborea* (L.) J. Wen & Boggan | `NEAR5` | **FAC** |
| *Aster lateriflorus* | *Symphyotrichum lateriflorum* (L.) Á. Löve & D. Löve | `SYLA4` | **FACW** |
| *Betula lutea* | *Betula alleghaniensis* Britton | `BEAL2` | **FAC** |
| *Carex rosea* var. *radiata* | *Carex radiata* (Wahlenb.) Small | `CARA11` | **FAC** |
| *Eupatorium dubium* | *Eutrochium dubium* (Willd. ex Poir.) E.E. Lamont | `EUDU2` | **FACW** |
| *Eupatorium fistulosum* | *Eutrochium fistulosum* (Barratt) E.E. Lamont | `EUFI14` | **FACW** |
| *Panicum clandestinum* | *Dichanthelium clandestinum* (L.) Gould | `DICL` | **FACW** |
| *Panicum dichotomum* | *Dichanthelium dichotomum* (L.) Gould | `DIDI6` | **FAC** |
| *Polygonum sagittatum* | *Persicaria sagittata* (L.) H. Gross | `PESA6` | **OBL** |
| *Scirpus cyperinus* | *Scirpus cyperinus* (L.) Kunth | `SCCY` | **OBL** |
| *Solidago graminifolia* | *Euthamia graminifolia* (L.) Nutt. | `EUGR5` | **FACW** |

---

## 3. Resolving Infraspecific Variations vs Species-Level Ratings

* **NWPL Indicator Assignment**:
  * If the NWPL lists a specific variety/subspecies, apply that rating directly.
  * If the variety is **not** listed in the NWPL, default to the species-level indicator status (e.g., if *Acer negundo* var. *texanum* is not listed separately, apply the status for *Acer negundo*).
* **FQA C-Value Assignment**:
  * Where varieties have distinct ecological niches, assign variety-specific $C$-values from the regional FQA database.
  * If unlisted at the variety rank, inherit the species-level $C$-value.
