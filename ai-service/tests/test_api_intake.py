import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_text_intake_hindi():
    payload = {
        "text": "मैं मांड्या में ₹2 लाख के साथ डेयरी फार्म शुरू करना चाहता हूँ। मुझे पशुपालन का अनुभव है।"
    }
    response = client.post("/api/v1/intake/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data
    assert data["language"]["code"] == "hi"
    assert data["profile"]["business_concept"] == "Dairy Farm"
    assert data["profile"]["available_capital"] == 200000
    assert data["profile"]["proposed_location"]["district"] == "Mandya"
    assert data["profile"]["stage_1_complete"] is True


def test_api_text_intake_minimal_and_continue():
    # 1. Minimal text
    payload = {"text": "I want to start a dairy business."}
    response = client.post("/api/v1/intake/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    assert "available_capital" in data["missing_fields"]
    assert "proposed_location" in data["missing_fields"]
    assert data["profile"]["stage_1_complete"] is False

    # 2. Continue intake with capital
    cont_payload = {
        "session_id": session_id,
        "answers": {
            "available_capital": 200000
        },
        "field": "available_capital"
    }
    cont_response = client.post("/api/v1/intake/continue", json=cont_payload)
    assert cont_response.status_code == 200
    cont_data = cont_response.json()
    assert cont_data["profile"]["available_capital"] == 200000
    assert "available_capital" not in cont_data["missing_fields"]


def test_api_text_intake_empty_error():
    payload = {"text": "   "}
    response = client.post("/api/v1/intake/text", json=payload)
    assert response.status_code == 422
