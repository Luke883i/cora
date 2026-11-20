"""PR32: real source-reticulum replay, external host readback and falsifiers."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cora.host_release import (
    _assert_valid, classify_host_snapshot, observe_github,
    original_git_dod, verify_expected_boundary, NODES, RELEASE_DOD,
)
from cora.reticulum import EXTERNAL, MODEL, BLOCKED

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40
OWNER = "Luke883i/cora"
TAG = "v1.0.0a4"


def fixture(protected=False, enforcement="off", checks=None):
    return {"name": "main", "commit": {"sha": COMMIT},
            "protected": protected, "protection": {
                "required_status_checks": {
                    "enforcement_level": enforcement,
                    "checks": checks or [], "contexts": []}}}


class ReleaseHostDoDTests(unittest.TestCase):
    def test_source_graph_is_complete_but_external_is_never_promoted(self):
        contract = json.loads((ROOT / RELEASE_DOD).read_text("utf-8"))
        paths = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()}
        assessment = _assert_valid(contract, paths)
        self.assertEqual(assessment["states"]["G_REPRO_SOURCE"], MODEL)
        self.assertEqual(assessment["states"]["G_GOVERNED_HOST"], EXTERNAL)
        self.assertEqual(assessment["states"]["G_RELEASE_ACCEPTANCE"], EXTERNAL)
        self.assertEqual(assessment["status"], EXTERNAL)
        self.assertEqual(assessment["authorization"], "NONE")
        self.assertEqual(len(contract["nodes"]), 16)

    def test_source_contract_reviewer_spoof_and_deleted_edge_fail(self):
        contract = json.loads((ROOT / RELEASE_DOD).read_text("utf-8"))
        paths = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()}
        hacked = copy.deepcopy(contract)
        next(x for x in hacked["nodes"] if x["id"] == "E_DISTINCT_REVIEWER")["scope"] = "SOURCE"
        with self.assertRaisesRegex(ValueError, "mandatory edge/scope"):
            _assert_valid(hacked, paths)
        hacked = copy.deepcopy(contract)
        next(x for x in hacked["nodes"] if x["id"] == "G_GOVERNED_HOST")["depends_on"].remove("E_DISTINCT_REVIEWER")
        with self.assertRaisesRegex(ValueError, "mandatory edge/scope"):
            _assert_valid(hacked, paths)
        hacked = copy.deepcopy(contract)
        next(x for x in hacked["nodes"] if x["id"] == "E_RELEASE_OWNER")["witness_paths"] = ["README.md"]
        with self.assertRaisesRegex(ValueError, "external reviewer or host"):
            _assert_valid(hacked, paths)
        missing = paths - {"tools/release_verify.py"}
        self.assertEqual(_assert_valid(contract, missing)["states"]["G_REPRO_SOURCE"], BLOCKED)

    def test_live_host_unprotected_evidence_does_not_authorize(self):
        r = classify_host_snapshot(fixture(), {"_observation_http": 403},
                                   {"_observation_http": 404},
                                   revision=COMMIT, repository=OWNER, tag=TAG)
        self.assertTrue(r["revision_is_main_head"])
        self.assertFalse(r["branch_protected"])
        self.assertFalse(r["required_checks_enforced_observed"])
        self.assertEqual(r["rulesets_status"], "API_FORBIDDEN")
        self.assertEqual(r["release_observation"], "TAG_RELEASE_NOT_PUBLISHED")
        self.assertIn("MAIN_NOT_PROTECTED_OBSERVED", r["blockers"])
        self.assertEqual(r["authorization"], "NONE")
        self.assertFalse(r["publication_authorized"])
        verify_expected_boundary(r)

    def test_real_checks_and_account_review_cannot_self_approve_release(self):
        reviewer_pr = {"user": {"login": "author"},
                       "head": {"sha": COMMIT}}
        reviews = [
            {"id": 3, "user": {"login": "author"}, "state": "APPROVED", "commit_id": COMMIT},
            {"id": 4, "user": {"login": "peer"}, "state": "APPROVED", "commit_id": COMMIT},
            {"id": 7, "user": {"login": "peer"}, "state": "DISMISSED", "commit_id": COMMIT},
            {"id": 9, "user": {"login": "peer2"}, "state": "APPROVED", "commit_id": "b" * 40},
            {"id": 12, "user": {"login": "peer3"}, "state": "APPROVED", "commit_id": COMMIT},
        ]
        r = classify_host_snapshot(
            fixture(True, "everyone", [{"context": "CI"}]),
            [], {"tag_name": TAG, "draft": False, "prerelease": True},
            revision=COMMIT, repository=OWNER, tag=TAG, pr=reviewer_pr,
            reviews=reviews)
        self.assertTrue(r["required_checks_enforced_observed"])
        self.assertEqual(r["distinct_non_author_head_approver_accounts"], ["peer3"])
        self.assertEqual(r["release_observation"], "PUBLISHED_REQUIRES_TAG_ASSET_AND_OWNER_ATTESTATION")
        self.assertEqual(r["external_gate"], "BLOCKED_EXTERNAL")
        self.assertFalse(r["publication_authorized"])
        self.assertIn("SIGNED_ARTIFACT_PROVENANCE_NOT_ATTESTED", r["blockers"])

    def test_pr_approval_attestation_rejects_unbounded_review_list(self):
        def mock(url, token):
            if "/branches/main" in url:
                return fixture()
            if "/rulesets" in url:
                return {"_observation_http": 403}
            if "/releases/tags/" in url:
                return {"_observation_http": 404}
            if "/pulls/31/reviews" in url:
                return [{}] * 100
            return {"user": {"login": "author"}, "head": {"sha": COMMIT}}
        with self.assertRaisesRegex(ValueError, "unavailable or truncated"):
            observe_github(OWNER, COMMIT, "private-token", pr_number=31, fetcher=mock)

    def test_live_read_only_token_never_in_json_and_malformed_fails_closed(self):
        targets = []
        def mock(url, token):
            targets.append(url)
            self.assertEqual(token, "private-token")
            return fixture() if "/branches/main" in url else (
                {"_observation_http": 403} if "/rulesets" in url else {"_observation_http": 404})
        report = observe_github(OWNER, COMMIT, "private-token", fetcher=mock)
        self.assertEqual(len(targets), 3)
        self.assertTrue(all(u.startswith("https://api.github.com/repos/" + OWNER) for u in targets))
        self.assertNotIn("private-token", json.dumps(report))
        with self.assertRaisesRegex(ValueError, "observation prerequisites"):
            observe_github(OWNER, COMMIT, "", fetcher=mock)
        forged = dict(report, authorization="APPROVE")
        with self.assertRaisesRegex(ValueError, "promoted"):
            verify_expected_boundary(forged)
        with self.assertRaisesRegex(ValueError, "main branch identity unknown"):
            classify_host_snapshot({}, [], {"_observation_http":404},
                                   revision=COMMIT, repository=OWNER, tag=TAG)

    def test_original_git_contract_replay_and_physical_mutant(self):
        if not (ROOT / ".git").exists():
            self.skipTest("no original Git checkout")
        sha, result = original_git_dod(ROOT)
        self.assertEqual(len(sha), 40)
        self.assertEqual(result["status"], EXTERNAL)
        # Minimal local Git fixture, avoiding clones and arbitrary target execution.
        contract = json.loads((ROOT / RELEASE_DOD).read_text("utf-8"))
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            subprocess.run(["git", "-C", str(folder), "init", "-q"], check=True)
            for x in contract["nodes"]:
                for item in x.get("witness_paths", []):
                    target = folder / item
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((ROOT / item).read_bytes())
            filename = folder / RELEASE_DOD
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(json.dumps(contract), encoding="utf-8")
            subprocess.run(["git","-C",str(folder),"add","."],check=True)
            subprocess.run(["git","-C",str(folder),"-c","user.name=CORA oracle",
                            "-c","user.email=test@example.invalid","commit","-qm","original source"],
                           check=True)
            self.assertEqual(original_git_dod(folder)[1]["status"], EXTERNAL)
            next(n for n in contract["nodes"] if n["id"] == "E_HOST_REQUIRED_CHECKS")["scope"] = "SOURCE"
            filename.write_text(json.dumps(contract), encoding="utf-8")
            subprocess.run(["git","-C",str(folder),"add","."],check=True)
            subprocess.run(["git","-C",str(folder),"-c","user.name=CORA oracle",
                            "-c","user.email=test@example.invalid","commit","-qm","physical forged host"],
                           check=True)
            with self.assertRaisesRegex(ValueError, "mandatory edge/scope"):
                original_git_dod(folder)


if __name__ == "__main__":
    unittest.main()
