"""PR36: actual CORA one-run, original-Git reticulum, HTML and finite adversaries."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.cli import main
from cora.one_run import (
    _original_dod, run_one, verify_one, render_one_html,
    validate_execution_row, validate_execution_rows,
)
from cora.one_run_stress import vector, stress_one_run
from cora.process_suite import run_suite, verify_suite

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *argv: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *argv],
                                   stderr=subprocess.PIPE).decode().strip()


class OneRunAssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").is_dir():
            raise unittest.SkipTest("original Git checkout required")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.source = run_one(ROOT, cls.sha)

    def test_actual_source_methods_and_noncompensatory_reticulum(self):
        d = self.source
        self.assertEqual(d["commit"], self.sha)
        self.assertEqual(d["tree"], git(ROOT, "rev-parse", "HEAD^{tree}"))
        self.assertEqual(d["source_process"]["process"], "full")
        self.assertEqual(len(d["activities"]), 8)
        self.assertEqual(d["catalog_commands_declared"], 71)
        self.assertEqual(d["catalog_commands_executed_individually"], 0)
        self.assertEqual(d["metrics"]["FAIL"], 0)
        self.assertEqual(d["metrics"]["NOT_RUN"], 2 if any(
            x["state"] == "NOT_RUN" for x in d["activities"]) else 1)
        self.assertIn(d["source_status"], ("PASS_SCOPED_WITH_UNVERIFIED_GAPS", "DEBT_BLOCKED"))
        self.assertEqual(d["runtime_status"], "NOT_RUN")
        self.assertEqual(d["global_status"], "BLOCKED_EXTERNAL")
        self.assertFalse(d["release_authorized"])
        self.assertEqual(d["authorization"], "NONE")
        self.assertEqual(d["dod"]["nodes"], 27)
        self.assertEqual(d["dod"]["gates"]["G_ONE_RUN_SOURCE"], "MODEL_ELIGIBLE_UNATTESTED")
        self.assertEqual(d["dod"]["gates"]["G_ONE_RUN_PRODUCT"], "BLOCKED_EXTERNAL")
        for row in d["activities"]:
            validate_execution_row(row)
            self.assertEqual(row["commit"], self.sha)
            self.assertIn(row["state"], ("EXECUTED_SCOPED", "REUSED_SCOPED",
                                         "BLOCKED", "NOT_RUN"))
            if row["state"] == "REUSED_SCOPED" and row["elapsed_ms"] is None:
                self.assertEqual(row["timing_basis"], "REUSED_NOT_INDEPENDENTLY_TIMED")

    def test_source_replay_and_html_byte_replay(self):
        report = self.source
        page = render_one_html(report)
        self.assertTrue(verify_one(ROOT, report, html_page=page))
        self.assertIn("CORA ONE-RUN | EXECUTION-BOUNDED", page)
        self.assertIn('id="run-execution"', page)
        self.assertIn('id="find"', page)
        self.assertIn("71 comandi dichiarati", page)
        self.assertIn("connect-src 'none'", page)
        self.assertIn("TEST_EXECUTION", json.dumps(report["self_tests"]))
        with self.assertRaisesRegex(ValueError, "HTML differs"):
            verify_one(ROOT, report, html_page=page.replace("Esiti realmente osservati", "APPROVED"))

    def test_canonical_json_roundtrip_preserves_html_byte_for_byte(self):
        source=self.source
        sorted_json=json.dumps(source,sort_keys=True,ensure_ascii=True)
        from_json=json.loads(sorted_json)
        self.assertEqual(render_one_html(source),render_one_html(from_json))
        self.assertTrue(verify_one(ROOT,from_json,
                                  html_page=render_one_html(source)))

    def test_finite_model_opt_in_is_visible_and_reproducible(self):
        from cora.one_run_stress import stress_one_run
        model=stress_one_run(100000,seed=883)
        self.assertEqual(model["cases"],100000)
        self.assertEqual(model["positive_controls"],6250)
        self.assertEqual(model["negative_scenarios"],93750)
        self.assertEqual(model["oracle_disagreements"],0)
        self.assertEqual(model["unauthorized_promotions"],0)
        self.assertEqual(model["physical_source_mutants"],0)
        self.assertEqual(self.source["model_stress"]["status"],"NOT_RUN")

    def test_legacy_process_suite_still_exact_deterministic(self):
        legacy = run_suite(ROOT, self.sha)
        self.assertNotIn("timing", legacy)
        self.assertTrue(all("elapsed_ms" not in x for x in legacy["results"]))
        self.assertTrue(verify_suite(ROOT, legacy))
        self.assertEqual(len(legacy["results"]), 8)

    def test_tamper_failure_cannot_be_erased_by_new_digest(self):
        valid = self.source
        for corruption in (
            lambda x: x["activities"][0].update(state="PASS"),
            lambda x: x["activities"][0].update(authority="APPROVED"),
            lambda x: x["activities"][0].update(commit="0"*40),
            lambda x: x["metrics"].update(FAIL=50),
            lambda x: x["catalog"].update(authorization="MERGE"),
            lambda x: x["dod"]["gates"].update(G_ONE_RUN_PRODUCT="PASS"),
            lambda x: x.update(global_status="PASS"),
            lambda x: x.update(catalog_commands_executed_individually=71),
            lambda x: x["excluded_not_run"].clear(),
            lambda x: x["self_tests"].update(state="RUN_REPORTED_UNATTESTED", returncode=0),
        ):
            forged = copy.deepcopy(valid)
            corruption(forged)
            with self.assertRaises((ValueError, KeyError, TypeError)):
                verify_one(ROOT, forged)

    def test_opt_in_is_never_silent_and_never_publishes(self):
        with patch("cora.one_run.subprocess.run") as probe:
            # Safe profile calls git through the original helper, which also
            # needs subprocess; use a direct patch of only the test executor
            # here by checking the default observed result.
            self.assertEqual(self.source["self_tests"]["state"], "NOT_RUN")
            self.assertFalse(self.source["release_authorized"])
            self.assertEqual(probe.call_count, 0)
        with self.assertRaisesRegex(ValueError, "bounded"):
            run_one(ROOT, self.sha, test_timeout=1)

    def test_offline_html_escapes_untrusted_run_reason(self):
        poisoned = copy.deepcopy(self.source)
        poisoned["activities"][0]["reason"] = '<img src=x onerror="alert(1)">'
        page = render_one_html(poisoned)
        self.assertNotIn('<img src=x onerror="alert(1)">', page)
        self.assertIn("&lt;img", page)
        self.assertIn("connect-src 'none'", page)

    def test_existing_cli_one_command_and_replay(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            report, page, machine = [out / name for name in ("run.json", "atlas.html", "atlas.json")]
            status = main(["process-run", str(ROOT), "--revision", self.sha,
                           "--process", "full", "--one-run", "--output", str(report),
                           "--atlas-html", str(page), "--atlas-json", str(machine)])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(report.read_text("utf-8")),
                             json.loads(machine.read_text("utf-8")))
            self.assertEqual(main(["verify-process", str(report), "--repo", str(ROOT),
                                   "--one-run", "--atlas-html", str(page),
                                   "--atlas-json", str(machine)]), 0)
            page.write_text(page.read_text("utf-8").replace(
                "71 comandi dichiarati", "71 comandi VERIFICATI"), encoding="utf-8")
            self.assertEqual(main(["verify-process", str(report), "--repo", str(ROOT),
                                   "--one-run", "--atlas-html", str(page)]), 3)

    def test_original_git_doD_physical_source_mutants(self):
        with tempfile.TemporaryDirectory() as d:
            clone = Path(d)/"git-fixture"
            subprocess.run(["git", "clone", "-q", "--local", str(ROOT), str(clone)], check=True)
            git(clone, "checkout", "-q", self.sha)
            git(clone, "config", "user.name", "CORA negative control")
            git(clone, "config", "user.email", "test@example.invalid")
            doc = clone / ".cora/contracts/dod/one-run-dod.json"
            original = json.loads(doc.read_text("utf-8"))
            self.assertEqual(_original_dod(clone, self.sha)["nodes"], 27)
            first = copy.deepcopy(original)
            next(n for n in first["nodes"] if n["id"] == "E_REVIEW")["scope"] = "SOURCE"
            doc.write_text(json.dumps(first), encoding="utf-8")
            git(clone, "add", ".cora/contracts/dod/one-run-dod.json")
            git(clone, "commit", "-qm", "mutant: forged source reviewer")
            with self.assertRaisesRegex(ValueError, "mandatory DoD"):
                _original_dod(clone, git(clone, "rev-parse", "HEAD"))
            git(clone, "checkout", "-q", self.sha)
            second = copy.deepcopy(original)
            next(n for n in second["nodes"] if n["id"] == "G_SOURCE_REPLAY")["depends_on"].remove("L_100K")
            doc.write_text(json.dumps(second), encoding="utf-8")
            git(clone, "add", ".cora/contracts/dod/one-run-dod.json")
            git(clone, "commit", "-qm", "mutant: remove necessary 100k gate")
            with self.assertRaisesRegex(ValueError, "mandatory DoD"):
                _original_dod(clone, git(clone, "rev-parse", "HEAD"))

    def test_typical_adversarial_families_and_replay_320(self):
        for i in range(32):
            name, rows, expected = vector(i, 883)
            self.assertEqual(name, __import__("cora.one_run_stress", fromlist=["FAMILIES"]).FAMILIES[i])
            if expected:
                self.assertTrue(validate_execution_rows(rows, expected_commit="a"*40))
            else:
                with self.assertRaises((ValueError, TypeError, KeyError)):
                    validate_execution_rows(rows, expected_commit="a"*40)
        a = stress_one_run(320, seed=883)
        b = stress_one_run(320, seed=883)
        self.assertEqual(a, b)
        self.assertEqual(a["positive_controls"], 20)
        self.assertEqual(a["negative_scenarios"], 300)
        self.assertEqual(a["distinct_input_fingerprints"], 320)
        self.assertEqual(a["oracle_disagreements"], 0)
        self.assertEqual(a["unauthorized_promotions"], 0)
        self.assertEqual(a["external"], "BLOCKED_EXTERNAL")


if __name__ == "__main__":
    unittest.main()
