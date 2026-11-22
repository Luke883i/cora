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
import tempfile
import shutil
from pathlib import Path

from .evidence import domain_hash, valid_path
from .git_snapshot import git, snapshot
from .integrated_registry import build_registry, verify_contract, SCHEMA as REGISTRY_SCHEMA
from .one_run import run_one, verify_one
from .genealogy import build_genealogy, corpus_available, BASE as HISTORIC_GIT_ANCHOR
from .independent_qualification import build_qualification, verify_qualification, CONTRACT as QUALIFICATION_CONTRACT
from .process_suite import operational_selection, operational_requirement_plan
from .process_bounds import run_bounded
from .debt import parse_sarif, MAX_SARIF

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
OPERATION_SCHEMA = "cora-capability-operation/1"

PORTABLE_LINK_SCHEMA = "cora-integrated-portable-link/1"
PORTABLE_LINK_REQUEST = "cora-portable-link-request/1"


def _portable_source_target_link(repo: Path, source: dict, manifest: Path) -> dict:
    """Correlate two original verified receipts, without new execution effects."""
    from .foreign_pilot import reconcile_portable_capabilities
    path = Path(manifest)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("bounded regular portable request file required")
    raw = path.read_bytes()
    try:
        request = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid portable request JSON") from exc
    if (not isinstance(request, dict) or set(request) != {
            "schema", "target_repo", "target_receipt", "target_evidence_dir", "bindings"}
            or request["schema"] != PORTABLE_LINK_REQUEST
            or not isinstance(request["target_repo"], str)
            or not isinstance(request["target_evidence_dir"], str)
            or not Path(request["target_repo"]).is_absolute()
            or not Path(request["target_evidence_dir"]).is_absolute()
            or not isinstance(request["target_receipt"], dict)
            or not isinstance(request["bindings"], list)):
        raise ValueError("explicit independent target and test binding request required")
    target = Path(request["target_repo"]).resolve(strict=True)
    if target == Path(repo).resolve(strict=True):
        raise ValueError("CORA and target must be distinct repositories")
    result = reconcile_portable_capabilities(repo, source, target,
        request["target_receipt"], Path(request["target_evidence_dir"]),
        bindings=request["bindings"])
    return {"schema": PORTABLE_LINK_SCHEMA,
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "source_commit": source["commit"],
            "target_commit": result["target_commit"],
            "target_tree": result["target_tree"],
            "reconciliation": result, "scope_status": result["scope_status"],
            "product_status": "BLOCKED_EXTERNAL", "authority": "NONE"}




def _capability_request(repo: Path, baseline: dict, request: dict) -> tuple[list[dict], dict]:
    """Validate every choice and input before any optional subprocess."""
    if (not isinstance(request, dict) or set(request) != {
            "schema", "commit", "tree", "decisions", "tests", "semgrep", "timeout"}
            or request["schema"] != "cora-capability-request/1"
            or request["commit"] != baseline["commit"]
            or request["tree"] != git(repo, "rev-parse", baseline["commit"] + "^{tree}").decode().strip()
            or type(request["timeout"]) is not int or not 1 <= request["timeout"] <= 60):
        raise ValueError("exact-SHA bounded capability request required")
    rows = operational_selection(baseline, request)
    ledger = snapshot(repo, baseline["commit"])
    records = {r["path"]: r for r in ledger["records"]}
    def regular(path: str) -> None:
        if (not isinstance(path, str) or not valid_path(path) or path.startswith("-")
                or path not in records or records[path]["status"] != "observed_git_blob"):
            raise ValueError("capability input must be a regular original Git file")
    tests, expected = request["tests"], set()
    if not isinstance(tests, list) or len(tests) > 8:
        raise ValueError("bounded native test selection required")
    paths = set()
    for item in tests:
        if (not isinstance(item, dict) or set(item) != {"path", "ids"}
                or not isinstance(item["path"], str)
                or not re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", item["path"])
                or item["path"] in paths or not isinstance(item["ids"], list)
                or not 1 <= len(item["ids"]) <= 64):
            raise ValueError("native adapter requires unique unittest paths and expected IDs")
        regular(item["path"])
        module = Path(item["path"]).stem + "."
        for case in item["ids"]:
            if (not isinstance(case, str) or not re.fullmatch(r"[A-Za-z_][\w.]{1,250}", case)
                    or not case.startswith(module) or case in expected):
                raise ValueError("unbound or duplicate expected native test ID")
            expected.add(case)
        paths.add(item["path"])
    referred = {case for d in request["decisions"] for case in d["test_ids"]}
    if referred != expected:
        raise ValueError("every expected native test must link to a selected obligation")
    semgrep = request["semgrep"]
    selected = {r["id"] for r in rows if r["selected"]}
    if ("external:semgrep" in selected) != (semgrep is not None):
        raise ValueError("Semgrep configuration must match its explicit selection")
    if semgrep is not None:
        if (not isinstance(semgrep, dict) or set(semgrep) != {"rules", "targets"}
                or not isinstance(semgrep["targets"], list) or not 1 <= len(semgrep["targets"]) <= 32
                or len(set(semgrep["targets"])) != len(semgrep["targets"])
                or not isinstance(semgrep["rules"], dict) or set(semgrep["rules"]) != {"rules"}
                or not isinstance(semgrep["rules"]["rules"], list)
                or not 1 <= len(semgrep["rules"]["rules"]) <= 16):
            raise ValueError("bounded local Semgrep configuration required")
        for path in semgrep["targets"]:
            regular(path)
        rule_ids = set()
        for rule in semgrep["rules"]["rules"]:
            if (not isinstance(rule, dict) or set(rule) != {"id", "pattern", "message", "languages", "severity"}
                    or not isinstance(rule["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", rule["id"])
                    or rule["id"] in rule_ids or rule["languages"] != ["python"]
                    or rule["severity"] not in ("INFO", "WARNING", "ERROR")
                    or any(not isinstance(rule[k], str) or not 1 <= len(rule[k]) <= 1024
                           for k in ("pattern", "message"))):
                raise ValueError("only local Python pattern rules are qualified in this slice")
            rule_ids.add(rule["id"])
    return rows, records


def _operation_projection(baseline: dict, request: dict, observations: list[dict],
                          artifacts: dict[str, bytes]) -> dict:
    """Reconcile raw retained bytes; never infer behavior from an exit alone."""
    rows = operational_selection(baseline, request)
    expected_ops = {"test:" + x["path"] for x in request["tests"]}
    if request["semgrep"] is not None:
        expected_ops |= {"semgrep-version", "external:semgrep"}
    seen, test_events, test_ok, scanner = set(), {}, {}, None
    for obs in observations:
        if (not isinstance(obs, dict) or set(obs) != {"id", "returncode", "reason", "duration_ms", "log", "sarif", "json"}
                or obs["id"] not in expected_ops or obs["id"] in seen
                or type(obs["duration_ms"]) is not int or obs["duration_ms"] < 0
                or (obs["returncode"] is not None and type(obs["returncode"]) is not int)
                or obs["reason"] not in ("EXIT_REPORTED", "TIMEOUT", "OUTPUT_LIMIT", "OS_ERROR", "NOT_INSTALLED")
                or obs["log"] not in artifacts):
            raise ValueError("invalid local capability observation")
        seen.add(obs["id"])
        raw = artifacts[obs["log"]]
        if obs["id"].startswith("test:"):
            cases, count, warnings = _parse_unittest_log(raw)
            ids = {r["activity_id"].split(":", 2)[-1] for r in cases}
            # The legacy parser uses a path prefix; recover the original dotted IDs.
            module = Path(obs["id"].removeprefix("test:")).stem
            ids = {module + "." + name for name in ids}
            expected = next(x["ids"] for x in request["tests"] if "test:" + x["path"] == obs["id"])
            good = (obs["reason"] == "EXIT_REPORTED" and obs["returncode"] == 0
                    and count is not None and count > 0 and not warnings
                    and all(x["state"] == "RUN_REPORTED_UNATTESTED" and x["outcome"] == "ok" for x in cases)
                    and set(expected) <= ids)
            for name in ids:
                if name in test_events:
                    raise ValueError("duplicate native event across test runs")
                test_events[name] = {"observation": obs["id"], "log": obs["log"], "successful_run": good}
            test_ok[obs["id"]] = good
        elif obs["id"] == "external:semgrep":
            scanner = "FAIL"
            if obs["sarif"] is not None and obs["sarif"] in artifacts and obs["reason"] == "EXIT_REPORTED":
                try:
                    payload = artifacts[obs["sarif"]]
                    parsed = parse_sarif(payload, set(request["semgrep"]["targets"]))
                    doc = json.loads(payload)
                    scan = json.loads(artifacts[obs["json"]])
                    valid = (len(doc["runs"]) == 1 and
                             "semgrep" in doc["runs"][0]["tool"]["driver"]["name"].casefold() and
                             not parsed["unknown"] and
                             scan["errors"] == [] and
                             set(scan["paths"]["scanned"]) == set(request["semgrep"]["targets"]) and
                             sorted((x["path"], x["start"]["line"]) for x in scan["results"]) ==
                             sorted((x["path"], x["line"]) for x in parsed["rows"]) and
                             all(i.get("executionSuccessful", True) is True and
                                 all(n.get("level") != "error" for n in i.get("toolExecutionNotifications", []))
                                 for i in doc["runs"][0].get("invocations", [])))
                    if valid and obs["returncode"] in (0, 1):
                        scanner = "FINDINGS" if parsed["rows"] else "SCOPED_NO_FINDINGS" if obs["returncode"] == 0 else "FAIL"
                except (ValueError, KeyError, TypeError, AttributeError):
                    scanner = "FAIL"
    if observations and seen != expected_ops:
        raise ValueError("partial capability execution ledger")
    allowed_files = {o["log"] for o in observations} | {
        o[k] for o in observations for k in ("sarif", "json") if o[k] is not None}
    if set(artifacts) != allowed_files:
        raise ValueError("unaccounted capability artifacts")
    version_ok = any(o["id"] == "semgrep-version" and o["returncode"] == 0 and
                     o["reason"] == "EXIT_REPORTED" and
                     re.fullmatch(rb"[0-9]+\.[0-9]+\.[0-9]+\s*", artifacts[o["log"]]) for o in observations)
    for row in rows:
        if not row["selected"]:
            continue
        row["test_evidence"] = [{"id": name, **test_events[name]} for name in row["decision"]["test_ids"] if name in test_events]
        row["tests_satisfied"] = bool(row["decision"]["test_ids"]) and all(
            test_events.get(name, {}).get("successful_run") is True for name in row["decision"]["test_ids"])
        if row["id"] == "external:semgrep":
            row["state"] = scanner if scanner is not None else "BLOCKED_EXECUTION_OPT_IN_REQUIRED"
            if scanner == "SCOPED_NO_FINDINGS" and not version_ok:
                row["state"] = "FAIL"
    successful = {"REUSED_SOURCE_METHOD_SCOPED", "REUSED_NATIVE_OBSERVATION_UNATTESTED", "SCOPED_NO_FINDINGS"}
    pending = [{"id": r["id"], "reason": r["state"] if r["state"] not in successful else "NATIVE_TEST_EVIDENCE_MISSING_OR_FAILED",
                "obligation": r["decision"]["obligation"]}
               for r in rows if r["selected"] and (r["state"] not in successful or not r["tests_satisfied"])]
    return {"rows": rows, "tests": test_events, "test_runs": test_ok,
            "scoped_runtime_goal": "PASS_SCOPED_LOCAL_UNATTESTED" if not pending else "DEBT_BLOCKED",
            "agent_handoff": {"gaps": pending, "next_unresolved": pending[0] if pending else None,
                              "extension": "AGENT_JUDGMENT_REQUIRES_QUALIFIED_ADAPTER_NOT_AUTOMATIC_CODEGEN"},
            "duplicate_source_executions": 0, "product_status": "BLOCKED_EXTERNAL", "authority": "NONE"}


def run_capability_operation(repo: Path, baseline: dict, request: dict, *,
                             execute: bool, evidence_dir: Path | None) -> dict:
    rows, records = _capability_request(repo, baseline, request)
    if type(execute) is not bool or execute and evidence_dir is None:
        raise ValueError("capability execution needs explicit opt-in and retained evidence")
    out = _outside_repo(repo, evidence_dir) if evidence_dir is not None else None
    observations, artifacts = [], {}
    if execute:
        if (any(r["status"] != "observed_git_blob" for r in records.values()) or
                sum(r["size"] for r in records.values()) > 32 * 1024 * 1024):
            raise ValueError("execution snapshot contains unresolved objects or exceeds 32MiB")
        out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cora-capabilities-", dir=out) as temp:
            work = Path(temp)
            for path, record in records.items():
                dst = work / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(git(repo, "cat-file", "blob", record["git_oid"], max_output=8 * 1024 * 1024))
                dst.chmod(0o755 if record["mode"] == "100755" else 0o644)
            # A disposable Git-byte copy is not an OS sandbox. Never forward credentials.
            env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "LANG") if k in os.environ}
            env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(work / "src") + os.pathsep + str(work),
                       SEMGREP_SEND_METRICS="off", SEMGREP_ENABLE_VERSION_CHECK="0",
                       SEMGREP_SETTINGS_FILE=str(work / ".cora-semgrep-settings.yml"))
            def observe(key: str, argv: list[str] | None, sarif: Path | None = None,
                        scan_json: Path | None = None) -> None:
                start = time.monotonic()
                code, reason, raw = None, "NOT_INSTALLED", b"tool not installed\n"
                if argv is not None:
                    try:
                        done = run_bounded(argv, cwd=work, timeout=request["timeout"], max_output=MAX_SARIF, env=env)
                        code, reason, raw = done.returncode, "EXIT_REPORTED", done.stdout
                    except subprocess.TimeoutExpired:
                        reason, raw = "TIMEOUT", b"bounded subprocess timeout\n"
                    except ValueError:
                        reason, raw = "OUTPUT_LIMIT", b"bounded subprocess output refused\n"
                    except OSError:
                        reason, raw = "OS_ERROR", b"bounded subprocess OS error\n"
                number = len(observations)
                log_name = "capability-%02d.log" % number
                artifacts[log_name] = raw
                outputs = {"sarif": None, "json": None}
                for kind, path in (("sarif", sarif), ("json", scan_json)):
                    if path is not None and path.is_file() and not path.is_symlink():
                        if path.stat().st_size <= MAX_SARIF:
                            outputs[kind] = "capability-%02d.%s" % (number, kind)
                            artifacts[outputs[kind]] = path.read_bytes()
                        else:
                            code, reason = None, "OUTPUT_LIMIT"
                observations.append({"id": key, "returncode": code, "reason": reason,
                                     "duration_ms": max(0, int((time.monotonic() - start) * 1000)),
                                     "log": log_name, **outputs})
            if request["semgrep"] is not None:
                config = work / ".cora-semgrep-rules.json"
                sarif = work / ".cora-semgrep-output.sarif"
                scan_json = work / ".cora-semgrep-output.json"
                if any(p.exists() for p in (config, sarif, scan_json, work / ".cora-semgrep-settings.yml")):
                    raise ValueError("reserved capability scratch path collision")
                config.write_bytes(_serialize(request["semgrep"]["rules"]))
                binary = shutil.which("semgrep")
                observe("semgrep-version", [binary, "--version"] if binary else None)
                argv = ([binary, "scan", "--oss-only", "--config", str(config), "--metrics=off",
                         "--disable-version-check", "--no-git-ignore", "--strict", "--error",
                         "--sarif-output", str(sarif), "--json-output", str(scan_json),
                         "--", *request["semgrep"]["targets"]] if binary else None)
                observe("external:semgrep", argv, sarif, scan_json)
            for test in request["tests"]:
                observe("test:" + test["path"], [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", Path(test["path"]).name, "-v"])
    projection = _operation_projection(baseline, request, observations, artifacts)
    report = {"schema": OPERATION_SCHEMA, "commit": baseline["commit"], "tree": request["tree"],
              "request": request, "execution_opt_in": execute, "observations": observations,
              "artifacts": [{"path": k, "sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v), "trust": "LOCAL_UNATTESTED"}
                            for k, v in sorted(artifacts.items())], **projection}
    if out is not None and artifacts:
        out.mkdir(parents=True, exist_ok=True)
        for name, raw in artifacts.items():
            dest = out / name
            if dest.is_symlink() or dest.exists():
                raise ValueError("capability evidence may not overwrite existing files")
            dest.write_bytes(raw)
    return report


def verify_capability_operation(repo: Path, baseline: dict, report: dict,
                                evidence_dir: Path | None) -> bool:
    from .native_gold import _read_bounded
    _capability_request(repo, baseline, report["request"])
    raw = {}
    if report["artifacts"] and evidence_dir is None:
        raise ValueError("capability replay requires retained observation bytes")
    if len({a["path"] for a in report["artifacts"]}) != len(report["artifacts"]):
        raise ValueError("duplicate capability artifact")
    for item in report["artifacts"]:
        if not re.fullmatch(r"capability-[0-9]{2}\.(log|sarif|json)", item["path"]):
            raise ValueError("unsafe capability evidence path")
        payload = _read_bounded(_outside_repo(repo, evidence_dir), item["path"], MAX_SARIF)
        if item != {"path": item["path"], "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "trust": "LOCAL_UNATTESTED"}:
            raise ValueError("capability evidence differs from retained bytes")
        raw[item["path"]] = payload
    expected = {"schema": OPERATION_SCHEMA, "commit": baseline["commit"], "tree": report["request"]["tree"],
                "request": report["request"], "execution_opt_in": report["execution_opt_in"],
                "observations": report["observations"], "artifacts": report["artifacts"],
                **_operation_projection(baseline, report["request"], report["observations"], raw)}
    if type(report["execution_opt_in"]) is not bool or (not report["execution_opt_in"] and report["observations"]):
        raise ValueError("execution outside declared opt-in")
    if expected != report:
        raise ValueError("capability claims do not replay from source and retained evidence")
    return True


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


def _attempts(registry: dict, baseline: dict, test: dict,
              hforge: dict | None = None) -> list[dict]:
    executed = {row["id"]: row for row in baseline["activities"]}
    cli_observed = {x["command"]: x for x in baseline.get("cli_capability_attempts", [])}
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
        elif row["kind"] == "PROFILE_STAGE" and key == "stage:hforge-source":
            state = ("EXECUTED_SCOPED" if hforge and
                     hforge["state"] == "PASS_SCOPED_GIT_SOURCE_AND_REPLAY"
                     else "BLOCKED")
            reason = hforge["state"] if hforge else "HFORGE_EVIDENCE_MISSING"
            origin = hforge.get("legacy_receipt_digest") if hforge else None
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
            bounded = cli_observed.get(key.removeprefix("cli:"))
            if bounded is not None:
                state, reason = bounded["state"], bounded["reason"]
                origin = bounded["stdout_sha256"]
            else:
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
                              if key in observed and test["log_sha256"] else
                              ["BOUNDED_CLI_OUTPUT_SHA256:" + origin]
                              if row["kind"] == "CLI_COMMAND" and state == "RUN_REPORTED_UNATTESTED"
                              and origin else []),
            "verification": ("SOURCE_REPLAY_ELIGIBLE" if row["kind"] == "INTERNAL_METHOD"
                             and state in ("EXECUTED_SCOPED", "REUSED_SCOPED")
                             else "UNATTESTED_LOCAL_EXIT" if key in observed or
                             row["kind"] == "CLI_COMMAND" and state == "RUN_REPORTED_UNATTESTED"
                             else "NOT_VERIFIED"),
            "authority": "NONE",
        })
    return rows


def _gap_register(registry: dict, attempts: list[dict], test: dict,
                  hforge: dict | None = None) -> dict:
    reasons: dict[str, list[str]] = {}
    for attempt in attempts:
        if attempt["state"] in ("NOT_RUN", "BLOCKED", "FAIL", "SKIPPED"):
            reasons.setdefault(attempt["reason"] or attempt["state"], []).append(attempt["activity_id"])
    if hforge and hforge["state"] != "NOT_APPLICABLE_PROFILE_NOT_COMMITTED":
        reasons["HFORGE_P2_AND_P5_UNATTESTED"] = ["stage:hforge-source"]
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
        "individually_executed_cli": sum(x["state"] == "RUN_REPORTED_UNATTESTED"
                                         and x["activity_id"].startswith("cli:") for x in attempts),
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
             "hforge.json": _serialize(bundle["hforge"]),
             "attempts.json": _serialize(bundle["attempts"]),
             "gaps.json": _serialize(bundle["gaps"]),
             "dod.json": _serialize(bundle["dod"]),
             "execution-manifest.json": _serialize(bundle["execution_manifest"])}
    if "genealogy" in bundle:
        files["genealogy.json"] = _serialize(bundle["genealogy"])
    if "qualification" in bundle:
        files["qualification.json"] = _serialize(bundle["qualification"])
    if "capability_operation" in bundle:
        files["capability-operation.json"] = _serialize(bundle["capability_operation"])
    if "portable_link" in bundle:
        files["portable-link.json"] = _serialize(bundle["portable_link"])
    if log is not None:
        files["unittest-verbose.log"] = log
    return files


def _manifest(bundle: dict, log: bytes | None, materialized: bool) -> dict:
    return {"schema": "cora-integrated-evidence-manifest/2",
            "state": "MATERIALIZED_LOCAL_NOT_INDEPENDENTLY_ATTESTED" if materialized
                     else "IN_REPORT_NOT_ON_DISK",
            "files": [{"path": k, "sha256": hashlib.sha256(v).hexdigest(),
                       "bytes": len(v), "trust": "LOCAL_UNATTESTED"}
                      for k, v in sorted(_artifact_payloads(bundle, log).items())]
                     + bundle.get("capability_operation", {}).get("artifacts", []),
            "authority": "NONE"}



def _hforge_source(repo: Path, sha: str, baseline: dict) -> dict:
    """Safe, replayable Git projection of H-FORGE, never target code execution."""
    from .integrated_registry import tree_paths
    names = set(tree_paths(repo, sha))
    required = {".cora/contracts/dod/hforge-transplant-dod.json",
                ".cora/contracts/profiles/hforge-profile-v1.json",
                "tools/hforge_profile.py"}
    common = {"schema": "cora-hforge-integrated-source/1", "commit": sha,
              "authorization": "NONE", "product_status": "BLOCKED_EXTERNAL",
              "native": "NOT_RUN_REQUIRES_CONSENT", "p5": "BLOCKED_EXTERNAL"}
    if not required.issubset(names):
        return {**common, "state": "NOT_APPLICABLE_PROFILE_NOT_COMMITTED",
                "missing": sorted(required-names)}
    doc = json.loads(git(repo, "show", sha +
        ":.cora/contracts/dod/hforge-transplant-dod.json").decode("utf-8"))
    profile = json.loads(git(repo, "show", sha +
        ":.cora/contracts/profiles/hforge-profile-v1.json").decode("utf-8"))
    clause = doc.get("one_run_absorption", {})
    if (doc.get("authority") != "NONE" or
        clause.get("schema") != "cora-hforge-one-run-absorption/1" or
        clause.get("authority") != "NONE" or clause.get("native_default") != "NOT_RUN" or
        clause.get("global_product") != "NOT_DEMONSTRATED" or
        len(clause.get("phases", [])) != 13 or
        len(set(clause.get("phases", []))) != 13 or
        len(clause.get("invariants", [])) != 12 or
        profile.get("schema") != "cora-hforge-profile/1" or
        profile.get("integration") != "PROFILE_NOT_ENGINE" or
        profile.get("required_scenarios", {}).get("declared_cli_help") != 71 or
        len(profile.get("required_scenarios", {}).get("native", [])) != 6):
        raise ValueError("H-FORGE original Git DoD/profile is not qualified")
    base = baseline["source_process"].get("change_base")
    if base is None:
        try:
            base = git(repo, "rev-parse", sha+"^").decode().strip()
        except ValueError:
            return {**common, "state": "DEBT_BLOCKED_ROOT_HAS_NO_PARENT"}
    if base == sha or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", base):
        raise ValueError("H-FORGE requires a distinct full original Git BASE")
    git(repo, "merge-base", "--is-ancestor", base, sha)
    def measure(rev: str) -> dict:
        raw = git(repo, "ls-tree", "-r", "-l", "-z", rev, max_output=16000000)
        if not raw.endswith(b"\0"):
            raise ValueError("H-FORGE truncated original tree")
        count = byte_size = links = 0
        for record in raw.split(b"\0")[:-1]:
            meta, path = record.split(b"\t", 1)
            mode, kind, oid, size = meta.split()
            if not path or b"\n" in path:
                raise ValueError("ambiguous H-FORGE path")
            if kind == b"commit" and mode == b"160000":
                links += 1
            elif kind == b"blob" and mode in (b"100644", b"100755", b"120000") and size.isdigit():
                count += 1
                byte_size += int(size)
            else:
                raise ValueError("unqualified H-FORGE original Git object")
        return {"files": count, "bytes": byte_size, "gitlinks": links,
                "tree_sha256": hashlib.sha256(raw).hexdigest()}
    before, after = measure(base), measure(sha)
    if verify_one(repo, baseline) is not True:
        raise ValueError("original One-Run did not replay for H-FORGE")
    return {**common, "state": ("PASS_SCOPED_GIT_SOURCE_AND_REPLAY"
                                if not (before["gitlinks"] or after["gitlinks"])
                                else "DEBT_BLOCKED_GITLINKS"),
            "base": base, "before": before, "after": after,
            "delta_files": after["files"]-before["files"],
            "delta_bytes": after["bytes"]-before["bytes"],
            "p0": "PASS_EXACT_GIT", "p1": "HOLD_NO_77_CASE_RECEIPT",
            "p2": "NOT_RUN_CONSENT_REQUIRED", "p3": "GIT_TREE_ONLY",
            "p4": "PASS_ORIGINAL_ONE_RUN_SOURCE_REPLAY",
            "legacy_receipt_digest": baseline["receipt_digest"]}


class ComprehensiveHistoryUnavailable(ValueError):
    """Comprehensive replay needs original Git objects, not just ZIP source bytes."""

    code = "CORA_HISTORY_UNAVAILABLE"
    safe_mode = "ZIP_INTAKE_SOURCE_ONLY"


def preflight_comprehensive_history(repo: Path, revision: str = "HEAD") -> dict:
    """Bounded, read-only history check; never authenticate GitHub or infer provenance.

    A forged local commit graph cannot qualify the historic CORA corpus: where
    its committed history register exists, the original PR38 anchor must be a
    real ancestor. All other source repositories still require usable parents.
    """
    repo = Path(repo).resolve(strict=True)

    def blocked(reason: str) -> None:
        raise ComprehensiveHistoryUnavailable(
            f"CORA_HISTORY_UNAVAILABLE[{reason}]: comprehensive replay needs an "
            "unshallowed original Git checkout with its historical objects; "
            "do not claim original Git history from an extracted ZIP. "
            "Safe source-only alternative: cora zip-intake <original-archive.zip>. "
            "No release or external authority is inferred.")

    try:
        if git(repo, "rev-parse", "--is-shallow-repository").strip() == b"true":
            blocked("SHALLOW_CHECKOUT")
        sha = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode("ascii").strip()
        git(repo, "cat-file", "-e", sha + "^{tree}")
        parents = git(repo, "rev-list", "--parents", "-n", "1", sha).decode("ascii").split()
    except ComprehensiveHistoryUnavailable:
        raise
    except (ValueError, OSError, UnicodeError):
        blocked("GIT_OBJECTS_MISSING_OR_INVALID")
    if not parents or parents[0] != sha or len(parents) < 2:
        blocked("NO_PARENT_HISTORY")
    if corpus_available(repo, sha):
        try:
            git(repo, "merge-base", "--is-ancestor", HISTORIC_GIT_ANCHOR, sha)
        except ValueError:
            blocked("ORIGINAL_CORPUS_ANCESTRY_UNAVAILABLE")
    return {"schema": "cora-comprehensive-history-preflight/1",
            "commit": sha, "state": "GIT_OBJECTS_AND_LINEAGE_READABLE_NOT_HOST_ATTESTED",
            "authority": "NONE", "zip_source_mode": "NOT_COMPREHENSIVE"}


def run_integrated(repo: Path, revision: str = "HEAD", *, process: str = "full",
                   max_commits: int = 64, focus: str | None = None,
                   execute_self_tests: bool = False,
                   authorization_file: Path | None = None,
                   evidence_dir: Path | None = None,
                   test_timeout: int = 240, model_stress_cases: int = 0,
                   change_base: str | None = None,
                   capability_intent: str | None = None,
                   capability_request: Path | None = None,
                   execute_capabilities: bool = False,
                   portable_link: Path | None = None) -> dict:
    repo = Path(repo).resolve(strict=True)
    preflight_comprehensive_history(repo, revision)
    sha = snapshot(repo, revision)["commit"]
    tree = git(repo, "rev-parse", sha + "^{tree}").decode("ascii").strip()
    if execute_self_tests != (authorization_file is not None):
        raise ValueError("comprehensive self-tests require both opt-in and an exact-SHA consent file")
    if execute_capabilities and (capability_request is None or execute_self_tests):
        raise ValueError("capability execution requires a request and cannot duplicate the full self-test run")
    if portable_link is not None and (evidence_dir is None or execute_self_tests):
        raise ValueError("portable target linkage needs retained evidence and no CORA self-test execution")
    out = _outside_repo(repo, evidence_dir) if evidence_dir is not None else None
    if execute_self_tests and (not (repo / ".git").exists() or
                                git(repo, "rev-parse", "HEAD").decode().strip() != sha):
        raise ValueError("only the explicitly authorized CORA HEAD checkout may run self-tests")
    registry = build_registry(repo, sha)
    base = run_one(repo, sha, process=process, max_commits=max_commits,
                   focus=focus, execute_self_tests=False,
                   model_stress_cases=model_stress_cases,change_base=change_base,
                   capability_intent=capability_intent)
    hforge = _hforge_source(repo, sha, base)
    test, log = _test_observation(repo, sha, tree,
                                  authorized=authorization_file if execute_self_tests else None,
                                  evidence_dir=out, timeout=test_timeout)
    attempts = _attempts(registry, base, test, hforge)
    order = _topological(registry)
    gaps = _gap_register(registry, attempts, test, hforge)
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
        "baseline_pr36": base, "registry": registry, "hforge": hforge,
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
    if capability_request is not None:
        if capability_request.stat().st_size > 128 * 1024:
            raise ValueError("capability request exceeds 128KiB")
        bundle["capability_contract"] = operational_requirement_plan(repo, sha)
        request = json.loads(capability_request.read_text("utf-8"))
        bundle["capability_operation"] = run_capability_operation(
            repo, base, request, execute=execute_capabilities, evidence_dir=out)
    if portable_link is not None:
        bundle["portable_link"] = _portable_source_target_link(repo, base, portable_link)
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
                      evidence_dir: Path | None = None,
                      portable_link: Path | None = None) -> bool:
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
    actual_hforge = _hforge_source(repo, sha, receipt["baseline_pr36"])
    if receipt.get("hforge") != actual_hforge:
        raise ValueError("H-FORGE evidence omitted, altered or cross-revision")
    if receipt["attempts"] != _attempts(expected, receipt["baseline_pr36"], test, actual_hforge):
        raise ValueError("unaccounted activity or forged per-method result")
    if receipt["gaps"] != _gap_register(expected, receipt["attempts"], test, actual_hforge):
        raise ValueError("hidden blocker or missing evidence gap")
    if receipt["dod"] != _dod(repo, sha, test, receipt["baseline_pr36"]):
        raise ValueError("DoD state promotion or missing obligation")
    if receipt["metrics"] != _metrics(expected, receipt["attempts"], test):
        raise ValueError("activity count or proof-level promotion")
    if "capability_operation" in receipt:
        required = operational_requirement_plan(repo, sha)
        if receipt.get("capability_contract") != required:
            raise ValueError("operational contract or AND cut altered")
        verify_capability_operation(repo, receipt["baseline_pr36"], receipt["capability_operation"], evidence_dir)
    elif "capability_contract" in receipt:
        raise ValueError("operational DoD without capability evidence")
    if "portable_link" in receipt:
        if portable_link is None or evidence_dir is None:
            raise ValueError("portable link replay requires original request and retained evidence")
        expected_link = _portable_source_target_link(repo, receipt["baseline_pr36"], portable_link)
        if receipt["portable_link"] != expected_link:
            raise ValueError("portable 81-owner to native test correlation altered")
    elif portable_link is not None:
        raise ValueError("unexpected external target link for unlinked receipt")
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
    capability_files = receipt.get("capability_operation", {}).get("artifacts", [])
    required_files.update(f["path"] for f in capability_files)
    if set(evidence_files) != required_files:
        raise ValueError("evidence artifact omitted")
    if any(evidence_files[f["path"]] != f for f in capability_files):
        raise ValueError("capability manifest differs from observation artifacts")
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
