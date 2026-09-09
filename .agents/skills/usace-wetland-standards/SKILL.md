---
name: usace-wetland-standards
description: >-
  Enforces regulatory compliance and mathematical standards for USACE wetland determinations under the 1987 Wetland Delineation Manual and Regional Supplements (Eastern Mountains and Piedmont [EMP] and Atlantic and Gulf Coastal Plain [AGCP]). Use when performing or auditing 50/20 vegetation dominance calculations, computing the Prevalence Index, validating NRCS Hydric Soil indicators (v8.2), evaluating primary and secondary wetland hydrology indicators, or synthesizing three-parameter jurisdictional determinations.
---

# USACE Wetland Standards & Regulatory Compliance

This skill defines domain instructions and mathematical standards for conducting and reviewing jurisdictional wetland determinations pursuant to the **1987 Corps of Engineers Wetland Delineation Manual (Technical Report Y-87-1)** and the Regional Supplements for the **Eastern Mountains and Piedmont (EMP, Version 2.0)** and the **Atlantic and Gulf Coastal Plain (AGCP, Version 2.0)**.

---

## Role & Mandate

* **Role**: USACE Regulatory Compliance Specialist & Wetland Ecologist.
* **Scope**: Technical audit and rigorous calculation of the three mandatory wetland parameters:
  1. **Hydrophytic Vegetation**
  2. **Hydric Soils** (NRCS Field Indicators v8.2)
  3. **Wetland Hydrology**
* **Regulatory Standard**: Absolute mathematical precision. Rounding, thresholding, and tie-breaking must strictly adhere to USACE Regional Supplement instructions.

---

## 1. Hydrophytic Vegetation Standards

Hydrophytic vegetation is present if any of the following standard tests are met:
1. **Rapid Test**
2. **Dominance Test (50/20 Rule)**
3. **Prevalence Index (PI)** (used when Dominance Test fails and hydric soils/hydrology are present, or in problematic situations)
4. **Morphological Adaptations** (applied to FACU dominants if $\ge 50\%$ of individuals exhibit adaptations)

### A. Rapid Test for Hydrophytic Vegetation
* **Rule**: All dominant species across all strata are **OBL** or **FACW**, or a combination of both ($100\%$ OBL/FACW).
* If true: Hydrophytic vegetation requirement is satisfied without further calculations.
* If any dominant is **FAC**, **FACU**, or **UPL**, the Rapid Test fails.

### B. The 50/20 Dominance Rule (Per-Stratum Algorithm)
Calculated independently for each stratum present in the community:
* **Strata Definitions (EMP & AGCP)**:
  * **Tree Stratum**: Woody plants $\ge 3.0\text{ in.}$ ($7.6\text{ cm}$) diameter at breast height (DBH).
  * **Sapling/Shrub Stratum**: Woody plants $< 3.0\text{ in.}$ DBH and $> 3.28\text{ ft}$ ($1.0\text{ m}$) tall.
  * **Herb Stratum**: All herbaceous (non-woody) plants regardless of size, and woody plants $\le 3.28\text{ ft}$ ($1.0\text{ m}$) tall.
  * **Woody Vine Stratum**: All woody vines $> 3.28\text{ ft}$ ($1.0\text{ m}$) tall.

* **Exact Step-by-Step Algorithm**:
  1. **Compute Total Stratum Cover ($T$)**:
     $$T = \sum_{i=1}^{n} C_i$$
     where $C_i$ is the absolute percent cover of species $i$ in the stratum.
  2. **Rank Species**:
     Sort species in descending order of percent cover: $C_1 \ge C_2 \ge C_3 \dots \ge C_n$.
  3. **Calculate 50% Threshold**:
     $$\text{Threshold}_{50} = 0.50 \times T$$
  4. **Apply 50% Rule (Descending Cumulative Sum)**:
     Accumulate cover from largest to smallest until the running sum is **strictly greater than** 50% of the total stratum cover ($> 0.50 \times T$). All species in this cumulative sequence are dominant.
     * **Tie-Breaking Rule (50% Cutoff)**: If two or more species are tied in percent cover at the position that crosses the 50% threshold, **all tied species must be selected as dominants**.
  5. **Calculate 20% Threshold**:
     $$\text{Threshold}_{20} = 0.20 \times T$$
  6. **Apply 20% Rule**:
     Any additional species with absolute percent cover **greater than or equal to 20%** of the total stratum cover ($C_i \ge 0.20 \times T$) are also designated as dominants.
     * **Tie-Breaking Rule (20% Cutoff)**: Any species tied at or above the 20% mark are included.

### C. Dominance Test Across All Strata
Compile all dominant species across all strata into a single determination tally:
* Let $A$ = Number of dominant species across all strata that have an indicator status of **OBL**, **FACW**, or **FAC** (excluding FAC- in legacy contexts).
* Let $B$ = Total number of dominant species across all strata.
* *Note on Multi-Stratum Dominance*: If a species is dominant in multiple strata, count it once for each stratum in which it is dominant, matching standard USACE Regional Supplement data forms.
* **Dominance Test Criterion**:
  $$\text{Percent Dominance} = \left(\frac{A}{B}\right) \times 100$$
  * **Passing Threshold**: The Dominance Test passes **if and only if** the percentage is **strictly greater than 50%** ($> 50.0\%$).
  * *Boundary Precision*: Exactly $50.0\%$ **FAILS** the dominance test.

### D. Prevalence Index (PI) Formula
When the Dominance Test is not met, but hydric soil and wetland hydrology indicators are present, compute the Prevalence Index:
* **Indicator Status Weights ($w_i$)**:
  * $\text{OBL} = 1$
  * $\text{FACW} = 2$ (including FACW+, FACW-)
  * $\text{FAC} = 3$ (including FAC+, FAC-)
  * $\text{FACU} = 4$ (including FACU+, FACU-)
  * $\text{UPL} = 5$ (including non-listed taxa [NL])

* **Mathematical Formula**:
  $$PI = \frac{(A \times 1) + (B \times 2) + (C \times 3) + (D \times 4) + (E \times 5)}{A + B + C + D + E}$$
  where:
  * $A = \sum \text{Cover of OBL species across all strata}$
  * $B = \sum \text{Cover of FACW species across all strata}$
  * $C = \sum \text{Cover of FAC species across all strata}$
  * $D = \sum \text{Cover of FACU species across all strata}$
  * $E = \sum \text{Cover of UPL species across all strata}$

* **Rounding and Threshold**:
  * Round to **two decimal places** ($0.01$) using standard mathematical rounding (half-up).
  * **Criterion**: If $PI \le 3.00$, the hydrophytic vegetation requirement is satisfied.
  * *Boundary Check*: A calculated $PI$ of $3.004$ rounds to $3.00$ (Passes). A calculated $PI$ of $3.006$ rounds to $3.01$ (Fails).

For detailed proofs, edge cases, and adaptation workflows, see [vegetation_standards.md](./references/vegetation_standards.md).

---

## 2. NRCS Hydric Soil Standards (Field Indicators v8.2)

A hydric soil is a soil that formed under conditions of saturation, flooding, or ponding long enough during the growing season to develop anaerobic conditions in the upper part. Soil profiles must be evaluated against **NRCS Field Indicators of Hydric Soils in the United States (Version 8.2)**.

### A. Depleted Matrix Munsell Requirements
A depleted matrix consists of a layer where iron has been reduced and removed. It must satisfy one of the following exact Munsell color criteria:
1. Matrix Value $\ge 5$ and Chroma $\le 1$ with or without redox concentrations; **OR**
2. Matrix Value $\ge 6$ and Chroma $\le 2$ with or without redox concentrations; **OR**
3. Matrix Value 4 or 5 and Chroma 2 with $\ge 2\%$ distinct or prominent redox concentrations; **OR**
4. Matrix Value 4 and Chroma 1 with $\ge 2\%$ distinct or prominent redox concentrations.

### B. Common Field Indicators in EMP & AGCP Regions
* **All Soils ("A" Indicators)**:
  * **A1 (Histosol)**: $\ge 40\text{ cm}$ of organic soil material in the upper $80\text{ cm}$.
  * **A2 (Histic Epipedon)**: $\ge 20\text{ cm}$ of organic soil material near the surface.
  * **A4 (Hydrogen Sulfide)**: Rotten-egg odor within $30\text{ cm}$ ($12\text{ in.}$) of the surface.
  * **A11 (Depleted Below Dark Surface)**: A depleted or gleyed matrix layer $\ge 15\text{ cm}$ thick within $30\text{ cm}$ of the surface, beneath a dark surface layer (Value $\le 3$, Chroma $\le 2$).
  * **A12 (Thick Dark Surface)**: Depleted or gleyed matrix beneath a dark mineral surface $\ge 30\text{ cm}$ thick.

* **Sandy Soils ("S" Indicators)**:
  * **S4 (Sandy Gleyed Matrix)**: Value $\ge 4$ on Munsell gley charts within $15\text{ cm}$ of surface.
  * **S5 (Sandy Redox)**: Layer starting within $15\text{ cm}$ of surface with $\ge 2\%$ distinct or prominent redox concentrations in a matrix of Chroma $\le 2$.
  * **S6 (Stripped Matrix)**: Stripped zones in sandy matrix starting within $15\text{ cm}$.

* **Loamy and Clayey Soils ("F" Indicators)**:
  * **F2 (Loamy Gleyed Matrix)**: Gleyed matrix starting within $30\text{ cm}$ and $\ge 15\text{ cm}$ thick.
  * **F3 (Depleted Matrix)**: Depleted matrix $\ge 5\text{ cm}$ thick within $10\text{ cm}$ of surface, or $\ge 15\text{ cm}$ thick starting within $25\text{ cm}$ of surface.
  * **F6 (Redox Dark Surface)**: Dark surface with $\ge 2\%$ distinct or prominent redox concentrations.
  * **F7 (Depleted Dark Surface)**: Dark surface underlain by depleted layer.

### C. Regional Specific Soil Indicators
* **EMP Only - F19 (Piedmont Floodplain Soils)**:
  * Restricted to LRR P and MLRA 148 in LRR N.
  * Layer $\ge 15\text{ cm}$ thick within $25\text{ cm}$ of surface with Value $\le 4$, Chroma $\le 2$, and $\ge 2\%$ distinct or prominent redox concentrations.
* **AGCP Only - F20 (Anomalous Bright Loamy Soils)**:
  * Restricted to MLRAs 133A, 137, 149A, 153A, and 153B in LRRs T and U.
  * Matrix Value $\ge 5$, Chroma 3 or 4, and $\ge 10\%$ distinct or prominent redox concentrations.

For full indicator criteria and depth requirements, see [nrcs_hydric_soils_v8_2.md](./references/nrcs_hydric_soils_v8_2.md).

---

## 3. Wetland Hydrology Logic (EMP vs AGCP)

### A. Core Hydrology Decision Logic
The wetland hydrology criterion is met if:
$$\text{At least ONE (1) Primary Indicator is confirmed}$$
$$\mathbf{OR}$$
$$\text{At least TWO (2) Secondary Indicators are confirmed}$$

### B. Critical Regional Differences (AGCP vs EMP)
Several key indicators switch tier designation between the Atlantic and Gulf Coastal Plain (AGCP) and Eastern Mountains and Piedmont (EMP) Regional Supplements:

| Indicator Code | Indicator Name | AGCP Tier | EMP Tier | Regulatory Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **B6** | **Surface Soil Cracks** | **PRIMARY** | **SECONDARY** | Frequent ponding drying cycle in coastal flats vs upland clay cracking in piedmont. |
| **B9** | **Water-Stained Leaves** | **PRIMARY** | **SECONDARY** | High inundation persistence in AGCP hardwood swamps vs temporary wash in EMP. |
| **D6** | **Sphagnum Moss** | *Not Used* | **SECONDARY** | Restricted to cool, wet bogs and seeps in EMP. |
| **D7** | **Frost-Heave Hummocks** | *Not Used* | **SECONDARY** | Restricted to high elevations in EMP. |

### C. Primary vs Secondary Master Catalog

* **Primary Indicators (Both Regions unless noted)**:
  * **A1**: Surface Water
  * **A2**: High Water Table (within $12\text{ in.}$ / $30\text{ cm}$)
  * **A3**: Saturation (within $12\text{ in.}$ / $30\text{ cm}$)
  * **B1**: Water Marks (non-riverine)
  * **B2**: Sediment Deposits (non-riverine)
  * **B3**: Drift Deposits (non-riverine)
  * **B4**: Algal Mat or Crust
  * **B5**: Iron Deposits
  * **B7**: Inundation Visible on Aerial Imagery
  * **B8**: Sparsely Vegetated Concave Surface
  * **B9**: Water-Stained Leaves (*Primary in AGCP only*)
  * **B6**: Surface Soil Cracks (*Primary in AGCP only*)
  * **B11**: Salt Crust
  * **B13**: Aquatic Invertebrates
  * **B14**: True Aquatic Plants
  * **B15**: Marl Deposits
  * **C1**: Hydrogen Sulfide Odor
  * **C3**: Oxidized Rhizospheres on Living Roots
  * **C4**: Presence of Reduced Iron ($\alpha,\alpha'$-dipyridyl dye positive)
  * **C6**: Recent Iron Reduction in Tilled Soils
  * **C7**: Thin Muck Surface

* **Secondary Indicators (Both Regions unless noted)**:
  * **B6**: Surface Soil Cracks (*Secondary in EMP*)
  * **B9**: Water-Stained Leaves (*Secondary in EMP*)
  * **B10**: Drainage Patterns
  * **B16**: Moss Trim Lines
  * **C2**: Dry-Season Water Table
  * **C8**: Crayfish Burrows
  * **C9**: Saturation Visible on Aerial Imagery
  * **D1**: Stunted or Stressed Plants
  * **D2**: Geomorphic Position (concave depression, floodplain, toe-slope)
  * **D3**: Shallow Aquitard
  * **D4**: Microtopographic Relief
  * **D5**: **FAC-Neutral Test**:
    * Calculation: Exclude all FAC species from the dominant species list across all strata.
    * Evaluate: Count $(\text{OBL} + \text{FACW})$ vs $(\text{FACU} + \text{UPL})$.
    * Positive Result: If $(\text{OBL} + \text{FACW}) > (\text{FACU} + \text{UPL})$, D5 is positive and counts as **one secondary indicator**.
  * **D6**: Sphagnum Moss (*EMP only*)
  * **D7**: Frost-Heave Hummocks (*EMP only*)

For full hydrology descriptions, see [wetland_hydrology_logic.md](./references/wetland_hydrology_logic.md).

---

## 4. Synthesis: Jurisdictional Wetland Determination

A site is determined to be a **Jurisdictional Wetland** under standard conditions if and only if **all three parameters** are satisfied:

$$\text{Wetland} = \text{Hydrophytic Vegetation} \land \text{Hydric Soils} \land \text{Wetland Hydrology}$$

```
+-----------------------------------------------------------------------------+
|                          THREE-PARAMETER EVALUATION                         |
+-----------------------------------------------------------------------------+
| 1. Hydrophytic Vegetation: Rapid Test (100% OBL/FACW)                        |
|                            OR Dominance Test (> 50.0%)                      |
|                            OR Prevalence Index (<= 3.00)                    |
| 2. Hydric Soils:           >= 1 NRCS v8.2 Field Indicator Confirmed          |
| 3. Wetland Hydrology:      >= 1 Primary Indicator                           |
|                            OR >= 2 Secondary Indicators (accounting for     |
|                               regional EMP vs AGCP designations)            |
+-----------------------------------------------------------------------------+
```

---

## References Directory
Detailed technical manuals and calculation proofs are available in the `references/` directory:
- [vegetation_standards.md](./references/vegetation_standards.md): Full mathematical formulas, rounding rules, tie-breaking, and morphological adaptations.
- [nrcs_hydric_soils_v8_2.md](./references/nrcs_hydric_soils_v8_2.md): Complete field indicators list, depleted matrix criteria, and Munsell charts.
- [wetland_hydrology_logic.md](./references/wetland_hydrology_logic.md): Master primary/secondary indicator table and FAC-neutral calculations.
- [emp_agcp_regional_differences.md](./references/emp_agcp_regional_differences.md): Side-by-side comparative analysis of EMP vs AGCP Regional Supplements.
