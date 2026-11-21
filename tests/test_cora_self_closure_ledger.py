"""Static coverage and nonpromotion checks for the recursive source proposal.

Not a target runtime acceptance oracle, nor a duplicate CORA engine.
"""
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / '.cora/assurance/cora-self-closure-ledger.json'


def validate_ledger(x):
    failures = []
    if x.get('authority') != 'SOURCE_PROPOSAL_NO_INDEPENDENT_RUNTIME_OR_REVIEW_AUTHORITY':
        failures.append('missing-authority-boundary')
    if x.get('global_status') != 'NOT_ACCEPTED':
        failures.append('unsupported-global-acceptance')
    issues = x.get('issues', [])
    slices = x.get('slices', [])
    ids = [i.get('id') for i in issues]
    slice_ids = [s.get('slice_id') for s in slices]
    if len(ids) != 27 or len(set(ids)) != 27:
        failures.append('not-27-distinct-issues')
    if len(slice_ids) != 25 or len(set(slice_ids)) != 25:
        failures.append('not-25-distinct-slices')
    if len(x.get('heuristic_signals', [])) != 106:
        failures.append('heuristic-inventory-incomplete')
    if len(x.get('engine_debt_register', [])) != 8:
        failures.append('engine-debt-inventory-incomplete')
    covered = set()
    for s in slices:
        covered.update(s.get('problem_ids', []))
        leaves = s.get('AND_DoD', [])
        if {v.get('id') for v in leaves} != {'SOURCE','TARGET_RUNTIME','EXTERNAL'}:
            failures.append('missing-and-leaf:' + str(s.get('slice_id')))
        if any(v.get('status') not in {'NOT_RUN','BLOCKED_EXTERNAL','UNKNOWN','PASS_SCOPED_LOCAL'} for v in leaves) or any(v.get('id') == 'EXTERNAL' and v.get('status') == 'PASS_SCOPED_LOCAL' for v in leaves):
            failures.append('unsupported-positive-attestation:' + str(s.get('slice_id')))
        if not s.get('positive_oracles') or not s.get('negative_falsifiers') or not s.get('rollback'):
            failures.append('missing-oracle-or-rollback:' + str(s.get('slice_id')))
    if set(ids) != covered or any(i.get('primary_slice') not in slice_ids for i in issues):
        failures.append('coverage-gap')
    if any(i.get('resolution_status') not in {'PATCH_CANDIDATE_SOURCE_TESTED_NOT_INDEPENDENTLY_ACCEPTED','OPEN_NOT_ACCEPTED'} for i in issues):
        failures.append('unsupported-issue-resolution')
    if any(i.get('resolution_status') == 'PATCH_CANDIDATE_SOURCE_TESTED_NOT_INDEPENDENTLY_ACCEPTED' and i.get('primary_slice') not in ('C01','C02','C03','C04') for i in issues):
        failures.append('false-patch-status')
    return failures


class ClosureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = json.loads(LEDGER.read_text(encoding='utf-8'))

    def test_current_source_ledger_is_complete_but_not_accepted(self):
        self.assertEqual(validate_ledger(self.current), [])

    def test_counterexamples_fail_closed(self):
        mutations = [
            ('no-issue', lambda x: x['issues'].pop()),
            ('no-slice', lambda x: x['slices'].pop()),
            ('no-runtime-leaf', lambda x: x['slices'][0]['AND_DoD'].pop(1)),
            ('pretend-done', lambda x: x.update(global_status='PASS')),
            ('fake-external', lambda x: x['slices'][0]['AND_DoD'][2].update(status='PASS')),
            ('false-resolution', lambda x: x['issues'][-1].update(resolution_status='PASS')),
        ]
        for name, mutation in mutations:
            with self.subTest(name=name):
                copy_ = copy.deepcopy(self.current)
                mutation(copy_)
                self.assertTrue(validate_ledger(copy_), name)
