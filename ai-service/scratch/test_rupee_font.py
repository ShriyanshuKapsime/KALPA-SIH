import io
import fitz
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

buf = io.BytesIO()
doc = SimpleDocTemplate(buf, pagesize=A4)
style = ParagraphStyle('TestStyle', fontName='Helvetica', fontSize=9, leading=12)
style_bold = ParagraphStyle('TestStyleBold', fontName='Helvetica-Bold', fontSize=9, leading=12)

p1 = Paragraph('Total Project Cost: <font name="DejaVuSans">₹</font>7,90,000', style)
p2 = Paragraph('Term Loan: <font name="DejaVuSans-Bold">₹</font>6,71,500', style_bold)

t = Table([
    [Paragraph('Item', style_bold), Paragraph('Cost (<font name="DejaVuSans-Bold">₹</font>)', style_bold)],
    [Paragraph('Machinery', style), Paragraph('<font name="DejaVuSans">₹</font>5,50,000', style)]
])

doc.build([p1, p2, t])

doc_fitz = fitz.open(stream=buf.getvalue(), filetype='pdf')
print('Fitz text extracted:')
print(doc_fitz[0].get_text())
