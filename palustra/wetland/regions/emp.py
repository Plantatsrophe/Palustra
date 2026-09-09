"""Eastern Mountains and Piedmont (EMP) Regional Supplement Strategy."""

from typing import Dict, List, Optional, Set
from palustra.wetland.regions.base import (
    RegionalSupplementEnum,
    RegionalSupplementPolicy,
    StratumCriteria,
)

# EMP Regional Hydrology Tiers
EMP_HYDROLOGY_TIERS: Dict[str, str] = {
    # Group A: Observation of Surface Water or Saturated Soils
    "A1": "Primary",
    "A2": "Primary",
    "A3": "Primary",
    # Group B: Evidence of Recent Inundation
    "B1": "Primary",
    "B2": "Primary",
    "B3": "Primary",
    "B4": "Primary",
    "B5": "Primary",
    "B6": "Secondary",   # Surface Soil Cracks: Secondary in EMP
    "B7": "Primary",
    "B8": "Primary",
    "B9": "Secondary",   # Water-Stained Leaves: Secondary in EMP
    "B10": "Secondary",
    "B11": "Primary",
    "B12": "Secondary",
    "B13": "Primary",
    "B14": "Primary",
    "B15": "Primary",
    "B16": "Secondary",
    # Group C: Evidence of Current or Recent Soil Saturation
    "C1": "Primary",
    "C2": "Secondary",
    "C3": "Primary",
    "C4": "Primary",
    "C5": "Primary",
    "C6": "Primary",
    "C7": "Primary",
    "C8": "Secondary",
    "C9": "Secondary",
    # Group D: Evidence from Other Site Conditions or Data
    "D1": "Secondary",
    "D2": "Secondary",
    "D3": "Secondary",
    "D4": "Secondary",
    "D5": "Secondary",   # FAC-Neutral Test
    "D6": "Secondary",   # Sphagnum Moss: Secondary in EMP
    "D7": "Secondary",   # Frost-Heave Hummocks: Secondary in EMP
}

# Approved NRCS Hydric Soil Indicators in EMP (v8.2)
EMP_APPROVED_SOIL_INDICATORS: Set[str] = {
    # All Soils
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A11", "A12",
    # Sandy Soils
    "S1", "S4", "S5", "S6", "S7", "S9",
    # Loamy and Clayey Soils
    "F2", "F3", "F6", "F7", "F8", "F12",
    # EMP-Specific
    "F19",  # Piedmont Floodplain Soils
}

# Curated regional indicator ratings for EMP (including key species that shift regionally)
EMP_TAXON_INDICATOR_RATINGS: Dict[str, str] = {
    # Shifting taxa
    "QUERCUS NIGRA": "FAC",
    "QUNI": "FAC",
    "ROBINIA PSEUDOACACIA": "FACU",
    "ROPS": "FACU",
    # Standard regional dominant taxa
    "ACER RUBRUM": "FAC",
    "ACRU": "FAC",
    "ACER NEGUNDO": "FAC",
    "ACNE2": "FAC",
    "BETULA NIGRA": "FACW",
    "BENI": "FACW",
    "BOEHMERIA CYLINDRICA": "FACW",
    "BOCY": "FACW",
    "CAREX LURIDA": "OBL",
    "CALU": "OBL",
    "CARYA TOMENTOSA": "UPL",
    "CATO6": "UPL",
    "CHIMAPHILA MACULATA": "UPL",
    "CHMA2": "UPL",
    "FAGUS GRANDIFOLIA": "FACU",
    "FAGR": "FACU",
    "FRAXINUS PENNSYLVANICA": "FACW",
    "FRPE": "FACW",
    "LIQUIDAMBAR STYRACIFLUA": "FAC",
    "LIST2": "FAC",
    "LIRIODENDRON TULIPIFERA": "FACU",
    "LITU": "FACU",
    "PINUS TAEDA": "FAC",
    "PITA": "FAC",
    "PINUS SEROTINA": "FACW",
    "PLATANUS OCCIDENTALIS": "FACW",
    "PLOC": "FACW",
    "POLYSTICHUM ACROSTICHOIDES": "FACU",
    "POAC4": "FACU",
    "QUERCUS ALBA": "FACU",
    "QUAL": "FACU",
    "QUERCUS PHELLOS": "FACW",
    "SAURURUS CERNUUS": "OBL",
    "SACE": "OBL",
    "TAXODIUM DISTICHUM": "OBL",
    "TADI2": "OBL",
    "TYPHA LATIFOLIA": "OBL",
    "TYLA": "OBL",
}


class EMPPolicy(RegionalSupplementPolicy):
    """Eastern Mountains and Piedmont Regional Supplement (EMP) Strategy."""

    def __init__(self, custom_indicators: Optional[Dict[str, str]] = None) -> None:
        self._indicators: Dict[str, str] = dict(EMP_TAXON_INDICATOR_RATINGS)
        if custom_indicators:
            for k, v in custom_indicators.items():
                self._indicators[k.strip().upper()] = v.strip().upper()

    @property
    def region_code(self) -> RegionalSupplementEnum:
        return RegionalSupplementEnum.EMP

    @property
    def region_name(self) -> str:
        return "Eastern Mountains and Piedmont Regional Supplement (Version 2.0)"

    def get_indicator_status(self, taxon_id: str, default_status: str = "NL") -> str:
        """Resolve regional indicator status under the EMP NWPL list."""
        if not taxon_id:
            return default_status
        clean_key = taxon_id.strip().upper()
        return self._indicators.get(clean_key, default_status)

    def register_indicator(self, taxon_id: str, indicator_status: str) -> None:
        """Register or override an indicator status in this policy."""
        self._indicators[taxon_id.strip().upper()] = indicator_status.strip().upper()

    def get_stratum_definitions(self) -> Dict[str, StratumCriteria]:
        """Return 4-stratum criteria per EMP Regional Supplement."""
        tree = StratumCriteria(
            name="Tree",
            min_dbh_in=3.0,
            growth_form="woody",
            plot_radius_ft=30.0,
            plot_radius_m=9.1,
            description="Woody plants >= 3.0 in. (7.6 cm) DBH regardless of height.",
        )
        sapling_shrub = StratumCriteria(
            name="Sapling/Shrub",
            max_dbh_in=3.0,
            min_height_m=1.0,
            growth_form="woody",
            plot_radius_ft=15.0,
            plot_radius_m=4.6,
            description="Woody plants < 3.0 in. DBH and > 3.28 ft (1.0 m) tall.",
        )
        herb = StratumCriteria(
            name="Herb",
            max_height_m=1.0,
            growth_form="herbaceous",
            plot_radius_ft=5.0,
            plot_radius_m=1.5,
            description="All herbaceous plants regardless of size, and woody plants <= 3.28 ft (1.0 m) tall.",
        )
        woody_vine = StratumCriteria(
            name="Woody Vine",
            min_height_m=1.0,
            growth_form="vine",
            plot_radius_ft=30.0,
            plot_radius_m=9.1,
            description="All woody vines > 3.28 ft (1.0 m) tall.",
        )

        return {
            "Tree": tree,
            "Sapling/Shrub": sapling_shrub,
            "Sapling": sapling_shrub,
            "Shrub": sapling_shrub,
            "Herb": herb,
            "Woody Vine": woody_vine,
            "Vine": woody_vine,
        }

    def get_hydrology_tier(self, indicator_code: str) -> str:
        """Return regulatory tier for an indicator code in EMP."""
        clean = indicator_code.strip().upper()
        return EMP_HYDROLOGY_TIERS.get(clean, "Not Recognized")

    def validate_hydrology_indicators(
        self,
        primary: List[str],
        secondary: List[str],
    ) -> bool:
        """Evaluate wetland hydrology compliance for EMP.

        Criteria: >= 1 confirmed Primary OR >= 2 confirmed Secondary indicators.
        Filters inputs to indicators that are recognized in EMP with their designated tier.
        """
        valid_primary = [c for c in primary if self.get_hydrology_tier(c) == "Primary"]
        valid_secondary = [c for c in secondary if self.get_hydrology_tier(c) == "Secondary"]
        return len(valid_primary) >= 1 or len(valid_secondary) >= 2

    @property
    def approved_soil_indicators(self) -> Set[str]:
        return set(EMP_APPROVED_SOIL_INDICATORS)

    def validate_hydric_soil_indicators(self, indicators: List[str]) -> bool:
        """Evaluate if at least one approved hydric soil indicator is confirmed for EMP."""
        cleaned = {c.strip().upper() for c in indicators if c.strip()}
        valid_confirmed = cleaned.intersection(self.approved_soil_indicators)
        return len(valid_confirmed) > 0
