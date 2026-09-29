import fitz

def detailed_inspect(pdf_path, label):
    print(f"\n=======================================================")
    print(f"DETAILED INSPECTION: {label} ({pdf_path})")
    print(f"=======================================================")
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    for i, page in enumerate(doc):
        text = page.get_text()
        rect = page.rect
        blocks = page.get_text("blocks")
        # blocks format: (x0, y0, x1, y1, text, block_no, block_type)
        print(f"\n--- Page {i+1} ({rect.width:.1f} x {rect.height:.1f} pt) [Blocks: {len(blocks)}] ---")
        for b in blocks:
            x0, y0, x1, y1, btext, bno, btype = b
            first_line = btext.strip().replace('\n', ' ')[:70]
            if first_line:
                print(f"  y=[{y0:5.1f} - {y1:5.1f}] : {first_line}")

if __name__ == "__main__":
    detailed_inspect("/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-6CDF3F.pdf", "TEST_A_ENGLISH")
    detailed_inspect("/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-11D6BF.pdf", "TEST_B_HINDI")
