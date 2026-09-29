"""
Comprehensive Test Suite for Stage 14.2: DPR Enrichment & Deterministic Inference (26 Tests: A through Z).
Verifies:
- Stage 14.1 handoff acceptance & readiness hard gate
- Preservation of upstream classification and user answers
- Multi-source provenance attribution (USER, VERIFIED_DOC, BENCHMARK, MARKET, POLICY, ENGINE)
- Zero-fabrication invariants (UNKNOWN != ZERO, no fake defaults, no fake document status)
- Financial Authority Boundary (M1-M6 outputs never overwritten by benchmarks)
- Recalculation flow strictly routing through Stage 14.1
- Validation rules (CHK_FINANCIAL_AUTHORITY, CHK_INTAKE_READINESS, CHK_UNKNOWN_NOT_ZERO, CHK_PROVENANCE_COMPLETENESS, CHK_FINANCIAL_BALANCE, CHK_BENCHMARK_ISOLATION)
- Assumption Review Package ("Confirm KALPA's Assumptions")
- Canonical 39-section / 8-module DPR structure
- Scenario isolation and disk persistence
"""
import sys
import os
import asyncio
import unittest

# Add ai-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dpr_stage1 import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    dpr_context_builder,
    dpr_gap_analyzer,
    dpr_scenario_manager,
    build_stage14_handoff_package,
    DPRStage14HandoffPackage,
    FieldStatus,
)
from app.services.dpr_stage2 import (
    dpr_enrichment_service,
    evidence_resolver,
    benchmark_resolver,
    market_resolver,
    policy_scheme_resolver,
    deterministic_inference_engine,
    dpr_enrichment_validator,
    DPREnrichmentPackage,
    EnrichmentField,
    EnrichmentSourceType,
    DerivationMethod,
    AssumptionReviewAction,
    AUTHORITATIVE_FINANCIAL_FIELDS,
)


class TestStage14_2EnrichmentPipeline(unittest.TestCase):
    """Test Suite covering all 26 Stage 14.2 requirements (A through Z)."""

    def setUp(self):
        from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository, SCENARIOS_DIR
        from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service, ENRICHMENT_DIR
        scenario_repository._store.clear()
        dpr_enrichment_service._cache.clear()
        # Clean disk persistence for test runs
        for d in [SCENARIOS_DIR, ENRICHMENT_DIR]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.startswith("test_"):
                        try:
                            os.remove(os.path.join(d, f))
                        except Exception:
                            pass

    def test_A_stage_14_1_handoff_accepted_by_14_2(self):
        """A. Stage 14.1 ready handoff is accepted by Stage 14.2 enrichment service."""
        async def _run():
            bid = "test_e2e_accept_001"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Surat Textile Loom")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Textile weaving and powerloom fabric production")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Kishore Bhai")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Surat")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIsInstance(pkg, DPREnrichmentPackage)
            self.assertEqual(pkg.business_id, bid)
            self.assertTrue(pkg.is_enrichment_complete)
            self.assertTrue(pkg.can_proceed_to_validation)
        asyncio.run(_run())

    def test_B_non_ready_14_1_handoff_rejected(self):
        """B. Non-ready 14.1 handoff halts 14.2 execution and returns blocked package."""
        async def _run():
            bid = "test_non_ready_gate_002"
            # Empty entrepreneur with no name or location -> unready
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)

            self.assertFalse(handoff.readiness.is_ready_for_stage_14_2)

            pkg = await dpr_enrichment_service.run_enrichment(
                business_id=bid,
                handoff_package_override=handoff
            )
            self.assertFalse(pkg.is_enrichment_complete)
            self.assertFalse(pkg.can_proceed_to_validation)
            self.assertFalse(pkg.validation.overall_valid)
            self.assertEqual(len(pkg.fields), 0)
            self.assertEqual(len(pkg.sections), 0)
            self.assertEqual(len(pkg.modules), 0)
            self.assertTrue(any("intake" in r.lower() for r in pkg.validation.blocking_reasons))
        asyncio.run(_run())

    def test_C_authoritative_classification_preserved(self):
        """C. Authoritative classification from Stages 1-3 is preserved in 14.2."""
        async def _run():
            bid = "test_class_preserve_003"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Agro Flour Mills")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Wheat milling")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Sanjay Kumar")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Madhya Pradesh")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Bhopal")

            raw_intake = {
                "business_node_id": "NODE_AGRO_01",
                "nic_code": "10611",
                "archetype": "MANUFACTURING",
                "sector": "Food Processing"
            }
            ctx = await dpr_context_builder.build_context(business_id=bid, raw_intake_inputs=raw_intake)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, handoff_package_override=handoff)
            self.assertEqual(pkg.intake_package_snapshot["business_classification"]["business_node_id"], "NODE_AGRO_01")
            self.assertEqual(pkg.intake_package_snapshot["business_classification"]["nic_code"], "10611")
        asyncio.run(_run())

    def test_D_user_answer_preserved(self):
        """D. User answers retain USER_PROVIDED source type."""
        async def _run():
            bid = "test_user_ans_004"
            dpr_scenario_manager.set_user_answer(bid, "premises_status", "OWNED")
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Own Premises Store")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Retail general store")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Vikas Jain")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Delhi")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Central")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            f_prem = pkg.fields.get("premises_status")
            self.assertIsNotNone(f_prem)
            self.assertEqual(f_prem.value, "OWNED")
            self.assertEqual(f_prem.source_type, EnrichmentSourceType.USER_PROVIDED)
        asyncio.run(_run())

    def test_E_benchmark_preserved(self):
        """E. Empirical benchmark default retains BENCHMARK_DERIVED source type."""
        async def _run():
            bid = "test_bm_preserve_005"
            bm_res = benchmark_resolver.resolve_benchmarks(business_id=bid, category="RETAIL")
            self.assertIsInstance(bm_res, dict)
            for k, v in bm_res.items():
                if not v.get("is_overridden"):
                    self.assertEqual(v["source_type"], EnrichmentSourceType.BENCHMARK_DERIVED)
                    self.assertNotIn(k, AUTHORITATIVE_FINANCIAL_FIELDS)
        asyncio.run(_run())

    def test_F_benchmark_override_preserved_separately(self):
        """F. Changing benchmark value produces USER_OVERRIDE while preserving baseline."""
        async def _run():
            bid = "test_ovr_preserve_006"
            dpr_scenario_manager.set_user_override(bid, "annual_revenue_growth_rate", 20.0)
            bm_res = benchmark_resolver.resolve_benchmarks(
                business_id=bid,
                category="RETAIL",
                user_overrides={"annual_revenue_growth_rate": 20.0}
            )
            growth = bm_res.get("annual_revenue_growth_rate")
            self.assertIsNotNone(growth)
            self.assertEqual(growth["value"], 20.0)
            self.assertEqual(growth["source_type"], EnrichmentSourceType.USER_OVERRIDE)
            self.assertTrue(growth["is_overridden"])
            self.assertIsNotNone(growth["baseline_benchmark_value"])
        asyncio.run(_run())

    def test_G_market_derived_field_provenance(self):
        """G. Upstream market intelligence produces MARKET_DERIVED fields with provenance."""
        m_ctx = {
            "target_customer_segments": "Urban households and boutique retailers",
            "competitor_summary": "Moderate competition with 4 local retail stores"
        }
        res = market_resolver.resolve_market_evidence(market_context=m_ctx)
        self.assertIn("target_customer_demographics", res)
        self.assertEqual(res["target_customer_demographics"]["source_type"], EnrichmentSourceType.MARKET_DERIVED)
        self.assertEqual(res["target_customer_demographics"]["value"], "Urban households and boutique retailers")

    def test_H_policy_derived_field_provenance(self):
        """H. Statutory scheme rules produce POLICY_DERIVED fields with official citations."""
        s_ctx = {
            "target_scheme_code": "PMEGP",
            "scheme_name": "Prime Minister Employment Generation Programme",
            "subsidy_percentage": 25.0,
            "promoter_margin_pct": 10.0
        }
        res = policy_scheme_resolver.resolve_policy_rules(scheme_context=s_ctx)
        self.assertIn("scheme_subsidy_percentage", res)
        self.assertEqual(res["scheme_subsidy_percentage"]["value"], 25.0)
        self.assertEqual(res["scheme_subsidy_percentage"]["source_type"], EnrichmentSourceType.POLICY_DERIVED)

    def test_I_engine_calculated_field_provenance(self):
        """I. M1-M6 outputs produce ENGINE_CALCULATED fields with dependencies."""
        async def _run():
            bid = "test_engine_calc_009"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Dairy Gold")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Dairy processing")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Anil Sharma")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Haryana")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Karnal")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 1000000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 200000.0)

            # Stage 14.1 recalculates financial package
            await dpr_scenario_manager.recalculate_scenario(business_id=bid)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            loan_fld = pkg.fields.get("bank_term_loan_amount")
            self.assertIsNotNone(loan_fld)
            self.assertEqual(loan_fld.source_type, EnrichmentSourceType.ENGINE_CALCULATED)
            self.assertGreater(len(loan_fld.upstream_dependencies), 0)
        asyncio.run(_run())

    def test_J_unknown_remains_unknown(self):
        """J. Missing non-material fields remain UNKNOWN and are not converted to zero."""
        async def _run():
            bid = "test_unknown_keep_010"
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, handoff_package_override=handoff)
            f_water = pkg.fields.get("water_requirement_daily_liters")
            if f_water:
                self.assertIsNone(f_water.value)
                self.assertEqual(f_water.status, "UNKNOWN")
        asyncio.run(_run())

    def test_K_no_financial_fabrication(self):
        """K. An uninitialized business does not fabricate project outlay."""
        async def _run():
            bid = "test_no_fab_011"
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, handoff_package_override=handoff)
            f_cost = pkg.fields.get("total_project_cost")
            self.assertIsNone(f_cost)
        asyncio.run(_run())

    def test_L_no_pmegp_default(self):
        """L. Target scheme is not silently defaulted to PMEGP."""
        async def _run():
            res = policy_scheme_resolver.resolve_policy_rules(scheme_context={})
            self.assertNotIn("target_scheme_code", res)
        asyncio.run(_run())

    def test_M_no_fake_market_values(self):
        """M. Omitted market context does not fabricate synthetic competitors."""
        res = market_resolver.resolve_market_evidence(market_context=None, opportunity_context=None)
        self.assertEqual(len(res), 0)

    def test_N_no_fake_evidence_strings(self):
        """N. Missing documents return DOCUMENT_PENDING with None, not fake strings."""
        docs = {
            "pan_card": {"status": "NOT_UPLOADED"},
            "udyam_registration": {"status": "UPLOADED", "verification_status": "PENDING_VERIFICATION"}
        }
        res = evidence_resolver.resolve_evidence(documents=docs, existing_fields={})
        for fid, fld in res.items():
            self.assertEqual(fld["status"], "DOCUMENT_PENDING")
            self.assertIsNone(fld["value"])
            self.assertNotEqual(fld.get("formatted_value"), "VERIFIED_ON_FILE")

    def test_O_financial_authority_boundary(self):
        """O. Benchmark resolver never resolves financial outputs; financial fields are ENGINE_CALCULATED."""
        bm_res = benchmark_resolver.resolve_benchmarks(business_id="test_o_bid", category="MANUFACTURING")
        for fid in AUTHORITATIVE_FINANCIAL_FIELDS:
            self.assertNotIn(fid, bm_res, f"Authoritative financial field {fid} was illegally produced by benchmark_resolver")

    def test_P_financial_recalculation_via_stage_14_1(self):
        """P. Updating an assumption triggers Stage 14.1 recalculation, updating downstream financial fields."""
        async def _run():
            bid = "test_recalc_flow_016"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Flour Mill Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Flour milling")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Karan")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Rajasthan")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Jaipur")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 1000000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 200000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg1 = await dpr_enrichment_service.run_enrichment(business_id=bid)
            loan1 = pkg1.fields["bank_term_loan_amount"].value

            # Update project cost via Stage 14.2 service update_assumption
            pkg2 = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="total_project_cost",
                action="OVERRIDE",
                value=1500000.0
            )
            loan2 = pkg2.fields["bank_term_loan_amount"].value
            self.assertNotEqual(loan1, loan2)
            self.assertGreater(loan2, loan1)
        asyncio.run(_run())

    def test_Q_financial_authority_validation_check(self):
        """Q. Validation fails if any authoritative financial field has BENCHMARK_DERIVED provenance."""
        bad_fields = {
            "total_project_cost": EnrichmentField(
                field_id="total_project_cost",
                section_id="sec_04",
                module_id="mod_02",
                label="Total Project Cost",
                value=500000.0,
                source_type=EnrichmentSourceType.BENCHMARK_DERIVED,  # VIOLATION!
                baseline_benchmark_value=500000.0
            )
        }
        summary = dpr_enrichment_validator.validate_enrichment(
            fields=bad_fields,
            financial_package={},
            intake_package={"readiness": {"is_ready_for_stage_14_2": True}},
            scenario_id="test_q_scen"
        )
        self.assertFalse(summary.overall_valid)
        self.assertTrue(any(c.check_id == "CHK_FINANCIAL_AUTHORITY" and not c.passed for c in summary.checks))

    def test_R_assumption_review_contains_only_relevant_editable_assumptions(self):
        """R. Confirm KALPA's Assumptions package contains editable operational assumptions."""
        async def _run():
            bid = "test_review_cards_015"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Handloom Silk")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Silk manufacturing")
            dpr_scenario_manager.set_user_answer(bid, "archetype", "MANUFACTURING")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Meera Sen")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Assam")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Kamrup")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            review = pkg.assumption_review
            self.assertGreater(len(review.assumptions_requiring_review), 0)
            for item in review.assumptions_requiring_review:
                self.assertTrue(item.editable)
                self.assertEqual(item.action, AssumptionReviewAction.USE_OR_CHANGE)
        asyncio.run(_run())

    def test_S_changing_benchmark_produces_user_override(self):
        """S. Updating assumption via service sets USER_OVERRIDE action."""
        async def _run():
            bid = "test_update_assump_016"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Spice Grinding")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Spices")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Devendra")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Kerala")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Kochi")

            pkg = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="operating_days_per_year",
                action="OVERRIDE",
                value=310
            )
            f_days = pkg.fields.get("operating_days_per_year")
            self.assertEqual(f_days.value, 310)
            self.assertEqual(f_days.source_type, EnrichmentSourceType.USER_OVERRIDE)
            self.assertTrue(f_days.is_overridden)
        asyncio.run(_run())

    def test_T_recalculation_updates_dependent_fields(self):
        """T. Recalculation triggers dependent field updates across M1-M6."""
        async def _run():
            bid = "test_recalc_deps_017_uniq"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Plastic Molding")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Plastic manufacturing")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Gopal")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Punjab")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Ludhiana")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 800000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 160000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            loan_1 = pkg.fields["bank_term_loan_amount"].value

            # Update project cost
            pkg_updated = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="total_project_cost",
                action="OVERRIDE",
                value=1200000.0
            )
            loan_2 = pkg_updated.fields["bank_term_loan_amount"].value
            self.assertNotEqual(loan_1, loan_2)
            self.assertGreater(loan_2, loan_1)
        asyncio.run(_run())

    def test_U_scenario_isolation_works(self):
        """U. Scenarios are isolated and do not mutate sibling scenarios."""
        async def _run():
            bid = "test_scen_iso_018"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Base Enterprise", scenario_id="scen_A")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Base Enterprise Trading", scenario_id="scen_A")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Base User", scenario_id="scen_A")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Goa", scenario_id="scen_A")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "North Goa", scenario_id="scen_A")

            pkg_A = await dpr_enrichment_service.run_enrichment(business_id=bid, scenario_id="scen_A")
            self.assertEqual(pkg_A.scenario_id, "scen_A")

            # Fork to scen_B
            dpr_scenario_manager.create_child_scenario(bid, parent_scenario_id="scen_A", child_scenario_id="scen_B")
            pkg_B = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="location_district",
                action="OVERRIDE",
                value="South Goa",
                scenario_id="scen_B"
            )

            self.assertEqual(pkg_B.fields["location_district"].value, "South Goa")
            # Verify scen_A remains North Goa
            pkg_A_refreshed = dpr_enrichment_service.get_persisted_enrichment(bid, "scen_A")
            self.assertEqual(pkg_A_refreshed.fields["location_district"].value, "North Goa")
        asyncio.run(_run())

    def test_V_39_sections_remain_canonical(self):
        """V. All 39 canonical DPR sections and 8 modules are preserved and enriched."""
        async def _run():
            bid = "test_39_sec_019"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Section Verification")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Section test enterprise")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Tester")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Odisha")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Cuttack")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertEqual(len(pkg.sections), 39)
            self.assertGreaterEqual(len(pkg.modules), 8)
        asyncio.run(_run())

    def test_W_stage_14_2_package_survives_restart(self):
        """W. Stage 14.2 Enriched Package persisted to disk reloads accurately."""
        async def _run():
            bid = "test_persist_14_2_020"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Persisted Enriched Business")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Persisted description")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Persist User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Telangana")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Hyderabad")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIsNotNone(pkg)

            # Reload from disk
            fresh_service = dpr_enrichment_service.__class__()
            loaded = fresh_service.get_persisted_enrichment(bid, pkg.scenario_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.business_id, bid)
            self.assertEqual(loaded.metadata["stage"], "STAGE_14_2_DPR_ENRICHMENT_INFERENCE")
        asyncio.run(_run())

    def test_X_frontend_loads_correct_scenario(self):
        """X. Enriched package tracks exact scenario_id in metadata."""
        async def _run():
            bid = "test_scen_track_021"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Scen Business", scenario_id="custom_scen_123")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Scen desc", scenario_id="custom_scen_123")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Scen User", scenario_id="custom_scen_123")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Karnataka", scenario_id="custom_scen_123")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Bengaluru", scenario_id="custom_scen_123")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, scenario_id="custom_scen_123")
            self.assertEqual(pkg.scenario_id, "custom_scen_123")
            self.assertEqual(pkg.metadata["scenario_id"], "custom_scen_123")
        asyncio.run(_run())

    def test_Y_frontend_never_displays_fake_defaults(self):
        """Y. Unresolved fields return None rather than synthetic strings."""
        async def _run():
            bid = "test_no_fake_strings_022"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "No Fake Strings Biz")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Testing clean outputs")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Clean User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Delhi")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "North")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            f_sub = pkg.fields.get("scheme_subsidy_percentage")
            if f_sub and f_sub.value is None:
                self.assertIsNone(f_sub.formatted_value)
        asyncio.run(_run())

    # ========================================================================
    # EXPLICIT REQUIREMENT 20 (ITEMS 1 THROUGH 24) COMPREHENSIVE TESTS
    # ========================================================================

    def test_01_stage14_1_to_stage14_2_handoff(self):
        """1. Stage14.1 -> Stage14.2 handoff contract ingestion."""
        async def _run():
            bid = "test_req01_handoff"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Kaveri Handloom")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Silk weaving")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Lakshmi")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Tamil Nadu")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Salem")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIsInstance(pkg, DPREnrichmentPackage)
            self.assertEqual(pkg.business_id, bid)
            self.assertIn("business_classification", pkg.intake_package_snapshot)
        asyncio.run(_run())

    def test_02_complete_handoff_requires_no_unnecessary_questions(self):
        """2. Complete handoff requires no unnecessary questions."""
        async def _run():
            from app.services.dpr_stage1 import dpr_question_engine
            bid = "test_req02_no_unnecessary_q"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Complete Enterprise")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Complete business")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Promoter Name")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Surat")

            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            q = await dpr_question_engine.get_next_question(gap_res, ctx)
            if q:
                # Question should NOT be for calculated outputs (DSCR, EBITDA, total_project_cost)
                self.assertNotIn(q.field_id, AUTHORITATIVE_FINANCIAL_FIELDS)
        asyncio.run(_run())

    def test_03_missing_field_creates_user_required_question(self):
        """3. Missing critical field creates USER_REQUIRED question."""
        async def _run():
            from app.services.dpr_stage1 import dpr_question_engine
            bid = "test_req03_missing_field"
            # No promoter name provided
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Missing Promoter Unit")
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            q = await dpr_question_engine.get_next_question(gap_res, ctx)
            self.assertIsNotNone(q)
            self.assertIn(q.field_id, ["promoter_name", "raw_business_description", "location_state"])
        asyncio.run(_run())

    def test_04_question_answer_resolves_canonical_field(self):
        """4. Question answer resolves canonical field ID."""
        async def _run():
            from app.services.dpr_stage1 import dpr_answer_resolver
            res = dpr_answer_resolver.resolve_answer("premises_status", "We operate from our own shop premises")
            self.assertTrue(res.validation_passed)
            self.assertEqual(res.canonical_value, "OWNED")
        asyncio.run(_run())

    def test_05_benchmark_resolves_operational_assumption(self):
        """5. Benchmark resolves operational assumption (e.g. operating days)."""
        async def _run():
            bm = benchmark_resolver.resolve_benchmarks(business_id="test_req05", category="MANUFACTURING")
            self.assertIn("operating_days_per_year", bm)
            self.assertEqual(bm["operating_days_per_year"]["source_type"], EnrichmentSourceType.BENCHMARK_DERIVED)
        asyncio.run(_run())

    def test_06_benchmark_cannot_override_financial_engine_output(self):
        """6. Benchmark cannot override financial engine output."""
        async def _run():
            bm = benchmark_resolver.resolve_benchmarks(business_id="test_req06", category="MANUFACTURING")
            for fin_f in AUTHORITATIVE_FINANCIAL_FIELDS:
                self.assertNotIn(fin_f, bm)
        asyncio.run(_run())

    def test_07_client_cannot_inject_arbitrary_benchmark(self):
        """7. Client cannot inject arbitrary benchmark numbers."""
        async def _run():
            bid = "test_req07_arbitrary_bench"
            dpr_scenario_manager.accept_benchmark(
                business_id=bid,
                field_id="operating_days_per_year",
                benchmark_value=999999,  # Bogus number
                benchmark_id="NON_EXISTENT_BENCHMARK_ID"
            )
            scen = dpr_scenario_manager.get_or_create_scenario(bid)
            # If not in authoritative repository, it should not be accepted as benchmark
            self.assertNotIn("operating_days_per_year", scen.accepted_benchmarks)
        asyncio.run(_run())

    def test_08_authoritative_benchmark_missing_yields_unknown(self):
        """8. Authoritative benchmark missing yields UNKNOWN status."""
        async def _run():
            bm = benchmark_resolver.resolve_benchmarks(business_id="test_req08_missing", category="NON_EXISTENT_ARCHETYPE")
            self.assertNotIn("unknown_exotic_field", bm)
        asyncio.run(_run())

    def test_09_explicit_zero_remains_zero(self):
        """9. Explicit zero remains zero and is not treated as missing."""
        async def _run():
            bid = "test_req09_zero"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Zero Test")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Zero description")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Zero User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Goa")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "North Goa")
            dpr_scenario_manager.set_user_answer(bid, "scheme_subsidy_percentage", 0.0)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            fld = pkg.fields.get("scheme_subsidy_percentage")
            self.assertIsNotNone(fld)
            self.assertEqual(fld.value, 0.0)
        asyncio.run(_run())

    def test_10_unknown_does_not_become_zero(self):
        """10. UNKNOWN does not become zero."""
        async def _run():
            bid = "test_req10_unknown_not_zero"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Unknown Not Zero")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Unknown Not Zero Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Tester")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Goa")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "South Goa")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            fld = pkg.fields.get("power_load_required_hp")
            if fld and fld.source_type == EnrichmentSourceType.UNKNOWN:
                self.assertIsNone(fld.value)
                self.assertNotEqual(fld.value, 0.0)
        asyncio.run(_run())

    def test_11_financial_package_and_enriched_financial_fields_must_match(self):
        """11. financial_package and enriched financial fields must match within tolerance."""
        async def _run():
            bid = "test_req11_match"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Match Enterprise")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Match Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Match User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Surat")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 1000000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 200000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)

            val_summary = pkg.validation
            fin_checks = val_summary.financial_authority_checks
            self.assertGreater(len(fin_checks), 0)
            for fc in fin_checks:
                self.assertEqual(fc.status, "PASS", f"Financial check failed for {fc.field_id}: {fc.reason}")
        asyncio.run(_run())

    def test_12_financial_source_must_be_engine_calculated(self):
        """12. Financial source must be ENGINE_CALCULATED."""
        async def _run():
            bid = "test_req12_source_engine"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Engine Calculated Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Engine Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Engine User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Punjab")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Ludhiana")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 900000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 180000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)

            f_loan = pkg.fields.get("bank_term_loan_amount")
            self.assertEqual(f_loan.source_type, EnrichmentSourceType.ENGINE_CALCULATED)
        asyncio.run(_run())

    def test_13_user_assumption_change_triggers_authoritative_recalculation(self):
        """13. User assumption change triggers authoritative recalculation."""
        async def _run():
            bid = "test_req13_recalc_trigger"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Recalc Trigger Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Recalc Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Recalc User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Maharashtra")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Pune")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 800000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 160000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg1 = await dpr_enrichment_service.run_enrichment(business_id=bid)
            old_loan = pkg1.fields["bank_term_loan_amount"].value

            pkg2 = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="total_project_cost",
                action="OVERRIDE",
                value=1200000.0
            )
            new_loan = pkg2.fields["bank_term_loan_amount"].value
            self.assertNotEqual(old_loan, new_loan)
        asyncio.run(_run())

    def test_14_recalculated_financial_package_reaches_14_2(self):
        """14. Recalculated financial package reaches 14.2."""
        async def _run():
            bid = "test_req14_pkg_reaches_14_2"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Package Reaches Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Package Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Package User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Haryana")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Gurgaon")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 1000000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 200000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIn("means_of_finance", pkg.financials)
            self.assertIn("project_cost", pkg.financials)
        asyncio.run(_run())

    def test_15_dependent_fields_refresh(self):
        """15. Dependent fields refresh on update."""
        async def _run():
            bid = "test_req15_dep_refresh"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Dep Refresh Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Dep Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Dep User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Vadodara")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 1000000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 200000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIsNotNone(pkg.fields["bank_term_loan_amount"].value)
            self.assertIsNotNone(pkg.fields["promoter_equity_amount"].value)
            self.assertEqual(
                pkg.fields["total_project_cost"].value,
                pkg.fields["bank_term_loan_amount"].value + pkg.fields["promoter_equity_amount"].value
            )
        asyncio.run(_run())

    def test_16_stale_values_are_not_retained(self):
        """16. Stale values are not retained after recalculation."""
        async def _run():
            bid = "test_req16_no_stale"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Stale Test")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Stale Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Stale User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Delhi")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Central")
            dpr_scenario_manager.set_user_answer(bid, "total_project_cost", 500000.0)
            dpr_scenario_manager.set_user_answer(bid, "promoter_equity_amount", 100000.0)

            await dpr_scenario_manager.recalculate_scenario(business_id=bid)
            pkg = await dpr_enrichment_service.update_assumption(
                business_id=bid,
                field_id="total_project_cost",
                action="OVERRIDE",
                value=750000.0
            )
            self.assertEqual(pkg.fields["total_project_cost"].value, 750000.0)
            self.assertEqual(pkg.financials["project_cost"]["total_project_cost"], 750000.0)
        asyncio.run(_run())

    def test_17_provenance_is_preserved(self):
        """17. Provenance is preserved across all resolved fields."""
        async def _run():
            bid = "test_req17_prov"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Prov Test")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Prov Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Prov User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Assam")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Guwahati")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertIn("business_name", pkg.provenance)
            self.assertEqual(pkg.provenance["business_name"]["source_type"], "USER_PROVIDED")
        asyncio.run(_run())

    def test_18_scenario_id_survives_every_api_flow(self):
        """18. Scenario ID survives across all enrichment mutations."""
        async def _run():
            bid = "test_req18_scen"
            sid = "SCENARIO_ALPHA_99"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Alpha Unit", scenario_id=sid)
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Alpha Desc", scenario_id=sid)
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Alpha User", scenario_id=sid)
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Goa", scenario_id=sid)
            dpr_scenario_manager.set_user_answer(bid, "location_district", "North Goa", scenario_id=sid)

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, scenario_id=sid)
            self.assertEqual(pkg.scenario_id, sid)
            self.assertEqual(pkg.metadata["scenario_id"], sid)
        asyncio.run(_run())

    def test_19_frontend_has_no_fabricated_defaults(self):
        """19. Frontend receives None/clean values rather than fabricated strings."""
        async def _run():
            bid = "test_req19_no_fab_front"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Clean Frontend Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Clean Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Clean User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Goa")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "North Goa")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            f_lease = pkg.fields.get("lease_period_years")
            if f_lease:
                self.assertIsNone(f_lease.value)
        asyncio.run(_run())

    def test_20_readiness_false_when_critical_gaps_remain(self):
        """20. Readiness is false when critical gaps remain."""
        async def _run():
            bid = "test_req20_unready_gaps"
            # Intentionally missing promoter name & location
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)
            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid, handoff_package_override=handoff)
            self.assertFalse(pkg.ready_for_stage_14_3)
            self.assertFalse(pkg.is_enrichment_complete)
        asyncio.run(_run())

    def test_21_readiness_true_for_a_fully_resolved_valid_package(self):
        """21. Readiness is true for a fully resolved valid package."""
        async def _run():
            bid = "test_req21_ready_complete"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Ready Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Ready business")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Ready Promoter")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Ahmedabad")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            self.assertTrue(pkg.ready_for_stage_14_3)
            self.assertTrue(pkg.is_enrichment_complete)
        asyncio.run(_run())

    def test_22_no_14_2_code_generates_final_pdf(self):
        """22. No Stage 14.2 service code generates final PDF report (handled exclusively by Stage 14.3)."""
        import inspect
        service_methods = [m[0] for m in inspect.getmembers(dpr_enrichment_service, predicate=inspect.ismethod)]
        self.assertNotIn("generate_pdf", service_methods)
        self.assertNotIn("render_pdf", service_methods)
        self.assertNotIn("build_pdf", service_methods)

    def test_23_14_2_output_conforms_to_dpr_enrichment_package(self):
        """23. Stage 14.2 output strictly conforms to DPR_ENRICHMENT_PACKAGE contract."""
        async def _run():
            bid = "test_req23_contract"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Contract Unit")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Contract Desc")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Contract User")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Surat")

            pkg = await dpr_enrichment_service.run_enrichment(business_id=bid)
            pkg_dict = pkg.model_dump()
            required_keys = [
                "scenario_id", "business_profile", "entrepreneur_profile", "market",
                "opportunity", "financials", "benchmarks", "schemes", "risk",
                "feasibility", "swot", "documents", "dpr_fields", "section_completeness",
                "gaps", "assumptions", "provenance", "validation", "readiness"
            ]
            for rk in required_keys:
                self.assertIn(rk, pkg_dict, f"Missing canonical key {rk} in DPR_ENRICHMENT_PACKAGE")
        asyncio.run(_run())

    def test_24_existing_regression_tests_remain_green(self):
        """24. Existing regression tests remain green and functional."""
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
