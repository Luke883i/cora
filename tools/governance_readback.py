"""PR39 read-only GitHub host governance probe; no local release authority.

An API response is a bounded remote observation, not proof that this workflow
runs as an independent reviewer or that host controls were enforced at merge.
403/404/unavailable are BLOCKED, never permission to merge.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
URL_TEMPLATE = "https://api.github.com/repos/{repo}/branches/{branch}/protection"


def probe(repo: str, branch: str, token: str | None = None) -> dict:
    if not REPO.fullmatch(repo) or not BRANCH.fullmatch(branch):
        raise ValueError("unsafe GitHub host identity")
    report = {
        "schema": "cora-host-governance-readback/1",
        "repository": repo, "branch": branch,
        "endpoint": "/branches/{branch}/protection",
        "http_status": None,
        "observation": "BLOCKED_NO_HOST_AUTHORITY",
        "required_checks_reported": [],
        "required_reviews_reported": None,
        "host_identity_independently_verified": False,
        "host_enforcement_attested": False,
        "merge_authorized": False,
        "release_authorized": False,
        "authority": "NONE",
    }
    if token is None or not token.strip():
        report["observation"] = "BLOCKED_NO_HOST_TOKEN"
        return report
    url = URL_TEMPLATE.format(repo=repo, branch=branch)
    request = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer " + token.strip(),
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "CORA-readonly-host-governance/1",
                 "X-GitHub-Api-Version": "2022-11-28"},
        method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            status = response.status
            body = response.read(128_001)
        if len(body) > 128_000:
            report["observation"] = "BLOCKED_OVERSIZED_HOST_RESPONSE"
            return report
    except urllib.error.HTTPError as err:
        report["http_status"] = int(err.code)
        report["observation"] = ("BLOCKED_NO_HOST_PERMISSION" if err.code == 403 else
                                  "BLOCKED_NOT_FOUND_OR_UNPROTECTED" if err.code == 404 else
                                  "BLOCKED_HOST_HTTP_ERROR")
        return report
    except (urllib.error.URLError, TimeoutError, OSError):
        report["observation"] = "BLOCKED_HOST_UNAVAILABLE"
        return report
    report["http_status"] = status
    if status != 200:
        report["observation"] = "BLOCKED_HOST_HTTP_ERROR"
        return report
    try:
        doc = json.loads(body.decode("utf-8"))
        required = doc.get("required_status_checks") or {}
        observed_checks = [x.get("context", "") for x in required.get("checks", [])]
        observed_checks += required.get("contexts", [])
        reviews = doc.get("required_pull_request_reviews")
        count = (reviews.get("required_approving_review_count")
                 if isinstance(reviews, dict) else None)
        if (any(not isinstance(x, str) or not x for x in observed_checks)
                or (count is not None and
                    (type(count) is not int or count < 0 or count > 100))):
            raise ValueError("incomplete host readback fields")
    except (ValueError, AttributeError, TypeError, KeyError, UnicodeError):
        report["observation"] = "BLOCKED_MALFORMED_HOST_RESPONSE"
        return report
    report["required_checks_reported"] = sorted(set(observed_checks))
    report["required_reviews_reported"] = count
    report["observation"] = ("HOST_CONFIGURATION_REPORTED_NOT_INDEPENDENTLY_ATTESTED"
                             if observed_checks and count is not None
                             else "BLOCKED_HOST_POLICY_INCOMPLETE")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only fail-closed GitHub main protection report")
    parser.add_argument("--repo", default="Luke883i/cora")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = probe(args.repo, args.branch, os.environ.get("GITHUB_TOKEN"))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
