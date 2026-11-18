"""PR50 real Git target fixtures, bounded evidence, negative mutations and no promotion."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cora.portable_assurance import run_portable, verify_portable, render_portable_html
from tools.verify_crossrepo_convergence import evaluate

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class PortableCrossRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence = self.root / "witnesses"
        self.evidence.mkdir()
        (self.evidence / "observed.txt").write_bytes(b"mock reported HTTP+browser evidence\n")
        self.repos = []
        for idx, source in enumerate(("web/app.mjs", "src/app.py")):
            repo = self.root / ("target" + str(idx))
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Portable fixture")
            git(repo, "config", "user.email", "fixture@example.invalid")
            file = repo / source
            file.parent.mkdir()
            file.write_text(
                "throw new Error('NEVER_EXECUTED'); import('./dynamic.mjs');\n" if idx == 0
                else "raise RuntimeError('NEVER_EXECUTED')\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "fixture original source")
            self.repos.append((repo, git(repo, "rev-parse", "HEAD"), source))
        self.profile = self.root / "profile.json"

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self, i=0):
        repo, commit, source = self.repos[i]
        return {
            "schema": "cora-portable-target/1",
            "target_repo": "Luke883i/" + ("teddy" if i == 0 else "NILO"),
            "revision": commit,
            "owners": [{"id": "original-owner", "path": source}],
            "witnesses": [{
                "id": "browser-claim", "category": "BROWSER", "path": "observed.txt",
                "sha256": hashlib.sha256((self.evidence / "observed.txt").read_bytes()).hexdigest(),
                "source_commit": commit, "oracle_id": "original-negative-oracle",
                "reported_outcome": "PASS_REPORTED_UNATTESTED"
            }],
            "method_links": [{
                "id": "LUMEN-to-Teddy" if i == 0 else "CORA-to-NILO",
                "kind": "METHOD_TRANSFER", "source_repo": "Luke883i/lumen" if i == 0 else "Luke883i/cora",
                "source_commit": "a" * 40 if i == 0 else "b" * 40,
                "target_owner": "original-owner", "target_commit": commit,
                "source_reference": "https://github.com/Luke883i/" + ("lumen" if i == 0 else "cora") + "/pull/1"
            }]
        }

    def write(self, doc):
        self.profile.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    def run_it(self, i=0, evidence=False):
        self.write(self.contract(i))
        repo = self.repos[i][0]
        return run_portable(repo, "HEAD", self.profile,
                            evidence_dir=self.evidence if evidence else None)

    def test_two_different_real_git_targets_and_replay(self):
        for i in range(2):
            with self.subTest(target=i):
                result = self.run_it(i, evidence=True)
                self.assertTrue(verify_portable(self.repos[i][0], result, self.profile,
                                evidence_dir=self.evidence))
                self.assertEqual(result["governed_status"], "BLOCKED_EXTERNAL")
                self.assertEqual(result["authorization"], "NONE")
                self.assertEqual(result["method_links"][0]["state"],
                                 "FOREIGN_GIT_SOURCE_UNVERIFIED")
                self.assertEqual(result["evidence"][0]["state"],
                                 "INTEGRITY_VERIFIED_EXECUTION_UNATTESTED")
                self.assertEqual(result["source_status"], "SOURCE_PARTIAL_NOT_CONFIGURED")
                self.assertEqual(result["source_process"]["unconfigured_manifests"], {
                    "artifact_roles": "cora.artifact-roles.json",
                    "python_candidate_graph": "cora.ontology.json"})
                self.assertEqual([x["method"] for x in result["source_process"]["results"]
                                 if x["status"] == "NOT_CONFIGURED"],
                                 ["artifact_roles", "python_candidate_graph"])
                self.assertEqual(len(result["source_process"]["results"]), 8)
                self.assertEqual(result["js_import_graph"],
                                 "NOT_OBSERVED_NONPYTHON_CONSUMERS_UNKNOWN")

    def test_js_parser_ships_with_installed_distribution(self):
        from importlib.resources import files
        parser = files("cora").joinpath("portable_js_imports.mjs")
        self.assertTrue(parser.is_file(), "parser missing from installed Python distribution")
        self.assertIn("SourceTextModule", parser.read_text(encoding="utf-8"))

    def test_opt_in_js_static_parser_and_dynamic_unknown(self):
        repo = self.repos[0][0]
        (repo / "web" / "app.mjs").write_text(
            "import { value } from './module.mjs';\n"
            "throw new Error('NEVER_EXECUTED'); import('./dynamic.mjs');\n",
            encoding="utf-8")
        (repo / "web" / "module.mjs").write_text("export const value = 1;\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "static import and dangerous top-level trap")
        self.repos[0] = (repo, git(repo, "rev-parse", "HEAD"), "web/app.mjs")
        self.write(self.contract())
        r = run_portable(repo, "HEAD", self.profile, parse_js=True)
        self.assertEqual(r["js_import_graph"]["scope"],
                         "PARSED_ESM_ONLY_DYNAMIC_AND_RUNTIME_UNKNOWN")
        self.assertIn("./module.mjs",
                      [x["specifier"] for x in r["js_import_graph"]["imports"]])
        self.assertTrue(r["js_import_graph"]["unknown"])
        self.assertFalse(r["js_import_graph"]["runtimeObserved"])
        self.assertTrue(verify_portable(repo, r, self.profile, parse_js=True))
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(repo, r, self.profile, parse_js=False)

    def test_js_syntax_error_is_not_false_green(self):
        repo = self.repos[0][0]
        (repo / "web" / "invalid.js").write_text("import {\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "syntax-negative")
        self.repos[0] = (repo, git(repo, "rev-parse", "HEAD"), "web/app.mjs")
        self.write(self.contract())
        result = run_portable(repo, "HEAD", self.profile, parse_js=True)
        self.assertEqual(result["source_status"], "DEBT_BLOCKED")
        self.assertEqual(len(result["js_import_graph"]["syntaxErrors"]), 1)
        self.assertTrue(verify_portable(repo, result, self.profile, parse_js=True))
        self.assertEqual(result["authorization"], "NONE")

    def test_tampered_receipt_and_html_rejected(self):
        result = self.run_it(evidence=True)
        html = render_portable_html(result)
        self.assertTrue(verify_portable(self.repos[0][0], result, self.profile,
                                        evidence_dir=self.evidence, html_page=html))
        modified = copy.deepcopy(result)
        modified["governed_status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(self.repos[0][0], modified, self.profile, evidence_dir=self.evidence)
        with self.assertRaisesRegex(ValueError, "HTML mismatch"):
            verify_portable(self.repos[0][0], result, self.profile,
                            evidence_dir=self.evidence, html_page=html.replace("BLOCKED_EXTERNAL", "PASS"))

    def test_symlink_owner_is_not_source_implementation(self):
        repo = self.repos[0][0]
        (repo / "web" / "linked.mjs").symlink_to("app.mjs")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "symlink cannot become owner")
        self.repos[0] = (repo, git(repo, "rev-parse", "HEAD"), "web/linked.mjs")
        self.write(self.contract())
        with self.assertRaisesRegex(ValueError, "qualified as original Git source"):
            run_portable(repo, "HEAD", self.profile)

    def test_tampered_bytes_and_symlink_rejected(self):
        result = self.run_it(evidence=True)
        (self.evidence / "observed.txt").write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "evidence tamper"):
            verify_portable(self.repos[0][0], result, self.profile, evidence_dir=self.evidence)
        (self.evidence / "observed.txt").unlink()
        (self.evidence / "observed.txt").symlink_to(self.profile)
        with self.assertRaisesRegex(ValueError, "symlink"):
            run_portable(self.repos[0][0], "HEAD", self.profile, evidence_dir=self.evidence)

    def test_profile_and_original_git_negative_family_matrix(self):
        original = self.contract()
        mutated = []
        def mutate(name, field, value):
            data = copy.deepcopy(original)
            field(data, value)
            mutated.append((name, data))
        mutate("stale-sha", lambda d,v:d.update(revision=v), "f" * 40)
        mutate("owner-path", lambda d,v:d["owners"][0].update(path=v), "../unbound")
        mutate("owner-missing", lambda d,v:d["owners"][0].update(path=v), "missing.py")
        mutate("duplicate-owner", lambda d,v:d["owners"].append(d["owners"][0].copy()), None)
        mutate("wrong-category", lambda d,v:d["witnesses"][0].update(category=v), "CERTIFIED_REAL_USER")
        mutate("missing-oracle", lambda d,v:d["witnesses"][0].update(oracle_id=v), "")
        mutate("witness-outcome-promotion", lambda d,v:d["witnesses"][0].update(reported_outcome=v), "PASS")
        mutate("witness-sha-mismatch", lambda d,v:d["witnesses"][0].update(source_commit=v), "d" * 40)
        mutate("witness-path-traversal", lambda d,v:d["witnesses"][0].update(path=v), "../secrets")
        mutate("fake-transfer-kind", lambda d,v:d["method_links"][0].update(kind=v), "VERIFIED_RUNTIME_DEPENDENCY")
        mutate("transfer-stale", lambda d,v:d["method_links"][0].update(target_commit=v), "c" * 40)
        mutate("upstream-forged-domain", lambda d,v:d["method_links"][0].update(source_reference=v), "https://example.invalid/claim")
        self.assertEqual(len(mutated), 12)
        for name, candidate in mutated:
            with self.subTest(mutation=name):
                self.write(candidate)
                with self.assertRaises(ValueError):
                    run_portable(self.repos[0][0], "HEAD", self.profile)
        self.assertEqual(evaluate(ROOT)["product_status"], "BLOCKED_EXTERNAL")

    def test_upstream_original_git_readback_and_source_staleness(self):
        doc = self.contract(0)
        source_repo, source_sha, _ = self.repos[1]
        doc["method_links"][0]["source_commit"] = source_sha
        self.write(doc)
        result = run_portable(self.repos[0][0], "HEAD", self.profile,
                              upstream_paths={"Luke883i/lumen": source_repo})
        self.assertEqual(result["method_links"][0]["state"],
                         "FOREIGN_COMMIT_READ_BACK_METHOD_ADOPTION_UNATTESTED")
        self.assertTrue(verify_portable(self.repos[0][0], result, self.profile,
                        upstream_paths={"Luke883i/lumen": source_repo}))
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(self.repos[0][0], result, self.profile)
        doc["method_links"][0]["source_commit"] = "1" * 40
        self.write(doc)
        with self.assertRaisesRegex(ValueError, "upstream source commit not read back"):
            run_portable(self.repos[0][0], "HEAD", self.profile,
                         upstream_paths={"Luke883i/lumen": source_repo})

    def test_new_git_revision_invalidates_old_profile(self):
        result = self.run_it()
        repo = self.repos[0][0]
        (repo / "web" / "extra.mjs").write_text("export const newCode = 1;\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "new source revision")
        with self.assertRaisesRegex(ValueError, "stale source revision"):
            run_portable(repo, "HEAD", self.profile)
        # Historical immutable receipts MUST replay for their *old* commit;
        # they must not be promoted to observations about the new HEAD.
        self.assertTrue(verify_portable(repo, result, self.profile))
        self.assertNotEqual(result["commit"], git(repo, "rev-parse", "HEAD"))

    def test_cli_one_run_transport(self):
        self.write(self.contract())
        receipt = self.root / "portable.json"
        html = self.root / "portable.html"
        cmd = [sys.executable, "-m", "cora.cli", "process-run",
               str(self.repos[0][0]), "--one-run", "--portable-profile",
               str(self.profile), "--output", str(receipt), "--atlas-html", str(html)]
        launched = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(launched.returncode, 2, launched.stderr)
        self.assertTrue(receipt.is_file(), launched.stderr)
        replay = subprocess.run([sys.executable, "-m", "cora.cli", "verify-process",
                                  str(receipt), "--repo", str(self.repos[0][0]),
                                  "--one-run", "--portable-profile", str(self.profile),
                                  "--atlas-html", str(html)],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
        self.assertIn("BLOCKED_EXTERNAL", replay.stdout)

    def test_p1_missing_in_committed_git_is_not_a_failed_configured_method(self):
        from cora.process_suite import run_suite, verify_suite
        for idx in range(2):
            repo, sha, _ = self.repos[idx]
            source_before = git(repo, "status", "--porcelain")
            strict = run_suite(repo, sha, process="full")
            self.assertEqual(strict["status"], "DEBT_BLOCKED")
            portable = self.run_it(idx)
            self.assertEqual(portable["source_status"], "SOURCE_PARTIAL_NOT_CONFIGURED")
            checks = {x["method"]:x for x in portable["source_process"]["results"]}
            self.assertEqual(len(checks), 8, "no method silently disappears from the dossier")
            self.assertEqual(checks["artifact_roles"]["status"], "NOT_CONFIGURED")
            self.assertEqual(checks["python_candidate_graph"]["status"], "NOT_CONFIGURED")
            self.assertEqual(checks["holistic_archaeology"]["status"], "PARTIAL_SCOPED_NOT_CONFIGURED")
            self.assertEqual(checks["git_snapshot"]["status"], "REUSED_SCOPED_FROM_HOLISTIC")
            self.assertEqual(checks["git_archaeology"]["status"], "REUSED_SCOPED_FROM_HOLISTIC")
            self.assertEqual(portable["governed_status"], "BLOCKED_EXTERNAL")
            self.assertEqual(portable["authorization"], "NONE")
            self.assertEqual(portable["target_name_scope"], "CALLER_DECLARED_UNAUTHENTICATED")
            self.assertTrue(verify_suite(repo, portable["source_process"]))
            self.assertEqual(git(repo,"status","--porcelain"), source_before)
            self.assertFalse((repo / "cora.ontology.json").exists())
            self.assertFalse((repo / "cora.artifact-roles.json").exists())
            # Dirty untracked manifests are not committed source, and never fill gaps.
            (repo / "cora.artifact-roles.json").write_text("not original Git bytes")
            (repo / "cora.ontology.json").write_text("not original Git bytes")
            after = self.run_it(idx)
            self.assertEqual(after, portable)
            self.assertTrue(verify_portable(repo, portable, self.profile))
            (repo / "cora.artifact-roles.json").unlink()
            (repo / "cora.ontology.json").unlink()

    def test_p1_invalid_present_is_debt_and_valid_present_is_scoped(self):
        repo, _, _ = self.repos[1]
        role = repo / "cora.artifact-roles.json"
        ontology = repo / "cora.ontology.json"
        role.write_text("{not-valid-json")
        git(repo, "add", "cora.artifact-roles.json")
        git(repo, "commit", "-qm", "committed malformed CORA role manifest")
        self.repos[1] = (repo, git(repo,"rev-parse","HEAD"), "src/app.py")
        invalid = self.run_it(1)
        self.assertEqual(invalid["source_status"], "DEBT_BLOCKED")
        bad = {x["method"]:x["status"] for x in invalid["source_process"]["results"]}
        self.assertEqual(bad["artifact_roles"], "DEBT_BLOCKED")
        self.assertEqual(bad["python_candidate_graph"], "NOT_CONFIGURED")
        self.assertEqual(invalid["source_process"]["unconfigured_manifests"],
                         {"python_candidate_graph": "cora.ontology.json"})
        self.assertTrue(verify_portable(repo, invalid, self.profile))
        role.write_text(json.dumps({"schema":"cora-artifact-roles/1", "rules":[{
            "pattern":"src/*.py", "roles":["SOFTWARE_SOURCE"],
            "rationale":"Target-owned declared code, not runtime proof."}]}))
        ontology.write_text(json.dumps({"schema":"cora-ontology/1", "products":[{
            "id":"target", "roots":["src"], "entrypoints":["src/app.py"]}],
            "software":[{"id":"target-module", "roots":["src"],
                         "product_ids":["target"]}]}))
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "valid target-owned declarations")
        self.repos[1] = (repo,git(repo,"rev-parse","HEAD"),"src/app.py")
        good = self.run_it(1)
        self.assertEqual(good["source_status"], "PASS_SCOPED_GIT_SOURCE_ONLY")
        self.assertEqual(good["source_process"]["unconfigured_manifests"], {})
        self.assertTrue(verify_portable(repo, good, self.profile))
        self.assertEqual(good["governed_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(good["source_process"]["authorized_action"], "NONE")

    def test_p1_receipt_promotion_and_manifest_identity_adversaries(self):
        result = self.run_it(0)
        for path, value in (("source_status", "PASS_SCOPED_GIT_SOURCE_ONLY"),
                            ("governed_status", "PASS"),
                            ("authorization", "ALLOW")):
            forged = copy.deepcopy(result)
            forged[path] = value
            with self.subTest(field=path), self.assertRaisesRegex(ValueError,"replay mismatch"):
                verify_portable(self.repos[0][0], forged, self.profile)
        forged = copy.deepcopy(result)
        forged["source_process"]["results"] = [row for row in forged["source_process"]["results"]
                                                 if row["method"] != "artifact_roles"]
        with self.assertRaisesRegex(ValueError,"replay mismatch"):
            verify_portable(self.repos[0][0], forged, self.profile)
        # A profile is required by the original portable interface; it is not a
        # synthetic substitute for independent host or a root ontology file.
        with self.assertRaises((TypeError,AttributeError)):
            run_portable(self.repos[0][0], "HEAD", None)

    def test_reticular_all_levels_and_no_false_source_global(self):
        r = evaluate(ROOT)
        self.assertEqual((r["obligations"], r["local"], r["intermediate"], r["global"]),
                         (25, 18, 5, 2))
        self.assertEqual(r["product_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(r["authority"], "NONE")


class TestPortableNonRootManifests(unittest.TestCase):
    def test_source_roles_and_graph_are_executed_not_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=root/'target';target.mkdir()
            (target/'contracts').mkdir();(target/'host').mkdir()
            (target/'host'/'edu.mjs').write_text('export const start=()=>1;\n')
            (target/'contracts'/'roles.json').write_text(json.dumps({
                'schema':'cora-artifact-roles/1','rules':[{
                'pattern':'host/*','roles':['SOFTWARE_SOURCE'],
                'rationale':'Git-versioned execution ownership declaration'}]}))
            (target/'contracts'/'ontology.json').write_text(json.dumps({
                'schema':'cora-ontology/1',
                'products':[{'id':'project_edu','roots':['host'],
                             'entrypoints':['host/edu.mjs']}],
                'software':[{'id':'edu','roots':['host'],
                            'product_ids':['project_edu']}]}))
            git(target,'init','-q');git(target,'config','user.name','Audit')
            git(target,'config','user.email','audit@example.invalid')
            git(target,'add','.');git(target,'commit','-qm','source objects')
            rev=git(target,'rev-parse','HEAD')
            profile=root/'profile.json'
            base={'schema':'cora-portable-target/3','target_repo':'example/edu',
                  'revision':rev,'owners':[{'id':'edu-owner','path':'host/edu.mjs'}],
                  'witnesses':[],'method_links':[],
                  'source_manifests':{'artifact_roles':'contracts/roles.json',
                                      'ontology':'contracts/ontology.json'}}
            profile.write_text(json.dumps(base))
            receipt=run_portable(target,rev,profile)
            methods={x['method']:x for x in receipt['source_process']['results']}
            self.assertEqual(receipt['source_process']['status'],'PASS_SCOPED_WITH_UNVERIFIED_GAPS')
            self.assertEqual(receipt['source_status'],'PASS_SCOPED_GIT_SOURCE_ONLY')
            for m in ('artifact_roles','python_candidate_graph'):
                self.assertEqual(methods[m]['status'],'REUSED_SCOPED_FROM_HOLISTIC')
                self.assertTrue(methods[m]['source_digest'])
            self.assertTrue(verify_portable(target,receipt,profile))
            self.assertEqual(receipt['authorization'],'NONE')
            self.assertEqual(receipt['behavior_status'],'BLOCKED_EXTERNAL')
            broken=json.loads(json.dumps(base));broken['source_manifests']['ontology']='contracts/missing.json'
            profile.write_text(json.dumps(broken))
            missing=run_portable(target,rev,profile)
            self.assertEqual(missing['source_process']['status'],'SOURCE_PARTIAL_NOT_CONFIGURED')
            self.assertEqual(next(x['status'] for x in missing['source_process']['results']
                                 if x['method']=='python_candidate_graph'),'NOT_CONFIGURED')
            with self.assertRaises(ValueError):verify_portable(target,receipt,profile)
            broken['source_manifests']['ontology']='../escape.json'
            profile.write_text(json.dumps(broken))
            with self.assertRaises(ValueError):run_portable(target,rev,profile)
            profile.write_text(json.dumps(base))
            (target/'contracts'/'roles.json').write_text('{"tampered":true}')
            self.assertTrue(verify_portable(target,receipt,profile))  # Git, not worktree
            old=dict(base,schema='cora-portable-target/1')
            old.pop('source_manifests');profile.write_text(json.dumps(old))
            legacy=run_portable(target,rev,profile)
            self.assertEqual(legacy['source_process']['status'],'SOURCE_PARTIAL_NOT_CONFIGURED')



if __name__ == "__main__":
    unittest.main()
