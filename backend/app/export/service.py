"""Unified export service coordinating official USACE PDFs and GIS GeoJSON boundary datasets."""

import io
import zipfile
from typing import Any, Dict, List, Optional

from app.export.geojson import plot_to_geojson_feature, plots_to_geojson_collection
from app.export.models import USACEPlotExportData
from app.export.pdf_form import render_usace_pdf, render_usace_project_pdf


class USACEExportService:
    """Enterprise export service for submission-ready USACE PDFs and GIS boundary datasets."""

    @staticmethod
    def export_plot_pdf(plot: USACEPlotExportData, watermark: Optional[str] = None) -> bytes:
        """Export a single USACE plot as an official 2-page PDF."""
        return render_usace_pdf(plot_data=plot, watermark=watermark)

    @staticmethod
    def export_project_pdf(plots: List[USACEPlotExportData], watermark: Optional[str] = None) -> bytes:
        """Export multiple plots consolidated into a single multi-page project report."""
        return render_usace_project_pdf(plots=plots, watermark=watermark)

    @staticmethod
    def export_geojson(
        plots: List[USACEPlotExportData],
        include_transect_lines: bool = True,
        skip_unlocated: bool = False,
    ) -> Dict[str, Any]:
        """Export plots to an RFC 7946 GeoJSON FeatureCollection."""
        return plots_to_geojson_collection(
            plots=plots,
            include_transect_lines=include_transect_lines,
            skip_unlocated=skip_unlocated,
        )

    @classmethod
    def export_project_zip(
        cls,
        plots: List[USACEPlotExportData],
        project_name: str = "Wetland_Project",
        watermark: Optional[str] = None,
        include_transect_lines: bool = True,
    ) -> bytes:
        """Create a zip bundle containing individual plot PDFs, consolidated PDF, and GeoJSON."""
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1. Individual 2-page PDFs
            for p in plots:
                pdf_bytes = cls.export_plot_pdf(p, watermark=watermark)
                clean_id = p.sampling_point.replace("/", "_").replace("\\", "_")
                zf.writestr(f"pdfs/USACE_DataForm_{clean_id}.pdf", pdf_bytes)

            # 2. Consolidated multi-plot PDF if multiple plots
            if len(plots) > 1:
                proj_pdf = cls.export_project_pdf(plots, watermark=watermark)
                zf.writestr(f"{project_name}_Consolidated_Forms.pdf", proj_pdf)

            # 3. GIS GeoJSON dataset
            import json
            geojson_data = cls.export_geojson(plots, include_transect_lines=include_transect_lines)
            zf.writestr(f"gis/{project_name}_boundary_points.geojson", json.dumps(geojson_data, indent=2))

        val = zip_buf.getvalue()
        zip_buf.close()
        return val
