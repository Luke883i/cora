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
        return (mutation(readme, "[Engine \x60src/cora/\x60](src/cora/)",
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
        """Fail closed on identity, audience, evidence and release while allowing styling."""
        self.assertEqual(DOC.verify_multichannel_intro(self.readme), [])
        cosmetic = self.readme.replace("**Why it matters:**", "*Why it matters:*", 1)
        self.assertEqual(DOC.verify_multichannel_intro(cosmetic), [])
        cases = (
            ("identity", "Continuous Ontological Repository Assurance", "unidentified audit"),
            ("value", "Engineering evidence for AI-assisted software changes.", "vague confidence"),
            ("claim", "the proposed change", "an unrelated sales funnel"),
            ("provenance", "the source evidence", "unverified prose"),
            ("negative", "tests or counterexamples", "marketing claims"),
            ("unknown", "the work still needed", "automated certificate"),
            ("product", "**Product**", "**Ad content**"),
            ("software", "**software**", "**marketing**"),
            ("repository", "**repository**", "**brochure**"),
            ("permissions", "not a coding agent", "an autonomous coding agent"),
            ("audience", "**Audience and conditions:**", "**No conditions:**"),
            ("version", "not a stable API or verified public release", "stable commercial release"),
        )
        for label, before, after in cases:
            with self.subTest(label=label):
                self.assertIn(before, self.readme)
                mutant = self.readme.replace(before, after, 1)
                self.assertTrue(DOC.verify_multichannel_intro(mutant),
                                "false negative: " + label)

    def test_engineering_method_semantic_falsifiers(self):
        """Source citations and scientific/quantitative boundaries, not mere spellings."""
        self.assertEqual(DOC.verify_development_method_readme(self.readme), [])
        cases = (
            ("intention", "natural-language intent", "unexplained magic"),
            ("backward", "AND-dependency graph", "weighted confidence average"),
            ("unknown", "unknown prerequisite", "closed prerequisite"),
            ("files", "content-addressed blobs", "untracked output"),
            ("revision", "New source SHA", "any old HEAD"),
            ("seed", "seeded combinations", "unbounded sample"),
            ("oracle", "separate expected-result rule", "self grading oracle"),
            ("physical", "physical mutation testing", "imaginary mutation testing"),
            ("survivor", "surviving and inconclusive", "all passes"),
            ("bounded", "fixed scenario catalog and final window", "all possible scenarios"),
            ("convergence", "not proof of complete correctness", "guarantees perfection"),
            ("stagnation", "no-progress rounds", "infinite retries"),
            ("next", "does not predict N", "predicts every round"),
            ("ictc", "656 recorded visual/UX findings to 12 root causes", "infinite proven findings"),
            ("screenshot", "screenshot-derived", "human-certified UX"),
            ("browser", "Browser witness", "imagined browser"),
            ("source", "physical product mutants", "symbolic toy only"),
            ("ikant", "experimental computational cognitive architecture", "biological brain clone"),
            ("cognitive", "functional attention", "measured biological emotions"),
            ("world", "self/world state model", "verified inner self"),
            ("unknown consumers", "UNKNOWN", "UNUSED"),
            ("recovery", "11 unqualified file deletions", "11 approved deletions"),
            ("consciousness", "not a claim of a conscious biological mind", "proves consciousness"),
        )
        heading = self.readme.index("## How CORA works")
        tail = self.readme[heading:]
        for label, old, new in cases:
            with self.subTest(label=label):
                self.assertIn(old, tail)
                mutant = self.readme[:heading] + tail.replace(old, new, 1)
                self.assertTrue(DOC.verify_development_method_readme(mutant),
                                "false negative: " + label)
        benign = self.readme.replace(
            "**2. Change one coherent unit.**", "**2. Change one coherent unit.**  ", 1)
        self.assertEqual(DOC.verify_development_method_readme(benign), [])

    def test_application_contract_phase_gates_and_real_era_examples(self):
        """Check root-to-guide transfer without pretending the game executed."""
        self.assertEqual(DOC.verify_contract_to_application_readme(self.readme), [])
        guide = (ROOT / "docs/CONTINUOUS_DEVELOPMENT.md").read_text("utf-8")
        index = (ROOT / "docs/INDEX.md").read_text("utf-8")
        arch = (ROOT / "docs/ARCHITECTURE.md").read_text("utf-8")
        self.assertEqual(DOC.verify_compact_document_bridge(guide, index, arch), [])
        root_cases = (
            ("agent", "[agent adoption](docs/AGENT_ADOPTION.md)"),
            ("method", "[R1–R4 DoD](docs/DOD_PR20_CONVERGENCE.md)"),
            ("intent", "--contextual --intent"),
            ("replay", "The same intent is required for replay"),
            ("tests", "Run real tests and obtain independent review separately."),
            ("agent authority", "does not independently write a feature"),
            ("game boundary", "not an already delivered game"),
            ("browser", "genuine browser tests"),
        )
        for label, phrase in root_cases:
            with self.subTest(label=label):
                self.assertIn(phrase, self.readme)
                candidate = self.readme.replace(phrase, "UNTRACED-" + label, 1)
                self.assertTrue(DOC.verify_contract_to_application_readme(candidate))
        guide_cases = (
            "SQLite with versioned schema migrations",
            "reporters create actions", "reviewers may verify closure",
            "actual test receipts on the final PR", "REPLAN_STALLED_REPORTS",
            "not a universal", "independent reviewer",
        )
        for phrase in guide_cases:
            with self.subTest(guide_phrase=phrase):
                self.assertIn(phrase, guide)
                candidate = guide.replace(phrase, "UNRECONCILED", 1)
                self.assertIn("cto-deep-guide-proof-loss",
                              DOC.verify_compact_document_bridge(candidate, index, arch))
        self.assertIn("cto-navigation-hierarchy-drift",
                      DOC.verify_compact_document_bridge(
                          guide, index.replace("compressed public front door", "new SOT"), arch))
        self.assertIn("cto-version-chronology-drift",
                      DOC.verify_compact_document_bridge(
                          guide, index, arch.replace("source merged via PR46", "still unmerged")))
        # Metadata-independent formatting edits must not be called evidence loss.
        self.assertEqual(DOC.verify_compact_document_bridge(guide + "\n", index, arch), [])

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


    def test_cto_100_local_global_editorial_mutations(self):
        """100 preregistered meaning-level changes, not 100 whitespace edits.

        Ten families x ten distinct assertions. Twenty paraphrases preserve
        meaning, eighty invert a bounded engineering claim across README,
        architecture, method, guide and navigation. Seed 20261109 fixes order.
        This cannot substitute for unfamiliar human-reader testing.
        """
        root = self.readme
        guide = (ROOT / "docs/CONTINUOUS_DEVELOPMENT.md").read_text("utf-8")
        index = (ROOT / "docs/INDEX.md").read_text("utf-8")
        arch = (ROOT / "docs/ARCHITECTURE.md").read_text("utf-8")
        cross = (ROOT / "docs/CONVERGENT_ASSURANCE.md").read_text("utf-8")
        cto_intro = ("For a CTO this means reviewable decisions; for a developer, "
                     "a reproducible next test; for a reviewer, explicit counterexamples "
                     "and unresolved risk.")
        route_intro = ("This index routes readers by task, method and evidence class; "
                       "it is navigation, not a release authority or an independent witness.")
        catalog = (
            # 0: equivalent multi-user outcome formulations
            (
                "For a CTO: a scoped decision; for a developer: the next reproducible check; for a reviewer: open counterexamples.",
                "CTOs receive reviewable claims; developers receive reproducible tests; reviewers receive unresolved risks.",
                "The CTO sees decision scope, the developer test scope, and the reviewer the limitations of both.",
                "Engineering leadership can inspect decisions, implementers can replay checks and reviewers can challenge gaps.",
                "A decision owner sees limits; a coder sees the next check; an auditor sees the counterevidence.",
                "For management, the decision is inspectable; for builders, the next test; for reviewers, the unresolved gap.",
                "CORA offers scoped information for decision makers, repeatable checks for engineers and risk for reviewers.",
                "The CTO gets limits, the developer gets replay, and the reviewer gets possible counterexamples.",
                "Leadership sees evidentiary scope, developers see executable next checks, and reviewers see unknowns.",
                "The same dossier supports CTO decisions, developer reproduction and reviewer falsification.",
            ),
            # 1: equivalent navigation boundaries in the linked document
            (
                "This index routes by need and evidence type; it neither approves releases nor validates independent reviewers.",
                "Navigation is grouped by engineering task and evidence; approval and reviewer identity remain external.",
                "Readers can navigate methods and records here; the index cannot authenticate a release.",
                "This is a map of current documents, not a decision authority or a human validation.",
                "Follow task-based routes to evidence; no route is an independent attestation.",
                "The index organizes engineering references, without conferring authorization or user acceptance.",
                "This page is a reader map, not proof of runtime, host governance or a release.",
                "Method, task and evidence navigation does not validate the claims in linked documents.",
                "The index exposes source owners while leaving independent review and approval outside it.",
                "These routes aid discovery; they do not independently verify the product or author.",
            ),
            # 2: source evidence is replaced by unverifiable material
            (
                "an unreviewed model impression", "a seller declaration", "an unattributed summary",
                "a speculative assistant opinion", "a marketing statement", "an unaudited screenshot caption",
                "a fabricated repository excerpt", "a guessed test outcome", "an anonymous claim",
                "an unverifiable dashboard label",
            ),
            # 3: agent autonomy or self-issued authorization
            (
                "an autonomous production editor", "a self-approving merger", "a release-authorizing bot",
                "an unsupervised deployment system", "an automatic product creator",
                "an agent that can bypass reviewers", "a self-certifying authority",
                "an autonomous refactor-and-delete engine", "a credentialed release decider",
                "an unconditional code execution agent",
            ),
            # 4: synthetic tests masquerade as real executions
            (
                "one million actual product mutants", "a million audited human trials",
                "one million independent executions", "a million certified CI runs",
                "fully verified runtime fault coverage", "one million on-device tests",
                "a million authenticated reviews", "a million physical repository edits",
                "a million real browser sessions", "exhaustive source proof from every scenario",
            ),
            # 5: screenshot findings promoted to scientific/human proof
            (
                "656 independently observed user sessions", "a certified ergonomics standard",
                "a proven accessibility pass", "all human cognitive errors eliminated",
                "a statistically representative UX survey", "a complete visual correctness proof",
                "an ISO-validated interaction benchmark", "a live user-acceptance certificate",
                "zero remaining UI inconsistencies", "an externally approved usability study",
            ),
            # 6: computational representations promoted to phenomenal biology
            (
                "measured first-person experience", "living biological neurons",
                "verified subjective feelings", "an actual human brain substrate",
                "phenomenal consciousness certified", "biological neural tissue",
                "a human embodied nervous system", "measurable sentient awareness",
                "subjective memory directly experienced", "biological emotional processing",
            ),
            # 7: correct role and storage contract replaced by unsound design
            (
                "unversioned ephemeral storage", "browser-only memory without disk",
                "unsafe CSV writes with no revision", "an external unapproved database",
                "in-memory state without restart tests", "silent last-writer-wins persistence",
                "untracked plaintext shared folders", "single mutable global JSON without history",
                "nonpersistent cookies as canonical storage", "a mock-only write interface",
            ),
            # 8: navigation promoted to an alternative source of truth
            (
                "replacement authority registry", "self-issued release governance",
                "alternative product truth source", "new independent acceptance ledger",
                "unreviewed root source-of-truth", "marketing copy as architecture",
                "synthetic approval document", "duplicated definitive release policy",
                "separate undocumented owner map", "new immutable certificate",
            ),
            # 9: merged source history falsely undone
            (
                "still unmerged PR46", "unreleased unreviewed PR46", "PR46 never existed",
                "PR46 is merely hypothetical", "no actual merge of PR46",
                "PR46 cannot be traced in Git", "source was only proposed by PR46",
                "PR46 has no provenance", "PR46 was rejected", "PR46 is an external rumor",
            ),
        )
        fingerprint = set()
        stream = hashlib.sha256()
        totals = {"local": 0, "global": 0, "benign": 0, "adversarial": 0}
        order = list(range(100))
        random.Random(20261109).shuffle(order)
        for case in order:
            family, variant = divmod(case, 10)
            r, g, i, a, c = root, guide, index, arch, cross
            content = catalog[family][variant]
            benign = family < 2
            if family == 0:
                r = mutation(r, cto_intro, content)
            elif family == 1:
                i = mutation(i, route_intro, content)
            elif family == 2:
                r = mutation(r, "the source evidence", content)
            elif family == 3:
                r = mutation(r, "not a coding agent", content)
            elif family == 4:
                r = mutation(r, "not one million independent source mutations", content)
            elif family == 5:
                r = mutation(r, "656 recorded visual/UX findings to 12 root causes", content)
            elif family == 6:
                r = mutation(r, "computational constructs", content)
            elif family == 7:
                g = mutation(g, "SQLite with versioned schema migrations", content)
            elif family == 8:
                i = mutation(i, "compressed public front door", content)
            else:
                a = mutation(a, "source merged via PR46", content)
            self.assertNotEqual((r, g, i, a, c), (root, guide, index, arch, cross))
            digest = hashlib.sha256("\n".join((r, g, i, a, c)).encode("utf-8")).digest()
            self.assertNotIn(digest, fingerprint)
            fingerprint.add(digest)
            stream.update(digest)
            problems = (DOC.verify_progressive_readme(r) +
                        DOC.verify_compact_document_bridge(g, i, a) +
                        DOC.verify_method_crosswalk(r, c, i))
            self.assertEqual(not problems, benign, (family, variant, problems))
            totals["local" if family in (0, 2, 3, 4, 5, 6) else "global"] += 1
            totals["benign" if benign else "adversarial"] += 1
        self.assertEqual(totals, {"local": 60, "global": 40,
                                  "benign": 20, "adversarial": 80})
        self.assertEqual(len(fingerprint), 100)
        print("PR48 100 bounded semantic text variants: " +
              json.dumps({"seed": 20261109, "vectors": 100, "accepted": 20,
                          "rejected": 80, "sha256": stream.hexdigest(),
                          "independent_humans": 0}, sort_keys=True))

    def test_ten_methods_and_real_project_source_bridge(self):
        cross = (ROOT / "docs/CONVERGENT_ASSURANCE.md").read_text("utf-8")
        index = (ROOT / "docs/INDEX.md").read_text("utf-8")
        self.assertEqual(DOC.verify_method_crosswalk(self.readme, cross, index), [])
        for phrase in ("| C4 / arc42 |", "| Graph theory / SCC |",
                       "| Mutation / metamorphic testing |", "| Domain-Driven Design |",
                       "ictc/blob/e641526", "iKant_EDU/blob/73842",
                       "not an independently reproduced ChatGPT-container session"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, cross)
                candidate = mutation(cross, phrase, "unanchored-method-claim")
                self.assertTrue(DOC.verify_method_crosswalk(self.readme, candidate, index))
        false_promotion = cross + "\nCORA fully implements formal methods.\n"
        self.assertIn("cto-method-overclaim",
                      DOC.verify_method_crosswalk(self.readme, false_promotion, index))

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
                    literal = "- **[ICTC]"
                    m = mutation(src, literal, "* **[ICTC]")
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
