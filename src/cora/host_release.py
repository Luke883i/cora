"""Read-only GitHub host facts for CORA release governance (not approval).

A live GitHub API reply is not proof of a human's identity, independent
authorization, signed provenance, or release fitness. No API writes.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from .git_snapshot import git
from .reticulum import assess_cut, MODEL, EXTERNAL, BLOCKED

SCHEMA = "cora-host-release-observation/1"
RELEASE_DOD = ".cora/contracts/dod/postmerge-release-dod.json"
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
RELEASE_TAG = re.compile(r"v[0-9A-Za-z.+-]+\Z")
NODES = {
    "L_EXACT_GIT_SOURCE": [],
    "L_REPEATED_CI": [],
    "L_DIAGNOSTIC_ORACLE": [],
    "L_RELEASE_CANDIDATE": [],
    "E_HOST_REQUIRED_CHECKS": [],
    "E_HOST_PROTECTED_MAIN": [],
    "E_DISTINCT_REVIEWER": [],
    "E_RELEASE_OWNER": [],
    "E_SIGNED_PROVENANCE": [],
    "E_PUBLISHED_TAG_PARITY": [],
    "E_REAL_EXTERNAL_PILOT": [],
    "E_OPERATIONAL_ROLLBACK": [],
    "G_REPRO_SOURCE": ["L_EXACT_GIT_SOURCE", "L_REPEATED_CI", "L_DIAGNOSTIC_ORACLE", "L_RELEASE_CANDIDATE"],
    "G_GOVERNED_HOST": ["E_HOST_REQUIRED_CHECKS", "E_HOST_PROTECTED_MAIN", "E_DISTINCT_REVIEWER"],
    "G_RELEASE_ACCEPTANCE": ["E_RELEASE_OWNER", "E_SIGNED_PROVENANCE", "E_PUBLISHED_TAG_PARITY", "E_REAL_EXTERNAL_PILOT", "E_OPERATIONAL_ROLLBACK"],
    "G_POSTMERGE_RELEASE": ["G_REPRO_SOURCE", "G_GOVERNED_HOST", "G_RELEASE_ACCEPTANCE"],
}
SOURCE_LEAVES = {x for x in NODES if x.startswith("L_")}
EXTERNAL_LEAVES = {x for x in NODES if x.startswith("E_")}


def _read_api(url: str, token: str) -> dict | list | None:
    """Never emit token or raw response; 403/404 are typed unknown/missing."""
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CORA-source-bound-governance-probe",
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as stream:
            content = stream.read(1024 * 1024 + 1)
            if len(content) > 1024 * 1024:
                raise ValueError("GitHub API response over bounded size")
            return json.loads(content)
    except urllib.error.HTTPError as error:
        if error.code in (403, 404):
            return {"_observation_http": error.code}
        raise


def _assert_valid(contract: dict, tree: set[str]) -> dict:
    if (contract.get("schema") != "cora-postmerge-release-dod/1"
            or contract.get("authority") != "NONE"
            or contract.get("global_goal") != "G_POSTMERGE_RELEASE"):
        raise ValueError("release DoD identity or authority drift")
    nodes = contract.get("nodes", [])
    if (len(nodes) != len(NODES) or len({x["id"] for x in nodes}) != len(nodes)
            or {x["id"] for x in nodes} != set(NODES)):
        raise ValueError("release DoD node lattice drift")
    observations = {}
    for node in nodes:
        key = node["id"]
        if (node.get("depends_on") != NODES[key]
                or node.get("scope") != ("SOURCE" if key.startswith(("L_", "G_REPRO_")) else "EXTERNAL")):
            raise ValueError("release DoD mandatory edge/scope drift")
        if key in EXTERNAL_LEAVES and node.get("witness_paths"):
            raise ValueError("external reviewer or host cannot use source witnesses")
        if key in SOURCE_LEAVES:
            paths = node.get("witness_paths")
            if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p in tree for p in paths):
                observations[key] = BLOCKED
            else:
                observations[key] = MODEL
    result = assess_cut(nodes, "G_POSTMERGE_RELEASE", observations)
    if (result["status"] != EXTERNAL or
            result["states"]["G_GOVERNED_HOST"] != EXTERNAL or
            result["states"]["G_RELEASE_ACCEPTANCE"] != EXTERNAL):
        raise ValueError("release status illegally elevated")
    return result


def original_git_dod(repo: Path, revision: str = "HEAD") -> tuple[str, dict]:
    """Bind the maturity extension to immutable Git source, not worktree JSON."""
    repo = Path(repo).resolve(strict=True)
    commit = git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode("ascii").strip()
    raw = git(repo, "show", commit + ":" + RELEASE_DOD, max_output=128 * 1024)
    contract = json.loads(raw)
    tree_raw = git(repo, "ls-tree", "-r", "--name-only", "-z", commit, max_output=10 * 1024 * 1024)
    paths = set(p.decode("utf-8") for p in tree_raw.split(b"\0") if p)
    return commit, _assert_valid(contract, paths)


def classify_host_snapshot(branch: dict, rulesets: dict | list,
                           release: dict, *, revision: str, repository: str,
                           tag: str, pr: dict | None = None,
                           reviews: list | None = None) -> dict:
    """Evaluate observed facts without treating an API response as a human veto."""
    if (not REPO.fullmatch(repository) or not SHA.fullmatch(revision)
            or not RELEASE_TAG.fullmatch(tag)
            or not isinstance(branch, dict) or not isinstance(rulesets, (dict, list))
            or not isinstance(release, dict)):
        raise ValueError("untrusted GitHub observation shape")
    if (branch.get("name") != "main"
            or not isinstance(branch.get("commit"), dict)
            or not SHA.fullmatch(str(branch["commit"].get("sha", "")))):
        raise ValueError("main branch identity unknown")
    enforcement = branch.get("protection", {}).get("required_status_checks", {})
    if not isinstance(enforcement, dict):
        enforcement = {}
    checks = enforcement.get("checks")
    contexts = enforcement.get("contexts")
    required = list(checks or []) + list(contexts or [])
    checked = (branch.get("protected") is True
               and enforcement.get("enforcement_level") not in (None, "off")
               and len(required) > 0)
    if isinstance(rulesets, list):
        ruleset_status = "API_LIST_OBSERVED_NOT_ENFORCEMENT_PROOF"
    else:
        ruleset_status = "API_FORBIDDEN" if rulesets.get("_observation_http") == 403 else "UNKNOWN"
    if release.get("_observation_http") == 404:
        publication = "TAG_RELEASE_NOT_PUBLISHED"
    elif release.get("_observation_http") == 403:
        publication = "RELEASE_API_FORBIDDEN"
    else:
        publication = ("DRAFT_RELEASE" if release.get("draft") is True
                       else "PUBLISHED_REQUIRES_TAG_ASSET_AND_OWNER_ATTESTATION"
                       if release.get("tag_name") == tag else "RELEASE_IDENTITY_UNKNOWN")
    distinct = []
    if pr is not None or reviews is not None:
        if not isinstance(pr, dict) or not isinstance(reviews, list):
            raise ValueError("PR and review facts must be supplied together")
        author = (pr.get("user") or {}).get("login")
        expected_head = (pr.get("head") or {}).get("sha")
        if not isinstance(author, str) or not SHA.fullmatch(str(expected_head)):
            raise ValueError("review subject not attributable")
        # Count only the latest GitHub state for each distinct non-author account.
        latest = {}
        for review in reviews:
            if not isinstance(review, dict):
                raise ValueError("invalid GitHub review")
            login = (review.get("user") or {}).get("login")
            if isinstance(login, str) and login != author:
                rid = review.get("id")
                if type(rid) is int and (login not in latest or latest[login]["id"] < rid):
                    latest[login] = review
        distinct = sorted(login for login, review in latest.items()
                          if review.get("state") == "APPROVED"
                          and review.get("commit_id") == expected_head)
    blockers = []
    if branch.get("protected") is not True:
        blockers.append("MAIN_NOT_PROTECTED_OBSERVED")
    if not checked:
        blockers.append("REQUIRED_CI_NOT_OBSERVED_AS_ENFORCED")
    if not distinct:
        blockers.append("NONAUTHOR_HEAD_APPROVAL_NOT_OBSERVED")
    if publication != "PUBLISHED_REQUIRES_TAG_ASSET_AND_OWNER_ATTESTATION":
        blockers.append(publication)
    # These obligations are not authenticated by read-only GitHub branch and
    # release endpoints, even if the host has enabled required status checks.
    blockers.extend(["HUMAN_RELEASE_OWNER_NOT_AUTHENTICATED",
                     "SIGNED_ARTIFACT_PROVENANCE_NOT_ATTESTED",
                     "EXTERNAL_PILOT_NOT_ATTESTED",
                     "OPERATIONAL_ROLLBACK_NOT_ATTESTED"])
    return {
        "schema": SCHEMA, "repository": repository, "revision": revision,
        "observed_main_head": branch["commit"]["sha"],
        "revision_is_main_head": branch["commit"]["sha"] == revision,
        "tag": tag, "branch_protected": branch.get("protected") is True,
        "required_checks_enforced_observed": checked,
        "required_check_count": len(required),
        "rulesets_status": ruleset_status, "release_observation": publication,
        "distinct_non_author_head_approver_accounts": distinct,
        "blockers": sorted(set(blockers)),
        "external_gate": "BLOCKED_EXTERNAL",
        "publication_authorized": False, "authorization": "NONE",
        "provenance": "AUTHENTICATED_READ_ONLY_GITHUB_API_RESPONSE_UNVALIDATED_BY_INDEPENDENT_HUMAN",
    }


def observe_github(repository: str, revision: str, token: str,
                   *, tag: str = "v1.0.0a4", pr_number: int | None = None,
                   fetcher=_read_api) -> dict:
    if (not isinstance(token, str) or len(token) < 1 or
            not REPO.fullmatch(repository) or not SHA.fullmatch(revision)
            or not RELEASE_TAG.fullmatch(tag) or
            (pr_number is not None and (type(pr_number) is not int or pr_number < 1))):
        raise ValueError("GitHub read-only observation prerequisites not met")
    url = "https://api.github.com/repos/" + repository
    branch = fetcher(url + "/branches/main", token)
    rules = fetcher(url + "/rulesets", token)
    release = fetcher(url + "/releases/tags/" + tag, token)
    pr = reviews = None
    if pr_number is not None:
        pr = fetcher(url + "/pulls/" + str(pr_number), token)
        reviews = fetcher(url + "/pulls/" + str(pr_number) + "/reviews?per_page=100", token)
        if not isinstance(reviews, list) or len(reviews) == 100:
            raise ValueError("review list unavailable or truncated")
    return classify_host_snapshot(branch, rules, release, revision=revision,
                                  repository=repository, tag=tag,
                                  pr=pr, reviews=reviews)


def verify_expected_boundary(report: dict) -> None:
    if (report.get("schema") != SCHEMA or report.get("authorization") != "NONE"
            or report.get("external_gate") != "BLOCKED_EXTERNAL"
            or report.get("publication_authorized") is not False
            or report.get("provenance") !=
            "AUTHENTICATED_READ_ONLY_GITHUB_API_RESPONSE_UNVALIDATED_BY_INDEPENDENT_HUMAN"):
        raise ValueError("host observation promoted into release authority")
