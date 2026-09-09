"""Base abstractions and data models for USACE Regional Supplement strategies."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple
from pydantic import BaseModel, Field


class RegionalSupplementEnum(str, Enum):
    """Approved and prospective USACE Regional Supplements."""

    EMP = "EMP"      # Eastern Mountains and Piedmont
    AGCP = "AGCP"    # Atlantic and Gulf Coastal Plain
    MW = "MW"        # Midwest
    NCNE = "NCNE"    # Northcentral and Northeast
    GP = "GP"        # Great Plains
    WM = "WM"        # Western Mountains, Valleys, and Coast
    AW = "AW"        # Arid West
    AK = "AK"        # Alaska
    HI = "HI"        # Hawaii and Pacific Islands
    CB = "CB"        # Caribbean Islands


class StratumCriteria(BaseModel):
    """Size cutoffs and physical criteria for a vegetation stratum under a regional supplement."""

    name: str = Field(..., description="Stratum designation (e.g. Tree, Sapling/Shrub, Herb, Woody Vine).")
    min_dbh_in: Optional[float] = Field(None, description="Inclusive minimum diameter at breast height in inches.")
    max_dbh_in: Optional[float] = Field(None, description="Exclusive maximum diameter at breast height in inches.")
    min_height_m: Optional[float] = Field(None, description="Inclusive minimum plant height in meters.")
    max_height_m: Optional[float] = Field(None, description="Exclusive maximum plant height in meters.")
    growth_form: Optional[str] = Field(None, description="Growth form: 'woody', 'herbaceous', 'vine', or 'any'.")
    plot_radius_ft: Optional[float] = Field(None, description="Standard sampling circular plot radius in feet.")
    plot_radius_m: Optional[float] = Field(None, description="Standard sampling circular plot radius in meters.")
    description: str = Field("", description="Official regulatory stratum definition.")

    def matches(
        self,
        dbh_in: Optional[float] = None,
        height_m: Optional[float] = None,
        is_woody: bool = True,
        is_vine: bool = False,
    ) -> bool:
        """Evaluate if an individual specimen satisfies this stratum's criteria."""
        # Woody vines
        if self.growth_form == "vine":
            if not is_vine:
                return False
            if self.min_height_m is not None and (height_m is None or height_m <= self.min_height_m):
                return False
            return True

        if is_vine:
            return False

        # Herb stratum: all herbaceous plants regardless of size, plus woody plants <= 1.0 m tall
        if self.growth_form == "herbaceous":
            if not is_woody:
                return True
            if height_m is not None and height_m > (self.max_height_m or 1.0):
                return False
            if dbh_in is not None and dbh_in >= 3.0:
                return False
            return True

        # Remaining strata require woody plants
        if not is_woody:
            return False

        # Tree stratum: woody plants >= min_dbh_in (3.0 in / 7.6 cm) DBH
        if self.min_dbh_in is not None:
            if dbh_in is None or dbh_in < self.min_dbh_in:
                return False
            return True

        # Sapling / Shrub stratum: woody plants < 3.0 in DBH and > 1.0 m tall
        if self.max_dbh_in is not None:
            if dbh_in is not None and dbh_in >= self.max_dbh_in:
                return False
            if self.min_height_m is not None:
                if height_m is None or height_m <= self.min_height_m:
                    return False
            return True

        return True


class RegionalSupplementPolicy(ABC):
    """Abstract Strategy interface governing regional regulatory wetland rules."""

    @property
    @abstractmethod
    def region_code(self) -> RegionalSupplementEnum:
        """The regulatory supplement enum identifier (e.g., EMP, AGCP)."""
        pass

    @property
    @abstractmethod
    def region_name(self) -> str:
        """Human-readable supplement title."""
        pass

    @abstractmethod
    def get_indicator_status(self, taxon_id: str, default_status: str = "NL") -> str:
        """Retrieve regional NWPL wetland indicator status (e.g. OBL, FACW, FAC, FACU, UPL, NL).

        Args:
            taxon_id: Scientific taxon name or USDA PLANTS symbol.
            default_status: Fallback indicator if taxon not specifically rated in this region.
        """
        pass

    @abstractmethod
    def get_stratum_definitions(self) -> Dict[str, StratumCriteria]:
        """Return the dictionary of stratum criteria definitions applicable to this region.

        Standard keys include 'Tree', 'Sapling/Shrub' (or 'Sapling'/'Shrub'), 'Herb', 'Woody Vine'.
        """
        pass

    @abstractmethod
    def validate_hydrology_indicators(
        self,
        primary: List[str],
        secondary: List[str],
    ) -> bool:
        """Validate whether the provided primary and secondary hydrology indicators satisfy the regional criteria.

        Under USACE standards, wetland hydrology is satisfied iff >= 1 confirmed Primary
        indicator OR >= 2 confirmed Secondary indicators are recognized in this region.
        """
        pass

    @abstractmethod
    def validate_hydric_soil_indicators(self, indicators: List[str]) -> bool:
        """Validate whether at least one approved NRCS hydric soil indicator is confirmed in this region.

        Filters the candidate indicator codes to those authorized in this regional supplement.
        """
        pass

    @abstractmethod
    def get_hydrology_tier(self, indicator_code: str) -> str:
        """Return regulatory tier for an indicator code in this region: 'Primary', 'Secondary', or 'Not Recognized'."""
        pass

    def classify_hydrology_indicators(
        self,
        observed_codes: Sequence[str],
    ) -> Tuple[List[str], List[str]]:
        """Classify a sequence of observed indicator codes into (primary_list, secondary_list) for this region."""
        primary: List[str] = []
        secondary: List[str] = []
        for raw_code in observed_codes:
            code = raw_code.strip().upper()
            tier = self.get_hydrology_tier(code)
            if tier == "Primary" and code not in primary:
                primary.append(code)
            elif tier == "Secondary" and code not in secondary:
                secondary.append(code)
        return primary, secondary

    @property
    @abstractmethod
    def approved_soil_indicators(self) -> Set[str]:
        """Set of NRCS field indicator codes approved for standard use in this region."""
        pass
