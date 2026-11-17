#!/usr/bin/env python3
"""Read-only author-scoped semantic and DOCX integrity checks for PR73 AOSP R1."""
from pathlib import Path
import sys,json,re,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'academics','ROA','cora','ictc','iKant_EDU','teddy','NILO','lumen','juriscribe'}
N='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def problems(root=ROOT):
    errors=[]
    def check(ok,code):
        if not ok:errors.append(code)
    try:
        content=json.loads((root/'AOSP_R1_BRIEF_CONTENT.json').read_text('utf8'))
        scope=json.loads((root/'AOSP_R1_PUBLIC_SCOPE.json').read_text('utf8'))
        freeze=(root/'AOSP_R1_SCIENCE_FREEZE.markdown').read_text('utf8')
        dod=(root/'AOSP_R1_PROJECT_AND_DOD.markdown').read_text('utf8')
    except (FileNotFoundError,ValueError,KeyError) as e:return ['SOURCE_UNAVAILABLE:'+str(e)]
    check(content['schema']=='aosp-r1-brief/1','SCHEMA_CHANGED')
    check(scope['programme']=='AOSP / Augmented Ontological-Semantic Platforms','AOSP_IDENTITY')
    reps=scope['repos'];names=[x['name'] for x in reps]
    check(len(reps)==9 and set(names)==EXPECTED and len(names)==len(set(names)),'PUBLIC_SET_INCOMPLETE_OR_PRIVATE')
    check(all(x['visibility']=='public' and x['url']=='https://github.com/Luke883i/'+x['name'] and x['branch']=='main' for x in reps),'SCOPE_OR_AUTHORITY')
    check(all(re.fullmatch('[0-9a-f]{40}',x['head_sha']) and re.fullmatch('[0-9a-f]{40}',x['readme_blob_sha']) for x in reps),'PIN_MISSING')
    check(scope['relationship']=='THEMATIC_PROGRAMME_NOT_SHARED_RUNTIME','FALSE_RUNTIME_INTEGRATION')
    check(len(content['steps'])==6 and [x[0] for x in content['steps']]==['01','02','03','04','05','06'],'METHOD_SEQUENCE')
    all_steps=' '.join(' '.join(x) for x in content['steps']).lower()
    check(all(k in all_steps for k in ['and','autorizz','git','falsific','umana']),'METHOD_AUTHORITY_GATE')
    check(len(content['repo_groups'])==6 and len(content['examples'])==4,'EXAMPLE_OR_REPO_COVERAGE')
    check(all(n.lower() in (' '.join(str(x) for row in content['repo_groups'] for x in row)).lower() for n in EXPECTED),'PUBLIC_REPOS_NOT_IN_BRIEF')
    cs=content['science'].lower()
    check(all(k in cs for k in ['11 pr','92 slot','70 non','16/16','quarantaquattro','zero persone','nessuna superiorita']),'SCIENTIFIC_NUMBERS_OR_NULL_LOST')
    check('non 70 difetti' in cs and 'non un exploit' in content['examples'][0][1] and 'non equivale' in content['examples'][1][1],'COUNTEREXAMPLE_LIMIT_LOST')
    check('cora non scrive' in all_steps,'CORA_AGENT_CONFUSION')
    check('non piattaforma unica' in content['definition'] and 'non' in content['status'].lower(),'FALSE_INTEGRATION_OR_ADOPTION')
    check(all(k in freeze for k in ['6695923c1689bc440fa26969d32eb32356c8df76','4ed58534022345e58d17207ab472a306d06d2925','70 unobserved','16/16','zero participants','44 author-modeled']),'FREEZE_CLAIM_BUDGET')
    check('D8 Explicit external gates' in dod and 'R1 stop' in dod,'DOD_EXTERNAL_LOST')
    file=root/'AOSP_R1_CTO_STANDALONE.docx'
    if not file.is_file():return errors+['DOCX_MISSING']
    try:
        with zipfile.ZipFile(file) as z:
            check(z.testzip() is None,'DOCX_CORRUPTED')
            d=ET.fromstring(z.read('word/document.xml'))
            txt=' '.join((t.text or '') for t in d.iter('{%s}t'%N))
            count=len(d.findall('.//{%s}br[@{%s}type="page"]'%(N,N)))
            check(count==1,'DOCX_PAGE_BREAK_COUNT')
            check('AOSP' in txt and 'CTO' in txt and 'PR73' in txt,'DOCX_STANDALONE_SCOPE')
            check(all(s in txt for s in [content['title'],content['definition'],content['science'],content['ctogate']]),'DOCX_SOURCE_DIVERGENCE')
            check(all(row[0] in txt and row[1] in txt for row in content['examples']),'DOCX_EXAMPLE_LOSS')
    except (zipfile.BadZipFile,KeyError,ET.ParseError) as e:errors.append('DOCX_INVALID:'+str(e))
    return errors
if __name__=='__main__':
    e=problems()
    print(json.dumps({'status':'PASS_AUTHOR_SCOPED' if not e else 'FAIL','issues':e,'rendered_pages':'VERIFY_VISUALLY_SEPARATE','external_human_understanding':'NOT_MEASURED','independent_review':'NOT_DONE'},indent=2))
    sys.exit(bool(e))
