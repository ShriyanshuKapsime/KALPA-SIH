"""
Prompt Builder for Stage 13: Dynamic SWOT Agent.
Constructs ultra-compact, precision prompts for Sarvam AI (sarvam-105b) enforcing:
- Strict JSON output structure
- Provenance citations across Stages 6–12
- Zero reasoning token exhaustion (no chain-of-thought, no step-by-step requests)
- Anti-fabrication constraints & data gap handling
- Bounded list cardinalities (3–5 items per category)
"""
import json
from typing import Dict, Any


def build_swot_system_prompt() -> str:
    return (
        "You are KALPA's Stage 13 Strategic SWOT Agent for rural Indian micro-enterprises.\n"
        "Think concisely and return ONLY a valid JSON object without markdown code blocks, conversational text, or reasoning commentary.\n\n"
        "Required JSON Structure:\n"
        "- executive_summary: string (1-2 sentences summarizing enterprise viability and strategic positioning)\n"
        "- strengths: array of 3 items with {id: 'ST-001', title, evidence, business_impact, priority: 'HIGH', source_stage: 'STAGE_10'|'STAGE_9'|'STAGE_12', data_status: 'KNOWN'}\n"
        "- weaknesses: array of 3 items with {id: 'WK-001', title, evidence, business_impact, priority: 'HIGH'|'MEDIUM', source_stage: 'STAGE_10'|'STAGE_9', data_status: 'KNOWN'|'DATA_GAP'}\n"
        "- opportunities: array of 3 items with {id: 'OP-001', title, evidence, action, priority: 'HIGH', source_stage: 'STAGE_6'|'STAGE_8', data_status: 'KNOWN'}\n"
        "- threats: array of 3 items with {id: 'TH-001', title, evidence, mitigation, priority: 'HIGH'|'MEDIUM', source_stage: 'STAGE_11', data_status: 'KNOWN'}\n"
        "- strategic_priorities: array of 3 items with {id: 'SP-001', action, reason, linked_dimension: 'market'|'finance'|'entrepreneur'|'risk', priority: 'HIGH'}\n"
        "- roadmap: array of 3 objects with [{phase: '0-30 days', actions: [...]}, {phase: '30-90 days', actions: [...]}, {phase: '90+ days', actions: [...]}]\n"
        "- strategic_direction: string (1-2 sentences)\n"
        "- confidence: float between 0.85 and 0.95\n\n"
        "CRITICAL RULES:\n"
        "1. Never invent missing facts. If an upstream field is missing, set data_status to 'DATA_GAP' and state 'Evidence unavailable'.\n"
        "2. Strengths and weaknesses must be internal to the enterprise/promoter; opportunities and threats must be external.\n"
        "3. Keep each title punchy and explanations to 1-2 factual sentences."
    )


def build_swot_user_prompt(evidence_context: Dict[str, Any]) -> str:
    b = evidence_context.get("business", {})
    m = evidence_context.get("market", {})
    f = evidence_context.get("finance", {})
    e = evidence_context.get("entrepreneur", {})
    r = evidence_context.get("risk", {})
    fs = evidence_context.get("feasibility", {})

    evidence_summary = {
        "venture": f"{b.get('name')} ({b.get('category') or b.get('domain')}) at {b.get('location')}",
        "market": f"Demand:{m.get('demand')}, Comp:{m.get('competition')}, Score:{m.get('score')}/100",
        "finance": f"DSCR:{f.get('dscr')}x, Cost:Rs {f.get('project_cost')}, Loan:Rs {f.get('loan_requirement')}, BEP:{f.get('break_even_pct') or f.get('score')}%",
        "entrepreneur": f"Score:{e.get('score')}/100, Skills:{', '.join(e.get('skills', [])[:2]) if e.get('skills') else 'Standard'}, Exp:{', '.join(e.get('experience', [])[:1]) if e.get('experience') else 'Domain exp'}",
        "risk": f"CompositeRisk:{r.get('score') or r.get('composite_risk')}, Critical:{', '.join(r.get('critical_risks', [])[:2]) if r.get('critical_risks') else 'Standard commercial risks'}",
        "feasibility": f"Viability:{fs.get('decision') or fs.get('viability')}, Score:{fs.get('score')}/100"
    }

    summary_json = json.dumps(evidence_summary, separators=(",", ":"))
    return (
        f"Verified Upstream Evidence:\n{summary_json}\n\n"
        f"Generate 3-item-per-category SWOT JSON for this venture:\n"
        f"Emit pure JSON object now:"
    )



def build_compact_retry_user_prompt(evidence_context: Dict[str, Any]) -> str:
    """
    Ultra-compact user prompt (<400 bytes) for Attempt 2 retries.
    Extracts only high-impact signals to guarantee fast single-shot completion.
    """
    b = evidence_context.get("business", {})
    m = evidence_context.get("market", {})
    f = evidence_context.get("finance", {})
    e = evidence_context.get("entrepreneur", {})
    r = evidence_context.get("risk", {})
    fs = evidence_context.get("feasibility", {})

    compact_summary = {
        "biz": f"{b.get('name')} ({b.get('category') or b.get('domain')}) at {b.get('location')}",
        "mkt": f"Demand:{m.get('demand')}, Comp:{m.get('competition')}, Score:{m.get('score')}",
        "fin": f"DSCR:{f.get('dscr')}, BEP:{f.get('break_even_pct') or f.get('score')}, Cost:{f.get('project_cost')}",
        "ent": f"Exp:{e.get('experience')}, Skills:{e.get('skills')}",
        "rsk": f"Risk:{r.get('score') or r.get('composite_risk')}, Critical:{r.get('critical_risks') or r.get('top_risk_vectors')}",
        "fea": f"Viability:{fs.get('decision') or fs.get('viability')}, Score:{fs.get('score')}"
    }

    summary_json = json.dumps(compact_summary, separators=(",", ":"))
    return (
        f"Generate 3-item-per-category SWOT JSON for this venture:\n{summary_json}\n\n"
        f"Emit pure JSON object now:"
    )


