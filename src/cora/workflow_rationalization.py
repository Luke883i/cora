"""CORA Git-bound CI workflow discovery and conservative rationalization.

Read-only: no workflow execution, deletion, rewrite, GitHub API access, or claims of
external consumer closure. Supported YAML constructs are deliberately a subset;
unknown dynamic syntax cannot be silently treated as absence of dependencies.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .git_snapshot import git, _sizes, _read_objects

SCHEMA = "cora-workflow-rationalization/1"
PREFIX = ".github/workflows/"
SUFFIX = (".yml", ".yaml")
TEXT_SUFFIX = (".md", ".json", ".yml", ".yaml", ".py", ".mjs",
               ".js", ".sh", ".toml", ".txt", ".xml")
MAX_WORKFLOWS = 1024
MAX_SCAN_PATHS = 8000
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_FILE = 512 * 1024
EVENTS = frozenset(("push", "pull_request", "pull_request_target",
                    "workflow_call", "workflow_dispatch", "workflow_run",
                    "repository_dispatch", "schedule", "merge_group",
                    "deployment", "deployment_status", "release",
                    "create", "delete", "issue_comment", "issues"))
WRITE_RISK = re.compile(r"(?m)^\s*(?:contents|id-token|packages|actions|"
                        r"pull-requests|issues|deployments):\s*write\b|"
                        r"^\s*permissions:\s*write-all\b", re.I)
DYNAMIC = re.compile(r"\$\{\{|\b(?:!include|!import)\b|"
                     r"^\s*(?:<<:|\S+:?\s*[&*][A-Za-z0-9_-]+)", re.M)
DANGEROUS = re.compile(r"\b(?:deploy|publish|release|upload-release-asset|"
                       r"docker\s+push|npm\s+publish|gh\s+release)\b", re.I)
USE = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*([^#\r\n]+)")
LOCAL = re.compile(r"^\./\.github/workflows/([A-Za-z0-9_.-]+\.ya?ml)$")
JOB = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):\s*(?:#.*)?$")
EVENT = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)")
GLOBAL_STEP = re.compile(r"(?m)^\s+(?:-\s*)?run:\s*(?:npm run check|"
                         r"python -m unittest discover)\s*$")
SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
PATH = re.compile(r"^[A-Za-z0-9_./-]+$")


def _sha_report(report: dict) -> str:
    data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b"CORA:workflow-rationalization:1\n" + data).hexdigest()


def _tree(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    raw = git(repo, "ls-tree", "-rz", "--full-tree", commit,
              max_output=16 * 1024 * 1024)
    listing = {}
    for row in raw.split(b"\0"):
        if not row:
            continue
        head, name = row.split(b"\t", 1)
        mode, typ, oid = head.decode("ascii").split(" ")
        path = name.decode("utf-8")
        if path in listing:
            raise ValueError("duplicate tree path")
        listing[path] = (mode, oid if typ == "blob" else "")
    return listing


def _source(repo: Path, revision: str) -> tuple[str, dict[str, tuple[str, str]]]:
    if not revision or revision.startswith("-") or "\0" in revision:
        raise ValueError("invalid revision")
    commit = git(repo, "rev-parse", "--verify", "--end-of-options",
                 revision + "^{commit}", max_output=128).decode("ascii").strip()
    if not SHA.fullmatch(commit):
        raise ValueError("invalid resolved commit")
    return commit, _tree(repo, commit)


def _read(repo: Path, entries: dict[str, tuple[str, str]],
          paths: list[str], *, strict: bool = True) -> tuple[dict[str, str], list[str]]:
    eligible: dict[str, str] = {}
    omitted: list[str] = []
    for path in paths:
        mode, oid = entries[path]
        if mode not in ("100644", "100755") or not SHA.fullmatch(oid):
            omitted.append(path)
        else:
            eligible[path] = oid
    ids = sorted(set(eligible.values()))
    sizes = _sizes(repo, ids)
    limited = {}
    total = 0
    for path, oid in sorted(eligible.items()):
        n = sizes[oid]
        if n > MAX_FILE or total + n > MAX_SOURCE_BYTES:
            omitted.append(path)
        else:
            limited[path] = oid
            total += n
    if strict and omitted:
        raise ValueError("unreadable workflow source: " + ",".join(sorted(omitted)[:4]))
    read_ids = sorted(set(limited.values()))
    data = _read_objects(repo, read_ids, sizes)
    texts = {}
    for path, oid in limited.items():
        try:
            texts[path] = data[oid].decode("utf-8")
        except UnicodeDecodeError:
            if strict:
                raise ValueError("non-UTF8 workflow source")
            omitted.append(path)
    return texts, sorted(omitted)


def _parse(text: str) -> dict:
    """Never present this restricted YAML lexer as a complete YAML parser."""
    events: set[str] = set()
    jobs: set[str] = set()
    in_events = False
    in_jobs = False
    ambiguous = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("on:"):
            in_events, in_jobs = True, False
            scalar = line[3:].split("#", 1)[0].strip()
            if scalar.startswith("[") and scalar.endswith("]"):
                events.update(z.strip(" '\"") for z in scalar[1:-1].split(",") if z.strip())
            elif scalar:
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", scalar):
                    events.add(scalar)
                else:
                    ambiguous = True
            continue
        if line.startswith("jobs:"):
            in_events, in_jobs = False, True
            continue
        if line and not line[0].isspace():
            in_events = in_jobs = False
            if line.startswith(("\"on\":", "'on':")):
                ambiguous = True
        if in_events:
            found = EVENT.match(line)
            if found:
                events.add(found.group(1))
            elif line.startswith("  - "):
                ambiguous = True
        if in_jobs:
            found = JOB.match(line)
            if found:
                jobs.add(found.group(1))
    uses = sorted({x.strip().strip("'\"") for x in USE.findall(text)})
    local = sorted({PREFIX + m.group(1) for used in uses
                    if (m := LOCAL.fullmatch(used))})
    hazard: set[str] = set()
    if WRITE_RISK.search(text):
        hazard.add("WRITE_OR_OIDC_PERMISSION")
    if "pull_request_target" in events:
        hazard.add("PR_TARGET_PRIVILEGE")
    if DANGEROUS.search(text):
        hazard.add("POSSIBLE_RELEASE_OR_DEPLOYMENT")
    if re.search(r"\bsecrets[.[]", text, re.I):
        hazard.add("POSSIBLE_SECRETS_ACCESS")
    if re.search(r"(?m)^\s*environment:\s*\S+", text):
        hazard.add("ENVIRONMENT_BOUND")
    if DYNAMIC.search(text):
        hazard.add("DYNAMIC_EXPRESSION_OR_YAML_COMPLEXITY")
    if not events or not jobs or events - EVENTS or ambiguous:
        hazard.add("PARTIAL_YAML_PARSE")
    if "workflow_call" in events:
        hazard.add("REUSABLE_WORKFLOW_ENTRY")
    if "workflow_dispatch" in events or "schedule" in events:
        hazard.add("MANUAL_OR_SCHEDULED_ENTRY")
    remote = sorted(x for x in uses if ".github/workflows/" in x and
                    not LOCAL.fullmatch(x))
    if remote:
        hazard.add("EXTERNAL_REUSABLE_WORKFLOW_REFERENCE")
    return {"events": sorted(events), "jobs": sorted(jobs),
            "uses": uses, "local_workflow_calls": local,
            "external_workflow_calls": remote, "flags": sorted(hazard),
            "shared_global_checks": len(GLOBAL_STEP.findall(text)),
            "parse_scope": "LEXICAL_PARTIAL_NEEDS_ACTIONLINT_OR_YAML_ORACLE"}


def audit_workflows(repo: Path, revision: str = "HEAD",
                    base: str | None = None) -> dict:
    repo = repo.resolve(strict=True)
    commit, entries = _source(repo, revision)
    workflows = sorted(p for p in entries if p.startswith(PREFIX) and p.endswith(SUFFIX))
    if len(workflows) > MAX_WORKFLOWS:
        raise ValueError("workflow count budget exceeded")
    wf_text, _ = _read(repo, entries, workflows)
    candidate = sorted(p for p in entries if not p.startswith(PREFIX) and
                       p.endswith(TEXT_SUFFIX))
    incomplete = False
    if len(candidate) > MAX_SCAN_PATHS:
        candidate = candidate[:MAX_SCAN_PATHS]
        incomplete = True
    other, omitted = _read(repo, entries, candidate, strict=False)
    incomplete = incomplete or bool(omitted)
    parsed = {p: _parse(wf_text[p]) for p in workflows}
    inbound = {p: [] for p in workflows}
    for caller, details in parsed.items():
        for callee in details["local_workflow_calls"]:
            if callee in inbound:
                inbound[callee].append(caller)
    source_refs = {p: [] for p in workflows}
    for path, text in other.items():
        for target in workflows:
            if target in text:
                source_refs[target].append(path)
    duplicates: dict[str, list[str]] = {}
    for path in workflows:
        oid = entries[path][1]
        duplicates.setdefault(oid, []).append(path)
    signatures = {}
    for path in workflows:
        signatures[path] = entries[path][1]
    items = []
    for path in workflows:
        details = parsed[path]
        refs = sorted(set(inbound[path] + source_refs[path]))
        dupe = sorted(duplicates[signatures[path]])
        protected = bool(details["flags"] or refs or incomplete)
        if len(dupe) > 1 and not protected:
            disposition = "REVIEW_CONSOLIDATION_CANDIDATE"
        elif details["flags"] or refs:
            disposition = "RETAIN_UNTIL_CONSUMER_REVIEW"
        elif details["shared_global_checks"]:
            disposition = "REVIEW_ADJUST_DUPLICATED_GLOBAL_CHECK"
        else:
            disposition = "INVESTIGATE_POTENTIAL_REDUNDANCY"
        blockers = ["EXTERNAL_CALLERS_AND_REQUIRED_CHECKS_UNKNOWN",
                    "NO_INDEPENDENT_RUN_COMPARISON",
                    "NO_AUTHENTICATED_NONAUTHOR_APPROVAL"]
        if incomplete:
            blockers.append("INCOMPLETE_STATIC_CONSUMER_SCAN")
        if details["flags"]:
            blockers.append("WORKFLOW_RISK_OR_PARSER_UNCERTAINTY")
        if refs:
            blockers.append("OBSERVED_STATIC_REFERENCES")
        items.append({"path": path, "git_oid": entries[path][1],
                      **details, "in_repo_callers": sorted(inbound[path]),
                      "other_literal_references": sorted(source_refs[path]),
                      "exact_content_duplicates": dupe if len(dupe) > 1 else [],
                      "disposition": disposition, "retirement_authorized": False,
                      "blockers": blockers,
                      "proposed_effect": "READ_ONLY_PLAN_NOT_APPLIED"})
    changes = []
    if base is not None:
        base_commit, old = _source(repo, base)
        for path in sorted(set(p for p in old if p.startswith(PREFIX) and p.endswith(SUFFIX)) |
                           set(workflows)):
            before, after = old.get(path), entries.get(path)
            if before == after:
                continue
            op = "ADD" if before is None else "REMOVE" if after is None else "MODIFY"
            changes.append({"path": path, "operation": op,
                            "base_oid": before[1] if before else None,
                            "head_oid": after[1] if after else None,
                            "governance": "BLOCKED_EXTERNAL",
                            "retirement_authorized": False})
    else:
        base_commit = None
    report = {"schema": SCHEMA, "commit": commit, "base_commit": base_commit,
              "workflow_count": len(items), "workflows": items,
              "changes": changes, "source_scan_complete": not incomplete,
              "unreadable_consumer_files": omitted[:100],
              "source_scope": "GIT_BLOBS_PARTIAL_YAML_AND_STATIC_LITERAL_REFERENCES",
              "source_status": "PASS_SCOPED_SOURCE" if not incomplete else "DEBT_BLOCKED_SOURCE_SCAN",
              "required_checks": "UNKNOWN_GITHUB_HOST",
              "external_consumers": "UNKNOWN_EXTERNAL_REPOS",
              "behavioral_equivalence": "NOT_TESTED",
              "deletion_or_edit_effect": "NONE",
              "governed_status": "BLOCKED_EXTERNAL",
              "authorization": "NONE"}
    report["receipt_sha256"] = _sha_report(report)
    return report


def verify_workflows(repo: Path, report: dict) -> None:
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError("invalid workflow report")
    rebuilt = audit_workflows(repo, report["commit"], base=report["base_commit"])
    if rebuilt != report:
        raise ValueError("workflow Git-revision replay mismatch")
