import requests
import json

BASE_URL = "http://localhost:3000/api"
AI_URL = "http://localhost:8000/api/v1"

def test_live_gateway():
    biz_id = "dairy_farm"
    print("--- 1. Testing Gateway New Scenario ---")
    resp = requests.post(f"{BASE_URL}/dpr/new-scenario/{biz_id}")
    print(f"Gateway New Scenario Status: {resp.status_code}")
    new_data = resp.json()
    print(f"Response: {json.dumps(new_data, indent=2)}")
    scen_id = new_data.get("scenario_id")

    print("\n--- 2. Checking Questions / Gaps on New Scenario ---")
    q_resp = requests.get(f"{BASE_URL}/dpr/question/next/{biz_id}", params={"scenario_id": scen_id})
    print(f"Question Status: {q_resp.status_code}")
    print(f"Question Data: {json.dumps(q_resp.json(), indent=2)[:300]}...")

    print("\n--- 3. Checking 14.2 Readiness for Incomplete Scenario ---")
    r_resp = requests.get(f"{BASE_URL}/dpr/14.2/readiness/{biz_id}", params={"scenario_id": scen_id})
    print(f"Readiness Status: {r_resp.status_code}")
    print(f"Readiness Data: {json.dumps(r_resp.json(), indent=2)}")

if __name__ == "__main__":
    test_live_gateway()
