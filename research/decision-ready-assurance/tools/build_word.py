#!/usr/bin/env python3
"""Build a Word 2-column research draft from the canonical markdown; requires python-docx."""
from pathlib import Path
from docx import Document
from docx.shared import Pt,Inches,RGBColor
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import argparse
ROOT=Path(__file__).resolve().parents[1]
def build(source,target):
 lines=source.read_text(encoding='utf-8').splitlines();d=Document();s=d.sections[0]
 s.page_width=Inches(8.5);s.page_height=Inches(11);s.left_margin=Inches(.66);s.right_margin=Inches(.66);s.top_margin=Inches(.65);s.bottom_margin=Inches(.63)
 norm=d.styles['Normal'];norm.font.name='Cambria';norm.font.size=Pt(8.75);norm.paragraph_format.space_after=Pt(5)
 for sty,sz in [('Title',18),('Heading 1',9.3)]:
  st=d.styles[sty];st.font.name='Calibri';st.font.size=Pt(sz);st.font.bold=True;st.font.color.rgb=RGBColor(11,31,58)
 p=d.add_paragraph(lines[0][2:],style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p=d.add_paragraph('Author-controlled design-science candidate · 16 November 2026');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 sec2=None;buf=[]
 def flush():
  if buf:d.add_paragraph(' '.join(buf));buf.clear()
 for line in lines[1:]:
  if line.startswith('## '):
   flush();h=line[3:]
   if h=='I. INTRODUCTION' and sec2 is None:
    sec2=d.add_section(WD_SECTION_START.CONTINUOUS)
    sec2.page_width=s.page_width;sec2.page_height=s.page_height
    for a in ['left_margin','right_margin','top_margin','bottom_margin']:setattr(sec2,a,getattr(s,a))
    cols=sec2._sectPr.xpath('./w:cols');c=cols[0] if cols else OxmlElement('w:cols');c.set(qn('w:num'),'2');c.set(qn('w:space'),'330')
    if not cols:sec2._sectPr.append(c)
   d.add_paragraph(h,style='Heading 1')
  elif not line.strip():flush()
  elif not line.startswith('# '):buf.append(line)
 flush();target.parent.mkdir(parents=True,exist_ok=True);d.save(target)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'MANUSCRIPT.markdown');p.add_argument('--out',type=Path,default=ROOT/'MANUSCRIPT_REGENERATED.docx');a=p.parse_args();build(a.source,a.out);print(a.out)
