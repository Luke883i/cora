# CORA for AI coding assistants — engineering method

## Intent, product truth and scope

CORA governs the coding agent; it is not a second agent and confers no merge, release or deletion authority. The user owns product intent, material acceptance and genuine outside decisions. An AI agent is responsible for reproducing the source identity, proposing the minimal material implementation slice, generating counterexamples and exposing unknowns. Source artifact identity, runtime execution, semantic correctness and human governance are distinct epistemic objects.

## Retrograde workflow

The canonical sequence is INTENT -> OBSERVE -> QUALIFY -> SLICE -> MATERIALIZE -> WITNESS -> CLOSE -> ACT. Work backwards from G_SOURCE_AGENT or G_GOVERNED_AGENT: identify mandatory intermediate AND cuts and the corresponding local leaves, each with a nearest falsifier; do not substitute output volume for closure.

INTENT: record target behavior, owner, acceptance oracle, constraints and authorization. OBSERVE: inspect actual main, exact commit SHA, source owners, architecture, debt and test history. QUALIFY: derive the local/intermediate/global lattice from the goal with dod-plan, treating missing external witnesses as BLOCKED. SLICE: choose one minimum material change that addresses the first real blocker and reuses the existing owner. MATERIALIZE: use independent regressions and semantic commits; preserve rollback. WITNESS: execute the real tests and record environment, command, SHA, negative cases and coverage. CLOSE: apply AND composition with no silent unknown-to-PASS promotion. ACT: open a PR, obtain exact-HEAD CI and independent review, then recompute postmerge on the merged main.

## DevOps timing and commands

| When | Agent obligation | CORA CLI | What it cannot prove |
| --- | --- | --- | --- |
| Discovery | source/product identity; intended outcome | dod-plan --stage intake; snapshot; audit | actual user acceptance |
| During development | owner reuse; one observable implementation delta; negative regression | dod-plan --stage implementation; process-run; file-lab | runtime correctness from static analysis |
| Before opening PR | all source prerequisites; exact base/head | dod-plan --stage premerge; dev-premerge; dod-assess; verify-dod | approval from self-issued claims |
| On PR check | real tests, full regressions, coverage, source mutants and 10M model when policy changes | stress-agent-dod --require-full; CI matrix | 10M real code mutants or production behavior |
| After merge | recompute source and debt on the actual merge SHA | dev-postmerge; debt-diff | that old PR SHA equals new main |
| Pilot/release | independent review, external security/runtime, recovery/rollback | dod-plan --stage release | release from model/CI alone |

The normative policy is .cora/contracts/dod/agent-dod.json. It fixes 24 failure families: six LOCAL, six INTERMEDIATE, six GLOBAL, six EXTERNAL. Each local node names a nearest falsifier, the four intermediate nodes are non-compensatory AND cuts, and G_SOURCE_AGENT depends on the first three intermediates while G_GOVERNED_AGENT additionally requires the independent external intermediate. Editing the PR policy cannot independently authorize acceptance; trusted BASE policy and hosting enforcement remain distinct.

## Input, output, evidence authenticity

Use cora dod-plan --stage premerge --output plan.json to obtain a source-only plan. To supply untrusted evidence claims, provide a JSON object with schema cora-agent-claims/1, head_sha as forty lowercase hex characters, and locals keyed by L01..L24. Each declared item may have status CLAIMED_PASS, BLOCKED or REFUTED; a CLAIMED_PASS must include the matching revision and a witness string. Run cora dod-assess claims.json --stage premerge --output result.json; run cora verify-dod result.json --observations claims.json for deterministic replay. Self-issued claims may produce MODEL_ELIGIBLE_UNATTESTED for source, never PASS_SCOPED, and never a governed/release GO. Wrong SHA, absent evidence, a refuted leaf, a forged authority or an altered report is rejected or blocked.

## Seeded semantic saturation and what 10 million means

The predeclared finite model has 24 typed fault dimensions and four semantic levels. Ten distinct seeds drive ten one-million-scenario sessions; every session forces all 24 individual fault families and the 276 unordered fault pairs, then generates varied one/two/three-fault scenarios via deterministic SplitMix64-derived mixing. An independent bit specification checks the source model; no synthetic case can self-attest governed release. The receipt records each seed, 1M count, covered families and pairs, distinct normalized fault signatures, new signatures in a 100k tail, oracle mismatches, unauthorized promotions and a stream SHA-256; two complete CI replays must produce exactly identical JSON. A session counts scenario calls, not ten million independent model interactions or physical target-code mutations.

The negative unittest writes and rejects 34 physical mutated contract JSON files (24 family changes and 10 structural/authority changes), not 34 production code mutants. Follow the ICTC #232 lesson: a small number of real product-source mutants against the actual runtime gate can reveal failures missed by a million schematic masks. If real source mutations, operational pilots and independently observed reviewer/host policy are absent, the corresponding claims stay open.

## Sampled methodological lineage (not transplanted test evidence)

- ICTC #183 (https://github.com/Luke883i/ictc/pull/183) uses ten independent model campaigns, pair coverage and no-novelty tails with an explicit governance boundary.
- ICTC #212 (https://github.com/Luke883i/ictc/pull/212) defines the deterministic intent-to-proof lifecycle and keeps a single canonical owner.
- ICTC #232 (https://github.com/Luke883i/ictc/pull/232) separates real product-source mutants and an HTTP runtime oracle from an earlier million-bitmask model.
- iKant_LE #190 (https://github.com/Luke883i/iKant_LE/pull/190) reverse-derives user-level acceptance prerequisites from an exact source/bootstrap chain, keeping native provider proof external.
- iKant_LE #200 (https://github.com/Luke883i/iKant_LE/pull/200) formalizes global/intermediate/local obligations and separates candidate source evidence from human authorization.

## Fail-closed stop criteria

STOP/BLOCKED on ambiguous product intent, missing canonical owner, inability to reproduce the pinned source, no independent behavioral oracle for a claimed runtime fix, missing required CI on the final HEAD, an uncovered critical family, an unsafe promotion, or an unauthenticated external reviewer. Use the current CORA AGENTS.md, GOVERNANCE.md, continuous policy and PR-16 source/runtime boundary. Release governance must remain external, and main protection must be checked in GitHub rather than inferred from repository source files.

## PR-18 historical correction

PR-17 counted the first 24 individual faults and 276 pairs by index even when a mutated `_scenario` could return the wrong mask. PR-18 counts only actual prespecified masks, asserts scenario diversity and includes six physical Python source mutants of CORA's finite model. `dod-assess` now identifies `next_unresolved_falsifier`, refuses whitespace-only witnesses and never treats L19–L24 caller claims as independently authenticated. This is better source-model falsification, **not** real target-repository semantic validity; see [the historiographic audit](archive/audits/AUDIT_PR18_MAIN.md).

## Current reader path after PR-20

This page explains the method and preserves the PR-17/18 agent-DoD semantics. For a newly adopting coding assistant, start with the [reader-first workflow](AGENT_ADOPTION.md) and the [current contextual assurance method](CONVERGENT_ASSURANCE.md); use the existing canonical reticular kernel, not a second plan engine. A real change requires an explicit `--intent` at `dev-premerge --contextual`, passed unchanged for `verify-contextual-gate`. A missing intent is debt-blocked, and a supplied intent remains caller-reported, not authenticated product acceptance. Real behavioral oracles and independent hosting are still external.
