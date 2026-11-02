"""PR-05 independent committed-Git fixtures and adverse evidence scenarios."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.closure import closure, verify_certificate, decide, make_certificate
from cora.closure_stress import stress_closure, scenario, FAMILIES
from cora.evidence import domain_hash
from cora.cli import main


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class ClosureGitFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.repo=Path(self.tmp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.name','Independent Fixture')
        git(self.repo,'config','user.email','fixture@invalid.example')
        for p in ('apps/alpha','apps/beta','src/shared'):(self.repo/p).mkdir(parents=True)
        (self.repo/'apps/alpha/main.py').write_text('import shared.util\n__import__("optional_module")\n')
        (self.repo/'apps/beta/task.py').write_text('import shared.util\n')
        (self.repo/'src/shared/util.py').write_text('VERSION=1\n')
        (self.repo/'apps/alpha/package.json').write_text('{"dependencies":{"left-pad":"1.3.0"},"scripts":{"test":"node test.js"}}')
        ont={'schema':'cora-ontology/1','products':[
            {'id':'alpha','roots':['apps/alpha'],'entrypoints':['apps/alpha/main.py']},
            {'id':'beta','roots':['apps/beta'],'entrypoints':['apps/beta/task.py']}],
            'software':[{'id':'shared','roots':['src/shared'],'product_ids':['alpha','beta']}]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ont))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','fixture truth')
        self.commit=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.tmp.cleanup()
    def test_positive_blob_and_revalidation(self):
        c=closure(self.repo,'committed_blob','apps/alpha/main.py')
        self.assertEqual(c['status'],'PASS_SCOPED')
        self.assertTrue(verify_certificate(self.repo,c))
    def test_missing_blob_counterexample(self):
        c=closure(self.repo,'committed_blob','missing.py')
        self.assertEqual(c['status'],'REFUTED')
        self.assertEqual(c['blocking'],['git_file_present'])
    def test_declared_product_positive(self):
        c=closure(self.repo,'declared_product_membership','apps/alpha/main.py',selector='alpha')
        self.assertEqual(c['status'],'PASS_SCOPED')
        self.assertIn('graph',c['sources'])
        self.assertTrue(verify_certificate(self.repo,c))
    def test_undeclared_product_refutes_identity(self):
        c=closure(self.repo,'declared_product_membership','apps/alpha/main.py',selector='nonexistent')
        self.assertEqual(c['status'],'REFUTED')
    def test_missing_membership_blocks(self):
        c=closure(self.repo,'declared_product_membership','apps/alpha/main.py',selector='beta')
        self.assertEqual(c['status'],'BLOCKED')
    def test_manifest_declared_dependency(self):
        c=closure(self.repo,'declared_manifest_dependency','apps/alpha/package.json',selector='left-pad')
        self.assertEqual(c['status'],'PASS_SCOPED')
        self.assertTrue(verify_certificate(self.repo,c))
    def test_unobserved_dependency_blocks(self):
        c=closure(self.repo,'declared_manifest_dependency','apps/alpha/package.json',selector='unseen')
        self.assertEqual(c['status'],'BLOCKED')
    def test_dynamic_import_blocks_static_candidate(self):
        c=closure(self.repo,'static_import_candidate','apps/alpha/main.py',selector='src/shared/util.py')
        self.assertEqual(c['status'],'BLOCKED')
        self.assertIn('import_resolution_nonambiguous',c['blocking'])
    def test_static_import_without_dynamic_is_pass_scoped(self):
        c=closure(self.repo,'static_import_candidate','apps/beta/task.py',selector='src/shared/util.py')
        self.assertEqual(c['status'],'PASS_SCOPED')
    def test_safe_deletion_always_blocked(self):
        c=closure(self.repo,'safe_deletion','apps/beta/task.py')
        self.assertEqual(c['status'],'BLOCKED')
        self.assertIn('runtime_paths_closure',c['blocking'])
        self.assertEqual(c['effect'],'OBSERVATIONAL_ONLY')
    def test_dirty_worktree_cannot_change_receipt(self):
        before=closure(self.repo,'committed_blob','apps/beta/task.py')
        (self.repo/'apps/beta/task.py').write_text('malicious change not committed')
        self.assertEqual(before,closure(self.repo,'committed_blob','apps/beta/task.py'))
    def test_new_commit_changes_evidence(self):
        before=closure(self.repo,'committed_blob','apps/beta/task.py')
        (self.repo/'apps/beta/task.py').write_text('new tracked commit')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','change')
        self.assertNotEqual(before['certificate_digest'],closure(self.repo,'committed_blob','apps/beta/task.py')['certificate_digest'])
        self.assertTrue(verify_certificate(self.repo,before))
    def test_reforged_certificate_rejected(self):
        c=closure(self.repo,'committed_blob','apps/alpha/main.py')
        c['status']='BLOCKED'
        c['certificate_digest']=domain_hash('CORA:closure-certificate:1',{k:v for k,v in c.items() if k!='certificate_digest'})
        with self.assertRaises(ValueError):verify_certificate(self.repo,c)
    def test_injected_obligation_rejected(self):
        c=closure(self.repo,'safe_deletion','apps/beta/task.py')
        c['obligations']=[{'id':'git_file_present','state':'VERIFIED','evidence':'forged'}]
        c['status']='PASS_SCOPED';c['blocking']=[]
        c['certificate_digest']=domain_hash('CORA:closure-certificate:1',{k:v for k,v in c.items() if k!='certificate_digest'})
        with self.assertRaises(ValueError):verify_certificate(self.repo,c)
    def test_unsupported_symlink_blocks(self):
        (self.repo/'link.py').symlink_to('/etc/passwd')
        git(self.repo,'add','link.py');git(self.repo,'commit','-qm','symlink')
        c=closure(self.repo,'committed_blob','link.py')
        self.assertEqual(c['status'],'BLOCKED')
    def test_cli_end_to_end(self):
        output=self.repo/'cert.json'
        self.assertEqual(main(['closure',str(self.repo),'--claim','committed_blob','--path','apps/alpha/main.py','--output',str(output)]),0)
        self.assertEqual(main(['verify-certificate',str(output),'--repo',str(self.repo)]),0)
    def test_selector_is_required(self):
        with self.assertRaises(ValueError):closure(self.repo,'declared_product_membership','apps/alpha/main.py')


class ClosurePureContract(unittest.TestCase):
    def test_priority_counterexample_over_unknown(self):
        status,blocked=decide([{'id':'a','state':'UNKNOWN','evidence':'x'},{'id':'b','state':'COUNTEREXAMPLE','evidence':'y'}])
        self.assertEqual((status,blocked),('REFUTED',['b']))
    def test_duplicate_obligation_fails(self):
        a={'id':'a','state':'VERIFIED','evidence':'x'}
        with self.assertRaises(ValueError):decide([a,a])
    def test_stress_family_count_and_replay(self):
        self.assertEqual(len(FAMILIES),24)
        a=stress_closure(seed=883,cases=2000)
        self.assertEqual(a,stress_closure(seed=883,cases=2000))
        self.assertEqual((a['mismatches'],a['distinct_evidence_vectors']),(0,2000))
    def test_invalid_synthetic_vector(self):
        with self.assertRaises(ValueError):scenario(1 << 20,883)

if __name__=='__main__':unittest.main()
