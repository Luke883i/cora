"""PR29 five-goal source, adversarial and original-Git witness tests."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.integrated_service import integrated_case
from cora.synergy import (five_dod, semantic_truth, reasoning_plan, import_ai_reasoning,
                          invoke_reasoner, behavioral_proofs, verify_behavioral_proofs,
                          semantic_evolution, verify_semantic_evolution,
                          unified_assurance, verify_unified_assurance,
                          stress_five_synergies, _validated_seed)

ROOT=Path(__file__).resolve().parents[1]


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],
                                   stderr=subprocess.PIPE).decode('utf-8').strip()


class FiveSynergiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'.git').exists():
            raise unittest.SkipTest('full original Git checkout required')
        cls.head=git(ROOT,'rev-parse','HEAD')

    def test_semantic_truth_against_original_source(self):
        base=integrated_case(ROOT,self.head)
        result=semantic_truth(ROOT,base)
        self.assertEqual(result['commit'],self.head)
        self.assertEqual(len(result['claims']),18)
        self.assertEqual(result['verified_semantic_claims'],0)
        self.assertEqual(result['authorization'],'NONE')
        self.assertTrue(all(x['semantic_entailment']=='NOT_ATTESTED' for x in result['claims']))
        self.assertEqual(five_dod(ROOT,self.head)['nodes'],29)
        self.assertEqual(five_dod(ROOT,self.head)['governed_status'],'BLOCKED_EXTERNAL')
        self.assertTrue(any(y['status']=='TEST_SYMBOLS_OBSERVED_NOT_RUN'
                            for x in result['claims'] for y in x['source_witnesses']))


    def test_ai_reasoner_opt_in_positive_and_adversarial(self):
        case=integrated_case(ROOT,self.head)
        truth=semantic_truth(ROOT,case)
        plan=reasoning_plan(case,truth)
        self.assertEqual(len(plan['candidate_questions']),18)
        self.assertFalse(plan['source_bytes_embedded'])
        self.assertFalse(plan['provider_invoked'])
        self.assertIn('claim:S01',plan['request']['valid_source_refs'])
        self.assertEqual(invoke_reasoner(case,truth)['provider'],'NOT_CONNECTED')
        with self.assertRaisesRegex(ValueError,'explicit valid'):
            invoke_reasoner(case,truth,lambda x: {},authorize=False)
        calls=[]
        def fake_provider(request):
            calls.append(request)
            return {'schema':'cora-integrated-ai/1',
                    'source_commit':case['commit'],
                    'case_digest':case['case_digest'],
                    'items':[{'id':'a1',
                        'hypothesis':'The README claim may not match its actual behavior.',
                        'support_refs':['claim:S01'],
                        'counter_refs':['method:documentation-assurance'],
                        'abstraction_path':['documents','architecture','product'],
                        'adversarial_scenario':'Break the source implementation but keep the README.',
                        'positive_control':'Preserve the source while verifying actual behavior.',
                        'action':'INVESTIGATE'}]}
        obs=invoke_reasoner(case,truth,fake_provider,authorize=True)
        self.assertEqual(len(calls),1)
        self.assertEqual(obs['provider'],'CALLBACK_CALLED_NOT_INDEPENDENTLY_ATTESTED')
        self.assertEqual(obs['observations'][0]['state'],'UNVERIFIED_AI_HYPOTHESIS')
        self.assertEqual(obs['authority'],'NONE')
        forged=fake_provider(plan['request'])
        forged['items'][0]['counter_refs']=['claim:S01']
        with self.assertRaisesRegex(ValueError,'same witness'):
            import_ai_reasoning(case,forged)
        forged['items'][0]['counter_refs']=['INVENTED']
        with self.assertRaises(ValueError):
            import_ai_reasoning(case,forged)
        forged['items'][0]['action']='APPROVE'
        with self.assertRaises(ValueError):
            import_ai_reasoning(case,forged)


    def test_original_behavioral_probes_and_forged_receipt(self):
        case=integrated_case(ROOT,self.head)
        inactive=behavioral_proofs(ROOT,case)
        self.assertEqual(inactive['source_probes_passed'],0)
        with self.assertRaises(ValueError):
            verify_behavioral_proofs(ROOT,inactive)
        evidence=behavioral_proofs(ROOT,case,authorize=True)
        self.assertEqual(evidence['source_probes_passed'],3)
        self.assertFalse(evidence['runtime_attested'])
        self.assertFalse(evidence['all_71_behaviors_proven'])
        self.assertTrue(verify_behavioral_proofs(ROOT,evidence))
        forged=copy.deepcopy(evidence)
        forged['source_probes_passed']=71
        with self.assertRaisesRegex(ValueError,'forged'):
            verify_behavioral_proofs(ROOT,forged)


    def test_real_continuous_semantic_impact_and_stale_forgery(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=Path(directory)/'evolution'
            subprocess.run(['git','clone','--no-local','-q',str(ROOT),str(repo)],check=True)
            git(repo,'config','user.name','CORA evolution case')
            git(repo,'config','user.email','test@example.invalid')
            git(repo,'checkout','-q',self.head)
            base=self.head
            path=repo/'README.md'
            path.write_text(path.read_text('utf-8')+'\\n## Candidate semantic evolution change\\n',encoding='utf-8')
            git(repo,'add','README.md')
            git(repo,'commit','-qm','change current product front door')
            head=git(repo,'rev-parse','HEAD')
            case=integrated_case(repo,head)
            report=semantic_evolution(repo,base,case)
            self.assertEqual(report['head_commit'],head)
            self.assertIn('README.md',report['changed_paths'])
            self.assertEqual(report['behavioral_regression'],'NOT_ATTESTED')
            self.assertEqual(report['dynamic_consumers'],'UNKNOWN')
            self.assertTrue(verify_semantic_evolution(repo,report))
            fake=copy.deepcopy(report)
            fake['unmapped_changed_paths']=[]
            fake['impacts']=[]
            with self.assertRaisesRegex(ValueError,'replay mismatch'):
                verify_semantic_evolution(repo,fake)


    def test_all_five_goals_end_to_end_and_forged_source_replay(self):
        parent=git(ROOT,'rev-parse','HEAD^')
        report=unified_assurance(ROOT,self.head,base=parent,execute_probes=True)
        self.assertEqual(report['method_counts'],{
            'commands':71,'families':8,'original_methods':14,
            'object_types':20,'abstraction_dimensions':12})
        self.assertEqual(len(report['truth']['claims']),18)
        self.assertEqual(len(report['reasoning_plan']['candidate_questions']),18)
        self.assertEqual(report['behavior']['source_probes_passed'],3)
        self.assertIsNotNone(report['evolution'])
        self.assertEqual(report['reticulum']['nodes'],29)
        self.assertEqual(report['goals']['G_UNIFIED'],'SOURCE_CANDIDATE_NOT_PRODUCT_READY')
        self.assertEqual(report['goals']['G_GOVERNED'],'BLOCKED_EXTERNAL')
        self.assertFalse(report['all_71_behaviors_proven'])
        self.assertFalse(report['actual_model_provider_attested'])
        self.assertTrue(verify_unified_assurance(ROOT,report))
        forged=copy.deepcopy(report)
        forged['goals']['G_GOVERNED']='PASS'
        with self.assertRaisesRegex(ValueError,'Git replay mismatch'):
            verify_unified_assurance(ROOT,forged)

    def test_seeded_semantic_mutations_controls_and_repeatability(self):
        a=stress_five_synergies(ROOT,self.head,cases=32000,seed=883)
        b=stress_five_synergies(ROOT,self.head,cases=32000,seed=883)
        self.assertEqual(a,b)
        self.assertEqual(a['families'],32)
        self.assertEqual(a['positive_controls'],2000)
        self.assertEqual(a['negative_scenarios'],30000)
        self.assertEqual(a['oracle_disagreements'],0)
        self.assertEqual(a['unauthorized_promotions'],0)
        self.assertEqual(a['physical_source_mutations'],0)
        self.assertEqual(a['external_status'],'BLOCKED_EXTERNAL')
        with self.assertRaises(ValueError):
            stress_five_synergies(ROOT,self.head,cases=1000001)

    def test_physical_preseed_fault_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=Path(directory)/'preseed'
            subprocess.run(['git','clone','--no-local','-q',str(ROOT),str(repo)],check=True)
            git(repo,'config','user.name','preseed adversarial source')
            git(repo,'config','user.email','mutant@example.invalid')
            git(repo,'checkout','-q',self.head)
            self.assertEqual(len(_validated_seed(repo,self.head)),32)
            path=repo/'.cora/fixtures/five-synergies-mutants.json'
            source=json.loads(path.read_text('utf-8'))
            source['rows'][2]['invalidated']=[]
            path.write_text(json.dumps(source),encoding='utf-8')
            git(repo,'add',path.relative_to(repo).as_posix())
            git(repo,'commit','-qm','preseed negative turned into false positive')
            with self.assertRaisesRegex(ValueError,'preseed semantic fault/oracle changed'):
                _validated_seed(repo,git(repo,'rev-parse','HEAD'))


    def test_real_unified_cli_and_source_replay(self):
        from cora.cli import main
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'five-goals.json'
            ai=Path(directory)/'ai-request.json'
            parent=git(ROOT,'rev-parse','HEAD^')
            self.assertEqual(main(['method-synthesize',str(ROOT),'--revision',self.head,
                                   '--synergic','--base-sha',parent,
                                   '--execute-source-probes','--output',str(out),
                                   '--ai-request-output',str(ai)]),0)
            report=json.loads(out.read_text('utf-8'))
            request=json.loads(ai.read_text('utf-8'))
            self.assertEqual(report['method_counts']['commands'],71)
            self.assertEqual(request['schema'],'cora-synergic-reasoner/1')
            self.assertFalse(request['provider_invoked'])
            self.assertEqual(main(['verify-method-synthesis',str(out),
                                   '--repo',str(ROOT),'--synergic']),0)
            stress=Path(directory)/'stress.json'
            self.assertEqual(main(['stress-convergence','--synergic','--repo',str(ROOT),
                                   '--revision',self.head,'--sessions','1',
                                   '--cases-per-session','3200','--output',str(stress)]),0)
            self.assertEqual(json.loads(stress.read_text('utf-8'))['oracle_disagreements'],0)

    def test_physical_dod_and_readme_source_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/'cora-original'
            subprocess.run(['git','clone','--no-local','-q',str(ROOT),str(local)],check=True)
            git(local,'config','user.name','CORA physical mutant')
            git(local,'config','user.email','mutant@example.invalid')
            git(local,'checkout','-q',self.head)
            dod=local/'.cora/contracts/dod/five-synergies-dod.json'
            payload=json.loads(dod.read_text('utf-8'))
            next(x for x in payload['nodes'] if x['id']=='G_GOVERNED')['depends_on'].remove('E_HOST')
            dod.write_text(json.dumps(payload),encoding='utf-8')
            git(local,'add',dod.relative_to(local).as_posix())
            git(local,'commit','-qm','physical missing external authority mutant')
            with self.assertRaisesRegex(ValueError,'removed dependency'):
                five_dod(local,'HEAD')
            git(local,'checkout','-q',self.head)
            readme=local/'README.md'
            original=readme.read_text('utf-8')
            claims=json.loads((local/'.cora/assurance/documentation-proofs.json').read_text('utf-8'))
            phrase=claims['nodes'][0]['readme_phrase']
            self.assertIn(phrase,original)
            readme.write_text(original.replace(phrase,'MUTATED_UNSUPPORTED_PRODUCT_CLAIM',1),encoding='utf-8')
            git(local,'add',readme.name)
            git(local,'commit','-qm','physical README original claim mutation')
            row=semantic_truth(local,integrated_case(local,'HEAD'))
            self.assertIn('S01',row['source_contradictions'])


if __name__=='__main__':
    unittest.main()
