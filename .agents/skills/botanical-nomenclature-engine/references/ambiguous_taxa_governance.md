# Ambiguous Field Taxa Governance Protocol

This document establishes the regulatory standards for managing ambiguous, provisional, or non-flowering botanical records (`sp.`, `cf.`, `aff.`, `sterile`) in wetland delineations and Floristic Quality Assessments.

---

## 1. Taxonomic Ambiguity Classifications

Field surveys often yield plant observations where species-level identification is incomplete due to phenological stage, grazing, mowing, or lack of reproductive structures.

| Notation | Formal Latin Meaning | Field Operational Definition |
| :--- | :--- | :--- |
| **`sp.` / `spp.`** | *species* (singular / plural) | Identification confirmed to Genus only. No specific epithet asserted. |
| **`cf.`** | *confer* ("compare with") | Provisional identification. Characters match the named species, but diagnostic structures (e.g., fruit, achenes) are absent. |
| **`aff.`** | *affinis* ("having affinity with") | Confirmed distinct entity morphologically related to, but not identical with, the named species. |
| **`sterile`** | *sterilis* | Strictly vegetative material with no reproductive organs; genus or family level only. |
| **`indet.`** | *indeterminatus* | Completely unidentifiable vegetative fragment or seedling. |

---

## 2. Mathematical Governance in USACE Wetland Determinations

### A. Total Stratum Cover Calculations ($T$)
* **Mandatory Rule**: All plant cover, regardless of identification status (including `sterile Poaceae` or `unknown herb`), **must be included** in the total stratum vegetative cover sum ($T = \sum c_i$).
* **Regulatory Rationale**: Excluding unknown plant cover artificially deflates the stratum total, which distorts the 50% and 20% dominance thresholds and erroneously inflates the relative dominance of identified species.

### B. Dominance Test (50/20 Rule) Indicator Assignment
When an ambiguous taxon is determined to be a dominant species in a stratum:
1. **Homogeneous Genera (Uniform Regional Status)**:
   * If **all** species of that genus naturally occurring within the site's ecological region share the **exact same** wetland indicator status, assign that status to the genus record.
   * *Examples*:
     * *Typha sp.* $\to$ **OBL** (all regional cattails are OBL).
     * *Osmundastrum sp.* $\to$ **FACW** (*Osmundastrum cinnamomeum* is FACW).
     * *Alnus sp.* in AGCP $\to$ **FACW** (*Alnus serrulata* is FACW).
2. **Heterogeneous Genera (Mixed Indicator Statuses)**:
   * Genera containing species that span multiple indicator classes (e.g., *Carex*, *Juncus*, *Quercus*, *Solidago*, *Dichanthelium*, *Hypericum*).
   * **Regulatory Standard**: The indicator status cannot be guessed or assumed to be hydrophytic.
   * **Treatment**:
     * If the surveyor cannot determine the species from vegetative keys or microhabitat context, the record is marked **Indeterminate**.
     * In the Dominance Test ($A/B$), the taxon counts toward the denominator ($B$, total dominants), but **cannot count toward the numerator ($A$, hydrophytic dominants)** unless definitive regional botanical documentation supports a conservative wet determination.

### C. Prevalence Index (PI) Integration
* **Rule**: Ambiguous taxa without a confirmed indicator status **cannot** be assigned a numeric weight ($w_i$).
* **Protocol**:
  * Exclude the ambiguous taxon from both the numerator (weighted sum) and the denominator (total cover) of the Prevalence Index equation.
  * If ambiguous taxa represent $> 10\%$ of total plot cover, document the limitation in the site determination remarks.

---

## 3. Mathematical Governance in Floristic Quality Assessment (FQA)

Ambiguous taxa have significant mathematical implications for FQA metrics:

### A. Exclusion from Species Richness ($N$) in Mean $C$ & $FQI$
* Standard regional FQA protocols (Taft et al. 1997, Herman et al. 2001, Gianopulos 2014) mandate that:
  $$\mathbf{Genus\text{-}only\;taxa\;(sp./spp.)\;and\;sterile\;fragments\;MUST\;be\;excluded\;from\;N}$$
* **Mathematical Proof of Error if Not Excluded**:
  * If a genus-level record (e.g., *Carex sp.*) is arbitrarily assigned $C = 0$ (like a non-native weed), it artificially depresses the community Mean $C$ and $FQI$.
  * If it is assigned an average genus $C$-value, it introduces unverified assumptions into an empirical index.
  * Therefore, it is omitted from $N_{\text{native}}$ and $N_{\text{total}}$ in standard $\bar{C}$ calculations, but retained in the site floristic inventory.

### B. Treatment of `cf.` (Provisional) vs `aff.` (Affinity) in FQA
* **`cf.` Records**: Accepted at the comparison species' $C$-value for provisional ecological scoring, but flagged as `PROVISIONAL`.
* **`aff.` Records**: Inherit the $C$-value only if confirmed by regional botanical authority; otherwise treated as unranked.

---

## 4. Decision Matrix for Field Botanists & Data Reviewers

```
Is the taxon identified to species?
├── YES ──> Assign verified USDA Symbol, NWPL status, and C-value.
└── NO
    ├── Is it qualified with "cf."?
    │   └── YES ──> Use comparison species' status & C-value; tag PROVISIONAL.
    ├── Is it qualified with "aff."?
    │   └── YES ──> Tag AFFINITY; do not assign C-value without voucher check.
    └── Is it a Genus-only (sp.) or Sterile record?
        ├── Measure and record absolute cover (MUST include in stratum T).
        ├── Does the genus have 100% uniform regional wetland status?
        │   ├── YES ──> Assign uniform NWPL status for dominance testing.
        │   └── NO  ──> Mark status INDETERMINATE (B tally only).
        └── OMIT from FQA C-value calculations (do not assign C=0).
```
