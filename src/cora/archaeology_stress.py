"""Seeded 1M *model* mutations of archaeology triage invariants (not real Git histories)."""
from __future__ import annotations
from collections import Counter
import hashlib
from .mutations import mix64, MASK

FAMILIES = (
 'staged_scaffold', 'abandoned_feature', 'orphan_with_dynamic_loader',
 'test_only_gold', 'contract_only_gold', 'migration_retained', 'workflow_hidden',
 'renamed_implementation', 'copied_component', 'large_commit_artifact',
 'cross_product_cochange', 'same_product_cochange', 'plugin_loader',
 'generator_output', 'runtime_probe', 'external_consumer', 'build_only',
 'release_only', 'squashed_PR', 'missing_PR_map', 'truncated_history',
 'security_control', 'naming_mislead', 'unclassified_source',
)


def model_flags(bits:int) -> tuple[str,...]:
    """Candidate labels are non-destructive; model is deliberately small."""
    if type(bits) is not int or not 0<=bits<(1<<20): raise ValueError('invalid model risk mask')
    roles_protected = bool(bits & 1)
    static_inbound = bool(bits & 2)
    touched_more_than_once = bool(bits & 4)
    roles_known = bool(bits & 8)
    current_git_blob_observed = bool(bits & 16)
    history_complete = bool(bits & 32)
    boundary_known = bool(bits & 64)
    result=[]
    if roles_protected and not static_inbound:
        result.append('POSSIBLE_UNCONNECTED_GOLD_REVIEW')
    if not roles_known and not static_inbound and not touched_more_than_once:
        result.append('POSSIBLE_SCAFFOLD_WASTE_REVIEW')
    if not current_git_blob_observed or not history_complete or not boundary_known:
        result.append('EVIDENCE_COVERAGE_DEBT')
    return tuple(sorted(result))


def oracle_by_boolean_contract(bits:int) -> tuple[str,...]:
    """Independent truth table of published finite Boolean contract."""
    protected=(bits%2)==1
    inbound=((bits//2)%2)==1
    multiple=((bits//4)%2)==1
    classified=((bits//8)%2)==1
    resolved=((bits//16)%2)==1
    all_history=((bits//32)%2)==1
    owned=((bits//64)%2)==1
    return tuple(sorted((['POSSIBLE_UNCONNECTED_GOLD_REVIEW'] if protected and not inbound else []) +
                        (['POSSIBLE_SCAFFOLD_WASTE_REVIEW'] if not classified and not inbound and not multiple else []) +
                        (['EVIDENCE_COVERAGE_DEBT'] if not (resolved and all_history and owned) else [])))


def stress_archaeology(seed:int=883,cases:int=1_000_000)->dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=1_000_000:
        raise ValueError('seed integer and 1..1000000 cases required')
    counts=Counter()
    family_counts=Counter()
    digest=hashlib.sha256()
    errors=0
    observed_signatures=set()
    for i in range(cases):
        mask = i ^ (seed & ((1<<20)-1))
        family = FAMILIES[mix64((i+seed)&MASK) % len(FAMILIES)]
        actual = model_flags(mask)
        expected = oracle_by_boolean_contract(mask)
        if actual != expected:errors+=1
        if 'POSSIBLE_SCAFFOLD_WASTE_REVIEW' in actual and mask & 2:errors+=1
        if 'POSSIBLE_UNCONNECTED_GOLD_REVIEW' in actual and not mask & 1:errors+=1
        counts['+'.join(actual) or 'NO_SPECIAL_FLAG']+=1
        family_counts[family]+=1
        observed_signatures.add(actual)
        digest.update(i.to_bytes(4,'big')+mask.to_bytes(4,'big')+FAMILIES.index(family).to_bytes(1,'big')+
                      '|'.join(actual).encode('ascii')+b'\n')
    return {'schema':'cora-archaeology-stress/1','cases':cases,'seed':seed,
            'families':len(FAMILIES),'distinct_input_masks':cases,
            'distinct_semantic_output_signatures':len(observed_signatures),
            'mismatches':errors,'outcomes':dict(sorted(counts.items())),
            'distribution':dict(sorted(family_counts.items())),
            'stream_sha256':digest.hexdigest(),
            'limit':'Finite synthetic oracle; no inference of real dead code, no million Git repos or runtime executions.'}
