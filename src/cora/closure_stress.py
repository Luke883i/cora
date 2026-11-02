"""Pre-seeded one-million model-mutation falsifier for closure decisions.

Twenty independently toggled evidence dimensions (2^20 possible vectors),
24 named contextual families, fixed rules external to policy implementation.
This does not simulate 1M physical repos or prove source analyzers complete.
"""
from __future__ import annotations
import hashlib
from .closure import decide
from .mutations import mix64, MASK

DOMAINS = (
    'git_blob', 'git_commit', 'file_provenance', 'product_identity',
    'product_membership', 'ownership_ambiguity', 'static_import', 'dynamic_import',
    'registry', 'build', 'deploy', 'runtime', 'external_consumer', 'data_migration',
    'retention', 'security', 'contract_tests', 'rollback', 'ci_workflow', 'supply_chain',
)
FAMILIES = (
    'binary_blob_mutated', 'git_commit_rebased', 'provenance_replayed', 'product_renamed',
    'boundary_moved', 'overlapping_roots', 'static_import_rewritten', 'dynamic_plugin_loader',
    'registry_shadowing', 'generated_build_input', 'deployment_override', 'dormant_runtime_flag',
    'cross_repository_consumer', 'pending_schema_migration', 'retention_hold', 'security_policy_drift',
    'test_contract_regression', 'rollback_failure', 'ci_dispatch_link', 'supply_chain_disagreement',
    'legacy_duplicate_with_unknowns', 'removed_entrypoint', 'workflow_rename', 'safe_delete_unsupported',
)
# Documented model constraints, independent of runtime/actual source graph.
RELEVANT = {
    'committed_blob': (0, 1, 2),
    'declared_product_membership': (0, 1, 2, 3, 4, 5),
    'declared_manifest_dependency': (0, 1, 2, 8, 19),
    'static_import_candidate': (0, 1, 2, 6, 7),
    'safe_deletion': tuple(range(20)),
}


def scenario(index: int, seed: int) -> tuple[str, list[dict], int, set[int]]:
    if index < 0 or index >= 1 << 20:
        raise ValueError('scenario index outside 20-bit unique vector space')
    # One-to-one 20-bit XOR permutation; every index yields a DISTINCT model state.
    mask = (index ^ (seed & ((1 << 20)-1)))
    family = FAMILIES[mix64((index + seed) & MASK) % len(FAMILIES)]
    claim = ('safe_deletion' if family == 'safe_delete_unsupported'
             else 'committed_blob' if family in FAMILIES[:3]
             else 'declared_product_membership' if family in FAMILIES[3:6]
             else 'static_import_candidate' if family in FAMILIES[6:8]
             else 'declared_manifest_dependency' if family in FAMILIES[8:10]
             else 'safe_deletion' if family in FAMILIES[10:20]
             else 'static_import_candidate')
    relevant = set(RELEVANT[claim])
    # Within each case select one family-specific, substantively meaningful counterexample.
    counterexample_at = FAMILIES.index(family) % 20
    obligations = []
    for i, domain in enumerate(DOMAINS):
        if i not in relevant:
            continue
        if claim == 'safe_deletion' and i in (7, 10, 11, 12, 14, 17):
            state = 'UNSUPPORTED'  # no route to unconditional deletion
        elif mask & (1 << i):
            state = 'COUNTEREXAMPLE' if i == counterexample_at else 'UNKNOWN'
        else:
            state = 'VERIFIED'
        obligations.append({'id':domain, 'state':state, 'evidence':f'fixture:{family}:{index:06x}:{domain}'})
    return family, obligations, mask, relevant


def oracle_by_bit_spec(family: str, mask: int, relevant: set[int]) -> str:
    """Independent boolean algebra oracle; does not call policy decision code."""
    counter = FAMILIES.index(family) % 20
    if counter in relevant and counter not in ((7,10,11,12,14,17) if (family in FAMILIES[10:20] or family == 'safe_delete_unsupported') else ()) and (mask >> counter) & 1:
        return 'REFUTED'
    if family in FAMILIES[10:20] or family == 'safe_delete_unsupported':
        return 'BLOCKED'
    for bit in relevant:
        if mask & (1 << bit):
            return 'BLOCKED'
    return 'PASS_SCOPED'


def stress_closure(*, seed: int = 883, cases: int = 1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or cases < 1 or cases > 1_000_000:
        raise ValueError('seed must be integer and cases in 1..1000000')
    stream = hashlib.sha256()
    totals = {'PASS_SCOPED':0, 'BLOCKED':0, 'REFUTED':0}
    families = {name:0 for name in FAMILIES}
    mismatches = 0
    unique = set()
    for i in range(cases):
        family, obligations, mask, relevant = scenario(i, seed)
        actual, blocking = decide(obligations)
        expected = oracle_by_bit_spec(family, mask, relevant)
        if actual != expected:
            mismatches += 1
        # Witness check: counterexample or unresolved ID must actually appear in the result.
        if actual == 'PASS_SCOPED' and blocking:
            mismatches += 1
        if actual == 'REFUTED' and any(o['id'] not in blocking for o in obligations if o['state'] == 'COUNTEREXAMPLE'):
            mismatches += 1
        if actual == 'BLOCKED' and any(o['id'] not in blocking for o in obligations if o['state'] in ('UNKNOWN','UNSUPPORTED')):
            mismatches += 1
        unique.add(mask)
        totals[actual] += 1
        families[family] += 1
        stream.update(i.to_bytes(4, 'big') + mask.to_bytes(4,'big') +
                      FAMILIES.index(family).to_bytes(1,'big') + actual.encode('ascii') +
                      b'\0' + ','.join(sorted(blocking)).encode('ascii') + b'\n')
    return {'schema':'cora-closure-stress/1', 'seed':seed, 'cases':cases,
            'families':len(FAMILIES), 'distinct_evidence_vectors':len(unique),
            'mismatches':mismatches, 'outcomes':totals, 'distribution':families,
            'stream_sha256':stream.hexdigest(),
            'scope':'20 evidence axes with bijective 20-bit preseeded vectors; synthetic contract scenarios, not 1M physical repositories',
            'oracle':'independent_bit_spec_decision_with_witness_validation'}
