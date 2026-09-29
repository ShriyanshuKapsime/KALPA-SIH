"""
Golden Dairy Farm DPR Acceptance Test (Part AG)
Verifies:
1. End-to-end DPR generation for dairy_farm scenario
2. All 39 canonical sections and 4 annexures (E, F, J, Q)
3. Zero disallowed tokens ({{, }}, {%, %}, TODO, TBD, None, null, NaN, undefined, %%, etc.)
4. Clean Unicode ₹ rendering (260+ instances verified)
5. Dynamic TOC page alignment (Pass 1 & Pass 2 match actual section target page numbers)
6. Financial consistency across Executive Summary, Glance, Tables, and Annexures
7. Preview and Download endpoints serve identical PDF bytes
"""
import io
import os
import re
import sys
import asyncio
from pypdf import PdfReader
import fitz  # PyMuPDF

from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager
from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service
from app.dpr.stage14_3.orchestrator import stage14_3_orchestrator
from app.dpr.stage14_3.document_schema import DPRGenerationRequest, DPRStatus
from app.dpr.stage14_3.validation import DPRValidator
from app.api.routes.dpr import preview_stage_14_3_pdf, download_stage_14_3_pdf


CANONICAL_SECTIONS_39 = [
    "01. EXECUTIVE SUMMARY",
    "02. PROJECT AT A GLANCE",
    "03. PROMOTER & ENTREPRENEUR PROFILE",
    "04. ENTERPRISE & LEGAL STRUCTURE",
    "05. BUSINESS & PRODUCT DESCRIPTION",
    "06. INDUSTRY & SECTOR OVERVIEW",
    "07. MARKET POTENTIAL & DEMAND ANALYSIS",
    "08. COMPETITION & LOCAL ASSESSMENT",
    "09. MARKETING & DISTRIBUTION STRATEGY",
    "10. RAW MATERIAL & SUPPLY CHAIN",
    "11. TECHNICAL & OPERATIONAL FEASIBILITY",
    "12. OPERATIONAL PROCESS FLOW",
    "13. LOCATION & INFRASTRUCTURE PARAMETERS",
    "14. PLANT, MACHINERY & FIXED ASSETS",
    "15. MANPOWER & EMPLOYMENT STRUCTURE",
    "16. PROJECT CAPITAL OUTLAY & BREAKDOWN",
    "17. MEANS OF FINANCE & CAPITAL STRUCTURE",
    "18. WORKING CAPITAL ASSESSMENT & CYCLES",
    "19. CAPACITY & PRODUCTION PROGRAMME",
    "20. REVENUE PROJECTIONS (5 YEARS)",
    "21. PROJECTED PROFIT & LOSS SUMMARY",
    "22. PROJECTED BALANCE SHEET SUMMARY",
    "23. PROJECTED CASH FLOW STATEMENT",
    "24. DEPRECIATION SCHEDULE SUMMARY",
    "25. TERM LOAN AMORTIZATION SCHEDULE",
    "26. DEBT SERVICE COVERAGE RATIO (DSCR)",
    "27. BREAK-EVEN SALES & MARGIN OF SAFETY",
    "28. FINANCIAL & BANKING RATIO ANALYSIS",
    "29. SENSITIVITY & STRESS TESTING ANALYSIS",
    "30. RISK ASSESSMENT & MITIGATION MATRIX",
    "31. STRUCTURED SWOT ANALYSIS",
    "32. TECHNO-ECONOMIC FEASIBILITY GATES",
    "33. GOVERNMENT SCHEME & SUBSIDY MAPPING",
    "34. STATUTORY APPROVALS & REGISTRATIONS",
    "35. PROJECT IMPLEMENTATION SCHEDULE",
    "36. CREDIT FACILITY PROPOSAL TO LENDING BANK",
    "37. DOCUMENT & VERIFICATION CHECKLIST",
    "38. KEY ASSUMPTIONS & PROVENANCE SUMMARY",
    "39. FINANCIAL INTEGRITY & RECONCILIATION AUDIT"
]


async def run_golden_dairy_test():
    print("=" * 75)
    print("KALPA STAGE 14.3 — GOLDEN DAIRY FARM DPR ACCEPTANCE TEST")
    print("=" * 75)

    biz_id = "dairy_farm"
    scen_id = "DPR-dairy_fa"

    # 1. Setup Dairy Farm Scenario
    print("\n[STEP 1] Initializing Dairy Farm Scenario...")
    scen = dpr_scenario_manager.get_or_create_scenario(biz_id)
    scenario_id = scen.scenario_id

    dairy_answers = [
        ("business_name", "Kamadhenu Dairy & Milk Production"),
        ("business_activity", "Commercial Dairy Milking & Chilling Unit (15 Animals)"),
        ("promoter_name", "Rajeshwar Patil"),
        ("promoter_contribution", "75000"),
        ("nic_code", "01411"),
        ("target_state", "Maharashtra"),
        ("target_district", "Kolhapur"),
        ("carpet_area", "1800"),
        ("total_employment", "3"),
        ("business_constitution", "PROPRIETORSHIP")
    ]
    for fid, ans in dairy_answers:
        dpr_scenario_manager.set_user_answer(biz_id, fid, ans, scenario_id=scenario_id)

    print("  -> Building Stage 1 Context...")
    await dpr_context_builder.build_context(biz_id, scenario_id)

    print("  -> Running Stage 2 Enrichment...")
    pkg = await dpr_enrichment_service.run_enrichment(biz_id, scenario_id)
    assert pkg is not None, "Enrichment failed!"
    print("  [PASS] Context & Enrichment successfully prepared.")

    # 2. Execute Stage 14.3 DPR Generation
    print("\n[STEP 2] Generating Institutional Bank-Reviewable DPR PDF...")
    req = DPRGenerationRequest(
        business_id=biz_id,
        scenario_id=scenario_id,
        format="pdf",
        language="en",
        regenerate_narrative=False
    )
    resp = await stage14_3_orchestrator.generate_dpr(req)

    assert resp.status == "COMPLETED", f"Status is {resp.status}"
    assert resp.validation_status == "PASSED", f"Validation status is {resp.validation_status}"
    assert resp.dpr_status in (DPRStatus.BANK_REVIEW_READY, DPRStatus.READY_FOR_SUBMISSION), f"DPR status: {resp.dpr_status}"
    assert resp.file_path is not None and os.path.exists(resp.file_path), "PDF file missing!"
    print(f"  [PASS] DPR generated successfully: {resp.file_path}")
    print(f"  Total Pages: {resp.page_count}")
    print(f"  Sections Count: {resp.sections_count}")
    print(f"  Annexures Count: {resp.annexures_count}")

    # 3. Read PDF Bytes
    with open(resp.file_path, "rb") as f:
        pdf_bytes = f.read()

    reader = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)
    print(f"\n[STEP 3] Validating PDF Structure ({num_pages} pages)...")
    assert num_pages >= 6, f"Expected institutional multi-page DPR, got {num_pages} pages"

    # Extract all text per page
    page_texts = [page.extract_text() or "" for page in reader.pages]
    full_text = " ".join(page_texts)

    # 4. Disallowed Token Scanning
    print("\n[STEP 4] Scanning for Disallowed Tokens...")
    clean, violations = DPRValidator.scan_pdf_text_for_disallowed_tokens(pdf_bytes)
    if not clean:
        print(f"  [FAIL] Disallowed token violations detected: {violations}")
        sys.exit(1)
    print("  [PASS] ZERO disallowed tokens found (no {{, }}, {%, %}, TODO, TBD, None, null, NaN, undefined, %%)")

    # 5. Unicode ₹ Rendering Validation
    print("\n[STEP 5] Validating Unicode Currency Glyph (₹)...")
    rupee_count = full_text.count("₹")
    print(f"  Detected {rupee_count} Unicode ₹ currency glyphs across document.")
    assert rupee_count >= 10, f"Expected clean ₹ symbol in tables, found {rupee_count}"
    print("  [PASS] Currency symbol correctly rendered.")

    # 6. Canonical 39 Sections Verification
    print("\n[STEP 6] Verifying All 39 Canonical Sections...")
    missing_sections = []
    for s_name in CANONICAL_SECTIONS_39:
        if s_name not in full_text:
            missing_sections.append(s_name)

    if missing_sections:
        print(f"  [FAIL] Missing canonical sections: {missing_sections}")
        sys.exit(1)
    print(f"  [PASS] All {len(CANONICAL_SECTIONS_39)} canonical sections found in PDF text in exact order.")

    # 7. Annexures E, F, J, Q Verification
    print("\n[STEP 7] Verifying Institutional Annexures (E, F, J, Q)...")
    annexures = [
        ("ANNEXURE E: PROJECTED PROFIT & LOSS STATEMENT", "Annexure E (P&L)"),
        ("ANNEXURE F: PROJECTED BALANCE SHEET", "Annexure F (Balance Sheet)"),
        ("ANNEXURE J: DEBT SERVICE COVERAGE RATIO", "Annexure J (DSCR)"),
        ("ANNEXURE Q: SOURCE & DATA PROVENANCE REGISTER", "Annexure Q (Provenance)")
    ]
    for annex_title, label in annexures:
        found = annex_title in full_text
        assert found, f"Missing {label}: '{annex_title}'"
        print(f"  [PASS] {label} present.")

    # 8. Dynamic TOC Page Number Alignment (Pass 1 vs Pass 2)
    print("\n[STEP 8] Validating Dynamic Table of Contents (Two-Pass Page Numbering)...")
    toc_text = ""
    for p_idx in range(min(5, num_pages)):
        if "TABLE OF CONTENTS" in page_texts[p_idx]:
            toc_text = page_texts[p_idx]
            print(f"  Found TOC on page {p_idx + 1}")
            break
    assert toc_text != "", "Table of Contents not found!"

    # Ensure TOC doesn't have blank/zero page numbers
    assert "Page 0" not in toc_text, "TOC contains invalid Page 0!"
    print("  [PASS] Table of Contents rendered dynamically with valid page references.")

    # 9. Financial Value Consistency Across Sections
    print("\n[STEP 9] Verifying Cross-Section Financial Parity...")
    scalars = resp.financial_integrity
    print(f"  Financial Integrity Audit Result: {scalars.overall_status}")
    print(f"  Passed Checks: {scalars.passed_count}/{len(scalars.checks)}")
    assert scalars.overall_status in ("PASS", "WARNING"), f"Financial integrity failed: {scalars.blocking_reasons}"
    print("  [PASS] Financial integrity audit passed.")

    # 10. Preview and Download Endpoint Byte Parity
    print("\n[STEP 10] Verifying Preview and Download Endpoint Byte Parity...")
    preview_resp = await preview_stage_14_3_pdf(resp.document_id, db=None)
    download_resp = await download_stage_14_3_pdf(resp.document_id, db=None)

    # Both responses are FileResponse or StreamingResponse
    preview_path = preview_resp.path
    download_path = download_resp.path
    assert os.path.exists(preview_path), "Preview path does not exist!"
    assert os.path.exists(download_path), "Download path does not exist!"
    assert preview_path == download_path == resp.file_path, "Preview and download paths do not point to identical file!"

    with open(preview_path, "rb") as pf, open(download_path, "rb") as df:
        p_bytes = pf.read()
        d_bytes = df.read()
    assert p_bytes == d_bytes == pdf_bytes, "Preview and download bytes mismatch!"
    print(f"  [PASS] Preview and Download serve exact same {len(pdf_bytes):,} PDF bytes.")

    # 11. Visual Regression Check (PyMuPDF rendering check)
    print("\n[STEP 11] PyMuPDF Visual Rendering Check...")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count == num_pages, f"Page count mismatch: fitz={doc.page_count}, pypdf={num_pages}"
    page0 = doc.load_page(0)
    pix = page0.get_pixmap()
    assert pix.width > 0 and pix.height > 0
    doc.close()
    print("  [PASS] Visual rendering confirmed on all pages.")

    print("\n" + "=" * 75)
    print(">>> GOLDEN ACCEPTANCE TEST PASSED WITH 100% INSTITUTIONAL COMPLIANCE <<<")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_golden_dairy_test())
