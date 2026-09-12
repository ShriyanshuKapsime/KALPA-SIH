import pytest
from app.knowledge.services.knowledge_service import KnowledgeService, get_knowledge_service
from app.knowledge.finance_calculator import (
    calculate_standard_emi,
    generate_amortization_schedule,
    calculate_baseline_rules,
    evaluate_financial_feasibility,
)
from app.schemas.knowledge import SchemeEligibilityQuery

PRIORITY_ENTERPRISES = [
    "rice_mill",
    "flour_mill",
    "spice_processing",
    "food_processing_micro",
    "dairy_farm",
    "poultry_farm",
    "goat_farming",
    "grocery_store",
    "saree_retail",
    "garment_store",
    "tailoring_shop",
    "beauty_salon",
    "mobile_repair",
    "furniture_carpentry",
    "handicrafts",
]


@pytest.fixture
def knowledge_service():
    return get_knowledge_service()


# ==============================================================================
# 1. 15 Priority Enterprises Coverage Tests (Layer 2 & Layer 3)
# ==============================================================================
@pytest.mark.parametrize("business_id", PRIORITY_ENTERPRISES)
def test_priority_enterprises_financial_benchmarks(knowledge_service: KnowledgeService, business_id: str):
    """Verify that every one of the 15 priority rural businesses has valid financial benchmarks."""
    bench = knowledge_service.get_financial_benchmark(business_id)
    assert bench is not None, f"Financial benchmark missing for {business_id}"
    assert bench.capex.range_min > 0
    assert bench.capex.typical >= bench.capex.range_min
    assert bench.capex.range_max >= bench.capex.typical
    assert bench.margins.gross_margin_pct_typical > 0
    assert bench.margins.net_margin_pct_typical > 0
    assert bench.timelines.payback_period_months > 0
    assert len(bench.cost_structure_pct) > 0
    assert bench.provenance is not None
    assert bench.provenance.organization or bench.provenance.source_name


@pytest.mark.parametrize("business_id", PRIORITY_ENTERPRISES)
def test_priority_enterprises_market_benchmarks(knowledge_service: KnowledgeService, business_id: str):
    """Verify that every one of the 15 priority rural businesses has valid market benchmarks."""
    bench = knowledge_service.get_market_benchmark(business_id)
    assert bench is not None, f"Market benchmark missing for {business_id}"
    assert bench.catchment.primary_radius_km > 0
    assert bench.catchment.secondary_radius_km >= bench.catchment.primary_radius_km
    assert bench.competition_and_saturation.saturation_threshold_units_per_10k_pop > 0
    assert len(bench.seasonality_factors) == 12
    assert "jan" in bench.seasonality_factors and "dec" in bench.seasonality_factors
    assert len(bench.demand_drivers) >= 2


@pytest.mark.parametrize("business_id", PRIORITY_ENTERPRISES)
def test_priority_enterprises_domain_profiles(knowledge_service: KnowledgeService, business_id: str):
    """Verify that every one of the 15 priority rural businesses has a Layer 2 domain profile."""
    prof = knowledge_service.get_business_profile(business_id)
    assert prof is not None, f"Business domain profile missing for {business_id}"
    assert prof.business_title is not None
    assert prof.space_and_infrastructure is not None
    assert "built_up_area_sqft_recommended" in prof.space_and_infrastructure
    assert "power_load_hp" in prof.power_and_utilities
    assert len(prof.compliance_and_licensing) >= 1 or len(prof.risk_factors) >= 1


# ==============================================================================
# 2. Deterministic Finance Math & Baseline Loan Rules Tests
# ==============================================================================
def test_reducing_balance_emi_math():
    """Verify mathematical accuracy of reducing balance EMI formula."""
    emi = calculate_standard_emi(100000.0, 12.0, 12)
    assert 8880.0 <= emi <= 8890.0

    # 0 interest rate edge case
    assert calculate_standard_emi(120000.0, 0.0, 12) == 10000.0


def test_sih_baseline_micro_finance_boundary_cases():
    """
    Project Cost <= 1.40 Lakhs must apply SIH_BASELINE_MICRO_FINANCE:
    - Rate: 6.5%
    - Tenure: 36 months
    - Moratorium: 3 months
    - Min promoter margin: 10%
    """
    # Exactly at boundary ₹1.40L (₹140,000)
    rules_140k = calculate_baseline_rules(project_cost=140000.0)
    assert rules_140k.baseline_rule_applied == "SIH_BASELINE_MICRO_FINANCE"
    assert rules_140k.is_micro_enterprise is True
    assert rules_140k.interest_rate_pct == 6.5
    assert rules_140k.tenure_months == 36
    assert rules_140k.moratorium_months == 3
    assert rules_140k.promoter_contribution_amount == 14000.0  # 10%
    assert rules_140k.loan_amount == 125000.0  # Capped at ₹1.25L
    assert rules_140k.monthly_emi > 0
    assert len(rules_140k.first_year_schedule) == 12

    # Under boundary: ₹80,000
    rules_80k = calculate_baseline_rules(project_cost=80000.0, available_margin=10000.0)
    assert rules_80k.baseline_rule_applied == "SIH_BASELINE_MICRO_FINANCE"
    assert rules_80k.interest_rate_pct == 6.5
    assert rules_80k.promoter_contribution_amount == 10000.0
    assert rules_80k.loan_amount == 70000.0


def test_sih_baseline_term_loan_boundary_cases():
    """
    Project Cost > 1.40 Lakhs up to 50 Lakhs must apply SIH_BASELINE_TERM_LOAN:
    - Rate: 8.0%
    - Tenure: 84 months (7 years)
    - Moratorium: 6 months
    - Min promoter margin: 10%
    """
    # Just above boundary: ₹140,001
    rules_above = calculate_baseline_rules(project_cost=140001.0)
    assert rules_above.baseline_rule_applied == "SIH_BASELINE_TERM_LOAN"
    assert rules_above.is_micro_enterprise is False
    assert rules_above.interest_rate_pct == 8.0
    assert rules_above.tenure_months == 84
    assert rules_above.moratorium_months == 6
    assert rules_above.promoter_contribution_amount >= 14000.10

    # Large enterprise: ₹10,00,000 (10 Lakhs)
    rules_10l = calculate_baseline_rules(project_cost=1000000.0, available_margin=150000.0)
    assert rules_10l.baseline_rule_applied == "SIH_BASELINE_TERM_LOAN"
    assert rules_10l.interest_rate_pct == 8.0
    assert rules_10l.loan_amount == 850000.0
    assert rules_10l.monthly_emi > 0


def test_moratorium_principal_deferment():
    """Verify that during moratorium months, principal payment is 0 and only interest is paid."""
    schedule, total_interest, total_payment = generate_amortization_schedule(
        principal=100000.0,
        annual_rate_pct=6.5,
        tenure_months=36,
        moratorium_months=3,
        moratorium_policy="principal_only",
        months_to_generate=12,
    )
    # Months 1, 2, 3 must have 0 principal repayment
    for row in schedule[:3]:
        assert row.principal_payment == 0.0
        assert row.closing_balance == 100000.0
        assert row.interest_payment > 0

    # Month 4 onwards principal repayment starts
    assert schedule[3].principal_payment > 0
    assert schedule[3].closing_balance < 100000.0


# ==============================================================================
# 3. MarketKnowledgePack & FinancialKnowledgePack Engine Interface Tests
# ==============================================================================
def test_get_market_context_known_business(knowledge_service: KnowledgeService):
    """Known enterprise returns ready MarketKnowledgePack with complete specs."""
    pack = knowledge_service.get_market_context("rice_mill")
    assert pack.available is True
    assert pack.status == "ready"
    assert pack.business_node_id == "rice_mill"
    assert pack.catchment is not None
    assert pack.catchment.primary_radius_km == 15.0
    assert len(pack.seasonality_factors) == 12
    assert pack.market_analysis_requirements is not None
    assert "AGMARKNET_DAILY_MANDI" in pack.market_analysis_requirements.dynamic_data_required


def test_get_market_context_unknown_business(knowledge_service: KnowledgeService):
    """Unknown enterprise returns structured missing data signals and recommended action."""
    pack = knowledge_service.get_market_context("aerospace_rocket_fuel_refinery")
    assert pack.available is False
    assert pack.status == "data_missing"
    assert pack.recommended_action == "fetch_dynamic_data"


def test_get_financial_context_known_business(knowledge_service: KnowledgeService):
    """Known enterprise returns ready FinancialKnowledgePack with deterministic calculations."""
    pack = knowledge_service.get_financial_context("spice_processing", project_cost=350000.0)
    assert pack.available is True
    assert pack.status == "ready"
    assert pack.benchmark_capex is not None
    assert pack.calculation_rules is not None
    assert pack.calculation_rules.baseline_rule_applied in ["SIH_BASELINE_TERM_LOAN", "PMFME_MOFPI"]
    assert pack.calculation_rules.monthly_emi > 0


def test_calculate_deterministic_financials(knowledge_service: KnowledgeService):
    """Feasibility calculation returns deterministic DSCR, breakeven, and feasibility status."""
    res = knowledge_service.calculate_deterministic_financials("flour_mill", project_cost=120000.0, available_margin=15000.0)
    assert res.business_node_id == "flour_mill"
    assert res.project_cost == 120000.0
    assert res.loan_amount == 105000.0
    assert res.monthly_emi > 0
    assert res.dscr_ratio >= 1.0
    assert res.feasibility_status in ["FEASIBLE", "CONDITIONAL", "HIGH_RISK"]


# ==============================================================================
# 4. Comprehensive 5-Layer Pack & Coverage Report Tests
# ==============================================================================
def test_get_comprehensive_business_pack(knowledge_service: KnowledgeService):
    """Verifies all 5 layers are assembled in a single call."""
    comp_pack = knowledge_service.get_comprehensive_business_pack("dairy_farm", project_cost=500000.0)
    assert comp_pack.available is True
    assert comp_pack.business_node_id == "dairy_farm"
    assert comp_pack.layer1_rules_and_schemes is not None
    assert comp_pack.layer2_domain_knowledge is not None
    assert comp_pack.layer3_financial_benchmarks is not None
    assert comp_pack.layer3_market_benchmarks is not None
    assert len(comp_pack.layer4_institutional_evidence) >= 1
    assert len(comp_pack.layer5_candidate_sources) >= 1
    assert comp_pack.quality_score.overall_confidence >= 0.80


def test_coverage_report(knowledge_service: KnowledgeService):
    """Verifies 31 datasets registry and 15 priority enterprises coverage audit."""
    rep = knowledge_service.get_coverage_report()
    assert rep.total_curated_datasets == 31
    assert rep.total_schemes >= 7
    assert rep.total_financial_benchmarks >= 15
    assert rep.total_market_benchmarks >= 15
    assert rep.total_business_profiles >= 15
    assert rep.completeness_score_pct >= 85.0
    assert len(rep.priority_businesses_coverage) == 15
    for pb, status in rep.priority_businesses_coverage.items():
        assert status["ready"] is True, f"{pb} is not fully ready in coverage matrix"
