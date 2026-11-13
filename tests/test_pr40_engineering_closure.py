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
        self.assertEqual(metrics["static_isolation_review_count"],
                         len(metrics["static_isolation_review_paths"]))
        self.assertTrue(all(path.startswith("src/cora/") for path in
                            metrics["static_isolation_review_paths"]))
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
        self.assertEqual(by[unknown]["consolidation_review"],
                         "STATIC_ISOLATION_REVIEW_ONLY_DYNAMIC_UNKNOWN")
        self.assertEqual(by[direct]["consolidation_review"],
                         "SOURCE_CONSUMER_OBSERVED_OR_UNRESOLVED_REQUIRES_COUNTERFACTUAL")
        self.assertEqual(by[cli]["consolidation_review"],
                         "CANONICAL_ENTRYPOINT_NOT_A_CONSOLIDATION_CANDIDATE")
        self.assertEqual(proof["metrics"]["static_isolation_review_paths"],
                         [unknown])
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

    def test_exact_git_component_dod_all_leaves_noncompensatory(self):
        report = ekc.analyze(ROOT, self.sha)
        dod = report["component_dod"]
        rows = {node["id"]: node for node in dod["nodes"]}
        self.assertEqual(dod["logic"], "NONCOMPENSATORY_AND")
        self.assertEqual(dod["abstract_goal"],
                         "EVIDENCE_BOUND_CAUSAL_CONTRIBUTION_AND_NO_LOSS_CONSOLIDATION")
        self.assertEqual(dod["source_goal"], "G_COMPONENT_SOURCE")
        self.assertEqual(dod["global_goal"], "G_COMPONENT")
        self.assertEqual(dod["global_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(dod["authority"], "NONE")
        self.assertEqual(dod["behavioral_equivalence"], "NOT_ATTESTED")
        self.assertFalse(dod["safe_consolidation_authorized"])
        self.assertEqual(len(dod["nodes"]), 14)
        self.assertEqual(set(dod["ordered_cut"]), set(rows))
        self.assertIn("G_COMPONENT_SOURCE", rows["G_COMPONENT"]["depends_on"])
        self.assertEqual(rows["G_COMPONENT"]["scope"], "EXTERNAL")
        for key in ("E1_NATIVE_BEHAVIOR_PARITY", "E2_INDEPENDENT_ABLATION",
                    "E3_INDEPENDENT_HOST_REVIEW"):
            self.assertEqual(rows[key]["scope"], "EXTERNAL")
            self.assertEqual(rows[key]["status"], "BLOCKED_EXTERNAL")
        self.assertEqual(rows["L4_NEGATIVE_ORACLES"]["status"],
                         "NATIVE_TEST_EXECUTION_NOT_ATTESTED_BY_REPORT")
        self.assertTrue(ekc.verify_report(ROOT, report))
        forged = copy.deepcopy(report)
        forged["component_dod"]["global_status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "does not replay"):
            ekc.verify_report(ROOT, forged)

    def test_component_dod_denominator_and_false_consolidation_fail_closed(self):
        report = ekc.analyze(ROOT, self.sha)
        source_index = report["component_contribution"]
        for field, value in (
            ("safe_consolidations_attested", 1),
            ("causal_effects_measured", 1),
            ("tracked_paths", source_index["metrics"]["tracked_paths"] - 1),
        ):
            modified = copy.deepcopy(source_index)
            modified["metrics"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ekc.component_dod_assessment(modified)
        modified = copy.deepcopy(source_index)
        modified["rows"][0]["consolidation"] = "SAFE_TO_REMOVE"
        with self.assertRaises(ValueError):
            ekc.component_dod_assessment(modified)
        modified = copy.deepcopy(source_index)
        modified["rows"] = modified["rows"][:-1]
        with self.assertRaises(ValueError):
            ekc.component_dod_assessment(modified)

    def test_physical_committed_global_dod_edge_removal_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            baseline = ekc.analyze(clone, "HEAD")
            self.assertEqual(baseline["component_dod"]["global_status"],
                             "BLOCKED_EXTERNAL")
            module = clone / "tools/verify_engineering_closure.py"
            before = module.read_text("utf-8")
            old = '"G_COMPONENT": ["G_COMPONENT_SOURCE", "I1_TRACE",'
            new = '"G_COMPONENT": ["I1_TRACE",'
            self.assertEqual(before.count(old), 1)
            module.write_text(before.replace(old, new), "utf-8")
            # Replaying the prior source SHA cannot legitimize uncommitted bytes.
            self.assertEqual(ekc.analyze(clone, "HEAD"), baseline)
            git(clone, "add", "tools/verify_engineering_closure.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: orphan source DoD from the global root")
            from os import environ
            run = subprocess.run(
                [sys.executable, "tools/verify_engineering_closure.py",
                 "--repo", str(clone), "--revision", "HEAD"],
                cwd=clone, env={**environ, "PYTHONPATH": str(clone / "src")},
                capture_output=True, text=True, check=False, timeout=60)
            self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
            self.assertIn("component DoD orphan", run.stdout + run.stderr)

    def test_closed_world_source_universe_is_exhaustive_not_behavioral(self):
        a = "a" * 40
        b = "b" * 40
        c = "c" * 40
        before = {"src/cora/cli.py": a, "src/cora/helper.py": b}
        unchanged = ekc.engine_source_universe(before, before)
        self.assertEqual(unchanged["source_byte_identity"],
                         "PASS_SCOPED_EXHAUSTIVE")
        self.assertEqual(unchanged["identical_blobs"], unchanged["denominator"])
        self.assertEqual(unchanged["accounted_paths"], unchanged["denominator"])
        self.assertEqual(unchanged["denominator"], 2)
        self.assertEqual(unchanged["full_runtime_behavior_equivalence"],
                         "NOT_ATTESTED")
        self.assertEqual(unchanged["authorization"], "NONE")
        for change, expected in (
            ({"src/cora/cli.py": a, "src/cora/helper.py": c}, "CHANGED_BLOB"),
            ({"src/cora/cli.py": a}, "REMOVED"),
            ({"src/cora/cli.py": a, "src/cora/helper.py": b,
              "src/cora/new.py": c}, "ADDED"),
        ):
            with self.subTest(expected=expected):
                observed = ekc.engine_source_universe(before, change)
                self.assertEqual(observed["source_byte_identity"], "REFUTED")
                self.assertEqual(observed["accounted_paths"], len(
                    set(before) | set(change)))
                self.assertIn(expected,
                              {r["difference"] for r in observed["rows"]})
                self.assertEqual(observed["full_runtime_behavior_equivalence"],
                                 "NOT_ATTESTED")
        for invalid in (
            {"src/cora/cli.py": "fake"},
            {"src/cora/../unsafe.py": a, "src/cora/cli.py": a},
            {"src/cora/helper.py": b},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                ekc.engine_source_universe(before, invalid)

    def test_full_engine_source_universe_exact_git_replay_and_forged_receipt(self):
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        report = ekc.analyze(ROOT, self.sha, equivalence_base=base)
        universe = report["engine_source_universe"]
        self.assertEqual(universe["base"], base)
        self.assertEqual(universe["head"], self.sha)
        self.assertEqual(universe["denominator"], report["counts"]["modules"])
        self.assertEqual(universe["accounted_paths"], universe["denominator"])
        self.assertEqual(universe["identical_blobs"], universe["denominator"])
        self.assertEqual(universe["changed_blobs"], 0)
        self.assertEqual(universe["added_blobs"], 0)
        self.assertEqual(universe["removed_blobs"], 0)
        self.assertEqual(universe["source_byte_identity"],
                         "PASS_SCOPED_EXHAUSTIVE")
        self.assertEqual(universe["content_readback_paths"], universe["denominator"])
        self.assertEqual(universe["content_byte_equal_paths"], universe["denominator"])
        self.assertEqual(universe["content_byte_different_paths"], [])
        self.assertEqual(universe["exact_content_parity"], "PASS_SCOPED_EXHAUSTIVE")
        self.assertEqual(universe["full_runtime_behavior_equivalence"],
                         "NOT_ATTESTED")
        self.assertEqual(report["component_dod"]["global_status"],
                         "BLOCKED_EXTERNAL")
        self.assertTrue(ekc.verify_report(ROOT, report))
        fake = copy.deepcopy(report)
        fake["engine_source_universe"]["rows"][0]["before_oid"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "does not replay"):
            ekc.verify_report(ROOT, fake)
        with self.assertRaisesRegex(ValueError, "ancestor"):
            ekc.git_engine_source_universe(ROOT, self.sha, base)

    def test_original_git_physical_mutation_breaks_exhaustive_source_identity(self):
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            baseline = ekc.git_engine_source_universe(clone, base, "HEAD")
            self.assertEqual(baseline["source_byte_identity"],
                             "PASS_SCOPED_EXHAUSTIVE")
            path = clone / "src/cora/reticulum.py"
            path.write_text(path.read_text("utf-8") +
                            "\n# source universe falsifier\n", "utf-8")
            self.assertEqual(ekc.git_engine_source_universe(
                clone, base, "HEAD"), baseline)
            git(clone, "add", "src/cora/reticulum.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: engine source blob identity regression")
            changed = ekc.analyze(clone, "HEAD", equivalence_base=base)
            index = changed["engine_source_universe"]
            self.assertEqual(index["source_byte_identity"], "REFUTED")
            self.assertEqual(index["changed_blobs"], 1)
            self.assertEqual(index["identical_blobs"] + index["changed_blobs"],
                             index["denominator"])
            self.assertEqual(index["content_readback_paths"], index["denominator"])
            self.assertEqual(index["content_byte_equal_paths"], index["denominator"] - 1)
            self.assertEqual(index["content_byte_different_paths"],
                             ["src/cora/reticulum.py"])
            self.assertEqual(index["exact_content_parity"],
                             "REFUTED_SOURCE_CONTENT_PARITY")
            self.assertEqual(index["full_runtime_behavior_equivalence"],
                             "NOT_ATTESTED")
            self.assertTrue(ekc.verify_report(clone, changed))

    def test_standalone_source_universe_cli_and_exact_report_replay(self):
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        import os
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / "source-universe.json"
            command = [sys.executable, str(ROOT / "tools/verify_engineering_closure.py"),
                       "--repo", str(ROOT), "--revision", self.sha,
                       "--equivalence-base", base, "--output", str(receipt)]
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            run = subprocess.run(command, cwd=ROOT, env=env,
                                 capture_output=True, text=True,
                                 check=False, timeout=90)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            document = json.loads(receipt.read_text("utf-8"))
            self.assertEqual(document["engine_source_universe"]["source_byte_identity"],
                             "PASS_SCOPED_EXHAUSTIVE")
            self.assertEqual(document["engine_source_universe"]["exact_content_parity"],
                             "PASS_SCOPED_EXHAUSTIVE")
            replay = subprocess.run(
                [sys.executable, str(ROOT / "tools/verify_engineering_closure.py"),
                 "--repo", str(ROOT), "--verify-report", str(receipt)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                check=False, timeout=90)
            self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
            self.assertEqual(json.loads(replay.stdout)["status"],
                             "SOURCE_REPLAY_SCOPED")

    def test_previous_engineering_receipt_semantics_preserved_under_extension(self):
        """Baseline verifier runs on baseline Git, new verifier on PR HEAD."""
        from types import ModuleType
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        previous = ModuleType("baseline_original_git_engineering_closure")
        baseline_code = git(ROOT, "show",
                            base + ":tools/verify_engineering_closure.py")
        exec(compile(baseline_code, "baseline_engineering_closure.py", "exec"),
             previous.__dict__)
        a = previous.analyze(ROOT, base)
        b = ekc.analyze(ROOT, self.sha)
        self.assertEqual(set(b) - set(a), {"component_contribution", "component_dod"})
        self.assertEqual(set(a) - set(b), set())
        for field in a:
            if field not in ("commit", "tree", "source_digest_sha256"):
                with self.subTest(field=field):
                    self.assertEqual(a[field], b[field])
        self.assertTrue(previous.verify_report(ROOT, a))
        self.assertTrue(ekc.verify_report(ROOT, b))
        self.assertNotEqual(a["commit"], b["commit"])
        self.assertNotEqual(a["source_digest_sha256"], b["source_digest_sha256"])

    def test_native_engine_behavior_parity_across_exact_git_revisions(self):
        """A fixed native sample: source blobs give broader identity, not universal runtime proof."""
        from os import environ
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        snippet = (
            "import json\n"
            "from cora.reticulum import MODEL, assess_cut, ordered_cut, invalidated_witnesses\n"
            "nodes=[{'id':'A','scope':'SOURCE','depends_on':[]},"
            "{'id':'E','scope':'EXTERNAL','depends_on':[]},"
            "{'id':'G','scope':'EXTERNAL','depends_on':['A','E']}]\n"
            "a=assess_cut(nodes,'G',{'A':MODEL,'E':MODEL})\n"
            "w=[{'id':'W','dependencies':['src/cora/reticulum.py'],"
            "'revision':'a'*40,'scope':'SOURCE'}]\n"
            "b=invalidated_witnesses(w,['src/cora/reticulum.py'],source_revision='b'*40)\n"
            "print(json.dumps({'cut':ordered_cut(nodes,'G'),'states':a['states'],"
            "'blocked':a['blocked_leaves'],'invalidation':b['witnesses']},sort_keys=True))\n"
        )
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            def run(revision):
                git(clone, "checkout", "-q", "-f", revision)
                return subprocess.run(
                    [sys.executable, "-c", snippet], cwd=clone,
                    env={**environ, "PYTHONPATH": str(clone / "src")},
                    capture_output=True, text=True, check=False, timeout=60)
            prior = run(base)
            candidate = run(self.sha)
            self.assertEqual(prior.returncode, 0, prior.stderr)
            self.assertEqual(candidate.returncode, 0, candidate.stderr)
            self.assertEqual(json.loads(prior.stdout), json.loads(candidate.stdout))
            observed = json.loads(candidate.stdout)
            self.assertEqual(observed["states"]["E"], "BLOCKED_EXTERNAL")
            self.assertEqual(observed["invalidation"][0]["state"],
                             "INVALIDATED_BY_CHANGED_SOURCE")

    def test_original_git_product_source_oids_unchanged_across_pr69(self):
        """All CORA engine module bytes match base; not a runtime equivalence claim."""
        base = "57dd5c4fb6317d9a9e951fcbebac9c7aa5560b6f"
        def module_oids(revision):
            paths = [p for p in git(ROOT, "ls-tree", "-r", "--name-only",
                                    revision, "--", "src/cora").splitlines()
                     if p.startswith("src/cora/") and p.endswith(".py")]
            return {p: git(ROOT, "rev-parse", revision + ":" + p)
                    for p in paths}
        before, after = module_oids(base), module_oids(self.sha)
        self.assertEqual(set(before), set(after))
        self.assertGreaterEqual(len(before), 60)
        self.assertEqual(before, after)
        # The assurance verifier does change; do not call the entire repo equal.
        verifier = "tools/verify_engineering_closure.py"
        self.assertNotEqual(git(ROOT, "rev-parse", base + ":" + verifier),
                            git(ROOT, "rev-parse", self.sha + ":" + verifier))
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            unit = clone / "src/cora/reticulum.py"
            content = unit.read_text("utf-8")
            unit.write_text(content + "\\n# simulated intentional product change\\n", "utf-8")
            git(clone, "add", "src/cora/reticulum.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: change a real engine implementation")
            self.assertNotEqual(git(ROOT, "rev-parse", base + ":src/cora/reticulum.py"),
                                git(clone, "rev-parse", "HEAD:src/cora/reticulum.py"))

    def test_actual_wrapper_consolidation_has_original_git_behavioral_parity(self):
        """Execute former source owner on the same Git inputs, not just compare labels."""
        from types import ModuleType
        former = "c03de9376b0de8455adf196a16e2f76cdbc95f0b"
        source_code = git(ROOT, "show",
                          former + ":tools/verify_engineering_closure.py")
        self.assertIn("def static_test_consumers(", source_code)
        previous = ModuleType("previous_component_closure")
        exec(compile(source_code, "previous_component_closure.py", "exec"),
             previous.__dict__)
        paths = git(ROOT, "ls-tree", "-r", "--name-only", self.sha).splitlines()
        modules = [p for p in paths if p.startswith("src/cora/")
                   and p.count("/") == 2 and p.endswith(".py")]
        tests = [p for p in paths if p.startswith("tests/test_")
                 and p.count("/") == 1 and p.endswith(".py")]
        old_edges = previous.static_test_consumers(ROOT, self.sha, tests, modules)
        new_edges = ekc.static_python_consumers(ROOT, self.sha, tests, modules)
        self.assertEqual(old_edges, new_edges)
        self.assertGreater(len(new_edges), 0)
        self.assertEqual(new_edges, ekc.static_python_consumers(
            ROOT, self.sha, list(reversed(tests)), list(reversed(modules))))
        self.assertFalse(hasattr(ekc, "static_test_consumers"),
                         "redundant compatibility wrapper should stay removed")

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
        self.assertEqual(by[module]["consolidation_review"],
                         "SOURCE_CONSUMER_OBSERVED_OR_UNRESOLVED_REQUIRES_COUNTERFACTUAL")
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

    def test_native_chat_bundle_external_review_guard_ablation(self):
        """Third physical causal witness: self-approval must be rejected before mutation."""
        from os import environ
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "source"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(clone))
            git(clone, "checkout", "-q", self.sha)
            script = (
                "import importlib.util\n"
                "from cora.chat_bundle import validate_step\n"
                "spec=importlib.util.spec_from_file_location('fixture',"
                "'tests/test_pr46_chat_bundle.py')\n"
                "mod=importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(mod)\n"
                "fixture=mod.ChatBundleTests('test_append_roundtrip_two_rounds_and_exact_handoff')\n"
                "fixture.setUp()\n"
                "step=fixture.step()\n"
                "step['dod']['nodes'][1]['observation']='REPORTED_OBSERVED'\n"
                "step['dod']['nodes'][1]['evidence_refs']=['self-reported-review']\n"
                "try:\n"
                "    validate_step(step)\n"
                "except ValueError as exc:\n"
                "    print('REJECTED:'+str(exc))\n"
                "else:\n"
                "    print('ACCEPTED')\n"
            )
            def run():
                return subprocess.run(
                    [sys.executable, "-c", script], cwd=clone,
                    env={**environ, "PYTHONPATH": str(clone / "src")},
                    capture_output=True, text=True, check=False, timeout=60)
            original = run()
            self.assertEqual(original.returncode, 0, original.stderr)
            self.assertEqual(original.stdout.strip(),
                             "REJECTED:external evidence cannot be self-approved")
            path = clone / "src/cora/chat_bundle.py"
            before = path.read_text("utf-8")
            guard = ('        if not n["depends_on"] and n["scope"] == "EXTERNAL" '
                     'and n["observation"] == "REPORTED_OBSERVED":\n'
                     '            raise ValueError("external evidence cannot be self-approved")')
            self.assertEqual(before.count(guard), 1)
            path.write_text(before.replace(guard,
                 '        if False:\n'
                 '            raise ValueError("external evidence cannot be self-approved")'),
                 "utf-8")
            git(clone, "add", "src/cora/chat_bundle.py")
            git(clone, "-c", "user.name=fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm",
                "mutant: chat bundle external approval guard removed")
            changed = run()
            self.assertEqual(changed.returncode, 0, changed.stderr)
            self.assertEqual(changed.stdout.strip(), "ACCEPTED")
            self.assertNotEqual(original.stdout, changed.stdout)

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
