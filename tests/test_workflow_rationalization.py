"""Actual Git fixtures and 1,000 conservative workflow-syntax counterexamples."""
from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.workflow_rationalization import audit_workflows, verify_workflows, _parse
from cora.reticulum import ordered_cut

ROOT = Path(__file__).resolve().parents[1]
SIMPLE = "on: [push]\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n"


def cmd(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


def change(repo, files=None, removed=()):
    for name, content in (files or {}).items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for name in removed:
        (repo / name).unlink()
    cmd(repo, "add", "-A")
    cmd(repo, "commit", "-qm", "source fixture")
    return cmd(repo, "rev-parse", "HEAD")


def create(folder, files):
    repo = folder / "repo"
    repo.mkdir()
    cmd(repo, "init", "-q")
    cmd(repo, "config", "user.name", "CORA fixture")
    cmd(repo, "config", "user.email", "fixture@example.invalid")
    change(repo, files)
    return repo


class WorkflowRationalizationTests(unittest.TestCase):
    def test_self_source_inventory_and_dod(self):
        r = audit_workflows(ROOT)
        self.assertEqual(r["source_status"], "PASS_SCOPED_SOURCE")
        self.assertGreaterEqual(r["workflow_count"], 12)
        self.assertEqual(r["authorization"], "NONE")
        self.assertEqual(r["governed_status"], "BLOCKED_EXTERNAL")
        self.assertTrue(all(not row["retirement_authorized"] for row in r["workflows"]))
        verify_workflows(ROOT, r)
        doc = json.loads((ROOT / ".cora/contracts/dod/workflow-dod.json").read_text("utf-8"))
        self.assertEqual(len(ordered_cut(doc["nodes"], "G_WORKFLOW_GOVERNED")), 15)

    def test_workflow_labels_express_permanent_business_obligations(self):
        workflows = sorted((ROOT / '.github/workflows').glob('*.yml'))
        self.assertEqual(len(workflows), 14)
        labels = []
        for path in workflows:
            with self.subTest(workflow=path.name):
                first = path.read_text(encoding='utf-8').splitlines()[0]
                self.assertTrue(first.startswith('name: CORA | '), first)
                label = first.partition('name: CORA | ')[2].strip()
                self.assertGreaterEqual(len(label.split()), 2)
                self.assertNotRegex(label, r'(?i)\bpr[-_# ]?\d+\b')
                labels.append(label)
        self.assertEqual(len(labels), len(set(labels)))

    def test_current_test_module_names_express_capabilities(self):
        modules = sorted((ROOT / 'tests').glob('test_*.py'))
        self.assertGreaterEqual(len(modules), 61)
        self.assertEqual(len({p.name for p in modules}), len(modules))
        for path in modules:
            with self.subTest(path=path.name):
                self.assertNotRegex(path.name, r'(?i)(?:^|_)pr\d+(?=_|\.|$)')
        # Falsifiers must be rejected regardless of the evolving module count.
        for forged in ('test_pr01.py', 'test_pr87_cockpit.py',
                       'test_continuous_pr14.py'):
            self.assertRegex(forged, r'(?i)(?:^|_)pr\d+(?=_|\.|$)')

    def test_all_explicit_unittest_patterns_reach_live_modules(self):
        # Detect the silent-zero-tests failure mode for quoted AND unquoted -p.
        import fnmatch
        import re
        modules = {p.name for p in (ROOT / 'tests').glob('test_*.py')}
        sources = sorted((ROOT / '.github/workflows').glob('*.yml'))
        pattern = re.compile(
            r"""python -m unittest discover -s tests -p\s+(?:'([^']+)'|"([^"]+)"|([^\s]+))""")
        selectors = []
        for workflow in sources:
            for match in pattern.finditer(workflow.read_text(encoding='utf-8')):
                selected_pattern = next(x for x in match.groups() if x is not None)
                selected = {n for n in modules if fnmatch.fnmatchcase(n, selected_pattern)}
                with self.subTest(workflow=workflow.name, pattern=selected_pattern):
                    self.assertTrue(selected, 'empty CI discovery selector')
                    self.assertNotRegex(selected_pattern,
                                        r'(?i)(?:^|_)pr\d+(?=_|\.|$)')
                selectors.append((workflow.name, selected_pattern, selected))
        self.assertGreaterEqual(len(selectors), 56)
        for forged in ('test_pr07.py', 'test_pr25_method_synthesis.py',
                       'test_nonexistent_module.py'):
            self.assertFalse(any(fnmatch.fnmatchcase(n, forged) for n in modules))

    def test_workflow_literal_test_paths_are_live_and_falsifiable(self):
        # A selector can be correct while a separate CLI --path is stale.
        import re
        live = {p.name for p in (ROOT / "tests").glob("test_*.py")}
        pattern = re.compile(r"tests/(test_[A-Za-z0-9_.-]+[.]py)")
        observed = 0
        for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
            for name in pattern.findall(workflow.read_text(encoding="utf-8")):
                with self.subTest(workflow=workflow.name, source=name):
                    self.assertIn(name, live, "dangling workflow test-path consumer")
                observed += 1
        self.assertGreater(observed, 0, "no workflow test-path consumers inspected")
        for mutant in ("tests/test_pr10_artifact_roles.py",
                       "tests/test_nonexistent_semantic_contract.py"):
            self.assertTrue(set(pattern.findall(mutant)) - live,
                            "adversarial stale path escaped the source oracle")

    def test_real_git_inbound_and_priviliged_workflows(self):
        with tempfile.TemporaryDirectory() as t:
            repo = create(Path(t), {
                ".github/workflows/engine.yml": "on: [workflow_call]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
                ".github/workflows/caller.yml": "on: [push]\njobs:\n  gate:\n    uses: ./.github/workflows/engine.yml\n",
                ".github/workflows/release.yml": "on: [pull_request_target]\npermissions:\n  contents: write\njobs:\n  ship:\n    runs-on: ubuntu-latest\n    steps:\n      - run: gh release create\n",
                "README.md": "uses .github/workflows/engine.yml\n",
            })
            out = audit_workflows(repo)
            target = next(x for x in out["workflows"] if x["path"].endswith("engine.yml"))
            self.assertEqual(target["in_repo_callers"], [".github/workflows/caller.yml"])
            self.assertEqual(target["other_literal_references"], ["README.md"])
            self.assertFalse(target["retirement_authorized"])
            other = next(x for x in out["workflows"] if x["path"].endswith("release.yml"))
            self.assertIn("PR_TARGET_PRIVILEGE", other["flags"])
            self.assertIn("WRITE_OR_OIDC_PERMISSION", other["flags"])
            verify_workflows(repo, out)

    def test_real_git_retirement_plan_and_forged_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            repo = create(Path(t), {".github/workflows/old.yml": SIMPLE,
                                    ".github/workflows/new.yml": SIMPLE})
            original = audit_workflows(repo)
            self.assertTrue(all(x["disposition"] == "REVIEW_CONSOLIDATION_CANDIDATE"
                                for x in original["workflows"]))
            previous = cmd(repo, "rev-parse", "HEAD")
            head = change(repo, removed=(".github/workflows/old.yml",))
            delta = audit_workflows(repo, head, base=previous)
            self.assertEqual(delta["changes"][0]["operation"], "REMOVE")
            self.assertEqual(delta["changes"][0]["governance"], "BLOCKED_EXTERNAL")
            self.assertFalse(delta["changes"][0]["retirement_authorized"])
            verify_workflows(repo, delta)
            tampered = json.loads(json.dumps(delta))
            tampered["changes"][0]["retirement_authorized"] = True
            with self.assertRaises(ValueError):
                verify_workflows(repo, tampered)
            with self.assertRaises(ValueError):
                verify_workflows(repo, dict(delta, commit=previous))
            self.assertNotEqual(original["receipt_sha256"], delta["receipt_sha256"])

    def test_dirty_tree_and_incomplete_scan_remain_honest(self):
        with tempfile.TemporaryDirectory() as t:
            repo = create(Path(t), {".github/workflows/a.yml": SIMPLE})
            original = audit_workflows(repo)
            (repo / ".github/workflows/a.yml").write_text("uncommitted", encoding="utf-8")
            self.assertEqual(original, audit_workflows(repo))
            change(repo, {"notes.json": "x" * 524400})
            outcome = audit_workflows(repo)
            self.assertFalse(outcome["source_scan_complete"])
            self.assertEqual(outcome["source_status"], "DEBT_BLOCKED_SOURCE_SCAN")
            self.assertFalse(outcome["workflows"][0]["retirement_authorized"])

    def test_one_thousand_typed_adversarial_patterns(self):
        distinct = set()
        for family in range(10):
            for i in range(100):
                text = SIMPLE + f"\n# family={family} vector={i}\n"
                if family == 0:
                    text = text.replace("on: [push]", "on: [workflow_dispatch]")
                    expected = "MANUAL_OR_SCHEDULED_ENTRY"
                elif family == 1:
                    text += "      - run: gh release create\n"
                    expected = "POSSIBLE_RELEASE_OR_DEPLOYMENT"
                elif family == 2:
                    text += "permissions:\n  contents: write\n"
                    expected = "WRITE_OR_OIDC_PERMISSION"
                elif family == 3:
                    text += "      - run: echo " + chr(36) + "{{ secrets.KEY }}\n"
                    expected = "POSSIBLE_SECRETS_ACCESS"
                elif family == 4:
                    text = text.replace("on: [push]", "on: [workflow_call]")
                    expected = "REUSABLE_WORKFLOW_ENTRY"
                elif family == 5:
                    text = text.replace("on: [push]", "on: [schedule]")
                    expected = "MANUAL_OR_SCHEDULED_ENTRY"
                elif family == 6:
                    text += f"      - uses: ./.github/workflows/t-{i}.yml\n"
                    expected = "EDGE"
                elif family == 7:
                    text = text.replace("jobs:", "unsupported:")
                    expected = "PARTIAL_YAML_PARSE"
                elif family == 8:
                    text = text.replace("on: [push]", "on: [pull_request_target]")
                    expected = "PR_TARGET_PRIVILEGE"
                else:
                    text += "      - uses: acme/tools/.github/workflows/build.yml@main\n"
                    expected = "EXTERNAL_REUSABLE_WORKFLOW_REFERENCE"
                row = _parse(text)
                if expected == "EDGE":
                    self.assertEqual(row["local_workflow_calls"],
                                     [f".github/workflows/t-{i}.yml"])
                else:
                    self.assertIn(expected, row["flags"])
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                self.assertNotIn(digest, distinct)
                distinct.add(digest)
        self.assertEqual(len(distinct), 1000)


if __name__ == "__main__":
    unittest.main()
