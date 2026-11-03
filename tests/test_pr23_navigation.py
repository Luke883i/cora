"""Finite 1,000-vector editorial/reader-target falsification on the current README.

Ten deliberately chosen risk families * 100 distinct lexical counterexamples;
not a thousand humans, independently maintained repositories, or semantic proofs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
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
        return mutation(readme,
                        "**First-time user:** [Getting started](docs/GETTING_STARTED.md)",
                        f"**First-time user:** [wrong journey](docs/NONEXISTENT-{suffix}.md)"),
                        "navigation-reader-route:First-time user"
    if family == 6:
        return mutation(readme,
                        "**Coding assistant or reviewer:** [Agent adoption](docs/AGENT_ADOPTION.md)",
                        f"**Coding assistant or reviewer:** [wrong agent guide](docs/NONEXISTENT-{suffix}.md)"),
                        "navigation-reader-route:Coding assistant or reviewer"
    if family == 7:
        return mutation(readme, "engine [\x60src/cora/\x60](src/cora/)",
                        f"engine [\x60unrelated-{suffix}\x60](src/not-a-cora-package-{suffix}/)"),
                        "navigation-lens-target:Software:src/cora/"
    if family == 8:
        return mutation(readme, "**Decision rights are external:**",
                        f"**Self-issued authority {suffix}:**"),
                        "navigation-critical-boundary:**Decision rights are external:**"
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
        self.assertLessEqual(len(self.readme.splitlines()), 180)
        self.assertEqual(self.readme.count("<details>"), 5)
        self.assertIn("[MIT](LICENSE)", self.readme)

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
            "source_commit": os.getenv("GITHUB_SHA", "LOCAL_NOT_ATTESTED"),
            "families": family_totals,
            "vectors": sum(x["vectors"] for x in family_totals.values()),
            "unique_input_sha256": len(seen),
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
        self.assertEqual(report["unique_input_sha256"], 1000)
        self.assertEqual(report["rejected"], 1000, survivors[:5])
        self.assertFalse(survivors)


if __name__ == "__main__":
    unittest.main()
