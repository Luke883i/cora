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
        self.assertEqual(cockpit['recommended'], 'ASK_FOR_WITNESS')
        self.assertEqual(cockpit['reported_open_dod_leaves'], 1)
        self.assertEqual([x['id'] for x in cockpit['choices']],
                         ['EXPLAIN', 'REPLAN', 'PROPOSE_NEXT_CHECK'])
        self.assertIsNone(cockpit['time_estimate'])
        self.assertIsNone(cockpit['remaining_phases_estimate'])
        self.assertEqual(cockpit['execution'], 'NONE')
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
