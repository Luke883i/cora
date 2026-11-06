"""Repeatable, adversarial *finite-model* CORA one-run execution-vector tests.

100,000 distinct, pre-seeded semantic input vectors across 32 families:
two valid controls and thirty realistic falsifications. These are not
100,000 physical source mutations, measured target defects, or independent
proofs of browser usability. The verifier is shared with live one-run rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .one_run import METHOD_FILES, validate_execution_rows

SCHEMA = "cora-one-run-stress/1"
SEED = 883
FAMILIES = (
    "POSITIVE_DIRECT_RECORDED", "POSITIVE_REUSED_UNTIMED",
    "UNSUPPORTED_PASS", "APPROVAL_SPOOF", "EXTERNAL_PROOF_SPOOF",
    "CROSS_COMMIT_VALID_SHA", "UNKNOWN_METHOD", "WRONG_METHOD_SOURCE",
    "MISSING_METHOD_ID", "FALSE_EXECUTED_REASON", "SOURCE_STATUS_MISMATCH",
    "RUNTIME_FAIL_AS_SOURCE_PASS", "NEGATIVE_ELAPSED", "ELAPSED_STRING",
    "UNBOUNDED_ELAPSED", "REUSED_MARKED_AS_DIRECT", "REUSED_WITH_FALSE_TIME",
    "NOT_RUN_WITH_FAKE_TIME", "NOT_RUN_WITH_SOURCE_DIGEST",
    "BLOCKED_WITHOUT_REASON", "MISSING_DIGEST_KEY", "EXTRA_APPROVAL_FLAG",
    "INVALID_SOURCE_DIGEST", "XSS_SOURCE_DIGEST", "XSS_SOURCE_PATH",
    "XSS_GIT_COMMIT", "UNSUPPORTED_PROOF_LABEL", "BOOLEAN_AUTHORITY",
    "UNSUPPORTED_TIMING", "NULL_METHOD_ID", "DUPLICATE_METHOD_ENTRY",
    "RUN_STATE_INCONSISTENT",
)


def _seed_row(i: int, seed: int, variant: str = "direct") -> dict:
    # Every input differs semantically by measured elapsed time and independent
    # fake-source digest; no duplicate vector counted as distinct by a counter.
    names = list(METHOD_FILES)
    name = names[(i + seed) % len(names)]
    digest = hashlib.sha256(f"CORA:model-seed:{seed}:{i}".encode("ascii")).hexdigest()
    row = {
        "id": name, "state": "EXECUTED_SCOPED",
        "source_state": "EXECUTED_SCOPED",
        "source": METHOD_FILES[name],
        "commit": "a" * 40, "source_digest": digest,
        "reason": None, "elapsed_ms": i,
        "timing_basis": "DIRECT_METHOD_EXECUTION",
        "proof_scope": "GIT_SOURCE_METHOD_NOT_PRODUCT_BEHAVIOR",
        "authority": "NONE",
    }
    if variant == "reuse":
        row.update(state="REUSED_SCOPED",
                   source_state="REUSED_SCOPED_FROM_HOLISTIC",
                   elapsed_ms=None, timing_basis="REUSED_NOT_INDEPENDENTLY_TIMED")
    elif variant == "skip":
        row.update(id="file_selection_if_focus", source=METHOD_FILES["file_selection_if_focus"],
                   state="NOT_RUN", source_state="NOT_RUN_REQUIRES_FOCUS",
                   elapsed_ms=None, source_digest=None, timing_basis="NOT_INVOKED")
    elif variant == "blocked":
        row.update(state="BLOCKED", source_state="DEBT_BLOCKED", reason="ValueError")
    return row


def vector(i: int, seed: int) -> tuple[str, list[dict], bool]:
    """Adversary generator is independent of verifier logic and its oracle."""
    if type(i) is not int or i < 0 or type(seed) is not int or seed < 0:
        raise ValueError("invalid deterministic vector coordinates")
    fam = i % len(FAMILIES)
    tag = FAMILIES[fam]
    v = _seed_row(i, seed, variant=(
        "reuse" if fam in (1, 15, 16)
        else "skip" if fam in (17, 18)
        else "blocked" if fam == 19 else "direct"))
    if fam == 2:
        v["state"] = "PASS"
    elif fam == 3:
        v["authority"] = "APPROVED_BY_CORA"
    elif fam == 4:
        v["proof_scope"] = "INDEPENDENT_RUNTIME_PROOF"
    elif fam == 5:
        v["commit"] = "b" * 40
    elif fam == 6:
        v["id"] = "remote_code_execution"
    elif fam == 7:
        v["source"] = "src/cora/another_module.py"
    elif fam == 8:
        v.pop("id")
    elif fam == 9:
        v["reason"] = "QUIETLY_IGNORED"
    elif fam == 10:
        v["source_state"] = "DEBT_BLOCKED"
    elif fam == 11:
        v["state"] = "FAIL"
    elif fam == 12:
        v["elapsed_ms"] = -i - 1
    elif fam == 13:
        v["elapsed_ms"] = str(i)
    elif fam == 14:
        v["elapsed_ms"] = 3_600_001 + i
    elif fam == 15:
        v["timing_basis"] = "DIRECT_METHOD_EXECUTION"
    elif fam == 16:
        v["elapsed_ms"] = i
    elif fam == 17:
        v["elapsed_ms"] = i
    elif fam == 18:
        v["source_digest"] = hashlib.sha256(b"false-source").hexdigest()
    elif fam == 19:
        v["reason"] = ""
    elif fam == 20:
        v.pop("source_digest")
    elif fam == 21:
        v["external_approval"] = True
    elif fam == 22:
        v["source_digest"] = "sha256:000"
    elif fam == 23:
        v["source_digest"] = '<script>alert("CORA")</script>'
    elif fam == 24:
        v["source"] = "<img src=x onerror=alert(1)>"
    elif fam == 25:
        v["commit"] = "</code><script>alert(1)</script>"
    elif fam == 26:
        v["proof_scope"] = "CERTIFIED_BEHAVIOR"
    elif fam == 27:
        v["authority"] = True
    elif fam == 28:
        v["timing_basis"] = "NOT_GOVERNED_BUT_PASSED"
    elif fam == 29:
        v["id"] = None
    elif fam == 30:
        return tag, [v, dict(v)], False
    elif fam == 31:
        v["source_state"] = "NOT_RUN_REQUIRES_FOCUS"
    return tag, [v], fam < 2


def stress_one_run(cases: int = 100000, *, seed: int = SEED) -> dict:
    if (type(cases) is not int or not 1 <= cases <= 100000
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("bounded pre-seeded finite-model campaign required")
    successes = negatives = disagreements = promotions = 0
    counts = {x: 0 for x in FAMILIES}
    digests = set()
    rolling = hashlib.sha256()
    survivors = []
    for i in range(cases):
        family, rows, expected_valid = vector(i, seed)
        payload = json.dumps(rows, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("ascii")).hexdigest()
        # Independently reject repeated identical test inputs.
        if digest in digests:
            raise ValueError("duplicate adversarial fixture counted twice")
        digests.add(digest)
        rolling.update(digest.encode("ascii"))
        counts[family] += 1
        accepted = True
        try:
            validate_execution_rows(rows, expected_commit="a" * 40)
        except (ValueError, KeyError, TypeError):
            accepted = False
        if expected_valid:
            successes += 1
        else:
            negatives += 1
            if accepted:
                promotions += 1
                if len(survivors) < 20:
                    survivors.append({"family": family, "input_fingerprint": digest})
        if accepted != expected_valid:
            disagreements += 1
    result = {
        "schema": SCHEMA, "seed": seed, "cases": cases,
        "families": len(FAMILIES), "family_counts": counts,
        "positive_controls": successes, "negative_scenarios": negatives,
        "distinct_input_fingerprints": len(digests),
        "oracle_disagreements": disagreements,
        "unauthorized_promotions": promotions,
        "survivors": survivors, "case_digest": rolling.hexdigest(),
        "physical_source_mutants": 0,
        "external": "BLOCKED_EXTERNAL", "authority": "NONE",
        "scope": "PRESEEDED_SEMANTIC_RECEIPT_MUTATIONS_NOT_PHYSICAL_GIT_MUTATIONS",
        "status": ("PASS_SCOPED_PRESEEDED_FINITE_MODEL" if not disagreements and
                   not promotions else "REFUTED"),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded pre-seeded one-run receipt falsification")
    parser.add_argument("--cases", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = stress_one_run(args.cases, seed=args.seed)
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "PASS_SCOPED_PRESEEDED_FINITE_MODEL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
