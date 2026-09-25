"""
Legacy Adapter.
Bridges the new Financial Intelligence Foundation to the existing Stage 9 contract.
Ensures backward compatibility — all existing fields remain intact.
New foundation fields are added alongside, never replacing.
"""
import logging
from typing import Dict, Any, Optional, List
from app.services.financial_engine.intelligence.archetype_registry import (
    FinancialArchetype, archetype_registry
)
from app.services.financial_engine.intelligence.assumption_registry import assumption_resolver
from app.services.financial_engine.intelligence.question_engine import question_engine
from app.services.financial_engine.intelligence.confidence import FoundationStatus

logger = logging.getLogger(__name__)


class LegacyAdapter:
    """
    Runs the Financial Intelligence Foundation underneath the existing
    Stage 9 engine and merges results into the existing contract
    as backward-compatible optional fields.
    """

    def enrich_financial_analysis(
        self,
        existing_response_dict: Dict[str, Any],
        business_profile: Optional[Dict[str, Any]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        benchmark_data_dict: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        scheme_data: Optional[Dict[str, Any]] = None,
        analysis_id: Optional[str] = None,
        project_cost_basis: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Takes the existing FinancialAnalysisResponse dict and enriches it
        with Financial Intelligence Foundation metadata.
        All existing fields remain untouched.
        """
        biz = business_profile or {}
        specific_business = biz.get("specific_business")
        sector = biz.get("sector")
        category = biz.get("category")
        subcategory = biz.get("subcategory") or biz.get("sub_category")
        nic_code = biz.get("nic_code")
        user_lang = language or (user_inputs or {}).get("language") or biz.get("language") or "en"

        # 1. Resolve financial archetype from Stage 2/3 classification
        try:
            archetype = archetype_registry.resolve(
                specific_business=specific_business,
                sector=sector,
                category=category,
                subcategory=subcategory,
                nic_code=nic_code,
            )
        except Exception as e:
            logger.warning(f"[FINANCE FOUNDATION] Archetype resolution failed: {e}")
            archetype = FinancialArchetype.OTHER

        logger.info(f"[FINANCE FOUNDATION] Resolved financial archetype={archetype.value}")

        # 2. Resolve assumptions with all real evidence sources
        try:
            resolution_result = assumption_resolver.resolve_all(
                archetype=archetype,
                user_inputs=user_inputs or {},
                benchmark_data=benchmark_data_dict or {},
                market_data=market_data or {},
                scheme_data=scheme_data or {},
                analysis_id=analysis_id,
            )
        except Exception as e:
            logger.warning(f"[FINANCE FOUNDATION] Assumption resolution failed: {e}")
            resolution_result = {
                "archetype": archetype.value,
                "assumptions": [],
                "assumption_status": FoundationStatus.FAILED.value,
                "resolved_count": 0,
                "total_count": 0,
                "user_required_count": 0,
                "unknown_count": 0,
                "assumption_confidence": {"overall": 0.0, "resolved": 0, "total": 0, "user_required": 0, "unknown": 0},
                "provenance": [],
            }

        # 3. Milestone 2: Automated Project Cost & Working Capital Engine
        project_cost_analysis_dict = None
        working_capital_analysis_dict = None
        try:
            from app.services.financial_engine.project_cost import project_cost_engine
            from app.services.financial_engine.intelligence.confidence import ResolvedAssumption

            raw_assumptions = resolution_result.get("assumptions", [])
            typed_assumptions = [
                a if isinstance(a, ResolvedAssumption) else ResolvedAssumption(**a)
                for a in raw_assumptions
            ]

            preferred_cost = (user_inputs or {}).get("preferred_project_cost")
            scheme_fin_cost = (scheme_data or {}).get("maximum_financeable_project_cost") or (scheme_data or {}).get("maximum_loan")

            pc_analysis, wc_analysis, enriched_assumptions = project_cost_engine.evaluate(
                archetype=archetype,
                assumptions=typed_assumptions,
                benchmark_data=benchmark_data_dict,
                user_inputs=user_inputs,
                scheme_financeable_cost=scheme_fin_cost,
                scheme_margin_ratio=float((scheme_data or {}).get("margin_ratio", 0.10)),
                preferred_project_cost=preferred_cost,
            )
            # Update assumptions with any newly derived assumptions from M2
            resolution_result["assumptions"] = [a.to_dict() for a in enriched_assumptions]
            project_cost_analysis_dict = pc_analysis.model_dump()
            working_capital_analysis_dict = wc_analysis.model_dump()
        except Exception as e:
            logger.warning(f"[PROJECT COST ENGINE] Milestone 2 evaluation failed: {e}")

        # 4. Generate questions for unresolved HIGH-criticality drivers in user's language
        try:
            questions = question_engine.generate_questions(
                assumptions=resolution_result.get("assumptions", []),
                language=user_lang,
            )
            required_user_inputs = [q.model_dump() for q in questions]
        except Exception as e:
            logger.warning(f"[FINANCE FOUNDATION] Question generation failed: {e}")
            required_user_inputs = []

        # 5. Enrich the existing financial_analysis container
        fa = existing_response_dict.get("financial_analysis", {})

        # Accurately describe project_cost_basis without altering project_cost itself
        fa["project_cost_basis"] = project_cost_basis or "MARGIN_DERIVED"
        fa["financial_archetype"] = archetype.value
        fa["assumption_status"] = resolution_result.get("assumption_status", "PARTIAL")
        fa["assumptions"] = resolution_result.get("assumptions", [])
        fa["required_user_inputs"] = required_user_inputs
        fa["assumption_confidence"] = resolution_result.get("assumption_confidence")
        fa["provenance"] = resolution_result.get("provenance", [])
        fa["model_version"] = "finance-foundation-v1"
        # Milestone 2 optional additions
        fa["project_cost_analysis"] = project_cost_analysis_dict
        fa["working_capital_analysis"] = working_capital_analysis_dict

        existing_response_dict["financial_analysis"] = fa

        logger.info(f"[FINANCE FOUNDATION] Legacy financial contract preserved with M1+M2 enrichment (basis={fa['project_cost_basis']})")
        return existing_response_dict


# Global singleton
legacy_adapter = LegacyAdapter()
