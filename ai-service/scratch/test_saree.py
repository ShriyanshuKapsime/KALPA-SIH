import sys, os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from app.services.financial_engine import financial_engine
import json

payload = {
    "analysis_id": "saree_test_001",
    "session_id": "saree_sess_001",
    "business_profile": {
        "business_id": "saree_retail",
        "specific_business": "Saree Retail",
        "sector": "Retail",
        "category": "Apparel Retail",
        "subcategory": "Women's Traditional Apparel",
    },
    "financial_profile": {
        "available_margin_capital": 200000.0,
        "preferred_project_cost": None,
    },
    "beneficiary_profile": {
        "beneficiary_category": "General",
        "gender": "Female",
        "is_greenfield": True,
    },
    "location_profile": {
        "district": "Varanasi",
        "state": "Uttar Pradesh",
    },
}

resp = financial_engine.analyze(payload)
c = resp.financial_analysis

import pprint

with open("scratch/saree_out.txt", "w", encoding="utf-8") as f:
    f.write("--- PROJECT FINANCING (M1) ---\n")
    if c.project_financing:
        f.write(pprint.pformat(c.project_financing.model_dump()) + "\n")

    f.write("\n--- CAPITAL STRUCTURE (M1) ---\n")
    if c.capital_structure:
        f.write(pprint.pformat(c.capital_structure.model_dump()) + "\n")

    f.write("\n--- PROJECT COST ANALYSIS (M2) ---\n")
    if c.project_cost_analysis:
        f.write(pprint.pformat(c.project_cost_analysis.model_dump()) + "\n")

    f.write("\n--- WORKING CAPITAL (M2) ---\n")
    if c.working_capital_analysis:
        f.write(pprint.pformat(c.working_capital_analysis.model_dump()) + "\n")

    f.write("\n--- DPR FINANCIAL PACKAGE (M6) ---\n")
    pkg = c.dpr_financial_package
    if pkg:
        f.write("Project Cost:\n" + pprint.pformat(pkg.project_cost.model_dump()) + "\n")
        f.write("Means of Finance:\n" + pprint.pformat(pkg.means_of_finance.model_dump()) + "\n")
        f.write("Loan Structure:\n" + pprint.pformat(pkg.loan_structure.model_dump()) + "\n")
        f.write("Banking Metrics:\n" + pprint.pformat(pkg.banking_metrics.model_dump()) + "\n")
        f.write("Completeness:\n" + pprint.pformat(pkg.data_completeness.model_dump()) + "\n")

    f.write("\n--- FINANCING OPTIMIZER (M5) ---\n")
    if c.financing_optimizer:
        f.write(pprint.pformat(c.financing_optimizer.model_dump()) + "\n")
    print("principal:", c.loan_management.principal)
    print("monthly_emi:", c.loan_management.monthly_emi)
    print("annual_interest_rate:", c.loan_management.annual_interest_rate)
    print("tenure_months:", c.loan_management.tenure_months)

print("\n--- DPR FINANCIAL PACKAGE (M6) ---")
pkg = c.dpr_financial_package
if pkg:
    print("PC total_project_cost:", pkg.project_cost.total_project_cost)
    print("MOF promoter_contribution:", pkg.means_of_finance.promoter_contribution)
    print("MOF term_loan:", pkg.means_of_finance.term_loan)
    print("MOF total_funding:", pkg.means_of_finance.total_funding)
    print("MOF is_gap_eliminated:", pkg.means_of_finance.is_gap_eliminated)
    print("LS sanctioned_loan_amount:", pkg.loan_structure.sanctioned_loan_amount)
    print("LS monthly_emi:", pkg.loan_structure.monthly_emi)
    print("BM average_dscr:", pkg.banking_metrics.average_dscr)
    print("BM break_even_sales_amount:", pkg.banking_metrics.break_even_sales_amount)
    print("DC status:", pkg.data_completeness.status)
    print("DC unresolved:", pkg.data_completeness.unresolved_fields)

print("\n--- FINANCING OPTIMIZER (M5) ---")
if c.financing_optimizer:
    print("status:", c.financing_optimizer.status)
    print("financing options count:", len(c.financing_optimizer.financing_options))
    for s in c.financing_optimizer.financing_options[:3]:
        print(f"  Scheme: {s.scheme_name}, Loan: {s.loan_amount}, Margin: {s.promoter_contribution}, Rate: {s.interest_rate}, EMI: {s.monthly_emi}, Stress DSCR: {s.stress_case_dscr}")
