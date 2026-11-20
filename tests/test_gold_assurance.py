"""PR19: real Git readback, physical temp-file mutations, adversarial model tests."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from cora.gold_assurance import load_gold_contract, retrograde_gold, pilot_sources, contextual_gold, blob_sha
from cora.gold_mutations import physical_mutants
from cora.gold_effects import audit_workflow, reconcile_effect_claim
from cora.gold_saturation import gold_saturation
from cora.cli import main

BASE=Path(__file__).resolve().parents[1]
POLICY=BASE/".cora/contracts/dod/gold-assurance.json"

def git(root,*args):
    p=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=True)
    return p.stdout.strip()

class GoldReticularAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=load_gold_contract(POLICY)

    def test_noncompensatory_backward_graph_and_boundaries(self):
        plan=retrograde_gold(self.contract)
        full=retrograde_gold(self.contract,"G_GOLD_GOVERNED")
        self.assertEqual(len(plan["local_cut"]),12)
        self.assertEqual(len(full["local_cut"]),16)
        self.assertEqual(plan["nodes"][-1],"G_GOLD_SOURCE")
        self.assertEqual(full["nodes"][-1],"G_GOLD_GOVERNED")
        self.assertEqual(len(full["nodes"]),23)
        self.assertEqual(plan,retrograde_gold(self.contract))
        self.assertEqual(full["authorization"],"NONE")

    def test_sixteen_physical_json_policy_mutants_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"contract.json"
            for i in range(16):
                item=copy.deepcopy(self.contract)
                item["nodes"][i]["family"]="forged-family"
                path.write_text(json.dumps(item),encoding="utf-8")
                with self.subTest(i=i):
                    with self.assertRaises(ValueError):
                        load_gold_contract(path)

    def test_structural_dod_mutants_rejected(self):
        bad=[
            lambda x:x["nodes"].pop(),
            lambda x:x["nodes"][16]["depends_on"].pop(),
            lambda x:x["nodes"][22].update({"scope":"SOURCE"}),
            lambda x:x["nodes"][0].update({"scope":"EXTERNAL"}),
            lambda x:x["nodes"][0].update({"id":"L02"}),
            lambda x:x["roots"].update({"governed":"G_GOLD_SOURCE"}),
            lambda x:x["patterns"][0].update({"gate":"I_EXTERNAL"}),
            lambda x:x["seeded_campaign"].update({"sessions":1}),
            lambda x:x["pilots"][0]["owner"].update({"git_blob":"0"*40}),
            lambda x:x["epistemic_boundary"].update({"authorization":"MERGE"}),
        ]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"m.json"
            for i,op in enumerate(bad):
                c=copy.deepcopy(self.contract)
                op(c)
                path.write_text(json.dumps(c),encoding="utf-8")
                with self.subTest(i=i):
                    # A different syntactically valid Git blob is an external
                    # source input and will be refuted at readback, not by schema.
                    if i==8:
                        self.assertEqual(load_gold_contract(path)["pilots"][0]["owner"]["git_blob"],"0"*40)
                    else:
                        with self.assertRaises(ValueError):
                            load_gold_contract(path)

    def _three_local_checkouts(self,base:Path):
        c=copy.deepcopy(self.contract)
        roots={}
        for index,p in enumerate(c["pilots"]):
            root=base/str(index)
            root.mkdir()
            git(root,"init","-q")
            git(root,"config","user.email","audit@example.invalid")
            git(root,"config","user.name","Audit Fixture")
            for slot in ("owner","sample"):
                spec=p[slot]
                data=(spec["marker"]+"\n# source-bound fixture\n").encode()
                target=root/spec["path"]
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
                spec["git_blob"]=blob_sha(data)
            git(root,"add",".")
            git(root,"commit","-qm","frozen source fixture")
            p["revision"]=git(root,"rev-parse","HEAD")
            roots[p["repo"]]=root
        return c,roots

    def test_three_repo_sha_bound_pilots_and_source_drift(self):
        self.assertEqual(pilot_sources(self.contract,{})["state"],"BLOCKED_INCOMPLETE")
        with tempfile.TemporaryDirectory() as td:
            c,roots=self._three_local_checkouts(Path(td))
            partial=pilot_sources(c,{c["pilots"][0]["repo"]:roots[c["pilots"][0]["repo"]]})
            self.assertEqual(partial["state"],"BLOCKED_INCOMPLETE")
            self.assertEqual(partial["source_readbacks_verified"],1)
            self.assertEqual(partial["source_readbacks_required"],3)
            self.assertEqual(partial["unresolved_repositories"],["Luke883i/ikant","Luke883i/aosp1"])
            self.assertEqual(partial["pilots"][1]["files"][0]["reason"],"NO_EXPLICIT_PINNED_CHECKOUT")
            self.assertEqual(partial["external"],"BLOCKED_EXTERNAL")
            self.assertEqual(partial["authorization"],"NONE")
            r=pilot_sources(c,roots)
            self.assertEqual(r["source_readbacks_verified"],3)
            self.assertEqual(r["unresolved_repositories"],[])
            self.assertEqual(r["state"],"SOURCE_READBACK_3_OF_3")
            self.assertEqual(len(r["pilots"]),3)
            self.assertTrue(all(x["owner_semantics"]=="DECLARED_NOT_INDEPENDENTLY_ATTESTED" for x in r["pilots"]))
            fake=contextual_gold(c,"Make coding agents accountable for exact-source change",r)
            self.assertEqual(fake["nearest_unresolved"],"L01")
            self.assertEqual(fake["pilot_provenance"],"UNTRUSTED_CLAIM_NOT_SOURCE_REPLAY")
            ctx=contextual_gold(c,"Make coding agents accountable for exact-source change",roots=roots)
            self.assertEqual(ctx["state"],"BLOCKED_MATERIAL_PRODUCT_PROOF")
            self.assertEqual(ctx["nearest_unresolved"],"L02")
            self.assertFalse(ctx.get("release_authorized",False))
            altered=copy.deepcopy(c)
            altered["pilots"][0]["sample"]["git_blob"]="a"*40
            self.assertEqual(pilot_sources(altered,roots)["state"],"BLOCKED_INCOMPLETE")
            path=roots[c["pilots"][0]["repo"]]/"changed.txt"
            path.write_text("change")
            git(roots[c["pilots"][0]["repo"]],"add",".")
            git(roots[c["pilots"][0]["repo"]],"commit","-qm","new HEAD invalidates old pilot")
            self.assertEqual(pilot_sources(c,roots)["state"],"BLOCKED_INCOMPLETE")

    def test_physical_mutant_baseline_killed_survived_not_confused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"target.py").write_text("def f():\n    return 1\n",encoding="utf-8")
            plan={"schema":"cora-physical-mutants/1","oracle":{"kind":"PYTHON_AST","path":"target.py"},
                  "mutants":[
                    {"id":"syntax-killed","path":"target.py","old":"return 1","new":"return ???"},
                    {"id":"semantic-survived","path":"target.py","old":"return 1","new":"return 0"}
                  ]}
            receipt=physical_mutants(root,plan)
            self.assertEqual(receipt["counts"],{"killed":1,"survived":1,"timeout":0,"inconclusive":0})
            self.assertEqual(receipt["status"],"BLOCKED_MUTANT_SURVIVOR_OR_UNKNOWN")
            self.assertIn("return 1",(root/"target.py").read_text())
            self.assertFalse(receipt["sandbox_attested"])

    def test_no_implicit_docker_execution_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"target.py").write_text("x=1")
            plan={"schema":"cora-physical-mutants/1",
                  "oracle":{"kind":"DOCKER_TEST","image":"python:3.11-slim",
                            "command":["python","-m","unittest","discover"]},
                  "mutants":[{"id":"syntax","path":"target.py","old":"x=1","new":"x=2"}]}
            r=physical_mutants(root,plan)
            self.assertEqual(r["status"],"BLOCKED_BASELINE_NOT_PROVEN")
            self.assertEqual(r["baseline"],"INCONCLUSIVE")
            self.assertEqual(r["counts"]["inconclusive"],1)
            (root/"out").symlink_to(root/"target.py")
            with self.assertRaises(ValueError):
                physical_mutants(root,plan)

    def test_explicit_docker_uses_private_temp_owner_and_pinned_no_network_image(self):
        from cora.gold_mutations import _oracle
        with tempfile.TemporaryDirectory() as td:
            oracle={"kind":"DOCKER_TEST","image":"python@sha256:"+("a"*64),
                    "command":["python","-m","unittest","discover"]}
            with patch("cora.gold_mutations.os.getuid",return_value=1001), \
                 patch("cora.gold_mutations.os.getgid",return_value=1002), \
                 patch("cora.gold_mutations.subprocess.run",
                       return_value=Mock(returncode=0)) as run:
                self.assertEqual(_oracle(Path(td),oracle,authorized=True),"PASS")
                args=run.call_args.args[0]
                self.assertIn("--user=1001:1002",args)
                self.assertIn("--network=none",args)
                self.assertIn("--read-only",args)
                self.assertIn("--pull=never",args)
                self.assertIn("python@sha256:"+("a"*64),args)
                self.assertNotIn("--user=65534:65534",args)
            with patch("cora.gold_mutations.os.getuid",return_value=0), \
                 patch("cora.gold_mutations.subprocess.run") as run:
                with self.assertRaises(ValueError):
                    _oracle(Path(td),oracle,authorized=True)
                run.assert_not_called()
            with patch("cora.gold_mutations.subprocess.run") as run:
                self.assertEqual(_oracle(Path(td),oracle,authorized=False),"INCONCLUSIVE")
                run.assert_not_called()
            oracle["image"]="python:3.11-slim"
            with self.assertRaises(ValueError):
                _oracle(Path(td),oracle,authorized=True)

    def test_workflow_effects_are_potential_not_executed(self):
        sha="b"*40
        clean="name: Probe\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        active=clean.replace("contents: read","contents: write")
        a=audit_workflow(active,path=".github/workflows/test.yml",revision=sha)
        self.assertIn("DECLARED_WRITE_CAPABILITY",a["potential_effects"])
        fake={"revision":sha,"source_sha256":a["source_sha256"],
              "target":"refs/heads/main","readback":True}
        r=reconcile_effect_claim(a,fake)
        self.assertTrue(r["state"].startswith("COHERENT_UNTRUSTED"))
        self.assertFalse(r["independent_host_attestation"])
        self.assertEqual(r["authorization"],"NONE")
        self.assertEqual(audit_workflow(clean,path="a.yml",revision=sha)["actual_effect"],"NOT_OBSERVED")

    def test_preseeded_faults_model_replay_and_faulty_generator(self):
        x=gold_saturation(self.contract,sessions=1,cases_per_session=2000)
        self.assertEqual(x,gold_saturation(self.contract,sessions=1,cases_per_session=2000))
        self.assertEqual(x["status"],"PARTIAL_NOT_10M")
        self.assertEqual(x["receipts"][0]["observed_singles"],12)
        self.assertEqual(x["receipts"][0]["observed_pairs"],66)
        self.assertEqual(x["unsafe_promotions"],0)
        with patch("cora.gold_saturation._scenario",return_value=0):
            negative=gold_saturation(self.contract,sessions=1,cases_per_session=300)
        self.assertEqual(negative["status"],"REFUTED")
        with patch("cora.gold_saturation._model",return_value=("MODEL_ELIGIBLE_UNATTESTED","GO")):
            negative=gold_saturation(self.contract,sessions=1,cases_per_session=300)
        self.assertEqual(negative["status"],"REFUTED")

    def test_cli_gold_plan_and_finite_model_scoped_exit(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"report.json"
            self.assertEqual(main(["gold-plan","--contract",str(POLICY),
                "--intent","Deliver verified repository-specific DoD","--output",str(out)]),0)
            self.assertEqual(json.loads(out.read_text())["authorization"],"NONE")
            self.assertEqual(main(["gold-pilot","--contract",str(POLICY),"--output",str(out)]),2)
            self.assertEqual(main(["stress-gold","--contract",str(POLICY),
                "--sessions","1","--cases-per-session","300","--require-full",
                "--output",str(out)]),2)
            self.assertEqual(json.loads(out.read_text())["real_source_mutations"],0)


if __name__=="__main__":
    unittest.main()
