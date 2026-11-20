import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.git_snapshot import snapshot
from cora.evidence import make_record, make_ledger, validate_record, validate_ledger
from cora.mutation_evidence import stress_evidence, FAMILIES, seeded_case


def g(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT).decode().strip()


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.commit='a'*40
        self.record=make_record(commit=self.commit,path='src/a.py',git_oid='b'*40,mode='100644',size=3,sha256='c'*64,status='observed_git_blob')
    def test_valid_record(self):
        self.assertTrue(validate_record(self.record))
    def test_tampered_hash(self):
        r=copy.deepcopy(self.record);r['sha256']='d'*64
        with self.assertRaises(ValueError):validate_record(r)
    def test_unknown_cannot_claim_runtime(self):
        r=copy.deepcopy(self.record);r['status']='runtime_verified'
        with self.assertRaises(ValueError):validate_record(r)
    def test_cross_commit(self):
        r=copy.deepcopy(self.record);r['commit']='d'*40
        r['digest']='e'*64
        with self.assertRaises(ValueError):make_ledger(self.commit,[r])
    def test_ledger_reorder(self):
        other=make_record(commit=self.commit,path='src/z.py',git_oid='b'*40,mode='100644',size=0,sha256='c'*64,status='observed_git_blob')
        l=make_ledger(self.commit,[other,self.record]);self.assertTrue(validate_ledger(l))
        l['records'].reverse()
        with self.assertRaises(ValueError):validate_ledger(l)
    def test_all_preseeded_oracles(self):
        for name,expected in FAMILIES:
            model,ledger=seeded_case(name,883)
            try:(validate_ledger if ledger else validate_record)(model);got=True
            except ValueError:got=False
            self.assertEqual(got,expected,name)
    def test_preseeded_replay(self):
        a=stress_evidence(seed=883,cases=1000)
        self.assertEqual(a,stress_evidence(seed=883,cases=1000))
        self.assertEqual(a['mismatches'],0)


class GitSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.repo=Path(self.t.name)
        g(self.repo,'init','-q')
        g(self.repo,'config','user.name','Cora Fixture')
        g(self.repo,'config','user.email','fixture@invalid.example')
        (self.repo/'live.py').write_text('print("original")\n')
        g(self.repo,'add','live.py');g(self.repo,'commit','-qm','baseline')
        self.commit=g(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.t.cleanup()
    def test_stable_against_uncommitted_changes(self):
        a=snapshot(self.repo,self.commit)
        (self.repo/'live.py').write_text('print("tampered")\n')
        (self.repo/'not-tracked').write_text('secret')
        self.assertEqual(a,snapshot(self.repo,'HEAD'))
        self.assertNotIn('not-tracked',{r['path'] for r in a['records']})
    def test_commit_change_produces_new_snapshot(self):
        a=snapshot(self.repo,self.commit)
        (self.repo/'live.py').write_text('print("new")\n')
        g(self.repo,'add','live.py');g(self.repo,'commit','-qm','next')
        b=snapshot(self.repo)
        self.assertNotEqual(a['ledger_digest'],b['ledger_digest'])
        self.assertTrue(validate_ledger(a));self.assertTrue(validate_ledger(b))
    def test_symlink_is_not_followed(self):
        (self.repo/'pointer').symlink_to('/etc/passwd')
        g(self.repo,'add','pointer');g(self.repo,'commit','-qm','symlink')
        a=snapshot(self.repo)
        s=[r for r in a['records'] if r['path']=='pointer'][0]
        self.assertEqual(s['status'],'symlink_unresolved');self.assertIsNone(s['sha256'])
    def test_lfs_pointer_unknown(self):
        (self.repo/'large.bin').write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+'a'*64+'\nsize 409600\n')
        g(self.repo,'add','large.bin');g(self.repo,'commit','-qm','lfs')
        a=snapshot(self.repo)
        self.assertEqual(next(r['status'] for r in a['records'] if r['path']=='large.bin'),'lfs_pointer_unresolved')
    def test_size_bound_unknown(self):
        (self.repo/'file.txt').write_text('abcdefghij')
        g(self.repo,'add','file.txt');g(self.repo,'commit','-qm','size')
        a=snapshot(self.repo,max_blob=4)
        self.assertEqual(next(r['status'] for r in a['records'] if r['path']=='file.txt'),'blob_too_large')
    def test_revalidate_detects_forged_digest(self):
        a=snapshot(self.repo)
        a['records'][0]['path']='another.py'
        with self.assertRaises(ValueError):validate_ledger(a)

if __name__=='__main__':unittest.main()
