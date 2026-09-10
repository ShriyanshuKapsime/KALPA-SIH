import pytest
from app.services.language_detector import detect_language
from app.services.money_normalizer import parse_indian_money
from app.services.entity_extractor import extract_deterministic_entities
from app.services.intake_pipeline import process_user_intake, continue_user_intake
from app.services.sarvam_service import normalize_sarvam_language


def test_sarvam_language_normalization():
    # English
    assert normalize_sarvam_language("English") == "en-IN"
    assert normalize_sarvam_language("en") == "en-IN"
    assert normalize_sarvam_language("en-IN") == "en-IN"

    # Hindi
    assert normalize_sarvam_language("Hindi") == "hi-IN"
    assert normalize_sarvam_language("hi") == "hi-IN"
    assert normalize_sarvam_language("hi-IN") == "hi-IN"

    # Kannada
    assert normalize_sarvam_language("Kannada") == "kn-IN"
    assert normalize_sarvam_language("kn") == "kn-IN"
    assert normalize_sarvam_language("kn-IN") == "kn-IN"

    # Marathi, Tamil, Telugu
    assert normalize_sarvam_language("mr") == "mr-IN"
    assert normalize_sarvam_language("ta") == "ta-IN"
    assert normalize_sarvam_language("te") == "te-IN"

    # Unknown / None / Ambiguous fallback
    assert normalize_sarvam_language(None) == "unknown"
    assert normalize_sarvam_language("") == "unknown"
    assert normalize_sarvam_language("auto") == "unknown"
    assert normalize_sarvam_language("unknown") == "unknown"
    assert normalize_sarvam_language("xyz_unsupported") == "unknown"


def test_money_normalization_multilingual():
    # English variations
    assert parse_indian_money("I have 2 lakh rupees")[0] == 200000
    assert parse_indian_money("budget of ₹2 lakhs")[0] == 200000
    assert parse_indian_money("two lakh rupees")[0] == 200000
    assert parse_indian_money("1.5 lakh")[0] == 150000
    assert parse_indian_money("₹50,000")[0] == 50000
    assert parse_indian_money("1.5 crore")[0] == 15000000

    # Kannada variations
    assert parse_indian_money("ಎರಡು ಲಕ್ಷ")[0] == 200000
    assert parse_indian_money("2 ಲಕ್ಷ")[0] == 200000
    assert parse_indian_money("50 ಸಾವಿರ")[0] == 50000
    assert parse_indian_money("ಮೂರು ಲಕ್ಷ")[0] == 300000

    # Hindi variations
    assert parse_indian_money("मेरे पास तीन लाख रुपये हैं")[0] == 300000
    assert parse_indian_money("₹2 लाख")[0] == 200000
    assert parse_indian_money("पचास हजार")[0] == 50000


def test_language_detection_priority():
    # English
    lang_code, lang_name = detect_language("I want to open a rice mill in Mandya.")
    assert lang_code == "en"
    assert lang_name == "English"

    # Kannada
    lang_code, lang_name = detect_language("ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ")
    assert lang_code == "kn"
    assert lang_name == "Kannada"

    # Hindi
    lang_code, lang_name = detect_language("मैं मांड्या में डेयरी फार्म शुरू करना चाहता हूँ।")
    assert lang_code == "hi"
    assert lang_name == "Hindi"

    # Marathi
    lang_code, lang_name = detect_language("मी माझ्या गावात किराणा दुकान सुरू करू इच्छितो")
    assert lang_code == "mr"
    assert lang_name == "Marathi"


@pytest.mark.asyncio
async def test_scenario_1_complete_english_input():
    # "I want to start a rice mill in Mandya with ₹2 lakh. I have experience in agriculture."
    text = "I want to start a rice mill in Mandya with ₹2 lakh. I have experience in agriculture."
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.business_concept == "Rice Mill"
    assert res.profile.intent == "start_business"
    assert res.profile.available_capital == 200000
    assert res.profile.proposed_location.district == "Mandya"
    assert res.profile.proposed_location.source == "user"
    assert len(res.profile.entrepreneur_skills) > 0
    assert res.profile.stage_1_complete is True
    assert res.next_action.type == "complete"
    assert len(res.missing_fields) == 0


@pytest.mark.asyncio
async def test_scenario_2_english_missing_skills():
    # "I want to open a dairy farm in Mysuru with ₹3 lakh."
    text = "I want to open a dairy farm in Mysuru with ₹3 lakh."
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.business_concept == "Dairy Farm"
    assert res.profile.available_capital == 300000
    assert res.profile.proposed_location.district == "Mysuru"
    assert "entrepreneur_skills" in res.missing_fields
    assert res.profile.stage_1_complete is False
    assert res.next_action.field == "entrepreneur_skills"
    assert "experience or skills" in res.next_action.question.lower()


@pytest.mark.asyncio
async def test_scenario_3_existing_business_expansion():
    # "I already run a grocery store and want to expand it. I can invest ₹1 lakh."
    text = "I already run a grocery store and want to expand it. I can invest ₹1 lakh."
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.intent == "expand_business"
    assert res.profile.business_concept == "Grocery & Kirana Store"
    assert res.profile.available_capital == 100000
    assert "proposed_location" in res.missing_fields
    assert "entrepreneur_skills" in res.missing_fields
    assert res.profile.stage_1_complete is False


@pytest.mark.asyncio
async def test_scenario_4_hindi_intake_and_clarification():
    # Hindi text
    text = "मैं मांड्या में डेयरी फार्म शुरू करना चाहता हूँ।"
    res = await process_user_intake(text=text, input_type="text")

    assert res.language.code == "hi"
    assert res.profile.business_concept == "Dairy Farm"
    assert res.profile.proposed_location.district == "Mandya"
    assert res.next_action.language == "hi"
    assert "पैसा या बजट" in res.next_action.question or "निवेश" in res.next_action.question


@pytest.mark.asyncio
async def test_scenario_5_kannada_intake_and_clarification():
    # Kannada full input
    text = "ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ₹2 ಲಕ್ಷ ಬಂಡವಾಳದೊಂದಿಗೆ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ. ನನಗೆ ಹೈನುಗಾರಿಕೆ ಅನುಭವವಿದೆ."
    res = await process_user_intake(text=text, input_type="text")

    assert res.language.code == "kn"
    assert res.profile.business_concept == "Dairy Farm"
    assert res.profile.available_capital == 200000
    assert res.profile.proposed_location.district == "Mandya"
    assert len(res.profile.entrepreneur_skills) > 0
    assert res.profile.stage_1_complete is True
    assert res.next_action.type == "complete"


@pytest.mark.asyncio
async def test_scenario_6_gps_fallback():
    # User does not provide location
    text = "I want to start a bakery with ₹1 lakh. I have baking experience."
    res = await process_user_intake(text=text, input_type="text")

    assert "proposed_location" in res.missing_fields
    assert res.profile.stage_1_complete is False

    # Submit GPS location
    updated = await continue_user_intake(
        session_id=res.session_id,
        gps_location={
            "latitude": 12.5218,
            "longitude": 76.8951,
            "accuracy": 15.0,
            "city": "Mandya"
        }
    )

    assert updated.profile.proposed_location.latitude == 12.5218
    assert updated.profile.proposed_location.longitude == 76.8951
    assert updated.profile.proposed_location.source == "gps"
    assert updated.profile.stage_1_complete is True


@pytest.mark.asyncio
async def test_scenario_7_user_location_overrides_gps():
    # User explicitly sets location to Mandya
    text = "I want to open a dairy farm in Mandya with ₹2 lakh. I have farming experience."
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.proposed_location.district == "Mandya"
    assert res.profile.proposed_location.source == "user"

    # Later GPS says Bengaluru
    updated = await continue_user_intake(
        session_id=res.session_id,
        gps_location={
            "latitude": 12.9716,
            "longitude": 77.5946,
            "city": "Bengaluru"
        }
    )

    # User location MUST REMAIN Mandya
    assert updated.profile.proposed_location.district == "Mandya"
    assert updated.profile.proposed_location.name == "Mandya"
    assert updated.profile.proposed_location.source == "user"


@pytest.mark.asyncio
async def test_scenario_8_explicit_no_experience_skills():
    text = "I want to open a saree shop in Nagpur with ₹3 lakh."
    res = await process_user_intake(text=text, input_type="text")
    assert "entrepreneur_skills" in res.missing_fields

    # User responds "I don't have experience"
    updated = await continue_user_intake(
        session_id=res.session_id,
        answers={"skills_status": "no_experience", "skills": "no experience"},
        field="entrepreneur_skills"
    )

    assert updated.profile.skills_status == "no_experience"
    assert updated.profile.entrepreneur_skills == []
    assert "entrepreneur_skills" not in updated.missing_fields
    assert updated.profile.stage_1_complete is True
