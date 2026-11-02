"""PR-06 actual Git worktree fixtures + independent expected policy outcomes."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.guard import install_guard
from cora.guard_runtime import verify
from cora.transform import plan_rename_docs, apply_rename_docs
from cora.transform_stress import decision_mutated, oracle_by_contract, stress_transform
from cora.cli import main


def g(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class RealGitTransformFixtures(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)
        g(self.repo,'init','-q');g(self.repo,'config','user.name','Fixture')
        g(self.repo,'config','user.email','fixture@invalid.example')
        (self.repo/'docs').mkdir()
        (self.repo/'docs/old.md').write_text('# Legacy\nuse docs/old.md\n')
        (self.repo/'README.md').write_text('Link docs/old.md and docs/old.md.\n')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','initial docs')
    def tearDown(self):self.temp.cleanup()
    def plan(self):return plan_rename_docs(self.repo,'docs/old.md','docs/new.md')
    def test_plan_deterministic(self):self.assertEqual(self.plan(),self.plan())
    def test_plan_never_changes_worktree(self):
        status=g(self.repo,'status','--porcelain')
        x=self.plan();self.assertEqual(x['edits'][0]['path'],'README.md')
        self.assertEqual(g(self.repo,'status','--porcelain'),status)
    def test_apply_updates_all_tracked_document_references(self):
        p=self.plan()
        receipt=apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=['python','-c',"import pathlib; assert pathlib.Path('docs/new.md').exists(); assert 'docs/old.md' not in pathlib.Path('README.md').read_text()"])
        self.assertEqual(receipt['status'],'SCOPED_APPLIED_TESTS_PASSED')
        self.assertFalse((self.repo/'docs/old.md').exists())
        self.assertIn('docs/new.md',(self.repo/'README.md').read_text())
        self.assertIn('docs/new.md',(self.repo/'docs/new.md').read_text())
    def test_test_failure_rollback(self):
        p=self.plan()
        before={x:(self.repo/x).read_bytes() for x in ('README.md','docs/old.md')}
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=['python','-c','raise SystemExit(42)'])
        self.assertEqual(before,{x:(self.repo/x).read_bytes() for x in before})
        self.assertFalse((self.repo/'docs/new.md').exists())
        self.assertEqual(g(self.repo,'status','--porcelain'),'')
    def test_missing_verification_command_blocks(self):
        p=self.plan()
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=[])
    def test_approval_mismatch_blocks(self):
        p=self.plan()
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval='forged',test_command=['python','-c','print(1)'])
    def test_reforged_plan_rejected(self):
        p=self.plan();p['edits'][0]['before_sha256']='0'*64
        from cora.evidence import domain_hash
        p['plan_digest']=domain_hash('CORA:transform-plan:1',{k:v for k,v in p.items() if k!='plan_digest'})
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=['python','-c','print(1)'])
    def test_stale_plan_after_new_commit_blocks(self):
        p=self.plan();(self.repo/'README.md').write_text('something new')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','new commit')
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=['python','-c','print(1)'])
    def test_dirty_worktree_blocks(self):
        (self.repo/'README.md').write_text('dirty')
        with self.assertRaises(ValueError):self.plan()
    def test_binary_references_block(self):
        (self.repo/'app.bin').write_bytes(b'\x00docs/old.md\x00')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','binary')
        with self.assertRaises(ValueError):self.plan()
    def test_code_references_block(self):
        (self.repo/'main.py').write_text("print('docs/old.md')\n")
        g(self.repo,'add','.');g(self.repo,'commit','-qm','code reference')
        with self.assertRaises(ValueError):self.plan()
    def test_symlink_source_blocks(self):
        (self.repo/'docs/old.md').unlink();(self.repo/'docs/old.md').symlink_to('/etc/passwd')
        g(self.repo,'add','-A');g(self.repo,'commit','-qm','symlink')
        with self.assertRaises(ValueError):self.plan()
    def test_destination_collision_blocks(self):
        (self.repo/'docs/new.md').write_text('collision')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','dest')
        with self.assertRaises(ValueError):self.plan()
    def test_unexpected_test_side_effect_rolls_back_owned_paths(self):
        p=self.plan()
        with self.assertRaises(ValueError):apply_rename_docs(self.repo,p,approval=p['plan_digest'],test_command=['python','-c',"import pathlib; pathlib.Path('unowned.txt').write_text('side effect')"])
        self.assertTrue((self.repo/'docs/old.md').exists())
        self.assertFalse((self.repo/'docs/new.md').exists())
        # This side effect is intentionally NOT claimed to be rolled back by CORA.
        self.assertTrue((self.repo/'unowned.txt').exists())
    def test_verifier_modification_of_postimage_is_rejected(self):
        p=self.plan()
        with self.assertRaises(ValueError):
            apply_rename_docs(self.repo,p,approval=p['plan_digest'],
                test_command=['python','-c',"import pathlib; pathlib.Path('README.md').write_text('tampered')"])
        self.assertEqual((self.repo/'README.md').read_text(), 'Link docs/old.md and docs/old.md.\n')
        self.assertTrue((self.repo/'docs/old.md').exists())
    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as outside:
            p=Path(outside)/'plan.json';r=Path(outside)/'receipt.json'
            self.assertEqual(main(['plan-rename-doc',str(self.repo),'--old','docs/old.md','--new','docs/new.md','--output',str(p)]),0)
            plan=json.loads(p.read_text())
            self.assertEqual(main(['apply-rename-doc',str(self.repo),'--plan',str(p),'--approve',plan['plan_digest'],'--test-command','python -c "assert True"','--output',str(r)]),0)
            self.assertTrue(r.exists())


class LocalGuardFixtures(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)
        g(self.repo,'init','-q');g(self.repo,'config','user.name','Fixture')
        g(self.repo,'config','user.email','fixture@invalid.example')
        for folder in ('apps/alpha','apps/beta'):
            (self.repo/folder).mkdir(parents=True)
        (self.repo/'apps/alpha/main.py').write_text('VALUE=1\n')
        (self.repo/'apps/beta/core.py').write_text('VALUE=2\n')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','initial')
        install_guard(self.repo,['alpha=apps/alpha=apps.alpha','beta=apps/beta=apps.beta'])
        g(self.repo,'add','.');g(self.repo,'commit','-qm','install guard')
        self.base=g(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.temp.cleanup()
    def test_guard_clean(self):self.assertEqual(verify(self.repo,self.base)['status'],'PASS_SCOPED')
    def test_cross_product_import_blocks(self):
        (self.repo/'apps/alpha/main.py').write_text('import apps.beta.core\n')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','cross import')
        self.assertIn('cross_product_import',{x['kind'] for x in verify(self.repo,self.base)['violations']})
    def test_dynamic_import_blocks(self):
        (self.repo/'apps/alpha/main.py').write_text("__import__('apps.beta.core')\n")
        g(self.repo,'add','.');g(self.repo,'commit','-qm','dynamic')
        self.assertIn('dynamic_import_unknown',{x['kind'] for x in verify(self.repo,self.base)['violations']})
    def test_relative_import_blocks(self):
        (self.repo/'apps/alpha/main.py').write_text('from . import util\n')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','relative')
        self.assertIn('relative_import_unknown',{x['kind'] for x in verify(self.repo,self.base)['violations']})
    def test_guard_self_edit_blocks(self):
        p=self.repo/'.cora/policy.json';d=json.loads(p.read_text());d['exceptions']=['self-approve'];p.write_text(json.dumps(d))
        g(self.repo,'add','.');g(self.repo,'commit','-qm','policy bypass')
        # Runtime raises fail-closed for unsupported exceptions before paths analysis.
        with self.assertRaises(ValueError):verify(self.repo,self.base)
    def test_guard_source_change_blocks(self):
        p=self.repo/'.cora/verify.py';p.write_text(p.read_text()+'\n# bypass\n')
        g(self.repo,'add','.');g(self.repo,'commit','-qm','guard edit')
        self.assertIn('guard_or_workflow_changed',{x['kind'] for x in verify(self.repo,self.base)['violations']})
    def test_cross_product_rename_blocks(self):
        g(self.repo,'mv','apps/alpha/main.py','apps/beta/main.py')
        g(self.repo,'commit','-qm','cross move')
        self.assertIn('cross_product_move',{x['kind'] for x in verify(self.repo,self.base)['violations']})
    def test_standalone_guard_executes(self):
        p=subprocess.run(['python',str(self.repo/'.cora/verify.py'),'--repo',str(self.repo),'--base',self.base],capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_guard_rejects_dirty_worktree(self):
        (self.repo/'apps/alpha/main.py').write_text('uncommitted')
        with self.assertRaises(ValueError):verify(self.repo,self.base)
    def test_missing_policy_fails_closed(self):
        (self.repo/'.cora/policy.json').unlink()
        with self.assertRaises(ValueError):verify(self.repo,self.base)
    def test_no_guard_overwrite(self):
        with self.assertRaises(ValueError):install_guard(self.repo,['alpha=apps/alpha=apps.alpha'])
    def test_installer_rejects_overlapping_roots(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td);g(x,'init','-q');g(x,'config','user.name','Fixture');g(x,'config','user.email','fixture@invalid.example')
            (x/'README.md').write_text('ok');g(x,'add','.');g(x,'commit','-qm','base')
            with self.assertRaises(ValueError):install_guard(x,['a=apps=apps','b=apps/b=b'])


class StressRules(unittest.TestCase):
    def test_oracle_edge_states(self):
        for n in range(1<<16):
            self.assertEqual(decision_mutated(n)[0],oracle_by_contract(n))
    def test_1m_unique_at_small_scale(self):
        v=stress_transform(seed=883,cases=5000)
        self.assertEqual((v['distinct_risk_vectors'],v['mismatches']), (5000,0))
    def test_invalid(self):
        with self.assertRaises(ValueError):stress_transform(cases=1000001)

if __name__=='__main__':unittest.main()
