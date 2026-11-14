"""Offline Git and PR70-shape falsifiers; no claim of native CORA execution."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cora import hforge_profile as h


def git(repo: Path, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout.strip()


def receipt(base, head):
    cases = [f"help:command-{i:03d}" for i in range(71)] + sorted(h.NATIVE)
    zero = hashlib.sha256(b"").hexdigest()
    okay = hashlib.sha256(b"ok\n").hexdigest()
    obs = {"exit_code": 0, "stdout_sha256": okay, "stdout_bytes": 3,
           "stderr_sha256": zero, "stderr_bytes": 0}
    return {"schema": h.OP_SCHEMA, "base": base, "head": head,
            "denominator": 77, "observed": 77, "passed": 77, "failed": [],
            "rows": [{"case": c, "status": "PASS", "baseline": copy.deepcopy(obs),
                      "candidate": copy.deepcopy(obs)} for c in cases],
            "status": "PASS_EXHAUSTIVE_FINITE_OBSERVATIONS", "authorization": "NONE",
            "product_global_status": "BLOCKED_EXTERNAL"}


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "hforge@fixture.invalid")
        git(self.repo, "config", "user.name", "H-FORGE test")
        (self.repo / "gold.py").write_text("print('product entrypoint')\n")
        (self.repo / "legacy.py").write_text("LEGACY = 'obsolete redundant code'\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "legacy.py").unlink()
        (self.repo / "entry.py").write_bytes((self.repo / "gold.py").read_bytes())
        (self.repo / "gold.py").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "candidate: remove legacy and rename gold")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def test_original_git_tree_true_contraction_and_rename_not_double_counted(self):
        d = h.compare_trees(self.repo, self.base, self.head)
        self.assertEqual(d["delta_files"], -1)
        self.assertEqual(d["delta_bytes"], -len("LEGACY = 'obsolete redundant code'\n"))
        self.assertEqual(d["scope"], "ALL_TRACKED_GIT_BLOBS")

    def test_non_ancestral_or_invalid_ref_rejected(self):
        with self.assertRaisesRegex(ValueError, "different"):
            h.compare_trees(self.repo, self.base, self.base)
        with self.assertRaisesRegex(ValueError, "full commit"):
            h.tree_metrics(self.repo, "HEAD")
        with self.assertRaisesRegex(ValueError, "ancestor"):
            h.compare_trees(self.repo, self.head, self.base)

    def test_complete_claim_shape_is_not_runtime_attestation(self):
        r = h.assess(self.repo, receipt(self.base, self.head), base=self.base,
                     head=self.head, contraction_claim=True)
        self.assertEqual(r["gates"]["P1"], "PASS_RECEIPT_SHAPE_NOT_RUNTIME_PROOF")
        self.assertEqual(r["gates"]["P3"], "PASS_MEASURED_CONTRACTION")
        self.assertEqual(r["gates"]["P2"], "HOLD")
        self.assertEqual(r["gates"]["P5"], "HOLD")
        self.assertEqual(r["status"], "DEBT_BLOCKED_GLOBAL")
        self.assertFalse(r["release_authorized"])
        self.assertEqual(r["authorization"], "NONE")

    def test_replay_must_use_original_upstream_runner_not_synthetic_git_fixture(self):
        # When moved into CORA the import may succeed; this synthetic fixture
        # still lacks PR70's original committed 77-command atlas and must fail.
        with self.assertRaises((ValueError, KeyError, FileNotFoundError)):
            h.assess(self.repo, receipt(self.base, self.head), base=self.base,
                     head=self.head, replay_native=True)

    def test_no_contraction_claim_when_files_added(self):
        (self.repo / "scaffold.py").write_text("more = 'NEW SCAFFOLD'\n")
        (self.repo / "more_scaffold.py").write_text("additional = True\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "adversarial positive scaffolding")
        altered = git(self.repo, "rev-parse", "HEAD")
        r = h.assess(self.repo, base=self.base, head=altered, contraction_claim=True)
        self.assertEqual(r["gates"]["P3"], "REFUTED_OR_UNVERIFIED_CONTRACTION")

    def test_forged_receipt_falsifiers(self):
        base = receipt(self.base, self.head)
        modifications = (
            lambda r: r["rows"].pop(),
            lambda r: r["rows"][0].update(case=r["rows"][1]["case"]),
            lambda r: r.update(passed=76),
            lambda r: r.update(head="a" * 40),
            lambda r: r["rows"][0]["baseline"].update(exit_code=True),
            lambda r: r["rows"][0]["baseline"].update(stdout_sha256="tampered"),
            lambda r: r["rows"][0].update(status="UNKNOWN"),
            lambda r: r.update(product_global_status="PASS"),
            lambda r: r.update(authorization="ALLOW_MERGE"),
            lambda r: r.update(denominator=76),
            lambda r: r["rows"][0]["candidate"].pop("stderr_bytes"),
        )
        for i, update in enumerate(modifications):
            with self.subTest(mutant=i):
                r = copy.deepcopy(base)
                update(r)
                with self.assertRaises(ValueError):
                    h.operational_claim(r, self.base, self.head)

    def test_forged_pass_with_different_bytes_rejected(self):
        r = receipt(self.base, self.head)
        r["rows"][0]["candidate"]["stdout_bytes"] = 5
        with self.assertRaisesRegex(ValueError, "per-case PASS"):
            h.operational_claim(r, self.base, self.head)

    def test_one_run_sidecar_binds_exact_git_and_never_promotes(self):
        case = receipt(self.base, self.head)
        result = h.assess(self.repo, case, base=self.base, head=self.head)
        tree = git(self.repo, "rev-parse", self.head + "^{tree}")
        integrated = {"schema": "cora-integrated-one-run/2", "commit": self.head,
                      "tree": tree, "authority": "NONE", "authorization": "NONE",
                      "release_authorized": False, "source_status": "DEBT_BLOCKED",
                      "product_status": "BLOCKED_EXTERNAL"}
        sidecar = h.one_run_reference(self.repo, result, integrated, case)
        self.assertEqual(sidecar["commit"], self.head)
        self.assertEqual(sidecar["status"], "SIDECAR_REFERENCE_NOT_NATIVE_ONERUN_VERIFICATION")
        self.assertFalse(sidecar["release_authorized"])
        for field, bad in (("tree", "a"*40), ("commit", self.base),
                           ("source_status", "PASS"), ("authorization", "ALLOW_MERGE"),
                           ("product_status", "PASS")):
            with self.subTest(field=field):
                altered = copy.deepcopy(integrated)
                altered[field] = bad
                with self.assertRaises(ValueError):
                    h.one_run_reference(self.repo, result, altered, case)

    def test_true_git_replay_vs_rehashed_forgery(self):
        case = receipt(self.base, self.head)
        report = h.assess(self.repo, case, base=self.base, head=self.head)
        self.assertTrue(h.verify_assessment(self.repo, report, case))
        forged = copy.deepcopy(report)
        forged["git_structure"]["delta_bytes"] = -999999
        forged["digest"] = h._canonical_digest(forged)
        with self.assertRaisesRegex(ValueError, "does not replay"):
            h.verify_assessment(self.repo, forged, case)

    def test_strict_result_fail_for_unauthorized_promotion(self):
        case = receipt(self.base, self.head)
        report = h.assess(self.repo, case, base=self.base, head=self.head)
        promoted = copy.deepcopy(report)
        promoted["status"] = "PASS_GLOBAL"
        with self.assertRaisesRegex(ValueError, "does not replay"):
            h.verify_assessment(self.repo, promoted, case)

    def test_relabelled_false_pass_rejected(self):
        r = receipt(self.base, self.head)
        r["rows"][2]["status"] = "REFUTED"
        with self.assertRaisesRegex(ValueError, "per-case PASS"):
            h.operational_claim(r, self.base, self.head)

    def test_untrusted_gitlink_blocks_tree_closure(self):
        # Git records a gitlink even if its remote content is unreachable.
        fake = "f" * 40
        git(self.repo, "update-index", "--add", "--cacheinfo", "160000," + fake + ",vendor/plugin")
        git(self.repo, "commit", "-qm", "record unresolvable gitlink")
        with_link = git(self.repo, "rev-parse", "HEAD")
        m = h.tree_metrics(self.repo, with_link)
        self.assertEqual(m["gitlinks_unresolved"], 1)
        r = h.assess(self.repo, base=self.base, head=with_link)
        self.assertEqual(r["gates"]["P3"], "HOLD_GITLINKS")

    def test_symlink_is_counted_not_followed(self):
        import os
        os.symlink("/etc/passwd", self.repo / "outside")
        git(self.repo, "add", "outside")
        git(self.repo, "commit", "-qm", "adversarial link to outside repo")
        sha = git(self.repo, "rev-parse", "HEAD")
        measured = h.tree_metrics(self.repo, sha)
        self.assertEqual(measured["symlinks"], 1)
        self.assertLess(measured["tracked_bytes"], 10000)

    def test_composite_mutant_survivors_require_legitimate_refuted_oracle(self):
        """Primary positive-only oracle misses 7 compensating composites.

        A second *valid* REFUTED receipt kills all seven; six occur in the
        first million seeded source mutants, so no inflated killed count.
        """
        good = receipt(self.base, self.head)
        refuted = copy.deepcopy(good)
        row = refuted["rows"][0]
        row["candidate"]["stdout_sha256"] = hashlib.sha256(b"changed\n").hexdigest()
        row["candidate"]["stdout_bytes"] = len(b"changed\n")
        row["status"] = "REFUTED"
        refuted["passed"] = 76
        refuted["failed"] = [row["case"]]
        refuted["status"] = "REFUTED_FINITE_OBSERVATIONS"
        self.assertEqual(h.operational_claim(refuted, self.base, self.head)["scoped_status"],
                         "REFUTED_FINITE_OBSERVATIONS")
        src = (Path(__file__).resolve().parents[1] / "src/cora/hforge_profile.py").read_text()
        function = src[src.index("def operational_claim("):src.index("\ndef assess(")]
        sites = (
            ('left["exit_code"] == right["exit_code"] == 0',
             'left["exit_code"] != right["exit_code"] == 0'),
            ('left["stdout_bytes"] > 0', 'left["stdout_bytes"] <= 0'),
            ('right["stdout_bytes"] > 0', 'right["stdout_bytes"] <= 0'),
        )
        comparison = ('if row["status"] != expected_status:',
                      'if row["status"] == expected_status:')
        self.assertEqual(function.count(comparison[0]), 1)
        for old, _ in sites:
            self.assertEqual(function.count(old), 1)
        with tempfile.TemporaryDirectory(prefix="hforge-refuted-oracle-") as tmp:
            for subset in range(1, 8):
                with self.subTest(mask=subset):
                    mutated = function.replace(*comparison)
                    for j, (old, new) in enumerate(sites):
                        if subset & (1 << j):
                            mutated = mutated.replace(old, new, 1)
                    p = Path(tmp) / "source_mutant.py"
                    p.write_text(mutated, encoding="utf-8")
                    ns = {"hashlib": hashlib, "re": h.re, "OP_SCHEMA": h.OP_SCHEMA,
                          "NATIVE": h.NATIVE, "_canonical_digest": h._canonical_digest}
                    exec(compile(p.read_bytes(), str(p), "exec"), ns)
                    # Such a composite escapes the positive-only mutation oracle.
                    self.assertIsInstance(ns["operational_claim"](good, self.base, self.head), dict)
                    # A legitimate refuted outcome is the independent second oracle.
                    with self.assertRaises(ValueError):
                        ns["operational_claim"](refuted, self.base, self.head)

    def test_capability_atlas_covers_all_eight_new_surfaces(self):
        """Prevent new unregistered modules/tests silently breaking source CI."""
        from tools.verify_capability_atlas import check
        root = Path(__file__).resolve().parents[1]
        report = check(root, "HEAD")
        self.assertEqual(report["source_status"], "PASS_SCOPED_SOURCE")
        self.assertGreaterEqual(report["surfaces"]["modules"], 64)
        self.assertGreaterEqual(report["surfaces"]["test_modules"], 59)
        self.assertGreaterEqual(report["surfaces"]["internal_dod"], 20)
        self.assertGreaterEqual(report["surfaces"]["internal_profiles"], 3)

if __name__ == '__main__':
    unittest.main()
