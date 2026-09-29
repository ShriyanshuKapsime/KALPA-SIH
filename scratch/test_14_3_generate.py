import requests
import json

BASE_URL = "http://localhost:3000/api"

def test_14_3_generate():
    biz_id = "dairy_farm"
    scen_id = "DPR-dairy_farm-413cef57"
    
    print(f"Calling POST {BASE_URL}/dpr/14.3/generate/{biz_id} for scenario {scen_id}...")
    resp = requests.post(
        f"{BASE_URL}/dpr/14.3/generate/{biz_id}",
        json={"scenario_id": scen_id, "format": "pdf", "language": "en"}
    )
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Text response: {resp.text}")

if __name__ == "__main__":
    test_14_3_generate()
