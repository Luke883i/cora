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

    def test_cto_positioning_source_contract(self):
        from verify_repository_contract import audit_product_positioning
        readme = (ROOT / 'README.md').read_text('utf-8')
        self.assertEqual(audit_product_positioning(ROOT, readme), [])

    def test_cto_falsification_11_realistic_false_promotions(self):
        from verify_repository_contract import audit_product_positioning
        readme = (ROOT / 'README.md').read_text('utf-8')
        start = readme.index('**CTO evaluation snapshot')
        end = readme.index('**71 declared CLI commands**', start)
        prefix, panel, suffix = readme[:start], readme[start:end], readme[end:]
        hostile = (
            ('actor', '**Who / what?**', '**Who / what? UNKNOWN**'),
            ('method', '**CORA-METHOD**', '**AUTONOMOUS-AGENT**'),
            ('engine', '**CORA-ENGINE**', '**AGENT-WRITER**'),
            ('oracle', 'falsifiable DoD', 'unqualified judgement'),
            ('scope', 'partial Python AST', 'complete Python semantics'),
            ('pilot', '**Teddy Node**', '**Universal Node**'),
            ('package', 'cora-audit 1.0.0a5', 'cora-audit 2.0.0'),
            ('sbom', 'NOT_GENERATED_BY_CI', 'GENERATED_AND_CERTIFIED'),
            ('sca', '**SCA/CVE: NOT_ATTESTED**', '**SCA/CVE: CERTIFIED**'),
            ('signing', 'SLSA provenance: NOT_ATTESTED', 'SLSA provenance: CERTIFIED'),
            ('approval', 'release: BLOCKED_EXTERNAL', 'release: APPROVED'),
        )
        for label, old, new in hostile:
            with self.subTest(label=label):
                self.assertIn(old, panel)
                mutant = prefix + panel.replace(old, new, 1) + suffix
                self.assertTrue(audit_product_positioning(ROOT, mutant))
        cosmetic = prefix + panel.replace(
            '**CTO evaluation snapshot', '**CTO evaluation snapshot', 1
        ).replace('Developer tooling for CTOs', 'Developer tooling for CTOs', 1) + suffix
        self.assertEqual(audit_product_positioning(ROOT, cosmetic), [])

    def test_cto_cross_source_mutants_fail_closed(self):
        import shutil
        from verify_repository_contract import audit_product_positioning
        paths = (
            'README.md', 'pyproject.toml', 'cora.ontology.json',
            '.cora/assurance/capability-atlas.json', 'LICENSE',
            'src/cora/cli.py', 'src/cora/native_gold.py',
            'docs/ARCHITECTURE.md', 'docs/INDEX.md', 'docs/RELEASE.md',
            'SECURITY.md', '.github/workflows/ci-release-candidate.yml',
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for rel in paths:
                dest = root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, dest)
            readme = (root / 'README.md').read_text('utf-8')
            self.assertEqual(audit_product_positioning(root, readme), [])
            cases = (
                ('package', 'pyproject.toml', 'version = "1.0.0a5"',
                 'version = "9.9.9"', 'positioning-package-license-drift'),
                ('pilot', 'src/cora/native_gold.py', '"Luke883i/teddy"',
                 '"Luke883i/unknown"', 'positioning-native-runtime-allowlist-drift'),
                ('build', '.github/workflows/ci-release-candidate.yml',
                 'sha256sum dist/', 'NO_SHA256 dist/', 'positioning-build-sbom-truth-drift'),
                ('supply-chain', 'docs/RELEASE.md', 'NOT_GENERATED_BY_CI',
                 'SBOM_CERTIFIED', 'positioning-security-release-truth-drift'),
                ('navigation', 'docs/ARCHITECTURE.md', 'CORA-METHOD',
                 'UNKNOWN-METHOD', 'positioning-architecture-navigation-drift'),
            )
            for label, rel, before, after, expected in cases:
                with self.subTest(label=label):
                    original = (root / rel).read_text('utf-8')
                    self.assertIn(before, original)
                    (root / rel).write_text(original.replace(before, after, 1),
                                            encoding='utf-8')
                    errors = audit_product_positioning(root, readme)
                    self.assertIn(expected, errors)
                    (root / rel).write_text(original, encoding='utf-8')

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
