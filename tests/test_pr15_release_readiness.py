"""Independent PR-15 negative fixtures; synthetic, source-only, not GitHub authority."""
from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json
import subprocess
from tools.verify_release_readiness import candidate_receipt
from tools.verify_release_readiness import REQUIRED, inspect_source, main

ROOT=Path(__file__).resolve().parents[1]

class ReadinessTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.repo=Path(self.tmp.name)
        for rel in REQUIRED:
            dest=self.repo/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/rel,dest)
    def tearDown(self):self.tmp.cleanup()
    def swap(self,rel,old,new):
        p=self.repo/rel
        c=p.read_text(encoding="utf-8")
        self.assertIn(old,c)
        p.write_text(c.replace(old,new),encoding="utf-8")
    def deny(self,expected):
        r=inspect_source(self.repo)
        self.assertEqual(r["source_status"],"BLOCKED_SOURCE")
        self.assertIn(expected,r["source_errors"])
        self.assertEqual(r["authorization"],"NONE")
        self.assertFalse(r["release_authorized"])
    def test_readiness_is_never_self_authorized(self):
        a=inspect_source(self.repo)
        self.assertEqual(a,inspect_source(self.repo))
        self.assertEqual(a["source_status"],"PASS_SCOPED")
        self.assertEqual(a["release_status"],"BLOCKED_EXTERNAL")
        self.assertEqual(main(["--repo",str(self.repo),"--require-release-approval"]),3)
    def test_product_software_repository_closeout_is_not_release_authority(self):
        report = inspect_source(self.repo)
        closure = report["object_closeout"]
        self.assertEqual(closure["closure_status"], "SOURCE_CONTRACT_RECONCILED")
        self.assertEqual(closure["product"],
                         {"id": "cora", "state": "SOURCE_SCOPE_DEFINED"})
        self.assertEqual({item["id"] for item in closure["software"]},
                         {"cora-engine", "cora-release-verification"})
        self.assertEqual(closure["repository"]["state"], "SOURCE_CONTROLS_DECLARED")
        self.assertEqual(closure["host_protection"], "HOST_UNVERIFIED")
        self.assertEqual(closure["runtime_target"], "NOT_ATTESTED_BY_SOURCE")
        self.assertFalse(closure["enterprise_accepted"])
        self.assertEqual(closure["authorization"], "NONE")
        self.assertEqual(report["release_status"], "BLOCKED_EXTERNAL")
        self.assertFalse(report["release_authorized"])

    def test_six_live_source_owners_reject_removed_closeout_obligations(self):
        masks = (
            ("README.md", "Enterprise evaluation candidate",
             "Enterprise approved", "CLOSURE_BOUNDARY_DRIFT:README.md"),
            ("GOVERNANCE.md", "SOURCE_SCOPE_DEFINED", "PRODUCT_APPROVED",
             "CLOSURE_BOUNDARY_DRIFT:GOVERNANCE.md"),
            ("GOVERNANCE.md", "IMPLEMENTED_SOURCE_SCOPED", "UNIVERSAL_RUNTIME_PASS",
             "CLOSURE_BOUNDARY_DRIFT:GOVERNANCE.md"),
            ("GOVERNANCE.md", "CANDIDATE_VERIFICATION_ONLY", "SIGNED_RELEASE",
             "CLOSURE_BOUNDARY_DRIFT:GOVERNANCE.md"),
            ("GOVERNANCE.md", "SOURCE_CONTROLS_DECLARED", "HOST_AUTO_APPROVED",
             "CLOSURE_BOUNDARY_DRIFT:GOVERNANCE.md"),
            ("docs/DOD_RELEASE_READINESS.md", "I6 for effective host governance",
             "I5 already proves host governance",
             "CLOSURE_BOUNDARY_DRIFT:docs/DOD_RELEASE_READINESS.md"),
            ("docs/RELEASE.md", "release_status=BLOCKED_EXTERNAL",
             "release_status=APPROVED",
             "CLOSURE_BOUNDARY_DRIFT:docs/RELEASE.md"),
            ("docs/ARCHITECTURE.md", "Closure owner:", "Approved by the CLI:",
             "CLOSURE_BOUNDARY_DRIFT:docs/ARCHITECTURE.md"),
            ("SECURITY.md", "Repository visibility does not establish protected-branch controls",
             "Repository publicity certifies host protection",
             "CLOSURE_BOUNDARY_DRIFT:SECURITY.md"),
        )
        for rel, old, new, expected in masks:
            with self.subTest(path=rel, claim=old):
                original = (self.repo / rel).read_text("utf-8")
                self.assertIn(old, original)
                (self.repo / rel).write_text(original.replace(old, new, 1),
                                             encoding="utf-8")
                try:
                    self.deny(expected)
                    self.assertEqual(inspect_source(self.repo)["object_closeout"]
                                     ["closure_status"], "BLOCKED_SOURCE")
                finally:
                    (self.repo / rel).write_text(original, encoding="utf-8")
        report = inspect_source(self.repo)
        self.assertEqual(report["source_status"], "PASS_SCOPED")

    def test_title_counterexample(self):
        self.swap("README.md","Continuous Ontological Repository Assurance","Code Ontology Repo Audit")
        self.deny("PRODUCT_EXPANSION_MISSING")
    def test_version_counterexample(self):
        self.swap("src/cora/__init__.py","1.0.0a5","1.0.0a3")
        self.deny("PACKAGE_INIT_VERSION_DRIFT")
    def test_package_counterexample(self):
        self.swap("pyproject.toml",'name = "cora-audit"','name = "cora-unrelated"')
        self.deny("PACKAGE_METADATA_DRIFT")
    def test_stale_review_note_label_is_rejected(self):
        self.swap(".github/workflows/ci-release-candidate.yml",
                  "printf 'CORA %s (alpha) — REVIEW CANDIDATE ONLY",
                  "printf 'CORA 1.0.0a4 (alpha) — REVIEW CANDIDATE ONLY")
        self.deny("REVIEW_NOTE_VERSION_OR_SHA_DRIFT")

    def test_review_note_version_cannot_be_hardcoded_instead_of_package_metadata(self):
        self.swap(".github/workflows/ci-release-candidate.yml",
                  '"$CORA_VERSION" "$EXPECTED_SHA" > dist/RELEASE_NOTES_REVIEW.txt',
                  '"1.0.0a4" "$EXPECTED_SHA" > dist/RELEASE_NOTES_REVIEW.txt')
        self.deny("REVIEW_NOTE_VERSION_OR_SHA_DRIFT")


    def test_pr55_review_note_emitted_bytes_not_only_yaml(self):
        from tools.release_verify import verify_review_note
        commit = "a" * 40
        version = "1.0.0a5"
        original = chr(10).join((
            f"CORA {version} (alpha) — REVIEW CANDIDATE ONLY",
            f"Exact commit: {commit}",
            "Unsigned, unpublished; not approved for release.",
            "Required before publish: green final main CI; independently authenticated reviewer and release manager; protected main and required checks; independently verified artifact provenance, real pilot and rollback.",
            "",
        ))
        with tempfile.TemporaryDirectory() as td:
            note = Path(td) / "RELEASE_NOTES_REVIEW.txt"
            note.write_text(original, encoding="utf-8")
            self.assertTrue(verify_review_note(note, version, commit))
            mutants = (
                original.replace(version, "1.0.0a4", 1),
                original.replace(commit, "b" * 40, 1),
                original.replace("ONLY" + chr(10), "ONLY" + chr(92) + "n", 1),
                original + "Public release approved." + chr(10),
                original.replace("Unsigned, unpublished", "Signed, published", 1),
            )
            for i, mutant in enumerate(mutants):
                with self.subTest(mutant=i):
                    note.write_text(mutant, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        verify_review_note(note, version, commit)

    def test_review_note_double_escaped_newline_is_refuted(self):
        self.swap(".github/workflows/ci-release-candidate.yml",
                  "ONLY" + chr(92) + "nExact commit:",
                  "ONLY" + chr(92) * 2 + "nExact commit:")
        self.deny("REVIEW_NOTE_VERSION_OR_SHA_DRIFT")

    def test_review_note_exact_commit_check_cannot_be_bypassed(self):
        self.swap(".github/workflows/ci-release-candidate.yml",
                  'grep -Fx "Exact commit: $EXPECTED_SHA" dist/RELEASE_NOTES_REVIEW.txt',
                  'echo "Exact commit: $EXPECTED_SHA"')
        self.deny("REVIEW_NOTE_VERSION_OR_SHA_DRIFT")

    def test_dod_absent(self):
        (self.repo/"docs/DOD_RELEASE_READINESS.md").unlink()
        self.deny("MISSING_OR_SYMLINK:docs/DOD_RELEASE_READINESS.md")
    def test_policy_reviewer_removed(self):
        self.swap(".cora/continuous-policy.json",'"INDEPENDENT_SECURITY_REVIEWER"','"PRODUCT_OWNER"')
        self.deny("CONTINUOUS_POLICY_COVERAGE_DRIFT")
    def test_privileged_workflow_drift(self):
        self.swap(".github/workflows/ci-release-readiness.yml","  pull_request:","  pull_request_target:")
        self.deny("WORKFLOW_SOURCE_POLICY_DRIFT:.github/workflows/ci-release-readiness.yml")
    def test_unpinned_action_drift(self):
        self.swap(".github/workflows/ci-release-readiness.yml",
                  "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
                  "actions/checkout@v4")
        self.deny("WORKFLOW_SOURCE_POLICY_DRIFT:.github/workflows/ci-release-readiness.yml")
    def test_role_rewrite_drift(self):
        self.swap("cora.artifact-roles.json",
                  '"pattern": "tools/verify_release_readiness.py"',
                  '"pattern": "tools/unknown_verifier.py"')
        self.deny("RELEASE_VERIFIER_ROLE_MISSING")
    def test_unclassified_changelog_is_refuted(self):
        self.swap("cora.artifact-roles.json",
                  '"pattern": "CHANGELOG.md"',
                  '"pattern": "UNCLASSIFIED_NOT_CHANGELOG.md"')
        self.deny("CHANGELOG_ROLE_MISSING")
    def test_fingerprint_detects_valid_change(self):
        a=inspect_source(self.repo)
        p=self.repo/"CHANGELOG.md"
        p.write_text(p.read_text()+"\nMinor documentation-only amendment.\n")
        b=inspect_source(self.repo)
        self.assertEqual(b["source_status"],"PASS_SCOPED")
        self.assertNotEqual(a["input_sha256"]["CHANGELOG.md"],b["input_sha256"]["CHANGELOG.md"])
    def test_alpha_receipt_is_never_release_authority(self):
        if not (ROOT/".git").exists():
            self.skipTest("original Git checkout required")
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
        with tempfile.TemporaryDirectory() as d:
            loc = Path(d)
            wheel = loc/"cora_audit-1.0.0a5-py3-none-any.whl"
            sdist = loc/"cora_audit-1.0.0a5.tar.gz"
            wheel.write_bytes(b"fake wheel bytes: this test mocks original archive oracle")
            sdist.write_bytes(b"fake tar bytes: this test mocks original archive oracle")
            verified = {"distribution": "cora-audit", "version": "1.0.0a5",
                        "wheel_sha256": "a"*64, "sdist_sha256": "b"*64}
            proof = loc/"verification.json"
            proof.write_text(json.dumps(verified), encoding="utf-8")
            installation = loc/"external.json"
            installation.write_text(json.dumps({
                "schema":"cora-external-validation/1",
                "status":"SCOPED_FIXTURES_PASS",
                "distribution_forms":{"wheel":{}, "sdist":{}},
            }), encoding="utf-8")
            with patch("tools.verify_release_readiness.verify_release", return_value=verified):
                candidate = candidate_receipt(ROOT, sha, wheel, sdist, proof, installation)
                self.assertEqual(candidate["source_commit"], sha)
                self.assertEqual(candidate["authorization"], "NONE")
                self.assertEqual(candidate["external_gate"], "BLOCKED_EXTERNAL")
                self.assertFalse(candidate["publication_authorized"])
                self.assertEqual(candidate["signed_provenance"], "NOT_ATTESTED")
                self.assertEqual(candidate["github_release"], "NOT_PUBLISHED")
                # A forged candidate verification report fails closed even
                # when the immutable original-artifact oracle is mocked.
                proof.write_text(json.dumps(dict(verified, version="9.9.9")), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "recomputed binaries"):
                    candidate_receipt(ROOT, sha, wheel, sdist, proof, installation)
            with self.assertRaisesRegex(ValueError, "not checkout HEAD"):
                candidate_receipt(ROOT, "0"*40, wheel, sdist, proof, installation)

    def test_worktree_scope_not_misrepresented_as_signed_provenance(self):
        a=inspect_source(self.repo)
        self.assertIn("UNPINNED",a["source_scope"])
        self.assertIn("PROTECTED_MAIN_REQUIRED_CHECKS_NOT_ATTESTED",a["external_obligations"])

if __name__=="__main__":unittest.main()
