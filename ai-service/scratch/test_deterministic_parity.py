import asyncio
import fitz
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager
from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service
from app.dpr.stage14_3.orchestrator import stage14_3_orchestrator
from app.dpr.stage14_3.document_schema import DPRGenerationRequest

async def test_deterministic_parity():
    # 1. Generate for dairy_farm with English promoter
    biz_id = "dairy_farm"
    scen = dpr_scenario_manager.get_or_create_scenario(biz_id)
    dpr_scenario_manager.set_user_answer(biz_id, "promoter_name", "Shriyanshu Kumar Kapsime", scenario_id=scen.scenario_id)
    await dpr_context_builder.build_context(biz_id, scen.scenario_id)
    await dpr_enrichment_service.run_enrichment(biz_id, scen.scenario_id)

    req_a = DPRGenerationRequest(business_id=biz_id, scenario_id=scen.scenario_id, format="pdf", language="en", regenerate_narrative=False)
    resp_a = await stage14_3_orchestrator.generate_dpr(req_a)

    # 2. Change ONLY promoter_name to Hindi in same scenario
    dpr_scenario_manager.set_user_answer(biz_id, "promoter_name", "श्रेयांसु कुमार कपसी में।", scenario_id=scen.scenario_id)
    await dpr_context_builder.build_context(biz_id, scen.scenario_id)
    await dpr_enrichment_service.run_enrichment(biz_id, scen.scenario_id)

    req_b = DPRGenerationRequest(business_id=biz_id, scenario_id=scen.scenario_id, format="pdf", language="en", regenerate_narrative=False)
    resp_b = await stage14_3_orchestrator.generate_dpr(req_b)

    print(f"Test A (English) Pages: {resp_a.page_count}")
    print(f"Test B (Hindi)   Pages: {resp_b.page_count}")
    print(f"Exact Match: {resp_a.page_count == resp_b.page_count}")

if __name__ == "__main__":
    asyncio.run(test_deterministic_parity())
