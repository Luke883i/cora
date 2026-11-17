"""Reproducible, author-defined publication checks for a five-page public field guide.
Checks exact original Git links and stated limits; not independent product validation.
"""
import io, json, re, zipfile, hashlib
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
DOC=ROOT/'From_Intent_to_Evidence.docx'
REGISTER=ROOT/'Original_Source_Register_149.json'
DEST=ROOT/'Editorial_Falsification_Report.json'
PROJECTS=['ICTC','Teddy','LUMEN','NILO','iKant_EDU','CORA','academics']
PHRASES=[
 'A claim is as strong as the observation that supports it',
 'not 149 independently repeated product tests',
 'All mandatory conditions must hold',
 'cannot approve itself',
 'not a running product',
 'does not mean that the live application was broken',
 'Unknown consumers are unresolved work',
 'not independently certify legal compliance',
 'cannot establish charm',
 'does not establish live institutional catalogue integration',
 'cannot prove successful admission',
 'does not establish superiority to a strong checklist',
 'cannot alone show that a method caused faster or better engineering',
]

def parts(content):
 with zipfile.ZipFile(io.BytesIO(content)) as z:
  return {k:z.read(k) for k in z.namelist()}

def rebuild(content, name, old, new):
 with zipfile.ZipFile(io.BytesIO(content)) as inp:
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w') as z:
   matched=False
   for info in inp.infolist():
    body=inp.read(info.filename)
    if info.filename==name:
     a=body.decode('utf-8')
     assert old in a,(name,old[:60])
     assert a.count(old)==1,(old,a.count(old))
     body=a.replace(old,new,1).encode('utf-8')
     matched=True
    z.writestr(info,body)
   assert matched
  return out.getvalue()

def evaluate(content,expected_links):
 d=Document(io.BytesIO(content))
 txt='\n'.join(p.text for p in d.paragraphs)+'\n'+'\n'.join(c.text for table in d.tables for row in table.rows for c in row.cells)
 headings=[p.text.strip() for p in d.paragraphs if p.style.name=='Heading 1']
 urls=[rel.target_ref for rel in d.part.rels.values() if rel.reltype.endswith('/hyperlink')]
 failures=[]
 if len(urls)!=40 or sorted(urls)!=sorted(expected_links):failures.append('ORIGINAL_GIT_LINK_IDENTITY')
 if len(set(urls))!=40:failures.append('DUPLICATE_SOURCE_LINK')
 if any(h not in headings for h in PROJECTS):failures.append('PROJECT_COVERAGE')
 for p in PHRASES:
  if p not in txt:failures.append('MATERIAL_CLAIM_MISSING:'+p)
 if re.search(r'\bR[1-9][0-9]*\b',txt):failures.append('DOCUMENT_VERSION_JARGON')
 if re.search(r'\b(PR|HEAD|DoD|A0)\b',txt):failures.append('OPERATIVE_SHORTHAND')
 for token in ['previous draft','earlier version of this guide','editorial review','revision history of this document']:
  if token in txt.lower():failures.append('SELF_HISTORY:'+token)
 if len(d.tables)!=2:failures.append('LAYOUT_TABLE_COUNT')
 for t in d.tables:
  if not t.rows[0]._tr.get_or_add_trPr().find(qn('w:tblHeader')) is not None:
   failures.append('TABLE_ACCESSIBILITY')
 return failures

def main():
 reg=json.loads(REGISTER.read_text())
 expected=[r['file_url'] for r in reg['records'] if r['featured_case_source']]
 assert reg['count']==149 and len(reg['records'])==149
 assert len(set((r['repository'],r['commit_sha'],r['file_path'],r['file_blob_sha']) for r in reg['records']))==149
 assert reg['source_identity_correction']['resolved_original_git_sha']=='80a1e71b98f63a9f5a30d4398eefaadea27ba39c'
 raw=DOC.read_bytes();errors=evaluate(raw,expected)
 assert not errors,errors
 base_xml=parts(raw)['word/document.xml'].decode()
 muts=[]; survivors=[]; digests=set()
 # 40 real changed hyperlink targets inside the OOXML package.
 for i,url in enumerate(expected):
  changed=url.replace('https://github.com/Luke883i/','https://github.com/fabricated/')
  sample=rebuild(raw,'word/_rels/document.xml.rels',url,changed)
  fail=evaluate(sample,expected)
  muts.append(('ORIGINAL_LINK_'+str(i+1),bool(fail),fail))
 # Seven changed user-visible project section names (not just metadata labels).
 for name in PROJECTS:
  needle='<w:t>'+name+'</w:t>'
  sample=rebuild(raw,'word/document.xml',needle,'<w:t>Unverified project</w:t>')
  fail=evaluate(sample,expected)
  muts.append(('PROJECT_HEADING_'+name,bool(fail),fail))
 # Thirteen changed material conclusions in a working Word copy.
 for i,p in enumerate(PHRASES):
  assert base_xml.count(p)==1,(p,base_xml.count(p))
  sample=rebuild(raw,'word/document.xml',p,'The evidence proves universal acceptance')
  fail=evaluate(sample,expected)
  muts.append(('CLAIM_INVERSION_'+str(i+1),bool(fail),fail))
  h=hashlib.sha1(sample).hexdigest()
  assert h not in digests
  digests.add(h)
 assert len(muts)==60
 # The 47 non-claim mutants also need distinct OOXML byte identities.
 for i,url in enumerate(expected):
  changed=url.replace('https://github.com/Luke883i/','https://github.com/fabricated/')
  digests.add(hashlib.sha1(rebuild(raw,'word/_rels/document.xml.rels',url,changed)).hexdigest())
 for name in PROJECTS:
  digests.add(hashlib.sha1(rebuild(raw,'word/document.xml','<w:t>'+name+'</w:t>','<w:t>Unverified project</w:t>')).hexdigest())
 assert len(digests)==60
 # Ten harmless author-metadata differences must remain accepted.
 benign=[]
 with zipfile.ZipFile(io.BytesIO(raw)) as z:core=z.read('docProps/core.xml').decode()
 # Alternate only untrusted metadata, not editorial text or original-source links.
 old='<dc:creator></dc:creator>' if '<dc:creator></dc:creator>' in core else None
 if old is None:
  import re
  m=re.search(r'<dc:creator[^>]*>.*?</dc:creator>',core)
  assert m is not None
  old=m.group(0)
 for i in range(10):
  replacement=f'<dc:creator>Unattributed local renderer {i}</dc:creator>'
  sample=rebuild(raw,'docProps/core.xml',old,replacement)
  benign.append(not evaluate(sample,expected))
 report={
  'schema':'standalone-field-guide-author-controlled-tests/1',
  'docx_sha256':hashlib.sha256(raw).hexdigest(),
  'register_sha256':hashlib.sha256(REGISTER.read_bytes()).hexdigest(),
  'docx_bytes':len(raw),
  'selected_source_records':149,
  'linked_original_source_files':40,
  'negative_physical_docx_copies':60,
  'negative_detected':sum(x[1] for x in muts),
  'negative_survived':[x[0] for x in muts if not x[1]],
  'distinct_negative_docx_digests':len(digests),
  'benign_metadata_controls':10,
  'benign_accepted':sum(benign),
  'author_oracle_scope':'LINKS_PROJECT_LABELS_AND_13_AUTHOR_SELECTED_CRITICAL_PHRASES',
  'not_claimed':['UNIVERSAL_COPY_SEMANTICS','NATIVE_RUNTIME_REEXECUTION','INDEPENDENT_HUMAN_USABILITY','CAUSAL_ADVANTAGE','GITHUB_HOST_APPROVAL'],
  'tests':[{'id':k,'caught':c,'finding':f[0] if f else None} for k,c,f in muts]
 }
 DEST.write_text(json.dumps(report,indent=2)+'\n')
 assert report['negative_detected']==60 and report['benign_accepted']==10
 print(json.dumps({k:v for k,v in report.items() if k!='tests'},indent=2))

if __name__=='__main__':main()
