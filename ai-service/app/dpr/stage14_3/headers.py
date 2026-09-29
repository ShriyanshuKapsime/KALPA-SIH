"""
Stage 14.3: Running Header Flowables and Page Template Callbacks.
Provides clean institutional header styling with thin divider rules.
"""
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
    MARGIN_TOP,
)


def draw_running_header(
    canv: canvas.Canvas,
    page_width: float,
    page_height: float,
    business_name: str,
    dpr_title: str = "DETAILED PROJECT REPORT"
):
    """
    Renders top running header across non-cover pages.
    """
    canv.saveState()
    left_x = MARGIN_LEFT
    right_x = page_width - MARGIN_RIGHT
    y_pos = page_height - (12 * mm)

    # Top Left: KALPA | DETAILED PROJECT REPORT
    canv.setFont(FONT_BOLD, 7.5)
    canv.setFillColor(COLOR_NAVY_DARK)
    canv.drawString(left_x, y_pos, "KALPA")

    canv.setFont(FONT_REGULAR, 7.5)
    canv.setFillColor(COLOR_MUTED_GREY)
    canv.drawString(left_x + 36, y_pos, f"|  {dpr_title}")

    # Top Right: Business Name
    clean_biz = (business_name or "Enterprise").strip()
    if len(clean_biz) > 40:
        clean_biz = clean_biz[:38] + "..."
    canv.setFont(FONT_BOLD, 7.5)
    canv.setFillColor(COLOR_NAVY_DARK)
    canv.drawRightString(right_x, y_pos, clean_biz)

    # Separator Line
    canv.setStrokeColor(COLOR_BORDER)
    canv.setLineWidth(0.5)
    canv.line(left_x, y_pos - 3, right_x, y_pos - 3)

    canv.restoreState()
