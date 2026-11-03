"""Source-only contextual gold reticulum; local Git snapshots, never untrusted execution."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from .evidence import domain_hash

SCHEMA = "cora-gold-assurance/1"
HEX = re.compile(r"^[0-9a-f]{40}$")
LOCAL = tuple(f"L{i:02d}" for i in range(1, 17))
CUTS = {
 "I_CONTEXT": LOCAL[:3], "I_PHYSICAL": LOCAL[3:6],
 "I_EFFECT": LOCAL[6:9], "I_PILOT": LOCAL[9:12],
 "I_EXTERNAL": LOCAL[12:],
 "G_GOLD_SOURCE": ("I_CONTEXT", "I_PHYSICAL", "I_EFFECT", "I_PILOT"),
 "G_GOLD_GOVERNED": ("G_GOLD_SOURCE", "I_EXTERNAL"),
}
FAMILIES = (
 "intent_provenance_missing", "ambiguous_or_duplicate_owner",
 "contextual_dependency_gap", "model_only_mutation",
 "mutant_classification_laundered", "unsafe_unconsented_execution",
 "hidden_ci_side_effect", "claimed_effect_without_readback",
 "self_attested_action_authority", "single_repo_overfit",
 "source_drift_or_stale_pin", "pilot_scoped_claim_inflation",
 "missing_host_branch_protection", "missing_non_author_review",
 "pilot_runtime_not_executed", "rollback_not_attested",
)
REPOS = ("Luke883i/ictc", "Luke883i/ikant", "Luke883i/aosp1")
PATTERN_CUTS = ("I_CONTEXT",)*4 + ("I_PHYSICAL",)*3 + ("I_EFFECT",)*3 + ("I_PILOT",)*2

def _safe_path(path: str) -> bool:
    return isinstance(path, str) and 0 < len(path) <= 240 and not path.startswith(("/", "-")) and "\\" not in path and "\x00" not in path and all(x not in ("", ".", "..") for x in path.split("/")) and str(PurePosixPath(path)) == path

def load_gold_contract(path: str | Path) -> dict:
    c = json.loads(Path(path).read_text("utf-8"))
    if not isinstance(c, dict) or c.get("schema") != SCHEMA or c.get("authority_effect") != "NONE":
        raise ValueError("gold contract/authority invalid")
    nodes = c.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 23 or not all(isinstance(n, dict) for n in nodes):
        raise ValueError("23 gold nodes required")
    ids = [n.get("id") for n in nodes]
    if len(set(ids)) != 23 or set(ids) != set(LOCAL) | set(CUTS):
        raise ValueError("missing/duplicate gold DoD node")
    index = {n["id"]: n for n in nodes}
    for i, key in enumerate(LOCAL):
        n = index[key]
        parent = list(CUTS)[i // 3] if i < 12 else "I_EXTERNAL"
        if (n.get("kind") != "LOCAL" or n.get("parent") != parent or
            n.get("family") != FAMILIES[i] or n.get("depends_on") != [] or
            n.get("scope") != ("EXTERNAL" if i >= 12 else "SOURCE") or
            not isinstance(n.get("falsifier"), str) or len(n["falsifier"]) < 12):
            raise ValueError("gold local node drift: " + key)
    for key, deps in CUTS.items():
        n = index[key]
        if (n.get("depends_on") != list(deps) or
            n.get("kind") != ("GLOBAL" if key.startswith("G_") else "INTERMEDIATE") or
            n.get("scope") != ("EXTERNAL" if key in ("I_EXTERNAL", "G_GOLD_GOVERNED") else "SOURCE")):
            raise ValueError("gold reticular edge/authority drift: " + key)
    if c.get("roots") != {"source":"G_GOLD_SOURCE","governed":"G_GOLD_GOVERNED"}:
        raise ValueError("promoted gold goal")
    patterns = c.get("patterns")
    if not isinstance(patterns, list) or len(patterns) != 12 or any(
        p.get("id") != f"P{i+1:02d}" or p.get("gate") != PATTERN_CUTS[i] or
        not isinstance(p.get("origin"), str) for i,p in enumerate(patterns)):
        raise ValueError("portable gold patterns missing")
    cam = c.get("seeded_campaign") or {}
    seeds = cam.get("seeds")
    if (cam.get("sessions") != 10 or cam.get("cases_per_session") != 1000000 or
        cam.get("pair_count") != 66 or cam.get("tail_cases") != 100000 or
        cam.get("fault_families") != list(FAMILIES[:12]) or
        cam.get("physical_source_mutants_in_10m") != 0 or
        not isinstance(seeds,list) or len(seeds) != 10 or len(set(seeds)) != 10 or
        any(type(i) is not int or i < 0 or i >= 2**32 for i in seeds)):
        raise ValueError("10M model boundary changed")
    pilots = c.get("pilots")
    if not isinstance(pilots, list) or tuple(p.get("repo") for p in pilots) != REPOS:
        raise ValueError("exact three source pilots required")
    for p in pilots:
        if not HEX.fullmatch(str(p.get("revision", ""))):
            raise ValueError("unbound pilot commit")
        for key in ("owner", "sample"):
            s = p.get(key)
            if (not isinstance(s, dict) or not _safe_path(s.get("path")) or
                not HEX.fullmatch(str(s.get("git_blob", ""))) or
                not isinstance(s.get("marker"), str) or not s["marker"]):
                raise ValueError("unbound pilot source file")
    if c.get("epistemic_boundary") != {
        "source":"SCOPED_SOURCE_NOT_PRODUCT_PROOF",
        "simulations":"FINITE_SEMANTIC_MODEL",
        "execution":"NOT_EXECUTED_UNLESS_EXPLICIT_DOCKER_OPT_IN",
        "governed":"BLOCKED_EXTERNAL","authorization":"NONE"}:
        raise ValueError("external authority boundary drift")
    return c

def retrograde_gold(contract: dict, goal: str = "G_GOLD_SOURCE") -> dict:
    if goal not in CUTS:
        raise ValueError("unknown goal")
    found = {n["id"]: n for n in contract["nodes"]}
    order, seen, active = [], set(), set()
    def walk(key):
        if key in active:
            raise ValueError("cycle")
        if key in seen:
            return
        active.add(key)
        for dep in found[key]["depends_on"]:
            walk(dep)
        active.remove(key)
        seen.add(key)
        order.append(key)
    walk(goal)
    result = {"schema":"cora-gold-retrograde/1","goal":goal,
              "nodes":order,"local_cut":[x for x in order if x in LOCAL],
              "status":"REQUIREMENTS_DERIVED_NOT_EXECUTED",
              "authorization":"NONE"}
    result["digest"] = domain_hash("CORA:gold-plan:1",result)
    return result

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def _git_file(root: Path, revision: str, path: str) -> bytes:
    rev = subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,timeout=15)
    if rev.returncode or rev.stdout.decode().strip() != revision:
        raise ValueError("source checkout not on pinned exact HEAD")
    p = subprocess.run(["git","-C",str(root),"show",revision+":"+path],
                       capture_output=True,timeout=30)
    if p.returncode or len(p.stdout) > 524288:
        raise ValueError("committed file missing/oversized")
    return p.stdout

def pilot_sources(contract: dict, roots: dict[str, Path]) -> dict:
    """Read from explicit local checkouts. No network, target execution or mutation."""
    if not isinstance(roots, dict) or any(r not in REPOS for r in roots):
        raise ValueError("only three pinned source repositories supported")
    rows = []
    for pilot in contract["pilots"]:
        repo, revision = pilot["repo"], pilot["revision"]
        items = []
        for slot in ("owner","sample"):
            spec = pilot[slot]
            row = {"slot":slot,"path":spec["path"],"expected_blob":spec["git_blob"]}
            if repo not in roots:
                row["state"] = "NOT_OBSERVED"
            else:
                try:
                    data = _git_file(Path(roots[repo]), revision, spec["path"])
                    actual = blob_sha(data)
                    row["actual_blob"] = actual
                    row["state"] = ("SOURCE_BYTES_VERIFIED" if actual == spec["git_blob"] and
                                    spec["marker"].encode() in data else "REFUTED")
                except (OSError,ValueError,subprocess.TimeoutExpired):
                    row["state"] = "BLOCKED_SOURCE"
            items.append(row)
        state = "SOURCE_READBACK_SCOPED" if all(x["state"]=="SOURCE_BYTES_VERIFIED" for x in items) else "BLOCKED"
        rows.append({"repo":repo,"revision":revision,"state":state,
                     "owner_semantics":"DECLARED_NOT_INDEPENDENTLY_ATTESTED",
                     "files":items})
    result = {"schema":"cora-gold-pilot/1","pilots":rows,
              "state":"SOURCE_READBACK_3_OF_3" if all(x["state"]=="SOURCE_READBACK_SCOPED" for x in rows) else "BLOCKED_INCOMPLETE",
              "runtime":"NOT_EXECUTED","external":"BLOCKED_EXTERNAL","authorization":"NONE"}
    result["digest"] = domain_hash("CORA:gold-pilot:1",result)
    return result

def contextual_gold(contract: dict, intent: str, pilot: dict | None = None, *, roots: dict | None = None) -> dict:
    if not isinstance(intent,str) or len(intent.strip()) < 12:
        raise ValueError("human product intent required")
    r = retrograde_gold(contract)
    if pilot is not None and roots is not None:
        raise ValueError("choose source reread or untrusted authored pilot report")
    if roots is not None:
        observed = {x["repo"]:x["state"] for x in pilot_sources(contract,roots)["pilots"]}
        provenance = "FRESH_GIT_BLOB_REPLAY_NOT_OWNER_SEMANTIC_VALIDATION"
    else:
        observed = {x["repo"]:"UNVERIFIED_IMPORTED_REPORT" for x in (pilot or {}).get("pilots", [])}
        provenance = "UNTRUSTED_CLAIM_NOT_SOURCE_REPLAY" if pilot is not None else "NOT_OBSERVED"
    leaf = "L02" if roots is not None and len(observed)==3 and all(
        x=="SOURCE_READBACK_SCOPED" for x in observed.values()) else "L01"
    result = {"schema":"cora-gold-contextual/1","intent_sha256":hashlib.sha256(intent.encode()).hexdigest(),
              "goal":r["goal"],"nodes":r["nodes"],"local_cut":r["local_cut"],
              "pilot_provenance":provenance,
              "contextual_bindings":[{"repo":p["repo"],"revision":p["revision"],
                "owner":p["owner"]["path"],"source":p["sample"]["path"],
                "observed":observed.get(p["repo"],"NOT_OBSERVED")} for p in contract["pilots"]],
              "nearest_unresolved":leaf,
              "nearest_falsifier":next(n["falsifier"] for n in contract["nodes"] if n["id"]==leaf),
              "state":"BLOCKED_MATERIAL_PRODUCT_PROOF",
              "owner_semantics":"UNATTESTED","runtime":"NOT_EXECUTED",
              "governed":"BLOCKED_EXTERNAL","authorization":"NONE"}
    result["digest"]=domain_hash("CORA:gold-contextual:1",result)
    return result
