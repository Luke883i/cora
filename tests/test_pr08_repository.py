"""PR-08: hardening with independent Git adversarial fixtures and README mutation probes."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from verify_repository_contract import audit_contract, COMMANDS  # noqa: E402
from cora.guard import install_guard
from cora.guard_runtime import verify as guard_verify
from cora.ontology import validate_ontology


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT).decode().strip()


class RepositoryContract(unittest.TestCase):
    def test_novice_static_readme_and_links(self):
        self.assertEqual(audit_contract(ROOT), [])
    def test_readme_missing_limit_is_detected(self):
        doc = (ROOT / 'README.md').read_text('utf-8')
        changed = doc.replace('## Operating boundaries', '## Undocumented')
        self.assertTrue(any('missing-section:' in x for x in audit_contract(ROOT, readme_override=changed)))
    def test_readme_missing_first_read_identity_is_detected(self):
        doc = (ROOT / 'README.md').read_text('utf-8')
        changed = doc.replace('**Product — CORA**', '**Capability — CORA**').replace('**Product**', '**Capability**')
        # Mutate all product-identity terms in first screen to falsify the first-read contract.
        lines=changed.splitlines()
        changed='\n'.join(s.replace('product', 'capability').replace('Product', 'Capability') for s in lines[:38] )+'\n'+'\n'.join(lines[38:])
        self.assertIn('first-read-missing:product', audit_contract(ROOT, readme_override=changed))
    def test_committed_self_ontology_is_valid(self):
        self.assertTrue(validate_ontology(json.loads((ROOT / 'cora.ontology.json').read_text('utf-8'))))
    def test_all_commands_accounted_for(self):
        self.assertEqual(len(COMMANDS), len(set(COMMANDS)))
        self.assertGreaterEqual(len(COMMANDS), 27)  # PR-08 compatibility floor; exact names checked by audit_contract


class IndependentGitGuardHardening(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.repo=Path(self.temp.name)
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@invalid.example')
        (self.repo/'apps/a').mkdir(parents=True)
        (self.repo/'apps/a/main.py').write_text('x=1\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'initial')
        self.before_install=git(self.repo, 'rev-parse', 'HEAD')
        install_guard(self.repo, ['a=apps/a=apps.a'])
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'install guard')
        self.after_install=git(self.repo, 'rev-parse', 'HEAD')
    def tearDown(self):
        self.temp.cleanup()
    def test_bootstrap_is_not_self_authorizing(self):
        result=guard_verify(self.repo, self.before_install)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('guard_bootstrap_requires_independent_review', {v['kind'] for v in result['violations']})
    def test_mutated_guard_old_base_still_blocks(self):
        p=self.repo/'.cora/verify.py'
        p.write_text(p.read_text() + '\n# untrusted bypass\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'mutate guard')
        result=guard_verify(self.repo, self.before_install)
        kinds={v['kind'] for v in result['violations']}
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('guard_or_workflow_changed', kinds)
        self.assertIn('guard_bootstrap_requires_independent_review', kinds)
    def test_mutated_guard_installed_base_still_blocks(self):
        p=self.repo/'.cora/verify.py'
        p.write_text(p.read_text() + '\n# changed\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'change guard')
        r=guard_verify(self.repo, self.after_install)
        self.assertEqual(r['status'], 'BLOCKED')
    def test_normal_postinstallation_source_change_passes(self):
        (self.repo/'apps/a/main.py').write_text('x=2\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'ordinary edit')
        self.assertEqual(guard_verify(self.repo, self.after_install)['status'], 'PASS_SCOPED')
    def test_modified_bootstrap_policy_fails(self):
        p=self.repo/'.cora/policy.json'
        p.write_text(p.read_text().replace('"exceptions": []', '"exceptions": ["bypass"]'))
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'forged policy')
        with self.assertRaises(ValueError):
            guard_verify(self.repo, self.before_install)


if __name__ == '__main__':
    unittest.main()
