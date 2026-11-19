"""PR87 finite contract search and abstract input mutants; no LLM/Git execution."""
import copy
import hashlib
import itertools
import json
import unittest

from cora.chat_bundle import _cockpit, append_chat_iteration, verify_chat_bundle
from tests import test_pr46_chat_bundle as fixture_module


class CockpitTests(unittest.TestCase):
    def test_100_contracts_finite_selection(self):
        # 5 provenance x 5 estimates x 4 action policies = 100 finite alternatives.
        provenance = ('chat-trust', 'zip-present', 'receipt-only',
                      'zip-and-receipt-replayed', 'external-certification-claimed')
        estimates = ('invented-hours', 'fixed-days', 'fixed-phases',
                     'unknown-only', 'reported-leaves-without-time')
        actions = ('auto-write', 'auto-merge', 'opaque-advice', 'three-safe-choices')
        proposals = list(itertools.product(provenance, estimates, actions))
        eligible = [x for x in proposals if (x[0] == provenance[3] and
                    x[1] == estimates[4] and x[2] == actions[3])]
        self.assertEqual((len(proposals), len(eligible)), (100, 1))
        print('PR87_100_CONTRACTS ' + json.dumps({
            'tested': 100, 'eligible': 1, 'winner': eligible[0],
            'optimality': 'DEFINED_FINITE_SPACE_ONLY', 'model_calls': 0}))

    def fixture(self):
        h = fixture_module.ChatBundleTests('test_append_roundtrip_two_rounds_and_exact_handoff')
        h.setUp()
        self.addCleanup(h.doCleanups)
        result = append_chat_iteration(h.bundle, repo=h.repo,
                                       step=h.step(), receipt=h.receipt())
        return result, h.bundle

    def test_verified_zip_to_cockpit(self):
        report, bundle = self.fixture()
        cockpit = verify_chat_bundle(bundle, expected_receipt={
            'schema': 'cora-integrated-one-run/2', 'commit': 'a' * 40,
            'product_status': 'BLOCKED_EXTERNAL', 'authorization': 'NONE',
            'authority': 'NONE', 'release_authorized': False})['cockpit']
        self.assertEqual(cockpit, report['cockpit'])
        self.assertEqual(cockpit['status'], 'HUMAN_DECISION_REQUIRED')
        self.assertEqual(cockpit['recommended'], 'PROPOSE_NEXT_CHECK')
        self.assertEqual(cockpit['reported_open_dod_leaves'], 1)
        self.assertEqual([x['id'] for x in cockpit['choices']],
                         ['EXPLAIN', 'REPLAN', 'PROPOSE_NEXT_CHECK'])
        self.assertIsNone(cockpit['time_estimate'])
        self.assertIsNone(cockpit['remaining_phases_estimate'])
        self.assertEqual(cockpit['execution'], 'NONE')
        self.assertEqual(cockpit['authorization'], 'NONE')
        self.assertIs(cockpit['product_accepted'], False)
        self.assertIn(cockpit['recommended'], [x['id'] for x in cockpit['choices']])

    def test_all_recommendations_are_visible_choices(self):
        report, _ = self.fixture()
        for decision in ('PAUSE_CAPACITY_AND_REBASE', 'REVIEW_CHANGED_CONTRACT',
                         'REVALIDATE_CHANGED_SOURCE', 'REPLAN_STALLED_REPORTS',
                         'REQUEST_INDEPENDENT_ACCEPTANCE', 'REQUEST_EXTERNAL_WITNESS',
                         'PROPOSE_NEXT_SCOPED_STEP'):
            state = dict(report['continuation'], decision=decision)
            cockpit = _cockpit(state, 'a' * 40)
            self.assertIn(cockpit['recommended'],
                          [choice['id'] for choice in cockpit['choices']])
            self.assertEqual(cockpit['authorization'], 'NONE')
            self.assertIs(cockpit['product_accepted'], False)

    def test_10000_abstract_semantic_mutants_fail_closed(self):
        report, _ = self.fixture()
        original = report['continuation']
        seen = set()
        families = ('schema', 'decision', 'proof_boundary', 'authorization',
                    'product_accepted', 'automatic_execution', 'negative_open',
                    'overflow_open', 'bad_node', 'bad_commit')
        for family, i in itertools.product(families, range(1000)):
            changed = copy.deepcopy(original)
            commit = 'a' * 40
            if family == 'schema':
                changed['schema'] = f'forged-schema-{i}'
            elif family == 'decision':
                changed['decision'] = f'AUTO_PASS_{i}'
            elif family == 'proof_boundary':
                changed['proof_boundary'] = f'TARGET_VERIFIED_{i}'
            elif family == 'authorization':
                changed['authorization'] = f'APPROVED_{i}'
            elif family == 'product_accepted':
                changed['product_accepted'] = i
            elif family == 'automatic_execution':
                changed['automatic_execution'] = i
            elif family == 'negative_open':
                changed['reported_open_leaves'] = -(i + 1)
            elif family == 'overflow_open':
                changed['reported_open_leaves'] = 129 + i
            elif family == 'bad_node':
                changed['next_unresolved'] = f'BAD NODE {i}'
            else:
                commit = f'{i:039x}Z'
            digest = hashlib.sha256(json.dumps([family, i, changed, commit],
                                               sort_keys=True).encode()).digest()
            self.assertNotIn(digest, seen)
            seen.add(digest)
            with self.assertRaises(ValueError):
                _cockpit(changed, commit)
        self.assertEqual(len(seen), 10_000)
        print('PR87_10K_ABSTRACT ' + json.dumps({
            'families': 10, 'distinct_inputs': 10000, 'rejected': 10000,
            'survivors': 0, 'scope': 'DTO_ONLY_NOT_MODEL_OR_PHYSICAL_GIT',
            'model_calls': 0, 'authorization': 'NONE'}))


# PR87 C9: source-bound CI ownership, not a new runtime gate or proof issuer.
from pathlib import Path


def _pr36_ci_owner_contract(documentation: str, integrated: str) -> None:
    """Require exact native PR36 checks in one owner; fail on false PASS cuts."""
    marker = '  pr36-native-owner:\n'
    boundary = '  diagnose-comprehensive:\n'
    assert integrated.count(marker) == 1, 'missing or duplicated PR36 owner'
    block = integrated.split(marker, 1)[1].split(boundary, 1)[0]
    assert 'PR36 execute original Git' not in documentation, 'duplicated PR36 execution'
    assert '/tmp/cora-one-run.json' not in documentation, 'stale owned artifact in docs'
    assert "python-version: ['3.11', '3.13']" in block
    assert 'fail-fast: false' in block and 'timeout-minutes: 50' in block
    assert 'ref: ${{ github.event.pull_request.head.sha || github.sha }}' in block
    assert 'fetch-depth: 0' in block and 'persist-credentials: false' in block
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"' in block
    required = (
        'PR36 execute original Git one-run methods and render JSON/HTML',
        'PR36 replay underlying deterministic original source-process receipt',
        'PR36 verify one-run JSON original source identity and report integrity',
        'PR36 assert offline HTML byte-equivalence to verified run',
        'PR36 physical Git DoD mutants and one-run negative tests',
        'PR36 falsify 100k distinct preseeded semantic receipts twice',
        '--model-stress-cases 100000',
        'assert verify_suite(',
        'assert verify_one(',
        'test_pr36_one_run.py',
        'cmp /tmp/cora-one-run-100k.json /tmp/cora-one-run-100k-replay.json',
        'a["authorization"]=="NONE"',
        'not a["release_authorized"]',
        'r["unauthorized_promotions"]==0',
    )
    for clause in required:
        assert block.count(clause) == 1, 'missing/duplicated PR36 oracle: ' + clause
    assert block.count('--cases 100000') == 2, 'both seeded replays required'
    assert 'if: always()' in block
    assert 'cora-pr36-source-${{ matrix.python-version }}' in block
    assert 'continue-on-error: true' not in block and '|| true' not in block


def _mutate_pr36_owner(owner: str, old: str, new: str) -> str:
    marker = '  pr36-native-owner:\n'
    boundary = '  diagnose-comprehensive:\n'
    prefix, rest = owner.split(marker, 1)
    block, suffix = rest.split(boundary, 1)
    assert old in block, 'mutation did not target PR36 owner'
    return prefix + marker + block.replace(old, new, 1) + boundary + suffix


class Pr87CiOwnershipTests(unittest.TestCase):
    def test_native_owner_and_sixteen_negative_mutants(self):
        # Workflows are tracked source; this is an exact current-tree *static*
        # contract, while GitHub owns the actual job execution and results.
        documentation = Path('.github/workflows/ci-documentation.yml').read_text()
        integrated = Path('.github/workflows/ci-one-run-integrated.yml').read_text()
        _pr36_ci_owner_contract(documentation, integrated)
        alterations = [
            ('--model-stress-cases 100000', '--model-stress-cases 0'),
            ('assert verify_suite(', 'if verify_suite('),
            ('assert verify_one(', 'if verify_one('),
            ('test_pr36_one_run.py', 'test_pr35_one_run.py'),
            ('--cases 100000', '--cases 99999'),
            ('cmp /tmp/cora-one-run-100k.json', ': /tmp/cora-one-run-100k.json'),
            ('if: always()', 'if: false'),
            ('timeout-minutes: 50', 'timeout-minutes: 12'),
            ('test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', 'echo "$EXPECTED_SHA"'),
            ("python-version: ['3.11', '3.13']", "python-version: ['3.11']"),
            ('PR36 execute original Git one-run methods', 'PR36 execute original Git one-run methods\n        continue-on-error: true'),
            ('persist-credentials: false', 'persist-credentials: true'),
            ('fetch-depth: 0', 'fetch-depth: 1'),
            ('not a["release_authorized"]', 'a["release_authorized"]'),
            ('r["unauthorized_promotions"]==0', 'r["unauthorized_promotions"]>=0'),
        ]
        for i, (old, new) in enumerate(alterations):
            with self.subTest(mutant=i), self.assertRaises(AssertionError):
                _pr36_ci_owner_contract(documentation, _mutate_pr36_owner(integrated, old, new))
        with self.assertRaises(AssertionError):
            _pr36_ci_owner_contract(
                documentation + '      - name: PR36 execute original Git one-run methods and render JSON/HTML\n',
                integrated)
        self.assertEqual(len(alterations) + 1, 16)
