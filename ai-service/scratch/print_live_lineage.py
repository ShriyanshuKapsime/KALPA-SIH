import httpx
import json

biz_id = "555a6f15-de8f-4f52-828c-5bfec7b57da0"
url = f"http://localhost:8000/api/v1/dpr/14.2/lineage/{biz_id}"
r = httpx.get(url)
print("HTTP Status:", r.status_code)
data = r.json()
fl = data.get("field_lineage", {})
print("Total Canonical Fields in Lineage:", len(fl))

fields = [
    "business_archetype",
    "nic_code",
    "promoter_experience_years",
    "covered_area_sqft",
    "total_project_cost",
    "bank_term_loan_amount",
    "promoter_equity_amount",
    "glance_average_dscr",
    "glance_break_even_utilization",
    "target_scheme_code",
    "dynamic_swot_matrix",
    "risk_mitigation_matrix",
    "feasibility_viability_synthesis",
    "evidence_source_register",
    "financial_integrity_verification",
]

print("-" * 80)
print(f"{'FIELD ID':<32} | {'STATUS':<20} | {'VALUE'}")
print("-" * 80)
for k in fields:
    rec = fl.get(k, {})
    val = rec.get("value")
    st = rec.get("status")
    if isinstance(val, (dict, list)):
        val_str = f"Structured [{type(val).__name__} with {len(val)} items]"
    else:
        val_str = str(val)
    print(f"{k:<32} | {str(st):<20} | {val_str}")
print("-" * 80)
