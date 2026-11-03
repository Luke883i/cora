"""One-million distinct finite semantic mutations; independent Boolean oracle.

This tests a *specified abstraction*, not 1M Git repositories. The 20-bit
vector varies evidence in 24 scenario families. No result authorizes deletion.
"""
from __future__ import annotations

import hashlib
from .mutations import mix64, MASK

SCHEMA = 'cora-selection-stress/1'
AXES = (
    'blob_present', 'git_record_verified', 'immutable_commit', 'owner_declared',
    'ontology_parsed', 'graph_available', 'incoming_static_edge',
    'declared_entrypoint', 'protected_contract_role', 'positive_runtime_trace',
    'positive_external_consumer', 'cross_repo_dependency', 'dynamic_unknown',
    'build_unknown', 'deploy_unknown', 'registry_unknown', 'retention_unknown',
    'human_reviewer', 'independent_required_check', 'behavior_equivalence_claim',
)
FAMILIES = (
    'python_import', 'node_manifest', 'rust_workspace', 'go_module',
    'maven_property', 'dotnet_project', 'workflow_reusable', 'docker_build',
    'plugin_registry', 'reflection_dispatch', 'config_feature_flag',
    'external_consumer', 'test_fixture', 'contract_verifier', 'codegen_artifact',
    'migration_script', 'legal_hold', 'telemetry_sample', 'git_symlink',
    'git_submodule', 'untracked_consumer', 'package_entrypoint',
    'release_tool', 'apparently_orphaned_file',
)
# Each family focuses a material subset of evidence dimensions; all vectors
# remain distinct, but *semantic* distinctness is reported separately.
FAMILY_AXES = tuple(tuple(sorted({0,1,2,3,4,5,6,7,8,9,10,11,
                                12 + i%5, 12 + (i//5)%5,
                                17 + i%3})) for i in range(len(FAMILIES)))
PROTECTED = (6,7,8,9,10,11)
INTEGRITY = (0,1,2,3,4,5)
UNKNOWNS = (12,13,14,15,16)


def model_selection(flags: int, family: int) -> tuple[str, tuple[int,...]]:
    """Implementation model: positive evidence dominates, missing integrity blocks."""
    if type(flags) is not int or not 0 <= flags < (1<<20) or type(family) is not int or not 0 <= family < 24:
        raise ValueError('invalid scenario')
    relevant = FAMILY_AXES[family]
    present = set(j for j in relevant if flags & (1<<j))
    missing = [j for j in INTEGRITY if j in relevant and j not in present]
    positive = [j for j in PROTECTED if j in present]
    unknown = [j for j in UNKNOWNS if j in present]
    if missing:
        return 'DEBT_BLOCKED',tuple(sorted(missing))
    if positive:
        return 'RETAIN_EVIDENCED',tuple(sorted(positive))
    if unknown:
        return 'INVESTIGATE',tuple(sorted(unknown))
    return 'INVESTIGATE',tuple()


def oracle_bit_spec(flags: int, family: int) -> str:
    """Independent bit algebra, not calling model_selection or sharing branches."""
    axes = sum(1<<j for j in FAMILY_AXES[family])
    required = 63  # six integrity bits 0..5
    positive = sum(1<<j for j in PROTECTED)
    if flags & (axes & required) != required:
        return 'DEBT_BLOCKED'
    if flags & (axes & positive):
        return 'RETAIN_EVIDENCED'
    return 'INVESTIGATE'


def stress_selection(*, seed: int = 883, cases: int = 1_000_000) -> dict:
    """Seeded bijection: 1M unique vectors, zero destructive claims by design."""
    if type(seed) is not int or type(cases) is not int or not 1 <= cases <= 1_000_000:
        raise ValueError('seed must be int; cases in 1..1,000,000')
    stream = hashlib.sha256()
    outcomes = {x:0 for x in ('DEBT_BLOCKED','RETAIN_EVIDENCED','INVESTIGATE')}
    distribution = {x:0 for x in FAMILIES}
    mismatch = 0
    witnessed = set()
    signatures = set()
    for i in range(cases):
        flags = i ^ (seed & ((1<<20)-1))
        family = mix64((i+seed)&MASK) % len(FAMILIES)
        actual, witness = model_selection(flags,family)
        expected = oracle_bit_spec(flags,family)
        if actual != expected:
            mismatch += 1
        if actual == 'DEBT_BLOCKED' and not all(not(flags & (1<<j)) for j in witness):
            mismatch += 1
        if actual == 'RETAIN_EVIDENCED' and not all(flags & (1<<j) for j in witness):
            mismatch += 1
        outcomes[actual] += 1
        distribution[FAMILIES[family]] += 1
        witnessed.add(flags)
        # Normalized relevant-axes signature; visibly not all 1M scenarios are
        # independently distinct semantic states.
        applicable = sum(1<<j for j in FAMILY_AXES[family])
        signatures.add((family,flags & applicable))
        stream.update(i.to_bytes(4,'little') + flags.to_bytes(4,'little') +
                      family.to_bytes(1,'little') + actual.encode('ascii') + b'\0')
    return {
        'schema': SCHEMA, 'seed':seed, 'cases':cases, 'families':len(FAMILIES),
        'distinct_vectors':len(witnessed),
        'distinct_applicable_semantic_signatures':len(signatures),
        'mismatches':mismatch,
        'outcomes':outcomes,'distribution':distribution,'stream_sha256':stream.hexdigest(),
        'oracle':'independently_coded_finite_bit_spec_and_witness_checks',
        'claim_scope':'synthetic_model_only; no source completeness, real runtime, or universal deletion proof',
        'authorized_destructive_changes':0,
    }
