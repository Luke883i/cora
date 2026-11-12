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
    'CHANGELOG.md', 'docs/archive/decisions/ADR-PR15.md', 'docs/archive/audits/AUDIT_PR15_MAIN.md',
    'docs/DOD_RELEASE_READINESS.md', 'docs/RELEASE.md',
    'tools/verify_release_readiness.py', '.github/workflows/ci-release-readiness.yml',
    'GOVERNANCE.md', 'docs/DOD_SELECTION.md', 'docs/FILE_LAB.md', 'docs/STANDARDS_MAINTENANCE_AUDIT.md',
    '.cora/contracts/dod/agent-dod.json', 'docs/AI_CODE_ASSURANCE.md', 'docs/archive/dod/DOD_PR17_AGENT.md',
    'src/cora/agent_assurance.py', 'src/cora/agent_saturation.py',
    '.cora/contracts/dod/gold-assurance.json', 'src/cora/gold_assurance.py', 'src/cora/gold_mutations.py',
    'src/cora/gold_effects.py', 'src/cora/gold_saturation.py',
    'docs/GOLD_ASSURANCE.md', 'docs/DOD_PR19_GOLD.md', '.github/workflows/ci-gold-assurance.yml',
    'docs/archive/audits/AUDIT_PR19_CLOSURE.md',
    '.cora/contracts/dod/convergence-dod.json', 'src/cora/reticulum.py',
    'docs/CONVERGENT_ASSURANCE.md', 'docs/DOD_PR20_CONVERGENCE.md',
    '.github/workflows/ci-convergence.yml',
    '.cora/contracts/dod/documentation-dod.json', 'docs/documentation-registry.json',
    'docs/INDEX.md', 'docs/GETTING_STARTED.md', 'docs/AGENT_ADOPTION.md',
    'docs/CLI_REFERENCE.md', 'docs/DOCUMENTATION_DOD.md',
    'tools/verify_documentation.py', 'tests/test_pr21_documentation.py',
    '.github/workflows/ci-documentation.yml',
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
    'workflow-audit', 'verify-workflows',
    'method-synthesize', 'verify-method-synthesis',
)



def audit_product_positioning(root: Path, readme: str) -> list[str]:
    """Source-derived CTO disclosure gate, NOT enterprise/user/runtime certification.

    Uses independent package metadata, product ontology, original native allowlist,
    release-candidate CI, security/release policy and the canonical capability
    inventory. Text evidence is explicitly untrusted for external authority.
    """
    errors: list[str] = []
    marker = "**CTO evaluation snapshot"
    if readme.count(marker) != 1 or "## What works today" not in readme:
        return ["positioning-frontdoor-missing"]
    start = readme.index(marker)
    end = readme.find("**71 declared CLI commands**", start)
    if end < start:
        return ["positioning-frontdoor-not-before-capabilities"]
    panel = readme[start:end]
    required = {
        "category": ("**Who / what?**", "CTOs", "reviewers", "AI coding-agent operators"),
        "method-engine": ("**CORA-METHOD**", "**CORA-ENGINE**", "third-party agents",
                          "not approval"),
        "unit": ("bounded software change", "falsifiable DoD", "unresolved obligations"),
        "target": ("Git-bound source inspection", "partial Python AST",
                   "static JavaScript ESM", "**Teddy Node**", "**ICTC HTTP/SQLite**"),
        "packaging": ("**MIT**", "**Python 3.11+**", "cora-audit 1.0.0a5",
                      "no declared mandatory Python runtime dependencies"),
        "sbom": ("**SBOM (CycloneDX 1.6): GENERATION_IN_CANDIDATE_CI**",),
        "sca": ("**SCA/CVE: SCAN_CI_BUILD_TOOLS_ONLY**",),
        "signing": ("**artifact signing / SLSA provenance: NOT_ATTESTED**",),
        "governance": ("**Independent reviewer, enforced branch rules, release: BLOCKED_EXTERNAL**",
                       "no production security SLA"),
        "safety": ("not an enterprise-readiness certificate", "Execution needs authorization"),
        "assurance-levels": ("**L1** = Git/source checks", "**L2** = bounded product experiments",
                             "**L3** = optional external assurance",
                             "L1/L2 may be useful without L3",
                             "cannot approve a release"),
        "routes": ("[Security](SECURITY.md)", "[Release](docs/RELEASE.md)"),
    }
    for label, phrases in required.items():
        if any(phrase not in panel for phrase in phrases):
            errors.append("positioning-missing:" + label)
    if re.search(r"\b(?:enterprise[- ]ready|SBOM generated|SCA passed|release approved|"
                 r"independently certified|SLSA certified)\b", panel, re.I):
        errors.append("positioning-unearned-authority")
    try:
        import tomllib
        package = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))["project"]
        ontology = json.loads((root / "cora.ontology.json").read_text("utf-8"))
        catalog = json.loads((root / ".cora/assurance/capability-atlas.json").read_text("utf-8"))
        cli = (root / "src/cora/cli.py").read_text("utf-8")
        native = ast.parse((root / "src/cora/native_gold.py").read_text("utf-8"))
        security = (root / "SECURITY.md").read_text("utf-8")
        release = (root / "docs/RELEASE.md").read_text("utf-8")
        architecture = (root / "docs/ARCHITECTURE.md").read_text("utf-8")
        index = (root / "docs/INDEX.md").read_text("utf-8")
        candidate = (root / ".github/workflows/ci-release-candidate.yml").read_text("utf-8")
        licence = (root / "LICENSE").read_text("utf-8")
        if (package.get("name") != "cora-audit" or package.get("version") != "1.0.0a5"
                or package.get("requires-python") != ">=3.11" or
                package.get("license") != "MIT" or package.get("dependencies") != [] or
                package.get("description") !=
                "Agent-agnostic engineering assurance for Git-based software changes" or
                not licence.startswith("MIT License")):
            errors.append("positioning-package-license-drift")
        if (ontology.get("schema") != "cora-ontology/1"
                or {p["id"] for p in ontology["products"]} != {"cora"}
                or {p["id"] for p in ontology["software"]}
                   != {"cora-engine", "cora-release-verification"}):
            errors.append("positioning-product-software-ontology-drift")
        if (len(catalog.get("families", [])) != 8
                or len(catalog.get("commands", [])) != 71
                or "eight declared CLI families" not in index):
            errors.append("positioning-capability-inventory-drift")
        pilots = [n.value for n in native.body
                  if isinstance(n, ast.Assign) and any(
                      isinstance(t, ast.Name) and t.id == "PILOTS" for t in n.targets)]
        if len(pilots) != 1 or set(ast.literal_eval(pilots[0])) != {
                "Luke883i/teddy", "Luke883i/ictc"}:
            errors.append("positioning-native-runtime-allowlist-drift")
        if not all(token in cli for token in (
                "process-run", "verify-process", "--portable-profile",
                "--portable-native-probe")):
            errors.append("positioning-cli-boundary-drift")
        if not all(token in candidate for token in (
                "tools/build_candidate.py", "tools/release_verify.py",
                "tools/external_validate.py", "sha256sum", "SHA256SUMS",
                "pip-audit==2.10.1", "--sbom-output", "--verify-sbom",
                "--provenance-output", "--verify-provenance",
                "--sca-raw", "--verify-sca", "build-tool-pins.json")):
            errors.append("positioning-build-sbom-truth-drift")
        if (not all(token in release for token in (
                "Post-PR52 CTO procurement", "CONFIGURED_IN_PR55_CANDIDATE_CI",
                "SLSA/in-toto", "BLOCKED_EXTERNAL", "not a self-issued"))
                or not all(token in security for token in (
                    "Supply-chain and enterprise evaluation disclosure",
                    "CycloneDX 1.6 SBOM", "no supported production release",
                    "NOT_ATTESTED"))):
            errors.append("positioning-security-release-truth-drift")
        if (not all(token in architecture for token in (
                "Product category, target and evidence boundaries",
                "CORA-METHOD", "CORA-ENGINE", "not an independent approval authority",
                "L1 engineering evidence", "L2 experimental product validation",
                "L3 optional external assurance"))
                or not all(token in release for token in (
                    "L1", "L2", "L3", "optional for experimental use"))
                or "[README](../README.md)" not in index):
            errors.append("positioning-architecture-navigation-drift")
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        errors.append("positioning-source-unreadable:" + type(exc).__name__)
    return errors


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
    errors.extend(audit_product_positioning(root, readme))
    front = '\n'.join(lines[:38]).lower()
    for token in ('product', 'software', 'repository', 'not', 'python'):
        if token not in front:
            errors.append('first-read-missing:' + token)
    title = '# CORA — Continuous Ontological Repository Assurance'
    marker = '<!-- programme-header:v2 -->'
    legacy = readme.startswith(title)
    header, separator, body = readme.partition('\n\n')
    # The original title-first source remains a valid historical test fixture.
    v2 = (separator != '' and header.startswith(marker)
          and readme.count(marker) == 1
          and all(token in header for token in (
              'Luke883i/academics', 'Luke883i/ROA', 'Luke883i/cora',
              'Repository-local code, evidence, and governance remain authoritative'))
          and body.startswith(title))
    if not (legacy or v2):
        errors.append('full-product-name-missing')
    if '**CORA (Continuous Ontological Repository Assurance)**' not in readme:
        errors.append('first-read-acronym-expansion-missing')
    if not (legacy or v2):
        errors.append('missing-title')
    for heading in ('## First five minutes', '## What works', '## Operating boundaries', '## Engineering map'):
        if heading not in readme:
            errors.append('missing-section:' + heading)
    # PR42: README line count is editorial telemetry, not an engineering gate.
    # Source identity, first-screen context, actual links and package/CLI checks remain.
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
    # The README is a product storefront, not the CLI index. Compare the
    # exhaustive reference with the existing canonical parser inventory.
    if 'cora --help' not in readme:
        errors.append('missing-cli-discovery')
    reference = (root / 'docs/CLI_REFERENCE.md')
    if reference.is_file():
        found = re.findall(r'^- `([a-z][a-z0-9-]+)` —', reference.read_text('utf-8'), re.M)
        if sorted(found) != sorted(COMMANDS):
            errors.append('cli-reference-command-drift')
    else:
        errors.append('missing-cli-reference')
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
                      'checks': 'readme-first-read, cli, paths, ontology, package, regressions, cto-positioning',
                      'positioning': {
                          'verdict': 'SOURCE_CROSSCHECK_ONLY',
                          'sbom': 'GENERATED_IN_CANDIDATE_CI_SCOPED',
                          'independent_assurance': 'BLOCKED_EXTERNAL',
                          'release_authorization': 'NONE',
                          'enterprise_ready': False,
                      },
                      'errors': errors},
                     indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == '__main__':
    sys.exit(main())
