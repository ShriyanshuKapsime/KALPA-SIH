import asyncio
import os
import sys
import fitz  # PyMuPDF to inspect pages and layout
from app.dpr.stage14_3.orchestrator import stage14_3_orchestrator, DPRGenerationRequest
from app.database import SessionLocal

async def main():
    db = SessionLocal()
    b_id = "biz_m6_test"
    s_id = "test_scen_01"
    
    # Test A: English
    req_a = DPRGenerationRequest(
        business_id=b_id,
        scenario_id=s_id,
        language="en",
        format="pdf",
        regenerate_narrative=False
    )
    print("Generating Test A (English)...")
    res_a = await stage14_3_orchestrator.generate_dpr(req_a, db=db)
    pdf_a_path = res_a.document_path
    print(f"Test A generated: {pdf_a_path}, status: {res_a.status}")

    # Inspect Test A with PyMuPDF
    doc_a = fitz.open(pdf_a_path)
    pages_a = len(doc_a)
    print(f"Test A total pages: {pages_a}")

    # Now let's test with a direct Indic promoter run
    from app.dpr.stage14_3.styles import wrap_indic_font, resolve_display_enum
    val_hi = "श्रेयांसु कुमार कपसी में।"
    wrapped_hi = resolve_display_enum(val_hi)
    print(f"Hindi promoter wrapped: {wrapped_hi}")

    for i in range(pages_a):
        page = doc_a[i]
        text = page.get_text()
        rect = page.rect
        # check for non-empty page
        print(f"Page {i+1}: text length = {len(text.strip())}, dimensions = {rect.width}x{rect.height}")
    
    doc_a.close()

if __name__ == "__main__":
    asyncio.run(main())
