"""CORA-on-CORA P0, finite model only; no self-certification."""
import copy, json, random, unittest
from pathlib import Path
from cora.reticulum import ordered_cut, assess_cut, MODEL, EXTERNAL
R=Path(__file__).resolve().parents[1]
P=R/'.cora/contracts/dod/self-governing-portable-development-v1.json'
LEAVES={f'L{i:02d}' for i in range(1,33)}
EXT={f'L{i:02d}' for i in (12,16,20,24,27,28,30,31,32)}
def validate(p):
    if (p.get('schema')!='cora-self-governing-portable-development/1' or
        p.get('authority')!='NONE' or p.get('product_go') is not False or
        p.get('release')!='HOLD' or p.get('global_status')!='OPEN' or
        p['baseline']['cora_main']!='23034955f84257839ad83468a58234dbf81c51dc' or
        p['baseline']['zip_has_git'] is not False or
        p['baseline']['target_runtime_tested'] is not False): raise ValueError('source/authority')
    n=p['nodes']; d={x['id']:x for x in n}
    if len(n)!=42 or len(d)!=42 or set(d)!=LEAVES|{f'G{i}' for i in range(1,9)}|{'G0','A0'}: raise ValueError('coverage')
    if d['A0']['depends_on']!=['G0'] or d['A0']['scope']!='EXTERNAL' or d['G0']['scope']!='EXTERNAL' or d['G0']['depends_on']!=[f'G{i}' for i in range(1,9)]: raise ValueError('global')
    for i in range(1,9):
        if d[f'G{i}']['depends_on']!=[f'L{j:02d}' for j in range(4*i-3,4*i+1)]: raise ValueError('and')
    for key in LEAVES:
        x=d[key]
        if (x['depends_on'] or x['scope']!=('EXTERNAL' if key in EXT else 'SOURCE') or
            x['status']!='OPEN' or 'ASSUMED_PASS' in x['oracle'] or len(x['oracle'])<20 or
            not x['owner'].startswith('src/cora/') or not (R/x['owner']).is_file()): raise ValueError('leaf')
    if len(ordered_cut(n,'A0'))!=42: raise ValueError('reticulum')
    if assess_cut(n,'A0',{k:MODEL for k in LEAVES-EXT})['status']!=EXTERNAL: raise ValueError('external')
    if len(p['golds'])!=12 or {x['id'] for x in p['golds']}!={f'GOLD{i:02d}' for i in range(1,13)}: raise ValueError('gold-count')
    for g in p['golds']:
        if (g['state']!='CANDIDATE_NOT_IMPLEMENTED' or g['transfer']!='SEMANTIC_NOT_CODE' or
            not (R/g['owner']).is_file() or g['leaf'] not in LEAVES or
            g['origin_url']!=f"https://github.com/Luke883i/iKant_EDU/pull/{g['origin_pr']}"): raise ValueError('gold')
    if len(p['phases'])!=7 or {x['id'] for x in p['phases']}!={f'P{i}' for i in range(7)}: raise ValueError('phases')
    all_leaves=[]
    for phase in p['phases']:
        i=int(phase['id'][1:]);all_leaves.extend(phase['leaves'])
        if phase['depends_on']!=([f'P{i-1}'] if i else []) or phase['status']!='OPEN': raise ValueError('phase')
    if len(all_leaves)!=32 or set(all_leaves)!=LEAVES: raise ValueError('phase-leaves')
    if (p['portability']['unprofiled_manifest_status']!='NOT_CONFIGURED_NOT_PASS' or
        p['portability']['must_not_write_target_root'] is not True or
        any(v is not False for v in p['nonpromotion'].values()) or
        p['minimality']['new_parallel_graph_engine']!='FORBIDDEN' or
        p['minimality']['reuse_existing_owner']!='REQUIRED' or
        p['science']['status']!='NOT_RUN' or p['science']['claimed_causal_benefit'] is not False or
        p['science']['effort_ratio_hypothesis']!=0.8 or
        p['mutation_campaign']['kind']!='FINITE_CONTRACT_MODEL_NOT_RUNTIME' or
        p['mutation_campaign']['physical_runtime_mutants']!=0): raise ValueError('promotion')
    return True
class ContractTests(unittest.TestCase):
    def test_semantic_contract_and_kernel(self):
        self.assertTrue(validate(json.loads(P.read_text())))
    def test_ten_thousand_deterministic_fault_injections(self):
        p=json.loads(P.read_text());rng=random.Random(25120261118)
        for i in range(100):
            q=copy.deepcopy(p);rng.shuffle(q['nodes']);rng.shuffle(q['golds']);rng.shuffle(q['phases'])
            self.assertTrue(validate(q),'valid metamorphic control')
        results=[0]*10
        for family in range(10):
            for i in range(1000):
                q=copy.deepcopy(p)
                if family==0:q['authority']=f'AUTO_AUTH_{i}'
                elif family==1:q['product_go']=True;q['global_status']=f'GREEN_{i}'
                elif family==2:q['release']=f'RELEASE_{i}'
                elif family==3:q['baseline']['cora_main']=f'{i+1:040x}'
                elif family==4:q['nodes'][1]['depends_on'][i%8]=f'FORGED_{i}'
                elif family==5:
                    x=next(x for x in q['nodes'] if x['id']==sorted(EXT)[i%len(EXT)])
                    x['scope']='SOURCE';x['owner']=f'src/cora/forged_{i}.py'
                elif family==6:
                    x=next(x for x in q['nodes'] if x['id']==f'L{1+i%32:02d}')
                    x['oracle']=f'ASSUMED_PASS_{i}'
                elif family==7:q['golds'][i%12]['owner']=f'src/cora/nonexistent_{i}.py'
                elif family==8:q['phases'][i%7]['leaves'][0]=f'UNKNOWN_{i}'
                elif family==9:q['nonpromotion'][f'fake_external_pass_{i}']=True
                try:validate(q)
                except ValueError:results[family]+=1
        self.assertEqual(results,[1000]*10)
        print('CORA CONTRACT 10000/10000 synthetically rejected, 100 controls retained, runtime mutants 0, G0 HOLD')


class ExecutableP0Tests(unittest.TestCase):
    def test_exact_git_source_report_and_cli_replay(self):
        import tempfile
        from cora.continuous import self_development_plan, verify_self_development_plan
        from cora.cli import main
        report = self_development_plan(R)
        self.assertEqual(report['global_dod'], 'HOLD')
        self.assertEqual(report['assessment']['status'], 'BLOCKED_EXTERNAL')
        self.assertFalse(report['product_go'])
        self.assertEqual(report['local_obligations'], 32)
        self.assertTrue(verify_self_development_plan(R, report))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'plan.json'
            from unittest.mock import patch
            with patch('pathlib.Path.cwd', return_value=R):
                self.assertEqual(main(['convergence-plan', '--contract',
                                       str(P.relative_to(R)), '--output', str(path)]), 0)
            self.assertEqual(json.loads(path.read_text()), report)
            self.assertTrue(verify_self_development_plan(R, json.loads(path.read_text())))
        for field, forged in (('global_dod', 'PASS'), ('product_go', True),
                              ('contract_blob', '0' * 40), ('authority', 'RELEASE_MANAGER'),
                              ('report_digest', '0' * 64)):
            fake = copy.deepcopy(report)
            fake[field] = forged
            with self.assertRaises(ValueError, msg=field):
                verify_self_development_plan(R, fake)

    def test_physical_git_contract_mutations_are_not_promoted(self):
        import subprocess, tempfile
        from cora.continuous import self_development_plan
        base = json.loads(P.read_text())
        owners = sorted({x['owner'] for x in base['nodes'] if x.get('owner')}
                        | {x['owner'] for x in base['golds']})
        def git(repo, *args):
            return subprocess.check_output(['git', '-C', str(repo), *args],
                                           stderr=subprocess.PIPE).decode().strip()
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.name', 'P0 fixture')
            git(repo, 'config', 'user.email', 'p0@example.invalid')
            contract = repo / '.cora/contracts/dod/self-governing-portable-development-v1.json'
            contract.parent.mkdir(parents=True)
            contract.write_text(json.dumps(base))
            for owner in owners:
                path = repo / owner
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('# original owner stand-in, no target execution\n')
            git(repo, 'add', '.')
            git(repo, 'commit', '-qm', 'original P0 physical fixture')
            self.assertEqual(self_development_plan(repo)['global_dod'], 'HOLD')
            mutations = [
                lambda x: x.update(product_go=True),
                lambda x: x['nodes'][1].update(depends_on=['G1']),
                lambda x: x['golds'][0].update(owner='src/cora/unknown_owner.py'),
                lambda x: next(n for n in x['nodes'] if n['id']=='L12').update(scope='SOURCE'),
            ]
            for i, mutate in enumerate(mutations):
                changed = copy.deepcopy(base)
                mutate(changed)
                contract.write_text(json.dumps(changed))
                git(repo, 'add', '.')
                git(repo, 'commit', '-qm', f'physical negative {i}')
                with self.assertRaises(ValueError, msg=f'mutation {i}'):
                    self_development_plan(repo)
            contract.write_text(json.dumps(base))
            git(repo, 'add', '.')
            git(repo, 'commit', '-qm', 'original valid contract restored')
            self.assertEqual(self_development_plan(repo)['global_dod'], 'HOLD')
