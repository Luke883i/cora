"""Physical Git and reticular falsifiers for the complete CORA capability source atlas."""
from __future__ import annotations
import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capability_verifier", ROOT/"tools/verify_capability_atlas.py")
CAP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CAP)


def g(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode("utf-8").strip()


def fork(root):
    source = root/"repo"
    g(ROOT, "clone", "--local", "-q", str(ROOT), str(source))
    g(source, "checkout", "-q", g(ROOT, "rev-parse", "HEAD"))
    g(source, "config", "user.name", "source proof fixture")
    g(source, "config", "user.email", "source@example.invalid")
    return source


def commit_json(repo, name, mutate):
    path = repo/name
    doc = json.loads(path.read_text("utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")
    g(repo, "add", name)
    g(repo, "commit", "-qm", "physically committed adversarial change")
    return g(repo, "rev-parse", "HEAD")


class CapabilityAtlasTests(unittest.TestCase):
    def test_01_source_census_and_exact_replay(self):
        r = CAP.check(ROOT)
        self.assertEqual(r["command_count"], 71)
        self.assertEqual(r["family_count"], 8)
        self.assertEqual(r["surfaces"]["modules"], 48)
        self.assertEqual(r["surfaces"]["operational_tools"], 15)
        self.assertEqual(r["surfaces"]["github_workflows"], 12)
        self.assertEqual(r["surfaces"]["contracts"], 13)
        self.assertEqual(r["surfaces"]["markdown"], 48)
        self.assertEqual(r["surfaces"]["test_modules"], 36)
        self.assertEqual(r["authorization"], "NONE")
        self.assertEqual(r["governed_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(r["ci_final_head"], "NOT_ATTESTED_BY_SOURCE")
        self.assertTrue(all(x["test_execution"]=="NOT_ATTESTED_BY_SOURCE" for x in r["commands"]))
        self.assertTrue(CAP.replay(ROOT, r))

    def test_02_forged_receipt_fails_and_dirty_tree_not_authoritative(self):
        original = CAP.check(ROOT)
        forged = copy.deepcopy(original)
        forged["commands"][0]["test_execution"] = "PASS"
        with self.assertRaises(ValueError):
            CAP.replay(ROOT, forged)
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            witnessed=CAP.check(local)
            (local/"README.md").write_text("fake source\n", encoding="utf-8")
            self.assertEqual(CAP.check(local), witnessed)
            self.assertTrue(CAP.replay(local,witnessed))

    def test_03_physical_target_effect_reclassification(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                row=next(x for x in doc["commands"] if x["command"]=="apply-rename-doc")
                row["interaction"]="SOURCE_ANALYSIS_OR_PROPOSAL"
            sha=commit_json(local,"cora.capability-atlas.json",change)
            with self.assertRaisesRegex(ValueError,"effectful command"):
                CAP.check(local,sha)

    def test_04_physical_disconnect_cli_from_source_and_test(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                row=next(x for x in doc["commands"] if x["command"]=="audit")
                row["method_source"]="src/cora/debt.py"
            sha=commit_json(local,"cora.capability-atlas.json",change)
            with self.assertRaisesRegex(ValueError,"implementation detached"):
                CAP.check(local,sha)
            def change2(doc):
                row=next(x for x in doc["commands"] if x["command"]=="audit")
                row["method_source"]="src/cora/audit.py"
                row["test_source"]="tests/nonexistent.py"
            sha=commit_json(local,"cora.capability-atlas.json",change2)
            with self.assertRaises(ValueError):
                CAP.check(local,sha)

    def test_05_physical_dod_edge_and_chronology_mutants(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                next(x for x in doc["nodes"] if x["id"]=="G_CAP_SOURCE")["depends_on"].pop()
            sha=commit_json(local,"cora.capability-dod.json",change)
            with self.assertRaisesRegex(ValueError,"DoD edge"):
                CAP.check(local,sha)
            # Restore the failed reticular mutation before the independent
            # documentation falsifier; otherwise a stale DoD could mask it.
            contract=local/"cora.capability-dod.json"
            contract.write_bytes((ROOT/"cora.capability-dod.json").read_bytes())
            g(local,"add","cora.capability-dod.json")
            g(local,"commit","-qm","restore DoD before chronology test")
            self.assertEqual(CAP.check(local)["source_status"],"PASS_SCOPED_SOURCE")
            path=local/"docs/ARCHITECTURE.md"
            text=path.read_text("utf-8").replace("merged PR-25","merged PR-22")
            path.write_text(text,encoding="utf-8")
            g(local,"add","docs/ARCHITECTURE.md")
            g(local,"commit","-qm","historical claim promoted to current")
            with self.assertRaisesRegex(ValueError,"current documentation chronology"):
                CAP.check(local)

    def test_06_physical_removed_workflow_and_reader_claim(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            (local/".github/workflows/ci-selection.yml").unlink()
            g(local,"add","-A")
            g(local,"commit","-qm","unexpected workflow retirement")
            with self.assertRaisesRegex(ValueError,"repository inventory drift"):
                CAP.check(local)
            # No implied permission to retire it from mere source absence.
            self.assertEqual(CAP.check(ROOT)["authorization"],"NONE")

    def test_07_thousand_finite_noncompensatory_mutants(self):
        original=json.loads((ROOT/"cora.capability-dod.json").read_text("utf-8"))
        seen=set()
        for family in range(10):
            for i in range(100):
                mutated=copy.deepcopy(original)
                mutated["nodes"][0]["description"] += " variant %03d" % i
                if family==0: mutated["authority"]="APPROVED"
                elif family==1: mutated["external_status"]="PASS"
                elif family==2: mutated["ci_status"]="PASSED_IN_SOURCE"
                elif family==3: next(x for x in mutated["nodes"] if x["id"]=="G_CAP_SOURCE")["depends_on"].pop()
                elif family==4: next(x for x in mutated["nodes"] if x["id"]=="G_CAP_ACCEPTED")["depends_on"].pop()
                elif family==5: next(x for x in mutated["nodes"] if x["id"]=="I_IDENTITY")["depends_on"].pop()
                elif family==6: next(x for x in mutated["nodes"] if x["id"]=="E01")["scope"]="SOURCE"
                elif family==7: next(x for x in mutated["nodes"] if x["id"]=="E02")["scope"]="SOURCE"
                elif family==8: mutated["nodes"][0]["id"]="C02"
                else: mutated["nodes"][0]["depends_on"]=["MISSING"]
                string=json.dumps(mutated,sort_keys=True)
                self.assertNotIn(string,seen)
                seen.add(string)
                with self.assertRaises(ValueError):
                    CAP.verify_dod(mutated)
        self.assertEqual(len(seen),1000)


if __name__=="__main__":
    unittest.main()
