"""Source-only, exact-Git checker of the R2 typed assurance profile.

This is a derived qualification tool under cora-release-verification, not a
new ontology owner, product-certification authority or target runtime runner.
Never executes target code, imports target modules, or invokes target tests.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
import subprocess
from pathlib import Path

PROFILE = 'cora.type-assurance-profile.json'
SCHEMA = 'cora-type-assurance-profile/1'
PLANES = frozenset('REPOSITORY SOFTWARE DEPLOYMENT RUNTIME PRODUCT GOVERNANCE EVIDENCE'.split())
QUALITY = frozenset('functional_suitability performance_efficiency compatibility interaction_capability reliability security maintainability flexibility safety'.split())
STRUCTURAL = frozenset('security reliability performance_efficiency maintainability'.split())
TYPES = frozenset('git-revision change-set artifact workflow documentation source-module dependency-graph contract-schema verification-oracle change-assurance build-artifact deployment-boundary runtime-instance runtime-receipt product-capability user-journey governance-owner policy-gate source-history evidence-claim'.split())
DURABILITY = frozenset('identity-epoch api-contract-compatibility state-integrity security-boundary failure-recovery deterministic-replay change-impact regression-negatives supply-chain-identity rollback-ability claim-truth authority-uniqueness'.split())
EXTRA_STANDARD = 'ISO_5055_2021'
HEX = re.compile(r'^[0-9a-f]{40}$')
IDENT = re.compile(r'^[a-z][a-z0-9-]{2,64}$')


def _git(repo: Path, *args: str) -> bytes:
    p = subprocess.run(['git', '-C', str(repo), *args], check=False,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if p.returncode:
        raise ValueError('GIT_UNAVAILABLE_OR_MISSING_OBJECT: ' + ' '.join(args[:2]))
    return p.stdout


def _read(repo: Path, sha: str, path: str) -> bytes:
    if not isinstance(path, str) or not path or path.startswith(('/', '-')) or '\\' in path or '\x00' in path or '..' in path.split('/'):
        raise ValueError('UNSAFE_SOURCE_PATH')
    return _git(repo, 'show', sha + ':' + path)


def _json(repo: Path, sha: str, path: str) -> dict:
    obj = json.loads(_read(repo, sha, path).decode('utf-8'))
    if not isinstance(obj, dict):
        raise ValueError('EXPECTED_JSON_OBJECT')
    return obj


def _unique(items: object, key: str) -> dict:
    if not isinstance(items, list):
        raise ValueError(key + '_LIST_REQUIRED')
    out = {}
    for row in items:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or row['id'] in out:
            raise ValueError(key + '_DUPLICATE_OR_INVALID_ID')
        out[row['id']] = row
    return out


def _strings(items: object) -> set[str]:
    if not isinstance(items, list) or any(not isinstance(x, str) for x in items) or len(set(items)) != len(items):
        raise ValueError('DUPLICATE_OR_INVALID_VECTOR')
    return set(items)


def validate(profile: dict, atlas: dict, ontology: dict, dod: dict, witness_read) -> dict:
    """Validate bounded *model completeness*, using an independent source reader.

    PASS below is only for this structural model, never for the product.
    """
    if not isinstance(profile, dict) or set(profile) != {
        'schema','authority','status','base','upstream','planes',
        'quality_characteristics','structural_quality_dimensions','standards',
        'types','durability_invariants','qualification','bounded_saturation'}:
        raise ValueError('PROFILE_SHAPE_INVALID')
    if (profile['schema'] != SCHEMA or profile['authority'] != 'NONE' or
        profile['status'] != 'DESIGN_SOURCE_CANDIDATE'):
        raise ValueError('AUTHORITY_OR_PROFILE_PROMOTED')
    if not isinstance(profile['base'],dict) or set(profile['base']) != {'repository','commit'} or profile['base']['repository'] != 'Luke883i/cora' or not isinstance(profile['base']['commit'],str) or not HEX.fullmatch(profile['base']['commit']):
        raise ValueError('BASE_IDENTITY_INVALID')
    if profile['upstream'] != {
        'method_atlas':'cora.method-atlas.json','ontology':'cora.ontology.json',
        'reticulum':'cora.method-synthesis-dod.json','artifact_roles':'cora.artifact-roles.json'}:
        raise ValueError('UPSTREAM_OWNER_CHANGED')
    if (_strings(profile['planes']) != PLANES or
        _strings(profile['quality_characteristics']) != QUALITY or
        _strings(profile['structural_quality_dimensions']) != STRUCTURAL):
        raise ValueError('QUALITY_OR_PLANE_UNIVERSE_INCOMPLETE')
    if not isinstance(atlas,dict) or atlas.get('schema') != 'cora-method-atlas/1' or atlas.get('authority') != 'NONE':
        raise ValueError('UPSTREAM_ATLAS_INVALID')
    methods = _unique(atlas.get('procedures'),'METHOD')
    refs = _strings(atlas.get('references'))
    standards = _unique(profile['standards'],'STANDARD')
    if set(standards) != refs | {EXTRA_STANDARD}:
        raise ValueError('STANDARD_REFERENCE_GAP')
    if any(not isinstance(x.get('url'),str) or not x['url'].startswith('https://') or x.get('scope') != 'METHOD_REFERENCE_NOT_COMPLIANCE' for x in standards.values()):
        raise ValueError('STANDARD_SCOPE_OR_URL_INVALID')
    if (ontology.get('schema') != 'cora-ontology/1' or
        not any(x.get('id')=='cora' for x in ontology.get('products',[])) or
        {x.get('id') for x in ontology.get('software',[])} != {'cora-engine','cora-release-verification'}):
        raise ValueError('PRODUCT_SOFTWARE_IDENTITY_MISMATCH')
    if dod.get('schema') != 'cora-method-synthesis-dod/1' or dod.get('authority') != 'NONE' or dod.get('external_status') != 'BLOCKED_EXTERNAL':
        raise ValueError('EXTERNAL_DOD_PROMOTED')
    gates = _unique(dod.get('nodes'),'GATE')
    if 'G_GOVERNED' not in gates or 'G_SOURCE' not in gates or gates['G_GOVERNED'].get('scope') != 'EXTERNAL':
        raise ValueError('EXTERNAL_GATE_MISSING')
    q = profile['qualification']
    if q != {'source':'SOURCE_CLASSIFICATION_ONLY','runtime':'BLOCKED_EXTERNAL',
             'review':'BLOCKED_EXTERNAL','host':'BLOCKED_EXTERNAL','product':'BLOCKED_EXTERNAL',
             'authorization':'NONE'}:
        raise ValueError('CLAIM_PROMOTED_WITHOUT_EXTERNAL_EVIDENCE')
    bound = profile['bounded_saturation']
    if (not isinstance(bound,dict) or set(bound) != {'interpretation','unsupported'} or
        bound['interpretation'] != 'DECLARED_20_TYPES_X_10_STANDARDS_X_9_QUALITY_AXES_AND_12_CODE_INVARIANTS_ONLY' or
        _strings(bound['unsupported']) != {'universal-type-completeness','ISO-conformance','dynamic-consumer-closure','execution-of-target-tests','real-deployment','independent-review'}):
        raise ValueError('BOUNDED_SATURATION_FALSE_CLAIM')
    types = _unique(profile['types'],'TYPE')
    if set(types) != TYPES:
        raise ValueError('TYPE_UNIVERSE_INCOMPLETE')
    if not all(IDENT.fullmatch(k) for k in types):
        raise ValueError('TYPE_ID_INVALID')
    used_methods,used_standards,used_quality,used_planes = set(),set(),set(),set()
    witnesses = {}
    for type_id,row in types.items():
        if set(row) != {'id','plane','existing_method','owner_source','owner_symbol','standards','quality','obligations','falsifier','status'}:
            raise ValueError('TYPE_ROW_SHAPE_INVALID: '+type_id)
        if row['plane'] not in PLANES or row['existing_method'] not in methods:
            raise ValueError('METHOD_OR_PLANE_MISSING: '+type_id)
        method = methods[row['existing_method']]
        if (row['owner_source'] != method.get('source') or
            not isinstance(row['owner_symbol'],str) or not row['owner_symbol'].isidentifier()):
            raise ValueError('OWNER_METHOD_CONFLICT: '+type_id)
        st = _strings(row['standards'])
        if not st or not st <= set(standards) or not set(method['standards']) <= st:
            raise ValueError('METHOD_STANDARD_MISMATCH: '+type_id)
        qq = _strings(row['quality'])
        if not qq or not qq <= QUALITY:
            raise ValueError('QUALITY_UNMAPPED: '+type_id)
        obligations = _strings(row['obligations'])
        if len(obligations) < 2 or not all(IDENT.fullmatch(x.replace('_','-')) for x in obligations):
            raise ValueError('OBLIGATIONS_INCOMPLETE: '+type_id)
        if (not isinstance(row['falsifier'],str) or len(row['falsifier']) < 16 or
            row['status'] != 'DECLARED_SOURCE_WITNESS_NOT_BEHAVIORAL_PROOF'):
            raise ValueError('FALSIFIER_ABSENT_OR_PROMOTED: '+type_id)
        path = row['owner_source']
        if path not in witnesses:
            data = witness_read(path)
            if not isinstance(data, bytes) or len(data) > 1024*1024:
                raise ValueError('SOURCE_WITNESS_INVALID: '+path)
            witnesses[path] = ast.parse(data.decode('utf-8'),filename=path)
        symbols = {node.name for node in ast.walk(witnesses[path])
                   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
        if row['owner_symbol'] not in symbols:
            raise ValueError('OWNER_SYMBOL_MISSING: '+type_id)
        used_methods.add(row['existing_method'])
        used_standards.update(st)
        used_quality.update(qq)
        used_planes.add(row['plane'])
    if (used_methods != set(methods) or used_standards != set(standards) or
        used_quality != QUALITY or used_planes != PLANES):
        raise ValueError('COVERAGE_INCOMPLETE')
    invariants = _unique(profile['durability_invariants'],'DURABILITY')
    if set(invariants) != DURABILITY:
        raise ValueError('CODE_DURABILITY_INCOMPLETE')
    for key,row in invariants.items():
        if set(row) != {'id','type','existing_method','negative_oracle','attestation','assurance'}:
            raise ValueError('INVARIANT_SHAPE_INVALID: '+key)
        if row['type'] not in types or row['existing_method'] != types[row['type']]['existing_method']:
            raise ValueError('INVARIANT_OWNER_MISMATCH: '+key)
        if (not isinstance(row['negative_oracle'],str) or len(row['negative_oracle']) < 14 or
            row['attestation'] != 'BLOCKED_EXTERNAL' or row['assurance'] != 'REQUIRES_REAL_TARGET_AND_REVIEW'):
            raise ValueError('INVARIANT_FALSE_PASS: '+key)
    return {'schema':'cora-type-assurance-verification/1','result':'PASS_SCOPED_STRUCTURAL_MODEL',
            'type_count':len(types),'plane_count':len(used_planes),
            'upstream_method_count':len(used_methods),'reference_count':len(used_standards),
            'quality_axis_count':len(used_quality),'code_durability_count':len(invariants),
            'source_witnesses':len(witnesses),'authorization':'NONE',
            'external':'BLOCKED_EXTERNAL','universal_completeness':'UNSUPPORTED'}


def verify_repo(repo: Path, revision: str = 'HEAD') -> dict:
    repo = Path(repo).resolve(strict=True)
    if not isinstance(revision,str) or not revision or revision.startswith('-') or '\x00' in revision:
        raise ValueError('INVALID_REVISION')
    sha = _git(repo,'rev-parse','--verify','--end-of-options',revision+'^{commit}').decode('ascii').strip()
    profile = _json(repo,sha,PROFILE)
    base = profile.get('base',{}).get('commit')
    if not isinstance(base,str) or not HEX.fullmatch(base):
        raise ValueError('BASE_INVALID')
    try:
        _git(repo,'merge-base','--is-ancestor',base,sha)
    except ValueError as e:
        raise ValueError('BASE_NOT_ANCESTOR') from e
    atlas = _json(repo,sha,'cora.method-atlas.json')
    ontology = _json(repo,sha,'cora.ontology.json')
    dod = _json(repo,sha,'cora.method-synthesis-dod.json')
    result = validate(profile,atlas,ontology,dod,lambda path:_read(repo,sha,path))
    result.update({'commit':sha,'profile_git_blob':_git(repo,'rev-parse',sha+':'+PROFILE).decode('ascii').strip(),
                   'method_atlas_git_blob':_git(repo,'rev-parse',sha+':cora.method-atlas.json').decode('ascii').strip(),
                   'baseline':base})
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description='Git-bound bounded type/standards/code durability audit')
    parser.add_argument('--repo',type=Path,default=Path('.'))
    parser.add_argument('--revision',default='HEAD')
    args=parser.parse_args()
    try:
        result=verify_repo(args.repo,args.revision)
    except (ValueError,UnicodeError,subprocess.SubprocessError,OSError,KeyError,TypeError,SyntaxError,json.JSONDecodeError) as e:
        print(json.dumps({'schema':'cora-type-assurance-verification/1','result':'REFUTED_SOURCE_MODEL',
                          'error':str(e),'authorization':'NONE'},sort_keys=True))
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
