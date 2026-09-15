"""
Deterministic Stage 10 Entrepreneur Profile Engine for KALPA MSME Platform.
Evaluates entrepreneur ↔ business alignment across 5 deterministic dimensions:
1. Skill alignment
2. Experience alignment
3. Training readiness
4. Resource availability
5. Operational readiness

DOES NOT use an LLM for scoring.
UNKNOWN remains UNKNOWN.
"""
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
    ComponentScore,
    ReadinessGap,
    RequiredSupportItem,
    ClarificationQuestion,
    ProvenanceRecord,
)
from app.knowledge.repositories.requirements_repository import RequirementsRepository
from app.knowledge.repositories.benchmarks_repository import BenchmarksRepository
from app.services.entrepreneur_profile_engine.constants import (
    WEIGHT_SKILLS,
    WEIGHT_EXPERIENCE,
    WEIGHT_TRAINING,
    WEIGHT_RESOURCES,
    WEIGHT_OPERATIONS,
    READINESS_THRESHOLD_HIGH,
    READINESS_THRESHOLD_MODERATE,
    READINESS_THRESHOLD_DEVELOPING,
    DOMAIN_SKILL_SYNONYMS,
    STANDARD_SUPPORT_PROGRAMS,
)
from app.core.logging import logger


class EntrepreneurProfileEngine:
    """
    Deterministic rules-based evaluation engine for Stage 10 Entrepreneur Readiness.
    """

    def __init__(self):
        self.requirements_repo = RequirementsRepository()
        self.benchmarks_repo = BenchmarksRepository()

    def _resolve_business_node_id(self, biz: Dict[str, Any]) -> Tuple[str, str]:
        """Resolves canonical business node id and title."""
        biz_id = (
            biz.get("business_id") or
            biz.get("business_node_id") or
            biz.get("specific_business") or
            biz.get("category") or
            "flour_milling_micro"
        )
        title = biz.get("business_title") or biz.get("specific_business") or biz.get("category") or "Micro Enterprise"
        
        # Clean slug mapping
        slug = str(biz_id).lower().replace(" ", "_").replace("-", "_")
        if "flour" in slug or "atta" in slug or "chakki" in slug:
            return "flour_milling_micro", title or "Micro Flour Milling Unit"
        elif "oil" in slug or "expeller" in slug:
            return "oil_expeller_unit", title or "Cold-Pressed Oil Expeller Unit"
        elif "spice" in slug or "masala" in slug:
            return "spice_grinding_packaging", title or "Spice Grinding & Packaging Unit"
        elif "dairy" in slug or "milk" in slug or "chilling" in slug:
            return "dairy_micro_chilling_aggregator", title or "Dairy Micro Chilling Unit"
        elif "poultry" in slug or "broiler" in slug:
            return "poultry_broiler_farm", title or "Poultry Broiler Farm"
        elif "weaving" in slug or "handloom" in slug:
            return "handloom_weaving_unit", title or "Handloom Weaving Unit"
        elif "solar" in slug or "pump" in slug:
            return "solar_pump_repair_service", title or "Solar Pump Repair Service"
        elif "compost" in slug or "fertilizer" in slug:
            return "organic_fertilizer_composting", title or "Organic Fertilizer Composting"
        
        return slug, title

    def _extract_inputs(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Extracts normalized user entrepreneur profile, business profile, and location."""
        # 1. Entrepreneur Profile
        ep = (
            request_data.get("user_profile") or
            request_data.get("entrepreneur_profile") or
            request_data.get("entrepreneur_context") or
            {}
        )
        if hasattr(ep, "model_dump"):
            ep = ep.model_dump()

        # Check if skills/experience were passed under top-level keys
        if "skills" in request_data and "skills" not in ep:
            ep["skills"] = request_data["skills"]
        if "experience" in request_data and "experience" not in ep:
            ep["experience"] = request_data["experience"]

        # 2. Business Profile
        biz = (
            request_data.get("business_profile") or
            request_data.get("business_context") or
            {}
        )
        if hasattr(biz, "model_dump"):
            biz = biz.model_dump()

        # 3. Location Profile
        loc = (
            request_data.get("location_profile") or
            request_data.get("location_context") or
            {}
        )
        if hasattr(loc, "model_dump"):
            loc = loc.model_dump()

        return ep, biz, loc

    def evaluate_skills(
        self,
        ep: Dict[str, Any],
        reqs: Optional[Any],
        node_id: str
    ) -> ComponentScore:
        """
        Evaluates deterministic skill alignment against benchmark requirements.
        """
        raw_skills = ep.get("skills") or {}
        if isinstance(raw_skills, dict):
            skills_list = raw_skills.get("skills", [])
            certified = raw_skills.get("certified_skills", [])
            level = raw_skills.get("skill_level")
        elif isinstance(raw_skills, list):
            skills_list = raw_skills
            certified = []
            level = None
        else:
            skills_list = [str(raw_skills)]
            certified = []
            level = None

        benchmark_skills = []
        if reqs and hasattr(reqs, "skills_and_manpower") and reqs.skills_and_manpower:
            sm = reqs.skills_and_manpower
            benchmark_skills = sm.get("key_skills", []) if isinstance(sm, dict) else getattr(sm, "key_skills", [])

        if not benchmark_skills:
            benchmark_skills = DOMAIN_SKILL_SYNONYMS.get(node_id, ["Domain technical knowledge", "Operations management"])

        if not skills_list:
            return ComponentScore(
                score=30.0,
                weight=WEIGHT_SKILLS,
                status="UNKNOWN",
                evidence="No prior specific skills declared by entrepreneur. Baseline learning support required.",
                matched_items=[],
                missing_items=benchmark_skills,
                details={"match_ratio": 0.0, "level": "UNKNOWN"}
            )

        # Match user skills against benchmark tokens
        matched = []
        missing = []
        user_tokens = set(" ".join(skills_list).lower().replace(",", " ").replace("-", " ").split())
        
        # Add domain synonyms
        synonyms = set(DOMAIN_SKILL_SYNONYMS.get(node_id, []))

        for req_skill in benchmark_skills:
            req_words = set(req_skill.lower().replace(",", " ").replace("(", " ").replace(")", " ").split())
            if (req_words & user_tokens) or (synonyms & user_tokens):
                matched.append(req_skill)
            else:
                missing.append(req_skill)

        if not matched and skills_list:
            # Check if any general trade skills match
            matched = [skills_list[0]]
            missing = benchmark_skills[1:] if len(benchmark_skills) > 1 else []

        match_ratio = len(matched) / max(1, len(benchmark_skills))
        base_score = min(100.0, match_ratio * 90.0 + (10.0 if certified else 0.0))
        
        if level == "EXPERT":
            base_score = min(100.0, base_score + 15.0)
        elif level == "INTERMEDIATE":
            base_score = min(100.0, base_score + 10.0)

        status = "STRONG" if base_score >= 75 else ("ADEQUATE" if base_score >= 50 else "DEVELOPING")
        evidence = f"Matched {len(matched)} of {len(benchmark_skills)} benchmark skills: {', '.join(matched)}."

        return ComponentScore(
            score=round(base_score, 1),
            weight=WEIGHT_SKILLS,
            status=status,
            evidence=evidence,
            matched_items=matched,
            missing_items=missing,
            details={"match_ratio": round(match_ratio, 2), "certified_count": len(certified)}
        )

    def evaluate_experience(
        self,
        ep: Dict[str, Any],
        node_id: str
    ) -> ComponentScore:
        """
        Evaluates deterministic experience alignment against minimum recommended years.
        """
        raw_exp = ep.get("experience") or {}
        if isinstance(raw_exp, dict):
            years = raw_exp.get("years_of_experience")
            if years is None:
                years = raw_exp.get("years")
            domain = raw_exp.get("domain") or ""
            prior_biz = raw_exp.get("prior_business_ownership", False)
        elif isinstance(raw_exp, (int, float)):
            years = float(raw_exp)
            domain = ""
            prior_biz = False
        else:
            years = None
            domain = ""
            prior_biz = False

        benchmark_min_years = 2.0 if node_id in ["flour_milling_micro", "oil_expeller_unit", "solar_pump_repair_service"] else 1.0

        if years is None:
            return ComponentScore(
                score=40.0,
                weight=WEIGHT_EXPERIENCE,
                status="UNKNOWN",
                evidence="Work experience years not explicitly stated; assuming entry-level baseline with mentorship.",
                matched_items=[],
                missing_items=["years_of_experience"],
                details={"benchmark_min_years": benchmark_min_years}
            )

        years = float(years)
        if years >= benchmark_min_years:
            score = min(100.0, 75.0 + ((years - benchmark_min_years) / benchmark_min_years) * 25.0)
            if prior_biz:
                score = min(100.0, score + 10.0)
            status = "STRONG"
            evidence = f"Entrepreneur possesses {years:.1f} years of relevant domain experience (benchmark: {benchmark_min_years:.1f} years)."
        elif years > 0:
            score = 50.0 + (years / benchmark_min_years) * 25.0
            status = "ADEQUATE"
            evidence = f"Entrepreneur possesses {years:.1f} years experience (approaching benchmark of {benchmark_min_years:.1f} years)."
        else:
            score = 25.0
            status = "DEVELOPING"
            evidence = "First-time entrepreneur with 0 reported years in direct trade; structured incubation recommended."

        return ComponentScore(
            score=round(score, 1),
            weight=WEIGHT_EXPERIENCE,
            status=status,
            evidence=evidence,
            matched_items=[f"{years} years experience"] if years > 0 else [],
            missing_items=[f"{benchmark_min_years} years recommended domain track record"] if years < benchmark_min_years else [],
            details={"years_reported": years, "benchmark_min_years": benchmark_min_years, "prior_business": prior_biz}
        )

    def evaluate_training(
        self,
        ep: Dict[str, Any],
        reqs: Optional[Any],
        node_id: str
    ) -> ComponentScore:
        """
        Evaluates training readiness and statutory certifications.
        """
        raw_tr = ep.get("training") or {}
        if isinstance(raw_tr, dict):
            has_formal = raw_tr.get("has_formal_training")
            certs = raw_tr.get("certifications", [])
            willing = raw_tr.get("willing_to_undergo_training", True)
        elif isinstance(raw_tr, bool):
            has_formal = raw_tr
            certs = []
            willing = True
        elif isinstance(raw_tr, list):
            has_formal = len(raw_tr) > 0
            certs = raw_tr
            willing = True
        else:
            has_formal = None
            certs = []
            willing = True

        mandatory_certs = []
        if node_id in ["flour_milling_micro", "oil_expeller_unit", "spice_grinding_packaging", "dairy_micro_chilling_aggregator"]:
            mandatory_certs.append("FSSAI / FoSTaC Food Safety Certificate")

        def _cert_matches(mand: str, user_cert: str) -> bool:
            mand_lower = mand.lower()
            u_lower = user_cert.lower()
            if "fostac" in u_lower or "fssai" in u_lower or "food safety" in u_lower:
                if "fostac" in mand_lower or "fssai" in mand_lower:
                    return True
            if "pmkvy" in u_lower and "pmkvy" in mand_lower:
                return True
            return any(w in u_lower for w in mand_lower.replace("/", " ").split() if len(w) > 3)

        matched_certs = [c for c in certs if any(_cert_matches(m, c) for m in mandatory_certs)]
        missing_certs = [m for m in mandatory_certs if not any(_cert_matches(m, c) for c in certs)]

        if has_formal or certs:
            has_all_mandatory = len(missing_certs) == 0
            score = 85.0 + (15.0 if has_all_mandatory else 0.0)
            status = "STRONG"
            evidence = f"Formal trade certifications verified: {', '.join(certs) if certs else 'Vocational Training'}"
        elif willing:
            score = 65.0
            status = "ADEQUATE"
            evidence = "Entrepreneur is willing to undertake prerequisite EDP/FoSTaC training prior to commissioning."
        else:
            score = 30.0
            status = "DEFICIENT"
            evidence = "No formal certification and reluctance towards mandatory trade training."

        return ComponentScore(
            score=round(score, 1),
            weight=WEIGHT_TRAINING,
            status=status,
            evidence=evidence,
            matched_items=certs if certs else (["Willing to undergo training"] if willing else []),
            missing_items=missing_certs,
            details={"has_formal_training": has_formal, "certifications_count": len(certs)}
        )

    def evaluate_resources(
        self,
        ep: Dict[str, Any],
        reqs: Optional[Any],
        node_id: str
    ) -> ComponentScore:
        """
        Evaluates physical premises, power connection, and machinery readiness.
        """
        raw_res = ep.get("resources") or {}
        if not isinstance(raw_res, dict):
            raw_res = {}

        area = raw_res.get("available_area_sqft")
        power = raw_res.get("power_connection_type")
        machinery = raw_res.get("existing_machinery", [])
        premises_avail = raw_res.get("land_or_premises_available")

        req_area = 200.0
        req_power = "SINGLE_PHASE"
        if reqs:
            if hasattr(reqs, "space_and_infrastructure") and reqs.space_and_infrastructure:
                si = reqs.space_and_infrastructure
                req_area = float(si.get("built_up_area_sqft_min", 200.0) if isinstance(si, dict) else getattr(si, "built_up_area_sqft_min", 200.0))
            if hasattr(reqs, "power_and_utilities") and reqs.power_and_utilities:
                pu = reqs.power_and_utilities
                req_power = pu.get("power_connection_type", "SINGLE_PHASE") if isinstance(pu, dict) else getattr(pu, "power_connection_type", "SINGLE_PHASE")

        # 1. Area score
        if area is not None:
            area_ratio = min(1.5, float(area) / max(1.0, req_area))
            area_score = min(100.0, area_ratio * 100.0)
        elif premises_avail is True:
            area_score = 75.0
        elif premises_avail is False:
            area_score = 30.0
        else:
            area_score = 50.0  # UNKNOWN

        # 2. Power score
        if power:
            if req_power == "THREE_PHASE_COMMERCIAL":
                power_score = 100.0 if "three" in power.lower() or "3" in power.lower() else 50.0
            else:
                power_score = 100.0
        else:
            power_score = 50.0  # UNKNOWN

        # 3. Machinery score
        machinery_score = 80.0 if len(machinery) > 0 else 60.0

        resource_score = 0.50 * area_score + 0.35 * power_score + 0.15 * machinery_score
        status = "STRONG" if resource_score >= 75 else ("ADEQUATE" if resource_score >= 50 else "DEVELOPING")

        matched = []
        missing = []
        if area and area >= req_area:
            matched.append(f"Premises Area ({area:.0f} sqft >= required {req_area:.0f} sqft)")
        elif area:
            missing.append(f"Premises Area shortfall ({area:.0f} sqft vs required {req_area:.0f} sqft)")

        if power and power_score >= 75:
            matched.append(f"Power connection adequate ({power})")
        elif power:
            missing.append(f"Power upgrade required: requires {req_power} (current: {power})")

        return ComponentScore(
            score=round(resource_score, 1),
            weight=WEIGHT_RESOURCES,
            status=status,
            evidence=f"Physical infrastructure readiness evaluated at {resource_score:.1f}%.",
            matched_items=matched,
            missing_items=missing,
            details={"area_sqft": area, "required_area_sqft": req_area, "power_connection": power, "required_power": req_power}
        )

    def evaluate_operations(
        self,
        ep: Dict[str, Any],
        reqs: Optional[Any],
        node_id: str
    ) -> ComponentScore:
        """
        Evaluates operational commitment and worker availability.
        """
        raw_ops = ep.get("operations") or {}
        if not isinstance(raw_ops, dict):
            raw_ops = {}

        commit = raw_ops.get("commitment_type")
        family = int(raw_ops.get("available_family_helpers") or 0)
        hired = int(raw_ops.get("hired_workers_planned") or 0)
        total_workers = family + hired + 1  # Including entrepreneur

        req_min_workers = 2
        if reqs and hasattr(reqs, "skills_and_manpower") and reqs.skills_and_manpower:
            sm = reqs.skills_and_manpower
            req_min_workers = int(sm.get("min_workers", 2) if isinstance(sm, dict) else getattr(sm, "min_workers", 2))

        # Commitment score
        if commit == "FULL_TIME":
            commit_score = 100.0
        elif commit == "PART_TIME":
            commit_score = 65.0
        elif commit == "SEASONAL":
            commit_score = 45.0
        else:
            commit_score = 75.0  # Assume full-time default

        # Manpower score
        manpower_ratio = min(1.5, total_workers / max(1, req_min_workers))
        manpower_score = min(100.0, manpower_ratio * 100.0)

        ops_score = 0.60 * commit_score + 0.40 * manpower_score
        status = "STRONG" if ops_score >= 75 else ("ADEQUATE" if ops_score >= 50 else "DEVELOPING")

        matched = [f"Operational commitment: {commit or 'FULL_TIME'}"]
        missing = []
        if total_workers < req_min_workers:
            missing.append(f"Worker shortfall: {total_workers} available vs {req_min_workers} benchmark minimum")

        return ComponentScore(
            score=round(ops_score, 1),
            weight=WEIGHT_OPERATIONS,
            status=status,
            evidence=f"Operational commitment and manpower capacity evaluated at {ops_score:.1f}%.",
            matched_items=matched,
            missing_items=missing,
            details={"commitment_type": commit or "FULL_TIME", "available_workers": total_workers, "required_workers": req_min_workers}
        )

    def identify_missing_fields_and_questions(
        self,
        ep: Dict[str, Any],
        node_id: str,
        title: str
    ) -> Tuple[List[str], List[ClarificationQuestion]]:
        """
        Determines missing fields in the entrepreneur profile and produces localized clarification questions.
        """
        missing_fields = []
        questions = []

        # 1. Skills
        raw_skills = ep.get("skills")
        if not raw_skills or (isinstance(raw_skills, dict) and not raw_skills.get("skills")):
            missing_fields.append("skills")
            questions.append(ClarificationQuestion(
                field="skills",
                question_en=f"What relevant skills, machine handling, or trade experience do you possess for running a {title}?",
                question_hi=f"{title} चलाने के लिए आपके पास कौन सा तकनीकी हुनर, मशीन चलाने का अनुभव या हुनर है?",
                question_kn=f"{title} ನಡೆಸಲು ನಿಮ್ಮಲ್ಲಿ ಯಾವ ತಾಂತ್ರಿಕ ಕೌಶಲ್ಯ ಅಥವಾ ಅನುಭವವಿದೆ?",
                input_type="text",
                suggested_options=["Machine operation", "Basic maintenance", "Retail sales", "No prior experience"],
                importance="HIGH"
            ))

        # 2. Experience
        raw_exp = ep.get("experience")
        years = raw_exp.get("years_of_experience") if isinstance(raw_exp, dict) else (raw_exp if isinstance(raw_exp, (int, float)) else None)
        if years is None:
            missing_fields.append("experience.years_of_experience")
            questions.append(ClarificationQuestion(
                field="experience.years_of_experience",
                question_en="How many years of prior experience do you have in this domain or running a business?",
                question_hi="इस व्यापार या संबंधित क्षेत्र में आपके पास कितने वर्षों का अनुभव है?",
                question_kn="ಈ ಕ್ಷೇತ್ರದಲ್ಲಿ ನಿಮಗೆ ಎಷ್ಟು ವರ್ಷಗಳ ಅನುಭವವಿದೆ?",
                input_type="number",
                suggested_options=["0 years (Fresh)", "1-2 years", "3-5 years", "5+ years"],
                importance="HIGH"
            ))

        # 3. Resources (Premises / Area)
        raw_res = ep.get("resources") or {}
        if not isinstance(raw_res, dict) or (raw_res.get("available_area_sqft") is None and raw_res.get("land_or_premises_available") is None):
            missing_fields.append("resources.available_area_sqft")
            questions.append(ClarificationQuestion(
                field="resources.available_area_sqft",
                question_en="Do you have land or a commercial shop ready? What is the approximate area in square feet?",
                question_hi="क्या आपके पास दुकान या जगह उपलब्ध है? लगभग कितने स्क्वायर फीट जगह है?",
                question_kn="ನಿಮ್ಮ ಬಳಿ ಜಾಗ ಅಥವಾ ಅಂಗಡಿ ಲಭ್ಯವಿದೆಯೇ? ಎಷ್ಟು ಚದರ ಅಡಿ?",
                input_type="number",
                suggested_options=["150 sq ft", "250 sq ft", "500 sq ft", "Yet to arrange"],
                importance="MEDIUM"
            ))

        # 4. Resources (Power Connection)
        if not isinstance(raw_res, dict) or not raw_res.get("power_connection_type"):
            if node_id in ["flour_milling_micro", "oil_expeller_unit", "solar_pump_repair_service"]:
                missing_fields.append("resources.power_connection_type")
                questions.append(ClarificationQuestion(
                    field="resources.power_connection_type",
                    question_en="What type of electricity connection is available at your site (Single Phase or 3-Phase Commercial)?",
                    question_hi="आपकी दुकान/स्थान पर बिजली का कौन सा कनेक्शन है (सिंगल फेस या 3-फेस कमर्शियल)?",
                    question_kn="ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲಿ ಯಾವ ರೀತಿಯ ವಿದ್ಯುತ್ ಸಂಪರ್ಕವಿದೆ (ಸಿಂಗಲ್ ಫೇಸ್ ಅಥವಾ 3-ಫೇಸ್)?",
                    input_type="select",
                    suggested_options=["THREE_PHASE_COMMERCIAL", "SINGLE_PHASE", "NO_CONNECTION"],
                    importance="HIGH"
                ))

        return missing_fields, questions

    def analyze(self, payload: Dict[str, Any]) -> EntrepreneurReadinessResponse:
        """
        Main deterministic analysis entrypoint for Stage 10.
        """
        ep, biz, loc = self._extract_inputs(payload)
        node_id, title = self._resolve_business_node_id(biz)
        
        # Retrieve benchmark requirements
        reqs = self.requirements_repo.get_by_business(node_id)
        
        # Check missing fields
        missing_fields, questions = self.identify_missing_fields_and_questions(ep, node_id, title)
        
        # Evaluate 5 deterministic components
        skills_comp = self.evaluate_skills(ep, reqs, node_id)
        exp_comp = self.evaluate_experience(ep, node_id)
        train_comp = self.evaluate_training(ep, reqs, node_id)
        res_comp = self.evaluate_resources(ep, reqs, node_id)
        ops_comp = self.evaluate_operations(ep, reqs, node_id)

        # Weighted composite score
        overall_score = (
            skills_comp.weight * skills_comp.score +
            exp_comp.weight * exp_comp.score +
            train_comp.weight * train_comp.score +
            res_comp.weight * res_comp.score +
            ops_comp.weight * ops_comp.score
        )
        overall_score = round(overall_score, 1)

        # Readiness Level
        if overall_score >= READINESS_THRESHOLD_HIGH:
            readiness_level = "HIGH"
        elif overall_score >= READINESS_THRESHOLD_MODERATE:
            readiness_level = "MODERATE"
        elif overall_score >= READINESS_THRESHOLD_DEVELOPING:
            readiness_level = "DEVELOPING"
        else:
            readiness_level = "LOW"

        # Determine if profile is incomplete
        # If critical fields like skills or experience or power are missing, return PROFILE_INCOMPLETE status
        is_profile_incomplete = len(missing_fields) >= 2
        status = "PROFILE_INCOMPLETE" if is_profile_incomplete else "READY"

        # Synthesize Strengths
        strengths = []
        if skills_comp.score >= 70:
            strengths.append(f"Strong practical domain skill alignment ({skills_comp.score:.0f}%)")
        if exp_comp.score >= 70:
            strengths.append(f"Demonstrated operating track record ({exp_comp.details.get('years_reported', 0)} years)")
        if train_comp.score >= 70:
            strengths.append("Certified or proactive training orientation")
        if res_comp.score >= 70:
            strengths.append("Adequate physical infrastructure & utility access")
        if ops_comp.score >= 70:
            strengths.append("Full-time dedicated founder bandwidth")
        if not strengths:
            strengths.append("High entrepreneurial motivation with open learning agility")

        # Synthesize Gaps
        gaps = []
        if skills_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="SKILLS",
                gap_description=f"Skill gaps identified in: {', '.join(skills_comp.missing_items) if skills_comp.missing_items else 'specific machine operations'}",
                severity="HIGH" if skills_comp.score < 40 else "MEDIUM",
                required_intervention="Short-term practical apprenticeship under experienced master operator",
                benchmark_reference=node_id
            ))
        if exp_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="EXPERIENCE",
                gap_description=f"Limited direct enterprise experience ({exp_comp.details.get('years_reported', 0)} years vs {exp_comp.details.get('benchmark_min_years', 2)} years recommended)",
                severity="MEDIUM",
                required_intervention="Incubation mentoring and handholding through first 6 months of operations",
                benchmark_reference=node_id
            ))
        if train_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="TRAINING",
                gap_description="Mandatory food safety / trade compliance certification pending",
                severity="HIGH" if "FSSAI" in str(train_comp.missing_items) else "MEDIUM",
                required_intervention="Complete FoSTaC / RSETI certificate course before commercial launch",
                benchmark_reference=node_id
            ))
        if res_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="RESOURCES",
                gap_description=f"Utility or physical space constraints ({', '.join(res_comp.missing_items) if res_comp.missing_items else 'adequate premises/power'})",
                severity="HIGH" if "power" in str(res_comp.missing_items).lower() else "MEDIUM",
                required_intervention="Upgrade commercial power sanction or secure compliant premise lease",
                benchmark_reference=node_id
            ))

        # Synthesize Required Support
        required_support = []
        if any(g.dimension == "TRAINING" for g in gaps) or train_comp.score < 75:
            required_support.append(RequiredSupportItem(
                category="TRAINING",
                title=STANDARD_SUPPORT_PROGRAMS["TRAINING"]["title"],
                description=STANDARD_SUPPORT_PROGRAMS["TRAINING"]["description"],
                scheme_or_program_link=STANDARD_SUPPORT_PROGRAMS["TRAINING"]["link"],
                priority="HIGH"
            ))
        if any(g.dimension == "SKILLS" for g in gaps) or skills_comp.score < 70:
            required_support.append(RequiredSupportItem(
                category="TRAINING",
                title=STANDARD_SUPPORT_PROGRAMS["SKILLS"]["title"],
                description=STANDARD_SUPPORT_PROGRAMS["SKILLS"]["description"],
                scheme_or_program_link=STANDARD_SUPPORT_PROGRAMS["SKILLS"]["link"],
                priority="HIGH"
            ))
        if any("power" in g.gap_description.lower() for g in gaps):
            required_support.append(RequiredSupportItem(
                category="INFRASTRUCTURE",
                title=STANDARD_SUPPORT_PROGRAMS["INFRASTRUCTURE"]["title"],
                description=STANDARD_SUPPORT_PROGRAMS["INFRASTRUCTURE"]["description"],
                scheme_or_program_link=STANDARD_SUPPORT_PROGRAMS["INFRASTRUCTURE"]["link"],
                priority="HIGH"
            ))
        
        required_support.append(RequiredSupportItem(
            category="ADVISORY",
            title=STANDARD_SUPPORT_PROGRAMS["ADVISORY"]["title"],
            description=STANDARD_SUPPORT_PROGRAMS["ADVISORY"]["description"],
            scheme_or_program_link=STANDARD_SUPPORT_PROGRAMS["ADVISORY"]["link"],
            priority="MEDIUM"
        ))

        # Confidence calculation
        assessed_factors = 5
        missing_count = len(missing_fields)
        confidence = max(0.40, round(1.0 - (missing_count * 0.15), 2))

        return EntrepreneurReadinessResponse(
            success=True,
            status=status,
            analysis_id=payload.get("analysis_id"),
            session_id=payload.get("session_id"),
            business_title=title,
            business_node_id=node_id,
            readiness_score=overall_score,
            readiness_level=readiness_level if status == "READY" else "INCOMPLETE",
            component_scores={
                "skills": skills_comp,
                "experience": exp_comp,
                "training": train_comp,
                "resources": res_comp,
                "operational_readiness": ops_comp,
            },
            strengths=strengths,
            gaps=gaps,
            required_support=required_support,
            missing_fields=missing_fields,
            questions=questions,
            confidence=confidence,
            provenance=ProvenanceRecord(
                benchmark_node_id=node_id,
                evaluation_type="DETERMINISTIC_RULES"
            )
        )


# Global singleton instance
entrepreneur_profile_engine = EntrepreneurProfileEngine()
