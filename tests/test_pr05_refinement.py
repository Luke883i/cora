"""Independent PR-05 refinement: distinguish refuted nonexistent from blocked existing files."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.closure import closure, make_certificate

class RefutedDeletionSubject(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        for args in [('init','-q'),('config','user.name','Fixture'),('config','user.email','fixture@invalid.example')]:
            subprocess.run(['git','-C',str(self.repo),*args],check=True,capture_output=True)
        (self.repo/'live.txt').write_text('legitimate file')
        for args in [('add','live.txt'),('commit','-qm','fixture')]:
            subprocess.run(['git','-C',str(self.repo),*args],check=True,capture_output=True)
    def tearDown(self): self.temp.cleanup()
    def test_existing_file_never_safe_to_delete(self):
        cert=closure(self.repo,'safe_deletion','live.txt')
        self.assertEqual(cert['status'],'BLOCKED')
    def test_nonexistent_file_is_refuted_not_safe(self):
        cert=closure(self.repo,'safe_deletion','nonexistent.txt')
        self.assertEqual(cert['status'],'REFUTED')
        self.assertEqual(cert['effect'],'OBSERVATIONAL_ONLY')
    def test_manual_positive_deletion_is_rejected(self):
        with self.assertRaises(ValueError):
            make_certificate('safe_deletion','a'*40,'live.txt','', 'b'*64,
                             [{'id':'irrelevant','state':'VERIFIED','evidence':'untrusted'}], {'ledger':'b'*64})

if __name__=='__main__': unittest.main()
