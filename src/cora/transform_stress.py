"""One million unique prespecified transformation/guard risk-state mutations.

Tests a finite policy model, not one million actual Git checkouts or refactors.
"""
from __future__ import annotations
import hashlib
from .mutations import mix64, MASK

FAMILIES = (
 'docs_reference_rename','source_modified_after_plan','plan_digest_resigned',
 'untracked_consumer','binary_reference','symlink_target','protected_guard_edit',
 'overlapping_product_roots','cross_product_move','dynamic_import',
 'relative_import','test_command_failure','missing_approval','dirty_worktree',
 'destination_collision','unexpected_test_side_effect','external_consumer',
 'workflow_reference','test_coverage_gap','changed_build_input',
 'migration_retention','rollback_exception','unsupported_language','valid_docs_only',
)
BITS = (
 'dirty','missing_source','target_collision','symlink','non_utf8','binary_consumer',
 'protected_file','test_failed','approval_missing','digest_changed','untracked_consumer',
 'dynamic_import','cross_product','unknown_external','incomplete_scan','verification_side_effect',
 'unsafe_path','non_document','retention_hold','workflow_consumer',
)
HARD = frozenset(range(11)) | {12,15,16,17}
UNKNOWN = {11,13,14,18,19}
# Each family activates a different set of contractual hazards; the remaining
# bits still vary the 20-axis vector (e.g. irrelevant environment conditions).
FAMILY_BITS = (
 (0,1,2,5,8,9,14), (0,9,14,15), (8,9,15), (10,13,14),
 (4,5,14), (3,16,2), (6,8,9), (12,14,16),
 (12,16,2), (11,13,14), (11,12,14), (7,15,8),
 (8,9,0), (0,1,2), (2,3,16), (7,15,14),
 (10,13,14), (19,13,14), (7,14,19), (19,13,14),
 (18,13,14), (7,15,0), (11,13,14), (0,1,2,3,5,6,7,8,9),
)


def decision_mutated(mask: int, family: int | None = None) -> tuple[str,tuple[int,...]]:
    """Production candidate model: examine typed effects and return blockers."""
    if not isinstance(mask,int) or mask < 0 or mask >= 1 << 20:
        raise ValueError('invalid mutation mask')
    applicable = range(20) if family is None else FAMILY_BITS[family]
    defects = {i for i in applicable if mask & (1 << i)}
    if defects & HARD:
        return 'BLOCKED',tuple(sorted(defects & HARD))
    if defects & UNKNOWN:
        return 'UNKNOWN',tuple(sorted(defects & UNKNOWN))
    return 'CANDIDATE_SCOPED',()


def oracle_by_contract(mask: int, family: int | None = None) -> str:
    """Separate declarative bitmask policy compiled from documented DoD hazards."""
    active = ((1<<20)-1) if family is None else sum(1<<i for i in FAMILY_BITS[family])
    hard = sum(1 << i for i in sorted(HARD)) & active
    uncertainty = sum(1 << i for i in sorted(UNKNOWN)) & active
    if mask & hard:
        return 'BLOCKED'
    if mask & uncertainty:
        return 'UNKNOWN'
    return 'CANDIDATE_SCOPED'


def stress_transform(*,seed:int=883,cases:int=1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or not 1 <= cases <= 1_000_000:
        raise ValueError('invalid stress parameters')
    stream=hashlib.sha256()
    counts={'BLOCKED':0,'UNKNOWN':0,'CANDIDATE_SCOPED':0}
    family_counts={name:0 for name in FAMILIES}
    mismatch=0
    unique=set()
    for i in range(cases):
        state=(i ^ (seed & ((1 << 20)-1)))
        family=FAMILIES[mix64((i+seed)&MASK)%len(FAMILIES)]
        fam_index=FAMILIES.index(family)
        got,blockers=decision_mutated(state, fam_index)
        expected=oracle_by_contract(state, fam_index)
        if got != expected or (got=='CANDIDATE_SCOPED' and blockers):
            mismatch+=1
        if got=='BLOCKED' and not any(state&(1<<j) for j in blockers):
            mismatch+=1
        counts[got]+=1
        family_counts[family]+=1
        unique.add(state)
        stream.update(i.to_bytes(4,'little')+state.to_bytes(4,'little')+
                      FAMILIES.index(family).to_bytes(1,'little')+
                      got.encode('ascii')+b'\0')
    return {'schema':'cora-transform-stress/1','seed':seed,'cases':cases,
            'families':len(FAMILIES),'distinct_risk_vectors':len(unique),
            'mismatches':mismatch,'outcomes':counts,'distribution':family_counts,
            'stream_sha256':stream.hexdigest(),
            'scope':'finite synthetic policy vectors; no 1M real repos, no universal behavioral preservation',
            'oracle':'independently defined hard/unknown bitmask contract'}
