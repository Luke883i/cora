"""Bounded native Gold pilot runner with retained log and exact Git readback.

Running untrusted target code is explicitly opt-in and requires an ephemeral
trusted-isolation decision by the invoking operator. This verifier DOES NOT
authenticate CI runner identity, human oversight, deployment or release.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git

SCHEMA = "cora-native-gold-probe/1"
HASH = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{1,63}$")
# Deliberately narrow; no generic shell, arbitrary commands or test selection.
PILOTS = {
    "Luke883i/teddy": (
        "tests/cora-adoption.test.mjs",
        ("node", "--no-warnings", "--experimental-vm-modules",
         "--test", "tests/cora-adoption.test.mjs"), None
    ),
    "Luke883i/ictc": (
        "tests/verification/e2e-cross-process-receipts-check.mjs",
        ("node", "tests/verification/e2e-cross-process-receipts-check.mjs"),
        "artifacts/e2e-cross-process-receipts.json"
    ),
}
MAX_LOG = 2 * 1024 * 1024
MAX_ARTIFACT = 4 * 1024 * 1024


def _reject(reason: str) -> None:
    raise ValueError("native Gold: " + reason)


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_bounded(root: Path, relative: str, limit: int) -> bytes:
    if root.is_symlink() or not root.is_dir():
        _reject("evidence root is not a normal directory")
    full = root / relative
    if full.is_symlink() or not full.is_file() or full.resolve().parent != root.resolve():
        _reject("evidence path is not a regular direct child of root")
    if full.stat().st_size > limit:
        _reject("evidence byte budget exceeded")
    return full.read_bytes()


def _git_source(repo: Path, sha: str, path: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        _reject("unbound Git revision")
    row = git(repo, "ls-tree", "-z", sha, "--", path, max_output=8192)
    if (not row.endswith(b"\0") or row.count(b"\0") != 1
            or row[:-1].split(b"\t", 1)[-1].decode("utf-8") != path
            or not row.startswith((b"100644 blob ", b"100755 blob "))):
        _reject("oracle is not original regular Git source")
    return _hash(git(repo, "show", sha + ":" + path, max_output=1024 * 1024))


def _ictc_native(payload: object, commit: str) -> bool:
    if not isinstance(payload, dict) or payload.get("schema") != "ictc-e2e-7process-real-write/v2":
        return False
    if payload.get("gitHead") != commit or payload.get("runtimeCommands") != 12:
        return False
    commands = payload.get("commandReceipts")
    negative = payload.get("negative")
    asserts = payload.get("asserts")
    if (not isinstance(commands, list) or len(commands) != 12
            or any(not isinstance(c, dict) or not HASH.fullmatch(str(c.get("receiptHash", "")))
                   for c in commands)
            or not isinstance(negative, dict)
            or not isinstance(negative.get("results"), list)
            or len(negative["results"]) != 7
            or any(not isinstance(x, dict) or x.get("status") != 403
                   for x in negative["results"])
            or negative.get("revisionBeforeDenials") != negative.get("revisionAfterDenials")
            or not isinstance(asserts, dict)):
        return False
    return all(asserts.get(k) is True for k in (
        "sevenProcesses", "integrityBinding", "semanticEventBindings",
        "privateActorIsolation", "deniedAuditorWrite")) and asserts.get("deniedAuditorRoutes") == 7


def _safe_env() -> dict[str, str]:
    allowed = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR")
    return {**{k: os.environ[k] for k in allowed if k in os.environ},
            "CI": "true", "GITHUB_TOKEN": "", "GH_TOKEN": "",
            "NODE_ENV": "test"}


def capture_native(repo: Path, target_repo: str, commit: str,
                   claim_id: str, out: Path) -> dict:
    """EXECUTES one opt-in named test with bounded subprocess; never a test bus.

    Never invoke automatically from source-only process-run or verify-process.
    """
    if target_repo not in PILOTS or not isinstance(claim_id, str) or not ID.fullmatch(claim_id):
        _reject("target/test/claim not allowlisted")
    repo = Path(repo).resolve(strict=True)
    oracle, command, artifact_rel = PILOTS[target_repo]
    if git(repo, "rev-parse", "HEAD").decode().strip() != commit:
        _reject("target HEAD changed")
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        _reject("tracked source worktree not clean before test")
    oracle_hash = _git_source(repo, commit, oracle)
    output = Path(out)
    if output.is_symlink() or output.exists() or repo == output.resolve() or repo in output.resolve().parents:
        _reject("fresh evidence output must be outside target and not a symlink")
    output.mkdir(parents=True, exist_ok=False)
    try:
        execution = subprocess.run(
            list(command), cwd=repo, env=_safe_env(),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=120, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        _reject("native subprocess unavailable/timeout: " + str(exc)[:100])
    if len(execution.stdout) > MAX_LOG:
        _reject("native process log too large")
    log = execution.stdout
    (output / "run.log").write_bytes(log)
    artifact_sha = None
    if artifact_rel and execution.returncode == 0:
        path = repo / artifact_rel
        if path.is_symlink() or not path.is_file() or repo not in path.resolve().parents:
            _reject("missing or unsafe native runtime artifact")
        if path.stat().st_size > MAX_ARTIFACT:
            _reject("native runtime artifact exceeds byte budget")
        raw = path.read_bytes()
        if not _ictc_native(json.loads(raw), commit):
            _reject("ICTC native HTTP/SQLite result does not meet local oracle")
        (output / "artifact.json").write_bytes(raw)
        artifact_sha = _hash(raw)
    if execution.returncode == 0 and target_repo == "Luke883i/teddy":
        if b"TAP version" not in log or b"# fail 0" not in log:
            _reject("Teddy Node test returned zero without TAP evidence")
    record = {
        "schema": SCHEMA, "target_repo": target_repo,
        "source_commit": commit, "claim_id": claim_id,
        "oracle_path": oracle, "oracle_sha256": oracle_hash,
        "command": list(command), "exit_code": execution.returncode,
        "log_file": "run.log", "log_sha256": _hash(log),
        "artifact_file": "artifact.json" if artifact_sha else None,
        "artifact_sha256": artifact_sha,
        "node_test": target_repo == "Luke883i/teddy",
        "runtime_scope": "LOCAL_PROCESS_EXIT_OBSERVED_BY_THIS_INVOCATION",
        "issuer_authentication": "NONE",
        "independent_review": "BLOCKED_EXTERNAL",
        "release_authorization": "NONE",
    }
    record["digest"] = domain_hash("CORA:native-gold-probe:1", record)
    (output / "receipt.json").write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return record


def replay_native(repo: Path, evidence_dir: Path,
                  record: dict | None = None) -> dict:
    """Byte/Git replay of a producer's claim, NOT proof it actually executed."""
    repo = Path(repo).resolve(strict=True)
    root = Path(evidence_dir)
    raw = _read_bounded(root, "receipt.json", MAX_ARTIFACT)
    declared = json.loads(raw)
    if record is not None and declared != record:
        _reject("native receipt replaced")
    if not isinstance(declared, dict) or set(declared) != {
        "schema", "target_repo", "source_commit", "claim_id",
        "oracle_path", "oracle_sha256", "command", "exit_code",
        "log_file", "log_sha256", "artifact_file", "artifact_sha256",
        "node_test", "runtime_scope", "issuer_authentication",
        "independent_review", "release_authorization", "digest"
    } or declared["schema"] != SCHEMA:
        _reject("invalid native receipt envelope")
    if (declared["target_repo"] not in PILOTS
            or not ID.fullmatch(str(declared["claim_id"]))):
        _reject("unrecognized pilot or claim")
    oracle, command, artifact_path = PILOTS[declared["target_repo"]]
    if (declared["oracle_path"] != oracle or declared["command"] != list(command)
            or declared["runtime_scope"] != "LOCAL_PROCESS_EXIT_OBSERVED_BY_THIS_INVOCATION"
            or declared["issuer_authentication"] != "NONE"
            or declared["independent_review"] != "BLOCKED_EXTERNAL"
            or declared["release_authorization"] != "NONE"
            or declared["node_test"] != (declared["target_repo"] == "Luke883i/teddy")
            or type(declared["exit_code"]) is not int
            or not -999 <= declared["exit_code"] <= 999
            or declared["log_file"] != "run.log"):
        _reject("native runner authority/command invalid")
    digest = declared.pop("digest")
    if domain_hash("CORA:native-gold-probe:1", declared) != digest:
        _reject("native receipt digest altered")
    declared["digest"] = digest
    if _git_source(repo, declared["source_commit"], oracle) != declared["oracle_sha256"]:
        _reject("native oracle Git source SHA drift")
    log = _read_bounded(root, "run.log", MAX_LOG)
    if _hash(log) != declared["log_sha256"]:
        _reject("native log tampered")
    if declared["exit_code"] == 0 and declared["node_test"]:
        if b"TAP version" not in log or b"# fail 0" not in log:
            _reject("TAP replay mismatch")
    if artifact_path is not None and declared["exit_code"] == 0:
        if declared["artifact_file"] != "artifact.json":
            _reject("ICTC artifact missing")
        artifact = _read_bounded(root, "artifact.json", MAX_ARTIFACT)
        if _hash(artifact) != declared["artifact_sha256"]:
            _reject("native artifact hash drift")
        if not _ictc_native(json.loads(artifact), declared["source_commit"]):
            _reject("native artifact oracle divergence")
    elif declared["artifact_file"] is not None or declared["artifact_sha256"] is not None:
        _reject("unexpected native artifact")
    return {
        "schema": "cora-native-gold-replay/1",
        "commit": declared["source_commit"], "target_repo": declared["target_repo"],
        "claim_id": declared["claim_id"], "oracle_path": oracle,
        "oracle_sha256": declared["oracle_sha256"], "runner_receipt_digest": digest,
        "report_status": ("LOCAL_RUNNER_PASS_REPORTED_UNAUTHENTICATED"
                          if declared["exit_code"] == 0 else "LOCAL_RUNNER_FAIL_REPORTED"),
        "log_sha256": declared["log_sha256"],
        "artifact_sha256": declared["artifact_sha256"],
        "execution_replay": "NOT_PERFORMED_SOURCE_AND_BYTE_READBACK_ONLY",
        "issuer_authenticated": False,
        "independent_oracle": "BLOCKED_EXTERNAL", "authorization": "NONE",
    }
