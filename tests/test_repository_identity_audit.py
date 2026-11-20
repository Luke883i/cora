import json
import tempfile
import unittest
from pathlib import Path
from cora.audit import audit, read_declarations
from cora.cli import main
from cora.mutations import stress, TEMPLATES

class PR01Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / 'apps' / 'alpha').mkdir(parents=True)
        (self.repo / 'apps' / 'alpha' / 'main.py').write_text('print(1)')
        (self.repo / 'apps' / 'beta').mkdir(parents=True)
        (self.repo / 'apps' / 'beta' / 'main.py').write_text('print(2)')
        self.declarations = {'products': [{'id':'alpha', 'root':'apps/alpha','entrypoints':['apps/alpha/main.py']}, {'id':'beta','root':'apps/beta','entrypoints':['apps/beta/main.py']}]}
    def tearDown(self): self.temp.cleanup()
    def test_determinism(self):
        self.assertEqual(audit(self.repo,self.declarations),audit(self.repo,self.declarations))
    def test_two_distinct_products(self):
        a = audit(self.repo,self.declarations)
        self.assertFalse(a['findings'])
        self.assertEqual({f['products'][0] for f in a['files']},{'alpha','beta'})
    def test_duplicate_entrypoint(self):
        d = {'products':[dict(p) for p in self.declarations['products']]}
        d['products'][1]['entrypoints']=['apps/alpha/main.py']
        self.assertIn('duplicate_entrypoint',{e['type'] for e in audit(self.repo,d)['findings']} if 'apps/alpha/main.py' in d['products'][0]['entrypoints'] else set())
    def test_nested_roots(self):
        d={'products':[{'id':'alpha','root':'apps/alpha'},{'id':'sub','root':'apps/alpha/sub'}]}
        self.assertIn('overlapping_product_roots',{e['type'] for e in audit(self.repo,d)['findings']})
    def test_missing_entrypoint(self):
        self.declarations['products'][0]['entrypoints']=['apps/alpha/gone.py']
        self.assertIn('missing_entrypoint',{e['type'] for e in audit(self.repo,self.declarations)['findings']})
    def test_symlink_unknown(self):
        (self.repo / 'link.py').symlink_to(self.repo / 'apps/alpha/main.py')
        self.assertIn('unresolved_symlink',{e['type'] for e in audit(self.repo,self.declarations)['findings']})
    def test_mutation_determinism(self):
        self.assertEqual(stress(seed=3,cases=1001),stress(seed=3,cases=1001))
    def test_all_mutation_families(self):
        self.assertEqual(len(TEMPLATES),20)
        self.assertEqual(stress(seed=883,cases=20000)['mismatches'],0)
    def test_cli_version(self): self.assertEqual(main(['version']),0)
    def test_invalid_escape(self):
        with self.assertRaises(ValueError): read_declarations(self.repo,'../escape')

if __name__=='__main__': unittest.main()
