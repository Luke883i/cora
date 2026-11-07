"""PR41 independent negative tests: committed Git, physical behavior and finite faults."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import verify_final_experimental as final

ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, timeout=90,
                            check=False)
    if result.returncode:
        raise ValueError("physical fixture Git failure: " + result.stderr[:700])
    return result.stdout.strip()


def commit(repo: Path, path: str, message: str) -> str:
    git(repo, "add", path)
    git(repo, "-c", "user.name=CORA negative oracle",
        "-c", "user.email=mutant@example.invalid",
        "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD")


class FinalExperimentalClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").exists():
            raise unittest.SkipTest("original Git full checkout required")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.contract = final.contract_at(ROOT, cls.sha)

    def test_01_30_nodes_all_external_noncompensatory(self):
        doc = self.contract
        self.assertEqual(len(doc["nodes"]), 30)
        self.assertEqual(len(doc["source"]), 15)
        self.assertEqual(len(doc["external"]), 7)
        self.assertEqual(len(doc["edges"]), 8)
        self.assertEqual(doc["edges"]["G_FINAL_EXPERIMENTAL"],
                         ["G_FREEZE_SOURCE", "G_EXTERNAL_BEHAVIOR",
                          "G_EXTERNAL_GOVERNANCE", "G_EXTERNAL_RELEASE"])
        self.assertEqual(doc["public_release"], "NOT_AUTHORIZED")
        self.assertEqual(doc["product_status"], "BLOCKED_EXTERNAL")

    def test_02_current_git_and_document_ontology(self):
        report = final.analyze(ROOT, self.sha)
        self.assertEqual(report["commit"], self.sha)
        self.assertEqual(report["counts"]["markdown"], 48)
        self.assertEqual(report["counts"]["cli"], 71)
        self.assertEqual(report["counts"]["declared_roles"],
                         report["counts"]["tracked"])
        self.assertEqual(report["behavior"]["execution"], "NOT_EXECUTED")
        self.assertEqual(report["host_enforcement"], "BLOCKED_EXTERNAL")
        self.assertFalse(report["release_authorized"])
        self.assertTrue(final.verify_report(ROOT, report))

    def test_03_physical_native_git_behavior_and_replay(self):
        report = final.analyze(ROOT, self.sha, run_behavior=True)
        self.assertEqual(report["behavior"]["fixture_repositories"], 2)
        self.assertTrue(report["behavior"]["cases"][0]["previous_sha_still_replayable"])
        self.assertEqual({x["status"] for x in report["behavior"]["cases"]},
                         {"MATCHED_NATIVE_GIT_REFERENCE_SCOPED"})
        self.assertTrue(final.verify_report(ROOT, report))
        self.assertEqual(report["behavior"]["maintained_target"],
                         "BLOCKED_EXTERNAL")
        self.assertFalse(report["release_authorized"])

    def test_04_full_2517_preregistered_semantic_masks(self):
        masks = final.preseed_masks()
        self.assertEqual(len(masks), 2517)
        self.assertEqual(len(set(masks)), 2517)
        one = final.stress(self.contract, cases=2517)
        two = final.stress(self.contract, cases=2517)
        self.assertEqual(one, two)
        self.assertEqual(one["distinct_finite_masks"], 2517)
        self.assertEqual(one["mismatches"], 0)
        self.assertEqual(one["unsafe_authorizations"], 0)
        self.assertEqual(one["status"], "PARTIAL_FINITE_MODEL")
        self.assertEqual(one["real_git_mutants"], 0)

    def test_05_faulty_model_cannot_self_recommend_release(self):
        with patch.object(final, "_model",
                          return_value=(True, True, True, True, True, "AUTHORIZE")):
            result = final.stress(self.contract, cases=2517)
        self.assertEqual(result["status"], "REFUTED")
        self.assertGreater(result["mismatches"], 2000)
        self.assertEqual(result["unsafe_authorizations"], 2517)
        self.assertFalse(result["release_authorized"])

    def test_06_Git_committed_temporal_falsehood_rejected(self):
        with tempfile.TemporaryDirectory(prefix="pr41-doc-mutant-") as temp:
            cloned = Path(temp) / "repo"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(cloned))
            git(cloned, "checkout", "-q", self.sha)
            path = cloned / "CHANGELOG.md"
            original = path.read_text("utf-8")
            path.write_text(original.replace(
                "PR40 engineering knowledge source convergence — merged source",
                "PR40 engineering knowledge source convergence — DRAFT, NOT MERGED"),
                encoding="utf-8")
            mutant = commit(cloned, "CHANGELOG.md",
                            "mutant: claim merged PR40 was unmerged")
            with self.assertRaisesRegex(ValueError, "temporal drift"):
                final.analyze(cloned, mutant)
            git(cloned, "reset", "--hard", "-q", self.sha)
            architecture = cloned / "docs/ARCHITECTURE.md"
            current_arch = architecture.read_text("utf-8")
            claim = "merged PR36–44" if "merged PR36–44" in current_arch else "merged PR36–40"
            self.assertIn(claim, current_arch)
            architecture.write_text(current_arch.replace(
                claim, "merged PR36–38"), encoding="utf-8")
            mutant = commit(cloned, "docs/ARCHITECTURE.md",
                            "mutant: outdated live architecture")
            with self.assertRaisesRegex(ValueError, "temporal drift"):
                final.analyze(cloned, mutant)
            git(cloned, "reset", "--hard", "-q", self.sha)
            release = cloned / "docs/RELEASE.md"
            release.write_text(release.read_text("utf-8").replace(
                "Existing GitHub release draft", "Published final release"),
                encoding="utf-8")
            mutant = commit(cloned, "docs/RELEASE.md",
                            "mutant: draft unverified as published release")
            with self.assertRaisesRegex(ValueError, "temporal drift"):
                final.analyze(cloned, mutant)

    def test_07_physical_external_governance_promotion_refuted(self):
        with tempfile.TemporaryDirectory(prefix="pr41-gov-mutant-") as temp:
            cloned = Path(temp) / "repo"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(cloned))
            git(cloned, "checkout", "-q", self.sha)
            path = cloned / final.CONTRACT
            changed = json.loads(path.read_text("utf-8"))
            next(x for x in changed["nodes"] if x["id"] ==
                 "E_H2_NONAUTHOR_REVIEW")["scope"] = "SOURCE"
            path.write_text(json.dumps(changed, indent=2) + "\n", "utf-8")
            mutant = commit(cloned, final.CONTRACT,
                            "mutant: external review self-signed")
            with self.assertRaisesRegex(ValueError, "scope"):
                final.contract_at(cloned, mutant)

    def test_08_unverified_host_and_forged_release_packet_refused(self):
        report = final.analyze(ROOT, self.sha)
        for field, value in (
            ("release_authorized", True),
            ("tag_authorized", True),
            ("host_enforcement", "ENFORCED"),
            ("product_status", "APPROVED"),
            ("ci_exact_head", "PASS"),
        ):
            fabricated = copy.deepcopy(report)
            fabricated[field] = value
            fabricated["digest"] = final.hashlib.sha256(
                final.canonical({k: v for k, v in fabricated.items()
                                 if k != "digest"})).hexdigest()
            with self.assertRaisesRegex(ValueError, "does not replay"):
                final.verify_report(ROOT, fabricated)

    def test_10_physical_Git_metric_and_freeze_contract_mutants(self):
        with tempfile.TemporaryDirectory(prefix="pr41-metric-mutant-") as temp:
            cloned = Path(temp) / "repo"
            git(ROOT, "clone", "--no-local", "-q", "--", str(ROOT), str(cloned))
            for field, scope in (
                ("markdown_registry_coverage_min", "metrics"),
                ("release_tag_commit_equal_final_main", "metrics"),
                ("forbidden", "release_freeze"),
            ):
                git(cloned, "reset", "--hard", "-q", self.sha)
                path = cloned / final.CONTRACT
                contract = json.loads(path.read_text("utf-8"))
                if field == "forbidden":
                    contract[scope][field].remove("AUTO_PUBLISH")
                else:
                    contract[scope][field] = False if field.startswith("release_tag") else 0
                path.write_text(json.dumps(contract, indent=2) + "\n", "utf-8")
                sha = commit(cloned, final.CONTRACT, "mutant: weaken " + field)
                with self.assertRaisesRegex(ValueError, "invariant drift"):
                    final.contract_at(cloned, sha)

    def test_09_seed_registry_tamper_does_not_redefine_families(self):
        altered = copy.deepcopy(self.contract)
        altered["metrics"]["semantic_cases_exact"] = 10000
        with self.assertRaisesRegex(ValueError, "model DoD not pinned"):
            final.stress(altered, cases=2517)
        self.assertEqual(final.FAULT_IDS[8], "GOV_PROTECTION_OFF")
        self.assertEqual(final.FAULT_IDS[15], "REL_MODEL_AS_APPROVAL")


if __name__ == "__main__":
    unittest.main()
