import pytest
from app.database.base import Base
from app.database.session import engine
import app.database.models
from app.main import app as fastapi_app
from fastapi.testclient import TestClient

if engine is not None:
    Base.metadata.create_all(bind=engine)

client = TestClient(fastapi_app)


def test_stage3_canonical_profile_full_pipeline():
    """
    End-to-End Test:
    Input: "I want to open a saree shop in my village with 3 lakh rupees and retail experience."
    Stage 1 -> Stage 2 (Saree Retail, NIC 47711) -> Stage 3 (Canonical Structured Business Profile Store)
    """
    # 1. Submit Stage 1 Intake
    intake_payload = {
        "text": "I want to open a saree shop in Chatra, Jharkhand with 3 lakh rupees and retail experience.",
        "language_code": "en"
    }
    res1 = client.post("/api/v1/intake/text", json=intake_payload)
    assert res1.status_code == 200
    intake_data = res1.json()
    session_id = intake_data["session_id"]
    assert session_id is not None
    assert intake_data["profile"]["available_capital"] == 300000.0

    # 2. Stage 2 Classification
    class_payload = {
        "session_id": session_id,
        "original_input": intake_payload["text"],
        "business_concept": "Saree Retail",
        "language_code": "en",
        "product_service": "Silk Sarees, Cotton Sarees",
        "skills": ["retail sales", "customer service"]
    }
    res2 = client.post("/api/v1/classification/classify", json=class_payload)
    assert res2.status_code == 200
    class_data = res2.json()
    assert class_data["classification_status"] == "complete"
    assert class_data["layer_a_nic"]["nic_code"] == "47711"
    assert class_data["layer_b_ontology"]["specific_business"] == "Saree Retail"

    # 3. Stage 3 Profile Build
    res3 = client.post("/api/v1/profile/build", json={"session_id": session_id})
    assert res3.status_code == 200
    build_data = res3.json()
    assert build_data["success"] is True
    assert build_data["workflow_state"] == "BUSINESS_PROFILE_READY"

    profile = build_data["profile"]
    analysis_id = build_data["analysis_id"]
    assert analysis_id is not None

    # Verify Schema & Provenance
    assert profile["schema_version"] == "1.0"
    assert profile["session_id"] == session_id
    assert profile["analysis_id"] == analysis_id
    assert profile["workflow"]["state"] == "BUSINESS_PROFILE_READY"
    assert profile["workflow"]["stage_completed"] == 3

    # Verify Business Profile & NIC
    bus = profile["business_profile"]
    assert bus["specific_business"] == "Saree Retail"
    assert bus["sector"] == "Retail"
    assert bus["nic"]["code"] == "47711"
    assert bus["nic"]["division"]["code"] == "47"
    assert "Saree" in bus["nic"]["description"] or "textiles" in bus["nic"]["description"]
    assert len(bus["products"]) > 0

    # Verify Location Normalization
    loc = profile["location_profile"]
    assert loc["district"] == "Chatra"
    assert loc["state"] == "Jharkhand"
    assert loc["country"] == "India"
    assert loc["source"] == "user"

    # Verify Financial Profile
    fin = profile["financial_profile"]
    assert fin["available_capital"] == 300000.0
    assert fin["currency"] == "INR"

    # Verify Downstream Analysis Requirements (Ontology-derived)
    reqs = profile["analysis_requirements"]
    assert len(reqs["direct_competitors"]) > 0
    assert len(reqs["demand_features"]) > 0
    assert len(reqs["infrastructure_requirements"]) > 0
    assert len(reqs["risk_factors"]) > 0
    assert len(reqs["required_datasets"]) > 0

    # Verify Data Quality
    dq = profile["data_quality"]
    assert dq["profile_complete"] is True
    assert dq["validation_status"] in ["PASSED", "PASSED_WITH_WARNINGS"]

    # 4. Verify Retrieval by Analysis ID
    res4 = client.get(f"/api/v1/profile/{analysis_id}")
    assert res4.status_code == 200
    retrieved_by_aid = res4.json()
    assert retrieved_by_aid["analysis_id"] == analysis_id
    assert retrieved_by_aid["business_profile"]["specific_business"] == "Saree Retail"

    # 5. Verify Retrieval by Session ID
    res5 = client.get(f"/api/v1/profile/session/{session_id}")
    assert res5.status_code == 200
    retrieved_by_sid = res5.json()
    assert retrieved_by_sid["session_id"] == session_id
    assert retrieved_by_sid["analysis_id"] == analysis_id


def test_stage3_profile_versioning_on_rebuild():
    """Verifies that rebuilding a profile increments profile_version and updates updated_at."""
    # 1. Create intake session
    res = client.post("/api/v1/intake/text", json={
        "text": "I want to start a rice mill in Mandya with 5 lakh rupees.",
        "language_code": "en"
    })
    session_id = res.json()["session_id"]

    # 2. First build
    res1 = client.post("/api/v1/profile/build", json={"session_id": session_id})
    assert res1.status_code == 200
    prof1 = res1.json()["profile"]
    assert prof1["profile_version"] == 1
    analysis_id = prof1["analysis_id"]

    # 3. Second build (update)
    res2 = client.post("/api/v1/profile/build", json={"session_id": session_id})
    assert res2.status_code == 200
    prof2 = res2.json()["profile"]
    assert prof2["profile_version"] == 2
    assert prof2["analysis_id"] == analysis_id  # Maintains identity
