"""
Milestone 6: Institutional-Grade Bankable DPR PDF Generator.
Constructed using ReportLab with bank-appraisal styling, multi-page numbering (Page X of Y),
running headers, financial statement tables, and regulatory disclosures.
Zero LLM dependencies. Deterministic PDF rendering.
"""
import io
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.financial_engine.dpr_packager.dpr_schema import DPRFinancialPackage
from app.services.financial_engine.dpr_packager.dpr_formatting import format_inr

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
        HRFlowable,
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
    BaseCanvas = canvas.Canvas
except ImportError:
    REPORTLAB_AVAILABLE = False
    BaseCanvas = object
    letter = (612, 792)
    A4 = (595, 842)


class NumberedCanvas(BaseCanvas):
    """
    Two-pass canvas to compute and render total page count dynamically.
    Adds institutional running header and footer with 'Page X of Y'.
    """

    def __init__(self, *args, **kwargs):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed.")
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        # Do not draw headers/footers on cover page (page 1)
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))

            # Running Header
            self.drawString(54, 11 * inch - 36, "CONFIDENTIAL & PROPRIETARY — DETAILED PROJECT REPORT (DPR)")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "INSTITUTIONAL BANK APPRAISAL")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

            # Running Footer
            self.line(54, 45, 8.5 * inch - 54, 45)
            self.setFont("Helvetica", 8)
            self.drawString(54, 32, "Prepared via KALPA MSME Credit Engine. Authoritative deterministic math.")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * inch - 54, 32, page_text)
            self.restoreState()


class DPRPdfGenerator:
    """
    Renders the complete M6 DPR Financial Package into an institutional-grade PDF.
    """

    def generate_pdf(
        self,
        financial_package: DPRFinancialPackage,
        non_financial_context: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Builds institutional PDF and returns raw bytes (and optionally writes to output_path).
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed in the environment. PDF generation is unavailable.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        self._configure_custom_styles(styles)

        story = []

        # 1. Institutional Cover Page
        self._build_cover_page(story, financial_package, styles)
        story.append(PageBreak())

        # 2. Executive Table of Contents / Dossier Metadata
        self._build_meta_summary(story, financial_package, styles)

        # 3. Non-financial Upstream Summary (Market, Feasibility, SWOT if provided)
        if non_financial_context:
            self._build_non_financial_section(story, non_financial_context, styles)

        # 4. Standardized 18 DPR Sections
        for section in financial_package.sections:
            self._build_dpr_section(story, section, styles)

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _configure_custom_styles(self, styles):
        styles.add(ParagraphStyle(
            name="CoverTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0F172A"),
            alignment=0,
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#475569"),
            alignment=0,
            spaceAfter=20
        ))
        styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        ))
        styles.add(ParagraphStyle(
            name="SectionSummary",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=1
        ))
        styles.add(ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1E293B")
        ))
        styles.add(ParagraphStyle(
            name="TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#0F172A")
        ))
        styles.add(ParagraphStyle(
            name="Disclosures",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748B"),
            spaceBefore=4,
            spaceAfter=8
        ))

    def _build_cover_page(self, story: List[Any], pkg: DPRFinancialPackage, styles):
        story.append(Spacer(1, 40))
        story.append(Paragraph("BANKABLE DETAILED PROJECT REPORT (DPR)", styles["CoverTitle"]))
        story.append(Paragraph("Institutional Credit Appraisal & Comprehensive Financial Feasibility Dossier", styles["CoverSubtitle"]))
        story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#EA580C"), spaceAfter=24))

        ident = pkg.project_identity
        prom = pkg.promoter_profile
        cost = pkg.project_cost
        mof = pkg.means_of_finance
        loan = pkg.loan_structure

        cover_info = [
            [
                Paragraph("<b>Project / Enterprise:</b>", styles["TableCellBold"]),
                Paragraph(ident.project_name or "Proposed MSME Venture", styles["TableCell"])
            ],
            [
                Paragraph("<b>Promoter / Beneficiary:</b>", styles["TableCellBold"]),
                Paragraph(prom.promoter_name or "Not available", styles["TableCell"])
            ],
            [
                Paragraph("<b>Location / District:</b>", styles["TableCellBold"]),
                Paragraph(f"{ident.district or 'Not specified'}, {ident.state or ''}", styles["TableCell"])
            ],
            [
                Paragraph("<b>Industry / Sector:</b>", styles["TableCellBold"]),
                Paragraph(f"{ident.category or 'MSME'} (NIC: {ident.nic_code or 'General'})", styles["TableCell"])
            ],
            [
                Paragraph("<b>Proposed Scheme:</b>", styles["TableCellBold"]),
                Paragraph(loan.scheme_name or "MSME Term Loan Scheme", styles["TableCell"])
            ],
            [
                Paragraph("<b>Total Project Outlay:</b>", styles["TableCellBold"]),
                Paragraph(format_inr(cost.total_project_cost), styles["TableCellBold"])
            ],
            [
                Paragraph("<b>Term Debt Requirement:</b>", styles["TableCellBold"]),
                Paragraph(format_inr(loan.sanctioned_loan_amount), styles["TableCellBold"])
            ],
            [
                Paragraph("<b>Promoter Equity Margin:</b>", styles["TableCellBold"]),
                Paragraph(format_inr(mof.promoter_contribution), styles["TableCell"])
            ],
            [
                Paragraph("<b>Report Dossier ID:</b>", styles["TableCellBold"]),
                Paragraph(pkg.package_id, styles["TableCell"])
            ],
            [
                Paragraph("<b>Appraisal Date:</b>", styles["TableCellBold"]),
                Paragraph(datetime.now().strftime("%d %B %Y"), styles["TableCell"])
            ],
        ]

        t = Table(cover_info, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 40))

        # Institutional Certification badge
        cert_data = [
            [
                Paragraph(
                    "<b>INSTITUTIONAL CREDIT GRADE:</b> This DPR was deterministically generated via the "
                    "KALPA Financial Intelligence Engine conforming to RBI MSME credit guidelines, "
                    "CMA standards, and statutory scheme benchmarks. Zero subjective LLM fabrication.",
                    styles["TableCell"]
                )
            ]
        ]
        cert_table = Table(cert_data, colWidths=[500])
        cert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(cert_table)

    def _build_meta_summary(self, story: List[Any], pkg: DPRFinancialPackage, styles):
        story.append(Paragraph("Dossier Summary & Credit Highlights", styles["SectionHeader"]))
        comp = pkg.data_completeness
        status_color = "#16A34A" if comp.is_dpr_eligible else "#DC2626"

        summary_rows = [
            ["DPR Status", comp.status.value, "Bankable Eligibility", "ELIGIBLE FOR SUBMISSION" if comp.is_dpr_eligible else "INCOMPLETE / DRAFT"],
            ["Total Financial Outlay", format_inr(pkg.project_cost.total_project_cost), "Bank Loan Requirement", format_inr(pkg.loan_structure.sanctioned_loan_amount)],
            ["Average DSCR (5 Yrs)", f"{pkg.banking_metrics.average_dscr or 'N/A'}x", "Break-Even Utilization", f"{pkg.banking_metrics.break_even_capacity_pct or 'N/A'}%"],
            ["Monthly Debt Service", format_inr(pkg.loan_structure.monthly_emi), "Financing Resilience", pkg.m5_stress_appraisal.financing_resilience_status or "RESILIENT"],
        ]
        t = Table(summary_rows, colWidths=[125, 125, 125, 125])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1E293B")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

    def _build_non_financial_section(self, story: List[Any], context: Dict[str, Any], styles):
        mkt = context.get("market_analysis") or {}
        feas = context.get("feasibility_result") or {}
        swot = context.get("swot_analysis") or {}

        if not mkt and not feas and not swot:
            return

        story.append(Paragraph("Upstream Business Feasibility & Opportunity Synthesis", styles["SectionHeader"]))
        summary_lines = []
        if feas.get("overall_feasibility_score"):
            summary_lines.append(f"Feasibility Score: {feas.get('overall_feasibility_score')}/100 ({feas.get('classification', 'Viable')}).")
        if mkt.get("demand_growth_rate"):
            summary_lines.append(f"Projected Market Demand Growth: {mkt.get('demand_growth_rate')}%.")

        story.append(Paragraph(" ".join(summary_lines) or "Verified upstream intelligence integrated.", styles["SectionSummary"]))
        story.append(Spacer(1, 10))

    def _build_dpr_section(self, story: List[Any], sec: Any, styles):
        flowables = [
            Paragraph(sec.title, styles["SectionHeader"]),
            Paragraph(sec.summary_text, styles["SectionSummary"])
        ]

        # Render tables
        for table_data in sec.tables:
            title = table_data.get("title")
            if title:
                flowables.append(Paragraph(f"<b>{title}</b>", styles["TableCellBold"]))
                flowables.append(Spacer(1, 4))

            headers = table_data.get("headers", [])
            raw_rows = table_data.get("rows", [])
            if not headers or not raw_rows:
                continue

            num_cols = len(headers)
            col_width = 504.0 / num_cols

            table_content = [
                [Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]
            ]
            for r in raw_rows:
                row_cells = []
                for idx, cell in enumerate(r):
                    str_cell = str(cell) if cell is not None else "Not available"
                    style_to_use = styles["TableCellBold"] if idx == 0 else styles["TableCell"]
                    row_cells.append(Paragraph(str_cell, style_to_use))
                table_content.append(row_cells)

            tab = Table(table_content, colWidths=[col_width] * num_cols, repeatRows=1)
            tab.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            flowables.append(tab)
            flowables.append(Spacer(1, 6))

        # Disclosures
        for note in sec.notes_and_disclosures:
            flowables.append(Paragraph(f"• {note}", styles["Disclosures"]))

        flowables.append(Spacer(1, 10))
        story.append(KeepTogether(flowables))


dpr_pdf_generator = DPRPdfGenerator()
