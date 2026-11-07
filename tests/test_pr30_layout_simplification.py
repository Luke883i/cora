"""PR30: Git-bound lossless layout, front-door and 10k seeded counterexamples."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "layout_verifier",ROOT/"tools/verify_layout_simplification.py")
LAYOUT=importlib.util.module_from_spec(spec)
spec.loader.exec_module(LAYOUT)


def git(repo:Path,*args:str)->str:
    return subprocess.check_output(["git","-C",str(repo),*args],
                                   stderr=subprocess.PIPE).decode().strip()


def change(repo:Path,path:str,mutator)->str:
    p=repo/path
    old=p.read_text("utf-8")
    p.write_text(mutator(old),encoding="utf-8")
    git(repo,"add",path)
    git(repo,"commit","-qm","original Git physical layout negative mutation")
    return git(repo,"rev-parse","HEAD")


class LayoutSimplificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/".git").exists():
            raise unittest.SkipTest("original Git checkout required")
        cls.head=git(ROOT,"rev-parse","HEAD")

    def test_01_lossless_archive_root_and_source_replay(self):
        report=LAYOUT.check(ROOT,self.head)
        self.assertEqual(report["root_before"],25)
        self.assertEqual(report["root_after"],11)
        self.assertEqual(report["top_level_docs_removed"],14)
        self.assertEqual(report["historical_blobs_preserved"],14)
        self.assertEqual(report["fixture_blobs_preserved"],1)
        self.assertEqual(report["internal_contract_blobs_preserved"],2)
        self.assertEqual(report["thematic_byte_identical"],8)
        self.assertEqual(report["thematic_structural_rewrites"],3)
        self.assertEqual(report["remaining_root_cora_json"],2)
        self.assertEqual(report["registered_markdown"],48)
        self.assertEqual(report["historical_records"],17)
        self.assertEqual(report["cli_commands"],71)
        self.assertEqual(report["dod"]["nodes"],23)
        self.assertEqual(report["authorization"],"NONE")
        self.assertTrue(LAYOUT.verify(ROOT,report))
        forged=copy.deepcopy(report)
        forged["historical_blobs_preserved"]=0
        with self.assertRaisesRegex(ValueError,"forged"):
            LAYOUT.verify(ROOT,forged)

    def test_02_seeded_ten_thousand_twice_and_bounds(self):
        a=LAYOUT.stress(ROOT,self.head,cases=10000,seed=883)
        b=LAYOUT.stress(ROOT,self.head,cases=10000,seed=883)
        self.assertEqual(a,b)
        self.assertEqual(a["families"],32)
        self.assertEqual(a["positive_controls"],626)
        self.assertEqual(a["negative_scenarios"],9374)
        self.assertEqual(a["oracle_disagreements"],0)
        self.assertEqual(a["unauthorized_promotions"],0)
        self.assertEqual(a["distinct_case_indices"],10000)
        self.assertEqual(a["actual_git_source_mutants"],0)
        self.assertFalse(a["product_ready"])
        self.assertEqual(a["external"],"BLOCKED_EXTERNAL")
        with self.assertRaises(ValueError):
            LAYOUT.stress(ROOT,self.head,cases=10001)

    def test_03_physical_historical_blob_and_readme_mutants(self):
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/"local"
            subprocess.run(["git","clone","--no-local","-q",str(ROOT),str(local)],check=True)
            git(local,"config","user.name","CORA original source mutant")
            git(local,"config","user.email","mutant@example.invalid")
            git(local,"checkout","-q",self.head)
            historical="docs/archive/decisions/ADR-PR01.md"
            sha=change(local,historical,lambda text:text+"\nFORGED ARCHIVAL EDIT\n")
            with self.assertRaisesRegex(ValueError,"Git blob changed"):
                LAYOUT.check(local,sha)
            git(local,"checkout","-q",self.head)
            sha=change(local,"README.md",
                       lambda text:text.replace(
                           "**Engineering evidence for AI-assisted software changes.**",
                           "**Product correctness is fully proven.**",1))
            with self.assertRaisesRegex(ValueError,"README source promise lost"):
                LAYOUT.check(local,sha)

    def test_04_physical_preseed_oracle_and_dod_cut_mutants(self):
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/"local"
            subprocess.run(["git","clone","--no-local","-q",str(ROOT),str(local)],check=True)
            git(local,"config","user.name","CORA preseed mutant")
            git(local,"config","user.email","mutant@example.invalid")
            git(local,"checkout","-q",self.head)
            path=".cora/layout-preseed.json"
            def poison(text):
                p=json.loads(text)
                p["mutants"][2]["invalidated"]=[]
                return json.dumps(p,indent=2)+"\n"
            sha=change(local,path,poison)
            with self.assertRaisesRegex(ValueError,"preseed case oracle poisoned"):
                LAYOUT.stress(local,sha,cases=10000)
            git(local,"checkout","-q",self.head)
            def cut(text):
                p=json.loads(text)
                next(n for n in p["nodes"] if n["id"]=="G_GOVERNED")["depends_on"].remove("E_HOST")
                return json.dumps(p,indent=2)+"\n"
            sha=change(local,".cora/layout-dod.json",cut)
            with self.assertRaisesRegex(ValueError,"missing dependency"):
                LAYOUT.check(local,sha)

    def test_06_internal_dod_blob_forgery_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/"local"
            subprocess.run(["git","clone","--no-local","-q",str(ROOT),str(local)],check=True)
            git(local,"config","user.name","CORA internal DoD proof")
            git(local,"config","user.email","mutant@example.invalid")
            git(local,"checkout","-q",self.head)
            for moved_path in (".cora/contracts/dod/workflow-dod.json",
                               ".cora/contracts/dod/integrated-dod.json"):
                git(local,"checkout","-q",self.head)
                def poison(text):
                    obj=json.loads(text)
                    obj["authority"]="APPROVED_BY_MUTANT"
                    return json.dumps(obj,indent=2)
                sha=change(local,moved_path,poison)
                with self.assertRaisesRegex(ValueError,"internal DoD original Git blob changed"):
                    LAYOUT.check(local,sha)

    def test_07_structural_catalog_mutation_and_routing_attack(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=Path(directory)/"copy"
            subprocess.run(["git","clone","--no-local","-q",str(ROOT),str(repo)],check=True)
            git(repo,"config","user.name","CORA thematic source falsifier")
            git(repo,"config","user.email","fixture@example.invalid")
            git(repo,"checkout","-q",self.head)
            catalog=".cora/assurance/capability-atlas.json"
            def alter(payload):
                data=json.loads(payload)
                data["authority"]="FORGED_ACCEPTED"
                return json.dumps(data,indent=2)
            tampered=change(repo,catalog,alter)
            with self.assertRaisesRegex(ValueError,"thematic Git source/target identity drift"):
                LAYOUT.check(repo,tampered)
            git(repo,"checkout","-q",self.head)
            contract=".cora/contracts/index.json"
            def forge_route(payload):
                data=json.loads(payload)
                next(r for r in data["bindings"] if r["logical"]=="cora.agent-dod.json")["canonical"]="cora.agent-dod.json"
                return json.dumps(data,indent=2)
            tampered=change(repo,contract,forge_route)
            with self.assertRaisesRegex(ValueError,"logical contract path index"):
                LAYOUT.check(repo,tampered)

    def test_pr42_postmigration_readme_authority_and_s04_mutants(self):
        """Historical migration bytes stay fixed; live proof edit is tightly scoped."""
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/"local"
            subprocess.run(["git","clone","--no-local","-q",
                            str(ROOT),str(local)],check=True)
            git(local,"config","user.name","CORA README migrated DoD mutant")
            git(local,"config","user.email","mutant@example.invalid")
            for path,field in (
                (".cora/contracts/dod/documentation-dod.json","authority"),
                (".cora/assurance/documentation-proofs.json","section"),
            ):
                git(local,"checkout","-q",self.head)
                def poison(text):
                    data=json.loads(text)
                    if field=="authority":
                        data["readme_refactor"]["accepted"]="APPROVED_BY_SOURCE"
                    else:
                        next(n for n in data["nodes"] if n["id"]=="S04")[
                            "readme_section"]="## Self-approved source"
                    return json.dumps(data,indent=2)+"\n"
                mutant=change(local,path,poison)
                diagnostic=("unauthorized postmigration README DoD evolution"
                            if field=="authority" else
                            "unauthorized postmigration S01-S18 proof edit")
                with self.assertRaisesRegex(ValueError,diagnostic):
                    LAYOUT.check(local,mutant)

    def test_05_link_and_atlas_integrity_also_existing_verifier(self):
        from cora.artifact_roles import artifact_audit
        from cora.git_snapshot import snapshot
        from importlib import util
        d=importlib.util.spec_from_file_location(
            "original_documentation_verifier",ROOT/"tools/verify_documentation.py")
        module=util.module_from_spec(d)
        d.loader.exec_module(module)
        self.assertEqual(module.verify(ROOT),[])
        report=artifact_audit(ROOT,self.head)
        self.assertEqual(report["summary"]["unclassified"],0)
        self.assertEqual(report["summary"]["stale_rules"],[])
        self.assertEqual(len(snapshot(ROOT,self.head)["records"])>0,True)

if __name__=="__main__":
    unittest.main()
