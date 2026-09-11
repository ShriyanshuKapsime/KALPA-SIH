import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.classification.ontology_service import normalize_business_concept, is_ambiguous_concept
from app.services.classification.nic_repository import search_official_nic_candidates, get_official_nic_record
from app.services.classification.hierarchy_validator import validate_nic_hierarchy
from app.services.classification.confidence_calculator import calculate_deterministic_confidence

client = TestClient(app)


def test_english_rice_mill_classification():
    payload = {
        "original_input": "I want to start a rice mill in Mandya with ₹2 lakh.",
        "business_concept": "Rice Mill",
        "language_code": "en",
        "product_service": "Paddy Milling & Rice Processing",
        "skills": ["agriculture"]
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "complete"
    assert data["clarification_needed"] is False
    assert data["layer_b_ontology"]["specific_business"] == "Rice Mill"
    assert "Grain Processing" in data["layer_b_ontology"]["category"]
    assert data["layer_a_nic"]["nic_code"] == "10612"
    assert data["classification_confidence"] >= 0.75
    assert data["confidence_level"] in ["HIGH", "MEDIUM"]
    assert "breakdown" in data["official_classification"]["confidence"]
    assert data["orchestrator_context"]["profile_ready"] is True
    assert data["orchestrator_context"]["official_nic_code"] == "10612"


def test_hindi_rice_mill_classification():
    payload = {
        "original_input": "मैं मांड्या में चावल की मिल शुरू करना चाहता हूँ",
        "business_concept": "चावल की मिल",
        "language_code": "hi"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "complete"
    assert data["layer_b_ontology"]["specific_business"] == "Rice Mill"
    assert data["layer_a_nic"]["nic_code"] == "10612"
    assert data["classification_confidence"] >= 0.75


def test_kannada_rice_mill_classification():
    payload = {
        "original_input": "ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ಅಕ್ಕಿ ಗಿರಣಿ ಆರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ",
        "business_concept": "ಅಕ್ಕಿ ಗಿರಣಿ",
        "language_code": "kn"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "complete"
    assert data["layer_b_ontology"]["specific_business"] == "Rice Mill"
    assert data["layer_a_nic"]["nic_code"] == "10612"
    assert data["classification_confidence"] >= 0.75


def test_hindi_dairy_farm_classification():
    payload = {
        "original_input": "मैं अपने गांव में डेयरी फार्म शुरू करना चाहता हूं",
        "business_concept": "डेयरी फार्म",
        "language_code": "hi"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "complete"
    assert data["layer_b_ontology"]["specific_business"] == "Dairy Farm"
    assert data["layer_a_nic"]["nic_code"] in ["01411", "01412", "10501"]


def test_kannada_dairy_farm_classification():
    payload = {
        "original_input": "ನಾನು ಹಾಲಿನ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ",
        "business_concept": "ಹಾಲಿನ ಡೈರಿ ಫಾರ್ಮ್",
        "language_code": "kn"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "complete"
    assert data["layer_b_ontology"]["specific_business"] == "Dairy Farm"
    assert data["layer_a_nic"]["nic_code"] in ["01411", "01412", "10501"]


def test_ambiguous_clothing_triggers_clarification():
    payload = {
        "original_input": "I want to start a clothing business.",
        "business_concept": "clothing business",
        "language_code": "en"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "needs_clarification"
    assert data["clarification_needed"] is True
    assert data["clarification"] is not None
    assert len(data["clarification"]["options"]) > 0


def test_ambiguous_food_business_triggers_clarification():
    payload = {
        "original_input": "I want to start a food business.",
        "business_concept": "food business",
        "language_code": "en"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "needs_clarification"
    assert data["clarification_needed"] is True
    assert data["clarification"] is not None


def test_unknown_business_does_not_assign_random_nic():
    payload = {
        "original_input": "I want to build a quantum teleportation chamber in outer space.",
        "business_concept": "quantum teleportation chamber",
        "language_code": "en"
    }
    response = client.post("/api/v1/classification/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["classification_status"] == "needs_clarification"
    assert data["clarification_needed"] is True
    assert data["layer_a_nic"] is None


def test_hierarchy_validation():
    rec = get_official_nic_record("10612")
    assert rec is not None
    is_valid, score, reason = validate_nic_hierarchy(rec)
    assert is_valid is True
    assert score == 1.0


def test_clarify_flow():
    # 1. Ambiguous initial request
    payload = {
        "session_id": "test-session-clarify-canonical-1",
        "original_input": "I want to start a clothing business.",
        "business_concept": "clothing business",
        "language_code": "en"
    }
    res1 = client.post("/api/v1/classification/classify", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["classification_status"] == "needs_clarification"
    
    # 2. Clarify with Saree Retail
    clarify_payload = {
        "session_id": "test-session-clarify-canonical-1",
        "answer": "Saree Retail",
        "language_code": "en"
    }
    res2 = client.post("/api/v1/classification/clarify", json=clarify_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["classification_status"] == "complete"
    assert data2["layer_b_ontology"]["specific_business"] == "Saree Retail"
    assert data2["layer_a_nic"]["nic_code"] == "47711"
    assert data2["orchestrator_context"]["profile_ready"] is True
    assert data2["orchestrator_context"]["official_nic_code"] == "47711"


def test_nic_details_endpoint():
    response = client.get("/api/v1/classification/nic/10612")
    assert response.status_code == 200
    data = response.json()
    assert data["activity"]["code"] == "10612"
    assert "Rice" in data["activity"]["title"]
