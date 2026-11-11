"""PR50 noncompensatory cross-repo contract: original Git, not self-issued approval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cora.git_snapshot import git
from cora.reticulum import MODEL, EXTERNAL, assess_cut, ordered_cut

CONTRACT = ".cora/contracts/dod/crossrepo-convergence-dod.json"
CUTS = {
    "I_S0": ["L00", "L01", "L02"],
    "I_S1": ["L10", "L11", "L12", "L13"],
    "I_S2": ["L20", "L21", "L22", "L23"],
    "I_S3": ["L30", "L31", "L32"],
    "I_S4": ["L40", "L41", "L42", "L43"],
    "G_SOURCE_CANDIDATE": ["I_S0", "I_S1", "I_S2", "I_S3"],
    "G_GOVERNED_PORTABILITY": ["G_SOURCE_CANDIDATE", "I_S4"],
}
EXTERNAL_LEAVES = {"L01", "L23", "L32", "L40", "L41", "L42", "L43"}
SOURCE_LEAVES = {
    "L00", "L02", "L10", "L11", "L12", "L13",
    "L20", "L21", "L22", "L30", "L31",
}
METRIC_KEYS = {
    "expected_original_workflows", "source_target_fixtures",
    "required_negative_families", "allowed_unauthorized_promotions",
    "required_report_replay", "verified_live_target_benchmarks",
    "min_new_user_sessions", "min_user_task_success_rate",
    "max_critical_false_proof_promotions", "efficiency_metric",
    "release_authorized",
}


def evaluate(root: Path, revision: str = "HEAD") -> dict:
    root = root.resolve(strict=True)
    commit = git(root, "rev-parse", revision).decode().strip()
    document = json.loads(git(root, "show", commit + ":" + CONTRACT).decode())
    if (document.get("schema") != "cora-crossrepo-convergence-dod/1"
            or document.get("authority") != "NONE"
            or document.get("global_goal") != "G_GOVERNED_PORTABILITY"
            or document.get("source_goal") != "G_SOURCE_CANDIDATE"
            or document.get("metrics", {}).keys() != METRIC_KEYS):
        raise ValueError("DoD contract identity or metrics drift")
    metrics = document["metrics"]
    if not (metrics["expected_original_workflows"] == 11
            and metrics["source_target_fixtures"] == 2
            and metrics["required_negative_families"] >= 12
            and metrics["allowed_unauthorized_promotions"] == 0
            and metrics["required_report_replay"] is True
            and metrics["verified_live_target_benchmarks"] == 2
            and metrics["min_new_user_sessions"] >= 8
            and metrics["min_user_task_success_rate"] >= .8
            and metrics["max_critical_false_proof_promotions"] == 0
            and metrics["release_authorized"] is False):
        raise ValueError("DoD quantitative protection weakened")
    nodes = document["nodes"]
    expected = set(CUTS) | EXTERNAL_LEAVES | SOURCE_LEAVES
    if (len(nodes) != len(expected) or len({n.get("id") for n in nodes}) != len(nodes)
            or {n["id"] for n in nodes} != expected):
        raise ValueError("missing, duplicate or extra obligation")
    for node in nodes:
        key = node["id"]
        if node.get("depends_on") != CUTS.get(key, []):
            raise ValueError("noncompensatory edge drift: " + key)
        kind = ("GLOBAL" if key.startswith("G_") else
                "INTERMEDIATE" if key.startswith("I_") else "LOCAL")
        scope = ("EXTERNAL" if key in EXTERNAL_LEAVES or
                 key in ("I_S4", "G_GOVERNED_PORTABILITY") else
                 "MIXED" if key in ("I_S0", "I_S2", "I_S3", "G_SOURCE_CANDIDATE") else
                 "SOURCE")
        if (node.get("kind") != kind or node.get("scope") != scope
                or not isinstance(node.get("claim"), str)
                or len(node["claim"]) < 15 or not isinstance(node.get("oracle"), str)
                or len(node["oracle"]) < 12):
            raise ValueError("obligation semantics/scope drift: " + key)
    if len(ordered_cut(nodes, document["global_goal"])) != len(nodes):
        raise ValueError("orphan obligation")
    # Give all SOURCE leaves the strongest permitted finite-model label.
    # No EXTERNAL leaf can be authenticated by this local exercise.
    model = assess_cut(nodes, document["global_goal"],
                       {k: MODEL for k in SOURCE_LEAVES})
    if (model["status"] != EXTERNAL or model["authorization"] != "NONE"
            or model["states"]["G_SOURCE_CANDIDATE"] == MODEL
            or any(model["states"][e] != EXTERNAL for e in EXTERNAL_LEAVES)):
        raise ValueError("source test promoted governed acceptance")
    return {
        "schema": "cora-crossrepo-convergence-contract-replay/1",
        "commit": commit, "tree": git(root, "rev-parse", commit + "^{tree}").decode().strip(),
        "obligations": len(nodes), "local": len(SOURCE_LEAVES | EXTERNAL_LEAVES),
        "intermediate": 5, "global": 2,
        "external_leaves": sorted(EXTERNAL_LEAVES),
        "source_model_status": model["states"]["G_SOURCE_CANDIDATE"],
        "product_status": "BLOCKED_EXTERNAL",
        "model_digest": model["digest"],
        "authority": "NONE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    result = evaluate(args.repo, args.revision)
    if args.verify and json.loads(args.verify.read_text("utf-8")) != result:
        raise ValueError("crossrepo contract report does not replay from original Git")
    if args.output:
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
