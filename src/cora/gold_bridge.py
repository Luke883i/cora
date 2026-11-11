"""Gold R1-R4 claim-to-oracle-to-native-witness source bridge.

A profile is caller-declared. Matching an original Git oracle to retained
observation bytes is NOT executing the oracle, authenticating its issuer,
assessing product correctness or granting host/release authority. This module
reuses CORA's existing reticulum and digest kernel, not a second approval bus.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .evidence import domain_hash, valid_path
from .git_snapshot import git
from .reticulum import ordered_cut

SCHEMA = "cora-portable-gold-bridge/1"
PROFILE = "cora-portable-target/2"
IDS = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{1,63}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
SCOPES = {"SOURCE", "BEHAVIOR", "EXTERNAL"}
KEYS = {
    "id", "claim", "scope", "owner_id", "source_path", "oracle_id",
    "oracle_path", "oracle_sha256", "witness_ids", "depends_on"
}


def _error(reason: str) -> None:
    raise ValueError("gold-bridge: " + reason)


def _id(value: object) -> bool:
    return isinstance(value, str) and IDS.fullmatch(value) is not None


def _regular_blob(repo: Path, revision: str, path: str) -> str:
    """Verify the exact regular committed Git blob and return its SHA-256."""
    if not valid_path(path):
        _error("unsafe original source/oracle path")
    try:
        record = git(repo, "ls-tree", "-z", revision, "--", path, max_output=8192)
        if not record.endswith(b"\0") or record.count(b"\0") != 1:
            _error("original oracle absent, ambiguous, or not regular")
        metadata, actual_path = record[:-1].split(b"\t", 1)
        if (actual_path.decode("utf-8") != path
                or not metadata.startswith((b"100644 blob ", b"100755 blob "))):
            _error("oracle must be a regular tracked source file")
        contents = git(repo, "show", revision + ":" + path, max_output=1024 * 1024)
    except (ValueError, OSError, UnicodeError) as exc:
        _error("oracle source Git readback unavailable: " + str(exc)[:90])
    return hashlib.sha256(contents).hexdigest()


def bridge_gold(repo: Path, commit: str, profile: dict,
                evidence: list[dict]) -> dict:
    """Create evidence *linkage*, never a claim that a native oracle ran."""
    if profile.get("schema") != PROFILE or not isinstance(profile.get("claims"), list):
        _error("Gold claim bindings require target-owned profile v2")
    claims = profile["claims"]
    if not 1 <= len(claims) <= 64 or not _id(profile.get("goal")):
        _error("bounded claim reticulum and one goal required")
    if profile.get("revision") != commit:
        _error("stale source revision")
    owner_paths = {o["id"]: o["path"] for o in profile["owners"]}
    declarations = {w["id"]: w for w in profile["witnesses"]}
    observed = {w["id"]: w for w in evidence}
    if len(observed) != len(declarations):
        _error("evidence inventory differs from declared witness IDs")
    seen, used_witnesses, validated = set(), set(), []
    for row in claims:
        if not isinstance(row, dict) or set(row) != KEYS:
            _error("unknown/missing claim field")
        key, owner, path = row["id"], row["owner_id"], row["source_path"]
        if not _id(key) or key in seen:
            _error("invalid or duplicate claim")
        seen.add(key)
        if (owner not in owner_paths or owner_paths[owner] != path
                or row["scope"] not in SCOPES
                or not isinstance(row["claim"], str)
                or not 12 <= len(row["claim"]) <= 1200
                or not _id(row["oracle_id"])
                or not isinstance(row["oracle_sha256"], str)
                or HASH.fullmatch(row["oracle_sha256"]) is None
                or not isinstance(row["witness_ids"], list)
                or not isinstance(row["depends_on"], list)
                or len(row["witness_ids"]) > 32):
            _error("claim/owner/oracle contract invalid")
        if (any(not _id(w) for w in row["witness_ids"])
                or len(set(row["witness_ids"])) != len(row["witness_ids"])
                or any(not _id(dep) for dep in row["depends_on"])
                or len(set(row["depends_on"])) != len(row["depends_on"])):
            _error("invalid or duplicate claim dependency/witness")
        # Only committed Git can substantiate the oracle's SOURCE IDENTITY.
        oracle_digest = _regular_blob(repo, commit, row["oracle_path"])
        if oracle_digest != row["oracle_sha256"]:
            _error("oracle byte drift versus original Git")
        bindings = []
        for wid in row["witness_ids"]:
            if wid not in declarations or wid in used_witnesses or wid not in observed:
                _error("missing/reused/unbound native witness")
            declaration, source = declarations[wid], observed[wid]
            if (declaration["source_commit"] != commit
                    or declaration["oracle_id"] != row["oracle_id"]
                    or source["oracle_id"] != row["oracle_id"]
                    or source["source_commit"] != commit
                    or source["sha256"] != declaration["sha256"]):
                _error("oracle or Git SHA mismatch in native witness")
            used_witnesses.add(wid)
            bindings.append({
                "id": wid, "category": source["category"], "sha256": source["sha256"],
                "observed": source["state"],
                "reported_outcome": source["reported_outcome"],
                "issuer_authenticated": False,
                "execution_attested": False,
            })
        validated.append({
            "id": key, "claim": row["claim"], "scope": row["scope"],
            "owner_id": owner, "source_path": path,
            "oracle_id": row["oracle_id"], "oracle_path": row["oracle_path"],
            "oracle_sha256": oracle_digest, "depends_on": list(row["depends_on"]),
            "witnesses": bindings, "source_git_readback": "ORIGINAL_BLOB_SHA256",
        })
    if used_witnesses != set(declarations):
        _error("orphan native witnesses must be bound to exactly one claim")
    try:
        ordered = ordered_cut(validated, profile["goal"])
    except ValueError as exc:
        _error("invalid noncompensatory DAG: " + str(exc))
    if len(ordered) != len(validated):
        _error("orphan claim outside declared goal")
    index = {item["id"]: item for item in validated}
    states: dict[str, str] = {}
    for key in ordered:
        node = index[key]
        rows = node["witnesses"]
        if not rows:
            status = "BLOCKED_NO_NATIVE_WITNESS"
        elif any(w["reported_outcome"] == "FAIL_REPORTED_UNATTESTED" for w in rows):
            status = "COUNTEREVIDENCE_REPORTED_UNATTESTED"
        elif any(w["observed"] != "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED"
                 for w in rows):
            status = "BLOCKED_NATIVE_BYTES_NOT_OBSERVED"
        elif node["scope"] == "EXTERNAL":
            status = "BLOCKED_EXTERNAL"
        elif any(states[dep] != "SOURCE_LINK_ONLY_UNATTESTED"
                 for dep in node["depends_on"]):
            status = "BLOCKED_PREREQUISITE"
        elif node["scope"] == "SOURCE":
            status = "SOURCE_LINK_ONLY_UNATTESTED"
        else:
            status = "BEHAVIOR_BYTES_ONLY_EXECUTION_UNATTESTED"
        states[key] = status
        node["status"] = status
        node["claim_proven"] = False
    result = {
        "schema": SCHEMA, "commit": commit, "target_repo": profile["target_repo"],
        "goal": profile["goal"], "ordered_cut": ordered,
        "claims": [index[key] for key in ordered],
        "source_oracle_bytes_replayed": len(validated),
        "native_witnesses_bound": len(used_witnesses),
        "native_witness_bytes_verified": sum(
            1 for r in validated for w in r["witnesses"]
            if w["observed"] == "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED"),
        "reported_counterevidence": sum(
            1 for r in validated for w in r["witnesses"]
            if w["reported_outcome"] == "FAIL_REPORTED_UNATTESTED"),
        "goal_status": "BLOCKED_INDEPENDENT_ORACLE_EXECUTION_AND_REVIEW",
        "gold_rails": {
            "R1": "COMMITTED_OWNER_AND_ORACLE_SOURCE_READBACK",
            "R2": "ORACLE_BYTES_READ_NOT_EXECUTED",
            "R3": "RETAINED_BYTES_IF_SUPPLIED_ISSUER_UNAUTHENTICATED",
            "R4": "INDEPENDENT_PRODUCT_PILOT_NOT_ATTESTED"
        },
        "external_status": "BLOCKED_EXTERNAL",
        "authorization": "NONE",
        "not_proven": [
            "oracle invocation", "native test success", "browser semantics",
            "artifact producer identity", "trusted CI", "human acceptance",
            "deployment", "release permission"
        ]
    }
    result["digest"] = domain_hash("CORA:portable-gold-bridge:1", result)
    return result
