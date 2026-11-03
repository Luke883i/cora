"""Canonical dependency/invalidations kernel shared by agent, gold and DevOps.

Graph structure is a source contract, never evidence that an obligation has
been executed, reviewed, or authorized. The same kernel accepts distinct
profile vocabularies; profile-specific validation remains with its owner.
"""
from __future__ import annotations

from .evidence import domain_hash, valid_path

MAX_NODES = 1024
MAX_WITNESSES = 2048
MODEL = "MODEL_ELIGIBLE_UNATTESTED"
BLOCKED = "BLOCKED_UNOBSERVED"
EXTERNAL = "BLOCKED_EXTERNAL"
REFUTED = "REFUTED"


def ordered_cut(nodes: list[dict], goal: str) -> list[str]:
    """Deterministic non-compensatory reverse-derivation; no orphan promotion."""
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        raise ValueError("bounded reticular nodes required")
    index = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("malformed reticular node")
        key, deps = node.get("id"), node.get("depends_on")
        if not isinstance(key, str) or not key or key in index:
            raise ValueError("duplicate/invalid reticular identity")
        if (not isinstance(deps, list) or len(deps) > MAX_NODES or
            any(not isinstance(d, str) or not d for d in deps) or
            len(set(deps)) != len(deps)):
            raise ValueError("duplicate/invalid prerequisite")
        index[key] = node
    if goal not in index:
        raise ValueError("unknown reticular goal")
    order, active, seen = [], set(), set()
    def visit(key):
        if key in active:
            raise ValueError("reticular dependency cycle")
        if key in seen:
            return
        if key not in index:
            raise ValueError("dangling reticular dependency")
        active.add(key)
        for dep in index[key]["depends_on"]:
            visit(dep)
        active.remove(key)
        seen.add(key)
        order.append(key)
    visit(goal)
    return order


def assess_cut(nodes: list[dict], goal: str, observations: dict[str, str]) -> dict:
    """Finite model claims never become real-world PASS or external authority."""
    order = ordered_cut(nodes, goal)
    by_id = {n["id"]: n for n in nodes}
    leaves = {k for k in order if not by_id[k]["depends_on"]}
    if not isinstance(observations, dict) or any(k not in leaves or
            v not in (MODEL, BLOCKED, REFUTED, EXTERNAL) for k, v in observations.items()):
        raise ValueError("non-leaf or invalid model observation")
    states = {}
    for key in order:
        node = by_id[key]
        if node.get("scope") == "EXTERNAL":
            state = EXTERNAL
        elif key in leaves:
            state = observations.get(key, BLOCKED)
        else:
            inputs = [states[p] for p in node["depends_on"]]
            state = (REFUTED if REFUTED in inputs else
                     MODEL if inputs and all(s == MODEL for s in inputs) else BLOCKED)
        states[key] = state
    blocked = [k for k in order if k in leaves and states[k] != MODEL]
    result = {"schema": "cora-reticular-assessment/1", "goal": goal,
              "ordered_cut": order, "states": states, "blocked_leaves": blocked,
              "next_unresolved": blocked[0] if blocked else None,
              "status": states[goal],
              "proof_level": "FINITE_MODEL_UNATTESTED",
              "authorization": "NONE"}
    result["digest"] = domain_hash("CORA:reticular-assessment:1", result)
    return result


def invalidated_witnesses(witnesses: list[dict], changed_paths: list[str],
                          *, source_revision: str) -> dict:
    """Invalidate only dependencies reached by changed paths.

    A not-invalidated witness is NOT validated: exact-revision re-observation
    and the external oracle still control promotion. No globbing or deletes.
    """
    if (not isinstance(witnesses, list) or len(witnesses) > MAX_WITNESSES or
        not isinstance(changed_paths, list) or
        any(not valid_path(p) for p in changed_paths) or
        len(changed_paths) != len(set(changed_paths)) or
        not isinstance(source_revision, str) or len(source_revision) not in (40, 64) or
        any(c not in "0123456789abcdef" for c in source_revision)):
        raise ValueError("bounded exact-revision invalidation required")
    changed = set(changed_paths)
    rows, ids = [], set()
    for w in witnesses:
        if not isinstance(w, dict) or set(w) != {"id", "dependencies", "revision", "scope"}:
            raise ValueError("versioned witness dependency format required")
        key, deps = w["id"], w["dependencies"]
        if (not isinstance(key, str) or not key or key in ids or
            not isinstance(deps, list) or not 1 <= len(deps) <= 512 or
            len(set(deps)) != len(deps) or any(not valid_path(p) for p in deps) or
            w["scope"] not in ("SOURCE", "EXTERNAL") or
            not isinstance(w["revision"], str)):
            raise ValueError("unsafe or duplicated witness dependency")
        ids.add(key)
        hit = sorted(set(deps) & changed)
        state = ("BLOCKED_EXTERNAL" if w["scope"] == "EXTERNAL" else
                 "INVALIDATED_BY_CHANGED_SOURCE" if hit else
                 "NOT_INVALIDATED_REQUIRES_REVALIDATION")
        rows.append({"id": key, "state": state, "changed_dependencies": hit,
                     "previous_revision": w["revision"], "current_revision": source_revision,
                     "authenticated": False, "authorization": "NONE"})
    result = {"schema": "cora-reticular-invalidation/1",
              "source_revision": source_revision, "changed_paths": sorted(changed),
              "witnesses": rows, "authorization": "NONE",
              "scope": "DECLARED_PATH_DEPENDENCIES_NOT_RUNTIME_CAUSALITY"}
    result["digest"] = domain_hash("CORA:reticular-invalidation:1", result)
    return result
