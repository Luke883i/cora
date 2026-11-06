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


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe independent-Git source fixture oracle")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_reference_campaign()
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
