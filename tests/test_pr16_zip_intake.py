"""PR-16 deterministic hostile ZIP fixtures, exact tree oracle and no implicit execution."""
from __future__ import annotations
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from cora.archive_intake import inspect_zip, verify_intake


def archive(path, entries):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as f:
        for name, raw, mode in entries:
            zi=zipfile.ZipInfo(name)
            zi.compress_type=zipfile.ZIP_DEFLATED
            zi.external_attr=(mode << 16)
            f.writestr(zi,raw)


class HostileZip(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.path=self.root/'source.zip'
        archive(self.path,[('bundle/alpha.txt',b'a',0o100644),('bundle/sub/beta.py',b'print(1)\n',0o100644)])
    def tearDown(self):self.tmp.cleanup()
    def fail_member(self, name, data=b'hello',mode=0o100644):
        archive(self.path,[('bundle/alpha.txt',b'a',0o100644),(name,data,mode)])
        with self.assertRaises(ValueError): inspect_zip(self.path)
    def test_positive_intake_and_strict_replay(self):
        with patch('subprocess.run',side_effect=AssertionError('untrusted code executed')):
            r=inspect_zip(self.path)
            self.assertEqual(r['execution'],'NOT_EXECUTED')
            self.assertEqual(r['git_history'],'UNAVAILABLE_NOT_IN_ZIP')
            self.assertTrue(verify_intake(self.path,r))
        self.assertEqual(r['tracked_files'],2)
        self.assertEqual(len(r['git_tree_sha1']),40)
        r['git_tree_sha1']='0'*40
        with self.assertRaises(ValueError): verify_intake(self.path,r)
    def test_clean_extraction_is_opt_in_and_no_overwrite(self):
        out=self.root/'workspace'
        r=inspect_zip(self.path,extract_to=out)
        self.assertEqual(r['workspace'],'CREATED_NO_EXECUTION')
        self.assertEqual((out/'sub/beta.py').read_bytes(),b'print(1)\n')
        with self.assertRaises(FileExistsError):inspect_zip(self.path,extract_to=out)
    def test_traversal(self): self.fail_member('bundle/../../outside.py')
    def test_absolute_path(self):self.fail_member('/tmp/payload.py')
    def test_backslash(self):self.fail_member('bundle/..\\other.py')
    def test_multiple_roots(self):self.fail_member('elsewhere/file.py')
    def test_git_directory(self):self.fail_member('bundle/.git/config')
    def test_git_directory_case(self):self.fail_member('bundle/.GIT/HEAD')
    def test_symlink(self):self.fail_member('bundle/link',b'/etc/passwd',0o120777)
    def test_duplicate(self):self.fail_member('bundle/alpha.txt',b'evil')
    def test_case_collision(self):self.fail_member('bundle/ALPHA.TXT',b'evil')
    def test_control_chars(self):self.fail_member('bundle/abc\nfile.py')
    def test_nfd_unicode(self):self.fail_member('bundle/cafe\u0301.py')
    def test_high_ratio_bomb(self):self.fail_member('bundle/bomb.py',b'\0'*1_000_000)
    def test_expected_tree_mismatch(self):
        with self.assertRaises(ValueError):inspect_zip(self.path,expected_tree='a'*40)
    def test_actual_archive_corruption(self):
        # Truncate physical ZIP; parser or integrity check must reject it.
        raw=self.path.read_bytes();self.path.write_bytes(raw[:-24])
        with self.assertRaises((zipfile.BadZipFile,ValueError,EOFError)):inspect_zip(self.path)

if __name__=='__main__':unittest.main()
