"""PR39: independent behavior source references, four noncompensatory product gates."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from cora.evidence import domain_hash
from cora.git_snapshot import git
from cora.independent_qualification import (
    CONTRACT, BASE, build_qualification, evaluate_study_packet,
    verify_contract, verify_qualification)
from cora.integrated_run import run_integrated, verify_integrated
from cora.integrated_html import render_integrated_html

ROOT = Path(__file__).resolve().parents[1]


def run_git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE, timeout=30).decode().strip()


def module_from_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    if spec is None or spec.loader is None:
        raise ValueError("tool module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IndependentQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").is_dir():
            raise unittest.SkipTest("requires exact original Git checkout")
        cls.sha = run_git(ROOT, "rev-parse", "HEAD")
        cls.contract = json.loads((ROOT / CONTRACT).read_text("utf-8"))
        cls.report = build_qualification(ROOT, cls.sha)

    def test_01_29_node_reticulum_and_all_external_gates_blocked(self):
        self.assertTrue(verify_contract(self.contract))
        self.assertEqual(len(self.contract["nodes"]), 29)
        r = self.report
        self.assertEqual(r["contract_schema"], "cora-independent-qualification-dod/1")
        self.assertEqual(r["commit"], self.sha)
        self.assertEqual(r["gate_count"], 4)
        self.assertEqual(r["external_gates_unclosed"], 4)
        self.assertEqual(r["authorization"], "NONE")
        self.assertFalse(r["release_authorized"])
        self.assertEqual(r["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(r["independent_target_count"], 0)
        self.assertEqual(r["human_usability_participants_observed"], 0)
        self.assertEqual({x["family"] for x in r["gates"]},
                         {"BEHAVIOR", "USABILITY", "ISOLATION", "GOVERNANCE"})
        for row in r["gates"]:
            self.assertFalse(row["missing_source_paths"])
            self.assertEqual(row["state"], "BLOCKED_EXTERNAL")
            self.assertEqual(row["independent_evidence"], "NOT_OBSERVED")
        self.assertTrue(verify_qualification(ROOT, r))

    def test_02_one_run_atlas_and_exact_git_replay_do_not_promote(self):
        bundle = run_integrated(ROOT, self.sha, process="source", max_commits=4)
        self.assertEqual(bundle["qualification"], self.report)
        page = render_integrated_html(bundle)
        self.assertIn('id="qualification"', page)
        self.assertIn("Independent qualification", page)
        for family in ("BEHAVIOR", "USABILITY", "ISOLATION", "GOVERNANCE"):
            self.assertIn(family, page)
        self.assertTrue(verify_integrated(ROOT, bundle, html_page=page))
        self.assertEqual(bundle["product_status"], "BLOCKED_EXTERNAL")
        tampered = copy.deepcopy(bundle)
        tampered["qualification"]["gates"][0]["state"] = "PASS"
        tampered["receipt_digest"] = domain_hash(
            "CORA:integrated-one-run:2",
            {k: v for k,v in tampered.items() if k != "receipt_digest"})
        with self.assertRaisesRegex(ValueError, "qualification"):
            verify_integrated(ROOT, tampered)

    def test_03_reject_proof_promotion_even_after_receipt_rehash(self):
        for change in (
            lambda x: x.update(product_status="PASS"),
            lambda x: x.update(authorization="RELEASE_APPROVED"),
            lambda x: x.update(release_authorized=True),
            lambda x: x.update(external_gates_unclosed=0),
            lambda x: x["gates"][0].update(state="PASS"),
            lambda x: x["gates"][1].update(independent_evidence="CERTIFIED"),
            lambda x: x.update(host_required_checks="VERIFIED"),
            lambda x: x.update(runtime_host_attestation="VERIFIED"),
        ):
            mutated=copy.deepcopy(self.report)
            change(mutated)
            unsigned={k:v for k,v in mutated.items() if k!="receipt_digest"}
            mutated["receipt_digest"]=domain_hash("CORA:independent-qualification:1",unsigned)
            with self.subTest(change=change.__code__.co_firstlineno):
                with self.assertRaises(ValueError):
                    verify_qualification(ROOT,mutated)

    def test_04_ten_thousand_seeded_contract_falsifiers(self):
        rng=random.Random(883)
        families=(
            "REMOVE_NODE", "DUPLICATE_ID", "REMOVE_EDGE", "PROMOTE_EXTERNAL",
            "PROMOTE_STATE", "FORGE_AUTHORITY", "WRONG_BASE", "WRONG_GLOBAL",
            "LOWER_REAL_TARGETS", "LOWER_STUDY_COUNT", "LIFT_HOST_ATTESTATION",
            "LIFT_HOST_AUTHORITY")
        accepted=0
        for i in range(10000):
            doc=copy.deepcopy(self.contract)
            kind=families[i%len(families)]
            if kind=="REMOVE_NODE":
                doc["nodes"].pop(rng.randrange(len(doc["nodes"])))
            elif kind=="DUPLICATE_ID":
                doc["nodes"][rng.randrange(1,4)]["id"]="S_B1_INDEPENDENT_GIT_ORACLE"
            elif kind=="REMOVE_EDGE":
                next(x for x in doc["nodes"] if x["id"]=="G_BEHAVIOR")["depends_on"].pop()
            elif kind=="PROMOTE_EXTERNAL":
                next(x for x in doc["nodes"] if x["id"]=="E_I1_HOST_POLICY_ATTESTATION")["scope"]="SOURCE"
            elif kind=="PROMOTE_STATE":
                next(x for x in doc["nodes"] if x["id"]=="G_PRODUCT_INDEPENDENT_QUALIFICATION")["state"]="PASS"
            elif kind=="FORGE_AUTHORITY":
                doc["authority"]="APPROVED"
            elif kind=="WRONG_BASE":
                doc["source_baseline"]="0"*40
            elif kind=="WRONG_GLOBAL":
                doc["global_goal"]="G_BEHAVIOR"
            elif kind=="LOWER_REAL_TARGETS":
                doc["requirements"]["BEHAVIOR"]["minimum_real_targets"]=1
            elif kind=="LOWER_STUDY_COUNT":
                doc["requirements"]["USABILITY"]["minimum_participants"]=7
            elif kind=="LIFT_HOST_ATTESTATION":
                doc["requirements"]["ISOLATION"]["host_attestation"]=False
            elif kind=="LIFT_HOST_AUTHORITY":
                doc["requirements"]["GOVERNANCE"]["host_authority_verified"]=False
            try:
                verify_contract(doc)
            except ValueError:
                pass
            else:
                accepted+=1
        self.assertEqual(accepted,0)
        self.assertEqual(len(families),12)

    def test_05_native_git_is_implementation_independent_and_catches_faults(self):
        # The oracle intentionally imports neither cora.git_snapshot nor
        # cora.evidence; subprocess comparison invokes installed CORA CLI.
        native=module_from_tool("independent_git_oracle")
        campaign=native.run_reference_campaign()
        self.assertEqual(campaign["fixture_count"],2)
        self.assertEqual(campaign["product_status"],"BLOCKED_EXTERNAL")
        self.assertEqual(campaign["independent_owners"],"NOT_ATTESTED")
        self.assertTrue(all(x["status"]=="MATCHED_NATIVE_GIT_REFERENCE_SCOPED"
                            for x in campaign["fixtures"]))
        self.assertTrue(campaign["fixtures"][0]["previous_sha_still_replayable"])
        expected={"commit":"1"*40,"records":{"file.txt":{
            "mode":"100644","git_oid":"2"*40,"status":"observed_git_blob",
            "size":2,"sha256":"a"*64}}}
        altered=copy.deepcopy(expected)
        altered["records"]["file.txt"]["sha256"]="b"*64
        with self.assertRaisesRegex(ValueError,"reference disagreement"):
            native.compare_expected(expected,altered)
        altered=copy.deepcopy(expected)
        altered["records"].clear()
        with self.assertRaisesRegex(ValueError,"reference disagreement"):
            native.compare_expected(expected,altered)

    def test_06_usability_threshold_is_only_numerical_and_non_authorizing(self):
        users=[]
        for i in range(8):
            users.append({
                "participant_id": f"person_{i:02d}",
                "persona": ("first_time_developer" if i<4 else
                            "independent_assurance_reviewer"),
                "repo_id": "repo_A" if i%2 else "repo_B",
                "minutes": 13+i%3,
                "tasks": [{"task_id":f"task_{j}","completed":True,
                           "proof_misclassified":False} for j in range(3)],
            })
        packet={"schema":"cora-usability-pilot/1",
                "subject_commit":self.sha,"participants":users}
        observed=evaluate_study_packet(packet,self.sha)
        self.assertEqual(observed["numerical_threshold"],"MET_IN_SUPPLIED_DATA")
        self.assertEqual(observed["identity_observation"],"UNAUTHENTICATED_SUBMITTED_DATA")
        self.assertFalse(observed["independent_usability_accepted"])
        self.assertEqual(observed["product_status"],"BLOCKED_EXTERNAL")
        changes=(
            lambda x: x["participants"].pop(),
            lambda x: x["participants"][0]["tasks"][0].update(proof_misclassified=True),
            lambda x: x["participants"][0].update(minutes=25),
            lambda x: [r.update(repo_id="one") for r in x["participants"]],
            lambda x: [r.update(persona="first_time_developer") for r in x["participants"]],
        )
        for change in changes:
            other=copy.deepcopy(packet)
            change(other)
            out=evaluate_study_packet(other,self.sha)
            self.assertEqual(out["numerical_threshold"],"NOT_MET")
            self.assertFalse(out["independent_usability_accepted"])
        forged=copy.deepcopy(packet)
        forged["participants"][0]["participant_id"]=forged["participants"][1]["participant_id"]
        with self.assertRaisesRegex(ValueError,"participant"):
            evaluate_study_packet(forged,self.sha)
        with self.assertRaisesRegex(ValueError,"commit"):
            evaluate_study_packet(packet,"0"*40)

    def test_07_readonly_github_host_probe_denies_403_and_unverified_success(self):
        host=module_from_tool("governance_readback")
        self.assertEqual(host.probe("Luke883i/cora","main")["observation"],
                         "BLOCKED_NO_HOST_TOKEN")
        forbidden=urllib.error.HTTPError("https://api.github.com",403,
                                         "Forbidden",{},None)
        with patch.object(host.urllib.request,"urlopen",side_effect=forbidden):
            result=host.probe("Luke883i/cora","main",token="private")
        self.assertEqual(result["http_status"],403)
        self.assertEqual(result["observation"],"BLOCKED_NO_HOST_PERMISSION")
        self.assertFalse(result["merge_authorized"])
        class FakeResponse:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):
                return json.dumps({"required_status_checks":{"checks":[
                    {"context":"CI-exact-head"}]},"required_pull_request_reviews":{
                    "required_approving_review_count":2}}).encode("utf-8")
        with patch.object(host.urllib.request,"urlopen",return_value=FakeResponse()):
            result=host.probe("Luke883i/cora","main",token="private")
        self.assertEqual(result["required_reviews_reported"],2)
        self.assertEqual(result["observation"],
                         "HOST_CONFIGURATION_REPORTED_NOT_INDEPENDENTLY_ATTESTED")
        self.assertFalse(result["host_enforcement_attested"])
        self.assertFalse(result["merge_authorized"])
        with self.assertRaisesRegex(ValueError,"identity"):
            host.probe("some/../other","main","private")

    def test_08_physical_git_external_state_mutant_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            local=Path(temp)/"clone"
            subprocess.run(["git","clone","-q","--local",str(ROOT),str(local)],
                           check=True,timeout=60)
            run_git(local,"checkout","-q",self.sha)
            run_git(local,"config","user.name","PR39 Git falsifier")
            run_git(local,"config","user.email","oracle@example.invalid")
            path=local/CONTRACT
            doc=json.loads(path.read_text("utf-8"))
            next(x for x in doc["nodes"] if x["id"]=="E_G1_VERIFIED_REQUIRED_CHECKS")["state"]="PASS"
            path.write_text(json.dumps(doc),encoding="utf-8")
            run_git(local,"add",CONTRACT)
            run_git(local,"commit","-qm","forged Git host authorization")
            with self.assertRaisesRegex(ValueError,"external qualification witness"):
                build_qualification(local,run_git(local,"rev-parse","HEAD"))


if __name__=="__main__":
    unittest.main()
