import sys
import json
from app.services.financial_engine.engine import financial_engine
from app.services.financial_engine.dpr_packager.dpr_schema import FinancialEngineStatus

businesses_to_test = [
    {
        "id": "saree_retail",
        "name": "Traditional Saree & Ethnic Wear Retail",
        "category": "RETAIL_TRADE",
        "nic": "47711",
        "margin": 100000.0,
        "cost": 500000.0,
    },
    {
        "id": "rice_mill",
        "name": "Modern Mini Rice Mill",
        "category": "AGRI_PROCESSING",
        "nic": "10612",
        "margin": 250000.0,
        "cost": 2500000.0,
    },
    {
        "id": "flour_mill",
        "name": "Atta / Flour Milling Unit",
        "category": "AGRI_PROCESSING",
        "nic": "10611",
        "margin": 200000.0,
        "cost": 2000000.0,
    },
    {
        "id": "grocery_store",
        "name": "General Provision & Kirana Store",
        "category": "RETAIL_TRADE",
        "nic": "47110",
        "margin": 100000.0,
        "cost": 500000.0,
    },
    {
        "id": "dairy_farm",
        "name": "Small Commercial Dairy Farm (10 Animals)",
        "category": "ANIMAL_HUSBANDRY",
        "nic": "01411",
        "margin": 150000.0,
        "cost": 1000000.0,
    },
    {
        "id": "tailoring_shop",
        "name": "Boutique Tailoring & Stitching Center",
        "category": "SERVICES",
        "nic": "14101",
        "margin": 50000.0,
        "cost": 300000.0,
    }
]

print("=" * 80)
print("MULTI-ARCHETYPE PIPELINE CROSS-REGRESSION TEST")
print("=" * 80)

all_passed = True

for biz in businesses_to_test:
    payload = {
        "analysis_id": f"reg_{biz['id']}_001",
        "session_id": f"sess_{biz['id']}_001",
        "business_profile": {
            "business_id": biz["id"],
            "specific_business": biz["name"],
            "business_category": biz["category"],
            "nic_code": biz["nic"]
        },
        "financial_profile": {
            "available_margin_capital": biz["margin"],
            "preferred_project_cost": biz["cost"]
        },
        "beneficiary_profile": {
            "beneficiary_category": "GENERAL",
            "gender": "Male",
            "is_greenfield": True
        }
    }

    try:
        resp = financial_engine.analyze(payload)
        fa = resp.financial_analysis
        dpr = fa.dpr_financial_package

        assert dpr is not None, "DPR Financial Package is None"
        assert dpr.project_cost is not None, "Project Cost is None"
        assert dpr.means_of_finance is not None, "Means of Finance is None"
        assert dpr.loan_structure is not None, "Loan Structure is None"
        assert dpr.banking_metrics is not None, "Banking Metrics is None"
        assert dpr.financial_engine_status in (
            FinancialEngineStatus.READY_FOR_DPR,
            FinancialEngineStatus.READY_WITH_DISCLOSED_UNKNOWNS
        ), f"Unexpected status: {dpr.financial_engine_status}"

        # Verification of balance: Sources == Uses
        total_cost = dpr.project_cost.total_project_cost
        margin = dpr.means_of_finance.promoter_contribution
        loan = dpr.means_of_finance.term_loan
        diff = abs((margin + loan) - total_cost)

        assert diff <= 1.0, f"Balance mismatch: margin({margin}) + loan({loan}) != cost({total_cost})"

        print(f"[PASS] {biz['id']:<18} | Cost: ₹{total_cost:,.2f} | Loan: ₹{loan:,.2f} | Margin: ₹{margin:,.2f} | DSCR: {dpr.banking_metrics.average_dscr} | Status: {dpr.financial_engine_status.value}")

    except Exception as e:
        print(f"[FAIL] {biz['id']:<18} | Error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

print("=" * 80)
if all_passed:
    print("ALL 6 ARCHETYPES PASSED INSTITUTIONAL CROSS-REGRESSION AUDIT SUCCESSFULLY!")
    sys.exit(0)
else:
    print("REGRESSION FAILURES DETECTED!")
    sys.exit(1)
