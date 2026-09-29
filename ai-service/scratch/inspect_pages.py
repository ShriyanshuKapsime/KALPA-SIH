import fitz

def inspect_pdf(pdf_path, label):
    print(f"\n--- INSPECTING {label}: {pdf_path} ---")
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        text = page.get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        headings = [l for l in lines if any(l.startswith(f"{n:02d}.") for n in range(1, 40)) or "ANNEXURE" in l]
        first_few = " | ".join(lines[:3]) if lines else "EMPTY"
        print(f"Page {i+1:02d}: Headings: {headings}  [Start: {first_few[:80]}]")

if __name__ == "__main__":
    inspect_pdf("/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-6CDF3F.pdf", "TEST_A_ENGLISH")
    inspect_pdf("/app/data/dpr_reports/KALPA-DPR-DAIRY_FA-11D6BF.pdf", "TEST_B_HINDI")
