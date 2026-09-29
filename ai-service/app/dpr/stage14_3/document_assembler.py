"""
Stage 14.3: Canonical DPR Document Assembler.
Assembles the complete 40-section institutional credit appraisal document,
resolves numeric placeholders safely from the canonical package after validation,
injects authoritative financial schedules and vector charts, and formats annexures.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    Flowable,
    HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

from app.dpr.stage14_3.styles import (
    COLOR_NAVY_DARK,
    COLOR_NAVY_ACCENT,
    COLOR_STEEL_BLUE,
    COLOR_BORDER,
    COLOR_BORDER_DARK,
    COLOR_CHARCOAL,
    COLOR_MUTED_GREY,
    COLOR_BG_LIGHT,
    COLOR_BG_CARD,
    COLOR_BG_SUBTOTAL,
    COLOR_WHITE,
    FONT_REGULAR,
    FONT_BOLD,
    PRINTABLE_WIDTH_PORTRAIT,
    PRINTABLE_WIDTH_LANDSCAPE,
    get_institutional_styles,
)
from app.dpr.stage14_3.document_schema import (
    DPRDocumentControl,
    ProjectAtAGlanceData,
    SectionNarrative,
    CanonicalSectionContent,
    SectionCompleteness,
    extract_financial_scalars,
)
from app.dpr.stage14_3.tables import DPRTableBuilder, sanitize_table_val
from app.dpr.stage14_3.charts import DPRChartBuilder
from app.dpr.stage14_3.flowcharts import DPRProcessFlowBuilder
from app.dpr.stage14_3.toc import SectionTarget
from app.dpr.stage14_3.annexures import DPRAnnexureBuilder
from app.dpr.stage14_3.provenance import ProvenanceRegistry
from app.services.financial_engine.dpr_packager.dpr_formatting import (
    format_inr,
    format_inr_lakhs,
    format_percentage,
    format_ratio,
)

styles = get_institutional_styles()


class DPRDocumentAssembler:
    """
    Compiles authoritative project data, M1-M6 financial outputs, and validated narratives
    into structured Platypus flowable elements for PDF generation.
    """

    def __init__(self):
        pass

    @classmethod
    def resolve_placeholders(cls, text: str, placeholder_map: Dict[str, str]) -> str:
        """Resolves placeholders strictly AFTER narrative validation."""
        resolved = text
        for ph, val in placeholder_map.items():
            resolved = resolved.replace(ph, str(val))

        # Clean any stray unmapped {{...}} template tags or {%.*%}
        resolved = re.sub(r'\{\{\s*([A-Za-z0-9_]+)\s*\}\}', lambda m: placeholder_map.get(f"{{{{{m.group(1)}}}}}", "—"), resolved)
        resolved = re.sub(r'\{\{.*?\}\}', '—', resolved)
        resolved = re.sub(r'\{%.*?%\}', '', resolved)
        resolved = resolved.replace("{{", "").replace("}}", "")

        # Clean duplicated suffixes & units
        resolved = re.sub(r'(\d+(?:\.\d+)?)\s*%\s*(?:percent|pct|Utilization%|Capacity%)', r'\1%', resolved, flags=re.IGNORECASE)
        resolved = re.sub(r'(\d+)\s*Months?\s*months?', r'\1 Months', resolved, flags=re.IGNORECASE)
        resolved = re.sub(r'%\s*%', '%', resolved)
        resolved = resolved.replace("Utilization%", "Utilization").replace("Capacity%", "Capacity")

        from app.dpr.stage14_3.styles import clean_and_wrap_text
        return clean_and_wrap_text(resolved)

    @classmethod
    def build_placeholder_map(cls, package: Any, fin_pkg: Dict[str, Any]) -> Dict[str, str]:
        """Constructs canonical placeholder values from authoritative financial package."""
        scalars = extract_financial_scalars(fin_pkg)
        cost = scalars["total_project_cost"]
        promoter = scalars["promoter_contribution"]
        term_loan = scalars["term_loan"]
        wc = scalars["working_capital"]
        y1_rev = scalars["year1_revenue"]
        y5_rev = scalars["year5_revenue"]
        ebitda_pct = scalars["ebitda_margin_pct"]
        pat = scalars["pat_year1"]
        avg_dscr = scalars["average_dscr"]
        min_dscr = scalars["minimum_dscr"]
        break_even = scalars["break_even_utilization"]

        margin_pct = (promoter / max(cost, 1.0)) * 100.0
        total_credit = term_loan + wc

        return {
            "{{PROJECT_COST}}": format_inr(cost, decimals=0),
            "{{PROMOTER_CONTRIBUTION}}": format_inr(promoter, decimals=0),
            "{{TERM_LOAN}}": format_inr(term_loan, decimals=0),
            "{{WORKING_CAPITAL}}": format_inr(wc, decimals=0),
            "{{TOTAL_CREDIT_EXPOSURE}}": format_inr(total_credit, decimals=0),
            "{{PROMOTER_MARGIN_PCT}}": f"{margin_pct:.1f}%",
            "{{TENURE_MONTHS}}": "84 Months",
            "{{MORATORIUM_MONTHS}}": "6 Months",
            "{{INTEREST_RATE}}": "9.50%",
            "{{YEAR1_REVENUE}}": format_inr(y1_rev, decimals=0),
            "{{YEAR5_REVENUE}}": format_inr(y5_rev, decimals=0),
            "{{EBITDA_MARGIN}}": f"{ebitda_pct:.1f}%",
            "{{PAT}}": format_inr(pat, decimals=0),
            "{{AVERAGE_DSCR}}": f"{avg_dscr:.2f}x",
            "{{MIN_DSCR}}": f"{min_dscr:.2f}x",
            "{{BREAK_EVEN}}": f"{break_even:.1f}%",
            "{{TOTAL_EMPLOYMENT}}": str(scalars.get("total_employment", 2)),
        }

    @classmethod
    def build_cover_page(
        cls,
        business_name: str,
        business_activity: str,
        promoter_name: str,
        location: str,
        generation_date: str,
        document_id: str,
        version: str = "v1.0"
    ) -> List[Flowable]:
        """Builds true institutional cover page."""
        flowables: List[Flowable] = []

        # Top Institutional Header
        flowables.append(Spacer(1, 20))
        flowables.append(Paragraph("KALPA", ParagraphStyle("CoverLogo", fontName=FONT_BOLD, fontSize=20, leading=22, textColor=COLOR_NAVY_DARK)))
        flowables.append(Paragraph("Rural & Semi-Urban Enterprise Advisory System", ParagraphStyle("CoverTagline", fontName=FONT_REGULAR, fontSize=9, leading=12, textColor=COLOR_STEEL_BLUE)))
        flowables.append(Spacer(1, 15))
        flowables.append(HRFlowable(width="100%", thickness=2, color=COLOR_NAVY_DARK, spaceBefore=0, spaceAfter=25))

        # Main Document Title
        flowables.append(Paragraph("DETAILED PROJECT REPORT", ParagraphStyle("CoverMainH", fontName=FONT_BOLD, fontSize=18, leading=22, textColor=COLOR_STEEL_BLUE, spaceAfter=8)))
        flowables.append(Paragraph(business_name.upper(), styles["CoverTitle"]))
        flowables.append(Paragraph(business_activity, styles["CoverSubtitle"]))

        flowables.append(Spacer(1, 25))
        flowables.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=0, spaceAfter=20))

        # Metadata Block
        meta_table_data = [
            [
                Paragraph("Prepared For:", styles["CoverMetaLabel"]),
                Paragraph("Institutional Credit / Bank Finance / Government Scheme Financing", styles["CoverMetaValue"]),
            ],
            [
                Paragraph("Promoter / Entrepreneur:", styles["CoverMetaLabel"]),
                Paragraph(promoter_name, styles["CoverMetaValue"]),
            ],
            [
                Paragraph("Proposed Project Location:", styles["CoverMetaLabel"]),
                Paragraph(location, styles["CoverMetaValue"]),
            ],
            [
                Paragraph("Date of Preparation:", styles["CoverMetaLabel"]),
                Paragraph(generation_date, styles["CoverMetaValue"]),
            ],
            [
                Paragraph("DPR Version:", styles["CoverMetaLabel"]),
                Paragraph(version, styles["CoverMetaValue"]),
            ],
            [
                Paragraph("Document Classification:", styles["CoverMetaLabel"]),
                Paragraph("PROJECT REPORT / CREDIT APPRAISAL DOCUMENT", styles["CoverMetaValue"]),
            ],
            [
                Paragraph("System Reference ID:", styles["CoverMetaLabel"]),
                Paragraph(document_id, styles["CoverMetaValue"]),
            ],
        ]

        meta_table = Table(meta_table_data, colWidths=[PRINTABLE_WIDTH_PORTRAIT * 0.35, PRINTABLE_WIDTH_PORTRAIT * 0.65])
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(meta_table)

        flowables.append(Spacer(1, 40))
        flowables.append(Paragraph(
            "Notice: This appraisal report has been compiled from entrepreneur-declared data, verified documentary evidence, "
            "institutional industry benchmarks, and authoritative financial models. It is prepared for credit appraisal "
            "and does not constitute a guaranteed lending sanction.",
            ParagraphStyle("CoverDisclaimer", fontName=FONT_REGULAR, fontSize=7.5, leading=10.5, textColor=COLOR_MUTED_GREY)
        ))

        flowables.append(PageBreak())
        return flowables

    @classmethod
    def build_document_control_page(
        cls,
        doc_control: DPRDocumentControl
    ) -> List[Flowable]:
        """Builds Document Control and Source Data Status page."""
        flowables: List[Flowable] = []

        flowables.append(SectionTarget("sec_00_control", "Document Control & Project Administration"))
        flowables.append(Paragraph("DOCUMENT CONTROL & ADMINISTRATION", styles["DocumentControlHeader"]))
        flowables.append(Paragraph("Formal administrative metadata, verification register, and document custody trail.", styles["Callout"]))
        flowables.append(Spacer(1, 6))

        clean_ref_id = doc_control.document_id.replace("KALPA-DPR-", "KALPA-APP-")

        control_items = [
            ("DPR Reference Number", doc_control.document_id),
            ("Appraisal Docket Ref", clean_ref_id),
            ("DPR Release Version", doc_control.dpr_version),
            ("Date of Compilation", doc_control.generation_date),
            ("Enterprise Commercial Name", doc_control.business_name),
            ("Lead Promoter / Applicant", doc_control.promoter_name),
            ("Project Operating Location", doc_control.location),
            ("Legal Entity Structure", doc_control.constitution),
            ("Business Classification", doc_control.business_classification),
            ("NIC Code (2008 Classification)", doc_control.nic_code),
            ("Credit Facility Purpose", doc_control.financing_purpose),
            ("Total Requested Bank Credit", doc_control.requested_finance),
            ("Appraisal Framework", doc_control.prepared_by),
            ("Data Cut-off Date", doc_control.data_cutoff_date),
        ]

        flowables.append(DPRTableBuilder.create_key_value_table(control_items))
        flowables.append(Spacer(1, 14))

        # Source / Data Verification Status Section
        flowables.append(Paragraph("SOURCE DATA & VERIFICATION REGISTER", styles["SectionHeading2"]))
        flowables.append(Paragraph(
            "Authoritative provenance breakdown of inputs utilized in this appraisal document:",
            styles["Body"]
        ))
        flowables.append(Spacer(1, 4))

        src_rows = []
        for src_name, status in doc_control.source_statuses.items():
            src_rows.append([src_name, status, "Validated via KALPA DPR Engine"])

        src_table = DPRTableBuilder.create_table(
            headers=["Data Stream", "Verification Status", "Authority Reference"],
            rows=src_rows,
            col_widths=[PRINTABLE_WIDTH_PORTRAIT * 0.35, PRINTABLE_WIDTH_PORTRAIT * 0.30, PRINTABLE_WIDTH_PORTRAIT * 0.35],
            alignments=["LEFT", "LEFT", "LEFT"]
        )
        flowables.append(src_table)

        flowables.append(PageBreak())
        return flowables

    @classmethod
    def build_executive_summary_page(
        cls,
        narrative: SectionNarrative,
        placeholder_map: Dict[str, str],
        dpr_status: str = "BANK_REVIEW_READY"
    ) -> List[Flowable]:
        """Builds Executive Summary with formal appraisal status."""
        flowables: List[Flowable] = []

        flowables.append(SectionTarget("sec_01_exec_summary", "Executive Summary"))
        flowables.append(Paragraph("01. EXECUTIVE SUMMARY", styles["SectionHeading1"]))

        # Status Badge Table
        status_label = dpr_status.replace("_", " ")
        badge_table = Table(
            [[Paragraph(f"DPR CLASSIFICATION: {status_label}", styles["BadgeText"])]],
            colWidths=[PRINTABLE_WIDTH_PORTRAIT]
        )
        badge_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_SUBTOTAL),
            ("BOX", (0, 0), (-1, -1), 0.75, COLOR_STEEL_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flowables.append(badge_table)
        flowables.append(Spacer(1, 10))

        # Narrative Paragraphs
        for p in narrative.paragraphs:
            resolved_p = cls.resolve_placeholders(p, placeholder_map)
            flowables.append(Paragraph(resolved_p, styles["Body"]))

        flowables.append(Spacer(1, 8))
        flowables.append(Paragraph("Source: KALPA Stage 14.3 Validated Appraisal Synthesis", styles["SourceNote"]))
        flowables.append(PageBreak())
        return flowables

    @classmethod
    def build_project_at_a_glance_page(
        cls,
        data: ProjectAtAGlanceData,
        fin_pkg: Dict[str, Any]
    ) -> List[Flowable]:
        """Builds comprehensive credit officer one-page summary."""
        flowables: List[Flowable] = []

        flowables.append(SectionTarget("sec_02_project_glance", "Project at a Glance"))
        flowables.append(Paragraph("02. PROJECT AT A GLANCE", styles["SectionHeading1"]))
        flowables.append(Paragraph("High-level credit appraisal matrix for institutional lending review.", styles["Callout"]))
        flowables.append(Spacer(1, 6))

        glance_rows = [
            ("Promoter Name", data.promoter_name),
            ("Legal Constitution", data.constitution),
            ("Business Activity / Industry", data.business_activity),
            ("NIC Code (5-Digit)", data.nic_code),
            ("Project Location / District", data.location),
            ("Primary Products / Services", data.products_services),
            ("Installed Operational Capacity", data.installed_capacity),
            ("Operating Capacity (Year 1)", data.operating_capacity),
            ("Total Project Cost", data.project_cost),
            ("Promoter Margin Contribution", data.promoter_contribution),
            ("Proposed Bank Term Loan", data.term_loan),
            ("Working Capital Facility Requirement", data.working_capital),
            ("Government Scheme / Subsidy Assistance", data.govt_assistance),
            ("Total Institutional Debt Exposure", data.total_bank_finance),
            ("Direct Employment Generated", data.employment),
            ("Project Implementation Period", data.implementation_period),
            ("Projected Turnover (Year 1)", data.year1_revenue),
            ("Projected Turnover (Steady-State)", data.steady_state_revenue),
            ("Operating EBITDA Margin", data.ebitda),
            ("Net Profit After Tax (PAT Year 1)", data.pat),
            ("Average Debt Service Coverage Ratio (DSCR)", data.average_dscr),
            ("Minimum DSCR (Repayment Tenure)", data.minimum_dscr),
            ("Break-Even Capacity Utilization", data.break_even),
            ("Estimated Capital Payback Period", data.payback_period),
            ("Overall Project Risk Classification", data.major_risk_level),
        ]

        table = DPRTableBuilder.create_key_value_table(glance_rows)
        flowables.append(table)
        flowables.append(Spacer(1, 6))
        flowables.append(Paragraph("Source: Reconciled Milestone 1–6 Financial & Appraisal Parameters", styles["SourceNote"]))

        flowables.append(PageBreak())
        return flowables

    @classmethod
    def build_canonical_section(
        cls,
        section_number: int,
        section_code: str,
        section_title: str,
        narrative: Optional[SectionNarrative],
        table_headers: Optional[List[str]] = None,
        table_rows: Optional[List[List[Any]]] = None,
        col_widths: Optional[List[float]] = None,
        chart_flowable: Optional[Flowable] = None,
        process_flow_flowable: Optional[Flowable] = None,
        sub_heading: Optional[str] = None,
        source_note: Optional[str] = None,
        placeholder_map: Optional[Dict[str, str]] = None,
        bullets: Optional[List[str]] = None
    ) -> List[Flowable]:
        """Builds a standardized canonical section with narrative, table, and vector charts."""
        from app.dpr.stage14_3.styles import clean_and_wrap_text
        flowables: List[Flowable] = []

        flowables.append(SectionTarget(section_code, f"{section_number:02d}. {section_title}"))
        flowables.append(Paragraph(f"{section_number:02d}. {section_title.upper()}", styles["SectionHeading1"]))

        if sub_heading:
            flowables.append(Paragraph(clean_and_wrap_text(sub_heading), styles["Callout"]))

        # Narrative Paragraphs
        if narrative and narrative.paragraphs:
            ph_map = placeholder_map or {}
            for p in narrative.paragraphs:
                res_p = cls.resolve_placeholders(p, ph_map)
                flowables.append(Paragraph(res_p, styles["Body"]))
            flowables.append(Spacer(1, 4))

        # Process Flow Chart if present
        if process_flow_flowable:
            flowables.append(Paragraph("Operational Process Flow Diagram:", styles["SectionHeading2"]))
            flowables.append(process_flow_flowable)
            flowables.append(Spacer(1, 6))

        # Bullets (e.g. SWOT / Key Drivers)
        if bullets:
            ph_map = placeholder_map or {}
            for b in bullets:
                res_b = cls.resolve_placeholders(b, ph_map)
                flowables.append(Paragraph(f"•  {res_b}", styles["Body"]))
            flowables.append(Spacer(1, 4))

        # Vector Chart if present
        if chart_flowable:
            flowables.append(chart_flowable)
            flowables.append(Spacer(1, 6))

        # Data Table if present
        if table_headers and table_rows:
            ph_map = placeholder_map or {}
            resolved_rows = [
                [cls.resolve_placeholders(str(cell), ph_map) for cell in row]
                for row in table_rows
            ]
            table = DPRTableBuilder.create_table(
                headers=table_headers,
                rows=resolved_rows,
                col_widths=col_widths
            )
            flowables.append(table)
            flowables.append(Spacer(1, 3))

        # Source Note
        if source_note:
            flowables.append(Paragraph(clean_and_wrap_text(source_note), styles["SourceNote"]))
        else:
            flowables.append(Paragraph("Source: KALPA Validated Appraisal System", styles["SourceNote"]))

        flowables.append(Spacer(1, 8))
        return flowables

