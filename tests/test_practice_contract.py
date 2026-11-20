"""Adversarial practice contract tests; no synthetic PASS for editorial quality."""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.practice_contract import PRACTICES, classify, project, verify


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class PracticeContractTests(unittest.TestCase):
    def test_all_ten_historical_practices_present_in_semantic_order(self):
        self.assertEqual([int(p[1]) for p in PRACTICES], list(range(48, 58)))
        report = classify(["src/cora/engine.py"])
        self.assertEqual(len(report["obligations"]), 10)
        self.assertEqual(report["editorial_refactor"]["state"], "REVIEW_REQUIRED")
        self.assertEqual(report["external_approval"], "NONE")
        self.assertFalse(report["runtime_observed"])
        self.assertTrue(next(x for x in report["obligations"]
                             if x["id"] == "P53_CROSS_DOCUMENT")["applicable"])

    def test_mutation_matrix_rejects_invented_path_and_spurious_release(self):
        for path in ("/etc/passwd", "../escape", "a/../b", "a\\b", "x\x00y"):
            with self.subTest(path=repr(path)), self.assertRaises(ValueError):
                classify([path])
        empty = classify([])
        self.assertFalse(any(p["applicable"] for p in empty["obligations"]))
        self.assertEqual(empty["editorial_refactor"]["state"], "NOT_TRIGGERED")
        readme = classify(["README.md"])
        self.assertTrue(readme["editorial_refactor"]["state"] == "REVIEW_REQUIRED")
        self.assertFalse(next(p for p in readme["obligations"]
                              if p["id"] == "P55_SUPPLY_CHAIN")["applicable"])
        release = classify(["pyproject.toml"])
        self.assertTrue(next(p for p in release["obligations"]
                             if p["id"] == "P55_SUPPLY_CHAIN")["applicable"])

    def test_real_git_first_parent_replay_and_tampered_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            git(root, "init", "-q")
            git(root, "config", "user.name", "CORA fixture")
            git(root, "config", "user.email", "fixture@example.invalid")
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-qm", "baseline")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
            git(root, "add", "src/app.py")
            git(root, "commit", "-qm", "implementation")
            sha = git(root, "rev-parse", "HEAD")
            receipt = project(root, sha)
            self.assertEqual(receipt["changed_paths"], ["src/app.py"])
            self.assertEqual(receipt["commit"], sha)
            self.assertTrue(verify(root, receipt))
            for change in ("digest", "commit", "runtime_observed"):
                mutant = copy.deepcopy(receipt)
                mutant[change] = True
                with self.subTest(change=change), self.assertRaises(ValueError):
                    verify(root, mutant)
