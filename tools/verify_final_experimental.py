"""PR41 final experimental *candidate*: exact-Git source/observed fixture verifier.

Not a release authority. External reviewer, maintained target, host isolation, usable
product, protected branch and release manager MUST be separately authenticated.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import importlib.util
import itertools
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

CONTRACT = ".cora/contracts/dod/final-experimental-dod.json"
FAULTS = ".cora/fixtures/final-experimental-faults.json"
SOURCE = [
    "D01_GIT_CHRONO", "D02_PROSE_NEGATIVE", "D03_ROLE_AND_CLI",
    "D04_ARCHIVE_SEPARATION", "D05_EXACT_HEAD_REPLAY",
    "B01_INDEPENDENT_NATIVE_ORACLE", "B02_PHYSICAL_NEGATIVE_CONTROL",
    "B03_NO_RUNTIME_PROMOTION", "B04_BEHAVIOR_DIGEST_REPLAY",
    "H01_HOST_NONPROMOTION", "H02_INDEPENDENT_REVIEW_POLICY",
    "H03_REQUIRED_CHECK_DESIGN", "R01_PACKAGE_VERSION",
    "R02_FINAL_EXPERIMENTAL_SCOPE", "R03_PRESEEDED_MILLION",
]
EXTERNAL = [
    "E_B1_REAL_TARGET", "E_B2_RUNTIME_ISOLATION", "E_B3_USER_STUDY",
    "E_H1_HOST_ENFORCEMENT", "E_H2_NONAUTHOR_REVIEW",
    "E_R1_TAG_ASSETS", "E_R2_RELEASE_OWNER",
]
EDGES = {
    "G_DOC_SOURCE": SOURCE[0:5],
    "G_BEHAVIOR_SOURCE": SOURCE[5:9],
    "G_GOVERNANCE_SOURCE": SOURCE[9:12],
    "G_FREEZE_SOURCE": ["G_DOC_SOURCE", "G_BEHAVIOR_SOURCE",
                        "G_GOVERNANCE_SOURCE", *SOURCE[12:15]],
    "G_EXTERNAL_BEHAVIOR": EXTERNAL[0:3],
    "G_EXTERNAL_GOVERNANCE": EXTERNAL[3:5],
    "G_EXTERNAL_RELEASE": EXTERNAL[5:7],
    "G_FINAL_EXPERIMENTAL": ["G_FREEZE_SOURCE", "G_EXTERNAL_BEHAVIOR",
                             "G_EXTERNAL_GOVERNANCE", "G_EXTERNAL_RELEASE"],
}
FAULT_IDS = [
    "DOC_UNMERGED_PR40", "DOC_ARCHITECTURE_STALE", "DOC_REGISTRY_BROKEN",
    "DOC_CLI_UNSYNCED", "BEHAV_SOURCE_FORGED", "BEHAV_STALE_COMMIT",
    "BEHAV_ORACLE_FAKE", "BEHAV_SYNTHETIC_AS_REAL",
    "GOV_PROTECTION_OFF", "GOV_RULES_403", "GOV_SAME_AUTHOR",
    "GOV_REQUIRED_CHECK_MISSING", "REL_TAG_MISMATCH",
    "REL_ARTIFACT_MISMATCH", "REL_ROLLBACK_MISSING",
    "REL_MODEL_AS_APPROVAL",
]
MASK = (1 << 64) - 1
SEEDS = [883, 20261107, 41, 1407]
SCHEMA = "cora-final-experimental-source/1"
BASELINE = "2e4951eec8877d16f366d0b49498eb4393a3b580"
EXPECTED_METRICS = {
  "doc_current_false_claims_max": 0,
  "git_tracked_role_coverage_min": 1,
  "markdown_registry_coverage_min": 1,
  "cli_parser_exact": 71,
  "native_git_fixture_repositories_min": 2,
  "real_git_changed_commit_cases_min": 1,
  "critical_false_pass_max": 0,
  "external_maintained_targets_min": 2,
  "independent_usability_participants_min": 8,
  "usability_tasks_per_person_min": 3,
  "usability_completion_min": 0.8,
  "critical_misclassification_max": 0,
  "semantic_cases_exact": 1000000,
  "seeds": [
    883,
    20261107,
    41,
    1407
  ],
  "fault_families_exact": 16,
  "preseed_up_to_fourway_exact": 2517,
  "model_mismatches_max": 0,
  "unsafe_authorizations_max": 0,
  "release_tag_commit_equal_final_main": True,
  "non_author_human_review_required": True,
  "required_status_checks_enforced": True,
  "exact_final_head_and_postmerge_ci": True,
  "release_rollback_drill_required": True
}
EXPECTED_FREEZE = {
  "scope": "FINAL_EXPERIMENTAL_SOURCE_BASELINE_CANDIDATE",
  "immutable_after_merge": "Every subsequent source-changing patch creates a new candidate and invalidates earlier receipts; experimental final tag only after independent authorization.",
  "stable_1_0_0": False,
  "public_release_authorized": False,
  "requires_independent_operator": True,
  "reused_orchestrator": "cora process-run --one-run --profile comprehensive",
  "forbidden": [
    "AUTO_MERGE",
    "AUTO_TAG",
    "AUTO_PUBLISH",
    "AUTO_DELETE",
    "SELF_APPROVAL",
    "SYNTHETIC_AS_REAL_TARGET"
  ]
}


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def git(repo: Path, *args: str) -> bytes:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_CONFIG_")
           and k not in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                         "GIT_INDEX_FILE")}
    result = subprocess.run(["git", "-C", str(repo), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, timeout=90, check=False)
    if result.returncode:
        raise ValueError("Git original source failed (exit %d): %s" %
                         (result.returncode,
                          result.stderr.decode("utf-8", "replace")[:800]))
    if len(result.stdout) > 16_000_000:
        raise ValueError("Git source exceeds bounded read")
    return result.stdout


def source(repo: Path, sha: str, path: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9._/\-]+", path):
        raise ValueError("unsafe source path")
    return git(repo, "show", sha + ":" + path).decode("utf-8")


def contract_at(repo: Path, sha: str) -> dict:
    doc = json.loads(source(repo, sha, CONTRACT))
    metrics = doc.get("metrics", {})
    if (doc.get("schema") != "cora-final-experimental-dod/1"
            or doc.get("authority") != "NONE"
            or doc.get("product_status") != "BLOCKED_EXTERNAL"
            or doc.get("public_release") != "NOT_AUTHORIZED"
            or doc.get("baseline_main") != BASELINE
            or doc.get("package_version") != "1.0.0a4"
            or doc.get("cli_count") != 71
            or doc.get("logic") != "NONCOMPENSATORY_AND"
            or doc.get("source") != SOURCE or doc.get("external") != EXTERNAL
            or doc.get("edges") != EDGES
            or doc.get("release_freeze", {}).get("public_release_authorized") is not False
            or doc.get("release_freeze", {}).get("requires_independent_operator") is not True):
        raise ValueError("final experiment source/external contract changed")
    if (metrics.get("semantic_cases_exact") != 1_000_000
            or metrics.get("seeds") != SEEDS
            or metrics.get("fault_families_exact") != len(FAULT_IDS)
            or metrics.get("preseed_up_to_fourway_exact") != 2517
            or metrics.get("model_mismatches_max") != 0
            or metrics.get("unsafe_authorizations_max") != 0
            or metrics.get("doc_current_false_claims_max") != 0
            or metrics.get("cli_parser_exact") != 71
            or metrics.get("native_git_fixture_repositories_min") != 2
            or metrics.get("external_maintained_targets_min") != 2
            or metrics.get("independent_usability_participants_min") != 8
            or metrics.get("usability_tasks_per_person_min") != 3
            or metrics.get("usability_completion_min") != 0.8
            or metrics.get("critical_misclassification_max") != 0
            or metrics.get("non_author_human_review_required") is not True
            or metrics.get("required_status_checks_enforced") is not True
            or metrics.get("exact_final_head_and_postmerge_ci") is not True):
        raise ValueError("measurable final experiment threshold drift")
    if metrics != EXPECTED_METRICS or doc.get("release_freeze") != EXPECTED_FREEZE:
        raise ValueError("complete final experiment metric/freeze invariant drift")
    by = {}
    for n in doc.get("nodes", []):
        name = n.get("id")
        if name in by:
            raise ValueError("duplicate final experiment node")
        by[name] = n
    if set(by) != set(SOURCE + EXTERNAL + list(EDGES)) or len(by) != 30:
        raise ValueError("final experiment obligation coverage changed")
    for name, node in by.items():
        ext = name in EXTERNAL or name == "G_FINAL_EXPERIMENTAL" or name.startswith("G_EXTERNAL_")
        if (node.get("scope") != ("EXTERNAL" if ext else "SOURCE")
                or node.get("depends_on") != EDGES.get(name, [])
                or node.get("acceptance") != (
                    "AUTHENTICATED_INDEPENDENT_OPERATOR_WITNESS" if ext else
                    ("EXACT_HEAD_CI_PLUS_GIT_REPLAY" if name in EDGES else
                     "EXECUTE_EXACT_GIT_ORACLE_AND_REPLAY"))
                or (ext and node.get("witness_paths"))
                or node.get("status") != (
                    "BLOCKED_EXTERNAL" if ext else "UNPROVEN_BY_DECLARATION")):
            raise ValueError("external gate scope, proof or AND edge was promoted: " + name)
    if len({x for deps in EDGES.values() for x in deps if x not in by}):
        raise ValueError("incomplete final DoD graph")
    fixture = json.loads(source(repo, sha, FAULTS))
    families = fixture.get("families")
    if (fixture.get("schema") != "cora-final-experimental-faults/1"
            or fixture.get("authority") != "NONE"
            or fixture.get("cases") != 1_000_000
            or fixture.get("seed_stream") != SEEDS
            or fixture.get("preregister") != "ZERO_SINGLE_PAIR_TRIPLE_QUADRUPLE_MASKS"
            or fixture.get("external_release_authority") != "NEVER_FROM_MODEL"
            or fixture.get("classification") !=
               "FINITE_SEMANTIC_MODEL_NOT_ONE_MILLION_REAL_GIT_COMMITS"
            or not isinstance(families, list)
            or [(x.get("id"), x.get("bit")) for x in families] !=
               list(zip(FAULT_IDS, range(16)))):
        raise ValueError("preseed fault definitions or model authority drift")
    return doc


def _original_paths(repo: Path, sha: str) -> list[str]:
    out = git(repo, "ls-tree", "-r", "--name-only", "-z", sha)
    names = sorted(x.decode("utf-8") for x in out.split(b"\0") if x)
    if not names or len(names) != len(set(names)):
        raise ValueError("original Git census incomplete")
    return names


def analyze(repo: Path, revision: str = "HEAD", *, run_behavior: bool = False) -> dict:
    repo = Path(repo).resolve(strict=True)
    sha = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("not a pinned original Git commit")
    doc = contract_at(repo, sha)
    if BASELINE not in git(repo, "rev-list", sha).decode().splitlines():
        raise ValueError("PR41 baseline is not an ancestor")
    subjects = git(repo, "log", "--format=%s", sha).decode("utf-8")
    if not re.search(r"(?m)^Merge pull request #40\b", subjects):
        raise ValueError("actual Git does not show merged PR40")
    tree = git(repo, "rev-parse", sha + "^{tree}").decode().strip()
    files = _original_paths(repo, sha)
    original = set(files)
    names = ["README.md", "CHANGELOG.md", "AGENTS.md",
             "docs/ARCHITECTURE.md", "docs/RELEASE.md", "docs/INDEX.md"]
    documents = {name: source(repo, sha, name) for name in names}
    # PR44 is verified in actual Git ancestry; do not fossilize a PR40-only prose gate.
    architecture_era = ("merged PR36–44" if re.search(
        r"(?m)^Merge pull request #44\b", subjects) else "merged PR36–40")
    expected = {
        "CHANGELOG.md": "PR40 engineering knowledge source convergence — merged source",
        "AGENTS.md": "Knowledge-convergence gate (source-only; independent gates outstanding)",
        "docs/ARCHITECTURE.md": architecture_era,
        "docs/RELEASE.md": "Existing GitHub release draft",
        "README.md": "[final experimental DoD](.cora/contracts/dod/final-experimental-dod.json)",
        "docs/INDEX.md": "../.cora/contracts/dod/final-experimental-dod.json",
    }
    if any(text not in documents[path] for path, text in expected.items()):
        raise ValueError("current document / merged Git temporal drift")
    if "PR40 merged source knowledge" not in documents["docs/RELEASE.md"]:
        raise ValueError("current release chronology lost merged PR40")
    if "published_at=null" not in documents["docs/RELEASE.md"] or "refs/tags/v1.0.0a4" not in documents["docs/RELEASE.md"]:
        raise ValueError("release draft tag/asset observation omitted")
    banned = {
        "CHANGELOG.md": ["PR40 engineering knowledge source convergence — DRAFT, NOT MERGED"],
        "AGENTS.md": ["PR40 knowledge-convergence gate (current source candidate)"],
        "docs/ARCHITECTURE.md": ["PR39 independent-qualification source candidate"],
    }
    if any(token in documents[path] for path, tokens in banned.items() for token in tokens):
        raise ValueError("current description falsely reports unmerged source")
    if "1.0.0a4" not in documents["docs/RELEASE.md"] or (
            "BLOCKED_EXTERNAL" not in documents["docs/RELEASE.md"]):
        raise ValueError("experimental release or external boundary missing")
    changed_archive = git(repo, "diff", "--name-only", BASELINE, sha, "--",
                          "docs/archive", ".cora/assurance/history")
    if changed_archive.strip():
        raise ValueError("historical records rewritten in final baseline")
    registry = json.loads(source(repo, sha, "docs/documentation-registry.json"))
    md = {path for path in files if path.endswith(".md")}
    documented = {r["path"] for r in registry["documents"]}
    if md != documented or len(md) != 48:
        raise ValueError("markdown registry is not 100 percent complete")
    roles = json.loads(source(repo, sha, "cora.artifact-roles.json"))["rules"]
    unclassified = sorted(path for path in files if not any(
        fnmatch.fnmatchcase(path, r["pattern"]) for r in roles))
    if unclassified:
        raise ValueError("original Git file roles missing: " + repr(unclassified[:4]))
    atlas = json.loads(source(repo, sha, ".cora/assurance/capability-atlas.json"))
    syntax = ast.parse(source(repo, sha, "src/cora/cli.py"))
    parser = [n.args[0].value for n in ast.walk(syntax)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "add_parser"
              and n.args and isinstance(n.args[0], ast.Constant)
              and isinstance(n.args[0].value, str)]
    declared = {row["command"] for row in atlas["commands"]}
    if len(parser) != 71 or len(declared) != 71 or set(parser) != declared:
        raise ValueError("existing CLI owner and capability atlas disconnected")
    project = tomllib.loads(source(repo, sha, "pyproject.toml"))["project"]
    init = source(repo, sha, "src/cora/__init__.py")
    if (project.get("name") != "cora-audit" or project.get("version") not in ("1.0.0a4", "1.0.0a5")
            or f'__version__ = "{project.get("version")}"' not in init):
        raise ValueError("experimental package identity mismatch")
    if doc["release_freeze"]["stable_1_0_0"] is not False:
        raise ValueError("experimental baseline promoted to stable product")
    behavioral = {
        "execution": "NOT_EXECUTED",
        "fixture_repositories": 0,
        "cases": [],
        "independent_implementation": "NATIVE_GIT_SOURCE_ORACLE_NOT_INDEPENDENT_OPERATOR",
        "maintained_target": "BLOCKED_EXTERNAL",
    }
    if run_behavior:
        spec = importlib.util.spec_from_file_location(
            "pr41_independent_oracle", Path(__file__).with_name("independent_git_oracle.py"))
        if not spec or not spec.loader:
            raise ValueError("independent native-Git oracle missing")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Reproducible Git physical fixture hashes without changing the maintained
        # external target or the current working tree.
        fixed = {"GIT_AUTHOR_DATE": "2001-01-01T00:00:00 +0000",
                 "GIT_COMMITTER_DATE": "2001-01-01T00:00:00 +0000"}
        with patch.dict(os.environ, fixed):
            result = mod.run_reference_campaign()
        if (result.get("fixture_count") != 2 or
                result.get("product_status") != "BLOCKED_EXTERNAL" or
                result.get("authorization") != "NONE" or
                len(result.get("fixtures", [])) != 2 or
                any(x.get("status") != "MATCHED_NATIVE_GIT_REFERENCE_SCOPED"
                    for x in result["fixtures"]) or
                not result["fixtures"][0].get("previous_sha_still_replayable")):
            raise ValueError("physical behavioral reference does not match Git")
        behavioral = {
            "execution": "ACTUAL_CORA_CLI_AND_NATIVE_GIT_EXECUTED",
            "fixture_repositories": 2,
            "cases": result["fixtures"],
            "independent_implementation": "NATIVE_GIT_SOURCE_ORACLE_NOT_INDEPENDENT_OPERATOR",
            "maintained_target": "BLOCKED_EXTERNAL",
        }
    report = {
        "schema": SCHEMA, "commit": sha, "tree": tree,
        "source": "EXACT_COMMITTED_GIT_WITH_OPTIONAL_PHYSICAL_FIXTURE",
        "authority": "NONE", "public_release": "NOT_AUTHORIZED",
        "release_authorized": False, "tag_authorized": False,
        "product_status": "BLOCKED_EXTERNAL", "host_enforcement": "BLOCKED_EXTERNAL",
        "independent_review": "BLOCKED_EXTERNAL",
        "status": "SOURCE_EVIDENCE_OBSERVED_NO_EXTERNAL_PROMOTION",
        "counts": {"tracked": len(files), "markdown": len(md),
                   "declared_roles": len(files), "cli": len(parser),
                   "dod_nodes": len(doc["nodes"]), "external_nodes": len(EXTERNAL)},
        "source_checklist": sorted(expected),
        "behavior": behavioral,
        "frozen_baseline": "CORA 1.0.0a4 FINAL EXPERIMENTAL CANDIDATE",
        "required_before_release": list(EXTERNAL),
        "ci_exact_head": "NOT_ATTESTED_BY_THIS_SOURCE_PROGRAM",
        "note": "CI and real target operators must independently verify this report; a Git hash is not reviewer approval.",
    }
    report["digest"] = hashlib.sha256(canonical(report)).hexdigest()
    return report


def verify_report(repo: Path, packet: dict) -> bool:
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("invalid final experimental receipt")
    expected = analyze(repo, packet.get("commit", "INVALID"),
                       run_behavior=packet.get("behavior", {}).get("execution") ==
                       "ACTUAL_CORA_CLI_AND_NATIVE_GIT_EXECUTED")
    if packet != expected:
        raise ValueError("final experimental evidence does not replay original Git")
    return True


def _mix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK
    return x ^ (x >> 31)


def _model(mask: int) -> tuple[bool, bool, bool, bool, bool, str]:
    """Implementation under challenge, intentionally distinct from reference."""
    a = (mask & 0x000F) == 0
    b = (mask & 0x00F0) == 0
    c = (mask & 0x0F00) == 0
    d = (mask & 0xF000) == 0
    return (a, b, c, d, mask == 0, "NONE")


def _reference(mask: int) -> tuple[bool, bool, bool, bool, bool]:
    """Independent Boolean fault specification, no model invocation."""
    classes = []
    for first in (0, 4, 8, 12):
        classes.append(all(not (mask & (1 << bit))
                           for bit in range(first, first + 4)))
    return (*classes, all(classes))


def preseed_masks() -> list[int]:
    out = [0]
    for size in range(1, 5):
        for bits in itertools.combinations(range(16), size):
            out.append(sum(1 << bit for bit in bits))
    if len(out) != 2517 or len(set(out)) != len(out):
        raise ValueError("preseed not exhaustive for up-to-fourway faults")
    return out


def stress(doc: dict, *, cases: int = 1_000_000) -> dict:
    """One million finite vector evaluations; NEVER a million code mutations."""
    if cases < 2517 or cases > 1_000_000 or not isinstance(cases, int):
        raise ValueError("finite model must cover all preseed masks with a bounded budget")
    if doc.get("metrics", {}).get("semantic_cases_exact") != 1_000_000:
        raise ValueError("model DoD not pinned")
    prereg = preseed_masks()
    seen = bytearray(65536)
    distinct = mismatches = unsafe = 0
    hasher = hashlib.sha256()
    theoretical = 0
    for i in range(cases):
        if i < len(prereg):
            mask = prereg[i]
        else:
            session = min(3, i * 4 // 1_000_000)
            mask = _mix64(i ^ (SEEDS[session] << 32)) & 0xFFFF
        if not seen[mask]:
            seen[mask] = 1
            distinct += 1
        observed = _model(mask)
        reference = _reference(mask)
        if observed[:5] != reference:
            mismatches += 1
        if observed[-1] != "NONE":
            unsafe += 1
        if reference[-1]:
            theoretical += 1
        hasher.update(mask.to_bytes(2, "little"))
        hasher.update(bytes(bool(x) for x in observed[:5]))
        hasher.update(b"0" if observed[-1] == "NONE" else b"1")
    return {
        "schema": "cora-final-experimental-finite-model/1",
        "cases": cases, "sessions": 4, "seeds": list(SEEDS),
        "fault_families": len(FAULT_IDS),
        "preregistered_masks": len(prereg),
        "distinct_finite_masks": distinct,
        "mismatches": mismatches,
        "unsafe_authorizations": unsafe,
        "theoretical_fault_free_cases_not_real_authority": theoretical,
        "real_git_mutants": 0, "release_authorized": False,
        "external_gates": "BLOCKED_EXTERNAL",
        "sha256": hasher.hexdigest(),
        "status": ("PASS_BOUNDED_FINITE_MODEL" if cases == 1_000_000 and
                   mismatches == 0 and unsafe == 0 else
                   "REFUTED" if mismatches or unsafe else "PARTIAL_FINITE_MODEL"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--revision", default="HEAD")
    ap.add_argument("--run-behavior", action="store_true")
    ap.add_argument("--stress-1m", action="store_true")
    ap.add_argument("--verify-report", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        if args.verify_report:
            report = json.loads(args.verify_report.read_text("utf-8"))
            if report.get("schema") == SCHEMA:
                verify_report(args.repo, report)
                outcome = {"schema": "cora-final-experimental-replay/1",
                           "commit": report["commit"], "status": "REPLAYED_SOURCE_AND_FIXTURE",
                           "release_authorized": False, "external_gates": "BLOCKED_EXTERNAL"}
            else:
                sha = git(args.repo, "rev-parse", "--verify",
                          args.revision + "^{commit}").decode().strip()
                expected = stress(contract_at(args.repo, sha),
                                  cases=report.get("cases", 0))
                expected["commit"] = sha
                expected["tree"] = git(args.repo, "rev-parse",
                                       sha + "^{tree}").decode().strip()
                if expected != report:
                    raise ValueError("finite model stream mismatch")
                outcome = {"schema": "cora-final-experimental-model-replay/1",
                           "commit": sha,
                           "status": "REPLAYED_FINITE_MODEL_NOT_RELEASE",
                           "release_authorized": False, "external_gates": "BLOCKED_EXTERNAL"}
        else:
            basic = analyze(args.repo, args.revision,
                            run_behavior=args.run_behavior)
            if args.stress_1m:
                outcome = stress(contract_at(args.repo, basic["commit"]))
                outcome["commit"] = basic["commit"]
                outcome["tree"] = basic["tree"]
            else:
                outcome = basic
        result = json.dumps(outcome, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(result, "utf-8")
        else:
            sys.stdout.write(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError, SyntaxError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "DEBT_BLOCKED", "error": str(exc),
                          "release_authorized": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
