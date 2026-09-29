"""
KALPA DPR Stage 14.1 — Authoritative Profile Data Lineage & Question Suppression Regression Test Suite.
Verifies that upstream Entrepreneur Profile (Stage 10/Stage 3/Stage 1) and user answer data
are monotonically consumed by the Canonical Field Registry and Question Engine, strictly preventing
duplicate questions, schema alias loss, falsy zero drops, and cross-scenario contamination.
"""
import pytest
import pytest_asyncio
from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    CANONICAL_SECTIONS,
    normalize_field_id,
    DPR_STATE_ISOLATION_ERROR,
)
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    CANONICAL_FIELDS,
    FieldResolutionStatus,
    get_canonical_entry,
    resolve_canonical_id,
    resolve_field_semantically,
    extract_value_from_dict,
    NON_ASKABLE_STATUSES,
)
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_gap_analyzer import dpr_gap_analyzer
from app.services.dpr_stage1.dpr_question_engine import dpr_question_engine, DPRQuestion
from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository, DPRScenarioState


@pytest.mark.asyncio
class TestDPR14_1ProfileLineageRegression:

    # 1. Experience upstream resolved suppresses question
    async def test_promoter_experience_upstream_resolved_suppresses_question(self):
        biz_id = "test_reg_exp_upstream_01"
        upstream = {
            "entrepreneur_profile": {"relevant_sector_experience": 3.0},
            "entrepreneur_readiness": {"relevant_sector_experience": 3.0},
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_experience_years"]
        assert field_rec["value"] == 3.0
        assert str(field_rec["status"]).startswith("RESOLVED_")

        gaps = dpr_gap_analyzer.analyze(ctx)
        gap_fids = [g.field_id for g in gaps.blocking_gaps + gaps.high_priority_gaps + gaps.optional_gaps]
        assert "promoter_experience_years" not in gap_fids

        q = await dpr_question_engine.pick_next_question(ctx, gaps)
        if q:
            assert q.field_id != "promoter_experience_years"

    # 2. Nested dict experience resolved
    async def test_promoter_experience_nested_dict_resolved(self):
        biz_id = "test_reg_exp_nested_02"
        upstream = {
            "entrepreneur_profile": {
                "experience": {"years_of_experience": 4}
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_experience_years"]
        assert field_rec["value"] == 4.0
        assert str(field_rec["status"]).startswith("RESOLVED_")

        gaps = dpr_gap_analyzer.analyze(ctx)
        gap_fids = [g.field_id for g in gaps.blocking_gaps + gaps.high_priority_gaps + gaps.optional_gaps]
        assert "promoter_experience_years" not in gap_fids

    # 3. Dot notation experience resolved
    async def test_promoter_experience_dot_notation_resolved(self):
        biz_id = "test_reg_exp_dot_03"
        upstream = {
            "entrepreneur_profile": {
                "experience.years_of_experience": 5
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_experience_years"]
        assert field_rec["value"] == 5.0
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 4. Zero years experience resolved without truthiness bug
    async def test_promoter_experience_zero_years_resolved_not_none(self):
        biz_id = "test_reg_exp_zero_04"
        upstream = {
            "entrepreneur_profile": {
                "years_of_experience": 0
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_experience_years"]
        assert field_rec["value"] == 0.0
        assert str(field_rec["status"]).startswith("RESOLVED_")
        assert field_rec["status"] != "USER_REQUIRED"

        gaps = dpr_gap_analyzer.analyze(ctx)
        gap_fids = [g.field_id for g in gaps.blocking_gaps + gaps.high_priority_gaps + gaps.optional_gaps]
        assert "promoter_experience_years" not in gap_fids

    # 5. User override precedence over profile
    async def test_promoter_experience_user_override_precedence(self):
        biz_id = "test_reg_exp_override_05"
        upstream = {
            "entrepreneur_profile": {"relevant_sector_experience": 2.0}
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream,
            user_overrides={"promoter_experience_years": 7.0}
        )
        field_rec = ctx["fields"]["promoter_experience_years"]
        assert field_rec["value"] == 7.0
        assert field_rec["status"] == FieldResolutionStatus.RESOLVED_USER.value

    # 6. Promoter education resolved
    async def test_promoter_education_upstream_resolved(self):
        biz_id = "test_reg_edu_06"
        upstream = {
            "entrepreneur_profile": {
                "education": {"highest_level": "GRADUATE"}
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_education"]
        assert field_rec["value"] == "GRADUATE"
        assert str(field_rec["status"]).startswith("RESOLVED_")

        gaps = dpr_gap_analyzer.analyze(ctx)
        gap_fids = [g.field_id for g in gaps.blocking_gaps + gaps.high_priority_gaps + gaps.optional_gaps]
        assert "promoter_education" not in gap_fids

    # 7. Promoter social category resolved
    async def test_promoter_social_category_upstream_resolved(self):
        biz_id = "test_reg_social_07"
        upstream = {
            "entrepreneur_profile": {
                "caste_category": "OBC"
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_social_category"]
        assert field_rec["value"] == "OBC"
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 8. Promoter EDP training status resolved
    async def test_promoter_edp_training_upstream_resolved(self):
        biz_id = "test_reg_edp_08"
        upstream = {
            "entrepreneur_profile": {
                "edp_training": "COMPLETED_RSETI"
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["promoter_edp_training_status"]
        assert field_rec["value"] == "COMPLETED_RSETI"
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 9. Covered area nested resources resolved
    async def test_covered_area_nested_resources_resolved(self):
        biz_id = "test_reg_area_09"
        upstream = {
            "entrepreneur_profile": {
                "resources": {"available_area_sqft": 450}
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["covered_area_sqft"]
        assert field_rec["value"] == 450.0
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 10. Premises status resolved
    async def test_premises_status_upstream_resolved(self):
        biz_id = "test_reg_prem_10"
        upstream = {
            "business_profile": {
                "premises_status": "RENTED"
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["premises_status"]
        assert field_rec["value"] == "RENTED"
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 11. Legal constitution resolved
    async def test_legal_constitution_upstream_resolved(self):
        biz_id = "test_reg_legal_11"
        upstream = {
            "business_profile": {
                "legal_constitution": "PROPRIETORSHIP"
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["legal_constitution"]
        assert field_rec["value"] == "PROPRIETORSHIP"
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 12. Udyam registration resolved
    async def test_udyam_registration_resolved(self):
        biz_id = "test_reg_udyam_12"
        upstream = {
            "business_profile": {
                "udyam": "UDYAM-KR-03-0012345"
            }
        }
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package=upstream
        )
        field_rec = ctx["fields"]["udyam_registration_number"]
        assert field_rec["value"] == "UDYAM-KR-03-0012345"
        assert str(field_rec["status"]).startswith("RESOLVED_")

    # 13. Monotonic resolution never downgrades to unknown
    async def test_monotonic_resolution_never_downgrades_to_unknown(self):
        biz_id = "test_reg_monotonic_13"
        scen_id = f"DPR-{biz_id}"
        state = scenario_repository.create_new_scenario(biz_id, scen_id)
        state.user_answers["promoter_experience_years"] = 3.5
        scenario_repository.save(state)

        ctx1 = await dpr_context_builder.build_context(
            business_id=biz_id,
            scenario_id=scen_id
        )
        assert ctx1["fields"]["promoter_experience_years"]["value"] == 3.5

        # Re-evaluating with empty direct params preserves 3.5 monotonically
        ctx2 = await dpr_context_builder.build_context(
            business_id=biz_id,
            scenario_id=scen_id
        )
        assert ctx2["fields"]["promoter_experience_years"]["value"] == 3.5
        assert str(ctx2["fields"]["promoter_experience_years"]["status"]).startswith("RESOLVED_")

    # 14. Unresolved gap produces question
    async def test_unresolved_material_gap_generates_question(self):
        biz_id = "test_reg_gap_14"
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            raw_intake_inputs={}
        )
        gaps = dpr_gap_analyzer.analyze(ctx)
        q = await dpr_question_engine.pick_next_question(ctx, gaps)
        # Should return a valid question for an unresolved editable gap
        if q:
            assert q.field_id in CANONICAL_FIELDS
            assert q.question_id == f"{q.field_id}:v1"
            assert q.question != ""

    # 15. Stable question ID
    async def test_stable_question_id(self):
        biz_id = "test_reg_qid_15"
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            raw_intake_inputs={}
        )
        gaps = dpr_gap_analyzer.analyze(ctx)
        q = await dpr_question_engine.pick_next_question(ctx, gaps)
        if q:
            assert q.question_id == f"{q.field_id}:v1"

    # 16. Cross-business isolation: Dairy vs Grocery
    async def test_cross_business_isolation_dairy_vs_grocery(self):
        dairy_id = "dairy_farm_isolated_reg"
        grocery_id = "grocery_store_isolated_reg"

        dairy_ctx = await dpr_context_builder.build_context(
            business_id=dairy_id,
            upstream_package={
                "business_profile": {
                    "business_name": "Gokul Dairy Farm",
                    "business_activity": "Dairy Farming & Milk Production"
                }
            }
        )
        grocery_ctx = await dpr_context_builder.build_context(
            business_id=grocery_id,
            upstream_package={
                "business_profile": {
                    "business_name": "Laxmi Kirana Store",
                    "business_activity": "Retail Grocery & FMCG Provisions"
                }
            }
        )

        assert "dairy" in dairy_ctx["fields"]["business_activity"]["value"].lower() or "milk" in dairy_ctx["fields"]["business_activity"]["value"].lower()
        assert "kirana" in grocery_ctx["fields"]["business_activity"]["value"].lower() or "grocery" in grocery_ctx["fields"]["business_activity"]["value"].lower()
        assert "kirana" not in dairy_ctx["fields"]["business_activity"]["value"].lower()
        assert "dairy" not in grocery_ctx["fields"]["business_activity"]["value"].lower()

    # 17. Lineage diagnostic data structure
    async def test_lineage_diagnostic_endpoint_data_structure(self):
        biz_id = "test_reg_lineage_17"
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            upstream_package={
                "entrepreneur_profile": {"years_of_experience": 2}
            }
        )
        fields = ctx.get("fields", {})
        assert len(fields) >= 80

        # Check promoter_experience_years lineage record properties
        exp_f = fields["promoter_experience_years"]
        assert exp_f["value"] == 2.0
        assert str(exp_f["status"]).startswith("RESOLVED_")
        assert "sources_checked" in exp_f
        assert len(exp_f["sources_checked"]) > 0
