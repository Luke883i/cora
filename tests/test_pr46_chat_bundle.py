"""Regression and hostile-archive checks for the portable chat session ledger."""
from __future__ import annotations
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from cora.chat_bundle import (append_chat_iteration, verify_chat_bundle,
                              validate_step, _json, load_chat_step)


class ChatBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.bundle = self.root / 'chat-session.zip'
        self.sha = 'a' * 40

    def receipt(self, commit=None):
        return {'schema': 'cora-integrated-one-run/2', 'commit': commit or self.sha,
                'product_status': 'BLOCKED_EXTERNAL', 'authorization': 'NONE',
                'authority': 'NONE', 'release_authorized': False}

    def step(self, n=1):
        return {
            'schema':'cora-chat-iteration/1', 'session_id':'test-run-01',
            'iteration':n, 'intent':'Test chat continuity without promotion',
            'actions':[{'id':'A1','action':'Capture exact source and inspect DoD',
                        'status':'DONE_REPORTED'}],
            'roadmap':[{'id':'R1','action':'Seek a real reviewer before closing',
                        'depends_on':[], 'dod_refs':['D2'],
                        'falsifier_refs':['F1'], 'status':'BLOCKED'}],
            'falsifiers':[{'id':'F1','claim':'Reviewer independence is established',
                           'method':'Demand host readback and independent signature',
                           'oracle':'A separate trusted operator verifies approval',
                           'status':'NOT_RUN'}],
            'dod':{'goal':'G', 'nodes':[
                {'id':'D1','depends_on':[],'scope':'SOURCE','acceptance':'Git source identified',
                 'observation':'REPORTED_OBSERVED','evidence_refs':['original-git:HEAD']},
                {'id':'D2','depends_on':[],'scope':'EXTERNAL','acceptance':'Independent review',
                 'observation':'UNOBSERVED','evidence_refs':[]},
                {'id':'G','depends_on':['D1','D2'],'scope':'SOURCE',
                 'acceptance':'Source and independent review',
                 'observation':'UNOBSERVED','evidence_refs':[]}]},
            'gaps':[{'id':'X1','description':'Separate qualified reviewer absent',
                     'blocks':['D2'], 'next_action':'Obtain qualified reviewer readback'}],
            'next_step':'Keep proof claims BLOCKED_EXTERNAL until independently observed'}

    def test_append_roundtrip_two_rounds_and_exact_handoff(self):
        r1 = append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        self.assertEqual(r1['iterations'],1)
        with zipfile.ZipFile(self.bundle) as z:
            old = {i.filename:z.read(i.filename) for i in z.infolist()}
        r2 = append_chat_iteration(self.bundle,repo=self.repo,step=self.step(2),receipt=self.receipt('b'*40))
        self.assertEqual(r2['iterations'],2)
        self.assertEqual(r2['last_commit'],'b'*40)
        self.assertEqual(verify_chat_bundle(self.bundle,expected_receipt=self.receipt('b'*40)),r2)
        with zipfile.ZipFile(self.bundle) as z:
            for path,data in old.items(): self.assertEqual(z.read(path),data)
            handoff=z.read('iterations/000002/handoff.md').decode()
            self.assertIn('## Explicit unresolved gaps',handoff)
            self.assertIn('BLOCKED_EXTERNAL',handoff)
            self.assertIn('Git source: '+'b'*40,handoff)

    def test_nonsequential_and_identity_change_fail_without_modification(self):
        append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        old=self.bundle.read_bytes()
        for bad in [self.step(1),self.step(3)]:
            with self.assertRaises(ValueError):
                append_chat_iteration(self.bundle,repo=self.repo,step=bad,receipt=self.receipt())
        other=self.step(2);other['session_id']='foreign-session'
        with self.assertRaises(ValueError):
            append_chat_iteration(self.bundle,repo=self.repo,step=other,receipt=self.receipt())
        self.assertEqual(old,self.bundle.read_bytes())

    def test_forged_receipt_and_source_promotion_refused(self):
        for key,value in [('product_status','PASS'),('authorization','MERGE'),
                          ('authority','ADMIN'),('release_authorized',True)]:
            bad=self.receipt();bad[key]=value
            with self.assertRaises(ValueError):
                append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=bad)
        self.assertFalse(self.bundle.exists())

    def test_dod_unknowns_orphan_cycles_and_unlinked_gaps_fail(self):
        for transform in [
            lambda a: a['gaps'].clear(),
            lambda a: a['dod']['nodes'][2].update(depends_on=['G']),
            lambda a: a['dod']['nodes'][0].update(observation='PASS'),
            lambda a: a['dod']['nodes'][1].update(observation='REPORTED_OBSERVED'),
            lambda a: a['dod']['nodes'][0].update(evidence_refs=[]),
            lambda a: a['roadmap'][0].update(falsifier_refs=[]),
            lambda a: a['falsifiers'][0].update(status='PASSED'),
            lambda a: a['dod']['nodes'].append({'id':'ORPHAN','depends_on':[],
                           'scope':'SOURCE','acceptance':'orphan','observation':'UNOBSERVED',
                           'evidence_refs':[]}),
        ]:
            step=self.step();transform(step)
            with self.subTest(step=step),self.assertRaises(ValueError): validate_step(step)

    def test_path_traversal_duplicate_and_modified_receipt_rejected(self):
        append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        with zipfile.ZipFile(self.bundle,'a') as z:
            z.writestr('../evil','x')
        with self.assertRaises(ValueError): verify_chat_bundle(self.bundle)
        self.bundle.unlink()
        append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        with zipfile.ZipFile(self.bundle,'a') as z:
            z.writestr('iterations/000001/source-receipt.json',_json(self.receipt('c'*40)))
        with self.assertRaises(ValueError): verify_chat_bundle(self.bundle)

    def test_archive_tampering_cannot_be_appended(self):
        append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        original=self.bundle.read_bytes()
        with zipfile.ZipFile(self.bundle,'a') as z:
            z.writestr('unmanifested.txt','evil')
        with self.assertRaises(ValueError):
            append_chat_iteration(self.bundle,repo=self.repo,step=self.step(2),receipt=self.receipt())
        self.assertNotEqual(original,self.bundle.read_bytes())

    def test_escape_repo_and_lock_rejected(self):
        with self.assertRaises(ValueError):
            append_chat_iteration(self.repo/'out.zip',repo=self.repo,step=self.step(),receipt=self.receipt())
        lock=self.bundle.with_name(self.bundle.name+'.lock');lock.write_text('busy')
        with self.assertRaises(ValueError):
            append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        self.assertEqual(lock.read_text(),'busy')

    def test_input_json_duplicate_key_and_size_rejected(self):
        p = self.root/'step.json'
        p.write_text(_json(self.step()).decode('utf-8'),encoding='utf-8')
        self.assertEqual(load_chat_step(p)['iteration'],1)
        p.write_text('{"schema":"x","schema":"y"}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,"duplicate JSON"):
            load_chat_step(p)
        p.write_bytes(b'x' * (8 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError,"oversized"):
            load_chat_step(p)

    def test_replay_latest_receipt_must_match(self):
        append_chat_iteration(self.bundle,repo=self.repo,step=self.step(),receipt=self.receipt())
        with self.assertRaises(ValueError):
            verify_chat_bundle(self.bundle,expected_receipt=self.receipt('f'*40))

if __name__=='__main__': unittest.main()
