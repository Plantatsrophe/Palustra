"""Palustra core domain exceptions and warnings."""

from typing import Optional


class PalustraDomainError(Exception):
    """Base exception for all Palustra domain errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TaxonNotFoundError(PalustraDomainError, KeyError):
    """Raised when a botanical taxon or USDA symbol cannot be located in the database."""

    def __init__(self, identifier: str, message: Optional[str] = None) -> None:
        msg = message or f"Taxon with identifier '{identifier}' not found in database."
        super().__init__(msg, details={"identifier": identifier})
        self.identifier = identifier


class AmbiguousTaxonWarning(UserWarning):
    """Issued when ambiguous, provisional, or non-definitive botanical field names are processed."""

    def __init__(self, raw_name: str, ambiguity_type: str, message: Optional[str] = None) -> None:
        msg = message or f"Ambiguous botanical entry '{raw_name}' classified as '{ambiguity_type}'."
        super().__init__(msg)
        self.raw_name = raw_name
        self.ambiguity_type = ambiguity_type


class InvalidCoverPercentageError(PalustraDomainError, ValueError):
    """Raised when vegetative cover percentage violates regulatory boundaries (0.0% to 100.0%)."""

    def __init__(
        self,
        percent_cover: float,
        taxon: Optional[str] = None,
        stratum: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        msg = (
            message
            or f"Invalid cover percentage '{percent_cover}%' for taxon '{taxon or 'Unknown'}' in stratum '{stratum or 'Unknown'}'. "
            f"Percent cover must be between 0.0 and 100.0."
        )
        super().__init__(
            msg,
            details={"percent_cover": percent_cover, "taxon": taxon, "stratum": stratum},
        )
        self.percent_cover = percent_cover
        self.taxon = taxon
        self.stratum = stratum


class InconsistentRegionalSupplementError(PalustraDomainError, ValueError):
    """Raised when an unsupported regional supplement or contradictory regional designation is provided."""

    def __init__(self, region: str, message: Optional[str] = None) -> None:
        msg = (
            message
            or f"Inconsistent or unsupported USACE Regional Supplement: '{region}'. Must be 'EMP' or 'AGCP'."
        )
        super().__init__(msg, details={"region": region})
        self.region = region


class ReportGenerationError(PalustraDomainError):
    """Raised when PDF, GeoJSON, or project bundle generation fails."""

    def __init__(self, report_type: str, cause: Optional[Exception] = None, message: Optional[str] = None) -> None:
        msg = message or f"Failed to generate '{report_type}' report: {str(cause) if cause else 'Unknown error'}"
        super().__init__(msg, details={"report_type": report_type, "cause": str(cause) if cause else None})
        self.report_type = report_type
        self.cause = cause
