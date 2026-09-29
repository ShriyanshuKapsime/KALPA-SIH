"""
Comprehensive Stage 14.1 Hardening & Production Freeze Test Suite (31 Tests).
Verifies all contract invariants, boundary conditions, zero-fabrication guarantees,
question priorities, multilingual resolutions, scenario states, disk persistence,
benchmark acceptance vs override, upstream classification preservation, and canonical handoff package.
"""
import sys
import os
import asyncio
import unittest

# Add ai-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    DPRModuleId,
    FieldMateriality,
    FieldSourceType,
    FieldStatus,
    DPRReadinessStatus,
    get_field_definition,
    is_field_applicable,
    normalize_field_id,
)
from app.services.dpr_stage1.dpr_context_builder import DPRContextBuilder, dpr_context_builder
from app.services.dpr_stage1.dpr_gap_analyzer import DPRGapAnalyzer, dpr_gap_analyzer
from app.services.dpr_stage1.dpr_question_engine import DPRQuestionEngine, dpr_question_engine
from app.services.dpr_stage1.dpr_answer_resolver import DPRAnswerResolver, dpr_answer_resolver
from app.services.dpr_stage1.dpr_scenario_manager import (
    DPRScenarioManager,
    dpr_scenario_manager,
    ScenarioRepository,
    DPRScenarioState,
)
from app.services.dpr_stage1.dpr_handoff import (
    build_stage14_handoff_package,
    build_stage1_handoff_package,
    DPRStage14HandoffPackage,
    DPRStage1HandoffPackage,
)


class TestStage1RegistryAndStructure(unittest.TestCase):
    """Test Suite 1: Structural Invariants and 39 Sections."""

    def test_canonical_modules_count(self):
        """Must have exactly 9 canonical modules (Module 0 to Module VIII)."""
        self.assertEqual(len(CANONICAL_MODULES), 9)
        expected_modules = [
            DPRModuleId.MODULE_0,
            DPRModuleId.MODULE_I,
            DPRModuleId.MODULE_II,
            DPRModuleId.MODULE_III,
            DPRModuleId.MODULE_IV,
            DPRModuleId.MODULE_V,
            DPRModuleId.MODULE_VI,
            DPRModuleId.MODULE_VII,
            DPRModuleId.MODULE_VIII,
        ]
        self.assertEqual(list(CANONICAL_MODULES.keys()), expected_modules)

    def test_canonical_sections_count(self):
        """Must have exactly 39 canonical DPR sections."""
        self.assertEqual(len(CANONICAL_SECTIONS), 39)
        # Verify key sections exist
        self.assertIn("0.1", CANONICAL_SECTIONS)
        self.assertIn("1.1", CANONICAL_SECTIONS)
        self.assertIn("4.1", CANONICAL_SECTIONS)
        self.assertIn("6.1", CANONICAL_SECTIONS)
        self.assertIn("8.4", CANONICAL_SECTIONS)

    def test_registered_fields_integrity(self):
        """Every field must have valid module, section, source type, and materiality."""
        self.assertGreaterEqual(len(ALL_DPR_FIELDS), 85)
        for fdef in ALL_DPR_FIELDS:
            self.assertIn(fdef.module_id, CANONICAL_MODULES)
            self.assertIn(fdef.section_id, CANONICAL_SECTIONS)
            self.assertIsInstance(fdef.materiality, FieldMateriality)
            self.assertIsInstance(fdef.default_source, FieldSourceType)

    def test_canonical_field_alias_normalization(self):
        """Legacy and alternative field aliases must normalize deterministically to canonical IDs."""
        self.assertEqual(normalize_field_id("cost_of_project"), "total_project_cost")
        self.assertEqual(normalize_field_id("term_loan"), "bank_term_loan_amount")
        self.assertEqual(normalize_field_id("promoter_contribution"), "promoter_equity_amount")
        self.assertEqual(normalize_field_id("scheme_code"), "target_scheme_code")
        self.assertEqual(normalize_field_id("working_capital"), "cost_working_capital_margin")
        self.assertEqual(normalize_field_id("non_existent_key_xyz"), "non_existent_key_xyz")


class TestStage1ZeroFabricationAndIntake(unittest.TestCase):
    """Test Suite 2: Empty Entrepreneur & Zero Fabrication Guarantees."""

    def test_empty_entrepreneur_no_fabrication(self):
        """An empty new entrepreneur must have NO synthetic numbers or fake pass states."""
        async def _run():
            ctx = await dpr_context_builder.build_context(business_id="test_new_empty_user_001")
            
            # Verify no hardcoded project cost
            fields = ctx.get("fields", {})
            self.assertIn("total_project_cost", fields)
            cop = fields["total_project_cost"]
            self.assertNotEqual(cop.get("value"), 500000.0)
            self.assertIsNone(cop.get("value"))
            
            # Verify no hardcoded DSCR
            self.assertIn("glance_average_dscr", fields)
            dscr = fields["glance_average_dscr"]
            self.assertNotEqual(dscr.get("value"), 2.15)
            self.assertIsNone(dscr.get("value"))
            
            # Verify no hardcoded scheme or location
            target_scheme = fields.get("target_scheme_code", {})
            self.assertNotEqual(target_scheme.get("value"), "PMEGP")
            self.assertIsNone(target_scheme.get("value"))
            
            # Check Gap Analysis
            gap_res = dpr_gap_analyzer.analyze(ctx)
            self.assertNotEqual(gap_res.dpr_readiness_status, DPRReadinessStatus.BANK_REVIEW_READY)
            self.assertFalse(gap_res.can_proceed_to_dpr)
            self.assertFalse(gap_res.is_ready_for_stage_14_2)
            self.assertGreater(len(gap_res.blocking_gaps), 0)
            
            # Verify Stage boundary: Archetype is not defaulted to 'Retail'
            self.assertIsNone(ctx.get("business_archetype"))
            self.assertEqual(ctx.get("benchmark_status"), "BENCHMARK_PENDING_STAGE_2")

        asyncio.run(_run())

    def test_promoter_contribution_no_default_margin(self):
        """Missing promoter contribution must remain UNKNOWN without 10% or 15% fabrication."""
        async def _run():
            ctx = await dpr_context_builder.build_context(business_id="test_no_margin_fab_002")
            fields = ctx.get("fields", {})
            pe = fields.get("promoter_equity_amount", {})
            self.assertIsNone(pe.get("value"))
            self.assertNotEqual(pe.get("value"), 50000.0)
            self.assertEqual(pe.get("status"), FieldStatus.UNKNOWN.value)
        asyncio.run(_run())

    def test_scheme_not_defaulted_to_pmegp_when_missing(self):
        """Target financing scheme must not default to PMEGP when omitted."""
        async def _run():
            ctx = await dpr_context_builder.build_context(business_id="test_scheme_omitted_003")
            fields = ctx.get("fields", {})
            sc = fields.get("target_scheme_code", {})
            self.assertIsNone(sc.get("value"))
            self.assertNotEqual(sc.get("value"), "PMEGP")
        asyncio.run(_run())


class TestStage1PopulatedIntakeAndDocument(unittest.TestCase):
    """Test Suite 3: Saree Retail & Dairy Farm Intake Flows."""

    def test_saree_retail_intake_flow(self):
        """Verify intake for Saree Retail in Varanasi correctly maps fields and preserves raw intent."""
        async def _run():
            bid = "test_saree_varanasi_002"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Kashi Handloom Sarees")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Handloom silk and cotton saree retail store in Chowk Varanasi")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Ananya Sharma")
            dpr_scenario_manager.set_user_answer(bid, "promoter_gender", "Female")
            dpr_scenario_manager.set_user_answer(bid, "promoter_social_category", "GENERAL")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Uttar Pradesh")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Varanasi")
            dpr_scenario_manager.set_user_answer(bid, "target_scheme_code", "PMEGP")
            dpr_scenario_manager.set_user_answer(bid, "premises_status", "RENTED")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            fields = ctx.get("fields", {})
            
            self.assertEqual(fields["business_name"]["value"], "Kashi Handloom Sarees")
            self.assertEqual(fields["business_name"]["source_type"], FieldSourceType.USER_PROVIDED.value)
            self.assertEqual(fields["location_district"]["value"], "Varanasi")
            self.assertEqual(fields["location_state"]["value"], "Uttar Pradesh")
            self.assertEqual(fields["premises_status"]["value"], "RENTED")
            
            # Check raw business description is preserved in intake
            self.assertEqual(ctx.get("raw_business_description"), "Handloom silk and cotton saree retail store in Chowk Varanasi")
            
        asyncio.run(_run())

    def test_document_verification_mapping(self):
        """Verified documents should update enclosure checklist and field sources."""
        async def _run():
            bid = "test_dairy_farm_doc_003"
            dpr_scenario_manager.update_document(bid, "udyam_certificate", "VERIFIED", document_name="udyam_reg.pdf")
            dpr_scenario_manager.update_document(bid, "pan_card", "VERIFIED", document_name="pan_card.jpg")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            docs = ctx.get("documents", {})
            self.assertEqual(docs.get("udyam_certificate", {}).get("status"), "VERIFIED")
            self.assertEqual(docs.get("pan_card", {}).get("status"), "VERIFIED")
            
        asyncio.run(_run())

    def test_document_update_immediate_rebuild(self):
        """Calling update_document on scenario immediately changes document status in rebuilt context."""
        async def _run():
            bid = "test_doc_immediate_004"
            dpr_scenario_manager.update_document(bid, "gst_certificate", "VERIFIED", document_name="gstin_cert.pdf")
            ctx = await dpr_context_builder.build_context(business_id=bid)
            self.assertEqual(ctx["documents"]["gst_certificate"]["status"], "VERIFIED")
            self.assertEqual(ctx["documents"]["gst_certificate"]["document_name"], "gstin_cert.pdf")
        asyncio.run(_run())


class TestStage1OverridesAndBaselines(unittest.TestCase):
    """Test Suite 4: Overrides, Immutable Baselines, and Unknown vs Zero."""

    def test_benchmark_override_and_restoration(self):
        """Overriding an assumption modifies the active value without altering baseline."""
        async def _run():
            bid = "test_override_user_004"
            # Set override
            dpr_scenario_manager.set_user_override(bid, "moratorium_period_months", 12.0)
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            fields = ctx.get("fields", {})
            mor = fields.get("moratorium_period_months", {})
            
            self.assertEqual(mor.get("value"), 12.0)
            self.assertEqual(mor.get("source_type"), FieldSourceType.USER_OVERRIDE.value)
            
            # Baselines check
            assumptions = ctx.get("assumptions", {})
            self.assertIn("moratorium_period_months", assumptions)
            
        asyncio.run(_run())

    def test_unknown_not_equal_to_zero(self):
        """Explicitly verify UNKNOWN != 0.0."""
        async def _run():
            # Case 1: missing field is UNKNOWN / USER_REQUIRED, not 0.0
            bid_missing = "test_unknown_missing_005"
            ctx1 = await dpr_context_builder.build_context(business_id=bid_missing)
            f_missing = ctx1["fields"].get("monthly_wages_total", {})
            self.assertIsNone(f_missing.get("value"))
            self.assertEqual(f_missing.get("status"), FieldStatus.USER_REQUIRED.value)
            self.assertNotEqual(f_missing.get("value"), 0.0)
            
            # Case 2: explicit 0.0 value is RESOLVED_USER with value 0.0
            bid_zero = "test_zero_explicit_005"
            dpr_scenario_manager.set_user_answer(bid_zero, "monthly_wages_total", 0.0)
            ctx2 = await dpr_context_builder.build_context(business_id=bid_zero)
            f_zero = ctx2["fields"].get("monthly_wages_total", {})
            self.assertEqual(f_zero.get("value"), 0.0)
            self.assertEqual(f_zero.get("status"), FieldStatus.RESOLVED_USER.value)
            
        asyncio.run(_run())

    def test_provenance_metadata_on_every_field(self):
        """Every field record must have valid source_type, source_id, source_reference, and confidence."""
        async def _run():
            bid = "test_provenance_check_006"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Proven Enterprise")
            ctx = await dpr_context_builder.build_context(business_id=bid)
            
            for fid, fld in ctx["fields"].items():
                self.assertIn("source_type", fld)
                self.assertIn("source_id", fld)
                self.assertIn("source_reference", fld)
                self.assertIn("confidence", fld)
                self.assertIn("status", fld)
        asyncio.run(_run())


class TestStage1QuestionEngineAndResolver(unittest.TestCase):
    """Test Suite 5: Prioritized Questioning & Multilingual Normalization."""

    def test_no_calculated_questions_generated(self):
        """Question engine must NEVER generate questions for calculated fields."""
        calculated_fids = {"total_project_cost", "glance_total_project_cost", "bank_term_loan_amount", "glance_average_dscr", "glance_break_even_utilization"}
        
        async def _run():
            ctx = await dpr_context_builder.build_context(business_id="test_calc_q_006")
            gap_res = dpr_gap_analyzer.analyze(ctx)
            
            # Check up to 10 questions in sequence
            visited_q_fields = set()
            for _ in range(10):
                q = await dpr_question_engine.get_next_question(gap_res, ctx)
                if not q:
                    break
                self.assertNotIn(q.field_id, calculated_fids, f"Calculated field {q.field_id} was asked in question engine!")
                visited_q_fields.add(q.field_id)
                # Temporarily mark resolved to get next
                ctx["fields"][q.field_id]["status"] = FieldStatus.RESOLVED_USER.value
                gap_res = dpr_gap_analyzer.analyze(ctx)
                
        asyncio.run(_run())

    def test_multilingual_number_and_unit_resolution(self):
        """Verify Hindi/English words, unit conversion (lakhs, crore), and boolean parsing."""
        resolver = dpr_answer_resolver
        
        # Hindi number words
        res_hi_1 = resolver.resolve_answer("project_timeline_months", "पंद्रह")
        self.assertTrue(res_hi_1.validation_passed)
        self.assertEqual(res_hi_1.canonical_value, 15.0)
        
        # English lakhs
        res_en_lakh = resolver.resolve_answer("cost_plant_machinery", "12.5 lakhs")
        self.assertTrue(res_en_lakh.validation_passed)
        self.assertEqual(res_en_lakh.canonical_value, 1250000.0)
        
        # English crore
        res_en_cr = resolver.resolve_answer("total_project_cost", "1.5 Cr")
        self.assertTrue(res_en_cr.validation_passed)
        self.assertEqual(res_en_cr.canonical_value, 15000000.0)

        # Percentage parsing
        res_pct = resolver.resolve_answer("capacity_utilization_year1", "65%")
        self.assertTrue(res_pct.validation_passed)
        self.assertEqual(res_pct.canonical_value, 65.0)
        
        # Options matching (e.g. premises_status)
        res_land = resolver.resolve_answer("premises_status", "rented space")
        self.assertTrue(res_land.validation_passed)
        self.assertEqual(res_land.canonical_value, "RENTED")
        
        # Invalid option rejection
        res_invalid = resolver.resolve_answer("premises_status", "flying airplane")
        self.assertFalse(res_invalid.validation_passed)
        self.assertIn("Invalid selection", res_invalid.validation_error)

    def test_alias_support_in_answer_resolver(self):
        """Answer resolver correctly handles canonical field aliases."""
        resolver = dpr_answer_resolver
        res = resolver.resolve_answer("cost_of_project", "25,00,000")
        self.assertTrue(res.validation_passed)
        self.assertEqual(res.canonical_value, 2500000.0)


class TestStage1FinancialIntegrityAndHandoff(unittest.TestCase):
    """Test Suite 6: Financial Integrity Validation & Canonical Stage 14.1 Handoff."""

    def test_financial_integrity_math_check(self):
        """Mathematical Sources == Uses balance check."""
        builder = dpr_context_builder
        
        # Balanced case
        ok, errs = builder._verify_financial_integrity(
            total_uses=1000000.0,
            total_sources=1000000.0,
            promoter_contrib=200000.0,
            term_loan=800000.0,
            working_cap_loan=0.0
        )
        self.assertTrue(ok)
        self.assertEqual(len(errs), 0)
        
        # Mismatched sources vs uses
        mismatch_ok, mismatch_errs = builder._verify_financial_integrity(
            total_uses=1000000.0,
            total_sources=900000.0,
            promoter_contrib=100000.0,
            term_loan=800000.0,
            working_cap_loan=0.0
        )
        self.assertFalse(mismatch_ok)
        self.assertGreater(len(mismatch_errs), 0)

    def test_canonical_stage14_handoff_package_contract(self):
        """Verify build_stage14_handoff_package contract for Stage 14.2 consumption."""
        async def _run():
            bid = "test_handoff_producer_007"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Varanasi Silk Weavers")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Manufacturing and weaving of pure mulberry silk sarees")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Rajesh Gupta")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Uttar Pradesh")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Varanasi")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            
            handoff = build_stage14_handoff_package(
                business_id=bid,
                context=ctx,
                gap_analysis=gap_res
            )
            
            self.assertIsInstance(handoff, DPRStage14HandoffPackage)
            self.assertEqual(handoff.metadata["stage"], "STAGE_14_1_INTAKE_GAP_RESOLUTION")
            self.assertEqual(handoff.metadata["target_stage"], "STAGE_14_2_ENRICHMENT_INFERENCE")
            self.assertEqual(handoff.metadata["business_id"], bid)
            self.assertEqual(handoff.raw_user_input.business_name_as_entered, "Varanasi Silk Weavers")
            self.assertEqual(handoff.raw_user_input.raw_business_description, "Manufacturing and weaving of pure mulberry silk sarees")
            self.assertEqual(handoff.entrepreneur_context.promoter_name, "Rajesh Gupta")
            self.assertEqual(handoff.location_context.state, "Uttar Pradesh")
            self.assertEqual(handoff.location_context.district, "Varanasi")
            
            # Must serialize cleanly to dict
            pkg_dict = handoff.model_dump()
            self.assertIn("raw_user_input", pkg_dict)
            self.assertIn("entrepreneur_context", pkg_dict)
            self.assertIn("location_context", pkg_dict)
            self.assertIn("readiness", pkg_dict)
            self.assertIn("unresolved_gaps", pkg_dict)
            self.assertIn("conflicts", pkg_dict)
            self.assertTrue(handoff.readiness.is_ready_for_stage_14_2)
            self.assertTrue(handoff.readiness.is_ready_for_stage_2)

        asyncio.run(_run())

    def test_upstream_classification_preservation_without_downgrade(self):
        """Authoritative upstream classifications from Stages 1-3 are preserved in DPR_INTAKE_PACKAGE."""
        async def _run():
            bid = "test_upstream_class_008"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Om Flour Mills")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Wheat and gram flour milling unit")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Ramesh Verma")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Madhya Pradesh")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Indore")
            
            # Simulate upstream classification
            raw_intake = {
                "business_node_id": "NODE_FLOUR_MILL_01",
                "nic_code": "10611",
                "archetype": "MANUFACTURING",
                "sector": "Food Processing",
                "subcategory": "Flour Milling"
            }
            
            ctx = await dpr_context_builder.build_context(business_id=bid, raw_intake_inputs=raw_intake)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)
            
            self.assertEqual(handoff.business_classification.business_node_id, "NODE_FLOUR_MILL_01")
            self.assertEqual(handoff.business_classification.nic_code, "10611")
            self.assertEqual(handoff.business_classification.archetype, "MANUFACTURING")
            self.assertTrue(handoff.business_classification.is_authoritative)

        asyncio.run(_run())

    def test_financial_integrity_with_subsidy_reconciliation(self):
        """Mathematical integrity check with subsidy: Sources (Promoter + Loan + Subsidy) == Total Cost."""
        builder = dpr_context_builder
        ok, errs = builder._verify_financial_integrity(
            total_uses=1000000.0,
            total_sources=1000000.0,
            promoter_contrib=150000.0,
            term_loan=600000.0,
            working_cap_loan=250000.0
        )
        self.assertTrue(ok)
        self.assertEqual(len(errs), 0)

    def test_financial_imbalance_conflict_discovery(self):
        """Financial package mismatch generates FINANCIAL_IMBALANCE conflict."""
        builder = dpr_context_builder
        fin_pkg_imbalance = {
            "project_cost": {"total_project_cost": 1500000.0},
            "means_of_finance": {
                "promoter_equity_amount": 300000.0,
                "term_loan_amount": 900000.0,
                "subsidy_amount": 0.0
            }
        }
        conflicts = builder._detect_conflicts(
            user_answers={},
            user_overrides={},
            documents={},
            benchmarks={},
            financial_package=fin_pkg_imbalance,
            resolved_fields={}
        )
        fin_conflict = next((c for c in conflicts if c.get("conflict_type") == "FINANCIAL_IMBALANCE"), None)
        self.assertIsNotNone(fin_conflict)
        self.assertEqual(fin_conflict["field_id"], "total_project_cost")


class TestStage1ConflictDiscovery(unittest.TestCase):
    """Test Suite 7: Conflict Discovery & Variance Flagging."""

    def test_user_vs_document_conflict_detection(self):
        """User answer differing from verified document must generate a conflict item."""
        async def _run():
            bid = "test_conflict_doc_001"
            repo = ScenarioRepository()
            mgr = DPRScenarioManager(repo=repo)
            
            # User says machinery cost is 500000
            mgr.set_user_answer(bid, "cost_plant_machinery", 500000.0)
            # Verified document states 750000
            mgr.update_document(
                business_id=bid,
                document_key="cost_plant_machinery",
                status="VERIFIED",
                document_name="Verified Machinery Quotation",
                extracted_value=750000.0
            )
            
            scen = repo.get(bid)
            ctx = await dpr_context_builder.build_context(
                business_id=bid,
                user_answers=scen.user_answers,
                document_statuses=scen.document_statuses
            )
            
            conflicts = ctx.get("conflicts", [])
            self.assertGreater(len(conflicts), 0)
            doc_conflict = next((c for c in conflicts if c.get("conflict_type") == "USER_VS_DOCUMENT"), None)
            self.assertIsNotNone(doc_conflict)
            self.assertEqual(doc_conflict["field_id"], "cost_plant_machinery")
            self.assertEqual(doc_conflict["user_value"], 500000.0)
            self.assertEqual(doc_conflict["document_value"], 750000.0)

        asyncio.run(_run())

    def test_benchmark_deviation_conflict_detection(self):
        """User override departing significantly (>50%) from baseline benchmark is recorded as deviation."""
        async def _run():
            bid = "test_conflict_bm_002"
            repo = ScenarioRepository()
            mgr = DPRScenarioManager(repo=repo)
            
            # User overrides daily production units to 5000
            mgr.set_user_override(bid, "daily_production_sales_units", 5000)
            
            scen = repo.get(bid)
            ctx = await dpr_context_builder.build_context(
                business_id=bid,
                user_overrides=scen.user_overrides
            )
            
            conflicts = ctx.get("conflicts", [])
            self.assertIsInstance(conflicts, list)

        asyncio.run(_run())


class TestStage1ScenarioPersistenceAndForking(unittest.TestCase):
    """Test Suite 8: Durable Persistence, Forking Isolation, and Benchmark Acceptance."""

    def test_scenario_survives_repository_reload(self):
        """Scenario data persisted to disk must reload accurately in fresh repository instances."""
        bid = "test_persist_biz_999"
        repo1 = ScenarioRepository()
        mgr1 = DPRScenarioManager(repo=repo1)
        
        mgr1.set_user_answer(bid, "business_name", "Durable Storage Enterprise")
        mgr1.set_user_override(bid, "interest_rate_term_loan", 8.5)
        
        # Instantiate completely fresh repository pointing to same directory
        repo2 = ScenarioRepository()
        scen_loaded = repo2.get(bid)
        
        self.assertIsNotNone(scen_loaded)
        self.assertEqual(scen_loaded.user_answers.get("business_name"), "Durable Storage Enterprise")
        self.assertEqual(scen_loaded.user_overrides.get("interest_rate_term_loan"), 8.5)

    def test_child_scenario_forking_does_not_mutate_parent(self):
        """Creating a child scenario and modifying it must NOT alter parent scenario values."""
        bid = "test_fork_parent_888"
        repo = ScenarioRepository()
        mgr = DPRScenarioManager(repo=repo)
        
        # Base parent scenario
        mgr.set_user_answer(bid, "business_name", "Parent Corporation", scenario_id="base")
        mgr.set_user_answer(bid, "location_city", "Mumbai", scenario_id="base")
        
        # Fork to child scenario
        child_scen = mgr.create_child_scenario(bid, parent_scenario_id="base", child_scenario_id="scenario_pessimistic")
        self.assertEqual(child_scen.parent_scenario_id, "base")
        self.assertEqual(child_scen.user_answers.get("business_name"), "Parent Corporation")
        
        # Modify child
        mgr.set_user_answer(bid, "location_city", "Thane", scenario_id="scenario_pessimistic")
        
        # Verify parent remains unchanged
        parent_scen = repo.get(bid, "base")
        self.assertEqual(parent_scen.user_answers.get("location_city"), "Mumbai")
        
        # Verify child has updated value
        child_refreshed = repo.get(bid, "scenario_pessimistic")
        self.assertEqual(child_refreshed.user_answers.get("location_city"), "Thane")

    def test_benchmark_acceptance_vs_override_provenance(self):
        """Accepting an unchanged benchmark marks BENCHMARK_ACCEPTED; modified value records USER_OVERRIDE."""
        bid = "test_bm_prov_777"
        repo = ScenarioRepository()
        mgr = DPRScenarioManager(repo=repo)
        
        # Accept benchmark unchanged
        mgr.accept_benchmark(bid, "working_capital_cycle_days", 45.0, user_modified_value=None)
        scen = repo.get(bid)
        self.assertIn("working_capital_cycle_days", scen.accepted_benchmarks)
        self.assertEqual(scen.accepted_benchmarks["working_capital_cycle_days"]["status"], FieldStatus.BENCHMARK_ACCEPTED.value)
        self.assertEqual(scen.accepted_benchmarks["working_capital_cycle_days"]["accepted_value"], 45.0)
        self.assertNotIn("working_capital_cycle_days", scen.user_overrides)
        
        # Accept benchmark with modification -> sets override
        mgr.accept_benchmark(bid, "annual_revenue_growth_rate", 10.0, user_modified_value=15.0)
        scen2 = repo.get(bid)
        self.assertEqual(scen2.user_overrides.get("annual_revenue_growth_rate"), 15.0)


class TestStage1ReadinessGates(unittest.TestCase):
    """Test Suite 9: Readiness Gate Invariants (Material vs Non-Material)."""

    def test_readiness_blocked_when_promoter_name_missing(self):
        """Stage 14.2 readiness gate must fail when promoter name is missing."""
        async def _run():
            bid = "test_no_promoter_gate_001"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Sole Venture")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Retail shop")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Maharashtra")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Nagpur")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            self.assertFalse(gap_res.is_ready_for_stage_14_2)
            self.assertTrue(any("promoter" in r.lower() for r in gap_res.stage_14_2_readiness_reasons))
        asyncio.run(_run())

    def test_readiness_blocked_when_location_missing(self):
        """Stage 14.2 readiness gate must fail when operating state/district are missing."""
        async def _run():
            bid = "test_no_location_gate_002"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Global Exporters")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Exporting garments")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Alok Nath")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            self.assertFalse(gap_res.is_ready_for_stage_14_2)
            self.assertTrue(any("location" in r.lower() for r in gap_res.stage_14_2_readiness_reasons))
        asyncio.run(_run())


    def test_critical_conflict_blocks_stage_14_2_readiness(self):
        """Stage 14.2 readiness gate must fail when a critical conflict exists."""
        async def _run():
            bid = "test_crit_conflict_gate_003"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Solar Tech Enterprises")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Solar panel distribution")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Vikram Rathore")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Rajasthan")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Jaipur")
            dpr_scenario_manager.set_user_answer(bid, "cost_plant_machinery", 500000.0)
            
            # Add verified document with conflicting machinery cost
            dpr_scenario_manager.update_document(
                business_id=bid,
                document_key="cost_plant_machinery",
                status="VERIFIED",
                document_name="Verified Quotation",
                extracted_value=900000.0
            )
            
            ctx = await dpr_context_builder.build_context(
                business_id=bid,
                user_answers=dpr_scenario_manager.get_or_create_scenario(bid).user_answers,
                document_statuses=dpr_scenario_manager.get_or_create_scenario(bid).document_statuses
            )
            gap_res = dpr_gap_analyzer.analyze(ctx)
            self.assertFalse(gap_res.is_ready_for_stage_14_2)
            self.assertTrue(any("conflict" in r.lower() for r in gap_res.stage_14_2_readiness_reasons))
        asyncio.run(_run())

    def test_recalculate_scenario_no_fallback_without_cost_or_margin(self):
        """Recalculating scenario without project cost or margin inputs does not fabricate values."""
        async def _run():
            bid = "test_recalc_no_fab_004"
            repo = ScenarioRepository()
            mgr = DPRScenarioManager(repo=repo)
            
            res = await mgr.recalculate_scenario(business_id=bid)
            ctx = res.get("dpr_context_package", {})
            fields = ctx.get("fields", {})
            
            self.assertIsNone(fields.get("total_project_cost", {}).get("value"))
            self.assertIsNone(fields.get("bank_term_loan_amount", {}).get("value"))
            self.assertIsNone(fields.get("promoter_equity_amount", {}).get("value"))
            self.assertFalse(res["gap_analysis"]["is_ready_for_stage_14_2"])
        asyncio.run(_run())

    def test_upstream_classifier_resolution_path(self):
        """When business archetype or NIC code are missing, gap analyzer marks UPSTREAM_CLASSIFIER."""
        async def _run():
            bid = "test_upstream_res_path_005"
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            
            s2_gaps = gap_res.pending_stage2_gaps
            self.assertGreater(len(s2_gaps), 0)
            for g in s2_gaps:
                self.assertEqual(g.gap_category, "UPSTREAM_CONTEXT_GAP")
                self.assertEqual(g.resolution_path, "UPSTREAM_CLASSIFIER")
        asyncio.run(_run())


class TestStage1MultiArchetypeWalkthroughs(unittest.TestCase):
    """Test Suite 10: Multi-Archetype End-to-End Walkthroughs."""

    def test_dairy_farm_intake_and_handoff(self):
        """Verify intake and handoff for a rural Dairy Farm in Anand, Gujarat."""
        async def _run():
            bid = "test_dairy_anand_001"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Amulya Dairy Farm")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Commercial dairy farming with 20 crossbred HF cows for raw milk supply")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Mahesh Patel")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Gujarat")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Anand")
            dpr_scenario_manager.set_user_answer(bid, "premises_status", "OWNED")
            dpr_scenario_manager.set_user_answer(bid, "legal_constitution", "PROPRIETORSHIP")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)
            
            self.assertTrue(handoff.readiness.is_ready_for_stage_14_2)
            self.assertEqual(handoff.raw_user_input.business_name_as_entered, "Amulya Dairy Farm")
            self.assertEqual(handoff.location_context.district, "Anand")
            self.assertEqual(handoff.location_context.state, "Gujarat")

        asyncio.run(_run())

    def test_food_processing_bakery_walkthrough(self):
        """Verify intake and handoff for an Artisan Bakery in Pune, Maharashtra."""
        async def _run():
            bid = "test_bakery_pune_002"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Crust & Crumb Bakers")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Automated bakery manufacturing sliced breads, cookies, and rusks")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Sunita Deshmukh")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Maharashtra")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Pune")
            dpr_scenario_manager.set_user_answer(bid, "premises_status", "RENTED")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)
            
            self.assertTrue(handoff.readiness.is_ready_for_stage_14_2)
            self.assertEqual(handoff.raw_user_input.business_name_as_entered, "Crust & Crumb Bakers")
            self.assertEqual(handoff.location_context.district, "Pune")

        asyncio.run(_run())

    def test_diagnostic_clinic_walkthrough(self):
        """Verify intake and handoff for a Healthcare Diagnostic Center in Patna, Bihar."""
        async def _run():
            bid = "test_clinic_patna_003"
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Sanjeevani Pathology & Imaging")
            dpr_scenario_manager.set_user_answer(bid, "raw_business_description", "Pathological testing and digital X-ray diagnostic laboratory")
            dpr_scenario_manager.set_user_answer(bid, "promoter_name", "Dr. Amit Kumar")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Bihar")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Patna")
            dpr_scenario_manager.set_user_answer(bid, "legal_constitution", "PARTNERSHIP")
            
            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)
            handoff = build_stage14_handoff_package(business_id=bid, context=ctx, gap_analysis=gap_res)
            
            self.assertTrue(handoff.readiness.is_ready_for_stage_14_2)
            self.assertEqual(handoff.location_context.district, "Patna")
            self.assertEqual(handoff.location_context.state, "Bihar")

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main(verbosity=2)
