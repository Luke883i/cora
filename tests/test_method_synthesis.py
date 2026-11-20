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



def clone_original_git_fixture(source, destination):
    """Independent transport clone; no hardlinked object store or leaked Git overrides.

    This deliberately does not retry: a failed physical Git fixture is an
    observed failure, with bounded diagnostic stderr rather than a hidden
    CalledProcessError. The root cause of the historical CI failure is not
    inferred by changing transport.
    """
    import os
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_CONFIG_") and key not in (
               "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
               "GIT_INDEX_FILE")}
    try:
        result = subprocess.run(
            ["git", "-C", str(source), "clone", "--no-local", "-q",
             "--", str(source), str(destination)],
            capture_output=True, text=True, timeout=60, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("original-Git physical fixture clone failed: " +
                           type(exc).__name__) from exc
    if result.returncode:
        detail = (result.stderr or result.stdout or "NO_GIT_DIAGNOSTIC").strip()
        raise RuntimeError("original-Git physical fixture clone failed"
                           f" (exit {result.returncode}): " + detail[:1200])
    if not (destination / ".git").exists():
        raise RuntimeError("clone returned success without original Git metadata")


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
        # Workflow census is bound to the original commit, not PR25's historical 12.
        # The independent Git tree count detects both additions and omissions.
        discovered = [p for p in git(ROOT, 'ls-tree', '-r', '--name-only',
                                    self.source, '--', '.github/workflows').splitlines()
                      if p.endswith(('.yml', '.yaml'))]
        self.assertGreaterEqual(len(discovered), 12)
        self.assertEqual(result['workflow_count'], len(discovered))
        self.assertEqual(result['authorization'],'NONE')
        self.assertEqual(result['source_model'],'BLOCKED_UNOBSERVED')
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
            clone_original_git_fixture(ROOT, local)
            git(local,'checkout','-q',self.source)
            git(local,'config','user.name','CI fixture')
            git(local,'config','user.email','ci@example.invalid')
            source = synthesize(local)
            self.assertTrue(verify_synthesis(local,source))
            commit = mutate(local,'.cora/contracts/profiles/method-atlas.json',
                            lambda x:x['procedures'][0].update(
                                source='src/cora/nonexistent.py'))
            with self.assertRaises(ValueError):
                synthesize(local,commit)
            with self.assertRaises(ValueError):
                verify_synthesis(local,dict(source,commit=commit))
            def wrong_identity(x):
                x['procedures'][0]['source']='src/cora/git_snapshot.py'
                x['product']='invented-product'
            mutate(local,'.cora/contracts/profiles/method-atlas.json',wrong_identity)
            with self.assertRaisesRegex(ValueError,'product/software identity mismatch'):
                synthesize(local)
            def wrong_reference(x):
                x['product']='cora'
                x['procedures'][0]['standards']=['UNKNOWN_REFERENCE']
            mutate(local,'.cora/contracts/profiles/method-atlas.json',wrong_reference)
            with self.assertRaisesRegex(ValueError,'method reference binding invalid'):
                synthesize(local)

    def test_physical_git_role_conflict_detected_not_approvable(self):
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'cora'
            clone_original_git_fixture(ROOT, local)
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
            self.assertEqual(result['source_model'],'REFUTED')
            self.assertEqual(result['governed_model'],'REFUTED')
            self.assertTrue(verify_synthesis(local,result))

    def test_source_readback_differs_from_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'cora'
            clone_original_git_fixture(ROOT, local)
            git(local,'checkout','-q',self.source)
            expected=synthesize(local)
            (local/'.cora/contracts/profiles/method-atlas.json').write_text('{}\n',encoding='utf-8')
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
        doc=json.loads((ROOT/'.cora/contracts/dod/method-synthesis-dod.json').read_text('utf-8'))
        self.assertEqual(len(ordered_cut(doc['nodes'],'G_GOVERNED')),16)
        self.assertEqual(doc['external_status'],'BLOCKED_EXTERNAL')


if __name__=='__main__':
    unittest.main()
