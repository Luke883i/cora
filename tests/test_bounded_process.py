"""C04: bounded output while an opted-in process actually runs."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from cora.process_bounds import run_bounded
from cora.transform import MAX_VERIFIER_LOG, apply_rename_docs, plan_rename_docs


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


class C04BoundedSubprocess(unittest.TestCase):
    def test_stdout_and_stderr_are_bounded_without_dropping_small_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = run_bounded([sys.executable, '-c',
                "import sys; print('ok'); print('warning',file=sys.stderr)"],
                cwd=Path(directory), timeout=4, max_output=1024)
            self.assertEqual(proc.returncode, 0)
            self.assertIn(b'ok', proc.stdout)
            self.assertIn(b'warning', proc.stdout)

    def test_oversize_fails_during_execution_without_collecting_full_output(self):
        with tempfile.TemporaryDirectory() as directory:
            started = time.monotonic()
            with self.assertRaisesRegex(ValueError, 'output exceeded byte budget'):
                run_bounded([sys.executable, '-c',
                    "import sys; sys.stdout.buffer.write(b'x' * 10_000_000); sys.stdout.flush()"],
                    cwd=Path(directory), timeout=8, max_output=4096)
            self.assertLess(time.monotonic() - started, 7)

    def test_timeout_and_nonzero_do_not_become_success(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.TimeoutExpired):
                run_bounded([sys.executable, '-c', 'import time; time.sleep(3)'],
                            cwd=Path(directory), timeout=1, max_output=1024)
            proc = run_bounded([sys.executable, '-c', 'raise SystemExit(32)'],
                               cwd=Path(directory), timeout=5, max_output=1024)
            self.assertEqual(proc.returncode, 32)


    def test_native_gold_overflow_cannot_create_a_success_receipt(self):
        from cora.native_gold import capture_native
        with tempfile.TemporaryDirectory(prefix='cora-native-c04-') as directory:
            root = Path(directory)
            repo = root / 'target'
            repo.mkdir()
            git(repo, 'init', '-q')
            git(repo, 'config', 'user.name', 'CORA test')
            git(repo, 'config', 'user.email', 'cora@example.invalid')
            oracle = repo / 'tests' / 'cora-adoption.test.mjs'
            oracle.parent.mkdir()
            oracle.write_text('// inert committed oracle\n')
            git(repo, 'add', '.'); git(repo, 'commit', '-qm', 'fixture')
            head = git(repo, 'rev-parse', 'HEAD')
            cmd = (sys.executable, '-c',
                   "import sys; sys.stdout.buffer.write(b'x' * 8_000_000)")
            with patch.dict('cora.native_gold.PILOTS',
                            {'Luke883i/teddy': ('tests/cora-adoption.test.mjs', cmd, None)}):
                with self.assertRaisesRegex(ValueError, 'log budget'):
                    capture_native(repo, 'Luke883i/teddy', head,
                                   'C_NATIVE', root / 'evidence')
            self.assertFalse((root / 'evidence' / 'receipt.json').exists())

    def test_invalid_byte_budget_is_rejected_before_process_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            for max_output in (0, -1, 64*1024*1024+1, True):
                with self.subTest(max_output=max_output), self.assertRaises(ValueError):
                    run_bounded([sys.executable, '-c', 'pass'],
                                cwd=Path(directory), timeout=2, max_output=max_output)

    def test_transform_rolls_back_on_output_overflow(self):
        with tempfile.TemporaryDirectory(prefix='cora-c04-') as directory:
            repo = Path(directory)
            git(repo,'init','-q');git(repo,'config','user.name','CORA test');git(repo,'config','user.email','cora@example.invalid')
            (repo/'docs').mkdir()
            old=repo/'docs'/'old.md';old.write_text('docs/old.md\n')
            old.chmod(0o755)
            git(repo,'add','.');git(repo,'commit','-qm','fixture')
            plan=plan_rename_docs(repo,'docs/old.md','docs/new.md')
            with patch('cora.transform.MAX_VERIFIER_LOG', 4096):
                with self.assertRaisesRegex(ValueError, 'output exceeded byte budget'):
                    apply_rename_docs(repo,plan,approval=plan['plan_digest'],
                        test_command=[sys.executable,'-c',
                            "import sys; sys.stdout.buffer.write(b'x'*100_000); sys.stdout.flush()"])
            self.assertEqual(old.read_text(),'docs/old.md\n')
            self.assertEqual(old.stat().st_mode & 0o777,0o755)
            self.assertFalse((repo/'docs'/'new.md').exists())
            self.assertEqual(git(repo,'status','--porcelain'),'')
