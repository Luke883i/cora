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


if __name__ == "__main__":
    unittest.main()
