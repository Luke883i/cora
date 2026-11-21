"""Falsification controls for fully-qualified xUnit TRX names and missing evidence."""
import copy
import unittest
from reticular_gate import evaluate, MODEL, BLOCKED, expected, NAMES, PIN

class ReticularContractTest(unittest.TestCase):
    def valid_receipt(self, qualified):
        prefix = 'MemoryPack.Tests.NativeVarIntByteContract.' if qualified else ''
        return {
            'pin': PIN,
            'source_original_sha256': 'bc41adf2ea96e6328f7277a9c7eb2de3c8b4f3e82ea12a7fe54142253ff4efe9',
            'status': 'PASS_SCOPED_NATIVE_NET8',
            'original': {'returncode': 1, 'tests': dict(zip((prefix + n for n in NAMES), ['Failed', 'Failed', 'Passed']))},
            'repaired': {'returncode': 0, 'tests': {prefix + n: 'Passed' for n in NAMES}},
            'full_suite': {'returncode': 0, 'tests': {'Existing.Smoke': 'Passed'}}}

    def test_bare_and_qualified_are_accepted(self):
        for qualified in (False, True):
            with self.subTest(qualified=qualified):
                report=evaluate(self.valid_receipt(qualified))
                self.assertEqual(report['native']['status'],MODEL)
                self.assertNotEqual(report['release']['status'],MODEL)

    def test_wrong_baseline_status_is_rejected(self):
        x=self.valid_receipt(True)
        x['original']['tests']['MemoryPack.Tests.NativeVarIntByteContract.'+NAMES[0]]='Passed'
        self.assertEqual(evaluate(x)['native']['status'],BLOCKED)

    def test_missing_after_result_rejected(self):
        x=self.valid_receipt(True)
        x['repaired']['tests'].pop('MemoryPack.Tests.NativeVarIntByteContract.'+NAMES[1])
        self.assertEqual(evaluate(x)['native']['status'],BLOCKED)

    def test_fake_outcome_or_renamed_test_rejected(self):
        x=self.valid_receipt(True)
        x['repaired']['tests']['MemoryPack.Tests.NativeVarIntByteContract.'+NAMES[0]]='Skipped'
        self.assertEqual(evaluate(x)['native']['status'],BLOCKED)
        x=self.valid_receipt(True)
        x['original']['tests']['tampered.nonmatching']='Failed'
        self.assertEqual(evaluate(x)['native']['status'],BLOCKED)

    def test_wrong_source_or_missing_full_suite_rejected(self):
        for field in ('pin','source_original_sha256'):
            x=self.valid_receipt(False);x[field]='0'*40
            self.assertEqual(evaluate(x)['native']['status'],BLOCKED)
        x=self.valid_receipt(False);x['full_suite']['tests']={}
        self.assertEqual(evaluate(x)['native']['status'],BLOCKED)

if __name__ == '__main__': unittest.main()
