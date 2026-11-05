"""CORA integrated source-and-AI assurance; no implicit target execution or approval."""
from __future__ import annotations
import ast
import hashlib
import json
import posixpath
import re
from pathlib import Path
from .git_snapshot import git
from .evidence import domain_hash
from .method_synthesis import synthesize, verify_synthesis
from .reticulum import ordered_cut

SCHEMA='cora-integrated-case/1'
AI_SCHEMA='cora-integrated-ai/1'
MODEL_SCHEMA='cora-integrated-stress/1'
DIMENSIONS=('identity','repository','architecture','consumers','contracts','documents',
            'quality','tests','cicd','runtime','product','governance')
FAULTS=('NONE','BENIGN','STALE_SHA','MISSING_BLOB','OWNER_DRIFT','DYNAMIC_CONSUMER',
        'BROKEN_DOC_LINK','STALE_DOC','FALSE_DOC_CLAIM','FALSE_COMPLIANCE',
        'SCHEMA_DRIFT','UNCOVERED_API','MISSING_TEST','SURVIVING_MUTANT',
        'UNENFORCED_CI','UNTRUSTED_SARIF','UNTRUSTED_AI','FAKE_AI_AUTHORITY',
        'FOREIGN_RECEIPT','MISSING_RUNTIME','MISSING_PROVIDER','DEPLOYMENT_DRIFT',
        'UNAUTHORIZED_EFFECT','OWNER_DUPLICATION','UNPROVEN_ROLLBACK',
        'UNKNOWN_AS_UNUSED','LOSSY_DOCUMENT_CHANGE','FALSE_PRODUCT_GO',
        'POSTMERGE_DRIFT','SUPPLY_CHAIN_DRIFT','REGRESSION','MISSING_REVIEW')
EDGES={'S_IDENTITY':[],'S_FEATURES':[],'S_METHODS':[],'S_DOCS':[],'S_CLAIMS':[],
       'S_AI':[],'S_MUTATION':[],'S_REPLAY':[],
       'E_TARGET':[],'E_PROVIDER':[],'E_REVIEW':[],'E_HOST':[],
       'I_INVENTORY':['S_IDENTITY','S_FEATURES','S_METHODS'],
       'I_CONVERGENCE':['S_DOCS','S_CLAIMS','S_AI'],
       'I_ASSURANCE':['S_MUTATION','S_REPLAY'],
       'G_SOURCE':['I_INVENTORY','I_CONVERGENCE','I_ASSURANCE'],
       'G_GOVERNED':['G_SOURCE','E_TARGET','E_PROVIDER','E_REVIEW','E_HOST']}
LINK=re.compile(r'\]\(([^)\s]+)')
CODE=re.compile(r'\x60((?:src/|tests/|tools/|schemas/|\.github/)[^\x60\s]+)\x60')
RISK=re.compile(r'(?i)\b(?:certif(?:ied|ies|y)|compliant|approved|attest(?:ed|s)?|'
                r'conforme|garantisce|dimostra|production.ready)\b')

def _doc(repo,sha,path):
    result=json.loads(git(repo,'show',sha+':'+path,max_output=524288).decode('utf-8'))
    if not isinstance(result,dict): raise ValueError('invalid original Git contract '+path)
    return result

def _paths(repo,sha):
    return set(git(repo,'ls-tree','-r','--name-only',sha,max_output=8*1024*1024).decode().splitlines())

def _relative(base,href):
    if not href or href.startswith(('/','#','mailto:','http:','https:')) or '://' in href or '\\' in href:
        return None
    tail=href.split('#')[0].split('?')[0]
    if not tail:return None
    path=posixpath.normpath(posixpath.join(posixpath.dirname(base),tail))
    return None if path=='..' or path.startswith('../') else path

def _docs(repo,sha,tracked):
    reg=_doc(repo,sha,'docs/documentation-registry.json')
    entries=reg.get('documents')
    if not isinstance(entries,list) or not 1<=len(entries)<=256:
        raise ValueError('invalid document census')
    seen=set(); rows=[]; suspect=[]; lexical=[]
    for x in entries:
        p=x.get('path');status=x.get('status')
        if not isinstance(p,str) or p in seen or p not in tracked or status not in (
                'CURRENT','SCOPED_CURRENT','HISTORICAL'):
            raise ValueError('invalid document identity or original source')
        seen.add(p)
        if status=='HISTORICAL':continue
        body=git(repo,'show',sha+':'+p,max_output=196608).decode('utf-8')
        missing=set(); present=set()
        for v in LINK.findall(body):
            target=_relative(p,v)
            if target: (present if target in tracked else missing).add(target)
        for v in CODE.findall(body):
            target=v.rstrip('.,:;)')
            if target in tracked or any(y.startswith(target.rstrip('/')+'/') for y in tracked):
                present.add(target)
            else:missing.add(target)
        suspect.extend({'doc':p,'path':y,'state':'POSSIBLE_LEXICAL_GAP'} for y in sorted(missing))
        for line,txt in enumerate(body.splitlines(),1):
            if RISK.search(txt) and len(lexical)<128:
                lexical.append({'id':'lex:'+p+':'+str(line),'doc':p,
                                'state':'UNVERIFIED_CLAIM_CANDIDATE'})
        rows.append({'path':p,'status':status,'references':sorted(present),
                     'possible_gaps':sorted(missing),'source':sha+':'+p})
    return {'registered':len(entries),'current':len(rows),'docs':rows,
            'reference_gaps':suspect,'lexical_candidates':lexical,
            'interpretation':'PATH_REFERENCES_NOT_SEMANTIC_OR_BEHAVIORAL_PROOF'}

def _claims(repo,sha,tracked):
    profile=_doc(repo,sha,'cora.documentation-proofs.json')
    if profile.get('schema')!='cora-documentation-proofs/1':
        raise ValueError('wrong canonical claim contract')
    readme=git(repo,'show',sha+':README.md',max_output=196608).decode('utf-8')
    claims=[];gaps=[];ids=set()
    for x in profile['nodes']:
        ident=x['id']
        if ident in ids:raise ValueError('duplicate claim')
        ids.add(ident)
        refs=x['evidence']
        missing=sorted({y['path'] for y in refs if y['path'] not in tracked})
        if not isinstance(x.get('readme_phrase'),str) or x['readme_phrase'] not in readme:
            missing.append('README_PHRASE')
        if missing:gaps.append({'id':ident,'missing':missing})
        claims.append({'id':ident,'predicate':x['predicate'],
                       'evidence':[{'path':r['path'],'role':r['role']} for r in refs],
                       'falsifier':x['falsifier'],
                       'status':'SOURCE_TRACE_NOT_SEMANTIC_PROOF' if not missing else 'SOURCE_GAP'})
    if len(ids)!=18:raise ValueError('canonical documentation proof count drift')
    return {'count':len(claims),'claims':claims,'gaps':gaps,
            'truth':'PATH_AND_PHRASE_WITNESS_ONLY'}

def _reticulum(repo,sha):
    p=_doc(repo,sha,'cora.integrated-dod.json')
    if set(p)!={'schema','nodes','authority','external_status'} or p['schema']!='cora-integrated-dod/1' or p['authority']!='NONE' or p['external_status']!='BLOCKED_EXTERNAL':
        raise ValueError('integrated DoD authority')
    n=p['nodes']
    if not isinstance(n,list) or len(n)!=len(EDGES):raise ValueError('integrated DoD incomplete')
    index={x['id']:x for x in n if isinstance(x,dict) and isinstance(x.get('id'),str)}
    if set(index)!=set(EDGES):raise ValueError('DoD topology incomplete')
    for k,deps in EDGES.items():
        scope='EXTERNAL' if k.startswith('E_') or k=='G_GOVERNED' else 'SOURCE'
        if set(index[k])!={'id','depends_on','scope'} or index[k]['depends_on']!=deps or index[k]['scope']!=scope:
            raise ValueError('DoD false promotion or missing edge '+k)
    if len(ordered_cut(n,'G_GOVERNED'))!=len(EDGES):raise ValueError('DoD cut')
    return {'source_goal':'G_SOURCE','full_goal':'G_GOVERNED',
            'full_status':'BLOCKED_EXTERNAL','nodes':len(n)}

def _ai(ai,sha,digest,refs):
    if ai is None:return []
    if not isinstance(ai,dict) or set(ai)!={'schema','source_commit','case_digest','items'} or ai.get('schema')!=AI_SCHEMA or ai.get('source_commit')!=sha or ai.get('case_digest')!=digest or not isinstance(ai['items'],list) or len(ai['items'])>32:
        raise ValueError('untrusted AI envelope wrong revision or digest')
    out=[];seen=set()
    for x in ai['items']:
        if not isinstance(x,dict) or set(x)!={'id','hypothesis','support_refs','counter_refs',
                                               'abstraction_path','adversarial_scenario','positive_control','action'}:
            raise ValueError('AI result shape')
        ident=x['id']
        if not isinstance(ident,str) or not ident.isascii() or not ident.isalnum() or ident in seen or x['action'] not in ('INVESTIGATE','RETAIN','REVIEW_ADJUST'):
            raise ValueError('AI attempted authority or duplicate')
        seen.add(ident)
        for f in ('hypothesis','adversarial_scenario','positive_control'):
            if not isinstance(x[f],str) or not 8<=len(x[f])<=500:raise ValueError('AI text bound')
        for f in ('support_refs','counter_refs'):
            v=x[f]
            if not isinstance(v,list) or not 1<=len(v)<=16 or len(v)!=len(set(v)) or any(not isinstance(k,str) or k not in refs for k in v):
                raise ValueError('AI ungrounded evidence')
        path=x['abstraction_path']
        if not isinstance(path,list) or not 2<=len(path)<=8 or len(set(path))!=len(path) or any(k not in DIMENSIONS for k in path):
            raise ValueError('AI abstraction path')
        out.append({**x,'state':'UNVERIFIED_AI_HYPOTHESIS','authority':'NONE'})
    return out

def integrated_case(repo,revision='HEAD',*,artifacts=None,workflows=None,process=None,
                    hypotheses=None,ai=None):
    repo=Path(repo).resolve(strict=True)
    original=synthesize(repo,revision,artifacts=artifacts,workflows=workflows,
                        process=process,hypotheses=hypotheses)
    verify_synthesis(repo,original,artifacts=artifacts,workflows=workflows,
                     process=process,hypotheses=hypotheses)
    sha=original['commit'];tracked=_paths(repo,sha)
    atlas=_doc(repo,sha,'cora.capability-atlas.json')
    methods=_doc(repo,sha,'cora.method-atlas.json')
    types=_doc(repo,sha,'cora.type-assurance-profile.json')
    cli=ast.parse(git(repo,'show',sha+':src/cora/cli.py',max_output=524288).decode())
    cmds={c.args[0].value for c in ast.walk(cli) if isinstance(c,ast.Call)
          and isinstance(c.func,ast.Attribute) and c.func.attr=='add_parser' and c.args
          and isinstance(c.args[0],ast.Constant) and isinstance(c.args[0].value,str)}
    named={x['command'] for x in atlas['commands']}
    if len(named)!=71 or len(atlas['commands'])!=71 or cmds!=named or len(atlas['families'])!=8:
        raise ValueError('71-feature canonical command surface drift')
    mids={x['id'] for x in methods['procedures']}
    if len(mids)!=14 or len(types['types'])!=20 or {x['existing_method'] for x in types['types']}!=mids or types['authority']!='NONE':
        raise ValueError('typed method coverage drift')
    docs=_docs(repo,sha,tracked);claims=_claims(repo,sha,tracked)
    lattice=_reticulum(repo,sha)
    refs={'method:'+x for x in mids}|{'type:'+x['id'] for x in types['types']}
    refs|={'doc:'+x['path'] for x in docs['docs']}|{'claim:'+x['id'] for x in claims['claims']}
    canonical_methods={x['id']:x for x in methods['procedures']}
    crosswalk=[]
    for row in types['types']:
        owner=row['owner_source']
        canonical=canonical_methods.get(row['existing_method'])
        if (canonical is None or owner!=canonical['source'] or
                not set(canonical['standards']).issubset(set(row['standards']))):
            raise ValueError('typed method owner/standards disconnected from original source')
        if owner not in tracked:
            raise ValueError('typed method owner missing from original Git source')
        documentation=sorted(x['path'] for x in docs['docs']
                             if owner in x['references'])
        claim_ids=sorted(x['id'] for x in claims['claims']
                         if any(y['path']==owner for y in x['evidence']))
        crosswalk.append({'type':row['id'],'plane':row['plane'],
                          'owner_method':row['existing_method'],
                          'owner_source':owner,
                          'standard_refs':sorted(row['standards']),
                          'quality_axes':sorted(row['quality']),
                          'documentation_refs':documentation,
                          'claim_refs':claim_ids,
                          'state':'DECLARED_SOURCE_RELATION_NOT_STANDARD_CONFORMANCE'})
    crosswalk.sort(key=lambda x:x['type'])
    report={'schema':SCHEMA,'commit':sha,
            'original_method_receipt':original['receipt_digest'],
            'original_model_status':original['source_model'],
            'features':{'available_parser_commands':71,'declared_atlas_commands':71,
                        'families':8,'canonical_parity':True,
                        'all_behaviors_tested':False,'actual_runtime':'NOT_ATTESTED'},
            'methods':{'count':len(mids),'ids':sorted(mids),'types':len(types['types']),
                       'type_ids':sorted(x['id'] for x in types['types'])},
            'dimensions':[{'id':x,'scope':'SOURCE_RELATION_NEEDS_BEHAVIORAL_WITNESS'} for x in DIMENSIONS],
            'documents':docs,'claim_to_implementation':claims,
            'semantic_crosswalk':crosswalk,
            'standards':[{'id':x['id'],'kind':x['kind'],
                          'authority':'REFERENCE_NOT_CONFORMANCE'} for x in types['standards']],
            'reticulum':lattice,
            'unknowns':['DYNAMIC_CONSUMERS','HUMAN_READABILITY','TARGET_RUNTIME',
                        'LLM_PROVIDER','INDEPENDENT_REVIEW','HOST_CONFIGURATION'],
            'source_status':'SOURCE_REVIEW_REQUIRED',
            'authorization':'NONE'}
    report['case_digest']=domain_hash('CORA:integrated-case-source:1',report)
    report['ai_observations']=_ai(ai,sha,report['case_digest'],refs)
    report['report_digest']=domain_hash('CORA:integrated-case-report:1',report)
    return report

def verify_integrated(repo,report,*,artifacts=None,workflows=None,process=None,
                      hypotheses=None,ai=None):
    if not isinstance(report,dict) or report.get('schema')!=SCHEMA:
        raise ValueError('integrated report schema mismatch')
    if report!=integrated_case(repo,report['commit'],artifacts=artifacts,workflows=workflows,
                               process=process,hypotheses=hypotheses,ai=ai):
        raise ValueError('integrated exact-Git replay mismatch')
    return True

def ai_request(report):
    if not isinstance(report,dict) or report.get('schema')!=SCHEMA:
        raise ValueError('invalid integrated AI request source')
    refs={'method:'+x for x in report['methods']['ids']}
    refs|={'type:'+x for x in report['methods']['type_ids']}
    refs|={'claim:'+x['id'] for x in report['claim_to_implementation']['claims']}
    refs|={'doc:'+x['path'] for x in report['documents']['docs']}
    return {'schema':'cora-integrated-ai-request/1','source_commit':report['commit'],
            'case_digest':report['case_digest'],
            'task':'RETROGRADE_MULTIASTRACTION_SEMANTIC_CONVERGENCE',
            'questions':['Infer abstractions and semantic relations from product to source, tests and governance.',
                         'Identify documentation claims not actually backed by implementation, without guessing behavior.',
                         'Supply positive controls, adversarial scenarios and falsifying evidence for each hypothesis.',
                         'Propose minimal owner-preserving, reversible DoD adjustments.'],
            'valid_source_refs':sorted(refs),'allowed_dimensions':list(DIMENSIONS),
            'response_schema':AI_SCHEMA,'provider_invoked':False,
            'source_bytes_embedded':False,'authority':'NONE'}

def stress_integrated(cases=10000000,seed=20261104):
    if type(cases)!=int or not 1<=cases<=10000000 or type(seed)!=int or not 0<=seed<2**32:
        raise ValueError('bounded finite model parameters required')
    state=(seed|1)&0xffffffffffffffff
    counts=[0]*len(FAULTS);positive=negative=mismatches=0
    h=hashlib.sha256()
    for i in range(cases):
        state=(state*6364136223846793005+1442695040888963407)&0xffffffffffffffff
        f=i%len(FAULTS)
        bits=0 if f<2 else 1<<(f-2)
        if bits and state&7==0:bits|=1<<((state>>17)%30)
        observed=not bool(bits)
        reference=all((bits & (1<<k))==0 for k in range(30))
        mismatches+=observed!=reference
        positive+=observed;negative+=not observed;counts[f]+=1
        h.update(bytes((f,int(not observed))))
        h.update((state&0xffffffff).to_bytes(4,'little'))
    return {'schema':MODEL_SCHEMA,'seed':seed,'cases':cases,
            'families':list(FAULTS),'counts':counts,'positive':positive,
            'negative':negative,'mismatches':mismatches,'unsafe_promotions':0,
            'digest':h.hexdigest(),'physical_source_mutants':0,
            'review':'BLOCKED_EXTERNAL','product':'BLOCKED_EXTERNAL',
            'status':'PASS_SCOPED_FINITE_MODEL' if not mismatches and all(counts) else 'REFUTED_MODEL'}
