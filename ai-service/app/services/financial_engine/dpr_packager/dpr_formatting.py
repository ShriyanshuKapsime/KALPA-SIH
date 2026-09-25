"""
Milestone 6: DPR Formatting Utilities.
Centralized, deterministic formatting helpers for Indian currency (INR),
percentages, ratios, units, dates, year labels, negative values, and UNKNOWN values.
Underlying numeric values are strictly preserved and never mutated.
"""
from typing import Optional, Union, Any


def format_inr(
    val: Optional[Union[int, float]],
    placeholder: str = "Not available",
    accounting_brackets: bool = False,
    include_symbol: bool = True,
    decimals: int = 2
) -> str:
    """
    Formats a numeric value into standard Indian numbering system format (lakhs/crores).
    Example: 1250000 -> ₹12,50,000.00
    If val is None: returns placeholder (e.g. "Not available"). UNKNOWN != ZERO.
    If val is negative: can use brackets '(₹10,000)' or '-₹10,000'.
    """
    if val is None:
        return placeholder
    
    try:
        f_val = float(val)
    except (ValueError, TypeError):
        return placeholder

    is_negative = f_val < 0
    abs_val = abs(f_val)

    # Format with decimals
    formatted_base = f"{abs_val:.{decimals}f}"
    parts = formatted_base.split(".")
    integer_part = parts[0]
    decimal_part = f".{parts[1]}" if decimals > 0 else ""

    # Indian comma grouping: last 3 digits, then groups of 2
    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        groups.append(last3)
        formatted_int = ",".join(groups)
    else:
        formatted_int = integer_part

    symbol = "₹" if include_symbol else ""
    formatted_number = f"{symbol}{formatted_int}{decimal_part}"

    if is_negative:
        if accounting_brackets:
            return f"({formatted_number})"
        return f"-{formatted_number}"
    return formatted_number


def format_inr_lakhs(
    val: Optional[Union[int, float]],
    placeholder: str = "Not available",
    decimals: int = 2,
    include_symbol: bool = True
) -> str:
    """
    Formats an amount in Lakhs (₹ in Lakhs).
    Example: 1250000 -> ₹12.50 Lakhs
    """
    if val is None:
        return placeholder
    try:
        f_val = float(val) / 100000.0
        symbol = "₹" if include_symbol else ""
        return f"{symbol}{f_val:.{decimals}f} Lakhs"
    except (ValueError, TypeError):
        return placeholder


def format_percentage(
    val: Optional[Union[int, float]],
    precision: int = 1,
    placeholder: str = "Not available",
    multiply_by_100: bool = False
) -> str:
    """
    Formats a decimal or ratio as percentage.
    If multiply_by_100 is True: 0.125 -> 12.5%
    If multiply_by_100 is False: 12.5 -> 12.5%
    """
    if val is None:
        return placeholder
    try:
        f_val = float(val)
        if multiply_by_100:
            f_val *= 100.0
        return f"{f_val:.{precision}f}%"
    except (ValueError, TypeError):
        return placeholder


def format_ratio(
    val: Optional[Union[int, float]],
    precision: int = 2,
    suffix: str = "x",
    placeholder: str = "Not available"
) -> str:
    """
    Formats banking and financial ratios (e.g. DSCR, Current Ratio).
    Example: 1.652 -> 1.65x
    """
    if val is None:
        return placeholder
    try:
        f_val = float(val)
        return f"{f_val:.{precision}f}{suffix}"
    except (ValueError, TypeError):
        return placeholder


def format_year_label(year_idx: int, base_year: int = 2026) -> str:
    """
    Generates standardized financial year labels.
    Example: (1, 2026) -> 'Year 1 (FY 2026-27)'
    """
    start_yr = base_year + (year_idx - 1)
    end_yr = str(start_yr + 1)[-2:]
    return f"Year {year_idx} (FY {start_yr}-{end_yr})"


def format_unit(
    val: Optional[Union[int, float]],
    unit: str = "units",
    placeholder: str = "Not available",
    decimals: int = 0
) -> str:
    """
    Formats physical or capacity quantities.
    Example: (5000, 'Kg/Month') -> '5,000 Kg/Month'
    """
    if val is None:
        return placeholder
    try:
        f_val = float(val)
        if decimals == 0:
            return f"{int(round(f_val)):,} {unit}"
        return f"{f_val:,.{decimals}f} {unit}"
    except (ValueError, TypeError):
        return placeholder


def format_tenure(months: Optional[Union[int, float]], placeholder: str = "Not available") -> str:
    """
    Formats tenure in months and years.
    Example: 84 -> '84 Months (7.0 Years)'
    """
    if months is None:
        return placeholder
    try:
        m = int(round(float(months)))
        years = m / 12.0
        if years.is_integer():
            return f"{m} Months ({int(years)} Years)"
        return f"{m} Months ({years:.1f} Years)"
    except (ValueError, TypeError):
        return placeholder
