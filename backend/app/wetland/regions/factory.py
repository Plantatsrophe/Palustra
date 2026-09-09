"""Factory pattern for USACE Regional Supplement policy instantiation."""

from typing import Dict, List, Optional, Type, Union
from app.wetland.regions.agcp import AGCPPolicy
from app.wetland.regions.base import (
    RegionalSupplementEnum,
    RegionalSupplementPolicy,
)
from app.wetland.regions.emp import EMPPolicy


class RegionalPolicyFactory:
    """Extensible factory for resolving and instantiating RegionalSupplementPolicy strategies."""

    _REGISTRY: Dict[str, Type[RegionalSupplementPolicy]] = {
        RegionalSupplementEnum.EMP.value: EMPPolicy,
        RegionalSupplementEnum.AGCP.value: AGCPPolicy,
    }

    _POLICY_CACHE: Dict[str, RegionalSupplementPolicy] = {}

    @classmethod
    def register_policy(
        cls,
        region_code: Union[RegionalSupplementEnum, str],
        policy_cls: Type[RegionalSupplementPolicy],
    ) -> None:
        """Register a new or custom regional supplement strategy class.

        Allows any of the remaining 8 USACE regions to be added simply by registering
        a new policy class conforming to RegionalSupplementPolicy.
        """
        code_str = (
            region_code.value
            if isinstance(region_code, RegionalSupplementEnum)
            else str(region_code)
        ).strip().upper()

        cls._REGISTRY[code_str] = policy_cls
        # Invalidate cache entry if replacing
        cls._POLICY_CACHE.pop(code_str, None)

    @classmethod
    def get_policy(
        cls,
        region_code: Union[RegionalSupplementEnum, str, RegionalSupplementPolicy],
        use_cache: bool = True,
    ) -> RegionalSupplementPolicy:
        """Obtain a RegionalSupplementPolicy instance for the given region.

        Args:
            region_code: Enum, string code ('EMP', 'AGCP', etc.), or existing policy instance.
            use_cache: Whether to return a cached singleton policy instance.

        Returns:
            An instantiated RegionalSupplementPolicy.

        Raises:
            ValueError: If the region_code is unrecognized.
        """
        if isinstance(region_code, RegionalSupplementPolicy):
            return region_code

        code_str = (
            region_code.value
            if hasattr(region_code, "value")
            else str(region_code)
        ).strip().upper()

        if code_str not in cls._REGISTRY:
            supported = ", ".join(sorted(cls._REGISTRY.keys()))
            raise ValueError(
                f"Unsupported USACE regional supplement: '{code_str}'. Supported regions: {supported}."
            )

        if use_cache and code_str in cls._POLICY_CACHE:
            return cls._POLICY_CACHE[code_str]

        policy_instance = cls._REGISTRY[code_str]()
        if use_cache:
            cls._POLICY_CACHE[code_str] = policy_instance
        return policy_instance

    @classmethod
    def list_supported_regions(cls) -> List[str]:
        """List all currently registered regional supplement codes."""
        return sorted(cls._REGISTRY.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached policy instances (useful in test isolation)."""
        cls._POLICY_CACHE.clear()
