"""
Hybrid Decision Engine & Deterministic Workflow Planner for Stage 4 Orchestrator.
Combines 6-factor explainable deterministic confidence scoring with optional
Groq LLM escalation for ambiguous or conflicting business contexts.
"""
import json
from typing import Dict, Any, List, Tuple
from app.services.llm_client import llm_client
from app.services.classification.ontology_service import ontology_service
from app.core.logging import logger


class HybridPlanner:
    def __init__(self):
        self.confidence_threshold = 0.75

    def calculate_deterministic_confidence(self, profile: Dict[str, Any]) -> Tuple[float, Dict[str, float], str]:
        """
        Calculates an explainable 6-factor confidence score for workflow routing.
        """
        dq = profile.get("data_quality", {})
        bus = profile.get("business_profile", {})
        loc = profile.get("location_profile", {})
        fin = profile.get("financial_profile", {})

        # Factor 1: Profile Completeness (25%)
        is_complete = dq.get("profile_complete", True)
        missing_count = len(dq.get("missing_fields", []))
        profile_completeness_score = 1.0 if is_complete else max(0.2, 1.0 - (missing_count * 0.25))

        # Factor 2: Location Quality (20%)
        district = loc.get("district") or loc.get("name")
        state = loc.get("state")
        if district and state:
            location_quality_score = 1.0
        elif district or state:
            location_quality_score = 0.7
        else:
            location_quality_score = 0.3

        # Factor 3: Classification Confidence (25%)
        nic = bus.get("nic", {})
        classification_confidence = float(nic.get("confidence") or 0.90)

        # Factor 4: Financial Data Availability (15%)
        cap = fin.get("available_capital")
        financial_data_score = 1.0 if cap is not None and cap > 0 else 0.6

        # Factor 5: Knowledge Coverage (15%)
        spec_bus = bus.get("specific_business") or bus.get("category", "")
        ontology_node = ontology_service.get_node_by_concept(spec_bus)
        knowledge_coverage_score = 1.0 if ontology_node else 0.75

        # Weighted combination
        confidence = (
            0.25 * profile_completeness_score +
            0.20 * location_quality_score +
            0.25 * classification_confidence +
            0.15 * financial_data_score +
            0.15 * knowledge_coverage_score
        )
        confidence = round(confidence, 4)

        factors = {
            "profile_completeness": round(profile_completeness_score, 2),
            "location_quality": round(location_quality_score, 2),
            "classification_confidence": round(classification_confidence, 2),
            "financial_data_available": round(financial_data_score, 2),
            "knowledge_coverage": round(knowledge_coverage_score, 2)
        }

        explanation = (
            f"Deterministic confidence score of {confidence * 100:.1f}% computed from "
            f"completeness ({factors['profile_completeness']}), location quality ({factors['location_quality']}), "
            f"classification confidence ({factors['classification_confidence']}), and financial clarity ({factors['financial_data_available']})."
        )
        return confidence, factors, explanation

    def generate_deterministic_plan(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates a DAG-structured execution plan tailored to the business profile.
        """
        plan = [
            {
                "step": 1,
                "agent": "domain_knowledge_agent",
                "purpose": "Retrieve industry benchmarks, official NIC hierarchy, and business infrastructure requirements",
                "priority": "HIGH",
                "status": "ready",
                "dependencies": []
            },
            {
                "step": 2,
                "agent": "market_intelligence_agent",
                "purpose": "Analyze local demand density, competitor clustering, and catchment demographics",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["domain_knowledge_agent"]
            },
            {
                "step": 3,
                "agent": "market_intelligence_engine",
                "purpose": "Clean evidence, calculate competitive pressure, analyze demand/supply/infra, and build Stage 7 ML features",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["market_intelligence_agent"]
            },
            {
                "step": 4,
                "agent": "opportunity_evaluation_engine",
                "purpose": "Synthesize market opportunity score, component trade-offs, critical constraints, and audit provenance",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["market_intelligence_engine"]
            },
            {
                "step": 5,
                "agent": "finance_engine",
                "purpose": "Calculate deterministic scheme routing, loan caps, EMI, amortization, profitability, break-even, DSCR, and financial viability",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["domain_knowledge_agent"]
            },
            {
                "step": 6,
                "agent": "entrepreneur_profile_engine",
                "purpose": "Evaluate deterministic entrepreneur-business alignment across skills, experience, training, resources, and operations",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["finance_engine"]
            },
            {
                "step": 7,
                "agent": "risk_engine",
                "purpose": "Evaluate Market, Financial, Operational, Seasonal, Supply Chain, Competition, and Infrastructure risks with critical risk preservation",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["entrepreneur_profile_engine"]
            },
            {
                "step": 8,
                "agent": "feasibility_engine",
                "purpose": "Evaluate Stage 12 deterministic composite feasibility scoring consuming Stage 8, Stage 9, Stage 10, and Stage 11 outputs",
                "priority": "HIGH",
                "status": "pending",
                "dependencies": ["opportunity_evaluation_engine", "finance_engine", "entrepreneur_profile_engine", "risk_engine"]
            }
        ]
        return plan

    async def plan_workflow(
        self,
        profile: Dict[str, Any],
        force_llm: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
        """
        Coordinates hybrid workflow planning:
        - Calculates explainable deterministic confidence.
        - Escalates to LLM only if confidence < threshold or force_llm is requested.
        - Falls back gracefully to deterministic plan if LLM is unavailable or fails.
        """
        confidence, factors, explanation = self.calculate_deterministic_confidence(profile)
        deterministic_plan = self.generate_deterministic_plan(profile)

        llm_usage = {"calls": 0, "used": False, "reasons": []}
        should_escalate_llm = force_llm or (confidence < self.confidence_threshold)

        if not should_escalate_llm:
            logger.info(f"[ORCHESTRATOR] Deterministic routing selected (confidence={confidence:.2f}). LLM escalation not required.")
            routing_metadata = {
                "decision_source": "deterministic",
                "deterministic_confidence": confidence,
                "factors": factors,
                "llm_used": False,
                "llm_reason": None,
                "explanation": explanation
            }
            return deterministic_plan, routing_metadata, llm_usage

        # Escalation path
        reason = "Low deterministic confidence threshold" if confidence < self.confidence_threshold else "Explicit user/system escalation"
        logger.info(f"[ORCHESTRATOR] Ambiguous workflow detected. Escalating to LLM planner. Reason: {reason}")
        llm_usage["reasons"].append(reason)

        if not llm_client.is_available:
            logger.info("[ORCHESTRATOR] LLM unavailable. Using deterministic fallback.")
            routing_metadata = {
                "decision_source": "deterministic_fallback",
                "deterministic_confidence": confidence,
                "factors": factors,
                "llm_used": False,
                "llm_reason": "LLM client not configured or unavailable",
                "explanation": f"{explanation} [LLM escalation attempted but client unavailable; using deterministic plan]"
            }
            return deterministic_plan, routing_metadata, llm_usage

        # Call LLM Planner
        try:
            llm_plan, llm_reason = await self._call_llm_planner(profile, deterministic_plan)
            llm_usage["calls"] += 1
            llm_usage["used"] = True
            llm_usage["reasons"].append(f"LLM planner generated customized execution plan: {llm_reason}")

            routing_metadata = {
                "decision_source": "hybrid_llm",
                "deterministic_confidence": confidence,
                "factors": factors,
                "llm_used": True,
                "llm_reason": llm_reason,
                "explanation": f"Workflow customized by LLM Planner: {llm_reason}"
            }
            return llm_plan, routing_metadata, llm_usage

        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] LLM planning exception: {e}. Falling back to deterministic plan.")
            routing_metadata = {
                "decision_source": "deterministic_fallback",
                "deterministic_confidence": confidence,
                "factors": factors,
                "llm_used": False,
                "llm_reason": f"LLM error: {str(e)}",
                "explanation": f"{explanation} [LLM execution failed; fell back to deterministic plan]"
            }
            return deterministic_plan, routing_metadata, llm_usage

    async def _call_llm_planner(
        self,
        profile: Dict[str, Any],
        fallback_plan: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Calls Groq LLM to refine the execution plan."""
        system_prompt = (
            "You are the KALPA Multi-Agent Workflow Orchestrator for Indian MSMEs.\n"
            "Given a Canonical Structured Business Profile, review the proposed agent execution plan.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            "  \"reasoning\": \"string explaining why this plan fits the enterprise\",\n"
            "  \"execution_plan\": [\n"
            "    {\"step\": 1, \"agent\": \"domain_knowledge_agent\", \"purpose\": \"...\", \"priority\": \"HIGH\", \"status\": \"ready\", \"dependencies\": []},\n"
            "    ...\n"
            "  ]\n"
            "}\n"
            "Available Agents: domain_knowledge_agent, market_intelligence_agent, market_intelligence_engine, opportunity_evaluation_engine, finance_engine, entrepreneur_profile_engine, risk_engine, feasibility_engine."
        )

        user_prompt = f"Canonical Business Profile:\n{json.dumps(profile, indent=2)}\n\nBaseline Plan:\n{json.dumps(fallback_plan, indent=2)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        result = await llm_client.chat_completion(
            messages=messages,
            json_mode=True,
            temperature=0.1
        )
        if not result or not isinstance(result, dict):
            return fallback_plan, "Deterministic baseline plan retained (LLM returned empty)."

        plan = result.get("execution_plan", fallback_plan)
        reason = result.get("reasoning", "LLM customized agent execution plan.")
        return plan, reason


# Global singleton instance
hybrid_planner = HybridPlanner()
