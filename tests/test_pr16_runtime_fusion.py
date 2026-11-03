"""G1/G2: opt-in Docker config and cross-source fusion cannot self-attest safety."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from cora.archive_intake import inspect_zip
from cora.runtime_observation import observe_runtime, verify_runtime_receipt
from cora.observation_fusion import fuse_evidence, verify_fusion
from cora.evidence import domain_hash
from cora.cli import main

IMAGE='python:3.13.5-slim@sha256:'+'a'*64

class RuntimeFusionFalsification(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.archive=self.root/'source.zip'
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('pkg/src/lib.py','def hello(): return True\n')
            z.writestr('pkg/tests/test_ok.py','import unittest\nclass Smoke(unittest.TestCase):\n def test_truth(self): self.assertTrue(True)\n')
        self.workspace=self.root/'work'
        self.intake=inspect_zip(self.archive,extract_to=self.workspace)
    def tearDown(self):self.tmp.cleanup()

    def test_untrusted_zip_never_autoexecutes(self):
        with patch('cora.runtime_observation.subprocess.run',side_effect=AssertionError('executed without opt-in')):
            report=observe_runtime(self.archive,self.workspace,image=IMAGE)
        self.assertEqual(report['execution_status'],'NOT_REQUESTED')
        self.assertEqual(report['authorization'],'NONE')
        self.assertTrue(verify_runtime_receipt(report))

    def test_docker_unavailable_fails_closed(self):
        with patch('cora.runtime_observation.shutil.which',return_value=None):
            result=observe_runtime(self.archive,self.workspace,execute=True,image=IMAGE)
        self.assertEqual(result['execution_status'],'BLOCKED_EXECUTOR_UNAVAILABLE')

    def test_missing_image_blocks(self):
        result=observe_runtime(self.archive,self.workspace,execute=True)
        self.assertEqual(result['execution_status'],'BLOCKED_NO_PINNED_IMAGE')

    def test_unpinned_image_rejected(self):
        with self.assertRaises(ValueError):
            observe_runtime(self.archive,self.workspace,execute=True,image='python:latest')

    def test_modified_workspace_rejected(self):
        (self.workspace/'src/lib.py').write_text('malicious\n')
        with self.assertRaises(ValueError):
            observe_runtime(self.archive,self.workspace,execute=False)

    def test_symlink_workspace_rejected(self):
        (self.workspace/'src/lib.py').unlink()
        (self.workspace/'src/lib.py').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            observe_runtime(self.archive,self.workspace)

    def test_docker_command_flags_and_unattested_result(self):
        calls=[]
        def fake(command,**kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command,0)
        with patch('cora.runtime_observation.shutil.which',return_value='/usr/bin/docker'), \
             patch('cora.runtime_observation.os.getuid',return_value=1001), \
             patch('cora.runtime_observation.os.getgid',return_value=1001), \
             patch('cora.runtime_observation.subprocess.run',side_effect=fake):
            r=observe_runtime(self.archive,self.workspace,execute=True,image=IMAGE)
        self.assertEqual(r['execution_status'],'RUN_REPORTED_UNATTESTED')
        self.assertEqual(r['sandbox_assurance'],'NOT_INDEPENDENTLY_ATTESTED')
        self.assertEqual(r['exit_code'],0)
        cmd=calls[0]
        # The executed mount must use the independently reconstructed private
        # archive content, never the mutable caller workspace (TOCTOU guard).
        mounts=[x for x in cmd if isinstance(x,str) and x.startswith('type=bind,src=')]
        self.assertEqual(len(mounts),1)
        self.assertNotIn('src='+str(self.workspace)+',',mounts[0])
        self.assertIn('cora-runtime-',mounts[0])
        for x in ('--network','none','--read-only','--cap-drop','ALL','--pids-limit','--memory','--cpus','--pull','never','--user'):
            self.assertIn(x,cmd)
        self.assertEqual(cmd[-6:],['python','-m','unittest','discover','-s','tests','-q'][-6:])
        self.assertNotIn('sh',cmd)
        self.assertEqual(r['authorization'],'NONE')
        self.assertTrue(verify_runtime_receipt(r))

    def test_runtime_mounts_private_staged_archive_not_caller_workspace(self):
        observed=[]
        def fake(command,**kwargs):
            observed.append(command)
            self.assertIn('--mount',command)
            mounted=command[command.index('--mount')+1]
            self.assertIn('dst=/work,readonly',mounted)
            self.assertNotIn('src='+str(self.workspace)+',',mounted)
            self.assertTrue(kwargs.get('preexec_fn'))
            return subprocess.CompletedProcess(command,0)
        with patch('cora.runtime_observation.shutil.which',return_value='/usr/bin/docker'), \\
             patch('cora.runtime_observation.os.getuid',return_value=1001), \\
             patch('cora.runtime_observation.os.getgid',return_value=1001), \\
             patch('cora.runtime_observation.subprocess.run',side_effect=fake):
            receipt=observe_runtime(self.archive,self.workspace,execute=True,image=IMAGE)
        self.assertEqual(receipt['execution_status'],'RUN_REPORTED_UNATTESTED')
        self.assertEqual(len(observed),1)

    def test_cross_archive_fusion_rejected_even_with_new_digest(self):
        r=observe_runtime(self.archive,self.workspace)
        forged={**r,'archive_sha256':'0'*64}
        forged['receipt_digest']=domain_hash('CORA:runtime-observation:1',
             {k:v for k,v in forged.items() if k!='receipt_digest'})
        with self.assertRaises(ValueError):fuse_evidence(self.intake,forged)

    def test_fusion_is_only_observational_and_replayable(self):
        runtime=observe_runtime(self.archive,self.workspace)
        synthetic={'schema':'cora-process-run/1','commit':'1'*40,'authorized_action':'NONE',
                   'status':'PASS_SCOPED_WITH_UNVERIFIED_GAPS','process':'full'}
        synthetic['run_digest']=domain_hash('CORA:process-run:1',synthetic)
        fusion=fuse_evidence(self.intake,runtime,synthetic)
        self.assertFalse(fusion['release_authorized'])
        self.assertEqual(fusion['authorization'],'NONE')
        self.assertEqual(fusion['source_git_history'],'UNAVAILABLE_FROM_ZIP')
        self.assertEqual(fusion['source_process_provenance'],'INDEPENDENT_GIT_ANCESTRY_NOT_ATTESTED')
        self.assertTrue(verify_fusion(self.intake,fusion,runtime,synthetic))
        fusion['runtime_coverage']='ATTESTED'
        with self.assertRaises(ValueError):verify_fusion(self.intake,fusion,runtime,synthetic)

    def test_cli_roundtrip(self):
        intake_path=self.root/'intake.json'
        fusion_path=self.root/'fusion.json'
        self.assertEqual(main(['zip-intake',str(self.archive),'--output',str(intake_path)]),0)
        self.assertEqual(main(['verify-zip-intake',str(intake_path),'--archive',str(self.archive)]),0)
        self.assertEqual(main(['fuse-evidence',str(intake_path),'--output',str(fusion_path)]),0)
        self.assertEqual(main(['verify-fusion',str(fusion_path),'--zip-report',str(intake_path)]),0)
        self.assertEqual(main(['runtime-observe',str(self.archive),'--workspace',str(self.workspace),
                               '--execute','--image','python:latest']),3)

if __name__=='__main__':unittest.main()
