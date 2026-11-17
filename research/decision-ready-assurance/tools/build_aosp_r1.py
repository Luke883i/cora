#!/usr/bin/env python3
"""Deterministic author-scoped OOXML builder for the PR73 AOSP R1 CTO brief."""
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZipInfo, ZIP_STORED
import json,sys,math
R=Path(__file__).resolve().parents[1]
S=json.loads((R/'AOSP_R1_BRIEF_CONTENT.json').read_text(encoding='utf-8'))
NAVY='0B1F3A'; MUTED='536278'; AMBER='BA7E23'; LIGHT='F1F5F9'; TEAL='00766D'
def E(s): return escape(str(s),{'"':'&quot;'})
def run(t,size=18,bold=False,color=NAVY):
 return f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="{math.floor(size*1.16+0.5)}"/><w:color w:val="{color}"/>{"<w:b/>" if bold else ""}</w:rPr><w:t xml:space="preserve">{E(t)}</w:t></w:r>'
def p(t='',size=18,bold=False,color=NAVY,before=0,after=60,shade=None,keep=False):
 sh=(f'<w:shd w:val="clear" w:fill="{shade}"/>' if shade else '')
 return f'<w:p><w:pPr>{sh}<w:spacing w:before="{math.floor(before*1.13+0.5)}" w:after="{math.floor(after*1.10+0.5)}" w:line="262" w:lineRule="auto"/>{"<w:keepNext/>" if keep else ""}</w:pPr>{run(t,size,bold,color)}</w:p>'
def heading(t): return p(t,21,True,NAVY,145,68,keep=True)
def tc(t,width,head=False,alt=False):
 fill='DCE8F0' if head else ('F7FAFC' if alt else 'FFFFFF')
 return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:shd w:val="clear" w:fill="{fill}"/><w:tcMar><w:top w:w="75" w:type="dxa"/><w:left w:w="95" w:type="dxa"/><w:bottom w:w="75" w:type="dxa"/><w:right w:w="95" w:type="dxa"/></w:tcMar></w:tcPr>{p(t,16 if head else 16,head,NAVY if head else "283548",0,0)}</w:tc>'
def table(rows,widths,header=False):
 grid=''.join(f'<w:gridCol w:w="{v}"/>' for v in widths)
 body=''.join('<w:tr>'+ ('<w:trPr><w:tblHeader w:val="true"/></w:trPr>' if header and i==0 else '') + ''.join(tc(v,widths[j],head=(header and i==0),alt=i%2==0) for j,v in enumerate(row))+'</w:tr>' for i,row in enumerate(rows))
 return f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders><w:bottom w:val="single" w:sz="4" w:color="DDE5ED"/></w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>'
body=[]
body.extend([
 p('AOSP  /  CORA METHOD  /  R1 • 17 NOVEMBRE 2026',14,True,TEAL,0,95),
 p(S['title'],40,True,NAVY,0,90),
 p(S['subtitle'],20,False,MUTED,0,145),
 p('LA DISTINZIONE CHE CONTA',17,True,AMBER,0,45),
 p(S['takeaway'],18,False,NAVY,0,95,shade=LIGHT),
 p(S['definition'],17,False,MUTED,0,125),
 heading('Il metodo in sei passaggi, spiegato da zero'),
 table([['N.','Fase','Cosa cambia / come falsificare']]+[[a,b,c] for a,b,c in S['steps']],[630,2300,7200],header=True),
 heading('Ecosistema AOSP pubblico: funzioni diverse, confini autonomi'),
 table([['Dominio','Repository','Funzione e limite']]+[[a,b,c] for a,b,c in S['repo_groups']],[1930,2390,5810],header=True),
 p('I nove repository sono pubblici; l’appartenenza al programma non implica integrazione tecnica, certificazione o identica maturita.',15,False,MUTED,95,0)
])
body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
body.extend([
 p('AOSP  /  CASI REALI  /  EVIDENZE E LIMITI',14,True,TEAL,0,95),
 p('Quattro esempi: come si evita il falso PASS',34,True,NAVY,0,100),
 p('Ogni esempio e un caso documentato in un repository pubblico o nel dossier PR73. Sono oracoli e controesempi circoscritti, non una misura dell’efficacia commerciale di CORA.',17,False,MUTED,0,95),
])
for name,desc,src in S['examples']:
 body.append(heading(name))
 body.append(p(desc,18,False,NAVY,0,45))
 body.append(p('Fonte: '+src,15,False,MUTED,0,30))
body.extend([
 heading('Stato dell’arte scientifico congelato: PR73 / MS-10'),
 p(S['science'],17,False,NAVY,0,65,shade=LIGHT),
 heading('Cosa dovrebbe chiedere un CTO prima di adottarlo'),
 p(S['ctogate'],17,False,NAVY,0,75),
 p(S['status'],16,True,AMBER,0,50),
 p('FONTI E RIPRODUZIONE',14,True,TEAL,75,35),
 p(S['sources'],14,False,MUTED,0,0),
])
NS='xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
sect='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="760" w:right="760" w:bottom="760" w:left="760" w:header="400" w:footer="400"/></w:sectPr>'
doc=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document '+NS+'><w:body>'+''.join(body)+sect+'</w:body></w:document>').encode('utf-8')
parts={
'[Content_Types].xml':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>''',
'_rels/.rels':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>''',
'docProps/core.xml':'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>AOSP - CORA method and public repository evidence, R1</dc:title><dc:description>Author-scoped CTO briefing; not scientific, human or product qualification.</dc:description></cp:coreProperties>''',
'word/document.xml':doc
}
out=Path(sys.argv[1]) if len(sys.argv)>1 else R/'AOSP_R1_CTO_STANDALONE.docx'
out.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(out,'w',compression=ZIP_STORED) as z:
 for name,data in parts.items():
  info=ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.compress_type=ZIP_STORED; info.external_attr=0o600<<16
  z.writestr(info,data.encode('utf-8') if isinstance(data,str) else data)
print(out, out.stat().st_size)
