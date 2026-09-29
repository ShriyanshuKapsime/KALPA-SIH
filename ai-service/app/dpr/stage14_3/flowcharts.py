"""
Stage 14.3: Business Archetype Process Flow Generator.
Generates vector process flow diagrams dynamically tailored to the business archetype:
Dairy, Manufacturing, Retail, Service, and Agriculture.
"""
from typing import Dict, Any, List, Optional, Tuple
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Group
from reportlab.lib import colors

from app.dpr.stage14_3.styles import (
    COLOR_NAVY_DARK,
    COLOR_STEEL_BLUE,
    COLOR_BORDER,
    COLOR_CHARCOAL,
    COLOR_WHITE,
    COLOR_BG_LIGHT,
    COLOR_BG_CARD,
    FONT_REGULAR,
    FONT_BOLD,
    PRINTABLE_WIDTH_PORTRAIT,
)

ARCHETYPE_STEPS = {
    "DAIRY": [
        ("01", "Livestock & Feed", "Procurement of quality feed & veterinary care"),
        ("02", "Milk Harvesting", "Hygienic daily milking & batch recording"),
        ("03", "Chilling & QC", "Rapid chilling to 4°C & fat/SNF testing"),
        ("04", "Packaging / Bulk", "Bulk dispatch / retail packaging"),
        ("05", "By-product Mgmt", "Organic manure processing & distribution"),
    ],
    "MANUFACTURING": [
        ("01", "Raw Material Inward", "Quality inspection & vendor receipt"),
        ("02", "Primary Processing", "Sizing, blending & primary preparation"),
        ("03", "Core Fabrication", "Machine processing & precision tooling"),
        ("04", "Quality Inspection", "Finished goods batch testing & QC"),
        ("05", "Packaging & Dispatch", "Protective packaging, storage & dispatch"),
    ],
    "RETAIL": [
        ("01", "Supplier Procurement", "Scheduled wholesale ordering & delivery"),
        ("02", "Inward Audit", "Barcoding, SKU verification & inventory entry"),
        ("03", "Merchandising", "Shelf placement, categorisation & display"),
        ("04", "Customer Checkout", "Point-of-Sale billing & payment settlement"),
        ("05", "Replenishment", "Stock monitoring & re-order automation"),
    ],
    "SERVICE": [
        ("01", "Customer Intake", "Work request logging & initial scope definition"),
        ("02", "Job Estimation", "Time, materials & scheduling assessment"),
        ("03", "Service Execution", "Skilled operational delivery & milestone tracking"),
        ("04", "Quality Verification", "Final inspection & client sign-off"),
        ("05", "Billing & Settlement", "Invoice generation & payment receipt"),
    ],
    "AGRICULTURE": [
        ("01", "Land & Seed Prep", "Field preparation, soil testing & certified seeds"),
        ("02", "Sowing & Planting", "Scientific spacing, fertilization & sowing"),
        ("03", "Agronomy & Irrigation", "Drip irrigation, weed control & pest management"),
        ("04", "Harvesting", "Maturity-timed harvesting & field sorting"),
        ("05", "Post-Harvest / Mandi", "Grading, packaging & dispatch to local APMC"),
    ],
}


class DPRProcessFlowBuilder:
    """
    Builds clean institutional vector process flowcharts for credit reports.
    """

    @classmethod
    def get_steps_for_archetype(cls, archetype: str, business_activity: str = "") -> List[Tuple[str, str, str]]:
        arch_clean = (archetype or "").upper()
        act_clean = (business_activity or "").lower()

        if "DAIRY" in arch_clean or "MILK" in act_clean or "COW" in act_clean:
            return ARCHETYPE_STEPS["DAIRY"]
        if "RETAIL" in arch_clean or "STORE" in act_clean or "SHOP" in act_clean or "KIRANA" in act_clean or "SAREE" in act_clean:
            return ARCHETYPE_STEPS["RETAIL"]
        if "SERVICE" in arch_clean or "REPAIR" in act_clean or "CONSULT" in act_clean:
            return ARCHETYPE_STEPS["SERVICE"]
        if "AGRI" in arch_clean or "CROP" in act_clean or "FARM" in act_clean:
            return ARCHETYPE_STEPS["AGRICULTURE"]
        return ARCHETYPE_STEPS["MANUFACTURING"]

    @classmethod
    def create_process_flow(
        cls,
        archetype: str = "MANUFACTURING",
        business_activity: str = "",
        custom_steps: Optional[List[Tuple[str, str, str]]] = None
    ) -> Drawing:
        steps = custom_steps or cls.get_steps_for_archetype(archetype, business_activity)
        num_steps = len(steps)

        dw = PRINTABLE_WIDTH_PORTRAIT
        dh = 65
        d = Drawing(dw, dh)

        box_w = (dw - (num_steps - 1) * 14) / num_steps
        box_h = 50
        y_pos = 8

        for idx, (step_num, title, desc) in enumerate(steps):
            x_pos = idx * (box_w + 14)

            # Node card background
            d.add(Rect(x_pos, y_pos, box_w, box_h, rx=3, ry=3, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.75))

            # Step number badge
            d.add(Rect(x_pos, y_pos + box_h - 13, 16, 13, rx=2, ry=2, fillColor=COLOR_NAVY_DARK, strokeColor=None))
            d.add(String(x_pos + 3, y_pos + box_h - 10, step_num, fontName="DejaVuSans-Bold", fontSize=6.5, fillColor=COLOR_WHITE))

            # Title
            d.add(String(x_pos + 20, y_pos + box_h - 10, title[:16], fontName="DejaVuSans-Bold", fontSize=7, fillColor=COLOR_NAVY_DARK))

            # Description (wrapped into two lines if long)
            words = desc.split()
            line1 = " ".join(words[:4])
            line2 = " ".join(words[4:8]) if len(words) > 4 else ""
            d.add(String(x_pos + 4, y_pos + 20, line1, fontName="DejaVuSans", fontSize=6, fillColor=COLOR_CHARCOAL))
            if line2:
                d.add(String(x_pos + 4, y_pos + 11, line2, fontName="DejaVuSans", fontSize=6, fillColor=COLOR_CHARCOAL))

            # Directional arrow between nodes
            if idx < num_steps - 1:
                arrow_x = x_pos + box_w + 2
                arrow_y = y_pos + (box_h / 2)
                d.add(Line(arrow_x, arrow_y, arrow_x + 8, arrow_y, strokeColor=COLOR_STEEL_BLUE, strokeWidth=1.2))
                d.add(Polygon(
                    [arrow_x + 8, arrow_y - 2.5, arrow_x + 12, arrow_y, arrow_x + 8, arrow_y + 2.5],
                    fillColor=COLOR_STEEL_BLUE,
                    strokeColor=None
                ))

        return d
