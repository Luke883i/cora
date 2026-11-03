"""Independent committed-Git debt sources, adverse SARIF and safe process tests."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.debt import debt_scan, verify_debt, compare_debt, parse_sarif
from cora.process_suite import run_suite, verify_suite, process_catalog
from cora.debt_stress import stress_debt, model_triage, oracle_spec
from cora.evidence import domain_hash
from cora.cli import main


def g(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.STDOUT).decode().strip()


class GitDebtFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        g(self.root,'init','-q');g(self.root,'config','user.email','fixture@invalid.example')
        g(self.root,'config','user.name','Independent Fixture')
        for p in ('src/a','src/b','docs'):(self.root/p).mkdir(parents=True)
        (self.root/'src/a/main.py').write_text('from . import massive\n')
        (self.root/'src/a/massive.py').write_text(self.heavy(1))
        (self.root/'src/b/worker.py').write_text('pass\n')
        (self.root/'docs/contract.md').write_text('Business contract must remain available.\n')
        (self.root/'cora.ontology.json').write_text(json.dumps({'schema':'cora-ontology/1','products':[
          {'id':'a','roots':['src/a'],'entrypoints':['src/a/main.py']},
          {'id':'b','roots':['src/b'],'entrypoints':['src/b/worker.py']}],
          'software':[{'id':'engine','roots':['src/a'],'product_ids':['a']}]}))
        (self.root/'cora.artifact-roles.json').write_text(json.dumps({'schema':'cora-artifact-roles/1','rules':[
          {'pattern':'src/a/main.py','roles':['ENTRYPOINT','SOFTWARE_SOURCE'],'rationale':'Explicit committed application entrypoint.'},
          {'pattern':'src/b/worker.py','roles':['SOFTWARE_SOURCE'],'rationale':'Explicit second product implementation.'},
          {'pattern':'docs/*','roles':['PRODUCT_CONTRACT'],'rationale':'Important normative product specifications.'}]}))
        g(self.root,'add','.');g(self.root,'commit','-qm','feat: fixture baseline')
        self.base=g(self.root,'rev-parse','HEAD')
        for i in range(2,8):
            (self.root/'src/a/massive.py').write_text(self.heavy(i))
            g(self.root,'add','.');g(self.root,'commit','-qm',f'feat: exercise hotspot {i}')
        self.head=g(self.root,'rev-parse','HEAD')
    @staticmethod
    def heavy(counter):
        return 'def f(n):\n'+''.join('    if n == %d: return %d\n'%(n,n) for n in range(24))+f'    return {counter}\n'
    def tearDown(self):self.tmp.cleanup()
    def sarif(self,uri='src/a/massive.py',level='error'):
        return json.dumps({'version':'2.1.0','runs':[{'tool':{'driver':{'name':'CheckTool'}},'results':[
          {'ruleId':'security/CWE-79','level':level,'message':{'text':'Claim, not verified'},
           'locations':[{'physicalLocation':{'artifactLocation':{'uri':uri},'region':{'startLine':4}}}]}]}]}).encode()

    def test_structural_signal_with_source_proof(self):
        r=debt_scan(self.root,max_commits=16)
        self.assertTrue(any(f['kind']=='CODE_COMPLEXITY' and f['path']=='src/a/massive.py' for f in r['findings']))
        self.assertTrue(any(f['kind']=='CHANGE_PRESSURE' for f in r['findings']))
        self.assertTrue(verify_debt(self.root,r))
    def test_role_missing_is_coverage_not_dead_code(self):
        r=debt_scan(self.root,max_commits=16)
        hits=[f for f in r['findings'] if f['path']=='src/a/massive.py' and f['kind']=='EVIDENCE_COVERAGE']
        self.assertTrue(hits)
        self.assertTrue(all(f['authorized_action']=='NONE' for f in r['findings']))
    def test_dirty_tree_does_not_affect_pinned_report(self):
        r=debt_scan(self.root,max_commits=8)
        (self.root/'src/a/massive.py').write_text('raise RuntimeError("should not run")\n')
        self.assertEqual(r,debt_scan(self.root,max_commits=8))
    def test_reforged_self_digest_rejected(self):
        r=debt_scan(self.root,max_commits=4)
        r['findings'][0]['authorized_action']='DELETE'
        r['report_digest']=domain_hash('CORA:debt-ledger:1',{k:v for k,v in r.items() if k!='report_digest'})
        with self.assertRaises(ValueError): verify_debt(self.root,r)
    def test_external_sarif_never_authorizes(self):
        raw=self.sarif()
        r=debt_scan(self.root,max_commits=5,sarif_bytes=raw)
        found=[x for x in r['findings'] if x['evidence_strength']=='EXTERNAL_UNVERIFIED']
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['kind'],'SECURITY_FINDING')
        self.assertEqual(found[0]['authorized_action'],'NONE')
        self.assertTrue(verify_debt(self.root,r,sarif_bytes=raw))
    def test_sarif_missing_replay_rejected(self):
        r=debt_scan(self.root,max_commits=3,sarif_bytes=self.sarif())
        with self.assertRaises(ValueError):verify_debt(self.root,r)
    def test_sarif_foreign_input_rejected(self):
        r=debt_scan(self.root,max_commits=3,sarif_bytes=self.sarif())
        with self.assertRaises(ValueError):verify_debt(self.root,r,sarif_bytes=self.sarif(level='note'))
    def test_malformed_sarif_objects_fail_closed(self):
        raw=self.sarif()
        doc=json.loads(raw)
        examples=[]
        v=json.loads(raw);v['runs'][0]['tool']=[];examples.append(v)
        v=json.loads(raw);v['runs'][0]['results'][0]['message']=[];examples.append(v)
        v=json.loads(raw);v['runs'][0]['results'][0]['locations'][0]['physicalLocation']['region']=[];examples.append(v)
        for instance in examples:
            with self.subTest(instance=instance['runs'][0]),self.assertRaises(ValueError):
                parse_sarif(json.dumps(instance).encode(),{'src/a/massive.py'})
    def test_full_process_reuses_same_commit_evidence(self):
        suite=run_suite(self.root,process='full',max_commits=3,focus='src/a/main.py')
        reused=[r for r in suite['results'] if r['status']=='REUSED_SCOPED_FROM_HOLISTIC']
        self.assertGreaterEqual(len(reused),4)
        self.assertTrue(verify_suite(self.root,suite))

    def test_sarif_path_escape_rejected(self):
        for p in ('../etc/passwd','/tmp/secret.py','https://bad.invalid/x.py','src/%2e%2e/x.py'):
            with self.subTest(p=p),self.assertRaises(ValueError):parse_sarif(self.sarif(uri=p),{'src/a/massive.py'})
    def test_unknown_sarif_path_visible(self):
        r=parse_sarif(self.sarif(uri='src/a/not-tracked.py'),{'src/a/massive.py'})
        self.assertEqual(r['rows'],[])
        self.assertIn('SARIF_PATH_NOT_IN_COMMIT:src/a/not-tracked.py',r['unknown'])
    def test_diff_is_detection_not_resolution_proof(self):
        r=compare_debt(self.root,self.base,self.head,max_commits=4)
        self.assertEqual(r['resolution_claim'],'NOT_PROVEN_ONLY_DETECTION_DELTA')
        self.assertEqual(r['authorized_action'],'NONE')
    def test_process_names_and_safe_exclusions(self):
        cat=process_catalog()
        self.assertEqual(len(cat['processes']),7)
        self.assertIn('target_test_execution',cat['excluded_unsafe_methods'])
    def test_independent_single_source_process(self):
        r=run_suite(self.root,process='source',max_commits=4)
        self.assertEqual(r['status'],'PASS_SCOPED_WITH_UNVERIFIED_GAPS')
        self.assertTrue(verify_suite(self.root,r))
        self.assertNotIn('debt_signals',[x['method'] for x in r['results']])
    def test_all_in_one_no_execution(self):
        r=run_suite(self.root,process='full',max_commits=3,focus='src/a/main.py')
        self.assertIn(r['status'],('PASS_SCOPED_WITH_UNVERIFIED_GAPS','DEBT_BLOCKED'))
        self.assertEqual(r['authorized_action'],'NONE')
        self.assertIn('debt_signals',[x['method'] for x in r['results']])
        self.assertNotIn('target_test_execution',[x['method'] for x in r['results']])
        self.assertTrue(verify_suite(self.root,r))
    def test_fake_process_status_fails_replay(self):
        r=run_suite(self.root,process='history',max_commits=3)
        r['results'][0]['status']='FABRICATED_PASS'
        r['run_digest']=domain_hash('CORA:process-run:1',{k:v for k,v in r.items() if k!='run_digest'})
        with self.assertRaises(ValueError):verify_suite(self.root,r)
    def test_cli_debt_full_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'report.json'
            self.assertEqual(main(['debt-scan',str(self.root),'--max-commits','3','--output',str(out)]),0)
            self.assertEqual(main(['verify-debt',str(out),'--repo',str(self.root)]),0)
    def test_cli_suite_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run.json'
            self.assertEqual(main(['process-run',str(self.root),'--process','history','--max-commits','3','--output',str(out)]),0)
            self.assertEqual(main(['verify-process',str(out),'--repo',str(self.root)]),0)
    def test_code_file_not_run_during_scanning(self):
        (self.root/'src/a/main.py').write_text('raise RuntimeError("never execute me")\n')
        g(self.root,'add','.');g(self.root,'commit','-qm','adversarial code')
        self.assertEqual(debt_scan(self.root,max_commits=3)['commit'],g(self.root,'rev-parse','HEAD'))


class ModelFalsification(unittest.TestCase):
    def test_4096_oracle_cases(self):
        for family in range(24):
            for bits in range(4096):
                self.assertEqual(model_triage(bits,family),oracle_spec(bits,family))
    def test_reproducible_4096(self):
        a=stress_debt(seed=883,cases=4096)
        self.assertEqual(a,stress_debt(seed=883,cases=4096))
        self.assertEqual((a['cases'],a['distinct_input_masks'],a['mismatches']),(4096,4096,0))
    def test_invalid_case_counts(self):
        with self.assertRaises(ValueError):stress_debt(cases=1_000_001)

if __name__=='__main__':unittest.main()
