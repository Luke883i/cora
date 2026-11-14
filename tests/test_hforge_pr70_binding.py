"""Real Git-anchored PR70 atlas/shape anti-forgery tests, no native execution."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from cora import hforge_profile as h
from tools import verify_operational_equivalence as op


def git(*args: str) -> str:
    return subprocess.check_output(['git', '-C', str(ROOT), *args],text=True).strip()


def fake_report(base: str, head: str) -> dict:
    cases, contract = op.universe(ROOT, base, head)
    okay = hashlib.sha256(b'ok\n').hexdigest()
    empty = hashlib.sha256(b'').hexdigest()
    obs = {'exit_code':0, 'stdout_sha256':okay,'stdout_bytes':3,
           'stderr_sha256':empty,'stderr_bytes':0}
    return {
        'schema':h.OP_SCHEMA, 'base':base, 'head':head,
        'manifest_sha256': hashlib.sha256(json.dumps(contract,sort_keys=True,
           separators=(',',':')).encode()).hexdigest(),
        'universe':'ALL_DECLARED_71_CLI_HELP_PLUS_6_NATIVE_OPERATIONS',
        'independent_reviewer':'NOT_ATTESTED',
        'denominator':77, 'observed':77, 'passed':77, 'failed':[],
        'rows':[{'case':c, 'status':'PASS', 'baseline':copy.deepcopy(obs),
                 'candidate':copy.deepcopy(obs)} for c in cases],
        'status':'PASS_EXHAUSTIVE_FINITE_OBSERVATIONS',
        'authorization':'NONE', 'product_global_status':'BLOCKED_EXTERNAL',
    }


class RealAtlasBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'.git').exists():
            raise unittest.SkipTest('requires Git checkout and PR70 committed atlas')
        cls.head = git('rev-parse', 'HEAD')
        cls.base = git('rev-parse', 'HEAD^')
        try:
            op.universe(ROOT,cls.base,cls.head)
        except Exception as exc:
            raise unittest.SkipTest(f'PR70 native universe not available: {exc}')

    def test_source_atlas_bind_does_not_upgrade_native_evidence(self):
        d = fake_report(self.base, self.head)
        binding = h.bind_pr70_universe(ROOT,d,base=self.base,head=self.head)
        self.assertEqual(binding['cases'],77)
        self.assertEqual(binding['authority'],'NONE')
        self.assertIn('NOT_RUNTIME_REPLAY',binding['scope'])
        cut = h.qualified_local_cut(ROOT,d,base=self.base,head=self.head)
        self.assertEqual(cut['gates']['P1'],'PASS_SOURCE_ATLAS_BOUND_NOT_NATIVE')
        self.assertEqual(cut['gates']['P2'],'HOLD')
        self.assertEqual(cut['gates']['P4'],'HOLD')
        self.assertIn('HOLD',cut['gates']['P5'])
        self.assertTrue(h.verify_local_cut(ROOT,cut,d))
        cut['gates']['P5']='PASS'
        with self.assertRaisesRegex(ValueError,'does not independently replay'):
            h.verify_local_cut(ROOT,cut,d)

    def test_wrong_71_command_names_cannot_pass_even_if_count_matches(self):
        d=fake_report(self.base,self.head)
        d['rows'][0]['case']='help:renamed-fake-command'
        # Shape alone would pass, but the Git atlas binding must refute it.
        h.operational_claim(d,self.base,self.head)
        with self.assertRaisesRegex(ValueError,'universe differs'):
            h.bind_pr70_universe(ROOT,d,base=self.base,head=self.head)

    def test_manifest_scope_and_reviewer_spoofing_blocked(self):
        baseline=fake_report(self.base,self.head)
        for key,value in [('manifest_sha256','a'*64),('universe','71_CASES_ONLY'),
                           ('independent_reviewer','YES_SIGNED')]:
            with self.subTest(key=key):
                d=copy.deepcopy(baseline);d[key]=value
                with self.assertRaises(ValueError):
                    h.bind_pr70_universe(ROOT,d,base=self.base,head=self.head)

    def test_forged_observations_cannot_be_promoted_to_native_replay(self):
        d=fake_report(self.base,self.head)
        # This is a valid but entirely fabricated shape; explicit rerun is
        # required before recording P2. Do not run 154 processes in unit test.
        cut=h.qualified_local_cut(ROOT,d,base=self.base,head=self.head)
        self.assertIsNone(cut['native_replay'])
        self.assertEqual(cut['global_dod'],'NOT_DEMONSTRATED')
        self.assertFalse(cut['release_authorized'])


if __name__=='__main__': unittest.main()
