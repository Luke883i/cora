"""PR33: measurable original-Git fixture observations and anti-promotion mutants."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora import ci_repro

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class ReproducibilityMetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("Original Git checkout needed")
        cls.sha = git(ROOT, "rev-parse", "HEAD")

    def test_exact_git_reticulum_noncompensatory(self):
        original = ci_repro.original_contract(ROOT, self.sha)
        self.assertEqual(original["authority"], "NONE")
        self.assertEqual(len(original["nodes"]), 21)
        self.assertEqual(original["metrics"]["min_repetitions_per_group_per_python"], 3)
        self.assertEqual(original["metrics"]["max_observed_failures"], 0)

    def test_three_real_measurements_without_test_execution_replay_claim(self):
        seen = []
        def success(argv, root, env, timeout):
            seen.append((argv, root, env, timeout))
            return subprocess.CompletedProcess(argv, 0, stdout="Ran 9 tests\nOK\n", stderr="")
        report = ci_repro.run_probe(ROOT, self.sha, group_names=("PR25_GIT_MUTANTS",), execute=success)
        self.assertEqual(report["sample_total"], 3)
        self.assertEqual(report["failures_total"], 0)
        self.assertEqual(len(seen), 3)
        self.assertEqual(report["tree"], git(ROOT, "rev-parse", "HEAD^{tree}"))
        self.assertEqual(report["status"], "PASS_SCOPED_REPEATABILITY_SAMPLE")
        self.assertFalse(report["release_authorized"])
        self.assertEqual(report["root_cause"], "NOT_ATTESTED")
        self.assertTrue(ci_repro.verify_report(report, ROOT, sha=self.sha))

    def test_failures_cannot_be_masked_by_later_success(self):
        calls = [0]
        def intermittent(argv, root, env, timeout):
            calls[0] += 1
            if calls[0] == 2:
                return subprocess.CompletedProcess(
                    argv, 1, stdout="",
                    stderr="ERROR: test_physical_git_atlas_and_identity_mutants (suite.Case)\nValueError: Git read\n")
            return subprocess.CompletedProcess(argv, 0, stdout="OK\n", stderr="")
        report = ci_repro.run_probe(ROOT, self.sha, group_names=("PR26_CAPABILITY_MUTANTS",), execute=intermittent)
        group = report["cohorts"]["PR26_CAPABILITY_MUTANTS"]
        self.assertEqual(group["failures"], 1)
        self.assertEqual(group["observed_failure_rate"], .333333)
        self.assertEqual(report["status"], "FAIL_OBSERVED")
        self.assertEqual(report["failures_total"], 1)
        tampered = copy.deepcopy(report)
        tampered["failures_total"] = 0
        tampered["status"] = "PASS_SCOPED_REPEATABILITY_SAMPLE"
        with self.assertRaisesRegex(ValueError, "masked"):
            ci_repro.verify_report(tampered, ROOT, sha=self.sha)

    def test_diagnostic_runner_blocks_token_forwarding(self):
        seen = []
        prior = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "not-for-child"
        try:
            def fake(argv, root, env, timeout):
                seen.append(env)
                return subprocess.CompletedProcess(argv, 0, stdout="OK", stderr="")
            report = ci_repro.run_probe(ROOT, self.sha, group_names=("PR25_GIT_MUTANTS",), execute=fake)
            self.assertEqual(report["sample_total"], 3)
            self.assertEqual(len(seen), 3)
            self.assertTrue(all("GITHUB_TOKEN" not in x for x in seen))
            self.assertNotIn("not-for-child", json.dumps(report))
        finally:
            if prior is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = prior

    def test_checkout_head_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "checkout HEAD differs"):
            ci_repro.run_probe(ROOT, "0" * 40, execute=lambda *args: None)
        with self.assertRaisesRegex(ValueError, "3-10"):
            ci_repro.run_probe(ROOT, self.sha, repetitions=2, execute=lambda *args: None)
        with self.assertRaisesRegex(ValueError, "unknown, empty"):
            ci_repro.run_probe(ROOT, self.sha, group_names=("FAKE",), execute=lambda *args: None)

    def test_git_committed_contract_edge_and_scope_mutants(self):
        original = json.loads((ROOT / ci_repro.DOD).read_text("utf-8"))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d)
            git(f, "init", "-q")
            target = f / ci_repro.DOD
            target.parent.mkdir(parents=True, exist_ok=True)
            def commit(doc):
                target.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
                git(f, "add", ci_repro.DOD)
                subprocess.run(["git", "-C", str(f), "-c", "user.name=CORA negative oracle",
                                "-c", "user.email=invalid@example.invalid",
                                "commit", "-qm", "physical committed contract"], check=True)
                return git(f, "rev-parse", "HEAD")
            sha = commit(original)
            self.assertEqual(ci_repro.original_contract(f, sha)["global_goal"], "G_QUALIFIED")
            changed = copy.deepcopy(original)
            next(x for x in changed["nodes"] if x["id"] == "G_REPETITION")["depends_on"].pop()
            with self.assertRaisesRegex(ValueError, "mandatory dependency"):
                ci_repro.original_contract(f, commit(changed))
            changed = copy.deepcopy(original)
            next(x for x in changed["nodes"] if x["id"] == "E_RCA_VERIFIED")["scope"] = "SOURCE"
            with self.assertRaisesRegex(ValueError, "mandatory dependency"):
                ci_repro.original_contract(f, commit(changed))


if __name__ == "__main__":
    unittest.main()
