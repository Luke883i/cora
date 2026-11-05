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
                          invoke_reasoner, behavioral_proofs, verify_behavioral_proofs)

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

    def test_physical_dod_and_readme_source_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            local=Path(directory)/'cora-original'
            subprocess.run(['git','clone','--local','-q',str(ROOT),str(local)],check=True)
            git(local,'config','user.name','CORA physical mutant')
            git(local,'config','user.email','mutant@example.invalid')
            git(local,'checkout','-q',self.head)
            dod=local/'cora.five-synergies-dod.json'
            payload=json.loads(dod.read_text('utf-8'))
            next(x for x in payload['nodes'] if x['id']=='G_GOVERNED')['depends_on'].remove('E_HOST')
            dod.write_text(json.dumps(payload),encoding='utf-8')
            git(local,'add',dod.name)
            git(local,'commit','-qm','physical missing external authority mutant')
            with self.assertRaisesRegex(ValueError,'removed dependency'):
                five_dod(local,'HEAD')
            git(local,'checkout','-q',self.head)
            readme=local/'README.md'
            original=readme.read_text('utf-8')
            claims=json.loads((local/'cora.documentation-proofs.json').read_text('utf-8'))
            phrase=claims['nodes'][0]['readme_phrase']
            self.assertIn(phrase,original)
            readme.write_text(original.replace(phrase,'MUTATED_UNSUPPORTED_PRODUCT_CLAIM',1),encoding='utf-8')
            git(local,'add',readme.name)
            git(local,'commit','-qm','physical README original claim mutation')
            row=semantic_truth(local,integrated_case(local,'HEAD'))
            self.assertIn('S01',row['source_contradictions'])


if __name__=='__main__':
    unittest.main()
