#!/usr/bin/env python3
"""Replay 100 physical JSON source copies against an independent author-authored oracle.
Bounded editorial/epistemic consistency: NOT a human study, screenshot replay or runtime proof.
"""
import argparse,copy,hashlib,json,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
R=Path(__file__).resolve().parents[1]
load=lambda name:json.loads((R/name).read_text(encoding='utf-8'))
def at(x,path):
 v=x['pages'][path[0]]
 v=v[path[1]] if len(path)==2 else v['blocks'][path[1]][path[2]]
 for key in path[3:]:v=v[key]
 return v
def put(x,path,value):
 v=x['pages'][path[0]] if len(path)==2 else x['pages'][path[0]]['blocks'][path[1]]
 for key in path[1:-1] if len(path)==2 else path[2:-1]:v=v[key]
 v[path[-1]]=value
def problems(x,oracle):
 out=[]
 if x.get('schema')!=oracle['expected_source_schema']:out.append('SCHEMA')
 if len(x.get('pages',[]))!=oracle['expected_pages']:out.append('PAGES')
 for row in oracle['criteria']:
  v=at(x,row['path'])
  if not isinstance(v,str) or row['required'] not in v:out.append(row['id'])
 for row in oracle.get('semantic_forbidden',[]):
  if row['text'] in at(x,row['path']):out.append(row['family'])
 text=json.dumps(x,ensure_ascii=False)
 for needle,code in [('15 annotated screenshot','SCREENSHOTS'),('28 individually owned findings','SCREENSHOTS'),('11 purposively selected pull requests','SCIENTIFIC'),('70 were unobserved','SCIENTIFIC'),('independent authorizer','HUMAN'),('content-addressed blobs','COMPUTATION'),('no new class','COMPUTATION')]:
  if needle not in text:out.append(code)
 return sorted(set(out))
def check_docx(source):
 file=R/'ENGLISH_FIELD_GUIDE_R2.docx'
 data=file.read_bytes()
 sha=hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()
 err=[]
 if sha!='ffa99d46c315258f3dc7cb8067e039b7c3ce3741':err.append('DOCX_BLOB_SHA_DRIFT')
 with ZipFile(file) as z:
  err.append('DOCX_CORRUPT') if z.testzip() else None
  root=ET.fromstring(z.read('word/document.xml'))
  w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
  s=' '.join(t.text or '' for t in root.iter(w+'t'))
  if len(root.findall('.//'+w+'br[@'+w+'type="page"]'))!=3:err.append('PAGE_BREAKS')
  for page in source['pages']:
   if page['title'] not in s or page['deck'] not in s:err.append('DOCX_TITLE_OR_DECK')
   for b in page['blocks']:
    if b['type'] in ('p','h2','call','small') and b['text'] not in s:err.append('DOCX_TEXT_DRIFT')
  if len(root.findall('.//'+w+'tbl'))<7:err.append('DIAGRAMS_MISSING')
 return sorted(set(err)),sha
def main():
 x=load('BRIEF_SOURCE.json');o=load('ORACLE_SPEC.json');m=load('MUTATION_CATALOG_100.json')
 if problems(x,o):raise SystemExit('BASELINE_BAD:'+repr(problems(x,o)))
 if len(m['mutants'])!=100 or len(set(v['id'] for v in m['mutants']))!=100:raise SystemExit('CATALOG_NOT_100_DISTINCT')
 outcomes=[]
 with tempfile.TemporaryDirectory() as temp:
  for row in m['mutants']:
   target=Path(temp)/(row['id']+'.json')
   y=copy.deepcopy(x)
   current=at(y,row['selector'])
   if row['original_anchor'] not in current:raise AssertionError('MISSING_ANCHOR '+row['id'])
   put(y,row['selector'],current.replace(row['original_anchor'],row['mutation']))
   target.write_text(json.dumps(y,ensure_ascii=False),encoding='utf8')
   changed=json.loads(target.read_text(encoding='utf8'))
   errs=problems(changed,o)
   outcomes.append({'id':row['id'],'family':row['family'],'status':'KILLED' if errs else 'SURVIVED','detected':errs,'mutated_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 benign=[]
 for i in range(10):
  y=copy.deepcopy(x);y['audience']+=' '+str(i);y['pages'][0]['kicker']+=' '
  benign.append(not problems(y,o))
 word_errors,sha=check_docx(x)
 r={'schema':'cora-r2-local-replay/1','mutants':100,'detected':sum(z['status']=='KILLED' for z in outcomes),'survivors':[z['id'] for z in outcomes if z['status']!='KILLED'],'benign_controls':10,'benign_accepted':sum(benign),'document_errors':word_errors,'document_git_blob_sha':sha,'scope':'AUTHOR_SCOPED_NOT_PEER_REVIEW','outcomes':outcomes}
 a=argparse.ArgumentParser();a.add_argument('--out');args=a.parse_args()
 if args.out:Path(args.out).write_text(json.dumps(r,indent=2)+chr(10))
 print(json.dumps({k:v for k,v in r.items() if k!='outcomes'},indent=2))
 return 0 if r['detected']==100 and r['benign_accepted']==10 and not word_errors else 1
if __name__=='__main__':sys.exit(main())
