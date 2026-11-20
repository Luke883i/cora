"""Adversarial semantic obligation tests: no report promotes its own provenance."""
from __future__ import annotations
import tempfile
import unittest
import zipfile
from pathlib import Path

from cora.archive_intake import inspect_zip
from cora.runtime_observation import observe_runtime, verify_runtime_receipt
from cora.semantic_lattice import lattice_from_evidence, verify_lattice
from cora.evidence import domain_hash
from cora.cli import main


class LatticeFalsification(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.archive=self.root/'source.zip'
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('source/code.py', 'pass\n')
        self.zip=inspect_zip(self.archive)
    def tearDown(self):self.tmp.cleanup()

    def test_source_only_does_not_require_or_invent_execution(self):
        report=lattice_from_evidence(self.archive,self.zip)
        self.assertEqual([n['id'] for n in report['nodes']],['G0','G1','G2','G3'])
        self.assertEqual(report['nodes'][0]['status'],'SOURCE_REPLAY_SCOPED')
        self.assertEqual(report['nodes'][1]['status'],'NOT_OBSERVED')
        self.assertEqual(report['nodes'][3]['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(report['source_DoD'],'PENDING_INDEPENDENT_HEAD_CI')
        self.assertFalse(report['release_authorized'])
        self.assertTrue(verify_lattice(self.archive,report,zip_report=self.zip))

    def test_replay_rejects_edited_source_and_promoted_authority(self):
        report=lattice_from_evidence(self.archive,self.zip)
        report['governed_DoD']='PASS'
        with self.assertRaises(ValueError):verify_lattice(self.archive,report,zip_report=self.zip)
        original=lattice_from_evidence(self.archive,self.zip)
        with zipfile.ZipFile(self.archive,'w') as z:z.writestr('source/code.py','changed\n')
        with self.assertRaises(ValueError):verify_lattice(self.archive,original,zip_report=self.zip)

    def test_workspace_witness_is_required_when_extracted(self):
        work=self.root/'work'
        receipt=inspect_zip(self.archive,extract_to=work)
        with self.assertRaises(ValueError):lattice_from_evidence(self.archive,receipt)
        report=lattice_from_evidence(self.archive,receipt,workspace=work)
        self.assertTrue(verify_lattice(self.archive,report,zip_report=receipt,workspace=work))

    def test_untrusted_runtime_report_cannot_forge_completed_test(self):
        work=self.root/'work'
        inspect_zip(self.archive,extract_to=work)
        runtime=observe_runtime(self.archive,work)
        for key,val in [('execution_status','RUN_REPORTED_UNATTESTED'),
                        ('runtime_coverage','ATTESTED')]:
            forged={**runtime,key:val}
            forged['receipt_digest']=domain_hash('CORA:runtime-observation:1',
                {k:v for k,v in forged.items() if k!='receipt_digest'})
            with self.assertRaises(ValueError):verify_runtime_receipt(forged)
            with self.assertRaises(ValueError):lattice_from_evidence(self.archive,self.zip,runtime_report=forged)

    def test_source_process_claim_cannot_be_promoted_to_git_ancestry(self):
        fixture={'schema':'cora-process-run/1','commit':'a'*40,'authorized_action':'NONE',
                 'status':'PASS_SCOPED_WITH_UNVERIFIED_GAPS','process':'full'}
        fixture['run_digest']=domain_hash('CORA:process-run:1',fixture)
        report=lattice_from_evidence(self.archive,self.zip,source_process=fixture)
        self.assertIn('SOURCE_PROCESS_GIT_LINKAGE',report['nodes'][2]['unknowns'])
        self.assertEqual(report['nodes'][3]['status'],'BLOCKED_EXTERNAL')

    def test_cli_lattice_roundtrip(self):
        a=self.root/'intake.json'; out=self.root/'lattice.json'
        self.assertEqual(main(['zip-intake',str(self.archive),'--output',str(a)]),0)
        self.assertEqual(main(['lattice-audit',str(self.archive),'--zip-report',str(a),
                               '--output',str(out)]),0)
        self.assertEqual(main(['verify-lattice',str(out),'--archive',str(self.archive),
                               '--zip-report',str(a)]),0)


if __name__=='__main__':unittest.main()
