"""Benchmark and critical coverage gates reject forged performance and missing witnesses."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tools.benchmark_pr16_git_batch import benchmark
from tools.verify_pr16_coverage import verify, CRITICAL

class BenchmarkContracts(unittest.TestCase):
    def test_independent_synthetic_oracle(self):
        report=benchmark(50)
        self.assertEqual(report['status'],'PASS_SCOPED')
        self.assertEqual(report['fixture_files'],50)
        self.assertLessEqual(report['batch_git_subprocesses'],5)
        self.assertGreater(report['oracle_object_reads'],report['batch_git_subprocesses']*5)

    def test_coverage_requires_critical_witnesses(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'coverage.json'
            path.write_text(json.dumps({'totals':{'percent_covered':95},
                                        'files':{}}),encoding='utf-8')
            report=verify(path)
            self.assertEqual(report['status'],'REFUTED')
            self.assertEqual(len(report['missing']),len(CRITICAL))

    def test_coverage_floor_refutes_low_critical(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'coverage.json'
            files={k:{'summary':{'percent_covered':91}} for k in CRITICAL}
            files[CRITICAL[0]]={'summary':{'percent_covered':65}}
            path.write_text(json.dumps({'totals':{'percent_covered':92},
                                         'files':files}),encoding='utf-8')
            report=verify(path)
            self.assertEqual(report['status'],'REFUTED')
            self.assertEqual(report['below_floor'][0]['path'],CRITICAL[0])

if __name__=='__main__':unittest.main()
