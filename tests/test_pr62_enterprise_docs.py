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

    def test_readme_evaluation_budget_and_source_reality(self):
        readme = (ROOT / "README.md").read_text("utf-8")
        index = (ROOT / "docs/INDEX.md").read_text("utf-8")
        self.assertLessEqual(len(readme.split()), 1450)
        self.assertLess(len(readme.encode("utf-8")), 14204)
        self.assertFalse(re.search(r"(?im)^#{2,3}[^\n]*\bPR[- ]?\d+", readme))
        self.assertLessEqual(len(re.findall(r"\bPR[- #]?\d+\b", readme, re.I)), 3)
        self.assertEqual(DOC.verify_readme_semantics(readme, root=ROOT), [])
        self.assertEqual(DOC.verify_progressive_readme(readme), [])
        self.assertIn("Implementation and historical detail", index)
        self.assertIn("compressed public front door", index)
        self.assertIn("SLSA provenance: NOT_ATTESTED", readme)
        self.assertIn("External acceptance remains `BLOCKED_EXTERNAL`", readme)
        self.assertIn("not one million independent source mutations", readme)

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

        def source_errors(r, g, s, d, engine):
            errors = []
            def need(condition, code):
                if not condition:
                    errors.append(code)
            need(g.count("## ChatGPT Project beta adapter") == 1,
                 "duplicate-or-missing-adapter")
            need(g.count("CORA LOCAL PROJECT ADAPTER — BETA v1") == 1,
                 "missing-canonical-project-prompt")
            need("Plus or Edu" in g and "Plus/Edu recipe" in r,
                 "undocumented-beta-plan-assumption")
            need("standard ChatGPT GitHub app is read-only" in g,
                 "read-vs-write-capability-confused")
            need("separate write-capable tool" in g and "cannot push code" in r,
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
            need(all(link in g for link in links), "untraceable-pr-history")
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


if __name__ == "__main__":
    unittest.main()
