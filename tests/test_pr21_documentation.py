"""PR-21: actual disposable-document mutations, never synthetic usability claims."""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from cora.reticulum import ordered_cut

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cora_documentation_verifier",
                                            ROOT / "tools/verify_documentation.py")
doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc)


def copy_fixture(dst: Path) -> None:
    inventory = json.loads((ROOT / "docs/documentation-registry.json").read_text("utf-8"))
    for entry in inventory["documents"]:
        path = entry["path"]
        (dst / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, dst / path)
    for path in ("docs/documentation-registry.json", ".cora/contracts/dod/documentation-dod.json",
                 "src/cora/cli.py"):
        (dst / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, dst / path)
    (dst / "LICENSE").write_text("Fixture only", encoding="utf-8")
    (dst / "cora.ontology.json").write_text("{}", encoding="utf-8")
    (dst / "cora.artifact-roles.json").write_text("{}", encoding="utf-8")


class DocumentationDoDTests(unittest.TestCase):
    def test_01_current_documentation_inventory_and_links(self):
        self.assertEqual(doc.verify(ROOT), [])
        registry = json.loads((ROOT / "docs/documentation-registry.json").read_text("utf-8"))
        self.assertEqual(len(registry["documents"]), 48)
        self.assertEqual(sum(bool(x["baseline_blob"]) for x in registry["documents"]), 43)
        self.assertEqual(registry["authority"],
                         "MAINTAINER_DECLARATION_NOT_INDEPENDENT_ATTESTATION")

    def test_02_reticular_global_has_independent_external_cut(self):
        data = json.loads((ROOT / ".cora/contracts/dod/documentation-dod.json").read_text("utf-8"))
        self.assertEqual(len(data["nodes"]), 28)
        self.assertEqual(len(ordered_cut(data["nodes"], "G_DOC_SOURCE")), 24)
        self.assertEqual(len(ordered_cut(data["nodes"], "G_DOC_ACCEPTED")), 28)
        self.assertEqual(data["external_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(data["authority"], "NONE")

    def test_03_physical_document_mutants_are_detected(self):
        def change(rel, replace):
            p = fixture / rel
            p.write_text(replace(p.read_text("utf-8")), encoding="utf-8")

        def registry_mutate(modifier):
            p = fixture / "docs/documentation-registry.json"
            j = json.loads(p.read_text("utf-8"))
            modifier(j)
            p.write_text(json.dumps(j), encoding="utf-8")

        def dod_mutate(modifier):
            p = fixture / ".cora/contracts/dod/documentation-dod.json"
            j = json.loads(p.read_text("utf-8"))
            modifier(j)
            p.write_text(json.dumps(j), encoding="utf-8")

        cases = [
            ("missing-index-link", lambda: change("docs/INDEX.md",
             lambda x: x.replace("](../README.md)", "](https://example.invalid)")), "not-indexed:README.md"),
            ("missing-doc", lambda: (fixture / "docs/FILE_LAB.md").unlink(), "missing:docs/FILE_LAB.md"),
            ("unregistered-doc", lambda: (fixture / "docs/rogue.md").write_text("# Unregistered", encoding="utf-8"), "unregistered:docs/rogue.md"),
            ("duplicate-registration", lambda: registry_mutate(
             lambda j: j["documents"].append(copy.deepcopy(j["documents"][0]))),
             "duplicate-or-wrong-document-count"),
            ("historical-identity-promoted", lambda: registry_mutate(
             lambda j: next(x for x in j["documents"] if x["path"] == "docs/archive/decisions/ADR-PR01.md").update(
                 {"status": "CURRENT"})), "historical-authority-promoted:docs/archive/decisions/ADR-PR01.md"),
            ("historical-source-edited", lambda: change("docs/archive/decisions/ADR-PR01.md",
             lambda x: x + "\nModified historical content\n"), "historical-content-changed:docs/archive/decisions/ADR-PR01.md"),
            ("broken-link", lambda: change("README.md",
             lambda x: x + "\n[Missing](docs/nonexistent.md)\n"), "broken-link:README.md:docs/nonexistent.md"),
            ("broken-heading-anchor", lambda: change("README.md",
             lambda x: x + "\n[Invalid](docs/INDEX.md#not-a-real-heading)\n"),
             "broken-anchor:README.md:docs/INDEX.md#not-a-real-heading"),
            ("cli-reference-incomplete", lambda: change("docs/CLI_REFERENCE.md",
             lambda x: x.replace("- `version` —", "- OMITTED —", 1)), "cli-reference-parser-drift"),
            ("readme-promise-removed", lambda: change("README.md",
             lambda x: x.replace("## Use CORA with an AI coding assistant",
                                 "## Obscured method", 1)), "readme-contract-regression"),
            ("intent-guide-removed", lambda: change("docs/AGENT_ADOPTION.md",
             lambda x: x.replace("--intent", "--with-goal")), "contextual-intent-omitted:docs/AGENT_ADOPTION.md"),
            ("intent-current-method-removed", lambda: change("docs/CONVERGENT_ASSURANCE.md",
             lambda x: x.replace("--intent", "--with-goal")), "contextual-intent-omitted:docs/CONVERGENT_ASSURANCE.md"),
            ("dod-edge-removed", lambda: dod_mutate(
             lambda j: next(x for x in j["nodes"] if x["id"] == "G_DOC_SOURCE")["depends_on"].pop()),
             "documentation-dod-invalid:ValueError"),
            ("dod-external-promoted", lambda: dod_mutate(
             lambda j: next(x for x in j["nodes"] if x["id"] == "E03").update({"scope": "SOURCE"})),
             "documentation-dod-invalid:ValueError"),
            ("release-wording", lambda: change("README.md",
             lambda x: x.replace("not a stable API", "a stable API", 1)), "release-claim-regression"),
        ]
        for label, mutate, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                fixture = Path(td)
                copy_fixture(fixture)
                mutate()
                problems = doc.verify(fixture)
                self.assertIn(expected, problems, problems)
                self.assertTrue(problems)

    def test_04_parser_commands_are_exact_not_legacy_catalog(self):
        import ast
        code = ast.parse((ROOT / "src/cora/cli.py").read_text("utf-8"))
        parser_names = {x.args[0].value for x in ast.walk(code)
                        if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                        and x.func.attr == "add_parser" and x.args
                        and isinstance(x.args[0], ast.Constant)
                        and isinstance(x.args[0].value, str)}
        names = doc.COMMAND.findall((ROOT / "docs/CLI_REFERENCE.md").read_text("utf-8"))
        self.assertEqual(len(parser_names), 71)
        self.assertEqual(len(names), 71)
        self.assertEqual(parser_names, set(names))


if __name__ == "__main__":
    unittest.main()
