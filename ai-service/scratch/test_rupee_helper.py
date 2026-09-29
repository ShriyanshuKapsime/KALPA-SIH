import re
import fitz
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansDevanagari', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansDevanagari-Bold', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf'))

def clean_text_for_flowable(text, bold=False):
    if text is None:
        return ""
    s = str(text)
    
    # 1. Clean duplicated units/suffixes
    s = re.sub(r'(\d+(?:\.\d+)?)\s*%\s*(?:percent|pct|Utilization%|Capacity%)', r'\1%', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+)\s*Months?\s*months?', r'\1 Months', s, flags=re.IGNORECASE)
    s = re.sub(r'%\s*%', '%', s)
    s = s.replace("Utilization%", "Utilization").replace("Capacity%", "Capacity")
    
    # 2. Wrap Rupee sign
    r_font = "DejaVuSans-Bold" if bold else "DejaVuSans"
    s = s.replace("₹", f'<font name="{r_font}">₹</font>')
    
    # 3. Check for Indic script characters (excluding ₹ which is 0x20B9)
    indic_chars = [c for c in s if ord(c) > 127 and c != '₹' and ord(c) != 0x20B9]
    if indic_chars:
        # Wrap any Devanagari sequences
        d_font = "NotoSansDevanagari-Bold" if bold else "NotoSansDevanagari"
        def _replace_indic(m):
            return f'<font name="{d_font}">{m.group(0)}</font>'
        s = re.sub(r'[\u0900-\u097F]+', _replace_indic, s)
        
    return s

buf = io.BytesIO()
doc = SimpleDocTemplate(buf, pagesize=A4)
base_styles = getSampleStyleSheet()
style = ParagraphStyle('Cell', parent=base_styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
style_bold = ParagraphStyle('CellB', parent=base_styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10)

p1 = Paragraph(clean_text_for_flowable("Total Project Cost: ₹7,90,000 (100.0%)", bold=False), style)
p2 = Paragraph(clean_text_for_flowable("Promoter Name: श्रेयांसु कुमार कपसी में।", bold=True), style_bold)
p3 = Paragraph(clean_text_for_flowable("Break-Even Utilization: 28.1% percent (Cash Break-Even: 32.5% Utilization%)", bold=False), style)
p4 = Paragraph(clean_text_for_flowable("Repayment Tenure: 84 Months months (Moratorium: 6 Months months)", bold=False), style)

t = Table([
    [Paragraph(clean_text_for_flowable("Cost Component", bold=True), style_bold), Paragraph(clean_text_for_flowable("Amount (₹)", bold=True), style_bold)],
    [Paragraph(clean_text_for_flowable("Plant & Machinery Outlay", bold=False), style), Paragraph(clean_text_for_flowable("₹6,50,000", bold=False), style)],
    [Paragraph(clean_text_for_flowable("Promoter (श्रेयांसु कुमार)", bold=False), style), Paragraph(clean_text_for_flowable("₹79,000", bold=False), style)],
])

doc.build([p1, p2, p3, p4, Spacer(1, 10), t])

doc_fitz = fitz.open(stream=buf.getvalue(), filetype='pdf')
print("--- Extracted text from PDF ---")
print(doc_fitz[0].get_text())
