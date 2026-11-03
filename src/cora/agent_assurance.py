"""Backward-derived AI coding-assistant DoD: descriptive evidence, never authority.

A self-reported observation is a CLAIM, not independently verified execution.
The fixed v1 fault family/edge vocabulary prevents scope erosion by editing
the candidate policy; BASE/hosting policy protection remains a separate gate.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .evidence import domain_hash

SCHEMA = "cora-agent-assurance-contract/1"
REPORT = "cora-agent-dod/1"
LOCAL_IDS = tuple("L%02d" % n for n in range(1, 25))
GROUPS = {
    "I_LOCAL": LOCAL_IDS[:6],
    "I_INTERMEDIATE": LOCAL_IDS[6:12],
    "I_GLOBAL": LOCAL_IDS[12:18],
    "I_EXTERNAL": LOCAL_IDS[18:24],
    "G_SOURCE_AGENT": ("I_LOCAL", "I_INTERMEDIATE", "I_GLOBAL"),
    "G_GOVERNED_AGENT": ("G_SOURCE_AGENT", "I_EXTERNAL"),
}
LEVELS = ("LOCAL", "INTERMEDIATE", "GLOBAL", "EXTERNAL")
STAGES = {
    "intake": "I_LOCAL",
    "implementation": "I_INTERMEDIATE",
    "premerge": "G_SOURCE_AGENT",
    "postmerge": "I_GLOBAL",
    "release": "G_GOVERNED_AGENT",
}
FAMILIES = (
    "ambiguous_product_owner", "unbound_source_identity",
    "unsafe_input_archive", "unmapped_dynamic_consumer",
    "untestable_behavior_target", "unreviewed_compatibility",
    "no_material_code_delta", "missing_negative_oracle",
    "tautological_test_oracle", "untrusted_runtime_receipt",
    "uncalibrated_stress_volume", "evidence_missing_invalidation",
    "stale_change_base", "policy_self_override",
    "unclosed_dod_dependency", "ci_different_revision",
    "regression_or_coverage_gap", "missing_postmerge_continuity",
    "branch_not_protected", "no_independent_review",
    "sandbox_not_attested", "real_repositories_unvalidated",
    "rollback_unverified", "release_authority_missing",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load_contract(path: Path) -> dict:
    """Reject edited/missing prerequisite edges, missing fault families and authority promotion."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("invalid agent DoD contract schema")
    nodes = data.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 30 or not all(isinstance(x, dict) for x in nodes):
        raise ValueError("agent DoD nodes missing/duplicated")
    found = {}
    for n in nodes:
        identifier = n.get("id")
        if not isinstance(identifier, str) or identifier in found:
            raise ValueError("unknown or duplicated DoD id")
        found[identifier] = n
    if set(found) != set(LOCAL_IDS) | set(GROUPS):
        raise ValueError("fixed source/external DoD vocabulary changed")
    for idx, identifier in enumerate(LOCAL_IDS):
        n = found[identifier]
        level = LEVELS[idx // 6]
        if (n.get("kind") != "LOCAL" or n.get("level") != level or
            n.get("scope") != ("EXTERNAL" if idx >= 18 else "SOURCE") or
            n.get("family") != FAMILIES[idx] or n.get("depends_on") != [] or
            not isinstance(n.get("falsifier"), str) or
            not 8 <= len(n["falsifier"]) <= 200):
            raise ValueError("local fault contract/authority mismatch: " + identifier)
    for identifier, dependencies in GROUPS.items():
        n = found[identifier]
        if (n.get("depends_on") != list(dependencies) or
            n.get("kind") != ("GLOBAL" if identifier.startswith("G_") else "INTERMEDIATE") or
            n.get("level") != ("EXTERNAL" if identifier in ("I_EXTERNAL", "G_GOVERNED_AGENT") else "SOURCE")):
            raise ValueError("prerequisite cut changed: " + identifier)
    if data.get("goals") != STAGES or data.get("prerequisites") != {
            "source": "G_SOURCE_AGENT", "governed": "G_GOVERNED_AGENT"}:
        raise ValueError("reverse derivation targets changed")
    if data.get("normative_boundary") != "SOURCE_MODEL_NOT_AN_AUTHORITY" or data.get("authorities") != {
        "source": "SELF_REPORTED_NEVER_APPROVED",
        "runtime": "UNTRUSTED_UNTIL_INDEPENDENTLY_ATTESTED",
        "governed": "OUTSIDE_CORA",
    }:
        raise ValueError("authority must remain external")
    seeds = data.get("seeds")
    if (not isinstance(seeds, list) or len(seeds) != 10 or
        any(type(s) is not int or not 0 <= s < (1 << 32) for s in seeds) or
        len(set(seeds)) != len(seeds)):
        raise ValueError("ten independent preseeded campaign seeds required")
    if data.get("mutation_budget") != {
        "sessions": 10, "cases_per_session": 1_000_000, "tail_cases": 100_000,
        "local_families": 6, "intermediate_families": 6,
        "global_families": 6, "external_families": 6, "min_pair_signatures": 276,
    }:
        raise ValueError("normative 10M saturation budget drift")
    return data


def _reachable(index: dict[str, dict], target: str) -> list[str]:
    if target not in index:
        raise ValueError("unknown DoD target")
    order, temporary, permanent = [], set(), set()

    def visit(identifier: str) -> None:
        if identifier in temporary:
            raise ValueError("DoD cycle")
        if identifier in permanent:
            return
        temporary.add(identifier)
        for dep in index[identifier]["depends_on"]:
            if dep not in index:
                raise ValueError("missing DoD dependency")
            visit(dep)
        temporary.remove(identifier)
        permanent.add(identifier)
        order.append(identifier)
    visit(target)
    return order


def backward_plan(contract: dict, *, goal: str = "G_SOURCE_AGENT") -> dict:
    index = {n["id"]: n for n in contract["nodes"]}
    path = _reachable(index, goal)
    locals_in_cut = [i for i in path if i in LOCAL_IDS]
    first = index[locals_in_cut[0]] if locals_in_cut else None
    result = {
        "schema": REPORT,
        "mode": "REVERSE_DERIVATION_ONLY",
        "goal": goal,
        "contract_digest": domain_hash("CORA:agent-contract:1", contract),
        "prerequisites_in_topological_order": path,
        "local_cut": locals_in_cut,
        "nearest_falsifier": {"id": first["id"], "method": first["falsifier"]} if first else None,
        "scope": "REQUIREMENTS_NOT_EXECUTION",
        "authorization": "NONE",
    }
    result["report_digest"] = domain_hash("CORA:agent-plan:1", result)
    return result


def assess_claims(contract: dict, observations: dict, *,
                  goal: str = "G_SOURCE_AGENT") -> dict:
    """The caller controls this JSON: even a fully populated DoD stays unverified."""
    if not isinstance(observations, dict) or observations.get("schema") != "cora-agent-claims/1":
        raise ValueError("agent claims schema missing")
    sha = observations.get("head_sha")
    if not isinstance(sha, str) or not HEX40.fullmatch(sha):
        raise ValueError("exact candidate SHA required, but not authenticated")
    claims = observations.get("locals")
    if not isinstance(claims, dict) or not set(claims).issubset(LOCAL_IDS):
        raise ValueError("unknown local observation key")
    index = {n["id"]: n for n in contract["nodes"]}
    path = _reachable(index, goal)
    derived, blockers = {}, []
    for identifier in path:
        n = index[identifier]
        if identifier in LOCAL_IDS:
            obj = claims.get(identifier)
            if obj is None:
                status = "BLOCKED_MISSING"
            elif not isinstance(obj, dict) or obj.get("status") not in ("CLAIMED_PASS", "REFUTED", "BLOCKED"):
                raise ValueError("invalid claimed observation state: " + identifier)
            elif obj["status"] == "REFUTED":
                status = "REFUTED"
            elif obj["status"] == "BLOCKED":
                status = "BLOCKED"
            elif (obj.get("revision") != sha or
                  not isinstance(obj.get("witness"), str) or
                  not 8 <= len(obj["witness"]) <= 512 or
                  not obj["witness"].strip()):
                status = "BLOCKED_WRONG_OR_MISSING_WITNESS"
            else:
                status = "CLAIMED_PRESENT_UNVERIFIED"
            # External witnesses cannot be certified by caller-supplied text,
            # even if their revision/digest formatting is consistent.
            if identifier in LOCAL_IDS[18:] and status == "CLAIMED_PRESENT_UNVERIFIED":
                status = "BLOCKED_EXTERNAL"
        else:
            predecessors = [derived[d] for d in n["depends_on"]]
            if identifier in ("I_EXTERNAL", "G_GOVERNED_AGENT"):
                status = "BLOCKED_EXTERNAL"
            elif "REFUTED" in predecessors:
                status = "REFUTED"
            elif any(not x.endswith("UNVERIFIED") and x != "MODEL_ELIGIBLE_UNATTESTED"
                     for x in predecessors):
                status = "BLOCKED"
            else:
                status = "MODEL_ELIGIBLE_UNATTESTED"
        derived[identifier] = status
        if identifier in LOCAL_IDS and status != "CLAIMED_PRESENT_UNVERIFIED":
            blockers.append(identifier)
    next_blocker = blockers[0] if blockers else None
    next_falsifier = ({
        "id": next_blocker,
        "status": derived[next_blocker],
        "method": index[next_blocker]["falsifier"],
        "scope": index[next_blocker]["scope"],
    } if next_blocker else None)
    result = {
        "schema": REPORT,
        "mode": "UNTRUSTED_AGENT_CLAIMS_RECONCILED",
        "goal": goal,
        "head_sha_claimed": sha,
        "contract_digest": domain_hash("CORA:agent-contract:1", contract),
        "claims_digest": domain_hash("CORA:agent-claims:1", observations),
        "states": derived,
        "blocked_locals": blockers,
        "next_unresolved_falsifier": next_falsifier,
        "goal_status": derived[goal],
        "authority": "UNVERIFIED_CLAIM_NO_EXTERNAL_ATTESTATION",
        "authorization": "NONE",
        "release_authorized": False,
        "unknowns": ["GITHUB_HEAD_AUTHENTICATION", "EXECUTION_AUTHENTICATION",
                     "INDEPENDENT_REVIEW", "PRODUCTION_VALIDITY"],
    }
    result["report_digest"] = domain_hash("CORA:agent-evaluation:1", result)
    return result


def verify_assessment(contract: dict, observations: dict, report: dict) -> bool:
    if not isinstance(report, dict) or report.get("schema") != REPORT:
        raise ValueError("invalid evaluation receipt")
    if report != assess_claims(contract, observations, goal=report.get("goal", "")):
        raise ValueError("evaluation altered or not reproducible")
    return True
