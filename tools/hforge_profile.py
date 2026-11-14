"""H-FORGE evidence projection for CORA; a profile, not a second runner.

A claim about original Git and a caller-controlled receipt remains untrusted
until the original observer is re-executed. Never authorizes target mutation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

SCHEMA = "cora-hforge-profile-result/1"
OP_SCHEMA = "cora-operational-observation/1"
REPLAY_SCHEMA = "cora-operational-replay/1"
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
NATIVE = frozenset(("version", "process-list", "snapshot-pinned", "graph-pinned",
                    "dod-plan-pinned", "stress-128"))


def _git(repo: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       timeout=60, check=False)
    if p.returncode != 0:
        raise ValueError("original Git evidence unavailable: " + " ".join(args[:2]))
    return p.stdout


def _commit(repo: Path, name: str) -> str:
    if not isinstance(name, str) or not SHA.fullmatch(name):
        raise ValueError("full commit SHA required")
    actual = _git(repo, "rev-parse", "--verify", name + "^{commit}").decode().strip()
    if actual != name:
        raise ValueError("Git revision mismatch")
    return actual


def tree_metrics(repo: Path, revision: str) -> dict:
    """Original Git tracked tree only; no filesystem heuristics, no link traversal."""
    sha = _commit(repo, revision)
    raw = _git(repo, "ls-tree", "-r", "-l", "-z", sha)
    rows = raw.split(b"\0")
    if rows[-1] != b"":
        raise ValueError("truncated Git tree")
    blobs = links = symlinks = size = 0
    digest = hashlib.sha256()
    for row in rows[:-1]:
        try:
            meta, path = row.split(b"\t", 1)
            mode, kind, oid, n = meta.split()
        except ValueError as exc:
            raise ValueError("malformed Git tree entry") from exc
        if b"\n" in path or b"\0" in path or not path:
            raise ValueError("unsafe or ambiguous Git tree path")
        if kind == b"commit" and mode == b"160000":
            links += 1
        elif kind == b"blob" and mode in (b"100644", b"100755", b"120000"):
            if not n.isdigit():
                raise ValueError("Git blob size unavailable")
            blobs += 1
            size += int(n)
            if mode == b"120000":
                symlinks += 1
        else:
            raise ValueError("unhandled tracked Git object")
        digest.update(row + b"\0")
    return {"commit": sha, "tracked_files": blobs, "tracked_bytes": size,
            "symlinks": symlinks, "gitlinks_unresolved": links,
            "tree_entries_sha256": digest.hexdigest(),
            "measurement": "ORIGINAL_GIT_TREE_NO_WORKTREE_INFERENCE"}


def compare_trees(repo: Path, base: str, head: str) -> dict:
    if base == head:
        raise ValueError("BASE and HEAD must be different commits")
    b, h = tree_metrics(repo, base), tree_metrics(repo, head)
    p = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head],
                       capture_output=True, timeout=30, check=False)
    if p.returncode != 0:
        raise ValueError("BASE must be ancestor of HEAD")
    return {"base": b, "head": h,
            "delta_files": h["tracked_files"] - b["tracked_files"],
            "delta_bytes": h["tracked_bytes"] - b["tracked_bytes"],
            "unresolved_gitlinks": b["gitlinks_unresolved"] + h["gitlinks_unresolved"],
            "scope": "ALL_TRACKED_GIT_BLOBS", "rename_does_not_imply_contraction": True}


def _canonical_digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def operational_claim(report: object, base: str, head: str) -> dict:
    """Syntactic binding only: NEVER treat untrusted report as an executed test."""
    if not isinstance(report, dict) or report.get("schema") != OP_SCHEMA:
        raise ValueError("not a PR70 operational report")
    if report.get("base") != base or report.get("head") != head:
        raise ValueError("operational receipt revision mismatch")
    if (report.get("denominator") != 77 or report.get("observed") != 77 or
            type(report.get("denominator")) is not int or
            type(report.get("observed")) is not int):
        raise ValueError("PR70 operational denominator must be complete")
    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != 77:
        raise ValueError("PR70 rows incomplete")
    case_names = [r.get("case") for r in rows if isinstance(r, dict)]
    if len(case_names) != 77 or len(set(case_names)) != 77 or any(
            not isinstance(x, str) or not x for x in case_names):
        raise ValueError("missing/duplicate native observations")
    help_cases = [x for x in case_names if x.startswith("help:")]
    if len(help_cases) != 71 or set(case_names) - set(help_cases) != NATIVE:
        raise ValueError("operational case universe incomplete")
    for row in rows:
        if row.get("status") not in ("PASS", "REFUTED"):
            raise ValueError("invalid PR70 row status")
        for side in ("baseline", "candidate"):
            o = row.get(side)
            if not isinstance(o, dict) or set(o) != {
                    "exit_code", "stdout_sha256", "stdout_bytes",
                    "stderr_sha256", "stderr_bytes"}:
                raise ValueError("invalid PR70 observation shape")
            if (type(o["exit_code"]) is not int or
                    any(type(o[k]) is not int or o[k] < 0
                        for k in ("stdout_bytes", "stderr_bytes")) or
                    any(not isinstance(o[k], str) or
                        not re.fullmatch(r"[0-9a-f]{64}", o[k])
                        for k in ("stdout_sha256", "stderr_sha256"))):
                raise ValueError("invalid observed byte hashes")
        left, right = row["baseline"], row["candidate"]
        exact_equal = all(left[k] == right[k] for k in (
            "exit_code", "stdout_sha256", "stdout_bytes",
            "stderr_sha256", "stderr_bytes"))
        empty_hash = hashlib.sha256(b"").hexdigest()
        successful = (left["exit_code"] == right["exit_code"] == 0
                      and left["stdout_bytes"] > 0 and right["stdout_bytes"] > 0
                      and left["stderr_bytes"] == right["stderr_bytes"] == 0
                      and left["stderr_sha256"] == right["stderr_sha256"] == empty_hash)
        expected_status = "PASS" if exact_equal and successful else "REFUTED"
        if row["status"] != expected_status:
            raise ValueError("claimed per-case PASS does not match recorded byte observations")
    if report.get("authority") not in (None, "NONE"):
        raise ValueError("claim cannot authorize action")
    if report.get("authorization") != "NONE" or report.get("product_global_status") != "BLOCKED_EXTERNAL":
        raise ValueError("nonpromoting source contract violated")
    if (report.get("passed") != sum(row["status"] == "PASS" for row in rows) or
            report.get("failed") != [row["case"] for row in rows if row["status"] == "REFUTED"]):
        raise ValueError("reported summary disagrees with observed rows")
    if report.get("status") != ("PASS_EXHAUSTIVE_FINITE_OBSERVATIONS"
                                 if report["passed"] == 77 else "REFUTED_FINITE_OBSERVATIONS"):
        raise ValueError("false global PASS/FAIL in PR70 source claim")
    return {"schema": report["schema"], "base": base, "head": head,
            "receipt_digest": _canonical_digest(report), "denominator": 77,
            "scoped_status": report["status"], "replay": "NOT_EXECUTED_BY_ADAPTER"}


def assess(repo: Path, report: dict | None = None, *, base: str, head: str,
           contraction_claim: bool = False, replay_native: bool = False) -> dict:
    """Project existing evidence. Real native replay delegates to PR70 with consent."""
    repo = Path(repo)
    delta = compare_trees(repo, base, head)
    gates = {key: "HOLD" for key in ("P0", "P1", "P2", "P3", "P4", "P5")}
    gates["P0"] = "PASS_ORIGINAL_GIT_BASE_HEAD_PINNED"
    gates["P3"] = "PASS_ORIGINAL_GIT_MEASUREMENT" if not delta["unresolved_gitlinks"] else "HOLD_GITLINKS"
    claim = operational_claim(report, base, head) if report is not None else None
    if claim is not None:
        gates["P1"] = "PASS_RECEIPT_SHAPE_NOT_RUNTIME_PROOF"
    if contraction_claim:
        gates["P3"] = ("PASS_MEASURED_CONTRACTION" if gates["P3"].startswith("PASS_")
                       and delta["delta_files"] < 0 and delta["delta_bytes"] < 0
                       else "REFUTED_OR_UNVERIFIED_CONTRACTION")
    if replay_native:
        if report is None:
            raise ValueError("cannot replay absent operational receipt")
        try:
            from tools import verify_operational_equivalence as upstream
        except ImportError as exc:
            raise ValueError("PR70 native verifier not installed in original checkout") from exc
        if upstream.verify(repo, report, execute_pinned_native=True) is not True:
            raise ValueError("original native replay did not verify")
        gates["P2"] = "PASS_REPLAYED_77_SCOPED" if claim["scoped_status"] == (
            "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS") else "REFUTED_OPERATIONAL_EQUIVALENCE"
    if gates["P2"] == "PASS_REPLAYED_77_SCOPED" and gates["P3"].startswith("PASS_"):
        gates["P4"] = "HOLD_ONE_RUN_INTEGRATION_NOT_REPLAYED"
    obligations = ["SIDE_EFFECTS_NOT_IN_PR70", "DYNAMIC_CONSUMERS_UNOBSERVED",
                   "EXTERNAL_CONSUMERS_UNOBSERVED", "PRODUCT_ERROR_PATHS_UNBOUNDED",
                   "HOST_AND_REVIEWER_AUTHORITY_NOT_ATTESTED", "ONERUN_COMPATIBILITY_NOT_EXECUTED"]
    result = {"schema": SCHEMA, "base": base, "head": head,
              "operational_claim": claim, "git_structure": delta,
              "gates": gates, "open_obligations": obligations,
              "status": "DEBT_BLOCKED_GLOBAL", "global_product_equivalence": "NOT_ATTESTED",
              "authorization": "NONE", "release_authorized": False,
              "proof_level": "SOURCE_MEASURED_OPERATIONAL_REPLAY_IF_CONSENTED_ONLY"}
    result["digest"] = hashlib.sha256(
        b"CORA:HFORGE:PROFILE:1\0" + _canonical_digest(result).encode()).hexdigest()
    return result


def verify_assessment(repo: Path, result: dict, report: dict | None = None, *,
                      contraction_claim: bool = False, replay_native: bool = False) -> bool:
    """Recompute against original Git. Never replay a claimed result as its own oracle."""
    if not isinstance(result, dict) or result.get("schema") != SCHEMA:
        raise ValueError("invalid H-FORGE report")
    expected = assess(repo, report, base=result.get("base"), head=result.get("head"),
                      contraction_claim=contraction_claim, replay_native=replay_native)
    if expected != result:
        raise ValueError("H-FORGE report does not replay original Git and source claim")
    return True


def one_run_reference(repo: Path, profile_result: dict, integrated_receipt: dict,
                      operational_report: dict | None = None, *,
                      contraction_claim: bool = False) -> dict:
    """Sidecar reference ONLY; does not alter or re-certify CORA One-Run."""
    if not isinstance(integrated_receipt, dict) or integrated_receipt.get("schema") != (
            "cora-integrated-one-run/2"):
        raise ValueError("not the canonical CORA integrated One-Run")
    if (integrated_receipt.get("authority") != "NONE" or
            integrated_receipt.get("authorization") != "NONE" or
            integrated_receipt.get("release_authorized") is not False or
            integrated_receipt.get("source_status") != "DEBT_BLOCKED" or
            integrated_receipt.get("product_status") != "BLOCKED_EXTERNAL"):
        raise ValueError("integrated One-Run cannot promote authority or product")
    sha = profile_result.get("head")
    if integrated_receipt.get("commit") != sha:
        raise ValueError("One-Run and H-FORGE are bound to different revisions")
    if not verify_assessment(repo, profile_result, operational_report,
                             contraction_claim=contraction_claim):
        raise ValueError("H-FORGE source not verified")
    expected_tree = _git(Path(repo), "rev-parse", sha + "^{tree}").decode().strip()
    if integrated_receipt.get("tree") != expected_tree:
        raise ValueError("One-Run tree does not match original Git")
    return {"schema": "cora-hforge-one-run-reference/1", "commit": sha,
            "tree": expected_tree, "hforge_digest": profile_result["digest"],
            "integrated_unverified_digest": _canonical_digest(integrated_receipt),
            "status": "SIDECAR_REFERENCE_NOT_NATIVE_ONERUN_VERIFICATION",
            "product_status": "BLOCKED_EXTERNAL", "authority": "NONE",
            "release_authorized": False}


def bind_pr70_universe(repo: Path, report: dict, *, base: str, head: str) -> dict:
    """Check a claimed 77-case result against BOTH committed PR70 atlases.

    Not an execution witness: only the upstream runner can replay native code.
    Fail closed if the PR70 verifier is absent, the manifest is narrowed, or
    the case identities differ despite an apparently correct denominator.
    """
    from tools import verify_operational_equivalence as upstream
    claim = operational_claim(report, base, head)
    cases, contract = upstream.universe(Path(repo), base, head)
    recorded = [x['case'] for x in report['rows']]
    if len(recorded) != len(cases) or set(recorded) != set(cases):
        raise ValueError('PR70 claimed universe differs from dual-Git atlas')
    manifest = hashlib.sha256(json.dumps(
        contract, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if report.get('manifest_sha256') != manifest:
        raise ValueError('PR70 manifest digest differs from original Git')
    if report.get('universe') != 'ALL_DECLARED_71_CLI_HELP_PLUS_6_NATIVE_OPERATIONS':
        raise ValueError('PR70 observation scope silently modified')
    if report.get('independent_reviewer') != 'NOT_ATTESTED':
        raise ValueError('self-authored reviewer assertion')
    return {
        'schema': 'cora-hforge-pr70-atlas-binding/1',
        'base': base, 'head': head, 'manifest_sha256': manifest,
        'claim_digest': claim['receipt_digest'],
        'cases': 77, 'scope': 'SOURCE_ATLAS_BOUND_RECEIPT_NOT_RUNTIME_REPLAY',
        'authority': 'NONE', 'product_status': 'BLOCKED_EXTERNAL',
    }


def verify_one_run_native(repo: Path, source_receipt: dict) -> dict:
    """Reuse actual CORA One-Run replay, not H-FORGE's shallow schema check."""
    from cora.one_run import verify_one
    if (not isinstance(source_receipt, dict) or
            source_receipt.get('schema') != 'cora-one-run/1' or
            source_receipt.get('authorization') != 'NONE'):
        raise ValueError('non-canonical or authorizing source One-Run')
    if verify_one(Path(repo), source_receipt) is not True:
        raise ValueError('CORA original source replay was not successful')
    return {
        'schema': 'cora-hforge-one-run-native-replay/1',
        'commit': source_receipt['commit'],
        'original_receipt_digest': source_receipt['receipt_digest'],
        'scope': 'REPLAYED_ORIGINAL_SOURCE_ONERUN_NOT_RUNTIME_PRODUCT',
        'authority': 'NONE', 'product_status': 'BLOCKED_EXTERNAL',
    }


def qualified_local_cut(repo: Path, report: dict, *, base: str, head: str,
                        one_run: dict | None = None,
                        replay_native: bool = False) -> dict:
    """Compose an exact-revision LOCAL cut, never an external/global DoD PASS.

    A caller cannot set P1/P2/P4 by submitting success strings: P1 rechecks
    both Git atlases; P2 re-executes PR70 with opt-in; P4 invokes original
    One-Run verifier. P5 explicitly retains unobserved effects and consumers.
    """
    binding = bind_pr70_universe(repo, report, base=base, head=head)
    structure = compare_trees(Path(repo), base, head)
    source_replay = None
    native_replay = None
    if one_run is not None:
        source_replay = verify_one_run_native(repo, one_run)
        if source_replay['commit'] != head:
            raise ValueError('One-Run must be bound to exact candidate HEAD')
    if replay_native:
        from tools import verify_operational_equivalence as upstream
        if upstream.verify(Path(repo), report, execute_pinned_native=True) is not True:
            raise ValueError('PR70 replay was not independently reproduced')
        native_replay = {
            'status': ('REPLAYED_FINITE_PASS' if report['status'] ==
                       'PASS_EXHAUSTIVE_FINITE_OBSERVATIONS' else
                       'REPLAYED_FINITE_REFUTED'), 'denominator': 77,
        }
    gates = {
        'P0': 'PASS_LOCAL_GIT_SOURCE_PIN',
        'P1': 'PASS_SOURCE_ATLAS_BOUND_NOT_NATIVE',
        'P2': ('PASS_FINITE_NATIVE_REPLAY_ONLY' if native_replay is not None and
               native_replay['status'] == 'REPLAYED_FINITE_PASS' else 'HOLD'),
        'P3': ('PASS_GIT_TREE_METRICS' if structure['unresolved_gitlinks'] == 0
               else 'HOLD_GITLINKS'),
        'P4': ('PASS_SOURCE_ONE_RUN_REPLAY_ONLY' if source_replay else 'HOLD'),
        'P5': 'HOLD_EXTERNAL_EFFECTS_CONSUMERS_REVIEW',
    }
    result = {
        'schema': 'cora-hforge-local-qualified-cut/1',
        'base': base, 'head': head, 'structure': structure,
        'atlas_binding': binding, 'native_replay': native_replay,
        'one_run_replay': source_replay, 'gates': gates,
        'unresolved': [
            'COMPLETE_ORIGINAL_GIT_HISTORY_UNAVAILABLE_IN_ZIP',
            'UNBOUNDED_DYNAMIC_CONSUMERS_UNOBSERVED',
            'PERSISTENT_SIDE_EFFECTS_NOT_COVERED_BY_PR70',
            'NATIVE_PRODUCT_ERROR_RECOVERY_UNVERIFIED',
            'EXTERNAL_CONSUMERS_AND_REVIEW_NOT_ATTESTED',
            'HOST_RELEASE_GOVERNANCE_NOT_ATTESTED',
        ],
        'global_dod': 'NOT_DEMONSTRATED', 'authorization': 'NONE',
        'release_authorized': False, 'product_status': 'BLOCKED_EXTERNAL',
    }
    result['digest'] = hashlib.sha256(
        b'CORA:HFORGE:QUALIFIED-LOCAL-CUT:1\0' +
        _canonical_digest(result).encode('ascii')).hexdigest()
    return result


def verify_local_cut(repo: Path, result: dict, report: dict, *,
                     one_run: dict | None = None,
                     replay_native: bool = False) -> bool:
    """Independently recompute against Git, PR70, and original One-Run."""
    if not isinstance(result, dict) or result.get('schema') != (
            'cora-hforge-local-qualified-cut/1'):
        raise ValueError('unsupported local H-FORGE cut')
    if result != qualified_local_cut(
            repo, report, base=result.get('base'), head=result.get('head'),
            one_run=one_run, replay_native=replay_native):
        raise ValueError('H-FORGE source cut does not independently replay')
    return True
