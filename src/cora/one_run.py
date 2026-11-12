"""Single-run CORA source assurance + honest execution HTML.

The existing process-run is the only owner of source method execution.
The original maturity_atlas is the only owner of CORA's 71-command catalog.
Neither a source method receipt nor an opt-in unittest exit authenticates product
behavior, a third-party review, or a release.
"""
from __future__ import annotations

import copy
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git, snapshot
from .maturity_atlas import build_atlas, render_html
from .process_suite import run_suite, verify_suite, IMPLEMENTED, process_catalog
from .reticulum import assess_cut, ordered_cut, EXTERNAL, MODEL
from .synergy import unified_assurance

SCHEMA = "cora-one-run/1"
DOD = ".cora/contracts/dod/one-run-dod.json"
HTML_MARKER = "CORA ONE-RUN | EXECUTION-BOUNDED"
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
STATUS_MAP = {
    "EXECUTED_SCOPED": "EXECUTED_SCOPED",
    "REUSED_SCOPED_FROM_HOLISTIC": "REUSED_SCOPED",
    "DEBT_BLOCKED": "BLOCKED",
    "NOT_RUN_REQUIRES_FOCUS": "NOT_RUN",
}
OUTCOMES = {"EXECUTED_SCOPED", "REUSED_SCOPED", "FAIL", "BLOCKED",
            "NOT_RUN", "RUN_REPORTED_UNATTESTED"}
METHOD_FILES = {
    "git_snapshot": "src/cora/git_snapshot.py",
    "artifact_roles": "src/cora/artifact_roles.py",
    "manifest_adapters": "src/cora/adapters.py",
    "git_archaeology": "src/cora/archaeology.py",
    "python_candidate_graph": "src/cora/graph.py",
    "holistic_archaeology": "src/cora/holistic.py",
    "debt_signals": "src/cora/debt.py",
    "file_selection_if_focus": "src/cora/selection.py",
}
# This exact dependency graph is independent of editable JSON declarations.
EDGES = {
    "G_EXECUTION": ["L_GIT", "L_ENTRY", "L_SOURCE_RUN", "L_OUTCOMES", "L_TIMINGS", "L_LINEAGE"],
    "G_PRESENTATION": ["L_CATALOG", "L_GAPS", "L_CONSENT", "L_JSON", "L_HTML", "L_ESCAPE"],
    "G_SOURCE_REPLAY": ["L_REPLAY", "L_100K", "L_REAL_MUTANTS"],
    "G_ONE_RUN_SOURCE": ["G_EXECUTION", "G_PRESENTATION", "G_SOURCE_REPLAY"],
    "G_GOVERNED_ONE_RUN": [
        "G_ONE_RUN_SOURCE", "E_TARGET_RUNTIME", "E_TEST_ORACLE",
        "E_USABILITY", "E_HOST", "E_REVIEW"],
    "G_ONE_RUN_PRODUCT": ["G_GOVERNED_ONE_RUN", "E_RELEASE"],
}
SOURCE_LEAVES = {
    "L_GIT", "L_ENTRY", "L_SOURCE_RUN", "L_OUTCOMES", "L_TIMINGS",
    "L_LINEAGE", "L_CATALOG", "L_GAPS", "L_CONSENT", "L_JSON",
    "L_HTML", "L_ESCAPE", "L_REPLAY", "L_100K", "L_REAL_MUTANTS",
}
EXTERNAL_LEAVES = {
    "E_TARGET_RUNTIME", "E_TEST_ORACLE", "E_USABILITY",
    "E_HOST", "E_REVIEW", "E_RELEASE",
}
ALL_IDS = set(EDGES) | SOURCE_LEAVES | EXTERNAL_LEAVES


def _original_dod(repo: Path, sha: str) -> dict:
    data = json.loads(git(repo, "show", sha + ":" + DOD, max_output=128 * 1024))
    nodes = data.get("nodes")
    if (data.get("schema") != "cora-one-run-dod/1"
            or data.get("authority") != "NONE"
            or data.get("source_goal") != "G_ONE_RUN_SOURCE"
            or data.get("global_goal") != "G_ONE_RUN_PRODUCT"
            or not isinstance(nodes, list) or len(nodes) != len(ALL_IDS)
            or len({n.get("id") for n in nodes}) != len(nodes)
            or {n["id"] for n in nodes} != ALL_IDS):
        raise ValueError("one-run original Git DoD identity drift")
    for node in nodes:
        key = node["id"]
        scope = "EXTERNAL" if key in EXTERNAL_LEAVES or key in (
            "G_GOVERNED_ONE_RUN", "G_ONE_RUN_PRODUCT") else "SOURCE"
        if node.get("scope") != scope or node.get("depends_on") != EDGES.get(key, []):
            raise ValueError("one-run mandatory DoD edge/scope drift")
        if key in EXTERNAL_LEAVES and node.get("witness_paths"):
            raise ValueError("external DoD promoted from source")
    if len(ordered_cut(nodes, "G_ONE_RUN_PRODUCT")) != len(nodes):
        raise ValueError("orphan one-run DoD nodes")
    m = data.get("metrics", {})
    if (m.get("commands_declared") != 71 or m.get("safe_source_method_count") != 8
            or m.get("min_seeded_cases") != 100000
            or m.get("positive_control_families") != 2
            or m.get("negative_fault_families") != 30
            or m.get("max_oracle_disagreements") != 0
            or m.get("max_unsafe_promotions") != 0
            or m.get("publication_authorized") is not False):
        raise ValueError("one-run quantitative DoD drift")
    assessed = assess_cut(nodes, "G_ONE_RUN_PRODUCT",
                          {name: MODEL for name in SOURCE_LEAVES})
    if (assessed["states"]["G_ONE_RUN_SOURCE"] != MODEL
            or assessed["status"] != EXTERNAL
            or assessed["authorization"] != "NONE"):
        raise ValueError("one-run DoD cannot become external PASS")
    return {"nodes": len(nodes), "gates": {
        "G_EXECUTION": assessed["states"]["G_EXECUTION"],
        "G_PRESENTATION": assessed["states"]["G_PRESENTATION"],
        "G_SOURCE_REPLAY": assessed["states"]["G_SOURCE_REPLAY"],
        "G_ONE_RUN_SOURCE": assessed["states"]["G_ONE_RUN_SOURCE"],
        "G_GOVERNED_ONE_RUN": assessed["states"]["G_GOVERNED_ONE_RUN"],
        "G_ONE_RUN_PRODUCT": assessed["states"]["G_ONE_RUN_PRODUCT"]},
        "checklist": data["checklist"], "goal": assessed["status"],
        "authority": "NONE", "source_level": "SOURCE_MODEL_NOT_EXECUTION_PROOF"}


def _is_cora(repo: Path, sha: str) -> bool:
    try:
        raw = git(repo, "show", sha + ":cora.ontology.json", max_output=64 * 1024)
        ontology = json.loads(raw)
        return isinstance(ontology, dict) and "cora" in str(ontology).lower() and (
            git(repo, "cat-file", "-e", sha + ":" + DOD, max_output=1024) == b"")
    except (ValueError, KeyError, subprocess.CalledProcessError):
        return False


ROW_FIELDS = {"id", "state", "source_state", "source", "commit",
              "source_digest", "reason", "elapsed_ms", "timing_basis",
              "proof_scope", "authority"}


def validate_execution_row(row: dict) -> bool:
    """Bounded semantic grammar also used by the 100k mutation verifier.

    Structural validity is not execution provenance; verify_one additionally
    compares these fields to an independently recomputed original-Git report.
    """
    if not isinstance(row, dict) or set(row) != ROW_FIELDS:
        raise ValueError("execution row missing, duplicate or unknown fields")
    name = row["id"]
    raw = row["source_state"]
    state = row["state"]
    elapsed = row["elapsed_ms"]
    timing = row["timing_basis"]
    digest = row["source_digest"]
    if (name not in METHOD_FILES or row["source"] != METHOD_FILES[name]
            or not isinstance(row["commit"], str) or not SHA.fullmatch(row["commit"])
            or raw not in STATUS_MAP or state != STATUS_MAP[raw]
            or state not in OUTCOMES
            or row["proof_scope"] != "GIT_SOURCE_METHOD_NOT_PRODUCT_BEHAVIOR"
            or row["authority"] != "NONE"
            or (digest is not None and (
                not isinstance(digest, str) or
                not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", digest)))
            or (elapsed is not None and (
                type(elapsed) is not int or not 0 <= elapsed <= 3600000))
            or timing not in ("DIRECT_METHOD_EXECUTION",
                              "SHARED_HOLISTIC_INVOCATION",
                              "REUSED_NOT_INDEPENDENTLY_TIMED",
                              "SOURCE_METHOD_UNAVAILABLE", "NOT_INVOKED")):
        raise ValueError("invalid execution row or unauthorized status promotion")
    if (state == "EXECUTED_SCOPED" and (
            elapsed is None or timing != "DIRECT_METHOD_EXECUTION"
            or row["reason"] is not None)
            or state == "REUSED_SCOPED" and (
                timing not in ("SHARED_HOLISTIC_INVOCATION", "REUSED_NOT_INDEPENDENTLY_TIMED")
                or (timing == "REUSED_NOT_INDEPENDENTLY_TIMED" and elapsed is not None)
                or (timing == "SHARED_HOLISTIC_INVOCATION" and elapsed is None)
                or row["reason"] is not None)
            or state == "NOT_RUN" and (
                elapsed is not None or timing != "NOT_INVOKED" or digest is not None)
            or state == "BLOCKED" and (
                not isinstance(row["reason"], str) or not row["reason"]
                or timing != "SOURCE_METHOD_UNAVAILABLE"
                and timing != "DIRECT_METHOD_EXECUTION")):
        raise ValueError("execution timing or error cannot be laundered")
    return True


def validate_execution_rows(rows: list[dict], *, expected_commit: str | None = None) -> bool:
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError("bounded one-run source methods only")
    if len({x.get("id") for x in rows if isinstance(x, dict)}) != len(rows):
        raise ValueError("duplicate source method observation")
    if not all(validate_execution_row(x) for x in rows):
        raise ValueError("unverifiable execution rows")
    if expected_commit is not None and (
            not SHA.fullmatch(expected_commit) or
            any(row["commit"] != expected_commit for row in rows)):
        raise ValueError("cross-commit execution evidence rejected")
    return True


def _row(method: dict, commit: str) -> dict:
    raw = method["status"]
    if raw not in STATUS_MAP or method["method"] not in METHOD_FILES:
        raise ValueError("unknown or unclassifiable source method")
    status = STATUS_MAP[raw]
    elapsed = method.get("elapsed_ms")
    timing = method.get("timing_basis")
    if (elapsed is not None and (type(elapsed) is not int or not 0 <= elapsed <= 3600000)
            or timing not in ("DIRECT_METHOD_EXECUTION",
                              "SHARED_HOLISTIC_INVOCATION",
                              "REUSED_NOT_INDEPENDENTLY_TIMED",
                              "SOURCE_METHOD_UNAVAILABLE", "NOT_INVOKED")
            or (raw == "REUSED_SCOPED_FROM_HOLISTIC" and
                timing not in ("SHARED_HOLISTIC_INVOCATION",
                               "REUSED_NOT_INDEPENDENTLY_TIMED"))
            or (status == "NOT_RUN" and elapsed is not None)
            or (status == "EXECUTED_SCOPED" and elapsed is None)
            or (status == "BLOCKED" and method.get("reason") is None)):
        raise ValueError("missing, forged or misleading activity measurement")
    row = {
        "id": method["method"], "state": status, "source_state": raw,
        "source": METHOD_FILES[method["method"]], "commit": commit,
        "source_digest": method.get("source_digest"),
        "reason": method.get("reason"),
        "elapsed_ms": elapsed,
        "timing_basis": timing,
        "proof_scope": "GIT_SOURCE_METHOD_NOT_PRODUCT_BEHAVIOR",
        "authority": "NONE",
    }
    validate_execution_row(row)
    return row


def _self_tests(repo: Path, *, enabled: bool, timeout: int) -> dict:
    record = {
        "id": "cora_unittest_suite", "state": "NOT_RUN",
        "reason": "EXPLICIT_OPT_IN_REQUIRED",
        "returncode": None, "elapsed_ms": None, "test_count": None,
        "log_sha256": None, "proof_scope": "TEST_EXECUTION_UNAUTHENTICATED",
        "authority": "NONE",
    }
    if not enabled:
        return record
    start = time.monotonic()
    # Never pass CI API/identity tokens to opt-in executing test code.
    protected = {"GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN",
                 "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "GITHUB_APP_TOKEN"}
    child_env = {k: v for k, v in os.environ.items()
                 if k not in protected and not k.startswith("ACTIONS_ID_TOKEN_REQUEST_")}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            cwd=repo, capture_output=True, timeout=timeout, check=False,
            env=child_env)
        out = (proc.stdout + b"\n" + proc.stderr)[-200_000:]
        code = proc.returncode
        reason = "EXIT_ZERO_NOT_INDEPENDENTLY_ATTESTED" if code == 0 else "TEST_EXIT_NONZERO"
    except subprocess.TimeoutExpired as exc:
        out = ((exc.stdout or b"") + b"\n" + (exc.stderr or b""))[-200_000:]
        code, reason = 124, "TEST_TIMEOUT"
    count_match = re.search(rb"(?m)^Ran ([0-9]{1,6}) tests?\b", out)
    count = int(count_match.group(1)) if count_match else None
    record.update({
        "test_count": count,
        "state": "RUN_REPORTED_UNATTESTED" if code == 0 else "FAIL",
        "reason": reason, "returncode": code,
        "elapsed_ms": max(0, int((time.monotonic()-start)*1000)),
        "log_sha256": hashlib.sha256(out).hexdigest(),
    })
    return record


def _metrics(rows: list[dict], test: dict) -> dict:
    totals = {k: sum(x["state"] == k for x in rows) for k in OUTCOMES}
    totals["NOT_RUN"] += int(test["state"] == "NOT_RUN")
    totals["FAIL"] += int(test["state"] == "FAIL")
    totals["RUN_REPORTED_UNATTESTED"] += int(test["state"] == "RUN_REPORTED_UNATTESTED")
    return dict(sorted(totals.items()))


def _plain_receipt(report: dict) -> dict:
    result = copy.deepcopy(report)
    for row in result["results"]:
        row.pop("elapsed_ms", None)
        row.pop("timing_basis", None)
    result.pop("timing", None)
    result.pop("run_digest", None)
    result["run_digest"] = domain_hash("CORA:process-run:1", result)
    return result


def run_one(repo: Path, revision: str = "HEAD", *,
            process: str = "full", max_commits: int = 64,
            focus: str | None = None, execute_self_tests: bool = False,
            test_timeout: int = 240, model_stress_cases: int = 0,
            change_base: str | None = None) -> dict:
    if (type(execute_self_tests) is not bool or not 30 <= test_timeout <= 900
            or type(model_stress_cases) is not int or model_stress_cases not in (0, 100000)):
        raise ValueError("bounded and explicitly authorized test operation required")
    repo = Path(repo).resolve(strict=True)
    commit = snapshot(repo, revision)["commit"]
    tree = git(repo, "rev-parse", commit + "^{tree}").decode("ascii").strip()
    cora = _is_cora(repo, commit)
    if execute_self_tests and (not cora or
                               git(repo, "rev-parse", "HEAD").decode().strip() != commit):
        raise ValueError("opt-in self-tests require exact CORA checkout HEAD")
    proc = run_suite(repo, commit, process=process,
                     max_commits=max_commits, focus=focus, measure=True,
                     change_base=change_base)
    activities = [_row(row, commit) for row in proc["results"]]
    validate_execution_rows(activities, expected_commit=commit)
    catalog = build_atlas(repo, unified_assurance(repo, commit)) if cora else None
    dod = _original_dod(repo, commit) if cora else {
        "goal": "BLOCKED_EXTERNAL", "authority": "NONE",
        "source_level": "NO_CORA_PRODUCT_DOD_ON_TARGET", "gates": {}, "checklist": []}
    test = _self_tests(repo, enabled=execute_self_tests, timeout=test_timeout)
    if model_stress_cases:
        # Fixed finite-model suite: safe, deterministic, no physical Git mutation.
        from .one_run_stress import stress_one_run
        model = stress_one_run(100000, seed=883)
    else:
        model = {"schema": "cora-one-run-model-not-run/1", "status": "NOT_RUN",
                 "cases": 0, "reason": "EXPLICIT_OPT_IN_REQUIRED",
                 "authority": "NONE", "external": "BLOCKED_EXTERNAL"}
    metrics = _metrics(activities, test)
    excluded = sorted(set(process_catalog()["excluded_unsafe_methods"]))
    receipt = {
        "schema": SCHEMA, "commit": commit, "tree": tree,
        "profile": "SAFE_SOURCE_PLUS_OPT_IN_TESTS" if execute_self_tests else "SAFE_SOURCE",
        "process": process, "history_limit": max_commits, "focus": focus,
        "source_process": proc,
        "activities": activities, "self_tests": test,
        "model_stress": model,
        "excluded_not_run": excluded,
        "catalog": catalog, "catalog_commands_declared": len(catalog["capabilities"]) if catalog else 0,
        "catalog_commands_executed_individually": 0,
        "catalog_scope": "CORA_ORIGINAL_GIT_DECLARATIONS_NOT_71_EXECUTIONS" if catalog
                         else "NOT_APPLICABLE_NONCORA_REPOSITORY",
        "metrics": metrics,
        "dod": dod,
        "source_status": ("DEBT_BLOCKED" if proc["status"] == "DEBT_BLOCKED"
                          or model["status"] == "REFUTED"
                         else "PASS_SCOPED_WITH_UNVERIFIED_GAPS"),
        "runtime_status": test["state"],
        "global_status": "BLOCKED_EXTERNAL",
        "authorization": "NONE", "release_authorized": False,
        "replay_scope": "SOURCE_REEXECUTABLE_TIMINGS_AND_RUNTIME_EXITS_NOT_REPLAY_ATTESTED",
    }
    receipt["receipt_digest"] = domain_hash("CORA:one-run:1", receipt)
    return receipt


def verify_one(repo: Path, receipt: dict, *, html_page: str | None = None) -> bool:
    if (not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA
            or receipt.get("authorization") != "NONE"
            or receipt.get("release_authorized") is not False
            or receipt.get("global_status") != "BLOCKED_EXTERNAL"
            or receipt.get("catalog_commands_executed_individually") != 0
            or receipt.get("replay_scope") !=
            "SOURCE_REEXECUTABLE_TIMINGS_AND_RUNTIME_EXITS_NOT_REPLAY_ATTESTED"):
        raise ValueError("one-run receipt identity/authority violation")
    sha = receipt.get("commit")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError("invalid original Git commit")
    repo = Path(repo).resolve(strict=True)
    if receipt.get("tree") != git(repo, "rev-parse", sha + "^{tree}").decode().strip():
        raise ValueError("wrong Git tree")
    plain = _plain_receipt(receipt["source_process"])
    if not verify_suite(repo, plain):
        raise ValueError("original source process replay failed")
    expected_activities = [_row(x, sha) for x in receipt["source_process"]["results"]]
    validate_execution_rows(receipt["activities"], expected_commit=sha)
    if expected_activities != receipt["activities"]:
        raise ValueError("execution outcomes or lineage have been rewritten")
    if (len({x["id"] for x in expected_activities}) != len(expected_activities)
            or receipt["source_process"]["commit"] != sha
            or receipt["process"] != plain["process"]
            or receipt["history_limit"] != plain["history_limit"]
            or receipt["focus"] != plain["focus"]):
        raise ValueError("execution identity mismatch")
    test = receipt.get("self_tests")
    if not isinstance(test, dict) or test.get("id") != "cora_unittest_suite":
        raise ValueError("missing optional-test observation")
    if (test.get("authority") != "NONE" or
            test.get("proof_scope") != "TEST_EXECUTION_UNAUTHENTICATED" or
            test.get("state") not in ("NOT_RUN", "FAIL", "RUN_REPORTED_UNATTESTED")):
        raise ValueError("forged test execution authority")
    if test["state"] == "NOT_RUN":
        if (test.get("reason") != "EXPLICIT_OPT_IN_REQUIRED" or
                any(test.get(k) is not None for k in (
                    "returncode", "elapsed_ms", "log_sha256", "test_count"))):
            raise ValueError("not-run test masked as executed")
    else:
        if (type(test.get("returncode")) is not int or
                type(test.get("elapsed_ms")) is not int or test["elapsed_ms"] < 0
                or not isinstance(test.get("log_sha256"), str)
                or len(test["log_sha256"]) != 64
                or (test["state"] == "FAIL") == (test["returncode"] == 0)
                or (test.get("test_count") is not None and
                    (type(test["test_count"]) is not int or
                     not 0 <= test["test_count"] <= 100000))):
            raise ValueError("invalid optional-test exit claim")
    if receipt.get("profile") != (
            "SAFE_SOURCE" if test["state"] == "NOT_RUN" else "SAFE_SOURCE_PLUS_OPT_IN_TESTS"):
        raise ValueError("profile and test scope inconsistent")
    if receipt.get("excluded_not_run") != sorted(process_catalog()["excluded_unsafe_methods"]):
        raise ValueError("not-run dangerous operations suppressed")
    if receipt.get("metrics") != _metrics(receipt["activities"], test):
        raise ValueError("aggregated metrics masked errors or skips")
    model = receipt.get("model_stress")
    if model is None:
        raise ValueError("model benchmark observation missing")
    if model.get("status") == "NOT_RUN":
        if model != {"schema": "cora-one-run-model-not-run/1", "status": "NOT_RUN",
                     "cases": 0, "reason": "EXPLICIT_OPT_IN_REQUIRED",
                     "authority": "NONE", "external": "BLOCKED_EXTERNAL"}:
            raise ValueError("not-run model benchmark forged")
    else:
        from .one_run_stress import stress_one_run
        if model != stress_one_run(100000, seed=883):
            raise ValueError("preseeded model benchmark is not reproducible")
    cora = _is_cora(repo, sha)
    expected_catalog = build_atlas(repo, unified_assurance(repo, sha)) if cora else None
    expected_dod = _original_dod(repo, sha) if cora else {
        "goal": "BLOCKED_EXTERNAL", "authority": "NONE",
        "source_level": "NO_CORA_PRODUCT_DOD_ON_TARGET", "gates": {}, "checklist": []}
    if (receipt.get("catalog") != expected_catalog or
            receipt.get("catalog_commands_declared") != (
                len(expected_catalog["capabilities"]) if expected_catalog else 0) or
            receipt.get("catalog_scope") != (
                "CORA_ORIGINAL_GIT_DECLARATIONS_NOT_71_EXECUTIONS" if cora else
                "NOT_APPLICABLE_NONCORA_REPOSITORY") or
            receipt.get("dod") != expected_dod or
            receipt.get("source_status") != (
                "DEBT_BLOCKED" if plain["status"] == "DEBT_BLOCKED"
                  or model["status"] == "REFUTED"
                else "PASS_SCOPED_WITH_UNVERIFIED_GAPS") or
            receipt.get("runtime_status") != test["state"]):
        raise ValueError("one-run source catalog or DoD drift")
    digest = receipt.get("receipt_digest")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_digest"}
    if digest != domain_hash("CORA:one-run:1", unsigned):
        raise ValueError("one-run receipt content tampered")
    if html_page is not None and html_page != render_one_html(receipt):
        raise ValueError("one-run HTML differs from verified receipt")
    return True


def render_one_html(receipt: dict) -> str:
    """Readable result dashboard; reuses PR31 atlas for the original 71 commands."""
    if receipt.get("schema") != SCHEMA or receipt.get("authorization") != "NONE":
        raise ValueError("unsafe one-run view")
    safe = lambda x: html.escape(str(x), quote=True)
    status = receipt["metrics"]
    metric_html = "".join(
        '<div class="metric"><b>' + str(status[key]) +
        '</b><span>' + safe(key.replace("_", " ")) + '</span></div>'
        for key in ("EXECUTED_SCOPED", "REUSED_SCOPED", "FAIL", "BLOCKED", "NOT_RUN", "RUN_REPORTED_UNATTESTED"))
    rows = []
    for item in receipt["activities"]:
        elapsed = "non misurato (riuso)" if item["elapsed_ms"] is None else str(item["elapsed_ms"]) + " ms"
        rows.append(
            '<details class="panel searchable" data-search="' +
            safe((item["id"]+" "+item["state"]+" "+str(item["reason"])).lower())+'"><summary>' +
            safe(item["id"]) + ' · <span class="state">' + safe(item["state"]) +
            '</span></summary><p>Tempo: ' + safe(elapsed) +
            ' · Fonte: <code>' + safe(item["source"]) +
            '</code></p><p class="small muted">Digest sorgente: ' + safe(item["source_digest"]) +
            ' · Prova: ' + safe(item["proof_scope"]) + ' · Motivo: ' +
            safe(item["reason"]) + '</p></details>')
    test = receipt["self_tests"]
    test_row = ('<div class="panel"><h3>Suite unittest locale (opt-in)</h3><p>Stato: <strong>' +
                safe(test["state"]) + '</strong> · ' + safe(test["reason"]) +
                '</p><p class="small">Exit code dichiarato: ' + safe(test["returncode"]) +
                ' · Durata: ' + safe(test["elapsed_ms"]) + ' ms · Test riportati: ' +
                safe(test["test_count"]) + ' · Log SHA-256: ' +
                safe(test["log_sha256"]) + '</p><p class="muted small">Un exit zero non certifica '
                'test di terzi né una release.</p></div>')
    excluded = "".join('<li><code>'+safe(x)+'</code> — NOT_RUN, azione non autorizzata</li>'
                       for x in receipt["excluded_not_run"])
    model = receipt["model_stress"]
    model_html = ('<div class="panel"><h3>Benchmark semantico pre-seeded (opt-in)</h3>'
                  '<p>Stato: <strong>' + safe(model["status"]) + '</strong> · casi: ' +
                  safe(model["cases"]) + '</p>' +
                  ('<p>Controlli positivi: ' + safe(model["positive_controls"]) +
                   ' · scenari negativi: ' + safe(model["negative_scenarios"]) +
                   ' · divergenze: ' + safe(model["oracle_disagreements"]) +
                   ' · promozioni indebite: ' + safe(model["unauthorized_promotions"]) +
                   '</p>' if model["status"] != "NOT_RUN" else
                   '<p class="small muted">Non eseguito senza --model-stress-cases 100000.</p>') +
                  '<p class="small muted">Modello finito di ricevute; zero mutazioni Git fisiche; '
                  'non certifica comportamenti runtime.</p></div>')
    gates = receipt["dod"]["gates"]
    # Same canonical order before and after json.dumps(sort_keys=True) replay.
    gate_order = ("G_EXECUTION", "G_PRESENTATION", "G_SOURCE_REPLAY",
                  "G_ONE_RUN_SOURCE", "G_GOVERNED_ONE_RUN", "G_ONE_RUN_PRODUCT")
    gate_html = "".join('<div class="gate"><strong>'+safe(name)+'</strong><span class="state">'+
                        safe(gates[name])+'</span></div>' for name in gate_order if name in gates)
    check_html = "".join('<li><strong>'+safe(c["id"])+'</strong> · '+safe(c["criterion"])+'</li>'
                         for c in receipt["dod"]["checklist"])
    panel = (f'<section id="run-execution"><h2>00 · Esiti realmente osservati</h2>'
             f'<p>Commit <code>{safe(receipt["commit"])}</code> · tree '
             f'<code>{safe(receipt["tree"])}</code> · processo <strong>{safe(receipt["process"])}</strong>. '
             'I risultati sorgente eseguiti, riutilizzati e non eseguiti non sono equivalenti.</p>'
             f'<div class="metrics" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">{metric_html}</div>'
             '<h3>Attività sorgente</h3>'+''.join(rows)+test_row+model_html+
             '<h3>Attività escluse / non eseguite</h3><div class="panel"><ul>'+excluded+
             '</ul></div><h3>Reticolo DoD e checklist</h3><div class="panel">'+gate_html+
             '<p class="small">Il reticolo sorgente è un modello, non prova '
             'di accettazione esterna.</p><ul>'+check_html+'</ul></div>'
             '<p class="note">71 comandi eventualmente elencati sotto = catalogo, '
             'non 71 invocazioni. Nessuna approvazione, release o esecuzione '
             'dei test target implicita.</p></section>')
    atlas = receipt["catalog"]
    if atlas:
        page = render_html(atlas)
        page = page.replace(
            '<nav><a href="#overview">Panoramica</a>',
            '<nav><a href="#run-execution">Esiti del run</a><a href="#overview">Panoramica</a>', 1)
        page = page.replace('<section id="maturity">', panel+'<section id="maturity">', 1)
        page = page.replace("CORA ATLAS | SOURCE-BOUNDED",
                            HTML_MARKER + " / CORA ATLAS | SOURCE-BOUNDED")
        return page.replace(
            "Non vengono eseguiti test target, Docker o provider AI per creare questa pagina.",
            "I test opzionali eseguiti sono visibili nella sezione 00; Docker e provider AI non sono invocati automaticamente.")
    style = """<style>
:root{--ink:#0b1f3a;--paper:#f4eee5;--text:#243247;--line:#e0d7c9}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--text);
font:15px/1.6 system-ui,sans-serif}main{max-width:1150px;margin:auto;padding:35px}
header{background:var(--ink);color:white;border-radius:16px;padding:40px}
.panel,.metric{background:white;border:1px solid var(--line);border-radius:12px;padding:20px;margin:10px 0}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.metric b{display:block;font-size:27px}summary{cursor:pointer;font-weight:700}
.state,.small{font-size:12px}.muted{color:#586a7b}code{overflow-wrap:anywhere}
.note{border-left:3px solid #c8892b;padding:14px;background:white}
@media(max-width:600px){main{padding:16px}header{padding:22px}}
</style>"""
    return ('<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
            'style-src &#39;unsafe-inline&#39;; connect-src &#39;none&#39;; form-action &#39;none&#39;">'
            '<title>CORA · One Run</title>' + style +
            '</head><body><main><header><h1>CORA · One Run</h1><p>' +
            safe(HTML_MARKER) + ' · repository generico, senza catalogo CORA</p></header>' +
            panel + '<footer>Source-bound. Autorità: NONE. Codice target non eseguito senza opt-in.</footer>'
            '</main></body></html>')
