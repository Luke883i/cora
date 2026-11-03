"""Documentation source contract: inventory, reachability, roles, CLI and DoD.

Static reports are NOT independent acceptance, host authority or user comprehension.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote

BASELINE_SHA = "ee6da7625dae1e4101e06eb979a348610f39093b"
BASELINE_MD = 43
EXPECTED_MD = 48
EXTERNAL = {"E01", "E02", "E03"}
SOURCE = {f"S{i:02d}" for i in range(1, 19)}
CUTS = {
    "I_VALUE": ["S01", "S02", "S03", "S06"],
    "I_ACCESS": ["S04", "S05", "S07", "S08", "S18"],
    "I_CONSISTENCY": ["S09", "S10", "S12", "S16", "S17"],
    "I_OPERATION": ["S11", "S13", "S14"],
    "I_EVIDENCE": ["S15"],
    "G_DOC_SOURCE": ["I_VALUE", "I_ACCESS", "I_CONSISTENCY", "I_OPERATION", "I_EVIDENCE"],
    "G_DOC_ACCEPTED": ["G_DOC_SOURCE", "E01", "E02", "E03"],
}
KNOWN_HISTORICAL = {
    "docs/DOD.md", "docs/DOD_PR17_AGENT.md",
    "docs/DOD_PR16_SEMANTIC_ASSURANCE.md",
    "docs/STANDARDS_MAINTENANCE_AUDIT.md",
    "docs/FORENSIC_SELF_AUDIT.md",
}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\((<[^>]+>|[^)\s]+)")
CODE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
COMMAND = re.compile(r"^- `([a-z][a-z0-9-]+)` —", re.M)
STATUS = {"CURRENT", "SCOPED_CURRENT", "HISTORICAL"}
KINDS = {"LANDING", "INDEX", "ADR", "AUDIT", "DOD", "CHANGELOG",
         "GOVERNANCE", "ARCHITECTURE", "REFERENCE", "METHOD"}
VALID_GROUP = {"00", "01", "02", "03", "04", "05", "06", "07"}


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def markdown_links(content: str) -> list[str]:
    output, inside, marker = [], False, ""
    for line in content.splitlines():
        m = CODE_FENCE.match(line)
        if m:
            kind = m.group(1)[0]
            if not inside:
                inside, marker = True, kind
            elif kind == marker:
                inside, marker = False, ""
            continue
        if not inside:
            output.extend(m.group(1).strip("<>") for m in LINK.finditer(line))
    return output


def resolve(base: str, href: str) -> tuple[str, str] | None:
    if href.startswith(("#", "https://", "http://", "mailto:", "tel:")):
        return None
    raw, _, anchor = unquote(href).partition("#")
    if not raw or "://" in raw or raw.startswith("/") or "\\" in raw:
        return None
    target = posixpath.normpath(posixpath.join(posixpath.dirname(base), raw))
    if target.startswith("../") or target in (".", ".."):
        return None
    return target, anchor


def heading_slugs(text: str) -> set[str]:
    slugs, counts = set(), {}
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not m:
            continue
        slug = re.sub(r"[^\w\- ]", "", m.group(1).lower()).strip().replace(" ", "-")
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        slugs.add(slug + (f"-{n}" if n else ""))
    return slugs


def validate_dod(root: Path, errors: list[str]) -> None:
    try:
        d = json.loads((root / "cora.documentation-dod.json").read_text("utf-8"))
        if (d.get("schema") != "cora-documentation-dod/1" or
            d.get("baseline_markdown_count") != BASELINE_MD or
            d.get("baseline_sha") != BASELINE_SHA or
            d.get("authority") != "NONE" or
            d.get("external_status") != "BLOCKED_EXTERNAL" or
            d.get("goals") != {"source": "G_DOC_SOURCE", "accepted": "G_DOC_ACCEPTED"}):
            raise ValueError("DoD status or authority altered")
        nodes = d["nodes"]
        if not isinstance(nodes, list) or len(nodes) != 28:
            raise ValueError("expected 28 DoD nodes")
        ids = [n["id"] for n in nodes]
        if len(set(ids)) != len(ids) or set(ids) != SOURCE | EXTERNAL | set(CUTS):
            raise ValueError("DoD identities inconsistent")
        for n in nodes:
            key = n["id"]
            if key in CUTS:
                if (n["depends_on"] != CUTS[key] or
                    n["kind"] != ("GLOBAL" if key.startswith("G_") else "INTERMEDIATE") or
                    n["scope"] != ("EXTERNAL" if key == "G_DOC_ACCEPTED" else "SOURCE")):
                    raise ValueError("DoD edge/scope drift")
            elif n["depends_on"] or n["kind"] != "LOCAL" or n["scope"] != (
                "EXTERNAL" if key in EXTERNAL else "SOURCE"
            ):
                raise ValueError("DoD leaf changed")
        from cora.reticulum import ordered_cut
        if len(ordered_cut(nodes, "G_DOC_ACCEPTED")) != 28:
            raise ValueError("DoD global not connected")
    except (OSError, ValueError, TypeError, KeyError, ImportError) as exc:
        errors.append("documentation-dod-invalid:" + type(exc).__name__)


def verify(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        registry = json.loads((root / "docs/documentation-registry.json").read_text("utf-8"))
        records = registry["documents"]
        if (registry["schema"] != "cora-documentation-registry/1" or
            registry["baseline_markdown_count"] != BASELINE_MD or
            registry["baseline_sha"] != BASELINE_SHA or
            registry["files_expected"] != EXPECTED_MD or
            registry["authority"] != "MAINTAINER_DECLARATION_NOT_INDEPENDENT_ATTESTATION"):
            raise ValueError("registry contract altered")
    except (OSError, ValueError, KeyError, TypeError):
        return ["invalid-documentation-registry"]
    actual = set()
    for p in root.rglob("*.md"):
        rel = p.relative_to(root)
        if any(part.startswith(".") and part not in (".github",) for part in rel.parts):
            continue
        if any(part in ("build", "dist", "site-packages") for part in rel.parts):
            continue
        actual.add(rel.as_posix())
    declared = [r.get("path") for r in records if isinstance(r, dict)]
    if len(declared) != EXPECTED_MD or len(set(declared)) != len(declared):
        errors.append("duplicate-or-wrong-document-count")
    if set(declared) != actual:
        errors.extend("unregistered:" + p for p in sorted(actual - set(declared)))
        errors.extend("missing:" + p for p in sorted(set(declared) - actual))
    if sum(bool(r.get("baseline_blob")) for r in records if isinstance(r, dict)) != BASELINE_MD:
        errors.append("baseline-43-markdown-count-drift")
    original = set()
    for r in records:
        if not isinstance(r, dict):
            errors.append("invalid-registry-entry")
            continue
        path = r.get("path")
        if not isinstance(path, str) or path.startswith("/") or ".." in path.split("/"):
            errors.append("invalid-path")
            continue
        historical = (path.startswith("docs/ADR-") or path.startswith("docs/AUDIT_")
                      or path in KNOWN_HISTORICAL)
        if r.get("status") not in STATUS or r.get("kind") not in KINDS or r.get("group") not in VALID_GROUP:
            errors.append("invalid-classification:" + path)
        if historical and (r.get("status") != "HISTORICAL" or
                           r.get("authority") != "HISTORICAL_RECORD"):
            errors.append("historical-authority-promoted:" + path)
        if r.get("baseline_blob"):
            original.add(path)
            if historical and (root / path).is_file() and git_blob_sha(
                (root / path).read_bytes()) != r["baseline_blob"]:
                errors.append("historical-content-changed:" + path)
    if len(original) != BASELINE_MD:
        errors.append("historical-baseline-incomplete")
    graph = {p: set() for p in actual}
    for path in sorted(actual):
        content = (root / path).read_text("utf-8")
        for href in markdown_links(content):
            target = resolve(path, href)
            if target is None:
                continue
            name, anchor = target
            dest = root / name
            if not dest.exists():
                errors.append("broken-link:" + path + ":" + name)
            elif anchor and dest.is_file() and dest.suffix == ".md" and (
                anchor not in heading_slugs(dest.read_text("utf-8"))):
                errors.append("broken-anchor:" + path + ":" + name + "#" + anchor)
            if name in graph:
                graph[path].add(name)
    reached, queue = {"README.md"}, ["README.md"]
    while queue:
        for linked in sorted(graph.get(queue.pop(0), ())):
            if linked not in reached:
                reached.add(linked)
                queue.append(linked)
    errors.extend("unreachable:" + p for p in sorted(actual - reached))
    for path in actual - {"docs/INDEX.md"}:
        if path not in graph.get("docs/INDEX.md", set()):
            errors.append("not-indexed:" + path)
    try:
        cli = ast.parse((root / "src/cora/cli.py").read_text("utf-8"))
        parsers = [n.args[0].value for n in ast.walk(cli)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "add_parser" and n.args
                   and isinstance(n.args[0], ast.Constant)
                   and isinstance(n.args[0].value, str)]
        reference = COMMAND.findall((root / "docs/CLI_REFERENCE.md").read_text("utf-8"))
        if len(parsers) != len(set(parsers)) or sorted(reference) != sorted(parsers):
            errors.append("cli-reference-parser-drift")
    except (OSError, SyntaxError):
        errors.append("cli-reference-unreadable")
    readme = (root / "README.md").read_text("utf-8")
    required = ("# CORA — Continuous Ontological Repository Assurance",
                "**CORA (Continuous Ontological Repository Assurance)**",
                "## First five minutes", "## What works today",
                "## Use CORA with an AI coding assistant", "## Operating boundaries",
                "## Engineering map", "1.0.0a4", "cora --help", "cora snapshot",
                "docs/INDEX.md", "BLOCKED_EXTERNAL", "--intent")
    if any(token not in readme for token in required):
        errors.append("readme-contract-regression")
    if len(readme.splitlines()) > 180:
        errors.append("readme-excessive-length")
    for path in ("README.md", "docs/AGENT_ADOPTION.md", "docs/CONVERGENT_ASSURANCE.md"):
        if not (root / path).is_file():
            errors.append("missing-procedure:" + path)
        elif "--intent" not in (root / path).read_text("utf-8"):
            errors.append("contextual-intent-omitted:" + path)
    if "not a stable" not in readme.lower() and "not a stable api" not in readme.lower():
        errors.append("release-claim-regression")
    validate_dod(root, errors)
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = verify(args.repo)
    print(json.dumps({"schema": "cora-documentation-verification/1",
                      "status": "PASS_SCOPED_STATIC" if not errors else "FAIL",
                      "source_ci": "NOT_ATTESTED_BY_THIS_PROCESS",
                      "governed": "BLOCKED_EXTERNAL", "authorization": "NONE",
                      "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
