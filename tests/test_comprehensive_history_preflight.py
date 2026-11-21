"""PR90 P0: physical Git history distinctions; ZIP source never becomes Git proof."""
from __future__ import annotations
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.integrated_run import (
    ComprehensiveHistoryUnavailable, preflight_comprehensive_history, run_integrated
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.PIPE, text=True
    ).strip()


class ComprehensiveHistoryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cora-history-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_git(self, *, count=1, historical_register=False):
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "user.name", "CORA Test")
        for i in range(count):
            (self.root / "asset.txt").write_text(f"commit {i}\n", encoding="utf-8")
            if historical_register:
                path = self.root / ".cora/assurance/history/pr01-37-commit-diff-audit.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"not":"original history"}\n', encoding="utf-8")
            git(self.root, "add", ".")
            git(self.root, "commit", "-qm", f"fixture {i}")

    def test_zip_directory_fails_typed_with_safe_fallback(self):
        (self.root / "README.md").write_text("extracted source\n")
        with self.assertRaises(ComprehensiveHistoryUnavailable) as raised:
            run_integrated(self.root)
        self.assertIn("GIT_OBJECTS_MISSING_OR_INVALID", str(raised.exception))
        self.assertIn("cora zip-intake", str(raised.exception))
        self.assertEqual(raised.exception.safe_mode, "ZIP_INTAKE_SOURCE_ONLY")

    def test_single_synthetic_commit_does_not_qualify_history(self):
        self.make_git()
        with self.assertRaisesRegex(ComprehensiveHistoryUnavailable, "NO_PARENT_HISTORY"):
            run_integrated(self.root)

    def test_two_git_commits_are_not_necessarily_host_provenance(self):
        self.make_git(count=2)
        result = preflight_comprehensive_history(self.root)
        self.assertEqual(result["commit"], git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(result["state"], "GIT_OBJECTS_AND_LINEAGE_READABLE_NOT_HOST_ATTESTED")
        self.assertEqual(result["authority"], "NONE")

    def test_fabricated_cora_history_cannot_replace_original_ancestry(self):
        self.make_git(count=2, historical_register=True)
        with self.assertRaisesRegex(ComprehensiveHistoryUnavailable, "ORIGINAL_CORPUS_ANCESTRY_UNAVAILABLE"):
            preflight_comprehensive_history(self.root)

    def test_shallow_clone_explicitly_declassifies_history(self):
        self.make_git(count=2)
        with tempfile.TemporaryDirectory(prefix="cora-shallow-") as tmp:
            dest = Path(tmp) / "copy"
            subprocess.run(["git", "clone", "-q", "--depth", "1",
                            self.root.as_uri(), str(dest)], check=True)
            with self.assertRaisesRegex(ComprehensiveHistoryUnavailable, "SHALLOW_CHECKOUT"):
                preflight_comprehensive_history(dest)

    def test_invalid_revision_never_passes(self):
        self.make_git(count=2)
        with self.assertRaisesRegex(ComprehensiveHistoryUnavailable, "GIT_OBJECTS_MISSING_OR_INVALID"):
            preflight_comprehensive_history(self.root, "nonexistent-ref")


if __name__ == "__main__":
    unittest.main()
