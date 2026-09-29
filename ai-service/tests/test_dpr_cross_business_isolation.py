"""
Cross-Business Regression Test: Kirana/Grocery Store vs Dairy Farm vs Saree Retail.
Tests strict state, cache, provenance, and identity isolation across 3 businesses.

17-Step Verification Workflow:
1. Load Grocery
2. Populate DPR
3. Confirm Grocery title
4. Confirm Grocery entrepreneur
5. Switch to Dairy
6. Confirm Dairy title
7. Confirm Dairy entrepreneur
8. Confirm Dairy business activity
9. Confirm Dairy NIC
10. Confirm no Grocery values remain
11. Switch to Saree
12. Confirm Saree title
13. Confirm Saree-specific values
14. Return to Dairy
15. Confirm Dairy values are still intact
16. Return to Grocery
17. Confirm Grocery values are still intact

Assertions:
- Dairy title MUST NOT contain "Kirana"
- Dairy title MUST NOT contain "Grocery"
- Saree title MUST NOT contain "Kirana"
- Saree title MUST NOT contain "Dairy"
- Grocery title MUST NOT contain "Dairy"
- Grocery title MUST NOT contain "Saree"
- Entrepreneur identity isolation across all three businesses.
"""
import pytest
import asyncio
from typing import Dict, Any

from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager, DPR_STATE_ISOLATION_ERROR
from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service
from app.services.dpr_stage1.dpr_registry import is_business_concept_match


@pytest.mark.asyncio
async def test_cross_business_three_way_isolation_regression():
    """
    17-step workflow testing strict identity, cache, and provenance isolation
    between Kirana & Grocery Store, Dairy Farm, and Saree Retail.
    """
    # Isolated Test Business IDs
    biz_grocery = "test_grocery"
    biz_dairy = "test_dairy_unit"
    biz_saree = "test_saree_shop"

    # Step 1: Load Grocery
    grocery_scen = dpr_scenario_manager.get_or_create_scenario(biz_grocery)
    assert grocery_scen.business_id == biz_grocery

    # Step 2: Populate Grocery DPR
    for fid, ans in [
        ("business_name", "Kirana & Grocery Store"),
        ("business_activity", "Retail sale of daily groceries, food items and consumer staples"),
        ("promoter_name", "Ramesh Kumar"),
        ("nic_code", "47110"),
        ("target_state", "Maharashtra"),
        ("target_district", "Pune"),
        ("legal_constitution", "PROPRIETORSHIP"),
        ("premises_status", "RENTED"),
        ("carpet_area", 450.0),
        ("promoter_experience_years", 6.0),
        ("promoter_education", "GRADUATE"),
    ]:
        dpr_scenario_manager.set_user_answer(
            business_id=biz_grocery,
            field_id=fid,
            value=ans,
            scenario_id=grocery_scen.scenario_id
        )

    grocery_ctx = await dpr_context_builder.build_context(
        business_id=biz_grocery,
        scenario_id=grocery_scen.scenario_id
    )
    grocery_enrich = await dpr_enrichment_service.run_enrichment(
        business_id=biz_grocery,
        scenario_id=grocery_scen.scenario_id
    )

    # Step 3: Confirm Grocery title
    grocery_title = grocery_enrich.fields["dpr_title"].value
    assert "Kirana" in grocery_title or "Grocery" in grocery_title
    assert "Dairy" not in grocery_title
    assert "Saree" not in grocery_title

    # Step 4: Confirm Grocery entrepreneur
    grocery_promoter = grocery_enrich.fields["promoter_name"].value
    assert grocery_promoter == "Ramesh Kumar"

    # Step 5: Switch to Dairy
    dairy_scen = dpr_scenario_manager.get_or_create_scenario(biz_dairy)
    assert dairy_scen.business_id == biz_dairy
    assert dairy_scen.scenario_id != grocery_scen.scenario_id

    for fid, ans in [
        ("business_name", "Dairy Farm"),
        ("business_activity", "Dairy Farm"),
        ("promoter_name", "Suresh Patil"),
        ("nic_code", "01411"),
        ("target_state", "Karnataka"),
        ("target_district", "Mandya"),
        ("legal_constitution", "PROPRIETORSHIP"),
        ("premises_status", "OWNED"),
        ("carpet_area", 1200.0),
        ("promoter_experience_years", 8.0),
        ("promoter_education", "GRADUATE"),
    ]:
        dpr_scenario_manager.set_user_answer(
            business_id=biz_dairy,
            field_id=fid,
            value=ans,
            scenario_id=dairy_scen.scenario_id
        )

    dairy_ctx = await dpr_context_builder.build_context(
        business_id=biz_dairy,
        scenario_id=dairy_scen.scenario_id
    )
    dairy_enrich = await dpr_enrichment_service.run_enrichment(
        business_id=biz_dairy,
        scenario_id=dairy_scen.scenario_id
    )

    # Step 6: Confirm Dairy title
    dairy_title = dairy_enrich.fields["dpr_title"].value
    assert "Dairy Farm" in dairy_title
    # Assertions: Dairy title MUST NOT contain "Kirana" or "Grocery"
    assert "Kirana" not in dairy_title, f"Contaminated Dairy title: {dairy_title}"
    assert "Grocery" not in dairy_title, f"Contaminated Dairy title: {dairy_title}"

    # Step 7: Confirm Dairy entrepreneur
    dairy_promoter = dairy_enrich.fields["promoter_name"].value
    assert dairy_promoter == "Suresh Patil"
    assert dairy_promoter != grocery_promoter

    # Step 8: Confirm Dairy business activity
    dairy_activity = dairy_enrich.fields["business_activity"].value
    assert "Dairy" in dairy_activity
    assert "Groceries" not in dairy_activity

    # Step 9: Confirm Dairy NIC
    dairy_nic = dairy_enrich.fields["nic_code"].value
    assert dairy_nic == "01411"

    # Step 10: Confirm no Grocery values remain in Dairy context / enrichment
    for fid, f in dairy_enrich.fields.items():
        val_str = str(f.value).lower()
        src_str = str(f.source_reference).lower()
        assert "kirana" not in val_str, f"Field {fid} in Dairy contains Kirana: {f.value}"
        assert "grocery" not in val_str, f"Field {fid} in Dairy contains Grocery: {f.value}"
        assert "kirana" not in src_str, f"Field {fid} in Dairy has Kirana source: {f.source_reference}"

    # Step 11: Switch to Saree
    saree_scen = dpr_scenario_manager.get_or_create_scenario(biz_saree)
    assert saree_scen.business_id == biz_saree
    assert saree_scen.scenario_id != dairy_scen.scenario_id

    for fid, ans in [
        ("business_name", "Saree Retail"),
        ("business_activity", "Retail sale of traditional sarees and bridal wear"),
        ("promoter_name", "Priya Sharma"),
        ("nic_code", "47510"),
        ("target_state", "Uttar Pradesh"),
        ("target_district", "Varanasi"),
        ("legal_constitution", "PARTNERSHIP"),
        ("premises_status", "RENTED"),
        ("carpet_area", 800.0),
        ("promoter_experience_years", 10.0),
        ("promoter_education", "POST_GRADUATE"),
    ]:
        dpr_scenario_manager.set_user_answer(
            business_id=biz_saree,
            field_id=fid,
            value=ans,
            scenario_id=saree_scen.scenario_id
        )

    saree_ctx = await dpr_context_builder.build_context(
        business_id=biz_saree,
        scenario_id=saree_scen.scenario_id
    )
    saree_enrich = await dpr_enrichment_service.run_enrichment(
        business_id=biz_saree,
        scenario_id=saree_scen.scenario_id
    )

    # Step 12: Confirm Saree title
    saree_title = saree_enrich.fields["dpr_title"].value
    assert "Saree Retail" in saree_title or "Saree" in saree_title
    # Assertions: Saree title MUST NOT contain "Kirana" or "Dairy"
    assert "Kirana" not in saree_title, f"Contaminated Saree title: {saree_title}"
    assert "Dairy" not in saree_title, f"Contaminated Saree title: {saree_title}"

    # Step 13: Confirm Saree-specific values
    saree_promoter = saree_enrich.fields["promoter_name"].value
    assert saree_promoter == "Priya Sharma"
    assert saree_promoter != dairy_promoter
    assert saree_promoter != grocery_promoter

    # Step 14: Return to Dairy
    reloaded_dairy_ctx = await dpr_context_builder.build_context(
        business_id=biz_dairy,
        scenario_id=dairy_scen.scenario_id
    )
    reloaded_dairy_enrich = dpr_enrichment_service.get_persisted_enrichment(
        business_id=biz_dairy,
        scenario_id=dairy_scen.scenario_id
    )

    # Step 15: Confirm Dairy values are still intact
    assert reloaded_dairy_ctx["business_id"] == biz_dairy
    assert reloaded_dairy_enrich is not None
    assert reloaded_dairy_enrich.business_id == biz_dairy
    assert reloaded_dairy_enrich.scenario_id == dairy_scen.scenario_id
    assert "Dairy" in reloaded_dairy_enrich.fields["dpr_title"].value
    assert "Kirana" not in reloaded_dairy_enrich.fields["dpr_title"].value
    assert reloaded_dairy_enrich.fields["promoter_name"].value == "Suresh Patil"
    assert reloaded_dairy_enrich.fields["nic_code"].value == "01411"

    # Step 16: Return to Grocery
    reloaded_grocery_ctx = await dpr_context_builder.build_context(
        business_id=biz_grocery,
        scenario_id=grocery_scen.scenario_id
    )
    reloaded_grocery_enrich = dpr_enrichment_service.get_persisted_enrichment(
        business_id=biz_grocery,
        scenario_id=grocery_scen.scenario_id
    )

    # Step 17: Confirm Grocery values are still intact
    assert reloaded_grocery_ctx["business_id"] == biz_grocery
    assert reloaded_grocery_enrich is not None
    assert reloaded_grocery_enrich.business_id == biz_grocery
    assert reloaded_grocery_enrich.scenario_id == grocery_scen.scenario_id
    reloaded_grocery_title = reloaded_grocery_enrich.fields["dpr_title"].value
    assert "Kirana" in reloaded_grocery_title or "Grocery" in reloaded_grocery_title
    # Assertions: Grocery title MUST NOT contain "Dairy" or "Saree"
    assert "Dairy" not in reloaded_grocery_title, f"Contaminated Grocery title: {reloaded_grocery_title}"
    assert "Saree" not in reloaded_grocery_title, f"Contaminated Grocery title: {reloaded_grocery_title}"
    assert reloaded_grocery_enrich.fields["promoter_name"].value == "Ramesh Kumar"


@pytest.mark.asyncio
async def test_hard_cross_business_contamination_check():
    """
    Asserts that the hard cross-business contamination check raises DPR_STATE_ISOLATION_ERROR
    when scenario_id or package data belongs to another business.
    """
    grocery_scen = dpr_scenario_manager.get_or_create_scenario("test_kirana")
    
    # Passing Grocery scenario to Dairy in ScenarioRepository.get must raise DPR_STATE_ISOLATION_ERROR
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        dpr_scenario_manager.repo.get("test_dairy", grocery_scen.scenario_id)

    # In DPRContextBuilder, build_context with mismatched business and scenario raises isolation error
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        await dpr_context_builder.build_context(
            business_id="test_dairy",
            scenario_id=grocery_scen.scenario_id
        )

    # In DPREnrichmentService, get_persisted_enrichment with cross-business scenario raises isolation error
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        dpr_enrichment_service.get_persisted_enrichment(
            business_id="test_dairy",
            scenario_id=grocery_scen.scenario_id
        )
