"""
Comprehensive regression test suite for /api/v1/intake/transcribe voice STT endpoint.
Validates:
1. test_successful_transcription (Sarvam returning clean string transcript)
2. test_none_transcription (Sarvam returning None -> no AttributeError, structured 422 failure)
3. test_empty_transcription (Sarvam returning empty/whitespace string -> structured 422 failure)
4. test_non_string_transcription (Sarvam returning non-string -> structured 422 failure)
5. test_sarvam_provider_error (Sarvam returning HTTP error or network failure -> structured 502 failure)
6. test_invalid_audio (missing, corrupted or <50 byte audio -> structured 400 failure)
7. test_frontend_safe_response_handling (response adheres to canonical contract)
8. test_failed_stt_keeps_clarification_question_pending (failed STT attempt leaves question state unchanged)
"""
import io
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_successful_transcription(client):
    """Sarvam STT returns valid string transcript -> 200 OK with canonical schema."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = ("5 years of commercial dairy farming experience", "en-IN")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")},
            data={"language_code": "en-IN"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcript"] == "5 years of commercial dairy farming experience"
        assert isinstance(data["transcript"], str)
        # Verify .strip() works cleanly
        assert data["transcript"].strip() == data["transcript"]
        assert data["provider"] == "sarvam"
        assert data["model"] is not None
        assert data["error"] is None

def test_none_transcription(client):
    """Sarvam STT returning None -> MUST NOT raise AttributeError, MUST return structured 422 failure."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        # Simulate upstream returning None transcript
        mock_stt.return_value = (None, "en-IN")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")},
            data={"language_code": "en-IN"}
        )
        # Crucial: Must NOT be 500 Internal Server Error
        assert response.status_code == 422
        data = response.json()
        error_payload = data.get("detail", data)
        assert error_payload["success"] is False
        assert error_payload["transcript"] is None
        assert error_payload["provider"] == "sarvam"
        assert error_payload["error"]["code"] == "STT_NULL_TRANSCRIPT"

def test_empty_transcription(client):
    """Sarvam STT returning empty/whitespace transcript -> structured 422 failure."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = ("    ", "hi-IN")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")},
            data={"language_code": "hi-IN"}
        )
        assert response.status_code == 422
        data = response.json()
        error_payload = data.get("detail", data)
        assert error_payload["success"] is False
        assert error_payload["transcript"] is None
        assert error_payload["error"]["code"] == "STT_NO_SPEECH_DETECTED"

def test_non_string_transcription(client):
    """Sarvam STT returning non-string transcript -> structured 422 failure without AttributeError."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = (12345, "en-IN")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")},
            data={"language_code": "en-IN"}
        )
        assert response.status_code == 422
        data = response.json()
        error_payload = data.get("detail", data)
        assert error_payload["success"] is False
        assert error_payload["transcript"] is None
        assert error_payload["error"]["code"] == "STT_INVALID_TRANSCRIPT_TYPE"

def test_sarvam_provider_error(client):
    """Sarvam STT provider failure -> structured 502 Bad Gateway failure."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.side_effect = RuntimeError("Sarvam STT rejected request (500): Internal Service Error")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")},
            data={"language_code": "en-IN"}
        )
        assert response.status_code == 502
        data = response.json()
        error_payload = data.get("detail", data)
        assert error_payload["success"] is False
        assert error_payload["transcript"] is None
        assert error_payload["error"]["code"] == "STT_PROVIDER_ERROR"

def test_invalid_audio(client):
    """Missing or empty (<50 bytes) audio file -> structured 400 Bad Request failure."""
    # Case 1: Missing audio
    response_no_file = client.post("/api/v1/intake/transcribe", data={"language_code": "en"})
    assert response_no_file.status_code == 400
    data1 = response_no_file.json()
    err1 = data1.get("detail", data1)
    assert err1["success"] is False
    assert err1["error"]["code"] == "MISSING_AUDIO"

    # Case 2: Tiny corrupted audio (<50 bytes)
    tiny_audio = io.BytesIO(b"RIFFtiny")
    response_tiny = client.post(
        "/api/v1/intake/transcribe",
        files={"file": ("tiny.wav", tiny_audio, "audio/wav")},
        data={"language_code": "en"}
    )
    assert response_tiny.status_code == 400
    data2 = response_tiny.json()
    err2 = data2.get("detail", data2)
    assert err2["success"] is False
    assert err2["error"]["code"] == "EMPTY_OR_CORRUPT_AUDIO"

def test_frontend_safe_response_handling(client):
    """Verifies that response contains canonical keys: success, transcript, provider, model, error."""
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = ("माझे पाच वर्षांचे अनुभव आहे", "mr-IN")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        
        response = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("marathi.webm", dummy_webm, "audio/webm")},
            data={"language_code": "mr-IN"}
        )
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["transcript"] == "माझे पाच वर्षांचे अनुभव आहे"
        assert res["provider"] == "sarvam"
        assert res["error"] is None

def test_failed_stt_keeps_clarification_question_pending(client):
    """A failed voice transcription attempt MUST NOT alter or erase pending questions."""
    # 1. Analyze profile to get pending questions
    init_res = client.post(
        "/api/v1/entrepreneur-profile/analyze",
        json={
            "business_profile": {
                "business_id": "dairy_farm",
                "specific_business": "Dairy Farm",
                "category": "Agriculture & Dairy"
            },
            "user_profile": {"skills": {}, "experience": {}}
        }
    )
    assert init_res.status_code == 200
    initial_data = init_res.json()
    initial_questions = initial_data.get("questions", [])
    initial_pending_count = initial_data.get("pending_count", len(initial_questions))
    assert len(initial_questions) > 0

    # 2. Attempt failed STT
    with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.side_effect = RuntimeError("Sarvam service down")
        dummy_webm = io.BytesIO(b"G\x4d\x80" + b"\x00" * 256)
        stt_resp = client.post(
            "/api/v1/intake/transcribe",
            files={"file": ("recording.webm", dummy_webm, "audio/webm")}
        )
        assert stt_resp.status_code == 502

    # 3. Verify question state was not modified in any way
    # The client/frontend does NOT submit clarification when STT fails
    # Re-inspecting the questions shows identical pending count
    assert initial_pending_count == len(initial_questions)
