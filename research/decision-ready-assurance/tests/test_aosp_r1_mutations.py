#!/usr/bin/env python3
"""Physical copied-file falsifiers; author-only, never a universal correctness claim."""
from pathlib import Path
import sys,shutil,tempfile,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from verify_aosp_r1 import problems,ROOT
FILES=['AOSP_R1_BRIEF_CONTENT.json','AOSP_R1_PUBLIC_SCOPE.json','AOSP_R1_SCIENCE_FREEZE.markdown','AOSP_R1_PROJECT_AND_DOD.markdown','AOSP_R1_CTO_STANDALONE.docx']
def mutate_json(p,fn):
 x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x,ensure_ascii=False))
variants=[
 ('private_repo','AOSP_R1_PUBLIC_SCOPE.json',lambda p:mutate_json(p,lambda x:x['repos'].append({'name':'synthetic_nonpublic_fixture','visibility':'private','url':'https://github.com/Luke883i/synthetic_nonpublic_fixture','branch':'main','head_sha':'0'*40,'readme_blob_sha':'0'*40}))),
 ('missing_repo','AOSP_R1_PUBLIC_SCOPE.json',lambda p:mutate_json(p,lambda x:x['repos'].pop())),
 ('wrong_visibility','AOSP_R1_PUBLIC_SCOPE.json',lambda p:mutate_json(p,lambda x:x['repos'][0].__setitem__('visibility','private'))),
 ('pin_lost','AOSP_R1_PUBLIC_SCOPE.json',lambda p:mutate_json(p,lambda x:x['repos'][0].__setitem__('head_sha','abc'))),
 ('shared_runtime','AOSP_R1_PUBLIC_SCOPE.json',lambda p:mutate_json(p,lambda x:x.__setitem__('relationship','SHARED_RUNTIME'))),
 ('missing_step','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x['steps'].pop())),
 ('invalid_denominator','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x.__setitem__('science',x['science'].replace('92 slot','99 slot')))),
 ('invented_win','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x.__setitem__('science',x['science'].replace('pari su 16/16','CORA vince 16/16')))),
 ('false_claim_70','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x.__setitem__('science',x['science'].replace('non 70 difetti','70 difetti')))),
 ('false_agent','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x['steps'][2].__setitem__(2,'CORA scrive e approva il prodotto'))),
 ('no_examples','AOSP_R1_BRIEF_CONTENT.json',lambda p:mutate_json(p,lambda x:x['examples'].pop())),
 ('freeze_lost','AOSP_R1_SCIENCE_FREEZE.markdown',lambda p:p.write_text(p.read_text().replace('70 unobserved','70 defects'))),
 ('external_gate_erased','AOSP_R1_PROJECT_AND_DOD.markdown',lambda p:p.write_text(p.read_text().replace('D8 Explicit external gates','D8 Fully certified'))),
 ('missing_docx','AOSP_R1_CTO_STANDALONE.docx',lambda p:p.unlink()),
 ('invalid_docx','AOSP_R1_CTO_STANDALONE.docx',lambda p:p.write_bytes(b'not a docx'))
]
with tempfile.TemporaryDirectory() as t:
 r=Path(t)
 for f in FILES:shutil.copy2(ROOT/f,r/f)
 assert not problems(r),'baseline failed: '+repr(problems(r))
 detected=[];survivors=[]
 for name,f,fn in variants:
  q=r/f;fn(q)
  (detected if problems(r) else survivors).append(name)
  shutil.copy2(ROOT/f,q)
 print(json.dumps({'mutants':len(variants),'detected':detected,'survivors':survivors,'pass':not survivors},indent=2))
 if survivors:sys.exit(1)
