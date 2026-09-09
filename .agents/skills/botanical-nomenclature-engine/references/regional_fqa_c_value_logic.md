# Regional Floristic Quality Assessment (FQA) & C-Value Logic

This document defines the mathematical foundations, ecological theory, and computational standards for **Floristic Quality Assessment (FQA)** and **Coefficient of Conservatism ($C$-value)** calculations.

---

## 1. Ecological Principles of the Coefficient of Conservatism ($C$)

The **Coefficient of Conservatism ($C$-value)** is an empirical, expert-derived score assigned to each plant species in a regional flora, representing its fidelity to intact natural habitats and its intolerance to anthropogenic degradation:

| $C$-Value | Ecological Fidelity & Tolerance Profile | Representative Natural Communities |
| :---: | :--- | :--- |
| **0** | Non-native (adventive/exotic) species, or ubiquitous native ruderal taxa. | Industrial brownfields, road verges, spoil piles, annual crop fields. |
| **1 – 3** | Wide ecological tolerance; opportunistic generalists thriving in disturbed sites. | Early successional pine plantations, overgrown pastures, utility corridors. |
| **4 – 6** | Intermediate conservatism; dominant matrix species of typical natural communities. | Mesic mixed hardwood forests, Piedmont bottomland hardwood corridors. |
| **7 – 8** | High ecological fidelity; taxa strongly tied to stable, late-successional ecosystems. | Mountain seeps, mature cypress-gum swamps, maritime live oak hammocks. |
| **9 – 10** | Extreme ecological specialists; restricted to pristine, fragile, or rare natural habitats. | Calcareous fens, southern Appalachian bogs, longleaf pine savannas, pocosins. |

---

## 2. Standardized FQA Mathematical Equations

### A. Mean $C$-Value Calculations

1. **Native Mean $C$ ($\bar{C}_{\text{native}}$)**:
   Evaluates the intrinsic conservatism of the native flora present on the site:
   $$\bar{C}_{\text{native}} = \frac{\sum_{i=1}^{N_{\text{native}}} C_i}{N_{\text{native}}}$$
   *where $N_{\text{native}}$ is the total number of native species with assigned $C$-values.*

2. **Total Mean $C$ ($\bar{C}_{\text{total}}$)**:
   Measures overall floristic quality while penalizing for the presence of non-native species (which receive $C = 0$):
   $$\bar{C}_{\text{total}} = \frac{\sum_{i=1}^{N_{\text{total}}} C_i}{N_{\text{total}}}$$
   *where $N_{\text{total}} = N_{\text{native}} + N_{\text{exotic}}$, and all exotic species are assigned $C = 0$.*

### B. Floristic Quality Index ($FQI$)

The $FQI$ integrates average conservatism with native species richness, scaling floristic quality by the square root of richness ($\sqrt{N}$) to mitigate pure area/sampling size inflation:

1. **Native Floristic Quality Index ($FQI_{\text{native}}$)**:
   $$FQI_{\text{native}} = \bar{C}_{\text{native}} \times \sqrt{N_{\text{native}}}$$

2. **Total Floristic Quality Index ($FQI_{\text{total}}$)**:
   $$FQI_{\text{total}} = \bar{C}_{\text{total}} \times \sqrt{N_{\text{total}}}$$

### C. Cover-Weighted Floristic Metrics

When stratum cover data are available, cover-weighted metrics evaluate the structural conservatism of the community rather than just presence/absence:

1. **Cover-Weighted Mean $C$ ($\bar{C}_{\text{weighted}}$)**:
   $$\bar{C}_{\text{weighted}} = \frac{\sum_{i=1}^{n} (C_i \times \text{Cover}_i)}{\sum_{i=1}^{n} \text{Cover}_i}$$
   *where $\text{Cover}_i$ is the absolute percent cover of species $i$.*

2. **Cover-Weighted $FQI$ ($FQI_{\text{weighted}}$)**:
   $$FQI_{\text{weighted}} = \bar{C}_{\text{weighted}} \times \sqrt{N}$$

---

## 3. Computational Boundary Rules & Edge Cases

1. **Non-Native (Exotic) Species Handling**:
   * In $\bar{C}_{\text{native}}$: Exotics are **completely excluded** from both the numerator and denominator.
   * In $\bar{C}_{\text{total}}$: Exotics are **included** in the denominator ($N_{\text{total}}$) and enter the numerator with $C = 0$.
   * *Effect*: High exotic cover drives $\bar{C}_{\text{total}}$ significantly lower than $\bar{C}_{\text{native}}$.
2. **Ambiguous Taxa (`sp.`, `sterile`, `indet.`)**:
   * Omitted from $N_{\text{native}}$, $N_{\text{total}}$, and cover-weighted formulas to prevent mathematical distortion.
3. **Rounding Standards**:
   * Mean $C$ values must be rounded to **two decimal places** ($0.01$).
   * $FQI$ values must be rounded to **one decimal place** ($0.1$) pursuant to standard regional publications.

---

## 4. Regional Ecological Interpretation Benchmarks (Southeast & Mid-Atlantic)

Based on calibrated regional reference wetland datasets (e.g., Gianopulos 2014, NC WAM standards):

| Native Mean $C$ ($\bar{C}_{\text{native}}$) | Native $FQI$ ($FQI_{\text{native}}$) | Floristic Quality Category | Ecological Condition & Integrity |
| :---: | :---: | :--- | :--- |
| **$< 3.0$** | **$< 15.0$** | **Low Floristic Quality** | Severely disturbed, dominated by ruderal weeds, early successional scrub, or non-native invasives. |
| **$3.0 - 4.5$** | **$15.0 - 25.0$** | **Moderate Floristic Quality** | Typical agricultural buffer, maturing secondary forest, moderate historic disturbance. |
| **$4.6 - 6.0$** | **$25.1 - 35.0$** | **High Floristic Quality** | Intact natural community, minimal recent disturbance, diverse native matrix. |
| **$> 6.0$** | **$> 35.0$** | **Exceptional (Conservation Priority)** | Pristine remnant ecosystem, rare species refugium, state natural heritage significance. |
