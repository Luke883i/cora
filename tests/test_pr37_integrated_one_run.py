"""PR37: exact-Git inventory, source replay, HTML and nonpromotion mutants."""
from __future__ import annotations

import copy
import json
import random
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.cli import main
from cora.evidence import domain_hash
from cora.integrated_registry import build_registry, verify_contract
from cora.integrated_run import run_integrated, verify_integrated, _attempts, _topological, _parse_unittest_log
from cora.integrated_html import render_integrated_html

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class IntegratedOneRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").is_dir():
            raise unittest.SkipTest("requires exact original Git source checkout")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.report = run_integrated(ROOT, cls.sha, evidence_dir=None)

    def test_total_census_is_an_accountability_not_execution_claim(self):
        report = self.report
        self.assertEqual(report["commit"], self.sha)
        registry = report["registry"]
        self.assertEqual(registry["declared_commands"], 71)
        self.assertEqual(registry["registered_commands"], 71)
        self.assertEqual(registry["dispatched_commands"], 71)
        self.assertEqual(registry["class_counts"]["CLI_COMMAND"], 71)
        self.assertEqual(registry["class_counts"]["INTERNAL_METHOD"], 8)
        self.assertGreater(registry["class_counts"]["TEST_CASE"], 20)
        self.assertGreater(registry["class_counts"]["VERIFIER"], 5)
        self.assertGreater(registry["class_counts"]["CI_WORKFLOW"], 5)
        self.assertEqual(report["metrics"]["registered_total"], len(registry["activities"]))
        self.assertEqual(report["metrics"]["activity_accounted"], len(report["attempts"]))
        self.assertEqual(report["metrics"]["individually_executed_cli"], 0)
        self.assertEqual(report["source_status"], "DEBT_BLOCKED")
        self.assertEqual(report["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(report["authority"], "NONE")
        self.assertEqual(report["authorization"], "NONE")
        self.assertEqual(len(report["dod"]["nodes"]), 55)
        self.assertEqual(len(report["baseline_pr36"]["dod"]["gates"]), 6)
        for row, result in zip(registry["activities"], report["attempts"]):
            self.assertEqual(row["activity_id"], result["activity_id"])
            self.assertEqual(result["authority"], "NONE")
            if row["effect_class"] != "READ_ONLY":
                self.assertNotEqual(row["execution_adapter"], "PR36_PROCESS_SUITE")
        self.assertEqual(len(_topological(registry)), len(registry["activities"]))
        self.assertEqual(report["gaps"]["unreported_activity_count"], 0)

    def test_original_git_replay_html_and_json_roundtrip(self):
        report = self.report
        page = render_integrated_html(report)
        self.assertTrue(verify_integrated(ROOT, report, html_page=page))
        self.assertIn('id="review-path"', page)
        for phrase in ("1. What can be concluded?", "2. Where is the evidence?",
                       "3. What could disprove it?", "BLOCKED_EXTERNAL"):
            self.assertIn(phrase, page)
        self.assertIn('href="#artifacts"', page)
        self.assertIn('href="#gaps"', page)
        self.assertIn('id="inventory"', page)
        self.assertIn('id="test-cases"', page)
        self.assertIn('id="dod"', page)
        self.assertIn('id="artifacts"', page)
        self.assertIn("script-src", page)
        self.assertIn("connect-src &#x27;none&#x27;", page)
        serialized = json.dumps(report, sort_keys=True, ensure_ascii=True)
        canonical = json.loads(serialized)
        self.assertEqual(render_integrated_html(canonical), page)
        self.assertTrue(verify_integrated(ROOT, canonical, html_page=page))
        with self.assertRaisesRegex(ValueError, "HTML"):
            verify_integrated(ROOT, report, html_page=page + "<b>APPROVED</b>")

    def test_registry_also_revalidates_against_original_git(self):
        source = build_registry(ROOT, self.sha)
        self.assertEqual(source, self.report["registry"])
        self.assertEqual(source["commit"], self.sha)
        self.assertEqual(source["authority"], "NONE")
        self.assertIn("workflow:.github/workflows/ci-verify-pull-request.yml",
                      {x["activity_id"] for x in source["activities"]})
        self.assertEqual({x["activity_id"] for x in source["activities"]
                          if x["kind"] == "CLI_COMMAND"},
                         {"cli:" + x["command"] for x in json.loads(
                          (ROOT / ".cora/assurance/capability-atlas.json").read_text())["commands"]})

    def test_forged_source_and_runtime_promotion_fail_with_recomputed_self_hash(self):
        mutations = (
            lambda x: x["attempts"][0].update(state="EXECUTED_SCOPED", reason=None),
            lambda x: x["attempts"][0].update(authority="RELEASE_APPROVED"),
            lambda x: x["registry"]["activities"].pop(),
            lambda x: x["plan"]["effectful_disallowed"].clear(),
            lambda x: x["metrics"].update(individually_executed_cli=71),
            lambda x: x["dod"].update(product_goal="PASS"),
            lambda x: x.update(product_status="PASS"),
            lambda x: x.update(authorization="APPROVED"),
            lambda x: x.update(source_status="PASS"),
            lambda x: x["tests"].update(state="RUN_REPORTED_UNATTESTED"),
            lambda x: x["gaps"].update(issues=[]),
            lambda x: x["execution_manifest"].update(trust="INDEPENDENT_ATTESTATION"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate.__code__.co_firstlineno):
                forged = copy.deepcopy(self.report)
                mutate(forged)
                unsigned = {k: v for k,v in forged.items() if k != "receipt_digest"}
                forged["receipt_digest"] = domain_hash("CORA:integrated-one-run:2", unsigned)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    verify_integrated(ROOT, forged)

    def test_untrusted_html_is_escaped_and_never_executable(self):
        untrusted = copy.deepcopy(self.report)
        untrusted["registry"]["activities"][0]["call_path"] = '<img src=x onerror=alert(1)>'
        page = render_integrated_html(untrusted)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", page)
        self.assertNotIn('<img src=x onerror=alert(1)>', page)
        self.assertIn("CORA | One-Run forensic atlas", page)
        # Malicious metrics cannot turn reviewer prose into executable HTML.
        untrusted["metrics"]["activity_accounted"] = "<img src=x onerror=alert(2)>"
        escaped = render_integrated_html(untrusted)
        self.assertIn("&lt;img src=x onerror=alert(2)&gt;", escaped)
        self.assertNotIn("<img src=x onerror=alert(2)>", escaped)

    def test_opt_in_fail_closed_without_separate_commit_consent(self):
        with self.assertRaisesRegex(ValueError, "both opt-in"):
            run_integrated(ROOT,self.sha,execute_self_tests=True)
        with tempfile.TemporaryDirectory() as out:
            consent = Path(out) / "consent.json"
            consent.write_text(json.dumps({
                "schema":"cora-explicit-execution-consent/1",
                "commit":"0" * 40,
                "tree": self.report["tree"],
                "operation":"CORA_LOCAL_SELF_TESTS",
                "checkout": str(ROOT)}))
            with self.assertRaisesRegex(ValueError, "consent"):
                run_integrated(ROOT,self.sha,execute_self_tests=True,
                               authorization_file=consent,evidence_dir=Path(out)/"evidence")

    def test_materialized_evidence_manifest_and_one_cli_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirpath = Path(tmp)
            reportpath, atlaspath, machinepath = dirpath/"run.json", dirpath/"index.html", dirpath/"machine.json"
            evidence = dirpath/"evidence"
            code = main(["process-run",str(ROOT),"--revision",self.sha,"--process","full",
                         "--one-run","--profile","comprehensive","--output",str(reportpath),
                         "--atlas-html",str(atlaspath),"--atlas-json",str(machinepath),
                         "--evidence-dir",str(evidence)])
            self.assertIn(code,(0,2))
            output = json.loads(reportpath.read_text("utf-8"))
            self.assertEqual(output, json.loads(machinepath.read_text("utf-8")))
            self.assertEqual(output["schema"], "cora-integrated-one-run/2")
            self.assertEqual(output["evidence_manifest"]["state"],
                             "MATERIALIZED_LOCAL_NOT_INDEPENDENTLY_ATTESTED")
            self.assertTrue(verify_integrated(ROOT,output,
                html_page=atlaspath.read_text("utf-8"),evidence_dir=evidence))
            self.assertEqual(main(["verify-process",str(reportpath),"--repo",str(ROOT),
                "--one-run","--atlas-html",str(atlaspath),"--atlas-json",str(machinepath),
                "--evidence-dir",str(evidence)]),0)
            with (evidence/"gaps.json").open("ab") as damaged:
                damaged.write(b"\nFORGED_PASS")
            with self.assertRaisesRegex(ValueError, "evidence was modified"):
                verify_integrated(ROOT,output,evidence_dir=evidence)


    def test_individual_test_logs_reparse_and_duplicate_refusal(self):
        raw = b"test_one (test_example.Case.test_one) ... ok\nRan 1 test in 0.001s\nOK\n"
        events, count, warnings = _parse_unittest_log(raw)
        self.assertEqual(count,1)
        self.assertEqual(warnings,[])
        self.assertEqual(events[0]["activity_id"],"case:tests/test_example.py:Case.test_one")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            _parse_unittest_log(raw + raw.split(b"\n")[0] + b"\n")

    def test_registry_dependency_cycle_rejected(self):
        malformed = copy.deepcopy(self.report["registry"])
        for row in malformed["activities"]:
            if row["activity_id"] == "method:git_snapshot":
                row["dependencies"] = ["method:artifact_roles"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            _topological(malformed)

    def test_physical_committed_contract_mutants(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["git","init","-q",str(target)],check=True)
            dest = target/".cora/contracts/dod"
            dest.mkdir(parents=True)
            for name in ("one-run-dod.json","integrated-one-run-dod.json"):
                (dest/name).write_bytes((ROOT/".cora/contracts/dod"/name).read_bytes())
            def commit(message):
                subprocess.run(["git","-C",str(target),"add","-A"],check=True)
                subprocess.run(["git","-C",str(target),"-c","user.email=cora@test.invalid",
                    "-c","user.name=NonAuthorOracle","commit","-qm",message],check=True)
                return git(target,"rev-parse","HEAD")
            good = commit("valid original Git contracts")
            self.assertEqual(verify_contract(target,good)["schema"],
                             "cora-integrated-one-run-dod/2")
            changed = json.loads((dest/"integrated-one-run-dod.json").read_text())
            gate = next(n for n in changed["nodes"] if n["id"] == "G_REGISTRY")
            gate["depends_on"] = []
            (dest/"integrated-one-run-dod.json").write_text(json.dumps(changed))
            bad = commit("physical Git DoD edge omission")
            with self.assertRaisesRegex(ValueError,"edge"):
                verify_contract(target,bad)
            # The original good SHA remains checkable after a bad committed descendant.
            self.assertEqual(verify_contract(target,good)["schema"],
                             "cora-integrated-one-run-dod/2")

    def test_ten_thousand_seeded_semantic_dod_mutants(self):
        original = verify_contract(ROOT,self.sha)
        baseline = json.dumps(original)
        rnd = random.Random(883)
        families = (
            "DROP_NODE","DUPLICATE_ID","REMOVE_GATE_EDGE","PROMOTE_EXTERNAL",
            "FORGE_AUTHORITY","WRONG_PR36_COMMIT","EXTRA_ORPHAN",
            "ALTER_REQUIRED_FIELDS","CYCLE_EDGE","WRONG_GLOBAL_GOAL",
        )
        for i in range(10000):
            family = families[i % len(families)]
            doc = json.loads(baseline)
            if family == "DROP_NODE":
                doc["nodes"].pop(rnd.randrange(len(doc["nodes"])))
            elif family == "DUPLICATE_ID":
                doc["nodes"][rnd.randrange(1,10)]["id"] = "S_PR36_IMPORTED"
            elif family == "REMOVE_GATE_EDGE":
                next(n for n in doc["nodes"] if n["id"]=="G_REGISTRY")["depends_on"].pop()
            elif family == "PROMOTE_EXTERNAL":
                next(n for n in doc["nodes"] if n["id"]=="E_HOST_ENFORCEMENT")["scope"]="SOURCE"
            elif family == "FORGE_AUTHORITY":
                doc["authority"]="RELEASE_APPROVED"
            elif family == "WRONG_PR36_COMMIT":
                doc["baseline_pr36"]["main_commit"]="0"*40
            elif family == "EXTRA_ORPHAN":
                doc["nodes"].append({"id":"S_UNCONNECTED","scope":"SOURCE","depends_on":[]})
            elif family == "ALTER_REQUIRED_FIELDS":
                doc["activity_registry"]["required_fields"].pop()
            elif family == "CYCLE_EDGE":
                next(n for n in doc["nodes"] if n["id"]=="G_REGISTRY")["depends_on"].append("G_ONE_RUN_PRODUCT")
            else:
                doc["global_goal"]="G_SOURCE_ONLY"
            with patch("cora.integrated_registry._source",return_value=json.dumps(doc)), \
                 patch("cora.integrated_registry._original_dod",return_value={"nodes":27}):
                with self.assertRaises((ValueError,KeyError,TypeError),msg=family):
                    verify_contract(ROOT,self.sha)
        # Finite contract mutants are not 10k real-source alterations or independent oracles.
        self.assertEqual(len(families),10)


    def test_hforge_is_accounted_in_single_original_git_one_run(self):
        report = self.report
        hforge = report["hforge"]
        self.assertEqual(hforge["commit"], self.sha)
        self.assertEqual(hforge["schema"], "cora-hforge-integrated-source/1")
        self.assertEqual(hforge["state"], "PASS_SCOPED_GIT_SOURCE_AND_REPLAY")
        self.assertEqual(hforge["p4"], "PASS_ORIGINAL_ONE_RUN_SOURCE_REPLAY")
        self.assertEqual(hforge["p2"], "NOT_RUN_CONSENT_REQUIRED")
        self.assertEqual(hforge["p5"], "BLOCKED_EXTERNAL")
        self.assertEqual(hforge["native"], "NOT_RUN_REQUIRES_CONSENT")
        self.assertEqual(hforge["legacy_receipt_digest"],
                         report["baseline_pr36"]["receipt_digest"])
        rows = [r for r in report["registry"]["activities"]
                if r["activity_id"] == "stage:hforge-source"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["effect_class"], "READ_ONLY")
        self.assertEqual(rows[0]["authorization_policy"], "AUTO_SOURCE_NATIVE_OPT_IN")
        attempts = [r for r in report["attempts"]
                    if r["activity_id"] == "stage:hforge-source"]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["state"], "EXECUTED_SCOPED")
        self.assertTrue(any(g["reason"] == "HFORGE_P2_AND_P5_UNATTESTED"
                            for g in report["gaps"]["issues"]))
        self.assertTrue(verify_integrated(ROOT, report))

    def test_hforge_forged_receipts_fail_even_after_rehashed_digest(self):
        attacks = [
            lambda r: r.pop("hforge"),
            lambda r: r["hforge"].update(commit="0"*40),
            lambda r: r["hforge"].update(base="1"*40),
            lambda r: r["hforge"].update(state="PASS_PRODUCT"),
            lambda r: r["hforge"].update(native="PASS_77"),
            lambda r: r["hforge"].update(p5="PASS"),
            lambda r: r["hforge"].update(delta_bytes=-999999),
            lambda r: r["hforge"]["after"].update(tree_sha256="f"*64),
            lambda r: r["registry"]["activities"].pop(
                next(i for i,x in enumerate(r["registry"]["activities"])
                     if x["activity_id"] == "stage:hforge-source")),
            lambda r: r["attempts"].pop(
                next(i for i,x in enumerate(r["attempts"])
                     if x["activity_id"] == "stage:hforge-source")),
            lambda r: r["gaps"].update(issues=[]),
            lambda r: r["evidence_manifest"]["files"].pop(
                next(i for i,x in enumerate(r["evidence_manifest"]["files"])
                     if x["path"] == "hforge.json")),
        ]
        for i, change in enumerate(attacks):
            with self.subTest(attack=i):
                forged = copy.deepcopy(self.report)
                change(forged)
                unsigned = {k:v for k,v in forged.items()
                            if k != "receipt_digest"}
                forged["receipt_digest"] = domain_hash(
                    "CORA:integrated-one-run:2", unsigned)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    verify_integrated(ROOT, forged)

    def test_physical_git_hforge_contract_mutations_are_refused(self):
        # Real committed source edits in a disposable Git clone, not model masks.
        path = ".cora/contracts/dod/hforge-transplant-dod.json"
        mutators = (
            lambda d: d.update(authority="APPROVED"),
            lambda d: d["one_run_absorption"].update(authority="APPROVED"),
            lambda d: d["one_run_absorption"].update(native_default="PASS"),
            lambda d: d["one_run_absorption"].update(global_product="PASS"),
            lambda d: d["one_run_absorption"]["phases"].pop(),
            lambda d: d["one_run_absorption"]["invariants"].pop(),
        )
        with tempfile.TemporaryDirectory(prefix="cora-hforge-physical-") as td:
            clone = Path(td)/"clone"
            subprocess.run(["git", "clone", "--no-local", "-q", str(ROOT),
                            str(clone)], check=True)
            git(clone, "config", "user.name", "CORA HFORGE falsifier")
            git(clone, "config", "user.email", "hforge@example.invalid")
            for idx, change in enumerate(mutators):
                with self.subTest(mutant=idx):
                    git(clone, "checkout", "-q", self.sha)
                    filename = clone/path
                    doc = json.loads(filename.read_text("utf-8"))
                    change(doc)
                    filename.write_text(json.dumps(doc, indent=2)+"\\n",
                                        encoding="utf-8")
                    git(clone, "add", path)
                    git(clone, "commit", "-qm", "mutant HFORGE gate "+str(idx))
                    mutant_sha = git(clone, "rev-parse", "HEAD")
                    with self.assertRaisesRegex(ValueError, "H-FORGE"):
                        run_integrated(clone, mutant_sha)



if __name__=="__main__":
    unittest.main()
