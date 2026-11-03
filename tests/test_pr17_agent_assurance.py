"""PR17: physical policy mutants, retrograde cuts, anti-promotion and finite oracle."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.agent_assurance import (LOCAL_IDS, FAMILIES, load_contract,
                                  backward_plan, assess_claims, verify_assessment)
from cora.agent_saturation import (_implementation, _reference_oracle,
                                   _scenario, saturate_agent_dod)
from cora.cli import main

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "cora.agent-dod.json"
HEAD = "a" * 40


class AgentAssuranceFalsification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract(POLICY)

    def test_backward_derivation_has_all_original_obligation_cuts(self):
        source = backward_plan(self.contract)
        governed = backward_plan(self.contract, goal="G_GOVERNED_AGENT")
        self.assertEqual(source["prerequisites_in_topological_order"][-1], "G_SOURCE_AGENT")
        self.assertEqual(len(source["local_cut"]), 18)
        self.assertEqual(governed["prerequisites_in_topological_order"][-1], "G_GOVERNED_AGENT")
        self.assertEqual(len(governed["local_cut"]), 24)
        self.assertEqual(len(governed["prerequisites_in_topological_order"]), 30)
        self.assertEqual(source["authorization"], "NONE")
        self.assertEqual(source, backward_plan(self.contract))

    def test_twenty_four_real_policy_file_mutants_killed(self):
        """Real temporary JSON file changes, NOT 24 source-code behavioral mutants."""
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td) / "cora.agent-dod.json"
            for idx in range(24):
                mutated = copy.deepcopy(self.contract)
                mutated["nodes"][idx]["family"] = "forged_" + FAMILIES[idx]
                temp.write_text(json.dumps(mutated), encoding="utf-8")
                with self.subTest(mutant=LOCAL_IDS[idx]):
                    with self.assertRaises(ValueError):
                        load_contract(temp)

    def test_structural_owner_and_authority_mutants_killed(self):
        mutations = (
            lambda m: m["nodes"].pop(),
            lambda m: m["nodes"][24]["depends_on"].pop(),
            lambda m: m["nodes"][29].update({"level": "SOURCE"}),
            lambda m: m["nodes"][0].update({"scope": "EXTERNAL"}),
            lambda m: m["nodes"][0].update({"id": "L02"}),
            lambda m: m["nodes"][0].update({"depends_on": ["G_GOVERNED_AGENT"]}),
            lambda m: m["authorities"].update({"governed": "AI_APPROVED"}),
            lambda m: m["goals"].update({"release": "G_SOURCE_AGENT"}),
            lambda m: m["seeds"].__setitem__(1, m["seeds"][0]),
            lambda m: m["mutation_budget"].update({"sessions": 1}),
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "candidate.json"
            for i, change in enumerate(mutations):
                mutated = copy.deepcopy(self.contract)
                change(mutated)
                path.write_text(json.dumps(mutated), encoding="utf-8")
                with self.subTest(mutant=i):
                    with self.assertRaises(ValueError):
                        load_contract(path)

    def _claims(self, all_locals=True):
        result = {"schema": "cora-agent-claims/1", "head_sha": HEAD, "locals": {}}
        if all_locals:
            for n in LOCAL_IDS:
                result["locals"][n] = {"status": "CLAIMED_PASS", "revision": HEAD,
                                       "witness": "self-reported-witness-not-attested"}
        return result

    def test_forged_all_pass_cannot_authorize_release(self):
        c = self._claims()
        source = assess_claims(self.contract, c)
        self.assertEqual(source["goal_status"], "MODEL_ELIGIBLE_UNATTESTED")
        self.assertTrue(verify_assessment(self.contract, c, source))
        governed = assess_claims(self.contract, c, goal="G_GOVERNED_AGENT")
        self.assertEqual(governed["goal_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(governed["states"]["I_EXTERNAL"], "BLOCKED_EXTERNAL")
        self.assertEqual(governed["authorization"], "NONE")
        self.assertFalse(governed["release_authorized"])
        source["authorization"] = "MERGE"
        with self.assertRaises(ValueError):
            verify_assessment(self.contract, c, source)

    def test_missing_unpinned_and_refuted_fail_closed(self):
        c = self._claims()
        c["locals"].pop("L03")
        self.assertEqual(assess_claims(self.contract,c)["goal_status"], "BLOCKED")
        c = self._claims()
        c["locals"]["L16"]["revision"] = "b" * 40
        self.assertEqual(assess_claims(self.contract,c)["goal_status"], "BLOCKED")
        c = self._claims()
        c["locals"]["L09"]["status"] = "REFUTED"
        self.assertEqual(assess_claims(self.contract,c)["goal_status"], "REFUTED")

    def test_replay_rejects_changed_claims_even_with_self_hash(self):
        c = self._claims()
        report = assess_claims(self.contract, c)
        c["locals"]["L12"]["witness"] = "tampered witness string"
        with self.assertRaises(ValueError):
            verify_assessment(self.contract, c, report)

    def test_seeded_campaign_replay_and_model_mutant_refutation(self):
        a = saturate_agent_dod(self.contract, sessions=1,cases_per_session=1000)
        b = saturate_agent_dod(self.contract, sessions=1,cases_per_session=1000)
        self.assertEqual(a,b)
        self.assertEqual(a["status"], "PARTIAL_NOT_10M")
        self.assertEqual(a["sessions_receipts"][0]["observed_all_pairs"],276)
        self.assertEqual(a["sessions_receipts"][0]["observed_single_faults"],24)
        self.assertEqual(a["unsafe_promotions"], 0)
        with patch("cora.agent_saturation._implementation",return_value=
                   ("MODEL_ELIGIBLE_UNATTESTED","GO")):
            corrupted = saturate_agent_dod(self.contract,sessions=1,cases_per_session=350)
        self.assertEqual(corrupted["status"], "REFUTED")
        self.assertGreater(corrupted["unsafe_promotions"],0)

    def test_independent_reference_known_cases(self):
        self.assertEqual(_reference_oracle(0),(True,False))
        self.assertEqual(_reference_oracle(1),(False,False))
        self.assertEqual(_reference_oracle(1 << 23),(True,False))
        for i in range(307):
            m = _scenario(i, self.contract["seeds"][0])
            implementation = _implementation(m)
            oracle = _reference_oracle(m)
            self.assertEqual(implementation[0] == "MODEL_ELIGIBLE_UNATTESTED",oracle[0])

    def test_cli_roundtrip_and_negative_exit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan=root / "plan.json"
            claims=root / "claims.json"
            report=root / "report.json"
            self.assertEqual(main(["dod-plan","--contract",str(POLICY),
                                    "--stage","premerge","--output",str(plan)]),0)
            self.assertEqual(json.loads(plan.read_text())["goal"],"G_SOURCE_AGENT")
            claims.write_text(json.dumps(self._claims()),encoding="utf-8")
            self.assertEqual(main(["dod-assess",str(claims),"--contract",str(POLICY),
                                    "--output",str(report)]),0)
            self.assertEqual(main(["verify-dod",str(report),"--observations",str(claims),
                                    "--contract",str(POLICY)]),0)
            self.assertEqual(main(["dod-assess",str(claims),"--contract",str(POLICY),
                                    "--stage","release"]),2)
            self.assertEqual(main(["stress-agent-dod","--contract",str(POLICY),
                                    "--sessions","1","--cases-per-session","400",
                                    "--require-full"]),2)


if __name__ == "__main__":
    unittest.main()
