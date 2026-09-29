import requests
import json
import time

BASE_URL = "http://localhost:3000/api"

def run_lifecycle():
    biz_id = "dairy_farm"
    print("==================================================")
    print("STEP 1: Create New Scenario via Gateway")
    print("==================================================")
    resp = requests.post(f"{BASE_URL}/dpr/new-scenario/{biz_id}")
    assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"
    scen_info = resp.json()
    scen_id = scen_info["scenario_id"]
    print(f"Created Scenario: {scen_id}")

    print("\n==================================================")
    print("STEP 2: Answer 14.1 Questions Iteratively")
    print("==================================================")
    answers_to_provide = {
        "promoter_name": "Sunil Deshmukh",
        "business_name": "Deshmukh Dairy Farm",
        "location_state": "Maharashtra",
        "location_district": "Pune",
        "primary_product_name": "Cow Milk",
        "operational_unit_count": 10,
        "daily_production_sales_units": 150,
        "unit_selling_price": 55,
        "total_project_cost": 1200000,
        "promoter_equity_amount": 300000,
        "bank_term_loan_amount": 900000,
    }

    for i in range(15):
        q_resp = requests.get(f"{BASE_URL}/dpr/question/next/{biz_id}", params={"scenario_id": scen_id})
        q_data = q_resp.json()
        if not q_data.get("has_question"):
            print(f"No more 14.1 questions! Message: {q_data.get('message')}")
            break
        q = q_data["question"]
        fid = q["field_id"]
        ans = answers_to_provide.get(fid, "Standard Value")
        print(f"Answering Q{i+1}: field_id={fid} -> ans={ans}")
        ans_resp = requests.post(
            f"{BASE_URL}/dpr/question/answer/{biz_id}",
            json={"field_id": fid, "value": ans, "scenario_id": scen_id}
        )
        if ans_resp.status_code != 200:
            print(f"Error answering {fid}: {ans_resp.text}")

    print("\n==================================================")
    print("STEP 3: Check Stage 14.1 Handoff / Readiness")
    print("==================================================")
    handoff_resp = requests.get(f"{BASE_URL}/dpr/handoff/{biz_id}", params={"scenario_id": scen_id})
    print(f"Handoff Status: {handoff_resp.status_code}")
    handoff_data = handoff_resp.json()
    is_ready_14_2 = handoff_data.get("readiness", {}).get("is_ready_for_stage_14_2")
    print(f"is_ready_for_stage_14_2: {is_ready_14_2}")
    if not is_ready_14_2:
        print(f"Blocking reasons for 14.2 handoff: {handoff_data.get('readiness', {}).get('reasons')}")

    print("\n==================================================")
    print("STEP 4: Run Stage 14.2 Enrichment")
    print("==================================================")
    enr_resp = requests.post(f"{BASE_URL}/dpr/enrichment/run/{biz_id}", params={"scenario_id": scen_id})
    print(f"Enrichment Run Status: {enr_resp.status_code}")
    enr_data = enr_resp.json()
    print(f"Enrichment summary: total_fields={len(enr_data.get('fields', {}))}")

    print("\n==================================================")
    print("STEP 5: Check Stage 14.2 -> 14.3 Readiness")
    print("==================================================")
    r14_2_resp = requests.get(f"{BASE_URL}/dpr/14.2/readiness/{biz_id}", params={"scenario_id": scen_id})
    print(f"14.2 Readiness Status: {r14_2_resp.status_code}")
    r14_2_data = r14_2_resp.json()
    print(f"ready_for_stage_14_3: {r14_2_data.get('ready_for_stage_14_3')}")
    print(f"blocking_reasons: {r14_2_data.get('blocking_reasons')}")
    print(f"unresolved_required_fields: {r14_2_data.get('unresolved_required_fields')}")

if __name__ == "__main__":
    run_lifecycle()
