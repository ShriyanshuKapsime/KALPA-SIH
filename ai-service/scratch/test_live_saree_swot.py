import asyncio
import time
import json
from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    BeneficiaryProfileInput
)
from app.services.financial_engine import financial_engine
from app.services.swot_engine.dynamic_swot_agent import dynamic_swot_agent
from app.schemas.swot import SWOTEvaluationRequest


async def run_live_saree_swot():
    print("--- 1. Running Financial Analysis for Saree Retail ---")
    fin_req = FinancialAnalysisRequest(
        analysis_id="live-saree-001",
        session_id="session-live-001",
        business_profile=BusinessProfileInput(
            business_id="saree_retail",
            specific_business="Saree Retail & Ethnic Wear Emporium",
            sector="Retail",
            category="Textiles"
        ),
        financial_profile=FinancialProfileInput(
            available_margin_capital=200000.0
        ),
        beneficiary_profile=BeneficiaryProfileInput(
            beneficiary_category="General",
            gender="Female",
            annual_family_income=300000.0
        ),
        user_driver_inputs={
            "tax_regime": "NEW_CONCESSIONAL",
            "business_constitution": "SOLE_PROPRIETORSHIP"
        }
    )
    fin_res = financial_engine.analyze(fin_req)
    fc = fin_res.financial_context
    print(f"Finance Complete: Total Cost = Rs {fc['project_cost']['total_project_cost']}, DSCR = {fc['banking_appraisal']['average_dscr']}x, EMI = Rs {fc['debt']['emi']}")

    print("\n--- 2. Triggering Stage 13 SWOT Evaluation ---")
    swot_req = SWOTEvaluationRequest(
        analysis_id="live-saree-001",
        session_id="session-live-001",
        business_profile={
            "business_id": "saree_retail",
            "specific_business": "Saree Retail & Ethnic Wear Emporium",
            "sector": "Retail",
            "category": "Textiles"
        },
        location_profile={
            "district": "Varanasi",
            "state": "Uttar Pradesh",
            "area_type": "Semi-Urban"
        },
        financial_analysis=fin_res.financial_analysis.model_dump(),
        financial_context=fc,
        market_analysis={
            "demand_index": 85,
            "competition_level": "MODERATE",
            "target_customer_density": "HIGH"
        },
        opportunity_result={
            "opportunity_score": 88,
            "catchment_density": "HIGH"
        },
        entrepreneur_readiness={
            "overall_score": 80,
            "domain_experience_years": 3,
            "core_skills": ["Direct customer sales", "Textile sourcing"]
        },
        risk_analysis={
            "composite_risk_score": 0.28,
            "top_risks": ["Seasonal wedding concentration", "Wholesale price volatility"]
        },
        feasibility_result={
            "viability_status": "VIABLE",
            "overall_feasibility_score": 84,
            "recommendation": "PROCEED"
        },
        force_refresh=True
    )

    t0 = time.time()
    swot_res = await dynamic_swot_agent.generate_swot_analysis(swot_req)
    elapsed = time.time() - t0

    print(f"\n--- 3. SWOT Result (Elapsed: {elapsed:.2f}s) ---")
    print(f"Status: {swot_res.status}")
    print(f"Provider: {swot_res.generation.mode} ({swot_res.generation.model})")
    print(f"Execution Time in Meta: {swot_res.generation.execution_time_ms} ms")
    print(f"Strengths ({len(swot_res.swot.strengths)}):")
    for s in swot_res.swot.strengths:
        print(f"  - [{s.id}] {s.title}: {s.explanation}")
        print(f"    Evidence: {s.evidence}")
    print(f"Weaknesses ({len(swot_res.swot.weaknesses)}):")
    for w in swot_res.swot.weaknesses:
        print(f"  - [{w.id}] {w.title}: {w.explanation}")
    print(f"Opportunities ({len(swot_res.swot.opportunities)}):")
    for o in swot_res.swot.opportunities:
        print(f"  - [{o.id}] {o.title}: {o.explanation}")
    print(f"Threats ({len(swot_res.swot.threats)}):")
    for t in swot_res.swot.threats:
        print(f"  - [{t.id}] {t.title}: {t.explanation}")
    print(f"Evidence Summary Financial: {swot_res.evidence_summary.financial}")


if __name__ == "__main__":
    asyncio.run(run_live_saree_swot())
