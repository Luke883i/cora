"""PR-25 cross-method original-source proof, physical mutations and finite counterexamples."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.artifact_roles import artifact_audit
from cora.method_synthesis import (
    synthesize, verify_synthesis, _ground_hypotheses, analyst_request)
from cora.process_suite import run_suite
from cora.reticulum import ordered_cut
from cora.workflow_rationalization import audit_workflows

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args],
                                   stderr=subprocess.PIPE).decode().strip()


def mutate(repo, path, update):
    file = repo / path
    original = json.loads(file.read_text('utf-8'))
    update(original)
    file.write_text(json.dumps(original,indent=2)+'\n',encoding='utf-8')
    git(repo,'add',path)
    git(repo,'commit','-qm','physical source mutation')
    return git(repo,'rev-parse','HEAD')


class MethodSynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = git(ROOT,'rev-parse','HEAD')

    def test_self_cora_correlates_original_methods_without_authority(self):
        result = synthesize(ROOT, self.source)
        self.assertEqual(result['product_id'],'cora')
        self.assertEqual(result['reference_count'],9)
        self.assertEqual(result['procedure_count'],14)
        self.assertEqual(len(result['method_reference_edges']),28)
        self.assertEqual(result['workflow_count'],12)
        self.assertEqual(result['authorization'],'NONE')
        self.assertEqual(result['governed_model'],'BLOCKED_EXTERNAL')
        self.assertEqual(result['process_state'],'NOT_SUPPLIED')
        self.assertEqual(len(result['external_gaps']),4)
        self.assertEqual(len(result['software_methods']),2)
        self.assertTrue(verify_synthesis(ROOT,result))
        ask = analyst_request(result)
        self.assertEqual(ask['output_authority'],'NONE')
        self.assertFalse(ask['source_bytes_embedded'])

    def test_supplied_original_receipts_are_cross_verified_not_trusted(self):
        artifacts = artifact_audit(ROOT,self.source)
        workflows = audit_workflows(ROOT,self.source)
        result = synthesize(ROOT,self.source,artifacts=artifacts,workflows=workflows)
        self.assertTrue(verify_synthesis(ROOT,result,artifacts=artifacts,workflows=workflows))
        forged = copy.deepcopy(artifacts)
        forged['summary']['unclassified'] = 123
        with self.assertRaises(ValueError):
            synthesize(ROOT,self.source,artifacts=forged,workflows=workflows)
        with self.assertRaises(ValueError):
            verify_synthesis(ROOT,dict(result,authorization='APPROVED'),
                             artifacts=artifacts,workflows=workflows)

    def test_source_process_is_optional_not_a_fake_executed_method(self):
        source_process = run_suite(ROOT,self.source,process='source')
        result = synthesize(ROOT,self.source,process=source_process)
        self.assertEqual(result['receipt_sources']['process'],source_process['run_digest'])
        self.assertEqual(result['process_state'],source_process['status'])
        self.assertTrue(verify_synthesis(ROOT,result,process=source_process))
        with self.assertRaises(ValueError):
            verify_synthesis(ROOT,result)

    def test_physical_git_atlas_and_identity_mutants(self):
        with tempfile.TemporaryDirectory() as folder:
            local = Path(folder)/'cora'
            git(ROOT,'clone','--local','-q',str(ROOT),str(local))
            git(local,'checkout','-q',self.source)
            git(local,'config','user.name','CI fixture')
            git(local,'config','user.email','ci@example.invalid')
            source = synthesize(local)
            self.assertTrue(verify_synthesis(local,source))
            commit = mutate(local,'cora.method-atlas.json',
                            lambda x:x['procedures'][0].update(
                                source='src/cora/nonexistent.py'))
            with self.assertRaises(ValueError):
                synthesize(local,commit)
            with self.assertRaises(ValueError):
                verify_synthesis(local,dict(source,commit=commit))
            mutate(local,'cora.method-atlas.json',
                   lambda x:x.update(product='invented-product'))
            with self.assertRaises(ValueError):
                synthesize(local)

    def test_physical_git_role_conflict_detected_not_approvable(self):
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'cora'
            git(ROOT,'clone','--local','-q',str(ROOT),str(local))
            git(local,'checkout','-q',self.source)
            git(local,'config','user.name','CI fixture')
            git(local,'config','user.email','ci@example.invalid')
            def change(x):
                for item in x['rules']:
                    if item['pattern']=='.github/workflows/*.yml':
                        item['roles']=['POLICY']
            sha=mutate(local,'cora.artifact-roles.json',change)
            result=synthesize(local,sha)
            mismatches=[x for x in result['findings'] if x['id']=='ROLE_MISMATCH']
            self.assertTrue(mismatches)
            self.assertEqual(result['authorization'],'NONE')
            self.assertTrue(verify_synthesis(local,result))

    def test_source_readback_differs_from_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'cora'
            git(ROOT,'clone','--local','-q',str(ROOT),str(local))
            git(local,'checkout','-q',self.source)
            expected=synthesize(local)
            (local/'cora.method-atlas.json').write_text('{}\n',encoding='utf-8')
            self.assertEqual(synthesize(local),expected)
            self.assertTrue(verify_synthesis(local,expected))

    def test_ai_overlay_never_becomes_an_execution_witness(self):
        base=synthesize(ROOT,self.source)
        claims={'schema':'cora-method-hypotheses/1','commit':self.source,'items':[{
            'id':'h1','statement':'Potential overlap in source-level workflow inventory.',
            'evidence_refs':['procedure:workflow-intelligence'],
            'counter_refs':['procedure:process-catalog'],
            'action':'INVESTIGATE'}]}
        report=synthesize(ROOT,self.source,hypotheses=claims)
        self.assertEqual(report['ai_hypotheses'][0]['state'],'UNVERIFIED_AI_HYPOTHESIS')
        self.assertEqual(report['ai_hypotheses'][0]['authority'],'NONE')
        self.assertTrue(verify_synthesis(ROOT,report,hypotheses=claims))
        with self.assertRaises(ValueError):
            verify_synthesis(ROOT,report)
        forged=copy.deepcopy(claims)
        forged['items'][0]['action']='APPROVE'
        with self.assertRaises(ValueError):
            synthesize(ROOT,self.source,hypotheses=forged)
        self.assertEqual(base['authorization'],'NONE')

    def test_one_thousand_distinct_lexical_model_counterexamples(self):
        sha=self.source
        valid={'procedure:workflow-intelligence','procedure:process-catalog'}
        seen=set()
        for family in range(10):
            for i in range(100):
                doc={'schema':'cora-method-hypotheses/1','commit':sha,'items':[{
                    'id':'h1','statement':'Candidate for source-only review: '+str(i),
                    'evidence_refs':['procedure:workflow-intelligence'],
                    'counter_refs':['procedure:process-catalog'],'action':'INVESTIGATE'}]}
                h=doc['items'][0]
                if family==0: doc['commit']='0'*39+str(i % 10)
                elif family==1: h['id']='bad id '+str(i)
                elif family==2: h['evidence_refs']=[]
                elif family==3: h['evidence_refs']=['unknown:'+str(i)]
                elif family==4: h['counter_refs']=['external:'+str(i)]
                elif family==5: h['action']='APPROVE_'+str(i)
                elif family==6: h['statement']='bad'+str(i)
                elif family==7: h['evidence_refs']*=2
                elif family==8: doc['schema']='cora-ai-authority/'+str(i)
                else: h['id']=''
                digest=hashlib.sha256(json.dumps(doc,sort_keys=True).encode()).hexdigest()
                self.assertNotIn(digest,seen)
                seen.add(digest)
                with self.assertRaises(ValueError):
                    _ground_hypotheses(doc,sha,valid)
        self.assertEqual(len(seen),1000)

    def test_dod_cut_maintains_external_obligations(self):
        doc=json.loads((ROOT/'cora.method-synthesis-dod.json').read_text('utf-8'))
        self.assertEqual(len(ordered_cut(doc['nodes'],'G_GOVERNED')),16)
        self.assertEqual(doc['external_status'],'BLOCKED_EXTERNAL')


if __name__=='__main__':
    unittest.main()
