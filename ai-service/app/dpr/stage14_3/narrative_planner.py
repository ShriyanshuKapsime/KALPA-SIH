"""
Stage 14.3: DPR Narrative Planner.
Plans section narrative requirements using Sarvam AI with deterministic fallback.
Extracts section-specific slice of DPR_NARRATIVE_SOURCE_PACKAGE.
"""
from typing import Dict, Any, List, Optional
from app.dpr.stage14_3.document_schema import NarrativePlan
from app.dpr.stage14_3.sarvam_service import SarvamDPRNarrativeService


class DPRNarrativePlanner:
    """
    Coordinates narrative planning per section, ensuring only verified facts enter scope.
    """

    def __init__(self, sarvam_service: Optional[SarvamDPRNarrativeService] = None):
        self.sarvam = sarvam_service or SarvamDPRNarrativeService()

    async def plan_section(
        self,
        section_id: str,
        section_title: str,
        source_data: Dict[str, Any],
        language: str = "en",
        business_id: str = "general",
        scenario_id: str = "default"
    ) -> NarrativePlan:
        # 1. Try Sarvam planning if configured
        if self.sarvam.is_configured:
            plan = await self.sarvam.create_narrative_plan(
                section_id=section_id,
                section_title=section_title,
                source_data=source_data,
                language=language,
                business_id=business_id,
                scenario_id=scenario_id
            )
            if plan:
                return plan

        # 2. Deterministic Plan Fallback
        return self._generate_deterministic_plan(section_id, section_title, source_data)

    def _generate_deterministic_plan(
        self,
        section_id: str,
        section_title: str,
        source_data: Dict[str, Any]
    ) -> NarrativePlan:
        key_points = []
        facts = []
        evidence = []

        if "business_name" in source_data:
            key_points.append(f"Enterprise identity: {source_data['business_name']}")
            facts.append("business_name")
        if "promoter_name" in source_data:
            key_points.append(f"Promoter profile and background: {source_data['promoter_name']}")
            facts.append("promoter_name")
        if "total_project_cost" in source_data or "project_cost" in source_data:
            key_points.append("Total capital requirements and project outlay")
            facts.append("project_cost")
        if "term_loan" in source_data:
            key_points.append("Proposed term loan facility and repayment obligations")
            facts.append("term_loan")
        if "market_demand" in source_data or "target_customers" in source_data:
            key_points.append("Local demand drivers and customer catchment")
            evidence.append("market_intelligence")
        if "risk_factors" in source_data or "risks" in source_data:
            key_points.append("Identified operational/financial risks and mitigation measures")
            evidence.append("risk_assessment")

        if not key_points:
            key_points.append(f"Appraisal and operational analysis for {section_title.lower()}")

        return NarrativePlan(
            section_id=section_id,
            key_points=key_points,
            evidence_to_reference=evidence,
            facts_used=facts,
            recommended_length="medium"
        )
