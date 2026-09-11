from typing import Dict, Any, List, Tuple


def calculate_deterministic_confidence(
    ontology_candidate: Dict[str, Any],
    nic_candidate: Dict[str, Any],
    competing_nic_candidates: List[Dict[str, Any]],
    hierarchy_valid: bool,
    hierarchy_score: float,
    profile_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes explainable, deterministic confidence based on 5 weighted pillars:
    1. Ontology Match Score (30%)
    2. NIC Activity Match Score (25%)
    3. Hierarchy Consistency Score (15%)
    4. Profile Context Consistency Score (15%)
    5. Candidate Separation Score (15%)
    """
    # 1. Ontology Match Score (0.0 to 1.0)
    ont_raw_score = ontology_candidate.get("score", 0.0) if ontology_candidate else 0.0
    ontology_match = round(min(max(float(ont_raw_score), 0.0), 1.0), 3)

    # 2. NIC Activity Match Score (0.0 to 1.0)
    nic_raw_score = nic_candidate.get("match_score", nic_candidate.get("score", 0.0)) if nic_candidate else 0.0
    nic_activity_match = round(min(max(float(nic_raw_score), 0.0), 1.0), 3)

    # 3. Hierarchy Consistency Score (0.0 to 1.0)
    hierarchy_consistency = round(min(max(float(hierarchy_score if hierarchy_valid else 0.0), 0.0), 1.0), 3)

    # 4. Profile Context Consistency Score (0.0 to 1.0)
    # Check if products, skills, or intent reinforce the chosen business activity
    context_score = 0.50  # baseline
    if profile_context:
        skills = profile_context.get("skills") or profile_context.get("entrepreneur_skills") or []
        products = profile_context.get("products") or []
        intent = profile_context.get("intent", "")

        # If user listed skills or products aligned with ontology
        if skills:
            context_score += 0.25
        if products:
            context_score += 0.15
        if intent in ["start_business", "expand_business", "existing_business"]:
            context_score += 0.10
    profile_context_consistency = round(min(max(context_score, 0.0), 1.0), 3)

    # 5. Candidate Separation Score (0.0 to 1.0)
    cand_scores = [c.get("match_score", c.get("score", 0.0)) for c in competing_nic_candidates]
    cand_scores = [s for s in cand_scores if s > 0]
    
    if len(cand_scores) <= 1:
        candidate_separation = 1.0 if cand_scores else 0.0
    else:
        top_1 = cand_scores[0]
        top_2 = cand_scores[1]
        diff = top_1 - top_2
        # Normalizing separation: diff of 0.30 or higher is full separation (1.0)
        candidate_separation = round(min(max(diff / max(top_1, 0.10), 0.0), 1.0), 3)

    # Weighted Mathematical Formula
    final_score = (
        (ontology_match * 0.30) +
        (nic_activity_match * 0.25) +
        (hierarchy_consistency * 0.15) +
        (profile_context_consistency * 0.15) +
        (candidate_separation * 0.15)
    )
    final_score = round(min(max(final_score, 0.0), 1.0), 2)
    percentage = int(round(final_score * 100))

    # Level Classification
    if final_score >= 0.90:
        level = "HIGH"
    elif final_score >= 0.75:
        level = "MEDIUM"
    elif final_score >= 0.60:
        level = "LOW"
    else:
        level = "INSUFFICIENT_CONFIDENCE"

    breakdown = {
        "ontology_match": ontology_match,
        "nic_activity_match": nic_activity_match,
        "hierarchy_consistency": hierarchy_consistency,
        "profile_context_consistency": profile_context_consistency,
        "candidate_separation": candidate_separation
    }

    return {
        "score": final_score,
        "percentage": percentage,
        "level": level,
        "breakdown": breakdown
    }
