"""
Stage 14.3: DPR Narrative Generator.
Orchestrates section-by-section institutional drafting with Sarvam AI,
automatic retry on validation failure, deterministic fallback templates,
and persistent semantic isolation caching.
"""
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from app.dpr.stage14_3.document_schema import (
    NarrativePlan,
    SectionNarrative,
    NarrativeProviderMetadata,
    NarrativeValidationResult,
)
from app.dpr.stage14_3.sarvam_service import SarvamDPRNarrativeService, PROMPT_VERSION
from app.dpr.stage14_3.narrative_planner import DPRNarrativePlanner
from app.dpr.stage14_3.narrative_validator import DPRNarrativeValidator

logger = logging.getLogger(__name__)


class NarrativeCache:
    """
    Isolated cache for validated section narratives.
    Strictly keyed by business_id, scenario_id, package hash, section_id, language, prompt_version, model.
    """

    def __init__(self):
        self._store: Dict[str, SectionNarrative] = {}

    def _make_key(
        self,
        business_id: str,
        scenario_id: str,
        source_hash: str,
        section_id: str,
        language: str,
        prompt_version: str,
        model: str
    ) -> str:
        return f"{business_id.strip().lower()}:{scenario_id.strip()}:{source_hash[:12]}:{section_id}:{language}:{prompt_version}:{model}"

    def get(
        self,
        business_id: str,
        scenario_id: str,
        source_hash: str,
        section_id: str,
        language: str = "en",
        prompt_version: str = PROMPT_VERSION,
        model: str = "sarvam-105b-conversations"
    ) -> Optional[SectionNarrative]:
        key = self._make_key(business_id, scenario_id, source_hash, section_id, language, prompt_version, model)
        return self._store.get(key)

    def set(
        self,
        business_id: str,
        scenario_id: str,
        source_hash: str,
        section_id: str,
        narrative: SectionNarrative,
        language: str = "en",
        prompt_version: str = PROMPT_VERSION,
        model: str = "sarvam-105b-conversations"
    ):
        key = self._make_key(business_id, scenario_id, source_hash, section_id, language, prompt_version, model)
        self._store[key] = narrative

    def invalidate_business(self, business_id: str, scenario_id: Optional[str] = None):
        b_clean = business_id.strip().lower()
        to_del = []
        for k in self._store.keys():
            if k.startswith(b_clean + ":"):
                if not scenario_id or f":{scenario_id.strip()}:" in k:
                    to_del.append(k)
        for k in to_del:
            self._store.pop(k, None)


narrative_cache = NarrativeCache()


class DPRNarrativeGenerator:
    """
    Generates validated institutional credit-appraisal prose for DPR sections.
    """

    def __init__(
        self,
        sarvam_service: Optional[SarvamDPRNarrativeService] = None,
        planner: Optional[DPRNarrativePlanner] = None,
        validator: Optional[DPRNarrativeValidator] = None
    ):
        self.sarvam = sarvam_service or SarvamDPRNarrativeService()
        self.planner = planner or DPRNarrativePlanner(self.sarvam)
        self.validator = validator or DPRNarrativeValidator()
        self.cache = narrative_cache

    def compute_package_hash(self, source_data: Dict[str, Any]) -> str:
        s = json.dumps(source_data, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    async def generate_section(
        self,
        section_id: str,
        section_title: str,
        business_id: str,
        scenario_id: str,
        source_data: Dict[str, Any],
        language: str = "en",
        archetype: str = "GENERAL",
        force_regenerate: bool = False
    ) -> SectionNarrative:
        pkg_hash = self.compute_package_hash(source_data)

        # 1. Check cache
        if not force_regenerate:
            cached = self.cache.get(
                business_id=business_id,
                scenario_id=scenario_id,
                source_hash=pkg_hash,
                section_id=section_id,
                language=language,
                prompt_version=PROMPT_VERSION,
                model=self.sarvam.model
            )
            if cached:
                return cached

        # 2. Step A: Narrative Planning
        plan = await self.planner.plan_section(
            section_id=section_id,
            section_title=section_title,
            source_data=source_data,
            language=language,
            business_id=business_id,
            scenario_id=scenario_id
        )

        # 3. Step B: Drafting with Sarvam AI & Validation (up to 2 attempts)
        narrative: Optional[SectionNarrative] = None
        if self.sarvam.is_configured:
            for attempt in range(1, 3):
                draft = await self.sarvam.draft_section_narrative(
                    section_id=section_id,
                    section_title=section_title,
                    plan=plan,
                    source_data=source_data,
                    language=language,
                    business_id=business_id,
                    scenario_id=scenario_id
                )
                if draft:
                    val_res = self.validator.validate_narrative(draft, source_data, section_id)
                    if val_res.is_valid:
                        draft.provider_metadata.retry_count = attempt - 1
                        draft.status = "VALIDATED"
                        self.cache.set(
                            business_id=business_id,
                            scenario_id=scenario_id,
                            source_hash=pkg_hash,
                            section_id=section_id,
                            narrative=draft,
                            language=language,
                            prompt_version=PROMPT_VERSION,
                            model=self.sarvam.model
                        )
                        return draft
                    else:
                        logger.warning(
                            f"[DPRNarrativeGenerator] Validation failed for {section_id} (attempt {attempt}): {val_res.error_details}"
                        )

        # 4. Deterministic Fallback if Sarvam is unavailable or validation failed
        fallback_narrative = self.build_deterministic_fallback(
            section_id=section_id,
            section_title=section_title,
            source_data=source_data,
            archetype=archetype,
            language=language
        )
        self.cache.set(
            business_id=business_id,
            scenario_id=scenario_id,
            source_hash=pkg_hash,
            section_id=section_id,
            narrative=fallback_narrative,
            language=language,
            prompt_version=PROMPT_VERSION,
            model=self.sarvam.model
        )
        return fallback_narrative

    def build_deterministic_fallback(
        self,
        section_id: str,
        section_title: str,
        source_data: Dict[str, Any],
        archetype: str = "GENERAL",
        language: str = "en"
    ) -> SectionNarrative:
        """
        Creates institutional-grade deterministic narrative template.
        Uses exact placeholders {{PROJECT_COST}}, {{TERM_LOAN}}, etc.
        """
        biz_name = source_data.get("business_name") or "the proposed enterprise"
        biz_activity = source_data.get("business_activity") or "commercial operations"
        promoter = source_data.get("promoter_name") or "the promoter"
        raw_loc = str(source_data.get("location") or "")
        if not raw_loc or "gps" in raw_loc.lower() or "current location" in raw_loc.lower():
            location = "the proposed project site"
        else:
            location = raw_loc

        raw_dist = str(source_data.get("district") or "")
        if not raw_dist or "gps" in raw_dist.lower() or "current location" in raw_dist.lower():
            catchment = "the target project catchment"
        else:
            catchment = raw_dist

        constitution = source_data.get("constitution") or "Proprietorship"

        paragraphs: List[str] = []

        if section_id == "executive_summary":
            paragraphs = [
                f"This Detailed Project Report presents the techno-economic appraisal for {biz_name}, "
                f"promoted by {promoter} as a {constitution}. The enterprise proposes to undertake {biz_activity} "
                f"at {location}.",
                "The total capital outlay for the project is estimated at {{PROJECT_COST}}, proposed to be financed "
                "through promoter margin contribution of {{PROMOTER_CONTRIBUTION}} and a bank term loan facility of {{TERM_LOAN}}, "
                "supplemented by working capital credit of {{WORKING_CAPITAL}}.",
                "Projected commercial performance indicates Year-1 revenue of {{YEAR1_REVENUE}}, scaling to {{YEAR5_REVENUE}} "
                "at full capacity utilization, with an operating EBITDA margin of {{EBITDA_MARGIN}} and projected PAT of {{PAT}}. "
                "Debt servicing capability is robust with an Average Debt Service Coverage Ratio (DSCR) of {{AVERAGE_DSCR}} "
                "(minimum {{MIN_DSCR}}) and break-even capacity utilization of {{BREAK_EVEN}}.",
                "Based on the techno-economic parameters, market catchment demand, and conservative financial projections, "
                "the project demonstrates strong technical feasibility and commercial viability for institutional credit appraisal."
            ]
        elif section_id == "promoter_profile":
            exp = source_data.get("experience_years")
            exp_str = f"with approximately {exp} years of relevant domain experience" if exp else "with demonstrated managerial readiness"
            edu = source_data.get("education") or "formal education"
            paragraphs = [
                f"The promoter, {promoter}, possesses {edu} background {exp_str} in the sector. "
                "The promoter brings direct operational familiarity with local supply channels and target customer demand.",
                f"The enterprise is constituted as a {constitution}, ensuring unified managerial accountability and direct "
                "operational oversight over daily production, procurement, and financial stewardship."
            ]
        elif section_id == "business_description":
            paragraphs = [
                f"{biz_name} is conceived to establish an efficient, modern commercial unit for {biz_activity} at {location}. "
                "The project addresses distinct local market demand with quality standards and dependable service turnaround.",
                "The operational model is structured to maintain lean overheads, standard inventory turns, and prompt trade settlements, "
                "enabling sustainable operating margins from the initial year of commercial operations."
            ]
        elif section_id == "market_potential":
            paragraphs = [
                f"Available market intelligence indicates sustained local demand for {biz_activity} within {catchment} and adjacent semi-urban catchments.",
                "The target market comprises local retail consumers, institutional aggregators, and commercial trade intermediaries. "
                "The proposed project location benefits from direct road connectivity, uninterrupted logistical access, and concentrated customer footfall."
            ]
        elif section_id == "technical_feasibility":
            paragraphs = [
                "The proposed technical infrastructure, machinery configuration, and utilities have been designed in accordance with "
                "institutional industry benchmarks and established manufacturing/processing standards.",
                "Adequate provisions have been incorporated for electric power supply, water availability, storage capacity, and raw material handling, "
                "ensuring uninterrupted production runs without operational bottlenecks."
            ]
        elif section_id == "project_cost_means_finance":
            paragraphs = [
                "The total project cost of {{PROJECT_COST}} comprises fixed capital expenditure (plant, machinery, and civil works) "
                "alongside pre-operative contingencies and working capital margin provisions.",
                "The proposed means of finance adheres to conservative prudential gearing norms, comprising {{PROMOTER_CONTRIBUTION}} "
                "as promoter equity margin and {{TERM_LOAN}} as institutional term loan borrowings."
            ]
        elif section_id == "financial_viability":
            paragraphs = [
                "Projected financial statements reflect sound operational economics, generating Year-1 turnover of {{YEAR1_REVENUE}} "
                "and steady-state revenue of {{YEAR5_REVENUE}}.",
                "The debt-servicing profile is demonstrated by an Average DSCR of {{AVERAGE_DSCR}}, comfortably above the standard banking benchmark of 1.50x, "
                "with break-even sales achieved at {{BREAK_EVEN}} utilization."
            ]
        elif section_id == "risk_mitigation":
            paragraphs = [
                "Operational and market risks have been systematically evaluated across supply, market volatility, and working capital cycles.",
                "Structured mitigation protocols—including diversified vendor sourcing, conservative inventory safety stocks, and disciplined debtor collection terms—"
                "ensure resilient operational performance under adverse market conditions."
            ]
        elif section_id == "banking_proposal":
            paragraphs = [
                "The enterprise submits a formal credit facility request for an institutional Term Loan of {{TERM_LOAN}} and Working Capital facility of {{WORKING_CAPITAL}}.",
                "Primary security will consist of first hypothecation charge on all plant, machinery, fixtures, and current assets acquired under bank finance, "
                "accompanied by personal guarantee of the promoter."
            ]
        else:
            paragraphs = [
                f"Based on the available project information, {biz_name} will operate as a {biz_activity} at {location}. "
                "The project parameters adhere to authoritative institutional guidelines and documented domain standards.",
                "Detailed technical specifications, operational schedules, and financial schedules are presented in the respective sections and annexures of this report."
            ]

        meta = NarrativeProviderMetadata(
            provider="deterministic",
            model=None,
            prompt_version=PROMPT_VERSION,
            fallback_used=True,
            language=language
        )

        return SectionNarrative(
            section_id=section_id,
            title=section_title,
            paragraphs=paragraphs,
            facts_used=["business_name", "promoter_name", "total_project_cost", "term_loan"],
            source_refs=["authoritative_project_package"],
            provider_metadata=meta,
            status="FALLBACK"
        )
