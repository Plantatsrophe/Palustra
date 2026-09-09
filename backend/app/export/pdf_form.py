"""Official USACE Regional Supplement Wetland Determination Data Form PDF Generator.

Maintains official two-page form layouts for:
- Eastern Mountains and Piedmont (EMP, Version 2.0)
- Atlantic and Gulf Coastal Plain (AGCP, Version 2.0)
Uses ReportLab 4+ / 5+ for vector-perfect form rendering and pypdf for validation & metadata.
"""

import io
from typing import Any, Dict, List, Optional, Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from palustra.export.models import USACEPlotExportData
from palustra.wetland.models import (
    RegionEnum,
    SoilHorizon,
    SpeciesCover,
    WetlandDeterminationResult,
)
from palustra.wetland.synthesis import perform_jurisdictional_wetland_determination


# Palette constants for crisp USACE regulatory reporting
COLOR_BLACK = colors.black
COLOR_WHITE = colors.white
COLOR_NAVY = HexColor("#0A2540")
COLOR_HEADER_BG = HexColor("#E2E8F0")
COLOR_ACCENT_BG = HexColor("#F1F5F9")
COLOR_BORDER = HexColor("#334155")
COLOR_BORDER_LIGHT = HexColor("#94A3B8")
COLOR_PASS_BG = HexColor("#DCFCE7")  # soft green
COLOR_FAIL_BG = HexColor("#FEE2E2")  # soft red


class USACEDataFormPDFBuilder:
    """Renders the official USACE Regional Supplement 2-Page Wetland Determination Form."""

    def __init__(self, plot_data: USACEPlotExportData, watermark: Optional[str] = None):
        self.plot = plot_data
        self.watermark = watermark
        self.page_width, self.page_height = letter  # 612 x 792 pt
        self.margin_x = 24.0  # 0.33 in
        self.margin_y = 24.0
        self.content_width = self.page_width - (2 * self.margin_x)  # 564 pt
        self.content_height = self.page_height - (2 * self.margin_y)  # 744 pt

        # Ensure determination result is available
        self.determination = self._ensure_determination()

    def _ensure_determination(self) -> WetlandDeterminationResult:
        if self.plot.determination is not None:
            return self.plot.determination

        # Perform synthesis evaluation
        return perform_jurisdictional_wetland_determination(
            plot_id=self.plot.sampling_point,
            region=self.plot.region,
            strata_vegetation=self.plot.strata_vegetation,
            soil_horizons=self.plot.soil_horizons,
            hydrology_indicators=self.plot.hydrology_indicators,
            enable_morphological_adaptations=True,
        )

    def generate(self) -> bytes:
        """Build the 2-page PDF in-memory and return valid PDF bytes."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setTitle(f"USACE Wetland Determination - {self.plot.sampling_point}")
        c.setAuthor(self.plot.investigator or "Palustra Wetland Survey")
        c.setSubject(f"USACE Regional Supplement Wetland Determination Form ({self.plot.region.value})")
        c.setCreator("Palustra Regulatory Export Engine")

        # Page 1: Header, Summary of Findings, Hydrology
        self._render_page_1(c)
        if self.watermark:
            self._draw_watermark(c)
        c.showPage()

        # Page 2: Vegetation Strata & Worksheets, Soils Profile & Indicators
        self._render_page_2(c)
        if self.watermark:
            self._draw_watermark(c)
        c.showPage()

        c.save()
        raw_pdf = buffer.getvalue()
        buffer.close()

        # Post-process with pypdf to inject metadata and guarantee 2 pages
        return self._post_process_pdf(raw_pdf)

    def _post_process_pdf(self, pdf_bytes: bytes) -> bytes:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if len(reader.pages) != 2:
            raise ValueError(f"USACE form must strictly contain 2 pages, got {len(reader.pages)}")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata({
            "/Title": f"USACE Regional Supplement Data Form - Plot {self.plot.sampling_point}",
            "/Author": self.plot.investigator or "Palustra",
            "/Subject": f"Wetland Determination Data Form - {self.plot.region.value} Region",
            "/Producer": "Palustra USACE Exporter (ReportLab + pypdf)",
            "/Keywords": "USACE, Wetland, Delineation, Hydrology, Soils, Vegetation, Form",
        })

        out_buffer = io.BytesIO()
        writer.write(out_buffer)
        final_pdf = out_buffer.getvalue()
        out_buffer.close()
        return final_pdf

    # =========================================================================
    # PAGE 1 RENDERING
    # =========================================================================

    def _render_page_1(self, c: canvas.Canvas):
        curr_y = self.page_height - self.margin_y

        # Title Block
        curr_y = self._draw_page1_title(c, curr_y)

        # Administrative / Location Information Block
        curr_y = self._draw_admin_header(c, curr_y)

        # Environmental Conditions Flags
        curr_y = self._draw_environmental_conditions(c, curr_y)

        # Summary of Findings Box
        curr_y = self._draw_summary_of_findings(c, curr_y)

        # Hydrology Section Box
        curr_y = self._draw_hydrology_section(c, curr_y)

        # Page 1 Footer
        self._draw_footer(c, page_num=1)

    def _draw_page1_title(self, c: canvas.Canvas, y: float) -> float:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(COLOR_NAVY)
        title = "WETLAND DETERMINATION DATA FORM \u2013 Regional Supplement"
        c.drawCentredString(self.page_width / 2.0, y - 10, title)

        region_name = (
            "Eastern Mountains and Piedmont Region (Version 2.0)"
            if self.plot.region == RegionEnum.EMP
            else "Atlantic and Gulf Coastal Plain Region (Version 2.0)"
        )
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(COLOR_BLACK)
        c.drawCentredString(self.page_width / 2.0, y - 22, region_name)

        return y - 28

    def _draw_admin_header(self, c: canvas.Canvas, y: float) -> float:
        box_x = self.margin_x
        box_w = self.content_width
        box_h = 92.0
        top_y = y

        # Box border
        c.setLineWidth(0.75)
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_WHITE)
        c.rect(box_x, top_y - box_h, box_w, box_h, fill=1, stroke=1)

        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(COLOR_BLACK)

        # Row 1 (y: top_y - 15)
        r1_y = top_y - 14
        self._draw_field(c, box_x + 6, r1_y, "Project/Site:", self.plot.project_name, 160)
        self._draw_field(c, box_x + 180, r1_y, "City/County:", self.plot.city_county or "", 120)
        self._draw_field(c, box_x + 310, r1_y, "Sampling Date:", self.plot.sampling_date, 100)
        self._draw_field(c, box_x + 420, r1_y, "Sampling Point:", self.plot.sampling_point, 130, bold_val=True)

        # Row 2 (y: top_y - 30)
        r2_y = top_y - 29
        self._draw_field(c, box_x + 6, r2_y, "Applicant/Owner:", self.plot.applicant_owner or "", 160)
        self._draw_field(c, box_x + 180, r2_y, "State:", self.plot.state or "", 120)
        self._draw_field(c, box_x + 310, r2_y, "Section, Township, Range:", self.plot.section_township_range or "", 240)

        # Row 3 (y: top_y - 45)
        r3_y = top_y - 44
        self._draw_field(c, box_x + 6, r3_y, "Investigator(s):", self.plot.investigator or "", 240)
        self._draw_field(c, box_x + 260, r3_y, "Local relief (concave, convex, none):", self.plot.local_relief or "", 140)
        slope_str = f"{self.plot.slope_percent}%" if self.plot.slope_percent is not None else ""
        self._draw_field(c, box_x + 410, r3_y, "Slope (%):", slope_str, 140)

        # Row 4 (y: top_y - 60)
        r4_y = top_y - 59
        self._draw_field(c, box_x + 6, r4_y, "Subregion (LRR or MLRA):", self.plot.subregion or "", 180)
        lat_str = f"{self.plot.latitude:.6f}" if self.plot.latitude is not None else ""
        self._draw_field(c, box_x + 200, r4_y, "Lat:", lat_str, 80)
        lon_str = f"{self.plot.longitude:.6f}" if self.plot.longitude is not None else ""
        self._draw_field(c, box_x + 290, r4_y, "Long:", lon_str, 80)
        self._draw_field(c, box_x + 380, r4_y, "Datum:", self.plot.datum, 60)
        self._draw_field(c, box_x + 450, r4_y, "NWI:", self.plot.nwi_classification or "Upland", 100)

        # Row 5 (y: top_y - 75)
        r5_y = top_y - 74
        self._draw_field(c, box_x + 6, r5_y, "Soil Map Unit Name:", self.plot.soil_map_unit_name or "Not Mapped", 540)

        return top_y - box_h - 4

    def _draw_environmental_conditions(self, c: canvas.Canvas, y: float) -> float:
        box_x = self.margin_x
        box_w = self.content_width
        box_h = 32.0
        top_y = y

        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.setFillColor(COLOR_ACCENT_BG)
        c.rect(box_x, top_y - box_h, box_w, box_h, fill=1, stroke=1)

        c.setFont("Helvetica", 7.0)
        c.setFillColor(COLOR_BLACK)

        # Line 1: Typical climatic conditions
        typ_yes = "[X]" if self.plot.climatic_conditions_typical else "[ ]"
        typ_no = "[ ]" if self.plot.climatic_conditions_typical else "[X]"
        c.drawString(
            box_x + 6,
            top_y - 11,
            f"Are climatic / hydrologic conditions on the site typical for this time of year?  Yes {typ_yes}   No {typ_no}  (If no, explain in Remarks.)",
        )

        # Line 2: Disturbed / Problematic flags
        v_dist = "[X]" if self.plot.vegetation_disturbed else "[ ]"
        s_dist = "[X]" if self.plot.soil_disturbed else "[ ]"
        h_dist = "[X]" if self.plot.hydrology_disturbed else "[ ]"
        v_prob = "[X]" if self.plot.vegetation_problematic else "[ ]"
        s_prob = "[X]" if self.plot.soil_problematic else "[ ]"
        h_prob = "[X]" if self.plot.hydrology_problematic else "[ ]"

        c.drawString(
            box_x + 6,
            top_y - 23,
            f"Are Vegetation {v_dist}, Soil {s_dist}, or Hydrology {h_dist} significantly disturbed?     "
            f"Are Vegetation {v_prob}, Soil {s_prob}, or Hydrology {h_prob} naturally problematic? (Explain in Remarks)",
        )

        return top_y - box_h - 6

    def _draw_summary_of_findings(self, c: canvas.Canvas, y: float) -> float:
        box_x = self.margin_x
        box_w = self.content_width
        box_h = 88.0
        top_y = y

        # Box outline
        c.setLineWidth(1.0)
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_WHITE)
        c.rect(box_x, top_y - box_h, box_w, box_h, fill=1, stroke=1)

        # Header bar
        header_h = 15.0
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(box_x, top_y - header_h, box_w, header_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(
            box_x + 6,
            top_y - 11,
            "SUMMARY OF FINDINGS \u2013 Attach site map showing sampling point locations, transects, important features, etc.",
        )

        # Divider between params and determination
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        col_split_x = box_x + 320
        c.line(col_split_x, top_y - header_h, col_split_x, top_y - box_h + 20)

        # Left Column: The Three Parameters
        veg_ok = self.determination.hydrophytic_vegetation.hydrophytic_vegetation_present
        soil_ok = self.determination.hydric_soils.hydric_soil_present
        hydro_ok = self.determination.wetland_hydrology.wetland_hydrology_present

        c.setFont("Helvetica", 7.5)
        c.setFillColor(COLOR_BLACK)

        self._draw_param_row(c, box_x + 12, top_y - 29, "Hydrophytic Vegetation Present?", veg_ok)
        self._draw_param_row(c, box_x + 12, top_y - 44, "Hydric Soil Present?", soil_ok)
        self._draw_param_row(c, box_x + 12, top_y - 59, "Wetland Hydrology Present?", hydro_ok)

        # Right Column: Synthesis Determination
        is_wetland = self.determination.is_jurisdictional_wetland
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(col_split_x + 14, top_y - 30, "Is the Sampled Area")
        c.drawString(col_split_x + 14, top_y - 42, "within a Wetland?")

        # Determination Badge Box
        badge_x = col_split_x + 120
        badge_y = top_y - 52
        badge_w = 110
        badge_h = 28
        c.setFillColor(COLOR_PASS_BG if is_wetland else COLOR_FAIL_BG)
        c.setStrokeColor(COLOR_BORDER)
        c.setLineWidth(1.0)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 3, fill=1, stroke=1)

        c.setFont("Helvetica-Bold", 10.0)
        c.setFillColor(HexColor("#14532D") if is_wetland else HexColor("#7F1D1D"))
        res_text = "YES (WETLAND)" if is_wetland else "NO (UPLAND)"
        c.drawCentredString(badge_x + (badge_w / 2.0), badge_y + 9, res_text)

        # Bottom Remarks inside summary box
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(box_x, top_y - box_h + 20, box_x + box_w, top_y - box_h + 20)

        rem_text = self.plot.summary_remarks or self.determination.summary
        c.setFont("Helvetica", 6.8)
        c.setFillColor(COLOR_BLACK)
        c.drawString(box_x + 6, top_y - box_h + 7, f"Remarks: {rem_text[:130]}")

        return top_y - box_h - 6

    def _draw_param_row(self, c: canvas.Canvas, x: float, y: float, label: str, passed: bool):
        c.setFont("Helvetica", 7.5)
        c.drawString(x, y, label)
        yes_cb = "[X]" if passed else "[ ]"
        no_cb = "[ ]" if passed else "[X]"
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x + 190, y, f"Yes {yes_cb}    No {no_cb}")

    def _draw_hydrology_section(self, c: canvas.Canvas, y: float) -> float:
        box_x = self.margin_x
        box_w = self.content_width
        box_h = y - self.margin_y - 15  # Stretch cleanly down to above footer
        top_y = y

        # Section outer box
        c.setLineWidth(1.0)
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_WHITE)
        c.rect(box_x, top_y - box_h, box_w, box_h, fill=1, stroke=1)

        # Section Header bar
        header_h = 15.0
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(box_x, top_y - header_h, box_w, header_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, top_y - 11, "HYDROLOGY")

        # Hydrology Checklist Definition (Region Sensitive)
        is_agcp = self.plot.region == RegionEnum.AGCP
        obs_set = set(self.plot.hydrology_indicators)

        # Primary Indicators List
        primary_col1 = [
            ("A1", "Surface Water (A1)"),
            ("A2", "High Water Table (A2)"),
            ("A3", "Saturation (A3)"),
            ("B1", "Water Marks (B1)"),
            ("B2", "Sediment Deposits (B2)"),
            ("B3", "Drift Deposits (B3)"),
            ("B4", "Algal Mat or Crust (B4)"),
            ("B5", "Iron Deposits (B5)"),
            ("B7", "Inundation Visible on Aerial (B7)"),
            ("B8", "Sparsely Veg. Concave Surface (B8)"),
        ]
        if is_agcp:
            primary_col1.append(("B6", "Surface Soil Cracks (B6)"))
            primary_col1.append(("B9", "Water-Stained Leaves (B9)"))

        primary_col2 = [
            ("B13", "Aquatic Fauna / Invertebrates (B13)"),
            ("B14", "True Aquatic Plants (B14)"),
            ("B15", "Marl Deposits (B15)"),
            ("C1", "Hydrogen Sulfide Odor (C1)"),
            ("C3", "Oxidized Rhizospheres on Living Roots (C3)"),
            ("C4", "Presence of Reduced Iron (C4)"),
            ("C6", "Recent Iron Reduction in Tilled Soils (C6)"),
            ("C7", "Thin Muck Surface (C7)"),
            ("Other", "Other (Explain in Remarks)"),
        ]

        # Secondary Indicators List
        secondary_col1 = []
        if not is_agcp:
            secondary_col1.append(("B6", "Surface Soil Cracks (B6)"))
            secondary_col1.append(("B9", "Water-Stained Leaves (B9)"))
        secondary_col1.extend([
            ("B10", "Drainage Patterns (B10)"),
            ("B16", "Moss Trim Lines (B16)"),
            ("C2", "Dry-Season Water Table (C2)"),
            ("C8", "Crayfish Burrows (C8)"),
            ("C9", "Saturation Visible on Aerial (C9)"),
        ])

        secondary_col2 = [
            ("D1", "Stunted or Stressed Plants (D1)"),
            ("D2", "Geomorphic Position (D2)"),
            ("D3", "Shallow Aquitard (D3)"),
            ("D4", "Microtopographic Relief (D4)"),
            ("D5", "FAC-Neutral Test (D5)"),
        ]
        if not is_agcp:
            secondary_col2.append(("D6", "Sphagnum Moss (D6)"))
            secondary_col2.append(("D7", "Frost-Heave Hummocks (D7)"))

        # Subheaders for Primary & Secondary
        cur_y = top_y - 25
        c.setFont("Helvetica-Bold", 7.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, cur_y, "Primary Indicators (minimum of one is required; check all that apply)")
        c.drawString(box_x + 284, cur_y, "Secondary Indicators (minimum of two required)")

        cur_y -= 10
        # Draw Indicators in two side-by-side halves
        left_half_x1 = box_x + 6
        left_half_x2 = box_x + 142
        right_half_x1 = box_x + 284
        right_half_x2 = box_x + 420

        # Draw Primary Indicators
        prim_y = cur_y
        for code, label in primary_col1:
            checked = "[X]" if code in obs_set else "[ ]"
            c.setFont("Helvetica", 6.2)
            c.setFillColor(COLOR_BLACK)
            c.drawString(left_half_x1, prim_y, f"{checked} {label}")
            prim_y -= 9.5

        prim_y2 = cur_y
        for code, label in primary_col2:
            checked = "[X]" if code in obs_set else "[ ]"
            c.setFont("Helvetica", 6.2)
            c.setFillColor(COLOR_BLACK)
            c.drawString(left_half_x2, prim_y2, f"{checked} {label}")
            prim_y2 -= 9.5

        # Draw Secondary Indicators
        sec_y = cur_y
        for code, label in secondary_col1:
            checked = "[X]" if code in obs_set else "[ ]"
            c.setFont("Helvetica", 6.2)
            c.setFillColor(COLOR_BLACK)
            c.drawString(right_half_x1, sec_y, f"{checked} {label}")
            sec_y -= 9.5

        sec_y2 = cur_y
        for code, label in secondary_col2:
            checked = "[X]" if code in obs_set else "[ ]"
            c.setFont("Helvetica", 6.2)
            c.setFillColor(COLOR_BLACK)
            c.drawString(right_half_x2, sec_y2, f"{checked} {label}")
            sec_y2 -= 9.5

        # Field Observations Sub-box
        obs_top_y = top_y - box_h + 130
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(box_x, obs_top_y, box_x + box_w, obs_top_y)

        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, obs_top_y - 12, "Field Observations:")

        # Field observation rows
        c.setFont("Helvetica", 7.0)
        c.setFillColor(COLOR_BLACK)

        sw_y = obs_top_y - 25
        sw_yes = "[X]" if self.plot.surface_water_present else "[ ]"
        sw_no = "[ ]" if self.plot.surface_water_present else "[X]"
        sw_d = f"{self.plot.surface_water_depth_in:.1f}" if self.plot.surface_water_depth_in is not None else "None"
        c.drawString(box_x + 12, sw_y, f"Surface Water Present?  Yes {sw_yes}  No {sw_no}   Depth (inches): {sw_d}")

        wt_yes = "[X]" if self.plot.water_table_present else "[ ]"
        wt_no = "[ ]" if self.plot.water_table_present else "[X]"
        wt_d = f"{self.plot.water_table_depth_in:.1f}" if self.plot.water_table_depth_in is not None else "None"
        c.drawString(box_x + 200, sw_y, f"Water Table Present?  Yes {wt_yes}  No {wt_no}   Depth (inches): {wt_d}")

        sat_yes = "[X]" if self.plot.saturation_present else "[ ]"
        sat_no = "[ ]" if self.plot.saturation_present else "[X]"
        sat_d = f"{self.plot.saturation_depth_in:.1f}" if self.plot.saturation_depth_in is not None else "None"
        c.drawString(box_x + 390, sw_y, f"Saturation Present?  Yes {sat_yes}  No {sat_no}   Depth (inches): {sat_d}")

        # Hydrology status confirmation
        hydro_status = "PRESENT" if self.determination.wetland_hydrology.wetland_hydrology_present else "NOT PRESENT"
        prim_count = len(self.determination.wetland_hydrology.primary_indicators)
        sec_count = len(self.determination.wetland_hydrology.secondary_indicators)
        c.setFont("Helvetica-Bold", 7.2)
        c.drawString(
            box_x + 12,
            obs_top_y - 42,
            f"Wetland Hydrology Criteria Met?  {hydro_status}  ({prim_count} Primary, {sec_count} Secondary confirmed)",
        )

        rec_data = self.plot.recorded_data_description or "None available"
        c.setFont("Helvetica", 6.8)
        c.drawString(box_x + 12, obs_top_y - 56, f"Recorded Data (stream gauge, monitoring well, aerial photos): {rec_data}")

        rem_h = self.plot.hydrology_remarks or "; ".join(self.determination.wetland_hydrology.remarks) or "Normal conditions observed."
        c.drawString(box_x + 12, obs_top_y - 70, f"Remarks: {rem_h[:130]}")

        return top_y - box_h

    # =========================================================================
    # PAGE 2 RENDERING
    # =========================================================================

    def _render_page_2(self, c: canvas.Canvas):
        curr_y = self.page_height - self.margin_y

        # Top Sampling Point Header
        curr_y = self._draw_page2_header(c, curr_y)

        # Upper Half: VEGETATION SECTION
        veg_h = 390.0
        self._draw_vegetation_section(c, curr_y, veg_h)
        curr_y -= (veg_h + 6)

        # Lower Half: SOILS SECTION
        soil_h = curr_y - self.margin_y - 15
        self._draw_soils_section(c, curr_y, soil_h)

        # Page 2 Footer
        self._draw_footer(c, page_num=2)

    def _draw_page2_header(self, c: canvas.Canvas, y: float) -> float:
        c.setFont("Helvetica-Bold", 9.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(self.margin_x, y - 10, f"SAMPLING POINT: {self.plot.sampling_point}")
        c.drawRightString(
            self.margin_x + self.content_width,
            y - 10,
            f"PROJECT: {self.plot.project_name} ({self.plot.region.value} Region)",
        )

        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER)
        c.line(self.margin_x, y - 14, self.margin_x + self.content_width, y - 14)
        return y - 18

    def _draw_vegetation_section(self, c: canvas.Canvas, y: float, height: float):
        box_x = self.margin_x
        box_w = self.content_width
        top_y = y

        # Vegetation Outer Box
        c.setLineWidth(1.0)
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_WHITE)
        c.rect(box_x, top_y - height, box_w, height, fill=1, stroke=1)

        # Header Bar
        header_h = 14.0
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(box_x, top_y - header_h, box_w, header_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, top_y - 10, "VEGETATION \u2013 Use scientific names of plants.")

        # Layout: Left column = 4 Strata Tables (width: 360 pt); Right column = Worksheets (width: 198 pt)
        col_w = 360.0
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(box_x + col_w, top_y - header_h, box_x + col_w, top_y - height)

        # Draw Left: 4 Strata Tables
        strata_order = [
            ("Tree Stratum", self.plot.tree_plot_size, "Tree", 4),
            ("Sapling/Shrub Stratum", self.plot.sapling_shrub_plot_size, "Sapling/Shrub", 4),
            ("Herb Stratum", self.plot.herb_plot_size, "Herb", 7),
            ("Woody Vine Stratum", self.plot.woody_vine_plot_size, "Woody Vine", 3),
        ]

        veg_det = self.determination.hydrophytic_vegetation
        s_y = top_y - header_h - 2

        for title, plot_size, key, max_rows in strata_order:
            stratum_res = veg_det.strata_results.get(key)
            species_list = self.plot.strata_vegetation.get(key, [])
            s_y = self._draw_stratum_table(c, box_x + 4, s_y, col_w - 8, title, plot_size or "", species_list, stratum_res, max_rows)

        # Draw Right: Dominance Test, Prevalence Index, Indicators
        right_x = box_x + col_w + 6
        right_w = box_w - col_w - 12
        rw_y = top_y - header_h - 6

        # Dominance Test Worksheet Table
        rw_y = self._draw_dominance_worksheet(c, right_x, rw_y, right_w, veg_det)

        # Prevalence Index Worksheet Table
        rw_y = self._draw_prevalence_worksheet(c, right_x, rw_y, right_w, veg_det)

        # Hydrophytic Vegetation Indicators Checklist
        rw_y = self._draw_hydrophytic_checklist(c, right_x, rw_y, right_w, veg_det)

    def _draw_stratum_table(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        w: float,
        title: str,
        plot_size: str,
        species_list: List[SpeciesCover],
        result: Optional[Any],
        max_rows: int,
    ) -> float:
        # Title bar
        c.setFillColor(COLOR_ACCENT_BG)
        c.rect(x, y - 10, w, 10, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 6.8)
        c.setFillColor(COLOR_NAVY)
        size_str = f" (Plot size: {plot_size})" if plot_size else ""
        c.drawString(x + 2, y - 8, f"{title}{size_str}")

        # Table Column Headers
        th_y = y - 19
        c.setFont("Helvetica-Bold", 6.0)
        c.setFillColor(COLOR_BLACK)
        c.drawString(x + 2, th_y, "Species Scientific Name")
        c.drawString(x + 195, th_y, "Cover %")
        c.drawString(x + 245, th_y, "Dominant?")
        c.drawString(x + 295, th_y, "Ind. Status")

        c.setLineWidth(0.3)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(x, th_y - 2, x + w, th_y - 2)

        # Rows
        row_y = th_y - 9
        row_h = 8.5
        species_dominants = set(sp.taxon.lower() for sp in result.dominants) if result else set()

        rows_to_show = species_list[:max_rows]
        for sp in rows_to_show:
            c.setFont("Helvetica-Oblique", 6.0)
            c.setFillColor(COLOR_BLACK)
            # Clean scientific name
            c.drawString(x + 2, row_y, sp.taxon[:42])

            c.setFont("Helvetica", 6.0)
            c.drawString(x + 202, row_y, f"{sp.percent_cover:.1f}%")

            is_dom = "Yes" if (sp.taxon.lower() in species_dominants or sp.is_dominant) else "No"
            c.drawString(x + 255, row_y, is_dom)

            ind = sp.indicator_status or "NL"
            c.drawString(x + 305, row_y, ind)

            c.setLineWidth(0.2)
            c.setStrokeColor(HexColor("#CBD5E1"))
            c.line(x, row_y - 1.5, x + w, row_y - 1.5)
            row_y -= row_h

        # Empty filler rows if few species
        empty_count = max(0, min(2, max_rows - len(rows_to_show)))
        for _ in range(empty_count):
            row_y -= (row_h - 2)

        # Summary line for 50% and 20% thresholds & Total Cover
        tot_cover = result.total_cover if result else sum(s.percent_cover for s in species_list)
        t50 = result.threshold_50 if result else (0.5 * tot_cover)
        t20 = result.threshold_20 if result else (0.2 * tot_cover)

        c.setFont("Helvetica-Bold", 5.8)
        c.setFillColor(COLOR_NAVY)
        c.drawString(
            x + 2,
            row_y,
            f"50% of total cover: {t50:.1f}   20% of total cover: {t20:.1f}   Total Cover = {tot_cover:.1f}%",
        )
        c.setLineWidth(0.4)
        c.setStrokeColor(COLOR_BORDER)
        c.line(x, row_y - 2, x + w, row_y - 2)

        return row_y - 6

    def _draw_dominance_worksheet(self, c: canvas.Canvas, x: float, y: float, w: float, veg_det: Any) -> float:
        c.setFont("Helvetica-Bold", 7.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(x, y, "Dominance Test Worksheet:")

        c.setFont("Helvetica", 6.0)
        c.setFillColor(COLOR_BLACK)
        y -= 10
        c.drawString(x + 2, y, f"Number of Dominant Species That Are OBL, FACW, or FAC: (A)")
        c.drawRightString(x + w - 4, y, str(veg_det.dominance_test_a))

        y -= 9
        c.drawString(x + 2, y, f"Total Number of Dominant Species Across All Strata: (B)")
        c.drawRightString(x + w - 4, y, str(veg_det.dominance_test_b))

        y -= 9
        c.setFont("Helvetica-Bold", 6.2)
        c.drawString(x + 2, y, f"Percent of Dominant Species That Are OBL, FACW, or FAC (A/B):")
        pct_str = f"{veg_det.dominance_test_percent:.1f}%"
        c.drawRightString(x + w - 4, y, pct_str)

        # Pass / Fail badge
        y -= 8
        c.setLineWidth(0.3)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(x, y, x + w, y)
        return y - 6

    def _draw_prevalence_worksheet(self, c: canvas.Canvas, x: float, y: float, w: float, veg_det: Any) -> float:
        c.setFont("Helvetica-Bold", 7.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(x, y, "Prevalence Index Worksheet:")

        # Table header
        y -= 9
        c.setFont("Helvetica-Bold", 5.8)
        c.drawString(x + 2, y, "Total % Cover of:")
        c.drawRightString(x + w - 4, y, "Multiply by:")

        # Compute stratum breakdown weights
        obl_c = sum(sp.percent_cover for sp in veg_det.all_dominants if sp.normalized_indicator == "OBL")
        facw_c = sum(sp.percent_cover for sp in veg_det.all_dominants if sp.normalized_indicator == "FACW")
        fac_c = sum(sp.percent_cover for sp in veg_det.all_dominants if sp.normalized_indicator == "FAC")
        facu_c = sum(sp.percent_cover for sp in veg_det.all_dominants if sp.normalized_indicator == "FACU")
        upl_c = sum(sp.percent_cover for sp in veg_det.all_dominants if sp.normalized_indicator in ("UPL", "NL"))

        tiers = [
            ("OBL species", obl_c, 1),
            ("FACW species", facw_c, 2),
            ("FAC species", fac_c, 3),
            ("FACU species", facu_c, 4),
            ("UPL species", upl_c, 5),
        ]

        c.setFont("Helvetica", 6.0)
        c.setFillColor(COLOR_BLACK)
        for name, cov, mult in tiers:
            y -= 8.5
            c.drawString(x + 2, y, f"{name}: {cov:.1f}")
            c.drawRightString(x + w - 4, y, f"x {mult} = {cov * mult:.1f}")

        # Column totals and PI
        pi_val = veg_det.prevalence_index
        pi_str = f"{pi_val:.2f}" if pi_val is not None else "N/A"
        y -= 9
        c.setFont("Helvetica-Bold", 6.2)
        c.setFillColor(COLOR_NAVY)
        c.drawString(x + 2, y, "Prevalence Index (B/A):")
        c.drawRightString(x + w - 4, y, pi_str)

        y -= 6
        c.setLineWidth(0.3)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(x, y, x + w, y)
        return y - 6

    def _draw_hydrophytic_checklist(self, c: canvas.Canvas, x: float, y: float, w: float, veg_det: Any) -> float:
        c.setFont("Helvetica-Bold", 7.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(x, y, "Hydrophytic Vegetation Indicators:")

        y -= 9
        indicators = [
            ("Rapid Test for Hydrophytic Vegetation", veg_det.rapid_test_passed),
            ("Dominance Test is > 50.0%", veg_det.dominance_test_passed),
            ("Prevalence Index is <= 3.00", veg_det.prevalence_index_passed or False),
            ("Morphological Adaptations", any(s.has_morphological_adaptations for s in veg_det.all_dominants)),
            ("Problematic Hydrophytic Vegetation", self.plot.vegetation_problematic),
        ]

        for label, checked in indicators:
            c.setFont("Helvetica", 6.0)
            c.setFillColor(COLOR_BLACK)
            cb = "[X]" if checked else "[ ]"
            c.drawString(x + 2, y, f"{cb}  {label}")
            y -= 8.5

        # Final Hydrophytic Vegetation Present Box
        y -= 2
        c.setFillColor(COLOR_PASS_BG if veg_det.hydrophytic_vegetation_present else COLOR_FAIL_BG)
        c.setStrokeColor(COLOR_BORDER)
        c.rect(x, y - 14, w - 4, 14, fill=1, stroke=1)

        c.setFont("Helvetica-Bold", 6.8)
        c.setFillColor(HexColor("#14532D") if veg_det.hydrophytic_vegetation_present else HexColor("#7F1D1D"))
        res_text = "HYDROPHYTIC VEGETATION: YES" if veg_det.hydrophytic_vegetation_present else "HYDROPHYTIC VEGETATION: NO"
        c.drawCentredString(x + ((w - 4) / 2.0), y - 10, res_text)

        return y - 18

    def _draw_soils_section(self, c: canvas.Canvas, y: float, height: float):
        box_x = self.margin_x
        box_w = self.content_width
        top_y = y

        # Section Outer Box
        c.setLineWidth(1.0)
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_WHITE)
        c.rect(box_x, top_y - height, box_w, height, fill=1, stroke=1)

        # Header Bar
        header_h = 14.0
        c.setFillColor(COLOR_HEADER_BG)
        c.rect(box_x, top_y - header_h, box_w, header_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, top_y - 10, "SOIL \u2013 Profile Description (Soil Pit Evaluation)")

        # Soil Profile Table Headers
        th_y = top_y - header_h - 10
        c.setFont("Helvetica-Bold", 6.2)
        c.setFillColor(COLOR_BLACK)
        c.drawString(box_x + 6, th_y, "Depth (in/cm)")
        c.drawString(box_x + 70, th_y, "Matrix Color (Munsell)")
        c.drawString(box_x + 160, th_y, "Redox Features (Munsell, %, Dist/Type)")
        c.drawString(box_x + 360, th_y, "Texture")
        c.drawString(box_x + 440, th_y, "Remarks")

        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(box_x + 4, th_y - 2, box_x + box_w - 4, th_y - 2)

        # Horizon Rows
        row_y = th_y - 9
        row_h = 8.5
        horizons = self.plot.soil_horizons[:5]  # show up to 5 layers cleanly

        for h in horizons:
            c.setFont("Helvetica", 6.0)
            c.setFillColor(COLOR_BLACK)
            depth_str = f"{h.top_depth_cm:.0f} - {h.bottom_depth_cm:.0f} cm"
            c.drawString(box_x + 6, row_y, depth_str)

            matrix_str = f"{h.matrix_hue} {h.matrix_value:.0f}/{h.matrix_chroma:.0f} ({100 - h.redox_percent:.0f}%)"
            c.drawString(box_x + 70, row_y, matrix_str)

            if h.redox_percent > 0:
                redox_str = f"{h.redox_hue or '10YR'} {h.redox_value or 5:.0f}/{h.redox_chroma or 6:.0f} ({h.redox_percent:.0f}%, {h.redox_distinctness})"
            else:
                redox_str = "None"
            c.drawString(box_x + 160, row_y, redox_str)

            c.drawString(box_x + 360, row_y, h.texture[:14])
            c.drawString(box_x + 440, row_y, (h.name or "Horizon")[:22])

            c.setLineWidth(0.2)
            c.setStrokeColor(HexColor("#CBD5E1"))
            c.line(box_x + 4, row_y - 1.5, box_x + box_w - 4, row_y - 1.5)
            row_y -= row_h

        # Empty fallback rows if no horizons
        if not horizons:
            c.setFont("Helvetica-Oblique", 6.0)
            c.drawString(box_x + 6, row_y, "No specific horizons logged. Field evaluation applied.")
            row_y -= row_h

        # Divider between Profile and Hydric Soil Indicators
        ind_top_y = row_y - 4
        c.setLineWidth(0.5)
        c.setStrokeColor(COLOR_BORDER_LIGHT)
        c.line(box_x + 4, ind_top_y, box_x + box_w - 4, ind_top_y)

        # Hydric Soil Indicators Checklist (2 columns)
        c.setFont("Helvetica-Bold", 6.8)
        c.setFillColor(COLOR_NAVY)
        c.drawString(box_x + 6, ind_top_y - 9, "Hydric Soil Indicators (NRCS Field Indicators v8.2):")

        confirmed_soils = set(self.determination.hydric_soils.confirmed_indicators)
        is_agcp = self.plot.region == RegionEnum.AGCP

        col1_inds = [
            ("A1", "Histosol (A1)"),
            ("A2", "Histic Epipedon (A2)"),
            ("A3", "Black Histic (A3)"),
            ("A4", "Hydrogen Sulfide (A4)"),
            ("A11", "Depleted Below Dark (A11)"),
            ("A12", "Thick Dark Surface (A12)"),
            ("S4", "Sandy Gleyed Matrix (S4)"),
            ("S5", "Sandy Redox (S5)"),
        ]

        col2_inds = [
            ("S6", "Stripped Matrix (S6)"),
            ("F2", "Loamy Gleyed Matrix (F2)"),
            ("F3", "Depleted Matrix (F3)"),
            ("F6", "Redox Dark Surface (F6)"),
            ("F7", "Depleted Dark Surface (F7)"),
            ("F19" if not is_agcp else "F20", "Piedmont Floodplain (F19)" if not is_agcp else "Anom. Bright Loamy (F20)"),
            ("Problem", "Indicators for Problematic Soils"),
        ]

        c_y = ind_top_y - 18
        for code, label in col1_inds:
            cb = "[X]" if code in confirmed_soils else "[ ]"
            c.setFont("Helvetica", 5.8)
            c.setFillColor(COLOR_BLACK)
            c.drawString(box_x + 6, c_y, f"{cb} {label}")
            c_y -= 8.0

        c_y2 = ind_top_y - 18
        for code, label in col2_inds:
            cb = "[X]" if code in confirmed_soils else "[ ]"
            c.setFont("Helvetica", 5.8)
            c.setFillColor(COLOR_BLACK)
            c.drawString(box_x + 220, c_y2, f"{cb} {label}")
            c_y2 -= 8.0

        # Soil Determination Box & Restrictive Layer
        res_box_x = box_x + 400
        res_box_y = ind_top_y - 65
        res_box_w = 158
        res_box_h = 56

        soil_ok = self.determination.hydric_soils.hydric_soil_present
        c.setFillColor(COLOR_PASS_BG if soil_ok else COLOR_FAIL_BG)
        c.setStrokeColor(COLOR_BORDER)
        c.rect(res_box_x, res_box_y, res_box_w, res_box_h, fill=1, stroke=1)

        c.setFont("Helvetica-Bold", 7.2)
        c.setFillColor(HexColor("#14532D") if soil_ok else HexColor("#7F1D1D"))
        res_txt = "HYDRIC SOIL: YES" if soil_ok else "HYDRIC SOIL: NO"
        c.drawCentredString(res_box_x + (res_box_w / 2.0), res_box_y + 42, res_txt)

        conf_str = ", ".join(confirmed_soils) if confirmed_soils else "None"
        c.setFont("Helvetica", 5.8)
        c.setFillColor(COLOR_BLACK)
        c.drawCentredString(res_box_x + (res_box_w / 2.0), res_box_y + 30, f"Confirmed: {conf_str}")

        restr_type = self.plot.restrictive_layer_type or "None"
        restr_d = f"{self.plot.restrictive_layer_depth_in:.1f} in" if self.plot.restrictive_layer_depth_in else "N/A"
        c.drawString(res_box_x + 6, res_box_y + 14, f"Restrictive Layer: {restr_type}")
        c.drawString(res_box_x + 6, res_box_y + 4, f"Depth: {restr_d}")

        # Soil Remarks Line
        s_rem = self.plot.soil_remarks or "; ".join(self.determination.hydric_soils.remarks) or "Profile evaluated to standard depth."
        c.setFont("Helvetica", 6.0)
        c.drawString(box_x + 6, top_y - height + 6, f"Remarks: {s_rem[:130]}")

    # =========================================================================
    # COMMON UTILITIES
    # =========================================================================

    def _draw_field(self, c: canvas.Canvas, x: float, y: float, label: str, val: str, width: float, bold_val: bool = False):
        c.setFont("Helvetica", 7.0)
        c.setFillColor(COLOR_BLACK)
        c.drawString(x, y, label)
        lw = c.stringWidth(label, "Helvetica", 7.0)

        c.setFont("Helvetica-Bold" if bold_val else "Helvetica", 7.0)
        c.drawString(x + lw + 3, y, str(val)[:45])

    def _draw_footer(self, c: canvas.Canvas, page_num: int):
        c.setFont("Helvetica", 6.5)
        c.setFillColor(COLOR_BORDER)
        c.drawString(
            self.margin_x,
            self.margin_y - 12,
            f"USACE Regional Supplement ({self.plot.region.value} Version 2.0) \u2013 Submission-Ready Official Form",
        )
        c.drawRightString(
            self.margin_x + self.content_width,
            self.margin_y - 12,
            f"Page {page_num} of 2",
        )

    def _draw_watermark(self, c: canvas.Canvas):
        if not self.watermark:
            return
        c.saveState()
        c.setFont("Helvetica-Bold", 54)
        c.setFillColor(HexColor("#94A3B8"), alpha=0.18)
        c.translate(self.page_width / 2.0, self.page_height / 2.0)
        c.rotate(45)
        c.drawCentredString(0, 0, self.watermark.upper())
        c.restoreState()


def render_usace_pdf(plot_data: USACEPlotExportData, watermark: Optional[str] = None) -> bytes:
    """Convenience helper to render a single submission-ready 2-page USACE PDF."""
    builder = USACEDataFormPDFBuilder(plot_data=plot_data, watermark=watermark)
    return builder.generate()


def render_usace_project_pdf(plots: List[USACEPlotExportData], watermark: Optional[str] = None) -> bytes:
    """Render and concatenate multiple USACE 2-page forms into a single multi-plot PDF."""
    if not plots:
        raise ValueError("Cannot generate project PDF from empty plot list")

    writer = PdfWriter()
    for plot in plots:
        single_pdf_bytes = render_usace_pdf(plot, watermark=watermark)
        reader = PdfReader(io.BytesIO(single_pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)

    writer.add_metadata({
        "/Title": f"USACE Regional Supplement Data Forms - Project Report ({len(plots)} plots)",
        "/Subject": "Consolidated Wetland Determination Data Forms",
        "/Producer": "Palustra Multi-Plot Exporter",
    })

    out_buffer = io.BytesIO()
    writer.write(out_buffer)
    consolidated = out_buffer.getvalue()
    out_buffer.close()
    return consolidated
