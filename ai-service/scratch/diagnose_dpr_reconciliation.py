import json
import os
import re
import fitz  # PyMuPDF

SCENARIO_PATH = "/app/data/dpr_scenarios/dairy_farm__DPR-dairy_farm-f44ddd19.json"
PDF_PATH = "/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-46798C.pdf"
OUTPUT_REPORT = "/app/data/dpr_reconciliation_diagnostic_report.json"
OUTPUT_MD = "/app/data/dpr_reconciliation_diagnostic_report.md"

def run_diagnosis():
    print(f"Loading scenario: {SCENARIO_PATH}")
    with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
        scen_data = json.load(f)

    fin_pkg = scen_data.get("financial_package") or {}
    user_answers = scen_data.get("user_answers") or {}

    print(f"Loading PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    page_count = len(doc)
    pages_text = [doc[i].get_text("text") for i in range(page_count)]
    full_text = "\n".join(pages_text)

    # Inspect upstream financial package values
    p_cost = fin_pkg.get("project_cost") or {}
    m_fin = fin_pkg.get("means_of_finance") or {}
    b_met = fin_pkg.get("banking_metrics") or {}
    wc_blk = fin_pkg.get("working_capital") or {}
    pnl = fin_pkg.get("projected_financial_statements") or fin_pkg.get("income_statement") or {}
    bs = fin_pkg.get("balance_sheet") or {}
    dscr_data = fin_pkg.get("dscr") or b_met.get("dscr_schedule") or {}

    upstream_map = {
        "business_name": scen_data.get("business_id"),
        "promoter": user_answers.get("promoter_name") or user_answers.get("entrepreneur_name"),
        "business_archetype": scen_data.get("business_archetype") or fin_pkg.get("business_archetype"),
        "nic_code": user_answers.get("nic_code"),
        "location": f"{user_answers.get('target_district')}, {user_answers.get('target_state')}",
        "total_project_cost": fin_pkg.get("total_project_cost") or p_cost.get("total_project_cost"),
        "promoter_contribution": fin_pkg.get("promoter_contribution") or m_fin.get("promoter_contribution") or m_fin.get("promoter_equity_amount"),
        "term_loan": fin_pkg.get("term_loan") or m_fin.get("term_loan") or m_fin.get("term_loan_amount"),
        "working_capital": fin_pkg.get("working_capital") or wc_blk.get("working_capital_margin_req"),
        "total_debt_exposure": None,
        "revenue_y1": fin_pkg.get("year1_revenue"),
        "revenue_y5": fin_pkg.get("year5_revenue"),
        "ebitda": fin_pkg.get("ebitda_margin_pct") or b_met.get("ebitda_margin"),
        "pat_y1": fin_pkg.get("pat_year1"),
        "dscr_avg": fin_pkg.get("average_dscr") or b_met.get("average_dscr"),
        "dscr_min": b_met.get("min_dscr"),
        "break_even": fin_pkg.get("break_even_utilization") or b_met.get("break_even_capacity_percentage"),
        "employment": user_answers.get("total_employment"),
        "promoter_margin_pct": m_fin.get("promoter_margin_pct") or m_fin.get("promoter_equity_percentage"),
        "loan_tenure": fin_pkg.get("loan_structure", {}).get("tenure_months"),
        "interest_rate": fin_pkg.get("loan_structure", {}).get("interest_rate"),
        "moratorium": fin_pkg.get("loan_structure", {}).get("moratorium_months"),
        "plant_machinery": p_cost.get("plant_and_machinery") or p_cost.get("plant_machinery"),
        "civil_cost": p_cost.get("land_and_building") or p_cost.get("civil_works"),
        "wc_margin": p_cost.get("working_capital_margin") or wc_blk.get("working_capital_margin_req"),
        "contingency": p_cost.get("contingency") or p_cost.get("contingencies"),
    }

    # Identify PDF occurrences
    sections = [
        "Executive Summary",
        "Project at a Glance",
        "Narrative sections",
        "Project Cost",
        "Means of Finance",
        "Working Capital",
        "Financial ratios",
        "Risk",
        "Credit Proposal",
        "Reconciliation",
        "Annexure E",
        "Annexure F",
        "Annexure J",
        "Annexure Q",
        "charts",
        "tables",
        "provenance"
    ]

    # Map each section to pages
    section_pages = {}
    for i, txt in enumerate(pages_text, 1):
        if "01. EXECUTIVE SUMMARY" in txt:
            section_pages["Executive Summary"] = i
        if "02. PROJECT AT A GLANCE" in txt or "PROJECT AT A GLANCE" in txt:
            section_pages["Project at a Glance"] = i
        if "16. PROJECT COST" in txt or "PROJECT COST & MEANS OF FINANCE" in txt:
            section_pages["Project Cost"] = i
            section_pages["Means of Finance"] = i
        if "WORKING CAPITAL" in txt:
            section_pages["Working Capital"] = i
        if "36. CREDIT FACILITY" in txt or "CREDIT FACILITY PROPOSAL" in txt:
            section_pages["Credit Proposal"] = i
        if "39. FINANCIAL INTEGRITY" in txt or "FINANCIAL INTEGRITY & RECONCILIATION" in txt:
            section_pages["Reconciliation"] = i
        if "ANNEXURE E" in txt:
            section_pages["Annexure E"] = i
        if "ANNEXURE F" in txt:
            section_pages["Annexure F"] = i
        if "ANNEXURE J" in txt:
            section_pages["Annexure J"] = i
        if "ANNEXURE Q" in txt:
            section_pages["Annexure Q"] = i

    print(f"Section page mapping detected: {section_pages}")

    # Build field-level source map and contradiction findings
    report = {
        "metadata": {
            "scenario_id": scen_data.get("scenario_id"),
            "business_id": scen_data.get("business_id"),
            "pdf_file": PDF_PATH,
            "pdf_pages": page_count,
        },
        "upstream_authoritative_values": upstream_map,
        "diagnosed_discrepancies": [],
        "field_comparisons": {}
    }

    # Discrepancy 1: Project cost components vs total
    # Check if sum(components) == total
    comp_sum = sum(filter(None, [
        upstream_map.get("plant_machinery") or 0,
        upstream_map.get("civil_cost") or 0,
        upstream_map.get("wc_margin") or 0,
        upstream_map.get("contingency") or 0
    ]))
    tot_cost = upstream_map.get("total_project_cost") or 0

    report["diagnosed_discrepancies"].append({
        "issue": "PROJECT_COST_COMPONENTS_MISMATCH",
        "description": f"Upstream plant_machinery ({upstream_map.get('plant_machinery')}) + civil ({upstream_map.get('civil_cost')}) + wc_margin ({upstream_map.get('wc_margin')}) + contingency ({upstream_map.get('contingency')}) = {comp_sum} vs total_project_cost = {tot_cost}",
        "upstream_tot": tot_cost,
        "upstream_sum": comp_sum,
        "discrepancy_amount": comp_sum - tot_cost
    })

    # Discrepancy 2: Hardcoded percentages in orchestrator / extract_financial_scalars
    report["diagnosed_discrepancies"].append({
        "issue": "ARBITRARY_SCALAR_FALLBACKS",
        "description": "extract_financial_scalars in document_schema.py used hardcoded multipliers (cost * 0.50, cost * 0.20, cost * 0.15) and static defaults (1000000.0, 1.95, 46.5) when keys differed, violating single source of truth.",
    })

    # Discrepancy 3: Double percentage formatting
    double_pct_matches = re.findall(r"\d+\.?\d*%%", full_text)
    report["diagnosed_discrepancies"].append({
        "issue": "DOUBLE_PERCENTAGE_FORMATTING",
        "description": f"Found double percentage '%%' in PDF text: {double_pct_matches}",
        "occurrences": double_pct_matches
    })

    # Discrepancy 4: Raw Enum rendering
    raw_enums = re.findall(r"(12TH_PASS|NOT_UNDERTAKEN|PROPRIETORSHIP|PVT_LTD|PARTNERSHIP)", full_text)
    report["diagnosed_discrepancies"].append({
        "issue": "RAW_ENUM_EXPOSURE",
        "description": f"Found raw database enums in PDF: {set(raw_enums)}",
        "occurrences": list(set(raw_enums))
    })

    # Discrepancy 5: Raw Internal IDs in bank-facing sections
    internal_id_matches = []
    for line in pages_text[:3]:
        for token in ["dairy_farm", "DPR-dairy_farm", "f44ddd19"]:
            if token in line:
                internal_id_matches.append(token)
    report["diagnosed_discrepancies"].append({
        "issue": "RAW_INTERNAL_IDS_IN_PDF",
        "description": f"Raw internal IDs displayed on Cover / Document Control / Header: {set(internal_id_matches)}",
        "occurrences": list(set(internal_id_matches))
    })

    # Discrepancy 6: Raw GPS string
    gps_found = "Current Location (GPS)" in full_text
    report["diagnosed_discrepancies"].append({
        "issue": "RAW_GPS_LOCATION_STRING",
        "description": "Found 'Current Location (GPS)' on Cover/Glance instead of sanitized institutional location.",
        "found": gps_found
    })

    # Discrepancy 7: TOC Hardcoded page 16
    p16_matches = len(re.findall(r"\b16\b", pages_text[2] + pages_text[3]))
    report["diagnosed_discrepancies"].append({
        "issue": "TOC_PAGE_NUMBER_COLLAPSE",
        "description": f"TOC on pages 3-4 contains {p16_matches} occurrences of '16' assigning almost all sections from 22 onwards to page 16.",
        "p16_count": p16_matches
    })

    # Save JSON report
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Save Markdown report
    md_lines = [
        "# KALPA STAGE 14.3 BANK-GRADE RECONCILIATION DIAGNOSTIC REPORT",
        f"**Scenario ID**: `{scen_data.get('scenario_id')}`",
        f"**Business ID**: `{scen_data.get('business_id')}`",
        f"**Regression PDF**: `{PDF_PATH}` ({page_count} pages)",
        "",
        "## 1. Upstream Authoritative Financial Values",
        "| Field | Upstream Key | Value |",
        "|---|---|---|",
    ]
    for k, v in upstream_map.items():
        md_lines.append(f"| {k} | M1-M6 / Scenario | `{v}` |")

    md_lines.extend([
        "",
        "## 2. Identified Discrepancies & Contradictions",
    ])
    for d in report["diagnosed_discrepancies"]:
        md_lines.append(f"### Issue: `{d['issue']}`")
        md_lines.append(f"- **Description**: {d['description']}")
        if "occurrences" in d:
            md_lines.append(f"- **Occurrences**: `{d['occurrences']}`")
        md_lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Reconciliation diagnostic report written to {OUTPUT_REPORT} and {OUTPUT_MD}")

if __name__ == "__main__":
    run_diagnosis()
