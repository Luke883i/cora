"""Counterexamples against the independent oracle and CORA receipt admission."""
import copy
import unittest

from cora_f5_gate import evaluate, MODEL, BLOCKED, PASS, PIN, PAIRS
from run_f5 import generate_oracle

class F5Admission(unittest.TestCase):
    def valid(self):
        return {"target": "Cysharp/MemoryPack", "target_sha": PIN, "status": PASS,
                "native_processes": 12, "cross_pairs": 9, "pairs": PAIRS[:],
                "supported_runtime_majors": [8, 9, 10], "verified_wire_files": 60,
                "oracle_sha256": "a" * 64,
                "negative_controls": {"bit_flip": "KILLED_NATIVE", "missing_file": "KILLED_NATIVE"}}

    def test_python_oracle_distinguishes_native_layouts(self):
        data = generate_oracle()
        self.assertEqual(len(data["cases"]), 10)
        self.assertNotEqual(data["cases"][0]["net10Hex"], data["cases"][0]["net9Hex"])
        self.assertEqual(data["cases"][0]["net10Hex"], "D4FEFFFF000000000092B5AF2B4FDF08")

    def test_complete_scoped_acceptance_with_global_hold(self):
        assessment = evaluate(self.valid())
        self.assertEqual(assessment["scoped"]["status"], MODEL)
        self.assertNotEqual(assessment["release"]["status"], MODEL)

    def test_missing_runtime_pair_rejected(self):
        r = self.valid()
        r["pairs"].pop()
        self.assertEqual(evaluate(r)["scoped"]["status"], BLOCKED)

    def test_missing_oracle_and_native_proofs_rejected(self):
        for key, value in (("verified_wire_files", 59), ("oracle_sha256", "bad"),
                           ("native_processes", 11), ("target_sha", "0" * 40),
                           ("status", "HOLD")):
            r=self.valid(); r[key]=value
            with self.subTest(key=key):
                self.assertEqual(evaluate(r)["scoped"]["status"], BLOCKED)

    def test_synthetic_negative_failure_without_evidence_rejected(self):
        r=self.valid()
        r["negative_controls"]["bit_flip"]="NOT_RUN"
        self.assertEqual(evaluate(r)["scoped"]["status"], BLOCKED)

    def test_out_of_scope_must_not_be_elevated(self):
        r=self.valid()
        r["maintainer_approved"]=True
        self.assertNotEqual(evaluate(r)["release"]["status"], MODEL)

if __name__=="__main__":
    unittest.main()
