"""PR31 original-Git maturity graph, HTML and forgery regression tests."""
from __future__ import annotations
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from cora.cli import main
from cora.maturity_atlas import build_atlas, render_html, verify_atlas
from cora.reticulum import EXTERNAL, MODEL, assess_cut
from cora.synergy import unified_assurance

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   stderr=subprocess.PIPE).decode().strip()


class MaturityAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / ".git").is_dir():
            raise unittest.SkipTest("full original Git checkout required")
        cls.sha = git(ROOT, "rev-parse", "HEAD")
        cls.base = git(ROOT, "rev-parse", "HEAD^")
        cls.unified = unified_assurance(ROOT, cls.sha, base=cls.base)
        cls.atlas = build_atlas(ROOT, cls.unified)

    def test_retrograde_six_gates_noncompensatory(self):
        a = self.atlas
        self.assertEqual(a["commit"], self.sha)
        self.assertEqual(a["identity"]["entrypoint"], "cora.cli:main")
        self.assertEqual(a["identity"]["software"],
                         ["cora-engine", "cora-release-verification"])
        self.assertEqual(len(a["maturity"]["gates"]), 6)
        self.assertEqual(len(a["maturity"]["nodes"]), 30)
        self.assertEqual(a["maturity"]["assessment"]["status"], EXTERNAL)
        self.assertEqual(a["maturity"]["gate_states"]["G2_SOURCE_INTEGRITY"], MODEL)
        for gate in a["maturity"]["gates"]:
            if gate != "G2_SOURCE_INTEGRITY":
                self.assertEqual(a["maturity"]["gate_states"][gate], EXTERNAL)
        self.assertFalse(a["maturity"]["missing_source_obligations"])
        self.assertEqual(a["authorization"], "NONE")

    def test_every_declared_command_bound_to_same_git_and_source_witness(self):
        a = self.atlas
        self.assertEqual(len(a["capabilities"]), 71)
        self.assertEqual(len(a["capability_families"]), 8)
        self.assertEqual(len(a["procedures"]), 14)
        self.assertEqual(len({x["command"] for x in a["capabilities"]}), 71)
        self.assertTrue(all(x["proof"] == "DECLARED_SOURCE_AND_TEST_PATH_NOT_EXECUTED"
                            for x in a["capabilities"]))
        self.assertEqual(a["lineage"]["independent_corroborations"], 0)
        self.assertTrue(a["lineage"]["shared_git_origins"])

    def test_html_navigation_and_benign_markup_cannot_inject(self):
        page = render_html(self.atlas)
        self.assertIn("CORA ATLAS | SOURCE-BOUNDED", page)
        self.assertIn('id="find"', page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn("connect-src 'none'", page)
        self.assertIn("71 comandi dichiarati", page)
        self.assertIn(self.sha, page)
        for row in self.atlas["capabilities"]:
            self.assertIn("<code>cora " + row["command"] + "</code>", page)
        hostile = copy.deepcopy(self.atlas)
        hostile["capabilities"][0]["command"] = '<strong>INJECTED</strong>'
        hostile["capability_families"][0]["label"] = '<aside>INJECTED</aside>'
        escaped = render_html(hostile)
        self.assertNotIn('<strong>INJECTED</strong>', escaped)
        self.assertNotIn('<aside>INJECTED</aside>', escaped)
        self.assertIn("&lt;strong&gt;", escaped)

    def test_replay_rejects_shared_origin_promotion_and_modified_html(self):
        a = copy.deepcopy(self.atlas)
        a["lineage"]["independent_corroborations"] = 71
        with self.assertRaisesRegex(ValueError, "original Git source"):
            verify_atlas(ROOT, self.unified, data=a)
        page = render_html(self.atlas)
        self.assertTrue(verify_atlas(ROOT, self.unified, data=self.atlas, page=page))
        with self.assertRaisesRegex(ValueError, "HTML differs"):
            verify_atlas(ROOT, self.unified, page=page.replace("Source candidate", "APPROVED"))

    def test_external_evidence_cannot_be_self_supplied(self):
        fake = {"E_PROTECTED_MAIN": MODEL, "E_REVIEW_IDENTITY": MODEL}
        observed = assess_cut(self.atlas["maturity"]["nodes"], "G_MATURITY", fake)
        self.assertEqual(observed["status"], EXTERNAL)
        self.assertEqual(observed["states"]["E_PROTECTED_MAIN"], EXTERNAL)
        self.assertEqual(observed["states"]["E_REVIEW_IDENTITY"], EXTERNAL)
        self.assertEqual(observed["authorization"], "NONE")

    def test_git_committed_external_review_reclassification_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            clone = Path(d) / "cora"
            subprocess.run(["git", "clone", "-q", "--no-local", str(ROOT), str(clone)], check=True)
            git(clone, "checkout", "-q", self.sha)
            git(clone, "config", "user.name", "CORA negative fixture")
            git(clone, "config", "user.email", "test@example.invalid")
            path = clone / ".cora/contracts/dod/maturity-dod.json"
            data = json.loads(path.read_text("utf-8"))
            for node in data["nodes"]:
                if node["id"] == "E_REVIEW_IDENTITY":
                    node["scope"] = "SOURCE"
                    node["witness_paths"] = ["README.md"]
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            git(clone, "add", ".cora/contracts/dod/maturity-dod.json")
            git(clone, "commit", "-qm", "mutant: forged reviewer from source")
            fake = copy.deepcopy(self.unified)
            fake["commit"] = git(clone, "rev-parse", "HEAD")
            with self.assertRaisesRegex(ValueError, "external assurance leaf"):
                build_atlas(clone, fake)
            # Independent second committed mutant removes G2 lineage and its leaf.
            git(clone, "checkout", "-q", self.sha)
            data = json.loads(path.read_text("utf-8"))
            data["nodes"] = [n for n in data["nodes"] if n["id"] != "L_LINEAGE"]
            next(n for n in data["nodes"] if n["id"] == "G2_SOURCE_INTEGRITY")["depends_on"].remove("L_LINEAGE")
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            git(clone, "add", ".cora/contracts/dod/maturity-dod.json")
            git(clone, "commit", "-qm", "mutant: erase G2 lineage cut")
            fake["commit"] = git(clone, "rev-parse", "HEAD")
            with self.assertRaisesRegex(ValueError, "mandatory maturity"):
                build_atlas(clone, fake)

    def test_cli_generates_and_replays_human_and_ai_views(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            report, atlas, page, request = (out / x for x in
                ("source.json", "atlas.json", "index.html", "ai.json"))
            call = ["method-synthesize", str(ROOT), "--synergic",
                    "--revision", self.sha, "--base-sha", self.base,
                    "--output", str(report), "--atlas-json", str(atlas),
                    "--atlas-html", str(page), "--ai-request-output", str(request)]
            self.assertEqual(main(call), 0)
            self.assertEqual(json.loads(atlas.read_text("utf-8")), self.atlas)
            self.assertIn("CORA ATLAS", page.read_text("utf-8"))
            self.assertFalse(json.loads(request.read_text("utf-8"))["provider_invoked"])
            replay = ["verify-method-synthesis", str(report), "--repo", str(ROOT),
                      "--synergic", "--atlas-json", str(atlas), "--atlas-html", str(page)]
            self.assertEqual(main(replay), 0)
            page.write_text(page.read_text("utf-8").replace("Source candidate", "APPROVED"), encoding="utf-8")
            self.assertEqual(main(replay), 3)


if __name__ == "__main__":
    unittest.main()
