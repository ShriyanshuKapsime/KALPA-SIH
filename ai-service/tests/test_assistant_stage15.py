"""
Targeted Tests for Stage 15: KALPA Personal AI Business Assistant.
Verifies context building (Stages 3–14), intent classification, constraint extraction, memory persistence,
deterministic fallback generation, scoping, and zero-hallucination compliance.
"""
import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.assistant_engine.context_builder import (
    safe_uuid,
    build_full_assistant_context,
    get_intent_context,
    calculate_pipeline_completeness,
    calculate_intent_completeness,
    INTENT_STAGE_MAP
)
from app.services.assistant_engine.assistant_service import (
    detect_intent,
    extract_user_claims_and_constraints,
    build_grounding_metadata,
    generate_contextual_actions,
    assistant_service
)
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse


def test_safe_uuid():
    valid = "12345678-1234-5678-1234-567812345678"
    assert safe_uuid(valid) == uuid.UUID(valid)
    assert safe_uuid(None) is None
    assert safe_uuid("invalid-uuid") is None
    assert safe_uuid(uuid.UUID(valid)) == uuid.UUID(valid)


def test_intent_detection_and_disambiguation():
    # TEST 1: Feasibility score & viability
    assert detect_intent("What is my feasibility score?") == "EXPLAIN_FEASIBILITY"
    assert detect_intent("Why did I get this score?") == "EXPLAIN_FEASIBILITY"
    assert detect_intent("Why is my business viable?") == "EXPLAIN_FEASIBILITY"

    # TEST 2: DSCR & Financial
    assert detect_intent("What is my DSCR?") == "EXPLAIN_FINANCE"
    assert detect_intent("What is my financial score?") == "EXPLAIN_FINANCE"
    assert detect_intent("What is my break even percentage?") == "EXPLAIN_FINANCE"

    # TEST 3: SWOT Weaknesses
    assert detect_intent("What are my biggest weaknesses?") == "EXPLAIN_SWOT"
    assert detect_intent("Explain my SWOT matrix") == "EXPLAIN_SWOT"

    # TEST 4: Next Steps & Planning
    assert detect_intent("What should I do next?") == "NEXT_ACTION"
    assert detect_intent("What are my next steps?") == "NEXT_ACTION"
    assert detect_intent("Where to start?") == "NEXT_ACTION"

    # TEST 5: Loan Guidance & Schemes
    assert detect_intent("How much loan do I need?") == "LOAN_GUIDANCE"
    assert detect_intent("What bank loans am I eligible for?") == "LOAN_GUIDANCE"
    assert detect_intent("Which PMEGP or MUDRA subsidy applies to me?") == "SCHEME_GUIDANCE"

    # TEST 6: Risk
    assert detect_intent("What are my risks?") == "EXPLAIN_RISK"
    assert detect_intent("How risky is my business?") == "EXPLAIN_RISK"

    # TEST 7: Registrations
    assert detect_intent("How do I get Udyam registration?") == "REGISTRATION_QUESTION"


def test_intent_stage_slicing():
    full_ctx = {
        "analysis_id": "11111111-1111-1111-1111-111111111111",
        "business_profile": {"business_name": "Agro Mill"},
        "market_analysis": {"competitor_count": 3},
        "opportunity_result": {"opportunity_score": 85.0},
        "financial_analysis": {"total_project_cost": 500000.0, "dscr": 1.45},
        "entrepreneur_readiness": {"readiness_score": 80.0},
        "risk_analysis": {"overall_risk_score": 25.0},
        "feasibility_result": {"overall_feasibility_score": 82.0},
        "swot_analysis": {"swot": {"strengths": ["Local demand"], "weaknesses": ["Working capital"]}},
        "dpr_report": {"report_type": "dpr"},
    }

    # EXPLAIN_RISK must slice business, risk, market, feasibility
    risk_slice = get_intent_context(full_ctx, "EXPLAIN_RISK")
    assert "business_profile" in risk_slice
    assert "risk_analysis" in risk_slice
    assert "market_analysis" in risk_slice
    assert "feasibility_result" in risk_slice

    # EXPLAIN_SWOT must slice business, swot, feasibility
    swot_slice = get_intent_context(full_ctx, "EXPLAIN_SWOT")
    assert "business_profile" in swot_slice
    assert "swot_analysis" in swot_slice
    assert "feasibility_result" in swot_slice

    # LOAN_GUIDANCE must slice business, financial, feasibility
    loan_slice = get_intent_context(full_ctx, "LOAN_GUIDANCE")
    assert "business_profile" in loan_slice
    assert "financial_analysis" in loan_slice
    assert "feasibility_result" in loan_slice


def test_user_constraint_extraction_no_stage9_overwrite():
    msg1 = "I don't want to borrow more than ₹3 lakh."
    c1 = extract_user_claims_and_constraints(msg1)
    assert len(c1) == 1
    assert c1[0]["type"] == "financial_constraint"
    assert c1[0]["value"] == 300000.0

    msg2 = "My available capital is only Rs 50000."
    c2 = extract_user_claims_and_constraints(msg2)
    assert len(c2) == 1
    assert c2[0]["type"] == "capital_limit"
    assert c2[0]["value"] == 50000.0


def test_missing_upstream_context_no_fabrication_and_no_fake_zeros():
    # Empty context must not invent numbers or replace missing values with ₹0
    empty_slice = {"business_profile": {"business_name": "Test Mill"}}
    resp = assistant_service._generate_deterministic_grounded_response(
        "What is my DSCR?",
        empty_slice,
        "EXPLAIN_FINANCE"
    )
    assert "not yet recorded" in resp.lower() or "not available" in resp.lower()
    assert "₹0" not in resp
    assert "0.0" not in resp

    resp_feas = assistant_service._generate_deterministic_grounded_response(
        "What is my feasibility score?",
        empty_slice,
        "EXPLAIN_FEASIBILITY"
    )
    assert "don't have a verified" in resp_feas.lower()
    assert "/100" not in resp_feas


def test_deterministic_response_exact_facts():
    factual_slice = {
        "business_profile": {"business_name": "Spices Unit"},
        "feasibility_result": {
            "overall_feasibility_score": 88.0,
            "viability_status": "VIABLE",
            "recommendation": "PROCEED"
        },
        "financial_analysis": {
            "total_project_cost": 500000.0,
            "bank_loan_requirement": 350000.0,
            "dscr": 1.55,
            "break_even_percentage": 42.0
        }
    }
    resp = assistant_service._generate_deterministic_grounded_response(
        "What is my feasibility score?",
        factual_slice,
        "EXPLAIN_FEASIBILITY"
    )
    assert "88.0/100" in resp or "88" in resp
    assert "VIABLE" in resp

    resp_fin = assistant_service._generate_deterministic_grounded_response(
        "What is my DSCR?",
        factual_slice,
        "EXPLAIN_FINANCE"
    )
    assert "1.55" in resp_fin
    assert "500,000" in resp_fin


def test_pipeline_completeness_calculation():
    full_ctx = {
        "business_profile": {"business_name": "Dairy Unit"},
        "market_analysis": {"demand": "high"},
        "financial_analysis": {"total_project_cost": 200000.0},
        "entrepreneur_readiness": {"skills": "experienced"},
        "risk_analysis": {"overall_risk": "low"},
        "feasibility_result": {"overall_feasibility_score": 75.0},
        "swot_analysis": {"swot": {"strengths": ["local milk supply"]}}
    }
    comp = calculate_pipeline_completeness(full_ctx)
    assert comp == 1.0

    partial_ctx = {
        "business_profile": {"business_name": "Dairy Unit"},
        "feasibility_result": {"overall_feasibility_score": 75.0}
    }
    comp_partial = calculate_pipeline_completeness(partial_ctx)
    assert 0.2 <= comp_partial <= 0.4


@pytest.mark.asyncio
async def test_assistant_handle_message_multi_stage_scenarios():
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    mock_filter.first.return_value = None
    mock_order.first.return_value = None
    mock_order.all.return_value = []

    # Scenario 1: Next steps
    res1 = await assistant_service.handle_message(
        analysis_id_str="11111111-1111-1111-1111-111111111111",
        session_id_str="22222222-2222-2222-2222-222222222222",
        user_message="What are my next steps?",
        db=mock_db
    )
    assert res1["intent"] == "NEXT_ACTION"
    assert res1["analysis_id"] == "11111111-1111-1111-1111-111111111111"
    assert res1["session_id"] == "22222222-2222-2222-2222-222222222222"
    assert "conversation_id" in res1
    assert "assistant_response" in res1

    # Scenario 2: DSCR inquiry
    res2 = await assistant_service.handle_message(
        analysis_id_str="11111111-1111-1111-1111-111111111111",
        session_id_str="22222222-2222-2222-2222-222222222222",
        user_message="What is my DSCR?",
        db=mock_db
    )
    assert res2["intent"] == "EXPLAIN_FINANCE"

    # Scenario 3: User constraint constraint extraction
    res3 = await assistant_service.handle_message(
        analysis_id_str="11111111-1111-1111-1111-111111111111",
        session_id_str="22222222-2222-2222-2222-222222222222",
        user_message="I don't want to borrow more than ₹3 lakh.",
        db=mock_db
    )
    assert res3["analysis_id"] == "11111111-1111-1111-1111-111111111111"


def test_assistant_api_integration():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.session import get_db

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order
    mock_filter.first.return_value = None
    mock_order.first.return_value = None
    mock_order.all.return_value = []

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Health check
    r_health = client.get("/api/v1/assistant/health")
    assert r_health.status_code == 200
    assert r_health.json() == {"status": "ok", "service": "stage15-assistant"}

    # 2. Invalid UUID in history
    r_bad = client.get("/api/v1/assistant/1111-bad/history")
    assert r_bad.status_code == 400

    # 3. Valid history check via canonical /{analysis_id}/history and legacy /history/{id}
    r_hist1 = client.get("/api/v1/assistant/11111111-1111-1111-1111-111111111111/history")
    assert r_hist1.status_code == 200
    assert "messages" in r_hist1.json()

    r_hist2 = client.get("/api/v1/assistant/history/11111111-1111-1111-1111-111111111111")
    assert r_hist2.status_code == 200
    assert "messages" in r_hist2.json()

    # 4. Valid context check via canonical /{analysis_id}/context and legacy /context/{id}
    r_ctx1 = client.get("/api/v1/assistant/11111111-1111-1111-1111-111111111111/context")
    assert r_ctx1.status_code == 200
    assert "context" in r_ctx1.json()
    assert "pipeline_completeness" in r_ctx1.json()

    r_ctx2 = client.get("/api/v1/assistant/context/11111111-1111-1111-1111-111111111111")
    assert r_ctx2.status_code == 200
    assert "context" in r_ctx2.json()

    # 5. Missing both IDs in chat request
    r_no_id = client.post("/api/v1/assistant/chat", json={"message": "Hello"})
    assert r_no_id.status_code == 400

    # 6. TTS Endpoint check with mocked synthesis
    with patch("app.api.routes.assistant.sarvam_tts_service.synthesize_speech", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": True,
            "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
            "format": "audio/wav",
            "mime_type": "audio/wav",
            "language_code": "hi-IN",
            "spoken_text": "Your feasibility score is 85 out of 100."
        }
        r_tts = client.post("/api/v1/assistant/tts", json={"text": "### Feasibility\nYour score is **85/100**.", "language": "hi"})
        assert r_tts.status_code == 200
        assert r_tts.json()["success"] is True
        assert "audio_base64" in r_tts.json()

    # 7. STT Endpoint check with mocked transcription
    with patch("app.api.routes.assistant.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = ("मेरा नाम राजेश है", "hi")
        fake_audio = b"RIFF....WAVEfmt ....data...." + b"\x00" * 200
        r_stt = client.post(
            "/api/v1/assistant/stt",
            files={"audio": ("sample.webm", fake_audio, "audio/webm")},
            data={"language": "hi"}
        )
        assert r_stt.status_code == 200
        assert r_stt.json()["success"] is True
        assert r_stt.json()["text"] == "मेरा नाम राजेश है"
        assert r_stt.json()["language"] == "hi"

    app.dependency_overrides.clear()


def test_clean_text_for_speech():
    from app.services.sarvam_service import clean_text_for_speech

    raw_text = """### Your Financial Feasibility
Your DSCR is **1.42**.
[STAGE 9: Financial Model]
1. Complete PMEGP training.
2. Verify supplier quota.
- Ensure GST registration.
Check out [Udyam](https://udyamregistration.gov.in).
```json
{"test": 123}
```
"""
    cleaned = clean_text_for_speech(raw_text)
    assert "###" not in cleaned
    assert "**" not in cleaned
    assert "STAGE 9" not in cleaned
    assert "```" not in cleaned
    assert "1.42" in cleaned
    assert "PMEGP" in cleaned


def test_validate_and_resolve_speaker():
    from app.services.sarvam_service import validate_and_resolve_speaker, VALID_BULBUL_V3_SPEAKERS

    # Valid speakers in set
    assert validate_and_resolve_speaker("shreya") == "shreya"
    assert validate_and_resolve_speaker("pooja") == "pooja"
    assert validate_and_resolve_speaker("RITU") == "ritu"
    assert validate_and_resolve_speaker("aditya") == "aditya"

    # None / empty / invalid speaker falls back to shreya
    assert validate_and_resolve_speaker(None) == "shreya"
    assert validate_and_resolve_speaker("") == "shreya"
    assert validate_and_resolve_speaker("meera") == "shreya"
    assert validate_and_resolve_speaker("invalid_xyz") == "shreya"


def test_split_text_for_tts_chunking():
    from app.services.sarvam_service import split_text_for_tts

    # Test 1: text length = 100 -> 1 chunk
    short_text = "आपके व्यवसाय के लिए प्रारंभिक वित्तीय विश्लेषण और व्यवहार्यता स्कोर 85/100 प्राप्त हुआ है।"
    assert len(short_text) < 500
    chunks = split_text_for_tts(short_text, max_chars=500)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    # Test 2: text length = 500 -> exactly 1 chunk
    exact_500 = "अ" * 500
    chunks_500 = split_text_for_tts(exact_500, max_chars=500)
    assert len(chunks_500) == 1
    assert len(chunks_500[0]) == 500

    # Test 3: text length = 501 -> 2 chunks, neither > 500
    text_501 = ("यह एक वाक्य है। " * 35)[:501]
    assert len(text_501) == 501
    chunks_501 = split_text_for_tts(text_501, max_chars=500)
    assert len(chunks_501) >= 2
    for c in chunks_501:
        assert len(c) <= 500

    # Test 4: Realistic Hindi response ~561 chars with danda (।)
    hindi_561 = (
        "आपके व्यवसाय में अनुभव मजबूत है। आपकी वित्तीय स्थिति भी अच्छी है और प्रारंभिक निवेश का प्रबंधन किया जा सकता है। "
        "इसलिए शुरुआत में सीमित स्टॉक और कम लागत वाले विपणन चैनलों के साथ काम करना बेहतर रहेगा। "
        "इसके बाद स्थानीय ग्राहकों से बात करके मांग को सत्यापित करें और अपने उत्पाद की गुणवत्ता सुनिश्चित करें। "
        "पीएमईजीपी योजना के तहत 25 प्रतिशत से 35 प्रतिशत तक पूंजीगत सब्सिडी प्राप्त की जा सकती है। "
        "कार्यशील पूंजी के लिए मुद्रा ऋण का लाभ उठाएं। अपने मासिक कैश फ्लो को पहले छह महीनों तक सावधानीपूर्वक ट्रैक करें। "
        "सभी आवश्यक अनुपालन और जीएसटी पंजीकरण समय पर पूरे करें ताकि व्यापार में कोई रुकावट न आए।"
    )
    assert len(hindi_561) > 500
    hindi_chunks = split_text_for_tts(hindi_561, max_chars=500)
    assert len(hindi_chunks) >= 2
    for hc in hindi_chunks:
        assert len(hc) <= 500
        assert not hc.endswith(" ")
    # Verify Hindi words are preserved and not mangled
    reconstructed = " ".join(hindi_chunks)
    assert "व्यवसाय" in reconstructed
    assert "पीएमईजीपी" in reconstructed
    assert "पूंजीगत" in reconstructed

    # Test 5: Long response ~1200 chars
    long_text = (
        "First Section: Detailed financial feasibility indicates strong debt service coverage ratio of 1.45. "
        "Working capital requirement stands at INR 5.5 Lakhs for initial 3 months of operations. \n\n"
        "Second Section: Market demand shows positive growth in the target tier-2 city corridor. "
        "Competitor concentration is moderate with 4 major organized players and multiple unorganized vendors. \n\n"
        "Third Section: Risk mitigation strategies include phased capital expenditure, pre-arranged raw material supply agreements, "
        "and active registration under the CGTMSE credit guarantee framework to secure collateral-free term loans."
    ) * 2
    long_chunks = split_text_for_tts(long_text, max_chars=500)
    assert len(long_chunks) >= 3
    for lc in long_chunks:
        assert len(lc) <= 500

    # Test 6: Empty text handling
    assert split_text_for_tts("") == []
    assert split_text_for_tts("   ") == []
    assert split_text_for_tts(None) == []


def test_concatenate_wav_audios():
    import io
    import wave
    import base64
    from app.services.sarvam_service import concatenate_wav_audios

    def create_dummy_wav_base64(num_frames: int = 100) -> str:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            # Write dummy PCM 16-bit silence
            w.writeframes(b'\x00\x00' * num_frames)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    wav1 = create_dummy_wav_base64(100)
    wav2 = create_dummy_wav_base64(150)

    combined_b64 = concatenate_wav_audios([wav1, wav2])
    assert combined_b64 is not None
    assert len(combined_b64) > 0

    # Decode and check frames
    raw = base64.b64decode(combined_b64)
    with wave.open(io.BytesIO(raw), 'rb') as w_res:
        assert w_res.getnchannels() == 1
        assert w_res.getsampwidth() == 2
        assert w_res.getframerate() == 22050
        assert w_res.getnframes() == 250

    # Single item passes through
    assert concatenate_wav_audios([wav1]) == wav1
    # Empty list returns empty string
    assert concatenate_wav_audios([]) == ""


def test_hindi_intent_detection():
    # Feasibility / viability in Hindi
    assert detect_intent("मेरे बिज़नेस का स्कोर क्या है?") == "EXPLAIN_FEASIBILITY"
    assert detect_intent("क्या मुझे यह बिज़नेस शुरू करना चाहिए?") == "EXPLAIN_FEASIBILITY"
    assert detect_intent("व्यवसाय व्यवहार्य है या नहीं?") == "EXPLAIN_FEASIBILITY"

    # Risk in Hindi
    assert detect_intent("मेरे बिज़नेस में क्या रिस्क है?") == "EXPLAIN_RISK"
    assert detect_intent("जोखिम कितना है?") == "EXPLAIN_RISK"

    # Finance / DSCR in Hindi
    assert detect_intent("पैसे की स्थिति कैसी है?") == "EXPLAIN_FINANCE"
    assert detect_intent("मेरा बजट और वित्तीय स्कोर क्या है?") == "EXPLAIN_FINANCE"

    # SWOT in Hindi
    assert detect_intent("मेरी कमजोरी क्या है?") == "EXPLAIN_SWOT"
    assert detect_intent("मेरी ताकत और कमजोरियां क्या हैं?") == "EXPLAIN_SWOT"
    assert detect_intent("SWOT विश्लेषण समझाएं") == "EXPLAIN_SWOT"

    # Next steps in Hindi
    assert detect_intent("आगे क्या करना चाहिए?") == "NEXT_ACTION"
    assert detect_intent("पहला कदम क्या होगा?") == "NEXT_ACTION"

    # Loan / Scheme in Hindi
    assert detect_intent("लोन कैसे मिलेगा?") == "LOAN_GUIDANCE"
    assert detect_intent("सरकारी योजना या सब्सिडी क्या है?") == "SCHEME_GUIDANCE"


def test_system_prompt_structure_and_grounding_directives():
    mock_context = {
        "analysis_id": "33333333-3333-3333-3333-333333333333",
        "business_profile": {
            "business_name": "Sharma Organic Dairy",
            "business_type": "Dairy Farming",
            "city": "Indore",
            "state": "Madhya Pradesh"
        },
        "feasibility_result": {
            "overall_feasibility_score": 78.5,
            "viability_status": "CONDITIONALLY_VIABLE",
            "market_score": 59.9,
            "financial_score": 92.0,
            "entrepreneur_fit_score": 85.0,
            "risk_resilience_score": 67.0
        },
        "financial_analysis": {
            "total_project_cost": 850000.0,
            "bank_loan_requirement": 500000.0,
            "dscr": 1.62,
            "break_even_percentage": 38.0
        },
        "swot_analysis": {
            "swot": {
                "strengths": ["High local raw milk supply", "Existing livestock experience"],
                "weaknesses": ["Working capital shortfall", "No cold storage backup"],
                "opportunities": ["B2B supply to urban sweet shops"],
                "threats": ["Feed price volatility"]
            },
            "priority_actions": [
                "Secure working capital credit limit of ₹1.5L",
                "Tie up with 3 local sweet shops for advance orders"
            ],
            "strategic_roadmap": [
                {"phase": "Month 1", "milestone": "Setup cold chillers & register Udyam"}
            ]
        },
        "evidence_gaps": [
            {"gap": "Exact village competitor cold-chain pricing unverified", "severity": "MEDIUM"}
        ],
        "user_memory": [
            {"type": "financial_constraint", "value": 300000.0, "text": "Cannot invest more than ₹3L personal cash"}
        ]
    }

    prompt = assistant_service._build_conversational_system_prompt(
        mock_context,
        intent="EXPLAIN_FEASIBILITY",
        user_lang="hi"
    )

    # 1. Verify 4-pillar scores are present in executive summary
    assert "78.5" in prompt or "78.5" in prompt
    assert "92.0" in prompt or "92" in prompt
    assert "59.9" in prompt
    assert "67.0" in prompt or "67" in prompt

    # 2. Verify Stage 13 priority actions are included
    assert "Secure working capital credit limit" in prompt

    # 3. Verify unverified data gaps section
    assert "Exact village competitor cold-chain pricing unverified" in prompt

    # 4. Verify user constraints
    assert "Cannot invest more than ₹3L personal cash" in prompt

    # 5. Verify Anti-Reanalysis & Grounding Rules are explicit
    assert "NEVER RE-ANALYZE" in prompt
    assert "DATA GAP IS NOT A NEGATIVE FINDING" in prompt
    assert "SYNTHESIZE AND CONNECT FINDINGS ACROSS PILLARS" in prompt
    assert "WHAT -> WHY -> WHAT IT MEANS -> WHAT TO DO" in prompt
    assert "hi" in prompt


def test_deterministic_response_hindi_support():
    mock_context = {
        "business_profile": {"business_name": "Agro Flour Mill"},
        "feasibility_result": {
            "overall_feasibility_score": 82.0,
            "viability_status": "VIABLE",
            "market_score": 75.0,
            "financial_score": 88.0,
            "entrepreneur_fit_score": 80.0,
            "risk_resilience_score": 70.0
        },
        "financial_analysis": {
            "total_project_cost": 600000.0,
            "bank_loan_requirement": 400000.0,
            "dscr": 1.48,
            "break_even_percentage": 45.0
        },
        "swot_analysis": {
            "priority_actions": ["उद्यम पोर्टल पर पंजीकरण पूरा करें", "आपूर्तिकर्ताओं के साथ दरें तय करें"]
        }
    }

    # Hindi question should return Hindi response with correct metrics
    resp_hi = assistant_service._generate_deterministic_grounded_response(
        "मेरा बिज़नेस स्कोर क्या है?",
        mock_context,
        "EXPLAIN_FEASIBILITY"
    )
    assert "82.0/100" in resp_hi or "82" in resp_hi
    assert "व्यवहार्यता" in resp_hi or "स्कोर" in resp_hi

    # Next steps in Hindi
    resp_actions = assistant_service._generate_deterministic_grounded_response(
        "आगे क्या करना चाहिए?",
        mock_context,
        "NEXT_ACTION"
    )
    assert "उद्यम पोर्टल पर पंजीकरण पूरा करें" in resp_actions or "पंजीकरण" in resp_actions
