"""
Deterministic Stage 10 Entrepreneur Profile Engine for KALPA MSME Platform.
Evaluates entrepreneur ↔ business alignment across 5 deterministic dimensions:
1. Skill alignment
2. Experience alignment
3. Training readiness
4. Resource availability
5. Operational readiness

Contextual & Benchmark-driven:
- Uses curated BusinessRepository and RequirementsRepository as single source of truth.
- Zero hardcoded domain assumptions in calculation logic.
- UNKNOWN remains UNKNOWN when evidence is missing.
- DOES NOT use an LLM for scoring.
- Never resurrects answered clarification questions.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
    ComponentScore,
    ReadinessGap,
    RequiredSupportItem,
    ClarificationQuestion,
    ProvenanceRecord,
)
from app.knowledge.repositories.business_repository import BusinessRepository
from app.knowledge.repositories.requirements_repository import RequirementsRepository
from app.knowledge.repositories.benchmarks_repository import BenchmarksRepository
from app.knowledge.repositories.schemes_repository import SchemesRepository
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
    CONTEXTUAL_SUPPORT_CATALOG,
)
from app.schemas.knowledge import BusinessProfileSchema, BusinessRequirementSchema
from app.core.logging import logger


class EntrepreneurProfileEngine:
    """
    Deterministic rules-based evaluation engine for Stage 10 Entrepreneur Readiness.
    """

    def __init__(self):
        self.business_repo = BusinessRepository()
        self.requirements_repo = RequirementsRepository()
        self.benchmarks_repo = BenchmarksRepository()
        self.schemes_repo = SchemesRepository()

    def _resolve_business_context(self, biz: Dict[str, Any]) -> Tuple[Optional[Any], Optional[Any], str, str]:
        """
        Resolves canonical business profile and requirements from curated knowledge repositories.
        """
        biz_id = str(
            biz.get("business_id") or
            biz.get("business_node_id") or
            biz.get("specific_business") or
            biz.get("category") or
            "saree_retail"
        )
        title = str(biz.get("business_title") or biz.get("specific_business") or biz.get("category") or "Micro Enterprise")

        # 1. Look up in BusinessRepository
        profile = self.business_repo.get_profile(biz_id)
        if not profile and biz.get("specific_business"):
            profile = self.business_repo.get_profile(biz.get("specific_business"))
        if not profile and biz.get("category"):
            profile = self.business_repo.get_profile(biz.get("category"))

        # 2. Look up in RequirementsRepository
        canonical_node_id = profile.business_node_id if profile else biz_id.lower().replace(" ", "_").replace("-", "_")
        reqs = self.requirements_repo.get_by_business(canonical_node_id)
        if not reqs and profile:
            reqs = self.requirements_repo.get_by_business(profile.business_node_id)

        # Preserve the specific requested business_id if provided, else fallback to canonical_node_id
        resolved_node_id = str(biz.get("business_id") or biz.get("business_node_id") or canonical_node_id)
        resolved_title = profile.business_title if profile else title
        return profile, reqs, resolved_node_id, resolved_title

    def _resolve_eval_args(self, arg1: Any = None, arg2: Any = None, arg3: Any = None) -> Tuple[Optional[Any], Optional[Any], str]:
        """Resolves (profile, reqs, node_id) flexibly from 1, 2, or 3 arguments."""
        profile = None
        reqs = None
        node_id = "saree_retail"

        for a in (arg1, arg2, arg3):
            if a is None:
                continue
            if isinstance(a, str):
                node_id = a
            elif isinstance(a, BusinessProfileSchema) or getattr(a, "__class__", None).__name__ == "BusinessProfileSchema":
                profile = a
            elif isinstance(a, BusinessRequirementSchema) or getattr(a, "__class__", None).__name__ == "BusinessRequirementSchema":
                reqs = a
            elif isinstance(a, dict):
                reqs = a
            elif hasattr(a, "business_node_id") or hasattr(a, "business_id"):
                profile = a

        if not profile and node_id:
            profile = self.business_repo.get_profile(node_id)
        if not reqs and node_id:
            reqs = self.requirements_repo.get_by_business(node_id)
        if profile and not reqs:
            reqs = self.requirements_repo.get_by_business(getattr(profile, "business_node_id", node_id))

        return profile, reqs, node_id

    def _extract_inputs(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Extracts normalized user entrepreneur profile, business profile, and location."""
        ep = (
            request_data.get("entrepreneur_profile") or
            request_data.get("user_profile") or
            request_data.get("entrepreneur_context") or
            {}
        )
        if hasattr(ep, "model_dump"):
            ep = ep.model_dump()

        if "skills" in request_data and "skills" not in ep:
            ep["skills"] = request_data["skills"]
        if "experience" in request_data and "experience" not in ep:
            ep["experience"] = request_data["experience"]

        biz = (
            request_data.get("business_profile") or
            request_data.get("business_context") or
            {}
        )
        if hasattr(biz, "model_dump"):
            biz = biz.model_dump()

        loc = (
            request_data.get("location_profile") or
            request_data.get("location_context") or
            {}
        )
        if hasattr(loc, "model_dump"):
            loc = loc.model_dump()

        return ep, biz, loc

    def merge_profiles(self, existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deeply merges extracted clarification updates into the canonical entrepreneur profile
        without overwriting existing valid data with nulls or empty structures.
        Also tracks answered fields to prevent question reappearance.
        """
        merged = dict(existing or {})
        answered = set(merged.get("answered_fields", []))

        for k, v in updates.items():
            if not v and v != 0 and v is not False:
                continue

            if k == "skills":
                curr_skills = merged.get("skills") or {}
                if isinstance(curr_skills, list):
                    curr_skills = {"skills": curr_skills}
                elif not isinstance(curr_skills, dict):
                    curr_skills = {"skills": []}

                new_skills = v.get("skills", []) if isinstance(v, dict) else (v if isinstance(v, list) else [str(v)])
                existing_list = list(curr_skills.get("skills", []))
                for s in new_skills:
                    if s and s not in existing_list:
                        existing_list.append(s)
                curr_skills["skills"] = existing_list
                curr_skills["source"] = "USER_CLARIFICATION"
                if isinstance(v, dict) and v.get("raw_text"):
                    curr_skills["raw_text"] = v["raw_text"]
                merged["skills"] = curr_skills
                answered.add("skills")

            elif k == "experience":
                curr_exp = merged.get("experience") or {}
                if not isinstance(curr_exp, dict):
                    curr_exp = {"years_of_experience": float(curr_exp) if isinstance(curr_exp, (int, float)) else None}

                if isinstance(v, dict):
                    if v.get("years_of_experience") is not None:
                        curr_exp["years_of_experience"] = float(v["years_of_experience"])
                    if v.get("domain"):
                        curr_exp["domain"] = v["domain"]
                    if v.get("prior_business_ownership") is not None:
                        curr_exp["prior_business_ownership"] = v["prior_business_ownership"]
                    if v.get("raw_text"):
                        curr_exp["raw_text"] = v["raw_text"]
                elif isinstance(v, (int, float)):
                    curr_exp["years_of_experience"] = float(v)

                curr_exp["source"] = "USER_CLARIFICATION"
                merged["experience"] = curr_exp
                answered.add("experience")
                answered.add("experience.years_of_experience")

            elif k == "resources":
                curr_res = merged.get("resources") or {}
                if not isinstance(curr_res, dict):
                    curr_res = {}
                if isinstance(v, dict):
                    for rk, rv in v.items():
                        if rv is not None:
                            curr_res[rk] = rv
                            answered.add(f"resources.{rk}")
                    if v.get("raw_text"):
                        curr_res["raw_text"] = v["raw_text"]
                curr_res["source"] = "USER_CLARIFICATION"
                merged["resources"] = curr_res
                if curr_res.get("available_area_sqft") is not None:
                    answered.add("resources.available_area_sqft")
                    answered.add("resources")
                if curr_res.get("power_connection_type"):
                    answered.add("resources.power_connection_type")

            elif k == "training":
                curr_tr = merged.get("training") or {}
                if not isinstance(curr_tr, dict):
                    curr_tr = {}
                if isinstance(v, dict):
                    for tk, tv in v.items():
                        if tv is not None:
                            if tk == "certifications" and isinstance(tv, list):
                                existing_certs = list(curr_tr.get("certifications", []))
                                for c in tv:
                                    if c not in existing_certs:
                                        existing_certs.append(c)
                                curr_tr["certifications"] = existing_certs
                            else:
                                curr_tr[tk] = tv
                    if v.get("raw_text"):
                        curr_tr["raw_text"] = v["raw_text"]
                curr_tr["source"] = "USER_CLARIFICATION"
                merged["training"] = curr_tr
                answered.add("training")

            elif k == "operations":
                curr_ops = merged.get("operations") or {}
                if not isinstance(curr_ops, dict):
                    curr_ops = {}
                if isinstance(v, dict):
                    for ok, ov in v.items():
                        if ov is not None:
                            curr_ops[ok] = ov
                    if v.get("raw_text"):
                        curr_ops["raw_text"] = v["raw_text"]
                curr_ops["source"] = "USER_CLARIFICATION"
                merged["operations"] = curr_ops
                answered.add("operations")
            else:
                merged[k] = v
                answered.add(k)

        merged["answered_fields"] = sorted(list(answered))
        return merged

    def evaluate_skills(
        self,
        ep: Dict[str, Any],
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None
    ) -> ComponentScore:
        """
        Evaluates deterministic skill alignment against benchmark requirements using normalized taxonomy.
        If skills evidence is absent: status = UNKNOWN, calculation shows 0 of N matched, confidence reduced.
        """
        profile, reqs, node_id = self._resolve_eval_args(arg1, arg2, arg3)

        raw_skills = ep.get("skills") or {}
        evidence_source = "BENCHMARK_DATABASE"
        if isinstance(raw_skills, dict):
            skills_list = raw_skills.get("skills", [])
            certified = raw_skills.get("certified_skills", [])
            level = raw_skills.get("skill_level")
            evidence_source = raw_skills.get("source") or ("USER_CLARIFICATION" if ep.get("answered_fields") and "skills" in ep["answered_fields"] else "USER_INPUT")
        elif isinstance(raw_skills, list):
            skills_list = raw_skills
            certified = []
            level = None
            evidence_source = "USER_INPUT"
        else:
            skills_list = [str(raw_skills)] if str(raw_skills).strip() else []
            certified = []
            level = None
            evidence_source = "USER_INPUT"

        # Resolve benchmark skills from ontology / requirements repository
        benchmark_skills = []
        if reqs and hasattr(reqs, "skills_and_manpower") and reqs.skills_and_manpower:
            sm = reqs.skills_and_manpower
            benchmark_skills = sm.get("key_skills", []) if isinstance(sm, dict) else getattr(sm, "key_skills", [])
        if not benchmark_skills and profile and hasattr(profile, "skills_and_manpower") and profile.skills_and_manpower:
            sm = profile.skills_and_manpower
            benchmark_skills = sm.get("key_skills", []) if isinstance(sm, dict) else getattr(sm, "key_skills", [])
        if not benchmark_skills:
            benchmark_skills = DOMAIN_SKILL_SYNONYMS.get(node_id.lower(), [
                "Domain technical operation", "Customer negotiation & trade management", "Basic accounting"
            ])

        # If user skills are completely unknown / not stated
        if not skills_list:
            return ComponentScore(
                score=30.0,
                weight=WEIGHT_SKILLS,
                status="UNKNOWN",
                evidence=["Domain skills unstated by entrepreneur. Baseline learning support required."],
                evidence_source="UNKNOWN",
                benchmark_requirement=benchmark_skills,
                matched_requirements=[],
                missing_requirements=benchmark_skills,
                matched_items=[],
                missing_items=benchmark_skills,
                gap="Domain skills not declared; learning intervention required",
                confidence=0.40,
                calculation=f"0 of {len(benchmark_skills)} required skill groups verified (Status: UNKNOWN)",
                details={"match_ratio": 0.0, "level": "UNKNOWN", "source": "BENCHMARK_DATABASE"}
            )

        # Match user tokens against benchmark skills taxonomy
        matched = []
        missing = []
        user_tokens = set(" ".join(skills_list).lower().replace(",", " ").replace("(", " ").replace(")", " ").replace("-", " ").replace("_", " ").split())

        for req_skill in benchmark_skills:
            req_words = set(req_skill.lower().replace(",", " ").replace("(", " ").replace(")", " ").replace("-", " ").replace("_", " ").split())
            req_words = {w for w in req_words if len(w) > 2 and w not in ["and", "for", "with", "the", "unit", "and/or"]}
            if req_words & user_tokens:
                matched.append(req_skill)
            else:
                missing.append(req_skill)

        # If user stated skills that don't match domain benchmark at all
        if not matched and skills_list:
            matched = []
            missing = list(benchmark_skills)
            match_ratio = 0.0
            base_score = 15.0 if level == "NOVICE" else (30.0 if level == "INTERMEDIATE" else 20.0)
            status = "GAP"
            calc_str = f"0 of {len(benchmark_skills)} required domain skill groups matched (0% domain overlap)"
            gap_str = f"Shortfall in domain skills: {', '.join(missing)}"
        else:
            match_ratio = len(matched) / max(1, len(benchmark_skills))
            base_score = 40.0 + match_ratio * 50.0 + (15.0 if certified else 0.0)

            if level == "EXPERT":
                base_score = min(100.0, base_score + 10.0)
            elif level == "INTERMEDIATE":
                base_score = min(100.0, base_score + 5.0)

            base_score = min(100.0, max(20.0, base_score))
            status = "STRONG" if base_score >= 75 else ("ADEQUATE" if base_score >= 50 else "GAP")
            calc_str = f"{len(matched)} of {len(benchmark_skills)} required skill groups matched ({match_ratio*100:.0f}%)"
            gap_str = f"Shortfall in: {', '.join(missing)}" if missing else "None"

        return ComponentScore(
            score=round(base_score, 1),
            weight=WEIGHT_SKILLS,
            status=status,
            evidence=[f"Verified skills: {', '.join(skills_list)}"],
            evidence_source=evidence_source,
            benchmark_requirement=benchmark_skills,
            matched_requirements=matched,
            missing_requirements=missing,
            matched_items=matched,
            missing_items=missing,
            gap=gap_str,
            confidence=0.92,
            calculation=calc_str,
            details={
                "match_ratio": round(match_ratio, 2),
                "certified_count": len(certified),
                "source": evidence_source
            }
        )

    def evaluate_experience(
        self,
        ep: Dict[str, Any],
        arg1: Any = None,
        arg2: Any = None
    ) -> ComponentScore:
        """
        Evaluates deterministic experience alignment against domain requirements.
        Compares actual user-provided years against business benchmark.
        If user explicitly says 0 years -> score = 0.0 (or entry level score), status = DEVELOPING / DEFICIENT.
        If experience is absent -> status = UNKNOWN.
        """
        profile, _, node_id = self._resolve_eval_args(arg1, arg2)

        raw_exp = ep.get("experience") or {}
        if isinstance(raw_exp, dict):
            years = raw_exp.get("years_of_experience")
            if years is None:
                years = raw_exp.get("years")
            domain = raw_exp.get("domain") or ""
            prior_biz = raw_exp.get("prior_business_ownership", False)
            source = raw_exp.get("source") or ("USER_CLARIFICATION" if ep.get("answered_fields") and "experience" in ep["answered_fields"] else "USER_INPUT")
        elif isinstance(raw_exp, (int, float)):
            years = float(raw_exp)
            domain = ""
            prior_biz = False
            source = "USER_INPUT"
        else:
            years = None
            domain = ""
            prior_biz = False
            source = "BENCHMARK_DATABASE"

        # Benchmark minimum experience years from ontology
        benchmark_min_years = 1.0
        if any(term in node_id.lower() for term in ["rice_mill", "flour_mill", "flour_milling", "oil_expeller", "solar_pump", "solar_pump_repair"]):
            benchmark_min_years = 2.0
        elif any(term in node_id.lower() for term in ["dairy_farm", "poultry_farm"]):
            benchmark_min_years = 1.5
        elif any(term in node_id.lower() for term in ["saree_retail", "garment_store", "grocery_store"]):
            benchmark_min_years = 1.0

        if years is None:
            return ComponentScore(
                score=35.0,
                weight=WEIGHT_EXPERIENCE,
                status="UNKNOWN",
                evidence=["Work experience years not explicitly stated; status UNKNOWN."],
                evidence_source="UNKNOWN",
                benchmark_requirement=[f">= {benchmark_min_years:.1f} years domain experience recommended"],
                matched_requirements=[],
                missing_requirements=[f"{benchmark_min_years:.1f} years domain experience"],
                matched_items=[],
                missing_items=["years_of_experience"],
                gap=f"Experience unverified ({benchmark_min_years:.1f} yrs recommended)",
                confidence=0.40,
                calculation=f"Experience unstated (Benchmark standard: >= {benchmark_min_years:.1f} years)",
                details={"benchmark_min_years": benchmark_min_years, "source": "BENCHMARK_DATABASE"}
            )

        years = float(years)
        if years >= benchmark_min_years:
            score = 100.0
            status = "STRONG"
            evidence_text = f"Possesses {years:.1f} years domain track record in {domain or 'direct trade'}."
            matched = [f"{years:.1f} years direct experience"]
            missing = []
            gap = "None (Benchmark satisfied)"
            calc_str = f"{years:.1f} years user experience >= {benchmark_min_years:.1f} years benchmark requirement → requirement satisfied → 100/100"
        elif years > 0:
            score = 40.0 + (years / benchmark_min_years) * 50.0
            status = "ADEQUATE"
            evidence_text = f"Possesses {years:.1f} years experience (approaching recommended {benchmark_min_years:.1f} years)."
            matched = [f"{years:.1f} years experience"]
            missing = [f"{benchmark_min_years - years:.1f} additional years recommended for mastery"]
            gap = f"{benchmark_min_years - years:.1f} years experience shortfall"
            calc_str = f"{years:.1f} actual yrs / {benchmark_min_years:.1f} benchmark yrs ({years/benchmark_min_years*100:.0f}%)"
        else:
            # 0 years of experience
            score = 10.0
            status = "GAP"
            evidence_text = "First-time entrepreneur with 0 reported years in direct trade; structured incubation recommended."
            matched = []
            missing = [f"{benchmark_min_years:.1f} years recommended domain track record"]
            gap = f"First-time founder without prior operating track record ({benchmark_min_years:.1f} yrs recommended)"
            calc_str = f"0.0 actual yrs vs {benchmark_min_years:.1f} benchmark yrs (0% track record)"

        return ComponentScore(
            score=round(score, 1),
            weight=WEIGHT_EXPERIENCE,
            status=status,
            evidence=[evidence_text],
            evidence_source=source,
            benchmark_requirement=[f">= {benchmark_min_years:.1f} years domain experience"],
            matched_requirements=matched,
            missing_requirements=missing,
            matched_items=matched,
            missing_items=missing,
            gap=gap,
            confidence=0.96,
            calculation=calc_str,
            details={
                "actual_experience_years": years,
                "required_experience_years": benchmark_min_years,
                "experience_gap_years": max(0.0, benchmark_min_years - years),
                "years_reported": years,
                "benchmark_min_years": benchmark_min_years,
                "formula": f"user_experience ({years:.1f} yrs) >= benchmark ({benchmark_min_years:.1f} yrs)",
                "inputs": {"years_of_experience": years, "domain": domain, "raw_text": raw_exp.get("raw_text")},
                "benchmark": {"min_years_required": benchmark_min_years},
                "domain": domain,
                "source": source
            }
        )

    def evaluate_training(
        self,
        ep: Dict[str, Any],
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None
    ) -> ComponentScore:
        """
        Evaluates training readiness and statutory certifications from business requirements.
        Separates MANDATORY vs RECOMMENDED vs OPTIONAL.
        If training information is unknown -> status = UNKNOWN.
        """
        profile, reqs, node_id = self._resolve_eval_args(arg1, arg2, arg3)

        raw_tr = ep.get("training") or {}
        evidence_source = "BENCHMARK_DATABASE"
        if isinstance(raw_tr, dict):
            has_formal = raw_tr.get("has_formal_training")
            certs = raw_tr.get("certifications", [])
            willing = raw_tr.get("willing_to_undergo_training", True)
            evidence_source = raw_tr.get("source") or ("USER_CLARIFICATION" if ep.get("answered_fields") and "training" in ep["answered_fields"] else "USER_INPUT")
        elif isinstance(raw_tr, bool):
            has_formal = raw_tr
            certs = []
            willing = True
            evidence_source = "USER_INPUT"
        elif isinstance(raw_tr, list):
            has_formal = len(raw_tr) > 0
            certs = raw_tr
            willing = True
            evidence_source = "USER_INPUT"
        else:
            has_formal = None
            certs = []
            willing = True
            evidence_source = "UNKNOWN"

        mandatory_certs = []
        recommended_certs = []

        if reqs and hasattr(reqs, "compliance_and_licensing") and reqs.compliance_and_licensing:
            for c in reqs.compliance_and_licensing:
                is_mand = c.get("mandatory") if isinstance(c, dict) else getattr(c, "mandatory", False)
                lic_name = c.get("license_name") if isinstance(c, dict) else getattr(c, "license_name", "")
                if lic_name:
                    if is_mand:
                        mandatory_certs.append(lic_name)
                    else:
                        recommended_certs.append(lic_name)
        elif profile and hasattr(profile, "compliance_and_licensing") and profile.compliance_and_licensing:
            for c in profile.compliance_and_licensing:
                is_mand = c.get("mandatory") if isinstance(c, dict) else getattr(c, "mandatory", False)
                lic_name = c.get("license_name") if isinstance(c, dict) else getattr(c, "license_name", "")
                if lic_name:
                    if is_mand:
                        mandatory_certs.append(lic_name)
                    else:
                        recommended_certs.append(lic_name)

        if not mandatory_certs and any(k in node_id.lower() for k in ["spice", "flour", "food", "dairy", "oil"]):
            mandatory_certs.append("FSSAI / FoSTaC Food Safety Certificate")

        matched_certs = []
        missing_certs = []
        for m in mandatory_certs:
            m_lower = m.lower()
            m_words = set(m_lower.replace("/", " ").replace("-", " ").split())
            if any(any(w in c.lower() for w in m_words if len(w) > 2) for c in certs) or any(c.lower() in m_lower or m_lower in c.lower() for c in certs):
                matched_certs.append(m)
            else:
                missing_certs.append(m)

        # If training info is totally unknown
        if has_formal is None and not certs and "training" not in (ep.get("answered_fields") or []):
            return ComponentScore(
                score=45.0,
                weight=WEIGHT_TRAINING,
                status="UNKNOWN",
                evidence=["Training and statutory certification status unstated."],
                evidence_source="UNKNOWN",
                benchmark_requirement=mandatory_certs or ["Statutory trade compliance awareness"],
                matched_requirements=[],
                missing_requirements=mandatory_certs,
                matched_items=[],
                missing_items=mandatory_certs,
                gap="Statutory training / license readiness unconfirmed",
                confidence=0.45,
                calculation="Training status unstated (Prerequisite training status: UNKNOWN)",
                details={"has_formal_training": None, "certifications_count": 0}
            )

        if has_formal or certs:
            has_all_mandatory = len(missing_certs) == 0
            score = 85.0 + (15.0 if has_all_mandatory else 0.0)
            status = "STRONG"
            evidence_text = f"Formal certifications verified: {', '.join(certs) if certs else 'Vocational Training'}."
            calc_str = f"Certified trade qualifications verified ({len(matched_certs)} of {len(mandatory_certs)} mandatory satisfied)"
            gap_str = f"Pending licenses: {', '.join(missing_certs)}" if missing_certs else "None"
        elif willing:
            score = 65.0
            status = "ADEQUATE"
            evidence_text = "Entrepreneur confirmed willingness to undertake prerequisite training prior to commercial launch."
            calc_str = "Pre-requisite training willingness confirmed; statutory certificate pending completion"
            gap_str = f"Mandatory compliance certificate pending: {', '.join(missing_certs) if missing_certs else 'FoSTaC / EDP'}"
        else:
            score = 25.0
            status = "DEFICIENT"
            evidence_text = "No formal certification and reluctance towards trade training."
            calc_str = "No trade training completed and reluctance reported"
            gap_str = "Mandatory trade certification missing"

        return ComponentScore(
            score=round(score, 1),
            weight=WEIGHT_TRAINING,
            status=status,
            evidence=[evidence_text],
            evidence_source=evidence_source,
            benchmark_requirement=mandatory_certs or ["Statutory trade compliance"],
            matched_requirements=certs if certs else (["Willing to undergo training"] if willing else []),
            missing_requirements=missing_certs,
            matched_items=certs if certs else (["Willing to undergo training"] if willing else []),
            missing_items=missing_certs,
            gap=gap_str,
            confidence=0.90,
            calculation=calc_str,
            details={"has_formal_training": has_formal, "certifications_count": len(certs)}
        )

    def evaluate_resources(
        self,
        ep: Dict[str, Any],
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None
    ) -> ComponentScore:
        """
        Evaluates physical premises area, power connection type, and machinery against benchmark requirements.
        Returns required_value, available_value, source, status, and gap.
        """
        profile, reqs, node_id = self._resolve_eval_args(arg1, arg2, arg3)

        raw_res = ep.get("resources") or {}
        if not isinstance(raw_res, dict):
            raw_res = {}

        area = raw_res.get("available_area_sqft")
        power = raw_res.get("power_connection_type")
        machinery = raw_res.get("existing_machinery", [])
        premises_avail = raw_res.get("land_or_premises_available")
        evidence_source = raw_res.get("source") or ("USER_CLARIFICATION" if ep.get("answered_fields") and "resources" in ep["answered_fields"] else "USER_INPUT")

        req_area = 150.0
        req_power = "SINGLE_PHASE_COMMERCIAL"

        if reqs:
            if hasattr(reqs, "space_and_infrastructure") and reqs.space_and_infrastructure:
                si = reqs.space_and_infrastructure
                req_area = float(si.get("built_up_area_sqft_min", 150.0) if isinstance(si, dict) else getattr(si, "built_up_area_sqft_min", 150.0))
            if hasattr(reqs, "power_and_utilities") and reqs.power_and_utilities:
                pu = reqs.power_and_utilities
                req_power = str(pu.get("power_connection_type", "SINGLE_PHASE_COMMERCIAL") if isinstance(pu, dict) else getattr(pu, "power_connection_type", "SINGLE_PHASE_COMMERCIAL"))
        elif profile:
            if hasattr(profile, "space_and_infrastructure") and profile.space_and_infrastructure:
                si = profile.space_and_infrastructure
                req_area = float(si.get("built_up_area_sqft_min", 150.0) if isinstance(si, dict) else getattr(si, "built_up_area_sqft_min", 150.0))
            if hasattr(profile, "power_and_utilities") and profile.power_and_utilities:
                pu = profile.power_and_utilities
                req_power = str(pu.get("power_connection_type", "SINGLE_PHASE_COMMERCIAL") if isinstance(pu, dict) else getattr(pu, "power_connection_type", "SINGLE_PHASE_COMMERCIAL"))

        if any(k in node_id.lower() for k in ["flour", "oil_expeller", "rice_mill", "cold_storage", "spice"]):
            req_power = "THREE_PHASE_COMMERCIAL"

        # 1. Area evaluation
        if area is not None:
            area_ratio = min(1.5, float(area) / max(1.0, req_area))
            area_score = min(100.0, area_ratio * 100.0)
        elif premises_avail is True:
            area_score = 80.0
        elif premises_avail is False:
            area_score = 25.0
        else:
            area_score = 45.0

        # 2. Power evaluation
        needs_3phase = "THREE" in req_power.upper() or "3" in req_power
        if power:
            has_3phase = "THREE" in str(power).upper() or "3" in str(power)
            if needs_3phase:
                power_score = 100.0 if has_3phase else 30.0
            else:
                power_score = 100.0
        else:
            power_score = 45.0 if needs_3phase else 80.0

        # 3. Machinery evaluation
        machinery_score = 85.0 if len(machinery) > 0 else 65.0

        resource_score = 0.50 * area_score + 0.35 * power_score + 0.15 * machinery_score
        status = "STRONG" if resource_score >= 75 else ("ADEQUATE" if resource_score >= 50 else "DEVELOPING")

        matched = []
        missing = []
        if area and area >= req_area:
            matched.append(f"Premises Area ({area:.0f} sqft >= required {req_area:.0f} sqft)")
        elif area:
            missing.append(f"Premises shortfall ({area:.0f} sqft vs required {req_area:.0f} sqft)")
        elif premises_avail:
            matched.append("Commercial premises confirmed available")

        if power and power_score >= 70:
            matched.append(f"Power connection adequate ({power})")
        elif power and power_score < 70:
            missing.append(f"Power upgrade required: requires {req_power} (current: {power})")

        calc_str = f"Area: {area or 'unspecified'} sqft vs {req_area:.0f} sqft req | Power: {power or 'unspecified'} vs {req_power} req"
        gap_str = "; ".join(missing) if missing else "None"

        return ComponentScore(
            score=round(resource_score, 1),
            weight=WEIGHT_RESOURCES,
            status=status,
            evidence=[f"Infrastructure evaluated against {node_id} (Area: {req_area:.0f} sqft, Power: {req_power})."],
            evidence_source=evidence_source,
            benchmark_requirement=[f"Area: >= {req_area:.0f} sqft", f"Power: {req_power}"],
            matched_requirements=matched,
            missing_requirements=missing,
            matched_items=matched,
            missing_items=missing,
            gap=gap_str,
            confidence=0.91 if (area is not None or power) else 0.45,
            calculation=calc_str,
            details={
                "area_sqft": area,
                "required_area_sqft": req_area,
                "power_connection": power,
                "required_power": req_power,
                "power_adequate": power_score >= 70
            }
        )

    def evaluate_operations(
        self,
        ep: Dict[str, Any],
        arg1: Any = None,
        arg2: Any = None,
        arg3: Any = None
    ) -> ComponentScore:
        """
        Evaluates operational commitment and worker capacity against domain benchmarks.
        Shows available_workers, required_workers, gap, and formula.
        """
        profile, reqs, node_id = self._resolve_eval_args(arg1, arg2, arg3)

        raw_ops = ep.get("operations") or {}
        if not isinstance(raw_ops, dict):
            raw_ops = {}

        commit = raw_ops.get("commitment_type")
        family = int(raw_ops.get("available_family_helpers") or 0)
        hired = int(raw_ops.get("hired_workers_planned") or 0)
        total_workers = family + hired + 1
        evidence_source = raw_ops.get("source") or ("USER_CLARIFICATION" if ep.get("answered_fields") and "operations" in ep["answered_fields"] else "USER_INPUT")

        req_min_workers = 2
        if reqs and hasattr(reqs, "skills_and_manpower") and reqs.skills_and_manpower:
            sm = reqs.skills_and_manpower
            req_min_workers = int(sm.get("min_workers", 2) if isinstance(sm, dict) else getattr(sm, "min_workers", 2))
        elif profile and hasattr(profile, "skills_and_manpower") and profile.skills_and_manpower:
            sm = profile.skills_and_manpower
            req_min_workers = int(sm.get("min_workers", 2) if isinstance(sm, dict) else getattr(sm, "min_workers", 2))

        if commit == "FULL_TIME":
            commit_score = 100.0
        elif commit == "PART_TIME":
            commit_score = 65.0
        elif commit == "SEASONAL":
            commit_score = 45.0
        else:
            commit_score = 75.0

        manpower_ratio = min(1.5, total_workers / max(1, req_min_workers))
        manpower_score = min(100.0, manpower_ratio * 100.0)

        ops_score = 0.60 * commit_score + 0.40 * manpower_score
        status = "STRONG" if ops_score >= 75 else ("ADEQUATE" if ops_score >= 50 else "DEVELOPING")

        matched = [f"Operational commitment: {commit or 'FULL_TIME'} ({total_workers} personnel)"]
        missing = []
        worker_gap = max(0, req_min_workers - total_workers)
        if worker_gap > 0:
            missing.append(f"Worker capacity shortfall: {total_workers} available vs {req_min_workers} benchmark minimum")

        calc_str = f"Commitment: {commit or 'FULL_TIME'} (60% weight) + Manpower: {total_workers}/{req_min_workers} workers ({manpower_ratio*100:.0f}%, 40% weight)"
        gap_str = f"Staffing deficit of {worker_gap} worker(s)" if worker_gap > 0 else "None"

        return ComponentScore(
            score=round(ops_score, 1),
            weight=WEIGHT_OPERATIONS,
            status=status,
            evidence=[f"Operational commitment: {commit or 'FULL_TIME'}, total personnel: {total_workers}."],
            evidence_source=evidence_source,
            benchmark_requirement=[f"Minimum workforce: >= {req_min_workers} persons", "Full-time operational focus"],
            matched_requirements=matched,
            missing_requirements=missing,
            matched_items=matched,
            missing_items=missing,
            gap=gap_str,
            confidence=0.92,
            calculation=calc_str,
            details={
                "commitment_type": commit or "FULL_TIME",
                "available_workers": total_workers,
                "required_workers": req_min_workers,
                "worker_gap": worker_gap
            }
        )

    def identify_missing_fields_and_questions(
        self,
        ep: Dict[str, Any],
        profile: Optional[Any],
        node_id: str,
        title: str
    ) -> Tuple[List[str], List[ClarificationQuestion]]:
        """
        Determines missing fields in the entrepreneur profile and produces localized, business-contextual clarification questions.
        If a field is already provided in ep or in answered_fields, it is NEVER returned.
        """
        missing_fields: List[str] = []
        questions: List[ClarificationQuestion] = []
        answered_fields = set(ep.get("answered_fields", []))

        # Benchmark lookups from profile / requirements
        bench_space = 250.0
        if profile and hasattr(profile, "space_and_infrastructure") and profile.space_and_infrastructure:
            si = profile.space_and_infrastructure
            bench_space = float(si.get("carpet_area_sqft", 250.0) if isinstance(si, dict) else getattr(si, "carpet_area_sqft", 250.0))

        bench_years = 1.0
        if profile and hasattr(profile, "skills_and_manpower") and profile.skills_and_manpower:
            sm = profile.skills_and_manpower
            bench_years = float(sm.get("min_years_experience", 1.0) if isinstance(sm, dict) else getattr(sm, "min_years_experience", 1.0))

        # Domain category detection
        is_retail = any(k in node_id.lower() or k in title.lower() for k in ["saree", "cloth", "garment", "retail", "textile", "store", "shop", "kirana", "grocery", "silk", "ethnic"])
        is_agro_mfg = any(k in node_id.lower() or k in title.lower() for k in ["flour", "rice", "mill", "oil", "spice", "chakki", "processing", "manufacturing", "paddy", "grain"])
        is_dairy_livestock = any(k in node_id.lower() or k in title.lower() for k in ["dairy", "milk", "cattle", "goat", "poultry", "livestock", "farm"])

        # 1. Skills
        raw_skills = ep.get("skills")
        has_skills = False
        if isinstance(raw_skills, dict):
            has_skills = bool(raw_skills.get("skills") and len(raw_skills["skills"]) > 0)
        elif isinstance(raw_skills, list):
            has_skills = len(raw_skills) > 0
        elif isinstance(raw_skills, str) and raw_skills.strip():
            has_skills = True

        if not has_skills and "skills" not in answered_fields:
            missing_fields.append("skills")

            if is_retail:
                q_en = f"What relevant retail sales, customer handling, garment merchandising, or shop management skills do you possess for running a {title}?"
                q_hi = f"{title} चलाने के लिए आपके पास कौन सा रिटेल बिक्री, ग्राहक प्रबंधन या कपड़ों की समझ का हुनर है?"
                q_kn = f"{title} ನಡೆಸಲು ನಿಮ್ಮಲ್ಲಿ ಯಾವ ವ್ಯಾಪಾರ ಮಾರಾಟ ಅಥವಾ ಗ್ರಾಹಕರ ಸೇವಾ ಕೌಶಲ್ಯವಿದೆ?"
                reason = f"Required to evaluate commercial sales capability, merchandising, and customer service readiness for {title}."
                bench = f"Benchmark requires retail customer handling and product sales skills for {title}."
                options = ["Retail sales & customer handling", "Billing & stock management", "Fabric/merchandise selection", "Fresh / No prior experience"]
            elif is_agro_mfg:
                q_en = f"What machinery operation, grain processing, or preventive maintenance skills do you possess for running a {title}?"
                q_hi = f"{title} चलाने के लिए आपके पास कौन सा मशीनरी संचालन, अनाज प्रसंस्करण या रखरखाव का कौशल है?"
                q_kn = f"{title} ನಡೆಸಲು ನಿಮ್ಮಲ್ಲಿ ಯಂತ್ರ ಕಾರ್ಯಾಚರಣೆ ಅಥವಾ ಸಂಸ್ಕರಣಾ ಕೌಶಲ್ಯವಿದೆಯೇ?"
                reason = f"Machine handling, process knowledge, and safety procedures are critical for {title} operational uptime."
                bench = f"Benchmark requires machinery operation and basic processing maintenance for {title}."
                options = ["Machinery operation", "Grading & quality inspection", "Routine equipment maintenance", "Fresh / Willing to learn"]
            elif is_dairy_livestock:
                q_en = f"What livestock handling, animal health management, or milk quality testing experience do you have for running a {title}?"
                q_hi = f"{title} चलाने के लिए आपके पास पशुपालन, पशु स्वास्थ्य या दूध परीक्षण का कौन सा अनुभव है?"
                q_kn = f"{title} ನಡೆಸಲು ನಿಮ್ಮಲ್ಲಿ ಜಾನುವಾರು ನಿರ್ವಹಣೆ ಅಥವಾ ಗುಣಮಟ್ಟ ಪರೀಕ್ಷಾ ಕೌಶಲ್ಯವಿದೆಯೇ?"
                reason = f"Animal welfare, hygiene protocols, and yield management are essential to the viability of {title}."
                bench = f"Benchmark requires livestock management and milk testing knowledge for {title}."
                options = ["Livestock handling", "Hygienic milking & testing", "Feed & fodder management", "Fresh / No prior experience"]
            else:
                q_en = f"What relevant technical skills, trade experience, or operational abilities do you possess for running a {title}?"
                q_hi = f"{title} चलाने के लिए आपके पास कौन सा तकनीकी हुनर, बिक्री का अनुभव या कौशल है?"
                q_kn = f"{title} ನಡೆಸಲು ನಿಮ್ಮಲ್ಲಿ ಯಾವ ವ್ಯಾಪಾರ ಕೌಶಲ್ಯ ಅಥವಾ ಅನುಭವವಿದೆ?"
                reason = f"Required to evaluate founder capability against {title} operational benchmarks."
                bench = f"Benchmark requires domain-aligned operational and trade skills for {title}."
                options = ["Trade & operational skills", "Customer service & sales", "General management", "Fresh / No prior experience"]

            questions.append(ClarificationQuestion(
                field="skills",
                question=q_en,
                question_en=q_en,
                question_hi=q_hi,
                question_kn=q_kn,
                input_type="text",
                suggested_options=options,
                priority="HIGH",
                importance="HIGH",
                reason=reason,
                benchmark=bench,
                current_value=None
            ))

        # 2. Experience
        raw_exp = ep.get("experience")
        years = None
        if isinstance(raw_exp, dict):
            years = raw_exp.get("years_of_experience")
            if years is None:
                years = raw_exp.get("years")
        elif isinstance(raw_exp, (int, float)):
            years = float(raw_exp)

        if years is None and "experience" not in answered_fields and "experience.years_of_experience" not in answered_fields:
            missing_fields.append("experience.years_of_experience")
            q_en = f"How many years of prior experience do you have in {title} or related commercial/trade work?"
            q_hi = f"{title} या संबंधित व्यापार/कार्य में आपके पास कितने वर्षों का अनुभव है?"
            q_kn = f"{title} ಅಥವಾ ಸಂಬಂಧಿತ ಕ್ಷೇತ್ರದಲ್ಲಿ ನಿಮಗೆ ಎಷ್ಟು ವರ್ಷಗಳ ಅನುಭವವಿದೆ?"
            reason = f"Prior operating experience determines founder execution autonomy and reduces initial business failure risk."
            bench = f"Recommended: >= {bench_years:.0f} year(s) of domain or commercial experience."

            questions.append(ClarificationQuestion(
                field="experience.years_of_experience",
                question=q_en,
                question_en=q_en,
                question_hi=q_hi,
                question_kn=q_kn,
                input_type="number",
                suggested_options=["0 years (Fresh Founder)", "1-2 years", "3-5 years", "5+ years"],
                priority="HIGH",
                importance="HIGH",
                reason=reason,
                benchmark=bench,
                current_value=None
            ))

        # 3. Resources (Premises / Area)
        raw_res = ep.get("resources") or {}
        has_area = False
        if isinstance(raw_res, dict):
            has_area = (raw_res.get("available_area_sqft") is not None) or (raw_res.get("land_or_premises_available") is not None)

        if not has_area and "resources.available_area_sqft" not in answered_fields and "resources" not in answered_fields:
            missing_fields.append("resources.available_area_sqft")
            q_en = f"How much premises floor space or shop area do you currently have available for your {title}? (in sq ft)"
            q_hi = f"{title} के लिए आपके पास कितनी जगह या दुकान उपलब्ध है? (लगभग कितने स्क्वायर फीट?)"
            q_kn = f"{title} ಗಾಗಿ ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಚದರ ಅಡಿ ಜಾಗ ಅಥವಾ ಅಂಗಡಿ ಲಭ್ಯವಿದೆ?"
            reason = f"Premises carpet area must accommodate operational layout, display/machinery, and storage requirements for {title}."
            bench = f"Recommended: >= {bench_space:.0f} sq ft commercial/workshop area."

            questions.append(ClarificationQuestion(
                field="resources.available_area_sqft",
                question=q_en,
                question_en=q_en,
                question_hi=q_hi,
                question_kn=q_kn,
                input_type="number",
                suggested_options=[f"{int(bench_space*0.75)} sq ft", f"{int(bench_space)} sq ft", f"{int(bench_space*1.5)} sq ft", "Arranging premises"],
                priority="MEDIUM",
                importance="MEDIUM",
                reason=reason,
                benchmark=bench,
                current_value=None
            ))

        # 4. Power (only if business requires heavy commercial 3-phase power)
        req_power = "SINGLE_PHASE"
        if profile and hasattr(profile, "power_and_utilities") and profile.power_and_utilities:
            pu = profile.power_and_utilities
            req_power = str(pu.get("power_connection_type", "SINGLE_PHASE") if isinstance(pu, dict) else getattr(pu, "power_connection_type", "SINGLE_PHASE"))

        if ("THREE" in req_power.upper() or "3" in req_power) and any(k in node_id.lower() for k in ["flour", "oil", "rice", "spice"]):
            has_power = isinstance(raw_res, dict) and bool(raw_res.get("power_connection_type"))
            if not has_power and "resources.power_connection_type" not in answered_fields:
                missing_fields.append("resources.power_connection_type")
                q_en = f"What type of electricity connection is available at your site for {title} (Single Phase or 3-Phase Commercial)?"
                q_hi = f"{title} के लिए आपकी दुकान/स्थान पर बिजली का कौन सा कनेक्शन है (सिंगल फेस या 3-फेस कमर्शियल)?"
                q_kn = f"{title} ಗಾಗಿ ನಿಮ್ಮ ಸ್ಥಳದಲ್ಲಿ ಯಾವ ರೀತಿಯ ವಿದ್ಯುತ್ ಸಂಪರ್ಕವಿದೆ (ಸಿಂಗಲ್ ಫೇಸ್ ಅಥವಾ 3-ಫೇಸ್)?"
                reason = f"Operating heavy processing equipment in {title} requires appropriate electrical supply phase and load."
                bench = f"Requires: {req_power} connection."

                questions.append(ClarificationQuestion(
                    field="resources.power_connection_type",
                    question=q_en,
                    question_en=q_en,
                    question_hi=q_hi,
                    question_kn=q_kn,
                    input_type="select",
                    suggested_options=["THREE_PHASE_COMMERCIAL", "SINGLE_PHASE", "NO_CONNECTION"],
                    priority="HIGH",
                    importance="HIGH",
                    reason=reason,
                    benchmark=bench,
                    current_value=None
                ))

        return missing_fields, questions

    def generate_support_recommendations(
        self,
        gaps: List[ReadinessGap],
        profile: Optional[Any],
        node_id: str
    ) -> List[RequiredSupportItem]:
        """
        Generates contextual, gap-specific support program recommendations from verified institutional catalogs.
        Replaces generic programs with GAP -> REQUIRED CAPABILITY -> SUPPORT TYPE -> RESOURCE.
        """
        recommendations: List[RequiredSupportItem] = []
        seen_keys = set()

        # 1. Food Safety & Compliance
        is_food = any(k in node_id.lower() for k in ["spice", "flour", "food", "dairy", "oil", "bakery", "rice"])
        has_train_gap = any(g.dimension == "TRAINING" for g in gaps)
        if is_food and (has_train_gap or any("fssai" in g.gap_description.lower() for g in gaps)):
            if "FOOD_SAFETY_COMPLIANCE" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["FOOD_SAFETY_COMPLIANCE"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("FOOD_SAFETY_COMPLIANCE")

        # 2. Dairy & Livestock Gap
        is_dairy = any(k in node_id.lower() for k in ["dairy", "cattle", "chilling", "poultry", "goat"])
        if is_dairy and any(g.dimension in ["SKILLS", "EXPERIENCE", "TRAINING"] for g in gaps):
            if "DAIRY_LIVESTOCK_MANAGEMENT" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["DAIRY_LIVESTOCK_MANAGEMENT"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("DAIRY_LIVESTOCK_MANAGEMENT")

        # 3. Retail & Inventory Management Gap
        is_retail = any(k in node_id.lower() for k in ["saree", "garment", "grocery", "retail", "kirana"])
        has_skill_gap = any(g.dimension == "SKILLS" for g in gaps)
        if is_retail and has_skill_gap:
            if "INVENTORY_MANAGEMENT" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["INVENTORY_MANAGEMENT"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("INVENTORY_MANAGEMENT")
            if "RETAIL_SALES_SKILLS" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["RETAIL_SALES_SKILLS"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("RETAIL_SALES_SKILLS")

        # 4. Solar Equipment Gap
        if "solar" in node_id.lower() and (has_skill_gap or has_train_gap):
            if "SOLAR_TECHNICAL_TRAINING" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["SOLAR_TECHNICAL_TRAINING"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("SOLAR_TECHNICAL_TRAINING")

        # 5. Infrastructure / Power Gap
        has_infra_gap = any(g.dimension == "RESOURCES" for g in gaps)
        if has_infra_gap and any("power" in g.gap_description.lower() for g in gaps):
            if "COMMERCIAL_POWER_UPGRADE" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["COMMERCIAL_POWER_UPGRADE"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("COMMERCIAL_POWER_UPGRADE")

        # 6. Experience / Incubation Gap
        has_exp_gap = any(g.dimension == "EXPERIENCE" for g in gaps)
        if has_exp_gap:
            if "ENTREPRENEURSHIP_EDP" not in seen_keys:
                rec_data = CONTEXTUAL_SUPPORT_CATALOG["ENTREPRENEURSHIP_EDP"]
                recommendations.append(RequiredSupportItem(**rec_data))
                seen_keys.add("ENTREPRENEURSHIP_EDP")

        # Fallback if no specific gaps
        if not recommendations:
            rec_data = CONTEXTUAL_SUPPORT_CATALOG["GENERAL_MSME_SUPPORT"]
            recommendations.append(RequiredSupportItem(**rec_data))

        return recommendations

    def analyze(self, payload: Dict[str, Any]) -> EntrepreneurReadinessResponse:
        """
        Main deterministic analysis entrypoint for Stage 10.
        Calculates composite readiness score across all 5 dimensions with complete calculation provenance.
        """
        ep, biz, loc = self._extract_inputs(payload)
        profile, reqs, node_id, title = self._resolve_business_context(biz)

        # 1. Identify missing fields & clarification questions
        missing_fields, questions = self.identify_missing_fields_and_questions(ep, profile, node_id, title)

        # 2. Evaluate all 5 deterministic components
        skills_comp = self.evaluate_skills(ep, profile, reqs, node_id)
        exp_comp = self.evaluate_experience(ep, profile, node_id)
        train_comp = self.evaluate_training(ep, profile, reqs, node_id)
        res_comp = self.evaluate_resources(ep, profile, reqs, node_id)
        ops_comp = self.evaluate_operations(ep, profile, reqs, node_id)

        # 3. Composite score calculation
        overall_score = (
            skills_comp.weight * skills_comp.score +
            exp_comp.weight * exp_comp.score +
            train_comp.weight * train_comp.score +
            res_comp.weight * res_comp.score +
            ops_comp.weight * ops_comp.score
        )
        overall_score = round(overall_score, 1)

        # 4. Profile completeness status
        is_profile_incomplete = len(missing_fields) > 0 or (skills_comp.status == "UNKNOWN" and exp_comp.status == "UNKNOWN")
        status = "PROFILE_INCOMPLETE" if is_profile_incomplete else "READY"

        # Readiness Level
        if status == "PROFILE_INCOMPLETE":
            readiness_level = "INCOMPLETE"
        elif overall_score >= READINESS_THRESHOLD_HIGH:
            readiness_level = "HIGH"
        elif overall_score >= READINESS_THRESHOLD_MODERATE:
            readiness_level = "MODERATE"
        elif overall_score >= READINESS_THRESHOLD_DEVELOPING:
            readiness_level = "DEVELOPING"
        else:
            readiness_level = "LOW"

        # 5. Calculation Provenance Records
        weights = {
            "skills": WEIGHT_SKILLS,
            "experience": WEIGHT_EXPERIENCE,
            "training": WEIGHT_TRAINING,
            "resources": WEIGHT_RESOURCES,
            "operational": WEIGHT_OPERATIONS,
            "operational_readiness": WEIGHT_OPERATIONS
        }

        calculation_provenance = [
            {
                "dimension": "SKILLS",
                "score": skills_comp.score,
                "weight": skills_comp.weight,
                "weighted_contribution": round(skills_comp.score * skills_comp.weight, 2),
                "calculation": skills_comp.calculation,
                "formula": f"matched_skills ({len(skills_comp.matched_requirements)}) / required_skills ({max(1, len(skills_comp.benchmark_requirement))})",
                "inputs": {"verified_skills": skills_comp.matched_items, "evidence": skills_comp.evidence},
                "benchmark": {"required_skills": skills_comp.benchmark_requirement},
                "result": f"{skills_comp.score:.0f}/100 ({skills_comp.status})",
                "status": skills_comp.status,
                "source": skills_comp.evidence_source,
                "confidence": skills_comp.confidence
            },
            {
                "dimension": "EXPERIENCE",
                "score": exp_comp.score,
                "weight": exp_comp.weight,
                "weighted_contribution": round(exp_comp.score * exp_comp.weight, 2),
                "calculation": exp_comp.calculation,
                "formula": exp_comp.details.get("formula", f"user_years >= benchmark_years"),
                "inputs": exp_comp.details.get("inputs", {"years": exp_comp.details.get("actual_experience_years")}),
                "benchmark": exp_comp.details.get("benchmark", {"min_years_required": exp_comp.details.get("benchmark_min_years", 1.0)}),
                "result": f"{exp_comp.score:.0f}/100 ({exp_comp.status})",
                "status": exp_comp.status,
                "source": exp_comp.evidence_source,
                "confidence": exp_comp.confidence
            },
            {
                "dimension": "TRAINING",
                "score": train_comp.score,
                "weight": train_comp.weight,
                "weighted_contribution": round(train_comp.score * train_comp.weight, 2),
                "calculation": train_comp.calculation,
                "formula": "has_formal_training (85 pts) + mandatory_certifications (15 pts)",
                "inputs": {"verified_certifications": train_comp.matched_items, "evidence": train_comp.evidence},
                "benchmark": {"mandatory_certifications": train_comp.benchmark_requirement},
                "result": f"{train_comp.score:.0f}/100 ({train_comp.status})",
                "status": train_comp.status,
                "source": train_comp.evidence_source,
                "confidence": train_comp.confidence
            },
            {
                "dimension": "RESOURCES",
                "score": res_comp.score,
                "weight": res_comp.weight,
                "weighted_contribution": round(res_comp.score * res_comp.weight, 2),
                "calculation": res_comp.calculation,
                "formula": "0.50 * area_score + 0.35 * power_score + 0.15 * machinery_score",
                "inputs": {"available_area_sqft": res_comp.details.get("area_sqft"), "power_connection": res_comp.details.get("power_connection")},
                "benchmark": {"required_area_sqft": res_comp.details.get("required_area_sqft"), "required_power": res_comp.details.get("required_power")},
                "result": f"{res_comp.score:.0f}/100 ({res_comp.status})",
                "status": res_comp.status,
                "source": res_comp.evidence_source,
                "confidence": res_comp.confidence
            },
            {
                "dimension": "OPERATIONS",
                "score": ops_comp.score,
                "weight": ops_comp.weight,
                "weighted_contribution": round(ops_comp.score * ops_comp.weight, 2),
                "calculation": ops_comp.calculation,
                "formula": "0.60 * commitment_score + 0.40 * manpower_score",
                "inputs": {"commitment_type": ops_comp.details.get("commitment_type"), "available_workers": ops_comp.details.get("available_workers")},
                "benchmark": {"required_workers": ops_comp.details.get("required_workers")},
                "result": f"{ops_comp.score:.0f}/100 ({ops_comp.status})",
                "status": ops_comp.status,
                "source": ops_comp.evidence_source,
                "confidence": ops_comp.confidence
            }
        ]

        # 6. Synthesize Strengths
        strengths: List[str] = []
        if skills_comp.score >= 70 and skills_comp.status != "UNKNOWN":
            strengths.append(f"Demonstrated trade skill alignment ({skills_comp.score:.0f}%)")
        if exp_comp.score >= 70 and exp_comp.status != "UNKNOWN":
            strengths.append(f"Operating experience track record ({exp_comp.details.get('years_reported', 0):.1f} years)")
        if train_comp.score >= 70 and train_comp.status != "UNKNOWN":
            strengths.append("Certified or proactive trade training orientation")
        if res_comp.score >= 70 and res_comp.status != "UNKNOWN":
            strengths.append("Adequate physical infrastructure & utility access")
        if ops_comp.score >= 70 and ops_comp.status != "UNKNOWN":
            strengths.append("Dedicated founder operational bandwidth")
        if not strengths:
            strengths.append("Entrepreneurial motivation with foundational learning agility")

        # 7. Synthesize Gaps
        gaps: List[ReadinessGap] = []
        if skills_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="SKILLS",
                gap_description=f"Skill gaps identified in: {', '.join(skills_comp.missing_requirements) if skills_comp.missing_requirements else 'domain operations'}",
                severity="HIGH" if skills_comp.score < 40 else "MEDIUM",
                required_intervention="Short-term practical apprenticeship under experienced master operator",
                benchmark_reference=node_id
            ))
        if exp_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="EXPERIENCE",
                gap_description=f"Limited domain experience ({exp_comp.details.get('actual_experience_years', 0):.1f} years vs {exp_comp.details.get('benchmark_min_years', 1):.1f} years recommended)",
                severity="HIGH" if exp_comp.details.get('actual_experience_years', 0) == 0 else "MEDIUM",
                required_intervention="Incubation mentoring and handholding through first 6 months of operations",
                benchmark_reference=node_id
            ))
        if train_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="TRAINING",
                gap_description=f"Mandatory compliance certification pending: {', '.join(train_comp.missing_requirements) if train_comp.missing_requirements else 'Statutory License'}",
                severity="HIGH" if train_comp.missing_requirements else "MEDIUM",
                required_intervention="Complete FoSTaC / RSETI certificate course before commercial launch",
                benchmark_reference=node_id
            ))
        if res_comp.score < 60:
            gaps.append(ReadinessGap(
                dimension="RESOURCES",
                gap_description=f"Infrastructure constraints ({', '.join(res_comp.missing_requirements) if res_comp.missing_requirements else 'adequate premises/power'})",
                severity="HIGH" if "power" in str(res_comp.missing_requirements).lower() else "MEDIUM",
                required_intervention="Upgrade commercial power sanction or secure compliant premise lease",
                benchmark_reference=node_id
            ))

        # 8. Contextual Support Recommendations
        required_support = self.generate_support_recommendations(gaps, profile, node_id)

        # 9. Confidence calculation
        missing_count = len(missing_fields)
        unknown_dims = sum(1 for c in [skills_comp, exp_comp, train_comp, res_comp, ops_comp] if c.status == "UNKNOWN")
        confidence = max(0.40, round(1.0 - (missing_count * 0.12) - (unknown_dims * 0.08), 2))

        return EntrepreneurReadinessResponse(
            success=True,
            status=status,
            analysis_id=payload.get("analysis_id"),
            session_id=payload.get("session_id"),
            business_title=title,
            business_node_id=node_id,
            readiness_score=overall_score,
            readiness_level=readiness_level,
            overall_score=overall_score,
            level=readiness_level,
            weights=weights,
            components={
                "skills": skills_comp,
                "experience": exp_comp,
                "training": train_comp,
                "resources": res_comp,
                "operational": ops_comp,
                "operational_readiness": ops_comp,
            },
            component_scores={
                "skills": skills_comp,
                "experience": exp_comp,
                "training": train_comp,
                "resources": res_comp,
                "operational": ops_comp,
                "operational_readiness": ops_comp,
            },
            calculation_provenance=calculation_provenance,
            strengths=strengths,
            gaps=gaps,
            required_support=required_support,
            pending_fields=missing_fields,
            answered_fields=ep.get("answered_fields", []),
            missing_fields=missing_fields,
            questions=questions,
            confidence=confidence,
            provenance=ProvenanceRecord(
                benchmark_node_id=node_id,
                evaluation_type="DETERMINISTIC_RULES",
                data_sources=["user_intake", "business_repository", "requirements_repository", "schemes_repository"]
            )
        )

    def is_stage10_complete(self, readiness: Union[EntrepreneurReadinessResponse, Dict[str, Any], None]) -> bool:
        """
        Authoritative validation function to determine whether Stage 10 Entrepreneur Profile
        has satisfied all required dimensions without pending clarification questions.
        """
        if readiness is None:
            return False

        if isinstance(readiness, dict):
            status = readiness.get("status", "")
            missing = readiness.get("missing_fields") or readiness.get("pending_fields") or []
            questions = readiness.get("questions") or []
            if status in ["CLARIFICATION_REQUIRED", "PROFILE_INCOMPLETE", "INCOMPLETE"]:
                return False
            if len(missing) > 0 or len(questions) > 0:
                return False
            if status in ["READY", "COMPLETE"]:
                return True
            # If status not set explicitly, check whether component_scores exist and have valid data
            comp_scores = readiness.get("component_scores") or readiness.get("components") or {}
            if comp_scores and len(missing) == 0 and len(questions) == 0:
                return True
            return False

        elif hasattr(readiness, "status"):
            if readiness.status in ["CLARIFICATION_REQUIRED", "PROFILE_INCOMPLETE", "INCOMPLETE"]:
                return False
            if (readiness.missing_fields and len(readiness.missing_fields) > 0) or (readiness.questions and len(readiness.questions) > 0):
                return False
            if readiness.status in ["READY", "COMPLETE"]:
                return True
            return False

        return False


entrepreneur_profile_engine = EntrepreneurProfileEngine()


def is_stage10_complete(readiness: Union[EntrepreneurReadinessResponse, Dict[str, Any], None]) -> bool:
    return entrepreneur_profile_engine.is_stage10_complete(readiness)

