"""PR51 Gold bridge: physical Git oracle, causal witness, negative receipt tests."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cora.gold_bridge import bridge_gold, SCHEMA as GOLD_SCHEMA
from cora.portable_assurance import _profile, run_portable, verify_portable, render_portable_html

ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.PIPE
    ).decode().strip()


class PR51NativeGoldBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cora-gold-pr51-")
        self.root = Path(self.tmp.name)
        self.art = self.root / "native-observations"
        self.art.mkdir()
        self.raw = {
            "source.txt": b"reported source test PASS - no authenticated runner\n",
            "browser.txt": b"reported browser PASS - no authenticated Chromium\n",
        }
        for path, value in self.raw.items():
            (self.art / path).write_bytes(value)
        self.repos = []
        for idx, entry in enumerate(("app.py", "web/app.mjs")):
            repo = self.root / ("repo-" + str(idx))
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Gold fixture")
            git(repo, "config", "user.email", "gold@example.invalid")
            source = repo / entry
            source.parent.mkdir(parents=True)
            source.write_text("raise RuntimeError('DO_NOT_EXECUTE')\n" if idx == 0
                              else "throw new Error('DO_NOT_EXECUTE');\n")
            for name in ("source", "browser"):
                file = repo / "tests" / (name + "_oracle.py")
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("raise RuntimeError('ORACLE_NOT_EXECUTED')\n")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "original oracle and product source")
            self.repos.append((repo, git(repo, "rev-parse", "HEAD"), entry))
        self.profile_path = self.root / "target-gold.json"

    def tearDown(self):
        self.tmp.cleanup()

    def profile(self, idx=0):
        repo, commit, entry = self.repos[idx]
        def oracle_sha(kind):
            return hashlib.sha256(
                subprocess.check_output(["git", "-C", str(repo), "show",
                                         commit + ":tests/" + kind + "_oracle.py"])
            ).hexdigest()
        def witness(id, category, path, oracle):
            return {
                "id": id, "category": category, "path": path,
                "sha256": hashlib.sha256(self.raw[path]).hexdigest(),
                "source_commit": commit, "oracle_id": oracle,
                "reported_outcome": "PASS_REPORTED_UNATTESTED"
            }
        claims = [
            {
                "id": "C_SOURCE", "claim": "Original source identity and source oracle bytes",
                "scope": "SOURCE", "owner_id": "product-owner",
                "source_path": entry, "oracle_id": "source-oracle",
                "oracle_path": "tests/source_oracle.py",
                "oracle_sha256": oracle_sha("source"),
                "witness_ids": ["source-evidence"], "depends_on": []
            },
            {
                "id": "C_BEHAVIOR", "claim": "Browser behavior matches the visible user promise",
                "scope": "BEHAVIOR", "owner_id": "product-owner",
                "source_path": entry, "oracle_id": "browser-oracle",
                "oracle_path": "tests/browser_oracle.py",
                "oracle_sha256": oracle_sha("browser"),
                "witness_ids": ["browser-evidence"], "depends_on": ["C_SOURCE"]
            },
            {
                "id": "C_GOVERNED", "claim": "Independent user acceptance and real host approval",
                "scope": "EXTERNAL", "owner_id": "product-owner",
                "source_path": entry, "oracle_id": "governance-oracle",
                "oracle_path": "tests/source_oracle.py",
                "oracle_sha256": oracle_sha("source"),
                "witness_ids": [], "depends_on": ["C_BEHAVIOR"]
            }
        ]
        return {
            "schema": "cora-portable-target/2",
            "target_repo": "Example/" + ("python" if idx == 0 else "node"),
            "revision": commit,
            "owners": [{"id": "product-owner", "path": entry}],
            "witnesses": [
                witness("source-evidence", "TEST_LOG", "source.txt", "source-oracle"),
                witness("browser-evidence", "BROWSER", "browser.txt", "browser-oracle")
            ],
            "method_links": [],
            "claims": claims, "goal": "C_GOVERNED"
        }

    def write(self, doc):
        self.profile_path.write_text(json.dumps(doc, sort_keys=True) + "\n")

    def observed(self, doc):
        return [
            {
                "id": w["id"], "category": w["category"],
                "source_commit": w["source_commit"], "oracle_id": w["oracle_id"],
                "sha256": w["sha256"], "reported_outcome": w["reported_outcome"],
                "state": "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED"
            } for w in doc["witnesses"]
        ]

    def direct(self, doc, idx=0, observed=True):
        _profile(doc, self.repos[idx][1])
        rows = self.observed(doc)
        if not observed:
            for row in rows:
                row["state"] = "NOT_RUN"
        return bridge_gold(self.repos[idx][0], self.repos[idx][1], doc, rows)

    def test_two_original_git_targets_and_four_gold_rails(self):
        for idx in range(2):
            with self.subTest(target=idx):
                doc = self.profile(idx)
                receipt = self.direct(doc, idx)
                self.assertEqual(receipt["schema"], GOLD_SCHEMA)
                self.assertEqual(receipt["source_oracle_bytes_replayed"], 3)
                self.assertEqual(receipt["native_witnesses_bound"], 2)
                self.assertEqual(receipt["native_witness_bytes_verified"], 2)
                self.assertEqual(receipt["goal"], "C_GOVERNED")
                self.assertEqual([c["id"] for c in receipt["claims"]],
                                 ["C_SOURCE", "C_BEHAVIOR", "C_GOVERNED"])
                self.assertEqual(
                    receipt["claims"][0]["status"], "SOURCE_LINK_ONLY_UNATTESTED")
                self.assertEqual(
                    receipt["claims"][1]["status"], "BEHAVIOR_BYTES_ONLY_EXECUTION_UNATTESTED")
                self.assertEqual(receipt["claims"][2]["status"], "BLOCKED_EXTERNAL")
                self.assertEqual(receipt["authorization"], "NONE")
                self.assertEqual(receipt["gold_rails"]["R4"],
                                 "INDEPENDENT_PRODUCT_PILOT_NOT_ATTESTED")
                self.assertTrue(all(not x["claim_proven"] for x in receipt["claims"]))

    def test_no_retained_bytes_and_skip_cannot_become_pass(self):
        doc = self.profile()
        missing = self.direct(doc, observed=False)
        self.assertEqual(missing["claims"][0]["status"],
                         "BLOCKED_NATIVE_BYTES_NOT_OBSERVED")
        self.assertEqual(missing["claims"][1]["status"],
                         "BLOCKED_NATIVE_BYTES_NOT_OBSERVED")
        doc["witnesses"][1]["reported_outcome"] = "SKIPPED_REPORTED_UNATTESTED"
        skipped = self.direct(doc)
        self.assertEqual(skipped["claims"][1]["status"],
                         "BLOCKED_NATIVE_SKIPPED_OR_NOT_RUN")
        self.assertEqual(skipped["claims"][2]["status"], "BLOCKED_EXTERNAL")
        self.assertEqual(skipped["native_witness_bytes_verified"], 2)
        doc["witnesses"][1]["reported_outcome"] = "NOT_RUN_REPORTED_UNATTESTED"
        self.assertEqual(self.direct(doc)["claims"][1]["status"],
                         "BLOCKED_NATIVE_SKIPPED_OR_NOT_RUN")
        doc["witnesses"][1]["reported_outcome"] = "FAIL_REPORTED_UNATTESTED"
        counter = self.direct(doc)
        self.assertEqual(counter["reported_counterevidence"], 1)
        self.assertEqual(counter["claims"][1]["status"],
                         "COUNTEREVIDENCE_REPORTED_UNATTESTED")

    def test_hostile_claim_and_oracle_mutations(self):
        original = self.profile()
        mutants = [
            ("false-owner", lambda p: p["claims"][0].update(owner_id="admin")),
            ("owner-source-mismatch", lambda p: p["claims"][0].update(source_path="tests/source_oracle.py")),
            ("missing-oracle", lambda p: p["claims"][0].update(oracle_path="tests/phantom.py")),
            ("forged-oracle", lambda p: p["claims"][0].update(oracle_sha256="f" * 64)),
            ("wrong-witness", lambda p: p["claims"][0].update(witness_ids=["phantom"])),
            ("cross-claim-reuse", lambda p: p["claims"][1].update(witness_ids=["source-evidence"])),
            ("oracle-id-mismatch", lambda p: p["claims"][0].update(oracle_id="browser-oracle")),
            ("fake-scope", lambda p: p["claims"][0].update(scope="INDEPENDENT_PASS")),
            ("fake-approval", lambda p: p["claims"][0].update(approved=True)),
            ("unknown-goal", lambda p: p.update(goal="NON_EXISTENT")),
            ("dangling-dependency", lambda p: p["claims"][0].update(depends_on=["MISSING"])),
            ("cycle", lambda p: p["claims"][0].update(depends_on=["C_GOVERNED"])),
            ("duplicate-claim", lambda p: p["claims"].append(copy.deepcopy(p["claims"][0]))),
            ("orphan-claim", lambda p: p["claims"].append({
                **copy.deepcopy(p["claims"][0]), "id": "C_ORPHAN", "witness_ids": []
            })),
            ("orphan-native-witness", lambda p: p["claims"][1].update(witness_ids=[])),
            ("duplicate-dependency", lambda p: p["claims"][1].update(depends_on=["C_SOURCE", "C_SOURCE"])),
            ("source-commit-forgery", lambda p: p["witnesses"][0].update(source_commit="a"*40)),
            ("unauthorized-external-claim", lambda p: p["claims"][2].update(scope="AUTHORIZED")),
            ("invalid-oracle-path", lambda p: p["claims"][0].update(oracle_path="../escape")),
            ("unbounded-claim", lambda p: p["claims"][0].update(claim="x"*1201)),
        ]
        self.assertEqual(len(mutants), 20)
        for label, mutate in mutants:
            with self.subTest(mutant=label):
                doc = copy.deepcopy(original)
                mutate(doc)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    self.direct(doc)

    def test_mutation_changes_original_oracle_git_and_fails_closed(self):
        doc = self.profile()
        repo, previous, source = self.repos[0]
        self.assertEqual(self.direct(doc)["native_witnesses_bound"], 2)
        (repo / "tests" / "browser_oracle.py").write_text(
            "raise RuntimeError('DIFFERENT_ORACLE')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "physical negative oracle source change")
        new_head = git(repo, "rev-parse", "HEAD")
        self.repos[0] = (repo, new_head, source)
        # Old receipts still belong to immutable earlier commit; the v2
        # contract cannot be carried to new HEAD without rebinding.
        with self.assertRaisesRegex(ValueError, "stale source revision"):
            self.direct(doc)
        doc["revision"] = new_head
        for w in doc["witnesses"]:
            w["source_commit"] = new_head
        with self.assertRaisesRegex(ValueError, "oracle byte drift"):
            self.direct(doc)

    def test_cli_portable_single_atlas_and_old_receipt_replay(self):
        doc = self.profile()
        self.write(doc)
        repo = self.repos[0][0]
        json_out = self.root / "gold.json"
        html_out = self.root / "gold.html"
        cmd = [sys.executable, "-m", "cora.cli", "process-run", str(repo),
               "--one-run", "--portable-profile", str(self.profile_path),
               "--portable-evidence-dir", str(self.art),
               "--output", str(json_out), "--atlas-html", str(html_out)]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertIn(run.returncode, (0, 2), run.stderr)
        receipt = json.loads(json_out.read_text())
        self.assertEqual(receipt["gold"]["goal_status"],
                         "BLOCKED_INDEPENDENT_ORACLE_EXECUTION_AND_REVIEW")
        self.assertEqual(receipt["authorization"], "NONE")
        self.assertIn("Gold R1-R4 claim-to-native-witness trace", html_out.read_text())
        self.assertTrue(verify_portable(repo, receipt, self.profile_path,
                        evidence_dir=self.art, html_page=html_out.read_text()))
        replay = subprocess.run(
            [sys.executable, "-m", "cora.cli", "verify-process", str(json_out),
             "--one-run", "--repo", str(repo),
             "--portable-profile", str(self.profile_path),
             "--portable-evidence-dir", str(self.art), "--atlas-html", str(html_out)],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
        altered = copy.deepcopy(receipt)
        altered["gold"]["claims"][1]["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(repo, altered, self.profile_path, evidence_dir=self.art)
        (self.art / "browser.txt").write_bytes(b"forged run result")
        with self.assertRaisesRegex(ValueError, "evidence tamper"):
            verify_portable(repo, receipt, self.profile_path, evidence_dir=self.art)

    def test_html_escapes_target_authored_claims(self):
        doc = self.profile()
        doc["claims"][0]["claim"] = "<script>alert('proof')</script> is not a witness"
        self.write(doc)
        result = run_portable(self.repos[0][0], "HEAD", self.profile_path)
        rendered = render_portable_html(result)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertEqual(result["gold"]["authorization"], "NONE")


if __name__ == "__main__":
    unittest.main()
