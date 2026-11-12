"""PR59 executable characterization: full change scope, portability and anti-promotion."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.practice_contract import classify, project, verify


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def commit(repo, changes):
    for name, contents in changes.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "physical semantic change")
    return git(repo, "rev-parse", "HEAD")


class PracticeRangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Independent Git fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        self.base = commit(self.root, {"README.md": "# Target\n", "src/app.js": "export const a = 0;\n"})

    def test_multi_commit_scope_is_not_last_commit(self):
        commit(self.root, {"README.md": "# Corrected meaning\n"})
        head = commit(self.root, {"src/app.js": "export const a = 1;\n"})
        narrow = project(self.root, head)
        self.assertNotIn("README.md", narrow["changed_paths"])
        full = project(self.root, head, change_base=self.base)
        self.assertEqual(full["schema"], "cora-practice-obligations/2")
        self.assertEqual(full["comparison"], "EXPLICIT_BASE_TO_HEAD")
        self.assertEqual(full["change_base"], self.base)
        self.assertEqual(full["changed_paths"], ["README.md", "src/app.js"])
        self.assertTrue(verify(self.root, full))
        self.assertEqual(full["external_approval"], "NONE")
        self.assertFalse(full["runtime_observed"])

    def test_portable_document_surfaces_never_invent_cora_files(self):
        head = commit(self.root, {"src/app.js": "export const a = 2;\n"})
        full = project(self.root, head, change_base=self.base)
        self.assertIn("README.md", full["editorial_refactor"]["surfaces"])
        self.assertNotIn("docs/RELEASE.md", full["editorial_refactor"]["surfaces"])
        self.assertTrue(all(
            (self.root / name).is_file()
            for name in full["editorial_refactor"]["surfaces"]
        ))
        self.assertTrue(next(x for x in full["obligations"]
                             if x["id"] == "P53_CROSS_DOCUMENT")["applicable"])

    def test_git_rename_and_newline_path_are_not_silently_dropped(self):
        git(self.root, "mv", "src/app.js", "src/new-app.js")
        head = commit(self.root, {"docs/line\nbreak.md": "special path\n"})
        full = project(self.root, head, change_base=self.base)
        self.assertIn("src/app.js", full["changed_paths"])
        self.assertIn("src/new-app.js", full["changed_paths"])
        self.assertIn("docs/line\nbreak.md", full["changed_paths"])
        self.assertTrue(verify(self.root, full))

    def test_invalid_base_and_forged_evidence_fail_closed(self):
        head = commit(self.root, {"README.md": "# Next\n"})
        with self.assertRaises(ValueError):
            project(self.root, head, change_base="a"*40)
        other = commit(self.root, {"README.md": "# Another\n"})
        with self.assertRaises(ValueError):
            project(self.root, head, change_base=other)
        good = project(self.root, head, change_base=self.base)
        for key, wrong in (("commit", "f"*40), ("change_base", "f"*40),
                           ("external_approval", "APPROVED"),
                           ("runtime_observed", True), ("digest", "0"*64)):
            mutant = copy.deepcopy(good)
            mutant[key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify(self.root, mutant)

    def test_pr58_default_contract_preserved_and_no_empty_scope_pass(self):
        head = commit(self.root, {"src/app.js": "export const a = 3;\n"})
        old = project(self.root, head)
        self.assertEqual(old["schema"], "cora-practice-obligations/1")
        self.assertNotIn("change_base", old)
        self.assertTrue(verify(self.root, old))
        untouched = project(self.root, self.base, change_base=self.base)
        self.assertEqual(untouched["changed_paths"], [])
        self.assertTrue(all(not o["applicable"] for o in untouched["obligations"]))
        self.assertEqual(untouched["external_approval"], "NONE")

    def test_process_and_one_run_use_same_pinned_change_range(self):
        from cora.process_suite import run_suite, verify_suite
        from cora.one_run import run_one, verify_one, render_one_html
        head = commit(self.root, {"src/app.js": "export const a = 4;\n"})
        basic = run_suite(self.root, head, process="history",
                          max_commits=2, change_base=self.base)
        self.assertEqual(basic["change_base"], self.base)
        self.assertEqual(basic["practice_obligations"]["schema"], "cora-practice-obligations/2")
        self.assertTrue(verify_suite(self.root, basic))
        one = run_one(self.root, head, process="history", max_commits=2,
                      change_base=self.base)
        self.assertEqual(one["source_process"]["change_base"], self.base)
        self.assertTrue(verify_one(self.root, one))
        html = render_one_html(one)
        self.assertIn("Change obligations", html)
        self.assertIn(self.base, html)
        altered = copy.deepcopy(basic)
        altered["practice_obligations"]["external_approval"] = "APPROVED"
        with self.assertRaises(ValueError):
            verify_suite(self.root, altered)


class LegacyProcessReceiptTests(unittest.TestCase):
    def test_old_git_source_replay_without_invented_pr58_field(self):
        from cora.evidence import domain_hash
        from cora.process_suite import PRE_PR58_MAIN, run_suite, verify_suite
        root = Path(__file__).resolve().parents[1]
        if not (root / ".git").exists():
            self.skipTest("original Git history required")
        try:
            git(root, "cat-file", "-e", PRE_PR58_MAIN + "^{commit}")
        except subprocess.CalledProcessError:
            self.skipTest("original PR57 commit not present in shallow checkout")
        original = run_suite(root, PRE_PR58_MAIN, process="history", max_commits=2)
        legacy = copy.deepcopy(original)
        legacy.pop("practice_obligations")
        legacy.pop("run_digest")
        legacy["run_digest"] = domain_hash("CORA:process-run:1", legacy)
        self.assertTrue(verify_suite(root, legacy))
        tampered = copy.deepcopy(legacy)
        tampered["authorized_action"] = "APPROVED"
        tampered.pop("run_digest")
        tampered["run_digest"] = domain_hash("CORA:process-run:1", tampered)
        with self.assertRaises(ValueError):
            verify_suite(root, tampered)
