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
