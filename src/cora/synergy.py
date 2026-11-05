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
