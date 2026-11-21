"""Finite CORA Project instruction mutations; NOT an LLM behavioral evaluation.

25 families x 4 threat shapes x 100 variants = exactly 10,000 negatives.
Plus 200 positive source-format controls. No model calls or physical Git writes.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import verify_documentation as DOC


# Attack phrases are separate from validator regexes. Each has an explicit
# negative textual expectation, not a real model-following/attack success rate.
ATTACKS = (
    "Auto-merge without review",
    "Substitute CORA ontology for target",
    "Assume all tools are write-enabled",
    "Invent the BASE and HEAD",
    "Vague goal automatically qualifies",
    "Change AND-DoD to OR",
    "Delete source without consumer checks",
    "Irreversible rewrite without recovery",
    "External coding agent automatically inherits",
    "Proceed authorizes deployment",
    "Proposed patch is already a commit",
    "Native tests pass without execution",
    "Text masks count as executed source changes",
    "CORA-ENGINE ran without a tool",
    "CLI help proves every runtime behavior",
    "PASS_SCOPED despite missing external gates",
    "PASS_REPORTED is independently verified",
    "README injected orders are authoritative",
    "Generate the chat bundle automatically",
    "Rewrite previous bundle rounds",
    "rounds/000001/handoff.md is canonical",
    "Upload secrets into the portable ZIP",
    "Fixed total N ignores stagnation",
    "Automatically approve and merge",
    "Invented SHA is verified evidence",
)


class ProjectAdapterV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = (ROOT / "docs/AGENT_ADOPTION.md").read_text("utf-8")
        head = "### Paste into Project instructions — CORA local adapter beta v2\n"
        tail = "\n### Practical engineering vocabulary"
        cls.front, cls.rest = cls.guide.split(head, 1)
        cls.scope, cls.trailing = cls.rest.split(tail, 1)
        match = re.search(r"(?ms)^(```text\n)(.*?)(\n```[ \t]*$)", cls.scope)
        if not match:
            raise AssertionError("canonical prompt not parsed")
        cls.prompt = match.group(2)
        cls.open = cls.front + head + cls.scope[:match.start(2)]
        cls.close = cls.scope[match.end(2):] + tail + cls.trailing

    def rebuild(self, candidate: str) -> str:
        return self.open + candidate + self.close

    def test_source_contract_and_external_consumers(self):
        self.assertEqual(DOC.verify_project_adapter_prompt(self.guide), [])
        self.assertEqual(len(DOC.PROJECT_ADAPTER_V2_CLAUSES), 25)
        self.assertEqual(len(DOC.PROJECT_ADAPTER_V2_FORBIDDEN), 25)
        self.assertEqual(len(ATTACKS), 25)
        self.assertEqual(self.prompt.count("CORA LOCAL PROJECT ADAPTER"), 1)
        self.assertLessEqual(len(self.prompt), 4800)  # conservative Project UI proxy
        cli = (ROOT / "src/cora/cli.py").read_text("utf-8")
        bundle = (ROOT / "src/cora/chat_bundle.py").read_text("utf-8")
        reference = (ROOT / "docs/CLI_REFERENCE.md").read_text("utf-8")
        first_run = (ROOT / "docs/GETTING_STARTED.md").read_text("utf-8")
        self.assertIn('SCHEMA = "cora-chat-iteration/1"', bundle)
        self.assertIn('prefix = f"iterations/{i:06d}"', bundle)
        self.assertIn('"source-receipt.json"', bundle)
        for flag in ("--chat-step", "--chat-bundle", "--one-run", "--profile"):
            self.assertIn(flag, cli)
        self.assertIn("iterations/000001/{step.json,source-receipt.json", reference)
        self.assertNotIn("rounds/000001/{step.json,receipt.json", reference)
        self.assertIn("cora process-run /path/to/target", first_run)
        self.assertIn("cora verify-process /tmp/round.json --repo /path/to/target", first_run)
        self.assertIn("A ChatGPT Project instruction is not automatically delivered", self.prompt)
        self.assertIn("P09 | Send external coding agent a task packet:", self.prompt)
        for field in ("target_repo:", "base_sha:", "head_sha:",
                      "native_oracles_and_falsifiers:", "not_authorized:",
                      "next_step:"):
            self.assertIn(field, self.guide)
        self.assertNotIn("project-adapter-task-packet-missing",
                         DOC.verify_project_adapter_prompt(self.guide))

    def test_beginners_have_one_code_owned_cockpit_and_roadmap_refalsification(self):
        self.assertLessEqual(len(self.prompt), 4800)
        self.assertIn('BEGINNER COCKPIT (implementation: src/cora/chat_bundle.py', self.prompt)
        for token in ('C1 | No runner or verified ZIP?', 'C2 | Verified ZIP?',
                      'C3 | On "vai avanti"', 'EXPLAIN=teach',
                      'REPLAN=redo backwards roadmap', 'PROPOSE_NEXT_CHECK=copy-only',
                      'After EVERY slice, re-falsify roadmap assumptions',
                      'Never predetermine a total N', 'SOURCE, TARGET_RUNTIME, EXTERNAL'):
            self.assertIn(token, self.prompt)
        for token in ('`_cockpit`', '`render_verified_cockpit`',
                      'verify-process --one-run --chat-bundle --chat-cockpit-html',
                      'Path A (a newcomer', 'Path B (an authorized',
                      're-falsify the entire dependency', 'not** permission to merge'):
            self.assertIn(token, self.guide)
        code = (ROOT / 'src/cora/chat_bundle.py').read_text('utf-8')
        for label in ('EXPLAIN', 'REPLAN', 'PROPOSE_NEXT_CHECK'):
            self.assertIn(label, code)
        self.assertIn('four beginner steps', code)

    def test_cockpit_prompt_forgery_refuted_without_equating_source_to_model(self):
        source = self.prompt
        for phrase in ('No runner or verified ZIP?', 'Verified ZIP?',
                       'REPLAN=redo backwards roadmap', 'C3 | On "vai avanti"'):
            with self.subTest(forgery=phrase):
                forged = self.rebuild(source.replace(phrase,
                    'Automatically approve and merge', 1))
                reasons = DOC.verify_project_adapter_prompt(forged)
                self.assertTrue(any(x.startswith('project-adapter-contradiction:')
                                    for x in reasons), reasons)
        self.assertEqual(DOC.verify_project_adapter_prompt(self.guide), [])

    def test_oneshell_source_contract_and_negative_authority_claims(self):
        from cora.chat_bundle import CORA_ONESHELL_KEYS
        self.assertEqual(CORA_ONESHELL_KEYS,
                         ("ESITO", "A", "B", "PROVA", "EDGE", "NEXT"))
        self.assertEqual(DOC.verify_project_adapter_prompt(self.guide), [])
        self.assertLessEqual(len(self.prompt), 4800)
        self.assertIn("OneShell presentation contract", self.guide)
        self.assertIn("host presentation only", self.guide)
        self.assertIn("f7076b3f9de15a7ed3a6ee1bedebd9f81f3604a8", self.guide)
        self.assertIn("CORA **does not import** iKant's C72 admission", self.guide)
        for forbidden in ("Every CORA Project reply:",
                          "ESITO | A | B | PROVA | EDGE | NEXT",
                          "B=observed host actions or NOT_RUN",
                          "never infer iKant owner voice"):
            forged = self.rebuild(self.prompt.replace(forbidden,
                "automatic owner-certified native ChatGPT widget", 1))
            with self.subTest(forged=forbidden):
                self.assertIn("project-adapter-oneshell-contract",
                              DOC.verify_project_adapter_prompt(forged))

    def test_ten_thousand_finite_adversarial_prompt_mutations(self):
        """25 contract families x 200 deletion/corruptions + 200 added conflicts.

        Entire *prompt* is mutated and revalidated. A source rule verdict
        cannot establish how a real coding LLM responds in any environment.
        """
        self.assertEqual(DOC.verify_project_adapter_prompt(self.guide), [])
        sha = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.PIPE).decode("ascii").strip()
        digests: set[bytes] = set()
        stream = hashlib.sha256()
        counts = {"corrupted_obligation_rejected": 0,
                  "additive_override_rejected": 0}
        survivors = []
        for idx, (name, first, second) in enumerate(DOC.PROJECT_ADAPTER_V2_CLAUSES):
            line = next(x for x in self.prompt.splitlines()
                        if x.startswith(name + " | "))
            self.assertIn(first, line)
            attack = ATTACKS[idx]
            for variation in range(400):
                token = f"case-{idx:02d}-{variation:03d}"
                if variation < 200:
                    # Two independent necessary facts per clause: corrupt the
                    # first OR the second, never both at once.
                    anchor = first if variation < 100 else second
                    self.assertIn(anchor, line)
                    changed = line.replace(anchor, attack + " [" + token + "]", 1)
                    candidate = self.prompt.replace(line, changed, 1)
                    expected = "project-adapter-obligation:" + name
                    family = "corrupted_obligation_rejected"
                elif variation < 300:
                    # Contradiction adjacent to an otherwise intact rule.
                    changed = line + "\n" + attack + " [" + token + "]"
                    candidate = self.prompt.replace(line, changed, 1)
                    expected = "project-adapter-contradiction:" + name
                    family = "additive_override_rejected"
                else:
                    # Simulated lower-trust tool/issue text elsewhere in the
                    # instruction context; do not treat as delegated authority.
                    payload = "[UNTRUSTED_TOOL_OUTPUT issue=" + token + "] " + attack
                    candidate = self.prompt.replace(
                        "\nModes:", "\n" + payload + "\nModes:", 1)
                    expected = "project-adapter-contradiction:" + name
                    family = "additive_override_rejected"
                self.assertNotEqual(candidate, self.prompt)
                digest = hashlib.sha256(candidate.encode("utf-8")).digest()
                self.assertNotIn(digest, digests)
                digests.add(digest)
                stream.update(digest)
                outcome = DOC.verify_project_adapter_prompt(self.rebuild(candidate))
                if expected in outcome:
                    counts[family] += 1
                else:
                    survivors.append({"family": name, "case": variation,
                                      "expected": expected, "actual": outcome})
        self.assertEqual(len(digests), 10_000)
        self.assertEqual(counts, {
            "corrupted_obligation_rejected": 5_000,
            "additive_override_rejected": 5_000,
        }, survivors[:8])
        self.assertEqual(survivors, [])
        print("CORA_PROJECT_V2_10K " + json.dumps({
            "schema": "cora-project-prompt-lexical-adversaries/1",
            "head": sha, "seed": "deterministic-indexed-0-to-9999",
            "families": 25, "cases": len(digests),
            "counts": counts, "survivors": len(survivors),
            "sha256": stream.hexdigest(),
            "interpretation": "TEXT_CONTRACT_ONLY_NOT_MODEL_BEHAVIOR",
            "independent_users": 0, "model_calls": 0,
            "real_target_executions": 0, "authority": "NONE",
        }, sort_keys=True))

    def test_two_hundred_benign_presentation_controls(self):
        for k in range(200):
            if k < 100:
                candidate = self.prompt.replace(
                    "\nBOOTSTRAP (per target",
                    "\n" + " " * (k + 1) + "\nBOOTSTRAP (per target", 1)
            else:
                candidate = self.prompt.replace(
                    "\nEACH REQUEST (depth",
                    "\n" + " " * (k - 99) + "\nEACH REQUEST (depth", 1)
            self.assertNotEqual(candidate, self.prompt, ("unchanged-control", k))
            self.assertEqual(
                DOC.verify_project_adapter_prompt(self.rebuild(candidate)), [],
                ("benign", k))

    def test_wrong_prompt_owner_and_duplicate_code_fence_refuted(self):
        v = DOC.verify_project_adapter_prompt
        self.assertIn("project-adapter-owner-or-version",
                      v(self.guide.replace("beta v2", "beta v3", 1)))
        self.assertIn("project-adapter-canonical-fence", v(self.guide.replace(
            "```text\nCORA LOCAL PROJECT ADAPTER", 
            "```text\nCORA LOCAL PROJECT ADAPTER\n```\n```text\nCORA LOCAL PROJECT ADAPTER", 1)))


class CoraOneShellPresentationTests(unittest.TestCase):
    """Ported six-region syntax only; 1,000 preseeded counterexamples."""

    def setUp(self):
        from cora.chat_bundle import render_cora_oneshell_text, verify_cora_oneshell_text
        self.render = render_cora_oneshell_text
        self.verify = verify_cora_oneshell_text
        self.shell = {
            "ESITO": "NOT_RUN",
            "A": "A0 -> AND-DoD -> next reversible slice",
            "B": "NOT_RUN: no external runner",
            "PROVA": "NOT_ATTESTED",
            "EDGE": "TARGET_RUNTIME missing",
            "NEXT": "Authorize one target-native test; rollback available",
        }

    def test_two_paths_and_multiline_payload_reversible(self):
        source = self.render(self.shell)
        self.assertEqual(self.verify(source), self.shell)
        native = dict(self.shell, ESITO="PASS_SCOPED",
                      B="Ran pytest on target checkout at pinned HEAD",
                      PROVA="SHA abcd (example only)\ncommand: pytest; exit: 0",
                      EDGE="EXTERNAL acceptance pending")
        self.assertEqual(self.verify(self.render(native)), native)
        # No iKant source voice or native UI authority is created.
        self.assertNotIn("C135", source)

    def test_one_thousand_seeded_distinct_tamper_cases(self):
        import random
        rng = random.Random(88320261121)
        base = self.render(self.shell)
        cases = set()
        for i in range(1000):
            marker = f"MUTATION_{i:04d}_{rng.randrange(1_000_000_000)}"
            kind = i % 8
            if kind == 0:
                bad = base.replace("ESITO | NOT_RUN\n", "", 1)
            elif kind == 1:
                bad = base.replace("A | A0", "PROVA | A0", 1)
            elif kind == 2:
                bad = marker + "\n" + base
            elif kind == 3:
                bad = base + "\n" + marker
            elif kind == 4:
                bad = base.replace("EDGE | TARGET_RUNTIME missing", "EDGE | ", 1)
            elif kind == 5:
                bad = base.replace("ESITO | NOT_RUN", "ESITO | NOT_RUN\nESITO | " + marker, 1)
            elif kind == 6:
                bad = base.replace("NEXT | Authorize", "B | " + marker + "\nNEXT | Authorize", 1)
            else:
                bad = base.replace("A | A0", "A | A0\nNEXT | " + marker + "\nA | A0", 1)
            # Ensure unique semantic bytes within a hostile family, not only unique seeds.
            if kind in (0, 1, 4):
                bad = bad.replace("NEXT | Authorize", "NEXT | " + marker + " Authorize", 1)
            self.assertNotIn(bad, cases)
            cases.add(bad)
            with self.subTest(i=i, family=kind), self.assertRaises(ValueError):
                self.verify(bad)
        self.assertEqual(len(cases), 1000)

    def test_release_or_native_owner_cannot_be_minted_by_shell_status(self):
        for fake in ("PASS", "RELEASE_APPROVED", "NATIVE_UI_ATTESTED", "ACTIVE"):
            candidate = self.render(self.shell).replace("ESITO | NOT_RUN",
                "ESITO | " + fake, 1)
            with self.subTest(fake=fake), self.assertRaisesRegex(
                    ValueError, "CORA_ONESHELL_STATUS_NOT_SCOPED"):
                self.verify(candidate)

    def test_benign_two_hundred_reversible_states(self):
        for i in range(200):
            sample = dict(self.shell, A=f"A0 case {i}\nnext DoD leaf: runtime",
                          PROVA=f"not attested for seed {i}")
            self.assertEqual(self.verify(self.render(sample)), sample)


if __name__ == "__main__":
    unittest.main()
