"""
KALPA SIH — Comprehensive End-to-End Data Lineage & DPR Golden Verification Suite
Tests:
1. Scenario A: Grocery Shop (NIC 47110) End-to-End (Stage 1 -> 3 -> Finance -> 14.1 -> 14.2)
2. Scenario B: Saree Retail (NIC 47711) Legitimate Flow
3. Scenario C: Cross-Session State Isolation (Grocery vs Dairy)
4. Scenario D: Zero-Question Gate & Readiness Trigger
5. Scenario E: Diagnostic Lineage Endpoint Validation
"""
import sys
import json
import urllib.request
import urllib.error

GATEWAY_URL = "http://127.0.0.1:3000/api/v1"
AI_SERVICE_URL = "http://127.0.0.1:8000/api/v1"

PROHIBITED_TOKENS = [
    "saree_retail",
    "Saree Retail",
    "47711",
    "Women's Traditional Apparel",
    "Banarasi Saree"
]

def make_req(method, url, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed
    except Exception as e:
        return 500, {"error": str(e)}


def assert_clean_of_prohibited(data, context_name=""):
    serialized = json.dumps(data)
    for tok in PROHIBITED_TOKENS:
        if tok in serialized:
            raise AssertionError(f"CRITICAL LEAKAGE: Found prohibited token '{tok}' in {context_name}!")
    print(f"  [PASS] Verified zero prohibited tokens in {context_name}")


def run_tests():
    print("======================================================================")
    print("KALPA SIH: COMPREHENSIVE END-TO-END DATA LINEAGE VERIFICATION")
    print("======================================================================")

    # ------------------------------------------------------------------
    # 1. SCENARIO A: GROCERY SHOP (NIC 47110) FLOW
    # ------------------------------------------------------------------
    print("\n--- [TEST 1] Scenario A: Grocery Shop (NIC 47110) Flow ---")
    intake_payload = {
        "text": "I want to start a grocery shop (kirana store) in Mandya Karnataka with 2 lakh rupees capital. My name is Suresh Kumar.",
        "language": "en"
    }
    status, intake_res = make_req("POST", f"{GATEWAY_URL}/intake/text", intake_payload)
    assert status == 200, f"Intake failed with status {status}: {intake_res}"
    session_id = intake_res.get("session_id")
    print(f"  [PASS] Stage 1 Intake Success: session_id={session_id}")

    # Build profile (Stage 3)
    profile_payload = {
        "session_id": session_id,
        "specific_business": "Grocery Store",
        "category": "Retail",
        "sector": "Retail",
        "nic_code": "47110",
        "location": {"district": "Mandya", "state": "Karnataka"},
        "entrepreneur": {"name": "Suresh Kumar", "experience_years": 3}
    }
    status, profile_res = make_req("POST", f"{GATEWAY_URL}/profile/build", profile_payload)
    assert status == 200, f"Profile build failed: {profile_res}"
    analysis_id = profile_res.get("analysis_id")
    print(f"  [PASS] Stage 3 Profile Built: analysis_id={analysis_id}")

    # Financial Engine Calculation
    fin_calc_payload = {
        "analysis_id": analysis_id,
        "session_id": session_id,
        "business_profile": {
            "business_id": "grocery_store",
            "business_node_id": "grocery_store",
            "specific_business": "Grocery Store",
            "sector": "Retail",
            "category": "Retail",
            "subcategory": "Grocery Store",
            "nic_code": "47110"
        },
        "financial_profile": {
            "available_margin_capital": 50000,
            "preferred_project_cost": 200000
        },
        "location_profile": {
            "district": "Mandya",
            "state": "Karnataka"
        }
    }
    status, fin_res = make_req("POST", f"{GATEWAY_URL}/financial-analysis/analyze", fin_calc_payload)
    assert status == 200, f"Finance calculation failed: {fin_res}"
    fin_pkg = fin_res.get("package") or fin_res.get("financial_context") or fin_res
    print(f"  [PASS] Finance M1-M6 Calculation Completed")

    # Assert no saree leakage in financial calculation
    assert_clean_of_prohibited(fin_res, "Finance M1-M6 Calculation Package")

    # Stage 14.1 DPR Gap Discovery
    status, dpr_res = make_req("GET", f"{GATEWAY_URL}/dpr/context/{analysis_id}")
    assert status == 200, f"DPR context failed: {dpr_res}"
    assert_clean_of_prohibited(dpr_res, "Stage 14.1 DPR Context")
    print(f"  [PASS] Stage 14.1 DPR Context Clean & Verified")

    # Stage 14.1 Next Question
    status, q_res = make_req("GET", f"{GATEWAY_URL}/dpr/question/next/{analysis_id}?language=en")
    assert status == 200, f"Next question failed: {q_res}"
    assert_clean_of_prohibited(q_res, "Stage 14.1 Next Question")
    print(f"  [PASS] Stage 14.1 Question Framer Tested (Clean, No Saree Reference)")

    # ------------------------------------------------------------------
    # 2. SCENARIO B: LEGITIMATE SAREE RETAIL FLOW (NIC 47711)
    # ------------------------------------------------------------------
    print("\n--- [TEST 2] Scenario B: Legitimate Saree Retail Flow (NIC 47711) ---")
    saree_intake = {
        "text": "I want to start a silk saree retail shop in Varanasi Uttar Pradesh with 5 lakh rupees capital. My name is Priya Sharma.",
        "language": "en"
    }
    status, s_res = make_req("POST", f"{GATEWAY_URL}/intake/text", saree_intake)
    assert status == 200, f"Saree intake failed: {s_res}"
    s_sid = s_res.get("session_id")
    print(f"  [PASS] Saree Retail Intake Succeeded: session_id={s_sid}")

    # Build profile
    s_profile = {
        "session_id": s_sid,
        "specific_business": "Saree Retail",
        "category": "Retail",
        "sector": "Retail",
        "nic_code": "47711",
        "location": {"district": "Varanasi", "state": "Uttar Pradesh"},
        "entrepreneur": {"name": "Priya Sharma"}
    }
    status, s_prof_res = make_req("POST", f"{GATEWAY_URL}/profile/build", s_profile)
    assert status == 200, f"Saree profile failed: {s_prof_res}"
    s_aid = s_prof_res.get("analysis_id")
    print(f"  [PASS] Saree Retail Profile Built: analysis_id={s_aid}")

    # Finance for Saree
    s_fin_payload = {
        "analysis_id": s_aid,
        "session_id": s_sid,
        "business_profile": {
            "business_id": "saree_retail",
            "business_node_id": "saree_retail",
            "specific_business": "Saree Retail",
            "sector": "Retail",
            "category": "Retail",
            "subcategory": "Saree Retail",
            "nic_code": "47711"
        },
        "financial_profile": {
            "available_margin_capital": 100000,
            "preferred_project_cost": 500000
        },
        "location_profile": {
            "district": "Varanasi",
            "state": "Uttar Pradesh"
        }
    }
    status, s_fin_res = make_req("POST", f"{GATEWAY_URL}/financial-analysis/analyze", s_fin_payload)
    assert status == 200, f"Saree finance failed: {s_fin_res}"
    print(f"  [PASS] Saree Retail Finance calculation passed with legitimate 47711 NIC")

    # ------------------------------------------------------------------
    # 3. SCENARIO C: CROSS-SESSION STATE ISOLATION
    # ------------------------------------------------------------------
    print("\n--- [TEST 3] Scenario C: Cross-Session State Isolation ---")
    # Verify Session A (Grocery) still clean after Saree calculation
    status, groc_check = make_req("GET", f"{GATEWAY_URL}/dpr/context/{analysis_id}")
    assert status == 200
    assert_clean_of_prohibited(groc_check, "Session A Context Post-Session B Run")
    print(f"  [PASS] Cross-Session Isolation Verified: Session A unaffected by Session B")

    # ------------------------------------------------------------------
    # 4. SCENARIO D: ZERO-QUESTION RESOLUTION GATE & STAGE 14.2 UNLOCK
    # ------------------------------------------------------------------
    print("\n--- [TEST 4] Scenario D: Zero-Question Resolution Gate & Stage 14.2 Unlock ---")
    status, gap_res = make_req("GET", f"{GATEWAY_URL}/dpr/gap-analysis/{analysis_id}")
    assert status == 200, f"Gap analysis failed: {gap_res}"
    print(f"  [PASS] Initial Stage 14.1 Gap Analysis: is_ready_for_stage_14_2={gap_res.get('is_ready_for_stage_14_2')}")

    # Answer the missing promoter name
    ans_payload = {"field_id": "promoter_name", "answer": "Suresh Kumar"}
    status, ans_res = make_req("POST", f"{GATEWAY_URL}/dpr/question/answer/{analysis_id}", ans_payload)
    assert status == 200, f"Answer question failed: {ans_res}"
    assert ans_res.get("success") is True, f"Answer submission unsuccessful: {ans_res}"
    assert ans_res.get("is_ready_for_stage_14_2") is True, f"Expected is_ready_for_stage_14_2 to become True, got {ans_res.get('is_ready_for_stage_14_2')}"
    print(f"  [PASS] Stage 14.1 Critical Gaps Resolved: is_ready_for_stage_14_2 = True!")

    # Verify Stage 14.2 Enrichment Execution
    status, enrich_res = make_req("POST", f"{GATEWAY_URL}/dpr/enrichment/run/{analysis_id}", {})
    assert status == 200, f"Enrichment run failed: {enrich_res}"
    assert enrich_res.get("ready_for_stage_14_3") is True or enrich_res.get("is_ready_for_stage_14_3") is True, "Expected ready_for_stage_14_3 to be True"
    assert_clean_of_prohibited(enrich_res, "Stage 14.2 Enriched DPR Package")
    print(f"  [PASS] Stage 14.2 DPR Enrichment Completed: Ready for Stage 14.3 Bankable DPR!")

    # ------------------------------------------------------------------
    # 5. SCENARIO E: DIAGNOSTIC LINEAGE ENDPOINT VALIDATION
    # ------------------------------------------------------------------
    print("\n--- [TEST 5] Scenario E: Diagnostic Lineage Endpoint Validation ---")
    status, lin_res = make_req("GET", f"{GATEWAY_URL}/dpr/stage1/debug/lineage/{analysis_id}")
    assert status == 200, f"Lineage endpoint failed: {lin_res}"
    assert lin_res.get("status") == "SUCCESS", "Lineage status not SUCCESS"
    assert "intake_lineage" in lin_res, "intake_lineage missing"
    assert "upstream_cards" in lin_res, "upstream_cards missing"
    assert "financial_engine_lineage" in lin_res, "financial_engine_lineage missing"
    assert_clean_of_prohibited(lin_res, "Diagnostic Lineage Payload for Grocery")
    print(f"  [PASS] Diagnostic Lineage Verified: Clean data lineage confirmed")

    print("\n======================================================================")
    print("ALL 5 GOLDEN TESTS PASSED WITH ZERO DATA LEAKAGE!")
    print("======================================================================")


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] UNEXPECTED ERROR: {e}")
        sys.exit(1)
