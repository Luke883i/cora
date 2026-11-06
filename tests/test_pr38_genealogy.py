"""PR38: all 37 PRs/305 commit deltas, nonmerge, lifecycle and atlas falsifiers."""
from __future__ import annotations

import copy
import json
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.genealogy import (
    BASE, DOD, HISTORY, build_genealogy, verify_dod_document,
    verify_history_document, _files, _delta, corpus_available, git_commit_headers,
)
from cora.integrated_run import run_integrated, verify_integrated
from cora.integrated_html import render_integrated_html

ROOT = Path(__file__).resolve().parents[1]


def g(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode().strip()


class HistoryReticularTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").is_dir():
            raise unittest.SkipTest("requires exact original Git checkout")
        cls.sha = g(ROOT, "rev-parse", "HEAD")
        cls.data = json.loads((ROOT / HISTORY).read_text("utf-8"))
        cls.dod = json.loads((ROOT / DOD).read_text("utf-8"))
        cls.headers = git_commit_headers(ROOT)
        cls.report = build_genealogy(ROOT, cls.sha)

    def test_01_individual_305_deltas_and_original_base(self):
        self.assertTrue(verify_dod_document(self.dod))
        self.assertTrue(verify_history_document(self.data, _files(ROOT, BASE), git_headers=self.headers))
        self.assertEqual(self.data["pr_count"], 37)
        self.assertEqual(self.data["unit_count"], 305)
        # PR24 scans text consumers under a strict per-file budget; preserve it.
        # The 305-unit machine record must stay bounded without relaxing that guard.
        self.assertLessEqual((ROOT / HISTORY).stat().st_size, 512 * 1024)
        self.assertEqual(self.data["closed_unmerged_prs"], [34])
        self.assertEqual(self.data["merged_prs"], 36)
        self.assertEqual(sum(p["commit_count"] for p in self.data["prs"]), 305)
        self.assertEqual(self.data["base_main_commit"], BASE)
        self.assertEqual(self.data["base_main_tree"],g(ROOT,"rev-parse",BASE+"^{tree}"))
        for p in self.data["prs"]:
            self.assertEqual(p["head_sha"],p["commits"][-1]["sha"])
            for commit in p["commits"]:
                self.assertEqual(commit["stats"]["total"],
                                 commit["stats"]["additions"]+commit["stats"]["deletions"])
                self.assertTrue(commit["paths"])
                self.assertNotEqual(commit["unit_epistemic_state"],"PASS_RUNTIME")

    def test_02_current_vs_historical_paths_no_deletion(self):
        r = self.report
        self.assertEqual(r["pr_count"],37)
        self.assertEqual(r["commit_count"],305)
        self.assertEqual(r["closed_unmerged"],[34])
        self.assertEqual(r["product_status"],"BLOCKED_EXTERNAL")
        self.assertEqual(r["authorization"],"NONE")
        self.assertEqual(r["retention"]["current_source_modules_removal_authorized"],0)
        self.assertEqual(r["retention"]["historical_or_relocated_count"],28)
        self.assertEqual(len({x["canonical_path"] for x in r["retention"]["candidates"]}),28)
        self.assertTrue(all(x["canonical_present_at_base"] for x in r["retention"]["candidates"]))
        self.assertTrue(all(x["canonical_path"] in _files(ROOT,BASE)
                            for x in r["retention"]["candidates"]))
        self.assertTrue(all(x["deletion_authorized"] is False
                            for x in r["retention"]["candidates"]))
        self.assertGreaterEqual(r["module_liveness"]["module_count"],56)
        self.assertEqual(r["module_liveness"]["automatic_deletion"],"NONE")
        self.assertTrue(all(x["safe_to_delete"] is False
                            for x in r["module_liveness"]["candidates"]))
        self.assertEqual(r["history_dod"]["source"],
                         "DEBT_BLOCKED_SOURCE_BENCHMARK_AND_FUTURE_CHECKS")
        self.assertEqual(len(r["prs"]),37)
        self.assertEqual(sum(len(p["commits"]) for p in r["prs"]),305)

    def test_03_dod_negative_surfaces_and_explicit_scope(self):
        bad = copy.deepcopy(self.dod)
        next(x for x in bad["nodes"] if x["id"] == "E01_INDEPENDENT_CODE_REVIEW")["scope"] = "SOURCE"
        with self.assertRaisesRegex(ValueError,"scope"):
            verify_dod_document(bad)
        bad = copy.deepcopy(self.dod)
        next(x for x in bad["nodes"] if x["id"] == "G_HISTORY_COVERAGE")["depends_on"].pop()
        with self.assertRaisesRegex(ValueError,"edge"):
            verify_dod_document(bad)
        bad = copy.deepcopy(self.dod)
        bad["authority"] = "RELEASE_APPROVED"
        with self.assertRaisesRegex(ValueError,"identity"):
            verify_dod_document(bad)

    def test_04_pr34_and_commit_delta_forgery_rejected(self):
        changes = (
            lambda x: x["prs"][33].update(merge_status="MERGED_SOURCE_RECORDED"),
            lambda x: x["prs"][33].update(merged_at="2026-11-06T12:00:00Z"),
            lambda x: x["prs"][0]["commits"].pop(),
            lambda x: x["prs"][0]["commits"][0].update(tree="0"*40),
            lambda x: x["prs"][1]["commits"][0]["stats"].update(total=-2),
            lambda x: x["prs"][4]["commits"][0]["paths"][0].update(path="../outside.py"),
            lambda x: x["prs"][20]["commits"][0].update(
                unit_epistemic_state="INDEPENDENT_RUNTIME_PASS"),
            lambda x: x.update(base_main_commit="0"*40),
            lambda x: x["prs"][3]["commits"][0].update(currently_present_paths=[]),
        )
        current=_files(ROOT,BASE)
        for fn in changes:
            mutant=copy.deepcopy(self.data)
            fn(mutant)
            with self.subTest(fn=fn.__code__.co_firstlineno):
                with self.assertRaises((ValueError,TypeError,KeyError)):
                    verify_history_document(mutant,current,git_headers=self.headers)

    def test_05_ten_thousand_finite_noncompensatory_model_mutants(self):
        rng=random.Random(883)
        faults=0
        for i in range(10000):
            mutated=copy.deepcopy(self.dod)
            family=i%12
            if family==0:
                mutated["nodes"].pop(rng.randrange(18))
            elif family==1:
                mutated["nodes"][rng.randrange(1,18)]["id"]=mutated["nodes"][0]["id"]
            elif family==2:
                next(x for x in mutated["nodes"] if x["id"]=="E01_INDEPENDENT_CODE_REVIEW")["scope"]="SOURCE"
            elif family==3:
                next(x for x in mutated["nodes"] if x["id"]=="G_HISTORY_COVERAGE")["depends_on"].append("FAKE_"+str(i))
            elif family==4:
                next(x for x in mutated["nodes"] if x["id"]=="G_HISTORY_COVERAGE")["depends_on"].pop()
            elif family==5:
                mutated["authority"]="APPROVED_"+str(i)
            elif family==6:
                mutated["baseline_main"]=("%040x" % (i+1))
            elif family==7:
                mutated["controls"]["historical_pr_count"]=38+i
            elif family==8:
                mutated["controls"]["execution_boundary"]="ALL_EXECUTED_"+str(i)
            elif family==9:
                mutated["checklist"].pop()
            elif family==10:
                mutated["falsification"]["cases"]=10001+i
            else:
                mutated["global_goal"]="G_SOURCE_ONLY_"+str(i)
            with self.assertRaises((ValueError,TypeError,KeyError),msg=str(family)):
                verify_dod_document(mutated)
            faults+=1
        self.assertEqual(faults,10000)
        # 10k finite vectors are not 10k physical repository mutations or
        # independently witnessed defects; actual Git mutants are tested separately.

    def test_06_physical_git_doD_and_nonmerged_status_mutants(self):
        with tempfile.TemporaryDirectory() as tmp:
            local=Path(tmp)/"clone"
            subprocess.run(["git","clone","-q","--local",str(ROOT),str(local)],check=True)
            g(local,"checkout","-q",self.sha)
            g(local,"config","user.name","PR38 source oracle")
            g(local,"config","user.email","oracle@example.invalid")
            original=(local/DOD).read_bytes()
            altered=json.loads(original)
            next(x for x in altered["nodes"] if x["id"]=="E02_REAL_TARGET_BENCHMARK")["scope"]="SOURCE"
            (local/DOD).write_text(json.dumps(altered))
            g(local,"add",DOD)
            g(local,"commit","-qm","physical Git DoD external-promotion attempt")
            with self.assertRaisesRegex(ValueError,"scope"):
                build_genealogy(local,g(local,"rev-parse","HEAD"))
            (local/DOD).write_bytes(original)
            history=json.loads((local/HISTORY).read_text("utf-8"))
            history["prs"][33]["merge_status"]="MERGED_SOURCE_RECORDED"
            (local/HISTORY).write_text(json.dumps(history))
            g(local,"add",DOD,HISTORY)
            g(local,"commit","-qm","physical original-Git PR34 history forgery")
            with self.assertRaisesRegex(ValueError,"PR34"):
                build_genealogy(local,g(local,"rev-parse","HEAD"))
            self.assertTrue(corpus_available(local,self.sha))

    def test_06b_committed_false_relocation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            local=Path(tmp)/"clone"
            subprocess.run(["git","clone","-q","--local",str(ROOT),str(local)],check=True)
            g(local,"checkout","-q",self.sha)
            g(local,"config","user.name","PR38 migration oracle")
            g(local,"config","user.email","oracle@example.invalid")
            path=local/".cora/layout-migration.json"
            doc=json.loads(path.read_text("utf-8"))
            doc["moves"][0]["new"]="docs/archive/nonexistent-historic.md"
            path.write_text(json.dumps(doc))
            g(local,"add",".cora/layout-migration.json")
            g(local,"commit","-qm","forged historical layout migration")
            with self.assertRaisesRegex(ValueError,"migration mapping"):
                build_genealogy(local,g(local,"rev-parse","HEAD"))

    def test_07_future_unregistered_module_creates_debt_not_auto_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            local=Path(tmp)/"clone"
            subprocess.run(["git","clone","-q","--local",str(ROOT),str(local)],check=True)
            g(local,"checkout","-q",self.sha)
            g(local,"config","user.name","PR38 unknown-feature fixture")
            g(local,"config","user.email","oracle@example.invalid")
            path=local/"src/cora/pr38_unregistered_future.py"
            path.write_text("def feature():\n    return 7\n")
            g(local,"add","src/cora/pr38_unregistered_future.py")
            g(local,"commit","-qm","unknown future feature without canonical registry")
            result=_delta(local,g(local,"rev-parse","HEAD"))
            self.assertEqual(result["catalog_status"],"DEBT_BLOCKED_UNREGISTERED")
            self.assertIn("src/cora/pr38_unregistered_future.py",
                          [x["path"] for x in result["catalog_violations"]])
            self.assertEqual(result["external"],"BLOCKED_EXTERNAL")

    def test_08_same_pr37_orchestrator_replay_and_human_navigable_html(self):
        bundle=run_integrated(ROOT,self.sha,process="source",max_commits=4)
        self.assertEqual(bundle["genealogy"],self.report)
        self.assertEqual(bundle["product_status"],"BLOCKED_EXTERNAL")
        self.assertEqual(bundle["authorization"],"NONE")
        page=render_integrated_html(bundle)
        self.assertTrue(verify_integrated(ROOT,bundle,html_page=page))
        self.assertIn('id="history"',page)
        self.assertIn('id="pr-34"',page)
        self.assertIn('</ul></details><h3>Current software module retention candidates</h3>',page)
        self.assertIn('href="https://github.com/Luke883i/cora/pull/34"',page)
        self.assertIn("Search PR, SHA, file or method",page)
        self.assertIn("CLOSED_UNMERGED",page)
        self.assertIn("git",page)
        self.assertIn("305",page)
        forged=copy.deepcopy(bundle)
        forged["genealogy"]["prs"][33]["state"]="MERGED"
        with self.assertRaisesRegex(ValueError,"genealogy"):
            verify_integrated(ROOT,forged)

    def test_09_history_html_escape_and_source_boundary(self):
        bundle=run_integrated(ROOT,self.sha,process="source",max_commits=4)
        forged=copy.deepcopy(bundle)
        forged["genealogy"]["prs"][0]["title"]='<img src=x onerror="alert(1)">'
        rendered=render_integrated_html(forged)
        self.assertNotIn('<img src=x onerror="alert(1)">',rendered)
        self.assertIn("&lt;img src=x",rendered)
        self.assertIn("0",rendered)
        self.assertIn("BLOCKED_EXTERNAL",rendered)
        forged["genealogy"]["prs"][0]["pr_url"]="javascript:alert(1)"
        escaped_link=render_integrated_html(forged)
        self.assertNotIn("javascript:alert(1)",escaped_link)
        self.assertIn('href="https://github.com/Luke883i/cora/pull/1"',escaped_link)


    def test_10_git_original_changed_paths_replayed_for_every_merged_unit(self):
        """301 merged PR commit units: compare GitHub census with original Git diff-tree.

        PR34's four closed-unmerged commits remain explicitly NOT OBSERVED here:
        they are not reachable from the original main ancestry and are not passed.
        """
        verified, withheld = 0, []
        for pr in self.data["prs"]:
            for unit in pr["commits"]:
                sha = unit["sha"]
                if sha not in self.headers:
                    withheld.append((pr["number"], sha))
                    continue
                raw = subprocess.check_output(
                    ["git", "-C", str(ROOT), "diff-tree", "--no-commit-id",
                     "--name-only", "-r", "-z", "-M", sha],
                    stderr=subprocess.PIPE, timeout=15)
                original = {v.decode("utf-8") for v in raw.split(b"\0") if v}
                declared = {entry["path"] for entry in unit["paths"]}
                with self.subTest(pr=pr["number"], commit=sha):
                    self.assertEqual(original, declared)
                verified += 1
        self.assertEqual(verified, 301)
        self.assertEqual(len(withheld), 4)
        self.assertEqual({pr for pr, _ in withheld}, {34})


if __name__ == "__main__":
    unittest.main()
