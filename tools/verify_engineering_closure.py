"""PR40 CORA-on-CORA: Git-bound engineering debt knowledge and finite falsifiers.

This tool reuses the original Git inventory, PR38 frozen genealogy, PR25/33
physical mutations and PR36-39 one-run/qualification without another executor.
AST call sites are STATIC RISK INDICATORS; no target code or external host is run.
Ten million inputs are bounded model vectors, not ten million Git commits.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

SCHEMA = "cora-engineering-knowledge/1"
CONTRACT = ".cora/contracts/dod/engineering-knowledge-dod.json"
BASE = "75827bfbd1d67f861e950c4802ccdd92e9c9a2e4"
SOURCE = (
    "S_GIT_IDENTITY", "S_FULL_SOURCE_CENSUS", "S_STATIC_DYNAMIC_BOUNDARIES",
    "S_TEMPORAL_DOC_TRUTH", "S_CI_FAIL_CLOSED", "S_GOVERNANCE_NONPROMOTION",
    "S_REUSED_HISTORY", "S_MODEL_AND_PHYSICAL_FALSIFIERS",
)
EXTERNAL = (
    "E_INDEPENDENT_RCA", "E_EFFECTIVE_HOST_PROTECTION",
    "E_INDEPENDENT_REVIEW", "E_MAINTAINED_TARGET_BEHAVIOR",
    "E_RUNTIME_USER_ACCEPTANCE",
)
EDGES = {
    "G_STATIC": list(SOURCE[:4]),
    "G_REPRO": [SOURCE[4], SOURCE[7]],
    "G_TRUTH": [SOURCE[5], SOURCE[6]],
    "G_SOURCE_EKC": ["G_STATIC", "G_REPRO", "G_TRUTH"],
    "G_EXTERNAL_EKC": list(EXTERNAL),
    "G_ENGINEERING_KNOWLEDGE": ["G_SOURCE_EKC", "G_EXTERNAL_EKC"],
}
FAULTS = (
    "CI_FAILED", "GIT_FIXTURE_FLAKY", "HOST_POLICY_MISSING",
    "REVIEW_NOT_AUTHENTICATED", "CURRENT_DOCUMENT_STALE",
    "DYNAMIC_IMPORT_UNOBSERVED", "RUNTIME_NOT_EXECUTED",
    "INDEPENDENT_ORACLE_ABSENT", "SYNTHETIC_CASE_PROMOTED",
    "MAINTAINED_TARGET_ABSENT", "HOST_ISOLATION_UNATTESTED",
    "RELEASE_ROLLBACK_UNATTESTED", "GIT_EVIDENCE_TAMPERED",
    "NEW_PATH_NOT_CATALOGUED",
)
SOURCE_FAULT_BITS = (0, 1, 4, 5, 6, 8, 12, 13)
SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
SAFE_PATH = re.compile(r"^[a-zA-Z0-9_./-]+$")
MASK64 = (1 << 64) - 1
CAMPAIGN = (0,) + tuple(
    sum(1 << bit for bit in combo)
    for size in (1, 2, 3, 4)
    for combo in itertools.combinations(range(14), size)
)
assert len(CAMPAIGN) == 1471
SOURCE_MASK = sum(1 << bit for bit in SOURCE_FAULT_BITS)


def git(repo: Path, *arguments: str, max_bytes: int = 12_000_000) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *arguments],
                          capture_output=True, timeout=35, check=False)
    if proc.returncode or len(proc.stdout) > max_bytes:
        raise ValueError("original Git command failed or exceeded bounded output")
    return proc.stdout


def source(repo: Path, sha: str, path: str) -> str:
    if not SAFE_PATH.fullmatch(path) or ".." in path.split("/"):
        raise ValueError("unsafe source witness path")
    return git(repo, "show", sha + ":" + path).decode("utf-8")


def canonical(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("utf-8")


def contract_at(repo: Path, sha: str) -> dict:
    doc = json.loads(source(repo, sha, CONTRACT))
    nodes = doc.get("nodes")
    all_ids = set(SOURCE) | set(EXTERNAL) | set(EDGES)
    if (doc.get("schema") != "cora-engineering-knowledge-dod/1"
            or doc.get("authority") != "NONE"
            or doc.get("product_status") != "BLOCKED_EXTERNAL"
            or doc.get("source_status") != "IMPLEMENTATION_CANDIDATE_NOT_ATTESTED"
            or doc.get("baseline_main") != BASE
            or doc.get("source_goal") != "G_SOURCE_EKC"
            or doc.get("global_goal") != "G_ENGINEERING_KNOWLEDGE"
            or doc.get("logic") != "NONCOMPENSATORY_AND"
            or doc.get("source") != list(SOURCE)
            or doc.get("external") != list(EXTERNAL)
            or doc.get("edges") != EDGES
            or not isinstance(nodes, list)
            or len(nodes) != len(all_ids)
            or {n.get("id") for n in nodes} != all_ids):
        raise ValueError("knowledge DoD authority, identity or coverage drift")
    for node in nodes:
        ident = node["id"]
        expected_scope = ("EXTERNAL" if ident in EXTERNAL or ident in
                          ("G_EXTERNAL_EKC", "G_ENGINEERING_KNOWLEDGE")
                          else "SOURCE")
        if (node.get("scope") != expected_scope
                or node.get("depends_on") != EDGES.get(ident, [])
                or node.get("status") != "NOT_ESTABLISHED_BY_DECLARATION"):
            raise ValueError("DoD mandatory scope/edge or assertion drift")
    metrics = doc.get("metrics", {})
    if (metrics.get("semantic_cases") != 10_000_000
            or metrics.get("sessions") != 10
            or metrics.get("cases_per_session") != 1_000_000
            or metrics.get("seeds") != [883,1387,2025,3347,4523,
                                        5801,6911,7927,8443,9829]
            or metrics.get("fault_families") != len(FAULTS)
            or metrics.get("preregistered_one_to_four_way_plus_control") != 1471
            or metrics.get("single_fault_coverage") != 14
            or metrics.get("pair_fault_coverage") != 91
            or metrics.get("max_mismatches") != 0
            or metrics.get("max_unsafe_promotions") != 0
            or metrics.get("real_source_mutations_in_model") != 0
            or metrics.get("exact_final_head_required") is not True):
        raise ValueError("knowledge semantic campaign thresholds drift")
    return doc


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return ""


def analyze(repo: Path, revision: str = "HEAD") -> dict:
    """Exact committed source/static inspection; dynamic behavior remains unknown."""
    repo = Path(repo).resolve(strict=True)
    sha = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    if not SHA.fullmatch(sha):
        raise ValueError("unknown original Git source identity")
    tree_sha = git(repo, "rev-parse", sha + "^{tree}").decode().strip()
    contract_at(repo, sha)
    raw = git(repo, "ls-tree", "-r", "--name-only", "-z", sha)
    paths = sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("duplicate or empty original Git tree")
    files = set(paths)
    modules = [p for p in paths if re.fullmatch(r"src/cora/[^/]+\.py", p)]
    tests = [p for p in paths if re.fullmatch(r"tests/test_[^/]+\.py", p)]
    tools = [p for p in paths if re.fullmatch(r"tools/[^/]+\.py", p)]
    workflows = [p for p in paths if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", p)]
    internal_dod = [p for p in paths if p.startswith(".cora/contracts/dod/") and p.endswith(".json")]
    imports, dynamic = [], []
    for path in modules:
        syntax = ast.parse(source(repo, sha, path), filename=path)
        for node in ast.walk(syntax):
            if isinstance(node, ast.ImportFrom) and node.level:
                possible = (("src/cora/" + node.module + ".py",)
                            if node.module else
                            tuple("src/cora/" + alias.name + ".py" for alias in node.names))
                for dep in possible:
                    if dep in files:
                        imports.append((path, dep))
            if isinstance(node, ast.Call):
                call = _call_name(node.func)
                if call in ("eval", "exec", "__import__", "getattr",
                            "importlib.import_module", "subprocess.run",
                            "subprocess.check_output", "subprocess.Popen",
                            "os.system", "os.popen"):
                    dynamic.append({"path": path, "line": node.lineno,
                                    "call": call, "status": "STATIC_CALLSITE_NOT_RUNTIME"})
    cli = ast.parse(source(repo, sha, "src/cora/cli.py"))
    parser = [node.args[0].value for node in ast.walk(cli)
              if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Attribute)
              and node.func.attr == "add_parser"
              and node.args and isinstance(node.args[0], ast.Constant)
              and isinstance(node.args[0].value, str)]
    atlas = json.loads(source(repo, sha, ".cora/assurance/capability-atlas.json"))
    if (len(parser) != 71 or len(set(parser)) != 71
            or set(parser) != {x["command"] for x in atlas["commands"]}):
        raise ValueError("CLI parser/atlas source identity mismatch")
    surfaces = atlas["repository_surfaces"]
    for key, actual in (("modules", modules), ("test_modules", tests),
                        ("operational_tools", tools),
                        ("github_workflows", workflows), ("internal_dod", internal_dod)):
        if surfaces.get(key) != actual:
            raise ValueError("knowledge atlas surface drift: " + key)
    history = json.loads(source(repo, sha, ".cora/assurance/history/pr01-37-commit-diff-audit.json"))
    if (history.get("pr_count") != 37 or history.get("unit_count") != 305
            or history.get("closed_unmerged_prs") != [34]):
        raise ValueError("original frozen PR38 historical witness drift")
    readme = source(repo, sha, "README.md")
    release = source(repo, sha, "docs/RELEASE.md")
    stale = [
        marker for marker, content in (
            ("README:PR38_CANDIDATE", readme),
            ("RELEASE:PR38_NEW_CANDIDATE", release))
        if ("The PR38 candidate" in content or
            "PR38 is a new source candidate" in content)
    ]
    if stale:
        raise ValueError("current documentation chronology drift: " + ",".join(stale))
    if "merged PR38" not in readme or "merged PR39" not in readme:
        raise ValueError("README lacks current merged source chronology")
    if "PR39 merged" not in release:
        raise ValueError("release status lacks PR39 merged/source-not-release distinction")
    report = {
        "schema": SCHEMA, "commit": sha, "tree": tree_sha,
        "source": "ORIGINAL_COMMITTED_GIT", "authority": "NONE",
        "status": "SOURCE_CENSUS_SCOPED_EXTERNAL_DEBT",
        "identity": {"product": "cora", "software": ["cora-engine",
                     "cora-release-verification"], "package": "cora-audit"},
        "counts": {"files": len(paths), "modules": len(modules), "tests": len(tests),
                   "tools": len(tools), "workflows": len(workflows),
                   "internal_dod": len(internal_dod), "cli": len(parser),
                   "static_import_edges": len(set(imports)),
                   "dynamic_callsite_indicators": len(dynamic)},
        "static_import_edges": [list(x) for x in sorted(set(imports))],
        "dynamic_callsites": sorted(dynamic, key=lambda d: (d["path"], d["line"], d["call"])),
        "debt_register": [
            {"id": "P0_CI_GIT_CLONE", "layer": "REPOSITORY",
             "state": "REQUIRES_EXACT_HEAD_CI_AND_INDEPENDENT_RCA",
             "witness": "tests/test_pr25_method_synthesis.py"},
            {"id": "P0_GITHUB_GOVERNANCE", "layer": "PRODUCT",
             "state": "BLOCKED_EXTERNAL_HOST_REQUIRED_CHECKS_AND_REVIEW",
             "witness": "tools/governance_readback.py"},
            {"id": "P1_TEMPORAL_DOCUMENTATION", "layer": "REPOSITORY",
             "state": "SOURCE_CHRONOLOGY_RECONCILED_NOT_REVIEWED",
             "witness": "docs/RELEASE.md"},
            {"id": "P1_DYNAMIC_DEPENDENCIES", "layer": "SOFTWARE",
             "state": "STATIC_CALLSITES_NOT_EXECUTION_COVERAGE",
             "witness": "src/cora/cli.py"},
            {"id": "P1_HISTORICAL_SCOPE", "layer": "REPOSITORY",
             "state": "PR01_37_FROZEN_PR38_39_NEED_SEPARATE_EXTENSION",
             "witness": ".cora/assurance/history/pr01-37-commit-diff-audit.json"},
            {"id": "P1_INDEPENDENT_BEHAVIOR", "layer": "PRODUCT",
             "state": "BLOCKED_EXTERNAL_REAL_MAINTAINED_TARGET",
             "witness": "tools/independent_git_oracle.py"},
            {"id": "P2_MODEL_SURVIVOR_SCOPE", "layer": "SOFTWARE",
             "state": "FINITE_MODEL_IS_NOT_PHYSICAL_GIT_FALSIFICATION",
             "witness": "src/cora/gold_saturation.py"},
            {"id": "P2_HOST_WORKFLOW_COVERAGE", "layer": "REPOSITORY",
             "state": "GITHUB_CHECKS_NOT_ENFORCEMENT",
             "witness": ".github/workflows/ci-semantic-lattice.yml"},
        ],
        "historical_scope": "FROZEN_PR01_37_NOT_A_CURRENT_PR_COUNT",
        "dynamic_execution": "NOT_EXECUTED_BY_STATIC_AUDIT",
        "current_ci": "MUST_BE_READ_FROM_EXTERNAL_EXACT_HEAD_GITHUB_CHECKS",
        "host_enforcement": "BLOCKED_EXTERNAL",
        "independent_approval": "NOT_ATTESTED",
        "product_qualified": False,
    }
    report["source_digest_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    return report


def verify_report(repo: Path, report: dict) -> bool:
    if (not isinstance(report, dict) or not SHA.fullmatch(str(report.get("commit", "")))
            or analyze(repo, report["commit"]) != report):
        raise ValueError("engineering knowledge report does not replay from original Git")
    return True


def mix64(n: int) -> int:
    x = (n + 0x9e3779b97f4a7c15) & MASK64
    x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & MASK64
    x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & MASK64
    return x ^ (x >> 31)


def _model(mask: int) -> tuple[str, str]:
    if type(mask) is not int or not 0 <= mask < 1 << len(FAULTS):
        raise ValueError("invalid engineering knowledge fault vector")
    blocked = any(mask & (1 << bit) for bit in SOURCE_FAULT_BITS)
    return ("SOURCE_DEBT_BLOCKED" if blocked else
            "MODEL_ELIGIBLE_UNATTESTED", "BLOCKED_EXTERNAL")


def _reference(mask: int) -> tuple[bool, bool]:
    """Separate finite Boolean specification; not a real-world behavioral oracle."""
    return (not any((mask // (2 ** bit)) % 2 for bit in
                    (0, 1, 4, 5, 6, 8, 12, 13)), False)


def stress(doc: dict, *, sessions: int = 10, cases_per_session: int = 1_000_000) -> dict:
    if (type(sessions) is not int or type(cases_per_session) is not int
            or not 1 <= sessions <= 10 or not 1471 <= cases_per_session <= 1_000_000):
        raise ValueError("bounded, catalog-complete semantic campaign required")
    seeds = doc["metrics"]["seeds"][:sessions]
    hashes, completed, mismatches, unsafe = [], 0, 0, 0
    for seed in seeds:
        digest = hashlib.sha256()
        seen = set()
        for i in range(cases_per_session):
            mask = (CAMPAIGN[i] if i < len(CAMPAIGN) else
                    CAMPAIGN[mix64(seed ^ i) % len(CAMPAIGN)])
            seen.add(mask)
            model_status, governed = _model(mask)
            ref_source, ref_governed = _reference(mask)
            eligible = model_status == "MODEL_ELIGIBLE_UNATTESTED"
            if eligible != ref_source:
                mismatches += 1
            if governed != "BLOCKED_EXTERNAL" or ref_governed or (
                    mask & SOURCE_MASK and eligible):
                unsafe += 1
            digest.update(mask.to_bytes(2, "big") + bytes((int(eligible),)))
        if len(seen) != len(CAMPAIGN):
            mismatches += 1
        hashes.append(digest.hexdigest())
        completed += cases_per_session
    aggregate = hashlib.sha256(b"".join(bytes.fromhex(x) for x in hashes)).hexdigest()
    full = sessions == 10 and cases_per_session == 1_000_000
    return {
        "schema": "cora-engineering-knowledge-stress/1",
        "status": ("PASS_SCOPED_FINITE_MODEL" if full and not mismatches and not unsafe
                   else "REFUTED" if mismatches or unsafe else "PARTIAL_FINITE_MODEL"),
        "cases": completed, "sessions": sessions, "cases_per_session": cases_per_session,
        "seeds": seeds, "fault_families": list(FAULTS),
        "preregistered_masks": len(CAMPAIGN), "observed_singles": len(FAULTS),
        "observed_pairs": len(FAULTS) * (len(FAULTS) - 1) // 2,
        "mismatches": mismatches, "unsafe_promotions": unsafe,
        "session_sha256": hashes, "aggregate_sha256": aggregate,
        "real_git_mutants": 0, "external_target_execution": "NOT_EXECUTED",
        "host_and_reviewer": "BLOCKED_EXTERNAL", "authorization": "NONE",
        "scope": "10M repeatable finite-model vectors (not unique or physical source mutations)",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--revision", default="HEAD")
    p.add_argument("--output", type=Path)
    p.add_argument("--verify-report", type=Path)
    p.add_argument("--stress-10m", action="store_true")
    args = p.parse_args()
    try:
        if args.verify_report:
            record = json.loads(args.verify_report.read_text("utf-8"))
            verify_report(args.repo, record)
            result = {"status": "SOURCE_REPLAY_SCOPED", "commit": record["commit"],
                      "authority": "NONE", "product": "BLOCKED_EXTERNAL"}
        else:
            result = analyze(args.repo, args.revision)
            if args.stress_10m:
                contract = contract_at(args.repo, result["commit"])
                result["finite_model"] = stress(contract)
                if result["finite_model"]["status"] != "PASS_SCOPED_FINITE_MODEL":
                    raise ValueError("10M source model did not satisfy preregistered checks")
        output = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(output, "utf-8")
        else:
            print(output, end="")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(type(exc).__name__ + ": " + str(exc))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
