from typing import Dict, Any, List, Optional
import uuid


def build_canonical_business_profile(
    session_id: str,
    stage1_payload: Dict[str, Any],
    ontology_result: Dict[str, Any],
    nic_record: Dict[str, Any],
    confidence_data: Dict[str, Any],
    top_candidates: List[Dict[str, Any]],
    normalized_concept: str
) -> Dict[str, Any]:
    """
    Constructs the canonical structured business profile consumed directly
    by the KALPA Orchestrator Agent and downstream specialized agents.
    """
    profile_data = stage1_payload.get("profile") or stage1_payload
    
    # 1. Entrepreneur Profile
    detected_lang = stage1_payload.get("language", {}).get("detected") if isinstance(stage1_payload.get("language"), dict) else stage1_payload.get("detected_language", "English")
    lang_code = stage1_payload.get("language_code") or (stage1_payload.get("language", {}).get("code") if isinstance(stage1_payload.get("language"), dict) else "en")
    selected_lang = stage1_payload.get("selected_language") or lang_code
    
    intent_type = profile_data.get("intent") or "start_business"
    business_stage = profile_data.get("business_stage") or "planning"
    
    location_data = profile_data.get("proposed_location") or stage1_payload.get("location") or {}
    loc_name = location_data.get("name", "")
    loc_district = location_data.get("district", "")
    loc_state = location_data.get("state", "")
    loc_lat = location_data.get("latitude")
    loc_lon = location_data.get("longitude")
    loc_source = location_data.get("source", "user_provided")
    
    capital_val = profile_data.get("available_capital") or stage1_payload.get("capital_available") or 0
    skills_list = profile_data.get("entrepreneur_skills") or stage1_payload.get("skills") or []
    
    # 2. Business Ontology
    sector = ontology_result.get("sector", "Manufacturing")
    category = ontology_result.get("category", "General Enterprise")
    sub_category = ontology_result.get("sub_category", ontology_result.get("subcategory", ""))
    specific_business = ontology_result.get("specific_business", normalized_concept)
    products = ontology_result.get("products", [])
    services = ontology_result.get("services", [])
    
    # 3. Official NIC Classification
    nic_version = nic_record.get("nic_version", "NIC-2008")
    sec_info = nic_record.get("section", {"code": "C", "title": "Manufacturing"})
    div_info = nic_record.get("division", {"code": "10", "title": "Manufacture of food products"})
    grp_info = nic_record.get("group", {"code": "106", "title": "Manufacture of grain mill products"})
    cls_info = nic_record.get("class", {"code": "1061", "title": "Manufacture of grain mill products"})
    sub_info = nic_record.get("subclass", {"code": nic_record.get("activity", {}).get("code", "10612"), "title": nic_record.get("activity", {}).get("title", "")})
    act_info = nic_record.get("activity", {
        "code": nic_record.get("code", "10612"),
        "official_title": nic_record.get("title", ""),
        "description": nic_record.get("description", "")
    })
    
    # Format activity object consistently
    official_activity = {
        "code": act_info.get("code", nic_record.get("code", "")),
        "official_title": act_info.get("title", act_info.get("official_title", nic_record.get("title", ""))),
        "description": act_info.get("description", nic_record.get("description", ""))
    }
    
    # Format top candidates list
    formatted_candidates = []
    for idx, cand in enumerate(top_candidates, start=1):
        c_act = cand.get("activity", {})
        formatted_candidates.append({
            "rank": idx,
            "code": c_act.get("code", cand.get("code", "")),
            "title": c_act.get("title", cand.get("title", "")),
            "score": cand.get("match_score", cand.get("score", 0.0))
        })
    
    # 4. Orchestrator Context
    orchestrator_context = {
        "profile_ready": True,
        "classification_verified": confidence_data["level"] in ["HIGH", "MEDIUM"],
        "recommended_next_stage": "market_intelligence",
        "business_activity": specific_business,
        "official_nic_code": official_activity["code"],
        "nic_version": nic_version,
        "sector": sector,
        "category": category,
        "location": {
            "name": loc_name,
            "district": loc_district,
            "state": loc_state,
            "latitude": loc_lat,
            "longitude": loc_lon
        },
        "available_capital": capital_val,
        "skills": skills_list,
        "language": lang_code,
        "classification_confidence": confidence_data["score"]
    }
    
    canonical_profile = {
        "success": True,
        "session_id": session_id,
        "business_id": str(uuid.uuid4()),
        "pipeline": {
            "stage_1_complete": True,
            "stage_2_complete": confidence_data["level"] in ["HIGH", "MEDIUM"]
        },
        "entrepreneur_profile": {
            "language": {
                "detected": detected_lang,
                "code": lang_code,
                "selected": selected_lang
            },
            "intent": {
                "type": intent_type,
                "stage": business_stage
            },
            "venture": {
                "business_concept": profile_data.get("business_concept") or stage1_payload.get("original_input", ""),
                "normalized_activity": normalized_concept,
                "product_service": profile_data.get("product_service", "")
            },
            "financial_profile": {
                "available_capital": capital_val,
                "currency": "INR"
            },
            "location": {
                "name": loc_name,
                "district": loc_district,
                "state": loc_state,
                "country": "India",
                "latitude": loc_lat,
                "longitude": loc_lon,
                "source": loc_source
            },
            "skills": skills_list
        },
        "business_ontology": {
            "sector": sector,
            "category": category,
            "subcategory": sub_category,
            "specific_business": specific_business,
            "products": products,
            "services": services
        },
        "official_classification": {
            "classification_status": "verified" if confidence_data["level"] in ["HIGH", "MEDIUM"] else "needs_clarification",
            "nic": {
                "version": nic_version,
                "section": sec_info,
                "division": div_info,
                "group": grp_info,
                "class": cls_info,
                "subclass": sub_info,
                "activity": official_activity
            },
            "confidence": confidence_data,
            "top_candidates": formatted_candidates
        },
        "orchestrator_context": orchestrator_context
    }
    
    return canonical_profile
