"""
Stage 14.3: Institutional DPR Table System.
Builds banking/appraisal tables with repeated headers, right-aligned currency,
accounting brackets for negatives, Indian numbering separators, and strict UNKNOWN != ZERO enforcement.
"""
from typing import Dict, Any, List, Optional, Union, Tuple
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors

from app.dpr.stage14_3.styles import (
    COLOR_NAVY_DARK,
    COLOR_STEEL_BLUE,
    COLOR_BORDER,
    COLOR_BORDER_DARK,
    COLOR_BG_LIGHT,
    COLOR_BG_SUBTOTAL,
    COLOR_WHITE,
    COLOR_CHARCOAL,
    PRINTABLE_WIDTH_PORTRAIT,
    PRINTABLE_WIDTH_LANDSCAPE,
    get_institutional_styles,
    resolve_display_enum,
    format_percent,
    clean_and_wrap_text,
)
from app.services.financial_engine.dpr_packager.dpr_formatting import (
    format_inr,
    format_inr_lakhs,
    format_percentage,
    format_ratio,
)

styles = get_institutional_styles()


def sanitize_table_val(val: Any, is_currency: bool = False, decimals: int = 2) -> str:
    """Strictly enforces UNKNOWN != ZERO and display sanitization rules."""
    if val is None:
        return "Not resolved"
    if isinstance(val, dict):
        if "value" in val:
            return sanitize_table_val(val["value"], is_currency=is_currency, decimals=decimals)
        if "amount" in val:
            return sanitize_table_val(val["amount"], is_currency=True, decimals=decimals)
        if "label" in val:
            return str(val["label"])
        # Format dictionary concisely
        items = [f"{k}: {v}" for k, v in val.items() if v is not None and str(v).strip() and not isinstance(v, (dict, list))]
        return "; ".join(items[:3]) if items else "Structured Data"
    if isinstance(val, list):
        if not val:
            return "—"
        return ", ".join(sanitize_table_val(x) for x in val[:5])

    s_val = str(val).strip()
    if s_val.upper() in ("UNKNOWN", "NONE", "NULL", "UNDEFINED"):
        return "Not resolved"
    if s_val.upper() == "USER_REQUIRED":
        return "To be provided"
    if s_val.upper() in ("DOCUMENT_PENDING", "PENDING_DOCUMENT"):
        return "Pending document"
    if s_val.upper() in ("NOT_APPLICABLE", "NA", "N/A"):
        return "Not applicable"
    if s_val.upper() == "CONFLICT":
        return "Conflict requires resolution"
    if s_val.upper() == "SOURCE_MAPPING_ERROR":
        return "Source mapping requires review"
    if "Current Location (GPS)" in s_val:
        return "Location to be confirmed"

    # Fix double percentage or descriptive percentage
    if "%" in s_val or "percent" in s_val.lower():
        return format_percent(s_val)

    if is_currency:
        try:
            f = float(val)
            res = format_inr(f, accounting_brackets=True, decimals=decimals)
            return clean_and_wrap_text(res, bold=False)
        except (ValueError, TypeError):
            return resolve_display_enum(s_val)

    return resolve_display_enum(s_val)


class DPRTableBuilder:
    """
    Standardized institutional table generator for portrait and landscape financial schedules.
    """

    @classmethod
    def create_table(
        cls,
        headers: List[str],
        rows: List[List[Any]],
        col_widths: Optional[List[float]] = None,
        alignments: Optional[List[str]] = None,
        is_landscape: bool = False,
        subtotal_rows: Optional[List[int]] = None,
        total_rows: Optional[List[int]] = None,
        currency_cols: Optional[List[int]] = None,
        unit_declaration: Optional[str] = None
    ) -> Table:
        total_printable = PRINTABLE_WIDTH_LANDSCAPE if is_landscape else PRINTABLE_WIDTH_PORTRAIT
        num_cols = len(headers)

        # Distribute column widths if not explicitly provided
        if not col_widths or len(col_widths) != num_cols:
            first_col_w = total_printable * 0.35 if num_cols > 2 else total_printable * 0.5
            rem_w = (total_printable - first_col_w) / max(num_cols - 1, 1)
            col_widths = [first_col_w] + [rem_w] * (num_cols - 1)
        else:
            # Scale col_widths to fit printable width exactly
            current_sum = sum(col_widths)
            if current_sum > 0:
                scale = total_printable / current_sum
                col_widths = [w * scale for w in col_widths]

        align_list = alignments or (["LEFT"] + ["RIGHT"] * (num_cols - 1) if num_cols > 1 else ["LEFT"])
        curr_set = set(currency_cols or [])
        subtotal_set = set(subtotal_rows or [])
        total_set = set(total_rows or [])

        # Build table matrix with Paragraph flowables
        data_matrix: List[List[Any]] = []

        # 1. Header row
        header_row_flowables = []
        for c_idx, h in enumerate(headers):
            style = styles["TableHeaderRight"] if align_list[c_idx] == "RIGHT" else styles["TableHeader"]
            header_row_flowables.append(Paragraph(clean_and_wrap_text(str(h), bold=True), style))
        data_matrix.append(header_row_flowables)

        # 2. Body rows
        for r_idx, row in enumerate(rows):
            if len(row) != len(headers):
                raise ValueError(
                    f"[Table Schema Error] Row {r_idx} length ({len(row)}) does not match header length ({len(headers)}). "
                    f"Row content: {row}"
                )
            is_subtotal = r_idx in subtotal_set
            is_total = r_idx in total_set
            row_flowables = []

            for c_idx, cell in enumerate(row):
                is_curr = c_idx in curr_set
                clean_txt = sanitize_table_val(cell, is_currency=is_curr)
                align = align_list[c_idx] if c_idx < len(align_list) else "LEFT"
                is_bold = is_total or is_subtotal

                if is_total:
                    cell_style = styles["TableCellRightBold"] if align == "RIGHT" else styles["TableCellBold"]
                elif is_subtotal:
                    cell_style = styles["TableCellRightBold"] if align == "RIGHT" else styles["TableCellBold"]
                else:
                    cell_style = styles["TableCellRight"] if align == "RIGHT" else styles["TableCell"]

                row_flowables.append(Paragraph(clean_and_wrap_text(clean_txt, bold=is_bold), cell_style))
            data_matrix.append(row_flowables)

        # 3. Apply ReportLab TableStyle
        ts_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_NAVY_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_NAVY_DARK),
        ]

        # Alternating background fills for rows (1-indexed due to header)
        for r_idx in range(len(rows)):
            mat_idx = r_idx + 1
            if r_idx in total_set:
                ts_commands.append(("BACKGROUND", (0, mat_idx), (-1, mat_idx), COLOR_BG_SUBTOTAL))
                ts_commands.append(("LINEABOVE", (0, mat_idx), (-1, mat_idx), 1.0, COLOR_BORDER_DARK))
                ts_commands.append(("LINEBELOW", (0, mat_idx), (-1, mat_idx), 1.5, COLOR_NAVY_DARK))
            elif r_idx in subtotal_set:
                ts_commands.append(("BACKGROUND", (0, mat_idx), (-1, mat_idx), COLOR_BG_SUBTOTAL))
                ts_commands.append(("LINEABOVE", (0, mat_idx), (-1, mat_idx), 0.75, COLOR_BORDER_DARK))
            elif r_idx % 2 == 1:
                ts_commands.append(("BACKGROUND", (0, mat_idx), (-1, mat_idx), COLOR_BG_LIGHT))

            # Row padding
            ts_commands.append(("TOPPADDING", (0, mat_idx), (-1, mat_idx), 3))
            ts_commands.append(("BOTTOMPADDING", (0, mat_idx), (-1, mat_idx), 3))

        t = Table(data_matrix, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle(ts_commands))
        return t

    @classmethod
    def create_key_value_table(
        cls,
        items: List[Tuple[str, Any]],
        col_widths: Optional[List[float]] = None
    ) -> Table:
        """Creates 2-column parameter / value table with subtle borders and clear typography."""
        total_w = PRINTABLE_WIDTH_PORTRAIT
        w1 = total_w * 0.45
        w2 = total_w * 0.55
        if col_widths and len(col_widths) == 2:
            w1, w2 = col_widths

        data = []
        for k, v in items:
            p_key = Paragraph(clean_and_wrap_text(str(k), bold=True), styles["TableCellBold"])
            p_val = Paragraph(clean_and_wrap_text(sanitize_table_val(v), bold=False), styles["TableCell"])
            data.append([p_key, p_val])

        t = Table(data, colWidths=[w1, w2])
        ts = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        for idx in range(len(items)):
            if idx % 2 == 1:
                ts.append(("BACKGROUND", (0, idx), (-1, idx), COLOR_BG_LIGHT))
        t.setStyle(TableStyle(ts))
        return t
