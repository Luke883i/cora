# CORA PR-20 — canonical convergent assurance

## Product/software/repository intent

The single **CORA** product continues to comprise `cora-engine` and `cora-release-verification`; this change does not create another agent or trust authority. Existing agent and Gold models share `reticulum.ordered_cut`, but retain their prior fixed vocabulary and output formats. The new profile `cora.convergence-dod.json` distinguishes source implementation from full real-world R1–R4 obligations and governed acceptance.

## Exact Git and context workflow

Run `cora convergence-plan --goal G_R1_R4_COMPLETE` for source/external cuts. Run `cora dev-premerge TARGET --base BASE_SHA --head PR_SHA --contextual --intent "The scoped change and its acceptance criteria" --convergence-contract PROFILE --output /tmp/cora-context.json`; replay with `cora verify-contextual-gate /tmp/cora-context.json --repo TARGET --intent "The scoped change and its acceptance criteria" --convergence-contract PROFILE`. After integration, run `cora dev-postmerge TARGET --previous REAL_PREMERGE_MAIN --head ACTUAL_MERGE_MAIN --contextual --intent "The scoped change and its acceptance criteria" --convergence-contract PROFILE --output /tmp/post.json`. The legacy commands without `--contextual` remain unchanged. The contextual gate is DEBT_BLOCKED without an explicit change intent; replay requires the same intent. See [agent adoption](AGENT_ADOPTION.md) for the complete workflow.

The contextual path uses `continuous.evaluate` (BASE-committed policy, exact commits and Git change list), `committed_ontology` (explicit product and software roots), `graph_from_commit` (static Python import **candidates**) and `gold_effects.audit_workflow` (potential CI effects). Missing ontology or unresolved source graph is **DEBT_BLOCKED**. Multiple declared owners and uncertain dynamic/relative imports remain review targets, never inferred runtime callpaths. The profile is PR-editable and must not authenticate its own acceptance.

## Selective witness invalidation, not inferred proof

Supply `--witnesses witnesses.json` with a JSON array, for example:

```json
[
  {"id":"W1","dependencies":["src/pkg/a.py"],"revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","scope":"SOURCE"},
  {"id":"W2","dependencies":["src/pkg/b.py"],"revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","scope":"EXTERNAL"}
]
```

The actual Git old/new changed paths are combined with transitively affected Python static-import **candidate** consumers. An intersecting witness dependency becomes `INVALIDATED_BY_CHANGED_SOURCE`; a nonintersecting one becomes `NOT_INVALIDATED_REQUIRES_REVALIDATION`, NOT PASS; an external one is always `BLOCKED_EXTERNAL`. All results are replayable against the committed Git source. Dynamic, non-Python and external consumers remain unobserved; the absence of a candidate import never proves no effect.

## DevOps timing and no implicit effects

At intake: record human intent, BASE and acceptance oracle. Before implementation: derive DoD, inspect owner ambiguities and select the smallest reversible slice (CORA does not prove global minimality). At premerge: run the contextual gate, required negative regressions and separate physical mutation oracle as authorized. PR-controlled CI only observes potential workflow effects; it does not execute deployments or authenticate readback. Postmerge: re-pin the actual merged main and redo impact/invalidation. An external reviewer alone can confer approval. `gold-mutate` stays an explicitly invoked mutator with AST/sandbox-limited oracles; CI does not run untrusted target code implicitly.

## 10 million seeded *semantic models*

`cora stress-convergence --require-full` constructs 10 fixed one-million-case sessions with 16 realistic software-assurance failure classes: ambiguous owner, dynamic consumer, self-editing policy, stale SHA, false invalidation, unrelated witness promotion, fabricated physical mutations, surviving mutants, unauthorized execution, unclassified CI effects, forged readback, private pilot inflation, premerge SHA drift, postmerge drift, forged review and missing rollback. The catalog enumerates the empty vector plus every 1–4-way interaction (**2,517 distinct normalized signatures**), including 16 singles and all 120 pairs per session; remaining cases are deterministically seeded mixtures. The last 100k should have zero new signatures in the **finite catalog**. Two full executions must produce byte-identical receipts, zero reference mismatches and zero unsafe model promotions. It executes **zero product-source mutants** and cannot establish statistical validity, semantic completeness, operational recovery or independent reviewer authority.

## External R1–R4 obligations

R1 requires an independently qualified real owner map and non-Python/dynamic consumer investigation; R2 requires real target behavioral mutants and independently attested confinement; R3 requires observed, authenticated target-side readback and effective hosting permissions; R4 requires legitimate private 3/3 source readback plus continuing real pre/postmerge/E2E/rollback tests. As of PR20 candidate, private ikant/aosp1 remain inaccessible to candidate CI, and these outcomes are **not observed**. Do not give PR-controlled workflows private-repository credentials to create a false green.

Source tests/CI can be `PASS_SCOPED` on an exact head. The complete global goal remains `BLOCKED_EXTERNAL` until the above independently collected evidence converges.

## PR-20 hardening: intent and deleted-source causality

The contextual DevOps opt-in accepts `--intent 'human-described bounded change and acceptance criteria'` and binds its digest to the exact BASE/HEAD. A missing per-change intent makes the source gate `DEBT_BLOCKED`; an explicit one is `CALLER_SUPPLIED_UNVERIFIED_BOUND_TO_BASE_HEAD`, **not** actual owner authority. Replay must provide the identical `--intent`; mismatched text, base or head refutes the receipt. When source files are deleted, renamed or change object type, CORA uses both the BASE and HEAD static candidate import graphs so removed modules do not silently lose their pre-change import consumers; a missing required BASE graph is debt-blocked. Legacy PR-16 evidence-lattice topology also uses the shared cycle/dangling-edge validator, retaining its separate evidence status vocabulary.


## Reflection 3/3 — typed method convergence and code-durability contract

The [bounded typed crosswalk](../cora.type-assurance-profile.json) specializes the *existing* method-atlas, artifact-role, ontology and reticulum owners. It declares 20 types in seven planes, links 14 current procedures, 10 methodological references (three ISO standards and seven non-ISO references), nine ISO/IEC 25010:2023 quality characteristics and 12 proposed durability invariants. **The crosswalk is a closed-world candidate, not a measurement of quality, ISO conformity, complete runtime use, or an authority to change/delete source.** The current independent checker is [verify_type_assurance.py](../tools/verify_type_assurance.py), within `cora-release-verification`; it checks exact Git blob bytes at the candidate HEAD and that the baseline is an ancestor.

### Bounded comparative learning: ICTC and iKant_EDU

The two repositories are *external consumer examples*, not the origin of new CORA decision authority. ICTC [#246](https://github.com/Luke883i/ictc/pull/246), [#241](https://github.com/Luke883i/ictc/pull/241), and [#239](https://github.com/Luke883i/ictc/pull/239) exhibit progressive navigation, product-document/presentation coherency, and conservative whole-repository source inventory. iKant_EDU [#216](https://github.com/Luke883i/iKant_EDU/pull/216), [#217](https://github.com/Luke883i/iKant_EDU/pull/217), and [#218](https://github.com/Luke883i/iKant_EDU/pull/218) exhibit minimal method absorption, local-owner-preserving reticular hygiene and a read-only prioritized consumer backlog. The **merged PR status and changed-file patches were inspected through GitHub**; the original target full test suites, native provider delivery, external consumers and deployment were **not executed or attested by this CORA change**. Some source/claim boundaries (e.g. the iKant_EDU #215 cutover) remain explicitly open.

### Source implementation and falsification

- Run `python tools/verify_type_assurance.py --repo . --revision HEAD` from a full checkout and inspect `PASS_SCOPED_STRUCTURAL_MODEL`, `authorization: NONE` and `external: BLOCKED_EXTERNAL`.
- Run `python -m unittest discover -s tests -p 'test_pr27_type_assurance.py' -v`. The local source-bundle suite exercises 29 distinct negative model families plus two physically committed synthetic Git mutants. The additional real-CORA test is *skipped outside a full Git checkout*, and on a genuine checkout it clones CORA into a disposable local repository and commits two original-source mutants: an owner symbol rename and an ungrounded removal of an external DoD edge.
- The canonical DoD is **still owned** by `cora.method-synthesis-dod.json`; the verifier rejects missing external leaves, cut-edge drift and nested-function spoofing. This does not introduce a second reticular runtime or a new CLI command.
- The existing `.github/workflows/ci-documentation.yml` performs exact-head Python 3.11/3.13 checks and writes a source-only receipt. A workflow file does **not** demonstrate that the job executed, passed or is a required branch-protection check; inspect GitHub checks for the precise final candidate HEAD.

### Non-compensatory acceptance and preserved debt

| Gate | Predicates | Sufficient witness | Current boundary |
| --- | --- | --- | --- |
| R3-G0 | BASE ancestry, commit identity, original blob readback | Exact Git object verification | Source-only |
| R3-G1 | 20 declared types, 7 planes and explicit non-universal scope | Bounded profile validator and missing-type mutants | Source-only |
| R3-G2 | 14 current method owners and no spoofed symbol | Canonical method-atlas, original code AST and physical rename mutant | Original checkout CI pending |
| R3-G3 | 10 categorized references and 9 quality axes | Declared crosswalk and altered-reference/quality mutants | No external standard conformance |
| R3-G4 | 12 typed durability obligations and falsifiers | Negative model suites | No real target durability proof |
| R3-G5 | Original reticular DoD closure, no source-to-external promotion | Changed-edge physical Git mutant | Independent approval absent |
| R3-G6 | Full original CORA tests at one final exact HEAD; real ICTC/iKant target probes | Actual workflow run and target-specific CI readback | Pending verification |
| R3-G7 | Independent reviewers, host rules, deployment behavior and governed rollback | External signed/host evidence | BLOCKED_EXTERNAL |

R3-G0–G5 are constrained source checks; the full claim is an AND of R3-G0…R3-G7. A finite synthetic campaign, local fixture test, accepted Git commit, or source-only CI cannot compensate for a missing external witness. A retained `UNKNOWN` consumer, absent target runtime or unobserved user journey must not become an unused file, safe deletion, release GO, verified product quality, or proof of independence.

### Review and post-merge protocol

Preserve the exact BASE/HEAD and original method-atlas/blob hashes; run `python -m unittest discover -s tests -v` and the checker on the *same* candidate SHA; inspect target-specific consumer and data flow effects for all changed source and documentation roles, plus the actual CI completion state. Perform a separate human review before merge. After a real merge, pin the *actual* merged SHA and run fresh `dev-postmerge`, source regression and the relevant behavioral oracles. Rollback means a separate, explicitly authorized reverse change with new readback; the mere presence of a source `git revert` path is not deployment recovery proof.

## Integrated service: original source-to-document-to-AI lattice (candidate)

**Intent.** CORA retains its single product and its original `cora-engine` and `cora-release-verification` software boundaries. The canonical `method-synthesize` command gains a strictly opt-in `--integrated` mode; no new agent, reviewer, execution authority, CI workflow, or 72nd command is introduced. This joins the existing source synthesis receipt, the full 71-command CLI inventory (eight families), original 14 procedure owners, 20 declared object types, 12 multi-abstraction dimensions, current document registry and original 18 README claim/evidence/falsifier relations. Each join is pinned to **one immutable Git revision** and checked by source replay. The resulting 20-row **semantic_crosswalk** binds each object type to its original method owner, source path, declared standards, quality axes, current-document path references and canonical README claim IDs; a missing owner path or an owner/standard mapping inconsistent with the canonical method atlas is a source contradiction, while an empty document reference is an explicit uncovered link rather than a false proof of compliance.

**Use from a full CORA Git checkout:**

```sh
cora method-synthesize . --revision HEAD --integrated --output /tmp/cora-integrated.json --ai-request-output /tmp/cora-ai-request.json
cora verify-method-synthesis /tmp/cora-integrated.json --repo . --integrated
cora stress-convergence --integrated --require-full --output /tmp/cora-integrated-10m.json
```

The generated AI request contains source-bound IDs and instructions to reverse-infer abstractions, distinguish product claims from tested behaviors, identify adversarial scenarios and positive controls, and recommend minimal reversible owner-preserving changes. It **does not invoke a provider**, leak the source bytes, or autonomously change code. To submit an AI result for safe source-scoped correlation, provide a bounded JSON document with `schema=cora-integrated-ai/1`, original `source_commit`, original `case_digest` and `items` carrying a hypothesis, cited support and counterexample references, an ordered abstraction path, an adversarial scenario, a positive control and `action=INVESTIGATE|RETAIN|REVIEW_ADJUST`. Use `--ai-observations RESPONSE` in both the generate and verify commands. All result items remain `UNVERIFIED_AI_HYPOTHESIS`; a duplicate ID, invented reference, stale source, role promotion or changed digest is rejected.

**Mechanically bounded DoD.** [Integrated lattice](../cora.integrated-dod.json) contains eight SOURCE leaves, three source AND-cuts and four EXTERNAL leaves with source and governed roots. The existing `reticulum.ordered_cut` verifies its exact dependency closure. G_SOURCE represents only source relationships and negative oracles; G_GOVERNED also requires real source-target behavior, a real model invocation if used, independently authenticated reviewer and host/product readback. It remains `BLOCKED_EXTERNAL`. `--integrated` only asserts *parity of 71 canonical CLI entrypoints*; it does not assert successful runtime execution of every command or certify ISO conformance. Documentation-to-source joins establish declared paths, README phrase/witness relationships and possible lexical inconsistencies; they are **not natural-language entailment or behavioral proof**.

**Realistic finite falsification, not 10M physical edits.** The opt-in model enumerates 32 finite fault families (stale source, claim drift, dynamic consumer, false compliance, authority promotion, missing runtime, no reviewer, missing rollback and others), with two positive families and 30 adversarial families. Ten million seeded trials and bounded same-seed replay must produce no reference/oracle disagreements; it does not establish saturation of real software defects or product correctness. Real original-source physical adversarial tests intentionally mutate the integrated DoD and README evidence in disposable Git clones. Historical corpus and external target behavior remain independently qualified.

**Ownership and closure.** `src/cora/integrated_service.py` composes `method_synthesis.py`, Git source, original claim evidence, type profile and reticulum, not an alternative source of truth. The capability inventory and artifact roles include the new module and contract. `ci-documentation.yml` runs original checkout source replay, tests, physical mutants and the 10M finite model; check the actual GitHub Actions run **at the final PR HEAD**. An independent reviewer must still assess possible doc false positives, unknown dynamic/external consumers, actual 71-command operational fitness, safety and release readiness. Postmerge rerun must use the actual merged SHA.


## Five synergic developments — retrograde mechanized DoD (PR29 candidate)

The five developments are **one minimal dependency lattice**: Semantic Truth Engine (G_TRUTH) → bounded AI Reasoning Engine (G_AI); a parallel original-source Behavioral Proof Engine (G_BEHAVIOR) and continuous cross-revision Semantic Evolution (G_EVOLUTION); all converge to G_UNIFIED. The governed root G_GOVERNED additionally requires real AI-provider execution where claimed, operational qualification of all commands, independent review, real target runtime and host authorization. Source success cannot compensate for those external leaves.

The canonical [five-synergies contract](../cora.five-synergies-dod.json) has 29 nodes, fixed in the existing `reticulum.ordered_cut` validator. The five source goals retain their original owners: `integrated_service.py`, `method_synthesis.py`, `continuous.py`, `git_snapshot.py`, and the canonical documentation proof/role/type atlases. `synergy.py` is a read-only composition, not a second authority.

**Mechanical witnesses by goal:**

- **G_TRUTH:** one-to-one 18 README claims → original source path/test AST witnesses. A missing phrase/path is a source contradiction; an AST symbol or named test is not semantic entailment or an executed behavior.
- **G_AI:** a bounded source-free inference request enumerates abstraction paths and positive/negative controls; response verification requires original SHA and case digest, valid/disjoint support/counterevidence and allowed non-authoritative review actions. Model invocation requires an explicit callback and authorization; live provider quality is not attested by a mock.
- **G_BEHAVIOR:** default NO_EXECUTION; operator-opt-in executes and exact-replays three original, read-only CORA source probes. Real runtime, dynamic callers and all 71 behaviors remain unsupported.
- **G_EVOLUTION:** `continuous.evaluate` uses **BASE-committed** policy to classify actual changed files/renames and preserve review roles. Each delta is correlated to current documents/claim witnesses; unresolved consumers remain UNKNOWN. An apparent semantic relation is review-candidate, not proof of a broken runtime behavior.
- **G_UNIFIED:** same-revision five-goal receipt, original owner coordination, digest replay and mandatory finite fault-class falsification. No G_GOVERNED/ISO/product/release GO is implied.

**Preseeded 1,000,000 semantically realistic finite cases.** [Corpus](../.cora/fixtures/five-synergies-mutants.json) contains 32 independent named scenarios over ten explicit failure dimensions: two benign/source-positive controls and 30 fault-class negatives (source drift, missing contract, false compliance, dynamic consumers, counterfeit evidence, missing tests, unchecked CI, rollback gaps and others). Each scenario carries a predeclared oracle and frozen fault vector checked against separate source-side reference mappings. One million seeded cases per run, then a second run and **byte-identical file comparison**, must yield 62,500 scoped positive controls, 937,500 blocked negatives, no disagreements, and no authorization promotion. These are **not one million independent physical code mutants**. The adversarial suite additionally performs original Git-committed mutations of the README/reticulum, forged behavioral receipts, altered consumer impact, invented AI references and the preseeded corpus; each must be rejected or remain review-required.

**Reviewer acceptance:** exact-head full unit regressions, the original source tests, the 1M model twice, and explicit claim-coverage/CI receipts on the same SHA. G_GOVERNED stays externally blocked; a PR author cannot self-approve protected branch rules, reviewer independence, target execution, hosted AI credentials or deploy/rollback.
