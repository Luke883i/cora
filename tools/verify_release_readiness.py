"""Strict source-only release readiness. No GitHub/reviewer/release attestation."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

NAME = "Continuous Ontological Repository Assurance"
REQUIRED = (
 "README.md","CHANGELOG.md","AGENTS.md","GOVERNANCE.md",
 "docs/CONTINUOUS_DEVELOPMENT.md",
 "docs/ARCHITECTURE.md","docs/ADR-PR15.md","docs/AUDIT_PR15_MAIN.md",
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
    if not readme.startswith("# CORA — "+NAME+"\n"):
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
    if len(readme.splitlines()) > 180:
        errors.append("README_OVERSIZED")
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
    for rel in ("docs/ADR-PR15.md","docs/RELEASE.md","docs/ARCHITECTURE.md"):
        if NAME not in txt(rel):
            errors.append("NAME_NOT_CONSISTENT:"+rel)
    for v in ("G-source","G-release","I1","I7","BLOCKED_EXTERNAL","L28"):
        if v not in txt("docs/DOD_RELEASE_READINESS.md"):
            errors.append("RELEASE_DOD_INCOMPLETE:"+v)
    return {
      "schema":"cora-release-source-readiness/1",
      "product_name":NAME,"distribution":"cora-audit","version":version,
      "source_scope":"WORKTREE_STATIC_UNPINNED_NOT_GITHUB_ATTESTATION",
      "input_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sorted(data.items())},
      "source_status":"PASS_SCOPED" if not errors else "BLOCKED_SOURCE",
      "source_errors":sorted(set(errors)),
      "release_status":"BLOCKED_EXTERNAL",
      "external_obligations":["PROTECTED_MAIN_REQUIRED_CHECKS_NOT_ATTESTED",
         "INDEPENDENT_NON_AUTHOR_APPROVAL_NOT_ATTESTED",
         "TRUSTED_FINAL_SHA_CI_NOT_ATTESTED_BY_LOCAL_SCRIPT",
         "SIGNED_PROVENANCE_AND_RELEASE_MANAGER_NOT_ATTESTED",
         "REAL_REPOSITORY_PILOT_AND_NOVICE_HUMAN_VALIDATION_OPEN"],
      "release_authorized":False,"authorization":"NONE",
    }

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=Path("."))
    p.add_argument("--output",type=Path)
    p.add_argument("--require-release-approval",action="store_true")
    a=p.parse_args(argv)
    try:
        report=inspect_source(a.repo)
    except OSError as exc:
        p.exit(2,"SOURCE INSPECTION ERROR: "+str(exc)+"\n")
    result=json.dumps(report,sort_keys=True,indent=2)+"\n"
    if a.output:a.output.write_text(result,encoding="utf-8")
    else:sys.stdout.write(result)
    if report["source_status"]!="PASS_SCOPED":return 2
    return 3 if a.require_release_approval else 0

if __name__=="__main__":
    raise SystemExit(main())
