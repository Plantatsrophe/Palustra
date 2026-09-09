"""Palustra core package exposing foundational domain models, exceptions, and protocols."""

from palustra.core.exceptions import (
    AmbiguousTaxonWarning,
    InconsistentRegionalSupplementError,
    InvalidCoverPercentageError,
    PalustraDomainError,
    ReportGenerationError,
    TaxonNotFoundError,
)

__all__ = [
    "PalustraDomainError",
    "TaxonNotFoundError",
    "AmbiguousTaxonWarning",
    "InvalidCoverPercentageError",
    "InconsistentRegionalSupplementError",
    "ReportGenerationError",
]
