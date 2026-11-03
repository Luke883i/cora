"""Adversarial Git fixtures for CORA PR-12 archaeology, groups and AI."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.archaeology import mine_history,verify_history
from cora.holistic import holistic_audit,verify_holistic,_coupling_groups
from cora.group_hypotheses import annotate_groups
from cora.evidence import domain_hash
from cora.archaeology_stress import stress_archaeology,model_flags,oracle_by_boolean_contract
from cora.cli import main


def git(repo,*a):
    return subprocess.check_output(['git','-C',str(repo),*a],stderr=subprocess.STDOUT).decode().strip()


class HistoryFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=Path(self.tmp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.name','Fixture');git(self.repo,'config','user.email','fixture@invalid.example')
        for p in ('src/p','src/q','docs','tests'):(self.repo/p).mkdir(parents=True)
        (self.repo/'src/p/main.py').write_text('import p.util\n')
        (self.repo/'src/p/util.py').write_text('VALUE=1\n')
        (self.repo/'src/p/scaffold.py').write_text('EXAMPLE=True\n')
        (self.repo/'src/q/other.py').write_text('VALUE=2\n')
        (self.repo/'docs/gold.md').write_text('Authoritative product contract\n')
        (self.repo/'tests/test_gold.py').write_text('def test_keep(): assert True\n')
        (self.repo/'cora.ontology.json').write_text(json.dumps({
            'schema':'cora-ontology/1','products':[
              {'id':'p','roots':['src/p'],'entrypoints':['src/p/main.py']},
              {'id':'q','roots':['src/q'],'entrypoints':['src/q/other.py']}],
            'software':[{'id':'engine','roots':['src/p'],'product_ids':['p']}]}))
        (self.repo/'cora.artifact-roles.json').write_text(json.dumps({
            'schema':'cora-artifact-roles/1','rules':[
              {'pattern':'src/p/main.py','roles':['ENTRYPOINT','SOFTWARE_SOURCE'],'rationale':'Declared product entrypoint for integration.'},
              {'pattern':'src/p/util.py','roles':['SOFTWARE_SOURCE'],'rationale':'Declared shared implementation path.'},
              {'pattern':'src/q/other.py','roles':['SOFTWARE_SOURCE'],'rationale':'Distinct product implementation path.'},
              {'pattern':'docs/gold.md','roles':['PRODUCT_CONTRACT'],'rationale':'Documented important business contract.'},
              {'pattern':'tests/*','roles':['TEST'],'rationale':'Declared repository test fixtures.'}]}))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','feat(core): baseline')
        for i in (2,3):
            (self.repo/'src/p/main.py').write_text('import p.util\nN='+str(i)+'\n')
            (self.repo/'src/p/util.py').write_text('VALUE='+str(i)+'\n')
            git(self.repo,'add','.');git(self.repo,'commit','-qm','feat(core): iteration '+str(i))
        (self.repo/'src/p/scaffold.py').rename(self.repo/'src/p/scaffold_v2.py')
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','refactor(core): rename scaffold')
        self.head=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.tmp.cleanup()

    def test_history_commits_rename_replay(self):
        h=mine_history(self.repo)
        self.assertEqual(len(h['events']),4)
        self.assertTrue(any(x['status'].startswith('R') for e in h['events'] for x in e['changes']))
        self.assertTrue(verify_history(self.repo,h))
    def test_two_distinct_commit_cochange(self):
        h=mine_history(self.repo)
        self.assertTrue(any(x['count']>=2 and x['a']=='src/p/main.py' and x['b']=='src/p/util.py' for x in h['cochange_pairs']))
    def test_ambiguous_history_budget_is_reported(self):
        self.assertTrue(mine_history(self.repo,max_commits=1)['history_truncated'])
    def test_pr_id_is_unverified_metadata(self):
        h=mine_history(self.repo,pr_index={'schema':'cora-pr-index/1','commits':{self.head:123}})
        self.assertEqual(h['events'][0]['pr_association'],'PR-123')
        self.assertEqual(h['events'][0]['pr_association_source'],'operator_supplied_unverified')
    def test_gold_scaffold_are_not_deletion_authority(self):
        r=holistic_audit(self.repo)
        files={x['path']:x for x in r['files']}
        self.assertIn('POSSIBLE_UNCONNECTED_GOLD_REVIEW',files['docs/gold.md']['review_flags'])
        self.assertIn('POSSIBLE_SCAFFOLD_WASTE_REVIEW',files['src/p/scaffold_v2.py']['review_flags'])
        self.assertTrue(all(not x['safe_to_delete'] for x in r['files']))
        self.assertTrue(verify_holistic(self.repo,r))
    def test_dirty_tree_does_not_change_committed_result(self):
        r=holistic_audit(self.repo)
        (self.repo/'src/p/main.py').write_text('UNCOMMITTED=True\n')
        self.assertEqual(r,holistic_audit(self.repo))
    def test_reforged_source_report_fails(self):
        r=holistic_audit(self.repo)
        r['files'][0]['safe_to_delete']=True
        r['report_digest']=domain_hash('CORA:holistic:1',{k:v for k,v in r.items() if k!='report_digest'})
        with self.assertRaises(ValueError):verify_holistic(self.repo,r)
    def test_ai_grounding_does_not_authorize(self):
        r=holistic_audit(self.repo)
        g=r['development_groups'][0]
        h={'schema':'cora-group-hypotheses/1','report_digest':r['report_digest'],'hypotheses':[
          {'group_id':g['id'],'hypothesis':'This might be dormant but is not proven unused.',
           'action':'PROPOSE_QUARANTINE','evidence_refs':['file:'+g['paths'][0],'file:nonexistent.py'],
           'counterevidence':['Consumer unknown'],'confidence_range':[0.2,0.95]}]}
        x=annotate_groups(self.repo,r,h)
        self.assertEqual(x['hypotheses'][0]['authorized_action'],'NONE')
        self.assertEqual(x['hypotheses'][0]['grounding_status'],'INSUFFICIENT_REFERENCES')
    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'full.json'
            self.assertEqual(main(['holistic-audit',str(self.repo),'--max-commits','20','--output',str(out)]),0)
            self.assertEqual(main(['verify-holistic',str(out),'--repo',str(self.repo)]),0)
    def test_truncated_history_cannot_prove_scaffold_age(self):
        report=holistic_audit(self.repo,max_commits=1)
        row=next(x for x in report['files'] if x['path']=='src/p/scaffold_v2.py')
        self.assertIn('HISTORY_WINDOW_TRUNCATED_UNKNOWN_LINEAGE',row['review_flags'])
        self.assertNotIn('POSSIBLE_SCAFFOLD_WASTE_REVIEW',row['review_flags'])
    def test_focus_paths_cannot_escape(self):
        with self.assertRaises(ValueError):holistic_audit(self.repo,focus='../escape.py')


class GroupPolicyFixture(unittest.TestCase):
    def test_temporal_edge_never_means_runtime_call(self):
        groups,edges=_coupling_groups(['p.py','q.py'],[{'a':'p.py','b':'q.py','count':2}],
          {'p.py':['a','b'],'q.py':['a','b']},{'p.py':('one',),'q.py':('two',)})
        self.assertEqual(len(groups),2)
        self.assertEqual(edges[0]['kind'],'HISTORICAL_ASSOCIATION_NOT_RUNTIME_EDGE')
    def test_unowned_bridge_cannot_merge_distinct_products(self):
        groups,_=_coupling_groups(['a.py','bridge.py','b.py'],
          [{'a':'a.py','b':'bridge.py','count':2},{'a':'bridge.py','b':'b.py','count':2}],
          {'a.py':['1','2'],'bridge.py':['1','2'],'b.py':['1','2']},
          {'a.py':('p',),'bridge.py':(),'b.py':('q',)})
        self.assertEqual(len(groups),2)
    def test_same_product_can_cluster(self):
        groups,_=_coupling_groups(['a.py','b.py'],[{'a':'a.py','b':'b.py','count':2}],
          {'a.py':['c','d'],'b.py':['c','d']},{'a.py':('p',),'b.py':('p',)})
        self.assertEqual(groups,[['a.py','b.py']])
    def test_independent_oracle_and_repeat(self):
        for m in range(4096):
            self.assertEqual(model_flags(m),oracle_by_boolean_contract(m))
        a=stress_archaeology(seed=883,cases=2000)
        self.assertEqual(a,stress_archaeology(seed=883,cases=2000))
        self.assertEqual(a['mismatches'],0)

if __name__=='__main__':unittest.main()
