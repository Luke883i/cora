"""Preseeded semantic fault simulation, independent finite oracle and novelty boundary.

A scenario applies typed faults to a *model* of a coding-agent delivery. Ten
million scenario calls do not imply ten million physical source mutations, real
LLM responses, repository executions or independent quality measurements.
"""
from __future__ import annotations

import hashlib

from .agent_assurance import FAMILIES, LOCAL_IDS, load_contract

MASK64 = (1 << 64) - 1
SOURCE_MASK = (1 << 18) - 1
EXTERNAL_MASK = ((1 << 24) - 1) ^ SOURCE_MASK
GROUP_MASKS = (
    (1 << 6) - 1,
    ((1 << 12) - 1) ^ ((1 << 6) - 1),
    ((1 << 18) - 1) ^ ((1 << 12) - 1),
)
PAIRS = tuple((i, j) for i in range(24) for j in range(i + 1, 24))
MODEL_LABEL = "MODEL_ELIGIBLE_UNATTESTED"
BLOCKED_LABEL = "BLOCKED"
SCHEMA = "cora-agent-saturation/1"


def _mix64(value: int) -> int:
    value = (value + 0x9e3779b97f4a7c15) & MASK64
    value = ((value ^ (value >> 30)) * 0xbf58476d1ce4e5b9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94d049bb133111eb) & MASK64
    return value ^ (value >> 31)


def _scenario(i: int, seed: int) -> int:
    if i < 24:
        return 1 << i
    if i < 300:
        a, b = PAIRS[i - 24]
        return (1 << a) | (1 << b)
    if i == 300:
        return 0  # A clean model is still not an authenticated release.
    if 301 <= i < 307:
        return 1 << (18 + i - 301)  # External-only blockers are not source failures.
    v = _mix64(seed + (i * 0x9e3779b97f4a7c15))
    a, b, c = (v >> 9) % 24, (v >> 27) % 24, (v >> 45) % 24
    mask = 1 << a
    if v & 1:
        mask |= 1 << b
    if v & 2:
        mask |= 1 << c
    return mask


def _implementation(mask: int) -> tuple[str, str]:
    """Model follows the explicit LOCAL -> INTERMEDIATE -> GLOBAL AND structure."""
    if type(mask) is not int or mask < 0 or mask >= (1 << 24):
        raise ValueError("out-of-ontology scenario")
    local_ok = not (mask & GROUP_MASKS[0])
    intermediate_ok = not (mask & GROUP_MASKS[1])
    global_ok = not (mask & GROUP_MASKS[2])
    source = MODEL_LABEL if (local_ok and intermediate_ok and global_ok) else BLOCKED_LABEL
    # Neither caller claims nor simulated absence of faults certify external review.
    return source, "BLOCKED_EXTERNAL"


def _reference_oracle(mask: int) -> tuple[bool, bool]:
    """Separately stated finite bit-spec: all first 18 local faults absent.

    There is intentionally no Boolean path to governed GO in synthetic fixtures.
    """
    if mask < 0 or mask >= (1 << len(FAMILIES)):
        raise ValueError("not a known semantic fault shape")
    candidate_source = (mask % (1 << 18)) == 0
    return candidate_source, False


def saturate_agent_dod(contract: dict, *, sessions: int = 10,
                       cases_per_session: int = 1_000_000) -> dict:
    if (type(sessions) is not int or type(cases_per_session) is not int or
        not 1 <= sessions <= 10 or not 307 <= cases_per_session <= 1_000_000):
        raise ValueError("bounded sessions/cases required")
    seeds = contract["seeds"][:sessions]
    rows = []
    aggregate = hashlib.sha256()
    overall_mismatches = 0
    overall_unsafe = 0
    for session, seed in enumerate(seeds):
        stream = hashlib.sha256()
        unique_signatures = set()
        exposures = set()
        observed_pairs = set()
        mismatches = unsafe = source_eligible = 0
        novelty_tail = 0
        preregistered_mismatches = 0
        # Four finite semantic layers: LOCAL/INTERMEDIATE/GLOBAL/EXTERNAL.
        exposed_levels = set()
        for i in range(cases_per_session):
            mask = _scenario(i, seed)
            actual_source, actual_governed = _implementation(mask)
            expected_source, expected_governed = _reference_oracle(mask)
            if (actual_source == MODEL_LABEL) != expected_source:
                mismatches += 1
            if actual_governed != "BLOCKED_EXTERNAL" or expected_governed:
                unsafe += 1
            if mask & SOURCE_MASK and actual_source == MODEL_LABEL:
                unsafe += 1
            if actual_source == MODEL_LABEL:
                source_eligible += 1
            # Audit the ACTUAL generated mask, not the loop counter. The
            # historical PR17 counter incremented even if _scenario was broken.
            if i < 24:
                if mask == (1 << i):
                    exposures.add(i)
                    exposed_levels.add(("LOCAL", "INTERMEDIATE", "GLOBAL", "EXTERNAL")[i // 6])
                else:
                    preregistered_mismatches += 1
            elif i < 300:
                a, b = PAIRS[i - 24]
                if mask == ((1 << a) | (1 << b)):
                    observed_pairs.add((a, b))
                else:
                    preregistered_mismatches += 1
            elif i == 300 and mask != 0:
                preregistered_mismatches += 1
            elif 301 <= i < 307 and mask != (1 << (18 + i - 301)):
                preregistered_mismatches += 1
            if mask.bit_count() > 3:
                preregistered_mismatches += 1
            # Full normalized signature space is finite: empty, 24 singles,
            # 276 pairs, and up to 2,024 unordered triples (if all indices differ).
            if mask not in unique_signatures:
                unique_signatures.add(mask)
                if i >= cases_per_session - min(100_000, cases_per_session // 10):
                    novelty_tail += 1
            stream.update(mask.to_bytes(3, "big") + bytes((actual_source == MODEL_LABEL,)))
        # A long run must exercise richer fault mixtures beyond the
        # 301 forced empty/single/pair signatures, not just repeat them.
        diversified = len(unique_signatures) > 301
        if (len(exposures) != 24 or len(observed_pairs) != 276 or
            len(exposed_levels) != 4 or source_eligible == 0 or
            not diversified or
            (cases_per_session == 1_000_000 and len(unique_signatures) < 1_000)):
            unsafe += 1
        mismatches += preregistered_mismatches
        digest = stream.hexdigest()
        row = {
            "session": session + 1, "seed": seed,
            "cases": cases_per_session,
            "observed_single_faults": len(exposures),
            "observed_all_pairs": len(observed_pairs),
            "required_pairs": len(PAIRS),
            "covered_levels": sorted(exposed_levels),
            "distinct_normalized_fault_signatures": len(unique_signatures),
            "new_signatures_in_tail": novelty_tail,
            "source_model_eligible_unattested": source_eligible,
            "oracle_mismatches": mismatches,
            "preregistered_sequence_mismatches": preregistered_mismatches,
            "scenario_diversity_validated": diversified,
            "unsafe_promotions": unsafe,
            "stream_sha256": digest,
        }
        aggregate.update(bytes.fromhex(digest))
        rows.append(row)
        overall_mismatches += mismatches
        overall_unsafe += unsafe
    saturated = (sessions == 10 and cases_per_session == 1_000_000 and
                 overall_mismatches == 0 and overall_unsafe == 0 and
                 all(r["new_signatures_in_tail"] == 0 for r in rows))
    return {
        "schema": SCHEMA,
        "status": "PASS_SCOPED_FINITE_MODEL" if saturated else
                  ("REFUTED" if overall_mismatches or overall_unsafe else "PARTIAL_NOT_10M"),
        "cases": sessions * cases_per_session,
        "preseeded_sessions": sessions,
        "families": list(FAMILIES),
        "levels": ["LOCAL", "INTERMEDIATE", "GLOBAL", "EXTERNAL"],
        "required_pair_signatures": len(PAIRS),
        "model_mismatches": overall_mismatches,
        "unsafe_promotions": overall_unsafe,
        "sessions_receipts": rows,
        "aggregate_sha256": aggregate.hexdigest(),
        "scope": "FINITE_SYNTHETIC_MODEL_NOT_10M_REAL_SOURCE_MUTANTS",
        "physical_source_mutations": 0,
        "external_runtime_evidence": "NOT_ATTESTED",
        "authorization": "NONE",
    }
