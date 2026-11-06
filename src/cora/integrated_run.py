"""PR37 integrated one-run dossier: preserve PR36 executor and qualify every omission."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git, snapshot
from .integrated_registry import build_registry, verify_contract, SCHEMA as REGISTRY_SCHEMA
from .one_run import run_one, verify_one
from .genealogy import build_genealogy, corpus_available
from .independent_qualification import build_qualification, verify_qualification, CONTRACT as QUALIFICATION_CONTRACT

SCHEMA = "cora-integrated-one-run/2"
ATTEMPT_STATES = {"EXECUTED_SCOPED", "REUSED_SCOPED", "BLOCKED", "FAIL",
                  "NOT_RUN", "RUN_REPORTED_UNATTESTED"}
LOCAL_SOURCE_CONTROLS = frozenset((
    "S_PR36_IMPORTED S_DISCOVER_CLI S_DISCOVER_NONCLI S_REGISTRY_SCHEMA "
    "S_REGISTRY_BIJECTION S_SCOPE_SEPARATION S_PLAN_DAG S_PLAN_REUSE "
    "S_EFFECT_GATING S_SOURCE_METHODS S_EXECUTOR_ADAPTERS S_TASK_RESULTS "
    "S_FAIL_PROPAGATION S_MANIFEST_GIT S_MANIFEST_ENV S_MANIFEST_TASK "
    "S_PROOF_LINEAGE S_EVIDENCE_MISSING S_ORIGINAL_SOURCE_REPLAY "
    "S_REPORT_REPLAY S_ATLAS_OVERVIEW S_ATLAS_DRILLDOWN S_ATLAS_DOD "
    "S_RESULT_METRICS S_GAP_REGISTER"
).split())
CONTROL_PLANE = "cli:process-run"
AUTH_SCHEMA = "cora-explicit-execution-consent/1"


def _serialize(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _outside_repo(repo: Path, directory: Path) -> Path:
    repo = repo.resolve(strict=True)
    target = directory.resolve()
    if target == repo or repo in target.parents:
        raise ValueError("evidence output cannot modify inspected repository")
    if target.exists() and (target.is_symlink() or not target.is_dir()):
        raise ValueError("evidence output must be a normal directory")
    return target


def _parse_unittest_log(log: bytes) -> tuple[list[dict], int | None, list[str]]:
    """Re-derive test events from locally retained bytes, not receipt declarations."""
    content = log.decode("utf-8", "replace")
    # unittest -v: test_method (test_module.Class.test_method) ... ok
    rx = re.compile(r"^(.+?) \(([^()]+)\) \.\.\. (ok|FAIL|ERROR|skipped .+|expected failure|unexpected success)$")
    cases = []
    ids = set()
    for line in content.splitlines():
        match = rx.match(line.strip())
        if match is None:
            continue
        dotted = match.group(2).split(".")
        if len(dotted) < 2:
            continue
        module = dotted[0]
        case_id = "case:tests/" + module + ".py:" + ".".join(dotted[1:])
        if case_id in ids:
            raise ValueError("duplicate execution event in verbose unittest log")
        ids.add(case_id)
        status = match.group(3)
        cases.append({"activity_id": case_id,
                      "state": "FAIL" if status in ("FAIL", "ERROR", "unexpected success")
                               else "SKIPPED" if status.startswith("skipped")
                               else "RUN_REPORTED_UNATTESTED",
                      "outcome": status[:160]})
    count_match = re.search(r"(?m)^Ran ([0-9]{1,6}) tests?\b", content)
    reported = int(count_match.group(1)) if count_match else None
    warnings = []
    if reported is None or len(cases) != reported:
        warnings.append("TEST_CASE_COUNT_NOT_RECONCILED")
    return sorted(cases, key=lambda x: x["activity_id"]), reported, warnings


def _test_observation(repo: Path, sha: str, tree: str, *,
                      authorized: Path | None, evidence_dir: Path | None,
                      timeout: int) -> tuple[dict, bytes | None]:
    missing = {
        "state": "NOT_RUN", "reason": "EXPLICIT_TEST_CONSENT_REQUIRED",
        "returncode": None, "duration_ms": None, "log_sha256": None,
        "log_bytes": None, "reported_tests": None, "parsed_cases": [],
        "parse_warnings": [], "proof_scope": "NO_RUNTIME_OBSERVATION",
        "authority": "NONE",
    }
    if authorized is None:
        return missing, None
    if evidence_dir is None:
        raise ValueError("runtime test log retention requires --evidence-dir")
    if not 30 <= timeout <= 900:
        raise ValueError("invalid bounded test timeout")
    consent = json.loads(Path(authorized).read_text("utf-8"))
    if (not isinstance(consent, dict) or set(consent) != {
            "schema", "commit", "tree", "operation", "checkout"}
            or consent["schema"] != AUTH_SCHEMA or consent["commit"] != sha
            or consent["tree"] != tree or consent["operation"] != "CORA_LOCAL_SELF_TESTS"
            or Path(consent["checkout"]).resolve(strict=True) != repo):
        raise ValueError("explicit exact-SHA/local-checkout consent missing or stale")
    if git(repo, "rev-parse", "HEAD").decode("ascii").strip() != sha:
        raise ValueError("self-tests require exact checkout HEAD")
    if git(repo, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("self-tests require clean checkout: prevent ambiguous execution")
    # Explicit consent is a scope assertion, not independent authentication or sandboxing.
    # Do not forward bearer credentials to arbitrary Python code in the checkout.
    deny = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "API_KEY",
            "PRIVATE_KEY", "ACTIONS_ID_TOKEN", "GITHUB_AUTH", "GH_AUTH")
    child_env = {k: v for k, v in os.environ.items()
                 if not any(flag in k.upper() for flag in deny)}
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=repo, capture_output=True, timeout=timeout, check=False, env=child_env)
        log, code = proc.stdout + b"\n" + proc.stderr, proc.returncode
        reason = "EXIT_ZERO_NOT_INDEPENDENTLY_ATTESTED" if code == 0 else "TEST_FAILURE"
    except subprocess.TimeoutExpired as exc:
        log, code, reason = (exc.stdout or b"") + b"\n" + (exc.stderr or b""), 124, "TIMEOUT"
    if len(log) > 4_000_000:
        # Avoid silently discarding evidence while claiming a complete test log.
        raise ValueError("test log exceeds bounded evidence retention; evidence blocked")
    cases, reported, warnings = _parse_unittest_log(log)
    return {
        "state": "RUN_REPORTED_UNATTESTED" if code == 0 else "FAIL",
        "reason": reason, "returncode": code,
        "duration_ms": max(0, int((time.monotonic() - start) * 1000)),
        "log_sha256": hashlib.sha256(log).hexdigest(), "log_bytes": len(log),
        "reported_tests": reported, "parsed_cases": cases,
        "parse_warnings": warnings, "proof_scope": "LOCAL_RUNTIME_OBSERVATION_UNATTESTED",
        "authority": "NONE",
    }, log


def _topological(registry: dict) -> list[str]:
    table = {x["activity_id"]: x for x in registry["activities"]}
    done, pending = [], set(table)
    while pending:
        ready = sorted(k for k in pending if set(table[k]["dependencies"]) <= set(done))
        if not ready:
            raise ValueError("activity registry contains dependency cycle or orphan")
        done.extend(ready)
        pending.difference_update(ready)
    return done


def _attempts(registry: dict, baseline: dict, test: dict) -> list[dict]:
    executed = {row["id"]: row for row in baseline["activities"]}
    observed = {row["activity_id"]: row for row in test["parsed_cases"]}
    ids = {row["activity_id"] for row in registry["activities"]}
    if any(k not in ids for k in observed):
        raise ValueError("unregistered test case outcome cannot be laundered")
    rows = []
    for row in registry["activities"]:
        key = row["activity_id"]
        state, reason, origin, elapsed = "NOT_RUN", "REGISTERED_NOT_EXECUTED", None, None
        if row["kind"] == "INTERNAL_METHOD":
            source = executed.get(key.removeprefix("method:"))
            if source is None:
                reason = "NOT_SELECTED_BY_PROCESS"
            else:
                state, reason = source["state"], source.get("reason")
                origin, elapsed = source.get("source_digest"), source.get("elapsed_ms")
        elif row["kind"] == "TEST_CASE" and key in observed:
            state, reason = observed[key]["state"], observed[key]["outcome"]
            origin = test["log_sha256"]
        elif row["kind"] == "TEST_SUITE":
            members = [event for event in test["parsed_cases"]
                       if event["activity_id"].startswith("case:" + row["source_paths"][0] + ":")]
            if members:
                state = "FAIL" if any(event["state"] == "FAIL" for event in members) else "RUN_REPORTED_UNATTESTED"
                reason = "ATTRIBUTED_CASE_EVENTS_NOT_INDEPENDENT_PROOF"
                origin, elapsed = test["log_sha256"], None
            elif test["state"] != "NOT_RUN":
                state, reason = "BLOCKED", "NO_ATTRIBUTABLE_CASES_FOR_SUITE"
            else:
                reason = "LOCAL_TESTS_NOT_AUTHORIZED"
        elif key == CONTROL_PLANE:
            reason = "ORCHESTRATOR_ENTRY_ALREADY_OBSERVED_NOT_INDIVIDUAL_CLI_EXECUTION"
        elif row["kind"] == "CLI_COMMAND":
            reason = "CLI_CATALOG_ONLY_NOT_INDIVIDUALLY_RUN"
        elif row["kind"] == "CI_WORKFLOW":
            reason = "REMOTE_HOST_WORKFLOW_NOT_TRIGGERED_OR_AUTHENTICATED"
        elif row["kind"] == "SOFTWARE_MODULE":
            reason = "MODULE_SOURCE_NOT_EXECUTABLE_TASK"
        elif row["effect_class"] != "READ_ONLY":
            reason = "EXTERNAL_AUTHORIZATION_AND_ISOLATION_NOT_ATTESTED"
        if state not in ATTEMPT_STATES | {"SKIPPED"}:
            raise ValueError("unknown activity terminal outcome")
        rows.append({
            "activity_id": key, "state": state, "reason": reason,
            "source_digest": origin, "elapsed_ms": elapsed,
            "evidence_refs": (["PR36:activity:" + key.removeprefix("method:")]
                              if row["kind"] == "INTERNAL_METHOD" and key.removeprefix("method:") in executed
                              else ["LOCAL_LOG_SHA256:" + test["log_sha256"]]
                              if key in observed and test["log_sha256"] else []),
            "verification": ("SOURCE_REPLAY_ELIGIBLE" if row["kind"] == "INTERNAL_METHOD"
                             and state in ("EXECUTED_SCOPED", "REUSED_SCOPED")
                             else "UNATTESTED_LOCAL_EXIT" if key in observed
                             else "NOT_VERIFIED"),
            "authority": "NONE",
        })
    return rows


def _gap_register(registry: dict, attempts: list[dict], test: dict) -> dict:
    reasons: dict[str, list[str]] = {}
    for attempt in attempts:
        if attempt["state"] in ("NOT_RUN", "BLOCKED", "FAIL", "SKIPPED"):
            reasons.setdefault(attempt["reason"] or attempt["state"], []).append(attempt["activity_id"])
    if test["parse_warnings"]:
        reasons["RUNTIME_TEST_CASE_LINEAGE_INCOMPLETE"] = ["suite:unittest-discover"]
    return {"schema": "cora-integrated-gaps/2",
            "issues": [{"reason": reason, "count": len(ids),
                        "activity_ids": sorted(ids),
                        "remediation": "REQUIRE_SPECIFIC_ORACLE_OR_AUTHORIZATION;DO_NOT_IMPUTE_PASS"}
                       for reason, ids in sorted(reasons.items())],
            "unreported_activity_count": 0,
            "product_external": "BLOCKED_EXTERNAL"}


def _dod(repo: Path, sha: str, test: dict, baseline: dict) -> dict:
    doc = verify_contract(repo, sha)
    observed_test_cases = bool(test["parsed_cases"]) and not test["parse_warnings"]
    source_nodes = set(LOCAL_SOURCE_CONTROLS)
    if observed_test_cases:
        source_nodes.add("S_TEST_CASE_EVENTS")
    if baseline["model_stress"]["status"] != "NOT_RUN":
        source_nodes.add("S_MODEL_FALSIFIERS")
    # Source witnesses are not approvals. Unknown source obligations remain debt,
    # even when their witness path exists. Never compensate with synthetic volume.
    nodes = []
    for node in doc["nodes"]:
        name = node["id"]
        if node["scope"] == "EXTERNAL":
            state = "BLOCKED_EXTERNAL"
        elif name in source_nodes and name.startswith("S_"):
            state = "SOURCE_WITNESS_PRESENT_NOT_INDEPENDENT_PROOF"
        else:
            state = "DEBT_BLOCKED"
        nodes.append({"id": name, "scope": node["scope"], "depends_on": node["depends_on"],
                      "state": state,
                      "proof_boundary": ("SOURCE_CANDIDATE" if name in source_nodes
                                         else "EXTERNAL_OR_UNOBSERVED")})
    return {
        "schema": "cora-integrated-dod-assessment/2",
        "nodes": nodes,
        "source_goal": "DEBT_BLOCKED",
        "product_goal": "BLOCKED_EXTERNAL",
        "unqualified_source": sorted(x["id"] for x in nodes
                                     if x["scope"] == "SOURCE" and x["state"] == "DEBT_BLOCKED"),
        "external": sorted(x["id"] for x in nodes if x["scope"] == "EXTERNAL"
                           and not x["depends_on"]),
        "authority": "NONE",
    }


def _metrics(registry: dict, attempts: list[dict], test: dict) -> dict:
    counters: dict[str, int] = {}
    for row in attempts:
        counters[row["state"]] = counters.get(row["state"], 0) + 1
    return {
        "registered_total": len(registry["activities"]),
        "registered_cli": registry["registered_commands"],
        "individually_executed_cli": 0,
        "activity_accounted": len(attempts),
        "activity_accountability_ratio": 1.0 if len(attempts) == len(registry["activities"]) else 0.0,
        "status_counts": dict(sorted(counters.items())),
        "reported_tests": test["reported_tests"],
        "identified_test_events": len(test["parsed_cases"]),
        "test_lineage_complete": (test["reported_tests"] is not None
                                  and test["reported_tests"] == len(test["parsed_cases"])),
        "unsafe_promotion_count": 0,
        "runtime_independent_attestation": False,
        "product_qualified": False,
    }


def _artifact_payloads(bundle: dict, log: bytes | None) -> dict[str, bytes]:
    files = {"registry.json": _serialize(bundle["registry"]),
             "attempts.json": _serialize(bundle["attempts"]),
             "gaps.json": _serialize(bundle["gaps"]),
             "dod.json": _serialize(bundle["dod"]),
             "execution-manifest.json": _serialize(bundle["execution_manifest"])}
    if "genealogy" in bundle:
        files["genealogy.json"] = _serialize(bundle["genealogy"])
    if "qualification" in bundle:
        files["qualification.json"] = _serialize(bundle["qualification"])
    if log is not None:
        files["unittest-verbose.log"] = log
    return files


def _manifest(bundle: dict, log: bytes | None, materialized: bool) -> dict:
    return {"schema": "cora-integrated-evidence-manifest/2",
            "state": "MATERIALIZED_LOCAL_NOT_INDEPENDENTLY_ATTESTED" if materialized
                     else "IN_REPORT_NOT_ON_DISK",
            "files": [{"path": k, "sha256": hashlib.sha256(v).hexdigest(),
                       "bytes": len(v), "trust": "LOCAL_UNATTESTED"}
                      for k, v in sorted(_artifact_payloads(bundle, log).items())],
            "authority": "NONE"}


def run_integrated(repo: Path, revision: str = "HEAD", *, process: str = "full",
                   max_commits: int = 64, focus: str | None = None,
                   execute_self_tests: bool = False,
                   authorization_file: Path | None = None,
                   evidence_dir: Path | None = None,
                   test_timeout: int = 240, model_stress_cases: int = 0) -> dict:
    repo = Path(repo).resolve(strict=True)
    sha = snapshot(repo, revision)["commit"]
    tree = git(repo, "rev-parse", sha + "^{tree}").decode("ascii").strip()
    if execute_self_tests != (authorization_file is not None):
        raise ValueError("comprehensive self-tests require both opt-in and an exact-SHA consent file")
    out = _outside_repo(repo, evidence_dir) if evidence_dir is not None else None
    if execute_self_tests and (not (repo / ".git").exists() or
                                git(repo, "rev-parse", "HEAD").decode().strip() != sha):
        raise ValueError("only the explicitly authorized CORA HEAD checkout may run self-tests")
    registry = build_registry(repo, sha)
    base = run_one(repo, sha, process=process, max_commits=max_commits,
                   focus=focus, execute_self_tests=False,
                   model_stress_cases=model_stress_cases)
    test, log = _test_observation(repo, sha, tree,
                                  authorized=authorization_file if execute_self_tests else None,
                                  evidence_dir=out, timeout=test_timeout)
    attempts = _attempts(registry, base, test)
    order = _topological(registry)
    gaps = _gap_register(registry, attempts, test)
    dod = _dod(repo, sha, test, base)
    env = {"python_version": platform.python_version(),
           "implementation": platform.python_implementation(),
           "platform": platform.system(), "architecture": platform.machine(),
           "scope": "LOCALLY_REPORTED_NOT_INDEPENDENTLY_ATTESTED"}
    bundle = {
        "schema": SCHEMA, "commit": sha, "tree": tree,
        "profile": "SOURCE_COMPREHENSIVE",
        "authority": "NONE", "authorization": "NONE",
        "release_authorized": False,
        "source_status": "DEBT_BLOCKED",
        "product_status": "BLOCKED_EXTERNAL",
        "baseline_pr36": base, "registry": registry,
        "plan": {"schema": "cora-integrated-plan/2", "order": order,
                 "source_methods": [x for x in order if x.startswith("method:")],
                 "effectful_disallowed": sorted(x["activity_id"] for x in registry["activities"]
                                              if x["effect_class"] != "READ_ONLY"),
                 "semantics": "DEPENDENCY_ORDER_NOT_EVERY_COMMAND_EXECUTION"},
        "attempts": attempts, "tests": test, "gaps": gaps, "dod": dod,
        "metrics": _metrics(registry, attempts, test),
        "execution_manifest": {
            "schema": "cora-integrated-execution/2",
            "commit": sha, "tree": tree, "runtime": env,
            "source_receipt_digest": base["receipt_digest"],
            "registry_digest": registry["digest"],
            "local_test_log_sha256": test["log_sha256"],
            "trust": "GIT_SOURCE_PLUS_UNATTESTED_LOCAL_CLAIMS",
            "authorization": "NONE",
        },
    }
    if corpus_available(repo, sha):
        bundle["genealogy"] = build_genealogy(repo, sha)
    if (QUALIFICATION_CONTRACT in {x.decode("utf-8") for x in
           git(repo, "ls-tree", "-r", "-z", "--name-only", sha,
               max_output=16_000_000).split(b"\0") if x}):
        bundle["qualification"] = build_qualification(repo, sha)
    bundle["evidence_manifest"] = _manifest(bundle, log, out is not None)
    bundle["receipt_digest"] = domain_hash("CORA:integrated-one-run:2", bundle)
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        for name, data in _artifact_payloads(bundle, log).items():
            destination = out / name
            if destination.is_symlink():
                raise ValueError("evidence destination may not be a symlink")
            destination.write_bytes(data)
    return bundle


def verify_integrated(repo: Path, receipt: dict, *, html_page: str | None = None,
                      evidence_dir: Path | None = None) -> bool:
    if (not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA
            or receipt.get("authority") != "NONE"
            or receipt.get("authorization") != "NONE"
            or receipt.get("release_authorized") is not False
            or receipt.get("product_status") != "BLOCKED_EXTERNAL"
            or receipt.get("source_status") != "DEBT_BLOCKED"
            or receipt.get("profile") != "SOURCE_COMPREHENSIVE"):
        raise ValueError("integrated one-run authority or product promotion")
    sha = receipt["commit"]
    repo = Path(repo).resolve(strict=True)
    if receipt["tree"] != git(repo, "rev-parse", sha + "^{tree}").decode().strip():
        raise ValueError("wrong integrated Git tree")
    if not verify_one(repo, receipt["baseline_pr36"]):
        raise ValueError("PR36 original source replay failed")
    if receipt["baseline_pr36"]["commit"] != sha:
        raise ValueError("cross revision PR36 report rejected")
    if "genealogy" in receipt:
        if receipt["genealogy"] != build_genealogy(repo, sha):
            raise ValueError("historical genealogy mismatch")
    elif corpus_available(repo, sha):
        raise ValueError("genealogy obligation missing from dossier")
    if "qualification" in receipt:
        if not verify_qualification(repo, receipt["qualification"]):
            raise ValueError("independent qualification Git replay failed")
        if receipt["qualification"]["commit"] != sha:
            raise ValueError("cross revision qualification prohibited")
    elif (QUALIFICATION_CONTRACT in {x.decode("utf-8") for x in
            git(repo, "ls-tree", "-r", "-z", "--name-only", sha,
                max_output=16_000_000).split(b"\0") if x}):
        raise ValueError("product qualification evidence silently omitted")
    expected = build_registry(repo, sha)
    if receipt.get("registry") != expected:
        raise ValueError("integrated registry differs from original Git")
    order = _topological(expected)
    plan = receipt["plan"]
    if (plan.get("schema") != "cora-integrated-plan/2"
            or plan.get("order") != order
            or plan.get("source_methods") != [x for x in order if x.startswith("method:")]
            or plan.get("effectful_disallowed") != sorted(
                x["activity_id"] for x in expected["activities"]
                if x["effect_class"] != "READ_ONLY")
            or plan.get("semantics") != "DEPENDENCY_ORDER_NOT_EVERY_COMMAND_EXECUTION"):
        raise ValueError("forged activity plan or unsafe execution permission")
    test = receipt["tests"]
    if (not isinstance(test, dict) or test.get("authority") != "NONE"
            or test.get("proof_scope") not in ("NO_RUNTIME_OBSERVATION",
                                               "LOCAL_RUNTIME_OBSERVATION_UNATTESTED")
            or test.get("state") not in ("NOT_RUN", "RUN_REPORTED_UNATTESTED", "FAIL")):
        raise ValueError("runtime claim promoted without independent authority")
    if test["state"] == "NOT_RUN":
        if any(test[k] is not None for k in (
                "returncode", "duration_ms", "log_sha256",
                "log_bytes", "reported_tests")) or test.get("parsed_cases"):
            raise ValueError("not-run tests laundered as executed")
    else:
        if (type(test.get("returncode")) is not int
                or type(test.get("duration_ms")) is not int
                or test["duration_ms"] < 0
                or not isinstance(test.get("log_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", test["log_sha256"])
                or type(test.get("log_bytes")) is not int or test["log_bytes"] < 0
                or (test["returncode"] == 0) != (test["state"] == "RUN_REPORTED_UNATTESTED")):
            raise ValueError("invalid untrusted test-exit envelope")
    seen = set()
    for x in test["parsed_cases"]:
        if (set(x) != {"activity_id", "state", "outcome"}
                or x["activity_id"] in seen
                or x["state"] not in ("RUN_REPORTED_UNATTESTED", "SKIPPED", "FAIL")):
            raise ValueError("malformed individual test event")
        seen.add(x["activity_id"])
    if receipt["attempts"] != _attempts(expected, receipt["baseline_pr36"], test):
        raise ValueError("unaccounted activity or forged per-method result")
    if receipt["gaps"] != _gap_register(expected, receipt["attempts"], test):
        raise ValueError("hidden blocker or missing evidence gap")
    if receipt["dod"] != _dod(repo, sha, test, receipt["baseline_pr36"]):
        raise ValueError("DoD state promotion or missing obligation")
    if receipt["metrics"] != _metrics(expected, receipt["attempts"], test):
        raise ValueError("activity count or proof-level promotion")
    m = receipt["execution_manifest"]
    if (m.get("commit") != sha or m.get("tree") != receipt["tree"]
            or m.get("source_receipt_digest") != receipt["baseline_pr36"]["receipt_digest"]
            or m.get("registry_digest") != expected["digest"]
            or m.get("local_test_log_sha256") != test["log_sha256"]
            or m.get("authorization") != "NONE"
            or m.get("trust") != "GIT_SOURCE_PLUS_UNATTESTED_LOCAL_CLAIMS"
            or m.get("runtime", {}).get("scope") != "LOCALLY_REPORTED_NOT_INDEPENDENTLY_ATTESTED"):
        raise ValueError("execution provenance altered")
    recorded = receipt.get("evidence_manifest")
    if (not isinstance(recorded, dict) or recorded.get("authority") != "NONE"
            or recorded.get("state") not in ("IN_REPORT_NOT_ON_DISK",
                "MATERIALIZED_LOCAL_NOT_INDEPENDENTLY_ATTESTED")):
        raise ValueError("forged evidence manifest status")
    # The log is not re-executed here. Its source and authenticity remain
    # unverified until an independent observing system supplies a witness.
    payloads = _artifact_payloads(receipt, None)
    evidence_files = {x["path"]: x for x in recorded["files"]}
    if len(evidence_files) != len(recorded["files"]):
        raise ValueError("duplicate evidence artifacts")
    required_files = set(payloads)
    if test["state"] != "NOT_RUN":
        required_files.add("unittest-verbose.log")
    if set(evidence_files) != required_files:
        raise ValueError("evidence artifact omitted")
    for path, payload in payloads.items():
        x = evidence_files[path]
        if (x["sha256"] != hashlib.sha256(payload).hexdigest()
                or x["bytes"] != len(payload) or x["trust"] != "LOCAL_UNATTESTED"):
            raise ValueError("content-addressed source evidence mismatch")
    if test["state"] != "NOT_RUN":
        x = evidence_files["unittest-verbose.log"]
        if x["sha256"] != test["log_sha256"] or x["bytes"] != test["log_bytes"]:
            raise ValueError("local test log evidence mismatch")
    if evidence_dir is not None:
        path = _outside_repo(repo, evidence_dir)
        if recorded["state"] != "MATERIALIZED_LOCAL_NOT_INDEPENDENTLY_ATTESTED":
            raise ValueError("claimed evidence materialization absent")
        for file in recorded["files"]:
            rel = file["path"]
            if not re.fullmatch(r"[A-Za-z0-9._-]+", rel):
                raise ValueError("unsafe evidence path")
            original = path / rel
            if not original.is_file() or original.is_symlink():
                raise ValueError("evidence artifact unavailable")
            data = original.read_bytes()
            if hashlib.sha256(data).hexdigest() != file["sha256"] or len(data) != file["bytes"]:
                raise ValueError("evidence was modified")
        if test["state"] != "NOT_RUN":
            raw = (path / "unittest-verbose.log").read_bytes()
            observed, total, warnings = _parse_unittest_log(raw)
            if (test["parsed_cases"] != observed or test["reported_tests"] != total
                    or test["parse_warnings"] != warnings):
                raise ValueError("individual test events diverge from retained log")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_digest"}
    if receipt.get("receipt_digest") != domain_hash("CORA:integrated-one-run:2", unsigned):
        raise ValueError("integrated receipt tampered")
    if html_page is not None:
        from .integrated_html import render_integrated_html
        if html_page != render_integrated_html(receipt):
            raise ValueError("integrated HTML is not byte-identical to JSON receipt")
    return True
