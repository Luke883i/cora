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

def _full_change(repo: Path, commit: str, base: str) -> dict:
    """Exact original-Git diff, including rename source and destination.

    The caller's selected BASE is a declaration, never a GitHub PR-base
    attestation. NUL-delimited name-status protects legal newline paths.
    """
    from .evidence import HEX, valid_path
    if not isinstance(base, str) or not HEX.fullmatch(base):
        raise ValueError("change base must be an exact Git commit SHA")
    resolved = git(repo, "rev-parse", "--verify", "--end-of-options",
                   base + "^{commit}", max_output=256).decode("ascii").strip()
    if resolved != base:
        raise ValueError("change base must be a full resolved commit")
    git(repo, "merge-base", "--is-ancestor", base, commit, max_output=256)
    raw = git(repo, "diff", "--name-status", "-z", "--find-renames",
              base, commit, max_output=16 * 1024 * 1024)
    parts = raw.split(b"\0")
    if parts[-1:] != [b""]:
        raise ValueError("unterminated original Git diff")
    parts.pop()
    entries = []
    i = 0
    while i < len(parts):
        status = parts[i].decode("ascii")
        i += 1
        if (not status or status[0] not in "ACDMRTUXB"
                or (len(status) > 1 and
                    (status[0] not in "RC" or not status[1:].isdigit()))):
            raise ValueError("unrecognized Git change status")
        count = 2 if status[0] in "RC" else 1
        if i + count > len(parts):
            raise ValueError("incomplete original Git rename/copy")
        paths = [p.decode("utf-8", "strict") for p in parts[i:i + count]]
        if not all(valid_path(p) for p in paths):
            raise ValueError("unsupported original Git path")
        entries.append({"status": status, "paths": paths})
        i += count
    paths = sorted({p for entry in entries for p in entry["paths"]})
    raw_tree = git(repo, "ls-tree", "-rz", "--full-tree", commit,
                   max_output=32 * 1024 * 1024)
    docs = set()
    for obj in raw_tree.split(b"\0"):
        if not obj:
            continue
        mode_kind_oid, name = obj.split(b"\t", 1)
        mode = mode_kind_oid.split(b" ", 1)[0]
        p = name.decode("utf-8", "strict")
        if mode in (b"100644", b"100755") and _is_doc(p):
            docs.add(p)
    # Prefer current front doors and files actually changed; never invent a
    # CORA-specific path in a third-party target repository.
    preferred = ("README.md", "AGENTS.md", "CHANGELOG.md", "SECURITY.md",
                 "docs/ARCHITECTURE.md", "docs/INDEX.md", "docs/RELEASE.md")
    selected = [p for p in preferred if p in docs]
    selected += [p for p in paths if p in docs and p not in selected]
    selected += [p for p in sorted(docs) if p not in selected]
    # The bound is explicit: a partial list cannot claim complete coverage.
    surfaces = selected[:64]
    result = classify(paths)
    result["editorial_refactor"]["surfaces"] = surfaces if (
        result["editorial_refactor"]["state"] == "REVIEW_REQUIRED") else []
    result["editorial_refactor"]["candidate_coverage"] = "TRACKED_REGULAR_DOCUMENTS_ONLY"
    result["editorial_refactor"]["unlisted_tracked_documents"] = max(0, len(selected) - len(surfaces))
    for obligation in result["obligations"]:
        obligation["basis"] = "GIT_PATH_TRIGGER_ONLY"
        obligation["evidence"] = "NOT_ASSESSED_BY_THIS_PROJECTION"
    return {"schema": "cora-practice-obligations/2", "commit": commit,
            "change_base": base, "comparison": "EXPLICIT_BASE_TO_HEAD",
            "scope_authority": "CALLER_DECLARED_BASE_NOT_PR_HOST_ATTESTED",
            "path_changes": entries, **result,
            "proof_scope": "GIT_CHANGE_RANGE_NOT_RUNTIME_OR_SEMANTIC_COMPLETENESS"}


def project(repo: Path, commit: str, *, change_base: str | None = None) -> dict:
    """Git-pinned PR58 compatibility or explicit BASE..HEAD projection."""
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
    if change_base is not None:
        report = _full_change(repo, commit, change_base)
        report["digest"] = domain_hash("CORA:practice-obligations:2", report)
        return report
    classified = classify(paths)
    report = {"schema": SCHEMA, "commit": commit, "comparison":
              "FIRST_PARENT" if len(parents) > 1 else "ROOT",
              **classified, "proof_scope": "GIT_PATH_TRIGGER_ONLY_NOT_SEMANTIC_OR_RUNTIME_PROOF"}
    report["digest"] = domain_hash("CORA:practice-obligations:1", report)
    return report

def verify(repo: Path, report: dict) -> bool:
    if (not isinstance(report, dict) or
            report.get("schema") not in (SCHEMA, "cora-practice-obligations/2")
            or not isinstance(report.get("commit"), str)):
        raise ValueError("invalid practice receipt")
    base = report.get("change_base") if report["schema"].endswith("/2") else None
    if project(repo, report["commit"], change_base=base) != report:
        raise ValueError("practice report differs from Git source")
    return True
