"""
Stage 14.3: Real Table of Contents (TOC) Generator.
Generates institutional Table of Contents matching actual final PDF pages
using a two-pass page number collection mechanism.
"""
from typing import Dict, List, Tuple, Optional
from reportlab.platypus import Table, TableStyle, Paragraph, Flowable
from reportlab.lib import colors

from app.dpr.stage14_3.styles import (
    COLOR_NAVY_DARK,
    COLOR_STEEL_BLUE,
    COLOR_BORDER,
    COLOR_BG_LIGHT,
    COLOR_BG_SUBTOTAL,
    COLOR_WHITE,
    COLOR_CHARCOAL,
    PRINTABLE_WIDTH_PORTRAIT,
    get_institutional_styles,
)

styles = get_institutional_styles()


class SectionTarget(Flowable):
    """Zero-height invisible flowable that notifies the canvas/doc of a section's page location."""

    def __init__(self, section_id: str, title: str):
        super().__init__()
        self.section_id = section_id
        self.title = title
        self.width = 0
        self.height = 0
        self.keepWithNext = True

    def draw(self):
        if hasattr(self.canv, "mark_section_page"):
            self.canv.mark_section_page(self.section_id)


class DPRTableOfContentsBuilder:
    """
    Builds the formal 3-column Table of Contents (Section, Title, Page).
    """

    @classmethod
    def create_toc_table(
        cls,
        toc_entries: List[Tuple[str, str, int]],  # (section_ref, title, page_number)
        col_widths: Optional[List[float]] = None
    ) -> Table:
        total_w = PRINTABLE_WIDTH_PORTRAIT
        w_sec = total_w * 0.16
        w_title = total_w * 0.70
        w_page = total_w * 0.14
        if col_widths and len(col_widths) == 3:
            w_sec, w_title, w_page = col_widths

        headers = ["Section", "Title / Content Description", "Page"]
        header_row = [
            Paragraph(headers[0], styles["TableHeader"]),
            Paragraph(headers[1], styles["TableHeader"]),
            Paragraph(headers[2], styles["TableHeaderRight"]),
        ]

        data = [header_row]

        subtotal_rows = []
        for idx, (sec_code, title, p_num) in enumerate(toc_entries):
            is_annexure_header = "ANNEXURE" in sec_code.upper() and len(sec_code) <= 12
            is_major_part = sec_code.startswith("PART") or sec_code.startswith("MODULE")

            p_style = styles["TOCSectionTitle"]
            if is_major_part or is_annexure_header:
                subtotal_rows.append(idx)
                p_style = styles["TableCellBold"]

            p_sec = Paragraph(sec_code, styles["TableCellBold"] if (is_major_part or is_annexure_header) else styles["TableCell"])
            p_title = Paragraph(title, p_style)
            p_page = Paragraph(str(p_num) if p_num > 0 else "—", styles["TOCPageNumber"])

            data.append([p_sec, p_title, p_page])

        t = Table(data, colWidths=[w_sec, w_title, w_page], repeatRows=1)

        ts = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_DARK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        for r_idx in range(len(toc_entries)):
            mat_idx = r_idx + 1
            if r_idx in subtotal_rows:
                ts.append(("BACKGROUND", (0, mat_idx), (-1, mat_idx), COLOR_BG_SUBTOTAL))
            elif r_idx % 2 == 1:
                ts.append(("BACKGROUND", (0, mat_idx), (-1, mat_idx), COLOR_BG_LIGHT))

        t.setStyle(TableStyle(ts))
        return t
