"""Pre-seeded synthetic adversarial risk matrix for file triage (no physical repos)."""
from __future__ import annotations
import hashlib
from .file_lab import triage_features
from .mutations import mix64, MASK

FAMILIES = (
 'python_static_import','dynamic_module_loader','reflection_registry','external_api_consumer',
 'retention_hold','migration_only','plugin_entrypoint','test_fixture','ci_workflow',
 'deployment_template','runtime_feature_flag','historical_rollback','generated_code',
 'data_asset','cross_product_import','shared_library','symlink','submodule',
 'unparsed_language','unresolved_manifest','runtime_trace_positive','runtime_trace_missing',
 'orphaned_in_partial_graph','quarantine_proposal',
)


def stress_file_lab(*, seed: int = 883, cases: int = 1_000_000) -> dict:
    if type(seed) is not int or type(cases) is not int or not 1 <= cases <= 1_000_000:
        raise ValueError('seed and cases invalid')
    stream = hashlib.sha256()
    totals = {'RETAIN': 0, 'INVESTIGATE': 0}
    distinct = set()
    mismatches = 0
    for i in range(cases):
        mask = i ^ (seed & ((1 << 20)-1))  # bijection over 20 risk axes
        family = FAMILIES[mix64((i + seed) & MASK) % len(FAMILIES)]
        # Some categories are only runtime/import unknowns, never positive use.
        positives = (mask & 1) != 0, (mask >> 1) & 3, (mask & 8) != 0
        actual = triage_features(entrypoint=positives[0], inbound_count=positives[1],
                                 runtime_positive=positives[2])
        # Oracle separately derived from the binary contract, not from implementation.
        expected = 'INVESTIGATE' if (mask & 0b1111) == 0 else 'RETAIN'
        if actual != expected:
            mismatches += 1
        distinct.add(mask)
        totals[actual] += 1
        stream.update(i.to_bytes(4, 'big') + mask.to_bytes(4, 'big') +
                      FAMILIES.index(family).to_bytes(1,'big') + actual.encode('ascii') + b'\n')
    return {'schema':'cora-file-lab-stress/1','seed':seed,'cases':cases,
            'distinct_risk_vectors':len(distinct),'families':len(FAMILIES),
            'mismatches':mismatches,'outcomes':totals,'digest':stream.hexdigest(),
            'limits':['Synthetic policy states, not independent file analyses',
                      'Unknown dimensions cannot create safe-deletion permission',
                      'Confidence bands are not statistically calibrated']}
