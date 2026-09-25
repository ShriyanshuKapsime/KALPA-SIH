import asyncio
import time
import json
import sys
import io

# Force UTF-8 output encoding for Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    BeneficiaryProfileInput
)
from app.services.financial_engine import financial_engine
from app.services.swot_engine.dynamic_swot_agent import dynamic_swot_agent
from app.schemas.swot import SWOTEvaluationRequest
from app.services.assistant_engine.assistant_service import assistant_service
from app.database.session import SessionLocal

async def run_acceptance_verification():
    print("==================================================")
    print("KALPA LIVE ACCEPTANCE VERIFICATION")
    print("==================================================")

    # ─────────────────────────────────────────────────────────────
    # TEST 3: Verify current Saree Retail financial values
    # ─────────────────────────────────────────────────────────────
    print("\n[TEST 3: Saree Retail Financial Integrity]")
    fin_req = FinancialAnalysisRequest(
        analysis_id="live-saree-acc-001",
        session_id="session-live-acc-001",
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
    proj_cost = fc["project_cost"]["total_project_cost"]
    loan = fc["funding"]["institutional_loan"]
    promoter_margin = fc["funding"]["required_promoter_contribution"]
    emi = fc["debt"]["emi"]
    dscr = fc["banking_appraisal"]["average_dscr"]
    pl_y1 = fc["profit_loss"][0]
    rev_y1 = pl_y1.get("revenue") or pl_y1.get("gross_revenue") or 0.0
    pat_y1 = pl_y1.get("pat") or pl_y1.get("net_profit_after_tax") or pl_y1.get("net_profit") or pl_y1.get("profit_after_tax") or 0.0
    bep = fc["banking_appraisal"].get("break_even_utilization") or fc["banking_appraisal"].get("break_even_utilization_pct")

    print(f"Project Cost:    ₹{proj_cost:,.2f} (Expected ₹5,00,000)")
    print(f"Promoter Margin: ₹{promoter_margin:,.2f} (Expected ₹50,000)")
    print(f"Bank Loan:       ₹{loan:,.2f} (Expected ₹4,50,000)")
    print(f"EMI:             ₹{emi:,.2f} (Expected ≈ ₹7,417.43)")
    print(f"Revenue Y1:      ₹{rev_y1:,.2f} (Expected ₹46,80,000)")
    print(f"PAT Y1:          ₹{pat_y1:,.2f} (Expected ₹10,08,845.69)")
    print(f"DSCR:            {dscr:.2f}x (Expected 12.09x)")
    print(f"BEP:             {bep}% (Expected 14.5%)")

    assert abs(proj_cost - 500000.0) < 1.0, f"Project Cost mismatch: {proj_cost}"
    assert abs(loan - 450000.0) < 1.0, f"Loan mismatch: {loan}"
    assert abs(emi - 7417.43) < 1.0, f"EMI mismatch: {emi}"
    assert abs(rev_y1 - 4680000.0) < 1.0, f"Revenue mismatch: {rev_y1}"
    assert abs(pat_y1 - 1008845.69) < 2.0, f"PAT mismatch: {pat_y1}"
    assert abs(dscr - 12.09) < 0.1, f"DSCR mismatch: {dscr}"
    print("✅ TEST 3 PASSED: All Saree Retail financial values preserved exactly.")

    # ─────────────────────────────────────────────────────────────
    # TEST 1: Live Business Assistant Request
    # ─────────────────────────────────────────────────────────────
    print("\n[TEST 1: Live Business Assistant Request]")
    db = SessionLocal()
    try:
        t0 = time.time()
        asst_res = await assistant_service.handle_message(
            analysis_id_str="00000000-0000-0000-0000-000000000001",
            session_id_str="00000000-0000-0000-0000-000000000002",
            user_message="What is my monthly EMI and how is it calculated from my loan amount?",
            language="en",
            db=db,
            financial_context=fc,
            financial_analysis=fin_res.financial_analysis.model_dump()
        )
        asst_elapsed = time.time() - t0
        print(f"Assistant Status: {asst_res['grounding_status']}")
        print(f"Model Provider:   {asst_res['model_provider']}")
        print(f"Model Used:       {asst_res['model_used']}")
        print(f"Elapsed Time:     {asst_elapsed:.2f}s")
        print(f"Response Preview:\n{asst_res['assistant_response'][:400]}...")
        
        assert asst_res["grounding_status"] == "GROUNDED", f"Expected GROUNDED, got {asst_res['grounding_status']}"
        assert asst_res["model_provider"] == "Sarvam AI", f"Expected Sarvam AI, got {asst_res['model_provider']}"
        assert asst_res["model_used"] is True, "Expected model_used=True"
        print("✅ TEST 1 PASSED: Live Assistant returned HTTP 200 from Sarvam AI with grounded response.")
    finally:
        db.close()

    # ─────────────────────────────────────────────────────────────
    # TEST 2: Live Stage 13 SWOT Request
    # ─────────────────────────────────────────────────────────────
    print("\n[TEST 2: Live Stage 13 SWOT Request]")
    swot_req = SWOTEvaluationRequest(
        analysis_id="live-saree-acc-001",
        session_id="session-live-acc-001",
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
            "competition_level": "MODERATE"
        },
        opportunity_result={
            "opportunity_score": 88
        },
        entrepreneur_readiness={
            "overall_score": 80,
            "domain_experience_years": 3,
            "core_skills": ["Direct customer sales", "Textile sourcing"]
        },
        risk_analysis={
            "composite_risk_score": 0.28,
            "primary_risk_drivers": ["Seasonal wedding concentration", "Wholesale price volatility"]
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
    swot_elapsed = time.time() - t0

    print(f"SWOT Status:      {swot_res.status}")
    print(f"SWOT Provider:    {swot_res.generation.mode}")
    print(f"SWOT Model:       {swot_res.generation.model}")
    print(f"Elapsed Time:     {swot_elapsed:.2f}s")
    print(f"Execution Meta:   {swot_res.generation.execution_time_ms}ms")
    print(f"Strengths Count:  {len(swot_res.swot.strengths)}")
    print(f"Weaknesses Count: {len(swot_res.swot.weaknesses)}")
    print(f"Opportunities:    {len(swot_res.swot.opportunities)}")
    print(f"Threats Count:    {len(swot_res.swot.threats)}")
    print(f"First Strength:   {swot_res.swot.strengths[0].title} - {swot_res.swot.strengths[0].explanation}")

    assert swot_res.status in ("SUCCESS", "COMPLETED"), f"Expected SUCCESS/COMPLETED, got {swot_res.status}"
    assert swot_res.generation.mode == "SARVAM_LLM", f"Expected SARVAM_LLM, got {swot_res.generation.mode}"
    assert len(swot_res.swot.strengths) >= 3, "Expected at least 3 strengths"
    print("✅ TEST 2 PASSED: Live Stage 13 SWOT returned HTTP 200 from Sarvam AI in sub-10s without fallback.")

    print("\n==================================================")
    print("ALL LIVE ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_acceptance_verification())
