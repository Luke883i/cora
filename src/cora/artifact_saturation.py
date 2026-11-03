"""Deterministic, finite semantic novelty saturation for artifact-role governance.

The enumeration is intentionally finite and preseeded; saturation of its classes
is NOT saturation of all possible software architectures or attack techniques.
"""
from __future__ import annotations
import hashlib

FAMILIES = (
    'name_collision_test_source', 'schema_named_runtime', 'workflow_as_contract',
    'test_as_prod_dependency', 'dual_role_fixture', 'nested_owner',
    'orphan_static_edge', 'reflection_loader', 'runtime_plugin', 'external_consumer',
    'migrator_hold', 'retention_hold', 'generated_contract', 'release_verifier',
    'monorepo_shared', 'reexport_path', 'non_python_runtime', 'ci_dispatch',
    'registry_alias', 'instrumentation_gap', 'artifact_rename', 'archival_candidate',
    'quarantine_candidate', 'schema_change',
)
# 16 role subsets x 32 uncertainty subsets x 24 context families = 12,288 classes.
CLASSES = len(FAMILIES) * 16 * 32
ROLE_BITS = ('SOFTWARE_SOURCE', 'TEST', 'CONTRACT_VERIFIER', 'WORKFLOW')
UNCERTAINTIES = ('missing_import', 'dynamic_loader', 'external_consumer', 'runtime_gap', 'owner_conflict')


def policy(mask: int, issue: int) -> str:
    if not 0 <= mask < 16 or not 0 <= issue < 32:
        raise ValueError('invalid finite role/uncertainty vector')
    if mask & 0b1110:
        return 'PROTECTED_REVIEW_REQUIRED'
    if issue:
        return 'INVESTIGATE_UNKNOWN'
    return 'OBSERVE_ONLY'


def independent_oracle(mask: int, issue: int) -> str:
    # Written as a separate decision table; both implement the finite fixture spec.
    obligations = (mask // 2) != 0
    uncertainty = issue != 0
    return ('PROTECTED_REVIEW_REQUIRED' if obligations
            else 'INVESTIGATE_UNKNOWN' if uncertainty else 'OBSERVE_ONLY')


def saturate(*, seed: int = 883, minimum_cases: int = 1_000_000,
             no_novelty: int = 10_000_000) -> dict:
    if type(seed) is not int or type(minimum_cases) is not int or type(no_novelty) is not int:
        raise ValueError('integer parameters required')
    if not 1 <= minimum_cases <= 2_000_000 or not 1 <= no_novelty <= 10_000_000:
        raise ValueError('saturation bounds exceeded')
    # A finite exhaustive enumeration gives a conservative and reproducible M;
    # counts after M are independent of semantic novelty *within this ontology*.
    target = minimum_cases + no_novelty
    seen = bytearray(CLASSES)
    novelty = 0
    last_novelty = -1
    novelty_after_M = 0
    mismatches = 0
    counts = {'PROTECTED_REVIEW_REQUIRED':0,'INVESTIGATE_UNKNOWN':0,'OBSERVE_ONLY':0}
    digest = hashlib.sha256()
    for i in range(target):
        # Seed permutes position within each exhaustive cycle, without losing any class.
        v = (i + (seed % CLASSES)) % CLASSES
        fam = v // 512
        role = (v // 32) % 16
        unknown = v % 32
        if not seen[v]:
            seen[v] = 1
            novelty += 1
            last_novelty = i
            if i >= minimum_cases:
                novelty_after_M += 1
        actual = policy(role, unknown)
        expected = independent_oracle(role, unknown)
        if actual != expected:
            mismatches += 1
        counts[actual] += 1
        digest.update(v.to_bytes(2,'big') + bytes((len(actual),)))
    return {'schema':'cora-artifact-saturation/1', 'seed':seed,
            'minimum_cases_M':minimum_cases, 'no_novelty_after_M':no_novelty,
            'total_cases':target,'finite_semantic_classes':CLASSES,
            'semantic_classes_observed':novelty,'last_new_class_zero_based':last_novelty,
            'new_classes_after_M':novelty_after_M,
            'mismatches':mismatches,'outcomes':counts,
            'stream_sha256':digest.hexdigest(),
            'interpretation':'EXHAUSTIVE_ONLY_WITHIN_PREDECLARED_FINITE_ONTOLOGY',
            'limits':['Not 11M distinct semantic concepts or repositories',
                      'Only 12288 predefined role/uncertainty/context classes',
                      'No evidence of real runtime non-use, calibrated probabilities or safe deletion']}
