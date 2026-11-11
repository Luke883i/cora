"""Portable CORA source-only One-Run over a caller-supplied target profile.

The target owns its ontology. A profile/record/log is not an executor, reviewer,
independent behavioral oracle or authorization. Source readback is Git-pinned;
non-Python and dynamic consumers remain explicitly unknown.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

from .evidence import domain_hash, valid_path
from .git_snapshot import git, snapshot
from .process_suite import run_suite

SCHEMA = "cora-portable-one-run/1"
PROFILE = "cora-portable-target/1"
SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}\Z")
TARGET = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{1,63}\Z")
KINDS = {"TEST_LOG", "HTTP", "BROWSER", "SCREENSHOT"}
LINKS = {"METHOD_TRANSFER", "METHODOLOGY_REFERENCE"}
OUTCOMES = {"PASS_REPORTED_UNATTESTED", "FAIL_REPORTED_UNATTESTED"}


def _sha(value: object) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def _path(value: object) -> bool:
    return isinstance(value, str) and valid_path(value) and value not in (".", "..")


def _reject(message: str) -> None:
    raise ValueError("portable: " + message)


def _profile(data: object, commit: str) -> dict:
    if not isinstance(data, dict) or set(data) != {
        "schema", "target_repo", "revision", "owners", "witnesses", "method_links"
    } or data["schema"] != PROFILE:
        _reject("invalid target-owned identity contract")
    if not isinstance(data["target_repo"], str) or not TARGET.fullmatch(data["target_repo"]):
        _reject("invalid target repo")
    if not _sha(data["revision"]) or data["revision"] != commit:
        _reject("stale source revision")
    owners = data["owners"]
    if not isinstance(owners, list) or not owners or len(owners) > 64:
        _reject("missing or oversized source owner list")
    owner_ids = set()
    for owner in owners:
        if not isinstance(owner, dict) or set(owner) != {"id", "path"}:
            _reject("invalid owner")
        if not isinstance(owner["id"], str) or not ID.fullmatch(owner["id"]) or not _path(owner["path"]):
            _reject("invalid owner path")
        if owner["id"] in owner_ids:
            _reject("duplicate source owner")
        owner_ids.add(owner["id"])
    witnesses = data["witnesses"]
    if not isinstance(witnesses, list) or len(witnesses) > 128:
        _reject("invalid witness list")
    seen = set()
    for witness in witnesses:
        if not isinstance(witness, dict) or set(witness) != {
            "id", "category", "path", "sha256", "source_commit",
            "oracle_id", "reported_outcome"
        }:
            _reject("invalid witness envelope")
        if (not isinstance(witness["id"], str) or not ID.fullmatch(witness["id"])
                or witness["id"] in seen or witness["category"] not in KINDS
                or not _path(witness["path"]) or not isinstance(witness["sha256"], str)
                or re.fullmatch(r"[a-f0-9]{64}", witness["sha256"]) is None
                or witness["source_commit"] != commit
                or not isinstance(witness["oracle_id"], str)
                or not ID.fullmatch(witness["oracle_id"])
                or witness["reported_outcome"] not in OUTCOMES):
            _reject("invalid, unbound or forged witness")
        seen.add(witness["id"])
    links = data["method_links"]
    if not isinstance(links, list) or len(links) > 64:
        _reject("invalid method transfer list")
    seen = set()
    for link in links:
        if not isinstance(link, dict) or set(link) != {
            "id", "kind", "source_repo", "source_commit", "target_owner",
            "target_commit", "source_reference"
        }:
            _reject("invalid typed transfer")
        if (not isinstance(link["id"], str) or not ID.fullmatch(link["id"])
                or link["id"] in seen or link["kind"] not in LINKS
                or not isinstance(link["source_repo"], str)
                or not TARGET.fullmatch(link["source_repo"])
                or not _sha(link["source_commit"])
                or link["target_owner"] not in owner_ids
                or link["target_commit"] != commit
                or not isinstance(link["source_reference"], str)
                or not link["source_reference"].startswith(
                    "https://github.com/" + link["source_repo"] + "/")
                or len(link["source_reference"]) > 700):
            _reject("stale/ambiguous upstream method link")
        seen.add(link["id"])
    return data


def _source_owners(repo: Path, commit: str, owners: list[dict]) -> None:
    for owner in owners:
        try:
            git(repo, "cat-file", "-e", commit + ":" + owner["path"], max_output=1024)
        except (ValueError, OSError):
            _reject("owner not in committed source: " + owner["id"])


def _bytes(root: Path, rel: str, target_repo: Path) -> bytes:
    if root.is_symlink() or not root.is_dir():
        _reject("evidence root must be a normal directory")
    base = root.resolve(strict=True)
    source = (base / rel)
    if target_repo == base or target_repo in base.parents:
        _reject("evidence root must be outside inspected repository")
    for node in [source] + list(source.parents)[:len(Path(rel).parts)]:
        if node.is_symlink():
            _reject("evidence symlink prohibited")
    path = source.resolve(strict=True)
    if base not in path.parents or not path.is_file():
        _reject("evidence escapes approved directory")
    if path.stat().st_size > 8 * 1024 * 1024:
        _reject("evidence exceeds bounded size")
    return path.read_bytes()


def run_portable(repo: Path, revision: str, profile: Path, *,
                 evidence_dir: Path | None = None) -> dict:
    """Read-only source dossier. No arbitrary target code or target test execution."""
    repo = Path(repo).resolve(strict=True)
    provenance = snapshot(repo, revision)
    commit = provenance["commit"]
    doc = json.loads(Path(profile).read_text(encoding="utf-8"))
    _profile(doc, commit)
    _source_owners(repo, commit, doc["owners"])
    if evidence_dir is not None:
        evidence_dir = Path(evidence_dir)
    evidence = []
    for w in doc["witnesses"]:
        if evidence_dir is None:
            state = "NOT_RUN"
        else:
            observed = hashlib.sha256(_bytes(evidence_dir, w["path"], repo)).hexdigest()
            if observed != w["sha256"]:
                _reject("evidence tamper: " + w["id"])
            state = "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED"
        evidence.append({
            "id": w["id"], "category": w["category"], "source_commit": commit,
            "oracle_id": w["oracle_id"], "sha256": w["sha256"],
            "reported_outcome": w["reported_outcome"], "state": state
        })
    suite = run_suite(repo, commit, process="full", max_commits=64)
    transfer = [{
        "id": link["id"], "kind": link["kind"],
        "source_repo": link["source_repo"], "source_commit": link["source_commit"],
        "target_owner": link["target_owner"], "target_commit": commit,
        "source_reference": link["source_reference"],
        "state": "FOREIGN_GIT_SOURCE_UNVERIFIED"
    } for link in doc["method_links"]]
    result = {
        "schema": SCHEMA, "commit": commit, "tree": git(repo, "rev-parse", commit + "^{tree}").decode().strip(),
        "target_repo": doc["target_repo"],
        "profile_sha256": hashlib.sha256(
            Path(profile).read_bytes()).hexdigest(),
        "owners": doc["owners"], "source_process": suite,
        "evidence": evidence, "method_links": transfer,
        "js_import_graph": "NOT_OBSERVED_NONPYTHON_CONSUMERS_UNKNOWN",
        "source_status": "DEBT_BLOCKED" if suite["status"] == "DEBT_BLOCKED"
                         else "PASS_SCOPED_GIT_SOURCE_ONLY",
        "behavior_status": "BLOCKED_EXTERNAL",
        "crossrepo_runtime_status": "BLOCKED_EXTERNAL",
        "governed_status": "BLOCKED_EXTERNAL",
        "authorization": "NONE",
        "excluded": ["target execution", "host rights", "reviewer identity",
                     "dynamic callers", "real user acceptance", "release permission"]
    }
    result["receipt_digest"] = domain_hash("CORA:portable-one-run:1", result)
    return result


def render_portable_html(result: dict) -> str:
    """Deterministic, escaped, offline and read-first, not an approval surface."""
    def esc(v: object) -> str:
        return html.escape(str(v), quote=True)
    lines = ["<!doctype html><html lang='en'><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width'>",
             "<title>CORA portable source dossier</title>",
             "<style>body{font:16px system-ui;max-width:850px;margin:3em auto;padding:1em}"
             "li{margin:.55em 0}code{overflow-wrap:anywhere}</style>",
             "<main><h1>CORA portable source dossier</h1>",
             "<p>Source evidence only; independent product acceptance BLOCKED_EXTERNAL.</p>",
             "<h2>Target and revision</h2><p><code>",
             esc(result["target_repo"]), " @ ", esc(result["commit"]), "</code></p>",
             "<h2>What ran</h2><ul>"]
    for method in result["source_process"]["results"]:
        lines.append("<li>" + esc(method["method"]) + ": " + esc(method["status"]) + "</li>")
    lines += ["</ul><h2>Retained evidence (not execution proof)</h2><ul>"]
    for item in result["evidence"]:
        lines.append("<li>" + esc(item["id"]) + ": " + esc(item["state"]) + "</li>")
    lines += ["</ul><h2>External method relations</h2><ul>"]
    for item in result["method_links"]:
        lines.append("<li>" + esc(item["id"]) + ": " + esc(item["state"]) + "</li>")
    lines += ["</ul><h2>Unclosed gates</h2><p>Browser, human acceptance, host,",
              "foreign source readback and release remain BLOCKED_EXTERNAL.</p>",
              "<p>Authorization: NONE. Dynamic and non-Python callers: UNKNOWN.</p>",
              "</main></html>\n"]
    return "".join(lines)


def verify_portable(repo: Path, receipt: dict, profile: Path, *,
                    evidence_dir: Path | None = None,
                    html_page: str | None = None) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        _reject("wrong report schema")
    fresh = run_portable(repo, receipt.get("commit", ""), profile, evidence_dir=evidence_dir)
    if fresh != receipt:
        _reject("Git/source/profile/receipt replay mismatch")
    if html_page is not None and render_portable_html(fresh) != html_page:
        _reject("HTML mismatch")
    return True
