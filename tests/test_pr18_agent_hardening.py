"""PR18 adversarial historiography: prove PR17 scenario coverage wasn't index-based.

Physical source mutants operate on isolated temporary COPIES of CORA's own Python
finite-model module; never execute untrusted target repository code.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cora.agent_saturation as saturation
from cora.agent_assurance import LOCAL_IDS, assess_claims, load_contract, verify_assessment

ROOT = Path(__file__).resolve().parents[1]


class AgentHistoricalHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract(ROOT / "cora.agent-dod.json")

    @staticmethod
    def claims():
        sha = "b" * 40
        return {"schema": "cora-agent-claims/1", "head_sha": sha, "locals": {
            n: {"status": "CLAIMED_PASS", "revision": sha, "witness": "source-unverified-claim"}
            for n in LOCAL_IDS}}

    def test_historical_index_based_saturation_false_positive_is_killed(self):
        """The original PR17 counter only counted positions, not masks."""
        with patch("cora.agent_saturation._scenario", return_value=0):
            result = saturation.saturate_agent_dod(self.contract, sessions=1, cases_per_session=1000)
        self.assertEqual(result["status"], "REFUTED")
        self.assertLess(result["sessions_receipts"][0]["observed_single_faults"], 24)
        self.assertLess(result["sessions_receipts"][0]["observed_all_pairs"], 276)
        self.assertGreater(result["sessions_receipts"][0]["preregistered_sequence_mismatches"], 0)

    def test_tail_collapse_cannot_fake_saturation(self):
        real = saturation._scenario

        def collapsed(i, seed):
            return real(i, seed) if i <= 306 else 0
        with patch("cora.agent_saturation._scenario", side_effect=collapsed):
            result = saturation.saturate_agent_dod(self.contract, sessions=1, cases_per_session=1100)
        self.assertEqual(result["status"], "REFUTED")
        self.assertFalse(result["sessions_receipts"][0]["scenario_diversity_validated"])

    def test_external_claims_cannot_self_attest_or_become_action(self):
        claims = self.claims()
        governed = assess_claims(self.contract, claims, goal="G_GOVERNED_AGENT")
        self.assertEqual(governed["goal_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(governed["states"]["L19"], "BLOCKED_EXTERNAL")
        self.assertEqual(governed["states"]["L24"], "BLOCKED_EXTERNAL")
        self.assertEqual(governed["next_unresolved_falsifier"]["id"], "L19")
        self.assertEqual(governed["authorization"], "NONE")
        self.assertFalse(governed["release_authorized"])

    def test_first_actionable_falsifier_follows_observed_blocker(self):
        claims = self.claims()
        claims["locals"]["L05"]["status"] = "BLOCKED"
        claims["locals"]["L09"]["status"] = "REFUTED"
        result = assess_claims(self.contract, claims)
        self.assertEqual(result["goal_status"], "REFUTED")
        self.assertEqual(result["next_unresolved_falsifier"]["id"], "L05")
        self.assertEqual(result["next_unresolved_falsifier"]["scope"], "SOURCE")
        self.assertTrue(verify_assessment(self.contract, claims, result))
        forged = copy.deepcopy(result)
        forged["next_unresolved_falsifier"]["id"] = "L20"
        with self.assertRaises(ValueError):
            verify_assessment(self.contract, claims, forged)

    def test_blank_witness_not_considered_evidence(self):
        claims = self.claims()
        claims["locals"]["L03"]["witness"] = "          "
        result = assess_claims(self.contract, claims)
        self.assertEqual(result["states"]["L03"], "BLOCKED_WRONG_OR_MISSING_WITNESS")
        self.assertEqual(result["next_unresolved_falsifier"]["id"], "L03")

    def test_six_physical_cora_source_mutants_are_killed(self):
        """6 source-code text mutations written to .py in temporary checkout.

        These are actual changed Python module bytes, but only CORA's finite
        model is exercised. They are not target product/runtime mutations.
        """
        original = Path(saturation.__file__).read_text(encoding="utf-8")
        mutants = [
            ('governed_escalation', 'return source, "BLOCKED_EXTERNAL"', 'return source, "AUTHORIZED"'),
            ('source_false_pass', 'source = MODEL_LABEL if (local_ok and intermediate_ok and global_ok) else BLOCKED_LABEL',
             'source = MODEL_LABEL if True else BLOCKED_LABEL'),
            ('oracle_false_positive', 'candidate_source = (mask % (1 << 18)) == 0', 'candidate_source = True'),
            ('erase_single_faults', 'return 1 << i', 'return 0'),
            ('erase_fault_pairs', 'return (1 << a) | (1 << b)', 'return 0'),
            ('erase_external_cases', 'return 1 << (18 + i - 301)', 'return 0'),
        ]
        with tempfile.TemporaryDirectory() as td:
            for name, before, after in mutants:
                self.assertEqual(original.count(before), 1, name)
                file = Path(td) / (name + ".py")
                file.write_text(original.replace(before, after, 1), encoding="utf-8")
                context = {"__name__": "cora.pr18_mutant_" + name, "__package__": "cora"}
                with self.subTest(mutant=name):
                    exec(compile(file.read_text("utf-8"), str(file), "exec"), context)
                    result = context["saturate_agent_dod"](self.contract, sessions=1, cases_per_session=1000)
                    self.assertEqual(result["status"], "REFUTED", name)
                    self.assertGreater(result["model_mismatches"] + result["unsafe_promotions"], 0, name)

    def test_corrected_scenarios_and_reproducible_receipt(self):
        a = saturation.saturate_agent_dod(self.contract, sessions=1, cases_per_session=1200)
        b = saturation.saturate_agent_dod(self.contract, sessions=1, cases_per_session=1200)
        self.assertEqual(a, b)
        self.assertEqual(a["status"], "PARTIAL_NOT_10M")
        self.assertEqual(a["model_mismatches"], 0)
        self.assertEqual(a["unsafe_promotions"], 0)
        self.assertEqual(a["sessions_receipts"][0]["observed_single_faults"], 24)
        self.assertEqual(a["sessions_receipts"][0]["observed_all_pairs"], 276)
        self.assertTrue(a["sessions_receipts"][0]["scenario_diversity_validated"])


if __name__ == "__main__":
    unittest.main()
