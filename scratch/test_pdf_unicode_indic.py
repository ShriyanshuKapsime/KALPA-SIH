import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

def test_multilingual_pdf():
    # Language fonts map
    fonts_map = {
        'hi': ('/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf'),
        'mr': ('/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf'),
        'kn': ('/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansKannada-Bold.ttf'),
        'ta': ('/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf'),
        'te': ('/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansTelugu-Bold.ttf'),
        'gu': ('/usr/share/fonts/truetype/noto/NotoSerifGujarati-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSerifGujarati-Bold.ttf'),
        'en': ('/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf'),
    }

    # Register each font family
    for lang, (reg_path, bold_path) in fonts_map.items():
        if os.path.exists(reg_path):
            pdfmetrics.registerFont(TTFont(f'Noto-{lang}', reg_path))
        if os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont(f'Noto-{lang}-Bold', bold_path))

    pdf_path = '/tmp/multilingual_dpr_test.pdf'
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    story = []

    samples = [
        ('en', 'Promoter / Entrepreneur Name: Rajesh Kumar Patil'),
        ('hi', 'प्रमोटर / उद्यमी का नाम: राजेश कुमार पाटिल'),
        ('mr', 'प्रमोटर / उद्योजक नाव: राजेश कुमार पाटील'),
        ('kn', 'ಮುಖ್ಯ ಉದ್ಯಮಿ / ಪ್ರವರ್ತಕರ ಹೆಸರು: ರಾಜೇಶ್ ಕುಮಾರ್ ಪಾಟೀಲ್'),
        ('ta', 'முதன்மை தொழில்முனைவோர் பெயர்: ராஜேஷ் குமார் பாட்டீல்'),
        ('te', 'ప్రధాన వ్యవస్థాపకుడు పేరు: రాజేష్ కుమార్ పాటిల్'),
        ('gu', 'મુખ્ય ઉદ્યોગસાહસિક / પ્રમોટરનું નામ: રાજેશ કુમાર પાટીલ'),
    ]

    for lang, text in samples:
        fname = f'Noto-{lang}' if f'Noto-{lang}' in pdfmetrics.getRegisteredFontNames() else 'Noto-hi'
        pstyle = ParagraphStyle(f'Style-{lang}', fontName=fname, fontSize=11, leading=15, textColor=colors.HexColor('#0F2942'))
        story.append(Paragraph(f"<b>[{lang.upper()}]</b>: {text}", pstyle))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"Generated PDF: {pdf_path} (size={os.path.getsize(pdf_path)} bytes)")

if __name__ == '__main__':
    test_multilingual_pdf()
