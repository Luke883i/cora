"""Finite CORA operational equivalence, NOT universal program semantics.

Explicitly opt-in: executes pinned CORA Python code from two original-Git
checkouts, only for the registered read-only probes. No arbitrary commands,
target transformations, external approvals or automatic merge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

CONTRACT = ".cora/assurance/operational-universe.json"
ATLAS = ".cora/assurance/capability-atlas.json"
SCHEMA = "cora-operational-observation/1"
NATIVE = ("version", "process-list", "snapshot-pinned", "graph-pinned",
          "dod-plan-pinned", "stress-128")
SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
CMD = re.compile(r"^[a-z][a-z0-9-]*$")
MAX_OUTPUT = 16 * 1024 * 1024

NEGATIVE_CONTROLS = (
    "DELETED_DECLARED_COMMAND", "FORGED_EQUALITY", "MISSING_OBSERVATION",
    "ALTERED_CLI_HELP", "WRONG_HEAD_OR_BASE", "SCOPE_NARROWING",
    "NONZERO_EXIT",
)
EXCLUDED = (
    "ALL_POSSIBLE_INPUTS", "DYNAMIC_EXTENSIONS", "NETWORK_SERVICES",
    "PERSISTENT_SIDE_EFFECTS", "DIFFERENT_HOST_ENVIRONMENTS",
    "INDEPENDENT_REVIEW", "BRANCH_PROTECTION",
    "FULL_PRODUCT_GLOBAL_EQUIVALENCE",
)
ENVIRONMENT = {
    "python": "SAME_INTERPRETER", "pythonhashseed": "0",
    "locale": "C.UTF-8", "timezone": "UTC", "columns": "100",
    "user_site": "DISABLED", "fixture": "PINNED_BASE_GIT_COMMIT",
}



def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        timeout=90, check=False)
    if result.returncode or len(result.stdout) > MAX_OUTPUT:
        raise ValueError("original Git operation failed or exceeded size bound: "
                         + " ".join(args[:2]))
    return result.stdout


def revision(repo: Path, name: str) -> str:
    sha = git(repo, "rev-parse", "--verify", name + "^{commit}").decode().strip()
    if not SHA.fullmatch(sha):
        raise ValueError("not an exact Git commit identity")
    return sha


def read_json(repo: Path, sha: str, path: str) -> dict:
    doc = json.loads(git(repo, "show", sha + ":" + path).decode("utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("invalid Git JSON contract")
    return doc


def universe(repo: Path, base: str, head: str) -> tuple[list[str], dict]:
    """No denominator may be inferred from a partially observed runtime."""
    contract = read_json(repo, head, CONTRACT)
    required = {
        "schema", "intent", "authority", "global_product_status",
        "expected_declared_cli_commands", "help_case", "native_cases",
        "native_execution", "base_head", "output_oracle", "runner_environment",
        "required_negative_controls", "excluded_obligations",
    }
    if (set(contract) != required or
            contract["schema"] != "cora-operational-observation-universe/1" or
            contract["authority"] != "NONE" or
            contract["global_product_status"] != "BLOCKED_EXTERNAL" or
            contract["native_execution"] != "EXPLICIT_OPT_IN_PINNED_CORA_SOURCE_ONLY" or
            contract["help_case"] != "ALL_DECLARED_COMMANDS_FROM_BOTH_GIT_PINNED_CAPABILITY_ATLASES" or
            contract["native_cases"] != list(NATIVE) or
            contract["expected_declared_cli_commands"] != 71 or
            contract["intent"] != "EXHAUSTIVE_EQUIVALENCE_ON_EXPLICIT_FINITE_OPERATIONS_ONLY" or
            contract["base_head"] != "DISTINCT_ANCESTRALLY_RELATED_COMMITS" or
            contract["output_oracle"] != "EXACT_RETURN_CODE_STDOUT_STDERR_BYTES_IN_SAME_RUNNER_ENVIRONMENT" or
            contract["runner_environment"] != ENVIRONMENT or
            contract["required_negative_controls"] != list(NEGATIVE_CONTROLS) or
            contract["excluded_obligations"] != list(EXCLUDED)):
        raise ValueError("operational contract incomplete or unsafe")
    command_sets = []
    for rev in (base, head):
        atlas = read_json(repo, rev, ATLAS)
        if atlas.get("schema") != "cora-capability-atlas/1":
            raise ValueError("capability atlas schema drift")
        entries = atlas.get("commands")
        if not isinstance(entries, list):
            raise ValueError("missing registered CLI command denominator")
        names = [item.get("command") for item in entries
                 if isinstance(item, dict)]
        if (len(names) != len(entries) or
                len(names) != contract["expected_declared_cli_commands"] or
                len(set(names)) != len(names) or
                any(not isinstance(name, str) or not CMD.fullmatch(name)
                    for name in names)):
            raise ValueError("missing, duplicate or invalid declared CLI command")
        command_sets.append(sorted(names))
    if command_sets[0] != command_sets[1]:
        raise ValueError("BASE/HEAD declared CLI universe changed")
    cases = ["help:" + cmd for cmd in command_sets[0]] + list(NATIVE)
    if len(cases) != 77 or len(set(cases)) != len(cases):
        raise ValueError("non-exhaustive finite operational universe")
    return cases, contract


def arguments(case: str, repo: Path, base: str, fixture: Path) -> list[str]:
    if case.startswith("help:"):
        cmd = case[5:]
        if not CMD.fullmatch(cmd):
            raise ValueError("invalid command in operational universe")
        return [cmd, "--help"]
    fixed = {
        "version": ["version"],
        "process-list": ["process-list"],
        "snapshot-pinned": ["snapshot", str(repo), "--revision", base],
        "graph-pinned": ["graph", str(repo), "--revision", base],
        "dod-plan-pinned": ["dod-plan", "--contract", str(fixture),
                            "--stage", "premerge"],
        "stress-128": ["stress", "--seed", "883", "--cases", "128"],
    }
    if case not in fixed:
        raise ValueError("unregistered native behavior")
    return fixed[case]


def execute(checkout: Path, argv: list[str]) -> dict:
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": str(checkout / "src"),
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "COLUMNS": "100",
        "TERM": "dumb",
        "TZ": "UTC",
        "LC_ALL": "C.UTF-8",
    })
    run = subprocess.run(
        [sys.executable, "-m", "cora.cli", *argv], cwd=checkout,
        env=env, capture_output=True, timeout=60, check=False)
    if len(run.stdout) > MAX_OUTPUT or len(run.stderr) > MAX_OUTPUT:
        raise ValueError("native observation exceeded size bound")
    return {"exit_code": run.returncode, "stdout": run.stdout,
            "stderr": run.stderr}


def observation_info(x: dict) -> dict:
    return {
        "exit_code": x["exit_code"],
        "stdout_sha256": hashlib.sha256(x["stdout"]).hexdigest(),
        "stdout_bytes": len(x["stdout"]),
        "stderr_sha256": hashlib.sha256(x["stderr"]).hexdigest(),
        "stderr_bytes": len(x["stderr"]),
    }


def compare(cases: list[str], before: dict, after: dict) -> dict:
    """Separate strict oracle: nonobservations cannot improve a ratio."""
    if (not isinstance(cases, list) or not cases or
            len(cases) != len(set(cases)) or
            set(before) != set(cases) or set(after) != set(cases)):
        raise ValueError("missing, duplicate or invented operational observation")
    rows, failures = [], []
    for case in cases:
        left, right = before[case], after[case]
        if (not isinstance(left, dict) or not isinstance(right, dict) or
                set(left) != {"exit_code", "stdout", "stderr"} or
                set(right) != {"exit_code", "stdout", "stderr"} or
                any(type(obs["exit_code"]) is not int or
                    not isinstance(obs["stdout"], bytes) or
                    not isinstance(obs["stderr"], bytes)
                    for obs in (left, right))):
            raise ValueError("malformed native operational observation")
        equal = (left["exit_code"] == right["exit_code"] and
                 left["stdout"] == right["stdout"] and
                 left["stderr"] == right["stderr"])
        successful = (left["exit_code"] == right["exit_code"] == 0
                      and bool(left["stdout"]) and bool(right["stdout"])
                      and not left["stderr"] and not right["stderr"])
        passed = equal and successful
        if not passed:
            failures.append(case)
        rows.append({"case": case, "status": "PASS" if passed else "REFUTED",
                     "baseline": observation_info(left),
                     "candidate": observation_info(right)})
    return {
        "denominator": len(cases), "observed": len(rows),
        "passed": len(cases) - len(failures),
        "failed": failures, "rows": rows,
        "status": ("PASS_EXHAUSTIVE_FINITE_OBSERVATIONS"
                   if not failures else "REFUTED_FINITE_OBSERVATIONS"),
    }


def run(repo: Path, base: str, head: str, *, execute_pinned_native: bool) -> dict:
    if not execute_pinned_native:
        raise ValueError("explicit --execute-pinned-native opt-in required")
    repo = repo.resolve(strict=True)
    base_sha, head_sha = revision(repo, base), revision(repo, head)
    if base_sha == head_sha:
        raise ValueError("BASE and HEAD must be distinct")
    ancestry = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor",
         base_sha, head_sha], capture_output=True, timeout=30, check=False)
    if ancestry.returncode != 0:
        raise ValueError("BASE must be an ancestor of HEAD")
    cases, contract = universe(repo, base_sha, head_sha)
    with tempfile.TemporaryDirectory(prefix="cora-operational-") as temp:
        root = Path(temp)
        fixture = root / "pinned-dod.json"
        fixture.write_bytes(git(
            repo, "show", base_sha + ":.cora/contracts/dod/agent-dod.json"))
        observations = []
        for index, sha in enumerate((base_sha, head_sha)):
            checkout = root / ("baseline" if index == 0 else "candidate")
            cloned = subprocess.run(
                ["git", "clone", "--no-local", "-q", "--", str(repo), str(checkout)],
                capture_output=True, timeout=120, check=False)
            if cloned.returncode:
                raise ValueError("isolated original Git clone failed")
            git(checkout, "checkout", "--detach", "-q", sha)
            if revision(checkout, "HEAD") != sha:
                raise ValueError("checkout identity drift")
            observations.append({
                case: execute(checkout, arguments(case, repo, base_sha, fixture))
                for case in cases
            })
        result = compare(cases, observations[0], observations[1])
    return {
        "schema": SCHEMA, "base": base_sha, "head": head_sha,
        "manifest_sha256": hashlib.sha256(
            json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "universe": "ALL_DECLARED_71_CLI_HELP_PLUS_6_NATIVE_OPERATIONS",
        "runner": "TWO_ORIGINAL_GIT_CHECKOUTS_ONE_PYTHON_BINARY_ONE_PINNED_INPUT",
        "method": "EXACT_EXIT_STDOUT_STDERR_BYTE_COMPARISON",
        "status": result["status"],
        "denominator": result["denominator"],
        "observed": result["observed"],
        "passed": result["passed"],
        "failed": result["failed"],
        "rows": result["rows"],
        "product_global_status": "BLOCKED_EXTERNAL",
        "independent_reviewer": "NOT_ATTESTED",
        "side_effect_equivalence": "OUTSIDE_OBSERVATION_UNIVERSE",
        "unregistered_behavior": "NOT_EVALUATED",
        "scoped_dod": {
            "I1_UNIVERSE": "PASS_CLOSED_77_FROM_DUAL_GIT_ATLAS",
            "I2_ENVIRONMENT": "OBSERVED_SAME_RUNNER_DIFFERENT_GIT_CHECKOUTS",
            "I3_OBSERVATIONS": result["status"],
            "I4_INDEPENDENT_REPLAY": "PENDING_SEPARATE_EXECUTION",
            "G_OP": "PENDING_REPLAY",
            "G_PRODUCT": "BLOCKED_EXTERNAL",
        },
        "authorization": "NONE",
    }


def verify(repo: Path, report: dict, *, execute_pinned_native: bool) -> bool:
    if (not isinstance(report, dict) or report.get("schema") != SCHEMA or
            not SHA.fullmatch(str(report.get("base", ""))) or
            not SHA.fullmatch(str(report.get("head", "")))):
        raise ValueError("malformed operational equivalence receipt")
    if run(repo, report["base"], report["head"],
           execute_pinned_native=execute_pinned_native) != report:
        raise ValueError("operational equivalence report does not independently replay")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--base")
    p.add_argument("--head", default="HEAD")
    p.add_argument("--output", type=Path)
    p.add_argument("--verify-report", type=Path)
    p.add_argument("--execute-pinned-native", action="store_true")
    args = p.parse_args()
    try:
        if args.verify_report:
            if args.base:
                raise ValueError("replay must derive base/head from the receipt")
            report = json.loads(args.verify_report.read_text("utf-8"))
            verify(args.repo, report, execute_pinned_native=args.execute_pinned_native)
            passed = report["status"] == "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS"
            result = {
                "schema": "cora-operational-replay/1",
                "base": report["base"], "head": report["head"],
                "status": ("REPLAYED_SCOPED_OPERATIONS" if passed
                           else "REPLAYED_REFUTED_SCOPED_OPERATIONS"),
                "scoped_global_dod": (
                    "PASS_ON_COMPLETE_REGISTERED_UNIVERSE" if passed
                    else "REFUTED"),
                "authorization": "NONE",
                "product_global_status": "BLOCKED_EXTERNAL",
            }
        else:
            if not args.base:
                raise ValueError("required exact --base Git commit")
            result = run(args.repo, args.base, args.head,
                         execute_pinned_native=args.execute_pinned_native)
        encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0 if result["status"] in (
            "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS",
            "REPLAYED_SCOPED_OPERATIONS") else 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            subprocess.SubprocessError) as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
