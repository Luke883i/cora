"""Actual Git-commit mutations against PR-21 source/semantic proof obligations.

No runtime sandbox or independent reviewer is certified by these disposable
fixtures. Every negative commits changed bytes and replays the target revision.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/verify_claim_evidence.py"
spec = importlib.util.spec_from_file_location("cora_documentation_proofs", MODULE)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def fixture(folder: Path) -> Path:
    target = folder / "repo"
    subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--local",
                    "--no-hardlinks", str(ROOT), str(target)],
                   capture_output=True, text=True, check=True, timeout=40)
    git(target, "checkout", "--force", "--detach", git(ROOT, "rev-parse", "HEAD"))
    git(target, "config", "user.name", "CORA fixture")
    git(target, "config", "user.email", "fixture@example.invalid")
    return target


def mutate_and_commit(root: Path, path: str, change) -> None:
    target = root / path
    original = target.read_text("utf-8")
    altered = change(original)
    if altered == original:
        raise AssertionError("fixture mutation did not change bytes: " + path)
    target.write_text(altered, "utf-8")
    git(root, "add", "--", path)
    git(root, "commit", "-q", "-m", "fixture: deliberately refute source claim")


class RevisionBoundDocumentationTests(unittest.TestCase):
    def test_01_source_graph_and_external_cut(self):
        result = proof.inspect(ROOT)
        self.assertEqual(result["source_status"], "PASS_SCOPED_SOURCE", result["errors"])
        self.assertEqual(result["source_claim_count"], 18)
        self.assertEqual([x["node"] for x in result["source_claims"]],
                         [f"S{i:02d}" for i in range(1, 19)])
        self.assertEqual(result["governed_status"], "BLOCKED_EXTERNAL")
        self.assertFalse(result["host_review_attested"])
        self.assertFalse(result["test_execution_attested_by_this_script"])
        self.assertEqual(result["authorization"], "NONE")
        self.assertEqual(result["external_obligations"],
                         {"E01": "NOT_OBSERVED", "E02": "NOT_OBSERVED",
                          "E03": "NOT_ATTESTED"})
        self.assertLessEqual(result["git_subprocesses"], 6)
        self.assertEqual(result, proof.inspect(ROOT))
        self.assertEqual({x["source_revision"] for x in result["source_claims"]},
                         {result["commit"]})

    def test_02_real_committed_semantic_and_code_mutants(self):
        def json_change(callback):
            def apply(text):
                doc = json.loads(text)
                callback(doc)
                return json.dumps(doc, indent=2) + "\n"
            return apply

        cases = [
            ("explicit-product-falsehood", "README.md",
             lambda s: s + "\nCORA is a coding agent.\n",
             "semantic-contradiction:CODING_AGENT_PROMOTION:README.md"),
            ("cross-document-contradiction", "docs/ARCHITECTURE.md",
             lambda s: s + "\nCORA automatically deletes source code.\n",
             "semantic-contradiction:AUTOMATIC_DELETION_PROMOTION:docs/ARCHITECTURE.md"),
            ("source-intent-disconnected", "src/cora/continuous.py",
             lambda s: s.replace('"intent_digest": intent_digest',
                                 '"unverified_purpose": intent_digest', 1),
             "S05-S12:actual-intent-binding-or-replay-missing"),
            ("parser-intent-disconnected", "src/cora/cli.py",
             lambda s: s.replace("'--intent'", "'--unbound-claim'"),
             "S04-S05:documented-cli-parser-missing"),
            ("contract-claim-refuted", "cora.documentation-proofs.json",
             json_change(lambda j: j["nodes"][0].update(
                 {"readme_phrase": "CORA autonomously writes all software"})),
             "readme-claim-not-supported:S01"),
            ("contract-falsifier-deleted", "cora.documentation-proofs.json",
             json_change(lambda j: j["nodes"][5].update({"falsifier": ""})),
             "missing-falsifier:S06"),
            ("reticular-external-omitted", "cora.documentation-dod.json",
             json_change(lambda j: next(x for x in j["nodes"]
                 if x["id"] == "G_DOC_ACCEPTED")["depends_on"].remove("E03")),
             "S09:noncompensatory-dod-tampered"),
            ("historic-audit-rewritten", "docs/AUDIT_PR18_MAIN.md",
             lambda s: s + "\nRetroactively approved.\n",
             "S10:historical-blob-mutated:docs/AUDIT_PR18_MAIN.md"),
            ("changelog-current-omitted", "CHANGELOG.md",
             lambda s: s.replace("PR-21", "undocumented revision"),
             "H2:post-pr21-chronology-stale"),
            ("generic-ci-intent", ".github/workflows/ci-convergence.yml",
             lambda s: s.replace("github.event.pull_request.title || github.event.head_commit.message",
                                 "'This is always a generic R1-R4 change'"),
             "H3:change-specific-intent-not-replayed"),
            ("ci-proof-dropped", ".github/workflows/ci-documentation.yml",
             lambda s: s.replace("tools/verify_claim_evidence.py",
                                 "tools/fabricated_verification.py"),
             "S15:missing-actual-falsification-ci"),
            ("cross-document-release-falsehood", "docs/RELEASE.md",
             lambda s: s + "\nCORA is a stable API.\n",
             "semantic-contradiction:STABLE_API_PROMOTION:docs/RELEASE.md"),
            ("package-version-drift", "pyproject.toml",
             lambda s: s.replace('version = "1.0.0a4"', 'version = "1.0.0a9"'),
             "S01-S16:package-release-source-disagreement"),
        ]
        for name, path, change, expected in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as td:
                repo = fixture(Path(td))
                mutate_and_commit(repo, path, change)
                outcome = proof.inspect(repo)
                self.assertIn(expected, outcome["errors"], outcome)
                self.assertEqual(outcome["source_status"], "REFUTED_SOURCE")
                self.assertEqual(outcome["governed_status"], "BLOCKED_EXTERNAL")
                self.assertEqual(outcome["authorization"], "NONE")

    def test_03_worktree_drift_not_promoted_to_committed_truth(self):
        with tempfile.TemporaryDirectory() as td:
            repo = fixture(Path(td))
            baseline = proof.inspect(repo)
            with (repo / "README.md").open("a", encoding="utf-8") as f:
                f.write("\nCORA is a coding agent.\n")
            self.assertEqual(proof.inspect(repo), baseline)
            mutate_and_commit(repo, "README.md",
                lambda s: s + "\nCORA automatically deletes code.\n")
            changed = proof.inspect(repo)
            self.assertNotEqual(changed["commit"], baseline["commit"])
            self.assertNotEqual(changed["receipt_sha256"], baseline["receipt_sha256"])

    def test_04_stale_or_forged_receipt_fails_replay(self):
        with tempfile.TemporaryDirectory() as td:
            repo = fixture(Path(td))
            original = proof.inspect(repo)
            report_path = Path(td) / "receipt.json"
            report_path.write_text(json.dumps(original), "utf-8")
            def cli(*args):
                return subprocess.run(["python", str(MODULE), "--repo", str(repo),
                                       "--verify-report", str(report_path), *args],
                                      capture_output=True, text=True, timeout=40)
            self.assertEqual(cli().returncode, 0)
            forged = dict(original)
            forged["authorization"] = "MERGE"
            report_path.write_text(json.dumps(forged), "utf-8")
            self.assertEqual(cli().returncode, 2)
            report_path.write_text(json.dumps(original), "utf-8")
            mutate_and_commit(repo, "README.md",
                lambda s: s + "\nCORA is a coding agent.\n")
            self.assertEqual(cli().returncode, 2)

    def test_05_missing_source_baseline_is_debt_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "partial"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.name", "CORA fixture")
            git(repo, "config", "user.email", "fixture@example.invalid")
            (repo / "README.md").write_text("Unrelated isolated repository\n", "utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-q", "-m", "isolated")
            with self.assertRaises(ValueError):
                proof.inspect(repo)


if __name__ == "__main__":
    unittest.main()
