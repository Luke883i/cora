"""PR62 noncompensatory enterprise-evaluable documentation review.

A million unique 20-bit *contract vectors* are not a million source mutations.
Real Markdown corruptions are separate, and no case is a human acceptance test.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cora_enterprise_doc_verifier", ROOT / "tools/verify_documentation.py")
DOC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOC)


class EnterpriseDocumentDoDTests(unittest.TestCase):
    def test_exhaustive_current_git_markdown_reticulum(self):
        actual = DOC.census_markdown(ROOT)
        self.assertEqual(actual["status"], "PASS_SCOPED", actual["errors"])
        self.assertEqual(actual["source_commit"], DOC.census_markdown(ROOT)["source_commit"])
        self.assertEqual(actual["counts"]["markdown"], 48)
        self.assertEqual(actual["counts"]["active"], 31)
        self.assertEqual(actual["counts"]["historical"], 17)
        self.assertEqual(actual["counts"]["original_git_parity"], 48)
        self.assertEqual(actual["counts"]["broken_local_links"], 0)
        self.assertEqual(actual["counts"]["missing_current_contracts"], 0)
        self.assertEqual(actual["counts"]["active_index_only"], sum(
            r["evaluation_route"] == "INDEX_ONLY_REVIEW" for r in actual["documents"]))
        self.assertEqual(actual["counts"]["active_history_mentions"], sum(
            r["pr_history_mentions"] for r in actual["documents"] if r["status"] != "HISTORICAL"))
        self.assertTrue(all(r["evaluation_route"] == "ARCHIVAL_NON_NORMATIVE"
                            for r in actual["documents"] if r["status"] == "HISTORICAL"))
        self.assertTrue(all(r["evaluation_route"] in ("ACTIVE_REFERENCED", "INDEX_ONLY_REVIEW")
                            for r in actual["documents"] if r["status"] != "HISTORICAL"))
        self.assertEqual(actual["external_links"], "NOT_PROBED")
        self.assertEqual(actual["external_acceptance"], "BLOCKED_EXTERNAL")
        self.assertEqual(actual["authority"], "NONE")

    def test_live_to_historical_links_require_local_nonoperative_context(self):
        """A discoverable archive cannot silently become today's procedure."""
        import json
        registry = json.loads((ROOT / "docs/documentation-registry.json").read_text("utf-8"))
        statuses = {d["path"]: d["status"] for d in registry["documents"]}
        checker = DOC.historical_authority_issues
        for path in ("docs/ARCHITECTURE.md", "docs/FILE_LAB.md",
                     "docs/AI_CODE_ASSURANCE.md", "CONTRIBUTING.md"):
            text = (ROOT / path).read_text("utf-8")
            self.assertEqual(checker(path, text, statuses), [], path)

        bad_routes = (
            ("docs/FILE_LAB.md",
             "See [standards audit](STANDARDS_MAINTENANCE_AUDIT.md)."),
            ("docs/ARCHITECTURE.md",
             "Use the [current DoD](DOD.md) for approval."),
            ("docs/AI_CODE_ASSURANCE.md",
             "Current required [agent audit](archive/audits/AUDIT_PR18_MAIN.md)."),
            ("docs/AI_CODE_ASSURANCE.md",
             "Required [agent audit](archive/audits/AUDIT_PR18_MAIN.md) now."),
        )
        for path, bad in bad_routes:
            with self.subTest(path=path):
                self.assertTrue(any(x.startswith("historical-authority-ambiguous:")
                                    for x in checker(path, bad, statuses)))
        self.assertEqual(checker(
            "docs/FILE_LAB.md",
            "For provenance only, see the [historical standards audit]"
            "(STANDARDS_MAINTENANCE_AUDIT.md).", statuses), [])
        self.assertEqual(checker(
            "docs/FILE_LAB.md",
            "```md\n[current](STANDARDS_MAINTENANCE_AUDIT.md)\n```", statuses), [])
        self.assertEqual(checker(
            "docs/INDEX.md",
            "- [OLD DOD](DOD.md) — HISTORICAL · DOD", statuses), [])

        report = DOC.census_markdown(ROOT)
        self.assertEqual(report["counts"]["active_method_to_current_dod_edges"],
                         sum(row["outbound_current_dod"]
                             for row in report["documents"]
                             if row["status"] in ("CURRENT", "SCOPED_CURRENT")
                             and row["kind"] == "METHOD"))
        self.assertEqual(report["counts"]["ambiguous_historical_authority"], 0,
                         report["errors"])
        self.assertEqual(report["counts"]["current_to_historical_edges"],
                         sum(r["outbound_historical"] for r in report["documents"]
                             if r["status"] in ("CURRENT", "SCOPED_CURRENT")))

    def test_local_fragment_links_are_not_invisible_to_the_graph(self):
        self.assertEqual(DOC.resolve("README.md", "#existing-heading"),
                         ("README.md", "existing-heading"))
        source = (ROOT / "README.md").read_text("utf-8")
        bad = DOC.census_markdown(ROOT, overrides={
            "README.md": source + "\n[broken local target](#unobserved-anchor)\n"
        })
        self.assertEqual(bad["status"], "REFUTED")
        self.assertTrue(any(e.startswith(
            "broken-anchor:README.md:README.md#unobserved-anchor")
            for e in bad["errors"]), bad["errors"])
        self.assertIn("worktree-git-parity:README.md", bad["errors"])
        self.assertEqual(DOC.census_markdown(ROOT)["counts"]["broken_local_links"], 0)

    def test_active_methods_have_direct_scoped_dod_routes(self):
        """Method -> DoD ownership is a link, not proof that a DoD passes."""
        import json
        registry = json.loads((ROOT / "docs/documentation-registry.json").read_text("utf-8"))
        statuses = {row["path"]: row["status"] for row in registry["documents"]}
        owners = {
            "docs/CONTINUOUS_DEVELOPMENT.md": "docs/DOD_CONTINUOUS.md",
            "docs/ENGINEERING_DEBT.md": "docs/DOD_ENGINEERING_DEBT.md",
            "docs/HOLISTIC_FORENSICS.md": "docs/DOD_HOLISTIC_FORENSICS.md",
            "docs/GOLD_ASSURANCE.md": "docs/DOD_PR19_GOLD.md",
            "docs/CONVERGENT_ASSURANCE.md": "docs/DOD_PR20_CONVERGENCE.md",
            "docs/ARTIFACT_SEMANTICS.md": "docs/DOD_V1_EXPERIMENTAL.md",
            "docs/RELEASE.md": "docs/DOD_RELEASE_READINESS.md",
        }
        def targets(path, body):
            return [DOC.resolve(path, link)
                    for link in DOC.markdown_links(body)]
        scoped_rows = {
            row["path"]: row for row in DOC.census_markdown(ROOT)["documents"]
        }
        for page, dod in owners.items():
            with self.subTest(page=page):
                self.assertEqual(statuses[page], "CURRENT")
                self.assertIn(statuses[dod], ("CURRENT", "SCOPED_CURRENT"))
                body = (ROOT / page).read_text("utf-8")
                self.assertIn("**Applicable current DoD:**", body)
                self.assertIn((dod, ""), targets(page, body))
                route = scoped_rows[page]
                self.assertGreaterEqual(route["outbound_current_dod"], 1)
                # A plausible local link to the INDEX does not discharge
                # a direct owner route; the negative source mutant must fail.
                relative = dod.rsplit("/", 1)[-1]
                mutant = body.replace("(" + relative + ")", "(INDEX.md)", 1)
                self.assertNotEqual(mutant, body)
                self.assertNotIn((dod, ""), targets(page, mutant))
                self.assertIn(("docs/INDEX.md", ""), targets(page, mutant))

    def test_readme_evaluation_budget_and_source_reality(self):
        readme = (ROOT / "README.md").read_text("utf-8")
        index = (ROOT / "docs/INDEX.md").read_text("utf-8")
        self.assertLessEqual(len(readme.split()), 1750)
        self.assertLess(len(readme.encode("utf-8")), 16000)
        self.assertFalse(re.search(r"(?im)^#{2,3}[^\n]*\bPR[- ]?\d+", readme))
        self.assertEqual(len(re.findall(r"\bPR[- #]?\d+\b", readme, re.I)), 0)
        self.assertEqual(DOC.verify_readme_semantics(readme, root=ROOT), [])
        self.assertEqual(DOC.verify_progressive_readme(readme), [])
        self.assertEqual(DOC.verify_project_first_readme(readme), [])
        self.assertIn("Implementation and historical detail", index)
        self.assertIn("compressed public front door", index)
        self.assertIn("SLSA provenance: NOT_ATTESTED", readme)
        self.assertIn("External acceptance remains `BLOCKED_EXTERNAL`", readme)
        self.assertIn("not one million independent source mutations", readme)

    def test_readme_badge_and_first_title_are_fail_closed(self):
        """Badge is allowed only with exact source, never generic title drift."""
        readme = (ROOT / "README.md").read_text("utf-8")
        badge = (
            "[![ROA Research Programme]"
            "(https://img.shields.io/badge/ROA-Research_Programme-1f6feb)]"
            "(https://github.com/Luke883i/academics)"
        )
        self.assertTrue(readme.startswith(badge))
        self.assertEqual(DOC.check_current_contract("README.md", readme), [])
        false_badge = readme.replace(badge, badge.replace("Programme", "Approval"), 1)
        self.assertIn("standalone-title:README.md",
                      DOC.check_current_contract("README.md", false_badge))
        false_title = readme.replace(
            "# CORA — Continuous Ontological Repository Assurance",
            "# Unattributed Corporate Software", 1)
        self.assertIn("standalone-title:README.md",
                      DOC.check_current_contract("README.md", false_title))

    def test_current_documents_disallow_pr_era_prose_but_keep_compat_refs(self):
        current = (ROOT / "docs/GETTING_STARTED.md").read_text("utf-8")
        check = DOC.check_current_contract
        self.assertEqual(check("docs/GETTING_STARTED.md", current), [])
        false = current + "\nPR999 is the current product contract.\n"
        self.assertIn("standalone-pr-narrative:docs/GETTING_STARTED.md",
                      check("docs/GETTING_STARTED.md", false))
        compatible = current + (
            '\n<a id="pr999-compatibility"></a>\n'
            '[Old source](archive/decisions/ADR-PR01.md)\n'
        )
        self.assertEqual(check("docs/GETTING_STARTED.md", compatible), [])
        history = (ROOT / "CHANGELOG.md").read_text("utf-8")
        self.assertEqual(check("CHANGELOG.md", history), [])

    def test_supply_chain_candidate_not_independent_attestation(self):
        ci = (ROOT / ".github/workflows/ci-release-candidate.yml").read_text("utf-8")
        release = (ROOT / "docs/RELEASE.md").read_text("utf-8")
        security = (ROOT / "SECURITY.md").read_text("utf-8")
        for marker in ("--sbom-output", "--verify-sbom", "--provenance-output",
                       "--verify-provenance", "--sca-raw", "--verify-sca",
                       "SHA256SUMS", "build-tool-pins.json"):
            self.assertIn(marker, ci)
        self.assertIn("Supply-chain and procurement evaluation", release)
        self.assertIn("The authoritative candidate identity is the exact Git HEAD", release)
        self.assertNotIn("The source baseline is merged PR60", release)
        self.assertIn("CycloneDX 1.6 SBOM", security)
        self.assertIn("NOT_ATTESTED", security)
        self.assertIn("BLOCKED_EXTERNAL", release)

    def test_physical_negative_and_positive_markdown_controls(self):
        readme = (ROOT / "README.md").read_text("utf-8")
        guide = (ROOT / "docs/GETTING_STARTED.md").read_text("utf-8")
        benign = guide.replace("**Operational use:**", "**Operational use:** ", 1)
        self.assertEqual(DOC.check_current_contract("docs/GETTING_STARTED.md", benign), [])
        self.assertTrue(DOC.check_current_contract(
            "docs/GETTING_STARTED.md",
            guide.replace("**Evidence:**", "**Approval:**", 1)))
        self.assertTrue(DOC.verify_readme_semantics(readme.replace(
            "**External acceptance remains `BLOCKED_EXTERNAL`**",
            "**External acceptance has been approved**", 1)))
        broken = DOC.census_markdown(ROOT, overrides={
            "README.md": readme + "\n[phantom](docs/never-existed-enterprise.md)\n"})
        self.assertEqual(broken["status"], "REFUTED")
        self.assertTrue(any(e.startswith("broken-link:README.md:") for e in broken["errors"]))
        self.assertIn("worktree-git-parity:README.md", broken["errors"])

    def test_pr63_project_adapter_source_truth_and_mutants(self):
        """Finite text/source adversaries; not a human Project or GitHub run."""
        readme = (ROOT / "README.md").read_text("utf-8")
        guide = (ROOT / "docs/AGENT_ADOPTION.md").read_text("utf-8")
        start = (ROOT / "docs/GETTING_STARTED.md").read_text("utf-8")
        dod = (ROOT / "docs/DOCUMENTATION_DOD.md").read_text("utf-8")
        implementation = (ROOT / "src/cora/chat_bundle.py").read_text("utf-8")
        links = (
            "cora/pull/46", "cora/pull/52",
            "ictc/pull/274", "ictc/pull/275",
            "teddy/pull/56", "iKant_EDU/pull/242",
            "iKant_EDU/pull/243",
        )
        commits = (
            "cora/commit/0c700530899446dc27b972c44979ed43b425cebf",
            "cora/commit/094294a3c051fb0a63c4efe19c467845cbb9e393",
            "ictc/commit/cc4d5dc7209823c85cbf170bef27f09f506b3df1",
            "ictc/commit/2aec4230a2f290089894a042fd900b6fa989f595",
            "teddy/commit/767e844ddba865a3bc1dab1d98182c76a10d326a",
            "iKant_EDU/commit/953caf5f79648600ff2a69595dfb6e2b05ae915c",
            "iKant_EDU/commit/b88cea03129ac39b994769cab75c9ff6ee5ee166",
        )

        def source_errors(r, g, s, d, engine):
            errors = []
            def need(condition, code):
                if not condition:
                    errors.append(code)
            need(g.count("## ChatGPT Project beta adapter") == 1,
                 "duplicate-or-missing-adapter")
            need(g.count("CORA LOCAL PROJECT ADAPTER — BETA v1") == 1,
                 "missing-canonical-project-prompt")
            need("Plus or Edu" in g and "ChatGPT Plus or Edu" in r,
                 "undocumented-beta-plan-assumption")
            need("standard ChatGPT GitHub app is read-only" in g,
                 "read-vs-write-capability-confused")
            need("separate write-capable tool" in g and "not permission to push or merge" in r,
                 "missing-independent-write-authorization")
            need("METHOD_ONLY BY DEFAULT" in g and "ENGINE_VERIFIED" in g
                 and "PR_MATERIALIZED" in g, "simulated-execution")
            need("product**" in g and "software**" in g and "repository**" in g,
                 "ontology-collapsed")
            need("not live ChatGPT memory" in g
                 and "**not** automatic chat memory" in r,
                 "handoff-overpromoted")
            need("iterations/{i:06d}" in engine
                 and "iterations/000001/handoff.md" in s,
                 "wrong-real-ZIP-path")
            need("#chatgpt-project-beta-adapter" in r
                 and "AGENT_ADOPTION.md#chatgpt-project-beta-adapter" in s,
                 "broken-canonical-route")
            need(all(link in g for link in links + commits), "untraceable-pr-history")
            need(all(term in g for term in (
                "Blobbing:", "Materialization:", "Semantic commit:",
                "Retrograde AND-DoD:", "Semantic diff:",
                "Falsification / semantic mutation:", "Saturation:",
                "Unknown consumer:")), "missing-engineering-vocabulary")
            need("R63_SOURCE =" in d and "R63_ACCEPTED =" in d
                 and "E01_FIRST_READ_HUMAN" in d
                 and "E03_ENFORCED_HOST_AND_NON_AUTHOR_REVIEW" in d,
                 "source-promoted-to-human-governance")
            return errors

        parts = (readme, guide, start, dod, implementation)
        self.assertEqual(source_errors(*parts), [])
        # One controlled contradiction per distinct reader-risk family.
        mutants = [
            (readme, guide.replace(
                "standard ChatGPT GitHub app is read-only",
                "standard ChatGPT GitHub app can automatically push code", 1),
             start, dod, implementation),
            (readme, guide.replace("separate write-capable tool",
                                   "the same read-only app", 1),
             start, dod, implementation),
            (readme, guide.replace("CORA LOCAL PROJECT ADAPTER — BETA v1",
                                   "unversioned informal instructions", 1),
             start, dod, implementation),
            (readme, guide + "\n## ChatGPT Project beta adapter\nDuplicate.\n",
             start, dod, implementation),
            (readme, guide, start.replace("iterations/000001/handoff.md",
                                          "rounds/000001/handoff.md", 1),
             dod, implementation),
            (readme, guide, start, dod.replace("R63_ACCEPTED =",
                                               "R63_ACCEPTED_IS_AUTOMATIC ="),
             implementation),
            (readme, guide.replace("teddy/pull/56",
                                   "teddy/pull/999999", 1),
             start, dod, implementation),
        ]
        for i, mutant in enumerate(mutants):
            with self.subTest(family=i):
                self.assertTrue(source_errors(*mutant),
                                "semantic corruption survived: " + str(i))

    def test_one_million_distinct_noncompensatory_contract_vectors(self):
        """Exactly 1,000,000 unique 20-bit states and an independent bit oracle."""
        self.assertEqual(len(DOC.ENTERPRISE_SOURCE_LEAVES), 12)
        self.assertEqual(len(DOC.ENTERPRISE_EXTERNAL_LEAVES), 8)
        outcomes = {"REFUTED_SOURCE": 0, "BLOCKED_EXTERNAL": 0,
                    "EVALUATION_ELIGIBLE": 0}
        digest = hashlib.sha256()
        for i in range(1_000_000):
            # Odd multiplier is a permutation modulo 2**20: no duplicate masks.
            mask = (i * 65537 + 1048575) & 1048575
            digest.update(mask.to_bytes(3, "little"))
            # Independent per-bit oracle rather than reusing assess_enterprise_cut.
            source_ok = all((mask >> bit) % 2 == 1 for bit in range(12))
            external_ok = all((mask >> bit) % 2 == 1 for bit in range(12, 20))
            expected = ("REFUTED_SOURCE" if not source_ok else
                        "BLOCKED_EXTERNAL" if not external_ok else
                        "EVALUATION_ELIGIBLE")
            observed = DOC.assess_enterprise_cut(mask)
            self.assertEqual(observed, expected, (i, mask))
            outcomes[observed] += 1
        self.assertEqual(sum(outcomes.values()), 1_000_000)
        self.assertGreater(outcomes["REFUTED_SOURCE"], 0)
        self.assertGreater(outcomes["BLOCKED_EXTERNAL"], 0)
        self.assertEqual(outcomes["EVALUATION_ELIGIBLE"], 1)
        self.assertNotEqual(digest.hexdigest(), "0" * 64)
        self.assertEqual(DOC.assess_enterprise_cut((1 << 12) - 1), "BLOCKED_EXTERNAL")
        for invalid in (-1, 1 << 20, None, True):
            with self.assertRaises(ValueError):
                DOC.assess_enterprise_cut(invalid)
        print("PR62 finite-contract vectors=1000000; final states="
              + repr(outcomes) + "; input_sha256=" + digest.hexdigest()
              + "; runtime_target_executions=0; release_authorizations=0")


import copy
import json
import subprocess
import sys
import tempfile

CAP_SPEC = importlib.util.spec_from_file_location(
    "cora_cross_surface_capability", ROOT / "tools/verify_capability_atlas.py")
CAP = importlib.util.module_from_spec(CAP_SPEC)
CAP_SPEC.loader.exec_module(CAP)


def g(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode("utf-8").strip()


class FullSurfaceExecutionTests(unittest.TestCase):

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
        # The installed interpreter package is the runtime source of the CLI;
        # compare its shipped .py and optional ESM bytes to every original
        # Git source object, not only to the prerelease version string.
        import cora
        package_root = Path(cora.__file__).resolve().parent
        for row in ledger["records"]:
            p = row["path"]
            if not (p.startswith("src/cora/") and
                    p.endswith((".py", ".mjs"))):
                continue
            self.assertEqual(row["status"], "observed_git_blob", p)
            installed = package_root / p[len("src/cora/"):]
            self.assertTrue(installed.is_file(), "package omits: " + p)
            self.assertEqual(hashlib.sha256(installed.read_bytes()).hexdigest(),
                             row["sha256"], "wheel/source byte drift: " + p)

        self.assertEqual(_strict_json(b'{"unique":true}'), {"unique": True})
        with self.assertRaisesRegex(ValueError, "duplicate JSON field"):
            _strict_json(b'{"authority":"NONE","authority":"APPROVED"}')
        with self.assertRaises(SyntaxError):
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


if __name__ == "__main__":
    unittest.main()
