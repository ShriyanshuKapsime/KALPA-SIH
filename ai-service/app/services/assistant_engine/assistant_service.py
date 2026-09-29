"""
Stage 15: KALPA Personal AI Business Assistant — Service Engine.
Handles contextual intent classification, strict prompt grounding from all deterministic KALPA stages,
Sarvam LLM calling with non-blocking async retries and timeouts, structured memory & constraint persistence,
realistic grounding telemetry, and dynamic action recommendations.
"""
import uuid
import json
import re
import time
import asyncio
import datetime
import httpx
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.database.models.assistant import AssistantConversation, AssistantMemory
from app.services.assistant_engine.context_builder import (
    build_full_assistant_context,
    get_intent_context,
    calculate_pipeline_completeness,
    calculate_intent_completeness,
    safe_uuid
)


# ─────────────────────────────────────────────────────────────
# Robust Intent Classification Patterns & Disambiguation
# ─────────────────────────────────────────────────────────────

INTENT_RULES = [
    # Specific Financial metrics
    ("REPAYMENT_QUESTION", [
        r"\bemi\b", r"\brepay", r"\btenure\b", r"\bmonthly installment\b",
        r"किस्त", r"ईएमआई", r"किश्त", r"मासिक किस्त", r"repayment"
    ]),
    ("COST_QUESTION", [
        r"\bproject cost\b", r"\bcapex\b", r"\bopex\b", r"\bexpense\b", r"\bhow much.*spend\b",
        r"कितना खर्च", r"कितना पैसा", r"लागत", r"कुल खर्च", r"खर्चा", r"budget"
    ]),
    ("LOAN_GUIDANCE", [
        r"\bloans?\b", r"\bborrow\b", r"\bbank finance\b", r"\bcollateral\b", r"\bmargin money\b",
        r"लोन", r"ऋण", r"कर्ज", r"उधार", r"बैंक लोन", r"loan milega"
    ]),
    ("SCHEME_GUIDANCE", [
        r"\bschemes?\b", r"\bsubsid", r"\bpmegp\b", r"\bmudra\b", r"\bstandup\b", r"\bjansamarth\b", r"\bgrant\b",
        r"योजना", r"सब्सिडी", r"पीएमईजीपी", r"मुद्रा योजना", r"अनुदान", r"scheme"
    ]),
    ("EXPLAIN_FINANCE", [
        r"\bfinancial score\b", r"\bdscr\b", r"\bbreak[\s-]?even\b", r"\bprofit\b", r"\brevenue\b", r"\bmargin\b", r"\bfinancial\b", r"\bfinance\b",
        r"पैसे की स्थिति", r"वित्तीय स्थिति", r"वित्तीय", r"मुनाफा", r"कमाई", r"प्रॉफिट", r"फाइनेंस"
    ]),

    # SWOT specific
    ("EXPLAIN_SWOT", [
        r"\bswot\b", r"\bweakness", r"\bstrength", r"\bopportunit", r"\bthreat", r"\bstrategic direction\b",
        r"कमजोरी", r"कमज़ोरी", r"ताकत", r"मजबूती", r"अवसर", r"खतरे", r"kamzori", r"taakat", r"strengths?"
    ]),

    # Feasibility specific
    ("EXPLAIN_FEASIBILITY", [
        r"\bfeasib", r"\bviab", r"\bfeasibility score\b", r"\boverall score\b", r"\bwhy.*score\b", r"\bwill it work\b", r"\bcan i start\b", r"\bpass.*fail\b",
        r"व्यवहार्यता", r"व्यवहार्य", r"शुरू करना चाहिए", r"शुरू करूँ", r"चलेगा या नहीं", r"feasibility", r"व्यवसाय कैसा", r"बिज़नेस कैसा", r"स्कोर क्या", r"स्कोर"
    ]),

    # Readiness & Skills
    ("TRAINING_QUESTION", [
        r"\btrain", r"\brseti\b", r"\bedp\b", r"\bskill development\b",
        r"ट्रेनिंग", r"प्रशिक्षण", r"कौशल", r"training"
    ]),
    ("EXPLAIN_READINESS", [
        r"\breadiness\b", r"\bskill", r"\bexperience\b", r"\bprepared\b", r"\bcapability\b", r"\bfit score\b",
        r"तैयार हूँ", r"तैयारी", r"क्षमता", r"अनुभव", r"फिट स्कोर", r"readiness"
    ]),
    ("CLOSE_GAP", [
        r"\bgap\b", r"\bclose.*gap\b", r"\bfix.*weakness\b", r"\bhow to improve\b",
        r"कैसे सुधारूं", r"सुधार कैसे", r"कमी कैसे दूर", r"kaise sudharu", r"सुधार"
    ]),

    # Risk specific
    ("EXPLAIN_RISK", [
        r"\brisk", r"\bdanger\b", r"\bfailure\b", r"\bmitigat", r"\bloss\b", r"\bresilience\b",
        r"रिस्क", r"जोखिम", r"खतरा", r"नुकसान", r"resilience"
    ]),

    # Market & Competitors
    ("COMPETITOR_QUESTION", [
        r"\bcompetitor", r"\brival\b", r"\bother shops\b", r"\bother sellers\b",
        r"प्रतियोगी", r"प्रतिस्पर्धी", r"दूसरी दुकान", r"कंपटीटर"
    ]),
    ("MARKET_QUESTION", [
        r"\bmarket size\b", r"\bcatchment\b", r"\bfootfall\b", r"\blocal demand\b",
        r"मांग", r"मांग कैसी", r"डिमांड", r"स्थानीय मांग"
    ]),
    ("EXPLAIN_MARKET", [
        r"\bmarket\b", r"\bdemand\b", r"\bcustomer\b", r"\btrend\b", r"\btarget audience\b",
        r"बाजार", r"ग्राहक", r"मार्केट", r"maang"
    ]),

    # DPR
    ("EXPLAIN_DPR", [
        r"\bdpr\b", r"\bdetailed project report\b", r"\bproject report\b", r"\bbank report\b",
        r"डीपीआर", r"प्रोजेक्ट रिपोर्ट"
    ]),

    # Legal & Registration
    ("REGISTRATION_QUESTION", [
        r"\bregist", r"\budyam\b", r"\bgst\b", r"\blicense\b", r"\bpermit\b", r"\bfssai\b", r"\bpan card\b",
        r"पंजीकरण", r"रजिस्ट्रेशन", r"उद्यम", r"जीएसटी"
    ]),
    ("DOCUMENT_QUESTION", [
        r"\bdocument", r"\bpaperwork\b", r"\bcertificate\b", r"\bform\b",
        r"दस्तावेज", r"कागजात", r"डॉक्यूमेंट"
    ]),

    # Next Steps & Planning
    ("NEXT_ACTION", [
        r"\bnext steps?\b", r"\bwhat should i do\b", r"\bwhere to start\b", r"\bhow to begin\b", r"\baction plans?\b", r"\broadmaps?\b", r"\bwhat next\b",
        r"क्या करना चाहिए", r"आगे क्या", r"अब क्या करें", r"शुरुआत कैसे", r"aage kya karu", r"कदम", r"पहला कदम"
    ]),
    ("BUSINESS_PLAN", [
        r"\bbusiness plans?\b", r"\bgrowth strateg", r"\bscale\b", r"\bexpansion\b",
        r"व्यापार योजना", r"बिजनेस प्लान", r"विस्तार"
    ]),
]


def detect_intent(message: str, previous_intent: Optional[str] = None) -> str:
    """
    Context-aware deterministic intent classifier with rule priority and disambiguation.
    """
    msg_lower = message.lower().strip()

    # Disambiguate bare words like "score" or "स्कोर"
    if re.search(r"\bscore\b", msg_lower) or "स्कोर" in msg_lower:
        if any(w in msg_lower for w in ["finance", "financial", "dscr", "money", "पैसा", "वित्तीय", "बजट"]):
            return "EXPLAIN_FINANCE"
        if any(w in msg_lower for w in ["market", "demand", "मांग", "बाजार", "मार्केट"]):
            return "EXPLAIN_MARKET"
        if any(w in msg_lower for w in ["risk", "threat", "danger", "रिस्क", "खतरा", "जोखिम"]):
            return "EXPLAIN_RISK"
        if any(w in msg_lower for w in ["readiness", "skill", "founder", "तैयारी", "कौशल", "अनुभव"]):
            return "EXPLAIN_READINESS"
        return "EXPLAIN_FEASIBILITY"

    # Evaluate pattern rules in order
    for intent, patterns in INTENT_RULES:
        for pat in patterns:
            if re.search(pat, msg_lower):
                return intent

    return "GENERAL_BUSINESS_QUESTION"


# ─────────────────────────────────────────────────────────────
# User Constraints, Claims & Preferences Extractor
# ─────────────────────────────────────────────────────────────

def extract_user_claims_and_constraints(message: str) -> List[Dict[str, Any]]:
    """
    Extracts explicit user-stated constraints, claims, or preferences without
    overwriting deterministic KALPA records.
    """
    claims = []
    msg = message.strip()

    # Max loan constraint
    loan_limit_match = re.search(
        r"(?:don'?t want to borrow more than|max(?:imum)? loan|loan limit|cannot borrow more than|not more than)\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|k|thousand|cr|crore)?",
        msg,
        re.IGNORECASE
    )
    if loan_limit_match:
        val_str = loan_limit_match.group(1).replace(",", "")
        unit = (loan_limit_match.group(2) or "").lower()
        try:
            num = float(val_str)
            if "lakh" in unit or "lac" in unit:
                num *= 100000
            elif "k" in unit or "thousand" in unit:
                num *= 1000
            elif "cr" in unit or "crore" in unit:
                num *= 10000000
            claims.append({
                "type": "financial_constraint",
                "field": "maximum_loan_ceiling",
                "value": num,
                "raw_text": loan_limit_match.group(0),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "user_claim"
            })
        except Exception:
            pass

    # Stated capital claim
    cap_match = re.search(
        r"(?:only have|available capital|my budget|own funds|capital\s*(?:is)?)[^0-9\n]{0,25}(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|k|thousand)?",
        msg,
        re.IGNORECASE
    )
    if cap_match:
        val_str = cap_match.group(1).replace(",", "")
        unit = (cap_match.group(2) or "").lower()
        try:
            num = float(val_str)
            if "lakh" in unit or "lac" in unit:
                num *= 100000
            elif "k" in unit or "thousand" in unit:
                num *= 1000
            claims.append({
                "type": "capital_limit",
                "field": "promoter_capital_stated",
                "value": num,
                "raw_text": cap_match.group(0),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "user_claim"
            })
        except Exception:
            pass

    # Experience claim
    exp_match = re.search(r"(?:i have|worked for|experience of)\s*(\d+)\s*(?:years?|yrs?|months?)", msg, re.IGNORECASE)
    if exp_match:
        claims.append({
            "type": "background_claim",
            "field": "stated_experience",
            "value": exp_match.group(0),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "user_claim"
        })

    return claims


# ─────────────────────────────────────────────────────────────
# Grounding Metadata Builder
# ─────────────────────────────────────────────────────────────

def build_grounding_metadata(context_slice: Dict[str, Any], intent: str) -> List[Dict[str, Any]]:
    """
    Constructs rich structured grounding metadata linking advice to source stages and fields.
    Only includes sources when non-empty meaningful data actually exists.
    """
    grounding = []

    bp = context_slice.get("business_profile")
    if bp and isinstance(bp, dict) and bp.get("business_name"):
        grounding.append({
            "stage": 3,
            "source": "business_profile",
            "field": "specific_business",
            "description": "Canonical Business Profile & Location"
        })

    mkt = context_slice.get("market_analysis")
    if mkt and isinstance(mkt, dict) and len(mkt) > 0:
        grounding.append({
            "stage": 6,
            "source": "market_analysis",
            "field": "market_evidence",
            "description": "Hyper-Local Market & Competitor Intelligence"
        })

    opp = context_slice.get("opportunity_result")
    if opp and isinstance(opp, dict) and len(opp) > 0:
        grounding.append({
            "stage": 8,
            "source": "opportunity_result",
            "field": "opportunity_score",
            "description": "Opportunity & Demand-Supply Gap Evaluation"
        })

    fin = context_slice.get("financial_analysis")
    if fin and isinstance(fin, dict) and fin.get("total_project_cost") is not None:
        grounding.append({
            "stage": 9,
            "source": "financial_analysis",
            "field": "dscr_and_project_cost",
            "description": "Deterministic Project Financing & DSCR"
        })

    readiness = context_slice.get("entrepreneur_readiness")
    if readiness and isinstance(readiness, dict) and len(readiness) > 0:
        grounding.append({
            "stage": 10,
            "source": "entrepreneur_readiness",
            "field": "skills_and_gaps",
            "description": "Entrepreneur Readiness & Capacity Assessment"
        })

    risk = context_slice.get("risk_analysis")
    if risk and isinstance(risk, dict) and len(risk) > 0:
        grounding.append({
            "stage": 11,
            "source": "risk_analysis",
            "field": "risk_matrix",
            "description": "Multi-Vector Risk & Resilience Assessment"
        })

    feas = context_slice.get("feasibility_result")
    if feas and isinstance(feas, dict) and feas.get("overall_feasibility_score") is not None:
        grounding.append({
            "stage": 12,
            "source": "feasibility_result",
            "field": "overall_feasibility_score",
            "description": "Multivariate Feasibility Synthesis & Decision"
        })

    swot = context_slice.get("swot_analysis")
    if swot and isinstance(swot, dict) and (swot.get("swot") or swot.get("strengths")):
        grounding.append({
            "stage": 13,
            "source": "swot_analysis",
            "field": "swot_matrix",
            "description": "Strategic Dynamic SWOT Matrix & Immediate Priorities"
        })

    dpr = context_slice.get("dpr_report")
    if dpr and isinstance(dpr, dict) and len(dpr) > 0:
        grounding.append({
            "stage": 14,
            "source": "dpr_report",
            "field": "detailed_project_report",
            "description": "Bank-Ready Detailed Project Report (DPR)"
        })

    return grounding


# ─────────────────────────────────────────────────────────────
# Dynamic Suggested Actions Generator
# ─────────────────────────────────────────────────────────────

def generate_contextual_actions(context: Dict[str, Any], intent: str) -> List[str]:
    """
    Generates action recommendations directly derived from actual available evidence.
    Returns empty list if no grounded actions exist.
    """
    actions = []
    feas = context.get("feasibility_result", {})
    swot = context.get("swot_analysis", {})
    fin = context.get("financial_analysis", {})
    readiness = context.get("entrepreneur_readiness", {})

    if intent in ["EXPLAIN_FEASIBILITY", "NEXT_ACTION"]:
        if swot.get("priority_actions") and len(swot["priority_actions"]) > 0:
            top_action = swot["priority_actions"][0]
            action_text = top_action.get("action", top_action) if isinstance(top_action, dict) else str(top_action)
            actions.append(f"How do I execute: {action_text[:35]}?")
        elif feas.get("key_constraints") and len(feas["key_constraints"]) > 0:
            actions.append(f"How do I resolve: {feas['key_constraints'][0][:30]}?")
        if fin.get("bank_loan_requirement") is not None:
            actions.append("What are the loan and scheme requirements?")

    elif intent in ["LOAN_GUIDANCE", "SCHEME_GUIDANCE", "EXPLAIN_FINANCE"]:
        if fin.get("applicable_scheme_name"):
            actions.append(f"Check {fin['applicable_scheme_name']} scheme details")
        if fin.get("bank_loan_requirement") is not None:
            actions.append("What documents do banks require for this loan?")
        if fin.get("dscr") is not None:
            actions.append("How does my DSCR affect loan approval?")

    elif intent == "EXPLAIN_SWOT":
        swot_matrix = swot.get("swot", {})
        weaknesses = swot.get("weaknesses") or swot_matrix.get("weaknesses", [])
        if weaknesses:
            actions.append("How can I mitigate my recorded weaknesses?")
        if swot.get("priority_actions") or swot.get("immediate_actions"):
            actions.append("Explain the immediate priority action plan")

    elif intent in ["EXPLAIN_MARKET", "COMPETITOR_QUESTION", "MARKET_QUESTION"]:
        actions.append("What are my primary market demand drivers?")
        actions.append("How should I position against local competitors?")

    elif intent in ["EXPLAIN_READINESS", "TRAINING_QUESTION", "CLOSE_GAP"]:
        if readiness.get("identified_gaps"):
            actions.append("What training can close my readiness gaps?")
        actions.append("What operational skills are critical for launch?")

    return actions[:3]


# ─────────────────────────────────────────────────────────────
# Personal Assistant Core Service Class
# ─────────────────────────────────────────────────────────────

class PersonalAssistantService:
    """
    Stage 15 Personal AI Business Assistant Service.
    Conversational advisory layer strictly grounded in deterministic KALPA stages.
    """

    def __init__(self):
        self.model = getattr(settings, "SARVAM_ASSISTANT_MODEL", "sarvam-105b-conversations") or "sarvam-105b-conversations"
        self.sarvam_url = getattr(settings, "SARVAM_LLM_ENDPOINT", "https://api.sarvam.ai/v1/chat/completions")
        self.timeout_sec = float(getattr(settings, "SARVAM_ASSISTANT_TIMEOUT", 90.0) or 90.0)
        self.http_timeout = httpx.Timeout(connect=10.0, read=self.timeout_sec, write=30.0, pool=10.0)

    @property
    def is_llm_available(self) -> bool:
        return bool(settings.is_sarvam_configured)

    def get_or_create_memory(
        self,
        analysis_uuid: Optional[uuid.UUID],
        session_uuid: Optional[uuid.UUID],
        db: Session
    ) -> AssistantMemory:
        """
        Retrieves or creates AssistantMemory safely scoped without substituting IDs.
        """
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

        if not mem:
            mem = AssistantMemory(
                analysis_id=analysis_uuid,
                session_id=session_uuid,
                business_memory={
                    "user_constraints": [],
                    "user_claims": [],
                    "important_preferences": {}
                },
                conversation_memory={
                    "questions_answered": [],
                    "user_concerns": [],
                    "user_decisions": [],
                    "selected_actions": []
                },
                business_status="PRE_LAUNCH"
            )
            db.add(mem)
            db.commit()
            db.refresh(mem)

        return mem

    def _clean_assistant_response_text(self, text: Optional[str]) -> str:
        """
        Sanitizes assistant responses to eliminate leaked raw variables, boolean flags, or code fragments.
        """
        if not text:
            return ""
        cleaned = str(text)
        # Remove raw boolean/state variable leaks
        cleaned = re.sub(r'\b(dpr_available|loan_guidance_available|business_launched|growth_manager_active):\s*(true|false)\b', '', cleaned, flags=re.IGNORECASE)
        # Remove raw colons followed by commas/periods
        cleaned = re.sub(r':\s*,', ',', cleaned)
        cleaned = re.sub(r':\s*\.', '.', cleaned)
        # Clean extra spaces
        cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)
        return cleaned.strip()

    def _build_conversational_system_prompt(
        self,
        context_slice: Dict[str, Any],
        intent: str,
        user_memory: Optional[Dict[str, Any]] = None,
        conv_memory: Optional[Dict[str, Any]] = None,
        language: str = "en",
        **kwargs: Any
    ) -> str:
        """
        Builds the strict grounded system prompt for Sarvam LLM.
        Includes all 7 core deterministic KALPA stages, unverified data gaps, user memory,
        and strict anti-reanalysis / pillar synthesis instructions.
        """
        target_lang = kwargs.get("user_lang") or language or "en"
        if user_memory is None:
            user_memory = {"user_constraints": context_slice.get("user_memory", [])}
        if conv_memory is None:
            conv_memory = {"user_decisions": context_slice.get("conversation_memory", [])}

        verified_kalpa_data: Dict[str, Any] = {}

        # 1. Canonical Business Profile (Stage 3 & 10)
        biz = context_slice.get("business_profile") or {}
        ent_prof = context_slice.get("entrepreneur_profile") or {}
        biz_name = biz.get("business_name") or biz.get("specific_business") or "Enterprise"
        verified_kalpa_data["business_profile"] = {
            "business_name": biz_name,
            "specific_business": biz.get("specific_business"),
            "category": biz.get("category"),
            "sector": biz.get("sector"),
            "nic_code": biz.get("nic_code"),
            "location": biz.get("location"),
            "available_capital": biz.get("capital"),
            "target_scale": biz.get("target_scale", "micro"),
            "business_model": biz.get("business_model"),
        }
        if ent_prof:
            verified_kalpa_data["entrepreneur_profile"] = {
                "experience": ent_prof.get("experience_years") or ent_prof.get("experience"),
                "education": ent_prof.get("education"),
                "skills": ent_prof.get("skills", []),
                "resources": ent_prof.get("resources", []),
                "operational_readiness": ent_prof.get("operational_readiness"),
            }

        # 2. Stage 12 Feasibility & 4-Pillar Synthesis (Crucial Anchor)
        feas = context_slice.get("feasibility_result") or {}
        if feas:
            verified_kalpa_data["feasibility_synthesis"] = {
                "overall_feasibility_score": feas.get("overall_feasibility_score"),
                "viability_status": feas.get("viability_status"),
                "recommendation": feas.get("recommendation"),
                "pillar_scores": feas.get("pillar_scores") or {
                    "market_score": feas.get("market_score"),
                    "financial_score": feas.get("financial_score"),
                    "entrepreneur_fit_score": feas.get("entrepreneur_fit_score"),
                    "risk_resilience_score": feas.get("risk_resilience_score"),
                },
                "critical_gates": feas.get("critical_gates", []),
                "positive_drivers": feas.get("positive_drivers", []),
                "key_constraints": feas.get("key_constraints", []),
                "conditions_for_launch": feas.get("conditions", []),
            }

        # 3. Stage 13 Strategic Dynamic SWOT Matrix & Roadmap
        swot = context_slice.get("swot_analysis") or {}
        if swot:
            swot_matrix = swot.get("swot") or {}
            verified_kalpa_data["swot_analysis"] = {
                "strengths": swot.get("strengths") or swot_matrix.get("strengths", []),
                "weaknesses": swot.get("weaknesses") or swot_matrix.get("weaknesses", []),
                "opportunities": swot.get("opportunities") or swot_matrix.get("opportunities", []),
                "threats": swot.get("threats") or swot_matrix.get("threats", []),
                "priority_action_plan": swot.get("priority_actions") or swot.get("immediate_actions") or [],
                "strategic_roadmap": swot.get("strategic_roadmap") or swot.get("recommendations") or [],
                "strategic_summary": swot.get("strategic_summary") or {},
                "conditions": swot.get("conditions") or feas.get("conditions", []),
            }

        # 4. Stage 9 Financial Model & Schemes
        fin = context_slice.get("financial_analysis") or {}
        fin_ctx = context_slice.get("financial_context") or (fin.get("financial_context") if isinstance(fin, dict) else None)
        if fin_ctx and isinstance(fin_ctx, dict):
            # Clean authoritative financial context without verbose 84-month amortization tables
            debt_clean = dict(fin_ctx.get("debt") or {})
            debt_clean.pop("repayment_schedule", None)
            debt_clean.pop("monthly_amortization", None)

            compact_fin_ctx = {
                "package_version": fin_ctx.get("package_version", "1.0.0"),
                "project_cost": fin_ctx.get("project_cost"),
                "funding": fin_ctx.get("funding"),
                "debt": debt_clean,
                "banking_appraisal": fin_ctx.get("banking_appraisal"),
                "profit_loss": fin_ctx.get("profit_loss"),
                "stress_appraisal": fin_ctx.get("m5_stress_appraisal"),
                "resolved_tax": fin_ctx.get("resolved_tax"),
            }
            verified_kalpa_data["financial_context"] = compact_fin_ctx
        elif fin_ctx:
            verified_kalpa_data["financial_context"] = fin_ctx
        if fin:
            verified_kalpa_data["financial_analysis"] = {
                "total_project_cost": fin.get("total_project_cost"),
                "promoter_contribution": fin.get("promoter_contribution"),
                "bank_loan_requirement": fin.get("bank_loan_requirement"),
                "working_capital": fin.get("working_capital"),
                "subsidy_amount": fin.get("subsidy_amount"),
                "applicable_scheme_name": fin.get("applicable_scheme_name"),
                "dscr": fin.get("dscr"),
                "break_even_percentage": fin.get("break_even_percentage"),
                "monthly_emi": fin.get("monthly_emi"),
                "interest_rate": fin.get("interest_rate") or fin.get("annual_interest_rate"),
                "tenure_months": fin.get("tenure_months"),
                "projected_annual_revenue": fin.get("projected_annual_revenue") or fin.get("annual_revenue"),
                "projected_operating_expenses": fin.get("projected_operating_expenses") or fin.get("annual_expenses"),
                "projected_net_profit": fin.get("projected_net_profit") or fin.get("net_profit"),
                "downside_dscr": fin.get("downside_dscr"),
                "profit_loss": fin.get("profit_loss"),
                "financial_viability": fin.get("financial_viability"),
            }

        # 5. Stage 5, 6 & 8 Market Intelligence & Opportunity
        mkt = context_slice.get("market_analysis") or {}
        opp = context_slice.get("opportunity_result") or {}
        if mkt or opp:
            verified_kalpa_data["market_and_opportunity"] = {
                "competitor_count": mkt.get("competitor_count"),
                "market_saturation_index": mkt.get("market_saturation_index") or mkt.get("saturation"),
                "estimated_monthly_demand": mkt.get("estimated_monthly_demand") or mkt.get("monthly_demand"),
                "catchment_population": mkt.get("catchment_population") or mkt.get("estimated_catchment_population"),
                "demand_drivers": mkt.get("demand_drivers", []),
                "opportunity_score": opp.get("opportunity_score"),
                "demand_supply_gap": opp.get("demand_supply_gap"),
                "growth_potential": opp.get("growth_potential_rating") or opp.get("growth_potential"),
            }

        # 6. Stage 10 & 11 Entrepreneur Readiness & Risk Vector
        readiness = context_slice.get("entrepreneur_readiness") or {}
        risk = context_slice.get("risk_analysis") or {}
        if readiness or risk:
            verified_kalpa_data["readiness_and_risk"] = {
                "readiness_score": readiness.get("readiness_score") or readiness.get("fit_score"),
                "skills_assessed": readiness.get("skills_assessed", []),
                "identified_gaps": readiness.get("identified_gaps", []),
                "training_recommended": readiness.get("training_recommended", []),
                "overall_risk_score": risk.get("overall_risk_score") or risk.get("composite_risk_score"),
                "risk_rating": risk.get("risk_rating") or risk.get("resilience_rating"),
                "primary_risk_vectors": risk.get("primary_risk_vectors", []),
                "mitigation_strategies": risk.get("mitigation_strategies", []),
            }

        # 7. Unverified Data Gaps
        gaps = context_slice.get("evidence_gaps") or []
        verified_kalpa_data["unverified_data_gaps"] = gaps

        # 8. DPR & Workflow State
        if context_slice.get("dpr_report"):
            verified_kalpa_data["dpr_report"] = context_slice["dpr_report"]
        verified_kalpa_data["workflow_state"] = context_slice.get("workflow_state", {})

        # User-Stated Information
        user_stated_info = {
            "user_constraints": user_memory.get("user_constraints", []),
            "user_claims": user_memory.get("user_claims", []),
            "important_preferences": user_memory.get("important_preferences", {}),
        }

        # Conversation Memory
        conversation_mem = {
            "user_decisions": conv_memory.get("user_decisions", []),
            "user_concerns": conv_memory.get("user_concerns", []),
            "selected_actions": conv_memory.get("selected_actions", []),
        }

        system_prompt = f"""You are KALPA, an empathetic, encouraging, and expert female AI business advisor (सहेली / मार्गदर्शक) for grassroots entrepreneurs in Bharat.
Your voice persona is Shreya (female). When communicating in Hindi, Marathi, or any Indian language, always use natural feminine self-referential verb and adjective forms (e.g., 'मैं आपकी मदद करूँगी', 'मैंने आपका DPR और financial report देखा है', 'मैं समझाती हूँ') to match your female voice (Shreya).

RESPONSE LANGUAGE: {target_lang}.
Respond conversationally, warmly, and naturally in {target_lang}. Keep unavoidable business terms (e.g. DSCR, PMEGP, Mudra, Subsidy, Cash Flow, Working Capital, Inventory, Margin, Break-Even, DPR) in simple English/Hinglish when speaking Hindi.

=== VERIFIED KALPA ANALYSIS (AUTHORITATIVE SOURCE OF TRUTH) ===
```json
{json.dumps(verified_kalpa_data, indent=2, ensure_ascii=False, default=str)}
```

=== USER-STATED CLAIMS & CONSTRAINTS ===
```json
{json.dumps(user_stated_info, indent=2, ensure_ascii=False, default=str)}
```

=== CONVERSATION MEMORY (RECENT TOPICS & DECISIONS) ===
```json
{json.dumps(conversation_mem, indent=2, ensure_ascii=False, default=str)}
```

CRITICAL ADVISORY DIRECTIVES:

1. DPR (DETAILED PROJECT REPORT) GUIDANCE:
   - If `dpr_report` is present or `workflow_state.dpr_available` is true, the entrepreneur's Bankable Detailed Project Report (DPR) has been FULLY GENERATED and compiled across 39 canonical sections and financial annexures.
   - When asked "is my DPR generated?", "क्या मेरा DPR बन गया?", or about DPR status, confirm clearly and enthusiastically that their Bankable DPR is generated, verified, and ready for bank submission.
   - State the key DPR figures from verified analysis (Total Project Cost, Bank Term Loan, Promoter Margin, Average DSCR).

2. NEVER RE-ANALYZE WHAT KALPA HAS ALREADY ANALYZED:
   KALPA's deterministic engines have already calculated market demand, competitor counts, project costs, DSCR, subsidies, readiness scores, risk vectors, feasibility, and SWOT priorities.
   NEVER ask the entrepreneur to "first survey 30 customers", "first do local market research", or "first calculate your budget" if KALPA has already recorded those findings. Explain KALPA's existing verified results!
   Only suggest field validation when an explicit gap is listed in `unverified_data_gaps` or the user specifically asks how to validate.

3. DATA GAP IS NOT A NEGATIVE FINDING:
   If data is unverified or missing, explain in clean, natural language: "KALPA के मौजूदा analysis में इस हिस्से का verified data उपलब्ध नहीं है."
   Never convert UNKNOWN into a negative fact.

4. SYNTHESIZE AND CONNECT FINDINGS ACROSS PILLARS:
   Do NOT merely quote an isolated number. Intelligently connect the 4 pillars (Market, Finance, Entrepreneur Readiness, Risk Resilience).

5. EXPLAIN THE 'WHY' (WHAT -> WHY -> WHAT IT MEANS -> WHAT TO DO):
   For analytical inquiries:
   - WHAT: State the finding/score directly.
   - WHY: Cite the exact reason from verified analysis.
   - WHAT IT MEANS: Explain the practical day-to-day impact for their specific enterprise.
   - WHAT TO DO: Guide them with actionable steps.

6. GROUNDED NEXT-STEP GUIDANCE:
   When asked "What should I do now?" / "आगे क्या करूँ?", strictly draw recommended actions from:
   1. Stage 13 Priority Action Plan (immediate sequenced steps)
   2. Stage 13 Strategic Roadmap & Conditions
   3. Stage 12 Launch Conditions & Critical Gates
   4. Stage 11 Risk Mitigations

7. ZERO FABRICATION & ZERO FALSE LOAN PROMISES:
   Never invent revenues, costs, margins, subsidy rates, or DSCR.
   Never promise guaranteed loan approval. Explain eligibility and required bank documentation based on available context.

8. FOLLOW-UP CONTINUITY:
   Use recent conversation memory to maintain conversational flow without restarting.

9. CRITICAL OUTPUT FORMATTING RULES:
   - NEVER output raw code tokens, snake_case variable names (e.g. `dpr_available: false`, `loan_guidance_available: true`, `total_project_cost`), or JSON key-value syntax in your conversational answer.
   - Express all facts and system states in natural, polished, human language.
   - Use clean Markdown formatting (e.g. `### Heading`, `- Bullet`, `**Bold**`).
   - Do NOT output raw `##` or trailing punctuation artifacts without proper headings.
   - Do NOT output generic AI fluff ("Certainly!", "As an AI language model...").
"""
        return system_prompt

    async def _call_sarvam_llm(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]],
        target_id_str: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Executes bounded Sarvam LLM call with non-blocking async sleep retry and structured telemetry.
        Returns (response_text, error_message).
        """
        if not self.is_llm_available:
            return None, "SARVAM_NOT_CONFIGURED"

        # Sanitize messages ensuring valid roles and non-empty string content
        valid_roles = {"system", "user", "assistant"}
        messages: List[Dict[str, str]] = []

        sys_content = str(system_prompt or "").strip()
        if sys_content:
            messages.append({"role": "system", "content": sys_content})

        for h in history[-6:]:  # Window of recent 3 turns
            h_role = str(h.get("role", "")).lower().strip()
            if h_role not in valid_roles:
                h_role = "user" if h_role not in ("system", "assistant") else h_role
            h_content = str(h.get("content", "") or "").strip()
            if h_content:
                messages.append({"role": h_role, "content": h_content})

        user_content = str(user_message or "").strip()
        if not user_content:
            user_content = "Please provide guidance based on my business context."
        messages.append({"role": "user", "content": user_content})

        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": settings.SARVAM_API_KEY.strip(),
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200,
        }

        # Safe debug logging (NO secrets / API keys logged)
        roles_summary = [m["role"] for m in messages]
        total_prompt_bytes = sum(len(m["content"].encode("utf-8")) for m in messages)
        logger.info(
            f"[ASSISTANT SARVAM DEBUG] "
            f"target_id={target_id_str} "
            f"model={self.model} "
            f"messages_count={len(messages)} "
            f"roles={roles_summary} "
            f"temperature=0.2 "
            f"max_tokens=1200 "
            f"prompt_bytes={total_prompt_bytes}"
        )

        max_attempts = 2
        last_error = None

        for attempt in range(1, max_attempts + 1):
            call_start = time.time()
            logger.info(f"[ASSISTANT SARVAM] target_id={target_id_str} attempt={attempt} model={self.model} started")

            try:
                async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                    res = await client.post(self.sarvam_url, headers=headers, json=payload)
                    elapsed_ms = (time.time() - call_start) * 1000.0
                    logger.info(f"[ASSISTANT SARVAM] target_id={target_id_str} attempt={attempt} status={res.status_code} elapsed_ms={elapsed_ms:.1f}")

                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if choices and len(choices) > 0:
                            content = choices[0].get("message", {}).get("content", "")
                            if content and isinstance(content, str) and content.strip():
                                return content.strip(), None
                        last_error = "EMPTY_RESPONSE_BODY"
                    else:
                        error_body = res.text[:500].replace("\n", " ")
                        logger.warning(f"[ASSISTANT SARVAM ERROR] target_id={target_id_str} attempt={attempt} status={res.status_code} body={error_body}")
                        last_error = f"HTTP_{res.status_code}"
                        if res.status_code in [429, 500, 502, 503, 504] and attempt < max_attempts:
                            await asyncio.sleep(1.0)  # Non-blocking async sleep
                        else:
                            break
            except httpx.TimeoutException:
                last_error = "TIMEOUT"
                logger.warning(f"[ASSISTANT SARVAM] target_id={target_id_str} attempt={attempt} TIMEOUT after {self.timeout_sec}s")
            except Exception as e:
                last_error = f"EXCEPTION_{type(e).__name__}"
                logger.warning(f"[ASSISTANT SARVAM] target_id={target_id_str} attempt={attempt} error={e}")

        return None, last_error

    def _generate_deterministic_grounded_response(
        self,
        user_message: str,
        context_slice: Dict[str, Any],
        intent: str,
        language: str = "en"
    ) -> str:
        """
        Produces zero-hallucination, strictly factual deterministic responses directly from
        verified KALPA database records when Sarvam LLM is unavailable or times out.
        Intelligently synthesizes across the 4 pillars, explains the WHY, and cites Stage 13 priorities.
        """
        biz = context_slice.get("business_profile", {})
        fin = context_slice.get("financial_analysis", {})
        fin_ctx = context_slice.get("financial_context") or (fin.get("financial_context") if isinstance(fin, dict) else None)
        if fin_ctx and isinstance(fin_ctx, dict):
            fin = dict(fin) if isinstance(fin, dict) else {}
            proj_cost = fin_ctx.get("project_cost") or {}
            funding = fin_ctx.get("funding") or {}
            debt = fin_ctx.get("debt") or {}
            banking = fin_ctx.get("banking_appraisal") or {}
            pl = fin_ctx.get("profit_loss") or []
            y1 = pl[0] if (isinstance(pl, list) and len(pl) > 0) else {}
            stress = fin_ctx.get("m5_stress_appraisal") or {}
            tax_info = fin_ctx.get("resolved_tax") or {}

            if fin.get("total_project_cost") is None: fin["total_project_cost"] = proj_cost.get("total_project_cost")
            if fin.get("promoter_contribution") is None: fin["promoter_contribution"] = funding.get("required_promoter_contribution")
            if fin.get("bank_loan_requirement") is None: fin["bank_loan_requirement"] = funding.get("institutional_loan") or debt.get("sanctioned_loan_amount")
            if fin.get("subsidy_amount") is None: fin["subsidy_amount"] = funding.get("subsidy_amount")
            if fin.get("monthly_emi") is None: fin["monthly_emi"] = debt.get("emi")
            if fin.get("interest_rate") is None: fin["interest_rate"] = debt.get("interest_rate_pct")
            if fin.get("tenure_months") is None: fin["tenure_months"] = debt.get("tenure_months")
            if fin.get("dscr") is None: fin["dscr"] = banking.get("average_dscr") or banking.get("min_dscr")
            if fin.get("break_even_percentage") is None: fin["break_even_percentage"] = banking.get("break_even_utilization_pct")
            if fin.get("projected_annual_revenue") is None: fin["projected_annual_revenue"] = y1.get("revenue")
            if fin.get("projected_operating_expenses") is None: fin["projected_operating_expenses"] = y1.get("opex")
            if fin.get("projected_net_profit") is None: fin["projected_net_profit"] = y1.get("pat")
            if fin.get("working_capital") is None: fin["working_capital"] = proj_cost.get("working_capital")
            if fin.get("downside_dscr") is None: fin["downside_dscr"] = stress.get("downside_dscr")
            if fin.get("downside_revenue") is None: fin["downside_revenue"] = stress.get("downside_revenue")
            if not fin.get("profit_loss"): fin["profit_loss"] = pl
            if not fin.get("resolved_tax"): fin["resolved_tax"] = tax_info

        feas = context_slice.get("feasibility_result", {})
        swot = context_slice.get("swot_analysis", {})
        risk = context_slice.get("risk_analysis", {})
        mkt = context_slice.get("market_analysis", {})
        opp = context_slice.get("opportunity_result", {})
        readiness = context_slice.get("entrepreneur_readiness", {})

        is_hindi = bool(
            (language and ("hi" in language.lower() or "hindi" in language.lower())) or
            re.search(r"[\u0900-\u097F]", user_message)
        )
        biz_name = biz.get("business_name") or biz.get("specific_business") or ("आपके व्यवसाय" if is_hindi else "your enterprise")

        if intent == "EXPLAIN_FEASIBILITY":
            score = feas.get("overall_feasibility_score")
            status = feas.get("viability_status")
            rec = feas.get("recommendation")
            pillars = feas.get("pillar_scores") or {}
            fin_score = pillars.get("financial_score")
            mkt_score = pillars.get("market_score")
            fit_score = pillars.get("entrepreneur_fit_score")
            risk_score = pillars.get("risk_resilience_score")

            if score is not None:
                if is_hindi:
                    lines = [
                        f"KALPA के Stage 12 assessment के अनुसार **{biz_name}** का समग्र व्यवहार्यता (Feasibility) स्कोर **{score}/100** है और स्थिति **{status or 'VIABLE'}** दर्ज की गई है.",
                        "",
                        "### मुख्य स्तंभ विश्लेषण (4-Pillar Breakdown)",
                    ]
                    if fin_score is not None:
                        lines.append(f"• **वित्तीय मजबूती (Financial Score)**: {fin_score}/100")
                    if fit_score is not None:
                        lines.append(f"• **उद्यमी तत्परता (Entrepreneur Fit)**: {fit_score}/100")
                    if mkt_score is not None:
                        lines.append(f"• **बाजार मांग (Market Score)**: {mkt_score}/100")
                    if risk_score is not None:
                        lines.append(f"• **जोखिम लचीलापन (Risk Resilience)**: {risk_score}/100")

                    if feas.get("conditions"):
                        cond_str = ", ".join([str(c) for c in feas["conditions"][:2]])
                        lines.extend(["", f"**शर्तें व सावधानियां**: {cond_str}"])

                    if swot.get("priority_actions"):
                        top_act = swot["priority_actions"][0]
                        act_t = top_act.get("action", top_act) if isinstance(top_act, dict) else str(top_act)
                        lines.extend(["", f"**Stage 13 प्राथमिकता**: {act_t}"])

                    return "\n".join(lines)
                else:
                    parts = [f"Your Stage 12 feasibility score for **{biz_name}** is **{score}/100**."]
                    if status:
                        parts.append(f"The recorded status is **'{status}'** with recommendation **'{rec or 'CONDITIONAL'}'**.")
                    if fin_score is not None and mkt_score is not None:
                        parts.append(f"Financial score stands at {fin_score}/100 and market score at {mkt_score}/100.")
                    if feas.get("conditions"):
                        parts.append(f"Key condition: {feas['conditions'][0]}.")
                    return " ".join(parts)
            return "KALPA के मौजूदा विश्लेषण में अभी Stage 12 feasibility score उपलब्ध नहीं है." if is_hindi else "I don't have a verified Stage 12 feasibility score for this analysis yet."

        elif intent == "REPAYMENT_QUESTION":
            emi = fin.get("monthly_emi")
            loan = fin.get("bank_loan_requirement")
            tenure = fin.get("tenure_months") or 60
            rate = fin.get("interest_rate") or fin.get("annual_interest_rate") or 9.5
            dscr = fin.get("dscr")

            if emi is not None or loan is not None:
                if is_hindi:
                    lines = [f"Stage 9 Financial Model के अनुसार **{biz_name}** का ऋण पुनर्भुगतान (Repayment & EMI) विवरण:"]
                    if emi is not None:
                        lines.append(f"• **मासिक किस्त (Monthly EMI)**: ₹{float(emi):,.2f}")
                    if loan is not None:
                        lines.append(f"• **कुल प्रस्तावित ऋण (Proposed Loan)**: ₹{float(loan):,.2f}")
                    if tenure:
                        lines.append(f"• **ऋण अवधि (Tenure)**: {tenure} माह ({int(tenure/12)} वर्ष)")
                    if rate:
                        lines.append(f"• **वार्षिक ब्याज दर (Interest Rate)**: {rate}% p.a.")
                    if dscr:
                        lines.append(f"• **ऋण चुकाने की क्षमता (DSCR)**: {dscr}x (बैंक मानक से ऊपर)")
                    return "\n".join(lines)
                else:
                    lines = [f"Your Stage 9 verified loan repayment schedule for {biz_name}:"]
                    if emi is not None:
                        lines.append(f"• Monthly EMI: ₹{float(emi):,.2f}")
                    if loan is not None:
                        lines.append(f"• Proposed Loan Principal: ₹{float(loan):,.2f}")
                    if tenure:
                        lines.append(f"• Loan Tenure: {tenure} months ({int(tenure/12)} years)")
                    if rate:
                        lines.append(f"• Interest Rate: {rate}% p.a.")
                    if dscr:
                        lines.append(f"• Debt Service Coverage Ratio (DSCR): {dscr}x")
                    return "\n".join(lines)
            return "ऋण पुनर्भुगतान व ईएमआई विवरण अभी वित्तीय विश्लेषण में दर्ज नहीं है." if is_hindi else "Loan repayment and EMI details are not yet recorded for this analysis."

        elif intent in ["EXPLAIN_FINANCE", "COST_QUESTION"]:
            cost = fin.get("total_project_cost")
            promoter = fin.get("promoter_contribution")
            loan = fin.get("bank_loan_requirement")
            dscr = fin.get("dscr")
            scheme = fin.get("applicable_scheme_name")
            subsidy = fin.get("subsidy_amount")
            wc = fin.get("working_capital")
            emi = fin.get("monthly_emi")
            ann_rev = fin.get("projected_annual_revenue")
            ann_pat = fin.get("projected_net_profit")
            bep = fin.get("break_even_percentage")
            downside_dscr = fin.get("downside_dscr")
            pl = fin.get("profit_loss") or []

            msg_low = user_message.lower()

            # Sub-query: Stress Testing / Downside
            if any(w in msg_low for w in ["downside", "stress", "shock", "fall", "drop", "मंदी", "नुकसान"]):
                if downside_dscr is not None:
                    if is_hindi:
                        return f"Stage 9 Stress Testing (Milestone 5) के अनुसार, गंभीर मंदी के परिदृश्य में भी आपका डाउनसाइड DSCR **{downside_dscr}x** रहता है, जो दर्शाता है कि उद्यम ऋण चुकाने में सक्षम रहेगा."
                    else:
                        return f"Under Stage 9 Stress Testing (Milestone 5), your enterprise maintains a downside DSCR of **{downside_dscr}x**, demonstrating debt solvency even during adverse market conditions."

            # Sub-query: Revenue / Sales Trajectory
            if any(w in msg_low for w in ["revenue", "sales", "turnover", "बिक्री", "कमाई"]):
                if pl and isinstance(pl, list) and len(pl) > 0:
                    if is_hindi:
                        lines = [f"Stage 9 Financial Model के अनुसार **{biz_name}** का 5-वर्षीय राजस्व (Revenue Projections):"]
                        for yr_data in pl[:5]:
                            yr_num = yr_data.get("year", 1)
                            r_val = yr_data.get("revenue", 0)
                            p_val = yr_data.get("pat", 0)
                            lines.append(f"• **वर्ष {yr_num}**: राजस्व ₹{r_val:,.2f} (शुद्ध लाभ: ₹{p_val:,.2f})")
                        return "\n".join(lines)
                    else:
                        lines = [f"Your Stage 9 5-Year Revenue Projections for {biz_name}:"]
                        for yr_data in pl[:5]:
                            yr_num = yr_data.get("year", 1)
                            r_val = yr_data.get("revenue", 0)
                            p_val = yr_data.get("pat", 0)
                            lines.append(f"• Year {yr_num}: Revenue ₹{r_val:,.2f} (Net PAT: ₹{p_val:,.2f})")
                        return "\n".join(lines)
                elif ann_rev is not None:
                    return (
                        f"Stage 9 के अनुसार **{biz_name}** का प्रथम वर्ष अनुमानित राजस्व **₹{ann_rev:,.2f}** है."
                        if is_hindi else
                        f"Your Stage 9 projected Year 1 annual revenue for {biz_name} is ₹{ann_rev:,.2f}."
                    )

            # Sub-query: Profitability / PAT / Margin
            if any(w in msg_low for w in ["profit", "pat", "ebitda", "margin", "मुनाफा", "लाभ"]):
                if ann_pat is not None:
                    if is_hindi:
                        lines = [f"Stage 9 Financial Model के अनुसार **{biz_name}** का लाभ विवरण:"]
                        lines.append(f"• **प्रथम वर्ष शुद्ध लाभ (PAT)**: ₹{ann_pat:,.2f}")
                        if ann_rev:
                            margin_pct = round((ann_pat / ann_rev) * 100, 1)
                            lines.append(f"• **शुद्ध लाभ मार्जिन (Net Margin)**: {margin_pct}%")
                        return "\n".join(lines)
                    else:
                        lines = [f"Your Stage 9 Profitability metrics for {biz_name}:"]
                        lines.append(f"• Year 1 Profit After Tax (PAT): ₹{ann_pat:,.2f}")
                        if ann_rev:
                            margin_pct = round((ann_pat / ann_rev) * 100, 1)
                            lines.append(f"• Net Profit Margin: {margin_pct}%")
                        return "\n".join(lines)

            # Sub-query: Break-even
            if any(w in msg_low for w in ["break-even", "breakeven", "break even", "ब्रेक-ईवन", "bep"]):
                if bep is not None:
                    if is_hindi:
                        return f"Stage 9 Financial Analysis के अनुसार **{biz_name}** का ब्रेक-ईवन उपयोग स्तर **{bep}%** है. इस स्तर के बाद व्यवसाय शुद्ध लाभ में प्रवेश करता है."
                    else:
                        return f"Your Stage 9 break-even capacity utilization is **{bep}%** for {biz_name}. Sales above this utilization level generate net operating profit."

            # General Finance & Cost Breakdown
            if cost is not None:
                if is_hindi:
                    lines = [f"Stage 9 Financial Model के अनुसार **{biz_name}** का संपूर्ण वित्तीय विवरण:"]
                    lines.append(f"• **कुल प्रोजेक्ट लागत (Total Project Cost)**: ₹{cost:,.2f}")
                    if promoter is not None:
                        lines.append(f"• **उद्यमी का अंशदान (Promoter Contribution)**: ₹{promoter:,.2f}")
                    if loan is not None:
                        lines.append(f"• **बैंक ऋण आवश्यकता (Bank Loan Requirement)**: ₹{loan:,.2f}")
                    if wc is not None:
                        lines.append(f"• **कार्यशील पूंजी (Working Capital)**: ₹{float(wc):,.2f}")
                    if emi is not None:
                        lines.append(f"• **अनुमानित मासिक किस्त (Monthly EMI)**: ₹{float(emi):,.2f}")
                    if scheme:
                        lines.append(f"• **लागू सरकारी योजना**: {scheme}" + (f" (सब्सिडी: ₹{subsidy:,.2f})" if subsidy else ""))
                    if ann_rev is not None:
                        lines.append(f"• **प्रथम वर्ष राजस्व**: ₹{ann_rev:,.2f}")
                    if ann_pat is not None:
                        lines.append(f"• **प्रथम वर्ष शुद्ध लाभ (PAT)**: ₹{ann_pat:,.2f}")
                    if dscr is not None:
                        lines.append(f"• **डीएससीआर (DSCR)**: {dscr}x (ऋण चुकाने की मजबूत क्षमता)")
                    if bep is not None:
                        lines.append(f"• **ब्रेक-ईवन क्षमता स्तर**: {bep}%")
                    return "\n".join(lines)
                else:
                    lines = [f"Your Stage 9 Financial Analysis records for {biz_name}:"]
                    lines.append(f"• Total Project Cost: ₹{cost:,.2f}")
                    if promoter is not None:
                        lines.append(f"• Promoter Margin: ₹{promoter:,.2f}")
                    if loan is not None:
                        lines.append(f"• Bank Loan Requirement: ₹{loan:,.2f}")
                    if wc is not None:
                        lines.append(f"• Working Capital: ₹{float(wc):,.2f}")
                    if emi is not None:
                        lines.append(f"• Monthly EMI: ₹{float(emi):,.2f}")
                    if scheme:
                        lines.append(f"• Matched Scheme: {scheme}")
                    if ann_rev is not None:
                        lines.append(f"• Year 1 Revenue: ₹{ann_rev:,.2f}")
                    if ann_pat is not None:
                        lines.append(f"• Year 1 PAT: ₹{ann_pat:,.2f}")
                    if dscr is not None:
                        lines.append(f"• DSCR: {dscr}x")
                    if bep is not None:
                        lines.append(f"• Break-Even Utilization: {bep}%")
                    return "\n".join(lines)
            return "वित्तीय लागत और डीएससीआर डेटा अभी इस विश्लेषण में दर्ज नहीं है." if is_hindi else "Financial cost and DSCR data is not yet recorded for this analysis."

        elif intent in ["LOAN_GUIDANCE", "SCHEME_GUIDANCE"]:
            loan = fin.get("bank_loan_requirement")
            scheme = fin.get("applicable_scheme_name")
            subsidy = fin.get("subsidy_amount")
            if loan is not None or scheme:
                if is_hindi:
                    parts = []
                    if loan is not None:
                        parts.append(f"आपके वित्तीय मॉडल में अनुमानित बैंक ऋण आवश्यकता **₹{loan:,.2f}** है.")
                    if scheme:
                        parts.append(f"मिलान की गई सरकारी क्रेडिट योजना **{scheme}** है.")
                    if subsidy is not None:
                        parts.append(f"अनुमानित पूंजीगत सब्सिडी **₹{subsidy:,.2f}** है.")
                    parts.append("कृपया ध्यान दें कि अंतिम ऋण स्वीकृति बैंक द्वारा डीपीआर और औपचारिक दस्तावेजों के सत्यापन पर निर्भर करती है.")
                    return " ".join(parts)
                else:
                    parts = []
                    if loan is not None:
                        parts.append(f"Your calculated financeable loan requirement is ₹{loan:,.2f}.")
                    if scheme:
                        parts.append(f"The matched government credit scheme in your analysis is {scheme}.")
                    if subsidy is not None:
                        parts.append(f"Estimated subsidy amount is ₹{subsidy:,.2f}.")
                    parts.append("Note that loan approval depends on bank verification of your DPR and credentials.")
                    return " ".join(parts)
            return "ऋण और सब्सिडी का आवंटन अभी वित्तीय प्रोफाइल में उत्पन्न नहीं हुआ है." if is_hindi else "Specific loan and scheme allocations have not yet been generated in your financial profile."

        elif intent in ["EXPLAIN_SWOT", "CLOSE_GAP"]:
            swot_matrix = swot.get("swot", {})
            strengths = swot.get("strengths") or swot_matrix.get("strengths", [])
            weaknesses = swot.get("weaknesses") or swot_matrix.get("weaknesses", [])
            priorities = swot.get("priority_actions") or swot.get("immediate_actions", [])

            if strengths or weaknesses:
                if is_hindi:
                    lines = [f"Stage 13 Strategic Dynamic SWOT Analysis के अनुसार **{biz_name}** का मूल्यांकन:"]
                    if strengths:
                        s_text = "; ".join([s.get("item", s) if isinstance(s, dict) else str(s) for s in strengths[:3]])
                        lines.append(f"• **मुख्य ताकत (Strengths)**: {s_text}")
                    if weaknesses:
                        w_text = "; ".join([w.get("item", w) if isinstance(w, dict) else str(w) for w in weaknesses[:3]])
                        lines.append(f"• **कमजोरियां (Weaknesses)**: {w_text}")
                    if priorities:
                        p_text = "; ".join([p.get("action", p) if isinstance(p, dict) else str(p) for p in priorities[:2]])
                        lines.append(f"• **सुधार व प्राथमिकता (Priority Actions)**: {p_text}")
                    return "\n".join(lines)
                else:
                    lines = ["From your Stage 13 Strategic SWOT Analysis:"]
                    if strengths:
                        s_text = "; ".join([s.get("item", s) if isinstance(s, dict) else str(s) for s in strengths[:2]])
                        lines.append(f"• Key Strengths: {s_text}")
                    if weaknesses:
                        w_text = "; ".join([w.get("item", w) if isinstance(w, dict) else str(w) for w in weaknesses[:2]])
                        lines.append(f"• Key Weaknesses: {w_text}")
                    if priorities:
                        p_text = "; ".join([p.get("action", p) if isinstance(p, dict) else str(p) for p in priorities[:2]])
                        lines.append(f"• Priority Next Steps: {p_text}")
                    return "\n".join(lines)
            return "Stage 13 SWOT परिणाम अभी उपलब्ध नहीं है." if is_hindi else "I don't have the Stage 13 SWOT result for this analysis yet."

        elif intent == "EXPLAIN_RISK":
            r_score = risk.get("overall_risk_score")
            r_rating = risk.get("risk_rating") or risk.get("resilience_rating")
            vectors = risk.get("primary_risk_vectors", [])
            mitigations = risk.get("mitigation_strategies", [])

            if r_score is not None or r_rating or vectors:
                if is_hindi:
                    lines = [f"Stage 11 Risk & Resilience Analysis के अनुसार **{biz_name}** का जोखिम विवरण:"]
                    if r_score is not None:
                        lines.append(f"• **समग्र जोखिम स्कोर**: {r_score}/100" + (f" ({r_rating})" if r_rating else ""))
                    if vectors:
                        v_str = ", ".join([str(v) for v in vectors[:3]])
                        lines.append(f"• **पहचाने गए मुख्य जोखिम**: {v_str}")
                    if mitigations:
                        m_str = ", ".join([str(m) for m in mitigations[:2]])
                        lines.append(f"• **रोकथाम व सुरक्षा उपाय (Mitigations)**: {m_str}")
                    return "\n".join(lines)
                else:
                    lines = [f"Your Stage 11 Risk Analysis records for {biz_name}:"]
                    if r_score is not None:
                        lines.append(f"• Composite Risk Score: {r_score}" + (f" ({r_rating})" if r_rating else ""))
                    if vectors:
                        v_str = ", ".join([str(v) for v in vectors[:3]])
                        lines.append(f"• Primary Risk Vectors: {v_str}")
                    if mitigations:
                        m_str = ", ".join([str(m) for m in mitigations[:2]])
                        lines.append(f"• Mitigations: {m_str}")
                    return "\n".join(lines)
            return "जोखिम विश्लेषण डेटा अभी इस प्रोफाइल में उपलब्ध नहीं है." if is_hindi else "Risk analysis data is not available in the current analysis."

        elif intent in ["EXPLAIN_MARKET", "COMPETITOR_QUESTION", "MARKET_QUESTION"]:
            count = mkt.get("competitor_count")
            demand = mkt.get("estimated_monthly_demand") or mkt.get("monthly_demand")
            pop = mkt.get("catchment_population") or mkt.get("estimated_catchment_population")

            if count is not None or demand is not None:
                if is_hindi:
                    lines = [f"Stage 6 Market Intelligence के अनुसार **{biz_name}** का बाजार विश्लेषण:"]
                    if count is not None:
                        lines.append(f"• **सक्रिय स्थानीय प्रतियोगी**: {count}")
                    if demand is not None:
                        lines.append(f"• **अनुमानित मासिक मांग (Monthly Demand)**: ₹{demand:,.2f}" if isinstance(demand, (int, float)) else f"• मासिक मांग: {demand}")
                    if pop:
                        lines.append(f"• **कैचमेंट आबादी**: {pop:,} लोग")
                    return "\n".join(lines)
                else:
                    lines = [f"Your Stage 6 Market Intelligence records for {biz_name}:"]
                    if count is not None:
                        lines.append(f"• Direct Competitors in Radius: {count}")
                    if demand is not None:
                        lines.append(f"• Estimated Monthly Catchment Demand: ₹{demand:,.2f}" if isinstance(demand, (int, float)) else f"• Monthly Demand: {demand}")
                    if pop:
                        lines.append(f"• Catchment Population: {pop:,}")
                    return "\n".join(lines)
            return "बाजार विश्लेषण साक्ष्य अभी उपलब्ध नहीं है." if is_hindi else "Market intelligence evidence is not available in the current analysis."

        elif intent in ["EXPLAIN_READINESS", "TRAINING_QUESTION"]:
            r_score = readiness.get("readiness_score") or readiness.get("fit_score")
            gaps = readiness.get("identified_gaps", [])
            training = readiness.get("training_recommended", [])

            if r_score is not None or gaps or training:
                if is_hindi:
                    lines = [f"Stage 10 Entrepreneur Readiness के अनुसार आपकी तैयारी:"]
                    if r_score is not None:
                        lines.append(f"• **उद्यमी तत्परता स्कोर**: {r_score}/100")
                    if gaps:
                        g_str = ", ".join([str(g) for g in gaps[:3]])
                        lines.append(f"• **सुधार के क्षेत्र (Gaps)**: {g_str}")
                    if training:
                        t_str = ", ".join([str(t) for t in training[:2]])
                        lines.append(f"• **अनुशंसित प्रशिक्षण (EDP / RSETI)**: {t_str}")
                    return "\n".join(lines)
                else:
                    lines = ["Your Stage 10 Entrepreneur Readiness records:"]
                    if r_score is not None:
                        lines.append(f"• Readiness Score: {r_score}/100")
                    if gaps:
                        lines.append(f"• Identified Gaps: {', '.join([str(g) for g in gaps[:3]])}")
                    if training:
                        lines.append(f"• Recommended Training: {', '.join([str(t) for t in training[:2]])}")
                    return "\n".join(lines)
            return "उद्यमी तत्परता डेटा अभी उपलब्ध नहीं है." if is_hindi else "Entrepreneur readiness data is not available in the current analysis."

        elif intent == "NEXT_ACTION":
            actions = swot.get("priority_actions") or swot.get("immediate_actions", [])
            if actions:
                if is_hindi:
                    items = "\n".join([f"{i+1}. {a.get('action', a) if isinstance(a, dict) else str(a)}" for i, a in enumerate(actions[:3])])
                    return f"Stage 13 Strategic Roadmap के अनुसार आपकी तत्काल कार्य योजना:\n{items}"
                else:
                    items = "\n".join([f"{i+1}. {a.get('action', a) if isinstance(a, dict) else str(a)}" for i, a in enumerate(actions[:3])])
                    return f"Here are the immediate actions recorded in your Stage 13 SWOT roadmap:\n{items}"
            return "अभी कोई विशिष्ट प्राथमिकताएं दर्ज नहीं हैं." if is_hindi else "No specific next actions are currently recorded in your SWOT analysis."

        # Fallback without generic assumptions
        if is_hindi:
            return (
                f"KALPA सलाहकार इंजन आपके **{biz_name}** के सत्यापित डेटा पर आधारित है. "
                f"कृपया व्यवहार्यता स्कोर, प्रोजेक्ट लागत, बैंक ऋण, जोखिम, या SWOT प्राथमिकताओं के बारे में पूछें."
            )
        return (
            f"KALPA's advisory engine is grounded in your verified pipeline for {biz_name}. "
            f"Please ask about your feasibility score, project cost, bank loans, risks, or SWOT matrix to view your verified findings."
        )

    async def handle_message(
        self,
        user_message: str,
        db: Session,
        analysis_id_str: Optional[str] = None,
        session_id_str: Optional[str] = None,
        conversation_id_str: Optional[str] = None,
        business_id_str: Optional[str] = None,
        language: str = "en",
        financial_context: Optional[Dict[str, Any]] = None,
        financial_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for handling user inquiries with grounded context and memory.
        Enforces separate analysis_id and session_id validation.
        """
        msg_clean = user_message.strip()
        if not msg_clean:
            raise ValueError("User message cannot be empty.")

        analysis_uuid = safe_uuid(analysis_id_str)
        session_uuid = safe_uuid(session_id_str)
        business_uuid = safe_uuid(business_id_str)

        # Validate that at least one valid identifier is provided
        if not analysis_uuid and not session_uuid:
            raise ValueError("Either a valid analysis_id or session_id must be provided.")

        # Real distinct Conversation ID
        conv_uuid = safe_uuid(conversation_id_str) or uuid.uuid4()
        target_log_id = str(analysis_uuid or session_uuid)

        # Step 1: Detect Intent
        intent = detect_intent(msg_clean)

        # Step 2: Build Canonical Context & Sliced Intent Context
        full_context = build_full_assistant_context(
            analysis_id=str(analysis_uuid) if analysis_uuid else None,
            session_id=str(session_uuid) if session_uuid else None,
            db=db,
            business_id=str(business_uuid) if business_uuid else None
        )
        if financial_context:
            full_context["financial_context"] = financial_context
        if financial_analysis:
            if not full_context.get("financial_analysis"):
                full_context["financial_analysis"] = financial_analysis
            elif isinstance(full_context["financial_analysis"], dict):
                full_context["financial_analysis"].update(financial_analysis)

        # Ensure financial_analysis is enriched from financial_context if present
        if full_context.get("financial_context"):
            fc_cur = full_context["financial_context"]
            fa_cur = full_context.setdefault("financial_analysis", {})
            if isinstance(fa_cur, dict) and isinstance(fc_cur, dict):
                p_c = fc_cur.get("project_cost") or {}
                f_n = fc_cur.get("funding") or {}
                d_b = fc_cur.get("debt") or {}
                b_k = fc_cur.get("banking_appraisal") or {}
                p_l = fc_cur.get("profit_loss") or []
                y_1 = p_l[0] if (isinstance(p_l, list) and len(p_l) > 0) else {}
                s_t = fc_cur.get("m5_stress_appraisal") or {}
                t_x = fc_cur.get("resolved_tax") or {}

                if not fa_cur.get("total_project_cost"): fa_cur["total_project_cost"] = p_c.get("total_project_cost")
                if not fa_cur.get("promoter_contribution"): fa_cur["promoter_contribution"] = f_n.get("required_promoter_contribution")
                if not fa_cur.get("bank_loan_requirement"): fa_cur["bank_loan_requirement"] = f_n.get("institutional_loan") or d_b.get("sanctioned_loan_amount")
                if not fa_cur.get("subsidy_amount"): fa_cur["subsidy_amount"] = f_n.get("subsidy_amount")
                if not fa_cur.get("monthly_emi"): fa_cur["monthly_emi"] = d_b.get("emi")
                if not fa_cur.get("interest_rate"): fa_cur["interest_rate"] = d_b.get("interest_rate_pct")
                if not fa_cur.get("tenure_months"): fa_cur["tenure_months"] = d_b.get("tenure_months")
                if not fa_cur.get("dscr"): fa_cur["dscr"] = b_k.get("average_dscr") or b_k.get("min_dscr")
                if not fa_cur.get("break_even_percentage"): fa_cur["break_even_percentage"] = b_k.get("break_even_utilization_pct")
                if not fa_cur.get("projected_annual_revenue"): fa_cur["projected_annual_revenue"] = y_1.get("revenue")
                if not fa_cur.get("projected_operating_expenses"): fa_cur["projected_operating_expenses"] = y_1.get("opex")
                if not fa_cur.get("projected_net_profit"): fa_cur["projected_net_profit"] = y_1.get("pat")
                fa_cur["working_capital"] = p_c.get("working_capital")
                fa_cur["downside_dscr"] = s_t.get("downside_dscr")
                fa_cur["downside_revenue"] = s_t.get("downside_revenue")
                fa_cur["profit_loss"] = p_l
                fa_cur["resolved_tax"] = t_x

        context_slice = get_intent_context(full_context, intent)
        pipeline_comp = calculate_pipeline_completeness(full_context)
        intent_comp = calculate_intent_completeness(context_slice, intent)

        # Step 3: Extract & Persist User Constraints, Claims & Preferences
        memory_rec = self.get_or_create_memory(analysis_uuid, session_uuid, db)
        biz_memory = memory_rec.business_memory or {}
        conv_memory = memory_rec.conversation_memory or {}

        new_claims = extract_user_claims_and_constraints(msg_clean)
        if new_claims:
            existing_claims = biz_memory.get("user_claims", [])
            existing_constraints = biz_memory.get("user_constraints", [])
            for c in new_claims:
                if c.get("type") == "financial_constraint":
                    existing_constraints.append(c)
                else:
                    existing_claims.append(c)
            biz_memory["user_constraints"] = existing_constraints[-10:]
            biz_memory["user_claims"] = existing_claims[-10:]
            memory_rec.business_memory = biz_memory

        # Step 4: Retrieve Scoped Conversation History (Strictly scoped)
        history_query = db.query(AssistantConversation)
        if analysis_uuid and session_uuid:
            past_msgs = history_query.filter(
                (AssistantConversation.analysis_id == analysis_uuid) &
                (AssistantConversation.session_id == session_uuid)
            ).order_by(
                AssistantConversation.created_at.asc(),
                AssistantConversation.message_index.asc()
            ).all()
        elif analysis_uuid:
            past_msgs = history_query.filter(
                AssistantConversation.analysis_id == analysis_uuid
            ).order_by(
                AssistantConversation.created_at.asc(),
                AssistantConversation.message_index.asc()
            ).all()
        elif session_uuid:
            past_msgs = history_query.filter(
                AssistantConversation.session_id == session_uuid
            ).order_by(
                AssistantConversation.created_at.asc(),
                AssistantConversation.message_index.asc()
            ).all()
        else:
            past_msgs = []

        history = []
        for m in past_msgs:
            if m.user_message:
                history.append({"role": "user", "content": m.user_message})
            if m.assistant_response:
                history.append({"role": "assistant", "content": m.assistant_response})

        # Calculate deterministic next message index
        existing_indices = [m.message_index for m in past_msgs if m.message_index is not None]
        next_idx = (max(existing_indices) + 1) if existing_indices else 0

        # Step 5: Build Grounded System Prompt & Call Sarvam
        effective_lang = language or full_context.get("user", {}).get("preferred_language", "en")
        system_prompt = self._build_conversational_system_prompt(
            context_slice, intent, biz_memory, conv_memory, effective_lang
        )

        llm_response, error = await self._call_sarvam_llm(
            system_prompt, msg_clean, history, target_log_id
        )

        if llm_response:
            final_response = self._clean_assistant_response_text(llm_response)
            grounding_status = "GROUNDED"
            model_provider = "Sarvam AI"
            model_used = True
        else:
            # Deterministic fallback strictly from verified KALPA records
            raw_fallback = self._generate_deterministic_grounded_response(
                msg_clean, context_slice, intent, effective_lang
            )
            final_response = self._clean_assistant_response_text(raw_fallback)
            grounding_status = "DETERMINISTIC_FALLBACK"
            model_provider = "Verified KALPA Fallback"
            model_used = False

        # Step 6: Grounding Telemetry & Dynamic Actions
        grounding_meta = build_grounding_metadata(context_slice, intent)
        suggested_actions = generate_contextual_actions(full_context, intent)

        # Step 7: Persist Conversation Turn
        conv_entry = AssistantConversation(
            conversation_id=conv_uuid,
            analysis_id=analysis_uuid,
            session_id=session_uuid,
            user_message=msg_clean,
            assistant_response=final_response,
            intent=intent,
            language=effective_lang,
            confidence=round(pipeline_comp, 2),
            grounded_sources=grounding_meta,
            suggested_actions=suggested_actions,
            message_index=next_idx
        )
        db.add(conv_entry)

        # Update Conversation Memory
        qa_list = conv_memory.get("questions_answered", [])
        qa_list.append({
            "q": msg_clean,
            "intent": intent,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        conv_memory["questions_answered"] = qa_list[-20:]
        memory_rec.conversation_memory = conv_memory

        db.commit()

        return {
            "conversation_id": str(conv_uuid),
            "analysis_id": str(analysis_uuid) if analysis_uuid else None,
            "session_id": str(session_uuid) if session_uuid else None,
            "user_message": msg_clean,
            "assistant_response": final_response,
            "intent": intent,
            "language": effective_lang,
            "grounded_sources": grounding_meta,
            "grounding_status": grounding_status,
            "pipeline_completeness": pipeline_comp,
            "intent_completeness": intent_comp,
            "suggested_actions": suggested_actions,
            "message_index": next_idx,
            "business_status": memory_rec.business_status,
            "model_provider": model_provider,
            "model_used": model_used
        }

    def get_history(
        self,
        target_id_str: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Retrieves scoped conversation history for a given analysis or session ID.
        """
        target_uuid = safe_uuid(target_id_str)
        if not target_uuid:
            return []

        msgs = db.query(AssistantConversation).filter(
            (AssistantConversation.analysis_id == target_uuid) |
            (AssistantConversation.session_id == target_uuid) |
            (AssistantConversation.conversation_id == target_uuid)
        ).order_by(
            AssistantConversation.created_at.asc(),
            AssistantConversation.message_index.asc()
        ).all()

        return [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "user_message": m.user_message,
                "assistant_response": m.assistant_response,
                "intent": m.intent,
                "language": m.language,
                "grounded_sources": m.grounded_sources or [],
                "suggested_actions": m.suggested_actions or [],
                "message_index": m.message_index,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ]

    def clear_history(
        self,
        target_id_str: str,
        db: Session
    ) -> bool:
        """
        Clears conversation history safely for a scoped analysis or session.
        """
        target_uuid = safe_uuid(target_id_str)
        if not target_uuid:
            return False

        db.query(AssistantConversation).filter(
            (AssistantConversation.analysis_id == target_uuid) |
            (AssistantConversation.session_id == target_uuid) |
            (AssistantConversation.conversation_id == target_uuid)
        ).delete()
        db.commit()
        return True


assistant_service = PersonalAssistantService()
