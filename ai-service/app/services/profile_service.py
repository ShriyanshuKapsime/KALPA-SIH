import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.database.models.intake import IntakeSession
from app.database.models.profile import StructuredBusinessProfile
from app.services.classification.classification_service import run_business_classification
from app.services.classification.ontology_service import load_ontology_data
from app.services.classification.nic_repository import get_official_nic_record
from app.schemas.profile import CanonicalBusinessProfile


def _normalize_location_fields(raw_loc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes location components: separates compound names (e.g. 'Chatra, Jharkhand'),
    cleans administrative levels, and standardizes source values.
    """
    name = (raw_loc.get("name") or raw_loc.get("city") or raw_loc.get("village") or "").strip()
    district = (raw_loc.get("district") or "").strip()
    state = (raw_loc.get("state") or "").strip()
    village = raw_loc.get("village")
    block = raw_loc.get("block") or raw_loc.get("taluk") or raw_loc.get("taluka")

    # Handle compound strings like 'Chatra, Jharkhand' or 'Mandya, Karnataka'
    if "," in district and not state:
        parts = [p.strip() for p in district.split(",") if p.strip()]
        if len(parts) >= 2:
            district = parts[0]
            state = parts[1]
    elif "," in name and not state:
        parts = [p.strip() for p in name.split(",") if p.strip()]
        if len(parts) >= 2:
            if not district:
                district = parts[0]
            state = parts[1]
            name = parts[0]

    # Clean redundant district naming
    if district and state and district.lower() == state.lower():
        district = name if name and name.lower() != state.lower() else district

    # Normalize source
    raw_source = str(raw_loc.get("source", "user")).lower().strip()
    if "gps" in raw_source:
        source = "gps"
    elif "geocode" in raw_source:
        source = "geocoded"
    elif "mixed" in raw_source:
        source = "mixed"
    else:
        source = "user"

    # Coordinates
    lat = raw_loc.get("latitude")
    lon = raw_loc.get("longitude")
    accuracy = raw_loc.get("accuracy")

    try:
        lat = float(lat) if lat is not None else None
    except (ValueError, TypeError):
        lat = None

    try:
        lon = float(lon) if lon is not None else None
    except (ValueError, TypeError):
        lon = None

    try:
        accuracy = float(accuracy) if accuracy is not None else None
    except (ValueError, TypeError):
        accuracy = None

    return {
        "name": name,
        "village": village,
        "block": block,
        "district": district,
        "state": state,
        "country": "India",
        "coordinates": {
          "latitude": lat,
          "longitude": lon,
          "accuracy": accuracy
        },
        "source": source
    }


def _retrieve_ontology_requirements(specific_business: str, category: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Retrieves downstream analysis requirements directly from KALPA Business Ontology.
    Never uses LLM hallucination. Returns fallback empty lists with explicit warnings if unmapped.
    """
    ontology_nodes = load_ontology_data()
    warnings = []

    clean_bus = (specific_business or "").lower().strip()
    matched_node = None

    for node in ontology_nodes:
        node_bus = node.get("specific_business", "").lower()
        if node_bus == clean_bus or clean_bus in node_bus or node.get("id", "").lower() in clean_bus:
            matched_node = node
            break

    if not matched_node:
        for node in ontology_nodes:
            aliases = [a.lower() for a in node.get("aliases", [])]
            if any(clean_bus in a for a in aliases):
                matched_node = node
                break

    if matched_node and "analysis_requirements" in matched_node:
        reqs = matched_node["analysis_requirements"]
        return {
            "direct_competitors": reqs.get("direct_competitors", []),
            "adjacent_competitors": reqs.get("adjacent_competitors", []),
            "substitute_businesses": reqs.get("substitute_businesses", []),
            "demand_features": reqs.get("demand_features", []),
            "infrastructure_requirements": reqs.get("infrastructure_requirements", []),
            "risk_factors": reqs.get("risk_factors", []),
            "required_datasets": reqs.get("required_datasets", [])
        }, warnings

    warnings.append("Ontology analysis requirements unavailable")
    return {
        "direct_competitors": [],
        "adjacent_competitors": [],
        "substitute_businesses": [],
        "demand_features": [],
        "infrastructure_requirements": [],
        "risk_factors": [],
        "required_datasets": []
    }, warnings


def _validate_canonical_profile(profile_dict: Dict[str, Any]) -> Tuple[bool, List[str], List[str], str]:
    """
    Validates structural completeness and semantic consistency of the canonical profile.
    Checks for missing fields, coordinate boundaries, numeric capital, and classification contradictions.
    """
    missing_fields = []
    warnings = []

    bus = profile_dict.get("business_profile", {})
    loc = profile_dict.get("location_profile", {})
    fin = profile_dict.get("financial_profile", {})
    ent = profile_dict.get("entrepreneur_profile", {})
    nic = bus.get("nic", {})

    # 1. Mandatory identity checks
    if not profile_dict.get("analysis_id"):
        missing_fields.append("analysis_id")
    if not profile_dict.get("session_id"):
        missing_fields.append("session_id")
    if not bus.get("original_concept") and not bus.get("normalized_concept"):
        missing_fields.append("business_profile.concept")
    if not bus.get("specific_business"):
        missing_fields.append("business_profile.specific_business")
    if not nic.get("code"):
        missing_fields.append("business_profile.nic.code")

    # 2. Capital check
    cap = fin.get("available_capital")
    if cap is not None:
        if not isinstance(cap, (int, float)) or cap < 0:
            warnings.append("Available capital must be a non-negative number")
    else:
        missing_fields.append("financial_profile.available_capital")

    # 3. Location check
    if not loc.get("district") and not loc.get("name"):
        missing_fields.append("location_profile.district")

    coords = loc.get("coordinates", {})
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    if lat is not None:
        if not (-90.0 <= lat <= 90.0):
            warnings.append(f"Invalid latitude value: {lat}")
    if lon is not None:
        if not (-180.0 <= lon <= 180.0):
            warnings.append(f"Invalid longitude value: {lon}")

    # 4. Classification confidence check
    conf = nic.get("confidence", 0.0)
    if not (0.0 <= conf <= 1.0):
        warnings.append(f"Classification confidence {conf} is out of [0, 1] range")

    # 5. Semantic Contradiction Check
    sector = (bus.get("sector") or "").lower()
    nic_code = str(nic.get("code", ""))
    div_code = str(nic.get("division", {}).get("code", ""))
    
    # Check if Retail sector maps to manufacturing division (e.g. div 10, 11, 12, 13)
    if "retail" in sector and div_code and div_code in ["10", "11", "12", "13", "14", "25", "31"]:
        warnings.append(f"Potential category contradiction: sector is '{sector}' but NIC division is '{div_code}'")

    # Check if Agriculture sector maps to retail division (div 47)
    if "agriculture" in sector and div_code == "47":
        warnings.append(f"Potential category contradiction: sector is '{sector}' but NIC division is '{div_code}'")

    profile_complete = len(missing_fields) == 0
    validation_status = "PASSED" if profile_complete and not warnings else "INCOMPLETE" if missing_fields else "PASSED_WITH_WARNINGS"

    return profile_complete, missing_fields, warnings, validation_status


async def build_canonical_profile_for_session(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Builds, validates, and persists the Stage 3 Canonical Structured Business Profile
    from validated Stage 1 (Intake) and Stage 2 (Classification) outputs.
    """
    logger.info(f"[STAGE 3 PROFILE BUILD START] session_id={session_id}")

    # 1. Load Stage 1 Session
    intake_uuid = None
    try:
        intake_uuid = uuid.UUID(session_id)
    except Exception:
        pass

    intake_sess = None
    if intake_uuid:
        intake_sess = db.query(IntakeSession).filter(IntakeSession.id == intake_uuid).first()

    if not intake_sess:
        logger.error(f"[STAGE 3 PROFILE ERROR] Session not found in database: session_id={session_id}")
        raise ValueError(f"IntakeSession {session_id} not found")

    structured_intake = intake_sess.structured_profile or {}
    logger.info(
        f"[STAGE 3 LOADED INTAKE] session_id={session_id}, "
        f"language={intake_sess.language_code}, "
        f"input_type={intake_sess.input_type}"
    )

    # 2. Load or Compute Stage 2 Classification
    stage2_data = structured_intake.get("canonical_business_profile") or structured_intake.get("stage_2_classification")

    if not stage2_data or not stage2_data.get("official_classification", {}).get("nic"):
        logger.info(f"[STAGE 3 PROFILE] Running Stage 2 Classification for session_id={session_id}")
        classification_result = await run_business_classification(structured_intake, db=db)
        stage2_data = (classification_result.get("canonical_profile") or classification_result) if classification_result else {}

    if not isinstance(stage2_data, dict):
        stage2_data = {}

    logger.info(f"[STAGE 3 LOADED CLASSIFICATION] session_id={session_id}")

    # 3. Extract and Merge Elements
    now_iso = datetime.now(timezone.utc).isoformat()

    # Provenance
    detected_lang = structured_intake.get("language_name") or intake_sess.language_name or "English"
    lang_code = structured_intake.get("language_code") or intake_sess.language_code or "en"
    input_mode = intake_sess.input_type or "text"

    # Business Profile
    original_concept = (
        structured_intake.get("business_concept") or
        intake_sess.original_text or
        structured_intake.get("original_input", "")
    )
    
    ontology_sec = stage2_data.get("business_ontology") or {}
    specific_business = ontology_sec.get("specific_business") or structured_intake.get("business_concept", "")
    sector = ontology_sec.get("sector", "Manufacturing")
    category = ontology_sec.get("category", "General Enterprise")
    sub_category = ontology_sec.get("subcategory") or ontology_sec.get("sub_category", "")
    products = ontology_sec.get("products", [])
    services = ontology_sec.get("services", [])

    # NIC details from Stage 2
    official_class = stage2_data.get("official_classification") or {}
    if not isinstance(official_class, dict):
        official_class = {}
    nic_node = official_class.get("nic") or {}
    if not isinstance(nic_node, dict):
        nic_node = {}
    nic_act = nic_node.get("activity") or {}
    if not isinstance(nic_act, dict):
        nic_act = {}
    nic_div = nic_node.get("division") or {}
    if not isinstance(nic_div, dict):
        nic_div = {}
    nic_grp = nic_node.get("group") or {}
    if not isinstance(nic_grp, dict):
        nic_grp = {}
    nic_cls = nic_node.get("class") or {}
    if not isinstance(nic_cls, dict):
        nic_cls = {}
    conf_node = official_class.get("confidence") or {}
    if not isinstance(conf_node, dict):
        conf_node = {}

    nic_code = nic_act.get("code") or nic_node.get("code", "")
    nic_title = nic_act.get("official_title") or nic_act.get("title") or nic_node.get("title", "")
    confidence_score = conf_node.get("score") if isinstance(conf_node.get("score"), (int, float)) else stage2_data.get("classification_confidence", 0.90)

    # Entrepreneur Profile
    skills = structured_intake.get("skills") or structured_intake.get("entrepreneur_skills") or []
    experience = structured_intake.get("experience") or []
    resources = structured_intake.get("resources") or []
    business_stage = structured_intake.get("intent") or structured_intake.get("business_stage") or "planning"

    # Location Profile & Normalization
    raw_loc = structured_intake.get("location") or structured_intake.get("proposed_location") or {}
    normalized_loc = _normalize_location_fields(raw_loc)
    logger.info(
        f"[STAGE 3 NORMALIZATION] district='{normalized_loc['district']}', "
        f"state='{normalized_loc['state']}', "
        f"source='{normalized_loc['source']}'"
    )

    # Financial Profile
    raw_cap = structured_intake.get("capital_available")
    if raw_cap is None:
        raw_cap = structured_intake.get("available_capital")
    
    try:
        available_cap = float(raw_cap) if raw_cap is not None else None
    except (ValueError, TypeError):
        available_cap = None

    # 4. Downstream Analysis Requirements from Ontology
    analysis_reqs, ont_warnings = _retrieve_ontology_requirements(specific_business, category)

    # Check for existing profile record
    existing_record = db.query(StructuredBusinessProfile).filter(
        StructuredBusinessProfile.session_id == intake_uuid
    ).first()

    analysis_id = str(existing_record.id) if existing_record else str(uuid.uuid4())
    profile_version = (existing_record.profile_version + 1) if existing_record else 1
    created_at = existing_record.created_at.isoformat() if (existing_record and existing_record.created_at) else now_iso

    # Assemble profile dict
    profile_payload = {
        "schema_version": "1.0",
        "profile_version": profile_version,
        "analysis_id": analysis_id,
        "session_id": str(session_id),
        "user_id": str(intake_sess.user_id) if intake_sess.user_id else None,
        "workflow": {
            "state": "BUSINESS_PROFILE_READY",
            "stage_completed": 3,
            "created_at": created_at,
            "updated_at": now_iso
        },
        "business_profile": {
            "original_concept": original_concept,
            "normalized_concept": specific_business.lower(),
            "sector": sector,
            "category": category,
            "sub_category": sub_category,
            "specific_business": specific_business,
            "nic": {
                "code": nic_code,
                "description": nic_title,
                "division": {
                    "code": str(nic_div.get("code", "")),
                    "name": str(nic_div.get("title", ""))
                },
                "group": {
                    "code": str(nic_grp.get("code", "")),
                    "name": str(nic_grp.get("title", ""))
                },
                "class": {
                    "code": str(nic_cls.get("code", "")),
                    "name": str(nic_cls.get("title", ""))
                },
                "classification_status": "verified" if confidence_score >= 0.75 else "needs_clarification",
                "confidence": round(float(confidence_score), 2)
            },
            "products": products,
            "services": services
        },
        "entrepreneur_profile": {
            "skills": skills,
            "experience": experience,
            "resources": resources,
            "business_stage": business_stage
        },
        "location_profile": normalized_loc,
        "financial_profile": {
            "available_capital": available_cap,
            "currency": "INR"
        },
        "analysis_requirements": analysis_reqs,
        "data_quality": {
            "profile_complete": False,
            "missing_fields": [],
            "warnings": ont_warnings,
            "validation_status": "PENDING"
        },
        "provenance": {
            "stage_1_session_id": str(session_id),
            "classification_id": stage2_data.get("business_id"),
            "language": lang_code,
            "input_mode": input_mode
        }
    }

    # 5. Validate Canonical Profile
    is_complete, missing_fields, val_warnings, val_status = _validate_canonical_profile(profile_payload)
    all_warnings = ont_warnings + val_warnings
    
    workflow_state = "BUSINESS_PROFILE_READY" if is_complete else "BUSINESS_PROFILE_INCOMPLETE"

    profile_payload["workflow"]["state"] = workflow_state
    profile_payload["data_quality"] = {
        "profile_complete": is_complete,
        "missing_fields": missing_fields,
        "warnings": all_warnings,
        "validation_status": val_status
    }

    logger.info(
        f"[STAGE 3 VALIDATION] status='{val_status}', "
        f"is_complete={is_complete}, "
        f"missing={missing_fields}, "
        f"warnings={all_warnings}"
    )

    # 6. Database Persistence
    try:
        if existing_record:
            existing_record.profile_version = profile_version
            existing_record.workflow_state = workflow_state
            existing_record.specific_business = specific_business
            existing_record.nic_code = nic_code
            existing_record.district = normalized_loc.get("district")
            existing_record.state = normalized_loc.get("state")
            existing_record.profile_json = profile_payload
            db.commit()
            db.refresh(existing_record)
        else:
            new_profile = StructuredBusinessProfile(
                id=uuid.UUID(analysis_id),
                session_id=intake_uuid,
                user_id=intake_sess.user_id,
                schema_version="1.0",
                profile_version=profile_version,
                workflow_state=workflow_state,
                specific_business=specific_business,
                nic_code=nic_code,
                district=normalized_loc.get("district"),
                state=normalized_loc.get("state"),
                profile_json=profile_payload
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)

        # Update IntakeSession structured profile
        current_sess_prof = intake_sess.structured_profile or {}
        current_sess_prof["stage_3_canonical_profile"] = profile_payload
        current_sess_prof["analysis_id"] = analysis_id
        intake_sess.structured_profile = current_sess_prof
        db.commit()

        logger.info(f"[STAGE 3 DATABASE SAVE] Saved StructuredBusinessProfile analysis_id={analysis_id}")
    except Exception as e:
        logger.error(f"[STAGE 3 DATABASE SAVE ERROR] Failed to save profile: {e}")
        db.rollback()
        raise

    logger.info(f"[STAGE 3 PROFILE READY] workflow_state='{workflow_state}', analysis_id={analysis_id}")
    return profile_payload


def get_profile_by_analysis_id(analysis_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Retrieves canonical business profile by analysis_id."""
    try:
        rec_uuid = uuid.UUID(analysis_id)
        rec = db.query(StructuredBusinessProfile).filter(StructuredBusinessProfile.id == rec_uuid).first()
        if rec:
            return rec.profile_json
    except Exception as e:
        logger.warning(f"[STAGE 3 GET ERROR] analysis_id={analysis_id}: {e}")
    return None


def get_profile_by_session_id(session_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Retrieves canonical business profile by session_id."""
    try:
        sess_uuid = uuid.UUID(session_id)
        rec = db.query(StructuredBusinessProfile).filter(
            StructuredBusinessProfile.session_id == sess_uuid
        ).order_by(StructuredBusinessProfile.profile_version.desc()).first()
        if rec:
            return rec.profile_json
    except Exception as e:
        logger.warning(f"[STAGE 3 GET ERROR] session_id={session_id}: {e}")
    return None
