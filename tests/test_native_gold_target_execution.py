"""PR52 real native Node test subprocess, exact-Git source and anti-promotion."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from importlib.resources import files as package_files
from pathlib import Path

from cora.native_gold import capture_native, replay_native, _ictc_native
from cora.portable_assurance import run_portable, verify_portable, render_portable_html


def git(repo: Path, *args) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class PR52NativeGold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cora-pr52-native-")
        self.root = Path(self.tmp.name)
        self.repo = self.root / "product"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Native test")
        git(self.repo, "config", "user.email", "native@example.invalid")
        path = self.repo / "tests" / "cora-adoption.test.mjs"
        path.parent.mkdir()
        path.write_text(
            "import test from 'node:test';\n"
            "import assert from 'node:assert/strict';\n"
            "test('physical node subprocess actually ran',()=>assert.equal(2+2,4));\n",
            encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "tracked real native oracle")
        self.head = git(self.repo, "rev-parse", "HEAD")
        self.out = self.root / "native-witness"

    def tearDown(self):
        self.tmp.cleanup()

    def profile(self):
        oracle = "tests/cora-adoption.test.mjs"
        raw = subprocess.check_output([
            "git", "-C", str(self.repo), "show", self.head + ":" + oracle])
        h = hashlib.sha256(raw).hexdigest()
        def claim(key, scope, deps):
            return {"id": key, "claim": "Original native Node test execution and replay linkage",
                    "scope": scope, "owner_id": "native-owner",
                    "source_path": oracle, "oracle_id": "node-oracle",
                    "oracle_path": oracle, "oracle_sha256": h,
                    "witness_ids": [], "depends_on": deps}
        return {
            "schema": "cora-portable-target/2", "target_repo": "Luke883i/teddy",
            "revision": self.head,
            "owners": [{"id": "native-owner", "path": oracle}],
            "witnesses": [], "method_links": [],
            "claims": [claim("C_RUNTIME", "BEHAVIOR", []),
                       claim("C_EXTERNAL", "EXTERNAL", ["C_RUNTIME"])],
            "goal": "C_EXTERNAL"
        }

    def test_actual_node_subprocess_captured_and_gold_one_run_replayed(self):
        generated = capture_native(self.repo, "Luke883i/teddy", self.head,
                                   "C_RUNTIME", self.out)
        self.assertEqual(generated["exit_code"], 0)
        observed = replay_native(self.repo, self.out)
        self.assertEqual(observed["report_status"],
                         "LOCAL_RUNNER_PASS_REPORTED_UNAUTHENTICATED")
        self.assertFalse(observed["issuer_authenticated"])
        profile = self.root / "profile.json"
        profile.write_text(json.dumps(self.profile()))
        report = run_portable(self.repo, "HEAD", profile, native_probe=self.out)
        self.assertEqual(report["native_gold"], observed)
        self.assertEqual(report["gold"]["goal_status"],
                         "BLOCKED_INDEPENDENT_ORACLE_EXECUTION_AND_REVIEW")
        self.assertEqual(report["gold"]["claims"][0]["local_runner"], observed)
        self.assertEqual(report["gold"]["claims"][0]["claim_proven"], False)
        self.assertEqual(report["gold"]["native_local_runner_probes"], 1)
        self.assertEqual(report["authorization"], "NONE")
        self.assertIn("Host identity UNATTESTED", render_portable_html(report))
        self.assertTrue(verify_portable(self.repo, report, profile,
                                        native_probe=self.out))
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(self.repo, report, profile)
        forged = copy.deepcopy(report)
        forged["native_gold"]["issuer_authenticated"] = True
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            verify_portable(self.repo, forged, profile, native_probe=self.out)

    def test_native_producer_and_receipt_mutations(self):
        with self.assertRaisesRegex(ValueError, "allowlisted"):
            capture_native(self.repo, "Luke883i/fiction", self.head,
                           "C_RUNTIME", self.out)
        with self.assertRaisesRegex(ValueError, "HEAD changed"):
            capture_native(self.repo, "Luke883i/teddy", "f"*40,
                           "C_RUNTIME", self.out)
        capture_native(self.repo, "Luke883i/teddy", self.head, "C_RUNTIME", self.out)
        original = (self.out / "receipt.json").read_bytes()
        log = (self.out / "run.log").read_bytes()
        for field, value in (
            ("release_authorization", "AUTHORIZED"),
            ("exit_code", 13),
            ("source_commit", "e"*40),
            ("oracle_sha256", "0"*64),
            ("claim_id", "C_FAKE"),
            ("target_repo", "Luke883i/ictc"),
            ("artifact_file", "artifact.json"),
            ("issuer_authentication", "INDEPENDENT"),
        ):
            with self.subTest(field=field):
                mutant = json.loads(original)
                mutant[field] = value
                (self.out / "receipt.json").write_text(json.dumps(mutant))
                with self.assertRaises(ValueError):
                    replay_native(self.repo, self.out)
        (self.out / "receipt.json").write_bytes(original)
        (self.out / "run.log").write_bytes(log + b"\nPASS INJECTED\n")
        with self.assertRaisesRegex(ValueError, "log tampered"):
            replay_native(self.repo, self.out)
        (self.out / "run.log").write_bytes(log)
        self.assertEqual(replay_native(self.repo, self.out)["authorization"], "NONE")

    def test_genuine_native_test_failure_is_not_promoted(self):
        path = self.repo / "tests" / "cora-adoption.test.mjs"
        path.write_text(
            "import test from 'node:test';\n"
            "import assert from 'node:assert/strict';\n"
            "test('RED physical oracle',()=>assert.fail('native rejection'));\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "physical failed test mutation")
        self.head = git(self.repo, "rev-parse", "HEAD")
        result = capture_native(self.repo, "Luke883i/teddy", self.head,
                                "C_RUNTIME", self.out)
        self.assertNotEqual(result["exit_code"], 0)
        observed = replay_native(self.repo, self.out)
        self.assertEqual(observed["report_status"], "LOCAL_RUNNER_FAIL_REPORTED")
        profile = self.root / "red.json"
        profile.write_text(json.dumps(self.profile()))
        r = run_portable(self.repo, "HEAD", profile, native_probe=self.out)
        self.assertEqual(r["native_gold"]["report_status"],
                         "LOCAL_RUNNER_FAIL_REPORTED")
        self.assertEqual(r["governed_status"], "BLOCKED_EXTERNAL")

    def test_ictc_12_write_7_denial_semantic_oracle_fails_closed(self):
        payload = {
            "schema": "ictc-e2e-7process-real-write/v2",
            "gitHead": self.head, "runtimeCommands": 12,
            "commandReceipts": [{"receiptHash": "a"*64} for _ in range(12)],
            "negative": {
                "results": [{"status": 403} for _ in range(7)],
                "revisionBeforeDenials": 34, "revisionAfterDenials": 34
            },
            "asserts": {
                "sevenProcesses": True, "integrityBinding": True,
                "semanticEventBindings": True, "privateActorIsolation": True,
                "deniedAuditorWrite": True, "deniedAuditorRoutes": 7
            }
        }
        self.assertTrue(_ictc_native(payload, self.head))
        for label, change in (
            ("wrong-head", lambda p:p.update(gitHead="f"*40)),
            ("missing-write", lambda p:p.update(runtimeCommands=11)),
            ("missing-receipt", lambda p:p["commandReceipts"].pop()),
            ("forged-receipt", lambda p:p["commandReceipts"][0].update(receiptHash="x")),
            ("denial-bypass", lambda p:p["negative"]["results"][0].update(status=200)),
            ("revision-changed", lambda p:p["negative"].update(revisionAfterDenials=35)),
            ("no-actor-isolation", lambda p:p["asserts"].update(privateActorIsolation=False))
        ):
            with self.subTest(mutant=label):
                altered = copy.deepcopy(payload)
                change(altered)
                self.assertFalse(_ictc_native(altered, self.head))

    def test_js_exact_relative_graph_missing_and_unknown(self):
        sub = self.repo / "web"
        sub.mkdir()
        (sub / "main.mjs").write_text(
            "import './present.mjs';\n"
            "import './missing.mjs';\n"
            "import './ambiguous';\n"
            "import 'external-package';\n"
            "const late=()=>import('./dynamic.mjs');\n"
            "throw Error('never run imports');\n")
        (sub / "present.mjs").write_text("export const yes=1;\n")
        (sub / "unknown.ts").write_text("export const notParsed: boolean=true;\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "physical ESM import graph")
        parser = package_files("cora").joinpath("portable_js_imports.mjs")
        import subprocess as sp
        proc = sp.run(["node", "--no-warnings", "--experimental-vm-modules",
                       str(parser), str(self.repo), "HEAD"],
                      capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        statuses = {x["specifier"]: x["status"] for x in result["candidateEdges"]}
        self.assertEqual(statuses["./present.mjs"], "RESOLVED_EXACT_COMMITTED_GIT_PATH")
        self.assertEqual(statuses["./missing.mjs"], "MISSING_EXACT_COMMITTED_GIT_PATH")
        self.assertEqual(statuses["./ambiguous"],
                         "UNKNOWN_EXTENSION_OR_DIRECTORY_RESOLUTION")
        self.assertEqual(statuses["external-package"],
                         "BARE_OR_PACKAGE_OR_BUILTIN_IMPORT_UNKNOWN")
        self.assertGreater(result["missingExactRelative"], 0)
        self.assertGreater(result["unknownImportResolutions"], 0)
        self.assertGreater(result["unparsedSourceExtensions"], 0)
        self.assertEqual(result["safeDeletion"], "NOT_PROVEN")
        self.assertFalse(result["runtimeObserved"])


if __name__ == "__main__":
    unittest.main()
