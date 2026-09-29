import requests

BASE_URL = "http://localhost:3000/api"
DOC_ID = "KALPA-DPR-DAIRY_FA-DCB5E4"

def test_endpoints():
    print(f"--- 1. Testing GET {BASE_URL}/dpr/14.3/status/{DOC_ID} ---")
    s_resp = requests.get(f"{BASE_URL}/dpr/14.3/status/{DOC_ID}")
    print(f"Status response: {s_resp.status_code}, data: {s_resp.json()}")

    print(f"\n--- 2. Testing GET {BASE_URL}/dpr/14.3/preview/{DOC_ID} ---")
    p_resp = requests.get(f"{BASE_URL}/dpr/14.3/preview/{DOC_ID}")
    print(f"Preview response: {p_resp.status_code}, content-type: {p_resp.headers.get('content-type')}, bytes: {len(p_resp.content)}")

if __name__ == "__main__":
    test_endpoints()
