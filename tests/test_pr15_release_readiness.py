"""Independent PR-15 negative fixtures; synthetic, source-only, not GitHub authority."""
from __future__ import annotations
import shutil
import tempfile
import unittest
from pathlib import Path
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
    def test_title_counterexample(self):
        self.swap("README.md","Continuous Ontological Repository Assurance","Code Ontology Repo Audit")
        self.deny("PRODUCT_EXPANSION_MISSING")
    def test_version_counterexample(self):
        self.swap("src/cora/__init__.py","1.0.0a4","1.0.0a3")
        self.deny("PACKAGE_INIT_VERSION_DRIFT")
    def test_package_counterexample(self):
        self.swap("pyproject.toml",'name = "cora-audit"','name = "cora-unrelated"')
        self.deny("PACKAGE_METADATA_DRIFT")
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
    def test_worktree_scope_not_misrepresented_as_signed_provenance(self):
        a=inspect_source(self.repo)
        self.assertIn("UNPINNED",a["source_scope"])
        self.assertIn("PROTECTED_MAIN_REQUIRED_CHECKS_NOT_ATTESTED",a["external_obligations"])

if __name__=="__main__":unittest.main()
