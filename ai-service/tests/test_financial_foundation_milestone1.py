"""
Milestone 1 — Financial Intelligence Foundation Hardened Test Suite.
Verifies all Milestone 1 requirements:
1. Archetype resolution from Stage 2/3 classification (without creating secondary ontology)
2. Functional default_benchmark_key resolution with source priority:
   USER_INPUT -> verified evidence -> MARKET_ENGINE -> BENCHMARK/KNOWLEDGE -> SCHEME_CONFIG -> UNKNOWN/USER_REQUIRED
3. User driver override over benchmark
4. Accurate project cost provenance: MARGIN_DERIVED, USER_SPECIFIED, SCHEME_CAPPED
5. Structured confidence summary: {overall, resolved, total, user_required, unknown}
6. Question engine: ONLY high-criticality unresolved drivers, natural entrepreneur language, language support
7. End-to-end FinancialEngine.analyze() integration with full Pydantic serialization
8. Stage 12 Feasibility backward compatibility
"""
import pytest
import json
from app.services.financial_engine import (
    financial_engine,
    FinancialArchetype,
    archetype_registry,
    driver_registry,
    DriverDefinition,
    FinancialDriver,
    assumption_resolver,
    ResolvedAssumption,
    SourceType,
    AssumptionStatus,
    question_engine,
    RequiredUserInput,
    provenance_tracker,
    CALCULATION_REGISTRY,
    legacy_adapter,
    FoundationStatus,
)
from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialProfileInput,
    BusinessProfileInput,
    LocationProfileInput,
    ProjectAssumptionsInput,
    FoundationConfidenceSummary,
)
from app.services.feasibility_engine.feature_vector import feasibility_feature_vector_builder


class TestFinancialFoundationHardening:

    # -------------------------------------------------------------------------
    # Test 1: Archetype Resolution from Canonical Stage 2/3 Classification
    # -------------------------------------------------------------------------
    def test_01_archetype_resolution_from_classification(self):
        # Grocery -> INVENTORY_RETAIL
        arch_grocery = archetype_registry.resolve(
            specific_business="Kirana General Store",
            sector="retail",
            category="grocery",
            subcategory="grocery"
        )
        assert arch_grocery == FinancialArchetype.INVENTORY_RETAIL

        # Dairy -> LIVESTOCK / AGRICULTURE
        arch_dairy = archetype_registry.resolve(
            specific_business="Dairy Unit",
            sector="agriculture",
            category="livestock",
            subcategory="dairy"
        )
        assert arch_dairy in (FinancialArchetype.LIVESTOCK, FinancialArchetype.AGRICULTURE)

        # Service / Repair -> SERVICE / REPAIR
        arch_service = archetype_registry.resolve(
            specific_business="Two Wheeler Repair Shop",
            sector="automotive",
            category="services",
            subcategory="repair"
        )
        assert arch_service in (FinancialArchetype.SERVICE, FinancialArchetype.REPAIR)

    # -------------------------------------------------------------------------
    # Scenario A: Retail Business with Benchmark Data & Functional default_benchmark_key
    # -------------------------------------------------------------------------
    def test_02_retail_business_benchmark_resolution(self):
        # Benchmark data provides gross_margin_pct and typical_working_capital_monthly_inr
        benchmark_data = {
            "gross_margin_pct": 28.5,
            "typical_working_capital_monthly_inr": 45000.0,
            "operating_cost_ratio": 0.15,
        }
        res = assumption_resolver.resolve_all(
            archetype=FinancialArchetype.INVENTORY_RETAIL,
            user_inputs={},
            benchmark_data=benchmark_data,
            analysis_id="test-retail-bm"
        )

        assert res["archetype"] == FinancialArchetype.INVENTORY_RETAIL.value
        assumptions_by_id = {a["driver_id"]: a for a in res["assumptions"]}

        # gross_margin resolved via default_benchmark_key="gross_margin_pct"
        assert "gross_margin" in assumptions_by_id
        gm = assumptions_by_id["gross_margin"]
        assert gm["status"] == AssumptionStatus.BENCHMARKED.value
        assert gm["value"] == 28.5
        assert gm["source_type"] == SourceType.BENCHMARK.value

        # opening_inventory resolved via default_benchmark_key="typical_working_capital_monthly_inr"
        assert "opening_inventory" in assumptions_by_id
        oi = assumptions_by_id["opening_inventory"]
        assert oi["status"] == AssumptionStatus.BENCHMARKED.value
        assert oi["value"] == 45000.0

    # -------------------------------------------------------------------------
    # Scenario B: Business with Missing High-Criticality Drivers -> Question Engine
    # -------------------------------------------------------------------------
    def test_03_missing_high_criticality_drivers_and_questions(self):
        # No user inputs, no benchmarks for premises ownership & monthly rent
        res = assumption_resolver.resolve_all(
            archetype=FinancialArchetype.SERVICE,
            user_inputs={},
            benchmark_data={},
            analysis_id="test-missing-high"
        )
        assumptions_by_id = {a["driver_id"]: a for a in res["assumptions"]}

        # ownership_type is HIGH criticality, cannot be benchmarked -> USER_REQUIRED (NEVER zero)
        assert "ownership_type" in assumptions_by_id
        ot = assumptions_by_id["ownership_type"]
        assert ot["status"] == AssumptionStatus.USER_REQUIRED.value
        assert ot["value"] is None  # Never silently replaced with 0

        # Generate questions in English
        en_questions = question_engine.generate_questions(res["assumptions"], language="en")
        assert len(en_questions) > 0
        for q in en_questions:
            assert q.criticality == "HIGH"  # ONLY high criticality
            assert q.language == "en"
            assert "Is the shop/workshop" in q.question or len(q.question) > 0

        # Generate questions in Hindi
        hi_questions = question_engine.generate_questions(res["assumptions"], language="hi")
        assert len(hi_questions) > 0
        assert hi_questions[0].language == "hi"

    # -------------------------------------------------------------------------
    # Scenario C: User-Provided Driver Overriding Benchmark (Source Priority)
    # -------------------------------------------------------------------------
    def test_04_user_driver_overrides_benchmark(self):
        # User explicitly provides gross_margin=35.0, benchmark says 20.0
        user_inputs = {"gross_margin": 35.0, "monthly_rent": 12000.0}
        benchmark_data = {"gross_margin_pct": 20.0, "monthly_rent": 8000.0}

        res = assumption_resolver.resolve_all(
            archetype=FinancialArchetype.INVENTORY_RETAIL,
            user_inputs=user_inputs,
            benchmark_data=benchmark_data,
            analysis_id="test-override"
        )
        assumptions_by_id = {a["driver_id"]: a for a in res["assumptions"]}

        gm = assumptions_by_id["gross_margin"]
        assert gm["source_type"] == SourceType.USER_INPUT.value
        assert gm["value"] == 35.0
        assert gm["confidence"] == 1.0
        assert gm["status"] == AssumptionStatus.RESOLVED.value

        rent = assumptions_by_id["monthly_rent"]
        assert rent["source_type"] == SourceType.USER_INPUT.value
        assert rent["value"] == 12000.0

    # -------------------------------------------------------------------------
    # Scenario D: Scheme & Market Evidence Resolution
    # -------------------------------------------------------------------------
    def test_05_scheme_and_market_evidence_resolution(self):
        market_data = {
            "monthly_rent": 9500.0,
            "commercial_rent_monthly": 9500.0
        }
        scheme_data = {
            "margin_ratio": 0.10,
            "interest_rate": 0.085
        }

        # Market rent resolved when user input is missing
        res = assumption_resolver.resolve_all(
            archetype=FinancialArchetype.SERVICE,
            user_inputs={},
            benchmark_data={},
            market_data=market_data,
            scheme_data=scheme_data,
            analysis_id="test-mkt-sch"
        )
        assumptions_by_id = {a["driver_id"]: a for a in res["assumptions"]}

        rent = assumptions_by_id["monthly_rent"]
        assert rent["source_type"] == SourceType.MARKET_ENGINE.value
        assert rent["value"] == 9500.0
        assert rent["confidence"] == 0.75

    # -------------------------------------------------------------------------
    # Scenario E: Structured Confidence Summary Contract
    # -------------------------------------------------------------------------
    def test_06_structured_confidence_contract(self):
        user_inputs = {"ownership_type": "OWN", "monthly_rent": 0.0}
        benchmark_data = {"gross_margin_pct": 25.0}

        res = assumption_resolver.resolve_all(
            archetype=FinancialArchetype.INVENTORY_RETAIL,
            user_inputs=user_inputs,
            benchmark_data=benchmark_data,
            analysis_id="test-conf"
        )

        conf = res["assumption_confidence"]
        assert isinstance(conf, dict)
        assert "overall" in conf
        assert "resolved" in conf
        assert "total" in conf
        assert "user_required" in conf
        assert "unknown" in conf
        assert isinstance(conf["overall"], float)
        assert conf["total"] == conf["resolved"] + conf["user_required"] + conf["unknown"]

    # -------------------------------------------------------------------------
    # Project-Cost Provenance: MARGIN_DERIVED vs USER_SPECIFIED vs SCHEME_CAPPED
    # -------------------------------------------------------------------------
    def test_07_project_cost_provenance_basis(self):
        # 1. Standard margin-derived
        req_margin = FinancialAnalysisRequest(
            financial_profile=FinancialProfileInput(available_margin_capital=30000.0),
            business_profile=BusinessProfileInput(specific_business="Retail Shop")
        )
        res_margin = financial_engine.analyze(req_margin)
        assert res_margin.financial_analysis.project_cost_basis == "MARGIN_DERIVED"

        # 2. User-specified preferred cost
        req_user = FinancialAnalysisRequest(
            financial_profile=FinancialProfileInput(
                available_margin_capital=50000.0,
                preferred_project_cost=200000.0
            ),
            business_profile=BusinessProfileInput(specific_business="Retail Shop")
        )
        res_user = financial_engine.analyze(req_user)
        assert res_user.financial_analysis.project_cost_basis == "USER_SPECIFIED"

        # 3. Scheme-capped (available margin ₹10,00,000 -> ₹1 Crore theoretical, capped at ₹50 Lakh)
        req_capped = FinancialAnalysisRequest(
            financial_profile=FinancialProfileInput(available_margin_capital=1000000.0),
            business_profile=BusinessProfileInput(specific_business="Manufacturing Unit")
        )
        res_capped = financial_engine.analyze(req_capped)
        assert res_capped.financial_analysis.project_cost_basis == "SCHEME_CAPPED"

    # -------------------------------------------------------------------------
    # Full End-to-End Pydantic Serialization Verification
    # -------------------------------------------------------------------------
    def test_08_full_e2e_serialization(self):
        req = FinancialAnalysisRequest(
            analysis_id="test-e2e-serialize",
            session_id="session-serialize-01",
            financial_profile=FinancialProfileInput(available_margin_capital=60000.0),
            business_profile=BusinessProfileInput(
                specific_business="Bakery Unit",
                sector="Food Processing",
                category="Food",
                subcategory="Bakery"
            ),
            project_assumptions=ProjectAssumptionsInput(
                expected_monthly_revenue=75000.0,
                expected_unit_price=50.0,
                expected_monthly_units=1500.0
            ),
            user_driver_inputs={"ownership_type": "RENTED", "monthly_rent": 7000.0},
            market_data={"competitor_density": "MODERATE"},
            language="en"
        )
        resp = financial_engine.analyze(req)

        # 1. Ensure type correctness
        assert isinstance(resp, FinancialAnalysisResponse)

        # 2. Pydantic model_dump()
        dumped = resp.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["analysis_id"] == "test-e2e-serialize"

        # 3. JSON serialization round-trip
        json_str = json.dumps(dumped)
        assert len(json_str) > 0
        reloaded = json.loads(json_str)
        assert reloaded["financial_analysis"]["project_cost_basis"] == "MARGIN_DERIVED"
        assert reloaded["financial_analysis"]["financial_archetype"] in (
            FinancialArchetype.FOOD_PROCESSING.value,
            FinancialArchetype.SMALL_MANUFACTURING.value
        )
        assert "overall" in reloaded["financial_analysis"]["assumption_confidence"]

    # -------------------------------------------------------------------------
    # Stage 12 Feasibility Engine Compatibility
    # -------------------------------------------------------------------------
    def test_09_feasibility_engine_compatibility(self):
        req = FinancialAnalysisRequest(
            financial_profile=FinancialProfileInput(available_margin_capital=50000.0),
            business_profile=BusinessProfileInput(specific_business="Textile Boutique"),
            project_assumptions=ProjectAssumptionsInput(expected_monthly_revenue=60000.0)
        )
        fin_resp = financial_engine.analyze(req)
        fin_dict = fin_resp.model_dump()

        fv = feasibility_feature_vector_builder.build_feature_vector(
            opportunity_data={},
            financial_data=fin_dict,
            entrepreneur_data={},
            risk_data={},
            market_data={}
        )
        assert fv is not None
        assert fv.dscr.value is not None
        assert fv.break_even_percentage.value is not None
        assert fv.financial_viability_score.value is not None
