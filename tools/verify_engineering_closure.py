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
        required_proof = ("INDEPENDENT_OPERATOR_REQUIRED" if expected_scope == "EXTERNAL"
                          else "EXACT_GIT_AND_EXECUTION_REQUIRED")
        if (node.get("scope") != expected_scope
                or node.get("depends_on") != EDGES.get(ident, [])
                or node.get("proof") != required_proof
                or (ident in EXTERNAL and node.get("witness_paths"))
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
            or metrics.get("exact_final_head_required") is not True
            or metrics.get("required_python") != ["3.11", "3.13"]):
        raise ValueError("knowledge semantic campaign thresholds drift")
    mandatory_nonclaims = {
        "FINITE_CASES_ARE_NOT_TEN_MILLION_GIT_MUTATIONS",
        "GIT_REPLAY_IS_NOT_REAL_TARGET_BEHAVIOR",
        "STATIC_AST_IS_NOT_DYNAMIC_RUNTIME_COVERAGE",
        "CI_GREEN_IS_NOT_HOST_ENFORCEMENT",
        "SOURCE_CANDIDATE_IS_NOT_REVIEWER_APPROVAL",
        "RCA_NOT_ESTABLISHED_BY_A_WORKAROUND",
        "GITHUB_403_IS_NOT_NO_PROTECTION",
        "NO_AUTO_MERGE_DEPLOY_PUBLICATION_OR_DELETION",
    }
    disclaimers = doc.get("nonclaims")
    if (not isinstance(disclaimers, list) or len(disclaimers) != len(mandatory_nonclaims)
            or set(disclaimers) != mandatory_nonclaims):
        raise ValueError("source/external negative boundary claims removed")
    return doc


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return prefix + "." + node.attr if prefix else node.attr
    return ""



def structural_units(code: str, path: str, test_only: bool = False) -> list[dict]:
    """AST-declared units; neither executable coverage nor inferred behavior."""
    syntax = ast.parse(code, filename=path)
    rows = []
    def visit(node: ast.AST, owner: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = owner + child.name
                if not test_only or child.name.startswith("test_"):
                    rows.append({
                        "symbol": name,
                        "kind": "CLASS" if isinstance(child, ast.ClassDef) else
                                "ASYNC_DEF" if isinstance(child, ast.AsyncFunctionDef) else "DEF",
                        "line": child.lineno,
                        "evidence": "AST_DECLARATION_NOT_EXECUTION",
                    })
                visit(child, name + ".")
            else:
                visit(child, owner)
    visit(syntax, "")
    return sorted(rows, key=lambda row: (row["line"], row["symbol"]))


def static_test_consumers(repo: Path, sha: str, tests: list[str],
                          modules: list[str]) -> list[tuple[str, str]]:
    """Candidate import edges, not proof that a test exercised a behavior."""
    known = set(modules)
    edges: set[tuple[str, str]] = set()
    for test_path in tests:
        syntax = ast.parse(source(repo, sha, test_path), filename=test_path)
        for node in ast.walk(syntax):
            candidates = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names
                                  if alias.name.startswith("cora."))
            elif isinstance(node, ast.ImportFrom):
                prefix = node.module or ""
                if prefix == "cora":
                    candidates.extend("cora." + alias.name for alias in node.names)
                elif prefix.startswith("cora."):
                    candidates.append(prefix)
            for qualified in candidates:
                parts = qualified.split(".")
                if len(parts) < 2:
                    continue
                target = "src/cora/" + parts[1] + ".py"
                if target in known:
                    edges.add((test_path, target))
    return sorted(edges)


def contribution_index(paths: list[str], modules: list[str], tools: list[str],
                       tests: list[str], imports: list[tuple[str, str]],
                       atlas: dict, test_imports: list[tuple[str, str]] | None = None,
                       units: dict[str, list[dict]] | None = None,
                       test_units: dict[str, list[dict]] | None = None) -> dict:
    """Source contribution graph, NOT causal ablation or safe-deletion evidence.

    Every tracked path is accounted for. The directed import graph only records
    literal, existing Python relative imports discovered by analyze(); missing
    static edges never imply no runtime caller or substitutability.
    """
    if (len(paths) != len(set(paths)) or "src/cora/cli.py" not in modules
            or not set(modules + tools + tests).issubset(set(paths))):
        raise ValueError("component denominator or entrypoint invalid")
    modules_set, tools_set, tests_set = set(modules), set(tools), set(tests)
    if units is not None and set(units) != modules_set:
        raise ValueError("module symbol census is incomplete")
    if test_units is not None and set(test_units) != tests_set:
        raise ValueError("test symbol census is incomplete")
    edges = {src: set() for src in modules}
    incoming = {src: set() for src in modules}
    for caller, callee in imports:
        if caller not in modules_set or callee not in modules_set:
            raise ValueError("static edge references missing module")
        edges[caller].add(callee)
        incoming[callee].add(caller)

    entrypoint = "src/cora/cli.py"
    direct = set(edges[entrypoint])
    reachable = {entrypoint}
    frontier = [entrypoint]
    while frontier:
        current = frontier.pop()
        for callee in sorted(edges[current] - reachable):
            reachable.add(callee)
            frontier.append(callee)

    by_test_import: dict[str, set[str]] = {src: set() for src in modules}
    for consumer, target in (test_imports or []):
        if consumer not in tests_set or target not in modules_set:
            raise ValueError("test import edge references missing source")
        by_test_import[target].add(consumer)

    by_command: dict[str, set[str]] = {src: set() for src in modules}
    by_family: dict[str, set[str]] = {src: set() for src in modules}
    by_witness: dict[str, set[str]] = {src: set() for src in modules}
    commands = atlas.get("commands")
    if not isinstance(commands, list):
        raise ValueError("component CLI method atlas unavailable")
    for binding in commands:
        source = binding.get("method_source")
        witness = binding.get("test_source")
        command = binding.get("command")
        if (source not in modules_set or witness not in tests_set
                or not isinstance(command, str) or not command):
            raise ValueError("component command has missing source/test witness")
        by_command[source].add(command)
        family = binding.get("family")
        if not isinstance(family, str) or not family:
            raise ValueError("command taxonomy is missing")
        by_family[source].add(family)
        by_witness[source].add(witness)

    rows = []
    for path in paths:
        if path in modules_set:
            kind = "PYTHON_MODULE"
            if path == entrypoint:
                state = "ENTRYPOINT"
            elif path in direct:
                state = "DIRECT_CLI_IMPORT"
            elif path in reachable:
                state = "TRANSITIVE_CLI_IMPORT"
            else:
                state = "NOT_OBSERVED_STATIC"
            if by_family[path] == {"finite-models"}:
                declared_role = "FINITE_MODEL_ASSURANCE_DECLARED_NOT_RUNTIME_VALIDATED"
            elif by_command[path]:
                declared_role = "CLI_COMMAND_SOURCE_DECLARED_NOT_RUNTIME_VALIDATED"
            else:
                declared_role = "NON_COMMAND_SUPPORT_SOURCE_CONSUMERS_INCOMPLETE"
            row = {
                "path": path, "surface": kind, "cli_static": state,
                "declared_capability_role": declared_role,
                "declared_families": sorted(by_family[path]),
                "imports": sorted(edges[path]), "imported_by": sorted(incoming[path]),
                "declared_units": (units or {}).get(path, []),
                "declared_commands": sorted(by_command[path]),
                "declared_test_witnesses": sorted(by_witness[path]),
                "static_test_import_candidates": sorted(by_test_import[path]),
                "consumer_status": "STATIC_CANDIDATES_DYNAMIC_UNKNOWN",
                "causal_effect": "NOT_MEASURED",
                "consolidation": "NOT_AUTHORIZED_UNTESTED",
            }
        else:
            if path in tools_set:
                kind = "OPERATIONAL_TOOL_SOURCE"
            elif path in tests_set:
                kind = "TEST_SOURCE"
            elif path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
                kind = "CI_DECLARATION"
            elif path.endswith(".md"):
                kind = "DOCUMENTATION_SOURCE"
            elif path.startswith(".cora/contracts/"):
                kind = "CONTRACT_SOURCE"
            else:
                kind = "OTHER_TRACKED_SOURCE"
            row = {
                "path": path, "surface": kind, "cli_static": "NOT_APPLICABLE",
                "test_cases": (test_units or {}).get(path, []) if path in tests_set else [],
                "causal_effect": "NOT_MEASURED",
                "consolidation": "NOT_AUTHORIZED_UNTESTED",
            }
        rows.append(row)
    reach = Counter(row["cli_static"] for row in rows if row["surface"] == "PYTHON_MODULE")
    metrics = {
        "tracked_paths": len(paths),
        "indexed_paths": len(rows),
        "python_modules": len(modules),
        "source_tools": len(tools),
        "test_sources": len(tests),
        "entrypoint_modules": reach["ENTRYPOINT"],
        "direct_cli_imports": reach["DIRECT_CLI_IMPORT"],
        "transitive_cli_imports": reach["TRANSITIVE_CLI_IMPORT"],
        "not_observed_static": reach["NOT_OBSERVED_STATIC"],
        "command_source_bindings": len(commands),
        "module_declarations": sum(len(v) for v in (units or {}).values()),
        "test_case_declarations": sum(len(v) for v in (test_units or {}).values()),
        "modules_with_symbol_census": len(units or {}),
        "tests_with_symbol_census": len(test_units or {}),
        "static_test_import_edges": sum(len(values) for values in by_test_import.values()),
        "modules_with_static_test_import_candidate": sum(
            bool(by_test_import[path]) for path in modules),
        "finite_model_assurance_declared_modules": sum(
            by_family[p] == {"finite-models"} for p in modules),
        "non_finite_cli_declared_modules": sum(
            bool(by_command[p]) and by_family[p] != {"finite-models"} for p in modules),
        "modules_without_declared_cli_witness": sum(
            not by_command[path] for path in modules),
        "causal_effects_measured": 0,
        "safe_consolidations_attested": 0,
    }
    if (metrics["finite_model_assurance_declared_modules"]
            + metrics["non_finite_cli_declared_modules"]
            + metrics["modules_without_declared_cli_witness"] != len(modules)):
        raise ValueError("declared source capability categories overlap or omit modules")
    if (metrics["indexed_paths"] != metrics["tracked_paths"]
            or sum(reach.values()) != len(modules)
            or reach["ENTRYPOINT"] != 1):
        raise ValueError("component source coverage incomplete")
    return {
        "schema": "cora-component-contribution/1",
        "scope": "ORIGINAL_GIT_STATIC_SOURCE_NOT_ABLATION",
        "authority": "NONE",
        "metrics": metrics,
        "rows": rows,
        "global_consolidation": "BLOCKED_EXTERNAL_BEHAVIORAL_PARITY_AND_GOVERNED_REVIEW",
    }


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
    # Product/software/repository truth is current; original Git is the historical oracle.
    if not all(token in readme for token in (
            "**Product:** assurance",
            "**Software:** `cora-engine` and `cora-release-verification`",
            "**Repository:** source, tests, CI and **historical ADRs**")):
        raise ValueError("README current product/software/repository boundaries missing")
    # Review the current operator contract, not the wording of a historical PR.
    # Neither a merged source commit nor a source test is publication authority.
    if not all(token in release for token in (
            "The authoritative candidate identity is the exact Git HEAD",
            "**Release = BLOCKED_EXTERNAL**",
            "not a stable API")):
        raise ValueError("current release source identity / external gate missing")
    test_edges = static_test_consumers(repo, sha, tests, modules)
    module_units = {
        path: structural_units(source(repo, sha, path), path) for path in modules
    }
    test_units = {
        path: structural_units(source(repo, sha, path), path, test_only=True)
        for path in tests
    }
    contribution = contribution_index(
        paths, modules, tools, tests, imports, atlas,
        test_edges, module_units, test_units)
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
        "component_contribution": contribution,
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



# PR43: obligation change accounting. This extends the existing source verifier;
# a count, asserted status or changed DoD is never approval or behavioral proof.
CLOSURE_SCHEMA = "cora-obligation-delta/1"


def closure_inventory(repo: Path, revision: str) -> dict:
    """Read ALL committed DoD node occurrences from original Git, not the worktree."""
    commit = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    paths = git(repo, "ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    paths = sorted(p for p in paths if re.fullmatch(
        r"\.cora/contracts/dod/[a-zA-Z0-9_-]+\.json", p))
    if not paths:
        raise ValueError("no canonical DoD contracts at pinned Git revision")
    nodes = {}
    for path in paths:
        document = json.loads(source(repo, commit, path))
        rows = document.get("nodes")
        if not isinstance(rows, list) or not rows:
            raise ValueError("DoD has no inspectable node list: " + path)
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise ValueError("malformed DoD node: " + path)
            identity = path + "::" + row["id"]
            if identity in nodes:
                raise ValueError("duplicate node identity: " + identity)
            scope = row.get("scope", "UNCLASSIFIED")
            if not isinstance(scope, str):
                raise ValueError("invalid scope: " + identity)
            deps = row.get("depends_on", [])
            if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
                raise ValueError("invalid dependencies: " + identity)
            claim = next((row[k] for k in ("claim", "description", "title", "family")
                          if isinstance(row.get(k), str) and row[k].strip()), "")
            nodes[identity] = {
                "scope": scope, "status": str(row.get("status", "NOT_ASSERTED")),
                "depends_on": sorted(deps), "claim": claim.strip(),
                "source_path": path,
            }
    return {"commit": commit, "contracts": paths, "nodes": nodes}


def closure_change(before: dict, after: dict) -> dict:
    """Count changed obligations; never convert declarations into verified closures."""
    a, b = before["nodes"], after["nodes"]
    removed, added = sorted(set(a)-set(b)), sorted(set(b)-set(a))
    changed = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    external_promotions = sorted(k for k in a.keys() & b.keys()
        if a[k]["scope"] == "EXTERNAL" and b[k]["scope"] != "EXTERNAL")
    asserted_passes = sorted(k for k, value in b.items()
        if value["status"].upper().startswith(("PASS", "APPROV", "CLOSED", "ACCEPT"))
        and (k not in a or value["status"] != a[k]["status"]))
    # Same wording is a duplication hint, not a proof of semantic equivalence.
    words = {}
    for identity, row in b.items():
        normalized = " ".join(row["claim"].lower().split())
        if normalized:
            words.setdefault(normalized, []).append(identity)
    suspected_overlaps = [{"claims": sorted(ids), "phrase": phrase}
                          for phrase, ids in sorted(words.items()) if len(ids) > 1]
    return {
        "before_occurrences": len(a), "after_occurrences": len(b),
        "contract_growth": len(after["contracts"]) - len(before["contracts"]),
        "obligation_occurrence_growth": len(b)-len(a),
        "added": added, "removed_not_closed": removed, "changed": changed,
        "external_scope_promotions": external_promotions,
        "asserted_passes_not_verified": asserted_passes,
        "possible_duplicate_wording_not_merged": suspected_overlaps,
        "external_open_occurrences": sum(x["scope"] == "EXTERNAL" for x in b.values()),
        "verified_closures": 0,
        "closure_yield": None,
        "identity_boundary": "PATH_PLUS_NODE_ID; cross-contract meaning requires independent equivalence mapping",
        "evidence_boundary": "NO_INDEPENDENT_RUNTIME_OR_HOST_RECEIPTS_VALIDATED",
    }


def closure_delta(repo: Path, base: str, head: str = "HEAD") -> dict:
    repo = Path(repo).resolve(strict=True)
    before, after = closure_inventory(repo, base), closure_inventory(repo, head)
    if before["commit"] == after["commit"]:
        raise ValueError("closure comparison needs two distinct commits")
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor",
         before["commit"], after["commit"]], capture_output=True, timeout=30)
    if ancestor.returncode != 0:
        raise ValueError("base must be ancestor of head; no unrelated baseline comparison")
    counts = closure_change(before, after)
    return {
        "schema": CLOSURE_SCHEMA, "base": before["commit"], "head": after["commit"],
        "status": "REFUTED" if counts["external_scope_promotions"] else "PASS_SCOPED_ACCOUNTING",
        "counts": counts, "authority": "NONE",
        "product": "BLOCKED_EXTERNAL", "release_authorized": False,
        "qualification": "ACCOUNTING_ONLY_NOT_INDEPENDENT_EVIDENCE",
    }


def verify_closure_delta(repo: Path, report: dict) -> bool:
    if not isinstance(report, dict) or report.get("schema") != CLOSURE_SCHEMA:
        raise ValueError("closure report schema invalid")
    expected = closure_delta(repo, report["base"], report["head"])
    if expected != report:
        raise ValueError("closure delta does not replay from original Git")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--revision", default="HEAD")
    p.add_argument("--output", type=Path)
    p.add_argument("--verify-report", type=Path)
    p.add_argument("--stress-10m", action="store_true")
    p.add_argument("--closure-base", help="compare pinned Git DoDs against --revision; source accounting only")
    p.add_argument("--verify-closure", type=Path, help="replay a closure delta using original Git")
    args = p.parse_args()
    try:
        if args.verify_closure:
            record = json.loads(args.verify_closure.read_text('utf-8'))
            verify_closure_delta(args.repo, record)
            result = {'status': 'REFUTED' if record['status'] == 'REFUTED'
                      else 'REPLAYED_SOURCE_ONLY', 'base': record['base'],
                      'head': record['head'], 'authority': 'NONE'}
        elif args.closure_base:
            if args.stress_10m or args.verify_report:
                raise ValueError('closure accounting is separate from stress or knowledge replay')
            result = closure_delta(args.repo, args.closure_base, args.revision)
        elif args.verify_report:
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
        return 2 if result.get("status") == "REFUTED" else 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(type(exc).__name__ + ": " + str(exc))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
