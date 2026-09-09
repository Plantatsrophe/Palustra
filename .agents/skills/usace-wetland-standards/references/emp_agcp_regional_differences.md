# Regional Supplement Comparison: EMP vs. AGCP

This reference provides a side-by-side comparative analysis of regulatory differences between the **Eastern Mountains and Piedmont Regional Supplement (EMP, Version 2.0)** and the **Atlantic and Gulf Coastal Plain Regional Supplement (AGCP, Version 2.0)**.

---

## 1. Geographic & Physiographic Boundaries

| Feature | Eastern Mountains & Piedmont (EMP) | Atlantic & Gulf Coastal Plain (AGCP) |
| :--- | :--- | :--- |
| **Land Resource Regions (LRRs)** | **N** (Northern Atlantic Slope), **P** (South Atlantic & Ohio Slopes), **R** (Northeastern Mountains), **S** (Northern Appalachian Ridges) | **O** (Mississippi Delta), **P** (coastal transition fringes), **T** (Atlantic & Gulf Coast Lowland), **U** (Florida Peninsula) |
| **Physiography** | Rolling hills, plateaus, Piedmont crystalline bedrock, Blue Ridge, Valley and Ridge, Appalachian Plateaus. | Flat coastal terraces, deltaic plains, barrier islands, estuarine marshes, Carolina bays, pine flatwoods. |
| **National Wetland Plant List (NWPL)** | Regional ratings defined in `2022_NWPL_EMP.xlsx`. | Regional ratings defined in `2022_NWPL_AGCP.xlsx`. |

---

## 2. Wetland Hydrology Indicator Tier Differences

The most critical regulatory differences between EMP and AGCP occur in the tier assignments of hydrology indicators:

| Code | Indicator Name | EMP Tier | AGCP Tier | Regulatory Rationale & Field Application |
| :---: | :--- | :---: | :---: | :--- |
| **B6** | **Surface Soil Cracks** | **Secondary** | **PRIMARY** | In the AGCP, prolonged ponding followed by rapid evaporation produces deep desiccation cracks on clayey/silty flats; in the EMP, shrinking Piedmont clays often crack without wetland ponding. |
| **B9** | **Water-Stained Leaves** | **Secondary** | **PRIMARY** | In the AGCP, flat topography causes leaves to be submerged in stagnant water for weeks, staining them blackish-gray; in the EMP, upland leaves can be temporarily stained in shaded gullies. |
| **D6** | **Sphagnum Moss** | **Secondary** | *Not Recognized* | Restrictive to cool, acid bogs, mountain seeps, and peat wetlands in the EMP Appalachian mountains. |
| **D7** | **Frost-Heave Hummocks** | **Secondary** | *Not Recognized* | Confined to high-elevation, frost-prone wetlands in the EMP region. |

---

## 3. Hydric Soil Indicator Discrepancies (NRCS v8.2)

### EMP-Specific Indicator: F19 (Piedmont Floodplain Soils)
* **Status**: Valid **only** in EMP (specifically LRR P and MLRA 148 in LRR N).
* **Criteria**: On active floodplains, a mineral layer $\ge 15\text{ cm}$ thick within $25\text{ cm}$ of the surface with:
  * Matrix Value $\le 4$ and Chroma $\le 2$, and
  * $\ge 2\%$ distinct or prominent redox concentrations.
* **Why it does not apply in AGCP**: AGCP floodplains have more mature alluvial stratification and lower gradient deposition that allow standard indicators (such as F3 or A11) to form.

### AGCP-Specific Indicator: F20 (Anomalous Bright Loamy Soils)
* **Status**: Valid **only** in AGCP (specifically MLRAs 133A, 137, 149A, 153A, 153B in LRRs T and U).
* **Criteria**: A mineral layer $\ge 10\text{ cm}$ thick within $30\text{ cm}$ of the surface with:
  * Matrix Value $\ge 5$ and Chroma 3 or 4, and
  * $\ge 10\%$ distinct or prominent redox concentrations.
* **Why it does not apply in EMP**: High-chroma goethite-rich sands and loams are a unique geological feature of the Coastal Plain parent material.

---

## 4. Vegetation Indicator Status Shifts (NWPL EMP vs AGCP)

Certain species exhibit different wetland indicator ratings between the EMP and AGCP regions due to climatic adaptation and hydrological tolerances.

*When evaluating a site, always match the plant taxon to the regional list corresponding to the site location (`Data/2022_NWPL_EMP.xlsx` vs `Data/2022_NWPL_AGCP.xlsx`).*

### Notable Species Indicator Shifts:

| Scientific Name | Common Name | EMP Rating | AGCP Rating | Regulatory Impact |
| :--- | :--- | :---: | :---: | :--- |
| *Pinus taeda* | Loblolly Pine | **FAC** (Hydrophytic) | **FAC** (Hydrophytic) | Major canopy dominant across both regions. |
| *Liquidambar styraciflua* | Sweetgum | **FAC** (Hydrophytic) | **FAC** (Hydrophytic) | Co-dominant in floodplains and flats. |
| *Liriodendron tulipifera* | Tuliptree / Yellow Poplar | **FACU** (Non-Hydrophytic) | **FACU** (Non-Hydrophytic) | Upland indicator in both regions. |
| *Fagus grandifolia* | American Beech | **FACU** (Non-Hydrophytic) | **FACU** (Non-Hydrophytic) | Upland indicator across both regions. |
| *Acer rubrum* | Red Maple | **FAC** (Hydrophytic) | **FAC** (Hydrophytic) | Ubiquitous across wetlands and mesic uplands. |
| *Betula nigra* | River Birch | **FACW** (Hydrophytic) | **FACW** (Hydrophytic) | Obligate/facultative riparian dominant. |

---

## 5. Summary Checklist for Cross-Regional Audits

1. **Confirm LRR & County**: Determine whether the site falls into the Piedmont/Mountain province (EMP) or the Coastal Plain province (AGCP).
2. **Select NWPL Regional List**: Use `2022_NWPL_EMP.xlsx` for EMP sites; use `2022_NWPL_AGCP.xlsx` for AGCP sites.
3. **Check B6 and B9 Tiers**:
   * If AGCP: B6 or B9 is alone sufficient to satisfy the wetland hydrology criterion as a **Primary** indicator.
   * If EMP: B6 or B9 counts only as a **Secondary** indicator and must be paired with at least one other secondary indicator.
4. **Soil Indicator Verification**:
   * Do not accept F19 outside of LRR P / MLRA 148.
   * Do not accept F20 outside of the designated AGCP MLRAs in LRRs T and U.
