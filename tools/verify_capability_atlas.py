"""CORA capability source census. Git-bound source only, not execution evidence."""
from __future__ import annotations
import ast
import json
import re
import argparse
from pathlib import Path
from cora.git_snapshot import git, _sizes, _read_objects
from cora.evidence import domain_hash
from cora.reticulum import ordered_cut

SCHEMA="cora-capability-proof/1"
EDGES={"I_IDENTITY":["C01","C02","C03","C04"],"I_ASSURANCE":["C05","C06","C07"],"G_CAP_SOURCE":["I_IDENTITY","I_ASSURANCE"],"G_CAP_ACCEPTED":["G_CAP_SOURCE","E01","E02","E03"]}
SENSITIVE={"audit":"WORKTREE_NOT_IMMUTABLE_GIT","apply-rename-doc":"MUTATES_TARGET_AFTER_EXPLICIT_APPROVAL_AND_TEST","guard-install":"WRITES_LOCAL_GUARD","zip-intake":"OPTIONAL_EXTRACTION_PRECHECK","runtime-observe":"OPTIONAL_DOCKER_RUNTIME_UNATTESTED","gold-mutate":"STAGED_PHYSICAL_MUTATIONS_OPTIONAL_DOCKER","file-decision":"RECORDS_HUMAN_CLAIM_NOT_APPROVAL","annotate-groups":"ANNOTATES_UNTRUSTED_AI_HYPOTHESES","method-synthesize":"OPTIONAL_UNTRUSTED_AI_HYPOTHESES"}

def source_at(repo, revision):
    from cora.workflow_rationalization import _source
    return _source(repo, revision)


def text_at(repo, entries, paths):
    from cora.workflow_rationalization import _read
    value, omitted = _read(repo, entries, sorted(set(paths)), strict=True)
    if omitted:
        raise ValueError("incomplete source read")
    return value


def parser_wiring(text):
    syntax = ast.parse(text)
    names = []
    imports = {}
    uses = {}
    for node in ast.walk(syntax):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_parser" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    names.append(arg.value)
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            path = "src/cora/" + (node.module or "__init__") + ".py"
            for symbol in node.names:
                imports[symbol.asname or symbol.name] = path
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            continue
        if not (isinstance(test.left, ast.Attribute)
                and test.left.attr == "cmd"
                and isinstance(test.left.value, ast.Name)
                and test.left.value.id == "args"):
            continue
        right = test.comparators[0]
        commands = []
        if isinstance(test.ops[0], ast.Eq) and isinstance(right, ast.Constant):
            commands = [right.value]
        elif isinstance(test.ops[0], ast.In) and isinstance(right, (ast.Tuple, ast.List)):
            commands = [x.value for x in right.elts if isinstance(x, ast.Constant)]
        used = {x.id for stmt in node.body for x in ast.walk(stmt)
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
        for command in commands:
            if isinstance(command, str):
                uses.setdefault(command, set()).update(used)
    # verify-ledger is the final else, deliberately not a named elif.
    if "validate_ledger(ledger)" in text and "snapshot(args.repo" in text:
        uses["verify-ledger"] = {"snapshot", "validate_ledger"}
    return names, imports, uses


def verify_dod(doc):
    if (doc.get("schema") != "cora-capability-dod/1"
            or doc.get("authority") != "NONE"
            or doc.get("external_status") != "BLOCKED_EXTERNAL"
            or doc.get("ci_status") != "MUST_BE_OBSERVED_EXACT_HEAD"):
        raise ValueError("invalid DoD authority")
    nodes = doc["nodes"]
    expected = {"C%02d" % n for n in range(1, 8)}
    expected |= {"E%02d" % n for n in range(1, 4)}
    expected |= set(EDGES)
    if {n["id"] for n in nodes} != expected:
        raise ValueError("DoD identities changed")
    for node in nodes:
        if node["id"] in EDGES and node["depends_on"] != EDGES[node["id"]]:
            raise ValueError("noncompensatory DoD edge removed")
        if node["id"].startswith("E") and node["scope"] != "EXTERNAL":
            raise ValueError("external DoD was promoted")
    if len(nodes) != 14 or len(ordered_cut(nodes, "G_CAP_ACCEPTED")) != 14:
        raise ValueError("incomplete reticular DoD")


def check(repo, revision="HEAD"):
    from cora.artifact_roles import roles_for, validate_declarations
    repo = Path(repo).resolve(strict=True)
    commit, tree = source_at(repo, revision)
    base = {".cora/assurance/capability-atlas.json", ".cora/contracts/dod/capability-dod.json",
            "cora.ontology.json", "cora.artifact-roles.json",
            "docs/documentation-registry.json", "src/cora/cli.py",
            "README.md", "docs/CLI_REFERENCE.md", "docs/INDEX.md",
            "docs/ARCHITECTURE.md", "docs/DOCUMENTATION_DOD.md", "CHANGELOG.md"}
    texts = text_at(repo, tree, base)
    atlas = json.loads(texts[".cora/assurance/capability-atlas.json"])
    dod = json.loads(texts[".cora/contracts/dod/capability-dod.json"])
    ontology = json.loads(texts["cora.ontology.json"])
    role_decl = json.loads(texts["cora.artifact-roles.json"])
    validate_declarations(role_decl)
    if (set(atlas) != {"schema", "origin", "authority", "classification",
                       "families", "commands", "repository_surfaces", "qualification"}
            or atlas["schema"] != "cora-capability-atlas/1" or atlas["authority"] != "NONE"
            or atlas["qualification"]["governed"] != "BLOCKED_EXTERNAL"):
        raise ValueError("invalid capability atlas")
    if (ontology.get("schema") != "cora-ontology/1"
            or atlas["origin"]["product"] not in {p["id"] for p in ontology["products"]}
            or set(atlas["origin"]["software"]) != {s["id"] for s in ontology["software"]}
            or atlas["origin"]["repository"] != "Luke883i/cora"):
        raise ValueError("declared product/software/repository identity changed")
    verify_dod(dod)
    families = atlas["families"]
    if len(families) != 8 or len({f["id"] for f in families}) != 8:
        raise ValueError("incomplete method taxonomy")
    family_ids = {f["id"] for f in families}
    active_docs = {x["path"] for x in json.loads(
        texts["docs/documentation-registry.json"])["documents"]
        if x["status"] in ("CURRENT", "SCOPED_CURRENT")}
    for family in families:
        if family["guide"] not in active_docs:
            raise ValueError("method has no current documentation")
    surfaces = atlas["repository_surfaces"]
    patterns = {
        "modules": lambda p: re.fullmatch(r"src/cora/[^/]+\.py", p),
        "operational_tools": lambda p: re.fullmatch(r"tools/[^/]+\.py", p),
        "github_workflows": lambda p: re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", p),
        "contracts": lambda p: re.fullmatch(r"cora\.[^/]+\.json", p),
        "internal_dod": lambda p: re.fullmatch(r"\.cora/contracts/dod/[^/]+\.json", p),
        "internal_profiles": lambda p: re.fullmatch(r"\.cora/contracts/profiles/[^/]+\.json", p),
        "assurance_records": lambda p: re.fullmatch(r"\.cora/assurance/[^/]+\.json", p),
        "markdown": lambda p: p.endswith(".md"),
        "test_modules": lambda p: re.fullmatch(r"tests/test_[^/]+\.py", p),
    }
    if set(surfaces) != set(patterns):
        raise ValueError("repository surface classes changed")
    for group, match in patterns.items():
        actual = sorted(path for path in tree if match(path))
        if surfaces[group] != actual:
            raise ValueError("repository inventory drift: " + group)
    names, imports, dispatch = parser_wiring(texts["src/cora/cli.py"])
    documented = re.findall(r"^- `([a-z][a-z0-9-]+)` —",
                            texts["docs/CLI_REFERENCE.md"], re.M)
    rows = atlas["commands"]
    declared = [x["command"] for x in rows]
    if (len(declared) != 71 or len(set(declared)) != len(declared)
            or set(declared) != set(names) or len(names) != len(set(names))
            or set(documented) != set(names) or len(documented) != len(set(documented))):
        raise ValueError("CLI, atlas and documentation diverged")

    linked = set()
    for row in rows:
        if (set(row) != {"command", "family", "method_source",
                         "test_source", "interaction"}
                or row["family"] not in family_ids
                or row["method_source"] not in surfaces["modules"]
                or row["test_source"] not in surfaces["test_modules"]):
            raise ValueError("invalid capability binding")
        command = row["command"]
        if command in SENSITIVE and row["interaction"] != SENSITIVE[command]:
            raise ValueError("effectful command reclassified: " + command)
        if command.startswith("stress") and row["interaction"] != "SYNTHETIC_MODEL_NOT_RUNTIME":
            raise ValueError("finite model promoted: " + command)
        if command not in dispatch:
            raise ValueError("CLI command has no dispatch path: " + command)
        if not any(imports.get(symbol) == row["method_source"]
                   for symbol in dispatch[command]):
            raise ValueError("implementation detached from command: " + command)
        if "SOFTWARE_SOURCE" not in roles_for(
                row["method_source"], role_decl["rules"])["roles"]:
            raise ValueError("implementation role no longer declared")
        if "TEST" not in roles_for(
                row["test_source"], role_decl["rules"])["roles"]:
            raise ValueError("test witness role no longer declared")
        linked.add(row["method_source"])
        linked.add(row["test_source"])
    sources = text_at(repo, tree, linked)
    for path, content in sources.items():
        syntax = ast.parse(content, filename=path)
        if path.startswith("tests/") and not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_") for node in ast.walk(syntax)):
            raise ValueError("test witness has no test functions: " + path)
    readme = texts["README.md"]
    # PR42: preserve the exact capability scope while permitting semantically
    # equivalent progressive prose. The old literal 71-command sentence was
    # an editorial choice, never a new authority or test-execution receipt.
    declared = re.search(r"(?<!\d)71 (?:declared )?CLI commands(?!\d)", readme)
    bounded = re.search(
        r"(?:not|\*\*not\*\*)\s+(?:71 independently proven features"
        r"|a claim that 71 product behaviors have been independently executed or certified)",
        readme, re.I)
    if ("[capability atlas](.cora/assurance/capability-atlas.json)" not in readme
            or not declared or not bounded):
        raise ValueError("README feature scope incomplete")
    if ("../.cora/assurance/capability-atlas.json" not in texts["docs/INDEX.md"]
            or "../.cora/contracts/dod/capability-dod.json" not in texts["docs/DOCUMENTATION_DOD.md"]):
        raise ValueError("capability evidence is not navigable")
    # Verify present-day documentation ownership instead of requiring PR-era
    # headings. Historical lineage remains in original Git and the registry.
    if ("## Current documentation ownership" not in texts["docs/ARCHITECTURE.md"]
            or "documentation-registry.json" not in texts["docs/ARCHITECTURE.md"]
            or "1.0.0a5" not in texts["CHANGELOG.md"]
            or "## Progressive navigation and five reader paths" not in texts["docs/DOCUMENTATION_DOD.md"]
            or "S01–S18" not in texts["docs/DOCUMENTATION_DOD.md"]):
        raise ValueError("current documentation ownership or source identity contradicted")
    receipts = [{"command":row["command"], "family":row["family"],
                 "interaction":row["interaction"],
                 "implementation_oid":tree[row["method_source"]][1],
                 "test_source_oid":tree[row["test_source"]][1],
                 "test_execution":"NOT_ATTESTED_BY_SOURCE"} for row in rows]
    report = {
        "schema":SCHEMA, "commit":commit, "source_status":"PASS_SCOPED_SOURCE",
        "command_count":len(rows), "commands":receipts, "family_count":len(families),
        "surfaces":{k:len(v) for k,v in sorted(surfaces.items())},
        "atlas_oid":tree[".cora/assurance/capability-atlas.json"][1],
        "dod_oid":tree[".cora/contracts/dod/capability-dod.json"][1],
        "cli_oid":tree["src/cora/cli.py"][1],
        "proof_scope":"SYNTAX_IMPORT_AND_SOURCE_TEST_WITNESS_NOT_EXECUTED",
        "real_target":"UNOBSERVED", "ci_final_head":"NOT_ATTESTED_BY_SOURCE",
        "governed_status":"BLOCKED_EXTERNAL", "authorization":"NONE"
    }
    report["receipt_digest"] = domain_hash("CORA:capability-proof:1", report)
    return report


def replay(repo, report):
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError("invalid proof receipt")
    if check(repo, report["commit"]) != report:
        raise ValueError("capability report differs from committed Git objects")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-report", type=Path)
    args = parser.parse_args()
    try:
        if args.verify_report:
            report = json.loads(args.verify_report.read_text("utf-8"))
            replay(args.repo, report)
            result = {"schema":"cora-capability-replay/1",
                      "commit":report["commit"],
                      "status":"REPLAYED_SOURCE_NOT_BEHAVIORAL_ATTESTATION",
                      "authorization":"NONE"}
        else:
            result = check(args.repo, args.revision)
        rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (ValueError, KeyError, TypeError, OSError, SyntaxError) as exc:
        print(json.dumps({"source_status":"DEBT_BLOCKED",
                          "error":str(exc), "authorization":"NONE"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
