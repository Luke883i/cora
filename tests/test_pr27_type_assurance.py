"""Bounded R2 structural qualification: real fixture Git objects and false-PASS mutants.

All fixtures are synthetic. No claim about target runtime, ISO conformance,
GitHub branch policy, or independent review follows from these tests.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('type_assurance',ROOT/'tools/verify_type_assurance.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
PROFILE=json.loads((ROOT/'.cora/contracts/profiles/type-assurance-profile.json').read_text('utf8'))


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE).decode().strip()


def fixture_atlas(profile):
    procedures={}
    for row in profile['types']:
        m=row['existing_method']
        if m not in procedures:
            procedures[m]={'id':m,'source':row['owner_source'],
                           'standards':[x for x in row['standards'] if x!='ISO_5055_2021']}
    return {'schema':'cora-method-atlas/1','authority':'NONE',
            'references':[x['id'] for x in profile['standards'] if x['id']!='ISO_5055_2021'],
            'procedures':list(procedures.values())}


def fixture_sources(profile):
    sources={}
    for row in profile['types']:
        sources.setdefault(row['owner_source'],set()).add(row['owner_symbol'])
    return {path:''.join(f'def {symbol}():\n    return None\n\n' for symbol in sorted(syms)).encode()
            for path,syms in sources.items()}


class TypeAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.profile=copy.deepcopy(PROFILE)
        self.atlas=fixture_atlas(self.profile)
        self.ontology={'schema':'cora-ontology/1',
            'products':[{'id':'cora'}],
            'software':[{'id':'cora-engine'},{'id':'cora-release-verification'}]}
        self.dod={'schema':'cora-method-synthesis-dod/1','authority':'NONE',
                  'external_status':'BLOCKED_EXTERNAL','nodes':[
                    {'id':id, 'depends_on':list(edges),
                     'scope':'EXTERNAL' if id in ('E01','E02','E03','E04','G_GOVERNED') else 'SOURCE'}
                    for id,edges in checker.EXPECTED_DOD_EDGES.items()]}
        self.sources=fixture_sources(self.profile)

    def validate(self,profile=None,atlas=None,sources=None,dod=None):
        def read(path):
            if path not in (sources or self.sources):
                raise ValueError('SOURCE_MISSING')
            return (sources or self.sources)[path]
        return checker.validate(profile if profile is not None else self.profile,
                                atlas if atlas is not None else self.atlas,
                                self.ontology,dod if dod is not None else self.dod,read)

    def test_closed_world_positive_is_not_a_release(self):
        result=self.validate()
        self.assertEqual((result['type_count'],result['upstream_method_count'],
                          result['reference_count'],result['quality_axis_count'],
                          result['code_durability_count']), (20,14,10,9,12))
        self.assertEqual(result['formal_standard_count'],3)
        self.assertEqual(result['external'],'BLOCKED_EXTERNAL')
        self.assertEqual(result['authorization'],'NONE')
        self.assertEqual(result['universal_completeness'],'UNSUPPORTED')

    def test_29_typed_mutant_families_fail_closed(self):
        families=[
            ('type-removed', lambda p,a,s,d:p['types'].pop()),
            ('type-duplicated',lambda p,a,s,d:p['types'].append(copy.deepcopy(p['types'][0]))),
            ('type-unknown',lambda p,a,s,d:p['types'][0].update(id='unregistered-object')),
            ('plane-unknown',lambda p,a,s,d:p['types'][0].update(plane='SUPERPLANE')),
            ('method-unknown',lambda p,a,s,d:p['types'][0].update(existing_method='new-scanner')),
            ('owner-source-diverged',lambda p,a,s,d:p['types'][0].update(owner_source='src/cora/fake.py')),
            ('owner-symbol-absent',lambda p,a,s,d:p['types'][0].update(owner_symbol='nonexistent')),
            ('standard-removed',lambda p,a,s,d:p['standards'].pop()),
            ('standard-duplicated',lambda p,a,s,d:p['standards'].append(copy.deepcopy(p['standards'][0]))),
            ('standard-false-url',lambda p,a,s,d:p['standards'][0].update(url='http://fake.example')),
            ('reference-kind-falsified',lambda p,a,s,d:next(x for x in p['standards'] if x['id']=='DORA_2026').update(kind='FORMAL_STANDARD')),
            ('type-standard-removed',lambda p,a,s,d:p['types'][0].update(standards=[])),
            ('method-new-unmapped',lambda p,a,s,d:a['procedures'].append({'id':'missing-mapped','source':'src/cora/a.py','standards':['NIST_CA7']})),
            ('quality-axis-erased',lambda p,a,s,d:p['quality_characteristics'].pop()),
            ('type-quality-unknown',lambda p,a,s,d:p['types'][0].update(quality=['new-quality'])) ,
            ('structural-axis-erased',lambda p,a,s,d:p['structural_quality_dimensions'].pop()),
            ('obligations-erased',lambda p,a,s,d:p['types'][0].update(obligations=[])),
            ('falsifier-erased',lambda p,a,s,d:p['types'][0].update(falsifier='')),
            ('type-false-pass',lambda p,a,s,d:p['types'][0].update(status='PASS')),
            ('code-invariant-missing',lambda p,a,s,d:p['durability_invariants'].pop()),
            ('code-invariant-promoted',lambda p,a,s,d:p['durability_invariants'][0].update(attestation='PASS')),
            ('code-invariant-owner',lambda p,a,s,d:p['durability_invariants'][0].update(type='bad-owner')),
            ('governed-gate-false-pass',lambda p,a,s,d:d.update(external_status='PASS')),
            ('qualification-false-pass',lambda p,a,s,d:p['qualification'].update(product='PASS')),
            ('saturation-false-cert',lambda p,a,s,d:p['bounded_saturation']['unsupported'].remove('ISO-conformance')),
            ('source-syntax-break',lambda p,a,s,d:s.update({p['types'][0]['owner_source']:b'def not python!!'})),
            ('method-dod-edge-removed',lambda p,a,s,d:next(x for x in d['nodes'] if x['id']=='G_GOVERNED')['depends_on'].remove('E01')),
            ('method-dod-external-promoted',lambda p,a,s,d:next(x for x in d['nodes'] if x['id']=='E01').update(scope='SOURCE')),
            ('owner-nested-fake-symbol',lambda p,a,s,d:s.update({p['types'][0]['owner_source']:b'def fake():\n    def snapshot():\n        return None\n'})),
        ]
        seen=[]
        for label,mutate in families:
            p,a,s,d=copy.deepcopy(self.profile),copy.deepcopy(self.atlas),copy.deepcopy(self.sources),copy.deepcopy(self.dod)
            mutate(p,a,s,d)
            with self.subTest(family=label):
                with self.assertRaises((ValueError,SyntaxError)):
                    self.validate(p,a,s,d)
            seen.append(label)
        self.assertEqual(len(seen),29)
        self.assertEqual(len(set(seen)),29)

    def test_real_git_commits_are_read_not_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=Path(directory)/'fixture'
            repo.mkdir()
            subprocess.run(['git','-C',str(repo),'init','-q'],check=True)
            git(repo,'config','user.name','Synthetic check')
            git(repo,'config','user.email','fixture@example.invalid')
            for path,data in self.sources.items():
                target=repo/path
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
            for path,obj in [('.cora/contracts/profiles/method-atlas.json',self.atlas),('cora.ontology.json',self.ontology),('.cora/contracts/dod/method-synthesis-dod.json',self.dod)]:
                target=repo/path
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text(json.dumps(obj),encoding='utf8')
            git(repo,'add','.')
            git(repo,'commit','-qm','baseline')
            baseline=git(repo,'rev-parse','HEAD')
            self.profile['base']['commit']=baseline
            (repo/'.cora/contracts/profiles/type-assurance-profile.json').write_text(json.dumps(self.profile),encoding='utf8')
            git(repo,'add','.')
            git(repo,'commit','-qm','install typed source model')
            good=git(repo,'rev-parse','HEAD')
            report=checker.verify_repo(repo,good)
            self.assertEqual(report['result'],'PASS_SCOPED_STRUCTURAL_MODEL')
            self.assertEqual(report['baseline'],baseline)
            (repo/'.cora/contracts/profiles/type-assurance-profile.json').write_text('{"uncommitted":"dirty"}',encoding='utf8')
            self.assertEqual(checker.verify_repo(repo,good),report)
            mutated=copy.deepcopy(self.profile)
            mutated['durability_invariants'][0]['attestation']='PASS'
            (repo/'.cora/contracts/profiles/type-assurance-profile.json').write_text(json.dumps(mutated),encoding='utf8')
            git(repo,'add','.')
            git(repo,'commit','-qm','physical git false-pass mutation')
            bad=git(repo,'rev-parse','HEAD')
            with self.assertRaisesRegex(ValueError,'INVARIANT_FALSE_PASS'):
                checker.verify_repo(repo,bad)
            self.assertEqual(checker.verify_repo(repo,good),report)
            altered=copy.deepcopy(mutated)
            altered['durability_invariants'][0]['attestation']='BLOCKED_EXTERNAL'
            altered['base']['commit']='0'*40
            (repo/'.cora/contracts/profiles/type-assurance-profile.json').write_text(json.dumps(altered),encoding='utf8')
            git(repo,'add','.')
            git(repo,'commit','-qm','physical git stale ancestor mutation')
            with self.assertRaisesRegex(ValueError,'BASE_NOT_ANCESTOR'):
                checker.verify_repo(repo,'HEAD')


    def test_full_original_repo_and_physical_owner_dod_mutants(self):
        if not (ROOT / '.git').is_dir():
            self.skipTest('full CORA Git checkout required; synthetic bundle cannot attest original source')
        baseline = checker.verify_repo(ROOT, 'HEAD')
        self.assertEqual(baseline['result'], 'PASS_SCOPED_STRUCTURAL_MODEL')
        self.assertEqual(baseline['external'], 'BLOCKED_EXTERNAL')
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / 'original-source-fixture'
            subprocess.run(['git','clone','--local','-q',str(ROOT),str(repo)],check=True)
            git(repo,'config','user.name','source negative witness')
            git(repo,'config','user.email','negative@example.invalid')
            git(repo,'checkout','-q',git(ROOT,'rev-parse','HEAD'))
            before = checker.verify_repo(repo, 'HEAD')
            self.assertEqual(before['profile_git_blob'],baseline['profile_git_blob'])
            owner = repo / 'src/cora/git_snapshot.py'
            text = owner.read_text(encoding='utf-8')
            self.assertIn('def snapshot(',text)
            owner.write_text(text.replace('def snapshot(', 'def renamed_snapshot(', 1),encoding='utf-8')
            git(repo,'add','src/cora/git_snapshot.py')
            git(repo,'commit','-qm','physical CORA owner-symbol mutant')
            with self.assertRaisesRegex(ValueError,'OWNER_SYMBOL_MISSING'):
                checker.verify_repo(repo,'HEAD')
            git(repo,'checkout','-q',git(ROOT,'rev-parse','HEAD'))
            dpath=repo/'.cora/contracts/dod/method-synthesis-dod.json'
            dod=json.loads(dpath.read_text(encoding='utf-8'))
            next(x for x in dod['nodes'] if x['id']=='G_GOVERNED')['depends_on'].remove('E01')
            dpath.write_text(json.dumps(dod,indent=2)+'\n',encoding='utf-8')
            git(repo,'add','.cora/contracts/dod/method-synthesis-dod.json')
            git(repo,'commit','-qm','physical CORA evidence-gate mutant')
            with self.assertRaisesRegex(ValueError,'METHOD_DOD_EDGE_OR_SCOPE_DRIFT'):
                checker.verify_repo(repo,'HEAD')

    def test_no_target_execution_or_unknown_promotion(self):
        source=(ROOT/'tools/verify_type_assurance.py').read_text('utf8')
        self.assertNotIn('subprocess.run([\'python\'',source)
        self.assertNotIn('exec(',source)
        self.assertNotIn('eval(',source)
        for name in ('runtime','review','host','product'):
            self.assertEqual(self.profile['qualification'][name],'BLOCKED_EXTERNAL')

if __name__ == '__main__':
    unittest.main()
