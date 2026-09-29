import os
import fitz
import glob

def render_and_inspect_pdf(pdf_path, out_dir):
    print(f"\n=======================================================")
    print(f"INSPECTING & RENDERING: {pdf_path}")
    print(f"=======================================================")
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    print(f"Total Pages: {len(doc)}")

    has_broken_glyphs = False
    orphan_headings = []
    
    for pno, page in enumerate(doc):
        # Render to image
        pix = page.get_pixmap(dpi=150)
        img_path = os.path.join(out_dir, f"page_{pno+1:02d}.png")
        pix.save(img_path)

        text = page.get_text()
        
        # Check for broken glyphs
        if "■" in text or "□" in text:
            print(f"[ERROR] Broken glyph square found on page {pno+1}")
            has_broken_glyphs = True
            
        # Check for Rupee sign
        rupee_count = text.count("₹")
        
        # Check headings
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        headings = [l for l in lines if any(l.startswith(f"{n:02d}.") for n in range(1, 41)) or "ANNEXURE" in l]
        
        # Check if heading is at the very bottom of the page with no content following
        if lines:
            last_line = lines[-1]
            if any(last_line.startswith(f"{n:02d}.") for n in range(1, 41)):
                orphan_headings.append((pno+1, last_line))
                print(f"[WARNING] Potential orphan heading at bottom of page {pno+1}: {last_line}")
                
        print(f"Page {pno+1:02d} ({page.rect.width:.0f}x{page.rect.height:.0f}): ₹ count={rupee_count:2d} | Headings: {headings[:3]} | Lines: {len(lines)}")

    print(f"\n--- Summary for {pdf_path} ---")
    print(f"Total Pages: {len(doc)}")
    print(f"Broken glyph squares found: {has_broken_glyphs}")
    print(f"Orphan headings: {len(orphan_headings)}")
    print(f"All page PNGs saved to: {out_dir}")

if __name__ == "__main__":
    # Find latest generated PDF in /app/data/dpr_reports/
    pdfs = glob.glob("/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-*.pdf")
    if pdfs:
        latest_pdf = max(pdfs, key=os.path.getmtime)
        render_and_inspect_pdf(latest_pdf, "/app/data/test_renders/LATEST_GOLDEN")
