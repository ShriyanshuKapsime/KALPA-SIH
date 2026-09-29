import requests
import json

BASE_URL = "http://localhost:3000/api"

def test_resolve():
    biz_id = "dairy_farm"
    
    # 1. Create a fresh scenario
    resp = requests.post(f"{BASE_URL}/dpr/new-scenario/{biz_id}")
    scen_data = resp.json()
    scen_id = scen_data["scenario_id"]
    print(f"Created Scenario: {scen_id}")

    # 2. Answer 14.1 critical inputs correctly
    answers_14_1 = {
        "promoter_name": "Dr. Sunil Deshmukh",
        "business_name": "Deshmukh Dairy Farm",
        "location_state": "Maharashtra",
        "location_district": "Pune",
        "premises_status": "OWNED",
        "primary_product_name": "Cow Milk",
    }

    for fid, ans in answers_14_1.items():
        ans_resp = requests.post(
            f"{BASE_URL}/dpr/question/answer/{biz_id}",
            json={"field_id": fid, "answer": ans, "scenario_id": scen_id}
        )
        print(f"Answered 14.1 {fid}: status={ans_resp.status_code}")

    # 3. Check 14.1 handoff
    handoff_resp = requests.get(f"{BASE_URL}/dpr/handoff/{biz_id}", params={"scenario_id": scen_id})
    print(f"Handoff is_ready_for_stage_14_2: {handoff_resp.json().get('readiness', {}).get('is_ready_for_stage_14_2')}")

    # 4. Run Stage 14.2 Enrichment
    enr_resp = requests.post(f"{BASE_URL}/dpr/enrichment/run/{biz_id}", params={"scenario_id": scen_id})
    print(f"Enrichment run status: {enr_resp.status_code}")

    # 5. Check 14.2 Readiness before addressing remaining gaps
    r1 = requests.get(f"{BASE_URL}/dpr/14.2/readiness/{biz_id}", params={"scenario_id": scen_id}).json()
    print(f"\nInitial 14.2 Readiness:")
    print(f"  ready_for_stage_14_3: {r1.get('ready_for_stage_14_3')}")
    print(f"  blocking_reasons: {r1.get('blocking_reasons')}")
    print(f"  unresolved_required_fields: {r1.get('unresolved_required_fields')}")

    # 6. Answer remaining gaps if any
    unresolved = r1.get('unresolved_required_fields', [])
    gap_answers = {
        "promoter_education": "GRADUATE",
        "cost_plant_machinery": 750000,
        "receivable_credit_days": 15,
        "inventory_holding_days": 15,
        "monthly_wages_total": 50000,
        "unit_selling_price": 60,
        "daily_production_sales_units": 200,
        "premises_status": "OWNED",
    }

    for fid in unresolved:
        val = gap_answers.get(fid, 10000 if "cost" in fid or "amount" in fid else "STANDARD")
        print(f"Resolving 14.2 gap: {fid} -> {val}")
        ans_resp = requests.post(
            f"{BASE_URL}/dpr/14.2/answer/{biz_id}",
            json={"field_id": fid, "answer": val, "scenario_id": scen_id}
        )
        print(f"  Result: {ans_resp.status_code}")

    # 7. Final 14.2 Readiness Check
    r2 = requests.get(f"{BASE_URL}/dpr/14.2/readiness/{biz_id}", params={"scenario_id": scen_id}).json()
    print(f"\nFinal 14.2 Readiness:")
    print(f"  ready_for_stage_14_3: {r2.get('ready_for_stage_14_3')}")
    print(f"  blocking_reasons: {r2.get('blocking_reasons')}")
    print(f"  unresolved_required_fields: {r2.get('unresolved_required_fields')}")

if __name__ == "__main__":
    test_resolve()
