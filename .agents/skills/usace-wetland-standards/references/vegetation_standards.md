# Hydrophytic Vegetation Mathematical & Regulatory Standards

This document establishes the exact mathematical algorithms, regulatory thresholds, boundary condition resolutions, and rounding rules for assessing hydrophytic vegetation under the **USACE 1987 Wetland Delineation Manual** and the **EMP & AGCP Regional Supplements**.

---

## 1. Strata Definitions and Sampling Plot Standards

The Eastern Mountains and Piedmont (EMP) and Atlantic and Gulf Coastal Plain (AGCP) Regional Supplements employ four vegetation strata defined by growth form and physical size:

| Stratum | Definition / Inclusion Criteria | Typical Plot Dimensions |
| :--- | :--- | :--- |
| **Tree** | Woody plants $\ge 3.0\text{ in.}$ ($7.6\text{ cm}$) DBH | $30\text{-ft}$ ($9.1\text{-m}$) radius circular plot |
| **Sapling / Shrub** | Woody plants $< 3.0\text{ in.}$ DBH and $> 3.28\text{ ft}$ ($1.0\text{ m}$) tall | $15\text{-ft}$ ($4.6\text{-m}$) radius circular plot |
| **Herb** | All herbaceous plants regardless of size, and woody plants $\le 3.28\text{ ft}$ ($1.0\text{ m}$) tall | $5\text{-ft}$ ($1.5\text{-m}$) radius circular plot |
| **Woody Vine** | All woody vines $> 3.28\text{ ft}$ ($1.0\text{ m}$) tall | $30\text{-ft}$ ($9.1\text{-m}$) radius circular plot |

---

## 2. The 50/20 Dominance Rule (Per-Stratum Algorithm)

The **50/20 Rule** selects the dominant plant species that collectively constitute the majority of vegetative cover in each stratum.

### Mathematical Formulation

Let $S = \{ (s_1, c_1), (s_2, c_2), \dots, (s_n, c_n) \}$ represent the species in a stratum, where $s_i$ is the species taxon and $c_i$ is its absolute percent cover ($c_i > 0$).

1. **Calculate Total Stratum Cover ($T$)**:
   $$T = \sum_{i=1}^{n} c_i$$

2. **Order Decreasing**:
   Sort species such that $c_1 \ge c_2 \ge c_3 \ge \dots \ge c_n$.

3. **Calculate Regulatory Cutoff Thresholds**:
   $$\text{Threshold}_{50} = 0.50 \times T$$
   $$\text{Threshold}_{20} = 0.20 \times T$$

4. **The 50% Dominance Set ($D_{50}$)**:
   Species are selected in descending rank order until the cumulative cover strictly exceeds the 50% threshold:
   $$k = \min \left\{ m \in \{1, \dots, n\} \;\middle|\; \sum_{i=1}^{m} c_i > \text{Threshold}_{50} \right\}$$
   $$D_{50} = \{ s_1, s_2, \dots, s_k \}$$

   * **Exact Tie-Breaking Rule at 50% Boundary**:
     If there exists any species $s_j$ with $j > k$ such that $c_j = c_k$, then **all species tied with $c_k$ must be included in $D_{50}$**:
     $$D_{50}^{\text{tied}} = D_{50} \cup \{ s_j \mid j > k \text{ and } c_j = c_k \}$$

5. **The 20% Dominance Set ($D_{20}$)**:
   Any species with an individual absolute cover of 20% or more of total stratum cover is dominant:
   $$D_{20} = \{ s_i \in S \mid c_i \ge \text{Threshold}_{20} \}$$

6. **Combined Stratum Dominants ($D_{\text{stratum}}$)**:
   $$D_{\text{stratum}} = D_{50}^{\text{tied}} \cup D_{20}$$

---

## 3. Dominance Test Across All Strata

Once dominants are determined for each stratum present in the plot:

1. **Tally Total Dominant Occurrences ($B$)**:
   $$B = \sum_{\text{all strata}} |D_{\text{stratum}}|$$
   *Note*: A species that is dominant in multiple strata is counted separately for each stratum in which it is dominant.

2. **Tally Hydrophytic Dominant Occurrences ($A$)**:
   Identify dominant occurrences with an official National Wetland Plant List (NWPL) wetland indicator status of **OBL**, **FACW**, or **FAC**:
   $$A = \sum_{\text{all strata}} |\{ s \in D_{\text{stratum}} \mid \text{Status}(s) \in \{\text{OBL}, \text{FACW}, \text{FAC}\} \}|$$

3. **Compute Dominance Test Percentage**:
   $$\text{Percent Hydrophytic Dominants} = \left( \frac{A}{B} \right) \times 100$$

4. **Regulatory Determination**:
   $$\text{Dominance Test} = \begin{cases} \text{PASSED}, & \text{if } \left( \frac{A}{B} \right) \times 100 > 50.0\% \\ \text{FAILED}, & \text{if } \left( \frac{A}{B} \right) \times 100 \le 50.0\% \end{cases}$$
   * **Strict Boundary Rule**: A result of exactly $50.00\%$ is a **FAIL**. The ratio must strictly exceed 50.0%.

---

## 4. Prevalence Index (PI) Calculation

When a plant community fails the Dominance Test ($A/B \le 50.0\%$), but indicators of hydric soil and wetland hydrology are both present, the **Prevalence Index (PI)** must be calculated.

### Ecological Weighting Scale

| Indicator Status | Definition | Numeric Weight ($w$) |
| :--- | :--- | :---: |
| **OBL** (Obligate Wetland) | Occurs almost always in wetlands ($>99\%$ probability) | **1** |
| **FACW** (Facultative Wetland) | Usually occurs in wetlands ($67\% - 99\%$ probability) | **2** |
| **FAC** (Facultative) | Equally likely in wetlands or uplands ($34\% - 66\%$ probability) | **3** |
| **FACU** (Facultative Upland) | Usually occurs in non-wetlands ($1\% - 33\%$ probability in wetlands) | **4** |
| **UPL** (Upland) | Almost never occurs in wetlands ($<1\%$ probability) | **5** |
| **NL** (Not Listed) | Treated as UPL pursuant to USACE policy | **5** |

### Mathematical Formula

Sum the absolute percent cover of all species in the plot according to their indicator status across all strata:
* $S_{\text{OBL}} = \sum \text{Cover of OBL species}$
* $S_{\text{FACW}} = \sum \text{Cover of FACW species}$
* $S_{\text{FAC}} = \sum \text{Cover of FAC species}$
* $S_{\text{FACU}} = \sum \text{Cover of FACU species}$
* $S_{\text{UPL}} = \sum \text{Cover of UPL species}$

$$\text{Prevalence Index (PI)} = \frac{(S_{\text{OBL}} \times 1) + (S_{\text{FACW}} \times 2) + (S_{\text{FAC}} \times 3) + (S_{\text{FACU}} \times 4) + (S_{\text{UPL}} \times 5)}{S_{\text{OBL}} + S_{\text{FACW}} + S_{\text{FAC}} + S_{\text{FACU}} + S_{\text{UPL}}}$$

### Regulatory Precision & Rounding Rules
* Calculate PI to unrounded floating precision, then round to **two decimal places** ($0.01$) using standard arithmetic rounding (`ROUND_HALF_UP`).
* **Compliance Threshold**:
  $$\text{Hydrophytic Criterion Met} \iff PI \le 3.00$$

### Numerical Example & Boundary Cases
* **Example A**:
  * $S_{\text{OBL}} = 20$, $S_{\text{FACW}} = 30$, $S_{\text{FAC}} = 20$, $S_{\text{FACU}} = 20$, $S_{\text{UPL}} = 10$. Total cover = 100.
  * Weighted Sum = $(20 \times 1) + (30 \times 2) + (20 \times 3) + (20 \times 4) + (10 \times 5) = 20 + 60 + 60 + 80 + 50 = 270$.
  * $PI = 270 / 100 = 2.70 \le 3.00$ $\implies$ **PASSED**.
* **Example B (Rounding Threshold)**:
  * Weighted Sum / Total Cover = $3.0049 \implies \text{Rounds to } 3.00 \implies$ **PASSED**.
  * Weighted Sum / Total Cover = $3.0051 \implies \text{Rounds to } 3.01 \implies$ **FAILED**.

---

## 5. Rapid Test for Hydrophytic Vegetation

The **Rapid Test** is an expedited field screening step:
* Evaluate all dominant species across all strata identified via the 50/20 rule.
* **Criterion**: If **100%** of dominant species across all strata have an indicator status of **OBL** or **FACW** (or any combination thereof), the Rapid Test is **PASSED**.
* If passed, the plant community is hydrophytic without needing to calculate the Dominance Test or Prevalence Index.
* If even one dominant species is **FAC**, **FACU**, or **UPL**, the Rapid Test **FAILS**, and the standard Dominance Test must be calculated.

---

## 6. Morphological Adaptations Procedure

If the Dominance Test fails and $PI > 3.00$, evaluate whether dominant species classified as FACU exhibit morphological adaptations to anaerobic soil conditions:
1. **Qualifying Adaptations**:
   * Adventitious roots (above root collar or soil surface)
   * Hypertrophied lenticels (swollen lenticels on stem/roots)
   * Multi-stemmed or buttressed trunks
   * Shallow root systems (roots exposed horizontally along surface)
   * Fluted trunk bases
2. **Frequency Threshold**:
   * Adaptations must be clearly observed on **$\ge 50\%$ of the individuals** of that FACU species within the sampling plot.
3. **Recalculation Protocol**:
   * If the threshold is satisfied, reassign that specific species from **FACU** to **FAC** for that stratum.
   * Recalculate both the **Dominance Test** and the **Prevalence Index**.
   * If either test passes under the adjusted status, the hydrophytic vegetation criterion is satisfied.
