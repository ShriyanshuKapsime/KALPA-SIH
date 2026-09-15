import uuid
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.services.language_detector import detect_language, LANGUAGE_MAP
from app.services.entity_extractor import extract_deterministic_entities, refine_with_llm
from app.services.money_normalizer import parse_indian_money
from app.services.intake.canonical_extractor import canonical_intake_extractor
from app.schemas.intake import (
    Stage1Profile,
    Stage1IntakeResponse,
    LocationData,
    ExistingBusinessData,
    NextAction,
    NextActionOption,
    LanguageDetail,
    UserIntakeProfile,
    InputMetadata,
    IntentInfo,
    BusinessInfo,
    EntrepreneurInfo,
    FinancialInfo,
    LocationInfo,
    FollowUpQuestion,
)
from app.database.models.intake import IntakeSession

# Fast in-memory session cache for resilience across environments
_IN_MEMORY_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Multilingual Clarification Templates (English, Kannada, Hindi, Marathi, Tamil, Telugu)
CLARIFICATION_TEMPLATES = {
    "business_concept": {
        "en": {
            "question": "What type of business would you like to start or expand?",
            "helper_text": "For example: dairy farming, rice mill, grocery shop, tailoring, food processing, etc.",
        },
        "kn": {
            "question": "ನೀವು ಯಾವ ರೀತಿಯ ವ್ಯವಹಾರ ಅಥವಾ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಅಥವಾ ವಿಸ್ತರಿಸಲು ಬಯಸುತ್ತೀರಿ?",
            "helper_text": "ಉದಾಹರಣೆಗೆ: ಡೈರಿ ಫಾರ್ಮ್, ರೈಸ್ ಮಿಲ್, ಕಿರಾಣಿ ಅಂಗಡಿ, ಟೈಲರಿಂಗ್, ಆಹಾರ ಸಂಸ್ಕರಣೆ ಇತ್ಯಾದಿ.",
        },
        "hi": {
            "question": "आप किस प्रकार का व्यवसाय या उद्यम शुरू या विस्तार करना चाहते हैं?",
            "helper_text": "उदाहरण के लिए: डेयरी फार्म, राइस मिल, किराना दुकान, सिलाई केंद्र, खाद्य प्रसंस्करण आदि।",
        },
        "mr": {
            "question": "तुम्हाला कोणत्या प्रकारचा व्यवसाय सुरू किंवा विस्तार करायचा आहे?",
            "helper_text": "उदा: डेअरी फार्म, किराणा दुकान, राईस मिल, टेलरिंग, अन्न प्रक्रिया इ.",
        },
    },
    "intent": {
        "en": {
            "question": "Are you planning to start a new business or expand an existing business?",
            "helper_text": "Select whether this is a fresh venture or scaling up an existing enterprise.",
            "options": [
                {"label": "Start New Business", "value": "start_business"},
                {"label": "Expand Existing Business", "value": "expand_business"}
            ]
        },
        "kn": {
            "question": "ನೀವು ಹೊಸ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಯೋಜಿಸುತ್ತಿದ್ದೀರಾ ಅಥವಾ ಈಗಾಗಲೇ ಇರುವ ವ್ಯವಹಾರವನ್ನು ವಿಸ್ತರಿಸಲು ಬಯಸುತ್ತೀರಾ?",
            "helper_text": "ಹೊಸ ಉದ್ಯಮವೇ ಅಥವಾ ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ವ್ಯಾಪಾರದ ವಿಸ್ತರಣೆಯೇ ಎಂಬುದನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
            "options": [
                {"label": "ಹೊಸ ಉದ್ಯಮ ಪ್ರಾರಂಭಿಸಿ", "value": "start_business"},
                {"label": "ಹಾಲಿ ಉದ್ಯಮ ವಿಸ್ತರಿಸಿ", "value": "expand_business"}
            ]
        },
        "hi": {
            "question": "क्या आप नया व्यवसाय शुरू करना चाहते हैं या किसी मौजूदा व्यवसाय का विस्तार करना चाहते हैं?",
            "helper_text": "कृपया चुनें कि यह नया उद्यम है या पुराने व्यवसाय का विस्तार।",
            "options": [
                {"label": "नया व्यवसाय शुरू करें", "value": "start_business"},
                {"label": "मौजूदा व्यवसाय का विस्तार करें", "value": "expand_business"}
            ]
        },
        "mr": {
            "question": "तुम्ही नवीन व्यवसाय सुरू करत आहात की सध्याचा व्यवसाय वाढवत आहात?",
            "helper_text": "कृपया निवडा की हा नवीन व्यवसाय आहे की विस्तार.",
            "options": [
                {"label": "नवीन व्यवसाय सुरू करा", "value": "start_business"},
                {"label": "सध्याचा व्यवसाय वाढवा", "value": "expand_business"}
            ]
        }
    },
    "available_capital": {
        "en": {
            "question": "How much money or budget can you invest in this business?",
            "helper_text": "For example: ₹50,000, ₹2 lakh, or ₹5 lakh.",
        },
        "kn": {
            "question": "ಈ ವ್ಯವಹಾರಕ್ಕಾಗಿ ನೀವು ಎಷ್ಟು ಹಣ ಅಥವಾ ಬಂಡವಾಳವನ್ನು ಹೂಡಿಕೆ ಮಾಡಬಹುದು?",
            "helper_text": "ಉದಾಹರಣೆಗೆ: ₹50,000, ₹2 ಲಕ್ಷ, ಅಥವಾ ₹5 ಲಕ್ಷ.",
        },
        "hi": {
            "question": "इस व्यवसाय के लिए आप कितना पैसा या बजट निवेश कर सकते हैं?",
            "helper_text": "उदाहरण के लिए: ₹50,000, ₹2 लाख, या ₹5 लाख।",
        },
        "mr": {
            "question": "या व्यवसायासाठी तुम्ही किती भांडवल किंवा रक्कम गुंतवू शकता?",
            "helper_text": "उदा: ₹50,000, ₹2 लाख, किंवा ₹5 लाख.",
        }
    },
    "proposed_location": {
        "en": {
            "question": "Where do you plan to run this business?",
            "helper_text": "You can enter your village, town, taluk, district, or city. Or tap 'Use Current Location'.",
        },
        "kn": {
            "question": "ಈ ವ್ಯವಹಾರವನ್ನು ನೀವು ಎಲ್ಲಿ (ಗ್ರಾಮ, ತಾಲೂಕು, ನಗರ ಅಥವಾ ಜಿಲ್ಲೆ) ನಡೆಸಲು ಯೋಜಿಸುತ್ತಿದ್ದೀರಿ?",
            "helper_text": "ನಿಮ್ಮ ಗ್ರಾಮ, ತಾಲೂಕು, ಜಿಲ್ಲೆ ಅಥವಾ ನಗರವನ್ನು ನಮೂದಿಸಿ ಅಥವಾ ಪ್ರಸ್ತುತ ಸ್ಥಳವನ್ನು ಬಳಸಿ.",
        },
        "hi": {
            "question": "आप इस व्यवसाय को कहाँ (गाँव, कस्बा, तहसील या जिला) चलाना चाहते हैं?",
            "helper_text": "आप अपना गाँव, कस्बा, जिला या शहर दर्ज कर सकते हैं या वर्तमान स्थान का उपयोग कर सकते हैं।",
        },
        "mr": {
            "question": "तुम्ही हा व्यवसाय कुठे (गाव, तालुका, शहर किंवा जिल्हा) सुरू करू इच्छिता?",
            "helper_text": "तुमचे गाव, तालुका किंवा जिल्हा प्रविष्ट करा किंवा वर्तमान स्थान वापरा.",
        }
    },
    "entrepreneur_skills": {
        "en": {
            "question": "What experience or skills do you have that could help with this business?",
            "helper_text": "For example: farming, dairy, tailoring, retail sales, cooking, machinery, carpentry, etc.",
        },
        "kn": {
            "question": "ಈ ವ್ಯವಹಾರಕ್ಕೆ ಸಹಾಯಕವಾಗುವಂತಹ ಯಾವ ಅನುಭವ ಅಥವಾ ಕೌಶಲ್ಯಗಳು ನಿಮ್ಮಲ್ಲಿವೆ?",
            "helper_text": "ಉದಾಹರಣೆಗೆ: ಕೃಷಿ, ಹೈನುಗಾರಿಕೆ, ಟೈಲರಿಂಗ್, ವ್ಯಾಪಾರ, ಅಡುಗೆ, ಮರಗೆಲಸ ಇತ್ಯಾದಿ.",
        },
        "hi": {
            "question": "इस व्यवसाय के लिए आपके पास क्या अनुभव या कौशल है जो मददगार हो सकता है?",
            "helper_text": "उदाहरण के लिए: खेती, डेयरी, सिलाई, दुकानदारी/बिक्री, खाना बनाना, मशीनरी आदि।",
        },
        "mr": {
            "question": "या व्यवसायासाठी तुमच्याकडे कोणता अनुभव किंवा कौशल्य आहे?",
            "helper_text": "उदा: शेती, डेअरी, शिलाई, विक्री/दुकानदारी, स्वयंपाक इ.",
        }
    }
}


def normalize_multilingual_text(text: str) -> str:
    """Applies unicode NFKC normalization, whitespace compression, and basic cleanup."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = " ".join(normalized.split())
    return normalized


def evaluate_stage1_missing_fields(
    business_concept: Optional[str],
    intent: Optional[str],
    available_capital: Optional[int],
    proposed_location: LocationData,
    skills_status: str,
    skills_list: List[str]
) -> List[str]:
    """
    Evaluates required fields for Stage 1 in strict priority order:
    1. business_concept
    2. intent (start_business | expand_business | existing_business)
    3. available_capital
    4. proposed_location (needs name, district, or GPS lat/lon)
    5. entrepreneur_skills (needs collected skills OR explicit no_experience)
    """
    missing = []

    # 1. Business concept
    if not business_concept or not str(business_concept).strip():
        missing.append("business_concept")

    # 2. Intent
    if not intent or intent == "unknown":
        missing.append("intent")

    # 3. Available capital
    if available_capital is None or available_capital < 0:
        missing.append("available_capital")

    # 4. Location
    has_loc = (
        bool(proposed_location.district and proposed_location.district.strip()) or
        bool(proposed_location.name and proposed_location.name.strip()) or
        (proposed_location.latitude is not None and proposed_location.longitude is not None)
    )
    if not has_loc:
        missing.append("proposed_location")

    # 5. Entrepreneur Skills
    if skills_status not in ["collected", "no_experience"]:
        if not skills_list or len(skills_list) == 0:
            missing.append("entrepreneur_skills")

    return missing


def build_next_action(missing_fields: List[str], language_code: str = "en") -> NextAction:
    """
    Builds language-aware NextAction clarification or completion block.
    Asks only ONE question at a time following priority order.
    """
    if not missing_fields:
        return NextAction(
            type="complete",
            field=None,
            question="",
            helper_text="",
            language=language_code,
            input_modes=["text", "voice"],
            tts_supported=True
        )

    field = missing_fields[0]
    tmpl_field = CLARIFICATION_TEMPLATES.get(field, {})

    # Fallback to English if current language template is not defined
    tmpl = tmpl_field.get(language_code) or tmpl_field.get("en", {
        "question": f"Please provide information for {field}.",
        "helper_text": ""
    })

    options = None
    if "options" in tmpl:
        options = [NextActionOption(**opt) for opt in tmpl["options"]]

    return NextAction(
        type="clarification",
        field=field,
        question=tmpl.get("question", ""),
        helper_text=tmpl.get("helper_text", ""),
        language=language_code,
        input_modes=["text", "voice"],
        tts_supported=True,
        options=options
    )


async def process_user_intake(
    text: str,
    input_type: str = "text",
    language_override: Optional[str] = None,
    user_id: Optional[str] = None,
    selected_language: Optional[str] = None,
    db: Optional[Session] = None
) -> Stage1IntakeResponse:
    """
    End-to-End Multilingual Stage 1 Intake Pipeline:
    Unicode Normalization -> Language Detection (Indic + English + Hinglish) ->
    Compositional Number & Amount Extraction -> Business Entity Extraction ->
    LLM Refinement (with graceful offline fallback) -> Missing Field Evaluation ->
    Intelligent Clarification Generation -> Persistence.
    """
    original_text = text.strip() if text else ""
    normalized_text = normalize_multilingual_text(original_text)
    logger.info(f"[STAGE 1 INTAKE PIPELINE] input_type='{input_type}', text='{normalized_text[:60]}...'")

    # Execute Canonical Intake Extractor
    canonical = await canonical_intake_extractor.extract_canonical_profile(
        text=normalized_text,
        language_hint=language_override or selected_language,
        use_llm_refinement=True
    )

    lang_dict = canonical.get("language", {})
    lang_code = lang_dict.get("code", "en")
    lang_name = lang_dict.get("name", "English")
    active_lang = selected_language or lang_code

    business_concept = canonical.get("business_concept")
    business_category_hint = canonical.get("business_category_hint")
    intent = canonical.get("intent", "start_business")
    business_stage = canonical.get("business_stage", "planning")
    available_capital = canonical.get("available_capital")
    capital_currency = canonical.get("capital_currency", "INR")

    loc_dict = canonical.get("proposed_location", {})
    proposed_location = LocationData(
        name=loc_dict.get("name", ""),
        district=loc_dict.get("district", ""),
        state=loc_dict.get("state", ""),
        country=loc_dict.get("country", "India"),
        latitude=loc_dict.get("latitude"),
        longitude=loc_dict.get("longitude"),
        source=loc_dict.get("source", "unresolved")
    )

    skills_list = canonical.get("entrepreneur_skills", [])
    skills_status = canonical.get("skills_status", "unspecified")
    if skills_list and skills_status == "unspecified":
        skills_status = "collected"

    existing_bus_dict = canonical.get("existing_business", {})
    existing_business = ExistingBusinessData(
        exists=existing_bus_dict.get("exists", intent in ["expand_business", "existing_business"]),
        type=existing_bus_dict.get("type", business_concept or ""),
        current_status=existing_bus_dict.get("current_status", "operational" if intent in ["expand_business", "existing_business"] else "")
    )

    confidence = canonical.get("confidence", {})

    # Evaluate Missing Fields
    missing_fields = evaluate_stage1_missing_fields(
        business_concept=business_concept,
        intent=intent,
        available_capital=available_capital,
        proposed_location=proposed_location,
        skills_status=skills_status,
        skills_list=skills_list
    )

    is_complete = (len(missing_fields) == 0)

    # Generate Language-Consistent Next Action Clarification
    next_action = build_next_action(missing_fields, language_code=active_lang)

    session_id = str(uuid.uuid4())

    profile = Stage1Profile(
        session_id=session_id,
        original_input=original_text,
        input_mode=input_type,
        detected_language=lang_name,
        language_code=lang_code,
        selected_language=active_lang,
        business_concept=business_concept,
        business_category_hint=business_category_hint,
        intent=intent,
        business_stage=business_stage,
        available_capital=available_capital,
        capital_currency=capital_currency,
        proposed_location=proposed_location,
        entrepreneur_skills=skills_list,
        skills_status=skills_status,
        existing_business=existing_business,
        missing_fields=missing_fields,
        clarification_history=[],
        confidence=confidence,
        stage_1_complete=is_complete
    )

    response = Stage1IntakeResponse(
        success=True,
        session_id=session_id,
        language=LanguageDetail(
            detected=lang_name,
            code=lang_code,
            selected=active_lang
        ),
        profile=profile,
        missing_fields=missing_fields,
        next_action=next_action
    )

    # Save to memory cache
    _IN_MEMORY_SESSIONS[session_id] = {
        "profile": profile.model_dump(),
        "response": response.model_dump(),
        "language_detail": response.language.model_dump()
    }

    # 7. Persist to PostgreSQL if active
    if db is not None:
        try:
            session_record = IntakeSession(
                id=uuid.UUID(session_id),
                user_id=uuid.UUID(user_id) if user_id else None,
                input_type=input_type,
                original_text=original_text,
                normalized_text=normalized_text,
                language_code=lang_code,
                language_name=lang_name,
                structured_profile=profile.model_dump(),
                pipeline_status="completed"
            )
            db.add(session_record)
            db.commit()
            db.refresh(session_record)
        except Exception as e:
            logger.warning(f"Failed to persist intake session to database ({e}). Retained in memory cache.")
            db.rollback()

    return response


async def continue_user_intake(
    session_id: str,
    answers: Optional[Dict[str, Any]] = None,
    follow_up_text: Optional[str] = None,
    field: Optional[str] = None,
    language_code: Optional[str] = None,
    gps_location: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Stage1IntakeResponse:
    """
    Intelligently merges follow-up answers into the existing Stage 1 session profile.
    Supports text, voice transcripts, button selections, and browser GPS fallback.
    """
    answers = answers or {}
    existing_dict: Optional[Dict[str, Any]] = None
    session_record: Optional[IntakeSession] = None

    if db is not None:
        try:
            session_record = db.query(IntakeSession).filter(IntakeSession.id == uuid.UUID(session_id)).first()
            if session_record and session_record.structured_profile:
                existing_dict = session_record.structured_profile
        except Exception as e:
            logger.warning(f"Database lookup error ({e}), checking in-memory session cache.")

    if not existing_dict:
        cached_entry = _IN_MEMORY_SESSIONS.get(session_id)
        if cached_entry:
            existing_dict = cached_entry.get("profile")

    if not existing_dict:
        # Create empty profile baseline if not found
        existing_profile = Stage1Profile(session_id=session_id)
    else:
        existing_profile = Stage1Profile(**existing_dict)

    active_lang = language_code or existing_profile.selected_language or existing_profile.language_code or "en"
    existing_profile.selected_language = active_lang

    clarification_entry = {
        "field": field,
        "input_text": follow_up_text,
        "answers": answers,
        "gps": bool(gps_location)
    }
    existing_profile.clarification_history.append(clarification_entry)

    # 1. Process Conversational Follow-Up Text if provided
    if follow_up_text and follow_up_text.strip():
        text_clean = normalize_multilingual_text(follow_up_text)

        # Handle explicit "no experience" in text
        no_exp_markers = ["no experience", "don't have experience", "ಯಾವುದೇ ಅನುಭವವಿಲ್ಲ", "ಅನುಭವವಿಲ್ಲ", "कोई अनुभव नहीं", "अनुभव नहीं है"]
        if any(nem in text_clean.lower() for nem in no_exp_markers):
            existing_profile.skills_status = "no_experience"
            existing_profile.entrepreneur_skills = []
        else:
            extra_extracted = extract_deterministic_entities(text_clean, language_code=active_lang)

            # Merge business concept if missing
            if not existing_profile.business_concept and extra_extracted.get("business_concept"):
                existing_profile.business_concept = extra_extracted["business_concept"]
                existing_profile.business_category_hint = extra_extracted.get("business_category_hint")

            # Merge capital if found
            if extra_extracted.get("available_capital") is not None:
                existing_profile.available_capital = extra_extracted["available_capital"]

            # Merge location (USER LOCATION ALWAYS WINS)
            ext_loc = extra_extracted.get("proposed_location", {})
            if ext_loc.get("district") or ext_loc.get("name"):
                if ext_loc.get("name"):
                    existing_profile.proposed_location.name = ext_loc["name"]
                if ext_loc.get("district"):
                    existing_profile.proposed_location.district = ext_loc["district"]
                if ext_loc.get("state"):
                    existing_profile.proposed_location.state = ext_loc["state"]
                existing_profile.proposed_location.source = "user"

            # Merge skills
            if extra_extracted.get("entrepreneur_skills"):
                current_skills = set(existing_profile.entrepreneur_skills)
                for sk in extra_extracted["entrepreneur_skills"]:
                    current_skills.add(sk)
                existing_profile.entrepreneur_skills = list(current_skills)
                existing_profile.skills_status = "collected"

    # 2. Process Explicit Structured Answers
    if "business_concept" in answers:
        existing_profile.business_concept = str(answers["business_concept"]).strip()

    if "intent" in answers:
        intent_val = str(answers["intent"]).strip()
        if intent_val in ["start_business", "expand_business", "existing_business"]:
            existing_profile.intent = intent_val
            existing_profile.business_stage = "existing" if intent_val in ["expand_business", "existing_business"] else "planning"
            existing_profile.existing_business.exists = (intent_val in ["expand_business", "existing_business"])

    if "available_capital" in answers:
        cap_val = answers["available_capital"]
        if isinstance(cap_val, (int, float)):
            existing_profile.available_capital = int(cap_val)
        elif isinstance(cap_val, str):
            parsed_money, _ = parse_indian_money(cap_val)
            if parsed_money is not None:
                existing_profile.available_capital = parsed_money
            else:
                try:
                    existing_profile.available_capital = int(cap_val)
                except ValueError:
                    pass

    # Location Answer (USER LOCATION ALWAYS WINS)
    if "proposed_location" in answers or "location" in answers or "district" in answers or "city" in answers or "village" in answers:
        loc_str = str(answers.get("proposed_location") or answers.get("location") or answers.get("district") or answers.get("village") or answers.get("city") or "")
        if loc_str.strip():
            existing_profile.proposed_location.name = loc_str.strip()
            loc_extract = extract_deterministic_entities(loc_str, language_code=active_lang).get("proposed_location", {})
            existing_profile.proposed_location.district = loc_extract.get("district") or loc_str.strip()
            if loc_extract.get("state"):
                existing_profile.proposed_location.state = loc_extract["state"]
            existing_profile.proposed_location.source = "user"

    if "state" in answers and answers["state"]:
        existing_profile.proposed_location.state = str(answers["state"]).strip()

    # GPS Location Fallback (Only applied if user hasn't specified explicit business location or as coordinates)
    if gps_location and isinstance(gps_location, dict):
        lat = gps_location.get("latitude")
        lon = gps_location.get("longitude")
        acc = gps_location.get("accuracy")
        existing_profile.proposed_location.latitude = lat
        existing_profile.proposed_location.longitude = lon
        existing_profile.proposed_location.accuracy = acc

        # If user did not provide an explicit location name, use GPS
        if existing_profile.proposed_location.source != "user" or not existing_profile.proposed_location.name:
            gps_city = gps_location.get("city") or gps_location.get("district") or gps_location.get("name")
            if gps_city:
                existing_profile.proposed_location.name = gps_city
                existing_profile.proposed_location.district = gps_city
            else:
                existing_profile.proposed_location.name = "Device GPS Location"
            existing_profile.proposed_location.source = "gps"

    # Entrepreneur Skills Answer
    if "entrepreneur_skills" in answers or "skills" in answers:
        skills_ans = answers.get("entrepreneur_skills") or answers.get("skills")
        if isinstance(skills_ans, list):
            existing_profile.entrepreneur_skills = skills_ans
            existing_profile.skills_status = "collected" if skills_ans else "no_experience"
        elif isinstance(skills_ans, str):
            if skills_ans.lower() in ["no_experience", "none", "no experience", "ಯಾವುದೇ ಅನುಭವವಿಲ್ಲ", "ಅನುಭವವಿಲ್ಲ", "कोई अनुभव नहीं"]:
                existing_profile.skills_status = "no_experience"
                existing_profile.entrepreneur_skills = []
            else:
                existing_profile.entrepreneur_skills = [s.strip() for s in skills_ans.split(",") if s.strip()]
                existing_profile.skills_status = "collected"

    if "skills_status" in answers:
        existing_profile.skills_status = answers["skills_status"]
        if answers["skills_status"] == "no_experience":
            existing_profile.entrepreneur_skills = []

    # 3. Re-evaluate Missing Fields
    missing_fields = evaluate_stage1_missing_fields(
        business_concept=existing_profile.business_concept,
        intent=existing_profile.intent,
        available_capital=existing_profile.available_capital,
        proposed_location=existing_profile.proposed_location,
        skills_status=existing_profile.skills_status,
        skills_list=existing_profile.entrepreneur_skills
    )

    is_complete = (len(missing_fields) == 0)
    existing_profile.missing_fields = missing_fields
    existing_profile.stage_1_complete = is_complete

    # 4. Generate Next Action Clarification
    next_action = build_next_action(missing_fields, language_code=active_lang)

    response = Stage1IntakeResponse(
        success=True,
        session_id=session_id,
        language=LanguageDetail(
            detected=existing_profile.detected_language,
            code=existing_profile.language_code,
            selected=active_lang
        ),
        profile=existing_profile,
        missing_fields=missing_fields,
        next_action=next_action
    )

    # Save to memory cache
    _IN_MEMORY_SESSIONS[session_id] = {
        "profile": existing_profile.model_dump(),
        "response": response.model_dump(),
        "language_detail": response.language.model_dump()
    }

    # Persist updated session to DB
    if db is not None and session_record is not None:
        try:
            session_record.structured_profile = existing_profile.model_dump()
            session_record.pipeline_status = "completed"
            db.commit()
            db.refresh(session_record)
        except Exception as e:
            logger.warning(f"Failed to update intake session in DB: {e}")
            db.rollback()

    return response


def get_cached_or_db_session(session_id: str, db: Optional[Session] = None) -> Optional[Stage1IntakeResponse]:
    """Retrieves session by session_id from DB or memory cache."""
    if db is not None:
        try:
            rec = db.query(IntakeSession).filter(IntakeSession.id == uuid.UUID(session_id)).first()
            if rec and rec.structured_profile:
                prof = Stage1Profile(**rec.structured_profile)
                missing = evaluate_stage1_missing_fields(
                    business_concept=prof.business_concept,
                    intent=prof.intent,
                    available_capital=prof.available_capital,
                    proposed_location=prof.proposed_location,
                    skills_status=prof.skills_status,
                    skills_list=prof.entrepreneur_skills
                )
                act_lang = prof.selected_language or prof.language_code or "en"
                next_act = build_next_action(missing, language_code=act_lang)
                return Stage1IntakeResponse(
                    success=True,
                    session_id=session_id,
                    language=LanguageDetail(
                        detected=prof.detected_language,
                        code=prof.language_code,
                        selected=act_lang
                    ),
                    profile=prof,
                    missing_fields=missing,
                    next_action=next_act
                )
        except Exception as e:
            logger.warning(f"DB session fetch error: {e}")

    cached = _IN_MEMORY_SESSIONS.get(session_id)
    if cached and "profile" in cached:
        prof = Stage1Profile(**cached["profile"])
        missing = evaluate_stage1_missing_fields(
            business_concept=prof.business_concept,
            intent=prof.intent,
            available_capital=prof.available_capital,
            proposed_location=prof.proposed_location,
            skills_status=prof.skills_status,
            skills_list=prof.entrepreneur_skills
        )
        act_lang = prof.selected_language or prof.language_code or "en"
        next_act = build_next_action(missing, language_code=act_lang)
        return Stage1IntakeResponse(
            success=True,
            session_id=session_id,
            language=LanguageDetail(
                detected=prof.detected_language,
                code=prof.language_code,
                selected=act_lang
            ),
            profile=prof,
            missing_fields=missing,
            next_action=next_act
        )

    return None
