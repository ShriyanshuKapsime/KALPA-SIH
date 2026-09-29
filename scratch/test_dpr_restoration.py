import os
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

font_path_reg = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
font_path_bold = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"

if os.path.exists(font_path_reg):
    pdfmetrics.registerFont(TTFont("NotoSansDevanagari", font_path_reg))
    pdfmetrics.registerFont(TTFont("NotoSansDevanagari-Bold", font_path_bold))
    print("Successfully registered NotoSansDevanagari")
else:
    print("Noto font path does not exist locally (may be in docker)")

styles = getSampleStyleSheet()
style_normal = ParagraphStyle(
    "TestNormal",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
)

text_en = "Promoter Name: Shriyanshu Kumar Kapsime"
text_hi = 'Promoter Name: <font name="NotoSansDevanagari">श्री रामकुमार शर्मा</font>'

doc = SimpleDocTemplate("test_output.pdf", pagesize=A4)
story = [
    Paragraph(text_en, style_normal),
    Spacer(1, 10),
    Paragraph(text_hi, style_normal),
]
try:
    doc.build(story)
    print("Build successful, size:", os.path.getsize("test_output.pdf"))
except Exception as e:
    print("Build failed:", e)
