# Adopt CORA in an AI coding workflow

**Document status:** CURRENT
**Current scope:** Using CORA as evidence infrastructure around a separate coding agent.
**Operational use:** Prepare a real target, pin BASE and HEAD, replay receipts after authorized changes.
**Evidence:** Target-owned ontology, contextual source receipts and real test logs.
**Limits:** Neither a chat handoff nor a receipt authenticates reviewers or deployment.


CORA **governs evidence and review** for a coding assistant; it does not write product code or authorize merging. A GitHub URL is a reading location, not an installation or a protected policy. Start with the [product README](../README.md), [agent rules](../AGENTS.md) and [method](AI_CODE_ASSURANCE.md).

## 1. Prepare the two repositories

Give the assistant access to a local CORA installation and a separate **target** checkout. Install CORA from an authorized clone using Python 3.11+:

```sh
python -m pip install -e /path/to/cora
cora --help
```

In the target, establish its *own* committed `cora.ontology.json`. Contextual pre/postmerge additionally requires a `.cora/continuous-policy.json` present in the trusted **BASE** revision. Its absence requires a separate human bootstrap decision; a candidate PR cannot approve its own policy. Review the [architecture](ARCHITECTURE.md) and [continuous method](CONTINUOUS_DEVELOPMENT.md). Do not overwrite the target's product and software identities with CORA's self-ontology.

## 2. Record the real engineering intent

The agent identifies the product outcome, independent acceptance oracle, impacted owners and consumers, and real BASE/HEAD commits. The exact change intent is supplied as text; CORA binds it to the source revision but does **not** authenticate its human author. Run the source/complete DoD plan:

```sh
cora convergence-plan --contract /path/to/cora/.cora/contracts/dod/convergence-dod.json
```

## 3. Execute an opt-in contextual source gate

After the target change is committed, replace the placeholders with real revisions. This is a source-only review workflow, not an implicit test runner or CI endorsement.

```sh
cora dev-premerge /path/to/target --base BASE_SHA --head PR_HEAD_SHA \
  --contextual --intent "Ship the stated change with its named acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json \
  --output /tmp/cora-premerge.json

cora verify-contextual-gate /tmp/cora-premerge.json --repo /path/to/target \
  --intent "Ship the stated change with its named acceptance tests" \
  --convergence-contract /path/to/cora/.cora/contracts/dod/convergence-dod.json
```

The same intent is required at replay. Missing intent produces `DEBT_BLOCKED`. A valid source report may still require review; dynamic consumers, behavioral tests and trusted side-effect readback remain separate obligations. `--strict` intentionally rejects unresolved conditions rather than turning them into approvals.

## 4. Complete real tests and review outside the receipt

Run the target project's real unit/integration tests and, only when authorized, concrete source mutators and relevant isolated runtime tests with independent oracles. Record SHA, environment, commands, coverage gaps, failed and surviving mutants. Do not present a deterministic 10-million-case finite model as 10 million source mutations or product behavioral passes.

Open the PR with the reports and unresolved blockers. Hosting administrators must independently enforce required checks and non-author approval. CORA does not configure those permissions.

## 5. Observe the actual merged revision

After a separately authorized merge, run `cora dev-postmerge TARGET --previous REAL_PREMERGE_MAIN --head ACTUAL_MERGED_MAIN --contextual --intent SAME_INTENT --convergence-contract PATH` and replay its receipt with `verify-contextual-gate`. A former PR-head green result is not a postmerge witness.

## Stopping conditions

Stop claims of acceptance when the target ontology is missing, ownership is ambiguous, the Git source or change intent cannot be reproduced, tests have no independent oracle, or effective permissions and reviewers are not attested. The full R1–R4 and governed roots remain blocked until real external witnesses converge. See [full R1–R4 DoD](DOD_PR20_CONVERGENCE.md) and [documentation DoD](DOCUMENTATION_DOD.md).

## Portable ChatGPT handoff (opt-in)

When using CORA in a chat-assisted workflow, distinguish the conversation's proposed actions from actual source evidence. Prepare a strict iteration JSON from `examples/chat-step.example.json`, execute **the same** `cora process-run --one-run --profile comprehensive` with `--chat-step` and `--chat-bundle`, then verify with `cora verify-process --one-run --chat-bundle`. Upload or transfer the ZIP to the next chat, read the latest `handoff.md`, and repeat with the next sequence number. Never claim automatic per-turn capture, external authorization, a genuine test execution, or chat-history completeness. See [Getting started](GETTING_STARTED.md).



## ChatGPT Project beta adapter

**Canonical prompt and owner:** this section is the single beta Project instruction source. The root README links here; `AGENTS.md` governs coding contributions and the target repository keeps its own product/software/runtime authority. This is an opt-in **CORA-METHOD** adapter, not a deployed CORA service or a replacement for `CORA-ENGINE`.

### Beginner setup: understand, modify, prove

1. **ChatGPT access:** the supported baseline for *this beta recipe* is **Plus or Edu**, subject to workspace and tool availability; a subscription alone is not proof of GitHub or code-execution entitlements. The local CORA Python CLI itself does **not** require ChatGPT.
2. **Authorize reading:** connect GitHub in ChatGPT, allow read access to [Luke883i/cora](https://github.com/Luke883i/cora) and the intended target repository, and confirm both are selectable. Never grant blanket repository access just for the tutorial.
3. **Authorize writing separately:** to implement a feature, the operator needs a **separate write-capable tool** with explicit permission on their own target repository, e.g. an authorized Codex environment or suitable GitHub write actions. The **standard ChatGPT GitHub app is read-only**; connecting it does not grant commits, pushes or PR creation. Do not infer tool support from a plan label. See [OpenAI's GitHub connection instructions](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt).
4. **Create a ChatGPT Project:** paste the canonical prompt below, name the target and goal, and distinguish observation from execution. A Project chat is not a CORA subprocess or an independently authenticated reviewer.
5. **Change and test:** have an authorized tool produce a bounded branch and commit, run CORA-ENGINE and target-native tests in a trusted checkout if available, inspect negative oracles, then propose a PR with exact-head evidence and unresolved conditions. Without runner access, report `NOT_RUN`; without write access, deliver only a draft, never a fictional commit.
6. **Continue later:** the opt-in [ChatGPT handoff](#portable-chatgpt-handoff-opt-in) is an **operator-generated temporary ZIP**. It contains numbered, locally produced step records, source receipts, DoD, evidence gaps, a handoff document and manifest; it is not live ChatGPT memory, encrypted evidence, a signature, or automatic transcript capture. Treat it as untrusted, verify it, and avoid secrets.

**Three objects, no authority transfer:** **product** = the target's observable value and acceptance criteria; **software** = its actual runtime plus CORA's optional local Python CLI; **repository** = that target's Git files, contracts, CI and provenance. CORA-METHOD guides the assistant; CORA-ENGINE only emits results when executed; target owners and humans approve.

### Paste into Project instructions — CORA local adapter beta v1

```text
CORA LOCAL PROJECT ADAPTER — BETA v1 (METHOD_ONLY BY DEFAULT)

Mission: Help develop and review the user's explicitly authorized target repository
using CORA-METHOD. Read Luke883i/cora as methodological reference only.
Do not transplant CORA's product ontology, policy, DoD or approvals into the target.

First: identify the exact Git repo/branch/HEAD, target product outcome,
software owners, consumer boundaries, relevant documents, test oracles,
tool capabilities and actual read/write/run permissions. If inaccessible,
declare UNKNOWN or NOT_RUN rather than inventing observations.

For each request:
1. State the product change, its audience and the minimal observable result.
2. Derive a backward AND-DoD: source, runtime, counterexamples, governance.
3. Inspect Git archaeology, documents, imports, dynamic/HTTP consumers and risks.
4. Select the smallest reversible semantic change and preserve original owners.
5. Use write tools only after authorization; bind blob/tree/commit/PR to real SHAs.
6. Falsify with independent expected outcomes and targeted native tests.
7. Replay source evidence with CORA-ENGINE only if it was actually executed.
8. Report PASS_SCOPED, REFUTED, NOT_RUN, UNKNOWN and BLOCKED_EXTERNAL faithfully.
9. Provide SHA, changed paths, test commands/results, survivors, debt and rollback.
10. Do not merge, release, delete or claim enterprise-ready by your own authority.

Modes: METHOD_ONLY (plan/chat), ENGINE_VERIFIED (real CORA CLI receipt),
TARGET_NATIVE (actual target tests), PR_MATERIALIZED (read-back GitHub objects).
A mode is earned by evidence, never by fluency or self-report.
The temporary CORA chat ZIP is an explicit opt-in handoff, not chat memory.
```

### Seven traceable engineering changes for a CTO

These are historical Git PRs, **not** evidence that CORA-ENGINE authored or certified each product. Read the exact source/diff and distinguish Git from runtime and human results.

| Case | Semantic outcome | Engineering lesson |
| --- | --- | --- |
| [CORA #46](https://github.com/Luke883i/cora/pull/46) | Portable per-iteration chat handoff | A chat plan becomes an inspectable, non-authorizing artifact. |
| [CORA #52](https://github.com/Luke883i/cora/pull/52) | Native Teddy Node and ICTC HTTP/SQLite pilots | Target-owned runtime evidence differs from source-only replay. |
| [ICTC #274](https://github.com/Luke883i/ictc/pull/274) | Physical `v3/` to `src/`, `public/`, `tests/` migration | Move consumers and entrypoints together; history stays history. |
| [ICTC #275](https://github.com/Luke883i/ictc/pull/275) | Post-cutover owner/path hardening | A tidy tree requires negative reachability checks. |
| [Teddy #56](https://github.com/Luke883i/teddy/pull/56) | CORA source assurance in its native Node repository | Reuse CORA without replacing Teddy's engine or product identity. |
| [iKant_EDU #242](https://github.com/Luke883i/iKant_EDU/pull/242) | Runtime evidence and DoD-of-DoD | Source receipts do not attest Host or MCP behavior. |
| [iKant_EDU #243](https://github.com/Luke883i/iKant_EDU/pull/243) | Root contraction with historical provenance and consumer DoD | No deletion by absence of a static reference alone. |

Other public **examples**, not blanket CORA-ENGINE qualifications: [academics](https://github.com/Luke883i/academics) (research entry), [ROA](https://github.com/Luke883i/ROA) (theory), [Juriscribe](https://github.com/Luke883i/juriscribe), [LUMEN](https://github.com/Luke883i/lumen) (browser target), and [NILO](https://github.com/Luke883i/NILO) (game/remote target). The seven cases above also link CORA, ICTC, Teddy and iKant_EDU.

## Phase-gated coding: adapt N without adding a coding agent to CORA

The human provides an adequately expressive A0 contract: intended behavior,
actors, data and state transitions, constraints, admissible effects and
acceptance criteria. For the LEVEL web-game demonstration, see
[the bounded full method](CONTINUOUS_DEVELOPMENT.md#level-contract-to-product-development-with-bounded-continuation-pr47-candidate).
The coding assistant proposes an AND-DAG of acceptance obligations
**backwards from the target outcome**, then chooses one reversible,
reviewable vertical slice. It writes code/files with **its own authorized
tools**; CORA does not write source, grant policy authority or merge.

After each explicitly invoked source-bound One-Run the **existing**
portable ZIP includes the current plan and proof gaps; replay now also
returns read-only continuation advice: first unresolved node,
candidate falsification action, round capacity, reported-contract drift,
exact source-change signal or three-round source/evidence stagnation.
It never predicts a final count N or grants execution permission.
A human saying **“proceed”** is authority for a previously agreed
bounded stage only, not general permission to execute untrusted code,
modify protected workflows, publish, install providers or merge.

In the new game target, make the first slice a playable movement and
checkpoint demonstration, not an invented six-level PASS. Each slice
should include positive/negative test oracles, Git commit identity,
target behavior readback, open gaps and rollback, plus build and
dependency/environment provenance. Distinguish model-mask saturation
from real code mutation and browser playback.

**No extra orchestrator:** reuse \`cora convergence-plan\`,
\`process-run --one-run --chat-step --chat-bundle\`, \`verify-process\`,
the canonical reticulum and the existing protected-host policy.
Never overwrite a target product's ontology or an original CI owner
with CORA's project identity. See also [the README](../README.md),
[CLI reference](CLI_REFERENCE.md) and [reticular contracts](../.cora/contracts/index.json).
