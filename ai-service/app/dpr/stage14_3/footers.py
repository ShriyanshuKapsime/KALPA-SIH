"""
Stage 14.3: Numbered Canvas & Running Footers.
Implements two-pass canvas that determines exact total page count,
draws institutional footers ("Page X of Y"), and captures section page targets for TOC.
"""
from typing import Dict, Any, List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

from app.dpr.stage14_3.styles import (
    COLOR_NAVY_DARK,
    COLOR_MUTED_GREY,
    COLOR_BORDER,
    FONT_REGULAR,
    FONT_BOLD,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_BOTTOM,
)
from app.dpr.stage14_3.headers import draw_running_header


class DPRNumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab Canvas.
    1. Records page states on showPage().
    2. On save(), computes total page count, renders running headers and footers,
       and builds section page bookmarks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self.document_id: str = "KALPA-DPR-001"
        self.version: str = "v1.0"
        self.classification: str = "PROJECT REPORT / CREDIT APPRAISAL DOCUMENT"
        self.business_name: str = ""
        self.section_page_map: Dict[str, int] = {}
        self.current_section_id: Optional[str] = None

    def set_document_metadata(
        self,
        document_id: str,
        business_name: str,
        version: str = "v1.0",
        classification: str = "PROJECT REPORT / CREDIT APPRAISAL DOCUMENT"
    ):
        self.document_id = document_id
        self.business_name = business_name
        self.version = version
        self.classification = classification

    def mark_section_page(self, section_id: str):
        """Records current page number for the given section."""
        self.section_page_map[section_id] = self._pageNumber

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)

        for state in self._saved_page_states:
            self.__dict__.update(state)
            page_num = self._pageNumber

            # Suppress header and footer on Page 1 (Cover Page)
            if page_num > 1:
                cur_w, cur_h = self._pagesize

                # Draw Running Header
                draw_running_header(
                    canv=self,
                    page_width=cur_w,
                    page_height=cur_h,
                    business_name=self.business_name
                )

                # Draw Running Footer
                self.saveState()
                left_x = MARGIN_LEFT
                right_x = cur_w - MARGIN_RIGHT
                center_x = cur_w / 2.0
                y_pos = 11 * mm

                # Separator Line
                self.setStrokeColor(COLOR_BORDER)
                self.setLineWidth(0.5)
                self.line(left_x, y_pos + 8, right_x, y_pos + 8)

                # Footer Left: Document ID | Version
                self.setFont(FONT_REGULAR, 7)
                self.setFillColor(COLOR_MUTED_GREY)
                self.drawString(left_x, y_pos, f"Ref: {self.document_id}  |  {self.version}")

                # Footer Center: Document Classification
                self.setFont(FONT_BOLD, 6.5)
                self.setFillColor(COLOR_NAVY_DARK)
                self.drawCentredString(center_x, y_pos, self.classification)

                # Footer Right: Page X of Y
                self.setFont(FONT_REGULAR, 7.5)
                self.setFillColor(COLOR_NAVY_DARK)
                self.drawRightString(right_x, y_pos, f"Page {page_num} of {num_pages}")

                self.restoreState()

            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)
