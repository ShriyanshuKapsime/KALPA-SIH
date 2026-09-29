import urllib.request
import json

def test(url, desc):
    print(f"Testing {desc}: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"  -> SUCCESS ({resp.status}): business_id={data.get('business_id')}, scenario_id={data.get('scenario_id')}")
            return resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  -> HTTP {e.code}: {body[:150]}")
        return e.code
    except Exception as e:
        print(f"  -> ERROR: {e}")
        return None

print("=== GATEWAY LIVE VERIFICATION ===")
s1 = test("http://localhost:3000/api/dpr/context/Kirana?scenario_id=DPR-Kirana", "Valid Context Kirana")
assert s1 == 200, f"Expected 200, got {s1}"

s2 = test("http://localhost:3000/api/dpr/context/Kirana%20?scenario_id=DPR-Kirana", "Context Kirana with trailing space")
assert s2 == 200, f"Expected 200, got {s2}"

s3 = test("http://localhost:3000/api/dpr/14.2/enrichment/Kirana?scenario_id=DPR-Kirana", "Enrichment Kirana")
assert s3 == 200, f"Expected 200, got {s3}"

s4 = test("http://localhost:3000/api/dpr/context/Kirana?scenario_id=DPR-saree_re", "Invalid Scenario DPR-saree_re on Kirana")
assert s4 == 409, f"Expected 409, got {s4}"

s5 = test("http://localhost:3000/api/dpr/14.2/enrichment/Kirana?scenario_id=DPR-saree_re", "Enrichment with mismatched scenario")
assert s5 == 409, f"Expected 409, got {s5}"

print("\nALL GATEWAY LIVE CHECKS PASSED PERFECTLY!")
