"""PR50 real Git target fixtures, bounded evidence, negative mutations and no promotion."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cora.portable_assurance import run_portable, verify_portable, render_portable_html
from tools.verify_crossrepo_convergence import evaluate

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class PortableCrossRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence = self.root / "witnesses"
        self.evidence.mkdir()
        (self.evidence / "observed.txt").write_bytes(b"mock reported HTTP+browser evidence\n")
        self.repos = []
        for idx, source in enumerate(("web/app.mjs", "src/app.py")):
            repo = self.root / ("target" + str(idx))
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Portable fixture")
            git(repo, "config", "user.email", "fixture@example.invalid")
            file = repo / source
            file.parent.mkdir()
            file.write_text(
                "throw new Error('NEVER_EXECUTED'); import('./dynamic.mjs');\n" if idx == 0
                else "raise RuntimeError('NEVER_EXECUTED')\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "fixture original source")
            self.repos.append((repo, git(repo, "rev-parse", "HEAD"), source))
        self.profile = self.root / "profile.json"

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self, i=0):
        repo, commit, source = self.repos[i]
        return {
            "schema": "cora-portable-target/1",
            "target_repo": "Luke883i/" + ("teddy" if i == 0 else "NILO"),
            "revision": commit,
            "owners": [{"id": "original-owner", "path": source}],
            "witnesses": [{
                "id": "browser-claim", "category": "BROWSER", "path": "observed.txt",
                "sha256": hashlib.sha256((self.evidence / "observed.txt").read_bytes()).hexdigest(),
                "source_commit": commit, "oracle_id": "original-negative-oracle",
                "reported_outcome": "PASS_REPORTED_UNATTESTED"
            }],
            "method_links": [{
                "id": "LUMEN-to-Teddy" if i == 0 else "CORA-to-NILO",
                "kind": "METHOD_TRANSFER", "source_repo": "Luke883i/lumen" if i == 0 else "Luke883i/cora",
                "source_commit": "a" * 40 if i == 0 else "b" * 40,
                "target_owner": "original-owner", "target_commit": commit,
                "source_reference": "https://github.com/Luke883i/" + ("lumen" if i == 0 else "cora") + "/pull/1"
            }]
        }

    def write(self, doc):
        self.profile.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def run_it(self, i=0, evidence=False):
        self.write(self.contract(i))
        repo = self.repos[i][0]
        return run_portable(repo, "HEAD", self.profile,
                            evidence_dir=self.evidence if evidence else None)

    def test_two_different_real_git_targets_and_replay(self):
        for i in range(2):
            with self.subTest(target=i):
                result = self.run_it(i, evidence=True)
                self.assertTrue(verify_portable(self.repos[i][0], result, self.profile,
                                evidence_dir=self.evidence))
                self.assertEqual(result["governed_status"], "BLOCKED_EXTERNAL")
                self.assertEqual(result["authorization"], "NONE")
                self.assertEqual(result["method_links"][0]["state"],
                                 "FOREIGN_GIT_SOURCE_UNVERIFIED")
                self.assertEqual(result["evidence"][0]["state"],
                                 "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED")
                self.assertIn(result["source_status"],
                              ("PASS_SCOPED_GIT_SOURCE_ONLY", "DEBT_BLOCKED"))
                self.assertEqual(result["js_import_graph"],
                                 "NOT_OBSERVED_NONPYTHON_CONSUMERS_UNKNOWN")

    def test_tampered_receipt_and_html_rejected(self):
        result = self.run_it(evidence=True)
        html = render_portable_html(result)
        self.assertTrue(verify_portable(self.repos[0][0], result, self.profile,
                                        evidence_dir=self.evidence, html_page=html))
        modified = copy.deepcopy(result)
        modified["governed_status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(self.repos[0][0], modified, self.profile, evidence_dir=self.evidence)
        with self.assertRaisesRegex(ValueError, "HTML mismatch"):
            verify_portable(self.repos[0][0], result, self.profile,
                            evidence_dir=self.evidence, html_page=html.replace("BLOCKED_EXTERNAL", "PASS"))

    def test_tampered_bytes_and_symlink_rejected(self):
        result = self.run_it(evidence=True)
        (self.evidence / "observed.txt").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "evidence tamper"):
            verify_portable(self.repos[0][0], result, self.profile, evidence_dir=self.evidence)
        (self.evidence / "observed.txt").unlink()
        (self.evidence / "observed.txt").symlink_to(self.profile)
        with self.assertRaisesRegex(ValueError, "symlink"):
            run_portable(self.repos[0][0], "HEAD", self.profile, evidence_dir=self.evidence)

    def test_profile_and_original_git_negative_family_matrix(self):
        original = self.contract()
        mutated = []
        def mutate(name, field, value):
            data = copy.deepcopy(original)
            field(data, value)
            mutated.append((name, data))
        mutate("stale-sha", lambda d,v:d.update(revision=v), "f" * 40)
        mutate("owner-path", lambda d,v:d["owners"][0].update(path=v), "../unbound")
        mutate("owner-missing", lambda d,v:d["owners"][0].update(path=v), "missing.py")
        mutate("duplicate-owner", lambda d,v:d["owners"].append(d["owners"][0].copy()), None)
        mutate("wrong-category", lambda d,v:d["witnesses"][0].update(category=v), "CERTIFIED_REAL_USER")
        mutate("missing-oracle", lambda d,v:d["witnesses"][0].update(oracle_id=v), "")
        mutate("witness-outcome-promotion", lambda d,v:d["witnesses"][0].update(reported_outcome=v), "PASS")
        mutate("witness-sha-mismatch", lambda d,v:d["witnesses"][0].update(source_commit=v), "d" * 40)
        mutate("witness-path-traversal", lambda d,v:d["witnesses"][0].update(path=v), "../secrets")
        mutate("fake-transfer-kind", lambda d,v:d["method_links"][0].update(kind=v), "VERIFIED_RUNTIME_DEPENDENCY")
        mutate("transfer-stale", lambda d,v:d["method_links"][0].update(target_commit=v), "c" * 40)
        mutate("upstream-forged-domain", lambda d,v:d["method_links"][0].update(source_reference=v), "https://example.invalid/claim")
        self.assertEqual(len(mutated), 12)
        for name, candidate in mutated:
            with self.subTest(mutation=name):
                self.write(candidate)
                with self.assertRaises(ValueError):
                    run_portable(self.repos[0][0], "HEAD", self.profile)
        self.assertEqual(evaluate(ROOT)["product_status"], "BLOCKED_EXTERNAL")

    def test_new_git_revision_invalidates_old_profile(self):
        result = self.run_it()
        repo = self.repos[0][0]
        (repo / "web" / "extra.mjs").write_text("export const newCode = 1;\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "new source revision")
        with self.assertRaisesRegex(ValueError, "stale source revision"):
            run_portable(repo, "HEAD", self.profile)
        with self.assertRaises(ValueError):
            verify_portable(repo, result, self.profile)

    def test_cli_one_run_transport(self):
        self.write(self.contract())
        receipt = self.root / "portable.json"
        html = self.root / "portable.html"
        cmd = [sys.executable, "-m", "cora.cli", "process-run",
               str(self.repos[0][0]), "--one-run", "--portable-profile",
               str(self.profile), "--output", str(receipt), "--atlas-html", str(html)]
        launched = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertIn(launched.returncode, (0, 2), launched.stderr)
        self.assertTrue(receipt.is_file(), launched.stderr)
        replay = subprocess.run([sys.executable, "-m", "cora.cli", "verify-process",
                                  str(receipt), "--repo", str(self.repos[0][0]),
                                  "--one-run", "--portable-profile", str(self.profile),
                                  "--atlas-html", str(html)],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
        self.assertIn("BLOCKED_EXTERNAL", replay.stdout)

    def test_reticular_all_levels_and_no_false_source_global(self):
        r = evaluate(ROOT)
        self.assertEqual((r["obligations"], r["local"], r["intermediate"], r["global"]),
                         (25, 18, 5, 2))
        self.assertEqual(r["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(r["authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
