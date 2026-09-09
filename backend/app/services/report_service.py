"""Orchestration service for official USACE PDF reports and GIS GeoJSON boundary datasets."""

import logging
from typing import Any, Dict, List, Optional

from palustra.core.exceptions import ReportGenerationError
from palustra.export.models import USACEPlotExportData
from palustra.export.service import USACEExportService
from palustra.services.determination_service import DeterminationService

logger = logging.getLogger("palustra.services.report")


class ReportService:
    """Enterprise report orchestration service for USACE regulatory deliverables."""

    def __init__(self, determination_service: Optional[DeterminationService] = None) -> None:
        """Initialize the report service with an optional determination engine."""
        self.determination_service = determination_service or DeterminationService()

    def generate_plot_pdf(
        self,
        plot: USACEPlotExportData,
        watermark: Optional[str] = None,
    ) -> bytes:
        """Generate an official two-page USACE Regional Supplement Data Form PDF.

        Ensures that three-parameter determinations are verified and rendered into
        submission-ready PDF bytes conforming to USACE form geometry standards.

        Raises:
            ReportGenerationError: If PDF rendering or layout generation fails.
        """
        try:
            # If plot has not had determinations synthesized, evaluate and attach
            if plot.determination is None:
                plot.determination = self.determination_service.synthesize_determination(plot)

            return USACEExportService.export_plot_pdf(plot=plot, watermark=watermark)
        except Exception as exc:
            sampling_pt = getattr(plot, "sampling_point", "Unknown")
            logger.error(f"Failed to generate USACE PDF for plot '{sampling_pt}': {exc}", exc_info=True)
            raise ReportGenerationError(report_type="USACE Data Form PDF", cause=exc) from exc

    def generate_project_pdf(
        self,
        plots: List[USACEPlotExportData],
        watermark: Optional[str] = None,
    ) -> bytes:
        """Generate a consolidated multi-plot USACE PDF report.

        Raises:
            ReportGenerationError: If PDF consolidation or rendering fails.
        """
        try:
            for p in plots:
                if p.determination is None:
                    p.determination = self.determination_service.synthesize_determination(p)

            return USACEExportService.export_project_pdf(plots=plots, watermark=watermark)
        except Exception as exc:
            logger.error(f"Failed to generate consolidated project PDF: {exc}", exc_info=True)
            raise ReportGenerationError(report_type="Consolidated USACE PDF", cause=exc) from exc

    def generate_boundary_geojson(
        self,
        plots: List[USACEPlotExportData],
        include_transect_lines: bool = True,
        skip_unlocated: bool = False,
    ) -> Dict[str, Any]:
        """Generate an RFC 7946 GeoJSON FeatureCollection for GIS boundary delineation.

        Raises:
            ReportGenerationError: If GeoJSON conversion or coordinate processing fails.
        """
        try:
            for p in plots:
                if p.determination is None:
                    p.determination = self.determination_service.synthesize_determination(p)

            return USACEExportService.export_geojson(
                plots=plots,
                include_transect_lines=include_transect_lines,
                skip_unlocated=skip_unlocated,
            )
        except Exception as exc:
            logger.error(f"Failed to generate boundary GeoJSON: {exc}", exc_info=True)
            raise ReportGenerationError(report_type="GeoJSON FeatureCollection", cause=exc) from exc

    def generate_project_bundle_zip(
        self,
        plots: List[USACEPlotExportData],
        project_name: str = "Wetland_Project",
        watermark: Optional[str] = None,
        include_transect_lines: bool = True,
    ) -> bytes:
        """Create a complete submission ZIP bundle with individual PDFs, consolidated PDF, and GeoJSON.

        Raises:
            ReportGenerationError: If ZIP packaging or archive creation fails.
        """
        try:
            for p in plots:
                if p.determination is None:
                    p.determination = self.determination_service.synthesize_determination(p)

            return USACEExportService.export_project_zip(
                plots=plots,
                project_name=project_name,
                watermark=watermark,
                include_transect_lines=include_transect_lines,
            )
        except Exception as exc:
            logger.error(f"Failed to generate project ZIP bundle: {exc}", exc_info=True)
            raise ReportGenerationError(report_type="Project ZIP Bundle", cause=exc) from exc
