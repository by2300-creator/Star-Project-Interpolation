"""Export the complete Markdown report, with full-page landscape figures."""
from pathlib import Path
import re
from html import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, Image, PageBreak, NextPageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DEST=ROOT/'output/pdf/P001-P010_combined_analysis_20261023.pdf'
DEST.parent.mkdir(parents=True,exist_ok=True)
FONT=Path('/Users/yangbolin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')
for name,file in [('Body','DejaVuSans.ttf'),('BodyBold','DejaVuSans-Bold.ttf'),('BodyItalic','DejaVuSans-Oblique.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
NAVY=colors.HexColor('#18364b');TEAL=colors.HexColor('#236c78')
styles={
    'body':ParagraphStyle('body',fontName='Body',fontSize=9.8,leading=14.2,spaceAfter=7),
    'title':ParagraphStyle('title',fontName='BodyBold',fontSize=21,leading=27,textColor=NAVY,spaceAfter=13),
    'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=13,leading=17,textColor=NAVY,spaceBefore=14,spaceAfter=8,keepWithNext=True),
    'h3':ParagraphStyle('h3',fontName='BodyBold',fontSize=10.5,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=6,keepWithNext=True),
    'cell':ParagraphStyle('cell',fontName='Body',fontSize=8,leading=11),
    'head':ParagraphStyle('head',fontName='BodyBold',fontSize=8,leading=11,textColor=colors.white),
    'figure_ref':ParagraphStyle('figure_ref',fontName='BodyItalic',fontSize=9.1,leading=13,textColor=TEAL,spaceAfter=9),
    'bullet':ParagraphStyle('bullet',fontName='Body',fontSize=9.4,leading=13.5,leftIndent=12,firstLineIndent=-9,spaceAfter=4),
}
def normalize(s):
    return s.translate(str.maketrans({'–':'-','—':'-','−':'-','‑':'-'}))
def inline(s):
    s=escape(normalize(s))
    s=re.sub(r'`([^`]+)`',r'<font size="8.6">\1</font>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    def link(m):
        dest=(HERE/m.group(2)).resolve().as_uri()
        return '<link href="'+escape(dest,quote=True)+'" color="#236c78">'+m.group(1)+'</link>'
    return re.sub(r'\[([^]]+)\]\(([^)]+)\)',link,s)

W,H=A4; LW,LH=landscape(A4); M=44
def page(c,doc):
    w,h=c._pagesize
    c.saveState();c.setStrokeColor(colors.HexColor('#cad5dc'));c.setLineWidth(.5)
    c.line(M,h-31,w-M,h-31)
    c.setFont('Body',8);c.setFillColor(NAVY)
    c.drawString(M,h-23,'INTERPOLATION STUDY  /  P001-P010')
    c.drawRightString(w-M,h-23,'23 October 2026')
    c.setFillColor(colors.HexColor('#647783'))
    c.drawString(M,23,'Controlled v9 sessions | October 5 recordings excluded')
    c.drawRightString(w-M,23,str(doc.page))
    c.restoreState()
doc=BaseDocTemplate(str(DEST),pagesize=A4,leftMargin=M,rightMargin=M,topMargin=46,bottomMargin=42,
    title='P001-P010: Combined analysis of the controlled experiment',author='Interpolation study')
doc.addPageTemplates([
    PageTemplate(id='portrait',frames=[Frame(M,42,W-2*M,H-88,id='text',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page,pagesize=A4),
    PageTemplate(id='figure',frames=[Frame(M,42,LW-2*M,LH-88,id='chart',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page,pagesize=landscape(A4)),
])
lines=(HERE/'REPORT.md').read_text().splitlines(); story=[];figures=[];i=0
while i<len(lines):
    s=lines[i].strip()
    if not s:i+=1;continue
    im=re.fullmatch(r'!\[([^]]+)\]\(([^)]+)\)',s)
    if im:
        num=len(figures)+1;figures.append((im.group(1),HERE/im.group(2)))
        story.append(Paragraph(f'<link href="#figure{num}" color="#236c78">Figure {num}. {escape(im.group(1))} - see full-page figures at the end.</link>',styles['figure_ref']))
        i+=1;continue
    if s.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in cells):rows.append(cells)
            i+=1
        n=len(rows[0]); width=W-2*M
        ratios={4:[.38,.20,.23,.19],5:[.30,.17,.18,.17,.18],6:[.14,.16,.08,.09,.20,.33]}.get(n,[1/n]*n)
        data=[[Paragraph(inline(x),styles['head' if j==0 else 'cell']) for x in row] for j,row in enumerate(rows)]
        table=Table(data,colWidths=[r*width for r in ratios],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f5f7'),colors.white]),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#c6d1d9'))]))
        story.extend([table,Spacer(1,10)]);continue
    if s.startswith('# '):story.append(Paragraph(inline(s[2:]),styles['title']))
    elif s.startswith('## '):story.append(Paragraph(inline(s[3:]),styles['h2']))
    elif s.startswith('### '):story.append(Paragraph(inline(s[4:]),styles['h3']))
    elif s.startswith('- '):story.append(Paragraph('• '+inline(s[2:]),styles['bullet']))
    else:
        buf=[s]
        while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#','|','- ','![')):
            i+=1;buf.append(lines[i].strip())
        story.append(Paragraph(inline(' '.join(buf)),styles['body']))
    i+=1
story.extend([NextPageTemplate('figure'),PageBreak()])
for k,(caption,path) in enumerate(figures,1):
    if k>1:story.append(PageBreak())
    story.append(Paragraph(f'<a name="figure{k}"/>Figure {k}. {escape(caption)}',styles['h2']))
    with PILImage.open(path) as im:iw,ih=im.size
    scale=min((LW-2*M)/iw,(LH-142)/ih)
    story.append(Image(str(path),width=iw*scale,height=ih*scale))
doc.build(story)
r=PdfReader(DEST)
text='\n'.join(p.extract_text() or '' for p in r.pages)
assert len(figures)==5
assert all(x in text for x in ['769567376','3490816988','3,080','191 / 200','P008','Outputs and reproducibility'])
print(DEST)
print('Pages:',len(r.pages),'Figures:',len(figures),'Bytes:',DEST.stat().st_size)
for n,p in enumerate(r.pages,1):print(n,len(p.extract_text() or ''),tuple(round(float(x)) for x in p.mediabox[2:]))
