"""Git-bound source evidence for the PR-21 documentation DoD.

This is a bounded independent source-oracle *candidate*, not a semantic theorem,
a behavioral test runner, or an attestation of CI, human review or hosting.
The proof contract is PR-editable, so its claims have no approval authority.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import posixpath
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from cora.reticulum import ordered_cut

SCHEMA = "cora-documentation-proof-receipt/1"
PROFILE = "cora.documentation-proofs.json"
BASELINE = "d8b75df872c1603597550bebfb8c331c565aa7f9"
DOCUMENT_BASELINE = "ee6da7625dae1e4101e06eb979a348610f39093b"
PREDICATES = (
    "product-frontdoor", "ontology", "agent-boundary", "first-use",
    "agent-adoption", "nonpromotion", "navigation", "registry",
    "precedence", "historical-authority", "cli-coverage", "intent-replay",
    "source-verifier", "governance-truth", "negative-oracles",
    "alpha-boundary", "baseline-preserved", "reader-route",
)
CRITICAL = (
    (r"\bCORA\s+(?:is|acts as|functions as)\s+(?:an?\s+)?(?:autonomous\s+)?coding agent\b",
     "CODING_AGENT_PROMOTION"),
    (r"\bCORA automatically deletes (?:source |unused )?code\b",
     "AUTOMATIC_DELETION_PROMOTION"),
    (r"\bCORA (?:authenticates|certifies) (?:independent )?reviewer(?:s| identities)?\b",
     "REVIEWER_AUTHORITY_PROMOTION"),
    (r"\bCORA (?:automatically|implicitly) runs (?:the |target )?tests\b",
     "IMPLICIT_TEST_PROMOTION"),
    (r"\bCORA is a stable API\b", "STABLE_API_PROMOTION"),
    (r"\bCORA (?:is|has) (?:a )?published (?:stable |public )?release\b",
     "PUBLISHED_RELEASE_PROMOTION"),
    (r"\bCORA (?:already )?enforces (?:protected |required )?(?:branch|main|reviews)\b",
     "HOST_ENFORCEMENT_PROMOTION"),
    (r"\b(?:10 million|ten million|10M) real (?:source )?mutants\b",
     "MODEL_VOLUME_PROMOTION"),
)
REQUIRED = (
    "README.md", "docs/INDEX.md", "docs/DOCUMENTATION_DOD.md",
    "docs/CLI_REFERENCE.md", "docs/documentation-registry.json",
    "docs/GETTING_STARTED.md", "docs/AGENT_ADOPTION.md",
    "docs/CONVERGENT_ASSURANCE.md", "docs/ARCHITECTURE.md",
    "docs/RELEASE.md", "CHANGELOG.md", "GOVERNANCE.md", "AGENTS.md",
    ".cora/continuous-policy.json", ".cora/layout-migration.json",
    ".github/workflows/ci-documentation.yml",
    ".github/workflows/ci-convergence.yml",
    "src/cora/cli.py", "src/cora/continuous.py", "src/cora/reticulum.py",
    "src/cora/__init__.py", "tools/verify_documentation.py",
    "cora.ontology.json", "cora.documentation-dod.json", "pyproject.toml",
)


class SourceStore:
    """Bounded Git object access; a worktree edit cannot change a HEAD witness."""

    def __init__(self, repo: Path, revision: str):
        self.repo = Path(repo).resolve(strict=True)
        self.calls = 0
        self.sha = self.run("rev-parse", "--verify", "--end-of-options",
                            revision + "^{commit}").decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", self.sha):
            raise ValueError("invalid source SHA")
        self.tree = self._tree(self.sha)
        self.baseline_tree = self._tree(BASELINE)
        self.document_baseline_tree = self._tree(DOCUMENT_BASELINE)
        self.bytes_by_path: dict[str, bytes] = {}

    def run(self, *cmd: str, input_data: bytes | None = None) -> bytes:
        self.calls += 1
        result = subprocess.run(["git", "-C", str(self.repo), *cmd],
                                input=input_data, capture_output=True,
                                timeout=75, check=False)
        if result.returncode:
            raise ValueError("git-source-unavailable:" + " ".join(cmd[:2]))
        if len(result.stdout) > 32 * 1024 * 1024:
            raise ValueError("git-output-exceeds-budget")
        return result.stdout

    def _tree(self, commit: str) -> dict[str, tuple[str, str]]:
        raw = self.run("ls-tree", "-rz", "--full-tree", commit)
        items = {}
        for entry in raw.split(b"\0"):
            if not entry:
                continue
            head, name = entry.split(b"\t", 1)
            mode, kind, oid = head.decode("ascii").split(" ")
            path = name.decode("utf-8")
            if path in items:
                raise ValueError("duplicate-git-path")
            items[path] = (mode, oid if kind == "blob" else "")
        return items

    def read(self, paths: set[str]) -> None:
        missing = paths - set(self.tree)
        if missing:
            raise ValueError("missing-evidence:" + ",".join(sorted(missing)))
        targets = {}
        for path in sorted(paths):
            mode, oid = self.tree[path]
            if mode not in ("100644", "100755") or not oid:
                raise ValueError("nonregular-evidence:" + path)
            targets[oid] = None
        oids = sorted(targets)
        stream = self.run("cat-file", "--batch",
                          input_data=("".join(x + "\n" for x in oids)).encode("ascii"))
        offset = 0
        for oid in oids:
            eol = stream.index(b"\n", offset)
            header = stream[offset:eol].decode("ascii").split()
            if len(header) != 3 or header[0] != oid or header[1] != "blob":
                raise ValueError("incorrect-batch-object")
            size = int(header[2])
            if size < 0 or size > 8 * 1024 * 1024:
                raise ValueError("evidence-blob-too-large")
            start = eol + 1
            if stream[start + size:start + size + 1] != b"\n":
                raise ValueError("invalid-batch-framing")
            targets[oid] = stream[start:start + size]
            offset = start + size + 1
        if offset != len(stream):
            raise ValueError("unexpected-batch-trailer")
        self.bytes_by_path = {p: targets[self.tree[p][1]] for p in paths}

    def text(self, path: str) -> str:
        return self.bytes_by_path[path].decode("utf-8")

    def json(self, path: str) -> dict:
        return json.loads(self.text(path))


def _ok(value: bool, errors: list[str], key: str) -> None:
    if not value:
        errors.append(key)


def _section(markdown: str, name: str) -> str:
    if name == "ROOT":
        return markdown.split("\n## ", 1)[0]
    if name not in markdown.splitlines():
        return ""
    return markdown.split(name + "\n", 1)[1].split("\n## ", 1)[0]


def _parser(source: str) -> tuple[set[str], set[str]]:
    syntax = ast.parse(source)
    commands, flags = set(), set()
    for node in ast.walk(syntax):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("add_parser", "add_argument") or not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
            continue
        (commands if node.func.attr == "add_parser" else flags).add(first.value)
    return commands, flags


def _changed_source_guards(store: SourceStore, errors: list[str]) -> None:
    readme = store.text("README.md")
    docs = store.json("docs/documentation-registry.json")
    active = [d["path"] for d in docs["documents"]
              if d["status"] in ("CURRENT", "SCOPED_CURRENT")]
    for path in active:
        body = store.text(path)
        for pattern, label in CRITICAL:
            if re.search(pattern, body, flags=re.I):
                errors.append("semantic-contradiction:" + label + ":" + path)
    _ok(len(active) == 31, errors, "active-document-status-count")
    _ok("not a coding agent" in readme.lower().replace("*", ""),
        errors, "readme-agent-boundary-missing")


def _readme_evidence(store: SourceStore, contract: dict, errors: list[str]) -> list[dict]:
    readme = store.text("README.md")
    rows = []
    seen = set()
    for i, node in enumerate(contract["nodes"], start=1):
        key = f"S{i:02d}"
        _ok(node.get("id") == key and node.get("predicate") == PREDICATES[i - 1],
            errors, "node-predicate-drift:" + key)
        phrase, section = node.get("readme_phrase"), node.get("readme_section")
        if not isinstance(phrase, str) or not phrase or not isinstance(section, str):
            errors.append("missing-readme-claim:" + key)
            continue
        start = _section(readme, section)
        _ok(phrase in start, errors, "readme-claim-not-supported:" + key)
        evidence = node.get("evidence")
        if not isinstance(evidence, list) or len(evidence) < 3:
            errors.append("evidence-chain-incomplete:" + key)
            continue
        roles = {e.get("role") for e in evidence if isinstance(e, dict)}
        paths = [e.get("path") for e in evidence if isinstance(e, dict)]
        _ok({"CLAIM", "IMPLEMENTATION", "TEST"} <= roles and
            len(paths) == len(set(paths)) and "README.md" in paths and
            all(isinstance(x, str) and x in store.tree for x in paths),
            errors, "unattributable-evidence:" + key)
        _ok(isinstance(node.get("falsifier"), str) and
            len(node["falsifier"]) >= 20, errors, "missing-falsifier:" + key)
        _ok(key not in seen, errors, "duplicate-source-leaf:" + key)
        seen.add(key)
        objs = [{"path": e["path"], "role": e["role"],
                 "git_blob_oid": store.tree[e["path"]][1]}
                for e in evidence if isinstance(e, dict) and e.get("path") in store.tree]
        rows.append({"node": key, "predicate": node.get("predicate"),
                     "readme_section": section,
                     "readme_phrase": phrase,
                     "source_revision": store.sha,
                     "witnesses": objs, "falsifier": node.get("falsifier"),
                     "test_execution": "NOT_ATTESTED_BY_SOURCE_VERIFIER"})
    _ok(seen == {f"S{i:02d}" for i in range(1, 19)},
        errors, "s01-s18-incomplete")
    return rows


def _semantic_oracles(store: SourceStore, errors: list[str]) -> None:
    r = store.text
    readme, cli = r("README.md"), r("src/cora/cli.py")
    commands, flags = _parser(cli)
    meta = tomllib.loads(r("pyproject.toml"))["project"]
    ont = store.json("cora.ontology.json")
    dod = store.json("cora.documentation-dod.json")
    docs = store.json("docs/documentation-registry.json")
    policy = store.json(".cora/continuous-policy.json")
    document = {n["id"]: n for n in dod["nodes"]}
    _ok(meta["name"] == "cora-audit" and
        meta["scripts"] == {"cora": "cora.cli:main"} and
        meta["version"] == "1.0.0a4" and
        meta["version"] in readme and
        meta["version"] in r("docs/RELEASE.md") and
        f'__version__ = "{meta["version"]}"' in r("src/cora/__init__.py"),
        errors, "S01-S16:package-release-source-disagreement")
    _ok(ont.get("schema") == "cora-ontology/1" and
        {p["id"] for p in ont["products"]} == {"cora"} and
        {p["id"] for p in ont["software"]} ==
        {"cora-engine", "cora-release-verification"},
        errors, "S02:actual-ontology-disagreement")
    _ok("not the AI coding assistant" in r("AGENTS.md") and
        "not a coding agent" in readme.lower().replace("*", ""),
        errors, "S03:agent-vs-framework-boundary")
    _ok({"audit", "snapshot", "verify-ledger",
         "dev-premerge", "verify-contextual-gate"} <= commands and
        {"--contextual", "--intent", "--convergence-contract"} <= flags,
        errors, "S04-S05:documented-cli-parser-missing")
    continuous = r("src/cora/continuous.py")
    _ok("def evaluate_contextual(" in continuous and
        "def verify_contextual_gate(" in continuous and
        '"intent_digest": intent_digest' in continuous and
        '"BLOCKED_MISSING_PER_CHANGE_INTENT"' in continuous and
        "report[\"head_commit\"]" in continuous,
        errors, "S05-S12:actual-intent-binding-or-replay-missing")
    reticulum = r("src/cora/reticulum.py")
    _ok("def ordered_cut(" in reticulum and
        "def assess_cut(" in reticulum and
        '"authorization": "NONE"' in reticulum and
        '"BLOCKED_EXTERNAL"' in reticulum,
        errors, "S06:reticular-nonpromotion-missing")
    registry = docs["documents"]
    seen_paths = [d["path"] for d in registry]
    current_md = {p for p in store.tree if p.endswith(".md")}
    _ok(len(registry) == 48 and len(set(seen_paths)) == 48 and
        set(seen_paths) == current_md,
        errors, "S07-S08:git-document-registry-mismatch")
    _ok({n["id"] for n in dod["nodes"]} ==
        ({f"S{i:02d}" for i in range(1, 19)} |
         {"E01", "E02", "E03", "I_VALUE", "I_ACCESS",
          "I_CONSISTENCY", "I_OPERATION", "I_EVIDENCE",
          "G_DOC_SOURCE", "G_DOC_ACCEPTED"}) and
        len(ordered_cut(dod["nodes"], "G_DOC_ACCEPTED")) == 28 and
        document["G_DOC_ACCEPTED"]["depends_on"] ==
        ["G_DOC_SOURCE", "E01", "E02", "E03"] and
        all(document[x]["scope"] == "EXTERNAL" for x in ("E01", "E02", "E03")),
        errors, "S09:noncompensatory-dod-tampered")
    index = r("docs/INDEX.md")
    for path in seen_paths:
        if path == "docs/INDEX.md":
            continue
        relative = path[5:] if path.startswith("docs/") else "../" + path
        if "](" + relative + ")" not in index:
            errors.append("S07-S18:index-route-missing:" + path)
    _ok(docs.get("baseline_sha") == DOCUMENT_BASELINE,
        errors, "S17:original-register-baseline-drift")
    original = [d for d in registry if d.get("baseline_blob")]
    historical = [d for d in registry if d["status"] == "HISTORICAL"]
    _ok(len(original) == 43 and len(historical) == 17,
        errors, "S10-S17:historical-cardinality-mismatch")
    # Preserve the original historical baseline keys across lossless Git renames.
    # The HEAD relocation map is an untrusted declaration: each mapped original
    # must still be present in the immutable documentation baseline, with the
    # same byte-identical blob recorded in the current Git tree.
    migration = json.loads(store.text(".cora/layout-migration.json"))
    if (migration.get("schema") != "cora-layout-migration/1" or
        migration.get("source_commit") != "6475633d836ca94dd9ecf799d1c7ca3c4735ad13" or
        migration.get("authority") != "NONE"):
        raise ValueError("historical relocation source authority drift")
    old_for_new = {x["new"]: x["old"] for x in migration["moves"]
                   if x["kind"] == "HISTORICAL_MARKDOWN"}
    if len(old_for_new) != 14:
        raise ValueError("historical relocation mapping incomplete")
    for item in original:
        path = item["path"]
        source_baseline_path = old_for_new.get(path, path)
        expected = store.document_baseline_tree.get(source_baseline_path, ("", ""))[1]
        _ok(bool(expected) and item["baseline_blob"] == expected,
            errors, "S17:baseline-object-mismatch:" + path)
        if item["status"] == "HISTORICAL":
            _ok(store.tree.get(path, ("", ""))[1] == expected,
                errors, "S10:historical-blob-mutated:" + path)
    ref = r("docs/CLI_REFERENCE.md")
    q = chr(96)
    documented = re.findall(r"^- " + q + r"([a-z][a-z0-9-]+)" + q + r" —",
                            ref, re.M)
    _ok(len(commands) == 71 and len(documented) == 71 and
        set(documented) == commands,
        errors, "S11:parser-document-command-mismatch")
    _ok(all("--intent" in r(p) for p in
            ("README.md", "docs/AGENT_ADOPTION.md",
             "docs/CONVERGENT_ASSURANCE.md")),
        errors, "S12:procedural-intent-missing")
    _ok("def verify(" in r("tools/verify_documentation.py") and
        "def validate_dod(" in r("tools/verify_documentation.py"),
        errors, "S13:verifier-not-implemented")
    _ok({"MAINTAINER", "INDEPENDENT_SECURITY_REVIEWER"} <=
        set(policy["required_human_roles"]) and
        ".github/workflows" in policy["high_risk_prefixes"] and
        "authorization" in continuous and
        re.search(r"unverified|not verified|no independent reviewer", r("GOVERNANCE.md"), re.I) is not None,
        errors, "S14:governance-vs-policy-disagreement")
    convergence_ci = r(".github/workflows/ci-convergence.yml")
    _ok("CHANGE_INTENT:" in convergence_ci and
        "github.event.pull_request.title" in convergence_ci and
        "github.event.head_commit.message" in convergence_ci and
        convergence_ci.count('--intent "$CHANGE_INTENT"') >= 3,
        errors, "H3:change-specific-intent-not-replayed")
    workflow = r(".github/workflows/ci-documentation.yml")
    _ok("test_pr21_documentation.py" in workflow and
        "test_pr22_documentation_proofs.py" in workflow and
        "tools/verify_claim_evidence.py" in workflow and
        "--verify-report" in workflow,
        errors, "S15:missing-actual-falsification-ci")
    _ok("staged, not published" in r("docs/RELEASE.md").lower() and
        "not a stable API" in readme and
        "BLOCKED_EXTERNAL" in r("docs/RELEASE.md"),
        errors, "S16:alpha-publication-promoted")
    _ok("GETTING_STARTED.md" in index and
        "AGENT_ADOPTION.md" in index and "CLI_REFERENCE.md" in index,
        errors, "S18:reader-path-not-present")
    _ok("PR-21" in r("CHANGELOG.md") and "PR-21" in r("docs/ARCHITECTURE.md"),
        errors, "H2:post-pr21-chronology-stale")


def inspect(repo: Path, revision: str = "HEAD") -> dict:
    store = SourceStore(repo, revision)
    preliminary = (PROFILE, "docs/documentation-registry.json")
    store.read(set(preliminary))
    profile = store.json(PROFILE)
    errors: list[str] = []
    _ok(profile.get("schema") == "cora-documentation-proofs/1" and
        profile.get("baseline_sha") == BASELINE and
        profile.get("contract_dod") == "cora.documentation-dod.json" and
        profile.get("authority") ==
        "CANDIDATE_SOURCE_REPLAY_NOT_HOST_OR_HUMAN_ATTESTATION" and
        len(profile.get("nodes", [])) == 18 and
        [x.get("id") for x in profile.get("externals", [])] == ["E01", "E02", "E03"] and
        all(x.get("state") == "BLOCKED_EXTERNAL" for x in profile.get("externals", [])),
        errors, "proof-profile-structure-or-authority-drift")
    paths = set(REQUIRED) | set(store.tree) & {
        d["path"] for d in store.json("docs/documentation-registry.json")["documents"]
        if d["status"] in ("CURRENT", "SCOPED_CURRENT")}
    for node in profile.get("nodes", []):
        for e in node.get("evidence", []):
            if isinstance(e, dict) and isinstance(e.get("path"), str):
                paths.add(e["path"])
    store.read(paths)
    claims = _readme_evidence(store, profile, errors)
    _changed_source_guards(store, errors)
    _semantic_oracles(store, errors)
    errors = sorted(set(errors))
    report = {
        "schema": SCHEMA, "commit": store.sha,
        "profile_git_blob_oid": store.tree[PROFILE][1],
        "baseline_commit": BASELINE, "source_goal": "G_DOC_SOURCE",
        "accepted_goal": "G_DOC_ACCEPTED",
        "source_status": "PASS_SCOPED_SOURCE" if not errors else "REFUTED_SOURCE",
        "source_claim_count": len(claims),
        "source_claims": claims,
        "errors": errors,
        "governed_status": "BLOCKED_EXTERNAL",
        "external_obligations": {"E01": "NOT_OBSERVED", "E02": "NOT_OBSERVED",
                                 "E03": "NOT_ATTESTED"},
        "host_review_attested": False,
        "test_execution_attested_by_this_script": False,
        "git_subprocesses": store.calls,
        "evidence_class": "COMMITTED_SOURCE_AND_STATIC_PREDICATES_ONLY",
        "authorization": "NONE",
    }
    raw = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["receipt_sha256"] = hashlib.sha256(b"CORA:doc-proof:1\n" + raw).hexdigest()
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CORA Git-bound documentation proof, no host attestation")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-report", type=Path)
    args = parser.parse_args(argv)
    try:
        actual = inspect(args.repo, args.revision)
        if args.verify_report:
            receipt = json.loads(args.verify_report.read_text("utf-8"))
            if receipt != actual:
                raise ValueError("REPLAY_MISMATCH_OR_STALE_REVISION")
        if args.output:
            args.output.write_text(json.dumps(actual, sort_keys=True, indent=2) + "\n",
                                   encoding="utf-8")
        else:
            print(json.dumps(actual, sort_keys=True, indent=2))
        return 0 if not actual["errors"] else 2
    except (OSError, ValueError, KeyError, TypeError, SyntaxError,
            subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": SCHEMA, "source_status": "DEBT_BLOCKED",
                          "reason": type(exc).__name__ + ":" + str(exc)[:150],
                          "authorization": "NONE"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
