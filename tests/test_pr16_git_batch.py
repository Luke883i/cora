"""PR-16 independent Git object oracle, mutation and subprocess-budget tests."""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cora.git_snapshot as gs


def run(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(repo), *args])


class GitBatchFalsification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        run(self.repo, 'init', '-q')
        run(self.repo, 'config', 'user.name', 'Fixture')
        run(self.repo, 'config', 'user.email', 'fixture@invalid.example')
        for i in range(100):
            (self.repo / ('file-%03d.dat' % i)).write_bytes(b'same payload\x00data' if i % 10 == 0 else (str(i)*i).encode())
        (self.repo / 'pointer').write_bytes(b'version https://git-lfs.github.com/spec/v1\n' + b'oid sha256:a\n')
        (self.repo / 'binary').write_bytes(b'\x00\nblob 99\x00\xff' * 24)
        (self.repo / 'large').write_bytes(b'large' * 200)
        (self.repo / 'target').symlink_to('file-000.dat')
        run(self.repo, 'add', '-A')
        run(self.repo, 'commit', '-qm', 'source snapshot fixture')
        self.sha = run(self.repo, 'rev-parse', 'HEAD').decode().strip()

    def tearDown(self):
        self.tmp.cleanup()

    def oracle(self, limit):
        rows = {}
        raw = run(self.repo, 'ls-tree', '-rz', '--full-tree', self.sha)
        for row in raw.split(b'\x00'):
            if not row: continue
            prefix, path = row.split(b'\t')
            mode, kind, oid = prefix.split(b' ')
            key = path.decode('utf-8')
            if mode == b'120000':
                rows[key] = ('symlink_unresolved', None, None)
                continue
            size = int(run(self.repo, 'cat-file', '-s', oid.decode()))
            if size > limit:
                rows[key] = ('blob_too_large', None, None)
                continue
            data = run(self.repo, 'cat-file', 'blob', oid.decode())
            if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                rows[key] = ('lfs_pointer_unresolved', None, None)
            else:
                rows[key] = ('observed_git_blob', size, hashlib.sha256(data).hexdigest())
        return rows

    def test_binary_duplicate_symlink_lfs_and_bounded_objects(self):
        for max_blob in (1, 20, 8*1024*1024):
            report = gs.snapshot(self.repo, self.sha, max_blob=max_blob)
            observed = {r['path']:(r['status'],r['size'],r['sha256']) for r in report['records']}
            self.assertEqual(observed, self.oracle(max_blob))
            self.assertEqual(report, gs.snapshot(self.repo,self.sha,max_blob=max_blob))

    def test_subprocess_budget_is_bounded_not_per_file(self):
        original = gs.subprocess.run
        calls = []
        def audited(*args, **kwargs):
            if args and args[0] and args[0][0] == 'git':
                calls.append(args[0])
            return original(*args,**kwargs)
        with patch.object(gs.subprocess, 'run', side_effect=audited):
            report = gs.snapshot(self.repo, self.sha)
        self.assertEqual(len(report['records']),104)
        self.assertLessEqual(len(calls),5, calls)
        self.assertEqual(len([c for c in calls if 'cat-file' in c]),2)

    def test_uncommitted_worktree_is_not_observed(self):
        initial=gs.snapshot(self.repo,self.sha)
        (self.repo/'file-001.dat').write_bytes(b'untrusted working tree')
        self.assertEqual(initial,gs.snapshot(self.repo,self.sha))

    def test_corrupted_batch_headers_fail_closed(self):
        with patch.object(gs, '_batch', return_value=b'deadbeef blob 5\nhello\n'):
            with self.assertRaises(ValueError):
                gs.snapshot(self.repo, self.sha)

if __name__ == '__main__': unittest.main()
