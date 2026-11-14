"""Real executed Git-fixture counterexamples not in PR70's 77-observation scope.

These are synthetic target programs executed from original Git checkouts;
they do NOT test CORA's own native runtime.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def command(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout.strip()


class TargetCounterfactual(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "original"
        self.repo.mkdir()
        command(self.repo, "init", "-q")
        command(self.repo, "config", "user.name", "fixture")
        command(self.repo, "config", "user.email", "fixture@example.invalid")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self, msg):
        command(self.repo, "add", "-A")
        command(self.repo, "commit", "-qm", msg)
        return command(self.repo, "rev-parse", "HEAD")

    def checkout(self, rev, target):
        command(self.repo, "worktree", "add", "-q", "--detach", str(target), rev)

    def run_app(self, root, *args):
        return subprocess.run([sys.executable, "app.py", *args], cwd=root,
                              capture_output=True, timeout=15)

    def test_same_exit_stdout_stderr_can_hide_changed_side_effects(self):
        path = self.repo / "app.py"
        path.write_text("from pathlib import Path\nPath('receipt.json').write_text('A')\nprint('OK')\n")
        base = self.commit("baseline with A side effect")
        path.write_text("from pathlib import Path\nPath('receipt.json').write_text('B')\nprint('OK')\n")
        head = self.commit("mutant with different persisted receipt")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        ra, rb = self.run_app(a), self.run_app(b)
        self.assertEqual((ra.returncode, ra.stdout, ra.stderr),
                         (rb.returncode, rb.stdout, rb.stderr))
        self.assertNotEqual((a / "receipt.json").read_bytes(),
                            (b / "receipt.json").read_bytes())

    def test_dynamic_plugin_unobserved_by_direct_import_candidates(self):
        path = self.repo / "app.py"
        path.write_text("import importlib\nimport sys\n"
                        "mod=importlib.import_module(sys.argv[1])\nprint(mod.result())\n")
        (self.repo / "plug.py").write_text("def result():\n    return 'plugin-works'\n")
        base = self.commit("baseline contains dynamically resolved consumer")
        (self.repo / "plug.py").unlink()
        head = self.commit("candidate deletes plugin with no static import")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        good, bad = self.run_app(a, "plug"), self.run_app(b, "plug")
        self.assertEqual(good.returncode, 0)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn(b"No module named", bad.stderr)

    def test_error_path_semantics_recovered_by_negative_input(self):
        path = self.repo / "app.py"
        path.write_text("import sys\n"
                        "if sys.argv[1]=='bad':\n    print('blocked', file=sys.stderr)\n    sys.exit(2)\n"
                        "print('OK')\n")
        base = self.commit("baseline rejects invalid input")
        path.write_text("import sys\n"
                        "if sys.argv[1]=='bad':\n    print('OK')\n    sys.exit(0)\n"
                        "print('OK')\n")
        head = self.commit("candidate silently accepts invalid input")
        a, b = self.root / "left", self.root / "right"
        self.checkout(base, a)
        self.checkout(head, b)
        self.assertEqual(self.run_app(a, "good").stdout, self.run_app(b, "good").stdout)
        self.assertNotEqual(self.run_app(a, "bad").returncode,
                            self.run_app(b, "bad").returncode)


if __name__ == "__main__":
    unittest.main()
