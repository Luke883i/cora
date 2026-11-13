"""Strict source-only release readiness. No GitHub/reviewer/release attestation."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.error
from pathlib import Path
from cora.host_release import observe_github, original_git_dod, verify_expected_boundary
# Both executable-script and package-import entrypoints are supported.
# A standalone 'python tools/verify_release_readiness.py' has tools/ as sys.path[0].
try:
    from tools.release_verify import verify_release
except ModuleNotFoundError as exc:
    if exc.name != "tools":
        raise
    from release_verify import verify_release

NAME = "Continuous Ontological Repository Assurance"
REQUIRED = (
 "README.md","CHANGELOG.md","AGENTS.md","GOVERNANCE.md","SECURITY.md",
 "docs/CONTINUOUS_DEVELOPMENT.md",
 "docs/ARCHITECTURE.md","docs/archive/decisions/ADR-PR15.md","docs/archive/audits/AUDIT_PR15_MAIN.md",
 "docs/DOD_RELEASE_READINESS.md","docs/RELEASE.md",
 "pyproject.toml","src/cora/__init__.py","cora.ontology.json",
 "cora.artifact-roles.json",".cora/continuous-policy.json",
 ".github/CODEOWNERS",".github/workflows/ci-release-candidate.yml",
 ".github/workflows/ci-release-readiness.yml",
)
WORKFLOWS = (
 ".github/workflows/ci-release-candidate.yml",
 ".github/workflows/ci-release-readiness.yml",
)

def inspect_source(root: Path) -> dict:
    root = Path(root).resolve(strict=True)
    errors = []
    data = {}
    for rel in REQUIRED:
        p = root / rel
        if not p.is_file() or p.is_symlink():
            errors.append("MISSING_OR_SYMLINK:"+rel)
        elif p.stat().st_size > 1024 * 1024:
            errors.append("OVERSIZED_INPUT:"+rel)
        else:
            data[rel] = p.read_bytes()
    def txt(rel):
        try:
            return data.get(rel,b"").decode("utf-8")
        except UnicodeDecodeError:
            errors.append("INVALID_UTF8:"+rel)
            return ""
    readme = txt("README.md")
    product_title = "# CORA — "+NAME+"\n"
    marker = "<!-- programme-header:v2 -->"
    # Accept only the exact optional, non-authorizing research-program badge.
    # A free-form banner must not bypass the original product identity gate.
    badge = (
        '[![ROA Research Programme]'
        '(https://img.shields.io/badge/ROA-Research_Programme-1f6feb)]'
        '(https://github.com/Luke883i/academics)\n\n'
    )
    candidate = readme[len(badge):] if readme.startswith(badge) else readme
    legacy = readme.startswith(product_title)
    header, sep, body = candidate.partition("\n\n")
    v2 = (header.startswith(marker) and candidate.count(marker) == 1
          and bool(sep) and body.startswith(product_title)
          and all(t in header for t in (
            "Luke883i/academics", "Luke883i/ROA", "Luke883i/cora",
            "Repository-local code, evidence, and governance remain authoritative")))
    if not (legacy or v2):
        errors.append("PRODUCT_EXPANSION_MISSING")
    if "**CORA ("+NAME+")**" not in readme:
        errors.append("PRODUCT_FIRST_READ_IDENTITY_MISSING")
    if any(v not in readme for v in ("## First five minutes","## Operating boundaries",
            "docs/RELEASE.md","docs/CONTINUOUS_DEVELOPMENT.md","product","software",
            "repository","cora --help")):
        errors.append("README_CONTRACT_INCOMPLETE")
    # The README is the landing page; procedure and release controls belong
    # to independently checked, dedicated current source documents.
    continuous_doc = txt("docs/CONTINUOUS_DEVELOPMENT.md")
    release_doc = txt("docs/RELEASE.md")
    if any(token not in continuous_doc for token in ("dev-premerge", "dev-postmerge")):
        errors.append("CURRENT_CONTINUOUS_METHOD_INCOMPLETE")
    if any(token not in release_doc for token in ("1.0.0a4", "BLOCKED_EXTERNAL")):
        errors.append("CURRENT_RELEASE_METHOD_INCOMPLETE")
    if "For this first introduction the base has" in readme:
        errors.append("STALE_BOOTSTRAP_CLAIM")
    # PR42: a hard 180-line limit falsely rejects meaning-preserving formatting.
    # Preserve all technical README, version, release, policy and file safety gates.
    version = None
    try:
        prj = tomllib.loads(txt("pyproject.toml"))["project"]
        version = prj["version"]
        if (prj["name"]!="cora-audit" or not isinstance(version,str) or
            not re.fullmatch(r"1\.0\.0a[1-9][0-9]*",version) or
            prj["scripts"]!={"cora":"cora.cli:main"} or
            prj["dependencies"]!=[] or prj["requires-python"]!=">=3.11"):
            errors.append("PACKAGE_METADATA_DRIFT")
    except (KeyError,TypeError,ValueError):
        errors.append("PACKAGE_METADATA_INVALID")
    try:
        tree = ast.parse(txt("src/cora/__init__.py"))
        found = [n.value.value for n in tree.body if isinstance(n,ast.Assign)
                 and isinstance(n.value,ast.Constant)
                 and any(isinstance(t,ast.Name) and t.id=="__version__" for t in n.targets)]
        if found != [version] or version is None:
            errors.append("PACKAGE_INIT_VERSION_DRIFT")
    except (SyntaxError,AttributeError):
        errors.append("PACKAGE_INIT_INVALID")
    if version and any(version not in txt(p) for p in ("README.md","CHANGELOG.md","docs/RELEASE.md")):
        errors.append("RELEASE_VERSION_DOCUMENTATION_DRIFT")
    try:
        obj = json.loads(txt("cora.ontology.json"))
        if obj["schema"]!="cora-ontology/1" or {v["id"] for v in obj["products"]}!={"cora"} or {v["id"] for v in obj["software"]}!={"cora-engine","cora-release-verification"}:
            errors.append("PRODUCT_SOFTWARE_ONTOLOGY_DRIFT")
    except (ValueError,TypeError,KeyError):
        errors.append("PRODUCT_SOFTWARE_ONTOLOGY_INVALID")
    try:
        reg = json.loads(txt("cora.artifact-roles.json"))
        rules = {v["pattern"]:set(v["roles"]) for v in reg["rules"]}
        if reg["schema"]!="cora-artifact-roles/1":
            errors.append("ARTIFACT_ROLE_SCHEMA_DRIFT")
        if not {"DOCUMENTATION","PRODUCT_CONTRACT"}.issubset(rules.get("CHANGELOG.md",set())):
            errors.append("CHANGELOG_ROLE_MISSING")
        if not {"CONTRACT_VERIFIER","RELEASE_TOOL"}.issubset(rules.get("tools/verify_release_readiness.py",set())):
            errors.append("RELEASE_VERIFIER_ROLE_MISSING")
        if not {"FIXTURE","TEST"}.issubset(rules.get("tests/test_pr15_release_readiness.py",set())):
            errors.append("RELEASE_TEST_ROLE_MISSING")
    except (ValueError,KeyError,TypeError):
        errors.append("ARTIFACT_ROLE_CONTRACT_INVALID")
    try:
        p = json.loads(txt(".cora/continuous-policy.json"))
        if (p["schema"]!="cora-continuous-policy/1" or
            not {"MAINTAINER","INDEPENDENT_SECURITY_REVIEWER"}.issubset(p["required_human_roles"]) or
            not {".cora",".github/workflows","tools"}.issubset(p["high_risk_prefixes"])):
            errors.append("CONTINUOUS_POLICY_COVERAGE_DRIFT")
    except (ValueError,KeyError,TypeError):
        errors.append("CONTINUOUS_POLICY_INVALID")
    for rel in WORKFLOWS:
        raw = txt(rel)
        if (not re.search(r"(?m)^on:\s*$",raw) or
            not re.search(r"(?m)^\s+pull_request:\s*$",raw) or
            "contents: read" not in raw or "pull_request_target:" in raw or
            "id-token: write" in raw or
            not re.search(r"uses:\s+actions/checkout@[a-f0-9]{40}\b",raw) or
            not re.search(r"uses:\s+actions/setup-python@[a-f0-9]{40}\b",raw)):
            errors.append("WORKFLOW_SOURCE_POLICY_DRIFT:"+rel)
    # PR54: candidate review notes must use the current package version and
    # candidate Git SHA, not a stale (possibly successful) historical release.
    # Static source verification checks the declared producer/guards; the
    # workflow's grep lines also verify the emitted bytes at execution time.
    note_workflow = txt(".github/workflows/ci-release-candidate.yml")
    note_contract = (
        "printf 'CORA %s (alpha) — REVIEW CANDIDATE ONLY",
        '"$CORA_VERSION" "$EXPECTED_SHA" > dist/RELEASE_NOTES_REVIEW.txt',
        'grep -Fx "CORA $CORA_VERSION (alpha) — REVIEW CANDIDATE ONLY" dist/RELEASE_NOTES_REVIEW.txt',
        'grep -Fx "Exact commit: $EXPECTED_SHA" dist/RELEASE_NOTES_REVIEW.txt',
    )
    note_line = next((line for line in note_workflow.splitlines()
                      if "printf 'CORA %s (alpha)" in line), "")
    if (any(marker not in note_workflow for marker in note_contract)
            or (chr(92) * 2 + "n") in note_line
            or re.search(r"printf 'CORA [0-9]+[.][0-9]+[.][0-9]+a[0-9]+", note_workflow)):
        errors.append("REVIEW_NOTE_VERSION_OR_SHA_DRIFT")
    for rel in ("docs/archive/decisions/ADR-PR15.md","docs/RELEASE.md","docs/ARCHITECTURE.md"):
        if NAME not in txt(rel):
            errors.append("NAME_NOT_CONSISTENT:"+rel)
    for v in ("G-source","G-release","I1","I7","BLOCKED_EXTERNAL","L28"):
        if v not in txt("docs/DOD_RELEASE_READINESS.md"):
            errors.append("RELEASE_DOD_INCOMPLETE:"+v)
    # Three distinct source objects: a reviewable declaration, never a
    # self-issued enterprise certificate or host/release authority.
    boundaries = {
        "README.md": (
            "**Enterprise evaluation candidate, not enterprise-qualified.**",
            "**Product:**", "**Software:**", "**Repository:**",
            "Formal three-boundary DoD", "NOT_RUN", "BLOCKED_EXTERNAL"),
        "GOVERNANCE.md": (
            "## Product, software and repository — bounded closeout",
            "SOURCE_SCOPE_DEFINED", "IMPLEMENTED_SOURCE_SCOPED",
            "CANDIDATE_VERIFICATION_ONLY", "SOURCE_CONTROLS_DECLARED",
            "HOST_UNVERIFIED", "G-source = I1", "G-release = G-source",
            "authorization=NONE"),
        "docs/DOD_RELEASE_READINESS.md": (
            "## Three-boundary closeout interpretation",
            "Product `cora`", "cora-engine", "cora-release-verification",
            "repository `Luke883i/cora`", "I6 for effective host governance",
            "I7", "BLOCKED_EXTERNAL",
            "release_authorized=false", "authorization=NONE"),
        "docs/RELEASE.md": (
            "## Three-boundary closure and acceptance",
            "source closure", "release_status=BLOCKED_EXTERNAL",
            "release_authorized=false", "authorization=NONE"),
        "docs/ARCHITECTURE.md": (
            "Closure owner:", "governance decision record",
            "Module existence does not authenticate runtime"),
        "SECURITY.md": (
            "Repository visibility does not establish protected-branch controls",
            "no supported production release", "NOT_ATTESTED"),
    }
    for rel, tokens in boundaries.items():
        source = txt(rel)
        if any(token not in source for token in tokens):
            errors.append("CLOSURE_BOUNDARY_DRIFT:" + rel)
    # A signed-looking source statement never turns a local source verifier
    # into an authenticated host or release approver.
    forbidden = (
        "release_status=APPROVED", "release_authorized=true",
        "authorization=APPROVED", "HOST_VERIFIED_BY_SOURCE",
    )
    if any(term in txt(rel) for rel in boundaries for term in forbidden):
        errors.append("CLOSURE_UNEARNED_APPROVAL")
    source_closure_ok = not any(
        e.startswith(("CLOSURE_BOUNDARY_DRIFT:", "CLOSURE_UNEARNED_APPROVAL",
                      "PRODUCT_SOFTWARE_ONTOLOGY", "PACKAGE_METADATA",
                      "WORKFLOW_SOURCE_POLICY")) for e in errors)
    object_closeout = {
        "schema": "cora-source-object-closeout/1",
        "product": {"id": "cora", "state": "SOURCE_SCOPE_DEFINED"},
        "software": [
            {"id": "cora-engine", "state": "IMPLEMENTED_SOURCE_SCOPED"},
            {"id": "cora-release-verification",
             "state": "CANDIDATE_VERIFICATION_ONLY"},
        ],
        "repository": {"id": "Luke883i/cora",
                       "state": "SOURCE_CONTROLS_DECLARED"},
        "closure_status": ("SOURCE_CONTRACT_RECONCILED" if
                           source_closure_ok else "BLOCKED_SOURCE"),
        "runtime_target": "NOT_ATTESTED_BY_SOURCE",
        "host_protection": "HOST_UNVERIFIED",
        "independent_review": "BLOCKED_EXTERNAL",
        "enterprise_accepted": False,
        "authorization": "NONE",
    }
    return {
      "schema":"cora-release-source-readiness/1",
      "product_name":NAME,"distribution":"cora-audit","version":version,
      "source_scope":"WORKTREE_STATIC_UNPINNED_NOT_GITHUB_ATTESTATION",
      "input_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sorted(data.items())},
      "source_status":"PASS_SCOPED" if not errors else "BLOCKED_SOURCE",
      "source_errors":sorted(set(errors)),
      "object_closeout":object_closeout,
      "release_status":"BLOCKED_EXTERNAL",
      "external_obligations":["PROTECTED_MAIN_REQUIRED_CHECKS_NOT_ATTESTED",
         "INDEPENDENT_NON_AUTHOR_APPROVAL_NOT_ATTESTED",
         "TRUSTED_FINAL_SHA_CI_NOT_ATTESTED_BY_LOCAL_SCRIPT",
         "SIGNED_PROVENANCE_AND_RELEASE_MANAGER_NOT_ATTESTED",
         "REAL_REPOSITORY_PILOT_AND_NOVICE_HUMAN_VALIDATION_OPEN"],
      "release_authorized":False,"authorization":"NONE",
    }

def candidate_receipt(root: Path, revision: str, wheel: Path, sdist: Path,
                      verification: Path, external: Path) -> dict:
    """Exact Git source and binary candidate facts; NEVER approval or publication.

    Verification report and external test report are compared, not trusted as
    standalone authority. Independent signature, maintainer and deployment
    decisions cannot originate in this process.
    """
    root = Path(root).resolve(strict=True)
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("candidate must name full exact Git SHA")
    def call(*args):
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, timeout=20)
        if done.returncode:
            raise ValueError("candidate Git provenance unavailable")
        return done.stdout.strip()
    if call("rev-parse", "--verify", "HEAD") != revision:
        raise ValueError("candidate revision is not checkout HEAD")
    tree = call("rev-parse", "HEAD^{tree}")
    # A working-tree build cannot masquerade as a committed-source build.
    dirty = subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", "."],
                           timeout=20)
    if dirty.returncode:
        raise ValueError("tracked source differs from committed Git tree")
    actual = verify_release(Path(wheel), Path(sdist), root)
    declared = json.loads(Path(verification).read_text("utf-8"))
    if declared != actual:
        raise ValueError("verification receipt does not match independently recomputed binaries")
    validation = json.loads(Path(external).read_text("utf-8"))
    if (validation.get("schema") != "cora-external-validation/1"
            or validation.get("status") != "SCOPED_FIXTURES_PASS"
            or set(validation.get("distribution_forms", {})) != {"wheel", "sdist"}):
        raise ValueError("installed-fixture evidence missing or wrong identity")
    version = actual["version"]
    if (version not in ("1.0.0a4", "1.0.0a5")
            or Path(wheel).name != f"cora_audit-{version}-py3-none-any.whl"
            or Path(sdist).name != f"cora_audit-{version}.tar.gz"):
        raise ValueError("candidate distribution name/version differs from release plan")
    return {
        "schema": "cora-alpha-candidate-receipt/1",
        "source_commit": revision, "source_tree": tree,
        "distribution": actual["distribution"], "version": version,
        "artifact_sha256": {
            Path(wheel).name: actual["wheel_sha256"],
            Path(sdist).name: actual["sdist_sha256"],
        },
        "wheel_sdist_original_source_parity": "VERIFIED_SCOPED",
        "installed_fixture_status": "PRESEEDED_SYNTHETIC_FIXTURES_PASS_NOT_REAL_CONSUMER",
        "signed_provenance": "NOT_ATTESTED",
        "protected_main": "NOT_ATTESTED_BY_CANDIDATE",
        "independent_reviewer": "NOT_ATTESTED",
        "release_manager": "NOT_ATTESTED",
        "tag": "NOT_CREATED", "github_release": "NOT_PUBLISHED",
        "root_cause_postmerge": "NOT_ATTESTED",
        "external_gate": "BLOCKED_EXTERNAL",
        "authorization": "NONE", "publication_authorized": False,
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=Path("."))
    p.add_argument("--output",type=Path)
    p.add_argument("--require-release-approval",action="store_true")
    p.add_argument("--observe-host", action="store_true", help="Read-only live GitHub branch/ruleset/release observation")
    p.add_argument("--host-repository", help="owner/repo; validated before any network call")
    p.add_argument("--host-commit", help="full exact checkout HEAD SHA")
    p.add_argument("--host-tag", default="v1.0.0a4")
    p.add_argument("--host-pr-number", type=int, help="optional review subject for GitHub account evidence")
    p.add_argument("--host-output", type=Path, help="sanitized JSON; NEVER includes GITHUB_TOKEN")
    p.add_argument("--require-host-enforcement", action="store_true", help="return 3 when host checks remain unprotected")
    p.add_argument("--candidate-sha", help="Full exact Git SHA to be packaged")
    p.add_argument("--candidate-wheel", type=Path)
    p.add_argument("--candidate-sdist", type=Path)
    p.add_argument("--candidate-verification", type=Path)
    p.add_argument("--candidate-external", type=Path)
    p.add_argument("--candidate-output", type=Path, help="Review-only artifact manifest")
    a=p.parse_args(argv)
    try:
        report=inspect_source(a.repo)
    except OSError as exc:
        p.exit(2,"SOURCE INSPECTION ERROR: "+str(exc)+"\n")
    result=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if a.output:a.output.write_text(result,encoding="utf-8")
    else:sys.stdout.write(result)
    if report["source_status"]!="PASS_SCOPED":return 2
    if a.candidate_sha is not None:
        if (a.observe_host or a.candidate_output is None
                or not all((a.candidate_wheel, a.candidate_sdist,
                            a.candidate_verification, a.candidate_external))):
            p.exit(2,"CANDIDATE_BLOCKED: incomplete or ambiguous input\n")
        try:
            evidence = candidate_receipt(a.repo, a.candidate_sha,
                                         a.candidate_wheel, a.candidate_sdist,
                                         a.candidate_verification, a.candidate_external)
            a.candidate_output.write_text(
                json.dumps(evidence,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
            p.exit(2,"CANDIDATE_BLOCKED: "+type(exc).__name__+"\n")
    if a.observe_host:
        try:
            commit, cut = original_git_dod(a.repo)
            if a.host_commit != commit:
                raise ValueError("host observation must refer to exact checkout HEAD")
            host = observe_github(a.host_repository or "", commit,
                                  os.environ.get("GITHUB_TOKEN", ""),
                                  tag=a.host_tag, pr_number=a.host_pr_number)
            verify_expected_boundary(host)
            observed = {
                "schema": "cora-host-release-dossier/1",
                "commit": commit, "source_doD": cut,
                "host": host, "external_gate": "BLOCKED_EXTERNAL",
                "release_authorized": False, "authorization": "NONE",
                "provenance": "GITHUB_API_LIVE_READ_ONLY_AND_ORIGINAL_GIT_SOURCE_NOT_INDEPENDENT_APPROVAL",
            }
            rendered = json.dumps(observed, sort_keys=True, indent=2) + "\n"
            if a.host_output:
                a.host_output.write_text(rendered, encoding="utf-8")
            else:
                sys.stdout.write(rendered)
            if a.require_host_enforcement and not host["required_checks_enforced_observed"]:
                return 3
        except (ValueError, OSError, KeyError, urllib.error.URLError) as exc:
            p.exit(2, "HOST_OBSERVATION_BLOCKED: " + type(exc).__name__ + "\n")
    return 3 if a.require_release_approval else 0

if __name__=="__main__":
    raise SystemExit(main())
