"""Falsifiers for the explicitly closed CORA operational observation universe."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import verify_operational_equivalence as op

ROOT = Path(__file__).resolve().parents[1]
MERGED_PR69_BASE = "8ed7d6be48d2aac1d9a232b10ebc747da3e0f5a4"


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        text=True, timeout=90, check=False)
    if result.returncode:
        raise RuntimeError("Git fixture failed: " + result.stderr[:400])
    return result.stdout.strip()


def captured(stdout=b"same\n", *, code=0, stderr=b""):
    return {"exit_code": code, "stdout": stdout, "stderr": stderr}


class StrictFiniteUniverseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("complete original Git checkout required")
        cls.head = git(ROOT, "rev-parse", "HEAD")

    def test_full_atlas_and_fixed_native_denominator(self):
        cases, contract = op.universe(ROOT, MERGED_PR69_BASE, self.head)
        self.assertEqual(len(cases), 77)
        self.assertEqual(len(set(cases)), 77)
        self.assertEqual(sum(case.startswith("help:") for case in cases), 71)
        self.assertEqual(cases[-6:], list(op.NATIVE))
        self.assertEqual(contract["global_product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(contract["authority"], "NONE")
        self.assertEqual(contract["runner_environment"], op.ENVIRONMENT)
        self.assertEqual(contract["required_negative_controls"],
                         list(op.NEGATIVE_CONTROLS))
        self.assertEqual(contract["excluded_obligations"], list(op.EXCLUDED))

    def test_strict_per_observation_equality_not_percentage_compensation(self):
        cases = ["help:snapshot", "version", "graph-pinned"]
        before = {case: captured() for case in cases}
        after = copy.deepcopy(before)
        result = op.compare(cases, before, after)
        self.assertEqual(result["denominator"], 3)
        self.assertEqual(result["passed"], 3)
        self.assertEqual(result["status"],
                         "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS")
        for changed, expected in (
            (captured(stdout=b"changed\n"), "help:snapshot"),
            (captured(code=1), "help:snapshot"),
            (captured(stderr=b"warning"), "help:snapshot"),
            (captured(stdout=b""), "help:snapshot"),
        ):
            with self.subTest(changed=changed):
                altered = copy.deepcopy(after)
                altered["help:snapshot"] = changed
                result = op.compare(cases, before, altered)
                self.assertEqual(result["failed"], [expected])
                self.assertEqual(result["passed"], 2)
                self.assertEqual(result["status"], "REFUTED_FINITE_OBSERVATIONS")
        with self.assertRaisesRegex(ValueError, "missing, duplicate or invented"):
            op.compare(cases, before, {"version": captured()})
        with self.assertRaisesRegex(ValueError, "missing, duplicate or invented"):
            op.compare(cases + ["version"], before, after)
        corrupted = copy.deepcopy(after)
        corrupted["version"] = {"exit_code": True, "stdout": b"same\n",
                                "stderr": b""}
        with self.assertRaisesRegex(ValueError, "malformed"):
            op.compare(cases, before, corrupted)

    def test_attacker_cannot_prune_contract_commands_or_native_cases(self):
        original = op.read_json
        def malicious(repo, sha, path):
            doc = original(repo, sha, path)
            if path == op.CONTRACT:
                doc = copy.deepcopy(doc)
                doc["native_cases"].pop()
            return doc
        with patch.object(op, "read_json", side_effect=malicious):
            with self.assertRaisesRegex(ValueError, "incomplete or unsafe"):
                op.universe(ROOT, MERGED_PR69_BASE, self.head)
        def missing(repo, sha, path):
            doc = original(repo, sha, path)
            if path == op.ATLAS and sha == self.head:
                doc = copy.deepcopy(doc)
                doc["commands"].pop()
            return doc
        with patch.object(op, "read_json", side_effect=missing):
            with self.assertRaisesRegex(ValueError, "missing, duplicate"):
                op.universe(ROOT, MERGED_PR69_BASE, self.head)
        def renamed(repo, sha, path):
            doc = original(repo, sha, path)
            if path == op.ATLAS and sha == self.head:
                doc = copy.deepcopy(doc)
                doc["commands"][0]["command"] = "forged-command"
            return doc
        with patch.object(op, "read_json", side_effect=renamed):
            with self.assertRaisesRegex(ValueError, "universe changed"):
                op.universe(ROOT, MERGED_PR69_BASE, self.head)


    def test_distinct_baseline_and_explicit_native_consent_required(self):
        with self.assertRaisesRegex(ValueError, "explicit"):
            op.run(ROOT, MERGED_PR69_BASE, self.head, execute_pinned_native=False)
        with self.assertRaisesRegex(ValueError, "distinct"):
            op.run(ROOT, self.head, self.head, execute_pinned_native=True)
        self.assertEqual(op.arguments("stress-128", ROOT,
                         MERGED_PR69_BASE, ROOT / "contract.json"),
                         ["stress", "--seed", "883", "--cases", "128"])
        with self.assertRaisesRegex(ValueError, "unregistered"):
            op.arguments("rm-repository", ROOT,
                         MERGED_PR69_BASE, ROOT / "contract.json")

    def test_physical_committed_help_mutant_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", "--detach", self.head)
            good = op.execute(clone, ["snapshot", "--help"])
            self.assertEqual(good["exit_code"], 0)
            cli = clone / "src/cora/cli.py"
            before = cli.read_text("utf-8")
            old = "sub.add_parser('snapshot')"
            self.assertEqual(before.count(old), 1)
            cli.write_text(before.replace(
                old, "sub.add_parser('snapshot', description='ADVERSARIAL HELP DRIFT')"),
                encoding="utf-8")
            git(clone, "add", "src/cora/cli.py")
            git(clone, "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: distinguish observed CLI help from previous Git")
            bad = op.execute(clone, ["snapshot", "--help"])
            self.assertEqual(bad["exit_code"], 0)
            self.assertIn(b"ADVERSARIAL HELP DRIFT", bad["stdout"])
            proof = op.compare(["help:snapshot"],
                               {"help:snapshot": good},
                               {"help:snapshot": bad})
            self.assertEqual(proof["status"], "REFUTED_FINITE_OBSERVATIONS")
            self.assertEqual(proof["failed"], ["help:snapshot"])


class EndToEndOperationalReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("complete original Git checkout required")
        cls.head = git(ROOT, "rev-parse", "HEAD")
        cls.receipt = op.run(ROOT, MERGED_PR69_BASE, cls.head,
                             execute_pinned_native=True)

    def test_all_observations_measured_and_no_global_promotion(self):
        receipt = self.receipt
        self.assertEqual(receipt["base"], MERGED_PR69_BASE)
        self.assertEqual(receipt["head"], self.head)
        self.assertEqual(receipt["denominator"], 77)
        self.assertEqual(receipt["observed"], 77)
        self.assertEqual(receipt["passed"], 77)
        self.assertEqual(receipt["failed"], [])
        self.assertEqual(receipt["status"],
                         "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS")
        self.assertEqual(receipt["product_global_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(receipt["independent_reviewer"], "NOT_ATTESTED")
        self.assertEqual(receipt["authorization"], "NONE")
        self.assertEqual(receipt["scoped_dod"]["G_OP"], "PENDING_REPLAY")
        self.assertEqual(receipt["runner_environment"]["working_directory"],
                         str(ROOT.resolve()))
        self.assertTrue(receipt["runner_environment"]["python"])
        self.assertEqual(receipt["runner_environment"]["pythonhashseed"], "0")
        self.assertEqual(len({row["case"] for row in receipt["rows"]}), 77)
        self.assertEqual(len([row for row in receipt["rows"]
                              if row["case"].startswith("help:")]), 71)

    def test_exact_receipt_replay_and_forged_status_rejected(self):
        self.assertTrue(op.verify(ROOT, self.receipt,
                                  execute_pinned_native=True))
        tampered = copy.deepcopy(self.receipt)
        tampered["passed"] = 78
        with patch.object(op, "run", return_value=self.receipt):
            with self.assertRaisesRegex(ValueError, "does not independently replay"):
                op.verify(ROOT, tampered, execute_pinned_native=True)


class OriginalGitP4ContractionTests(unittest.TestCase):
    """Source-exact P3/P4 native receipt parity, not an external acceptance verdict."""

    def test_original_git_before_after_receipt_and_physical_negative(self):
        if not (ROOT / '.git').exists():
            self.skipTest('full original Git history required')
        base = 'cd897deb297a18fae9bf2910e2a7474fe04d6beb'
        # The historic P4 observation must remain immutable after future work.
        head = '987de6407c75a3978ca41cf544d098ff33bf6268'
        hardened = 'd59eb015d5627971037fca26628a04f6ef23dc00'
        before_final = '2fd4167a4b797e8cd19baa92784294eb324fa63c'
        final = '85b3bbd8196c5d721b234ee39ea47b81d3d9f525'
        for path, before, after in (
            ('src/cora/continuous.py',
             '66150559c14f89aeb0f84cca6a50d00828ee6161',
             '517c1c53ac4c398efb7d283ba93a2700ede39cc2'),
            ('src/cora/git_snapshot.py',
             '1cad583f29c31791ae43b50f115785ee35670c05',
             'a32fddb65b2b4bdd05fe905094156183744d6e7f'),
        ):
            self.assertEqual(git(ROOT, 'rev-parse', base + ':' + path), before)
            self.assertEqual(git(ROOT, 'rev-parse', head + ':' + path), after)
        test_path = 'tests/test_change_lifecycle_governance.py'
        self.assertEqual(git(ROOT, 'rev-parse', base + ':' + test_path),
                         git(ROOT, 'rev-parse', head + ':' + test_path))
        with tempfile.TemporaryDirectory(prefix='cora-p4-original-native-') as td:
            root = Path(td)
            fixture = root / 'fixture'
            fixture.mkdir()
            git(fixture, 'init', '-q')
            git(fixture, 'config', 'user.name', 'fixture')
            git(fixture, 'config', 'user.email', 'fixture@example.invalid')
            (fixture / 'example.py').write_text('print(1)\n')
            git(fixture, 'add', '-A')
            git(fixture, 'commit', '-qm', 'base')
            (fixture / '.cora').mkdir()
            (fixture / '.cora/continuous-policy.json').write_text(json.dumps({
                'schema': 'cora-continuous-policy/1', 'version': 1,
                'max_changed_paths': 20, 'high_risk_prefixes': ['.github/workflows', '.cora'],
                'high_risk_paths': ['GOVERNANCE.md', 'pyproject.toml'],
                'required_human_roles': ['MAINTAINER', 'INDEPENDENT_SECURITY_REVIEWER'],
                'review_processes': ['source', 'history', 'debt', 'verification']}))
            git(fixture, 'add', '-A')
            git(fixture, 'commit', '-qm', 'policy')
            target_base = git(fixture, 'rev-parse', 'HEAD')
            (fixture / 'example.py').write_text('print(2)\n')
            git(fixture, 'add', '-A')
            git(fixture, 'commit', '-qm', 'candidate')
            target_head = git(fixture, 'rev-parse', 'HEAD')
            runner = (
                'import json,sys\nfrom pathlib import Path\n'
                'from cora.continuous import evaluate,agent_check\n'
                'repo,base,head,out=sys.argv[1:]\n'
                'receipt=evaluate(Path(repo),base,head)\n'
                "claim={'schema':'cora-agent-proposal/1','agent_id':'negative',"
                "'base_commit':base,'head_commit':head,'intent':'unsafe',"
                "'changed_paths':['forged.py'],'test_claims':[],"
                "'unknowns':[],'authorized_action':'DELETE'}\n"
                "try:\n agent_check(Path(repo),claim)\n decision='ACCEPTED_IN_ERROR'\n"
                "except ValueError:\n decision='DENIED'\n"
                "Path(out).write_text(json.dumps({'receipt':receipt,'denial':decision},sort_keys=True))\n"
                "print('OK')\n"
            )
            def execute(checkout, label):
                effect = root / (label + '.json')
                env = {**os.environ, 'PYTHONPATH': str(checkout / 'src'),
                       'PYTHONNOUSERSITE': '1', 'PYTHONHASHSEED': '0'}
                run = subprocess.run(
                    [sys.executable, '-c', runner, str(fixture), target_base,
                     target_head, str(effect)], cwd=checkout, env=env,
                    capture_output=True, timeout=40, check=False)
                self.assertEqual(run.returncode, 0, run.stderr)
                return {'exit_code': run.returncode, 'stdout': run.stdout,
                        'stderr': run.stderr,
                        'effects': {'receipt.json': effect.read_bytes()}}
            def clone_at(sha, label):
                checkout = root / label
                git(ROOT, 'clone', '--no-local', '-q', '--', str(ROOT), str(checkout))
                git(checkout, 'checkout', '-q', '--detach', sha)
                return checkout
            earlier, later = clone_at(base, 'earlier'), clone_at(head, 'later')
            a, b = execute(earlier, 'earlier'), execute(later, 'later')
            self.assertEqual(a, b)
            self.assertEqual(json.loads(b['effects']['receipt.json'])['denial'], 'DENIED')
            c = execute(clone_at(hardened, 'hardened'), 'hardened')
            self.assertEqual(b, c)  # same persistent receipt and denial
            test = [{'id': 'p4-native-policy', 'path': test_path}]
            receipt = op.native_counterfactual(ROOT, base, head, test,
                 {'p4-native-policy': a}, {'p4-native-policy': b})
            self.assertEqual(receipt['status'], 'PASS_SCOPED_FINITE_NATIVE')
            self.assertTrue(op.verify_native_counterfactual(ROOT, receipt, test,
                {'p4-native-policy': a}, {'p4-native-policy': b}))
            followon = op.native_counterfactual(ROOT, head, hardened, test,
                {'p4-native-policy': b}, {'p4-native-policy': c})
            self.assertEqual(followon['status'], 'PASS_SCOPED_FINITE_NATIVE')
            self.assertTrue(op.verify_native_counterfactual(ROOT, followon, test,
                {'p4-native-policy': b}, {'p4-native-policy': c}))
            before_last = execute(clone_at(before_final, 'before-final'), 'before-final')
            after_last = execute(clone_at(final, 'final'), 'final')
            self.assertEqual(before_last, after_last)
            last = op.native_counterfactual(ROOT, before_final, final, test,
                {'p4-native-policy': before_last}, {'p4-native-policy': after_last})
            self.assertEqual(last['status'], 'PASS_SCOPED_FINITE_NATIVE')
            self.assertTrue(op.verify_native_counterfactual(ROOT, last, test,
                {'p4-native-policy': before_last}, {'p4-native-policy': after_last}))
            mutant = clone_at(final, 'mutant')
            file = mutant / 'src/cora/git_snapshot.py'
            original = file.read_text('utf-8')
            marker = '    return proc.stdout\n\n\ndef _batch('
            self.assertEqual(original.count(marker), 1)
            file.write_text(original.replace(marker,
                "    if args and args[0] == 'diff':\n        return b''\n"
                '    return proc.stdout\n\n\ndef _batch(', 1), encoding='utf-8')
            git(mutant, 'add', 'src/cora/git_snapshot.py')
            git(mutant, '-c', 'user.name=fixture', '-c',
                'user.email=fixture@example.invalid', 'commit', '-qm', 'native physical mutant')
            mutant_head = git(mutant, 'rev-parse', 'HEAD')
            corrupted = execute(mutant, 'mutated')
            self.assertEqual((after_last['exit_code'], after_last['stdout'], after_last['stderr']),
                             (corrupted['exit_code'], corrupted['stdout'], corrupted['stderr']))
            self.assertNotEqual(after_last['effects'], corrupted['effects'])
            bad = op.native_counterfactual(mutant, final, mutant_head, test,
                 {'p4-native-policy': after_last}, {'p4-native-policy': corrupted})
            self.assertEqual(bad['status'], 'FAIL_OBSERVED')


    def test_p4_net_runtime_source_contraction_and_no_second_executor(self):
        if not (ROOT / '.git').exists():
            self.skipTest('full original Git history required')
        base = 'cd897deb297a18fae9bf2910e2a7474fe04d6beb'
        p4 = '987de6407c75a3978ca41cf544d098ff33bf6268'
        hardened = 'd59eb015d5627971037fca26628a04f6ef23dc00'
        final = '85b3bbd8196c5d721b234ee39ea47b81d3d9f525'
        paths = ('src/cora/continuous.py', 'src/cora/git_snapshot.py')
        epochs = {sha: {path: op.git(ROOT, 'show', sha + ':' + path)
                        for path in paths} for sha in (base, p4, hardened, final)}
        measured = {sha: sum(len(data) for data in files.values())
                    for sha, files in epochs.items()}
        self.assertLess(measured[p4], measured[base])
        self.assertLess(measured[hardened], measured[p4])
        self.assertLess(measured[final], measured[hardened])
        before, after = epochs[base][paths[0]], epochs[final][paths[0]]
        self.assertIn(b'def _git(', before)
        self.assertNotIn(b'def _git(', after)
        self.assertNotIn(b'subprocess.run(', after)  # all Git process owners retired
        self.assertIn(b'from .git_snapshot import git', after)
        self.assertIn(b'invalid bounded Git output budget', epochs[final][paths[1]])
        self.assertEqual(set(git(ROOT, 'diff', '--name-only', p4, final,
                                 '--', 'src/cora').splitlines()), set(paths))


if __name__ == "__main__":
    unittest.main()
