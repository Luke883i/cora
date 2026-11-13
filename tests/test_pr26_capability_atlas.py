"""Physical Git and reticular falsifiers for the complete CORA capability source atlas."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capability_verifier", ROOT/"tools/verify_capability_atlas.py")
CAP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CAP)


def g(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode("utf-8").strip()


def fork(root):
    source = root/"repo"
    # Preserve original Git objects without hardlink-based local clone races.
    # Do not retry: retain a bounded diagnostic on any failure.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_CONFIG_") and key not in (
               "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
               "GIT_INDEX_FILE")}
    try:
        observed = subprocess.run(
            ["git", "-C", str(ROOT), "clone", "--no-local", "-q",
             "--", str(ROOT), str(source)],
            capture_output=True, text=True, check=False, timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("PR26 physical Git fixture transport failed: "
                           + type(exc).__name__) from exc
    if observed.returncode:
        raise RuntimeError("PR26 physical Git fixture clone failed "
                           f"(exit {observed.returncode}): "
                           + (observed.stderr or "NO_GIT_DIAGNOSTIC")[:1000])
    if not (source / ".git").exists():
        raise RuntimeError("PR26 clone returned success without original Git")
    g(source, "checkout", "-q", g(ROOT, "rev-parse", "HEAD"))
    g(source, "config", "user.name", "source proof fixture")
    g(source, "config", "user.email", "source@example.invalid")
    return source


def commit_json(repo, name, mutate):
    path = repo/name
    doc = json.loads(path.read_text("utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")
    g(repo, "add", name)
    g(repo, "commit", "-qm", "physically committed adversarial change")
    return g(repo, "rev-parse", "HEAD")


class CapabilityAtlasTests(unittest.TestCase):
    def test_01_source_census_and_exact_replay(self):
        r = CAP.check(ROOT)
        self.assertEqual(r["command_count"], 71)
        self.assertEqual(r["family_count"], 8)
        self.assertGreaterEqual(r["surfaces"]["modules"], 48)
        # Preserve the 15 original PR38 tools; future canonical tool growth
        # must reconcile with exact Git instead of a stale fixed-count oracle.
        sha = g(ROOT, "rev-parse", "HEAD")
        base = "324bc2d44d291f2256f354d2f2837e2ff2e62b52"
        tools_now = {p for p in g(ROOT, "ls-tree", "-r", "--name-only",
                                  sha, "--", "tools").splitlines()
                     if p.startswith("tools/") and p.count("/") == 1 and p.endswith(".py")}
        tools_base = {p for p in g(ROOT, "ls-tree", "-r", "--name-only",
                                   base, "--", "tools").splitlines()
                      if p.startswith("tools/") and p.count("/") == 1 and p.endswith(".py")}
        self.assertEqual(len(tools_base), 15)
        self.assertTrue(tools_base.issubset(tools_now))
        self.assertEqual(r["surfaces"]["operational_tools"], len(tools_now))
        # The PR26 baseline had twelve workflows; later valid additions remain
        # mandatory inventory, not regressions or silently ignored consumers.
        sha = g(ROOT, "rev-parse", "HEAD")
        current = [p for p in g(ROOT, "ls-tree", "-r", "--name-only", sha,
                               "--", ".github/workflows").splitlines()
                   if p.endswith((".yml", ".yaml"))]
        baseline = [p for p in g(ROOT, "ls-tree", "-r", "--name-only",
                                "cfca7f5e6ab777d4aacf2c0989812925eb31b459",
                                "--", ".github/workflows").splitlines()
                    if p.endswith((".yml", ".yaml"))]
        self.assertEqual(len(baseline), 12)
        self.assertTrue(set(baseline).issubset(set(current)))
        self.assertEqual(r["surfaces"]["github_workflows"], len(current))
        self.assertEqual(r["surfaces"]["contracts"], 2)
        self.assertGreaterEqual(r["surfaces"]["internal_dod"], 9)
        self.assertEqual(r["surfaces"]["internal_profiles"], 2)
        self.assertEqual(r["surfaces"]["assurance_records"], 2)
        self.assertEqual(r["surfaces"]["markdown"], 48)
        self.assertGreaterEqual(r["surfaces"]["test_modules"], 36)
        self.assertEqual(r["authorization"], "NONE")
        self.assertEqual(r["governed_status"], "BLOCKED_EXTERNAL")
        self.assertEqual(r["ci_final_head"], "NOT_ATTESTED_BY_SOURCE")
        self.assertTrue(all(x["test_execution"]=="NOT_ATTESTED_BY_SOURCE" for x in r["commands"]))
        self.assertTrue(CAP.replay(ROOT, r))

    def test_02_forged_receipt_fails_and_dirty_tree_not_authoritative(self):
        original = CAP.check(ROOT)
        forged = copy.deepcopy(original)
        forged["commands"][0]["test_execution"] = "PASS"
        with self.assertRaises(ValueError):
            CAP.replay(ROOT, forged)
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            witnessed=CAP.check(local)
            (local/"README.md").write_text("fake source\n", encoding="utf-8")
            self.assertEqual(CAP.check(local), witnessed)
            self.assertTrue(CAP.replay(local,witnessed))

    def test_03_physical_target_effect_reclassification(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                row=next(x for x in doc["commands"] if x["command"]=="apply-rename-doc")
                row["interaction"]="SOURCE_ANALYSIS_OR_PROPOSAL"
            sha=commit_json(local,".cora/assurance/capability-atlas.json",change)
            with self.assertRaisesRegex(ValueError,"effectful command"):
                CAP.check(local,sha)

    def test_04_physical_disconnect_cli_from_source_and_test(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                row=next(x for x in doc["commands"] if x["command"]=="audit")
                row["method_source"]="src/cora/debt.py"
            sha=commit_json(local,".cora/assurance/capability-atlas.json",change)
            with self.assertRaisesRegex(ValueError,"implementation detached"):
                CAP.check(local,sha)
            def change2(doc):
                row=next(x for x in doc["commands"] if x["command"]=="audit")
                row["method_source"]="src/cora/audit.py"
                row["test_source"]="tests/nonexistent.py"
            sha=commit_json(local,".cora/assurance/capability-atlas.json",change2)
            with self.assertRaises(ValueError):
                CAP.check(local,sha)

    def test_05_physical_dod_edge_and_chronology_mutants(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            def change(doc):
                next(x for x in doc["nodes"] if x["id"]=="G_CAP_SOURCE")["depends_on"].pop()
            sha=commit_json(local,".cora/contracts/dod/capability-dod.json",change)
            with self.assertRaisesRegex(ValueError,"DoD edge"):
                CAP.check(local,sha)
            # Restore the failed reticular mutation before the independent
            # documentation falsifier; otherwise a stale DoD could mask it.
            contract=local/".cora/contracts/dod/capability-dod.json"
            contract.write_bytes((ROOT/".cora/contracts/dod/capability-dod.json").read_bytes())
            g(local,"add",".cora/contracts/dod/capability-dod.json")
            g(local,"commit","-qm","restore DoD before chronology test")
            self.assertEqual(CAP.check(local)["source_status"],"PASS_SCOPED_SOURCE")
            path=local/"docs/ARCHITECTURE.md"
            text=path.read_text("utf-8").replace("## Current documentation ownership","## Unverified product ownership")
            path.write_text(text,encoding="utf-8")
            g(local,"add","docs/ARCHITECTURE.md")
            g(local,"commit","-qm","historical claim promoted to current")
            with self.assertRaisesRegex(ValueError,"current documentation ownership"):
                CAP.check(local)

    def test_06_physical_removed_workflow_and_reader_claim(self):
        with tempfile.TemporaryDirectory() as t:
            local=fork(Path(t))
            (local/".github/workflows/ci-selection.yml").unlink()
            g(local,"add","-A")
            g(local,"commit","-qm","unexpected workflow retirement")
            with self.assertRaisesRegex(ValueError,"repository inventory drift"):
                CAP.check(local)
            # No implied permission to retire it from mere source absence.
            self.assertEqual(CAP.check(ROOT)["authorization"],"NONE")

    def test_07_thousand_finite_noncompensatory_mutants(self):
        original=json.loads((ROOT/".cora/contracts/dod/capability-dod.json").read_text("utf-8"))
        seen=set()
        for family in range(10):
            for i in range(100):
                mutated=copy.deepcopy(original)
                mutated["nodes"][0]["description"] += " variant %03d" % i
                if family==0: mutated["authority"]="APPROVED"
                elif family==1: mutated["external_status"]="PASS"
                elif family==2: mutated["ci_status"]="PASSED_IN_SOURCE"
                elif family==3: next(x for x in mutated["nodes"] if x["id"]=="G_CAP_SOURCE")["depends_on"].pop()
                elif family==4: next(x for x in mutated["nodes"] if x["id"]=="G_CAP_ACCEPTED")["depends_on"].pop()
                elif family==5: next(x for x in mutated["nodes"] if x["id"]=="I_IDENTITY")["depends_on"].pop()
                elif family==6: next(x for x in mutated["nodes"] if x["id"]=="E01")["scope"]="SOURCE"
                elif family==7: next(x for x in mutated["nodes"] if x["id"]=="E02")["scope"]="SOURCE"
                elif family==8: mutated["nodes"][0]["id"]="C02"
                else: mutated["nodes"][0]["depends_on"]=["MISSING"]
                string=json.dumps(mutated,sort_keys=True)
                self.assertNotIn(string,seen)
                seen.add(string)
                with self.assertRaises(ValueError):
                    CAP.verify_dod(mutated)
        self.assertEqual(len(seen),1000)


    def test_08_complete_committed_static_surface_and_strict_json(self):
        """Full tracked Git-source census; does not imply all runtime paths run."""
        import hashlib
        from cora.chat_bundle import _strict_json
        from cora.git_snapshot import snapshot
        head = g(ROOT, "rev-parse", "HEAD")
        ledger = snapshot(ROOT, head)
        paths = [p.decode("utf-8") for p in subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files", "-z"]).split(b"\0") if p]
        self.assertEqual([row["path"] for row in ledger["records"]],
                         sorted(paths))
        counts = {"python": 0, "json": 0, "markdown": 0,
                  "workflows": 0, "javascript": 0}
        for row in ledger["records"]:
            if row["status"] != "observed_git_blob":
                self.assertIn(row["status"], (
                    "symlink_unresolved", "gitlink_unresolved",
                    "blob_too_large", "lfs_pointer_unresolved"))
                continue
            source = (ROOT / row["path"]).read_bytes()
            self.assertEqual(row["sha256"], hashlib.sha256(source).hexdigest(),
                             row["path"])
            self.assertEqual(row["size"], len(source), row["path"])
            if row["path"].endswith(".py"):
                compile(source, row["path"], "exec")
                counts["python"] += 1
            elif row["path"].endswith(".json"):
                _strict_json(source)
                counts["json"] += 1
            elif row["path"].endswith(".md"):
                counts["markdown"] += 1
            elif row["path"].startswith(".github/workflows/") and row["path"].endswith(".yml"):
                counts["workflows"] += 1
            elif row["path"].endswith(".mjs"):
                counts["javascript"] += 1
        # Inventory grows and contracts with the exact checked-out Git tree.
        # Fixed-era counts are diagnostics, not a ban on future safe changes.
        expected = {
            "python": sum(p.endswith(".py") for p in paths),
            "json": sum(p.endswith(".json") for p in paths),
            "markdown": sum(p.endswith(".md") for p in paths),
            "workflows": sum(p.startswith(".github/workflows/") and
                             p.endswith(".yml") for p in paths),
            "javascript": sum(p.endswith(".mjs") for p in paths),
        }
        self.assertEqual(counts, expected)
        self.assertEqual(len(ledger["records"]), len(paths))
        self.assertEqual(counts["markdown"], 48)  # existing registry contract
        self.assertEqual(_strict_json(b'{"unique":true}'), {"unique": True})
        with self.assertRaisesRegex(ValueError, "duplicate JSON field"):
            _strict_json(b'{"authority":"NONE","authority":"APPROVED"}')
        with self.assertRaises(ValueError):
            compile(b"def wrong(: pass", "mutated.py", "exec")

    def test_09_all_declared_commands_execute_help_as_installed_cli(self):
        """Actual subprocess parser smoke, NOT 71 target behaviors or executions."""
        import sys
        src = (ROOT / "src/cora/cli.py").read_text("utf-8")
        names, _, _ = CAP.parser_wiring(src)
        declared = [r["command"] for r in
                    json.loads((ROOT / ".cora/assurance/capability-atlas.json").read_text("utf-8"))["commands"]]
        self.assertEqual(set(names), set(declared))
        self.assertEqual(len(declared), len(set(declared)))
        self.assertEqual(len(declared), 71)
        for cmd in sorted(declared):
            with self.subTest(command=cmd):
                proc = subprocess.run(
                    [sys.executable, "-m", "cora.cli", cmd, "--help"],
                    input=b"", capture_output=True, timeout=15, check=False)
                self.assertEqual(proc.returncode, 0,
                                 (cmd + ": " + proc.stderr.decode("utf-8", "replace")[-500:]))
                self.assertIn(b"usage:", proc.stdout.lower())
        invalid = subprocess.run(
            [sys.executable, "-m", "cora.cli", "cora-unknown-command", "--help"],
            input=b"", capture_output=True, timeout=15, check=False)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn(b"invalid choice", invalid.stderr.lower())

    def test_10_real_git_cli_snapshot_replay_and_forgery_rejection(self):
        """Installed CLI + original disposable Git; no host or target oracle."""
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target"
            target.mkdir()
            g(target, "init", "-q")
            g(target, "config", "user.name", "CORA smoke")
            g(target, "config", "user.email", "fixture@example.invalid")
            (target / "payload.txt").write_text("original\n", "utf-8")
            g(target, "add", "payload.txt")
            g(target, "commit", "-qm", "original fixture")
            sha = g(target, "rev-parse", "HEAD")
            ledger_path = base / "ledger.json"
            run_path = base / "process.json"

            def cli(*argv):
                return subprocess.run(
                    [sys.executable, "-m", "cora.cli", *map(str, argv)],
                    capture_output=True, timeout=45, check=False)

            observed = cli("snapshot", target, "--revision", sha,
                           "--output", ledger_path)
            self.assertEqual(observed.returncode, 0, observed.stderr[-700:])
            ledger = json.loads(ledger_path.read_text("utf-8"))
            self.assertEqual(ledger["commit"], sha)
            self.assertEqual(ledger["coverage"]["runtime"], "unsupported")
            self.assertEqual(len(ledger["records"]), 1)
            verified = cli("verify-ledger", ledger_path, "--repo", target)
            self.assertEqual(verified.returncode, 0, verified.stderr[-700:])
            self.assertEqual(json.loads(verified.stdout)["status"],
                             "verified_against_git_objects")

            # A dirty target worktree does not rewrite the original commit.
            (target / "payload.txt").write_text("uncommitted change\n", "utf-8")
            self.assertEqual(cli("verify-ledger", ledger_path, "--repo", target).returncode, 0)
            forged = copy.deepcopy(ledger)
            forged["coverage"]["runtime"] = "certified"
            ledger_path.write_text(json.dumps(forged), "utf-8")
            rejected = cli("verify-ledger", ledger_path, "--repo", target)
            self.assertEqual(rejected.returncode, 3, rejected.stderr[-700:])
            self.assertIn(b"CORA error:", rejected.stderr)

            produced = cli("process-run", target, "--revision", sha,
                           "--process", "history", "--output", run_path)
            self.assertEqual(produced.returncode, 0, produced.stderr[-700:])
            process = json.loads(run_path.read_text("utf-8"))
            self.assertEqual(process["commit"], sha)
            self.assertEqual(process["authorized_action"], "NONE")
            replayed = cli("verify-process", run_path, "--repo", target)
            self.assertEqual(replayed.returncode, 0, replayed.stderr[-700:])
            process["results"][0]["status"] = "INDEPENDENTLY_CERTIFIED"
            run_path.write_text(json.dumps(process), "utf-8")
            rejected = cli("verify-process", run_path, "--repo", target)
            self.assertEqual(rejected.returncode, 3, rejected.stderr[-700:])


    def test_11_installed_optional_js_parser_is_syntactically_valid(self):
        """Cross-language syntax only. Node execution/runtime still separate."""
        import shutil
        node = shutil.which("node")
        if not node:
            self.skipTest("NODE_NOT_INSTALLED: JS parser execution NOT_RUN")
        parser = ROOT / "src/cora/portable_js_imports.mjs"
        proc = subprocess.run([node, "--check", str(parser)],
                              capture_output=True, timeout=20, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        with tempfile.TemporaryDirectory() as td:
            broken = Path(td) / "broken.mjs"
            broken.write_text("export const = unexpected;\n", encoding="utf-8")
            negative = subprocess.run([node, "--check", str(broken)],
                                      capture_output=True, timeout=20, check=False)
            self.assertNotEqual(negative.returncode, 0)

    def test_12_twenty_bounded_standard_frontier_lenses_have_single_owner(self):
        """Lenses name source owners; they do not claim native runtime coverage."""
        import re
        path = ROOT / "docs/CONTINUOUS_DEVELOPMENT.md"
        doc = path.read_text("utf-8")
        marker = "## Full-surface assessment lenses"
        self.assertEqual(doc.count(marker), 1)
        block = doc.split(marker, 1)[1].split(
            "\n## Trust boundary and known debt", 1)[0]
        names = re.findall(r"(?m)^\| ([SF][0-9]{2}) \|", block)
        self.assertEqual(names, (["S%02d" % k for k in range(1, 11)] +
                                 ["F%02d" % k for k in range(1, 11)]))
        self.assertIn("not twenty implemented engines", block)
        self.assertIn("71/71 CLI bootstrap checks", block)
        self.assertIn("AND obligations", block)
        # A superficially plausible duplicate lens must fail the same contract.
        self.assertNotEqual(
            re.findall(r"(?m)^\| ([SF][0-9]{2}) \|",
                       block.replace("| F10 ", "| F09 ", 1)), names)


if __name__=="__main__":
    unittest.main()
