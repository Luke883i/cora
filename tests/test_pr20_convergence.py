"""PR-20: independent Git fixtures, retrograde controls and bounded adversaries."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.agent_assurance import load_contract, backward_plan
from cora.gold_assurance import (
    load_gold_contract, retrograde_gold, load_convergence_contract, convergent_plan,
    SOURCE_LEAVES, EXTERNAL_LEAVES,
)
from cora.gold_saturation import saturate_convergence
from cora.reticulum import ordered_cut, assess_cut, invalidated_witnesses, MODEL
from cora.continuous import evaluate_contextual, verify_contextual_gate
from cora.cli import main

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "cora.convergence-dod.json"


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def fixture(where: Path, *, ambiguous: bool = False, ontology: bool = True,
            workflow: bool = False) -> tuple[Path, str, str]:
    where.mkdir(parents=True)
    git(where, "init", "-q")
    git(where, "config", "user.name", "Reticular Fixture")
    git(where, "config", "user.email", "fixture@example.invalid")
    (where / "src/pkg").mkdir(parents=True)
    (where / "src/pkg/__init__.py").write_text("", encoding="utf-8")
    (where / "src/pkg/a.py").write_text("def answer():\n    return 1\n", encoding="utf-8")
    (where / "src/pkg/b.py").write_text("import pkg.a\nx = pkg.a.answer()\n", encoding="utf-8")
    (where / ".cora").mkdir()
    policy = {
        "schema": "cora-continuous-policy/1", "version": 1,
        "max_changed_paths": 256, "high_risk_prefixes": [".github/workflows"],
        "high_risk_paths": ["src/pkg/a.py"],
        "required_human_roles": ["MAINTAINER", "INDEPENDENT_SECURITY_REVIEWER"],
        "review_processes": ["source", "architecture", "verification"],
    }
    (where / ".cora/continuous-policy.json").write_text(json.dumps(policy), encoding="utf-8")
    if ontology:
        products = [{"id": "demo", "roots": ["src/pkg"],
                     "entrypoints": ["src/pkg/b.py"]}]
        if ambiguous:
            products.append({"id": "demo-overlap", "roots": ["src/pkg"],
                             "entrypoints": ["src/pkg/b.py"]})
        ontology_data = {"schema": "cora-ontology/1",
                         "products": products,
                         "software": [{"id": "demo-engine", "roots": ["src/pkg"],
                                       "product_ids": ["demo"]}]}
        (where / "cora.ontology.json").write_text(
            json.dumps(ontology_data), encoding="utf-8")
    git(where, "add", ".")
    git(where, "commit", "-qm", "baseline with trusted continuous policy")
    base = git(where, "rev-parse", "HEAD")
    (where / "src/pkg/a.py").write_text("def answer():\n    return 2\n", encoding="utf-8")
    if workflow:
        (where / ".github/workflows").mkdir(parents=True)
        (where / ".github/workflows/writer.yml").write_text(
            "name: publish\npermissions:\n  contents: write\njobs:\n  publish:\n"
            "    runs-on: ubuntu-latest\n    steps:\n      - run: git push\n", encoding="utf-8")
    git(where, "add", ".")
    git(where, "commit", "-qm", "material behavior delta")
    return where, base, git(where, "rev-parse", "HEAD")


class ConvergenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_convergence_contract(CONTRACT)

    def test_one_canonical_kernel_preserves_both_legacy_profiles(self):
        a = load_contract(ROOT / "cora.agent-dod.json")
        g = load_gold_contract(ROOT / "cora.gold-assurance.json")
        self.assertEqual(len(backward_plan(a)["local_cut"]), 18)
        self.assertEqual(len(retrograde_gold(g)["local_cut"]), 12)
        self.assertEqual(len(backward_plan(a, goal="G_GOVERNED_AGENT")["local_cut"]), 24)
        self.assertEqual(len(retrograde_gold(g, "G_GOLD_GOVERNED")["local_cut"]), 16)
        self.assertEqual(ordered_cut(a["nodes"], "G_SOURCE_AGENT"),
                         backward_plan(a)["prerequisites_in_topological_order"])
        self.assertEqual(ordered_cut(g["nodes"], "G_GOLD_SOURCE"),
                         retrograde_gold(g)["nodes"])

    def test_complete_reticulum_noncompensatory_and_external(self):
        source = convergent_plan(self.profile, "G_SOURCE_CONVERGENCE")
        full = convergent_plan(self.profile, "G_R1_R4_COMPLETE")
        governed = convergent_plan(self.profile, "G_GOVERNED")
        self.assertEqual(len(source["source_locals"]), 10)
        self.assertEqual(len(source["external_locals"]), 0)
        self.assertEqual(len(full["external_locals"]), 9)
        self.assertEqual(len(governed["external_locals"]), 10)
        self.assertEqual(len(governed["prerequisites"]), 28)
        source_claims = {x: MODEL for x in SOURCE_LEAVES}
        full_claims = {x: MODEL for x in SOURCE_LEAVES + EXTERNAL_LEAVES
                       if x != "E_REVIEW"}
        s = assess_cut(self.profile["nodes"], "G_SOURCE_CONVERGENCE",
                       source_claims)
        f = assess_cut(self.profile["nodes"], "G_R1_R4_COMPLETE", full_claims)
        # Caller-supplied assertions outside the selected reverse cut must
        # not be silently accepted by a more permissive implementation.
        with self.assertRaises(ValueError):
            assess_cut(self.profile["nodes"], "G_R1_R4_COMPLETE",
                       {**full_claims, "E_REVIEW": MODEL})
        self.assertEqual(s["status"], "MODEL_ELIGIBLE_UNATTESTED")
        self.assertEqual(f["status"], "BLOCKED_EXTERNAL")
        self.assertEqual(f["states"]["E_R4_PRIVATE"], "BLOCKED_EXTERNAL")
        self.assertEqual(f["authorization"], "NONE")
        # A source counterexample must be preserved across EXTERNAL global
        # cuts; hiding REFUTED under a generic external debt loses the oracle.
        from cora.reticulum import REFUTED
        refuted = assess_cut(self.profile["nodes"], "G_R1_R4_COMPLETE",
                             {**full_claims, "S06": REFUTED})
        self.assertEqual(refuted["states"]["R2_PHYSICAL"], "REFUTED")
        self.assertEqual(refuted["status"], "REFUTED")
        self.assertEqual(refuted["states"]["E_R2_BEHAVIOR"], "BLOCKED_EXTERNAL")
        self.assertEqual(refuted["authorization"], "NONE")

    def test_mutated_policy_and_edges_are_not_reclassified_as_pass(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "policy.json"
            mutations = []
            for i in range(16):
                candidate = copy.deepcopy(self.profile)
                candidate["faults"][i]["kind"] += "-forged"
                mutations.append(candidate)
            for i in range(10):
                candidate = copy.deepcopy(self.profile)
                candidate["nodes"][i]["scope"] = "EXTERNAL"
                mutations.append(candidate)
            for op in (
                lambda x: x["nodes"][-1]["depends_on"].pop(),
                lambda x: x["nodes"][-2].update({"scope": "SOURCE"}),
                lambda x: x["goals"].update({"complete": "G_SOURCE_CONVERGENCE"}),
                lambda x: x["campaign"].update({"executed_target_mutants": 10_000_000}),
                lambda x: x["evidence"].update({"external": "SELF_AUTHORIZED"}),
            ):
                candidate = copy.deepcopy(self.profile)
                op(candidate)
                mutations.append(candidate)
            self.assertEqual(len(mutations), 31)
            for i, candidate in enumerate(mutations):
                file.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(mutant=i), self.assertRaises(ValueError):
                    load_convergence_contract(file)

    def test_cycle_dangling_and_duplicate_fail_closed(self):
        nodes = [{"id": "A", "depends_on": ["B"]},
                 {"id": "B", "depends_on": ["A"]}]
        with self.assertRaises(ValueError):
            ordered_cut(nodes, "A")
        nodes[1]["depends_on"] = ["C"]
        with self.assertRaises(ValueError):
            ordered_cut(nodes, "A")
        nodes[1]["id"] = "A"
        with self.assertRaises(ValueError):
            ordered_cut(nodes, "A")

    def test_precise_path_invalidation_is_not_proof_promotion(self):
        witnesses = [
            {"id": "A", "dependencies": ["src/pkg/a.py"],
             "revision": "a"*40, "scope": "SOURCE"},
            {"id": "B", "dependencies": ["src/pkg/b.py"],
             "revision": "a"*40, "scope": "SOURCE"},
            {"id": "C", "dependencies": ["docs/independent.md"],
             "revision": "a"*40, "scope": "SOURCE"},
            {"id": "EXTERNAL", "dependencies": ["docs/independent.md"],
             "revision": "a"*40, "scope": "EXTERNAL"},
        ]
        report = invalidated_witnesses(witnesses, ["src/pkg/a.py"], source_revision="b"*40)
        self.assertEqual([x["state"] for x in report["witnesses"]],
                         ["INVALIDATED_BY_CHANGED_SOURCE",
                          "NOT_INVALIDATED_REQUIRES_REVALIDATION",
                          "NOT_INVALIDATED_REQUIRES_REVALIDATION",
                          "BLOCKED_EXTERNAL"])
        self.assertEqual(report["authorization"], "NONE")
        forged = copy.deepcopy(witnesses)
        forged[0]["dependencies"] = ["../escape"]
        with self.assertRaises(ValueError):
            invalidated_witnesses(forged, ["src/pkg/a.py"], source_revision="b"*40)

    def test_contextual_git_graph_reverse_import_and_witness_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, head = fixture(Path(td) / "repo", workflow=True)
            manifests = [
                {"id": "A", "dependencies": ["src/pkg/a.py"],
                 "revision": base, "scope": "SOURCE"},
                {"id": "B", "dependencies": ["src/pkg/b.py"],
                 "revision": base, "scope": "SOURCE"},
                {"id": "C", "dependencies": ["docs/independent.md"],
                 "revision": base, "scope": "SOURCE"},
            ]
            r = evaluate_contextual(repo, base, head, contract=self.profile,
                                    witnesses=manifests)
            self.assertEqual(r["schema"], "cora-contextual-devops/1")
            self.assertEqual(r["continuous_gate"]["base_commit"], base)
            self.assertEqual(r["head_commit"], head)
            self.assertIn("src/pkg/b.py", r["candidate_affected_paths"])
            self.assertEqual(r["candidate_affected_paths"],
                             sorted(r["candidate_affected_paths"]))
            owned = next(x for x in r["owner_candidates"] if x["path"] == "src/pkg/a.py")
            self.assertEqual(owned["declared_products"], ["demo"])
            self.assertEqual([x["state"] for x in r["invalidation"]["witnesses"]],
                             ["INVALIDATED_BY_CHANGED_SOURCE",
                              "INVALIDATED_BY_CHANGED_SOURCE",
                              "NOT_INVALIDATED_REQUIRES_REVALIDATION"])
            self.assertTrue(r["workflow_effects"])
            self.assertIn("DECLARED_WRITE_CAPABILITY",
                          r["workflow_effects"][0]["potential_effects"])
            self.assertEqual(r["workflow_effects"][0]["actual_effect"], "NOT_OBSERVED")
            self.assertEqual(r["canonical_lattice"]["complete_dod"], "BLOCKED_EXTERNAL")
            self.assertEqual(r["mutations"], "NOT_EXECUTED")
            self.assertTrue(verify_contextual_gate(repo, r, contract=self.profile,
                                                  witnesses=manifests))
            forged = copy.deepcopy(r)
            forged["invalidation"]["witnesses"][2]["state"] = "PASS"
            with self.assertRaises(ValueError):
                verify_contextual_gate(repo, forged, contract=self.profile,
                                       witnesses=manifests)

    def test_deleted_module_recovers_prechange_consumers(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, head = fixture(Path(td) / "delete-source")
            git(repo, "rm", "src/pkg/a.py")
            git(repo, "commit", "-qm", "remove imported source module")
            removed_head = git(repo, "rev-parse", "HEAD")
            report = evaluate_contextual(repo, head, removed_head,
                                         contract=self.profile, witnesses=[
                {"id": "consumer", "dependencies": ["src/pkg/b.py"],
                 "revision": head, "scope": "SOURCE"},
                {"id": "independent", "dependencies": ["docs/nothing.md"],
                 "revision": head, "scope": "SOURCE"},
            ])
            self.assertTrue(report["base_candidate_graph_required"])
            self.assertIsNotNone(report["base_candidate_graph_source"])
            self.assertIn("src/pkg/a.py", report["changed_paths"])
            self.assertIn("src/pkg/b.py", report["candidate_affected_paths"])
            self.assertEqual(report["invalidation"]["witnesses"][0]["state"],
                             "INVALIDATED_BY_CHANGED_SOURCE")
            self.assertEqual(report["invalidation"]["witnesses"][1]["state"],
                             "NOT_INVALIDATED_REQUIRES_REVALIDATION")
            self.assertEqual(report["authorization"], "NONE")
            self.assertTrue(verify_contextual_gate(repo, report, contract=self.profile,
                                                  witnesses=[
                {"id": "consumer", "dependencies": ["src/pkg/b.py"],
                 "revision": head, "scope": "SOURCE"},
                {"id": "independent", "dependencies": ["docs/nothing.md"],
                 "revision": head, "scope": "SOURCE"},
            ]))

    def test_owner_collision_and_missing_ontology_never_pass(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, head = fixture(Path(td) / "overlap", ambiguous=True)
            r = evaluate_contextual(repo, base, head, contract=self.profile)
            self.assertEqual(r["next_action"], "QUALIFY_CONFLICTING_PRODUCT_OWNERS")
            self.assertIn("AMBIGUOUS_DECLARED_OWNER",
                          [x["owner_status"] for x in r["owner_candidates"]])
            absent, before, after = fixture(Path(td) / "unknown", ontology=False)
            rr = evaluate_contextual(absent, before, after, contract=self.profile)
            self.assertEqual(rr["status"], "DEBT_BLOCKED")
            self.assertEqual(rr["next_action"], "SUPPLY_COMMITTED_ONTOLOGY_AND_REPRODUCE_GRAPH")
            self.assertIsNone(rr["candidate_graph_source"])

    def test_lifecycle_pre_postmerge_and_legacy_are_not_reclassified(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, head = fixture(Path(td) / "repo")
            source = evaluate_contextual(repo, base, head, contract=self.profile)
            post = evaluate_contextual(repo, base, head, phase="postmerge",
                                       contract=self.profile)
            self.assertEqual(source["phase"], "premerge")
            self.assertEqual(post["phase"], "postmerge")
            self.assertEqual(source["continuous_gate"]["phase"], "premerge")
            self.assertEqual(post["continuous_gate"]["phase"], "postmerge")
            self.assertEqual(post["external_approval"], "BLOCKED_EXTERNAL")
            self.assertNotEqual(source["digest"], post["digest"])
            self.assertTrue(verify_contextual_gate(repo, post, contract=self.profile))

    def test_intent_validation_and_base_head_digest_is_stable(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base, head = fixture(Path(td) / "intent")
            intent = "Human requests a reversible behavior delta with a test oracle"
            first = evaluate_contextual(repo, base, head, contract=self.profile,
                                        intent=intent)
            second = evaluate_contextual(repo, base, head, contract=self.profile,
                                         intent=intent)
            self.assertEqual(first["intent_digest"], second["intent_digest"])
            self.assertEqual(first["intent_status"],
                             "CALLER_SUPPLIED_UNVERIFIED_BOUND_TO_BASE_HEAD")
            self.assertTrue(verify_contextual_gate(repo, first,
                                                   contract=self.profile, intent=intent))
            with self.assertRaises(ValueError):
                verify_contextual_gate(repo, first, contract=self.profile,
                                       intent="Different stated outcome, same source")
            with self.assertRaises(ValueError):
                evaluate_contextual(repo, base, head, contract=self.profile,
                                    intent="embedded" + chr(0) + "nul is illegal in intent")
            no_intent = evaluate_contextual(repo, base, head, contract=self.profile)
            self.assertEqual(no_intent["status"], "DEBT_BLOCKED")
            self.assertEqual(no_intent["intent_digest"], None)

    def test_preseeded_model_replay_and_falsified_generator(self):
        r = saturate_convergence(self.profile, sessions=1, cases_per_session=3000)
        self.assertEqual(r, saturate_convergence(self.profile, sessions=1, cases_per_session=3000))
        self.assertEqual(r["status"], "PARTIAL_NOT_10M")
        self.assertEqual(r["receipts"][0]["observed_singles"], 16)
        self.assertEqual(r["receipts"][0]["observed_pairs"], 120)
        self.assertEqual(r["receipts"][0]["normalized_signatures"], 2517)
        self.assertEqual(r["unsafe_promotions"], 0)
        self.assertEqual(r["source_mutants_executed"], 0)
        with patch("cora.gold_saturation.convergence_scenario", return_value=0):
            broken = saturate_convergence(self.profile, sessions=1, cases_per_session=3000)
        self.assertEqual(broken["status"], "REFUTED")
        with patch("cora.gold_saturation.convergence_model",
                   return_value=("MODEL_ELIGIBLE_UNATTESTED", "RELEASE_GO")):
            broken = saturate_convergence(self.profile, sessions=1, cases_per_session=3000)
        self.assertEqual(broken["status"], "REFUTED")

    def test_convergent_cli_with_replay_and_strict_nonpromotion(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.json"
            self.assertEqual(main(["convergence-plan", "--contract", str(CONTRACT),
                                   "--output", str(out)]), 0)
            plan = json.loads(out.read_text())
            self.assertEqual(len(plan["source_locals"]), 10)
            self.assertEqual(len(plan["external_locals"]), 9)
            self.assertEqual(main(["stress-convergence", "--contract", str(CONTRACT),
                                   "--sessions", "1", "--cases-per-session", "3000",
                                   "--require-full", "--output", str(out)]), 2)
            self.assertEqual(json.loads(out.read_text())["source_mutants_executed"], 0)
            repo, base, head = fixture(Path(td) / "repo")
            self.assertEqual(main(["dev-premerge", str(repo), "--base", base, "--head", head,
                                   "--contextual", "--convergence-contract", str(CONTRACT),
                                   "--output", str(out)]), 0)
            report = json.loads(out.read_text())
            self.assertEqual(report["authorization"], "NONE")
            self.assertEqual(report["intent_status"], "BLOCKED_MISSING_PER_CHANGE_INTENT")
            self.assertEqual(report["status"], "DEBT_BLOCKED")
            self.assertEqual(main(["verify-contextual-gate", str(out), "--repo", str(repo),
                                   "--convergence-contract", str(CONTRACT)]), 0)
            intent = "Deliver answer=2 preserving independently testable behavior"
            self.assertEqual(main(["dev-premerge", str(repo), "--base", base, "--head", head,
                                   "--contextual", "--intent", intent,
                                   "--convergence-contract", str(CONTRACT),
                                   "--output", str(out)]), 0)
            intent_report = json.loads(out.read_text())
            self.assertEqual(intent_report["intent_status"],
                             "CALLER_SUPPLIED_UNVERIFIED_BOUND_TO_BASE_HEAD")
            self.assertIsNotNone(intent_report["intent_digest"])
            self.assertEqual(main(["verify-contextual-gate", str(out), "--repo", str(repo),
                                   "--intent", intent, "--convergence-contract", str(CONTRACT)]), 0)
            self.assertEqual(main(["verify-contextual-gate", str(out), "--repo", str(repo),
                                   "--intent", "Contradictory spoofed intent",
                                   "--convergence-contract", str(CONTRACT)]), 3)
            self.assertEqual(main(["dev-postmerge", str(repo), "--previous", base, "--head", head,
                                   "--contextual", "--convergence-contract", str(CONTRACT),
                                   "--strict", "--output", str(out)]), 2)
            self.assertEqual(json.loads(out.read_text())["external_approval"], "BLOCKED_EXTERNAL")


if __name__ == "__main__":
    unittest.main()
