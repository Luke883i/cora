"""R3 integrated source service: full original CORA, real Git mutants and finite controls."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.cli import main as cora_cli
from cora.integrated_service import (
    AI_SCHEMA, DIMENSIONS, FAULTS, ai_request, integrated_case,
    stress_integrated, verify_integrated,
)
from cora.method_synthesis import verify_synthesis

ROOT=Path(__file__).resolve().parents[1]

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],
                                   stderr=subprocess.PIPE).decode('utf-8').strip()

class IntegratedServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'.git').exists():
            raise unittest.SkipTest('requires original full CORA Git checkout')
        cls.sha=git(ROOT,'rev-parse','HEAD')

    def test_original_source_joins_and_exact_replay(self):
        case=integrated_case(ROOT,self.sha)
        self.assertEqual(case['commit'],self.sha)
        self.assertEqual(case['features']['available_parser_commands'],71)
        self.assertEqual(case['features']['declared_atlas_commands'],71)
        self.assertEqual(case['features']['families'],8)
        self.assertFalse(case['features']['all_behaviors_tested'])
        self.assertEqual(case['methods']['count'],14)
        self.assertEqual(case['methods']['types'],20)
        self.assertEqual(len(case['dimensions']),12)
        self.assertEqual(case['claim_to_implementation']['count'],18)
        self.assertEqual(len(case['semantic_crosswalk']),20)
        self.assertTrue(all(x['owner_source'].startswith(('src/','tools/')) for x in case['semantic_crosswalk']))
        self.assertTrue(all(x['state']=='DECLARED_SOURCE_RELATION_NOT_STANDARD_CONFORMANCE'
                            for x in case['semantic_crosswalk']))
        self.assertEqual(case['reticulum']['nodes'],17)
        self.assertEqual(case['reticulum']['full_status'],'BLOCKED_EXTERNAL')
        self.assertEqual(case['authorization'],'NONE')
        self.assertTrue(verify_integrated(ROOT,case))
        forged=copy.deepcopy(case)
        forged['features']['all_behaviors_tested']=True
        with self.assertRaisesRegex(ValueError,'replay mismatch'):
            verify_integrated(ROOT,forged)

    def test_all_71_canonical_cli_help_surfaces_are_reachable_without_effects(self):
        case=integrated_case(ROOT,self.sha)
        self.assertTrue(case['features']['canonical_parity'])
        import ast
        source=(ROOT/'src/cora/cli.py').read_text('utf-8')
        tree=ast.parse(source)
        commands=sorted({
            node.args[0].value for node in ast.walk(tree)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
            and node.func.attr=='add_parser' and node.args
            and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str)
        })
        self.assertEqual(len(commands),71)
        for command in commands:
            with self.subTest(command=command),contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as raised:
                    cora_cli([command,'--help'])
                self.assertEqual(raised.exception.code,0)
                self.assertIn('usage:',output.getvalue())
        # This is parser accessibility, not 71 independently executed features.

    def test_untrusted_ai_support_counterexample_and_stale_digest(self):
        original=integrated_case(ROOT,self.sha)
        prompt=ai_request(original)
        self.assertFalse(prompt['provider_invoked'])
        self.assertFalse(prompt['source_bytes_embedded'])
        self.assertEqual(prompt['authority'],'NONE')
        self.assertIn('claim:S01',prompt['valid_source_refs'])
        self.assertEqual(len(original['methods']['type_ids']),20)
        self.assertIn('type:git-revision',prompt['valid_source_refs'])
        result={'schema':AI_SCHEMA,'source_commit':self.sha,
                'case_digest':original['case_digest'],'items':[{
                    'id':'a1',
                    'hypothesis':'README claim may be semantically broader than software behavior.',
                    'support_refs':['claim:S01'],
                    'counter_refs':['method:documentation-assurance'],
                    'abstraction_path':['documents','architecture','product'],
                    'adversarial_scenario':'Keep README phrase while removing underlying behavior.',
                    'positive_control':'Check a real original method source and independent consumer.',
                    'action':'INVESTIGATE'}]}
        case=integrated_case(ROOT,self.sha,ai=result)
        self.assertEqual(case['ai_observations'][0]['state'],'UNVERIFIED_AI_HYPOTHESIS')
        self.assertEqual(case['ai_observations'][0]['authority'],'NONE')
        self.assertTrue(verify_integrated(ROOT,case,ai=result))
        with self.assertRaises(ValueError):
            verify_integrated(ROOT,case)
        for change in ('case_digest','source_commit'):
            bad=copy.deepcopy(result)
            bad[change]='0'*64 if change=='case_digest' else '0'*40
            with self.subTest(mutation=change),self.assertRaises(ValueError):
                integrated_case(ROOT,self.sha,ai=bad)
        for change in ('support_refs','counter_refs'):
            bad=copy.deepcopy(result)
            bad['items'][0][change]=['FORGED_WITNESS']
            with self.subTest(mutation=change),self.assertRaises(ValueError):
                integrated_case(ROOT,self.sha,ai=bad)
        bad=copy.deepcopy(result)
        bad['items'][0]['action']='APPROVE'
        with self.assertRaises(ValueError):
            integrated_case(ROOT,self.sha,ai=bad)

    def test_physical_real_cora_dod_and_document_mutants(self):
        with tempfile.TemporaryDirectory() as folder:
            local=Path(folder)/'original'
            subprocess.run(['git','clone','--local','-q',str(ROOT),str(local)],check=True)
            git(local,'config','user.name','CORA negative source fixture')
            git(local,'config','user.email','fixture@example.invalid')
            git(local,'checkout','-q',self.sha)
            base=integrated_case(local)
            self.assertTrue(verify_integrated(local,base))
            contract=local/'.cora/contracts/dod/integrated-dod.json'
            doc=json.loads(contract.read_text('utf-8'))
            next(x for x in doc['nodes'] if x['id']=='G_GOVERNED')['depends_on'].remove('E_REVIEW')
            contract.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
            git(local,'add','.cora/contracts/dod/integrated-dod.json')
            git(local,'commit','-qm','physical external-DoD-edge source mutant')
            with self.assertRaisesRegex(ValueError,'DoD false promotion'):
                integrated_case(local,'HEAD')
            git(local,'checkout','-q',self.sha)
            readme=local/'README.md'
            source=readme.read_text('utf-8')
            from_profile=json.loads((local/'cora.documentation-proofs.json').read_text('utf-8'))
            phrase=from_profile['nodes'][0]['readme_phrase']
            self.assertIn(phrase,source)
            readme.write_text(source.replace(phrase,'UNSUPPORTED_CANDIDATE_SENTENCE',1),encoding='utf-8')
            git(local,'add','README.md')
            git(local,'commit','-qm','physical stale README/claim mismatch')
            observed=integrated_case(local,'HEAD')
            self.assertTrue(any(x['id']=='S01' for x in observed['claim_to_implementation']['gaps']))
            self.assertFalse(observed['features']['all_behaviors_tested'])
            self.assertEqual(observed['authorization'],'NONE')
            git(local,'checkout','-q',self.sha)
            profile=local/'cora.type-assurance-profile.json'
            obj=json.loads(profile.read_text('utf-8'))
            obj['types'][0]['owner_source']='src/cora/ontology.py'
            profile.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
            git(local,'add','cora.type-assurance-profile.json')
            git(local,'commit','-qm','physical method-owner crosswalk substitution')
            with self.assertRaisesRegex(ValueError,'typed method owner/standards disconnected'):
                integrated_case(local,'HEAD')

    def test_seeded_semantic_fault_models_not_runtime_attestation(self):
        a=stress_integrated(32000,20261104)
        b=stress_integrated(32000,20261104)
        self.assertEqual(a,b)
        self.assertEqual(len(FAULTS),32)
        self.assertEqual(len(DIMENSIONS),12)
        self.assertEqual(a['positive'],2000)
        self.assertEqual(a['negative'],30000)
        self.assertEqual(a['mismatches'],0)
        self.assertEqual(a['unsafe_promotions'],0)
        self.assertEqual(a['physical_source_mutants'],0)
        self.assertEqual(a['product'],'BLOCKED_EXTERNAL')
        with self.assertRaises(ValueError):
            stress_integrated(10000001)

if __name__=='__main__':
    unittest.main()
