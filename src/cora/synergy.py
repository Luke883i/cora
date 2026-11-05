"""Five synergic CORA assurances, source-bound and non-authoritative.

Source analysis only until an explicitly authorized probe or provider is supplied.
The original integrated_service, method_synthesis, continuous and reticulum own
their existing decisions; this module composes them, never replaces them.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

from .git_snapshot import git
from .reticulum import ordered_cut

DOD_SCHEMA = 'cora-five-synergies-dod/1'
TRUTH_SCHEMA = 'cora-semantic-truth/1'
EXPECTED_EDGES = {
    'T_GIT': [], 'T_CLAIM': [], 'T_SYMBOL': [], 'T_TEST': [],
    'A_PROMPT': [], 'A_GROUNDED': [], 'A_COUNTER': [], 'A_PROVIDER_OPTIN': [],
    'B_PROBE': [], 'B_NEGATIVE': [], 'B_SCOPE': [],
    'C_DIFF': [], 'C_IMPACT': [], 'C_POLICY': [],
    'U_JOIN': [], 'U_REPLAY': [], 'U_STRESS': [], 'U_AUTHORITIES': [],
    'G_TRUTH': ['T_GIT', 'T_CLAIM', 'T_SYMBOL', 'T_TEST'],
    'G_AI': ['G_TRUTH', 'A_PROMPT', 'A_GROUNDED', 'A_COUNTER', 'A_PROVIDER_OPTIN'],
    'G_BEHAVIOR': ['B_PROBE', 'B_NEGATIVE', 'B_SCOPE'],
    'G_EVOLUTION': ['C_DIFF', 'C_IMPACT', 'C_POLICY'],
    'G_UNIFIED': ['G_TRUTH','G_AI','G_BEHAVIOR','G_EVOLUTION',
                  'U_JOIN','U_REPLAY','U_STRESS','U_AUTHORITIES'],
    'E_REAL_PROVIDER': [], 'E_ALL_FEATURES': [], 'E_INDEPENDENT_REVIEW': [],
    'E_TARGET_RUNTIME': [], 'E_HOST': [],
    'G_GOVERNED': ['G_UNIFIED','E_REAL_PROVIDER','E_ALL_FEATURES',
                   'E_INDEPENDENT_REVIEW','E_TARGET_RUNTIME','E_HOST'],
}


def five_dod(repo: Path, commit: str) -> dict:
    source = git(Path(repo), 'show', commit + ':cora.five-synergies-dod.json',
                 max_output=128 * 1024)
    contract = json.loads(source.decode('utf-8'))
    if (set(contract) != {
        'schema','authority','source_goal','accepted_goal','external_status',
        'interpretation','nodes'
    } or contract['schema'] != DOD_SCHEMA or contract['authority'] != 'NONE'
        or contract['source_goal'] != 'G_UNIFIED'
        or contract['accepted_goal'] != 'G_GOVERNED'
        or contract['external_status'] != 'BLOCKED_EXTERNAL'
        or contract['interpretation'] != 'BOUNDED_SOURCE_ASSURANCE_NOT_PRODUCT_CERTIFICATION'):
        raise ValueError('five-goal contract authority or schema changed')
    nodes = contract['nodes']
    if not isinstance(nodes,list) or len(nodes) != len(EXPECTED_EDGES):
        raise ValueError('incomplete five-goal reticulum')
    found = {}
    for row in nodes:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str):
            raise ValueError('invalid reticulum row')
        if row['id'] in found:
            raise ValueError('duplicated reticulum node')
        found[row['id']] = row
    if set(found) != set(EXPECTED_EDGES):
        raise ValueError('missing or invented reticulum node')
    for ident, deps in EXPECTED_EDGES.items():
        actual=found[ident]
        scope = 'EXTERNAL' if ident.startswith('E_') or ident == 'G_GOVERNED' else 'SOURCE'
        if set(actual) != {'id','depends_on','scope'} or actual['depends_on'] != deps or actual['scope'] != scope:
            raise ValueError('removed dependency or false promotion: '+ident)
    if len(ordered_cut(nodes,'G_GOVERNED')) != len(EXPECTED_EDGES):
        raise ValueError('incomplete governed AND cut')
    return {'schema':DOD_SCHEMA,'source_goal':'G_UNIFIED',
            'governed_goal':'G_GOVERNED','nodes':len(nodes),
            'source_model':'CANDIDATE_NOT_COMPLETE',
            'governed_status':'BLOCKED_EXTERNAL','authorization':'NONE'}


def _python_witness(repo: Path, sha: str, path: str, *, is_test: bool) -> dict:
    """Observe original Git Python syntax; no imported target code is executed."""
    if not path.endswith('.py'):
        return {'path':path,'status':'NON_PYTHON_WITNESS_NOT_EXECUTED','symbols':[]}
    raw=git(repo,'show',sha+':'+path,max_output=512*1024)
    syntax=ast.parse(raw.decode('utf-8'),filename=path)
    symbols=sorted({node.name for node in ast.walk(syntax)
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
                    and (not is_test or node.name.startswith('test_'))})
    return {'path':path,'status':('TEST_SYMBOLS_OBSERVED_NOT_RUN' if is_test
                                else 'PYTHON_DECLARATIONS_OBSERVED_NOT_CALLED'),
            'symbols':symbols[:24], 'symbol_count':len(symbols)}


def semantic_truth(repo: Path, integrated: dict) -> dict:
    """One-to-one canonical 18 README claims -> exact Git witnesses and test AST."""
    from .integrated_service import SCHEMA as ORIGINAL_CASE
    if not isinstance(integrated,dict) or integrated.get('schema') != ORIGINAL_CASE:
        raise ValueError('invalid original integrated case')
    repo=Path(repo).resolve(strict=True)
    sha=integrated['commit']
    rows=[];conflicts=[];unknown=[]
    for claim in integrated['claim_to_implementation']['claims']:
        references=claim['evidence']
        impl=[x['path'] for x in references if x['role']=='IMPLEMENTATION']
        tests=[x['path'] for x in references if x['role']=='TEST']
        if claim['status']=='SOURCE_GAP':
            status='SOURCE_CONTRADICTION'
        elif not impl or not tests:
            status='EVIDENCE_GAP'
        else:
            status='SOURCE_WITNESSES_ONLY'
        observed=[]
        if status != 'SOURCE_CONTRADICTION':
            for path in sorted(set(impl)):
                observed.append(_python_witness(repo,sha,path,is_test=False))
            for path in sorted(set(tests)):
                observed.append(_python_witness(repo,sha,path,is_test=True))
            if any(x['status']=='TEST_SYMBOLS_OBSERVED_NOT_RUN'
                   and x['symbol_count']==0 for x in observed):
                status='TEST_ORACLE_NOT_LOCATED'
        if status=='SOURCE_CONTRADICTION':
            conflicts.append(claim['id'])
        else:
            unknown.append(claim['id'])  # trace is never semantic entailment
        rows.append({'claim_id':claim['id'],'predicate':claim['predicate'],
                     'status':status,'implementation_paths':sorted(set(impl)),
                     'test_paths':sorted(set(tests)),'source_witnesses':observed,
                     'declared_falsifier':claim['falsifier'],
                     'semantic_entailment':'NOT_ATTESTED',
                     'runtime_behavior':'NOT_OBSERVED'})
    if len(rows)!=18 or len({x['claim_id'] for x in rows})!=18:
        raise ValueError('canonical README claims count or identity changed')
    return {'schema':TRUTH_SCHEMA,'commit':sha,'claims':rows,
            'source_contradictions':sorted(conflicts),
            'semantic_unknowns':sorted(unknown),
            'verified_semantic_claims':0,
            'qualification':'SOURCE_AST_OBSERVATION_NOT_BEHAVIORAL_PROOF',
            'authorization':'NONE'}


REASON_SCHEMA = 'cora-synergic-reasoner/1'


def reasoning_plan(integrated: dict, truth: dict) -> dict:
    """Bounded, source-free AI case. It asks, never asserts, semantic entailment."""
    from .integrated_service import ai_request
    if truth.get('commit') != integrated.get('commit'):
        raise ValueError('cross-revision AI source plan rejected')
    request=ai_request(integrated)
    cases=[]
    for row in truth['claims']:
        ref='claim:'+row['claim_id']
        if ref not in request['valid_source_refs']:
            raise ValueError('AI case missing canonical evidence reference')
        cases.append({'claim_ref':ref,'source_status':row['status'],
                      'question':'Can a behavior be disproved despite source-level claim and test witnesses?',
                      'negative_control':'Mutate declared README phrase or implementation and re-check from Git.',
                      'positive_control':'Keep source contract and test witness intact; require independent runtime proof.',
                      'semantic_entailment':'UNKNOWN'})
    return {'schema':REASON_SCHEMA,'source_commit':integrated['commit'],
            'case_digest':integrated['case_digest'],
            'request':request,'candidate_questions':cases,
            'source_bytes_embedded':False,'provider_invoked':False,
            'authority':'NONE'}


def import_ai_reasoning(integrated: dict, answer: dict) -> dict:
    """Constrain a model's claims to exact source refs; no LLM result is evidence."""
    from .integrated_service import _ai, ai_request
    allowed=set(ai_request(integrated)['valid_source_refs'])
    observed=_ai(answer,integrated['commit'],integrated['case_digest'],allowed)
    for item in observed:
        if set(item['support_refs']) & set(item['counter_refs']):
            raise ValueError('AI support and counterexample cannot be the same witness')
    return {'schema':'cora-synergic-ai-observation/1',
            'source_commit':integrated['commit'],
            'items':observed,'state':'UNTRUSTED_AI_HYPOTHESES_NOT_PROOF',
            'provider_identity':'UNATTESTED','approval':'NONE'}


def invoke_reasoner(integrated: dict, truth: dict, provider=None, *,
                    authorize: bool = False) -> dict:
    """Explicit caller-owned provider callback; never outbound network by default.

    A provider supplied by the caller may use a real model. The only material
    passed is a bounded, source-free request. Its return is always untrusted.
    """
    plan=reasoning_plan(integrated,truth)
    if provider is None:
        if authorize:
            raise ValueError('AI provider not connected')
        return {'schema':'cora-synergic-reasoner-invocation/1',
                'provider':'NOT_CONNECTED','plan':plan,
                'observations':[],'authority':'NONE'}
    if authorize is not True or not callable(provider):
        raise ValueError('explicit valid AI callback authorization required')
    output=provider(plan['request'])
    assessment=import_ai_reasoning(integrated,output)
    return {'schema':'cora-synergic-reasoner-invocation/1',
            'provider':'CALLBACK_CALLED_NOT_INDEPENDENTLY_ATTESTED',
            'plan':plan,'observations':assessment['items'],
            'authority':'NONE'}


BEHAVIOR_SCHEMA = 'cora-synergic-behavioral-proof/1'

def behavioral_proofs(repo: Path, integrated: dict, *, authorize: bool = False) -> dict:
    """Only safe, original CORA Git-source operations, never target test or runtime."""
    if not isinstance(integrated,dict) or integrated.get('schema')!='cora-integrated-case/1':
        raise ValueError('invalid original integrated source case')
    sha=integrated['commit']
    if authorize is not True:
        return {'schema':BEHAVIOR_SCHEMA,'commit':sha,
                'status':'NOT_RUN_REQUIRES_EXPLICIT_AUTHORIZATION','probes':[],
                'source_probes_passed':0,'all_71_behaviors_proven':False,
                'runtime_attested':False,'authorization':'NONE'}
    if integrated['ai_observations']:
        raise ValueError('unreplayed AI overlay cannot be promoted to behavioral proof')
    from .git_snapshot import snapshot
    from .evidence import validate_ledger, domain_hash
    from .method_synthesis import synthesize, verify_synthesis
    from .integrated_service import verify_integrated
    repo=Path(repo).resolve(strict=True)
    ledger=snapshot(repo,sha)
    validate_ledger(ledger)
    method=synthesize(repo,sha)
    verify_synthesis(repo,method)
    verify_integrated(repo,integrated)
    probes=[
        {'id':'git-ledger','receipt':ledger['ledger_digest'],
         'scope':'ORIGINAL_GIT_SOURCE_ONLY'},
        {'id':'method-synthesis-replay','receipt':method['receipt_digest'],
         'scope':'ORIGINAL_METHODS_SOURCE_ONLY'},
        {'id':'integrated-report-replay','receipt':integrated['report_digest'],
         'scope':'ORIGINAL_INTEGRATION_SOURCE_ONLY'},
    ]
    output={'schema':BEHAVIOR_SCHEMA,'commit':sha,
            'status':'OBSERVED_LOCAL_SOURCE_PROBES_NOT_RUNTIME',
            'probes':probes,'source_probes_passed':len(probes),
            'all_71_behaviors_proven':False,'runtime_attested':False,
            'authorization':'NONE'}
    output['receipt_digest']=domain_hash('CORA:five-behavior-probes:1',output)
    return output

def verify_behavioral_proofs(repo: Path, report: dict) -> bool:
    if not isinstance(report,dict) or report.get('schema')!=BEHAVIOR_SCHEMA or report.get('status')!='OBSERVED_LOCAL_SOURCE_PROBES_NOT_RUNTIME':
        raise ValueError('invalid or unexecuted behavior receipt')
    from .integrated_service import integrated_case
    expected=behavioral_proofs(repo,integrated_case(repo,report['commit']),authorize=True)
    if report!=expected:
        raise ValueError('behavioral result forged or stale')
    return True


EVOLUTION_SCHEMA = 'cora-synergic-evolution/1'


def semantic_evolution(repo: Path, base: str, integrated: dict) -> dict:
    """Join BASE-policy lifecycle changes with original document/code links.

    A touched source is a potential documentation impact, never causality proof.
    Absence of a static relation is UNKNOWN, not proof of no consumers.
    """
    from .continuous import evaluate, verify_gate
    from .evidence import domain_hash
    if not isinstance(integrated,dict) or integrated.get('schema')!='cora-integrated-case/1':
        raise ValueError('invalid integrated source case')
    repo=Path(repo).resolve(strict=True)
    gate=evaluate(repo,base,integrated['commit'],phase='premerge')
    verify_gate(repo,gate)
    changed=sorted({p for row in gate['changed_paths']
                    for p in (row['old_path'],row['new_path'])})
    links={}
    for row in integrated['semantic_crosswalk']:
        links.setdefault(row['owner_source'],{'docs':set(),'claims':set()})
        links[row['owner_source']]['docs'].update(row['documentation_refs'])
        links[row['owner_source']]['claims'].update(row['claim_refs'])
    documented={x['path'] for x in integrated['documents']['docs']}
    impacts=[];unmapped=[]
    for path in changed:
        refs=links.get(path)
        doc_hits=set(refs['docs']) if refs else set()
        claimed=set(refs['claims']) if refs else set()
        for item in integrated['claim_to_implementation']['claims']:
            if any(e['path']==path for e in item['evidence']):
                claimed.add(item['id'])
        if path in documented:
            doc_hits.add(path)
        mapped=bool(doc_hits or claimed or refs)
        if not mapped:
            unmapped.append(path)
        impacts.append({'path':path,'affected_current_docs':sorted(doc_hits),
                        'affected_readme_claims':sorted(claimed),
                        'disposition':'REVIEW_DOC_AND_BEHAVIOR' if mapped else 'UNKNOWN_CONSUMER_OR_UNDOCUMENTED_CHANGE'})
    result={'schema':EVOLUTION_SCHEMA,'base_commit':gate['base_commit'],
            'head_commit':gate['head_commit'],
            'gate_receipt':gate['receipt_digest'],'gate_status':gate['status'],
            'policy_modified':gate['policy_modified'],
            'required_human_roles':gate['required_human_roles'],
            'changed_paths':changed,'impacts':impacts,
            'unmapped_changed_paths':sorted(unmapped),
            'behavioral_regression':'NOT_ATTESTED',
            'dynamic_consumers':'UNKNOWN',
            'authorization':'NONE'}
    result['receipt_digest']=domain_hash('CORA:synergy-evolution:1',result)
    return result


def verify_semantic_evolution(repo: Path, report: dict) -> bool:
    if not isinstance(report,dict) or report.get('schema')!=EVOLUTION_SCHEMA:
        raise ValueError('invalid semantic evolution receipt')
    from .integrated_service import integrated_case
    expected=semantic_evolution(repo,report['base_commit'],
                                integrated_case(repo,report['head_commit']))
    if report!=expected:
        raise ValueError('semantic evolution replay mismatch')
    return True
