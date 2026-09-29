import sys
import asyncio
import json

sys.path.insert(0, r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service")

from scratch.test_grocery_mock import grocery_sources
from app.services.dpr_stage1 import dpr_scenario_manager, build_stage14_handoff_package
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_gap_analyzer import dpr_gap_analyzer
from app.services.dpr_stage2 import dpr_enrichment_service

async def run_pipeline():
    biz_id = "test_grocery_store_pipeline"
    scen_id = "DPR-GROCERY-01"

    # Step 1: Build Stage 14.1 Context Package
    ctx = await dpr_context_builder.build_context(
        business_id=biz_id,
        scenario_id=scen_id,
        upstream_package=grocery_sources,
        user_answers=grocery_sources.get("user_answers")
    )
    print(f"Step 1: Built Context Package with {len(ctx['fields'])} fields.")

    # Step 2: Gap Analysis
    gap_res = dpr_gap_analyzer.analyze(ctx)
    print(f"Step 2: Gap Analysis -> Can proceed to DPR: {gap_res.can_proceed_to_dpr}, Blocking gaps: {len(gap_res.blocking_gaps)}")

    # Step 3: Stage 14.1 Handoff Package
    handoff = build_stage14_handoff_package(
        dpr_context_package=ctx,
        gap_analysis_result=gap_res,
        business_id=biz_id,
        scenario_id=scen_id,
    )
    print(f"Step 3: Created Handoff Package -> is_ready_for_stage_14_2: {handoff.readiness.is_ready_for_stage_14_2}")

    # Step 4: Run Stage 14.2 Enrichment Pipeline
    enrichment = await dpr_enrichment_service.run_enrichment(
        business_id=biz_id,
        scenario_id=scen_id,
        handoff_package_override=handoff
    )
    print(f"Step 4: Stage 14.2 Enrichment complete!")
    print(f"  Enrichment fields count: {len(enrichment.fields)}")
    print(f"  Enrichment overall_valid: {enrichment.validation.overall_valid}")
    print(f"  Enrichment ready_for_stage_14_3: {enrichment.ready_for_stage_14_3}")
    print(f"  Enrichment is_enrichment_complete: {enrichment.is_enrichment_complete}")
    print(f"  Validation passed checks: {enrichment.validation.passed_checks} / {enrichment.validation.total_checks}")
    print(f"  Blocking reasons: {enrichment.readiness.get('blocking_reasons')}")

    # Verify key regression values in enriched package
    f = enrichment.fields
    assert f["business_archetype"].value == "Essential Retail"
    assert f["nic_code"].value == "47110"
    assert f["promoter_experience_years"].value == 4.0
    assert f["covered_area_sqft"].value == 250.0
    assert f["total_project_cost"].value == 300000.0
    assert f["bank_term_loan_amount"].value == 270000.0
    assert f["promoter_equity_amount"].value == 30000.0
    assert f["glance_average_dscr"].value == 12.83
    assert f["glance_break_even_utilization"].value == 15.4
    assert f["target_scheme_code"].value == "MSME Term Loan Scheme"
    print("\n[SUCCESS] All Stage 14.1 and Stage 14.2 pipeline checks PASSED with 100% data integrity!")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
