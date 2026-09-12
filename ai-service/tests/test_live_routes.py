import urllib.request
import urllib.error
import json

def check_url(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    try:
        with urllib.request.urlopen(req, data=body, timeout=10) as response:
            resp_body = response.read().decode("utf-8")
            print(f"[{method}] {url} -> {response.status}")
            try:
                parsed = json.loads(resp_body)
                print(f"   Response keys/sample: {list(parsed.keys()) if isinstance(parsed, dict) else len(parsed)}")
            except Exception:
                print(f"   Response preview: {resp_body[:100]}")
    except urllib.error.HTTPError as e:
        print(f"[{method}] {url} -> HTTPError {e.code}: {e.reason}")
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"   Error body: {err_body[:200]}")
    except Exception as e:
        print(f"[{method}] {url} -> Exception: {e}")

if __name__ == "__main__":
    print("--- Testing AI-Service Direct (Port 8000) ---")
    check_url("http://localhost:8000/health")
    check_url("http://localhost:8000/api/v1/knowledge/business-profiles")
    check_url("http://localhost:8000/api/v1/market-intelligence/tools/health")

    print("\n--- Testing Gateway (Port 3000) ---")
    check_url("http://localhost:3000/health")
    check_url("http://localhost:3000/api/knowledge/business-profiles")
    check_url("http://localhost:3000/api/knowledge/financial-pack/calculate", method="POST", data={"business_id": "rice_mill", "project_cost": 140000.0, "available_margin": 14000.0})
    check_url("http://localhost:3000/api/market-intelligence/tools/health")
    check_url("http://localhost:3000/api/market-intelligence/collect", method="POST", data={"business_profile": {"business_profile": {"specific_business": "Saree Retail"}}})
