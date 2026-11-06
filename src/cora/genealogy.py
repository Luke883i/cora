"""PR38: unit-granular historical Git evidence and non-deleting evolution assurance.

The GitHub PR metadata is a frozen *source observation*, not an independent
host witness. A missing import or old path is never permission to delete.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .git_snapshot import git

HISTORY = ".cora/assurance/history/pr01-37-commit-diff-audit.json"
DOD = ".cora/contracts/dod/history-convergence-dod.json"
BASE = "d214c71ce654c700edaaa418e6de8e7c7bab3738"
PR_COUNT, COMMIT_COUNT = 37, 305
CATEGORIES = frozenset((
    "CI_GOVERNANCE", "DOCUMENTATION", "ENGINE", "RELEASE", "TEST", "CONTRACT",
    "PRESENTATION", "TRUST_BOUNDARY", "VERIFIER_TOOL", "MIGRATION_OR_ARCHIVE"
))
LEAVES = tuple("S%02d_%s" % (i, name) for i, name in enumerate([
    "PR_CENSUS","COMMIT_CENSUS","FILE_DELTA_PROVENANCE","NONMERGED_TRUTH",
    "CURRENT_SOURCE_LINEAGE","NO_FALSE_DEAD_CODE","ARCHIVE_MIGRATION_COMPAT",
    "SINGLE_PRIMARY_ENTRY","CURRENT_HISTORICAL_DOCS",
    "FEATURE_DELTA_INVARIANTS","CANONICAL_CATALOGS","ATLAS_PR_COMMIT_NAV",
    "ATLAS_EVIDENCE_REFS","ATLAS_STATUS_NONPROMOTION","ORIGINAL_GIT_REPLAY",
    "REAL_AND_FINITE_FALSIFIERS","FINAL_SHA_CI","RETICULAR_CLOSURE_CHECK"
], 1))
EXTERNAL = (
    "E01_INDEPENDENT_CODE_REVIEW", "E02_REAL_TARGET_BENCHMARK",
    "E03_RUNTIME_ISOLATION_AND_ATTESTATION", "E04_NEW_USER_INTERPRETATION",
    "E05_HOST_RELEASE_ROLLBACK", "E06_DELETION_CONSUMER_READBACK"
)
EDGES = {
    "G_HISTORY_COVERAGE": list(LEAVES[:5]),
    "G_RETENTION_HARDENING": list(LEAVES[5:7]),
    "G_DOCUMENTATION_TRUTH": list(LEAVES[7:9]),
    "G_FUTURE_CONVERGENCE": list(LEAVES[9:11]),
    "G_ATLAS_FORENSICS": list(LEAVES[11:14]),
    "G_FALSIFIABLE_SOURCE": list(LEAVES[14:]),
    "G_HISTORY_CONVERGED_SOURCE": [
        "G_HISTORY_COVERAGE", "G_RETENTION_HARDENING",
        "G_DOCUMENTATION_TRUTH", "G_FUTURE_CONVERGENCE",
        "G_ATLAS_FORENSICS", "G_FALSIFIABLE_SOURCE"],
    "G_PRODUCT_CLOSURE": ["G_HISTORY_CONVERGED_SOURCE", *EXTERNAL],
}
SHA = re.compile(r"[0-9a-f]{40}")
ALLOWED_STATUS = frozenset(("added", "modified", "removed", "renamed",
                            "copied", "changed", "unchanged"))
DOD_SCHEMA = "cora-history-convergence-dod/1"
HISTORY_SCHEMA = "cora-history-reticular-audit/1"
REPORT_SCHEMA = "cora-history-genealogy-report/1"


def _source(repo: Path, sha: str, path: str, limit: int = 2_000_000) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
        raise ValueError("unsafe Git evidence filename")
    return git(repo, "show", sha + ":" + path,
               max_output=limit).decode("utf-8")


def _files(repo: Path, sha: str) -> set[str]:
    raw = git(repo, "ls-tree", "-r", "--name-only", "-z", sha,
              max_output=16_000_000)
    files = [x.decode("utf-8") for x in raw.split(b"\0") if x]
    if len(files) != len(set(files)) or not files:
        raise ValueError("Git history target inventory invalid")
    return set(files)


def _safe_path(path: object) -> bool:
    return (isinstance(path, str) and bool(path) and
            not path.startswith("/") and "\\" not in path and
            "\0" not in path and all(x not in (".", "..", "") for x in path.split("/")))


def _validate_dag(nodes: list[dict], goal: str) -> None:
    lookup = {n["id"]: n for n in nodes}
    seen: set[str] = set()
    visiting: set[str] = set()

    def walk(node: str) -> None:
        if node in visiting:
            raise ValueError("cycle in severe history DoD")
        if node in seen:
            return
        if node not in lookup:
            raise ValueError("unknown DoD obligation")
        visiting.add(node)
        for dep in lookup[node]["depends_on"]:
            walk(dep)
        visiting.remove(node)
        seen.add(node)

    walk(goal)
    if len(seen) != len(nodes):
        raise ValueError("unreachable history DoD nodes")


def verify_dod_document(doc: dict) -> bool:
    expected = set(LEAVES) | set(EXTERNAL) | set(EDGES)
    if (doc.get("schema") != DOD_SCHEMA or doc.get("authority") != "NONE"
            or doc.get("baseline_main") != BASE
            or doc.get("source_goal") != "G_HISTORY_CONVERGED_SOURCE"
            or doc.get("global_goal") != "G_PRODUCT_CLOSURE"
            or doc.get("semantics") != "BACKWARD_DERIVED_AND_NONCOMPENSATORY"
            or not isinstance(doc.get("nodes"), list)
            or len(doc["nodes"]) != 32 or
            {n.get("id") for n in doc["nodes"]} != expected):
        raise ValueError("severe history DoD identity/coverage drift")
    for node in doc["nodes"]:
        key = node["id"]
        scope = ("EXTERNAL" if key in EXTERNAL or key == "G_PRODUCT_CLOSURE"
                 else "SOURCE")
        if node.get("scope") != scope or node.get("depends_on") != EDGES.get(key, []):
            raise ValueError("severe history DoD scope or mandatory edge altered")
    if (doc.get("controls", {}).get("historical_pr_count") != PR_COUNT or
            doc["controls"].get("historical_commit_count") != COMMIT_COUNT or
            doc["controls"].get("nonmerged_prs") != [34] or
            doc["controls"].get("history_file") != HISTORY or
            doc["controls"].get("execution_boundary") != "PR37_SAFE_SOURCE_ONLY_DEFAULT"
            or len(doc.get("checklist", [])) != 24
            or len(doc.get("metrics", {})) != 14
            or doc.get("falsification", {}).get("cases") != 10000
            or doc.get("falsification", {}).get("seed") != 883):
        raise ValueError("history DoD threshold, safe executor, or mutation obligation relaxed")
    _validate_dag(doc["nodes"], "G_PRODUCT_CLOSURE")
    return True


def git_commit_headers(repo: Path) -> dict[str, tuple[str, list[str]]]:
    """Independent original-Git identity oracle: tree and parents for each reachable SHA."""
    output = git(repo, "log", "--format=%H %T %P", BASE,
                 max_output=15_000_000).decode("utf-8")
    parsed = {}
    for line in output.splitlines():
        fields = line.split(" ")
        if len(fields) >= 2 and SHA.fullmatch(fields[0]) and SHA.fullmatch(fields[1]):
            parsed[fields[0]] = (fields[1], fields[2:])
    if not parsed:
        raise ValueError("original Git history headers unavailable")
    return parsed


def verify_history_document(doc: dict, base_files: set[str],
                            *, git_headers: dict | None = None) -> bool:
    if (doc.get("schema") != HISTORY_SCHEMA
            or doc.get("base_main_commit") != BASE
            or doc.get("repository") != "Luke883i/cora"
            or doc.get("unit_count") != COMMIT_COUNT
            or doc.get("pr_count") != PR_COUNT
            or doc.get("merged_prs") != 36
            or doc.get("closed_unmerged_prs") != [34]
            or doc.get("original_main_paths") != len(base_files)
            or not isinstance(doc.get("prs"), list)
            or len(doc["prs"]) != PR_COUNT):
        raise ValueError("historical corpus identity, PR status, or Git path census drift")
    seen: set[str] = set()
    total = 0
    for expected_number, pr in enumerate(doc["prs"], 1):
        number = pr.get("number")
        if number != expected_number:
            raise ValueError("PR chronology incomplete or reordered")
        if (pr.get("merge_status") !=
                ("CLOSED_UNMERGED_HISTORICAL" if number == 34
                 else "MERGED_SOURCE_RECORDED")
                or (pr.get("merged_at") is None) != (number == 34)
                or not SHA.fullmatch(str(pr.get("head_sha")))
                or not isinstance(pr.get("commits"), list)
                or pr.get("commit_count") != len(pr["commits"])
                or not pr["commits"]):
            raise ValueError("PR34 nonmerge/PR metadata/commit census misrepresented")
        if pr["head_sha"] != pr["commits"][-1].get("sha"):
            raise ValueError("PR head no longer matches final historic commit")
        union: set[str] = set()
        total_changes = 0
        for idx, c in enumerate(pr["commits"]):
            if idx and pr["commits"][idx - 1]["sha"] not in c.get("parents", []):
                raise ValueError("commit genealogy broken inside PR")
            sha = c.get("sha")
            if (not isinstance(sha, str) or not SHA.fullmatch(sha)
                    or sha in seen or not SHA.fullmatch(str(c.get("tree")))
                    or not isinstance(c.get("parents"), list)
                    or not c["parents"] or any(
                        not SHA.fullmatch(str(x)) for x in c["parents"])
                    or not isinstance(c.get("subject"), str)
                    or not c["subject"]
                    or not isinstance(c.get("paths"), list)
                    or not c["paths"]):
                raise ValueError("malformed, duplicated or unparented commit")
            seen.add(sha)
            if git_headers is not None and sha in git_headers:
                original_tree, original_parents = git_headers[sha]
                if c["tree"] != original_tree or c["parents"] != original_parents:
                    raise ValueError("committed Git tree/parent lineage differs from original Git")
            stats = c.get("stats")
            if (not isinstance(stats, dict) or
                    any(type(stats.get(k)) is not int or stats[k] < 0
                        for k in ("total", "additions", "deletions"))
                    or stats["total"] != stats["additions"] + stats["deletions"]):
                raise ValueError("invalid commit-level change statistics")
            total_changes += stats["total"]
            paths: list[str] = []
            for file in c["paths"]:
                name = file.get("path")
                if (not _safe_path(name)
                        or file.get("status") not in ALLOWED_STATUS
                        or any(type(file.get(k)) is not int or file[k] < 0
                               for k in ("additions", "deletions"))
                        or (file.get("previous") is not None
                            and not _safe_path(file["previous"]))):
                    raise ValueError("malformed committed filename or changed-path metadata")
                paths.append(name)
            if len(set(paths)) != len(paths):
                raise ValueError("duplicate changed path in one commit")
            union.update(paths)
            live = {p for p in paths if p in base_files}
            absent = set(paths) - live
            if (set(c.get("currently_present_paths", [])) != live
                    or set(c.get("current_absent_or_relocated_paths", [])) != absent
                    or len(c["currently_present_paths"]) != len(live)
                    or len(c["current_absent_or_relocated_paths"]) != len(absent)
                    or c.get("commit_url") !=
                    "https://github.com/Luke883i/cora/commit/" + sha
                    or c.get("unit_epistemic_state") !=
                    "COMMIT_METADATA_AND_CHANGED_PATHS_OBSERVED_NOT_BEHAVIORAL_PROOF"
                    or not isinstance(c.get("semantic_domains"), list)
                    or not c["semantic_domains"]
                    or not set(c["semantic_domains"]) <= CATEGORIES
                    or not isinstance(c.get("required_witnesses"), list)
                    or "GIT_PARENT_TREE_DIFF_REPLAY" not in c["required_witnesses"]):
                raise ValueError("commit lineage, obligation or current-path classification forged")
        if (pr.get("distinct_touched_paths") != len(union)
                or pr.get("total_commit_changes") != total_changes
                or pr.get("current_present") != len(union & base_files)
                or pr.get("historical_or_relocated") != len(union - base_files)
                or pr.get("source_scope") !=
                "HISTORICAL_SOURCE_DIFF_METADATA_NOT_CURRENT_RUNTIME_ATTESTATION"):
            raise ValueError("PR net summary or source trust scope mutated")
        total += len(pr["commits"])
    if total != COMMIT_COUNT or len(seen) != COMMIT_COUNT:
        raise ValueError("full per-commit provenance not accounted")
    return True


def corpus_available(repo: Path, revision: str) -> bool:
    result = __import__("subprocess").run(
        ["git", "-C", str(repo), "cat-file", "-e", revision + ":" + HISTORY],
        stdout=__import__("subprocess").PIPE,
        stderr=__import__("subprocess").PIPE, timeout=30, check=False)
    return result.returncode == 0


def _delta(repo: Path, sha: str) -> dict:
    if sha == BASE:
        paths: list[str] = []
    else:
        proc = __import__("subprocess").run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", BASE, sha],
            capture_output=True, timeout=30, check=False)
        if proc.returncode:
            return {"status": "BASE_NOT_ANCESTOR_DEBT_BLOCKED",
                    "new_paths": [], "affected_paths": [],
                    "required_witnesses": ["BASE_AND_HEAD_LINEAGE_REQUIRED"]}
        raw = git(repo, "diff", "--name-only", "--no-renames", "-z", BASE, sha,
                  max_output=12_000_000)
        paths = sorted({b.decode("utf-8") for b in raw.split(b"\0") if b})
    required: set[str] = set()
    for path in paths:
        if path.startswith("src/"):
            required.update(("SOURCE_TEST_AND_ERROR_NEGATIVE",
                             "CAPABILITY_ATLAS_AND_ARTIFACT_ROLE"))
        if path.startswith(".github/"):
            required.update(("WORKFLOW_CENSUS_AND_EXACT_HEAD_CI",
                             "GITHUB_HOST_ENFORCEMENT_EXTERNAL"))
        if path.startswith("docs/") or path.endswith(".md"):
            required.update(("DOCUMENTATION_INDEX_AND_CLAIM_EVIDENCE",))
        if path.startswith(".cora/contracts/"):
            required.update(("DOD_EDGE_NEGATIVE_AND_CANONICAL_ROUTING",))
        if path.startswith("tests/"):
            required.update(("TEST_ORACLE_PROVENANCE_AND_REPLAY",))
        if path in ("src/cora/integrated_html.py", "src/cora/integrated_run.py"):
            required.update(("HTML_JSON_REPLAY_AND_ACCESSIBILITY",))
    # Future changes must appear in the *current* exact-Git catalogs,
    # without creating a second source of truth or a fixed 71/13 gate.
    atlas = json.loads(_source(repo, sha, ".cora/assurance/capability-atlas.json"))
    routes = json.loads(_source(repo, sha, ".cora/contracts/index.json"))
    catalog = atlas.get("repository_surfaces", {})
    registered_dods = {x["canonical"] for x in routes.get("bindings", [])
                       if x.get("scope") == "INTERNAL_DOD"}
    violations = []
    current_paths = _files(repo, sha)
    for path in paths:
        if path not in current_paths:
            continue  # Deletions demand independent consumers, not catalog membership.
        kind = ("modules" if re.fullmatch(r"src/cora/[^/]+\.py", path)
                else "test_modules" if re.fullmatch(r"tests/test_[^/]+\.py", path)
                else "github_workflows" if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path)
                else "internal_dod" if re.fullmatch(r"\.cora/contracts/dod/[^/]+\.json", path)
                else None)
        if kind and path not in catalog.get(kind, []):
            violations.append({"path": path, "code": "SURFACE_NOT_IN_CANONICAL_ATLAS"})
        if kind == "internal_dod" and path not in registered_dods:
            violations.append({"path": path, "code": "DOD_NOT_IN_CANONICAL_ROUTING"})
    return {
        "status": "SOURCE_CHANGED_NEW_FEATURES_REQUIRE_SEPARATE_WITNESSES"
                  if paths else "NO_GIT_DELTA_FROM_HISTORY_BASE",
        "affected_paths": paths,
        "required_witnesses": sorted(required),
        "catalog_violations": violations,
        "catalog_status": "DEBT_BLOCKED_UNREGISTERED" if violations else "SOURCE_CATALOG_COVERED_NOT_BEHAVIORAL_PROOF",
        "source_conclusion": "DEBT_BLOCKED_UNTIL_INDEPENDENT_REVIEW",
        "external": "BLOCKED_EXTERNAL",
    }


def build_genealogy(repo: Path, revision: str) -> dict:
    """Read only original Git commits; never execute discovered code or delete."""
    repo = Path(repo).resolve(strict=True)
    sha = git(repo, "rev-parse", "--verify", "--end-of-options",
              revision + "^{commit}", max_output=128).decode().strip()
    if not SHA.fullmatch(sha):
        raise ValueError("invalid genealogy revision")
    if not corpus_available(repo, sha):
        return {"schema": REPORT_SCHEMA, "commit": sha,
                "status": "NOT_AVAILABLE_BEFORE_PR38_BASELINE",
                "product_status": "BLOCKED_EXTERNAL",
                "authorization": "NONE"}
    dod = json.loads(_source(repo, sha, DOD))
    verify_dod_document(dod)
    data = json.loads(_source(repo, sha, HISTORY, limit=3_000_000))
    base_files = _files(repo, BASE)
    if (data.get("base_main_tree") !=
            git(repo, "rev-parse", BASE + "^{tree}",
                max_output=128).decode().strip()):
        raise ValueError("frozen historical source tree differs from original Git")
    headers = git_commit_headers(repo)
    verify_history_document(data, base_files, git_headers=headers)
    # Reachability is not a hosted PR review or runtime assertion.
    ancestors = set(headers)
    missing_merged = sorted(
        c["sha"] for p in data["prs"] if p["merge_status"] == "MERGED_SOURCE_RECORDED"
        for c in p["commits"] if c["sha"] not in ancestors)
    nonmerge = sorted(c["sha"] for p in data["prs"] if p["number"] == 34
                      for c in p["commits"])
    units = []
    per_pr = []
    old_paths = set()
    for pr in data["prs"]:
        segment = []
        for c in pr["commits"]:
            old_paths.update(c["current_absent_or_relocated_paths"])
            segment.append({
                "sha": c["sha"], "subject": c["subject"],
                "additions": c["stats"]["additions"],
                "deletions": c["stats"]["deletions"],
                "domains": c["semantic_domains"],
                "path_count": len(c["paths"]),
                "paths": [row["path"] for row in c["paths"]],
                "currently_present_paths": c["currently_present_paths"],
                "historical_or_relocated_paths": c["current_absent_or_relocated_paths"],
                "obligations": c["required_witnesses"],
                "unit_status": ("CLOSED_UNMERGED_NO_PRODUCT_CLAIM" if pr["number"] == 34
                                else "HISTORICAL_GIT_DIFF_NOT_CURRENT_RUNTIME"),
            })
        units.extend(segment)
        per_pr.append({
            "number": pr["number"], "title": pr["title"],
            "state": pr["merge_status"], "phase": pr["phase"],
            "commits": segment, "commit_count": len(segment),
            "domains": pr["domains"],
            "pr_url": pr["pr_url"],
        })
    # The 28 old paths are candidates for *path migration reconciliation*,
    # not signals that any current source module is unused.
    relocation_candidates = [{
        "old_path": p,
        "classification": ("HISTORICAL_DOC_ARCHIVE_PATH" if p.startswith("docs/")
                           else "FORMER_ROOT_CONTRACT_OR_PROFILE"),
        "action": "PRESERVE_OR_VERIFY_CANONICAL_MAPPING",
        "deletion_authorized": False, "independent_consumer_readback": "NOT_ATTESTED"
    } for p in sorted(old_paths)]
    result = {
        "schema": REPORT_SCHEMA, "commit": sha,
        "baseline_commit": BASE, "baseline_tree": data["base_main_tree"],
        "status": ("GIT_BOUND_HISTORY_WITH_OPEN_INDEPENDENT_DEBT"
                   if not missing_merged else "GIT_MERGED_COMMIT_REACHABILITY_DEBT"),
        "pr_count": len(per_pr), "commit_count": len(units),
        "merged_pr_count": 36, "closed_unmerged": [34],
        "merged_commits_missing_in_base_ancestry": missing_merged,
        "pr34_unmerged_commit_sha": nonmerge,
        "prs": per_pr, "retention": {
            "historical_or_relocated_count": len(relocation_candidates),
            "candidates": relocation_candidates,
            "safe_deletion": "NONE; INDEPENDENT_CONSUMER_AND_BEHAVIOR_ORACLE_REQUIRED",
            "current_source_modules_removal_authorized": 0,
        },
        "future_delta": _delta(repo, sha),
        "history_dod": {
            "source": "DEBT_BLOCKED_SOURCE_BENCHMARK_AND_FUTURE_CHECKS",
            "product": "BLOCKED_EXTERNAL",
            "contract_nodes": len(dod["nodes"]),
        },
        "proof_boundary": ("INDIVIDUAL_GIT_DIFF_METADATA_AND_BASE_TREE"
                           "_NOT_INDEPENDENT_RUNTIME_OR_MERGE_AUTHORITY"),
        "product_status": "BLOCKED_EXTERNAL", "authorization": "NONE",
    }
    return result
