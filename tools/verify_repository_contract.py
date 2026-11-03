"""PR-08 repository self-description contract (stdlib only; independent of docs prose).

Run from any location: python tools/verify_repository_contract.py --repo .
This verifies static navigability, not genuine human comprehension or security.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
import sys
from pathlib import Path

CORE_DOCS = [
    'README.md', 'LICENSE', 'SECURITY.md', 'CONTRIBUTING.md',
    'docs/ARCHITECTURE.md', 'docs/DOD.md', 'docs/AUDIT_PR01_PR07.md',
    'cora.ontology.json', 'cora.artifact-roles.json', 'pyproject.toml', 'src/cora/cli.py',
    'docs/HOLISTIC_FORENSICS.md', 'docs/DOD_HOLISTIC_FORENSICS.md',
    'docs/ENGINEERING_DEBT.md', 'docs/DOD_ENGINEERING_DEBT.md',
    'AGENTS.md', 'docs/CONTINUOUS_DEVELOPMENT.md', 'docs/DOD_CONTINUOUS.md',
    'CHANGELOG.md', 'docs/ADR-PR15.md', 'docs/AUDIT_PR15_MAIN.md',
    'docs/DOD_RELEASE_READINESS.md', 'docs/RELEASE.md',
    'tools/verify_release_readiness.py', '.github/workflows/ci-release-readiness.yml',
    'GOVERNANCE.md', 'docs/DOD_SELECTION.md', 'docs/FILE_LAB.md', 'docs/STANDARDS_MAINTENANCE_AUDIT.md',
    'cora.agent-dod.json', 'docs/AI_CODE_ASSURANCE.md', 'docs/DOD_PR17_AGENT.md',
    'src/cora/agent_assurance.py', 'src/cora/agent_saturation.py',
    'cora.gold-assurance.json', 'src/cora/gold_assurance.py', 'src/cora/gold_mutations.py',
    'src/cora/gold_effects.py', 'src/cora/gold_saturation.py',
    'docs/GOLD_ASSURANCE.md', 'docs/DOD_PR19_GOLD.md', '.github/workflows/ci-gold-assurance.yml',
    'docs/AUDIT_PR19_CLOSURE.md',
    'cora.convergence-dod.json', 'src/cora/reticulum.py',
    'docs/CONVERGENT_ASSURANCE.md', 'docs/DOD_PR20_CONVERGENCE.md',
    '.github/workflows/ci-convergence.yml',
]
COMMANDS = (
    'version', 'audit', 'snapshot', 'verify-ledger', 'graph', 'explain',
    'adapter-audit', 'verify-adapters', 'closure', 'verify-certificate',
    'plan-rename-doc', 'apply-rename-doc', 'guard-install', 'guard-check',
    'stress', 'stress-evidence', 'stress-graph', 'stress-adapters',
    'stress-closure', 'stress-transform',
    'file-lab', 'verify-file-lab', 'file-decision', 'stress-file-lab',
    'artifact-audit', 'verify-artifacts', 'stress-artifact-semantics',
    'select-file', 'verify-selection', 'stress-selection',
    'holistic-audit', 'verify-holistic', 'archaeology', 'verify-archaeology', 'annotate-groups', 'stress-archaeology',
    'debt-scan', 'verify-debt', 'debt-diff', 'process-list', 'process-run', 'verify-process', 'stress-debt',
    'dev-premerge', 'dev-postmerge', 'verify-dev-gate', 'agent-check', 'stress-continuous',
    'zip-intake', 'verify-zip-intake', 'runtime-observe', 'fuse-evidence', 'verify-fusion',
    'lattice-audit', 'verify-lattice', 'dod-plan', 'dod-assess', 'verify-dod', 'stress-agent-dod',
    'gold-plan', 'gold-pilot', 'gold-mutate', 'gold-effects', 'stress-gold',
    'convergence-plan', 'verify-contextual-gate', 'stress-convergence',
)


def audit_contract(root: Path, *, readme_override: str | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for rel in CORE_DOCS:
        if not (root / rel).is_file():
            errors.append('missing-path:' + rel)
    if errors:
        return errors
    readme = readme_override if readme_override is not None else (root / 'README.md').read_text('utf-8')
    lines = readme.splitlines()
    front = '\n'.join(lines[:38]).lower()
    for token in ('product', 'software', 'repository', 'not', 'python', 'install', 'audit', 'snapshot'):
        if token not in front:
            errors.append('first-read-missing:' + token)
    if not readme.startswith('# CORA — Continuous Ontological Repository Assurance'):
        errors.append('full-product-name-missing')
    if '**CORA (Continuous Ontological Repository Assurance)**' not in readme:
        errors.append('first-read-acronym-expansion-missing')
    if not readme.startswith('# CORA'):
        errors.append('missing-title')
    for heading in ('## First five minutes', '## What works', '## Operating boundaries', '## Engineering map'):
        if heading not in readme:
            errors.append('missing-section:' + heading)
    if len(lines) > 180:
        errors.append('readme-too-long:' + str(len(lines)))
    if 'safe_deletion' not in readme and 'deletion' not in readme:
        errors.append('missing-deletion-boundary')
    # Direct README links must resolve in this checkout: no dangling onboarding.
    for match in re.finditer(r'\]\(([^)]+)\)', readme):
        dest = match.group(1).split('#', 1)[0]
        if not dest or '://' in dest or dest.startswith('mailto:'):
            continue
        if dest.startswith('/') or '..' in Path(dest).parts or not (root / dest).exists():
            errors.append('broken-readme-link:' + dest)
    try:
        data = json.loads((root / 'cora.ontology.json').read_text('utf-8'))
        # A checked-in declared product and two declared software identities.
        assert data['schema'] == 'cora-ontology/1'
        assert {x['id'] for x in data['products']} == {'cora'}
        assert {'cora-engine', 'cora-release-verification'} == {x['id'] for x in data['software']}
        assert 'src/cora/cli.py' in data['products'][0]['entrypoints']
        for p in data['products'] + data['software']:
            for path in p['roots']:
                assert (root / path).is_dir(), path
    except (AssertionError, ValueError, KeyError, TypeError) as e:
        errors.append('self-ontology-invalid:' + str(e))
    try:
        import tomllib
        project = tomllib.loads((root / 'pyproject.toml').read_text('utf-8'))
        declared_version=project['project']['version']
        init_source=(root/'src/cora/__init__.py').read_text('utf-8')
        if f'__version__ = "{declared_version}"' not in init_source or declared_version not in readme:
            errors.append('release-version-drift')
        assert project['project']['name'] == 'cora-audit'
        assert project['project']['scripts'] == {'cora': 'cora.cli:main'}
        assert project['project']['dependencies'] == []
    except (AssertionError, ValueError, KeyError, TypeError) as e:
        errors.append('packaging-contract-invalid:' + str(e))
    # Discover registered parsers from the actual AST rather than a handwritten list.
    tree = ast.parse((root / 'src/cora/cli.py').read_text('utf-8'))
    commands = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_parser':
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                commands.append(n.args[0].value)
    if sorted(commands) != sorted(COMMANDS):
        errors.append('command-registry-drift:' + repr(sorted(set(commands) ^ set(COMMANDS))))
    # README maps every non-stress command or directs readers to --help.
    if 'cora --help' not in readme:
        errors.append('missing-cli-discovery')
    for cmd in COMMANDS:
        if not cmd.startswith('stress') and f'`{cmd}`' not in readme and not re.search(r'\bcora\s+' + re.escape(cmd) + r'(?=\s|$)', readme):
            errors.append('unmentioned-command:' + cmd)
    # Each foundational provenance/guard capability must have a test file.
    for n in range(1, 8):
        if not (root / 'tests' / f'test_pr0{n}.py').is_file():
            errors.append('missing-pr-regression:' + str(n))
    return errors


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args(argv)
    errors = audit_contract(a.repo)
    print(json.dumps({'schema': 'cora-repository-contract/1', 'status': 'PASS_SCOPED' if not errors else 'FAIL',
                      'checks': 'readme-first-read, cli, paths, ontology, package, regressions', 'errors': errors},
                     indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == '__main__':
    sys.exit(main())
