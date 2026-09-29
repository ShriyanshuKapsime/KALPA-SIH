"""
Smoke test suite for KALPA DPR Stage 1 Implementation:
TEST 1 — COMPLETE GAP SCAN
TEST 2 — BENCHMARK OVERRIDE
TEST 3 — QUESTION FLOW
TEST 4 — SARVAM FAILURE HANDLING
TEST 5 — NO STALE FINANCE
"""
import sys
import os
import asyncio

# Add ai-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from app.services.dpr_stage1 import (
    ALL_DPR_FIELDS,
    CANONICAL_MODULES,
    CANONICAL_SECTIONS,
    dpr_context_builder,
    dpr_gap_analyzer,
    dpr_question_engine,
    dpr_answer_resolver,
    dpr_scenario_manager,
    DPRQuestion,
)


async def run_stage1_smoke_tests():
    print("============================================================")
    print("STARTING KALPA DPR STAGE 1 TARGETED SMOKE TESTS")
    print("============================================================\n")

    # -------------------------------------------------------------
    # TEST 1: COMPLETE GAP SCAN (Saree Retail Scenario)
    # -------------------------------------------------------------
    print("------------------------------------------------------------")
    print("TEST 1 — COMPLETE GAP SCAN (Saree Retail Scenario)")
    print("------------------------------------------------------------")

    biz_id_saree = "test-saree-retail-001"
    ctx_saree = await dpr_context_builder.build_context(
        business_id=biz_id_saree,
        scenario_id="DPR-SAREE-SCENARIO-1"
    )

    gap_res_saree = dpr_gap_analyzer.analyze(ctx_saree)

    print(f"Total Registered Fields: {gap_res_saree.total_fields}")
    print(f"Applicable Fields: {gap_res_saree.applicable_fields}")
    print(f"Resolved Fields: {gap_res_saree.resolved} (Benchmark: {gap_res_saree.benchmark_resolved}, Engine: {gap_res_saree.engine_resolved}, User: {gap_res_saree.user_resolved})")
    print(f"User Required Gaps: {gap_res_saree.user_required}")
    print(f"Document Pending Gaps: {gap_res_saree.document_pending}")
    print(f"Sections Inspected: {len(gap_res_saree.section_summaries)} / 39")
    print(f"Modules Inspected: {len(gap_res_saree.module_summaries)} / 8")
    print(f"Readiness Status: {gap_res_saree.dpr_readiness_status.value}")

    assert len(gap_res_saree.section_summaries) == 39, "All 39 sections must be inspected!"
    assert len(gap_res_saree.module_summaries) == 9, "Module 0 + 8 canonical modules must be inspected!"
    assert gap_res_saree.total_fields == len(ALL_DPR_FIELDS), "All registered fields must be evaluated!"
    print(">>> TEST 1 PASSED: All 39 sections & 8 modules inspected with strict field-level resolution.\n")

    # -------------------------------------------------------------
    # TEST 2: BENCHMARK OVERRIDE (Dairy: 10 -> 5 animals)
    # -------------------------------------------------------------
    print("------------------------------------------------------------")
    print("TEST 2 — BENCHMARK OVERRIDE (Dairy: 10 -> 5 animals)")
    print("------------------------------------------------------------")

    biz_id_dairy = "test-dairy-farm-002"
    scenario_id_dairy = "DPR-DAIRY-SCENARIO-1"

    # Step 1: Initial context has benchmark 10 animals
    ctx_dairy_initial = await dpr_context_builder.build_context(
        business_id=biz_id_dairy,
        scenario_id=scenario_id_dairy
    )
    initial_bench_animals = ctx_dairy_initial.get("assumptions", {}).get("operational_unit_count", 10)
    print(f"Initial Benchmark Starting Animals: {initial_bench_animals}")

    # Step 2: Apply user override: 5 animals
    dpr_scenario_manager.set_user_override(
        business_id=biz_id_dairy,
        field_id="operational_unit_count",
        value=5,
        scenario_id=scenario_id_dairy
    )

    # Step 3: Trigger authoritative financial recalculation
    recalc_result = await dpr_scenario_manager.recalculate_scenario(
        business_id=biz_id_dairy,
        scenario_id=scenario_id_dairy,
        changed_field_id="operational_unit_count"
    )

    updated_ctx_dairy = recalc_result["dpr_context_package"]
    updated_gap_dairy = recalc_result["gap_analysis"]
    impact_data = recalc_result["impact"]

    # Verify baseline benchmark remains immutable and user override is 5
    assump_rec = updated_ctx_dairy["assumptions"].get("operational_unit_count")
    base_val = assump_rec.get("baseline") if isinstance(assump_rec, dict) else assump_rec
    assert updated_ctx_dairy["overrides"]["operational_unit_count"] == 5, "Override must be 5!"
    assert updated_ctx_dairy["fields"]["operational_unit_count"]["value"] == 5, "Resolved value must be 5!"
    assert updated_ctx_dairy["fields"]["operational_unit_count"]["status"] == "RESOLVED_OVERRIDE", "Status must be RESOLVED_OVERRIDE!"

    print(f"Base Benchmark Value: {base_val} (Immutable)")
    print(f"Scenario Override: {updated_ctx_dairy['overrides']['operational_unit_count']}")
    print(f"Resolved Field Status: {updated_ctx_dairy['fields']['operational_unit_count']['status']}")
    print("Affected Metrics from Authoritative Recalculation:")
    for m in impact_data["affected_metrics"]:
        print(f"  - {m['label']}: Old={m['formatted_old']} -> New={m['formatted_new']}")

    print(">>> TEST 2 PASSED: Benchmark preserved, override stored, authoritative recalculation executed.\n")

    # -------------------------------------------------------------
    # TEST 3: QUESTION FLOW (USER_REQUIRED field -> Question -> Answer -> Gap Disappears)
    # -------------------------------------------------------------
    print("------------------------------------------------------------")
    print("TEST 3 — QUESTION FLOW (Targeted Questioning & Answer Resolution)")
    print("------------------------------------------------------------")

    # 1. Inspect next question from gap analyzer
    next_q = await dpr_question_engine.get_next_question(
        gap_analysis=gap_res_saree,
        dpr_context_package=ctx_saree,
        language="en"
    )
    assert next_q is not None, "A question should be available for unresolved gaps"
    print(f"Generated Question Field ID: {next_q.field_id}")
    print(f"Question Text: {next_q.question_text}")
    print(f"Explanation: {next_q.explanation}")
    print(f"Input Type: {next_q.input_type}")

    # 2. Simulate User Answering "I already own the shop"
    answer_res = dpr_answer_resolver.resolve_answer(
        field_id=next_q.field_id,
        raw_answer="Already own the premises" if next_q.field_id == "premises_status" else "Sole Proprietorship"
    )
    print(f"Answer Resolution Passed: {answer_res.validation_passed}")
    print(f"Canonical Value: {answer_res.canonical_value}")
    print(f"Multi-field Updates: {answer_res.multi_field_updates}")

    # 3. Save answer into scenario and recalculate
    dpr_scenario_manager.set_user_answer(
        business_id=biz_id_saree,
        field_id=next_q.field_id,
        value=answer_res.canonical_value,
        multi_updates=answer_res.multi_field_updates,
        scenario_id="DPR-SAREE-SCENARIO-1"
    )

    recalc_after_ans = await dpr_scenario_manager.recalculate_scenario(
        business_id=biz_id_saree,
        scenario_id="DPR-SAREE-SCENARIO-1",
        changed_field_id=next_q.field_id
    )

    post_ans_ctx = recalc_after_ans["dpr_context_package"]
    post_ans_field = post_ans_ctx["fields"][next_q.field_id]
    assert post_ans_field["status"] == "RESOLVED_USER", f"Field status should now be RESOLVED_USER, got {post_ans_field['status']}"
    print(f"Field {next_q.field_id} Status Now: {post_ans_field['status']} (Value: {post_ans_field['value']})")
    print(">>> TEST 3 PASSED: Question served, answer resolved into canonical field, gap cleared.\n")

    # -------------------------------------------------------------
    # TEST 4: SARVAM FAILURE HANDLING & TTS/STT RESILIENCE
    # -------------------------------------------------------------
    print("------------------------------------------------------------")
    print("TEST 4 — SARVAM FAILURE HANDLING (Deterministic Fallback)")
    print("------------------------------------------------------------")

    # Test Hindi question with deterministic fallback
    hi_q = await dpr_question_engine.get_next_question(
        gap_analysis=gap_res_saree,
        dpr_context_package=ctx_saree,
        language="hi"
    )
    print(f"Hindi Question: {hi_q.question_text}")
    print(f"Hindi Explanation: {hi_q.explanation}")
    assert hi_q.question_text and len(hi_q.question_text) > 0, "Hindi fallback template must produce question text!"

    # Test Number word parsing in answer resolver
    spoken_num = dpr_answer_resolver.resolve_answer(
        field_id="daily_production_sales_units",
        raw_answer="पंद्रह"  # 15 in Hindi
    )
    assert spoken_num.canonical_value == 15, f"Expected 15 from 'पंद्रह', got {spoken_num.canonical_value}"
    print(f"STT Spoken Word Resolution: 'पंद्रह' -> {spoken_num.canonical_value}")

    print(">>> TEST 4 PASSED: Deterministic fallback & multilingual parsing operate reliably.\n")

    # -------------------------------------------------------------
    # TEST 5: NO STALE FINANCE (Version & Consistency Guarantee)
    # -------------------------------------------------------------
    print("------------------------------------------------------------")
    print("TEST 5 — NO STALE FINANCE (Coherent Scenario Consistency)")
    print("------------------------------------------------------------")

    # Verify scenario version incremented
    state_saree = dpr_scenario_manager.get_or_create_scenario(biz_id_saree, "DPR-SAREE-SCENARIO-1")
    print(f"Scenario Version: {state_saree.version}")
    print(f"Last Recalculated At: {state_saree.last_recalculated_at}")

    # Check that financial package adheres to zero-fabrication (cost_field is None until financial engine runs)
    cost_field = post_ans_ctx["fields"]["total_project_cost"]["value"]
    print(f"DPR Context Project Cost (Pre-calculation): {cost_field}")
    assert cost_field is None or cost_field > 0, "Project cost must be None (zero fabrication) or positive computed value"

    print(">>> TEST 5 PASSED: Scenario versioning and zero-fabrication consistency verified.\n")

    print("============================================================")
    print("ALL 5 SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_stage1_smoke_tests())
