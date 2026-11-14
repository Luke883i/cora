"""Bounded original CORA-engine product pilot: Git receipts, readback, tamper."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tools import hforge_profile as h
from cora.one_run import run_one


def git(root: Path,*args):
    p=subprocess.run(['git','-C',str(root),*args],text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout.strip()


def cli(*args):
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
    return subprocess.run([sys.executable,'-m','cora.cli',*map(str,args)],
            cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)


class NativeTargetEvidencePilot(unittest.TestCase):
    def test_git_snapshot_and_real_receipt_readback_then_forgery(self):
        with tempfile.TemporaryDirectory(prefix='hforge-native-pilot-') as tmp:
            repo=Path(tmp)/'target';repo.mkdir()
            git(repo,'init','-q');git(repo,'config','user.name','pilot')
            git(repo,'config','user.email','pilot@example.invalid')
            (repo/'component.py').write_text('def run(): return 1\n')
            git(repo,'add','component.py');git(repo,'commit','-qm','base')
            before=git(repo,'rev-parse','HEAD');p1=Path(tmp)/'ledger1.json'
            out=cli('snapshot',repo,'--revision',before,'--output',p1)
            self.assertEqual(out.returncode,0,out.stderr)
            self.assertEqual(cli('verify-ledger',p1,'--repo',repo).returncode,0)
            (repo/'component.py').write_text('def run(): return 2\n')
            git(repo,'add','component.py');git(repo,'commit','-qm','change')
            after=git(repo,'rev-parse','HEAD');p2=Path(tmp)/'ledger2.json'
            self.assertNotEqual(before,after)
            out=cli('snapshot',repo,'--revision',after,'--output',p2)
            self.assertEqual(out.returncode,0,out.stderr)
            self.assertNotEqual(p1.read_bytes(),p2.read_bytes())
            self.assertEqual(cli('verify-ledger',p2,'--repo',repo).returncode,0)
            # A historical Git witness stays bound to its old commit.
            self.assertEqual(cli('verify-ledger',p1,'--repo',repo).returncode,0)
            d=json.loads(p2.read_text());d['commit']=before
            forged=Path(tmp)/'forged.json';forged.write_text(json.dumps(d))
            rejected=cli('verify-ledger',forged,'--repo',repo)
            self.assertNotEqual(rejected.returncode,0,
                                'forged cross-revision receipt accepted')

    def test_source_onerun_native_replayer_rejects_self_authored_status(self):
        if not (ROOT/'.git').exists():
            self.skipTest('Git history required')
        r=run_one(ROOT,revision='HEAD',max_commits=8)
        w=h.verify_one_run_native(ROOT,r)
        self.assertEqual(w['scope'],'REPLAYED_ORIGINAL_SOURCE_ONERUN_NOT_RUNTIME_PRODUCT')
        self.assertEqual(w['product_status'],'BLOCKED_EXTERNAL')
        modified=dict(r);modified['source_status']='PASS_UNBOUNDED'
        with self.assertRaises(ValueError):
            h.verify_one_run_native(ROOT,modified)


if __name__=='__main__':unittest.main()
