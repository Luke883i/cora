"""PR97 hardening: scoped native verification on exact PyPA upstream blobs.

The fixture is an explicit *subset* of upstream, not its original commit tree.
No GitHub CI, OS sandbox or reviewer authority is inferred from these tests.
"""
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cora.foreign_pilot import (
    run_foreign_pilot, verify_foreign_pilot, prioritize_obligations,
    _outside, ADAPTERS,
)
from cora.one_run import verify_one

FIXTURE = Path(__file__).parent / 'fixtures' / 'third_party' / 'pypa_sampleproject'


class ForeignTargetHardeningTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix='cora-foreign-test-'))
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.target = self.home / 'target'
        shutil.copytree(FIXTURE, self.target, ignore=shutil.ignore_patterns('upstream-reference.json', '__pycache__'))
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.commit()
        (self.target / '.local-fixture-note').write_text('Local subset reconstruction, not original upstream tree\n')
        self.commit()
        self.request = self.make_request()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.target), *args], stderr=subprocess.PIPE, text=True).strip()

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'local fixture source transition')

    def make_request(self, adapters=('unittest',), trusted=True):
        return {'schema': 'cora-foreign-pilot-request/1', 'commit': self.git('rev-parse', 'HEAD'),
                'tree': self.git('rev-parse', 'HEAD^{tree}'), 'choices': [
                    {'adapter': adapter, 'path': 'tests/test_simple.py',
                     'expected': ['test_simple.TestSimple.test_add_one'],
                     'obligation': 'ORIGINAL_ADD_ONE',
                     'reason': 'independent original PyPA test on Git blobs'} for adapter in adapters],
                'timeout': 20, 'trusted_local_execution': trusted}

    def run_pilot(self, name='evidence', execute=True):
        return run_foreign_pilot(self.target, self.request, execute=execute,
                                 evidence_dir=self.home / name)

    def test_upstream_blob_identity(self):
        original = json.loads((FIXTURE / 'upstream-reference.json').read_text())
        self.assertEqual(original['upstream_commit'], '621e4974ca25ce531773def586ba3ed8e736b3fc')
        self.assertEqual(original['scope'], 'EXACT_BLOB_RECONSTRUCTION_NOT_FULL_UPSTREAM_TREE')
        for path, expected in original['files'].items():
            self.assertEqual(self.git('rev-parse', 'HEAD:' + path), expected)
            self.assertEqual(self.git('hash-object', path), expected)

    def test_one_run_original_target_unittest(self):
        result = self.run_pilot()
        self.assertEqual(result['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertEqual(result['test_linkage'][0]['observed'], ['test_simple.TestSimple.test_add_one'])
        self.assertEqual(result['source_one_run']['commit'], self.request['commit'])
        self.assertTrue(verify_foreign_pilot(self.target, result, self.home / 'evidence'))

    def test_physical_target_mutant_is_refuted(self):
        (self.target / 'src/sample/simple.py').write_text('def add_one(number):\n    return number + 2\n')
        self.commit()
        self.request = self.make_request()
        mutant = self.run_pilot('mutant')
        self.assertEqual(mutant['selected_outcome'], 'DEBT_BLOCKED')
        self.assertNotEqual(mutant['observations'][0]['exit'], 0)
        self.assertTrue(verify_foreign_pilot(self.target, mutant, self.home / 'mutant'))
        (self.target / 'src/sample/simple.py').write_text('def add_one(number):\n    return number + 1\n')
        self.commit()
        self.request = self.make_request()
        restored = self.run_pilot('restored')
        self.assertEqual(restored['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')

    def test_ranking_requires_structured_obligations(self):
        result = self.run_pilot()
        valid = [{'id': 'ORIGINAL_ADD_ONE', 'owners': ['unittest'], 'impact': 4}]
        sources = [{'repo': self.target, 'report': result, 'evidence_dir': self.home / 'evidence'}]
        self.assertEqual(prioritize_obligations(valid, sources, budget_ms=20000)[0]['state'], 'QUALIFIED_CANDIDATE')
        for bad in (['please select intelligently'], [{'id': 'x', 'owners': ['unittest'], 'impact': 1000}],
                    [{'id': 'x', 'owners': ['unittest', 'unittest'], 'impact': 4}]):
            with self.assertRaises(ValueError):
                prioritize_obligations(bad, sources, budget_ms=20000)

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'optional pytest adapter not installed')
    def test_measured_two_adapter_selection(self):
        self.request = self.make_request(('unittest', 'pytest'))
        result = self.run_pilot()
        self.assertEqual(result['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        ranking = prioritize_obligations(
            [{'id': 'ORIGINAL_ADD_ONE', 'owners': ['unittest', 'pytest', 'semgrep'], 'impact': 4}],
            [{'repo': self.target, 'report': result, 'evidence_dir': self.home / 'evidence'}], budget_ms=20000)
        self.assertEqual({x['adapter'] for x in ranking}, {'unittest', 'pytest', 'semgrep'})
        self.assertEqual(sum(x['state'] == 'QUALIFIED_CANDIDATE' for x in ranking), 2)
        self.assertGreaterEqual(ranking[0]['decision_score'], ranking[1]['decision_score'])
        self.assertEqual(ranking[2]['state'], 'BLOCKED_MISSING_ADAPTER')
        modified = copy.deepcopy(result)
        modified['test_linkage'][0]['state'] = 'DEBT_BLOCKED'
        with self.assertRaises(ValueError):
            prioritize_obligations([{'id': 'ORIGINAL_ADD_ONE', 'owners': ['unittest'], 'impact': 1}],
                [{'repo': self.target, 'report': modified, 'evidence_dir': self.home / 'evidence'}], budget_ms=20000)

    def test_failed_history_cannot_be_qualified_by_low_cost(self):
        # A fast known failure is still negative evidence, never a preferred adapter.
        (self.target / 'src/sample/simple.py').write_text('def add_one(number):\n    return number + 2\n')
        self.commit()
        self.request = self.make_request()
        bad = self.run_pilot()
        self.assertEqual(bad['selected_outcome'], 'DEBT_BLOCKED')
        ranked = prioritize_obligations(
            [{'id': 'ORIGINAL_ADD_ONE', 'owners': ['unittest'], 'impact': 100}],
            [{'repo': self.target, 'report': bad, 'evidence_dir': self.home / 'evidence'}],
            budget_ms=20000)
        self.assertEqual(ranked[0]['state'], 'BLOCKED_NO_POSITIVE_RUNTIME_EVIDENCE')
        self.assertIsNone(ranked[0]['decision_score'])
        self.assertEqual(ranked[0]['observed_success_rate'], 0)

    @unittest.skipUnless(os.name == 'posix', 'process groups available only on POSIX')
    def test_bounded_runner_cancels_descendant_on_timeout(self):
        from cora.foreign_pilot import _bounded_target_command
        sentinel = self.home / 'late-child.txt'
        child = "import time; time.sleep(2); open(%r,'w').write('escaped')" % str(sentinel)
        parent = "import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', %r]);time.sleep(4)" % child
        with self.assertRaises(subprocess.TimeoutExpired):
            _bounded_target_command([sys.executable, '-c', parent], self.home,
                                    {'PATH': os.environ.get('PATH', '')}, timeout=1)
        import time
        time.sleep(2.3)
        self.assertFalse(sentinel.exists(), 'process group child escaped bounded cancellation')

    def test_unknown_adapter_stays_blocked(self):
        self.request = self.make_request(('semgrep',))
        result = self.run_pilot()
        self.assertEqual(result['selected_outcome'], 'DEBT_BLOCKED')
        self.assertEqual(result['observations'][0]['reason'], 'MISSING_ADAPTER')
        self.assertEqual(result['next_unresolved']['adapter'], 'semgrep')
        self.assertTrue(verify_foreign_pilot(self.target, result, self.home / 'evidence'))

    def test_explicit_optin_and_stale_sha(self):
        blocked = self.run_pilot('denied', execute=False)
        self.assertEqual(blocked['selected_outcome'], 'DEBT_BLOCKED')
        self.assertEqual(blocked['observations'], [])
        self.assertTrue(verify_foreign_pilot(self.target, blocked, self.home / 'denied'))
        self.request['trusted_local_execution'] = False
        with self.assertRaises(ValueError):
            self.run_pilot('nonconsented')
        self.request['trusted_local_execution'] = True
        self.request['commit'] = 'a' * 40
        with self.assertRaises(ValueError):
            self.run_pilot('stale')
        self.request = self.make_request()
        self.request['tree'] = 'b' * 40
        with self.assertRaises(ValueError):
            self.run_pilot('wrong-tree')

    def test_path_and_result_bounds(self):
        self.request['choices'][0]['path'] = '../unsafe.py'
        with self.assertRaises(ValueError):
            self.run_pilot('escape')
        self.request = self.make_request()
        self.request['timeout'] = 900
        with self.assertRaises(ValueError):
            self.run_pilot('timeout')
        self.request = self.make_request()
        with self.assertRaises(ValueError):
            _outside(self.target, self.target / 'unsafe-output')
        # A committed symlink cannot be copied or followed into the pilot executor.
        (self.target / 'sym').symlink_to('src/sample/simple.py')
        self.commit()
        self.request = self.make_request()
        with self.assertRaises(ValueError):
            self.run_pilot('symlink')

    def test_runtime_timeout_and_output_limit(self):
        source = (
            'import unittest\nclass TestSimple(unittest.TestCase):\n'
            '    def test_add_one(self): print("X" * 610000)\n'
        )
        (self.target / 'tests/test_simple.py').write_text(source)
        self.commit()
        self.request = self.make_request()
        overflow = self.run_pilot('overflow')
        self.assertEqual(overflow['observations'][0]['reason'], 'OUTPUT_LIMIT')
        self.assertEqual(overflow['selected_outcome'], 'DEBT_BLOCKED')
        self.assertTrue(verify_foreign_pilot(self.target, overflow, self.home / 'overflow'))
        slow = (
            'import unittest, time\nclass TestSimple(unittest.TestCase):\n'
            '    def test_add_one(self): time.sleep(3)\n'
        )
        (self.target / 'tests/test_simple.py').write_text(slow)
        self.commit()
        self.request = self.make_request()
        self.request['timeout'] = 1
        timed = self.run_pilot('timed')
        self.assertEqual(timed['observations'][0]['reason'], 'TIMEOUT')
        self.assertEqual(timed['selected_outcome'], 'DEBT_BLOCKED')
        self.assertTrue(verify_foreign_pilot(self.target, timed, self.home / 'timed'))

    def test_no_host_isolation_authority(self):
        result = self.run_pilot()
        self.assertEqual(result['isolation'], 'PROCESS_BOUNDS_ONLY_NOT_OS_SANDBOX')
        self.assertEqual(result['product_acceptance'], 'BLOCKED_EXTERNAL')
        self.assertEqual(result['authority'], 'NONE')
        self.assertEqual(result['artifacts'][0]['trust'], 'LOCAL_UNATTESTED')
        self.assertNotEqual(result['selected_outcome'], 'PASS_INDEPENDENTLY_ATTESTED')

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'optional pytest adapter not installed')
    def test_two_adapter_real_runners(self):
        self.request = self.make_request(('unittest', 'pytest'))
        result = self.run_pilot()
        self.assertEqual(len(result['observations']), 2)
        self.assertEqual(set(x['adapter'] for x in result['test_linkage']), set(ADAPTERS))
        self.assertEqual(result['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        self.assertTrue(verify_foreign_pilot(self.target, result, self.home / 'evidence'))

    def test_source_receipt_original_one_run_replay(self):
        result = self.run_pilot()
        self.assertEqual(result['source_one_run']['schema'], 'cora-one-run/1')
        self.assertTrue(verify_one(self.target, result['source_one_run']))
        self.assertEqual(result['source_one_run']['catalog_commands_declared'], 0)
        self.assertFalse(result['source_one_run']['release_authorized'])

    def test_log_tamper_is_refuted(self):
        result = self.run_pilot()
        self.assertTrue(verify_foreign_pilot(self.target, result, self.home / 'evidence'))
        file = self.home / 'evidence' / 'pilot-00.log'
        file.write_bytes(file.read_bytes() + b'INJECTED\n')
        with self.assertRaises(ValueError):
            verify_foreign_pilot(self.target, result, self.home / 'evidence')

    def test_skipped_and_empty_cannot_pass(self):
        for i, source in enumerate(('import unittest\n',
                "import unittest\nclass TestSimple(unittest.TestCase):\n    @unittest.skip('non-run')\n    def test_add_one(self): pass\n")):
            (self.target / 'tests/test_simple.py').write_text(source)
            self.commit()
            self.request = self.make_request()
            result = self.run_pilot('bad-' + str(i))
            self.assertEqual(result['selected_outcome'], 'DEBT_BLOCKED')
            self.assertTrue(verify_foreign_pilot(self.target, result, self.home / ('bad-' + str(i))))

    def test_immutable_target_source(self):
        before = self.git('status', '--porcelain')
        result = self.run_pilot()
        self.assertEqual(result['commit'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(before, self.git('status', '--porcelain'))
        self.assertEqual(result['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'optional pytest adapter not installed')
    def test_cli_one_run_foreign_end_to_end(self):
        root = Path(__file__).resolve().parents[1]
        self.request = self.make_request(('unittest', 'pytest'))
        requestfile = self.home / 'request.json'
        requestfile.write_text(json.dumps(self.request))
        reportfile = self.home / 'report.json'
        env = os.environ.copy()
        env['PYTHONPATH'] = str(root / 'src')
        cmd = [sys.executable, '-m', 'cora.cli', 'process-run', str(self.target), '--one-run',
               '--foreign-request', str(requestfile), '--execute-foreign',
               '--evidence-dir', str(self.home / 'evidence'), '--output', str(reportfile)]
        completed = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + '\n' + completed.stderr)
        data = json.loads(reportfile.read_text())
        self.assertEqual(data['selected_outcome'], 'PASS_SCOPED_LOCAL_UNATTESTED')
        replay = subprocess.run([sys.executable, '-m', 'cora.cli', 'verify-process', str(reportfile),
                                 '--repo', str(self.target), '--one-run',
                                 '--evidence-dir', str(self.home / 'evidence')],
                                cwd=root, env=env, text=True, capture_output=True)
        self.assertEqual(replay.returncode, 0, replay.stdout + '\n' + replay.stderr)
        self.assertTrue(verify_foreign_pilot(self.target, data, self.home / 'evidence'))

    def test_unchanged_original_one_run_path(self):
        from cora.one_run import run_one
        with_request = self.run_pilot()
        baseline = run_one(self.target, 'HEAD', process='history')
        self.assertEqual(baseline['schema'], with_request['source_one_run']['schema'])
        self.assertTrue(verify_one(self.target, baseline))
        self.assertEqual(baseline['runtime_status'], 'NOT_RUN')


if __name__ == '__main__':
    unittest.main()
