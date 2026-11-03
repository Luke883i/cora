"""One million reproducible *model* mutations of bounded debt triage policy.

These are not a million independent repositories, empirical false-positive rates,
or audited real software defects. Oracle is separate Boolean specification.
"""
from __future__ import annotations
import hashlib
from collections import Counter
from .mutations import mix64, MASK

FAMILIES = (
 'complex_function','nested_branch','high_churn','same_product_cochange',
 'cross_product_cochange','orphan_test_hint','stale_artifact_role',
 'missing_test_coverage','missing_runtime_coverage','external_sarif_warning',
 'external_sarif_error','truncated_history','undocumented_entrypoint',
 'mixed_build_manifest','lock_resolution_unknown','unsafe_release',
 'unsigned_attestation','protected_workflow','API_contract_change',
 'secrets_scanner_claim','dynamic_import','unknown_ownership',
 'candidate_retention','gold_not_imported',
)
# Five evidence axes are applicable in each context. Other bits are independent
# perturbations of environment and history; non-applicable axes cannot assert proof.
RELEVANT = tuple(tuple(sorted({0,1,2,3,4,(i%15)+5,((i+7)%15)+5})) for i in range(24))


def model_triage(mask:int,family:int)->tuple[str,str]:
    if type(family) is not int or type(mask) is not int or not 0<=family<24 or not 0<=mask<(1<<20):
        raise ValueError('invalid finite debt stress state')
    applicable=RELEVANT[family]
    active={i for i in applicable if mask & (1<<i)}
    if 0 in active or 1 in active:
        return ('DEBT_BLOCKED','NO_PRIORITY')
    if 2 in active:
        return ('HUMAN_REVIEW','P1_REVIEW')
    if 3 in active:
        return ('HUMAN_REVIEW','P2_INVESTIGATE')
    if 4 in active:
        return ('UNCALIBRATED_UNKNOWN','NO_PRIORITY')
    return ('MONITOR_ONLY','P3_MONITOR')


def oracle_spec(mask:int,family:int)->tuple[str,str]:
    """Independent from model_triage: sequential Boolean algebra contract."""
    a=sum(1<<i for i in RELEVANT[family])
    unsafe=((mask & a & 3)!=0)
    high=((mask & a & 4)!=0)
    medium=((mask & a & 8)!=0)
    uncert=((mask & a & 16)!=0)
    return (('DEBT_BLOCKED','NO_PRIORITY') if unsafe else
            ('HUMAN_REVIEW','P1_REVIEW') if high else
            ('HUMAN_REVIEW','P2_INVESTIGATE') if medium else
            ('UNCALIBRATED_UNKNOWN','NO_PRIORITY') if uncert else
            ('MONITOR_ONLY','P3_MONITOR'))


def stress_debt(seed:int=883,cases:int=1_000_000)->dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=1_000_000:
        raise ValueError('invalid seed/cases')
    counts=Counter(); families=Counter();semantics=set();digest=hashlib.sha256();mismatch=0
    for i in range(cases):
        bits=i ^ (seed & ((1<<20)-1))
        idx=mix64((i+seed)&MASK)%24
        label=model_triage(bits,idx)
        expected=oracle_spec(bits,idx)
        if label!=expected: mismatch+=1
        if (bits & 3) and label[0]=='MONITOR_ONLY':mismatch+=1
        counts[label[0]]+=1;families[FAMILIES[idx]]+=1
        semantics.add((idx,*label))
        digest.update(i.to_bytes(4,'big')+bits.to_bytes(4,'big')+idx.to_bytes(1,'big')+
                      (label[0]+'|'+label[1]).encode('ascii')+b'\0')
    return {'schema':'cora-debt-stress/1','seed':seed,'cases':cases,'families':len(FAMILIES),
            'distinct_input_masks':cases,'semantic_output_signatures':len(semantics),
            'mismatches':mismatch,'outcomes':dict(sorted(counts.items())),
            'distribution':dict(sorted(families.items())),
            'stream_sha256':digest.hexdigest(),
            'scope':'Finite seeded model vectors, not independent Git histories or real defects',
            'oracle':'independent_boolean_spec_not_empirical_truth'}
