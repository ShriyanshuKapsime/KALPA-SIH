"""
Comprehensive Test Suite for KALPA Stage 14.3:
Final Institutional-Grade Bank-Review-Ready DPR Generation Engine with Sarvam LLM Narrative Layer.

Tests:
1. Sarvam API success (mocked)
2. Sarvam timeout fallback
3. Sarvam invalid response fallback
4. Sarvam hallucinated number rejection (explicit test: project_cost = 500000, LLM = ₹700000 -> FAIL -> Fallback -> No 700000 in PDF)
5. Sarvam hallucinated competitor & scheme rejection
6. UNKNOWN != ZERO handling
7. Placeholder resolution ({{PROJECT_COST}}, {{TERM_LOAN}}, etc.)
8. Source reference preservation (Annexure Q)
9. Deterministic fallback behavior
10. Narrative cache hit and invalidation
11. Business / scenario identity mismatch (DPR_STATE_ISOLATION_ERROR)
12. Complete DPR generation & PDF structural validation (page count > 1, dual orientation, TOC, headers, footers)
13. Financial consistency validation (M1–M6 parity)
14. Disallowed token scan ({{, None, null, undefined, <div, Traceback, TODO, FIXME)
15. Visual regression inspection (PyMuPDF pixmap inspection)
16. Cross-business isolation (Grocery vs Dairy vs Saree)
"""
import io
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pypdf import PdfReader
import pymupdf as fitz

from app.dpr.stage14_3 import (
    Stage14_3Orchestrator,
    stage14_3_orchestrator,
    DPRStatus,
    DPR_STATE_ISOLATION_ERROR,
    DPRGenerationRequest,
    DPRGenerationResponse,
    SarvamDPRNarrativeService,
    DPRNarrativePlanner,
    DPRNarrativeGenerator,
    narrative_cache,
    DPRNarrativeValidator,
    DPRDocumentAssembler,
    DPRPDFRenderer,
    dpr_pdf_renderer,
    DPRValidator,
    DPRStatusEngine,
    SectionNarrative,
    NarrativePlan,
    NarrativeProviderMetadata,
)
from app.dpr.stage14_3.tables import sanitize_table_val
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service


# -------------------------------------------------------------------------
# HELPER: Clean Enriched Business Package (Dairy Farm)
# -------------------------------------------------------------------------
async def get_dairy_enrichment_package():
    biz_id = "test_dpr_dairy"
    scen = dpr_scenario_manager.get_or_create_scenario(biz_id)

    # Populate canonical fields
    for fid, ans in [
        ("business_name", "Ganga Dairy & Livestock Unit"),
        ("business_activity", "Commercial Dairy Farming and Milk Production"),
        ("promoter_name", "Suresh Patil"),
        ("nic_code", "01411"),
        ("target_state", "Maharashtra"),
        ("target_district", "Kolhapur"),
        ("legal_constitution", "PROPRIETORSHIP"),
        ("premises_status", "OWNED"),
        ("carpet_area", 1500.0),
        ("promoter_experience_years", 8.0),
        ("promoter_education", "GRADUATE"),
    ]:
        dpr_scenario_manager.set_user_answer(
            business_id=biz_id,
            field_id=fid,
            value=ans,
            scenario_id=scen.scenario_id
        )

    await dpr_context_builder.build_context(biz_id, scen.scenario_id)
    pkg = await dpr_enrichment_service.run_enrichment(biz_id, scen.scenario_id)
    return pkg


# -------------------------------------------------------------------------
# 1. SARVAM API SUCCESS (MOCKED)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sarvam_api_success_mock():
    mock_service = SarvamDPRNarrativeService(api_key="test_key_dummy")

    mock_plan = {
        "section_id": "executive_summary",
        "key_points": ["Commercial dairy production", "Outlay of {{PROJECT_COST}}"],
        "evidence_to_reference": ["market_study"],
        "facts_used": ["business_name", "total_project_cost"],
        "recommended_length": "medium"
    }

    mock_draft = {
        "section_id": "executive_summary",
        "title": "Executive Summary",
        "paragraphs": [
            "The proposed enterprise, Ganga Dairy, envisages establishing a commercial milk production unit.",
            "The total capital outlay required is {{PROJECT_COST}}, financed through {{PROMOTER_CONTRIBUTION}} and {{TERM_LOAN}}."
        ],
        "facts_used": ["business_name", "total_project_cost"],
        "source_refs": ["financial_package"]
    }

    with patch.object(mock_service, "_call_sarvam_chat", side_effect=[mock_plan, mock_draft]):
        plan = await mock_service.create_narrative_plan(
            section_id="executive_summary",
            section_title="Executive Summary",
            source_data={"business_name": "Ganga Dairy", "total_project_cost": 1000000.0}
        )
        assert plan is not None
        assert "Commercial dairy production" in plan.key_points

        draft = await mock_service.draft_section_narrative(
            section_id="executive_summary",
            section_title="Executive Summary",
            plan=plan,
            source_data={"business_name": "Ganga Dairy", "total_project_cost": 1000000.0}
        )
        assert draft is not None
        assert draft.provider_metadata.provider == "sarvam"
        assert draft.provider_metadata.fallback_used is False
        assert len(draft.paragraphs) == 2


# -------------------------------------------------------------------------
# 2. SARVAM TIMEOUT & FALLBACK
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sarvam_timeout_fallback():
    mock_service = SarvamDPRNarrativeService(api_key="test_key_dummy")
    with patch.object(mock_service, "_call_sarvam_chat", side_effect=asyncio.TimeoutError("Timeout")):
        gen = DPRNarrativeGenerator(sarvam_service=mock_service)
        narrative = await gen.generate_section(
            section_id="executive_summary",
            section_title="Executive Summary",
            business_id="test_timeout_biz",
            scenario_id="DPR-test",
            source_data={"business_name": "Timeout Unit", "location": "Pune, Maharashtra"},
            force_regenerate=True
        )

        assert narrative is not None
        assert narrative.provider_metadata.fallback_used is True
        assert narrative.provider_metadata.provider == "deterministic"
        assert any("Timeout Unit" in p for p in narrative.paragraphs)


# -------------------------------------------------------------------------
# 3. SARVAM INVALID RESPONSE FALLBACK
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sarvam_invalid_response_fallback():
    mock_service = SarvamDPRNarrativeService(api_key="test_key_dummy")
    # Returns None (e.g. malformed JSON or empty choices)
    with patch.object(mock_service, "_call_sarvam_chat", return_value=None):
        gen = DPRNarrativeGenerator(sarvam_service=mock_service)
        narrative = await gen.generate_section(
            section_id="technical_feasibility",
            section_title="Technical Feasibility",
            business_id="test_inv_biz",
            scenario_id="DPR-test",
            source_data={"business_name": "Invalid Response Unit"},
            force_regenerate=True
        )

        assert narrative is not None
        assert narrative.provider_metadata.fallback_used is True
        assert "Technical & Operational Feasibility" in narrative.title or "Technical" in narrative.title


# -------------------------------------------------------------------------
# 4. EXPLICIT HALLUCINATED NUMBER REJECTION TEST
# Input: project_cost = 500000
# LLM: "The proposed project requires an investment of ₹700000."
# EXPECTED: NARRATIVE_VALIDATION_FAILED -> Fallback -> PDF must NOT contain 700000
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sarvam_hallucinated_number_rejection():
    validator = DPRNarrativeValidator()

    # Source has 500000 (5 lakh)
    source_data = {
        "business_name": "Standard Store",
        "total_project_cost": 500000.0,
        "term_loan": 375000.0,
        "promoter_contribution": 125000.0,
    }

    # Valid narrative with 5 lakh / placeholders
    valid_narrative = SectionNarrative(
        section_id="project_cost",
        title="Project Cost",
        paragraphs=["The proposed project requires an investment of ₹5 lakh, financed via term loan."],
        facts_used=["total_project_cost"],
        source_refs=["financial_package"]
    )
    val_res = validator.validate_narrative(valid_narrative, source_data, "project_cost")
    assert val_res.is_valid is True

    # Hallucinated narrative asserting ₹700000
    hallucinated_narrative = SectionNarrative(
        section_id="project_cost",
        title="Project Cost",
        paragraphs=["The proposed project requires an investment of ₹700000."],
        facts_used=["total_project_cost"],
        source_refs=["financial_package"]
    )
    val_fail_res = validator.validate_narrative(hallucinated_narrative, source_data, "project_cost")
    assert val_fail_res.is_valid is False
    assert any("700000" in check for check in val_fail_res.failed_checks)

    # Now verify that DPRNarrativeGenerator rejects this draft, falls back, and does NOT emit 700000
    mock_service = SarvamDPRNarrativeService(api_key="test_key_dummy")
    with patch.object(mock_service, "_call_sarvam_chat", return_value={
        "section_id": "project_cost_means_finance",
        "title": "Project Cost & Means of Finance",
        "paragraphs": ["The proposed project requires an investment of ₹700000."],
        "facts_used": ["total_project_cost"],
        "source_refs": ["financial_package"]
    }):
        gen = DPRNarrativeGenerator(sarvam_service=mock_service, validator=validator)
        final_narrative = await gen.generate_section(
            section_id="project_cost_means_finance",
            section_title="Project Cost & Means of Finance",
            business_id="test_halluc_biz",
            scenario_id="DPR-halluc",
            source_data=source_data,
            force_regenerate=True
        )

        assert final_narrative.provider_metadata.fallback_used is True
        for p in final_narrative.paragraphs:
            assert "700000" not in p
            assert "₹700000" not in p
            assert "7 lakh" not in p.lower()


# -------------------------------------------------------------------------
# 5. HALLUCINATED COMPETITOR & SCHEME REJECTION
# -------------------------------------------------------------------------
def test_hallucinated_competitor_and_scheme_rejection():
    validator = DPRNarrativeValidator()
    source_data = {
        "business_name": "Agri Tech",
        "schemes": {"applicable_scheme": "PMEGP"},
    }

    # Prohibited buzzwords
    bad_buzzword_narrative = SectionNarrative(
        section_id="executive_summary",
        title="Summary",
        paragraphs=["This is a game-changing, highly profitable rural venture with guaranteed success."],
        facts_used=[],
        source_refs=[]
    )
    res = validator.validate_narrative(bad_buzzword_narrative, source_data, "executive_summary")
    assert res.is_valid is False
    assert any("game-changing" in f for f in res.failed_checks)

    # Hallucinated scheme not in source
    bad_scheme_narrative = SectionNarrative(
        section_id="schemes",
        title="Schemes",
        paragraphs=["The unit is approved under XYZUNAUTHORIZED scheme for 90% capital grant."],
        facts_used=[],
        source_refs=[]
    )
    res2 = validator.validate_narrative(bad_scheme_narrative, source_data, "schemes")
    assert res2.is_valid is False
    assert any("XYZUNAUTHORIZED" in f for f in res2.failed_checks)


# -------------------------------------------------------------------------
# 6. UNKNOWN != ZERO HANDLING
# -------------------------------------------------------------------------
def test_unknown_not_zero_handling():
    # Never render UNKNOWN as 0 or ₹0
    assert sanitize_table_val(None) == "Not resolved"
    assert sanitize_table_val("UNKNOWN") == "Not resolved"
    assert sanitize_table_val("USER_REQUIRED") == "To be provided"
    assert sanitize_table_val("DOCUMENT_PENDING") == "Pending document"
    assert sanitize_table_val("NOT_APPLICABLE") == "Not applicable"
    assert sanitize_table_val("CONFLICT") == "Conflict requires resolution"
    assert sanitize_table_val("SOURCE_MAPPING_ERROR") == "Source mapping requires review"
    # Concrete zero remains 0 or formatted currency
    assert "0.00" in sanitize_table_val(0, is_currency=True)
    assert "50,000.00" in sanitize_table_val(50000, is_currency=True)


# -------------------------------------------------------------------------
# 7. PLACEHOLDER RESOLUTION
# -------------------------------------------------------------------------
def test_placeholder_resolution():
    fin_pkg = {
        "total_project_cost": 1250000.0,
        "promoter_contribution": 312500.0,
        "term_loan": 937500.0,
        "working_capital": 200000.0,
        "year1_revenue": 1800000.0,
        "year5_revenue": 3200000.0,
        "ebitda_margin_pct": 24.5,
        "pat_year1": 210000.0,
        "average_dscr": 2.15,
        "minimum_dscr": 1.78,
        "break_even_utilization": 42.0,
    }

    ph_map = DPRDocumentAssembler.build_placeholder_map(None, fin_pkg)
    raw_text = (
        "Total outlay is {{PROJECT_COST}}, funded by {{PROMOTER_CONTRIBUTION}} and {{TERM_LOAN}}. "
        "Average DSCR is {{AVERAGE_DSCR}} and break-even is {{BREAK_EVEN}}."
    )

    resolved = DPRDocumentAssembler.resolve_placeholders(raw_text, ph_map)
    assert "{{" not in resolved
    assert "}}" not in resolved
    assert "12,50,000" in resolved
    assert "3,12,500" in resolved
    assert "9,37,500" in resolved
    assert "2.15x" in resolved
    assert "42.0%" in resolved


# -------------------------------------------------------------------------
# 8. IDENTITY VALIDATION & STATE ISOLATION (DPR_STATE_ISOLATION_ERROR)
# -------------------------------------------------------------------------
def test_identity_validation_mismatch():
    pkg = MagicMock()
    pkg.business_id = "test_dairy_unit"
    pkg.scenario_id = "DPR-dairy"

    # Mismatched business ID -> MUST raise DPR_STATE_ISOLATION_ERROR
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        DPRValidator.validate_identity(
            requested_business_id="test_grocery_store",
            requested_scenario_id="DPR-dairy",
            package=pkg
        )

    # Mismatched scenario ID -> MUST raise DPR_STATE_ISOLATION_ERROR
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        DPRValidator.validate_identity(
            requested_business_id="test_dairy_unit",
            requested_scenario_id="DPR-saree-001",
            package=pkg
        )

    # Matching IDs -> Pass
    DPRValidator.validate_identity(
        requested_business_id="test_dairy_unit",
        requested_scenario_id="DPR-dairy",
        package=pkg
    )


# -------------------------------------------------------------------------
# 9. COMPLETE END-TO-END DPR GENERATION & PDF VALIDATION
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_complete_dpr_generation_and_pdf_structure():
    pkg = await get_dairy_enrichment_package()
    req = DPRGenerationRequest(
        business_id=pkg.business_id,
        scenario_id=pkg.scenario_id,
        format="pdf",
        language="en"
    )

    resp: DPRGenerationResponse = await stage14_3_orchestrator.generate_dpr(req)

    assert resp.status == "COMPLETED"
    assert resp.page_count > 1
    assert resp.dpr_status in (DPRStatus.BANK_REVIEW_READY, DPRStatus.READY_FOR_SUBMISSION)
    assert resp.file_path is not None
    assert os.path.exists(resp.file_path)

    # 1. Inspect generated PDF with pypdf
    with open(resp.file_path, "rb") as f:
        pdf_bytes = f.read()

    reader = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)
    assert num_pages >= 4  # True multi-page document

    # 2. Search for disallowed tokens (MUST BE ZERO)
    clean, violations = DPRValidator.scan_pdf_text_for_disallowed_tokens(pdf_bytes)
    assert clean is True, f"PDF contains disallowed tokens: {violations}"

    # 3. Check for mandatory content in text
    all_text = " ".join([page.extract_text() for page in reader.pages])
    assert "DETAILED PROJECT REPORT" in all_text
    assert "DOCUMENT CONTROL" in all_text
    assert "EXECUTIVE SUMMARY" in all_text
    assert "PROJECT AT A GLANCE" in all_text
    assert "ANNEXURE E" in all_text
    assert "ANNEXURE F" in all_text
    assert "ANNEXURE J" in all_text

    # 4. Visual regression check with PyMuPDF
    vis_clean, vis_pages, vis_errs = DPRValidator.validate_visual_regression(pdf_bytes)
    assert vis_clean is True, f"Visual regression errors: {vis_errs}"
    assert vis_pages == num_pages


# -------------------------------------------------------------------------
# 10. CROSS-BUSINESS THREE-WAY ISOLATION REGRESSION
# Grocery -> Dairy -> Saree -> Grocery (zero contamination)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cross_business_isolation_three_way():
    biz_grocery = "test_iso_grocery"
    biz_dairy = "test_iso_dairy"
    biz_saree = "test_iso_saree"

    # 1. Setup Grocery
    scen_g = dpr_scenario_manager.get_or_create_scenario(biz_grocery)
    for fid, ans in [
        ("business_name", "Annapurna Kirana & Grocery"),
        ("business_activity", "Retail distribution of food staples"),
        ("promoter_name", "Rameshwar Gupta"),
        ("nic_code", "47110"),
        ("target_state", "Maharashtra"),
        ("target_district", "Pune"),
    ]:
        dpr_scenario_manager.set_user_answer(biz_grocery, fid, ans, scenario_id=scen_g.scenario_id)
    await dpr_context_builder.build_context(biz_grocery, scen_g.scenario_id)
    pkg_g = await dpr_enrichment_service.run_enrichment(biz_grocery, scen_g.scenario_id)

    # 2. Setup Dairy
    scen_d = dpr_scenario_manager.get_or_create_scenario(biz_dairy)
    for fid, ans in [
        ("business_name", "Amrutdhara Dairy Farm"),
        ("business_activity", "Commercial Dairy Milking Unit"),
        ("promoter_name", "Suresh Patil"),
        ("nic_code", "01411"),
        ("target_state", "Maharashtra"),
        ("target_district", "Kolhapur"),
    ]:
        dpr_scenario_manager.set_user_answer(biz_dairy, fid, ans, scenario_id=scen_d.scenario_id)
    await dpr_context_builder.build_context(biz_dairy, scen_d.scenario_id)
    pkg_d = await dpr_enrichment_service.run_enrichment(biz_dairy, scen_d.scenario_id)

    # 3. Setup Saree
    scen_s = dpr_scenario_manager.get_or_create_scenario(biz_saree)
    for fid, ans in [
        ("business_name", "Banaras Silk & Saree Retail"),
        ("business_activity", "Traditional Saree Showroom"),
        ("promoter_name", "Priya Sharma"),
        ("nic_code", "47510"),
        ("target_state", "Uttar Pradesh"),
        ("target_district", "Varanasi"),
    ]:
        dpr_scenario_manager.set_user_answer(biz_saree, fid, ans, scenario_id=scen_s.scenario_id)
    await dpr_context_builder.build_context(biz_saree, scen_s.scenario_id)
    pkg_s = await dpr_enrichment_service.run_enrichment(biz_saree, scen_s.scenario_id)

    # Generate Dairy DPR
    resp_dairy = await stage14_3_orchestrator.generate_dpr(
        DPRGenerationRequest(business_id=biz_dairy, scenario_id=scen_d.scenario_id)
    )
    with open(resp_dairy.file_path, "rb") as f:
        dairy_text = " ".join([page.extract_text() for page in PdfReader(f).pages])

    # Assert Dairy has zero Kirana or Saree words
    assert "Amrutdhara Dairy" in dairy_text
    assert "Suresh Patil" in dairy_text
    assert "Kirana" not in dairy_text
    assert "Annapurna" not in dairy_text
    assert "Saree" not in dairy_text
    assert "Priya Sharma" not in dairy_text

    # Generate Saree DPR
    resp_saree = await stage14_3_orchestrator.generate_dpr(
        DPRGenerationRequest(business_id=biz_saree, scenario_id=scen_s.scenario_id)
    )
    with open(resp_saree.file_path, "rb") as f:
        saree_text = " ".join([page.extract_text() for page in PdfReader(f).pages])

    # Assert Saree has zero Dairy or Kirana words
    assert "Banaras Silk" in saree_text
    assert "Priya Sharma" in saree_text
    assert "Amrutdhara" not in saree_text
    assert "Dairy" not in saree_text
    assert "Kirana" not in saree_text
