"""
FastAPI Routes for STAGE 4.5: KALPA Domain Knowledge & Benchmark Hub.
Exposes access to 31 consolidated SIH datasets, government schemes, financial/market benchmarks,
business profiles, risk library, institutional documents, and engine-ready knowledge packs.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.schemas.knowledge import (
    CoverageReportSchema,
    DataSourceMetadataSchema,
    GovernmentSchemeSchema,
    FinancialBenchmarkSchema,
    MarketBenchmarkSchema,
    BusinessProfileSchema,
    BusinessRequirementSchema,
    RiskItemSchema,
    InstitutionalDocumentSchema,
    DynamicDataRequirementSchema,
    SchemeEligibilityQuery,
    SchemeEligibilityResult,
    MarketKnowledgePack,
    FinancialKnowledgePack,
    FinancialFeasibilityResult,
    ComprehensiveBusinessKnowledgePack,
)
from app.knowledge.services.knowledge_service import get_knowledge_service
from app.knowledge.finance_calculator import calculate_standard_emi
from app.core.logging import logger

router = APIRouter(prefix="/knowledge", tags=["Stage 4.5 - Domain Knowledge & Benchmark Hub"])


class DeterministicFinanceCalculationRequest(BaseModel):
    business_id: str
    project_cost: Optional[float] = None
    available_margin: Optional[float] = None
    available_capital: Optional[float] = None
    currency: Optional[str] = "INR"
    scheme_context: Optional[bool] = True


@router.get(
    "/coverage",
    response_model=CoverageReportSchema,
    summary="Get Knowledge Hub Coverage & Status Report",
    description="Returns aggregate health, provenance breakdown, ingestion statuses, and completeness percentage across all 31 SIH datasets and 15 priority enterprise domains."
)
def get_coverage_report():
    try:
        service = get_knowledge_service()
        return service.get_coverage_report()
    except Exception as e:
        logger.error(f"[KNOWLEDGE API ERROR] Coverage report failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coverage report: {str(e)}"
        )


@router.get(
    "/sources",
    response_model=List[DataSourceMetadataSchema],
    summary="List Master Data Source Registry (31 SIH Datasets)",
    description="Lists all 31 consolidated SIH rural datasets with source attribution, ministry, format, and status."
)
def list_data_sources(
    category: Optional[str] = Query(None, description="Filter by category e.g. ENTERPRISE_REGISTRY, SCHEMES, CLIMATE"),
    domain: Optional[str] = Query(None, description="Filter by coverage domain"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status e.g. AVAILABLE, PARTIAL, REGISTERED_NOT_LOADED"),
):
    service = get_knowledge_service()
    return service.get_data_sources(category=category, domain=domain, status=status_filter)


@router.get(
    "/sources/{dataset_id}",
    response_model=DataSourceMetadataSchema,
    summary="Get Data Source by ID",
    description="Retrieves metadata and ingestion status for a specific dataset."
)
def get_data_source(dataset_id: str):
    service = get_knowledge_service()
    source = service.get_data_source(dataset_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID '{dataset_id}' not found in registry."
        )
    return source


@router.get(
    "/schemes",
    response_model=List[GovernmentSchemeSchema],
    summary="List Official Government Schemes & Baseline Rules",
    description="Retrieves all official national schemes (PMEGP, PMMY Mudra, PMFME, StandUp India, CGTMSE, AHIDF) and challenge baseline rules with explicit provenance."
)
def list_government_schemes(
    category: Optional[str] = Query(None, description="Filter by category e.g. CHALLENGE_BASELINE_RULE, COLLATERAL_FREE_MICRO_CREDIT"),
    tier: Optional[str] = Query(None, description="Filter by scheme tier e.g. MICRO_CREDIT, TERM_LOAN, SHISHU, KISHORE"),
):
    service = get_knowledge_service()
    return service.get_schemes(category=category, tier=tier)


@router.get(
    "/schemes/{scheme_id}",
    response_model=GovernmentSchemeSchema,
    summary="Get Government Scheme by ID",
    description="Retrieves complete financial terms, eligibility criteria, and provenance for a specific scheme."
)
def get_government_scheme(scheme_id: str):
    service = get_knowledge_service()
    scheme = service.get_scheme(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' not found."
        )
    return scheme


@router.post(
    "/schemes/evaluate",
    response_model=SchemeEligibilityResult,
    summary="Evaluate Scheme Eligibility & Baseline Rules",
    description="Evaluates an enterprise profile against all official schemes and applies challenge baseline interest/moratorium rules."
)
def evaluate_scheme_eligibility(query: SchemeEligibilityQuery):
    service = get_knowledge_service()
    return service.evaluate_scheme_eligibility(query)


@router.get(
    "/business-profiles",
    summary="List Layer 2 Business Domain Profiles",
    description="Lists operational domain profiles for all 15 priority rural enterprise archetypes."
)
def list_business_profiles():
    service = get_knowledge_service()
    profiles = service.get_all_business_profiles()
    return {
        "status": "success",
        "count": len(profiles),
        "businesses": [
            {
                "business_id": p.business_node_id,
                "name": p.business_title,
                "sector": p.sector or "Rural MSME",
                "category": p.category or "General MSME",
                "knowledge_available": True,
                **p.model_dump()
            }
            for p in profiles
        ]
    }


@router.get(
    "/business-profiles/{business_id}",
    response_model=BusinessProfileSchema,
    summary="Get Business Domain Profile by ID or Alias",
    description="Retrieves operational domain profile including machinery, licenses, space, power, and supply chain specs."
)
def get_business_profile(business_id: str):
    service = get_knowledge_service()
    profile = service.get_business_profile(business_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No business domain profile found for '{business_id}'."
        )
    return profile


@router.get(
    "/benchmarks/financial",
    response_model=List[FinancialBenchmarkSchema],
    summary="List All Financial Benchmarks",
    description="Returns financial benchmarks (CapEx, working capital, gross/net margins, payback) for all indexed rural business nodes."
)
def list_financial_benchmarks():
    service = get_knowledge_service()
    return service.get_all_financial_benchmarks()


@router.get(
    "/benchmarks/financial/{business_node_id}",
    response_model=FinancialBenchmarkSchema,
    summary="Get Financial Benchmark by Business Node ID or NIC Code",
    description="Retrieves verified financial benchmarks, cost structure, margins, and unit economics for a business."
)
def get_financial_benchmark(business_node_id: str):
    service = get_knowledge_service()
    bench = service.get_financial_benchmark(business_node_id)
    if not bench:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No financial benchmark found for business node or NIC '{business_node_id}'."
        )
    return bench


@router.get(
    "/benchmarks/market",
    response_model=List[MarketBenchmarkSchema],
    summary="List All Market Benchmarks",
    description="Returns market benchmarks (catchment radius, saturation threshold, seasonality) for all indexed rural business nodes."
)
def list_market_benchmarks():
    service = get_knowledge_service()
    return service.get_all_market_benchmarks()


@router.get(
    "/benchmarks/market/{business_node_id}",
    response_model=MarketBenchmarkSchema,
    summary="Get Market Benchmark by Business Node ID",
    description="Retrieves catchment radius, saturation threshold, and monthly seasonality multipliers."
)
def get_market_benchmark(business_node_id: str):
    service = get_knowledge_service()
    bench = service.get_market_benchmark(business_node_id)
    if not bench:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market benchmark found for business node '{business_node_id}'."
        )
    return bench


@router.get(
    "/market-pack/{business_id}",
    response_model=MarketKnowledgePack,
    summary="Get Engine-Ready Market Knowledge Pack",
    description="Supplies Market Intelligence Engine with catchment benchmarks, seasonality, and dynamic data requirements."
)
def get_market_knowledge_pack(
    business_id: str,
    location: Optional[str] = Query(None, description="Optional location for contextual filtering"),
):
    service = get_knowledge_service()
    return service.get_market_context(business_id=business_id, location=location)


@router.get(
    "/financial-pack/{business_id}",
    response_model=FinancialKnowledgePack,
    summary="Get Engine-Ready Financial Knowledge Pack",
    description="Supplies Finance Engine & DPR Generator with CapEx/OpEx benchmarks, eligible schemes, and baseline calculation rules."
)
def get_financial_knowledge_pack(
    business_id: str,
    project_cost: Optional[float] = Query(None, description="Optional project cost to compute baseline rules"),
    available_margin: Optional[float] = Query(None, description="Optional promoter equity contribution"),
):
    service = get_knowledge_service()
    return service.get_financial_context(
        business_id=business_id,
        project_cost=project_cost,
        available_margin=available_margin,
    )


@router.post(
    "/financial-pack/calculate",
    summary="Execute Deterministic Financial Feasibility Calculation",
    description="Calculates reducing balance EMI, DSCR, and payback deterministically with 0 LLM calls."
)
def calculate_financial_feasibility(request: DeterministicFinanceCalculationRequest):
    service = get_knowledge_service()
    
    # Resolve project cost
    project_cost = request.project_cost
    if project_cost is None:
        if request.available_capital is not None and request.available_capital > 0:
            # Standard 15% promoter margin -> project cost capacity
            project_cost = round(request.available_capital / 0.15, 2)
        else:
            fin_bench = service.get_financial_benchmark(request.business_id)
            project_cost = fin_bench.capex.typical if fin_bench else 140000.0

    # Resolve margin
    margin = request.available_margin if request.available_margin is not None else request.available_capital
    if margin is None:
        margin = round(project_cost * 0.10, 2)

    feas_result = service.calculate_deterministic_financials(
        business_id=request.business_id,
        project_cost=project_cost,
        available_margin=margin,
    )

    # Scheme eligibility evaluation
    scheme_eval = service.evaluate_scheme_eligibility(
        SchemeEligibilityQuery(
            project_cost=project_cost,
            available_margin=margin,
            business_node_id=request.business_id,
            is_rural=True
        )
    )

    eligible_schemes = []
    for s in scheme_eval.matched_schemes:
        is_rec = (s.scheme_id == scheme_eval.recommended_scheme_id)
        eligible_schemes.append({
            "scheme_id": s.scheme_id,
            "scheme_name": s.scheme_name,
            "nodal_agency": s.nodal_agency,
            "eligibility_status": "potentially_eligible" if is_rec else "requires_verification",
            "max_loan_amount": s.financial_terms.max_loan_amount,
            "interest_rate_pct": s.financial_terms.interest_rate_pct,
            "subsidy_pct": s.financial_terms.subsidy_pct,
            "moratorium_months": s.financial_terms.moratorium_months,
            "tenure_months": s.financial_terms.tenure_months,
            "disclaimer": "Official eligibility is subject to institutional bank appraisal and documentation verification."
        })

    # Repayment options across multiple tenures
    repayment_options = [
        {
            "tenure_label": "3-Year Micro Term (36 Months)",
            "tenure_months": 36,
            "interest_rate_pct": 6.5,
            "moratorium_months": 3,
            "monthly_emi": calculate_standard_emi(feas_result.loan_amount, 6.5, 33),
        },
        {
            "tenure_label": "5-Year Standard Term (60 Months)",
            "tenure_months": 60,
            "interest_rate_pct": 8.0,
            "moratorium_months": 6,
            "monthly_emi": calculate_standard_emi(feas_result.loan_amount, 8.0, 54),
        },
        {
            "tenure_label": "7-Year Long Term (84 Months)",
            "tenure_months": 84,
            "interest_rate_pct": 8.5,
            "moratorium_months": 6,
            "monthly_emi": calculate_standard_emi(feas_result.loan_amount, 8.5, 78),
        }
    ]

    fin_bench = service.get_financial_benchmark(request.business_id)
    provenance = []
    if fin_bench and fin_bench.provenance:
        provenance.append(fin_bench.provenance.model_dump())
    else:
        provenance.append({
            "source_id": "SRC-BENCHMARK-NABARD",
            "source_name": "NABARD Model Bankable Project Profiles",
            "organization": "National Bank for Agriculture and Rural Development",
            "confidence": 0.92
        })

    return {
        "status": "success",
        "business_node_id": feas_result.business_node_id,
        "project_cost_capacity": feas_result.project_cost,
        "project_cost": feas_result.project_cost,
        "margin_contribution": feas_result.promoter_contribution,
        "promoter_contribution": feas_result.promoter_contribution,
        "maximum_loan_amount": feas_result.loan_amount,
        "loan_amount": feas_result.loan_amount,
        "monthly_emi": feas_result.monthly_emi,
        "estimated_monthly_revenue": feas_result.estimated_monthly_revenue,
        "estimated_monthly_net_profit": feas_result.estimated_monthly_net_profit,
        "dscr_ratio": feas_result.dscr_ratio,
        "breakeven_months": feas_result.breakeven_months,
        "payback_period_months": feas_result.payback_period_months,
        "feasibility_status": feas_result.feasibility_status,
        "risk_notes": feas_result.risk_notes,
        "baseline_rule_applied": feas_result.baseline_rule_applied,
        "eligible_schemes": eligible_schemes,
        "repayment_options": repayment_options,
        "calculation_metadata": {
            "dscr_ratio": feas_result.dscr_ratio,
            "breakeven_months": feas_result.breakeven_months,
            "payback_period_months": feas_result.payback_period_months,
            "estimated_monthly_revenue": feas_result.estimated_monthly_revenue,
            "estimated_monthly_net_profit": feas_result.estimated_monthly_net_profit,
        },
        "provenance": provenance
    }


@router.get(
    "/comprehensive-pack/{business_id}",
    response_model=ComprehensiveBusinessKnowledgePack,
    summary="Get 5-Layer Comprehensive Business Knowledge Pack",
    description="Assembles all 5 logical layers: Schemes (L1), Domain Profile (L2), Benchmarks (L3), Evidence (L4), and Dynamic Specs (L5)."
)
def get_comprehensive_pack(
    business_id: str,
    project_cost: Optional[float] = Query(None, description="Optional total project cost for scheme evaluation"),
    available_margin: Optional[float] = Query(None, description="Optional promoter equity"),
):
    service = get_knowledge_service()
    return service.get_comprehensive_business_pack(
        business_node_id=business_id,
        project_cost=project_cost,
        available_margin=available_margin,
    )


@router.get(
    "/business/{business_node_id}/requirements",
    response_model=BusinessRequirementSchema,
    summary="Get Business Domain Technical Requirements",
    description="Retrieves space, power, core machinery, manpower skills, and compliance licenses required."
)
def get_business_requirements(business_node_id: str):
    service = get_knowledge_service()
    reqs = service.get_business_requirements(business_node_id)
    if not reqs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No technical domain requirements found for business node '{business_node_id}'."
        )
    return reqs


@router.get(
    "/business/{business_node_id}/pack",
    summary="Get Legacy Business Knowledge Pack",
    description="Aggregates financial benchmarks, market catchment, equipment requirements, risks, schemes, and reference documents in one call."
)
def get_business_knowledge_pack(
    business_node_id: str,
    project_cost: Optional[float] = Query(None, description="Optional total project cost for scheme evaluation")
):
    service = get_knowledge_service()
    pack = service.get_comprehensive_business_pack(business_node_id=business_node_id, project_cost=project_cost)
    return pack


@router.get(
    "/risks",
    response_model=List[RiskItemSchema],
    summary="List Enterprise Risk Library",
    description="Retrieves categorized operational, market, financial, environmental, and regulatory risks with mitigations."
)
def list_risks(
    category: Optional[str] = Query(None, description="Filter by category e.g. OPERATIONAL, FINANCIAL, REGULATORY, MARKET, CLIMATE_AND_ENVIRONMENTAL"),
    severity: Optional[str] = Query(None, description="Filter by severity e.g. LOW, MEDIUM, HIGH, CRITICAL"),
    business_node_id: Optional[str] = Query(None, description="Filter risks applicable to a specific business node"),
):
    service = get_knowledge_service()
    return service.get_risks(category=category, severity=severity, business_node_id=business_node_id)


@router.get(
    "/documents",
    response_model=List[InstitutionalDocumentSchema],
    summary="List Institutional Knowledge Documents",
    description="Retrieves official research reports, NABARD bankable projects, and RBI circulars with ingestion status."
)
def list_documents(
    institution: Optional[str] = Query(None, description="Filter by institution name e.g. NABARD, RBI, MSME, SIDBI, FSSAI"),
    category: Optional[str] = Query(None, description="Filter by document category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by ingestion status e.g. EXTRACTED, INDEXED, REGISTERED"),
    business_node_id: Optional[str] = Query(None, description="Filter documents applicable to a specific business node"),
):
    service = get_knowledge_service()
    return service.get_institutional_documents(
        institution=institution,
        category=category,
        status=status_filter,
        business_node_id=business_node_id,
    )


@router.get(
    "/dynamic-requirements",
    response_model=List[DynamicDataRequirementSchema],
    summary="List Dynamic Data Requirements",
    description="Retrieves external dynamic data specifications required by future intelligence engines."
)
def list_dynamic_requirements(
    domain: Optional[str] = Query(None, description="Filter by domain e.g. MARKET_INTELLIGENCE, FINANCE, FEASIBILITY"),
    consuming_engine: Optional[str] = Query(None, description="Filter by consuming engine"),
):
    service = get_knowledge_service()
    return service.get_dynamic_data_requirements(domain=domain, consuming_engine=consuming_engine)
