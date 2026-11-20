"""Independent temporary Git fixtures; negative claims stay fail-closed."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.evidence import domain_hash
from cora.file_lab import (AI_SCHEMA, RUNTIME_SCHEMA, examine_file, verify_lab,
                           ai_prompt, record_human_decision)
from cora.cli import main


def git(repo, *cmd):
    return subprocess.check_output(['git', '-C', str(repo), *cmd], stderr=subprocess.STDOUT).decode().strip()


class LabFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo,'init','-q')
        git(self.repo,'config','user.name','Independent Fixture')
        git(self.repo,'config','user.email','fixture@invalid.example')
        for name in ('apps/api','apps/worker','src/shared'):
            (self.repo/name).mkdir(parents=True)
        (self.repo/'apps/api/main.py').write_text('import shared.util\n__import__("optional_plugin")\n')
        (self.repo/'apps/worker/task.py').write_text('import shared.util\n')
        (self.repo/'src/shared/util.py').write_text('ANSWER=42\n')
        (self.repo/'src/shared/legacy.py').write_text('LEGACY=True\n')
        (self.repo/'apps/api/package.json').write_text('{"dependencies":{"left-pad":"1.3.0"}}')
        ontology={'schema':'cora-ontology/1','products':[
            {'id':'api','roots':['apps/api'],'entrypoints':['apps/api/main.py']},
            {'id':'worker','roots':['apps/worker'],'entrypoints':['apps/worker/task.py']}],
            'software':[{'id':'shared','roots':['src/shared'],'product_ids':['api','worker']}]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ontology))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','fixture')
        self.commit=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.temp.cleanup()
    def file(self,path='src/shared/util.py',**kwargs):
        return examine_file(self.repo,path,**kwargs)
    def write_external(self, value):
        p=Path(self.temp.name+'.json')
        p.write_text(json.dumps(value))
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        return p
    def test_distinguishes_product_software_repo_and_file(self):
        l=self.file();self.assertEqual(l['commit'],self.commit)
        self.assertEqual(len(l['relations']['incoming']),4) # repo, declared software, two importers
        self.assertIn('software:shared',l['levels']['L2_software']['declared_software_or_product'])
        self.assertEqual(l['triage']['current_state'],'RETAIN')
        self.assertEqual(l['scope'].split(';')[0],'read_only_single_file')
    def test_static_incoming_and_outgoing_are_distinguished(self):
        l=self.file('apps/worker/task.py')
        self.assertEqual(l['levels']['L1_code']['outgoing_python_import_candidates'][0]['target'],'file:src/shared/util.py')
        self.assertTrue(l['levels']['L3_product']['entrypoint'])
    def test_candidate_unreferenced_is_never_dead_or_deletable(self):
        l=self.file('src/shared/legacy.py')
        self.assertTrue(l['dead_code']['unreferenced_in_partial_graph'])
        self.assertEqual(l['dead_code']['status'],'NOT_PROVEN')
        self.assertEqual(l['triage']['current_state'],'INVESTIGATE')
        self.assertFalse(any(x['permitted'] for x in l['triage']['available_treatments'] if x['state']=='DELETE_BLOCKED'))
    def test_dynamic_unknown_is_not_false_clean(self):
        l=self.file('apps/api/main.py')
        self.assertIn('dynamic_import_unknown',{f['kind'] for f in l['levels']['L1_code']['unresolved']})
    def test_manifest_dep_and_unknown_semantics(self):
        l=self.file('apps/api/package.json')
        self.assertEqual(l['relations']['manifest']['dependencies'][0]['name'],'left-pad')
        self.assertEqual(l['levels']['L5_operational']['external_consumers'],'UNOBSERVED')
    def test_dirty_worktree_not_part_of_commit(self):
        a=self.file();(self.repo/'src/shared/util.py').write_text('CHANGED')
        self.assertEqual(a,self.file())
    def test_new_commit_changes_lab(self):
        a=self.file();(self.repo/'src/shared/util.py').write_text('CHANGED')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','commit')
        self.assertNotEqual(a['lab_digest'],self.file()['lab_digest'])
    def test_lab_verification_resists_rehashed_fake_edges(self):
        l=self.file();self.assertTrue(verify_lab(self.repo,l))
        l['triage']['current_state']='DELETE_BLOCKED'
        l['lab_digest']=domain_hash('CORA:file-lab:1',{k:v for k,v in l.items() if k!='lab_digest'})
        with self.assertRaises(ValueError):verify_lab(self.repo,l)
    def test_runtime_import_is_scoped_self_reported_only(self):
        doc={'schema':RUNTIME_SCHEMA,'commit':self.commit,'provenance':'sample:otel-export:run-18',
             'observations':[{'path':'src/shared/legacy.py','kind':'loaded','count':7,'source_ref':'span:abc'}]}
        l=self.file('src/shared/legacy.py',runtime_events=self.write_external(doc))
        self.assertEqual(l['levels']['L5_operational']['runtime']['status'],'CALLER_SUPPLIED_UNVERIFIED')
        self.assertEqual(l['triage']['current_state'],'RETAIN')
        self.assertEqual(l['dead_code']['status'],'NOT_PROVEN')
        with self.assertRaises(ValueError):verify_lab(self.repo,l)
    def test_runtime_commit_mismatch_fails(self):
        doc={'schema':RUNTIME_SCHEMA,'commit':'0'*40,'provenance':'sample','observations':[]}
        with self.assertRaises(ValueError):self.file(runtime_events=self.write_external(doc))
    def test_absent_runtime_observation_not_nonuse(self):
        doc={'schema':RUNTIME_SCHEMA,'commit':self.commit,'provenance':'sample','observations':[]}
        l=self.file('src/shared/legacy.py',runtime_events=self.write_external(doc))
        self.assertEqual(l['dead_code']['status'],'NOT_PROVEN')
        self.assertTrue(l['dead_code']['candidate_for_investigation'])
    def test_ai_hypotheses_do_not_promote_grounding_into_proof(self):
        l=self.file();ref=l['evidence_ids'][0]
        doc={'schema':AI_SCHEMA,'commit':self.commit,'path':l['path'],
             'hypotheses':[{'hypothesis':'Maybe used by external API','suggested_treatment':'ARCHIVE_CANDIDATE',
                            'evidence_refs':[ref,'forged:abc'],'counterevidence':['unknown public consumers'],
                            'confidence_range':[0.1,0.9]}]}
        augmented=self.file(ai_hypotheses=self.write_external(doc))
        self.assertEqual(augmented['ai']['hypotheses'][0]['grounding_status'],'NOT_GROUNDED')
        self.assertEqual(augmented['ai']['hypotheses'][0]['state'],'UNVERIFIED_AI_HYPOTHESIS')
        self.assertFalse(augmented['triage']['automatic_change_authorized'])
    def test_ai_subject_mismatch_rejected(self):
        doc={'schema':AI_SCHEMA,'commit':'0'*40,'path':'src/shared/util.py','hypotheses':[]}
        with self.assertRaises(ValueError):self.file(ai_hypotheses=self.write_external(doc))
    def test_ai_bad_confidence_rejected(self):
        doc={'schema':AI_SCHEMA,'commit':self.commit,'path':'src/shared/util.py','hypotheses':[
            {'hypothesis':'delete','suggested_treatment':'DELETE_BLOCKED','evidence_refs':[],
             'counterevidence':[],'confidence_range':[1.0,0.0]}]}
        with self.assertRaises(ValueError):self.file(ai_hypotheses=self.write_external(doc))
    def test_prompt_has_no_source_code_or_network_action(self):
        p=ai_prompt(self.file())
        self.assertNotIn('ANSWER=42',json.dumps(p))
        self.assertEqual(p['output_contract'],AI_SCHEMA)
        self.assertIn('No source file content',p['privacy'])
    def test_human_two_person_gate_for_archive(self):
        lab=self.file()
        d=record_human_decision(lab,actor='human1',role='PRODUCT_OWNER',action='ARCHIVE_CANDIDATE',
                                rationale='Needs explicit retention review')
        self.assertEqual(d['state'],'AWAITING_INDEPENDENT_REVIEW')
        d2=record_human_decision(lab,actor='human1',role='PRODUCT_OWNER',action='ARCHIVE_CANDIDATE',
                                rationale='Needs explicit retention review',second_reviewer='human2')
        self.assertEqual(d2['state'],'HUMAN_INTENT_RECORDED_NOT_EXECUTED')
        self.assertEqual(d2['effect'],'RECORD_ONLY_NO_REPO_CHANGES')
    def test_delete_always_blocked_even_with_two_humans(self):
        d=record_human_decision(self.file(),actor='person1',role='TECH_LEAD',action='DELETE_BLOCKED',
                                rationale='Delete after human review',second_reviewer='person2')
        self.assertEqual(d['state'],'BLOCKED_NO_DELETION_CAPABILITY')
    def test_human_identity_is_not_authenticated(self):
        d=record_human_decision(self.file(),actor='person1',role='MAINTAINER',action='RETAIN',
                                rationale='Retain during maintenance review')
        self.assertEqual(d['effect'],'RECORD_ONLY_NO_REPO_CHANGES')
    def test_invalid_file_escape_and_missing(self):
        with self.assertRaises(ValueError):self.file('../secrets')
        with self.assertRaises(ValueError):self.file('missing.py')
    def test_cli_file_lab_and_decision_on_real_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            lab_path=Path(temp)/'lab.json';prompt=Path(temp)/'prompt.json';decision=Path(temp)/'decision.json'
            self.assertEqual(main(['file-lab',str(self.repo),'--path','src/shared/legacy.py',
                                   '--output',str(lab_path),'--prompt-output',str(prompt)]),0)
            self.assertEqual(main(['verify-file-lab',str(lab_path),'--repo',str(self.repo)]),0)
            self.assertEqual(main(['file-decision',str(lab_path),'--actor','engineer','--role','MAINTAINER',
                                   '--action','INVESTIGATE','--rationale','Check unknown external consumers',
                                   '--output',str(decision)]),0)
            self.assertEqual(json.loads(decision.read_text())['state'],'HUMAN_INTENT_RECORDED_NOT_EXECUTED')
            self.assertEqual(git(self.repo,'status','--porcelain'),'')

if __name__=='__main__':unittest.main()
