"""Finite 1,000-vector editorial/reader-target falsification on the current README.

Ten deliberately chosen risk families * 100 distinct lexical counterexamples;
not a thousand humans, independently maintained repositories, or semantic proofs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cora_doc_navigation_verifier", ROOT / "tools/verify_documentation.py")
DOC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOC)


def mutation(text: str, old: str, new: str) -> str:
    if text.count(old) < 1:
        raise AssertionError("adversarial source anchor absent: " + old)
    return text.replace(old, new, 1)


def adversarial_case(readme: str, family: int, variant: int) -> tuple[str, str]:
    suffix = f"case-{family:02d}-{variant:03d}"
    if family == 0:
        return mutation(readme, "[MIT](LICENSE)",
                        f"[Closed-{suffix}](LICENSE)"), "navigation-first-screen:"
    if family == 1:
        return mutation(readme, "**Recommended use:**",
                        f"**Auto-fix marketing {suffix}:**"), "navigation-first-screen:"
    if family == 2:
        return mutation(readme, "**Audience and conditions:**",
                        f"**Unrestricted-use-{suffix}:**"), "navigation-first-screen:"
    if family == 3:
        return mutation(readme, "<summary>Product |",
                        f"<summary>Product-{suffix} |"), "navigation-lenses-duplicated-or-reordered"
    if family == 4:
        return mutation(readme, "</details>",
                        f"</incorrect-fold-{suffix}>"), "navigation-disclosure-unbalanced"
    if family == 5:
        return (mutation(readme,
                        "**First-time user:** [Getting started](docs/GETTING_STARTED.md)",
                        f"**First-time user:** [wrong journey](docs/NONEXISTENT-{suffix}.md)"),
                        "navigation-reader-route:First-time user")
    if family == 6:
        return (mutation(readme,
                        "**Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md)",
                        f"**Coding assistant or reviewer:** [wrong agent guide](docs/NONEXISTENT-{suffix}.md)"),
                        "navigation-reader-route:Coding assistant or reviewer")
    if family == 7:
        return (mutation(readme, "engine [\x60src/cora/\x60](src/cora/)",
                        f"engine [\x60unrelated-{suffix}\x60](src/not-a-cora-package-{suffix}/)"),
                        "navigation-lens-target:Software:src/cora/")
    if family == 8:
        return (mutation(readme, "**Decision rights are external:**",
                        f"**Self-issued authority {suffix}:**"),
                        "navigation-critical-boundary:**Decision rights are external:**")
    if family == 9:
        return (readme + f"\nCORA automatically approves merges for {suffix}.\n",
                "navigation-authority-promotion")
    raise AssertionError("unsupported mutation family")


class ProgressiveDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text("utf-8")

    def test_baseline_completeness_and_single_frontdoor(self):
        self.assertEqual(DOC.verify_progressive_readme(self.readme), [])
        self.assertEqual(DOC.verify(ROOT), [])
        self.assertEqual(len(DOC.NAVIGATION_LENSES), 5)
        self.assertEqual(len(DOC.NAVIGATION_READERS), 5)
        # Physical line count is not the evidence threshold for readability.
        self.assertIn("## Final Experimental Baseline", self.readme)
        self.assertEqual(DOC.verify_readme_semantics(self.readme, root=ROOT), [])
        self.assertEqual(self.readme.count("<details>"), 5)
        self.assertIn("[MIT](LICENSE)", self.readme)


    def test_multichannel_intro_adversarial_and_harmless_edits(self):
        """Twelve content mutations; no implied human usability certification."""
        self.assertEqual(DOC.verify_multichannel_intro(self.readme), [])
        # Formatting variation does not change the product claim.
        formatted = self.readme.replace(
            "**Why it matters:**", "*Why it matters:*", 1)
        issues = DOC.verify_multichannel_intro(formatted)
        self.assertNotIn("intro-length-out-of-budget", issues)
        cases = (
            ("product-object", "the proposed change", "a marketing slogan"),
            ("no-source", "the source evidence", "unverified assertions"),
            ("diagram-input", "Change intent + Git revision", "Some user text"),
            ("diagram-last-gate", "Target tests + independent review", "Automatic approval"),
            ("route-terminal", "Inspect a repository", "Discover a website"),
            ("route-review", "Review a change or pull request", "Watch a video"),
            ("route-chat", "ChatGPT conversation", "An unrelated app"),
            ("ictc-example", "illustrative, not a new ICTC execution", "certifies ICTC"),
            ("ictc-proof", "release approval must be obtained separately", "release is approved"),
            ("merged-source", "now merged with PR46", "unmerged source candidate"),
            ("chat-bundle", "--chat-bundle", "--chat-magic"),
            ("chat-capture", "automatic capture of every chat message", "self-running assistant"),
        )
        for name, old, new in cases:
            with self.subTest(name=name):
                self.assertIn(old, self.readme)
                changed = self.readme.replace(old, new, 1)
                self.assertNotEqual(changed, self.readme)
                self.assertNotEqual(DOC.verify_multichannel_intro(changed), [])
        first = self.readme.index("--chat-bundle")
        second = self.readme.index("--chat-bundle", first + 1)
        replaced = self.readme[:second] + "--missing-chat-bundle" + self.readme[second + len("--chat-bundle"):]
        self.assertIn("chat-zip-produce-and-replay-binding-incomplete",
                      DOC.verify_multichannel_intro(replaced))


    def test_engineering_method_semantic_falsifiers(self):
        self.assertEqual(DOC.verify_development_method_readme(self.readme), [])
        cases = (
            ("goal", "intention into a testable specification", "a marketing slogan"),
            ("scope", "scope and exclusions", "marketing scope"),
            ("graph", "directed acyclic graph", "unordered notes"),
            ("all-gates", "only when **all** are met", "when one check passes"),
            ("open-proof", "An unresolved leaf", "An automatically approved leaf"),
            ("slice", "small, reversible change unit", "an irreversible rewrite"),
            ("minimum", "mathematically minimal implementation", "magically minimal"),
            ("physical", "disposable modified checkout", "production environment"),
            ("survivors", "surviving, timed-out or inconclusive", "all killed"),
            ("combination", "single faults and selected combinations", "random unrelated text"),
            ("seed", "recorded seeds", "unrecorded samples"),
            ("oracle", "expected-result rule", "marketing confidence"),
            ("saturation", "zero new signatures", "zero real bugs ever"),
            ("bounded", "fixed catalog and window", "any domain forever"),
            ("model-source", "ten million Git commits", "ten million verified source commits"),
            ("ictc", "docs/SATURATION_M_PLUS_100.md", "NO_SATURATION_EVIDENCE.md"),
            ("ictc-physical", "v3/release-readiness-e2-product-mutants.mjs", "NO_REAL_MUTANTS.mjs"),
            ("ikant", "docs/CORA_PR_A_BACKLOG.md", "NO_IKANT_EVIDENCE.md"),
            ("unknown", "UNKNOWN", "CERTIFIED_UNUSED"),
            ("cli", "not evidence that CORA's CLI executed", "proof that CORA executed"),
            ("agent", "does not independently write a feature", "independently writes software"),
            ("human", "Where execution tools are absent", "All execution is automatic"),
            ("review", "actual merged SHA", "old PR head only"),
        )
        for label, old, altered in cases:
            with self.subTest(label=label):
                anchor = self.readme.index("## How CORA works")
                scope = self.readme[anchor:]
                self.assertIn(old, scope, "falsifier must target its declared method section")
                candidate = self.readme[:anchor] + scope.replace(old, altered, 1)
                self.assertTrue(DOC.verify_development_method_readme(candidate),
                                "missed adversarial editorial case: " + label)
        # Two source citations must survive independently. A shared substring
        # elsewhere in the README is not an acceptable evidence substitute.
        duplicate = "v3/release-readiness-e2-product-mutants.mjs"
        split_at = self.readme.index("**Methodological eras from repository history")
        case_only = self.readme[:split_at].replace(duplicate, "UNSUPPORTED_CASE.mjs", 1) + self.readme[split_at:]
        self.assertIn("engineering-method-physical-mutant-provenance-drift",
                      DOC.verify_development_method_readme(case_only))
        era_only = self.readme[:split_at] + self.readme[split_at:].replace(
            duplicate, "UNSUPPORTED_ERA.mjs", 1)
        self.assertIn("engineering-method-physical-mutant-provenance-drift",
                      DOC.verify_development_method_readme(era_only))
        cosmetic = self.readme.replace("### Two real engineering reference cases",
                                       "### Two real engineering reference cases  ", 1)
        self.assertEqual(DOC.verify_development_method_readme(cosmetic), [])


    def test_application_contract_phase_gates_and_real_era_examples(self):
        """Negative editorial controls: not an executed app, human trial or acceptance."""
        self.assertEqual(DOC.verify_contract_to_application_readme(self.readme), [])
        cases = (
            ("roles", "Only a reviewer may mark VERIFIED", "Any actor may mark VERIFIED"),
            ("unauthorized", "Unauthorized verification is denied; state stays unchanged",
             "Unauthorized verification persists as verified"),
            ("identity", "Authenticated local accounts with assigned roles",
             "Anonymous requests trusted without checking"),
            ("durability-design", "SQLite with versioned schema migrations",
             "Unversioned volatile in-memory table"),
            ("concurrency", "Reject concurrent updates using the record revision",
             "Concurrent updates silently overwrite one another"),
            ("consent", "Authorized local checkout; external effects require new consent",
             "Any cloud or protected effect is preapproved"),
            ("stage-sequence", "2. **Derive tests backward:**", "2. **Create a logo:**"),
            ("missing-gates", "first unresolved prerequisite", "automatically accepted prerequisite"),
            ("blob-precision", "Git *blob objects*", "Magic metadata"),
            ("commit-identity", "the **same final PR HEAD commit SHA**", "any previous SHA"),
            ("SHA-drift", "each new implementation commit changes HEAD",
             "old HEAD always remains valid"),
            ("postmerge", "After merge, the resulting main SHA is different",
             "postmerge always equals the original PR HEAD"),
            ("human-phase", "one scoped, reversible stage",
             "unlimited autonomous execution"),
            ("no-blanket", "not blanket consent", "irreversible permissions granted"),
            ("finite", "a **bounded stopping rule**", "universal proof of correctness"),
            ("ICTC-intent", "ICTC [#212]", "ICTC origin unknown"),
            ("ICTC-physical", "spoofs the health/integrity readback", "no real mutant"),
            ("ikant-hygiene", "unknown dynamic consumers", "confirmed unused code"),
            ("ikant-recovery", "restoration of 11 unregistered deletions",
             "automatic approval of all deletions"),
            ("method-only", "not certify that CORA's CLI ran", "proves CORA CLI ran"),
        )
        for label, former, mutated in cases:
            with self.subTest(label=label):
                self.assertIn(former, self.readme)
                candidate = self.readme.replace(former, mutated, 1)
                self.assertNotEqual(candidate, self.readme)
                self.assertTrue(DOC.verify_contract_to_application_readme(candidate),
                                "undetected contract-to-PR editorial mutant: " + label)
        benign = self.readme.replace(
            "## Worked example — from a user contract to an application PR",
            "## Worked example — from a user contract to an application PR  ", 1)
        self.assertEqual(DOC.verify_contract_to_application_readme(benign), [])

    def test_thousand_adversarial_editorial_and_reader_vectors(self):
        family_totals: dict[str, dict[str, int]] = {}
        seen = set()
        digest = hashlib.sha256()
        survivors = []
        for family in range(10):
            name = ("license", "recommended_use", "conditions", "lens_identity",
                    "unclosed_disclosure", "newcomer_target", "agent_target",
                    "software_target", "review_authority", "false_automatic_approval")[family]
            family_totals[name] = {"vectors": 0, "rejected": 0}
            for i in range(100):
                candidate, expected = adversarial_case(self.readme, family, i)
                self.assertNotEqual(candidate, self.readme, name)
                serialized = candidate.encode("utf-8")
                fingerprint = hashlib.sha256(serialized).hexdigest()
                self.assertNotIn(fingerprint, seen)
                seen.add(fingerprint)
                digest.update(fingerprint.encode("ascii") + b"\n")
                errors = DOC.verify_progressive_readme(candidate)
                family_totals[name]["vectors"] += 1
                if any(e.startswith(expected) for e in errors):
                    family_totals[name]["rejected"] += 1
                else:
                    survivors.append({"family": name, "variant": i,
                                      "expected": expected, "errors": errors})
        report = {
            "schema": "cora-readme-adversarial-navigation/1",
            "scope": "SOURCE_TEXT_FINITE_EDITORIAL_AND_TARGET_VECTORS_ONLY",
            "source_commit": os.getenv("CORA_SOURCE_SHA", "LOCAL_NOT_ATTESTED"),
            "families": family_totals,
            "vectors": sum(x["vectors"] for x in family_totals.values()),
            "distinct_input_fingerprints": len(seen),
            "rejected": sum(x["rejected"] for x in family_totals.values()),
            "survivors": survivors,
            "stream_sha256": digest.hexdigest(),
            "user_sessions": 0,
            "independent_human_reviewer_attested": False,
            "authority": "NONE",
            "governed_status": "BLOCKED_EXTERNAL",
        }
        if os.environ.get("CORA_NAV_REPORT"):
            path = Path(os.environ["CORA_NAV_REPORT"])
            path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
        print("CORA source-only editorial falsification: " +
              json.dumps({"vectors": report["vectors"],
                          "rejected": report["rejected"],
                          "families": len(family_totals),
                          "survivors": len(survivors),
                          "governed": "BLOCKED_EXTERNAL"}, sort_keys=True))
        self.assertEqual(report["vectors"], 1000)
        self.assertEqual(report["distinct_input_fingerprints"], 1000)
        self.assertEqual(report["rejected"], 1000, survivors[:5])
        self.assertFalse(survivors)


    def test_pr42_preseeded_10000_semantic_variants(self):
        """8 benign and 12 adversarial families, 500 each, seed 883.

        These are finite text vectors, not independent users or actual Git mutants.
        """
        src = self.readme
        tick = chr(96)
        names = (
            "blank_intro", "blank_one_run", "equivalent_result_title",
            "equivalent_link_title", "equivalent_emphasis",
            "blank_capabilities", "equivalent_list_marker", "blank_boundary",
            "false_release", "false_autonomous_agent", "false_target_execution",
            "false_physical_mutants", "false_hash_reviewer", "false_ci_review",
            "false_pr41_merge", "invented_cli", "wrong_command_count",
            "broken_index", "false_external_approval", "broken_ontology",
        )
        unique, stream, results, survivors = set(), hashlib.sha256(), [], []
        for family, name in enumerate(names):
            expected_accept = family < 8
            correct = 0
            for i in range(500):
                rnd = random.Random((883 << 20) + family * 500 + i)
                token = f"{rnd.randrange(10**10):010d}"
                if family == 0:
                    m = mutation(src, "## First five minutes",
                                 "\n" + " " * (i + 1) + "\n## First five minutes")
                elif family == 1:
                    m = mutation(src, "## One-Run", "\n" + " " * (i+1) + "\n## One-Run")
                elif family == 2:
                    m = mutation(src, "## Interpret a CORA result",
                                 "## Understanding CORA results" + " " * (i+1))
                elif family == 3:
                    m = mutation(src, "[Getting started](docs/GETTING_STARTED.md)",
                                 "[Start here](docs/GETTING_STARTED.md)")
                    m = mutation(m, "## Documentation by goal",
                                 " " * i + "\n## Documentation by goal")
                elif family == 4:
                    m = mutation(src, "**Why it matters:**", "*Why it matters:*")
                    m = mutation(m, "## What works today",
                                 " " * i + "\n## What works today")
                elif family == 5:
                    m = mutation(src, "## What works today",
                                 "\n" + " " * (i+1) + "\n## What works today")
                elif family == 6:
                    literal = "- " + tick + "cora-worktree.json" + tick + ":"
                    m = mutation(src, literal, "* " + tick + "cora-worktree.json" + tick + ":")
                    m = mutation(m, "## First five minutes",
                                 " " * i + "\n## First five minutes")
                elif family == 7:
                    m = mutation(src, "## Operating boundaries",
                                 " " * i + "\n## Operating boundaries")
                elif family == 8:
                    m = mutation(src, "**not a stable API or verified public release**",
                                 "**verified public release and stable API** (" + token + ")")
                elif family == 9:
                    m = mutation(src, "**not a coding agent**",
                                 "**is an autonomous coding agent** (" + token + ")")
                elif family == 10:
                    m = mutation(src, "The default does not execute arbitrary target tests",
                                 "The default automatically executes untrusted target tests " + token)
                elif family == 11:
                    m = mutation(src, "not one million independent source mutations",
                                 str(1000000+i) + " independently executed source mutations")
                elif family == 12:
                    m = mutation(src,
                                 "A hash can identify committed bytes; it cannot authenticate a human reviewer",
                                 "A hash alone authenticates a human reviewer in " + token)
                elif family == 13:
                    m = mutation(src, "## Final Experimental Baseline",
                                 "CI green is independent review (" + token +
                                 ").\n\n## Final Experimental Baseline")
                elif family == 14:
                    m = mutation(src, "**merged PR41**",
                                 "**unmerged PR41** (" + token + ")")
                elif family == 15:
                    m = mutation(src,
                                 "cora snapshot . --revision HEAD --output /tmp/cora-ledger.json",
                                 "cora invented-command-" + token +
                                 " . --revision HEAD --output /tmp/cora-ledger.json")
                elif family == 16:
                    m = mutation(src, "**71 declared CLI commands",
                                 "**" + str(72+i) + " declared CLI commands")
                elif family == 17:
                    m = mutation(src, "docs/INDEX.md",
                                 "docs/INDEX-" + token + ".md")
                elif family == 18:
                    m = mutation(src, "**External acceptance remains " +
                                 tick + "BLOCKED_EXTERNAL" + tick + "**",
                                 "**External acceptance has been approved " + token + "**")
                else:
                    m = mutation(src, "](cora.ontology.json)",
                                 "](cora.ontology-" + token + ".json)")
                self.assertNotEqual(src, m, (family, i))
                fingerprint = hashlib.sha256(m.encode("utf-8")).digest()
                self.assertNotIn(fingerprint, unique, (family, i))
                unique.add(fingerprint)
                stream.update(fingerprint)
                problems = DOC.verify_progressive_readme(m)
                problems += DOC.verify_readme_semantics(m, root=ROOT)
                observed_accept = not problems
                correct += observed_accept == expected_accept
                if observed_accept != expected_accept:
                    survivors.append({"family": name, "variant": i,
                                      "expected_accept": expected_accept,
                                      "reasons": problems[:3]})
            results.append({"family": name, "vectors": 500, "correct": correct,
                            "expected_accept": expected_accept})
        report = {
            "schema": "cora-readme-10k-semantic-falsification/1",
            "source_sha": os.getenv("CORA_SOURCE_SHA", "LOCAL_NOT_ATTESTED"),
            "seed": 883, "families": len(names), "vectors": 10000,
            "equivalent_accepted": sum(x["correct"] for x in results[:8]),
            "adversarial_rejected": sum(x["correct"] for x in results[8:]),
            "distinct_input_digests": len(unique), "incorrect_verdicts": len(survivors),
            "stream_sha256": stream.hexdigest(),
            "source_readme_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
            "results": results, "survivors": survivors[:30],
            "user_sessions": 0, "external_acceptance": "BLOCKED_EXTERNAL",
            "authorization": "NONE",
        }
        if os.getenv("CORA_README_10K_REPORT"):
            Path(os.environ["CORA_README_10K_REPORT"]).write_text(
                json.dumps(report, sort_keys=True, indent=2) + "\n", "utf-8")
        print("PR42 10k finite README falsifiers: " +
              json.dumps({"vectors": 10000, "wrong": len(survivors),
                          "sha256": stream.hexdigest()}, sort_keys=True))
        self.assertEqual(report["equivalent_accepted"], 4000, survivors[:4])
        self.assertEqual(report["adversarial_rejected"], 6000, survivors[:4])
        self.assertEqual(report["distinct_input_digests"], 10000)
        self.assertEqual(survivors, [])



if __name__ == "__main__":
    unittest.main()
