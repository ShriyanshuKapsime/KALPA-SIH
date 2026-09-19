import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.session import get_db_context
from app.core.logging import logger
from app.database.models.intake import IntakeSession
from app.services.classification.ontology_service import (
    normalize_business_concept,
    search_ontology_candidates,
    is_ambiguous_concept,
    load_ontology_data
)
from app.services.classification.nic_repository import (
    search_official_nic_candidates,
    get_official_nic_record,
    load_official_nic_dataset
)
from app.services.classification.hierarchy_validator import validate_nic_hierarchy
from app.services.classification.confidence_calculator import calculate_deterministic_confidence
from app.services.classification.canonical_profile_builder import build_canonical_business_profile
from app.services.classification.llm_classifier import classify_with_llm

# Multilingual Clarification Prompts & Options
CLARIFICATION_TEMPLATES = {
    "clothing": {
        "en": {
            "question": "What type of clothing or textile business do you want to start?",
            "options": [
                {"label": "Saree & Traditional Apparel Retail", "value": "Saree Retail"},
                {"label": "Ready-made Garments Store (Men/Women/Kids)", "value": "Readymade Garments Store"},
                {"label": "Tailoring & Dressmaking Boutique", "value": "Tailoring & Garment Shop"},
                {"label": "Handloom / Powerloom Weaving", "value": "Weaving of Textiles"}
            ]
        },
        "hi": {
            "question": "आप किस प्रकार का कपड़ों का व्यवसाय शुरू करना चाहते हैं?",
            "options": [
                {"label": "साड़ी एवं पारंपरिक परिधान की दुकान", "value": "Saree Retail"},
                {"label": "रेडीमेड कपड़े की दुकान", "value": "Readymade Garments Store"},
                {"label": "सिलाई एवं टेलरिंग केंद्र", "value": "Tailoring & Garment Shop"},
                {"label": "हथकरघा / बुनाई का काम", "value": "Weaving of Textiles"}
            ]
        },
        "kn": {
            "question": "ನೀವು ಯಾವ ರೀತಿಯ ಬಟ್ಟೆ ಅಥವಾ ವಸ್ತ್ರೋದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?",
            "options": [
                {"label": "ಸೀರೆ ಮತ್ತು ಸಾಂಪ್ರದಾಯಿಕ ಉಡುಪುಗಳ ಅಂಗಡಿ", "value": "Saree Retail"},
                {"label": "ರೆಡಿಮೇಡ್ ಉಡುಪುಗಳ ಮಳಿಗೆ", "value": "Readymade Garments Store"},
                {"label": "ಟೈಲರಿಂಗ್ ಮತ್ತು ಹೊಲಿಗೆ ಕೇಂದ್ರ", "value": "Tailoring & Garment Shop"},
                {"label": "ಮಗ್ಗ ಮತ್ತು ನೇಯ್ಗೆ ಉದ್ಯಮ", "value": "Weaving of Textiles"}
            ]
        }
    },
    "food": {
        "en": {
            "question": "What specific type of food or agro enterprise do you want to start?",
            "options": [
                {"label": "Rice Mill / Paddy Processing Unit", "value": "Rice Mill"},
                {"label": "Flour Mill (Atta Chakki)", "value": "Flour Mill (Atta Chakki)"},
                {"label": "Vegetarian Restaurant / Eatery", "value": "Vegetarian Restaurant / Dhaba"},
                {"label": "Bakery & Confectionery", "value": "Bakery & Sweets Production"},
                {"label": "Oil Mill / Cold Pressed Oil Extraction", "value": "Edible Oil Mill (Ganuga)"}
            ]
        },
        "hi": {
            "question": "आप किस प्रकार का खाद्य या कृषि व्यवसाय शुरू करना चाहते हैं?",
            "options": [
                {"label": "राइस मिल (चावल प्रसंस्करण)", "value": "Rice Mill"},
                {"label": "आटा चक्की / पिसाई केंद्र", "value": "Flour Mill (Atta Chakki)"},
                {"label": "शाकाहारी होटल / भोजनालय", "value": "Vegetarian Restaurant / Dhaba"},
                {"label": "बेकरी एवं मिष्ठान उद्योग", "value": "Bakery & Sweets Production"},
                {"label": "तेल मिल / कोल्हू", "value": "Edible Oil Mill (Ganuga)"}
            ]
        },
        "kn": {
            "question": "ನೀವು ಯಾವ ನಿರ್ದಿಷ್ಟ ಆಹಾರ ಅಥವಾ ಕೃಷಿ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?",
            "options": [
                {"label": "ಅಕ್ಕಿ ಗಿರಣಿ (ರೈಸ್ ಮಿಲ್)", "value": "Rice Mill"},
                {"label": "ಹಿಟ್ಟಿನ ಗಿರಣಿ (ಆಟಾ ಚಕ್ಕಿ)", "value": "Flour Mill (Atta Chakki)"},
                {"label": "ಶಾಕಾಹಾರಿ ಹೋಟೆಲ್ / ಖಾನಾವಳಿ", "value": "Vegetarian Restaurant / Dhaba"},
                {"label": "ಬೇಕರಿ ಮತ್ತು ಸ್ವೀಟ್ಸ್ ತಯಾರಿಕೆ", "value": "Bakery & Sweets Production"},
                {"label": "ಎಣ್ಣೆ ಗಾಣ / ಗಿರಣಿ", "value": "Edible Oil Mill (Ganuga)"}
            ]
        }
    },
    "generic": {
        "en": {
            "question": "Could you specify the primary product or service of your venture?",
            "options": [
                {"label": "Retail Store / Shop", "value": "Kirana & Grocery Store"},
                {"label": "Agro / Food Manufacturing Unit", "value": "Rice Mill"},
                {"label": "Farming & Animal Husbandry", "value": "Dairy Farm"},
                {"label": "Technical Repair & Services", "value": "Two Wheeler Repair Shop"}
            ]
        },
        "hi": {
            "question": "क्या आप अपने व्यवसाय के मुख्य उत्पाद या सेवा का विवरण दे सकते हैं?",
            "options": [
                {"label": "दुकान / किराना स्टोर", "value": "Kirana & Grocery Store"},
                {"label": "कृषि / खाद्य प्रसंस्करण इकाई", "value": "Rice Mill"},
                {"label": "पशुपालन एवं डेयरी फार्म", "value": "Dairy Farm"},
                {"label": "तकनीकी रिपेयर एवं सर्विस", "value": "Two Wheeler Repair Shop"}
            ]
        },
        "kn": {
            "question": "ನಿಮ್ಮ ಉದ್ಯಮದ ಪ್ರಮುಖ ಉತ್ಪನ್ನ ಅಥವಾ ಸೇವೆಯನ್ನು ನಿರ್ದಿಷ್ಟಪಡಿಸಬಹುದೇ?",
            "options": [
                {"label": "ಕಿರಾಣಿ ಅಂಗಡಿ / ಮಳಿಗೆ", "value": "Kirana & Grocery Store"},
                {"label": "ಕೃಷಿ / ಆಹಾರ ಸಂಸ್ಕರಣಾ ಘಟಕ", "value": "Rice Mill"},
                {"label": "ಹೈನುಗಾರಿಕೆ ಮತ್ತು ಡೈರಿ ಫಾರ್ಮ್", "value": "Dairy Farm"},
                {"label": "ತಾಂತ್ರಿಕ ರಿಪೇರಿ ಮತ್ತು ಸೇವಾ ಘಟಕ", "value": "Two Wheeler Repair Shop"}
            ]
        }
    }
}


def _get_clarification_card(concept: str, language_code: str) -> Dict[str, Any]:
    lang = language_code if language_code in ["kn", "hi", "en"] else "en"
    clean = (concept or "").lower()
    
    if any(k in clean for k in ["cloth", "garment", "apparel", "textile", "ಬಟ್ಟೆ", "कपड़ा", "साड़ी"]):
        template = CLARIFICATION_TEMPLATES["clothing"].get(lang, CLARIFICATION_TEMPLATES["clothing"]["en"])
    elif any(k in clean for k in ["food", "hotel", "restaurant", "eatery", "ಊಟ", "ತಿಂಡಿ", "खाना", "भोजन"]):
        template = CLARIFICATION_TEMPLATES["food"].get(lang, CLARIFICATION_TEMPLATES["food"]["en"])
    else:
        template = CLARIFICATION_TEMPLATES["generic"].get(lang, CLARIFICATION_TEMPLATES["generic"]["en"])
        
    return {
        "field": "specific_business",
        "question": template["question"],
        "language": lang,
        "options": template["options"],
        "input_modes": ["options", "text", "voice"]
    }


async def run_business_classification(
    raw_payload: Dict[str, Any],
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Stage 2.5 Dual-Layer Classification Engine:
    Structured Intake -> Ontology Matcher -> NIC Candidate Retrieval ->
    Hierarchy Validation -> Deterministic 5-Pillar Confidence -> Canonical Profile Store
    """
    session_id = raw_payload.get("session_id") or raw_payload.get("intake_id") or str(uuid.uuid4())
    logger.info(f"[CLASSIFICATION START] session_id={session_id}")
    logger.info("[CLASSIFICATION INPUT] %s", raw_payload)

    # Extract Stage 1 fields
    profile_data = raw_payload.get("profile") or raw_payload
    original_input = (
        raw_payload.get("original_input") or
        profile_data.get("original_input") or
        raw_payload.get("original_text") or
        raw_payload.get("business_description") or
        raw_payload.get("text") or ""
    )
    
    business_concept = (
        profile_data.get("business_concept") or
        raw_payload.get("business_concept") or
        raw_payload.get("business_idea") or
        original_input
    )
    
    language_code = (
        profile_data.get("language_code") or
        raw_payload.get("language_code") or
        "en"
    )
    
    product_service = (
        profile_data.get("product_service") or
        raw_payload.get("product_service") or ""
    )

    # STEP 1: Multilingual Concept Normalization
    normalized_concept = normalize_business_concept(business_concept, language_code)
    logger.info(f"[NORMALIZED CONCEPT] input='{business_concept}' -> normalized='{normalized_concept}'")

    # STEP 2: Ambiguity Check
    is_ambiguous = is_ambiguous_concept(normalized_concept) or is_ambiguous_concept(original_input) or is_ambiguous_concept(business_concept)

    # STEP 3: Layer A - KALPA Business Ontology Match
    ontology_candidates = search_ontology_candidates(
        query_text=original_input,
        normalized_concept=normalized_concept,
        product_service=product_service,
        limit=5
    )
    logger.info(f"[ONTOLOGY MATCH] Found {len(ontology_candidates)} candidates: {[c['specific_business'] for c in ontology_candidates]}")

    # STEP 4: Layer B - Official NIC Candidate Search
    ontology_nic_hints = []
    for cand in ontology_candidates[:2]:
        ontology_nic_hints.extend(cand.get("nic_candidates", []))

    nic_candidates = search_official_nic_candidates(
        normalized_concept=normalized_concept,
        keywords=ontology_candidates[0].get("products", []) if ontology_candidates else [],
        ontology_nic_hints=ontology_nic_hints,
        limit=5
    )
    logger.info(f"[NIC CANDIDATES] Found {len(nic_candidates)} candidates: {[n['activity']['code'] for n in nic_candidates]}")

    # STEP 5: Controlled Groq LLM Ranking (Candidate Selection Only)
    llm_result = await classify_with_llm(
        business_text=original_input,
        normalized_concept=normalized_concept,
        language_code=language_code,
        ontology_candidates=ontology_candidates,
        nic_candidates=[{"code": n["activity"]["code"], "title": n["activity"]["title"]} for n in nic_candidates]
    )

    # STEP 6: Select Best Candidates
    selected_ontology = None
    selected_nic = None

    if ontology_candidates:
        best_ont = ontology_candidates[0]
        llm_selected_id = llm_result.get("selected_ontology_id") if llm_result else None
        
        if llm_selected_id:
            for cand in ontology_candidates:
                if cand.get("id") == llm_selected_id:
                    selected_ontology = cand
                    break
        if not selected_ontology:
            selected_ontology = best_ont

        best_nic_code = None
        if llm_result and llm_result.get("selected_nic_code"):
            best_nic_code = llm_result.get("selected_nic_code")
        elif selected_ontology.get("nic_candidates"):
            best_nic_code = selected_ontology.get("nic_candidates")[0]
        elif nic_candidates:
            best_nic_code = nic_candidates[0]["activity"]["code"]

        if best_nic_code:
            selected_nic = get_official_nic_record(best_nic_code)
            if not selected_nic and nic_candidates:
                selected_nic = nic_candidates[0]

        if selected_nic:
            matching_cand = next((c for c in nic_candidates if c["activity"]["code"] == selected_nic["activity"]["code"]), None)
            if matching_cand and "match_score" in matching_cand:
                selected_nic["match_score"] = matching_cand["match_score"]
            elif "match_score" not in selected_nic:
                if selected_ontology and selected_nic["activity"]["code"] in selected_ontology.get("nic_candidates", []):
                    selected_nic["match_score"] = 0.95
                else:
                    selected_nic["match_score"] = 0.85

    # Handle Unknown or Zero-Match Concepts
    if not selected_ontology or not selected_nic:
        logger.warning("[CLASSIFICATION] Unknown business activity or no candidate matched. Triggering clarification.")
        clarification_card = _get_clarification_card(normalized_concept, language_code)
        
        return {
            "success": False,
            "session_id": session_id,
            "classification_status": "needs_clarification",
            "input_summary": {
                "business_concept": business_concept,
                "original_language": language_code,
                "normalized_business_concept": normalized_concept
            },
            "layer_a_nic": None,
            "layer_b_ontology": None,
            "official_classification": {
                "classification_status": "needs_clarification",
                "nic": None,
                "confidence": {
                    "score": 0.0,
                    "percentage": 0,
                    "level": "INSUFFICIENT_CONFIDENCE",
                    "breakdown": {
                        "ontology_match": 0.0,
                        "nic_activity_match": 0.0,
                        "hierarchy_consistency": 0.0,
                        "profile_context_consistency": 0.0,
                        "candidate_separation": 0.0
                    }
                },
                "top_candidates": []
            },
            "classification_confidence": 0.0,
            "clarification_needed": True,
            "clarification": clarification_card,
            "candidate_summary": []
        }

    # STEP 7: Hierarchy Validation
    is_hierarchy_valid, hierarchy_score, hierarchy_msg = validate_nic_hierarchy(selected_nic)
    logger.info(f"[HIERARCHY VALIDATION] Valid={is_hierarchy_valid}, Score={hierarchy_score}, Reason='{hierarchy_msg}'")

    # STEP 8: Deterministic 5-Pillar Confidence Calculation
    profile_context_dict = {
        "skills": profile_data.get("entrepreneur_skills") or raw_payload.get("skills") or [],
        "products": selected_ontology.get("products", []),
        "intent": profile_data.get("intent", "start_business")
    }

    confidence_data = calculate_deterministic_confidence(
        ontology_candidate=selected_ontology,
        nic_candidate=selected_nic,
        competing_nic_candidates=nic_candidates,
        hierarchy_valid=is_hierarchy_valid,
        hierarchy_score=hierarchy_score,
        profile_context=profile_context_dict
    )
    logger.info(f"[CONFIDENCE BREAKDOWN] Score={confidence_data['score']} ({confidence_data['level']}), Breakdown={confidence_data['breakdown']}")

    # If Ambiguous or Confidence is Insufficient/Low -> Clarify
    if is_ambiguous or confidence_data["level"] in ["INSUFFICIENT_CONFIDENCE", "LOW"]:
        logger.info(f"[CLARIFICATION REQUIRED] is_ambiguous={is_ambiguous}, level={confidence_data['level']}")
        clarification_card = _get_clarification_card(normalized_concept, language_code)
        
        return {
            "success": True,
            "session_id": session_id,
            "classification_status": "needs_clarification",
            "input_summary": {
                "business_concept": business_concept,
                "original_language": language_code,
                "normalized_business_concept": normalized_concept
            },
            "layer_a_nic": None,
            "layer_b_ontology": None,
            "official_classification": {
                "classification_status": "needs_clarification",
                "nic": None,
                "confidence": confidence_data,
                "top_candidates": [
                    {
                        "rank": idx + 1,
                        "code": cand["activity"]["code"],
                        "title": cand["activity"]["title"],
                        "score": cand.get("match_score", 0.0)
                    }
                    for idx, cand in enumerate(nic_candidates[:3])
                ]
            },
            "classification_confidence": confidence_data["score"],
            "clarification_needed": True,
            "clarification": clarification_card,
            "candidate_summary": [
                {"id": c.get("id"), "name": c.get("specific_business"), "score": c.get("score")}
                for c in ontology_candidates[:4]
            ]
        }

    # STEP 9: Build Canonical Structured Business Profile
    canonical_profile = build_canonical_business_profile(
        session_id=session_id,
        stage1_payload=raw_payload,
        ontology_result=selected_ontology,
        nic_record=selected_nic,
        confidence_data=confidence_data,
        top_candidates=nic_candidates[:4],
        normalized_concept=normalized_concept
    )

    # Legacy Backward Compatibility mapping for Layer A & Layer B
    layer_a_nic = {
        "nic_code": selected_nic["activity"]["code"],
        "nic_description": selected_nic["activity"]["title"],
        "division": selected_nic["division"]["code"],
        "division_name": selected_nic["division"]["title"],
        "group": selected_nic["group"]["code"],
        "group_name": selected_nic["group"]["title"],
        "class": selected_nic["class"]["code"],
        "class_name": selected_nic["class"]["title"],
        "subclass": selected_nic["subclass"]["code"],
        "subclass_title": selected_nic["subclass"]["title"],
        "section": selected_nic["section"]["code"],
        "section_name": selected_nic["section"]["title"],
        "confidence": confidence_data["score"],
        "status": "confirmed"
    }

    layer_b_ontology = {
        "sector": selected_ontology.get("sector"),
        "category": selected_ontology.get("category"),
        "sub_category": selected_ontology.get("sub_category", selected_ontology.get("subcategory")),
        "specific_business": selected_ontology.get("specific_business"),
        "products": selected_ontology.get("products", []),
        "services": selected_ontology.get("services", []),
        "confidence": confidence_data["score"]
    }

    # STEP 10: Persist canonical profile to database
    try:
        _persist_business_profile(db, session_id, canonical_profile)
    except Exception as err:
        logger.error(f"[DATABASE PERSIST ERROR] Failed saving structured canonical profile: {err}")

    final_result = {
        "success": True,
        "session_id": session_id,
        "classification_status": "complete",
        "input_summary": {
            "business_concept": business_concept,
            "original_language": language_code,
            "normalized_business_concept": normalized_concept
        },
        "layer_a_nic": layer_a_nic,
        "layer_b_ontology": layer_b_ontology,
        "official_classification": canonical_profile["official_classification"],
        "orchestrator_context": canonical_profile["orchestrator_context"],
        "classification_confidence": confidence_data["score"],
        "confidence_level": confidence_data["level"],
        "confidence_breakdown": confidence_data["breakdown"],
        "clarification_needed": False,
        "clarification": None,
        "candidate_summary": [
            {"id": c.get("id"), "name": c.get("specific_business"), "score": c.get("score")}
            for c in ontology_candidates[:3]
        ],
        "structured_business_profile": canonical_profile,
        "canonical_profile": canonical_profile
    }

    logger.info("[FINAL CLASSIFICATION] %s", final_result)
    return final_result


def _persist_business_profile(db: Optional[Session], session_id: str, profile_dict: Dict[str, Any]):
    """
    Saves or updates the IntakeSession structured profile with the canonical Stage 2 business profile.
    """
    if not session_id:
        return
    try:
        intake_uuid = uuid.UUID(str(session_id))
    except Exception:
        return

    def _do_update(sess: Session):
        intake_sess = sess.query(IntakeSession).filter(IntakeSession.id == intake_uuid).first()
        if intake_sess:
            current_profile = dict(intake_sess.structured_profile or {})
            current_profile["stage_2_classification"] = profile_dict
            current_profile["canonical_business_profile"] = profile_dict
            intake_sess.structured_profile = current_profile
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(intake_sess, "structured_profile")
            sess.commit()
            logger.info(f"[DATABASE] Updated IntakeSession {session_id} with Canonical Stage 2 Profile.")

    try:
        if db:
            _do_update(db)
        else:
            with get_db_context() as sess:
                if sess:
                    _do_update(sess)
    except Exception as e:
        logger.error(f"[DATABASE ERROR] _persist_business_profile error: {e}")
        if db:
            db.rollback()
