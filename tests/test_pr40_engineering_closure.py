"""PR40 original-Git falsifiers for knowledge convergence, source debt and 10M model."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import verify_engineering_closure as ekc

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError("original-Git fixture failed: " + result.stderr[:1000])
    return result.stdout.strip()


class EngineeringKnowledgeClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("complete original Git checkout required")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.doc = ekc.contract_at(ROOT, cls.sha)

    def test_reuse_not_new_orchestrator_and_exact_source_census(self):
        report = ekc.analyze(ROOT, self.sha)
        self.assertEqual(report["commit"], self.sha)
        self.assertEqual(report["counts"]["cli"], 71)
        self.assertGreater(report["counts"]["modules"], 50)
        self.assertGreater(report["counts"]["dynamic_callsite_indicators"], 0)
        self.assertEqual(report["host_enforcement"], "BLOCKED_EXTERNAL")
        self.assertEqual(report["dynamic_execution"], "NOT_EXECUTED_BY_STATIC_AUDIT")
        self.assertEqual(report["authority"], "NONE")
        self.assertTrue(ekc.verify_report(ROOT, report))

    def test_report_tampering_and_source_promotions_refused(self):
        report = ekc.analyze(ROOT, self.sha)
        for field, value in (
            ("host_enforcement", "ATTESTED"),
            ("product_qualified", True),
            ("dynamic_execution", "FULLY_COVERED"),
        ):
            fake = copy.deepcopy(report)
            fake[field] = value
            with self.assertRaisesRegex(ValueError, "does not replay"):
                ekc.verify_report(ROOT, fake)

    def test_preregistered_faults_and_deterministic_digest(self):
        a = ekc.stress(self.doc, sessions=1, cases_per_session=2000)
        b = ekc.stress(self.doc, sessions=1, cases_per_session=2000)
        self.assertEqual(a, b)
        self.assertEqual(a["cases"], 2000)
        self.assertEqual(a["preregistered_masks"], 1471)
        self.assertEqual(a["observed_singles"], 14)
        self.assertEqual(a["observed_pairs"], 91)
        self.assertEqual(a["mismatches"], 0)
        self.assertEqual(a["unsafe_promotions"], 0)
        self.assertEqual(a["status"], "PARTIAL_FINITE_MODEL")
        self.assertEqual(a["real_git_mutants"], 0)
        self.assertEqual(a["host_and_reviewer"], "BLOCKED_EXTERNAL")

    def test_deliberate_model_regression_is_detected_by_separate_oracle(self):
        with patch.object(ekc, "_model", return_value=("MODEL_ELIGIBLE_UNATTESTED", "APPROVED")):
            result = ekc.stress(self.doc, sessions=1, cases_per_session=1471)
        self.assertGreater(result["mismatches"], 0)
        self.assertGreater(result["unsafe_promotions"], 0)
        self.assertEqual(result["status"], "REFUTED")

    def test_external_dod_scope_and_temporal_doc_physical_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "fixture"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            contract = clone / ekc.CONTRACT
            original = json.loads(contract.read_text("utf-8"))
            altered = copy.deepcopy(original)
            next(x for x in altered["nodes"] if x["id"] == "E_INDEPENDENT_REVIEW")["scope"] = "SOURCE"
            contract.write_text(json.dumps(altered, indent=2) + "\n", "utf-8")
            git(clone, "add", ekc.CONTRACT)
            git(clone, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: external reviewer self-certification")
            with self.assertRaisesRegex(ValueError, "scope"):
                ekc.contract_at(clone, git(clone, "rev-parse", "HEAD"))
            git(clone, "checkout", "-q", self.sha)
            readme = clone / "README.md"
            readme.write_text(readme.read_text("utf-8") +
                              "\nThe PR38 candidate is the current product.\n", "utf-8")
            git(clone, "add", "README.md")
            git(clone, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: current documentation reverts to old PR38")
            with self.assertRaisesRegex(ValueError, "chronology drift"):
                ekc.analyze(clone, "HEAD")

    def test_original_git_mutants_never_clone_with_local_object_transport(self):
        # Source-only guard on all committed tests; no runtime attestation.
        import ast
        filenames = git(ROOT, "ls-tree", "-r", "--name-only", self.sha, "--", "tests")
        inspected = 0
        for path in filenames.splitlines():
            if not (path.startswith("tests/") and path.endswith(".py")):
                continue
            syntax = ast.parse(git(ROOT, "show", self.sha + ":" + path),
                               filename=path)
            for node in ast.walk(syntax):
                if not isinstance(node, ast.Call):
                    continue
                literals = []
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        literals.append(arg.value)
                    elif isinstance(arg, (ast.List, ast.Tuple)):
                        literals.extend(v.value for v in arg.elts
                                        if isinstance(v, ast.Constant)
                                        and isinstance(v.value, str))
                if "clone" in literals:
                    inspected += 1
                    self.assertNotIn("--local", literals,
                                     path + ":" + str(node.lineno)
                                     + " original-Git hardlink clone is forbidden")
        self.assertGreaterEqual(inspected, 16)

    def test_declared_external_proof_is_not_self_signed_source(self):
        self.assertEqual(
            next(n for n in self.doc["nodes"] if n["id"] == "G_EXTERNAL_EKC")["proof"],
            "INDEPENDENT_OPERATOR_REQUIRED")
        self.assertEqual(
            next(n for n in self.doc["nodes"] if n["id"] == "G_ENGINEERING_KNOWLEDGE")["proof"],
            "INDEPENDENT_OPERATOR_REQUIRED")

    def test_source_only_dod_never_authenticates_external_leaf(self):
        by = {n["id"]: n for n in self.doc["nodes"]}
        self.assertEqual(by["G_ENGINEERING_KNOWLEDGE"]["scope"], "EXTERNAL")
        self.assertEqual(by["G_SOURCE_EKC"]["scope"], "SOURCE")
        self.assertEqual(self.doc["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(self.doc["authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
