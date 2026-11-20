"""PR90 preregistered semantic scenario stream: 12 interacting dimensions.

These are finite model states, not 1M independently executed Git mutations or
user trials. A separate rule-based oracle challenges each modeled decision.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import gcd, prod
from pathlib import Path

FIELDS = (
    ("persona", ("beginner", "maintainer", "reviewer", "cto", "auditor")),
    ("mode", ("chat-method", "local-engine")),
    ("target", ("issue-webapp", "payment-api", "health-triage", "student-portal",
                "sensor-pipeline", "supplier-onboarding")),
    ("revision", ("exact-git", "stale-git", "source-zip-only", "unknown")),
    ("evidence", ("no-receipt", "caller-claim", "git-replay", "target-native")),
    ("runner", ("none", "read-only", "separate-authorized", "untrusted")),
    ("cockpit", ("missing", "verified-zip", "stale-zip", "forged-zip")),
    ("action", ("explain", "replan", "next-check", "auto-merge")),
    ("dod", ("unresolved", "source-reported", "refuted", "external-open")),
    ("host", ("unknown", "self-claimed", "independently-observed")),
    ("rollback", ("unplanned", "documented", "native-tested")),
    ("impact", ("low", "financial", "privacy", "safety", "availability")),
)
SPACE = prod(len(values) for _, values in FIELDS)
STRIDE = 104729
SCHEMA = "cora-pr90-finite-release-scenarios/1"
assert gcd(STRIDE, SPACE) == 1 and SPACE > 1_000_000


def case_at(index: int, seed: int = 883) -> dict:
    """A seeded permutation of distinct semantic tuples, not a nonce-only test."""
    n = (index * STRIDE + seed) % SPACE
    item = {}
    for name, choices in FIELDS:
        n, offset = divmod(n, len(choices))
        item[name] = choices[offset]
    return item


def candidate(case: dict) -> dict:
    """The scoped release/navigation policy under stress."""
    exact = case["revision"] == "exact-git"
    observed = case["evidence"] in ("git-replay", "target-native")
    runner = case["runner"] == "separate-authorized"
    source = "PASS_SCOPED_SOURCE" if exact and observed and runner else (
        "METHOD_ONLY" if case["mode"] == "chat-method" else "NOT_RUN")
    navigation = ("VERIFIED_OFFLINE_NAVIGATOR"
                  if source == "PASS_SCOPED_SOURCE" and
                  case["mode"] == "chat-method" and
                  case["cockpit"] == "verified-zip"
                  else "NO_VERIFIED_NAVIGATOR")
    choice = ("NONEXECUTING_CHOICE" if case["action"] != "auto-merge"
              and case["dod"] != "refuted" else "BLOCKED")
    return {"source": source, "navigation": navigation, "choice": choice,
            "release": "BLOCKED_EXTERNAL", "authorization": "NONE",
            "auto_execution": False, "time_estimate": None}


def independent_oracle(case: dict) -> dict:
    """Independently expressed truth table, no call into the candidate rule."""
    allowed_source = (
        case.get("revision") == "exact-git"
        and case.get("runner") == "separate-authorized"
        and case.get("evidence") not in ("no-receipt", "caller-claim"))
    if allowed_source:
        source_state = "PASS_SCOPED_SOURCE"
    elif case.get("mode") == "local-engine":
        source_state = "NOT_RUN"
    else:
        source_state = "METHOD_ONLY"
    if (allowed_source and case.get("mode") != "local-engine"
            and case.get("cockpit") == "verified-zip"):
        nav_state = "VERIFIED_OFFLINE_NAVIGATOR"
    else:
        nav_state = "NO_VERIFIED_NAVIGATOR"
    if case.get("action") in ("explain", "replan", "next-check") and case.get("dod") != "refuted":
        choice_state = "NONEXECUTING_CHOICE"
    else:
        choice_state = "BLOCKED"
    return dict(source=source_state, navigation=nav_state, choice=choice_state,
                release="BLOCKED_EXTERNAL", authorization="NONE",
                auto_execution=False, time_estimate=None)


def run(*, cases: int = 1_000_000, seed: int = 883) -> dict:
    if not 1 <= cases <= 1_000_000 or type(seed) is not int or seed < 0:
        raise ValueError("bounded preregistered cases [1,1000000], nonnegative integer seed")
    stream = hashlib.sha256()
    observed_ids = set()
    counts = Counter()
    examples = []
    mismatches = 0
    false_promotions = 0
    for i in range(cases):
        permutation_index = (i * STRIDE + seed) % SPACE
        if permutation_index in observed_ids:
            raise ValueError("semantic vector repeated")
        observed_ids.add(permutation_index)
        item = case_at(i, seed)
        actual = candidate(item)
        oracle = independent_oracle(item)
        if actual != oracle:
            mismatches += 1
        if (actual["release"] != "BLOCKED_EXTERNAL"
                or actual["authorization"] != "NONE" or actual["auto_execution"]):
            false_promotions += 1
        counts[actual["source"]] += 1
        counts[actual["navigation"]] += 1
        counts[actual["choice"]] += 1
        counts[item["impact"]] += 1
        # Encode all 12 interacting semantic fields and all derived decisions.
        line = json.dumps([i, item, actual], sort_keys=True, separators=(",", ":"))
        stream.update(line.encode("utf-8") + b"\n")
        if i < 8:
            examples.append({"vector": item, "decision": actual})
    # Eight distinct counterfactual result corruptions, not source-file changes.
    origin = candidate(case_at(23, seed))
    forged = (
        dict(origin, release="APPROVED"),
        dict(origin, authorization="SELF_APPROVED"),
        dict(origin, auto_execution=True),
        dict(origin, source="UNIVERSAL_PASS"),
        dict(origin, navigation="AUTONOMOUS_CHAT_PLUGIN"),
        dict(origin, choice="AUTO_MERGE"),
        dict(origin, time_estimate=0),
        dict(origin, release="AUTHORIZED_BY_CI"),
    )
    rejected_forged = sum(x != independent_oracle(case_at(23, seed)) for x in forged)
    return {
        "schema": SCHEMA, "status": "PASS_BOUNDED_FINITE_MODEL" if
        not mismatches and not false_promotions and rejected_forged == len(forged)
        else "REFUTED",
        "seed": seed, "cases": cases, "semantic_dimensions": len(FIELDS),
        "semantic_space": SPACE, "seeded_permutation_stride": STRIDE,
        "distinct_semantic_tuples_observed": len(observed_ids),
        "scenario_counts": dict(sorted(counts.items())),
        "model_oracle_mismatches": mismatches,
        "false_release_promotions": false_promotions,
        "forged_results_tested": len(forged), "forged_results_rejected": rejected_forged,
        "sha256": stream.hexdigest(), "samples": examples,
        "physical_git_mutants": 0, "independent_reader_trials": 0,
        "verified_browser_interactions": 0, "release": "BLOCKED_EXTERNAL",
        "authorization": "NONE", "no_auto_merge": True,
        "scope": "TWELVE_DIMENSION_FINITE_SCENARIO_MODEL_NOT_TARGET_OR_HOST_EXECUTION",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=883)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    report = run(cases=args.cases, seed=args.seed)
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "PASS_BOUNDED_FINITE_MODEL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
