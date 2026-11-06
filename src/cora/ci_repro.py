"""CORA-on-CORA: independently repeat original Git falsifiers and quantify failures.

This executor records a *sample* from the exact checkout. It is not a host
permission check, root-cause proof, or release authorization. No network/API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from .reticulum import EXTERNAL, MODEL, assess_cut, ordered_cut

SCHEMA = "cora-postmerge-repro-metrics/1"
DOD = ".cora/contracts/dod/postmerge-repro-dod.json"
GROUPS = {
    "PR25_GIT_MUTANTS": "test_pr25_method_synthesis.py",
    "PR26_CAPABILITY_MUTANTS": "test_pr26_capability_atlas.py",
}
EDGES = {
    "G_GIT_IDENTITY": ["L_COMMIT", "L_TREE"],
    "G_ENV_PARITY": ["L_ENVIRONMENT", "L_COMMAND"],
    "G_REPETITION": ["L_PR25_REPEATS", "L_PR26_REPEATS", "L_METRIC_FLOORS"],
    "G_DIAGNOSTICS": ["L_FAIL_CLOSED", "L_LOG_FINGERPRINT"],
    "G_POSTMERGE_REPRODUCIBLE": [
        "G_GIT_IDENTITY", "G_ENV_PARITY", "G_REPETITION", "G_DIAGNOSTICS",
        "E_MAIN_POSTMERGE", "E_RCA_VERIFIED"],
    "G_RELEASE_GOVERNANCE": ["E_REVIEWER", "E_REQUIRED_CHECKS", "E_RELEASE_OWNER"],
    "G_QUALIFIED": ["G_POSTMERGE_REPRODUCIBLE", "G_RELEASE_GOVERNANCE"],
}
SOURCE_LEAVES = {
    "L_COMMIT", "L_TREE", "L_ENVIRONMENT", "L_COMMAND",
    "L_PR25_REPEATS", "L_PR26_REPEATS", "L_METRIC_FLOORS",
    "L_FAIL_CLOSED", "L_LOG_FINGERPRINT",
}
EXTERNAL_LEAVES = {
    "E_MAIN_POSTMERGE", "E_RCA_VERIFIED", "E_REVIEWER",
    "E_REQUIRED_CHECKS", "E_RELEASE_OWNER",
}
ALL_IDS = SOURCE_LEAVES | EXTERNAL_LEAVES | set(EDGES)
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
FAILURE = re.compile(r"^(?:ERROR|FAIL): ([a-zA-Z0-9_.() ]{1,180})", re.M)
ERROR_TYPE = re.compile(r"(?m)^(?:[a-zA-Z_][a-zA-Z_0-9.]*Error|Exception):")
SECRET_ENV = {"GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
              "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "GITHUB_APP_TOKEN"}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True,
                            capture_output=True, text=True, timeout=15)
    return result.stdout.strip()


def original_contract(repo: Path, sha: str) -> dict:
    raw = subprocess.run(
        ["git", "-C", str(repo), "show", sha + ":" + DOD],
        check=True, capture_output=True, text=True, timeout=15).stdout
    doc = json.loads(raw)
    if (doc.get("schema") != "cora-postmerge-repro-dod/1"
            or doc.get("authority") != "NONE"
            or doc.get("global_goal") != "G_QUALIFIED"
            or doc.get("logic") != "NONCOMPENSATORY_AND"):
        raise ValueError("reproduction DoD identity drift")
    nodes = doc.get("nodes")
    if (not isinstance(nodes, list) or len(nodes) != len(ALL_IDS)
            or len({n.get("id") for n in nodes}) != len(nodes)
            or {n["id"] for n in nodes} != ALL_IDS):
        raise ValueError("reproduction DoD node identity drift")
    by = {n["id"]: n for n in nodes}
    for name in ALL_IDS:
        node = by[name]
        dependencies = EDGES.get(name, [])
        expected_scope = "SOURCE" if name.startswith(("L_", "G_GIT_", "G_ENV_", "G_REPETITION", "G_DIAGNOSTICS")) else "EXTERNAL"
        if node.get("depends_on") != dependencies or node.get("scope") != expected_scope:
            raise ValueError("reproduction DoD mandatory dependency/scope drift")
        if name in EXTERNAL_LEAVES and node.get("witness_paths"):
            raise ValueError("external acceptance cannot use source witness")
    if len(ordered_cut(nodes, "G_QUALIFIED")) != len(nodes):
        raise ValueError("unreachable reproduction obligations")
    values = {x: MODEL for x in SOURCE_LEAVES}
    assessed = assess_cut(nodes, "G_QUALIFIED", values)
    if assessed["status"] != EXTERNAL:
        raise ValueError("source DoD incorrectly grants external acceptance")
    m = doc.get("metrics", {})
    if (m.get("required_groups") != list(GROUPS)
            or m.get("required_python") != ["3.11", "3.13"]
            or m.get("min_repetitions_per_group_per_python") != 3
            or m.get("max_observed_failures") != 0
            or m.get("external_root_cause") != "INDEPENDENT_ATTESTATION_REQUIRED"):
        raise ValueError("measurable gate thresholds drifted")
    return doc


def environment() -> dict:
    try:
        git_version = subprocess.run(
            ["git", "--version"], check=True, capture_output=True,
            text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        git_version = "NOT_OBSERVED"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--disable-pip-version-check"],
            check=True, capture_output=True, text=True, timeout=15)
        # Do not publish local paths, tokens or package index credentials.
        dependencies_sha = hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()
    except (OSError, subprocess.SubprocessError):
        dependencies_sha = "UNAVAILABLE"
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_micro": sys.version_info.micro,
        "system": platform.system(),
        "git": git_version,
        "dependency_lock_sha256": dependencies_sha,
        "coverage_version": _coverage_version(),
        "hash_seed": "UNSET" if "PYTHONHASHSEED" not in os.environ else
                     "PRESENT_NONDISCLOSED",
    }


def _coverage_version() -> str:
    try:
        from importlib.metadata import version
        return version("coverage")
    except Exception:
        return "NOT_INSTALLED"


def _run(argv: list[str], repo: Path, env: dict, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=repo, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, check=False,
                          timeout=timeout)


def _percentile95(values: list[int]) -> int:
    if not values:
        return 0
    return sorted(values)[math.ceil(.95 * len(values)) - 1]


def _attempt(argv: list[str], repo: Path, *, execute, timeout: int) -> dict:
    # The tests must not inherit GitHub API or Actions artifact credentials.
    env = {k: v for k, v in os.environ.items()
           if k not in SECRET_ENV and not k.startswith("ACTIONS_ID_TOKEN_REQUEST_")}
    start = time.monotonic()
    rc, out, err, reason = 2, "", "", "RUNNER_ERROR"
    try:
        completed = execute(argv, repo, env, timeout)
        rc = int(completed.returncode)
        out = completed.stdout or ""
        err = completed.stderr or ""
        reason = "OK" if rc == 0 else "TEST_EXIT_NONZERO"
    except subprocess.TimeoutExpired as exc:
        rc = 124
        reason = "TEST_TIMEOUT"
        out = exc.stdout or ""
        err = exc.stderr or ""
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        reason = type(exc).__name__
        rc = 125
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    if isinstance(err, bytes):
        err = err.decode("utf-8", "replace")
    text = (str(out) + "\n" + str(err))[-200_000:]
    failures = sorted(set(FAILURE.findall(text)))
    error_classes = sorted(set(ERROR_TYPE.findall(text)))
    # Failure content is not included in the portable report: original CI logs
    # remain the attributable traceback source, with no token forwarding.
    return {
        "returncode": rc, "outcome": reason,
        "elapsed_ms": max(0, int((time.monotonic() - start) * 1000)),
        "failure_test_ids": failures[:12],
        "exception_classes": error_classes[:12],
        "test_output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "truncated_output": len(str(out)) + len(str(err)) > 200_000,
    }


def run_probe(repo: Path, sha: str, *, repetitions: int = 3,
              group_names: tuple[str, ...] | None = None,
              execute=_run) -> dict:
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError("a full exact Git SHA is mandatory")
    if type(repetitions) is not int or not 3 <= repetitions <= 10:
        raise ValueError("3-10 independent observations required")
    names = tuple(GROUPS) if group_names is None else group_names
    if not names or len(set(names)) != len(names) or any(n not in GROUPS for n in names):
        raise ValueError("unknown, empty or duplicate test cohort")
    repo = Path(repo).resolve(strict=True)
    if git(repo, "rev-parse", "HEAD") != sha:
        raise ValueError("checkout HEAD differs from requested source commit")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    original_contract(repo, sha)
    result = {}
    for group in names:
        argv = [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                "-p", GROUPS[group], "-q"]
        samples = [_attempt(argv, repo, execute=execute, timeout=180)
                   for _ in range(repetitions)]
        failed = sum(x["returncode"] != 0 for x in samples)
        latencies = [x["elapsed_ms"] for x in samples]
        result[group] = {
            "argv_module": "unittest", "test_file": GROUPS[group],
            "samples": samples, "sample_count": len(samples),
            "failures": failed, "observed_failure_rate": round(failed / len(samples), 6),
            "elapsed_min_ms": min(latencies), "elapsed_max_ms": max(latencies),
            "elapsed_p95_ms": _percentile95(latencies),
        }
    full = {
        "schema": SCHEMA, "commit": sha, "tree": tree, "source": "ORIGINAL_GIT_HEAD",
        "environment": environment(), "cohorts": result, "requested_repetitions": repetitions,
        "sample_total": sum(x["sample_count"] for x in result.values()),
        "failures_total": sum(x["failures"] for x in result.values()),
        "qualification": "SAMPLED_SOURCE_EXECUTION_NOT_INDEPENDENT_RCA",
        "root_cause": "NOT_ATTESTED",
        "postmerge_status": "BLOCKED_EXTERNAL",
        "release_authorized": False, "authorization": "NONE",
    }
    full["status"] = ("FAIL_OBSERVED" if full["failures_total"] else
                      "PASS_SCOPED_REPEATABILITY_SAMPLE")
    verify_report(full, repo, sha=sha)
    return full


def verify_report(report: dict, repo: Path, *, sha: str) -> bool:
    if (not isinstance(report, dict) or report.get("schema") != SCHEMA
            or report.get("commit") != sha
            or report.get("tree") != git(repo, "rev-parse", sha + "^{tree}")
            or report.get("authorization") != "NONE"
            or report.get("postmerge_status") != "BLOCKED_EXTERNAL"
            or report.get("release_authorized") is not False
            or report.get("root_cause") != "NOT_ATTESTED"
            or report.get("qualification") !=
            "SAMPLED_SOURCE_EXECUTION_NOT_INDEPENDENT_RCA"):
        raise ValueError("untrusted, misattributed or overpromoted CI evidence")
    total = failed = 0
    if not isinstance(report.get("cohorts"), dict) or not report["cohorts"]:
        raise ValueError("missing sample cohorts")
    if not isinstance(report.get("environment"), dict):
        raise ValueError("missing environment identity")
    for key, cohort in report["cohorts"].items():
        if key not in GROUPS or cohort.get("test_file") != GROUPS[key]:
            raise ValueError("unbound test cohort")
        samples = cohort.get("samples", [])
        if len(samples) != cohort.get("sample_count") or not 3 <= len(samples) <= 10:
            raise ValueError("missing or incomplete independent samples")
        if any(type(s.get("returncode")) is not int or type(s.get("elapsed_ms")) is not int
               or s["elapsed_ms"] < 0 for s in samples):
            raise ValueError("invalid measured sample")
        counts = sum(s["returncode"] != 0 for s in samples)
        vals = [s["elapsed_ms"] for s in samples]
        if (cohort.get("failures") != counts
                or cohort.get("observed_failure_rate") != round(counts / len(samples), 6)
                or cohort.get("elapsed_min_ms") != min(vals)
                or cohort.get("elapsed_max_ms") != max(vals)
                or cohort.get("elapsed_p95_ms") != _percentile95(vals)):
            raise ValueError("CI metrics do not reconcile to raw attempts")
        total += len(samples)
        failed += counts
    if (total != report.get("sample_total")
            or failed != report.get("failures_total")
            or report.get("requested_repetitions") not in range(3, 11)
            or any(v["sample_count"] != report["requested_repetitions"]
                   for v in report["cohorts"].values())
            or report.get("status") !=
            ("FAIL_OBSERVED" if failed else "PASS_SCOPED_REPEATABILITY_SAMPLE")):
        raise ValueError("failed or omitted attempts masked as PASS")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measured postmerge source-only Git fixture repetition")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--sha", required=True)
    parser.add_argument("--group", choices=tuple(GROUPS), action="append")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run_probe(args.repo, args.sha, repetitions=args.repetitions,
                           group_names=tuple(args.group) if args.group else None)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        print(json.dumps({"commit": report["commit"], "tree": report["tree"],
                          "sample_total": report["sample_total"],
                          "failures_total": report["failures_total"],
                          "status": report["status"],
                          "authorization": "NONE"}, sort_keys=True))
        if report["failures_total"]:
            # Safe typed failure witnesses, no raw logs or credential strings.
            # A later passing attempt never downgrades this nonzero exit.
            for group, cohort in sorted(report["cohorts"].items()):
                for attempt_no, sample in enumerate(cohort["samples"], 1):
                    if sample["returncode"] != 0:
                        print(json.dumps({
                            "group": group, "attempt": attempt_no,
                            "returncode": sample["returncode"],
                            "outcome": sample["outcome"],
                            "exception_classes": sample["exception_classes"],
                            "failure_test_ids": sample["failure_test_ids"],
                            "log_sha256": sample["test_output_sha256"],
                        }, sort_keys=True), file=sys.stderr)
        return 3 if report["failures_total"] else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        # No pass or fake metrics on internal errors. Full error remains in CI logs.
        print("POSTMERGE_PROBE_BLOCKED: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
