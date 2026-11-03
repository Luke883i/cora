"""Deterministic finite model falsifier; no claims about million real PRs."""
from __future__ import annotations

import hashlib
from collections import Counter
from .mutations import mix64, MASK

FAMILIES = ('clean_pr','untrusted_bootstrap','policy_replaced','policy_renamed',
            'workflow_changed','guard_changed','release_changed','source_change',
            'test_claim_forged','self_signed_receipt','base_rewritten','postmerge_drift',
            'deleted_policy','changed_path_overflow','untrusted_agent','no_runtime_coverage',
            'product_scope_change','codeowner_removed','new_release_workflow',
            'external_consumer_unknown','SARIF_unverified','independent_review_missing',
            'hotspot_increase','documentation_only')


def observed_policy(bits:int)->str:
    """Conservative policy priority; fabricated approvals are never evidence."""
    if type(bits) is not int or not 0<=bits<(1<<20):raise ValueError('invalid model input')
    missing_policy=bool(bits & 1)
    divergent_base=bool(bits & 2)
    change_over_budget=bool(bits & 4)
    bootstrap=bool(bits & 8)
    if missing_policy or divergent_base or change_over_budget:return 'BLOCKED'
    if bootstrap:return 'BOOTSTRAP_REVIEW_REQUIRED'
    return 'OBSERVED_REVIEW_REQUIRED'


def independent_truth_table(bits:int)->str:
    """Separate Boolean contract, no call to policy implementation."""
    conditions=[(bits//(2**i))%2 for i in range(4)]
    if any(conditions[:3]):return 'BLOCKED'
    if conditions[3]:return 'BOOTSTRAP_REVIEW_REQUIRED'
    return 'OBSERVED_REVIEW_REQUIRED'


def stress_continuous(*,seed:int=883,cases:int=1_000_000)->dict:
    if type(seed) is not int or type(cases) is not int or not 1<=cases<=1_000_000:
        raise ValueError('seed int and case count in 1..1M required')
    counts=Counter();family_counts=Counter();digest=hashlib.sha256();mismatches=0
    unique=set()
    for i in range(cases):
        bits=i ^ (seed & ((1<<20)-1))
        family=FAMILIES[mix64((i+seed)&MASK) % len(FAMILIES)]
        actual=observed_policy(bits)
        expected=independent_truth_table(bits)
        if actual!=expected:mismatches+=1
        counts[actual]+=1;family_counts[family]+=1
        unique.add(bits)
        digest.update(i.to_bytes(4,'big')+bits.to_bytes(4,'big')+FAMILIES.index(family).to_bytes(1,'big')+actual.encode('ascii')+b'\n')
    return {'schema':'cora-continuous-stress/1','cases':cases,'seed':seed,'families':len(FAMILIES),
            'distinct_input_masks':len(unique),'distinct_semantic_decisions':len(counts),
            'outcomes':dict(sorted(counts.items())),'distribution':dict(sorted(family_counts.items())),
            'mismatches':mismatches,'stream_sha256':digest.hexdigest(),
            'limit':'Finite synthetic Boolean policy, not real 1M PR reviews, builds, deployments or users'}
