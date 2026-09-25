"""
Verification script for Stage 14: Bankable DPR Generation.
Tests synthesis of verified M1-M6 financial package into institutional PDF and metadata.
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.financial_engine import financial_engine
from app.engines.dpr.schemas import DPRDocumentRequest
from app.engines.dpr.service import dpr_generation_engine, REPORTS_DIR

async def main():
    print("--- Testing Stage 14 Bankable DPR Generation ---")
    
    # 1. Analyze Saree Retail
    payload = {
        "analysis_id": "test_saree_dpr_analysis",
        "session_id": "test_saree_dpr_session",
        "business_profile": {
            "business_id": "retail_saree_01",
            "specific_business": "Traditional & Designer Saree Retail Store",
            "business_category": "RETAIL_TRADE",
            "nic_code": "47511"
        },
        "financial_profile": {
            "available_margin_capital": 200000.0,
            "preferred_project_cost": 500000.0
        },
        "beneficiary_profile": {
            "beneficiary_category": "GENERAL",
            "gender": "Female",
            "is_greenfield": True
        },
        "location_profile": {
            "district": "Varanasi",
            "state": "Uttar Pradesh"
        }
    }
    
    analysis_resp = financial_engine.analyze(payload)
    fin_pkg = analysis_resp.financial_analysis.dpr_financial_package
    assert fin_pkg is not None, "DPR Financial Package must not be None"
    
    print(f"[1] M6 DPR Package generated. Status: {fin_pkg.data_completeness.status}")
    print(f"    Project Cost: Rs. {fin_pkg.project_cost.total_project_cost}")
    print(f"    Loan: Rs. {fin_pkg.loan_structure.sanctioned_loan_amount}")
    print(f"    Promoter Margin: Rs. {fin_pkg.means_of_finance.promoter_contribution}")
    print(f"    Funding Surplus / Reserve: Rs. {fin_pkg.means_of_finance.funding_surplus}")
    print(f"    Monthly EMI: Rs. {fin_pkg.loan_structure.monthly_emi}")
    print(f"    Tenure: {fin_pkg.loan_structure.tenure_months} months")
    
    # 2. Invoke DPR Generation Engine
    req = DPRDocumentRequest(
        business_id="retail_saree_01",
        session_id="test_saree_dpr_session",
        analysis_id="test_saree_dpr_analysis",
        scheme_code="PMEGP",
        financial_package=fin_pkg,
        non_financial_context={
            "market_analysis": {
                "tam": 12000000.0,
                "target_customers": "Local weddings, festival shoppers, retail consumers",
                "demand_drivers": ["Festive demand", "Handloom heritage appeal"]
            },
            "swot_analysis": {
                "strengths": ["Prime retail location", "Verified vendor connections"],
                "opportunities": ["Festive surge", "E-commerce expansion"]
            }
        }
    )
    
    dpr_meta = await dpr_generation_engine.generate_dpr(req)
    
    print(f"\n[2] DPR Document Metadata:")
    print(f"    Document ID: {dpr_meta.document_id}")
    print(f"    Title: {dpr_meta.title}")
    print(f"    Pages: {dpr_meta.pages}")
    print(f"    Format: {dpr_meta.file_format}")
    print(f"    Status: {dpr_meta.status}")
    print(f"    PDF Path: {dpr_meta.file_path}")
    print(f"    Download URL: {dpr_meta.download_url}")
    print(f"    Completeness: {dpr_meta.completeness_status}")
    print(f"    Eligible: {dpr_meta.is_dpr_eligible}")
    print(f"    Financial Highlights: {dpr_meta.financial_highlights}")
    
    assert os.path.exists(dpr_meta.file_path), f"File {dpr_meta.file_path} must exist"
    file_size = os.path.getsize(dpr_meta.file_path)
    # 3. Test with a fully completed benchmark business (e.g. Artisanal Bakery)
    print("\n--- Testing Fully Resolved Benchmark DPR (Bakery) ---")
    bakery_payload = {
        "analysis_id": "test_bakery_dpr_analysis",
        "session_id": "test_bakery_dpr_session",
        "business_profile": {
            "business_id": "bakery_01",
            "specific_business": "Artisanal Bakery & Cafe",
            "business_category": "FOOD_PROCESSING",
            "nic_code": "10712"
        },
        "financial_profile": {
            "available_margin_capital": 300000.0,
            "preferred_project_cost": 1200000.0
        },
        "beneficiary_profile": {
            "beneficiary_category": "GENERAL",
            "gender": "Male",
            "is_greenfield": True
        },
        "location_profile": {
            "district": "Pune",
            "state": "Maharashtra"
        }
    }
    b_resp = financial_engine.analyze(bakery_payload)
    b_pkg = b_resp.financial_analysis.dpr_financial_package
    b_req = DPRDocumentRequest(
        business_id="bakery_01",
        session_id="test_bakery_dpr_session",
        analysis_id="test_bakery_dpr_analysis",
        financial_package=b_pkg
    )
    b_meta = await dpr_generation_engine.generate_dpr(b_req)
    print(f"[3] Benchmark DPR Document Metadata:")
    print(f"    Document ID: {b_meta.document_id}")
    print(f"    Pages: {b_meta.pages}")
    print(f"    Status: {b_meta.status}")
    print(f"    Completeness: {b_meta.completeness_status}")
    print(f"    Eligible: {b_meta.is_dpr_eligible}")
    print(f"    DSCR: {b_meta.financial_highlights.get('average_dscr')}")
    print(f"    BEP Sales: Rs. {b_meta.financial_highlights.get('break_even_sales_amount')}")
    print(f"    Resilience: {b_meta.financial_highlights.get('resilience_status')}")
    print(f"    PDF Size: {os.path.getsize(b_meta.file_path)} bytes")

if __name__ == "__main__":
    asyncio.run(main())
