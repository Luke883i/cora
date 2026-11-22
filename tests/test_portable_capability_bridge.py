"""PR99 pre-PR: source-scoped, physical target and negative cross-receipt oracles.

The 81-owner rows here are a MODEL negative-control fixture, not the
original verified One-Run 81-owner plan. Never promote them to real execution.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.foreign_pilot import (
    _project_portable_receipts, reconcile_portable_capabilities,
    verify_portable_capabilities, run_foreign_pilot,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/third_party/pypa_sampleproject'


def git(root: Path, *argv: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *argv], text=True).strip()


def model_source_81() -> dict:
    """Finite synthetic input for consumer contracts, NOT a verified plan."""
    atlas = json.loads((ROOT / '.cora/assurance/capability-atlas.json').read_text())
    assert len(atlas['commands']) == 71
    rows = []
    for item in atlas['commands']:
        name = item['command']
        selected = name == 'process-run'
        rows.append({'id': 'cora:' + name, 'kind': 'NATIVE_CLI',
                     'selected': selected, 'state': 'BLOCKED' if selected else 'NOT_SELECTED',
                     'authority': 'NONE'})
    rows += [{'id': 'external:model-fixture-%02d' % i,
              'kind': 'UPSTREAM_CANDIDATE', 'selected': False,
              'state': 'NOT_SELECTED', 'authority': 'NONE'} for i in range(10)]
    rows.sort(key=lambda row: row['id'])
    return {'schema': 'cora-universal-capability-plan/1',
            'commit': 'f' * 40, 'authority': 'NONE',
            'product_status': 'BLOCKED_EXTERNAL', 'rows': rows,
            'counts': {'total': 81, 'native': 71, 'external': 10,
                       'selected': 1, 'blocked': 1, 'not_selected': 80,
                       'run_reported': 0, 'source_reused': 0}}


class PortableBridgeDoDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='cora-pr99-native-')
        cls.dir = Path(cls.temp.name)
        cls.target = cls.dir / 'target'
        shutil.copytree(FIXTURE, cls.target,
                        ignore=shutil.ignore_patterns('upstream-reference.json', '__pycache__'))
        git(cls.target, 'init', '-q')
        git(cls.target, 'config', 'user.name', 'Local target oracle')
        git(cls.target, 'config', 'user.email', 'fixture@example.invalid')
        git(cls.target, 'add', '-A')
        git(cls.target, 'commit', '-qm', 'original verified PyPA blob subset')
        cls.request = {'schema': 'cora-foreign-pilot-request/1',
                       'commit': git(cls.target, 'rev-parse', 'HEAD'),
                       'tree': git(cls.target, 'rev-parse', 'HEAD^{tree}'),
                       'choices': [{'adapter': 'unittest', 'path': 'tests/test_simple.py',
                                    'expected': ['test_simple.TestSimple.test_add_one'],
                                    'obligation': 'ORIGINAL_ADD_ONE',
                                    'reason': 'target-owned Git-native original test'}],
                       'timeout': 20, 'trusted_local_execution': True}
        cls.evidence = cls.dir / 'native-logs'
        cls.target_receipt = run_foreign_pilot(cls.target, cls.request, execute=True,
                                               evidence_dir=cls.evidence)
        cls.source = {'commit': 'f' * 40,
                      'universal_capability_plan': model_source_81()}
        cls.bindings = [{'owner_id': 'cora:process-run',
                         'obligation': 'ORIGINAL_ADD_ONE',
                         'adapter': 'unittest', 'path': 'tests/test_simple.py',
                         'test_id': 'test_simple.TestSimple.test_add_one'}]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def project(self, source=None, target=None, bindings=None):
        return _project_portable_receipts(
            source if source is not None else self.source,
            target if target is not None else self.target_receipt,
            bindings if bindings is not None else self.bindings)

    def test_original_git_eighty_one_owner_plan_and_native_link(self):
        """Use the REAL 81-owner One-Run output; never promote its blocked rows."""
        from cora.one_run import run_one, verify_one
        from cora.foreign_pilot import reconcile_portable_capabilities
        from cora.integrated_run import _portable_source_target_link
        receipt = run_one(ROOT, 'HEAD', process='history',
                          capability_intent='process-run')
        self.assertTrue(verify_one(ROOT, receipt))
        plan = receipt['universal_capability_plan']
        self.assertEqual(plan['counts']['total'], 81)
        process_owner = next(x for x in plan['rows'] if x['id'] == 'cora:process-run')
        self.assertTrue(process_owner['selected'])
        self.assertEqual(process_owner['state'], 'BLOCKED')
        evidence = reconcile_portable_capabilities(
            ROOT, receipt, self.target, self.target_receipt,
            self.evidence, bindings=self.bindings)
        self.assertEqual(evidence['scope_status'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertEqual(evidence['catalog_metrics']['source_owners_executed_by_bridge'], 0)
        self.assertEqual(evidence['native_test_metrics']['passing_test_ids'], 1)
        self.assertEqual(evidence['universal_81_execution'], 'BLOCKED_EXTERNAL')
        manifest = self.dir / 'integrated-link.json'
        request = {'schema': 'cora-portable-link-request/1',
                   'target_repo': str(self.target.resolve()),
                   'target_receipt': self.target_receipt,
                   'target_evidence_dir': str(self.evidence.resolve()),
                   'bindings': copy.deepcopy(self.bindings)}
        manifest.write_text(json.dumps(request), encoding='utf-8')
        linked = _portable_source_target_link(ROOT, receipt, manifest)
        self.assertEqual(linked['reconciliation'], evidence)
        self.assertEqual(linked['authority'], 'NONE')
        self.assertEqual(linked['product_status'], 'BLOCKED_EXTERNAL')
        # Full original comprehensive source execution: the 81-row plan and
        # the existing target receipt must survive materialization and replay.
        from cora.integrated_run import run_integrated, verify_integrated
        folder = self.dir / 'comprehensive-link-evidence'
        full = run_integrated(ROOT, 'HEAD', process='history',
                              portable_link=manifest, evidence_dir=folder)
        self.assertEqual(full['baseline_pr36']['universal_capability_plan']['counts']['total'], 81)
        self.assertEqual(full['portable_link']['reconciliation'], evidence)
        self.assertEqual(full['portable_link']['scope_status'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertEqual(full['product_status'], 'BLOCKED_EXTERNAL')
        self.assertTrue(verify_integrated(ROOT, full, evidence_dir=folder,
                                          portable_link=manifest))
        request['bindings'][0] = dict(request['bindings'][0], test_id='forged.Test.fake')
        self.assertEqual(self.bindings[0]['test_id'], 'test_simple.TestSimple.test_add_one')
        manifest.write_text(json.dumps(request), encoding='utf-8')
        with self.assertRaises(ValueError):
            _portable_source_target_link(ROOT, receipt, manifest)

    def test_reticular_32_node_backward_and_dod_is_closed(self):
        contract = json.loads((ROOT / '.cora/contracts/dod/pr99-portable-universal-dod.json').read_text())
        self.assertEqual(contract['schema'], 'cora-pr99-portable-universal-dod/1')
        self.assertEqual(contract['authority'], 'NONE')
        self.assertEqual(contract['remote_pr98']['source_blob_oid'],
                         '29b18eefa4652ee344af01fd2426631076d81cd2')
        self.assertIs(contract['remote_pr98']['head_present_in_local_git'], True)
        self.assertEqual(contract['remote_pr98']['merged_main'],
                         '744401c53dd62640f93d26f3b7c96b82940d059f')
        graph = {n['id']: n for n in contract['nodes']}
        self.assertEqual(len(graph), len(contract['nodes']))
        self.assertEqual(len(graph), 32)
        self.assertEqual(contract['global_goals'], ['G_SCOPED_BRIDGE', 'G_UNIVERSAL_PRODUCT'])
        entered, visited = set(), set()
        def walk(node):
            if node in entered:
                raise ValueError('cycle')
            if node in visited:
                return
            if node not in graph:
                raise ValueError('missing leaf')
            entered.add(node)
            for leaf in graph[node]['depends_on']:
                walk(leaf)
            entered.remove(node)
            visited.add(node)
        walk('G_UNIVERSAL_PRODUCT')
        self.assertEqual(visited, set(graph))
        external = [n for n in graph.values() if n['scope'] == 'EXTERNAL'
                    and n['kind'] == 'LOCAL']
        self.assertEqual(len(external), 8)
        self.assertTrue(all(n['status'] == 'BLOCKED_EXTERNAL' for n in external))
        self.assertEqual(graph['G_UNIVERSAL_PRODUCT']['status'], 'BLOCKED_EXTERNAL')
        named = [n for n in graph.values() if n['kind'] == 'LOCAL'
                 and n['scope'] != 'EXTERNAL']
        self.assertEqual(len(named), 14)
        methods = {x for x in dir(type(self)) if x.startswith('test_')}
        for node in named:
            self.assertIn(node['oracle'].split('.')[-1], methods)

    def test_pr100_candidate_25_node_follow_on_no_global_promotion(self):
        contract = json.loads((ROOT / '.cora/contracts/dod/pr99-portable-universal-dod.json').read_text())
        candidate = contract['candidate_follow_on']
        self.assertEqual(candidate['schema'], 'cora-universal-frontier-candidate/1')
        self.assertEqual(candidate['authority'], 'NONE')
        self.assertEqual(candidate['status'], 'SOURCE_CANDIDATE_NOT_ACCEPTED')
        self.assertEqual(candidate['source_lock']['as_is_pr99_head'],
                         'ede6479b7740e5f33da32599912f36900c61432d')
        self.assertEqual(candidate['source_lock']['as_is_pr99_contract_blob'],
                         '62eed37bcadd812ecbf5d5da42fa16e1ac48dba0')
        self.assertEqual(candidate['metrics']['source']['owner_catalog_exact'], 81)
        self.assertEqual(candidate['metrics']['source']['canonical_project_prompt_modifications_max'], 0)
        self.assertEqual(candidate['release_rule']['global'], 'BLOCKED_EXTERNAL')
        self.assertEqual(len(candidate['falsifiers']), 12)

        def validate(data):
            graph = {x['id']: x for x in data['nodes']}
            if len(graph) != len(data['nodes']) or len(graph) != 25:
                raise ValueError('duplicate or missing DoD nodes')
            entered, seen = set(), set()
            def visit(node):
                if node in entered or node not in graph:
                    raise ValueError('cycle or missing DoD leaf')
                if node in seen:
                    return
                entered.add(node)
                for leaf in graph[node]['depends_on']:
                    visit(leaf)
                entered.remove(node)
                seen.add(node)
            visit('G_UNIVERSAL_ACCEPTED')
            if len(seen) != len(graph) or data['release_rule']['global'] != 'BLOCKED_EXTERNAL':
                raise ValueError('unreachable or promoted global')
            if any(x['status'] != 'BLOCKED_EXTERNAL' for x in data['nodes']
                   if x['scope'] == 'EXTERNAL'):
                raise ValueError('external authority forged')
            return True

        self.assertTrue(validate(candidate))
        for fault in ('drop-leaf', 'duplicate', 'fake-release', 'fake-review'):
            with self.subTest(fault=fault):
                altered = copy.deepcopy(candidate)
                if fault == 'drop-leaf':
                    altered['nodes'] = altered['nodes'][:-1]
                elif fault == 'duplicate':
                    altered['nodes'].append(copy.deepcopy(altered['nodes'][-1]))
                elif fault == 'fake-release':
                    altered['release_rule']['global'] = 'PASS'
                else:
                    next(x for x in altered['nodes'] if x['scope'] == 'EXTERNAL')['status'] = 'PASS'
                with self.assertRaises(ValueError):
                    validate(altered)

    def test_release_and_security_metrics_never_self_authorize(self):
        doc = json.loads((ROOT / '.cora/contracts/dod/pr99-portable-universal-dod.json').read_text())
        qm = doc['quality_metrics']
        self.assertEqual(qm['development']['cli_commands_exact'], 71)
        self.assertEqual(qm['development']['declared_owners_exact'], 81)
        self.assertEqual(qm['native_testing']['mutation_survivors_max'], 0)
        self.assertEqual(qm['evidence']['unqualified_isolation_pass_max'], 0)
        self.assertTrue(qm['release']['required_checks_completed'])
        self.assertTrue(qm['release']['security_review_signed_by_non_author'])
        self.assertEqual(qm['release']['merge_release_authority'], 'EXTERNAL_HUMAN_ONLY')
        self.assertEqual(doc['current_claim'].endswith('BLOCKED_EXTERNAL.'), True)

    def test_model_81_rows_and_one_native_test_cannot_promote_81_executions(self):
        result = self.project()
        self.assertEqual(result['scope_status'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertEqual(result['native_test_metrics']['passing_test_ids'], 1)
        self.assertEqual(result['catalog_metrics'], {
            'total': 81, 'native': 71, 'external': 10,
            'source_owners_executed_by_bridge': 0, 'selected': 1})
        self.assertEqual(result['universal_81_execution'], 'BLOCKED_EXTERNAL')
        self.assertEqual(result['host_isolation'], 'NOT_ATTESTED')
        self.assertEqual(result['independent_acceptance'], 'BLOCKED_EXTERNAL')
        self.assertEqual(result['bindings'][0]['cora_owner_execution'],
                         'NOT_ATTESTED_BY_TARGET_TEST')

    def test_original_native_target_event_and_git_are_not_synthetic(self):
        self.assertEqual(self.target_receipt['selected_outcome'],
                         'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertEqual(self.target_receipt['commit'], git(self.target, 'rev-parse', 'HEAD'))
        self.assertEqual(self.target_receipt['tree'], git(self.target, 'rev-parse', 'HEAD^{tree}'))
        self.assertEqual(self.target_receipt['test_linkage'][0]['observed'],
                         ['test_simple.TestSimple.test_add_one'])

    def test_missing_real_universal_plan_must_block(self):
        with self.assertRaisesRegex(ValueError, '81-owner plan required'):
            self.project({'commit': 'f' * 40})

    def test_80_or_82_owner_rows_refuted(self):
        for mod in ('pop', 'append'):
            src = copy.deepcopy(self.source)
            if mod == 'pop':
                src['universal_capability_plan']['rows'].pop()
            else:
                src['universal_capability_plan']['rows'].append(copy.deepcopy(
                    src['universal_capability_plan']['rows'][0]))
            with self.subTest(mod=mod), self.assertRaises(ValueError):
                self.project(src)

    def test_forged_counts_and_authority_refuted(self):
        for key, value in (('total', 80), ('native', 72), ('selected', 81)):
            src = copy.deepcopy(self.source)
            src['universal_capability_plan']['counts'][key] = value
            with self.subTest(count=key), self.assertRaises(ValueError):
                self.project(src)
        src = copy.deepcopy(self.source)
        src['universal_capability_plan']['authority'] = 'APPROVED'
        with self.assertRaises(ValueError):
            self.project(src)

    def test_upstream_tool_cannot_be_laundered_into_execution(self):
        src = copy.deepcopy(self.source)
        candidate = next(x for x in src['universal_capability_plan']['rows']
                         if x['kind'] == 'UPSTREAM_CANDIDATE')
        candidate['state'], candidate['selected'] = 'RUN_REPORTED_UNATTESTED', True
        src['universal_capability_plan']['counts'].update(
            selected=2, run_reported=1, not_selected=79)
        with self.assertRaisesRegex(ValueError, 'external tool execution'):
            self.project(src)

    def test_foreign_target_cannot_impersonate_executed_cora_command(self):
        bind = copy.deepcopy(self.bindings)
        bind[0]['owner_id'] = 'cora:version'
        with self.assertRaisesRegex(ValueError, 'unqualified capability owner'):
            self.project(bindings=bind)

    def test_unselected_owner_cannot_inherit_target_result(self):
        src = copy.deepcopy(self.source)
        owner = next(x for x in src['universal_capability_plan']['rows']
                     if x['id'] == 'cora:process-run')
        owner['selected'], owner['state'] = False, 'NOT_SELECTED'
        src['universal_capability_plan']['counts'].update(selected=0, blocked=0,
                                                         not_selected=81)
        with self.assertRaisesRegex(ValueError, 'unselected'):
            self.project(src)

    def test_unexpected_test_id_or_duplicate_binding_is_refuted(self):
        for mod in ('unknown', 'duplicate'):
            bind = copy.deepcopy(self.bindings)
            if mod == 'unknown':
                bind[0]['test_id'] = 'invented.Test.fake'
            else:
                bind.append(copy.deepcopy(bind[0]))
            with self.subTest(mod=mod), self.assertRaises(ValueError):
                self.project(bindings=bind)

    def test_tampered_or_skipped_target_test_fails_closed(self):
        for state in ('NOT_RUN', 'DEBT_BLOCKED'):
            target = copy.deepcopy(self.target_receipt)
            target['test_linkage'][0]['state'] = state
            projection = self.project(target=target)
            self.assertEqual(projection['scope_status'], 'DEBT_BLOCKED')
            self.assertEqual(projection['native_test_metrics']['passing_test_ids'], 0)
            self.assertEqual(projection['native_test_metrics']['blocked_test_ids'], 1)
            self.assertEqual(projection['bindings'][0]['native_test_status'], 'DEBT_BLOCKED')

    def test_no_sandbox_or_reviewer_promotion(self):
        for field in ('isolation', 'authority', 'product_acceptance'):
            target = copy.deepcopy(self.target_receipt)
            target[field] = 'INDEPENDENTLY_APPROVED'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.project(target=target)

    def test_genuine_dual_verification_cannot_be_bypassed_by_presented_data(self):
        # Source fixture is MODEL_ONLY; the verification call is instrumented
        # to show EXACTLY the independent dependency boundary, never to claim
        # that the synthetic source receipt is a real 81-owner One-Run receipt.
        from cora.one_run import verify_one as original_verify_one
        def verify_source(repo, receipt):
            # Only the historical CORA plan is modeled; the real target's
            # original One-Run receipt MUST still be verified, not mocked.
            if Path(repo).resolve() == ROOT.resolve():
                return True
            return original_verify_one(repo, receipt)
        with patch('cora.foreign_pilot.verify_one', side_effect=verify_source) as source_verify:
            result = reconcile_portable_capabilities(
                ROOT, self.source, self.target, self.target_receipt,
                self.evidence, bindings=self.bindings)
            self.assertTrue(verify_portable_capabilities(
                ROOT, self.source, self.target, self.target_receipt,
                self.evidence, result))
            self.assertEqual(source_verify.call_count, 4)
            self.assertEqual(result['authority'], 'NONE')
            self.assertEqual(result['independent_acceptance'], 'BLOCKED_EXTERNAL')
            altered = copy.deepcopy(result)
            altered['catalog_metrics']['source_owners_executed_by_bridge'] = 81
            with self.assertRaisesRegex(ValueError, 'reconciliation altered'):
                verify_portable_capabilities(ROOT, self.source, self.target,
                                             self.target_receipt, self.evidence, altered)
        # Without the original 81-owner source receipt replay, positive
        # correlation is *not* a demonstrated target runtime integration.
        with self.assertRaises(ValueError):
            reconcile_portable_capabilities(ROOT, self.source, self.target,
                                            self.target_receipt, self.evidence,
                                            bindings=self.bindings)

    def test_real_retained_byte_tampering_is_refuted(self):
        file = self.evidence / 'pilot-00.log'
        original = file.read_bytes()
        try:
            file.write_bytes(original + b'FORGED PASS\n')
            from cora.one_run import verify_one as original_verify_one
            with patch('cora.foreign_pilot.verify_one', side_effect=lambda repo, receipt:
                       True if Path(repo).resolve() == ROOT.resolve() else
                       original_verify_one(repo, receipt)):
                with self.assertRaises(ValueError):
                    reconcile_portable_capabilities(ROOT, self.source,
                        self.target, self.target_receipt, self.evidence,
                        bindings=self.bindings)
        finally:
            file.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
