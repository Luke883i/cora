"""PR39 independent-product-qualification boundary above existing One-Run.

No source-only program can independently certify its own reviewer, host settings,
runtime isolation, user-study results or production target accuracy. This module
replays bounded Git-defined qualifications and fails closed at those boundaries.
It never executes target code, calls GitHub, or authorizes release.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .evidence import domain_hash
from .git_snapshot import git

SCHEMA = "cora-independent-qualification/1"
CONTRACT_SCHEMA = "cora-independent-qualification-dod/1"
CONTRACT = ".cora/contracts/dod/independent-qualification-dod.json"
BASE = "324bc2d44d291f2256f354d2f2837e2ff2e62b52"
FAMILIES = ("BEHAVIOR", "USABILITY", "ISOLATION", "GOVERNANCE")
SOURCE = {
    "BEHAVIOR": ("S_B1_INDEPENDENT_GIT_ORACLE", "S_B2_TWO_REAL_GIT_FIXTURES",
                 "S_B3_NEGATIVE_REFERENCE_MUTANTS", "S_B4_COVERAGE_BOUNDARY"),
    "USABILITY": ("S_U1_TASK_SCRIPT", "S_U2_COMPLETION_METRICS",
                  "S_U3_ZERO_FALSE_PROMOTION", "S_U4_PILOT_DATA_VALIDATOR"),
    "ISOLATION": ("S_I1_DENY_BY_DEFAULT", "S_I2_PINNED_MINIMAL_DOCKER_PLAN",
                  "S_I3_TIMEOUT_TEARDOWN_DEBT", "S_I4_NO_SANDBOX_SELF_ATTEST"),
    "GOVERNANCE": ("S_G1_REQUIRED_CHECK_CENSUS", "S_G2_HOST_READBACK_AUTHORITY",
                   "S_G3_INDEPENDENT_REVIEW_IDENTITIES",
                   "S_G4_RELEASE_AND_ROLLBACK_DENY"),
}
EXTERNAL = {
    "BEHAVIOR": ("E_B1_MAINTAINED_EXTERNAL_TARGET", "E_B2_DISTINCT_OWNER_ORACLE"),
    "USABILITY": ("E_U1_REAL_USERS_TWO_PERSONAS", "E_U2_INDEPENDENT_OBSERVER"),
    "ISOLATION": ("E_I1_HOST_POLICY_ATTESTATION", "E_I2_NEGATIVE_ESCAPE_AND_KILL_TEST"),
    "GOVERNANCE": ("E_G1_VERIFIED_REQUIRED_CHECKS",
                   "E_G2_REVIEW_AND_RELEASE_AUTHORITY"),
}
GOAL = "G_PRODUCT_INDEPENDENT_QUALIFICATION"
SHA = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
HASH = re.compile(r"^[a-f0-9]{64}$")
# File witnesses prove presence in a Git tree, not successful execution.
WITNESSES = {
    "BEHAVIOR": (
        "tools/independent_git_oracle.py", "tests/test_pr39_qualification.py",
        "tools/external_validate.py"),
    "USABILITY": (
        "docs/RELEASE.md",
        "tests/test_pr39_qualification.py"),
    "ISOLATION": (
        "src/cora/runtime_observation.py", "tests/test_pr16_runtime_fusion.py",
        "tests/test_pr39_qualification.py"),
    "GOVERNANCE": (
        ".github/workflows/ci-one-run-integrated.yml",
        "docs/RELEASE.md",
        "tests/test_pr39_qualification.py"),
}


def _git_text(repo: Path, sha: str, path: str) -> str:
    if not path or ".." in path.split("/") or not re.fullmatch(r"[\w./-]+", path):
        raise ValueError("unsafe qualification Git path")
    blob = git(repo, "show", sha + ":" + path, max_output=64_000)
    return blob.decode("utf-8")


def _tree_paths(repo: Path, sha: str) -> set[str]:
    raw = git(repo, "ls-tree", "-r", "-z", "--name-only", sha,
              max_output=16_000_000)
    return {p.decode("utf-8") for p in raw.split(b"\0") if p}


def verify_contract(doc: dict) -> bool:
    """Frozen semantics: no loss or scope relaxation of a mandatory gate."""
    if (not isinstance(doc, dict)
            or doc.get("schema") != CONTRACT_SCHEMA
            or doc.get("authority") != "NONE"
            or doc.get("source_baseline") != BASE
            or doc.get("product_status") != "BLOCKED_EXTERNAL"
            or doc.get("source_status") != "IMPLEMENTATION_CANDIDATE_UNVERIFIED"
            or doc.get("semantics") != "ALL_FOUR_MANDATORY_GATES_NONCOMPENSATORY"
            or doc.get("one_run_contract") !=
               "PRESERVE_EXISTING_PROCESS_RUN_NO_SECOND_ORCHESTRATOR"
            or doc.get("global_goal") != GOAL
            or doc.get("source") != {k: list(v) for k, v in SOURCE.items()}
            or doc.get("external") != {k: list(v) for k, v in EXTERNAL.items()}):
        raise ValueError("qualification DoD authority, boundary or scope altered")
    nodes = doc.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 29:
        raise ValueError("qualification DoD node count altered")
    lookup = {n.get("id"): n for n in nodes if isinstance(n, dict)}
    if len(lookup) != len(nodes):
        raise ValueError("duplicate qualification DoD identity")
    expected = set(sum((list(v) for v in SOURCE.values()), []) +
                   sum((list(v) for v in EXTERNAL.values()), []) +
                   ["G_" + k for k in FAMILIES] + [GOAL])
    if set(lookup) != expected:
        raise ValueError("missing or extra qualification gate")
    for family in FAMILIES:
        for name in SOURCE[family]:
            if (lookup[name].get("scope") != "SOURCE" or
                    lookup[name].get("state") != "SOURCE_WITNESS_REQUIRED" or
                    lookup[name].get("depends_on") != []):
                raise ValueError("source qualification witness scope altered")
        for name in EXTERNAL[family]:
            if (lookup[name].get("scope") != "EXTERNAL" or
                    lookup[name].get("state") != "BLOCKED_EXTERNAL" or
                    lookup[name].get("depends_on") != []):
                raise ValueError("external qualification witness promoted")
        node = lookup["G_" + family]
        if (node.get("scope") != "EXTERNAL" or
                node.get("state") != "BLOCKED_EXTERNAL" or
                node.get("depends_on") != list(SOURCE[family] + EXTERNAL[family])):
            raise ValueError("qualification mandatory edge removed")
    goal = lookup[GOAL]
    if (goal.get("scope") != "EXTERNAL" or
            goal.get("state") != "BLOCKED_EXTERNAL" or
            goal.get("depends_on") != ["G_" + k for k in FAMILIES]):
        raise ValueError("product goal edge or scope promoted")
    thresholds = doc.get("requirements", {})
    if (thresholds.get("BEHAVIOR", {}).get("minimum_real_targets") != 2
            or thresholds.get("BEHAVIOR", {}).get("minimum_independent_oracle_owners") != 1
            or thresholds.get("BEHAVIOR", {}).get("critical_false_passes") != 0
            or thresholds.get("USABILITY", {}).get("minimum_participants") != 8
            or thresholds.get("USABILITY", {}).get("minimum_repositories") != 2
            or thresholds.get("USABILITY", {}).get("independent_observer") is not True
            or thresholds.get("USABILITY", {}).get("task_completion_min_ratio") != 0.8
            or thresholds.get("USABILITY", {}).get("critical_proof_misclassifications") != 0
            or thresholds.get("ISOLATION", {}).get("host_attestation") is not True
            or thresholds.get("ISOLATION", {}).get("negative_host_tests") is not True
            or thresholds.get("ISOLATION", {}).get("teardown_verified") is not True
            or thresholds.get("GOVERNANCE", {}).get("host_authority_verified") is not True
            or thresholds.get("GOVERNANCE", {}).get("reviewer_independent") is not True
            or thresholds.get("GOVERNANCE", {}).get("rollback_drill") is not True
            or doc.get("source_falsification", {}).get("cases") != 10000):
        raise ValueError("qualification numerical or host threshold weakened")
    return True


def build_qualification(repo: Path, revision: str = "HEAD") -> dict:
    """Only exact Git source witnesses are observed; external gates never pass."""
    repo = Path(repo).resolve(strict=True)
    sha = git(repo, "rev-parse", "--verify", "--end-of-options",
              revision + "^{commit}", max_output=128).decode().strip()
    if not SHA.fullmatch(sha):
        raise ValueError("invalid qualification revision")
    tree = git(repo, "rev-parse", sha + "^{tree}", max_output=128).decode().strip()
    doc = json.loads(_git_text(repo, sha, CONTRACT))
    verify_contract(doc)
    entries = _tree_paths(repo, sha)
    sections = []
    for family in FAMILIES:
        declared = WITNESSES[family]
        found = sorted(set(declared) & entries)
        missing = sorted(set(declared) - entries)
        sections.append({
            "gate": "G_" + family, "family": family,
            "source_obligations": list(SOURCE[family]),
            "external_obligations": list(EXTERNAL[family]),
            "source_witness_paths": found,
            "missing_source_paths": missing,
            "source_observation": ("SOURCE_WITNESSES_PRESENT_NOT_EXECUTED" if not missing
                                   else "DEBT_BLOCKED_SOURCE_WITNESSES_MISSING"),
            "independent_evidence": "NOT_OBSERVED",
            "state": "BLOCKED_EXTERNAL", "release_authorized": False,
            "next_action": {
                "BEHAVIOR": "Run native Git oracle plus independently-owned maintained-target reference and compare per-case differences.",
                "USABILITY": "Have separate operator observe eight real participants on two repositories, with no proof-level misclassification.",
                "ISOLATION": "Have host administrator attest containment, kill/timeout and denied network/filesystem/secret access in an isolated environment.",
                "GOVERNANCE": "Read back main branch rules/required checks with host-authorized account, verify reviewers and perform rollback drill."
            }[family],
        })
    packet = {
        "schema": SCHEMA, "commit": sha, "tree": tree,
        "contract_schema": CONTRACT_SCHEMA,
        "source_status": ("SOURCE_WITNESSES_PRESENT_NOT_EXECUTED"
                          if all(not x["missing_source_paths"] for x in sections)
                          else "DEBT_BLOCKED_SOURCE_WITNESSES_MISSING"),
        "product_status": "BLOCKED_EXTERNAL", "authorization": "NONE",
        "release_authorized": False,
        "gates": sections, "gate_count": 4, "external_gates_unclosed": 4,
        "independent_target_count": 0, "human_usability_participants_observed": 0,
        "runtime_host_attestation": "NOT_OBSERVED",
        "host_required_checks": "NOT_OBSERVED",
        "failure_on_missing_external": True,
        "evidence_boundary": ("SOURCE_GIT_WITNESS_PATHS_NOT_INDEPENDENT_EXECUTION_"
                              "USABILITY_ISOLATION_OR_HOST_GOVERNANCE"),
    }
    packet["receipt_digest"] = domain_hash("CORA:independent-qualification:1", packet)
    return packet


def verify_qualification(repo: Path, receipt: dict) -> bool:
    if (not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA
            or receipt.get("product_status") != "BLOCKED_EXTERNAL"
            or receipt.get("authorization") != "NONE"
            or receipt.get("release_authorized") is not False
            or receipt.get("external_gates_unclosed") != 4):
        raise ValueError("self-qualified external product claim is forbidden")
    if receipt != build_qualification(repo, receipt["commit"]):
        raise ValueError("qualification original Git witness replay mismatch")
    return True



def evaluate_paired_work(packet: dict, commit: str) -> dict:
    """PR56 blinded crossover arithmetic; never authentication of real subjects.

    The user study must be pre-registered externally and observed by an
    independent facilitator. Supplied measurements are untrusted assertions.
    """
    if (not isinstance(packet, dict) or
            set(packet) != {"schema", "subject_commit", "protocol", "participants"} or
            packet["schema"] != "cora-pr56-paired-work/1" or
            packet["protocol"] != "CROSSOVER_AB_BA_EIGHT_TWO_REPOSITORIES" or
            packet["subject_commit"] != commit or not SHA.fullmatch(str(commit))):
        raise ValueError("PR56 crossover identity or preregistered protocol drift")
    users = packet["participants"]
    if not isinstance(users, list) or not 8 <= len(users) <= 100:
        raise ValueError("PR56 participant count outside preregistered limits")
    seen, personas, repositories, sequences = set(), set(), set(), []
    totals = {"baseline": 0.0, "cora": 0.0}
    complete = {"baseline": 0, "cora": 0}
    critical = {"baseline": 0, "cora": 0}
    for user in users:
        if (not isinstance(user, dict) or
                set(user) != {"participant_id", "persona", "repo_id",
                              "sequence", "arms"}):
            raise ValueError("PR56 incomplete participant or arm envelope")
        pid, persona, rid = (user["participant_id"], user["persona"], user["repo_id"])
        if (not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", pid)
                or pid in seen
                or persona not in ("first_time_developer", "independent_assurance_reviewer")
                or rid not in ("teddy", "ictc")
                or user["sequence"] not in ("baseline-cora", "cora-baseline")
                or not isinstance(user["arms"], list)
                or len(user["arms"]) != 2):
            raise ValueError("PR56 wrong participant identity, persona or target")
        seen.add(pid); personas.add(persona); repositories.add(rid)
        sequences.append(user["sequence"])
        expected = user["sequence"].split("-")
        if [x.get("arm") for x in user["arms"] if isinstance(x, dict)] != expected:
            raise ValueError("PR56 unbalanced or duplicated trial arm")
        for x in user["arms"]:
            if (not isinstance(x, dict) or set(x) != {
                    "arm", "setup_minutes", "execution_minutes", "review_minutes",
                    "task_completed", "critical_false_passes"} or
                    type(x["task_completed"]) is not bool or
                    type(x["critical_false_passes"]) is not int or
                    not 0 <= x["critical_false_passes"] <= 10):
                raise ValueError("PR56 missing cost segment or false-pass measurement")
            times = [x[y] for y in (
                "setup_minutes", "execution_minutes", "review_minutes")]
            if any(type(t) not in (int, float) or not 0 <= t <= 120
                   for t in times):
                raise ValueError("PR56 invalid or non-finite observed task time")
            if not 0 < sum(times) <= 240:
                raise ValueError("PR56 impossible completed trial duration")
            arm = x["arm"]
            totals[arm] += sum(times)
            complete[arm] += int(x["task_completed"])
            critical[arm] += x["critical_false_passes"]
    if (len(repositories) != 2 or len(personas) != 2 or
            any(sum(1 for u in users if u["persona"] == p) < 4
                for p in personas) or
            min(sequences.count("baseline-cora"),
                sequences.count("cora-baseline")) < 4):
        raise ValueError("PR56 crossover lacks personas, targets or balanced arm order")
    n = len(users)
    return {
        "schema": "cora-pr56-paired-work-analysis/1", "subject_commit": commit,
        "participant_count_supplied": n,
        "two_original_target_ids_supplied": sorted(repositories),
        "reported_completions": complete, "reported_critical_false_passes": critical,
        "reported_total_minutes": {k: round(v, 5) for k, v in totals.items()},
        "reported_cora_minus_baseline_minutes": round(totals["cora"] - totals["baseline"], 5),
        "reported_cora_to_baseline_cost_ratio": round(
            totals["cora"] / totals["baseline"], 5),
        "reported_cora_completion_fraction": round(complete["cora"] / n, 5),
        "numerical_criterion": ("MET_IN_SUBMITTED_DATA"
            if complete["cora"] / n >= 0.8 and critical["cora"] == 0 else "NOT_MET"),
        "causal_superiority_proven": False,
        "subject_identity_authenticated": False,
        "independent_observer_authenticated": False,
        "operator_review": "NOT_ATTESTED",
        "measurement_scope": "UNVERIFIED_HUMAN_SUPPLIED_CROSSOVER_VALUES",
        "product_status": "BLOCKED_EXTERNAL", "authorization": "NONE",
    }


def evaluate_study_packet(packet: dict, commit: str) -> dict:
    """A bounded usability *analysis*, never independent identity attestation.

    Participants and measurements are assertions from a supplied file. Operators
    must independently verify their identities, timestamps, repo access, consent,
    recordings and interpretation before any external acceptance.
    """
    if not isinstance(packet, dict) or packet.get("schema") != "cora-usability-pilot/1":
        raise ValueError("invalid study schema")
    if packet.get("subject_commit") != commit or not SHA.fullmatch(str(commit)):
        raise ValueError("study and source commit differ")
    users = packet.get("participants")
    if not isinstance(users, list) or len(users) > 100:
        raise ValueError("invalid study participants")
    seen = set()
    completed = 0
    repo_ids = set()
    personas = set()
    critical = 0
    total = 0
    for row in users:
        if (not isinstance(row, dict) or set(row) !=
                {"participant_id", "persona", "repo_id", "tasks", "minutes"}
                or not isinstance(row["participant_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", row["participant_id"])
                or row["participant_id"] in seen
                or row["persona"] not in ("first_time_developer",
                                          "independent_assurance_reviewer")
                or not isinstance(row["repo_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{2,64}", row["repo_id"])
                or type(row["minutes"]) not in (int, float)
                or not 0 <= row["minutes"] <= 240
                or not isinstance(row["tasks"], list)
                or not 3 <= len(row["tasks"]) <= 10):
            raise ValueError("invalid study participant or duplicated identity")
        seen.add(row["participant_id"])
        repo_ids.add(row["repo_id"])
        personas.add(row["persona"])
        task_ids = [task.get("task_id") for task in row["tasks"] if isinstance(task, dict)]
        if (len(set(task_ids)) != len(row["tasks"]) or
                not {"start_one_run", "trace_lineage", "explain_blocked"}.issubset(task_ids)):
            raise ValueError("missing or duplicated required usability task")
        for task in row["tasks"]:
            if (not isinstance(task, dict) or
                    set(task) != {"task_id", "completed", "proof_misclassified"}
                    or not isinstance(task["task_id"], str)
                    or type(task["completed"]) is not bool
                    or type(task["proof_misclassified"]) is not bool):
                raise ValueError("invalid usability task evidence")
            completed += int(task["completed"])
            critical += int(task["proof_misclassified"])
            total += 1
    ratio = completed / total if total else 0.0
    criteria_met = (len(seen) >= 8 and len(repo_ids) >= 2 and
                    len(personas) == 2 and ratio >= 0.8 and critical == 0 and
                    all(row["minutes"] <= 20 for row in users))
    return {
        "schema": "cora-usability-pilot-analysis/1", "subject_commit": commit,
        "participant_count_reported": len(seen), "repo_count_reported": len(repo_ids),
        "personas_reported": sorted(personas),
        "task_count": total, "completion_ratio": round(ratio, 5),
        "critical_proof_misclassifications": critical,
        "numerical_threshold": "MET_IN_SUPPLIED_DATA" if criteria_met else "NOT_MET",
        "identity_observation": "UNAUTHENTICATED_SUBMITTED_DATA",
        "independent_usability_accepted": False,
        "product_status": "BLOCKED_EXTERNAL",
        "authority": "NONE",
    }
