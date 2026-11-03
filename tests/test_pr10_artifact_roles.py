"""Independent Git fixtures for overlapping test/contract/software names."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.artifact_roles import (artifact_audit,verify_artifact_report,roles_for,validate_declarations)
from cora.file_lab import examine_file, verify_lab
from cora.artifact_saturation import saturate,CLASSES,policy,independent_oracle
from cora.evidence import domain_hash


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE).decode().strip()


class IndependentFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.name','Role fixture');git(self.repo,'config','user.email','roles@invalid.example')
        (self.repo/'src').mkdir()
        (self.repo/'src/test_contract.py').write_text('import os\nassert True\n')
        (self.repo/'src/contract_test.py').write_text('RULE=True\n')
        (self.repo/'main.py').write_text('import src.test_contract\n')
        roles={'schema':'cora-artifact-roles/1','rules':[
            {'pattern':'src/*.py','roles':['SOFTWARE_SOURCE'],'rationale':'Actual source membership declared by maintainers'},
            {'pattern':'src/test_contract.py','roles':['CONTRACT_VERIFIER','SOFTWARE_SOURCE','TEST'],'rationale':'Explicit triple-role file tested independently'},
            {'pattern':'cora.artifact-roles.json','roles':['ARTIFACT_INDEX'],'rationale':'Self role metadata declaration'},
            {'pattern':'main.py','roles':['ENTRYPOINT','SOFTWARE_SOURCE'],'rationale':'Explicit entrypoint from fixture definition'},
            {'pattern':'cora.ontology.json','roles':['PRODUCT_CONTRACT'],'rationale':'Committed product and software ontology'},
        ]}
        (self.repo/'cora.artifact-roles.json').write_text(json.dumps(roles))
        ont={'schema':'cora-ontology/1','products':[{'id':'demo','roots':['src','main.py'],'entrypoints':['main.py']}],
            'software':[{'id':'impl','roots':['src'],'product_ids':['demo']}]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ont))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','fixture')
    def tearDown(self):self.temp.cleanup()
    def test_multirole_same_file(self):
        report=artifact_audit(self.repo)
        entry=next(a for a in report['artifacts'] if a['path']=='src/test_contract.py')
        self.assertEqual(set(entry['roles']),{'SOFTWARE_SOURCE','TEST','CONTRACT_VERIFIER'})
        self.assertEqual(entry['status'],'DECLARED_NOT_BEHAVIORALLY_ATTESTED')
        other=next(a for a in report['artifacts'] if a['path']=='src/contract_test.py')
        self.assertEqual(other['roles'],['SOFTWARE_SOURCE']) # reversed filename is NOT semantic proof
        self.assertTrue(verify_artifact_report(self.repo,report))
    def test_dirty_worktree_invariant(self):
        before=artifact_audit(self.repo)
        (self.repo/'src/test_contract.py').write_text('changed but uncommitted')
        self.assertEqual(before,artifact_audit(self.repo))
    def test_tampering_even_with_rehashed_digest(self):
        data=artifact_audit(self.repo)
        entry=next(a for a in data['artifacts'] if a['path']=='src/contract_test.py')
        entry['roles']=['TEST']
        data['report_digest']=domain_hash('CORA:artifact-report:1',{k:v for k,v in data.items() if k!='report_digest'})
        with self.assertRaises(ValueError):verify_artifact_report(self.repo,data)
    def test_manifest_missing_or_injected_does_not_prove_runtime(self):
        lab=examine_file(self.repo,'src/test_contract.py')
        self.assertIn('CONTRACT_VERIFIER',lab['artifact_roles']['roles'])
        self.assertEqual(lab['dead_code']['status'],'NOT_PROVEN')
        self.assertFalse(lab['triage']['automatic_change_authorized'])
        self.assertTrue(verify_lab(self.repo,lab))
    def test_invalid_root_and_duplicate_pattern(self):
        r={'schema':'cora-artifact-roles/1','rules':[{'pattern':'../secret','roles':['TEST'],'rationale':'Unsafe rule pattern must be rejected'}]}
        with self.assertRaises(ValueError):validate_declarations(r)
    def test_unclassified_artifact_blocks_self_completeness(self):
        (self.repo/'unknown.data').write_bytes(b'unknown')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','new object')
        report=artifact_audit(self.repo)
        self.assertIn('unknown.data',[x['path'] for x in report['artifacts'] if not x['roles']])
    def test_real_commit_switch_changes_report(self):
        old=artifact_audit(self.repo)
        (self.repo/'new.txt').write_text('new')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','new')
        self.assertNotEqual(old['report_digest'],artifact_audit(self.repo)['report_digest'])


class FinitePolicyTests(unittest.TestCase):
    def test_all_512_role_uncertainty_oracle_pairs(self):
        for role in range(16):
            for unknown in range(32):
                self.assertEqual(policy(role,unknown),independent_oracle(role,unknown))
    def test_saturation_small(self):
        result=saturate(seed=883,minimum_cases=CLASSES,no_novelty=1000)
        self.assertEqual((result['semantic_classes_observed'],result['new_classes_after_M'],result['mismatches']),(CLASSES,0,0))
    def test_saturation_replay(self):
        self.assertEqual(saturate(seed=883,minimum_cases=20000,no_novelty=100),saturate(seed=883,minimum_cases=20000,no_novelty=100))
    def test_invalid_risks(self):
        with self.assertRaises(ValueError):policy(-1,0)

if __name__=='__main__':unittest.main()
