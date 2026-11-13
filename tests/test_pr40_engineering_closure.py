"""PR40 original-Git falsifiers for knowledge convergence, source debt and 10M model."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import verify_engineering_closure as ekc

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError("original-Git fixture failed: " + result.stderr[:1000])
    return result.stdout.strip()


class EngineeringKnowledgeClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("complete original Git checkout required")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.doc = ekc.contract_at(ROOT, cls.sha)

    def test_reuse_not_new_orchestrator_and_exact_source_census(self):
        report = ekc.analyze(ROOT, self.sha)
        self.assertEqual(report["commit"], self.sha)
        self.assertEqual(report["counts"]["cli"], 71)
        self.assertGreater(report["counts"]["modules"], 50)
        self.assertGreater(report["counts"]["dynamic_callsite_indicators"], 0)
        self.assertEqual(report["host_enforcement"], "BLOCKED_EXTERNAL")
        self.assertEqual(report["dynamic_execution"], "NOT_EXECUTED_BY_STATIC_AUDIT")
        self.assertEqual(report["authority"], "NONE")
        self.assertTrue(ekc.verify_report(ROOT, report))

    def test_release_provenance_gate_does_not_depend_on_historic_pr_prose(self):
        report = ekc.analyze(ROOT, self.sha)
        self.assertEqual(report["product_qualified"], False)
        self.assertEqual(report["host_enforcement"], "BLOCKED_EXTERNAL")
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            release = clone / "docs/RELEASE.md"
            release.write_text(release.read_text("utf-8").replace(
                "The authoritative candidate identity is the exact Git HEAD",
                "The candidate identity is inferred from last year's PR"), "utf-8")
            git(clone, "add", "docs/RELEASE.md")
            git(clone, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: release identity made historical")
            with self.assertRaisesRegex(ValueError, "current release source identity"):
                ekc.analyze(clone, "HEAD")

    def test_report_tampering_and_source_promotions_refused(self):
        report = ekc.analyze(ROOT, self.sha)
        for field, value in (
            ("host_enforcement", "ATTESTED"),
            ("product_qualified", True),
            ("dynamic_execution", "FULLY_COVERED"),
        ):
            fake = copy.deepcopy(report)
            fake[field] = value
            with self.assertRaisesRegex(ValueError, "does not replay"):
                ekc.verify_report(ROOT, fake)

    def test_preregistered_faults_and_deterministic_digest(self):
        a = ekc.stress(self.doc, sessions=1, cases_per_session=2000)
        b = ekc.stress(self.doc, sessions=1, cases_per_session=2000)
        self.assertEqual(a, b)
        self.assertEqual(a["cases"], 2000)
        self.assertEqual(a["preregistered_masks"], 1471)
        self.assertEqual(a["observed_singles"], 14)
        self.assertEqual(a["observed_pairs"], 91)
        self.assertEqual(a["mismatches"], 0)
        self.assertEqual(a["unsafe_promotions"], 0)
        self.assertEqual(a["status"], "PARTIAL_FINITE_MODEL")
        self.assertEqual(a["real_git_mutants"], 0)
        self.assertEqual(a["host_and_reviewer"], "BLOCKED_EXTERNAL")

    def test_deliberate_model_regression_is_detected_by_separate_oracle(self):
        with patch.object(ekc, "_model", return_value=("MODEL_ELIGIBLE_UNATTESTED", "APPROVED")):
            result = ekc.stress(self.doc, sessions=1, cases_per_session=1471)
        self.assertGreater(result["mismatches"], 0)
        self.assertGreater(result["unsafe_promotions"], 0)
        self.assertEqual(result["status"], "REFUTED")

    def test_external_dod_scope_and_temporal_doc_physical_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "fixture"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            contract = clone / ekc.CONTRACT
            original = json.loads(contract.read_text("utf-8"))
            altered = copy.deepcopy(original)
            next(x for x in altered["nodes"] if x["id"] == "E_INDEPENDENT_REVIEW")["scope"] = "SOURCE"
            contract.write_text(json.dumps(altered, indent=2) + "\n", "utf-8")
            git(clone, "add", ekc.CONTRACT)
            git(clone, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: external reviewer self-certification")
            with self.assertRaisesRegex(ValueError, "scope"):
                ekc.contract_at(clone, git(clone, "rev-parse", "HEAD"))
            git(clone, "checkout", "-q", self.sha)
            readme = clone / "README.md"
            readme.write_text(readme.read_text("utf-8") +
                              "\nThe PR38 candidate is the current product.\n", "utf-8")
            git(clone, "add", "README.md")
            git(clone, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: current documentation reverts to old PR38")
            with self.assertRaisesRegex(ValueError, "chronology drift"):
                ekc.analyze(clone, "HEAD")

    def test_original_git_mutants_never_clone_with_local_object_transport(self):
        # Source-only guard on all committed tests; no runtime attestation.
        import ast
        filenames = git(ROOT, "ls-tree", "-r", "--name-only", self.sha, "--", "tests")
        inspected = 0
        for path in filenames.splitlines():
            if not (path.startswith("tests/") and path.endswith(".py")):
                continue
            syntax = ast.parse(git(ROOT, "show", self.sha + ":" + path),
                               filename=path)
            for node in ast.walk(syntax):
                if not isinstance(node, ast.Call):
                    continue
                literals = []
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        literals.append(arg.value)
                    elif isinstance(arg, (ast.List, ast.Tuple)):
                        literals.extend(v.value for v in arg.elts
                                        if isinstance(v, ast.Constant)
                                        and isinstance(v.value, str))
                if "clone" in literals:
                    inspected += 1
                    self.assertNotIn("--local", literals,
                                     path + ":" + str(node.lineno)
                                     + " original-Git hardlink clone is forbidden")
        self.assertGreaterEqual(inspected, 16)

    def test_declared_external_proof_is_not_self_signed_source(self):
        self.assertEqual(
            next(n for n in self.doc["nodes"] if n["id"] == "G_EXTERNAL_EKC")["proof"],
            "INDEPENDENT_OPERATOR_REQUIRED")
        self.assertEqual(
            next(n for n in self.doc["nodes"] if n["id"] == "G_ENGINEERING_KNOWLEDGE")["proof"],
            "INDEPENDENT_OPERATOR_REQUIRED")

    def test_source_only_dod_never_authenticates_external_leaf(self):
        by = {n["id"]: n for n in self.doc["nodes"]}
        self.assertEqual(by["G_ENGINEERING_KNOWLEDGE"]["scope"], "EXTERNAL")
        self.assertEqual(by["G_SOURCE_EKC"]["scope"], "SOURCE")
        self.assertEqual(self.doc["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(self.doc["authority"], "NONE")



    def test_component_index_denominator_trace_and_nonpromotion(self):
        report = ekc.analyze(ROOT, self.sha)
        proof = report["component_contribution"]
        metrics = proof["metrics"]
        rows = proof["rows"]
        self.assertEqual(proof["schema"], "cora-component-contribution/1")
        self.assertEqual(proof["authority"], "NONE")
        self.assertEqual(metrics["tracked_paths"], report["counts"]["files"])
        self.assertEqual(metrics["indexed_paths"], len(rows))
        self.assertEqual(metrics["python_modules"], report["counts"]["modules"])
        self.assertEqual(metrics["source_tools"], report["counts"]["tools"])
        self.assertEqual(metrics["test_sources"], report["counts"]["tests"])
        self.assertEqual(metrics["command_source_bindings"], 71)
        self.assertEqual(
            sum(metrics[name] for name in (
                "entrypoint_modules", "direct_cli_imports", "transitive_cli_imports",
                "not_observed_static")), report["counts"]["modules"])
        self.assertEqual(
            metrics["finite_model_assurance_declared_modules"]
            + metrics["non_finite_cli_declared_modules"]
            + metrics["modules_without_declared_cli_witness"],
            metrics["python_modules"])
        roles = {row["path"]: row.get("declared_capability_role")
                 for row in rows if row["surface"] == "PYTHON_MODULE"}
        self.assertEqual(roles["src/cora/cli.py"],
                         "CLI_ENTRYPOINT_ORCHESTRATOR_SOURCE")
        self.assertGreater(metrics["static_tool_import_edges"], 0)
        self.assertIn("tools/verify_capability_atlas.py",
                      next(row["static_tool_import_candidates"] for row in rows
                           if row["path"] == "src/cora/reticulum.py"))
        self.assertEqual(roles["src/cora/gold_saturation.py"],
                         "FINITE_MODEL_ASSURANCE_DECLARED_NOT_RUNTIME_VALIDATED")
        self.assertEqual(roles["src/cora/continuous.py"],
                         "CLI_COMMAND_SOURCE_DECLARED_NOT_RUNTIME_VALIDATED")
        self.assertEqual(roles["src/cora/native_gold.py"],
                         "NON_COMMAND_SUPPORT_SOURCE_CONSUMERS_INCOMPLETE")
        self.assertEqual(metrics["causal_effects_measured"], 0)
        self.assertEqual(metrics["safe_consolidations_attested"], 0)
        self.assertEqual(len({r["path"] for r in rows}), len(rows))
        self.assertTrue(all(r["causal_effect"] == "NOT_MEASURED" for r in rows))
        self.assertTrue(all(r["consolidation"] == "NOT_AUTHORIZED_UNTESTED" for r in rows))
        self.assertEqual(
            proof["global_consolidation"],
            "BLOCKED_EXTERNAL_BEHAVIORAL_PARITY_AND_GOVERNED_REVIEW")
        fake = copy.deepcopy(report)
        fake["component_contribution"]["rows"][0]["consolidation"] = "SAFE_TO_REMOVE"
        with self.assertRaisesRegex(ValueError, "does not replay"):
            ekc.verify_report(ROOT, fake)

    def test_component_contribution_static_graph_counterexamples(self):
        cli = "src/cora/cli.py"
        direct = "src/cora/direct.py"
        indirect = "src/cora/indirect.py"
        unknown = "src/cora/dynamic_only.py"
        test = "tests/test_direct.py"
        tool = "tools/verify_direct.py"
        paths = sorted([cli, direct, indirect, unknown, test, tool, "docs/README.md"])
        proof = ekc.contribution_index(
            paths, [cli, direct, indirect, unknown], [tool], [test],
            [(cli, direct), (direct, indirect)],
            {"commands": [{"command": "direct", "method_source": direct,
                           "test_source": test, "family": "git-evidence"}]})
        by = {r["path"]: r for r in proof["rows"]}
        self.assertEqual(by[cli]["cli_static"], "ENTRYPOINT")
        self.assertEqual(by[direct]["cli_static"], "DIRECT_CLI_IMPORT")
        self.assertEqual(by[indirect]["cli_static"], "TRANSITIVE_CLI_IMPORT")
        self.assertEqual(by[unknown]["cli_static"], "NOT_OBSERVED_STATIC")
        self.assertEqual(by[unknown]["consumer_status"],
                         "STATIC_CANDIDATES_DYNAMIC_UNKNOWN")
        self.assertEqual(by[direct]["declared_commands"], ["direct"])
        self.assertEqual(by[direct]["declared_families"], ["git-evidence"])
        self.assertEqual(by[direct]["declared_capability_role"],
                         "CLI_COMMAND_SOURCE_DECLARED_NOT_RUNTIME_VALIDATED")
        self.assertEqual(by[direct]["declared_test_witnesses"], [test])
        self.assertEqual(by[tool]["surface"], "OPERATIONAL_TOOL_SOURCE")
        self.assertEqual(by[test]["surface"], "TEST_SOURCE")
        self.assertEqual(proof["metrics"]["tracked_paths"], len(paths))
        self.assertEqual(proof["metrics"]["not_observed_static"], 1)
        self.assertEqual(proof["metrics"]["safe_consolidations_attested"], 0)
        with self.assertRaisesRegex(ValueError, "denominator"):
            ekc.contribution_index(paths + [cli], [cli, direct, indirect, unknown],
                                   [tool], [test], [], {"commands": []})
        with self.assertRaisesRegex(ValueError, "missing module"):
            ekc.contribution_index(paths, [cli, direct, indirect, unknown],
                                   [tool], [test], [(cli, "src/cora/absent.py")],
                                   {"commands": []})
        for command, interaction in (
            ("ordinary", "SYNTHETIC_MODEL_NOT_RUNTIME"),
            ("stress-ordinary", "UNRESTRICTED_RUNTIME"),
        ):
            with self.subTest(command=command), self.assertRaisesRegex(
                    ValueError, "finite-model-only role"):
                ekc.contribution_index(
                    paths, [cli, direct, indirect, unknown],
                    [tool], [test], [],
                    {"commands": [{"command": command, "method_source": direct,
                                   "test_source": test, "family": "finite-models",
                                   "interaction": interaction}]})
        with self.assertRaisesRegex(ValueError, "missing source/test witness"):
            ekc.contribution_index(paths, [cli, direct, indirect, unknown],
                                   [tool], [test], [], {"commands": [
                                       {"command": "fake", "method_source": unknown,
                                        "test_source": "tests/absent.py"}]})

    def test_static_test_import_candidates_are_not_behavioral_receipts(self):
        report = ekc.analyze(ROOT, self.sha)
        index = report["component_contribution"]
        rows = {row["path"]: row for row in index["rows"]}
        self.assertGreater(index["metrics"]["static_test_import_edges"], 0)
        self.assertGreater(index["metrics"]["modules_with_static_test_import_candidate"], 0)
        # This exact committed test declares an import; that is source linkage only.
        self.assertIn("tests/test_pr59_consolidation.py",
                      rows["src/cora/practice_contract.py"]["static_test_import_candidates"])
        self.assertEqual(index["metrics"]["causal_effects_measured"], 0)
        self.assertEqual(index["metrics"]["safe_consolidations_attested"], 0)
        fake = copy.deepcopy(report)
        fake["component_contribution"]["rows"][0]["causal_effect"] = "PROVED_NECESSARY"
        with self.assertRaisesRegex(ValueError, "does not replay"):
            ekc.verify_report(ROOT, fake)

    def test_git_only_static_test_consumer_replay_detects_source_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            original_report = ekc.analyze(clone, "HEAD")
            target = "src/cora/practice_contract.py"
            def refs(document):
                return next(row["static_test_import_candidates"]
                            for row in document["component_contribution"]["rows"]
                            if row["path"] == target)
            self.assertIn("tests/test_pr59_consolidation.py", refs(original_report))
            file = clone / "tests/test_pr59_consolidation.py"
            before = file.read_text("utf-8")
            needle = "from cora.practice_contract import classify, project, verify"
            self.assertEqual(before.count(needle), 1)
            file.write_text(before.replace(needle,
                "# mutant: statically remove practice contract test import"), "utf-8")
            self.assertEqual(ekc.analyze(clone, "HEAD"), original_report)
            git(clone, "add", "tests/test_pr59_consolidation.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: disconnect declarative test import")
            changed = ekc.analyze(clone, "HEAD")
            self.assertNotIn("tests/test_pr59_consolidation.py", refs(changed))
            self.assertEqual(changed["component_contribution"]["metrics"][
                "causal_effects_measured"], 0)
            self.assertTrue(ekc.verify_report(clone, changed))

    def test_granular_ast_symbol_and_test_case_census_with_exact_git_replay(self):
        report = ekc.analyze(ROOT, self.sha)
        proof = report["component_contribution"]
        rows = {row["path"]: row for row in proof["rows"]}
        metrics = proof["metrics"]
        self.assertEqual(metrics["modules_with_symbol_census"], report["counts"]["modules"])
        self.assertEqual(metrics["tests_with_symbol_census"], report["counts"]["tests"])
        self.assertEqual(metrics["module_declarations"], sum(
            len(rows[path]["declared_units"]) for path in rows
            if rows[path]["surface"] == "PYTHON_MODULE"))
        self.assertEqual(metrics["test_case_declarations"], sum(
            len(rows[path]["test_cases"]) for path in rows
            if rows[path]["surface"] == "TEST_SOURCE"))
        self.assertGreater(metrics["module_declarations"], report["counts"]["modules"])
        self.assertEqual(metrics["module_lexical_call_candidates"], sum(
            len(unit["lexical_call_candidates"])
            for row in rows.values() if row["surface"] == "PYTHON_MODULE"
            for unit in row["declared_units"]))
        self.assertEqual(metrics["test_lexical_call_candidates"], sum(
            len(unit["lexical_call_candidates"])
            for row in rows.values() if row["surface"] == "TEST_SOURCE"
            for unit in row["test_cases"]))
        self.assertGreater(metrics["module_lexical_call_candidates"], 0)
        self.assertGreater(metrics["test_lexical_call_candidates"], 0)
        self.assertGreater(metrics["test_case_declarations"], report["counts"]["tests"])
        self.assertIn("snapshot", {unit["symbol"] for unit in
                      rows["src/cora/git_snapshot.py"]["declared_units"]})
        self.assertTrue(any(unit["symbol"].endswith(
            "test_granular_ast_symbol_and_test_case_census_with_exact_git_replay")
            for unit in rows["tests/test_pr40_engineering_closure.py"]["test_cases"]))
        self.assertEqual(metrics["causal_effects_measured"], 0)
        fake = copy.deepcopy(report)
        fake["component_contribution"]["metrics"]["module_declarations"] += 1
        with self.assertRaisesRegex(ValueError, "does not replay"):
            ekc.verify_report(ROOT, fake)

    def test_lexical_qualified_ast_units_and_syntax_failure(self):
        code = ("class Outer:\n"
                "    def method(self):\n"
                "        def nested():\n"
                "            return 1\n"
                "        return nested()\n"
                "    async def test_async(self):\n"
                "        return 2\n")
        units = ekc.structural_units(code, "synthetic.py")
        self.assertEqual([u["symbol"] for u in units], [
            "Outer", "Outer.method", "Outer.method.nested", "Outer.test_async"])
        self.assertEqual([u["kind"] for u in units], [
            "CLASS", "DEF", "DEF", "ASYNC_DEF"])
        by_symbol = {unit["symbol"]: unit for unit in units}
        self.assertEqual(by_symbol["Outer"]["lexical_call_candidates"], [])
        self.assertEqual(by_symbol["Outer.method"]["lexical_call_candidates"],
                         ["nested"])
        self.assertEqual(by_symbol["Outer.method.nested"]["lexical_call_candidates"],
                         [])
        self.assertTrue(all(unit["evidence"] ==
            "AST_DECLARATION_AND_CALL_CANDIDATES_NOT_EXECUTION" for unit in units))
        self.assertEqual([u["symbol"] for u in ekc.structural_units(
            code, "synthetic.py", test_only=True)], ["Outer.test_async"])
        with self.assertRaises(SyntaxError):
            ekc.structural_units("def broken(\n", "synthetic.py")

    def test_component_denominator_negative_omission_and_duplicate_falsifiers(self):
        cli = "src/cora/cli.py"
        module = "src/cora/example.py"
        tool = "tools/example.py"
        test = "tests/test_example.py"
        paths = [cli, module, tool, test]
        for modules, tools, tests in (
            ([cli], [tool], [test]),
            ([cli, module], [], [test]),
            ([cli, module], [tool], []),
            ([cli, module, module], [tool], [test]),
        ):
            with self.subTest(modules=modules, tools=tools, tests=tests):
                with self.assertRaisesRegex(ValueError, "denominator classes"):
                    ekc.contribution_index(paths, modules, tools, tests, [],
                                           {"commands": []})
        proof = ekc.contribution_index(
            paths, [cli, module], [tool], [test], [], {"commands": []})
        self.assertEqual(proof["metrics"]["tracked_paths"], 4)
        self.assertEqual(proof["metrics"]["indexed_paths"], 4)

    def test_static_tool_consumer_unknown_and_negative_contract(self):
        cli = "src/cora/cli.py"
        module = "src/cora/reticulum.py"
        tool = "tools/verify.py"
        rows = ekc.contribution_index(
            [cli, module, tool], [cli, module], [tool], [],
            [(cli, module)], {"commands": []},
            tool_imports=[(tool, module)])
        by = {row["path"]: row for row in rows["rows"]}
        self.assertEqual(by[module]["static_tool_import_candidates"], [tool])
        self.assertEqual(by[module]["causal_effect"], "NOT_MEASURED")
        self.assertEqual(by[cli]["declared_capability_role"],
                         "CLI_ENTRYPOINT_ORCHESTRATOR_SOURCE")
        self.assertEqual(rows["metrics"]["static_tool_import_edges"], 1)
        with self.assertRaisesRegex(ValueError, "tool import edge"):
            ekc.contribution_index(
                [cli, module, tool], [cli, module], [tool], [], [],
                {"commands": []}, tool_imports=[("tools/missing.py", module)])
        with self.assertRaisesRegex(ValueError, "tool import edge"):
            ekc.contribution_index(
                [cli, module, tool], [cli, module], [tool], [], [],
                {"commands": []}, tool_imports=[(tool, "src/cora/missing.py")])

    def test_physical_committed_tool_consumer_disconnection(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            before = ekc.analyze(clone, "HEAD")
            def consumers(report):
                return next(row["static_tool_import_candidates"] for row in
                            report["component_contribution"]["rows"]
                            if row["path"] == "src/cora/reticulum.py")
            witness = "tools/verify_capability_atlas.py"
            self.assertIn(witness, consumers(before))
            path = clone / witness
            text = path.read_text("utf-8")
            original = "from cora.reticulum import ordered_cut"
            self.assertEqual(text.count(original), 1)
            path.write_text(text.replace(original,
                 "# mutant: disconnect statically imported reticulum"), "utf-8")
            self.assertEqual(ekc.analyze(clone, "HEAD"), before)
            git(clone, "add", witness)
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: remove source tool consumer edge")
            after = ekc.analyze(clone, "HEAD")
            self.assertNotIn(witness, consumers(after))
            self.assertTrue(ekc.verify_report(clone, after))
            self.assertEqual(after["component_contribution"]["metrics"][
                "safe_consolidations_attested"], 0)

    def test_native_reticular_external_guard_fails_on_committed_ablation(self):
        """One real subprocess counterfactual, not a universal causal proof."""
        from os import environ
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "repo"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            snippet = (
                "from cora.reticulum import assess_cut, MODEL\n"
                "nodes=[{'id':'E','scope':'EXTERNAL','depends_on':[]},"
                "{'id':'G','scope':'SOURCE','depends_on':['E']}]\n"
                "print(assess_cut(nodes,'G',{'E':MODEL})['status'])\n"
            )
            def oracle():
                return subprocess.run(
                    [sys.executable, "-c", snippet], cwd=clone,
                    env={**environ, "PYTHONPATH": str(clone / "src")},
                    capture_output=True, text=True, check=False, timeout=60)
            before = oracle()
            self.assertEqual(before.returncode, 0, before.stderr)
            self.assertEqual(before.stdout.strip(), "BLOCKED_UNOBSERVED")
            file = clone / "src/cora/reticulum.py"
            content = file.read_text("utf-8")
            original = ('state = (EXTERNAL if node.get("scope") == "EXTERNAL" else\n'
                        '                     observations.get(key, BLOCKED))')
            self.assertEqual(content.count(original), 1)
            mutated = content.replace(original,
                                      'state = observations.get(key, BLOCKED)')
            file.write_text(mutated, "utf-8")
            # Dirty bytes have not changed original committed source identity.
            self.assertEqual(git(clone, "rev-parse", "HEAD"), self.sha)
            git(clone, "add", "src/cora/reticulum.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: remove mandatory external leaf guard")
            after = oracle()
            self.assertEqual(after.returncode, 0, after.stderr)
            self.assertEqual(after.stdout.strip(), "MODEL_ELIGIBLE_UNATTESTED")
            self.assertNotEqual(after.stdout, before.stdout)

    def test_physical_committed_cli_import_mutation_changes_source_not_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            baseline = ekc.analyze(clone, "HEAD")
            module = "src/cora/git_snapshot.py"
            def state(report):
                return next(r["cli_static"] for r in
                            report["component_contribution"]["rows"]
                            if r["path"] == module)
            self.assertEqual(state(baseline), "DIRECT_CLI_IMPORT")
            # A bounded native CLI ablation: same disposable runner and command.
            # This witnesses a single behavior, not universal module necessity.
            from os import environ
            def snapshot_cli():
                return subprocess.run(
                    [sys.executable, "-m", "cora.cli", "snapshot",
                     str(clone), "--revision", "HEAD"],
                    cwd=clone, env={**environ, "PYTHONPATH": str(clone / "src")},
                    capture_output=True, text=True, check=False, timeout=60)
            baseline_cli = snapshot_cli()
            self.assertEqual(baseline_cli.returncode, 0,
                             baseline_cli.stderr[:1000])

            cli = clone / "src/cora/cli.py"
            original = cli.read_text("utf-8")
            needle = "from .git_snapshot import snapshot"
            self.assertEqual(original.count(needle), 1)
            cli.write_text(original.replace(needle,
                                            "# removed import in physical falsifier"),
                           "utf-8")
            # The original Git commit, NOT a dirty working tree, owns the proof.
            self.assertEqual(ekc.analyze(clone, "HEAD"), baseline)
            git(clone, "add", "src/cora/cli.py")
            git(clone, "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "mutant: disconnect CLI import without updating atlas")
            changed = ekc.analyze(clone, "HEAD")
            ablated_cli = snapshot_cli()
            self.assertNotEqual(ablated_cli.returncode, 0,
                                "ablation must be behaviorally discriminating")
            self.assertIn("snapshot", ablated_cli.stderr)
            self.assertNotEqual(changed["commit"], baseline["commit"])
            self.assertNotEqual(state(changed), "DIRECT_CLI_IMPORT")
            self.assertEqual(changed["component_contribution"]["metrics"][
                "safe_consolidations_attested"], 0)
            self.assertTrue(ekc.verify_report(clone, changed))
            forged = copy.deepcopy(changed)
            forged["component_contribution"]["metrics"]["safe_consolidations_attested"] = 1
            with self.assertRaisesRegex(ValueError, "does not replay"):
                ekc.verify_report(clone, forged)



class ClosureEconomyAdversarialTests(unittest.TestCase):
    """Finite counterexamples plus a real two-commit original-Git fixture."""

    def inventory(self, status="BLOCKED_EXTERNAL", scope="EXTERNAL", extra=False):
        items = {"x.json::E01": {"scope": scope, "status": status,
                 "depends_on": [], "claim": "independent human review",
                 "source_path": "x.json"}}
        if extra:
            items["y.json::E02"] = {"scope": "EXTERNAL", "status": "BLOCKED_EXTERNAL",
                 "depends_on": [], "claim": "independent human review",
                 "source_path": "y.json"}
        return {"commit": "a"*40, "contracts": ["x.json"], "nodes": items}

    def test_removal_is_not_evidence_of_closure(self):
        before = self.inventory()
        after = self.inventory()
        after["nodes"] = {}
        report = ekc.closure_change(before, after)
        self.assertEqual(len(report["removed_not_closed"]), 1)
        self.assertEqual(report["verified_closures"], 0)
        self.assertIsNone(report["closure_yield"])

    def test_self_asserted_pass_never_counts(self):
        report = ekc.closure_change(self.inventory(), self.inventory("PASS_SCOPED"))
        self.assertEqual(len(report["asserted_passes_not_verified"]), 1)
        self.assertEqual(report["verified_closures"], 0)

    def test_external_scope_downgrade_detected(self):
        report = ekc.closure_change(self.inventory(), self.inventory(scope="SOURCE"))
        self.assertEqual(report["external_scope_promotions"], ["x.json::E01"])

    def test_duplicate_wording_is_only_a_candidate(self):
        report = ekc.closure_change(self.inventory(), self.inventory(extra=True))
        self.assertEqual(len(report["possible_duplicate_wording_not_merged"]), 1)
        self.assertEqual(report["verified_closures"], 0)

    def test_original_git_mutation_and_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "repo"
            root.mkdir()
            git(root, "init", "-q")
            git(root, "config", "user.name", "fixture")
            git(root, "config", "user.email", "fixture@example.invalid")
            location = root / ".cora/contracts/dod"
            location.mkdir(parents=True)
            path = location / "example.json"
            doc = {"schema": "test", "nodes": [
                {"id": "E01", "scope": "EXTERNAL", "status": "BLOCKED_EXTERNAL",
                 "depends_on": [], "claim": "external decision"}]}
            path.write_text(json.dumps(doc), encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "baseline")
            base = git(root, "rev-parse", "HEAD")
            doc["nodes"][0]["scope"] = "SOURCE"
            path.write_text(json.dumps(doc), encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "unsafe semantic promotion")
            result = ekc.closure_delta(root, base)
            self.assertEqual(result["status"], "REFUTED")
            self.assertTrue(ekc.verify_closure_delta(root, result))
            receipt = Path(folder) / "refuted.json"
            receipt.write_text(json.dumps(result), encoding="utf-8")
            proc = subprocess.run([
                sys.executable, str(ROOT / "tools/verify_engineering_closure.py"),
                "--repo", str(root), "--verify-closure", str(receipt)],
                capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            fake = copy.deepcopy(result)
            fake["counts"]["verified_closures"] = 1
            with self.assertRaisesRegex(ValueError, "does not replay"):
                ekc.verify_closure_delta(root, fake)
            with self.assertRaises(ValueError):
                ekc.closure_delta(root, git(root, "rev-parse", "HEAD"), base)



if __name__ == "__main__":
    unittest.main()
