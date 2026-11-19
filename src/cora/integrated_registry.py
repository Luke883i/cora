"""Git-pinned universal CORA activity registry; inventory is not execution."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git
from .one_run import METHOD_FILES, _method_files, _original_dod
from .reticulum import ordered_cut

SCHEMA = "cora-integrated-activity-registry/2"
DOD = ".cora/contracts/dod/integrated-one-run-dod.json"
ATLAS = ".cora/assurance/capability-atlas.json"
# Exact immutable topology fingerprint; the contract JSON owns the node graph.
# Independent of ordering, this rejects omissions, substitutions and edge/scope drift.
DOD_GRAPH_DIGEST = "a10466976148b9ef2a7a3e4423e517f7296fc073433c1c93b7893aa4edeefe34"
REQUIRED = (
    "activity_id", "version", "owner_software", "source_paths", "entrypoint",
    "call_path", "input_contract", "output_contract", "dependencies",
    "effect_class", "authorization_policy", "execution_adapter",
    "verifier_id", "evidence_schema", "trust_class",
)
EFFECTFUL_CLI = {
    "apply-rename-doc": "REPOSITORY_WRITE",
    "guard-install": "REPOSITORY_WRITE",
    "file-decision": "LOCAL_EXECUTION",
    "annotate-groups": "LOCAL_EXECUTION",
    "runtime-observe": "LOCAL_EXECUTION",
    "gold-mutate": "LOCAL_EXECUTION",
    "zip-intake": "LOCAL_EXECUTION",
}
# Preserve the exact three effect classes of the existing Git-pinned interactions.
INTERACTION_EFFECT = {
    **dict.fromkeys(("OPTIONAL_UNTRUSTED_AI_HYPOTHESES PACKAGE_VERSION_ONLY "
        "SOURCE_ANALYSIS_OR_PROPOSAL SOURCE_OR_CLAIM_REPLAY_SCOPED "
        "SOURCE_PILOT_REQUIRES_AUTHORIZED_CHECKOUTS SYNTHETIC_MODEL_NOT_RUNTIME "
        "UNTRUSTED_WORKFLOW_TEXT_STATIC WORKTREE_NOT_IMMUTABLE_GIT").split(), "READ_ONLY"),
    **dict.fromkeys(("MUTATES_TARGET_AFTER_EXPLICIT_APPROVAL_AND_TEST "
        "WRITES_LOCAL_GUARD").split(), "REPOSITORY_WRITE"),
    **dict.fromkeys(("ANNOTATES_UNTRUSTED_AI_HYPOTHESES "
        "OPTIONAL_DOCKER_RUNTIME_UNATTESTED OPTIONAL_EXTRACTION_PRECHECK "
        "RECORDS_HUMAN_CLAIM_NOT_APPROVAL "
        "STAGED_PHYSICAL_MUTATIONS_OPTIONAL_DOCKER").split(), "LOCAL_EXECUTION"),
}
SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def _source(repo: Path, sha: str, path: str, limit: int = 1024 * 1024) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
        raise ValueError("unsafe registry source path")
    return git(repo, "show", sha + ":" + path, max_output=limit).decode("utf-8")


def tree_paths(repo: Path, sha: str) -> list[str]:
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError("registry requires exact Git commit")
    data = git(repo, "ls-tree", "-r", "--name-only", "-z", sha, max_output=16 * 1024 * 1024)
    paths = [x.decode("utf-8") for x in data.split(b"\0") if x]
    if len(paths) != len(set(paths)) or not paths:
        raise ValueError("invalid committed source inventory")
    return sorted(paths)


def _parser_commands(text: str) -> tuple[list[str], set[str]]:
    tree = ast.parse(text)
    names, dispatch = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                names.append(node.args[0].value)
        if not isinstance(node, ast.If):
            continue
        comparison = node.test
        if (not isinstance(comparison, ast.Compare) or len(comparison.ops) != 1
                or not isinstance(comparison.left, ast.Attribute)
                or comparison.left.attr != "cmd"
                or not isinstance(comparison.left.value, ast.Name)
                or comparison.left.value.id != "args"):
            continue
        right = comparison.comparators[0]
        if isinstance(comparison.ops[0], ast.Eq) and isinstance(right, ast.Constant) and isinstance(right.value, str):
            dispatch.add(right.value)
        elif isinstance(comparison.ops[0], ast.In) and isinstance(right, (ast.Tuple, ast.List)):
            dispatch.update(x.value for x in right.elts if isinstance(x, ast.Constant) and isinstance(x.value, str))
    # PR01 legacy fallback dispatch is the last else in main().
    if "validate_ledger(ledger)" in text and "snapshot(args.repo" in text:
        dispatch.add("verify-ledger")
    if len(names) != len(set(names)) or set(names) != dispatch:
        raise ValueError("CLI parser to dispatch mismatch: " + repr(sorted(set(names) ^ dispatch)))
    return sorted(names), dispatch


def _cases(text: str, path: str) -> list[tuple[str, int]]:
    root = ast.parse(text)
    items = []
    for node in root.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    items.append((node.name + "." + child.name, child.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            items.append((node.name, node.lineno))
    if len(items) != len({name for name, _ in items}):
        raise ValueError("duplicate declared test identifier: " + path)
    return sorted(items)


def verify_contract(repo: Path, sha: str) -> dict:
    """DoD structure and historical PR36 source are separate, noncompensatory."""
    doc = json.loads(_source(repo, sha, DOD))
    if (doc.get("schema") != "cora-integrated-one-run-dod/2"
            or doc.get("authority") != "NONE"
            or doc.get("source_goal") != "G_ONE_RUN_INTEGRATED_SOURCE"
            or doc.get("global_goal") != "G_ONE_RUN_PRODUCT"
            or doc.get("semantics") != "BACKWARD_DERIVED_AND_NONCOMPENSATORY"):
        raise ValueError("integrated DoD identity or authority drift")
    base = doc.get("baseline_pr36", {})
    if (base.get("immutable_node_count") != 27 or base.get("pr") != 36
            or base.get("schema") != "cora-one-run-dod/1"
            or base.get("main_commit") != "cfca7f5e6ab777d4aacf2c0989812925eb31b459"):
        raise ValueError("PR36 reference altered")
    if _original_dod(repo, sha)["nodes"] != 27:
        raise ValueError("PR36 original DoD not preserved")
    nodes = doc.get("nodes")
    if (not isinstance(nodes, list) or len(nodes) != 55
            or len({n.get("id") for n in nodes}) != len(nodes)
            or len(doc.get("checklist", [])) != 30
            or len(doc.get("metrics", {})) != 14
            or doc.get("activity_registry", {}).get("required_fields") != list(REQUIRED)):
        raise ValueError("integrated DoD node or registry contract drift")
    topology = sorted((n["id"], n["scope"], n["depends_on"]) for n in nodes)
    if domain_hash("CORA:integrated-dod-graph:2", topology) != DOD_GRAPH_DIGEST:
        raise ValueError("integrated DoD mandatory edge/scope drift")
    if any(n["id"].startswith("E_") and n.get("witness_paths") for n in nodes):
        raise ValueError("external acceptance forged from source")
    if len(ordered_cut(nodes, "G_ONE_RUN_PRODUCT")) != len(nodes):
        raise ValueError("DoD orphan or cycle")
    return doc


def _activity(activity_id: str, kind: str, source: str,
              *, owner: str, entry: str, effect: str, adapter: str,
              policy: str, verifier: str, dependencies: list[str] | None = None,
              paths: list[str] | None = None, detail: str = "") -> dict:
    return {
        "activity_id": activity_id, "kind": kind, "version": 1,
        "owner_software": owner,
        "source_paths": paths if paths is not None else [source],
        "entrypoint": entry, "call_path": detail or "DECLARED_SOURCE_ONLY",
        "input_contract": "NOT_INFERRED_FROM_FILENAME",
        "output_contract": "NOT_INFERRED_FROM_FILENAME",
        "dependencies": dependencies or [], "effect_class": effect,
        "authorization_policy": policy, "execution_adapter": adapter,
        "verifier_id": verifier, "evidence_schema": "cora-integrated-attempt/2",
        "trust_class": "GIT_SOURCE",
    }


def build_registry(repo: Path, sha: str) -> dict:
    """Read *only* original Git, reconcile 71 parser/atlas commands and all discovery classes."""
    repo = Path(repo).resolve(strict=True)
    verify_contract(repo, sha)
    paths = tree_paths(repo, sha)
    files = set(paths)
    cli_text = _source(repo, sha, "src/cora/cli.py")
    parsed, dispatched = _parser_commands(cli_text)
    atlas = json.loads(_source(repo, sha, ATLAS))
    commands = atlas.get("commands")
    if (atlas.get("schema") != "cora-capability-atlas/1"
            or atlas.get("authority") != "NONE" or not isinstance(commands, list)):
        raise ValueError("invalid capability atlas provenance")
    by_name = {row["command"]: row for row in commands}
    if len(by_name) != len(commands) or set(parsed) != set(by_name):
        raise ValueError("registered 71-command inventory not equal to original parser")
    # Same implementation, same declared test file: no independent binding table.
    test_by_source = {}
    for row in commands:
        source, test = row["method_source"], row["test_source"]
        if source in test_by_source and test_by_source[source] != test:
            raise ValueError("inconsistent test source for shared owner: " + source)
        if not test.startswith("tests/test_") or not test.endswith(".py"):
            raise ValueError("declared test source must be a test suite: " + test)
        test_by_source[source] = test
    items = []
    for name in parsed:
        row = by_name[name]
        source, test = row["method_source"], row["test_source"]
        if source not in files or test not in files:
            raise ValueError("command source or test witness absent: " + name)
        effect = EFFECTFUL_CLI.get(name, "READ_ONLY")
        expected_effect = INTERACTION_EFFECT.get(row["interaction"])
        if expected_effect != effect:
            raise ValueError("unsafe CLI reclassification: " + name)
        items.append(_activity("cli:" + name, "CLI_COMMAND", source,
            owner="cora-engine", entry="cora " + name, effect=effect,
            adapter="NOT_AUTO_EXECUTABLE", policy="INDIVIDUAL_INVOCATION_ONLY",
            verifier="NOT_INDEPENDENTLY_REGISTERED", paths=["src/cora/cli.py", source, test],
            detail="PARSER_AND_DISPATCH_OBSERVED;NOT_INDIVIDUALLY_EXECUTED;"
                   "DECLARED_TEST_UNATTESTED;BEHAVIOR_UNATTESTED"))
    if METHOD_FILES != _method_files():
        raise ValueError("source method owner does not match executor")
    for name, source in sorted(METHOD_FILES.items()):
        if source not in files:
            raise ValueError("source executor missing: " + name)
        items.append(_activity("method:" + name, "INTERNAL_METHOD", source,
            owner="cora-engine", entry="process_suite." + name, effect="READ_ONLY",
            adapter="PR36_PROCESS_SUITE", policy="SOURCE_AUTOMATED",
            verifier="verify-process", detail="SAFE_SOURCE_METHOD",
            dependencies=[] if name == "git_snapshot" else ["method:git_snapshot"]))
    if {".cora/contracts/profiles/hforge-profile-v1.json",
            ".cora/contracts/dod/hforge-transplant-dod.json",
            "tools/hforge_profile.py"}.issubset(files):
        items.append(_activity("stage:hforge-source", "PROFILE_STAGE",
            "tools/hforge_profile.py", owner="cora-release-verification",
            entry="cora process-run --one-run --profile comprehensive",
            effect="READ_ONLY", adapter="INTEGRATED_SAFE_GIT_SOURCE",
            policy="AUTO_SOURCE_NATIVE_OPT_IN", verifier="verify-process",
            dependencies=["method:git_snapshot"],
            paths=["tools/hforge_profile.py",
                   ".cora/contracts/profiles/hforge-profile-v1.json",
                   ".cora/contracts/dod/hforge-transplant-dod.json"],
            detail="SOURCE_GIT_ONLY_NO_NATIVE_77_REPLAY"))
    for path in paths:
        if re.fullmatch(r"tools/[^/]+\.py", path):
            kind = ("VERIFIER" if path.startswith("tools/verify_")
                    else "BENCHMARK" if "benchmark" in path or "stress" in path
                    else "OPERATIONAL_TOOL")
            items.append(_activity("tool:" + path, kind, path,
                owner="cora-release-verification", entry="python " + path,
                effect="LOCAL_EXECUTION", adapter="NOT_AUTO_EXECUTABLE",
                policy="SEPARATE_OPERATOR_AUTHORIZATION",
                verifier="NOT_INDEPENDENTLY_REGISTERED"))
        elif re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path):
            items.append(_activity("workflow:" + path, "CI_WORKFLOW", path,
                owner="cora-release-verification", entry=path,
                effect="EXTERNAL_MUTATION", adapter="HOST_OBSERVATION_ONLY",
                policy="HOST_ENFORCEMENT_NOT_ATTESTED",
                verifier="EXTERNAL_HOST_REQUIRED"))
        elif re.fullmatch(r"tests/test_[^/]+\.py", path):
            items.append(_activity("suite:" + path, "TEST_SUITE", path,
                owner="cora-engine", entry="unittest discover:" + path,
                effect="LOCAL_EXECUTION", adapter="NOT_AUTO_EXECUTABLE",
                policy="EXPLICIT_OPT_IN_AND_TRUST_BOUNDARY",
                verifier="LOCAL_EXIT_NOT_INDEPENDENT_ORACLE"))
            cases = _cases(_source(repo, sha, path), path)
            if path in test_by_source.values() and not cases:
                raise ValueError("declared test source has no test cases: " + path)
            for name, lineno in cases:
                items.append(_activity("case:" + path + ":" + name,
                    "TEST_CASE", path, owner="cora-engine", entry=name,
                    effect="LOCAL_EXECUTION", adapter="NOT_AUTO_EXECUTABLE",
                    policy="EXPLICIT_OPT_IN_AND_TRUST_BOUNDARY",
                    verifier="LOCAL_EXIT_NOT_INDEPENDENT_ORACLE",
                    detail=path + ":" + str(lineno)))
        elif re.fullmatch(r"src/cora/[^/]+\.py", path):
            items.append(_activity("module:" + path, "SOFTWARE_MODULE", path,
                owner="cora-engine", entry=path, effect="READ_ONLY",
                adapter="SOURCE_REFERENCE_ONLY", policy="NOT_DIRECTLY_INVOKABLE",
                verifier="NOT_APPLICABLE_MODULE_IS_NOT_EXECUTION"))
    items.sort(key=lambda row: row["activity_id"])
    ids = [row["activity_id"] for row in items]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("duplicate or empty activity registry")
    present = set(ids)
    for row in items:
        if set(REQUIRED) - row.keys() or any(dep not in present for dep in row["dependencies"]):
            raise ValueError("incomplete activity registry or orphan dependency")
        if row["effect_class"] != "READ_ONLY" and row["execution_adapter"] == "PR36_PROCESS_SUITE":
            raise ValueError("effectful activity silently auto-executable")
    groups = {}
    for row in items:
        groups[row["kind"]] = groups.get(row["kind"], 0) + 1
    report = {
        "schema": SCHEMA, "commit": sha,
        "tree": git(repo, "rev-parse", sha + "^{tree}").decode("ascii").strip(),
        "authority": "NONE", "source_status": "SOURCE_REGISTRY_NOT_EXECUTION",
        "declared_commands": len(parsed),
        "registered_commands": sum(x["kind"] == "CLI_COMMAND" for x in items),
        "dispatched_commands": len(dispatched),
        "class_counts": dict(sorted(groups.items())),
        "activities": items,
        "surface_inventory": {
            "modules": sum(p.startswith("src/cora/") and p.endswith(".py") for p in paths),
            "tools": sum(p.startswith("tools/") and p.endswith(".py") for p in paths),
            "tests": sum(p.startswith("tests/test_") and p.endswith(".py") for p in paths),
            "workflows": sum(p.startswith(".github/workflows/") and p.endswith(".yml") for p in paths),
        },
        "proof_boundary": "PARSER_DISPATCH_GIT_SOURCE_NOT_RUNTIME_OR_EXTERNAL",
    }
    report["digest"] = domain_hash("CORA:integrated-registry:2", report)
    return report
