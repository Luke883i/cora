import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.graph import graph_from_commit, explain_path, modules_for
from cora.graph_stress import stress_graph, FAMILIES
from cora.ontology import validate_ontology


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name)
        git(self.repo,'init','-q');git(self.repo,'config','user.name','CORA Fixture');git(self.repo,'config','user.email','fixture@invalid.example')
        for d in ('apps/api','apps/worker','src/shared'):(self.repo/d).mkdir(parents=True)
        (self.repo/'apps/api/main.py').write_text('import shared.util\n__import__("plugins.dynamic")\n')
        (self.repo/'apps/worker/task.py').write_text('import shared.util\n')
        (self.repo/'src/shared/util.py').write_text('CONST=1\n')
        ontology={'schema':'cora-ontology/1','products':[{'id':'api','roots':['apps/api'],'entrypoints':['apps/api/main.py']},{'id':'worker','roots':['apps/worker'],'entrypoints':['apps/worker/task.py']}],'software':[{'id':'sharedlib','roots':['src/shared'],'product_ids':['api','worker']}]}
        (self.repo/'cora.ontology.json').write_text(json.dumps(ontology))
        git(self.repo,'add','.');git(self.repo,'commit','-qm','fixture')
    def tearDown(self):self.tmp.cleanup()
    def test_manual_oracle_expected_edges(self):
        g=graph_from_commit(self.repo)
        edge={(e['source'],e['target'],e['kind']) for e in g['edges']}
        expected={('file:apps/api/main.py','file:src/shared/util.py','static_import_candidate'),('file:apps/worker/task.py','file:src/shared/util.py','static_import_candidate'),('software:sharedlib','product:api','declared_implements_product'),('software:sharedlib','product:worker','declared_implements_product'),('product:api','file:apps/api/main.py','declared_entrypoint')}
        self.assertTrue(expected.issubset(edge))
        self.assertEqual(len([e for e in g['edges'] if e['kind']=='static_import_candidate']),2)
        self.assertIn('dynamic_import_unknown',{x['kind'] for x in g['findings']})
        self.assertEqual(g['coverage']['runtime'],'unsupported')
        self.assertTrue(explain_path(g,'product:api','file:src/shared/util.py')['reachable_in_declared_graph'])
    def test_clean_tree_not_part_of_snapshot(self):
        old=graph_from_commit(self.repo)
        (self.repo/'apps/api/main.py').write_text('import malicious.plugin\n')
        self.assertEqual(old,graph_from_commit(self.repo))
    def test_new_commit_changes_graph(self):
        old=graph_from_commit(self.repo)
        (self.repo/'src/shared/another.py').write_text('NEW=1\n')
        git(self.repo,'add','.');git(self.repo,'commit','-qm','new')
        self.assertNotEqual(old['graph_digest'],graph_from_commit(self.repo)['graph_digest'])
    def test_unreachable_is_not_delete_safe(self):
        g=graph_from_commit(self.repo)
        a=explain_path(g,'product:worker','file:apps/api/main.py')
        self.assertFalse(a['reachable_in_declared_graph'])
        self.assertIn('not safe deletion',a['caveat'])
    def test_no_ontology_rejected(self):
        (self.repo/'cora.ontology.json').unlink()
        git(self.repo,'add','-A');git(self.repo,'commit','-qm','remove')
        with self.assertRaises(ValueError):graph_from_commit(self.repo)
    def test_missing_reference_rejected(self):
        doc={'schema':'cora-ontology/1','products':[],'software':[{'id':'x','roots':['src/x'],'product_ids':['no-product']}]}
        with self.assertRaises(ValueError):validate_ontology(doc)
    def test_module_resolution_alias(self):
        self.assertIn('shared.util',modules_for('src/shared/util.py'))
    def test_graph_mutations_all(self):
        self.assertEqual(len(FAMILIES),24)
        self.assertEqual(stress_graph(seed=883,cases=5000)['mismatches'],0)
    def test_repeat_deterministic(self):
        self.assertEqual(stress_graph(seed=88,cases=1200),stress_graph(seed=88,cases=1200))

if __name__=='__main__':unittest.main()
