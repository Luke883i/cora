"""PR29 five-goal source, adversarial and original-Git witness tests."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.integrated_service import integrated_case
from cora.synergy import five_dod, semantic_truth

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
