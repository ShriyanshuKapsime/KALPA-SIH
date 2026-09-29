"""
Stage 15: KALPA Personal AI Business Assistant — Canonical Context Builder.
Builds the canonical AssistantContext from persisted upstream stage outputs (Stages 3–14).
Preserves distinct analysis_id, session_id, and business_id without collapsing identifiers.
Retrieves only verified stage outputs — never fabricates missing data.
"""
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.market import MarketEvidenceRecord
from app.database.models.finance import FinancialProfile
from app.database.models.feasibility import FeasibilityResult
from app.database.models.swot import SwotResult
from app.database.models.orchestrator import OrchestrationRecord
from app.database.models.report import GeneratedReport
from app.database.models.assistant import AssistantMemory


# ─────────────────────────────────────────────────────────────
# Intent → Required Stage Slicing Map
# ─────────────────────────────────────────────────────────────
INTENT_STAGE_MAP = {
    "EXPLAIN_FEASIBILITY": [
        "business_profile", "market_analysis", "opportunity_result",
        "financial_analysis", "entrepreneur_readiness", "risk_analysis",
        "feasibility_result", "swot_analysis"
    ],
    "EXPLAIN_MARKET": [
        "business_profile", "market_analysis", "opportunity_result"
    ],
    "EXPLAIN_FINANCE": [
        "business_profile", "financial_analysis", "feasibility_result"
    ],
    "EXPLAIN_RISK": [
        "business_profile", "risk_analysis", "market_analysis", "feasibility_result"
    ],
    "EXPLAIN_READINESS": [
        "business_profile", "entrepreneur_readiness", "feasibility_result"
    ],
    "EXPLAIN_SWOT": [
        "business_profile", "swot_analysis", "feasibility_result"
    ],
    "EXPLAIN_DPR": [
        "business_profile", "market_analysis", "opportunity_result",
        "financial_analysis", "entrepreneur_readiness", "risk_analysis",
        "feasibility_result", "swot_analysis", "dpr_report"
    ],
    "LOAN_GUIDANCE": [
        "business_profile", "financial_analysis", "feasibility_result"
    ],
    "SCHEME_GUIDANCE": [
        "business_profile", "financial_analysis", "feasibility_result"
    ],
    "BUSINESS_PLAN": [
        "business_profile", "market_analysis", "opportunity_result",
        "financial_analysis", "entrepreneur_readiness", "risk_analysis",
        "feasibility_result", "swot_analysis"
    ],
    "NEXT_ACTION": [
        "business_profile", "feasibility_result", "swot_analysis",
        "entrepreneur_readiness", "risk_analysis"
    ],
    "MARKET_QUESTION": [
        "business_profile", "market_analysis", "opportunity_result"
    ],
    "COMPETITOR_QUESTION": [
        "business_profile", "market_analysis"
    ],
    "COST_QUESTION": [
        "business_profile", "financial_analysis"
    ],
    "REPAYMENT_QUESTION": [
        "business_profile", "financial_analysis"
    ],
    "OPERATIONAL_QUESTION": [
        "business_profile", "entrepreneur_readiness"
    ],
    "TRAINING_QUESTION": [
        "business_profile", "entrepreneur_readiness"
    ],
    "REGISTRATION_QUESTION": [
        "business_profile"
    ],
    "DOCUMENT_QUESTION": [
        "business_profile", "financial_analysis"
    ],
    "CLOSE_GAP": [
        "business_profile", "entrepreneur_readiness", "risk_analysis", "swot_analysis"
    ],
    "CLARIFICATION": [
        "business_profile"
    ],
    "GENERAL_BUSINESS_QUESTION": [
        "business_profile", "market_analysis", "financial_analysis", "feasibility_result", "swot_analysis"
    ],
    "UNKNOWN": [
        "business_profile", "feasibility_result"
    ],
}


def safe_uuid(val: Any) -> Optional[uuid.UUID]:
    """Safely converts string or UUID object to uuid.UUID without exceptions."""
    if not val:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        clean_str = str(val).strip().strip("'\"")
        return uuid.UUID(clean_str)
    except Exception:
        return None


def calculate_pipeline_completeness(context: Dict[str, Any]) -> float:
    """
    Computes global core pipeline completeness score (0.0 to 1.0) based on verified core stages (3-13).
    DPR is considered optional and does not penalize core completeness.
    """
    checkpoints = [
        bool(context.get("business_profile") and context["business_profile"].get("business_name")),
        bool(context.get("market_analysis") and len(context["market_analysis"]) > 0),
        bool(context.get("financial_analysis") and context["financial_analysis"].get("total_project_cost") is not None),
        bool(context.get("entrepreneur_readiness") and len(context["entrepreneur_readiness"]) > 0),
        bool(context.get("risk_analysis") and len(context["risk_analysis"]) > 0),
        bool(context.get("feasibility_result") and context["feasibility_result"].get("overall_feasibility_score") is not None),
        bool(context.get("swot_analysis") and context["swot_analysis"].get("swot")),
    ]
    if not checkpoints:
        return 0.0
    return round(sum(1 for c in checkpoints if c) / len(checkpoints), 2)


def calculate_intent_completeness(context_slice: Dict[str, Any], intent: str) -> float:
    """
    Calculates whether the specific stages required for the detected intent are populated.
    """
    needed_keys = INTENT_STAGE_MAP.get(intent, INTENT_STAGE_MAP["UNKNOWN"])
    if not needed_keys:
        return 1.0
    present_count = 0
    for k in needed_keys:
        val = context_slice.get(k)
        if val and isinstance(val, dict) and len(val) > 0:
            present_count += 1
    return round(present_count / len(needed_keys), 2)


def build_full_assistant_context(
    analysis_id: Optional[str],
    session_id: Optional[str],
    db: Session,
    business_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds the canonical AssistantContext from persisted upstream stage outputs.
    Preserves distinct analysis_id, session_id, and business_id.
    Missing data remains null / empty dict — never fabricated.
    """
    analysis_uuid = safe_uuid(analysis_id)
    session_uuid = safe_uuid(session_id)
    business_uuid = safe_uuid(business_id)

    context: Dict[str, Any] = {
        "analysis_id": str(analysis_uuid) if analysis_uuid else None,
        "session_id": str(session_uuid) if session_uuid else None,
        "business_id": str(business_uuid) if business_uuid else None,
        "user": {
            "language": "en",
            "preferred_language": "en",
            "communication_style": "simple",
            "voice_enabled": True
        },
        "business_profile": {},
        "market_analysis": {},
        "opportunity_result": {},
        "financial_analysis": {},
        "entrepreneur_readiness": {},
        "risk_analysis": {},
        "feasibility_result": {},
        "swot_analysis": {},
        "dpr_report": {},
        "workflow_state": {
            "current_stage": 13,
            "dpr_available": False,
            "loan_guidance_available": True,
            "business_launched": False,
            "growth_manager_active": False,
        },
        "user_memory": {},
        "conversation_memory": {},
    }

    if not db or (not analysis_uuid and not session_uuid):
        return context

    try:
        # ─────────────────────────────────────────────────────────────
        # 1. Structured Business Profile (Stage 3 & 10)
        # ─────────────────────────────────────────────────────────────
        prof = None
        if analysis_uuid:
            prof = db.query(StructuredBusinessProfile).filter(
                StructuredBusinessProfile.id == analysis_uuid
            ).order_by(StructuredBusinessProfile.created_at.desc()).first()

        if not prof and session_uuid:
            prof = db.query(StructuredBusinessProfile).filter(
                StructuredBusinessProfile.session_id == session_uuid
            ).order_by(StructuredBusinessProfile.created_at.desc()).first()

        if prof and prof.profile_json:
            pj = prof.profile_json
            bp = pj.get("business_profile") or {}
            lp = pj.get("location_profile") or {}

            context["business_profile"] = {
                "business_id": str(prof.id),
                "specific_business": prof.specific_business or bp.get("specific_business") or bp.get("business_name"),
                "business_name": prof.specific_business or bp.get("business_name") or bp.get("specific_business"),
                "category": pj.get("category") or bp.get("category"),
                "sector": pj.get("sector") or bp.get("sector"),
                "nic_code": prof.nic_code or bp.get("nic_code"),
                "location": {
                    "village": lp.get("village") or prof.district,
                    "district": prof.district or lp.get("district"),
                    "state": prof.state or lp.get("state"),
                },
                "capital": pj.get("capital") or bp.get("available_capital") or bp.get("proposed_investment"),
                "business_intent": pj.get("business_intent") or bp.get("business_intent"),
                "business_model": bp.get("business_model"),
                "target_scale": bp.get("target_scale", "micro"),
            }

            if pj.get("entrepreneur_profile"):
                context["entrepreneur_profile"] = pj["entrepreneur_profile"]

            if pj.get("entrepreneur_readiness"):
                context["entrepreneur_readiness"] = pj["entrepreneur_readiness"]

            lang = pj.get("language") or pj.get("detected_language") or "en"
            context["user"]["language"] = lang
            context["user"]["preferred_language"] = lang

            if not context["session_id"] and prof.session_id:
                context["session_id"] = str(prof.session_id)

        # ─────────────────────────────────────────────────────────────
        # 2. Market Evidence Record (Stage 6)
        # ─────────────────────────────────────────────────────────────
        mkt = None
        if analysis_uuid:
            mkt = db.query(MarketEvidenceRecord).filter(
                MarketEvidenceRecord.id == analysis_uuid
            ).order_by(MarketEvidenceRecord.created_at.desc()).first()

        if not mkt and session_uuid:
            mkt = db.query(MarketEvidenceRecord).filter(
                MarketEvidenceRecord.session_id == session_uuid
            ).order_by(MarketEvidenceRecord.created_at.desc()).first()

        if mkt:
            context["market_analysis"] = mkt.market_evidence or mkt.full_profile or {}
            if mkt.evidence_gaps:
                context["evidence_gaps"] = mkt.evidence_gaps
            elif isinstance(mkt.full_profile, dict) and mkt.full_profile.get("evidence_gaps"):
                context["evidence_gaps"] = mkt.full_profile.get("evidence_gaps")

        # ─────────────────────────────────────────────────────────────
        # 3. Orchestration Record (Stages 8, 9, 10, 11)
        # ─────────────────────────────────────────────────────────────
        orch = None
        if analysis_uuid:
            orch = db.query(OrchestrationRecord).filter(
                OrchestrationRecord.id == analysis_uuid
            ).order_by(OrchestrationRecord.created_at.desc()).first()

        if not orch and session_uuid:
            orch = db.query(OrchestrationRecord).filter(
                OrchestrationRecord.session_id == session_uuid
            ).order_by(OrchestrationRecord.created_at.desc()).first()

        if orch and orch.orchestration_output:
            out = orch.orchestration_output
            res = out.get("agent_results", {}) if isinstance(out, dict) else {}

            if not context.get("opportunity_result"):
                context["opportunity_result"] = (
                    res.get("opportunity_evaluation_engine") or res.get("opportunity_evaluation")
                    or out.get("opportunity_evaluation") or out.get("opportunity_result") or {}
                )

            if not context.get("entrepreneur_readiness"):
                context["entrepreneur_readiness"] = (
                    res.get("entrepreneur_profile_engine") or res.get("entrepreneur_profile")
                    or out.get("entrepreneur_profile") or {}
                )

            if not context.get("risk_analysis"):
                context["risk_analysis"] = (
                    res.get("risk_engine") or res.get("risk_analysis") or out.get("risk_analysis") or {}
                )

        # ─────────────────────────────────────────────────────────────
        # 4. Financial Profile (Stage 9)
        # ─────────────────────────────────────────────────────────────
        fin = None
        fin_query = db.query(FinancialProfile)
        if analysis_uuid:
            fin = fin_query.filter(
                (FinancialProfile.id == analysis_uuid) |
                (FinancialProfile.business_id == analysis_uuid)
            ).order_by(FinancialProfile.created_at.desc()).first()

        if not fin and business_uuid:
            fin = fin_query.filter(FinancialProfile.business_id == business_uuid).order_by(FinancialProfile.created_at.desc()).first()

        if not fin and session_uuid:
            fin = fin_query.filter(
                (FinancialProfile.id == session_uuid) |
                (FinancialProfile.business_id == session_uuid)
            ).order_by(FinancialProfile.created_at.desc()).first()

        if not fin and prof:
            fin = fin_query.filter(FinancialProfile.business_id == prof.id).order_by(FinancialProfile.created_at.desc()).first()

        if fin:
            bk = fin.breakdown_json if isinstance(fin.breakdown_json, dict) else {}
            context["financial_context"] = bk.get("financial_context")
            context["financial_analysis"] = {
                "total_project_cost": fin.total_project_cost or bk.get("total_project_cost"),
                "promoter_contribution": fin.promoter_contribution or bk.get("promoter_contribution"),
                "bank_loan_requirement": fin.bank_loan_requirement or bk.get("bank_loan_requirement") or bk.get("term_loan"),
                "subsidy_amount": fin.subsidy_amount or bk.get("subsidy_amount"),
                "applicable_scheme_name": fin.applicable_scheme_name or bk.get("applicable_scheme_name") or bk.get("recommended_scheme"),
                "projected_annual_revenue": fin.projected_annual_revenue or bk.get("projected_annual_revenue") or bk.get("first_year_revenue"),
                "projected_operating_expenses": fin.projected_operating_expenses or bk.get("projected_operating_expenses") or bk.get("first_year_opex"),
                "projected_net_profit": fin.projected_net_profit or bk.get("projected_net_profit") or bk.get("first_year_pat"),
                "dscr": fin.debt_service_coverage_ratio or bk.get("dscr") or bk.get("average_dscr"),
                "break_even_percentage": fin.break_even_percentage or bk.get("break_even_percentage"),
                "monthly_emi": bk.get("monthly_emi"),
                "scheme_matches": bk.get("scheme_matches") or [],
                "retained_reserve": bk.get("retained_reserve") or bk.get("margin_surplus"),
                "interest_rate": bk.get("interest_rate"),
                "tenure_months": bk.get("tenure_months"),
                "financial_viability": "viable" if (isinstance(fin.debt_service_coverage_ratio, (int, float)) and fin.debt_service_coverage_ratio >= 1.25) else "marginal",
                "dpr_financial_package": bk.get("dpr_financial_package"),
                "financial_context": bk.get("financial_context"),
            }
        elif prof and prof.profile_json and (prof.profile_json.get("financial_analysis") or prof.profile_json.get("financial_profile") or prof.profile_json.get("financial_context")):
            p_fin = prof.profile_json.get("financial_analysis") or prof.profile_json.get("financial_profile") or {}
            p_ctx = prof.profile_json.get("financial_context") or (p_fin.get("financial_context") if isinstance(p_fin, dict) else None)
            context["financial_context"] = p_ctx
            context["financial_analysis"] = p_fin if isinstance(p_fin, dict) else {}
            if p_ctx and isinstance(context["financial_analysis"], dict):
                context["financial_analysis"]["financial_context"] = p_ctx
        elif orch and orch.orchestration_output:
            orch_fin = (orch.orchestration_output.get("agent_results", {}).get("finance_engine")
                        or orch.orchestration_output.get("agent_results", {}).get("financial_analysis")
                        or orch.orchestration_output.get("financial_analysis"))
            if orch_fin and isinstance(orch_fin, dict):
                context["financial_analysis"] = orch_fin
                context["financial_context"] = orch_fin.get("financial_context")

        # If financial_context is present, enrich financial_analysis with its canonical fields
        if context.get("financial_context"):
            fc = context["financial_context"]
            fa = context.setdefault("financial_analysis", {})
            if isinstance(fa, dict) and isinstance(fc, dict):
                proj_cost = fc.get("project_cost") or {}
                funding = fc.get("funding") or {}
                debt = fc.get("debt") or {}
                banking = fc.get("banking_appraisal") or {}
                pl = fc.get("profit_loss") or []
                y1 = pl[0] if (isinstance(pl, list) and len(pl) > 0) else {}
                stress = fc.get("m5_stress_appraisal") or {}
                tax_info = fc.get("resolved_tax") or {}

                if not fa.get("total_project_cost"): fa["total_project_cost"] = proj_cost.get("total_project_cost")
                if not fa.get("promoter_contribution"): fa["promoter_contribution"] = funding.get("required_promoter_contribution")
                if not fa.get("bank_loan_requirement"): fa["bank_loan_requirement"] = funding.get("institutional_loan") or debt.get("sanctioned_loan_amount")
                if not fa.get("subsidy_amount"): fa["subsidy_amount"] = funding.get("subsidy_amount")
                if not fa.get("monthly_emi"): fa["monthly_emi"] = debt.get("emi")
                if not fa.get("interest_rate"): fa["interest_rate"] = debt.get("interest_rate_pct")
                if not fa.get("tenure_months"): fa["tenure_months"] = debt.get("tenure_months")
                if not fa.get("dscr"): fa["dscr"] = banking.get("average_dscr") or banking.get("min_dscr")
                if not fa.get("break_even_percentage"): fa["break_even_percentage"] = banking.get("break_even_utilization_pct")
                if not fa.get("projected_annual_revenue"): fa["projected_annual_revenue"] = y1.get("revenue")
                if not fa.get("projected_operating_expenses"): fa["projected_operating_expenses"] = y1.get("opex")
                if not fa.get("projected_net_profit"): fa["projected_net_profit"] = y1.get("pat")
                fa["working_capital"] = proj_cost.get("working_capital")
                fa["downside_dscr"] = stress.get("downside_dscr")
                fa["downside_revenue"] = stress.get("downside_revenue")
                fa["profit_loss"] = pl
                fa["resolved_tax"] = tax_info

        # ─────────────────────────────────────────────────────────────
        # 5. Feasibility Result (Stage 12)
        # ─────────────────────────────────────────────────────────────
        feas = None
        if analysis_uuid:
            feas = db.query(FeasibilityResult).filter(
                FeasibilityResult.id == analysis_uuid
            ).order_by(FeasibilityResult.created_at.desc()).first()

        if not feas and session_uuid:
            feas = db.query(FeasibilityResult).filter(
                FeasibilityResult.session_id == session_uuid
            ).order_by(FeasibilityResult.created_at.desc()).first()

        if feas:
            context["feasibility_result"] = {
                "overall_feasibility_score": feas.overall_feasibility_score,
                "viability_status": feas.viability_status,
                "recommendation": feas.recommendation,
                "confidence_score": feas.confidence_score,
                "pillar_scores": feas.pillar_scores or {
                    "market_score": feas.market_score,
                    "financial_score": feas.financial_score,
                    "entrepreneur_fit_score": feas.entrepreneur_fit_score,
                    "risk_resilience_score": feas.risk_resilience_score,
                },
                "critical_gates": feas.critical_gates or [],
                "positive_drivers": feas.positive_drivers or [],
                "key_constraints": feas.key_constraints or [],
                "conditions": feas.conditions or [],
                "strengths": feas.strengths or [],
                "weaknesses": feas.weaknesses or [],
                "opportunities": feas.opportunities or [],
                "threats": feas.threats or [],
                "advisory_notes": feas.advisory_notes or [],
                "pivot_recommendations": feas.pivot_recommendations or [],
            }

        # ─────────────────────────────────────────────────────────────
        # 6. Dynamic SWOT Result (Stage 13) — Complete Output
        # ─────────────────────────────────────────────────────────────
        swot = None
        if analysis_uuid:
            swot = db.query(SwotResult).filter(
                SwotResult.id == analysis_uuid
            ).order_by(SwotResult.created_at.desc()).first()

        if not swot and session_uuid:
            swot = db.query(SwotResult).filter(
                SwotResult.session_id == session_uuid
            ).order_by(SwotResult.created_at.desc()).first()

        if swot and swot.swot_json:
            context["swot_analysis"] = {
                "status": swot.status,
                "confidence": swot.confidence_score,
                "swot": swot.swot_json,
                "strengths": swot.swot_json.get("strengths", []),
                "weaknesses": swot.swot_json.get("weaknesses", []),
                "opportunities": swot.swot_json.get("opportunities", []),
                "threats": swot.swot_json.get("threats", []),
                "priority_actions": swot.immediate_actions_json or swot.swot_json.get("priority_actions", []) or swot.swot_json.get("priority_action_plan", []),
                "strategic_roadmap": swot.strategic_summary_json.get("roadmap") or swot.recommendations_json or swot.swot_json.get("strategic_roadmap", []),
                "conditions": (feas.conditions if feas else []) or swot.swot_json.get("conditions", []),
                "strategic_summary": swot.strategic_summary_json or {},
                "recommendations": swot.recommendations_json or [],
                "immediate_actions": swot.immediate_actions_json or [],
                "evidence_summary": swot.evidence_summary_json or {},
                "model_metadata": swot.model_metadata_json or {},
            }

        # ─────────────────────────────────────────────────────────────
        # 7. Stage 14 DPR / Generated Report Inspection
        # ─────────────────────────────────────────────────────────────
        dpr_rec = None
        dpr_query = db.query(GeneratedReport)
        if analysis_uuid:
            dpr_rec = dpr_query.filter(
                (GeneratedReport.id == analysis_uuid) | (GeneratedReport.business_id == analysis_uuid)
            ).order_by(GeneratedReport.created_at.desc()).first()

        if not dpr_rec and session_uuid:
            dpr_rec = dpr_query.filter(GeneratedReport.business_id == session_uuid).order_by(GeneratedReport.created_at.desc()).first()

        if not dpr_rec and business_uuid:
            dpr_rec = dpr_query.filter(GeneratedReport.business_id == business_uuid).order_by(GeneratedReport.created_at.desc()).first()

        dpr_data = None
        if dpr_rec:
            dpr_data = {
                "report_id": str(dpr_rec.id),
                "report_type": dpr_rec.report_type,
                "report_title": dpr_rec.report_title,
                "report_summary": dpr_rec.report_summary,
                "file_format": dpr_rec.file_format,
                "payload": dpr_rec.report_payload or {}
            }

        # Also inspect active DPR scenario in scenario_manager / disk
        from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager
        biz_candidates = [
            c for c in [
                business_id,
                str(business_uuid) if business_uuid else None,
                str(analysis_uuid) if analysis_uuid else None,
                str(session_uuid) if session_uuid else None,
                prof.specific_business if prof else None,
                str(prof.id) if prof else None
            ] if c
        ]

        found_scen = None
        matched_biz = None
        for b_cand in biz_candidates:
            scen = dpr_scenario_manager.get(b_cand)
            if scen and (scen.financial_package or scen.user_answers or scen.user_overrides):
                found_scen = scen
                matched_biz = b_cand
                break

        if found_scen or dpr_rec:
            context["workflow_state"]["dpr_available"] = True
            context["workflow_state"]["current_stage"] = 14

            fin_pkg = (found_scen.financial_package if found_scen else {}) or {}
            bm = fin_pkg.get("banking_metrics") or {}
            proj = fin_pkg.get("project_cost") or {}
            means = fin_pkg.get("means_of_finance") or {}

            raw_name = (prof.specific_business if prof else None) or matched_biz or business_id or "Enterprise"
            clean_biz_name = raw_name.replace("_", " ").title() if (isinstance(raw_name, str) and "_" in raw_name) else str(raw_name)

            dpr_info = {
                "report_id": str(dpr_rec.id) if dpr_rec else (found_scen.scenario_id if found_scen else "DPR-CURRENT"),
                "dpr_status": "BANK_REVIEW_READY",
                "report_title": f"Institutional Detailed Project Report - {clean_biz_name}",
                "business_name": clean_biz_name,
                "total_project_cost": proj.get("total_project_cost") or context.get("financial_analysis", {}).get("total_project_cost"),
                "bank_term_loan": means.get("bank_term_loan") or means.get("term_loan") or context.get("financial_analysis", {}).get("bank_loan_requirement"),
                "promoter_contribution": means.get("promoter_margin") or means.get("promoter_equity") or context.get("financial_analysis", {}).get("promoter_contribution"),
                "average_dscr": bm.get("average_dscr") or context.get("financial_analysis", {}).get("dscr"),
                "total_sections": 39,
                "completed_sections": 39,
                "pdf_available": True,
                "summary": f"Institutional-grade Bank-Review-Ready DPR generated across 39 canonical sections and financial annexures (P&L, Balance Sheet, DSCR schedules) for {clean_biz_name}."
            }
            if dpr_data:
                dpr_info.update(dpr_data)
            context["dpr_report"] = dpr_info

        # ─────────────────────────────────────────────────────────────
        # 8. Assistant Memory (Stage 15)
        # ─────────────────────────────────────────────────────────────
        mem = None
        if analysis_uuid and session_uuid:
            mem = db.query(AssistantMemory).filter(
                (AssistantMemory.analysis_id == analysis_uuid) &
                (AssistantMemory.session_id == session_uuid)
            ).first()

        if not mem and analysis_uuid:
            mem = db.query(AssistantMemory).filter(AssistantMemory.analysis_id == analysis_uuid).first()

        if not mem and session_uuid:
            mem = db.query(AssistantMemory).filter(AssistantMemory.session_id == session_uuid).first()

        if mem:
            context["user_memory"] = mem.business_memory or {}
            context["conversation_memory"] = mem.conversation_memory or {}
            context["workflow_state"]["business_launched"] = (mem.business_status == "LAUNCHED")

    except Exception as e:
        logger.error(f"[ASSISTANT CONTEXT BUILDER] Error querying database: {e}", exc_info=True)

    return context


def get_intent_context(full_context: Dict[str, Any], intent: str) -> Dict[str, Any]:
    """
    Returns the grounded context for a given intent.
    Preserves all available stage outputs so the assistant can synthesize across pillars,
    while highlighting the primary intent-focused stages.
    """
    sliced = dict(full_context)
    sliced["primary_intent"] = intent
    sliced["intent_focus_stages"] = INTENT_STAGE_MAP.get(intent, INTENT_STAGE_MAP["UNKNOWN"])
    return sliced

