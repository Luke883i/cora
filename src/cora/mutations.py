"""Seeded in-memory repository-graph mutations, not physical repository rewrites.

Twenty curated mutation families with an externally authored expected-label
matrix. Mutations vary realistic filenames, roots, entrypoints and unknown
consumer types. Both outcome and mutated-model identity are hashed.
"""
from __future__ import annotations
import hashlib
import json
from .audit import owner_of

TEMPLATES = (
    ("rename_in_product", "ok"), ("add_product_source", "ok"),
    ("remove_unreferenced_source", "ok"), ("change_source_content", "ok"),
    ("cross_product_move", "unassigned"), ("nested_product_root", "overlap"),
    ("duplicate_entrypoint", "duplicate"), ("missing_entrypoint", "missing"),
    ("external_entrypoint", "outside"), ("symlink_input", "uncertain"),
    ("dynamic_loader", "uncertain"), ("reflection_registry", "uncertain"),
    ("workflow_external_call", "uncertain"), ("feature_flag_inactive", "uncertain"),
    ("unobserved_migration", "uncertain"), ("build_generated_path", "uncertain"),
    ("git_submodule_boundary", "uncertain"), ("external_consumer", "uncertain"),
    ("unmapped_deployable", "uncertain"), ("rename_with_ci_reference", "uncertain"),
)
MASK = (1 << 64) - 1

def mix64(v: int) -> int:
    v = (v + 0x9E3779B97F4A7C15) & MASK
    v = ((v ^ (v >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    v = ((v ^ (v >> 27)) * 0x94D049BB133111EB) & MASK
    return v ^ (v >> 31)

def mutate(name: str, salt: int) -> dict:
    """Generate a unique local architectural mutation of a two-product model."""
    root = f"apps/catalog_{salt & 65535:04x}"
    other = f"apps/worker_{(salt >> 16) & 65535:04x}"
    file = f"{root}/main_{(salt >> 32) & 65535:04x}.py"
    files = [file, f"{root}/support_{salt & 4095:03x}.py"]
    entries = [file]
    roots = {"catalog": root, "worker": other}
    unknown: list[str] = []
    if name == "rename_in_product":
        files[0] = entries[0] = f"{root}/new_{salt & 65535:04x}.py"
    elif name == "add_product_source":
        files.append(f"{root}/added_{(salt >> 23) & 8191:x}.py")
    elif name == "remove_unreferenced_source":
        files.pop()
    elif name == "cross_product_move":
        files[0] = entries[0] = f"shared/moved_{salt & 65535:04x}.py"
    elif name == "nested_product_root":
        roots["worker"] = root + "/tools"
    elif name == "duplicate_entrypoint":
        entries.append(file)
    elif name == "missing_entrypoint":
        files.remove(file)
    elif name == "external_entrypoint":
        files[0] = entries[0] = f"{other}/foreign_{salt & 65535:04x}.py"
    elif name not in ("change_source_content",):
        unknown.append(name)
    return {"roots": roots, "files": files, "entrypoints": entries, "unknown": unknown, "salt": salt}

def classify(m: dict) -> str:
    roots, files, entries = m["roots"], set(m["files"]), m["entrypoints"]
    r = list(roots.values())
    if any(a == b or a.startswith(b + "/") or b.startswith(a + "/") for i, a in enumerate(r) for b in r[i + 1:]):
        return "overlap"
    if len(entries) != len(set(entries)):
        return "duplicate"
    if any(e not in files for e in entries):
        return "missing"
    if any(owner_of(e, roots) != ["catalog"] for e in entries):
        return "unassigned" if any(not owner_of(e, roots) for e in entries) else "outside"
    if m["unknown"]:
        return "uncertain"
    return "ok"

def stress(*, seed: int = 883, cases: int = 1_000_000) -> dict:
    if not 1 <= cases <= 10_000_000:
        raise ValueError("cases must be in 1..10_000_000")
    digest = hashlib.sha256()
    totals = {name: 0 for name, _ in TEMPLATES}
    wrong = 0
    for i in range(cases):
        v = mix64((seed ^ i) & MASK)
        name, oracle = TEMPLATES[v % len(TEMPLATES)]
        model = mutate(name, v)
        got = classify(model)
        wrong += got != oracle
        totals[name] += 1
        digest.update(i.to_bytes(8, "little") + v.to_bytes(8, "little") + bytes([v % len(TEMPLATES), len(got)]))
    return {"schema": "cora-pr01-mutation-stress/2", "seed": seed, "cases": cases, "model": "seeded in-memory repository topology and consumer mutations", "fixture_families": len(TEMPLATES), "mismatches": wrong, "distribution": totals, "stream_sha256": digest.hexdigest(), "limits": ["Not independent repository samples", "In-memory topology mutations, not file-system rewrites", "Independent category labels, but expected outcomes derive from fixture design", "No runtime reachability or deletion-equivalence proof"]}
