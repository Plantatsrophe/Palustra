# Wetland Hydrology Indicator Logic (EMP & AGCP)

This reference defines the regulatory requirements, operational rules, field indicator classifications, and regional logic switches for assessing wetland hydrology under the **USACE 1987 Manual** and the **Eastern Mountains and Piedmont (EMP)** and **Atlantic and Gulf Coastal Plain (AGCP)** Regional Supplements.

---

## 1. Regulatory Hydrology Standard

Under USACE standards, the wetland hydrology criterion requires:
> **Continuous inundation or soil saturation in the major part of the root zone (upper $12\text{ in.}$ / $30\text{ cm}$) for a minimum of 14 consecutive days during the growing season in at least 5 out of 10 years (50% probability).**

### Growing Season Determination
The growing season is active when either:
1. **Vegetation Phenology (Biological Indicator)**: Two or more non-evergreen vascular plant species exhibit active aboveground growth, such as bud burst, leaf emergence, stem elongation, or flowering.
2. **Soil Temperature (Biological Zero)**: Soil temperature measured at $12\text{ in.}$ ($30\text{ cm}$) depth exceeds $41^\circ\text{F}$ ($5^\circ\text{C}$).
3. **Climatic Data**: Standard local NRCS WETS table median frost-free dates ($28^\circ\text{F}$ or $32^\circ\text{F}$ thresholds).

---

## 2. Decision Logic: Primary vs. Secondary Indicators

The presence of wetland hydrology is confirmed in the field if:
$$\mathbf{At\;least\;ONE\;(1)\;Primary\;Indicator\;is\;present}$$
$$\mathbf{OR}$$
$$\mathbf{At\;least\;TWO\;(2)\;Secondary\;Indicators\;are\;present}$$

A single secondary indicator is **insufficient** to satisfy the hydrology requirement.

---

## 3. Master Indicator Catalog & Regional Tiers

The table below details every official hydrology indicator, specifying whether it functions as a **Primary** or **Secondary** indicator in the **Atlantic and Gulf Coastal Plain (AGCP)** versus the **Eastern Mountains and Piedmont (EMP)** regions:

| Code | Indicator Description | AGCP Tier | EMP Tier | Critical Field Observation Requirements |
| :--- | :--- | :---: | :---: | :--- |
| **Group A: Observation of Surface Water or Saturated Soils** |
| **A1** | **Surface Water** | **Primary** | **Primary** | Direct visual observation of water standing on the surface. |
| **A2** | **High Water Table** | **Primary** | **Primary** | Water table measured in an unlined pit within the upper $12\text{ in.}$ ($30\text{ cm}$) after equilibrium. |
| **A3** | **Saturation** | **Primary** | **Primary** | Visual observation of glistening soil pores or water glistening under pressure within the upper $12\text{ in.}$. |
| **Group B: Evidence of Recent Inundation** |
| **B1** | **Water Marks** | **Primary\*** | **Primary\*** | Physical stains on trees or structures indicating sustained ponding (*Primary in non-riverine, Secondary in riverine*). |
| **B2** | **Sediment Deposits** | **Primary\*** | **Primary\*** | Silt/clay coatings on vegetation or woody debris (*Primary in non-riverine, Secondary in riverine*). |
| **B3** | **Drift Deposits** | **Primary\*** | **Primary\*** | Rafts of organic debris stranded along contour lines (*Primary in non-riverine, Secondary in riverine*). |
| **B4** | **Algal Mat or Crust** | **Primary** | **Primary** | Dried algal mats or papery sheets adhering to soil or vegetation. |
| **B5** | **Iron Deposits** | **Primary** | **Primary** | Orange/red precipitates of oxidized iron or oily sheen on pooled surface water. |
| **B6** | **Surface Soil Cracks** | **PRIMARY** | **SECONDARY** | Desiccation cracks in silty/clayey surface deposits caused by ponding drying. |
| **B7** | **Inundation on Aerial Imagery** | **Primary** | **Primary** | Standing surface water clearly visible in aerial photography taken in normal precipitation conditions. |
| **B8** | **Sparsely Vegetated Concave Surface** | **Primary** | **Primary** | Concave depression where prolonged ponding prevents herbaceous establishment. |
| **B9** | **Water-Stained Leaves** | **PRIMARY** | **SECONDARY** | Dark brown, blackish, or curled leaf litter stained by prolonged inundation. |
| **B10** | **Drainage Patterns** | **Secondary** | **Secondary** | Scoured flow paths, braided channels, or debris wash lines in the absence of a defined stream bed. |
| **B11** | **Salt Crust** | **Primary** | **Primary** | Precipitated mineral salts on the soil surface from evaporating brackish/saline waters. |
| **B12** | **Biogenic Tool Marks** | **Secondary** | **Secondary** | Impressions in wet substrate made by animal foraging/tracks during inundation. |
| **B13** | **Aquatic Invertebrates** | **Primary** | **Primary** | Living or dead aquatic fauna (fairy shrimp, snails, clam shrimp, water boatmen, midge larvae). |
| **B14** | **True Aquatic Plants** | **Primary** | **Primary** | Plants requiring standing water for life cycle (e.g., *Nuphar*, *Nymphaea*, *Utricularia*, *Potamogeton*). |
| **B15** | **Marl Deposits** | **Primary** | **Primary** | Calcium carbonate precipitates deposited by algae or shellfish in mineral-rich wetlands. |
| **B16** | **Moss Trim Lines** | **Secondary** | **Secondary** | Sharp lower boundary on epiphytic mosses on tree trunks matching the high-water line. |
| **Group C: Evidence of Current or Recent Soil Saturation** |
| **C1** | **Hydrogen Sulfide Odor** | **Primary** | **Primary** | Distinct rotten egg odor released within the upper $12\text{ in.}$ ($30\text{ cm}$) upon excavation. |
| **C2** | **Dry-Season Water Table** | **Secondary** | **Secondary** | Water table within $24\text{ in.}$ ($60\text{ cm}$) of surface during the dry season or normal dry periods. |
| **C3** | **Oxidized Rhizospheres on Living Roots** | **Primary** | **Primary** | Bright reddish-brown iron pore linings around live, active plant roots in the upper $12\text{ in.}$. |
| **C4** | **Presence of Reduced Iron** | **Primary** | **Primary** | Immediate positive color reaction (bright pink/red) to $\alpha,\alpha'$-dipyridyl dye on freshly broken soil. |
| **C5** | **Salt Glands** | **Primary** | **Primary** | Active salt glands on halophytic plant species (*Spartina*, *Distichlis*). |
| **C6** | **Recent Iron Reduction in Tilled Soils** | **Primary** | **Primary** | Redox concentrations forming within plow layer of farmed wetlands. |
| **C7** | **Thin Muck Surface** | **Primary** | **Primary** | Layer of muck $1\text{ to }2\text{ cm}$ thick on mineral soil surface. |
| **C8** | **Crayfish Burrows** | **Secondary** | **Secondary** | Mud chimney burrows built by burrowing wetland crayfish. |
| **C9** | **Saturation on Aerial Imagery** | **Secondary** | **Secondary** | Distinct dark, wet soil signatures visible on aerial photographs during dry/normal periods. |
| **Group D: Evidence from Other Site Conditions or Data** |
| **D1** | **Stunted or Stressed Plants** | **Secondary** | **Secondary** | Morphological stress (chlorosis, stunted stems) on non-wetland plants caused by waterlogging. |
| **D2** | **Geomorphic Position** | **Secondary** | **Secondary** | Location in a concave depression, swale, abandoned channel, floodplain backswamp, or toe of slope. |
| **D3** | **Shallow Aquitard** | **Secondary** | **Secondary** | Impermeable subsoil horizon (hardpan, fragipan, dense clay) within $24\text{ in.}$ maintaining a perched water table. |
| **D4** | **Microtopographic Relief** | **Secondary** | **Secondary** | Hummock-and-hollow microtopography created by windthrow or differential plant growth in wet areas. |
| **D5** | **FAC-Neutral Test** | **Secondary** | **Secondary** | Calculated from dominant vegetation (see Section 4). |
| **D6** | **Sphagnum Moss** | *Not Used* | **SECONDARY** | Extensive sheets of *Sphagnum* moss growing on the soil surface (*EMP only*). |
| **D7** | **Frost-Heave Hummocks** | *Not Used* | **SECONDARY** | Hummocks created by frost action in saturated soils (*EMP only*). |

---

## 4. The FAC-Neutral Test (Indicator D5)

The **FAC-Neutral Test** is a mathematical evaluation of the dominant plant species across all strata to serve as a secondary hydrology indicator.

### Mathematical Procedure
1. Compile the list of all dominant species across all strata determined via the 50/20 rule.
2. **Exclude all FAC species** (FAC, FAC+, FAC-).
3. Count the number of dominant species that are more wet than facultative ($N_{\text{wet}}$):
   $$N_{\text{wet}} = |\{ s \in \text{Dominants} \mid \text{Status}(s) \in \{\text{OBL}, \text{FACW}, \text{FACW+}, \text{FACW-}\} \}|$$
4. Count the number of dominant species that are more dry than facultative ($N_{\text{dry}}$):
   $$N_{\text{dry}} = |\{ s \in \text{Dominants} \mid \text{Status}(s) \in \{\text{FACU}, \text{FACU+}, \text{FACU-}, \text{UPL}, \text{NL}\} \}|$$
5. **Evaluation**:
   $$\text{FAC-Neutral Result} = \begin{cases} \mathbf{POSITIVE}, & \text{if } N_{\text{wet}} > N_{\text{dry}} \\ \mathbf{NEGATIVE}, & \text{if } N_{\text{wet}} \le N_{\text{dry}} \end{cases}$$

### Regulatory Effect
* If $N_{\text{wet}} > N_{\text{dry}}$, the test is **Positive**, and **Secondary Indicator D5** is validated.
* When paired with at least one other secondary indicator (e.g., D2 Geomorphic Position), the wetland hydrology criterion is met.
