"""Ten preseeded million-scenario semantic fault models, not physical source mutants.

Faults represent realistic engineering failure *classes* imported from the
three repositories. No scenario executes target code or authenticates CI/host.
"""
from __future__ import annotations
import hashlib
from .gold_assurance import FAMILIES

SCHEMA = "cora-gold-saturation/1"
MASK64 = (1 << 64) - 1
PAIRS = tuple((i,j) for i in range(12) for j in range(i+1,12))
ELIGIBLE = "MODEL_ELIGIBLE_UNATTESTED"
BLOCKED = "BLOCKED"

def _mix(value: int) -> int:
    x = (value + 0x9e3779b97f4a7c15) & MASK64
    x = ((x^(x>>30))*0xbf58476d1ce4e5b9) & MASK64
    x = ((x^(x>>27))*0x94d049bb133111eb) & MASK64
    return x ^ (x>>31)

def _scenario(i: int, seed: int) -> int:
    if i < 12:
        return 1 << i
    if i < 78:
        a,b=PAIRS[i-12]
        return (1 << a) | (1 << b)
    if i==78:
        return 0
    v = _mix(seed ^ (i*0x9e3779b97f4a7c15))
    out = 1 << ((v>>1)%12)
    if v&1:
        out |= 1 << ((v>>17)%12)
    if v&2:
        out |= 1 << ((v>>33)%12)
    if v&4:
        out |= 1 << ((v>>49)%12)
    return out

def _model(mask: int) -> tuple[str,str]:
    if type(mask) is not int or mask < 0 or mask >= (1<<12):
        raise ValueError("unknown semantic attack")
    gates = (mask&7)==0 and (mask&56)==0 and (mask&448)==0 and (mask&3584)==0
    return (ELIGIBLE if gates else BLOCKED), "BLOCKED_EXTERNAL"

def _oracle(mask: int) -> tuple[bool,bool]:
    """Separately phrased finite specification, NOT independent-world evidence."""
    return (mask == 0), False

def gold_saturation(contract: dict, *, sessions: int=10, cases_per_session: int=1000000) -> dict:
    if (type(sessions) is not int or type(cases_per_session) is not int or
        not 1 <= sessions <= 10 or not 300 <= cases_per_session <= 1000000):
        raise ValueError("bounded preseeded model campaign required")
    seeds = contract["seeded_campaign"]["seeds"][:sessions]
    receipts = []
    cumulative = hashlib.sha256()
    mismatches_total=unsafe_total=0
    for idx,seed in enumerate(seeds):
        stream=hashlib.sha256()
        signatures=set()
        singles=set()
        pairs=set()
        preregistered=0
        unsafe=mismatches=novel_tail=eligible=0
        tail_start=cases_per_session-min(100000,cases_per_session//10)
        for i in range(cases_per_session):
            mask = _scenario(i,seed)
            actual,governed = _model(mask)
            reference,ref_governed=_oracle(mask)
            if (actual==ELIGIBLE)!=reference:
                mismatches+=1
            if governed!="BLOCKED_EXTERNAL" or ref_governed or (mask and actual==ELIGIBLE):
                unsafe+=1
            if actual==ELIGIBLE:
                eligible+=1
            if i<12:
                if mask == 1<<i:
                    singles.add(i)
                else:
                    preregistered+=1
            elif i<78:
                a,b=PAIRS[i-12]
                if mask==((1<<a)|(1<<b)):
                    pairs.add((a,b))
                else:
                    preregistered+=1
            elif i==78 and mask!=0:
                preregistered+=1
            if mask.bit_count()>4:
                preregistered+=1
            if mask not in signatures:
                signatures.add(mask)
                if i >= tail_start:
                    novel_tail+=1
            stream.update(mask.to_bytes(2,"big"))
            stream.update(bytes((actual==ELIGIBLE,)))
        if len(singles)!=12 or len(pairs)!=66 or eligible<1 or len(signatures)<=79:
            unsafe+=1
        mismatches+=preregistered
        result={
            "session":idx+1,"seed":seed,"cases":cases_per_session,
            "observed_singles":len(singles),"observed_pairs":len(pairs),
            "unique_fault_signatures":len(signatures),
            "new_signatures_tail":novel_tail,
            "preregistered_mismatches":preregistered,
            "model_mismatches":mismatches,"unsafe_promotions":unsafe,
            "source_model_eligible_not_certified":eligible,
            "sha256":stream.hexdigest(),
        }
        cumulative.update(bytes.fromhex(result["sha256"]))
        receipts.append(result)
        mismatches_total+=mismatches
        unsafe_total+=unsafe
    full = sessions==10 and cases_per_session==1000000
    pass_model = (full and mismatches_total==0 and unsafe_total==0
                  and all(r["new_signatures_tail"]==0 for r in receipts))
    return {
        "schema":SCHEMA,"status":"PASS_SCOPED_FINITE_MODEL" if pass_model else
        ("REFUTED" if mismatches_total or unsafe_total else "PARTIAL_NOT_10M"),
        "families":list(FAMILIES[:12]), "levels":["LOCAL","INTERMEDIATE","GLOBAL"],
        "cases":sessions*cases_per_session,"sessions":sessions,
        "pair_coverage_required":66,"mismatches":mismatches_total,
        "unsafe_promotions":unsafe_total,"receipts":receipts,
        "aggregate_sha256":cumulative.hexdigest(),
        "real_source_mutations":0,"target_runtime":"NOT_EXECUTED",
        "source_coverage":"FINITE_TYPED_FAULT_MODEL_ONLY",
        "external_governance":"BLOCKED_EXTERNAL","authorization":"NONE",
    }


# PR-20: more realistic finite *engineering fault classes*, still never target
# source mutations. Every 1–4-way interaction is pre-registered, and the tail
# proves saturation only within this finite catalog.
from itertools import combinations
from .gold_assurance import FAULT_FAMILIES

CONVERGENCE_CATALOG = (0,) + tuple(
    sum(1 << bit for bit in combo)
    for size in (1, 2, 3, 4)
    for combo in combinations(range(16), size)
)
CONVERGENCE_PAIRS = tuple(combinations(range(16), 2))
CONVERGENCE_MODEL = "MODEL_ELIGIBLE_UNATTESTED"
CONVERGENCE_BLOCKED = "BLOCKED"


def convergence_scenario(i: int, seed: int) -> int:
    if i < len(CONVERGENCE_CATALOG):
        return CONVERGENCE_CATALOG[i]
    return CONVERGENCE_CATALOG[_mix(seed ^ (i * 0x9e3779b97f4a7c15)) %
                               len(CONVERGENCE_CATALOG)]


def convergence_model(mask: int) -> tuple[str, str]:
    """Four distinct source rails; any local source fault blocks the model."""
    if type(mask) is not int or mask < 0 or mask >= 1 << 16:
        raise ValueError("invalid bounded convergence fault vector")
    owner = (mask & ((1 << 4) - 1)) == 0
    mutation = (mask & (((1 << 9) - 1) ^ ((1 << 4) - 1))) == 0
    effects = (mask & (((1 << 12) - 1) ^ ((1 << 9) - 1))) == 0
    lifecycle = (mask & (((1 << 14) - 1) ^ ((1 << 12) - 1))) == 0
    return (CONVERGENCE_MODEL if owner and mutation and effects and lifecycle
            else CONVERGENCE_BLOCKED, "BLOCKED_EXTERNAL")


def convergence_reference(mask: int) -> tuple[bool, bool]:
    """Independent finite specification, not an independent product oracle."""
    return all((mask >> bit) & 1 == 0 for bit in range(14)), False


def saturate_convergence(contract: dict, *, sessions: int = 10,
                         cases_per_session: int = 1_000_000) -> dict:
    if (type(sessions) is not int or type(cases_per_session) is not int or
        not 1 <= sessions <= 10 or
        not len(CONVERGENCE_CATALOG) <= cases_per_session <= 1_000_000):
        raise ValueError("campaign requires each pre-registered semantic signature")
    seeds = contract["campaign"]["seeds"][:sessions]
    if len(CONVERGENCE_CATALOG) != 2517:
        raise ValueError("fixed 16-factor one-to-four-way ontology drift")
    receipts = []
    aggregate = hashlib.sha256()
    total_mismatches = total_promotions = 0
    for sid, seed in enumerate(seeds):
        seen, singles, pairs = set(), set(), set()
        mismatches = promotions = tail_novel = candidates = 0
        digest = hashlib.sha256()
        tail = cases_per_session - min(100_000, cases_per_session // 10)
        for i in range(cases_per_session):
            mask = convergence_scenario(i, seed)
            actual, governed = convergence_model(mask)
            expected_source, expected_governed = convergence_reference(mask)
            if (actual == CONVERGENCE_MODEL) != expected_source:
                mismatches += 1
            if (governed != "BLOCKED_EXTERNAL" or expected_governed or
                (mask & ((1 << 14) - 1) and actual == CONVERGENCE_MODEL)):
                promotions += 1
            if actual == CONVERGENCE_MODEL:
                candidates += 1
            if i < len(CONVERGENCE_CATALOG) and mask != CONVERGENCE_CATALOG[i]:
                mismatches += 1
            if mask.bit_count() > 4:
                mismatches += 1
            if mask.bit_count() == 1:
                singles.add(mask.bit_length() - 1)
            elif mask.bit_count() == 2:
                bits = tuple(k for k in range(16) if mask & (1 << k))
                pairs.add(bits)
            if mask not in seen:
                seen.add(mask)
                if i >= tail:
                    tail_novel += 1
            digest.update(mask.to_bytes(2, "big"))
            digest.update(bytes((actual == CONVERGENCE_MODEL,)))
        if (len(singles) != 16 or len(pairs) != 120 or
            len(seen) != len(CONVERGENCE_CATALOG) or candidates < 1):
            promotions += 1
        row = {
            "session": sid + 1, "seed": seed, "cases": cases_per_session,
            "observed_singles": len(singles), "observed_pairs": len(pairs),
            "normalized_signatures": len(seen),
            "new_signatures_tail": tail_novel,
            "model_mismatches": mismatches, "unsafe_promotions": promotions,
            "source_model_eligible_not_certified": candidates,
            "stream_sha256": digest.hexdigest(),
        }
        aggregate.update(bytes.fromhex(row["stream_sha256"]))
        receipts.append(row)
        total_mismatches += mismatches
        total_promotions += promotions
    complete = sessions == 10 and cases_per_session == 1_000_000
    clean = total_mismatches == 0 and total_promotions == 0 and all(
        x["new_signatures_tail"] == 0 for x in receipts)
    return {
        "schema": "cora-convergence-saturation/1",
        "status": ("PASS_SCOPED_FINITE_MODEL" if complete and clean else
                   "REFUTED" if not clean else "PARTIAL_NOT_10M"),
        "cases": sessions * cases_per_session, "sessions": sessions,
        "families": list(FAULT_FAMILIES), "receipts": receipts,
        "model_mismatches": total_mismatches, "unsafe_promotions": total_promotions,
        "normalized_signatures_per_session": len(CONVERGENCE_CATALOG),
        "aggregate_sha256": aggregate.hexdigest(),
        "source_mutants_executed": 0, "target_runtime": "NOT_EXECUTED",
        "complete_R1_R4": "BLOCKED_EXTERNAL",
        "scope": "PRESEEDED_FINITE_FAULT_CLASSES_NOT_10M_SOURCE_MUTANTS",
        "authorization": "NONE",
    }
