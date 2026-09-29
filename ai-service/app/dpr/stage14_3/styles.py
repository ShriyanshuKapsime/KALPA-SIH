"""
Stage 14.3: Institutional Document Styles, Palette & Central Resolvers.
Defines conservative banking/appraisal typography, color tokens, Unicode font registration,
display-value resolvers, and ReportLab stylesheets.
Guarantees clean page geometry for both Portrait and Landscape A4 pages.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Page Dimensions & Margins
PAGE_WIDTH_PORTRAIT, PAGE_HEIGHT_PORTRAIT = A4
PAGE_WIDTH_LANDSCAPE, PAGE_HEIGHT_LANDSCAPE = landscape(A4)

MARGIN_LEFT = 22 * mm   # ~62.36 pt
MARGIN_RIGHT = 18 * mm  # ~51.02 pt
MARGIN_TOP = 20 * mm    # ~56.70 pt
MARGIN_BOTTOM = 20 * mm # ~56.70 pt

PRINTABLE_WIDTH_PORTRAIT = PAGE_WIDTH_PORTRAIT - MARGIN_LEFT - MARGIN_RIGHT    # ~481.9 pt
PRINTABLE_HEIGHT_PORTRAIT = PAGE_HEIGHT_PORTRAIT - MARGIN_TOP - MARGIN_BOTTOM  # ~728.5 pt

MARGIN_LANDSCAPE_LR = 18 * mm
MARGIN_LANDSCAPE_TB = 18 * mm
PRINTABLE_WIDTH_LANDSCAPE = PAGE_WIDTH_LANDSCAPE - (2 * MARGIN_LANDSCAPE_LR)  # ~739.8 pt
PRINTABLE_HEIGHT_LANDSCAPE = PAGE_HEIGHT_LANDSCAPE - (2 * MARGIN_LANDSCAPE_TB) # ~493.3 pt

# Institutional Color Palette
COLOR_NAVY_DARK = colors.HexColor("#0F2942")     # Dominant primary / cover / main headers
COLOR_NAVY_ACCENT = colors.HexColor("#1E3A5F")   # Sub-headers / category titles
COLOR_STEEL_BLUE = colors.HexColor("#2E5B82")    # Accent lines / section badges
COLOR_CHARCOAL = colors.HexColor("#2D3748")      # Primary body text
COLOR_MUTED_GREY = colors.HexColor("#718096")    # Secondary captions / source notes
COLOR_BORDER = colors.HexColor("#CBD5E0")        # Table gridlines & divider rules
COLOR_BORDER_DARK = colors.HexColor("#718096")   # Total line dark borders
COLOR_BG_LIGHT = colors.HexColor("#F8FAFC")      # Alternating row fill
COLOR_BG_SUBTOTAL = colors.HexColor("#EDF2F7")   # Subtotal row fill
COLOR_BG_CARD = colors.HexColor("#F7FAFC")       # Information box fill
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_SUCCESS = colors.HexColor("#22543D")       # Passing status / positive variance
COLOR_WARNING = colors.HexColor("#744210")       # Warning status
COLOR_DANGER = colors.HexColor("#742A2A")        # Failure / gap status

# Canonical Standard ReportLab Fonts for pristine layout & metrics
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_BOLD_ITALIC = "Helvetica-BoldOblique"

_FONTS_REGISTERED = False

INDIC_FONTS_MAP = {
    "hi": ("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
    "mr": ("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
    "kn": ("/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansKannada-Bold.ttf"),
    "ta": ("/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf"),
    "te": ("/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansTelugu-Bold.ttf"),
    "gu": ("/usr/share/fonts/truetype/noto/NotoSerifGujarati-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSerifGujarati-Bold.ttf"),
}

def init_institutional_fonts():
    """Registers Unicode TrueType fonts under explicit names for inline text fallback."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    # Standard Unicode DejaVu Sans for Rupee (₹) and Latin Symbols
    deja_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    deja_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(deja_reg):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", deja_reg))
        except Exception as e:
            logger.warning(f"[FONTS] DejaVuSans reg error: {e}")
    if os.path.exists(deja_bold):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", deja_bold))
        except Exception as e:
            logger.warning(f"[FONTS] DejaVuSans-Bold reg error: {e}")

    # Devanagari (Hindi, Marathi)
    dev_reg = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    dev_bold = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
    if os.path.exists(dev_reg):
        try:
            pdfmetrics.registerFont(TTFont("NotoSansDevanagari", dev_reg))
            pdfmetrics.registerFont(TTFont("Noto-hi", dev_reg))
            pdfmetrics.registerFont(TTFont("Noto-mr", dev_reg))
        except Exception as e:
            logger.warning(f"[FONTS] Devanagari reg error: {e}")
    if os.path.exists(dev_bold):
        try:
            pdfmetrics.registerFont(TTFont("NotoSansDevanagari-Bold", dev_bold))
            pdfmetrics.registerFont(TTFont("Noto-hi-Bold", dev_bold))
            pdfmetrics.registerFont(TTFont("Noto-mr-Bold", dev_bold))
        except Exception as e:
            logger.warning(f"[FONTS] Devanagari bold error: {e}")

    # Register other Indic language fonts
    for l_code, (r_p, b_p) in INDIC_FONTS_MAP.items():
        if l_code in ("hi", "mr"):
            continue
        if r_p and os.path.exists(r_p):
            try:
                base_name = os.path.basename(r_p).replace(".ttf", "")
                pdfmetrics.registerFont(TTFont(base_name, r_p))
                pdfmetrics.registerFont(TTFont(f"Noto-{l_code}", r_p))
            except Exception:
                pass
        if b_p and os.path.exists(b_p):
            try:
                base_name = os.path.basename(b_p).replace(".ttf", "")
                pdfmetrics.registerFont(TTFont(base_name, b_p))
                pdfmetrics.registerFont(TTFont(f"Noto-{l_code}-Bold", b_p))
            except Exception:
                pass

    _FONTS_REGISTERED = True

# Register at import time
init_institutional_fonts()


def clean_and_wrap_text(text: Any, bold: bool = False) -> str:
    """
    Cleans duplicate suffixes and safely wraps Rupee glyph (₹) and Indic characters
    with inline <font name="..."> tags so ReportLab renders them crisply without
    altering global document font metrics or table widths.
    """
    if text is None:
        return ""
    s = str(text)

    # 1. Clean duplicated units/suffixes
    s = re.sub(r'(\d+(?:\.\d+)?)\s*%\s*(?:percent|pct|Utilization%|Capacity%)', r'\1%', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+)\s*Months?\s*months?', r'\1 Months', s, flags=re.IGNORECASE)
    s = re.sub(r'%\s*%', '%', s)
    s = s.replace("Utilization%", "Utilization").replace("Capacity%", "Capacity")

    # 2. Wrap Rupee sign if present
    r_font = "DejaVuSans-Bold" if bold else "DejaVuSans"
    if "₹" in s:
        # Avoid double-wrapping if already wrapped
        if f'<font name="{r_font}">₹</font>' not in s:
            s = re.sub(r'₹', f'<font name="{r_font}">₹</font>', s)

    # 3. Check for Indic script characters (excluding ₹)
    indic_chars = [c for c in s if ord(c) > 127 and c != '₹' and ord(c) != 0x20B9]
    if indic_chars:
        # Determine language font family
        cp = ord(indic_chars[0])
        if 0x0C80 <= cp <= 0x0CFF:
            i_font = "NotoSansKannada-Bold" if bold else "NotoSansKannada"
        elif 0x0B80 <= cp <= 0x0BFF:
            i_font = "NotoSansTamil-Bold" if bold else "NotoSansTamil"
        elif 0x0C00 <= cp <= 0x0C7F:
            i_font = "NotoSansTelugu-Bold" if bold else "NotoSansTelugu"
        elif 0x0A80 <= cp <= 0x0AFF:
            i_font = "NotoSerifGujarati-Bold" if bold else "NotoSerifGujarati"
        else:
            i_font = "NotoSansDevanagari-Bold" if bold else "NotoSansDevanagari"

        if f'<font name="{i_font}">' not in s:
            # Wrap contiguous non-ASCII sequences (excluding XML tags)
            def _replace_indic(m):
                content = m.group(0)
                if content.startswith("<font") or content.startswith("</font"):
                    return content
                return f'<font name="{i_font}">{content}</font>'
            s = re.sub(r'[\u0900-\u0D7F]+', _replace_indic, s)

    return s


def wrap_indic_font(text: Any, bold: bool = False) -> str:
    """Alias for backwards compatibility."""
    return clean_and_wrap_text(text, bold=bold)


def format_percent(val: Any) -> str:
    """
    Centralized percentage formatter. Never appends double '%%' or 'percent'.
    Accepts floats (46.5 or 0.465), ints, or strings with existing '%'.
    """
    if val is None or val == "" or str(val).strip().lower() in ("none", "null", "undefined"):
        return "—"
    if isinstance(val, (int, float)):
        num = float(val)
        if 0 < num < 1.0:
            num = num * 100.0
        return f"{num:.1f}%"
    s = str(val).strip()
    # Clean any trailing or duplicated % or percent
    s = re.sub(r'(?:%+|\s*percent|\s*pct)+$', '', s, flags=re.IGNORECASE).strip()
    try:
        num = float(s)
        if 0 < num < 1.0:
            num = num * 100.0
        return f"{num:.1f}%"
    except ValueError:
        # If it's a descriptive string that already contains '%', return clean string
        if "%" in str(val):
            clean_s = re.sub(r'%\s*%', '%', str(val)).strip()
            clean_s = re.sub(r'%\s*(?:percent|pct)', '%', clean_s, flags=re.IGNORECASE)
            return clean_s
        return f"{s}%" if s else "—"


def resolve_display_enum(val: Any) -> str:
    """
    Centralized resolver that converts database enum strings into clean,
    professional institutional labels for bank-facing appraisal documents.
    Preserves regional language Unicode text (Hindi, Marathi, Kannada, etc.) directly.
    """
    if val is None or val == "":
        return "To be confirmed during appraisal"
    s = str(val).strip()
    if not s:
        return "To be confirmed during appraisal"

    # If string contains non-ASCII or Rupee characters, clean and wrap safely
    if any(ord(c) > 127 for c in s) or "₹" in s:
        return clean_and_wrap_text(s.replace("_", " "))

    s_upper = s.upper()
    if "CURRENT LOCATION" in s_upper or "GPS" in s_upper:
        return "Target Catchment Area"

    mapping = {
        "12TH_PASS": "Higher Secondary (12th Pass)",
        "10TH_PASS": "Secondary School (10th Pass)",
        "GRADUATE": "Graduate / Bachelor's Degree",
        "POST_GRADUATE": "Post Graduate / Master's Degree",
        "DOCTORATE": "Doctorate / Professional Qualification",
        "DIPLOMA": "Technical Diploma",
        "ILLITERATE": "Primary / Self-Educated",
        "NOT_UNDERTAKEN": "Not Yet Undertaken",
        "UNDERTAKEN": "Formally Completed",
        "IN_PROGRESS": "Currently in Progress",
        "COMPLETED": "Completed",
        "SOLE_PROPRIETORSHIP": "Sole Proprietorship",
        "PROPRIETORSHIP": "Sole Proprietorship",
        "PARTNERSHIP": "Registered Partnership Firm",
        "PVT_LTD": "Private Limited Company",
        "PUBLIC_LTD": "Public Limited Company",
        "LLP": "Limited Liability Partnership (LLP)",
        "COOPERATIVE": "Cooperative Society",
        "OPC": "One Person Company",
        "OWNED": "Self-Owned Premises",
        "RENTED": "Rented / Commercial Lease",
        "LEASED": "Long-Term Commercial Lease",
        "GENERAL": "General Category",
        "OBC": "Other Backward Classes (OBC)",
        "SC": "Scheduled Caste (SC)",
        "ST": "Scheduled Tribe (ST)",
        "MINORITY": "Minority Community",
        "WOMEN": "Women Entrepreneur",
        "MALE": "Male",
        "FEMALE": "Female",
        "RURAL": "Rural Area",
        "SEMI_URBAN": "Semi-Urban Area",
        "URBAN": "Urban Area",
        "METRO": "Metropolitan Area",
        "MANUFACTURING": "Manufacturing / Processing",
        "SERVICES": "Services Enterprise",
        "TRADING": "Trading / Retail Distribution",
        "AGRI_ALLIED": "Agriculture & Allied Activities",
    }
    if s in mapping:
        return mapping[s]

    acronyms = {
        "RBI": "RBI", "MSME": "MSME", "PSL": "PSL", "CGTMSE": "CGTMSE",
        "CIBIL": "CIBIL", "EDP": "EDP", "GST": "GST", "PAN": "PAN",
        "WDV": "WDV", "NIC": "NIC", "DSCR": "DSCR", "EBITDA": "EBITDA",
        "PAT": "PAT", "PBT": "PBT", "ROCE": "ROCE", "SLM": "SLM"
    }

    words = str(val).replace("_", " ").split()
    resolved_words = [acronyms.get(w.upper(), w.capitalize()) for w in words]
    return " ".join(resolved_words)


def format_currency(val: Any, decimals: int = 0) -> str:
    """Format as ₹7,90,000 using Indian numbering."""
    from app.services.financial_engine.dpr_packager.dpr_formatting import format_inr
    return format_inr(val, decimals=decimals)


def format_amount_lakh(val: Any, decimals: int = 2) -> str:
    """Format as ₹1.40 lakh."""
    from app.services.financial_engine.dpr_packager.dpr_formatting import format_inr_lakhs
    return format_inr_lakhs(val, decimals=decimals)


def format_percentage(val: Any, decimals: int = 2) -> str:
    """Format as 9.50% safely without %%."""
    return format_percent(val)


def format_ratio(val: Any, decimals: int = 2) -> str:
    """Format as 1.99x."""
    try:
        f = float(val)
        return f"{f:.{decimals}f}x"
    except (ValueError, TypeError):
        return f"{val}x"


def resolve_display_location(
    district: Optional[str] = None,
    state: Optional[str] = None,
    address: Optional[str] = None,
    raw_loc: Optional[str] = None
) -> str:
    """
    Sanitizes location string for institutional credit reports.
    Guarantees 'Current Location (GPS)' is NEVER rendered on bank-facing documents.
    """
    d = (district or "").strip()
    s = (state or "").strip()
    addr = (address or "").strip()
    raw = (raw_loc or "").strip()

    # Reject raw GPS placeholders (case-insensitive)
    if "gps" in d.lower() or "current location" in d.lower():
        d = ""
    if "gps" in s.lower() or "current location" in s.lower():
        s = ""
    if "gps" in addr.lower() or "current location" in addr.lower():
        addr = ""
    if "gps" in raw.lower() or "current location" in raw.lower():
        raw = ""

    # Priority 1: District and State
    if d and s and d.lower() != "district" and s.lower() != "state":
        return f"{d}, {s}"
    elif d and d.lower() != "district":
        return d
    elif s and s.lower() != "state":
        return s

    # Priority 2: Validated Address
    if addr and "gps" not in addr.lower():
        return addr

    # Priority 3: Clean raw location
    if raw and "gps" not in raw.lower() and "none" not in raw.lower():
        return raw

    return "Location to be confirmed during bank appraisal"


def get_institutional_styles(language: str = "en") -> Dict[str, ParagraphStyle]:
    """
    Creates complete suite of ParagraphStyles using standard Helvetica fonts for bank-review-ready DPR formatting.
    """
    base_styles = getSampleStyleSheet()

    styles = {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName=FONT_BOLD,
            fontSize=22,
            leading=26,
            textColor=COLOR_NAVY_DARK,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=16,
            textColor=COLOR_STEEL_BLUE,
            alignment=TA_LEFT,
            spaceAfter=15,
        ),
        "CoverMetaLabel": ParagraphStyle(
            "CoverMetaLabel",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8.5,
            leading=11,
            textColor=COLOR_MUTED_GREY,
            spaceAfter=2,
        ),
        "CoverMetaValue": ParagraphStyle(
            "CoverMetaValue",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=13,
            textColor=COLOR_CHARCOAL,
            spaceAfter=8,
        ),
        "DocumentControlHeader": ParagraphStyle(
            "DocumentControlHeader",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=COLOR_NAVY_DARK,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "SectionHeading1": ParagraphStyle(
            "SectionHeading1",
            parent=base_styles["Heading1"],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=15,
            textColor=COLOR_NAVY_DARK,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "SectionHeading2": ParagraphStyle(
            "SectionHeading2",
            parent=base_styles["Heading2"],
            fontName=FONT_BOLD,
            fontSize=10.5,
            leading=13.5,
            textColor=COLOR_NAVY_ACCENT,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            leading=13,
            textColor=COLOR_CHARCOAL,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=13,
            textColor=COLOR_CHARCOAL,
            spaceAfter=4,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=12,
            textColor=COLOR_NAVY_DARK,
            spaceBefore=3,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=COLOR_WHITE,
            alignment=TA_LEFT,
        ),
        "TableHeaderRight": ParagraphStyle(
            "TableHeaderRight",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=COLOR_WHITE,
            alignment=TA_RIGHT,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_CHARCOAL,
            alignment=TA_LEFT,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_CHARCOAL,
            alignment=TA_LEFT,
        ),
        "TableCellRight": ParagraphStyle(
            "TableCellRight",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_CHARCOAL,
            alignment=TA_RIGHT,
        ),
        "TableCellRightBold": ParagraphStyle(
            "TableCellRightBold",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_CHARCOAL,
            alignment=TA_RIGHT,
        ),
        "SourceNote": ParagraphStyle(
            "SourceNote",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=7,
            leading=9,
            textColor=COLOR_MUTED_GREY,
            spaceBefore=3,
            spaceAfter=6,
        ),
        "UnitDeclaration": ParagraphStyle(
            "UnitDeclaration",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_STEEL_BLUE,
            alignment=TA_RIGHT,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "BadgeText": ParagraphStyle(
            "BadgeText",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
        ),
        "TOCSectionTitle": ParagraphStyle(
            "TOCSectionTitle",
            parent=base_styles["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_CHARCOAL,
        ),
        "TOCPageNumber": ParagraphStyle(
            "TOCPageNumber",
            parent=base_styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_NAVY_DARK,
            alignment=TA_RIGHT,
        ),
    }

    return styles
