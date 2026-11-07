"""PR39 independent-implementation source oracle for the CORA Git snapshot CLI.

Uses native Git rev-parse/ls-tree/cat-file and hashlib, not cora.git_snapshot,
evidence.make_record, or CORA's internal semantic predicates. The two generated
repos are controlled fixtures; the result is NOT a maintained external target
benchmark or an independent human/operator witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _call(args: list[str], *, cwd: Path | None = None) -> bytes:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, timeout=30, check=False)
    if proc.returncode:
        raise ValueError("bounded native Git/CLI oracle failed: " +
                         proc.stderr.decode("utf-8", "replace")[:300])
    if len(proc.stdout) > 4_000_000:
        raise ValueError("reference oracle output too large")
    return proc.stdout


def git(repo: Path, *args: str) -> bytes:
    return _call(["git", "-C", str(repo), *args])


def expected_native_git(repo: Path, rev: str = "HEAD") -> dict:
    """Separate expected results computed from git CLI and byte hashing."""
    commit = git(repo, "rev-parse", rev).decode().strip()
    rows = {}
    listing = git(repo, "ls-tree", "-rz", "--full-tree", commit)
    for line in listing.split(b"\0"):
        if not line:
            continue
        hdr, rawpath = line.split(b"\t", 1)
        mode, kind, oid = hdr.decode("ascii").split(" ")
        name = rawpath.decode("utf-8")
        if mode in ("100644", "100755"):
            content = git(repo, "cat-file", "blob", oid)
            if content.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                status, size, digest = "lfs_pointer_unresolved", None, None
            else:
                status, size, digest = ("observed_git_blob", len(content),
                                         hashlib.sha256(content).hexdigest())
        elif mode == "120000":
            status, size, digest = "symlink_unresolved", None, None
        else:
            raise ValueError("fixture unexpectedly includes gitlink or unknown mode")
        rows[name] = {"mode": mode, "git_oid": oid,
                      "status": status, "size": size, "sha256": digest}
    return {"commit": commit, "records": rows}


def observe_cora_cli(repo: Path, commit: str) -> dict:
    raw = _call([sys.executable, "-m", "cora.cli", "snapshot", str(repo),
                 "--revision", commit])
    report = json.loads(raw)
    if report.get("commit") != commit:
        raise ValueError("CORA returned wrong reference commit")
    return {"commit": report["commit"],
            "records": {x["path"]: {key: x[key] for key in
                        ("mode", "git_oid", "status", "size", "sha256")}
                        for x in report["records"]}}


def compare_expected(expected: dict, observed: dict) -> dict:
    if expected != observed:
        exp, obs = expected.get("records", {}), observed.get("records", {})
        missing = sorted(set(exp) - set(obs))
        extra = sorted(set(obs) - set(exp))
        mismatched = sorted(k for k in set(exp) & set(obs) if exp[k] != obs[k])
        raise ValueError("independent Git reference disagreement: " +
                         json.dumps({"commit_mismatch":
                                     expected.get("commit") != observed.get("commit"),
                                     "missing": missing, "extra": extra,
                                     "mismatched": mismatched}, sort_keys=True))
    return {"case_count": len(expected["records"]),
            "status": "MATCHED_NATIVE_GIT_REFERENCE_SCOPED",
            "release_authorized": False}


def _fixture(root: Path, variant: int) -> tuple[Path, str]:
    repo = root / ("target-" + str(variant))
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oracle@example.invalid")
    git(repo, "config", "user.name", "Native-Git Reference")
    if variant == 1:
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("print('CORA test')\n", "utf-8")
        (repo / "space file.txt").write_bytes(b"first line\nsecond line\n")
        (repo / "binary.dat").write_bytes(bytes(range(32)))
        script = repo / "run.sh"
        script.write_text("#!/bin/sh\nexit 0\n", "utf-8")
        script.chmod(0o755)
        (repo / ".gitattributes").write_text("*.dat binary\n", "utf-8")
    elif variant == 2:
        (repo / "pkg").mkdir()
        (repo / "pkg" / "a.py").write_text("X = 1\n", "utf-8")
        (repo / "README.md").write_text("# fixture\n", "utf-8")
        (repo / "pointer.txt").write_bytes(
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + b"a" * 64 + b"\nsize 4\n")
        try:
            (repo / "readme-link").symlink_to("README.md")
        except (NotImplementedError, OSError):
            raise RuntimeError("symlink fixture unavailable; never silently skip it")
    else:
        raise ValueError("unexpected fixture variant")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "independent controlled fixture")
    return repo, git(repo, "rev-parse", "HEAD").decode().strip()


def run_reference_campaign() -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix="cora-pr39-oracle-") as tmp:
        for variant in (1, 2):
            repo, sha = _fixture(Path(tmp), variant)
            expected = expected_native_git(repo, sha)
            observed = observe_cora_cli(repo, sha)
            verdict = compare_expected(expected, observed)
            # Real committed second revision prevents working-tree inference.
            if variant == 1:
                with (repo / "src" / "main.py").open("a", encoding="utf-8") as f:
                    f.write("print('second commit')\n")
                git(repo, "add", ".")
                git(repo, "commit", "-qm", "second revision oracle")
                verdict["previous_sha_still_replayable"] = (
                    compare_expected(expected, observe_cora_cli(repo, sha))["status"] ==
                    "MATCHED_NATIVE_GIT_REFERENCE_SCOPED")
            results.append({"fixture": variant, "commit": sha, **verdict})
    packet = {
        "schema": "cora-independent-git-reference/1",
        "implementation": "NATIVE_GIT_CLI_SEPARATE_FROM_CORA_SOURCE",
        "fixtures": results, "fixture_count": len(results),
        "scope": "TWO_SYNTHETIC_GIT_REPOSITORIES_NOT_EXTERNAL_MAINTAINED_TARGETS",
        "independent_owners": "NOT_ATTESTED",
        "host_attestation": "NONE",
        "product_status": "BLOCKED_EXTERNAL",
        "authorization": "NONE",
    }
    packet["sha256"] = hashlib.sha256(
        json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return packet



# PR44: independent *implementation* of the PR43 obligation-delta comparator.
# It uses native Git directly; this does not authenticate a separate human owner.
def native_dod_nodes(repo: Path, revision: str) -> dict:
    commit = git(repo, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    paths = git(repo, "ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    contracts = sorted(p for p in paths if p.startswith(".cora/contracts/dod/")
                       and p.endswith(".json") and "/" not in p[len(".cora/contracts/dod/"):])
    if not contracts:
        raise ValueError("no original-Git DoD documents found")
    results = {}
    for path in contracts:
        document = json.loads(git(repo, "show", commit + ":" + path))
        rows = document.get("nodes")
        if not isinstance(rows, list) or not rows:
            raise ValueError("malformed canonical DoD nodes")
        for item in rows:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError("malformed canonical DoD identity")
            key = path + "::" + item["id"]
            if key in results:
                raise ValueError("duplicate canonical DoD identity")
            deps = item.get("depends_on", [])
            if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
                raise ValueError("malformed canonical DoD dependencies")
            claim = ""
            for field in ("claim", "description", "title", "family"):
                if isinstance(item.get(field), str) and item[field].strip():
                    claim = item[field].strip()
                    break
            scope = item.get("scope", "UNCLASSIFIED")
            if not isinstance(scope, str):
                raise ValueError("malformed canonical DoD scope")
            results[key] = {
                "scope": scope, "status": str(item.get("status", "NOT_ASSERTED")),
                "depends_on": sorted(deps), "claim": claim, "source_path": path}
    return {"commit": commit, "contracts": contracts, "nodes": results}


def independent_closure_challenge(repo: Path, record: dict) -> dict:
    """Recalculate EVERY claimed count without calling the CORA producer."""
    if not isinstance(record, dict) or record.get("schema") != "cora-obligation-delta/1":
        raise ValueError("foreign or missing closure receipt schema")
    if record.get("authority") != "NONE" or record.get("product") != "BLOCKED_EXTERNAL":
        raise ValueError("source receipt cannot assert host or product approval")
    if record.get("release_authorized") is not False:
        raise ValueError("source receipt cannot authorize release")
    if record.get("qualification") != "ACCOUNTING_ONLY_NOT_INDEPENDENT_EVIDENCE":
        raise ValueError("scope of proof was promoted")
    start = native_dod_nodes(repo, record["base"])
    end = native_dod_nodes(repo, record["head"])
    if start["commit"] != record["base"] or end["commit"] != record["head"]:
        raise ValueError("receipt does not pin complete commit identities")
    if start["commit"] == end["commit"]:
        raise ValueError("no actual revision delta")
    # git merge-base --is-ancestor does not return stdout and must be checked.
    proc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                           start["commit"], end["commit"]],
                          capture_output=True, timeout=30)
    if proc.returncode:
        raise ValueError("unrelated or reverse Git ancestry")
    before, after = start["nodes"], end["nodes"]
    keys0, keys1 = set(before), set(after)
    changed = sorted(k for k in keys0 & keys1 if before[k] != after[k])
    removed = sorted(keys0 - keys1)
    added = sorted(keys1 - keys0)
    unsafe = sorted(k for k in keys0 & keys1
                    if before[k]["scope"] == "EXTERNAL" and after[k]["scope"] != "EXTERNAL")
    asserted = sorted(k for k in keys1
                      if after[k]["status"].upper().startswith(("PASS", "APPROV", "CLOSED", "ACCEPT"))
                      and (k not in keys0 or before[k]["status"] != after[k]["status"]))
    repeated = {}
    for key, node in after.items():
        value = " ".join(node["claim"].lower().split())
        if value:
            repeated.setdefault(value, []).append(key)
    aliases = [{"claims": sorted(ids), "phrase": phrase}
               for phrase, ids in sorted(repeated.items()) if len(ids) > 1]
    expected = {
        "before_occurrences": len(keys0), "after_occurrences": len(keys1),
        "contract_growth": len(end["contracts"]) - len(start["contracts"]),
        "obligation_occurrence_growth": len(keys1) - len(keys0),
        "added": added, "removed_not_closed": removed, "changed": changed,
        "external_scope_promotions": unsafe, "asserted_passes_not_verified": asserted,
        "possible_duplicate_wording_not_merged": aliases,
        "external_open_occurrences": sum(x["scope"] == "EXTERNAL" for x in after.values()),
        "verified_closures": 0, "closure_yield": None,
        "identity_boundary": "PATH_PLUS_NODE_ID; cross-contract meaning requires independent equivalence mapping",
        "evidence_boundary": "NO_INDEPENDENT_RUNTIME_OR_HOST_RECEIPTS_VALIDATED",
    }
    if record.get("counts") != expected:
        raise ValueError("independent original-Git counts disagree with submitted report")
    expected_status = "REFUTED" if unsafe else "PASS_SCOPED_ACCOUNTING"
    if record.get("status") != expected_status:
        raise ValueError("reported gate status contradicts native Git")
    return {
        "schema": "cora-independent-closure-challenge/1",
        "base": start["commit"], "head": end["commit"],
        "checked_node_occurrences": len(after),
        "status": "REFUTED" if unsafe else "MATCHED_NATIVE_GIT_SOURCE_ONLY",
        "source_impl_independent": True,
        "operator_independence": "NOT_ATTESTED",
        "host_rules": "NOT_ATTESTED",
        "product": "BLOCKED_EXTERNAL",
        "authority": "NONE", "release_authorized": False,
    }


def reviewer_brief(report: dict, challenge: dict) -> str:
    """Three-task explanation generated from independently recomputed counts."""
    counts = report["counts"]
    if challenge["head"] != report["head"]:
        raise ValueError("mixed-commit reviewer pack")
    lines = [
        "# Review CORA changes without knowing CORA vocabulary",
        "",
        "This packet is a local source comparison, NOT a product certificate.",
        "Recomputed reference: native Git (different implementation; same repository owner not independent person).",
        "Base commit: `" + report["base"] + "`",
        "Compared commit: `" + report["head"] + "`",
        "",
        "## Task 1 — What changed?",
        "Recorded requirement occurrences before: " + str(counts["before_occurrences"]),
        "Recorded requirement occurrences after: " + str(counts["after_occurrences"]),
        "New occurrences: " + str(len(counts["added"])),
        "Removed occurrences (NOT completed requirements): " + str(len(counts["removed_not_closed"])),
        "Changed occurrences: " + str(len(counts["changed"])),
        "Potential duplicate wording (NOT semantic equivalence): " + str(len(counts["possible_duplicate_wording_not_merged"])),
        "",
        "## Task 2 — What has actually been demonstrated?",
        "Git content and counters were recalculated by a separate implementation.",
        "Actual independent closures proved by this packet: ZERO.",
        "Claimed PASS statuses without independent verification: " + str(len(counts["asserted_passes_not_verified"])),
        "A Git hash proves source identity, not runtime behavior or who reviewed it.",
        "External review, real targets, user comprehension and host protection remain unverified.",
        "",
        "## Task 3 — How could I refute it?",
        "Check the stated base/head using native git and inspect any changed DoD.",
        "Change a count or the product status in the JSON and re-run the native-Git challenge.",
        "For each promised product behavior, demand a separately preregistered real-world test.",
        "Reject a removed requirement as 'closed'; demand an accountable non-author decision.",
        "",
        "## Final disposition",
        "Native Git source challenge: " + challenge["status"],
        "Product acceptance: BLOCKED_EXTERNAL; no merge, release or host authorization.",
        "A meaningful comprehension test requires unfamiliar, observed human participants.",
        "",
    ]
    return "\n".join(lines)



def main() -> int:
    parser = argparse.ArgumentParser(description="Safe independent-Git source fixture oracle")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--closure-report", type=Path, help="independently re-evaluate PR43 source accounting")
    parser.add_argument("--reader-brief", type=Path, help="plain-English three-task review guide")
    args = parser.parse_args()
    if args.closure_report:
        report = json.loads(args.closure_report.read_text("utf-8"))
        result = independent_closure_challenge(args.repo, report)
        if args.reader_brief:
            args.reader_brief.write_text(reviewer_brief(report, result), encoding="utf-8")
    else:
        if args.reader_brief:
            raise ValueError("--reader-brief requires --closure-report")
        result = run_reference_campaign()
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 2 if result.get('status') == 'REFUTED' else 0


if __name__ == "__main__":
    raise SystemExit(main())
