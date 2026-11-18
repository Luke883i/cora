"""Real executed Git-fixture counterexamples not in PR70's 77-observation scope.

These are synthetic target programs executed from original Git checkouts;
they do NOT test CORA's own native runtime.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def command(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout.strip()


class TargetCounterfactual(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "original"
        self.repo.mkdir()
        command(self.repo, "init", "-q")
        command(self.repo, "config", "user.name", "fixture")
        command(self.repo, "config", "user.email", "fixture@example.invalid")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self, msg):
        command(self.repo, "add", "-A")
        command(self.repo, "commit", "-qm", msg)
        return command(self.repo, "rev-parse", "HEAD")

    def checkout(self, rev, target):
        command(self.repo, "worktree", "add", "-q", "--detach", str(target), rev)

    def run_app(self, root, *args):
        return subprocess.run([sys.executable, "app.py", *args], cwd=root,
                              capture_output=True, timeout=15)

    def test_same_exit_stdout_stderr_can_hide_changed_side_effects(self):
        path = self.repo / "app.py"
        path.write_text("from pathlib import Path\nPath('receipt.json').write_text('A')\nprint('OK')\n")
        base = self.commit("baseline with A side effect")
        path.write_text("from pathlib import Path\nPath('receipt.json').write_text('B')\nprint('OK')\n")
        head = self.commit("mutant with different persisted receipt")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        ra, rb = self.run_app(a), self.run_app(b)
        self.assertEqual((ra.returncode, ra.stdout, ra.stderr),
                         (rb.returncode, rb.stdout, rb.stderr))
        self.assertNotEqual((a / "receipt.json").read_bytes(),
                            (b / "receipt.json").read_bytes())

    def test_dynamic_plugin_unobserved_by_direct_import_candidates(self):
        path = self.repo / "app.py"
        path.write_text("import importlib\nimport sys\n"
                        "mod=importlib.import_module(sys.argv[1])\nprint(mod.result())\n")
        (self.repo / "plug.py").write_text("def result():\n    return 'plugin-works'\n")
        base = self.commit("baseline contains dynamically resolved consumer")
        (self.repo / "plug.py").unlink()
        head = self.commit("candidate deletes plugin with no static import")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        good, bad = self.run_app(a, "plug"), self.run_app(b, "plug")
        self.assertEqual(good.returncode, 0)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn(b"No module named", bad.stderr)

    def test_error_path_semantics_recovered_by_negative_input(self):
        path = self.repo / "app.py"
        path.write_text("import sys\n"
                        "if sys.argv[1]=='bad':\n    print('blocked', file=sys.stderr)\n    sys.exit(2)\n"
                        "print('OK')\n")
        base = self.commit("baseline rejects invalid input")
        path.write_text("import sys\n"
                        "if sys.argv[1]=='bad':\n    print('OK')\n    sys.exit(0)\n"
                        "print('OK')\n")
        head = self.commit("candidate silently accepts invalid input")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        self.assertEqual(self.run_app(a, "good").stdout, self.run_app(b, "good").stdout)
        self.assertNotEqual(self.run_app(a, "bad").returncode,
                            self.run_app(b, "bad").returncode)

class P3NativeCounterfactualTests(unittest.TestCase):
    """Committed target mutations executed only in throwaway, local Git clones."""

    def setUp(self):
        from tools import verify_operational_equivalence as op
        self.op = op
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'source'
        self.repo.mkdir()
        command(self.repo, 'init', '-q')
        command(self.repo, 'config', 'user.name', 'fixture')
        command(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'app.py').write_text("def decision():\n    return 'ALLOWED'\n")
        (self.repo / 'oracle.py').write_text(
            "from pathlib import Path\nimport app\n"
            "Path('receipt.txt').write_text(app.decision())\nprint('OK')\n")
        self.base = self.commit('baseline')
        (self.repo / 'app.py').write_text("# innocuous edit\ndef decision():\n    return 'BLOCKED'\n")
        self.head = self.commit('two physical source changes')
        self.tests = [{'id': 'original-native-oracle', 'path': 'oracle.py'}]

    def commit(self, message):
        command(self.repo, 'add', '-A')
        command(self.repo, 'commit', '-qm', message)
        return command(self.repo, 'rev-parse', 'HEAD')

    def run_revision(self, repo, sha):
        dest = Path(self.tmp.name) / ('checkout_' + str(len(list(Path(self.tmp.name).iterdir()))))
        command(repo, 'clone', '--no-local', '-q', '--', str(repo), str(dest))
        command(dest, 'checkout', '-q', '--detach', sha)
        run = subprocess.run([sys.executable, 'oracle.py'], cwd=dest,
                             capture_output=True, timeout=15, check=False)
        effects = {}
        output = dest / 'receipt.txt'
        if output.exists():
            effects['receipt.txt'] = output.read_bytes()
        return {'exit_code': run.returncode, 'stdout': run.stdout,
                'stderr': run.stderr, 'effects': effects}

    def test_real_native_effect_change_and_test_identity(self):
        a = self.run_revision(self.repo, self.base)
        b = self.run_revision(self.repo, self.head)
        self.assertEqual((a['exit_code'], a['stdout'], a['stderr']),
                         (b['exit_code'], b['stdout'], b['stderr']))
        self.assertNotEqual(a['effects'], b['effects'])
        report = self.op.native_counterfactual(
            self.repo, self.base, self.head, self.tests,
            {'original-native-oracle': a}, {'original-native-oracle': b})
        self.assertEqual(report['status'], 'FAIL_OBSERVED')
        self.assertEqual(report['failed'], ['original-native-oracle'])
        self.assertEqual(report['unknown'], [])
        self.assertEqual(report['product_global_status'] if 'product_global_status' in report
                         else report['external_and_runtime_closure'], 'BLOCKED_EXTERNAL')
        self.assertTrue(self.op.verify_native_counterfactual(
            self.repo, report, self.tests, {'original-native-oracle': a},
            {'original-native-oracle': b}))
        forged = dict(report)
        forged['status'] = 'PASS_SCOPED_FINITE_NATIVE'
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            self.op.verify_native_counterfactual(
                self.repo, forged, self.tests, {'original-native-oracle': a},
                {'original-native-oracle': b})
        from cora.evidence import domain_hash
        forged['digest'] = domain_hash('CORA:native-counterfactual:1',
                                      {k:v for k,v in forged.items() if k!='digest'})
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            self.op.verify_native_counterfactual(
                self.repo, forged, self.tests, {'original-native-oracle': a},
                {'original-native-oracle': b})

    def test_unknowns_cannot_qualify_native_success(self):
        a = self.run_revision(self.repo, self.base)
        b = self.run_revision(self.repo, self.head)
        key='original-native-oracle'
        missing = self.op.native_counterfactual(self.repo, self.base, self.head,
                                               self.tests, {key:a}, {})
        self.assertEqual(missing['status'], 'UNKNOWN_INCOMPLETE')
        self.assertEqual(missing['unknown'], [key])
        no_effect = dict(b, effects={})
        absent_effect = self.op.native_counterfactual(
            self.repo, self.base, self.head, self.tests, {key:a}, {key:no_effect})
        self.assertEqual(absent_effect['status'], 'UNKNOWN_INCOMPLETE')
        (self.repo / 'oracle.py').write_text(
            "from pathlib import Path\nimport app\n"
            "Path('receipt.txt').write_text(app.decision())\nprint('MUTATED')\n")
        changed_oracle = self.commit('physical test identity drift')
        drift = self.op.native_counterfactual(
            self.repo, self.base, changed_oracle, self.tests, {key:a}, {key:b})
        self.assertEqual(drift['tests'][0]['status'], 'UNKNOWN_TEST_IDENTITY_DRIFT')
        with self.assertRaisesRegex(ValueError, 'denominator invalid'):
            self.op.native_counterfactual(self.repo, self.base, self.head,
                                          self.tests + self.tests, {key:a}, {key:b})

    def test_ddmin_finds_physical_fault_and_unknown_is_not_pass(self):
        a = self.run_revision(self.repo, self.base)
        executions = []
        def physical_probe(changes):
            # Never memoize a probe: a second call must execute a fresh native
            # checkout to falsify nondeterminism, not replay a cached verdict.
            work = Path(self.tmp.name) / ('patch_' + str(len(executions)))
            command(self.repo, 'clone', '--no-local', '-q', '--', str(self.repo), str(work))
            command(work, 'checkout', '-q', '--detach', self.base)
            prefix = '# innocuous edit\n' if 'noise' in changes else ''
            value = 'BLOCKED' if 'fault' in changes else 'ALLOWED'
            (work / 'app.py').write_text(prefix + "def decision():\n    return '" + value + "'\n")
            if changes:
                command(work, '-c', 'user.name=fixture',
                        '-c', 'user.email=fixture@example.invalid',
                        'add', 'app.py')
                command(work, '-c', 'user.name=fixture',
                        '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'subset physical source mutation')
            head = command(work, 'rev-parse', 'HEAD')
            b = self.run_revision(work, head)
            verdict = ('FAIL' if b['effects'] != a['effects'] else 'PASS')
            executions.append((changes, head, verdict))
            return verdict
        result = self.op.minimize_native_failure(['noise', 'fault'],
                                                  physical_probe, max_probes=64)
        self.assertEqual(result['status'], 'FAIL_1_MINIMAL_NATIVE_WITNESS')
        self.assertEqual(result['minimized'], ['fault'])
        self.assertEqual(len(executions), len(result['trials']) * 2)
        self.assertGreaterEqual(len({x[1] for x in executions}), 2)
        self.assertFalse(result['safe_deletion'])
        flaky = iter(['FAIL', 'PASS'])
        unknown = self.op.minimize_native_failure(['fault'],
                     lambda _: next(flaky), max_probes=4)
        self.assertEqual(unknown['status'], 'UNKNOWN_OR_NOT_REPRODUCED')
        with self.assertRaisesRegex(ValueError, 'oracle or budget invalid'):
            self.op.minimize_native_failure(['fault', 'fault'], physical_probe)



if __name__ == "__main__":
    unittest.main()
