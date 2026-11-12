"""Git-pinned engineering practice obligations; advisory, not another assurance bus.

A bounded, deterministic projection from changed paths to required investigation.
No runtime, external review, user experience or release is attested by this map.
"""
from __future__ import annotations

from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git

SCHEMA = "cora-practice-obligations/1"
# Archaeological sources PR48..57. Each practice is an obligation to obtain
# evidence, not an assertion that the evidence already exists.
PRACTICES = (
    ("P48_EDITORIAL_COMPRESSION", "48", "Product entrypoint: clarity, compression, correct audience and navigable evidence"),
    ("P49_ECOSYSTEM_IDENTITY", "49", "Standalone product identity and truthful programme cross-references"),
    ("P50_RETICULAR_TRANSFER", "50", "Backwards DoD and portable source-to-obligation-to-witness mapping"),
    ("P51_SINGLE_DOSSIER", "51", "Reuse the original One-Run and correlate witness with claim, no second engine"),
    ("P52_NATIVE_TARGET", "52", "Use real target-owned oracles and separate static from runtime outcomes"),
    ("P53_CROSS_DOCUMENT", "53", "Reconcile README, metadata, architecture, security, release and actual capability"),
    ("P54_STALE_IDENTITY", "54", "Reject mismatched version, commit and physical review-note identities"),
    ("P55_SUPPLY_CHAIN", "55", "Physical package hashes, scoped SBOM/SCA and unsigned provenance without promotion"),
    ("P56_NEGATIVE_ORACLES", "56", "Original Git replay, negative mutants and measured-cost validity"),
    ("P57_EVIDENCE_LEVELS", "57", "Distinguish L1 engineering, L2 experiments and optional external L3"),
)
DOC = ("README.md", "AGENTS.md", "CHANGELOG.md", "SECURITY.md", "GOVERNANCE.md")
def _is_doc(p: str) -> bool:
    return p in DOC or p.startswith("docs/") or p.endswith(".md")

def _is_engineering(p: str) -> bool:
    return p.startswith(("src/", "tests/", "tools/", ".github/", ".cora/")) or p == "pyproject.toml"

def _needs_release(p: str) -> bool:
    return p == "pyproject.toml" or "release" in p.lower() or p.startswith(".github/workflows/")

def classify(paths: list[str]) -> dict:
    """Pure classifier, suitable for negative mutation testing."""
    if not isinstance(paths, list) or any(not isinstance(p, str) or not p or
            p.startswith("/") or ".." in p.split("/") or "\\"
            in p or "\x00" in p for p in paths):
        raise ValueError("invalid changed paths")
    unique = sorted(set(paths))
    docs = any(_is_doc(p) for p in unique)
    code = any(_is_engineering(p) for p in unique)
    release = any(_needs_release(p) for p in unique)
    change = bool(unique)
    required = {
        "P48_EDITORIAL_COMPRESSION": change,
        "P49_ECOSYSTEM_IDENTITY": docs or code,
        "P50_RETICULAR_TRANSFER": change,
        "P51_SINGLE_DOSSIER": code,
        "P52_NATIVE_TARGET": code,
        "P53_CROSS_DOCUMENT": docs or code,
        "P54_STALE_IDENTITY": release,
        "P55_SUPPLY_CHAIN": release,
        "P56_NEGATIVE_ORACLES": change,
        "P57_EVIDENCE_LEVELS": change,
    }
    return {
        "changed_paths": unique,
        "obligations": [
            {"id": name, "origin_pr": int(pr), "requirement": requirement,
             "applicable": required[name],
             "state": "REQUIRES_AGENT_OR_OPERATOR_EVIDENCE" if required[name]
                      else "NOT_TRIGGERED_BY_PATH_HEURISTIC"}
            for name, pr, requirement in PRACTICES
        ],
        "editorial_refactor": {
            "state": "REVIEW_REQUIRED" if docs or code else "NOT_TRIGGERED",
            "surfaces": ["README.md", "docs/ARCHITECTURE.md", "docs/INDEX.md",
                         "SECURITY.md", "docs/RELEASE.md", "AGENTS.md"]
                        if docs or code else [],
            "decision": "Assess claim changes, audience, links and actual runtime truth; "
                        "edit only when evidence justifies it, never blindly rewrite."
        },
        "runtime_observed": False,
        "external_approval": "NONE",
    }

def project(repo: Path, commit: str) -> dict:
    """Inspect exact Git commit against its first parent (or root empty tree)."""
    repo = Path(repo)
    parents = git(repo, "rev-list", "--parents", "-n", "1", commit).decode().split()
    if not parents or parents[0] != commit:
        raise ValueError("invalid exact commit")
    args = ("diff-tree", "--no-commit-id", "--name-only", "-r", "--root",
            parents[1], commit) if len(parents) > 1 else (
            "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit)
    raw = git(repo, *args, max_output=1024 * 1024)
    try:
        paths = [p for p in raw.decode("utf-8").splitlines() if p]
    except UnicodeDecodeError as exc:
        raise ValueError("unsupported non-UTF8 changed paths") from exc
    classified = classify(paths)
    report = {"schema": SCHEMA, "commit": commit, "comparison":
              "FIRST_PARENT" if len(parents) > 1 else "ROOT",
              **classified, "proof_scope": "GIT_PATH_TRIGGER_ONLY_NOT_SEMANTIC_OR_RUNTIME_PROOF"}
    report["digest"] = domain_hash("CORA:practice-obligations:1", report)
    return report

def verify(repo: Path, report: dict) -> bool:
    if (not isinstance(report, dict) or report.get("schema") != SCHEMA or
            not isinstance(report.get("commit"), str) or
            project(repo, report["commit"]) != report):
        raise ValueError("practice report differs from Git source")
    return True
