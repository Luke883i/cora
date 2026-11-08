"""Portable, logically append-only ChatGPT iteration ledger for One-Run.

Every entry is caller-supplied or locally generated, never human-approved.
The hash chain detects accidental and untrusted edits only when a trusted
previous digest is retained outside the archive; it is not a signature.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from .reticulum import MODEL, BLOCKED, EXTERNAL, REFUTED, assess_cut, ordered_cut

SCHEMA = "cora-chat-iteration/1"
BUNDLE_SCHEMA = "cora-chat-bundle/1"
MAX_ROUNDS = 128
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ENTRY_BYTES = 8 * 1024 * 1024
FILES = ("step.json", "source-receipt.json", "dod.json", "handoff.md", "manifest.json")
ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
SESSION = re.compile(r"^[a-z][a-z0-9_-]{2,39}$")
SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")


def _json(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json(data: bytes) -> object:
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError("duplicate JSON field")
            result[k] = v
        return result
    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs)


def _string(value: object, what: str, limit: int = 1500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise ValueError("invalid " + what)
    return value.strip()


def _rows(data: object, keys: set[str], what: str) -> list[dict]:
    if not isinstance(data, list) or not 1 <= len(data) <= 128:
        raise ValueError("missing/oversized " + what)
    ids = set()
    for item in data:
        if not isinstance(item, dict) or set(item) != keys:
            raise ValueError("invalid " + what + " fields")
        key = item["id"]
        if not isinstance(key, str) or not ID.fullmatch(key) or key in ids:
            raise ValueError("duplicate/invalid " + what + " identity")
        ids.add(key)
    return data


def validate_step(step: object) -> dict:
    if not isinstance(step, dict) or set(step) != {
        "schema", "session_id", "iteration", "intent", "actions", "roadmap",
        "falsifiers", "dod", "gaps", "next_step"} or step["schema"] != SCHEMA:
        raise ValueError("invalid chat iteration contract")
    if not isinstance(step["session_id"], str) or not SESSION.fullmatch(step["session_id"]):
        raise ValueError("invalid chat session id")
    if type(step["iteration"]) is not int or not 1 <= step["iteration"] <= MAX_ROUNDS:
        raise ValueError("invalid chat iteration number")
    _string(step["intent"], "intent")
    _string(step["next_step"], "next step")
    acts = _rows(step["actions"], {"id", "action", "status"}, "actions")
    for a in acts:
        _string(a["action"], "action")
        if a["status"] not in ("TODO", "DONE_REPORTED", "BLOCKED"):
            raise ValueError("action status cannot authorize work")
    fals = _rows(step["falsifiers"], {"id", "claim", "method", "oracle", "status"}, "falsifiers")
    for f in fals:
        for key in ("claim", "method", "oracle"):
            _string(f[key], "falsifier " + key)
        if f["status"] not in ("NOT_RUN", "PASS_REPORTED", "REFUTED_REPORTED"):
            raise ValueError("invalid falsification status")
    if not isinstance(step["dod"], dict) or set(step["dod"]) != {"goal", "nodes"}:
        raise ValueError("missing reticular DoD")
    nodes = _rows(step["dod"]["nodes"],
                  {"id", "depends_on", "scope", "acceptance", "observation", "evidence_refs"}, "DoD")
    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        _string(n["acceptance"], "DoD acceptance")
        if n["scope"] not in ("SOURCE", "EXTERNAL") or n["observation"] not in (
                "UNOBSERVED", "REPORTED_OBSERVED", "REFUTED"):
            raise ValueError("unsupported DoD state")
        if not isinstance(n["depends_on"], list) or any(
                not isinstance(k, str) or k not in node_ids for k in n["depends_on"]):
            raise ValueError("unresolved DoD dependency")
        if not isinstance(n["evidence_refs"], list) or len(n["evidence_refs"]) > 16 or any(
                not isinstance(e, str) or len(e) > 256 or not e.strip() for e in n["evidence_refs"]):
            raise ValueError("invalid evidence references")
        if n["depends_on"] and n["observation"] != "UNOBSERVED":
            raise ValueError("aggregate DoD nodes cannot self-report outcomes")
        if not n["depends_on"] and n["scope"] == "EXTERNAL" and n["observation"] == "REPORTED_OBSERVED":
            raise ValueError("external evidence cannot be self-approved")
        if not n["depends_on"] and n["observation"] == "REPORTED_OBSERVED" and not n["evidence_refs"]:
            raise ValueError("claimed observation needs a declared source reference")
    ordered = ordered_cut(nodes, step["dod"]["goal"])
    if set(ordered) != node_ids:
        raise ValueError("orphan DoD node")
    fals_ids = {f["id"] for f in fals}
    roads = _rows(step["roadmap"],
                  {"id", "action", "depends_on", "dod_refs", "falsifier_refs", "status"}, "roadmap")
    road_ids = {r["id"] for r in roads}
    for item in roads:
        _string(item["action"], "roadmap action")
        if item["status"] not in ("TODO", "IN_PROGRESS", "DONE_REPORTED", "BLOCKED"):
            raise ValueError("invalid roadmap state")
        for key, allowed in (("depends_on", road_ids), ("dod_refs", node_ids),
                             ("falsifier_refs", fals_ids)):
            values = item[key]
            if not isinstance(values, list) or len(values) > 32 or any(v not in allowed for v in values):
                raise ValueError("unresolved roadmap relation")
            if key != "depends_on" and not values:
                raise ValueError("roadmap action lacks DoD/falsifier trace")
    if set(ordered_cut(roads, roads[-1]["id"])) != road_ids:
        raise ValueError("orphan roadmap action")
    gaps = _rows(step["gaps"], {"id", "description", "blocks", "next_action"}, "gaps")
    covered = set()
    for g in gaps:
        _string(g["description"], "gap")
        _string(g["next_action"], "gap recovery")
        if not isinstance(g["blocks"], list) or not g["blocks"] or any(
                n not in node_ids for n in g["blocks"]):
            raise ValueError("gap lacks DoD relation")
        covered.update(g["blocks"])
    missing = {n["id"] for n in nodes if not n["depends_on"] and (
        n["scope"] == "EXTERNAL" or n["observation"] != "REPORTED_OBSERVED")}
    if not missing.issubset(covered):
        raise ValueError("unreported blocking DoD gap")
    actionable = {ref for action in roads if action["status"] != "DONE_REPORTED"
                  for ref in action["dod_refs"]}
    if not missing.issubset(actionable):
        raise ValueError("unresolved DoD obligations missing a live falsification roadmap")
    return step



def load_chat_step(path: Path) -> dict:
    """Load a bounded, unambiguous caller JSON; never silently accept duplicate keys."""
    source = Path(path)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_ENTRY_BYTES:
        raise ValueError("invalid or oversized chat iteration input")
    return validate_step(_strict_json(source.read_bytes()))


def _derived(step: dict) -> dict:
    nodes = step["dod"]["nodes"]
    observations = {}
    for n in nodes:
        if n["depends_on"]:
            continue
        observations[n["id"]] = (EXTERNAL if n["scope"] == "EXTERNAL" else
                                  REFUTED if n["observation"] == "REFUTED" else
                                  MODEL if n["observation"] == "REPORTED_OBSERVED" else BLOCKED)
    result = assess_cut(nodes, step["dod"]["goal"], observations)
    return {
        "schema": "cora-chat-derived-dod/1", "goal": result["goal"],
        "dependency_order": result["ordered_cut"], "states": result["states"],
        "next_unresolved": result["next_unresolved"],
        "next_falsification_actions": [
            {"action_id": r["id"], "falsifier_ids": r["falsifier_refs"]}
            for r in step["roadmap"] if result["next_unresolved"] in r["dod_refs"]
            and r["status"] != "DONE_REPORTED"],
        "proof_level": "CALLER_REPORTED_FINITE_MODEL_NOT_ATTESTED",
        "product_status": "BLOCKED_EXTERNAL", "authorization": "NONE",
    }


def _handoff(step: dict, commit: str, trace: dict) -> bytes:
    def plain(x):
        return str(x).replace("\r", " ").replace("\n", " ").replace("`", "'").strip()
    lines = ["# CORA chat handoff (untrusted user-supplied plan)", "",
             "Session: " + step["session_id"] + " | iteration: " + str(step["iteration"]),
             "Git source: " + commit, "Intent: " + plain(step["intent"]),
             "DoD goal: " + trace["goal"] + " | status: " + trace["states"][trace["goal"]],
             "Next unresolved DoD: " + str(trace["next_unresolved"]),
             "Suggested next falsification actions (derived from unresolved DoD): " +
             ", ".join(v["action_id"] for v in trace["next_falsification_actions"]),
             "", "## Roadmap (caller statements; not verification)"]
    for r in step["roadmap"]:
        lines.append("- " + r["id"] + " [" + r["status"] + "]: " + plain(r["action"]))
    lines += ["", "## Falsification strategy"]
    for f in step["falsifiers"]:
        lines.append("- " + f["id"] + " [" + f["status"] + "]: " + plain(f["claim"]) +
                     " | oracle: " + plain(f["oracle"]))
    lines += ["", "## Explicit unresolved gaps"]
    for g in step["gaps"]:
        lines.append("- " + g["id"] + " -> " + ", ".join(g["blocks"]) + ": " +
                     plain(g["description"]) + " | next: " + plain(g["next_action"]))
    lines += ["", "Next step: " + plain(step["next_step"]), "",
              "REVIEW BOUNDARY: Git source observation is not target behavior; bundle hashes",
              "are not signatures; this handoff cannot grant merge, release or reviewer authority.", ""]
    return "\n".join(lines).encode("utf-8")


def _validate_receipt(receipt: object) -> dict:
    if not isinstance(receipt, dict) or (receipt.get("schema") != "cora-integrated-one-run/2"
            or receipt.get("product_status") != "BLOCKED_EXTERNAL"
            or receipt.get("authorization") != "NONE"
            or receipt.get("authority") != "NONE"
            or receipt.get("release_authorized") is not False
            or not isinstance(receipt.get("commit"), str)
            or not SHA.fullmatch(receipt["commit"])):
        raise ValueError("chat bundle requires unpromoted comprehensive One-Run receipt")
    return receipt


def _entry(prefix: str, name: str) -> str:
    return prefix + "/" + name


def _read_archive(path: Path) -> tuple[dict, int, str | None, str | None]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("invalid or oversized chat bundle")
    with zipfile.ZipFile(path) as z:
        records = z.infolist()
        if len(records) > 1 + MAX_ROUNDS * len(FILES) or len(records) < 1:
            raise ValueError("invalid chat bundle entry count")
        names = [v.filename for v in records]
        if len(names) != len(set(names)) or "meta/session.json" not in names:
            raise ValueError("duplicate or missing chat bundle entry")
        total = 0
        for v in records:
            total += v.file_size
            if (v.file_size > MAX_ENTRY_BYTES or total > MAX_ARCHIVE_BYTES
                    or v.flag_bits & 1 or v.is_dir() or v.filename.startswith("/")
                    or "\\" in v.filename or ".." in v.filename.split("/")
                    or (v.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("unsafe chat bundle entry")
        meta = _strict_json(z.read("meta/session.json"))
        if (not isinstance(meta, dict) or _json(meta) != z.read("meta/session.json") or
                set(meta) != {"schema", "session_id"}
                or meta["schema"] != BUNDLE_SCHEMA
                or not isinstance(meta["session_id"], str)
                or not SESSION.fullmatch(meta["session_id"])):
            raise ValueError("invalid chat session metadata")
        if (len(names) - 1) % len(FILES):
            raise ValueError("incomplete chat iteration")
        count = (len(names) - 1) // len(FILES)
        if not 1 <= count <= MAX_ROUNDS:
            raise ValueError("no chat iterations")
        expected = {"meta/session.json"}
        parent = None
        last_commit = None
        for i in range(1, count + 1):
            prefix = f"iterations/{i:06d}"
            expected.update(_entry(prefix, name) for name in FILES)
            step_bytes = z.read(_entry(prefix, "step.json"))
            step = validate_step(_strict_json(step_bytes))
            if step_bytes != _json(step) or step["session_id"] != meta["session_id"] or step["iteration"] != i:
                raise ValueError("noncanonical/misaligned chat iteration")
            receipt_bytes = z.read(_entry(prefix, "source-receipt.json"))
            receipt = _validate_receipt(_strict_json(receipt_bytes))
            if receipt_bytes != _json(receipt):
                raise ValueError("noncanonical source receipt")
            trace_bytes = z.read(_entry(prefix, "dod.json"))
            if trace_bytes != _json(_derived(step)):
                raise ValueError("reticular DoD was not derived from current step")
            handoff_bytes = z.read(_entry(prefix, "handoff.md"))
            if handoff_bytes != _handoff(step, receipt["commit"], _derived(step)):
                raise ValueError("handoff differs from step")
            manifest_bytes = z.read(_entry(prefix, "manifest.json"))
            manifest = _strict_json(manifest_bytes)
            entries = {name: {"sha256": _hash(z.read(_entry(prefix, name))),
                              "bytes": len(z.read(_entry(prefix, name)))} for name in FILES[:-1]}
            expected_manifest = {"schema": "cora-chat-manifest/1", "sequence": i,
                                 "session_id": meta["session_id"], "source_commit": receipt["commit"],
                                 "previous_sha256": parent, "entries": entries,
                                 "authority": "NONE", "product_status": "BLOCKED_EXTERNAL"}
            if manifest_bytes != _json(expected_manifest):
                raise ValueError("chat manifest/hash chain mismatch")
            parent = _hash(manifest_bytes)
            last_commit = receipt["commit"]
        if set(names) != expected:
            raise ValueError("unmanifested chat bundle entry")
    return meta, count, parent, last_commit



def _continuation_from_verified_bundle(path: Path, count: int) -> dict:
    """Bounded next-step *advice* from already replayed, untrusted session records.

    N is observed a posteriori, never precomputed. Reworded roadmaps and
    DONE_REPORTED labels do not constitute behavioral or engineering progress.
    No tool execution, permission, source rewrite or release follows this hint.
    """
    recent = []
    with zipfile.ZipFile(path) as archive:
        for i in range(max(1, count - 2), count + 1):
            prefix = f"iterations/{i:06d}"
            step = _strict_json(archive.read(prefix + "/step.json"))
            receipt = _strict_json(archive.read(prefix + "/source-receipt.json"))
            # _read_archive has already validated these exact bounded entries.
            nodes = step["dod"]["nodes"]
            structure = sorted((n["id"], n["scope"], n["acceptance"],
                                tuple(sorted(n["depends_on"]))) for n in nodes)
            fingerprint = _hash(_json({
                "intent": step["intent"], "goal": step["dod"]["goal"],
                "nodes": structure,
            }))
            reports = sorted((n["id"], n["observation"],
                              tuple(sorted(n["evidence_refs"]))) for n in nodes
                             if not n["depends_on"])
            recent.append({"step": step, "receipt": receipt,
                           "contract_hash": fingerprint,
                           "source_evidence_hash": _hash(_json({
                               "commit": receipt["commit"], "reports": reports,
                           }))})
    last = recent[-1]
    derived = _derived(last["step"])
    next_id = derived["next_unresolved"]
    index = {n["id"]: n for n in last["step"]["dod"]["nodes"]}
    previous = recent[-2] if len(recent) > 1 else None
    contract_drift = bool(previous and previous["contract_hash"] != last["contract_hash"])
    changed_sha = bool(previous and previous["receipt"]["commit"] != last["receipt"]["commit"])
    self_reports_changed = bool(previous and not changed_sha and
                                previous["source_evidence_hash"] != last["source_evidence_hash"])
    no_progress_tail = (len(recent) == 3 and
                        len({r["contract_hash"] for r in recent}) == 1 and
                        len({r["source_evidence_hash"] for r in recent}) == 1)
    if count >= MAX_ROUNDS:
        decision = "PAUSE_CAPACITY_AND_REBASE"
    elif contract_drift:
        decision = "REVIEW_CHANGED_CONTRACT"
    elif changed_sha:
        decision = "REVALIDATE_CHANGED_SOURCE"
    elif no_progress_tail:
        decision = "REPLAN_STALLED_REPORTS"
    elif next_id is None:
        decision = "REQUEST_INDEPENDENT_ACCEPTANCE"
    elif index[next_id]["scope"] == "EXTERNAL":
        decision = "REQUEST_EXTERNAL_WITNESS"
    else:
        decision = "PROPOSE_NEXT_SCOPED_STEP"
    return {
        "schema": "cora-chat-continuation-advice/1",
        "iterations_observed": count, "iteration_capacity_left": MAX_ROUNDS - count,
        "next_iteration_if_authorized": count + 1 if count < MAX_ROUNDS else None,
        "predetermined_total_N": None,
        "next_unresolved": next_id,
        "next_falsification_actions": derived["next_falsification_actions"],
        "reported_open_leaves": sum(
            1 for node in last["step"]["dod"]["nodes"]
            if not node["depends_on"] and
            derived["states"][node["id"]] != MODEL),
        "contract_drift": contract_drift,
        "source_revision_changed": changed_sha,
        "caller_only_evidence_delta": self_reports_changed,
        "repeated_no_progress_tail": no_progress_tail,
        "decision": decision, "automatic_execution": False,
        "product_accepted": False, "authorization": "NONE",
        "proof_boundary": "SOURCE_REPLAY_AND_CALLER_REPORTS_NOT_TARGET_ATTESTATION",
    }


def verify_chat_bundle(path: Path, *, expected_receipt: dict | None = None) -> dict:
    meta, count, latest_hash, commit = _read_archive(Path(path))
    if expected_receipt is not None:
        with zipfile.ZipFile(path) as z:
            actual = _strict_json(z.read(f"iterations/{count:06d}/source-receipt.json"))
        if actual != expected_receipt:
            raise ValueError("chat bundle latest receipt does not match One-Run report")
    return {"schema": "cora-chat-bundle-verification/1", "session_id": meta["session_id"],
            "iterations": count, "last_commit": commit, "last_manifest_sha256": latest_hash,
            "status": "PORTABLE_BYTES_REPLAYED_NOT_INDEPENDENTLY_ATTESTED",
            "authorization": "NONE", "product_status": "BLOCKED_EXTERNAL",
            "continuation": _continuation_from_verified_bundle(Path(path), count)}


def append_chat_iteration(bundle: Path, *, repo: Path, step: dict, receipt: dict) -> dict:
    validate_step(step)
    _validate_receipt(receipt)
    target = Path(bundle).absolute()
    source = Path(repo).resolve(strict=True)
    if target == source or source in target.parents or target.parent == source:
        raise ValueError("chat bundle must stay outside inspected repository")
    if not target.parent.is_dir() or target.is_symlink():
        raise ValueError("chat bundle parent must be a real directory")
    if target.exists() and target.stat().st_nlink > 1:
        raise ValueError("linked archive cannot be rewritten")
    lock = target.with_name(target.name + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("concurrent chat bundle writer") from exc
    os.close(fd)
    tmp = None
    try:
        if target.exists():
            meta, count, parent, _ = _read_archive(target)
            if step["session_id"] != meta["session_id"] or step["iteration"] != count + 1:
                raise ValueError("append-only chat iteration sequence violation")
        else:
            meta = {"schema": BUNDLE_SCHEMA, "session_id": step["session_id"]}
            count, parent = 0, None
            if step["iteration"] != 1:
                raise ValueError("first chat step must be iteration 1")
        if count >= MAX_ROUNDS:
            raise ValueError("chat bundle round limit")
        if target.exists() and target.stat().st_size > MAX_ARCHIVE_BYTES // 2:
            raise ValueError("chat bundle growth limit")
        trace = _derived(step)
        prefix = f"iterations/{count + 1:06d}"
        contents = {"step.json": _json(step), "source-receipt.json": _json(receipt),
                    "dod.json": _json(trace), "handoff.md": _handoff(step, receipt["commit"], trace)}
        manifest = {"schema": "cora-chat-manifest/1", "sequence": count + 1,
                    "session_id": step["session_id"], "source_commit": receipt["commit"],
                    "previous_sha256": parent,
                    "entries": {n: {"sha256": _hash(b), "bytes": len(b)} for n, b in contents.items()},
                    "authority": "NONE", "product_status": "BLOCKED_EXTERNAL"}
        contents["manifest.json"] = _json(manifest)
        if any(len(v) > MAX_ENTRY_BYTES for v in contents.values()):
            raise ValueError("chat iteration entry too large")
        fd, name = tempfile.mkstemp(prefix=".cora-chat-", suffix=".zip", dir=target.parent)
        os.close(fd)
        tmp = Path(name)
        if target.exists():
            shutil.copyfile(target, tmp)
        with zipfile.ZipFile(tmp, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            if count == 0:
                z.writestr("meta/session.json", _json(meta))
            for part, content in contents.items():
                z.writestr(_entry(prefix, part), content)
        result = verify_chat_bundle(tmp, expected_receipt=receipt)
        if tmp.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("chat archive exceeds maximum size")
        os.replace(tmp, target)
        tmp = None
        return result
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)