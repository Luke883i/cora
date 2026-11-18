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


def execute(checkout: Path, argv: list[str], *, workdir: Path | None = None) -> dict:
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
        [sys.executable, "-m", "cora.cli", *argv], cwd=workdir or checkout,
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
                case: execute(checkout, arguments(case, repo, base_sha, fixture),
                              workdir=repo)
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
        "runner_environment": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "working_directory": str(repo),
            "pythonhashseed": "0",
            "locale": "C.UTF-8",
            "timezone": "UTC",
            "columns": "100",
            "user_site": "DISABLED",
        },
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

# P3: native counterfactual adjudication reuses this original operational owner.
# These functions classify caller-observed native effects; they NEVER launch
# arbitrary foreign-target code or authenticate the evidence producer.
def native_counterfactual(repo: Path, base: str, head: str,
                          tests: list[dict], baseline: dict,
                          candidate: dict) -> dict:
    """Classify a closed native test universe with exact Git test identity.

    Observation = {exit_code:int, stdout:bytes, stderr:bytes,
                   effects:{relative_path:bytes}}. An absent observation or
    missing effect is UNKNOWN, not a false PASS. Only the operator may execute
    target code in separately trusted isolation.
    """
    from cora.evidence import domain_hash, valid_path
    if (not isinstance(tests, list) or not 1 <= len(tests) <= 256 or
            any(not isinstance(t, dict) or set(t) != {'id', 'path'} or
                not isinstance(t['id'], str) or not t['id'] or
                not isinstance(t['path'], str) or not valid_path(t['path'])
                for t in tests) or
            len({t['id'] for t in tests}) != len(tests) or
            not isinstance(baseline, dict) or not isinstance(candidate, dict) or
            set(baseline) - {t['id'] for t in tests} or
            set(candidate) - {t['id'] for t in tests}):
        raise ValueError('P3 native test denominator invalid')
    repo = Path(repo).resolve(strict=True)
    b, h = revision(repo, base), revision(repo, head)
    if b == h:
        raise ValueError('P3 distinct Git revisions required')
    ancestor = subprocess.run(['git', '-C', str(repo), 'merge-base',
                               '--is-ancestor', b, h],
                              capture_output=True, timeout=30, check=False)
    if ancestor.returncode:
        raise ValueError('P3 source revisions must have original ancestry')
    def original_oid(sha, path):
        row = git(repo, 'ls-tree', '-z', sha, '--', path)
        if (row.count(b'\0') != 1 or not row.endswith(b'\0') or
                b'\t' not in row or
                row.split(b'\t', 1)[1][:-1].decode('utf-8') != path or
                not row.startswith((b'100644 blob ', b'100755 blob '))):
            return None
        return row.split(b'\t', 1)[0].decode('ascii').split()[-1]
    def valid_observation(obs):
        return (isinstance(obs, dict) and set(obs) ==
                {'exit_code', 'stdout', 'stderr', 'effects'} and
                type(obs['exit_code']) is int and
                isinstance(obs['stdout'], bytes) and
                isinstance(obs['stderr'], bytes) and
                isinstance(obs['effects'], dict) and
                bool(obs['effects']) and len(obs['effects']) <= 32 and
                all(isinstance(p, str) and valid_path(p) and
                    isinstance(v, bytes) and len(v) <= 1024 * 1024
                    for p, v in obs['effects'].items()) and
                len(obs['stdout']) <= MAX_OUTPUT and
                len(obs['stderr']) <= MAX_OUTPUT)
    def fingerprint(obs):
        if not valid_observation(obs):
            return None
        return {
            'exit_code': obs['exit_code'],
            'stdout_sha256': hashlib.sha256(obs['stdout']).hexdigest(),
            'stderr_sha256': hashlib.sha256(obs['stderr']).hexdigest(),
            'effect_sha256': {p: hashlib.sha256(data).hexdigest()
                              for p, data in sorted(obs['effects'].items())},
        }
    rows = []
    for item in tests:
        key, path = item['id'], item['path']
        left_oid, right_oid = original_oid(b, path), original_oid(h, path)
        left, right = fingerprint(baseline.get(key)), fingerprint(candidate.get(key))
        if left_oid is None or right_oid is None:
            status = 'UNKNOWN_TEST_NOT_IN_ORIGINAL_GIT'
        elif left_oid != right_oid:
            status = 'UNKNOWN_TEST_IDENTITY_DRIFT'
        elif left is None or right is None:
            status = 'UNKNOWN_NATIVE_OBSERVATION_OR_EFFECT_MISSING'
        elif left['exit_code'] != 0:
            status = 'UNKNOWN_BASELINE_ORACLE_NOT_ACCEPTED'
        elif left != right:
            status = 'FAIL_OBSERVED_NATIVE_COUNTERFACTUAL'
        else:
            status = 'PASS_SCOPED_SAME_OBSERVED_NATIVE_EFFECTS'
        rows.append({'id': key, 'path': path, 'base_oracle_oid': left_oid,
                     'head_oracle_oid': right_oid, 'baseline': left,
                     'candidate': right, 'status': status})
    bad = [row['id'] for row in rows if row['status'].startswith('FAIL_')]
    unknown = [row['id'] for row in rows if row['status'].startswith('UNKNOWN_')]
    result = {'schema': 'cora-native-counterfactual/1', 'base': b, 'head': h,
              'tests': rows, 'denominator': len(tests), 'failed': bad,
              'unknown': unknown,
              'status': ('FAIL_OBSERVED' if bad else
                         'UNKNOWN_INCOMPLETE' if unknown else
                         'PASS_SCOPED_FINITE_NATIVE'),
              'execution': 'OPERATOR_SUPPLIED_ORIGINAL_GIT_NATIVE_OBSERVATIONS',
              'producer_authenticated': False,
              'external_and_runtime_closure': 'BLOCKED_EXTERNAL',
              'release_authorization': 'NONE'}
    result['digest'] = domain_hash('CORA:native-counterfactual:1', result)
    return result



def verify_native_counterfactual(repo: Path, report: dict, tests: list[dict],
                                 baseline: dict, candidate: dict) -> bool:
    """Reopen original Git oracle blobs and recompare caller-supplied evidence.

    A changed caller-controlled observation can be rehashed; this replay
    detects report-only forgery, NOT producer collusion or missing effects.
    """
    from cora.evidence import domain_hash
    if not isinstance(report, dict) or report.get('schema') != 'cora-native-counterfactual/1':
        raise ValueError('invalid P3 counterfactual receipt')
    if report.get('digest') != domain_hash('CORA:native-counterfactual:1',
                                            {k: v for k, v in report.items() if k != 'digest'}):
        raise ValueError('P3 counterfactual digest mismatch')
    actual = native_counterfactual(repo, report['base'], report['head'],
                                   tests, baseline, candidate)
    if actual != report:
        raise ValueError('P3 counterfactual Git and native evidence replay mismatch')
    return True


def minimize_native_failure(changes: list[str], native_probe, *,
                            max_probes: int = 128) -> dict:
    """Deterministic 1-minimal source-change witness, never semantic deletion proof.

    The caller must explicitly supply an isolated *native* oracle that returns
    FAIL, PASS, or UNKNOWN for a selected subset of physical changes. Probe
    twice and refuse to shrink across nondeterministic/unknown outcomes.
    """
    from cora.evidence import domain_hash
    if (not isinstance(changes, list) or not 1 <= len(changes) <= 128 or
            any(not isinstance(x, str) or not x for x in changes) or
            len(set(changes)) != len(changes) or
            type(max_probes) is not int or not 2 <= max_probes <= 512 or
            not callable(native_probe)):
        raise ValueError('P3 ddmin changes, oracle or budget invalid')
    trials = []
    def check(subset):
        if 2 * len(trials) + 2 > max_probes:
            return 'UNKNOWN_BUDGET'
        a, b = native_probe(tuple(subset)), native_probe(tuple(subset))
        if a not in ('FAIL', 'PASS', 'UNKNOWN') or b not in ('FAIL', 'PASS', 'UNKNOWN'):
            raise ValueError('P3 native oracle returned unrecognized outcome')
        state = a if a == b else 'UNKNOWN_FLAKY'
        trials.append({'subset': list(subset), 'first': a, 'second': b,
                       'status': state})
        return state
    current = list(changes)
    initial = check(current)
    if initial != 'FAIL':
        state = 'UNKNOWN_OR_NOT_REPRODUCED'
    else:
        granularity = 2
        while len(current) > 1:
            width = max(1, (len(current) + granularity - 1) // granularity)
            parts = [current[i:i + width] for i in range(0, len(current), width)]
            reduced = False
            for group in parts:
                complement = [x for x in current if x not in group]
                if complement and check(complement) == 'FAIL':
                    current, reduced = complement, True
                    granularity = max(2, granularity - 1)
                    break
            if reduced:
                continue
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
        # Final 1-minimality check is mandatory; unknown/budget never certifies it.
        checked = True
        for idx in range(len(current)):
            subset = current[:idx] + current[idx + 1:]
            verdict = check(subset)
            if verdict != 'PASS':
                checked = False
                break
        state = ('FAIL_1_MINIMAL_NATIVE_WITNESS' if checked and
                 all(t['status'] in ('PASS', 'FAIL') for t in trials) else
                 'UNKNOWN_MINIMALITY')
    result = {'schema': 'cora-native-ddmin/1', 'source_changes': changes,
              'minimized': current, 'trials': trials, 'status': state,
              'scope': 'OPERATOR_SUPPLIED_NATIVE_PROBE_NOT_CAUSAL_UNIVERSALITY',
              'unknown_trials': sum(x['status'] == 'UNKNOWN_FLAKY' or
                                    x['status'] == 'UNKNOWN' for x in trials),
              'execution_authority': 'NONE', 'safe_deletion': False}
    result['digest'] = domain_hash('CORA:native-ddmin:1', result)
    return result


def native_counterfactual_cut(native: dict, minimized: dict | None = None) -> dict:
    """P3 four-gate AND cut: typed model evidence, NEVER product admission.

    The cut is structural: caller-provided receipts are not independently
    authenticated. The external reviewer, provider and rollback never PASS.
    """
    from cora.evidence import domain_hash
    from cora.reticulum import assess_cut, MODEL, BLOCKED, EXTERNAL, REFUTED
    if (not isinstance(native, dict) or native.get('schema') != 'cora-native-counterfactual/1' or
            native.get('digest') != domain_hash('CORA:native-counterfactual:1',
                {k:v for k,v in native.items() if k != 'digest'})):
        raise ValueError('P3 invalid native receipt for AND cut')
    if minimized is not None and (not isinstance(minimized, dict) or
            minimized.get('schema') != 'cora-native-ddmin/1' or
            minimized.get('digest') != domain_hash('CORA:native-ddmin:1',
                {k:v for k,v in minimized.items() if k != 'digest'})):
        raise ValueError('P3 invalid ddmin receipt for AND cut')
    gates = {
        'P3_G1': ('L1_GIT', 'L2_TEST_IDENTITY', 'L3_DENOMINATOR'),
        'P3_G2': ('L4_NATIVE_OBSERVATIONS', 'L5_PERSISTED_EFFECTS', 'L6_NEGATIVE_UNKNOWN'),
        'P3_G3': ('L7_PHYSICAL_WITNESS', 'L8_REPEATABILITY', 'L9_ONE_MINIMAL'),
        'P3_G4': ('L10_INDEPENDENT_REPLAY', 'L11_AUTHENTICATED_REVIEW', 'L12_ROLLBACK'),
    }
    nodes = [{'id':'P3_G0','scope':'EXTERNAL','depends_on':list(gates)}]
    for gate, leaves in gates.items():
        nodes.append({'id':gate,'scope':'EXTERNAL' if gate == 'P3_G4' else 'MODEL',
                      'depends_on':list(leaves)})
        nodes.extend({'id':leaf,'scope': ('EXTERNAL' if leaf in
                       ('L11_AUTHENTICATED_REVIEW','L12_ROLLBACK') else 'MODEL'),
                      'depends_on':[]} for leaf in leaves)
    rows = native.get('tests', [])
    good_ids = bool(rows) and native.get('denominator') == len(rows)
    test_stable = good_ids and all(x.get('base_oracle_oid') is not None and
                                   x.get('base_oracle_oid') == x.get('head_oracle_oid')
                                   for x in rows)
    statuses = [x.get('status','') for x in rows]
    native_state = (REFUTED if any(x.startswith('FAIL_') for x in statuses) else
                    BLOCKED if any(x.startswith('UNKNOWN_') for x in statuses) or not statuses
                    else MODEL)
    obs = {'L1_GIT': MODEL, 'L2_TEST_IDENTITY': MODEL if test_stable else BLOCKED,
           'L3_DENOMINATOR': MODEL if good_ids else BLOCKED,
           'L4_NATIVE_OBSERVATIONS': native_state,
           'L5_PERSISTED_EFFECTS': native_state,
           'L6_NEGATIVE_UNKNOWN': (MODEL if any(
               x.get('id','').startswith('negative:') and
               not x.get('status','').startswith('UNKNOWN_') for x in rows) else BLOCKED),
           'L7_PHYSICAL_WITNESS': BLOCKED,  # caller labels are not Git physical proof
           'L8_REPEATABILITY': (MODEL if minimized and minimized.get('trials') and
               all(x.get('first') == x.get('second') and x.get('status') in ('PASS','FAIL')
                   for x in minimized['trials']) else BLOCKED),
           'L9_ONE_MINIMAL': MODEL if minimized and minimized.get('status') ==
               'FAIL_1_MINIMAL_NATIVE_WITNESS' else BLOCKED,
           'L10_INDEPENDENT_REPLAY': BLOCKED}
    assessment = assess_cut(nodes, 'P3_G0', obs)
    result = {'schema': 'cora-p3-native-cut/1', 'cut': assessment,
              'source_receipts': {'native': native['digest'],
                                  'ddmin': minimized['digest'] if minimized else None},
              'physical_git_linkage': 'NOT_AUTHENTICATED_FROM_LABELS',
              'external_evidence': 'BLOCKED_EXTERNAL', 'product_go': False}
    result['digest'] = domain_hash('CORA:p3-native-cut:1', result)
    return result

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
