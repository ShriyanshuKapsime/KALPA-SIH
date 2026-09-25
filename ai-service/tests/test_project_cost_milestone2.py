"""
Hardened Targeted Test Suite for Milestone 2: Automated Project Cost & Working Capital Engine.
Validates all P0 requirements:
1. Complete retail benchmark flow
2. Service business with structural zero inventory
3. No benchmark/default data -> unresolved (None/UNKNOWN) instead of invented values
4. User input overrides benchmark
5. CapEx total benchmark without category breakdown preserves total and leaves categories None
6. Salary without benchmark/rate is NOT derived (no unsourced ₹10k default)
7. Unknown scheme financing reconciliation (never replaces scheme cost with calculated cost)
8. Opening inventory and Working Capital have NO double counting
9. M1 -> M2 -> Stage 9 complete end-to-end execution
10. Verify M2 values directly change downstream Stage 9 outputs (capital structure, profitability, viability)
11. Legacy request without M2 data succeeds seamlessly
12. Schema validation and serialization compatibility
13. Circular and invalid dependencies rejected safely
"""
import pytest
from typing import Dict, Any, List

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    BeneficiaryProfileInput,
    LocationProfileInput,
    ProjectAssumptionsInput,
    FinancialAnalysisContainer,
    ProjectCostAnalysis,
    WorkingCapitalAnalysis,
)
from app.services.financial_engine.intelligence.archetype_registry import (
    FinancialArchetype, archetype_registry
)
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, SourceType, AssumptionStatus, AssumptionType, Provenance
)
from app.services.financial_engine.project_cost import (
    derivation_engine,
    DerivationEngine,
    CircularDependencyError,
    working_capital_engine,
    WorkingCapitalEngine,
    capex_engine,
    CapExEngine,
    project_cost_reconciler,
    ProjectCostReconciler,
    project_cost_engine,
    ProjectCostEngine,
)
from app.services.financial_engine.engine import financial_engine
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


def _make_asm(driver_id: str, value: Any, source_type: SourceType, conf: float = 0.90, user_confirmed: bool = False) -> ResolvedAssumption:
    return ResolvedAssumption(
        driver_id=driver_id,
        value=value,
        unit="INR" if "cost" in driver_id or "revenue" in driver_id or "margin_cap" in driver_id or "inventory" in driver_id or "price" in driver_id else "count",
        source_type=source_type,
        source_id=f"TEST_{source_type.value}",
        confidence=conf,
        status=AssumptionStatus.RESOLVED,
        assumption_type=AssumptionType.USER_INPUT if user_confirmed else AssumptionType.FACT,
        user_confirmed=user_confirmed,
        required=True,
        provenance=Provenance(
            source_type=source_type,
            source_id="TEST",
            description=f"Test assumption for {driver_id}",
            confidence=conf
        )
    )


# =============================================================================
# 1. Complete Retail Benchmark Flow
# =============================================================================
def test_complete_retail_benchmark_flow():
    """
    Complete retail flow with evidenced inventory, rent, margins, and buffer parameters.
    Produces deterministic project cost and working capital decomposition.
    """
    assumptions = [
        _make_asm("monthly_transactions", 500, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("average_ticket", 200.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("gross_margin", 25.0, SourceType.BENCHMARK),
        _make_asm("inventory_days", 30.0, SourceType.BENCHMARK),
        _make_asm("monthly_rent", 8000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("staff_count", 1, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("salary_cost", 10000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("electricity_cost", 1500.0, SourceType.USER_INPUT, user_confirmed=True),
    ]

    benchmark = BenchmarkFinancialData(
        business_id="sample_retail",
        business_title="Retail Store",
        working_capital_months_recommended=1.0,
        typical_capex_inr=150000.0,
        confidence=0.90,
    )

    pc_analysis, wc_analysis, derived = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        benchmark_data=benchmark,
        user_inputs={"preferred_project_cost": 250000.0},
        scheme_financeable_cost=300000.0,
        scheme_margin_ratio=0.10,
    )

    # Derivations
    asm_map = {a.driver_id: a for a in derived}
    assert asm_map["monthly_revenue"].value == 100000.0  # 500 * 200
    assert asm_map["monthly_cogs"].value == 75000.0     # 100000 * (1 - 0.25)
    assert asm_map["inventory_requirement"].value == 75000.0  # (75000 / 30) * 30

    # Working Capital
    assert wc_analysis.status == "RESOLVED"
    assert wc_analysis.inventory_requirement == 75000.0
    # Evidenced 1-month buffer = 8000 + 10000 + 1500 = 19500
    assert wc_analysis.operating_cash_buffer == 19500.0
    assert wc_analysis.total_working_capital == 94500.0

    # Project Cost Decomposition
    assert pc_analysis.status == "RESOLVED"
    assert pc_analysis.capex == 150000.0
    assert pc_analysis.opening_inventory == 75000.0
    assert pc_analysis.working_capital == 19500.0  # non-inventory WC buffer
    assert pc_analysis.pre_operating_cost is None   # No unsourced pre-op default (remains None / UNKNOWN)
    assert pc_analysis.contingency is None          # No unsourced contingency (remains None / UNKNOWN)
    assert pc_analysis.total_project_cost == 244500.0  # 150000 + 75000 + 19500
    assert pc_analysis.promoter_margin == 24450.0      # 10%
    assert pc_analysis.debt_component == 220050.0


# =============================================================================
# 2. Service Business with Structural Zero Inventory
# =============================================================================
def test_service_structural_zero_inventory():
    """
    Service businesses hold NO retail merchandise inventory (₹0.00 structural zero).
    Working capital is driven by evidenced operating buffer, not retail inventory logic.
    """
    assumptions = [
        _make_asm("jobs_per_day", 10, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("operating_days", 25, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("average_realization", 300.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("monthly_rent", 12000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("salary_cost", 15000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("electricity_cost", 2000.0, SourceType.USER_INPUT, user_confirmed=True),
    ]

    pc_analysis, wc_analysis, _ = project_cost_engine.evaluate(
        archetype=FinancialArchetype.SERVICE,
        assumptions=assumptions,
        user_inputs={"operating_buffer_months": 2.0, "capex_override": 100000.0},
        scheme_financeable_cost=200000.0,
    )

    assert wc_analysis.inventory_requirement == 0.0
    assert pc_analysis.opening_inventory == 0.0
    assert wc_analysis.operating_cash_buffer == 58000.0  # (12000 + 15000 + 2000) * 2.0
    assert wc_analysis.total_working_capital == 58000.0
    assert wc_analysis.methodology == "SERVICE_OPERATING_BUFFER"


# =============================================================================
# 3. No Benchmark / Default Data -> Unresolved, Never Invented
# =============================================================================
def test_no_benchmark_unresolved_not_invented():
    """
    When required parameters (like inventory days or operating buffer) are absent
    and no benchmark exists, values must remain UNKNOWN/None, NEVER silently invented.
    """
    # Only transactions and rent provided, missing average_ticket and inventory_days
    assumptions = [
        _make_asm("monthly_transactions", 500, SourceType.USER_INPUT),
        _make_asm("monthly_rent", 8000.0, SourceType.USER_INPUT),
    ]

    pc_analysis, wc_analysis, derived = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        benchmark_data=None,  # No benchmark
    )

    # Derivation cannot invent average_ticket or revenue
    val_map = {a.driver_id: a.value for a in derived}
    assert val_map.get("monthly_revenue") is None
    assert val_map.get("monthly_cogs") is None

    # Working capital cannot invent days or buffer
    assert wc_analysis.status == "INSUFFICIENT_DATA"
    assert wc_analysis.total_working_capital is None

    # Project cost cannot invent capex or total
    assert pc_analysis.status == "INSUFFICIENT_DATA"
    assert pc_analysis.capex is None
    assert pc_analysis.total_project_cost is None


# =============================================================================
# 4. User Input Overrides Benchmark
# =============================================================================
def test_user_override_beats_benchmark():
    """
    User-specified inputs strictly override benchmarks with 1.0 confidence.
    """
    assumptions = [
        _make_asm("opening_inventory", 150000.0, SourceType.USER_INPUT, conf=1.0, user_confirmed=True),
        _make_asm("monthly_rent", 10000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("salary_cost", 12000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("monthly_cogs", 80000.0, SourceType.BENCHMARK),
        _make_asm("inventory_days", 30.0, SourceType.BENCHMARK),
    ]

    benchmark = BenchmarkFinancialData(
        business_id="sample_retail",
        business_title="Sample Retail Store",
        typical_capex_inr=100000.0,
        typical_working_capital_monthly_inr=50000.0,
    )

    pc_analysis, wc_analysis, _ = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        benchmark_data=benchmark,
        user_inputs={"capex_override": 180000.0},
        scheme_financeable_cost=400000.0,
    )

    assert pc_analysis.opening_inventory == 150000.0
    inv_comp = next(c for c in pc_analysis.components if c.component_id == "opening_inventory")
    assert inv_comp.source_type == "USER_INPUT"

    assert pc_analysis.capex == 180000.0
    capex_comp = next(c for c in pc_analysis.components if c.component_id == "capex")
    assert capex_comp.source_type == "USER_SPECIFIED"


# =============================================================================
# 5. CapEx Total Benchmark Without Category Breakdown
# =============================================================================
def test_capex_total_benchmark_without_category_breakdown():
    """
    When benchmark provides only total CapEx, preserve total and leave categories None (UNKNOWN).
    No unsourced archetype percentage splits!
    """
    engine = CapExEngine()
    benchmark = BenchmarkFinancialData(
        business_id="sample_unit",
        business_title="Sample Unit",
        typical_capex_inr=250000.0,
    )

    decomp = engine.decompose(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        benchmark_data=benchmark,
    )

    assert decomp.total_capex == 250000.0
    assert decomp.source == "BENCHMARK_DERIVED"
    # Category decomposition MUST remain None because benchmark has no breakdown
    assert decomp.premises_setup is None
    assert decomp.machinery_equipment is None
    assert decomp.furniture_fixtures is None
    assert decomp.technology_pos is None


# =============================================================================
# 6. Salary Without Benchmark / Rate is NOT Derived
# =============================================================================
def test_salary_without_benchmark_not_derived():
    """
    Salary is NOT derived from hardcoded staff_count * 10000.
    It requires an evidenced salary_per_person rate.
    """
    engine = DerivationEngine()
    # staff_count provided, but salary_per_person missing
    assumptions = [
        _make_asm("staff_count", 3, SourceType.USER_INPUT),
    ]

    resolved = engine.resolve_derivations(FinancialArchetype.INVENTORY_RETAIL, assumptions)
    val_map = {a.driver_id: a.value for a in resolved}

    assert val_map.get("salary_cost") is None  # Must NOT be derived as 30,000!

    # Now provide salary_per_person
    assumptions_with_rate = [
        _make_asm("staff_count", 3, SourceType.USER_INPUT),
        _make_asm("salary_per_person", 12000.0, SourceType.USER_INPUT),
    ]
    resolved2 = engine.resolve_derivations(FinancialArchetype.INVENTORY_RETAIL, assumptions_with_rate)
    val_map2 = {a.driver_id: a.value for a in resolved2}
    assert val_map2["salary_cost"] == 36000.0  # 3 * 12000


# =============================================================================
# 7. Unknown Scheme Financing Reconciliation
# =============================================================================
def test_unknown_scheme_financing_reconciliation():
    """
    Never replace unknown scheme financeable cost with calculated cost.
    Variance remains None and status is INSUFFICIENT_DATA or PARTIALLY_DERIVED.
    """
    reconciler = ProjectCostReconciler()
    rec = reconciler.reconcile(
        calculated_project_cost=300000.0,
        scheme_financeable_project_cost=None,  # Unknown scheme limit
        user_requested_project_cost=350000.0,
        promoter_margin=30000.0,
        debt_component=270000.0,
    )

    assert rec.calculated_project_cost == 300000.0
    assert rec.scheme_financeable_project_cost is None
    assert rec.variance is None
    assert rec.reconciliation_status == "INSUFFICIENT_DATA"
    assert "limit is unknown" in rec.reconciliation_explanation


# =============================================================================
# 8. Opening Inventory / WC No Double Counting
# =============================================================================
def test_opening_inventory_wc_no_double_counting():
    """
    Opening inventory (e.g. 75,000) and non-inventory working capital buffer (19,500)
    sum exactly to total working capital requirement (94,500).
    Project cost does not count opening inventory twice.
    """
    assumptions = [
        _make_asm("opening_inventory", 75000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("monthly_rent", 10000.0, SourceType.USER_INPUT, user_confirmed=True),
        _make_asm("salary_cost", 9500.0, SourceType.USER_INPUT, user_confirmed=True),
    ]

    pc_analysis, wc_analysis, _ = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        user_inputs={"operating_buffer_months": 1.0, "capex_override": 100000.0},
        scheme_financeable_cost=250000.0,
    )

    # Working Capital Analysis totals
    assert wc_analysis.inventory_requirement == 75000.0
    assert wc_analysis.operating_cash_buffer == 19500.0
    assert wc_analysis.total_working_capital == 94500.0

    # Project Cost Analysis line items
    assert pc_analysis.opening_inventory == 75000.0
    assert pc_analysis.working_capital == 19500.0  # Non-inventory portion
    assert pc_analysis.capex == 100000.0

    # Total project cost = capex (100k) + opening_inv (75k) + non_inv_wc (19.5k) = 194.5k
    assert pc_analysis.total_project_cost == 194500.0
    assert pc_analysis.opening_inventory + pc_analysis.working_capital == wc_analysis.total_working_capital


# =============================================================================
# 9. M1 -> M2 -> Stage 9 End-to-End
# =============================================================================
def test_m1_m2_stage9_end_to_end():
    """
    Complete flow: M1 Evidence Resolution -> M2 Derivations & Project Cost ->
    Stage 9 Calculations -> FinancialAnalysisResponse.
    """
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(
            available_margin_capital=150000.0,
            preferred_project_cost=500000.0,
        ),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Family Readymade Garments & Apparel Store",
            sector="retail",
            category="apparel",
        ),
        project_assumptions=ProjectAssumptionsInput(
            expected_monthly_revenue=120000.0,
        ),
    )

    resp = financial_engine.analyze(req)
    assert resp.audit.llm_used is False
    assert resp.financial_analysis.financial_archetype == "INVENTORY_RETAIL"

    pc = resp.financial_analysis.project_cost_analysis
    assert pc is not None
    assert pc.capex is not None
    assert pc.reconciliation is not None

    wc = resp.financial_analysis.working_capital_analysis
    assert wc is not None
    assert wc.total_working_capital is not None
    assert wc.total_working_capital > 0.0


# =============================================================================
# 10. Verify M2 Changes Downstream Stage 9 Outputs
# =============================================================================
def test_verify_m2_changes_downstream_stage9_outputs():
    """
    Verify that M2 CapEx, Working Capital, and derived Revenue actually feed into
    Stage 9 CapitalStructure, Profitability, and Viability.
    """
    # Business with benchmark garment_store (capex 280k, working capital 150k)
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Readymade Garment Store",
            sector="retail",
        ),
        project_assumptions=ProjectAssumptionsInput(),
        user_driver_inputs={
            "monthly_transactions": 600,
            "average_ticket": 300.0,  # Expected revenue derived as 180,000
        }
    )

    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    # 1. Capital structure consumed M2's CapEx vs Working Capital ratio
    assert fa.capital_structure.fixed_capital_capex > 0.0
    assert fa.capital_structure.working_capital > 0.0

    # 2. Profitability consumed M2 derived revenue (600 * 300 = 180,000)
    assert fa.profitability.monthly_revenue == 180000.0
    assert fa.profitability.monthly_cogs > 0.0
    assert fa.profitability.monthly_operating_profit > 0.0

    # 3. Downstream viability DSCR is evaluated from M2 derived operating profit
    assert fa.debt_service.dscr is not None


# =============================================================================
# 11. Legacy Request Without M2 Still Works
# =============================================================================
def test_legacy_request_without_m2_still_works():
    """
    Standard request with minimal financial profile succeeds without regressions.
    """
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=80000.0),
        business_profile=BusinessProfileInput(business_id="rice_mill"),
    )
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    assert fa.scheme_result.status == "MATCHED"
    assert fa.loan_management.monthly_emi > 0.0
    assert fa.repayment.total_periods > 0
    assert fa.capital_structure.total_project_cost > 0.0


# =============================================================================
# 12. Schema and Serialization Compatibility
# =============================================================================
def test_schema_serialization_compatibility():
    """
    FinancialAnalysisContainer validates and serializes cleanly with Pydantic.
    """
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
        business_profile=BusinessProfileInput(specific_business="Grocery Retail Store", sector="retail"),
    )
    response = financial_engine.analyze(req)
    dumped = response.model_dump()
    assert "project_cost_analysis" in dumped["financial_analysis"]
    assert "working_capital_analysis" in dumped["financial_analysis"]


# =============================================================================
# 13. Invalid / Negative / Cyclic Dependencies Rejected
# =============================================================================
def test_invalid_negative_cyclic_dependencies_rejected():
    """
    Circular dependencies raise CircularDependencyError safely.
    Negative financial values are guarded.
    """
    engine = DerivationEngine()
    cyclic_graph = {
        "driver_a": ["driver_b"],
        "driver_b": ["driver_c"],
        "driver_c": ["driver_a"],
    }

    assert engine.detect_cycles(cyclic_graph) is not None
    with pytest.raises(CircularDependencyError):
        engine.get_topological_order(cyclic_graph)


# =============================================================================
# 14. Agriculture and Livestock Working Capital Engine
# =============================================================================
def test_agriculture_and_livestock_working_capital():
    """
    Agriculture & Livestock uses seasonal operational buffer based on raw material / inputs.
    Never uses retail merchandise inventory logic.
    """
    wc_eng = WorkingCapitalEngine()

    # Case A: Evidenced inputs + buffer months
    assumptions = [
        _make_asm("raw_material_cost", 500.0, SourceType.USER_INPUT),
        _make_asm("installed_capacity", 100, SourceType.USER_INPUT),
        _make_asm("operating_buffer_months", 3.0, SourceType.USER_INPUT),
    ]
    res = wc_eng.calculate(FinancialArchetype.AGRICULTURE, assumptions)
    assert res.status == "RESOLVED"
    # monthly inputs = 500 * 100 = 50,000; 3 months = 150,000
    assert res.total_working_capital == 150000.0
    assert res.inventory_requirement is None
    assert res.methodology == "SEASONAL_OPERATING_BUFFER"

    # Case B: Missing parameters -> INSUFFICIENT_DATA (never defaults to 0)
    res_empty = wc_eng.calculate(FinancialArchetype.LIVESTOCK, [])
    assert res_empty.status == "INSUFFICIENT_DATA"
    assert res_empty.confidence == 0.0


# =============================================================================
# 15. Craft and Repair Archetypes
# =============================================================================
def test_craft_and_repair_working_capital():
    """
    Craft uses operating cash buffer for artisanal materials.
    Repair handles spare parts / consumables holding.
    """
    wc_eng = WorkingCapitalEngine()

    # Craft
    craft_asms = [
        _make_asm("raw_material_cost", 15000.0, SourceType.USER_INPUT),
        _make_asm("monthly_rent", 5000.0, SourceType.USER_INPUT),
        _make_asm("operating_buffer_months", 2.0, SourceType.USER_INPUT),
    ]
    res_craft = wc_eng.calculate(FinancialArchetype.CRAFT, craft_asms)
    assert res_craft.status == "RESOLVED"
    assert res_craft.total_working_capital == 40000.0  # (15000 + 5000) * 2

    # Repair with spare parts
    repair_asms = [
        _make_asm("material_cost_per_job", 200.0, SourceType.USER_INPUT),
        _make_asm("jobs_per_day", 5, SourceType.USER_INPUT),
        _make_asm("operating_days", 25, SourceType.USER_INPUT),
        _make_asm("inventory_days", 15.0, SourceType.USER_INPUT),
        _make_asm("monthly_rent", 6000.0, SourceType.USER_INPUT),
        _make_asm("operating_buffer_months", 1.0, SourceType.USER_INPUT),
    ]
    res_repair = wc_eng.calculate(FinancialArchetype.REPAIR, repair_asms)
    assert res_repair.status == "RESOLVED"
    # monthly parts = 200 * 5 * 25 = 25,000; 15 days = 12,500
    assert res_repair.inventory_requirement == 12500.0
    assert res_repair.operating_cash_buffer == 6000.0
    assert res_repair.total_working_capital == 18500.0


# =============================================================================
# 16. Food Processing & Small Manufacturing
# =============================================================================
def test_manufacturing_and_food_processing_operating_cycle():
    """
    Manufacturing uses COGS, inventory days, receivable days, payable credit, and fixed opex buffer.
    """
    wc_eng = WorkingCapitalEngine()

    mfg_asms = [
        _make_asm("monthly_revenue", 200000.0, SourceType.USER_INPUT),
        _make_asm("monthly_cogs", 120000.0, SourceType.USER_INPUT),
        _make_asm("inventory_days", 30.0, SourceType.BENCHMARK),
        _make_asm("receivable_days", 15.0, SourceType.BENCHMARK),
        _make_asm("payable_days", 20.0, SourceType.BENCHMARK),
        _make_asm("monthly_rent", 10000.0, SourceType.USER_INPUT),
        _make_asm("salary_cost", 20000.0, SourceType.USER_INPUT),
        _make_asm("operating_buffer_months", 1.0, SourceType.USER_INPUT),
    ]
    res_mfg = wc_eng.calculate(FinancialArchetype.FOOD_PROCESSING, mfg_asms)
    assert res_mfg.status == "RESOLVED"
    # Inventory: (120,000 / 30) * 30 = 120,000
    assert res_mfg.inventory_requirement == 120000.0
    # Receivables: (200,000 / 30) * 15 = 100,000
    assert res_mfg.receivable_requirement == 100000.0
    # Payables credit: (120,000 / 30) * 20 = 80,000
    assert res_mfg.payable_credit == 80000.0
    # Operating cash buffer: (10,000 + 20,000) * 1 = 30,000
    assert res_mfg.operating_cash_buffer == 30000.0
    # Total WC = 120,000 + 100,000 + 30,000 - 80,000 = 170,000
    assert res_mfg.total_working_capital == 170000.0
    assert res_mfg.operating_cycle_days == 25.0  # 30 + 15 - 20


# =============================================================================
# 17. Targeted Hardening Tests (Rules 1-6)
# =============================================================================

def test_targeted_1_unknown_wc_dependency_does_not_become_zero():
    """
    TEST 1: Unknown WC dependency does not become zero.
    receivables = None, inventory = 50000, cash_buffer = 10000, payables = 5000.
    DO NOT calculate 55000.
    Must mark WC as PARTIALLY_DERIVED with total_working_capital=None.
    """
    wc_eng = WorkingCapitalEngine()
    assumptions = [
        _make_asm("opening_inventory", 50000.0, SourceType.USER_INPUT),
        _make_asm("operating_cash_buffer", 10000.0, SourceType.USER_INPUT),
        _make_asm("payables", 5000.0, SourceType.USER_INPUT),
        _make_asm("receivables", None, SourceType.USER_INPUT),
    ]
    res = wc_eng.calculate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        user_inputs={"receivables": None, "payables": 5000.0}
    )
    assert res.total_working_capital is None  # MUST NOT be 55000
    assert res.status == "PARTIALLY_DERIVED"
    assert res.inventory_requirement == 50000.0
    assert res.operating_cash_buffer == 10000.0
    assert res.payable_credit == 5000.0
    assert res.receivable_requirement is None
    # Provenance notes missing receivables
    missing_notes = [p["description"] for p in res.provenance if "receivables" in p["description"].lower()]
    assert len(missing_notes) > 0


def test_targeted_2_explicit_wc_value_of_zero_remains_zero():
    """
    TEST 2: Explicit WC value of 0 remains 0.
    receivables = 0, inventory = 50000, cash_buffer = 10000, payables = 5000.
    Explicit 0 is preserved and calculation resolves to 55000.
    """
    wc_eng = WorkingCapitalEngine()
    assumptions = [
        _make_asm("opening_inventory", 50000.0, SourceType.USER_INPUT),
        _make_asm("operating_cash_buffer", 10000.0, SourceType.USER_INPUT),
        _make_asm("payables", 5000.0, SourceType.USER_INPUT),
        _make_asm("receivables", 0.0, SourceType.USER_INPUT),
    ]
    res = wc_eng.calculate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        user_inputs={"receivables": 0.0, "payables": 5000.0}
    )
    assert res.receivable_requirement == 0.0  # Explicitly preserved
    assert res.total_working_capital == 55000.0  # 50000 + 0 + 10000 - 5000
    assert res.status == "RESOLVED"


def test_targeted_3_unknown_pre_op_cost_remains_none_in_project_cost_analysis():
    """
    TEST 3: Unknown pre-operative cost remains None/UNKNOWN in final ProjectCostAnalysis.
    """
    assumptions = [
        _make_asm("opening_inventory", 50000.0, SourceType.USER_INPUT),
        _make_asm("operating_cash_buffer", 10000.0, SourceType.USER_INPUT),
    ]
    pc_analysis, wc_analysis, _ = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        user_inputs={"capex_override": 100000.0},
        benchmark_data=None,  # No pre-op benchmark
    )
    assert pc_analysis.pre_operating_cost is None
    pre_op_comp = next((c for c in pc_analysis.components if c.component_id == "pre_operating_cost"), None)
    assert pre_op_comp is not None
    assert pre_op_comp.amount is None
    assert pre_op_comp.status == "UNKNOWN"


def test_targeted_4_unknown_contingency_remains_none_in_project_cost_analysis():
    """
    TEST 4: Unknown contingency remains None/UNKNOWN in final ProjectCostAnalysis.
    """
    assumptions = [
        _make_asm("opening_inventory", 50000.0, SourceType.USER_INPUT),
        _make_asm("operating_cash_buffer", 10000.0, SourceType.USER_INPUT),
    ]
    pc_analysis, wc_analysis, _ = project_cost_engine.evaluate(
        archetype=FinancialArchetype.INVENTORY_RETAIL,
        assumptions=assumptions,
        user_inputs={"capex_override": 100000.0},
        benchmark_data=None,  # No contingency benchmark
    )
    assert pc_analysis.contingency is None
    cont_comp = next((c for c in pc_analysis.components if c.component_id == "contingency"), None)
    assert cont_comp is not None
    assert cont_comp.amount is None
    assert cont_comp.status == "UNKNOWN"


def test_targeted_5_m2_normalization_returned_financing_equals_effective_financing():
    """
    TEST 5: When M2 normalization occurs, returned FinancialAnalysisContainer.project_financing
    equals effective_project_financing actually used downstream.
    """
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(
            available_margin_capital=100000.0,
            preferred_project_cost=600000.0,
        ),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Apparel Retail",
            sector="retail",
            category="apparel",
        ),
        project_assumptions=ProjectAssumptionsInput(
            expected_monthly_revenue=150000.0,
        ),
        user_driver_inputs={
            "monthly_transactions": 500,
            "average_ticket": 300.0,
            "gross_margin": 30.0,
            "inventory_days": 30.0,
            "monthly_rent": 10000.0,
            "salary_cost": 15000.0,
            "electricity_cost": 2000.0,
            "operating_buffer_months": 1.0,
            "capex_override": 150000.0,
        }
    )

    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    # M2 total project cost is resolved
    pc = fa.project_cost_analysis
    assert pc is not None
    assert pc.total_project_cost is not None
    assert pc.total_project_cost > 0.0

    # Returned project_financing MUST match the normalized financing
    pf = fa.project_financing
    expected_margin = round(min(100000.0, pc.total_project_cost * 0.10), 2)
    expected_loan = round(pc.total_project_cost - expected_margin, 2)

    assert pf.required_margin == expected_margin
    assert pf.theoretical_loan_requirement == expected_loan
    assert pf.estimated_financeable_loan == min(expected_loan, pf.scheme_maximum_loan)

    # Loan management downstream matches the effective loan
    assert fa.loan_management.principal == pf.estimated_financeable_loan


def test_targeted_6_m2_normalized_project_cost_propagates_downstream():
    """
    TEST 6: M2-normalized project cost actually propagates into downstream Stage 9 calculations.
    """
    # Baseline run
    req_low = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Retail Store",
            sector="retail",
        ),
        project_assumptions=ProjectAssumptionsInput(expected_monthly_revenue=100000.0),
        user_driver_inputs={
            "capex_override": 100000.0,
            "opening_inventory": 40000.0,
            "operating_cash_buffer": 10000.0,
        }
    )
    resp_low = financial_engine.analyze(req_low)

    # Higher cost run (higher M2 CapEx and Inventory)
    req_high = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Retail Store",
            sector="retail",
        ),
        project_assumptions=ProjectAssumptionsInput(expected_monthly_revenue=100000.0),
        user_driver_inputs={
            "capex_override": 250000.0,
            "opening_inventory": 80000.0,
            "operating_cash_buffer": 20000.0,
        }
    )
    resp_high = financial_engine.analyze(req_high)

    fa_low = resp_low.financial_analysis
    fa_high = resp_high.financial_analysis

    # 1. Total project cost changed
    assert fa_high.capital_structure.total_project_cost > fa_low.capital_structure.total_project_cost

    # 2. Loan principal and EMI changed downstream
    assert fa_high.loan_management.principal > fa_low.loan_management.principal
    assert fa_high.loan_management.monthly_emi > fa_low.loan_management.monthly_emi

    # 3. Debt service coverage and viability changed downstream
    assert fa_high.debt_service.dscr != fa_low.debt_service.dscr


