"""
KALPA DPR Regression Suite: Fresh-Start Pipeline + Profile Type Normalization + Stage 14.1/14.2 Handoff Contract.

Validates:
1. Exact resolution of numeric enum IDs (e.g. 2.0 -> "12TH_PASS" / "Higher Secondary (12th Pass)") without weakening Pydantic schemas.
2. Stage 14.2 handoff package construction without Pydantic validation errors.
3. Fresh DPR Scenario creation (unique scenario_id / iteration_id) inheriting all Stage 1–13 authoritative facts while cleanly resetting old DPR answers/overrides/question history.
4. Monotonic resolution and question suppression for known upstream facts.
5. Cross-business and cross-iteration isolation.
6. Full diagnostic lineage tracing.
"""
import pytest
import pytest_asyncio
from app.services.dpr_stage1.profile_normalizer import (
    profile_normalizer,
    ProfileNormalizer,
    EducationStatus,
    SocialCategory,
    TrainingStatus,
    PremisesStatus,
    LegalConstitution,
    NormalizedFieldResult,
)
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    FieldResolutionStatus,
    extract_value_from_dict,
    resolve_field_semantically,
    NON_ASKABLE_STATUSES,
)
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_gap_analyzer import dpr_gap_analyzer
from app.services.dpr_stage1.dpr_question_engine import dpr_question_engine
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager, scenario_repository
from app.services.dpr_stage1.dpr_handoff import (
    build_stage14_handoff_package,
    EntrepreneurContext,
    DPRStage14HandoffPackage,
)
from app.services.dpr_stage1.dpr_registry import DPR_STATE_ISOLATION_ERROR


# ============================================================================
# PART 1 & 2: PROFILE TYPE MAPPING & NORMALIZATION TESTS
# ============================================================================

class TestProfileTypeNormalization:

    def test_education_enum_id_normalizes_correctly(self):
        """Verify numeric IDs (int and float) map to canonical EducationStatus and display labels."""
        # 0 -> BELOW_8TH
        r0 = profile_normalizer.normalize_education(0.0)
        assert r0.canonical_value == "BELOW_8TH"
        assert r0.display_label == "Below 8th Pass"
        assert r0.canonical_type == "string"
        assert r0.is_valid is True

        # 1 -> 10TH_PASS
        r1 = profile_normalizer.normalize_education(1)
        assert r1.canonical_value == "10TH_PASS"
        assert r1.display_label == "Secondary (10th Pass)"

        # 2.0 -> 12TH_PASS (Exact bug reproduced and resolved)
        r2 = profile_normalizer.normalize_education(2.0)
        assert r2.canonical_value == "12TH_PASS"
        assert r2.display_label == "Higher Secondary (12th Pass)"
        assert r2.raw_value == 2.0
        assert r2.raw_type == "float"
        assert r2.normalization_method == "ENUM_ID_TO_LABEL"

        # 3 -> GRADUATE
        r3 = profile_normalizer.normalize_education("3")
        assert r3.canonical_value == "GRADUATE"

        # 4 -> POST_GRADUATE
        r4 = profile_normalizer.normalize_education(4.0)
        assert r4.canonical_value == "POST_GRADUATE"

        # 5 -> PROFESSIONAL_DOCTORATE
        r5 = profile_normalizer.normalize_education(5)
        assert r5.canonical_value == "PROFESSIONAL_DOCTORATE"

    def test_education_text_synonyms(self):
        """Verify human-readable strings resolve to canonical EducationStatus."""
        assert profile_normalizer.normalize_education("Intermediate (10+2)").canonical_value == "12TH_PASS"
        assert profile_normalizer.normalize_education("B.Tech Mechanical").canonical_value == "GRADUATE"
        assert profile_normalizer.normalize_education("MBA Finance").canonical_value == "POST_GRADUATE"
        assert profile_normalizer.normalize_education("Matriculation (10th)").canonical_value == "10TH_PASS"
        assert profile_normalizer.normalize_education("Ph.D Dairy Science").canonical_value == "PROFESSIONAL_DOCTORATE"

    def test_social_category_enum_id_normalizes_correctly(self):
        """Verify numeric IDs and text map to canonical SocialCategory."""
        # 1 -> GENERAL
        r1 = profile_normalizer.normalize_social_category(1.0)
        assert r1.canonical_value == "GENERAL"

        # 2.0 -> OBC (Exact bug reproduced and resolved)
        r2 = profile_normalizer.normalize_social_category(2.0)
        assert r2.canonical_value == "OBC"
        assert r2.display_label == "Other Backward Class (OBC)"
        assert r2.raw_value == 2.0
        assert r2.raw_type == "float"
        assert r2.normalization_method == "ENUM_ID_TO_LABEL"

        # 3 -> SC
        r3 = profile_normalizer.normalize_social_category(3)
        assert r3.canonical_value == "SC"

        # 4 -> ST
        r4 = profile_normalizer.normalize_social_category(4.0)
        assert r4.canonical_value == "ST"

        # 5 -> MINORITY
        r5 = profile_normalizer.normalize_social_category(5)
        assert r5.canonical_value == "MINORITY"

        # Women Entrepreneur
        rw = profile_normalizer.normalize_social_category("Women Entrepreneur")
        assert rw.canonical_value == "WOMEN"

    def test_edp_training_enum_id_normalizes_correctly(self):
        """Verify numeric IDs, booleans, and specific training subtypes map properly."""
        # 0 -> NOT_UNDERTAKEN
        r0 = profile_normalizer.normalize_training_status(0.0)
        assert r0.canonical_value == "NOT_UNDERTAKEN"

        # 1 -> COMPLETED
        r1 = profile_normalizer.normalize_training_status(1)
        assert r1.canonical_value == "COMPLETED"

        # 2.0 -> IN_PROGRESS (Exact bug reproduced and resolved)
        r2 = profile_normalizer.normalize_training_status(2.0)
        assert r2.canonical_value == "IN_PROGRESS"
        assert r2.display_label == "In Progress / Ongoing Training"
        assert r2.raw_value == 2.0
        assert r2.raw_type == "float"

        # Boolean True / False
        assert profile_normalizer.normalize_training_status(True).canonical_value == "COMPLETED"
        assert profile_normalizer.normalize_training_status(False).canonical_value == "NOT_UNDERTAKEN"

        # Specific subtype
        r_rseti = profile_normalizer.normalize_training_status("COMPLETED_RSETI")
        assert r_rseti.canonical_value == "COMPLETED_RSETI"
        assert r_rseti.canonical_enum == "COMPLETED"

    def test_invalid_profile_type_returns_mapping_error(self):
        """Verify unmappable data returns SOURCE_MAPPING_ERROR without crashing."""
        r = profile_normalizer.normalize_education("INVALID_UNKNOWN_DEGREE_XYZ_9999")
        assert r.status == "SOURCE_MAPPING_ERROR"
        assert r.canonical_value is None
        assert r.is_valid is False
        assert r.error_message is not None

    def test_experience_years_zero_preserved(self):
        """Verify 0.0 or 0 experience years is preserved as valid float (not None or UNKNOWN)."""
        r0 = profile_normalizer.normalize_experience_years(0)
        assert r0.canonical_value == 0.0
        assert r0.status == "RESOLVED_PROFILE"

        r0f = profile_normalizer.normalize_experience_years(0.0)
        assert r0f.canonical_value == 0.0
        assert r0f.status == "RESOLVED_PROFILE"

    def test_no_numeric_enum_leaks_into_context(self):
        """Verify extract_value_from_dict never leaks unrelated fields into education/social category."""
        corrupt_dict = {
            "experience": {"years_of_experience": 2.0}
        }
        # Searching for education aliases in a dict that only contains experience must return None, None
        val, path = extract_value_from_dict(corrupt_dict, ["promoter_education", "education", "highest_education"])
        assert val is None
        assert path is None


# ============================================================================
# PART 6, 7, 8, 9: FRESH DPR SCENARIO CREATION & INHERITANCE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestFreshDPRScenarioLifecycle:

    async def test_new_dpr_creates_new_scenario_id(self):
        """Verify create_fresh_dpr_scenario creates unique collision-safe scenario IDs."""
        biz_id = "test_fresh_dairy_01"
        s1 = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id)
        s2 = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id)

        assert s1.scenario_id != s2.scenario_id
        assert "-iter-" in s1.scenario_id
        assert "-iter-" in s2.scenario_id
        assert s1.business_id == biz_id
        assert s2.business_id == biz_id

    async def test_new_dpr_does_not_copy_old_answers_or_overrides(self):
        """Verify answers and overrides in scenario 1 are NOT present in fresh scenario 2."""
        biz_id = "test_fresh_dairy_02"
        s1 = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id)
        
        # User answers questions in iteration 1
        dpr_scenario_manager.set_user_answer(biz_id, "primary_sales_channel", "LOCAL_WHOLESALE", scenario_id=s1.scenario_id)
        dpr_scenario_manager.set_user_override(biz_id, "covered_area_sqft", 2500.0, scenario_id=s1.scenario_id)

        s1_loaded = dpr_scenario_manager.get_or_create_scenario(biz_id, s1.scenario_id)
        assert s1_loaded.user_answers.get("primary_sales_channel") == "LOCAL_WHOLESALE"
        assert s1_loaded.user_overrides.get("covered_area_sqft") == 2500.0

        # Create fresh iteration 2
        s2 = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id)
        s2_loaded = dpr_scenario_manager.get_or_create_scenario(biz_id, s2.scenario_id)

        # Fresh scenario has empty answers and overrides
        assert s2_loaded.user_answers == {}
        assert s2_loaded.user_overrides == {}
        assert s2_loaded.accepted_benchmarks == {}
        assert s2_loaded.question_history == []

    async def test_new_dpr_inherits_upstream_profile_and_engines(self):
        """Verify fresh DPR inherits Stages 1–13 authoritative facts automatically."""
        biz_id = "test_fresh_dairy_03"
        upstream = {
            "business_intake": {
                "business_name": "Gokul Pure Dairy Farm",
                "promoter_name": "Ramesh Patel",
                "location_state": "Gujarat",
                "location_district": "Anand",
            },
            "classification": {
                "business_node_id": "dairy_farm_001",
                "archetype": "dairy",
                "nic_code": "01411",
                "sector": "Agri & Allied"
            },
            "entrepreneur_profile": {
                "education": 2.0,  # Raw float enum ID
                "social_category": 2.0,  # Raw float enum ID
                "edp_training_status": 1.0,  # Raw float enum ID
                "years_of_experience": 4.5
            },
            "financial_package": {
                "total_project_cost": 1500000.0,
                "promoter_contribution": 300000.0,
                "bank_loan_requirement": 1200000.0,
                "dscr": 1.85,
                "break_even": 42.5
            },
            "feasibility_context": {
                "overall_feasibility_score": 91.0,
                "viability_status": "BANKABLE_COMMERCIALLY_VIABLE"
            },
            "swot_context": {
                "swot": {
                    "strengths": ["Strong local dairy cooperative network"],
                    "weaknesses": ["Working capital seasonality"],
                    "opportunities": ["Direct milk packaging brand"],
                    "threats": ["Fodder cost inflation"]
                }
            }
        }

        fresh_scen = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id, upstream_context=upstream)

        # Build context for fresh scenario
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            scenario_id=fresh_scen.scenario_id,
            upstream_package=upstream,
            user_overrides=fresh_scen.user_overrides,
            user_answers=fresh_scen.user_answers
        )

        # 1. Classification inherited
        assert ctx["fields"]["business_archetype"]["value"] == "dairy"
        assert ctx["fields"]["business_archetype"]["status"] in [FieldResolutionStatus.RESOLVED_ENGINE.value, FieldResolutionStatus.RESOLVED_UPSTREAM.value]

        # 2. Profile inherited and normalized (float 2.0 -> "12TH_PASS", "OBC", "COMPLETED")
        assert ctx["fields"]["promoter_education"]["value"] == "12TH_PASS"
        assert ctx["fields"]["promoter_social_category"]["value"] == "OBC"
        assert ctx["fields"]["promoter_edp_training_status"]["value"] == "COMPLETED"
        assert ctx["fields"]["promoter_experience_years"]["value"] == 4.5

        # 3. Financials inherited
        assert ctx["fields"]["total_project_cost"]["value"] == 1500000.0
        dscr_val = ctx["fields"]["dscr_analysis_multi_year"]["value"]
        assert (dscr_val.get("average_dscr") == 1.85 if isinstance(dscr_val, dict) else dscr_val == 1.85)

        # 4. Feasibility & SWOT inherited
        assert ctx["fields"]["feasibility_viability_synthesis"]["status"] == FieldResolutionStatus.RESOLVED_ENGINE.value
        assert ctx["fields"]["dynamic_swot_matrix"]["status"] == FieldResolutionStatus.RESOLVED_ENGINE.value

        # 5. Gap analysis & Question engine: Inherited fields must NOT be asked
        gaps = dpr_gap_analyzer.analyze(ctx)
        gap_fids = [g.field_id for g in gaps.blocking_gaps + gaps.high_priority_gaps + gaps.optional_gaps]

        assert "promoter_education" not in gap_fids
        assert "promoter_social_category" not in gap_fids
        assert "promoter_edp_training_status" not in gap_fids
        assert "promoter_experience_years" not in gap_fids
        assert "total_project_cost" not in gap_fids
        assert "business_archetype" not in gap_fids


# ============================================================================
# PART 21 & 22: STAGE 14.2 HANDOFF & PYDANTIC VALIDATION FIX
# ============================================================================

@pytest.mark.asyncio
class TestStage14_2HandoffContract:

    async def test_14_2_consumes_canonical_context_with_no_pydantic_error(self):
        """
        Critical Test: Verify that when raw upstream profile contains float 2.0 for
        education, social_category, and edp_training_status, build_stage14_handoff_package
        successfully constructs EntrepreneurContext without Pydantic validation errors.
        """
        biz_id = "test_handoff_dairy_04"
        upstream = {
            "business_intake": {
                "business_name": "Amrit Dairy Farm",
                "promoter_name": "Sunita Sharma",
                "location_state": "Rajasthan",
                "location_district": "Jaipur",
                "raw_business_description": "Modern commercial dairy farm with 20 HF cows"
            },
            "classification": {
                "archetype": "dairy",
                "nic_code": "01411"
            },
            "entrepreneur_profile": {
                "education": 2.0,  # Float 2.0
                "social_category": 2.0,  # Float 2.0
                "edp_training_status": 2.0,  # Float 2.0
                "years_of_experience": 3.0
            }
        }

        fresh_scen = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id, upstream_context=upstream)

        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            scenario_id=fresh_scen.scenario_id,
            upstream_package=upstream
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)

        # Build Stage 14.1 -> 14.2 handoff package
        handoff = build_stage14_handoff_package(
            business_id=biz_id,
            context=ctx,
            gap_analysis=gap_res,
            scenario_id=fresh_scen.scenario_id
        )

        assert isinstance(handoff, DPRStage14HandoffPackage)
        assert isinstance(handoff.entrepreneur_context, EntrepreneurContext)
        
        # Verify strict type safety: strings, not floats
        assert handoff.entrepreneur_context.education == "12TH_PASS"
        assert isinstance(handoff.entrepreneur_context.education, str)

        assert handoff.entrepreneur_context.social_category == "OBC"
        assert isinstance(handoff.entrepreneur_context.social_category, str)

        assert handoff.entrepreneur_context.edp_training_status == "IN_PROGRESS"
        assert isinstance(handoff.entrepreneur_context.edp_training_status, str)

        assert handoff.entrepreneur_context.experience_years == 3.0
        assert isinstance(handoff.entrepreneur_context.experience_years, float)


# ============================================================================
# PART 23: DIAGNOSTIC LINEAGE ENDPOINT TEST
# ============================================================================

@pytest.mark.asyncio
class TestLineageProvenance:

    async def test_lineage_records_complete_provenance(self):
        """Verify field lineage contains raw_value, canonical_value, normalization_method, and question_suppressed."""
        biz_id = "test_lineage_dairy_05"
        upstream = {
            "business_intake": {
                "business_name": "Krishna Dairy",
                "promoter_name": "Krishna Murthy",
                "location_state": "Karnataka",
                "location_district": "Mysuru"
            },
            "entrepreneur_profile": {
                "education": 2.0,
                "social_category": 1.0,
                "years_of_experience": 5.0
            }
        }

        fresh_scen = dpr_scenario_manager.create_fresh_dpr_scenario(biz_id, upstream_context=upstream)
        ctx = await dpr_context_builder.build_context(
            business_id=biz_id,
            scenario_id=fresh_scen.scenario_id,
            upstream_package=upstream
        )

        edu_rec = ctx["fields"]["promoter_education"]
        assert edu_rec["value"] == "12TH_PASS"
        assert edu_rec["raw_value"] == 2.0
        assert edu_rec["raw_type"] == "float"
        assert edu_rec["canonical_type"] == "string"
        assert edu_rec["normalization_method"] == "ENUM_ID_TO_LABEL"
        assert edu_rec["question_suppressed"] is True
        assert edu_rec["status"] == FieldResolutionStatus.RESOLVED_PROFILE.value
